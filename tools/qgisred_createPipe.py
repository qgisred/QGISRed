from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qgis.core import QgsPointXY, QgsPoint, QgsGeometry, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnappingUtils, Qgis


class QGISRedCreatePipeTool(QgsMapTool):
    def __init__(self, button, iface, projectDirectory, netwName, method):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.ProjectDirectory = projectDirectory
        self.NetworkName = netwName
        self.method = method
        self.setAction(button)

        self.startMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.startMarker.setColor(QColor(255, 87, 51))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.endMarker.setColor(QColor(255, 87, 51))
        self.endMarker.setIconSize(15)
        self.endMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()

        self.snapper = None
        self.rubberBand1 = None
        self.rubberBand2 = None
        self.resetProperties()

    def activate(self):
        QgsMapTool.activate(self)

        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(1)  # Vertex
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)  # All layers
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.snapper.setConfig(config)

    def deactivate(self):
        self.resetProperties()
        QgsMapTool.deactivate(self)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    """Methods"""

    def resetProperties(self):
        # self.toolbarButton.setChecked(False)
        if self.rubberBand1 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand1)
        if self.rubberBand2 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand2)
        self.startMarker.hide()
        self.endMarker.hide()

        self.mousePoints = []
        self.firstClicked = False
        self.objectSnapped = None

        self.rubberBand1 = None
        self.rubberBand2 = None

    def createRubberBand(self, points):
        myPoints1 = []
        for p in points:
            myPoints1.append(QgsPoint(p.x(), p.y()))
        myPoints1.remove(myPoints1[-1])
        if self.rubberBand1 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand1)
        try:  # From QGis 3.30
            self.rubberBand1 = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Line)
        except:
            self.rubberBand1 = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand1.setToGeometry(QgsGeometry.fromPolyline(myPoints1), None)
        self.rubberBand1.setColor(QColor(240, 40, 40))
        self.rubberBand1.setWidth(1)
        self.rubberBand1.setLineStyle(Qt.SolidLine)

        myPoints2 = []
        myPoints2.append(QgsPoint(points[-2].x(), points[-2].y()))
        myPoints2.append(QgsPoint(points[-1].x(), points[-1].y()))
        if self.rubberBand2 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand2)
        try:  # From QGis 3.30
            self.rubberBand2 = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Line)
        except:
            self.rubberBand2 = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand2.setToGeometry(QgsGeometry.fromPolyline(myPoints2), None)
        self.rubberBand2.setColor(QColor(240, 40, 40))
        self.rubberBand2.setWidth(1)
        self.rubberBand2.setLineStyle(Qt.DashLine)

    """Events"""

    def canvasPressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.firstClicked:
                self.firstClicked = True
                point = self.toMapCoordinates(event.pos())
                if self.objectSnapped is not None:
                    point = self.objectSnapped.point()
                self.mousePoints.append(point)
                self.mousePoints.append(point)
            else:
                self.mousePoints.append(self.mousePoints[-1])
            self.createRubberBand(self.mousePoints)

        if event.button() == Qt.RightButton:
            self.mousePoints.remove(self.mousePoints[-1])
            if self.firstClicked:
                if len(self.mousePoints) == 2 and self.mousePoints[0] == self.mousePoints[1]:
                    createdPipe = False
                elif len(self.mousePoints) < 2:
                    createdPipe = False
                else:
                    createdPipe = True
            if createdPipe:
                self.method(self.mousePoints)
            self.resetProperties()

    def canvasMoveEvent(self, event):
        # Mouse not clicked
        if not self.firstClicked:
            match = self.snapper.snapToMap(self.toMapCoordinates(event.pos()))
            if match.isValid():
                self.objectSnapped = match
                self.startMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.startMarker.show()
            else:
                self.objectSnapped = None
                self.startMarker.hide()
        # Mouse clicked
        else:
            point = self.toMapCoordinates(event.pos())
            match = self.snapper.snapToMap(point)
            if match.isValid():
                self.objectSnapped = match
                self.endMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.endMarker.show()
                self.mousePoints[-1] = match.point()
            else:
                self.objectSnapped = None
                self.endMarker.hide()
                self.mousePoints[-1] = point
            self.createRubberBand(self.mousePoints)
