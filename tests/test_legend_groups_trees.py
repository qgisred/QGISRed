# -*- coding: utf-8 -*-
"""Group combo entries for query groups: per-tree subgroups and Demand Builder filtering."""
import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog


class FakeLayer:
    def __init__(self, identifier=None, rendererType="categorizedSymbol"):
        self._identifier = identifier
        self._rendererType = rendererType

    def customProperty(self, key, default=None):
        if key == "qgisred_identifier":
            return self._identifier if self._identifier is not None else default
        return default

    def renderer(self):
        if self._rendererType is None:
            return None
        layer = self

        class _Renderer:
            def type(self):
                return layer._rendererType

        return _Renderer()


class FakeLayerNode:
    def __init__(self, layer):
        self._layer = layer

    def layer(self):
        return self._layer


class FakeGroup:
    def __init__(self, name, identifier=None, children=None):
        self._name = name
        self._identifier = identifier
        self._children = children or []
        self._parent = None
        for child in self._children:
            if isinstance(child, FakeGroup):
                child._parent = self

    def name(self):
        return self._name

    def customProperty(self, key, default=None):
        if key == "qgisred_identifier":
            return self._identifier if self._identifier is not None else default
        return default

    def children(self):
        return self._children

    def parent(self):
        return self._parent


@pytest.fixture(autouse=True)
def fakeTreeClasses(monkeypatch):
    monkeypatch.setattr(legendsModule, "QgsLayerTreeGroup", FakeGroup)
    monkeypatch.setattr(legendsModule, "QgsLayerTreeLayer", FakeLayerNode)
    monkeypatch.setattr(legendsModule, "QgsVectorLayer", FakeLayer)


def _dialog():
    return QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)


def _collect(root):
    results = []
    _dialog().collectGroupsRecursive(root, [], results)
    return results


class TestTreeSubgroups:
    def _root(self):
        treeOne = FakeGroup("MyTree", identifier="qgisred_mytree", children=[
            FakeLayerNode(FakeLayer("qgisred_tree_links", "categorizedSymbol")),
            FakeLayerNode(FakeLayer("qgisred_tree_nodes", "singleSymbol")),
        ])
        treeTwo = FakeGroup("OtherTree", identifier="qgisred_othertree", children=[
            FakeLayerNode(FakeLayer("qgisred_tree_links", "categorizedSymbol")),
        ])
        emptyTree = FakeGroup("EmptyTree", identifier="qgisred_emptytree")
        trees = FakeGroup("Trees", identifier="qgisred_trees", children=[treeOne, treeTwo, emptyTree])
        queries = FakeGroup("Queries", identifier="qgisred_queries", children=[trees])
        network = FakeGroup("Network", children=[queries])
        # Mirror production: the walk starts at the invisible layer-tree root
        return FakeGroup("", children=[network])

    def test_each_tree_subgroup_is_listed_but_not_the_trees_parent(self):
        labels = [label for label, _path, _group in _collect(self._root())]
        assert "MyTree" in labels and "OtherTree" in labels
        assert "Trees" not in labels
        assert "EmptyTree" not in labels

    def test_entry_path_points_to_the_tree_subgroup(self):
        paths = {label: path for label, path, _group in _collect(self._root())}
        assert paths["MyTree"] == "Network / Queries / Trees / MyTree"

    def test_single_symbol_tree_nodes_layer_is_renderable(self):
        nodesOnly = FakeGroup("NodesTree", identifier="qgisred_nodestree", children=[
            FakeLayerNode(FakeLayer("qgisred_tree_nodes", "singleSymbol")),
        ])
        FakeGroup("Trees", identifier="qgisred_trees", children=[nodesOnly])
        assert _dialog().groupHasRenderableLayers(nodesOnly)


class TestDemandsBuilderGroup:
    def _group(self):
        return FakeGroup("DemandsBuilder", identifier="qgisred_demandsbuilder", children=[
            FakeLayerNode(FakeLayer("qgisred_demandsbuilder_consumptionpoints", "categorizedSymbol")),
            FakeLayerNode(FakeLayer("qgisred_demandsbuilder_demandlinks", "categorizedSymbol")),
            FakeLayerNode(FakeLayer("qgisred_demandsbuilder_sectors", "categorizedSymbol")),
            FakeLayerNode(FakeLayer("qgisred_demandsbuilder_isolateddemandsserviceconnections", "singleSymbol")),
        ])

    def test_only_points_and_links_are_collected(self):
        layers = []
        _dialog().collectRenderableLayersRecursive(self._group(), layers, False)
        identifiers = {layer.customProperty("qgisred_identifier") for layer in layers}
        assert identifiers == {
            "qgisred_demandsbuilder_consumptionpoints",
            "qgisred_demandsbuilder_demandlinks",
        }

    def test_group_is_allowed_in_the_combo(self):
        assert "qgisred_demandsbuilder" in QGISRedLegendsDialog.ALLOWED_GROUP_IDENTIFIERS


class TestConnectivityGroup:
    def test_single_symbol_connectivity_links_is_listed(self):
        connectivity = FakeGroup("Connectivity", identifier="qgisred_connectivity", children=[
            FakeLayerNode(FakeLayer("qgisred_connectivity_links", "singleSymbol")),
        ])
        root = FakeGroup("Network", children=[FakeGroup("Issues", children=[connectivity])])
        labels = [label for label, _path, _group in _collect(root)]
        assert labels == ["Connectivity"]


class TestIsolatedSegmentsGroup:
    def _group(self):
        return FakeGroup("Isolated Segments", identifier="qgisred_isolatedsegments", children=[
            FakeLayerNode(FakeLayer("qgisred_isolatedsegments_links", "singleSymbol")),
            FakeLayerNode(FakeLayer("qgisred_isolatedsegments_nodes", "singleSymbol")),
            FakeLayerNode(FakeLayer("qgisred_isolatedsegments_isolateddemands", "singleSymbol")),
        ])

    def test_group_is_listed_and_all_layers_collected(self):
        group = self._group()
        root = FakeGroup("Network", children=[FakeGroup("Queries", children=[group])])
        labels = [label for label, _path, _group in _collect(root)]
        assert labels == ["Isolated Segments"]

        layers = []
        _dialog().collectRenderableLayersRecursive(group, layers, True, isQueriesGroup=True)
        assert len(layers) == 3


class TestPanelAndDialogParity:
    """Every singleSymbol layer the group enumeration admits must be editable.

    If an identifier is collected for the combo but missing from
    EDITABLE_QUERY_IDENTIFIERS, the dialog shows an empty table for it and the
    layers-panel click is silently ignored — the two paths diverge.
    """

    QUERY_SINGLE_SYMBOL_LAYERS = [
        "qgisred_isolatedsegments_links",
        "qgisred_isolatedsegments_nodes",
        "qgisred_isolatedsegments_isolateddemands",
        "qgisred_hydraulicsectors_isolateddemands",
        "qgisred_tree_nodes",
        "qgisred_connectivity_links",
    ]

    @pytest.mark.parametrize("identifier", QUERY_SINGLE_SYMBOL_LAYERS)
    def test_collected_single_symbol_query_layers_are_editable(self, identifier):
        group = FakeGroup("Query", identifier="qgisred_isolatedsegments", children=[
            FakeLayerNode(FakeLayer(identifier, "singleSymbol")),
        ])
        layers = []
        _dialog().collectRenderableLayersRecursive(group, layers, True, isQueriesGroup=True)
        assert len(layers) == 1
        assert identifier in QGISRedLegendsDialog.EDITABLE_QUERY_IDENTIFIERS

    def test_union_covers_both_sets(self):
        assert QGISRedLegendsDialog.EDITABLE_QUERY_IDENTIFIERS == (
            QGISRedLegendsDialog.SIZE_ONLY_QUERY_IDENTIFIERS
            | QGISRedLegendsDialog.SINGLE_EDITABLE_QUERY_IDENTIFIERS
        )
