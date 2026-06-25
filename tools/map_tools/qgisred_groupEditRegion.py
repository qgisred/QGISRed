# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsPoint, QgsPointXY, QgsGeometry
from qgis.gui import QgsMapTool, QgsRubberBand
try:
    from qgis.gui import Qgis as QgisGui
except Exception:
    try:
        from qgis.core import Qgis as QgisGui
    except Exception:
        QgisGui = None


class QGISRedGroupEditRegionTool(QgsMapTool):
    """Polygon picker for the Group Edit dialog.

    Left-click adds a vertex; right-click closes the polygon and emits
    `regionPicked` with the resulting QgsGeometry (in map CRS). Pressing
    right-click with no vertices simply cancels and emits `regionCancelled`.
    """

    regionPicked = pyqtSignal(object)
    regionCancelled = pyqtSignal()

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.mousePoints = []
        self.rubberBand = self._makeRubberBand(QColor(255, 0, 0, 80), Qt.PenStyle.SolidLine)
        self.previewBand = self._makeRubberBand(QColor(240, 40, 40, 0), Qt.PenStyle.DashLine)

    def _makeRubberBand(self, fillColor, lineStyle):
        try:
            band = QgsRubberBand(self.canvas, QgisGui.GeometryType.Polygon)
        except Exception:
            band = QgsRubberBand(self.canvas, 3)
        band.setColor(fillColor)
        band.setWidth(2)
        band.setLineStyle(lineStyle)
        return band

    def reset(self):
        self.mousePoints = []
        try:
            self.rubberBand.reset(QgisGui.GeometryType.Polygon)
            self.previewBand.reset(QgisGui.GeometryType.Polygon)
        except Exception:
            self.rubberBand.reset(3)
            self.previewBand.reset(3)

    def deactivate(self):
        self.reset()
        self.rubberBand.hide()
        self.previewBand.hide()
        QgsMapTool.deactivate(self)

    """Events"""

    def canvasMoveEvent(self, event):
        if not self.mousePoints:
            return
        point = self.toMapCoordinates(event.pos())
        self._drawPreview(self.mousePoints + [point])

    def canvasPressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self.toMapCoordinates(event.pos())
            self.mousePoints.append(point)
            self._drawPreview(self.mousePoints)
            return

        if event.button() == Qt.MouseButton.RightButton:
            if len(self.mousePoints) < 3:
                self.reset()
                self.regionCancelled.emit()
                self.canvas.unsetMapTool(self)
                return
            geometry = QgsGeometry.fromPolygonXY([list(self.mousePoints)])
            self.reset()
            self.regionPicked.emit(geometry)
            self.canvas.unsetMapTool(self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.reset()
            self.regionCancelled.emit()
            self.canvas.unsetMapTool(self)

    def _drawPreview(self, points):
        try:
            self.rubberBand.reset(QgisGui.GeometryType.Polygon)
            self.previewBand.reset(QgisGui.GeometryType.Polygon)
        except Exception:
            self.rubberBand.reset(3)
            self.previewBand.reset(3)
        if len(points) < 2:
            return
        ring = [QgsPointXY(p.x(), p.y()) for p in points]
        if len(ring) >= 3:
            self.rubberBand.setToGeometry(QgsGeometry.fromPolygonXY([ring]), None)
        else:
            line = [QgsPoint(p.x(), p.y()) for p in points]
            self.previewBand.setToGeometry(QgsGeometry.fromPolyline(line), None)
        self.rubberBand.show()
        self.previewBand.show()
