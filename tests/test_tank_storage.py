# -*- coding: utf-8 -*-
import math

import pytest

from QGISRed.ui.analysis.qgisred_results_binary import _NT_JUNCTION, _NT_RESERVOIR, _NT_TANK
from QGISRed.ui.analysis.qgisred_tank_storage import (
    _find_tank_row,
    _tank_area_from_diameter,
    _tank_can_overflow,
    _tank_diameter_dbf_to_model_length,
    _tank_node_index,
    _tank_spill_value,
    cylindrical_volume_from_level,
    getOut_TimesTankSpill,
    getOut_TimesTankStoredVolumes,
    getOut_TimesTankVolume,
    getOut_TimesTotalTankSpill,
    interpolate_volume_curve,
    spill_flow_from_tank_state,
    total_stored_volume_from_tank_rows,
    total_tank_spill_from_period,
    volume_from_level,
)
from QGISRed.tests.helpers.epanet_out_builder import build_epanet_out


def _cylindrical_volume(head, elevation, min_level, min_volume, diameter):
    level = head - elevation
    area = _tank_area_from_diameter(diameter)
    return cylindrical_volume_from_level(
        level,
        min_volume=min_volume,
        min_level=min_level,
        cross_section_area=area,
    )


class TestVolumeFromLevel:
    def test_cylindrical(self):
        volume, uses_curve = volume_from_level(
            2.0, min_volume=10.0, min_level=0.0, cross_section_area=math.pi * 4.0,
        )
        assert uses_curve is False
        assert volume == pytest.approx(10.0 + math.pi * 4.0 * 2.0)

    def test_cylindrical_with_min_level(self):
        volume = cylindrical_volume_from_level(
            3.0, min_volume=10.0, min_level=1.0, cross_section_area=math.pi * 4.0,
        )
        assert volume == pytest.approx(10.0 + math.pi * 4.0 * 2.0)

    def test_si_dbf_diameter_mm_to_meters(self):
        assert _tank_diameter_dbf_to_model_length(15500.0, 5) == pytest.approx(15.5)
        d_m = _tank_diameter_dbf_to_model_length(4000.0, 5)
        assert _tank_area_from_diameter(d_m) == pytest.approx(math.pi * 4.0)

    def test_us_dbf_diameter_feet_unchanged(self):
        assert _tank_diameter_dbf_to_model_length(60.0, 1) == pytest.approx(60.0)

    def test_interpolate_curve(self):
        points = [(0.0, 10.0), (2.0, 30.0), (4.0, 70.0)]
        assert interpolate_volume_curve(1.0, points) == pytest.approx(20.0)
        assert interpolate_volume_curve(0.0, points) == pytest.approx(10.0)
        assert interpolate_volume_curve(5.0, points) == pytest.approx(70.0)

    def test_curve_volume_floors_at_hmin(self):
        points = [(2.0, 30.0), (4.0, 70.0)]
        volume, uses_curve = volume_from_level(
            1.0, min_volume=0.0, min_level=2.0, cross_section_area=0.0,
            volume_curve_points=points,
        )
        assert uses_curve is True
        assert volume == pytest.approx(30.0)

    def test_cylindrical_floors_at_vmin(self):
        volume, uses_curve = volume_from_level(
            0.0, min_volume=10.0, min_level=2.0, cross_section_area=math.pi * 4.0,
        )
        assert uses_curve is False
        assert volume == pytest.approx(10.0)

    def test_undeclared_min_volume_defaults_to_area_times_min_level(self):
        """EPANET: when MinVolume=0, Vmin = A*Hmin so stored volume = A*h, not A*(h-Hmin)."""
        area = math.pi * 4.0
        volume, uses_curve = volume_from_level(
            5.0, min_volume=0.0, min_level=2.0, cross_section_area=area,
        )
        assert uses_curve is False
        assert volume == pytest.approx(area * 5.0)


class TestTotalStoredVolumeFromRows:
    def test_sum_multiple_tanks(self):
        rows = [
            {"volumes": [100.0, 110.0]},
            {"volumes": [200.0, 210.0]},
        ]
        assert total_stored_volume_from_tank_rows(rows) == pytest.approx([300.0, 320.0])

    def test_empty_rows(self):
        assert total_stored_volume_from_tank_rows([]) == []


class TestThreeTankNetworkFormula:
    """Regression from manual EPANET check (SI, diameter in metres).

    All three tanks have undeclared ``MinVolume`` (0), so EPANET sets ``Vmin = A*Hmin``
    and stored volume is ``A*h`` for each.
    """

    TANKS = (
        ("tank1", [145.00, 145.65, 147.06], 131.90, 0.1, 0.0, 85.0),
        ("tank2", [140.00, 138.655, 137.398], 116.50, 6.5, 0.0, 50.0),
        ("tank3", [158.00, 158.85, 160.01], 129.00, 4.0, 0.0, 164.0),
    )
    EPANET_TOTALS = (733076.12, 752079.10, 782115.95)

    def _rows_for_all_hours(self):
        return [
            {
                "volumes": [
                    _cylindrical_volume(heads[h], elev, hmin, vmin, diam)
                    for h in range(3)
                ],
            }
            for _tid, heads, elev, hmin, vmin, diam in self.TANKS
        ]

    def _expected_total(self, hour):
        return sum(
            _cylindrical_volume(heads[hour], elev, hmin, vmin, diam)
            for _tid, heads, elev, hmin, vmin, diam in self.TANKS
        )

    def test_sum_matches_formula_each_hour(self):
        totals = total_stored_volume_from_tank_rows(self._rows_for_all_hours())
        for hour in range(3):
            assert totals[hour] == pytest.approx(self._expected_total(hour), rel=1e-6)

    def test_hour_zero_matches_epanet(self):
        assert self._expected_total(0) == pytest.approx(self.EPANET_TOTALS[0], rel=1e-5)


class TestTankSpillFlow:
    def test_overflow_flag(self):
        assert _tank_can_overflow("YES") is True
        assert _tank_can_overflow("no") is False
        assert _tank_can_overflow("") is False

    def test_spill_only_when_full(self):
        assert spill_flow_from_tank_state(
            12.5, 24.9, can_overflow=True, min_level=5.0, max_level=25.0,
        ) == 0.0
        assert spill_flow_from_tank_state(
            12.5, 25.0, can_overflow=True, min_level=5.0, max_level=25.0,
        ) == pytest.approx(12.5)

    def test_no_overflow_tank(self):
        assert spill_flow_from_tank_state(
            20.0, 30.0, can_overflow=False, min_level=0.0, max_level=10.0,
        ) == 0.0

    def test_sum_two_overflow_tanks(self):
        node_types = [_NT_TANK, _NT_TANK]
        node_ids = ["T1", "T2"]
        props = {
            "T1": {
                "elevation": 100.0,
                "min_level": 0.0,
                "max_level": 20.0,
                "can_overflow": True,
            },
            "T2": {
                "elevation": 50.0,
                "min_level": 0.0,
                "max_level": 10.0,
                "can_overflow": True,
            },
        }
        demands = [5.0, 3.0]
        heads = [120.0, 60.0]
        total = total_tank_spill_from_period(
            demands, heads, node_types, node_ids, props,
        )
        assert total == pytest.approx(8.0)

    def test_skips_tank_without_overflow_enabled(self):
        node_types = [_NT_TANK]
        node_ids = ["T1"]
        props = {
            "T1": {
                "elevation": 100.0,
                "min_level": 0.0,
                "max_level": 20.0,
                "can_overflow": False,
            },
        }
        assert total_tank_spill_from_period(
            [10.0], [120.0], node_types, node_ids, props,
        ) == 0.0


class TestGetOutTimesTankStoredVolumes:
    def test_missing_out_returns_empty(self):
        assert getOut_TimesTankStoredVolumes("/no/such/file.out", "", "Net") == []
        assert getOut_TimesTotalTankSpill("/no/such/file.out", "", "Net") == []


class TestFindTankRow:
    def test_returns_matching_row(self):
        rows = [{"tank_id": "A", "volumes": [1.0]}, {"tank_id": "B", "volumes": [2.0]}]
        assert _find_tank_row(rows, "B") == {"tank_id": "B", "volumes": [2.0]}

    def test_missing_returns_none(self):
        assert _find_tank_row([{"tank_id": "A"}], "Z") is None
        assert _find_tank_row([], "A") is None


class TestTankNodeIndex:
    META = {
        "node_ids": ["R1", "J1", "T1", "T2"],
        "node_types": [_NT_RESERVOIR, _NT_JUNCTION, _NT_TANK, _NT_TANK],
    }

    def test_finds_tank(self):
        assert _tank_node_index(self.META, "T1") == 2
        assert _tank_node_index(self.META, "T2") == 3

    def test_reservoir_and_junction_are_not_tanks(self):
        assert _tank_node_index(self.META, "R1") is None
        assert _tank_node_index(self.META, "J1") is None

    def test_unknown_id(self):
        assert _tank_node_index(self.META, "XX") is None


class TestTankSpillValue:
    PROPS = {"elevation": 100.0, "min_level": 5.0, "max_level": 25.0, "can_overflow": True}

    def test_spill_only_when_full(self):
        # head - elevation = 24.9 < max_level -> no spill
        assert _tank_spill_value(12.5, 124.9, self.PROPS) == 0.0
        # head - elevation = 25.0 == max_level -> spill equals demand
        assert _tank_spill_value(12.5, 125.0, self.PROPS) == pytest.approx(12.5)

    def test_no_spill_without_overflow_enabled(self):
        props = dict(self.PROPS, can_overflow=False)
        assert _tank_spill_value(12.5, 125.0, props) == 0.0

    def test_factors_applied(self):
        # head_factor scales head, demand_factor scales the spill flow
        assert _tank_spill_value(
            10.0, 12.5, self.PROPS, head_factor=10.0, demand_factor=2.0,
        ) == pytest.approx(20.0)


def _tank_network_out(tmp_path):
    """Two storage tanks (T1, T2), one reservoir, one junction; two report steps.

    T1: area = pi, elevation = 100 ; T2: area = 2.0, elevation = 50.
    With no project DBF, EPANET MinVolume defaults to 0, so stored volume is
    ``area * (head - elevation)``.
    """
    node_ids = ["R1", "J1", "T1", "T2"]
    p0 = [
        (0.0, 200.0, 0.0, 0.0),   # R1
        (5.0, 70.0, 0.0, 0.0),    # J1
        (0.0, 105.0, 0.0, 0.0),   # T1 -> level 5
        (0.0, 60.0, 0.0, 0.0),    # T2 -> level 10
    ]
    p1 = [
        (0.0, 200.0, 0.0, 0.0),
        (5.0, 68.0, 0.0, 0.0),
        (0.0, 108.0, 0.0, 0.0),   # T1 -> level 8
        (0.0, 62.0, 0.0, 0.0),    # T2 -> level 12
    ]
    link_data = [[(5.0, 1.0, 10.0, 0.0, 3.0, 0.0, 0.0, 0.02)]] * 2
    data = build_epanet_out(
        node_ids=node_ids,
        link_ids=["P1"],
        link_from=[0],
        link_to=[1],
        link_types=[1],
        tank_node_indices=[0, 2, 3],
        tank_areas=[0.0, math.pi, 2.0],
        node_elevations=[200.0, 50.0, 100.0, 50.0],
        link_lengths=[1000.0],
        link_diameters=[300.0],
        periods_node_data=[p0, p1],
        periods_link_data=link_data,
    )
    out_path = tmp_path / "tanks.out"
    out_path.write_bytes(data)
    return str(out_path)


class TestPerTankVolumeFromOut:
    def test_each_tank_volume_series(self, tmp_path):
        out_path = _tank_network_out(tmp_path)
        assert getOut_TimesTankVolume(out_path, "", "Net", "T1") == pytest.approx(
            [math.pi * 5.0, math.pi * 8.0]
        )
        assert getOut_TimesTankVolume(out_path, "", "Net", "T2") == pytest.approx([20.0, 24.0])

    def test_reservoir_and_unknown_return_empty(self, tmp_path):
        out_path = _tank_network_out(tmp_path)
        assert getOut_TimesTankVolume(out_path, "", "Net", "R1") == []
        assert getOut_TimesTankVolume(out_path, "", "Net", "ZZ") == []

    def test_missing_file_returns_empty(self):
        assert getOut_TimesTankVolume("/no/such/file.out", "", "Net", "T1") == []
        assert getOut_TimesTankSpill("/no/such/file.out", "", "Net", "T1") == []

    def test_spill_zero_without_overflow_dbf(self, tmp_path):
        # No project DBF -> overflow disabled -> flat zero series (still per-period).
        out_path = _tank_network_out(tmp_path)
        assert getOut_TimesTankSpill(out_path, "", "Net", "T1") == [0.0, 0.0]
        assert getOut_TimesTankSpill(out_path, "", "Net", "R1") == []
