# -*- coding: utf-8 -*-
"""What clicking the legend's outdated-layer warning actually does.

The manager only says *which* layer went stale and *how*; this is the half that asks the
user and then runs the right tool — a simulation for results, a rebuild for a thematic map,
and nothing at all for the layers that have no one-click way back.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.sections.layer_management_section import LayerManagementSection
from QGISRed.tools.utils.qgisred_stale_layer_manager import KIND_RESULTS, KIND_THEMATIC, KIND_DERIVED

_MESSAGE_BOX = "qgis.PyQt.QtWidgets.QMessageBox"
_PROJECT = "QGISRed.sections.layer_management_section.QgsProject"
_TIMER = "QGISRed.sections.layer_management_section.QTimer"

THEME_ID = "qgisred_query_pipes_diameter"


def _section():
    section = object.__new__(LayerManagementSection)
    section.iface = MagicMock()
    section.tr = lambda message: message
    section.runModel = MagicMock()
    section.runRebuildThematicMaps = MagicMock(return_value=True)
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
