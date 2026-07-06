# -*- coding: utf-8 -*-
"""Utility helper methods for QGISRed."""

from qgis.core import QgsCoordinateTransform, QgsProject, QgsRectangle
from qgis.PyQt.QtGui import QCursor
from ctypes import windll

from ..tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_ui_utils import QGISRedUIUtils


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

    def getTolerance(self):
        LOGPIXELSX = 88
        user32 = windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        pix_per_inch = windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
        user32.ReleaseDC(0, dc)

        unitsPerPixel = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel()
        un = 25.4 / pix_per_inch
        return 1 * unitsPerPixel / un

    def getUniformedPath(self, path):
        return QGISRedFileSystemUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedFileSystemUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedFileSystemUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

    def _normalizeLayerName(self, layerName):
        return layerName.lower().replace(" ", "")

    def _getQgisRedIdentifierFromLayerName(self, layerName):
        mapping = {
            "pipe": "qgisred_pipes",
            "pipes": "qgisred_pipes",
            "junction": "qgisred_junctions",
            "junctions": "qgisred_junctions",
            "demand": "qgisred_demands",
            "demands": "qgisred_demands",
            "reservoir": "qgisred_reservoirs",
            "reservoirs": "qgisred_reservoirs",
            "tank": "qgisred_tanks",
            "tanks": "qgisred_tanks",
            "pump": "qgisred_pumps",
            "pumps": "qgisred_pumps",
            "valve": "qgisred_valves",
            "valves": "qgisred_valves",
            "source": "qgisred_sources",
            "sources": "qgisred_sources",
            "serviceconnection": "qgisred_serviceconnections",
            "serviceconnections": "qgisred_serviceconnections",
            "isolationvalve": "qgisred_isolationvalves",
            "isolationvalves": "qgisred_isolationvalves",
            "meter": "qgisred_meters",
            "meters": "qgisred_meters",
        }

        normalizedName = self._normalizeLayerName(layerName)
        return mapping.get(normalizedName, f"qgisred_{normalizedName}")

    def _getIdFieldName(self, layerName, layer):
        idFieldsByLayer = {
            "junction": "JunctionID",
            "junctions": "JunctionID",
            "tank": "TankID",
            "tanks": "TankID",
            "pump": "PumpID",
            "pumps": "PumpID",
            "valve": "ValveID",
            "valves": "ValveID",
            "reservoir": "ReservoirID",
            "reservoirs": "ReservoirID",
            "pipe": "PipeID",
            "pipes": "PipeID",
            "source": "SourceID",
            "sources": "SourceID",
            "demand": "DemandID",
            "demands": "DemandID",
            "serviceconnection": "ServiceConnectionID",
            "serviceconnections": "ServiceConnectionID",
            "isolationvalve": "IsolationValveID",
            "isolationvalves": "IsolationValveID",
            "meter": "MeterID",
            "meters": "MeterID",
        }

        fields = layer.fields()
        normalizedName = self._normalizeLayerName(layerName)
        expectedField = idFieldsByLayer.get(normalizedName)

        if expectedField is not None and fields.indexFromName(expectedField) != -1:
            return expectedField

        for candidate in ("Id", "ID", "id"):
            if fields.indexFromName(candidate) != -1:
                return candidate

        if len(fields) > 0:
            firstField = fields[0].name()
            if firstField.lower() == "id":
                return firstField

        return None

    def getSelectedFeaturesIds(self):
        linkIdsList = []
        nodeIdsList = []
        self.selectedFids = {}
        self.selectedIds = {}

        layers = self.getLayers()

        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)

            for layerName in self.ownMainLayers:
                layerPath = self.generatePath(
                    self.ProjectDirectory,
                    self.NetworkName + "_" + layerName + ".shp"
                )

                if layerName == "Sources" or layerName == "Demands":
                    continue

                if openedLayerPath == layerPath:
                    idFieldName = self._getIdFieldName(layerName, layer)

                    if idFieldName is None:
                        continue

                    fids = []
                    ids = []

                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())

                        id = str(feature[idFieldName])

                        if id == "NULL":
                            self.selectedFids = {}
                            return False

                        ids.append(id)

                        if layer.geometryType() == 0:
                            nodeIdsList.append(id)
                        else:
                            linkIdsList.append(id)

                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids

                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)

            for layerName in self.complementaryLayers:
                layerPath = self.generatePath(
                    self.ProjectDirectory,
                    self.NetworkName + "_" + layerName + ".shp"
                )

                if openedLayerPath == layerPath:
                    idFieldName = self._getIdFieldName(layerName, layer)

                    if idFieldName is None:
                        continue

                    fids = []
                    ids = []

                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())

                        id = str(feature[idFieldName])

                        if id == "NULL":
                            self.selectedFids = {}
                            return False

                        ids.append(id)

                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids

                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ";"

        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ";"

        return True

    def setSelectedFeaturesById(self):
        layers = self.getLayers()

        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)

            for layerName in self.ownMainLayers:
                layerPath = self.generatePath(
                    self.ProjectDirectory,
                    self.NetworkName + "_" + layerName + ".shp"
                )

                if layerName == "Sources" or layerName == "Demands":
                    continue

                if openedLayerPath == layerPath:
                    if layerName in self.selectedFids:
                        layer.selectByIds(self.selectedFids[layerName])

    def zoomToElementFromProperties(self, layerName, elementId):
        layers = self.getLayers()
        layer = None

        target_id = self._getQgisRedIdentifierFromLayerName(layerName)

        for la in layers:
            if la.customProperty("qgisred_identifier") == target_id:
                layer = la
                break

        if layer:
            idFieldName = self._getIdFieldName(layerName, layer)

            if idFieldName is None:
                return

            safeElementId = str(elementId).replace("'", "''")
            features = layer.getFeatures(f'"{idFieldName}" = \'{safeElementId}\'')

            for feat in features:
                layer.selectByIds([feat.id()])

                geom = feat.geometry()
                if geom.isNull():
                    continue

                box = geom.boundingBox()

                canvas_extent = self.iface.mapCanvas().extent()
                buffer = max(canvas_extent.width(), canvas_extent.height()) * 0.10

                if box.width() == 0 or box.height() == 0:
                    center = box.center()
                    box = QgsRectangle(
                        center.x() - buffer,
                        center.y() - buffer,
                        center.x() + buffer,
                        center.y() + buffer
                    )
                else:
                    box.grow(buffer * 0.15)

                self.iface.mapCanvas().setExtent(box)
                self.iface.mapCanvas().refresh()
                return

    def transformPoint(self, point):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        pipesCrs = utils.getProjectCrs()
        projectCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        xform = QgsCoordinateTransform(projectCrs, pipesCrs, QgsProject.instance())
        return xform.transform(point)

    def pushMessage(self, text, level=0, duration=5):
        """
        Standardized pushMessage for QGISRed plugin.
        Delegates to the project-wide utility.
        """
        QGISRedUIUtils.showGlobalMessage(self.iface, text, level=level, duration=duration)
