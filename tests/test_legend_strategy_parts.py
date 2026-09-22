# -*- coding: utf-8 -*-
"""Save-strategy parts are independent: allClasses can be saved together with
colors and sizes, and loading a combined strategy pins the classes first."""
import os
from unittest.mock import MagicMock
import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSaveStrategyDialog


def _dialog():
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
    dialog.currentFieldName = "Class"
    return dialog


class FakeCheckBox:
    def __init__(self, checked=False):
        self._checked = checked
        self.enabled = True
        self.toolTip = ""

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = bool(checked)

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)

    def setToolTip(self, text):
        self.toolTip = text


APPLICABLE = {"structural": ("S", ""), "sizes": ("Z", ""), "colors": ("C", "")}


class TestSaveStrategyDialog:
    """A tick always means "recalculated when the style is loaded", for every part."""

    def _strategyDialog(self, isCategorical, structural=False, sizes=False, colors=False, automatic=True,
                        partOptions=APPLICABLE):
        dialog = QGISRedSaveStrategyDialog.__new__(QGISRedSaveStrategyDialog)
        dialog.isCategorical = isCategorical
        dialog.partOptions = partOptions
        dialog.rbAutomaticLegend = FakeCheckBox(automatic)
        dialog.rbFixedLegend = FakeCheckBox(not automatic)
        dialog.ckStructural = FakeCheckBox(structural)
        dialog.ckSizes = FakeCheckBox(sizes)
        dialog.ckColors = FakeCheckBox(colors)
        return dialog

    def test_the_mutual_exclusion_hook_is_gone(self):
        # vars(), not hasattr(): the QDialog test stub answers any attribute.
        assert "onStructuralToggled" not in vars(QGISRedSaveStrategyDialog)

    def test_a_fixed_legend_saves_no_strategy_whatever_is_ticked(self):
        dialog = self._strategyDialog(False, True, True, True, automatic=False)
        assert dialog.selectedParts() == []

    def test_numeric_parts_are_the_ticked_ones(self):
        assert self._strategyDialog(False, True, True, True).selectedParts() == ["intervals", "sizes", "colors"]
        assert self._strategyDialog(False, colors=True).selectedParts() == ["colors"]

    def test_categories_that_are_not_rebuilt_are_pinned(self):
        # "All Classes" used to be a tick meaning the opposite of the other two.
        assert self._strategyDialog(True, sizes=True, colors=True).selectedParts() == ["allClasses", "sizes", "colors"]

    def test_categories_rebuilt_from_the_values_are_not_pinned(self):
        assert self._strategyDialog(True, structural=True, colors=True).selectedParts() == ["colors"]

    def test_automatic_with_nothing_ticked_is_a_fixed_legend(self):
        assert self._strategyDialog(True).selectedParts() == []

    def test_classes_can_only_be_rebuilt_along_with_the_colors(self):
        dialog = self._strategyDialog(True, structural=True, colors=False)
        dialog.updatePartsEnabled()
        assert dialog.ckStructural.enabled is False and dialog.ckStructural.isChecked() is False

    def test_a_part_that_cannot_be_recalculated_stays_greyed(self):
        options = dict(APPLICABLE, sizes=("Sizes: kept as shown", "The sizes are set by hand."))
        dialog = self._strategyDialog(False, partOptions=options)
        dialog.updatePartsEnabled()
        assert dialog.ckSizes.enabled is False and dialog.ckColors.enabled is True

    def test_it_starts_from_what_the_overwritten_file_holds(self):
        dialog = self._strategyDialog(True, automatic=False)
        dialog.restoreInitialParts(["colors"])
        assert dialog.selectedParts() == ["colors"]  # colors without pinned classes: rebuilt

        pinned = self._strategyDialog(True, automatic=False)
        pinned.restoreInitialParts(["allClasses", "colors"])
        assert pinned.selectedParts() == ["allClasses", "colors"]

    def test_a_new_file_starts_as_a_fixed_legend(self):
        dialog = self._strategyDialog(False)
        dialog.restoreInitialParts(())
        assert dialog.rbFixedLegend.isChecked() and dialog.selectedParts() == []

    def test_automatic_is_not_offered_when_nothing_can_be_recalculated(self):
        nothing = {part: ("kept as shown", "why") for part in APPLICABLE}
        dialog = self._strategyDialog(True, partOptions=nothing)
        dialog.restoreInitialParts(["colors"])
        assert dialog.rbAutomaticLegend.enabled is False and dialog.selectedParts() == []


class TestBuildCategoricalStrategy:
    def _dialogWithParts(self, allClassesPart="ALL", colorsPart="COLORS"):
        dialog = _dialog()
        dialog.receivedRenderers = []

        def buildAllClassesPart(renderer=None):
            dialog.receivedRenderers.append(renderer)
            return allClassesPart

        dialog.buildAllClassesPart = buildAllClassesPart
        dialog.buildSizesPart = lambda: "SIZES"
        dialog.buildColorsPart = lambda: colorsPart
        return dialog

    def test_all_three_parts_build_one_strategy(self):
        dialog = self._dialogWithParts()
        strategy = dialog.buildCategoricalStrategy(["allClasses", "sizes", "colors"], "RENDERER")
        assert strategy["parts"] == ["allClasses", "sizes", "colors"]
        assert strategy["allClasses"] == "ALL"
        assert strategy["sizes"] == "SIZES"
        assert strategy["colors"] == "COLORS"
        assert strategy["mode"] == "categorized" and strategy["field"] == "Class"
        assert dialog.receivedRenderers == ["RENDERER"]

    def test_all_classes_alone_stays_a_pure_snapshot(self):
        strategy = self._dialogWithParts().buildCategoricalStrategy(["allClasses"])
        assert strategy["parts"] == ["allClasses"]
        assert "sizes" not in strategy and "colors" not in strategy

    def test_unbuildable_all_classes_drops_the_strategy(self):
        dialog = self._dialogWithParts(allClassesPart=None)
        assert dialog.buildCategoricalStrategy(["allClasses", "colors"]) is None

    def test_unbuildable_colors_drops_the_strategy(self):
        dialog = self._dialogWithParts(colorsPart=None)
        assert dialog.buildCategoricalStrategy(["allClasses", "colors"]) is None

    def test_intervals_are_never_persisted_for_categorical(self):
        strategy = self._dialogWithParts().buildCategoricalStrategy(["intervals", "colors"])
        assert strategy["parts"] == ["colors"]
        assert "intervals" not in strategy

    def test_build_from_current_ui_forwards_the_renderer(self):
        dialog = self._dialogWithParts()
        dialog.buildStrategyFromCurrentUi(["allClasses"], "RENDERER")
        assert dialog.receivedRenderers == ["RENDERER"]


class FakeSymbol:
    def __init__(self, colorName="#112233", size=2.5, width=0.5):
        self._colorName = colorName
        self._size = size
        self._width = width

    def color(self):
        symbol = self

        class _Color:
            def name(self):
                return symbol._colorName

        return _Color()

    def size(self):
        return self._size

    def width(self):
        return self._width


class FakeCategory:
    def __init__(self, value, label="lbl", symbol=None, render=True):
        self._value = value
        self._label = label
        self._symbol = symbol or FakeSymbol()
        self._render = render

    def value(self):
        return self._value

    def label(self):
        return self._label

    def symbol(self):
        return self._symbol

    def renderState(self):
        return self._render


class FakeCategorizedRenderer:
    def __init__(self, categories):
        self._categories = categories

    def categories(self):
        return self._categories


class TestBuildAllClassesPart:
    def _dialog(self, monkeypatch, geometryType):
        monkeypatch.setattr(legendsModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)
        dialog = _dialog()

        class _Layer:
            def geometryType(self):
                return geometryType

            def renderer(self):
                return "LIVE-RENDERER"

        dialog.currentLayer = _Layer()
        return dialog

    def test_snapshot_uses_the_passed_renderer_not_the_live_layer(self, monkeypatch):
        dialog = self._dialog(monkeypatch, legendsModule.WKB_POINT_GEOMETRY)
        renderer = FakeCategorizedRenderer([
            FakeCategory("Open", label="Open valves", symbol=FakeSymbol("#aabbcc", size=3.0)),
            FakeCategory(None, label="#NA", render=False),
        ])
        part = dialog.buildAllClassesPart(renderer)
        assert part == {"classes": [
            {"value": "Open", "label": "Open valves", "color": "#aabbcc", "size": 3.0, "render": True},
            {"value": None, "label": "#NA", "color": "#112233", "size": 2.5, "render": False},
        ]}

    def test_line_geometry_records_widths(self, monkeypatch):
        dialog = self._dialog(monkeypatch, legendsModule.WKB_LINE_GEOMETRY)
        part = dialog.buildAllClassesPart(FakeCategorizedRenderer([
            FakeCategory("A", symbol=FakeSymbol(width=1.25)),
        ]))
        assert part["classes"][0]["size"] == 1.25

    def test_non_categorized_renderer_returns_none(self, monkeypatch):
        dialog = self._dialog(monkeypatch, legendsModule.WKB_POINT_GEOMETRY)
        assert dialog.buildAllClassesPart("rule-based") is None


class TestStrategyPartReasons:
    """Why a part cannot be recalculated; an empty reason means it can."""

    def _dialog(self, sourceRuleRenderer=None, colorsSetByHand=False, fieldIndex=2):
        dialog = _dialog()
        dialog._sourceRuleRenderer = sourceRuleRenderer
        dialog.tr = lambda text: text
        dialog.currentColorMode = lambda: "Manual" if colorsSetByHand else "Random"
        dialog.cbSizes = MagicMock()
        dialog.cbSizes.currentText.return_value = "Linear"
        dialog.currentLayer = MagicMock()
        dialog.currentLayer.fields.return_value.indexFromName.return_value = fieldIndex
        return dialog

    def test_a_plain_categorized_legend_can_recalculate_everything(self):
        dialog = self._dialog()
        assert (dialog.classesPartReason(), dialog.sizesPartReason(), dialog.colorsPartReason()) == ("", "", "")

    def test_a_rule_based_legend_is_always_saved_as_shown(self):
        # Replaying colors would rebuild Link Status or the hydraulic sectors as plain
        # categories and lose their rules; sizes would silently do nothing.
        dialog = self._dialog(sourceRuleRenderer="RULES")
        reasons = {dialog.classesPartReason(), dialog.sizesPartReason(), dialog.colorsPartReason()}
        assert reasons == {dialog.ruleBasedLegendReason()}
        assert not dialog.canBuildColorsPart() and not dialog.canBuildSizesPart()

    def test_colors_set_by_hand_say_how_to_change_that(self):
        dialog = self._dialog(colorsSetByHand=True)
        assert "Choose Random, a ramp or a palette" in dialog.colorsPartReason()
        assert "choose Random, a ramp or a palette in Colors first" in dialog.classesPartReason()

    def test_classes_from_a_formula_cannot_be_rebuilt(self):
        # Demand Builder classifies a CASE expression: there is no column to read values from.
        assert "formula" in self._dialog(fieldIndex=-1).classesPartReason()

    def test_a_kept_part_is_shown_as_such(self):
        dialog = self._dialog()
        assert dialog.strategyPartOption("Sizes", "Sizes: Linear", "why") == ("%1: kept as shown".replace("%1", "Sizes"), "why")
        assert dialog.strategyPartOption("Sizes", "Sizes: Linear", "") == ("Sizes: Linear", "")


class TestLoadBranching:
    def _dialog(self, monkeypatch, strategy):
        # The dialog reports the outcome through QMessageBox, whose real signature
        # wants a QWidget parent -- and the dialog base is stubbed for the whole suite.
        monkeypatch.setattr(legendsModule, "QMessageBox", MagicMock())
        dialog = _dialog()
        dialog.calls = []

        class _Layer:
            def customProperty(self, key, default=None):
                return "qgisred_pipes" if key == "qgisred_identifier" else default

            def name(self):
                return "Pipes"

        dialog.currentLayer = _Layer()
        dialog.tr = lambda text: text
        dialog.getElementNameForIdentifier = lambda identifier: "Pipes"
        dialog.getProjectStyleFilename = lambda name: "Net_Pipes.qml"
        dialog.getStyleBasename = lambda name: name
        dialog.getProjectDirectoryFromUtils = lambda: "/project"
        dialog.getStyleFolder = lambda globalStyle: "/global"
        dialog.readStrategyFromStyleFile = lambda path: strategy
        dialog.applyStyleFileToLayer = lambda path: dialog.calls.append("file")
        dialog.applyStrategyToDialog = lambda s: dialog.calls.append("strategy")
        dialog.applyLegend = lambda: dialog.calls.append("apply")
        # The loader resolves the file through QGISRedStylingUtils.findStyleFile, which
        # lists the folder and matches in lowercase — so the stub is listdir, not exists.
        monkeypatch.setattr(os, "listdir", lambda folder: ["Net_Pipes.qml"])
        return dialog

    def _strategy(self, parts):
        return {"schema": "qgisred.legendStrategy.v2", "mode": "categorized", "field": "Class", "parts": parts}

    def test_pure_snapshot_goes_straight_onto_the_layer(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["allClasses"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["file"]

    def test_combined_strategy_pins_classes_then_applies_parts(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["allClasses", "colors", "sizes"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["file", "strategy", "apply"]

    def test_dynamic_strategy_regenerates_on_top_of_the_saved_classes(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["colors"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["file", "strategy", "apply"]

    def test_default_style_never_reads_a_strategy(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["colors"]))
        dialog.pluginFolder = "/plugin"
        monkeypatch.setattr(os, "listdir", lambda folder: ["Pipes.qml.bak"])
        dialog.loadDefaultStyle()
        assert dialog.calls == ["file"]

    @pytest.mark.parametrize("load, expected", [
        ("loadProjectStyle", "No style has been saved for this layer in the layerStyles folder of the project."),
        ("loadGlobalStyle", "No style has been saved for this layer at the global level."),
    ])
    def test_a_missing_saved_style_gets_its_own_message(self, monkeypatch, load, expected):
        dialog = self._dialog(monkeypatch, None)
        monkeypatch.setattr(os, "listdir", lambda folder: [])
        getattr(dialog, load)()
        assert dialog.calls == []
        warning = legendsModule.QMessageBox.warning
        warning.assert_called_once()
        assert warning.call_args[0][2] == expected
