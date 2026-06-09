# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.qgisred_node_demand_utils import (
    is_junction_node_layer,
    junction_positive_node_demand,
)


class _FakeFeatureFields:
    def __init__(self, names):
        self._names = names

    def names(self):
        return self._names


class _FakeFeature:
    def __init__(self, attributes):
        self._attributes = attributes

    def fields(self):
        return _FakeFeatureFields(list(self._attributes.keys()))

    def __getitem__(self, name):
        return self._attributes[name]


class TestJunctionNodeLayer:
    def test_tanks_and_reservoirs_are_not_junction_layers(self):
        assert is_junction_node_layer("qgisred_tanks") is False
        assert is_junction_node_layer("qgisred_reservoirs") is False

    def test_junction_and_results_layers_are_junction_layers(self):
        assert is_junction_node_layer("qgisred_junctions") is True
        assert is_junction_node_layer("qgisred_node_demand") is True


class TestJunctionPositiveNodeDemand:
    def test_returns_positive_junction_demand(self):
        feature = _FakeFeature({"Type": "JUNCTION", "Demand": 4.5})
        assert junction_positive_node_demand(feature) == 4.5

    def test_ignores_tanks_reservoirs_and_non_positive(self):
        assert junction_positive_node_demand(_FakeFeature({"Type": "TANK", "Demand": 10.0})) is None
        assert junction_positive_node_demand(_FakeFeature({"Type": "RESERVOIR", "Demand": 10.0})) is None
        assert junction_positive_node_demand(_FakeFeature({"Type": "JUNCTION", "Demand": 0.0})) is None
        assert junction_positive_node_demand(_FakeFeature({"Type": "JUNCTION", "Demand": -2.0})) is None

    def test_layer_identifier_overrides_missing_type(self):
        feature = _FakeFeature({"Demand": 6.0})
        assert junction_positive_node_demand(feature, "qgisred_junctions") == 6.0
        assert junction_positive_node_demand(feature, "qgisred_tanks") is None
