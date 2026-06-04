import math
import os
import struct

from .qgisred_results_binary import (
    _LT_PUMP,
    _VALVE_TYPES,
    average_node_pressure_excluding_reservoirs,
    _resolve_link_status,
    getOut_Metadata,
    total_water_demand_from_demands,
    total_water_supply_from_demands,
)

_HYD_MAGIC = 516114521
_HYD_HEADER_SIZE = 32

# EPANET flow unit codes (from EN_FlowUnits enum)
_FU_CFS = 0
_FU_GPM = 1
_FU_MGD = 2
_FU_IMGD = 3
_FU_AFD = 4
_FU_LPS = 5
_FU_LPM = 6
_FU_MLD = 7
_FU_CMH = 8
_FU_CMD = 9

# Conversion from internal cfs to output flow units
_CFS_TO_FLOW = {
    _FU_CFS: 1.0,
    _FU_GPM: 448.8311688,
    _FU_MGD: 0.646317,
    _FU_IMGD: 0.5382,
    _FU_AFD: 1.98347,
    _FU_LPS: 28.3168466,
    _FU_LPM: 1699.0108,
    _FU_MLD: 2.446575,
    _FU_CMH: 101.940647,
    _FU_CMD: 2446.57553,
}

# 1 cfs in m3/s
_CFS_TO_M3S = 0.0283168466


def _hyd_usable_end(data):
    payload_len = len(data) - _HYD_HEADER_SIZE
    if payload_len % 4 == 1 and data[-1] == 0x1A:
        return len(data) - 1
    return len(data)


def _hyd_record_size_bytes(n_nodes, n_links):
    # 4(Htime) + 2*Nnodes*4 + 3*Nlinks*4 + 4(hydstep)
    return 8 + (8 * n_nodes) + (12 * n_links)


def _iter_hyd_records(data, n_nodes, n_links):
    """Return (offsets, times, steps) scanning fixed-format records until hydstep==0."""
    rec_size = _hyd_record_size_bytes(n_nodes, n_links)
    usable_end = _hyd_usable_end(data)
    offsets = []
    times = []
    steps = []
    off = _HYD_HEADER_SIZE
    while off + rec_size <= usable_end:
        time_s = struct.unpack_from("<i", data, off)[0]
        step_pos = off + rec_size - 4
        hydstep = struct.unpack_from("<i", data, step_pos)[0]
        offsets.append(off)
        times.append(time_s)
        steps.append(hydstep)
        off += rec_size
        if hydstep == 0:
            break
    return offsets, times, steps


def _map_hyd_status_to_out_indicator(status_value):
    """Map .hyd LinkStatus enum to the indicator semantics used by _resolve_link_status."""
    s = int(round(float(status_value)))
    # EPANET variants can store:
    # - indicator-style statuses (0..7 where OPEN=3, ACTIVE=4) -> already compatible
    # - compact enum statuses (CLOSED=0, OPEN=1, ACTIVE=2)      -> remap to 2/3/4
    if s in (0, 1, 2):
        compact_map = {0: 2, 1: 3, 2: 4}
        return compact_map[s]
    return s


def _is_metric_model(flow_units):
    # EPANET metric flow units are LPS and above.
    return flow_units is not None and int(flow_units) >= _FU_LPS


def _head_factor_from_units(flow_units):
    # Internal hydraulic head in .hyd is feet; convert to meters for SI projects.
    return 0.3048 if _is_metric_model(flow_units) else 1.0


def _flow_factor_from_units(flow_units):
    return _CFS_TO_FLOW.get(int(flow_units), 1.0)


def _pressure_factor_from_units(flow_units, pres_units):
    # Convert pressure from head-difference units to requested pressure units.
    # pres_units codes (EPANET): 0=psi, 1=kPa, 2=meters
    pu = int(pres_units) if pres_units is not None else 2
    is_metric = _is_metric_model(flow_units)
    if pu == 0:  # psi
        return 0.4333 if not is_metric else 1.422334
    if pu == 1:  # kPa
        return 2.98898 if not is_metric else 9.80665
    # meters or unknown: keep as head units
    return 1.0


def _diameter_to_meters(diameter_value, flow_units):
    if diameter_value is None:
        return None
    d = float(diameter_value)
    if _is_metric_model(flow_units):
        # SI projects store diameter in mm in .out static section
        return d / 1000.0
    # US projects store diameter in inches
    return d * 0.0254


def _diameter_to_feet(diameter_value):
    if diameter_value is None:
        return None
    return float(diameter_value) / 12.0


def _unit_headloss_from_headloss(headloss, length):
    if length is None or length <= 0:
        return None
    # Match .out semantics: unit headloss per 1000 length-units
    return (headloss * 1000.0) / length


def _detect_hyd_status_compact(data, n_nodes, n_links, offsets):
    # Compact enum usually 0/1/2; indicator style uses OPEN=3 etc.
    max_code = -10
    for off in offsets[: min(len(offsets), 8)]:
        status_off = off + 4 + (2 * n_nodes) * 4 + n_links * 4
        for i in range(min(n_links, 64)):
            s = int(round(struct.unpack_from("<f", data, status_off + i * 4)[0]))
            if s > max_code:
                max_code = s
            if max_code >= 3:
                return False
    return max_code <= 2


def getHyd_Metadata(hyd_file_path, out_file_path):
    """Read .hyd metadata and combine with static network metadata from .out."""
    if not os.path.exists(hyd_file_path) or not os.path.exists(out_file_path):
        return None

    with open(out_file_path, "rb") as out_f:
        out_meta = getOut_Metadata(out_f, include_lengths=True, include_geometry=True)
    if not out_meta:
        return None

    with open(hyd_file_path, "rb") as hyd_f:
        data = hyd_f.read()
    if len(data) < _HYD_HEADER_SIZE + 4:
        return None

    magic, version, n_nodes, n_links, n_tanks, n_pumps, n_valves, duration = struct.unpack_from("<8i", data, 0)
    if magic != _HYD_MAGIC:
        return None
    if (
        n_nodes != out_meta["n_nodes"]
        or n_links != out_meta["n_links"]
        or n_tanks != out_meta["n_tanks"]
        or n_pumps != out_meta["n_pumps"]
    ):
        return None

    rec_size = _hyd_record_size_bytes(n_nodes, n_links)
    offsets, times, steps = _iter_hyd_records(data, n_nodes, n_links)
    if not offsets:
        return None
    status_compact = _detect_hyd_status_compact(data, n_nodes, n_links, offsets)

    meta = dict(out_meta)
    meta.update({
        "hyd_path": hyd_file_path,
        "hyd_magic": magic,
        "hyd_version": version,
        "hyd_duration": duration,
        "hyd_num_periods": len(offsets),
        "hyd_period_size": rec_size,
        "hyd_results_offset": _HYD_HEADER_SIZE,
        "hyd_record_words": rec_size // 4,
        "hyd_record_offsets": offsets,
        "hyd_status_compact": status_compact,
        "hyd_times": times,
        "hyd_steps": steps,
        "hyd_report_start": times[0] if times else out_meta["report_start"],
        "hyd_report_step": steps[0] if steps and steps[0] > 0 else (times[1] - times[0] if len(times) > 1 else out_meta["report_step"]),
    })
    return meta


def _calculate_hyd_period_index(time_seconds, meta):
    n = meta["hyd_num_periods"]
    if n <= 1:
        return 0
    times = meta.get("hyd_times") or []
    if times:
        idx = min(range(len(times)), key=lambda i: abs(int(times[i]) - int(time_seconds)))
        return max(0, min(idx, n - 1))
    step = meta.get("hyd_report_step", 0)
    if step <= 0:
        return 0
    idx = int((time_seconds - meta.get("hyd_report_start", 0)) / step)
    return max(0, min(idx, n - 1))


def _read_hyd_period(hyd_file_path, meta, period_index):
    n = meta["n_nodes"]
    nl = meta["n_links"]
    offsets = meta.get("hyd_record_offsets") or []
    if offsets and 0 <= period_index < len(offsets):
        base = offsets[period_index]
    else:
        base = meta["hyd_results_offset"] + period_index * meta["hyd_period_size"]
    with open(hyd_file_path, "rb") as f:
        f.seek(base)
        data = f.read(meta["hyd_period_size"])
    if len(data) < meta["hyd_period_size"]:
        raise EOFError("Unexpected EOF while reading .hyd period")

    off = 0
    time_s = struct.unpack_from("<i", data, off)[0]
    off += 4
    demands = struct.unpack_from(f"<{n}f", data, off)
    off += 4 * n
    heads = struct.unpack_from(f"<{n}f", data, off)
    off += 4 * n
    flows = struct.unpack_from(f"<{nl}f", data, off)
    off += 4 * nl
    statuses = struct.unpack_from(f"<{nl}f", data, off)
    off += 4 * nl
    settings = struct.unpack_from(f"<{nl}f", data, off)
    return time_s, demands, heads, flows, statuses, settings


def getHyd_TimeNodesProperties(hyd_file_path, out_file_path, time_seconds):
    """Read node properties for one hydraulic calculation instant."""
    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return {}

    p = _calculate_hyd_period_index(time_seconds, meta)
    _, demands, heads, _, _, _ = _read_hyd_period(hyd_file_path, meta, p)
    head_factor = _head_factor_from_units(meta.get("flow_units"))
    pressure_factor = _pressure_factor_from_units(meta.get("flow_units"), meta.get("pres_units"))
    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    elevations = meta.get("node_elevations") or [0.0] * meta["n_nodes"]

    results = {}
    for i, node_id in enumerate(meta["node_ids"]):
        head = float(heads[i]) * head_factor
        elevation = float(elevations[i]) if i < len(elevations) else 0.0
        pressure = (head - elevation) * pressure_factor
        results[node_id] = {
            "Pressure": pressure,
            "Head": head,
            "Demand": float(demands[i]) * flow_factor,
            "Quality": None,
        }
    return results


def getHyd_TimeLinksProperties(hyd_file_path, out_file_path, time_seconds):
    """Read link properties for one hydraulic calculation instant."""
    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return {}

    p = _calculate_hyd_period_index(time_seconds, meta)
    _, _, node_heads, flows, statuses, settings = _read_hyd_period(hyd_file_path, meta, p)
    head_factor = _head_factor_from_units(meta.get("flow_units"))
    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    status_compact = bool(meta.get("hyd_status_compact", False))
    node_elevations = meta.get("node_elevations") or [0.0] * meta["n_nodes"]
    node_heads_converted = [float(h) * head_factor for h in node_heads]
    node_pressures = [float(h) - float(z) for h, z in zip(node_heads_converted, node_elevations)]
    link_lengths = meta.get("link_lengths") or []
    link_diameters = meta.get("link_diameters") or []

    results = {}
    for i, link_id in enumerate(meta["link_ids"]):
        link_type = meta["link_types"][i]
        from_idx = meta["link_from"][i]
        to_idx = meta["link_to"][i]
        flow_internal_cfs = float(flows[i])
        flow = flow_internal_cfs * flow_factor
        setting = float(settings[i])
        from_head = float(node_heads_converted[from_idx])
        to_head = float(node_heads_converted[to_idx])
        from_pressure = float(node_pressures[from_idx])
        to_pressure = float(node_pressures[to_idx])
        is_pump_or_valve = (link_type == _LT_PUMP) or (link_type in _VALVE_TYPES)

        status_text = _resolve_link_status(
            indicator=float(_map_hyd_status_to_out_indicator(statuses[i]) if status_compact else int(round(float(statuses[i])))),
            link_type=link_type,
            Q=flow_internal_cfs,
            setting=setting,
            from_head=from_head,
            to_head=to_head,
            from_pressure=from_pressure,
            to_pressure=to_pressure,
        )

        is_closed_flag = "CLOSED" in status_text.upper() or abs(flow_internal_cfs) <= 1e-12
        if link_type == _LT_PUMP:
            # Match .out convention for pumps (head gain represented as negative loss),
            # but closed pumps report zero loss.
            if is_closed_flag:
                headloss = 0.0
            else:
                headloss = from_head - to_head
            headloss_abs = abs(headloss)
        else:
            # .out reports pipe/valve headloss as positive magnitude.
            headloss_abs = abs(from_head - to_head)
            headloss = headloss_abs
        velocity = None
        unit_headloss = None
        friction = None

        if not is_pump_or_valve:
            flow_units = meta.get("flow_units")
            diameter = _diameter_to_meters(link_diameters[i] if i < len(link_diameters) else None, flow_units)
            length = float(link_lengths[i]) if i < len(link_lengths) else 0.0
            if is_closed_flag:
                velocity = 0.0
                headloss = 0.0
                unit_headloss = 0.0
                friction = 0.0
            else:
                if _is_metric_model(flow_units):
                    if diameter and diameter > 0:
                        area_m2 = math.pi * (diameter ** 2) / 4.0
                        velocity = abs(flow_internal_cfs * _CFS_TO_M3S) / area_m2 if area_m2 > 0 else None
                else:
                    d_ft = _diameter_to_feet(link_diameters[i] if i < len(link_diameters) else None)
                    if d_ft and d_ft > 0:
                        area_ft2 = math.pi * (d_ft ** 2) / 4.0
                        velocity = abs(flow_internal_cfs) / area_ft2 if area_ft2 > 0 else None

                if length > 0:
                    unit_headloss = _unit_headloss_from_headloss(headloss_abs, length)

                # Darcy-Weisbach factor in SI base units.
                if diameter and diameter > 0 and length > 0 and abs(flow_internal_cfs * _CFS_TO_M3S) > 1e-12:
                    q_m3s = flow_internal_cfs * _CFS_TO_M3S
                    slope = (headloss_abs if _is_metric_model(flow_units) else headloss_abs * 0.3048) / (length if _is_metric_model(flow_units) else length * 0.3048)
                    friction = 12.104 * (diameter ** 5) * slope / (q_m3s ** 2)

        results[link_id] = {
            "Status": status_text,
            "Flow": flow,
            "Velocity": velocity,
            "HeadLoss": headloss,
            "UnitHdLoss": unit_headloss,
            "FricFactor": friction,
            "ReactRate": None,
            "Quality": None,
        }
    return results


def _aggregate_numeric_timeseries(values, times, stat, *, flow_abs_mode=False):
    if not values:
        return None
    pairs = [(t, v) for t, v in zip(times, values) if v is not None]
    if not pairs:
        return None

    if flow_abs_mode:
        # Match .out semantics: extrema/range/stddev on |Q|, but min/max keep signed Q at extremum time.
        abs_vals = [abs(v) for _, v in pairs]
        signed_vals = [v for _, v in pairs]
        if stat == "Maximum":
            idx = max(range(len(abs_vals)), key=lambda i: abs_vals[i])
            return {"Time": int(pairs[idx][0]), "Value": float(signed_vals[idx])}
        if stat == "Minimum":
            idx = min(range(len(abs_vals)), key=lambda i: abs_vals[i])
            return {"Time": int(pairs[idx][0]), "Value": float(signed_vals[idx])}
        if stat == "Average":
            return {
                "Flow_Unsig": {"Value": float(sum(abs_vals) / len(abs_vals))},
                "Flow_Sig": {"Value": float(sum(signed_vals) / len(signed_vals))},
            }
        if stat == "Range":
            return {"Value": float(max(abs_vals) - min(abs_vals))}
        if stat == "StdDev":
            mean = float(sum(abs_vals) / len(abs_vals))
            var = float(sum((x - mean) ** 2 for x in abs_vals) / len(abs_vals))
            return {"Value": math.sqrt(var)}
        return None

    vals = [v for _, v in pairs]
    if stat == "Maximum":
        idx = max(range(len(vals)), key=lambda i: vals[i])
        return {"Time": int(pairs[idx][0]), "Value": float(vals[idx])}
    if stat == "Minimum":
        idx = min(range(len(vals)), key=lambda i: vals[i])
        return {"Time": int(pairs[idx][0]), "Value": float(vals[idx])}
    if stat == "Average":
        return {"Value": float(sum(vals) / len(vals))}
    if stat == "Range":
        return {"Value": float(max(vals) - min(vals))}
    if stat == "StdDev":
        mean = float(sum(vals) / len(vals))
        var = float(sum((x - mean) ** 2 for x in vals) / len(vals))
        return {"Value": math.sqrt(var)}
    return None


def getHyd_StatNodesProperties(hyd_file_path, out_file_path, stat):
    """Node statistics from .hyd for stat in {'Maximum','Minimum','Average','Range','StdDev'}."""
    valid = {"Maximum", "Minimum", "Average", "Range", "StdDev"}
    if stat not in valid:
        raise ValueError(f"stat must be one of {valid}")

    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return {}

    times = list(meta.get("hyd_times") or [])
    if not times:
        n = meta.get("hyd_num_periods", 0)
        start = meta.get("hyd_report_start", 0)
        step = meta.get("hyd_report_step", 0)
        times = [start + i * step for i in range(n)]
    if not times:
        return {}

    per_time = [getHyd_TimeNodesProperties(hyd_file_path, out_file_path, t) for t in times]
    if not per_time:
        return {}

    node_ids = meta.get("node_ids") or list(per_time[0].keys())
    result = {}
    for node_id in node_ids:
        pressure_vals = [step.get(node_id, {}).get("Pressure") for step in per_time]
        head_vals = [step.get(node_id, {}).get("Head") for step in per_time]
        demand_vals = [step.get(node_id, {}).get("Demand") for step in per_time]
        node_stats = {}
        p_stat = _aggregate_numeric_timeseries(pressure_vals, times, stat)
        h_stat = _aggregate_numeric_timeseries(head_vals, times, stat)
        d_stat = _aggregate_numeric_timeseries(demand_vals, times, stat)
        if p_stat is not None:
            node_stats["Pressure"] = p_stat
        if h_stat is not None:
            node_stats["Head"] = h_stat
        if d_stat is not None:
            node_stats["Demand"] = d_stat
        result[node_id] = node_stats
    return result


def getHyd_StatLinksProperties(hyd_file_path, out_file_path, stat):
    """Link statistics from .hyd for stat in {'Maximum','Minimum','Average','Range','StdDev'}."""
    valid = {"Maximum", "Minimum", "Average", "Range", "StdDev"}
    if stat not in valid:
        raise ValueError(f"stat must be one of {valid}")

    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return {}

    times = list(meta.get("hyd_times") or [])
    if not times:
        n = meta.get("hyd_num_periods", 0)
        start = meta.get("hyd_report_start", 0)
        step = meta.get("hyd_report_step", 0)
        times = [start + i * step for i in range(n)]
    if not times:
        return {}

    per_time = [getHyd_TimeLinksProperties(hyd_file_path, out_file_path, t) for t in times]
    if not per_time:
        return {}

    link_ids = meta.get("link_ids") or list(per_time[0].keys())
    result = {}
    for link_id in link_ids:
        flow_vals = [step.get(link_id, {}).get("Flow") for step in per_time]
        vel_vals = [step.get(link_id, {}).get("Velocity") for step in per_time]
        hl_vals = [step.get(link_id, {}).get("HeadLoss") for step in per_time]
        uhl_vals = [step.get(link_id, {}).get("UnitHdLoss") for step in per_time]
        ff_vals = [step.get(link_id, {}).get("FricFactor") for step in per_time]

        link_stats = {}
        flow_stat = _aggregate_numeric_timeseries(flow_vals, times, stat, flow_abs_mode=True)
        if flow_stat is not None:
            if stat == "Average" and isinstance(flow_stat, dict) and "Flow_Unsig" in flow_stat:
                link_stats.update(flow_stat)
            else:
                link_stats["Flow"] = flow_stat

        for name, vals in (
            ("Velocity", vel_vals),
            ("HeadLoss", hl_vals),
            ("UnitHdLoss", uhl_vals),
            ("FricFactor", ff_vals),
        ):
            agg = _aggregate_numeric_timeseries(vals, times, stat)
            if agg is not None:
                link_stats[name] = agg

        result[link_id] = link_stats
    return result


def getHyd_TimesTotalWaterSupply(hyd_file_path, out_file_path):
    """Time series of total water supply from hydraulic (.hyd) calculation steps."""
    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []

    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    node_types = meta["node_types"]
    time_series = []
    for p in range(meta["hyd_num_periods"]):
        _, demands, _, _, _, _ = _read_hyd_period(hyd_file_path, meta, p)
        scaled = [float(d) * flow_factor for d in demands]
        time_series.append(total_water_supply_from_demands(scaled, node_types))
    return time_series


def getHyd_TimesTotalWaterDemand(hyd_file_path, out_file_path):
    """Time series of total water demand from hydraulic (.hyd) calculation steps."""
    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []

    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    node_types = meta["node_types"]
    time_series = []
    for p in range(meta["hyd_num_periods"]):
        _, demands, _, _, _, _ = _read_hyd_period(hyd_file_path, meta, p)
        scaled = [float(d) * flow_factor for d in demands]
        time_series.append(total_water_demand_from_demands(scaled, node_types))
    return time_series


def getHyd_TimesAverageNodePressure(hyd_file_path, out_file_path):
    """Mean nodal pressure at each .hyd step (junctions and tanks; reservoirs excluded)."""
    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []

    head_factor = _head_factor_from_units(meta.get("flow_units"))
    pressure_factor = _pressure_factor_from_units(meta.get("flow_units"), meta.get("pres_units"))
    node_types = meta["node_types"]
    elevations = meta.get("node_elevations") or [0.0] * meta["n_nodes"]
    time_series = []
    for p in range(meta["hyd_num_periods"]):
        _, _, heads, _, _, _ = _read_hyd_period(hyd_file_path, meta, p)
        pressures = []
        for i, _node_type in enumerate(node_types):
            head = float(heads[i]) * head_factor
            elevation = float(elevations[i]) if i < len(elevations) else 0.0
            pressures.append((head - elevation) * pressure_factor)
        time_series.append(
            average_node_pressure_excluding_reservoirs(pressures, node_types)
        )
    return time_series
