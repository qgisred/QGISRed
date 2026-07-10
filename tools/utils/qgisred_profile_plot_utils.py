# -*- coding: utf-8 -*-

ENVELOPE_MODES = ("off", "band", "lines", "both")


def resolve_envelope_mode(mode):
    show_band = mode in ("band", "both")
    show_lines = mode in ("lines", "both")
    return show_band, show_lines


def profile_line_segments(points):
    segments = []
    current = []
    for d, v in points:
        if v is None:
            if len(current) >= 2:
                segments.append(current)
            current = []
        else:
            current.append((d, v))
    if len(current) >= 2:
        segments.append(current)
    return segments


def nearest_visible_point(points, data_x):
    best = None
    best_dist = None
    for idx, (d, v) in enumerate(points):
        if v is None:
            continue
        dist = abs(d - data_x)
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best = (idx, d, v)
    return best


def cursor_snapshot(series, data_x):
    nearest = None
    for s in series:
        candidate = nearest_visible_point(s["points"], data_x)
        if candidate is not None:
            nearest = candidate
            break
    if nearest is None:
        return None
    idx, distance, _value = nearest
    node_id = None
    for s in series:
        ids = s.get("node_ids")
        if ids and idx < len(ids):
            node_id = ids[idx]
            break
    entries = []
    for s in series:
        points = s["points"]
        if idx < len(points) and points[idx][1] is not None:
            entries.append({
                "label": s.get("label", ""),
                "color": s.get("color"),
                "value": points[idx][1],
            })
    return {"index": idx, "distance": distance, "entries": entries, "node_id": node_id}


def truncate_id(value, max_len=10):
    text = "" if value is None else str(value)
    if len(text) > max_len:
        return text[:max_len] + "…"
    return text


def format_profile_value(value):
    if value is None:
        return "-"
    magnitude = abs(value)
    if magnitude >= 100:
        return "{:.1f}".format(value)
    if magnitude >= 1:
        return "{:.2f}".format(value)
    return "{:.3f}".format(value)
