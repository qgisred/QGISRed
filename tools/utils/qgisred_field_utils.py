# -*- coding: utf-8 -*-
import os
import json

from PyQt5.QtCore import QCoreApplication
from qgis.core import QgsProject, QgsMessageLog, Qgis


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class QGISRedFieldUtils:
    _unit_definitions = None

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

        units = self.getUnits()

        self.identifierToElementName = {
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
            'qgisred_links_connectivity': 'Links Connectivity',
            'qgisred_links_hydraulicsectors': 'Links_ HydraulicSectors',
            'qgisred_nodes_hydraulicsectors': 'Nodes_ HydraulicSectors',
            'qgisred_links_demandsectors': 'Links_ Demand Sectors',
            'qgisred_nodes_demandsectors': 'Nodes_ Demand Sectors',
            'qgisred_isolatedsegments_links': 'IsolatedSegments Links',
            'qgisred_isolatedsegments_nodes': 'IsolatedSegments Nodes',
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
            'qgisred_links': 'Links',
            'qgisred_nodes': 'Nodes',
            'qgisred_query_diameter_diam': f'Pipe Diameters {units}',
            'qgisred_query_length_len': f'Pipe Lengths {units}',
            'qgisred_query_material_mat': 'Pipe Materials',
        }

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    def getLayerSupportsCategorized(self, layerIdentifier):
        if not layerIdentifier:
            return False

        unitDefs = self.loadUnitDefinitions()

        for category, layers in unitDefs.items():
            if layerIdentifier in layers:
                return layers[layerIdentifier].get("supports_categorized", False)

        return False

    """Options"""
    def getQualityModel(self):
        """Returns the quality model type: 'Chemical', 'Age', or 'Trace'."""
        model, _ = QgsProject.instance().readEntry("QGISRed", "project_qualitymodel", "Chemical")
        return model

    """Fields"""
    def getFieldPrettyName(self, elementCategory, fieldName):
        """Get the pretty display name for a field from FieldPrettyNames in qgisred_units.json."""
        if not fieldName:
            return fieldName

        fieldPrettyNames = self.loadUnitDefinitions().get("FieldPrettyNames", {})
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if category and category in fieldPrettyNames:
            if fieldName in fieldPrettyNames[category]:
                return fieldPrettyNames[category][fieldName]

        return fieldPrettyNames.get("Common", {}).get(fieldName, fieldName)

    def getFieldRawName(self, elementCategory, prettyName):
        """Get the raw field name from a pretty display name."""
        if not prettyName:
            return prettyName

        fieldPrettyNames = self.loadUnitDefinitions().get("FieldPrettyNames", {})
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if category and category in fieldPrettyNames:
            for rawName, displayName in fieldPrettyNames[category].items():
                if displayName == prettyName:
                    return rawName

        for rawName, displayName in fieldPrettyNames.get("Common", {}).items():
            if displayName == prettyName:
                return rawName

        return prettyName

    def getAllFieldPrettyNames(self, elementCategory=None):
        """Get all field pretty name mappings for a category, merged with Common."""
        fieldPrettyNames = self.loadUnitDefinitions().get("FieldPrettyNames", {})

        if elementCategory is None:
            return fieldPrettyNames

        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None
        result = dict(fieldPrettyNames.get("Common", {}))
        if category and category in fieldPrettyNames:
            result.update(fieldPrettyNames[category])

        return result

    """Units"""
    def loadUnitDefinitions(self):
        if QGISRedFieldUtils._unit_definitions is not None:
            return QGISRedFieldUtils._unit_definitions

        jsonPath = os.path.join(_plugin_root(), "defaults", "qgisred_units.json")

        if os.path.exists(jsonPath):
            try:
                with open(jsonPath, 'r', encoding='utf-8') as f:
                    QGISRedFieldUtils._unit_definitions = json.load(f)
            except Exception as e:
                QgsMessageLog.logMessage(f"Error loading unit definitions: {e}", "QGISRed", Qgis.Warning)
                QGISRedFieldUtils._unit_definitions = {}
        else:
            QGISRedFieldUtils._unit_definitions = {}

        return QGISRedFieldUtils._unit_definitions

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

    def getMassUnits(self):
        """Returns concentration units string, e.g. 'mg/L' or 'µg/L'."""
        units, _ = QgsProject.instance().readEntry("QGISRed", "project_massunits", "mg/L")
        return units

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

    def getFieldUnit(self, elementCategory, fieldName):
        """Get the unit abbreviation for a field based on element category and field name."""
        if not fieldName:
            return ""

        unitSystem = self.getUnits()
        unitDefs = self.loadUnitDefinitions()

        # Convert identifier to category name
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if not category or category not in unitDefs:
            return ""

        categoryUnits = unitDefs[category]

        # Get pretty name for the field
        prettyName = self.getFieldPrettyName(elementCategory, fieldName)

        # Search for matching property
        for _, unitInfo in categoryUnits.items():
            if not isinstance(unitInfo, dict):
                continue
            propertyName = unitInfo.get("property", "")
            if not propertyName:
                continue

            # Try exact match with field name
            if propertyName.lower() == fieldName.lower():
                unitData = unitInfo.get(unitSystem)
                if unitData:
                    return unitData.get("abbr", "")

            # Try exact match with pretty name
            if propertyName.lower() == prettyName.lower():
                unitData = unitInfo.get(unitSystem)
                if unitData:
                    return unitData.get("abbr", "")

            # Try prefix match (property is prefix of pretty name)
            if prettyName.lower().startswith(propertyName.lower()):
                unitData = unitInfo.get(unitSystem)
                if unitData:
                    return unitData.get("abbr", "")

        return ""

    def getFieldUnitFullName(self, elementCategory, fieldName):
        """Get the full unit name for a field (for tooltips)."""
        if not fieldName:
            return ""

        unitSystem = self.getUnits()
        unitDefs = self.loadUnitDefinitions()

        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if not category or category not in unitDefs:
            return ""

        categoryUnits = unitDefs[category]
        prettyName = self.getFieldPrettyName(elementCategory, fieldName)

        for _, unitInfo in categoryUnits.items():
            if not isinstance(unitInfo, dict):
                continue
            propertyName = unitInfo.get("property", "")
            if not propertyName:
                continue

            if (propertyName.lower() == fieldName.lower() or
                    propertyName.lower() == prettyName.lower() or
                    prettyName.lower().startswith(propertyName.lower())):
                unitData = unitInfo.get(unitSystem)
                if unitData:
                    name = unitData.get("name", "")
                    return name if name and name != "-" else ""

        return ""
