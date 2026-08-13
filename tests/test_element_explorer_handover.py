# -*- coding: utf-8 -*-
"""Handing the canvas from the Element Explorer to a Time Series chart.

Two things used to survive the handover, both because the identify tool is a second actor
the arbiter knew nothing about: the tool stayed armed, so a click on the map meant for the
chart came back to the Explorer and raised its dock; and the tool's own red highlight
stayed on the element, next to the chart's.
"""
import sys
from unittest.mock import MagicMock

from .conftest import _qt_stub

sys.modules['qgis.gui'].QgsMapTool = _qt_stub("QgsMapTool")
sys.modules['qgis.gui'].QgsMapToolIdentify = _qt_stub("QgsMapToolIdentify")

from QGISRed.tools.map_tools.qgisred_identifyFeature import QGISRedIdentifyFeature  # noqa: E402
from QGISRed.ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock  # noqa: E402


def _identifiedFromTheMap():
    """The tool highlights first, then the dock highlights too."""
    tool = QGISRedIdentifyFeature.__new__(QGISRedIdentifyFeature)
    tool.canvas = MagicMock()
    tool.currentHighlight = MagicMock()

    dock = QGISRedElementExplorerDock.__new__(QGISRedElementExplorerDock)
    dock.mainHighlight = MagicMock()
    dock.currentSelectedHighlight = None
    dock.adjacentHighlights = []
    dock._selectedLayers = []
    dock.canvas = MagicMock()
    dock.canvas.mapTool.return_value = tool
    return dock, tool


def test_suspending_clears_both_reds_from_the_map():
    dock, tool = _identifiedFromTheMap()

    dock.clearMapHighlights()

    assert tool.currentHighlight is None
    assert dock.mainHighlight is None


def test_suspending_leaves_the_layer_selections_alone():
    """Why the suspend cannot just call the tool's clearHighlights(): that one also drops
    the selection on every layer, which is shared state other docks read."""
    dock, _tool = _identifiedFromTheMap()
    layer = MagicMock()
    dock._selectedLayers = [layer]

    dock.clearMapHighlights()

    assert dock._selectedLayers == [layer]
    layer.removeSelection.assert_not_called()


def _analysisSection():
    """Imported per call, never at collection time: importing the section pulls in the whole
    map_tools package, and test_map_tools_create_line.py has to load qgisred_createLineTool
    after it has swapped its own module mocks in."""
    from QGISRed.sections.analysis_section import AnalysisSection

    return AnalysisSection


def _sectionWith(currentTool):
    section = _analysisSection().__new__(_analysisSection())
    section.myMapTools = {"TimeSeries": MagicMock()}
    section.iface = MagicMock()
    section.canvas = section.iface.mapCanvas.return_value
    section.canvas.mapTool.return_value = currentTool
    section._activeTimeSeriesDock = None
    section._setActiveTimeSeriesDock = MagicMock()
    section._restyleTimeSeriesDocks = MagicMock()
    section._applyTimeSeriesMapStateForDock = MagicMock()
    return section


def test_the_chart_takes_the_canvas_tool_from_the_identify_tool():
    identify = QGISRedIdentifyFeature.__new__(QGISRedIdentifyFeature)
    section = _sectionWith(identify)

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_called_once_with(section.myMapTools["TimeSeries"])


def test_the_chart_does_not_take_an_unrelated_tool():
    """A pan, a zoom or a digitising tool is the user in the middle of something."""
    section = _sectionWith(MagicMock())

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_not_called()
