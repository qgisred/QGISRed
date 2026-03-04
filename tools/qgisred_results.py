import struct
import os

ROUNDING_PRECISION = 4

_LT_CV   = 0  
_LT_PIPE = 1  
_LT_PUMP = 2  
_LT_PRV  = 3  
_LT_PSV  = 4  
_LT_PBV  = 5  
_LT_FCV  = 6  
_LT_TCV  = 7  
_LT_GPV  = 8  
_NT_JUNCTION  = 0
_NT_RESERVOIR = 1
_NT_TANK      = 2
_VALVE_TYPES = {_LT_PRV, _LT_PSV, _LT_PBV, _LT_FCV, _LT_TCV, _LT_GPV}

_SI_XHEAD      = 0  # Pump shut off (cannot deliver head)
_SI_TEMPCLOSED = 1  # Temporarily closed
_SI_CLOSED     = 2  # Closed
_SI_OPEN       = 3  # Open
_SI_ACTIVE     = 4  # Active (control valve modulating)
_SI_XFLOW      = 5  # Pump exceeded max flow
_SI_XFCV       = 6  # FCV cannot deliver set flow
_SI_XPRESSURE  = 7  # Valve cannot sustain/reduce set pressure

"""Helpers"""
def _read_ids(f, count):
    """Helper to read an array of 32-character IDs."""
    ids = []
    for _ in range(count):
        raw_data = f.read(32)
        null_index = raw_data.find(b'\0')
        if null_index != -1:
            raw_id = raw_data[:null_index]
        else:
            raw_id = raw_data
        ids.append(raw_id.decode('ascii', errors='ignore').strip())
    return ids

def _read_floats(f, count):
    """Helper to read an array of floats safely."""
    if count <= 0:
        return []
    data = f.read(count * 4)
    if len(data) < count * 4:
        raise EOFError(f"Expected {count * 4} bytes but read only {len(data)}")
    return struct.unpack(f'{count}f', data)

def _read_ints(f, count):
    """Helper to read an array of signed ints safely."""
    if count <= 0:
        return []
    data = f.read(count * 4)
    if len(data) < count * 4:
        raise EOFError(f"Expected {count * 4} bytes but read only {len(data)}")
    return struct.unpack(f'{count}i', data)

def _resolve_link_status(indicator, link_type, Q, setting,
                          from_head, to_head, from_pressure, to_pressure):
    """
    Convert a raw EPANET status indicator (0–7) to a descriptive text status.

    indicator     : raw status float from binary (cast to int internally)
    link_type     : link type code (_LT_* constant)
    Q             : flow for this link at this time step
    setting       : Setting field value — speed ratio (n) for pumps,
                    Pset/Qset for valves
    from_head     : hydraulic head at the from-node
    to_head       : hydraulic head at the to-node
    from_pressure : pressure at the from-node
    to_pressure   : pressure at the to-node
    """
    ind = int(round(indicator))

    if link_type in (_LT_CV, _LT_PIPE):
        if ind == _SI_TEMPCLOSED:
            return "Temp Closed"
        elif ind == _SI_CLOSED:
            return "Closed"
        elif ind == _SI_OPEN:
            return "Open"
        else:
            return "Closed"
    elif link_type == _LT_PUMP:
        if ind == _SI_XHEAD:
            return "Closed (H>Hmax)"
        elif ind == _SI_CLOSED:
            return "Closed"
        elif ind == _SI_OPEN:
            return "Closed" if setting == 0 else "Open"
        elif ind == _SI_XFLOW:
            return "Open (Q>Qmax)"
        else:
            return "Closed"
    else:
        is_fcv = link_type == _LT_FCV
        is_psv = link_type == _LT_PSV
        is_prv = link_type == _LT_PRV
        is_pbv = link_type == _LT_PBV

        # State 13: Active (Rev Pump) — PBV, ACTIVE indicator, reverse flow
        if is_pbv and ind == _SI_ACTIVE and Q < 0:
            return "Active (Rev Pump)"

        # State 7: Open (Q < Qset) — FCV cannot deliver set flow
        if is_fcv and ind == _SI_XFCV:
            return "Open (Q<Qset)"

        # State 8: Closed (Q < 0) — FCV/PSV/PRV closed due to reverse flow
        if (is_fcv or is_psv or is_prv) and ind == _SI_CLOSED and from_head < to_head:
            return "Closed (Q<0)"

        # States 9/10: PSV — upstream pressure vs Pset (= setting field)
        if is_psv:
            if ind == _SI_CLOSED:
                return "Closed (Pup<Pset)"
            elif ind == _SI_OPEN:
                return "Open (Pup>Pset)"
            elif ind == _SI_XPRESSURE:
                return "Closed (Pup<Pset)" if from_pressure < setting else "Open (Pup>Pset)"
            elif ind == _SI_ACTIVE:
                return "Active"
            else:
                return "Closed"

        # States 11/12: PRV — downstream pressure vs Pset (= setting field)
        if is_prv:
            if ind == _SI_CLOSED:
                return "Closed (Pdw>Pset)"
            elif ind == _SI_OPEN:
                return "Open (Pdw<Pset)"
            elif ind == _SI_XPRESSURE:
                return "Closed (Pdw>Pset)" if to_pressure > setting else "Open (Pdw<Pset)"
            elif ind == _SI_ACTIVE:
                return "Active"
            else:
                return "Closed"

        # FCV Closed with ACTIVE indicator when Qset == 0
        if is_fcv and ind == _SI_ACTIVE and setting == 0:
            return "Closed"

        # General valve states (TCV, GPV, PBV non-reverse, or unmatched FCV)
        if ind == _SI_CLOSED:
            return "Closed"
        elif ind == _SI_OPEN:
            return "Open"
        elif ind == _SI_ACTIVE:
            return "Active"
        else:
            return "Closed"

def _get_out_file_metadata(f, include_lengths=False):
    """Parses the static part of the EPANET .out file and returns metadata."""

    prologue_fixed = f.read(15 * 4)
    if len(prologue_fixed) < 60:
        return None

    (magic1, version, n_nodes, n_tanks, n_links, n_pumps, n_valves,
     wq_type, wq_index, flow_units, pres_units, stats_flag,
     report_start, report_step, duration) = struct.unpack('15i', prologue_fixed)

    if magic1 != 516114521:
        return None

    f.seek(824, 1)
    node_ids = _read_ids(f, n_nodes)
    link_ids = _read_ids(f, n_links)
    link_from  = [x - 1 for x in _read_ints(f, n_links)]
    link_to    = [x - 1 for x in _read_ints(f, n_links)]

    link_types = _read_ints(f, n_links)
    tank_node_indices = [x - 1 for x in _read_ints(f, n_tanks)]
    tank_areas = _read_floats(f, n_tanks)
    f.seek(4 * n_nodes, 1)       # skip node elevations
    node_types = [_NT_JUNCTION] * n_nodes
    for i in range(n_tanks):
        node_idx = tank_node_indices[i]
        if tank_areas[i] == 0:
            node_types[node_idx] = _NT_RESERVOIR
        else:
            node_types[node_idx] = _NT_TANK

    link_lengths = None
    if include_lengths:
        link_lengths = _read_floats(f, n_links)
        f.seek(4 * n_links, 1)
    else:
        f.seek(8 * n_links, 1)

    f.seek((28 * n_pumps) + 4, 1)
    results_offset = f.tell()

    f.seek(0, 2)
    file_size = f.tell()
    f.seek(-12, 2)
    epilogue_data = f.read(12)
    num_periods, error_code, magic2 = struct.unpack('3i', epilogue_data)

    if num_periods > 0:
        period_size = (file_size - 12 - results_offset) // num_periods
    else:
        period_size = 0

    return {
        "n_nodes": n_nodes,
        "n_links": n_links,
        "n_tanks": n_tanks,
        "n_pumps": n_pumps,
        "report_start": report_start,
        "report_step": report_step,
        "num_periods": num_periods,
        "results_offset": results_offset,
        "period_size": period_size,
        "node_ids": node_ids,
        "link_ids": link_ids,
        "link_lengths": link_lengths,
        "node_types": node_types,
        "link_types": link_types,
        "link_from": link_from,
        "link_to": link_to,
    }

def _calculate_period_index(time_seconds, meta):
    """Calculates the reporting period index for a given time."""
    if meta["num_periods"] <= 1:
        return 0
    if meta["report_step"] <= 0:
        return 0
    period_index = int((time_seconds - meta["report_start"]) / meta["report_step"])
    return max(0, min(period_index, meta["num_periods"] - 1))

"""Results"""
def getOut_TimeNodesProperties(out_file_path, time_seconds):
    """Reads node results from an EPANET binary (.out) file for a specific time."""
    if not os.path.exists(out_file_path):
        return {}

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f)
        if not meta:
            return {}
        
        period_index = _calculate_period_index(time_seconds, meta)
        
        period_size = meta["period_size"]
        target_offset = meta["results_offset"] + (period_index * period_size)
        f.seek(target_offset)
        n = meta["n_nodes"]
        demands = _read_floats(f, n)
        heads = _read_floats(f, n)
        pressures = _read_floats(f, n)
        qualities = _read_floats(f, n)

        results = {}
        for i in range(n):
            results[meta["node_ids"][i]] = {
                "Pressure": round(float(pressures[i]), ROUNDING_PRECISION),
                "Head": round(float(heads[i]), ROUNDING_PRECISION),
                "Demand": round(float(demands[i]), ROUNDING_PRECISION),
                "Quality": round(float(qualities[i]), ROUNDING_PRECISION)
            }
        return results

def getOut_TimeLinksProperties(out_file_path, time_seconds):
    """Reads link results from an EPANET binary (.out) file for a specific time."""
    if not os.path.exists(out_file_path):
        return {}

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f, include_lengths=True)
        if not meta:
            return {}

        period_index = _calculate_period_index(time_seconds, meta)

        n = meta["n_nodes"]
        nl = meta["n_links"]
        base_offset = meta["results_offset"] + (period_index * meta["period_size"])

        f.seek(base_offset + n * 4)          # skip demands
        node_heads = _read_floats(f, n)
        node_pressures = _read_floats(f, n)
        f.seek(n * 4, 1)                     # skip node qualities

        flows          = _read_floats(f, nl)
        velocities     = _read_floats(f, nl)
        headlosses     = _read_floats(f, nl)
        qualities      = _read_floats(f, nl)
        statuses       = _read_floats(f, nl)
        settings       = _read_floats(f, nl)
        reaction_rates = _read_floats(f, nl)
        friction_rates = _read_floats(f, nl)

        results = {}
        for i in range(nl):
            link_type = meta["link_types"][i]
            from_idx = meta["link_from"][i]
            to_idx   = meta["link_to"][i]

            status_text = _resolve_link_status(
                indicator=float(statuses[i]),
                link_type=link_type,
                Q=float(flows[i]),
                setting=float(settings[i]),
                from_head=float(node_heads[from_idx]),
                to_head=float(node_heads[to_idx]),
                from_pressure=float(node_pressures[from_idx]),
                to_pressure=float(node_pressures[to_idx])
            )

            pumpOrValve = (link_type == _LT_PUMP) or (link_type in _VALVE_TYPES)
            unit_headloss = float(headlosses[i])
            length = meta["link_lengths"][i]
            if pumpOrValve:
                headloss_calc = unit_headloss
            else:
                headloss_calc = (unit_headloss * length) / 1000.0

            results[meta["link_ids"][i]] = {
                "Flow": round(float(flows[i]), ROUNDING_PRECISION),
                "Velocity": None if pumpOrValve else round(float(velocities[i]), ROUNDING_PRECISION),
                "HeadLoss": round(headloss_calc, ROUNDING_PRECISION),
                "UnitHdLoss": None if pumpOrValve else round(unit_headloss, ROUNDING_PRECISION),
                "FricFactor": None if pumpOrValve else round(float(friction_rates[i]), ROUNDING_PRECISION),
                "Status": status_text,
                "ReactRate": None if pumpOrValve else round(float(reaction_rates[i]), ROUNDING_PRECISION),
                "Quality": round(float(qualities[i]), ROUNDING_PRECISION)
            }
        return results

def getOut_TimeNodeProperties(out_file_path, time_seconds, node_id):
    """Returns properties for a specific node ID by seeking directly to its data."""
    if not os.path.exists(out_file_path):
        return {}

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f)
        if not meta or node_id not in meta["node_ids"]:
            return {}

        node_index = meta["node_ids"].index(node_id)
        period_index = _calculate_period_index(time_seconds, meta)
        
        period_size = meta["period_size"]
        base_node_offset = meta["results_offset"] + (period_index * period_size)
        
        vars_found = {}
        var_names = ["Demand", "Head", "Pressure", "Quality"]
        
        for i, name in enumerate(var_names):
            f.seek(base_node_offset + (i * meta["n_nodes"] * 4) + (node_index * 4))
            val = struct.unpack('f', f.read(4))[0]
            vars_found[name] = round(float(val), ROUNDING_PRECISION)
            
        return vars_found

def getOut_TimeLinkProperties(out_file_path, time_seconds, link_id):
    """Returns properties for a specific link ID by seeking directly to its data."""
    if not os.path.exists(out_file_path):
        return {}

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f)
        if not meta or link_id not in meta["link_ids"]:
            return {}

        link_index = meta["link_ids"].index(link_id)
        period_index = _calculate_period_index(time_seconds, meta)
        
        link_type = meta["link_types"][link_index]
        from_idx  = meta["link_from"][link_index]
        to_idx    = meta["link_to"][link_index]
        period_size = meta["period_size"]
        base_period_offset = meta["results_offset"] + (period_index * period_size)
        base_link_offset = base_period_offset + meta["n_nodes"] * 16

        var_names = ["Flow", "Velocity", "UnitHdLoss", "Quality", "Status", "Setting", "ReactRate", "FricFactor"]
        vars_found = {}

        nL, nT, nN = meta["n_links"], meta["n_tanks"], meta["n_nodes"]
        len_pos = 60 + 824 + (32 * nN) + (32 * nL) + (12 * nL + 8 * nT + 4 * nN) + (4 * link_index)
        f.seek(len_pos)
        length = struct.unpack('f', f.read(4))[0]

        pumpOrValve = (link_type == _LT_PUMP) or (link_type in _VALVE_TYPES)
        _BLANK_NAMES = {"Velocity", "UnitHdLoss", "FricFactor", "ReactRate"}

        for i, name in enumerate(var_names):
            f.seek(base_link_offset + (i * meta["n_links"] * 4) + (link_index * 4))
            val = struct.unpack('f', f.read(4))[0]
            if pumpOrValve and name in _BLANK_NAMES:
                vars_found[name] = None
                if name == "UnitHdLoss":
                    vars_found["HeadLoss"] = round(float(val), ROUNDING_PRECISION)
            else:
                vars_found[name] = round(float(val), ROUNDING_PRECISION)
                if name == "UnitHdLoss":
                    vars_found["HeadLoss"] = round((float(val) * length) / 1000.0, ROUNDING_PRECISION)

        f.seek(base_period_offset + nN * 4 + from_idx * 4)
        from_head = struct.unpack('f', f.read(4))[0]
        f.seek(base_period_offset + nN * 4 + to_idx * 4)
        to_head = struct.unpack('f', f.read(4))[0]

        f.seek(base_period_offset + nN * 8 + from_idx * 4)
        from_pressure = struct.unpack('f', f.read(4))[0]
        f.seek(base_period_offset + nN * 8 + to_idx * 4)
        to_pressure = struct.unpack('f', f.read(4))[0]

        vars_found["Status"] = _resolve_link_status(
            indicator=vars_found["Status"],
            link_type=link_type,
            Q=vars_found["Flow"],
            setting=vars_found["Setting"],
            from_head=from_head,
            to_head=to_head,
            from_pressure=from_pressure,
            to_pressure=to_pressure
        )

        return vars_found

def getOut_TimesNodeProperty(out_file_path, node_id, property_name):
    """Returns a time-series array for a specific property of a node."""
    if not os.path.exists(out_file_path):
        return []

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f)
        var_names = ["Demand", "Head", "Pressure", "Quality"]
        if not meta or node_id not in meta["node_ids"] or property_name not in var_names:
            return []

        node_index = meta["node_ids"].index(node_id)
        var_index = var_names.index(property_name)
        num_periods = meta["num_periods"]
        period_size = meta["period_size"]
        results_offset = meta["results_offset"]
        
        time_series = []
        for p in range(num_periods):
            pos = results_offset + (p * period_size) + (var_index * meta["n_nodes"] * 4) + (node_index * 4)
            f.seek(pos)
            val = struct.unpack('f', f.read(4))[0]
            time_series.append(round(float(val), ROUNDING_PRECISION))
            
        return time_series

def getOut_TimesLinkProperty(out_file_path, link_id, property_name):
    """Returns a time-series array for a specific property of a link."""
    if not os.path.exists(out_file_path):
        return []

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f, include_lengths=(property_name == "HeadLoss"))
        
        var_names = ["Flow", "Velocity", "UnitHdLoss", "Quality", "Status", "Setting", "ReactRate", "FricFactor"]
        calc_headloss = False
        effective_property = property_name
        
        if property_name == "HeadLoss":
            calc_headloss = True
            effective_property = "UnitHdLoss"
            
        if not meta or link_id not in meta["link_ids"] or effective_property not in var_names:
            return []

        link_index = meta["link_ids"].index(link_id)
        num_periods = meta["num_periods"]
        period_size = meta["period_size"]
        results_offset = meta["results_offset"]
        n_nodes = meta["n_nodes"]
        n_links = meta["n_links"]
        node_results_size = n_nodes * 16
        link_type = meta["link_types"][link_index]

        _BLANK_PROPS = {"Velocity", "UnitHdLoss", "FricFactor", "ReactRate"}
        if property_name in _BLANK_PROPS and ((link_type == _LT_PUMP) or (link_type in _VALVE_TYPES)):
            return [None] * num_periods

        if property_name == "Status":
            from_idx = meta["link_from"][link_index]
            to_idx   = meta["link_to"][link_index]
            time_series = []
            for p in range(num_periods):
                base = results_offset + p * period_size

                f.seek(base + node_results_size + 0 * n_links * 4 + link_index * 4)
                Q = struct.unpack('f', f.read(4))[0]

                f.seek(base + node_results_size + 5 * n_links * 4 + link_index * 4)
                setting = struct.unpack('f', f.read(4))[0]

                f.seek(base + node_results_size + 4 * n_links * 4 + link_index * 4)
                indicator = struct.unpack('f', f.read(4))[0]

                f.seek(base + n_nodes * 4 + from_idx * 4)
                from_head = struct.unpack('f', f.read(4))[0]
                f.seek(base + n_nodes * 4 + to_idx * 4)
                to_head = struct.unpack('f', f.read(4))[0]

                f.seek(base + n_nodes * 8 + from_idx * 4)
                from_pressure = struct.unpack('f', f.read(4))[0]
                f.seek(base + n_nodes * 8 + to_idx * 4)
                to_pressure = struct.unpack('f', f.read(4))[0]

                time_series.append(_resolve_link_status(
                    indicator, link_type, Q, setting,
                    from_head, to_head, from_pressure, to_pressure
                ))
            return time_series

        var_index = var_names.index(effective_property)
        length = meta["link_lengths"][link_index] if calc_headloss else 1.0

        time_series = []
        for p in range(num_periods):
            pos = results_offset + (p * period_size) + node_results_size + (var_index * n_links * 4) + (link_index * 4)
            f.seek(pos)
            val = struct.unpack('f', f.read(4))[0]

            final_val = float(val)
            if calc_headloss:
                if (link_type == _LT_PUMP) or (link_type in _VALVE_TYPES):
                    final_val = float(val)
                else:
                    final_val = (final_val * length) / 1000.0

            time_series.append(round(final_val, ROUNDING_PRECISION))

        return time_series

"""Statistics"""
def getOut_StatNodesProperties(out_file_path, stat):
    """Returns a statistic for each node property across all reporting periods.

    stat: "Max" | "Min" | "Mean" | "Range" | "StdDev"

    Max/Min return {"Time": int, "Value": float}.
    Mean, Range and StdDev return {"Value": float}.

    Returns:
        dict[node_id, dict[property, dict]]
    """
    import math

    VALID_STATS = {"Max", "Min", "Mean", "Range", "StdDev"}
    if stat not in VALID_STATS:
        raise ValueError(f"stat must be one of {VALID_STATS}")

    if not os.path.exists(out_file_path):
        return {}

    with open(out_file_path, 'rb') as f:
        meta = _get_out_file_metadata(f)
        if not meta or meta["num_periods"] == 0:
            return {}

        n              = meta["n_nodes"]
        num_periods    = meta["num_periods"]
        report_start   = meta["report_start"]
        report_step    = meta["report_step"]
        results_offset = meta["results_offset"]
        period_size    = meta["period_size"]
        node_ids       = meta["node_ids"]

        # Binary layout order: Demand=0, Head=1, Pressure=2, Quality=3
        var_names  = ["Demand", "Head", "Pressure", "Quality"]
        n_vars     = len(var_names)
        node_block = n_vars * n
        fmt        = f'{node_block}f'
        byte_count = node_block * 4

        need_max = stat in ("Max", "Range")
        need_min = stat in ("Min", "Range")

        NEG_INF = float('-inf')
        POS_INF = float('inf')

        if need_max:
            max_vals  = [[NEG_INF] * n for _ in range(n_vars)]
            max_times = [[-1]       * n for _ in range(n_vars)]
        if need_min:
            min_vals  = [[POS_INF] * n for _ in range(n_vars)]
            min_times = [[-1]      * n for _ in range(n_vars)]
        if stat == "Mean":
            sums = [[0.0] * n for _ in range(n_vars)]
        if stat == "StdDev":
            # Welford's online algorithm: track count, mean, M2
            wf_mean = [[0.0] * n for _ in range(n_vars)]
            wf_M2   = [[0.0] * n for _ in range(n_vars)]

        actual_periods = 0
        for p in range(num_periods):
            time_s = report_start + p * report_step
            f.seek(results_offset + p * period_size)
            raw = f.read(byte_count)
            if len(raw) < byte_count:
                break
            vals = struct.unpack(fmt, raw)
            actual_periods += 1

            for vi in range(n_vars):
                base = vi * n
                for ni in range(n):
                    v = vals[base + ni]
                    if need_max:
                        if v > max_vals[vi][ni]:
                            max_vals[vi][ni]  = v
                            max_times[vi][ni] = time_s
                    if need_min:
                        if v < min_vals[vi][ni]:
                            min_vals[vi][ni]  = v
                            min_times[vi][ni] = time_s
                    if stat == "Mean":
                        sums[vi][ni] += v
                    if stat == "StdDev":
                        delta = v - wf_mean[vi][ni]
                        wf_mean[vi][ni] += delta / actual_periods
                        wf_M2[vi][ni]   += delta * (v - wf_mean[vi][ni])

        output_order = ["Pressure", "Head", "Demand", "Quality"]
        var_idx = {name: i for i, name in enumerate(var_names)}

        results = {}
        for ni in range(n):
            node_props = {}
            for name in output_order:
                vi = var_idx[name]
                if stat == "Max":
                    node_props[name] = {
                        "Time":  max_times[vi][ni],
                        "Value": round(float(max_vals[vi][ni]), ROUNDING_PRECISION)
                    }
                elif stat == "Min":
                    node_props[name] = {
                        "Time":  min_times[vi][ni],
                        "Value": round(float(min_vals[vi][ni]), ROUNDING_PRECISION)
                    }
                elif stat == "Mean":
                    node_props[name] = {
                        "Value": round(sums[vi][ni] / actual_periods, ROUNDING_PRECISION)
                    }
                elif stat == "Range":
                    node_props[name] = {
                        "Value": round(float(max_vals[vi][ni] - min_vals[vi][ni]), ROUNDING_PRECISION)
                    }
                elif stat == "StdDev":
                    variance = wf_M2[vi][ni] / actual_periods if actual_periods > 0 else 0.0
                    node_props[name] = {
                        "Value": round(math.sqrt(variance), ROUNDING_PRECISION)
                    }
            results[node_ids[ni]] = node_props
        return results
