# -*- coding: utf-8 -*-
"""The Legend Editor shows a fixed-threshold result style as the file states it.

Only the result styles that rebuild their classes from the data (a strategy with an
intervals part) start from Pretty Breaks; the pressure, velocity... styles keep the
thresholds, the minimum and the maximum of the spec, and the Value column keeps enough
decimals for a bound such as 14.995 to survive an Apply.
"""
import json
from unittest.mock import MagicMock

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog


def _dialog(identifier, strategy=None):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = MagicMock()
    properties = {"qgisred_identifier": identifier}
    if strategy is not None:
        properties["qgisred_legend_strategy"] = json.dumps(strategy)
    dialog.currentLayer.customProperty.side_effect = lambda key, default=None: properties.get(key, default)
    dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_NUMERIC
    dialog.cbMode = MagicMock()
    dialog.cbMode.findData.return_value = 5
    dialog.previousClassificationMode = None
    dialog.updateUiBasedOnFieldType = MagicMock()
    dialog.applyClassificationMethod = MagicMock()
    return dialog


_PRETTY = {"schema": "qgisred.legendStrategy.v2", "mode": "graduated", "field": "Head",
           "parts": ["intervals", "colors"], "intervals": {"classificationMode": "Pretty", "classes": 5}}


class TestDefaultClassificationMode:
    def test_a_fixed_threshold_result_style_stays_in_manual_mode(self):
        dialog = _dialog("qgisred_node_pressure")
        dialog.applyDefaultClassificationMode()
        dialog.cbMode.setCurrentIndex.assert_not_called()

    def test_a_result_style_with_automatic_intervals_starts_from_pretty_breaks(self):
        dialog = _dialog("qgisred_node_head", _PRETTY)
        dialog.applyDefaultClassificationMode()
        dialog.cbMode.setCurrentIndex.assert_called_once_with(5)
        assert dialog.previousClassificationMode == "Pretty"

    def test_selecting_pretty_breaks_keeps_the_classes_the_layer_draws(self):
        dialog = _dialog("qgisred_node_demand", _PRETTY)
        dialog.applyDefaultClassificationMode()
        # Selected with the signals blocked: the mode handler would classify every value anew
        assert dialog.cbMode.blockSignals.call_args_list[0].args == (True,)
        assert dialog.cbMode.blockSignals.call_args_list[-1].args == (False,)
        dialog.applyClassificationMethod.assert_not_called()

    def test_a_strategy_that_only_replays_colors_keeps_the_classes(self):
        strategy = dict(_PRETTY, parts=["colors"])
        dialog = _dialog("qgisred_node_head", strategy)
        dialog.applyDefaultClassificationMode()
        dialog.cbMode.setCurrentIndex.assert_not_called()


class TestRangeText:
    def test_the_spec_bounds_survive_the_value_column(self):
        assert QGISRedLegendsDialog.formatRangeText(-10, 14.995) == "-10 - 14.995"
        assert QGISRedLegendsDialog.formatRangeText(0.0095, 0.0145) == "0.0095 - 0.0145"
        assert QGISRedLegendsDialog.formatRangeText(49.995, 200) == "49.995 - 200"
