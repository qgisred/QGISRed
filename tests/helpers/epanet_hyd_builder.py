# -*- coding: utf-8 -*-
"""Builder for synthetic EPANET .hyd binary files used in tests."""
import struct


def build_epanet_hyd(n_nodes, n_links, records, duration=3600, n_tanks=0, n_pumps=0, n_valves=0):
    """Build a minimal .hyd file.

    records: list of dicts with keys time_s, step_s, demands, heads, flows, statuses, settings
    """
    buf = bytearray()
    buf.extend(struct.pack(
        "<8i",
        516114521,
        20,
        n_nodes,
        n_links,
        n_tanks,
        n_pumps,
        n_valves,
        duration,
    ))
    for rec in records:
        buf.extend(struct.pack("<i", rec["time_s"]))
        buf.extend(struct.pack(f"<{n_nodes}f", *rec["demands"]))
        buf.extend(struct.pack(f"<{n_nodes}f", *rec["heads"]))
        buf.extend(struct.pack(f"<{n_links}f", *rec["flows"]))
        buf.extend(struct.pack(f"<{n_links}f", *rec["statuses"]))
        buf.extend(struct.pack(f"<{n_links}f", *rec["settings"]))
        buf.extend(struct.pack("<i", rec.get("step_s", 3600)))
    buf.append(0x1A)
    return bytes(buf)
