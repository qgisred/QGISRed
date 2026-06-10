# -*- coding: utf-8 -*-
import math
import sys
from unittest.mock import MagicMock

from QGISRed.tools.utils.qgisred_axis_scale_utils import compute_nice_scale


def test_axis_series_data_filters_non_finite_and_huge_values_to_prevent_overflow():
    w = _timeseries_plot_widget()

    huge_int = 10**400
    w.series = [
        {
            "x": [0, 1, 2, 3, 4, 5],
            "y": [1.0, huge_int, 2.0, float("inf"), float("nan"), 3.0],
        }
    ]

    all_x, all_y, y_cat, any_stepped = w._axisSeriesData(w.series)
    assert y_cat is None
    assert any_stepped is False

    assert all_y == [1.0, 2.0, 3.0]
    assert all(math.isfinite(v) for v in all_y)

    assert w.series[0]["y"] == [1.0, 2.0, 3.0]
    assert w.series[0]["x"] == [0.0, 2.0, 5.0]

    s = compute_nice_scale(min(all_y), max(all_y), max_ticks=2)
    assert math.isfinite(s.axis_min)
    assert math.isfinite(s.axis_max)
    assert s.step > 0


def _timeseries_plot_widget():
    from qgis.PyQt import uic

    qtwidgets = sys.modules.get("qgis.PyQt.QtWidgets")
    if qtwidgets is not None:
        class _DummyQWidget:
            def __init__(self, *args, **kwargs):
                pass

            def setMouseTracking(self, *args, **kwargs):
                return None

            def setMinimumSize(self, *args, **kwargs):
                return None

        qtwidgets.QWidget = _DummyQWidget
        qtwidgets.QDockWidget = type("QDockWidget", (), {})

    uic.loadUiType.return_value = (type("FORM_CLASS", (), {}), None)

    from QGISRed.ui.analysis.qgisred_timeseries_dock import TimeSeriesPlotWidget

    return TimeSeriesPlotWidget()


def test_y_axis_title_includes_unit_for_global_system_series():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "System",
            "y_label_with_unit": "Total Stored Volume (m³)",
            "y_axis": "left",
        },
    ]
    w._assignYAxisByMagnitude()
    assert w._y_label_left == "System (m³)"


def test_y_axis_title_keeps_magnitude_when_units_already_present():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "Pressure (m)",
            "y_label_with_unit": "Pressure (m)",
            "y_axis": "left",
        },
    ]
    w._assignYAxisByMagnitude()
    assert w._y_label_left == "Pressure (m)"


def test_y_axis_title_keeps_system_and_accumulates_units_for_multiple_global_series():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Stored Volume (m³)",
            "y_axis": "left",
        },
        {
            "x": [0, 1],
            "y": [3.0, 4.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Tank Spill Flow (L/s)",
            "y_axis": "left",
        },
    ]
    w._assignYAxisByMagnitude()
    # "System" is not repeated per variable; its units accumulate inside it.
    assert w._y_label_left == "System (m³, L/s)"


def test_y_axis_title_enriches_system_when_sharing_axis_with_unit_bearing_magnitude():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "Pressure (m)",
            "legend_type": "qgisred_junctions",
            "y_label_with_unit": "Pressure (m)",
            "y_axis": "left",
        },
        {
            "x": [0, 1],
            "y": [3.0, 4.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Stored Volume (ft3)",
            "y_axis": "left",
        },
        {
            "x": [0, 1],
            "y": [5.0, 6.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Water Supply (gpm)",
            "y_axis": "right",
        },
    ]
    w._assignYAxisByMagnitude()
    # System keeps its unit even next to a magnitude that already has one, and
    # both axis titles reflect the actual side of each curve.
    assert w._y_label_left == "Pressure (m), System (ft3)"
    assert w._y_label_right == "System (gpm)"


def test_global_series_default_to_right_axis():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Water Supply (gpm)",
        },
        {
            "x": [0, 1],
            "y": [3.0, 4.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Stored Volume (ft3)",
        },
    ]
    w._assignYAxisByMagnitude()
    assert [s["y_axis"] for s in w.series] == ["right", "right"]
    assert w._y_label_right == "System (gpm, ft3)"
    assert w._y_label_left == ""


def test_first_non_system_magnitude_keeps_left_axis_with_system_on_right():
    w = _timeseries_plot_widget()
    w.series = [
        {
            "x": [0, 1],
            "y": [1.0, 2.0],
            "magnitude": "Pressure (m)",
            "legend_type": "qgisred_junctions",
            "y_label_with_unit": "Pressure (m)",
        },
        {
            "x": [0, 1],
            "y": [3.0, 4.0],
            "magnitude": "System",
            "legend_type": "global",
            "y_label_with_unit": "Total Water Supply (gpm)",
        },
    ]
    w._assignYAxisByMagnitude()
    assert [s["y_axis"] for s in w.series] == ["left", "right"]
    assert w._y_label_left == "Pressure (m)"
    assert w._y_label_right == "System (gpm)"

