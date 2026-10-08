# -*- coding: utf-8 -*-
"""The default result styles follow the Results Panel spec.

Every Node*/Link*.qml.bak is written by scripts/build_result_styles.py from one table of
classes; the files must equal what the script writes (so a hand edit does not drift from
it) and the table itself must say what the spec says, which the literals here pin down.
"""
import importlib.util
import json
import os
import re
import sqlite3
from xml.etree import ElementTree

import pytest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES_FOLDER = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")
DATABASE = os.path.join(PLUGIN_ROOT, "defaults", "qgisred_symbology_style.db.bak")

SPEC_PALETTE = ("#004eff", "#00ffff", "#00ff00", "#ffd800", "#ff3800")


def _loadScript(name):
    path = os.path.join(PLUGIN_ROOT, "scripts", name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = _loadScript("build_result_styles")
RESULT_STYLE_NAMES = [spec["name"] for spec in generator.RESULT_STYLES]


def _shipped(name):
    with open(os.path.join(STYLES_FOLDER, name + ".qml.bak"), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def _root(name):
    return ElementTree.fromstring(_shipped(name))


def _ranges(name):
    return [(float(r.get("lower")), float(r.get("upper")), r.get("label"))
            for r in _root(name).findall("renderer-v2/ranges/range")]


def _labels(name):
    return [label for _lower, _upper, label in _ranges(name)]


def _option(element, optionName):
    for option in element.iter("Option"):
        if option.get("name") == optionName:
            return option.get("value")
    return None


def _classSymbols(name):
    return _root(name).findall("renderer-v2/symbols/symbol")


def _rgb(colorText):
    return "#%02x%02x%02x" % tuple(int(part) for part in colorText.split(",")[:3])


def _classColors(name):
    colors = []
    for symbol in _classSymbols(name):
        layers = symbol.findall("layer")
        if symbol.get("type") == "marker":
            circle = next(layer for layer in layers if layer.get("class") == "SimpleMarker")
            colors.append(_rgb(_option(circle, "color")))
        else:
            colors.append(_rgb(_option(layers[0], "line_color")))
    return colors


def _sizeExpressions(name):
    return [option.get("value") for option in _root(name).iter("Option")
            if option.get("name") == "expression" and option.get("value") not in (None, "0")]


def _customProperty(name, key):
    return _option(_root(name).find("customproperties"), key)


class TestShippedFilesMatchTheGenerator:
    @pytest.mark.parametrize("spec", generator.RESULT_STYLES, ids=RESULT_STYLE_NAMES)
    def test_the_file_is_what_the_script_writes(self, spec):
        assert _shipped(spec["name"]) == generator.renderStyle(spec)

    def test_no_other_result_style_ships(self):
        shipped = sorted(name[:-len(".qml.bak")] for name in os.listdir(STYLES_FOLDER)
                         if name.endswith(".qml.bak") and name[:4] in ("Node", "Link"))
        assert shipped == sorted(RESULT_STYLE_NAMES)


class TestFixedThresholds:
    """Ranges and labels of the spec tables (Sept 2026), first class from Min, last to Max."""

    @pytest.mark.parametrize("name, labels", [
        ("NodePressureSI", ["< 0", "0 < 15", "15 < 30", "30 < 40", "40 < 50", "> 50"]),
        ("NodePressureUS", ["< 0", "0 < 20", "20 < 40", "40 < 60", "60 < 70", "> 70"]),
        ("NodeChlorine", ["< 0.2", "0.2 < 0.4", "0.4 < 0.6", "0.6 < 0.8", "> 0.8"]),
        ("NodeTrace", ["< 20", "20 < 40", "40 < 60", "60 < 80", "> 80"]),
        ("NodeAge", ["< 12", "12 < 24", "24 < 48", "48 < 72", "> 72"]),
        ("LinkVelocitySI", ["< 0.25", "0.25 < 0.5", "0.5 < 0.75", "0.75 < 1", "> 1"]),
        ("LinkVelocityUS", ["< 0.75", "0.75 < 1.5", "1.5 < 2.25", "2.25 < 3", "> 3"]),
        ("LinkHeadLossSI", ["< 0.1", "0.1 < 0.5", "0.5 < 1", "1 < 2", "> 2"]),
        ("LinkHeadLossUS", ["< 0.3", "0.3 < 1.5", "1.5 < 3", "3 < 6", "> 6"]),
        ("LinkUnitHdLoss", ["< 0.5", "0.5 < 1", "1 < 2", "2 < 5", "> 5"]),
        ("LinkFricFactor", ["< 0.01", "0.01 < 0.015", "0.015 < 0.02", "0.02 < 0.03", "> 0.03"]),
        ("LinkChlorine", ["< 0.2", "0.2 < 0.4", "0.4 < 0.6", "0.6 < 0.8", "> 0.8"]),
        ("LinkTrace", ["< 20", "20 < 40", "40 < 60", "60 < 80", "> 80"]),
        ("LinkAge", ["< 12", "12 < 24", "24 < 48", "48 < 72", "> 72"]),
    ])
    def test_labels(self, name, labels):
        assert _labels(name) == labels

    @pytest.mark.parametrize("name, minimum, maximum", [
        ("NodePressureSI", -1000, 200), ("NodePressureUS", -1000, 300), ("NodeChlorine", 0, 2), ("NodeTrace", 0, 100),
        ("NodeAge", 0, 1000), ("LinkVelocitySI", 0, 10), ("LinkVelocityUS", 0, 30), ("LinkHeadLossSI", 0, 50),
        ("LinkHeadLossUS", 0, 150), ("LinkUnitHdLoss", 0, 50), ("LinkFricFactor", 0, 1), ("LinkChlorine", 0, 2),
        ("LinkTrace", 0, 100), ("LinkAge", 0, 1000),
    ])
    def test_outer_bounds_are_the_spec_minimum_and_maximum(self, name, minimum, maximum):
        ranges = _ranges(name)
        assert ranges[0][0] == minimum
        assert ranges[-1][1] == maximum

    def test_classes_are_consecutive_and_a_value_on_a_threshold_reads_in_the_upper_class(self):
        ranges = _ranges("LinkFricFactor")
        assert [upper for _lower, upper, _label in ranges[:-1]] == [0.0095, 0.0145, 0.0195, 0.0295]
        assert [lower for lower, _upper, _label in ranges[1:]] == [0.0095, 0.0145, 0.0195, 0.0295]
        pressure = _ranges("NodePressureSI")
        assert pressure[1][1] == 14.995 and pressure[2][0] == 14.995

    def test_fixed_styles_carry_no_strategy(self):
        assert _customProperty("NodePressureSI", "qgisred_legend_strategy") is None


class TestPrettyBreakStyles:
    PRETTY = ["NodeHead", "NodeDemand", "NodeChemical", "LinkFlow", "LinkReactRate", "LinkChemical"]

    @pytest.mark.parametrize("name, field", [
        ("NodeHead", "Head"), ("NodeDemand", "Demand"), ("NodeChemical", "Quality"),
        ("LinkFlow", "abs(Flow)"), ("LinkReactRate", "ReactRate"), ("LinkChemical", "Quality"),
    ])
    def test_the_file_carries_a_pretty_breaks_strategy_over_the_results_palette(self, name, field):
        strategy = json.loads(_customProperty(name, "qgisred_legend_strategy"))

        assert strategy["schema"] == "qgisred.legendStrategy.v2"
        assert strategy["mode"] == "graduated"
        assert strategy["field"] == field
        assert strategy["parts"] == ["intervals", "colors"]
        assert strategy["intervals"]["classificationMode"] == "Pretty"
        assert strategy["intervals"]["classes"] == 5
        assert strategy["colors"] == {"source": "ramp", "rampName": "QGISRed EPANET Results", "invertRamp": False}

    @pytest.mark.parametrize("name", PRETTY)
    def test_placeholder_classes_already_wear_the_palette_and_a_source_ramp(self, name):
        root = _root(name)
        assert root.find("renderer-v2/classificationMethod").get("id") == "Pretty"
        placeholders = 6 if name == "NodeDemand" else 5
        assert len(root.findall("renderer-v2/ranges/range")) == placeholders
        assert _classColors(name)[-5:] == list(SPEC_PALETTE)
        ramp = root.find("renderer-v2/colorramp")
        assert ramp.get("name") == "[source]" and ramp.get("type") == "preset"
        rampColors = [_rgb(_option(ramp, "preset_color_%d" % index)) for index in range(5)]
        assert rampColors == list(SPEC_PALETTE)

    def test_flow_classifies_its_absolute_value(self):
        assert _root("LinkFlow").find("renderer-v2").get("attr") == "abs(Flow)"

    def test_demand_breaks_come_from_the_absolute_values_of_the_junctions_only(self):
        strategy = json.loads(_customProperty("NodeDemand", "qgisred_legend_strategy"))
        assert strategy["intervals"]["sampleField"] == (
            "if(coalesce(\"NodeType\", \"Type\") in ('TANK','RESERVOIR'), NULL, abs(\"Demand\"))")
        assert _root("NodeDemand").find("renderer-v2").get("attr") == "Demand"

    def test_head_breaks_ignore_the_reservoirs(self):
        strategy = json.loads(_customProperty("NodeHead", "qgisred_legend_strategy"))
        assert strategy["intervals"]["sampleField"] == (
            "if(coalesce(\"NodeType\", \"Type\") in ('RESERVOIR'), NULL, \"Head\")")
        assert "negativeClass" not in strategy["intervals"]

    def test_demand_keeps_a_white_larger_class_below_zero(self):
        strategy = json.loads(_customProperty("NodeDemand", "qgisred_legend_strategy"))
        assert strategy["intervals"]["negativeClass"] is True
        ranges = _ranges("NodeDemand")
        assert ranges[0] == (-1e10, -0.005, "< 0")
        assert _classColors("NodeDemand")[0] == "#ffffff"
        circle = next(layer for layer in _classSymbols("NodeDemand")[0].findall("layer")
                      if layer.get("class") == "SimpleMarker")
        assert _option(circle, "size") == "3.5"


class TestColoursAndSizes:
    @pytest.mark.parametrize("name", ["NodeChlorine", "LinkVelocitySI", "LinkFricFactor"])
    def test_five_classes_take_the_five_palette_colours_in_order(self, name):
        assert _classColors(name) == list(SPEC_PALETTE)

    def test_the_negative_pressure_class_is_white_and_the_others_take_the_palette(self):
        assert _classColors("NodePressureSI") == ["#ffffff"] + list(SPEC_PALETTE)
        assert _classColors("NodePressureUS") == ["#ffffff"] + list(SPEC_PALETTE)

    def test_tank_and_reservoir_frames_are_a_darker_shade_of_the_class_colour(self):
        symbol = _classSymbols("NodeChlorine")[0]
        water, frame = symbol.findall("layer")[:2]
        assert _rgb(_option(water, "color")) == SPEC_PALETTE[0]
        assert _rgb(_option(frame, "color")) == "#00319f"

    @pytest.mark.parametrize("name", ["NodeHead", "NodeTrace"])
    def test_node_sizes(self, name):
        expressions = _sizeExpressions(name)
        assert {expression[-6:].strip() for expression in expressions} == {"8,0))", "0,2))"}
        circle = next(layer for layer in _classSymbols(name)[0].findall("layer")
                      if layer.get("class") == "SimpleMarker")
        assert _option(circle, "size") == "2"

    def test_the_negative_pressure_junction_is_larger(self):
        symbols = _classSymbols("NodePressureSI")
        circles = [next(layer for layer in symbol.findall("layer") if layer.get("class") == "SimpleMarker")
                   for symbol in symbols]
        assert [_option(circle, "size") for circle in circles] == ["3", "2", "2", "2", "2", "2"]
        assert _sizeExpressions("NodePressureSI")[9].endswith("0,3))")

    @pytest.mark.parametrize("name", ["LinkFlow", "LinkStatus", "LinkAge"])
    def test_link_sizes(self, name):
        root = _root(name)
        lineWidths = {_option(symbol.findall("layer")[0], "line_width") for symbol in _classSymbols(name)}
        assert lineWidths == {"0.7"}
        icons = {expression[-8:] for expression in _sizeExpressions(name)}
        assert icons == {", 7, 0))"}
        units = {option.get("value") for option in root.iter("Option") if option.get("name", "").endswith("_unit")}
        assert units == {"MM"}

    def test_every_result_style_leaves_labels_and_map_tips_to_the_dock(self):
        for name in RESULT_STYLE_NAMES:
            root = _root(name)
            assert root.get("labelsEnabled") == "0"
            assert root.find("labeling") is None


class TestIdentifiers:
    @pytest.mark.parametrize("name, identifier", [
        ("NodePressureSI", "qgisred_node_pressure"), ("NodePressureUS", "qgisred_node_pressure"),
        ("NodeHead", "qgisred_node_head"), ("NodeDemand", "qgisred_node_demand"),
        ("NodeChlorine", "qgisred_node_quality"), ("NodeChemical", "qgisred_node_quality"),
        ("NodeTrace", "qgisred_node_quality"), ("NodeAge", "qgisred_node_quality"),
        ("LinkFlow", "qgisred_link_flow"), ("LinkVelocitySI", "qgisred_link_velocity"),
        ("LinkVelocityUS", "qgisred_link_velocity"), ("LinkHeadLossSI", "qgisred_link_headloss"),
        ("LinkHeadLossUS", "qgisred_link_headloss"), ("LinkUnitHdLoss", "qgisred_link_unitheadloss"),
        ("LinkFricFactor", "qgisred_link_frictionfactor"), ("LinkReactRate", "qgisred_link_reactionrate"),
        ("LinkChlorine", "qgisred_link_quality"), ("LinkChemical", "qgisred_link_quality"),
        ("LinkTrace", "qgisred_link_quality"), ("LinkAge", "qgisred_link_quality"),
        ("LinkStatus", "qgisred_link_status"),
    ])
    def test_identifier(self, name, identifier):
        assert _customProperty(name, "qgisred_identifier") == identifier


class TestStatus:
    def test_three_groups_of_epanet_states(self):
        rules = _root("LinkStatus").findall("renderer-v2/rules/rule")
        assert [(rule.get("label"), rule.get("filter")) for rule in rules] == [
            ("Open", "\"Status\" LIKE 'Open%'"),
            ("Active", "\"Status\" LIKE 'Active%'"),
            ("Closed", "\"Status\" LIKE '%Closed%'"),
        ]
        assert _classColors("LinkStatus") == ["#00ff00", "#ffd800", "#ff3800"]


class TestResultsPalette:
    def test_the_generator_and_the_style_database_share_the_spec_colours(self):
        styleDb = _loadScript("build_style_db")
        entry = next(entry for entry in styleDb.PRESET_PALETTES if entry[0] == "QGISRed EPANET Results")

        assert entry[1] == SPEC_PALETTE
        assert generator.PALETTE == SPEC_PALETTE

    def test_the_shipped_database_holds_them(self):
        connection = sqlite3.connect("file:%s?mode=ro" % DATABASE.replace("\\", "/"), uri=True)
        try:
            xml = connection.execute("SELECT xml FROM colorramp WHERE name = 'QGISRed EPANET Results'").fetchone()[0]
        finally:
            connection.close()
        colors = re.findall(r'value="(\d+,\d+,\d+),255" name="preset_color_\d"', xml)
        assert [_rgb(color) for color in colors] == list(SPEC_PALETTE)
