# -*- coding: utf-8 -*-
"""Tools section for QGISRed (lengths, roughness, elevation, demands, scenarios, isolated segments, tree)."""

from qgis.PyQt.QtWidgets import QApplication, QFileDialog
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsSingleSymbolRenderer, QgsSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsProperty
import hashlib

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
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

    def _getExternalLoadedLayers(self):
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

    def _getDemandsBuilderPointLayers(self):
        points = []
        demands_builder_id = QGISRedLayerUtils.groupIdentifiers.get("DemandsBuilder")
        root = QgsProject.instance().layerTreeRoot()

        for layer in QGISRedLayerUtils().getLayers():
            if layer is None:
                continue
            if layer.type() != LAYER_TYPE_VECTOR:
                continue
            if layer.geometryType() != 0:
                continue
            if not layer.customProperty("qgisred_identifier"):
                continue

            layer_node = root.findLayer(layer.id())
            if layer_node is None:
                continue

            parent = layer_node.parent()
            while parent is not None:
                if isinstance(parent, QgsLayerTreeGroup):
                    if parent.customProperty("qgisred_identifier") == demands_builder_id:
                        points.append(layer.source())
                        break
                    if parent.name() in ("DemandsBuilder", "Demands Builder"):
                        points.append(layer.source())
                        break
                parent = parent.parent()

        result = ""
        if points:
            result = "[POINT]" + ";".join(points)
        return result
    
    def _getDemandsBuilderLineLayers(self):
        lines = []
        demands_builder_id = QGISRedLayerUtils.groupIdentifiers.get("DemandsBuilder")
        root = QgsProject.instance().layerTreeRoot()

        for layer in QGISRedLayerUtils().getLayers():
            if layer is None:
                continue
            if layer.type() != LAYER_TYPE_VECTOR:
                continue
            if layer.geometryType() != 1:
                continue
            if not layer.customProperty("qgisred_identifier"):
                continue

            layer_node = root.findLayer(layer.id())
            if layer_node is None:
                continue

            parent = layer_node.parent()
            while parent is not None:
                if isinstance(parent, QgsLayerTreeGroup):
                    if parent.customProperty("qgisred_identifier") == demands_builder_id:
                        lines.append(layer.source())
                        break
                    if parent.name() in ("DemandsBuilder", "Demands Builder"):
                        lines.append(layer.source())
                        break
                parent = parent.parent()

        result = ""
        if lines:
            result = "[LINE]" + ";".join(lines)
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

        externalLayers = self._getExternalLoadedLayers()
        qgisredPointLayers = self._getDemandsBuilderPointLayers()
        qgisredLineLayers = self._getDemandsBuilderLineLayers() 

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.especificComplementaryLayers = ["ServiceConnections"]
        resMessage = GISRed.DemandsBuilder(self.ProjectDirectory,
            self.NetworkName,
            self.tempFolder,
            ids,
            externalLayers,
            qgisredPointLayers,
            qgisredLineLayers
        )
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "", layerType = "demandsBuilder")
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

    def _colorForDemandCategory(self, category):
        text = "" if category is None else str(category).strip()

        if text == "" or text.lower() in ("null", "undefined"):
            return QColor("orange")

        normalized = text.lower()
        digest = hashlib.md5(normalized.encode("utf-8")).hexdigest()
        hue = int(digest[:8], 16) % 360

        color = QColor()
        color.setHsv(hue, 180, 220)
        return color

    def _applyDemandsBuilderStyle(self, vlayer):
        from ..tools.utils.qgisred_styling_utils import QGISRedStylingUtils

        if "IsolatedDemandsServiceConnections" in vlayer.name():
            QGISRedStylingUtils(
                self.ProjectDirectory,
                self.NetworkName,
                self.iface
            ).setStyle(vlayer, "DemandsBuilderIsolatedDemandsServiceConnections")
            vlayer.triggerRepaint()
            return
        
        geom_type = vlayer.geometryType()
        field_index = vlayer.fields().indexFromName("Category")

        if field_index != -1:
            unique_cats = set()
            has_uncategorized = False

            for feature in vlayer.getFeatures():
                raw_cat = feature[field_index]
                text = "" if raw_cat is None else str(raw_cat).strip()

                if text == "" or text.lower() in ("null", "undefined"):
                    has_uncategorized = True
                else:
                    unique_cats.add(text)

            categories = []

            if has_uncategorized:
                symbol_uncategorized = QgsSymbol.defaultSymbol(geom_type)
                symbol_uncategorized.setColor(QColor("orange"))
                categories.append(
                    QgsRendererCategory("Uncategorized", symbol_uncategorized, "Uncategorized")
                )

            for cat in sorted(unique_cats):
                color = self._colorForDemandCategory(cat)

                symbol = QgsSymbol.defaultSymbol(geom_type)
                symbol.setColor(color)

                categories.append(
                    QgsRendererCategory(cat, symbol, cat)
                )

            category_expression = (
                "CASE "
                "WHEN \"Category\" IS NULL "
                "OR trim(\"Category\") = '' "
                "OR lower(trim(\"Category\")) IN ('null', 'undefined') "
                "THEN 'Uncategorized' "
                "ELSE trim(\"Category\") "
                "END"
            )

            renderer = QgsCategorizedSymbolRenderer(
                category_expression,
                categories
            )

            vlayer.setRenderer(renderer)
            from ..tools.utils.qgisred_styling_utils import QGISRedStylingUtils
            QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface).translateRendererLabels(vlayer)

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

        # Build color expression for labels based on category colors
        if field_index != -1:
            color_expression = "CASE "
            if has_uncategorized:
                color_expression += "WHEN \"Category\" IS NULL OR trim(\"Category\") = '' OR lower(trim(\"Category\")) IN ('null', 'undefined') THEN 'orange' "
            for cat in sorted(unique_cats):
                safe_cat = cat.replace("'", "''")
                hex_color = self._colorForDemandCategory(cat).name()

                color_expression += (
                    f"WHEN trim(\"Category\") = '{safe_cat}' "
                    f"THEN '{hex_color}' "
                )
            color_expression += "ELSE 'gray' END"
            
            label_settings.dataDefinedProperties().setProperty(QgsPalLayerSettings.Color, QgsProperty.fromExpression(color_expression))

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
            base_demand_field = getattr(self, "_demandsBuilderNewBaseDemandFieldName", "BaseDemand")
            if base_demand_field and vlayer.fields().indexFromName(base_demand_field) != -1:

                # Create new text format for point labels with larger size
                point_text_format = QgsTextFormat()
                point_text_format.setSize(12)
                point_text_format.setColor(QColor("black"))
                label_settings.setFormat(point_text_format)
                
                label_settings.fieldName = f'"{base_demand_field}"'
                label_settings.isExpression = True
                label_settings.enabled = True

                vlayer.setLabelsEnabled(True)
                vlayer.setLabeling(
                    QgsVectorLayerSimpleLabeling(label_settings)
                )

        vlayer.triggerRepaint()

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

