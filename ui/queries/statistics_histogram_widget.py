# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QPointF, QRectF, Qt, pyqtSignal
from qgis.PyQt.QtGui import QFontMetrics, QPainter
from qgis.PyQt.QtWidgets import QWidget

from ..analysis.timeseries_plot_style import qfont
from ...tools.utils.qgisred_axis_scale_utils import compute_nice_scale, estimate_max_ticks, format_number_tick
from .statistics_histogram_layout import (
    adaptive_axis_tick_font_size,
    cap_bottom_margin,
    cumulative_right_axis_margin,
    longest_x_label_width,
    rotated_x_label_extra_height,
    x_tick_labels_need_rotation,
)
from .statistics_histogram_renderer import StatisticsHistogramRenderer


class StatisticsHistogramWidget(QWidget):
    viewChanged = pyqtSignal()

    _TICK_CHAR_WIDTH = 6.0

    def tr(self, message):
        return QCoreApplication.translate("StatisticsHistogramWidget", message)

    def __init__(self, parent=None):
        super(StatisticsHistogramWidget, self).__init__(parent)
        self.bins = []
        self.mode = "plain"
        self.title = ""
        self.subtitle = ""
        self.xLabel = ""
        self.yLabelLeft = ""
        self.statKey = "count"
        self.valueKey = None
        self.hoverIndex = None
        self._barRects = []
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._panActive = False
        self._panStartPos = None
        self._panStartOffset = 0.0
        self._renderer = StatisticsHistogramRenderer()
        self._axisTickFontSize = 9
        self._rotatedLabelExtra = 0
        self.marginLeft = 52
        self.marginRight = 30
        self.marginTop = 40
        self.marginBottom = 44
        self.setMinimumSize(200, 180)
        self.setMouseTracking(True)

    def setBins(self, bins, mode="plain", xLabel="", yLabelLeft="", statKey="count", valueKey=None):
        self.bins = list(bins or [])
        self.mode = mode if mode in ("cumulative", "intensive", "plain") else "plain"
        self.xLabel = xLabel or ""
        self.yLabelLeft = yLabelLeft or ""
        self.statKey = statKey or "count"
        self.valueKey = valueKey
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._fitMargins()
        self.update()

    def setMode(self, mode):
        if mode in ("cumulative", "intensive", "plain"):
            self.mode = mode
            self._fitMargins()
            self.update()

    def setTitles(self, title, subtitle=""):
        self.title = title or ""
        self.subtitle = subtitle or ""
        self._fitMargins()
        self.update()

    def clear(self):
        self.bins = []
        self.title = ""
        self.subtitle = ""
        self.xLabel = ""
        self.yLabelLeft = ""
        self.statKey = "count"
        self.valueKey = None
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._fitMargins()
        self.update()

    def barValueFor(self, binData):
        if self.mode == "cumulative":
            return binData.get("sum", 0.0)
        if self.mode == "intensive":
            return binData.get("avg", 0.0) if binData.get("count", 0) else 0.0
        if self.valueKey is not None:
            return binData.get("values", {}).get(self.valueKey, 0)
        if self.statKey == "sum":
            return binData.get("sum", 0.0) if binData.get("count", 0) else 0.0
        if self.statKey == "avg":
            return binData.get("avg", 0.0) if binData.get("count", 0) else 0.0
        if self.statKey == "stddev":
            return binData.get("stddev", 0.0) if binData.get("count", 0) > 1 else 0.0
        if self.statKey == "min":
            minValue = binData.get("min")
            return minValue if minValue is not None else 0.0
        if self.statKey == "max":
            maxValue = binData.get("max")
            return maxValue if maxValue is not None else 0.0
        return binData.get("count", 0)

    def resizeEvent(self, event):
        super(StatisticsHistogramWidget, self).resizeEvent(event)
        self._fitMargins()

    def axisTickFontSize(self):
        return self._axisTickFontSize

    def _fitMargins(self):
        self._axisTickFontSize = adaptive_axis_tick_font_size(self.width(), self.height())
        tick_font = qfont(self._axisTickFontSize)
        font_metrics = QFontMetrics(tick_font)

        plot_width_guess = max(40, self.width() - self.marginLeft - self.marginRight)
        plot_height_guess = max(40, self.height() - self.marginTop - self.marginBottom)
        values = [self.barValueFor(bin_data) for bin_data in self.bins]
        if not values:
            values = [0.0, 1.0]
        data_min = min(values + [0.0])
        data_max = max(values + [0.0])
        if data_max == data_min:
            data_max = data_min + 1.0
        label_height = font_metrics.height() + 4
        max_ticks = estimate_max_ticks(plot_height_guess, label_height, max_ticks=10)
        scale = compute_nice_scale(data_min, data_max, max_ticks, include_zero=True)
        max_tick_label_width = 0
        for tick_value in scale.ticks():
            label = format_number_tick(tick_value, scale.step)
            if self.mode == "relative":
                label = label + "%"
            max_tick_label_width = max(max_tick_label_width, font_metrics.horizontalAdvance(label))
        self.marginLeft = max(44, min(76, max_tick_label_width + 14))

        if self.mode == "cumulative":
            right_tick_labels = [
                format_number_tick(tick_value, 1.0)
                for tick_value in compute_nice_scale(0.0, 100.0, 6, include_zero=True).ticks()
            ]
            self.marginRight = cumulative_right_axis_margin(
                self._axisTickFontSize,
                right_tick_labels,
                "%",
                min_margin=40,
                max_margin=88,
            )
        else:
            self.marginRight = max(18, min(36, max(18, plot_width_guess // 30)))

        plot_width = max(0, self.width() - self.marginLeft - self.marginRight)
        rotate = x_tick_labels_need_rotation(self.bins, plot_width, self._axisTickFontSize, self._TICK_CHAR_WIDTH)
        base_bottom = font_metrics.height() + (22 if rotate else 14)
        if self.xLabel and not rotate:
            base_bottom += font_metrics.height() + 4
        self.marginBottom = max(30, min(56, base_bottom))

        if rotate:
            max_label_width = longest_x_label_width(self.bins, self._axisTickFontSize)
            rotated_extra = rotated_x_label_extra_height(
                self._axisTickFontSize,
                max_label_width,
                has_x_label=bool(self.xLabel),
            )
            self._rotatedLabelExtra = cap_bottom_margin(
                self.height(),
                self.marginTop,
                self.marginBottom,
                rotated_extra,
            ) - self.marginBottom
        else:
            self._rotatedLabelExtra = 0

    def resetView(self):
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self.hoverIndex = None
        self.update()
        self.viewChanged.emit()

    def zoomIn(self, factor=1.3):
        self._applyZoom(factor)

    def zoomOut(self, factor=1.3):
        self._applyZoom(1.0 / factor)

    def _applyZoom(self, factor, anchorX=None):
        plotRect = self.getPlotRect()
        if plotRect.width() <= 0 or not self.bins:
            return
        previousZoom = self.zoomFactor
        newZoom = max(1.0, min(20.0, self.zoomFactor * factor))
        if newZoom == previousZoom:
            return
        if anchorX is None:
            anchorX = plotRect.center().x()
        relativeX = anchorX - plotRect.left() - self.panOffset
        scaleRatio = newZoom / previousZoom
        newOffset = anchorX - plotRect.left() - relativeX * scaleRatio
        self.zoomFactor = newZoom
        self.panOffset = self._clampOffset(newOffset, plotRect, newZoom)
        self.hoverIndex = None
        self.update()
        self.viewChanged.emit()

    def _clampOffset(self, offset, plotRect, zoom):
        totalWidth = plotRect.width() * zoom
        minOffset = plotRect.width() - totalWidth
        if minOffset > 0:
            minOffset = 0
        if offset > 0:
            offset = 0
        if offset < minOffset:
            offset = minOffset
        return offset

    def xTickLabelsNeedRotation(self):
        plot_width = max(0, self.width() - self.marginLeft - self.marginRight)
        return x_tick_labels_need_rotation(self.bins, plot_width, self._axisTickFontSize, self._TICK_CHAR_WIDTH)

    def getPlotRect(self):
        x = self.marginLeft
        y = self.marginTop
        width = max(0, self.width() - self.marginLeft - self.marginRight)
        bottom_margin = self.marginBottom + self._rotatedLabelExtra
        height = max(0, self.height() - self.marginTop - bottom_margin)
        return QRectF(x, y, width, height)

    def paintEvent(self, event):
        painter = QPainter(self)
        self._renderer.render(self, painter)

    def leaveEvent(self, event):
        if self.hoverIndex is not None:
            self.hoverIndex = None
            self.update()

    def wheelEvent(self, event):
        if not self.bins:
            return
        plotRect = self.getPlotRect()
        cursorPos = event.position() if hasattr(event, "position") else QPointF(event.pos())
        if not plotRect.contains(cursorPos):
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.25 if delta > 0 else 1.0 / 1.25
        self._applyZoom(factor, anchorX=cursorPos.x())
        event.accept()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self.bins:
            return
        plotRect = self.getPlotRect()
        cursorPos = QPointF(event.pos())
        if not plotRect.contains(cursorPos):
            return
        self._panActive = True
        self._panStartPos = cursorPos
        self._panStartOffset = self.panOffset
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if self._panActive:
            self._panActive = False
            self._panStartPos = None
            self.unsetCursor()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.bins:
            self.resetView()

    def mouseMoveEvent(self, event):
        cursorPos = QPointF(event.pos())
        plotRect = self.getPlotRect()
        if self._panActive and self._panStartPos is not None:
            deltaX = cursorPos.x() - self._panStartPos.x()
            newOffset = self._clampOffset(self._panStartOffset + deltaX, plotRect, self.zoomFactor)
            if newOffset != self.panOffset:
                self.panOffset = newOffset
                self.hoverIndex = None
                self.update()
                self.viewChanged.emit()
            return
        newHover = self._barIndexAt(cursorPos, plotRect)
        if newHover != self.hoverIndex:
            self.hoverIndex = newHover
            self.update()

    def _barIndexAt(self, cursorPos, plotRect):
        if not self._barRects or not plotRect.contains(cursorPos):
            return None
        for barIndex, barRect in enumerate(self._barRects):
            visibleRect = QRectF(barRect).intersected(plotRect)
            if visibleRect.width() <= 0:
                continue
            if visibleRect.left() <= cursorPos.x() <= visibleRect.right() and plotRect.top() <= cursorPos.y() <= plotRect.bottom():
                return barIndex
        return None
