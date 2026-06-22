# -*- coding: utf-8 -*-
from .qgisred_timeseries_dock import TimeSeriesPlotWidget


class ResultsEvolutionPlotWidget(TimeSeriesPlotWidget):
    def __init__(self, parent=None):
        super(ResultsEvolutionPlotWidget, self).__init__(parent)
        self._simplified_cursor_only = True
        self._base_min_w = 180
        self._base_min_h = 150
        self.setMinimumSize(self._base_min_w, self._base_min_h)
        self._updateMinimumWidthForTitle()

    def _legendGroups(self):
        return []

    def wheelEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        event.ignore()

    def contextMenuEvent(self, event):
        event.ignore()
