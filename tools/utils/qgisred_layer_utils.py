# -*- coding: utf-8 -*-
import os

from PyQt5.QtCore import QCoreApplication, QTimer
from qgis.core import (
    QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer,
    QgsVectorLayer, QgsCoordinateReferenceSystem
)


class QGISRedLayerUtils:
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

    MAIN_GROUP_ORDER = ["Results", "Queries", "Issues", "Inputs"]

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

    def tr(self, message):
        return QCoreApplication.translate("QGISRedLayerUtils", message)

    def runTask(self, process, postprocess):
        process()
        QTimer.singleShot(0, postprocess)

    def _fs(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _styling(self):
        from .qgisred_styling_utils import QGISRedStylingUtils
        return QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _identifiers(self):
        from .qgisred_identifier_utils import QGISRedIdentifierUtils
        return QGISRedIdentifierUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def getProjectDirectory(self):
        return self.ProjectDirectory

    def getProjectCrs(self):
        fs = self._fs()
        layerPath = fs.generatePath(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")
        for layer in self.getLayers():
            if layerPath == fs.getLayerPath(layer):
                return layer.crs()
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        return crs

    def getLayers(self):
        return [treeLayer.layer() for treeLayer in QgsProject.instance().layerTreeRoot().findLayers()]

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

    def applyStylesToInputLayers(self):
        styling = self._styling()
        inputGroup = self.getInputGroup()
        if inputGroup is None:
            return
        for child in inputGroup.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    identifier = layer.customProperty("qgisred_identifier")
                    if identifier:
                        styling.setStyle(layer, identifier.replace("qgisred_", ""))

    """Groups"""
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
        return self.getOrCreateGroup("Inputs")

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

    def _getOrCreateNetGroup(self, root):
        netGroup = self._findGroupByNameRecursive(root, self.NetworkName)
        if not netGroup:
            netGroup = root.insertGroup(0, self.NetworkName)
            self.setGroupIdentifier(netGroup, self.NetworkName)
        return netGroup

    def _ensureMainGroupOrder(self, netGroup):
        """Reorder MAIN_GROUP_ORDER groups as direct children of netGroup (top→bottom)."""
        for groupName in reversed(self.MAIN_GROUP_ORDER):
            group = None
            identifier = self.groupIdentifiers.get(groupName)
            if identifier:
                for child in netGroup.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        if child.customProperty("qgisred_identifier") == identifier:
                            group = child
                            break
            if not group:
                for child in netGroup.children():
                    if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
                        group = child
                        break
            if group:
                cloned = group.clone()
                netGroup.insertChildNode(0, cloned)
                netGroup.removeChildNode(group)

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
            netGroup = self._getOrCreateNetGroup(root)
        parent = netGroup if netGroup else root
        newGroup = parent.insertGroup(0, groupName)
        self.setGroupIdentifier(newGroup, groupName)
        if netGroup:
            self._ensureMainGroupOrder(netGroup)
            # Re-find after reorder since the node may have been cloned
            identifier = self.groupIdentifiers.get(groupName)
            if identifier:
                refound = self.findGroupByIdentifier(identifier)
                if refound:
                    return refound
        return newGroup

    def getOrCreateNestedGroup(self, path):
        if not path or len(path) == 0:
            return QgsProject.instance().layerTreeRoot()
        root = QgsProject.instance().layerTreeRoot()
        currentParent = root
        netGroup = None
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
            # Track the network group (first level) to enforce main group order
            if i == 0 and self.NetworkName and groupName == self.NetworkName:
                netGroup = foundGroup
            # After resolving the level directly inside the network group, reorder
            if i == 1 and netGroup is not None:
                self._ensureMainGroupOrder(netGroup)
                # Re-find foundGroup in case it was cloned during reorder
                identifier = self.groupIdentifiers.get(groupName)
                if identifier:
                    refound = None
                    for child in netGroup.children():
                        if isinstance(child, QgsLayerTreeGroup):
                            if child.customProperty("qgisred_identifier") == identifier:
                                refound = child
                                break
                    if refound:
                        foundGroup = refound
            currentParent = foundGroup
        return currentParent

    """Open Layers"""
    def isLayerOpened(self, layerName):
        fs = self._fs()
        layers = self.getLayers()
        originalLayerName = self._identifiers().getOriginalNameFromLayerName(layerName)
        layerPath = fs.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ".shp")

        for layer in layers:
            openedLayerPath = fs.getLayerPath(layer)
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
        styling = self._styling()
        identifiers = self._identifiers()
        showName = self.getLayerNameToLegend(name)
        showName = self.tr(showName)
        name = name.replace(" ", "")
        originalName = identifiers.getOriginalNameFromLayerName(name)
        layerName = self.NetworkName + "_" + originalName
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + ext), showName, "ogr")
            if not ext == ".dbf":
                if results:
                    styling.setResultStyle(vlayer, originalName)
                elif sectors:
                    styling.setSectorsStyle(vlayer)
                elif issues:
                    pass
                else:
                    styling.setStyle(vlayer, name.lower())

            # disable labels by default
            vlayer.setLabelsEnabled(False)

            QgsProject.instance().addMapLayer(vlayer, group is None)
            identifiers.setLayerIdentifier(vlayer, name)
            if group is not None:
                if toEnd:
                    group.addChildNode(QgsLayerTreeLayer(vlayer))
                else:
                    group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer
            if results:
                self.orderResultLayers(group)

    def openTreeLayer(self, group, name, treeName, link=False):
        identifiers = self._identifiers()
        originalName = identifiers.getOriginalNameFromLayerName(name)
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_" + originalName + "_Tree_" + treeName + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            if link:
                self._styling().setTreeStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            identifiers.setLayerIdentifier(vlayer, name)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def openIsolatedSegmentsLayer(self, group, name):
        identifiers = self._identifiers()
        originalName = identifiers.getOriginalNameFromLayerName(name)
        layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_IsolatedSegments_" + originalName + ".shp")
        if os.path.exists(layerPath):
            vlayer = QgsVectorLayer(layerPath, name, "ogr")
            self._styling().setIsolatedSegmentsStyle(vlayer)
            QgsProject.instance().addMapLayer(vlayer, group is None)
            identifiers.setLayerIdentifier(vlayer, name)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def openGroupLayers(self, groupName, layerNames):
        styling = self._styling()
        root = QgsProject.instance().layerTreeRoot()
        netGroup = root.insertGroup(0, self.NetworkName)
        treeGroup = netGroup.insertGroup(0, groupName)
        for lay in layerNames:
            layerName = lay
            showName = self.tr(self.getLayerNameToLegend(layerName))
            layerPath = os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
            if not os.path.exists(layerPath):
                continue

            if treeGroup is None:
                vlayer = self.iface.addVectorLayer(layerPath, showName, "ogr")
            else:
                vlayer = QgsVectorLayer(layerPath, showName, "ogr")
                QgsProject.instance().addMapLayer(vlayer, False)
                treeGroup.insertChildNode(0, QgsLayerTreeLayer(vlayer))

            if vlayer is not None:
                styling.setStyle(vlayer, layerName.lower())
                # Disable labels by default
                vlayer.setLabelsEnabled(False)
        if groupName == "Inputs":
            for child in treeGroup.children():
                child.setCustomProperty("showFeatureCount", True)

    """Remove Layers"""
    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        fs = self._fs()
        identifiers = self._identifiers()
        layers = self.getLayers()
        originalLayerName = identifiers.getOriginalNameFromLayerName(name)
        layerPath = fs.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ext)

        for layer in layers:
            if identifiers.isThematicMapsLayer(layer):
                continue
            openedLayerPath = fs.getLayerPath(layer)
            if openedLayerPath == layerPath:
                QgsProject.instance().removeMapLayer(layer.id())

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



