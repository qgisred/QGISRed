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
    snap_distance = None
    best_gap = None
    owner = None
    owner_idx = None
    for s in series:
        candidate = nearest_visible_point(s["points"], data_x)
        if candidate is None:
            continue
        _s_idx, s_distance, _s_value = candidate
        gap = abs(s_distance - data_x)
        if best_gap is None or gap < best_gap:
            best_gap = gap
            snap_distance = s_distance
            owner = s
            owner_idx = _s_idx
    if snap_distance is None:
        return None
    node_id = None
    if owner is not None:
        ids = owner.get("node_ids")
        if ids and owner_idx < len(ids):
            node_id = ids[owner_idx]
    entries = []
    index = 0
    for s in series:
        candidate = nearest_visible_point(s["points"], snap_distance)
        if candidate is None:
            continue
        s_idx, s_distance, s_value = candidate
        if not entries:
            index = s_idx
        entries.append({
            "label": s.get("label", ""),
            "color": s.get("color"),
            "value": s_value,
            "distance": s_distance,
            "point_index": s_idx,
        })
    return {"index": index, "distance": snap_distance, "entries": entries, "node_id": node_id}


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
