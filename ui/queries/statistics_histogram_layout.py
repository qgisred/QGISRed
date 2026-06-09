# -*- coding: utf-8 -*-
from qgis.PyQt.QtGui import QFontMetrics

from ..analysis.timeseries_plot_style import qfont

_MIN_PLOT_HEIGHT_PX = 48
_MIN_PLOT_HEIGHT_RATIO = 0.38
ROTATED_LABEL_SIN = 0.7071067811865476


def adaptive_axis_tick_font_size(width, height):
    """Scale axis tick labels down in narrow or short panels."""
    ref = min(max(int(width), 1), max(int(height), 1))
    if ref < 170:
        return 6
    if ref < 220:
        return 7
    if ref < 300:
        return 8
    return 9


def adaptive_axis_title_font_size(tick_font_size):
    return max(7, min(10, int(tick_font_size) + 1))


def cumulative_right_axis_margin(
    tick_font_size,
    tick_labels,
    title_text="",
    *,
    tick_offset=6,
    title_gap=10,
    edge_pad=8,
    min_margin=36,
    max_margin=96,
):
    """Reserve width for right-axis tick numbers plus optional rotated title."""
    font_metrics = QFontMetrics(qfont(tick_font_size))
    tick_width = max((font_metrics.horizontalAdvance(label) for label in tick_labels), default=0)
    if title_text:
        title_font = qfont(adaptive_axis_title_font_size(tick_font_size), bold=True)
        title_width = QFontMetrics(title_font).horizontalAdvance(title_text)
        margin = tick_offset + tick_width + title_gap + title_width + edge_pad
    else:
        margin = tick_offset + tick_width + edge_pad
    return max(min_margin, min(max_margin, margin))


def longest_x_label_width(bins, tick_font_size):
    if not bins:
        return 0
    font_metrics = QFontMetrics(qfont(tick_font_size))
    return max(font_metrics.horizontalAdvance(bin_data.get("label", "")) for bin_data in bins)


def x_tick_labels_need_rotation(bins, plot_width, tick_font_size, tick_char_width=6.0):
    if not bins or plot_width <= 0:
        return False
    available_per_bar = plot_width / max(1, len(bins))
    longest_px = longest_x_label_width(bins, tick_font_size)
    if longest_px > 0:
        return longest_px > available_per_bar * 0.92
    longest_chars = max((len(bin_data.get("label", "")) for bin_data in bins), default=0)
    return longest_chars * tick_char_width > available_per_bar


def rotated_x_label_extra_height(tick_font_size, max_label_width, has_x_label=False):
    font_metrics = QFontMetrics(qfont(tick_font_size))
    label_width = max(0.0, float(max_label_width))
    rotated_height = label_width * ROTATED_LABEL_SIN + font_metrics.descent() + 4
    if has_x_label:
        rotated_height += font_metrics.height() + 6
    return rotated_height


def cap_bottom_margin(widget_height, margin_top, base_bottom, rotated_extra, *, min_plot_px=_MIN_PLOT_HEIGHT_PX, min_plot_ratio=_MIN_PLOT_HEIGHT_RATIO):
    widget_height = max(int(widget_height), 1)
    margin_top = max(int(margin_top), 0)
    base_bottom = max(int(base_bottom), 0)
    rotated_extra = max(float(rotated_extra), 0.0)
    min_plot = max(min_plot_px, int(widget_height * min_plot_ratio))
    max_bottom = max(base_bottom, widget_height - margin_top - min_plot)
    return min(base_bottom + int(round(rotated_extra)), max_bottom)


def max_rotated_label_width(plot_width, bin_count, tick_font_size, slot_scale=1.15):
    if bin_count <= 0 or plot_width <= 0:
        return 60.0
    slot_width = plot_width / bin_count
    font_height = QFontMetrics(qfont(tick_font_size)).height()
    return max(24.0, min(72.0, slot_width * slot_scale + font_height))
