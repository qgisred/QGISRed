# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest

from QGISRed.ui.analysis.timeseries_plot_renderer import TimeSeriesPlotRenderer
from QGISRed.ui.analysis.timeseries_time_utils import (
    civil_midnight_elapsed_hours,
    format_civil_time,
    format_elapsed_time,
    merge_time_of_day_x_ticks,
    parse_clock_time_to_seconds,
)


class _Rect:
    def __init__(self, left=0.0, top=0.0, width=100.0, height=100.0):
        self._l = float(left)
        self._t = float(top)
        self._w = float(width)
        self._h = float(height)

    def left(self):
        return self._l

    def top(self):
        return self._t

    def width(self):
        return self._w

    def height(self):
        return self._h

    def right(self):
        return self._l + self._w

    def bottom(self):
        return self._t + self._h


class _Widget:
    def __init__(self, series):
        self.series = series

    def tr(self, s):
        return s


class TestTimeFormatting:
    @pytest.mark.parametrize(
        "hours, expected",
        [
            (0.0, "0h"),
            (10.0, "10h"),
            (10.5, "10h 30m"),
            (15.0 / 3600.0, "15s"),
            (10.0 + (30.0 / 60.0) + (15.0 / 3600.0), "10h 30m 15s"),
            (24.0, "1d"),
            (34.0, "1d 10h"),
            (24.0 + (15.0 / 3600.0), "1d 0h 0m 15s"),
        ],
    )
    def test_tooltip_instant_format(self, hours, expected):
        r = TimeSeriesPlotRenderer()
        assert r._format_absolute_time_hours(hours) == expected

    @pytest.mark.parametrize(
        "hours, expected",
        [
            (0.0, "0"),
            (10.0, "10"),
            (10.5, "10:30"),
            (24.0, "0\n1d"),
            (34.0, "10"),
            (48.0, "0\n2d"),
        ],
    )
    def test_axis_tick_format(self, hours, expected):
        r = TimeSeriesPlotRenderer()
        assert r._format_absolute_time_hours_axis(hours) == expected

    def test_time_of_day_axis_uses_start_clock(self):
        r = TimeSeriesPlotRenderer()
        start = parse_clock_time_to_seconds("17:00")

        assert r._format_absolute_time_hours_axis(0.0, hour_format="hm", start_clock_seconds=start) == "17:00"
        assert r._format_absolute_time_hours_axis(7.0, hour_format="hm", start_clock_seconds=start) == "0:00\n1d"
        assert r._format_absolute_time_hours_axis(16.0 + 11.0 / 60.0 + 7.0 / 3600.0, hour_format="hm", start_clock_seconds=start) == "9:11:07"

    def test_elapsed_hm_axis_is_not_time_of_day(self):
        r = TimeSeriesPlotRenderer()
        start = parse_clock_time_to_seconds("17:00")

        assert r._format_absolute_time_hours_axis(7.0, hour_format="elapsed_hm", start_clock_seconds=start) == "7:00"
        assert r._format_absolute_time_hours_axis(24.0, hour_format="elapsed_hm", start_clock_seconds=start) == "0:00\n1d"
        assert r._format_absolute_time_hours_axis(34.0, hour_format="elapsed_hm", day_format="total_hours", start_clock_seconds=start) == "34:00"

    def test_time_of_day_axis_supports_am_pm(self):
        r = TimeSeriesPlotRenderer()
        start = parse_clock_time_to_seconds("17:00")

        assert r._format_absolute_time_hours_axis(0.0, hour_format="hm_ampm", start_clock_seconds=start) == "5:00 pm"
        assert r._format_absolute_time_hours_axis(7.0, hour_format="hm_ampm", start_clock_seconds=start) == "12:00 am\n1d"

    def test_csv_civil_time_includes_day_and_seconds(self):
        start = parse_clock_time_to_seconds("17:00")

        assert format_civil_time(0.0, start) == "17:00"
        assert format_civil_time(16.0 + 11.0 / 60.0 + 7.0 / 3600.0, start) == "1d 9:11:07"

    def test_elapsed_time_csv_format_follows_hour_and_day_options(self):
        assert format_elapsed_time(10.5, hour_format="h", day_format="split_days") == "10.5"
        assert format_elapsed_time(34.5, hour_format="h", day_format="split_days") == "1d 10.5"
        assert format_elapsed_time(34.5, hour_format="h", day_format="total_hours") == "34.5"
        assert format_elapsed_time(34.5, hour_format="elapsed_hm", day_format="split_days") == "1d 10:30"
        assert format_elapsed_time(34.5, hour_format="elapsed_hm", day_format="total_hours") == "34:30"

    def test_civil_midnight_ticks_include_first_day_boundary(self):
        start = parse_clock_time_to_seconds("17:00")

        assert civil_midnight_elapsed_hours(0.0, 10.0, start) == [7.0]

    def test_merge_time_of_day_x_ticks_drops_ticks_near_midnight(self):
        start = parse_clock_time_to_seconds("07:10")
        midnight = round((86400 - 7 * 3600 - 10 * 60) / 3600.0, 9)

        merged = merge_time_of_day_x_ticks(
            [16.0, 17.0, 18.0],
            min_hours=0.0,
            max_hours=48.0,
            start_clock_seconds=start,
            min_sep_hours=0.75,
        )

        assert midnight in merged
        assert 17.0 not in merged
        assert 16.0 in merged

    def test_merge_time_of_day_x_ticks_07_10_start_hourly_axis(self):
        start = parse_clock_time_to_seconds("07:10")
        midnight = round((86400 - 7 * 3600 - 10 * 60) / 3600.0, 9)
        hourly = [float(h) for h in range(49)]

        merged = merge_time_of_day_x_ticks(
            hourly,
            min_hours=0.0,
            max_hours=48.0,
            start_clock_seconds=start,
            min_sep_hours=1.0,
        )

        assert midnight in merged
        for neighbor in (16.0, 17.0, 18.0):
            if abs(neighbor - midnight) < 1.0:
                assert neighbor not in merged


class _StubPoint:
    def __init__(self, x: float, y: float):
        self._x = float(x)
        self._y = float(y)

    def x(self):
        return self._x

    def y(self):
        return self._y


class _StubRect:
    def __init__(self, left=0.0, top=0.0, width=400.0, height=200.0):
        self._l = float(left)
        self._t = float(top)
        self._w = float(width)
        self._h = float(height)

    def left(self):
        return self._l

    def top(self):
        return self._t

    def right(self):
        return self._l + self._w

    def bottom(self):
        return self._t + self._h

    def width(self):
        return self._w


class _StubFontMetrics:
    """Métricas fijas para probar la lógica sin depender de QFontMetrics real/mockeado."""

    def height(self):
        return 12

    def descent(self):
        return 2

    def horizontalAdvance(self, text):
        return max(8, 7 * len(str(text)))


class TestPointValueLabelSelection:
    def test_spread_points_allow_more_labels_on_zoom(self):
        r = TimeSeriesPlotRenderer()
        fm = _StubFontMetrics()
        plot_rect = _StubRect()
        texts = ["1", "2", "3"]
        spread = [_StubPoint(50.0, 50.0), _StubPoint(200.0, 140.0), _StubPoint(340.0, 60.0)]
        indices = r._select_point_value_label_indices(
            spread, texts, fm, plot_rect, x_off=10.0, y_off=-10.0
        )
        assert indices == [0, 1, 2]

    def test_dense_points_limit_labels(self):
        r = TimeSeriesPlotRenderer()
        fm = _StubFontMetrics()
        plot_rect = _StubRect()
        dense = [_StubPoint(20.0 + i * 4.0, 100.0) for i in range(60)]
        texts = ["123.45"] * len(dense)
        indices = r._select_point_value_label_indices(
            dense, texts, fm, plot_rect, x_off=10.0, y_off=-10.0
        )
        assert len(indices) < len(dense)
        assert len(indices) <= 12


class TestMarkerValueFormatting:
    def test_point_value_text_uses_units_table_decimals(self):
        r = TimeSeriesPlotRenderer()
        series = {
            "series_key": "Link:pipes:Flow:P-1",
            "y_categorical_labels": None,
        }
        with patch("QGISRed.ui.analysis.timeseries_plot_renderer.QGISRedFieldUtils") as mock_fu:
            mock_fu.return_value.getDecimals.return_value = 1
            assert r._point_value_text(series, 12.3456) == "12.3"

    def test_point_value_text_without_series_key_keeps_compact_format(self):
        r = TimeSeriesPlotRenderer()
        series = {"series_key": "", "y_categorical_labels": None}
        assert r._point_value_text(series, 12.3456) == "12.346"


class TestTooltipValueFormatting:
    @pytest.mark.parametrize(
        "value, expected",
        [
            (None, ""),
            (0, "0"),
            (12, "12"),
            (12.3, "12.3"),
            (12.3456, "12.346"),
            (99999.99, "99999.99"),
            (100000, "1.000e+05"),
            (-100000, "-1.000e+05"),
        ],
    )
    def test_decimal_until_limit_then_exponential(self, value, expected):
        r = TimeSeriesPlotRenderer()
        assert r._format_value_full(value) == expected


class TestTooltipUnits:
    def test_units_are_appended_with_space(self):
        r = TimeSeriesPlotRenderer()
        w = _Widget(
            [
                {
                    "x": [1.0],
                    "y": [2.0],
                    "label": "Presión",
                    "magnitude": "Presión (m)",
                    "color": "#ff0000",
                }
            ]
        )

        lines, _pts = r._collect_hover_tooltip_data(
            w,
            0,
            1.0,
            _Rect(),
            x_state={"min_x": 0.0, "x_range": 10.0},
            y_state_left={"min_y": 0.0, "max_y": 10.0},
            y_state_right=None,
        )

        assert len(lines) == 1
        _color, _muted, _legend_type, prefix, value, suffix = lines[0]
        assert prefix == "Presión: "
        assert value == "2"
        assert suffix == " m"

    def test_tooltip_line_includes_legend_type(self):
        r = TimeSeriesPlotRenderer()
        w = _Widget(
            [
                {
                    "x": [1.0],
                    "y": [2.0],
                    "label": "Tubería 1",
                    "legend_type": "qgisred_pipes",
                    "magnitude": "Caudal (L/s)",
                    "color": "#00aa00",
                }
            ]
        )

        lines, _pts = r._collect_hover_tooltip_data(
            w,
            0,
            1.0,
            _Rect(),
            x_state={"min_x": 0.0, "x_range": 10.0},
            y_state_left={"min_y": 0.0, "max_y": 10.0},
            y_state_right=None,
        )

        assert len(lines) == 1
        _color, _muted, legend_type, _prefix, _value, _suffix = lines[0]
        assert legend_type == "qgisred_pipes"


class TestAxisUnitExtraction:
    def test_extracts_single_unit(self):
        r = TimeSeriesPlotRenderer()
        assert r._extract_unit_from_magnitude("Presión (m)") == "m"

    def test_extracts_multiple_units_unique_in_order(self):
        r = TimeSeriesPlotRenderer()
        assert r._extract_unit_from_magnitude("Presión (m), Caudal (L/s)") == "m, L/s"
        assert r._extract_unit_from_magnitude("A (m), B (m), C (L/s), D (m)") == "m, L/s"

    def test_axis_title_uses_only_units_when_available(self):
        r = TimeSeriesPlotRenderer()
        assert r._axis_title_from_magnitude("Presión (m)") == "m"
        assert r._axis_title_from_magnitude("Presión (m), Caudal (L/s)") == "m, L/s"

    def test_axis_title_keeps_original_when_no_units(self):
        r = TimeSeriesPlotRenderer()
        assert r._axis_title_from_magnitude("Estado") == "Estado"
