# -*- coding: utf-8 -*-
import os
import sys
import types

import pytest

import QGISRed
from QGISRed.tools.utils.qgisred_network_graph import build_adjacency
from QGISRed.tools.utils.qgisred_profile_path import ProfilePathError

if "QGISRed.sections" not in sys.modules:
    _pkg = types.ModuleType("QGISRed.sections")
    _pkg.__path__ = [os.path.join(os.path.dirname(QGISRed.__file__), "sections")]
    sys.modules["QGISRed.sections"] = _pkg

from QGISRed.sections.profile_section import ProfileSection, ProfileState


class _Section(ProfileSection):
    def __init__(self, adjacency, link_lengths):
        self._activeProfile = ProfileState()
        self.messages = []
        self._profileAdjacency = adjacency
        self._profileLinkLengths = link_lengths

    def tr(self, text):
        return text

    def pushMessage(self, text, level=3):
        self.messages.append((text, level))

    def _redrawProfile(self):
        pass


def _branch(reference_nodes):
    return {"reference_nodes": list(reference_nodes), "offset": 0.0, "path": None, "distances": None}


def _grid():
    # A-B-C-D trunk; E hangs off both B and C; F hangs off E; G hangs off E.
    node_ids = ["A", "B", "C", "D", "E", "F", "G"]
    link_ids = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    link_from = [0, 1, 2, 1, 4, 2, 4]
    link_to = [1, 2, 3, 4, 5, 4, 6]
    lengths = {lid: 100.0 for lid in link_ids}
    return build_adjacency(node_ids, link_ids, link_from, link_to), lengths


def test_rebuild_places_branch_after_trunk_with_offset():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()

    assert s._profilePath["nodes"] == ["A", "B", "C", "D"]
    assert s._profileDistances == [0.0, 100.0, 200.0, 300.0]
    branch = s._profileBranches[0]
    assert branch["path"]["nodes"] == ["B", "E", "F"]
    assert branch["offset"] == 100.0
    assert branch["distances"] == [100.0, 200.0, 300.0]


def test_rebuild_rejects_branch_that_reuses_trunk_pipe():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["A", "C"])]
    with pytest.raises(ProfilePathError):
        s._rebuildProfilePaths()


def test_is_branch_origin():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    assert s._isBranchOrigin("B") is True
    assert s._isBranchOrigin("F") is False
    assert s._isBranchOrigin("C") is False


def test_branch_has_derivations_detects_subbranch():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    trunk_branch = _branch(["B", "F"])
    sub_branch = _branch(["E", "G"])
    s._profileBranches = [trunk_branch, sub_branch]
    s._rebuildProfilePaths()

    assert s._branchHasDerivations(trunk_branch) is True
    assert s._branchHasDerivations(sub_branch) is False


def test_remove_origin_is_blocked():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()

    s._applyProfileRemove("B")
    assert len(s._profileBranches) == 1
    assert s.messages


def test_remove_final_of_two_node_branch_deletes_it():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()

    s._applyProfileRemove("F")
    assert s._profileBranches == []


def test_remove_bifurcation_node_is_blocked():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"]), _branch(["E", "G"])]
    s._rebuildProfilePaths()

    # E is the origin of the sub-branch, so it cannot be removed from the trunk branch.
    s._applyProfileRemove("E")
    assert len(s._profileBranches) == 2
    assert s.messages


def test_move_bifurcation_reroutes_each_derivation():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()

    # Move the branch origin from B to C; the branch must re-route C-E-F.
    s._applyProfileMove("B", "C")
    branch = s._profileBranches[0]
    assert branch["reference_nodes"] == ["C", "F"]
    assert branch["path"]["nodes"] == ["C", "E", "F"]
    assert branch["offset"] == 200.0


def test_move_is_rejected_when_reroute_needs_declared_pipe():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()

    # D only connects to the trunk, so the branch cannot reach F from D.
    s._applyProfileMove("B", "D")
    branch = s._profileBranches[0]
    assert branch["reference_nodes"] == ["B", "F"]
    assert branch["path"]["nodes"] == ["B", "E", "F"]
    assert s.messages
