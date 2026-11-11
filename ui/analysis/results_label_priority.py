# -*- coding: utf-8 -*-
"""Label priority levels for the Results map ("Show only the most relevant values").

Each element gets a level from 1 (most relevant, shown even at the farthest zoom) to
LEVEL_COUNT (only shown when zoomed in close). The relevance comes from a tree that
follows the main flows of the network:

* The minimum resistance tree is the maximum spanning tree on |flow|, grown from the
  sources (reservoirs and tanks). Components without a source start at the node that
  carries the largest flow.
* Node pressure, head and quality: the change in value from the parent node along the
  tree. Sources come first. Dead ends score the change accumulated since the last
  bifurcation; tree leaves closed by chords (loop links) also score the jump across them.
* Node demand-like magnitudes and link relative magnitudes (velocity, unit headloss,
  friction factor, reaction rate...): the value itself.
* Link flow and headloss: the flow, discounted when it just carries on the incoming
  flow of its upstream node (main continuation with little change). Links entering or
  leaving a reservoir or tank get level 0: always shown, even over other labels.
* Link quality: the change from the upstream link.
* Link status: closed elements, active valves and pumps/valves first; open pipes last.

Levels are handed out by area so labels spread over the whole map: at each level the
network is split into cells (CELLS_PER_SCREEN per screen side at the zoom where that
level appears) and the most relevant element of every cell not yet labelled takes it.

Pure Python (no QGIS imports) so it can be unit tested on its own.
"""
import heapq
import math

LEVEL_COUNT = 8
# Level 0: always shown and allowed to overlap other labels (flows at sources).
ALWAYS_LEVEL = 0
# Cells per screen side for the spatial spread: each level adds at most one label per
# cell, so a screen holds about CELLS_PER_SCREEN² new labels at every zoom step.
CELLS_PER_SCREEN = 6
# Without positions, labels allowed at the full network extent. Each level up
# quadruples the count, which keeps the density on screen roughly constant.
BASE_COUNT = 20

_INF = float("inf")

NODE_CHANGE_FIELDS = {"Pressure", "Head", "Quality"}
LINK_FLOW_FIELDS = {"Flow", "Flow_Sig", "Flow_Unsig", "HeadLoss"}
LINK_CHANGE_FIELDS = {"Quality"}


class FlowTree:
    """Topology plus the max-flow spanning tree. Node and link references are indices."""

    def __init__(self, n_nodes, link_ends, flows_abs, roots):
        self.n_nodes = n_nodes
        self.link_ends = link_ends
        self.node_links = [[] for _ in range(n_nodes)]
        for li, (a, b) in enumerate(link_ends):
            if 0 <= a < n_nodes and 0 <= b < n_nodes and a != b:
                self.node_links[a].append((li, b))
                self.node_links[b].append((li, a))
        self.sources = {r for r in roots if 0 <= r < n_nodes}
        self.parent_link = [-1] * n_nodes
        self.parent_node = [-1] * n_nodes
        self.is_root = [False] * n_nodes
        self.order = []  # visit order: every parent precedes its children
        self.children = [[] for _ in range(n_nodes)]  # (link, child)
        self.tree_link = [False] * len(link_ends)
        self._grow(flows_abs, roots)

    def _flow(self, flows_abs, li):
        q = flows_abs[li] if li < len(flows_abs) else None
        return abs(q) if q is not None else 0.0

    def _grow(self, flows_abs, roots):
        visited = [False] * self.n_nodes
        heap = []

        def visit(node, link, parent):
            visited[node] = True
            self.order.append(node)
            if link < 0:
                self.is_root[node] = True
            else:
                self.parent_link[node] = link
                self.parent_node[node] = parent
                self.tree_link[link] = True
                self.children[parent].append((link, node))
            for li, other in self.node_links[node]:
                if not visited[other]:
                    heapq.heappush(heap, (-self._flow(flows_abs, li), li, other, node))

        def drain():
            while heap:
                _, li, node, parent = heapq.heappop(heap)
                if not visited[node]:
                    visit(node, li, parent)

        for r in roots:
            if 0 <= r < self.n_nodes and not visited[r]:
                visit(r, -1, -1)
        drain()
        # Components with no source: start from the node carrying the most flow.
        fallback = sorted(
            range(self.n_nodes),
            key=lambda n: -sum(self._flow(flows_abs, li) for li, _ in self.node_links[n]),
        )
        for n in fallback:
            if not visited[n]:
                visit(n, -1, -1)
                drain()

    def degree(self, node):
        return len(self.node_links[node])


# ----------------------------------------------------------------------
# Scores (higher = more relevant; None or <= 0 = least relevant)
# ----------------------------------------------------------------------

def _diff(a, b):
    if a is None or b is None:
        return 0.0
    return abs(a - b)


def node_change_scores(tree, values):
    scores = [0.0] * tree.n_nodes
    anchor = [-1] * tree.n_nodes  # nearest ancestor that is a root or a bifurcation
    for n in tree.order:
        if tree.is_root[n]:
            scores[n] = _INF
            continue
        p = tree.parent_node[n]
        anchor[n] = p if (tree.is_root[p] or len(tree.children[p]) >= 2) else anchor[p]
        score = _diff(values[n], values[p])
        if not tree.children[n]:
            if tree.degree(n) == 1:
                # True end of the network: the whole change along its branch.
                score = max(score, _diff(values[n], values[anchor[n]]))
            else:
                for li, other in tree.node_links[n]:
                    if not tree.tree_link[li]:
                        score = max(score, _diff(values[n], values[other]))
        scores[n] = score
    return scores


def link_flow_scores(tree, flows_abs):
    def q(li):
        v = flows_abs[li] if li < len(flows_abs) else None
        return abs(v) if v is not None else 0.0

    def inflow(node):
        li = tree.parent_link[node]
        return q(li) if li >= 0 else None

    scores = [0.0] * len(tree.link_ends)
    for u in tree.order:
        kids = tree.children[u]
        if not kids:
            continue
        q_in = inflow(u)
        dominant = max(kids, key=lambda k: q(k[0]))[0]
        for li, _ in kids:
            q_l = q(li)
            if li == dominant and q_in:
                # Main continuation: only as relevant as the flow it loses or gains.
                scores[li] = q_l * min(1.0, abs(q_l - q_in) / q_in)
            else:
                scores[li] = q_l
    for li, (a, b) in enumerate(tree.link_ends):
        if tree.tree_link[li] or not (0 <= a < tree.n_nodes and 0 <= b < tree.n_nodes):
            continue
        q_l = q(li)
        q_ref = max(inflow(a) or 0.0, inflow(b) or 0.0)
        scores[li] = q_l * min(1.0, q_l / q_ref) if q_ref > 0 else q_l
    return scores


def link_change_scores(tree, values):
    def upstream_value(node):
        li = tree.parent_link[node]
        return values[li] if li >= 0 else None

    scores = [0.0] * len(tree.link_ends)
    for u in tree.order:
        for li, _ in tree.children[u]:
            scores[li] = _INF if tree.is_root[u] else _diff(values[li], upstream_value(u))
    for li, (a, b) in enumerate(tree.link_ends):
        if tree.tree_link[li] or not (0 <= a < tree.n_nodes and 0 <= b < tree.n_nodes):
            continue
        scores[li] = max(_diff(values[li], upstream_value(a)), _diff(values[li], upstream_value(b)))
    return scores


def value_scores(values):
    return [abs(v) if v is not None else 0.0 for v in values]


def status_levels(statuses, link_types):
    levels = []
    for status, ltype in zip(statuses, link_types):
        status = str(status or "")
        relevant = ("Closed" in status or status.startswith("Active")
                    or str(ltype or "").upper() in ("PUMP", "VALVE"))
        levels.append(1 if relevant else LEVEL_COUNT)
    return levels


def _valid(score):
    return score is not None and score > 0 and not math.isnan(score)


def _global_levels(ranked, levels):
    limit, level = BASE_COUNT, 1
    for rank, i in enumerate(ranked):
        while rank >= limit and level < LEVEL_COUNT:
            limit *= 4
            level += 1
        levels[i] = level


def _spatial_levels(ranked, positions, levels):
    """Best element per cell at each level; cells halve in size with every level."""
    placed = [i for i in ranked if positions[i] is not None]
    for i in ranked:
        if positions[i] is None:
            levels[i] = LEVEL_COUNT
    if not placed:
        return
    min_x = min(positions[i][0] for i in placed)
    min_y = min(positions[i][1] for i in placed)
    size = max(max(positions[i][0] for i in placed) - min_x,
               max(positions[i][1] for i in placed) - min_y) or 1.0
    remaining = placed
    for level in range(1, LEVEL_COUNT):
        if not remaining:
            return
        cells = CELLS_PER_SCREEN * 2 ** (level - 1)
        cell = size / cells
        taken, rest = set(), []
        for i in remaining:  # most relevant first
            x, y = positions[i]
            # min() keeps the far edge of the network inside the last cell.
            key = (min(int((x - min_x) // cell), cells - 1), min(int((y - min_y) // cell), cells - 1))
            if key in taken:
                rest.append(i)
            else:
                taken.add(key)
                levels[i] = level
        remaining = rest
    for i in remaining:
        levels[i] = LEVEL_COUNT


def scores_to_levels(scores, positions=None):
    """Turn scores into levels: spread by area when positions (x, y) are given, by rank
    otherwise (top BASE_COUNT level 1, top BASE_COUNT*4 level 2...).

    Elements with no score (no change, zero, missing) go right after the last level in
    use, so they appear as soon as every scored label is on screen instead of waiting
    for the deepest zoom.
    """
    ranked = sorted((i for i, s in enumerate(scores) if _valid(s)), key=lambda i: -scores[i])
    levels = [LEVEL_COUNT] * len(scores)
    if positions is None:
        _global_levels(ranked, levels)
    else:
        _spatial_levels(ranked, positions, levels)
    if ranked:
        unscored_level = min(LEVEL_COUNT, max(levels[i] for i in ranked) + 1)
        ranked_set = set(ranked)
        for i in range(len(scores)):
            if i not in ranked_set:
                levels[i] = unscored_level
    return levels


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def compute_levels(field, is_node, tree, values, flows_abs, statuses=None, link_types=None,
                   positions=None):
    """Return a level per element (node indices if is_node, link indices otherwise).

    positions: (x, y) per element (or None) to spread the labels over the map.
    """
    if is_node:
        if field in NODE_CHANGE_FIELDS:
            return scores_to_levels(node_change_scores(tree, values), positions)
        return scores_to_levels(value_scores(values), positions)
    if field == "Status":
        return status_levels(statuses or [], link_types or [])
    if field in LINK_FLOW_FIELDS:
        levels = scores_to_levels(link_flow_scores(tree, flows_abs), positions)
        for li, (a, b) in enumerate(tree.link_ends):
            if a in tree.sources or b in tree.sources:
                levels[li] = ALWAYS_LEVEL
        return levels
    if field in LINK_CHANGE_FIELDS:
        return scores_to_levels(link_change_scores(tree, values), positions)
    return scores_to_levels(value_scores(values), positions)
