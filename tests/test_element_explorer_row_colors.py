# -*- coding: utf-8 -*-
"""Row colours of the Element Explorer tables.

Data tab: a junction's Emitter Coefficient row is a lighter orange than its demand rows,
and only while the coefficient is above zero; a service connection's base demand and
pattern rows take the junctions' orange. Results tab: a node's Demand row and the Quality
row of nodes and links replace the plain results yellow with their own blends, on the
Value and Units cells like every other results row.

Real QGIS only: the colours are read back from real table items, and the results layer
is found through the real project tree.
"""
import os
import xml.etree.ElementTree as ElementTree
from unittest.mock import MagicMock

import pytest

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from QGISRed.ui.analysis.qgisred_results_data import LINK_RESULT_FIELDS, NODE_RESULT_FIELDS
from QGISRed.ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock

from .conftest import REAL_QGIS

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="reads the colours back from real table items")

_STYLES_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "defaults", "layerStyles")
_NUMERIC_FIELDS = {"Elevation", "BaseDem", "EmittCoef", "IniQuality", "Length", "Diameter", "Roughness",
                   "BaseDemand", "Reliabilit"}

SOURCE_PINK = "#ffe0ff"
DEMAND_ORANGE = "#ffe4cc"
EMITTER_ORANGE = "#fff2e2"
RESULTS_YELLOW = "#fff8dc"
RESULTS_PRESSURE = "#e2fbc4"
RESULTS_FLOW = "#cff3fb"


def _shippedFieldNames(styleName):
    """The attribute table columns of the shipped style: the layer's fields in their order."""
    root = ElementTree.parse(os.path.join(_STYLES_FOLDER, styleName + ".qml.bak")).getroot()
    columns = root.findall("attributetableconfig/columns/column")
    return [column.get("name") for column in columns if column.get("type") == "field"]


def _memoryLayer(geometry, fieldNames, identifier):
    from qgis.core import QgsVectorLayer

    uri = "%s?crs=EPSG:3857&%s" % (geometry, "&".join(
        "field=%s:%s" % (name, "double" if name in _NUMERIC_FIELDS else "string") for name in fieldNames))
    layer = QgsVectorLayer(uri, identifier, "memory")
    layer.setCustomProperty("qgisred_identifier", identifier)
    return layer


def _layerFromShippedStyle(styleName, geometry, identifier):
    return _memoryLayer(geometry, _shippedFieldNames(styleName), identifier)


def _feature(layer, values):
    from qgis.core import QgsFeature

    feature = QgsFeature(layer.fields())
    for name, value in values.items():
        feature.setAttribute(name, value)
    return feature


def _dock():
    """The dock as its tables see it: real brushes, mocked widgets that record the items."""
    dock = QGISRedElementExplorerDock.__new__(QGISRedElementExplorerDock)
    dock.dataTableWidget = MagicMock()
    dock.tableResults = MagicMock()
    dock.labelResultsTime = MagicMock()
    dock.initTableWidgets()
    dock.demandSpatialIndex = None
    dock.demandSpatialLayer = None
    dock.sourceSpatialIndex = None
    dock.sourceSpatialLayer = None
    dock.demandPageIndex = 0
    dock.demandsPerPage = 1
    dock.nodeLayers = ["qgisred_junctions"]
    dock.linkLayers = ["qgisred_pipes"]
    dock.resultsCurrentTimeText = ""
    dock.resultsCurrentStat = ""
    return dock


def _rows(table):
    """The items setItem() placed on the mocked table, one dict per row keyed by column."""
    rows = {}
    for call in table.setItem.call_args_list:
        row, column, item = call.args
        rows.setdefault(row, {})[column] = item
    return [rows[row] for row in sorted(rows)]


def _rowNamed(table, propertyName):
    for row in _rows(table):
        if row[0].text() == propertyName:
            return row
    raise AssertionError("no row named %r" % propertyName)


def _colorOf(item):
    from qgis.PyQt.QtCore import Qt

    brush = item.background()
    if brush.style() == Qt.BrushStyle.NoBrush:
        return None
    return brush.color().name()


class TestJunctionEmitterRow:
    def _populated(self, emitterCoefficient):
        dock = _dock()
        dock.currentLayer = _layerFromShippedStyle("Junctions", "Point", "qgisred_junctions")
        dock.currentFeature = _feature(dock.currentLayer, {
            "JunctionID": "J1", "Elevation": 10.0, "BaseDem": 2.0, "DemPattID": "P1",
            "EmittCoef": emitterCoefficient,
        })
        dock.populateDataTableWidget()
        return dock

    def _row(self, dock, fieldName):
        propertyName = QGISRedFieldUtils().getProperty(normalize_element("qgisred_junctions"), fieldName)
        return _rowNamed(dock.dataTableWidget, propertyName)

    def test_a_positive_coefficient_tints_its_row_lighter_than_the_demand(self):
        dock = self._populated(0.5)

        emitterRow = self._row(dock, "EmittCoef")
        assert [_colorOf(emitterRow[column]) for column in (0, 1, 2)] == [EMITTER_ORANGE] * 3
        assert _colorOf(self._row(dock, "BaseDem")[1]) == DEMAND_ORANGE

    def test_a_zero_coefficient_leaves_its_row_white(self):
        dock = self._populated(0.0)

        emitterRow = self._row(dock, "EmittCoef")
        assert [_colorOf(emitterRow[column]) for column in (0, 1, 2)] == [None] * 3


class TestServiceConnectionDemandRows:
    def test_base_demand_and_pattern_take_the_junction_orange(self):
        dock = _dock()
        dock.currentLayer = _layerFromShippedStyle("ServiceConnections", "LineString", "qgisred_serviceconnections")
        dock.currentFeature = _feature(dock.currentLayer, {
            "Id": "C1", "Length": 5.0, "BaseDemand": 1.0, "Pattern": "P1",
        })

        dock.populateDataTableWidget()

        element = normalize_element("qgisred_serviceconnections")
        utils = QGISRedFieldUtils()
        for fieldName in ("BaseDemand", "Pattern"):
            row = _rowNamed(dock.dataTableWidget, utils.getProperty(element, fieldName))
            assert [_colorOf(row[column]) for column in (0, 1, 2)] == [DEMAND_ORANGE] * 3
        assert _colorOf(_rowNamed(dock.dataTableWidget, utils.getProperty(element, "Length"))[1]) is None


@pytest.fixture
def resultsGroup():
    """A Results group in the real project tree, under the Chemical quality model so Quality is listed."""
    from qgis.core import QgsProject

    project = QgsProject.instance()
    previousModel, hadModel = project.readEntry("QGISRed", "project_qualitymodel", "")
    project.writeEntry("QGISRed", "project_qualitymodel", "Chemical")
    root = project.layerTreeRoot()
    group = root.addGroup("Results")
    group.setCustomProperty("qgisred_identifier", "qgisred_results")
    yield group
    for layerNode in group.findLayers():
        project.removeMapLayer(layerNode.layerId())
    root.removeChildNode(group)
    if hadModel:
        project.writeEntry("QGISRed", "project_qualitymodel", previousModel)
    else:
        project.removeEntry("QGISRed", "project_qualitymodel")


def _resultsLayer(group, geometry, identifier, idFieldName, fieldsDefinition, values):
    from qgis.core import QgsProject, QgsVectorLayer

    uri = "%s?crs=EPSG:3857&field=%s:string&%s" % (geometry, idFieldName, "&".join(
        "field=%s:%s" % (name, kind.lower()) for name, kind, *_ in fieldsDefinition))
    layer = QgsVectorLayer(uri, identifier, "memory")
    layer.setCustomProperty("qgisred_identifier", identifier)
    layer.dataProvider().addFeatures([_feature(layer, values)])
    QgsProject.instance().addMapLayer(layer, False)
    group.addLayer(layer)
    return layer


class TestResultsRows:
    def _nodeDock(self, resultsGroup):
        dock = _dock()
        dock.currentLayer = _layerFromShippedStyle("Junctions", "Point", "qgisred_junctions")
        dock.currentFeature = _feature(dock.currentLayer, {"JunctionID": "J1"})
        _resultsLayer(resultsGroup, "Point", "qgisred_node_pressure", "NodeID", NODE_RESULT_FIELDS, {
            "NodeID": "J1", "Time": "00:00:00", "Pressure": 30.0, "Head": 40.0, "Demand": 2.0, "Quality": 0.5,
        })
        return dock

    def _linkDock(self, resultsGroup):
        dock = _dock()
        dock.currentLayer = _memoryLayer("LineString", ["PipeID"], "qgisred_pipes")
        dock.currentFeature = _feature(dock.currentLayer, {"PipeID": "P1"})
        _resultsLayer(resultsGroup, "LineString", "qgisred_link_flow", "LinkID", LINK_RESULT_FIELDS, {
            "LinkID": "P1", "Time": "00:00:00", "Status": "Open", "Flow": 3.0, "Quality": 0.4,
        })
        return dock

    def _resultRows(self, dock, isNode):
        fieldOrder = dock.getResultsFieldOrder(isNode)
        rows = _rows(dock.tableResults)
        assert len(rows) == len(fieldOrder)
        return dict(zip(fieldOrder, rows))

    def test_a_node_demand_row_and_quality_row_reuse_the_data_colours(self, resultsGroup):
        dock = self._nodeDock(resultsGroup)

        dock.populateResultsTable()

        rows = self._resultRows(dock, True)
        assert [_colorOf(rows["Demand"][column]) for column in (1, 2)] == [DEMAND_ORANGE] * 2
        assert [_colorOf(rows["Quality"][column]) for column in (1, 2)] == [SOURCE_PINK] * 2
        assert [_colorOf(rows["Pressure"][column]) for column in (1, 2)] == [RESULTS_PRESSURE] * 2
        assert _colorOf(rows["Head"][1]) == RESULTS_YELLOW

    def test_the_property_cell_stays_white_on_every_results_row(self, resultsGroup):
        dock = self._nodeDock(resultsGroup)

        dock.populateResultsTable()

        assert [_colorOf(row[0]) for row in self._resultRows(dock, True).values()] == [None] * 4

    def test_a_link_quality_row_reuses_the_source_colour(self, resultsGroup):
        dock = self._linkDock(resultsGroup)

        dock.populateResultsTable()

        rows = self._resultRows(dock, False)
        assert [_colorOf(rows["Quality"][column]) for column in (1, 2)] == [SOURCE_PINK] * 2
        assert [_colorOf(rows["Flow"][column]) for column in (1, 2)] == [RESULTS_FLOW] * 2
        assert "Demand" not in rows
