# -*- coding: utf-8 -*-
"""The thematic-map catalogue and the builder that turns one of its entries into a layer.

Both used to live inside the Thematic Maps dialog, where the only way to name a map was to
tick its checkbox. They are apart from it so the legend's outdated-layer warning can rebuild
a single map without a dialog, and these tests exercise them the same way it does.
"""
import os
import re
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils import qgisred_thematicmaps_queries as queries_module
from QGISRed.tools.utils.qgisred_thematicmaps_queries import buildQueryCatalogue, queryIdentifier
from QGISRed.tools.utils import qgisred_thematicmaps_builder as builder_module
from QGISRed.tools.utils.qgisred_thematicmaps_builder import QGISRedThematicMapsBuilder

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIALOG_SOURCE = os.path.join(PLUGIN_ROOT, "ui", "queries", "qgisred_thematicmaps_dialog.py")

BUILDER_MODULE = "QGISRed.tools.utils.qgisred_thematicmaps_builder."


@pytest.fixture(autouse=True)
def projectSettings(monkeypatch):
    monkeypatch.setattr(queries_module.QGISRedProjectUtils, "getUnits", staticmethod(lambda: "SI"))
    monkeypatch.setattr(queries_module.QGISRedProjectUtils, "getHeadlossFormula", staticmethod(lambda: "H-W"))


class TestCatalogue:

    def test_every_map_has_its_own_identifier(self):
        identifiers = [queryIdentifier(query) for query in buildQueryCatalogue()]

        assert len(identifiers) == len(set(identifiers))

    def test_the_catalogue_and_the_dialog_describe_the_same_maps(self):
        """The split put the catalogue on one side and the checkboxes on the other. An
        identifier only one side knows is a map the user can never build, or a checkbox
        that ticks nothing — and neither fails loudly at runtime.

        Read from the source because createIdentifierCheckboxMapping returns real widgets.
        """
        with open(DIALOG_SOURCE, encoding="utf-8") as source:
            checkboxIdentifiers = set(re.findall(r"'(qgisred_query_\w+)':\s*self\.\w+", source.read()))

        assert {queryIdentifier(query) for query in buildQueryCatalogue()} == checkboxIdentifiers

    def test_units_reach_the_style_of_a_unit_dependent_map(self, monkeypatch):
        monkeypatch.setattr(queries_module.QGISRedProjectUtils, "getUnits", staticmethod(lambda: "US"))

        byId = {queryIdentifier(query): query for query in buildQueryCatalogue()}

        assert byId["qgisred_query_pipes_diameter"]["qml_file"] == "PipeDiametersUS.qml"

    @pytest.mark.parametrize("formula, qmlFile, suffix", [
        ("H-W", "PipeRoughnessesHW.qml", "_HW"),
        ("C-M", "PipeRoughnessesCM.qml", "_CM"),
        ("D-W", "PipeRoughnessesDWSI.qml", "_DW"),
    ])
    def test_the_headloss_formula_picks_the_roughness_style(self, monkeypatch, formula, qmlFile, suffix):
        monkeypatch.setattr(queries_module.QGISRedProjectUtils, "getHeadlossFormula", staticmethod(lambda: formula))

        byId = {queryIdentifier(query): query for query in buildQueryCatalogue()}
        roughness = byId["qgisred_query_pipes_roughness"]

        assert (roughness["qml_file"], roughness["name_suffix"]) == (qmlFile, suffix)


class _Builder(QGISRedThematicMapsBuilder):
    """A builder whose tree lookups answer, so applyQueries reaches processQuery."""

    def __init__(self, pipesLayer, junctionsLayer):
        super().__init__(MagicMock(), "/proj", "Net")
        self._pipes = pipesLayer
        self._junctions = junctionsLayer
        self.processQuery = MagicMock()

    def getRootGroup(self):
        return MagicMock()

    def getOrCreateQueriesGroup(self, rootGroup, inputsGroup):
        return "thematicGroup"

    def findLayerInGroup(self, group, layerName=None, custom_property=None):
        return self._junctions if custom_property == "qgisred_junctions" else self._pipes


@pytest.fixture
def builder():
    made = []

    def build(pipesLayer="pipes", junctionsLayer="junctions"):
        item = _Builder(pipesLayer, junctionsLayer)
        made.append(item)
        return item

    with patch(BUILDER_MODULE + "QGISRedLayerUtils") as utils:
        utils.return_value.getOrCreateGroup.return_value = "inputsGroup"
        yield build


def _builtIdentifiers(builder):
    return [queryIdentifier(call.args[0]) for call in builder.processQuery.call_args_list]


class TestApplyQueries:

    def test_only_the_named_maps_are_built(self, builder):
        item = builder()

        assert item.applyQueries(buildQueryCatalogue(), {"qgisred_query_pipes_material"}) is True
        assert _builtIdentifiers(item) == ["qgisred_query_pipes_material"]

    def test_an_unknown_identifier_builds_nothing(self, builder):
        item = builder()

        assert item.applyQueries(buildQueryCatalogue(), {"qgisred_query_pipes_nosuchfield"}) is False
        item.processQuery.assert_not_called()

    def test_a_junctions_map_is_built_from_the_junctions_layer(self, builder):
        item = builder()

        item.applyQueries(buildQueryCatalogue(), {"qgisred_query_junctions_elevation"})

        assert item.processQuery.call_args.args[1] == "junctions"

    def test_a_pipes_map_is_built_from_the_pipes_layer(self, builder):
        item = builder()

        item.applyQueries(buildQueryCatalogue(), {"qgisred_query_pipes_length"})

        assert item.processQuery.call_args.args[1] == "pipes"

    def test_a_project_without_pipes_builds_nothing(self, builder):
        item = builder(pipesLayer=None)

        assert item.applyQueries(buildQueryCatalogue(), {"qgisred_query_pipes_length"}) is False
        item.processQuery.assert_not_called()

    def test_a_junctions_map_survives_a_project_without_junctions(self, builder):
        item = builder(junctionsLayer=None)

        assert item.applyQueries(buildQueryCatalogue(), {"qgisred_query_junctions_elevation"}) is True
        item.processQuery.assert_not_called()

    def test_rebuilding_by_identifier_reads_the_catalogue_itself(self, builder):
        item = builder()

        assert item.rebuildThematicMaps(["qgisred_query_pipes_material"]) is True
        assert _builtIdentifiers(item) == ["qgisred_query_pipes_material"]


class TestFindingTheMapToReplace:
    """Rebuilding a map has to find the one already in the tree, or it just adds a second.

    The identifier is stamped on the *layer*; a QgsLayerTreeLayer keeps its own, separate
    custom property store and knows nothing about it. Reading it off the node answers None
    for every map there is — silently, which is why the old map stayed put beside its
    rebuild instead of being replaced.
    """

    def _node(self, identifier, isLayerNode=True):
        node = MagicMock()
        node.nodeType.return_value = builder_module.NODE_TYPE_LAYER
        # The node's own store is empty: this is the read that used to be made.
        node.customProperty.return_value = None
        layer = MagicMock()
        layer.customProperty.side_effect = (
            lambda name, *a: identifier if name == "qgisred_identifier" else None)
        node.layer.return_value = layer if isLayerNode else None
        node.checkedLayers.return_value = [] if isLayerNode else [layer]
        return node

    def _group(self, children):
        group = MagicMock()
        group.children.return_value = children
        group.nodeType.return_value = builder_module.NODE_TYPE_GROUP
        return group

    def _finder(self):
        return object.__new__(QGISRedThematicMapsBuilder)

    def test_the_existing_map_is_found_by_its_layers_identifier(self, monkeypatch):
        monkeypatch.setattr(builder_module, "QgsLayerTreeLayer", MagicMock)
        node = self._node("qgisred_query_pipes_diameter")
        group = self._group([self._node("qgisred_query_pipes_length"), node])

        found, position = self._finder().findLayerByIdentifier(group, "qgisred_query_pipes_diameter")

        assert found is node
        assert position == 1

    def test_a_map_in_a_nested_group_is_found_too(self, monkeypatch):
        monkeypatch.setattr(builder_module, "QgsLayerTreeLayer", MagicMock)
        node = self._node("qgisred_query_pipes_diameter")
        group = self._group([self._group([node])])

        found, _position = self._finder().findLayerByIdentifier(group, "qgisred_query_pipes_diameter")

        assert found is node

    def test_an_absent_map_is_reported_as_such(self, monkeypatch):
        monkeypatch.setattr(builder_module, "QgsLayerTreeLayer", MagicMock)
        group = self._group([self._node("qgisred_query_pipes_length")])

        assert self._finder().findLayerByIdentifier(group, "qgisred_query_pipes_diameter") == (None, None)

    def test_a_node_that_only_answers_checkedLayers_is_still_read(self, monkeypatch):
        """Not every layer node in the tree is a QgsLayerTreeLayer; the removal that
        follows already covers both, and so must the lookup that feeds it."""
        monkeypatch.setattr(builder_module, "QgsLayerTreeLayer", type("Other", (), {}))
        node = self._node("qgisred_query_pipes_diameter", isLayerNode=False)
        group = self._group([node])

        found, _position = self._finder().findLayerByIdentifier(group, "qgisred_query_pipes_diameter")

        assert found is node
