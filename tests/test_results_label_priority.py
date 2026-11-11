# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.results_label_priority import (
    ALWAYS_LEVEL,
    FlowTree,
    compute_levels,
    link_flow_scores,
    node_change_scores,
    scores_to_levels,
)


def _main_with_branch():
    # Reservoir 0 feeds a main 0-1-2-3-4; node 2 tees off a small branch 2-5-6.
    link_ends = [(0, 1), (1, 2), (2, 3), (3, 4), (2, 5), (5, 6)]
    flows = [100.0, 99.0, 60.0, 59.0, 40.0, 39.0]
    return FlowTree(7, link_ends, flows, roots=[0]), flows


def test_node_pressure_relevance_follows_the_change_along_the_flow_tree():
    tree, flows = _main_with_branch()
    pressures = [50.0, 49.0, 30.0, 29.5, 29.0, 28.0, 10.0]
    scores = node_change_scores(tree, pressures)
    assert scores[0] == max(scores)                      # the source comes first
    assert scores[2] > scores[1] > scores[3]             # big drop at 2 beats small ones
    assert scores[6] == 20.0                             # dead end: change since the tee
    assert compute_levels("Pressure", True, tree, pressures, flows)[0] == 1


def test_link_flow_relevance_discounts_the_plain_continuation():
    tree, flows = _main_with_branch()
    scores = link_flow_scores(tree, flows)
    # Both legs of the tee outrank pipes that just carry the same flow on.
    assert scores[2] > scores[1]
    assert scores[4] > scores[5]
    # The reservoir outlet is always shown.
    assert compute_levels("Flow", False, tree, [None] * 6, flows)[0] == ALWAYS_LEVEL


def test_levels_spread_the_labels_over_the_whole_map():
    # A busy cluster with big scores on the left and a quiet one with small scores on
    # the right: the quiet area still gets a level-1 label, and a zero score is not
    # left for the deepest zoom.
    positions = [(0, 0), (1, 0), (2, 0), (100, 0), (101, 0), (102, 0)]
    scores = [90.0, 80.0, 70.0, 3.0, 2.0, 0.0]
    levels = scores_to_levels(scores, positions)
    assert levels[0] == 1 and levels[3] == 1
    assert levels[1] > 1 and levels[4] > 1
    assert levels[5] == max(levels[:5]) + 1
