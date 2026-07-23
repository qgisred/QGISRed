# -*- coding: utf-8 -*-
"""Tests for tools/qgisred_results.py — the EPANET binary (.out) parser."""
import io
import struct
import os
import sys
import pytest

from QGISRed.ui.analysis.qgisred_results_binary import (
    getOut_Metadata,
    getOut_TimeNodesProperties,
    getOut_TimeLinksProperties,
    getOut_TimeNodeProperties,
    getOut_TimeLinkProperties,
    getOut_TimesNodeProperty,
    getOut_TimesTotalWaterSupply,
    getOut_TimesTotalWaterDemand,
    getOut_TimesLinkProperty,
    total_water_demand_from_demands,
    total_water_supply_from_demands,
    getOut_StatNodesProperties,
    getOut_StatLinksProperties,
)
from QGISRed.ui.analysis.qgisred_results_hyd import (
    getHyd_Metadata,
    getHyd_TimeNodesProperties,
    getHyd_TimeLinksProperties,
    getHyd_StatNodesProperties,
    getHyd_StatLinksProperties,
)

from .helpers.epanet_out_builder import simple_network_out, pump_valve_network_out, simple_network_out_with_trailing
from .helpers.epanet_hyd_builder import build_epanet_hyd


# ═══════════════════════════════════════════════════════════════════════
# 1. getOut_Metadata — Binary header parsing
# ═══════════════════════════════════════════════════════════════════════

class TestGetOutMetadata:
    def test_parses_simple_network(self, simple_network_out):
        with open(simple_network_out, 'rb') as f:
            meta = getOut_Metadata(f)

        assert meta is not None
        assert meta["n_nodes"] == 3
        assert meta["n_links"] == 2
        assert meta["n_tanks"] == 1
        assert meta["num_periods"] == 2
        assert meta["report_start"] == 0
        assert meta["report_step"] == 3600
        assert meta["node_ids"] == ["R1", "J1", "J2"]
        assert meta["link_ids"] == ["P1", "P2"]
        assert meta["link_from"] == [0, 1]
        assert meta["link_to"] == [1, 2]
        assert list(meta["link_types"]) == [1, 1]

    def test_node_types_reservoir(self, simple_network_out):
        with open(simple_network_out, 'rb') as f:
            meta = getOut_Metadata(f)

        # R1 (idx 0) should be reservoir (area = 0)
        assert meta["node_types"][0] == 1  # _NT_RESERVOIR
        # J1, J2 should be junction
        assert meta["node_types"][1] == 0  # _NT_JUNCTION
        assert meta["node_types"][2] == 0

    def test_include_lengths(self, simple_network_out):
        with open(simple_network_out, 'rb') as f:
            meta = getOut_Metadata(f, include_lengths=True)
        assert meta["link_lengths"] is not None
        assert len(meta["link_lengths"]) == 2
        assert abs(meta["link_lengths"][0] - 1000.0) < 1
        assert abs(meta["link_lengths"][1] - 500.0) < 1

    def test_without_lengths(self, simple_network_out):
        with open(simple_network_out, 'rb') as f:
            meta = getOut_Metadata(f, include_lengths=False)
        assert meta["link_lengths"] is None

    def test_invalid_file(self, tmp_path):
        bad_file = tmp_path / "bad.out"
        bad_file.write_bytes(b'\x00' * 100)
        with open(str(bad_file), 'rb') as f:
            meta = getOut_Metadata(f)
        assert meta is None

    def test_too_small_file(self, tmp_path):
        bad_file = tmp_path / "tiny.out"
        bad_file.write_bytes(b'\x00' * 10)
        with open(str(bad_file), 'rb') as f:
            meta = getOut_Metadata(f)
        assert meta is None


# ═══════════════════════════════════════════════════════════════════════
# 5. Full file reading — Nodes and Links at a time step
# ═══════════════════════════════════════════════════════════════════════

class TestGetOutTimeNodesProperties:
    def test_returns_all_nodes(self, simple_network_out):
        results = getOut_TimeNodesProperties(simple_network_out, 0)
        assert len(results) == 3
        assert set(results.keys()) == {"R1", "J1", "J2"}

    def test_node_properties_period0(self, simple_network_out):
        results = getOut_TimeNodesProperties(simple_network_out, 0)
        j1 = results["J1"]
        assert set(j1.keys()) == {"Pressure", "Head", "Demand", "Quality"}
        assert j1["Demand"] == pytest.approx(5.0)
        assert j1["Head"] == pytest.approx(80.0)
        assert j1["Pressure"] == pytest.approx(29.43)
        assert j1["Quality"] == pytest.approx(0.5)

    def test_node_properties_period1(self, simple_network_out):
        results = getOut_TimeNodesProperties(simple_network_out, 3600)
        j1 = results["J1"]
        assert j1["Demand"] == pytest.approx(6.0)
        assert j1["Head"] == pytest.approx(75.0)

    def test_nonexistent_file(self):
        results = getOut_TimeNodesProperties("/nonexistent/file.out", 0)
        assert results == {}


class TestGetOutTimeLinksProperties:
    def test_returns_all_links(self, simple_network_out):
        results = getOut_TimeLinksProperties(simple_network_out, 0)
        assert len(results) == 2
        assert set(results.keys()) == {"P1", "P2"}

    def test_link_properties_period0(self, simple_network_out):
        results = getOut_TimeLinksProperties(simple_network_out, 0)
        p1 = results["P1"]
        assert p1["Flow"] == pytest.approx(10.0)
        assert p1["Velocity"] == pytest.approx(1.5)
        assert p1["Quality"] == pytest.approx(0.4)
        assert p1["Status"] == "Open"

    def test_headloss_calculated_from_unit_headloss(self, simple_network_out):
        results = getOut_TimeLinksProperties(simple_network_out, 0)
        p1 = results["P1"]
        # HeadLoss = unit_headloss * length / 1000 = 20.0 * 1000 / 1000 = 20.0
        assert p1["HeadLoss"] == pytest.approx(20.0)
        # UnitHdLoss should be the raw unit headloss
        assert p1["UnitHdLoss"] == pytest.approx(20.0)

    def test_pump_fields_are_none(self, pump_valve_network_out):
        results = getOut_TimeLinksProperties(pump_valve_network_out, 0)
        pu1 = results["PU1"]
        assert pu1["Velocity"] is None
        assert pu1["UnitHdLoss"] is None
        assert pu1["FricFactor"] is None
        assert pu1["ReactRate"] is None
        # Flow and HeadLoss should still have values
        assert pu1["Flow"] is not None
        assert pu1["HeadLoss"] is not None

    def test_pump_headloss_not_multiplied_by_length(self, pump_valve_network_out):
        results = getOut_TimeLinksProperties(pump_valve_network_out, 0)
        pu1 = results["PU1"]
        # Pumps use raw headloss without length multiplication
        assert pu1["HeadLoss"] == pytest.approx(20.0)

    def test_valve_status_active(self, pump_valve_network_out):
        results = getOut_TimeLinksProperties(pump_valve_network_out, 0)
        v1 = results["V1"]
        # PRV in the fixture is set to Active (status 4)
        assert v1["Status"] == "Active"

    def test_nonexistent_file(self):
        results = getOut_TimeLinksProperties("/nonexistent/file.out", 0)
        assert results == {}


# ═══════════════════════════════════════════════════════════════════════
# 6. Single element reading
# ═══════════════════════════════════════════════════════════════════════

class TestGetOutTimeNodeProperties:
    def test_specific_node(self, simple_network_out):
        result = getOut_TimeNodeProperties(simple_network_out, 0, "J1")
        assert result["Demand"] == pytest.approx(5.0)
        assert result["Head"] == pytest.approx(80.0)
        assert result["Pressure"] == pytest.approx(29.43)
        assert result["Quality"] == pytest.approx(0.5)

    def test_node_not_found(self, simple_network_out):
        result = getOut_TimeNodeProperties(simple_network_out, 0, "NONEXISTENT")
        assert result == {}

    def test_nonexistent_file(self):
        result = getOut_TimeNodeProperties("/nonexistent/file.out", 0, "J1")
        assert result == {}


class TestGetOutTimeLinkProperties:
    def test_specific_link(self, simple_network_out):
        result = getOut_TimeLinkProperties(simple_network_out, 0, "P1")
        assert result["Flow"] == pytest.approx(10.0)
        assert result["Status"] == "Open"

    def test_link_not_found(self, simple_network_out):
        result = getOut_TimeLinkProperties(simple_network_out, 0, "NONEXISTENT")
        assert result == {}

    def test_nonexistent_file(self):
        result = getOut_TimeLinkProperties("/nonexistent/file.out", 0, "P1")
        assert result == {}


# ═══════════════════════════════════════════════════════════════════════
# 7. Time series
# ═══════════════════════════════════════════════════════════════════════

class TestGetOutTimesNodeProperty:
    def test_pressure_timeseries(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "J1", "Pressure")
        assert len(ts) == 2
        assert ts[0] == pytest.approx(29.43)
        assert ts[1] == pytest.approx(24.52)

    def test_demand_timeseries(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "J1", "Demand")
        assert len(ts) == 2
        assert ts[0] == pytest.approx(5.0)
        assert ts[1] == pytest.approx(6.0)

    def test_invalid_property(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "J1", "InvalidProp")
        assert ts == []

    def test_invalid_node(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "NONEXISTENT", "Pressure")
        assert ts == []


class TestTotalWaterSupply:
    def test_from_demands_reservoir_and_junction_inflow(self):
        # R=reservoir, J=junction, T=tank
        node_types = [1, 0, 0, 2]
        demands = [-10.0, -3.0, 5.0, -100.0]
        assert total_water_supply_from_demands(demands, node_types) == pytest.approx(13.0)

    def test_timeseries_simple_network(self, simple_network_out):
        ts = getOut_TimesTotalWaterSupply(simple_network_out)
        assert len(ts) == 2
        assert ts[0] == pytest.approx(10.0)
        assert ts[1] == pytest.approx(12.0)


class TestTotalWaterDemand:
    def test_from_demands_reservoir_and_junction_outflow(self):
        node_types = [1, 0, 0, 2]
        demands = [8.0, -3.0, 5.0, 100.0]
        assert total_water_demand_from_demands(demands, node_types) == pytest.approx(13.0)

    def test_timeseries_simple_network(self, simple_network_out):
        ts = getOut_TimesTotalWaterDemand(simple_network_out)
        assert len(ts) == 2
        assert ts[0] == pytest.approx(10.0)
        assert ts[1] == pytest.approx(12.0)


class TestGetOutTimesLinkProperty:
    def test_flow_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "Flow")
        assert len(ts) == 2
        assert ts[0] == pytest.approx(10.0)
        assert ts[1] == pytest.approx(12.0)

    def test_velocity_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "Velocity")
        assert len(ts) == 2
        assert ts[0] == pytest.approx(1.5)
        assert ts[1] == pytest.approx(1.8)

    def test_headloss_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "HeadLoss")
        assert len(ts) == 2
        # HeadLoss = unit_headloss * length / 1000
        assert ts[0] == pytest.approx(20.0 * 1000.0 / 1000.0)
        assert ts[1] == pytest.approx(25.0 * 1000.0 / 1000.0)

    def test_status_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "Status")
        assert len(ts) == 2
        assert ts[0] == "Open"
        assert ts[1] == "Open"

    def test_pump_velocity_returns_none(self, pump_valve_network_out):
        ts = getOut_TimesLinkProperty(pump_valve_network_out, "PU1", "Velocity")
        assert all(v is None for v in ts)

    def test_invalid_link(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "NONEXISTENT", "Flow")
        assert ts == []


# ═══════════════════════════════════════════════════════════════════════
# 8. Statistics across time
# ═══════════════════════════════════════════════════════════════════════

class TestGetOutStatNodesProperties:
    def test_maximum(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Maximum")
        assert "J1" in results
        j1 = results["J1"]
        # Head max: period0=80, period1=75 → max=80 at time=0
        assert j1["Head"]["Value"] == pytest.approx(80.0)
        assert j1["Head"]["Time"] == 0
        # Demand max: period0=5, period1=6 → max=6 at time=3600
        assert j1["Demand"]["Value"] == pytest.approx(6.0)
        assert j1["Demand"]["Time"] == 3600

    def test_minimum(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Minimum")
        j1 = results["J1"]
        assert j1["Head"]["Value"] == pytest.approx(75.0)
        assert j1["Head"]["Time"] == 3600
        assert j1["Demand"]["Value"] == pytest.approx(5.0)
        assert j1["Demand"]["Time"] == 0

    def test_average(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Average")
        j1 = results["J1"]
        # Head average: (80 + 75) / 2 = 77.5
        assert j1["Head"]["Value"] == pytest.approx(77.5)
        # Demand average: (5 + 6) / 2 = 5.5
        assert j1["Demand"]["Value"] == pytest.approx(5.5)

    def test_range(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Range")
        j1 = results["J1"]
        assert j1["Head"]["Value"] == pytest.approx(80.0 - 75.0)
        assert j1["Demand"]["Value"] == pytest.approx(6.0 - 5.0)

    def test_stddev(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "StdDev")
        j1 = results["J1"]
        # Population stddev of [80, 75] = sqrt(((80-77.5)^2 + (75-77.5)^2) / 2) = 2.5
        assert abs(j1["Head"]["Value"] - 2.5) < 0.01

    def test_invalid_stat_raises(self, simple_network_out):
        with pytest.raises(ValueError):
            getOut_StatNodesProperties(simple_network_out, "InvalidStat")

    def test_nonexistent_file(self):
        results = getOut_StatNodesProperties("/nonexistent/file.out", "Maximum")
        assert results == {}


class TestGetOutStatLinksProperties:
    def test_maximum(self, simple_network_out):
        results = getOut_StatLinksProperties(simple_network_out, "Maximum")
        assert "P1" in results
        p1 = results["P1"]
        # Flow max: abs(10) vs abs(12) → max |flow|=12 at time=3600
        assert p1["Flow"]["Value"] == pytest.approx(12.0)
        assert p1["Flow"]["Time"] == 3600

    def test_minimum(self, simple_network_out):
        results = getOut_StatLinksProperties(simple_network_out, "Minimum")
        p1 = results["P1"]
        assert p1["Flow"]["Value"] == pytest.approx(10.0)
        assert p1["Flow"]["Time"] == 0

    def test_average(self, simple_network_out):
        results = getOut_StatLinksProperties(simple_network_out, "Average")
        p1 = results["P1"]
        # Average uses abs for unsigned flow and signed for signed
        assert "Flow_Unsig" in p1
        assert "Flow_Sig" in p1

    def test_status_excluded(self, simple_network_out):
        results = getOut_StatLinksProperties(simple_network_out, "Maximum")
        p1 = results["P1"]
        # Status is categorical, should not be in results
        assert "Status" not in p1

    def test_invalid_stat_raises(self, simple_network_out):
        with pytest.raises(ValueError):
            getOut_StatLinksProperties(simple_network_out, "BadStat")


# ═══════════════════════════════════════════════════════════════════════
# 9. Trailing-bytes robustness
#    Regression for the bug where period_size was derived from file size
#    instead of network dimensions. Real EPANET binaries (e.g. 2.2) can
#    append extra summary bytes before the epilogue, causing the file-size
#    formula to overestimate period_size by 1 byte and byte-drift every
#    period past index 0 (producing garbage / negative pressure values).
# ═══════════════════════════════════════════════════════════════════════

class TestTrailingBytesRobustness:
    def test_period0_correct_with_trailing(self, simple_network_out_with_trailing):
        """Period 0 must read correctly regardless of trailing bytes."""
        results = getOut_TimeNodesProperties(simple_network_out_with_trailing, 0)
        j1 = results["J1"]
        assert j1["Pressure"] == pytest.approx(29.43)
        assert j1["Head"]     == pytest.approx(80.0)
        assert j1["Demand"]   == pytest.approx(5.0)

    def test_period1_correct_with_trailing(self, simple_network_out_with_trailing):
        """Period 1 must read the correct values even when extra bytes follow
        the last period. Without the fix (file-size-based period_size) this
        period starts 1 byte off, producing garbage floats."""
        results = getOut_TimeNodesProperties(simple_network_out_with_trailing, 3600)
        j1 = results["J1"]
        assert j1["Pressure"] == pytest.approx(24.52)
        assert j1["Head"]     == pytest.approx(75.0)
        assert j1["Demand"]   == pytest.approx(6.0)

    def test_no_negative_pressures_with_trailing(self, simple_network_out_with_trailing):
        """No junction should report a negative pressure in any period."""
        for t in (0, 3600):
            results = getOut_TimeNodesProperties(simple_network_out_with_trailing, t)
            for node_id, props in results.items():
                assert props["Pressure"] >= 0.0, (
                    f"Negative pressure {props['Pressure']} for {node_id} at t={t}s"
                )


@pytest.fixture
def simple_network_hyd(tmp_path):
    periods = [
        {
            "time": 0,
            "step": 1800,
            "demands": [-10.0, 5.0, 5.0],
            "heads": [100.0, 80.0, 60.0],
            "flows": [10.0, 5.0],
            "statuses": [3.0, 3.0],
            "settings": [0.0, 0.0],
        },
        {
            "time": 1800,
            "step": 1800,
            "demands": [-11.0, 5.5, 5.5],
            "heads": [100.0, 77.0, 57.0],
            "flows": [11.0, 5.5],
            "statuses": [3.0, 3.0],
            "settings": [0.0, 0.0],
        },
        {
            "time": 3600,
            "step": 1800,
            "demands": [-12.0, 6.0, 6.0],
            "heads": [100.0, 75.0, 55.0],
            "flows": [12.0, 6.0],
            "statuses": [3.0, 3.0],
            "settings": [0.0, 0.0],
        },
    ]
    hyd_path = tmp_path / "test_network.hyd"
    hyd_path.write_bytes(build_epanet_hyd(periods, n_nodes=3, n_links=2, n_tanks=1, duration=3600))
    return str(hyd_path)


@pytest.fixture
def pump_valve_network_hyd(tmp_path):
    periods = [
        {
            "time": 0,
            "step": 3600,
            "demands": [-20.0, 10.0, 10.0],
            "heads": [100.0, 80.0, 60.0],
            "flows": [20.0, 10.0],
            "statuses": [3.0, 4.0],
            "settings": [1.0, 40.0],
        }
    ]
    hyd_path = tmp_path / "pump_valve_network.hyd"
    hyd_path.write_bytes(build_epanet_hyd(periods, n_nodes=3, n_links=2, n_tanks=1, n_pumps=1, n_valves=1, duration=0))
    return str(hyd_path)


class TestHydResults:
    def test_hyd_metadata_uses_out_topology(self, simple_network_out, simple_network_hyd):
        meta = getHyd_Metadata(simple_network_hyd, simple_network_out)
        assert meta is not None
        assert meta["n_nodes"] == 3
        assert meta["n_links"] == 2
        assert meta["hyd_num_periods"] == 3
        assert meta["hyd_report_step"] == 1800

    def test_hyd_nodes_pressure_calculated(self, simple_network_out, simple_network_hyd):
        # Middle hydraulic step should be available from .hyd
        results = getHyd_TimeNodesProperties(simple_network_hyd, simple_network_out, 1800)
        j1 = results["J1"]
        with open(simple_network_out, "rb") as f:
            out_meta = getOut_Metadata(f)
        flow_units = out_meta["flow_units"]
        pres_units = out_meta["pres_units"]
        is_metric = flow_units >= 5
        head_factor = 0.3048 if is_metric else 1.0
        if pres_units == 0:
            pressure_factor = 1.422334 if is_metric else 0.4333
        elif pres_units == 1:
            pressure_factor = 9.80665 if is_metric else 2.98898
        else:
            pressure_factor = 1.0

        assert j1["Demand"] == pytest.approx(5.5)
        assert j1["Head"] == pytest.approx(77.0 * head_factor)
        # Pressure = (head - elevation) converted to project pressure units.
        assert j1["Pressure"] == pytest.approx((77.0 * head_factor - 50.0) * pressure_factor)
        assert j1["Quality"] is None

    def test_hyd_links_derived_values(self, simple_network_out, simple_network_hyd):
        results = getHyd_TimeLinksProperties(simple_network_hyd, simple_network_out, 1800)
        p1 = results["P1"]
        with open(simple_network_out, "rb") as f:
            out_meta = getOut_Metadata(f, include_lengths=True, include_geometry=True)
        flow_units = out_meta["flow_units"]
        is_metric = flow_units >= 5
        cfs_to_flow = {
            0: 1.0, 1: 448.8311688, 2: 0.646317, 3: 0.5382, 4: 1.98347,
            5: 28.3168466, 6: 1699.0108, 7: 2.446575, 8: 101.940647, 9: 2446.57553,
        }
        flow_factor = cfs_to_flow.get(flow_units, 1.0)
        head_factor = 0.3048 if is_metric else 1.0
        expected_headloss = (100.0 - 77.0) * head_factor
        expected_unit = (expected_headloss * 1000.0) / 1000.0

        raw_flow_cfs = 11.0
        expected_flow = raw_flow_cfs * flow_factor

        diameter_raw = out_meta["link_diameters"][0]
        if is_metric:
            diameter_m = diameter_raw / 1000.0
            area = 3.141592653589793 * (diameter_m ** 2) / 4.0
            expected_velocity = abs(raw_flow_cfs * 0.0283168466) / area
            length_m = out_meta["link_lengths"][0]
            slope = expected_headloss / length_m
        else:
            diameter_ft = diameter_raw / 12.0
            area = 3.141592653589793 * (diameter_ft ** 2) / 4.0
            expected_velocity = abs(raw_flow_cfs) / area
            diameter_m = diameter_raw * 0.0254
            length_ft = out_meta["link_lengths"][0]
            slope = (expected_headloss * 0.3048) / (length_ft * 0.3048)

        q_m3s = raw_flow_cfs * 0.0283168466
        expected_f = 12.104 * (diameter_m ** 5) * slope / (q_m3s ** 2)

        assert p1["Status"] == "Open"
        assert p1["Flow"] == pytest.approx(expected_flow)
        assert p1["HeadLoss"] == pytest.approx(expected_headloss)
        assert p1["UnitHdLoss"] == pytest.approx(expected_unit)
        assert p1["Velocity"] == pytest.approx(expected_velocity)
        assert p1["FricFactor"] == pytest.approx(expected_f)
        assert p1["ReactRate"] is None
        assert p1["Quality"] is None

    def test_hyd_pump_and_valve_keep_blank_fields(self, pump_valve_network_out, pump_valve_network_hyd):
        results = getHyd_TimeLinksProperties(pump_valve_network_hyd, pump_valve_network_out, 0)
        pump = results["PU1"]
        valve = results["V1"]

        assert pump["Velocity"] is None
        assert pump["UnitHdLoss"] is None
        assert pump["FricFactor"] is None
        assert valve["Velocity"] is None
        assert valve["UnitHdLoss"] is None
        assert valve["FricFactor"] is None

    def test_hyd_node_stats_average(self, simple_network_out, simple_network_hyd):
        stats = getHyd_StatNodesProperties(simple_network_hyd, simple_network_out, "Average")
        assert "J1" in stats
        j1 = stats["J1"]
        assert "Head" in j1 and "Demand" in j1 and "Pressure" in j1
        # Average Demand over 3 records: (5.0 + 5.5 + 6.0)/3
        assert j1["Demand"]["Value"] == pytest.approx((5.0 + 5.5 + 6.0) / 3.0)

    def test_hyd_link_stats_maximum(self, simple_network_out, simple_network_hyd):
        stats = getHyd_StatLinksProperties(simple_network_hyd, simple_network_out, "Maximum")
        assert "P1" in stats
        p1 = stats["P1"]
        assert "Flow" in p1
        # Max |Q| occurs at last record (12.0 in fixture)
        assert p1["Flow"]["Value"] == pytest.approx(12.0)
        assert p1["Flow"]["Time"] == 3600

