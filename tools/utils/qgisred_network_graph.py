# -*- coding: utf-8 -*-
from collections import OrderedDict


def build_adjacency(node_ids, link_ids, link_from, link_to):
    adjacency = OrderedDict((nid, []) for nid in node_ids)
    for i, lid in enumerate(link_ids):
        from_idx = link_from[i]
        to_idx = link_to[i]
        if from_idx < 0 or to_idx < 0:
            continue
        if from_idx >= len(node_ids) or to_idx >= len(node_ids):
            continue
        a = node_ids[from_idx]
        b = node_ids[to_idx]
        adjacency.setdefault(a, []).append((lid, b))
        adjacency.setdefault(b, []).append((lid, a))
    return adjacency


def build_adjacency_from_meta(meta):
    return build_adjacency(
        meta["node_ids"],
        meta["link_ids"],
        meta["link_from"],
        meta["link_to"],
    )


def _expand_level(adjacency, level, parent_own, parent_other, excluded):
    next_level = []
    for node in level:
        for link, neighbor in adjacency.get(node, []):
            if link in excluded:
                continue
            if neighbor in parent_own:
                continue
            parent_own[neighbor] = (node, link)
            if neighbor in parent_other:
                return next_level, neighbor
            next_level.append(neighbor)
    return next_level, None


def _reconstruct(meet, parent_forward, parent_backward):
    nodes_forward = []
    links_forward = []
    node = meet
    while node is not None:
        prev, link = parent_forward[node]
        nodes_forward.append(node)
        if link is not None:
            links_forward.append(link)
        node = prev
    nodes_forward.reverse()
    links_forward.reverse()

    nodes_backward = []
    links_backward = []
    node = meet
    while True:
        prev, link = parent_backward[node]
        if link is None:
            break
        nodes_backward.append(prev)
        links_backward.append(link)
        node = prev

    return nodes_forward + nodes_backward, links_forward + links_backward


def min_path(adjacency, start, end, excluded_links=None):
    if start not in adjacency or end not in adjacency:
        return None
    if start == end:
        return [start], []

    excluded = excluded_links or set()
    parent_forward = {start: (None, None)}
    parent_backward = {end: (None, None)}
    level_forward = [start]
    level_backward = [end]
    expand_forward = True

    while level_forward and level_backward:
        if expand_forward:
            level_forward, meet = _expand_level(
                adjacency, level_forward, parent_forward, parent_backward, excluded
            )
        else:
            level_backward, meet = _expand_level(
                adjacency, level_backward, parent_backward, parent_forward, excluded
            )
        if meet is not None:
            return _reconstruct(meet, parent_forward, parent_backward)
        expand_forward = not expand_forward

    return None
