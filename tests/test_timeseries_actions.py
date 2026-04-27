# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest
from qgis.PyQt.QtCore import QPointF, QRectF, Qt

from QGISRed.ui.analysis.timeseries_actions import clear_all_timeseries
from QGISRed.ui.analysis.timeseries_legend_interaction import LegendInteractionController


class _Dock:
    def __init__(self):
        self.updatePlotSeries = MagicMock()


class _SectionLike:
    def __init__(self):
        self.timeSeriesSelection = [{"dummy": 1}]
        self._timeSeriesSelectionKey = "something"
        self.lastTimeSeriesFeature = object()
        self.lastTimeSeriesLayer = object()
        self.lastTimeSeriesCategory = "Node"

        self._timeSeriesResetSelection = MagicMock(
            side_effect=lambda: (setattr(self, "timeSeriesSelection", []), setattr(self, "_timeSeriesSelectionKey", None))
        )
        self._clearTimeSeriesMapSelection = MagicMock()
        self._clearTimeSeriesHighlight = MagicMock()
        self.timeSeriesDock = _Dock()


class TestTimeSeriesActions:
    def test_clear_all_timeseries_resets_state_and_clears_plot(self):
        s = _SectionLike()

        clear_all_timeseries(s)

        assert s.timeSeriesSelection == []
        assert s._timeSeriesSelectionKey is None
        assert s.lastTimeSeriesFeature is None
        assert s.lastTimeSeriesLayer is None
        assert s.lastTimeSeriesCategory is None

        s._timeSeriesResetSelection.assert_called_once()
        s._clearTimeSeriesMapSelection.assert_called_once()
        s._clearTimeSeriesHighlight.assert_called_once()
        s.timeSeriesDock.updatePlotSeries.assert_called_once_with([], "", "", "")


class _Widget:
    def __init__(self):
        self.series = [{"series_key": "a"}, {"series_key": "b"}]
        self._legend_hitboxes = []
        self._legend_delete_hitboxes = []
        self.removed = []
        self.updated = 0

    def update(self):
        self.updated += 1

    def removeSeries(self, idx: int) -> bool:
        self.removed.append(int(idx))
        return True


class TestTimeSeriesLegendActions:
    def test_click_on_delete_hitbox_removes_series(self):
        w = _Widget()
        w._legend_delete_hitboxes = [(QRectF(0, 0, 10, 10), 1)]
        w._legend_hitboxes = [(QRectF(0, 0, 10, 10), 0)]  # overlaps, delete should win

        c = LegendInteractionController(w)
        c.begin(QPointF(5, 5), Qt.KeyboardModifier.NoModifier)

        assert c.apply_delete_if_click() is True
        assert w.removed == [1]

    def test_delete_has_priority_over_toggle_drag(self):
        w = _Widget()
        w._legend_delete_hitboxes = [(QRectF(0, 0, 10, 10), 1)]
        w._legend_hitboxes = [(QRectF(0, 0, 10, 10), 0)]

        c = LegendInteractionController(w)
        c.begin(QPointF(5, 5), Qt.KeyboardModifier.NoModifier)

        # internal state: delete candidate set, drag candidate cleared
        assert c._delete_candidate_idx == 1
        assert c._drag_candidate_idx is None
