# -*- coding: utf-8 -*-
"""The Style Library button of the Legend Editor.

It opens the QGIS Style Manager on the QGISRed library the user edits, and can put the
default library back. Either way the palettes offered by the dialog are reread afterwards.
"""
from unittest.mock import MagicMock

import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog


def _dialog(monkeypatch, answer="Yes"):
    messageBox = MagicMock()
    messageBox.question.return_value = getattr(messageBox.StandardButton, answer)
    monkeypatch.setattr(legendsModule, "QMessageBox", messageBox)
    styleManager = MagicMock()
    monkeypatch.setattr(legendsModule, "QgsStyleManagerDialog", styleManager)
    restore = MagicMock()
    monkeypatch.setattr(legendsModule.QGISRedStylingUtils, "restoreStyleDatabase", restore)

    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.style = "LIBRARY"
    dialog.refreshed = []
    dialog.refreshColorRamps = lambda: dialog.refreshed.append(dialog.style)
    return dialog, styleManager, restore, messageBox


class TestOpeningTheStyleManager:
    def test_it_opens_on_the_library_of_the_dialog(self, monkeypatch):
        dialog, styleManager, _restore, _box = _dialog(monkeypatch)

        dialog.openStyleManager()

        styleManager.assert_called_once_with("LIBRARY", dialog)
        styleManager.return_value.exec_.assert_called_once_with()

    def test_the_palettes_are_reread_once_it_closes(self, monkeypatch):
        dialog, _manager, _restore, _box = _dialog(monkeypatch)
        dialog.openStyleManager()
        assert dialog.refreshed == ["LIBRARY"]


class TestRestoringTheDefaultLibrary:
    def test_the_user_is_asked_first_and_no_changes_nothing(self, monkeypatch):
        dialog, _manager, restore, messageBox = _dialog(monkeypatch, answer="No")

        dialog.restoreDefaultStyleLibrary()

        messageBox.question.assert_called_once()
        restore.assert_not_called()
        assert dialog.refreshed == []

    def test_yes_restores_the_database_and_rereads_the_palettes(self, monkeypatch):
        dialog, _manager, restore, _box = _dialog(monkeypatch, answer="Yes")

        dialog.restoreDefaultStyleLibrary()

        restore.assert_called_once_with()
        assert dialog.refreshed == [None]

    def test_the_dialog_lets_go_of_the_database_before_it_is_replaced(self, monkeypatch):
        dialog, _manager, restore, _box = _dialog(monkeypatch, answer="Yes")
        restore.side_effect = lambda: dialog.refreshed.append(("restored while style is", dialog.style))

        dialog.restoreDefaultStyleLibrary()

        assert dialog.refreshed[0] == ("restored while style is", None)


class TestTheLibraryMenu:
    def _dialogWithButton(self, monkeypatch, trackedExists, rampKinds):
        monkeypatch.setattr(legendsModule, "QMenu", MagicMock())
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.tr = lambda text: text
        dialog.colorRampKinds = rampKinds
        dialog.btStyleLibrary = MagicMock()
        monkeypatch.setattr(legendsModule.os.path, "exists", lambda path: trackedExists)
        return dialog

    @pytest.mark.parametrize("trackedExists", [True, False])
    def test_restoring_is_only_offered_in_a_checkout_with_the_tracked_database(self, monkeypatch, trackedExists):
        dialog = self._dialogWithButton(monkeypatch, trackedExists, {"Blues": "2 colors Ramps"})
        dialog.setupStyleLibraryMenu()
        assert dialog.actionRestoreStyleLibrary.setEnabled.call_args[0][0] is trackedExists

    def test_the_button_is_greyed_when_the_library_could_not_be_read(self, monkeypatch):
        dialog = self._dialogWithButton(monkeypatch, True, {})
        dialog.setupStyleLibraryMenu()
        dialog.btStyleLibrary.setEnabled.assert_called_once_with(False)
