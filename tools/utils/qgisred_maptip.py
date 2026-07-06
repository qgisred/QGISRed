# -*- coding: utf-8 -*-
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeatureRequest,
                       QgsRectangle, QgsExpression,
                       QgsExpressionContext, QgsExpressionContextUtils)
from qgis.PyQt.QtGui import QCursor
from qgis.PyQt.QtWidgets import QApplication, QLabel
from qgis.PyQt.QtCore import Qt, QEvent, QObject, QTimer, QPoint

from ...compat import WKB_POINT_GEOMETRY


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
        self._hideTimer.timeout.connect(self._label.hide)

        iface.mapCanvas().xyCoordinates.connect(self._onMove)
        # Hide when mouse leaves the canvas area
        iface.mapCanvas().viewport().installEventFilter(self)
        # Hide when the user switches to another application (Alt+Tab, click elsewhere)
        QApplication.instance().applicationStateChanged.connect(self._onAppState)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def stop(self):
        """Disconnect signals and destroy the floating widget."""
        try:
            self._showTimer.stop()
            self._hideTimer.stop()
            self._iface.mapCanvas().xyCoordinates.disconnect(self._onMove)
            self._iface.mapCanvas().viewport().removeEventFilter(self)
            QApplication.instance().applicationStateChanged.disconnect(self._onAppState)
            self._label.hide()
            self._label.deleteLater()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Leave:
            self._showTimer.stop()
            self._hideTimer.stop()
            self._label.hide()
        return False   # never consume the event

    def _onAppState(self, state):
        if state != Qt.ApplicationState.ApplicationActive:
            self._showTimer.stop()
            self._hideTimer.stop()
            self._label.hide()

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
        else:
            self._label.hide()

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
