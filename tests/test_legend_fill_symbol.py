# -*- coding: utf-8 -*-
"""Colour edits on a polygon layer (the Demand Builder sectors) in the Legend Editor."""
import pytest

from .conftest import REAL_QGIS

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS symbols")


def _rgba(color):
    return color.red(), color.green(), color.blue(), color.alpha()


def test_a_fill_takes_the_picked_colour_and_keeps_its_outline():
    from qgis.core import QgsFillSymbol
    from qgis.PyQt.QtGui import QColor

    symbol = QgsFillSymbol.createSimple({"color": "166,206,227,90", "outline_color": "128,128,128,255"})
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)

    dialog.applyColorToSymbol(symbol, QColor(200, 0, 0, 90))

    fill = symbol.symbolLayer(0)
    assert _rgba(fill.color()) == (200, 0, 0, 90)
    assert _rgba(fill.strokeColor()) == (128, 128, 128, 255)
