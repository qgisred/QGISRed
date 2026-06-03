# -*- coding: utf-8 -*-
import pytest

from QGISRed.ui.analysis.timeseries_globals import (
    TOTAL_WATER_DEMAND_KEY,
    TOTAL_WATER_SUPPLY_KEY,
    get_global_timeseries,
)

from .helpers.epanet_out_builder import simple_network_out  # noqa: F401 — pytest fixture


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

    def test_unknown_variable(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        assert get_global_timeseries(source, "Unknown") == []
