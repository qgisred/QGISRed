# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFontMetrics, QPainterPath, QPen

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    estimate_max_ticks,
    format_number_tick,
)
from ..queries.statistics_histogram_renderer import StatisticsHistogramRenderer
from .timeseries_plot_style import BORDER_COLOR, GRID_COLOR, PLOT_BG_COLOR, TEXT_AXIS, qfont

CUMULATIVE_CURVE_COLOR = QColor(200, 60, 60)


class ResultsDistributionRenderer(StatisticsHistogramRenderer):
    """Histogram renderer for simulation results: class bars + optional cumulative curve."""

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
        right_scale = (
            self._computeCumulativeScale(widget, plotRect)
            if cumulative_mode in ("absolute", "relative")
            else None
        )

        self._drawGridAndLeftAxis(widget, painter, plotRect, left_scale)
        if right_scale is not None:
            self._drawDistributionRightAxis(widget, painter, plotRect, right_scale)

        bar_rects = self._drawBars(widget, painter, plotRect, left_scale)
        widget._barRects = bar_rects

        self._drawXAxisLabels(widget, painter, plotRect, bar_rects)

        if cumulative_mode in ("absolute", "relative") and right_scale is not None:
            self._drawCumulativeFrequencyCurve(widget, painter, plotRect, right_scale, bar_rects)

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

    def _computeLeftScale(self, widget, plotRect):
        values = [self._bin_bar_value(widget, bin_data) for bin_data in widget.bins]
        if not values:
            values = [0.0, 1.0]
        data_min = min(values + [0.0])
        data_max = max(values + [0.0])
        if data_max == data_min:
            data_max = data_min + 1.0
        label_height = QFontMetrics(qfont(self._AXIS_TICK_FONT_SIZE)).height() + 4
        max_ticks = estimate_max_ticks(plotRect.height(), label_height, max_ticks=10)
        return compute_nice_scale(data_min, data_max, max_ticks, include_zero=True)

    def _computeCumulativeScale(self, widget, plotRect):
        cumulative_mode = getattr(widget, "cumulative_mode", None)
        total_count = getattr(widget, "_totalCount", 0) or sum(
            item.get("count", 0) for item in widget.bins
        )
        if cumulative_mode == "relative":
            data_max = 100.0
        else:
            data_max = max(float(total_count), 1.0)
        label_height = QFontMetrics(qfont(self._AXIS_TICK_FONT_SIZE)).height() + 4
        max_ticks = estimate_max_ticks(plotRect.height(), label_height, max_ticks=8)
        return compute_nice_scale(0.0, data_max, max_ticks, include_zero=True)

    def _drawGridAndLeftAxis(self, widget, painter, plotRect, scale):
        painter.setFont(qfont(self._AXIS_TICK_FONT_SIZE))
        font_metrics = QFontMetrics(painter.font())
        bar_mode = self._bar_mode(widget)
        for tick_value in scale.ticks():
            tick_y = self._yForValue(plotRect, scale, tick_value)
            painter.setPen(QPen(GRID_COLOR, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plotRect.left(), tick_y), QPointF(plotRect.right(), tick_y))
            label = format_number_tick(tick_value, scale.step)
            painter.setPen(TEXT_AXIS)
            label_x = plotRect.left() - 6 - font_metrics.horizontalAdvance(label)
            painter.drawText(QPointF(label_x, tick_y + font_metrics.ascent() / 2 - 1), label)
        if widget.yLabelLeft:
            painter.setPen(TEXT_AXIS)
            painter.setFont(qfont(self._AXIS_TITLE_FONT_SIZE, bold=True))
            painter.save()
            painter.translate(12, plotRect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, widget.yLabelLeft)
            painter.restore()

    def _drawDistributionRightAxis(self, widget, painter, plotRect, scale):
        cumulative_mode = getattr(widget, "cumulative_mode", "absolute")
        painter.setFont(qfont(self._AXIS_TICK_FONT_SIZE))
        font_metrics = QFontMetrics(painter.font())
        for tick_value in scale.ticks():
            tick_y = self._yForValue(plotRect, scale, tick_value)
            label = format_number_tick(tick_value, scale.step)
            painter.setPen(TEXT_AXIS)
            painter.drawText(
                QPointF(plotRect.right() + 6, tick_y + font_metrics.ascent() / 2 - 1),
                label,
            )
        axis_title = getattr(widget, "yLabelRight", "") or ""
        if axis_title:
            painter.setPen(TEXT_AXIS)
            painter.setFont(qfont(self._AXIS_TITLE_FONT_SIZE, bold=True))
            painter.save()
            painter.translate(widget.width() - 12, plotRect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, axis_title)
            painter.restore()

    def _drawCumulativeFrequencyCurve(self, widget, painter, plotRect, right_scale, bar_rects):
        if not bar_rects:
            return

        total_count = getattr(widget, "_totalCount", 0) or sum(
            item.get("count", 0) for item in widget.bins
        )
        if total_count <= 0:
            return

        cumulative_mode = getattr(widget, "cumulative_mode", "absolute")
        running = 0.0
        final_y_value = 0.0
        points = [QPointF(plotRect.left(), self._yForValue(plotRect, right_scale, 0.0))]

        for bin_index, bin_data in enumerate(widget.bins):
            if bin_index >= len(bar_rects):
                break
            running += bin_data.get("count", 0)
            if cumulative_mode == "relative":
                final_y_value = (running / float(total_count)) * 100.0
            else:
                final_y_value = running
            points.append(
                QPointF(
                    bar_rects[bin_index].center().x(),
                    self._yForValue(plotRect, right_scale, final_y_value),
                )
            )

        points.append(
            QPointF(plotRect.right(), self._yForValue(plotRect, right_scale, final_y_value))
        )

        path = self._continuous_path_through_points(points)
        painter.setPen(QPen(CUMULATIVE_CURVE_COLOR, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setClipRect(plotRect)
        painter.drawPath(path)
        painter.setClipping(False)

    def _continuous_path_through_points(self, points):
        path = QPainterPath()
        if not points:
            return path
        if len(points) == 1:
            path.moveTo(points[0])
            return path
        if len(points) == 2:
            path.moveTo(points[0])
            path.lineTo(points[1])
            return path

        smoothness = 0.48
        path.moveTo(points[0])
        for index in range(len(points) - 1):
            start = points[index]
            end = points[index + 1]
            delta_x = end.x() - start.x()
            control_1 = QPointF(start.x() + delta_x * smoothness, start.y())
            control_2 = QPointF(end.x() - delta_x * smoothness, end.y())
            path.cubicTo(control_1, control_2, end)
        return path
