# -*- coding: utf-8 -*-
"""The classes of a tool output come with its data: the Legend Editor shows no class tools for them.

Connectivity, Hydraulic Sectors, Demand Sectors, Isolated Segments and Trees layers hide the
Current/All selector and the + and - buttons, and keep them disabled; a thematic map on a
category keeps them. The up and down arrows move a class of a categorized legend by hand.
"""
import os

import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeLineEdit:
    pass


@pytest.fixture(autouse=True)
def valueCellsAreLineEdits(monkeypatch):
    monkeypatch.setattr(legendsModule, "QLineEdit", FakeLineEdit)


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


class FakeTable:
    def __init__(self, rows=3):
        self.rows = rows

    def rowCount(self):
        return self.rows

    def cellWidget(self, row, column):
        return None


def _dialog(identifier):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.currentLayer = FakeLayer(identifier) if identifier else None
    dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
    for name in ("btClassPlus", "btClassMinus", "cbClasses", "leClassCount", "labelClassCount", "labelClass",
                 "labelFrameLegends", "labelClassOrder", "cbClassOrder", "line_4", "btUp", "btDown"):
        setattr(dialog, name, FakeWidget())
    dialog.tableView = FakeTable()
    dialog.classCountRowVisible = True
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
        assert (dialog.btClassPlus.visible, dialog.btClassMinus.visible, dialog.cbClasses.visible) == (
            False, False, False)
        assert (dialog.labelClass.visible, dialog.cbClassOrder.visible, dialog.labelClassCount.visible) == (
            True, True, True)

    def test_they_are_shown_for_a_thematic_map_on_a_category(self):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateClassButtonsVisibility(True, False, False)
        assert (dialog.btClassPlus.visible, dialog.btClassMinus.visible, dialog.cbClasses.visible) == (
            True, True, True)

    def test_they_stay_disabled_for_a_tool_output_whatever_is_selected(self):
        dialog = _dialog("qgisred_hydraulicsectors_nodes")
        dialog.getSelectedRows = lambda: [0]
        dialog.updateButtonStates()
        assert (dialog.btClassPlus.enabled, dialog.btClassMinus.enabled) == (False, False)


class TestTheClassesRow:
    """Categorized: Current/All, + and -, and the number of classes. Graduated: the count box."""

    def test_a_categorized_legend_shows_the_selector_and_the_count_text(self):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateClassCountWidgetsVisibility()
        assert (dialog.cbClasses.visible, dialog.labelClassCount.visible, dialog.leClassCount.visible) == (
            True, True, False)

    def test_a_graduated_legend_keeps_its_count_box(self):
        dialog = _dialog("qgisred_query_pipes_diameter")
        dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_NUMERIC
        dialog.updateClassCountWidgetsVisibility()
        assert (dialog.cbClasses.visible, dialog.labelClassCount.visible, dialog.leClassCount.visible) == (
            False, False, True)

    def test_the_separator_closes_the_classes_group_only_when_there_is_one(self):
        dialog = _dialog("qgisred_pipes")
        dialog.updateClassButtonsVisibility(False, False, False)
        assert dialog.line_4.visible is False
        dialog.updateClassButtonsVisibility(True, False, False)
        assert dialog.line_4.visible is True


class TestTheArrows:
    def test_the_dialog_has_the_move_buttons(self):
        with open(os.path.join(PLUGIN_ROOT, "ui", "project", "qgisred_legends_dialog.ui"), encoding="utf-8") as ui:
            text = ui.read()
        assert 'name="btUp"' in text and 'name="btDown"' in text

    def test_they_are_shown_for_categorized_legends_only(self):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateNavigationButtonsVisibility(True)
        assert (dialog.btUp.visible, dialog.btDown.visible) == (True, True)
        dialog.updateNavigationButtonsVisibility(False)
        assert (dialog.btUp.visible, dialog.btDown.visible) == (False, False)

    @pytest.mark.parametrize("selected, expected", [
        ([0], (False, True)), ([1], (True, True)), ([2], (True, False)), ([0, 1], (False, False)), ([], (False, False)),
    ])
    def test_they_move_a_single_class_within_the_table(self, selected, expected):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateMoveButtonsState(True, selected)
        assert (dialog.btUp.enabled, dialog.btDown.enabled) == expected

    def test_a_fixed_legend_keeps_its_order(self):
        dialog = _dialog("qgisred_query_pipes_material")
        dialog.updateMoveButtonsState(False, [1])
        assert (dialog.btUp.enabled, dialog.btDown.enabled) == (False, False)
