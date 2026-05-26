# -*- coding: utf-8 -*-
"""Builder for synthetic EPANET .hyd binary files used in tests."""
import struct

_HYD_MAGIC = 516114521


def build_epanet_hyd(periods_data, n_nodes, n_links, n_tanks=0, n_pumps=0, n_valves=0, duration=0, include_node_pressures=False):
    """Build a simplified EPANET-compatible .hyd stream.

    periods_data: list of dict with keys:
      - time: int seconds
      - step: int seconds (hydraulic step at this record)
      - demands: list[float] size n_nodes
      - heads: list[float] size n_nodes
      - flows: list[float] size n_links
      - statuses: list[float] size n_links
      - settings: list[float] size n_links
    """
    buf = bytearray()
    header = struct.pack(
        "<8i",
        _HYD_MAGIC,
        22,  # version
        n_nodes,
        n_links,
        n_tanks,
        n_pumps,
        n_valves,
        int(duration),
    )
    buf.extend(header)

    for period in periods_data:
        buf.extend(struct.pack("<i", int(period["time"])))
        node_keys = ("demands", "heads", "pressures") if include_node_pressures else ("demands", "heads")
        for key in node_keys:
            for val in period[key]:
                buf.extend(struct.pack("<f", float(val)))
        for key in ("flows", "statuses", "settings"):
            for val in period[key]:
                buf.extend(struct.pack("<f", float(val)))
        buf.extend(struct.pack("<i", int(period.get("step", 0))))
    return bytes(buf)
