# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.results_label_priority import (
    BASE_COUNT,
    LEVEL_COUNT,
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
    # The reservoir outlet and both legs of the tee outrank pipes that just carry the
    # same flow on.
    assert scores[0] > scores[2] > scores[1]
    assert scores[4] > scores[5]
    # Top BASE_COUNT -> level 1, next ones -> level 2; a zero score -> the level after
    # the last one in use, not the deepest zoom.
    levels = scores_to_levels([float(i) for i in range(BASE_COUNT * 2 + 1)])
    assert levels[-1] == 1 and levels[-BASE_COUNT - 1] == 2 and levels[0] == 3 < LEVEL_COUNT
