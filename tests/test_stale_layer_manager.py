# -*- coding: utf-8 -*-
"""What the staleness warning may land on, and how it is kept off everything else."""
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_stale_layer_manager import StaleLayerManager


NET = "test123"


class _FakeLayer:
    def __init__(self, layerId, path, identifier=""):
        self._id = layerId
        self._path = path
        self._identifier = identifier

    def id(self):
        return self._id

    def dataProvider(self):
        provider = MagicMock()
        provider.dataSourceUri.return_value = self._path
        return provider

    def customProperty(self, name, default=None):
        if name == "qgisred_identifier":
            return self._identifier
        return default


class _FakeNode:
    def __init__(self, layerId):
        self._layerId = layerId

    def layerId(self):
        return self._layerId


class _FakeView:
    """Stands in for QgsLayerTreeView, keyed by node like the real one."""

    def __init__(self):
        self._byNode = {}
        self._viewport = MagicMock()

    def viewport(self):
        return self._viewport

    def indicators(self, node):
        return list(self._byNode.get(id(node), []))

    def addIndicator(self, node, indicator):
        self._byNode.setdefault(id(node), []).append(indicator)

    def removeIndicator(self, node, indicator):
        self._byNode.get(id(node), []).remove(indicator)


def _write(path, mtime):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(b"x")
    os.utime(path, (mtime, mtime))
    return path


@pytest.fixture
def project(tmp_path):
    """A project whose inputs are newer than everything the DLL derived from them."""
    projDir = str(tmp_path)
    old = time.time() - 3600
    new = time.time()

    _write(os.path.join(projDir, NET + "_Pipes.shp"), new)
    _write(os.path.join(projDir, NET + "_Junctions.dbf"), new)

    paths = {
        "input": os.path.join(projDir, NET + "_Pipes.shp"),
        "results": _write(os.path.join(projDir, "Results", NET + "_Base_Node.shp"), old),
        "issues": _write(os.path.join(projDir, "Issues", NET + "_Pipes_Issues.shp"), old),
        "queries": _write(os.path.join(projDir, "Queries", "Trees", NET + "_Tree_1_Nodes.shp"), old),
        "auxiliary": _write(
            os.path.join(projDir, "Auxiliary Layers", "DemandBuilder",
                         NET + "_DemandBuilder_Sectors_sec1.shp"), old),
        "demandSectors": _write(
            os.path.join(projDir, "Auxiliary Layers", "DemandSectors", NET + "_DemandSectors_Nodes.shp"), old),
    }
    return projDir, paths


class _Harness:
    """A manager with a fake project tree behind it."""

    def __init__(self, projDir, layers, nodes=None):
        self.view = _FakeView()
        self.nodes = {layer.id(): _FakeNode(layer.id()) for layer in layers} if nodes is None else nodes
        iface = MagicMock()
        iface.layerTreeView.return_value = self.view

        self._patch = patch("QGISRed.tools.utils.qgisred_stale_layer_manager.QgsProject")
        qgsProject = self._patch.start()
        instance = qgsProject.instance.return_value
        instance.mapLayers.return_value = {layer.id(): layer for layer in layers}
        instance.layerTreeRoot.return_value.findLayers.return_value = list(self.nodes.values())
        instance.layerTreeRoot.return_value.findLayer.side_effect = self.nodes.get

        self.manager = StaleLayerManager(iface, lambda: (NET, projDir))

    def flagged(self):
        """Layer ids whose node currently shows a warning."""
        return {
            layerId for layerId, node in self.nodes.items()
            if self.view.indicators(node)
        }

    def close(self):
        self._patch.stop()


@pytest.fixture
def harness(project):
    made = []

    def build(layers, nodes=None):
        projDir, _paths = project
        item = _Harness(projDir, layers, nodes)
        made.append(item)
        return item

    yield build
    # Reverse order: mock.patch restores the value it saw at start(), so unwinding out of
    # order would leave one test's mock behind in the module.
    for item in reversed(made):
        item.close()


class TestRelevance:
    def test_derived_layers_are_flagged(self, project, harness):
        _projDir, paths = project
        item = harness([
            _FakeLayer("results", paths["results"]),
            _FakeLayer("issues", paths["issues"]),
            _FakeLayer("queries", paths["queries"]),
        ])
        item.manager._check()
        assert item.flagged() == {"results", "issues", "queries"}

    def test_input_layers_are_never_flagged(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("pipes", paths["input"])])
        item.manager._check()
        assert item.flagged() == set()

    def test_auxiliary_folder_is_never_flagged(self, project, harness):
        """The Demand Builder's themes are the user's data, not something derived."""
        _projDir, paths = project
        item = harness([
            _FakeLayer("aux", paths["auxiliary"]),
            _FakeLayer("demSec", paths["demandSectors"]),
        ])
        item.manager._check()
        assert item.flagged() == set()

    def test_auxiliary_identifier_is_never_flagged(self, project, harness):
        """A theme opened from outside the project folder is excluded by identifier."""
        projDir, _paths = project
        outsider = _write(os.path.join(projDir, "Results", NET + "_DemandBuilder_Sectors_x.shp"),
                          time.time() - 3600)
        item = harness([_FakeLayer("aux", outsider, identifier="qgisred_demandbuilder_sectors")])
        item.manager._check()
        assert item.flagged() == set()

    def test_sibling_folder_does_not_match_by_prefix(self, project, harness):
        projDir, _paths = project
        lookalike = _write(os.path.join(projDir, "ResultsBackup", NET + "_Base_Node.shp"), time.time() - 3600)
        item = harness([_FakeLayer("backup", lookalike)])
        item.manager._check()
        assert item.flagged() == set()

    def test_up_to_date_layer_is_not_flagged(self, project, harness):
        projDir, _paths = project
        fresh = _write(os.path.join(projDir, "Results", NET + "_Fresh_Node.shp"), time.time() + 60)
        item = harness([_FakeLayer("fresh", fresh)])
        item.manager._check()
        assert item.flagged() == set()


class TestGhostIndicators:
    def test_ghost_on_an_unrelated_node_is_swept(self, project, harness):
        """A node that inherited an indicator from a destroyed one loses it on the next pass."""
        _projDir, paths = project
        item = harness([_FakeLayer("pipes", paths["input"])])
        ghost = MagicMock()
        ghost.toolTip.return_value = item.manager._tooltip()
        item.view.addIndicator(item.nodes["pipes"], ghost)

        item.manager._check()

        assert item.flagged() == set()

    def test_duplicate_on_a_stale_node_is_reduced_to_one(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._check()
        ghost = MagicMock()
        ghost.toolTip.return_value = item.manager._tooltip()
        item.view.addIndicator(item.nodes["results"], ghost)

        item.manager._check()

        assert len(item.view.indicators(item.nodes["results"])) == 1

    def test_other_plugins_indicators_are_left_alone(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("pipes", paths["input"])])
        foreign = MagicMock()
        foreign.toolTip.return_value = "Filtered layer"
        item.view.addIndicator(item.nodes["pipes"], foreign)

        item.manager._check()

        assert item.view.indicators(item.nodes["pipes"]) == [foreign]

    def test_indicator_leaves_the_node_before_it_dies(self, project, harness):
        """The view keys indicators by node pointer: a leaked one resurfaces on the next
        project, attached to whatever node lands on the same address."""
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._check()
        assert item.flagged() == {"results"}

        item.manager._onLayersWillBeRemoved(["results"])

        assert item.flagged() == set()

    def test_will_be_removed_repaints(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._check()
        item.view.viewport().update.reset_mock()

        item.manager._onLayersWillBeRemoved(["results"])

        item.view.viewport().update.assert_called_once()

    def test_will_be_removed_accepts_layer_objects(self, project, harness):
        """PyQt may deliver either overload of layersWillBeRemoved."""
        _projDir, paths = project
        layer = _FakeLayer("results", paths["results"])
        item = harness([layer])
        item.manager._check()

        item.manager._onLayersWillBeRemoved([layer])

        assert item.flagged() == set()


class TestRefresh:
    def test_adding_an_indicator_repaints_the_viewport(self, project, harness):
        """update() on the view does not reach the viewport, so the row would only redraw
        when the legend was scrolled."""
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])

        item.manager._check()

        item.view.viewport().update.assert_called_once()

    def test_a_pass_that_changes_nothing_does_not_repaint(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._check()
        item.view.viewport().update.reset_mock()

        item.manager._check()

        item.view.viewport().update.assert_not_called()

    def test_new_layers_schedule_a_debounced_check(self, project, harness):
        """A rebuilt group gives the layer a new node with no indicator on it; waiting for
        the 5 s tick to put it back is what looked like a slow refresh."""
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        # QTimer is mocked at class level, so every instance shares one recorder.
        item.manager._pending.start.reset_mock()

        item.manager._onLayersAdded([])

        item.manager._pending.start.assert_called_once()


class TestPluginReload:
    """A reloaded plugin leaves the previous manager connected and ticking unless it is
    found and shut down: it closes over the old plugin's blank project info, so its idea of
    what is stale is 'nothing', and it strips every warning the new manager adds."""

    def test_a_new_manager_stops_the_previous_one(self, project, harness):
        _projDir, paths = project
        first = harness([_FakeLayer("results", paths["results"])])
        second = harness([_FakeLayer("results", paths["results"])])

        assert first.manager._stopped is True
        assert second.manager._stopped is False

    def test_a_superseded_manager_touches_nothing(self, project, harness):
        _projDir, paths = project
        first = harness([_FakeLayer("results", paths["results"])])
        first.manager._check()
        harness([_FakeLayer("results", paths["results"])])

        # The zombie's own view still shows what it put there; what matters is that
        # another pass neither adds nor removes anything.
        first.view.viewport().update.reset_mock()
        first.manager._check()
        first.manager._onLayersWillBeRemoved(["results"])

        first.view.viewport().update.assert_not_called()

    def test_stop_disconnects_even_if_clearing_fails(self, project, harness):
        """stop() runs inside unload()'s blanket suppress: a failure while clearing the
        icons must not leave the manager connected."""
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._clearAll = MagicMock(side_effect=RuntimeError("view already gone"))

        item.manager.stop()

        assert item.manager._stopped is True
        assert item.manager._isActive() is False
