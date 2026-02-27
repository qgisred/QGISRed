import struct
import os

ROUNDING_PRECISION = 4

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

    f.seek((12 * n_links) + (8 * n_tanks) + (4 * n_nodes), 1)
    
    link_lengths = None
    if include_lengths:
        link_lengths = _read_floats(f, n_links)
        f.seek(4 * n_links, 1)
    else:
        f.seek(8 * n_links, 1)
    
    f.seek((28 * n_pumps) + 4, 1)
    results_offset = f.tell()

    # Calculate results_offset from the end of file (epilogue)
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
        "link_lengths": link_lengths
    }

def _calculate_period_index(time_seconds, meta):
    """Calculates the reporting period index for a given time."""
    if meta["num_periods"] <= 1:
        return 0
    if meta["report_step"] <= 0:
        return 0
    period_index = int((time_seconds - meta["report_start"]) / meta["report_step"])
    return max(0, min(period_index, meta["num_periods"] - 1))

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

        period_size = meta["period_size"]
        target_offset = meta["results_offset"] + (period_index * period_size) + (meta["n_nodes"] * 16)
        f.seek(target_offset)

        nl = meta["n_links"]
        flows = _read_floats(f, nl)
        velocities = _read_floats(f, nl)
        headlosses = _read_floats(f, nl)
        qualities = _read_floats(f, nl)
        statuses = _read_floats(f, nl)

        results = {}
        for i in range(nl):
            unit_headloss = float(headlosses[i])
            length = meta["link_lengths"][i]
            headloss_calc = (unit_headloss * length) / 1000.0
            
            results[meta["link_ids"][i]] = {
                "Flow": round(float(flows[i]), ROUNDING_PRECISION),
                "Velocity": round(float(velocities[i]), ROUNDING_PRECISION),
                "UnitHeadLoss": round(unit_headloss, ROUNDING_PRECISION),
                "HeadLoss": round(headloss_calc, ROUNDING_PRECISION),
                "Status": round(float(statuses[i]), ROUNDING_PRECISION),
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
        
        period_size = meta["period_size"]
        base_link_offset = meta["results_offset"] + (period_index * period_size) + (meta["n_nodes"] * 16)
        
        var_names = ["Flow", "Velocity", "UnitHeadLoss", "Quality", "Status"]
        vars_found = {}

        nL, nT, nN = meta["n_links"], meta["n_tanks"], meta["n_nodes"]
        len_pos = 60 + 824 + (32 * nN) + (32 * nL) + (12 * nL + 8 * nT + 4 * nN) + (4 * link_index)
        f.seek(len_pos)
        length = struct.unpack('f', f.read(4))[0]

        for i, name in enumerate(var_names):
            f.seek(base_link_offset + (i * meta["n_links"] * 4) + (link_index * 4))
            val = struct.unpack('f', f.read(4))[0]
            vars_found[name] = round(float(val), ROUNDING_PRECISION)
            if (name == "UnitHeadLoss"):
                vars_found["HeadLoss"] = round((float(val) * length) / 1000.0, ROUNDING_PRECISION)
            
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
        
        var_names = ["Flow", "Velocity", "UnitHeadLoss", "Quality", "Status"]
        calc_headloss = False
        effective_property = property_name
        
        if property_name == "HeadLoss":
            calc_headloss = True
            effective_property = "UnitHeadLoss"
            
        if not meta or link_id not in meta["link_ids"] or effective_property not in var_names:
            return []

        link_index = meta["link_ids"].index(link_id)
        var_index = var_names.index(effective_property)
        num_periods = meta["num_periods"]
        period_size = meta["period_size"]
        results_offset = meta["results_offset"]
        node_results_size = meta["n_nodes"] * 16
        length = meta["link_lengths"][link_index]
        
        time_series = []
        for p in range(num_periods):
            pos = results_offset + (p * period_size) + node_results_size + (var_index * meta["n_links"] * 4) + (link_index * 4)
            f.seek(pos)
            val = struct.unpack('f', f.read(4))[0]
            
            final_val = float(val)
            if calc_headloss:
                final_val = (final_val * length) / 1000.0
                
            time_series.append(round(final_val, ROUNDING_PRECISION))
            
        return time_series
