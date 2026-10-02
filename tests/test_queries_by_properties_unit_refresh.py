# -*- coding: utf-8 -*-
"""The unit next to the value field survives a refresh of the Queries by Properties dock.

Changing the headloss formula in Analysis Options reloads the layers, and the dock
rebuilds its combos and puts the queried property back with signals blocked. The unit
label is only wired to the property signal, so it kept showing the unit of the default
property (Flow) while the combo said Roughness Coefficient.
"""
from unittest.mock import patch

import pytest

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils
from QGISRed.tests.helpers.queries_by_properties_fakes import PROJECT_UTILS_MODULE, makeDock, makeProject


@pytest.fixture(autouse=True)
def clearUnitDefinitions():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


def _restoreRoughnessWithFormula(formula):
    dock = makeDock()
    dock.cbElementType.addItem("Pipes", "qgisred_pipes")
    dock.cbProperty.addItem("Flow", "Flow")
    dock.cbProperty.addItem("Roughness Coeff", "RoughCoeff")
    dock.cbStatisticsFor.addItem("Flow", "Flow")
    # The refresh rebuilds the combos from the layer; here they stay as built.
    dock.updateProperties = lambda: None
    dock.updateConditions = lambda: None
    dock.updateValues = lambda: None
    state = {"elementType": "qgisred_pipes", "property": "RoughCoeff", "condition": "<=",
             "valueText": "0.1", "statisticsFor": "Flow"}
    with patch(PROJECT_UTILS_MODULE + ".QgsProject") as projectCls:
        projectCls.instance.return_value = makeProject(project_units="LPS", project_headloss=formula)
        dock.restoreCurrentQueryState(state)
    return dock


@pytest.mark.parametrize("formula, unit", [
    ("D-W", "mm"),
    ("C-M", "s/m¹ᐟ³"),
])
def test_restored_property_shows_its_own_unit_for_the_current_formula(formula, unit):
    dock = _restoreRoughnessWithFormula(formula)

    assert dock.cbProperty.currentData() == "RoughCoeff"
    dock.labelValueUnit.setText.assert_called_with(unit)
    dock.labelValueUnit.setVisible.assert_called_with(True)


def test_restored_property_without_unit_hides_the_label():
    dock = _restoreRoughnessWithFormula("H-W")

    dock.labelValueUnit.setText.assert_not_called()
    dock.labelValueUnit.setVisible.assert_called_with(False)
