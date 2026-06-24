# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFontMetrics

from ..analysis.timeseries_plot_style import qfont

_MIN_PLOT_HEIGHT_PX = 48
_MIN_PLOT_HEIGHT_RATIO = 0.38
ROTATED_LABEL_SIN = 0.7071067811865476

TITLE_FONT_SIZE = 11
SUBTITLE_FONT_SIZE = 9
TITLE_TOP_PADDING = 4
TITLE_BOTTOM_PADDING = 6


def wrap_title_lines(title, max_width, max_lines=2):
    """Word-wrap a chart title into at most max_lines, eliding the final line."""
    text = (title or "").strip()
    if not text:
        return []
    fontMetrics = QFontMetrics(qfont(TITLE_FONT_SIZE, bold=True))
    maxWidth = max(0, int(max_width))
    if fontMetrics.horizontalAdvance(text) <= maxWidth:
        return [text]
    words = text.split()
    lines = []
    current = ""
    index = 0
    while index < len(words) and len(lines) < max_lines - 1:
        candidate = words[index] if not current else current + " " + words[index]
        if not current or fontMetrics.horizontalAdvance(candidate) <= maxWidth:
            current = candidate
            index += 1
        else:
            lines.append(current)
            current = ""
    tail = " ".join(words[index:])
    lastLine = tail if not current else (current + " " + tail if tail else current)
    lines.append(fontMetrics.elidedText(lastLine, Qt.TextElideMode.ElideRight, maxWidth))
    return lines


def title_top_margin(title, subtitle, width, *, min_margin=40, max_lines=2):
    """Top margin needed above the plot for a wrapped title plus subtitle."""
    top = TITLE_TOP_PADDING
    if title:
        lineCount = len(wrap_title_lines(title, max(0, int(width) - 8), max_lines))
        top += lineCount * QFontMetrics(qfont(TITLE_FONT_SIZE, bold=True)).height()
    if subtitle:
        top += QFontMetrics(qfont(SUBTITLE_FONT_SIZE)).height()
    return max(min_margin, top + TITLE_BOTTOM_PADDING)


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
    return max(7, min(11, int(tick_font_size) + 1))


def cumulative_right_axis_margin(
    tick_font_size,
    tick_labels,
    title_text="",
    *,
    tick_offset=6,
    title_gap=6,
    edge_pad=8,
    min_margin=36,
    max_margin=96,
):
    """Reserve width for right-axis tick numbers plus optional rotated title."""
    fontMetrics = QFontMetrics(qfont(tick_font_size))
    tickWidth = max((fontMetrics.horizontalAdvance(label) for label in tick_labels), default=0)
    if title_text:
        titleFont = qfont(adaptive_axis_title_font_size(tick_font_size), bold=True)
        titleStrip = QFontMetrics(titleFont).height()
        margin = tick_offset + tickWidth + title_gap + titleStrip + edge_pad
    else:
        margin = tick_offset + tickWidth + edge_pad
    return max(min_margin, min(max_margin, margin))


def longest_x_label_width(bins, tick_font_size):
    if not bins:
        return 0
    fontMetrics = QFontMetrics(qfont(tick_font_size))
    return max(fontMetrics.horizontalAdvance(binData.get("label", "")) for binData in bins)


def x_tick_labels_need_rotation(bins, plot_width, tick_font_size, tick_char_width=6.0):
    if not bins or plot_width <= 0:
        return False
    availablePerBar = plot_width / max(1, len(bins))
    longestPx = longest_x_label_width(bins, tick_font_size)
    if longestPx > 0:
        return longestPx > availablePerBar * 0.92
    longestChars = max((len(binData.get("label", "")) for binData in bins), default=0)
    return longestChars * tick_char_width > availablePerBar


def rotated_x_label_extra_height(tick_font_size, max_label_width, has_x_label=False):
    fontMetrics = QFontMetrics(qfont(tick_font_size))
    labelWidth = max(0.0, float(max_label_width))
    rotatedHeight = labelWidth * ROTATED_LABEL_SIN + fontMetrics.descent() + 4
    if has_x_label:
        rotatedHeight += fontMetrics.height() + 6
    return rotatedHeight


def cap_bottom_margin(widget_height, margin_top, base_bottom, rotated_extra, *, min_plot_px=_MIN_PLOT_HEIGHT_PX, min_plot_ratio=_MIN_PLOT_HEIGHT_RATIO):
    widget_height = max(int(widget_height), 1)
    margin_top = max(int(margin_top), 0)
    base_bottom = max(int(base_bottom), 0)
    rotated_extra = max(float(rotated_extra), 0.0)
    minPlot = max(min_plot_px, int(widget_height * min_plot_ratio))
    maxBottom = max(base_bottom, widget_height - margin_top - minPlot)
    return min(base_bottom + int(round(rotated_extra)), maxBottom)


def max_rotated_label_width_for_space(space_below, tick_font_size, has_x_label=False):
    fontMetrics = QFontMetrics(qfont(tick_font_size))
    usable = float(space_below) - fontMetrics.descent() - 4
    if has_x_label:
        usable -= fontMetrics.height() + 6
    if usable <= 0:
        return 20.0
    return max(20.0, usable / ROTATED_LABEL_SIN)
