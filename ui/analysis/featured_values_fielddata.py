# -*- coding: utf-8 -*-
OK = "OK"
_SIGNAL_COLUMNS = 8


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def _lines(text):
    lines = (text or "").split("\n")
    if not lines or lines[0].strip() != OK:
        return []
    return [line.rstrip("\r").split("\t") for line in lines[1:] if line.strip()]


def parse_signals(text):
    signals = {}
    for columns in _lines(text):
        if len(columns) < _SIGNAL_COLUMNS or not columns[0]:
            continue
        x, y = _number(columns[5]), _number(columns[6])
        signals[columns[0]] = {
            "id": columns[0],
            "meter": columns[1],
            "element": columns[2],
            "magnitude": columns[3],
            "units": columns[4],
            "point": (x, y) if x is not None and y is not None else None,
            "hasData": columns[7] == "1",
        }
    return signals


def parse_values(text):
    values = {}
    for columns in _lines(text):
        if len(columns) >= 2 and columns[0]:
            values[columns[0]] = _number(columns[1])
    return values


def join_ids(signal_ids):
    return "\n".join(signal_ids)
