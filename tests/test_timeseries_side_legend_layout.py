# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.timeseries_plot_layout import layout_side_legend, place_side_legend

ROW_H = 14
ROW_GAP = 16


def _group(name, count):
    return (name, [(i, None, f"{name} {i}", "qgisred_junctions") for i in range(count)])


def _height_for_rows(rows):
    return (rows - 1) * ROW_GAP + ROW_H


def test_everything_fits_in_one_column():
    groups = [_group("Pressure", 3)]
    headers, placed, hidden = place_side_legend(groups, 0.0, _height_for_rows(4), 1, ROW_H, ROW_GAP)
    assert headers == [(0, 0.0)]
    assert [item[2] for item, _col, _y in placed] == ["Pressure 0", "Pressure 1", "Pressure 2"]
    assert hidden == []


def test_items_that_do_not_fit_are_reported_as_hidden():
    groups = [_group("Pressure", 5)]
    _headers, placed, hidden = place_side_legend(groups, 0.0, _height_for_rows(3), 1, ROW_H, ROW_GAP)
    assert len(placed) == 2
    assert [item[2] for item in hidden] == ["Pressure 2", "Pressure 3", "Pressure 4"]


def test_a_group_whose_header_does_not_fit_is_hidden_whole():
    groups = [_group("Pressure", 2), _group("Flow", 2)]
    _headers, _placed, hidden = place_side_legend(groups, 0.0, _height_for_rows(3), 1, ROW_H, ROW_GAP)
    assert [item[2] for item in hidden] == ["Flow 0", "Flow 1"]


def test_two_columns_split_a_group_in_halves():
    groups = [_group("Pressure", 4)]
    _headers, placed, hidden = place_side_legend(groups, 0.0, _height_for_rows(3), 2, ROW_H, ROW_GAP)
    assert [col for _item, col, _y in placed] == [0, 0, 1, 1]
    assert hidden == []


def test_overflow_keeps_the_last_row_free_for_the_more_indicator():
    groups = [_group("Pressure", 5)]
    bottom = _height_for_rows(4)
    _headers, placed, hidden = layout_side_legend(groups, 0.0, bottom, 1, ROW_H, ROW_GAP)
    assert len(placed) == 2
    assert len(hidden) == 3
    last_item_bottom = max(y for _item, _col, y in placed) + ROW_H
    assert last_item_bottom <= bottom - ROW_H
