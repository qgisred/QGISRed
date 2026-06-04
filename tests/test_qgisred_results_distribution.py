# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.qgisred_results_distribution import (
    _ResultsDistributionMixin,
    _find_class_index,
    _format_range_label,
    _parse_category_from_filter,
)


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
