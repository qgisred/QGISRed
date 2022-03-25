from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication
from qgis.core import QgsPointXY, QgsPoint, QgsGeometry, QgsFeature, QgsRectangle, QgsVectorLayer, QgsMapLayer
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.utils import Qgis
import processing


class QGISRedMultiLayerSelection(QgsMapTool):

    def __init__(self, iface, canvas, action):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.iface = iface
        self.setAction(action)
        self.myRubberBand = QgsRubberBand(self.canvas, 3)  # 3= Polygon
        mFillColor = QColor(255, 0, 0, 100)
        self.myRubberBand.setColor(mFillColor)
        self.myRubberBand.setWidth(2)
        self.myRubberBand.setLineStyle(2)

        self.rubberBand1 = None
        self.rubberBand2 = None

        self.reset()

    def deactivate(self):
        self.reset()
        self.myRubberBand.hide()
        QgsMapTool.deactivate(self)

    def activate(self):
        QgsMapTool.activate(self)

    """Methods"""
    def reset(self):
        self.initialPoint = None
        self.finalPoint = None
        self.isSelecting = False
        self.myRubberBand.reset(3)  # 3= Polygon

        if self.rubberBand1 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand1)
        if self.rubberBand2 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand2)

        self.mousePoints = []
        self.rubberBand1 = None
        self.rubberBand2 = None

    def createRubberBand(self, points):
        myPoints1 = []
        for p in points:
            myPoints1.append(QgsPoint(p.x(), p.y()))
        myPoints1.remove(myPoints1[-1])
        myPoints1.append(myPoints1[0])
        if self.rubberBand1 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand1)
        self.rubberBand1 = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand1.setToGeometry(QgsGeometry.fromPolyline(myPoints1), None)
        self.rubberBand1.setColor(QColor(240, 40, 40))
        self.rubberBand1.setWidth(1)
        self.rubberBand1.setLineStyle(Qt.SolidLine)

        myPoints2 = []
        myPoints2.append(QgsPoint(points[-2].x(), points[-2].y()))
        myPoints2.append(QgsPoint(points[-1].x(), points[-1].y()))
        myPoints2.append(QgsPoint(points[0].x(), points[0].y()))
        if self.rubberBand2 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand2)
        self.rubberBand2 = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand2.setToGeometry(QgsGeometry.fromPolyline(myPoints2), None)
        self.rubberBand2.setColor(QColor(240, 40, 40))
        self.rubberBand2.setWidth(1)
        self.rubberBand2.setLineStyle(Qt.DashLine)

    def showRectangle(self, initialPoint, finalPoint):
        self.myRubberBand.reset(3)
        if initialPoint.x() == finalPoint.x() or initialPoint.y() == finalPoint.y():
            return
        point1 = QgsPointXY(initialPoint.x(), initialPoint.y())
        point2 = QgsPointXY(initialPoint.x(), finalPoint.y())
        point3 = QgsPointXY(finalPoint.x(), finalPoint.y())
        point4 = QgsPointXY(finalPoint.x(), initialPoint.y())

        self.myRubberBand.addPoint(point1, False)
        self.myRubberBand.addPoint(point2, False)
        self.myRubberBand.addPoint(point3, False)
        self.myRubberBand.addPoint(point4, False)
        self.myRubberBand.closePoints()
        self.myRubberBand.show()

    def getRectangle(self):
        if self.initialPoint is None or self.finalPoint is None:
            return None
        elif self.initialPoint.x() == self.finalPoint.x() or self.initialPoint.y() == self.finalPoint.y():
            return None
        return QgsRectangle(self.initialPoint, self.finalPoint)

    """Events"""
    def canvasPressEvent(self, e):
        if e.button() == Qt.RightButton and len(self.mousePoints) > 0:
            poligon = QgsVectorLayer('Polygon', 'poly', "memory")
            pr = poligon.dataProvider()
            poly = QgsFeature()
            if len(self.mousePoints) > 3:
                self.mousePoints.remove(self.mousePoints[-1])
            poly.setGeometry(QgsGeometry.fromPolygonXY([self.mousePoints]))
            pr.addFeatures([poly])

            layers = self.canvas.layers()
            try:
                for layer in layers:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        continue
                    modifiers = QApplication.keyboardModifiers()
                    if modifiers == Qt.ShiftModifier:
                        processing.run('qgis:selectbylocation',
                                       {'INPUT': layer, 'PREDICATE': [0], 'INTERSECT': poligon, 'METHOD': 3})  # Remove
                    elif modifiers == Qt.ControlModifier:
                        processing.run('qgis:selectbylocation',
                                       {'INPUT': layer, 'PREDICATE': [0], 'INTERSECT': poligon, 'METHOD': 1})  # Add
                    else:
                        processing.run('qgis:selectbylocation',
                                       {'INPUT': layer, 'PREDICATE': [0], 'INTERSECT': poligon, 'METHOD': 0})  # Set
            except Exception:
                self.iface.messageBar().pushMessage("Warning", "Polygon not valid for selecting elements", level=1, duration=5)
            self.reset()
            poligon = None
            return
        elif e.button() == Qt.RightButton:
            self.canvas.unsetMapTool(self)
            self.deactivate()
            return
        # Rectangle
        if len(self.mousePoints) == 0:
            self.initialPoint = self.toMapCoordinates(e.pos())
            self.finalPoint = self.initialPoint
            self.isSelecting = True
            self.showRectangle(self.initialPoint, self.finalPoint)
        # Poliline
        point = self.toMapCoordinates(e.pos())
        self.mousePoints.append(point)
        if len(self.mousePoints) == 1:
            self.mousePoints.append(point)

    def canvasReleaseEvent(self, e):
        self.isSelecting = False
        rect = self.getRectangle()
        if rect is None:
            if len(self.mousePoints) > 0:
                self.createRubberBand(self.mousePoints)
        else:
            self.mousePoints = []
            layers = self.canvas.layers()
            for layer in layers:
                if layer.type() == QgsMapLayer.RasterLayer:
                    continue
                lRect = self.canvas.mapSettings().mapToLayerCoordinates(layer, rect)
                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ShiftModifier:
                    layer.selectByRect(lRect, Qgis.SelectBehavior.RemoveFromSelection)  # Remove
                elif modifiers == Qt.ControlModifier:
                    layer.selectByRect(lRect, Qgis.SelectBehavior.AddToSelection)  # Add
                else:
                    layer.selectByRect(lRect, Qgis.SelectBehavior.SetSelection)  # Set
            self.myRubberBand.hide()

    def canvasMoveEvent(self, e):
        point = self.toMapCoordinates(e.pos())
        if self.isSelecting:
            self.finalPoint = point
            self.showRectangle(self.initialPoint, self.finalPoint)
        elif len(self.mousePoints) > 0:
            self.mousePoints[-1] = point
            self.createRubberBand(self.mousePoints)
