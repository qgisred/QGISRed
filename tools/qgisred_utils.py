# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer
from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer
from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsProperty
from qgis.core import Qgis, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
from qgis.core import QgsRendererCategory, QgsSimpleFillSymbolLayer, QgsCategorizedSymbolRenderer
from PyQt5.QtGui import QColor
# Others imports
import os
import tempfile
import platform
from zipfile import ZipFile
import datetime


class QGISRedUtils:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def isLayerOpened(self, layerName):
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/", "\\"):
                return True
        return False

    def openElementsLayers(self, group, crs, ownMainLayers, ownFiles):
        # for fileName in ownFiles:
        # self.openLayer(crs, group, fileName, ".dbf")
        for fileName in ownMainLayers:
            self.openLayer(crs, group, fileName)
        self.orderLayers(group)

    def openIssuesLayers(self, group, crs, layers):
        for fileName in layers:
            self.openLayer(crs, group, fileName, issues=True)

    def openLayer(self, crs, group, name, ext=".shp", results=False, toEnd=False, sectors=False, issues=False, tree=False):
        layerName = self.NetworkName + "_" + name
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(
                self.ProjectDirectory, layerName + ext), name, "ogr")
            if not ext == ".dbf":
                vlayer.setCrs(crs)
                if results:
                    self.setResultStyle(vlayer)
                elif sectors:
                    self.setSectorsStyle(vlayer)
                elif tree:
                    self.setTreeStyle(vlayer)
                elif issues:
                    pass
                else:
                    self.setStyle(vlayer, name.lower())
            QgsProject.instance().addMapLayer(vlayer, group is None)
            if group is not None:
                if toEnd:
                    group.addChildNode(QgsLayerTreeLayer(vlayer))
                else:
                    group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer
            if results:
                self.orderResultLayers(group)

    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ext).replace("/", "\\"):
                QgsProject.instance().removeMapLayer(layer.id())
        self.iface.mapCanvas().refresh()
        del layers

    def orderLayers(self, group):
        mylayersNames = ["Sources.shp", "Reservoirs.shp", "Tanks.shp", "Pumps.shp", "Valves.shp", "Demands.shp", "Junctions.shp",
                         "Pipes.shp", "Patterns.dbf", "Curves.dbf", "Controls.dbf", "Rules.dbf", "Options.dbf", "DefaultValues.dbf"]
        for layerName in mylayersNames:
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance(
            ).layerTreeRoot().findLayers()]
            for layer in layers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName).replace("/", "\\"):
                    _layer = layer.clone()
                    QgsProject.instance().addMapLayer(_layer, group is None)
                    if group is not None:
                        group.addChildNode(QgsLayerTreeLayer(_layer))
                        QgsProject.instance().removeMapLayer(layer.id())

    def orderResultLayers(self, group):
        layers = [tree_layer.layer() for tree_layer in group.findLayers()]
        for layer in layers:
            if not layer.geometryType() == 0:  # Point
                _layer = layer.clone()
                QgsProject.instance().addMapLayer(_layer, group is None)
                if group is not None:
                    group.addChildNode(QgsLayerTreeLayer(_layer))
                    QgsProject.instance().removeMapLayer(layer.id())

    def writeFile(self, file, string):
        file.write(string)

    def setStyle(self, layer, name):
        if name == "":
            return
        stylePath = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "layerStyles")

        # user style
        qmlPath = os.path.join(stylePath, name + "_user.qml")
        if os.path.exists(qmlPath):
            ret = layer.loadNamedStyle(qmlPath)
            return

        # default style
        qmlPath = os.path.join(stylePath, name + ".qml.bak")
        if os.path.exists(qmlPath):
            ret = layer.loadNamedStyle(qmlPath)
        svgPath = os.path.join(stylePath, name + ".svg")
        if os.path.exists(svgPath):
            render = None
            if layer.geometryType() == 0:  # Point
                svg_style = dict()
                svg_style['name'] = svgPath
                svg_style['size'] = str(7)
                if name == "demands":
                    svg_style['fill'] = '#9a1313'
                symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.changeSymbolLayer(0, symbol_layer)
                renderer = QgsSingleSymbolRenderer(symbol)
            else:  # Line
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(1.5)
                if name == "pipes":
                    lineSymbol.setColor(QColor("#0f1291"))
                symbol.appendSymbolLayer(lineSymbol)
                # Symbol
                marker = QgsMarkerSymbol.createSimple({})
                marker.deleteSymbolLayer(0)
                svg_props = dict()
                svg_props['name'] = svgPath
                svg_props['size'] = str(5)
                svg_props['offset'] = '-0.5,-0.5'
                svg_props['offset_unit'] = 'Pixel'
                markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
                marker.appendSymbolLayer(markerSymbol)
                # Final Symbol
                finalMarker = QgsMarkerLineSymbolLayer()
                finalMarker.setSubSymbol(marker)
                finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                symbol.appendSymbolLayer(finalMarker)
                if name == "pipes":
                    prop = QgsProperty()
                    prop.setExpressionString(
                        "if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))")
                    symbol.symbolLayer(1).setDataDefinedProperty(
                        0, prop)  # 0 = PropertySize
                    symbol.symbolLayer(1).setDataDefinedProperty(
                        9, prop)  # 9 = PropertyWidth
                renderer = QgsSingleSymbolRenderer(symbol)

            layer.setRenderer(renderer)

    def setResultStyle(self, layer):
        stylePath = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "layerStyles")

        # default style
        if layer.geometryType() == 0:  # Point
            qmlBasePath = os.path.join(stylePath, "nodeResults.qml.bak")
        else:
            qmlBasePath = os.path.join(stylePath, "linkResults.qml.bak")
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
                svgPath = os.path.join(stylePath, "arrow.svg")
                contents = contents.replace("arrow.svg", svgPath)
                qmlPath = os.path.join(stylePath, "linkResults.qml")
            f = open(qmlPath, "w+")
            f.write(contents)
            f.close()
            ret = layer.loadNamedStyle(qmlPath)
            os.remove(qmlPath)

    def setSectorsStyle(self, layer):
        from random import randrange

        # get unique values
        field = 'Class'
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors
            field = 'SubNet'
            fni = layer.fields().indexFromName(field)

        unique_values = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = None
            if layer.geometryType() == 0:  # Point
                layer_style = dict()
                layer_style['color'] = '%d, %d, %d' % (
                    randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layer_style['size'] = str(2)
                symbol_layer = QgsSimpleMarkerSymbolLayer.create(layer_style)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(1.5)
                lineSymbol.setColor(
                    QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256)))
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(
                unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

    def getGISRedFolder(self):
        # if "64bit" in str(platform.architecture()):
        # folder = os.environ["ProgramFiles"]
        # else:
        # try:
        # folder = os.environ["ProgramFiles(x86)"]
        # except:
        # folder = os.environ["ProgramFiles"]
        # return os.path.join(folder, "GISRed")
        return os.path.join(os.path.join(os.popen('echo %appdata%').read().strip(), "QGISRed"), "dlls")

    def setCurrentDirectory(self):
        os.chdir(self.getGISRedFolder())

    def getFilePaths(self):
        # initializing empty file paths list
        file_paths = []
        # crawling through directory and subdirectories
        for root, directories, files in os.walk(self.ProjectDirectory):
            for filename in files:
                if self.NetworkName in filename:
                    # join the two strings in order to form the full filepath.
                    filepath = os.path.join(root, filename)
                    file_paths.append(filepath.replace("/", "\\"))
        # returning all file paths
        return file_paths

    def saveBackup(self, key):
        file_paths = self.getFilePaths()
        dirpath = os.path.join(
            tempfile._get_default_tempdir(), "qgisred" + key)
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except:
                pass

        with ZipFile(os.path.join(dirpath, os.path.basename(self.ProjectDirectory) + "-" + self.NetworkName + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".zip"), 'w') as zip:
            # writing each file one by one
            for file in file_paths:
                zip.write(file, file.replace(
                    self.ProjectDirectory.replace("/", "\\"), ""))

    def setTreeStyle(self, layer):
        from random import randrange

        # get unique values
        field = 'ArcType'
        fni = layer.fields().indexFromName(field)
        unique_values = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = None
            if layer.geometryType() == 0:  # Point
                layer_style = dict()
                layer_style['color'] = '%d, %d, %d' % (
                    randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layer_style['size'] = str(2)
                symbol_layer = QgsSimpleMarkerSymbolLayer.create(layer_style)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(3)
                lineSymbol.setColor(QColor(178, 47, 60))
                if "Branch" in unique_value:
                    lineSymbol.setColor(QColor(22, 139, 251))
                else:
                    lineSymbol.setPenStyle(3)
                    lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(
                unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
