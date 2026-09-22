# -*- coding: utf-8 -*-
"""The legend editor swatch draws the symbol at the size the map will draw it.

It used to ease the size cell value into a fixed range, through symbol.setWidth(). On a
pump or valve that call is skewed by the marker line, which reports its icon size as its
width: with "All" the line shrank and the icon all but vanished, while with "Line" (no
marker line left) the line came out almost four times thicker than on the map.
"""
import inspect

import pytest

from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSymbolColorSelector


class _FakeLine:
    def __init__(self, width):
        self._width = width

    def layerType(self):
        return "SimpleLine"

    def subSymbol(self):
        return None

    def width(self):
        return self._width

    def setWidth(self, width):
        self._width = width


class _FakeMarkerSymbol:
    def __init__(self, size):
        self._size = size

    def size(self):
        return self._size

    def setSize(self, size):
        self._size = size

    def symbolLayers(self):
        return []


class _FakeMarkerLine:
    """Like the real one, its width is its icon size: scaling it as a width would be wrong."""

    def __init__(self, iconSize):
        self.icon = _FakeMarkerSymbol(iconSize)

    def layerType(self):
        return "MarkerLine"

    def subSymbol(self):
        return self.icon

    def width(self):
        return self.icon.size()

    def setWidth(self, width):
        raise AssertionError("a marker line must be resized through its icon")


class _FakeLineSymbol:
    def __init__(self, *symbolLayers):
        self._symbolLayers = list(symbolLayers)

    def symbolLayers(self):
        return self._symbolLayers

    def setWidth(self, width):
        raise AssertionError("symbol.setWidth() is skewed by marker lines")


def _selector(sizeValue):
    selector = QGISRedSymbolColorSelector.__new__(QGISRedSymbolColorSelector)
    selector.previewSizeValue = sizeValue
    return selector


class TestTrueLineSize:
    def test_the_line_alone_is_drawn_at_the_cell_value(self):
        line = _FakeLine(0.8)

        _selector(0.8).applyTrueLineSize(_FakeLineSymbol(line))

        assert line.width() == pytest.approx(0.8)

    def test_all_draws_line_and_icon_at_their_real_sizes(self):
        line, markerLine = _FakeLine(0.8), _FakeMarkerLine(5)

        _selector(0.8).applyTrueLineSize(_FakeLineSymbol(line, markerLine))

        assert line.width() == pytest.approx(0.8)
        assert markerLine.icon.size() == pytest.approx(5)

    def test_the_icon_grows_with_the_line_as_the_size_is_typed(self):
        line, markerLine = _FakeLine(0.8), _FakeMarkerLine(5)

        _selector(1.6).applyTrueLineSize(_FakeLineSymbol(line, markerLine))

        assert line.width() == pytest.approx(1.6)
        assert markerLine.icon.size() == pytest.approx(10)

    def test_a_hairline_is_still_visible(self):
        line = _FakeLine(0.8)

        _selector(0.01).applyTrueLineSize(_FakeLineSymbol(line))

        assert line.width() == pytest.approx(QGISRedSymbolColorSelector.minimumPreviewLineWidth)

    def test_a_line_without_a_width_yet_takes_the_cell_value(self):
        line = _FakeLine(0)

        _selector(0.6).applyTrueLineSize(_FakeLineSymbol(line))

        assert line.width() == pytest.approx(0.6)


class TestFitToSwatch:
    def test_a_symbol_that_fits_is_left_at_its_true_size(self):
        line, markerLine = _FakeLine(0.8), _FakeMarkerLine(5)

        reduced = _selector(None).fitPreviewToSwatch(_FakeLineSymbol(line, markerLine), 7.0)

        assert reduced is False
        assert (line.width(), markerLine.icon.size()) == (0.8, 5)

    def test_a_symbol_too_big_is_reduced_as_a_whole(self):
        line, markerLine = _FakeLine(1.6), _FakeMarkerLine(10)

        reduced = _selector(None).fitPreviewToSwatch(_FakeLineSymbol(line, markerLine), 5.0)

        assert reduced is True
        assert markerLine.icon.size() == pytest.approx(5.0)
        assert line.width() == pytest.approx(0.8)  # same proportion to the icon as before

    def test_a_marker_too_big_is_reduced(self):
        tank = _FakeMarkerSymbol(7)

        reduced = _selector(None).fitPreviewToSwatch(tank, 4.2)

        assert reduced is True
        assert tank.size() == pytest.approx(4.2)


class TestMapAndScreenDpi:
    """The button draws at the physical dpi of the screen, the map canvas at its own:
    the preview is scaled by their ratio so both show the same pixels."""

    def test_a_line_symbol_is_scaled_whole(self):
        line, markerLine = _FakeLine(0.8), _FakeMarkerLine(5)

        _selector(None).scalePreviewSymbol(_FakeLineSymbol(line, markerLine), 96 / 120)

        assert line.width() == pytest.approx(0.64)
        assert markerLine.icon.size() == pytest.approx(4.0)

    def test_a_marker_symbol_is_scaled_through_its_size(self):
        tank = _FakeMarkerSymbol(7)

        _selector(None).scalePreviewSymbol(tank, 96 / 120)

        assert tank.size() == pytest.approx(5.6)


class TestNoSkewedWidthCall:
    @pytest.mark.parametrize("method", ["applySizeScaling", "applyTrueLineSize", "scaleLineSymbol",
                                        "fitPreviewToSwatch"])
    def test_the_preview_never_sets_the_width_of_the_whole_symbol(self, method):
        source = inspect.getsource(getattr(QGISRedSymbolColorSelector, method))
        code = "\n".join(line.split("#")[0] for line in source.splitlines())

        assert "symbol.setWidth(" not in code
