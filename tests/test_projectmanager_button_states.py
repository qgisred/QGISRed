# -*- coding: utf-8 -*-
"""Project Manager buttons enable per selected row, instead of refusing after the click.

The dialog cannot be instantiated (conftest stubs loadUiType), so the widgets are mocked and
updateButtonStates() is exercised directly.
"""
from unittest.mock import MagicMock

import pytest

from QGISRed.ui.general.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog

ROW_ONLY = ("btExport", "btClone", "btGo2Folder")
NEEDS_CLOSED = ("btOpen", "btRemove", "btUnLoad", "btChangeName", "btMove")
ALL_BUTTONS = ROW_ONLY + NEEDS_CLOSED + ("btUp", "btDown")

OPEN_PROJECT = "C:/projects/Net"
OPEN_NETWORK = "Net"


def _dialog(selectedRow=0, rowCount=3, name=OPEN_NETWORK, project=OPEN_PROJECT, hasSelection=True):
    dialog = QGISRedProjectManagerDialog.__new__(QGISRedProjectManagerDialog)
    dialog.tr = lambda text: text
    dialog.ProjectDirectory = OPEN_PROJECT
    dialog.NetworkName = OPEN_NETWORK
    dialog.utils = MagicMock()
    dialog.utils.getUniformedPath.side_effect = lambda p: p

    dialog.twProjectList = MagicMock()
    dialog.twProjectList.rowCount.return_value = rowCount
    dialog._getSelectedRowInfo = lambda: (hasSelection, name, project, selectedRow)

    for attribute in ALL_BUTTONS:
        setattr(dialog, attribute, MagicMock())
    return dialog


def _enabled(dialog, attribute):
    return getattr(dialog, attribute).setEnabled.call_args[0][0]


def _tooltip(dialog, attribute):
    return getattr(dialog, attribute).setToolTip.call_args[0][0]


class TestWithoutSelection:
    def test_every_row_button_is_disabled(self):
        dialog = _dialog(hasSelection=False, selectedRow=-1)
        dialog.updateButtonStates()
        for attribute in ALL_BUTTONS:
            assert _enabled(dialog, attribute) is False, attribute

    def test_the_tooltip_says_to_pick_a_row(self):
        dialog = _dialog(hasSelection=False, selectedRow=-1)
        dialog.updateButtonStates()
        for attribute in ROW_ONLY + NEEDS_CLOSED:
            assert _tooltip(dialog, attribute) == "Select a project first."


class TestOnAnotherProject:
    def test_everything_is_available(self):
        dialog = _dialog(selectedRow=1, name="Other", project="C:/projects/Other")
        dialog.updateButtonStates()
        for attribute in ROW_ONLY + NEEDS_CLOSED:
            assert _enabled(dialog, attribute) is True, attribute

    def test_no_tooltip_gets_in_the_way(self):
        dialog = _dialog(selectedRow=1, name="Other", project="C:/projects/Other")
        dialog.updateButtonStates()
        for attribute in ROW_ONLY + NEEDS_CLOSED:
            assert _tooltip(dialog, attribute) == ""


class TestOnTheOpenProject:
    """Move, rename, remove, unload and open all used to pop a message after the click."""

    def test_the_operations_that_need_it_closed_are_disabled(self):
        dialog = _dialog(selectedRow=0)
        dialog.updateButtonStates()
        for attribute in NEEDS_CLOSED:
            assert _enabled(dialog, attribute) is False, attribute
            assert _tooltip(dialog, attribute) == "This is the project currently open in QGIS."

    def test_the_harmless_ones_stay_available(self):
        # Exporting, cloning or opening the folder of the current project is perfectly fine
        dialog = _dialog(selectedRow=0)
        dialog.updateButtonStates()
        for attribute in ROW_ONLY:
            assert _enabled(dialog, attribute) is True, attribute


class TestReordering:
    @pytest.mark.parametrize("row,rowCount,up,down", [
        (0, 3, False, True),    # first row cannot go up
        (1, 3, True, True),
        (2, 3, True, False),    # last row cannot go down
        (0, 1, False, False),   # the only row goes nowhere
    ])
    def test_bounds(self, row, rowCount, up, down):
        dialog = _dialog(selectedRow=row, rowCount=rowCount, name="Other", project="C:/other")
        dialog.updateButtonStates()
        assert _enabled(dialog, "btUp") is up
        assert _enabled(dialog, "btDown") is down


class TestGuardsAreKept:
    """The handlers keep their own checks: double-clicking a row calls openProject directly, so the
    disabled button is not the only thing standing between the user and the operation."""

    @pytest.mark.parametrize("method,message", [
        ("openProject", "Selected project is currently opened."),
        ("changeName", "Current project can not be renamed."),
        ("moveProject", "Current project can not be moved."),
    ])
    def test_the_handler_still_refuses(self, method, message):
        import inspect
        source = inspect.getsource(getattr(QGISRedProjectManagerDialog, method))
        assert message in source
