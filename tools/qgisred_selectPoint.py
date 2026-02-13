from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor, QPixmap
from qgis.core import QgsPointXY, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapCanvasSnappingUtils


class QGISRedSelectPointTool(QgsMapTool):
    def __init__(self, button, parent, method, type=1):
        QgsMapTool.__init__(self, parent.iface.mapCanvas())
        self.canvas = parent.iface.mapCanvas()
        self.iface = parent.iface
        self.parent = parent
        self.method = method
        self.setAction(button)
        self.type = type

        # type 1: points; 2: lines; 3: 2-points; 4: 2-line; 5: point-line

        self.startMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.startMarker.setColor(QColor(255, 87, 51))
        if self.type == 3 or self.type == 4 or self.type == 5:
            self.startMarker.setColor(QColor(139, 0, 0))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        if self.type == 2 or self.type == 4:
            try:
                self.startMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE)  # or ICON_CROSS, ICON_X
            except:
                self.startMarker.setIconType(QgsVertexMarker.ICON_X)  # or ICON_CROSS, ICON_X
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.endMarker.setColor(QColor(0, 128, 0))
        self.endMarker.setIconSize(15)
        self.endMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        if self.type == 4 or self.type == 5:
            self.endMarker.setIconType(QgsVertexMarker.ICON_X)  # or ICON_CROSS, ICON_X
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()
        self.firstPoint = None

        self.snapper = None
        self.resetProperties()

    def activate(self):
        # Guard against calls during shutdown
        if hasattr(self.parent, 'isUnloading') and self.parent.isUnloading:
            return
        QgsMapTool.activate(self)
        pencil_cursor = QCursor(QPixmap(":/plugins/QGISRed/images/pencil.svg"), 0, 0)
        self.canvas.setCursor(pencil_cursor)
        type = 1
        if self.type == 2 or self.type == 4:
            type = 2
        self.configSnapper(type)

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

    def configSnapper(self, type):
        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(type)  # 1: Vertex; 2:Segment
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)  # All layers
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.snapper.setConfig(config)

    def resetProperties(self):
        self.firstPoint = None
        self.startMarker.hide()
        self.endMarker.hide()
        self.objectSnapped = None

    """Events"""

    def canvasReleaseEvent(self, event):
        # Guard against calls during shutdown
        if hasattr(self.parent, 'isUnloading') and self.parent.isUnloading:
            return
        if event.button() == Qt.LeftButton:
            if self.objectSnapped is None:
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("A not valid point was selected"), level=1, duration=5)
                return
            if self.type == 3 or self.type == 4 or self.type == 5:
                if self.firstPoint is None:
                    self.firstPoint = self.objectSnapped.point()
                    if self.type == 5:
                        self.configSnapper(2)
                else:
                    point1 = self.firstPoint
                    point2 = self.objectSnapped.point()
                    # Call to parent method
                    self.method(point1, point2)
                    self.deactivate()
                    self.activate()
                    # self.resetProperties()
                    # if self.type == 5:
                    #     self.configSnapper(1)
            else:
                point = self.objectSnapped.point()
                # Call to parent method
                self.deactivate()
                self.activate()
                self.method(point)

                # self.resetProperties()
        if event.button() == Qt.RightButton:
            if self.type == 3 or self.type == 5:
                if self.objectSnapped is None:
                    self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("A not valid point was selected"), level=1, duration=5)
                    return
                else:
                    point = self.objectSnapped.point()
                    # Call to parent method
                    # Tconnection & Split/merge Juncitons
                    self.method(point, None)
                    self.deactivate()
                    self.activate()
                    # self.resetProperties()
            else:
                self.canvas.unsetMapTool(self)
                self.deactivate()
                return

    def canvasMoveEvent(self, event):
        match = self.snapper.snapToMap(self.toMapCoordinates(event.pos()))
        if match.isValid():
            self.objectSnapped = match
            if self.firstPoint is None:
                self.startMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.startMarker.show()
            else:
                self.endMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.endMarker.show()
        else:
            self.startMarker.hide()
            self.endMarker.hide()
            self.objectSnapped = None
