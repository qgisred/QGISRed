from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QColor
from qgis.core import QgsPointXY, QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsVector
from qgis.core import QgsVectorLayerEditUtils, QgsSnappingConfig
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnappingUtils
from ..tools.qgisred_utils import QGISRedUtils


class QGISRedEditConnectionsTool(QgsMapTool):
    ownMainLayers = ["ServiceConnections"]

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

    def activate(self):
        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        myLayers = []
        # Editing
        layers = self.getLayers()
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            for name in self.ownMainLayers:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp")
                if openedLayerPath == layerPath:
                    myLayers.append(layer)
                    if not layer.isEditable():
                        layer.startEditing()
        # Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(2)  # Vertex
        config.setMode(2)  # All layers
        config.setTolerance(10)
        config.setUnits(1)  # Pixels
        config.setEnabled(True)
        self.snapper.setConfig(config)

        self.pipeSnapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.pipeSnapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(2)  # Vertex
        config.setMode(2)  # All layers
        config.setTolerance(10)
        config.setUnits(1)  # Pixels
        config.setEnabled(True)
        self.pipeSnapper.setConfig(config)

    def deactivate(self):
        self.toolbarButton.setChecked(False)
        # End Editing
        layers = self.getLayers()
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            for name in self.ownMainLayers:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp")
                if openedLayerPath == layerPath:
                    if layer.isModified():
                        layer.commitChanges()
                    else:
                        layer.rollBack()

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    """Methods"""
    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedUtils().getLayers()

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
            if abs(yEst - myPoint.y()) < 1E-9:
                return True
        else:
            xEst = heightM * width / height + point1.x()
            if abs(xEst - myPoint.x()) < 1E-9:
                return True
        return False

    def createRubberBand(self, points):
        myPoints = points
        if isinstance(points[0], QgsPointXY):
            myPoints = []
            for p in points:
                myPoints.append(QgsPoint(p.x(), p.y()))
        self.rubberBand = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(myPoints), None)
        self.rubberBand.setColor(QColor(55, 198, 5))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.DashLine)
        self.newVertexMarker.setCenter(
            QgsPointXY(points[0].x(), points[0].y()))
        self.newVertexMarker.show()

    def updateRubberBand(self):
        newX = self.clickedPoint.x() + self.newPositionVector.x()
        newY = self.clickedPoint.y() + self.newPositionVector.y()
        self.rubberBand.movePoint(1, QgsPointXY(newX, newY))
        self.newVertexMarker.setCenter(QgsPointXY(newX, newY))

    def moveVertexLink(self, layer, feature, newPosition, vertexIndex):
        if layer.isEditable():
            layer.beginEditCommand("Update link geometry")
            try:
                edit_utils = QgsVectorLayerEditUtils(layer)
                edit_utils.moveVertex(newPosition.x(), newPosition.y(), feature.id(), vertexIndex)
            except Exception as e:
                layer.destroyEditCommand()
                raise e
            layer.endEditCommand()

    def deleteVertexLink(self, layer, feature, vertexIndex):
        if layer.isEditable():
            layer.beginEditCommand("Update link geometry")
            try:
                edit_utils = QgsVectorLayerEditUtils(layer)
                edit_utils.deleteVertex(feature.id(), vertexIndex)
            except Exception as e:
                layer.destroyEditCommand()
                raise e
            layer.endEditCommand()

    def insertVertexLink(self, layer, feature, newPoint):
        if layer.isEditable():
            layer.beginEditCommand("Update link geometry")
            vertex = -1
            if layer.geometryType() == 1:  # Line
                featureGeometry = self.selectedFeature.geometry()
                if featureGeometry.isMultipart():
                    parts = featureGeometry.get()
                    for part in parts:  # only one part
                        for i in range(len(part)-1):
                            if self.isInPath(QgsPointXY(part[i].x(), part[i].y()),
                                             QgsPointXY(part[i+1].x(), part[i+1].y()), newPoint):
                                vertex = i+1
            try:
                edit_utils = QgsVectorLayerEditUtils(layer)
                edit_utils.insertVertex(
                    newPoint.x(), newPoint.y(), feature.id(), vertex)
            except Exception as e:
                layer.destroyEditCommand()
                raise e
            layer.endEditCommand()

    """Events"""
    def canvasPressEvent(self, event):
        if self.objectSnapped is None:
            self.clickedPoint = None
            return

        if event.button() == Qt.RightButton:
            self.mouseClicked = False
            self.clickedPoint = None

        if event.button() == Qt.LeftButton:
            self.clickedPoint = self.objectSnapped.point()
            if self.vertexIndex == -1:
                return
            self.mouseClicked = True
            self.createRubberBand([self.objectSnapped.point(), self.objectSnapped.point()])

    def canvasMoveEvent(self, event):
        mousePoint = self.toMapCoordinates(event.pos())
        # Mouse not clicked
        if not self.mouseClicked:
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
                                    i = i+1
                                    # if i == 0 or i == len(part)-1:
                                    #     continue
                                    matchedPoint = QgsPointXY(vertex.x(), vertex.y())
                                    if self.areOverlapedPoints(QgsGeometry.fromPointXY(matchedPoint),
                                                               QgsGeometry.fromPointXY(QgsPointXY(v.x(), v.y()))):
                                        middleNode = True
                                        self.vertexIndex = i
                                        break
                    if middleNode:
                        self.vertexMarker.setCenter(QgsPointXY(vertex.x(), vertex.y()))
                        self.vertexMarker.show()
                    else:
                        self.vertexMarker.hide()
                else:
                    self.objectSnapped = None
                    self.selectedFeature = None
                    self.selectedLayer = None
                    self.vertexMarker.hide()
            else:
                self.objectSnapped = None
                self.selectedFeature = None
                self.selectedLayer = None
                self.vertexMarker.hide()
        # Mouse clicked
        else:
            # Snap pipe layer
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
        if self.mouseClicked:
            if event.button() == 1:
                mousePoint = self.toMapCoordinates(event.pos())
                if (self.pipeSnapped is not None):
                    mousePoint = self.pipeSnapped.point()
                self.mouseClicked = False
                if self.objectSnapped is not None:
                    self.moveVertexLink(self.selectedLayer, self.selectedFeature, mousePoint, self.vertexIndex)
        elif event.button() == 2:
            if self.objectSnapped is not None:
                self.deleteVertexLink(self.selectedLayer, self.selectedFeature, self.vertexIndex)
        elif event.button() == 1:
            if self.objectSnapped is not None:
                self.insertVertexLink(self.selectedLayer, self.selectedFeature, self.objectSnapped.point())
        self.objectSnapped = None
        self.pipeSnapped = None
        self.selectedFeature = None
        self.selectedLayer = None
        self.vertexIndex = -1
        self.iface.mapCanvas().refresh()
        # Remove vertex marker and rubber band
        self.vertexMarker.hide()
        self.iface.mapCanvas().scene().removeItem(self.rubberBand)
        self.newVertexMarker.hide()
        self.pipeMarker.hide()
