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
    getOut_TimesLinkProperty,
    getOut_StatNodesProperties,
    getOut_StatLinksProperties,
    ROUNDING_PRECISION,
)

from .helpers.epanet_out_builder import simple_network_out, pump_valve_network_out



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
        assert j1["Demand"] == round(5.0, ROUNDING_PRECISION)
        assert j1["Head"] == round(80.0, ROUNDING_PRECISION)
        assert j1["Pressure"] == round(29.43, ROUNDING_PRECISION)
        assert j1["Quality"] == round(0.5, ROUNDING_PRECISION)

    def test_node_properties_period1(self, simple_network_out):
        results = getOut_TimeNodesProperties(simple_network_out, 3600)
        j1 = results["J1"]
        assert j1["Demand"] == round(6.0, ROUNDING_PRECISION)
        assert j1["Head"] == round(75.0, ROUNDING_PRECISION)

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
        assert p1["Flow"] == round(10.0, ROUNDING_PRECISION)
        assert p1["Velocity"] == round(1.5, ROUNDING_PRECISION)
        assert p1["Quality"] == round(0.4, ROUNDING_PRECISION)
        assert p1["Status"] == "Open"

    def test_headloss_calculated_from_unit_headloss(self, simple_network_out):
        results = getOut_TimeLinksProperties(simple_network_out, 0)
        p1 = results["P1"]
        # HeadLoss = unit_headloss * length / 1000 = 20.0 * 1000 / 1000 = 20.0
        assert p1["HeadLoss"] == round(20.0, ROUNDING_PRECISION)
        # UnitHdLoss should be the raw unit headloss
        assert p1["UnitHdLoss"] == round(20.0, ROUNDING_PRECISION)

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
        assert pu1["HeadLoss"] == round(20.0, ROUNDING_PRECISION)

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
        assert result["Demand"] == round(5.0, ROUNDING_PRECISION)
        assert result["Head"] == round(80.0, ROUNDING_PRECISION)
        assert result["Pressure"] == round(29.43, ROUNDING_PRECISION)
        assert result["Quality"] == round(0.5, ROUNDING_PRECISION)

    def test_node_not_found(self, simple_network_out):
        result = getOut_TimeNodeProperties(simple_network_out, 0, "NONEXISTENT")
        assert result == {}

    def test_nonexistent_file(self):
        result = getOut_TimeNodeProperties("/nonexistent/file.out", 0, "J1")
        assert result == {}


class TestGetOutTimeLinkProperties:
    def test_specific_link(self, simple_network_out):
        result = getOut_TimeLinkProperties(simple_network_out, 0, "P1")
        assert result["Flow"] == round(10.0, ROUNDING_PRECISION)
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
        assert ts[0] == round(29.43, ROUNDING_PRECISION)
        assert ts[1] == round(24.52, ROUNDING_PRECISION)

    def test_demand_timeseries(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "J1", "Demand")
        assert len(ts) == 2
        assert ts[0] == round(5.0, ROUNDING_PRECISION)
        assert ts[1] == round(6.0, ROUNDING_PRECISION)

    def test_invalid_property(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "J1", "InvalidProp")
        assert ts == []

    def test_invalid_node(self, simple_network_out):
        ts = getOut_TimesNodeProperty(simple_network_out, "NONEXISTENT", "Pressure")
        assert ts == []


class TestGetOutTimesLinkProperty:
    def test_flow_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "Flow")
        assert len(ts) == 2
        assert ts[0] == round(10.0, ROUNDING_PRECISION)
        assert ts[1] == round(12.0, ROUNDING_PRECISION)

    def test_velocity_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "Velocity")
        assert len(ts) == 2
        assert ts[0] == round(1.5, ROUNDING_PRECISION)
        assert ts[1] == round(1.8, ROUNDING_PRECISION)

    def test_headloss_timeseries(self, simple_network_out):
        ts = getOut_TimesLinkProperty(simple_network_out, "P1", "HeadLoss")
        assert len(ts) == 2
        # HeadLoss = unit_headloss * length / 1000
        assert ts[0] == round(20.0 * 1000.0 / 1000.0, ROUNDING_PRECISION)
        assert ts[1] == round(25.0 * 1000.0 / 1000.0, ROUNDING_PRECISION)

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
        assert j1["Head"]["Value"] == round(80.0, ROUNDING_PRECISION)
        assert j1["Head"]["Time"] == 0
        # Demand max: period0=5, period1=6 → max=6 at time=3600
        assert j1["Demand"]["Value"] == round(6.0, ROUNDING_PRECISION)
        assert j1["Demand"]["Time"] == 3600

    def test_minimum(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Minimum")
        j1 = results["J1"]
        assert j1["Head"]["Value"] == round(75.0, ROUNDING_PRECISION)
        assert j1["Head"]["Time"] == 3600
        assert j1["Demand"]["Value"] == round(5.0, ROUNDING_PRECISION)
        assert j1["Demand"]["Time"] == 0

    def test_average(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Average")
        j1 = results["J1"]
        # Head average: (80 + 75) / 2 = 77.5
        assert j1["Head"]["Value"] == round(77.5, ROUNDING_PRECISION)
        # Demand average: (5 + 6) / 2 = 5.5
        assert j1["Demand"]["Value"] == round(5.5, ROUNDING_PRECISION)

    def test_range(self, simple_network_out):
        results = getOut_StatNodesProperties(simple_network_out, "Range")
        j1 = results["J1"]
        assert j1["Head"]["Value"] == round(80.0 - 75.0, ROUNDING_PRECISION)
        assert j1["Demand"]["Value"] == round(6.0 - 5.0, ROUNDING_PRECISION)

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
        assert p1["Flow"]["Value"] == round(12.0, ROUNDING_PRECISION)
        assert p1["Flow"]["Time"] == 3600

    def test_minimum(self, simple_network_out):
        results = getOut_StatLinksProperties(simple_network_out, "Minimum")
        p1 = results["P1"]
        assert p1["Flow"]["Value"] == round(10.0, ROUNDING_PRECISION)
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
