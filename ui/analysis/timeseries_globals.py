# -*- coding: utf-8 -*-
"""Registry and computation of system-wide time series variables."""

from qgis.PyQt.QtCore import QCoreApplication

from .qgisred_results_binary import getOut_TimesTotalWaterDemand, getOut_TimesTotalWaterSupply

TOTAL_WATER_SUPPLY_KEY = "TotalWaterSupply"
TOTAL_WATER_DEMAND_KEY = "TotalWaterDemand"

GLOBAL_SYSTEM_VARIABLE_KEYS = frozenset({
    TOTAL_WATER_SUPPLY_KEY,
    TOTAL_WATER_DEMAND_KEY,
})


def tr(message: str) -> str:
    return QCoreApplication.translate("TimeSeriesGlobals", message)


def global_system_variable_choices():
    """Return (key, display_label) pairs for system global-variable combo (no empty entry)."""
    return [
        (TOTAL_WATER_SUPPLY_KEY, tr("Total Water Supply")),
        (TOTAL_WATER_DEMAND_KEY, tr("Total Water Demand")),
    ]


def global_variable_display_label(key: str) -> str:
    labels = {
        TOTAL_WATER_SUPPLY_KEY: tr("Total Water Supply"),
        TOTAL_WATER_DEMAND_KEY: tr("Total Water Demand"),
    }
    return labels.get(key, key)


def get_global_timeseries(source, variable_key):
    """Return a full time series for a system global variable."""
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
    return []
