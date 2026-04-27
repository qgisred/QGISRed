# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QFontMetrics

from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    estimate_max_ticks,
    format_number_tick,
)

from .timeseries_plot_style import AXIS_MAX_TICKS, PLOT_TOP_PAD, qfont


class PlotLayoutCalculator:
    _AXIS_TICK_FONT_SIZE = 10
    @staticmethod
    def _y_tick_labels_for_width(
        all_y: Sequence[float],
        y_cat: Optional[Sequence[str]],
        fm: QFontMetrics,
        plot_h: float,
    ) -> List[str]:
        if y_cat:
            return [y_cat[i] for i in range(len(y_cat))]
        if not all_y:
            return []
        min_y, max_y = min(all_y), max(all_y)
        max_ticks_y = estimate_max_ticks(plot_h, fm.height() + 6, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
        scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return [format_number_tick(v, scale.step) for v in scale.ticks()]

    @classmethod
    def _compute_left_margin(
        cls,
        *,
        base_margin_left: float,
        all_y_left: Sequence[float],
        y_cat_left: Optional[Sequence[str]],
        fm: QFontMetrics,
        plot_h: float,
    ) -> float:
        tick_labels = cls._y_tick_labels_for_width(all_y_left, y_cat_left, fm, plot_h)
        if not tick_labels:
            return float(base_margin_left)
        max_label_w = 0
        for label_text in tick_labels:
            max_label_w = max(max_label_w, fm.horizontalAdvance(label_text))
        return max(float(base_margin_left), float(max_label_w + 40))

    @classmethod
    def _compute_right_axis_label_width(
        cls,
        *,
        all_y_right: Sequence[float],
        y_cat_right: Optional[Sequence[str]],
        fm: QFontMetrics,
        plot_h: float,
    ) -> float:
        tick_labels = cls._y_tick_labels_for_width(all_y_right, y_cat_right, fm, plot_h)
        if not tick_labels:
            return 0.0
        max_label_w = 0
        for label_text in tick_labels:
            max_label_w = max(max_label_w, fm.horizontalAdvance(label_text))
        return max(0.0, float(max_label_w + 18))

    @classmethod
    def compute_plot_rect(cls, widget) -> Tuple[QRectF, float, float]:
        w = widget.width()
        h = widget.height()

        fm = QFontMetrics(qfont(cls._AXIS_TICK_FONT_SIZE))

        left_series, right_series = widget._seriesByAxis()
        _x_l, all_y_left, y_cat_left, _st_left = widget._axisSeriesData(left_series)
        _x_r, all_y_right, y_cat_right, _st_right = widget._axisSeriesData(right_series)

        legend_w = widget._legendRequiredWidth()
        widget._legend_reserved_w = legend_w

        plot_h_est = h - (widget.margin_top + PLOT_TOP_PAD) - widget.margin_bottom
        local_margin_left = cls._compute_left_margin(
            base_margin_left=float(widget.margin_left),
            all_y_left=all_y_left,
            y_cat_left=y_cat_left,
            fm=fm,
            plot_h=plot_h_est,
        )
        right_axis_label_w = cls._compute_right_axis_label_width(
            all_y_right=all_y_right,
            y_cat_right=y_cat_right,
            fm=fm,
            plot_h=plot_h_est,
        )

        local_margin_bottom = widget.margin_bottom
        if widget.data_x and len(widget.data_x) > 1:
            has_days = max(widget.data_x) >= 24
            tick_block_h = fm.height() * 2 + 16 if has_days else fm.height() + 20
            # Space for axis title + gap + bottom padding (keeps it off the dock edge)
            axis_title_h = (fm.height() + 2 + 2 + 6) if (getattr(widget, "x_label", "") or "").strip() else 0
            extra = tick_block_h + axis_title_h
            local_margin_bottom = max(local_margin_bottom, extra)

        widget._right_axis_label_w = right_axis_label_w
        local_margin_right = widget.margin_right + right_axis_label_w + (widget._legend_reserved_w + 10 if widget._legend_reserved_w else 0)

        plot_rect = QRectF(
            local_margin_left,
            widget.margin_top + PLOT_TOP_PAD,
            w - local_margin_left - local_margin_right,
            h - (widget.margin_top + PLOT_TOP_PAD) - local_margin_bottom,
        )
        return plot_rect, local_margin_left, right_axis_label_w

