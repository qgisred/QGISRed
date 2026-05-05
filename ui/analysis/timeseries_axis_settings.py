# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import List, Optional, Sequence

from qgis.PyQt.QtGui import QColor

from ...tools.utils.qgisred_axis_scale_utils import (
    NiceScale,
    compute_nice_scale,
    estimate_max_ticks,
    format_number_tick,
)

from .timeseries_plot_style import AXIS_MAX_TICKS, BORDER_COLOR, FONT_FAMILY, PLOT_BG_COLOR


@dataclass
class TimeSeriesAxisSettings:
    title: str = ""
    auto_scale: bool = True
    fixed_min: float = 0.0
    fixed_max: float = 1.0
    fixed_divisions: int = 5
    show_grid: bool = True
    tick_font_size: int = 10
    tick_font_family: str = ""
    tick_color_hex: str = "#000000"
    decimal_places: int = -1

    x_hour_format: str = "hm"
    x_day_format: str = "split_days"

    def resolved_font_family(self) -> str:
        f = (self.tick_font_family or "").strip()
        return f or FONT_FAMILY

    def tick_qcolor(self) -> QColor:
        c = QColor(self.tick_color_hex)
        if not c.isValid():
            c = QColor("#000000")
        return c

    def decimal_places_or_none(self) -> Optional[int]:
        if self.decimal_places is None or self.decimal_places < 0:
            return None
        return int(self.decimal_places)


def default_axis_settings() -> TimeSeriesAxisSettings:
    return TimeSeriesAxisSettings()


def clone_axis_settings(s: TimeSeriesAxisSettings) -> TimeSeriesAxisSettings:
    return copy.copy(s)


@dataclass
class TimeSeriesGeneralSettings:
    title: str = ""
    widget_bg_hex: str = "#ffffff"
    plot_bg_hex: str = ""
    frame_color_hex: str = ""
    frame_width: int = 1
    legend_position: str = "right"
    legend_show_frame: bool = False
    legend_show_background: bool = False
    legend_symbol_size: int = 12
    legend_columns: int = 1

    def widget_bg_qcolor(self) -> QColor:
        c = QColor(self.widget_bg_hex)
        return c if c.isValid() else QColor("#ffffff")

    def plot_bg_qcolor(self) -> QColor:
        raw = (self.plot_bg_hex or "").strip()
        if not raw:
            return QColor(PLOT_BG_COLOR)
        c = QColor(raw)
        return c if c.isValid() else QColor(PLOT_BG_COLOR)

    def frame_qcolor(self) -> QColor:
        raw = (self.frame_color_hex or "").strip()
        if not raw:
            return QColor(BORDER_COLOR)
        c = QColor(raw)
        return c if c.isValid() else QColor(BORDER_COLOR)


def default_general_settings() -> TimeSeriesGeneralSettings:
    return TimeSeriesGeneralSettings()


def clone_general_settings(s: TimeSeriesGeneralSettings) -> TimeSeriesGeneralSettings:
    return copy.copy(s)


def _clamp_divisions(n: int) -> int:
    if n < 1:
        return 1
    return min(n, AXIS_MAX_TICKS)


def build_fixed_linear_scale(axis_min: float, axis_max: float, divisions: int) -> NiceScale:
    divisions = _clamp_divisions(int(divisions))
    if axis_max <= axis_min:
        axis_max = axis_min + 1.0
    step = (axis_max - axis_min) / float(divisions)
    if step == 0:
        step = 1.0
    return NiceScale(axis_min=axis_min, axis_max=axis_max, step=step, divisions=divisions)


def _format_tick_number(value: float, step: float, dec: Optional[int]) -> str:
    if dec is None:
        return format_number_tick(value, step)
    try:
        return format_number_tick(value, step, decimal_places=dec)
    except TypeError:
        return format_number_tick(value, step)


def preview_y_tick_labels(
    all_y: Sequence[float],
    y_cat: Optional[Sequence[str]],
    cfg: TimeSeriesAxisSettings,
    plot_h: float,
    fm_height: float,
) -> List[str]:
    dec = cfg.decimal_places_or_none()
    if y_cat:
        return [str(y_cat[i]) for i in range(len(y_cat))]
    if not all_y:
        return []
    min_y, max_y = min(all_y), max(all_y)
    if not cfg.auto_scale:
        lo, hi = float(cfg.fixed_min), float(cfg.fixed_max)
        if hi <= lo:
            hi = lo + 1.0
        scale = build_fixed_linear_scale(lo, hi, cfg.fixed_divisions)
    else:
        max_ticks_y = estimate_max_ticks(plot_h, fm_height + 6, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
        scale = compute_nice_scale(min_y, max_y, max_ticks_y)
    return [_format_tick_number(v, scale.step, dec) for v in scale.ticks()]
