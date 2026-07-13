# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch
import pytest
from QGISRed.ui.analysis.qgisred_results_rendering import _ResultsRenderingMixin
from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils

# Helper to build a mock QgsProject
def _make_project(flow_unit="LPS"):
    proj = MagicMock()
    def read_entry(section, key, default=""):
        if section == "QGISRed" and key == "project_units":
            return flow_unit, True
        return default, False
    proj.readEntry.side_effect = read_entry
    return proj

class MockDock(_ResultsRenderingMixin):
    def __init__(self):
        self.cbNodeLabels = MagicMock()
        self.cbLinkLabels = MagicMock()
        self.spNodeDecimals = MagicMock()
        self.spLinkDecimals = MagicMock()
        self._labelFontSize = 10
        self._labelColorByRange = False
        self._labelShowId = False

    def tr(self, text):
        return text

@pytest.fixture(autouse=True)
def clear_cache():
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None

class TestResultsLabels:
    def test_set_layer_labels_show_id(self):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            
            MockProj.instance.return_value = _make_project("LPS")

            dock = MockDock()
            dock._labelShowId = True
            dock.cbNodeLabels.isChecked.return_value = True
            dock.spNodeDecimals.value.return_value = 2

            layer = MagicMock()
            layer.geometryType.return_value = 0  # Node

            # Call method under test
            dock.setLayerLabels(layer, "Pressure")

            # Extract the layer_settings passed to QgsVectorLayerSimpleLabeling
            assert MockLabeling.call_args is not None
            layer_settings = MockLabeling.call_args[0][0]

            # The fieldName attribute on settings contains the expression
            expr = layer_settings.fieldName
            
            # When show_id is True, first line should be the "Id" field
            assert '"Id"' in expr
            # Type case/when should NOT be present
            assert 'CASE' not in expr
            assert 'JUNCTION' not in expr
            # Second line should contain the formatted value
            assert 'format_number' in expr

    def test_set_layer_labels_no_show_id(self):
        with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as MockProj, \
             patch("QGISRed.ui.analysis.qgisred_results_rendering.QgsVectorLayerSimpleLabeling") as MockLabeling:
            
            MockProj.instance.return_value = _make_project("LPS")

            dock = MockDock()
            dock._labelShowId = False
            dock.cbNodeLabels.isChecked.return_value = True
            dock.spNodeDecimals.value.return_value = 2

            layer = MagicMock()
            layer.geometryType.return_value = 0  # Node

            dock.setLayerLabels(layer, "Pressure")

            assert MockLabeling.call_args is not None
            layer_settings = MockLabeling.call_args[0][0]

            expr = layer_settings.fieldName
            
            # When show_id is False, it should only show the value expression
            assert '"Id"' not in expr
            assert 'format_number("Pressure", 2)' in expr
