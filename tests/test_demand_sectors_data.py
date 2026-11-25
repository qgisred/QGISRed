# -*- coding: utf-8 -*-
from QGISRed.ui.digitaltwin import demand_sectors_data as ds_data

ANSWER = "OK\nsummary\t1\t1\t0\t2\nsector\tS1\tValid\t10\t9\t1\t12.5\nsector\tZ1\tZ\t4\t3\t1\t0.05"


def test_the_options_carry_the_z_limit_with_a_dot_decimal():
    assert ds_data.build_options(0.25) == "zLimit=0.25"
    assert ds_data.build_options(1) == "zLimit=1.0"


def test_an_answer_becomes_a_summary_and_one_row_per_sector():
    result = ds_data.parse_identification(ANSWER)

    assert result["summary"] == {ds_data.VALID: 1, ds_data.Z: 1, ds_data.UNCONTROLLED: 0, "ignoredMeters": 2}
    assert result["sectors"] == [
        {"id": "S1", "kind": "Valid", "nodes": 10, "links": 9, "meters": 1, "demand": 12.5},
        {"id": "Z1", "kind": "Z", "nodes": 4, "links": 3, "meters": 1, "demand": 0.05},
    ]


def test_an_error_answer_is_not_an_identification():
    assert ds_data.parse_identification("Error: no folder") is None
    assert ds_data.parse_identification("") is None
    assert ds_data.error_message("Error: no folder") == "no folder"


def test_unreadable_rows_are_skipped():
    result = ds_data.parse_identification("OK\nsector\tS1\tValid\tx\t9\t1\t12.5\nsector\tS2\tValid\t5\t4\t1\t3\n\n")

    assert [sector["id"] for sector in result["sectors"]] == ["S2"]


def test_the_sectors_can_be_created_only_when_one_is_not_uncontrolled():
    uncontrolled = ds_data.parse_identification("OK\nsummary\t0\t0\t1\t0\nsector\tU1\tUncontrolled\t5\t4\t0\t3")

    assert ds_data.can_create(ds_data.parse_identification(ANSWER))
    assert not ds_data.can_create(uncontrolled)
    assert not ds_data.can_create(None)


def test_only_flow_counter_and_level_meters_delimit_sectors():
    assert ds_data.has_sector_meters(["Manometer", "Flowmeter"])
    assert ds_data.has_sector_meters([" levelsensor "])
    assert not ds_data.has_sector_meters(["Manometer", None, ""])
    assert not ds_data.has_sector_meters([])
