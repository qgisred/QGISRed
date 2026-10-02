# -*- coding: utf-8 -*-
"""Tank mixing fields follow the quality model.

Without a quality model EPANET does not mix anything, so Mixing Model and Mixing
Fraction are noise. With one, the model is shown and the fraction only matters for
the two-compartment model (2COMP). The rule lives in the field utils and is applied
by the Element Explorer (per tank), the Queries by Properties dock and the Statistics
on Properties dock (per layer: the fraction shows when any tank uses 2COMP).
"""
import inspect
from unittest.mock import patch

import pytest

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils
from QGISRed.ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from QGISRed.ui.queries.qgisred_statisticsandgraphs_dock import QGISRedStatisticsDock
from QGISRed.tests.helpers.queries_by_properties_fakes import (
    DOCK_MODULE, PROJECT_UTILS_MODULE, FakeField, FakeFields, FakeLayer, makeDock, makeProject,
)

# The shipped Tanks table, as written by the plugin DLL (field names and types).
TANK_FIELDS = [
    FakeField("Id", "string"), FakeField("Elevation"), FakeField("IniLevel"), FakeField("MinLevel"),
    FakeField("MaxLevel"), FakeField("Diameter"), FakeField("MinVolume"), FakeField("IdVolCurve", "string"),
    FakeField("Overflow", "string"), FakeField("MixingMod", "string"), FakeField("MixingFrac"),
    FakeField("ReactCoef"), FakeField("IniQuality"), FakeField("Tag", "string"), FakeField("Descrip", "string"),
]


@pytest.fixture(autouse=True)
def clearUnitDefinitions():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


def _withQualityModel(qualityModel):
    patcher = patch(PROJECT_UTILS_MODULE + ".QgsProject")
    projectCls = patcher.start()
    projectCls.instance.return_value = makeProject(project_units="LPS", project_qualitymodel=qualityModel)
    return patcher


class TestRule:
    @pytest.mark.parametrize("qualityModel, mixingModels, hidden", [
        ("None", ["2COMP"], {"MixingMod", "MixingFrac"}),
        ("Chemical", ["MIXED", "FIFO"], {"MixingFrac"}),
        ("Chemical", ["NONE"], {"MixingFrac"}),
        ("Chemical", [None], {"MixingFrac"}),
        ("Chemical", ["MIXED", " 2comp "], set()),
        ("Age", ["2COMP"], set()),
        ("Trace", [], {"MixingFrac"}),
    ])
    def test_hidden_fields_by_quality_and_mixing_model(self, qualityModel, mixingModels, hidden):
        patcher = _withQualityModel(qualityModel)
        try:
            assert QGISRedFieldUtils.getHiddenTankMixingFields(mixingModels) == hidden
        finally:
            patcher.stop()


class TestElementExplorer:
    def _hidden(self, qualityModel, layerIdentifier, mixingModel):
        dock = QGISRedElementExplorerDock.__new__(QGISRedElementExplorerDock)
        fields = FakeFields(TANK_FIELDS)
        attributes = [None] * len(TANK_FIELDS)
        attributes[fields.indexFromName("MixingMod")] = mixingModel
        patcher = _withQualityModel(qualityModel)
        try:
            return dock.hiddenQualityFields(layerIdentifier, fields, attributes)
        finally:
            patcher.stop()

    def test_no_quality_model_hides_both_mixing_fields_and_the_chemical_ones(self):
        assert self._hidden("None", "qgisred_tanks", "2COMP") == {"ReactCoef", "IniQuality", "MixingMod", "MixingFrac"}

    def test_chemical_model_hides_only_the_fraction_of_a_fully_mixed_tank(self):
        assert self._hidden("Chemical", "qgisred_tanks", "MIXED") == {"MixingFrac"}

    def test_chemical_model_shows_the_fraction_of_a_two_components_tank(self):
        assert self._hidden("Chemical", "qgisred_tanks", "2COMP") == set()

    def test_age_model_keeps_the_chemical_fields_hidden_but_shows_the_mixing_ones(self):
        assert self._hidden("Age", "qgisred_tanks", "2COMP") == {"ReactCoef", "IniQuality"}

    def test_other_layers_keep_their_chemical_only_fields(self):
        assert self._hidden("None", "qgisred_pipes", None) == {"BulkCoeff", "WallCoeff"}


class TestQueriesByProperties:
    def _propertyLists(self, qualityModel, mixingModels):
        layer = FakeLayer("qgisred_tanks", TANK_FIELDS,
                          rows=[{"Id": f"T{i}", "MixingMod": model} for i, model in enumerate(mixingModels)])
        dock = makeDock()
        dock.cbElementType.addItem("Tanks", "qgisred_tanks")
        dock.updateConditions = lambda: None
        dock.updateValues = lambda: None
        patcher = _withQualityModel(qualityModel)
        try:
            with patch(DOCK_MODULE + ".QgsProject") as projectCls:
                with patch(DOCK_MODULE + ".QGISRedLayerUtils") as layerUtils:
                    projectCls.instance.return_value.mapLayers.return_value = {"tanks": layer}
                    layerUtils.getLayersByGroupIdentifier.return_value = []
                    dock.updateProperties()
        finally:
            patcher.stop()
        return dock.cbProperty.internalNames(), dock.cbStatisticsFor.internalNames()

    def test_no_quality_model_lists_neither_mixing_field(self):
        properties, statistics = self._propertyLists("None", ["NONE", "MIXED"])

        assert "MixingMod" not in properties
        assert "MixingFrac" not in properties
        assert "MixingFrac" not in statistics
        assert "Elevation" in properties

    def test_chemical_model_lists_the_mixing_model_but_not_the_fraction(self):
        properties, statistics = self._propertyLists("Chemical", ["MIXED", "FIFO"])

        assert "MixingMod" in properties
        assert "MixingFrac" not in properties
        assert "MixingFrac" not in statistics

    def test_a_two_components_tank_brings_the_fraction_into_both_lists(self):
        properties, statistics = self._propertyLists("Chemical", ["MIXED", "2COMP"])

        assert "MixingMod" in properties
        assert "MixingFrac" in properties
        assert "MixingFrac" in statistics

    def test_the_two_components_value_is_matched_regardless_of_case(self):
        properties, _statistics = self._propertyLists("Age", ["2comp"])

        assert "MixingFrac" in properties


class TestStatisticsOnProperties:
    def _hiddenLower(self, qualityModel, identifier, mixingModels):
        dock = object.__new__(QGISRedStatisticsDock)
        dock.fieldUtils = QGISRedFieldUtils()
        layer = FakeLayer(identifier, TANK_FIELDS, rows=[{"MixingMod": model} for model in mixingModels])
        patcher = _withQualityModel(qualityModel)
        try:
            return dock.hiddenTankMixingFieldsLower(layer, identifier)
        finally:
            patcher.stop()

    def test_no_quality_model_hides_both_mixing_fields(self):
        assert self._hiddenLower("None", "qgisred_tanks", ["2COMP"]) == {"mixingmod", "mixingfrac"}

    def test_chemical_model_hides_the_fraction_unless_a_tank_uses_two_components(self):
        assert self._hiddenLower("Chemical", "qgisred_tanks", ["MIXED"]) == {"mixingfrac"}
        assert self._hiddenLower("Chemical", "qgisred_tanks", ["MIXED", "2COMP"]) == set()

    def test_other_layers_are_left_alone(self):
        assert self._hiddenLower("None", "qgisred_pipes", []) == set()

    @pytest.mark.parametrize("methodName", [
        "updateProperties", "updateClassifyBy", "updateSecondClassifyBy", "updateAttributes",
    ])
    def test_every_property_list_applies_the_rule(self, methodName):
        """The four lists build their hidden set inline; each has to add the mixing rule to it."""
        source = inspect.getsource(getattr(QGISRedStatisticsDock, methodName))

        assert "nonChemicalFields | self.hiddenTankMixingFieldsLower(layer, elementIdentifier)" in source
