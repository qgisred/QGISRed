# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsTask, QgsApplication, QgsLayerMetadata
from qgis.core import QgsSymbol, Qgis, QgsLayerTreeGroup, QgsLayerDefinition
from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer
from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsVectorLayerCache
from qgis.core import QgsMessageLog, NULL
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.utils import iface

import os
import tempfile
import datetime
import shutil
import random
from shutil import copyfile
import platform
from zipfile import ZipFile
from random import randrange
from xml.etree import ElementTree
import json

class QGISRedUtils:
    DllTempoFolder = None

    groupIdentifiers = {
        'Inputs': 'qgisred_inputs',
        'Results': 'qgisred_results',
        'Queries': 'qgisred_queries',
        'Thematic Maps': 'qgisred_thematicmaps',
        'Connectivity': 'qgisred_connectivity',
        'HydraulicSectors': 'qgisred_hydraulicsectors',
        'Demand Sectors': 'qgisred_demandsectors',
        'IsolatedSegments': 'qgisred_isolatedsegments'
    }

    identifierToGroupName = {
        'qgisred_inputs': 'Inputs',
        'qgisred_results': 'Results',
        'qgisred_queries': 'Queries',
        'qgisred_thematicmaps': 'Thematic Maps',
        'qgisred_connectivity': 'Connectivity',
        'qgisred_hydraulicsectors': 'HydraulicSectors',
        'qgisred_demandsectors': 'Demand Sectors',
        'qgisred_isolatedsegments': 'IsolatedSegments'
    }

    # Unit definitions loaded from JSON file
    _unit_definitions = None

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

        self.identifierToGroupName = {
            'qgisred_inputs': 'Inputs',
            'qgisred_results': 'Results',
            'qgisred_queries': 'Queries',
            'qgisred_thematicmaps': 'Thematic Maps',
            'qgisred_connectivity': 'Connectivity',
            'qgisred_hydraulicsectors': 'HydraulicSectors',
            'qgisred_demandsectors': 'Demand Sectors',
            'qgisred_isolatedsegments': 'IsolatedSegments'
        }

        self.elementIdentifiers = {
            'Pipes': 'pipes',
            'Junctions': 'junctions',
            'Tanks': 'tanks',
            'Reservoirs': 'reservoirs',
            'Valves': 'valves',
            'Pumps': 'pumps',
            'Demands': 'demands',
            'Sources': 'sources',
            'IsolationValves': 'isolationvalves',
            'ServiceConnections': 'serviceconnections',
            'Meters': 'meters'
        }

        units = self.getUnits()

        self.identifierToElementName = {
            # Existing main network layers
            'qgisred_pipes': 'Pipes',
            'qgisred_junctions': 'Junctions', 
            'qgisred_demands': 'Demands',
            'qgisred_reservoirs': 'Reservoirs',
            'qgisred_tanks': 'Tanks',
            'qgisred_pumps': 'Pumps',
            'qgisred_valves': 'Valves',
            'qgisred_sources': 'Sources',
            'qgisred_serviceconnections': 'Service Connections',
            'qgisred_isolationvalves': 'Isolation Valves',
            'qgisred_meters': 'Meters',
            
            # Result layers
            'qgisred_link_flow': 'Link Flow',
            'qgisred_link_velocity': 'Link Velocity',
            'qgisred_link_headloss': 'Link HeadLoss',
            'qgisred_link_unitheadloss': 'Link UnitHeadLoss',
            'qgisred_link_status': 'Link Status',
            'qgisred_link_quality': 'Link Quality',
            'qgisred_node_pressure': 'Node Pressure',
            'qgisred_node_head': 'Node Head',
            'qgisred_node_demand': 'Node Demand',
            'qgisred_node_quality': 'Node Quality',
            
            # Connectivity layers
            'qgisred_links_connectivity': 'Links Connectivity',
            
            # Sector layers
            'qgisred_links_hydraulicsectors': 'Links_ HydraulicSectors',
            'qgisred_nodes_hydraulicsectors': 'Nodes_ HydraulicSectors',
            'qgisred_links_demandsectors': 'Links_ Demand Sectors',
            'qgisred_nodes_demandsectors': 'Nodes_ Demand Sectors',
            
            # Isolated segments layers
            'qgisred_isolatedsegments_links': 'IsolatedSegments Links',
            'qgisred_isolatedsegments_nodes': 'IsolatedSegments Nodes',
            
            # Issues layers
            'qgisred_pipes_issues': 'Pipes Issues',
            'qgisred_junctions_issues': 'Junctions Issues',
            'qgisred_demands_issues': 'Demands Issues',
            'qgisred_valves_issues': 'Valves Issues',
            'qgisred_pumps_issues': 'Pumps Issues',
            'qgisred_tanks_issues': 'Tanks Issues',
            'qgisred_reservoirs_issues': 'Reservoirs Issues',
            'qgisred_sources_issues': 'Sources Issues',
            'qgisred_isolationvalves_issues': 'Isolation Valves Issues',
            'qgisred_hydrants_issues': 'Hydrants Issues',
            'qgisred_washoutvalves_issues': 'WashoutValves Issues',
            'qgisred_airreleasevalves_issues': 'AirReleaseValves Issues',
            'qgisred_serviceconnections_issues': 'Service Connections Issues',
            'qgisred_meters_issues': 'Meters Issues',
            
            # Tree layers
            'qgisred_links': 'Links',
            'qgisred_nodes': 'Nodes',

            # Thematic Maps Layers
            'qgisred_query_diameter_diam': f'Pipe Diameters {units}',
            'qgisred_query_length_len': f'Pipe Lengths {units}',
            'qgisred_query_material_mat': 'Pipe Materials',
        }
        
    """Layers"""

    def getLayers(self):
        return [treeLayer.layer() for treeLayer in QgsProject.instance().layerTreeRoot().findLayers()]

    def getProjectDirectory(self):
        return self.ProjectDirectory

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
    
    def findGroupRecursive(self, parent, groupName):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
                return child
            elif isinstance(child, QgsLayerTreeGroup):
                result = self.findGroupRecursive(child, groupName)
                if result:
                    return result
        return None

    def getInputGroup(self):
        root = QgsProject.instance().layerTreeRoot()
        inputGroup = self.findGroupRecursive(root, "Inputs")
        if inputGroup is None:
            netGroup = self.findGroupRecursive(root, self.NetworkName)
            if netGroup is None:
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.insertGroup(0, "Inputs")
        return inputGroup

    @classmethod
    def findGroupByIdentifier(cls, identifier):
        root = QgsProject.instance().layerTreeRoot()
        return cls._findGroupByIdentifierRecursive(root, identifier)

    @classmethod
    def _findGroupByIdentifierRecursive(cls, parent, identifier):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                groupId = child.customProperty("qgisred_identifier")
                if groupId == identifier:
                    return child
                result = cls._findGroupByIdentifierRecursive(child, identifier)
                if result:
                    return result
        return None

    @classmethod
    def setGroupIdentifier(cls, group, keyOrName):
        if not group:
            return
        normalizedName = keyOrName.lower().replace(" ", "")
        identifier = f"qgisred_{normalizedName}"
        existingId = group.customProperty("qgisred_identifier")
        if existingId != identifier:
            group.setCustomProperty("qgisred_identifier", identifier)
            if keyOrName not in cls.groupIdentifiers:
                cls.groupIdentifiers[keyOrName] = identifier
            if identifier not in cls.identifierToGroupName:
                cls.identifierToGroupName[identifier] = keyOrName

    def getOrCreateGroup(self, groupName):
        root = QgsProject.instance().layerTreeRoot()
        identifier = self.groupIdentifiers.get(groupName)
        if identifier:
            group = self.findGroupByIdentifier(identifier)
            if group:
                return group
        group = self._findGroupByNameRecursive(root, groupName)
        if group:
            self.setGroupIdentifier(group, groupName)
            return group
        netGroup = None
        if self.NetworkName:
            netGroup = self._findGroupByNameRecursive(root, self.NetworkName)
            if not netGroup:
                netGroup = root.insertGroup(0, self.NetworkName)
                self.setGroupIdentifier(netGroup, self.NetworkName)
        parent = netGroup if netGroup else root
        newGroup = parent.insertGroup(0, groupName)
        self.setGroupIdentifier(newGroup, groupName)
        return newGroup

    @classmethod
    def _findGroupByNameRecursive(cls, parent, groupName):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                if child.name() == groupName:
                    return child
                result = cls._findGroupByNameRecursive(child, groupName)
                if result:
                    return result
        return None

    def getOrCreateNestedGroup(self, path):
        if not path or len(path) == 0:
            return QgsProject.instance().layerTreeRoot()
        root = QgsProject.instance().layerTreeRoot()
        currentParent = root
        for i, groupName in enumerate(path):
            foundGroup = None
            identifier = self.groupIdentifiers.get(groupName)
            if identifier:
                for child in currentParent.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        if child.customProperty("qgisred_identifier") == identifier:
                            foundGroup = child
                            break
            if not foundGroup:
                for child in currentParent.children():
                    if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
                        foundGroup = child
                        break
            if not foundGroup:
                foundGroup = currentParent.insertGroup(0, groupName)
                self.setGroupIdentifier(foundGroup, groupName)
            else:
                self.setGroupIdentifier(foundGroup, groupName)
            currentParent = foundGroup
        return currentParent

    """Open Layers"""

    def isLayerOpened(self, layerName):
        layers = self.getLayers()
        originalLayerName = self.getOriginalNameFromLayerName(layerName)
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ".shp")

        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            if openedLayerPath == layerPath:
                return True
        return False

    def openElementsLayers(self, group, ownMainLayers, processOnly=False):
        if not processOnly:
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
        originalName = self.getOriginalNameFromLayerName(name)
        layerName = self.NetworkName + "_" + originalName 
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + ext), showName, "ogr")
            if not ext == ".dbf":
                if results:
                    self.setResultStyle(vlayer, originalName)
                elif sectors:
                    self.setSectorsStyle(vlayer)
                elif issues:
                    pass
                else:
                    self.setStyle(vlayer, name.lower())
            
            # disable labels by default
            vlayer.setLabelsEnabled(False)
            
            QgsProject.instance().addMapLayer(vlayer, group is None)
            self.setLayerIdentifier(vlayer, name) 
            if group is not None:
                if toEnd:
                    group.addChildNode(QgsLayerTreeLayer(vlayer))
                else:
                    group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer
            if results:
                self.orderResultLayers(group)


    def openTreeLayer(self, group, name, treeName, link=False):
        originalName = self.getOriginalNameFromLayerName(name)
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_" + originalName + "_Tree_" + treeName + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            if link:
                self.setTreeStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            self.setLayerIdentifier(vlayer, name) 
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def openIsolatedSegmentsLayer(self, group, name):
        originalName = self.getOriginalNameFromLayerName(name)
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_IsolatedSegments_" + originalName + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            self.setIsolatedSegmentsStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            self.setLayerIdentifier(vlayer, name)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    """Remove Layers"""

    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def isThematicMapsLayer(self, layer):
        identifier = layer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_query_")

    def removeLayer(self, name, ext=".shp"):
        layers = self.getLayers()
        originalLayerName = self.getOriginalNameFromLayerName(name)
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ext)

        groupLayers = []
        root = QgsProject.instance().layerTreeRoot()
        for groupName in ["Inputs", "Queries", "Results"]:
            group = root.findGroup(groupName)
            if group:
                groupLayers.extend([child.layer() for child in group.findLayers()])
        
        if groupLayers:
            layers = [layer for layer in layers if layer in groupLayers]

        for layer in layers:
            if self.isThematicMapsLayer(layer):
                continue
            openedLayerPath = self.getLayerPath(layer)
            if openedLayerPath == layerPath:
                QgsProject.instance().removeMapLayer(layer.id())

    """Order Layers"""
    def orderLayers(self, group):
        if group is None:
            return
        
        desiredOrderIdentifiers = [
            'qgisred_meters',
            'qgisred_serviceconnections', 
            'qgisred_isolationvalves',
            'qgisred_sources',
            'qgisred_reservoirs',
            'qgisred_tanks',
            'qgisred_demands',
            'qgisred_junctions',
            'qgisred_pumps',
            'qgisred_valves',
            'qgisred_pipes'
        ]

        identifierToNode = {}
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    identifier = layer.customProperty("qgisred_identifier")
                    if identifier:
                        identifierToNode[identifier] = child

        for targetIdentifier in reversed(desiredOrderIdentifiers):
            node = identifierToNode.get(targetIdentifier)
            if not node:
                continue

            cloned = node.clone()
            group.insertChildNode(0, cloned)
            group.removeChildNode(node)

    def orderResultLayers(self, group):
        layers = [treeLayer.layer() for treeLayer in group.findLayers()]
        for layer in layers:
            if not layer.geometryType() == 0:  # Point
                clonedLayer = layer.clone()
                QgsProject.instance().addMapLayer(clonedLayer, group is None)
                if group is not None:
                    group.addChildNode(QgsLayerTreeLayer(clonedLayer))
                    QgsProject.instance().removeMapLayer(layer.id())

    """Paths"""

    def getUniformedPath(self, path):
        if path is None:
            return ""
        path = os.path.realpath(path)
        return path.replace("/", os.sep)

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

        # project-specific style
        projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
        qmlPath = os.path.join(projectStylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            return

        # plugin style
        qmlPath = os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            return

        # default style
        defaultStylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "defaults", "layerStyles")
        qmlPath = os.path.join(defaultStylePath, name + ".qml.bak")
        if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)

    def setResultStyle(self, layer, name=""):
        # Convert result layer name to QML filename (e.g., "Link_Flow" -> "LinkFlow")
        qmlName = name.replace("_", "") if name else ""
        
        layerStylesPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "layerStyles")
        defaultStylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "defaults", "layerStyles")
        
        # Search order: project folder -> layerStyles -> defaults/layerStyles
        if qmlName:
            # project style
            projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
            qmlPath = os.path.join(projectStylePath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                return
            
            # global layerStyles
            qmlPath = os.path.join(layerStylesPath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                return
            
            # default .bak style
            qmlPath = os.path.join(defaultStylePath, qmlName + ".qml.bak")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                return
        
        #TODO -> remove this fallback
        # Fallback to generic node/link results style
        if layer.geometryType() == 0:  # Point
            qmlBasePath = os.path.join(defaultStylePath, "nodeResults.qml.bak")
        else:
            qmlBasePath = os.path.join(defaultStylePath, "linkResults.qml.bak")
        if os.path.exists(qmlBasePath):
            f = open(qmlBasePath, "r")
            contents = f.read()
            f.close()
            qmlPath = ""
            if layer.geometryType() == 0:  # Point
                svgPath = os.path.join(defaultStylePath, "tanksResults.svg")
                contents = contents.replace("tanks.svg", svgPath)
                svgPath = os.path.join(defaultStylePath, "reservoirsResults.svg")
                contents = contents.replace("reservoirs.svg", svgPath)
                qmlPath = os.path.join(defaultStylePath, "nodeResults.qml")
            else:
                svgPath = os.path.join(defaultStylePath, "pumps.svg")
                contents = contents.replace("pumps.svg", svgPath)
                svgPath = os.path.join(defaultStylePath, "valves.svg")
                contents = contents.replace("valves.svg", svgPath)
                svgPath = os.path.join(defaultStylePath, "arrow.svg")
                contents = contents.replace("arrow.svg", svgPath)
                qmlPath = os.path.join(defaultStylePath, "linkResults.qml")
            f = open(qmlPath, "w+")
            f.write(contents)
            f.close()
            layer.loadNamedStyle(qmlPath)
            os.remove(qmlPath)

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
        stylePath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "defaults", "layerStyles")

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
            with open(metadataFile, "r", encoding="latin-1") as contentFile:
                data = contentFile.read()
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
                        self.applyStylesToInputLayers()
                    else:
                        request = QMessageBox.question(
                            self.iface.mainWindow(),
                            self.tr("QGISRed project"),
                            self.tr("We cannot find the qgis project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group."),
                            QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                        )
                        if request == QMessageBox.Yes:
                            qfd = QFileDialog()
                            filter = "qgz(*.qgz)"
                            f = QFileDialog.getOpenFileName(qfd, "Select QGis file", "", filter)
                            qgisPath = f[0]
                            if not qgisPath == "":
                                QgsProject.instance().read(qgisPath)
                                self.applyStylesToInputLayers()
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
                            netGroup = root.insertGroup(0, self.NetworkName)
                            group = netGroup.insertGroup(0, groupName)
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
        netGroup = root.insertGroup(0, self.NetworkName)
        treeGroup = netGroup.insertGroup(0, groupName)
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
                # Disable labels by default
                vlayer.setLabelsEnabled(False)
        if groupName == "Inputs":
            for child in treeGroup.children():
                child.setCustomProperty("showFeatureCount", True)

    def applyStylesToInputLayers(self):
        inputGroup = self.getInputGroup()
        if inputGroup is None:
            return
        for child in inputGroup.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layerName = layer.name().replace(" ", "")
                    self.setStyle(layer, layerName.lower())

    def saveFilesInZip(self, zipPath):
        filePaths = []
        for f in os.listdir(self.ProjectDirectory):
            filepath = os.path.join(self.ProjectDirectory, f)
            if os.path.isfile(filepath):
                filePaths.append(self.getUniformedPath(filepath))

        with ZipFile(zipPath, "w") as zipFile:
            for file in filePaths:
                if self.getUniformedPath(self.ProjectDirectory) + "\\" + self.NetworkName + "_" in file:
                    zipFile.write(file, file.replace(self.getUniformedPath(self.ProjectDirectory), ""))

    def unzipFile(self, zipfile, directory):
        with ZipFile(zipfile, "r") as zipRef:
            zipRef.extractall(directory)

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

    """BID"""

    def getUnits(self):
        units, ok = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")

        internationalUnits = ["LPS", "LPM", "MLD", "CMH", "CMD"]
        americanUnits = ["CFS", "GPM", "MGD", "IMGD", "AFD"]

        if units in americanUnits:
            return 'US'
        elif units in internationalUnits:
            return 'SI'
        else:
            return 'SI'

    def loadUnitDefinitions(self):
        if QGISRedUtils._unit_definitions is not None:
            return QGISRedUtils._unit_definitions

        jsonPath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "defaults", "qgisred_units.json"
        )

        if os.path.exists(jsonPath):
            try:
                with open(jsonPath, 'r', encoding='utf-8') as f:
                    QGISRedUtils._unit_definitions = json.load(f)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error loading unit definitions: {e}", "QGISRed", Qgis.Warning)
                QGISRedUtils._unit_definitions = {}
        else:
            QGISRedUtils._unit_definitions = {}

        return QGISRedUtils._unit_definitions

    def getUnitAbbreviationForLayer(self, layerIdentifier):
        if not layerIdentifier:
            return ""

        unitSystem = self.getUnits()
        unitDefs = self.loadUnitDefinitions()

        for category, layers in unitDefs.items():
            if layerIdentifier in layers:
                unitInfo = layers[layerIdentifier].get(unitSystem)
                if unitInfo:
                    return unitInfo.get("abbr", "")

        return ""

    def getLayerSupportsCategorized(self, layerIdentifier):
        if not layerIdentifier:
            return False

        unitDefs = self.loadUnitDefinitions()

        for category, layers in unitDefs.items():
            if layerIdentifier in layers:
                return layers[layerIdentifier].get("supports_categorized", False)

        return False

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
        attributeTableFilterModel = QgsAttributeTableFilterModel(iface.mapCanvas(), sourceModel)

        layer.setAttributeTableConfig(config)
        attributeTableFilterModel.setAttributeTableConfig(config)
        attributeTableView.setAttributeTableConfig(config)

    """Layer Identifiers"""

    def setLayerIdentifier(self, layer, layerType):
        identifier = f"qgisred_{layerType.lower()}"
        layer.setCustomProperty("qgisred_identifier", identifier)
        layerMeta = QgsLayerMetadata()
        layerMeta.setIdentifier(identifier)
        layer.setMetadata(layerMeta)

    def getOriginalNameFromLayerName(self, layerName):
        layersByName = QgsProject.instance().mapLayersByName(layerName)

        if not layersByName:
            return layerName

        qgsVectorLayer = layersByName[0]
        layerIdentifier = qgsVectorLayer.customProperty("qgisred_identifier")

        if not layerIdentifier:
            return layerName

        return self.identifierToElementName.get(layerIdentifier, layerName)

    def assignLayerIdentifiers(self):
        layersByPath = {self.getLayerPath(layer): layer for layer in self.getLayers()}
        baseDir = self.ProjectDirectory
        networkPrefix = f"{self.NetworkName}_"

        for elementName, identifier in self.elementIdentifiers.items():
            expectedPath = self.generatePath(baseDir, f"{networkPrefix}{elementName}.shp")
            if layer := layersByPath.get(expectedPath):
                if not layer.customProperty("qgisred_identifier"):
                    self.setLayerIdentifier(layer, identifier)

    def enforceGroupIdentifiers(self, parent=None):
        if parent is None:
            parent = QgsProject.instance().layerTreeRoot()

        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                groupName = child.name()

                matchingIdentifier = None
                for identifier, mappedName in self.identifierToGroupName.items():
                    if groupName == mappedName:
                        matchingIdentifier = identifier
                        break

                if matchingIdentifier:
                    existingIdentifier = child.customProperty("qgisred_identifier")
                    if not existingIdentifier or existingIdentifier != matchingIdentifier:
                        child.setCustomProperty("qgisred_identifier", matchingIdentifier)

                self.enforceGroupIdentifiers(child)

    def enforceLayerIdentifiers(self):
        layers = self.getLayers()

        for layer in layers:
            layerName = layer.name()

            matchingIdentifier = None
            for identifier, mappedName in self.identifierToElementName.items():
                if layerName == mappedName:
                    matchingIdentifier = identifier
                    break

            if matchingIdentifier:
                existingIdentifier = layer.customProperty("qgisred_identifier")
                if not existingIdentifier or existingIdentifier != matchingIdentifier:
                    layer.setCustomProperty("qgisred_identifier", matchingIdentifier)
                    layerMeta = QgsLayerMetadata()
                    layerMeta.setIdentifier(matchingIdentifier)
                    layer.setMetadata(layerMeta)

    def enforceAllIdentifiers(self):
        self.enforceGroupIdentifiers()
        self.enforceLayerIdentifiers()

    """QLR Operations"""

    def getQLRFolder(self):
        qlrFolder = os.path.join(self.getGISRedFolder(), "qlr")
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)
        return qlrFolder

    def saveProjectAsQLR(self):
        qlrFolder = os.path.join(self.getQLRFolder(), self.NetworkName)
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)

        savedCount = 0
        layers = self.getLayers()
        root = QgsProject.instance().layerTreeRoot()
        layerMeta = {}

        for layer in layers:
            identifier = layer.customProperty("qgisred_identifier")
            if not identifier:
                continue

            layerNode = root.findLayer(layer.id())
            if not layerNode:
                continue

            parent = layerNode.parent()
            groupPath = []
            current = parent
            while current and current != root:
                groupPath.insert(0, current.name())
                current = current.parent()

            position = 0
            if parent:
                for i, child in enumerate(parent.children()):
                    if child == layerNode:
                        position = i
                        break

            layerMeta[identifier] = {
                "group_path": groupPath,
                "position": position,
                "name": layer.name()
            }

            qlrFilename = f"{identifier}.qlr"
            qlrPath = os.path.join(qlrFolder, qlrFilename)

            try:
                success = QgsLayerDefinition.exportLayerDefinition(qlrPath, [layerNode])
                if success:
                    savedCount += 1
            except Exception:
                continue

        if savedCount > 0:
            metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
            with open(metadataPath, 'w') as f:
                json.dump(layerMeta, f, indent=2)

        return (savedCount > 0, qlrFolder)

    def loadProjectFromQLR(self):
        qlrFolder = os.path.join(self.getQLRFolder(), self.NetworkName)

        if not os.path.exists(qlrFolder):
            return False

        qlrFiles = [f for f in os.listdir(qlrFolder) if f.endswith('.qlr')]
        if not qlrFiles:
            return False

        layerMeta = {}
        metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
        if os.path.exists(metadataPath):
            with open(metadataPath, 'r') as f:
                layerMeta = json.load(f)

        self.removePluginLayers()

        loadedLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for qlrFile in qlrFiles:
            qlrPath = os.path.join(qlrFolder, qlrFile)
            identifier = qlrFile.replace('.qlr', '')

            try:
                success = QgsLayerDefinition().loadLayerDefinition(
                    qlrPath,
                    QgsProject.instance(),
                    root
                )
                if success:
                    for layer in self.getLayers():
                        if layer.customProperty("qgisred_identifier") == identifier:
                            loadedLayers.append((layer, identifier))
                            break
            except Exception:
                continue

        for layer, identifier in loadedLayers:
            metadata = layerMeta.get(identifier, {})
            groupPath = metadata.get("group_path", [])
            position = metadata.get("position", 0)

            targetGroup = root
            for groupName in groupPath:
                existingGroup = targetGroup.findGroup(groupName)
                if existingGroup:
                    targetGroup = existingGroup
                else:
                    targetGroup = targetGroup.insertGroup(0, groupName)

            layerNode = root.findLayer(layer.id())
            if layerNode and targetGroup != root:
                clonedNode = layerNode.clone()
                numChildren = len(targetGroup.children())
                insertPos = min(position, numChildren)
                targetGroup.insertChildNode(insertPos, clonedNode)

                if layerNode.parent():
                    layerNode.parent().removeChildNode(layerNode)

        return len(loadedLayers) > 0

    def deleteProjectQLR(self):
        qlrFolder = os.path.join(self.getQLRFolder(), self.NetworkName)

        if not os.path.exists(qlrFolder):
            return False

        deletedAny = False

        for filename in os.listdir(qlrFolder):
            if filename.endswith('.qlr') or filename == 'layer_metadata.json':
                try:
                    os.remove(os.path.join(qlrFolder, filename))
                    deletedAny = True
                except Exception:
                    pass

        try:
            if not os.listdir(qlrFolder):
                os.rmdir(qlrFolder)
        except Exception:
            pass

        return deletedAny

    """Plugin Layers"""

    def removePluginLayers(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        layersToRemove = []

        for layer in self.getLayers():
            if layer.customProperty("qgisred_identifier"):
                layerNode = root.findLayer(layer.id())
                if layerNode and layerNode.parent():
                    layerNode.parent().removeChildNode(layerNode)
                layersToRemove.append(layer.id())

        for layerId in layersToRemove:
            project.removeMapLayer(layerId)

        if self.iface:
            self.iface.mapCanvas().refresh()

    def removeEmptyLayersInGroup(self, group, exceptions=None):
        if exceptions is None:
            exceptions = ["Pipes"]
        project = QgsProject.instance()

        for node in list(group.children()):
            if isinstance(node, QgsLayerTreeLayer):
                layer = node.layer()
                if layer and layer.featureCount() == 0 and layer.name() not in exceptions:
                    layerId = layer.id()
                    project.removeMapLayer(layerId)

        if self.iface:
            self.iface.mapCanvas().refresh()

    def getThematicMapsLayers(self):
        root = QgsProject.instance().layerTreeRoot()
        thematicGroup = self.findGroupRecursive(root, "Thematic Maps")

        if thematicGroup:
            return [treeLayer.layer() for treeLayer in thematicGroup.findLayers()]
        return []

    """Project Files"""

    def addProjectToGplFile(self, gplFile, networkName='', projectDirectory='', rawEntryLine=None):
        projectDirectory = self.getUniformedPath(projectDirectory)
        newEntry = rawEntryLine or f"{networkName};{projectDirectory}"
        newEntry = newEntry.strip()

        existingEntries = []
        if os.path.exists(gplFile):
            with open(gplFile, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line != newEntry:
                        existingEntries.append(line)

        with open(gplFile, "w") as f:
            f.write(newEntry + "\n")
            for entry in existingEntries:
                f.write(entry + "\n")