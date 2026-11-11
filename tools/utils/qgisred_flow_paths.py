# -*- coding: utf-8 -*-
"""Upstream / downstream sub-networks of a node at a given instant.

Pure graph logic, free of QGIS, so it can be unit tested on its own.

The network is oriented by the sign of the link flows: a link with a positive
flow carries water from its start node to its end node, a negative flow the
other way round, and a link with (practically) no flow carries nothing and is
never crossed.

Upstream routes start at the selected node and walk *against* the flow, through
the links that feed it, until nothing more feeds the route. Downstream routes
walk *with* the flow until the terminal nodes where water only comes in.

A source — a tank, a reservoir or a junction with negative demand — met along
the way does not stop the walk: the routes keep going through the links that
feed it (upstream) or that leave it (downstream). Every link gets a *level*:
the smallest number of sources standing between the link and the selected
node. Level 0 links reach the selected node directly; level 1 links only reach
it through one source, and so on. When a link reaches the node both directly
and through a source, the direct route wins (level 0), which is what the
minimum gives.
"""
from collections import deque

UPSTREAM = "up"
DOWNSTREAM = "down"

# Flows at or below this magnitude are treated as "no flow": a closed link in
# EPANET reports a tiny residual flow, not an exact zero.
DEFAULT_FLOW_TOLERANCE = 1e-4


def oriented_links(link_endpoints, flows, tolerance=DEFAULT_FLOW_TOLERANCE, closed_links=None):
    """Return {link_id: (upstream_node, downstream_node)} for links carrying water."""
    closed = closed_links or set()
    oriented = {}
    for link_id, ends in link_endpoints.items():
        if link_id in closed:
            continue
        flow = flows.get(link_id)
        if flow is None:
            continue
        try:
            flow = float(flow)
        except (TypeError, ValueError):
            continue
        if abs(flow) <= tolerance:
            continue
        start, end = ends
        oriented[link_id] = (start, end) if flow > 0 else (end, start)
    return oriented


def trace_flow_paths(start_node, oriented, source_nodes, direction):
    """Walk the oriented network from `start_node` and level every link reached.

    Returns {"links": {link_id: level}, "nodes": {node_id: level}}. The start
    node is not in "nodes" and never counts as a source, so clicking on a tank
    still shows its own routes at level 0.
    """
    adjacency = {}
    for link_id, (up_node, down_node) in oriented.items():
        if direction == UPSTREAM:
            adjacency.setdefault(down_node, []).append((link_id, up_node))
        else:
            adjacency.setdefault(up_node, []).append((link_id, down_node))

    node_level = {start_node: 0}
    link_level = {}
    # 0-1 BFS: crossing a source costs one level, everything else is free.
    queue = deque([(start_node, 0)])
    while queue:
        node, level = queue.popleft()
        if level > node_level.get(node, level):
            continue
        for link_id, neighbor in adjacency.get(node, ()):
            if level < link_level.get(link_id, level + 1):
                link_level[link_id] = level
            cost = 1 if neighbor != start_node and neighbor in source_nodes else 0
            neighbor_level = level + cost
            if neighbor_level < node_level.get(neighbor, neighbor_level + 1):
                node_level[neighbor] = neighbor_level
                if cost:
                    queue.append((neighbor, neighbor_level))
                else:
                    queue.appendleft((neighbor, neighbor_level))

    node_level.pop(start_node, None)
    return {"links": link_level, "nodes": node_level}


def source_nodes_from(node_types, node_demands, tolerance=DEFAULT_FLOW_TOLERANCE):
    """Nodes that bring water from outside: tanks, reservoirs and negative demands.

    node_types uses the EPANET codes of the .out metadata: 0 junction,
    1 reservoir, 2 tank.
    """
    sources = {nid for nid, kind in node_types.items() if kind in (1, 2)}
    for nid, demand in (node_demands or {}).items():
        try:
            if demand is not None and float(demand) < -tolerance:
                sources.add(nid)
        except (TypeError, ValueError):
            continue
    return sources


def flow_path_widths(link_flows, link_ids, min_width, max_width):
    """Line width for each link, proportional to the magnitude of its flow."""
    magnitudes = {}
    for lid in link_ids:
        try:
            magnitudes[lid] = abs(float(link_flows.get(lid) or 0.0))
        except (TypeError, ValueError):
            magnitudes[lid] = 0.0
    top = max(magnitudes.values()) if magnitudes else 0.0
    if top <= 0:
        return {lid: min_width for lid in magnitudes}
    return {
        lid: min_width + (max_width - min_width) * value / top
        for lid, value in magnitudes.items()
    }


def upstream_link_sources(start_node, up_links, oriented, flows, source_nodes):
    """Tell, for each upstream link, which source most of its water comes from.

    The upstream sub-network starts at a handful of nodes nothing feeds within
    it (reservoirs, tanks, negative demands). Walking it downstream from them,
    every node mixes the water of its inflows in proportion to their flows, and
    each link leaving the node takes the source that brings most of it. A source
    met along the way (a tank, say) starts afresh as a new intermediate source.

    Returns ({link_id: source_node}, [source_node, ...]); the list is ordered
    by the flow leaving each source, largest first.
    """
    incoming, outgoing = {}, {}
    for lid in up_links:
        ends = oriented.get(lid)
        if ends is None:
            continue
        up_node, down_node = ends
        incoming.setdefault(down_node, []).append((lid, up_node))
        outgoing.setdefault(up_node, []).append((lid, down_node))
        incoming.setdefault(up_node, [])
        outgoing.setdefault(down_node, [])

    def magnitude(lid):
        try:
            return abs(float(flows.get(lid) or 0.0))
        except (TypeError, ValueError):
            return 0.0

    pending = {node: len(links) for node, links in incoming.items()}
    ready = deque(sorted((n for n, count in pending.items() if count == 0), key=str))
    mixes, link_source = {}, {}
    while pending:
        if not ready:
            # A loop of flows (numerical noise): break it at the node whose
            # inflows are best known.
            node = max(pending, key=lambda n: (
                sum(1 for _l, up in incoming[n] if up in mixes), str(n)))
        else:
            node = ready.popleft()
            if node not in pending:
                continue
        del pending[node]
        known = [(lid, up) for lid, up in incoming[node] if up in mixes]
        if not known or (node != start_node and node in source_nodes):
            mix = {node: 1.0}
        else:
            mix = {}
            total = sum(magnitude(lid) for lid, _up in known) or float(len(known))
            for lid, up in known:
                weight = (magnitude(lid) or (0.0 if total else 1.0)) / total
                for source, share in mixes[up].items():
                    mix[source] = mix.get(source, 0.0) + share * weight
        mixes[node] = mix
        main = max(mix.items(), key=lambda item: (item[1], str(item[0])))[0]
        for lid, down in outgoing.get(node, ()):
            link_source[lid] = main
            if down in pending:
                pending[down] -= 1
                if pending[down] == 0:
                    ready.append(down)

    out_flow = {}
    for lid, source in link_source.items():
        if oriented[lid][0] == source:
            out_flow[source] = out_flow.get(source, 0.0) + magnitude(lid)
    order = sorted(set(link_source.values()), key=lambda s: (-out_flow.get(s, 0.0), str(s)))
    return link_source, order
