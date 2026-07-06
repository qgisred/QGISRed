from contextlib import suppress
# -*- coding: utf-8 -*-
"""Time series actions.

Kept in ui/analysis to be importable in unit tests on non-Windows environments,
avoiding Windows-only DLL imports pulled by sections/.
"""


# Node magnitudes shown for every node (same set as the results panel).
_NODE_BASE_FIELDS = (
    ("lbl_pressure", "Pressure"),
    ("lbl_head", "Head"),
    ("lbl_demand", "Demand"),
    ("lbl_quality", "Quality"),
)
# Extra magnitudes offered only when the picked node is a storage tank (DEPOSITO).
_NODE_TANK_FIELDS = (
    ("lbl_tank_volume", "Volume"),
    ("lbl_tank_overflow", "TankSpill"),
)
# Link magnitudes for the right-click picker menu (signed/unsigned flow excluded;
# those are only selectable from the results combo, not the map menu).
_LINK_MENU_FIELDS = (
    "lbl_flow", "lbl_velocity", "lbl_headloss", "lbl_unit_headloss",
    "lbl_friction_factor", "lbl_status", "lbl_reaction_rate", "lbl_quality",
)


def node_magnitude_field_map(dock, is_tank=False) -> dict:
    """Ordered display-label → internal-property map for node magnitudes.

    When ``is_tank`` is true, appends the tank-only Volume and Overflow Flow
    magnitudes after the standard four.
    """
    fields = list(_NODE_BASE_FIELDS)
    if is_tank:
        fields += list(_NODE_TANK_FIELDS)
    result = {}
    for attr, internal in fields:
        label = getattr(dock, attr, "")
        if not label:
            continue
        text = str(label).strip()
        if not text or text in result:
            continue
        result[text] = internal
    return result


def magnitude_choices(dock, category, is_tank=False) -> list:
    """Ordered, de-duplicated magnitude labels for the right-click picker menu."""
    if category == "Node":
        return list(node_magnitude_field_map(dock, is_tank=is_tank).keys())
    out = []
    for attr in _LINK_MENU_FIELDS:
        label = getattr(dock, attr, "")
        if not label:
            continue
        text = str(label).strip()
        if not text or text in out:
            continue
        out.append(text)
    return out


def clear_all_timeseries(section, dock=None) -> None:
    """Reset selection, clear map selection/highlights, and clear the plot."""
    if dock is None:
        dock = getattr(section, "activeTimeSeriesDock", None)

    try:
        section._timeSeriesResetSelection(dock)
    except Exception:
        with suppress(Exception):
            dock.selection = []
            dock.selectionKey = None

    with suppress(Exception):
        dock.lastFeature = None
        dock.lastLayer = None
        dock.lastCategory = None

    with suppress(Exception):
        if dock is getattr(section, "activeTimeSeriesDock", None):
            section._clearTimeSeriesMapSelection()

    with suppress(Exception):
        section._clearTimeSeriesHighlight(dock)

    with suppress(Exception):
        if dock is not None:
            dock.updatePlotSeries([], "", "", "")
            with suppress(Exception):
                dock.resetGlobalVarCombos()

