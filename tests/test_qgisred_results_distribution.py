# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.qgisred_results_distribution import (
    _ResultsDistributionMixin,
    _find_class_index,
    _format_range_label,
    _include_link_feature_for_distribution,
    _parse_category_from_filter,
)
from QGISRed.ui.analysis.results_distribution_renderer import (
    ResultsDistributionRenderer,
    format_distribution_hover_value,
    hit_test_cumulative_polyline,
)


class TestFormatDistributionHoverValue:
    def test_absolute_count_as_integer(self):
        assert format_distribution_hover_value(42) == "42"

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


class TestDistributionChartTitleTemplate:
    def test_frequency_title_with_units(self):
        title = (
            _ResultsDistributionMixin._DISTRIBUTION_TITLE_TEMPLATE.replace("%1", "Flow").replace(
                "%2", " (gpm)"
            )
        )
        assert title == "Flow frequency (gpm)"

    def test_frequency_title_without_units(self):
        title = _ResultsDistributionMixin._DISTRIBUTION_TITLE_TEMPLATE.replace("%1", "Pressure").replace(
            "%2", ""
        )
        assert title == "Pressure frequency"


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


class TestIncludeLinkFeatureForDistribution:
    def test_headloss_includes_pipes_with_unit_headloss(self):
        feature = _FakeFeature({"UnitHdLoss": 12.5, "HeadLoss": 3.0})
        assert _include_link_feature_for_distribution(feature, "HeadLoss") is True
        assert _include_link_feature_for_distribution(feature, "UnitHdLoss") is True

    def test_headloss_excludes_pumps_and_valves(self):
        feature = _FakeFeature({"UnitHdLoss": None, "HeadLoss": 20.0})
        assert _include_link_feature_for_distribution(feature, "HeadLoss") is False
        assert _include_link_feature_for_distribution(feature, "UnitHdLoss") is False

    def test_other_fields_unfiltered(self):
        feature = _FakeFeature({"UnitHdLoss": None, "Flow": 10.0})
        assert _include_link_feature_for_distribution(feature, "Flow") is True


class TestFormatRangeLabel:
    def test_formats_interval(self):
        assert _format_range_label(0.0, 10.0) == "0.00 - 10.00"


class TestParseCategoryFromFilter:
    def test_reads_status_literal(self):
        expression = '"Status" = \'Open\''
        assert _parse_category_from_filter(expression, "Status") == "Open"


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
