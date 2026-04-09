# -*- coding: utf-8 -*-
"""Tests for unit-extraction logic in QGISRedFieldUtils.

All QGIS dependencies are mocked via conftest.py.  QgsProject.instance()
is patched per-test to simulate different project settings (flow units,
concentration units, etc.) without requiring a running QGIS instance.
"""
import pytest
from unittest.mock import MagicMock, patch

from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils


# ---------------------------------------------------------------------------
# Helper: build a minimal mock for QgsProject.instance().readEntry()
# ---------------------------------------------------------------------------
def _make_project(flow_unit="LPS", concentration_units="mg/L", quality_model="Chemical"):
    """Return a mock QgsProject that answers readEntry for the keys we care about."""
    proj = MagicMock()

    def read_entry(section, key, default=""):
        if section == "QGISRed" and key == "project_units":
            return flow_unit, True
        if section == "QGISRed" and key == "project_concentrationunits":
            return concentration_units, True
        if section == "QGISRed" and key == "project_qualitymodel":
            return quality_model, True
        return default, False

    proj.readEntry.side_effect = read_entry
    return proj


# ---------------------------------------------------------------------------
# Fixture: fresh FieldUtils instance (cache cleared before each test)
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure the unit-definitions cache is cleared between tests."""
    QGISRedFieldUtils._unit_definitions = None
    yield
    QGISRedFieldUtils._unit_definitions = None


@pytest.fixture
def fu():
    # __init__ calls getUnits() immediately, so QgsProject must be mocked
    # before the instance is created.
    with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
        MockProj.instance.return_value = _make_project("LPS")
        instance = QGISRedFieldUtils()
    # After construction the mock is released; individual tests re-patch as needed.
    return instance


# ---------------------------------------------------------------------------
# _resolveAbbr  (pure logic, no project needed)
# ---------------------------------------------------------------------------
class TestResolveAbbr:
    def test_plain_abbr_unchanged(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("m/s") == "m/s"

    def test_empty_abbr(self, fu):
        assert fu._resolveAbbr("") == ""

    def test_none_abbr(self, fu):
        assert fu._resolveAbbr(None) is None

    def test_same_as_flow_lps(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("See FlowUnits") == "lps"

    def test_same_as_flow_lpm(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPM")
            assert fu._resolveAbbr("See FlowUnits") == "lpm"

    def test_same_as_flow_gpm(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu._resolveAbbr("See FlowUnits") == "gpm"

    def test_same_as_flow_cms(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("CMS")
            assert fu._resolveAbbr("See FlowUnits") == "cms"

    def test_same_as_pressure_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("See PressUnits") == "m"

    def test_same_as_pressure_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu._resolveAbbr("See PressUnits") == "psi"

    def test_same_as_mass_mg(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/l")
            assert fu._resolveAbbr("See MassUnits/L") == "mg/L"

    def test_same_as_mass_ug(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="µg/L")
            assert fu._resolveAbbr("See MassUnits/L") == "µg/L"

    def test_same_as_mass_per_day(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._resolveAbbr("See MassUnits/L/day") == "mg/L/day"

    def test_same_as_mass_per_min(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._resolveAbbr("See MassUnits/min") == "mg/min"

    def test_composite_flow_and_pressure(self, fu):
        """Emitter coefficient: See FlowUnits/sqr(See PressUnits)"""
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            result = fu._resolveAbbr("See FlowUnits/sqr(See PressUnits)")
            assert result == "lps/√m"

    def test_composite_flow_and_pressure_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            result = fu._resolveAbbr("See FlowUnits/sqr(See PressUnits)")
            assert result == "gpm/√psi"

    def test_sqr_replaced_with_sqrt_symbol(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("sqr(m)") == "√m"

    def test_sqr_not_in_abbr_unchanged(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("m/s") == "m/s"


# ---------------------------------------------------------------------------
# _getFlowFieldAbbr
# ---------------------------------------------------------------------------
class TestGetFlowFieldAbbr:
    @pytest.mark.parametrize("unit_code,expected_abbr", [
        ("LPS",  "lps"),
        ("LPM",  "lpm"),
        ("MLD",  "mld"),
        ("CMS",  "cms"),
        ("CMH",  "cmh"),
        ("CMD",  "cmd"),
        ("CFS",  "cfs"),
        ("GPM",  "gpm"),
        ("MGD",  "mgd"),
        ("IMGD", "imgd"),
        ("AFD",  "afd"),
    ])
    def test_all_flow_units(self, fu, unit_code, expected_abbr):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(unit_code)
            assert fu._getFlowFieldAbbr() == expected_abbr


# ---------------------------------------------------------------------------
# _getPressureFieldAbbr
# ---------------------------------------------------------------------------
class TestGetPressureFieldAbbr:
    def test_si_returns_m(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._getPressureFieldAbbr() == "m"

    def test_us_returns_psi(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu._getPressureFieldAbbr() == "psi"


# ---------------------------------------------------------------------------
# _getMassAbbr
# ---------------------------------------------------------------------------
class TestGetMassAbbr:
    def test_mg(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._getMassAbbr() == "mg"

    def test_ug(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="µg/L")
            assert fu._getMassAbbr() == "µg"

    def test_uses_si_abbr_for_si_project(self, fu):
        fake_row = {"si_abbr": "mg_si", "us_abbr": "mg_us", "condition_value": "mg/L"}
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L")
            with patch.object(fu, "_getRowByCondition", return_value=fake_row):
                assert fu._getMassAbbr() == "mg_si"

    def test_uses_us_abbr_for_us_project(self, fu):
        fake_row = {"si_abbr": "mg_si", "us_abbr": "mg_us", "condition_value": "mg/L"}
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM", "mg/L")
            with patch.object(fu, "_getRowByCondition", return_value=fake_row):
                assert fu._getMassAbbr() == "mg_us"

    def test_unknown_concentration_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="unknown/L")
            assert fu._getMassAbbr() == ""


# ---------------------------------------------------------------------------
# CSV loading: loadUnitDefinitions + _getFirstRow + _getRowByCondition
# ---------------------------------------------------------------------------
class TestCsvLoading:
    def test_csv_loads_rows(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            defs = fu.loadUnitDefinitions()
            assert len(defs["rows"]) > 0

    def test_pipes_length_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getFirstRow("Pipes", "Length")
            assert row["si_abbr"] == "m"
            assert row["us_abbr"] == "ft"
            assert row["si_dec"] == 2

    def test_wall_coeff_condition_0(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getRowByCondition("Pipes", "WallCoeff", "0")
            # order-0: mass/L/day units (expressed as "See MassUnits/L/day" in the CSV)
            assert "See MassUnits" in row["si_abbr"]

    def test_wall_coeff_condition_1(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getRowByCondition("Pipes", "WallCoeff", "1")
            assert row["si_abbr"] == "1/day"

    def test_valve_setting_fcv(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            row = fu._getRowByCondition("Valves", "Setting", "FCV")
            assert row["si_abbr"] == "See FlowUnits"

    def test_nodes_pressure_condition_kpa(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            # Pressure options moved to Global/PressUnits; Nodes/Pressure now references See PressUnits
            row = fu._getRowByCondition("Global", "PressUnits", "KPA")
            assert row["si_abbr"] == "kPa"

    def test_unknown_condition_falls_back_to_first_row(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getRowByCondition("Pipes", "Length", "nonexistent")
            # Fallback: first unconditional row for Pipes/Length
            assert row["si_abbr"] == "m"

    def test_pretty_names_loaded(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            defs = fu.loadUnitDefinitions()
            assert "Pipes" in defs["prettyNames"]
            assert defs["prettyNames"]["Pipes"]["Length"] == "Length"

    def test_cache_reused(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            defs1 = fu.loadUnitDefinitions()
            defs2 = fu.loadUnitDefinitions()
            assert defs1 is defs2


# ---------------------------------------------------------------------------
# Public API: getUnitAbbreviationForLayer
# ---------------------------------------------------------------------------
class TestGetUnitAbbreviationForLayer:
    def test_pipes_length_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu.getUnitAbbreviationForLayer("qgisred_query_pipes_length") == "m"

    def test_pipes_length_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu.getUnitAbbreviationForLayer("qgisred_query_pipes_length") == "ft"

    def test_unknown_layer_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            assert fu.getUnitAbbreviationForLayer("qgisred_query_unknown") == ""

    def test_empty_layer_id(self, fu):
        assert fu.getUnitAbbreviationForLayer("") == ""


# ---------------------------------------------------------------------------
# Public API: getResultPropertyUnit
# ---------------------------------------------------------------------------
class TestGetResultPropertyUnit:
    def test_flow_lps(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu.getResultPropertyUnit("Link", "Flow") == "lps"

    def test_flow_gpm(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu.getResultPropertyUnit("Link", "Flow") == "gpm"

    def test_flow_mld(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("MLD")
            assert fu.getResultPropertyUnit("Link", "Flow") == "mld"

    def test_velocity_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu.getResultPropertyUnit("Link", "Velocity") == "m/s"

    def test_velocity_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu.getResultPropertyUnit("Link", "Velocity") == "ft/s"

    def test_pressure_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu.getResultPropertyUnit("Node", "Pressure") == "m"

    def test_pressure_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu.getResultPropertyUnit("Node", "Pressure") == "psi"

    def test_demand_resolves_same_as_flow(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPM")
            assert fu.getResultPropertyUnit("Node", "Demand") == "lpm"

    def test_unknown_property_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            assert fu.getResultPropertyUnit("Node", "Unknown") == ""


# ---------------------------------------------------------------------------
# _getCurrencyAbbr — unitSystem branch
# ---------------------------------------------------------------------------
class TestGetCurrencyAbbr:
    def test_uses_si_abbr_for_si_project(self, fu):
        fake_row = {"si_abbr": "$_si", "us_abbr": "$_us"}
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            with patch.object(fu, "_getFirstRow", return_value=fake_row):
                assert fu._getCurrencyAbbr() == "$_si"

    def test_uses_us_abbr_for_us_project(self, fu):
        fake_row = {"si_abbr": "$_si", "us_abbr": "$_us"}
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            with patch.object(fu, "_getFirstRow", return_value=fake_row):
                assert fu._getCurrencyAbbr() == "$_us"

    def test_no_row_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            with patch.object(fu, "_getFirstRow", return_value={}):
                assert fu._getCurrencyAbbr() == ""


# ---------------------------------------------------------------------------
# Quality model-aware unit resolution
# ---------------------------------------------------------------------------
class TestQualityModel:
    # _getQualityResultAbbr
    def test_result_quality_chemical_returns_mass_abbr(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Chemical")
            assert fu._getQualityResultAbbr("Nodes") == "mg/L"

    def test_result_quality_trace_returns_percent(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Trace")
            assert fu._getQualityResultAbbr("Nodes") == "%"

    def test_result_quality_age_returns_hr(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Age")
            assert fu._getQualityResultAbbr("Nodes") == "hr"

    def test_result_quality_none_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "None")
            assert fu._getQualityResultAbbr("Nodes") == ""

    def test_result_quality_custom_model_treated_as_chemical(self, fu):
        """Any model name other than None/Trace/Age is treated as Chemical."""
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Chlorine")
            assert fu._getQualityResultAbbr("Nodes") == "mg/L"

    def test_result_quality_links_chemical(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Chemical")
            assert fu._getQualityResultAbbr("Links") == "mg/L"

    # _getIniQualityAbbr
    def test_ini_quality_chemical_returns_mass_abbr(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Chemical")
            assert fu._getIniQualityAbbr("Junctions") == "mg/L"

    def test_ini_quality_trace_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Trace")
            assert fu._getIniQualityAbbr("Junctions") == ""

    def test_ini_quality_age_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Age")
            assert fu._getIniQualityAbbr("Junctions") == ""

    def test_ini_quality_none_returns_empty(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "None")
            assert fu._getIniQualityAbbr("Junctions") == ""

    # getResultPropertyUnit integration
    def test_get_result_property_unit_quality_chemical(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Chemical")
            assert fu.getResultPropertyUnit("Node", "Quality") == "mg/L"

    def test_get_result_property_unit_quality_trace(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Trace")
            assert fu.getResultPropertyUnit("Node", "Quality") == "%"

    def test_get_result_property_unit_quality_age(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS", "mg/L", "Age")
            assert fu.getResultPropertyUnit("Node", "Quality") == "hr"
