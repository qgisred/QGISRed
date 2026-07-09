# -*- coding: utf-8 -*-
import pytest

from QGISRed.tools.utils.qgisred_network_graph import build_adjacency
from QGISRed.tools.utils.qgisred_profile_path import (
    ProfilePathError,
    build_profile_path,
    cumulative_distances,
    sample_node_variable,
    cumulative_link_losses,
    reference_nodes_from_path,
    add_pass_node,
    remove_pass_node,
    move_pass_node,
    flow_direction_along_path,
    envelope_points,
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


def test_reference_nodes_from_path():
    path = build_profile_path(_network(), ["A", "C", "E"])
    assert reference_nodes_from_path(path) == ["A", "C", "E"]


def test_add_pass_node_converts_intermediate_without_changing_trace():
    path = build_profile_path(_network(), ["A", "C"])
    assert path["nodes"] == ["A", "B", "C"]
    updated = add_pass_node(path, "B")
    assert updated["nodes"] == ["A", "B", "C"]
    assert updated["links"] == path["links"]
    assert updated["is_reference"] == [True, True, True]
    assert reference_nodes_from_path(updated) == ["A", "B", "C"]


def test_add_pass_node_rejects_non_intermediate():
    path = build_profile_path(_network(), ["A", "C"])
    with pytest.raises(ProfilePathError):
        add_pass_node(path, "A")
    with pytest.raises(ProfilePathError):
        add_pass_node(path, "E")


def test_remove_interior_pass_node_merges_segment():
    refs = ["A", "C", "E"]
    new_refs = remove_pass_node(refs, "C")
    assert new_refs == ["A", "E"]
    path = build_profile_path(_network(), new_refs)
    assert path["nodes"] == ["A", "B", "C", "D", "E"]
    assert path["is_reference"] == [True, False, False, False, True]


def test_remove_endpoint_pass_node_trims():
    refs = ["A", "C", "E"]
    path = build_profile_path(_network(), remove_pass_node(refs, "A"))
    assert path["nodes"] == ["C", "D", "E"]


def test_remove_pass_node_rejects_non_reference():
    with pytest.raises(ProfilePathError):
        remove_pass_node(["A", "C"], "B")


def test_move_pass_node_recomputes_adjacent_segments():
    refs = ["A", "C", "E"]
    new_refs = move_pass_node(refs, "C", "D")
    assert new_refs == ["A", "D", "E"]
    path = build_profile_path(_network(), new_refs)
    assert path["nodes"] == ["A", "B", "C", "D", "E"]
    assert path["is_reference"] == [True, False, False, True, True]


def test_move_pass_node_rejects_non_reference():
    with pytest.raises(ProfilePathError):
        move_pass_node(["A", "C"], "B", "D")


def test_flow_direction_forward_link_positive_flow():
    nodes = ["A", "B"]
    links = ["L1"]
    endpoints = {"L1": ("A", "B")}
    assert flow_direction_along_path(nodes, links, endpoints, {"L1": 5.0}) == [1]


def test_flow_direction_forward_link_negative_flow():
    nodes = ["A", "B"]
    links = ["L1"]
    endpoints = {"L1": ("A", "B")}
    assert flow_direction_along_path(nodes, links, endpoints, {"L1": -5.0}) == [-1]


def test_flow_direction_path_traverses_link_backwards():
    nodes = ["B", "A"]
    links = ["L1"]
    endpoints = {"L1": ("A", "B")}
    assert flow_direction_along_path(nodes, links, endpoints, {"L1": 5.0}) == [-1]
    assert flow_direction_along_path(nodes, links, endpoints, {"L1": -5.0}) == [1]


def test_flow_direction_zero_or_missing_flow():
    nodes = ["A", "B", "C"]
    links = ["L1", "L2"]
    endpoints = {"L1": ("A", "B"), "L2": ("B", "C")}
    assert flow_direction_along_path(nodes, links, endpoints, {"L1": 0.0}) == [0, 0]


def test_envelope_points_aligns_max_min_to_nodes():
    nodes = ["A", "B", "C"]
    distances = [0.0, 100.0, 250.0]
    stat_max = {"A": {"Head": {"Value": 82.0}}, "B": {"Head": {"Value": 71.0}}, "C": {"Head": {"Value": 61.0}}}
    stat_min = {"A": {"Head": {"Value": 78.0}}, "B": {"Head": {"Value": 65.0}}, "C": {"Head": {"Value": 55.0}}}
    max_pts, min_pts = envelope_points(nodes, distances, stat_max, stat_min, "Head")
    assert max_pts == [(0.0, 82.0), (100.0, 71.0), (250.0, 61.0)]
    assert min_pts == [(0.0, 78.0), (100.0, 65.0), (250.0, 55.0)]


def test_envelope_points_missing_node_is_none():
    max_pts, min_pts = envelope_points(["A", "X"], [0.0, 50.0], {"A": {"Head": {"Value": 5.0}}}, {}, "Head")
    assert max_pts == [(0.0, 5.0), (50.0, None)]
    assert min_pts == [(0.0, None), (50.0, None)]
