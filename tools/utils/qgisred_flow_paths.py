# -*- coding: utf-8 -*-
from collections import deque

UPSTREAM = "up"
DOWNSTREAM = "down"

DEFAULT_FLOW_TOLERANCE = 1e-4


def oriented_links(link_endpoints, flows, tolerance=DEFAULT_FLOW_TOLERANCE, closed_links=None):
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
    adjacency = {}
    for link_id, (up_node, down_node) in oriented.items():
        if direction == UPSTREAM:
            adjacency.setdefault(down_node, []).append((link_id, up_node))
        else:
            adjacency.setdefault(up_node, []).append((link_id, down_node))

    node_level = {start_node: 0}
    link_level = {}
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
    sources = {nid for nid, kind in node_types.items() if kind in (1, 2)}
    for nid, demand in (node_demands or {}).items():
        try:
            if demand is not None and float(demand) < -tolerance:
                sources.add(nid)
        except (TypeError, ValueError):
            continue
    return sources


def flow_path_widths(link_flows, link_ids, min_width, max_width):
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


ROUTE_MAX_FLOW = "flow"
ROUTE_MIN_TIME = "time"
ROUTE_MIN_ENERGY = "energy"
ROUTE_MIN_LENGTH = "length"
ROUTE_CRITERIA = (ROUTE_MAX_FLOW, ROUTE_MIN_TIME, ROUTE_MIN_ENERGY, ROUTE_MIN_LENGTH)


def trace_routes(start_node, end_node, oriented, subnetwork_links, direction):
    adjacency = {}
    for link_id in subnetwork_links:
        ends = oriented.get(link_id)
        if ends is None:
            continue
        up_node, down_node = ends
        if direction == DOWNSTREAM:
            adjacency.setdefault(down_node, []).append((link_id, up_node))
        else:
            adjacency.setdefault(up_node, []).append((link_id, down_node))

    links = set()
    seen = {end_node}
    stack = [end_node]
    while stack:
        node = stack.pop()
        if node == start_node:
            continue
        for link_id, neighbor in adjacency.get(node, ()):
            links.add(link_id)
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return links if start_node in seen else set()


def _as_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def route_link_costs(criterion, link_ids, flows, velocities=None, headlosses=None, lengths=None):
    velocities = velocities or {}
    headlosses = headlosses or {}
    lengths = lengths or {}
    costs = {}
    for lid in link_ids:
        flow = abs(_as_float(flows.get(lid)) or 0.0)
        if criterion == ROUTE_MAX_FLOW:
            costs[lid] = flow
        elif criterion == ROUTE_MIN_LENGTH:
            costs[lid] = abs(_as_float(lengths.get(lid)) or 0.0)
        elif criterion == ROUTE_MIN_TIME:
            length = abs(_as_float(lengths.get(lid)) or 0.0)
            velocity = abs(_as_float(velocities.get(lid)) or 0.0)
            if length <= 0:
                costs[lid] = 0.0
            else:
                costs[lid] = length / velocity if velocity > 0 else float("inf")
        elif criterion == ROUTE_MIN_ENERGY:
            costs[lid] = flow * max(_as_float(headlosses.get(lid)) or 0.0, 0.0)
        else:
            costs[lid] = 0.0
    return costs


def optimal_route(origin, destination, oriented, route_links, link_costs, bottleneck=False):
    import heapq

    adjacency = {}
    for link_id in route_links:
        ends = oriented.get(link_id)
        if ends is not None:
            adjacency.setdefault(ends[0], []).append((link_id, ends[1]))

    best = {origin: float("inf") if bottleneck else 0.0}
    previous = {}
    done = set()
    counter = 0
    heap = [(-best[origin] if bottleneck else best[origin], counter, origin)]
    while heap:
        _key, _order, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        if node == destination:
            break
        for link_id, neighbor in adjacency.get(node, ()):
            if neighbor in done:
                continue
            cost = link_costs.get(link_id, 0.0)
            if bottleneck:
                value = min(best[node], cost)
                better = value > best.get(neighbor, float("-inf"))
                key = -value
            else:
                value = best[node] + max(cost, 0.0)
                better = value < best.get(neighbor, float("inf"))
                key = value
            if better:
                best[neighbor] = value
                previous[neighbor] = (link_id, node)
                counter += 1
                heapq.heappush(heap, (key, counter, neighbor))

    if destination == origin or destination not in previous:
        return []
    path = []
    node = destination
    while node != origin:
        link_id, node = previous[node]
        path.append(link_id)
    path.reverse()
    return path


def _route_nodes(origin, route, oriented):
    nodes = [origin]
    for lid in route:
        nodes.append(oriented[lid][1])
    return nodes


def _magnitude(flows, lid):
    return abs(_as_float(flows.get(lid)) or 0.0)


def _busiest_way(start, targets, outgoing, oriented, flows):
    route, node, seen = [], start, {start}
    while not route or node not in targets:
        options = outgoing.get(node)
        if not options:
            return []
        lid = max(options, key=lambda link: (_magnitude(flows, link), str(link)))
        node = oriented[lid][1]
        if node in seen:
            return []
        seen.add(node)
        route.append(lid)
    return route


def _cheapest_way(start, targets, outgoing, oriented, costs):
    import heapq

    best, previous, done = {start: 0.0}, {}, set()
    heap, counter = [(0.0, 0, start)], 0
    while heap:
        cost, _order, node = heapq.heappop(heap)
        if node in done:
            continue
        done.add(node)
        if node != start and node in targets:
            route = []
            while node != start:
                lid, node = previous[node]
                route.append(lid)
            return route[::-1]
        for lid in outgoing.get(node, ()):
            neighbor = oriented[lid][1]
            value = cost + max(costs.get(lid, 0.0), 0.0)
            if neighbor not in done and value < best.get(neighbor, float("inf")):
                best[neighbor] = value
                previous[neighbor] = (lid, node)
                counter += 1
                heapq.heappush(heap, (value, counter, neighbor))
    return []


def _best_way(start, targets, oriented, allowed, costs, flows, by_flow):
    outgoing = {}
    for lid in allowed:
        ends = oriented.get(lid)
        if ends is not None:
            outgoing.setdefault(ends[0], []).append(lid)
    if by_flow:
        return _busiest_way(start, targets, outgoing, oriented, flows)
    return _cheapest_way(start, targets, outgoing, oriented, costs)


def largest_flow_route(origin, destination, oriented, route_links, flows):
    return _best_way(origin, {destination}, oriented, route_links, {}, flows, True)


def route_decomposition(origin, destination, oriented, route_links, link_costs, flows, by_flow=False):
    best = []
    if by_flow:
        best = largest_flow_route(origin, destination, oriented, route_links, flows)
    if not best:
        costs = {lid: _magnitude(flows, lid) for lid in route_links} if by_flow else link_costs
        best = optimal_route(origin, destination, oriented, route_links, costs, bottleneck=by_flow)
    if not best:
        return []
    routes = [{"links": best, "own": list(best)}]
    covered = set(best)
    visited = set(_route_nodes(origin, best, oriented))
    skipped = set()
    while True:
        leaving = [lid for lid in route_links
                   if lid not in covered and lid not in skipped and lid in oriented and oriented[lid][0] in visited]
        if not leaving:
            break
        first = max(leaving, key=lambda lid: (_magnitude(flows, lid), str(lid)))
        head = oriented[first][1]
        own = [first]
        if head not in visited:
            free = {lid for lid in route_links if lid not in covered and lid != first}
            rest = _best_way(head, visited, oriented, free, link_costs, flows, by_flow)
            if not rest:
                skipped.add(first)
                continue
            own += rest
        start, end = oriented[own[0]][0], oriented[own[-1]][1]
        to_start = {lid: 1.0 / max(_magnitude(flows, lid), 1e-9) for lid in covered} if by_flow else link_costs
        before = _best_way(origin, {start}, oriented, covered, to_start, flows, False) if start != origin else []
        after = _best_way(end, {destination}, oriented, covered, link_costs, flows, by_flow) \
            if end != destination else []
        routes.append({"links": before + own + after, "own": own})
        covered.update(own)
        visited.update(_route_nodes(start, own, oriented))
    return routes


def route_flow_balance(route, oriented, flows, demands=None):
    if not route:
        return {"links": 0, "first": 0.0, "gained": 0.0, "lost": 0.0, "last": 0.0}
    inner = {oriented[lid][1] for lid in route[:-1]}
    on_route = set(route)
    gained = lost = 0.0
    for lid, (up_node, down_node) in oriented.items():
        if lid in on_route:
            continue
        if down_node in inner:
            gained += _magnitude(flows, lid)
        if up_node in inner:
            lost += _magnitude(flows, lid)
    for node in inner:
        demand = _as_float((demands or {}).get(node)) or 0.0
        if demand > 0:
            lost += demand
        else:
            gained -= demand
    return {"links": len(route), "first": _magnitude(flows, route[0]), "gained": gained, "lost": lost,
            "last": _magnitude(flows, route[-1])}


def route_shades(count, step=0.25, reach=0.8):
    if count > 1:
        step = min(step, reach / (count - 1))
    return [step * position for position in range(count)]


def faded(rgb, fraction):
    return tuple(int(round(channel + (255 - channel) * fraction)) for channel in rgb)


def route_summary(route, flows, velocities=None, headlosses=None, lengths=None):
    length = sum(route_link_costs(ROUTE_MIN_LENGTH, route, flows, lengths=lengths).values())
    time = sum(route_link_costs(ROUTE_MIN_TIME, route, flows, velocities=velocities, lengths=lengths).values())
    energy = sum(route_link_costs(ROUTE_MIN_ENERGY, route, flows, headlosses=headlosses).values())
    carried = route_link_costs(ROUTE_MAX_FLOW, route, flows).values()
    return {"length": length, "time": time, "energy": energy,
            "flow": sum(carried) / len(carried) if carried else 0.0}


def place_callouts(callouts, bounds, overlap=None, gap=7.0, margin=3.0):
    left, top, right, bottom = bounds
    placed, result = [], []
    for x, y, width, height, required in callouts:
        candidates = [spot for reach in (gap, gap * 3.5, gap * 7.0) for spot in (
            (x - width / 2.0, y - reach - height), (x - width / 2.0, y + reach),
            (x + reach, y - height / 2.0), (x - reach - width, y - height / 2.0),
            (x + reach, y - reach - height), (x - reach - width, y - reach - height),
            (x + reach, y + reach), (x - reach - width, y + reach),
        )]
        best = None
        for cx, cy in candidates:
            rect = (cx, cy, cx + width, cy + height)
            if rect[0] < left or rect[1] < top or rect[2] > right or rect[3] > bottom:
                continue
            if any(rect[0] < other[2] + margin and other[0] < rect[2] + margin
                   and rect[1] < other[3] + margin and other[1] < rect[3] + margin for other in placed):
                continue
            hidden = overlap(rect) if overlap is not None else 0.0
            if best is None or hidden < best[0]:
                best = (hidden, rect)
            if hidden <= 0:
                break
        if best is None and required:
            cx = min(max(candidates[0][0], left), max(right - width, left))
            cy = min(max(candidates[0][1], top), max(bottom - height, top))
            best = (0.0, (cx, cy, cx + width, cy + height))
        if best is None:
            result.append(None)
            continue
        placed.append(best[1])
        result.append(best[1][:2])
    return result
