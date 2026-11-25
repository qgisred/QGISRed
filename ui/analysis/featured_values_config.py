# -*- coding: utf-8 -*-
import copy
import json
import os

MAX_LEVEL = 5
KIND_SIMULATED = "simulated"
KIND_SIGNAL = "signal"
NODE = "Node"
LINK = "Link"
METER = "Meter"

NODE_FIELDS = ("Pressure", "Head", "Demand", "Quality")
LINK_FIELDS = ("Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "Status", "ReactRate", "Quality")

STYLE_PLAIN = "plain"
STYLE_HALO = "halo"
STYLE_OPAQUE = "opaque"
STYLE_FRAME = "frame"
STYLES = (STYLE_PLAIN, STYLE_HALO, STYLE_OPAQUE, STYLE_FRAME)

_SIGNAL_COUNTERPARTS = {
    "Pressure": (NODE, "Pressure"),
    "Level": (NODE, "Pressure"),
    "Flow": (LINK, "Flow"),
    "Velocity": (LINK, "Velocity"),
    "ChemicalConcentration": (None, "Quality"),
}

_DEFAULT_DISPLAY = {
    "visible": True,
    "showSimulated": True,
    "showMeasured": True,
    "hiddenMagnitudes": [],
    "maxLevel": MAX_LEVEL,
    "zoomDependent": False,
    "fontSize": 10,
    "showId": False,
    "showUnits": True,
    "simulatedStyle": STYLE_OPAQUE,
    "measuredStyle": STYLE_FRAME,
}


def default_config():
    return {"version": 1, "items": [], "display": copy.deepcopy(_DEFAULT_DISPLAY)}


def config_path(project_directory, network_name):
    return os.path.join(project_directory, network_name + "_FeaturedValues.json")


def _clamp_level(value):
    try:
        return max(1, min(MAX_LEVEL, int(value)))
    except (TypeError, ValueError):
        return 1


def _normalize_item(raw):
    if not isinstance(raw, dict):
        return None
    level = _clamp_level(raw.get("level", 1))
    if raw.get("kind") == KIND_SIGNAL:
        signal = str(raw.get("signal") or "")
        return {"kind": KIND_SIGNAL, "signal": signal, "level": level} if signal else None
    element, element_id, field = raw.get("element"), str(raw.get("id") or ""), raw.get("field")
    fields = NODE_FIELDS if element == NODE else LINK_FIELDS if element == LINK else ()
    if not element_id or field not in fields:
        return None
    return {"kind": KIND_SIMULATED, "element": element, "id": element_id, "field": field, "level": level}


def normalize(raw):
    config = default_config()
    if not isinstance(raw, dict):
        return config
    for raw_item in raw.get("items") or []:
        item = _normalize_item(raw_item)
        if item is not None:
            add_item(config, item)
    display = raw.get("display") if isinstance(raw.get("display"), dict) else {}
    for key, default in _DEFAULT_DISPLAY.items():
        value = display.get(key, default)
        if type(value) is not type(default):
            value = copy.deepcopy(default)
        config["display"][key] = value
    config["display"]["maxLevel"] = _clamp_level(config["display"]["maxLevel"])
    for key in ("simulatedStyle", "measuredStyle"):
        if config["display"][key] not in STYLES:
            config["display"][key] = _DEFAULT_DISPLAY[key]
    return config


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return normalize(json.load(handle))
    except (OSError, ValueError):
        return default_config()


def save(path, config):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2, ensure_ascii=False)


def item_key(item):
    if item["kind"] == KIND_SIGNAL:
        return (KIND_SIGNAL, item["signal"].lower())
    return (KIND_SIMULATED, item["element"], item["id"], item["field"])


def add_item(config, item):
    key = item_key(item)
    if any(item_key(existing) == key for existing in config["items"]):
        return False
    config["items"].append(item)
    return True


def signal_counterpart(signal, node_ids, link_ids):
    element, field = _SIGNAL_COUNTERPARTS.get(signal.get("magnitude") or "", (None, None))
    element_id = signal.get("element") or ""
    if not field or not element_id:
        return None
    if element is None:
        element = NODE if element_id in node_ids else LINK if element_id in link_ids else None
    known = node_ids if element == NODE else link_ids if element == LINK else ()
    if element_id not in known:
        return None
    return element, element_id, field


def magnitude_key(element, field):
    return "{}/{}".format(element, field)


def build_rows(config, signals, node_ids, link_ids):
    signals_by_id = {signal_id.lower(): signal for signal_id, signal in signals.items()}
    node_ids, link_ids = set(node_ids), set(link_ids)
    rows = []
    measured = set()
    for item in config["items"]:
        if item["kind"] != KIND_SIGNAL:
            continue
        signal = signals_by_id.get(item["signal"].lower())
        if signal is None:
            continue
        counterpart = signal_counterpart(signal, node_ids, link_ids)
        meter = signal.get("meter") or ""
        row = {
            "item": item, "kind": KIND_SIGNAL, "signal": signal.get("id") or item["signal"],
            "meter": meter, "level": item["level"], "element": None, "id": "", "field": None,
            "magnitude": magnitude_key("Signal", signal.get("magnitude") or ""),
        }
        if counterpart is not None:
            row["element"], row["id"], row["field"] = counterpart
            row["magnitude"] = magnitude_key(counterpart[0], counterpart[2])
            measured.add(counterpart)
        row["group"] = (METER, meter) if meter else (row["element"], row["id"])
        rows.append(row)

    for item in config["items"]:
        if item["kind"] != KIND_SIMULATED:
            continue
        known = node_ids if item["element"] == NODE else link_ids
        if item["id"] not in known or (item["element"], item["id"], item["field"]) in measured:
            continue
        rows.append({
            "item": item, "kind": KIND_SIMULATED, "signal": "", "meter": "", "level": item["level"],
            "element": item["element"], "id": item["id"], "field": item["field"],
            "magnitude": magnitude_key(item["element"], item["field"]),
            "group": (item["element"], item["id"]),
        })
    return rows


def assign_slots(rows, display):
    hidden = set(display.get("hiddenMagnitudes") or [])
    next_slot = {}
    ordered = sorted(range(len(rows)), key=lambda index: (rows[index]["level"], index))
    for index in ordered:
        row = rows[index]
        row["showSimulated"] = bool(display.get("showSimulated")) and row["field"] is not None
        row["showMeasured"] = bool(display.get("showMeasured")) and row["kind"] == KIND_SIGNAL
        visible = (row["magnitude"] not in hidden and row["level"] <= display.get("maxLevel", MAX_LEVEL)
                   and (row["showSimulated"] or row["showMeasured"]))
        row["slot"] = -1
        if visible:
            row["slot"] = next_slot.get(row["group"], 0)
            next_slot[row["group"]] = row["slot"] + 1
    return rows
