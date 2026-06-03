# -*- coding: utf-8 -*-
"""Registry and computation of system-wide time series variables."""

from qgis.PyQt.QtCore import QCoreApplication

from .qgisred_results_binary import getOut_TimesTotalWaterSupply

TOTAL_WATER_SUPPLY_KEY = "TotalWaterSupply"


def tr(message: str) -> str:
    return QCoreApplication.translate("TimeSeriesGlobals", message)


def global_system_variable_choices():
    """Return (key, display_label) pairs for system global-variable combo (no empty entry)."""
    return [
        (TOTAL_WATER_SUPPLY_KEY, tr("Total Water Supply")),
    ]


def global_variable_display_label(key: str) -> str:
    labels = {TOTAL_WATER_SUPPLY_KEY: tr("Total Water Supply")}
    return labels.get(key, key)


def get_global_timeseries(source, variable_key):
    """Return a full time series for a system global variable."""
    if variable_key == TOTAL_WATER_SUPPLY_KEY:
        if source["kind"] == "out":
            return getOut_TimesTotalWaterSupply(source["out_path"])
        from .qgisred_results_hyd import getHyd_TimesTotalWaterSupply

        return getHyd_TimesTotalWaterSupply(source["hyd_path"], source["out_path"])
    return []
