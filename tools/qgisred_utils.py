# -*- coding: utf-8 -*-
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsTask, QgsApplication, QgsLayerMetadata
from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, Qgis, QgsLayerTreeGroup
from qgis.core import QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsProperty, QgsLayerDefinition
from qgis.core import QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
from qgis.core import QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsCoordinateReferenceSystem, QgsVectorLayerCache
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.core import QgsSymbolLayer, NULL
from qgis.utils import iface
from qgis.core import QgsSingleSymbolRenderer, QgsSymbol,QgsSvgMarkerSymbolLayer,QgsMarkerLineSymbolLayer,QgsMarkerSymbol,QgsWkbTypes
from qgis.core import QgsReadWriteContext
from PyQt5.QtXml import QDomDocument
from qgis.core import (
    QgsProject,
    QgsLayerTreeLayer,
    QgsLayerDefinition,
    QgsMessageLog,
    Qgis
)

# Others imports
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

    def getOrCreateNetworkGroup(self):
        root = QgsProject.instance().layerTreeRoot()
        identifier = self.groupIdentifiers.get(self.NetworkName)
        if identifier:
            group = self.findGroupByIdentifier(identifier)
            if group:
                return group
        group = self._findGroupByNameRecursive(root, self.NetworkName)
        if group:
            self.setGroupIdentifier(group, self.NetworkName)
            return group
        networkGroup = root.insertGroup(0, self.NetworkName)
        self.setGroupIdentifier(networkGroup, self.NetworkName)
        return networkGroup

    @classmethod
    def assignGroupIdentifiers(cls):
        root = QgsProject.instance().layerTreeRoot()
        cls._assignGroupIdentifiersRecursive(root)

    @classmethod
    def _assignGroupIdentifiersRecursive(cls, parent):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                existingId = child.customProperty("qgisred_identifier")
                if not existingId:
                    groupName = child.name()
                    cls.setGroupIdentifier(child, groupName)
                else:
                    groupName = child.name()
                    if groupName not in cls.groupIdentifiers:
                        cls.groupIdentifiers[groupName] = existingId
                    if existingId not in cls.identifierToGroupName:
                        cls.identifierToGroupName[existingId] = groupName
                cls._assignGroupIdentifiersRecursive(child)

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

    def openElementsLayers(self, group, ownMainLayers,processOnly=False):
        print("reached 2")
        if not processOnly:
            for fileName in ownMainLayers:
                self.openLayer(group, fileName)
        if len(ownMainLayers) > 0:
            print("true")
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
                    self.setResultStyle(vlayer)
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

    def removeLayer(self, name, ext=".shp"):
        layers = self.getLayers()
        originalLayerName = self.getOriginalNameFromLayerName(name)
        layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ext)

        # Check in Inputs, Queries, and Results groups
        groupLayers = []
        root = QgsProject.instance().layerTreeRoot()
        for groupName in ["Inputs", "Queries", "Results"]:
            group = root.findGroup(groupName)
            if group:
                groupLayers.extend([child.layer() for child in group.findLayers()])
        
        if groupLayers:
            layers = [layer for layer in layers if layer in groupLayers]

        for layer in layers:
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
        projectStylePath = os.path.join(self.ProjectDirectory, "defaults", "layerStyles")
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

    """BID"""

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

    def apply_categorized_renderer(self, layer, field, qml_file):
        material_field_index = layer.fields().indexFromName(field)
        
        if material_field_index == -1:
            raise ValueError(self.tr(f'{field} field not found in layer {layer.name()}'))

        unique_values = layer.uniqueValues(material_field_index)
        categories = []

        style_uri = qml_file
        existing_categories = {}
        if style_uri and os.path.exists(style_uri):
            temp_layer = QgsVectorLayer(layer.source(), layer.name(), layer.providerType())
            temp_layer.loadNamedStyle(qml_file)
            renderer = temp_layer.renderer()
            
            if isinstance(renderer, QgsCategorizedSymbolRenderer):
                for cat in renderer.categories():
                    existing_categories[cat.value()] = cat.symbol().color()
        
        non_null_values = [value for value in unique_values if value != NULL]
        null_values = [value for value in unique_values if value == NULL]

        for value in non_null_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if value in existing_categories:
                symbol.setColor(existing_categories[value])
            else:
                random_color = QColor.fromRgb(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
                symbol.setColor(random_color)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        if null_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            dark_gray = QColor.fromRgb(192, 192, 192)
            symbol.setColor(dark_gray)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(null_values[0], symbol, str("#NA"))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)
        layer.saveNamedStyle(qml_file)

    def hide_fields(self, layer, fieldname):
        config = layer.attributeTableConfig()
        columns = config.columns()
        
        fields_to_keep = ['Id', fieldname]
        
        for column in columns:
            column.hidden = column.name not in fields_to_keep
        
        config.setColumns(columns)
        
        layer_cache = QgsVectorLayerCache(layer, layer.featureCount())

        source_model = QgsAttributeTableModel(layer_cache)
        source_model.loadLayer()
        
        attribute_table_view = QgsAttributeTableView()
        attribute_table_filter_model = QgsAttributeTableFilterModel(iface.mapCanvas(), source_model)
        
        layer.setAttributeTableConfig(config)
        attribute_table_filter_model.setAttributeTableConfig(config)
        attribute_table_view.setAttributeTableConfig(config)

    def setLayerIdentifier(self, layer, layerType):
        identifier = f"qgisred_{layerType.lower()}"
        layer.setCustomProperty("qgisred_identifier", identifier)
        layer_metadata = QgsLayerMetadata()
        layer_metadata.setIdentifier(identifier)
        layer.setMetadata(layer_metadata)

    def getQLRFolder(self):
        qlr_folder = os.path.join(self.getGISRedFolder(), "qlr")
        if not os.path.exists(qlr_folder):
            os.makedirs(qlr_folder)
        return qlr_folder

    def saveProjectAsQLR(self):
        # Get network-scoped QLR folder
        qlr_folder = os.path.join(self.getQLRFolder(), self.NetworkName)
        if not os.path.exists(qlr_folder):
            os.makedirs(qlr_folder)
        
        saved_count = 0
        layers = self.getLayers()
        root = QgsProject.instance().layerTreeRoot()
        
        # Dictionary to store layer metadata
        layer_metadata = {}
        
        for layer in layers:
            # Filter only layers with qgisred_identifier custom property
            identifier = layer.customProperty("qgisred_identifier")
            if not identifier:
                continue
                
            # Find the layer's tree node and parent group
            layer_node = root.findLayer(layer.id())
            if not layer_node:
                continue
            
            # Get parent group info
            parent = layer_node.parent()
            group_path = []
            current = parent
            while current and current != root:
                group_path.insert(0, current.name())
                current = current.parent()
            
            # Get position in parent
            position = 0
            if parent:
                for i, child in enumerate(parent.children()):
                    if child == layer_node:
                        position = i
                        break
            
            # Store metadata
            layer_metadata[identifier] = {
                "group_path": group_path,
                "position": position,
                "name": layer.name()
            }
            
            # Export single layer QLR with identifier as filename
            qlr_filename = f"{identifier}.qlr"
            qlr_path = os.path.join(qlr_folder, qlr_filename)
            
            try:
                success = QgsLayerDefinition.exportLayerDefinition(
                    qlr_path, 
                    [layer_node]
                )
                if success:
                    saved_count += 1
            except Exception:
                continue
        
        # Save metadata file
        if saved_count > 0:
            import json
            metadata_path = os.path.join(qlr_folder, "layer_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(layer_metadata, f, indent=2)
        
        return (saved_count > 0, qlr_folder)

    def loadProjectFromQLR(self):
        # Build the same folder path used in save
        qlr_folder = os.path.join(self.getQLRFolder(), self.NetworkName)
        
        # Check if folder exists and has QLR files
        if not os.path.exists(qlr_folder):
            return False
        
        qlr_files = [f for f in os.listdir(qlr_folder) if f.endswith('.qlr')]
        if not qlr_files:
            return False
        
        # Load metadata
        layer_metadata = {}
        metadata_path = os.path.join(qlr_folder, "layer_metadata.json")
        if os.path.exists(metadata_path):
            import json
            with open(metadata_path, 'r') as f:
                layer_metadata = json.load(f)
        
        # Remove currently loaded plugin layers first
        self.removePluginLayers()
        
        # Prepare to track loaded layers for repositioning
        loaded_layers = []
        root = QgsProject.instance().layerTreeRoot()
        
        # First pass: Load all QLR files temporarily to root
        for qlr_file in qlr_files:
            qlr_path = os.path.join(qlr_folder, qlr_file)
            identifier = qlr_file.replace('.qlr', '')
            
            try:
                # Load to a temporary location
                success = QgsLayerDefinition().loadLayerDefinition(
                    qlr_path,
                    QgsProject.instance(),
                    root
                )
                if success:
                    # Find the newly loaded layer
                    for layer in self.getLayers():
                        if layer.customProperty("qgisred_identifier") == identifier:
                            loaded_layers.append((layer, identifier))
                            break
            except Exception:
                continue
        
        # Second pass: Move layers to correct groups and positions
        for layer, identifier in loaded_layers:
            metadata = layer_metadata.get(identifier, {})
            group_path = metadata.get("group_path", [])
            position = metadata.get("position", 0)
            
            # Find or create the target group
            target_group = root
            for group_name in group_path:
                existing_group = target_group.findGroup(group_name)
                if existing_group:
                    target_group = existing_group
                else:
                    target_group = target_group.insertGroup(0, group_name)
            
            # Find the layer's current node
            layer_node = root.findLayer(layer.id())
            if layer_node and target_group != root:
                # Clone the node to the target group at the correct position
                cloned_node = layer_node.clone()
                
                # Insert at the correct position (clamped to valid range)
                num_children = len(target_group.children())
                insert_pos = min(position, num_children)
                target_group.insertChildNode(insert_pos, cloned_node)
                
                # Remove the original node from root
                if layer_node.parent():
                    layer_node.parent().removeChildNode(layer_node)
        
        return len(loaded_layers) > 0

    def deleteProjectQLR(self):
        # Build the network-specific folder path
        qlr_folder = os.path.join(self.getQLRFolder(), self.NetworkName)
        
        if not os.path.exists(qlr_folder):
            return False
        
        deleted_any = False
        
        # Remove all QLR files and metadata
        for filename in os.listdir(qlr_folder):
            if filename.endswith('.qlr') or filename == 'layer_metadata.json':
                try:
                    os.remove(os.path.join(qlr_folder, filename))
                    deleted_any = True
                except Exception:
                    pass
        
        # Remove the now-empty network subfolder
        try:
            if not os.listdir(qlr_folder):
                os.rmdir(qlr_folder)
        except Exception:
            pass
        
        return deleted_any

    def removePluginLayers(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        layers_to_remove = []
        
        # Collect all layer nodes with qgisred_identifier
        for layer in self.getLayers():
            if layer.customProperty("qgisred_identifier"):
                layer_node = root.findLayer(layer.id())
                if layer_node and layer_node.parent():
                    # Remove from tree
                    layer_node.parent().removeChildNode(layer_node)
                # Add to removal list
                layers_to_remove.append(layer.id())
        
        # Remove the layers from the project
        for layer_id in layers_to_remove:
            project.removeMapLayer(layer_id)
        
        # Refresh canvas if available
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
                    layer_id = layer.id()
                    project.removeMapLayer(layer_id)

        if self.iface:
            self.iface.mapCanvas().refresh()
    
    def getOriginalNameFromLayerName(self, layerName):
        layersByName = QgsProject.instance().mapLayersByName(layerName)
        
        if not layersByName:
            return layerName

        qgsVectorLayer = layersByName[0]
        
        layerIdentifier = qgsVectorLayer.customProperty("qgisred_identifier")
        print('identifier : ', layerIdentifier)

        if not layerIdentifier:
            return layerName
        
        return self.identifierToElementName.get(layerIdentifier, layerName)

    def assignLayerIdentifiers(self):
        # Create a dictionary of layers keyed by their paths
        layersByPath = {self.getLayerPath(layer): layer for layer in self.getLayers()}

        # Pre-compute common path components
        baseDir = self.ProjectDirectory
        networkPrefix = f"{self.NetworkName}_"

        # Process each element type
        for elementName, identifier in self.elementIdentifiers.items():
            # Construct the expected layer path
            expectedPath = self.generatePath(baseDir, f"{networkPrefix}{elementName}.shp")

            # Check if layer exists and needs identifier assignment
            if layer := layersByPath.get(expectedPath):
                if not layer.customProperty("qgisred_identifier"):
                    self.setLayerIdentifier(layer, identifier)

    def enforceGroupIdentifiers(self, parent=None):
        """Recursively enforce qgisred_identifier on all groups that match identifierToGroupName"""
        if parent is None:
            parent = QgsProject.instance().layerTreeRoot()

        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                groupName = child.name()

                # Check if this group name matches any in our identifier mappings
                matchingIdentifier = None
                for identifier, mappedName in self.identifierToGroupName.items():
                    if groupName == mappedName:
                        matchingIdentifier = identifier
                        break

                # If we found a matching identifier, check and apply if missing
                if matchingIdentifier:
                    existingIdentifier = child.customProperty("qgisred_identifier")
                    if not existingIdentifier or existingIdentifier != matchingIdentifier:
                        child.setCustomProperty("qgisred_identifier", matchingIdentifier)

                # Recursively process subgroups
                self.enforceGroupIdentifiers(child)

    def enforceLayerIdentifiers(self):
        """Enforce qgisred_identifier on all layers that match identifierToElementName"""
        layers = self.getLayers()

        for layer in layers:
            layerName = layer.name()

            # Check if this layer name matches any in our identifier mappings
            matchingIdentifier = None
            for identifier, mappedName in self.identifierToElementName.items():
                if layerName == mappedName:
                    matchingIdentifier = identifier
                    break

            # If we found a matching identifier, check and apply if missing
            if matchingIdentifier:
                existingIdentifier = layer.customProperty("qgisred_identifier")
                if not existingIdentifier or existingIdentifier != matchingIdentifier:
                    layer.setCustomProperty("qgisred_identifier", matchingIdentifier)
                    # Also update layer metadata
                    layer_metadata = QgsLayerMetadata()
                    layer_metadata.setIdentifier(matchingIdentifier)
                    layer.setMetadata(layer_metadata)

    def enforceAllIdentifiers(self):
        """Enforce qgisred_identifier on all groups and layers after opening a project"""
        self.enforceGroupIdentifiers()
        self.enforceLayerIdentifiers()

    def addProjectToGplFile(self, gplFile, networkName='', projectDirectory='', rawEntryLine=None):
        projectDirectory = self.getUniformedPath(projectDirectory)
        newEntry = rawEntryLine or f"{networkName};{projectDirectory}"
        newEntry = newEntry.strip()
        
        # Read existing entries, preserving order
        existingEntries = []
        if os.path.exists(gplFile):
            with open(gplFile, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line != newEntry:  # Skip empty lines and duplicates
                        existingEntries.append(line)
        
        # Write new entry at the beginning, followed by existing entries
        with open(gplFile, "w") as f:
            f.write(newEntry + "\n")
            for entry in existingEntries:
                f.write(entry + "\n")

    def getThematicMapsLayers(self):
        # Get and return all layers from Thematic Maps group, wherever it's located
        root = QgsProject.instance().layerTreeRoot()
        thematicGroup = self.findGroupRecursive(root, "Thematic Maps")
        
        if thematicGroup:
            return [tree_layer.layer() for tree_layer in thematicGroup.findLayers()]
        return []