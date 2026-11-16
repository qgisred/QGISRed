# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog


class _ModeCombo:
    def __init__(self, data, text):
        self._data = data
        self._text = text

    def currentData(self):
        return self._data

    def currentText(self):
        return self._text


def _dialog(modeId, modeText):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.cbMode = _ModeCombo(modeId, modeText)
    dialog.showNotice = MagicMock()
    dialog.getRangeValues = MagicMock(return_value=None)
    return dialog


def test_automatic_mode_says_why_the_range_cannot_be_edited():
    dialog = _dialog("Jenks", "Natural Breaks (Jenks)")
    dialog.openRangeEditor(0)
    dialog.showNotice.assert_called_once_with(
        "The ranges are calculated by the Natural Breaks (Jenks) mode. Switch the mode to Manual to edit them."
    )
    dialog.getRangeValues.assert_not_called()


def test_manual_mode_opens_the_editor_without_a_notice():
    dialog = _dialog("Manual", "Manual")
    dialog.openRangeEditor(0)
    dialog.showNotice.assert_not_called()
    dialog.getRangeValues.assert_called_once_with(0)
