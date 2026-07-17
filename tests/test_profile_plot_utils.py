# -*- coding: utf-8 -*-
from QGISRed.tools.utils.qgisred_profile_plot_utils import (
    profile_line_segments,
    nearest_visible_point,
    cursor_snapshot,
    format_profile_value,
    resolve_envelope_mode,
    truncate_id,
    profile_variable_color_hex,
    label_with_unit,
    joined_labels,
    profile_x_range,
    profile_data_area,
    series_path_key,
    series_path_keys,
    series_for_path,
    path_key_for_node_id,
    point_segment_distance,
    polyline_pixel_distance,
    nearest_path_key,
)


def _paths_series():
    return [
        {"label": "Head", "display_label": "Head (m)", "points": [(0.0, 50.0), (100.0, 48.0)],
         "node_ids": ["N1", "N2"], "path_key": "main", "path_label": "Main path"},
        {"label": "Branch 1", "readout_label": "Head (m)", "points": [(100.0, 46.0), (200.0, 44.0)],
         "node_ids": ["N2", "N3"], "path_key": "branch_0", "path_label": "Branch 1"},
    ]


def test_profile_data_area_leaves_margin_on_sides_and_top():
    assert profile_data_area(64.0, 54.0, 700.0, 400.0, side_pad=12.0, top_pad=14.0) == (76.0, 68.0, 688.0, 400.0)


def test_profile_data_area_keeps_baseline_at_the_bottom_axis():
    assert profile_data_area(64.0, 54.0, 700.0, 400.0)[3] == 400.0


def test_profile_data_area_drops_side_pad_when_plot_is_too_narrow():
    left, _top, right, _bottom = profile_data_area(64.0, 54.0, 74.0, 400.0)
    assert (left, right) == (64.0, 74.0)


def test_profile_data_area_drops_top_pad_when_plot_is_too_short():
    _left, top, _right, bottom = profile_data_area(64.0, 54.0, 700.0, 58.0)
    assert (top, bottom) == (54.0, 58.0)


def test_joined_labels_head_axis_title():
    title = label_with_unit(joined_labels(["Elevation", "Head"]), "m")
    assert title == "Elevation, Head (m)"


def test_joined_labels_dedups_preserving_order():
    assert joined_labels(["Elevation", "Head", "Elevation"]) == "Elevation, Head"


def test_joined_labels_skips_blanks():
    assert joined_labels(["Elevation", "", None, "Head"]) == "Elevation, Head"


def test_joined_labels_empty():
    assert joined_labels([]) == ""
    assert joined_labels(None) == ""


def test_joined_labels_single_label_has_no_comma():
    assert label_with_unit(joined_labels(["Pressure"]), "m") == "Pressure (m)"


def test_profile_x_range_ends_exactly_at_last_node():
    assert profile_x_range(0.0, 1234.0) == (0.0, 1234.0)


def test_profile_x_range_keeps_offset_start():
    assert profile_x_range(150.0, 980.5) == (150.0, 980.5)


def test_profile_x_range_degenerate_gets_unit_width():
    assert profile_x_range(50.0, 50.0) == (50.0, 51.0)


def test_profile_x_range_no_dead_zone_versus_nice_scale():
    from QGISRed.tools.utils.qgisred_axis_scale_utils import compute_nice_scale

    nice = compute_nice_scale(0.0, 1234.0, 8)
    _x0, x1 = profile_x_range(0.0, 1234.0)
    assert nice.axis_max > 1234.0
    assert x1 == 1234.0


def test_profile_x_range_visible_ticks_stay_on_nice_values():
    from QGISRed.tools.utils.qgisred_axis_scale_utils import compute_nice_scale

    x0, x1 = profile_x_range(0.0, 1234.0)
    ticks = [t for t in compute_nice_scale(x0, x1, 8).ticks() if x0 - 1e-9 <= t <= x1 + 1e-9]
    assert ticks == [0.0, 200.0, 400.0, 600.0, 800.0, 1000.0, 1200.0]


def test_label_with_unit_appends_unit():
    assert label_with_unit("Pressure", "m") == "Pressure (m)"


def test_label_with_unit_without_unit_is_plain_label():
    assert label_with_unit("Pressure", "") == "Pressure"
    assert label_with_unit("Pressure", None) == "Pressure"


def test_label_with_unit_ignores_blank_unit():
    assert label_with_unit("Distance", "   ") == "Distance"


def test_cursor_snapshot_prefers_display_label():
    series = [
        {"label": "Pressure", "display_label": "Pressure (m)", "color": "c1",
         "points": [(0.0, 40.0), (50.0, 35.0)]},
    ]
    snap = cursor_snapshot(series, 0.0)
    assert [e["label"] for e in snap["entries"]] == ["Pressure (m)"]


def test_cursor_snapshot_falls_back_to_label():
    series = [{"label": "Branch 1", "color": "c1", "points": [(0.0, 40.0)]}]
    snap = cursor_snapshot(series, 0.0)
    assert [e["label"] for e in snap["entries"]] == ["Branch 1"]


def test_profile_variable_color_hex_known_keys():
    assert profile_variable_color_hex("Pressure") == "#729b6f"
    assert profile_variable_color_hex("Head") == "#1f78b4"
    assert profile_variable_color_hex("Quality") == "#8d5a99"
    assert profile_variable_color_hex("Elevation") == "#8c643c"
    assert profile_variable_color_hex("HeadLoss") == "#becf50"


def test_profile_variable_color_hex_unknown_key():
    assert profile_variable_color_hex("Demand") == ""


def test_profile_variable_colors_are_distinct():
    from QGISRed.tools.utils.qgisred_profile_plot_utils import PROFILE_VARIABLE_COLORS

    values = list(PROFILE_VARIABLE_COLORS.values())
    assert len(values) == len(set(values))


def test_resolve_envelope_mode_off():
    assert resolve_envelope_mode("off") == (False, False)


def test_resolve_envelope_mode_band_only():
    assert resolve_envelope_mode("band") == (True, False)


def test_resolve_envelope_mode_lines_only():
    assert resolve_envelope_mode("lines") == (False, True)


def test_resolve_envelope_mode_both():
    assert resolve_envelope_mode("both") == (True, True)


def test_resolve_envelope_mode_unknown_is_off():
    assert resolve_envelope_mode("") == (False, False)


def test_line_segments_all_visible():
    pts = [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]
    assert profile_line_segments(pts) == [[(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]]


def test_line_segments_split_on_none():
    pts = [(0.0, 1.0), (1.0, 2.0), (2.0, None), (3.0, 4.0), (4.0, 5.0)]
    assert profile_line_segments(pts) == [[(0.0, 1.0), (1.0, 2.0)], [(3.0, 4.0), (4.0, 5.0)]]


def test_line_segments_isolated_point_has_no_segment():
    pts = [(0.0, 1.0), (1.0, None), (2.0, 3.0), (3.0, None)]
    assert profile_line_segments(pts) == []


def test_nearest_visible_point_skips_none():
    pts = [(0.0, None), (10.0, 5.0), (20.0, 6.0)]
    assert nearest_visible_point(pts, 9.0) == (1, 10.0, 5.0)
    assert nearest_visible_point(pts, 100.0) == (2, 20.0, 6.0)


def test_nearest_visible_point_all_none():
    assert nearest_visible_point([(0.0, None), (1.0, None)], 0.5) is None


def test_cursor_snapshot_per_series_nearest():
    series = [
        {"label": "Head", "color": "c1", "points": [(0.0, 80.0), (50.0, 70.0), (100.0, 60.0)]},
        {"label": "Elevation", "color": "c2", "points": [(0.0, 30.0), (50.0, 25.0), (100.0, 20.0)]},
    ]
    snap = cursor_snapshot(series, 48.0)
    assert snap["index"] == 1
    assert snap["distance"] == 50.0
    vals = [(e["label"], e["value"]) for e in snap["entries"]]
    assert vals == [("Head", 70.0), ("Elevation", 25.0)]


def test_cursor_snapshot_uses_nearest_visible_per_series():
    series = [
        {"label": "A", "color": "c1", "points": [(0.0, 1.0), (10.0, 2.0)]},
        {"label": "B", "color": "c2", "points": [(0.0, None), (10.0, 9.0)]},
    ]
    snap = cursor_snapshot(series, 0.0)
    assert snap["index"] == 0
    vals = {e["label"]: e["value"] for e in snap["entries"]}
    assert vals == {"A": 1.0, "B": 9.0}


def test_cursor_snapshot_branch_offset_uses_own_point():
    # A branch is offset along X and has a different length; each series must
    # report the value at ITS own nearest point, not the main series' index.
    series = [
        {"label": "Main", "color": "c1", "points": [(0.0, 10.0), (100.0, 20.0), (200.0, 30.0)]},
        {"label": "Branch", "color": "c2",
         "points": [(100.0, 15.0), (150.0, 25.0), (180.0, 28.0), (250.0, 40.0)]},
    ]
    snap = cursor_snapshot(series, 250.0)
    assert snap["index"] == 2
    assert snap["distance"] == 250.0
    vals = {e["label"]: e["value"] for e in snap["entries"]}
    assert vals["Main"] == 30.0
    assert vals["Branch"] == 40.0


def test_cursor_snapshot_empty():
    assert cursor_snapshot([], 0.0) is None


def test_format_profile_value():
    assert format_profile_value(None) == "-"
    assert format_profile_value(153.27) == "153.3"
    assert format_profile_value(29.4) == "29.40"
    assert format_profile_value(0.512) == "0.512"


def test_truncate_id_short():
    assert truncate_id("N1") == "N1"
    assert truncate_id("1234567890") == "1234567890"


def test_truncate_id_long():
    assert truncate_id("VeryLongNodeId12345") == "VeryLongNo…"
    assert truncate_id(1234567890123) == "1234567890…"


def test_truncate_id_empty():
    assert truncate_id(None) == ""


def test_cursor_snapshot_node_id():
    series = [
        {"label": "Head", "color": "c1", "points": [(0.0, 80.0), (50.0, 70.0), (100.0, 60.0)],
         "node_ids": ["A", "B", "C"]},
        {"label": "Elevation", "color": "c2", "points": [(0.0, 30.0), (50.0, 25.0), (100.0, 20.0)]},
    ]
    snap = cursor_snapshot(series, 48.0)
    assert snap["node_id"] == "B"


def test_cursor_snapshot_node_id_absent():
    series = [{"label": "A", "color": "c1", "points": [(0.0, 1.0), (10.0, 2.0)]}]
    snap = cursor_snapshot(series, 0.0)
    assert snap["node_id"] is None


def test_cursor_snapshot_node_id_from_snap_owner():
    series = [
        {"label": "Main", "color": "c1",
         "points": [(0.0, 10.0), (100.0, 20.0), (200.0, 30.0)],
         "node_ids": ["A", "B", "C"]},
        {"label": "Branch", "color": "c2",
         "points": [(100.0, 15.0), (150.0, 25.0), (250.0, 40.0)],
         "node_ids": ["B", "X", "Y"]},
    ]
    snap = cursor_snapshot(series, 150.0)
    assert snap["distance"] == 150.0
    assert snap["node_id"] == "X"


def test_series_path_key_defaults_to_main():
    assert series_path_key({"label": "Head"}) == "main"
    assert series_path_key({"label": "B1", "path_key": "branch_0"}) == "branch_0"


def test_series_path_keys_are_unique_and_ordered():
    assert series_path_keys(_paths_series()) == ["main", "branch_0"]


def test_series_for_path_filters_by_key():
    filtered = series_for_path(_paths_series(), "branch_0")
    assert [s["label"] for s in filtered] == ["Branch 1"]


def test_series_for_path_returns_all_when_key_is_none():
    assert len(series_for_path(_paths_series(), None)) == 2


def test_series_for_path_falls_back_when_key_is_unknown():
    assert len(series_for_path(_paths_series(), "branch_9")) == 2


def test_path_key_for_node_id_prefers_first_matching_series():
    assert path_key_for_node_id(_paths_series(), "N2") == "main"
    assert path_key_for_node_id(_paths_series(), "N3") == "branch_0"


def test_path_key_for_node_id_without_match():
    assert path_key_for_node_id(_paths_series(), "ZZ") is None
    assert path_key_for_node_id(_paths_series(), None) is None


def test_point_segment_distance_projects_inside_the_segment():
    assert point_segment_distance(5.0, 3.0, 0.0, 0.0, 10.0, 0.0) == 3.0


def test_point_segment_distance_clamps_beyond_the_ends():
    assert point_segment_distance(-4.0, 3.0, 0.0, 0.0, 10.0, 0.0) == 5.0


def test_point_segment_distance_on_degenerate_segment():
    assert point_segment_distance(3.0, 4.0, 0.0, 0.0, 0.0, 0.0) == 5.0


def test_polyline_pixel_distance_uses_closest_segment():
    pixels = [(0.0, 0.0), (10.0, 0.0), (20.0, 20.0)]
    assert polyline_pixel_distance(pixels, 5.0, 4.0) == 4.0


def test_polyline_pixel_distance_ignores_gaps():
    pixels = [(0.0, 0.0), None, (100.0, 100.0)]
    assert polyline_pixel_distance(pixels, 0.0, 6.0) == 6.0


def test_polyline_pixel_distance_without_points():
    assert polyline_pixel_distance([], 0.0, 0.0) is None


def test_nearest_path_key_picks_the_curve_under_the_cursor():
    entries = [
        {"path_key": "main", "pixels": [(0.0, 0.0), (100.0, 0.0)]},
        {"path_key": "branch_0", "pixels": [(0.0, 50.0), (100.0, 50.0)]},
    ]
    assert nearest_path_key(entries, 50.0, 40.0) == "branch_0"
    assert nearest_path_key(entries, 50.0, 10.0) == "main"


def test_nearest_path_key_keeps_first_entry_on_ties():
    entries = [
        {"path_key": "main", "pixels": [(0.0, 0.0), (100.0, 0.0)]},
        {"path_key": "branch_0", "pixels": [(0.0, 0.0), (100.0, 0.0)]},
    ]
    assert nearest_path_key(entries, 50.0, 10.0) == "main"


def test_nearest_path_key_without_drawable_entries():
    assert nearest_path_key([{"path_key": "main", "pixels": []}], 0.0, 0.0) is None


def test_cursor_snapshot_reports_owner_path():
    snap = cursor_snapshot(series_for_path(_paths_series(), "branch_0"), 190.0)
    assert snap["path_key"] == "branch_0"
    assert snap["path_label"] == "Branch 1"
    assert [e["label"] for e in snap["entries"]] == ["Head (m)"]
    assert snap["node_id"] == "N3"


def test_cursor_snapshot_readout_label_wins_over_label():
    series = [{"label": "Branch 1", "readout_label": "Head (m)", "display_label": "ignored",
               "points": [(0.0, 1.0)]}]
    assert cursor_snapshot(series, 0.0)["entries"][0]["label"] == "Head (m)"


def test_cursor_snapshot_defaults_to_main_path():
    snap = cursor_snapshot([{"label": "Head", "points": [(0.0, 1.0)]}], 0.0)
    assert snap["path_key"] == "main"
    assert snap["path_label"] == ""
