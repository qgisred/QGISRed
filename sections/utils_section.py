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
        elif self.savedExtent is not None:
            self.iface.mapCanvas().setExtent(self.savedExtent)
            self.iface.mapCanvas().refresh()
            self.savedExtent = None

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
        return QGISRedFileSystemUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedFileSystemUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedFileSystemUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

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
                            self.pushMessage(message, level=1, duration=5)
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
                            self.pushMessage(message, level=1, duration=5)
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

        # Robust identifier resolution (handling singular/plural and spaces)
        mapping = {
            'pipe': 'qgisred_pipes',
            'junction': 'qgisred_junctions',
            'demand': 'qgisred_demands',
            'reservoir': 'qgisred_reservoirs',
            'tank': 'qgisred_tanks',
            'pump': 'qgisred_pumps',
            'valve': 'qgisred_valves',
            'source': 'qgisred_sources',
            'serviceconnection': 'qgisred_serviceconnections',
            'isolationvalve': 'qgisred_isolationvalves',
            'meter': 'qgisred_meters'
        }
        
        normalized_name = layerName.lower().replace(" ", "")
        target_id = mapping.get(normalized_name, f"qgisred_{normalized_name}")

        for la in layers:
            found_id = la.customProperty("qgisred_identifier")
            if found_id == target_id:
                layer = la
                break

        if layer:
            # elementId is the user-facing "Id" field
            features = layer.getFeatures(f'"Id" = \'{elementId}\'')
            for feat in features:
                # Select feature for visual feedback
                layer.selectByIds([feat.id()])

                geom = feat.geometry()
                if geom.isNull():
                    continue

                box = geom.boundingBox()

                # Compute a canvas-relative buffer: 10% of the current canvas extent.
                # This keeps the zoom proportional for both large and small networks.
                canvas_extent = self.iface.mapCanvas().extent()
                buffer = max(canvas_extent.width(), canvas_extent.height()) * 0.10

                if box.width() == 0 or box.height() == 0:
                    # Point feature: center the view with the adaptive buffer
                    center = box.center()
                    box = QgsRectangle(
                        center.x() - buffer, center.y() - buffer,
                        center.x() + buffer, center.y() + buffer
                    )
                else:
                    # Line/polygon feature: expand the bounding box by the same buffer
                    # so the feature is never shown edge-to-edge of the canvas
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
