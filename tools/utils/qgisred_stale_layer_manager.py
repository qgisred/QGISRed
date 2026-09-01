# -*- coding: utf-8 -*-
"""The "this layer no longer matches the network" warning in the legend.

The hard part is not deciding which layers are stale — it is keeping the icon on the right
row. QgsLayerTreeView stores its indicators in a hash keyed by *node pointer*, and the
plugin rebuilds the layer tree constantly: opening a group, reordering result layers or
reloading a project destroys nodes and builds new ones. An indicator left on a destroyed
node stays in that hash under a dangling key, and the next node allocated at the same
address inherits it — which is how the warning turned up on input layers that are never
even checked, sometimes twice on the same row.

So the indicators are not tracked by layer id and trusted to stay put. Every pass sweeps
the whole tree, compares what is actually attached against what should be, and fixes the
difference. Ghosts are recognised because the manager keeps the objects it created, so
indicators belonging to other plugins are never touched.
"""
from contextlib import suppress
import os
import glob as _glob

from qgis.core import QgsProject
from qgis.gui import QgsLayerTreeViewIndicator
from qgis.PyQt.QtCore import Qt, QEvent, QObject, QTimer, QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .qgisred_filesystem_utils import DIR_ISSUES, DIR_QUERIES, DIR_RESULTS, DIR_AUXILIARY_LAYERS
from .qgisred_project_utils import QGISRedProjectUtils

# Layers the DLL derives from the network: if an input has been edited since they were
# written, what they show no longer describes the current network.
MONITORED_SUBDIRS = (DIR_ISSUES, DIR_QUERIES, DIR_RESULTS)

# The Demand Builder's themes live here. They are the user's own working data — imported
# consumption points, billing sectors — not something the plugin recomputes from the
# network, so an input edited afterwards says nothing about whether they are still valid.
EXCLUDED_SUBDIRS = (DIR_AUXILIARY_LAYERS,)

# The same exclusion by qgisred_identifier, for a theme opened from somewhere else (the
# Demands Manager can add layers to the group from outside the project folder).
EXCLUDED_IDENTIFIER_PREFIXES = ("qgisred_demandbuilder", "qgisred_demandsectors")

# Thematic maps whose legend class labels embed a length unit, so the units they were
# built with can be recovered for layers created before the qgisred_theme_units stamp.
LEGACY_UNITS_IDENTIFIERS = ("qgisred_query_pipes_length", "qgisred_query_pipes_diameter")
UNIT_SYSTEM_BY_TOKEN = {"m": "SI", "mm": "SI", "ft": "US", "in": "US"}

# What a warning means, and therefore what clicking it can offer to do. Results and
# thematic maps have a one-click way back to a valid state; everything else is a report.
KIND_RESULTS = "results"
KIND_THEMATIC = "thematic"
KIND_DERIVED = "derived"
ACTIONABLE_KINDS = (KIND_RESULTS, KIND_THEMATIC)

# Marks an indicator as this plugin's. The tooltip used to be that mark, but it is
# translated and now differs per kind, which would turn ownership into a list of strings to
# keep in sync with four .ts files.
_INDICATOR_PROPERTY = "qgisredStaleWarning"

# Where the running manager is published so the *next* plugin load can find it.
#
# Reloading the plugin re-imports this module, so a module-level global would come back
# empty and the previous manager — still connected to QgsProject, still holding a running
# timer, and still closing over the unloaded plugin's now-blank NetworkName — would keep
# sweeping the tree and stripping the warnings the new manager had just put there.
# qgis.utils is never reloaded, which makes it the one place the two loads share.
_REGISTRY_ATTRIBUTE = "_qgisredStaleLayerManager"


def _activeInstance():
    with suppress(Exception):
        import qgis.utils
        return getattr(qgis.utils, _REGISTRY_ATTRIBUTE, None)
    return None


def _setActiveInstance(manager):
    with suppress(Exception):
        import qgis.utils
        setattr(qgis.utils, _REGISTRY_ATTRIBUTE, manager)


def _eventPosition(event):
    # Qt6 replaced QMouseEvent.pos() with position(), which returns a QPointF.
    with suppress(Exception):
        return event.position().toPoint()
    return event.pos()


class _IndicatorHoverFilter(QObject):
    """Feeds the layer tree's mouse moves to the manager, so it can show a hand cursor
    over a warning a click can act on.

    A separate object only because StaleLayerManager is not a QObject and Qt lets nothing
    else filter events; it holds no logic of its own.
    """

    def __init__(self, manager, view):
        super().__init__(view)
        self._manager = manager
        self._view = view
        viewport = view.viewport()
        # Without tracking, moves only arrive while a mouse button is held down.
        self._trackingWasOn = viewport.hasMouseTracking()
        viewport.setMouseTracking(True)
        viewport.installEventFilter(self)

    def detach(self):
        with suppress(Exception):
            viewport = self._view.viewport()
            viewport.removeEventFilter(self)
            if not self._trackingWasOn:
                viewport.setMouseTracking(False)

    def eventFilter(self, _obj, event):
        with suppress(Exception):
            eventType = event.type()
            if eventType == QEvent.Type.MouseMove:
                self._manager.updateHoverCursor(_eventPosition(event))
            elif eventType == QEvent.Type.Leave:
                self._manager.updateHoverCursor(None)
        return False   # never consume anything


class StaleLayerManager:
    """Polls every 5 s and marks Issues/Queries/Results layers whose files are older than
    the newest input shapefile."""

    def __init__(self, iface, getProjectInfo, onIndicatorClicked=None):
        """
        iface              — QgisInterface
        getProjectInfo     — callable returning (NetworkName, ProjectDirectory); empty
                             strings mean no project is open.
        onIndicatorClicked — callable(layerId, kind) run when the user clicks an actionable
                             warning; None leaves every warning informational.
        """
        self._iface = iface
        self._getProjectInfo = getProjectInfo
        self._onIndicatorClicked = onIndicatorClicked
        self._owned = {}           # indicator this manager created → the kind it was made for
        self._indicators = {}      # layer_id → the indicator currently on its node
        self._dirty = False        # an indicator was added or removed since the last repaint
        self._stopped = False
        self._hoverCursorApplied = False

        previous = _activeInstance()
        if previous is not None and previous is not self:
            with suppress(Exception):
                previous.stop()
        _setActiveInstance(self)

        # Strip the indicator while the node is still alive. The sweep would catch the
        # leftover eventually, but only once something else surfaced it.
        QgsProject.instance().layersWillBeRemoved.connect(self._onLayersWillBeRemoved)

        # The poll only notices a file whose mtime moved. Opening a group gives its layers
        # brand new nodes that carry no indicator at all, and waiting up to five seconds
        # for the next tick to put it back is what read as "it takes a while".
        # legendLayersAdded fires once per batch — the layer tree's own addedChildren
        # fires per node, which is far too hot a signal to hang plugin code off.
        self._pending = QTimer()
        self._pending.setSingleShot(True)
        self._pending.setInterval(200)
        self._pending.timeout.connect(self._check)
        QgsProject.instance().legendLayersAdded.connect(self._onLayersAdded)

        self._timer = QTimer()
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._check)
        self._timer.start()

        self._hoverFilter = None
        if onIndicatorClicked is not None:
            with suppress(Exception):
                self._hoverFilter = _IndicatorHoverFilter(self, self._view())

    @staticmethod
    def tr(msg):
        return QCoreApplication.translate("StaleLayerManager", msg)

    # ------------------------------------------------------------------
    # Relevance
    # ------------------------------------------------------------------

    @staticmethod
    def _isUnder(normFile, projDir, subdir):
        """True when `normFile` sits inside `projDir/subdir`.

        The trailing separator makes the test land on a folder boundary: without it
        "Results" also matches a sibling called "ResultsBackup".
        """
        prefix = os.path.normcase(os.path.join(projDir, subdir)) + os.sep
        return normFile.startswith(prefix)

    @classmethod
    def _isMonitoredPath(cls, normFile, projDir):
        if any(cls._isUnder(normFile, projDir, excluded) for excluded in EXCLUDED_SUBDIRS):
            return False
        return any(cls._isUnder(normFile, projDir, monitored) for monitored in MONITORED_SUBDIRS)

    @staticmethod
    def _isExcludedIdentifier(layer):
        identifier = layer.customProperty("qgisred_identifier") or ""
        return str(identifier).lower().startswith(EXCLUDED_IDENTIFIER_PREFIXES)

    # ------------------------------------------------------------------
    # Timer callback
    # ------------------------------------------------------------------

    def _staleLayerKinds(self):
        """Derived layers written before the last input edit, mapped to their kind."""
        net, projDir = self._getProjectInfo()
        if not net or not projDir:
            return {}

        inputFiles = (
            _glob.glob(os.path.join(projDir, f"{net}_*.shp")) +
            _glob.glob(os.path.join(projDir, f"{net}_*.dbf"))
        )
        inputFiles = [f for f in inputFiles if os.path.exists(f)]
        if not inputFiles:
            return {}

        newestInput = max(os.path.getmtime(f) for f in inputFiles)

        stale = {}
        for layer in list(QgsProject.instance().mapLayers().values()):
            provider = layer.dataProvider()
            if provider is None:
                continue

            layerFile = provider.dataSourceUri().split("|")[0].strip()
            normFile = os.path.normcase(layerFile)
            relevant = (
                self._isMonitoredPath(normFile, projDir)
                and os.path.basename(layerFile).lower().startswith(net.lower() + "_")
                and not self._isExcludedIdentifier(layer)
            )
            if not relevant or not os.path.exists(layerFile):
                continue

            if newestInput > os.path.getmtime(layerFile):
                stale[layer.id()] = (KIND_RESULTS if self._isUnder(normFile, projDir, DIR_RESULTS)
                                     else KIND_DERIVED)

        return stale

    def _backfillThemeUnits(self, layer):
        # Themes created before the units stamp existed carry no qgisred_theme_units;
        # recover the build units once from the unit tokens of the legend class labels.
        if layer.customProperty("qgisred_theme_units"):
            return
        if layer.customProperty("qgisred_identifier") not in LEGACY_UNITS_IDENTIFIERS:
            return
        with suppress(Exception):
            inferredSystems = set()
            for legendItem in layer.renderer().legendSymbolItems():
                token = (legendItem.label() or "").strip().rsplit(" ", 1)[-1]
                if token in UNIT_SYSTEM_BY_TOKEN:
                    inferredSystems.add(UNIT_SYSTEM_BY_TOKEN[token])
            if len(inferredSystems) == 1:
                layer.setCustomProperty("qgisred_theme_units", inferredSystems.pop())

    def _outdatedThemeLayerIds(self):
        """Ids of thematic map layers built with units, flow units or a headloss
        formula the project no longer uses."""
        net, projDir = self._getProjectInfo()
        if not net or not projDir:
            return set()

        try:
            currentUnits = QGISRedProjectUtils.getUnits()
            currentFormula = QGISRedProjectUtils.getHeadlossFormula()
            currentFlowUnits = QGISRedProjectUtils.getFlowUnit()
        except Exception:
            return set()

        outdated = set()
        for layer in list(QgsProject.instance().mapLayers().values()):
            self._backfillThemeUnits(layer)
            themeUnits = layer.customProperty("qgisred_theme_units")
            themeFormula = layer.customProperty("qgisred_theme_formula")
            themeFlowUnits = layer.customProperty("qgisred_theme_flow_units")
            unitsChanged = bool(themeUnits) and themeUnits != currentUnits
            formulaChanged = bool(themeFormula) and themeFormula != currentFormula
            flowUnitsChanged = bool(themeFlowUnits) and themeFlowUnits != currentFlowUnits
            if unitsChanged or formulaChanged or flowUnitsChanged:
                outdated.add(layer.id())

        return outdated

    def _isActive(self):
        """False for a manager the plugin has moved on from.

        stop() is the normal way out, but it runs inside unload()'s blanket suppress and a
        single failure there used to leave the whole object connected and ticking. Checking
        the registry means a superseded manager does nothing even if it was never stopped.
        """
        if self._stopped:
            return False
        active = _activeInstance()
        return active is None or active is self

    def _kindByLayerId(self):
        """Every flagged layer and what kind of staleness it has.

        The two sources cannot collide today — a thematic map reads the input shapefile in
        the project root, which the file check never looks at — but the file check is the
        authoritative one, so it is applied last.
        """
        kinds = {layerId: KIND_THEMATIC for layerId in self._outdatedThemeLayerIds()}
        kinds.update(self._staleLayerKinds())
        return kinds

    def _check(self):
        if not self._isActive():
            return
        self._syncIndicators(self._kindByLayerId())

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------

    def _view(self):
        return self._iface.layerTreeView()

    def _tooltip(self, kind=KIND_DERIVED):
        if kind == KIND_RESULTS:
            return (self.tr("Results may be outdated — the network has changed since the last simulation")
                    + "\n" + self.tr("Click this icon to run the simulation again"))
        if kind == KIND_THEMATIC:
            return (self.tr("Thematic map may be outdated — project settings have changed since it was built")
                    + "\n" + self.tr("Click this icon to rebuild it"))
        return self.tr("Layer may be outdated — inputs have changed since last generation")

    def _isOurs(self, indicator):
        """Ghosts outlive the manager that made them: reloading the plugin starts with an
        empty `_owned` while the view still holds indicators from the previous load.
        """
        if indicator in self._owned:
            return True
        with suppress(Exception):
            # `is True` rather than a truth test: property() answers None when unset, but a
            # foreign object is free to answer anything at all.
            if indicator.property(_INDICATOR_PROPERTY) is True:
                return True
        with suppress(Exception):
            # A ghost from a load that predates the property carries the one tooltip that
            # version ever set.
            return indicator.toolTip() == self._tooltip()
        return False

    def _ownIndicators(self, view, node):
        """The indicators on `node` that this manager put there — ghosts included."""
        with suppress(Exception):
            return [indicator for indicator in view.indicators(node) if self._isOurs(indicator)]
        return []

    def _createIndicator(self, view, node, layerId, kind):
        indicator = QgsLayerTreeViewIndicator(view)
        indicator.setIcon(QIcon(":/images/iconWarning.svg"))
        indicator.setToolTip(self._tooltip(kind))
        with suppress(Exception):
            indicator.setProperty(_INDICATOR_PROPERTY, True)
        if kind in ACTIONABLE_KINDS and self._onIndicatorClicked is not None:
            # clicked() carries a QModelIndex of the view's model, and by the time it fires
            # the tree may have been rebuilt under it; the layer id captured when the
            # indicator was attached is the only stable handle on what was clicked.
            with suppress(Exception):
                indicator.clicked.connect(
                    lambda _index, layerId=layerId: self._dispatchClick(layerId))
        view.addIndicator(node, indicator)
        self._owned[indicator] = kind
        self._dirty = True
        return indicator

    def _dispatchClick(self, layerId):
        if not self._isActive() or self._onIndicatorClicked is None:
            return
        # The sweep that attached this indicator may be five seconds old, so what the click
        # is worth is decided now: a layer that is no longer stale does nothing.
        kind = self._kindByLayerId().get(layerId)
        if kind not in ACTIONABLE_KINDS:
            return
        with suppress(Exception):
            self._onIndicatorClicked(layerId, kind)

    def _dropIndicator(self, view, node, indicator):
        self._owned.pop(indicator, None)
        with suppress(Exception):
            view.removeIndicator(node, indicator)
        self._dirty = True

    def _repaint(self, view):
        """Force the legend to redraw.

        add/removeIndicator call update() on the view, but the rows are painted by the
        viewport — a child widget, which that update never reaches. Without this the icon
        only appears once something else repaints the tree, which in practice meant
        scrolling the legend.
        """
        if not self._dirty:
            return
        self._dirty = False
        with suppress(Exception):
            view.viewport().update()

    def _indicatorAt(self, pos):
        """The indicator drawn under `pos`, or None.

        QGIS lays the icons out in its own item delegate, which the Python bindings do not
        expose, so the strip has to be located the way QgsLayerTreeViewProxyStyle does: one
        cell per icon, each as wide as the row is tall, packed against the right edge of the
        viewport and clear of the layer mark. Getting this wrong only misplaces the cursor
        hint — the click itself is QGIS's own hit test, not this one.
        """
        view = self._view()
        index = view.indexAt(pos)
        if not index.isValid():
            return None
        node = view.index2node(index)
        if node is None:
            return None
        indicators = view.indicators(node)
        if not indicators:
            return None

        row = view.visualRect(index)
        height = row.height()
        if height <= 0:
            return None
        left = (view.viewport().width() - height * len(indicators)
                - height // 10 - view.layerMarkWidth())
        if pos.x() < left or not (row.top() <= pos.y() < row.top() + height):
            return None

        cell = (pos.x() - left) // height
        return indicators[cell] if 0 <= cell < len(indicators) else None

    def updateHoverCursor(self, pos):
        """Show a hand while the pointer is over a warning that clicking can act on.

        `pos` is in viewport coordinates; None means the pointer has left the tree.
        """
        if not self._isActive():
            return

        wanted = False
        if pos is not None and self._onIndicatorClicked is not None:
            with suppress(Exception):
                wanted = self._owned.get(self._indicatorAt(pos)) in ACTIONABLE_KINDS
        if wanted == self._hoverCursorApplied:
            return

        with suppress(Exception):
            viewport = self._view().viewport()
            if wanted:
                viewport.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                viewport.unsetCursor()
            self._hoverCursorApplied = wanted

    def _syncIndicators(self, kindByLayerId):
        """Make every node in the tree carry exactly the indicator it should.

        Walking the tree rather than the stale set is the point: a node that should carry
        nothing is just as much a mismatch as one missing its warning, and that is the case
        a ghost shows up as.
        """
        view = self._view()
        root = QgsProject.instance().layerTreeRoot()
        nodes = []
        with suppress(Exception):
            nodes = list(root.findLayers())

        attached = {}
        for node in nodes:
            layerId = node.layerId()
            kind = kindByLayerId.get(layerId)
            existing = self._ownIndicators(view, node)
            # Only an indicator this manager built for this very kind may stay. An adopted
            # ghost looks right but its clicked() goes nowhere — it belongs to a manager
            # that is gone — and a kind that changed since means both the tooltip and the
            # action behind it are now wrong. Either way it is replaced, not reused.
            keep = next((i for i in existing if self._owned.get(i) == kind), None) if kind else None
            for indicator in existing:
                if indicator is not keep:
                    self._dropIndicator(view, node, indicator)
            if kind and keep is None:
                keep = self._createIndicator(view, node, layerId, kind)
            if keep is not None:
                attached[layerId] = keep

        self._indicators = attached
        self._repaint(view)

    def _clearNode(self, view, node):
        for indicator in self._ownIndicators(view, node):
            self._dropIndicator(view, node, indicator)

    def _clearAll(self):
        self._syncIndicators({})

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _onLayersWillBeRemoved(self, layers):
        """Take the indicator off the node before the node is destroyed."""
        if not self._isActive():
            return
        view = self._view()
        root = QgsProject.instance().layerTreeRoot()
        for item in layers:
            layerId = item if isinstance(item, str) else getattr(item, "id", lambda: None)()
            if not layerId:
                continue
            self._indicators.pop(layerId, None)
            node = None
            with suppress(Exception):
                node = root.findLayer(layerId)
            if node is not None:
                self._clearNode(view, node)
        self._repaint(view)

    def _onLayersAdded(self, _layers):
        """Re-check shortly after the new nodes are in place.

        Debounced rather than immediate: opening a group emits this once per call, and the
        plugin opens several in a row.
        """
        if not self._isActive():
            return
        self._pending.start()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def forceCheck(self):
        """Run an immediate staleness check without waiting for the next timer tick."""
        self._check()

    def stop(self):
        """Disconnect and clean up. Safe to call twice, and never leaves half a manager.

        unload() calls this inside a blanket suppress, so the order matters: everything
        that keeps the object reachable from Qt goes first, and the flag is set in a
        finally, so a failure while clearing the icons cannot resurrect the manager.
        """
        try:
            with suppress(Exception):
                QgsProject.instance().layersWillBeRemoved.disconnect(self._onLayersWillBeRemoved)
            with suppress(Exception):
                QgsProject.instance().legendLayersAdded.disconnect(self._onLayersAdded)
            with suppress(Exception):
                self._timer.stop()
            with suppress(Exception):
                self._pending.stop()
            with suppress(Exception):
                self.updateHoverCursor(None)
            with suppress(Exception):
                if self._hoverFilter is not None:
                    self._hoverFilter.detach()
                self._hoverFilter = None
            with suppress(Exception):
                self._clearAll()
        finally:
            self._stopped = True
            if _activeInstance() is self:
                _setActiveInstance(None)
