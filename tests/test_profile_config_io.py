# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.profile_chart_settings import (
    ProfileAxisSettings, ProfileGeneralSettings, ProfileCurveStyle,
)
from QGISRed.ui.analysis.profile_config_io import (
    serialize_profile_config, parse_profile_config_string,
)


def _sample():
    profile = {
        "variable": "Head",
        "reference_nodes": ["N1", "N5", "N9"],
        "branches": [
            {"reference_nodes": ["N5", "B2"], "offset": 123.5},
        ],
        "options": {"show_symbols": True, "show_labels": False, "envelope_mode": "band"},
    }
    axis_x = ProfileAxisSettings(title="Distance", auto_scale=False, fixed_min=0.0, fixed_max=1000.0, show_grid=True)
    axis_y = ProfileAxisSettings(title="Head", auto_scale=True, show_grid=False)
    general = ProfileGeneralSettings(show_legend=True, plot_bg_hex="#fafcff", legend_position="right",
                                     legend_font_size=9, legend_symbol_size=22, legend_show_frame=True,
                                     legend_bg_hex="#eeeeee")
    overrides = {
        "Head": ProfileCurveStyle(color_hex="#1f77b4", width=2.5, line_style="dashed",
                                  show_markers=True, marker_size=3.0),
        "Elevation": ProfileCurveStyle(color_hex="#8c643c", width=1.5, line_style="solid",
                                       show_markers=False, marker_size=2.0),
    }
    return profile, axis_x, axis_y, general, overrides


def test_roundtrip_profile():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides, comment="My profile")
    parsed = parse_profile_config_string(blob)

    assert parsed["comment"] == "My profile"
    assert parsed["variable"] == "Head"
    assert parsed["reference_nodes"] == ["N1", "N5", "N9"]
    assert parsed["options"] == {"show_symbols": True, "show_labels": False, "envelope_mode": "band"}


def test_roundtrip_branches():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides)
    parsed = parse_profile_config_string(blob)

    assert len(parsed["branches"]) == 1
    assert parsed["branches"][0]["reference_nodes"] == ["N5", "B2"]
    assert parsed["branches"][0]["offset"] == 123.5


def test_roundtrip_axes_and_general():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides)
    parsed = parse_profile_config_string(blob)

    assert parsed["axis_x"].title == "Distance"
    assert parsed["axis_x"].auto_scale is False
    assert parsed["axis_x"].fixed_max == 1000.0
    assert parsed["axis_y"].show_grid is False
    assert parsed["general"].legend_position == "right"
    assert parsed["general"].legend_font_size == 9
    assert parsed["general"].legend_show_frame is True


def test_roundtrip_curve_overrides():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides)
    parsed = parse_profile_config_string(blob)

    head = parsed["curve_overrides"]["Head"]
    assert head.color_hex == "#1f77b4"
    assert head.width == 2.5
    assert head.line_style == "dashed"
    elev = parsed["curve_overrides"]["Elevation"]
    assert elev.show_markers is False
    assert elev.marker_size == 2.0


def test_comment_only_reader():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides, comment="Hello")
    import xml.etree.ElementTree as ET
    root = ET.fromstring(blob)
    assert (root.find("Comment").text or "") == "Hello"


def test_roundtrip_secondary_and_right_axis():
    profile, axis_x, axis_y, general, overrides = _sample()
    profile["secondary_variable"] = "Quality"
    axis_y_right = ProfileAxisSettings(title="Quality", auto_scale=True, show_grid=False)
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides, axis_y_right=axis_y_right)
    parsed = parse_profile_config_string(blob)
    assert parsed["secondary_variable"] == "Quality"
    assert parsed["axis_y_right"].title == "Quality"
    assert parsed["axis_y_right"].show_grid is False


def test_secondary_defaults_empty():
    profile, axis_x, axis_y, general, overrides = _sample()
    blob = serialize_profile_config(profile, axis_x, axis_y, general, overrides)
    parsed = parse_profile_config_string(blob)
    assert parsed["secondary_variable"] == ""


def test_empty_config():
    profile = {"variable": "", "reference_nodes": [], "branches": [], "options": {}}
    blob = serialize_profile_config(profile, ProfileAxisSettings(), ProfileAxisSettings(),
                                    ProfileGeneralSettings(), {})
    parsed = parse_profile_config_string(blob)
    assert parsed["reference_nodes"] == []
    assert parsed["branches"] == []
    assert parsed["curve_overrides"] == {}
