# -*- coding: utf-8 -*-
"""Registry and computation of system-wide time series variables."""

from qgis.PyQt.QtCore import QCoreApplication

from .qgisred_results_binary import (
    getOut_TimesAverageNodePressure,
    getOut_TimesTotalWaterDemand,
    getOut_TimesTotalWaterSupply,
)
from .qgisred_tank_storage import (
    getHyd_TimesTotalStoredVolume,
    getHyd_TimesTotalTankSpill,
    getOut_TimesTotalStoredVolume,
    getOut_TimesTotalTankSpill,
)

TOTAL_WATER_SUPPLY_KEY = "TotalWaterSupply"
TOTAL_WATER_DEMAND_KEY = "TotalWaterDemand"
TOTAL_STORED_VOLUME_KEY = "TotalStoredVolume"
TOTAL_TANK_SPILL_KEY = "TotalTankSpill"
AVERAGE_NODE_PRESSURE_KEY = "AverageNodePressure"

# Display-only decimals for time-series charts/tables (not used in volume math).
TOTAL_STORED_VOLUME_DISPLAY_DECIMALS = 2

# EPANET model volume units are ft³ (US) / m³ (SI). Like EPANET-UI, stored
# volume is displayed in million gallons for US flow units (imperial for IMGD).
_FT3_PER_MILLION_US_GALLON = 1.0e6 * 231.0 / 1728.0  # 1 MG in ft³ (1 US gal = 231 in³)
_FT3_PER_MILLION_IMPERIAL_GALLON = 1.0e6 * 4.54609 / 28.316846592  # 1 MGI in ft³

GLOBAL_SYSTEM_VARIABLE_KEYS = frozenset({
    TOTAL_WATER_SUPPLY_KEY,
    TOTAL_WATER_DEMAND_KEY,
    TOTAL_STORED_VOLUME_KEY,
    TOTAL_TANK_SPILL_KEY,
    AVERAGE_NODE_PRESSURE_KEY,
})


def tr(message: str) -> str:
    return QCoreApplication.translate("TimeSeriesGlobals", message)


def global_axis_group_label() -> str:
    """Short Y-axis / legend group title for system global-variable series."""
    return tr("System")


def _stored_volume_us_abbreviation() -> str:
    """Return ``MG``/``MGI`` when the project uses US flow units, ``''`` for SI."""
    try:
        from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils

        if QGISRedProjectUtils.getUnits() != "US":
            return ""
        flow_unit = (QGISRedProjectUtils.getFlowUnit() or "").strip().upper()
        return "MGI" if flow_unit == "IMGD" else "MG"
    except Exception:
        return ""


def stored_volume_display_factor() -> float:
    """Factor from model volume units (ft³ US / m³ SI) to display units."""
    abbr = _stored_volume_us_abbreviation()
    if abbr == "MGI":
        return 1.0 / _FT3_PER_MILLION_IMPERIAL_GALLON
    if abbr == "MG":
        return 1.0 / _FT3_PER_MILLION_US_GALLON
    return 1.0


def global_system_variable_choices():
    """Return (key, display_label) pairs for system global-variable combo (no empty entry)."""
    return [
        (TOTAL_WATER_SUPPLY_KEY, tr("Total Water Supply")),
        (TOTAL_WATER_DEMAND_KEY, tr("Total Water Demand")),
        (TOTAL_STORED_VOLUME_KEY, tr("Total Stored Volume")),
        (TOTAL_TANK_SPILL_KEY, tr("Total Tank Spill Flow")),
        (AVERAGE_NODE_PRESSURE_KEY, tr("Average Node Pressure")),
    ]


def global_series_y_display_decimals(variable_key: str):
    """Return fixed Y-axis display decimals for a global variable, or None for CSV defaults."""
    if variable_key == TOTAL_STORED_VOLUME_KEY:
        return TOTAL_STORED_VOLUME_DISPLAY_DECIMALS
    return None


def global_variable_display_label(key: str) -> str:
    labels = {
        TOTAL_WATER_SUPPLY_KEY: tr("Total Water Supply"),
        TOTAL_WATER_DEMAND_KEY: tr("Total Water Demand"),
        TOTAL_STORED_VOLUME_KEY: tr("Total Stored Volume"),
        TOTAL_TANK_SPILL_KEY: tr("Total Tank Spill Flow"),
        AVERAGE_NODE_PRESSURE_KEY: tr("Average Node Pressure"),
    }
    return labels.get(key, key)


def global_variable_short_label(key: str) -> str:
    """Short name for values-table column header (second row under ``System``)."""
    labels = {
        TOTAL_WATER_SUPPLY_KEY: tr("Supply"),
        TOTAL_WATER_DEMAND_KEY: tr("Demand"),
        TOTAL_STORED_VOLUME_KEY: tr("Storage"),
        TOTAL_TANK_SPILL_KEY: tr("Spill"),
        AVERAGE_NODE_PRESSURE_KEY: tr("Pressure"),
    }
    return labels.get(key, key)


def global_variable_table_column_label(variable_key: str) -> str:
    """Values-table second header row: abbreviated variable and unit."""
    short = global_variable_short_label(variable_key)
    unit_abbr = global_variable_unit_abbreviation(variable_key)
    return f"{short} ({unit_abbr})" if unit_abbr else short


def global_variable_key_from_series_key(series_key: str) -> str:
    parts = str(series_key or "").split(":")
    if len(parts) >= 3 and parts[0] == "Global":
        return parts[2]
    return ""


def global_variable_unit_abbreviation(variable_key: str) -> str:
    from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element

    utils = QGISRedFieldUtils()
    if variable_key == TOTAL_STORED_VOLUME_KEY:
        us_abbr = _stored_volume_us_abbreviation()
        if us_abbr:
            return us_abbr
        return utils.getUnitAbbreviation(normalize_element("Tanks"), "MinVolume")
    if variable_key == AVERAGE_NODE_PRESSURE_KEY:
        return utils.getUnitAbbreviation(normalize_element("Nodes"), "Pressure")
    return utils.getUnitAbbreviation(normalize_element("Node"), "Demand")


def global_variable_legend_label(variable_key: str) -> str:
    """Legend / table row label: variable name and unit (Y-axis group stays on ``System``)."""
    display = global_variable_display_label(variable_key)
    unit_abbr = global_variable_unit_abbreviation(variable_key)
    return f"{display} ({unit_abbr})" if unit_abbr else display


def get_global_timeseries(source, variable_key):
    """Return a full time series for a system global variable."""
    project_directory = source.get("project_directory") or ""
    network_name = source.get("network_name") or ""

    if variable_key == TOTAL_WATER_SUPPLY_KEY:
        if source["kind"] == "out":
            return getOut_TimesTotalWaterSupply(source["out_path"])
        from .qgisred_results_hyd import getHyd_TimesTotalWaterSupply

        return getHyd_TimesTotalWaterSupply(source["hyd_path"], source["out_path"])
    if variable_key == TOTAL_WATER_DEMAND_KEY:
        if source["kind"] == "out":
            return getOut_TimesTotalWaterDemand(source["out_path"])
        from .qgisred_results_hyd import getHyd_TimesTotalWaterDemand

        return getHyd_TimesTotalWaterDemand(source["hyd_path"], source["out_path"])
    if variable_key == TOTAL_STORED_VOLUME_KEY:
        if source["kind"] == "out":
            series = getOut_TimesTotalStoredVolume(
                source["out_path"], project_directory, network_name,
            )
        else:
            series = getHyd_TimesTotalStoredVolume(
                source["hyd_path"], source["out_path"], project_directory, network_name,
            )
        factor = stored_volume_display_factor()
        if factor != 1.0:
            return [v * factor for v in series]
        return series
    if variable_key == TOTAL_TANK_SPILL_KEY:
        if source["kind"] == "out":
            return getOut_TimesTotalTankSpill(
                source["out_path"], project_directory, network_name,
            )
        return getHyd_TimesTotalTankSpill(
            source["hyd_path"], source["out_path"], project_directory, network_name,
        )
    if variable_key == AVERAGE_NODE_PRESSURE_KEY:
        if source["kind"] == "out":
            return getOut_TimesAverageNodePressure(source["out_path"])
        from .qgisred_results_hyd import getHyd_TimesAverageNodePressure

        return getHyd_TimesAverageNodePressure(source["hyd_path"], source["out_path"])
    return []
