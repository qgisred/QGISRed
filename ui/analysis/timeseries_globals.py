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

# Stored volume comes out of the results binary in EPANET model volume units
# (m³ SI / ft³ US). *Which* unit it is displayed in is declared by the units CSV
# (Global/VolumeUnits, reached through Nodes/Volume); how big each unit is lives here,
# so a unit added to the CSV only needs its size added to this table.
# Keyed by the CSV abbreviation on purpose: the conversion follows the unit, not the
# unit system, so renaming m3 to hm3 in the CSV must not keep the old factor.
# ft3 is here as a *source* unit (what US projects report in), never as a target.
# Keys are plain spellings — they go through plain_unit_abbr(), which makes how the CSV
# writes the exponent (m3, m^3 or m³) irrelevant to the lookup.
_CUBIC_METERS_PER_VOLUME_UNIT = {
    "m3": 1.0,
    "ft3": 0.028316846592,  # 1728 in³ of 0.0254 m
    "MG": 3785.411784,      # 1e6 US gallons of 3.785411784 L
    "IMG": 4546.09,         # 1e6 imperial gallons of 4.54609 L
}
# Volume unit each EPANET unit system reports in, keyed by CSV ConditionValue.
_MODEL_VOLUME_UNIT = {"SI": "m3", "US": "ft3", "IMGD": "ft3"}
# Unknown units already reported, so a repainting chart logs each one only once.
_UNKNOWN_VOLUME_UNITS_WARNED = set()

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


def _warn_unknown_volume_unit(unit: str) -> None:
    """Log an unconvertible volume unit once, so a repainting chart does not spam."""
    if unit in _UNKNOWN_VOLUME_UNITS_WARNED:
        return
    _UNKNOWN_VOLUME_UNITS_WARNED.add(unit)
    from qgis.core import QgsMessageLog
    from ...compat import QGIS_WARNING

    QgsMessageLog.logMessage(
        "Volume unit '{}' has no size declared in timeseries_globals: stored volume "
        "is left in model units.".format(unit),
        "QGISRed", QGIS_WARNING,
    )


def stored_volume_display_factor() -> float:
    """Factor from the model volume unit (m³ SI / ft³ US) to the project display unit.

    The CSV decides which unit the volume is shown in; ``_CUBIC_METERS_PER_VOLUME_UNIT``
    says how big each unit is, and the factor is the ratio between the two. A unit with
    no size declared cannot be converted, so the series is left in model units and the
    unit is logged, rather than silently mislabelled with a stale factor.
    """
    try:
        from ...tools.utils.qgisred_field_utils import (
            QGISRedFieldUtils, normalize_element, plain_unit_abbr,
        )

        utils = QGISRedFieldUtils()
        source_unit = _MODEL_VOLUME_UNIT.get(utils.getVolumeUnitsCondition(), "m3")
        target_unit = utils.getUnitAbbreviation(normalize_element("Nodes"), "Volume")
    except Exception:
        return 1.0

    source_unit = plain_unit_abbr(source_unit)
    target_unit = plain_unit_abbr(target_unit)
    if not target_unit or target_unit == source_unit:
        return 1.0
    source_size = _CUBIC_METERS_PER_VOLUME_UNIT.get(source_unit)
    target_size = _CUBIC_METERS_PER_VOLUME_UNIT.get(target_unit)
    if not source_size or not target_size:
        _warn_unknown_volume_unit(target_unit if not target_size else source_unit)
        return 1.0
    return source_size / target_size


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
        from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element

        return QGISRedFieldUtils().getDecimals(normalize_element("Nodes"), "Volume")
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


# Preferred Y axis for each system global variable when no axis is set explicitly.
# Flow magnitudes (supply/demand/spill) go left; stored volume and average pressure
# go right. Supply and demand share the flow scale group, so they always land together.
GLOBAL_VARIABLE_PREFERRED_AXIS = {
    TOTAL_WATER_SUPPLY_KEY: "left",
    TOTAL_WATER_DEMAND_KEY: "left",
    TOTAL_TANK_SPILL_KEY: "left",
    TOTAL_STORED_VOLUME_KEY: "right",
    AVERAGE_NODE_PRESSURE_KEY: "right",
}


def preferred_axis_for_global_variable(variable_key: str) -> str:
    return GLOBAL_VARIABLE_PREFERRED_AXIS.get(variable_key, "left")


# Fixed RGB colour per system global variable (only five exist for now): produced
# flow blue, consumed flow magenta, spilled flow red, stored volume green, average
# pressure orange. Returned as a tuple so this module stays free of Qt imports.
GLOBAL_VARIABLE_RGB = {
    TOTAL_WATER_SUPPLY_KEY: (31, 119, 180),
    TOTAL_WATER_DEMAND_KEY: (199, 31, 138),
    TOTAL_TANK_SPILL_KEY: (214, 39, 40),
    TOTAL_STORED_VOLUME_KEY: (44, 160, 44),
    AVERAGE_NODE_PRESSURE_KEY: (255, 127, 14),
}


def global_variable_rgb(variable_key: str):
    """Return the fixed ``(r, g, b)`` colour for a system variable, or ``None``."""
    return GLOBAL_VARIABLE_RGB.get(variable_key)


def _series_scale_bucket(series: dict) -> str:
    """Scale group of a series, used to keep compatible scales on one axis.

    Supply, demand and spill share one ``global:flow`` group (same units, so they
    never need splitting and supply/demand stay together). Stored volume and average
    pressure each get their own group. Element series group by their magnitude label.
    """
    if (series.get("legend_type") or "").strip().lower() == "global":
        variable_key = global_variable_key_from_series_key(series.get("series_key") or "")
        if variable_key in (TOTAL_WATER_SUPPLY_KEY, TOTAL_WATER_DEMAND_KEY, TOTAL_TANK_SPILL_KEY):
            return "global:flow"
        if variable_key == TOTAL_STORED_VOLUME_KEY:
            return "global:volume"
        if variable_key == AVERAGE_NODE_PRESSURE_KEY:
            return "global:pressure"
        return "global:other"
    return "element:" + (series.get("magnitude") or "").strip()


# Order in which a scale group is relocated to fill an empty axis (most movable
# first). ``global:flow`` moves as a single group, so produced and consumed flow
# always stay on the same axis even when relocated.
_AXIS_FALLBACK_MOVE_ORDER = ("global:volume", "global:pressure", "global:other", "global:flow")


def assign_default_series_axes(series):
    """Left/right Y axis per series when none is set explicitly.

    System (global) variables follow their per-variable preference
    (:data:`GLOBAL_VARIABLE_PREFERRED_AXIS`): produced/consumed/spilled flow on the
    left, stored volume and average pressure on the right. Element series keep the
    legacy layout (first magnitude left, the rest right).

    When the preferences would leave one axis empty while the other carries two or
    more distinct scale groups, one group is moved to the empty axis to maximise
    visibility (e.g. stored volume + average pressure alone split across both axes
    instead of crowding the right). Produced, consumed and spilled flow share one
    scale group that always moves as a unit, so produced and consumed flow stay on
    the same axis.
    """
    buckets = [_series_scale_bucket(s) for s in series]
    ordered = []
    for bucket in buckets:
        if bucket not in ordered:
            ordered.append(bucket)

    first_element = next((b for b in ordered if b.startswith("element:")), None)
    sides = {}
    for bucket in ordered:
        if bucket.startswith("global:"):
            variable_axis = "right" if bucket in ("global:volume", "global:pressure") else "left"
            sides[bucket] = variable_axis
        else:
            sides[bucket] = "left" if bucket == first_element else "right"

    left_buckets = [b for b in ordered if sides[b] == "left"]
    right_buckets = [b for b in ordered if sides[b] == "right"]
    if len(ordered) >= 2 and (not left_buckets or not right_buckets):
        crowded = right_buckets if not left_buckets else left_buckets
        empty_side = "left" if not left_buckets else "right"
        movable = next((b for b in _AXIS_FALLBACK_MOVE_ORDER if b in crowded), None)
        if movable is None:
            extra_elements = [b for b in crowded if b.startswith("element:") and b != first_element]
            movable = extra_elements[-1] if extra_elements else None
        if movable is not None:
            sides[movable] = empty_side

    return [sides[bucket] for bucket in buckets]


def global_variable_unit_abbreviation(variable_key: str) -> str:
    from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element

    utils = QGISRedFieldUtils()
    if variable_key == TOTAL_STORED_VOLUME_KEY:
        return utils.getUnitAbbreviation(normalize_element("Nodes"), "Volume")
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
