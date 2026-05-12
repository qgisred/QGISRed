# -*- coding: utf-8 -*-
"""Tools section for QGISRed (lengths, roughness, elevation, demands, scenarios, isolated segments, tree)."""

import os

from qgis.PyQt.QtWidgets import QApplication, QFileDialog
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeLayer, QgsSingleSymbolRenderer, QgsSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,  QgsTextFormat
from random import randint

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_filesystem_utils import (
    DIR_QUERIES, DIR_ISOLATED_SEGMENTS, DIR_AUXILIARY_LAYERS, DIR_DEMAND_BUILDER,
)
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType
from ..compat import LAYER_TYPE_VECTOR


class ToolsSection:
    """Calculate lengths, set/convert roughness, interpolate elevation, demand sectors, scenario/demands manager."""

    def runCalculateLengths(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CalculateLengths(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runElevationInterpolation(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.ElevationFiles = ""
        qfd = QFileDialog()
        path = ""
        filter = "asc(*.asc)"
        f = QFileDialog.getOpenFileNames(qfd, "Select ASC file", path, filter)
        if not f[1] == "":
            for fil in f[0]:
                self.ElevationFiles = self.ElevationFiles + fil + ";"

            # Process
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            resMessage = GISRed.ElevationInterpolation(
                self.ProjectDirectory, self.NetworkName, self.tempFolder, self.ElevationFiles
            )
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, self.tr("Any elevation has been estimated"))

    def runSetRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.SetRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runConvertRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ConvertRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def _getAuxiliarLayers(self):
        points, lines, polygons = [], [], []
        for layer in QGISRedLayerUtils().getLayers():
            if layer is None:
                continue
            if layer.type() != LAYER_TYPE_VECTOR:
                continue
            if layer.customProperty("qgisred_identifier"):
                continue
            geom_type = layer.geometryType()
            path = layer.source()
            if geom_type == 0:
                points.append(path)
            elif geom_type == 1:
                lines.append(path)
            elif geom_type == 2:
                polygons.append(path)
        result = ""
        if points:
            result += "[POINT]" + ";".join(points)
        if lines:
            result += "[LINE]" + ";".join(lines)
        if polygons:
            result += "[POLYGON]" + ";".join(polygons)
        return result

    def runDemandsBuilder(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.getSelectedFeaturesIds()
        ids = ""
        if "Junctions" in self.selectedIds:
            ids = "Junctions:" + str(self.selectedIds["Junctions"]) + ";"

        auxiliarLayers = self._getAuxiliarLayers()

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.DemandsBuilder(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids, auxiliarLayers)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "", layerType = "demandBuilder")
        self.selectedFids = {}

    def runScenarioManager(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ScenarioManager(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runDemandSectors(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.Sectors = "DemandSectors"
        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.DemandSectors(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "", layerType="sectors")

    """Isolated Segments"""

    def runIsolatedSegments(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        resMessage = "Select"
        tool = "pointIsolatedSegment"
        if point == True or point == False:
            point = ""
            self.gisredDll = None
        if not point == "":
            point = self.transformPoint(point)
            point = str(point.x()) + ":" + str(point.y())

            # Process
            if self.gisredDll is None:
                self.gisredDll = GISRed.CreateInstance()
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            resMessage = GISRed.IsolatedSegments(self.gisredDll, self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
            QApplication.restoreOverrideCursor()

        if resMessage in ("False", "Cancelled"):
            return
        if resMessage == "Select":
            self.blockLayers(True)
            self.myMapTools[tool] = QGISRedSelectPointTool(self.isolatedSegmentsButton, self, self.runIsolatedSegments, SelectPointType.Line, cursor=":/images/iconIsolatedSegments.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            return
        if "shps" in resMessage:
            if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
                self.isolatedSegmentsButton.setChecked(False)
            self.gisredDll = None
        self.blockLayers(False)
        self.processCsharpResult(resMessage, "", layerType="isolatedSegments")

    def _applyDemandBuilderStyle(self, vlayer):
        geom_type = vlayer.geometryType()
        field_index = vlayer.fields().indexFromName("Category")

        if not hasattr(self, "category_colors"):
            self.category_colors = {}

        if field_index != -1:
            unique_cats = set()
            has_undefined = False

            for feature in vlayer.getFeatures():
                raw_cat = feature[field_index]
                text = "" if raw_cat is None else str(raw_cat).strip()

                if text == "" or text.lower() in ("null", "undefined"):
                    has_undefined = True
                else:
                    unique_cats.add(text)

            categories = []

            if has_undefined:
                symbol_undefined = QgsSymbol.defaultSymbol(geom_type)
                symbol_undefined.setColor(QColor("orange"))
                categories.append(
                    QgsRendererCategory("Undefined", symbol_undefined, "Undefined")
                )

            for cat in sorted(unique_cats):
                if cat not in self.category_colors:
                    self.category_colors[cat] = QColor.fromRgb(
                        randint(0, 255),
                        randint(0, 255),
                        randint(0, 255)
                    )

                symbol = QgsSymbol.defaultSymbol(geom_type)
                symbol.setColor(self.category_colors[cat])

                categories.append(
                    QgsRendererCategory(cat, symbol, cat)
                )

            category_expression = (
                "CASE "
                "WHEN \"Category\" IS NULL "
                "OR trim(\"Category\") = '' "
                "OR lower(trim(\"Category\")) IN ('null', 'undefined') "
                "THEN 'Undefined' "
                "ELSE trim(\"Category\") "
                "END"
            )

            renderer = QgsCategorizedSymbolRenderer(
                category_expression,
                categories
            )

            vlayer.setRenderer(renderer)

        else:
            symbol = QgsSymbol.defaultSymbol(geom_type)

            if geom_type == 0:
                symbol.setColor(QColor("orange"))
            elif geom_type == 1:
                symbol.setColor(QColor("blue"))

            renderer = QgsSingleSymbolRenderer(symbol)
            vlayer.setRenderer(renderer)

        # Labels
        label_settings = QgsPalLayerSettings()

        text_format = QgsTextFormat()
        text_format.setSize(10)

        label_settings.setFormat(text_format)

        if geom_type == 1:
            if vlayer.fields().indexFromName("%Dem") != -1:

                label_settings.fieldName = '"%Dem" || \' %\''
                label_settings.isExpression = True
                label_settings.enabled = True
                label_settings.placement = QgsPalLayerSettings.Line

                vlayer.setLabelsEnabled(True)
                vlayer.setLabeling(
                    QgsVectorLayerSimpleLabeling(label_settings)
                )

        elif geom_type == 0:
            if vlayer.fields().indexFromName("BaseDemand") != -1:

                label_settings.fieldName = '"BaseDemand"'
                label_settings.isExpression = True
                label_settings.enabled = True

                vlayer.setLabelsEnabled(True)
                vlayer.setLabeling(
                    QgsVectorLayerSimpleLabeling(label_settings)
                )

        vlayer.triggerRepaint()

    def openDemandBuilderLayers(self):
        demandBuilderGroup = self.getDemandBuilderGroup()

        isoFolder = os.path.join(
            self.ProjectDirectory,
            DIR_AUXILIARY_LAYERS,
            DIR_DEMAND_BUILDER
        )

        utils = QGISRedLayerUtils(
            isoFolder,
            self.NetworkName,
            self.iface
        )

        if self._demandBuilderExtraPaths:

            for path in self._demandBuilderExtraPaths:

                if not os.path.exists(path):
                    continue

                # Reload existing layer
                reloaded_layer = utils._tryReloadExistingLayer(path)

                if reloaded_layer:
                    self._applyDemandBuilderStyle(reloaded_layer)
                    continue

                # Create new layer
                displayName = os.path.splitext(
                    os.path.basename(path)
                )[0]

                vlayer = QgsVectorLayer(
                    path,
                    displayName,
                    "ogr"
                )

                if not vlayer.isValid():
                    continue

                self._applyDemandBuilderStyle(vlayer)

                QgsProject.instance().addMapLayer(
                    vlayer,
                    False
                )

                demandBuilderGroup.insertChildNode(
                    0,
                    QgsLayerTreeLayer(vlayer)
                )

            self._demandBuilderExtraPaths = []

    def openIsolatedSegmentsLayers(self):
        # Open layers
        isoaltedSegmentsGroup = self.getIsolatedSegmentsGroup()
        isoFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, DIR_ISOLATED_SEGMENTS)
        utils = QGISRedLayerUtils(isoFolder, self.NetworkName, self.iface)
        utils.openLayer(isoaltedSegmentsGroup, "IsolatedSegments_Links")
        utils.openLayer(isoaltedSegmentsGroup, "IsolatedSegments_Nodes")
        utils.openLayer(isoaltedSegmentsGroup, "IsolatedSegments_IsolatedDemands")

    def getIsolatedSegmentsGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Isolated Segments"])
    
    def getDemandBuilderGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Auxiliary Layers", "DemandBuilder"])

    def removeIsolatedSegmentsLayers(self):
        isoFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, DIR_ISOLATED_SEGMENTS)
        utils = QGISRedLayerUtils(isoFolder, self.NetworkName, self.iface)
        utils.removeLayers(["IsolatedSegments_Links", "IsolatedSegments_Nodes"])

    """Tree"""

    def runTree(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = ""
        if point is not False:
            point = self.transformPoint(point)
            point1 = str(point.x()) + ":" + str(point.y())

        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.Tree(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1)
        QApplication.restoreOverrideCursor()

        if resMessage in ("False", "Cancelled"):
            return
        if resMessage == "Select":
            self.selectPointToTree()
            return
        if "shps" in resMessage:
            self.treeName = resMessage.split("^")[1]
            resMessage = "shps"
        self.processCsharpResult(resMessage, "", layerType="tree")

    def selectPointToTree(self):
        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(None, self, self.runTree, SelectPointType.Point)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def openTreeLayers(self):
        # Open layers
        treeGroup = self.getTreeGroup()
        treeFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, "Tree_" + self.treeName)
        utils = QGISRedLayerUtils(treeFolder, self.NetworkName, self.iface)
        utils.openTreeLayer(treeGroup, "Links", self.treeName, link=True)
        utils.openTreeLayer(treeGroup, "Nodes", self.treeName)

    def getTreeGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Tree: " + self.treeName])

    def removeTreeLayers(self):
        treeFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, "Tree_" + self.treeName)
        utils = QGISRedLayerUtils(treeFolder, self.NetworkName, self.iface)
        utils.removeLayers(["Links_Tree_" + self.treeName, "Nodes_Tree_" + self.treeName])
        self.removeEmptyQuerySubGroup("Tree")
