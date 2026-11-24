# -*- coding: utf-8 -*-
from QGISRed.ui.analysis import featured_values_config as fv_config
from QGISRed.ui.analysis import featured_values_fielddata as fv_data


def test_field_data_answers_from_the_dll_become_signals_and_values():
    signals = fv_data.parse_signals("OK\nS_P\tM1\tN1\tPressure\tm\t10.5\t20\t1\nS_Q\t\tP1\tFlow\tl/s\t\t\t0")
    values = fv_data.parse_values("OK\nS_P\t31.25\nS_Q\t")

    assert signals["S_P"] == {"id": "S_P", "meter": "M1", "element": "N1", "magnitude": "Pressure", "units": "m",
                              "point": (10.5, 20.0), "hasData": True}
    assert signals["S_Q"]["point"] is None and not signals["S_Q"]["hasData"]
    assert values == {"S_P": 31.25, "S_Q": None}
    assert fv_data.parse_signals("Error: no folder") == {}


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
