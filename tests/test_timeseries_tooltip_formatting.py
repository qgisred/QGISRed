# -*- coding: utf-8 -*-
import pytest


from QGISRed.ui.analysis.timeseries_plot_renderer import TimeSeriesPlotRenderer


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
            (24.0, "1d"),
            (34.0, "1d 10h"),
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
