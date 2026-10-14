# -*- coding: utf-8 -*-
"""The classes of a tool output come with its data: the Legend Editor shows no class tools for them.

Connectivity, Hydraulic Sectors, Demand Sectors, Isolated Segments and Trees layers hide the
Add all values, + and - buttons and keep them disabled; a thematic map on a category keeps them.
The up and down arrows that moved a class are gone: the Class Order entry orders the classes.
"""
import os

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeLayer:
    def __init__(self, identifier):
        self.identifier = identifier

    def customProperty(self, name):
        return self.identifier if name == "qgisred_identifier" else None


class FakeWidget:
    def __init__(self):
        self.visible = None
        self.enabled = None

    def setVisible(self, visible):
        self.visible = bool(visible)

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


def _dialog(identifier):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = FakeLayer(identifier) if identifier else None
    dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
    for name in ("btClassPlus", "btClassMinus", "btClassifyAll", "labelClass", "labelFrameLegends",
                 "labelClassOrder", "cbClassOrder"):
        setattr(dialog, name, FakeWidget())
    dialog.updateClassCountWidgetsVisibility = lambda: None
    return dialog


TOOL_LAYERS = [
    "qgisred_connectivity_links", "qgisred_hydraulicsectors_links", "qgisred_hydraulicsectors_nodes",
    "qgisred_demandsectors_links", "qgisred_demandsectors_nodes", "qgisred_isolatedsegments_nodes",
    "qgisred_tree_links", "qgisred_tree_nodes",
]
EDITABLE_LAYERS = ["qgisred_query_pipes_material", "qgisred_demandbuilder_sectors", "qgisred_pipes", None]


class TestWhichLayersBringTheirClasses:
    @pytest.mark.parametrize("identifier", TOOL_LAYERS)
    def test_the_tool_outputs_do(self, identifier):
        assert _dialog(identifier).hasToolDefinedClasses() is True

    @pytest.mark.parametrize("identifier", EDITABLE_LAYERS)
    def test_the_other_layers_do_not(self, identifier):
        assert _dialog(identifier).hasToolDefinedClasses() is False


class TestTheClassTools:
    def test_they_are_hidden_for_a_tool_output(self):
        dialog = _dialog("qgisred_demandsectors_links")
        dialog.updateClassButtonsVisibility(True, False, False)
        assert (dialog.btClassPlus.visible, dialog.btClassMinus.visible, dialog.btClassifyAll.visible) == (
            False, False, False)
        assert (dialog.labelClass.visible, dialog.cbClassOrder.visible) == (True, True)

    def test_they_are_shown_for_a_thematic_map_on_a_category(self):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateClassButtonsVisibility(True, False, False)
        assert (dialog.btClassPlus.visible, dialog.btClassMinus.visible, dialog.btClassifyAll.visible) == (
            True, True, True)

    def test_they_stay_disabled_for_a_tool_output_whatever_is_selected(self):
        dialog = _dialog("qgisred_hydraulicsectors_nodes")
        dialog.getSelectedRows = lambda: [0]
        dialog.updateButtonStates()
        assert (dialog.btClassPlus.enabled, dialog.btClassMinus.enabled) == (False, False)


class TestTheArrowsAreGone:
    def test_the_dialog_has_no_move_buttons(self):
        with open(os.path.join(PLUGIN_ROOT, "ui", "project", "qgisred_legends_dialog.ui"), encoding="utf-8") as ui:
            text = ui.read()
        assert "btUp" not in text and "btDown" not in text and "arrowType" not in text

    def test_the_dialog_has_no_move_handlers(self):
        assert not {"moveClassUp", "moveClassDown", "moveRow", "swapTableRows"} & set(vars(QGISRedLegendsDialog))
