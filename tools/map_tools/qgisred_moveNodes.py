from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QColor
from qgis.core import QgsPointXY, QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsVector
from qgis.core import QgsVectorLayerEditUtils, QgsSnappingConfig, QgsTolerance
from ...compat import SNAP_TYPE_VERTEX
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


class QGISRedMoveNodesTool(QgsMapTool):
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs", "Demands", "Sources"]
    myNodeLayers = ["Junctions", "Tanks", "Reservoirs", "Demands", "Sources"]

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
        self.mousePoint = None

        self.mouseClicked = False
        self.clickedPoint = None
        self.objectSnapped = None
        self.selectedNodeFeature = None
        self.selectedNodeLayer = None
        self.adjacentFeatures = None
        self.newPositionVector = QgsVector(0, 0)
        self.rubberBand = None
        self.newVertexMarker = QgsVertexMarker(self.iface.mapCanvas())
        self.newVertexMarker.setColor(QColor(55, 198, 5))
        self.newVertexMarker.setIconSize(15)
        self.newVertexMarker.setIconType(QgsVertexMarker.ICON_BOX)  # or ICON_CROSS, ICON_X
        self.newVertexMarker.setPenWidth(3)
        self.newVertexMarker.hide()

    def activate(self):
        cursor = QCursor()
        cursor.setShape(Qt.CursorShape.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        self._connectedEditLayers = []
        for layer in self.getLayers():
            if layer.customProperty("qgisred_identifier"):
                layer.editingStarted.connect(self._deactivateDueToEdit)
                self._connectedEditLayers.append(layer)

        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(SNAP_TYPE_VERTEX)
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)  # All layers
        config.setTolerance(1)
        config.setUnits(QgsTolerance.UnitType.ProjectUnits)
        config.setEnabled(True)
        self.snapper.setConfig(config)

    def deactivate(self):
        self.vertexMarker.hide()
        self.newVertexMarker.hide()
        self.toolbarButton.setChecked(False)
        for layer in getattr(self, "_connectedEditLayers", []):
            try:
                layer.editingStarted.disconnect(self._deactivateDueToEdit)
            except Exception:
                pass
        self._connectedEditLayers = []

    def _deactivateDueToEdit(self):
        self.iface.mapCanvas().unsetMapTool(self)

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

    def findAdjacentElements(self, nodeGeometry):
        adjacentElements = {}
        layers = self.getLayers()
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            for name in self.ownMainLayers:
                layePath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp")
                if openedLayerPath == layePath:
                    adjacentFeatures = []
                    for feature in layer.getFeatures():
                        featureGeometry = feature.geometry()
                        if layer.geometryType() == 0:  # Point
                            if self.areOverlapedPoints(nodeGeometry, featureGeometry):
                                adjacentFeatures.append(feature)
                        elif layer.geometryType() == 1:
                            if featureGeometry.isMultipart():
                                for part in featureGeometry.get():  # only one part
                                    first_vertex = part[0]
                                    last_vertex = part[-1]
                            else:
                                first_vertex = featureGeometry.get()[0]
                                last_vertex = featureGeometry.get()[-1]

                            firsVertex = QgsGeometry.fromPointXY(QgsPointXY(first_vertex.x(), first_vertex.y()))
                            lastVertex = QgsGeometry.fromPointXY(QgsPointXY(last_vertex.x(), last_vertex.y()))
                            if self.areOverlapedPoints(nodeGeometry, firsVertex) or self.areOverlapedPoints(
                                nodeGeometry, lastVertex
                            ):
                                adjacentFeatures.append(feature)
                    if len(adjacentFeatures) > 0:
                        adjacentElements[layer] = adjacentFeatures

        return adjacentElements

    def areOverlapedPoints(self, point1, point2):
        tolerance = 0.1
        if point1.distance(point2) < tolerance:
            return True
        else:
            return False

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

    def moveNodePoint(self, layer, nodeFeature, newPosition):
        layer.startEditing()
        layer.beginEditCommand("Move node")
        try:
            edit_utils = QgsVectorLayerEditUtils(layer)
            edit_utils.moveVertex(newPosition.x(), newPosition.y(), nodeFeature.id(), 0)
        except Exception as e:
            layer.destroyEditCommand()
            layer.rollBack()
            raise e
        layer.endEditCommand()
        layer.commitChanges()

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

    """Events"""

    def canvasPressEvent(self, event):
        if self.objectSnapped is None:
            self.clickedPoint = None
            return

        if event.button() == Qt.MouseButton.RightButton:
            self.mouseClicked = False
            self.clickedPoint = None

        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseClicked = True
            self.clickedPoint = self.objectSnapped.point()

            self.selectedNodeFeature = None
            self.adjacentFeatures = None

            foundNode = False
            layers = self.getLayers()
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                for name in self.myNodeLayers:
                    layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp")
                    if openedLayerPath == layerPath:
                        locatedPoint = self.snapper.locatorForLayer(layer)
                        match = locatedPoint.nearestVertex(self.objectSnapped.point(), 1)
                        if match.isValid():
                            featureId = match.featureId()
                            request = QgsFeatureRequest().setFilterFid(featureId)
                            node = list(layer.getFeatures(request))
                            self.selectedNodeLayer = layer
                            foundNode = True

            if not foundNode:
                return

            self.selectedNodeFeature = QgsFeature(node[0])
            self.adjacentFeatures = self.findAdjacentElements(self.selectedNodeFeature.geometry())
            self.createRubberBand([self.objectSnapped.point(), self.objectSnapped.point()])

    def canvasMoveEvent(self, event):
        self.mousePoint = self.toMapCoordinates(event.pos())
        # Mouse not clicked
        if not self.mouseClicked:
            match = self.snapper.snapToMap(self.mousePoint)
            if match.isValid():
                self.objectSnapped = match
                vertex = match.point()
                self.vertexMarker.setCenter(QgsPointXY(vertex.x(), vertex.y()))
                self.vertexMarker.show()
                cursor = QCursor()
                cursor.setShape(Qt.CursorShape.SizeAllCursor)
                self.iface.mapCanvas().setCursor(cursor)
            else:
                self.objectSnapped = None
                self.selectedNodeFeature = None
                self.vertexMarker.hide()
                cursor = QCursor()
                cursor.setShape(Qt.CursorShape.ArrowCursor)
                self.iface.mapCanvas().setCursor(cursor)
        # Mouse clicked
        else:
            # Update rubber band
            if self.objectSnapped is not None and self.rubberBand is not None:
                snappedPoint = self.objectSnapped.point()
                self.newPositionVector = QgsVector(self.mousePoint.x() - snappedPoint.x(), self.mousePoint.y() - snappedPoint.y())
                self.updateRubberBand()

    def canvasReleaseEvent(self, event):
        mousePoint = self.toMapCoordinates(event.pos())
        if not self.mouseClicked:
            return

        if event.button() == 1:
            self.mouseClicked = False

            if self.objectSnapped is not None:
                if self.selectedNodeFeature is not None:
                    for adjLayer in self.adjacentFeatures:
                        for feature in self.adjacentFeatures[adjLayer]:
                            if adjLayer.geometryType() == 0:  # Point
                                self.moveNodePoint(adjLayer, feature, mousePoint)
                            else:
                                nodeGeometry = self.selectedNodeFeature.geometry()
                                featureGeometry = feature.geometry()

                                if featureGeometry.isMultipart():
                                    for part in featureGeometry.get():  # only one part
                                        firstVertex = part[0]
                                        vertices = len(part)
                                else:
                                    firstVertex = featureGeometry.get()[0]
                                    vertices = 2
                                firstPoint = QgsGeometry.fromPointXY(QgsPointXY(firstVertex.x(), firstVertex.y()))
                                if self.areOverlapedPoints(nodeGeometry, firstPoint):
                                    index = 0
                                else:
                                    index = vertices - 1
                                self.moveVertexLink(adjLayer, feature, mousePoint, index)
                self.objectSnapped = None
                self.selectedNodeFeature = None
                self.iface.mapCanvas().refresh()

            # Remove vertex marker and rubber band
            self.vertexMarker.hide()
            self.iface.mapCanvas().scene().removeItem(self.rubberBand)
            self.newVertexMarker.hide()