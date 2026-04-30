# -*- coding: utf-8 -*-
import math
import sys
from unittest.mock import MagicMock

from QGISRed.tools.utils.qgisred_axis_scale_utils import compute_nice_scale


def test_axis_series_data_filters_non_finite_and_huge_values_to_prevent_overflow():
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

    w = TimeSeriesPlotWidget()

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

