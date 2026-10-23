# -*- coding: utf-8 -*-
"""Opening a layer in the Legend Editor shows the strategy its style carries.

The Class Order, Intervals, Sizes and Colors selectors move to what the layer's legend
strategy says (a shipped style, or one saved by the user), while the classes stay as the
layer draws them. The Layers Panel hears of one renderer per Apply or load, so its class
counts never read N/D. Pipe ages are captioned in years whatever the unit system.
"""
import json
from unittest.mock import MagicMock

import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.tools.utils.qgisred_styling_utils import PALETTE_KIND_SEQUENTIAL
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

CATEGORICAL = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
NUMERIC = QGISRedLegendsDialog.FIELD_TYPE_NUMERIC
PALETTE = "QGISRed Qualitative 10"


class FakeCombo:
    def __init__(self, values):
        self.values = list(values)
        self.index = 0
        self.blocked = False
        self.selections = []

    def findData(self, data):
        return self.values.index(data) if data in self.values else -1

    def setCurrentIndex(self, index):
        self.index = index
        self.selections.append((self.values[index], self.blocked))

    def currentData(self):
        return self.values[self.index]

    def currentIndex(self):
        return self.index

    def blockSignals(self, blocked):
        self.blocked = blocked


def _strategy(mode="categorized", parts=(), **blocks):
    strategy = {"schema": "qgisred.legendStrategy.v2", "mode": mode, "field": "Material", "parts": list(parts)}
    strategy.update(blocks)
    return strategy


def _dialog(strategy, fieldType=CATEGORICAL, isResults=False):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = MagicMock()
    rawStrategy = json.dumps(strategy) if strategy is not None else None
    dialog.currentLayer.customProperty.side_effect = (
        lambda key, default=None: rawStrategy if key == "qgisred_legend_strategy" else default)
    dialog.currentFieldType = fieldType
    dialog.isResultsLayer = lambda: isResults
    dialog.cbClassOrder = FakeCombo(["none", "ascending", "descending"])
    dialog.cbClasses = FakeCombo(["current", "all"])
    dialog.availableUniqueValues = []
    dialog.cbMode = FakeCombo(["Manual", "Pretty", "Jenks"])
    dialog.cbSizes = FakeCombo(["Manual", "Equal", "Linear"])
    dialog.cbColors = FakeCombo(["Manual", "Random", PALETTE_KIND_SEQUENTIAL])
    for name in ("spinSizeEqual", "spinSizeMin", "spinSizeMax", "ckSizeInvert", "ckColorInvert", "btnColorRamp"):
        setattr(dialog, name, MagicMock())
    dialog.colorRampKinds = {PALETTE: PALETTE_KIND_SEQUENTIAL}
    dialog.style = MagicMock()
    dialog.previousClassificationMode = None
    dialog.previousSizeMode = None
    dialog.calls = []
    for name in ("updateUiBasedOnFieldType", "updateSizeControlsVisibility", "updateColorControlsVisibility",
                 "syncColorRampButton", "applyColorLogic", "applySizeLogic", "markLegendEdited"):
        setattr(dialog, name, lambda *args, name=name, **kwargs: dialog.calls.append(name))
    return dialog


class TestShowingTheStrategyOnOpen:
    def test_a_layer_without_a_strategy_leaves_the_selectors_alone(self):
        dialog = _dialog(None)
        dialog.showLayerStrategyModes()
        assert dialog.cbColors.selections == [] and dialog.cbSizes.selections == [] and dialog.calls == []

    def test_the_class_order_is_selected(self):
        dialog = _dialog(_strategy(parts=["colors"], classOrder="descending", colors={"source": "random"}))
        dialog.showLayerStrategyModes()
        assert dialog.cbClassOrder.currentData() == "descending"
        # Selected with its signals held: opening a layer does not sort its classes
        assert dialog.cbClassOrder.selections == [("descending", True)]

    def test_a_style_that_adds_every_value_selects_all(self):
        dialog = _dialog(_strategy(parts=["allValues"]))
        dialog.showLayerStrategyModes()
        assert dialog.cbClasses.currentData() == "all"

    def test_a_style_with_pinned_classes_selects_current(self):
        dialog = _dialog(_strategy(parts=["allClasses", "colors"], colors={"source": "random"}))
        dialog.cbClasses.index = 1
        dialog.showLayerStrategyModes()
        assert dialog.cbClasses.currentData() == "current"

    def test_the_palette_is_selected_without_recolouring_the_classes(self):
        colors = {"source": "ramp", "rampName": PALETTE, "invertRamp": True}
        dialog = _dialog(_strategy(parts=["colors"], colors=colors))

        dialog.showLayerStrategyModes()

        assert dialog.cbColors.selections == [(PALETTE_KIND_SEQUENTIAL, True)]
        dialog.btnColorRamp.setActiveRampByName.assert_called_once_with(PALETTE)
        dialog.ckColorInvert.setChecked.assert_called_once_with(True)
        assert "syncColorRampButton" in dialog.calls and "updateColorControlsVisibility" in dialog.calls
        assert "applyColorLogic" not in dialog.calls and "markLegendEdited" not in dialog.calls

    def test_the_ramp_list_is_filled_with_its_signals_held(self):
        # Listing the ramps selects the first one, which would otherwise recolour the table.
        dialog = _dialog(_strategy(parts=["colors"], colors={"source": "ramp", "rampName": PALETTE}))
        dialog.syncColorRampButton = lambda: dialog.calls.append(dialog.btnColorRamp.blockSignals.call_args[0][0])
        dialog.showLayerStrategyModes()
        assert dialog.calls[-1] is True and dialog.btnColorRamp.blockSignals.call_args[0][0] is False

    def test_random_colours_are_selected(self):
        dialog = _dialog(_strategy(parts=["colors"], colors={"source": "random"}))
        dialog.showLayerStrategyModes()
        assert dialog.cbColors.currentData() == "Random" and "applyColorLogic" not in dialog.calls

    def test_an_unknown_ramp_keeps_the_colours_manual(self):
        dialog = _dialog(_strategy(parts=["colors"], colors={"source": "ramp", "rampName": "Gone"}))
        dialog.style = MagicMock()
        legendsModule.QGISRedStylingUtils.colorRampKind = staticmethod(lambda style, name: None)
        dialog.showLayerStrategyModes()
        assert dialog.cbColors.currentData() == "Manual"

    def test_the_sizes_mode_and_its_values_are_selected_without_resizing(self):
        sizes = {"mode": "Linear", "value": 1.0, "min": 0.4, "max": 2.5, "invert": True}
        dialog = _dialog(_strategy(parts=["sizes"], sizes=sizes))

        dialog.showLayerStrategyModes()

        assert dialog.cbSizes.selections == [("Linear", True)] and dialog.previousSizeMode == "Linear"
        dialog.spinSizeMin.setValue.assert_called_once_with(0.4)
        dialog.spinSizeMax.setValue.assert_called_once_with(2.5)
        dialog.ckSizeInvert.setChecked.assert_called_once_with(True)
        assert "updateSizeControlsVisibility" in dialog.calls and "applySizeLogic" not in dialog.calls

    def test_the_intervals_mode_of_a_thematic_map_is_selected(self):
        intervals = {"classificationMode": "Pretty", "classes": 5}
        dialog = _dialog(_strategy(mode="graduated", parts=["intervals"], intervals=intervals), fieldType=NUMERIC)

        dialog.showLayerStrategyModes()

        assert dialog.cbMode.selections == [("Pretty", True)] and dialog.previousClassificationMode == "Pretty"
        assert dialog.calls == ["updateUiBasedOnFieldType"]

    def test_result_layers_leave_their_intervals_to_the_results_rule(self):
        intervals = {"classificationMode": "Pretty", "classes": 5}
        strategy = _strategy(mode="graduated", parts=["intervals"], intervals=intervals)
        dialog = _dialog(strategy, fieldType=NUMERIC, isResults=True)
        dialog.showLayerStrategyModes()
        assert dialog.cbMode.selections == []

    def test_a_broken_strategy_is_ignored(self):
        dialog = _dialog(None)
        dialog.currentLayer.customProperty.side_effect = lambda key, default=None: "{not json"
        assert dialog.readStrategyFromLayer() is None


class FakeLayer:
    def __init__(self, blocked=False):
        self.blocked = blocked
        self.events = []
        self.rendererChanged = MagicMock(emit=lambda: self.events.append("rendererChanged"))
        self.legendChanged = MagicMock(emit=lambda: self.events.append("legendChanged"))

    def signalsBlocked(self):
        return self.blocked

    def blockSignals(self, blocked):
        self.blocked = blocked
        self.events.append(("blocked", blocked))

    def triggerRepaint(self):
        self.events.append("repaint")

    def setRenderer(self, renderer):
        self.events.append(("setRenderer", self.blocked))

    def renderer(self):
        return MagicMock()

    def id(self):
        return "layer"


class TestHoldingTheLayerSignals:
    def _dialog(self):
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        return dialog

    def test_the_panel_hears_of_the_final_renderer_once_the_writes_are_done(self):
        layer = FakeLayer()
        with self._dialog().holdingLayerSignals(layer):
            layer.setRenderer("first")
            layer.setRenderer("second")
        assert layer.events == [("blocked", True), ("setRenderer", True), ("setRenderer", True), ("blocked", False),
                                "rendererChanged", "legendChanged", "repaint"]

    def test_a_hold_inside_another_hold_announces_nothing_itself(self):
        layer = FakeLayer(blocked=True)
        with self._dialog().holdingLayerSignals(layer):
            pass
        assert layer.events == [("blocked", True), ("blocked", True)]

    def test_apply_writes_the_renderer_and_the_null_class_while_the_signals_are_held(self):
        dialog = self._dialog()
        layer = FakeLayer()
        dialog.currentLayer = layer
        dialog.sortTableRowsByClassOrder = lambda: None
        dialog.buildRendererFromDialog = lambda: "renderer"
        dialog._syncHydraulicSectorSibling = lambda renderer: None
        dialog._syncDemandBuilderLabelColors = lambda renderer: None
        dialog.restoreResultNullClass = lambda: layer.setRenderer("null class")
        dialog.ensureLayerVisible = lambda layer: None
        dialog.rememberAppliedLayer = lambda: None
        dialog.isFactorCell = lambda: False
        dialog.clearLegendEdited = lambda: None

        dialog.applyLegend()

        writes = [event for event in layer.events if isinstance(event, tuple) and event[0] == "setRenderer"]
        assert writes == [("setRenderer", True), ("setRenderer", True)]
        assert layer.events.index("legendChanged") > layer.events.index(writes[-1])


class TestTheUnitsCaption:
    def _dialog(self, monkeypatch, identifier):
        monkeypatch.setattr(legendsModule.QGISRedProjectUtils, "getUnits", staticmethod(lambda: "SI"))
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.tr = lambda text: text
        dialog.utils = object()
        dialog.currentLayer = MagicMock()
        dialog.currentLayer.customProperty.return_value = identifier
        dialog.getCurrentLayerUnitAbbr = lambda: "mm"
        return dialog

    @pytest.mark.parametrize("identifier", ["qgisred_query_pipes_age", "qgisred_query_pipes_installyear"])
    def test_pipe_ages_and_installation_years_read_in_years(self, monkeypatch, identifier):
        assert self._dialog(monkeypatch, identifier).getLegendUnitsText() == "(years)"

    @pytest.mark.parametrize("identifier, expected", [
        ("qgisred_query_pipes_diameter", "SI units (mm)"),
        ("qgisred_pipes", "SI units"),
    ])
    def test_the_other_layers_keep_their_caption(self, monkeypatch, identifier, expected):
        assert self._dialog(monkeypatch, identifier).getLegendUnitsText() == expected
