# -*- coding: utf-8 -*-

ENVELOPE_MODES = ("off", "band", "lines", "both")

PROFILE_VARIABLE_COLORS = {
    "Elevation": "#8c643c",
    "Head": "#1f78b4",
    "Pressure": "#729b6f",
    "Quality": "#8d5a99",
    "HeadLoss": "#becf50",
}


def profile_variable_color_hex(key):
    return PROFILE_VARIABLE_COLORS.get(key, "")


PROFILE_VARIABLE_UNIT_FIELDS = {
    "Elevation": ("Junctions", "Elevation"),
    "Head": ("Nodes", "Head"),
    "Pressure": ("Nodes", "Pressure"),
    "Quality": ("Nodes", "Quality"),
    "HeadLoss": ("Nodes", "Head"),
}

PROFILE_DISTANCE_UNIT_FIELD = ("Pipes", "Length")


def label_with_unit(label, unit_abbr):
    label = label or ""
    unit_abbr = (unit_abbr or "").strip()
    return "{} ({})".format(label, unit_abbr) if unit_abbr else label


def joined_labels(labels):
    unique = []
    for label in labels or []:
        if label and label not in unique:
            unique.append(label)
    return ", ".join(unique)


def profile_x_range(data_min, data_max):
    x0 = float(data_min)
    x1 = float(data_max)
    if x1 <= x0:
        x1 = x0 + 1.0
    return x0, x1


PROFILE_AREA_SIDE_PAD = 12.0
PROFILE_AREA_TOP_PAD = 14.0


def profile_data_area(left, top, right, bottom,
                      side_pad=PROFILE_AREA_SIDE_PAD, top_pad=PROFILE_AREA_TOP_PAD):
    inner_left = float(left) + side_pad
    inner_right = float(right) - side_pad
    if inner_right - inner_left < 8.0:
        inner_left, inner_right = float(left), float(right)
    inner_top = float(top) + top_pad
    if float(bottom) - inner_top < 8.0:
        inner_top = float(top)
    return inner_left, inner_top, inner_right, float(bottom)


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


MAIN_PATH_KEY = "main"


def series_path_key(s):
    return s.get("path_key") or MAIN_PATH_KEY


def series_path_keys(series):
    keys = []
    for s in series or []:
        key = series_path_key(s)
        if key not in keys:
            keys.append(key)
    return keys


def series_for_path(series, path_key):
    if path_key is None:
        return list(series or [])
    filtered = [s for s in series or [] if series_path_key(s) == path_key]
    return filtered or list(series or [])


def path_key_for_node_id(series, node_id):
    if node_id is None or node_id == "":
        return None
    target = str(node_id)
    for s in series or []:
        for nid in s.get("node_ids") or []:
            if str(nid) == target:
                return series_path_key(s)
    return None


def point_segment_distance(x, y, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    length_sq = dx * dx + dy * dy
    if length_sq <= 1e-12:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    t = ((x - x1) * dx + (y - y1) * dy) / length_sq
    t = max(0.0, min(1.0, t))
    nx = x1 + t * dx
    ny = y1 + t * dy
    return ((x - nx) ** 2 + (y - ny) ** 2) ** 0.5


def polyline_pixel_distance(pixels, x, y):
    best = None
    previous = None
    for pixel in pixels or []:
        if pixel is None:
            previous = None
            continue
        if previous is None:
            dist = ((x - pixel[0]) ** 2 + (y - pixel[1]) ** 2) ** 0.5
        else:
            dist = point_segment_distance(x, y, previous[0], previous[1], pixel[0], pixel[1])
        if best is None or dist < best:
            best = dist
        previous = pixel
    return best


def nearest_path_key(entries, x, y):
    best_key = None
    best_dist = None
    for entry in entries or []:
        dist = polyline_pixel_distance(entry.get("pixels"), x, y)
        if dist is None:
            continue
        if best_dist is None or dist < best_dist - 1e-9:
            best_dist = dist
            best_key = entry.get("path_key")
    return best_key


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
    path_key = MAIN_PATH_KEY
    path_label = ""
    if owner is not None:
        ids = owner.get("node_ids")
        if ids and owner_idx < len(ids):
            node_id = ids[owner_idx]
        path_key = series_path_key(owner)
        path_label = owner.get("path_label") or ""
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
            "label": s.get("readout_label") or s.get("display_label") or s.get("label", ""),
            "color": s.get("color"),
            "value": s_value,
            "distance": s_distance,
            "point_index": s_idx,
        })
    return {"index": index, "distance": snap_distance, "entries": entries, "node_id": node_id,
            "path_key": path_key, "path_label": path_label}


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
