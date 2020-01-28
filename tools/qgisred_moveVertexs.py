from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor, QColor
from qgis.core import QgsPointXY, QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsTolerance, QgsVector, QgsVertexId, QgsPointLocator,\
    QgsSnappingUtils, QgsVectorLayerEditUtils, QgsSnappingConfig #QgsSnapper
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMessageBar, QgsMapCanvasSnappingUtils

import os

class QGISRedMoveVertexsTool(QgsMapTool):
    ownMainLayers = ["Pipes", "Valves", "Pumps"]
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
        
        self.mouseClicked = False
        self.clickedPoint = None
        self.objectSnapped = None
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
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            for name in self.ownMainLayers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp").replace("/","\\"):
                    myLayers.append(layer)
                    if not layer.isEditable():
                        layer.startEditing()
        #Snapping
        self.snapper = QgsMapCanvasSnappingUtils(self.iface.mapCanvas())
        self.snapper.setMapSettings(self.iface.mapCanvas().mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(1) #Vertex
        config.setMode(2) #All layers
        config.setTolerance(2)
        config.setUnits(2) #Pixels
        config.setEnabled(True)
        self.snapper.setConfig(config)

    def deactivate(self):
        self.toolbarButton.setChecked(False)
        #End Editing
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            for name in self.ownMainLayers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp").replace("/","\\"):
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
                myPoints.append(QgsPoint(p.x(),p.y()))
        self.rubberBand = QgsRubberBand(self.iface.mapCanvas(), False)
        self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(myPoints), None)
        self.rubberBand.setColor(QColor(55, 198, 5))
        self.rubberBand.setWidth(1)
        self.rubberBand.setLineStyle(Qt.DashLine)
        self.newVertexMarker.setCenter(QgsPointXY(points[0].x(), points[0].y()))
        self.newVertexMarker.show()

    def updateRubberBand(self):
        self.rubberBand.movePoint(1, QgsPointXY(self.clickedPoint.x() + self.newPositionVector.x(), self.clickedPoint.y() + self.newPositionVector.y()))
        self.newVertexMarker.setCenter(QgsPointXY(self.clickedPoint.x() + self.newPositionVector.x(), self.clickedPoint.y() + self.newPositionVector.y()))

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

    def canvasPressEvent(self, event):
        if self.objectSnapped is None:
            self.clickedPoint = None
            return
        
        if event.button() == Qt.RightButton:
            self.mouseClicked = False
            self.clickedPoint = None
        
        if event.button() == Qt.LeftButton:
            self.mouseClicked = True
            self.clickedPoint = self.objectSnapped.point()
            
            if self.selectedFeature is None: 
                return
            self.createRubberBand([self.objectSnapped.point(), self.objectSnapped.point()])

    def canvasMoveEvent(self, event):
        mousePoint = self.toMapCoordinates(event.pos())
        # Mouse not clicked
        if not self.mouseClicked:
            matchSnapper = self.snapper.snapToMap(mousePoint)
            if matchSnapper.isValid():
                valid= False
                layer = matchSnapper.layer()
                for name in self.ownMainLayers:
                    if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ".shp").replace("/","\\"):
                        valid = True
                if valid:
                    vertex = matchSnapper.point()
                    featureId = matchSnapper.featureId()
                    request = QgsFeatureRequest().setFilterFid(featureId)
                    nodes = list(layer.getFeatures(request))
                    self.selectedFeature = QgsFeature(nodes[0])
                    # #Ver aquí si es el nudo inicial y final
                    middleNode = False
                    self.vertexIndex=-1
                    if layer.geometryType()==1: #Line
                        featureGeometry= self.selectedFeature.geometry()
                        if featureGeometry.isMultipart():
                            parts = featureGeometry.get()
                            for part in parts: #only one part
                                if middleNode:
                                    break
                                i=-1
                                for v in part:
                                    i=i+1
                                    if i==0 or i==len(part)-1:
                                        continue
                                    matchedPoint = QgsPointXY(vertex.x(),vertex.y())
                                    if self.areOverlapedPoints(QgsGeometry.fromPointXY(matchedPoint), QgsGeometry.fromPointXY(QgsPointXY(v.x(),v.y()))):
                                        middleNode = True
                                        self.vertexIndex=i
                                        break
                    if middleNode:
                        self.objectSnapped = matchSnapper
                        self.selectedLayer = layer
                        self.vertexMarker.setCenter(QgsPointXY(vertex.x(), vertex.y()))
                        self.vertexMarker.show()
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
            else:
                self.objectSnapped = None
                self.selectedFeature = None
                self.selectedLayer = None
                self.vertexMarker.hide()
        # Mouse clicked
        else:
            # # Update rubber band
            if self.objectSnapped is not None and self.rubberBand is not None:
                snappedPoint = self.objectSnapped.point()
                self.newPositionVector = QgsVector(mousePoint.x() - snappedPoint.x(), mousePoint.y() - snappedPoint.y())
                self.updateRubberBand()

    def canvasReleaseEvent(self, event):
        mousePoint = self.toMapCoordinates(event.pos())
        if not self.mouseClicked:
            return
        
        if event.button() == 1:
            self.mouseClicked = False
            if self.objectSnapped is not None:
                self.moveVertexLink(self.selectedLayer,self.selectedFeature,mousePoint, self.vertexIndex)
                self.objectSnapped = None
                self.selectedFeature= None
                self.selectedLayer = None
                self.vertexIndex=-1
                self.iface.mapCanvas().refresh()
            # Remove vertex marker and rubber band
            self.vertexMarker.hide()
            self.iface.mapCanvas().scene().removeItem(self.rubberBand)
            self.newVertexMarker.hide()