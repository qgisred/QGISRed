# -*- coding: utf-8 -*-
"""Time series actions.

Kept in ui/analysis to be importable in unit tests on non-Windows environments,
avoiding Windows-only DLL imports pulled by sections/.
"""


def clear_all_timeseries(section) -> None:
    """Reset selection, clear map selection/highlights, and clear the plot."""
    try:
        section._timeSeriesResetSelection()
    except Exception:
        try:
            section.timeSeriesSelection = []
            section._timeSeriesSelectionKey = None
        except Exception:
            pass

    try:
        section.lastTimeSeriesFeature = None
        section.lastTimeSeriesLayer = None
        section.lastTimeSeriesCategory = None
    except Exception:
        pass

    try:
        section._clearTimeSeriesMapSelection()
    except Exception:
        pass

    try:
        section._clearTimeSeriesHighlight()
    except Exception:
        pass

    try:
        dock = getattr(section, "timeSeriesDock", None)
        if dock is not None:
            dock.updatePlotSeries([], "", "", "")
    except Exception:
        pass

