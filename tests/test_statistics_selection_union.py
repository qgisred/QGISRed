# -*- coding: utf-8 -*-
"""Tests for the selected-elements union of the Statistics and Graphs dock.

The "Only selected elements" filter unions the selections of the Inputs and
Results layers, joined by element id. QGIS keeps a layer's selection alive when
the layer or its group is hidden, so the union must ignore selections on layers
that are not effectively visible in the layer tree.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

from unittest.mock import MagicMock, patch

from QGISRed.ui.queries.qgisred_statisticsandgraphs_dock import QGISRedStatisticsDock

_DOCK_MODULE = "QGISRed.ui.queries.qgisred_statisticsandgraphs_dock"


class _FakeFields:
    def indexFromName(self, name):
        return 0


class _FakeFeature:
    def __init__(self, fid, elementId):
        self._fid = fid
        self._elementId = elementId

    def id(self):
        return self._fid

    def __getitem__(self, fieldName):
        return self._elementId


class _FakeLayer:
    def __init__(self, features, selectedFids):
        self._features = features
        self._selectedFids = set(selectedFids)

    def id(self):
        return "fake-layer-id"

    def fields(self):
        return _FakeFields()

    def selectedFeatureIds(self):
        return list(self._selectedFids)

    def selectedFeatures(self):
        return [feature for feature in self._features if feature.id() in self._selectedFids]

    def getFeatures(self, request):
        return list(self._features)


def _makeDock(counterpartLayers, visibleLayers):
    dock = object.__new__(QGISRedStatisticsDock)
    dock.fieldUtils = MagicMock()
    dock.fieldUtils.getIdFieldName.return_value = "Id"
    dock.selectionCounterpartLayers = lambda baseLayer: list(counterpartLayers)
    dock.isLayerVisibleInTree = lambda layer: any(layer is visible for visible in visibleLayers)
    return dock


def _makeLayers():
    baseLayer = _FakeLayer(
        [_FakeFeature(1, "P1"), _FakeFeature(2, "P2"), _FakeFeature(3, "P3")],
        selectedFids=[1],
    )
    counterpartLayer = _FakeLayer(
        [_FakeFeature(10, "P1"), _FakeFeature(20, "P2"), _FakeFeature(30, "P3")],
        selectedFids=[20],
    )
    return baseLayer, counterpartLayer


class TestUnionSelectedFids:
    def _union(self, visibleLayers):
        baseLayer, counterpartLayer = _makeLayers()
        visible = [
            layer for layer, isVisible in ((baseLayer, "base" in visibleLayers), (counterpartLayer, "counterpart" in visibleLayers))
            if isVisible
        ]
        dock = _makeDock([counterpartLayer], visible)
        with patch(_DOCK_MODULE + ".QgsFeatureRequest", MagicMock()):
            return dock.unionSelectedFids(baseLayer)

    def test_both_groups_visible_unions_both_selections(self):
        assert self._union({"base", "counterpart"}) == {1, 2}

    def test_hidden_counterpart_selection_is_ignored(self):
        assert self._union({"base"}) == {1}

    def test_hidden_base_selection_is_ignored(self):
        assert self._union({"counterpart"}) == {2}

    def test_both_groups_hidden_yields_empty_selection(self):
        assert self._union(set()) == set()


class TestIsLayerVisibleInTree:
    def _visibility(self, node):
        dock = object.__new__(QGISRedStatisticsDock)
        with patch(_DOCK_MODULE + ".QgsProject") as projectCls:
            projectCls.instance.return_value.layerTreeRoot.return_value.findLayer.return_value = node
            return dock.isLayerVisibleInTree(_FakeLayer([], []))

    def test_checked_node_is_visible(self):
        node = MagicMock()
        node.isVisible.return_value = True
        assert self._visibility(node) is True

    def test_unchecked_node_is_hidden(self):
        node = MagicMock()
        node.isVisible.return_value = False
        assert self._visibility(node) is False

    def test_layer_without_tree_node_keeps_counting(self):
        assert self._visibility(None) is True
