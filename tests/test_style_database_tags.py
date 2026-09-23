# -*- coding: utf-8 -*-
"""The shipped style database classifies its ramps and palettes by kind.

The Colors list of the legend editor is built from these tags, so a ramp or palette left
without one, or carrying two, would show up in the wrong place or not at all.
"""
import os
import re
import sqlite3

import pytest

from QGISRed.tools.utils.qgisred_styling_utils import (
    PALETTE_KIND_LABELED,
    PALETTE_KINDS,
    RAMP_KIND_MORE_COLORS,
    RAMP_KIND_THREE_COLORS,
    RAMP_KIND_TWO_COLORS,
    RAMP_KINDS,
)

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(PLUGIN_ROOT, "defaults", "qgisred_symbology_style.db.bak")

# Saved legend strategies refer to a ramp by its name: these must never go away.
NAMES_IN_SAVED_STRATEGIES = [
    "QGISRed Elevation", "QGISRed Pressure", "QGISRed Velocity", "QGISRed Blue to Green", "QGISRed Grayscale",
    "QGISRed Pipe Diameters", "QGISRed Pipe Ages", "QGISRed Pipe Roughness", "QGISRed Pipe Materials",
    "QGISRed Qualitative 10", "QGISRed EPANET Results",
]


def _ramps():
    connection = sqlite3.connect("file:%s?mode=ro" % DATABASE.replace("\\", "/"), uri=True)
    try:
        rows = connection.execute("SELECT id, name, xml FROM colorramp").fetchall()
        tags = connection.execute(
            "SELECT m.colorramp_id, t.name FROM ctagmap m JOIN tag t ON t.id = m.tag_id").fetchall()
    finally:
        connection.close()
    return [(name, xml, [tag for rampId, tag in tags if rampId == identifier]) for identifier, name, xml in rows]


RAMPS = _ramps()
GRADIENTS = [ramp for ramp in RAMPS if 'type="gradient"' in ramp[1]]
PRESETS = [ramp for ramp in RAMPS if 'type="preset"' in ramp[1]]


def _colorCount(xml):
    stops = re.search(r'value="([^"]*)" name="stops"', xml)
    return 2 + (len(stops.group(1).split(":")) if stops else 0)


class TestRampKinds:
    @pytest.mark.parametrize("name, xml, tags", GRADIENTS, ids=[ramp[0] for ramp in GRADIENTS])
    def test_a_ramp_carries_the_tag_of_its_number_of_colors(self, name, xml, tags):
        colorCount = _colorCount(xml)
        expected = {2: RAMP_KIND_TWO_COLORS, 3: RAMP_KIND_THREE_COLORS}.get(colorCount, RAMP_KIND_MORE_COLORS)

        assert [tag for tag in tags if tag in RAMP_KINDS] == [expected]
        assert "Ramps" in tags

    @pytest.mark.parametrize("kind", RAMP_KINDS)
    def test_no_ramp_kind_is_left_empty(self, kind):
        assert any(kind in tags for _name, _xml, tags in GRADIENTS)


class TestPaletteKinds:
    @pytest.mark.parametrize("name, xml, tags", PRESETS, ids=[ramp[0] for ramp in PRESETS])
    def test_a_palette_carries_exactly_one_kind(self, name, xml, tags):
        assert len([tag for tag in tags if tag in PALETTE_KINDS]) == 1
        assert "Palettes" in tags

    @pytest.mark.parametrize("kind", PALETTE_KINDS)
    def test_no_palette_kind_is_left_empty(self, kind):
        assert any(kind in tags for _name, _xml, tags in PRESETS)

    @pytest.mark.parametrize("name", ["QGISRed Pipe Materials", "QGISRed Link Status", "QGISRed Initial Status"])
    def test_palettes_whose_colors_are_named_after_values_are_labeled(self, name):
        tags = next(tags for rampName, _xml, tags in PRESETS if rampName == name)
        assert PALETTE_KIND_LABELED in tags

    def test_labels_with_signs_are_stored_as_valid_xml(self):
        xml = next(xml for name, xml, _tags in PRESETS if name == "QGISRed Link Status")
        assert "Closed (Q&lt;0)" in xml and "Closed (Q<0)" not in xml


class TestNamesAreStable:
    @pytest.mark.parametrize("name", NAMES_IN_SAVED_STRATEGIES)
    def test_a_name_saved_strategies_may_refer_to_is_still_there(self, name):
        assert name in [rampName for rampName, _xml, _tags in RAMPS]
