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

def _get_out_file_metadata(f, include_lengths=False):
    """Parses the static part of the EPANET .out file and returns metadata."""
    # --- Read Prologue ---
    prologue_fixed = f.read(15 * 4)
    if len(prologue_fixed) < 60:
        return None
    
    (magic1, version, n_nodes, n_tanks, n_links, n_pumps, n_valves, 
     wq_type, wq_index, flow_units, pres_units, stats_flag, 
     report_start, report_step, duration) = struct.unpack('15i', prologue_fixed)

    if magic1 != 516114521:
        return None

    # Skip Titles/Filenames (824 bytes)
    f.seek(824, 1)

    # Read Node IDs
    node_ids = _read_ids(f, n_nodes)
    
    # Read Link IDs
    link_ids = _read_ids(f, n_links)

    # 1. Skip Head Node, Tail Node, and Type Code (12 per link), 
    #    Tank Index and Surface Area (8 per tank), 
    #    Elevation of Each Node (4 per node)
    f.seek((12 * n_links) + (8 * n_tanks) + (4 * n_nodes), 1)
    
    link_lengths = None
    if include_lengths:
        # 2. Read Length of Each Link
        link_lengths = struct.unpack(f'{n_links}f', f.read(4 * n_links))
    else:
        # Just skip them
        f.seek(4 * n_links, 1)
    
    # 3. Skip Diameter of Each Link (4 per link) and Energy Section (28 per pump + 4)
    # ... offset to epilogue logic follows ...
    f.seek((4 * n_links) + (28 * n_pumps) + 4, 1)
    results_offset = f.tell()

    # Read Epilogue (last 12 bytes)
    f.seek(-12, 2)
    epilogue_data = f.read(12)
    if len(epilogue_data) < 12:
        return None
    num_periods, error_code, magic2 = struct.unpack('3i', epilogue_data)

    return {
        "n_nodes": n_nodes,
        "n_links": n_links,
        "n_tanks": n_tanks,
        "n_pumps": n_pumps,
        "report_start": report_start,
        "report_step": report_step,
        "num_periods": num_periods,
        "results_offset": results_offset,
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
        
        # Seek to period (each period has Nodes[4] + Links[8] variables)
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
        target_offset = meta["results_offset"] + (period_index * period_size)
        f.seek(target_offset)

        # Read Node Results (4 blocks: Demand, Head, Pressure, Quality)
        n = meta["n_nodes"]
        demands = struct.unpack(f'{n}f', f.read(n * 4))
        heads = struct.unpack(f'{n}f', f.read(n * 4))
        pressures = struct.unpack(f'{n}f', f.read(n * 4))
        qualities = struct.unpack(f'{n}f', f.read(n * 4))

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

        # Seek to period, skip node results
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
        target_offset = meta["results_offset"] + (period_index * period_size) + (meta["n_nodes"] * 16)
        f.seek(target_offset)

        # Read Link Results (8 blocks)
        nl = meta["n_links"]
        flows = struct.unpack(f'{nl}f', f.read(nl * 4))
        velocities = struct.unpack(f'{nl}f', f.read(nl * 4))
        headlosses = struct.unpack(f'{nl}f', f.read(nl * 4))
        qualities = struct.unpack(f'{nl}f', f.read(nl * 4))
        statuses = struct.unpack(f'{nl}f', f.read(nl * 4))

        results = {}
        for i in range(nl):
            unit_headloss = float(headlosses[i])
            length = meta["link_lengths"][i]
            headloss_calc = (unit_headloss * length) / 1000.0
            
            results[meta["link_ids"][i]] = {
                "Flow": round(float(flows[i]), ROUNDING_PRECISION),
                "Velocity": round(float(velocities[i]), ROUNDING_PRECISION),
                "UnitHeadloss": round(unit_headloss, ROUNDING_PRECISION),
                "Headloss": round(headloss_calc, ROUNDING_PRECISION),
                "Quality": round(float(qualities[i]), ROUNDING_PRECISION),
                "Status": round(float(statuses[i]), ROUNDING_PRECISION)
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
        
        # Base offset for this period's nodes
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
        base_node_offset = meta["results_offset"] + (period_index * period_size)
        
        # Each variable is a block of n_nodes * 4 bytes
        # Variable Order: Demand, Head, Pressure, Quality
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
        
        # Base offset for this period's links (after nodes)
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
        base_link_offset = meta["results_offset"] + (period_index * period_size) + (meta["n_nodes"] * 16)
        
        # Variable Blocks for Links
        var_names = ["Flow", "Velocity", "UnitHeadloss", "Quality", "Status"]
        vars_found = {}

        nL, nT, nN = meta["n_links"], meta["n_tanks"], meta["n_nodes"]
        len_pos = 60 + 824 + (32 * nN) + (32 * nL) + (12 * nL + 8 * nT + 4 * nN) + (4 * link_index)
        f.seek(len_pos)
        length = struct.unpack('f', f.read(4))[0]

        for i, name in enumerate(var_names):
            f.seek(base_link_offset + (i * meta["n_links"] * 4) + (link_index * 4))
            val = struct.unpack('f', f.read(4))[0]
            vars_found[name] = round(float(val), ROUNDING_PRECISION)
            if (name == "UnitHeadloss"):
                vars_found["Headloss"] = round((float(val) * length) / 1000.0, ROUNDING_PRECISION)
            
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
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
        results_offset = meta["results_offset"]
        
        time_series = []
        for p in range(num_periods):
            # Posición: Inicio periodo + bloque de variable + posición del nodo
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
        meta = _get_out_file_metadata(f, include_lengths=(property_name == "Headloss"))
        
        var_names = ["Flow", "Velocity", "UnitHeadloss", "Quality", "Status"]
        calc_headloss = False
        effective_property = property_name
        
        if property_name == "Headloss":
            calc_headloss = True
            effective_property = "UnitHeadloss"
            
        if not meta or link_id not in meta["link_ids"] or effective_property not in var_names:
            return []

        link_index = meta["link_ids"].index(link_id)
        var_index = var_names.index(effective_property)
        num_periods = meta["num_periods"]
        period_size = (meta["n_nodes"] * 16) + (meta["n_links"] * 32)
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
