# -*- coding: utf-8 -*-
from contextlib import suppress
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeatureRequest,
                       QgsRectangle, QgsExpression,
                       QgsExpressionContext, QgsExpressionContextUtils)
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication, QLabel, QWidget
from qgis.PyQt.QtCore import Qt, QEvent, QObject, QTimer, QPoint

from ...compat import WKB_POINT_GEOMETRY

# The native map tip renders its HTML in a web view (a plain text browser on builds
# without WebKit). That descendant is what tells it apart from the canvas' other child
# widgets — the scroll bars and the viewport, which must never be hidden.
_NATIVE_VIEW_CLASSES = ("QgsWebView", "QWebView", "QWebEngineView", "QTextBrowser")


def isNativeMapTip(widget, canvas=None):
    """True when this widget is the one QGIS built to draw its own map tip.

    The canvas and its viewport are never it, no matter what they hold: the viewport is
    what draws the map, so hiding it would leave a blank canvas.
    """
    if canvas is not None and (widget is canvas or widget is canvas.viewport()):
        return False
    if widget.metaObject().className() in _NATIVE_VIEW_CLASSES:
        return True
    return any(child.metaObject().className() in _NATIVE_VIEW_CLASSES
               for child in widget.findChildren(QWidget))


def hideNativeMapTip(canvas):
    """Hide the tip QGIS draws for the active layer, so only ours is on screen.

    Ours covers the same layers and more, but QGIS places its own at a different origin
    and sizes it from its own text, so it sticks out behind ours as a stray edge above
    or to the side. There is no API to switch it off; the widget it builds is a child
    of the canvas and hiding it is enough, because QGIS builds a new one on the next
    hover. Only called while our tip is up, so a layer we do not cover keeps its own.
    """
    # Which of canvas and viewport owns the tip depends on the QGIS version — sweep both.
    for child in list(canvas.children()) + list(canvas.viewport().children()):
        if not isinstance(child, QWidget):
            continue
        if child.isVisible() and isNativeMapTip(child, canvas):
            child.hide()


class QGISRedMapTip(QObject):
    """Shows map-tip HTML for ALL visible layers with a mapTipTemplate, not just the
    active legend layer.  Respects the QGIS 'Show map tips' toolbar toggle.

    Usage:
        tip = QGISRedMapTip(iface)   # connects to canvas
        tip.stop()                   # disconnects and destroys the widget (on unload)
    """

    _SHOW_DELAY_MS = 150   # ms of stillness before showing
    _HIDE_DELAY_MS = 300   # ms of movement before hiding (fires once, not per-pixel)
    _TOLERANCE_PX  = 8     # pixel radius for feature search
    _TIP_OFFSET    = QPoint(19, 0)   # label top-left relative to cursor hotspot

    def __init__(self, iface):
        super().__init__(None)
        self._iface = iface
        self._hoverPoint = None

        self._showTimer = QTimer()
        self._showTimer.setSingleShot(True)
        self._showTimer.setInterval(self._SHOW_DELAY_MS)
        self._showTimer.timeout.connect(self._query)

        # None parent → true top-level; move() accepts global screen coordinates
        self._label = QLabel(None)
        self._label.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setWordWrap(True)
        self._label.setMaximumWidth(400)
        self._label.setStyleSheet(
            "QLabel { background-color: white; border: 1px solid black;"
            " padding: 5px; color: black; }"
        )
        self._label.hide()

        # Fires once 300 ms after the FIRST move — does NOT restart on every pixel
        self._hideTimer = QTimer()
        self._hideTimer.setSingleShot(True)
        self._hideTimer.setInterval(self._HIDE_DELAY_MS)
        self._hideTimer.timeout.connect(self._hideLabel)

        iface.mapCanvas().xyCoordinates.connect(self._onMove)
        # Hide when mouse leaves the canvas area
        iface.mapCanvas().viewport().installEventFilter(self)
        # QGIS builds its own tip as a canvas child and shows it a while after ours.
        # Watching the canvas for new children lets us catch that widget the moment it
        # asks to be shown, which is the only way to suppress it without a flash.
        iface.mapCanvas().installEventFilter(self)
        self._watchExistingChildren()
        # Hide when the user switches to another application (Alt+Tab, click elsewhere)
        QApplication.instance().applicationStateChanged.connect(self._onAppState)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def hide(self):
        """Hide the tip now and cancel any pending show (e.g. while a menu is up)."""
        with suppress(Exception):
            self._showTimer.stop()
            self._hideTimer.stop()
            self._hideLabel()

    def stop(self):
        """Disconnect signals and destroy the floating widget."""
        with suppress(Exception):
            self._showTimer.stop()
            self._hideTimer.stop()
            self._iface.mapCanvas().xyCoordinates.disconnect(self._onMove)
            self._iface.mapCanvas().viewport().removeEventFilter(self)
            self._iface.mapCanvas().removeEventFilter(self)
            QApplication.instance().applicationStateChanged.disconnect(self._onAppState)
            self._label.hide()
            self._label.deleteLater()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        etype = event.type()
        if etype == QEvent.Type.Leave:
            self._showTimer.stop()
            self._hideTimer.stop()
            self._hideLabel()
        elif etype == QEvent.Type.ChildAdded:
            # QGIS creates the tip widget empty and fills it in before showing it, so
            # there is nothing to recognise yet — just start watching it.
            self._watch(event.child())
        elif etype in (QEvent.Type.Show, QEvent.Type.ShowToParent):
            # By now the widget carries its view, so it can be told apart. Hiding it
            # here, while the show is still being delivered, means it never gets painted
            # — which a sweep on a timer cannot promise, hence the flash it left behind.
            if self._label.isVisible() and isNativeMapTip(obj, self._iface.mapCanvas()):
                obj.hide()
                return True
        return False   # never consume anything else

    def _hideLabel(self):
        self._label.hide()

    def _watch(self, child):
        """Follow a new canvas child so its show event reaches our filter."""
        with suppress(Exception):
            if child is not None and child.isWidgetType():
                child.installEventFilter(self)

    def _watchExistingChildren(self):
        """Catch a tip widget QGIS built before the plugin was loaded.

        ChildAdded only fires for children created from now on, and QGIS keeps its tip
        widget around between hovers on some versions.
        """
        with suppress(Exception):
            canvas = self._iface.mapCanvas()
            for child in list(canvas.children()) + list(canvas.viewport().children()):
                self._watch(child)

    def _onAppState(self, state):
        if state != Qt.ApplicationState.ApplicationActive:
            self._showTimer.stop()
            self._hideTimer.stop()
            self._hideLabel()

    def _onMove(self, point):
        self._hoverPoint = point
        self._showTimer.start()
        if self._label.isVisible() and not self._hideTimer.isActive():
            self._hideTimer.start()

    def _query(self):
        if not self._iface.actionMapTips().isChecked():
            return
        if self._hoverPoint is None:
            return

        canvas = self._iface.mapCanvas()
        tol = self._TOLERANCE_PX * canvas.mapUnitsPerPixel()
        rect = QgsRectangle(
            self._hoverPoint.x() - tol, self._hoverPoint.y() - tol,
            self._hoverPoint.x() + tol, self._hoverPoint.y() + tol,
        )

        point_parts, other_parts = [], []
        for layer in self._layersWithTips():
            rendered = self._render(layer, rect)
            if rendered is None:
                continue
            if layer.geometryType() == WKB_POINT_GEOMETRY:
                point_parts.append(rendered)
            else:
                other_parts.append(rendered)

        parts = point_parts if point_parts else other_parts
        self._hideTimer.stop()
        if parts:
            self._label.setText("<hr/>".join(parts))
            self._label.adjustSize()
            self._label.move(QCursor.pos() + self._TIP_OFFSET)
            self._label.show()
            self._label.raise_()
            # The event filter covers a native tip shown from now on; this covers one
            # already on screen, from a hover that started before ours had anything.
            with suppress(Exception):
                hideNativeMapTip(canvas)
        else:
            self._hideLabel()

    @staticmethod
    def _render(layer, rect):
        feats = list(layer.getFeatures(QgsFeatureRequest().setFilterRect(rect)))
        if not feats:
            return None
        ctx = QgsExpressionContext()
        ctx.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        ctx.setFeature(feats[0])
        rendered = QgsExpression.replaceExpressionText(layer.mapTipTemplate(), ctx).strip()
        return rendered or None

    @staticmethod
    def _layersWithTips():
        root = QgsProject.instance().layerTreeRoot()
        for node in root.findLayers():
            if not node.isVisible():
                continue
            layer = node.layer()
            if isinstance(layer, QgsVectorLayer) and layer.mapTipTemplate().strip():
                yield layer
