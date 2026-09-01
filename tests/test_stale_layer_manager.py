# -*- coding: utf-8 -*-
"""What the staleness warning may land on, and how it is kept off everything else."""
import os
import time
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_stale_layer_manager import (
    StaleLayerManager, KIND_RESULTS, KIND_THEMATIC, KIND_DERIVED)
from QGISRed.tools.utils.qgisred_project_utils import QGISRedProjectUtils


NET = "test123"


class _FakeLayer:
    def __init__(self, layerId, path, identifier="", properties=None, renderer=None):
        self._id = layerId
        self._path = path
        self._properties = {"qgisred_identifier": identifier}
        self._properties.update(properties or {})
        self._renderer = renderer

    def id(self):
        return self._id

    def dataProvider(self):
        provider = MagicMock()
        provider.dataSourceUri.return_value = self._path
        return provider

    def customProperty(self, name, default=None):
        return self._properties.get(name, default)

    def setCustomProperty(self, name, value):
        self._properties[name] = value

    def renderer(self):
        return self._renderer


class _FakeLegendItem:
    def __init__(self, label):
        self._label = label

    def label(self):
        return self._label


class _FakeRenderer:
    def __init__(self, labels):
        self._labels = labels

    def legendSymbolItems(self):
        return [_FakeLegendItem(label) for label in self._labels]


class _FakeNode:
    def __init__(self, layerId):
        self._layerId = layerId

    def layerId(self):
        return self._layerId


class _FakeRect:
    def __init__(self, top, height):
        self._top = top
        self._height = height

    def top(self):
        return self._top

    def height(self):
        return self._height


class _FakeIndex:
    def __init__(self, node=None):
        self.node = node

    def isValid(self):
        return self.node is not None


class _FakePoint:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class _FakeView:
    """Stands in for QgsLayerTreeView, keyed by node like the real one.

    Rows only exist for the hover tests, which have to place them: everything else about
    the view is indicator bookkeeping.
    """

    ROW_HEIGHT = 20
    VIEWPORT_WIDTH = 300

    def __init__(self):
        self._byNode = {}
        self._viewport = MagicMock()
        self._viewport.width.return_value = self.VIEWPORT_WIDTH
        self._rows = []        # (node, top of its row), in the order they were placed
        self._markWidth = 0

    def viewport(self):
        return self._viewport

    def indicators(self, node):
        return list(self._byNode.get(id(node), []))

    def addIndicator(self, node, indicator):
        self._byNode.setdefault(id(node), []).append(indicator)

    def removeIndicator(self, node, indicator):
        self._byNode.get(id(node), []).remove(indicator)

    # -- geometry, for the hover cursor ------------------------------------

    def placeRow(self, node, top=0):
        self._rows.append((node, top))

    def setLayerMarkWidth(self, width):
        self._markWidth = width

    def layerMarkWidth(self):
        return self._markWidth

    def indexAt(self, pos):
        for node, top in self._rows:
            if top <= pos.y() < top + self.ROW_HEIGHT:
                return _FakeIndex(node)
        return _FakeIndex()

    def index2node(self, index):
        return index.node

    def visualRect(self, index):
        for node, top in self._rows:
            if node is index.node:
                return _FakeRect(top, self.ROW_HEIGHT)
        return _FakeRect(0, 0)


def _fakeIndicator(*_args):
    """A stand-in whose property() and toolTip() answer what was set on it.

    A bare MagicMock class hands out one shared return_value, so every indicator in a test
    would be the same object — and the manager keys its ownership by indicator, one entry
    per kind. Two kinds in one project would then overwrite each other every pass.
    """
    indicator = MagicMock()
    state = {}
    indicator.setProperty.side_effect = state.__setitem__
    indicator.property.side_effect = lambda name: state.get(name)
    indicator.setToolTip.side_effect = lambda text: state.__setitem__("tooltip", text)
    indicator.toolTip.side_effect = lambda: state.get("tooltip")
    return indicator


@pytest.fixture(autouse=True)
def _stubQtObjects():
    """Stand in for the two Qt objects the fake project tree cannot satisfy.

    QgsLayerTreeViewIndicator needs a real QgsLayerTreeView, and the debounce tests
    assert on the QTimer instead of waiting five seconds for its tick.
    """
    module = "QGISRed.tools.utils.qgisred_stale_layer_manager."
    with patch(module + "QgsLayerTreeViewIndicator", side_effect=_fakeIndicator), \
         patch(module + "QTimer"):
        yield


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

    def __init__(self, projDir, layers, nodes=None, onClick=None):
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

        self.onClick = onClick
        self.manager = StaleLayerManager(iface, lambda: (NET, projDir), onClick)

    def flagged(self):
        """Layer ids whose node currently shows a warning."""
        return {
            layerId for layerId, node in self.nodes.items()
            if self.view.indicators(node)
        }

    def indicatorOn(self, layerId):
        """The single indicator attached to `layerId`'s node."""
        indicators = self.view.indicators(self.nodes[layerId])
        assert len(indicators) == 1
        return indicators[0]

    def clickSlot(self, layerId):
        """The slot the manager connected to that indicator's clicked() signal."""
        return self.indicatorOn(layerId).clicked.connect.call_args.args[0]

    def close(self):
        self._patch.stop()


@pytest.fixture
def harness(project):
    made = []

    def build(layers, nodes=None, onClick=None):
        projDir, _paths = project
        item = _Harness(projDir, layers, nodes, onClick)
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


class TestOutdatedThemes:
    """Thematic map layers are flagged when the setting they were built with —
    unit system, flow units or headloss formula — no longer matches the project."""

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def test_theme_built_with_current_settings_is_not_flagged(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("theme", paths["input"], properties={
            "qgisred_theme_units": "SI",
            "qgisred_theme_formula": "D-W",
            "qgisred_theme_flow_units": "LPS",
        })])
        item.manager._check()
        assert item.flagged() == set()

    def test_theme_built_with_the_other_unit_system_is_flagged(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("theme", paths["input"], properties={
            "qgisred_theme_units": "US",
        })])
        item.manager._check()
        assert item.flagged() == {"theme"}

    def test_base_demand_theme_is_flagged_when_flow_units_change(self, project, harness):
        """CMH and LPS are both SI: the base demand theme reacts to the flow unit
        itself, not the unit system."""
        _projDir, paths = project
        item = harness([_FakeLayer("theme", paths["input"], properties={
            "qgisred_theme_flow_units": "CMH",
        })])
        item.manager._check()
        assert item.flagged() == {"theme"}

    def test_roughness_theme_is_flagged_when_the_formula_changes(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("theme", paths["input"], properties={
            "qgisred_theme_formula": "H-W",
        })])
        item.manager._check()
        assert item.flagged() == {"theme"}


class TestThemeUnitsBackfill:
    """Length and diameter maps created before the qgisred_theme_units stamp existed
    carry none; their build units are inferred from the unit in the legend labels."""

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def test_legacy_us_lengths_map_is_stamped_and_flagged_on_an_si_project(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length",
                           renderer=_FakeRenderer(["0 < 1 ft", "1 < 10 ft", "> 1000 ft"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") == "US"
        assert item.flagged() == {"theme"}

    def test_legacy_si_diameters_map_is_stamped_but_not_flagged(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_diameter",
                           renderer=_FakeRenderer(["< 100 mm", "100 < 150 mm", "> 600 mm"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") == "SI"
        assert item.flagged() == set()

    def test_labels_mixing_both_systems_are_not_trusted(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length",
                           renderer=_FakeRenderer(["0 - 1 m", "1 - 10 in"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") is None
        assert item.flagged() == set()

    def test_labels_without_unit_tokens_leave_the_layer_alone(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length",
                           renderer=_FakeRenderer(["low", "high", "Unknown"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") is None
        assert item.flagged() == set()

    def test_a_unitless_class_does_not_block_agreeing_labels(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length",
                           renderer=_FakeRenderer(["0 - 1 m", "> 1000 m", "Unknown"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") == "SI"

    def test_an_existing_stamp_is_never_overwritten(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length",
                           properties={"qgisred_theme_units": "SI"},
                           renderer=_FakeRenderer(["0 < 1 ft", "> 1000 ft"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") == "SI"
        assert item.flagged() == set()

    def test_other_thematic_maps_are_not_stamped(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_material",
                           renderer=_FakeRenderer(["0 - 1 m", "> 1000 m"]))
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") is None

    def test_a_layer_without_a_renderer_does_not_break_the_pass(self, project, harness):
        _projDir, paths = project
        layer = _FakeLayer("theme", paths["input"], identifier="qgisred_query_pipes_length")
        item = harness([layer])
        item.manager._check()
        assert layer.customProperty("qgisred_theme_units") is None
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
        foreign.property.return_value = None
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


class TestStalenessKinds:
    """A warning has to say what went out of date, because that decides what a click does."""

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def test_results_are_the_kind_a_simulation_can_fix(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])

        assert item.manager._kindByLayerId() == {"results": KIND_RESULTS}

    def test_issues_and_queries_are_only_reported(self, project, harness):
        _projDir, paths = project
        item = harness([
            _FakeLayer("issues", paths["issues"]),
            _FakeLayer("queries", paths["queries"]),
        ])

        assert item.manager._kindByLayerId() == {"issues": KIND_DERIVED, "queries": KIND_DERIVED}

    def test_an_outdated_theme_is_its_own_kind(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("theme", paths["input"],
                                   properties={"qgisred_theme_units": "US"})])

        assert item.manager._kindByLayerId() == {"theme": KIND_THEMATIC}

    def test_only_the_actionable_tooltips_invite_a_click(self, project, harness):
        _projDir, paths = project
        manager = harness([_FakeLayer("pipes", paths["input"])]).manager
        module = "QGISRed.tools.utils.qgisred_stale_layer_manager."

        # tr() goes through the mocked QCoreApplication, which answers with a MagicMock;
        # translate to identity so the assertions can read the strings themselves.
        with patch(module + "QCoreApplication") as translator:
            translator.translate.side_effect = lambda _context, message: message

            assert "Click" in manager._tooltip(KIND_RESULTS)
            assert "Click" in manager._tooltip(KIND_THEMATIC)
            assert "Click" not in manager._tooltip(KIND_DERIVED)
            assert manager._tooltip() == manager._tooltip(KIND_DERIVED)


class TestIndicatorClicks:
    """Clicking an actionable warning hands the layer and its kind to the plugin."""

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def test_a_results_warning_dispatches_its_layer_and_kind(self, project, harness):
        _projDir, paths = project
        onClick = MagicMock()
        item = harness([_FakeLayer("results", paths["results"])], onClick=onClick)
        item.manager._check()

        item.clickSlot("results")(MagicMock())

        onClick.assert_called_once_with("results", KIND_RESULTS)

    def test_a_theme_warning_dispatches_its_layer_and_kind(self, project, harness):
        _projDir, paths = project
        onClick = MagicMock()
        item = harness([_FakeLayer("theme", paths["input"],
                                   properties={"qgisred_theme_units": "US"})], onClick=onClick)
        item.manager._check()

        item.clickSlot("theme")(MagicMock())

        onClick.assert_called_once_with("theme", KIND_THEMATIC)

    def test_an_informational_warning_is_never_connected(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("issues", paths["issues"])], onClick=MagicMock())
        item.manager._check()

        item.indicatorOn("issues").clicked.connect.assert_not_called()

    def test_without_a_callback_nothing_is_connected(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])])
        item.manager._check()

        item.indicatorOn("results").clicked.connect.assert_not_called()

    def test_a_layer_that_stopped_being_stale_does_nothing(self, project, harness):
        """Up to five seconds pass between the sweep and the click, so what the click is
        worth is worked out when it happens, not when the icon went up."""
        _projDir, paths = project
        onClick = MagicMock()
        item = harness([_FakeLayer("results", paths["results"])], onClick=onClick)
        item.manager._check()
        slot = item.clickSlot("results")
        fresh = time.time() + 60
        os.utime(paths["results"], (fresh, fresh))

        slot(MagicMock())

        onClick.assert_not_called()

    def test_a_superseded_managers_indicator_is_inert(self, project, harness):
        """Its connections outlive it, and the layers it flagged are still flagged."""
        _projDir, paths = project
        onClick = MagicMock()
        item = harness([_FakeLayer("results", paths["results"])], onClick=onClick)
        item.manager._check()
        slot = item.clickSlot("results")
        harness([_FakeLayer("results", paths["results"])], onClick=MagicMock())

        slot(MagicMock())

        onClick.assert_not_called()


class TestIndicatorReuse:
    """An indicator may only be reused when this manager built it for this same kind."""

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def test_a_ghost_is_recognised_by_its_property(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("pipes", paths["input"])])
        ghost = _fakeIndicator()
        ghost.setProperty("qgisredStaleWarning", True)
        item.view.addIndicator(item.nodes["pipes"], ghost)

        item.manager._check()

        assert item.flagged() == set()

    def test_an_adopted_ghost_is_replaced_rather_than_reused(self, project, harness):
        """It carries the right icon but its clicked() belongs to a manager that is gone,
        so keeping it would leave a warning that looks clickable and is not."""
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])], onClick=MagicMock())
        ghost = _fakeIndicator()
        ghost.setProperty("qgisredStaleWarning", True)
        item.view.addIndicator(item.nodes["results"], ghost)

        item.manager._check()

        assert item.indicatorOn("results") is not ghost
        item.indicatorOn("results").clicked.connect.assert_called_once()

    def test_a_layer_that_changes_kind_gets_a_fresh_indicator(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])], onClick=MagicMock())
        item.manager._kindByLayerId = lambda: {"results": KIND_DERIVED}
        item.manager._check()
        informational = item.indicatorOn("results")

        item.manager._kindByLayerId = lambda: {"results": KIND_RESULTS}
        item.manager._check()

        assert item.indicatorOn("results") is not informational
        assert item.indicatorOn("results").toolTip() == item.manager._tooltip(KIND_RESULTS)

    def test_an_unchanged_kind_keeps_the_same_indicator(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("results", paths["results"])], onClick=MagicMock())
        item.manager._check()
        first = item.indicatorOn("results")

        item.manager._check()

        assert item.indicatorOn("results") is first


class TestHoverCursor:
    """The pointer turns into a hand over a warning a click can act on — and only there.

    The icon strip is laid out the way QgsLayerTreeViewProxyStyle does it: cells as wide as
    the row is tall, packed against the right of the viewport, clear of the layer mark and
    of a one-tenth-of-a-row gap. With _FakeView's 20 px rows, a 300 px viewport and no
    layer mark, a lone indicator occupies x 298..317 — off the right edge in this fake,
    which is exactly what a real narrow panel does too, so the tests use its left edge.
    """

    @pytest.fixture(autouse=True)
    def projectSettings(self):
        with patch.object(QGISRedProjectUtils, "getUnits", return_value="SI"), \
             patch.object(QGISRedProjectUtils, "getHeadlossFormula", return_value="D-W"), \
             patch.object(QGISRedProjectUtils, "getFlowUnit", return_value="LPS"):
            yield

    def _flagged(self, project, harness, kind="results", markWidth=0, onClick=None):
        """A harness whose single stale layer already carries its warning, row placed."""
        _projDir, paths = project
        item = harness([_FakeLayer(kind, paths[kind])], onClick=onClick or MagicMock())
        item.view.setLayerMarkWidth(markWidth)
        item.view.placeRow(item.nodes[kind], top=0)
        item.manager._check()
        return item

    def _stripLeft(self, item, count=1):
        height = _FakeView.ROW_HEIGHT
        return (_FakeView.VIEWPORT_WIDTH - height * count
                - height // 10 - item.view.layerMarkWidth())

    def test_the_pointer_over_the_icon_becomes_a_hand(self, project, harness):
        item = self._flagged(project, harness)

        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))

        item.view.viewport().setCursor.assert_called_once()

    def test_the_pointer_over_the_layer_name_is_left_alone(self, project, harness):
        item = self._flagged(project, harness)

        item.manager.updateHoverCursor(_FakePoint(20, 10))

        item.view.viewport().setCursor.assert_not_called()

    def test_the_layer_mark_shifts_the_strip_left(self, project, harness):
        """QGIS reserves a band on the right for the current-layer mark; the icons sit
        before it, so a point that was over the icon without the mark no longer is."""
        item = self._flagged(project, harness, markWidth=30)

        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))
        assert item.view.viewport().setCursor.called

        item.view.viewport().setCursor.reset_mock()
        item.manager.updateHoverCursor(None)
        item.manager.updateHoverCursor(_FakePoint(_FakeView.VIEWPORT_WIDTH - 5, 10))
        item.view.viewport().setCursor.assert_not_called()

    def test_an_informational_warning_gets_no_hand(self, project, harness):
        item = self._flagged(project, harness, kind="issues")

        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))

        item.view.viewport().setCursor.assert_not_called()

    def test_another_plugins_icon_beside_ours_gets_no_hand(self, project, harness):
        """Cells map to the indicator list in paint order, so the one under the pointer
        has to be identified, not merely counted."""
        item = self._flagged(project, harness)
        foreign = _fakeIndicator()
        item.view.addIndicator(item.nodes["results"], foreign)
        left = self._stripLeft(item, count=2)

        item.manager.updateHoverCursor(_FakePoint(left + 5, 10))
        assert item.view.viewport().setCursor.called, "ours is the first cell"

        item.manager.updateHoverCursor(None)
        item.view.viewport().setCursor.reset_mock()
        item.manager.updateHoverCursor(_FakePoint(left + _FakeView.ROW_HEIGHT + 5, 10))
        item.view.viewport().setCursor.assert_not_called()

    def test_leaving_the_tree_restores_the_pointer(self, project, harness):
        item = self._flagged(project, harness)
        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))

        item.manager.updateHoverCursor(None)

        item.view.viewport().unsetCursor.assert_called_once()

    def test_a_row_without_a_warning_is_left_alone(self, project, harness):
        _projDir, paths = project
        item = harness([_FakeLayer("pipes", paths["input"])], onClick=MagicMock())
        item.view.placeRow(item.nodes["pipes"], top=0)
        item.manager._check()

        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))

        item.view.viewport().setCursor.assert_not_called()

    def test_the_pointer_is_not_reset_on_every_move(self, project, harness):
        """MouseMove arrives continuously; only the changes may reach the viewport."""
        item = self._flagged(project, harness)
        overTheName = _FakePoint(20, 10)

        item.manager.updateHoverCursor(overTheName)
        item.manager.updateHoverCursor(overTheName)

        item.view.viewport().unsetCursor.assert_not_called()

    def test_a_stopped_manager_stops_touching_the_pointer(self, project, harness):
        item = self._flagged(project, harness)
        item.manager.stop()
        item.view.viewport().setCursor.reset_mock()

        item.manager.updateHoverCursor(_FakePoint(self._stripLeft(item) + 5, 10))

        item.view.viewport().setCursor.assert_not_called()
