# -*- coding: utf-8 -*-
"""The palettes offered by the Legend Editor follow the style library while the dialog is open.

Opening the colour dropdown rereads the style database, so a ramp added or edited in the
Style Manager meanwhile is offered without closing the dialog; the ramp in use stays
selected and the legend is not marked as edited by the refresh alone.
"""
import os
from unittest.mock import patch

import pytest

from .conftest import REAL_QGIS

from QGISRed.tools.utils.qgisred_styling_utils import RAMP_KIND_TWO_COLORS
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedColorRampSelector
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="needs a real style database and Qt widgets")

STYLE_DATABASE_PATH = "QGISRed.tools.utils.qgisred_styling_utils.QGISRedStylingUtils.styleDatabasePath"


def _gradient(first, last):
    from qgis.core import QgsGradientColorRamp
    from qgis.PyQt.QtGui import QColor
    return QgsGradientColorRamp(QColor(first), QColor(last))


def _addRamp(databasePath, name, ramp):
    from qgis.core import QgsStyle
    style = QgsStyle()
    style.load(databasePath)
    assert style.addColorRamp(name, ramp, True)


@pytest.fixture
def databasePath(tmp_path):
    from qgis.core import QgsStyle
    path = str(tmp_path / "library.db")
    assert QgsStyle().createDatabase(path)
    _addRamp(path, "First", _gradient("#000000", "#ffffff"))
    with patch(STYLE_DATABASE_PATH, return_value=path):
        yield path


def _dialog():
    from qgis.PyQt.QtWidgets import QComboBox
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.hasUnappliedEdits = False
    dialog.btnColorRamp = QGISRedColorRampSelector()
    dialog.btnColorRamp.aboutToShowPopup.connect(dialog.refreshColorRamps)
    dialog.cbColors = QComboBox()
    dialog.cbColors.addItem(RAMP_KIND_TWO_COLORS, RAMP_KIND_TWO_COLORS)
    dialog.loadStyleDatabase()
    dialog.syncColorRampButton()
    return dialog


class TestRefreshColorRamps:
    def test_a_ramp_added_to_the_library_is_offered_without_reopening(self, databasePath):
        dialog = _dialog()
        assert list(dialog.btnColorRamp.colorRampCache) == ["First"]

        _addRamp(databasePath, "Second", _gradient("#ff0000", "#0000ff"))
        dialog.refreshColorRamps()

        assert sorted(dialog.btnColorRamp.colorRampCache) == ["First", "Second"]

    def test_an_edited_ramp_is_offered_with_its_new_colors(self, databasePath):
        dialog = _dialog()
        _addRamp(databasePath, "First", _gradient("#ff0000", "#0000ff"))

        dialog.refreshColorRamps()

        assert dialog.btnColorRamp.colorRampCache["First"].color1().name() == "#ff0000"

    def test_the_ramp_in_use_stays_selected(self, databasePath):
        _addRamp(databasePath, "Second", _gradient("#ff0000", "#0000ff"))
        dialog = _dialog()
        dialog.btnColorRamp.setActiveRampByName("Second")

        dialog.refreshColorRamps()

        assert dialog.btnColorRamp.activeRampName == "Second"
        assert dialog.btnColorRamp.currentText() == "Second"

    def test_the_refresh_alone_does_not_mark_the_legend_as_edited(self, databasePath):
        dialog = _dialog()
        dialog.refreshColorRamps()
        assert dialog.hasUnappliedEdits is False

    def test_opening_the_dropdown_is_what_refreshes(self, databasePath):
        dialog = _dialog()
        _addRamp(databasePath, "Second", _gradient("#ff0000", "#0000ff"))

        dialog.btnColorRamp.showPopup()
        dialog.btnColorRamp.hidePopup()

        assert sorted(dialog.btnColorRamp.colorRampCache) == ["First", "Second"]

    def test_a_library_that_could_not_be_read_keeps_the_fallback_ramps(self, tmp_path):
        with patch(STYLE_DATABASE_PATH, return_value=os.path.join(str(tmp_path), "missing.db")):
            dialog = _dialog()
            dialog.refreshColorRamps()
        fallback = QGISRedLegendsDialog.fallbackColorRamps()[RAMP_KIND_TWO_COLORS]
        assert set(dialog.btnColorRamp.colorRampCache) == set(fallback)


class TestPickingTheShownRampAgain:
    def test_it_applies_the_ramp_once_more(self, databasePath):
        selector = QGISRedColorRampSelector()
        selector.addColorRamps({"First": _gradient("#000000", "#ffffff")})
        applied = []
        selector.rampChanged.connect(lambda ramp: applied.append(ramp.color1().name()))

        selector.activated.emit(selector.currentIndex())

        assert applied == ["#000000"]
