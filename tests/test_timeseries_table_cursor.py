# -*- coding: utf-8 -*-
import math


def test_table_cell_click_sets_synced_cursor():
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    class _Plot:
        last_hours = None

        def setSyncedCursorTimeHours(self, hours):
            self.last_hours = float(hours)

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = _Plot()
    d._table_x_hours = [0.0, 1.5, 3.0]
    d.btnSyncCursor = None
    d._onTableCellClicked(1, 2)
    assert d.plot.last_hours == 1.5


def test_table_row_for_hours_picks_nearest_step():
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._table_x_hours = [0.0, 1.0, 2.5, 4.0]
    assert d._tableRowForHours(2.4) == 2
    assert d._tableRowForHours(0.05) == 0


def test_table_cell_click_ignores_invalid_row():
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    class _Plot:
        last_hours = None

        def setSyncedCursorTimeHours(self, hours):
            self.last_hours = hours

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = _Plot()
    d._table_x_hours = [0.0]
    d.btnSyncCursor = None
    d._onTableCellClicked(5, 0)
    assert d.plot.last_hours is None
