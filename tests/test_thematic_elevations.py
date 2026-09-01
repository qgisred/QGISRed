# -*- coding: utf-8 -*-
"""The junction elevations thematic map cannot ship fixed classes: elevations go
from flat networks to hundreds of metres of relief, against any datum. The style
only fixes the look of five classes (colors, 2.5 mm circles); the dialog recomputes
the breaks from the data with Pretty Breaks, shifts them so a value sitting on a
break reads in the upper class, widens the outer classes, and writes the project's
length unit into legend, labels and map tip. One style therefore serves SI and US.
"""
import os
import re
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock

import pytest

from QGISRed.tools.utils import qgisred_thematicmaps_builder as builder_module
from QGISRed.tools.utils.qgisred_thematicmaps_builder import QGISRedThematicMapsBuilder

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLE_PATH = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", "JunctionElevations.qml.bak")
DIALOG_SOURCE = os.path.join(PLUGIN_ROOT, "ui", "queries", "qgisred_thematicmaps_dialog.py")
QUERIES_SOURCE = os.path.join(PLUGIN_ROOT, "tools", "utils", "qgisred_thematicmaps_queries.py")

# Blue (lowest) to red (highest), as specified for the map: #446ee7, #7bddee,
# #84f71e, #f7ba22, #f21835.
DOCUMENT_COLORS = ["68,110,231,255", "123,221,238,255", "132,247,30,255", "247,186,34,255", "242,24,53,255"]


def loadStyle():
    return ET.parse(STYLE_PATH).getroot()


def markerOption(symbol, name):
    return symbol.find("layer/Option/Option[@name='%s']" % name).get("value")


class TestShippedStyle:

    def test_five_placeholder_classes_carry_the_document_colors_and_size(self):
        renderer = loadStyle().find("renderer-v2")
        assert renderer.get("type") == "graduatedSymbol"
        assert renderer.get("attr") == "Elevation"
        assert renderer.get("graduatedMethod") == "GraduatedColor"
        assert renderer.find("classificationMethod").get("id") == "Pretty"

        ranges = renderer.findall("ranges/range")
        assert len(ranges) == 5
        symbols = {symbol.get("name"): symbol for symbol in renderer.findall("symbols/symbol")}
        for classRange, color in zip(ranges, DOCUMENT_COLORS):
            symbol = symbols[classRange.get("symbol")]
            assert markerOption(symbol, "color").startswith(color)
            assert markerOption(symbol, "size") == "2.5"
            assert markerOption(symbol, "name") == "circle"
            # Nothing inherited from the Junctions style may override the class
            # look per feature (the input style sizes and fills by demand).
            assert symbol.find("layer/data_defined_properties/Option/Option[@name='properties']").get("value") is None
            assert symbol.find("layer/data_defined_properties/Option/Option[@name='properties']/Option") is None

    def test_source_symbol_is_a_plain_circle_for_the_recomputed_classes(self):
        # updateClasses clones the source symbol into every new class.
        source = loadStyle().find("renderer-v2/source-symbol/symbol")
        assert markerOption(source, "size") == "2.5"
        assert markerOption(source, "name") == "circle"
        assert source.find("layer/data_defined_properties/Option/Option[@name='properties']/Option") is None

    def test_labels_and_map_tip_leave_the_unit_to_the_dialog(self):
        root = loadStyle()
        textStyle = root.find("labeling/settings/text-style")
        assert textStyle.get("isExpression") == "1"
        assert textStyle.get("fieldName") == "round(\"Elevation\",1) ||' [units]'"
        assert textStyle.get("fontSize") == "8"
        assert textStyle.get("textColor").startswith("193,148,39,255")  # #c19427
        placement = root.find("labeling/settings/placement")
        assert (placement.get("dist"), placement.get("distUnits")) == ("2", "Point")
        assert (placement.get("labelMarginDistance"), placement.get("labelMarginDistanceUnit")) == ("3", "Point")

        mapTip = root.find("mapTip")
        assert mapTip.get("enabled") == "1"
        assert mapTip.text == "[%'Elev '|| round(\"Elevation\",1) ||' [units]'%]"

    def test_style_is_read_only_and_carries_no_foreign_identity(self):
        root = loadStyle()
        assert root.get("readOnly") == "1"
        assert root.get("labelsEnabled") == "0"
        # A qgisred_identifier copied from the Junctions layer would turn the
        # query layer into an input layer for the rest of the plugin.
        assert root.find("customproperties/Option/Option[@name='qgisred_identifier']") is None
        columns = {column.get("name"): column.get("hidden")
                   for column in root.findall("attributetableconfig/columns/column")}
        assert columns["Elevation"] == "0"
        assert columns["BaseDem"] == "1"


class TestDialogWiring:

    def test_one_style_serves_both_unit_systems_and_is_shipped(self):
        with open(QUERIES_SOURCE, encoding="utf-8") as source:
            catalogue = source.read()
        with open(DIALOG_SOURCE, encoding="utf-8") as source:
            dialog = source.read()
        assert "'qml_file': 'JunctionElevations.qml'" in catalogue
        assert not re.search(r"junction_elevation_\{units\}", catalogue)
        assert os.path.exists(STYLE_PATH)
        # The option must be reachable: it was hidden while unimplemented.
        assert "self.cbJunctionsElevation.hide()" not in dialog


class _GraduatedRendererStub:
    """Records what the dialog does to the renderer; updateClasses returns the
    classes handed to the stub as Pretty Breaks would compute them."""

    def __init__(self, shippedColors, computedBreaks):
        self._ranges = [self._range(lower, upper, color)
                        for (lower, upper), color in zip([(0, 1)] * len(shippedColors), shippedColors)]
        self._computedBreaks = computedBreaks
        self.sourceSymbol = None
        self.sourceColorRamp = None
        self.classificationMethod = None
        self.updatedClassesWith = None
        self.lowerValues = {}
        self.upperValues = {}
        self.labels = {}
        self.addedClasses = []

    @staticmethod
    def _range(lower, upper, color):
        classRange = MagicMock()
        classRange.lowerValue.return_value = lower
        classRange.upperValue.return_value = upper
        classRange.symbol.return_value.color.return_value = color
        return classRange

    def ranges(self):
        return list(self._ranges)

    def setSourceSymbol(self, symbol):
        self.sourceSymbol = symbol

    def setSourceColorRamp(self, ramp):
        self.sourceColorRamp = ramp

    def setClassificationMethod(self, method):
        self.classificationMethod = method

    def updateClasses(self, layer, classCount):
        self.updatedClassesWith = (layer, classCount)
        self._ranges = [self._range(lower, upper, "computed")
                        for lower, upper in zip(self._computedBreaks, self._computedBreaks[1:])]

    def updateRangeLowerValue(self, index, value):
        self.lowerValues[index] = value

    def updateRangeUpperValue(self, index, value):
        self.upperValues[index] = value

    def updateRangeLabel(self, index, label):
        self.labels[index] = label

    def addClass(self, classRange):
        self.addedClasses.append(classRange)


@pytest.fixture
def graduatedStub(monkeypatch):
    monkeypatch.setattr(builder_module, "QgsGraduatedSymbolRenderer", _GraduatedRendererStub)
    monkeypatch.setattr(builder_module, "QgsRendererRange", lambda *args: args)
    # Real QGIS rejects the plain color names the stub hands out.
    monkeypatch.setattr(builder_module, "QgsGradientStop", MagicMock())
    monkeypatch.setattr(builder_module, "QgsGradientColorRamp", MagicMock())
    monkeypatch.setattr(builder_module, "QgsClassificationPrettyBreaks", MagicMock())
    return _GraduatedRendererStub


def _builder():
    return object.__new__(QGISRedThematicMapsBuilder)


class TestClassifyElevationByPrettyBreaks:

    def test_breaks_are_recomputed_shifted_and_labelled_with_the_unit(self, graduatedStub):
        # Pretty Breaks on a 3.5 .. 97 m network: min, 20, 40, 60, 80, max.
        renderer = graduatedStub(["blue", "cyan", "green", "yellow", "red"], [3.5, 20, 40, 60, 80, 97])
        layer = MagicMock()
        layer.renderer.return_value = renderer

        _builder().classifyElevationByPrettyBreaks(layer, "m")

        assert renderer.updatedClassesWith == (layer, 5)
        assert renderer.labels == {0: "< 20 m", 1: "20 < 40 m", 2: "40 < 60 m", 3: "60 < 80 m", 4: ">= 80 m"}
        # A junction at exactly 20 m must read in "20 < 40 m", so the break
        # moves down by 0.001; the outer classes swallow any edit that follows.
        assert renderer.lowerValues == {0: -100000, 1: 19.999, 2: 39.999, 3: 59.999, 4: 79.999}
        assert renderer.upperValues == {0: 19.999, 1: 39.999, 2: 59.999, 3: 79.999, 4: 100000}

    def test_class_look_comes_from_the_shipped_legend(self, graduatedStub):
        renderer = graduatedStub(["blue", "cyan", "green", "yellow", "red"], [0, 20, 40, 60, 80, 100])
        layer = MagicMock()
        layer.renderer.return_value = renderer
        shippedFirstSymbol = renderer.ranges()[0].symbol.return_value

        _builder().classifyElevationByPrettyBreaks(layer, "ft")

        # updateClasses clones the source symbol per class, so it must be the
        # shipped circle, and the ramp must run through the five shipped colors.
        assert renderer.sourceSymbol is shippedFirstSymbol.clone.return_value
        rampCall = builder_module.QgsGradientColorRamp.call_args
        assert rampCall.args[0] == "blue" and rampCall.args[1] == "red"
        stopCalls = [call.args for call in builder_module.QgsGradientStop.call_args_list[-3:]]
        assert stopCalls == [(0.25, "cyan"), (0.5, "green"), (0.75, "yellow")]
        assert renderer.classificationMethod is builder_module.QgsClassificationPrettyBreaks.return_value

    def test_pretty_breaks_class_count_is_honoured_whatever_it_is(self, graduatedStub):
        # R's pretty gives "about" five classes: 0 .. 300 yields six.
        renderer = graduatedStub(["blue", "cyan", "green", "yellow", "red"], [0, 50, 100, 150, 200, 250, 300])
        layer = MagicMock()
        layer.renderer.return_value = renderer

        _builder().classifyElevationByPrettyBreaks(layer, "m")

        assert renderer.labels[0] == "< 50 m"
        assert renderer.labels[5] == ">= 250 m"
        assert renderer.upperValues[5] == 100000

    def test_a_flat_network_keeps_a_single_class_instead_of_none(self, graduatedStub):
        # Pretty Breaks return no class when min == max (a new network with
        # every elevation still at 0); nothing would be drawn.
        renderer = graduatedStub(["blue", "cyan", "green", "yellow", "red"], [])
        layer = MagicMock()
        layer.renderer.return_value = renderer
        layer.minimumValue.return_value = 0.0

        _builder().classifyElevationByPrettyBreaks(layer, "m")

        assert len(renderer.addedClasses) == 1
        lower, upper, _symbol, label = renderer.addedClasses[0]
        assert (lower, upper, label) == (-100000, 100000, "0 m")
        assert renderer.labels == {}

    def test_other_renderers_are_left_alone(self, graduatedStub):
        layer = MagicMock()
        layer.renderer.return_value = MagicMock()

        _builder().classifyElevationByPrettyBreaks(layer, "m")

        layer.renderer.return_value.updateClasses.assert_not_called()


class TestBreakFormatting:

    @pytest.mark.parametrize("value, text", [
        (20.0, "20"), (0.5, "0.5"), (1500.0, "1500"), (2.25, "2.25"), (-5.0, "-5"), (0.0, "0"),
        (0.30000000000000004, "0.3"),
    ])
    def test_pretty_values_print_without_spurious_decimals(self, value, text):
        assert _builder().formatBreakValue(value) == text


class TestLengthUnitsInLabelsAndMapTip:

    def test_placeholder_is_replaced_in_map_tip_and_label_expression(self, monkeypatch):
        monkeypatch.setattr(builder_module, "QgsVectorLayerSimpleLabeling", lambda settings: ("labeling", settings))
        layer = MagicMock()
        layer.mapTipTemplate.return_value = "[%'Elev '|| round(\"Elevation\",1) ||' [units]'%]"
        labelSettings = MagicMock()
        labelSettings.fieldName = "round(\"Elevation\",1) ||' [units]'"
        layer.labeling.return_value.settings.return_value = labelSettings

        _builder().applyLengthUnitsToElevationStyle(layer, "ft")

        layer.setMapTipTemplate.assert_called_once_with("[%'Elev '|| round(\"Elevation\",1) ||' ft'%]")
        assert labelSettings.fieldName == "round(\"Elevation\",1) ||' ft'"
        layer.setLabeling.assert_called_once_with(("labeling", labelSettings))

    def test_a_layer_without_labeling_only_gets_its_map_tip(self):
        layer = MagicMock()
        layer.mapTipTemplate.return_value = "[units]"
        layer.labeling.return_value = None

        _builder().applyLengthUnitsToElevationStyle(layer, "m")

        layer.setMapTipTemplate.assert_called_once_with("m")
        layer.setLabeling.assert_not_called()


class TestUnitResolution:

    @pytest.mark.parametrize("unitSystem, units", [("SI", "m"), ("US", "ft")])
    def test_adaptation_resolves_the_length_unit_of_the_project(self, monkeypatch, unitSystem, units):
        from QGISRed.tools.utils.qgisred_project_utils import QGISRedProjectUtils
        monkeypatch.setattr(QGISRedProjectUtils, "getUnits", staticmethod(lambda: unitSystem))
        builder = _builder()
        seen = {}
        builder.classifyElevationByPrettyBreaks = lambda layer, units: seen.setdefault("classify", units)
        builder.applyLengthUnitsToElevationStyle = lambda layer, units: seen.setdefault("style", units)

        builder.adaptElevationDerivedLayer(MagicMock())

        assert seen == {"classify": units, "style": units}
