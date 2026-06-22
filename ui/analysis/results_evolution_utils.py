# -*- coding: utf-8 -*-
from __future__ import annotations


_FLOW_ALIASES = frozenset({"Flow_Sig", "Flow_Unsig"})

_TANK_IDENTIFIER = "qgisred_tanks"


def evolution_prop_internal(category, field_name):
    field = (field_name or "").strip()
    if not field:
        return ""
    if field in _FLOW_ALIASES:
        return "Flow"
    return field


def map_status_series(values):
    mapped = []
    for status in values:
        text = str(status).upper()
        if "CLOSED" in text:
            mapped.append(0)
        elif "ACTIVE" in text:
            mapped.append(1)
        elif "OPEN" in text:
            mapped.append(2)
        else:
            mapped.append(0)
    return mapped


def tank_buttons_visibility(layer_identifier, prop_internal):
    is_tank = (layer_identifier or "") == _TANK_IDENTIFIER
    prop = (prop_internal or "").strip()
    show_volume = is_tank and prop == "Pressure"
    show_spill = is_tank and prop == "Demand"
    return show_volume, show_spill


def results_time_text_to_hours(text, single_period_label=""):
    text = (text or "").strip()
    if not text or text == single_period_label:
        return 0.0
    try:
        days = 0
        hms_text = text
        if "d" in text:
            parts = text.split()
            days = int(parts[0].replace("d", ""))
            hms_text = parts[1]
        hms = hms_text.split(":")
        if len(hms) == 2:
            return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60) / 3600.0
        if len(hms) != 3:
            return None
        return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])) / 3600.0
    except Exception:
        return None
