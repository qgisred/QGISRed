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
        ["Time (h)", "Time of day", "Junction J1\nDemand (l/s)"],
        [
            ["0:00", "12am", "1.2"],
            ["1:00", "1am", "2.4"],
        ],
    )

    assert d._valuesTableClipboardText([0, 1], [0, 1, 2]) == (
        "Time (h)\tTime of day\tJunction J1\nDemand (l/s)\n0:00\t12am\t1.2\n1:00\t1am\t2.4"
    )


def test_values_table_data_matches_table_layout():
    _patch_qt_for_import()
    from unittest.mock import patch

    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock
    from QGISRed.ui.analysis.timeseries_plot_renderer import TimeSeriesPlotRenderer

    class _Plot:
        def _seriesIsDrawn(self, s):
            return True

        series = [
            {
                "x": [0.0, 1.0],
                "y": [10.0, 20.0],
                "magnitude": "Pressure (m)",
                "series_key": "Node:layer:Pressure:J1",
                "legend_type": "Node",
            },
            {
                "x": [0.0, 1.0],
                "y": [1.2, 2.4],
                "magnitude": "Flow (gpm)",
                "series_key": "Link:layer:Flow:P1",
                "legend_type": "Link",
            },
        ]

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.tr = lambda message: message
    d.plot = _Plot()
    d.plot._renderer = TimeSeriesPlotRenderer()
    d.plot._axis_cfg_x = type("C", (), {"x_hour_format": "hm"})()
    d.plot._start_clock_seconds = 0
    d._plotHasCurves = lambda: True

    with patch("QGISRed.ui.analysis.timeseries_plot_renderer.QGISRedFieldUtils") as mock_fu:
        mock_fu.return_value.getDecimals.return_value = 2
        result = d._valuesTableData()
    assert result is not None
    table_headers, csv_header_rows, rows, xs = result
    assert xs == [0.0, 1.0]
    assert table_headers[0] == "Time (h)"
    assert table_headers[1] == "Time of day"
    assert table_headers[2] == "Node J1\nPressure (m)"
    assert table_headers[3] == "Link P1\nFlow (gpm)"
    assert csv_header_rows[0][2] == "Node J1"
    assert csv_header_rows[1][2] == "Pressure (m)"
    assert csv_header_rows[0][0] == "Time (h)"
    assert csv_header_rows[1][0] == ""
    assert rows[0][0] == "0:00"
    assert rows[0][1] == "12am"
    assert rows[0][2] == "10.00"
    assert rows[1][2] == "20.00"


def test_values_table_uses_get_decimals_from_series_key():
    _patch_qt_for_import()
    from unittest.mock import patch

    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock
    from QGISRed.ui.analysis.timeseries_plot_renderer import TimeSeriesPlotRenderer

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = type("_Plot", (), {"_renderer": TimeSeriesPlotRenderer()})()
    series = {"series_key": "Node:layer:Pressure:J1", "y_categorical_labels": None}

    with patch("QGISRed.ui.analysis.timeseries_plot_renderer.QGISRedFieldUtils") as mock_fu:
        mock_fu.return_value.getDecimals.return_value = 1
        text = d._seriesDisplayValue(series, 12.3456)

    mock_fu.return_value.getDecimals.assert_called_once_with("Nodes", "Pressure")
    assert text == "12.3"


def test_format_cursor_time_text_follows_results_dock():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    class _ResultsDock:
        civilMode = True
        amPmFormat = False
        continuousHoursMode = False

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._resultsDock = _ResultsDock()
    d.plot = type("P", (), {"_start_clock_seconds": 0, "_axis_cfg_x": type("C", (), {"x_hour_format": "hm"})()})()
    d.plot._renderer = type("R", (), {})()
    from QGISRed.ui.analysis.timeseries_plot_renderer import TimeSeriesPlotRenderer

    d.plot._renderer = TimeSeriesPlotRenderer()
    assert d._formatCursorTimeText(0.0) == "0:00"
    d._resultsDock.civilMode = False
    d._resultsDock.continuousHoursMode = True
    assert d._formatCursorTimeText(34.5) == "34:30"


def test_parse_results_time_text_to_hours_matches_results_dock():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    class _ResultsDock:
        lbl_singlePeriod = "Single Period"

        @staticmethod
        def _elapsedTextToHours(text):
            text = (text or "").strip()
            if not text or text == "Single Period":
                return 0.0
            days = 0
            hms_text = text
            if "d" in text:
                parts = text.split()
                days = int(parts[0].replace("d", ""))
                hms_text = parts[1]
            hms = hms_text.split(":")
            if len(hms) == 2:
                return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60) / 3600.0
            return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])) / 3600.0

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.tr = lambda message: message
    d._resultsDock = _ResultsDock()

    assert d._parseResultsTimeTextToHours("0:00:00") == 0.0
    assert d._parseResultsTimeTextToHours("10d 0:00") == 240.0
    assert d._parseResultsTimeTextToHours("1:30") == 1.5
    assert d._parseResultsTimeTextToHours("Single Period") == 0.0


def test_global_series_table_header_two_lines_system_and_abbreviated(monkeypatch):
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    monkeypatch.setattr(
        "QGISRed.ui.analysis.timeseries_globals.tr",
        lambda message, *_args, **_kwargs: message,
    )
    monkeypatch.setattr(
        "QGISRed.ui.analysis.timeseries_globals.global_variable_unit_abbreviation",
        lambda _key: "gpm",
    )

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.tr = lambda message: message
    series_legacy = {
        "label": "Total Water Supply",
        "magnitude": "Total Water Supply (LPS)",
        "series_key": "Global:global:TotalWaterSupply:TotalWaterSupply",
        "legend_type": "global",
    }
    assert d._seriesTableColumnHeaderParts(series_legacy) == ("System", "Supply (gpm)")
    assert d._seriesTableColumnHeaderLabel(series_legacy) == "System\nSupply (gpm)"

    series_current = {
        "label": "Total Water Supply (LPS)",
        "magnitude": "System",
        "series_key": "Global:global:TotalWaterDemand:TotalWaterDemand",
        "legend_type": "global",
    }
    assert d._seriesTableColumnHeaderParts(series_current) == ("System", "Demand (gpm)")
    assert d._seriesTableColumnHeaderLabel(series_current) == "System\nDemand (gpm)"


def test_series_table_column_header_two_lines():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.tr = lambda message: message
    series = {
        "magnitude": "Pressure (m)",
        "series_key": "Node:layer:Pressure:J1",
        "legend_type": "Node",
    }
    assert d._seriesTableColumnHeaderParts(series) == ("Node J1", "Pressure (m)")
    assert d._seriesTableColumnHeaderLabel(series) == "Node J1\nPressure (m)"


def test_values_table_clipboard_text_for_selected_rows():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    selected = [_Index(0, 0), _Index(0, 1), _Index(0, 2), _Index(2, 0), _Index(2, 1), _Index(2, 2)]
    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._table = _FakeTable(
        ["Time (h)", "Time of day", "Junction J1\nDemand (l/s)"],
        [
            ["0:00", "12am", "1.2"],
            ["1:00", "1am", "2.4"],
            ["2:00", "2am", "3.6"],
        ],
        selected,
    )

    rows, cols = d._tableSelectedRowsAndColumns(d._table)
    assert d._valuesTableClipboardText(rows, cols) == (
        "Time (h)\tTime of day\tJunction J1\nDemand (l/s)\n0:00\t12am\t1.2\n2:00\t2am\t3.6"
    )

