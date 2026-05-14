# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFontMetrics, QPainterPath, QPen

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    estimate_max_ticks,
    format_number_tick,
)
from ..analysis.timeseries_plot_style import (
    BORDER_COLOR,
    DEFAULT_SERIES_COLOR,
    GRID_COLOR,
    PLOT_BG_COLOR,
    TEXT_AXIS,
    TEXT_DARK,
    TOOLTIP_BORDER,
    qfont,
)


CUMULATIVE_CURVE_COLOR = QColor(200, 60, 60)
AVERAGE_LINE_COLOR = QColor(40, 40, 40)
BAR_BORDER_COLOR = QColor(40, 80, 130)
TOOLTIP_BG_COLOR = QColor(255, 255, 255, 235)


class StatisticsHistogramRenderer:
    _AXIS_TITLE_FONT_SIZE = 10
    _AXIS_TICK_FONT_SIZE = 9
    _TITLE_FONT_SIZE = 11
    _SUBTITLE_FONT_SIZE = 9

    def render(self, widget, painter):
        painter.setRenderHint(PAINTER_ANTIALIASING)
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

        self._drawTitle(widget, painter)
        self._drawSubtitle(widget, painter, plotRect)

        leftScale = self._computeLeftScale(widget, plotRect)
        rightScale = self._computeRightScale() if widget.mode == "cumulative" else None

        self._drawGridAndLeftAxis(widget, painter, plotRect, leftScale)
        if rightScale is not None:
            self._drawRightAxis(widget, painter, plotRect, rightScale)

        barRects = self._drawBars(widget, painter, plotRect, leftScale)
        widget._barRects = barRects

        self._drawXAxisLabels(widget, painter, plotRect, barRects)

        if widget.mode == "cumulative" and rightScale is not None:
            self._drawCumulativeCurve(widget, painter, plotRect, rightScale, barRects)
            self._drawTotalLabel(widget, painter, plotRect)
        elif widget.mode == "intensive":
            self._drawAverageLine(widget, painter, plotRect, leftScale)

        if widget.hoverIndex is not None and 0 <= widget.hoverIndex < len(barRects):
            self._drawHoverTooltip(widget, painter, plotRect, barRects)

    def _drawNoData(self, widget, painter):
        painter.setPen(QColor(120, 120, 120))
        painter.setFont(qfont(11))
        painter.drawText(widget.rect(), Qt.AlignmentFlag.AlignCenter, widget.tr("No data"))

    def _drawTitle(self, widget, painter):
        if not widget.title:
            return
        painter.setPen(TEXT_DARK)
        painter.setFont(qfont(self._TITLE_FONT_SIZE, bold=True))
        rect = QRectF(0, 4, widget.width(), 18)
        elided = QFontMetrics(painter.font()).elidedText(
            widget.title, Qt.TextElideMode.ElideRight, max(0, int(widget.width()) - 8)
        )
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, elided)

    def _drawSubtitle(self, widget, painter, plotRect):
        if not widget.subtitle:
            return
        painter.setPen(QColor(80, 80, 80))
        painter.setFont(qfont(self._SUBTITLE_FONT_SIZE))
        rect = QRectF(0, 22, widget.width(), 14)
        elided = QFontMetrics(painter.font()).elidedText(
            widget.subtitle, Qt.TextElideMode.ElideRight, max(0, int(widget.width()) - 8)
        )
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, elided)

    def _computeLeftScale(self, widget, plotRect):
        values = []
        for binData in widget.bins:
            if widget.mode == "cumulative":
                values.append(binData.get("sum", 0.0))
            elif widget.mode == "intensive":
                values.append(binData.get("avg", 0.0) if binData.get("count", 0) else 0.0)
            else:
                values.append(binData.get("count", 0))
        if not values:
            values = [0.0, 1.0]
        dataMin = min(values + [0.0])
        dataMax = max(values + [0.0])
        if dataMax == dataMin:
            dataMax = dataMin + 1.0
        labelHeight = QFontMetrics(qfont(self._AXIS_TICK_FONT_SIZE)).height() + 4
        maxTicks = estimate_max_ticks(plotRect.height(), labelHeight, max_ticks=10)
        return compute_nice_scale(dataMin, dataMax, maxTicks, include_zero=True)

    def _computeRightScale(self):
        return compute_nice_scale(0.0, 100.0, 6, include_zero=True)

    def _drawGridAndLeftAxis(self, widget, painter, plotRect, scale):
        painter.setFont(qfont(self._AXIS_TICK_FONT_SIZE))
        fontMetrics = QFontMetrics(painter.font())
        for tickValue in scale.ticks():
            tickY = self._yForValue(plotRect, scale, tickValue)
            painter.setPen(QPen(GRID_COLOR, 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(plotRect.left(), tickY), QPointF(plotRect.right(), tickY))
            label = format_number_tick(tickValue, scale.step)
            painter.setPen(TEXT_AXIS)
            labelX = plotRect.left() - 6 - fontMetrics.horizontalAdvance(label)
            painter.drawText(QPointF(labelX, tickY + fontMetrics.ascent() / 2 - 1), label)
        if widget.yLabelLeft:
            painter.setPen(TEXT_AXIS)
            painter.setFont(qfont(self._AXIS_TITLE_FONT_SIZE, bold=True))
            painter.save()
            painter.translate(12, plotRect.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, widget.yLabelLeft)
            painter.restore()

    def _drawRightAxis(self, widget, painter, plotRect, scale):
        painter.setFont(qfont(self._AXIS_TICK_FONT_SIZE))
        fontMetrics = QFontMetrics(painter.font())
        for tickValue in scale.ticks():
            tickY = self._yForValue(plotRect, scale, tickValue)
            label = format_number_tick(tickValue, scale.step) + "%"
            painter.setPen(TEXT_AXIS)
            painter.drawText(QPointF(plotRect.right() + 6, tickY + fontMetrics.ascent() / 2 - 1), label)
        painter.setPen(TEXT_AXIS)
        painter.setFont(qfont(self._AXIS_TITLE_FONT_SIZE, bold=True))
        painter.save()
        painter.translate(widget.width() - 12, plotRect.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-80, -10, 160, 20), Qt.AlignmentFlag.AlignCenter, "%")
        painter.restore()

    def _drawBars(self, widget, painter, plotRect, leftScale):
        binCount = len(widget.bins)
        if binCount == 0:
            return []
        zoom = max(0.2, widget.zoomFactor)
        totalWidth = plotRect.width() * zoom
        slotWidth = totalWidth / binCount
        gapWidth = max(2, slotWidth * 0.15)
        barWidth = max(1.0, slotWidth - gapWidth)
        offset = widget.panOffset
        barRects = []
        for binIndex, binData in enumerate(widget.bins):
            barX = plotRect.left() + offset + binIndex * slotWidth + gapWidth / 2
            if widget.mode == "cumulative":
                barValue = binData.get("sum", 0.0)
            elif widget.mode == "intensive":
                barValue = binData.get("avg", 0.0) if binData.get("count", 0) else 0.0
            else:
                barValue = binData.get("count", 0)
            barTop = self._yForValue(plotRect, leftScale, barValue)
            zeroY = self._yForValue(plotRect, leftScale, 0.0)
            top = min(barTop, zeroY)
            height = abs(zeroY - barTop)
            barRect = QRectF(barX, top, barWidth, height)
            barRects.append(barRect)
            visibleRect = QRectF(barRect).intersected(plotRect)
            if visibleRect.width() > 0 and visibleRect.height() >= 0:
                fillColor = QColor(DEFAULT_SERIES_COLOR)
                if widget.hoverIndex == binIndex:
                    fillColor = fillColor.lighter(115)
                painter.fillRect(visibleRect, fillColor)
                painter.setPen(QPen(BAR_BORDER_COLOR, 1))
                painter.drawRect(visibleRect)
        return barRects

    def _drawXAxisLabels(self, widget, painter, plotRect, barRects):
        painter.setFont(qfont(self._AXIS_TICK_FONT_SIZE))
        fontMetrics = QFontMetrics(painter.font())
        painter.setPen(TEXT_AXIS)
        maxLabelWidth = max(40.0, (barRects[0].width() if barRects else 40.0) + 6)
        for binIndex, binData in enumerate(widget.bins):
            if binIndex >= len(barRects):
                break
            barRect = barRects[binIndex]
            centerX = barRect.center().x()
            if centerX < plotRect.left() - 4 or centerX > plotRect.right() + 4:
                continue
            label = binData.get("label", "")
            elided = fontMetrics.elidedText(label, Qt.TextElideMode.ElideRight, int(maxLabelWidth))
            textWidth = fontMetrics.horizontalAdvance(elided)
            painter.drawText(
                QPointF(centerX - textWidth / 2, plotRect.bottom() + fontMetrics.ascent() + 2),
                elided,
            )
        if widget.xLabel:
            painter.setFont(qfont(self._AXIS_TITLE_FONT_SIZE, bold=True))
            painter.drawText(
                QRectF(plotRect.left(), plotRect.bottom() + fontMetrics.height() + 6, plotRect.width(), 16),
                Qt.AlignmentFlag.AlignCenter,
                widget.xLabel,
            )

    def _drawCumulativeCurve(self, widget, painter, plotRect, rightScale, barRects):
        totalSum = sum(binData.get("sum", 0.0) for binData in widget.bins) or 1.0
        running = 0.0
        path = QPainterPath()
        firstPoint = True
        for binIndex, binData in enumerate(widget.bins):
            if binIndex >= len(barRects):
                break
            running += binData.get("sum", 0.0)
            percent = (running / totalSum) * 100.0
            pointX = barRects[binIndex].center().x()
            pointY = self._yForValue(plotRect, rightScale, percent)
            if firstPoint:
                path.moveTo(pointX, pointY)
                firstPoint = False
            else:
                path.lineTo(pointX, pointY)
        painter.setPen(QPen(CUMULATIVE_CURVE_COLOR, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setClipRect(plotRect)
        painter.drawPath(path)
        painter.setClipping(False)

    def _drawTotalLabel(self, widget, painter, plotRect):
        totalSum = sum(binData.get("sum", 0.0) for binData in widget.bins)
        text = "{}: {}".format(widget.tr("Total"), format_number_tick(totalSum, max(abs(totalSum) / 100.0, 0.01)))
        if widget.yLabelLeft:
            text = text + " " + widget.yLabelLeft
        painter.setFont(qfont(self._SUBTITLE_FONT_SIZE, bold=True))
        painter.setPen(CUMULATIVE_CURVE_COLOR)
        fontMetrics = QFontMetrics(painter.font())
        textWidth = fontMetrics.horizontalAdvance(text)
        painter.drawText(QPointF(plotRect.right() - textWidth - 4, plotRect.top() + fontMetrics.ascent() + 2), text)

    def _drawAverageLine(self, widget, painter, plotRect, leftScale):
        totalCount = sum(binData.get("count", 0) for binData in widget.bins)
        totalSum = sum(binData.get("sum", 0.0) for binData in widget.bins)
        if totalCount <= 0:
            return
        average = totalSum / totalCount
        averageY = self._yForValue(plotRect, leftScale, average)
        if averageY < plotRect.top() or averageY > plotRect.bottom():
            return
        painter.setPen(QPen(AVERAGE_LINE_COLOR, 1.5, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(plotRect.left(), averageY), QPointF(plotRect.right(), averageY))
        text = "{}: {}".format(widget.tr("Avg"), format_number_tick(average, max(abs(average) / 100.0, 0.01)))
        painter.setFont(qfont(self._SUBTITLE_FONT_SIZE, bold=True))
        painter.setPen(AVERAGE_LINE_COLOR)
        painter.drawText(QPointF(plotRect.left() + 6, averageY - 4), text)

    def _drawHoverTooltip(self, widget, painter, plotRect, barRects):
        binIndex = widget.hoverIndex
        binData = widget.bins[binIndex]
        barRect = barRects[binIndex]
        lines = [binData.get("label", "")]
        lines.append("{}: {}".format(widget.tr("Count"), binData.get("count", 0)))
        if widget.mode == "cumulative" or widget.mode == "plain":
            sumValue = binData.get("sum", 0.0)
            lines.append("{}: {}".format(
                widget.tr("Sum"),
                format_number_tick(sumValue, max(abs(sumValue) / 100.0, 0.01)),
            ))
        if binData.get("count", 0) > 0:
            averageValue = binData.get("avg", 0.0)
            lines.append("{}: {}".format(
                widget.tr("Avg"),
                format_number_tick(averageValue, max(abs(averageValue) / 100.0, 0.01)),
            ))
        font = qfont(self._SUBTITLE_FONT_SIZE)
        painter.setFont(font)
        fontMetrics = QFontMetrics(font)
        textWidth = max(fontMetrics.horizontalAdvance(line) for line in lines) + 12
        textHeight = fontMetrics.height() * len(lines) + 10
        tooltipX = barRect.center().x() + 8
        tooltipY = max(plotRect.top() + 4, barRect.top() - textHeight - 4)
        if tooltipX + textWidth > plotRect.right():
            tooltipX = barRect.center().x() - textWidth - 8
        tooltipRect = QRectF(tooltipX, tooltipY, textWidth, textHeight)
        painter.setBrush(TOOLTIP_BG_COLOR)
        painter.setPen(QPen(TOOLTIP_BORDER, 1))
        painter.drawRoundedRect(tooltipRect, 4, 4)
        painter.setPen(TEXT_DARK)
        lineY = tooltipY + fontMetrics.ascent() + 4
        for line in lines:
            painter.drawText(QPointF(tooltipX + 6, lineY), line)
            lineY += fontMetrics.height()

    def _yForValue(self, plotRect, scale, value):
        axisRange = scale.axis_max - scale.axis_min
        if axisRange == 0:
            return plotRect.bottom()
        relative = (value - scale.axis_min) / axisRange
        return plotRect.bottom() - relative * plotRect.height()
