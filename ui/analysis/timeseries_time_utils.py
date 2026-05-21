# -*- coding: utf-8 -*-
from __future__ import annotations

import math
import os
import re
import unicodedata
from typing import Optional


_TIME_RE = re.compile(r"^\s*(\d{1,2})(?::(\d{1,2}))?(?::(\d{1,2}))?\s*([ap]\.?\s*m\.?|am|pm)?\s*$", re.IGNORECASE)
_START_CLOCK_KEYS = {
    "STARTCLOCKTIME",
    "STARTCLOCK",
    "STARTINGTIME",
    "STARTTIME",
    "HORAREALDEINICIODELASIMULACION",
    "HORAREALINICIOSIMULACION",
}


def parse_clock_time_to_seconds(value) -> Optional[int]:
    text = str(value or "").strip()
    if not text:
        return None
    match = _TIME_RE.match(text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    second = int(match.group(3) or 0)
    suffix = (match.group(4) or "").lower().replace(".", "").replace(" ", "")

    if minute > 59 or second > 59:
        return None

    if suffix in ("am", "pm"):
        if not 1 <= hour <= 12:
            return None
        if suffix == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
    elif not 0 <= hour <= 23:
        return None

    return hour * 3600 + minute * 60 + second


def _normalize_key(value) -> str:
    text = str(value or "")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch for ch in text.upper() if ch.isalnum())


def _parse_start_clock_from_text(text: str) -> Optional[int]:
    in_times = False
    for raw_line in (text or "").splitlines():
        line = raw_line.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            in_times = line.strip("[]").strip().upper() == "TIMES"
            continue

        upper = line.upper()
        if in_times and upper.startswith("START CLOCKTIME"):
            parsed = parse_clock_time_to_seconds(line[len("START CLOCKTIME"):].strip())
            if parsed is not None:
                return parsed

        for label in ("START CLOCKTIME", "STARTING TIME", "START TIME"):
            idx = upper.find(label)
            if idx < 0:
                continue
            candidate = line[idx + len(label):].strip(" \t:=.-")
            parsed = parse_clock_time_to_seconds(candidate)
            if parsed is not None:
                return parsed
    return None


def _read_text_start_clock(path: str) -> Optional[int]:
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as handle:
            return _parse_start_clock_from_text(handle.read())
    except Exception:
        return None


def _read_options_dbf_start_clock(project_directory: str, network_name: str) -> Optional[int]:
    if not project_directory or not network_name:
        return None
    path = os.path.join(project_directory, f"{network_name}_Options.dbf")
    if not os.path.exists(path):
        return None
    try:
        from qgis.core import QgsVectorLayer

        layer = QgsVectorLayer(path, "Options", "ogr")
        if hasattr(layer, "isValid") and not layer.isValid():
            return None
        for feature in layer.getFeatures():
            attrs = feature.attributes()
            if len(attrs) < 3:
                continue
            key = _normalize_key(attrs[1])
            if key not in _START_CLOCK_KEYS:
                continue
            parsed = parse_clock_time_to_seconds(attrs[2])
            if parsed is not None:
                return parsed
    except Exception:
        return None
    return None


def simulation_start_clock_seconds(
    project_directory: str = "",
    network_name: str = "",
    binary_path: str = "",
    fallback: int = 0,
) -> int:
    parsed = _read_options_dbf_start_clock(project_directory, network_name)
    if parsed is not None:
        return parsed

    candidates = []
    if binary_path:
        root, _ext = os.path.splitext(binary_path)
        candidates.extend([root + ".rpt", root + ".inp"])
    if project_directory and network_name:
        candidates.extend([
            os.path.join(project_directory, f"{network_name}.inp"),
            os.path.join(project_directory, f"{network_name}_Base.inp"),
        ])

    for path in candidates:
        parsed = _read_text_start_clock(path)
        if parsed is not None:
            return parsed

    try:
        return int(fallback) % 86400
    except Exception:
        return 0


def civil_time_parts(hours, start_clock_seconds: int = 0):
    try:
        elapsed_seconds = int(round(float(hours) * 3600.0))
    except Exception:
        return None
    try:
        start_seconds = int(start_clock_seconds) % 86400
    except Exception:
        start_seconds = 0

    total_seconds = start_seconds + elapsed_seconds
    day = math.floor(total_seconds / 86400)
    seconds_in_day = total_seconds - day * 86400
    hour = seconds_in_day // 3600
    minute = (seconds_in_day % 3600) // 60
    second = seconds_in_day % 60
    return int(day), int(hour), int(minute), int(second)


def format_civil_time(hours, start_clock_seconds: int = 0, *, include_seconds: bool = True, am_pm: bool = False) -> str:
    parts = civil_time_parts(hours, start_clock_seconds)
    if parts is None:
        return ""
    day, hour, minute, second = parts

    if am_pm:
        suffix = "am" if hour < 12 else "pm"
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        time_text = f"{display_hour}:{minute:02d} {suffix}"
    elif include_seconds:
        time_text = f"{hour}:{minute:02d}:{second:02d}"
    else:
        time_text = f"{hour}:{minute:02d}"

    return f"{day}d {time_text}"


def _format_decimal_hours(value: float, decimal_sep: str = ".") -> str:
    text = format(float(value), ".12g")
    if decimal_sep != ".":
        text = text.replace(".", decimal_sep)
    return text


def format_elapsed_time(
    hours,
    *,
    hour_format: str = "h",
    day_format: str = "split_days",
    include_seconds: bool = True,
    decimal_sep: str = ".",
) -> str:
    try:
        total_seconds = int(round(float(hours) * 3600.0))
    except Exception:
        return ""

    sign = "-" if total_seconds < 0 else ""
    abs_seconds = abs(total_seconds)
    days = abs_seconds // 86400
    rem = abs_seconds % 86400
    rem_hours_decimal = rem / 3600.0

    hour_format = (hour_format or "h").strip()
    day_format = (day_format or "split_days").strip()

    if hour_format == "h":
        if day_format == "total_hours":
            return sign + _format_decimal_hours(abs_seconds / 3600.0, decimal_sep)
        time_text = _format_decimal_hours(rem_hours_decimal, decimal_sep)
        return f"{sign}{days}d {time_text}" if days else sign + time_text

    if day_format == "total_hours":
        total_hours = abs_seconds // 3600
        minute = (abs_seconds % 3600) // 60
        second = abs_seconds % 60
        time_text = f"{total_hours}:{minute:02d}:{second:02d}" if include_seconds else f"{total_hours}:{minute:02d}"
        return sign + time_text

    hour = rem // 3600
    minute = (rem % 3600) // 60
    second = rem % 60
    time_text = f"{hour}:{minute:02d}:{second:02d}" if include_seconds else f"{hour}:{minute:02d}"
    return f"{sign}{days}d {time_text}" if days else sign + time_text


def civil_midnight_elapsed_hours(min_hours: float, max_hours: float, start_clock_seconds: int = 0):
    try:
        lo = float(min_hours)
        hi = float(max_hours)
        start_seconds = int(start_clock_seconds) % 86400
    except Exception:
        return []
    if hi < lo:
        lo, hi = hi, lo

    start_day = math.floor((start_seconds + lo * 3600.0) / 86400.0)
    end_day = math.floor((start_seconds + hi * 3600.0) / 86400.0)
    out = []
    for day in range(int(start_day) + 1, int(end_day) + 1):
        elapsed = (day * 86400 - start_seconds) / 3600.0
        if lo - 1e-9 <= elapsed <= hi + 1e-9:
            out.append(float(elapsed))
    return out
