# -*- coding: utf-8 -*-
"""Runtime legend-strategy application: combined allClasses+colors strategies
recolor the pinned classes in place, and later steps no longer wipe them."""
import random
import zlib

import QGISRed.tools.utils.qgisred_styling_utils as stylingModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

NULL_SENTINEL = object()


def _utils():
    return QGISRedStylingUtils("", "")


class FakeLayer:
    def __init__(self, renderer=None, fieldIndex=2):
        self._renderer = renderer
        self._fieldIndex = fieldIndex
        self.setRenderers = []

    def fields(self):
        layer = self

        class _Fields:
            def indexFromName(self, name):
                return layer._fieldIndex

        return _Fields()

    def renderer(self):
        return self._renderer

    def setRenderer(self, renderer):
        self.setRenderers.append(renderer)
        self._renderer = renderer

    def triggerRepaint(self):
        pass

    def setLabelsEnabled(self, enabled):
        pass

    def name(self):
        return "Layer"


class FakeSymbol:
    def __init__(self):
        self.appliedColor = None

    def clone(self):
        return FakeSymbol()

    def setColor(self, color):
        self.appliedColor = color


class FakeCategory:
    def __init__(self, value, label="lbl", render=True):
        self._value = value
        self._label = label
        self._render = render
        self._symbol = FakeSymbol()

    def value(self):
        return self._value

    def label(self):
        return self._label

    def symbol(self):
        return self._symbol

    def renderState(self):
        return self._render


class FakeCategorizedRenderer:
    def __init__(self, *args):
        # Accepts both FakeCategorizedRenderer(categories) in tests and the
        # QGIS constructor form QgsCategorizedSymbolRenderer(field, categories).
        if len(args) == 2:
            self._field, self._categories = args
        else:
            self._categories = args[0]
            self._field = "Class"
        self.updates = []

    def categories(self):
        return list(self._categories)

    def classAttribute(self):
        return self._field

    def updateCategorySymbol(self, index, symbol):
        self.updates.append((index, symbol))


class TestApplyLegendStrategyDispatch:
    def _recordingUtils(self):
        utils = _utils()
        utils.calls = []
        utils.applyAllClassesSnapshot = lambda layer, field, block: utils.calls.append("snapshot")
        utils.applyCategorizedColors = lambda layer, field, index, block: utils.calls.append("rebuild")
        utils.applyCategorizedColorsInPlace = lambda layer, block: utils.calls.append("inPlace")
        utils.applyGraduatedClassification = lambda layer, field, block: utils.calls.append("intervals")
        utils.applySizesStrategy = lambda layer, block: utils.calls.append("sizes")
        return utils

    def _strategy(self, parts, schema="qgisred.legendStrategy.v2"):
        strategy = {"schema": schema, "mode": "categorized", "field": "Class"}
        if parts is not None:
            strategy["parts"] = parts
        strategy["colors"] = {"source": "random"}
        return strategy

    def test_combined_strategy_recolors_in_place(self):
        utils = self._recordingUtils()
        utils.applyLegendStrategy(FakeLayer(), self._strategy(["allClasses", "colors", "sizes"]))
        assert utils.calls == ["snapshot", "inPlace", "sizes"]

    def test_colors_only_still_rebuilds_from_data(self):
        utils = self._recordingUtils()
        utils.applyLegendStrategy(FakeLayer(), self._strategy(["colors"]))
        assert utils.calls == ["rebuild"]

    def test_v1_without_parts_keeps_the_legacy_rebuild(self):
        utils = self._recordingUtils()
        utils.applyLegendStrategy(FakeLayer(), self._strategy(None, schema="qgisred.legendStrategy.v1"))
        assert utils.calls == ["rebuild"]


class TestInPlaceRecolor:
    def _recolor(self, monkeypatch, categories, colorsBlock=None):
        monkeypatch.setattr(stylingModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)
        monkeypatch.setattr(stylingModule, "NULL", NULL_SENTINEL)
        utils = _utils()
        utils.resolved = []

        def resolveCategoryColor(value, index, count, ramp, invertRamp):
            utils.resolved.append((value, index, count))
            return f"color:{value}"

        utils.resolveCategoryColor = resolveCategoryColor
        renderer = FakeCategorizedRenderer(categories)
        utils.applyCategorizedColorsInPlace(FakeLayer(renderer), colorsBlock or {"source": "random"})
        return renderer, utils

    def test_positions_are_computed_over_real_categories_only(self, monkeypatch):
        categories = [FakeCategory("A"), FakeCategory("B"), FakeCategory(NULL_SENTINEL), FakeCategory("")]
        renderer, utils = self._recolor(monkeypatch, categories)
        assert utils.resolved == [("A", 0, 2), ("B", 1, 2)]

    def test_null_stays_grey_and_catch_all_keeps_its_color(self, monkeypatch):
        categories = [FakeCategory("A"), FakeCategory(NULL_SENTINEL), FakeCategory("")]
        renderer, _utils_ = self._recolor(monkeypatch, categories)
        updatedIndexes = [index for index, _symbol in renderer.updates]
        assert 1 in updatedIndexes  # NULL recolored (grey)
        assert 2 not in updatedIndexes  # "" catch-all untouched
        realUpdate = dict(renderer.updates)[0]
        assert realUpdate.appliedColor == "color:A"

    def test_non_categorized_renderer_is_left_alone(self, monkeypatch):
        monkeypatch.setattr(stylingModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)
        monkeypatch.setattr(stylingModule, "NULL", NULL_SENTINEL)
        utils = _utils()
        layer = FakeLayer("rule-based-renderer")
        utils.applyCategorizedColorsInPlace(layer, {"source": "random"})
        assert layer.setRenderers == []


class TestDeterministicRandomColor:
    def test_seed_is_stable_across_processes(self, monkeypatch):
        captured = []

        class FakeQColor:
            @staticmethod
            def fromRgb(r, g, b):
                captured.append((r, g, b))
                return (r, g, b)

        monkeypatch.setattr(stylingModule, "QColor", FakeQColor)
        utils = _utils()
        first = utils.resolveCategoryColor("Zone1", 0, 3, None, False)
        second = utils.resolveCategoryColor("Zone1", 2, 5, None, True)
        assert first == second  # depends only on the value, not on position

        seeded = random.Random(zlib.crc32("Zone1".encode("utf-8")))
        expected = (seeded.randint(0, 255), seeded.randint(0, 255), seeded.randint(0, 255))
        assert first == expected


class TestTranslateRendererLabels:
    def _translate(self, monkeypatch, categories):
        monkeypatch.setattr(stylingModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)

        class FakeRendererCategory:
            def __init__(self, value, symbol, label):
                self._value = value
                self._symbol = symbol
                self._label = label
                self._render = True

            def value(self):
                return self._value

            def label(self):
                return self._label

            def renderState(self):
                return self._render

            def setRenderState(self, state):
                self._render = state

        monkeypatch.setattr(stylingModule, "QgsRendererCategory", FakeRendererCategory)
        utils = _utils()
        utils.tr = lambda message: message
        layer = FakeLayer(FakeCategorizedRenderer(categories))
        utils.translateRendererLabels(layer)
        return layer.setRenderers[0]._categories

    def test_custom_labels_and_visibility_survive(self, monkeypatch):
        source = FakeCategory("Zone9", label="My custom label", render=False)
        rebuiltCategories = self._translate(monkeypatch, [source])
        assert rebuiltCategories[0].label() == "My custom label"
        assert rebuiltCategories[0].renderState() is False

    def test_special_values_are_still_translated(self, monkeypatch):
        rebuiltCategories = self._translate(monkeypatch, [FakeCategory("ClosedLinks", label="whatever")])
        assert rebuiltCategories[0].label() == "Closed Links"
