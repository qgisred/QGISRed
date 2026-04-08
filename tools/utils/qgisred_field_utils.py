# -*- coding: utf-8 -*-
import os
import csv as _csv

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsProject, QgsMessageLog, Qgis


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


_COMMON_PRETTY_NAMES = {
    "Id":      "Identifier",
    "Tag":     "Tag",
    "Descrip": "Description",
}

_CATEGORIZED_LAYER_IDS = {
    'qgisred_query_pipes_length',
    'qgisred_query_pipes_diameter',
}

_LAYER_ID_TO_FIELD = {
    # Pipes
    'qgisred_query_pipes_length':                    ('Pipes', 'Length'),
    'qgisred_query_pipes_diameter':                  ('Pipes', 'Diameter'),
    'qgisred_query_pipes_roughness':                 ('Pipes', 'RoughCoeff'),
    'qgisred_query_pipes_losscoeff':                 ('Pipes', 'LossCoeff'),
    'qgisred_query_pipes_material':                  ('Pipes', 'Material'),
    'qgisred_query_pipes_installdate':               ('Pipes', 'InstalDate'),
    'qgisred_query_pipes_age':                       ('Pipes', 'Age'),
    'qgisred_query_pipes_initstatus':                ('Pipes', 'IniStatus'),
    'qgisred_query_pipes_bulkcoeff':                 ('Pipes', 'BulkCoeff'),
    'qgisred_query_pipes_wallcoeff':                 ('Pipes', 'WallCoeff'),
    'qgisred_query_pipes_tag':                       ('Pipes', 'Tag'),
    # Tanks
    'qgisred_query_tanks_elevation':                 ('Tanks', 'Elevation'),
    'qgisred_query_tanks_level':                     ('Tanks', 'IniLevel'),
    'qgisred_query_tanks_diameter':                  ('Tanks', 'Diameter'),
    'qgisred_query_tanks_volume':                    ('Tanks', 'MinVolume'),
    'qgisred_query_tanks_volumecurve':               ('Tanks', 'IdVolCurve'),
    'qgisred_query_tanks_overflow':                  ('Tanks', 'Overflow'),
    'qgisred_query_tanks_mixmodel':                  ('Tanks', 'MixingMod'),
    'qgisred_query_tanks_mixingfraction':            ('Tanks', 'MixingFrac'),
    'qgisred_query_tanks_bulkcoeff':                 ('Tanks', 'ReactCoef'),
    'qgisred_query_tanks_initquality':               ('Tanks', 'IniQuality'),
    'qgisred_query_tanks_tag':                       ('Tanks', 'Tag'),
    # Reservoirs
    'qgisred_query_reservoirs_totalhead':            ('Reservoirs', 'TotalHead'),
    'qgisred_query_reservoirs_headpattern':          ('Reservoirs', 'IdHeadPatt'),
    'qgisred_query_reservoirs_initquality':          ('Reservoirs', 'IniQuality'),
    'qgisred_query_reservoirs_tag':                  ('Reservoirs', 'Tag'),
    # Junctions
    'qgisred_query_junctions_elevation':             ('Junctions', 'Elevation'),
    'qgisred_query_junctions_basedemand':            ('Junctions', 'BaseDem'),
    'qgisred_query_junctions_patterndemand':         ('Junctions', 'IdPattDem'),
    'qgisred_query_junctions_emittercoeff':          ('Junctions', 'EmittCoef'),
    'qgisred_query_junctions_initquality':           ('Junctions', 'IniQuality'),
    'qgisred_query_junctions_tag':                   ('Junctions', 'Tag'),
    # Valves
    'qgisred_query_valves_type':                     ('Valves', 'Type'),
    'qgisred_query_valves_diameter':                 ('Valves', 'Diameter'),
    'qgisred_query_valves_setting':                  ('Valves', 'Setting'),
    'qgisred_query_valves_headlosscurve':            ('Valves', 'IdHeadLoss'),
    'qgisred_query_valves_losscoeff':                ('Valves', 'LossCoeff'),
    'qgisred_query_valves_initstatus':               ('Valves', 'IniStatus'),
    'qgisred_query_valves_tag':                      ('Valves', 'Tag'),
    # Pumps
    'qgisred_query_pumps_headcurve':                 ('Pumps', 'IdHFCurve'),
    'qgisred_query_pumps_pumpcurve':                 ('Pumps', 'IdHFCurve'),
    'qgisred_query_pumps_power':                     ('Pumps', 'Power'),
    'qgisred_query_pumps_speed':                     ('Pumps', 'Speed'),
    'qgisred_query_pumps_speedpattern':              ('Pumps', 'IdSpeedPat'),
    'qgisred_query_pumps_initstatus':                ('Pumps', 'IniStatus'),
    'qgisred_query_pumps_efficiency':                ('Pumps', 'IdEffiCur'),
    'qgisred_query_pumps_effcurve':                  ('Pumps', 'IdEffiCur'),
    'qgisred_query_pumps_energyprice':               ('Pumps', 'EnergyPric'),
    'qgisred_query_pumps_pricepattern':              ('Pumps', 'IdPricePat'),
    'qgisred_query_pumps_tag':                       ('Pumps', 'Tag'),
    'qgisred_query_pumps_type':                      ('Pumps', 'Type'),
    # Sources
    'qgisred_query_sources_massinjection':           ('Sources', 'BaseValue'),
    # Service Connection
    'qgisred_query_serviceconnection_length':        ('Service Connection', 'Length'),
    'qgisred_query_serviceconnection_diameter':      ('Service Connection', 'Diameter'),
    'qgisred_query_serviceconnection_roughness':     ('Service Connection', 'Roughness'),
    'qgisred_query_serviceconnection_material':      ('Service Connection', 'Material'),
    'qgisred_query_serviceconnection_installdate':   ('Service Connection', 'InstDate'),
    'qgisred_query_serviceconnection_age':           ('Service Connection', 'Age'),
    'qgisred_query_serviceconnection_basedemand':    ('Service Connection', 'BaseDemand'),
    'qgisred_query_serviceconnection_patterndemand': ('Service Connection', 'Pattern'),
    'qgisred_query_serviceconnection_reliability':   ('Service Connection', 'Reliabilit'),
    'qgisred_query_serviceconnection_isactive':      ('Service Connection', 'IsActive'),
    'qgisred_query_serviceconnection_tag':           ('Service Connection', 'Tag'),
    # Isolation Valves
    'qgisred_query_isolationvalves_diameter':        ('Isolation Valves', 'Diameter'),
    'qgisred_query_isolationvalves_losscoeff':       ('Isolation Valves', 'LossCoeff'),
    'qgisred_query_isolationvalves_status':          ('Isolation Valves', 'Status'),
    'qgisred_query_isolationvalves_available':       ('Isolation Valves', 'Available'),
    'qgisred_query_isolationvalves_installdate':     ('Isolation Valves', 'InstDate'),
    'qgisred_query_isolationvalves_age':             ('Isolation Valves', 'Age'),
    'qgisred_query_isolationvalves_tag':             ('Isolation Valves', 'Tag'),
    # Meters
    'qgisred_query_meters_type':                     ('Meters', 'Type'),
    'qgisred_query_meters_isactive':                 ('Meters', 'IsActive'),
    'qgisred_query_meters_installdate':              ('Meters', 'InstDate'),
    'qgisred_query_meters_age':                      ('Meters', 'Age'),
    'qgisred_query_meters_tag':                      ('Meters', 'Tag'),
    # Result Nodes
    'qgisred_results_node_pressure':                 ('Nodes', 'Pressure'),
    'qgisred_results_node_head':                     ('Nodes', 'Head'),
    'qgisred_results_node_demand':                   ('Nodes', 'Demand'),
    'qgisred_results_node_quality':                  ('Nodes', 'Quality'),
    'qgisred_results_node_waterage':                 ('Nodes', 'Quality'),
    'qgisred_results_node_trace':                    ('Nodes', 'Quality'),
    # Result Links
    'qgisred_results_link_flow':                     ('Links', 'Flow'),
    'qgisred_results_link_velocity':                 ('Links', 'Velocity'),
    'qgisred_results_link_headloss':                 ('Links', 'HeadLoss'),
    'qgisred_results_link_unitheadloss':             ('Links', 'UnitHdLoss'),
    'qgisred_results_link_frictionfactor':           ('Links', 'FricFactor'),
    'qgisred_results_link_energy':                   ('Links', 'Energy'),
    'qgisred_results_link_status':                   ('Links', 'Status'),
    'qgisred_results_link_quality':                  ('Links', 'Quality'),
    'qgisred_results_link_waterage':                 ('Links', 'Quality'),
    'qgisred_results_link_trace':                    ('Links', 'Quality'),
    'qgisred_results_link_reactrate':                ('Links', 'ReactRate'),
}


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
        return QCoreApplication.translate("QGISRedFieldUtils", message)

    def getLayerSupportsCategorized(self, layerIdentifier):
        return layerIdentifier in _CATEGORIZED_LAYER_IDS

    """Options"""
    def getQualityModel(self):
        """Returns the quality model type: 'Chemical', 'Age', or 'Trace'."""
        model, _ = QgsProject.instance().readEntry("QGISRed", "project_qualitymodel", "Chemical")
        return model

    """Fields"""
    def getFieldPrettyName(self, elementCategory, fieldName):
        """Get the pretty display name for a field from the CSV-derived prettyNames."""
        if not fieldName:
            return fieldName

        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if category and category in prettyNames:
            if fieldName in prettyNames[category]:
                return prettyNames[category][fieldName]

        return prettyNames.get("Common", {}).get(fieldName, fieldName)

    def getFieldRawName(self, elementCategory, prettyName):
        """Get the raw field name from a pretty display name."""
        if not prettyName:
            return prettyName

        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if category and category in prettyNames:
            for rawName, displayName in prettyNames[category].items():
                if displayName == prettyName:
                    return rawName

        for rawName, displayName in prettyNames.get("Common", {}).items():
            if displayName == prettyName:
                return rawName

        return prettyName

    def getAllFieldPrettyNames(self, elementCategory=None):
        """Get all field pretty name mappings for a category, merged with Common."""
        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})

        if elementCategory is None:
            return prettyNames

        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None
        result = dict(prettyNames.get("Common", {}))
        if category and category in prettyNames:
            result.update(prettyNames[category])

        return result

    """Units"""
    def loadUnitDefinitions(self):
        # Validate cache: must be the new CSV-based structure (has "rows" list).
        # If it holds the old JSON structure (no "rows" key), reload from CSV.
        cached = QGISRedFieldUtils._unit_definitions
        if cached is not None and isinstance(cached.get("rows"), list):
            return cached

        csvPath = os.path.join(_plugin_root(), "defaults", "qgisred_units.csv")
        rows, prettyNames = [], {}

        if os.path.exists(csvPath):
            try:
                with open(csvPath, 'r', encoding='utf-8-sig', errors='replace') as f:
                    reader = _csv.reader(f, delimiter=';')
                    next(reader)  # skip header
                    for line in reader:
                        if len(line) < 9 or not line[0].strip():
                            continue
                        element   = line[0].strip()
                        prop      = line[1].strip()
                        fieldName = line[2].strip()
                        si_dec_s  = line[5].strip()
                        us_dec_s  = line[8].strip()
                        row = {
                            "element":   element,
                            "property":  prop,
                            "fieldName": fieldName,
                            "si_name":   line[3].strip(),
                            "si_abbr":   line[4].strip(),
                            "si_dec":    int(si_dec_s) if si_dec_s.isdigit() else None,
                            "us_name":   line[6].strip(),
                            "us_abbr":   line[7].strip(),
                            "us_dec":    int(us_dec_s) if us_dec_s.isdigit() else None,
                            "notes":     line[9].strip() if len(line) > 9 else "",
                        }
                        rows.append(row)
                        # prettyNames: primer match por (element_norm, fieldName)
                        normEl = element.replace(" ", "")
                        if normEl not in prettyNames:
                            prettyNames[normEl] = {}
                        if fieldName and fieldName not in prettyNames[normEl]:
                            prettyNames[normEl][fieldName] = prop
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error loading unit definitions: {e}", "QGISRed", Qgis.Warning)

        prettyNames["Common"] = dict(_COMMON_PRETTY_NAMES)
        # Alias plural para identifierToElementName que usa "ServiceConnections"
        if "ServiceConnection" in prettyNames:
            prettyNames.setdefault("ServiceConnections", prettyNames["ServiceConnection"])

        QGISRedFieldUtils._unit_definitions = {"rows": rows, "prettyNames": prettyNames}
        return QGISRedFieldUtils._unit_definitions

    def _getFirstRow(self, element, fieldName):
        """Return first CSV row matching (element, fieldName), or empty dict."""
        normEl = element.replace(" ", "").lower()
        for row in self.loadUnitDefinitions().get("rows", []):
            if (row["element"].replace(" ", "").lower() == normEl
                    and row["fieldName"] == fieldName):
                return row
        return {}

    def _getFirstRowByProperty(self, element, propertyName):
        """Return first CSV row matching (element, property display name), case-insensitive."""
        normEl = element.replace(" ", "").lower()
        propLow = propertyName.lower()
        for row in self.loadUnitDefinitions().get("rows", []):
            if (row["element"].replace(" ", "").lower() == normEl
                    and row["property"].lower() == propLow):
                return row
        return {}

    def _lookupFieldAbbr(self, element, fieldName, unitSystem):
        """Return abbreviation for first CSV row matching (element, fieldName)."""
        row = self._getFirstRow(element, fieldName) or self._getFirstRowByProperty(element, fieldName)
        if not row:
            return ""
        name = row["si_name"] if unitSystem == "SI" else row["us_name"]
        if name == "Same as Flow":
            return self._getFlowFieldAbbr()
        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return abbr if abbr and name not in ("Text", "") else ""

    def _getFlowFieldAbbr(self):
        """Return the exact flow unit abbreviation for the current project (e.g. lpm, gpm)."""
        flowUnit, _ = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")
        flowUnitUpper = flowUnit.upper()
        unitSystem = self.getUnits()
        for row in self.loadUnitDefinitions().get("rows", []):
            if row["element"] != "Links" or row["fieldName"] != "Flow":
                continue
            if flowUnitUpper in row["notes"].upper():
                abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
                return abbr if abbr else row["si_abbr"]  # CMS has no us_abbr
        return self._lookupFieldAbbr("Links", "Flow", unitSystem)

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

        field_key = _LAYER_ID_TO_FIELD.get(layerIdentifier)
        if not field_key:
            return ""

        element, fieldName = field_key
        return self._lookupFieldAbbr(element, fieldName, self.getUnits())

    def getResultPropertyUnit(self, category, prop_internal):
        """Returns unit abbreviation for a result property (category='Node'|'Link')."""
        prop_map = {
            ("Node", "Pressure"):   ("Nodes", "Pressure"),
            ("Node", "Head"):       ("Nodes", "Head"),
            ("Node", "Demand"):     ("Nodes", "Demand"),
            ("Node", "Quality"):    ("Nodes", "Quality"),
            ("Link", "Flow"):       ("Links", "Flow"),
            ("Link", "Velocity"):   ("Links", "Velocity"),
            ("Link", "HeadLoss"):   ("Links", "HeadLoss"),
            ("Link", "UnitHdLoss"): ("Links", "UnitHdLoss"),
            ("Link", "FricFactor"): ("Links", "FricFactor"),
            ("Link", "ReactRate"):  ("Links", "ReactRate"),
            ("Link", "Quality"):    ("Links", "Quality"),
        }
        field_key = prop_map.get((category, prop_internal))
        if not field_key:
            return ""
        element, fieldName = field_key

        # Return exact project flow unit (lpm, gpm, etc.)
        if element == "Links" and fieldName == "Flow":
            return self._getFlowFieldAbbr()

        unitSystem = self.getUnits()
        abbr = self._lookupFieldAbbr(element, fieldName, unitSystem)

        # Fallback for "Same as Flow" fields (Demand, etc.)
        if not abbr:
            row = self._getFirstRow(element, fieldName)
            name = row.get("si_name" if unitSystem == "SI" else "us_name", "")
            if name == "Same as Flow":
                return self._getFlowFieldAbbr()
        return abbr

    def getFieldUnit(self, elementCategory, fieldName):
        """Get the unit abbreviation for a field based on element category and field name."""
        if not fieldName:
            return ""

        unitSystem = self.getUnits()
        category = self.identifierToElementName.get(elementCategory, elementCategory)

        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return ""

        name = row["si_name"] if unitSystem == "SI" else row["us_name"]
        # "Same as Flow" → exact project flow unit
        if name == "Same as Flow":
            return self._getFlowFieldAbbr()

        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return abbr if abbr and name not in ("Text", "") else ""

    def getFieldUnitFullName(self, elementCategory, fieldName):
        """Get the full unit name for a field (for tooltips)."""
        if not fieldName:
            return ""

        unitSystem = self.getUnits()
        category = self.identifierToElementName.get(elementCategory, elementCategory)

        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return ""

        name = row["si_name"] if unitSystem == "SI" else row["us_name"]
        # "Same as Flow" is kept literal so callers (element_explorer_dock line 2509)
        # can detect it and resolve to project flow units themselves
        return name if name and name not in ("Text", "-") else ""

    def getFieldDecimals(self, elementCategory, fieldName, default=2):
        """Return decimal precision for a field per the CSV (SI Decimals / US Decimals columns).

        Parameters
        ----------
        elementCategory : str
            Layer identifier (e.g. 'qgisred_pipes') or element name.
        fieldName : str
            Raw DB column name or property display name.
        default : int
            Fallback when the CSV row has no decimal value.

        Returns
        -------
        int
        """
        if not fieldName:
            return default

        unitSystem = self.getUnits()
        category = self.identifierToElementName.get(elementCategory, elementCategory)

        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return default

        dec = row["si_dec"] if unitSystem == "SI" else row["us_dec"]
        return dec if dec is not None else default
