# -*- coding: utf-8 -*-
"""Helpers for node Demand in the results distribution histogram only."""
from qgis.core import NULL

_NODE_SPECIAL_TYPES = frozenset({"TANK", "RESERVOIR"})
_NON_JUNCTION_LAYER_IDS = frozenset({"qgisred_tanks", "qgisred_reservoirs"})


def is_junction_node_layer(layer_identifier=None):
    if not layer_identifier:
        return True
    return layer_identifier not in _NON_JUNCTION_LAYER_IDS


def is_junction_node_feature(feature, layer_identifier=None):
    if layer_identifier in _NON_JUNCTION_LAYER_IDS:
        return False
    field_names = feature.fields().names()
    if "Type" in field_names:
        node_type = str(feature["Type"] or "").strip().upper()
        return node_type not in _NODE_SPECIAL_TYPES
    return is_junction_node_layer(layer_identifier)


def junction_positive_node_demand(feature, layer_identifier=None):
    """Return positive junction demand for charts/stats, or None if excluded."""
    if not is_junction_node_feature(feature, layer_identifier):
        return None
    if "Demand" not in feature.fields().names():
        return None
    raw = feature["Demand"]
    if raw is None or raw == NULL:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0.0:
        return None
    return value

