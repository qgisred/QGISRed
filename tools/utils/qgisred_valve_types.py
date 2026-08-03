# -*- coding: utf-8 -*-
"""Centralized display names for EPANET valve type codes (PRV/PSV/PBV/FCV/TCV/GPV, CV).

Single source used by every dialog that shows a valve's Type (Group Edit,
Element Explorer, Queries by Properties, Statistics, Thematic Maps/Labels)
instead of each one showing the raw 3-letter code or translating it locally
— the previous pattern for link status (Open/Closed/Active, scattered
self.tr() calls per dialog) is exactly the drift this avoids.

Long names and abbreviations come from EPANET's own official manuals
(Spanish/French: Fernando Martínez-Alzamora, UPV; Portuguese: EPANET Brasil,
LENHS-UFPB — see i18n/QGISRed_PT_BR_glossary.md), not literal word-by-word
translation: e.g. FCV is "Controladora de Caudal" in the Spanish manual, not
"Limitadora", and the French manual names PRV/PSV by what they stabilize
("Stabilisatrice Aval/Amont"), unrelated word-for-word to "reductora".

The English keys below are the *source* strings for pylupdate5 — the actual
QCoreApplication.translate() calls that make them extractable live in
tools/qgisred_translatable_strings.py (dict values here are never literals
passed to translate(), so pylupdate can't see them on its own). Where a
language has no official localized abbreviation (all of French; PBV/TCV/GPV
in Portuguese), its .ts entry for VALVE_TYPE_ABBREVIATIONS is left
unfinished/absent on purpose: Qt falls back to the source text, i.e. the
plain EPANET code, which is exactly the desired fallback — not an invented
abbreviation.
"""
from qgis.PyQt.QtCore import QCoreApplication

# EPANET code -> long descriptive name (English source text), singular, without
# the word "Valve" (the field itself is already labelled "Valve Type").
VALVE_TYPE_LONG_NAMES = {
    "PRV": "Pressure Reducing",
    "PSV": "Pressure Sustaining",
    "PBV": "Pressure Breaker",
    "FCV": "Flow Control",
    "TCV": "Throttle Control",
    "GPV": "General Purpose",
    "CV": "Check",
}


def getValveTypeName(code, translate=True):
    """Long descriptive name for an EPANET valve type code.

    Codes not in VALVE_TYPE_LONG_NAMES (including None/empty) are returned
    unchanged — several callers (e.g. Queries by Properties) pull the value
    live from a feature attribute, which may hold something other than a
    recognised valve type code.

    getValveTypeName("PRV")               -> "Pressure Reducing" (or translated)
    getValveTypeName("PRV", translate=False) -> "Pressure Reducing" (always English)
    """
    if not code:
        return code
    name = VALVE_TYPE_LONG_NAMES.get(code)
    if name is None:
        return code
    return QCoreApplication.translate("ValveTypeNames", name) if translate else name


def getValveTypeAbbreviation(code):
    """Short, localized abbreviation — for read-only displays where the long
    name doesn't fit (map labels, chart/histogram axes). Falls back to the
    plain EPANET code where the active language has no official localized
    abbreviation (see module docstring), and to the code unchanged for
    values outside VALVE_TYPE_LONG_NAMES.

    getValveTypeAbbreviation("PRV") -> "VRP" (Spanish/Portuguese) or "PRV" (English/French)
    """
    if not code or code not in VALVE_TYPE_LONG_NAMES:
        return code
    return QCoreApplication.translate("ValveTypeAbbreviations", code)
