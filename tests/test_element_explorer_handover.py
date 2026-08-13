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
    from QGISRed.tools.utils.qgisred_highlight_manager import QGISRedHighlightManager

    section = _analysisSection().__new__(_analysisSection())
    section.highlightManager = QGISRedHighlightManager()
    section.myMapTools = {"TimeSeries": MagicMock()}
    section.iface = MagicMock()
    section.canvas = section.iface.mapCanvas.return_value
    section.canvas.mapTool.return_value = currentTool
    section._activeTimeSeriesDock = None
    section._setActiveTimeSeriesDock = MagicMock()
    section._restyleTimeSeriesDocks = MagicMock()
    section._applyTimeSeriesMapStateForDock = MagicMock()
    return section


class _NativeIdentifyTool:
    """QGIS's own Identify Features. Recognised by name: the class is not wrapped for
    Python, so it reaches us cast to whatever base sip found."""

    __module__ = "qgis.gui"


class _NativePanTool:
    __module__ = "qgis.gui"


def test_the_chart_takes_the_canvas_tool_from_the_element_explorer():
    identify = QGISRedIdentifyFeature.__new__(QGISRedIdentifyFeature)
    section = _sectionWith(identify)

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_called_once_with(section.myMapTools["TimeSeries"])


def test_the_chart_takes_the_canvas_tool_from_qgis_own_identify():
    """A competing subject, not a navigation gesture: turning back to the chart ends its
    turn, and the mouse belongs to the chart again."""
    section = _sectionWith(_NativeIdentifyTool())

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_called_once_with(section.myMapTools["TimeSeries"])


def test_the_chart_takes_the_canvas_tool_from_the_multiple_selector():
    """QGISRed's own multiple selector picks things off the map too. It is not filed as a
    selection tool by the arbiter — every plugin tool is "plugin, no owner" before its job is
    looked at — so it has to be named. The selected elements survive: they live in the
    layers, not in the tool."""
    from QGISRed.tools.map_tools.qgisred_multilayerSelection import QGISRedMultiLayerSelection

    selector = QGISRedMultiLayerSelection.__new__(QGISRedMultiLayerSelection)
    section = _sectionWith(selector)

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_called_once_with(section.myMapTools["TimeSeries"])


def test_the_chart_does_not_take_a_navigation_tool():
    """A pan or a zoom is the user in the middle of a gesture, not another subject."""
    section = _sectionWith(_NativePanTool())

    section._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    section.canvas.setMapTool.assert_not_called()


def _resultsSectionWith(currentTool):
    section = _sectionWith(currentTool)
    section.myMapTools["ResultsEvolution"] = MagicMock()
    section._resultsEvolutionHighlight = MagicMock()
    section._resultsEvolutionDock = MagicMock()
    section._resultsEvolutionDock.return_value._activeEvolutionLayerType.return_value = "junctions"
    return section


def test_the_results_panel_answers_the_same_question_as_the_chart():
    """Both reclaims ask one predicate, so the two cannot drift apart again."""
    identify = _NativeIdentifyTool()

    charts = _sectionWith(identify)
    charts._reclaimMapToolForTimeSeries(MagicMock(highlights={"J1": 1}))

    results = _resultsSectionWith(identify)
    results._reclaimMapToolForResultsEvolution()

    charts.canvas.setMapTool.assert_called_once_with(charts.myMapTools["TimeSeries"])
    results.canvas.setMapTool.assert_called_once_with(results.myMapTools["ResultsEvolution"])


def test_the_results_panel_also_leaves_a_navigation_tool_alone():
    results = _resultsSectionWith(_NativePanTool())

    results._reclaimMapToolForResultsEvolution()

    results.canvas.setMapTool.assert_not_called()
