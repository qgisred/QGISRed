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


class _TextItem:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class _Index:
    def __init__(self, row, col):
        self._row = row
        self._col = col

    def row(self):
        return self._row

    def column(self):
        return self._col


class _SelectionModel:
    def __init__(self, indexes):
        self._indexes = indexes

    def selectedIndexes(self):
        return self._indexes


class _FakeTable:
    def __init__(self, headers, rows, selected_indexes=None):
        self._headers = headers
        self._rows = rows
        self._selection = _SelectionModel(selected_indexes or [])

    def rowCount(self):
        return len(self._rows)

    def columnCount(self):
        return len(self._headers)

    def horizontalHeaderItem(self, col):
        return _TextItem(self._headers[col])

    def item(self, row, col):
        return _TextItem(self._rows[row][col])

    def selectionModel(self):
        return self._selection


def test_values_table_clipboard_text_for_entire_table():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._table = _FakeTable(
        ["Time (h)", "Time of day", "Junction J1 - Demand"],
        [
            ["0:00", "12am", "1.2"],
            ["1:00", "1am", "2.4"],
        ],
    )

    assert d._valuesTableClipboardText([0, 1], [0, 1, 2]) == (
        "Time (h)\tTime of day\tJunction J1 - Demand\n0:00\t12am\t1.2\n1:00\t1am\t2.4"
    )


def test_values_table_clipboard_text_for_selected_rows():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    selected = [_Index(0, 0), _Index(0, 1), _Index(0, 2), _Index(2, 0), _Index(2, 1), _Index(2, 2)]
    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._table = _FakeTable(
        ["Time (h)", "Time of day", "Junction J1 - Demand"],
        [
            ["0:00", "12am", "1.2"],
            ["1:00", "1am", "2.4"],
            ["2:00", "2am", "3.6"],
        ],
        selected,
    )

    rows, cols = d._tableSelectedRowsAndColumns(d._table)
    assert d._valuesTableClipboardText(rows, cols) == (
        "Time (h)\tTime of day\tJunction J1 - Demand\n0:00\t12am\t1.2\n2:00\t2am\t3.6"
    )

