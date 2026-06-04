# -*- coding: utf-8 -*-
import math

import pytest

from QGISRed.ui.analysis.qgisred_tank_storage import (
    _tank_area_from_diameter,
    _tank_diameter_dbf_to_model_length,
    cylindrical_volume_from_level,
    getOut_TimesTankStoredVolumes,
    interpolate_volume_curve,
    total_stored_volume_from_tank_rows,
    volume_from_level,
)


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
    """Regression from manual EPANET check (SI, diameter in metres)."""

    TANKS = (
        ("tank1", [145.00, 145.65, 147.06], 131.90, 0.1, 0.0, 85.0),
        ("tank2", [140.00, 138.655, 137.398], 116.50, 6.5, 0.0, 50.0),
        ("tank3", [158.00, 158.85, 160.01], 129.00, 4.0, 0.0, 164.0),
    )
    QGIS_TOTALS = (635249.66, 654318.46, 684211.27)

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

    def test_hour_zero_matches_qgis_display(self):
        assert self._expected_total(0) == pytest.approx(self.QGIS_TOTALS[0], rel=1e-5)


class TestGetOutTimesTankStoredVolumes:
    def test_missing_out_returns_empty(self):
        assert getOut_TimesTankStoredVolumes("/no/such/file.out", "", "Net") == []
