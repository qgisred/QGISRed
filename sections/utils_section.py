# -*- coding: utf-8 -*-
"""Utility helper methods for QGISRed."""

from qgis.core import QgsCoordinateTransform, QgsProject
from PyQt5.QtGui import QCursor
from ctypes import windll

from ..tools.qgisred_utils import QGISRedUtils


class UtilsSection:
    """Pure helper methods: cursor, extent, tolerance, paths, feature selection, coordinate transform."""

    def setCursor(self, shape):
        cursor = QCursor()
        cursor.setShape(shape)
        self.iface.mapCanvas().setCursor(cursor)

    def setExtent(self):
        if self.zoomToFullExtent:
            self.iface.mapCanvas().zoomToFullExtent()
            self.iface.mapCanvas().refresh()
            self.zoomToFullExtent = False
        else:
            if self.extent is not None:
                self.iface.mapCanvas().setExtent(self.extent)
                self.iface.mapCanvas().refresh()
                self.extent = None

    def getTolerance(self):
        # DPI
        LOGPIXELSX = 88
        user32 = windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        pix_per_inch = windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
        user32.ReleaseDC(0, dc)

        # CanvasPixels
        unitsPerPixel = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel()
        # x WidthPixels --> m/px * px = metros
        # 25.4 mm == inch
        un = 25.4 / pix_per_inch  # x WidthPixels -- > mm/px x px = mm
        # 1mm * unitsPerPixel / un -->tolerance
        tolerance = 1 * unitsPerPixel / un
        return tolerance

    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedUtils().getLayers()

    def getSelectedFeaturesIds(self):
        linkIdsList = []
        nodeIdsList = []
        self.selectedFids = {}
        self.selectedIds = {}

        layers = self.getLayers()
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if layerName == "Sources" or layerName == "Demands": #TODO
                    continue
                if self.getLayerPath(layer) == layerPath:
                    fids = []
                    ids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        id = str(feature["Id"])
                        if id == "NULL":
                            message = self.tr("Some Ids are not defined. Commit before and try again.")
                            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                            self.selectedFids = {}
                            return False
                        if layer.geometryType() == 0:
                            ids.append(id)
                            nodeIdsList.append(id)
                        else:
                            ids.append(id)
                            linkIdsList.append(id)
                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids
                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        mylayersNames = self.complementaryLayers
        for layer in layers:
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if self.getLayerPath(layer) == layerPath:
                    fids = []
                    ids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        id = str(feature["Id"])
                        if id == "NULL":
                            message = self.tr("Some Ids are not defined. Commit before and try again.")
                            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                            self.selectedFids = {}
                            return False
                        ids.append(id)
                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids
                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        # Generate concatenate string for links and nodes
        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ";"
        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ";"
        return True

    def setSelectedFeaturesById(self):
        layers = self.getLayers()
        mylayersNames = self.ownMainLayers
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if layerName == "Sources" or layerName == "Demands":
                    continue
                if openedLayerPath == layerPath:
                    if layerName in self.selectedFids:
                        layer.selectByIds(self.selectedFids[layerName])

    def zoomToElementFromProperties(self, layerName, elementId):
        layers = self.getLayers()
        layer = None

        layer_identifier = f"qgisred_{layerName.lower()}"

        for la in layers:
            if la.customProperty("qgisred_identifier") == layer_identifier:
                layer = la
                break

        if layer:
            features = layer.getFeatures('"Id"=\'' + elementId + "'")
            for feat in features:
                box = feat.geometry().boundingBox()
                self.iface.mapCanvas().setExtent(box)
                self.iface.mapCanvas().refresh()
                return

    def transformPoint(self, point):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        pipesCrs = utils.getProjectCrs()
        projectCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        xform = QgsCoordinateTransform(projectCrs, pipesCrs, QgsProject.instance())
        return xform.transform(point)
