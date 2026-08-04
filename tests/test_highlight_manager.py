# -*- coding: utf-8 -*-
"""Arbitration of map highlights between docks."""
import pytest

from QGISRed.tools.utils.qgisred_highlight_manager import (
    MapToolRole,
    QGISRedDelegatedHighlightOwner,
    QGISRedHighlightManager,
)


class FakeOwner:
    """Minimal owner: counts how many times it was asked to hide/show."""

    def __init__(self, key, tools=None, canActivate=True):
        self.highlightOwnerKey = key
        self.suspends = 0
        self.restores = 0
        self.shown = False
        self._tools = tools or []
        self._canActivate = canActivate

    def highlightWidget(self):
        return None

    def ownsWidget(self, widget):
        return False

    def ownsMapTool(self, tool):
        return any(t is tool for t in self._tools)

    def canActivate(self):
        return self._canActivate

    def suspendMapHighlights(self):
        self.suspends += 1
        self.shown = False

    def restoreMapHighlights(self):
        self.restores += 1
        self.shown = True


class FakeWidget:
    """Stands in for a dock: knows its own children for isAncestorOf."""

    def __init__(self, children=()):
        self._children = list(children)

    def isAncestorOf(self, widget):
        return widget in self._children


# Native tools, named as QGIS names them.
class QgsMapToolPan:
    pass


class QgsMapToolZoom:
    pass


class QgsMapToolIdentify:
    pass


class _FakeIface:
    """QgisInterface stand-in exposing the action getters the manager asks for.

    Any action name not passed in returns a fresh object, which is what an
    unrelated QGIS action looks like: never identical to the tool's own.
    """

    def __init__(self, **actions):
        self._actions = actions

    def __getattr__(self, name):
        if not name.startswith("action"):
            raise AttributeError(name)
        value = self._actions.get(name, object())
        return lambda: value


class QGISRedIdentifyFeature(QgsMapToolIdentify):
    """Derives from the native identify tool, exactly like the real one."""
    __module__ = "QGISRed.tools.map_tools.qgisred_identifyFeature"


class QGISRedMoveNodes:
    """An editing tool: belongs to the plugin but owns no dock."""
    __module__ = "QGISRed.tools.map_tools.qgisred_moveNodes"


@pytest.fixture
def manager():
    # iface=None: connecting to the canvas signal fails and is suppressed, which
    # is what we want — these tests drive the handlers directly.
    return QGISRedHighlightManager(iface=None)


def test_activating_one_owner_suspends_the_others(manager):
    a, b, c = FakeOwner("a"), FakeOwner("b"), FakeOwner("c")
    for owner in (a, b, c):
        manager.register(owner)

    manager.activate(a)

    assert a.shown is True
    assert b.suspends == 1 and c.suspends == 1
    assert manager.activeOwner() is a


def test_reactivating_the_active_owner_does_nothing(manager):
    a, b = manager.register(FakeOwner("a")), manager.register(FakeOwner("b"))

    manager.activate(a)
    manager.activate(a)

    assert a.restores == 1
    assert b.suspends == 1


def test_suspended_owner_is_restored_when_activated_again(manager):
    a, b = manager.register(FakeOwner("a")), manager.register(FakeOwner("b"))

    manager.activate(a)
    manager.activate(b)
    manager.activate(a)

    assert a.restores == 2
    assert a.suspends == 1
    assert a.shown is True and b.shown is False


def test_suspend_all_keeps_the_active_owner_so_it_can_come_back(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.suspendAll("native select")

    assert a.shown is False
    assert manager.activeOwner() is a
    assert manager.isSuspended(a) is True

    manager.activate(a)
    assert a.shown is True


def test_owner_that_cannot_activate_does_not_take_the_canvas(manager):
    a = manager.register(FakeOwner("a"))
    empty = manager.register(FakeOwner("empty", canActivate=False))
    manager.activate(a)

    manager.activate(empty)

    assert empty.restores == 0
    assert a.shown is True
    assert manager.activeOwner() is a


def test_unregister_drops_the_owner_from_arbitration(manager):
    a, b = manager.register(FakeOwner("a")), manager.register(FakeOwner("b"))
    manager.activate(a)

    manager.unregister(a)
    manager.activate(b)

    assert a.suspends == 0
    assert manager.owners() == [b]
    assert manager.ownerByKey("a") is None


def test_drawing_claims_the_canvas_without_a_redraw(manager):
    """Regression: a dock whose highlight appears while editing a filter gets no
    focus event at that moment, so drawing has to be a claim of its own."""
    a = manager.register(FakeOwner("a"))
    drawer = manager.register(FakeOwner("drawer"))
    manager.activate(a)

    manager.claim(drawer)

    assert a.shown is False and a.suspends == 1
    assert manager.activeOwner() is drawer
    assert manager.isSuspended(drawer) is False
    # It already drew — asking it to draw again would be wasted work.
    assert drawer.restores == 0


def test_claiming_ignores_can_activate(manager):
    """The graphics on screen are the proof; canActivate is a prediction and
    would veto the very dock that just drew."""
    a = manager.register(FakeOwner("a"))
    drawer = manager.register(FakeOwner("drawer", canActivate=False))
    manager.activate(a)

    manager.claim(drawer)

    assert manager.activeOwner() is drawer
    assert a.shown is False


def test_claiming_from_an_unregistered_owner_is_ignored(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.claim(FakeOwner("orphan"))

    assert manager.activeOwner() is a
    assert a.shown is True


def test_claiming_during_arbitration_does_not_re_enter(manager):
    """restoreMapHighlights draws, and drawing claims — that must not restart
    the arbitration from inside it."""
    class ClaimingOwner(FakeOwner):
        def restoreMapHighlights(self):
            super().restoreMapHighlights()
            manager.claim(self)

    owner = manager.register(ClaimingOwner("claiming"))
    other = manager.register(FakeOwner("other"))

    manager.activate(owner)

    assert owner.restores == 1
    assert other.suspends == 1
    assert manager.activeOwner() is owner


def test_a_suspended_owner_can_be_told_it_is_suspended(manager):
    """Docks guard their reactive redraws with this, so it must stay true for
    exactly as long as the arbiter is holding the canvas away from them."""
    a, b = manager.register(FakeOwner("a")), manager.register(FakeOwner("b"))

    manager.activate(a)
    assert manager.isSuspended(b) is True
    assert manager.isSuspended(a) is False

    manager.activate(b)
    assert manager.isSuspended(a) is True
    assert manager.isSuspended(b) is False


def test_a_suspended_owner_that_redraws_takes_the_canvas_back(manager):
    """The counterpart of the guard: a claim from a suspended owner is honoured.
    That is why the guard has to live in the docks' reactive paths — the arbiter
    cannot tell a user-driven redraw from an incidental one."""
    a = manager.register(FakeOwner("a"))
    b = manager.register(FakeOwner("b"))
    manager.activate(a)

    manager.claim(b)

    assert manager.activeOwner() is b
    assert manager.isSuspended(a) is True


def test_suspending_an_unregistered_owner_still_clears_its_graphics(manager):
    """A dock hidden after closing has already been unregistered; its graphics
    must still go, without leaving it in the suspended bookkeeping."""
    orphan = FakeOwner("orphan")

    manager.suspend(orphan)

    assert orphan.suspends == 1
    assert manager.isSuspended(orphan) is False


def test_owner_lookup_by_key_and_by_focused_widget(manager):
    child = object()
    dock = FakeWidget(children=[child])

    owner = manager.register(QGISRedDelegatedHighlightOwner(
        "family", lambda: [dock], lambda: None, lambda: None))

    assert manager.ownerByKey("family") is owner
    assert manager.ownerForWidget(dock) is owner
    assert manager.ownerForWidget(child) is owner
    assert manager.ownerForWidget(object()) is None


# -- Map tool classification -------------------------------------------------

def test_plugin_identify_tool_is_owned_not_native_selection(manager):
    """Regression: QGISRedIdentifyFeature subclasses QgsMapToolIdentify, so the
    plugin check has to run before any native isinstance test."""
    tool = QGISRedIdentifyFeature()
    owner = manager.register(FakeOwner("elementExplorer", tools=[tool]))

    role, matched = manager.classifyMapTool(tool)

    assert role == MapToolRole.OWNED
    assert matched is owner


def test_plugin_tool_without_owner_is_plugin_other(manager):
    manager.register(FakeOwner("a"))

    role, owner = manager.classifyMapTool(QGISRedMoveNodes())

    assert role == MapToolRole.PLUGIN_OTHER
    assert owner is None


@pytest.mark.parametrize("tool", [QgsMapToolPan(), QgsMapToolZoom(), None])
def test_navigation_tools_are_neutral(manager, tool):
    assert manager.classifyMapTool(tool)[0] == MapToolRole.NAVIGATION


def test_native_identify_is_a_competing_tool(manager):
    """QgsMapToolIdentify *is* wrapped for Python, so its own name identifies it."""
    assert manager.classifyMapTool(QgsMapToolIdentify())[0] == MapToolRole.SELECTION


@pytest.mark.parametrize("actionName", [
    "actionSelect",
    "actionSelectRectangle",
    "actionSelectPolygon",
    "actionSelectFreehand",
    "actionSelectRadius",
    "actionIdentify",
])
def test_native_select_is_recognised_by_its_toolbar_action(actionName):
    """Regression: QgsMapToolSelect is not exposed to Python, so sip hands it
    over as a bare QgsMapTool and the class name says nothing. Only the QAction
    the toolbar installed on it gives it away."""
    action = object()
    iface = _FakeIface(**{actionName: action})
    manager = QGISRedHighlightManager(iface=iface)

    class UnwrappedSelectTool:
        """What sip actually returns: no usable name."""
        __name__ = "QgsMapTool"

        def action(self):
            return action

    assert manager.classifyMapTool(UnwrappedSelectTool())[0] == MapToolRole.SELECTION


def test_a_tool_carrying_an_unrelated_action_is_still_navigation():
    iface = _FakeIface(actionSelect=object())
    manager = QGISRedHighlightManager(iface=iface)

    class MeasureTool:
        def action(self):
            return object()

    assert manager.classifyMapTool(MeasureTool())[0] == MapToolRole.NAVIGATION


def test_plugin_tools_provider_recognises_tools_it_cannot_name(manager):
    """A plugin tool whose module does not match the naming rule is still told
    apart from a native one through the live myMapTools dictionary."""
    class OddlyNamedTool:
        __module__ = "somewhere.else"

    tool = OddlyNamedTool()
    manager._pluginMapTools = lambda: [tool]

    assert manager.classifyMapTool(tool)[0] == MapToolRole.PLUGIN_OTHER


# -- The mapToolSet handler --------------------------------------------------

def test_panning_leaves_the_highlights_alone(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.onMapToolSet(QgsMapToolPan())

    assert a.shown is True
    assert a.suspends == 0


def test_native_select_suspends_everything():
    action = object()
    manager = QGISRedHighlightManager(iface=_FakeIface(actionSelect=action))
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    class UnwrappedSelectTool:
        def action(self):
            return action

    manager.onMapToolSet(UnwrappedSelectTool())

    assert a.shown is False


def test_native_identify_suspends_everything(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.onMapToolSet(QgsMapToolIdentify())

    assert a.shown is False


def test_native_digitizing_tool_suspends_everything(manager, monkeypatch):
    """QgsMapToolAddFeature and the vertex tool are not exposed to Python
    either, but every editing tool descends from QgsMapToolEdit, which is."""
    import sys

    class QgsMapToolEdit:
        pass

    class QgsMapToolDigitizeFeature(QgsMapToolEdit):
        """What sip returns for QGIS's add-feature tool."""

    monkeypatch.setattr(sys.modules["qgis.gui"], "QgsMapToolEdit", QgsMapToolEdit, raising=False)
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    role, _owner = manager.classifyMapTool(QgsMapToolDigitizeFeature())
    manager.onMapToolSet(QgsMapToolDigitizeFeature())

    assert role == MapToolRole.EDITING
    assert a.shown is False


def test_plugin_editing_tool_suspends_everything(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.onMapToolSet(QGISRedMoveNodes())

    assert a.shown is False


def test_putting_a_layer_into_edit_mode_suspends_everything(manager):
    """Toggling editing never changes the map tool, so the layer signal is the
    only warning that the geometry under the highlights is about to move."""
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.onLayerEditingStarted()

    assert a.shown is False
    assert manager.activeOwner() is a  # comes back when the dock is refocused


def test_a_tool_owned_by_another_dock_hands_the_canvas_over(manager):
    tool = QGISRedIdentifyFeature()
    a = manager.register(FakeOwner("a"))
    b = manager.register(FakeOwner("b", tools=[tool]))
    manager.activate(a)

    manager.onMapToolSet(tool)

    assert manager.activeOwner() is b
    assert b.shown is True and a.shown is False


def test_focus_moving_into_a_dock_hands_the_canvas_over(manager):
    child = object()
    dock = FakeWidget(children=[child])
    a = manager.register(FakeOwner("a"))
    b = manager.register(QGISRedDelegatedHighlightOwner(
        "b", lambda: [dock], lambda: None, lambda: None))
    manager.activate(a)

    manager.onFocusChanged(None, child)

    assert manager.activeOwner() is b
    assert a.shown is False


def test_focus_leaving_to_the_canvas_changes_nothing(manager):
    a = manager.register(FakeOwner("a"))
    manager.activate(a)

    manager.onFocusChanged(None, object())

    assert a.shown is True
    assert manager.activeOwner() is a


# -- Re-entrancy -------------------------------------------------------------

def test_restore_that_sets_a_map_tool_does_not_re_enter(manager):
    """Restoring an owner re-arms its map tool, which fires mapToolSet again.
    That second pass must not run the arbitration a second time."""
    tool = QGISRedIdentifyFeature()

    class RearmingOwner(FakeOwner):
        def restoreMapHighlights(self):
            super().restoreMapHighlights()
            manager.onMapToolSet(tool)

    owner = manager.register(RearmingOwner("rearming", tools=[tool]))
    other = manager.register(FakeOwner("other"))

    manager.activate(owner)

    assert owner.restores == 1
    assert other.suspends == 1


# -- Teardown ----------------------------------------------------------------

def test_shutdown_clears_the_registry_and_hides_everything(manager):
    a, b = manager.register(FakeOwner("a")), manager.register(FakeOwner("b"))
    manager.activate(a)

    manager.shutdown()

    assert a.shown is False and b.shown is False
    assert manager.owners() == []
    assert manager.activeOwner() is None
