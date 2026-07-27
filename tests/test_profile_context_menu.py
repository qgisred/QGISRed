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


def _linear():
    # A-B-C-D-E chain: A,E connectivity 1; B,C,D connectivity 2.
    node_ids = ["A", "B", "C", "D", "E"]
    link_ids = ["L1", "L2", "L3", "L4"]
    link_from = [0, 1, 2, 3]
    link_to = [1, 2, 3, 4]
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
    # A has connectivity 1 (only L1, already used): no extend, no branch — only move/delete.
    assert _labels(s, "A") == ["Move pass node", "Delete pass node"]


def test_classify_main_terminal():
    s = _tree()
    assert s._profileClassifyNode("D") == "terminal"
    # D has connectivity 1 (only L3, used): no line free to extend — only move/delete.
    assert _labels(s, "D") == ["Move pass node", "Delete pass node"]


def test_classify_bifurcation():
    s = _tree()
    assert s._profileClassifyNode("B") == "bifurcation"
    # B has connectivity 3 but all its lines (L1, L2, L4) are already used: no free
    # line for another branch. A branch origin is not deletable, so only move.
    assert _labels(s, "B") == ["Move pass node"]


def test_classify_intermediate_path_node():
    s = _tree()
    assert s._profileClassifyNode("C") == "intermediate_path"
    assert _labels(s, "C") == ["Declare pass node"]
    assert s._profileClassifyNode("E") == "intermediate_path"


def test_classify_branch_terminal():
    s = _tree()
    assert s._profileClassifyNode("F") == "terminal"
    # F has connectivity 1 (only L5, used): no line free to extend — only move/delete.
    assert _labels(s, "F") == ["Move pass node", "Delete pass node"]


def test_classify_foreign_node_with_tree_offers_nothing():
    s = _tree()
    assert s._profileClassifyNode("G") is None
    assert _labels(s, "G") == []


def test_classify_declared_through_waypoint():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    # C has connectivity 3 with a free line (L6): branch is offered (Rule 3).
    assert s._profileClassifyNode("C") == "through"
    assert _labels(s, "C") == ["Create branch", "Move pass node", "Delete pass node"]


def test_connectivity_2_interior_node_has_no_branch():
    adjacency, lengths = _linear()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["B", "C", "D"]
    s._rebuildProfilePaths()
    # C is an interior pass node of connectivity 2 (both lines used): no branch (Rule 2).
    assert s._profileClassifyNode("C") == "through"
    assert _labels(s, "C") == ["Move pass node", "Delete pass node"]


def test_connectivity_2_endpoints_can_extend():
    adjacency, lengths = _linear()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["B", "C", "D"]
    s._rebuildProfilePaths()
    # B and D are connectivity-2 endpoints with a free line, so extend is offered.
    assert _labels(s, "B") == ["Extend path", "Move pass node", "Delete pass node"]
    assert _labels(s, "D") == ["Extend path", "Move pass node", "Delete pass node"]


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


def test_double_click_intermediate_declares_pass_node():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._rebuildProfilePaths()
    assert s._profileClassifyNode("C") == "intermediate_path"

    s._profileHandleDoubleClickNode("C")

    assert "C" in s._profileReferenceNodes


def test_double_click_pass_node_deletes_it():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    assert s._profileClassifyNode("C") == "through"

    s._profileHandleDoubleClickNode("C")

    assert s._profileReferenceNodes == ["A", "D"]


def test_double_click_ignored_during_tracing():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    s._profileEditSeq = "main"  # mid-tracing

    s._profileHandleDoubleClickNode("C")

    assert s._profileReferenceNodes == ["A", "C", "D"]  # unchanged


def test_left_click_pass_node_arms_move():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    s._profileEditSeq = None
    s._resolveProfileNode = lambda _point: "C"  # C is a declared pass node

    s._profileEditLeftClick(object())

    assert s._profileEditSeq == "move"
    assert s._profileMoveSource == "C"


def test_left_click_intermediate_node_does_nothing():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._rebuildProfilePaths()
    s._profileEditSeq = None
    s._resolveProfileNode = lambda _point: "C"  # C is intermediate, not declared

    s._profileEditLeftClick(object())

    assert s._profileEditSeq is None
    assert getattr(s, "_profileMoveSource", None) is None


def test_right_double_click_endpoint_extends():
    adjacency, lengths = _linear()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["B", "C", "D"]
    s._rebuildProfilePaths()
    s._profileContextPending = True  # a menu was deferred by the first right-click
    # B is the path start with a free line (A-B), so extend is armed at the start.
    s._profileHandleRightDoubleClickNode("B")
    assert s._profileEditSeq == "main"
    assert s._profileExtendAtStart is True


def test_right_double_click_interior_pass_starts_branch():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    s._profileContextPending = True
    # C has connectivity 3 with a free line (L6), so a branch is started.
    s._profileHandleRightDoubleClickNode("C")
    assert s._profileEditSeq == "branch"
    assert len(s._profileBranches) == 1


def test_right_double_click_ignored_without_pending_menu():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "C", "D"]
    s._rebuildProfilePaths()
    # No context menu was deferred (e.g. a stray double right-click): do nothing.
    s._profileHandleRightDoubleClickNode("C")
    assert getattr(s, "_profileEditSeq", None) is None
    assert s._profileBranches == []
