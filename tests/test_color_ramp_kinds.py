# -*- coding: utf-8 -*-
"""How the colors of a ramp or a palette reach the classes of a legend, by kind.

Interpolated spreads the palette over the classes and always keeps its first and last
colors; Sequential hands the colors out in the order they are declared; Labeled gives
each class the color labeled with its value. The legend editor and the replay of a saved
strategy both go through these, so they cannot disagree.
"""
import pytest

import QGISRed.tools.utils.qgisred_styling_utils as stylingModule
from QGISRed.compat import STYLE_ENTITY_COLORRAMP
from QGISRed.tools.utils.qgisred_styling_utils import (
    QGISRedStylingUtils,
    PALETTE_KIND_LABELED,
    PALETTE_KIND_SEQUENTIAL,
    PALETTE_KIND_INTERPOLATED,
    RAMP_KIND_MORE_COLORS,
    RAMP_KIND_THREE_COLORS,
    RAMP_KIND_TWO_COLORS,
)


class FakeColor:
    def __init__(self, red, green=0, blue=0):
        self.rgb = (red, green, blue)

    def red(self):
        return self.rgb[0]

    def green(self):
        return self.rgb[1]

    def blue(self):
        return self.rgb[2]


class FakePalette:
    def __init__(self, reds, labels=None):
        self._colors = [FakeColor(red) for red in reds]
        self._labels = labels or [str(red) for red in reds]

    def colors(self):
        return list(self._colors)

    def fetchColors(self):
        return list(zip(self._colors, self._labels))


class FakeGradient:
    def __init__(self, innerStops=0):
        self._innerStops = innerStops

    def stops(self):
        return [object()] * self._innerStops

    def color(self, position):
        return ("gradient", round(position, 3))


@pytest.fixture(autouse=True)
def plainColors(monkeypatch):
    """QColor is mocked: stand in for it with something that keeps its components."""
    class FakeQColor:
        def __new__(cls, *args):
            return args[0] if len(args) == 1 else FakeColor(*args)

        @staticmethod
        def fromRgb(red, green, blue):
            return (red, green, blue)

    monkeypatch.setattr(stylingModule, "QColor", FakeQColor)
    monkeypatch.setattr(stylingModule, "NULL", object())


def _reds(palette, kind, values, invert=False):
    utils = QGISRedStylingUtils("", "")
    colors = [utils.rampClassColor(palette, kind, value, index, len(values), invert) for index, value in enumerate(values)]
    return [None if color is None else color.red() for color in colors]


SEVEN = [0, 10, 20, 30, 40, 50, 60]


class TestInterpolatedPalette:
    def test_as_many_classes_as_colors_takes_them_all_in_order(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_INTERPOLATED, list("abcdefg")) == SEVEN

    def test_fewer_classes_pick_real_colors_and_keep_both_ends(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_INTERPOLATED, list("abcde")) == [0, 20, 30, 50, 60]

    @pytest.mark.parametrize("classCount", range(2, 8))
    def test_the_last_color_is_never_lost(self, classCount):
        # The old algorithm floored the position and could stop short of the last color.
        reds = _reds(FakePalette(SEVEN), PALETTE_KIND_INTERPOLATED, ["x"] * classCount)
        assert (reds[0], reds[-1]) == (0, 60)

    def test_more_classes_than_colors_blend_between_neighbours(self):
        assert _reds(FakePalette([0, 100]), PALETTE_KIND_INTERPOLATED, list("abcde")) == [0, 25, 50, 75, 100]

    def test_a_single_class_takes_the_first_color(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_INTERPOLATED, ["a"]) == [0]

    def test_invert_hands_the_same_colors_out_backwards(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_INTERPOLATED, list("abcde"), invert=True) == [60, 50, 30, 20, 0]


class TestSequentialPalette:
    def test_colors_come_in_the_order_they_are_declared(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_SEQUENTIAL, list("abc")) == [0, 10, 20]

    def test_more_classes_than_colors_start_over(self):
        assert _reds(FakePalette([0, 10, 20]), PALETTE_KIND_SEQUENTIAL, list("abcde")) == [0, 10, 20, 0, 10]

    def test_invert_hands_the_same_colors_out_backwards(self):
        assert _reds(FakePalette(SEVEN), PALETTE_KIND_SEQUENTIAL, list("abc"), invert=True) == [20, 10, 0]


class TestLabeledPalette:
    PALETTE = FakePalette([1, 2, 3], ["CI, FG, FF", "PVC", "NULL"])

    def test_each_class_takes_the_color_labeled_with_its_value(self):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, ["PVC", "FG"]) == [2, 1]

    def test_the_order_of_the_classes_does_not_matter(self):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, ["FG", "PVC"]) == [1, 2]

    def test_case_and_spaces_do_not_matter(self):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, [" pvc ", "ff"]) == [2, 1]

    @pytest.mark.parametrize("missing", [None, "", "#NA", "NULL"])
    def test_a_missing_value_goes_by_the_null_label(self, missing):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, [missing]) == [3]

    def test_a_value_without_a_label_is_left_to_the_caller(self):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, ["Copper"]) == [None]

    def test_invert_means_nothing_for_labels(self):
        assert _reds(self.PALETTE, PALETTE_KIND_LABELED, ["PVC", "FG"], invert=True) == [2, 1]

    def test_status_values_with_brackets_and_signs_match(self):
        palette = FakePalette([1, 2], ["Closed, Closed (H>Hmax), Closed (Q<0)", "Open, Open (Q>Qmax)"])
        assert _reds(palette, PALETTE_KIND_LABELED, ["Closed (Q<0)", "Open (Q>Qmax)"]) == [1, 2]

    def test_an_unlabeled_class_falls_back_to_its_own_stable_color(self):
        utils = QGISRedStylingUtils("", "")
        utils.rampClassColor = lambda *args: None
        fallback = utils.resolveCategoryColor("Copper", 0, 1, self.PALETTE, False, PALETTE_KIND_LABELED)
        again = utils.resolveCategoryColor("Copper", 5, 9, self.PALETTE, False, PALETTE_KIND_LABELED)
        assert fallback is not None and fallback == again


class TestGradientRamp:
    def test_it_is_sampled_evenly_end_to_end(self):
        utils = QGISRedStylingUtils("", "")
        colors = [utils.rampClassColor(FakeGradient(), RAMP_KIND_TWO_COLORS, None, index, 3, False) for index in range(3)]
        assert colors == [("gradient", 0.0), ("gradient", 0.5), ("gradient", 1.0)]

    def test_a_ramp_of_unknown_kind_is_sampled_like_a_gradient(self):
        # Strategies saved before kinds existed only name their ramp.
        assert QGISRedStylingUtils("", "").rampClassColor(FakeGradient(), None, None, 1, 3, True) == ("gradient", 0.5)


class FakeStyle:
    def __init__(self, ramps, tags=None):
        self.ramps, self.tags = ramps, tags or {}

    def colorRamp(self, name):
        return self.ramps.get(name)

    def tagsOfSymbol(self, entity, name):
        assert entity == STYLE_ENTITY_COLORRAMP
        return self.tags.get(name, [])


class TestColorRampKind:
    @pytest.mark.parametrize("innerStops, kind", [(0, RAMP_KIND_TWO_COLORS), (1, RAMP_KIND_THREE_COLORS),
                                                  (2, RAMP_KIND_MORE_COLORS), (3, RAMP_KIND_MORE_COLORS)])
    def test_a_ramp_is_told_by_its_number_of_colors(self, innerStops, kind):
        style = FakeStyle({"ramp": FakeGradient(innerStops)})
        assert QGISRedStylingUtils.colorRampKind(style, "ramp") == kind

    @pytest.mark.parametrize("kind", [PALETTE_KIND_INTERPOLATED, PALETTE_KIND_SEQUENTIAL, PALETTE_KIND_LABELED])
    def test_a_palette_is_told_by_its_tag(self, kind):
        style = FakeStyle({"palette": FakePalette(SEVEN)}, {"palette": ["Palettes", kind]})
        assert QGISRedStylingUtils.colorRampKind(style, "palette") == kind

    def test_an_untagged_palette_is_interpolated(self):
        assert QGISRedStylingUtils.colorRampKind(FakeStyle({"palette": FakePalette(SEVEN)}), "palette") == PALETTE_KIND_INTERPOLATED

    def test_an_unknown_ramp_has_no_kind(self):
        assert QGISRedStylingUtils.colorRampKind(FakeStyle({}), "missing") is None
