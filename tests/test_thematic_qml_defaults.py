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

EXPECTED = {
    "PipeInstallationYears.qml.bak": {
        "field": "InstYear",
        "expression": 'to_int( left( "InstalDate" ,4))',
        "labels": ["< 1925", "1925 - 1949", "1950 - 1974", "1975 - 1999", "2000 - 2014", ">= 2015"],
        "bounds": (1000.0, 2050.0),
        "mapTip": 'Year [%"InstYear"%]',
    },
    "PipeAges.qml.bak": {
        "field": "Age",
        "expression": "round(year(age(now(),to_datetime(\"InstalDate\",'yyyyMMdd'))),0)",
        "labels": ["< 10", "10 - 24", "25 - 49", "50 - 74", "75 - 100", ">= 100"],
        "bounds": (0.0, 1000.0),
        "mapTip": '[%"Age"%] years old',
    },
}

GREY = "128,128,128,255"


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
        # contiguous, and all on the virtual field.
        previousUpper = None
        for rule in rules[:-1]:
            field, lower, upper = parseRangeFilter(rule.get("filter"))
            assert field == expected["field"]
            assert lower < upper
            if previousUpper is not None:
                assert lower == previousUpper
            previousUpper = upper
        firstLower = parseRangeFilter(rules[0].get("filter"))[1]
        assert (firstLower, previousUpper) == expected["bounds"]

        # Undated pipes land in the catch-all Unknown rule, drawn grey.
        elseRule = rules[-1]
        assert elseRule.get("filter") == "ELSE"
        assert elseRule.get("label") == "Unknown"
        symbols = {symbol.get("name"): symbol for symbol in renderer.findall("symbols/symbol")}
        assert len(symbols) == 7
        assert lineOption(symbols[elseRule.get("symbol")], "line_color").startswith(GREY)
        for symbol in symbols.values():
            assert lineOption(symbol, "line_width") == "0.8"

    def test_virtual_field_is_declared_in_the_style_itself(self, fileName):
        expected = EXPECTED[fileName]
        fields = loadStyle(fileName).findall("expressionfields/field")
        assert len(fields) == 1
        assert fields[0].get("name") == expected["field"]
        assert fields[0].get("expression") == expected["expression"]
        assert fields[0].get("typeName") == "integer"

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
