# -*- coding: utf-8 -*-
"""The Queries by Properties dock follows the statistic chosen in the Results panel.

Result layers keep one schema; the statistic decides which columns hold values. An
Average fills Flow_Unsig and leaves Flow NULL, every statistic leaves Status NULL. The
property lists, the criteria already entered and the unit shown must follow, whether
the statistic is read from the open Results dock or from the layer when it is closed.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils
from QGISRed.tests.helpers.queries_by_properties_fakes import (
    DOCK_MODULE, PROJECT_UTILS_MODULE, FakeField, FakeLayer, makeDock, makeProject,
)

LINK_FIELDS = [FakeField("Id", "string"), FakeField("Time", "string"), FakeField("Statistics", "string"),
               FakeField("Status", "string"), FakeField("Flow"), FakeField("Flow_Unsig"), FakeField("Flow_Sig"),
               FakeField("Velocity"), FakeField("HeadLoss"), FakeField("UnitHdLoss"), FakeField("FricFactor"),
               FakeField("ReactRate"), FakeField("Quality")]
PIPE_FIELDS = [FakeField("Id", "string"), FakeField("Diameter"), FakeField("Material", "string"), FakeField("Length")]


class FakeResultsDock:
    """The attributes of the Results dock the queries dock reads."""
    lbl_maximum = "Maximum"
    lbl_minimum = "Minimum"
    lbl_range = "Range"
    lbl_average = "Average"
    lbl_std_deviation = "StdDev"
    Scenario = "Base"

    def __init__(self, stat=None):
        self._statsMode = stat is not None
        self._currentStat = stat or "None"
        self.lbTime = MagicMock()


@pytest.fixture(autouse=True)
def clearUnitDefinitions():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


def _linkResultsLayer(statistic):
    return FakeLayer("qgisred_link_results", LINK_FIELDS, rows=[{"Id": "P1", "Statistics": statistic}])


def _liveSip():
    sip = MagicMock()
    sip.isdeleted.return_value = False
    return patch(DOCK_MODULE + ".sip", sip)


class TestLinkPropertiesWithTheResultsDockOpen:
    def _properties(self, stat):
        dock = makeDock()
        dock.resultsDock = FakeResultsDock(stat)
        with _liveSip():
            return dock.getVisibleLinkResultProperties()

    def test_time_mode_offers_flow_and_status(self):
        properties = self._properties(None)

        assert "Flow" in properties
        assert "Status" in properties
        assert "Flow_Unsig" not in properties

    def test_average_offers_the_unsigned_flow_instead_of_flow(self):
        properties = self._properties("Average")

        assert "Flow_Unsig" in properties
        assert "Flow" not in properties

    @pytest.mark.parametrize("stat", ["Maximum", "Minimum", "Range", "StdDev"])
    def test_other_statistics_keep_flow(self, stat):
        properties = self._properties(stat)

        assert "Flow" in properties
        assert "Flow_Unsig" not in properties

    @pytest.mark.parametrize("stat", ["Maximum", "Average"])
    def test_statistics_leave_status_out(self, stat):
        assert "Status" not in self._properties(stat)


class TestLinkPropertiesWithTheResultsDockClosed:
    def _properties(self, statisticInLayer):
        dock = makeDock()
        dock.resultsDock = None
        with patch(DOCK_MODULE + ".QGISRedLayerUtils") as layerUtils:
            layerUtils.getLayersByGroupIdentifier.return_value = [_linkResultsLayer(statisticInLayer)]
            return dock.getVisibleLinkResultProperties()

    def test_an_average_layer_offers_the_unsigned_flow(self):
        properties = self._properties("Average")

        assert "Flow_Unsig" in properties
        assert "Flow" not in properties
        assert "Status" not in properties

    def test_a_maximum_layer_offers_flow_without_status(self):
        properties = self._properties("Maximum")

        assert "Flow" in properties
        assert "Status" not in properties

    def test_a_time_layer_offers_everything(self):
        properties = self._properties(None)

        assert "Flow" in properties
        assert "Status" in properties


class TestStatisticChange:
    def _dockWithFlowCriterion(self):
        dock = makeDock()
        dock.cbElementType.addItem("Pipes", "qgisred_pipes")
        for combo in (dock.cbProperty, dock.cbStatisticsFor):
            combo.addItem("Flow", "Flow")
            combo.addItem("Diameter", "Diameter")
        dock.cbStatisticsFor.setCurrentIndex(1)
        dock.radioSingleCriteria.isChecked.return_value = False
        dock.radioMultipleCriteria.isChecked.return_value = True
        dock.criteria = [{'property': 'Flow', 'condition': '>=', 'value': 5, 'operator': '+', 'enabled': True}]
        dock.updateConditions = lambda: None
        dock.updateValues = lambda: None
        dock.reloadCriteriaTable = MagicMock()
        dock.resultsDock = FakeResultsDock("Average")
        return dock

    def _changeStatistic(self, dock, stat):
        dock.resultsDock = FakeResultsDock(stat)
        pipes = FakeLayer("qgisred_pipes", PIPE_FIELDS, rows=[{"Id": "P1"}])
        with _liveSip():
            with patch(DOCK_MODULE + ".QgsProject") as projectCls:
                with patch(DOCK_MODULE + ".QGISRedLayerUtils") as layerUtils:
                    with patch(PROJECT_UTILS_MODULE + ".QgsProject") as settingsCls:
                        projectCls.instance.return_value.mapLayers.return_value = {"pipes": pipes}
                        layerUtils.getLayersByGroupIdentifier.return_value = [_linkResultsLayer(stat)]
                        layerUtils.getResultsCurrentTimeText.return_value = None
                        settingsCls.instance.return_value = makeProject(project_units="LPS",
                                                                        project_qualitymodel="Chemical")
                        dock.onResultsStatisticsChanged(stat or "")

    def test_average_moves_the_criterion_and_the_property_to_the_unsigned_flow(self):
        dock = self._dockWithFlowCriterion()

        self._changeStatistic(dock, "Average")

        assert dock.criteria[0]['property'] == "Flow_Unsig"
        assert dock.cbProperty.currentData() == "Flow_Unsig"
        dock.reloadCriteriaTable.assert_called_once()

    def test_leaving_average_moves_them_back_to_flow(self):
        dock = self._dockWithFlowCriterion()
        self._changeStatistic(dock, "Average")

        self._changeStatistic(dock, "Maximum")

        assert dock.criteria[0]['property'] == "Flow"
        assert dock.cbProperty.currentData() == "Flow"
        assert "Status" not in dock.cbProperty.internalNames()

    def test_time_mode_brings_status_back(self):
        dock = self._dockWithFlowCriterion()

        self._changeStatistic(dock, None)

        assert dock.criteria[0]['property'] == "Flow"
        assert "Status" in dock.cbProperty.internalNames()

    def test_the_statistics_target_is_kept(self):
        dock = self._dockWithFlowCriterion()

        self._changeStatistic(dock, "Average")

        assert dock.cbStatisticsFor.currentData() == "Diameter"


class TestUnsignedFlowUnit:
    def _dock(self):
        dock = makeDock()
        dock.cbElementType.addItem("Pipes", "qgisred_pipes")
        dock.cbProperty.addItem("Flow", "Flow_Unsig")
        dock.cbStatisticsFor.addItem("Flow", "Flow_Unsig")
        return dock

    def test_the_unsigned_flow_shows_the_flow_unit(self):
        dock = self._dock()
        with patch(PROJECT_UTILS_MODULE + ".QgsProject") as settingsCls:
            settingsCls.instance.return_value = makeProject(project_units="GPM")
            unit = dock.getUnitForProperty("Flow_Unsig")
            dock.updateValueUnitLabel()
            dock.updateStatisticsUnitLabel()

        assert unit == "gpm"
        dock.labelValueUnit.setText.assert_called_with("gpm")
        dock.labelStatisticsUnit.setToolTip.assert_called_with("gpm")


class TestContextSuffix:
    def test_the_statistic_of_a_closed_dock_comes_from_the_layer(self):
        dock = makeDock()
        dock.resultsDock = None
        with patch(DOCK_MODULE + ".QGISRedLayerUtils") as layerUtils:
            layerUtils.getLayersByGroupIdentifier.return_value = [_linkResultsLayer("Range")]
            suffix = dock.getDynamicContextSuffix()

        assert suffix == " for Range values for report times"

    def test_the_statistic_of_the_open_dock_wins(self):
        dock = makeDock()
        dock.resultsDock = FakeResultsDock("StdDev")
        with _liveSip():
            suffix = dock.getDynamicContextSuffix()

        assert suffix == " for StdDev values for report times"
