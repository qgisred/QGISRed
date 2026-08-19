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
    def __init__(self, checked):
        self._checked = checked

    def isChecked(self):
        return self._checked


class TestSaveStrategyDialog:
    def _strategyDialog(self, isCategorical, structural, sizes, colors):
        dialog = QGISRedSaveStrategyDialog.__new__(QGISRedSaveStrategyDialog)
        dialog.isCategorical = isCategorical
        dialog.ckStructural = FakeCheckBox(structural)
        dialog.ckSizes = FakeCheckBox(sizes)
        dialog.ckColors = FakeCheckBox(colors)
        return dialog

    def test_the_mutual_exclusion_hook_is_gone(self):
        # vars(), not hasattr(): the QDialog test stub answers any attribute.
        assert "onStructuralToggled" not in vars(QGISRedSaveStrategyDialog)

    def test_all_three_parts_can_be_selected_together(self):
        dialog = self._strategyDialog(True, True, True, True)
        assert dialog.selectedParts() == ["allClasses", "sizes", "colors"]

    def test_numeric_structural_maps_to_intervals(self):
        dialog = self._strategyDialog(False, True, True, True)
        assert dialog.selectedParts() == ["intervals", "sizes", "colors"]


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


class TestBuildableParts:
    def _dialog(self, sourceRuleRenderer):
        dialog = _dialog()
        dialog._sourceRuleRenderer = sourceRuleRenderer

        class _Table:
            def rowCount(self):
                return 3

        dialog.tableView = _Table()
        dialog.canBuildIntervalsPart = lambda: False
        dialog.canBuildSizesPart = lambda: False
        dialog.canBuildColorsPart = lambda: False
        return dialog

    def test_all_classes_offered_for_plain_categorized(self):
        assert self._dialog(None).getBuildableStrategyParts() == ["allClasses"]

    def test_all_classes_not_offered_for_rule_based_layers(self):
        assert self._dialog("RULES").getBuildableStrategyParts() == []


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
        dialog.getElementNameForIdentifier = lambda identifier: "Pipes"
        dialog.getProjectStyleFilename = lambda name: "Net_Pipes.qml"
        dialog.getProjectDirectoryFromUtils = lambda: "/project"
        dialog.readStrategyFromStyleFile = lambda path: strategy
        dialog.loadLiteralStyleIntoDialog = lambda path: dialog.calls.append("literal")
        dialog.applyStrategyToDialog = lambda s: dialog.calls.append("strategy")
        # The loader resolves the file through QGISRedStylingUtils.findStyleFile, which
        # lists the folder and matches in lowercase — so the stub is listdir, not exists.
        monkeypatch.setattr(os, "listdir", lambda folder: ["Net_Pipes.qml"])
        return dialog

    def _strategy(self, parts):
        return {"schema": "qgisred.legendStrategy.v2", "mode": "categorized", "field": "Class", "parts": parts}

    def test_pure_snapshot_loads_as_literal_only(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["allClasses"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["literal"]

    def test_combined_strategy_pins_classes_then_applies_parts(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["allClasses", "colors", "sizes"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["literal", "strategy"]

    def test_dynamic_strategy_skips_the_literal_load(self, monkeypatch):
        dialog = self._dialog(monkeypatch, self._strategy(["colors"]))
        dialog.loadProjectStyle()
        assert dialog.calls == ["strategy"]
