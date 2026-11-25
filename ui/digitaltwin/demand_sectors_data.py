# -*- coding: utf-8 -*-
OK = "OK"
VALID = "Valid"
Z = "Z"
UNCONTROLLED = "Uncontrolled"
SECTOR_METER_TYPES = ("flowmeter", "countermeter", "levelsensor")


def build_options(z_limit):
    return "zLimit={}".format(repr(float(z_limit)))


def _integer(text):
    try:
        return int(text)
    except ValueError:
        return None


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def parse_identification(text):
    lines = [line.rstrip("\r").split("\t") for line in (text or "").split("\n")]
    if not lines or lines[0][0].strip() != OK:
        return None

    summary = {VALID: 0, Z: 0, UNCONTROLLED: 0, "ignoredMeters": 0}
    sectors = []
    for columns in lines[1:]:
        if columns[0] == "summary" and len(columns) >= 5:
            counts = [_integer(value) for value in columns[1:5]]
            if None not in counts:
                summary = dict(zip((VALID, Z, UNCONTROLLED, "ignoredMeters"), counts))
        elif columns[0] == "sector" and len(columns) >= 7:
            nodes, links, meters = _integer(columns[3]), _integer(columns[4]), _integer(columns[5])
            demand = _number(columns[6])
            if columns[1] and None not in (nodes, links, meters, demand):
                sectors.append({"id": columns[1], "kind": columns[2], "nodes": nodes, "links": links,
                                "meters": meters, "demand": demand})
    return {"summary": summary, "sectors": sectors}


def error_message(text):
    return (text or "").replace("Error:", "", 1).strip()


def can_create(identification):
    return identification is not None and any(sector["kind"] != UNCONTROLLED for sector in identification["sectors"])


def has_sector_meters(meter_types):
    return any(str(meter_type or "").strip().lower() in SECTOR_METER_TYPES for meter_type in meter_types)
