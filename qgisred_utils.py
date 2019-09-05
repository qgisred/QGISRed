# -*- coding: utf-8 -*-
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer

try: #QGis 3.x
    from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer
    from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer
    from qgis.core import Qgis, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
    from qgis.core import QgsRendererCategory, QgsSimpleFillSymbolLayer, QgsCategorizedSymbolRenderer
    from PyQt5.QtGui import QColor
except: #QGis 2.x
    from qgis.core import QgsSvgMarkerSymbolLayerV2 as QgsSvgMarkerSymbolLayer, QgsSymbolV2 as QgsSymbol 
    from qgis.core import QgsSingleSymbolRendererV2 as QgsSingleSymbolRenderer, QgsLineSymbolV2 as QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayerV2 as QgsSimpleLineSymbolLayer, QgsMarkerSymbolV2 as QgsMarkerSymbol 
    from qgis.core import QgsMarkerLineSymbolLayerV2 as QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayerV2 as QgsSimpleMarkerSymbolLayer
    from qgis.core import QgsRendererCategoryV2 as QgsRendererCategory, QgsSimpleFillSymbolLayerV2 as QgsSimpleFillSymbolLayer, QgsCategorizedSymbolRendererV2 as QgsCategorizedSymbolRenderer
    from qgis.core import QgsMapLayerRegistry, QgsMapLayerRegistry, QGis as Qgis
    from PyQt4.QtGui import QColor

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
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/","\\"):
                return True
        return False

    def openElementsLayers(self, group, crs, ownMainLayers, ownFiles):
        for fileName in ownFiles:
            self.openLayer(crs, group, fileName, ".dbf")
        for fileName in ownMainLayers:
            self.openLayer(crs, group, fileName)

    def openIssuesLayers(self, group, crs, layers):
        for fileName in layers:
            self.openLayer(crs, group, fileName, issues=True)

    def openLayer(self, crs, group, name, ext=".shp", results=False, toEnd=False, sectors=False, issues=False):
        layerName = self.NetworkName + "_" + name
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + ext), name, "ogr")
            if not ext == ".dbf":
                vlayer.setCrs(crs)
                if results:
                    self.setResultStyle(vlayer)
                elif sectors:
                    self.setSectorsStyle(vlayer)
                elif issues:
                    pass
                else:
                    self.setStyle(vlayer, name.lower())
            try: #QGis 3.x
                QgsProject.instance().addMapLayer(vlayer, group is None)
            except: #QGis 2.x
                QgsMapLayerRegistry.instance().addMapLayer(vlayer, group is None)
            if group is not None:
                if toEnd:
                    group.addChildNode(QgsLayerTreeLayer(vlayer))
                else:
                    group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ext).replace("/","\\"):
                try: #QGis 3.x
                    QgsProject.instance().removeMapLayer(layer.id())
                except: #QGis 2.x
                    QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
        self.iface.mapCanvas().refresh()
        del layers

    def writeFile(self, file, string):
        try: #QGis 2.x !!!!!!
            file.write(string.encode('utf-8'))
        except:
            file.write(string)

    def setStyle(self, layer, name):
        if name=="":
            return
        stylePath = os.path.join(os.path.dirname(__file__), "layerStyles")
        
        qmlPath= os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            ret = layer.loadNamedStyle(qmlPath)
        
        svgPath= os.path.join(stylePath, name + ".svg")
        if os.path.exists(svgPath):
            render = None
            if layer.geometryType()==0: #Point
                svg_style = dict()
                svg_style['name'] = svgPath
                svg_style['size'] = str(7)
                symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.changeSymbolLayer(0, symbol_layer)
                renderer = QgsSingleSymbolRenderer(symbol)
            else: #Line
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2) #Pixels
                lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)
                # Symbol
                marker = QgsMarkerSymbol.createSimple({})
                marker.deleteSymbolLayer(0)
                svg_props = dict()
                svg_props['name'] = svgPath
                svg_props['size'] = str(6)
                markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
                marker.appendSymbolLayer(markerSymbol)
                # Final Symbol
                finalMarker = QgsMarkerLineSymbolLayer()
                finalMarker.setSubSymbol(marker)
                finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                symbol.appendSymbolLayer(finalMarker)
                renderer = QgsSingleSymbolRenderer(symbol)
            
            try: #QGis 3.x
                layer.setRenderer(renderer)
            except: #QGis 2.x
                layer.setRendererV2(renderer)

    def setResultStyle(self, layer):
        stylePath = os.path.join(os.path.dirname(__file__), "layerStyles")
        
        if layer.geometryType()==0: #Point
            qmlBasePath= os.path.join(stylePath, "nodeResultsBase.qml")
        else:
            qmlBasePath= os.path.join(stylePath, "linkResultsBase.qml")
        if os.path.exists(qmlBasePath):
            f=open(qmlBasePath, "r")
            contents =f.read()
            f.close()
            qmlPath=""
            if layer.geometryType()==0: #Point
                svgPath= os.path.join(stylePath, "tanksResults.svg")
                contents = contents.replace("tanks.svg", svgPath)
                svgPath= os.path.join(stylePath, "reservoirsResults.svg")
                contents = contents.replace("reservoirs.svg", svgPath)
                qmlPath= os.path.join(stylePath, "nodeResults.qml")
            else:
                svgPath= os.path.join(stylePath, "pumps.svg")
                contents = contents.replace("pumps.svg", svgPath)
                svgPath= os.path.join(stylePath, "valves.svg")
                contents = contents.replace("valves.svg", svgPath)
                svgPath= os.path.join(stylePath, "arrow.svg")
                contents = contents.replace("arrow.svg", svgPath)
                qmlPath= os.path.join(stylePath, "linkResults.qml")
            f=open(qmlPath, "w+")
            f.write(contents)
            f.close()
            ret = layer.loadNamedStyle(qmlPath)

    def setSectorsStyle(self, layer):
        from random import randrange

        # get unique values 
        field = 'Class'
        print(field)
        try: #Qgis 3.x
            fni = layer.fields().indexFromName(field)
        except: #Qgis 2.x
            fni = layer.fieldNameIndex(field)

        print(fni)
        if fni==-1: #Hydraulic sectors
            field = 'SubNet'
            try: #Qgis 3.x
                fni = layer.fields().indexFromName(field)
            except: #Qgis 2.x
                fni = layer.fieldNameIndex(field)
        
        unique_values = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = None
            if layer.geometryType()==0: #Point
                layer_style =  dict()
                layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))
                layer_style['size'] = str(2)
                symbol_layer = QgsSimpleMarkerSymbolLayer.create(layer_style)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2) #Pixels
                lineSymbol.setWidth(1.5)
                lineSymbol.setColor(QColor(randrange(0,256), randrange(0,256), randrange(0,256)))
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            try: #QGis 3.x
                layer.setRenderer(renderer)
            except: #QGis 2.x
                layer.setRendererV2(renderer)

    def getGISRedFolder(self):
        if "64bit" in str(platform.architecture()):
            folder = os.environ["ProgramFiles"]
        else:
            try:
                folder = os.environ["ProgramFiles(x86)"]
            except:
                folder = os.environ["ProgramFiles"]
        return os.path.join(folder, "GISRed")

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
                    file_paths.append(filepath.replace("/","\\")) 
        # returning all file paths 
        return file_paths 

    def saveBackup(self, key):
        file_paths = self.getFilePaths()
        dirpath = os.path.join(tempfile._get_default_tempdir(), "qgisred" + key)
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except:
                pass
        
        with ZipFile(os.path.join(dirpath, os.path.basename(self.ProjectDirectory) + "-" + self.NetworkName + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + ".zip"),'w') as zip:
            # writing each file one by one 
            for file in file_paths:
                zip.write(file, file.replace(self.ProjectDirectory.replace("/","\\"), ""))