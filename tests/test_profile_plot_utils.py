# -*- coding: utf-8 -*-
from QGISRed.tools.utils.qgisred_profile_plot_utils import (
    profile_line_segments,
    nearest_visible_point,
    cursor_snapshot,
    format_profile_value,
    resolve_envelope_mode,
    truncate_id,
)


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


def test_cursor_snapshot_aligns_series_by_index():
    series = [
        {"label": "Head", "color": "c1", "points": [(0.0, 80.0), (50.0, 70.0), (100.0, 60.0)]},
        {"label": "Elevation", "color": "c2", "points": [(0.0, 30.0), (50.0, 25.0), (100.0, 20.0)]},
    ]
    snap = cursor_snapshot(series, 48.0)
    assert snap["index"] == 1
    assert snap["distance"] == 50.0
    assert snap["entries"] == [
        {"label": "Head", "color": "c1", "value": 70.0},
        {"label": "Elevation", "color": "c2", "value": 25.0},
    ]


def test_cursor_snapshot_skips_none_entry():
    series = [
        {"label": "A", "color": "c1", "points": [(0.0, 1.0), (10.0, 2.0)]},
        {"label": "B", "color": "c2", "points": [(0.0, None), (10.0, 9.0)]},
    ]
    snap = cursor_snapshot(series, 0.0)
    assert snap["index"] == 0
    assert snap["entries"] == [{"label": "A", "color": "c1", "value": 1.0}]


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
