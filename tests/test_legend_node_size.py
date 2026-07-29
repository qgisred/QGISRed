# -*- coding: utf-8 -*-
"""Editing a node size in the legend editor has to reach the map, not just the legend.

On result layers the marker size comes from a per-symbol-layer data-defined expression,
which beats setSize(). Writing only the latter changed the legend swatch — drawn with no
feature, so the expression cannot evaluate and QGIS falls back to the static size — while
the map kept the old size.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.ui.analysis.qgisred_results_rendering import apply_junction_size, read_node_base_sizes
from QGISRed.compat import WKB_LINE_GEOMETRY

JUNCTION = "if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 2)"
TANK = "if(\"Type\" ='TANK', 7, 0)"
RESERVOIR = "if(\"Type\" ='RESERVOIR', 7, 0)"


class TestApplyJunctionSize:
    def test_the_junction_expression_takes_the_new_size(self):
        assert apply_junction_size(JUNCTION, 3) == "if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 3)"

    @pytest.mark.parametrize("expression", [TANK, RESERVOIR])
    def test_tanks_and_reservoirs_keep_theirs(self, expression):
        # They are a different symbol with their own Appearance factor; the editor's
        # single Size column edits the junction marker.
        assert apply_junction_size(expression, 3) == expression

    def test_a_bare_size_is_replaced(self):
        assert apply_junction_size("2.0", 3) == "3"

    @pytest.mark.parametrize("expression", [
        'scale_linear("Pressure", 0, 50, 2, 4)',   # proportional mode
        'if(BaseDem > 0, 3, 1)',                   # a thematic map, none of our business
    ])
    def test_anything_unrecognised_is_left_alone(self, expression):
        assert apply_junction_size(expression, 3) == expression

    def test_no_expression_at_all(self):
        assert apply_junction_size("", 3) == ""
        assert apply_junction_size(None, 3) == ""


def _symbolLayer(expression, active=True):
    prop = MagicMock()
    prop.isActive.return_value = active
    prop.expressionString.return_value = expression
    properties = MagicMock()
    properties.property.return_value = prop
    symbolLayer = MagicMock()
    symbolLayer.dataDefinedProperties.return_value = properties
    return symbolLayer, properties


def _symbol(symbolLayers):
    symbol = MagicMock()
    symbol.symbolLayerCount.return_value = len(symbolLayers)
    symbol.symbolLayer.side_effect = lambda i: symbolLayers[i]
    return symbol


def _dialog():
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.geometryType.return_value = 0  # point
    return dialog


class TestApplyNodeSizeExpressions:
    def test_the_junction_layer_is_rewritten(self):
        junctionLayer, properties = _symbolLayer(JUNCTION)
        dialog = _dialog()

        with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsProperty") as qgsProperty:
            dialog.applyNodeSizeExpressions(_symbol([junctionLayer]), 3)

        qgsProperty.fromExpression.assert_called_once_with(
            "if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 3)")
        junctionLayer.setDataDefinedProperties.assert_called_once_with(properties)

    def test_the_tank_layer_is_not_touched(self):
        tankLayer, _ = _symbolLayer(TANK)
        dialog = _dialog()

        with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsProperty") as qgsProperty:
            dialog.applyNodeSizeExpressions(_symbol([tankLayer]), 3)

        qgsProperty.fromExpression.assert_not_called()
        tankLayer.setDataDefinedProperties.assert_not_called()

    def test_a_layer_without_a_size_expression_is_skipped(self):
        plainLayer, _ = _symbolLayer(JUNCTION, active=False)
        dialog = _dialog()

        with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsProperty") as qgsProperty:
            dialog.applyNodeSizeExpressions(_symbol([plainLayer]), 3)

        qgsProperty.fromExpression.assert_not_called()


class TestGetNodeSize:
    """Reading has to mirror writing, or the column shows one number and the map another.

    The Appearance factor writes only the expression, so a table reading symbol.size()
    kept showing the value last typed here while the map already drew base × factor.
    """

    def test_the_drawn_size_comes_from_the_expression(self):
        junctionLayer, _ = _symbolLayer("if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 6)")
        symbol = _symbol([junctionLayer])
        symbol.size.return_value = 3  # what the editor last wrote, and not what is drawn

        assert _dialog()._getNodeSize(symbol) == 6

    def test_the_tank_expression_is_not_mistaken_for_the_junction_one(self):
        tankLayer, _ = _symbolLayer(TANK)
        junctionLayer, _ = _symbolLayer("if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 6)")
        symbol = _symbol([tankLayer, junctionLayer])
        symbol.size.return_value = 3

        assert _dialog()._getNodeSize(symbol) == 6

    def test_without_an_expression_the_static_size_is_used(self):
        plainLayer, _ = _symbolLayer(JUNCTION, active=False)
        symbol = _symbol([plainLayer])
        symbol.size.return_value = 2.5

        assert _dialog()._getNodeSize(symbol) == 2.5

    def test_the_size_does_not_drift_on_a_round_trip(self):
        # Reopening the editor and applying without touching anything must not resize
        # anything. The text may gain a decimal point (6 -> 6.0); the value may not move.
        expression = "if(\"Type\" ='RESERVOIR' or \"Type\"='TANK', 0, 6)"
        junctionLayer, _ = _symbolLayer(expression)
        symbol = _symbol([junctionLayer])
        symbol.size.return_value = 3

        shown = _dialog()._getNodeSize(symbol)

        assert read_node_base_sizes(apply_junction_size(expression, shown))[0] == shown


class TestTemplateSymbol:
    """A class added in the editor must inherit the structure of the ones already there.

    A default symbol is a bare marker: it carries none of the data-defined size
    expressions, pump and valve icons or flow arrows the result styles are built from.
    """

    def test_an_existing_symbol_is_cloned(self):
        first, last = MagicMock(), MagicMock()

        result = _dialog().templateSymbol([first, last])

        assert result is last.clone.return_value, "the newest class is the natural template"
        first.clone.assert_not_called()

    def test_a_missing_symbol_is_skipped(self):
        usable = MagicMock()

        result = _dialog().templateSymbol([usable, None])

        assert result is usable.clone.return_value

    def test_with_nothing_to_copy_it_falls_back_to_a_default(self):
        dialog = _dialog()

        with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsSymbol") as qgsSymbol:
            result = dialog.templateSymbol([])

        assert result is qgsSymbol.defaultSymbol.return_value


class TestApplySizeToSymbol:
    def test_a_point_symbol_gets_both_the_static_size_and_the_expression(self):
        # setSize keeps the legend swatch in step; the expression is what the map reads.
        dialog = _dialog()
        dialog.applyNodeSizeExpressions = MagicMock()
        symbol = MagicMock()

        dialog.applySizeToSymbol(symbol, 3)

        symbol.setSize.assert_called_once_with(3)
        dialog.applyNodeSizeExpressions.assert_called_once_with(symbol, 3)

    def test_a_line_symbol_only_sets_its_width(self):
        dialog = _dialog()
        dialog.currentLayer.geometryType.return_value = WKB_LINE_GEOMETRY
        dialog.applyNodeSizeExpressions = MagicMock()
        symbol = MagicMock()

        dialog.applySizeToSymbol(symbol, 1.5)

        symbol.setWidth.assert_called_once_with(1.5)
        dialog.applyNodeSizeExpressions.assert_not_called()
