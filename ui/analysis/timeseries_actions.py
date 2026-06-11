# -*- coding: utf-8 -*-
"""Time series actions.

Kept in ui/analysis to be importable in unit tests on non-Windows environments,
avoiding Windows-only DLL imports pulled by sections/.
"""


def clear_all_timeseries(section, dock=None) -> None:
    """Reset selection, clear map selection/highlights, and clear the plot."""
    if dock is None:
        dock = getattr(section, "activeTimeSeriesDock", None)

    try:
        section._timeSeriesResetSelection(dock)
    except Exception:
        try:
            dock.selection = []
            dock.selectionKey = None
        except Exception:
            pass

    try:
        dock.lastFeature = None
        dock.lastLayer = None
        dock.lastCategory = None
    except Exception:
        pass

    try:
        if dock is getattr(section, "activeTimeSeriesDock", None):
            section._clearTimeSeriesMapSelection()
    except Exception:
        pass

    try:
        section._clearTimeSeriesHighlight(dock)
    except Exception:
        pass

    try:
        if dock is not None:
            dock.updatePlotSeries([], "", "", "")
            try:
                dock.resetGlobalVarCombos()
            except Exception:
                pass
    except Exception:
        pass

