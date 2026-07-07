# -*- coding: utf-8 -*-
from .qgisred_network_graph import min_path


class ProfilePathError(Exception):
    pass


def build_profile_path(adjacency, reference_nodes):
    reference_nodes = list(reference_nodes)
    if not reference_nodes:
        return {"nodes": [], "links": [], "is_reference": []}
    if len(reference_nodes) == 1:
        return {"nodes": [reference_nodes[0]], "links": [], "is_reference": [True]}

    nodes = []
    links = []
    reference_indices = set()

    for i in range(len(reference_nodes) - 1):
        a = reference_nodes[i]
        b = reference_nodes[i + 1]
        result = min_path(adjacency, a, b)
        if result is None:
            raise ProfilePathError(
                "No path connects reference nodes '{}' and '{}'".format(a, b)
            )
        segment_nodes, segment_links = result
        if i == 0:
            reference_indices.add(0)
            nodes.extend(segment_nodes)
            links.extend(segment_links)
        else:
            nodes.extend(segment_nodes[1:])
            links.extend(segment_links)
        reference_indices.add(len(nodes) - 1)

    is_reference = [idx in reference_indices for idx in range(len(nodes))]
    return {"nodes": nodes, "links": links, "is_reference": is_reference}


def cumulative_distances(links, link_lengths):
    distances = [0.0]
    for link in links:
        distances.append(distances[-1] + float(link_lengths.get(link, 0.0)))
    return distances


def sample_node_variable(nodes, distances, node_values, is_reference=None):
    samples = []
    for i, node in enumerate(nodes):
        value = node_values.get(node)
        reference = True if is_reference is None else is_reference[i]
        samples.append(
            {
                "node": node,
                "distance": distances[i],
                "value": None if value is None else float(value),
                "is_reference": reference,
            }
        )
    return samples


def cumulative_link_losses(links, link_losses):
    values = [0.0]
    for link in links:
        values.append(values[-1] + float(link_losses.get(link, 0.0)))
    return values


def reference_nodes_from_path(path):
    return [path["nodes"][i] for i, is_ref in enumerate(path["is_reference"]) if is_ref]


def add_pass_node(path, node):
    for i, current in enumerate(path["nodes"]):
        if current == node and not path["is_reference"][i]:
            new_is_reference = list(path["is_reference"])
            new_is_reference[i] = True
            return {
                "nodes": list(path["nodes"]),
                "links": list(path["links"]),
                "is_reference": new_is_reference,
            }
    raise ProfilePathError("Node '{}' is not an intermediate point of the current path".format(node))


def remove_pass_node(reference_nodes, node):
    if node not in reference_nodes:
        raise ProfilePathError("Node '{}' is not a declared profile point".format(node))
    return [n for n in reference_nodes if n != node]


def move_pass_node(reference_nodes, node, new_node):
    if node not in reference_nodes:
        raise ProfilePathError("Only declared profile points can be moved")
    return [new_node if n == node else n for n in reference_nodes]
