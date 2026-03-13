from PyQt5.QtGui import QColor, QCursor, QPixmap, QPainter, QPainterPath, QPen
from PyQt5.QtCore import Qt, QPoint
from qgis.core import QgsPointXY, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapCanvasSnappingUtils


class QGISRedSelectPointTool(QgsMapTool):
    def __init__(self, button, parent, method, type=1, cursor=None, icon_size=24):
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
            self.custom_cursor = self.create_combined_cursor(cursor)
        elif cursor is None:
            self.custom_cursor = Qt.CrossCursor

        # type 1: points; 2: lines; 3: 2-points; 4: 2-line; 5: point-line
        self.startMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.startMarker.setColor(QColor(255, 87, 51))
        if self.type == 3 or self.type == 4 or self.type == 5:
            self.startMarker.setColor(QColor(139, 0, 0))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_BOX)
        if self.type == 2 or self.type == 4:
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
        if self.type == 4 or self.type == 5:
            self.endMarker.setIconType(QgsVertexMarker.ICON_X)
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()
        self.firstPoint = None

        self.snapper = None
        self.resetProperties()

    def create_combined_cursor(self, icon):
        """Create a professional, sharp cursor with a slender arrow and a custom icon."""
        ratio = self.iface.mainWindow().devicePixelRatioF()
        
        # Calculate canvas size to avoid clipping
        canvas_width = max(32, 12 + self.icon_size)
        canvas_height = max(32, 12 + self.icon_size)
        
        pixmap = QPixmap(int(canvas_width * ratio), int(canvas_height * ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        # Use antialiasing for smooth diagonal lines
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Create a slender, proportional arrow path (Standard UI style)
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(0, 15)
        path.lineTo(4, 11)
        path.lineTo(6, 16)
        path.lineTo(8, 15)
        path.lineTo(6, 10.5)
        path.lineTo(11, 11)
        path.closeSubpath()
        
        # Draw with a clean black outline and white fill
        # Width 0 creates a cosmetic pen (the thinnest possible sharp line)
        painter.setPen(QPen(QColor(Qt.black), 0, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
        painter.setBrush(Qt.white)
        painter.drawPath(path)
        
        # Draw the custom icon at the bottom-right
        icon_pixmap = icon if isinstance(icon, QPixmap) else QPixmap(icon)
        if not icon_pixmap.isNull():
            scaled_icon = icon_pixmap.scaled(int(self.icon_size * ratio), int(self.icon_size * ratio), 
                                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled_icon.setDevicePixelRatio(ratio)
            
            # Position it adjusted by the size for a unified look
            offset = 11 if self.icon_size > 20 else 13
            painter.drawPixmap(offset, offset, scaled_icon)
        
        painter.end()
        # The hotspot (0,0) is at the tip
        return QCursor(pixmap, 0, 0)

    def activate(self):
        # Guard against calls during shutdown
        if hasattr(self.parent, 'isUnloading') and self.parent.isUnloading:
            return
        QgsMapTool.activate(self)
        if self.custom_cursor:
            self.canvas.setCursor(self.custom_cursor)

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
