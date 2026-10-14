# -*- coding: utf-8 -*-
"""The Symbol library selector at the bottom of the Legend Editor.

A combo picks the library the ramps and palettes come from (the default one or the user's own);
with the own library selected a pencil opens the QGIS Style Manager on it. Whatever is edited
there, or whichever library is picked, the palettes and the class colours follow at once.
"""
from unittest.mock import MagicMock

import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.tools.utils.qgisred_styling_utils import STYLE_LIBRARY_DEFAULT, STYLE_LIBRARY_OWNER


class FakeCombo:
    def __init__(self):
        self.items = []
        self.index = -1
        self.currentIndexChanged = MagicMock()
        self.blocked = False

    def addItem(self, text, data):
        self.items.append((text, data))

    def findData(self, data):
        return next((i for i, item in enumerate(self.items) if item[1] == data), -1)

    def setCurrentIndex(self, index):
        self.index = index
        if not self.blocked:
            for call in self.currentIndexChanged.connect.call_args_list:
                call[0][0]()

    def currentData(self):
        return self.items[self.index][1] if self.index >= 0 else None

    def blockSignals(self, block):
        self.blocked = block


def _dialog(monkeypatch, selected=STYLE_LIBRARY_OWNER, rampKinds=None):
    styleManager = MagicMock()
    monkeypatch.setattr(legendsModule, "QgsStyleManagerDialog", styleManager)
    utils = legendsModule.QGISRedStylingUtils
    monkeypatch.setattr(utils, "selectedStyleLibrary", staticmethod(lambda: selected))
    saved = []
    monkeypatch.setattr(utils, "setSelectedStyleLibrary", staticmethod(saved.append))
    monkeypatch.setattr(utils, "ensureOwnerStyleDatabase", staticmethod(lambda: None))

    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.style = MagicMock(name="library")
    dialog.colorRampKinds = {"Blues": "2 colors Ramps"} if rampKinds is None else rampKinds
    dialog.cbStyleLibrary = FakeCombo()
    dialog.btEditStyleLibrary = MagicMock()
    dialog.btnColorRamp = MagicMock()
    dialog.btnColorRamp.activeRampName = "Blues"
    dialog.btnColorRamp.colorRampCache = {"Blues": object()}
    dialog.events = []
    dialog.refreshColorRamps = lambda: dialog.events.append("reread")
    dialog.applyColorLogic = lambda forceRefresh=False: dialog.events.append(("recolour", forceRefresh))
    dialog.markLegendEdited = lambda: dialog.events.append("edited")
    dialog.saved = saved
    dialog.styleManager = styleManager
    return dialog


class TestTheSelector:
    def test_it_offers_the_default_and_the_owner_library(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.setupStyleLibrarySelector()
        assert [data for _text, data in dialog.cbStyleLibrary.items] == [STYLE_LIBRARY_DEFAULT, STYLE_LIBRARY_OWNER]

    @pytest.mark.parametrize("selected", [STYLE_LIBRARY_DEFAULT, STYLE_LIBRARY_OWNER])
    def test_it_starts_on_the_stored_choice_without_announcing_it(self, monkeypatch, selected):
        dialog = _dialog(monkeypatch, selected=selected)
        dialog.setupStyleLibrarySelector()
        assert dialog.cbStyleLibrary.currentData() == selected
        assert dialog.events == []

    def test_the_pencil_shows_only_for_the_owner_library(self, monkeypatch):
        dialog = _dialog(monkeypatch, selected=STYLE_LIBRARY_DEFAULT)
        dialog.setupStyleLibrarySelector()
        dialog.btEditStyleLibrary.setVisible.assert_called_with(False)

        dialog.cbStyleLibrary.setCurrentIndex(dialog.cbStyleLibrary.findData(STYLE_LIBRARY_OWNER))

        dialog.btEditStyleLibrary.setVisible.assert_called_with(True)

    def test_the_pencil_keeps_its_place_while_hidden_so_the_row_does_not_shift(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.setupStyleLibrarySelector()
        policy = dialog.btEditStyleLibrary.sizePolicy.return_value
        policy.setRetainSizeWhenHidden.assert_called_once_with(True)
        dialog.btEditStyleLibrary.setSizePolicy.assert_called_once_with(policy)

    def test_the_pencil_is_greyed_when_the_library_could_not_be_read(self, monkeypatch):
        dialog = _dialog(monkeypatch, rampKinds={})
        dialog.setupStyleLibrarySelector()
        dialog.btEditStyleLibrary.setEnabled.assert_called_with(False)

    def test_switching_stores_the_choice_and_recolours_the_classes(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.setupStyleLibrarySelector()

        dialog.cbStyleLibrary.setCurrentIndex(dialog.cbStyleLibrary.findData(STYLE_LIBRARY_DEFAULT))

        assert dialog.saved == [STYLE_LIBRARY_DEFAULT]
        assert dialog.events == ["reread", ("recolour", True), "edited"]


class TestEditingTheOwnerLibrary:
    def test_the_pencil_opens_the_style_manager_on_the_library_of_the_dialog(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        library = dialog.style

        dialog.openStyleManager()

        dialog.styleManager.assert_called_once_with(library, dialog)
        dialog.styleManager.return_value.exec_.assert_called_once_with()

    def test_the_colours_follow_once_it_closes(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.openStyleManager()
        assert dialog.events == ["reread", ("recolour", True), "edited"]

    def test_each_save_in_the_manager_recolours_the_classes_at_once(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.connectStyleLibrarySignals(dialog.style)

        slot = dialog.style.rampChanged.connect.call_args[0][0]
        slot()

        assert dialog.events == ["reread", ("recolour", True), "edited"]

    def test_a_ramp_that_no_longer_exists_is_not_applied(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        dialog.btnColorRamp.colorRampCache = {}

        dialog.onStyleLibraryEdited()

        assert dialog.events == ["reread"]

    def test_the_manager_stops_announcing_once_closed(self, monkeypatch):
        dialog = _dialog(monkeypatch)
        library = dialog.style

        dialog.openStyleManager()

        library.rampChanged.disconnect.assert_called_once_with(dialog.onStyleLibraryEdited)
