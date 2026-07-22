# -*- coding: utf-8 -*-
import os
import sys
import types

import QGISRed
from QGISRed.tools.utils.qgisred_network_graph import build_adjacency

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

    def _recomputeProfileStructure(self):
        self._rebuildProfilePaths()

    def _redrawProfile(self):
        pass


def _branch(reference_nodes):
    return {"reference_nodes": list(reference_nodes), "offset": 0.0, "path": None, "distances": None}


def _grid():
    node_ids = ["A", "B", "C", "D", "E", "F", "G"]
    link_ids = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    link_from = [0, 1, 2, 1, 4, 2, 4]
    link_to = [1, 2, 3, 4, 5, 4, 6]
    lengths = {lid: 100.0 for lid in link_ids}
    return build_adjacency(node_ids, link_ids, link_from, link_to), lengths


def _labels(section, node_id):
    role = section._profileClassifyNode(node_id)
    return [label for label, _handler in section._profileMenuEntries(role, node_id)]


def _tree():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [_branch(["B", "F"])]
    s._rebuildProfilePaths()
    return s


def test_classify_origin():
    s = _tree()
    assert s._profileClassifyNode("A") == "origin"
    assert _labels(s, "A") == ["Extend path", "Create branch"]


def test_classify_main_terminal():
    s = _tree()
    assert s._profileClassifyNode("D") == "terminal"
    assert _labels(s, "D") == ["Extend path", "Create branch", "Move pass node", "Delete pass node"]


def test_classify_bifurcation():
    s = _tree()
    assert s._profileClassifyNode("B") == "bifurcation"
    assert _labels(s, "B") == ["Create branch"]


def test_classify_intermediate_path_node():
    s = _tree()
    assert s._profileClassifyNode("C") == "intermediate_path"
    assert _labels(s, "C") == ["Declare pass node"]
    assert s._profileClassifyNode("E") == "intermediate_path"


def test_classify_branch_terminal():
    s = _tree()
    assert s._profileClassifyNode("F") == "terminal"
    assert _labels(s, "F") == ["Extend path", "Create branch", "Move pass node", "Delete pass node"]


def test_classify_foreign_node_with_tree_offers_nothing():
    s = _tree()
    assert s._profileClassifyNode("G") is None
    assert _labels(s, "G") == []


def test_classify_declared_through_waypoint():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    assert s._profileClassifyNode("C") == "through"
    assert _labels(s, "C") == ["Create branch", "Move pass node", "Delete pass node"]


def test_classify_without_tree_offers_start_on_node_only():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    assert s._profileClassifyNode("A") == "start"
    assert _labels(s, "A") == ["Start new path here"]
    assert s._profileClassifyNode(None) is None


def test_extend_from_origin_prepends_and_marks_start():
    s = _tree()
    s._profileStartExtend("A")
    assert s._profileEditSeq == "main"
    assert s._profileExtendAtStart is True


def test_extend_from_terminal_appends():
    s = _tree()
    s._profileStartExtend("D")
    assert s._profileEditSeq == "main"
    assert s._profileExtendAtStart is False


def test_append_main_node_at_start_prepends():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["B", "D"]
    s._rebuildProfilePaths()
    s._profileEditSeq = "main"
    s._profileExtendAtStart = True
    s._profileAppendMainNode("A")
    assert s._profileReferenceNodes[0] == "A"
    assert s._profilePath["nodes"][0] == "A"


def test_append_main_node_rolls_back_when_it_breaks_a_branch():
    s = _tree()
    s._profileEditSeq = "main"
    s._profileExtendAtStart = True
    s._profileAppendMainNode("E")
    assert s._profileReferenceNodes == ["A", "D"]
    assert s.messages


def test_finish_sequence_prunes_empty_branch():
    s = _tree()
    s._profileStartBranch("C")
    assert len(s._profileBranches) == 2
    s._profileFinishSequence()
    assert len(s._profileBranches) == 1
    assert s._profileEditSeq is None
