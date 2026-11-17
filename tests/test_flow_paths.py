# -*- coding: utf-8 -*-
from QGISRed.tools.utils.qgisred_flow_paths import (
    DOWNSTREAM,
    ROUTE_MAX_FLOW,
    ROUTE_MIN_LENGTH,
    UPSTREAM,
    optimal_route,
    place_callouts,
    oriented_links,
    route_decomposition,
    route_link_costs,
    route_tones,
    source_nodes_from,
    trace_flow_paths,
    upstream_link_sources,
    trace_routes,
)

ENDPOINTS = {
    "P1": ("R1", "J1"), "P2": ("J1", "N"), "P3": ("N", "T1"),
    "P4": ("J2", "T1"), "P5": ("J2", "R1"),
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
    assert links == {"P2": 0, "P3": 0, "P1": 0, "P9": 1, "P4": 1, "P5": 1}


def test_downstream_continues_past_a_tank_with_a_lighter_level():
    links = _trace(DOWNSTREAM)["links"]
    assert links == {"P6": 0, "P7": 0, "P8": 1}


def test_upstream_links_take_the_source_bringing_most_of_their_water():
    oriented = oriented_links(ENDPOINTS, FLOWS, closed_links={"P10"})
    sources = source_nodes_from(NODE_TYPES, {})
    up = _trace(UPSTREAM)["links"]
    link_source, order = upstream_link_sources("N", up, oriented, FLOWS, sources)
    assert link_source == {"P1": "R1", "P2": "R1", "P9": "R1", "P5": "R1", "P4": "R1", "P3": "T1"}
    assert order == ["R1", "T1"]

    mixed = {"L1": ("A", "X"), "L2": ("B", "X"), "L3": ("X", "N")}
    flows = {"L1": 2.0, "L2": 5.0, "L3": 7.0}
    link_source, order = upstream_link_sources("N", mixed, mixed, flows, {"A", "B"})
    assert link_source["L3"] == "B" and order == ["B", "A"]


ROUTE_ENDPOINTS = {"AB": ("A", "B"), "BD": ("B", "D"), "AC": ("A", "C"), "CD": ("C", "D"), "DE": ("D", "E")}
ROUTE_FLOWS = {"AB": 10.0, "BD": 10.0, "AC": 2.0, "CD": 2.0, "DE": 12.0}
ROUTE_LENGTHS = {"AB": 500.0, "BD": 500.0, "AC": 100.0, "CD": 100.0, "DE": 50.0}


def _routes(start, end, direction):
    oriented = oriented_links(ROUTE_ENDPOINTS, ROUTE_FLOWS)
    subnetwork = trace_flow_paths(start, oriented, set(), direction)["links"]
    return oriented, trace_routes(start, end, oriented, subnetwork, direction)


def test_routes_between_two_nodes_follow_the_flow_only():
    _oriented, links = _routes("A", "D", DOWNSTREAM)
    assert links == {"AB", "BD", "AC", "CD"}
    assert _routes("D", "A", UPSTREAM)[1] == links
    assert _routes("E", "A", DOWNSTREAM)[1] == set()


def test_optimal_route_depends_on_the_criterion():
    oriented, links = _routes("A", "D", DOWNSTREAM)

    def best(criterion):
        costs = route_link_costs(criterion, links, ROUTE_FLOWS, lengths=ROUTE_LENGTHS)
        return optimal_route("A", "D", oriented, links, costs, bottleneck=criterion == ROUTE_MAX_FLOW)

    assert best(ROUTE_MAX_FLOW) == ["AB", "BD"]
    assert best(ROUTE_MIN_LENGTH) == ["AC", "CD"]


def test_routes_are_the_busiest_way_plus_the_stretches_only_the_others_use():
    endpoints = {"AB": ("A", "B"), "BD": ("B", "D"), "AC": ("A", "C"), "CD": ("C", "D"), "BC": ("B", "C")}
    flows = {"AB": 9.0, "BD": 6.0, "AC": 2.0, "CD": 5.0, "BC": 3.0}
    oriented = oriented_links(endpoints, flows)
    links = set(endpoints)
    costs = route_link_costs(ROUTE_MAX_FLOW, links, flows)
    routes = route_decomposition("A", "D", oriented, links, costs, flows, by_flow=True)
    assert routes == [
        {"links": ["AB", "BD"], "own": ["AB", "BD"]},
        {"links": ["AB", "BC", "CD"], "own": ["BC", "CD"]},
        {"links": ["AC", "CD"], "own": ["AC"]},
    ]


def test_alternative_stretches_that_touch_get_different_tones():
    oriented = {"M1": ("A", "B"), "M2": ("B", "C"), "X": ("A", "B"), "Y": ("A", "C"), "Z": ("B", "C")}
    routes = [{"own": ["M1", "M2"]}, {"own": ["X"]}, {"own": ["Y"]}, {"own": ["Z"]}]
    tones = route_tones(routes, oriented, 4)
    assert tones[0] is None
    assert len({tones[1], tones[2], tones[3]}) == 3
    far = {"M": ("A", "B"), "N": ("B", "C"), "O": ("C", "D"), "P": ("A", "B"), "Q": ("C", "D")}
    assert route_tones([{"own": ["M", "N", "O"]}, {"own": ["P"]}, {"own": ["Q"]}], far, 1) == [None, 0, 0]


def test_callouts_avoid_the_routes_and_each_other_or_are_left_out():
    def overlap(rect):
        return 1.0 if rect[1] < 90 else 0.0

    spots = place_callouts(
        [(200, 100, 60, 20, True), (200, 100, 60, 20, False), (5, 5, 400, 400, False)],
        (0, 0, 400, 300), overlap=overlap)
    assert spots[0] == (170, 107)
    assert spots[1] == (170, 149)
    assert spots[2] is None
