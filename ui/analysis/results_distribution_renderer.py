# -*- coding: utf-8 -*-
import math

from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFontMetrics, QPainterPath, QPen

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    NiceScale,
    compute_nice_scale,
    estimate_max_ticks,
    format_number_tick,
)
from ..queries.statistics_histogram_renderer import (
    StatisticsHistogramRenderer,
    TOOLTIP_BG_COLOR,
)
from .timeseries_plot_style import BORDER_COLOR, GRID_COLOR, PLOT_BG_COLOR, TEXT_AXIS, TEXT_DARK, TOOLTIP_BORDER, qfont

CUMULATIVE_CURVE_COLOR = QColor(200, 60, 60)

_TICK_LEN = 4
_CURVE_HIT_TOLERANCE = 10.0


def format_distribution_hover_value(value, as_percent=False):
    """Format a histogram hover value as count or percentage text."""
    if as_percent:
        return "{} %".format(format_number_tick(value, 0.1))
    rounded = round(value)
    if abs(value - rounded) < 1e-9:
        return str(int(rounded))
    return format_number_tick(value, max(abs(value) / 100.0, 0.01))


def _distance_point_to_segment(px, py, ax, ay, bx, by):
    dx = bx - ax
    dy = by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay), 0.0
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    closest_x = ax + t * dx
    closest_y = ay + t * dy
    return math.hypot(px - closest_x, py - closest_y), t


def hit_test_cumulative_polyline(cursor_x, cursor_y, points, tolerance=_CURVE_HIT_TOLERANCE):
    """Return interpolated (x, count, screen_x, screen_y) if cursor is near the polyline."""
    if len(points) < 2:
        return None

    best = None
    best_distance = float(tolerance)
    for index in range(len(points) - 1):
        start = points[index]
        end = points[index + 1]
        distance, t = _distance_point_to_segment(
            cursor_x,
            cursor_y,
            start["screen_x"],
            start["screen_y"],
            end["screen_x"],
            end["screen_y"],
        )
        if distance < best_distance:
            best_distance = distance
            best = {
                "x": start["x"] + t * (end["x"] - start["x"]),
                "count": start["count"] + t * (end["count"] - start["count"]),
                "screen_x": start["screen_x"] + t * (end["screen_x"] - start["screen_x"]),
                "screen_y": start["screen_y"] + t * (end["screen_y"] - start["screen_y"]),
            }
    return best


class ResultsDistributionRenderer(StatisticsHistogramRenderer):
    """Histogram renderer for simulation results: class bars + optional cumulative curve."""

    _TITLE_FONT_SIZE = 10

    def render(self, widget, painter):
        painter.setRenderHint(PAINTER_ANTIALIASING)
        outer_fill = getattr(widget, "outer_fill_color", None)
        if outer_fill is not None:
            painter.fillRect(widget.rect(), outer_fill)
        else:
            painter.fillRect(widget.rect(), Qt.GlobalColor.white)

        if not widget.bins:
            self._drawNoData(widget, painter)
            return

        plotRect = widget.getPlotRect()
        if plotRect.width() <= 10 or plotRect.height() <= 10:
            return

        painter.fillRect(plotRect, PLOT_BG_COLOR)
        painter.setPen(QPen(BORDER_COLOR, 1))
        painter.drawRect(plotRect)

        # Optional title/subtitle (used when only one chart is shown).
        if getattr(widget, "show_title", False):
            self._drawTitle(widget, painter)
        if getattr(widget, "show_subtitle", False):
            self._drawSubtitle(widget, painter, plotRect)

        left_scale = self._computeLeftScale(widget, plotRect)
        cumulative_mode = getattr(widget, "cumulative_mode", None)
        cumulative_points = getattr(widget, "cumulative_points", [])
        cumulative_bars = self._hasCumulativeBars(widget)
        right_scale = (
            self._computeCumulativeScale(widget, plotRect)
            if cumulative_mode in ("absolute", "relative") and cumulative_points
            else None
        )

        self._drawGridAndLeftAxis(widget, painter, plotRect, left_scale)
        if right_scale is not None:
            self._drawDistributionRightAxis(widget, painter, plotRect, right_scale)
            self._drawDistributionTopAxis(widget, painter, plotRect)

        widget._cumulativeBarRects = []
        if cumulative_bars:
            self._drawCumulativeBars(widget, painter, plotRect, left_scale)

        bar_rects = self._drawBars(widget, painter, plotRect, left_scale)
        widget._barRects = bar_rects

        self._drawXAxisLabels(widget, painter, plotRect, bar_rects)

        if cumulative_mode in ("absolute", "relative") and right_scale is not None:
            self._drawCumulativeFrequencyCurve(widget, painter, plotRect, right_scale)

        hover_segment = getattr(widget, "hoverSegment", None)
        if hover_segment == "curve":
            curve_sample = getattr(widget, "hoverCurveSample", None)
            if curve_sample:
                self._drawCurveHoverMarker(painter, curve_sample)
                self._drawCurveHoverTooltip(widget, painter, plotRect, curve_sample)
        else:
            hover_index = getattr(widget, "hoverIndex", None)
            if hover_index is not None and 0 <= hover_index < len(bar_rects):
                self._drawHoverTooltip(widget, painter, plotRect, bar_rects)

    def _bar_mode(self, widget):
        return getattr(widget, "bar_mode", "plain")

    def _bin_bar_value(self, widget, binData):
        bar_mode = self._bar_mode(widget)
        if bar_mode == "relative":
            total_count = getattr(widget, "_totalCount", 0) or sum(
                item.get("count", 0) for item in widget.bins
            )
            if total_count <= 0:
                return 0.0
            return (binData.get("count", 0) / float(total_count)) * 100.0
        return binData.get("count", 0)

    def _bin_cumulative_bar_value(self, widget, binData):
        cumulative_count = binData.get("cumulative_count")
        if cumulative_count is None:
            return None
        if self._bar_mode(widget) == "relative":
            total_count = getattr(widget, "_totalCount", 0) or sum(
                item.get("count", 0) for item in widget.bins
            )
            if total_count <= 0:
                return 0.0
            return (cumulative_count / float(total_count)) * 100.0
        return cumulative_count

    def _hasCumulativeBars(self, widget):
        cumulative_mode = getattr(widget, "cumulative_mode", None)
        if cumulative_mode not in ("absolute", "relative"):
            return False
        if getattr(widget, "cumulative_points", []):
            return False
        return any(bin_data.get("cumulative_count") is not None for bin_data in widget.bins)

    def _computeLeftScale(self, widget, plotRect):
        values = [self._bin_bar_value(widget, bin_data) for bin_data in widget.bins]
        if self._hasCumulativeBars(widget):
            for bin_data in widget.bins:
                value = self._bin_cumulative_bar_value(widget, bin_data)
                if value is not None:
                    values.append(value)
        if not values:
            values = [0.0, 1.0]
        data_min = min(values + [0.0])
        data_max = max(values + [0.0])
        if data_max == data_min:
            data_max = data_min + 1.0
        label_height = QFontMetrics(qfont(self._tickFontSize(widget))).height() + 4
        max_ticks = estimate_max_ticks(plotRect.height(), label_height, max_ticks=10)
        return compute_nice_scale(data_min, data_max, max_ticks, include_zero=True)

    def _computeCumulativeScale(self, widget, plotRect):
        cumulative_mode = getattr(widget, "cumulative_mode", None)
        points = getattr(widget, "cumulative_points", [])
        total_count = points[-1].get("count", 0) if points else 0
        if total_count <= 0:
            total_count = getattr(widget, "_totalCount", 0) or sum(
                item.get("count", 0) for item in widget.bins
            )
        if cumulative_mode == "relative":
            # Fixed % scale: never exceed 100.
            # Use 4 intervals of 25% for stable, readable ticks.
            return NiceScale(axis_min=0.0, axis_max=100.0, step=25.0, divisions=4)
        else:
            data_max = max(float(total_count), 1.0)
        label_height = QFontMetrics(qfont(self._tickFontSize(widget))).height() + 4
        max_ticks = estimate_max_ticks(plotRect.height(), label_height, max_ticks=8)
        return compute_nice_scale(0.0, data_max, max_ticks, include_zero=True)

    def _drawGridAndLeftAxis(self, widget, painter, plotRect, scale):
        painter.setFont(qfont(self._tickFontSize(widget)))
        font_metrics = QFontMetrics(painter.font())
        # Slightly stronger grid than the time-series default.
        grid_color = QColor(GRID_COLOR).darker(115)
        for tick_value in scale.ticks():
            tick_y = self._yForValue(plotRect, scale, tick_value)
            painter.setPen(QPen(grid_color, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plotRect.left(), tick_y), QPointF(plotRect.right(), tick_y))

            # Small ticks on the left axis (no vertical gridlines).
            painter.setPen(QPen(TEXT_AXIS, 1))
            painter.drawLine(
                QPointF(plotRect.left(), tick_y),
                QPointF(plotRect.left() - _TICK_LEN, tick_y),
            )

            label = format_number_tick(tick_value, scale.step)
            painter.setPen(TEXT_AXIS)
            label_x = plotRect.left() - 6 - font_metrics.horizontalAdvance(label)
            painter.drawText(QPointF(label_x, tick_y + font_metrics.ascent() / 2 - 1), label)
        if widget.yLabelLeft:
            painter.setPen(TEXT_AXIS)
            painter.setFont(qfont(self._titleFontSize(widget), bold=True))
            painter.save()
            painter.translate(12, plotRect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, widget.yLabelLeft)
            painter.restore()

    def _drawDistributionRightAxis(self, widget, painter, plotRect, scale):
        painter.setFont(qfont(self._tickFontSize(widget)))
        font_metrics = QFontMetrics(painter.font())
        for tick_value in scale.ticks():
            tick_y = self._yForValue(plotRect, scale, tick_value)
            label = format_number_tick(tick_value, scale.step)
            painter.setPen(TEXT_AXIS)
            # Small ticks on the right axis (no horizontal gridlines for this axis).
            painter.drawLine(
                QPointF(plotRect.right(), tick_y),
                QPointF(plotRect.right() + _TICK_LEN, tick_y),
            )
            painter.drawText(
                QPointF(plotRect.right() + 6, tick_y + font_metrics.ascent() / 2 - 1),
                label,
            )
        axis_title = getattr(widget, "yLabelRight", "") or ""
        if axis_title:
            painter.setPen(TEXT_AXIS)
            painter.setFont(qfont(self._titleFontSize(widget), bold=True))
            painter.save()
            painter.translate(widget.width() - 12, plotRect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, axis_title)
            painter.restore()

    def _drawCumulativeBars(self, widget, painter, plotRect, left_scale):
        bin_count = len(widget.bins)
        if bin_count == 0:
            widget._cumulativeBarRects = []
            return

        cumulative_rects = [None] * bin_count
        zoom = max(0.2, widget.zoomFactor)
        total_width = plotRect.width() * zoom
        slot_width = total_width / bin_count
        gap_width = max(2, slot_width * 0.15)
        bar_width = max(1.0, slot_width - gap_width)
        offset = widget.panOffset
        zero_y = self._yForValue(plotRect, left_scale, 0.0)

        for bin_index, bin_data in enumerate(widget.bins):
            cumulative_value = self._bin_cumulative_bar_value(widget, bin_data)
            if cumulative_value is None:
                continue

            bar_x = plotRect.left() + offset + bin_index * slot_width + gap_width / 2
            bar_top = self._yForValue(plotRect, left_scale, cumulative_value)
            top = min(bar_top, zero_y)
            height = abs(zero_y - bar_top)
            bar_rect = QRectF(bar_x, top, bar_width, height)
            cumulative_rects[bin_index] = bar_rect
            visible_rect = bar_rect.intersected(plotRect)
            if visible_rect.width() <= 0 or visible_rect.height() < 0:
                continue

            bar_color = bin_data.get("color")
            fill_color = QColor(bar_color) if bar_color is not None else QColor(CUMULATIVE_CURVE_COLOR)
            fill_color = fill_color.lighter(155)
            fill_color.setAlpha(135)
            if (
                getattr(widget, "hoverIndex", None) == bin_index
                and getattr(widget, "hoverSegment", None) == "cumulative"
            ):
                fill_color = fill_color.lighter(112)
                fill_color.setAlpha(175)
            painter.fillRect(visible_rect, fill_color)

        widget._cumulativeBarRects = cumulative_rects

    def _hasCumulativeCurve(self, widget):
        return (
            getattr(widget, "cumulative_mode", None) in ("absolute", "relative")
            and bool(getattr(widget, "cumulative_points", []))
        )

    def _cumulativeCurveGeometry(self, widget, plotRect):
        points_data = getattr(widget, "cumulative_points", [])
        scale_range = self._cumulativeXRange(widget)
        if not points_data or scale_range is None or plotRect.width() <= 0:
            return []

        x_min, x_max = scale_range
        total_count = points_data[-1].get("count", 0)
        if total_count <= 0:
            return []

        right_scale = self._computeCumulativeScale(widget, plotRect)
        cumulative_mode = getattr(widget, "cumulative_mode", "absolute")
        geometry = []
        for point_data in points_data:
            count = point_data.get("count", 0)
            x_value = point_data.get("x", x_min)
            y_value = (count / float(total_count)) * 100.0 if cumulative_mode == "relative" else count
            geometry.append({
                "x": float(x_value),
                "count": float(count),
                "screen_x": self._xForCumulativeValue(plotRect, x_min, x_max, x_value),
                "screen_y": self._yForValue(plotRect, right_scale, y_value),
            })
        return geometry

    def hitTestCumulativeCurve(self, widget, cursor_pos, plotRect, tolerance=_CURVE_HIT_TOLERANCE):
        if not self._hasCumulativeCurve(widget) or not plotRect.contains(cursor_pos):
            return None
        geometry = self._cumulativeCurveGeometry(widget, plotRect)
        return hit_test_cumulative_polyline(cursor_pos.x(), cursor_pos.y(), geometry, tolerance)

    def _curveHoverTooltipLines(self, widget, curve_sample):
        x_label = getattr(widget, "xLabel", "") or widget.tr("Value")
        cumulative_mode = getattr(widget, "cumulative_mode", "absolute")
        as_percent = cumulative_mode == "relative"
        x_text = format_number_tick(curve_sample["x"], max(abs(curve_sample["x"]) / 100.0, 0.01))
        total_count = getattr(widget, "_totalCount", 0) or sum(
            item.get("count", 0) for item in widget.bins
        )
        count_value = curve_sample["count"]
        if as_percent and total_count > 0:
            count_value = (count_value / float(total_count)) * 100.0
        count_text = format_distribution_hover_value(count_value, as_percent=as_percent)
        return [
            "{}: {}".format(x_label, x_text),
            "{}: {}".format(widget.tr("Cumulative"), count_text),
        ]

    def _drawCurveHoverMarker(self, painter, curve_sample):
        painter.setPen(QPen(CUMULATIVE_CURVE_COLOR, 2))
        painter.setBrush(CUMULATIVE_CURVE_COLOR)
        painter.drawEllipse(
            QPointF(curve_sample["screen_x"], curve_sample["screen_y"]),
            4,
            4,
        )

    def _drawCurveHoverTooltip(self, widget, painter, plotRect, curve_sample):
        lines = self._curveHoverTooltipLines(widget, curve_sample)
        self._drawHoverTooltipAt(
            painter,
            plotRect,
            QPointF(curve_sample["screen_x"], curve_sample["screen_y"]),
            lines,
        )

    def _hoverTooltipLines(self, widget, bin_data):
        segment = getattr(widget, "hoverSegment", None) or "frequency"
        as_percent = self._bar_mode(widget) == "relative"
        class_label = bin_data.get("label", "")

        if segment == "cumulative":
            value = self._bin_cumulative_bar_value(widget, bin_data)
            if value is None:
                value = 0.0
            value_text = format_distribution_hover_value(value, as_percent=as_percent)
            return [class_label, "{}: {}".format(widget.tr("Cumulative"), value_text)]

        value = self._bin_bar_value(widget, bin_data)
        value_text = format_distribution_hover_value(value, as_percent=as_percent)
        if as_percent:
            return [class_label, value_text]
        return [class_label, "{}: {}".format(widget.tr("Count"), value_text)]

    def _drawHoverTooltip(self, widget, painter, plotRect, barRects):
        bin_index = widget.hoverIndex
        if bin_index is None or bin_index >= len(widget.bins) or bin_index >= len(barRects):
            return

        lines = self._hoverTooltipLines(widget, widget.bins[bin_index])
        bar_rect = barRects[bin_index]
        anchor = QPointF(bar_rect.center().x(), bar_rect.top())
        self._drawHoverTooltipAt(painter, plotRect, anchor, lines, prefer_above=True)

    def _drawHoverTooltipAt(self, painter, plotRect, anchor, lines, prefer_above=False):
        font = qfont(self._SUBTITLE_FONT_SIZE)
        painter.setFont(font)
        font_metrics = QFontMetrics(font)
        text_width = max(font_metrics.horizontalAdvance(line) for line in lines) + 12
        text_height = font_metrics.height() * len(lines) + 10
        tooltip_x = anchor.x() + 8
        if prefer_above:
            tooltip_y = max(plotRect.top() + 4, anchor.y() - text_height - 4)
        else:
            tooltip_y = max(plotRect.top() + 4, anchor.y() - text_height - 4)
        if tooltip_x + text_width > plotRect.right():
            tooltip_x = anchor.x() - text_width - 8
        tooltip_rect = QRectF(tooltip_x, tooltip_y, text_width, text_height)
        painter.setBrush(TOOLTIP_BG_COLOR)
        painter.setPen(QPen(TOOLTIP_BORDER, 1))
        painter.drawRoundedRect(tooltip_rect, 4, 4)
        painter.setPen(TEXT_DARK)
        line_y = tooltip_y + font_metrics.ascent() + 4
        for line in lines:
            painter.drawText(QPointF(tooltip_x + 6, line_y), line)
            line_y += font_metrics.height()

    def _drawDistributionTopAxis(self, widget, painter, plotRect):
        scale_range = self._cumulativeXRange(widget)
        if scale_range is None:
            return

        x_min, x_max = scale_range
        label_font = qfont(self._tickFontSize(widget))
        painter.setFont(label_font)
        font_metrics = QFontMetrics(label_font)
        max_ticks = estimate_max_ticks(plotRect.width(), font_metrics.height() + 8, max_ticks=8)
        scale = compute_nice_scale(x_min, x_max, max_ticks, include_zero=False)

        painter.setPen(TEXT_AXIS)
        painter.drawLine(QPointF(plotRect.left(), plotRect.top()), QPointF(plotRect.right(), plotRect.top()))
        for tick_value in scale.ticks():
            if tick_value < x_min or tick_value > x_max:
                continue
            tick_x = self._xForCumulativeValue(plotRect, x_min, x_max, tick_value)
            label = format_number_tick(tick_value, scale.step)
            text_width = font_metrics.horizontalAdvance(label)
            painter.drawLine(QPointF(tick_x, plotRect.top()), QPointF(tick_x, plotRect.top() - _TICK_LEN))
            painter.drawText(
                QPointF(tick_x - text_width / 2, plotRect.top() - 7),
                label,
            )

    def _drawCumulativeFrequencyCurve(self, widget, painter, plotRect, right_scale):
        points_data = getattr(widget, "cumulative_points", [])
        scale_range = self._cumulativeXRange(widget)
        if not points_data or scale_range is None:
            return

        x_min, x_max = scale_range
        total_count = points_data[-1].get("count", 0)
        if total_count <= 0:
            return

        cumulative_mode = getattr(widget, "cumulative_mode", "absolute")
        path = QPainterPath()
        first_point = True

        for point_data in points_data:
            count = point_data.get("count", 0)
            y_value = (count / float(total_count)) * 100.0 if cumulative_mode == "relative" else count
            point = QPointF(
                self._xForCumulativeValue(plotRect, x_min, x_max, point_data.get("x", x_min)),
                self._yForValue(plotRect, right_scale, y_value),
            )
            if first_point:
                path.moveTo(point)
                first_point = False
            else:
                path.lineTo(point)

        painter.setPen(QPen(CUMULATIVE_CURVE_COLOR, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setClipRect(plotRect)
        painter.drawPath(path)
        painter.setClipping(False)

    def _cumulativeXRange(self, widget):
        points = getattr(widget, "cumulative_points", [])
        if not points:
            return None
        x_values = [point.get("x", 0.0) for point in points]
        x_min = min(x_values)
        x_max = max(x_values)
        if x_min == x_max:
            pad = abs(x_min) * 0.1 or 1.0
            x_min -= pad
            x_max += pad
        return x_min, x_max

    def _xForCumulativeValue(self, plotRect, x_min, x_max, value):
        axis_range = x_max - x_min
        if axis_range == 0:
            return plotRect.left()
        relative = (float(value) - x_min) / axis_range
        return plotRect.left() + relative * plotRect.width()
