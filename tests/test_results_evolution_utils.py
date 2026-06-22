# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.results_evolution_utils import (
    evolution_prop_internal,
    map_status_series,
    results_time_text_to_hours,
    tank_buttons_visibility,
)


class TestEvolutionPropInternal:
    def test_signed_and_unsigned_flow_map_to_flow(self):
        assert evolution_prop_internal("Link", "Flow_Sig") == "Flow"
        assert evolution_prop_internal("Link", "Flow_Unsig") == "Flow"

    def test_other_fields_pass_through(self):
        assert evolution_prop_internal("Node", "Pressure") == "Pressure"
        assert evolution_prop_internal("Link", "Velocity") == "Velocity"
        assert evolution_prop_internal("Link", "Status") == "Status"

    def test_empty_field(self):
        assert evolution_prop_internal("Node", "") == ""
        assert evolution_prop_internal("Node", None) == ""


class TestMapStatusSeries:
    def test_status_levels(self):
        values = ["CLOSED", "Active", "open", "XFCV Active", "Unknown"]
        assert map_status_series(values) == [0, 1, 2, 1, 0]

    def test_empty(self):
        assert map_status_series([]) == []


class TestTankButtonsVisibility:
    def test_tank_pressure_shows_volume(self):
        assert tank_buttons_visibility("qgisred_tanks", "Pressure") == (True, False)

    def test_tank_demand_shows_spill(self):
        assert tank_buttons_visibility("qgisred_tanks", "Demand") == (False, True)

    def test_tank_other_variable_hides_both(self):
        assert tank_buttons_visibility("qgisred_tanks", "Head") == (False, False)

    def test_non_tank_hides_both(self):
        assert tank_buttons_visibility("qgisred_junctions", "Pressure") == (False, False)
        assert tank_buttons_visibility("qgisred_reservoirs", "Demand") == (False, False)


class TestResultsTimeTextToHours:
    def test_hms(self):
        assert results_time_text_to_hours("1:30:00") == 1.5
        assert results_time_text_to_hours("2:00") == 2.0

    def test_with_days(self):
        assert results_time_text_to_hours("1d 2:00:00") == 26.0

    def test_single_period_and_empty(self):
        assert results_time_text_to_hours("Single Period", "Single Period") == 0.0
        assert results_time_text_to_hours("") == 0.0

    def test_unparseable(self):
        assert results_time_text_to_hours("not-a-time") is None
