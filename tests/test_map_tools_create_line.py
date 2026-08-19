# -*- coding: utf-8 -*-
import pytest
import sys
import os
from unittest.mock import MagicMock

from .conftest import REAL_QGIS


# ---------------------------------------------------------------------------
# Stand-ins used only when the suite runs against the mocked QGIS.
#
# QgsMapTool must be a real Python class (not a MagicMock instance) so that
# QGISRedCreateLineTool can subclass it without the MagicMock metaclass
# interfering with class attribute lookup.
# ---------------------------------------------------------------------------
class _StubPoint:
    def __init__(self, x, y):
        self._x = float(x)
        self._y = float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y

    def __eq__(self, other):
        return isinstance(other, _StubPoint) and self._x == other._x and self._y == other._y

    def __repr__(self):
        return f"_StubPoint({self._x}, {self._y})"


class _StubMapTool:
    def __init__(self, *args, **kwargs):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def setAction(self, action):
        pass

    def toMapCoordinates(self, pos):
        return MagicMock()


class _StubVertexMarker:
    ICON_BOX = 'ICON_BOX'
    ICON_X = 'ICON_X'
    ICON_CROSS = 'ICON_CROSS'

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return MagicMock()


class _StubRubberBand:
    ICON_CROSS = 'ICON_CROSS'

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        return MagicMock()


def _configureSharedMocks():
    """Put the stubs on the mocks conftest already installed.

    Replacing the sys.modules entries outright -- what this module used to do --
    left every module imported afterwards seeing mocks, which silently disabled
    the real-QGIS run for half the suite.
    """
    gui = sys.modules['qgis.gui']
    gui.QgsMapTool = _StubMapTool
    gui.QgsVertexMarker = _StubVertexMarker
    gui.QgsRubberBand = _StubRubberBand

    core = sys.modules['qgis.core']
    core.QgsPointXY = _StubPoint
    core.QgsSnappingConfig.Vertex = 1
    core.QgsSnappingConfig.Segment = 2
    core.QgsSnappingConfig.VertexAndSegment = 3
    core.QgsWkbTypes.LineGeometry = 2
    core.QgsWkbTypes.PointGeometry = 1

    qt = sys.modules['qgis.PyQt.QtCore'].Qt
    qt.MouseButton.LeftButton = 1
    qt.MouseButton.RightButton = 2
    qt.PenStyle.SolidLine = 1
    qt.PenStyle.DashLine = 2


if REAL_QGIS:
    from qgis.core import QgsPointXY as _Point
    from qgis.gui import QgsMapCanvas
    from qgis.PyQt.QtCore import Qt
    from QGISRed.compat import QAction
    LEFT_BUTTON = Qt.MouseButton.LeftButton
    RIGHT_BUTTON = Qt.MouseButton.RightButton
else:
    _Point = _StubPoint
    LEFT_BUTTON, RIGHT_BUTTON = 1, 2
    _configureSharedMocks()
    # The stubs must be in place before the tool binds its module-level names, so
    # drop a copy imported by an earlier test module instead of reusing it.
    sys.modules.pop('QGISRed.tools.map_tools.qgisred_createLineTool', None)

from QGISRed.tools.map_tools.qgisred_createLineTool import QGISRedCreateLineTool  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------
def _make_tool(cls=QGISRedCreateLineTool, canvas_width=100.0):
    """Instantiate a line tool, against the real QGIS when the suite runs that way."""
    iface = MagicMock()
    canvas = None
    button = MagicMock()
    if REAL_QGIS:
        canvas = QgsMapCanvas()
        iface.mapCanvas.return_value = canvas
        button = QAction("test")
    method = MagicMock()
    tool = cls(button, iface, "dir", "net", method)
    if canvas is not None:
        tool._testCanvas = canvas  # the markers live on it; keep it from being collected
    # A real canvas refits the extent to its own aspect ratio, so the width the grid
    # tests need cannot be set on it -- the iface is swapped for a mock afterwards.
    tool.iface = MagicMock()
    tool.iface.mapCanvas.return_value.extent.return_value.width.return_value = canvas_width
    # Replace rubber band rendering with no-op so state tests stay clean
    tool.createRubberBand = MagicMock()
    return tool, method


# ---------------------------------------------------------------------------
# 1. Grid spacing — nice-number rounding
# ---------------------------------------------------------------------------
class TestGridSpacing:
    """_calcGridSpacing() should return a 1/2/5 × 10^n number giving ~15 columns."""

    @pytest.mark.parametrize("width, expected", [
        (15.0,    1.0),    # raw=1.0   → nice=1 × 10^0
        (22.5,    2.0),    # raw=1.5   → not < 1.5 → nice=2 × 10^0
        (25.0,    2.0),    # raw=1.67  → nice=2 × 10^0
        (52.5,    5.0),    # raw=3.5   → not < 3.5 → nice=5 × 10^0
        (75.0,    5.0),    # raw=5.0   → nice=5 × 10^0
        (150.0,  10.0),    # raw=10.0  → nice=1 × 10^1
        (300.0,  20.0),    # raw=20.0  → nice=2 × 10^1
        (1000.0, 50.0),    # raw=66.7  → nice=5 × 10^1
        (10000.0, 500.0),  # raw=666.7 → nice=5 × 10^2
        (0.0,    1.0),     # degenerate: width<=0 → fallback 1.0
        (-5.0,   1.0),     # degenerate: negative → fallback 1.0
    ])
    def test_spacing(self, width, expected):
        tool, _ = _make_tool(canvas_width=width)
        assert tool._calcGridSpacing() == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 2. Grid snap — nearest grid point
# ---------------------------------------------------------------------------
class TestSnapToGrid:
    """_snapToGrid() should round each coordinate to the nearest multiple of spacing."""

    @pytest.fixture
    def tool(self):
        t, _ = _make_tool()
        return t

    @pytest.mark.parametrize("spacing, px, py, ex, ey", [
        (10.0,  13.7,  27.3,  10.0,  30.0),   # rounds down / up
        (10.0,   5.0,  15.0,   0.0,  20.0),   # x halfway: round(0.5)=0 (banker's rounding)
        (5.0,    7.4,  12.6,   5.0,  15.0),   # spacing=5
        (1.0,    3.7,   9.2,   4.0,   9.0),   # spacing=1 (integer coordinates)
        (100.0, 149.9, 250.1, 100.0, 300.0),  # large spacing
    ])
    def test_snap(self, tool, spacing, px, py, ex, ey):
        tool._gridSpacing = spacing
        result = tool._snapToGrid(_Point(px, py))
        assert result.x() == pytest.approx(ex)
        assert result.y() == pytest.approx(ey)

    def test_snap_already_on_grid(self, tool):
        tool._gridSpacing = 10.0
        result = tool._snapToGrid(_Point(20.0, 30.0))
        assert result.x() == pytest.approx(20.0)
        assert result.y() == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# 3. canvasPressEvent — state machine
# ---------------------------------------------------------------------------
class TestPressEventStateMachine:
    """canvasPressEvent manages firstClicked and mousePoints accumulation."""

    @pytest.fixture
    def tool_method(self):
        return _make_tool()

    def _left_click(self, tool, x=0.0, y=0.0):
        """Simulate a left-click at map coordinates (x, y)."""
        tool.toMapCoordinates = lambda pos: _Point(x, y)
        event = MagicMock()
        event.button.return_value = LEFT_BUTTON
        tool.canvasPressEvent(event)

    def _right_click(self, tool):
        event = MagicMock()
        event.button.return_value = RIGHT_BUTTON
        tool.canvasPressEvent(event)

    # --- first left click ---

    def test_first_left_click_sets_firstClicked(self, tool_method):
        tool, _ = tool_method
        assert not tool.firstClicked
        self._left_click(tool, 10.0, 20.0)
        assert tool.firstClicked

    def test_first_left_click_adds_two_identical_points(self, tool_method):
        tool, _ = tool_method
        self._left_click(tool, 10.0, 20.0)
        assert len(tool.mousePoints) == 2
        assert tool.mousePoints[0] == tool.mousePoints[1]
        assert tool.mousePoints[0] == _Point(10.0, 20.0)

    def test_second_left_click_appends_point(self, tool_method):
        tool, _ = tool_method
        self._left_click(tool, 10.0, 20.0)
        self._left_click(tool, 30.0, 40.0)
        assert len(tool.mousePoints) == 3

    # --- right click finalisation ---

    def test_right_click_with_two_distinct_points_calls_method(self, tool_method):
        tool, method = tool_method
        # Manually set up state: firstClicked + two distinct points + cursor point
        tool.firstClicked = True
        tool.mousePoints = [_Point(0.0, 0.0), _Point(10.0, 10.0), _Point(10.0, 10.0)]
        self._right_click(tool)
        method.assert_called_once()

    def test_right_click_with_only_one_point_does_not_call_method(self, tool_method):
        tool, method = tool_method
        # mousePoints = [p] after first click, before any move: [p, p]
        tool.firstClicked = True
        tool.mousePoints = [_Point(5.0, 5.0), _Point(5.0, 5.0)]
        self._right_click(tool)
        method.assert_not_called()

    def test_right_click_resets_state(self, tool_method):
        tool, _ = tool_method
        tool.firstClicked = True
        tool.mousePoints = [_Point(0.0, 0.0), _Point(10.0, 10.0), _Point(10.0, 10.0)]
        self._right_click(tool)
        assert not tool.firstClicked
        assert tool.mousePoints == []

    # --- grid snap on first click ---

    def test_first_click_snaps_to_grid_when_no_object_snapped(self, tool_method):
        tool, _ = tool_method
        tool.SHOW_GRID = True
        tool._showGrid = True
        tool._gridSpacing = 10.0
        # Raw click at (13.0, 27.0), grid snap → (10.0, 30.0)
        self._left_click(tool, 13.0, 27.0)
        assert tool.mousePoints[0] == _Point(10.0, 30.0)

    def test_first_click_grid_snap_inactive_when_show_grid_false(self, tool_method):
        tool, _ = tool_method
        tool.SHOW_GRID = False
        tool._gridSpacing = 10.0
        self._left_click(tool, 13.0, 27.0)
        # No grid snap → raw coordinates preserved
        assert tool.mousePoints[0] == _Point(13.0, 27.0)

    def test_object_snapped_takes_priority_over_grid(self, tool_method):
        tool, _ = tool_method
        tool.SHOW_GRID = True
        tool._gridSpacing = 10.0
        snap_point = _Point(99.0, 99.0)
        snap_match = MagicMock()
        snap_match.point.return_value = snap_point
        tool.objectSnapped = snap_match
        self._left_click(tool, 13.0, 27.0)
        assert tool.mousePoints[0] == _Point(99.0, 99.0)


# ---------------------------------------------------------------------------
# 4. Base class configuration — unified attributes
# ---------------------------------------------------------------------------
class TestBaseClassConfig:
    """Verify that QGISRedCreateLineTool declares the correct unified class attributes."""

    def test_snaps_to_vertices_and_segments(self):
        assert QGISRedCreateLineTool.SNAP_TO_SEGMENTS is True

    def test_shows_grid(self):
        assert QGISRedCreateLineTool.SHOW_GRID is True

    def test_excludes_pump_and_valve_segment_snaps(self):
        assert "Pumps" in QGISRedCreateLineTool.EXCLUDE_SEGMENT_LAYERS
        assert "Valves" in QGISRedCreateLineTool.EXCLUDE_SEGMENT_LAYERS
