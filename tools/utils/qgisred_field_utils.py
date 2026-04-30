# -*- coding: utf-8 -*-
import os
import re
import csv as _csv
import shutil

from qgis.PyQt.QtCore import QCoreApplication
from .qgisred_filesystem_utils import QGISRedFileSystemUtils
from qgis.core import QgsProject, QgsMessageLog, Qgis


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


_COMMON_PRETTY_NAMES = {
    "Id":      "Identifier",
    "Tag":     "Tag",
    "Descrip": "Description",
}

_NON_CHEMICAL_MODELS = frozenset({"none", "trace", "age"})

_SUPERSCRIPT_TRANSLATION = str.maketrans("0123456789/", "⁰¹²³⁴⁵⁶⁷⁸⁹ᐟ")

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

        self.identifierToElementName = {
            'qgisred_pipes': 'Pipes',
            'qgisred_junctions': 'Junctions',
            'qgisred_demands': 'Multiple Demands',
            'qgisred_reservoirs': 'Reservoirs',
            'qgisred_tanks': 'Tanks',
            'qgisred_pumps': 'Pumps',
            'qgisred_valves': 'Valves',
            'qgisred_sources': 'Sources',
            'qgisred_serviceconnections': 'Service Connection',
            'qgisred_isolationvalves': 'Isolation Valves',
            'qgisred_meters': 'Meters',
            'qgisred_links': 'Links',
            'qgisred_nodes': 'Nodes',
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

    def getChemicalLabel(self):
        """Returns the chemical substance label defined in Analysis Options, or ''."""
        label, _ = QgsProject.instance().readEntry("QGISRed", "project_chemicallabel", "")
        return label.strip()

    def getTraceNode(self):
        """Returns the Trace source node ID defined in Analysis Options, or ''."""
        node, _ = QgsProject.instance().readEntry("QGISRed", "project_tracenode", "")
        return node.strip()

    def getQualityDisplayName(self):
        """Returns the display name for the Quality result field based on the quality model."""
        model = self.getQualityModel().upper()
        if model == "AGE":
            return self.tr("Age")
        if model == "TRACE":
            node = self.getTraceNode()
            return self.tr("Trace %1").replace("%1", str(node)).strip() if node else self.tr("Trace")
        # CHEMICAL or any other active model
        label = self.getChemicalLabel()
        return label if label else self.tr("Chemical")

    def showReactRate(self):
        """ReactRate is only meaningful for Chemical quality simulations."""
        return self.getQualityModel().upper() not in ("NONE", "AGE", "TRACE")

    """Fields"""
    def getFieldPrettyName(self, elementCategory, fieldName, translate=True):
        """Get the pretty display name for a field from the CSV-derived prettyNames."""
        if not fieldName:
            return fieldName

        # Dynamic override: Quality in result layers uses the quality-model-specific name
        if translate and fieldName == "Quality":
            category = self.identifierToElementName.get(elementCategory, elementCategory)
            if category in ("Nodes", "Links"):
                if self.getQualityModel().upper() != "NONE":
                    return self.getQualityDisplayName()

        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        category = category.replace(" ", "") if category else None

        if category and category in prettyNames:
            if fieldName in prettyNames[category]:
                prop = prettyNames[category][fieldName]
                return QCoreApplication.translate("FieldPrettyNames", prop) if translate else prop

        prop = prettyNames.get("Common", {}).get(fieldName, fieldName)
        return QCoreApplication.translate("FieldPrettyNames", prop) if translate else prop

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

        _CSV_FILENAME = "qgisred_properties_units_decimals.csv"
        globalDir = os.path.join(QGISRedFileSystemUtils().getQGISRedFolder(), "global_defaults")
        csvPath = os.path.join(globalDir, _CSV_FILENAME)
        fallback = os.path.join(_plugin_root(), "defaults", _CSV_FILENAME)
        if os.path.exists(fallback):
            os.makedirs(globalDir, exist_ok=True)
            if not os.path.exists(csvPath) or os.path.getmtime(fallback) > os.path.getmtime(csvPath):
                shutil.copy2(fallback, csvPath)
        rows, prettyNames = [], {}

        if os.path.exists(csvPath):
            try:
                with open(csvPath, 'r', encoding='utf-8-sig', errors='replace') as f:
                    reader = _csv.reader(f, delimiter=',')
                    next(reader)  # skip header
                    for line in reader:
                        if len(line) < 9 or not line[0].strip():
                            continue
                        element   = line[0].strip()
                        fieldName = line[1].strip()
                        prop      = line[2].strip()
                        si_dec_s  = line[5].strip()
                        us_dec_s  = line[8].strip()
                        row = {
                            "element":         element,
                            "fieldName":       fieldName,
                            "property":        prop,
                            "si_name":         line[3].strip(),
                            "si_abbr":         line[4].strip(),
                            "si_dec":          int(si_dec_s) if si_dec_s.isdigit() else None,
                            "us_name":         line[6].strip(),
                            "us_abbr":         line[7].strip(),
                            "us_dec":          int(us_dec_s) if us_dec_s.isdigit() else None,
                            "condition_value": line[9].strip()  if len(line) > 9  else "",
                            "notes":           line[10].strip() if len(line) > 10 else "",
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
        """Return CSV row matching (element, fieldName).

        When multiple rows discriminate on the headloss formula (notes ==
        'HeadLoss formulae'), the row matching project_headloss is returned.
        """
        normEl = element.replace(" ", "").lower()
        matches = [row for row in self.loadUnitDefinitions().get("rows", [])
                   if row["element"].replace(" ", "").lower() == normEl
                   and row["fieldName"] == fieldName]
        if not matches:
            return {}
        if len(matches) > 1 and all(row["notes"] == "HeadLoss formulae" for row in matches):
            active = QgsProject.instance().readEntry("QGISRed", "project_headloss", "D-W")[0]
            for row in matches:
                if row["condition_value"].lower() == active.lower():
                    return row
        return matches[0]

    def _getRowByCondition(self, element, fieldName, conditionValue):
        """Return the CSV row matching (element, fieldName, conditionValue).

        Within a given (element, fieldName) pair, conditionValue is always unique,
        so no conditionType discriminator is needed.
        Falls back to the first unconditional row for that (element, fieldName), then
        to _getFirstRow(), so callers always get a usable result even for unknown values.
        FieldName comparison is case-insensitive to tolerate minor CSV inconsistencies.
        """
        normEl = element.replace(" ", "").lower()
        cvLow  = conditionValue.lower()
        for row in self.loadUnitDefinitions().get("rows", []):
            if row["element"].replace(" ", "").lower() != normEl:
                continue
            if row["fieldName"].lower() != fieldName.lower():
                continue
            if row["condition_value"].lower() == cvLow:
                return row
        # Fallback 1: first unconditional row (condition_value is empty)
        for row in self.loadUnitDefinitions().get("rows", []):
            if (row["element"].replace(" ", "").lower() == normEl
                    and row["fieldName"].lower() == fieldName.lower()
                    and not row["condition_value"]):
                return row
        # Fallback 2: absolute first match
        return self._getFirstRow(element, fieldName)

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
        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return self._resolveAbbr(abbr)

    def _resolveAbbr(self, abbr):
        """Resolve all 'See X' tokens in an abbreviation string.

        Handles composite abbreviations like 'See FlowUnits/sqr(See PressUnits)'
        by replacing every known token with its runtime value.
        """
        if not abbr:
            return abbr
        if "See " in abbr:
            abbr = abbr.replace("See FlowUnits", self._getFlowFieldAbbr())
            abbr = abbr.replace("See PressUnits", self._getPressureFieldAbbr())
            abbr = abbr.replace("See MassUnits", self._getMassAbbr())
            abbr = abbr.replace("See Currency", self._getCurrencyAbbr())
        abbr = re.sub(r'sqr\(([^)]+)\)', r'√\1', abbr)
        abbr = self._formatExponents(abbr)
        return abbr

    def _formatExponents(self, text):
        """Convert ASCII exponent notation in unit strings to Unicode superscripts.

        Supports '^(N/M)' (parenthesised, including fractions) and '^N' (bare digits),
        e.g. 's/m^(1/3)' -> 's/m¹ᐟ³', 'm^2' -> 'm²'.
        """
        text = re.sub(r'\^\(([0-9/]+)\)', lambda m: m.group(1).translate(_SUPERSCRIPT_TRANSLATION), text)
        text = re.sub(r'\^(\d+)', lambda m: m.group(1).translate(_SUPERSCRIPT_TRANSLATION), text)
        return text

    def _getCurrencyAbbr(self):
        """Return the currency abbreviation (first Global/Currency row in the CSV)."""
        row = self._getFirstRow("Global", "Currency")
        if not row:
            return ""
        unitSystem = self.getUnits()
        return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]

    def _getMassAbbr(self):
        """Return the mass unit abbreviation for the current project (e.g. 'mg' or 'ug').

        Looks up the Global/Mass CSV row whose ConditionValue matches the project
        concentration units (case-insensitive). Falls back to splitting the
        concentration units string if no CSV row is found.
        """
        concUnits = self.getConcentrationUnits()
        row = self._getRowByCondition("Global", "MassUnits", concUnits)
        if row and row["condition_value"].lower() == concUnits.lower():
            unitSystem = self.getUnits()
            return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return ""

    def _getQualityResultAbbr(self, element):
        """Return unit abbreviation for Quality result fields based on the quality model.

        Chemical (or any model not in None/Trace/Age) → resolved mass/L abbr
        Trace → %
        Age → hr
        None → ""
        """
        modelLow = self.getQualityModel().lower()
        if modelLow == "none":
            return ""
        if modelLow in ("trace", "age"):
            condVal = modelLow.capitalize()  # "Trace" or "Age" — matches CSV ConditionValue
        else:
            condVal = "Chemical"
        row = self._getRowByCondition(element, "Quality", condVal)
        if not row:
            return ""
        unitSystem = self.getUnits()
        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return self._resolveAbbr(abbr)

    def _getIniQualityAbbr(self, element):
        """Return unit abbreviation for IniQuality fields.

        Returns "" if the quality model is None, Trace, or Age (IniQuality is inapplicable).
        For Chemical (or any other model name), resolves the mass/L abbreviation.
        """
        if self.getQualityModel().lower() in _NON_CHEMICAL_MODELS:
            return ""
        row = self._getFirstRow(element, "IniQuality")
        if not row:
            return ""
        unitSystem = self.getUnits()
        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return self._resolveAbbr(abbr)

    def _getPressureFieldAbbr(self):
        """Return the pressure unit abbreviation for the current project.

        Defaults to METERS (SI) or PSI (US) until the exact pressure unit setting
        is exposed from the native library.
        """
        unitSystem = self.getUnits()
        condVal = "METERS" if unitSystem == "SI" else "PSI"
        row = self._getRowByCondition("Global", "PressUnits", condVal)
        if row:
            return row["si_abbr"] or row["us_abbr"]
        return self._lookupFieldAbbr("Global", "PressUnits", unitSystem)

    def _getFlowFieldAbbr(self):
        """Return the exact flow unit abbreviation for the current project (e.g. lpm, gpm).

        The CSV has one row per flow unit (not SI+US in the same row), with ConditionValue
        equal to the EPANET unit code (LPS, GPM, MLD, etc.). The non-empty abbr in that
        row is the abbreviation to display.
        """
        flowUnit, _ = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")
        row = self._getRowByCondition("Global", "FlowUnits", flowUnit)
        if row:
            return row["si_abbr"] or row["us_abbr"]
        return self._lookupFieldAbbr("Global", "FlowUnits", self.getUnits())

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

    def getConcentrationUnits(self):
        """Returns concentration units string, e.g. 'mg/L' or 'µg/L'."""
        units, _ = QgsProject.instance().readEntry("QGISRed", "project_concentrationunits", "mg/L")
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

        if fieldName == "Quality":
            return self._getQualityResultAbbr(element)
        if element == "Links" and fieldName == "Flow":
            return self._getFlowFieldAbbr()
        if element == "Nodes" and fieldName == "Pressure":
            return self._getPressureFieldAbbr()

        unitSystem = self.getUnits()
        return self._lookupFieldAbbr(element, fieldName, unitSystem)

    def getFieldUnit(self, elementCategory, fieldName):
        """Get the unit abbreviation for a field based on element category and field name."""
        if not fieldName:
            return ""

        unitSystem = self.getUnits()
        category = self.identifierToElementName.get(elementCategory, elementCategory)

        if fieldName == "IniQuality":
            return self._getIniQualityAbbr(category)

        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return ""

        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return self._resolveAbbr(abbr)

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

    def isTextField(self, elementCategory, fieldName):
        if not fieldName:
            return False
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return False
        name = (row["si_name"] or row["us_name"] or "").strip().lower()
        return name in ("text", "year as text", "-")

    def isDateField(self, elementCategory, fieldName):
        if not fieldName:
            return False
        category = self.identifierToElementName.get(elementCategory, elementCategory)
        row = self._getFirstRow(category, fieldName) or self._getFirstRowByProperty(category, fieldName)
        if not row:
            return False
        name = (row["si_name"] or row["us_name"] or "").strip().lower()
        return name == "year as text"

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
