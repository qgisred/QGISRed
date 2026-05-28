# -*- coding: utf-8 -*-
import sys


def _patch_qt_for_import():
    """Allow importing QGISRed.ui.analysis.qgisred_timeseries_dock in tests."""
    from unittest.mock import MagicMock
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

    uic.loadUiType = MagicMock(return_value=(type("FORM_CLASS", (), {}), None))


def test_table_time_of_day_format_dd_hms():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = type("P", (), {"_start_clock_seconds": 0, "_axis_cfg_x": type("C", (), {"x_hour_format": "hm"})()})()
    assert d._format_civil_time_col2(0.0) == "12am"
    assert d._format_civil_time_col2(7.0) == "7am"
    assert d._format_civil_time_col2(24.0).startswith("1d 12am")

    d.plot._start_clock_seconds = 17 * 3600
    assert d._format_civil_time_col2(0.0).startswith("5pm")
    assert "1d" in d._format_civil_time_col2(7.0)

    d.plot._start_clock_seconds = 0
    d.plot._axis_cfg_x.x_hour_format = "hm_ampm"
    assert d._format_civil_time_col2(0.0) == "12am"
    assert d._format_civil_time_col2(12.0) == "12pm"


def test_table_elapsed_decimal_format():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = type("P", (), {"_axis_cfg_x": type("C", (), {"x_hour_format": "h"})()})()
    assert d._format_elapsed_time_col1(0.0) == "0.00"
    assert d._format_elapsed_time_col1(10.5) == "10.50"

    d.plot._axis_cfg_x.x_hour_format = "elapsed_hm"
    assert d._format_elapsed_time_col1(10.5) == "10:30"

