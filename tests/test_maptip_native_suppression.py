# -*- coding: utf-8 -*-
"""Hiding the map tip QGIS draws on its own.

Our tip replaces the native one — it covers every visible layer, not just the active
one — but QGIS keeps drawing its own underneath, at its own origin and with its own
width, so an edge of it shows around ours. The sweep that hides it walks the canvas'
children, which is also where the viewport and the scroll bars live: hiding one of
those would blank the map, so the identification has to be exact.
"""
from unittest.mock import MagicMock, patch

from QGISRed.tools.utils.qgisred_maptip import hideNativeMapTip, isNativeMapTip

_MODULE = "QGISRed.tools.utils.qgisred_maptip."


class _FakeWidget:
    def __init__(self, className="QWidget", children=(), visible=True):
        self._className = className
        self._children = list(children)
        self._visible = visible
        self.hidden = False

    def metaObject(self):
        meta = MagicMock()
        meta.className.return_value = self._className
        return meta

    def children(self):
        return list(self._children)

    def findChildren(self, _type):
        found = []
        for child in self._children:
            found.append(child)
            found.extend(child.findChildren(_type))
        return found

    def isVisible(self):
        return self._visible

    def hide(self):
        self.hidden = True
        self._visible = False


def _nativeTip():
    """What QGIS builds: a bare widget wrapping the view that renders the tip HTML."""
    return _FakeWidget(children=[_FakeWidget("QgsWebView")])


def _sweep(canvasChildren, viewport):
    canvas = _FakeWidget(children=canvasChildren)
    canvas.viewport = lambda: viewport
    with patch(_MODULE + "QWidget", _FakeWidget):
        hideNativeMapTip(canvas)


class TestNativeTipIdentification:
    def test_widget_rendering_tip_html_is_recognised(self):
        assert isNativeMapTip(_nativeTip())

    def test_view_itself_is_recognised(self):
        # Some builds have no WebKit and fall back to a plain text browser.
        assert isNativeMapTip(_FakeWidget("QTextBrowser"))

    def test_canvas_furniture_is_not_mistaken_for_a_tip(self):
        assert not isNativeMapTip(_FakeWidget("QScrollBar"))
        assert not isNativeMapTip(_FakeWidget(children=[_FakeWidget("QLabel")]))

    def test_the_viewport_is_never_a_tip_whatever_it_holds(self):
        """It draws the map — hiding it would blank the canvas. The show events of the
        canvas and its viewport reach the same filter as the tip's, so the exclusion
        cannot rely on them merely not looking like one."""
        viewport = _FakeWidget("QWidget", children=[_FakeWidget("QgsWebView")])
        canvas = _FakeWidget("QgsMapCanvas")
        canvas.viewport = lambda: viewport
        assert not isNativeMapTip(viewport, canvas)
        assert not isNativeMapTip(canvas, canvas)
        # Without the canvas to compare against, the question cannot be answered
        assert isNativeMapTip(viewport)


class TestNativeTipSweep:
    def test_native_tip_is_hidden(self):
        native = _nativeTip()
        viewport = _FakeWidget("QWidget")
        _sweep([native, viewport], viewport)
        assert native.hidden

    def test_viewport_and_scrollbars_are_left_alone(self):
        """The viewport draws the map: hiding it would blank the canvas."""
        viewport = _FakeWidget("QWidget", children=[_FakeWidget("QTextBrowser")])
        scrollbar = _FakeWidget("QScrollBar")
        _sweep([viewport, scrollbar], viewport)
        assert not viewport.hidden and not scrollbar.hidden

    def test_tip_parented_to_the_viewport_is_also_swept(self):
        """Which of canvas or viewport owns the tip depends on the QGIS version."""
        native = _nativeTip()
        viewport = _FakeWidget("QWidget", children=[native])
        _sweep([viewport], viewport)
        assert native.hidden

    def test_an_already_hidden_tip_is_not_touched_again(self):
        native = _nativeTip()
        native._visible = False
        _sweep([native], _FakeWidget())
        assert not native.hidden
