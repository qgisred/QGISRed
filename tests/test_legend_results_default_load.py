# -*- coding: utf-8 -*-
"""Loading a shipped result style into the Legend Editor replays the strategy it carries.

The result styles whose classes depend on the data (Pretty Breaks) ship placeholder classes
and a legend strategy; the dock replays it through setStyle, so the editor's "Load Default
Style" has to do the same or the layer would show the placeholders.
"""
from unittest.mock import MagicMock, patch

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

_DIALOG_MOD = "QGISRed.ui.project.qgisred_legends_dialog"


def _dialog(identifier, fieldName):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.customProperty.side_effect = (
        lambda key, default=None: identifier if key == "qgisred_identifier" else default)
    dialog.currentFieldName = fieldName
    dialog.loadStyleKeepingLabelVisibility = MagicMock()
    dialog.restoreResultNullClass = MagicMock()
    dialog.showAppliedLayerStyle = MagicMock()
    return dialog


class TestApplyStyleFileToLayer:
    def test_a_result_layer_replays_the_strategy_of_the_file_on_the_displayed_field(self):
        dialog = _dialog("qgisred_node_head", "Head")
        with patch(_DIALOG_MOD + ".QGISRedStylingUtils") as styling:
            dialog.applyStyleFileToLayer("/plugin/defaults/layerStyles/NodeHead.qml.bak")

        styling.return_value.applyStrategyFromLayer.assert_called_once_with(dialog.currentLayer, "Head")
        dialog.loadStyleKeepingLabelVisibility.assert_called_once_with("/plugin/defaults/layerStyles/NodeHead.qml.bak")
        dialog.restoreResultNullClass.assert_called_once()

    def test_an_input_layer_is_loaded_as_it_is(self):
        dialog = _dialog("qgisred_pipes", "Diameter")
        with patch(_DIALOG_MOD + ".QGISRedStylingUtils") as styling:
            dialog.applyStyleFileToLayer("/plugin/defaults/layerStyles/Pipes.qml.bak")

        styling.return_value.applyStrategyFromLayer.assert_not_called()
