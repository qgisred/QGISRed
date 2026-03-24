# -*- coding: utf-8 -*-
import os
import tempfile
import random
from random import randrange

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsVectorLayer, QgsSymbol, Qgis, QgsLayerTreeGroup,
    QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsVectorLayerCache, NULL
)
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.utils import iface as _iface


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


def create_combined_cursor(icon, iface=None, icon_size=24):
    """Create a cursor with a slender arrow and a custom icon at the bottom-right.

    icon: str resource path, QPixmap, or QCursor (returned as-is).
    iface: optional QGIS iface, used for devicePixelRatioF (falls back to 1.0).
    icon_size: size in logical pixels for the overlaid icon (default 24).
    """
    from PyQt5.QtGui import QCursor, QPixmap, QPainter, QPainterPath, QPen, QColor
    from PyQt5.QtCore import Qt

    if isinstance(icon, QCursor):
        return icon

    ratio = 1.0
    if iface is not None:
        try:
            ratio = iface.mainWindow().devicePixelRatioF()
        except Exception:
            pass

    canvas_size = max(32, 12 + icon_size)
    pixmap = QPixmap(int(canvas_size * ratio), int(canvas_size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(0, 15)
    path.lineTo(4, 11)
    path.lineTo(6, 16)
    path.lineTo(8, 15)
    path.lineTo(6, 10.5)
    path.lineTo(11, 11)
    path.closeSubpath()

    painter.setPen(QPen(QColor(Qt.black), 0, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin))
    painter.setBrush(Qt.white)
    painter.drawPath(path)

    icon_pixmap = icon if isinstance(icon, QPixmap) else QPixmap(icon)
    if not icon_pixmap.isNull():
        scaled = icon_pixmap.scaled(
            int(icon_size * ratio), int(icon_size * ratio),
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        scaled.setDevicePixelRatio(ratio)
        offset = 11 if icon_size > 20 else 13
        painter.drawPixmap(offset, offset, scaled)

    painter.end()
    return QCursor(pixmap, 0, 0)


class QGISRedStylingUtils:
    defaultSvgPathText = "defaultSvgPath"

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    def _getQGISRedFolder(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).getQGISRedFolder()

    def setStyle(self, layer, name):
        if name == "":
            return

        # 1- project style
        projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
        qmlPath = os.path.join(projectStylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            return

        # 2- global style
        stylePath = os.path.join(self._getQGISRedFolder(), "defaults", "layerStyles")
        qmlPath = os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            return

        # 3- default style
        pluginPath = _plugin_root()
        defaultStylePath = os.path.join(pluginPath, "defaults", "layerStyles")
        qmlPath = os.path.join(defaultStylePath, name + ".qml.bak")
        tempStylePath = self.replaceSvgPathInQml(qmlPath, self.defaultSvgPathText, pluginPath)
        if os.path.exists(tempStylePath):
            layer.loadNamedStyle(tempStylePath)

    def setResultStyle(self, layer, name=""):
        # Convert result layer name to QML filename (e.g., "Link_Flow" -> "LinkFlow")
        qmlName = name.replace("_", "") if name else ""

        # Search order: project folder -> layerStyles -> defaults/layerStyles
        if qmlName:
            # 1- project style
            projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
            qmlPath = os.path.join(projectStylePath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                return

            # 2- global style
            globalStylesPath = os.path.join(self._getQGISRedFolder(), "defaults", "layerStyles")
            qmlPath = os.path.join(globalStylesPath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                return

            # 3- default style
            pluginPath = _plugin_root()
            defaultStylePath = os.path.join(pluginPath, "defaults", "layerStyles")
            qmlPath = os.path.join(defaultStylePath, qmlName + ".qml.bak")
            tempStylePath = self.replaceSvgPathInQml(qmlPath, self.defaultSvgPathText, pluginPath)
            if os.path.exists(tempStylePath):
                layer.loadNamedStyle(tempStylePath)
                return

    def replaceSvgPathInQml(self, qmlPath, defaultSvgPath, pluginPath):
        if not os.path.exists(qmlPath):
            return qmlPath

        try:
            with open(qmlPath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            newContent = content.replace(defaultSvgPath, pluginPath)

            tempPath = os.path.join(tempfile.gettempdir(), next(tempfile._get_candidate_names()) + ".qml")
            with open(tempPath, 'w', encoding='utf-8') as f:
                f.write(newContent)

            return tempPath
        except Exception:
            return qmlPath

    def setSectorsStyle(self, layer):
        # get unique values
        field = "Class"
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors
            field = "SubNet"
            fni = layer.fields().indexFromName(field)

        uniqueValues = layer.dataProvider().uniqueValues(fni)
        uniqueValues = sorted(uniqueValues)

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbolLayer = None
            if layer.geometryType() == 0:  # Point
                layerStyle = dict()
                layerStyle["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layerStyle["size"] = str(2)
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(2)
                lineSymbol.setColor(QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256)))
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            # create renderer object
            category = QgsRendererCategory(uniqueValue, symbol, str(uniqueValue))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

    def setTreeStyle(self, layer):
        # get unique values
        field = "ArcType"
        fni = layer.fields().indexFromName(field)
        uniqueValues = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbolLayer = None
            if layer.geometryType() == 0:  # Point
                layerStyle = dict()
                layerStyle["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layerStyle["size"] = str(2)
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(3)
                lineSymbol.setColor(QColor(178, 47, 60))
                if "Branch" in uniqueValue:
                    lineSymbol.setColor(QColor(22, 139, 251))
                else:
                    lineSymbol.setPenStyle(3)
                    lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            # create renderer object
            category = QgsRendererCategory(uniqueValue, symbol, str(uniqueValue))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

    def setIsolatedSegmentsStyle(self, layer):
        stylePath = os.path.join(_plugin_root(), "defaults", "layerStyles")

        # default style
        if layer.geometryType() == 0:  # Point
            qmlBasePath = os.path.join(stylePath, "isolatedSegmentsNodes.qml.bak")
        else:
            qmlBasePath = os.path.join(stylePath, "isolatedSegmentsLinks.qml.bak")
        if os.path.exists(qmlBasePath):
            f = open(qmlBasePath, "r")
            contents = f.read()
            f.close()
            qmlPath = ""
            if layer.geometryType() == 0:  # Point
                svgPath = os.path.join(stylePath, "tanksResults.svg")
                contents = contents.replace("tanks.svg", svgPath)
                svgPath = os.path.join(stylePath, "reservoirsResults.svg")
                contents = contents.replace("reservoirs.svg", svgPath)
                qmlPath = os.path.join(stylePath, "nodeResults.qml")
            else:
                svgPath = os.path.join(stylePath, "pumps.svg")
                contents = contents.replace("pumps.svg", svgPath)
                svgPath = os.path.join(stylePath, "valves.svg")
                contents = contents.replace("valves.svg", svgPath)
                qmlPath = os.path.join(stylePath, "linkResults.qml")
            f = open(qmlPath, "w+")
            f.write(contents)
            f.close()
            layer.loadNamedStyle(qmlPath)
            os.remove(qmlPath)

    def applyCategorizedRenderer(self, layer, field, qmlFile):
        fieldIndex = layer.fields().indexFromName(field)

        if fieldIndex == -1:
            raise ValueError(self.tr(f'{field} field not found in layer {layer.name()}'))

        uniqueValues = layer.uniqueValues(fieldIndex)
        categories = []

        existingCategories = {}
        if qmlFile and os.path.exists(qmlFile):
            tempLayer = QgsVectorLayer(layer.source(), layer.name(), layer.providerType())
            tempLayer.loadNamedStyle(qmlFile)
            renderer = tempLayer.renderer()

            if isinstance(renderer, QgsCategorizedSymbolRenderer):
                for cat in renderer.categories():
                    existingCategories[cat.value()] = cat.symbol().color()

        nonNullValues = [value for value in uniqueValues if value != NULL]
        nullValues = [value for value in uniqueValues if value == NULL]

        for value in nonNullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if value in existingCategories:
                symbol.setColor(existingCategories[value])
            else:
                randomColor = QColor.fromRgb(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
                symbol.setColor(randomColor)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        if nullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            darkGray = QColor.fromRgb(192, 192, 192)
            symbol.setColor(darkGray)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(nullValues[0], symbol, str("#NA"))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)
        layer.saveNamedStyle(qmlFile)

    def hideFields(self, layer, fieldname):
        config = layer.attributeTableConfig()
        columns = config.columns()

        fieldsToKeep = ['Id', fieldname]

        for column in columns:
            column.hidden = column.name not in fieldsToKeep

        config.setColumns(columns)

        layerCache = QgsVectorLayerCache(layer, layer.featureCount())

        sourceModel = QgsAttributeTableModel(layerCache)
        sourceModel.loadLayer()

        attributeTableView = QgsAttributeTableView()
        attributeTableFilterModel = QgsAttributeTableFilterModel(_iface.mapCanvas(), sourceModel)

        layer.setAttributeTableConfig(config)
        attributeTableFilterModel.setAttributeTableConfig(config)
        attributeTableView.setAttributeTableConfig(config)
