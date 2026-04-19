# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import QCoreApplication, QTimer
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
        return QCoreApplication.translate("InputLayerNames", message)

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
        if group is None:
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
        if netGroup is None:
            netGroup = root.insertGroup(0, self.NetworkName)
            self.setGroupIdentifier(netGroup, self.NetworkName)
        return netGroup

    def _getInsertPosition(self, netGroup, groupName):
        """Return the correct insert index within netGroup for groupName per MAIN_GROUP_ORDER."""
        if groupName not in self.MAIN_GROUP_ORDER:
            return 0
        desiredIdx = self.MAIN_GROUP_ORDER.index(groupName)
        insertPos = 0
        for i, child in enumerate(netGroup.children()):
            if not isinstance(child, QgsLayerTreeGroup):
                continue
            childId = child.customProperty("qgisred_identifier")
            childName = child.name()
            for j, orderedName in enumerate(self.MAIN_GROUP_ORDER):
                ident = self.groupIdentifiers.get(orderedName)
                if (ident and childId == ident) or childName == orderedName:
                    if j < desiredIdx:
                        insertPos = i + 1
                    break
        return insertPos

    def getOrCreateGroup(self, groupName):
        root = QgsProject.instance().layerTreeRoot()
        identifier = self.groupIdentifiers.get(groupName)

        # Resolve netGroup first so we can search its children directly.
        # In QGIS 4 / PyQt6, re-calling layerTreeRoot() may return a different
        # wrapper whose children() doesn't reflect the real tree, and PyQt6
        # QgsLayerTreeGroup objects are falsy when the C++ object is invalid,
        # so always use `is None` checks instead of truthiness.
        netGroup = None
        if self.NetworkName:
            netGroup = self._getOrCreateNetGroup(root)

        # Search within netGroup first (avoids re-calling layerTreeRoot internally)
        if netGroup is not None:
            for child in netGroup.children():
                if not isinstance(child, QgsLayerTreeGroup):
                    continue
                if identifier and child.customProperty("qgisred_identifier") == identifier:
                    return child
                if child.name() == groupName:
                    self.setGroupIdentifier(child, groupName)
                    return child

        # Fallback: search rest of tree using the root we already have
        found = self._findGroupByIdentifierRecursive(root, identifier) if identifier else None
        if found is not None:
            return found
        found = self._findGroupByNameRecursive(root, groupName)
        if found is not None:
            self.setGroupIdentifier(found, groupName)
            return found

        if netGroup is not None:
            pos = self._getInsertPosition(netGroup, groupName)
            newGroup = netGroup.insertGroup(pos, groupName)
        else:
            newGroup = root.insertGroup(0, groupName)
        self.setGroupIdentifier(newGroup, groupName)
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
            if foundGroup is None:
                for child in currentParent.children():
                    if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
                        foundGroup = child
                        break
            if foundGroup is None:
                if i == 1 and netGroup is not None:
                    pos = self._getInsertPosition(netGroup, groupName)
                    foundGroup = currentParent.insertGroup(pos, groupName)
                else:
                    foundGroup = currentParent.insertGroup(0, groupName)
                self.setGroupIdentifier(foundGroup, groupName)
            else:
                self.setGroupIdentifier(foundGroup, groupName)
            if i == 0 and self.NetworkName and groupName == self.NetworkName:
                netGroup = foundGroup
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

    def _tryReloadExistingLayer(self, layerPath):
        """If a layer at *layerPath* is already open, reload its OGR data in-place and
        return True. Returns False if no open layer matches, meaning the caller should
        open it fresh."""
        fs = self._fs()
        for layer in self.getLayers():
            if fs.getLayerPath(layer) == layerPath:
                layer.dataProvider().reloadData()
                layer.updateExtents()
                layer.triggerRepaint()
                return True
        return False

    def _reloadOpenLayer(self, layerName):
        """Reload OGR data for an already-open network layer (file was overwritten in-place)."""
        fs = self._fs()
        identifiers = self._identifiers()
        originalLayerName = identifiers.getOriginalNameFromLayerName(layerName)
        layerPath = fs.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ".shp")
        self._tryReloadExistingLayer(layerPath)

    def openElementsLayers(self, group, ownMainLayers, processOnly=False):
        if not processOnly:
            for fileName in ownMainLayers:
                if self.isLayerOpened(fileName):
                    # Layer already open — reload its data in-place (no remove/reopen flicker)
                    self._reloadOpenLayer(fileName)
                else:
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
        layerPath = os.path.join(self.ProjectDirectory, layerName + ext)
        if os.path.exists(layerPath):
            # If the layer is already open, reload its data in-place (no duplicate added)
            if self._tryReloadExistingLayer(layerPath):
                return
            vlayer = QgsVectorLayer(layerPath, showName, "ogr")
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
            if self._tryReloadExistingLayer(layerPath):
                return
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
            if self._tryReloadExistingLayer(layerPath):
                return
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
            exceptions = [self.tr("Pipes")]
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



