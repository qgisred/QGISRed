# -*- coding: utf-8 -*-
import pytest

from QGISRed.ui.analysis.timeseries_globals import (
    TOTAL_STORED_VOLUME_DISPLAY_DECIMALS,
    TOTAL_STORED_VOLUME_KEY,
    TOTAL_TANK_SPILL_KEY,
    TOTAL_WATER_DEMAND_KEY,
    TOTAL_WATER_SUPPLY_KEY,
    get_global_timeseries,
    global_series_y_display_decimals,
)

from QGISRed.tests.helpers.epanet_out_builder import simple_network_out  # noqa: F401


class TestGetGlobalTimeseries:
    def test_total_water_supply_out(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        ts = get_global_timeseries(source, TOTAL_WATER_SUPPLY_KEY)
        assert len(ts) == 2
        assert ts[0] == pytest.approx(10.0)

    def test_total_water_demand_out(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        ts = get_global_timeseries(source, TOTAL_WATER_DEMAND_KEY)
        assert len(ts) == 2
        assert ts[0] == pytest.approx(10.0)

    def test_total_stored_volume_out(self, monkeypatch):
        expected = [635249.67, 654252.65, 684289.51]

        def fake_total(out_path, project_directory, network_name):
            assert out_path == "net.out"
            assert project_directory == "/proj"
            assert network_name == "Net"
            return list(expected)

        monkeypatch.setattr(
            "QGISRed.ui.analysis.timeseries_globals.getOut_TimesTotalStoredVolume",
            fake_total,
        )
        source = {
            "kind": "out",
            "out_path": "net.out",
            "project_directory": "/proj",
            "network_name": "Net",
        }
        assert get_global_timeseries(source, TOTAL_STORED_VOLUME_KEY) == expected

    def test_total_tank_spill_out(self, monkeypatch):
        expected = [0.0, 12.5, 8.0]

        def fake_spill(out_path, project_directory, network_name):
            assert out_path == "net.out"
            assert project_directory == "/proj"
            assert network_name == "Net"
            return list(expected)

        monkeypatch.setattr(
            "QGISRed.ui.analysis.timeseries_globals.getOut_TimesTotalTankSpill",
            fake_spill,
        )
        source = {
            "kind": "out",
            "out_path": "net.out",
            "project_directory": "/proj",
            "network_name": "Net",
        }
        assert get_global_timeseries(source, TOTAL_TANK_SPILL_KEY) == expected

    def test_unknown_variable(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        assert get_global_timeseries(source, "Unknown") == []


class TestGlobalSeriesDisplayDecimals:
    def test_stored_volume_uses_two_decimals(self):
        assert global_series_y_display_decimals(TOTAL_STORED_VOLUME_KEY) == 2
        assert TOTAL_STORED_VOLUME_DISPLAY_DECIMALS == 2

    def test_other_globals_use_csv_defaults(self):
        assert global_series_y_display_decimals(TOTAL_WATER_SUPPLY_KEY) is None
