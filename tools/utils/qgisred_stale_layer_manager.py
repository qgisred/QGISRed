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
from qgis.PyQt.QtCore import QTimer, QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .qgisred_filesystem_utils import DIR_ISSUES, DIR_QUERIES, DIR_RESULTS, DIR_AUXILIARY_LAYERS

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


class StaleLayerManager:
    """Polls every 5 s and marks Issues/Queries/Results layers whose files are older than
    the newest input shapefile."""

    def __init__(self, iface, getProjectInfo):
        """
        iface          — QgisInterface
        getProjectInfo — callable returning (NetworkName, ProjectDirectory); empty
                         strings mean no project is open.
        """
        self._iface = iface
        self._getProjectInfo = getProjectInfo
        self._owned = set()        # every indicator this manager created and has not removed
        self._indicators = {}      # layer_id → the indicator currently on its node
        self._dirty = False        # an indicator was added or removed since the last repaint
        self._stopped = False

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

    def _staleLayerIds(self):
        """Ids of the derived layers written before the last input edit."""
        net, projDir = self._getProjectInfo()
        if not net or not projDir:
            return set()

        inputFiles = (
            _glob.glob(os.path.join(projDir, f"{net}_*.shp")) +
            _glob.glob(os.path.join(projDir, f"{net}_*.dbf"))
        )
        inputFiles = [f for f in inputFiles if os.path.exists(f)]
        if not inputFiles:
            return set()

        newestInput = max(os.path.getmtime(f) for f in inputFiles)

        stale = set()
        for layer in list(QgsProject.instance().mapLayers().values()):
            provider = layer.dataProvider()
            if provider is None:
                continue

            layerFile = provider.dataSourceUri().split("|")[0].strip()
            relevant = (
                self._isMonitoredPath(os.path.normcase(layerFile), projDir)
                and os.path.basename(layerFile).lower().startswith(net.lower() + "_")
                and not self._isExcludedIdentifier(layer)
            )
            if not relevant or not os.path.exists(layerFile):
                continue

            if newestInput > os.path.getmtime(layerFile):
                stale.add(layer.id())

        return stale

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

    def _check(self):
        if not self._isActive():
            return
        self._syncIndicators(self._staleLayerIds())

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------

    def _view(self):
        return self._iface.layerTreeView()

    def _tooltip(self):
        return self.tr("Layer may be outdated — inputs have changed since last generation")

    def _isOurs(self, indicator):
        """Ghosts outlive the manager that made them: reloading the plugin starts with an
        empty `_owned` while the view still holds indicators from the previous load. The
        tooltip is what identifies those, and it is specific enough not to claim an
        indicator another plugin added.
        """
        if indicator in self._owned:
            return True
        with suppress(Exception):
            return indicator.toolTip() == self._tooltip()
        return False

    def _ownIndicators(self, view, node):
        """The indicators on `node` that this manager put there — ghosts included."""
        with suppress(Exception):
            return [indicator for indicator in view.indicators(node) if self._isOurs(indicator)]
        return []

    def _createIndicator(self, view, node):
        indicator = QgsLayerTreeViewIndicator(view)
        indicator.setIcon(QIcon(":/images/iconWarning.svg"))
        indicator.setToolTip(self._tooltip())
        view.addIndicator(node, indicator)
        self._owned.add(indicator)
        self._dirty = True
        return indicator

    def _dropIndicator(self, view, node, indicator):
        self._owned.discard(indicator)
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

    def _syncIndicators(self, staleIds):
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
            existing = self._ownIndicators(view, node)
            # One is enough; a second on the same row is a ghost by definition.
            keep = existing[0] if (layerId in staleIds and existing) else None
            for indicator in existing:
                if indicator is not keep:
                    self._dropIndicator(view, node, indicator)
            if layerId in staleIds and keep is None:
                keep = self._createIndicator(view, node)
            if keep is not None:
                attached[layerId] = keep

        self._indicators = attached
        self._repaint(view)

    def _clearNode(self, view, node):
        for indicator in self._ownIndicators(view, node):
            self._dropIndicator(view, node, indicator)

    def _clearAll(self):
        self._syncIndicators(set())

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
                self._clearAll()
        finally:
            self._stopped = True
            if _activeInstance() is self:
                _setActiveInstance(None)
