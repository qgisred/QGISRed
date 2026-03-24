# -*- coding: utf-8 -*-
from PyQt5.QtCore import QCoreApplication
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
        englishName = self.identifierToElementName.get(identifier)
        if not englishName:
            return None
        if englishName == "Demands":
            englishName = "Multiple Demands"
        return self.tr(englishName)

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

