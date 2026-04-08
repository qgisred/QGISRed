from enum import IntEnum
from qgis.PyQt.QtGui import QColor, QCursor, QPixmap
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapCanvasSnappingUtils
from ..utils.qgisred_styling_utils import create_combined_cursor
from ..utils.qgisred_ui_utils import QGISRedUIUtils
from ...compat import (
    SNAP_TYPE_VERTEX, SNAP_TYPE_SEGMENT, SNAP_TYPE_BOTH,
    VERTEX_ICON_BOX, VERTEX_ICON_TRIANGLE
)


class SelectPointType(IntEnum):
    Point = 1
    Line = 2
    TwoPoints = 3
    TwoLines = 4
    PointLine = 5


class QGISRedSelectPointTool(QgsMapTool):
    def __init__(self, button, parent, method, type=SelectPointType.Point, cursor=None, icon_size=24):
        # type 1: points; 2: lines; 3: 2-points; 4: 2-line; 5: point-line
        QgsMapTool.__init__(self, parent.iface.mapCanvas())
        self.canvas = parent.iface.mapCanvas()
        self.iface = parent.iface
        self.parent = parent
        self.method = method
        self.setAction(button)
        self.type = type
        self.icon_size = icon_size
        
        # Handle cursor: can be a string path, a QPixmap, or a QCursor
        self.custom_cursor = None
        if isinstance(cursor, QCursor):
            self.custom_cursor = cursor
        elif isinstance(cursor, (str, QPixmap)):
            self.custom_cursor = create_combined_cursor(cursor, self.iface, self.icon_size)
        elif cursor is None:
            self.custom_cursor = Qt.CursorShape.CrossCursor

        self.startMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.startMarker.setColor(QColor(255, 87, 51))
        if self.type == SelectPointType.TwoPoints or self.type == SelectPointType.TwoLines or self.type == SelectPointType.PointLine:
            self.startMarker.setColor(QColor(139, 0, 0))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_BOX)
        if self.type == SelectPointType.Line or self.type == SelectPointType.TwoLines:
            try:
                self.startMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE)
            except:
                self.startMarker.setIconType(QgsVertexMarker.ICON_X)
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.endMarker.setColor(QColor(0, 128, 0))
        self.endMarker.setIconSize(15)
        self.endMarker.setIconType(QgsVertexMarker.ICON_BOX)
        if self.type == SelectPointType.TwoLines or self.type == SelectPointType.PointLine:
            self.endMarker.setIconType(QgsVertexMarker.ICON_X)
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
        if self.custom_cursor:
            self.canvas.setCursor(self.custom_cursor)

        snap_type = SNAP_TYPE_VERTEX
        if self.type == SelectPointType.Line:
            snap_type = SNAP_TYPE_BOTH
        elif self.type == SelectPointType.TwoLines:
            snap_type = SNAP_TYPE_SEGMENT
        self.configSnapper(snap_type)

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

    def configSnapper(self, snapping_type):
        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(snapping_type)  # SNAP_TYPE_VERTEX or SNAP_TYPE_SEGMENT
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
        if event.button() == Qt.MouseButton.LeftButton:
            if self.objectSnapped is None:
                QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("A not valid point was selected"), level=1, duration=5)
                return
            if self.type == SelectPointType.TwoPoints or self.type == SelectPointType.TwoLines or self.type == SelectPointType.PointLine:
                if self.firstPoint is None:
                    self.firstPoint = self.objectSnapped.point()
                    if self.type == SelectPointType.PointLine:
                        self.configSnapper(SNAP_TYPE_SEGMENT)
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
        if event.button() == Qt.MouseButton.RightButton:
            if self.type == SelectPointType.TwoPoints or self.type == SelectPointType.PointLine:
                if self.objectSnapped is None:
                    QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("A not valid point was selected"), level=1, duration=5)
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

            if self.type == SelectPointType.Line:
                marker = self.startMarker if self.firstPoint is None else self.endMarker
                if match.hasVertex():
                    marker.setIconType(VERTEX_ICON_BOX)
                elif match.hasEdge():
                    marker.setIconType(VERTEX_ICON_TRIANGLE)

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
