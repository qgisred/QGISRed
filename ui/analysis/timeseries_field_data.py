# -*- coding: utf-8 -*-
import re

from qgis.PyQt.QtGui import QColor

OK = "OK"
LEGEND_INDEX = -1
LEGEND_TYPE = "field_data"
NEUTRAL_COLOR = QColor(90, 90, 90)
SUPPORTED = {
    "Node": ("Pressure", "Head", "Quality"),
    "Link": ("Flow", "Velocity", "UnitHdLoss", "Quality"),
}
_UNIT_RE = re.compile(r"\(([^()]*)\)\s*$")


def series_units(series):
    match = _UNIT_RE.search(str(series.get("y_label_with_unit") or ""))
    return match.group(1).strip() if match else ""


def series_request(series):
    key = str(series.get("series_key") or "")
    parts = key.split(":", 3)
    if len(parts) < 4 or not parts[3]:
        return None
    category, _layer, variable, element = parts
    if variable not in SUPPORTED.get(category, ()):
        return None
    units = series_units(series)
    if variable == "Quality" and "/L" not in units:
        return None
    return "\t".join(text.replace("\t", " ").replace("\n", " ") for text in (key, element, variable, units))


def build_requests(series_list):
    return "\n".join(request for request in map(series_request, series_list or []) if request)


def sampling_window(times_seconds):
    times = sorted(float(t) for t in times_seconds or [])
    if not times:
        return None
    step = (times[-1] - times[0]) / (len(times) - 1) if len(times) > 1 else 0.0
    return times[0], times[-1], step


def parse_series(text):
    lines = (text or "").split("\n")
    if not lines or lines[0].strip() != OK:
        return {}
    curves = {}
    for line in lines[1:]:
        columns = line.rstrip("\r").split("\t")
        if len(columns) < 3:
            continue
        try:
            hours, value = float(columns[1]) / 3600.0, float(columns[2])
        except ValueError:
            continue
        curve = curves.setdefault(columns[0], {"x": [], "y": []})
        curve["x"].append(hours)
        curve["y"].append(value)
    return curves


def has_stored_data(signals):
    return any(signal.get("hasData") for signal in (signals or {}).values())


def soft_color(color):
    base = QColor(color)
    return QColor(*(int(round(channel + (255 - channel) * 0.6)) for channel in (base.red(), base.green(), base.blue())))


def marker_colors(curve_color, cfg):
    outline = QColor(getattr(cfg, "field_marker_color_hex", "") or "")
    if not outline.isValid():
        outline = QColor(curve_color) if curve_color is not None else QColor(NEUTRAL_COLOR)
    fill = QColor(getattr(cfg, "field_marker_fill_hex", "") or "")
    if not fill.isValid():
        fill = soft_color(outline)
    if not bool(getattr(cfg, "field_marker_filled", True)):
        fill = QColor(255, 255, 255)
    return outline, fill


def nearest_value(curve, hours, tolerance):
    best = None
    for x, y in zip(curve.get("x") or [], curve.get("y") or []):
        distance = abs(x - hours)
        if distance <= tolerance and (best is None or distance < best[0]):
            best = (distance, y)
    return None if best is None else best[1]
