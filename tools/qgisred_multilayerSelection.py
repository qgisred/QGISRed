from qgis.gui import *
from qgis.core import *
from PyQt5.Qt import *

class QGISRedUtilsMultiLayerSelection(QgsMapTool):

    def __init__(self, canvas, action):
        QgsMapTool.__init__(self, canvas)
        self.canvas = canvas
        self.setAction(action)
        self.myRubberBand = QgsRubberBand(self.canvas, 3) #3= Polygon
        mFillColor = QColor( 255, 0, 0, 100);
        self.myRubberBand.setColor(mFillColor)
        self.myRubberBand.setWidth(2)
        self.myRubberBand.setLineStyle(2)
        self.reset()
    
    def reset(self):
        self.initialPoint = None
        self.finalPoint = None
        self.isSelecting = False
        self.myRubberBand.reset(3) #3= Polygon
    
    def canvasPressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.canvas.unsetMapTool(self)
            self.deactivate()
            return
        self.initialPoint = self.toMapCoordinates(e.pos())
        self.finalPoint = self.initialPoint
        self.isSelecting = True
        self.showRectangle(self.initialPoint, self.finalPoint)
    
    def canvasReleaseEvent(self, e):
        self.isSelecting = False
        rect = self.getRectangle()
        layers = self.canvas.layers()
        for layer in layers:
            if layer.type() == QgsMapLayer.RasterLayer:
                continue
            if rect is not None:
                lRect = self.canvas.mapSettings().mapToLayerCoordinates(layer, rect)
                modifiers = QApplication.keyboardModifiers()
                if modifiers == QtCore.Qt.ShiftModifier:
                    layer.selectByRect(lRect, 3) #Remove
                elif modifiers == QtCore.Qt.ControlModifier:
                    layer.selectByRect(lRect, 1) #Add
                else:
                    layer.selectByRect(lRect, 0) #Set
        self.myRubberBand.hide()
    
    def canvasMoveEvent(self, e):
        if not self.isSelecting:
            return
        self.finalPoint = self.toMapCoordinates(e.pos())
        self.showRectangle(self.initialPoint, self.finalPoint)
    
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
    
    def deactivate(self):
        self.myRubberBand.hide()
        QgsMapTool.deactivate(self)
        
    def activate(self):
        QgsMapTool.activate(self)