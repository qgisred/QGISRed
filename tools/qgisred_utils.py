# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsTask, QgsApplication
from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, Qgis
from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsProperty
from qgis.core import QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem
from qgis.core import QgsSymbolLayer

# Others imports
import os
import tempfile
import datetime
import shutil
from shutil import copyfile
import platform
from zipfile import ZipFile
from random import randrange
from xml.etree import ElementTree


class QGISRedUtils:
    DllTempoFolder = None

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    """Layers"""

    def getLayers(self):
        return [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]

    def getProjectCrs(self):
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")
        for layer in self.getLayers():
            if layerPath == self.getLayerPath(layer):
                return layer.crs()
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        return crs

    def getProjectExtent(self):
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")
        for layer in self.getLayers():
            if layerPath == self.getLayerPath(layer):
                return layer.extent()
        return None

    def getLayerNameToLegend(self, original):
        upperIndex = []
        for x in range(len(original)):
            if original[x].isupper():
                upperIndex.append(x)
        upperIndex = upperIndex[::-1]
        for ind in upperIndex:
            if ind != 0:
                original = original[:ind] + " " + original[ind:]

        if "Demands" in original:
            original = "Multiple Demands"
        return original

    """Open Layers"""

    def isLayerOpened(self, layerName):
        layers = self.getLayers()
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            if openedLayerPath == layerPath:
                return True
        return False

    def openElementsLayers(self, group, ownMainLayers):
        for fileName in ownMainLayers:
            self.openLayer(group, fileName)
        if len(ownMainLayers) > 0:
            self.orderLayers(group)
        for child in group.children():
            child.setCustomProperty("showFeatureCount", True)

    def openIssuesLayers(self, group, layers):
        for fileName in layers:
            self.openLayer(group, fileName, issues=True)

    def openLayer(self, group, name, ext=".shp", results=False, toEnd=False, sectors=False, issues=False):
        showName = self.getLayerNameToLegend(name)
        name = name.replace(" ", "")
        layerName = self.NetworkName + "_" + name
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + ext), showName, "ogr")
            if not ext == ".dbf":
                if results:
                    self.setResultStyle(vlayer)
                elif sectors:
                    self.setSectorsStyle(vlayer)
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

    def openTreeLayer(self, group, name, treeName, link=False):
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + "_Tree_" + treeName + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            if link:
                self.setTreeStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def openIsolatedSegmentsLayer(self, group, name):
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_IsolatedSegments_" + name + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            self.setIsolatedSegmentsStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    """Remove Layers"""

    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        layers = self.getLayers()
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + name + ext)
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            if openedLayerPath == layerPath:
                QgsProject.instance().removeMapLayer(layer.id())
        self.iface.mapCanvas().refresh()
        del layers

    """Order Layers"""

    def orderLayers(self, group):
        mylayersNames = [
            "Meters.shp",
            "ServiceConnections.shp",
            "IsolationValves.shp",
            "Hydrants.shp",
            "WashoutValves.shp",
            "AirReleaseValves.shp",
            "Sources.shp",
            "Reservoirs.shp",
            "Tanks.shp",
            "Demands.shp",
            "Junctions.shp",
            "Pumps.shp",
            "Valves.shp",
            "Pipes.shp",
        ]
        layersToDelete = []
        layers = self.getLayers()
        for layerName in mylayersNames:
            layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName)
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == layerPath:
                    layerCloned = layer.clone()
                    layersToDelete.append(layer.id())
                    QgsProject.instance().addMapLayer(layerCloned, group is None)
                    if group is not None:
                        group.addChildNode(QgsLayerTreeLayer(layerCloned))

        if len(layersToDelete) > 0:
            QgsProject.instance().removeMapLayers(layersToDelete)

    def orderResultLayers(self, group):
        layers = [tree_layer.layer() for tree_layer in group.findLayers()]  # Only in group
        for layer in layers:
            if not layer.geometryType() == 0:  # Point
                clonedLayer = layer.clone()
                QgsProject.instance().addMapLayer(clonedLayer, group is None)
                if group is not None:
                    group.addChildNode(QgsLayerTreeLayer(clonedLayer))
                    QgsProject.instance().removeMapLayer(layer.id())

    """Paths"""

    def getUniformedPath(self, path):
        return path.replace("/", "\\")

    def getLayerPath(self, layer):
        try:
            path = str(layer.dataProvider().dataSourceUri().split("|")[0])
            return self.getUniformedPath(path)
        except:
            return ""

    def generatePath(self, folder, fileName):
        return self.getUniformedPath(os.path.join(folder, fileName))

    """Styles"""

    def setStyle(self, layer, name):
        if name == "":
            return
        stylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layerStyles")

        # user style
        qmlPath = os.path.join(stylePath, name + "_user.qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            return

        # default style
        qmlPath = os.path.join(stylePath, name + ".qml.bak")
        if os.path.exists(qmlPath):
            if name == "meters":
                f = open(qmlPath, "r")
                contents = f.read()
                f.close()
                newQmlPath = ""
                svgPath = os.path.join(stylePath, "meterCount.svg")
                contents = contents.replace("meterCount.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterDiff.svg")
                contents = contents.replace("meterDiff.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterEnergy.svg")
                contents = contents.replace("meterEnergy.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterFlow.svg")
                contents = contents.replace("meterFlow.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterLevel.svg")
                contents = contents.replace("meterLevel.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterMan.svg")
                contents = contents.replace("meterMan.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterOpen.svg")
                contents = contents.replace("meterOpen.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterQuality.svg")
                contents = contents.replace("meterQuality.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterStatus.svg")
                contents = contents.replace("meterStatus.svg", svgPath)
                svgPath = os.path.join(stylePath, "meterTacho.svg")
                contents = contents.replace("meterTacho.svg", svgPath)
                newQmlPath = os.path.join(stylePath, "meters.qml")
                f = open(newQmlPath, "w+")
                f.write(contents)
                f.close()
                layer.loadNamedStyle(newQmlPath)
                os.remove(newQmlPath)
            else:
                layer.loadNamedStyle(qmlPath)
        svgPath = os.path.join(stylePath, name + ".svg")
        if os.path.exists(svgPath):
            if layer.geometryType() == 0:  # Point
                svg_style = dict()
                svg_style["name"] = svgPath
                size = "7"
                svg_style["size"] = size
                if name == "demands":
                    svg_style["fill"] = "#9a1313"
                symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.changeSymbolLayer(0, symbol_layer)
                renderer = QgsSingleSymbolRenderer(symbol)
            else:  # Line
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)
                # Line Color
                pipesColor = "if(IniStatus is NULL, '#0f1291',if(IniStatus !='CLOSED', '#0f1291','#ff0f13'))"
                valvesColor = "if(IniStatus is NULL, '#85b66f',if(IniStatus is 'CLOSED', '#ff0f13', if(IniStatus !='ACTIVE', '#85b66f','#ff9900')))"
                pumpsColor = "if(IniStatus is NULL, '#85b66f',if(IniStatus !='CLOSED', '#85b66f','#ff0f13'))"
                prop = QgsProperty()
                tip= ""
                if name == "pipes":
                    tip = "[Pipe]"
                    prop.setExpressionString(pipesColor)
                if name == "valves":
                    tip = "[Valve]"
                    prop.setExpressionString(valvesColor)
                if name == "pumps":
                    tip = "[Pump]"
                    prop.setExpressionString(pumpsColor)
                symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeColor, prop)
                # Custom dash
                prop2 = QgsProperty()
                prop2.setExpressionString("if(IniStatus = 'CLOSED', '5;2', '5000;0')")
                symbol.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyCustomDash, prop2)
                # Symbol
                marker = QgsMarkerSymbol.createSimple({})
                marker.deleteSymbolLayer(0)
                svg_props = dict()
                svg_props["name"] = svgPath
                size = 5
                if name == "pipes":
                    size = 0
                svg_props["size"] = str(size)
                svg_props["offset"] = "-0.5,-0.5"
                svg_props["offset_unit"] = "Pixel"
                markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
                # SVG marker Color
                markerSymbol.setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor, prop)
                marker.appendSymbolLayer(markerSymbol)
                # Final Symbol
                finalMarker = QgsMarkerLineSymbolLayer()
                finalMarker.setSubSymbol(marker)
                finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                symbol.appendSymbolLayer(finalMarker)
                if name == "pipes":
                    prop = QgsProperty()
                    prop.setExpressionString("if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,5))")
                    finalMarker.setDataDefinedProperty(QgsSymbolLayer.PropertyWidth, prop)  # 9 = PropertyWidth
                renderer = QgsSingleSymbolRenderer(symbol)
                layer.setMapTipTemplate(tip + " [% \"Id\" %]")    

            layer.setRenderer(renderer)

    def setResultStyle(self, layer):
        stylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layerStyles")

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
            # ret = layer.loadNamedStyle(qmlPath)
            layer.loadNamedStyle(qmlPath)
            os.remove(qmlPath)

    def setSectorsStyle(self, layer):
        # get unique values
        field = "Class"
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors
            field = "SubNet"
            fni = layer.fields().indexFromName(field)

        unique_values = layer.dataProvider().uniqueValues(fni)
        unique_values = sorted(unique_values)

        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbol_layer = None
            if layer.geometryType() == 0:  # Point
                layer_style = dict()
                layer_style["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layer_style["size"] = str(2)
                symbol_layer = QgsSimpleMarkerSymbolLayer.create(layer_style)
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
            layer.setRenderer(renderer)

    def setTreeStyle(self, layer):
        # get unique values
        field = "ArcType"
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
                layer_style["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layer_style["size"] = str(2)
                symbol_layer = QgsSimpleMarkerSymbolLayer.create(layer_style)
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
            category = QgsRendererCategory(unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)

    def setIsolatedSegmentsStyle(self, layer):
        stylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layerStyles")

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
            # ret = layer.loadNamedStyle(qmlPath)
            layer.loadNamedStyle(qmlPath)
            os.remove(qmlPath)

    """Others"""

    def copyDependencies(self):
        if not os.path.exists(self.getGISRedDllFolder()):
            return
        QGISRedUtils.DllTempoFolder = tempfile._get_default_tempdir() + "\\QGISRed_" + next(tempfile._get_candidate_names())
        shutil.copytree(self.getGISRedDllFolder(), QGISRedUtils.DllTempoFolder)

    def getGISRedFolder(self):
        return os.path.join(os.getenv("APPDATA"), "QGISRed")

    def getGISRedDllFolder(self):
        plat = "x86"
        if "64bit" in str(platform.architecture()):
            plat = "x64"
        dllFolder = os.path.join(self.getGISRedFolder(), "dlls")
        return os.path.join(dllFolder, plat)

    def getCurrentDll(self):
        os.chdir(QGISRedUtils.DllTempoFolder)
        return os.path.join(QGISRedUtils.DllTempoFolder, "GISRed.QGisPlugins.dll")

    def getUserFolder(self):
        userFolder = os.path.expanduser("~\\QGISRed")
        try:  # create directory if does not exist
            os.stat(userFolder)
        except Exception:
            os.mkdir(userFolder)
        userFolder = os.path.expanduser("~\\QGISRed\\Projects")
        try:  # create directory if does not exist
            os.stat(userFolder)
        except Exception:
            os.mkdir(userFolder)
        return userFolder

    """Open/Save/Remove files"""

    def openProjectInQgis(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, "r", encoding="latin-1") as content_file:
                data = content_file.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for qgs in root.findall("./ThirdParty/QGISRed/QGisProject"):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    qgisPath = finfo.filePath()
                    if not os.path.isfile(qgisPath): # Create absolute path
                        currentDirectory = os.getcwd()
                        os.chdir(self.ProjectDirectory)
                        qgisPath = os.path.abspath(qgisPath)
                        os.chdir(currentDirectory)

                    if os.path.exists(qgisPath):   
                        QgsProject.instance().read(qgisPath)
                    else:
                        request = QMessageBox.question(
                            self.iface.mainWindow(),
                            "QGISRed project",
                            "We cannot find the qgis project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group.",
                            QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                        )
                        if request == QMessageBox.Yes:
                            qfd = QFileDialog()
                            filter = "qgz(*.qgz)"
                            f = QFileDialog.getOpenFileName(qfd, "Select QGis file", "", filter)
                            qgisPath = f[0]
                            if not qgisPath == "":
                                QgsProject.instance().read(qgisPath)
                        else:
                            layers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
                            self.openGroupLayers("Inputs", layers)
                    return
            for groups in root.findall("./ThirdParty/QGISRed/Groups"):
                for group in groups:
                    groupName = group.tag
                    layers = []
                    for lay in group.iter("Layer"):
                        layers.append(lay.text)
                    self.openGroupLayers(groupName, layers)
                   
        else:  # old file
            gqpFilename = os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")
            if os.path.exists(gqpFilename):
                f = open(gqpFilename, "r")
                lines = f.readlines()
                qgsFile = lines[2]
                if ".qgs" in qgsFile or ".qgz" in qgsFile:
                    finfo = QFileInfo(qgsFile)
                    QgsProject.instance().read(finfo.filePath())
                else:
                    group = None
                    for i in range(2, len(lines)):
                        if "[" in lines[i]:
                            groupName = str(lines[i].strip("[").strip("\r\n").strip("]")).replace(self.NetworkName + " ", "")
                            root = QgsProject.instance().layerTreeRoot()
                            netGroup = root.addGroup(self.NetworkName)
                            group = netGroup.addGroup(groupName)
                        else:
                            layerPath = lines[i].strip("\r\n")
                            if not os.path.exists(layerPath):
                                continue
                            vlayer = None
                            layerName = os.path.splitext(os.path.basename(layerPath))[0].replace(self.NetworkName + "_", "")
                            if group is None:
                                vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
                            else:
                                vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                                QgsProject.instance().addMapLayer(vlayer, False)
                                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
                            if vlayer is not None:
                                if ".shp" in layerPath:
                                    names = (os.path.splitext(os.path.basename(layerPath))[0]).split("_")
                                    nameLayer = names[len(names) - 1]
                                    QGISRedUtils().setStyle(vlayer, nameLayer.lower())
            else:
                self.iface.messageBar().pushMessage("Warning", "File not found", level=1, duration=5)

    def openGroupLayers(self, groupName, layerNames):
        root = QgsProject.instance().layerTreeRoot()
        netGroup = root.addGroup(self.NetworkName)
        treeGroup = netGroup.addGroup(groupName)
        for lay in layerNames:
            layerName = lay
            layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
            if not os.path.exists(layerPath):
                continue

            if treeGroup is None:
                vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
            else:
                vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                QgsProject.instance().addMapLayer(vlayer, False)
                treeGroup.insertChildNode(0, QgsLayerTreeLayer(vlayer))

            if vlayer is not None:
                QGISRedUtils().setStyle(vlayer, layerName.lower())
        if groupName == "Inputs":
            for child in treeGroup.children():
                child.setCustomProperty("showFeatureCount", True)
        
    def saveFilesInZip(self, zipPath):
        file_paths = []
        for f in os.listdir(self.ProjectDirectory):
            filepath = os.path.join(self.ProjectDirectory, f)
            if os.path.isfile(filepath):
                file_paths.append(self.getUniformedPath(filepath))

        with ZipFile(zipPath, "w") as zip:
            for file in file_paths:
                if self.getUniformedPath(self.ProjectDirectory) + "\\" + self.NetworkName + "_" in file:
                    zip.write(file, file.replace(self.getUniformedPath(self.ProjectDirectory), ""))

    def unzipFile(self, zipfile, directory):
        with ZipFile(zipfile, "r") as zip_ref:
            zip_ref.extractall(directory)

    def saveBackup(self):
        dirpath = os.path.join(self.ProjectDirectory, "backups")
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except Exception:
                pass

        timeString = datetime.datetime.now().timestamp()
        zipPath = os.path.join(dirpath, self.NetworkName + "_" + str(timeString) + ".zip")

        self.saveFilesInZip(zipPath)
        return zipPath

    def writeFile(self, file, string):
        file.write(string)

    def copyFolderFiles(self, originalFolder, destinationFolder):
        if not os.path.exists(destinationFolder):
            try:
                os.mkdir(destinationFolder)
            except Exception:
                pass

        folder = self.getUniformedPath(originalFolder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath):
                try:
                    copyfile(r"" + filepath, r"" + filepath.replace(folder, destinationFolder))
                except:
                    pass
            elif os.path.isdir(filepath):
                self.copyFolderFiles(filepath, os.path.join(destinationFolder, f))

    def removeFolder(self, folder):
        try:
            if os.path.exists(folder) and os.path.isdir(folder):
                shutil.rmtree(folder)
        except:
            return False
        return True

    """Tasks"""

    def runTask(self, name, process, postprocess, managing=False):
        if managing:
            task = QgsTask.fromFunction(name, process, on_finished=postprocess)
            task.run()
            QgsApplication.taskManager().addTask(task)
        else:
            process(None)
            postprocess()

    def getUnits(self):
        units, ok = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")

        # International Units
        international_units = ["LPS", "LPM", "MLD", "CMH", "CMD"]
        # American Units 
        american_units = ["CFS", "GPM", "MGD", "IMGD", "AFD"]

        print("units: ", units)
        if units in american_units:
            return 'US'
        elif units in international_units:
            return 'SI'
        else:
            # Default to SI units
            return 'SI'