# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QPointF, QRectF, Qt, pyqtSignal
from qgis.PyQt.QtGui import QPainter
from qgis.PyQt.QtWidgets import QWidget

from .statistics_histogram_renderer import StatisticsHistogramRenderer


class StatisticsHistogramWidget(QWidget):
    viewChanged = pyqtSignal()

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
        self.hoverIndex = None
        self._barRects = []
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._panActive = False
        self._panStartPos = None
        self._panStartOffset = 0.0
        self._renderer = StatisticsHistogramRenderer()
        self.marginLeft = 52
        self.marginRight = 30
        self.marginTop = 40
        self.marginBottom = 44
        self.setMinimumSize(200, 180)
        self.setMouseTracking(True)

    def setBins(self, bins, mode="plain", xLabel="", yLabelLeft=""):
        self.bins = list(bins or [])
        self.mode = mode if mode in ("cumulative", "intensive", "plain") else "plain"
        self.xLabel = xLabel or ""
        self.yLabelLeft = yLabelLeft or ""
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self.update()

    def setMode(self, mode):
        if mode in ("cumulative", "intensive", "plain"):
            self.mode = mode
            self.update()

    def setTitles(self, title, subtitle=""):
        self.title = title or ""
        self.subtitle = subtitle or ""
        self.update()

    def clear(self):
        self.bins = []
        self.title = ""
        self.subtitle = ""
        self.xLabel = ""
        self.yLabelLeft = ""
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self.update()

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

    def getPlotRect(self):
        x = self.marginLeft
        y = self.marginTop
        width = max(0, self.width() - self.marginLeft - self.marginRight)
        height = max(0, self.height() - self.marginTop - self.marginBottom)
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
