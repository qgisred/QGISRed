import math
from qgis.PyQt.QtCore import Qt, QSettings, QEvent, QPoint, QCoreApplication
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QCheckBox, QFrame, QHBoxLayout
from qgis.core import QgsPointXY, QgsPoint, QgsGeometry, QgsProject, QgsSnappingConfig, QgsTolerance, Qgis
from ...compat import SNAP_TYPE_VERTEX
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnappingUtils
try:
    from qgis.gui import Qgis
except:
    try:
        from qgis.core import Qgis  # Compatibility with QGis 3.4x
    except:
        pass


class QGISRedCreateLineTool(QgsMapTool):
    """Base class for line-drawing map tools (pipes, connections).

    Subclasses override class attributes to customize visual and snapping behavior:
      MARKER_ICON      — QgsVertexMarker icon type
      MARKER_SIZE      — icon size in pixels
      SNAP_TYPE        — 1=Vertex, 3=Segment
      SNAP_TO_SEGMENTS — True enables firstSnapped logic and double-click to finish
      SHOW_GRID        — True draws an adaptive grid overlay and snaps to it
    """

    MARKER_ICON = QgsVertexMarker.ICON_BOX
    MARKER_SIZE = 15
    SNAP_TYPE = SNAP_TYPE_VERTEX
    SNAP_TO_SEGMENTS = False
    SHOW_GRID = False

    def __init__(self, button, iface, projectDirectory, netwName, method):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.ProjectDirectory = projectDirectory
        self.NetworkName = netwName
        self.method = method
        self.setAction(button)

        self.startMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.startMarker.setColor(QColor(255, 87, 51))
        self.startMarker.setIconSize(self.MARKER_SIZE)
        self.startMarker.setIconType(self.MARKER_ICON)
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.endMarker.setColor(QColor(255, 87, 51))
        self.endMarker.setIconSize(self.MARKER_SIZE)
        self.endMarker.setIconType(self.MARKER_ICON)
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()

        self.snapper = None
        self.rubberBand1 = None
        self.rubberBand2 = None
        self._gridRubberBand = None
        self._gridSpacing = 0.0
        self._gridOverlayWidget = None
        self._gridOverlayCb = None
        self._showGrid = self.SHOW_GRID
        self.resetProperties()

    def activate(self):
        QgsMapTool.activate(self)

        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(self.SNAP_TYPE)
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.snapper.setConfig(config)

        if self.SHOW_GRID:
            self._showGrid = QSettings().value("QGISRed/showComplementaryGrid", self.SHOW_GRID, type=bool)
            self._createGridOverlay()
            if self._showGrid:
                self._updateGrid()
                self.iface.mapCanvas().extentsChanged.connect(self._updateGrid)

    def deactivate(self):
        if self._showGrid:
            try:
                self.iface.mapCanvas().extentsChanged.disconnect(self._updateGrid)
            except Exception:
                pass
        if self._gridOverlayWidget is not None:
            self.iface.mainWindow().removeEventFilter(self)
            self._gridOverlayWidget.deleteLater()
            self._gridOverlayWidget = None
            self._gridOverlayCb = None
        self._clearGrid()
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
        if self.rubberBand1 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand1)
        if self.rubberBand2 is not None:
            self.iface.mapCanvas().scene().removeItem(self.rubberBand2)
        self.startMarker.hide()
        self.endMarker.hide()

        self.mousePoints = []
        self.firstClicked = False
        self.firstSnapped = False
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
        self.rubberBand1.setLineStyle(Qt.PenStyle.SolidLine)

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
        self.rubberBand2.setLineStyle(Qt.PenStyle.DashLine)

    """Grid"""

    def _calcGridSpacing(self):
        """Return a 'nice' grid spacing (~15 columns across the visible extent)."""
        width = self.iface.mapCanvas().extent().width()
        if width <= 0:
            return 1.0
        raw = width / 15.0
        exp = math.floor(math.log10(raw))
        base = raw / (10 ** exp)
        if base < 1.5:
            nice = 1
        elif base < 3.5:
            nice = 2
        else:
            nice = 5
        return nice * (10 ** exp)

    def _clearGrid(self):
        if self._gridRubberBand is not None:
            self.iface.mapCanvas().scene().removeItem(self._gridRubberBand)
            self._gridRubberBand = None

    def _updateGrid(self):
        """Redraw the grid overlay to match the current canvas extent."""
        self._clearGrid()
        self._gridSpacing = self._calcGridSpacing()
        s = self._gridSpacing
        extent = self.iface.mapCanvas().extent()

        # First grid coordinate >= xmin / ymin
        import math as _math
        x0 = _math.ceil(extent.xMinimum() / s) * s
        y0 = _math.ceil(extent.yMinimum() / s) * s

        xs = []
        x = x0
        while x <= extent.xMaximum():
            xs.append(x)
            x += s
        ys = []
        y = y0
        while y <= extent.yMaximum():
            ys.append(y)
            y += s

        # Safety cap: max 50×50 = 2500 points
        if len(xs) > 50:
            xs = xs[:50]
        if len(ys) > 50:
            ys = ys[:50]

        if not xs or not ys:
            return

        # Build multipoint geometry
        pts = [QgsPointXY(x, y) for x in xs for y in ys]
        geom = QgsGeometry.fromMultiPointXY(pts)

        try:
            self._gridRubberBand = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Point)
        except:
            self._gridRubberBand = QgsRubberBand(self.iface.mapCanvas(), True)
        self._gridRubberBand.setToGeometry(geom, None)
        self._gridRubberBand.setColor(QColor(100, 100, 200, 100))
        self._gridRubberBand.setIcon(QgsRubberBand.ICON_CROSS)
        self._gridRubberBand.setIconSize(4)

    def _snapToGrid(self, point):
        """Round a QgsPointXY to the nearest grid intersection."""
        s = self._gridSpacing
        return QgsPointXY(round(point.x() / s) * s, round(point.y() / s) * s)

    def _createGridOverlay(self):
        """Create a floating checkbox over the top-right corner of the canvas.
        Parented to mainWindow so it receives events independently of the canvas."""
        main_win = self.iface.mainWindow()
        frame = QFrame(main_win)
        frame.setStyleSheet(
            "QFrame { background: rgba(255,255,255,200); border-radius:4px; padding:2px; }"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(6, 2, 6, 2)
        cb = QCheckBox(self._gridLabel())
        cb.setChecked(self._showGrid)
        cb.toggled.connect(self._onGridToggled)
        layout.addWidget(cb)
        frame.adjustSize()
        self._gridOverlayCb = cb
        self._gridOverlayWidget = frame
        self._repositionOverlay()
        frame.show()
        frame.raise_()
        main_win.installEventFilter(self)

    def _repositionOverlay(self):
        """Place the overlay at the top-right of the map canvas."""
        if self._gridOverlayWidget is None:
            return
        canvas = self.iface.mapCanvas()
        main_win = self.iface.mainWindow()
        margin = 10
        top_right = canvas.mapTo(main_win, QPoint(canvas.width(), 0))
        w = self._gridOverlayWidget.width()
        self._gridOverlayWidget.move(top_right.x() - w - margin, top_right.y() + 40)

    def eventFilter(self, obj, event):
        """Reposition the overlay when the main window is resized."""
        if obj is self.iface.mainWindow() and event.type() == QEvent.Type.Resize:
            self._repositionOverlay()
        return False

    def _gridLabel(self):
        if self._showGrid:
            return QCoreApplication.translate("QGISRedCreateLineTool", "Hide complementary grid")
        return QCoreApplication.translate("QGISRedCreateLineTool", "Show complementary grid")

    def _onGridToggled(self, checked):
        """Toggle grid on/off and persist the choice."""
        self._showGrid = checked
        QSettings().setValue("QGISRed/showComplementaryGrid", checked)
        if self._gridOverlayCb is not None:
            self._gridOverlayCb.setText(self._gridLabel())
            self._gridOverlayWidget.adjustSize()
            self._repositionOverlay()
        if checked:
            self._updateGrid()
            self.iface.mapCanvas().extentsChanged.connect(self._updateGrid)
        else:
            try:
                self.iface.mapCanvas().extentsChanged.disconnect(self._updateGrid)
            except Exception:
                pass
            self._clearGrid()

    """Events"""

    def canvasPressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.firstClicked:
                self.firstClicked = True
                point = self.toMapCoordinates(event.pos())
                if self.objectSnapped is not None:
                    if self.SNAP_TO_SEGMENTS:
                        self.firstSnapped = True
                    point = self.objectSnapped.point()
                elif self._showGrid and self._gridSpacing > 0:
                    point = self._snapToGrid(point)
                self.mousePoints.append(point)
                self.mousePoints.append(point)
            else:
                if self.SNAP_TO_SEGMENTS and self.objectSnapped is not None:
                    self.mousePoints.remove(self.mousePoints[-1])
                    point = self.objectSnapped.point()
                    self.mousePoints.append(point)
                self.mousePoints.append(self.mousePoints[-1])
            self.createRubberBand(self.mousePoints)

        if event.button() == Qt.MouseButton.RightButton:
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

    def canvasDoubleClickEvent(self, event):
        if not self.SNAP_TO_SEGMENTS:
            return
        if (self.objectSnapped is not None or self.firstSnapped) and len(self.mousePoints) > 2:
            self.mousePoints.remove(self.mousePoints[-1])
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
            elif self._showGrid and self._gridSpacing > 0:
                self.objectSnapped = None
                gridPt = self._snapToGrid(self.toMapCoordinates(event.pos()))
                self.startMarker.setCenter(gridPt)
                self.startMarker.show()
            else:
                self.objectSnapped = None
                self.startMarker.hide()
        # Mouse clicked
        else:
            if self.SNAP_TO_SEGMENTS:
                self.startMarker.hide()
            point = self.toMapCoordinates(event.pos())
            match = self.snapper.snapToMap(point)
            if match.isValid():
                self.objectSnapped = match
                self.endMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.endMarker.show()
                self.mousePoints[-1] = match.point()
            else:
                self.objectSnapped = None
                if self._showGrid and self._gridSpacing > 0:
                    point = self._snapToGrid(point)
                    self.endMarker.setCenter(point)
                    self.endMarker.show()
                else:
                    self.endMarker.hide()
                self.mousePoints[-1] = point
            self.createRubberBand(self.mousePoints)
