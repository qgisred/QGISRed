# -*- coding: utf-8 -*-
"""Keep tools/qgisred_translatable_strings.py in sync with its data sources.

pylupdate only extracts literal strings it can see in the source, so display
names that live in a dict (PLURAL_PROPERTY_NAMES) or in a CSV are mirrored as
explicit QCoreApplication.translate() calls in qgisred_translatable_strings.py.
Nothing enforces that mirroring at runtime: a missing entry simply shows up
untranslated in the UI.  These tests catch the drift instead.
"""
import ast
import csv
import os

import pytest

from QGISRed.tools.utils.qgisred_field_utils import PLURAL_PROPERTY_NAMES
from QGISRed.tools.utils.qgisred_valve_types import VALVE_TYPE_LONG_NAMES

_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_STRINGS_FILE = os.path.join(_PLUGIN_ROOT, "tools", "qgisred_translatable_strings.py")
_UNITS_CSV = os.path.join(_PLUGIN_ROOT, "defaults", "qgisred_properties_units_decimals.csv")


def _translated_literals(context):
    """Return every literal passed to QCoreApplication.translate(context, "…")."""
    with open(_STRINGS_FILE, "r", encoding="utf-8") as handle:
        tree = ast.parse(handle.read(), filename=_STRINGS_FILE)

    literals = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or len(node.args) < 2:
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "translate":
            continue
        callContext, text = node.args[0], node.args[1]
        if not isinstance(callContext, ast.Constant) or not isinstance(text, ast.Constant):
            continue
        if callContext.value == context:
            literals.add(text.value)
    return literals


def _csvPrettyNames():
    """Return the property display names of the CSV that reach the UI.

    'Global' rows are skipped: their property column holds marker names
    (FlowUnits, Currency…) that only the 'See <marker>' redirection reads,
    never a field label shown to the user.
    """
    with open(_UNITS_CSV, "r", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.reader(handle, delimiter=",")
        next(reader)  # header
        return {
            line[2].strip()
            for line in reader
            if len(line) >= 9 and line[2].strip() and line[0].strip() != "Global"
        }


class TestTranslatableStringsFileIsParsable:
    def test_field_pretty_names_context_is_populated(self):
        # Guards the extraction helper itself: a rename of the context or a change
        # in how the calls are written would otherwise make every test below pass
        # vacuously on an empty set.
        assert len(_translated_literals("FieldPrettyNames")) > 50


class TestPluralPropertyNamesAreTranslatable:
    def test_every_plural_is_mirrored(self):
        literals = _translated_literals("FieldPrettyNames")
        missing = sorted(set(PLURAL_PROPERTY_NAMES.values()) - literals)
        assert not missing, (
            "Plural names in PLURAL_PROPERTY_NAMES with no QCoreApplication.translate() "
            "call in tools/qgisred_translatable_strings.py (they will not reach the .ts "
            "files and will show untranslated): {}".format(", ".join(missing))
        )


class TestCsvPrettyNamesAreTranslatable:
    def test_every_csv_property_is_mirrored(self):
        if not os.path.exists(_UNITS_CSV):
            pytest.skip("units CSV not shipped in this checkout")
        literals = _translated_literals("FieldPrettyNames")
        missing = sorted(_csvPrettyNames() - literals)
        assert not missing, (
            "Property display names in defaults/qgisred_properties_units_decimals.csv "
            "with no QCoreApplication.translate() call in "
            "tools/qgisred_translatable_strings.py: {}".format(", ".join(missing))
        )


class TestValveTypeNamesAreTranslatable:
    def test_every_long_name_is_mirrored(self):
        literals = _translated_literals("ValveTypeNames")
        missing = sorted(set(VALVE_TYPE_LONG_NAMES.values()) - literals)
        assert not missing, (
            "Valve type long names in VALVE_TYPE_LONG_NAMES with no "
            "QCoreApplication.translate() call in tools/qgisred_translatable_strings.py: "
            "{}".format(", ".join(missing))
        )

    def test_every_abbreviation_source_is_mirrored(self):
        literals = _translated_literals("ValveTypeAbbreviations")
        missing = sorted(set(VALVE_TYPE_LONG_NAMES.keys()) - literals)
        assert not missing, (
            "Valve type codes in VALVE_TYPE_LONG_NAMES with no "
            "QCoreApplication.translate('ValveTypeAbbreviations', ...) call in "
            "tools/qgisred_translatable_strings.py: {}".format(", ".join(missing))
        )
