# -*- coding: utf-8 -*-
"""Tests for time series selection keeping global variables on map pick."""


def _time_series_map_selection_items(section):
    return [
        it for it in (getattr(section, "timeSeriesSelection", None) or [])
        if it.get("category") != "Global"
    ]


def _time_series_reset_map_selection(section):
    section.timeSeriesSelection = [
        it for it in (getattr(section, "timeSeriesSelection", None) or [])
        if it.get("category") == "Global"
    ]
    section._timeSeriesSelectionKey = None


class _SectionLike:
    def __init__(self, selection):
        self.timeSeriesSelection = list(selection)
        self._timeSeriesSelectionKey = "x"


class TestTimeSeriesMapSelection:
    def test_reset_map_selection_keeps_globals(self):
        s = _SectionLike([
            {"category": "Global", "element_id": "TotalWaterSupply"},
            {"category": "Node", "element_id": "J1", "layer_identifier": "qgisred_junctions"},
        ])
        _time_series_reset_map_selection(s)
        assert len(s.timeSeriesSelection) == 1
        assert s.timeSeriesSelection[0]["category"] == "Global"

    def test_map_selection_items_excludes_globals(self):
        s = _SectionLike([
            {"category": "Global", "element_id": "TotalWaterSupply"},
            {"category": "Link", "element_id": "P1"},
        ])
        items = _time_series_map_selection_items(s)
        assert len(items) == 1
        assert items[0]["category"] == "Link"
