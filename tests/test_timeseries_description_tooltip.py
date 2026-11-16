# -*- coding: utf-8 -*-
from .test_timeseries_values_table_formatting import _patch_qt_for_import


class _Rect:
    def __init__(self, inside):
        self._inside = inside

    def contains(self, _pos):
        return self._inside


def _plot(description="", hover_index=None, overflow_rect=None, overflow_labels=()):
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import TimeSeriesPlotWidget

    p = TimeSeriesPlotWidget.__new__(TimeSeriesPlotWidget)
    p.description = description
    p.hover_index = hover_index
    p._legend_overflow_rect = overflow_rect
    p._legend_overflow_labels = list(overflow_labels)
    return p


def test_description_is_the_tooltip_when_nothing_else_is_shown():
    assert _plot("Sector norte")._tooltipTextAt(None) == "Sector norte"


def test_no_tooltip_without_description():
    assert _plot("")._tooltipTextAt(None) is None


def test_point_hover_tooltip_wins_over_the_description():
    assert _plot("Sector norte", hover_index=3)._tooltipTextAt(None) is None


def test_hidden_legend_curves_win_over_the_description():
    p = _plot("Sector norte", overflow_rect=_Rect(True), overflow_labels=["A", "B"])
    assert p._tooltipTextAt(None) == "A\nB"


def test_description_shows_outside_the_hidden_curves_indicator():
    p = _plot("Sector norte", overflow_rect=_Rect(False), overflow_labels=["A"])
    assert p._tooltipTextAt(None) == "Sector norte"


def test_dock_description_lives_in_the_plot():
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d.plot = _plot()
    d._chartComment = "Sector norte"
    assert d.plot.description == "Sector norte"
    assert d._chartComment == "Sector norte"
