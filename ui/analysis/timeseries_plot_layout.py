# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from qgis.PyQt.QtCore import QRectF
from qgis.PyQt.QtGui import QFont, QFontMetrics

from .timeseries_axis_settings import preview_y_tick_labels
from .timeseries_time_utils import civil_time_parts
from .timeseries_plot_style import FONT_FAMILY, LEGEND_OUTSIDE_BOTTOM_EXTRA, LEGEND_OUTSIDE_LEFT_EXTRA, LEGEND_OUTSIDE_TOP_EXTRA, PLOT_TOP_PAD


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
        if not (getattr(widget, "_y_magnitudes_left", []) or []):
            if not all_y_left and not y_cat_left:
                return float(base_margin_left)
        tick_labels = preview_y_tick_labels(all_y_left, y_cat_left, cfg, plot_h, float(fm.height()))
        if not tick_labels:
            return float(base_margin_left)
        max_label_w = 0
        for label_text in tick_labels:
            max_label_w = max(max_label_w, fm.horizontalAdvance(label_text))
        title_extra = 0.0
        title = (getattr(cfg, "title", "") or "").strip()
        if not title and (getattr(widget, "_y_magnitudes_left", []) or []):
            title = (getattr(widget, "_y_label_left", "") or "").strip()
        if title:
            title_size = max(5, min(int(getattr(cfg, "title_font_size", 10) or 10), 48))
            title_fm = QFontMetrics(QFont(cfg.resolved_title_font_family(), title_size))
            title_extra = float(title_fm.height() + 8)
        return max(float(base_margin_left), float(max_label_w + 40 + title_extra))

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
        title_extra = 0.0
        title = (getattr(cfg, "title", "") or getattr(widget, "_y_label_right", "") or "").strip()
        if title:
            title_size = max(5, min(int(getattr(cfg, "title_font_size", 10) or 10), 48))
            title_fm = QFontMetrics(QFont(cfg.resolved_title_font_family(), title_size))
            title_extra = float(title_fm.height() + 8)
        return max(0.0, float(max_label_w + 18 + title_extra))

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
        sz_title_x = max(5, min(int(getattr(cfg_x, "title_font_size", 10) or 10), 48)) if cfg_x else 10
        fam_l = cfg_yl.resolved_font_family() if cfg_yl else FONT_FAMILY
        fam_r = cfg_yr.resolved_font_family() if cfg_yr else FONT_FAMILY
        fam_x = cfg_x.resolved_font_family() if cfg_x else FONT_FAMILY
        fam_title_x = cfg_x.resolved_title_font_family() if cfg_x else FONT_FAMILY
        fm_left = QFontMetrics(QFont(fam_l, sz_l))
        fm_right = QFontMetrics(QFont(fam_r, sz_r))
        fm_x = QFontMetrics(QFont(fam_x, sz_x))
        fm_title_x = QFontMetrics(QFont(fam_title_x, sz_title_x))

        left_series, right_series = widget._seriesByAxis()
        _x_l, all_y_left, y_cat_left, _st_left = widget._axisSeriesData(left_series)
        _x_r, all_y_right, y_cat_right, _st_right = widget._axisSeriesData(right_series)

        gen = getattr(widget, "_general_cfg", None)
        legend_pos = (getattr(gen, "legend_position", "") or "right").strip() if gen is not None else "right"
        legend_w = widget._legendRequiredWidth()
        legend_h = widget._legendRequiredHeight()
        widget._legend_reserved_w = int(legend_w) if legend_pos in ("right", "left") else 0
        widget._legend_reserved_h = int(legend_h) if legend_pos in ("top", "bottom") else 0

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
            hour_format = (getattr(cfg_x, "x_hour_format", "") or "hm").strip() if cfg_x is not None else "hm"
            day_format = (getattr(cfg_x, "x_day_format", "") or "split_days").strip() if cfg_x is not None else "split_days"
            if hour_format in ("hm", "hm_ampm", "tod_hm", "tod_ampm"):
                start_clock_seconds = int(getattr(widget, "_start_clock_seconds", 0) or 0)
                min_parts = civil_time_parts(min(widget.data_x), start_clock_seconds)
                max_parts = civil_time_parts(eff_max, start_clock_seconds)
                has_days = bool(day_format == "split_days" and min_parts is not None and max_parts is not None and max_parts[0] > min_parts[0])
            else:
                has_days = eff_max >= 24 and day_format == "split_days"
            tick_block_h = fm_x.height() * 2 + 16 if has_days else fm_x.height() + 20
            axis_title_h = (fm_title_x.height() + 2 + 2 + 6) if cls._effective_x_title(widget) else 0
            extra = tick_block_h + axis_title_h
            local_margin_bottom = max(local_margin_bottom, extra)

        if legend_pos == "bottom" and getattr(widget, "_legend_reserved_h", 0):
            local_margin_bottom += float(widget._legend_reserved_h + LEGEND_OUTSIDE_BOTTOM_EXTRA)

        if legend_pos == "left" and widget._legend_reserved_w:
            local_margin_left += float(widget._legend_reserved_w + 10 + LEGEND_OUTSIDE_LEFT_EXTRA)

        title_txt = (getattr(gen, "title", "") or getattr(widget, "title", "") or "").strip() if gen is not None else (getattr(widget, "title", "") or "").strip()
        title_margin_top = float(widget.margin_top)
        if title_txt:
            title_size = max(5, min(int(getattr(gen, "title_font_size", 10) or 10), 48)) if gen is not None else 10
            title_family = gen.resolved_title_font_family() if gen is not None else FONT_FAMILY
            title_fm = QFontMetrics(QFont(title_family, title_size))
            title_margin_top = max(title_margin_top, float(title_fm.height() + 12))
        local_margin_top = title_margin_top + PLOT_TOP_PAD
        if legend_pos == "top" and getattr(widget, "_legend_reserved_h", 0):
            local_margin_top += float(widget._legend_reserved_h + LEGEND_OUTSIDE_TOP_EXTRA)

        widget._right_axis_label_w = right_axis_label_w
        local_margin_right = widget.margin_right + right_axis_label_w
        if legend_pos == "right" and widget._legend_reserved_w:
            local_margin_right += float(widget._legend_reserved_w + 10)

        plot_rect = QRectF(
            local_margin_left,
            local_margin_top,
            w - local_margin_left - local_margin_right,
            h - local_margin_top - local_margin_bottom,
        )
        return plot_rect, local_margin_left, right_axis_label_w
