# -*- coding: utf-8 -*-
import pytest

from QGISRed.tools.utils.qgisred_network_graph import build_adjacency
from QGISRed.tools.utils.qgisred_profile_path import (
    ProfilePathError,
    build_profile_path,
    cumulative_distances,
    sample_node_variable,
    cumulative_link_losses,
)


def _network():
    node_ids = ["A", "B", "C", "D", "E"]
    link_ids = ["L1", "L2", "L3", "L4"]
    link_from = [0, 1, 2, 3]
    link_to = [1, 2, 3, 4]
    return build_adjacency(node_ids, link_ids, link_from, link_to)


def test_build_profile_path_single_reference():
    result = build_profile_path(_network(), ["A"])
    assert result == {"nodes": ["A"], "links": [], "is_reference": [True]}


def test_build_profile_path_autocompletes_intermediate_nodes():
    result = build_profile_path(_network(), ["A", "C"])
    assert result["nodes"] == ["A", "B", "C"]
    assert result["links"] == ["L1", "L2"]
    assert result["is_reference"] == [True, False, True]


def test_build_profile_path_multiple_references():
    result = build_profile_path(_network(), ["A", "C", "E"])
    assert result["nodes"] == ["A", "B", "C", "D", "E"]
    assert result["links"] == ["L1", "L2", "L3", "L4"]
    assert result["is_reference"] == [True, False, True, False, True]


def test_build_profile_path_disconnected_raises():
    node_ids = ["A", "B", "X"]
    link_ids = ["L1"]
    adjacency = build_adjacency(node_ids, link_ids, [0], [1])
    with pytest.raises(ProfilePathError):
        build_profile_path(adjacency, ["A", "X"])


def test_cumulative_distances():
    link_lengths = {"L1": 1000.0, "L2": 500.0}
    assert cumulative_distances(["L1", "L2"], link_lengths) == [0.0, 1000.0, 1500.0]


def test_cumulative_distances_missing_length_defaults_zero():
    assert cumulative_distances(["L1"], {}) == [0.0, 0.0]


def test_sample_node_variable():
    nodes = ["A", "B", "C"]
    distances = [0.0, 100.0, 250.0]
    node_values = {"A": 80.0, "B": 70.0, "C": 60.0}
    is_reference = [True, False, True]
    samples = sample_node_variable(nodes, distances, node_values, is_reference)
    assert samples[1] == {"node": "B", "distance": 100.0, "value": 70.0, "is_reference": False}
    assert samples[2]["value"] == 60.0


def test_sample_node_variable_missing_value_is_none():
    samples = sample_node_variable(["A"], [0.0], {})
    assert samples[0]["value"] is None
    assert samples[0]["is_reference"] is True


def test_cumulative_link_losses():
    losses = {"L1": 20.0, "L2": 40.0}
    assert cumulative_link_losses(["L1", "L2"], losses) == [0.0, 20.0, 60.0]
