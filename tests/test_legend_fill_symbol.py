# -*- coding: utf-8 -*-
"""Colour and size edits on a polygon layer (the Demand Builder sectors) in the Legend Editor."""
import pytest

from .conftest import REAL_QGIS

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS symbols")


def _rgba(color):
    return color.red(), color.green(), color.blue(), color.alpha()


def _sectorsSymbol():
    from qgis.core import QgsFillSymbol

    return QgsFillSymbol.createSimple(
        {"color": "166,206,227,90", "outline_color": "128,128,128,255", "outline_width": "0.26"}
    )


def _polygonDialog():
    from unittest.mock import MagicMock
    from QGISRed.compat import WKB_LINE_GEOMETRY, WKB_POINT_GEOMETRY

    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.geometryType.return_value = max(WKB_LINE_GEOMETRY, WKB_POINT_GEOMETRY) + 1
    dialog.currentLayer.customProperty.return_value = "qgisred_demandbuilder_sectors"
    return dialog


def test_a_fill_takes_the_picked_colour_and_keeps_its_outline():
    from qgis.PyQt.QtGui import QColor

    symbol = _sectorsSymbol()
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)

    dialog.applyColorToSymbol(symbol, QColor(200, 0, 0, 90))

    fill = symbol.symbolLayer(0)
    assert _rgba(fill.color()) == (200, 0, 0, 90)
    assert _rgba(fill.strokeColor()) == (128, 128, 128, 255)


def test_the_size_cell_of_a_fill_shows_its_outline_width():
    assert _polygonDialog().currentSymbolSize(_sectorsSymbol(), "fill") == pytest.approx(0.26)


def test_the_size_of_a_fill_is_applied_to_its_outline():
    symbol = _sectorsSymbol()

    _polygonDialog().applySizeToSymbol(symbol, 0.8)

    assert symbol.symbolLayer(0).strokeWidth() == pytest.approx(0.8)
    assert _rgba(symbol.symbolLayer(0).color()) == (166, 206, 227, 90)


def test_the_opacity_cell_shows_the_alpha_of_the_fill_as_a_percent():
    from qgis.PyQt.QtGui import QColor
    from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedOpacityPercentSpinBox

    opacityWidget = QGISRedOpacityPercentSpinBox()

    opacityWidget.showOpacityOf(QColor(166, 206, 227, 90))

    assert opacityWidget.value() == 35


def test_the_opacity_percent_becomes_the_alpha_of_the_picked_colour():
    from qgis.PyQt.QtGui import QColor
    from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedOpacityPercentSpinBox

    opacityWidget = QGISRedOpacityPercentSpinBox()
    opacityWidget.setValue(50)
    symbol = _sectorsSymbol()

    _polygonDialog().applyColorToSymbol(symbol, opacityWidget.colorWithOpacity(QColor(200, 0, 0, 90)))

    assert _rgba(symbol.symbolLayer(0).color()) == (200, 0, 0, 128)
    assert _rgba(symbol.symbolLayer(0).strokeColor()) == (128, 128, 128, 255)


def _borderDialog(mode):
    from unittest.mock import MagicMock

    dialog = _polygonDialog()
    dialog.cbBorder = MagicMock()
    dialog.cbBorder.currentData.return_value = mode
    return dialog


@pytest.mark.parametrize("mode, expectedStroke", [
    ("black", (0, 0, 0, 255)),
    ("fill", (200, 0, 0, 255)),
    ("darker", (125, 0, 0, 255)),
])
def test_the_border_option_colours_the_outline_from_the_fill(mode, expectedStroke):
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtGui import QColor

    symbol = _sectorsSymbol()

    _borderDialog(mode).applyRowColorToSymbol(symbol, QColor(200, 0, 0, 90))

    fill = symbol.symbolLayer(0)
    assert _rgba(fill.color()) == (200, 0, 0, 90)
    assert _rgba(fill.strokeColor()) == expectedStroke
    assert fill.strokeStyle() == Qt.PenStyle.SolidLine


def test_no_border_hides_the_outline_and_keeps_its_width_for_later():
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtGui import QColor

    symbol = _sectorsSymbol()

    _borderDialog("none").applyRowColorToSymbol(symbol, QColor(200, 0, 0, 90))

    assert symbol.symbolLayer(0).strokeStyle() == Qt.PenStyle.NoPen
    assert symbol.symbolLayer(0).strokeWidth() == pytest.approx(0.26)


@pytest.mark.parametrize("outline, expectedMode", [
    ({"outline_style": "no"}, "none"),
    ({"outline_color": "0,0,0,255"}, "black"),
    ({"outline_color": "35,35,35,255"}, "black"),
    ({"outline_color": "166,206,227,255"}, "fill"),
    ({"outline_color": "104,129,142,255"}, "darker"),
])
def test_the_border_option_is_read_back_from_the_outline(outline, expectedMode):
    from qgis.core import QgsFillSymbol

    properties = {"color": "166,206,227,90", "outline_color": "0,0,0,255", "outline_width": "0.26"}
    properties.update(outline)

    assert _polygonDialog().detectBorderMode(QgsFillSymbol.createSimple(properties)) == expectedMode


def test_the_swatch_draws_the_fill_with_the_typed_outline_width():
    from qgis.PyQt.QtGui import QColor
    from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSymbolColorSelector

    swatch = QGISRedSymbolColorSelector(None, "fill", QColor(166, 206, 227, 90), actualSymbol=_sectorsSymbol())
    swatch.previewSizeValue = 0.8
    preview = _sectorsSymbol()

    swatch.applySizeScaling(preview)

    assert preview.symbolLayer(0).strokeWidth() == pytest.approx(0.8)
