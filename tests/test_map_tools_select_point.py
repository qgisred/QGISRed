# -*- coding: utf-8 -*-
"""Right-click / double-click routing of QGISRedSelectPointTool."""
import sys
from unittest.mock import MagicMock

import pytest

from .conftest import REAL_QGIS, _qt_stub

if REAL_QGIS:
    from qgis.core import QgsPointXY
    from qgis.gui import QgsMapCanvas
    from QGISRed.compat import QAction
else:
    # Replacing the real class would leave every module imported afterwards seeing
    # a stub, so it is only done when there is no real QGIS to subclass.
    sys.modules['qgis.gui'].QgsMapTool = _qt_stub("QgsMapTool")

from QGISRed.tools.map_tools import qgisred_selectPoint as sp  # noqa: E402
from QGISRed.tools.map_tools.qgisred_selectPoint import (  # noqa: E402
    QGISRedSelectPointTool, SelectPointType,
)


class _StubPoint:
    def __init__(self, x, y=None):
        if y is None:
            x, y = x.x(), x.y()
        self._x, self._y = float(x), float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __eq__(self, other):
        return isinstance(other, _StubPoint) and (self._x, self._y) == (other._x, other._y)

    def __repr__(self):
        return f"_StubPoint({self._x}, {self._y})"


# The tool feeds its points to QgsPointXY, which only accepts the real thing.
_Point = QgsPointXY if REAL_QGIS else _StubPoint


def _match(point):
    m = MagicMock()
    m.isValid.return_value = point is not None
    m.point.return_value = point
    return m


def _makeTool(type, double_click_callback=None, context_callback=None):
    if REAL_QGIS:
        # Built for real: a tool created with __new__ has no C++ side, and the real
        # canvas rejects it as soon as something like unsetMapTool() touches it.
        parent = MagicMock(isUnloading=False)
        canvas = QgsMapCanvas()
        parent.iface.mapCanvas.return_value = canvas
        tool = QGISRedSelectPointTool(
            QAction("test"), parent, MagicMock(), type=type,
            context_callback=context_callback, double_click_callback=double_click_callback,
        )
        tool._testCanvas = canvas  # the markers live on it; keep it from being collected
        # QgsMapTool keeps its own reference to the canvas; this attribute is only what
        # the plugin calls unsetMapTool() on, and the tests watch those calls.
        tool.canvas = MagicMock()
        # The real toMapCoordinates() would choke on the mocked event position, and
        # the handler swallows exceptions, so the failure would be silent.
        tool.toMapCoordinates = MagicMock()
    else:
        tool = QGISRedSelectPointTool.__new__(QGISRedSelectPointTool)
        tool.type = type
        tool.parent = MagicMock(isUnloading=False)
        tool.iface = MagicMock()
        tool.canvas = tool.iface.mapCanvas.return_value
        tool.method = MagicMock()
        tool.pass_modifiers = False
        tool.move_callback = None
        tool.context_callback = context_callback
        tool.double_click_callback = double_click_callback
        tool.show_snap_marker = True
        tool._ignore_next_release = False
        tool._lastClickActed = False
    tool.startMarker = MagicMock()
    tool.endMarker = MagicMock()
    tool.firstPoint = None
    tool.objectSnapped = None
    tool.snapper = MagicMock()
    tool.snapper.snapToMap.return_value = _match(None)
    return tool


def _event(button=None, pos=(0, 0)):
    e = MagicMock()
    e.button.return_value = button
    e.pos.return_value = pos
    return e


@pytest.fixture(autouse=True)
def _identityPointXY(monkeypatch):
    monkeypatch.setattr(sp, "QgsPointXY", _Point)


LEFT = sp.Qt.MouseButton.LeftButton
RIGHT = sp.Qt.MouseButton.RightButton


class TestDoubleClick:
    """A double-click is a single gesture: one action, no leftover release."""

    @pytest.mark.parametrize("type", [SelectPointType.PointLine, SelectPointType.TwoPoints])
    def test_reusesFirstClickPoint(self, type):
        callback = MagicMock()
        tool = _makeTool(type, double_click_callback=callback)
        tool.firstPoint = _Point(10, 20)
        # Snapping again would answer with the segment under the cursor, not the node.
        tool.snapper.snapToMap.return_value = _match(_Point(99, 99))

        tool.canvasDoubleClickEvent(_event(LEFT))

        callback.assert_called_once_with(_Point(10, 20), LEFT)
        assert tool.firstPoint is None

    def test_snapsWhenNoFirstPoint(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Point, double_click_callback=callback)
        tool.snapper.snapToMap.return_value = _match(_Point(5, 6))

        tool.canvasDoubleClickEvent(_event(LEFT))

        callback.assert_called_once_with(_Point(5, 6), LEFT)

    @pytest.mark.parametrize("type", [SelectPointType.PointLine, SelectPointType.TwoPoints])
    def test_ignoredWhenFirstClickCompletedThePair(self, type):
        callback = MagicMock()
        tool = _makeTool(type, double_click_callback=callback)
        tool.snapper.snapToMap.return_value = _match(_Point(99, 99))

        tool.canvasDoubleClickEvent(_event(LEFT))

        callback.assert_not_called()

    def test_ignoredWhenFirstClickAlreadyActed(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Line, double_click_callback=callback)
        tool.method.return_value = True
        tool.objectSnapped = _match(_Point(5, 6))
        tool.snapper.snapToMap.return_value = _match(_Point(5, 6))
        tool.deactivate = MagicMock()
        tool.activate = MagicMock()

        tool.canvasReleaseEvent(_event(LEFT))
        tool.canvasDoubleClickEvent(_event(LEFT))

        tool.method.assert_called_once_with(_Point(5, 6))
        callback.assert_not_called()

    def test_firesWhenFirstClickDidNothing(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Line, double_click_callback=callback)
        tool.method.return_value = False
        tool.objectSnapped = _match(_Point(5, 6))
        tool.snapper.snapToMap.return_value = _match(_Point(5, 6))
        tool.deactivate = MagicMock()
        tool.activate = MagicMock()

        tool.canvasReleaseEvent(_event(LEFT))
        tool.canvasDoubleClickEvent(_event(LEFT))

        callback.assert_called_once_with(_Point(5, 6), LEFT)

    def test_ignoredWhenNothingSnapped(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Point, double_click_callback=callback)

        tool.canvasDoubleClickEvent(_event(LEFT))

        callback.assert_not_called()

    @pytest.mark.parametrize("callback", [None, MagicMock()])
    def test_trailingReleaseIsSwallowed(self, callback):
        tool = _makeTool(SelectPointType.Line, double_click_callback=callback)
        tool.objectSnapped = _match(_Point(1, 2))

        tool.canvasDoubleClickEvent(_event(LEFT))
        assert tool._ignore_next_release
        tool.canvasReleaseEvent(_event(LEFT))

        tool.method.assert_not_called()
        assert not tool._ignore_next_release


class TestRightClick:
    """Right-click on a single-point tool goes to the context callback."""

    def test_forwardsSnappedPoint(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Line, context_callback=callback)
        tool.objectSnapped = _match(_Point(3, 4))

        tool.canvasReleaseEvent(_event(RIGHT))

        callback.assert_called_once_with(_Point(3, 4))
        assert tool.objectSnapped is None
        tool.method.assert_not_called()

    def test_forwardsNoneWhenNothingSnapped(self):
        callback = MagicMock()
        tool = _makeTool(SelectPointType.Line, context_callback=callback)

        tool.canvasReleaseEvent(_event(RIGHT))

        callback.assert_called_once_with(None)
        tool.canvas.unsetMapTool.assert_not_called()

    @pytest.mark.parametrize("type", [SelectPointType.PointLine, SelectPointType.TwoPoints])
    @pytest.mark.parametrize("firstPoint", [None, _Point(1, 1)])
    def test_emptySpaceLeavesTwoStepTools(self, type, firstPoint):
        tool = _makeTool(type)
        tool.firstPoint = firstPoint

        tool.canvasReleaseEvent(_event(RIGHT))

        tool.canvas.unsetMapTool.assert_called_once_with(tool)
        tool.method.assert_not_called()

    def test_twoStepToolsCallMethodWithoutSecondPoint(self):
        tool = _makeTool(SelectPointType.PointLine)
        tool.objectSnapped = _match(_Point(7, 8))
        tool.deactivate = MagicMock()
        tool.activate = MagicMock()

        tool.canvasReleaseEvent(_event(RIGHT))

        tool.method.assert_called_once_with(_Point(7, 8), None)
