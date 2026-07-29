# -*- coding: utf-8 -*-
"""Reading a rule-based result renderer back as a graduated one.

applyNullStyle turns the graduated renderer into rules so NULL features stay visible, and
the legend editor has to undo that to fill its table. The filter expressions come from
whatever built them, so the parsing cannot be tied to one spelling: a table that comes up
empty means every rule was rejected here.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL


class _FakeRule:
    def __init__(self, expression, label="range"):
        self._expression = expression
        self._label = label

    def filterExpression(self):
        return self._expression

    def label(self):
        return self._label

    def symbol(self):
        symbol = MagicMock()
        symbol.clone.return_value = "symbol"
        return symbol


class _FakeRuleBasedRenderer:
    def __init__(self, *rules):
        root = MagicMock()
        root.children.return_value = list(rules)
        self._root = root

    def rootRule(self):
        return self._root


class _FakeRange:
    def __init__(self, lower, upper, symbol, label):
        self.lower, self.upper, self.label = lower, upper, label


class _FakeGraduated:
    def __init__(self, classAttribute, ranges):
        self.classAttribute, self.ranges = classAttribute, ranges


def _convert(renderer):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    module = "QGISRed.ui.project.qgisred_legends_dialog."
    with patch(module + "QgsRuleBasedRenderer", _FakeRuleBasedRenderer), \
         patch(module + "QgsRendererRange", _FakeRange), \
         patch(module + "QgsGraduatedSymbolRenderer", _FakeGraduated):
        return dialog.ruleBasedAsGraduated(renderer)


BOUND = QGISRedLegendsDialog.OPEN_RANGE_BOUND


class TestTheRealFiveClassStyle:
    """The exact rules QGIS 3.44 produces for the shipped LinkVelocity style.

    The outer two carry a single bound; reading only two-sided filters dropped them and
    the table came up with three rows instead of five.
    """

    RULES = [
        ("<0.1", "(Velocity) <= 0.1000000000000000"),
        ("0.1-0.5", "(Velocity) > 0.1000000000000000 AND (Velocity) <= 0.5000000000000000"),
        ("0.5-1", "(Velocity) > 0.5000000000000000 AND (Velocity) <= 1.0000000000000000"),
        ("1-2", "(Velocity) > 1.0000000000000000 AND (Velocity) <= 2.0000000000000000"),
        (">2", "(Velocity) > 2.0000000000000000"),
    ]

    def _renderer(self):
        rules = [_FakeRule(expression, label) for label, expression in self.RULES]
        return _FakeRuleBasedRenderer(*rules, _FakeRule("ELSE", label=_NULL_RULE_LABEL))

    def test_every_class_survives(self):
        result = _convert(self._renderer())

        assert [r.label for r in result.ranges] == ["<0.1", "0.1-0.5", "0.5-1", "1-2", ">2"]

    def test_the_open_ends_get_the_sentinel_the_styles_use(self):
        # -1e10 / 1e10 is what the .qml files carry, so applying without changes writes
        # the very same numbers back.
        result = _convert(self._renderer())

        assert (result.ranges[0].lower, result.ranges[0].upper) == (-BOUND, 0.1)
        assert (result.ranges[-1].lower, result.ranges[-1].upper) == (2.0, BOUND)

    def test_the_column_is_recovered_from_the_first_parsable_rule(self):
        # The first rule has no ">=" at all, which is what used to abort the whole read.
        assert _convert(self._renderer()).classAttribute == "Velocity"


class TestFilterSpellings:
    """Each of these is a shape the conversion has produced at some point."""

    @pytest.mark.parametrize("expression, expected", [
        # Built by hand by the old applyNullStyle.
        ("(Pressure) >= 10 AND (Pressure) <= 20", "Pressure"),
        # QGIS's convertFromRenderer, quoting a plain column.
        ('"Pressure" >= 10 AND "Pressure" <= 20', "Pressure"),
        # Same, leaving it bare.
        ("Pressure >= 10 AND Pressure <= 20", "Pressure"),
        # An expression, which is never quoted: this is the Flow case.
        ("abs(Flow) >= 10 AND abs(Flow) <= 20", "abs(Flow)"),
        ("(abs(Flow)) >= 10 AND (abs(Flow)) <= 20", "abs(Flow)"),
        # Single-bound outer classes.
        ("(Pressure) <= 20", "Pressure"),
        ("abs(Flow) > 20", "abs(Flow)"),
    ])
    def test_the_classified_column_is_recovered(self, expression, expected):
        result = _convert(_FakeRuleBasedRenderer(_FakeRule(expression)))

        assert result is not None, "an unparsed filter leaves the editor table empty"
        assert result.classAttribute == expected

    def test_ranges_after_the_first_use_an_exclusive_lower_bound(self):
        renderer = _FakeRuleBasedRenderer(
            _FakeRule('"Pressure" >= 0 AND "Pressure" <= 10'),
            _FakeRule('"Pressure" > 10 AND "Pressure" <= 20'),
        )

        result = _convert(renderer)

        assert [(r.lower, r.upper) for r in result.ranges] == [(0.0, 10.0), (10.0, 20.0)]

    def test_bounds_are_read_from_the_comparisons_not_from_any_digit(self):
        # A column whose name carries a digit used to shift the bounds: scanning every
        # number in the string picked up the "1" of P1 as the lower bound.
        result = _convert(_FakeRuleBasedRenderer(_FakeRule('"P1" >= 10 AND "P1" <= 20')))

        assert (result.ranges[0].lower, result.ranges[0].upper) == (10.0, 20.0)

    def test_scientific_and_negative_bounds(self):
        result = _convert(_FakeRuleBasedRenderer(_FakeRule('"Head" >= -1.5e-3 AND "Head" <= 2.5E2')))

        assert (result.ranges[0].lower, result.ranges[0].upper) == (-0.0015, 250.0)


class TestRulesThatAreNotRanges:
    def test_the_null_rule_is_ignored(self):
        renderer = _FakeRuleBasedRenderer(
            _FakeRule('"Pressure" >= 0 AND "Pressure" <= 10'),
            _FakeRule("", label=_NULL_RULE_LABEL),
        )

        assert len(_convert(renderer).ranges) == 1

    def test_a_rule_that_is_not_a_range_is_skipped(self):
        # Status classifies with LIKE conditions; there is no graduated renderer behind it.
        renderer = _FakeRuleBasedRenderer(_FakeRule("\"Status\" LIKE '%Closed%'"))

        assert _convert(renderer) is None

    def test_a_renderer_with_no_rules_yields_nothing(self):
        assert _convert(_FakeRuleBasedRenderer()) is None


class TestUnwrapClassAttribute:
    @pytest.mark.parametrize("raw, expected", [
        ('"Pressure"', "Pressure"),
        ("(Pressure)", "Pressure"),
        ("  Pressure  ", "Pressure"),
        ("abs(Flow)", "abs(Flow)"),
        ("(abs(Flow))", "abs(Flow)"),
        ("coalesce(a, b)", "coalesce(a, b)"),
    ])
    def test_only_real_wrappers_are_removed(self, raw, expected):
        assert QGISRedLegendsDialog.unwrapClassAttribute(raw) == expected
