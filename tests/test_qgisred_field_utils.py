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
def _make_project(flow_unit="LPS", concentration_units="mg/L"):
    """Return a mock QgsProject that answers readEntry for the keys we care about."""
    proj = MagicMock()

    def read_entry(section, key, default=""):
        if section == "QGISRed" and key == "project_units":
            return flow_unit, True
        if section == "QGISRed" and key == "project_concentrationunits":
            return concentration_units, True
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
            assert fu._resolveAbbr("Same as Flow") == "lps"

    def test_same_as_flow_lpm(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPM")
            assert fu._resolveAbbr("Same as Flow") == "lpm"

    def test_same_as_flow_gpm(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu._resolveAbbr("Same as Flow") == "gpm"

    def test_same_as_flow_cms(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("CMS")
            assert fu._resolveAbbr("Same as Flow") == "cms"

    def test_same_as_pressure_si(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            assert fu._resolveAbbr("Same as Pressure") == "m"

    def test_same_as_pressure_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            assert fu._resolveAbbr("Same as Pressure") == "psi"

    def test_same_as_mass_mg(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._resolveAbbr("Same as Mass/L") == "mg/L"

    def test_same_as_mass_ug(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="ug/L")
            assert fu._resolveAbbr("Same as Mass/L") == "ug/L"

    def test_same_as_mass_per_day(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._resolveAbbr("Same as Mass/L/day") == "mg/L/day"

    def test_same_as_mass_per_min(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg/L")
            assert fu._resolveAbbr("Same as Mass/min") == "mg/min"

    def test_composite_flow_and_pressure(self, fu):
        """Emitter coefficient: Same as Flow/sqr(Same as Pressure)"""
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            result = fu._resolveAbbr("Same as Flow/sqr(Same as Pressure)")
            assert result == "lps/√m"

    def test_composite_flow_and_pressure_us(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("GPM")
            result = fu._resolveAbbr("Same as Flow/sqr(Same as Pressure)")
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
            MockProj.instance.return_value = _make_project(concentration_units="ug/L")
            assert fu._getMassAbbr() == "ug"

    def test_no_slash_returns_full(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project(concentration_units="mg")
            assert fu._getMassAbbr() == "mg"


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
            # order-0: mass/L/day units (expressed as "Same as Mass/L/day" in the CSV)
            assert "Same as Mass" in row["si_abbr"]

    def test_wall_coeff_condition_1(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getRowByCondition("Pipes", "WallCoeff", "1")
            assert row["si_abbr"] == "1/day"

    def test_valve_setting_fcv(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project("LPS")
            row = fu._getRowByCondition("Valves", "Setting", "FCV")
            assert row["si_abbr"] == "Same as Flow"

    def test_nodes_pressure_condition_kpa(self, fu):
        with patch("QGISRed.tools.utils.qgisred_field_utils.QgsProject") as MockProj:
            MockProj.instance.return_value = _make_project()
            row = fu._getRowByCondition("Nodes", "Pressure", "KPA")
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
