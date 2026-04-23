# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt.QtCore import QPointF, Qt


class LegendInteractionController:
    def __init__(self, widget):
        self._w = widget
        self._drag_candidate_idx = None
        self._drag_active = False
        self._drag_start_pos = None
        self._drop_target_idx = None
        self._pressed_modifiers = None
        self._moved = False

    def reset(self) -> None:
        self._drag_candidate_idx = None
        self._drag_start_pos = None
        self._drag_active = False
        self._drop_target_idx = None
        self._pressed_modifiers = None
        self._moved = False

    def begin(self, pos: QPointF, modifiers) -> None:
        clicked_idx = None
        for rect, series_idx in self._w._legend_hitboxes:
            if rect.contains(pos):
                clicked_idx = series_idx
                break
        if clicked_idx is None:
            return

        self._drag_candidate_idx = clicked_idx
        self._drag_start_pos = QPointF(pos)
        self._drag_active = False
        self._drop_target_idx = clicked_idx
        self._pressed_modifiers = modifiers
        self._moved = False

    def update_drag(self, pos: QPointF) -> bool:
        if self._drag_candidate_idx is None or self._drag_start_pos is None:
            return False

        dx = abs(pos.x() - self._drag_start_pos.x())
        dy = abs(pos.y() - self._drag_start_pos.y())
        if (dx + dy) > 1:
            self._moved = True
        if not self._drag_active and (dx + dy) > 5:
            self._drag_active = True

        if not self._drag_active:
            return False

        target = self._drop_target_idx
        best_dist = None
        for rect, series_idx in self._w._legend_hitboxes:
            cy = rect.center().y()
            d = abs(pos.y() - cy)
            if best_dist is None or d < best_dist:
                best_dist = d
                target = series_idx
        if target != self._drop_target_idx:
            self._drop_target_idx = target
            self._w.update()
        return True

    @property
    def drag_active(self) -> bool:
        return bool(self._drag_active)

    @property
    def moved(self) -> bool:
        return bool(self._moved)

    @property
    def drop_target_idx(self):
        return self._drop_target_idx

    @property
    def drag_candidate_idx(self):
        return self._drag_candidate_idx

    def apply_reorder_if_needed(self) -> bool:
        if self._drag_candidate_idx is None or self._drop_target_idx is None:
            return False
        from_idx = int(self._drag_candidate_idx)
        to_idx = int(self._drop_target_idx)
        if not (0 <= from_idx < len(self._w.series) and 0 <= to_idx < len(self._w.series)) or from_idx == to_idx:
            return False

        item = self._w.series.pop(from_idx)
        insert_at = to_idx - 1 if from_idx < to_idx else to_idx
        insert_at = max(0, min(insert_at, len(self._w.series)))
        self._w.series.insert(insert_at, item)
        order = [str(s.get("series_key") or "") for s in self._w.series]
        self._w.seriesOrderChanged.emit(order)
        return True

    def apply_toggle_if_click(self) -> bool:
        if self._drag_candidate_idx is None or self._moved:
            return False
        clicked_idx = int(self._drag_candidate_idx)
        if not (0 <= clicked_idx < len(self._w.series)):
            return False

        modifiers = self._pressed_modifiers or Qt.KeyboardModifier.NoModifier
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if is_shift:
            for i, s in enumerate(self._w.series):
                s["highlighted"] = (i == clicked_idx)
                s["muted"] = (i != clicked_idx)
            return True

        if is_ctrl:
            s = self._w.series[clicked_idx]
            s["highlighted"] = not bool(s.get("highlighted", False))
            if s["highlighted"]:
                s["muted"] = False
            return True

        s = self._w.series[clicked_idx]
        s["muted"] = not bool(s.get("muted", False))
        if s["muted"]:
            s["highlighted"] = False
        return True

