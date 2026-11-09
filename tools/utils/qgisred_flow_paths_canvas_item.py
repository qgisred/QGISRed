# -*- coding: utf-8 -*-
"""Canvas item that draws the upstream / downstream routes of a node.

Rubber bands only know a colour and a width, but the routes have to keep the
look of the results map: a flow arrow on pipes and the pump / valve icons. So
the links are drawn here with real QGIS line symbols, built from the same SVG
icons the results styles use, on a canvas item that sits on top of the map
like any other highlight and is removed just as easily.
"""
import os
from contextlib import suppress

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFields,
    QgsLineSymbol,
    QgsMarkerLineSymbolLayer,
    QgsMarkerSymbol,
    QgsProject,
    QgsRenderContext,
    QgsSimpleLineSymbolLayer,
    QgsSvgMarkerSymbolLayer,
)
from qgis.gui import QgsMapCanvasItem
from qgis.PyQt.QtGui import QColor, QPainter

_ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "defaults", "layerStyles", "icons",
)
_LINK_ICONS = {
    "pipe": "arrow.svg",
    "pump": "pumps.svg",
    "valve": "valves.svg",
}
# Same base size the results styles give to pump and valve icons (mm).
_VALVE_PUMP_ICON_SIZE = 7.0
# The rest of the network, drawn underneath the routes so they stand out.
_BACKGROUND_COLOR = QColor(170, 170, 170)
_BACKGROUND_WIDTH = 0.4
# White veil laid over the map before anything else, so the results colours
# of the layers underneath do not compete with the routes.
_VEIL_COLOR = QColor(255, 255, 255, 170)


def _central_marker_layer(svg_name, fill, size, stroke=None, stroke_width=0.0):
    marker = QgsSvgMarkerSymbolLayer(os.path.join(_ICONS_DIR, svg_name), size)
    marker.setFillColor(fill)
    marker.setStrokeColor(stroke if stroke is not None else QColor(255, 255, 255))
    marker.setStrokeWidth(stroke_width)
    line_layer = QgsMarkerLineSymbolLayer(True)
    line_layer.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
    line_layer.setSubSymbol(QgsMarkerSymbol([marker]))
    return line_layer


def build_link_symbol(kind, color, width):
    """Line symbol for one link of the routes: a line plus its type icon.

    An icon the colour of the line disappears into it, so arrows, pumps and
    valves get a darker fill and a white outline, and grow with the line.
    """
    line = QgsSimpleLineSymbolLayer(color, width)
    symbol = QgsLineSymbol([line])
    if kind in ("pump", "valve"):
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS[kind], color.darker(150), _VALVE_PUMP_ICON_SIZE - 1.0 + width * 2.0,
            stroke=QColor(255, 255, 255), stroke_width=0.25))
    else:
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS["pipe"], color.darker(170), 3.5 + width * 1.2,
            stroke=QColor(255, 255, 255), stroke_width=0.25))
    return symbol


def build_background_symbol(kind):
    """Grey symbol for a link that is not on any route."""
    symbol = QgsLineSymbol([QgsSimpleLineSymbolLayer(_BACKGROUND_COLOR, _BACKGROUND_WIDTH)])
    if kind in ("pump", "valve"):
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS[kind], _BACKGROUND_COLOR, _VALVE_PUMP_ICON_SIZE * 0.7))
    return symbol


def build_node_symbol():
    return QgsMarkerSymbol.createSimple({
        "name": "circle",
        "color": "255,255,0,255",
        "outline_color": "0,0,0,255",
        "outline_width": "0.8",
        "size": "5",
    })


class QGISRedFlowPathsCanvasItem(QgsMapCanvasItem):
    """Draws a list of (geometry, crs, symbol) entries over the whole canvas."""

    def __init__(self, canvas):
        QgsMapCanvasItem.__init__(self, canvas)
        self._canvas = canvas
        self._entries = []
        self._mapEntries = []
        self._mapCrs = None
        self.setZValue(100)
        canvas.extentsChanged.connect(self._sync)
        self._sync()

    def setEntries(self, entries):
        """entries: list of (QgsGeometry, QgsCoordinateReferenceSystem, QgsSymbol), drawn in order."""
        self._entries = list(entries or [])
        self._mapCrs = None
        self._sync()

    def dispose(self):
        with suppress(Exception):
            self._canvas.extentsChanged.disconnect(self._sync)
        self._entries = []
        self._mapEntries = []
        with suppress(Exception):
            self._canvas.scene().removeItem(self)

    def _sync(self):
        # The item covers the whole visible map, so its local coordinates are
        # the canvas pixel coordinates the render context maps to.
        with suppress(Exception):
            self.setRect(self._canvas.extent())
        self.update()

    def _entriesInMapCrs(self, destination):
        if self._mapCrs is not None and self._mapCrs == destination:
            return self._mapEntries
        project = QgsProject.instance()
        mapped = []
        for geometry, crs, symbol in self._entries:
            geom = type(geometry)(geometry)
            if crs is not None and crs.isValid() and destination.isValid() and crs != destination:
                with suppress(Exception):
                    geom.transform(QgsCoordinateTransform(crs, destination, project))
            mapped.append((geom, symbol))
        self._mapEntries = mapped
        self._mapCrs = destination
        return mapped

    def paint(self, painter, option=None, widget=None):
        if not self._entries:
            return
        painter.fillRect(self.boundingRect(), _VEIL_COLOR)
        settings = self._canvas.mapSettings()
        context = QgsRenderContext.fromMapSettings(settings)
        context.setPainter(painter)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fields = QgsFields()
        # Consecutive entries usually share their symbol (the whole grey
        # network does), so each symbol is started once per run, not per link.
        active = None
        try:
            for geom, symbol in self._entriesInMapCrs(settings.destinationCrs()):
                if symbol is not active:
                    if active is not None:
                        active.stopRender(context)
                    symbol.startRender(context, fields)
                    active = symbol
                feature = QgsFeature(fields)
                feature.setGeometry(geom)
                with suppress(Exception):
                    symbol.renderFeature(feature, context)
        finally:
            if active is not None:
                with suppress(Exception):
                    active.stopRender(context)
