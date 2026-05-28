# -*- coding: utf-8 -*-
import os
import re
import csv as _csv
import shutil

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsMessageLog, Qgis
from .qgisred_filesystem_utils import QGISRedFileSystemUtils
from .qgisred_project_utils import QGISRedProjectUtils

# Maps QGIS input-layer identifiers to canonical element names used in the CSV.
IDENTIFIER_TO_ELEMENT = {
    'qgisred_pipes':              'Pipes',
    'qgisred_junctions':          'Junctions',
    'qgisred_demands':            'Multiple Demands',
    'qgisred_reservoirs':         'Reservoirs',
    'qgisred_tanks':              'Tanks',
    'qgisred_pumps':              'Pumps',
    'qgisred_valves':             'Valves',
    'qgisred_sources':            'Sources',
    'qgisred_serviceconnections': 'Service Connection',
    'qgisred_isolationvalves':    'Isolation Valves',
    'qgisred_meters':             'Meters',
    'qgisred_links':              'Links',
    'qgisred_nodes':              'Nodes',
}

# Maps QGIS query/result layer identifiers to (element, fieldName) for use
# with the 4 main QGISRedFieldUtils methods.
LAYER_ID_TO_FIELD = {
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

_COMMON_PRETTY_NAMES = {
    "Id":      "Identifier",
    "Tag":     "Tag",
    "Descrip": "Description",
}
_NON_CHEMICAL_MODELS = frozenset({"none", "trace", "age"})
_CHEMICAL_ONLY_FIELDS = frozenset({"IniQuality", "ReactRate"})
_SUPERSCRIPT_TRANSLATION = str.maketrans("0123456789/", "⁰¹²³⁴⁵⁶⁷⁸⁹ᐟ")

def normalize_element(element: str) -> str:
    """Return the canonical element name used in the CSV for any identifier form.

    Handles three cases:
      - QGIS layer identifier  ('qgisred_pipes'  -> 'Pipes')
      - Singular result name   ('Node' -> 'Nodes', 'Link' -> 'Links')
      - Already-canonical name ('Pipes', 'Nodes', …) returned unchanged

    Call this before passing an element to the four main QGISRedFieldUtils methods
    whenever the identifier may come from a QGIS layer or a result category string.

    Example::

        el = normalize_element(layerIdentifier)
        abbr = utils.getUnitAbbreviation(el, fieldName)
    """
    mapped = IDENTIFIER_TO_ELEMENT.get(element)
    if mapped:
        return mapped
    if element == "Node":
        return "Nodes"
    if element == "Link":
        return "Links"
    return element

def resolve_layer_id(layer_identifier: str):
    """Return (element, fieldName) for a QGIS layer identifier, or None if not mapped.

    Use the returned tuple to call the QGISRedFieldUtils main methods:

        field = resolve_layer_id(layerIdentifier)
        if field:
            abbr = utils.getUnitAbbreviation(*field)
    """
    return LAYER_ID_TO_FIELD.get(layer_identifier)

def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

class QGISRedFieldUtils:
    """Utilities for field metadata (pretty names, units, decimals).

    Main public API — all require a canonical element name and a fieldName:
        getProperty(element, fieldName, translate=True) -> str
        getUnitAbbreviation(element, fieldName)         -> str
        getUnitFullName(element, fieldName)             -> str
        getDecimals(element, fieldName, default=2)      -> int

    Module-level helpers to resolve identifiers before calling the main methods:
        normalize_element(element)       -> canonical name  ('qgisred_pipes' -> 'Pipes')
        resolve_layer_id(layerIdentifier)-> (element, fieldName) tuple or None
    """

    _unit_definitions = None

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    # ------------------------------------------------------------------ #
    # Main public API                                                      #
    # ------------------------------------------------------------------ #

    def getProperty(self, element: str, fieldName: str, translate: bool = True) -> str:
        """Return the human-readable display name for a field.

        ``element`` must be a canonical element name (e.g. 'Pipes', 'Nodes').
        Use ``normalize_element()`` first if you have a QGIS layer identifier.

        For the Quality field on Nodes/Links layers the name is determined
        by the project's quality model (Chemical / Age / Trace) and resolved
        automatically; pass translate=False to get the raw English string.

        getProperty('Pipes',      'Length')   -> 'Length'  (or translated)
        getProperty('Junctions',  'EmittCoef')-> 'Emitter Coefficient'
        getProperty('Nodes',      'Quality')  -> 'Chlorine'  (if chemical label set)
        """
        if not fieldName:
            return fieldName

        if translate and fieldName == "Quality" and element in ("Nodes", "Links"):
            if QGISRedProjectUtils.getQualityModel().upper() != "NONE":
                return QGISRedProjectUtils.getQualityDisplayName()

        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})
        normEl = element.replace(" ", "")

        if normEl in prettyNames and fieldName in prettyNames[normEl]:
            prop = prettyNames[normEl][fieldName]
            return QCoreApplication.translate("FieldPrettyNames", prop) if translate else prop

        prop = prettyNames.get("Common", {}).get(fieldName, fieldName)
        return QCoreApplication.translate("FieldPrettyNames", prop) if translate else prop

    def getUnitAbbreviation(self, element: str, fieldName: str, conditionFeature: str = "") -> str:
        """Return the unit abbreviation for a field, respecting SI/US project setting.

        ``element`` must be a canonical element name (e.g. 'Pipes', 'Nodes').
        Use ``normalize_element()`` first if you have a QGIS layer identifier.

        ``conditionFeature`` is an optional per-feature attribute value that selects
        the correct CSV row for fields whose unit depends on feature-level data
        (e.g. pass the valve type for Valves.Setting).

        getUnitAbbreviation('Pipes',  'Length')            -> 'm'  (SI) / 'ft'  (US)
        getUnitAbbreviation('Links',  'Flow')              -> 'lps'  (if project unit = LPS)
        getUnitAbbreviation('Nodes',  'Pressure')          -> 'm'  (SI) / 'psi'  (US)
        getUnitAbbreviation('Nodes',  'Quality')           -> 'mg/L'  (Chemical, SI, mg/L conc.)
        getUnitAbbreviation('Valves', 'Setting', 'PRV')    -> 'm'  (SI pressure)
        """
        row = self._resolveRow(element, fieldName, conditionFeature)
        if not row:
            return ""
        unitSystem = QGISRedProjectUtils.getUnits()
        abbr = row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return self._resolveAbbr(abbr)

    def getUnitFullName(self, element: str, fieldName: str, conditionFeature: str = "") -> str:
        """Return the full unit name for a field (intended for tooltips).

        ``element`` must be a canonical element name (e.g. 'Pipes', 'Nodes').
        Use ``normalize_element()`` first if you have a QGIS layer identifier.

        ``conditionFeature`` is an optional per-feature attribute value (see
        ``getUnitAbbreviation`` for details).

        Returns '' for text/date fields and fields without a defined unit.

        getUnitFullName('Pipes', 'Length')   -> 'Meters'  (SI) / 'Feet'  (US)
        getUnitFullName('Pipes', 'Material') -> ''
        """
        if not fieldName:
            return ""
        row = self._resolveRow(element, fieldName, conditionFeature)
        if not row:
            return ""
        unitSystem = QGISRedProjectUtils.getUnits()
        name = row["si_name"] if unitSystem == "SI" else row["us_name"]
        if not name or name in ("Text", "-"):
            return ""
        return QCoreApplication.translate("UnitFullNames", name)

    def getDecimals(self, element: str, fieldName: str, default: int = 2, conditionFeature: str = "") -> int:
        """Return the display decimal precision for a field.

        ``element`` must be a canonical element name (e.g. 'Pipes', 'Nodes').
        Use ``normalize_element()`` first if you have a QGIS layer identifier.

        ``conditionFeature`` is an optional per-feature attribute value (see
        ``getUnitAbbreviation`` for details).

        Returns ``default`` when the CSV has no entry for the field or when the
        field is inapplicable for the current project configuration.

        getDecimals('Pipes', 'Diameter')            -> 1  (SI)
        getDecimals('Links', 'Flow')                -> 2  (LPS) / 1  (GPM)
        getDecimals('Nodes', 'Pressure')            -> 2
        getDecimals('Nodes', 'Quality', default=3)  -> 2  (Chemical) / 1  (Age/Trace)
        """
        return self._rowDecimals(self._resolveRow(element, fieldName, conditionFeature), default)

    def getFieldRawName(self, element: str, prettyName: str) -> str:
        """Return the raw field name for a given pretty display name (inverse of getProperty).

        ``element`` must be a canonical element name. Use ``normalize_element()`` first
        if you have a QGIS layer identifier.
        """
        if not prettyName:
            return prettyName

        normEl = element.replace(" ", "")
        prettyNames = self.loadUnitDefinitions().get("prettyNames", {})

        if normEl in prettyNames:
            for rawName, displayName in prettyNames[normEl].items():
                if displayName == prettyName:
                    return rawName

        for rawName, displayName in prettyNames.get("Common", {}).items():
            if displayName == prettyName:
                return rawName

        return prettyName

    # ------------------------------------------------------------------ #
    # Additional public methods                                            #
    # ------------------------------------------------------------------ #

    def isTextField(self, element: str, fieldName: str) -> bool:
        """Return True if the field holds text (no numeric formatting should be applied).

        ``element`` must be a canonical element name. Use ``normalize_element()`` first
        if you have a QGIS layer identifier.
        """
        if not fieldName:
            return False
        row = self._getFirstRow(element, fieldName) or self._getFirstRowByProperty(element, fieldName)
        if not row:
            return False
        name = (row["si_name"] or row["us_name"] or "").strip().lower()
        return name in ("text", "year as text", "-")

    def isDateField(self, element: str, fieldName: str) -> bool:
        """Return True if the field holds a year-as-text date value.

        ``element`` must be a canonical element name. Use ``normalize_element()`` first
        if you have a QGIS layer identifier.
        """
        if not fieldName:
            return False
        row = self._getFirstRow(element, fieldName) or self._getFirstRowByProperty(element, fieldName)
        if not row:
            return False
        name = (row["si_name"] or row["us_name"] or "").strip().lower()
        return name == "year as text"

    # ------------------------------------------------------------------ #
    # CSV loading and row lookup                                           #
    # ------------------------------------------------------------------ #

    def loadUnitDefinitions(self):
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
                        normEl = element.replace(" ", "")
                        if normEl not in prettyNames:
                            prettyNames[normEl] = {}
                        if fieldName and fieldName not in prettyNames[normEl]:
                            prettyNames[normEl][fieldName] = prop
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error loading unit definitions: {e}", "QGISRed", Qgis.Warning)

        prettyNames["Common"] = dict(_COMMON_PRETTY_NAMES)
        if "ServiceConnection" in prettyNames:
            prettyNames.setdefault("ServiceConnections", prettyNames["ServiceConnection"])

        QGISRedFieldUtils._unit_definitions = {"rows": rows, "prettyNames": prettyNames}
        return QGISRedFieldUtils._unit_definitions

    def _resolveRow(self, element: str, fieldName: str, conditionFeature: str = "") -> dict:
        """Return the CSV row for (element, fieldName) given current project settings.

        Returns {} if the field is inapplicable for the current project configuration
        (e.g. IniQuality / ReactRate when quality model is not Chemical, or Quality
        when quality model is None).
        All condition-dependent lookups (flow unit, pressure unit, quality model,
        headloss formula) are resolved here so callers only need to extract the column.

        ``conditionFeature`` is an optional per-feature attribute value used when the
        CSV row selection depends on a feature-level property (e.g. valve type for
        Setting, curve type for XValue/Yvalue). When omitted, the first matching row
        is returned.
        """
        if fieldName in _CHEMICAL_ONLY_FIELDS:
            if QGISRedProjectUtils.getQualityModel().lower() in _NON_CHEMICAL_MODELS:
                return {}

        if fieldName in ("Flow", "Demand"):
            return self._getRowByCondition("Global", "FlowUnits", QGISRedProjectUtils.getFlowUnit())

        if fieldName == "Pressure":
            condVal = "METERS" if QGISRedProjectUtils.getUnits() == "SI" else "PSI"
            return self._getRowByCondition("Global", "PressUnits", condVal)

        if fieldName == "Quality":
            modelLow = QGISRedProjectUtils.getQualityModel().lower()
            if modelLow == "none":
                return {}
            condVal = modelLow.capitalize() if modelLow in ("trace", "age") else "Chemical"
            return self._getRowByCondition(element, "Quality", condVal)

        if conditionFeature:
            return self._getRowByCondition(element, fieldName, conditionFeature)
        return self._getFirstRow(element, fieldName) or self._getFirstRowByProperty(element, fieldName)

    def _getFirstRow(self, element, fieldName):
        """Return the CSV row matching (element, fieldName).

        When multiple rows exist for the same (element, fieldName) and all are
        discriminated by the headloss formula (notes == 'HeadLoss formulae'),
        the row matching the project setting is returned.
        """
        normEl = element.replace(" ", "").lower()
        matches = [row for row in self.loadUnitDefinitions().get("rows", [])
                   if row["element"].replace(" ", "").lower() == normEl
                   and row["fieldName"] == fieldName]
        if not matches:
            return {}
        if len(matches) > 1 and all(row["notes"] == "HeadLoss formulae" for row in matches):
            active = QGISRedProjectUtils.getHeadlossFormula()
            for row in matches:
                if row["condition_value"].lower() == active.lower():
                    return row
        return matches[0]

    def _getRowByCondition(self, element, fieldName, conditionValue):
        """Return the CSV row matching (element, fieldName, conditionValue).

        Falls back to the first unconditional row, then to _getFirstRow().
        fieldName comparison is case-insensitive.
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
        for row in self.loadUnitDefinitions().get("rows", []):
            if (row["element"].replace(" ", "").lower() == normEl
                    and row["fieldName"].lower() == fieldName.lower()
                    and not row["condition_value"]):
                return row
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

    # ------------------------------------------------------------------ #
    # Private resolution helpers                                           #
    # ------------------------------------------------------------------ #

    def _rowDecimals(self, row, default=2):
        if not row:
            return default
        unitSystem = QGISRedProjectUtils.getUnits()
        dec = row["si_dec"] if unitSystem == "SI" else row["us_dec"]
        return dec if dec is not None else default

    def _resolveAbbr(self, abbr):
        """Expand 'See X' tokens in an abbreviation string using project settings."""
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
        """Convert ASCII exponent notation to Unicode superscripts (e.g. 'm^2' -> 'm²')."""
        text = re.sub(r'\^\(([0-9/]+)\)', lambda m: m.group(1).translate(_SUPERSCRIPT_TRANSLATION), text)
        text = re.sub(r'\^(\d+)', lambda m: m.group(1).translate(_SUPERSCRIPT_TRANSLATION), text)
        return text

    def _getFlowFieldAbbr(self):
        """Return the flow unit abbreviation for the current project (e.g. 'lps', 'gpm')."""
        flowUnit = QGISRedProjectUtils.getFlowUnit()
        row = self._getRowByCondition("Global", "FlowUnits", flowUnit)
        if row:
            return row["si_abbr"] or row["us_abbr"]
        unitSystem = QGISRedProjectUtils.getUnits()
        row = self._getFirstRow("Global", "FlowUnits")
        if not row:
            return ""
        return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]

    def _getPressureFieldAbbr(self):
        """Return the pressure unit abbreviation for the current project ('m' or 'psi')."""
        unitSystem = QGISRedProjectUtils.getUnits()
        condVal = "METERS" if unitSystem == "SI" else "PSI"
        row = self._getRowByCondition("Global", "PressUnits", condVal)
        if row:
            return row["si_abbr"] or row["us_abbr"]
        row = self._getFirstRow("Global", "PressUnits")
        if not row:
            return ""
        return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]

    def _getMassAbbr(self):
        """Return the mass unit abbreviation for the current project ('mg' or 'µg')."""
        concUnits = QGISRedProjectUtils.getConcentrationUnits()
        row = self._getRowByCondition("Global", "MassUnits", concUnits)
        if row and row["condition_value"].lower() == concUnits.lower():
            unitSystem = QGISRedProjectUtils.getUnits()
            return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]
        return ""

    def _getCurrencyAbbr(self):
        """Return the currency abbreviation (first Global/Currency row in the CSV)."""
        row = self._getFirstRow("Global", "Currency")
        if not row:
            return ""
        unitSystem = QGISRedProjectUtils.getUnits()
        return row["si_abbr"] if unitSystem == "SI" else row["us_abbr"]

