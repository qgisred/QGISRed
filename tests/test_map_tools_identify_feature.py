# -*- coding: utf-8 -*-
"""The identify tool survives being deactivated while it is still on the canvas.

deactivate() destroys the snap markers, but Escape, a project change and the highlight
arbiter handing the canvas to another panel and back all call it without taking the tool
off the canvas. The mouse kept arriving in canvasMoveEvent, landing on a None marker.
"""
import sys
from unittest.mock import MagicMock
import pytest

from .conftest import _qt_stub

sys.modules['qgis.gui'].QgsMapTool = _qt_stub("QgsMapTool")
sys.modules['qgis.gui'].QgsMapToolIdentify = _qt_stub("QgsMapToolIdentify")

from QGISRed.tools.map_tools.qgisred_identifyFeature import QGISRedIdentifyFeature  # noqa: E402


def _deactivatedTool():
    """A tool deactivate() has dismantled, still sitting on the canvas."""
    tool = QGISRedIdentifyFeature.__new__(QGISRedIdentifyFeature)
    tool.canvas = MagicMock()
    tool.custom_cursor = None
    tool.currentHighlight = None
    tool.firstPoint = None
    tool.objectSnapped = None
    tool.startMarker = MagicMock()
    tool.endMarker = MagicMock()
    tool.snapper = MagicMock()
    tool.snapper.snapToMap.return_value = MagicMock(isValid=lambda: False)
    tool.toMapCoordinates = MagicMock()
    tool.dock = MagicMock()
    tool.removeVertexMarkers()
    tool.disconnectDockSignals()
    tool.dock.dockClosed.reset_mock()
    return tool


def test_a_mouse_move_after_deactivation_does_not_raise():
    tool = _deactivatedTool()

    tool.canvasMoveEvent(MagicMock())  # used to raise AttributeError on a None marker


@pytest.mark.mock_only
def test_reactivating_the_tool_rebuilds_the_markers_and_the_snapper():
    """The Element Explorer re-arms the instance it remembers rather than building a new
    one, so activate() is the only chance to get the markers back — and it has to rebuild
    them before configSnapper(), which startVertexes() would otherwise undo."""
    tool = _deactivatedTool()

    tool.activate()

    assert tool.startMarker is not None
    assert tool.endMarker is not None
    assert tool.snapper is not None


@pytest.mark.mock_only
def test_reactivating_the_tool_listens_for_the_dock_closing_again():
    """deactivate() drops the dockClosed connection, and onDockClosed is what takes this
    tool's highlight off the map and its cursor off the canvas when the Explorer is closed.
    Without this, closing it after a chart had borrowed the canvas left both behind."""
    tool = _deactivatedTool()

    tool.activate()

    tool.dock.dockClosed.connect.assert_called_once_with(tool.onDockClosed)
