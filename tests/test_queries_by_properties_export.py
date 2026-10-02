# -*- coding: utf-8 -*-
"""The statistics export of the Queries by Properties dock.

The user picks the file. The CSV opens with the project (the network name), the
scenario, the element type, the query (or queries) with their time or statistic, the
magnitude the statistics are about, then a blank line and the table. Every header
line is one CSV cell, so a comma inside a value cannot split it.
"""
import csv
import os
import re
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils
from QGISRed.tests.helpers.queries_by_properties_fakes import (
    DOCK_MODULE, PROJECT_UTILS_MODULE, FakeField, FakeLayer, makeDock, makeProject,
)
from QGISRed.tests.test_queries_by_properties_result_stats import FakeResultsDock, LINK_FIELDS

PIPE_FIELDS = [FakeField("Id", "string"), FakeField("Diameter"), FakeField("Material", "string"), FakeField("Length")]
PIPES_SOURCE = "C:/projects/GranRed/GranRed_Pipes.shp|layerid=0"


class _FakeCell:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class FakeStatisticsTable:
    def __init__(self, headers, rows):
        self._headers = headers
        self._rows = rows

    def columnCount(self):
        return len(self._headers)

    def rowCount(self):
        return len(self._rows)

    def horizontalHeaderItem(self, col):
        return _FakeCell(self._headers[col])

    def item(self, row, col):
        return _FakeCell(self._rows[row][col])


@pytest.fixture(autouse=True)
def clearUnitDefinitions():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


def _dock(headers=("Count", "Avg", "Min", "Max", "StdD"), rows=(("3", "80.00", "50.00", "100.00", "20.00"),)):
    dock = makeDock()
    dock.cbElementType.addItem("Pipes", "qgisred_pipes")
    dock.cbProperty.addItem("Diameter", "Diameter")
    dock.cbCondition.addItem("<=")
    dock.cbValue.value.return_value = "100"
    dock.cbStatisticsFor.addItem("Diameter", "Diameter")
    dock.cbStatisticsFor.addItem("Flow", "Flow")
    dock.cbStatisticsFor.addItem("Flow", "Flow_Unsig")
    dock.cbStatisticsFor.addItem("None", "_none_")
    dock.lastStatisticsEnglishHeaders = list(headers)
    dock.tableWidgetStatistics = FakeStatisticsTable(list(headers), [list(row) for row in rows])
    dock.resultsDock = None
    return dock


def _multipleCriteria(dock, comment=""):
    dock.radioSingleCriteria.isChecked.return_value = False
    dock.radioMultipleCriteria.isChecked.return_value = True
    dock.multipleCriteriaComment.text.return_value = comment
    dock.criteria = [
        {'property': 'Flow', 'condition': '>=', 'value': 5, 'operator': '+', 'enabled': True},
        {'property': 'Diameter', 'condition': '<=', 'value': 100, 'operator': '-', 'enabled': True},
        {'property': 'Material', 'condition': '=', 'value': 'a,b', 'operator': '+', 'enabled': False},
    ]


def _export(dock, tmp_path, timeText=None, resultsLayers=(), pipesSource=PIPES_SOURCE, proposedPaths=None):
    """Run exportStatistics against tmp_path and give back the parsed CSV rows."""
    outPath = os.path.join(str(tmp_path), "chosen.csv")
    layers = {"pipes": FakeLayer("qgisred_pipes", PIPE_FIELDS, source=pipesSource)} if pipesSource else {}

    def saveFileName(parent, title, proposed, filters):
        if proposedPaths is not None:
            proposedPaths.append(proposed)
            return "", ""
        return outPath, ""

    with patch(DOCK_MODULE + ".QFileDialog") as fileDialog, patch(DOCK_MODULE + ".QMessageBox"):
        with patch(DOCK_MODULE + ".QgsProject") as projectCls, patch(DOCK_MODULE + ".QGISRedLayerUtils") as layerUtils:
            with patch(PROJECT_UTILS_MODULE + ".QgsProject") as settingsCls:
                fileDialog.getSaveFileName.side_effect = saveFileName
                projectCls.instance.return_value.mapLayers.return_value = layers
                projectCls.instance.return_value.homePath.return_value = str(tmp_path)
                projectCls.instance.return_value.baseName.return_value = "qgisfile"
                layerUtils.getLayersByGroupIdentifier.return_value = list(resultsLayers)
                layerUtils.getResultsCurrentTimeText.return_value = timeText
                settingsCls.instance.return_value = makeProject(
                    project_units="LPS", project_qualitymodel="Chemical", project_headloss="D-W")
                dock.exportStatistics()
    if not os.path.exists(outPath):
        return None
    with open(outPath, newline='', encoding='utf-8') as f:
        return list(csv.reader(f))


def _linkLayer(statistic=None):
    return FakeLayer("qgisred_link_results", LINK_FIELDS, rows=[{"Id": "P1", "Statistics": statistic}])


class TestHeaderBlock:
    def test_single_static_query(self, tmp_path):
        rows = _export(_dock(), tmp_path)

        assert rows[:6] == [
            ["Project: GranRed"],
            ["Scenario: Base"],
            ["Element type: Pipes"],
            ["Query: Diameter <= 100 mm"],
            ["Statistics: Diameter (mm)"],
            [],
        ]
        assert rows[6:] == [["Count", "Avg", "Min", "Max", "StdD"], ["3", "80.00", "50.00", "100.00", "20.00"]]

    def test_multiple_queries_at_a_time_list_only_the_enabled_criteria(self, tmp_path):
        dock = _dock(rows=(("2", "1", "1", "1", "0"), ("1", "2", "2", "2", "0"), ("3", "1.5", "1", "2", "0.5")))
        _multipleCriteria(dock, comment="Big pipes")
        dock.cbStatisticsFor.setCurrentIndex(1)

        rows = _export(dock, tmp_path, timeText="12:00:00", resultsLayers=[_linkLayer()])

        assert rows[3:9] == [
            ["Queries at 12:00:00:"],
            ["+ Flow >= 5 lps"],
            ["- Diameter <= 100 mm"],
            ["Comment: Big pipes"],
            ["Statistics: Flow (lps)"],
            [],
        ]

    def test_rows_of_several_criteria_are_named(self, tmp_path):
        dock = _dock(rows=(("2", "1", "1", "1", "0"), ("1", "2", "2", "2", "0"), ("3", "1.5", "1", "2", "0.5")))
        _multipleCriteria(dock)

        rows = _export(dock, tmp_path)

        assert rows[-4:] == [
            ["Criterion", "Count", "Avg", "Min", "Max", "StdD"],
            ["Cr1", "2", "1", "1", "1", "0"],
            ["Cr2", "1", "2", "2", "2", "0"],
            ["All", "3", "1.5", "1", "2", "0.5"],
        ]

    def test_a_static_query_about_a_result_magnitude_still_tells_the_time(self, tmp_path):
        dock = _dock()
        dock.cbStatisticsFor.setCurrentIndex(1)

        rows = _export(dock, tmp_path, timeText="0:00:00", resultsLayers=[_linkLayer()])

        assert rows[3] == ["Query: Diameter <= 100 mm at 0:00:00"]

    def test_a_single_period_run_names_it_as_the_time(self, tmp_path):
        dock = _dock()
        dock.cbStatisticsFor.setCurrentIndex(1)

        rows = _export(dock, tmp_path, timeText="Single Period", resultsLayers=[_linkLayer()])

        assert rows[3] == ["Query: Diameter <= 100 mm at Single Period"]

    def test_a_results_statistic_replaces_the_time(self, tmp_path):
        dock = _dock()
        dock.cbStatisticsFor.setCurrentIndex(2)

        rows = _export(dock, tmp_path, resultsLayers=[_linkLayer("Average")])

        assert rows[3] == ["Query: Diameter <= 100 mm for Average values for report times"]
        assert rows[4] == ["Statistics: Flow_Unsig (lps)"]

    def test_counting_elements_has_no_magnitude(self, tmp_path):
        dock = _dock(headers=("Count",), rows=(("3",),))
        dock.cbStatisticsFor.setCurrentIndex(3)

        rows = _export(dock, tmp_path)

        assert rows[4] == ["Statistics: Count"]
        assert rows[6:] == [["Count"], ["3"]]

    def test_a_comma_in_a_value_stays_in_one_cell(self, tmp_path):
        dock = _dock()
        dock.cbProperty.clear()
        dock.cbProperty.addItem("Material", "Material")
        dock.cbCondition.clear()
        dock.cbCondition.addItem("=")
        dock.cbValue.value.return_value = "a,b"

        rows = _export(dock, tmp_path)

        assert rows[3] == ["Query: Material = a,b"]

    def test_the_scenario_comes_from_the_results_dock(self, tmp_path):
        dock = _dock()
        dock.resultsDock = FakeResultsDock()
        dock.resultsDock.Scenario = "Alt"
        sip = MagicMock()
        sip.isdeleted.return_value = False

        with patch(DOCK_MODULE + ".sip", sip):
            rows = _export(dock, tmp_path)

        assert rows[1] == ["Scenario: Alt"]


class TestProjectName:
    def test_the_network_name_comes_from_the_pipes_layer_not_the_qgis_file(self, tmp_path):
        rows = _export(_dock(), tmp_path)

        assert rows[0] == ["Project: GranRed"]

    def test_without_pipes_layer_the_qgis_file_name_is_used(self, tmp_path):
        rows = _export(_dock(), tmp_path, pipesSource="")

        assert rows[0] == ["Project: qgisfile"]


class TestDefaultFileNames:
    def test_statistics_file_is_named_after_the_network(self, tmp_path):
        proposed = []

        assert _export(_dock(), tmp_path, proposedPaths=proposed) is None
        assert re.fullmatch(r"GranRed_Query_Statistics_\d{8}_\d{6}\.csv", os.path.basename(proposed[0]))
        assert os.path.dirname(proposed[0]) == str(tmp_path)

    def test_criteria_file_is_named_after_the_network(self, tmp_path):
        dock = _dock()
        proposed = []

        def saveFileName(parent, title, proposedPath, filters):
            proposed.append(proposedPath)
            return "", ""

        with patch(DOCK_MODULE + ".QFileDialog") as fileDialog, patch(DOCK_MODULE + ".QgsProject") as projectCls:
            fileDialog.getSaveFileName.side_effect = saveFileName
            projectCls.instance.return_value.mapLayers.return_value = {
                "pipes": FakeLayer("qgisred_pipes", PIPE_FIELDS, source=PIPES_SOURCE)}
            projectCls.instance.return_value.homePath.return_value = str(tmp_path)
            dock.exportCriteria()

        assert re.fullmatch(r"GranRed_Query_Criteria_\d{8}_\d{6}\.txt", os.path.basename(proposed[0]))
