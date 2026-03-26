# -*- coding: utf-8 -*-
"""Builder for synthetic EPANET .out binary files used in tests."""
import struct
import pytest


def _pack_id(text, width=32):
    """Encode a string into a fixed-width null-padded bytes block."""
    encoded = text.encode('ascii')[:width]
    return encoded + b'\x00' * (width - len(encoded))


def build_epanet_out(
    node_ids,           # list[str]
    link_ids,           # list[str]
    link_from,          # list[int]  (0-based node index)
    link_to,            # list[int]  (0-based node index)
    link_types,         # list[int]  (_LT_* constants)
    tank_node_indices,  # list[int]  (0-based, nodes that are tanks/reservoirs)
    tank_areas,         # list[float] (0.0 = reservoir, >0 = tank)
    node_elevations,    # list[float]
    link_lengths,       # list[float]
    link_diameters,     # list[float]
    periods_node_data,  # list of list of (demand, head, pressure, quality) per node
    periods_link_data,  # list of list of (flow, velocity, headloss, quality, status, setting, reactrate, fricfactor) per link
    report_start=0,
    report_step=3600,
    n_pumps=0,
    n_valves=0,
    wq_type=0,
    flow_units=0,
    pres_units=0,
):
    """Build a minimal EPANET .out binary file and return bytes.

    Binary layout (simplified):
      Prologue (15 ints) → 824 bytes skipped → node IDs (32 each)
      → link IDs (32 each) → link_from (int each) → link_to (int each)
      → link_types (int each) → tank_node_indices (int each) → tank_areas (float each)
      → node_elevations (float each) → link_lengths (float each) → link_diameters (float each)
      → pump energy data (28 bytes × n_pumps) → peak_demand (1 float)
      → [per-period results] → epilogue (num_periods, error_code, magic2)
    """
    n_nodes = len(node_ids)
    n_links = len(link_ids)
    n_tanks = len(tank_node_indices)
    num_periods = len(periods_node_data)
    duration = report_start + (num_periods - 1) * report_step if num_periods > 0 else 0

    buf = bytearray()

    # ── Prologue (15 ints = 60 bytes) ──
    prologue = struct.pack('15i',
        516114521,       # magic1
        20,              # version
        n_nodes,
        n_tanks,
        n_links,
        n_pumps,
        n_valves,
        wq_type,
        0,               # wq_index
        flow_units,
        pres_units,
        0,               # stats_flag
        report_start,
        report_step,
        duration,
    )
    buf.extend(prologue)

    # ── 824 bytes skipped by the reader after prologue ──
    buf.extend(b'\x00' * 824)

    # ── Node IDs (32 bytes each) ──
    for nid in node_ids:
        buf.extend(_pack_id(nid))

    # ── Link IDs (32 bytes each) ──
    for lid in link_ids:
        buf.extend(_pack_id(lid))

    # ── link_from (1-based ints) ──
    for idx in link_from:
        buf.extend(struct.pack('i', idx + 1))

    # ── link_to (1-based ints) ──
    for idx in link_to:
        buf.extend(struct.pack('i', idx + 1))

    # ── link_types (ints) ──
    for lt in link_types:
        buf.extend(struct.pack('i', lt))

    # ── tank_node_indices (1-based ints) ──
    for ti in tank_node_indices:
        buf.extend(struct.pack('i', ti + 1))

    # ── tank_areas (floats) ──
    for ta in tank_areas:
        buf.extend(struct.pack('f', ta))

    # ── node elevations (floats, skipped by reader) ──
    for elev in node_elevations:
        buf.extend(struct.pack('f', elev))

    # ── link_lengths (floats) ──
    for ll in link_lengths:
        buf.extend(struct.pack('f', ll))

    # ── link_diameters (floats, skipped together with lengths when not include_lengths) ──
    for ld in link_diameters:
        buf.extend(struct.pack('f', ld))

    # ── pump energy data (28 bytes × n_pumps) + peak_demand (1 float = 4 bytes) ──
    buf.extend(b'\x00' * (28 * n_pumps))
    buf.extend(struct.pack('f', 0.0))  # peak demand

    # ── Period results ──
    for p_idx in range(num_periods):
        node_data = periods_node_data[p_idx]   # list of n_nodes tuples
        link_data = periods_link_data[p_idx]   # list of n_links tuples

        # Node results: 4 vars × n_nodes floats
        # Order: demands, heads, pressures, qualities
        for var_idx in range(4):
            for ni in range(n_nodes):
                buf.extend(struct.pack('f', node_data[ni][var_idx]))

        # Link results: 8 vars × n_links floats
        # Order: flows, velocities, headlosses, qualities, statuses, settings, reaction_rates, friction_rates
        for var_idx in range(8):
            for li in range(n_links):
                buf.extend(struct.pack('f', link_data[li][var_idx]))

    # ── Epilogue (3 ints) ──
    buf.extend(struct.pack('3i', num_periods, 0, 516114521))

    return bytes(buf)


@pytest.fixture
def simple_network_out(tmp_path):
    """Create a small EPANET .out file with 2 junctions, 1 reservoir, 2 pipes.
    Two reporting periods (t=0, t=3600).

    Network:
        Reservoir R1  ──pipe P1──  Junction J1  ──pipe P2──  Junction J2
        (node 0)                   (node 1)                   (node 2)
    """
    node_ids = ["R1", "J1", "J2"]
    link_ids = ["P1", "P2"]
    link_from = [0, 1]    # P1: R1→J1, P2: J1→J2
    link_to = [1, 2]
    link_types = [1, 1]   # Both _LT_PIPE
    tank_node_indices = [0]
    tank_areas = [0.0]    # area=0 → reservoir
    node_elevations = [100.0, 50.0, 30.0]
    link_lengths = [1000.0, 500.0]
    link_diameters = [300.0, 200.0]

    # Period 0 (t=0): node data = (demand, head, pressure, quality)
    p0_nodes = [
        (-10.0, 100.0, 0.0,    0.0),   # R1
        (5.0,   80.0,  29.43,  0.5),   # J1
        (5.0,   60.0,  29.43,  0.3),   # J2
    ]
    # Period 0: link data = (flow, velocity, headloss, quality, status, setting, reactrate, fricfactor)
    p0_links = [
        (10.0, 1.5, 20.0, 0.4, 3.0, 0.0, 0.0, 0.02),  # P1 (status=3=Open)
        (5.0,  1.0, 40.0, 0.3, 3.0, 0.0, 0.0, 0.03),   # P2 (status=3=Open)
    ]

    # Period 1 (t=3600): slightly different values
    p1_nodes = [
        (-12.0, 100.0, 0.0,    0.0),
        (6.0,   75.0,  24.52,  0.6),
        (6.0,   55.0,  24.52,  0.4),
    ]
    p1_links = [
        (12.0, 1.8, 25.0, 0.5, 3.0, 0.0, 0.0, 0.025),
        (6.0,  1.2, 50.0, 0.4, 3.0, 0.0, 0.0, 0.035),
    ]

    data = build_epanet_out(
        node_ids=node_ids,
        link_ids=link_ids,
        link_from=link_from,
        link_to=link_to,
        link_types=link_types,
        tank_node_indices=tank_node_indices,
        tank_areas=tank_areas,
        node_elevations=node_elevations,
        link_lengths=link_lengths,
        link_diameters=link_diameters,
        periods_node_data=[p0_nodes, p1_nodes],
        periods_link_data=[p0_links, p1_links],
        report_start=0,
        report_step=3600,
    )

    out_path = tmp_path / "test_network.out"
    out_path.write_bytes(data)
    return str(out_path)


@pytest.fixture
def pump_valve_network_out(tmp_path):
    """Network with a pump and a PRV valve for testing status resolution.

    Network:
        Reservoir R1  ──pump PU1──  Junction J1  ──PRV V1──  Junction J2
        (node 0)                     (node 1)                  (node 2)
    """
    node_ids = ["R1", "J1", "J2"]
    link_ids = ["PU1", "V1"]
    link_from = [0, 1]
    link_to = [1, 2]
    link_types = [2, 3]   # _LT_PUMP=2, _LT_PRV=3
    tank_node_indices = [0]
    tank_areas = [0.0]
    node_elevations = [100.0, 50.0, 30.0]
    link_lengths = [0.0, 0.0]
    link_diameters = [0.0, 200.0]

    # Period 0: pump open, PRV active
    p0_nodes = [
        (-20.0, 100.0, 0.0,   0.0),
        (10.0,  80.0,  29.43, 0.0),
        (10.0,  60.0,  29.43, 0.0),
    ]
    p0_links = [
        # pump: flow=20, status=3(Open), setting=1.0 (speed ratio)
        (20.0, 0.0, 20.0, 0.0, 3.0, 1.0, 0.0, 0.0),
        # PRV: flow=10, status=4(Active), setting=40.0 (Pset)
        (10.0, 0.0, 0.0,  0.0, 4.0, 40.0, 0.0, 0.0),
    ]

    data = build_epanet_out(
        node_ids=node_ids,
        link_ids=link_ids,
        link_from=link_from,
        link_to=link_to,
        link_types=link_types,
        tank_node_indices=tank_node_indices,
        tank_areas=tank_areas,
        node_elevations=node_elevations,
        link_lengths=link_lengths,
        link_diameters=link_diameters,
        periods_node_data=[p0_nodes],
        periods_link_data=[p0_links],
        report_start=0,
        report_step=3600,
        n_pumps=1,
        n_valves=1,
    )

    out_path = tmp_path / "pump_valve_network.out"
    out_path.write_bytes(data)
    return str(out_path)
