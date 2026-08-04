# -*- coding: utf-8 -*-
"""Arbitration of map highlights between the plugin docks.

Six docks draw temporary graphics on the canvas (QgsHighlight, rubber bands,
vertex markers) and several of them also select features on their layer. Until
this module existed each one decided on its own when to erase them, which gave
three different answers to the same question: TimeSeries and Profile handed the
canvas over to each other through cross-calls between their sections, the
Element Explorer wiped its highlights on *any* map tool change — panning
included — and the two query docks did nothing at all, so their highlights
outlived the dock being hidden.

The rule is now single and global: exactly one owner shows highlights at a time.
Losing ownership *suspends* an owner, it does not destroy its state — every dock
keeps enough information (the picked feature, the query expression, the profile
path) to redraw itself, so getting the focus back restores what was on screen.

Native QGIS tools are graded rather than treated as one block. Navigating the
map is not a change of subject, so pan and zoom leave the highlights alone;
identify and select produce a competing highlight of their own, so they suspend.

Ownership is decided from two signals, connected once here instead of once per
section: QApplication.focusChanged (the user clicked into a dock) and
QgsMapCanvas.mapToolSet (a tool took the canvas).
"""
from contextlib import suppress

from qgis.PyQt.QtCore import QEvent


class MapToolRole:
    """What a map tool means for highlight ownership."""

    OWNED = "owned"                # belongs to a registered owner
    PLUGIN_OTHER = "plugin_other"  # a QGISRed tool with no owner (editing tools)
    EDITING = "editing"            # native digitizing — the geometry itself is changing
    NAVIGATION = "navigation"      # pan / zoom / measure — does not change the subject
    SELECTION = "selection"        # native identify / select — competing highlight


# QGIS's own select and identify tools live in src/app and are NOT wrapped for
# Python: sip hands them over cast to the nearest wrapped base, so a select tool
# arrives as a bare QgsMapTool and an add-feature tool as QgsMapToolDigitizeFeature.
# Their class names therefore say nothing, and they are identified instead by the
# QAction the toolbar button sets on them, which QgisInterface does expose.
_SELECTION_IFACE_ACTIONS = (
    "actionIdentify",
    "actionSelect",
    "actionSelectRectangle",
    "actionSelectPolygon",
    "actionSelectFreehand",
    "actionSelectRadius",
)

# Class names are still a useful last resort for tools that *are* wrapped
# (QgsMapToolIdentify and its subclasses arrive under their own name).
_SELECTION_TOOL_MARKERS = ("identify", "select")

# Navigating is not a change of subject. Listed for documentation only;
# anything unrecognised also ends up as NAVIGATION.
_NAVIGATION_TOOL_MARKERS = ("pan", "zoom", "measure")

# How a QGISRed map tool is recognised without importing every tool module.
_PLUGIN_TOOL_MODULE_MARKER = "tools.map_tools"
_PLUGIN_TOOL_NAME_PREFIX = "QGISRed"


def _isNativeEditingTool(tool):
    """True for any QGIS digitizing tool.

    QgsMapToolEdit is the root of the whole editing family and *is* wrapped, so
    even the unwrapped app-level tools (add feature, vertex tool) arrive as one
    of its subclasses.
    """
    with suppress(Exception):
        from qgis.gui import QgsMapToolEdit

        return isinstance(tool, QgsMapToolEdit)
    return False


ACTIVE_ACCENT = "#0097A7"
INACTIVE_ACCENT = "#B0BEC5"


def _isPluginMapTool(tool):
    """True for a map tool that belongs to QGISRed.

    Checked *before* any isinstance test against the native classes, because
    QGISRedIdentifyFeature derives from QgsMapToolIdentify and would otherwise
    be filed as a competing native tool.
    """
    if tool is None:
        return False
    cls = type(tool)
    module = getattr(cls, "__module__", "") or ""
    if _PLUGIN_TOOL_MODULE_MARKER in module:
        return True
    return (getattr(cls, "__name__", "") or "").startswith(_PLUGIN_TOOL_NAME_PREFIX)


def _nativeToolRole(tool):
    name = (getattr(type(tool), "__name__", "") or "").lower()
    for marker in _SELECTION_TOOL_MARKERS:
        if marker in name:
            return MapToolRole.SELECTION
    return MapToolRole.NAVIGATION


class QGISRedHighlightOwnerMixin:
    """Protocol for a dock that draws its own highlights on the canvas.

    Mixed in *before* QDockWidget so the event overrides below run first:

        class MyDock(QGISRedHighlightOwnerMixin, QDockWidget):
            highlightOwnerKey = "myDock"

    Subclasses implement clearMapHighlights() and redrawMapHighlights(); the
    suspend/restore pair on top of them is what the manager drives.
    """

    highlightOwnerKey = "unnamed"
    highlightActiveAccent = ACTIVE_ACCENT
    highlightInactiveAccent = INACTIVE_ACCENT

    # -- Wiring ------------------------------------------------------------
    def highlightManager(self):
        return getattr(self, "_highlightManager", None)

    def notifyHighlightActivated(self):
        """The user turned to this dock — take the canvas if there is anything
        to show on it."""
        manager = self.highlightManager()
        if manager is not None:
            with suppress(Exception):
                manager.activate(self)

    def isHighlightSuspended(self):
        """True when the arbiter has taken the canvas away from this dock.

        Guard *reactive* redraws with it — a dock that repaints because another
        one changed the layer selection would claim the canvas straight back,
        and the two would trade it forever. Redraws the user actually asked for
        need no guard: drawing is a legitimate claim.
        """
        manager = self.highlightManager()
        if manager is None:
            return False
        with suppress(Exception):
            return bool(manager.isSuspended(self))
        return False

    def notifyHighlightDrawn(self):
        """This dock just put graphics on the canvas — take ownership.

        Call it from every path that draws. Focus alone is not enough: a dock
        whose highlight appears as a side effect of editing a filter draws long
        after the click that focused it.
        """
        manager = self.highlightManager()
        if manager is not None:
            with suppress(Exception):
                manager.claim(self)

    # -- Protocol the manager calls ---------------------------------------
    def highlightWidget(self):
        """Widget whose destruction unregisters this owner."""
        return self

    def ownsWidget(self, widget):
        """True when `widget` is this dock or lives inside it."""
        if widget is None:
            return False
        with suppress(Exception):
            return widget is self or self.isAncestorOf(widget)
        return False

    def ownsMapTool(self, tool):
        return False

    def canActivate(self):
        """False when the dock has nothing to show, so clicking around in it
        does not take the canvas away from whoever is actually using it."""
        return True

    def clearMapHighlights(self):
        """Remove the graphics from the canvas. Must not lose the state needed
        to draw them again."""

    def redrawMapHighlights(self):
        """Draw the highlights again from the state kept by the dock."""

    def suspendMapHighlights(self):
        self.clearMapHighlights()
        self.applyHighlightAccent(False)

    def restoreMapHighlights(self):
        self.redrawMapHighlights()
        self.applyHighlightAccent(True)

    def applyHighlightAccent(self, isActive):
        from .qgisred_ui_utils import QGISRedUIUtils

        accent = self.highlightActiveAccent if isActive else self.highlightInactiveAccent
        with suppress(Exception):
            QGISRedUIUtils.applyDockStyle(self, accent)

    # -- Qt events that mean "the user is working here" --------------------
    def focusInEvent(self, event):
        self.notifyHighlightActivated()
        super(QGISRedHighlightOwnerMixin, self).focusInEvent(event)

    def mousePressEvent(self, event):
        self.notifyHighlightActivated()
        super(QGISRedHighlightOwnerMixin, self).mousePressEvent(event)

    def showEvent(self, event):
        super(QGISRedHighlightOwnerMixin, self).showEvent(event)
        self.notifyHighlightActivated()

    def hideEvent(self, event):
        # A hidden dock must not leave graphics behind on the canvas, whether or
        # not it ever got registered (tabifying one away used to orphan them).
        manager = self.highlightManager()
        if manager is None:
            with suppress(Exception):
                self.clearMapHighlights()
        else:
            with suppress(Exception):
                manager.suspend(self)
        super(QGISRedHighlightOwnerMixin, self).hideEvent(event)


class QGISRedDockActivationMixin:
    """Turns clicking, focusing or showing a dock into one `activated` signal.

    For docks whose highlights are arbitrated by a Section rather than by
    themselves (Profile, TimeSeries): they cannot implement the owner protocol
    above, but they still have to say when the user turned to them, and the
    answer to "what counts as turning to a dock" belongs in one place.

    Mix in *before* QDockWidget, and declare the signal in the dock's own class
    body — PyQt only registers signals found on the class it is building, not
    on plain-Python bases:

        class MyDock(QGISRedDockActivationMixin, QDockWidget):
            activated = pyqtSignal()
    """

    def emitActivated(self):
        with suppress(Exception):
            self.activated.emit()

    def eventFilter(self, obj, event):
        with suppress(Exception):
            if event is not None and event.type() == QEvent.Type.MouseButtonPress:
                self.emitActivated()
        return super(QGISRedDockActivationMixin, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        self.emitActivated()
        super(QGISRedDockActivationMixin, self).mousePressEvent(event)

    def focusInEvent(self, event):
        self.emitActivated()
        super(QGISRedDockActivationMixin, self).focusInEvent(event)

    def showEvent(self, event):
        super(QGISRedDockActivationMixin, self).showEvent(event)
        self.emitActivated()


class QGISRedDelegatedHighlightOwner:
    """Owner whose highlights are managed by a Section rather than by the dock.

    TimeSeries and Profile keep their highlight state in analysis_section /
    profile_section, spread over a variable number of docks that behave as one
    subject: opening a second profile panel does not erase the first one's path.
    So the owner is the *family*, not a single dock — `widgets` returns the docks
    currently belonging to it, and suspend/restore are the section callables that
    already did this work under the old cede/reclaim names.
    """

    def __init__(self, key, widgets, suspend, restore, ownedTools=None, accent=None, canActivate=None):
        self.highlightOwnerKey = key
        self._widgets = widgets
        self._suspend = suspend
        self._restore = restore
        self._ownedTools = ownedTools
        self._accent = accent
        self._canActivate = canActivate

    def highlightWidget(self):
        # A family outlives any single dock, so nothing here auto-unregisters it.
        return None

    def docks(self):
        with suppress(Exception):
            return list(self._widgets() or [])
        return []

    def ownsWidget(self, widget):
        if widget is None:
            return False
        for dock in self.docks():
            if dock is None:
                continue
            with suppress(Exception):
                if dock is widget or dock.isAncestorOf(widget):
                    return True
        return False

    def ownsMapTool(self, tool):
        if tool is None or self._ownedTools is None:
            return False
        with suppress(Exception):
            return any(t is not None and t is tool for t in (self._ownedTools() or []))
        return False

    def canActivate(self):
        if self._canActivate is None:
            return True
        with suppress(Exception):
            return bool(self._canActivate())
        return False

    def suspendMapHighlights(self):
        with suppress(Exception):
            self._suspend()
        self.applyHighlightAccent(False)

    def restoreMapHighlights(self):
        with suppress(Exception):
            self._restore()
        self.applyHighlightAccent(True)

    def applyHighlightAccent(self, isActive):
        if self._accent is None:
            return
        with suppress(Exception):
            self._accent(isActive)


class QGISRedHighlightManager:
    """Decides which registered owner may show highlights on the canvas."""

    def __init__(self, iface=None, pluginMapTools=None):
        self.iface = iface
        # Callable returning the plugin's live map tools (usually
        # `lambda: (self.myMapTools or {}).values()`), so an editing tool with
        # no owner can still be told apart from a native one.
        self._pluginMapTools = pluginMapTools
        self._owners = []
        self._active = None
        # Owners held by identity, not by id(): a collected owner's id can be
        # handed to the next object and revive somebody else's suspended state.
        self._suspended = []
        self._busy = False
        self._connected = False
        self._editingWatchedLayers = []

    # -- Registry ----------------------------------------------------------
    def isRegistered(self, owner):
        return any(o is owner for o in self._owners)

    def register(self, owner):
        if owner is None or self.isRegistered(owner):
            return owner
        self._owners.append(owner)
        with suppress(Exception):
            owner._highlightManager = self
        widget = self._ownerWidget(owner)
        if widget is not None:
            with suppress(Exception):
                widget.destroyed.connect(lambda *_a, o=owner: self.unregister(o))
        self._connectSignals()
        return owner

    def unregister(self, owner):
        if owner is None:
            return
        self._owners = [o for o in self._owners if o is not owner]
        self._suspended = [o for o in self._suspended if o is not owner]
        if self._active is owner:
            self._active = None

    def owners(self):
        return list(self._owners)

    def ownerByKey(self, key):
        return next((o for o in self._owners if getattr(o, "highlightOwnerKey", None) == key), None)

    def activateByKey(self, key):
        self.activate(self.ownerByKey(key))

    def activeOwner(self):
        return self._active

    def isSuspended(self, owner):
        return any(o is owner for o in self._suspended)

    # -- Arbitration -------------------------------------------------------
    def activate(self, owner):
        """Give `owner` the canvas: restore its highlights, suspend everyone else."""
        if owner is None or not self.isRegistered(owner) or self._busy:
            return
        if self._active is owner and not self.isSuspended(owner):
            return
        with suppress(Exception):
            if not owner.canActivate():
                return
        self._busy = True
        try:
            for other in self._owners:
                if other is not owner:
                    self._suspendOwner(other)
            self._active = owner
            self._suspended = [o for o in self._suspended if o is not owner]
            with suppress(Exception):
                owner.restoreMapHighlights()
        finally:
            self._busy = False

    def claim(self, owner):
        """The owner has just drawn on the canvas of its own accord.

        Drawing *is* a claim on the canvas, and it is the only one some docks
        ever make: a dock that could not activate while it had nothing to show
        (see canActivate) gets no further focus event once its filter finally
        matches something. So ownership is taken here without asking the owner
        to redraw what it has already drawn, and without consulting canActivate
        — the graphics on screen are the proof.
        """
        if owner is None or not self.isRegistered(owner) or self._busy:
            return
        self._busy = True
        try:
            for other in self._owners:
                if other is not owner:
                    self._suspendOwner(other)
            self._active = owner
            self._suspended = [o for o in self._suspended if o is not owner]
            with suppress(Exception):
                owner.applyHighlightAccent(True)
        finally:
            self._busy = False

    def suspend(self, owner):
        """Suspend a single owner (its dock was hidden, say) without handing
        ownership to anybody else."""
        if owner is None or self._busy:
            return
        if not self.isRegistered(owner):
            # Already unregistered — still clear its graphics, but keep it out
            # of the bookkeeping.
            with suppress(Exception):
                owner.suspendMapHighlights()
            return
        self._busy = True
        try:
            self._suspendOwner(owner)
        finally:
            self._busy = False

    def suspendAll(self, reason=""):
        """Nobody owns the canvas right now — a native selection tool or one of
        the plugin's editing tools took it. The active owner is remembered so
        clicking back into its dock brings its highlights back."""
        if self._busy:
            return
        self._busy = True
        try:
            for owner in self._owners:
                self._suspendOwner(owner)
        finally:
            self._busy = False

    def _suspendOwner(self, owner):
        if self.isSuspended(owner):
            return
        self._suspended.append(owner)
        with suppress(Exception):
            owner.suspendMapHighlights()

    # -- Map tool classification ------------------------------------------
    def classifyMapTool(self, tool):
        """Return (role, owner). `owner` is set only for MapToolRole.OWNED."""
        if tool is None:
            return MapToolRole.NAVIGATION, None
        for owner in self._owners:
            with suppress(Exception):
                if owner.ownsMapTool(tool):
                    return MapToolRole.OWNED, owner
        if _isPluginMapTool(tool) or self._isKnownPluginTool(tool):
            return MapToolRole.PLUGIN_OTHER, None
        if _isNativeEditingTool(tool):
            # Digitizing changes the very geometry the highlights describe.
            return MapToolRole.EDITING, None
        if self._isNativeSelectionTool(tool):
            return MapToolRole.SELECTION, None
        return _nativeToolRole(tool), None

    def _isKnownPluginTool(self, tool):
        if self._pluginMapTools is None:
            return False
        with suppress(Exception):
            return any(t is tool for t in (self._pluginMapTools() or []))
        return False

    def _isNativeSelectionTool(self, tool):
        """Recognise QGIS's select and identify tools by their toolbar action.

        Their classes are not wrapped for Python, so the tool object arrives as
        a plain QgsMapTool and its name gives nothing away. The QAction that the
        toolbar button installed on it is the one handle left, and QgisInterface
        publishes the same action objects.
        """
        action = None
        with suppress(Exception):
            action = tool.action()
        if action is None or self.iface is None:
            return False
        for name in _SELECTION_IFACE_ACTIONS:
            with suppress(Exception):
                getter = getattr(self.iface, name, None)
                if getter is not None and getter() is action:
                    return True
        return False

    # -- Signals -----------------------------------------------------------
    def _connectSignals(self):
        if self._connected:
            return
        from qgis.PyQt.QtWidgets import QApplication

        with suppress(Exception):
            QApplication.instance().focusChanged.connect(self.onFocusChanged)
        with suppress(Exception):
            self.iface.mapCanvas().mapToolSet.connect(self.onMapToolSet)
        self._connected = True
        self.watchLayerEditing()

    def watchLayerEditing(self):
        """Suspend the highlights as soon as a layer is put into edit mode.

        Toggling editing does not change the map tool, so mapToolSet never
        fires; without this, a highlight would sit on top of geometry the user
        is about to move. Re-run whenever the layer set changes.
        """
        with suppress(Exception):
            from qgis.core import QgsProject

            QgsProject.instance().layersAdded.connect(self._onLayersAdded)
        for layer in self._projectVectorLayers():
            if any(watched is layer for watched in self._editingWatchedLayers):
                continue
            with suppress(Exception):
                layer.editingStarted.connect(self.onLayerEditingStarted)
                self._editingWatchedLayers.append(layer)

    def _projectVectorLayers(self):
        with suppress(Exception):
            from qgis.core import QgsProject, QgsVectorLayer

            return [
                layer for layer in QgsProject.instance().mapLayers().values()
                if isinstance(layer, QgsVectorLayer)
            ]
        return []

    def _onLayersAdded(self, _layers=None):
        self.watchLayerEditing()

    def onLayerEditingStarted(self):
        self.suspendAll(MapToolRole.EDITING)

    def _unwatchLayerEditing(self):
        with suppress(Exception):
            from qgis.core import QgsProject

            QgsProject.instance().layersAdded.disconnect(self._onLayersAdded)
        for layer in list(self._editingWatchedLayers):
            with suppress(Exception):
                layer.editingStarted.disconnect(self.onLayerEditingStarted)
        self._editingWatchedLayers = []

    def onFocusChanged(self, old, now):
        if now is None:
            return
        owner = self.ownerForWidget(now)
        if owner is not None:
            self.activate(owner)

    def onMapToolSet(self, tool, oldTool=None):
        role, owner = self.classifyMapTool(tool)
        if role == MapToolRole.OWNED:
            self.activate(owner)
        elif role in (MapToolRole.PLUGIN_OTHER, MapToolRole.EDITING, MapToolRole.SELECTION):
            self.suspendAll(role)
        # NAVIGATION: panning or zooming is not a change of subject.

    def ownerForWidget(self, widget):
        if widget is None:
            return None
        for owner in self._owners:
            with suppress(Exception):
                if owner.ownsWidget(widget):
                    return owner
        return None

    @staticmethod
    def _ownerWidget(owner):
        with suppress(Exception):
            return owner.highlightWidget()
        return None

    # -- Teardown ----------------------------------------------------------
    def shutdown(self):
        from qgis.PyQt.QtWidgets import QApplication

        with suppress(Exception):
            QApplication.instance().focusChanged.disconnect(self.onFocusChanged)
        with suppress(Exception):
            self.iface.mapCanvas().mapToolSet.disconnect(self.onMapToolSet)
        self._unwatchLayerEditing()
        self._connected = False
        for owner in list(self._owners):
            with suppress(Exception):
                owner.suspendMapHighlights()
        self._owners = []
        self._suspended = []
        self._active = None
