# -*- coding: utf-8 -*-
"""Centralized display names for meter type codes (Manometer, Flowmeter, ...).

Single source used by every place that shows a meter's type (map tip,
Element Explorer) instead of each one translating it locally.

The English keys below are the *source* strings for pylupdate5 -- the actual
QCoreApplication.translate() calls that make them extractable live in
tools/qgisred_translatable_strings.py (dict values here are never literals
passed to translate(), so pylupdate can't see them on its own). See
qgisred_valve_types.py for the same pattern applied to valve types.
"""
from qgis.PyQt.QtCore import QCoreApplication

# Meter type code (as stored by the DLL, e.g. Meters.MeterType) -> descriptive
# name (English source text).
METER_TYPE_LABELS = {
    "Manometer": "Manometer",
    "Flowmeter": "Flowmeter",
    "Countermeter": "Countermeter",
    "LevelSensor": "Level Sensor",
    "DifferentialManometer": "Differential Manometer",
    "QualitySensor": "Quality Sensor",
    "EnergySensor": "Energy Sensor",
    "StatusSensor": "Status Sensor",
    "ValveOpening": "Valve Opening",
    "Tachometer": "Tachometer",
}


def getMeterTypeName(code, translate=True):
    """Descriptive name for a meter type code.

    Codes not in METER_TYPE_LABELS (including None/empty) are returned
    unchanged, the same fallback as getValveTypeName.

    getMeterTypeName("Manometer")                -> "Manometer" (or translated)
    getMeterTypeName("Manometer", translate=False) -> "Manometer" (always English)
    """
    if not code:
        return code
    label = METER_TYPE_LABELS.get(code)
    if label is None:
        return code
    return QCoreApplication.translate("MeterTypeNames", label) if translate else label
