# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.timeseries_axis_settings import (
    default_axis_settings,
    default_general_settings,
)
from QGISRed.ui.analysis.timeseries_config_io import (
    next_available_config_name,
    parse_timeseries_config_string,
    serialize_timeseries_config,
)


def _full_curve():
    return {
        "category": "Node",
        "layer_identifier": "qgisred_junctions",
        "element_id": "J1",
        "prop_internal": "Pressure",
        "prop_display": "Pressure",
        "y_label_with_unit": "Pressure (m)",
        "is_stepped": False,
        "y_categorical_labels": None,
        "y_display_decimals": None,
        "y_axis": "left",
        "label": "Junction J1",
        "color": "#0078d7",
        "line_style": "dashed",
        "line_width": 2.5,
        "show_markers": True,
        "marker_symbol": "square",
        "marker_size": 8,
        "marker_color": "#ff0000",
        "marker_hollow": False,
        "show_point_values": True,
        "visible": True,
        "muted": False,
        "highlighted": True,
        "emphasis_mode": "highlighted",
        "legend_font_family": "Arial",
        "legend_font_size": 9,
    }


def _roundtrip(curves, axis_x=None, axis_yl=None, axis_yr=None, general=None):
    axis_x = axis_x or default_axis_settings()
    axis_yl = axis_yl or default_axis_settings()
    axis_yr = axis_yr or default_axis_settings()
    general = general or default_general_settings()
    blob = serialize_timeseries_config(curves, axis_x, axis_yl, axis_yr, general)
    return parse_timeseries_config_string(blob)


class TestTimeSeriesConfigIO:
    def test_full_curve_roundtrips_every_field(self):
        curve = _full_curve()
        parsed = _roundtrip([curve])
        assert len(parsed["curves"]) == 1
        out = parsed["curves"][0]
        for key, value in curve.items():
            assert out[key] == value, f"field {key}: {out[key]!r} != {value!r}"

    def test_categorical_labels_roundtrip(self):
        curve = _full_curve()
        curve["prop_internal"] = "Status"
        curve["is_stepped"] = True
        curve["y_categorical_labels"] = ["Closed", "Active", "Open"]
        parsed = _roundtrip([curve])
        out = parsed["curves"][0]
        assert out["is_stepped"] is True
        assert out["y_categorical_labels"] == ["Closed", "Active", "Open"]

    def test_y_display_decimals_none_and_int(self):
        none_curve = _full_curve()
        int_curve = _full_curve()
        int_curve["element_id"] = "J2"
        int_curve["y_display_decimals"] = 3
        parsed = _roundtrip([none_curve, int_curve])
        assert parsed["curves"][0]["y_display_decimals"] is None
        assert parsed["curves"][1]["y_display_decimals"] == 3

    def test_axis_settings_roundtrip(self):
        axis_x = default_axis_settings()
        axis_x.title = "Elapsed time"
        axis_x.auto_scale = False
        axis_x.fixed_min = 1.5
        axis_x.fixed_max = 24.0
        axis_x.fixed_divisions = 6
        axis_x.show_grid = False
        axis_x.decimal_places = 2
        axis_x.x_hour_format = "ampm"
        parsed = _roundtrip([], axis_x=axis_x)
        out = parsed["axis_x"]
        assert out.title == "Elapsed time"
        assert out.auto_scale is False
        assert out.fixed_min == 1.5
        assert out.fixed_max == 24.0
        assert out.fixed_divisions == 6
        assert out.show_grid is False
        assert out.decimal_places == 2
        assert out.x_hour_format == "ampm"

    def test_general_settings_roundtrip(self):
        general = default_general_settings()
        general.title = "My chart"
        general.title_font_size = 14
        general.legend_position = "bottom"
        general.legend_show_frame = True
        general.legend_symbol_size = 20
        general.plot_bg_hex = "#fafafa"
        parsed = _roundtrip([], general=general)
        out = parsed["general"]
        assert out.title == "My chart"
        assert out.title_font_size == 14
        assert out.legend_position == "bottom"
        assert out.legend_show_frame is True
        assert out.legend_symbol_size == 20
        assert out.plot_bg_hex == "#fafafa"

    def test_empty_curves(self):
        parsed = _roundtrip([])
        assert parsed["curves"] == []
        assert parsed["version"] == "1"


BASE = "Net_TimeSeries_Config.cfg"


class TestNextAvailableConfigName:
    def test_base_free_returns_base(self):
        assert next_available_config_name(BASE, []) == BASE
        assert next_available_config_name(BASE, ["Other.cfg"]) == BASE

    def test_base_taken_returns_first_counter(self):
        assert next_available_config_name(BASE, [BASE]) == "Net_TimeSeries_Config_1.cfg"

    def test_continues_from_highest_existing(self):
        existing = [BASE, "Net_TimeSeries_Config_1.cfg", "Net_TimeSeries_Config_2.cfg"]
        assert next_available_config_name(BASE, existing) == "Net_TimeSeries_Config_3.cfg"

    def test_continues_from_last_value_not_filling_gaps(self):
        existing = [BASE, "Net_TimeSeries_Config_2.cfg"]
        assert next_available_config_name(BASE, existing) == "Net_TimeSeries_Config_3.cfg"

    def test_ignores_other_extensions(self):
        existing = [BASE, "Net_TimeSeries_Config_5.txt"]
        assert next_available_config_name(BASE, existing) == "Net_TimeSeries_Config_1.cfg"

    def test_skips_taken_candidate(self):
        existing = [BASE, "Net_TimeSeries_Config_2.cfg", "Net_TimeSeries_Config_1.cfg"]
        assert next_available_config_name(BASE, existing) == "Net_TimeSeries_Config_3.cfg"

    def test_non_numeric_suffix_ignored(self):
        existing = [BASE, "Net_TimeSeries_Config_final.cfg"]
        assert next_available_config_name(BASE, existing) == "Net_TimeSeries_Config_1.cfg"
