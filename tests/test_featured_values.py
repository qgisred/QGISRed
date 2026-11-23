# -*- coding: utf-8 -*-
from QGISRed.ui.analysis import featured_values_config as fv_config
from QGISRed.ui.analysis import featured_values_fielddata as fv_data

HOUR = 3600 * fv_data.TICKS_PER_SECOND


def test_measured_value_follows_edits_rules_and_gaps():
    original = [(0, 10.0), (HOUR, -1.0), (2 * HOUR, 12.0), (8 * HOUR, 20.0)]
    changes = [fv_data.Change(2 * HOUR, 14.0, 1, fv_data.CHANGE_VALUE)]
    series = fv_data.Series(True, 0, original, changes, [])
    rules = fv_data.Rules(2.0, 0.0, 0.0, False, True)

    points = fv_data.effective_points(series, rules)

    assert points == [(0, 20.0), (2 * HOUR, 14.0), (8 * HOUR, 40.0)]
    assert fv_data.value_at(points, 0, 3600) == 20.0
    assert fv_data.value_at(points, 2 * HOUR + HOUR // 4, 3600) == 14.0
    assert fv_data.value_at(points, 5 * HOUR, 3600) is None


def test_rows_merge_signals_with_their_simulated_value_and_stack_by_level():
    config = fv_config.default_config()
    for item in (
        {"kind": "simulated", "element": "Node", "id": "N1", "field": "Pressure", "level": 1},
        {"kind": "simulated", "element": "Node", "id": "N1", "field": "Head", "level": 3},
        {"kind": "simulated", "element": "Node", "id": "N1", "field": "Demand", "level": 2},
        {"kind": "signal", "signal": "s_p", "level": 1},
    ):
        fv_config.add_item(config, item)
    signals = {"S_P": {"id": "S_P", "meter": "M1", "element": "N1", "magnitude": "Pressure"}}
    config["display"]["maxLevel"] = 2

    rows = fv_config.assign_slots(fv_config.build_rows(config, signals, ["N1"], ["P1"]), config["display"])

    by_field = {(row["kind"], row["field"]): row for row in rows}
    assert ("simulated", "Pressure") not in by_field
    measured = by_field[("signal", "Pressure")]
    assert (measured["id"], measured["group"], measured["slot"]) == ("N1", ("Meter", "M1"), 0)
    assert measured["showSimulated"] and measured["showMeasured"]
    assert by_field[("simulated", "Demand")]["slot"] == 0
    assert by_field[("simulated", "Head")]["slot"] == -1
