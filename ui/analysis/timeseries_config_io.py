# -*- coding: utf-8 -*-
"""Serialization of the TimeSeries chart configuration to/from XML (.cfg).

Pure module (no heavy QGIS dependencies) so it stays unit-testable: it only
deals with plain dicts for curves and the axis/general dataclasses. Color values
are handled as ``#rrggbb`` strings here; the QColor conversion lives in the
caller (analysis_section).
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from dataclasses import fields
from typing import List, Optional

from .timeseries_axis_settings import (
    TimeSeriesAxisSettings,
    TimeSeriesGeneralSettings,
    default_axis_settings,
    default_general_settings,
)

CONFIG_VERSION = "1"

_CURVE_STR_KEYS = (
    "category", "layer_identifier", "element_id", "prop_internal", "prop_display",
    "y_label_with_unit", "y_axis", "label", "color", "line_style", "marker_symbol",
    "marker_color", "emphasis_mode", "legend_font_family",
)
_CURVE_FLOAT_KEYS = (("line_width", 2.0),)
_CURVE_INT_KEYS = (("marker_size", 6), ("legend_font_size", 8))
_CURVE_BOOL_KEYS = (
    "is_stepped", "show_markers", "marker_hollow", "show_point_values",
    "visible", "muted", "highlighted",
)


def _bool_to_str(value) -> str:
    return "true" if value else "false"


def _str_to_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default: Optional[int]) -> Optional[int]:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _dataclass_to_attribs(obj) -> dict:
    attribs = {}
    for f in fields(obj):
        value = getattr(obj, f.name)
        if isinstance(value, bool):
            attribs[f.name] = _bool_to_str(value)
        elif value is None:
            attribs[f.name] = ""
        else:
            attribs[f.name] = str(value)
    return attribs


def _apply_attribs_to_dataclass(attribs: dict, obj):
    for f in fields(obj):
        if f.name not in attribs:
            continue
        raw = attribs.get(f.name)
        current = getattr(obj, f.name)
        if isinstance(current, bool):
            setattr(obj, f.name, _str_to_bool(raw))
        elif isinstance(current, int):
            parsed = _to_int(raw, None)
            if parsed is not None:
                setattr(obj, f.name, parsed)
        elif isinstance(current, float):
            setattr(obj, f.name, _to_float(raw, current))
        else:
            setattr(obj, f.name, raw if raw is not None else "")
    return obj


def _curve_to_element(parent, curve: dict):
    attribs = {}
    for key in _CURVE_STR_KEYS:
        value = curve.get(key)
        attribs[key] = "" if value is None else str(value)
    for key, _default in _CURVE_FLOAT_KEYS:
        attribs[key] = str(_to_float(curve.get(key), _default))
    for key, _default in _CURVE_INT_KEYS:
        attribs[key] = str(_to_int(curve.get(key), _default))
    for key in _CURVE_BOOL_KEYS:
        attribs[key] = _bool_to_str(bool(curve.get(key)))
    decimals = curve.get("y_display_decimals")
    if decimals is not None:
        attribs["y_display_decimals"] = str(int(decimals))

    element = ET.SubElement(parent, "Curve", attribs)

    labels = curve.get("y_categorical_labels")
    if labels:
        labels_el = ET.SubElement(element, "CategoricalLabels")
        for label in labels:
            label_el = ET.SubElement(labels_el, "Label")
            label_el.text = str(label)
    return element


def _element_to_curve(element) -> dict:
    attribs = element.attrib
    curve = {}
    for key in _CURVE_STR_KEYS:
        curve[key] = attribs.get(key, "")
    for key, default in _CURVE_FLOAT_KEYS:
        curve[key] = _to_float(attribs.get(key), default)
    for key, default in _CURVE_INT_KEYS:
        curve[key] = _to_int(attribs.get(key), default)
    for key in _CURVE_BOOL_KEYS:
        curve[key] = _str_to_bool(attribs.get(key, "false"))

    raw_decimals = attribs.get("y_display_decimals")
    curve["y_display_decimals"] = _to_int(raw_decimals, None) if raw_decimals not in (None, "") else None

    labels_el = element.find("CategoricalLabels")
    if labels_el is not None:
        curve["y_categorical_labels"] = [(le.text or "") for le in labels_el.findall("Label")]
    else:
        curve["y_categorical_labels"] = None
    return curve


def build_config_tree(
    curves: List[dict],
    axis_x: TimeSeriesAxisSettings,
    axis_y_left: TimeSeriesAxisSettings,
    axis_y_right: TimeSeriesAxisSettings,
    general: TimeSeriesGeneralSettings,
    comment: str = "",
) -> ET.Element:
    root = ET.Element("TimeSeriesConfig", version=CONFIG_VERSION)

    if comment:
        ET.SubElement(root, "Comment").text = comment

    curves_el = ET.SubElement(root, "Curves")
    for curve in curves or []:
        _curve_to_element(curves_el, curve)

    axes_el = ET.SubElement(root, "Axes")
    for role, cfg in (("x", axis_x), ("yLeft", axis_y_left), ("yRight", axis_y_right)):
        attribs = {"role": role}
        attribs.update(_dataclass_to_attribs(cfg))
        ET.SubElement(axes_el, "Axis", attribs)

    ET.SubElement(root, "General", _dataclass_to_attribs(general))
    return root


def serialize_timeseries_config(
    curves: List[dict],
    axis_x: TimeSeriesAxisSettings,
    axis_y_left: TimeSeriesAxisSettings,
    axis_y_right: TimeSeriesAxisSettings,
    general: TimeSeriesGeneralSettings,
    comment: str = "",
) -> bytes:
    root = build_config_tree(curves, axis_x, axis_y_left, axis_y_right, general, comment)
    try:
        ET.indent(root)
    except AttributeError:
        pass
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_timeseries_config(
    path: str,
    curves: List[dict],
    axis_x: TimeSeriesAxisSettings,
    axis_y_left: TimeSeriesAxisSettings,
    axis_y_right: TimeSeriesAxisSettings,
    general: TimeSeriesGeneralSettings,
    comment: str = "",
) -> None:
    root = build_config_tree(curves, axis_x, axis_y_left, axis_y_right, general, comment)
    try:
        ET.indent(root)
    except AttributeError:
        pass
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def parse_config_root(root) -> dict:
    curves: List[dict] = []
    curves_el = root.find("Curves")
    if curves_el is not None:
        for curve_el in curves_el.findall("Curve"):
            curves.append(_element_to_curve(curve_el))

    axis_x = default_axis_settings()
    axis_y_left = default_axis_settings()
    axis_y_right = default_axis_settings()
    axes_el = root.find("Axes")
    if axes_el is not None:
        by_role = {axis_el.get("role", ""): axis_el for axis_el in axes_el.findall("Axis")}
        if "x" in by_role:
            _apply_attribs_to_dataclass(by_role["x"].attrib, axis_x)
        if "yLeft" in by_role:
            _apply_attribs_to_dataclass(by_role["yLeft"].attrib, axis_y_left)
        if "yRight" in by_role:
            _apply_attribs_to_dataclass(by_role["yRight"].attrib, axis_y_right)

    general = default_general_settings()
    general_el = root.find("General")
    if general_el is not None:
        _apply_attribs_to_dataclass(general_el.attrib, general)

    comment_el = root.find("Comment")
    comment = (comment_el.text or "") if comment_el is not None else ""

    return {
        "version": root.get("version", ""),
        "comment": comment,
        "curves": curves,
        "axis_x": axis_x,
        "axis_y_left": axis_y_left,
        "axis_y_right": axis_y_right,
        "general": general,
    }


def parse_timeseries_config_string(text) -> dict:
    root = ET.fromstring(text)
    return parse_config_root(root)


def read_timeseries_config(path: str) -> dict:
    root = ET.parse(path).getroot()
    return parse_config_root(root)


def read_timeseries_config_comment(path: str) -> str:
    """Return only the saved description, tolerating any read/parse error."""
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return ""
    comment_el = root.find("Comment")
    return (comment_el.text or "") if comment_el is not None else ""


def next_available_config_name(filename: str, existing_names) -> str:
    """Return a config filename that does not collide with ``existing_names``.

    If the base name is free it is returned unchanged. Otherwise an
    incrementing ``_N`` suffix is appended, continuing from the highest ``_N``
    already present so the offered name does not repeat a previously saved one.
    """
    existing = set(existing_names or [])
    if filename not in existing:
        return filename
    stem, ext = os.path.splitext(filename)
    prefix = stem + "_"
    max_n = 0
    for name in existing:
        root, file_ext = os.path.splitext(name)
        if file_ext.lower() != ext.lower() or not root.startswith(prefix):
            continue
        suffix = root[len(prefix):]
        if suffix.isdigit():
            max_n = max(max_n, int(suffix))
    n = max_n + 1
    candidate = f"{stem}_{n}{ext}"
    while candidate in existing:
        n += 1
        candidate = f"{stem}_{n}{ext}"
    return candidate
