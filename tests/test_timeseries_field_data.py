# -*- coding: utf-8 -*-
from QGISRed.ui.analysis import timeseries_field_data as field_data


def test_plotted_curves_become_requests_and_the_answer_becomes_marker_series():
    series = [
        {"series_key": "Node:qgisred_junctions:Head:N1", "y_label_with_unit": "Head (m)"},
        {"series_key": "Link:qgisred_pipes:Velocity:P:1", "y_label_with_unit": "Velocity (m/s)"},
        {"series_key": "Link:qgisred_pipes:Status:P2", "y_label_with_unit": "Status"},
        {"series_key": "Global::Demand:Demand", "y_label_with_unit": "Demand (lps)"},
    ]

    requests = field_data.build_requests(series)
    curves = field_data.parse_series(
        "OK\nNode:qgisred_junctions:Head:N1\t1800\t52.5\nNode:qgisred_junctions:Head:N1\t3600\t51\nbroken")

    assert requests == ("Node:qgisred_junctions:Head:N1\tN1\tHead\tm\n"
                        "Link:qgisred_pipes:Velocity:P:1\tP:1\tVelocity\tm/s")
    assert curves == {"Node:qgisred_junctions:Head:N1": {"x": [0.5, 1.0], "y": [52.5, 51.0]}}
    assert field_data.sampling_window([0, 3600, 7200, 10800]) == (0.0, 10800.0, 3600.0)
    assert field_data.parse_series("Error: no folder") == {}


def test_field_data_widen_the_axis_and_add_a_single_legend_entry_while_shown():
    from .test_timeseries_axis_series_data import _timeseries_plot_widget

    widget = _timeseries_plot_widget()
    widget.tr = lambda text: text
    widget.update = lambda: None
    widget.series = [
        {"x": [0, 1], "y": [10.0, 12.0], "series_key": "a", "label": "N1", "magnitude": "Pressure (m)"},
        {"x": [0, 1], "y": [1.0, 2.0], "series_key": "b", "label": "N2", "magnitude": "Pressure (m)"},
    ]

    widget.setFieldData({"a": {"x": [0.5], "y": [30.0]}, "b": {"x": [0.5], "y": [1.5]}})
    shown = widget._axisSeriesData(widget.series)[1]
    groups = widget._legendGroups()
    widget.setFieldData({})

    assert max(shown) == 30.0
    assert [title for title, _items in groups] == ["Pressure (m)", "Field data"]
    assert len(groups[-1][1]) == 1
    assert len(widget._legendGroups()) == 1
