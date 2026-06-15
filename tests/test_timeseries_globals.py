# -*- coding: utf-8 -*-
import pytest

from QGISRed.ui.analysis.timeseries_globals import (
    AVERAGE_NODE_PRESSURE_KEY,
    TOTAL_STORED_VOLUME_DISPLAY_DECIMALS,
    TOTAL_STORED_VOLUME_KEY,
    TOTAL_TANK_SPILL_KEY,
    TOTAL_WATER_DEMAND_KEY,
    TOTAL_WATER_SUPPLY_KEY,
    get_global_timeseries,
    global_series_y_display_decimals,
    global_variable_key_from_series_key,
    global_variable_short_label,
    global_variable_table_column_label,
    global_variable_unit_abbreviation,
    stored_volume_display_factor,
)
from QGISRed.ui.analysis.qgisred_results_binary import (
    _NT_JUNCTION,
    _NT_RESERVOIR,
    _NT_TANK,
    average_junction_pressure,
    getOut_TimesAverageNodePressure,
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

    def test_average_node_pressure_excludes_reservoir_and_tank(self):
        pressures = [0.0, 30.0, 20.0, 40.0]
        node_types = [_NT_RESERVOIR, _NT_JUNCTION, _NT_JUNCTION, _NT_TANK]
        assert average_junction_pressure(pressures, node_types) == pytest.approx(25.0)

    def test_average_node_pressure_out(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        ts = get_global_timeseries(source, AVERAGE_NODE_PRESSURE_KEY)
        assert len(ts) == 2
        assert ts[0] == pytest.approx(29.43)
        assert ts[1] == pytest.approx(24.52)
        assert getOut_TimesAverageNodePressure(simple_network_out) == ts

    def test_unknown_variable(self, simple_network_out):
        source = {"kind": "out", "out_path": simple_network_out}
        assert get_global_timeseries(source, "Unknown") == []


def _patch_timeseries_globals_tr(monkeypatch):
    monkeypatch.setattr(
        "QGISRed.ui.analysis.timeseries_globals.tr",
        lambda message, *_args, **_kwargs: message,
    )


class TestGlobalTableColumnLabels:
    @pytest.fixture(autouse=True)
    def _identity_tr(self, monkeypatch):
        _patch_timeseries_globals_tr(monkeypatch)

    def test_key_from_series_key(self):
        assert global_variable_key_from_series_key(
            "Global:global:TotalWaterSupply:TotalWaterSupply",
        ) == TOTAL_WATER_SUPPLY_KEY

    def test_table_column_label(self, monkeypatch):
        monkeypatch.setattr(
            "QGISRed.ui.analysis.timeseries_globals.global_variable_unit_abbreviation",
            lambda _key: "gpm",
        )
        assert global_variable_table_column_label(TOTAL_WATER_SUPPLY_KEY) == "Supply (gpm)"
        assert global_variable_table_column_label(TOTAL_WATER_DEMAND_KEY) == "Demand (gpm)"

    def test_short_labels(self):
        assert global_variable_short_label(TOTAL_WATER_SUPPLY_KEY) == "Supply"
        assert global_variable_short_label(TOTAL_TANK_SPILL_KEY) == "Spill"


class TestGlobalSeriesDisplayDecimals:
    def test_stored_volume_uses_two_decimals(self):
        assert global_series_y_display_decimals(TOTAL_STORED_VOLUME_KEY) == 2
        assert TOTAL_STORED_VOLUME_DISPLAY_DECIMALS == 2

    def test_other_globals_use_csv_defaults(self):
        assert global_series_y_display_decimals(TOTAL_WATER_SUPPLY_KEY) is None


def _patch_project_units(monkeypatch, units, flow_unit):
    monkeypatch.setattr(
        "QGISRed.tools.utils.qgisred_project_utils.QGISRedProjectUtils.getUnits",
        lambda: units,
    )
    monkeypatch.setattr(
        "QGISRed.tools.utils.qgisred_project_utils.QGISRedProjectUtils.getFlowUnit",
        lambda: flow_unit,
    )


class TestStoredVolumeDisplayUnits:
    """Stored volume mirrors EPANET-UI: MG/MGI for US flow units, m³ for SI."""

    def test_us_flow_units_use_million_us_gallons(self, monkeypatch):
        _patch_project_units(monkeypatch, "US", "GPM")
        assert global_variable_unit_abbreviation(TOTAL_STORED_VOLUME_KEY) == "MG"
        # 1 MG = 1e6 US gal = 1e6 * 231/1728 ft³
        assert stored_volume_display_factor() == pytest.approx(1728.0 / (231.0 * 1.0e6))

    def test_imperial_flow_unit_uses_million_imperial_gallons(self, monkeypatch):
        _patch_project_units(monkeypatch, "US", "IMGD")
        assert global_variable_unit_abbreviation(TOTAL_STORED_VOLUME_KEY) == "MGI"
        # 1 MGI = 1e6 imp gal = 1e6 * 4.54609 L / 28.316846592 L-per-ft³
        assert stored_volume_display_factor() == pytest.approx(28.316846592 / (4.54609 * 1.0e6))

    def test_si_flow_units_keep_cubic_meters(self, monkeypatch):
        _patch_project_units(monkeypatch, "SI", "LPS")
        monkeypatch.setattr(
            "QGISRed.tools.utils.qgisred_field_utils.QGISRedFieldUtils.getUnitAbbreviation",
            lambda self, element, field, conditionFeature="": "m3",
        )
        assert global_variable_unit_abbreviation(TOTAL_STORED_VOLUME_KEY) == "m3"
        assert stored_volume_display_factor() == 1.0

    def test_stored_volume_series_converted_to_mg_for_us_projects(self, monkeypatch):
        _patch_project_units(monkeypatch, "US", "GPM")
        ft3_per_mg = 1.0e6 * 231.0 / 1728.0
        monkeypatch.setattr(
            "QGISRed.ui.analysis.timeseries_globals.getOut_TimesTotalStoredVolume",
            lambda *_a, **_k: [ft3_per_mg, 2.0 * ft3_per_mg],
        )
        source = {"kind": "out", "out_path": "net.out", "project_directory": "/p", "network_name": "N"}
        assert get_global_timeseries(source, TOTAL_STORED_VOLUME_KEY) == pytest.approx([1.0, 2.0])

    def test_stored_volume_series_unchanged_for_si_projects(self, monkeypatch):
        _patch_project_units(monkeypatch, "SI", "LPS")
        monkeypatch.setattr(
            "QGISRed.ui.analysis.timeseries_globals.getOut_TimesTotalStoredVolume",
            lambda *_a, **_k: [635249.67, 654252.65],
        )
        source = {"kind": "out", "out_path": "net.out", "project_directory": "/p", "network_name": "N"}
        assert get_global_timeseries(source, TOTAL_STORED_VOLUME_KEY) == [635249.67, 654252.65]
