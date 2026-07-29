# -*- coding: utf-8 -*-
"""Applying a legend leaves a result layer rule-based, with its NULL class.

The dialog builds a graduated renderer, but the results dock assumes result layers are
rule-based: applySymbolScaleFactors returns early otherwise, so every Appearance factor
silently stops working. A graduated renderer also skips NULL features entirely, so they
would disappear from the map instead of being drawn grey.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog


@pytest.fixture
def styling():
    with patch("QGISRed.ui.project.qgisred_legends_dialog.QGISRedStylingUtils") as utils:
        yield utils


def _dialog(identifier="qgisred_node_pressure"):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.projectDirectory = "C:/proj"
    dialog.networkName = "Net"
    dialog.qgisInterface = MagicMock()
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.customProperty.return_value = identifier
    dialog.buildRendererFromDialog = MagicMock(return_value=MagicMock())
    dialog.ensureLayerVisible = MagicMock()
    return dialog


class TestRestoreResultNullClass:
    def test_a_result_layer_gets_the_null_class_back(self, styling):
        dialog = _dialog("qgisred_link_flow")

        dialog.restoreResultNullClass()

        styling.return_value.applyNullStyle.assert_called_once_with(dialog.currentLayer)

    def test_other_layers_are_left_alone(self, styling):
        # Only result layers follow the NULL-class convention; an input layer has no
        # business being converted to rule-based here.
        dialog = _dialog("qgisred_pipes")

        dialog.restoreResultNullClass()

        styling.return_value.applyNullStyle.assert_not_called()

    def test_a_failure_does_not_break_applying(self, styling):
        dialog = _dialog()
        styling.return_value.applyNullStyle.side_effect = RuntimeError("boom")

        dialog.restoreResultNullClass()  # must not raise


class TestSavingIsNotAffected:
    """The file must keep the graduated form the dialog shows, not the applied one.

    applyNullStyle bakes the classified column into every rule filter, and LinkFlow.qml is
    shared by Flow, Flow_Sig and Flow_Unsig: a rule-based file could not be re-pointed at
    another of them on load, the way setClassAttribute re-points a graduated one.
    """

    def test_the_file_is_written_from_the_dialog_not_from_the_layer(self, styling):
        dialog = _dialog()
        dialog.buildStrategyFromCurrentUi = MagicMock(return_value=None)
        module = "QGISRed.ui.project.qgisred_legends_dialog."

        with patch(module + "QgsVectorLayer") as vectorLayer, patch(module + "QgsMapLayerStyle"):
            tempLayer = vectorLayer.return_value
            tempLayer.isValid.return_value = True

            dialog.saveDialogLegendToFile("C:/proj/layerStyles/Net_NodePressure.qml", [])

        tempLayer.setRenderer.assert_called_once_with(dialog.buildRendererFromDialog.return_value)
        tempLayer.saveNamedStyle.assert_called_once()
        dialog.currentLayer.setRenderer.assert_not_called()
        dialog.currentLayer.saveNamedStyle.assert_not_called()
        styling.return_value.applyNullStyle.assert_not_called()


class TestApplyLegendRestoresIt:
    def test_applying_on_a_result_layer_restores_the_null_class(self, styling):
        dialog = _dialog()

        dialog.applyLegend()

        dialog.currentLayer.setRenderer.assert_called_once()
        styling.return_value.applyNullStyle.assert_called_once_with(dialog.currentLayer)

    def test_nothing_is_restored_when_there_is_no_renderer_to_commit(self, styling):
        dialog = _dialog()
        dialog.buildRendererFromDialog.return_value = None

        dialog.applyLegend()

        dialog.currentLayer.setRenderer.assert_not_called()
        styling.return_value.applyNullStyle.assert_not_called()
