# -*- coding: utf-8 -*-
import random
from collections import deque

import pytest

from QGISRed.tools.utils.qgisred_network_graph import (
    build_adjacency,
    build_adjacency_from_meta,
    min_path,
)
from QGISRed.tests.helpers.epanet_out_builder import build_epanet_out
from QGISRed.ui.analysis.qgisred_results_binary import getOut_Metadata


def _linear_network():
    node_ids = ["A", "B", "C", "D"]
    link_ids = ["L1", "L2", "L3"]
    link_from = [0, 1, 2]
    link_to = [1, 2, 3]
    return build_adjacency(node_ids, link_ids, link_from, link_to)


def test_adjacency_is_bidirectional():
    adjacency = _linear_network()
    assert ("L1", "B") in adjacency["A"]
    assert ("L1", "A") in adjacency["B"]
    assert ("L2", "C") in adjacency["B"]


def test_min_path_same_node():
    adjacency = _linear_network()
    assert min_path(adjacency, "A", "A") == (["A"], [])


def test_min_path_single_link():
    adjacency = _linear_network()
    assert min_path(adjacency, "A", "B") == (["A", "B"], ["L1"])


def test_min_path_linear():
    adjacency = _linear_network()
    nodes, links = min_path(adjacency, "A", "D")
    assert nodes == ["A", "B", "C", "D"]
    assert links == ["L1", "L2", "L3"]


def test_min_path_reverse():
    adjacency = _linear_network()
    nodes, links = min_path(adjacency, "D", "A")
    assert nodes == ["D", "C", "B", "A"]
    assert links == ["L3", "L2", "L1"]


def test_min_path_minimizes_number_of_links():
    node_ids = ["A", "B", "C", "D"]
    link_ids = ["direct", "long1", "long2"]
    link_from = [0, 0, 2]
    link_to = [3, 2, 3]
    adjacency = build_adjacency(node_ids, link_ids, link_from, link_to)
    nodes, links = min_path(adjacency, "A", "D")
    assert nodes == ["A", "D"]
    assert links == ["direct"]


def test_min_path_disconnected_returns_none():
    node_ids = ["A", "B", "X", "Y"]
    link_ids = ["L1", "LX"]
    link_from = [0, 2]
    link_to = [1, 3]
    adjacency = build_adjacency(node_ids, link_ids, link_from, link_to)
    assert min_path(adjacency, "A", "X") is None


def test_min_path_unknown_node_returns_none():
    adjacency = _linear_network()
    assert min_path(adjacency, "A", "Z") is None


def test_min_path_excluded_links_forces_detour():
    node_ids = ["A", "B", "C", "D"]
    link_ids = ["direct", "long1", "long2"]
    link_from = [0, 0, 2]
    link_to = [3, 2, 3]
    adjacency = build_adjacency(node_ids, link_ids, link_from, link_to)
    nodes, links = min_path(adjacency, "A", "D", excluded_links={"direct"})
    assert nodes == ["A", "C", "D"]
    assert links == ["long1", "long2"]


def test_min_path_excluded_links_can_disconnect():
    adjacency = _linear_network()
    assert min_path(adjacency, "A", "D", excluded_links={"L2"}) is None


def test_min_path_excluded_links_none_is_default():
    adjacency = _linear_network()
    assert min_path(adjacency, "A", "D", excluded_links=None) == (
        ["A", "B", "C", "D"],
        ["L1", "L2", "L3"],
    )


def _reference_hop_distance(adjacency, start, end):
    if start == end:
        return 0
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        node, dist = queue.popleft()
        for _link, neighbor in adjacency.get(node, []):
            if neighbor == end:
                return dist + 1
            if neighbor not in seen:
                seen.add(neighbor)
                queue.append((neighbor, dist + 1))
    return None


def _path_is_walkable(adjacency, nodes, links, start, end):
    if nodes[0] != start or nodes[-1] != end or len(links) != len(nodes) - 1:
        return False
    for i, link in enumerate(links):
        if not any(l == link and nb == nodes[i + 1] for l, nb in adjacency[nodes[i]]):
            return False
    return True


@pytest.mark.parametrize("seed", range(400))
def test_min_path_is_always_minimal_on_random_meshed_graphs(seed):
    rng = random.Random(seed)
    n = rng.randint(4, 14)
    node_ids = [f"N{i}" for i in range(n)]
    link_ids, link_from, link_to = [], [], []
    for e in range(rng.randint(n, n * 3)):
        a, b = rng.randrange(n), rng.randrange(n)
        if a == b:
            continue
        link_ids.append(f"L{e}")
        link_from.append(a)
        link_to.append(b)
    adjacency = build_adjacency(node_ids, link_ids, link_from, link_to)
    start, end = node_ids[0], node_ids[-1]
    result = min_path(adjacency, start, end)
    reference = _reference_hop_distance(adjacency, start, end)
    if reference is None:
        assert result is None
    else:
        assert result is not None
        nodes, links = result
        assert _path_is_walkable(adjacency, nodes, links, start, end)
        assert len(links) == reference


def test_adjacency_from_metadata_matches_binary_indexing():
    node_ids = ["R1", "J1", "J2"]
    link_ids = ["P1", "P2"]
    data = build_epanet_out(
        node_ids=node_ids,
        link_ids=link_ids,
        link_from=[0, 1],
        link_to=[1, 2],
        link_types=[1, 1],
        tank_node_indices=[0],
        tank_areas=[0.0],
        node_elevations=[100.0, 50.0, 30.0],
        link_lengths=[1000.0, 500.0],
        link_diameters=[300.0, 200.0],
        periods_node_data=[[(-10.0, 100.0, 0.0, 0.0), (5.0, 80.0, 29.0, 0.5), (5.0, 60.0, 29.0, 0.3)]],
        periods_link_data=[[(10.0, 1.5, 20.0, 0.4, 3.0, 0.0, 0.0, 0.02), (5.0, 1.0, 40.0, 0.3, 3.0, 0.0, 0.0, 0.03)]],
    )
    import io

    meta = getOut_Metadata(io.BytesIO(data))
    adjacency = build_adjacency_from_meta(meta)
    nodes, links = min_path(adjacency, "R1", "J2")
    assert nodes == ["R1", "J1", "J2"]
    assert links == ["P1", "P2"]
