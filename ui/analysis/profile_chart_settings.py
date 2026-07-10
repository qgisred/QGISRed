# -*- coding: utf-8 -*-
import copy
from dataclasses import dataclass, field


@dataclass
class ProfileAxisSettings:
    title: str = ""
    auto_scale: bool = True
    fixed_min: float = 0.0
    fixed_max: float = 100.0
    show_grid: bool = True


@dataclass
class ProfileGeneralSettings:
    show_legend: bool = True
    plot_bg_hex: str = "#fafcff"
    legend_position: str = "center"
    legend_font_size: int = 8
    legend_symbol_size: int = 18
    legend_show_frame: bool = False
    legend_bg_hex: str = ""


LEGEND_POSITIONS = ("left", "center", "right")


@dataclass
class ProfileCurveStyle:
    color_hex: str = ""
    width: float = 2.0
    line_style: str = "solid"
    show_markers: bool = True
    marker_size: float = 2.5


LINE_STYLES = ("solid", "dashed", "dotted")


def clone_axis(settings):
    return copy.copy(settings)


def clone_general(settings):
    return copy.copy(settings)


def clone_curve_overrides(overrides):
    return {label: copy.copy(style) for label, style in (overrides or {}).items()}
