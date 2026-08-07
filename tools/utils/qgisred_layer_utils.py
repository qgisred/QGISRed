# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtCore import QCoreApplication, QTimer
from qgis.core import (
    QgsProject, QgsLayerTreeGroup, QgsLayerTreeLayer,
    QgsVectorLayer, QgsCoordinateReferenceSystem, QgsDataProvider,
    QgsAttributeTableConfig, QgsCategorizedSymbolRenderer
)


class QGISRedLayerUtils:
    groupIdentifiers = {
        'Inputs': 'qgisred_inputs',
        'Issues': 'qgisred_issues',
        'Results': 'qgisred_results',
        'Queries': 'qgisred_queries',
        'Auxiliary Layers': 'qgisred_auxiliary',
        'Thematic Maps': 'qgisred_thematicmaps',
        'Connectivity': 'qgisred_connectivity',
        'HydraulicSectors': 'qgisred_hydraulicsectors',
        'Demand Sectors': 'qgisred_demandsectors',
        'IsolatedSegments': 'qgisred_isolatedsegments',
        'DemandBuilder': 'qgisred_demandbuilder',
        'DemandSectors': 'qgisred_demandsectors',
        'Trees': 'qgisred_trees',
    }

    identifierToGroupName = {
        'qgisred_inputs': 'Inputs',
        'qgisred_issues': 'Issues',
        'qgisred_results': 'Results',
        'qgisred_queries': 'Queries',
        'qgisred_auxiliary': 'Auxiliary Layers',
        'qgisred_thematicmaps': 'Thematic Maps',
        'qgisred_connectivity': 'Connectivity',
        'qgisred_hydraulicsectors': 'HydraulicSectors',
        'qgisred_isolatedsegments': 'IsolatedSegments',
        'qgisred_demandbuilder': 'DemandBuilder',
        'qgisred_demandsectors': 'DemandSectors',
        'qgisred_trees': 'Trees',
    }

    # Maps qgisred_identifier → canonical English group name (locale-independent)
    _IDENTIFIER_TO_CANONICAL = {
        'qgisred_inputs':           'Inputs',
        'qgisred_issues':           'Issues',
        'qgisred_results':          'Results',
        'qgisred_queries':          'Queries',
        'qgisred_auxiliary':        'Auxiliary Layers',
        'qgisred_thematicmaps':     'Thematic Maps',
        'qgisred_connectivity':     'Connectivity',
        'qgisred_hydraulicsectors': 'Hydraulic Sectors',
        'qgisred_demandsectors':    'Demand Sectors',
        'qgisred_isolatedsegments': 'Isolated Segments',
        'qgisred_demandbuilder':    'Demand Builder',
        'qgisred_trees':            'Trees',
        # Written by builds where setGroupIdentifier derived the identifier from the name
        # instead of reading it from groupIdentifiers. Existing projects still carry it.
        'qgisred_auxiliarylayers':  'Auxiliary Layers',
        # Before DemandsBuilder lost its plural.
        'qgisred_demandsbuilder':   'Demand Builder',
    }

    MAIN_GROUP_ORDER = ["Results", "Queries", "Issues", "Auxiliary Layers", "Inputs"]

    _CATEGORIZED_LAYER_IDS = {
        'qgisred_query_pipes_length',
        'qgisred_query_pipes_diameter',
    }

    @classmethod
    def getLayerSupportsCategorized(cls, layerIdentifier: str) -> bool:
        """Return True if the layer supports categorized legend classification."""
        return layerIdentifier in cls._CATEGORIZED_LAYER_IDS

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

        self.identifierToGroupName = {
            'qgisred_inputs': 'Inputs',
            'qgisred_issues': 'Issues',
            'qgisred_results': 'Results',
            'qgisred_queries': 'Queries',
            'qgisred_auxiliary': 'Auxiliary Layers',
            'qgisred_thematicmaps': 'Thematic Maps',
            'qgisred_connectivity': 'Connectivity',
            'qgisred_hydraulicsectors': 'HydraulicSectors',
            'qgisred_demandsectors': 'DemandSectors',
            'qgisred_isolatedsegments': 'IsolatedSegments',
            'qgisred_demandbuilder': 'DemandBuilder',
            'qgisred_trees': 'Trees',
        }

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    @classmethod
    def _translateGroupName(cls, name):
        """Return the translated display name for a canonical group name."""
        # Direct QCoreApplication.translate calls so pylupdate5 indexes every string:
        _TRANSLATIONS = {
            "Inputs":            QCoreApplication.translate("QGISRedGroups", "Inputs"),
            "Issues":            QCoreApplication.translate("QGISRedGroups", "Issues"),
            "Results":           QCoreApplication.translate("QGISRedGroups", "Results"),
            "Queries":           QCoreApplication.translate("QGISRedGroups", "Queries"),
            "Thematic Maps":     QCoreApplication.translate("QGISRedGroups", "Thematic Maps"),
            "Connectivity":      QCoreApplication.translate("QGISRedGroups", "Connectivity"),
            "Hydraulic Sectors": QCoreApplication.translate("QGISRedGroups", "Hydraulic Sectors"),
            "Demand Sectors":    QCoreApplication.translate("QGISRedGroups", "Demand Sectors"),
            "Isolated Segments": QCoreApplication.translate("QGISRedGroups", "Isolated Segments"),
            "Trees":             QCoreApplication.translate("QGISRedGroups", "Trees"),
            "DemandBuilder":     QCoreApplication.translate("QGISRedGroups", "DemandBuilder"),
            "DemandSectors":     QCoreApplication.translate("QGISRedGroups", "DemandSectors"),
            "Auxiliary Layers":   QCoreApplication.translate("QGISRedGroups", "Auxiliary Layers"),
        }
        # Dynamic tree groups (e.g. "Tree: J5-Unión") don't need translation; return as-is
        if name.startswith("Tree: "):
            return name
        return _TRANSLATIONS.get(name, name)

    @classmethod
    def getCanonicalGroupName(cls, group):
        """Return the canonical English name for a QgsLayerTreeGroup.
        Uses the qgisred_identifier property; falls back to group.name()."""
        identifier = group.customProperty("qgisred_identifier")
        return cls._IDENTIFIER_TO_CANONICAL.get(identifier, group.name())

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

        if "Isolated Demands" in original:
            original = "Isolated Demands"
        elif "Demands" in original:
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
    def findGroupsByIdentifier(cls, identifier):
        # Projects can hold duplicated groups with the same identifier (e.g. after a
        # network rename), so consumers needing layers must merge all matches.
        root = QgsProject.instance().layerTreeRoot()
        groups = []
        cls._collectGroupsByIdentifierRecursive(root, identifier, groups)
        return groups

    @classmethod
    def _collectGroupsByIdentifierRecursive(cls, parent, identifier, groups):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                if child.customProperty("qgisred_identifier") == identifier:
                    groups.append(child)
                cls._collectGroupsByIdentifierRecursive(child, identifier, groups)

    @classmethod
    def getLayersByGroupIdentifier(cls, identifier):
        layers = []
        for group in cls.findGroupsByIdentifier(identifier):
            for layerNode in group.findLayers():
                layer = layerNode.layer()
                if layer is not None:
                    layers.append(layer)
        return layers

    @classmethod
    def setGroupIdentifier(cls, group, keyOrName):
        if group is None:
            return
        # The declared mapping wins over deriving one from the name. "Auxiliary Layers"
        # is declared as qgisred_auxiliary but derives as qgisred_auxiliarylayers, which
        # _IDENTIFIER_TO_CANONICAL does not know — so the group fell back to its localised
        # name and the metadata ended up with tags like <CapasAuxiliares>, which nothing
        # could read back.
        identifier = cls.groupIdentifiers.get(keyOrName)
        if not identifier:
            identifier = "qgisred_" + keyOrName.lower().replace(" ", "")
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

        translated = self._translateGroupName(groupName)

        # Search within netGroup first (avoids re-calling layerTreeRoot internally)
        if netGroup is not None:
            for child in netGroup.children():
                if not isinstance(child, QgsLayerTreeGroup):
                    continue
                if identifier and child.customProperty("qgisred_identifier") == identifier:
                    if child.name() != translated:
                        child.setName(translated)
                    return child
                if child.name() == groupName or child.name() == translated:
                    self.setGroupIdentifier(child, groupName)
                    if child.name() != translated:
                        child.setName(translated)
                    return child

        # Fallback: search rest of tree using the root we already have
        found = self._findGroupByIdentifierRecursive(root, identifier) if identifier else None
        if found is not None:
            if found.name() != translated:
                found.setName(translated)
            return found
        found = self._findGroupByNameRecursive(root, groupName)
        if found is None:
            found = self._findGroupByNameRecursive(root, translated)
        if found is not None:
            self.setGroupIdentifier(found, groupName)
            if found.name() != translated:
                found.setName(translated)
            return found

        if netGroup is not None:
            pos = self._getInsertPosition(netGroup, groupName)
            newGroup = netGroup.insertGroup(pos, translated)
        else:
            newGroup = root.insertGroup(0, translated)
        self.setGroupIdentifier(newGroup, groupName)
        return newGroup

    def getOrCreateNestedGroup(self, path, applyVisibility=True):
        """Find or create a nested group, bringing it to the front of its siblings.

        `applyVisibility=False` leaves every group's checkbox exactly as the user left it.
        A tool that opens layers as the result of running something is expected to show
        what it produced, but the layer manager only loads and unloads on request: turning
        the legend on and off underneath the user is not part of what they asked for.
        """
        if not path or len(path) == 0:
            return QgsProject.instance().layerTreeRoot()
        root = QgsProject.instance().layerTreeRoot()
        currentParent = root
        netGroup = None
        for i, groupName in enumerate(path):
            foundGroup = None
            translated = self._translateGroupName(groupName) if i > 0 else groupName
            identifier = self.groupIdentifiers.get(groupName)
            if identifier:
                for child in currentParent.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        if child.customProperty("qgisred_identifier") == identifier:
                            foundGroup = child
                            break
            if foundGroup is None:
                for child in currentParent.children():
                    if isinstance(child, QgsLayerTreeGroup) and (
                        child.name() == groupName or child.name() == translated
                    ):
                        foundGroup = child
                        break
            if foundGroup is None:
                if i == 1 and netGroup is not None:
                    pos = self._getInsertPosition(netGroup, groupName)
                    foundGroup = currentParent.insertGroup(pos, translated)
                else:
                    foundGroup = currentParent.insertGroup(0, translated)
                self.setGroupIdentifier(foundGroup, groupName)
            else:
                self.setGroupIdentifier(foundGroup, groupName)
                if i > 0 and foundGroup.name() != translated:
                    foundGroup.setName(translated)
            if i == 0 and self.NetworkName and groupName == self.NetworkName:
                netGroup = foundGroup
            # From index 1 onwards: show this group and hide its siblings within the
            # parent. Index 0 is either the network root or a top-level group we don't
            # own, so we never touch its siblings.
            if i > 0 and applyVisibility:
                if i == 1:
                    # Top-level group under network root.
                    # Inputs: touch nothing at all (no visibility changes).
                    # Issues/Queries/Auxiliary: leave Inputs visibility unchanged; hide everything else.
                    # Results: hide all other groups.
                    if groupName == "Inputs":
                        pass
                    else:
                        keepInputs = groupName in ("Issues", "Queries", "Auxiliary Layers")
                        inputsId = self.groupIdentifiers.get("Inputs")
                        for sibling in currentParent.children():
                            if not isinstance(sibling, QgsLayerTreeGroup):
                                continue
                            if sibling == foundGroup:
                                sibling.setItemVisibilityChecked(True)
                            elif keepInputs and sibling.customProperty("qgisred_identifier") == inputsId:
                                pass  # leave Inputs visibility unchanged
                            else:
                                sibling.setItemVisibilityChecked(False)
                else:
                    # Deeper subgroups: hide all siblings except the active one.
                    for sibling in currentParent.children():
                        if isinstance(sibling, QgsLayerTreeGroup):
                            sibling.setItemVisibilityChecked(sibling == foundGroup)
            currentParent = foundGroup
        return currentParent

    """Open Layers"""

    def isLayerOpened(self, layerName):
        fs = self._fs()
        identifiers = self._identifiers()
        layers = self.getLayers()
        originalLayerName = identifiers.getOriginalNameFromLayerName(layerName)
        layerPath = fs.generatePath(self.ProjectDirectory, self.NetworkName + "_" + originalLayerName + ".shp")

        for layer in layers:
            if identifiers.isThematicMapsLayer(layer):
                continue
            openedLayerPath = fs.getLayerPath(layer)
            if openedLayerPath == layerPath:
                return True
        return False

    def _findLayerByPath(self, layerPath):
        """Return the open QgsVectorLayer whose source file matches *layerPath*, or None.
        Thematic-maps layers share source paths with input layers and must be excluded."""
        fs = self._fs()
        identifiers = self._identifiers()
        for layer in self.getLayers():
            if identifiers.isThematicMapsLayer(layer):
                continue
            if fs.getLayerPath(layer) == layerPath:
                return layer
        return None

    def _tryReloadExistingLayer(self, layerPath):
        """If a layer at *layerPath* is already open, reload its OGR data in-place and
        return the layer. Returns None if no open layer matches, meaning the caller should
        open it fresh."""
        layer = self._findLayerByPath(layerPath)
        if layer is not None:
            layer.dataProvider().reloadData()
            layer.setDataSource(layerPath, layer.name(), "ogr", QgsDataProvider.ProviderOptions())
            layer.setAttributeTableConfig(QgsAttributeTableConfig())
            layer.updateFields()
            layer.updateExtents()
            layer.triggerRepaint()
        self.refreshThematicMapLayers(layerPath)
        return layer

    def refreshThematicMapLayers(self, layerPath):
        """Reload and repaint open thematic-map layers whose source file is *layerPath*.
        They share the shapefile with an input layer, so an edit committed to that file
        must reach them too; only their data cache is refreshed, never their symbology."""
        from contextlib import suppress

        fs = self._fs()
        identifiers = self._identifiers()
        layerPath = fs.getUniformedPath(layerPath)
        for layer in self.getLayers():
            with suppress(Exception):
                if not identifiers.isThematicMapsLayer(layer):
                    continue
                if fs.getLayerPath(layer) != layerPath:
                    continue
                provider = layer.dataProvider()
                if provider is not None:
                    provider.reloadData()
                layer.updateExtents()
                with suppress(Exception):
                    self._rebuildCategorizedThematicRenderer(layer)
                layer.triggerRepaint()
                with suppress(Exception):
                    layer.countSymbolFeatures()

    def _rebuildCategorizedThematicRenderer(self, layer):
        """A categorized thematic map classifies by literal value, so a value first
        introduced by an edit has no category yet and its feature would not be drawn.
        Rebuild the categories from the current data; existing values keep the colours
        saved in the layer's style file."""
        if not isinstance(layer.renderer(), QgsCategorizedSymbolRenderer):
            return
        field = layer.customProperty("query_field")
        if not field:
            return
        self._styling().applyCategorizedRenderer(layer, field, layer.customProperty("styleURI"))

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

    def _applySectorStyle(self, styling, layer, originalName):
        """Style a sector layer: a style of the user's own wins over the family default.

        Hydraulic sectors ship a style file, so setStyle already covers them. Demand
        sectors have theirs computed instead — setSectorsStyle draws a random colour per
        class and redraws them on every reload — which used to mean a saved style could
        never take effect for them.
        """
        if "HydraulicSectors" in originalName:
            styling.setStyle(layer, originalName)
        elif not styling.setSavedStyle(layer, originalName):
            styling.setSectorsStyle(layer)

    def openLayer(self, group, name, ext=".shp", results=False, toEnd=False, sectors=False, issues=False,
                  demandBuilder=False):
        styling = self._styling()
        identifiers = self._identifiers()
        name = name.replace(" ", "")
        identifier = f"qgisred_{name.lower()}"
        if issues:
            baseName = name.replace("_Issues", "")
            baseIdentifier = f"qgisred_{baseName.lower()}"
            translatedBase = identifiers.getTranslatedNameForIdentifier(baseIdentifier) or self.tr(self.getLayerNameToLegend(baseName))
            showName = self.tr("%1 I").replace("%1", translatedBase)
        elif demandBuilder:
            showName = identifiers.getAuxiliaryThemeName(name, self.NetworkName) or name
        else:
            showName = identifiers.getTranslatedNameForIdentifier(identifier) or self.tr(self.getLayerNameToLegend(name))
        originalName = identifiers.getOriginalNameFromLayerName(name)
        layerName = self.NetworkName + "_" + originalName
        layerPath = os.path.join(self.ProjectDirectory, layerName + ext)
        if os.path.exists(layerPath):
            # If the layer is already open, reload its data in-place (no duplicate added)
            reloaded = self._tryReloadExistingLayer(layerPath)
            if reloaded:
                # Styles computed from the layer's own values must be rebuilt on every
                # reload: the values may have changed under them.
                if sectors or demandBuilder:
                    existingLayer = self._findLayerByPath(layerPath)
                    if existingLayer is not None:
                        if sectors:
                            self._applySectorStyle(styling, existingLayer, originalName)
                        else:
                            styling.setDemandBuilderStyle(existingLayer, originalName)
                return
            vlayer = QgsVectorLayer(layerPath, showName, "ogr")
            if not ext == ".dbf":
                if results:
                    styling.setStyle(vlayer, originalName)
                elif sectors:
                    self._applySectorStyle(styling, vlayer, originalName)
                elif demandBuilder:
                    styling.setDemandBuilderStyle(vlayer, originalName)
                elif issues:
                    pass
                else:
                    styling.setStyle(vlayer, name.lower())

            QgsProject.instance().addMapLayer(vlayer, group is None)
            identifiers.setLayerIdentifier(vlayer, name)
            if group is not None:
                treeNode = QgsLayerTreeLayer(vlayer)
                if toEnd:
                    group.addChildNode(treeNode)
                else:
                    group.insertChildNode(0, treeNode)
            del vlayer
            if results:
                self.orderResultLayers(group)

    def openTreeLayer(self, group, name, treeName, link=False):
        identifiers = self._identifiers()
        identifierKey = "Tree_Links" if link else "Tree_Nodes"
        identifier = f"qgisred_{identifierKey.lower()}"
        showName = identifiers.getTranslatedNameForIdentifier(identifier) or self.tr(name)
        originalName = identifiers.getOriginalNameFromLayerName(name)
        candidates = [
            os.path.join(self.ProjectDirectory, self.NetworkName + "_" + treeName + "_" + originalName + ".shp"),
        ]
        layerPath = None
        for candidate in candidates:
            if os.path.exists(candidate):
                layerPath = candidate
                break
        if layerPath is None:
            return
        if self._tryReloadExistingLayer(layerPath):
            return
        vlayer = QgsVectorLayer(layerPath, showName, "ogr")
        if link:
            self._styling().setStyle(vlayer, "Tree_Links")
        else:
            self._styling().setStyle(vlayer, "Tree_Nodes")
        QgsProject.instance().addMapLayer(vlayer, group is None)
        identifiers.setLayerIdentifier(vlayer, identifierKey)
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
        if groupName == "Inputs":
            for child in treeGroup.children():
                child.setCustomProperty("showFeatureCount", True)

    """Remove Layers"""

    @staticmethod
    def stopRenderingForRemoval(iface=None):
        """Leave every map canvas with no render job running and no cached image.

        A layer destroyed while a parallel render job is in flight leaves a dangling
        QgsMapLayer pointer behind: when the job finishes, QGIS runs
        QgsMapRendererJob::cleanupJobs -> QgsMapRendererCache::setCacheImageWithParameters
        -> dropUnusedConnections, which dereferences it and dies with an access violation.
        The crash surfaces later, from the Qt event loop, with no trace of the code that
        removed the layer.

        stopRendering() cancels and joins the render threads, so no renderingFinished
        event can arrive afterwards; clearCache() drops the cached images that still
        reference the layer. Must be called *before* removeMapLayer().
        """
        from contextlib import suppress

        if iface is None:
            with suppress(Exception):
                from qgis.utils import iface as qgis_iface
                iface = qgis_iface
        if iface is None:
            return

        canvases = []
        with suppress(Exception):
            canvases = list(iface.mapCanvases())
        with suppress(Exception):
            main = iface.mapCanvas()
            if main is not None and main not in canvases:
                canvases.append(main)

        for canvas in canvases:
            with suppress(Exception):
                canvas.stopRendering()
            with suppress(Exception):
                canvas.clearCache()

    def removeLayers(self, layers, ext=".shp"):
        self.stopRenderingForRemoval(self.iface)
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        self.stopRenderingForRemoval(self.iface)
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
        self.stopRenderingForRemoval(self.iface)
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
        self.stopRenderingForRemoval(self.iface)
        project = QgsProject.instance()

        for node in list(group.children()):
            if isinstance(node, QgsLayerTreeLayer):
                layer = node.layer()
                if layer and layer.featureCount() == 0 and layer.name() not in exceptions:
                    layerId = layer.id()
                    project.removeMapLayer(layerId)

        if self.iface:
            self.iface.mapCanvas().refresh()

    @staticmethod
    def clearNativeIdentifyResults(iface=None):
        from contextlib import suppress
        from qgis.PyQt.QtCore import QMetaObject
        from qgis.PyQt.QtWidgets import QApplication, QDialog

        windows = []
        with suppress(Exception):
            if iface is not None and iface.mainWindow() is not None:
                windows.append(iface.mainWindow())
        with suppress(Exception):
            windows.extend(QApplication.topLevelWidgets())

        seen = set()
        for window in windows:
            if window is None or id(window) in seen:
                continue
            seen.add(id(window))
            with suppress(Exception):
                for dialog in window.findChildren(QDialog):
                    if dialog.metaObject().className() == "QgsIdentifyResultsDialog":
                        QMetaObject.invokeMethod(dialog, "clear")

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
                    # The original layer is destroyed here: no render job may be holding it.
                    self.stopRenderingForRemoval(self.iface)
                    QgsProject.instance().removeMapLayer(layer.id())

    """Render order"""

    # Themes that are a backdrop rather than a part of the network: filled polygons that
    # hide whatever the tree keeps below them. Where the legend shows them is the user's
    # business, so instead of moving them the render order pushes them under the network.
    BACKDROP_LAYER_IDENTIFIERS = ("qgisred_demandbuilder_sectors",)

    # Marks a custom layer order this plugin wrote. Without it, switching the order off
    # again could throw away one the user set up in the Layer Order panel themselves.
    _CUSTOM_ORDER_ENTRY = ("QGISRed", "CustomLayerOrder")

    @classmethod
    def isBackdropLayer(cls, layer):
        if layer is None:
            return False
        return layer.customProperty("qgisred_identifier") in cls.BACKDROP_LAYER_IDENTIFIERS

    @classmethod
    def applyBackdropRenderOrder(cls):
        """Draw the sector themes under the network, wherever the legend keeps them.

        QGIS renders the layer tree from the bottom up unless the project carries a custom
        layer order — the flat list the Layer Order panel edits, first entry drawn on top.
        Setting one is what lets a theme sit at the top of its group and still be painted
        underneath everything the network is made of.

        The list is rebuilt from the tree rather than stored, so it needs no saving: a
        project reopened without one (a network with no .qgs, where nothing persists it)
        falls back into place as soon as anything touches a layer.

        Returns True when a custom order is left in force.
        """
        root = QgsProject.instance().layerTreeRoot()
        if root is None:
            return False

        order = cls._treeLayerOrder(root)
        backdrops = [layer for layer in order if cls.isBackdropLayer(layer)]
        if not backdrops:
            cls._clearOwnRenderOrder(root)
            return False

        backdropIds = {layer.id() for layer in backdrops}
        rest = [layer for layer in order if layer.id() not in backdropIds]
        position = cls._backdropPosition(rest)
        wanted = rest[:position] + backdrops + rest[position:]

        # Nothing to say when the order already reads like this: writing it again would
        # redraw the canvas and mark the project modified on every layer that is opened.
        if root.hasCustomLayerOrder() and cls._sameLayers(root.customLayerOrder(), wanted):
            return True

        root.setCustomLayerOrder(wanted)
        root.setHasCustomLayerOrder(True)
        QgsProject.instance().writeEntry(cls._CUSTOM_ORDER_ENTRY[0], cls._CUSTOM_ORDER_ENTRY[1], True)
        return True

    @staticmethod
    def _sameLayers(current, wanted):
        return [layer.id() for layer in current if layer is not None] == [layer.id() for layer in wanted]

    @staticmethod
    def _treeLayerOrder(root):
        """Every layer in the tree, top first — the order QGIS renders in by default.

        Read from the tree and not from layerOrder(), which returns the custom order once
        there is one: building each pass on top of the last would let the two drift apart
        as layers come and go.
        """
        order = []
        seen = set()
        for node in root.findLayers():
            layer = node.layer()
            # A node whose layer is gone, or the same layer showing twice in the tree.
            if layer is None or layer.id() in seen:
                continue
            seen.add(layer.id())
            order.append(layer)
        return order

    @classmethod
    def _backdropPosition(cls, order):
        """Index just past the last input layer.

        Not the end of the list: whatever the user keeps below the network — a base map,
        typically — has to stay below the backdrop too, or the backdrop would hide it.
        """
        inputIds = {layer.id() for layer in cls.getLayersByGroupIdentifier("qgisred_inputs")}
        positions = [i for i, layer in enumerate(order) if layer.id() in inputIds]
        return positions[-1] + 1 if positions else len(order)

    @classmethod
    def _clearOwnRenderOrder(cls, root):
        """Give the project back its default order, but only if we are what changed it."""
        project = QgsProject.instance()
        if not project.readBoolEntry(cls._CUSTOM_ORDER_ENTRY[0], cls._CUSTOM_ORDER_ENTRY[1], False)[0]:
            return
        root.setHasCustomLayerOrder(False)
        project.removeEntry(cls._CUSTOM_ORDER_ENTRY[0], cls._CUSTOM_ORDER_ENTRY[1])

    @staticmethod
    def getResultsCurrentTimeText():
        """Lee el campo Time de la primera feature disponible en capas de resultados.

        Devuelve el texto formateado almacenado en la capa (civil/elapsed/ampm)
        o None si no hay capas de resultados o el campo no existe.
        """
        resultsGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_results")
        if not resultsGroup:
            return None
        for layerNode in resultsGroup.findLayers():
            layer = layerNode.layer()
            if not layer:
                continue
            time_idx = layer.fields().indexFromName("Time")
            if time_idx < 0:
                continue
            for feat in layer.getFeatures():
                val = feat.attribute(time_idx)
                val_str = str(val) if val is not None else ""
                if val_str and val_str not in ("NULL", "None", ""):
                    return val_str
        return None
