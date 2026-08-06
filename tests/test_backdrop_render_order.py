# -*- coding: utf-8 -*-
"""The custom layer order that keeps the sector themes under the network.

Sector themes are filled polygons, and the legend puts them wherever the user wants them
— above the network, most of the time. QGIS renders the tree from the bottom up, so what
stops them covering the pipes is a custom layer order: the flat list the Layer Order panel
edits, rebuilt from the tree every time a layer is opened or closed.
"""

from unittest.mock import MagicMock

import pytest

from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from QGISRed.tools.utils import qgisred_layer_utils

SECTORS = "qgisred_demandbuilder_sectors"


class _FakeLayer:
    def __init__(self, layerId, identifier=None):
        self._id = layerId
        self._identifier = identifier

    def id(self):
        return self._id

    def customProperty(self, name, default=None):
        if name == "qgisred_identifier":
            return self._identifier if self._identifier is not None else default
        return default

    def __repr__(self):
        return "_FakeLayer(%s)" % self._id


class _FakeNode:
    def __init__(self, layer):
        self._layer = layer

    def layer(self):
        return self._layer


class _FakeRoot:
    def __init__(self, layers, customOrder=None, hasCustomOrder=False):
        self._nodes = [_FakeNode(layer) for layer in layers]
        self._customOrder = list(customOrder or [])
        self._hasCustomOrder = hasCustomOrder
        self.writes = 0

    def findLayers(self):
        return self._nodes

    def customLayerOrder(self):
        return list(self._customOrder)

    def setCustomLayerOrder(self, layers):
        self._customOrder = list(layers)
        self.writes += 1

    def hasCustomLayerOrder(self):
        return self._hasCustomOrder

    def setHasCustomLayerOrder(self, enabled):
        self._hasCustomOrder = enabled

    def orderIds(self):
        return [layer.id() for layer in self._customOrder]


class _FakeProject:
    def __init__(self, root):
        self._root = root
        self.entries = {}

    def layerTreeRoot(self):
        return self._root

    def writeEntry(self, scope, key, value):
        self.entries[(scope, key)] = value
        return True

    def readBoolEntry(self, scope, key, default=False):
        return (self.entries.get((scope, key), default), (scope, key) in self.entries)

    def removeEntry(self, scope, key):
        self.entries.pop((scope, key), None)
        return True


@pytest.fixture
def project(monkeypatch):
    """Installs a project whose tree the test builds, and returns a builder for it."""

    holder = {}

    def build(layers, inputIds=(), customOrder=None, hasCustomOrder=False, entry=None):
        root = _FakeRoot(layers, customOrder, hasCustomOrder)
        instance = _FakeProject(root)
        if entry is not None:
            instance.entries[QGISRedLayerUtils._CUSTOM_ORDER_ENTRY] = entry
        monkeypatch.setattr(
            qgisred_layer_utils, "QgsProject", MagicMock(instance=MagicMock(return_value=instance))
        )
        inputs = [layer for layer in layers if layer is not None and layer.id() in set(inputIds)]
        monkeypatch.setattr(
            QGISRedLayerUtils, "getLayersByGroupIdentifier", classmethod(lambda cls, identifier: inputs)
        )
        holder["root"] = root
        holder["project"] = instance
        return root, instance

    build.holder = holder
    return build


class TestBackdropPlacement:
    def test_sector_themes_are_drawn_below_the_inputs(self, project):
        """The theme leads the tree and still ends up under the pipes."""
        sector = _FakeLayer("sector", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        junctions = _FakeLayer("junctions", "qgisred_junctions")
        root, _ = project([sector, junctions, pipes], inputIds=["pipes", "junctions"])

        assert QGISRedLayerUtils.applyBackdropRenderOrder() is True
        assert root.orderIds() == ["junctions", "pipes", "sector"]
        assert root.hasCustomLayerOrder() is True

    def test_what_the_user_keeps_under_the_network_stays_under_it(self, project):
        """A base map below the network must not be hidden by the backdrop."""
        sector = _FakeLayer("sector", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        basemap = _FakeLayer("basemap")
        root, _ = project([sector, pipes, basemap], inputIds=["pipes"])

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["pipes", "sector", "basemap"]

    def test_without_inputs_the_backdrop_goes_last(self, project):
        sector = _FakeLayer("sector", SECTORS)
        other = _FakeLayer("other")
        root, _ = project([sector, other])

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["other", "sector"]

    def test_several_themes_keep_the_order_the_tree_gives_them(self, project):
        first = _FakeLayer("first", SECTORS)
        second = _FakeLayer("second", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, _ = project([first, second, pipes], inputIds=["pipes"])

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["pipes", "first", "second"]

    def test_the_order_is_rebuilt_from_the_tree_not_from_itself(self, project):
        """Reading the previous custom order back would let the two drift apart."""
        sector = _FakeLayer("sector", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, _ = project(
            [sector, pipes], inputIds=["pipes"], customOrder=[sector], hasCustomOrder=True
        )

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["pipes", "sector"]

    def test_a_node_whose_layer_is_gone_is_skipped(self, project):
        sector = _FakeLayer("sector", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, _ = project([sector, None, pipes], inputIds=["pipes"])

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["pipes", "sector"]

    def test_a_layer_showing_twice_in_the_tree_is_listed_once(self, project):
        """A duplicated entry would be a layer QGIS renders twice."""
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        sector = _FakeLayer("sector", SECTORS)
        root, _ = project([sector, pipes, pipes], inputIds=["pipes"])

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.orderIds() == ["pipes", "sector"]


class TestWhenNothingHasToChange:
    def test_an_order_already_in_place_is_not_written_again(self, project):
        """Rewriting it would redraw the canvas and dirty the project on every layer."""
        sector = _FakeLayer("sector", SECTORS)
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, _ = project(
            [sector, pipes], inputIds=["pipes"], customOrder=[pipes, sector], hasCustomOrder=True
        )

        assert QGISRedLayerUtils.applyBackdropRenderOrder() is True
        assert root.writes == 0

    def test_a_project_with_no_themes_is_left_alone(self, project):
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, instance = project([pipes], inputIds=["pipes"])

        assert QGISRedLayerUtils.applyBackdropRenderOrder() is False
        assert root.hasCustomLayerOrder() is False
        assert instance.entries == {}

    def test_the_last_theme_closing_gives_the_project_its_order_back(self, project):
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, instance = project([pipes], inputIds=["pipes"], hasCustomOrder=True, entry=True)

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.hasCustomLayerOrder() is False
        assert instance.entries == {}

    def test_an_order_the_user_set_up_themselves_is_never_switched_off(self, project):
        """No entry of ours in the project means the order is not ours to undo."""
        pipes = _FakeLayer("pipes", "qgisred_pipes")
        root, _ = project([pipes], inputIds=["pipes"], hasCustomOrder=True)

        QGISRedLayerUtils.applyBackdropRenderOrder()

        assert root.hasCustomLayerOrder() is True


class TestBackdropIdentification:
    def test_the_sector_themes_are_the_ones_declared_by_the_naming_rules(self):
        """The identifier is built by qgisred_auxiliary_layers, not spelled twice."""
        from QGISRed.tools.utils.qgisred_auxiliary_layers import AUXILIARY_TYPES_BY_KEY

        assert AUXILIARY_TYPES_BY_KEY["Sectors"].identifier in QGISRedLayerUtils.BACKDROP_LAYER_IDENTIFIERS

    def test_a_layer_with_no_identifier_is_not_a_backdrop(self):
        assert QGISRedLayerUtils.isBackdropLayer(_FakeLayer("plain")) is False
        assert QGISRedLayerUtils.isBackdropLayer(None) is False

    def test_the_consumption_and_link_themes_are_not_backdrops(self):
        """Points and lines do not hide anything, and they read better on top."""
        from QGISRed.tools.utils.qgisred_auxiliary_layers import AUXILIARY_TYPES_BY_KEY

        for key in ("Consumptions", "Links"):
            layer = _FakeLayer(key, AUXILIARY_TYPES_BY_KEY[key].identifier)
            assert QGISRedLayerUtils.isBackdropLayer(layer) is False


class TestSchedulingFromTheSection:
    def _makeSection(self, monkeypatch):
        from QGISRed.sections import layer_management_section

        section = object.__new__(layer_management_section.LayerManagementSection)
        section.isUnloading = False
        section._backdropOrderPending = False

        scheduled = []
        monkeypatch.setattr(
            layer_management_section, "QTimer",
            MagicMock(singleShot=lambda _msec, callback: scheduled.append(callback)),
        )
        return section, scheduled

    def test_the_work_is_deferred_a_turn(self, monkeypatch):
        """layersAdded fires before the plugin puts the layer in the tree."""
        section, scheduled = self._makeSection(monkeypatch)

        section.runLayerOrderChanged()

        assert len(scheduled) == 1

    def test_a_batch_of_layers_makes_one_pass(self, monkeypatch):
        section, scheduled = self._makeSection(monkeypatch)

        section.runLayerOrderChanged()
        section.runLayerOrderChanged()
        section.runLayerOrderChanged()

        assert len(scheduled) == 1

    def test_the_next_change_is_scheduled_again(self, monkeypatch):
        section, scheduled = self._makeSection(monkeypatch)
        applied = []
        monkeypatch.setattr(
            QGISRedLayerUtils, "applyBackdropRenderOrder", classmethod(lambda cls: applied.append(True))
        )

        section.runLayerOrderChanged()
        scheduled[0]()
        section.runLayerOrderChanged()

        assert applied == [True]
        assert len(scheduled) == 2

    def test_nothing_is_scheduled_while_the_plugin_is_unloading(self, monkeypatch):
        section, scheduled = self._makeSection(monkeypatch)
        section.isUnloading = True

        section.runLayerOrderChanged()

        assert scheduled == []

    def test_a_failure_does_not_reach_the_signal(self, monkeypatch):
        """The slot runs on every layer added to any project, ours or not."""
        section, _scheduled = self._makeSection(monkeypatch)
        monkeypatch.setattr(
            QGISRedLayerUtils, "applyBackdropRenderOrder",
            classmethod(lambda cls: (_ for _ in ()).throw(RuntimeError("boom"))),
        )

        section.applyBackdropRenderOrder()

        assert section._backdropOrderPending is False
