# -*- coding: utf-8 -*-
"""Closing the Legend Editor, the locked class count and "Add all values".

Cancel, Esc and the window X ask the same question about the edits not applied yet.
A class count the user cannot set is grey. Adding all values removes "Other Values".
"""
from unittest.mock import MagicMock

import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

from .conftest import REAL_QGIS


def _dialog():
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    return dialog


def _closingDialog(monkeypatch, answer):
    messageBox = MagicMock()
    messageBox.question.return_value = getattr(messageBox.StandardButton, answer)
    monkeypatch.setattr(legendsModule, "QMessageBox", messageBox)

    dialog = _dialog()
    dialog.isClosing = False
    dialog.hasAppliedChanges = False
    dialog.hasUnappliedEdits = True
    dialog.closeResult = 0
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.name.return_value = "Pipes"
    dialog.close = MagicMock()
    dialog.done = MagicMock()
    return dialog, messageBox


CLOSING_WAYS = ["cancelAndClose", "reject"]


@pytest.mark.parametrize("closingWay", CLOSING_WAYS)
class TestClosingWithEditsNotApplied:
    def test_the_user_is_asked_and_no_keeps_the_dialog_open(self, monkeypatch, closingWay):
        dialog, messageBox = _closingDialog(monkeypatch, "No")

        getattr(dialog, closingWay)()

        messageBox.question.assert_called_once()
        assert "Discard them?" in messageBox.question.call_args.args[2]
        dialog.close.assert_not_called()
        assert not dialog.isClosing

    def test_yes_closes_the_dialog(self, monkeypatch, closingWay):
        dialog, messageBox = _closingDialog(monkeypatch, "Yes")

        getattr(dialog, closingWay)()

        messageBox.question.assert_called_once()
        dialog.close.assert_called_once_with()

    def test_nothing_is_asked_without_edits(self, monkeypatch, closingWay):
        dialog, messageBox = _closingDialog(monkeypatch, "No")
        dialog.hasUnappliedEdits = False

        getattr(dialog, closingWay)()

        messageBox.question.assert_not_called()
        dialog.close.assert_called_once_with()


class TestWindowCloseButton:
    def test_no_keeps_the_dialog_open(self, monkeypatch):
        dialog, messageBox = _closingDialog(monkeypatch, "No")
        event = MagicMock()

        dialog.closeEvent(event)

        messageBox.question.assert_called_once()
        event.ignore.assert_called_once_with()


@pytest.mark.skipif(not REAL_QGIS, reason="the class count is a real spin box")
class TestClassCountBox:
    def _dialog(self):
        from qgis.PyQt.QtWidgets import QSpinBox

        dialog = _dialog()
        dialog.leClassCount = QSpinBox()
        dialog.classCountRowVisible = True
        return dialog

    def test_a_locked_count_is_grey_and_read_only(self):
        dialog = self._dialog()

        dialog.setClassCountEditable(False)

        assert dialog.leClassCount.isReadOnly()
        assert "background-color: #F0F0F0" in dialog.leClassCount.styleSheet()
        assert "font-size: %s" % QGISRedLegendsDialog.CONTROL_FONT_SIZE in dialog.leClassCount.styleSheet()

    def test_an_editable_count_is_white_again(self):
        dialog = self._dialog()
        dialog.setClassCountEditable(False)

        dialog.setClassCountEditable(True)

        assert not dialog.leClassCount.isReadOnly()
        assert "background-color: white" in dialog.leClassCount.styleSheet()
        assert "#F0F0F0" not in dialog.leClassCount.styleSheet()
        assert "font-size: %s" % QGISRedLegendsDialog.CONTROL_FONT_SIZE in dialog.leClassCount.styleSheet()


@pytest.mark.skipif(not REAL_QGIS, reason="the classes are rows of a real table with real line edits")
class TestAddAllValuesRemovesOtherValues:
    def _dialog(self, labels):
        from qgis.PyQt.QtWidgets import QLineEdit, QTableWidget

        dialog = _dialog()
        dialog.tableView = QTableWidget(0, 5)
        for label in labels:
            self._addRow(dialog, label)
        dialog.availableUniqueValues = ["PVC", "Steel"]
        dialog.addCategoricalClass = lambda: self._addRow(dialog, dialog.availableUniqueValues.pop(), 0)
        for name in (
            "updateClassCount",
            "updateButtonStates",
            "handleColorLogicOnClassChange",
            "handleSizeLogicOnClassChange",
            "markLegendEdited",
        ):
            setattr(dialog, name, MagicMock())
        self.lineEditClass = QLineEdit
        return dialog

    def _addRow(self, dialog, label, row=None):
        from qgis.PyQt.QtWidgets import QLineEdit

        row = dialog.tableView.rowCount() if row is None else row
        dialog.tableView.insertRow(row)
        dialog.tableView.setCellWidget(row, 4, QLineEdit(label))

    def _labels(self, dialog):
        return [dialog.tableView.cellWidget(row, 4).text() for row in range(dialog.tableView.rowCount())]

    def test_the_other_values_class_is_removed(self):
        dialog = self._dialog(["Iron", "Other Values"])

        dialog.classifyAllUniqueValues()

        assert sorted(self._labels(dialog)) == ["Iron", "PVC", "Steel"]

    def test_the_classes_stay_when_there_is_no_other_values_class(self):
        dialog = self._dialog(["Iron"])

        dialog.classifyAllUniqueValues()

        assert sorted(self._labels(dialog)) == ["Iron", "PVC", "Steel"]
