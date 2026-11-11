# -*- coding: utf-8 -*-
from QGISRed.tools.utils.qgisred_flow_paths import (
    DOWNSTREAM,
    UPSTREAM,
    oriented_links,
    source_nodes_from,
    trace_flow_paths,
    upstream_link_sources,
)

# R1 --P1--> J1 --P2--> N <--P3-- T1 <--P4-- J2 <--P5-- R1
#                       N --P6--> J3 --P7--> T2 --P8--> J4
#                       J1 --P9--> T1
# P10 is closed (negative flow but closed) and P11 has no flow.
ENDPOINTS = {
    "P1": ("R1", "J1"), "P2": ("J1", "N"), "P3": ("N", "T1"),  # P3 flows T1 -> N
    "P4": ("J2", "T1"), "P5": ("J2", "R1"),                    # P5 flows R1 -> J2
    "P6": ("N", "J3"), "P7": ("J3", "T2"), "P8": ("T2", "J4"),
    "P9": ("J1", "T1"), "P10": ("N", "J5"), "P11": ("J6", "N"),
}
FLOWS = {
    "P1": 10.0, "P2": 6.0, "P3": -4.0, "P4": 3.0, "P5": -3.0,
    "P6": 5.0, "P7": 5.0, "P8": 2.0, "P9": 1.0, "P10": -2.0, "P11": 0.0,
}
NODE_TYPES = {"R1": 1, "T1": 2, "T2": 2, "J1": 0, "J2": 0, "J3": 0, "J4": 0, "N": 0}


def _trace(direction):
    oriented = oriented_links(ENDPOINTS, FLOWS, closed_links={"P10"})
    sources = source_nodes_from(NODE_TYPES, {"J4": 1.0})
    return trace_flow_paths("N", oriented, sources, direction)


def test_upstream_levels_prefer_the_direct_route():
    links = _trace(UPSTREAM)["links"]
    # P2 and P3 feed N directly and P1 feeds J1, which feeds N directly. P9 and
    # P4 only reach N through tank T1, and P5 through J2 into T1: level 1.
    assert links == {"P2": 0, "P3": 0, "P1": 0, "P9": 1, "P4": 1, "P5": 1}


def test_downstream_continues_past_a_tank_with_a_lighter_level():
    links = _trace(DOWNSTREAM)["links"]
    assert links == {"P6": 0, "P7": 0, "P8": 1}


def test_upstream_links_take_the_source_bringing_most_of_their_water():
    # A tank on the way is a new source: P3 leaves T1, the rest comes from R1.
    oriented = oriented_links(ENDPOINTS, FLOWS, closed_links={"P10"})
    sources = source_nodes_from(NODE_TYPES, {})
    up = _trace(UPSTREAM)["links"]
    link_source, order = upstream_link_sources("N", up, oriented, FLOWS, sources)
    assert link_source == {"P1": "R1", "P2": "R1", "P9": "R1", "P5": "R1", "P4": "R1", "P3": "T1"}
    assert order == ["R1", "T1"]

    # X mixes 2 from A with 5 from B, so what leaves X towards N is B's.
    mixed = {"L1": ("A", "X"), "L2": ("B", "X"), "L3": ("X", "N")}
    flows = {"L1": 2.0, "L2": 5.0, "L3": 7.0}
    link_source, order = upstream_link_sources("N", mixed, mixed, flows, {"A", "B"})
    assert link_source["L3"] == "B" and order == ["B", "A"]
