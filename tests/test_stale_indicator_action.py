# -*- coding: utf-8 -*-
"""What clicking the legend's outdated-layer warning actually does.

The manager only says *which* layer went stale and *how*; this is the half that asks the
user and then runs the right tool — a simulation for results, a rebuild for a thematic map,
the tool that wrote the layer for the rest, and nothing at all for the layers that have no
one-click way back.
"""
import inspect
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.qgisred import QGISRed
from QGISRed.sections.layer_management_section import LayerManagementSection
from QGISRed.tools.utils.qgisred_stale_layer_manager import (
    KIND_RESULTS, KIND_THEMATIC, KIND_TREE, KIND_CONNECTIVITY, KIND_DERIVED, TOOL_RERUN_BY_KIND)

# Patched on the module under test, never on qgis.PyQt.QtWidgets: patch() on Python 3.9
# walks getattr from __import__("qgis"), which on the mocked qgis package hands out a
# fresh child mock instead of the QtWidgets the code imports — so the patch missed.
_MESSAGE_BOX = "QGISRed.sections.layer_management_section.QMessageBox"
_PROJECT = "QGISRed.sections.layer_management_section.QgsProject"
_TIMER = "QGISRed.sections.layer_management_section.QTimer"

THEME_ID = "qgisred_query_pipes_diameter"
TREE_LAYER_ID = "tree_nodes_layer_id"

# Results have a confirmation test of their own, and the parametrised ones below assert that
# nothing but the tool they asked for ran.
TOOL_RERUNS = [(kind, method, args) for kind, (method, args) in TOOL_RERUN_BY_KIND.items()
               if kind != KIND_RESULTS]

# Every plugin method this feature calls by name, with the arguments it passes.
PLUGIN_ENTRY_POINTS = list(TOOL_RERUN_BY_KIND.values()) + [
    ("runRebuildThematicMaps", ([THEME_ID],)),
    ("runAutoTree", (TREE_LAYER_ID,)),
]


def _section():
    section = object.__new__(LayerManagementSection)
    section.iface = MagicMock()
    section.tr = lambda message: message
    section.runRebuildThematicMaps = MagicMock(return_value=True)
    section.runAutoTree = MagicMock()
    for method, _args in TOOL_RERUN_BY_KIND.values():
        setattr(section, method, MagicMock())
    section._staleLayerManager = MagicMock()
    return section


def _themeLayer(identifier=THEME_ID):
    layer = MagicMock()
    layer.customProperty.side_effect = (
        lambda name, *a: identifier if name == "qgisred_identifier" else None)
    return layer


@pytest.fixture
def answer():
    """Drives the confirmation dialog; yields a setter for what the user replies."""
    with patch(_MESSAGE_BOX) as messageBox:
        # Real StandardButton values are flags the code ORs together.
        messageBox.StandardButton.Yes = 1
        messageBox.StandardButton.No = 2

        def reply(value):
            messageBox.question.return_value = value
            return messageBox

        yield reply


@pytest.fixture
def project():
    with patch(_PROJECT) as qgsProject:
        yield qgsProject.instance.return_value


class TestConfirmation:

    def test_results_run_the_simulation_again_when_accepted(self, answer, project):
        section = _section()
        answer(1)

        section._runStaleIndicatorAction("results", KIND_RESULTS)

        section.runModel.assert_called_once_with()

    def test_declining_leaves_the_results_alone(self, answer, project):
        section = _section()
        answer(2)

        section._runStaleIndicatorAction("results", KIND_RESULTS)

        section.runModel.assert_not_called()

    def test_a_thematic_map_is_rebuilt_by_its_own_identifier_when_accepted(self, answer, project):
        section = _section()
        answer(1)
        project.mapLayer.return_value = _themeLayer()

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section.runRebuildThematicMaps.assert_called_once_with([THEME_ID])

    def test_declining_leaves_the_thematic_map_alone(self, answer, project):
        section = _section()
        answer(2)
        project.mapLayer.return_value = _themeLayer()

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section.runRebuildThematicMaps.assert_not_called()

    def test_an_informational_warning_asks_nothing_and_does_nothing(self, answer, project):
        section = _section()
        messageBox = answer(1)

        section._runStaleIndicatorAction("issues", KIND_DERIVED)

        messageBox.question.assert_not_called()
        section.runModel.assert_not_called()
        section.runRebuildThematicMaps.assert_not_called()


class TestToolRerun:
    """A tool's warning re-runs that tool, exactly as its menu entry would."""

    @pytest.mark.parametrize("kind, runner, args", TOOL_RERUNS)
    def test_accepting_runs_the_tool_again(self, answer, project, kind, runner, args):
        section = _section()
        answer(1)

        section._runStaleIndicatorAction("layer", kind)

        getattr(section, runner).assert_called_once_with(*args)
        section.runModel.assert_not_called()
        section.runRebuildThematicMaps.assert_not_called()

    @pytest.mark.parametrize("kind, runner, args", TOOL_RERUNS)
    def test_declining_leaves_the_tool_alone(self, answer, project, kind, runner, args):
        section = _section()
        answer(2)

        section._runStaleIndicatorAction("layer", kind)

        getattr(section, runner).assert_not_called()

    def test_the_warning_is_left_to_the_tool_to_clear(self, answer, project):
        """The tool re-checks itself once its files are written; a cancelled dialog writes
        nothing, and the warning has to stay up."""
        section = _section()
        answer(1)

        section._runStaleIndicatorAction("layer", KIND_CONNECTIVITY)

        section._staleLayerManager.forceCheck.assert_not_called()


class TestThematicRebuild:

    def test_the_warning_is_cleared_as_soon_as_the_map_is_rebuilt(self, answer, project):
        """The rebuild re-stamps the layer, but the sweep is on a five second timer."""
        section = _section()
        answer(1)
        project.mapLayer.return_value = _themeLayer()

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section._staleLayerManager.forceCheck.assert_called_once_with()

    def test_a_rebuild_that_did_not_happen_leaves_the_warning_up(self, answer, project):
        section = _section()
        answer(1)
        section.runRebuildThematicMaps.return_value = False
        project.mapLayer.return_value = _themeLayer()

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section._staleLayerManager.forceCheck.assert_not_called()

    def test_a_layer_closed_before_the_answer_came_back_is_not_rebuilt(self, answer, project):
        section = _section()
        answer(1)
        project.mapLayer.return_value = None

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section.runRebuildThematicMaps.assert_not_called()

    def test_a_layer_that_is_not_a_thematic_map_is_not_rebuilt(self, answer, project):
        section = _section()
        answer(1)
        project.mapLayer.return_value = _themeLayer(identifier="qgisred_pipes")

        section._runStaleIndicatorAction("theme", KIND_THEMATIC)

        section.runRebuildThematicMaps.assert_not_called()


class TestTreeAutoRefresh:
    """Unlike the other tools, Tree needs to know *which* tree went stale -- there is no
    fixed-args table entry for it, see TOOL_RERUN_BY_KIND's comment."""

    def test_a_tree_warning_calls_auto_tree_with_the_layer_id_when_accepted(self, answer, project):
        section = _section()
        answer(1)

        section._runStaleIndicatorAction(TREE_LAYER_ID, KIND_TREE)

        section.runAutoTree.assert_called_once_with(TREE_LAYER_ID)

    def test_declining_leaves_the_tree_alone(self, answer, project):
        section = _section()
        answer(2)

        section._runStaleIndicatorAction(TREE_LAYER_ID, KIND_TREE)

        section.runAutoTree.assert_not_called()


class TestDeferral:

    def test_the_action_never_runs_inside_the_click(self):
        """clicked() arrives from the layer tree view's own mouse handler, and both actions
        rebuild the nodes that view is in the middle of handling."""
        section = _section()

        with patch(_TIMER) as timer:
            section.onStaleIndicatorClicked("results", KIND_RESULTS)

            delay, deferred = timer.singleShot.call_args.args
            assert delay == 0

        section.runModel.assert_not_called()

        with patch(_MESSAGE_BOX) as messageBox, patch(_PROJECT):
            messageBox.StandardButton.Yes = 1
            messageBox.StandardButton.No = 2
            messageBox.question.return_value = 1
            deferred()

        section.runModel.assert_called_once_with()


class TestEntryPointsExist:
    """The tools live in sibling section mixins and are reached through getattr on the
    composed plugin, so a rename would only surface when a user clicks that one warning."""

    @pytest.mark.parametrize("method", [method for method, _args in PLUGIN_ENTRY_POINTS])
    def test_the_plugin_has_the_method(self, method):
        assert hasattr(QGISRed, method), f"QGISRed has no {method}()"

    @pytest.mark.parametrize("method, args", PLUGIN_ENTRY_POINTS)
    def test_the_method_takes_the_arguments_the_click_passes(self, method, args):
        inspect.signature(getattr(QGISRed, method)).bind(MagicMock(), *args)
