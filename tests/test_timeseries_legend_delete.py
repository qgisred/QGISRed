# -*- coding: utf-8 -*-
import pytest

from qgis.PyQt.QtCore import QPointF, QRectF, Qt

from QGISRed.ui.analysis.timeseries_legend_interaction import LegendInteractionController


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


class TestLegendDelete:
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

