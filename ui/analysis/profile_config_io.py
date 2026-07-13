# -*- coding: utf-8 -*-
from __future__ import annotations

from contextlib import suppress
import xml.etree.ElementTree as ET  # nosec B405 — local profile config files written by this plugin, no external input
from dataclasses import fields
from typing import List

from .profile_chart_settings import (
    ProfileAxisSettings,
    ProfileGeneralSettings,
    ProfileCurveStyle,
)
from .timeseries_config_io import next_available_config_name  # noqa: F401

CONFIG_VERSION = "1"

_CURVE_STR_KEYS = ("label", "color_hex", "line_style")
_CURVE_FLOAT_KEYS = (("width", 2.0), ("marker_size", 2.5))
_CURVE_BOOL_KEYS = ("show_markers",)


def _bool_to_str(value) -> str:
    return "true" if value else "false"


def _str_to_bool(value) -> bool:
    return str(value).strip().lower() in ("true", "1", "yes")


def _to_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value, default):
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


def build_config_tree(profile, axis_x, axis_y, general, curve_overrides, comment="", axis_y_right=None) -> ET.Element:
    root = ET.Element("ProfileConfig", version=CONFIG_VERSION)

    if comment:
        ET.SubElement(root, "Comment").text = comment

    options = profile.get("options", {}) or {}
    profile_el = ET.SubElement(root, "Profile", {
        "variable": str(profile.get("variable", "")),
        "secondary_variable": str(profile.get("secondary_variable", "") or ""),
        "show_symbols": _bool_to_str(options.get("show_symbols")),
        "show_labels": _bool_to_str(options.get("show_labels")),
        "envelope_mode": str(options.get("envelope_mode", "off") or "off"),
    })

    nodes_el = ET.SubElement(profile_el, "ReferenceNodes")
    for node in profile.get("reference_nodes", []) or []:
        ET.SubElement(nodes_el, "Node").text = str(node)

    branches_el = ET.SubElement(profile_el, "Branches")
    for branch in profile.get("branches", []) or []:
        branch_el = ET.SubElement(branches_el, "Branch", {
            "offset": str(_to_float(branch.get("offset"), 0.0)),
        })
        for node in branch.get("reference_nodes", []) or []:
            ET.SubElement(branch_el, "Node").text = str(node)

    axes_el = ET.SubElement(root, "Axes")
    axes = [("x", axis_x), ("y", axis_y)]
    if axis_y_right is not None:
        axes.append(("yRight", axis_y_right))
    for role, cfg in axes:
        attribs = {"role": role}
        attribs.update(_dataclass_to_attribs(cfg))
        ET.SubElement(axes_el, "Axis", attribs)

    ET.SubElement(root, "General", _dataclass_to_attribs(general))

    curves_el = ET.SubElement(root, "Curves")
    for label, style in (curve_overrides or {}).items():
        attribs = {
            "label": str(label),
            "color_hex": str(getattr(style, "color_hex", "") or ""),
            "line_style": str(getattr(style, "line_style", "solid") or "solid"),
            "width": str(_to_float(getattr(style, "width", 2.0), 2.0)),
            "marker_size": str(_to_float(getattr(style, "marker_size", 2.5), 2.5)),
            "show_markers": _bool_to_str(getattr(style, "show_markers", True)),
        }
        ET.SubElement(curves_el, "Curve", attribs)

    return root


def write_profile_config(path, profile, axis_x, axis_y, general, curve_overrides, comment="", axis_y_right=None) -> None:
    root = build_config_tree(profile, axis_x, axis_y, general, curve_overrides, comment, axis_y_right)
    with suppress(AttributeError):
        ET.indent(root)
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def serialize_profile_config(profile, axis_x, axis_y, general, curve_overrides, comment="", axis_y_right=None) -> bytes:
    root = build_config_tree(profile, axis_x, axis_y, general, curve_overrides, comment, axis_y_right)
    with suppress(AttributeError):
        ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _nodes_from(parent) -> List[str]:
    if parent is None:
        return []
    return [(node.text or "").strip() for node in parent.findall("Node") if (node.text or "").strip()]


def parse_config_root(root) -> dict:
    comment_el = root.find("Comment")
    comment = (comment_el.text or "") if comment_el is not None else ""

    profile_el = root.find("Profile")
    variable = ""
    secondary_variable = ""
    reference_nodes: List[str] = []
    branches: List[dict] = []
    options = {"show_symbols": False, "show_labels": False, "envelope_mode": "off"}
    if profile_el is not None:
        variable = profile_el.get("variable", "")
        secondary_variable = profile_el.get("secondary_variable", "") or ""
        options = {
            "show_symbols": _str_to_bool(profile_el.get("show_symbols", "false")),
            "show_labels": _str_to_bool(profile_el.get("show_labels", "false")),
            "envelope_mode": profile_el.get("envelope_mode", "off") or "off",
        }
        reference_nodes = _nodes_from(profile_el.find("ReferenceNodes"))
        branches_el = profile_el.find("Branches")
        if branches_el is not None:
            for branch_el in branches_el.findall("Branch"):
                branches.append({
                    "offset": _to_float(branch_el.get("offset"), 0.0),
                    "reference_nodes": _nodes_from(branch_el),
                })

    axis_x = ProfileAxisSettings()
    axis_y = ProfileAxisSettings()
    axis_y_right = ProfileAxisSettings()
    axes_el = root.find("Axes")
    if axes_el is not None:
        by_role = {axis_el.get("role", ""): axis_el for axis_el in axes_el.findall("Axis")}
        if "x" in by_role:
            _apply_attribs_to_dataclass(by_role["x"].attrib, axis_x)
        if "y" in by_role:
            _apply_attribs_to_dataclass(by_role["y"].attrib, axis_y)
        if "yRight" in by_role:
            _apply_attribs_to_dataclass(by_role["yRight"].attrib, axis_y_right)

    general = ProfileGeneralSettings()
    general_el = root.find("General")
    if general_el is not None:
        _apply_attribs_to_dataclass(general_el.attrib, general)

    curve_overrides = {}
    curves_el = root.find("Curves")
    if curves_el is not None:
        for curve_el in curves_el.findall("Curve"):
            label = curve_el.get("label", "")
            if not label:
                continue
            curve_overrides[label] = ProfileCurveStyle(
                color_hex=curve_el.get("color_hex", ""),
                width=_to_float(curve_el.get("width"), 2.0),
                line_style=curve_el.get("line_style", "solid") or "solid",
                show_markers=_str_to_bool(curve_el.get("show_markers", "true")),
                marker_size=_to_float(curve_el.get("marker_size"), 2.5),
            )

    return {
        "version": root.get("version", ""),
        "comment": comment,
        "variable": variable,
        "secondary_variable": secondary_variable,
        "reference_nodes": reference_nodes,
        "branches": branches,
        "options": options,
        "axis_x": axis_x,
        "axis_y": axis_y,
        "axis_y_right": axis_y_right,
        "general": general,
        "curve_overrides": curve_overrides,
    }


def parse_profile_config_string(text) -> dict:
    root = ET.fromstring(text)  # nosec B314 — local chart config content, not external input
    return parse_config_root(root)


def read_profile_config(path) -> dict:
    root = ET.parse(path).getroot()  # nosec B314 — local file written by this plugin, not external input
    return parse_config_root(root)


def read_profile_config_comment(path) -> str:
    try:
        root = ET.parse(path).getroot()  # nosec B314 — local file written by this plugin, not external input
    except Exception:
        return ""
    comment_el = root.find("Comment")
    return (comment_el.text or "") if comment_el is not None else ""
