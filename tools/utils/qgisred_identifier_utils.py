# -*- coding: utf-8 -*-
import os
import re
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerMetadata

from .qgisred_filesystem_utils import ELEMENT_LAYERS


class QGISRedIdentifierUtils:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

        from .qgisred_field_utils import IDENTIFIER_TO_ELEMENT
        self.identifierToElementName = IDENTIFIER_TO_ELEMENT

        # Element name -> identifier suffix, which is just the name lowercased.
        self.elementIdentifiers = {name: name.lower() for name in ELEMENT_LAYERS}

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

        self.identifierToLegendName = {
            'qgisred_pipes': 'Pipes',
            'qgisred_junctions': 'Junctions',
            'qgisred_demands': 'Multiple Demands',
            'qgisred_reservoirs': 'Reservoirs',
            'qgisred_tanks': 'Tanks',
            'qgisred_pumps': 'Pumps',
            'qgisred_valves': 'Valves',
            'qgisred_sources': 'Sources',
            'qgisred_serviceconnections': 'Service Connections',
            'qgisred_isolationvalves': 'Isolation Valves',
            'qgisred_meters': 'Meters',
            'qgisred_connectivity_links': 'Connect_Links',
            'qgisred_hydraulicsectors_links': 'HydSec_Links',
            'qgisred_hydraulicsectors_nodes': 'HydSec_Nodes',
            'qgisred_hydraulicsectors_isolateddemands': 'HydSec_Isolated Demands',
            'qgisred_demandsectors_links': 'DemSec_Links',
            'qgisred_demandsectors_nodes': 'DemSec_Nodes',
            'qgisred_isolatedsegments_links': 'IsolSeg_Links',
            'qgisred_isolatedsegments_nodes': 'IsolSeg_Nodes',
            'qgisred_isolatedsegments_isolateddemands': 'IsolSeg_Isolated Demands',
            'qgisred_tree_links': 'Tree_Links',
            'qgisred_tree_nodes': 'Tree_Nodes',
            'qgisred_demandbuilder_demandlinks': 'DemBuild_Links',
            'qgisred_demandbuilder_consumptionpoints': 'DemBuild_Consumptions',
            'qgisred_demandbuilder_isolateddemandsserviceconnections': 'DemBuild_Isolated Demands Connections',
            'qgisred_demandbuilder_sectors': 'DemBuild_Sectors'
        }

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    def _normalizeDemandBuilderLayerType(self, layerType):
        """Collapse a Demand Builder file name onto the identifier of its *type*.

        There can be several themes of each type, named by the user, so the token is
        matched anywhere in the name rather than at its end: both
        "Net_DemandBuilder_Sectors" and "Net_DemandBuilder_Sectors_Barrios" are sectors.
        The longest tokens are tried first, so IsolatedDemandsServiceConnections is not
        mistaken for something shorter it happens to contain.
        """
        if not isinstance(layerType, str):
            return layerType

        # Shares the folder with the managed themes but is not one of them. Both spellings
        # are matched: files written before DemandsBuilder lost its plural still exist.
        isolated = "demandbuilder_isolateddemandsserviceconnections"
        lowerType = layerType.lower()
        if isolated in lowerType or "demandsbuilder_isolateddemandsserviceconnections" in lowerType:
            return isolated

        # The file names were shortened (DemandBuilder_Consumptions) while the identifiers
        # were not, so the tokens come from the naming rules instead of being repeated
        # here. Matched anywhere in the string: callers pass file names with and without
        # the network prefix, and both have to resolve.
        from .qgisred_auxiliary_layers import AUXILIARY_LAYER_TYPES

        lower = layerType.lower()
        for candidate in AUXILIARY_LAYER_TYPES:
            for token in candidate.fileTokens:
                if token.lower() in lower:
                    return candidate.identifierToken.lower()
        return layerType

    def _getLayerPath(self, layer):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).getLayerPath(layer)

    def _getLayers(self):
        return [treeLayer.layer() for treeLayer in QgsProject.instance().layerTreeRoot().findLayers()]

    def _generatePath(self, folder, fileName):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        fs = QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return fs.generatePath(folder, fileName)

    def _findGroupRecursive(self, parent, groupName):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
                return child
            elif isinstance(child, QgsLayerTreeGroup):
                result = self._findGroupRecursive(child, groupName)
                if result:
                    return result
        return None

    def setLayerIdentifier(self, layer, layerType):
        normalizedType = self._normalizeDemandBuilderLayerType(layerType)
        identifier = normalizedType.lower()
        # Accept a full identifier as layerType without doubling the prefix
        while identifier.startswith("qgisred_"):
            identifier = identifier[len("qgisred_"):]
        identifier = f"qgisred_{identifier}"
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
        layersByPath = {os.path.normcase(self._getLayerPath(layer)): layer for layer in self._getLayers()}
        baseDir = self.ProjectDirectory
        networkPrefix = f"{self.NetworkName}_"

        for elementName, identifier in self.elementIdentifiers.items():
            expectedPath = self._generatePath(baseDir, f"{networkPrefix}{elementName}.shp")
            if layer := layersByPath.get(os.path.normcase(expectedPath)):
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
        layersByPath = {os.path.normcase(self._getLayerPath(layer)): layer for layer in self._getLayers()}
        networkPrefix = f"{self.NetworkName}_"

        for elementName, identifierKey in self.elementIdentifiers.items():
            expectedPath = self._generatePath(self.ProjectDirectory, f"{networkPrefix}{elementName}.shp")
            layer = layersByPath.get(os.path.normcase(expectedPath))
            if layer is None:
                continue
            expectedIdentifier = f"qgisred_{identifierKey}"
            existingIdentifier = layer.customProperty("qgisred_identifier")
            if not existingIdentifier or existingIdentifier != expectedIdentifier:
                self.setLayerIdentifier(layer, identifierKey)

    def enforceAllIdentifiers(self):
        self.enforceGroupIdentifiers()
        self.enforceLayerIdentifiers()

    @staticmethod
    def repairDoubledIdentifiers():
        """Collapse 'qgisred_qgisred_...' identifiers written by older builds that
        passed a full identifier to setLayerIdentifier (e.g. the Tree layers)."""
        for layer in QgsProject.instance().mapLayers().values():
            identifier = layer.customProperty("qgisred_identifier")
            if isinstance(identifier, str) and identifier.startswith("qgisred_qgisred_"):
                while identifier.startswith("qgisred_qgisred_"):
                    identifier = identifier[len("qgisred_"):]
                layer.setCustomProperty("qgisred_identifier", identifier)

    def getAuxiliaryThemeName(self, baseName, networkName=""):
        """Legend name for a Demand Builder theme file: its family, then its own name.

        Joined the way the file name joins them — DemBuild_Sectors_Barrios — so the legend
        entry and the shapefile on disk read as the same thing.

        Both the layer manager and the metadata reopen go through here, so a theme is
        called the same however it got loaded. Deriving it from the file name instead
        would go through getLayerNameToLegend, whose "Demands" rule turns every one of
        these — DemandBuilder is in all their names — into "Multiple Demands".

        Returns "" when the file is not a recognised theme, so callers can fall back.
        """
        from .qgisred_auxiliary_layers import parseBaseName

        layerType, themeName = parseBaseName(baseName, networkName or self.NetworkName)
        if layerType is None:
            return ""
        family = self.getTranslatedNameForIdentifier(layerType.identifier)
        if not family:
            return ""
        return family + "_" + themeName if themeName else family

    def getTranslatedNameForIdentifier(self, identifier):
        """Returns the translated legend name for a qgisred_identifier, or None if unknown."""
        source = self.identifierToLegendName.get(identifier)
        if source is None:
            return None
        return self.tr(source)

    def getTreeLayerName(self, treeName, link):
        from .qgisred_layer_utils import QGISRedLayerUtils

        source = "Tree_%1_Links" if link else "Tree_%1_Nodes"
        return self.tr(source).replace("%1", QGISRedLayerUtils.treeBareName(treeName))

    def getLocaleLayerName(self, layer):
        """Legend name of a QGISRed layer in the active locale, or None when it has no default name."""
        identifier = layer.customProperty("qgisred_identifier")
        if not identifier:
            return None
        if identifier in ("qgisred_tree_nodes", "qgisred_tree_links"):
            from .qgisred_layer_utils import QGISRedLayerUtils

            layerPath = self._getLayerPath(layer)
            treeName = QGISRedLayerUtils.treeNameFromLayerPath(layerPath, self.NetworkName)
            if not treeName:
                return None
            return self.getTreeLayerName(treeName, identifier == "qgisred_tree_links")
        if identifier.startswith("qgisred_demandbuilder_"):
            baseName = os.path.splitext(os.path.basename(self._getLayerPath(layer)))[0]
            return self.getAuxiliaryThemeName(baseName) or None
        if identifier.startswith("qgisred_query_"):
            return self._getThematicMapLayerName(layer, identifier)
        if identifier in ("qgisred_node", "qgisred_link"):
            return self._getResultLayerName(layer, identifier)
        return self.getTranslatedNameForIdentifier(identifier)

    def _getThematicMapLayerName(self, layer, identifier):
        from .qgisred_thematicmaps_queries import buildQueryCatalogue, queryIdentifier

        for query in buildQueryCatalogue():
            if queryIdentifier(query) != identifier:
                continue
            suffix = query.get("name_suffix", "")
            if suffix:
                # The formula suffix records the one the map was built with, which the
                # project may have changed since; the stale-map check owns that mismatch.
                currentSuffix = re.search(r"_(DW|HW|CM)$", layer.name())
                if currentSuffix:
                    suffix = currentSuffix.group(0)
            return QCoreApplication.translate("InputLayerNames", query["layer_name"]) + suffix
        return None

    def _getResultLayerName(self, layer, identifier):
        from ...ui.analysis.qgisred_results_data import NO_VARIABLE_METADATA_TAG, resultLayerDisplayName

        layerType = "Link" if identifier == "qgisred_link" else "Node"
        baseName = os.path.splitext(os.path.basename(self._getLayerPath(layer)))[0]
        scenario = baseName[len(self.NetworkName) + 1:].rsplit("_", 1)[0] if self.NetworkName else ""
        variable, _ = QgsProject.instance().readEntry("QGISRed", f"results_{scenario}_{layerType}", "")
        if not variable:
            return None
        if variable == NO_VARIABLE_METADATA_TAG:
            if layerType == "Link":
                return QCoreApplication.translate("QGISRedResultsDock", "Links", "result layer name")
            return QCoreApplication.translate("QGISRedResultsDock", "Nodes")
        return resultLayerDisplayName(layerType, variable)

    def renameLayersToLocale(self):
        """Gives every QGISRed layer of the project its default name in the active locale."""
        for layer in self._getLayers():
            if layer is None:
                continue
            translatedName = self.getLocaleLayerName(layer)
            if translatedName and layer.name() != translatedName:
                layer.setName(translatedName)

    """Thematic Maps"""

    def isThematicMapsLayer(self, layer):
        identifier = layer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_query_")

    def getThematicMapsLayers(self):
        root = QgsProject.instance().layerTreeRoot()
        thematicGroup = self._findGroupRecursive(root, "Thematic Maps")

        if thematicGroup:
            return [treeLayer.layer() for treeLayer in thematicGroup.findLayers()]
        return []
