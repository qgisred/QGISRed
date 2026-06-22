# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest
from qgis.PyQt.QtCore import QPointF, QRectF, Qt

from QGISRed.ui.analysis.timeseries_actions import (
    clear_all_timeseries,
    magnitude_choices,
    node_magnitude_field_map,
)
from QGISRed.ui.analysis.timeseries_legend_interaction import LegendInteractionController


class _MagDock:
    lbl_pressure = "Pressure"
    lbl_head = "Head"
    lbl_demand = "Demand"
    lbl_quality = "Quality"
    lbl_tank_volume = "Volume"
    lbl_tank_overflow = "Overflow Flow"
    lbl_flow = "Flow"
    lbl_velocity = "Velocity"
    lbl_headloss = "HeadLoss"
    lbl_unit_headloss = "Unit HeadLoss"
    lbl_friction_factor = "Friction Factor"
    lbl_status = "Status"
    lbl_reaction_rate = "Reaction Rate"


class TestMagnitudeChoices:
    def test_plain_node_excludes_tank_magnitudes(self):
        assert magnitude_choices(_MagDock(), "Node", is_tank=False) == [
            "Pressure", "Head", "Demand", "Quality",
        ]

    def test_tank_node_appends_volume_and_overflow(self):
        assert magnitude_choices(_MagDock(), "Node", is_tank=True) == [
            "Pressure", "Head", "Demand", "Quality", "Volume", "Overflow Flow",
        ]

    def test_link_choices_exclude_tank_magnitudes(self):
        choices = magnitude_choices(_MagDock(), "Link", is_tank=True)
        assert "Volume" not in choices and "Overflow Flow" not in choices
        assert choices[0] == "Flow" and "Status" in choices

    def test_field_map_maps_tank_labels_to_internal_props(self):
        plain = node_magnitude_field_map(_MagDock(), is_tank=False)
        assert "Volume" not in plain and "Overflow Flow" not in plain
        tank = node_magnitude_field_map(_MagDock(), is_tank=True)
        assert tank["Volume"] == "Volume"
        assert tank["Overflow Flow"] == "TankSpill"
        assert tank["Pressure"] == "Pressure"


class _Dock:
    def __init__(self):
        self.selection = [{"dummy": 1}]
        self.selectionKey = "something"
        self.lastFeature = object()
        self.lastLayer = object()
        self.lastCategory = "Node"
        self.updatePlotSeries = MagicMock()
        self.resetGlobalVarCombos = MagicMock()


class _SectionLike:
    def __init__(self):
        self.timeSeriesDock = _Dock()
        self.activeTimeSeriesDock = self.timeSeriesDock

        self._timeSeriesResetSelection = MagicMock(
            side_effect=lambda d: (setattr(d, "selection", []), setattr(d, "selectionKey", None))
        )
        self._clearTimeSeriesMapSelection = MagicMock()
        self._clearTimeSeriesHighlight = MagicMock()


class TestTimeSeriesActions:
    def test_clear_all_timeseries_resets_state_and_clears_plot(self):
        s = _SectionLike()
        dock = s.timeSeriesDock

        clear_all_timeseries(s, dock)

        assert dock.selection == []
        assert dock.selectionKey is None
        assert dock.lastFeature is None
        assert dock.lastLayer is None
        assert dock.lastCategory is None

        s._timeSeriesResetSelection.assert_called_once_with(dock)
        s._clearTimeSeriesMapSelection.assert_called_once()
        s._clearTimeSeriesHighlight.assert_called_once_with(dock)
        dock.updatePlotSeries.assert_called_once_with([], "", "", "")
        dock.resetGlobalVarCombos.assert_called_once()

    def test_clear_all_timeseries_defaults_to_active_dock(self):
        s = _SectionLike()

        clear_all_timeseries(s)

        assert s.timeSeriesDock.selection == []
        s._timeSeriesResetSelection.assert_called_once_with(s.timeSeriesDock)
        s.timeSeriesDock.updatePlotSeries.assert_called_once_with([], "", "", "")


class _Widget:
    def __init__(self):
        self.series = [{"series_key": "a"}, {"series_key": "b"}]
        self._legend_hitboxes = []
        self._legend_delete_hitboxes = []
        self.removed = []
        self.updated = 0

    def update(self):
        self.updated += 1

    def removeSeries(self, idx: int) -> bool:
        self.removed.append(int(idx))
        return True


class TestTimeSeriesLegendActions:
    def test_click_on_delete_hitbox_removes_series(self):
        w = _Widget()
        w._legend_delete_hitboxes = [(QRectF(0, 0, 10, 10), 1)]
        w._legend_hitboxes = [(QRectF(0, 0, 10, 10), 0)]  # overlaps, delete should win

        c = LegendInteractionController(w)
        c.begin(QPointF(5, 5), Qt.KeyboardModifier.NoModifier)

        assert c.apply_delete_if_click() is True
        assert w.removed == [1]

    def test_delete_has_priority_over_toggle_drag(self):
        w = _Widget()
        w._legend_delete_hitboxes = [(QRectF(0, 0, 10, 10), 1)]
        w._legend_hitboxes = [(QRectF(0, 0, 10, 10), 0)]

        c = LegendInteractionController(w)
        c.begin(QPointF(5, 5), Qt.KeyboardModifier.NoModifier)

        # internal state: delete candidate set, drag candidate cleared
        assert c._delete_candidate_idx == 1
        assert c._drag_candidate_idx is None
