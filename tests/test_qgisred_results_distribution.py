# -*- coding: utf-8 -*-
from unittest.mock import MagicMock, patch

from QGISRed.ui.analysis.qgisred_results_distribution import (
    _ResultsDistributionMixin,
    _find_class_index,
    _format_range_label,
    _include_feature_for_distribution,
    _parse_category_from_filter,
    build_distribution_bins,
    extract_legend_classes,
)
from QGISRed.tools.utils.qgisred_legend_rule_utils import OPEN_RANGE_BOUND
from QGISRed.tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL
from QGISRed.ui.analysis.results_distribution_renderer import (
    ResultsDistributionRenderer,
    format_distribution_hover_value,
    hit_test_cumulative_polyline,
)
from QGISRed.ui.analysis.results_distribution_widget import resolve_hover_bar_at


class TestFormatDistributionHoverValue:
    def test_absolute_count_as_integer(self):
        assert format_distribution_hover_value(42) == "42"

    def test_interpolated_absolute_count_has_no_decimals(self):
        assert format_distribution_hover_value(23.7) == "24"

    def test_relative_percent(self):
        assert format_distribution_hover_value(25.5, as_percent=True).endswith(" %")


class TestDistributionHoverTooltipLines:
    def test_frequency_relative(self):
        renderer = ResultsDistributionRenderer()

        class Widget:
            bar_mode = "relative"
            hoverSegment = "frequency"
            bins = [{"label": "Open", "count": 25}]

            _totalCount = 100

            def tr(self, message):
                return message

        lines = renderer._hoverTooltipLines(Widget(), Widget.bins[0])
        assert lines[0] == "Open"
        assert lines[1].endswith(" %")

    def test_cumulative_absolute(self):
        renderer = ResultsDistributionRenderer()

        class Widget:
            bar_mode = "plain"
            hoverSegment = "cumulative"
            bins = [{"label": "Closed", "count": 10, "cumulative_count": 30}]

            _totalCount = 100

            def tr(self, message):
                return message

        lines = renderer._hoverTooltipLines(Widget(), Widget.bins[0])
        assert lines == ["Closed", "Cumulative: 30"]

    def test_frequency_zero_count(self):
        renderer = ResultsDistributionRenderer()

        class Widget:
            bar_mode = "plain"
            hoverSegment = "frequency"
            bins = [{"label": "Active", "count": 0}]
            _totalCount = 10

            def tr(self, message):
                return message

        lines = renderer._hoverTooltipLines(Widget(), Widget.bins[0])
        assert lines == ["Active", "Count: 0"]

    def test_frequency_header_includes_magnitude(self):
        renderer = ResultsDistributionRenderer()

        class Widget:
            bar_mode = "plain"
            hoverSegment = "frequency"
            xLabel = "Pressure"
            bins = [{"label": "10 - 20", "count": 5}]
            _totalCount = 50

            def tr(self, message):
                return message

        lines = renderer._hoverTooltipLines(Widget(), Widget.bins[0])
        assert lines == ["Pressure: 10 - 20", "Count: 5"]


class TestDistributionHoverPriority:
    def test_cumulative_curve_wins_over_bar_when_both_hit(self):
        from unittest.mock import MagicMock

        from qgis.PyQt.QtCore import QPointF

        from QGISRed.ui.analysis.results_distribution_widget import resolve_distribution_hover_at

        class _Widget:
            bins = [{"label": "A", "count": 1}]
            cumulative_mode = "absolute"
            cumulative_points = [{"x": 1.0, "count": 1}]
            _barRects = [object()]

            def __init__(self):
                self._renderer = MagicMock()
                self._hover_bar_at = MagicMock(return_value=(0, "frequency"))
                self._plot_rect = MagicMock()
                self._plot_rect.contains.return_value = True

            def getPlotRect(self):
                return self._plot_rect

            def _hasCumulativeCurve(self):
                return self.cumulative_mode in ("absolute", "relative") and bool(self.cumulative_points)

            def _hoverBarAt(self, cursor_pos, plot_rect):
                return self._hover_bar_at(cursor_pos, plot_rect)

        widget = _Widget()
        curve_sample = {"x": 5.0, "count": 25.0, "screen_x": 50.0, "screen_y": 70.0}
        widget._renderer.hitTestCumulativeCurve.return_value = curve_sample

        index, segment, curve = resolve_distribution_hover_at(widget, QPointF(50, 70))

        assert index is None
        assert segment == "curve"
        assert curve is curve_sample
        widget._hover_bar_at.assert_not_called()


class TestHitTestCumulativePolyline:
    def test_detects_point_near_segment(self):
        points = [
            {"screen_x": 0.0, "screen_y": 0.0, "x": 0.0, "count": 0.0},
            {"screen_x": 100.0, "screen_y": 0.0, "x": 10.0, "count": 50.0},
        ]
        hit = hit_test_cumulative_polyline(50.0, 5.0, points, tolerance=8.0)
        assert hit is not None
        assert 4.0 < hit["x"] < 6.0
        assert 24.0 < hit["count"] < 26.0

    def test_returns_none_when_far_from_curve(self):
        points = [
            {"screen_x": 0.0, "screen_y": 0.0, "x": 0.0, "count": 0.0},
            {"screen_x": 100.0, "screen_y": 0.0, "x": 10.0, "count": 50.0},
        ]
        assert hit_test_cumulative_polyline(50.0, 40.0, points, tolerance=8.0) is None


class TestCurveHoverTooltipLines:
    def test_shows_variable_and_relative_cumulative(self):
        renderer = ResultsDistributionRenderer()

        class Widget:
            xLabel = "Pressure"
            cumulative_mode = "relative"
            bins = [{"count": 1}]
            _totalCount = 100

            def tr(self, message):
                return message

        lines = renderer._curveHoverTooltipLines(
            Widget(),
            {"x": 12.5, "count": 40.0},
        )
        assert lines[0].startswith("Pressure:")
        assert lines[1].startswith("Cumulative:")
        assert lines[1].endswith(" %")


class _R:
    def __init__(self, left, right, top, bottom):
        self._l, self._r, self._t, self._b = left, right, top, bottom

    def left(self):
        return self._l

    def right(self):
        return self._r

    def top(self):
        return self._t

    def bottom(self):
        return self._b


class _P:
    def __init__(self, x, y):
        self._x, self._y = x, y

    def x(self):
        return self._x

    def y(self):
        return self._y


class TestHoverBarAtGeometry:
    PLOT = _R(0, 300, 0, 200)
    BARS = [
        _R(10, 90, 198, 200),
        _R(110, 190, 80, 200),
        _R(210, 290, 200, 200),
    ]

    def _hover(self, x, y, cum_rects=None, has_cum=False):
        return resolve_hover_bar_at(self.BARS, cum_rects or [], has_cum, _P(x, y), self.PLOT)

    def test_zero_count_bin_hoverable_in_its_column(self):
        assert self._hover(250, 100) == (2, "frequency")

    def test_tiny_bar_hoverable_above_its_top(self):
        assert self._hover(50, 40) == (0, "frequency")

    def test_outside_any_column_returns_none(self):
        assert self._hover(100, 100) == (None, None)

    def test_outside_plot_vertically_returns_none(self):
        assert self._hover(50, 250) == (None, None)

    def test_cumulative_segment_above_frequency(self):
        cum = [_R(10, 90, 50, 200)]
        assert self._hover(50, 100, cum_rects=cum, has_cum=True) == (0, "cumulative")

    def test_frequency_segment_within_cumulative(self):
        cum = [_R(10, 90, 50, 200)]
        assert self._hover(50, 199, cum_rects=cum, has_cum=True) == (0, "frequency")


class TestDistributionChartTitleTemplate:
    def test_frequency_title_with_units(self):
        title = (
            _ResultsDistributionMixin._DISTRIBUTION_TITLE_TEMPLATE.replace("%1", "Flows").replace(
                "%2", " (gpm)"
            )
        )
        assert title == "Flows frequency (gpm)"

    def test_frequency_title_without_units(self):
        title = _ResultsDistributionMixin._DISTRIBUTION_TITLE_TEMPLATE.replace("%1", "Pressures").replace(
            "%2", ""
        )
        assert title == "Pressures frequency"


class TestDistributionChartTitleUsesPlural:
    """The histogram covers every element, so its title must read in plural."""

    class _Dock(_ResultsDistributionMixin):
        def __init__(self, field):
            self._field = field

        def _distributionFieldForLayer(self, layer_type):
            return self._field

        def _distributionMagnitudeLabel(self, layer_type):
            return "fallback"

        def tr(self, message):
            return message

    def _title(self, layer_type, field, plural, singular, unit):
        fieldUtils = MagicMock()
        fieldUtils.getPluralProperty.return_value = plural
        fieldUtils.getProperty.return_value = singular
        fieldUtils.getUnitAbbreviation.return_value = unit
        with patch(
            "QGISRed.ui.analysis.qgisred_results_distribution.QGISRedFieldUtils",
            return_value=fieldUtils,
        ):
            return self._Dock(field)._distributionChartTitle(layer_type), fieldUtils

    def test_title_uses_plural_name(self):
        title, fieldUtils = self._title("Node", "Pressure", "Pressures", "Pressure", "m")
        assert title == "Pressures frequency (m)"
        fieldUtils.getPluralProperty.assert_called_once_with("Nodes", "Pressure")

    def test_title_without_unit(self):
        title, _ = self._title("Link", "Velocity", "Velocities", "Velocity", "")
        assert title == "Velocities frequency"

    def test_no_field_gives_empty_title(self):
        title, _ = self._title("Node", "", "", "", "")
        assert title == ""


class _FakeHost:
    def __init__(self):
        self.visible = None

    def setVisible(self, value):
        self.visible = bool(value)


class _FakeLayout:
    def __init__(self):
        self.widgets = []

    def removeWidget(self, widget):
        if widget in self.widgets:
            self.widgets.remove(widget)

    def insertWidget(self, index, widget):
        self.widgets.insert(index, widget)


class _FakePopout:
    def __init__(self):
        self.controls = None
        self._visible = False

    def attachControls(self, bar):
        self.controls = bar

    def detachControls(self, bar):
        if self.controls is bar:
            self.controls = None

    def isVisible(self):
        return self._visible


class _DistLifecycleHarness(_ResultsDistributionMixin):
    def __init__(self, active):
        self._active = active
        self._distribution_popout = None
        self.nodeDistributionChartHost = _FakeHost()
        self.linkDistributionChartHost = _FakeHost()
        self.distributionChartContainer = _FakeHost()
        self.verticalLayout_DistributionChart = _FakeLayout()
        self._dist_controls_bar = object()
        self.verticalLayout_DistributionChart.widgets.append(self._dist_controls_bar)

    def _activeDistributionLayerType(self):
        return self._active


class TestDistributionPanelVisibility:
    def test_active_chart_shown(self):
        harness = _DistLifecycleHarness("Node")
        harness._applySmallChartVisibility()
        assert harness.nodeDistributionChartHost.visible is True
        assert harness.linkDistributionChartHost.visible is False

    def test_panel_hidden_when_no_active_layer(self):
        harness = _DistLifecycleHarness(None)
        harness._syncDistributionPanelVisibility()
        assert harness.distributionChartContainer.visible is False


class TestDistributionControlsTravel:
    def test_expand_moves_controls_and_hides_panel(self):
        harness = _DistLifecycleHarness("Node")
        harness._distribution_popout = _FakePopout()
        harness._moveControlsToPopout()
        assert harness._distribution_popout.controls is harness._dist_controls_bar
        assert harness._dist_controls_bar not in harness.verticalLayout_DistributionChart.widgets
        assert harness.distributionChartContainer.visible is False

    def test_collapse_returns_controls_and_shows_panel(self):
        harness = _DistLifecycleHarness("Link")
        harness._distribution_popout = _FakePopout()
        harness._moveControlsToPopout()
        harness._restoreControlsToDock()
        assert harness._distribution_popout.controls is None
        assert harness._dist_controls_bar in harness.verticalLayout_DistributionChart.widgets
        assert harness.distributionChartContainer.visible is True
        assert harness.linkDistributionChartHost.visible is True

    def test_collapse_keeps_panel_hidden_without_active_layer(self):
        harness = _DistLifecycleHarness(None)
        harness._distribution_popout = _FakePopout()
        harness._restoreControlsToDock()
        assert harness.distributionChartContainer.visible is False


class _FakeFeatureFields:
    def __init__(self, names):
        self._names = names

    def names(self):
        return self._names


class _FakeFeature:
    def __init__(self, attributes):
        self._attributes = attributes

    def fields(self):
        return _FakeFeatureFields(list(self._attributes.keys()))

    def __getitem__(self, name):
        return self._attributes[name]


class TestIncludeFeatureForDistribution:
    def test_headloss_includes_pipes_with_unit_headloss(self):
        feature = _FakeFeature({"UnitHdLoss": 12.5, "HeadLoss": 3.0})
        assert _include_feature_for_distribution(feature, "HeadLoss") is True
        assert _include_feature_for_distribution(feature, "UnitHdLoss") is True

    def test_headloss_excludes_pumps_and_valves(self):
        feature = _FakeFeature({"UnitHdLoss": None, "HeadLoss": 20.0})
        assert _include_feature_for_distribution(feature, "HeadLoss") is False
        assert _include_feature_for_distribution(feature, "UnitHdLoss") is False

    def test_other_fields_unfiltered(self):
        feature = _FakeFeature({"UnitHdLoss": None, "Flow": 10.0})
        assert _include_feature_for_distribution(feature, "Flow") is True

    def test_demand_includes_positive_junction_only(self):
        junction = _FakeFeature({"Type": "JUNCTION", "Demand": 5.0})
        assert _include_feature_for_distribution(junction, "Demand") is True

    def test_demand_excludes_tank_reservoir_and_non_positive(self):
        tank = _FakeFeature({"Type": "TANK", "Demand": 8.0})
        reservoir = _FakeFeature({"Type": "RESERVOIR", "Demand": 12.0})
        negative = _FakeFeature({"Type": "JUNCTION", "Demand": -3.0})
        assert _include_feature_for_distribution(tank, "Demand") is False
        assert _include_feature_for_distribution(reservoir, "Demand") is False
        assert _include_feature_for_distribution(negative, "Demand") is False


class TestFormatRangeLabel:
    def test_formats_interval(self):
        assert _format_range_label(0.0, 10.0) == "0.00 - 10.00"


class TestParseCategoryFromFilter:
    def test_reads_status_literal(self):
        expression = '"Status" = \'Open\''
        assert _parse_category_from_filter(expression, "Status") == "Open"


class _FakeRule:
    def __init__(self, expression, label="range"):
        self._expression, self._label = expression, label

    def filterExpression(self):
        return self._expression

    def label(self):
        return self._label

    def symbol(self):
        symbol = MagicMock()
        symbol.color.return_value = "color"
        return symbol


class _FakeRuleBasedRenderer:
    def __init__(self, *rules):
        root = MagicMock()
        root.children.return_value = list(rules)
        self._root = root

    def rootRule(self):
        return self._root


class _FakeLayer:
    def __init__(self, renderer, features=()):
        self._renderer, self._features = renderer, list(features)

    def renderer(self):
        return self._renderer

    def getFeatures(self):
        return list(self._features)

    def customProperty(self, _name):
        return ""


def _extract(renderer, field="Velocity"):
    module = "QGISRed.ui.analysis.qgisred_results_distribution."
    with patch(module + "QgsRuleBasedRenderer", _FakeRuleBasedRenderer), \
         patch(module + "QgsGraduatedSymbolRenderer", type("_G", (), {})), \
         patch(module + "QgsCategorizedSymbolRenderer", type("_C", (), {})):
        return extract_legend_classes(_FakeLayer(renderer), field)


class TestLegendClassesFromRules:
    """The rules applyNullStyle leaves on a results layer, as QGIS 3.44 writes them.

    The outer classes carry a single bound. Rejecting them dropped the whole numeric
    read, the classes were then taken as categorical -their own labels as values- and
    every bar came out at zero on the histogram.
    """

    RULES = [
        ("<0.1", "(Velocity) <= 0.1000000000000000"),
        ("0.1-0.5", "(Velocity) > 0.1000000000000000 AND (Velocity) <= 0.5000000000000000"),
        ("0.5-1", "(Velocity) > 0.5000000000000000 AND (Velocity) <= 1.0000000000000000"),
        (">1", "(Velocity) > 1.0000000000000000"),
    ]

    def _renderer(self):
        rules = [_FakeRule(expression, label) for label, expression in self.RULES]
        return _FakeRuleBasedRenderer(*rules, _FakeRule("ELSE", label=_NULL_RULE_LABEL))

    def test_the_classes_are_read_as_numeric(self):
        classes, mode = _extract(self._renderer())

        assert mode == "numeric"
        assert [c["label"] for c in classes] == ["<0.1", "0.1-0.5", "0.5-1", ">1"]

    def test_the_open_ends_reach_the_sentinel_bound(self):
        classes, _mode = _extract(self._renderer())

        assert (classes[0]["lo"], classes[0]["hi"]) == (-OPEN_RANGE_BOUND, 0.1)
        assert (classes[-1]["lo"], classes[-1]["hi"]) == (1.0, OPEN_RANGE_BOUND)

    def test_a_column_quoted_the_other_way_is_read_too(self):
        renderer = _FakeRuleBasedRenderer(_FakeRule('"Pressure" >= 10 AND "Pressure" <= 20'))

        classes, mode = _extract(renderer, field="Pressure")

        assert mode == "numeric"
        assert (classes[0]["lo"], classes[0]["hi"]) == (10.0, 20.0)

    def test_features_land_in_the_open_ended_classes(self):
        module = "QGISRed.ui.analysis.qgisred_results_distribution."
        layer = _FakeLayer(self._renderer(), [
            _FakeFeature({"Velocity": 0.05}),   # <0.1
            _FakeFeature({"Velocity": 0.3}),    # 0.1-0.5
            _FakeFeature({"Velocity": 7.0}),    # >1
            _FakeFeature({"Velocity": 9.0}),    # >1
        ])
        with patch(module + "QgsRuleBasedRenderer", _FakeRuleBasedRenderer), \
             patch(module + "QgsGraduatedSymbolRenderer", type("_G", (), {})), \
             patch(module + "QgsCategorizedSymbolRenderer", type("_C", (), {})):
            bins, _x_label = build_distribution_bins(layer, "Velocity")

        assert [b["count"] for b in bins] == [1, 1, 0, 2]

    def test_rules_that_name_no_value_are_not_turned_into_empty_bars(self):
        # Neither a range nor a "Field" = 'value' filter: no class can be counted, and
        # saying so leaves the chart showing "No data" instead of bars stuck at zero.
        renderer = _FakeRuleBasedRenderer(_FakeRule("\"Status\" LIKE '%Closed%'", label="Closed"))

        assert _extract(renderer, field="Status") == ([], None)


class TestFindClassIndex:
    def test_numeric_last_interval_is_inclusive(self):
        classes = [
            {"lo": 0.0, "hi": 5.0, "category": None},
            {"lo": 5.0, "hi": 10.0, "category": None},
        ]
        assert _find_class_index(classes, "numeric", 10.0) == 1
        assert _find_class_index(classes, "numeric", 5.0) == 1

    def test_categorical_matches_category_value(self):
        classes = [{"category": "Open", "lo": None, "hi": None}]
        assert _find_class_index(classes, "categorical", "Open") == 0
