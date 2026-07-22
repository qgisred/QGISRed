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


HEAD_MAX = {"A": 100.0, "B": 95.0, "C": 90.0, "D": 85.0, "E": 93.0, "F": 80.0}
HEAD_MIN = {"A": 60.0, "B": 58.0, "C": 55.0, "D": 50.0, "E": 57.0, "F": 45.0}
PRESS_MAX = {"A": 40.0, "B": 38.0, "C": 36.0, "D": 34.0, "E": 37.0, "F": 30.0}
PRESS_MIN = {"A": 10.0, "B": 9.0, "C": 8.0, "D": 7.0, "E": 8.5, "F": 5.0}


class _Dock:
    def __init__(self):
        self.stable = None

    def setStableRanges(self, left, right):
        self.stable = (left, right)


class _Section(ProfileSection):
    def __init__(self, adjacency, link_lengths):
        self._activeProfile = ProfileState()
        self._profileAdjacency = adjacency
        self._profileLinkLengths = link_lengths
        self._profileNodeElev = {n: 30.0 for n in "ABCDEFG"}

    def _profileStats(self):
        stat_max = {n: {"Head": {"Value": HEAD_MAX[n]}, "Pressure": {"Value": PRESS_MAX[n]}} for n in HEAD_MAX}
        stat_min = {n: {"Head": {"Value": HEAD_MIN[n]}, "Pressure": {"Value": PRESS_MIN[n]}} for n in HEAD_MIN}
        return stat_max, stat_min


def _grid():
    node_ids = ["A", "B", "C", "D", "E", "F", "G"]
    link_ids = ["L1", "L2", "L3", "L4", "L5", "L6", "L7"]
    link_from = [0, 1, 2, 1, 4, 2, 4]
    link_to = [1, 2, 3, 4, 5, 4, 6]
    lengths = {lid: 100.0 for lid in link_ids}
    return build_adjacency(node_ids, link_ids, link_from, link_to), lengths


def _tree():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._profileBranches = [{"reference_nodes": ["B", "F"], "offset": 0.0, "path": None, "distances": None}]
    s._rebuildProfilePaths()
    return s


def test_head_stable_points_span_whole_simulation_over_all_nodes():
    s = _tree()
    segments = s._profileStableSegments(include_branches=True)
    pts = s._profileStableAxisPoints("Head", segments)
    values = [v for _d, v in pts]
    assert max(values) == 100.0  # A max
    assert min(values) == 45.0   # F min (branch node)


def test_headloss_has_no_stable_points():
    s = _tree()
    segments = s._profileStableSegments(include_branches=True)
    assert s._profileStableAxisPoints("HeadLoss", segments) is None


def test_apply_stable_ranges_includes_elevation_for_head():
    s = _tree()
    dock = _Dock()
    s._applyProfileStableRanges(dock, "Head", "")
    left, right = dock.stable
    values = [v for _d, v in left]
    assert 30.0 in values          # elevation folded in
    assert max(values) == 100.0
    assert right is None


def test_apply_stable_ranges_sets_right_axis_for_secondary():
    s = _tree()
    dock = _Dock()
    s._applyProfileStableRanges(dock, "Head", "Pressure")
    _left, right = dock.stable
    rvalues = [v for _d, v in right]
    assert max(rvalues) == 40.0   # A pressure max, main path only
    assert min(rvalues) == 7.0    # D pressure min


def test_apply_stable_ranges_branchless_head_has_no_branch_nodes():
    adjacency, lengths = _grid()
    s = _Section(adjacency, lengths)
    s._profileReferenceNodes = ["A", "D"]
    s._rebuildProfilePaths()
    dock = _Dock()
    s._applyProfileStableRanges(dock, "Head", "")
    left, _right = dock.stable
    values = [v for _d, v in left]
    assert max(values) == 100.0   # A head max
    assert min(values) == 30.0    # elevation floor
    assert 45.0 not in values     # F min head absent: no branch
    assert 80.0 not in values     # F max head absent: no branch
