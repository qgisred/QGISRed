from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.core import QgsPointXY, QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsVector
from qgis.core import QgsVectorLayerEditUtils, QgsSnappingConfig, QgsTolerance
from ...compat import SNAP_TYPE_SEGMENT
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnappingUtils
try:
    from qgis.gui import Qgis
except:
    try:
        from qgis.core import Qgis # Compatibility with QGis 3.4x
    except:
        pass

from ..utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ..utils.qgisred_layer_utils import QGISRedLayerUtils


class QGISRedEditLinksGeometryTool(QgsMapTool):
    ownMainLayers = ["Pipes", "Valves", "Pumps", "ServiceConnections"]

    def __init__(self, button, iface, projectDirectory, netwName):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.ProjectDirectory = projectDirectory
        self.NetworkName = netwName
        self.toolbarButton = button

        self.snapper = None
        self.vertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.vertexMarker.setColor(QColor(255, 87, 51))
        self.vertexMarker.setIconSize(15)
        self.vertexMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.vertexMarker.setPenWidth(3)
        self.vertexMarker.hide()

        self.pipeSnapper = None
        self.pipeMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.pipeMarker.setColor(QColor(143, 0, 255))
        self.pipeMarker.setIconSize(10)
        try:
            self.pipeMarker.setIconType(QgsVertexMarker.ICON_DOUBLE_TRIANGLE)  # or ICON_CROSS, ICON_X
        except:
            self.pipeMarker.setIconType(QgsVertexMarker.ICON_X)  # or ICON_CROSS, ICON_X
        self.pipeMarker.setPenWidth(3)
        self.pipeMarker.hide()

        self.mouseClicked = False
        self.clickedPoint = None
        self.objectSnapped = None
        self.pipeSnapped = None
        self.selectedFeature = None
        self.selectedLayer = None
        self.newPositionVector = QgsVector(0, 0)
        self.rubberBand = None
        self.newVertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.newVertexMarker.setColor(QColor(55, 198, 5))
        self.newVertexMarker.setIconSize(15)
        self.newVertexMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.newVertexMarker.setPenWidth(3)
        self.newVertexMarker.hide()

        self.segmentRubberBand = None
        self.insertMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.insertMarker.setColor(QColor(55, 198, 5))
        self.insertMarker.setFillColor(QColor(55, 198, 5))
        self.insertMarker.setIconSize(14)
        self.insertMarker.setIconType(QgsVertexMarker.ICON_CROSS)
        self.insertMarker.setPenWidth(4)
        self.insertMarker.setZValue(100)
        self.insertMarker.hide()

        self.featureRubberBand = None
        self.vertexMarkers = []
        self.hoveredFeatureId = None
        self.hoveredLayerId = None
        self.hoveredVertexIdx = -1

    def activate(self):
        cursor = QCursor()
        cursor.setShape(Qt.CursorShape.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(SNAP_TYPE_SEGMENT)
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)  # All layers
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.snapper.setConfig(config)

        self.pipeSnapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.pipeSnapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(SNAP_TYPE_SEGMENT)
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)  # All layers
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.pipeSnapper.setConfig(config)

    def deactivate(self):
        self.newVertexMarker.hide()
        self.pipeMarker.hide()
        self._clearAllHighlights()
        self.toolbarButton.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    """Methods"""

    def getUniformedPath(self, path):
        return QGISRedFileSystemUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedFileSystemUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedFileSystemUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

    def areOverlapedPoints(self, point1, point2):
        tolerance = 0.1
        if point1.distance(point2) < tolerance:
            return True
        else:
            return False

    def isInPath(self, point1, point2, myPoint):
        width = point2.x() - point1.x()
        height = point2.y() - point1.y()
        widthM = myPoint.x() - point1.x()
        heightM = myPoint.y() - point1.y()
        if abs(width) >= abs(height):
            yEst = widthM * height / width + point1.y()
            if abs(yEst - myPoint.y()) < 1e-9:
                return True
        else:
            xEst = heightM * width / height + point1.x()
            if abs(xEst - myPoint.x()) < 1e-9:
                return True
        return False

    def _buildFeatureHighlight(self, feature):
        geom = feature.geometry()
        try:
            self.featureRubberBand = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Line)
        except Exception:
            self.featureRubberBand = QgsRubberBand(self.iface.mapCanvas(), False)
        self.featureRubberBand.setToGeometry(geom, None)
        self.featureRubberBand.setColor(QColor(255, 80, 80, 100))
        self.featureRubberBand.setWidth(5)

        for v in geom.vertices():
            m = QgsVertexMarker(self.iface.mapCanvas())
            m.setCenter(QgsPointXY(v.x(), v.y()))
            m.setColor(QColor(120, 120, 120))
            m.setFillColor(QColor(255, 255, 255, 200))
            m.setIconSize(7)
            m.setIconType(QgsVertexMarker.ICON_CIRCLE)
            m.setPenWidth(2)
            self.vertexMarkers.append(m)

    def _updateHoverHighlight(self, layer, feature, isVertex, vertexIdx, snapMatch):
        featureId = feature.id()
        layerId = layer.id()
        if featureId != self.hoveredFeatureId or layerId != self.hoveredLayerId:
            self._clearAllHighlights()
            self.hoveredFeatureId = featureId
            self.hoveredLayerId = layerId
            self._buildFeatureHighlight(feature)

        # Reset previously enlarged vertex
        if 0 <= self.hoveredVertexIdx < len(self.vertexMarkers):
            m = self.vertexMarkers[self.hoveredVertexIdx]
            m.setColor(QColor(120, 120, 120))
            m.setFillColor(QColor(255, 255, 255, 200))
            m.setIconSize(7)
            m.setPenWidth(2)
        self.hoveredVertexIdx = -1

        if isVertex:
            self._hideSegmentHighlight()
            if 0 <= vertexIdx < len(self.vertexMarkers):
                m = self.vertexMarkers[vertexIdx]
                m.setColor(QColor(255, 87, 51))
                m.setFillColor(QColor(255, 87, 51, 80))
                m.setIconSize(20)
                m.setPenWidth(3)
                self.hoveredVertexIdx = vertexIdx
            cursor = QCursor()
            cursor.setShape(Qt.CursorShape.SizeAllCursor)
            self.iface.mapCanvas().setCursor(cursor)
            self.iface.mainWindow().statusBar().showMessage(
                self.tr("QGISRed: Drag to move vertex · Right-click to delete")
            )
        else:
            self.iface.mainWindow().statusBar().clearMessage()
            self._showSegmentHighlight(feature, snapMatch)

    def _clearAllHighlights(self):
        if self.featureRubberBand is not None:
            self.iface.mapCanvas().scene().removeItem(self.featureRubberBand)
            self.featureRubberBand = None
        for m in self.vertexMarkers:
            self.iface.mapCanvas().scene().removeItem(m)
        self.vertexMarkers = []
        self.hoveredFeatureId = None
        self.hoveredLayerId = None
        self.hoveredVertexIdx = -1
        self._hideSegmentHighlight()
        self.iface.mainWindow().statusBar().clearMessage()
        cursor = QCursor()
        cursor.setShape(Qt.CursorShape.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def _showSegmentHighlight(self, feature, snapMatch):
        featureGeometry = feature.geometry()
        snapPoint = snapMatch.point()
        sp = QgsPointXY(snapPoint.x(), snapPoint.y())
        result = featureGeometry.closestSegmentWithContext(sp)
        afterVertex = result[2]
        if afterVertex <= 0:
            return
        p1 = featureGeometry.vertexAt(afterVertex - 1)
        p2 = featureGeometry.vertexAt(afterVertex)
        if p1.isEmpty() or p2.isEmpty():
            return
        if self.segmentRubberBand is not None:
            self.iface.mapCanvas().scene().removeItem(self.segmentRubberBand)
        try:
            self.segmentRubberBand = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Line)
        except Exception:
            self.segmentRubberBand = QgsRubberBand(self.iface.mapCanvas(), False)
        self.segmentRubberBand.setToGeometry(QgsGeometry.fromPolyline([p1, p2]), None)
        self.segmentRubberBand.setColor(QColor(220, 50, 50, 160))
        self.segmentRubberBand.setWidth(4)
        self.insertMarker.setCenter(sp)
        self.insertMarker.show()
        cursor = QCursor()
        cursor.setShape(Qt.CursorShape.PointingHandCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def _hideSegmentHighlight(self):
        if self.segmentRubberBand is not None:
            self.iface.mapCanvas().scene().removeItem(self.segmentRubberBand)
            self.segmentRubberBand = None
        self.insertMarker.hide()

    def createRubberBand(self, points):
        myPoints = points
        if isinstance(points[0], QgsPointXY):
            myPoints = []
            for p in points:
                myPoints.append(QgsPoint(p.x(), p.y()))
        try:  # From QGis 3.30
            self.rubberBand = QgsRubberBand(self.iface.mapCanvas(), Qgis.GeometryType.Line)
        except:
            self.rubberBand = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(myPoints), None)
        self.rubberBand.setColor(QColor(55, 198, 5))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.PenStyle.DashLine)
        self.newVertexMarker.setCenter(QgsPointXY(points[0].x(), points[0].y()))
        self.newVertexMarker.show()

    def updateRubberBand(self):
        newX = self.clickedPoint.x() + self.newPositionVector.x()
        newY = self.clickedPoint.y() + self.newPositionVector.y()
        self.rubberBand.movePoint(1, QgsPointXY(newX, newY))
        self.newVertexMarker.setCenter(QgsPointXY(newX, newY))

    def moveVertexLink(self, layer, feature, newPosition, vertexIndex):
        layer.startEditing()
        layer.beginEditCommand("Update link geometry")
        try:
            edit_utils = QgsVectorLayerEditUtils(layer)
            edit_utils.moveVertex(newPosition.x(), newPosition.y(), feature.id(), vertexIndex)
        except Exception as e:
            layer.destroyEditCommand()
            layer.rollBack()
            raise e
        layer.endEditCommand()
        layer.commitChanges()

    def deleteVertexLink(self, layer, feature, vertexIndex):
        layer.startEditing()
        layer.beginEditCommand("Update link geometry")
        try:
            edit_utils = QgsVectorLayerEditUtils(layer)
            edit_utils.deleteVertex(feature.id(), vertexIndex)
        except Exception as e:
            layer.destroyEditCommand()
            layer.rollBack()
            raise e
        layer.endEditCommand()
        layer.commitChanges()

    def insertVertexLink(self, layer, feature, newPoint):
        layer.startEditing()
        layer.beginEditCommand("Update link geometry")
        vertex = -1
        if layer.geometryType() == 1:  # Line
            featureGeometry = self.selectedFeature.geometry()
            if featureGeometry.isMultipart():
                parts = featureGeometry.get()
                for part in parts:  # only one part
                    for i in range(len(part) - 1):
                        if self.isInPath(
                            QgsPointXY(part[i].x(), part[i].y()), QgsPointXY(part[i + 1].x(), part[i + 1].y()), newPoint
                        ):
                            vertex = i + 1
        try:
            edit_utils = QgsVectorLayerEditUtils(layer)
            edit_utils.insertVertex(newPoint.x(), newPoint.y(), feature.id(), vertex)
        except Exception as e:
            layer.destroyEditCommand()
            layer.rollBack()
            raise e
        layer.endEditCommand()
        layer.commitChanges()

    """Events"""

    def canvasPressEvent(self, event):
        if self.objectSnapped is None:
            self.clickedPoint = None
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.mouseClicked = False
            self.clickedPoint = None

        if event.button() == Qt.MouseButton.LeftButton:
            self.clickedPoint = self.objectSnapped.point()
            if self.vertexIndex == -1:
                return
            self.mouseClicked = True
            self.createRubberBand([self.objectSnapped.point(), self.objectSnapped.point()])

    def canvasMoveEvent(self, event):
        mousePoint = self.toMapCoordinates(event.pos())
        # Mouse not clicked
        if not self.mouseClicked:
            self.pipeSnappedOn = False
            matchSnapper = self.snapper.snapToMap(mousePoint)
            if matchSnapper.isValid():
                valid = False
                layer = matchSnapper.layer()
                snapLayerPath = self.getLayerPath(layer)
                for name in self.ownMainLayers:
                    layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp")
                    if snapLayerPath == layerPath:
                        valid = True
                if valid:
                    self.objectSnapped = matchSnapper
                    self.selectedLayer = layer

                    vertex = matchSnapper.point()
                    featureId = matchSnapper.featureId()
                    request = QgsFeatureRequest().setFilterFid(featureId)
                    nodes = list(layer.getFeatures(request))
                    self.selectedFeature = QgsFeature(nodes[0])
                    # #Ver aquí si es el nudo inicial y final
                    middleNode = False
                    self.vertexIndex = -1
                    if layer.geometryType() == 1:  # Line
                        featureGeometry = self.selectedFeature.geometry()
                        if featureGeometry.isMultipart():
                            parts = featureGeometry.get()
                            for part in parts:  # only one part
                                if middleNode:
                                    break
                                i = -1
                                for v in part:
                                    i = i + 1
                                    if (i == 0 or i == len(part) - 1) and "ServiceConnections" not in snapLayerPath:
                                        continue

                                    matchedPoint = QgsPointXY(vertex.x(), vertex.y())
                                    if self.areOverlapedPoints(
                                        QgsGeometry.fromPointXY(matchedPoint), QgsGeometry.fromPointXY(QgsPointXY(v.x(), v.y()))
                                    ):
                                        middleNode = True
                                        self.vertexIndex = i
                                        if (i == 0 or i == len(part) - 1) and "ServiceConnections" in snapLayerPath:
                                            self.pipeSnappedOn = True
                                        break
                    self._updateHoverHighlight(layer, self.selectedFeature, middleNode, self.vertexIndex, self.objectSnapped)
                else:
                    self.objectSnapped = None
                    self.selectedFeature = None
                    self.selectedLayer = None
                    self._clearAllHighlights()
            else:
                self.objectSnapped = None
                self.selectedFeature = None
                self.selectedLayer = None
                self._clearAllHighlights()
        # Mouse clicked
        else:
            # Snap pipe layer
            if self.pipeSnappedOn:
                matchSnapper = self.pipeSnapper.snapToMap(mousePoint)
                if matchSnapper.isValid():
                    valid = False
                    layer = matchSnapper.layer()
                    snapLayerPath = self.getLayerPath(layer)
                    for name in self.ownMainLayers:
                        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")
                        if snapLayerPath == layerPath:
                            valid = True
                    if valid:
                        self.pipeSnapped = matchSnapper
                        self.pipeMarker.setCenter(matchSnapper.point())
                        self.pipeMarker.show()
                    else:
                        self.pipeMarker.hide()
                else:
                    self.pipeMarker.hide()
                    self.pipeSnapped = None

            # # Update rubber band
            if self.objectSnapped is not None and self.rubberBand is not None:
                snappedPoint = self.objectSnapped.point()
                self.newPositionVector = QgsVector(mousePoint.x() - snappedPoint.x(), mousePoint.y() - snappedPoint.y())
                self.updateRubberBand()

    def canvasReleaseEvent(self, event):
        insertedPoint = None
        if self.mouseClicked:
            if event.button() == 1:
                mousePoint = self.toMapCoordinates(event.pos())
                if self.pipeSnapped is not None:
                    mousePoint = self.pipeSnapped.point()
                self.mouseClicked = False
                if self.objectSnapped is not None:
                    self.moveVertexLink(self.selectedLayer, self.selectedFeature, mousePoint, self.vertexIndex)
        elif event.button() == 2:
            if self.objectSnapped is not None:
                self.deleteVertexLink(self.selectedLayer, self.selectedFeature, self.vertexIndex)
        elif event.button() == 1:
            if self.objectSnapped is not None:
                insertedPoint = self.objectSnapped.point()
                self.insertVertexLink(self.selectedLayer, self.selectedFeature, insertedPoint)
        self.objectSnapped = None
        self.pipeSnapped = None
        self.selectedFeature = None
        self.selectedLayer = None
        self.vertexIndex = -1
        self.iface.mapCanvas().refresh()
        # Remove vertex marker and rubber band
        self.iface.mapCanvas().scene().removeItem(self.rubberBand)
        self.newVertexMarker.hide()
        self.pipeMarker.hide()
        self._clearAllHighlights()