# -*- coding: utf-8 -*-
"""Every size of a style is expressed in millimetres.

The shipped styles used to mix pixels and millimetres, so the same number in the legend
editor meant different thicknesses. They are all millimetres now, and a style the user
saved before that is converted when it is loaded, keeping the look it had.
"""
import glob
import json
import os
import re

import pytest

from QGISRed.compat import RENDER_UNIT_MILLIMETERS, RENDER_UNIT_PIXELS, RENDER_UNIT_POINTS
from QGISRed.compat import SL_PROP_SIZE, SL_PROP_STROKE_WIDTH
from QGISRed.tools.utils import qgisred_styling_utils as stylingModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIXEL = 25.4 / 96
POINT = 25.4 / 72


class _FakeProperty:
    def __init__(self, expression):
        self.expression = expression

    def isActive(self):
        return True

    def expressionString(self):
        return self.expression


class _FakeProperties:
    def __init__(self, expressions):
        self.expressions = expressions

    def property(self, key):
        expression = self.expressions.get(key)
        return _FakeProperty(expression) if expression else None


class _FakeSymbolLayer:
    """A symbol layer exposing only the accessors it is given, like the real classes do."""

    def __init__(self, subSymbol=None, expressions=None, **sizes):
        self._subSymbol = subSymbol
        self._expressions = dict(expressions or {})
        for name, (value, unit) in sizes.items():
            self._addAccessor(name, value, unit)

    def _addAccessor(self, name, value, unit):
        state = {"value": value, "unit": unit}
        capitalised = name[0].upper() + name[1:]
        setattr(self, name, lambda: state["value"])
        setattr(self, "set" + capitalised, lambda newValue: state.update(value=newValue))
        setattr(self, name + "Unit", lambda: state["unit"])
        setattr(self, "set" + capitalised + "Unit", lambda newUnit: state.update(unit=newUnit))

    def subSymbol(self):
        return self._subSymbol

    def dataDefinedProperties(self):
        return _FakeProperties(self._expressions)

    def setDataDefinedProperty(self, key, newProperty):
        self._expressions[key] = newProperty


class _FakeSymbol:
    def __init__(self, *symbolLayers):
        self._symbolLayers = list(symbolLayers)

    def symbolLayers(self):
        return self._symbolLayers


@pytest.fixture(autouse=True)
def expressionsAsText(monkeypatch):
    """QgsProperty is mocked: keep the rewritten expression as plain text to assert on."""
    monkeypatch.setattr(stylingModule.QgsProperty, "fromExpression", lambda expression: expression)


class TestConvertSymbolSizes:
    def test_a_pixel_line_keeps_its_look_in_millimetres(self):
        line = _FakeSymbolLayer(width=(1.5, RENDER_UNIT_PIXELS))

        factor = QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(line))

        assert factor == pytest.approx(PIXEL)
        assert line.width() == pytest.approx(0.397)
        assert line.widthUnit() == RENDER_UNIT_MILLIMETERS

    def test_points_use_their_own_factor(self):
        marker = _FakeSymbolLayer(size=(6, RENDER_UNIT_POINTS))

        QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(marker))

        assert marker.size() == pytest.approx(round(6 * POINT, 3))

    def test_millimetres_are_left_alone(self):
        line = _FakeSymbolLayer(width=(0.8, RENDER_UNIT_MILLIMETERS), offset=(0, RENDER_UNIT_MILLIMETERS))

        assert QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(line)) is None
        assert line.width() == 0.8

    def test_every_size_of_a_layer_is_converted_not_only_the_first(self):
        marker = _FakeSymbolLayer(size=(10, RENDER_UNIT_PIXELS), strokeWidth=(4.6, RENDER_UNIT_PIXELS))

        QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(marker))

        assert marker.size() == pytest.approx(2.646)
        assert marker.strokeWidth() == pytest.approx(1.217)

    def test_a_marker_line_is_converted_through_its_marker(self):
        # Its width() is the marker size: scaling it as a line width would shrink the icon.
        icon = _FakeSymbolLayer(size=(5, RENDER_UNIT_MILLIMETERS), strokeWidth=(2, RENDER_UNIT_PIXELS))
        markerLine = _FakeSymbolLayer(subSymbol=_FakeSymbol(icon), width=(5, RENDER_UNIT_PIXELS))

        QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(markerLine))

        assert markerLine.width() == 5
        assert icon.size() == 5
        assert icon.strokeWidth() == pytest.approx(0.529)

    def test_the_numbers_of_a_size_expression_follow_the_unit(self):
        line = _FakeSymbolLayer(width=(2.6, RENDER_UNIT_PIXELS),
                                expressions={SL_PROP_STROKE_WIDTH: "if(\"Type\" = 'SC', 2, 0)"})

        QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(line))

        assert line._expressions[SL_PROP_STROKE_WIDTH] == "if(\"Type\" = 'SC', 0.529, 0)"

    def test_an_expression_already_in_millimetres_is_not_scaled(self):
        # The circle of isolated segments: pixel stroke, but its size expression is in mm.
        circle = _FakeSymbolLayer(size=(0, RENDER_UNIT_MILLIMETERS), strokeWidth=(2, RENDER_UNIT_PIXELS),
                                  expressions={SL_PROP_SIZE: "if(\"Type\" = 'SC', 2, 0)"})

        QGISRedStylingUtils.convertSymbolSizesToMillimeters(_FakeSymbol(circle))

        assert circle._expressions[SL_PROP_SIZE] == "if(\"Type\" = 'SC', 2, 0)"


class _FakeLayer:
    def __init__(self, strategy=None):
        self.properties = {"qgisred_legend_strategy": json.dumps(strategy)} if strategy else {}

    def customProperty(self, name):
        return self.properties.get(name)

    def setCustomProperty(self, name, value):
        self.properties[name] = value

    def sizes(self):
        return json.loads(self.properties["qgisred_legend_strategy"])["sizes"]


class TestConvertStrategySizes:
    def test_sizes_saved_before_millimetres_are_scaled_once(self):
        layer = _FakeLayer({"sizes": {"mode": "Linear", "value": 2, "min": 1.5, "max": 3}})

        QGISRedStylingUtils()._convertStrategySizesToMillimeters(layer, PIXEL)

        assert layer.sizes() == {"mode": "Linear", "value": 0.529, "min": 0.397, "max": 0.794, "unit": "MM"}

    def test_sizes_already_in_millimetres_are_kept(self):
        layer = _FakeLayer({"sizes": {"mode": "Equal", "value": 0.8, "min": 0, "max": 0, "unit": "MM"}})

        QGISRedStylingUtils()._convertStrategySizesToMillimeters(layer, PIXEL)

        assert layer.sizes()["value"] == 0.8

    def test_a_layer_without_a_strategy_is_left_alone(self):
        layer = _FakeLayer()

        QGISRedStylingUtils()._convertStrategySizesToMillimeters(layer, PIXEL)

        assert layer.properties == {}


class TestShippedStylesAreInMillimetres:
    @pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", "*.qml.bak"))),
                             ids=os.path.basename)
    def test_no_size_is_declared_in_pixels(self, path):
        with open(path, encoding="utf-8") as handle:
            text = handle.read()

        assert not re.findall(r'(?:value|v)="Pixel"', text)
