# -*- coding: utf-8 -*-
"""In-place expression rewrites the legend editor applies to the shipped styles.

Fixtures are the exact expressions from defaults/layerStyles/*.qml.bak: the
rewrites must change only the targeted color/size literal and keep the
coalesce()/with_variable() retro-compat wrappers untouched.
"""
import re

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import (
    DEMAND_BASE_FILL_PATTERNS,
    ISOLATION_VALVE_GREEN_PATTERN,
    METER_ACTIVE_FILL_PATTERNS,
    SERVICE_CONNECTION_ACTIVE_FILL_PATTERN,
    SERVICE_CONNECTION_ACTIVE_STROKE_PATTERNS,
    QGISRedLegendsDialog,
    extractMeterTypeFromExpression,
    formatExpressionNumber,
    parseCategoricalRuleFilter,
    rewriteMeterSizeExpression,
    scaleNumericLiterals,
    substituteCapturedGroup,
)


SERVICE_CONNECTION_STROKE = "if(IsActive is NULL, '#85b66f',if(IsActive >0, '#85b66f','#ff0f13'))"
SERVICE_CONNECTION_FILL = (
    "if(coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseDemand'))>0,"
    " if(IsActive is NULL or IsActive >0,'#b7dfa3','#c7cbc5'),'#fff')"
)
ISOLATION_VALVE_FILL = (
    "if( \"Available\"!=0, if( coalesce(attribute($currentfeature,'IniStatus'),"
    "attribute($currentfeature,'Status'))='CLOSED', color_rgb(255,19,19),"
    " if(\"LossCoeff\" = 0, color_rgb(18,180,37), color_rgb(246,185,18))), color_rgb(125,139,143))"
)
DEMANDS_FILL = (
    "with_variable('bd',coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseValue')),"
    "if (@bd is NULL, '#ffffff', if( @bd >0, '#fdbf6f', if (@bd <0 , '#a6cee3', '#ffffff'))))"
)
DEMANDS_FILL_LEGACY = (
    "if (BaseValue is NULL, '#ffffff', if( BaseValue >0, '#fdbf6f', "
    "if (BaseValue <0 , '#a6cee3', '#ffffff')))"
)
DEMANDS_SIZE = (
    "with_variable('bd',coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseValue')),"
    "if (@bd is NULL, 1.6, if( @bd >0, 1.6, if (@bd <0 , 3.5, 1.6))))"
)
METER_SIZE = (
    "with_variable('mt',coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type')),"
    " if (@mt is NULL, 0, if (@mt = 'Flowmeter', 5, 0)))"
)
METER_SIZE_MANOMETER = (
    "with_variable('mt',coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type')),"
    " if (@mt is NULL, 5, if (@mt = 'Manometer', 5, 0)))"
)
METER_SIZE_LEGACY = "if (Type is NULL, 0, if (Type = 'Flowmeter', 5, 0))"


class TestServiceConnections:
    def test_stroke_active_branches_change_inactive_red_stays(self):
        expr = SERVICE_CONNECTION_STROKE
        for pattern in SERVICE_CONNECTION_ACTIVE_STROKE_PATTERNS:
            expr, changed = substituteCapturedGroup(expr, pattern, "#123456")
            assert changed
        assert expr == "if(IsActive is NULL, '#123456',if(IsActive >0, '#123456','#ff0f13'))"

    def test_fill_keeps_coalesce_wrapper_and_inactive_branches(self):
        expr, changed = substituteCapturedGroup(
            SERVICE_CONNECTION_FILL, SERVICE_CONNECTION_ACTIVE_FILL_PATTERN, "#c4e4ae"
        )
        assert changed
        assert "coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseDemand'))" in expr
        assert "'#c4e4ae'" in expr
        assert "'#c7cbc5'" in expr and "'#fff'" in expr
        assert "#b7dfa3" not in expr

    def test_stroke_patterns_do_not_touch_the_fill_only_branches(self):
        expr, changed = substituteCapturedGroup(
            SERVICE_CONNECTION_FILL, SERVICE_CONNECTION_ACTIVE_STROKE_PATTERNS[0], "#123456"
        )
        assert not changed
        assert expr == SERVICE_CONNECTION_FILL


class TestIsolationValves:
    def test_only_the_losscoeff_green_branch_changes(self):
        expr, changed = substituteCapturedGroup(
            ISOLATION_VALVE_FILL, ISOLATION_VALVE_GREEN_PATTERN, "color_rgb(10,20,30)"
        )
        assert changed
        assert "color_rgb(10,20,30)" in expr
        assert "color_rgb(18,180,37)" not in expr
        # The rest of the expression is untouched
        assert "coalesce(attribute($currentfeature,'IniStatus')" in expr
        assert "color_rgb(255,19,19)" in expr
        assert "color_rgb(246,185,18)" in expr
        assert "color_rgb(125,139,143)" in expr

    def test_reader_regex_matches_the_shipped_expression(self):
        _prop, regex = QGISRedLegendsDialog.INPUT_COLOR_READERS["qgisred_isolationvalves"]
        match = re.compile(regex).search(ISOLATION_VALVE_FILL)
        assert match and match.groups() == ("18", "180", "37")


class TestMultipleDemands:
    @staticmethod
    def _substituteBase(expr, newHex):
        changedAny = False
        for pattern in DEMAND_BASE_FILL_PATTERNS:
            expr, changed = substituteCapturedGroup(expr, pattern, newHex)
            changedAny = changedAny or changed
        return expr, changedAny

    @pytest.mark.parametrize("expr", [DEMANDS_FILL, DEMANDS_FILL_LEGACY])
    def test_only_the_white_base_branches_change(self, expr):
        newExpr, changed = self._substituteBase(expr, "#123456")
        assert changed
        assert newExpr.count("'#123456'") == 2
        assert "#ffffff" not in newExpr
        # The demand colors stay fixed
        assert "'#fdbf6f'" in newExpr and "'#a6cee3'" in newExpr

    def test_with_variable_wrapper_survives(self):
        newExpr, _ = self._substituteBase(DEMANDS_FILL, "#123456")
        assert newExpr.startswith("with_variable('bd',coalesce(")

    @pytest.mark.parametrize("expr", [DEMANDS_FILL, DEMANDS_FILL_LEGACY])
    def test_reader_regex_reads_the_base_color(self, expr):
        _prop, regex = QGISRedLegendsDialog.INPUT_COLOR_READERS["qgisred_demands"]
        match = re.compile(regex).search(expr)
        assert match and match.group(1) == "#ffffff"

    def test_substitution_is_idempotent_after_a_first_apply(self):
        once, _ = self._substituteBase(DEMANDS_FILL, "#123456")
        twice, changed = self._substituteBase(once, "#abcdef")
        assert changed
        assert twice.count("'#abcdef'") == 2 and "#123456" not in twice

    def test_size_scaling_keeps_wrapper_and_ratio(self):
        scaled = scaleNumericLiterals(DEMANDS_SIZE, 2.0)
        assert scaled.startswith("with_variable('bd',coalesce(")
        assert "3.2" in scaled and "7" in scaled
        assert "1.6," not in scaled
        # comparison literals stay zero
        assert "@bd >0" in scaled and "@bd <0" in scaled


class TestMeters:
    def test_with_variable_form_rewrites_in_place(self):
        newExpr, meterType = rewriteMeterSizeExpression(METER_SIZE, 7)
        assert meterType == "Flowmeter"
        assert newExpr.startswith("with_variable('mt',coalesce(")
        assert "if (@mt = 'Flowmeter', 7, 0)" in newExpr
        assert "@mt is NULL, 0," in newExpr  # zero NULL branch stays hidden

    def test_manometer_nonzero_null_branch_follows_the_new_size(self):
        newExpr, meterType = rewriteMeterSizeExpression(METER_SIZE_MANOMETER, 8)
        assert meterType == "Manometer"
        assert "@mt is NULL, 8," in newExpr
        assert "if (@mt = 'Manometer', 8, 0)" in newExpr

    def test_only_type_filter_skips_other_layers(self):
        newExpr, meterType = rewriteMeterSizeExpression(METER_SIZE, 7, onlyType="Manometer")
        assert meterType == "Flowmeter"
        assert newExpr == METER_SIZE

    def test_legacy_flat_form_still_handled(self):
        newExpr, meterType = rewriteMeterSizeExpression(METER_SIZE_LEGACY, 6.5)
        assert meterType == "Flowmeter"
        assert newExpr == "if (Type is NULL, 0, if (Type = 'Flowmeter', 6.5, 0))"

    def test_type_extraction(self):
        assert extractMeterTypeFromExpression(METER_SIZE) == "Flowmeter"
        assert extractMeterTypeFromExpression("if(IsActive is NULL, '#ffffff', '#cccccc')") is None

    def test_active_fill_patterns_keep_inactive_grey(self):
        expr = "if(IsActive is NULL, '#ffffff',if(IsActive !=0, '#ffffff','#cccccc'))"
        for pattern in METER_ACTIVE_FILL_PATTERNS:
            expr, changed = substituteCapturedGroup(expr, pattern, "#ff8800")
            assert changed
        assert expr == "if(IsActive is NULL, '#ff8800',if(IsActive !=0, '#ff8800','#cccccc'))"


class TestRuleFilters:
    """The five HydraulicSectorsLinks rule filters, including the ClosedLinks split."""

    @pytest.mark.parametrize("filterExpr, value", [
        ("\"Class\" = 'H-Q'", "H-Q"),
        ("\"Class\" = 'H-nQ'", "H-nQ"),
        ("\"Class\" = 'nH-Q'", "nH-Q"),
        ("\"Class\" = 'nH-nQ' AND \"SubNet\" <> 'ClosedLinks'", "nH-nQ"),
        ("\"Class\" = 'nH-nQ' AND \"SubNet\" = 'ClosedLinks'", "ClosedLinks"),
    ])
    def test_hydraulic_sectors_filters(self, filterExpr, value):
        assert parseCategoricalRuleFilter(filterExpr) == ("Class", value)

    @pytest.mark.parametrize("filterExpr", [
        "(Pressure) >= 0 AND (Pressure) <= 10",
        "ELSE",
        "",
        None,
        "\"Class\" IN ('a', 'b')",
    ])
    def test_non_categorical_filters_are_rejected(self, filterExpr):
        assert parseCategoricalRuleFilter(filterExpr) is None


class TestScaling:
    def test_tree_nodes_expression(self):
        assert scaleNumericLiterals("if(\"NodeType\" = 'Tank', 7, 0)", 1.5) == "if(\"NodeType\" = 'Tank', 10.5, 0)"

    def test_zero_branches_stay_zero(self):
        assert scaleNumericLiterals("if (EmittCoef>0, 0, 1.3)", 2) == "if (EmittCoef>0, 0, 2.6)"

    def test_quoted_values_are_not_scaled(self):
        assert scaleNumericLiterals("if(\"Type\" = 'Zone2', 4, 0)", 2) == "if(\"Type\" = 'Zone2', 8, 0)"

    def test_number_formatting(self):
        assert formatExpressionNumber(2.0) == "2"
        assert formatExpressionNumber(3.2000000001) == "3.2"
        assert formatExpressionNumber(10.5) == "10.5"
