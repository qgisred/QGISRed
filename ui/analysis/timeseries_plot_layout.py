# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QFont, QFontMetrics

from .timeseries_axis_settings import preview_y_tick_labels
from .timeseries_plot_style import FONT_FAMILY, PLOT_TOP_PAD


class PlotLayoutCalculator:
    @staticmethod
    def _effective_x_title(widget) -> str:
        cfg = getattr(widget, "_axis_cfg_x", None)
        if cfg and (cfg.title or "").strip():
            return (cfg.title or "").strip()
        return (getattr(widget, "x_label", "") or "").strip()

    @classmethod
    def _compute_left_margin(
        cls,
        *,
        base_margin_left: float,
        all_y_left: Sequence[float],
        y_cat_left: Optional[Sequence[str]],
        fm: QFontMetrics,
        plot_h: float,
        widget,
    ) -> float:
        cfg = getattr(widget, "_axis_cfg_y_left", None)
        if cfg is None:
            return float(base_margin_left)
        tick_labels = preview_y_tick_labels(all_y_left, y_cat_left, cfg, plot_h, float(fm.height()))
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
        widget,
    ) -> float:
        cfg = getattr(widget, "_axis_cfg_y_right", None)
        if cfg is None:
            return 0.0
        tick_labels = preview_y_tick_labels(all_y_right, y_cat_right, cfg, plot_h, float(fm.height()))
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

        cfg_yl = getattr(widget, "_axis_cfg_y_left", None)
        cfg_yr = getattr(widget, "_axis_cfg_y_right", None)
        cfg_x = getattr(widget, "_axis_cfg_x", None)
        sz_l = max(5, min(int(getattr(cfg_yl, "tick_font_size", 10) or 10), 48)) if cfg_yl else 10
        sz_r = max(5, min(int(getattr(cfg_yr, "tick_font_size", 10) or 10), 48)) if cfg_yr else 10
        sz_x = max(5, min(int(getattr(cfg_x, "tick_font_size", 10) or 10), 48)) if cfg_x else 10
        fam_l = cfg_yl.resolved_font_family() if cfg_yl else FONT_FAMILY
        fam_r = cfg_yr.resolved_font_family() if cfg_yr else FONT_FAMILY
        fam_x = cfg_x.resolved_font_family() if cfg_x else FONT_FAMILY
        fm_left = QFontMetrics(QFont(fam_l, sz_l))
        fm_right = QFontMetrics(QFont(fam_r, sz_r))
        fm_x = QFontMetrics(QFont(fam_x, sz_x))

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
            fm=fm_left,
            plot_h=plot_h_est,
            widget=widget,
        )
        right_axis_label_w = cls._compute_right_axis_label_width(
            all_y_right=all_y_right,
            y_cat_right=y_cat_right,
            fm=fm_right,
            plot_h=plot_h_est,
            widget=widget,
        )

        local_margin_bottom = widget.margin_bottom
        if widget.data_x and len(widget.data_x) > 1:
            if cfg_x and not cfg_x.auto_scale:
                eff_max = float(cfg_x.fixed_max)
            else:
                eff_max = max(widget.data_x)
            has_days = eff_max >= 24
            tick_block_h = fm_x.height() * 2 + 16 if has_days else fm_x.height() + 20
            axis_title_h = (fm_x.height() + 2 + 2 + 6) if cls._effective_x_title(widget) else 0
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

