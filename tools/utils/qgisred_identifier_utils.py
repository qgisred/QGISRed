# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsLayerMetadata


class QGISRedIdentifierUtils:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

        from .qgisred_field_utils import QGISRedFieldUtils
        _field = QGISRedFieldUtils(directory, networkName, iface)
        self.identifierToElementName = _field.identifierToElementName

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
            'qgisred_connectivity_links': 'Links Connectivity',
            'qgisred_hydraulicsectors_links': 'Links HS',
            'qgisred_hydraulicsectors_nodes': 'Nodes HS',
            'qgisred_hydraulicsectors_isolateddemands': 'Isolated Demands HS',
            'qgisred_demandsectors_links': 'Links DS',
            'qgisred_demandsectors_nodes': 'Nodes DS',
            'qgisred_isolatedsegments_links': 'Links IS',
            'qgisred_isolatedsegments_nodes': 'Nodes IS',
            'qgisred_isolatedsegments_isolateddemands': 'Isolated Demands IS',
            'qgisred_tree_links': 'Links T',
            'qgisred_tree_nodes': 'Nodes T',
        }

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    def _getLayerPath(self, layer):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).getLayerPath(layer)

    def _getLayers(self):
        return [treeLayer.layer() for treeLayer in QgsProject.instance().layerTreeRoot().findLayers()]

    def _generatePath(self, folder, fileName):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).generatePath(folder, fileName)

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
        layersByPath = {self._getLayerPath(layer): layer for layer in self._getLayers()}
        baseDir = self.ProjectDirectory
        networkPrefix = f"{self.NetworkName}_"

        for elementName, identifier in self.elementIdentifiers.items():
            expectedPath = self._generatePath(baseDir, f"{networkPrefix}{elementName}.shp")
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
        layersByPath = {self._getLayerPath(layer): layer for layer in self._getLayers()}
        networkPrefix = f"{self.NetworkName}_"

        for elementName, identifierKey in self.elementIdentifiers.items():
            expectedPath = self._generatePath(self.ProjectDirectory, f"{networkPrefix}{elementName}.shp")
            layer = layersByPath.get(expectedPath)
            if layer is None:
                continue
            expectedIdentifier = f"qgisred_{identifierKey}"
            existingIdentifier = layer.customProperty("qgisred_identifier")
            if not existingIdentifier or existingIdentifier != expectedIdentifier:
                self.setLayerIdentifier(layer, identifierKey)

    def enforceAllIdentifiers(self):
        self.enforceGroupIdentifiers()
        self.enforceLayerIdentifiers()

    def getTranslatedNameForIdentifier(self, identifier):
        """Returns the translated legend name for a qgisred_identifier, or None if unknown."""
        source = self.identifierToLegendName.get(identifier)
        if source is None:
            return None
        return self.tr(source)

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

