# -*- coding: utf-8 -*-
"""Parser for EPANET hydraulic save files (.hyd)."""
import os
import struct
import math

import numpy as np

from .qgisred_results_binary import (
    ROUNDING_PRECISION,
    getOut_Metadata,
    _resolve_link_status,
)
_HYD_MAGIC = 516114521
_HYD_HEADER_SIZE = 32


def _hyd_usable_end(data):
    payload_len = len(data) - _HYD_HEADER_SIZE
    if payload_len % 4 == 1 and data[-1] == 0x1A:
        return len(data) - 1
    return len(data)


def getHyd_Metadata(hyd_path):
    """Return metadata for an EPANET .hyd file, or None if invalid/missing."""
    if not os.path.exists(hyd_path):
        return None

    with open(hyd_path, "rb") as f:
        data = f.read()

    if len(data) < _HYD_HEADER_SIZE + 4:
        return None

    magic, version, n_nodes, n_links, n_tanks, n_pumps, n_valves, duration = struct.unpack_from(
        "<8i", data, 0
    )
    if magic != _HYD_MAGIC:
        return None

    record_words = 1 + (2 * n_nodes) + (3 * n_links) + 1
    word_count = (_hyd_usable_end(data) - _HYD_HEADER_SIZE) // 4
    if record_words <= 0 or word_count % record_words != 0:
        return None

    num_records = word_count // record_words
    record_bytes = record_words * 4
    times = []
    steps = []
    off = _HYD_HEADER_SIZE
    for _ in range(num_records):
        time_s = struct.unpack_from("<i", data, off)[0]
        off += 4 + (2 * n_nodes + 3 * n_links) * 4
        step_s = struct.unpack_from("<i", data, off)[0]
        off += 4
        times.append(time_s)
        steps.append(step_s)

    return {
        "magic": magic,
        "version": version,
        "n_nodes": n_nodes,
        "n_links": n_links,
        "n_tanks": n_tanks,
        "n_pumps": n_pumps,
        "n_valves": n_valves,
        "duration": duration,
        "num_records": num_records,
        "record_bytes": record_bytes,
        "record_words": record_words,
        "times": times,
        "steps": steps,
    }


def getHyd_TimeLabels(hyd_path):
    """Return time labels as a ';'-separated string (same format as GISRed.Compute)."""
    from .qgisred_results_data import seconds_to_time_str

    meta = getHyd_Metadata(hyd_path)
    if not meta or meta["num_records"] <= 1:
        from qgis.PyQt.QtCore import QCoreApplication
        return QCoreApplication.translate("QGISRedResultsDock", "Single Period")

    return ";".join(seconds_to_time_str(t) for t in meta["times"])


def _find_hyd_period_index(times, time_seconds):
    if not times:
        return 0
    for i, t in enumerate(times):
        if t == time_seconds:
            return i
    return max(0, min(len(times) - 1, int(round(
        (time_seconds - times[0]) / max(times[1] - times[0], 1) if len(times) > 1 else 0
    ))))


def _read_hyd_period_arrays(data, meta, period_index):
    n_nodes = meta["n_nodes"]
    n_links = meta["n_links"]
    record_bytes = meta["record_bytes"]
    off = _HYD_HEADER_SIZE + period_index * record_bytes
    time_s = struct.unpack_from("<i", data, off)[0]
    off += 4
    demands = struct.unpack_from(f"<{n_nodes}f", data, off)
    off += 4 * n_nodes
    heads = struct.unpack_from(f"<{n_nodes}f", data, off)
    off += 4 * n_nodes
    flows = struct.unpack_from(f"<{n_links}f", data, off)
    off += 4 * n_links
    statuses = struct.unpack_from(f"<{n_links}f", data, off)
    off += 4 * n_links
    settings = struct.unpack_from(f"<{n_links}f", data, off)
    return time_s, demands, heads, flows, statuses, settings


def _read_out_elevations(out_path, n_nodes):
    """Read node elevations from the static section of a companion .out file."""
    with open(out_path, "rb") as f:
        prologue = f.read(15 * 4)
        if len(prologue) < 60:
            return None
        magic1, version, n_nodes_out, n_tanks, n_links, n_pumps, n_valves = struct.unpack(
            "7i", prologue[:28]
        )
        if magic1 != _HYD_MAGIC or n_nodes_out != n_nodes:
            return None
        f.seek(824, 1)
        f.seek(32 * n_nodes + 32 * n_links + 12 * n_links + 8 * n_tanks, 1)
        from .qgisred_results_binary import _read_floats
        return _read_floats(f, n_nodes)


def getHyd_TimeNodesProperties(hyd_path, time_seconds, out_path):
    """Node results for one hydraulic instant (Demand, Head, Pressure; Quality=None)."""
    hyd_meta = getHyd_Metadata(hyd_path)
    if not hyd_meta:
        return {}

    out_meta = None
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            out_meta = getOut_Metadata(f)

    if not out_meta or out_meta["n_nodes"] != hyd_meta["n_nodes"]:
        return {}

    with open(hyd_path, "rb") as f:
        data = f.read()

    period_index = _find_hyd_period_index(hyd_meta["times"], time_seconds)
    _, demands, heads, _, _, _ = _read_hyd_period_arrays(data, hyd_meta, period_index)
    elevations = _read_out_elevations(out_path, hyd_meta["n_nodes"]) or [0.0] * hyd_meta["n_nodes"]

    results = {}
    for i, nid in enumerate(out_meta["node_ids"]):
        pressure = float(heads[i]) - float(elevations[i])
        results[nid] = {
            "Pressure": round(pressure, ROUNDING_PRECISION),
            "Head": round(float(heads[i]), ROUNDING_PRECISION),
            "Demand": round(float(demands[i]), ROUNDING_PRECISION),
            "Quality": None,
        }
    return results


def getHyd_TimeLinksProperties(hyd_path, time_seconds, out_path):
    """Link results for one hydraulic instant (Flow, Status, Setting; others None)."""
    hyd_meta = getHyd_Metadata(hyd_path)
    if not hyd_meta:
        return {}

    with open(out_path, "rb") as f:
        out_meta = getOut_Metadata(f, include_lengths=True)
    if not out_meta or out_meta["n_links"] != hyd_meta["n_links"]:
        return {}

    with open(hyd_path, "rb") as f:
        data = f.read()

    period_index = _find_hyd_period_index(hyd_meta["times"], time_seconds)
    _, _, heads, flows, statuses, settings = _read_hyd_period_arrays(
        data, hyd_meta, period_index
    )

    n = out_meta["n_nodes"]
    nl = out_meta["n_links"]
    elevations = _read_out_elevations(out_path, n) or [0.0] * n

    results = {}
    for i in range(nl):
        link_type = out_meta["link_types"][i]
        from_idx = out_meta["link_from"][i]
        to_idx = out_meta["link_to"][i]

        status_text = _resolve_link_status(
            indicator=float(statuses[i]),
            link_type=link_type,
            Q=float(flows[i]),
            setting=float(settings[i]),
            from_head=float(heads[from_idx]),
            to_head=float(heads[to_idx]),
            from_pressure=float(heads[from_idx]) - float(elevations[from_idx]),
            to_pressure=float(heads[to_idx]) - float(elevations[to_idx]),
        )

        results[out_meta["link_ids"][i]] = {
            "Status": status_text,
            "Flow": round(float(flows[i]), ROUNDING_PRECISION),
            "Velocity": None,
            "HeadLoss": None,
            "UnitHdLoss": None,
            "FricFactor": None,
            "ReactRate": None,
            "Quality": None,
        }
    return results


def getHyd_StatNodesProperties(hyd_path, stat, out_path):
    """Statistics for node properties across all hydraulic calculation instants."""
    VALID_STATS = {"Maximum", "Minimum", "Average", "Range", "StdDev"}
    if stat not in VALID_STATS:
        raise ValueError(f"stat must be one of {VALID_STATS}")

    hyd_meta = getHyd_Metadata(hyd_path)
    if not hyd_meta or hyd_meta["num_records"] == 0:
        return {}

    with open(out_path, "rb") as f:
        out_meta = getOut_Metadata(f)
    if not out_meta or out_meta["n_nodes"] != hyd_meta["n_nodes"]:
        return {}

    n = hyd_meta["n_nodes"]
    node_ids = out_meta["node_ids"]
    elevations = _read_out_elevations(out_path, n) or [0.0] * n

    with open(hyd_path, "rb") as f:
        data = f.read()

    need_max = stat in ("Maximum", "Range")
    need_min = stat in ("Minimum", "Range")
    var_names = ["Demand", "Head", "Pressure"]

    if need_max:
        max_vals = np.full((3, n), -np.inf, dtype=np.float32)
        max_times = np.full((3, n), -1, dtype=np.int64)
    if need_min:
        min_vals = np.full((3, n), np.inf, dtype=np.float32)
        min_times = np.full((3, n), -1, dtype=np.int64)
    if stat == "Average":
        sums = np.zeros((3, n), dtype=np.float64)
    if stat == "StdDev":
        wf_mean = np.zeros((3, n), dtype=np.float64)
        wf_M2 = np.zeros((3, n), dtype=np.float64)

    actual_periods = 0
    for p in range(hyd_meta["num_records"]):
        time_s, demands, heads, _, _, _ = _read_hyd_period_arrays(data, hyd_meta, p)
        d = np.array(demands, dtype=np.float32)
        h = np.array(heads, dtype=np.float32)
        pr = h - np.array(elevations, dtype=np.float32)
        vals = np.vstack([d, h, pr])
        actual_periods += 1

        if need_max:
            mask = vals > max_vals
            max_vals = np.where(mask, vals, max_vals)
            max_times[mask] = time_s
        if need_min:
            mask = vals < min_vals
            min_vals = np.where(mask, vals, min_vals)
            min_times[mask] = time_s
        if stat == "Average":
            sums += vals.astype(np.float64)
        if stat == "StdDev":
            v_d = vals.astype(np.float64)
            delta = v_d - wf_mean
            wf_mean += delta / actual_periods
            wf_M2 += delta * (v_d - wf_mean)

    output_order = ["Pressure", "Head", "Demand"]
    var_idx = {name: i for i, name in enumerate(var_names)}
    results = {}
    for ni in range(n):
        node_props = {}
        for name in output_order:
            vi = var_idx[name]
            if stat == "Maximum":
                node_props[name] = {
                    "Time": int(max_times[vi, ni]),
                    "Value": round(float(max_vals[vi, ni]), ROUNDING_PRECISION),
                }
            elif stat == "Minimum":
                node_props[name] = {
                    "Time": int(min_times[vi, ni]),
                    "Value": round(float(min_vals[vi, ni]), ROUNDING_PRECISION),
                }
            elif stat == "Average":
                node_props[name] = {
                    "Value": round(float(sums[vi, ni]) / actual_periods, ROUNDING_PRECISION),
                }
            elif stat == "Range":
                node_props[name] = {
                    "Value": round(float(max_vals[vi, ni] - min_vals[vi, ni]), ROUNDING_PRECISION),
                }
            elif stat == "StdDev":
                variance = float(wf_M2[vi, ni]) / actual_periods if actual_periods > 0 else 0.0
                node_props[name] = {
                    "Value": round(math.sqrt(variance), ROUNDING_PRECISION),
                }
        results[node_ids[ni]] = node_props
    return results


def getHyd_StatLinksProperties(hyd_path, stat, out_path):
    """Statistics for link Flow across all hydraulic calculation instants."""
    VALID_STATS = {"Maximum", "Minimum", "Average", "Range", "StdDev"}
    if stat not in VALID_STATS:
        raise ValueError(f"stat must be one of {VALID_STATS}")

    hyd_meta = getHyd_Metadata(hyd_path)
    if not hyd_meta or hyd_meta["num_records"] == 0:
        return {}

    with open(out_path, "rb") as f:
        out_meta = getOut_Metadata(f, include_lengths=True)
    if not out_meta or out_meta["n_links"] != hyd_meta["n_links"]:
        return {}

    nl = hyd_meta["n_links"]
    link_ids = out_meta["link_ids"]

    with open(hyd_path, "rb") as f:
        data = f.read()

    need_max = stat in ("Maximum", "Range")
    need_min = stat in ("Minimum", "Range")
    if need_max:
        max_vals = np.full(nl, -np.inf, dtype=np.float32)
        max_times = np.full(nl, -1, dtype=np.int64)
    if need_min:
        min_vals = np.full(nl, np.inf, dtype=np.float32)
        min_times = np.full(nl, -1, dtype=np.int64)
    if stat == "Average":
        sums = np.zeros(nl, dtype=np.float64)
    if stat == "StdDev":
        wf_mean = np.zeros(nl, dtype=np.float64)
        wf_M2 = np.zeros(nl, dtype=np.float64)

    actual_periods = 0
    for p in range(hyd_meta["num_records"]):
        time_s, _, _, flows, _, _ = _read_hyd_period_arrays(data, hyd_meta, p)
        vals = np.array(flows, dtype=np.float32)
        actual_periods += 1
        if need_max:
            mask = vals > max_vals
            max_vals = np.where(mask, vals, max_vals)
            max_times[mask] = time_s
        if need_min:
            mask = vals < min_vals
            min_vals = np.where(mask, vals, min_vals)
            min_times[mask] = time_s
        if stat == "Average":
            sums += vals.astype(np.float64)
        if stat == "StdDev":
            v_d = vals.astype(np.float64)
            delta = v_d - wf_mean
            wf_mean += delta / actual_periods
            wf_M2 += delta * (v_d - wf_mean)

    results = {}
    for li in range(nl):
        link_props = {
            "Status": None,
            "Velocity": None,
            "HeadLoss": None,
            "UnitHdLoss": None,
            "FricFactor": None,
            "ReactRate": None,
            "Quality": None,
        }
        if stat == "Maximum":
            link_props["Flow"] = {
                "Time": int(max_times[li]),
                "Value": round(float(max_vals[li]), ROUNDING_PRECISION),
            }
        elif stat == "Minimum":
            link_props["Flow"] = {
                "Time": int(min_times[li]),
                "Value": round(float(min_vals[li]), ROUNDING_PRECISION),
            }
        elif stat == "Average":
            link_props["Flow"] = {
                "Value": round(float(sums[li]) / actual_periods, ROUNDING_PRECISION),
            }
            link_props["Flow_Unsig"] = link_props["Flow"]
            link_props["Flow_Sig"] = link_props["Flow"]
        elif stat == "Range":
            link_props["Flow"] = {
                "Value": round(float(max_vals[li] - min_vals[li]), ROUNDING_PRECISION),
            }
        elif stat == "StdDev":
            variance = float(wf_M2[li]) / actual_periods if actual_periods > 0 else 0.0
            link_props["Flow"] = {
                "Value": round(math.sqrt(variance), ROUNDING_PRECISION),
            }
        results[link_ids[li]] = link_props
    return results
