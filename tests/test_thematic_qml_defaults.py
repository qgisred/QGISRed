# -*- coding: utf-8 -*-
"""The two date-derived thematic maps live almost entirely in their style files.

PipeInstallationYears and PipeAges are the first shipped styles to declare a
virtual field in the QML itself — the renderer classifies InstYear/Age, columns
that do not exist in Pipes.shp — and the first thematic maps to carry a
rule-based renderer with a visible grey Unknown class instead of a graduated
one. Nothing else exercises those files: a malformed filter, a renamed virtual
field or a rule the legend editor cannot parse back would only surface as a
silently unstyled layer inside QGIS.
"""
import os
import re
import xml.etree.ElementTree as ET

import pytest

from QGISRed.tools.utils.qgisred_legend_rule_utils import parseRangeFilter

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES_DIR = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")
DIALOG_SOURCE = os.path.join(PLUGIN_ROOT, "ui", "queries", "qgisred_thematicmaps_dialog.py")

# Both styles declare both derived fields, whichever one they classify by, so a
# map tip or a label can be switched from one to the other without editing the
# expression back in.
VIRTUAL_FIELDS = {
    "InstYear": 'to_int( left( "InstalDate" ,4))',
    "Age": "round(year(age(now(),to_datetime(\"InstalDate\",'yyyyMMdd'))),0)",
}

EXPECTED = {
    "PipeInstallationYears.qml.bak": {
        "field": "InstYear",
        # Newest first: the legend reads in the order the renewal plan is argued.
        "labels": [">= 2015", "2000 - 2014", "1975 - 1999", "1950 - 1974", "1925 - 1949", "< 1925"],
        "bounds": (1000.0, 2050.0),
        "mapTip": 'Inst. [%"InstYear"%]',
    },
    "PipeAges.qml.bak": {
        "field": "Age",
        # Oldest last: same pipes, read the other way round.
        "labels": ["< 10", "10 - 24", "25 - 49", "50 - 74", "75 - 100", ">= 100"],
        "bounds": (0.0, 1000.0),
        "mapTip": '[%"Age"%] yr',
    },
}

GREY = "211,211,211,255"


def loadStyle(fileName):
    return ET.parse(os.path.join(STYLES_DIR, fileName)).getroot()


def lineOption(symbol, name):
    option = symbol.find("layer/Option/Option[@name='%s']" % name)
    return option.get("value")


@pytest.mark.parametrize("fileName", sorted(EXPECTED))
class TestDateDerivedThematicStyles:

    def test_rules_cover_the_decades_and_end_in_a_grey_unknown(self, fileName):
        expected = EXPECTED[fileName]
        renderer = loadStyle(fileName).find("renderer-v2")
        assert renderer.get("type") == "RuleRenderer"

        rules = renderer.findall("rules/rule")
        assert len(rules) == 7
        assert [rule.get("label") for rule in rules[:-1]] == expected["labels"]

        # The range filters must stay readable by the legend editor's parser,
        # contiguous, and all on the virtual field. The two styles list their
        # classes in opposite directions, so compare the ranges in value order
        # rather than in legend order.
        ranges = []
        for rule in rules[:-1]:
            field, lower, upper = parseRangeFilter(rule.get("filter"))
            assert field == expected["field"]
            assert lower < upper
            ranges.append((lower, upper))
        ranges.sort()
        for (_lower, upper), (nextLower, _nextUpper) in zip(ranges, ranges[1:]):
            assert nextLower == upper
        assert (ranges[0][0], ranges[-1][1]) == expected["bounds"]

        # Undated pipes land in the catch-all Unknown rule, drawn grey.
        elseRule = rules[-1]
        assert elseRule.get("filter") == "ELSE"
        assert elseRule.get("label") == "Unknown"
        symbols = {symbol.get("name"): symbol for symbol in renderer.findall("symbols/symbol")}
        assert len(symbols) == 7
        assert lineOption(symbols[elseRule.get("symbol")], "line_color").startswith(GREY)
        for symbol in symbols.values():
            assert lineOption(symbol, "line_width") == "0.8"

    def test_virtual_fields_are_declared_in_the_style_itself(self, fileName):
        expected = EXPECTED[fileName]
        fields = {field.get("name"): field for field in loadStyle(fileName).findall("expressionfields/field")}

        assert set(fields) == set(VIRTUAL_FIELDS)
        assert expected["field"] in fields
        for name, expression in VIRTUAL_FIELDS.items():
            assert fields[name].get("expression") == expression
            assert fields[name].get("typeName") == "integer"

    def test_map_tip_and_label_read_the_virtual_field(self, fileName):
        expected = EXPECTED[fileName]
        root = loadStyle(fileName)

        mapTip = root.find("mapTip")
        assert mapTip.get("enabled") == "1"
        assert mapTip.text == expected["mapTip"]

        textStyle = root.find("labeling/settings/text-style")
        assert textStyle.get("isExpression") == "1"
        assert textStyle.get("fontSize") == "8"
        assert '"%s"' % expected["field"] in textStyle.get("fieldName")


def test_dialog_ships_a_default_for_every_referenced_style():
    """Both query dicts must point at style files that actually exist: a missing
    default is silent — loadQmlStyle skips loadNamedStyle and the layer comes up
    with QGIS's single-symbol line."""
    with open(DIALOG_SOURCE, encoding="utf-8") as source:
        referenced = re.findall(r"'qml_file':\s*'(Pipe(?:InstallationYears|Ages)\.qml)'", source.read())
    assert sorted(referenced) == ["PipeAges.qml", "PipeInstallationYears.qml"]
    for qmlFile in referenced:
        assert os.path.exists(os.path.join(STYLES_DIR, qmlFile + ".bak"))


def test_dialog_ships_a_default_for_every_roughness_variant():
    """The roughness map picks its style at runtime from the headloss formula
    (H-W, C-M) plus the unit system for D-W, so every branch the dialog can
    build must resolve to a shipped default."""
    with open(DIALOG_SOURCE, encoding="utf-8") as source:
        text = source.read()
    referenced = set(re.findall(r"'(PipeRoughnesses\w+)(?:\{units\})?\.qml'", text))
    expected = {"PipeRoughnessesHW", "PipeRoughnessesCM", "PipeRoughnessesDW"}
    assert referenced == expected
    for name in ("PipeRoughnessesHW", "PipeRoughnessesCM", "PipeRoughnessesDWSI", "PipeRoughnessesDWUS"):
        assert os.path.exists(os.path.join(STYLES_DIR, name + ".qml.bak"))
    # The renderer must classify the real Pipes column.
    for name in ("PipeRoughnessesHW", "PipeRoughnessesCM", "PipeRoughnessesDWSI", "PipeRoughnessesDWUS"):
        renderer = loadStyle(name + ".qml.bak").find("renderer-v2")
        assert renderer.get("attr") == "RoughCoeff"
