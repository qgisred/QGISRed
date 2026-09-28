# -*- coding: utf-8 -*-
"""Centralized display names for EPANET source type codes (CONCEN, MASS, ...).

Single source used by every place that shows a source's type (map tip,
Element Explorer) instead of each one translating it locally. See
qgisred_valve_types.py for the same pattern applied to valve types.

The English keys below are the *source* strings for pylupdate5 -- the actual
QCoreApplication.translate() calls that make them extractable live in
tools/qgisred_translatable_strings.py (dict values here are never literals
passed to translate(), so pylupdate can't see them on its own).
"""
from qgis.PyQt.QtCore import QCoreApplication

# EPANET source type code -> descriptive name (English source text).
SOURCE_TYPE_LABELS = {
    "CONCEN": "Concentration",
    "MASS": "Mass Booster",
    "FLOWPACED": "Flow Paced Booster",
    "SETPOINT": "Set Point Booster",
}


def getSourceTypeName(code, translate=True):
    """Descriptive name for an EPANET source type code.

    Codes not in SOURCE_TYPE_LABELS (including None/empty) are returned
    unchanged, the same fallback as getValveTypeName.

    getSourceTypeName("CONCEN")                -> "Concentration" (or translated)
    getSourceTypeName("CONCEN", translate=False) -> "Concentration" (always English)
    """
    if not code:
        return code
    label = SOURCE_TYPE_LABELS.get(code)
    if label is None:
        return code
    return QCoreApplication.translate("SourceTypeNames", label) if translate else label
