# -*- coding: utf-8 -*-
import os
from contextlib import suppress

from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFields,
    QgsGeometry,
    QgsLineSymbol,
    QgsMarkerLineSymbolLayer,
    QgsMarkerSymbol,
    QgsProject,
    QgsRenderContext,
    QgsSimpleLineSymbolLayer,
    QgsSvgMarkerSymbolLayer,
)
from qgis.gui import QgsMapCanvasItem
from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFont, QFontMetricsF, QPainter, QPainterPath, QPen, QPolygonF

from .qgisred_field_utils import QGISRedFieldUtils
from .qgisred_flow_paths import place_callouts

_ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "defaults", "layerStyles", "icons",
)
_LINK_ICONS = {
    "pipe": "arrow.svg",
    "pump": "pumps.svg",
    "valve": "valves.svg",
}
_VALVE_PUMP_ICON_SIZE = 7.0
_BACKGROUND_COLOR = QColor(170, 170, 170)
_BACKGROUND_WIDTH = 0.4
_VEIL_COLOR = QColor(255, 255, 255, 170)
_CASING_WIDTH = 0.35
_ALTERNATIVE_ARROW_SIZE = 2.9
_LABEL_PADDING = 6.0
_COMPACT_PADDING = 3.5
_LABEL_POINTER = 7.0
_LABEL_RADIUS = 6.0


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
    line = QgsSimpleLineSymbolLayer(color, width)
    symbol = QgsLineSymbol([line])
    if kind in ("pump", "valve"):
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS[kind], color.darker(150), _VALVE_PUMP_ICON_SIZE - 1.0 + width * 2.0,
            stroke=QColor(255, 255, 255), stroke_width=0.25))
    else:
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS["pipe"], color, 1.5 + width * 2.2,
            stroke=QColor(255, 255, 255), stroke_width=0.25))
    return symbol


def build_route_symbol(kind, fill, casing, width, arrow_color=None):
    border = QgsSimpleLineSymbolLayer(casing, width + 2 * _CASING_WIDTH)
    line = QgsSimpleLineSymbolLayer(fill, width)
    for layer in (border, line):
        layer.setPenCapStyle(Qt.PenCapStyle.RoundCap)
        layer.setPenJoinStyle(Qt.PenJoinStyle.RoundJoin)
    symbol = QgsLineSymbol([border, line])
    if kind in ("pump", "valve"):
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS[kind], fill.darker(150), _VALVE_PUMP_ICON_SIZE - 1.0 + width,
            stroke=QColor(255, 255, 255), stroke_width=0.25))
    elif arrow_color is not None:
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS["pipe"], arrow_color, _ALTERNATIVE_ARROW_SIZE,
            stroke=arrow_color, stroke_width=0.2))
    else:
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS["pipe"], QColor(255, 255, 255), width * 1.4,
            stroke=casing, stroke_width=0.1))
    return symbol


def build_background_symbol(kind):
    symbol = QgsLineSymbol([QgsSimpleLineSymbolLayer(_BACKGROUND_COLOR, _BACKGROUND_WIDTH)])
    if kind in ("pump", "valve"):
        symbol.appendSymbolLayer(_central_marker_layer(
            _LINK_ICONS[kind], _BACKGROUND_COLOR, _VALVE_PUMP_ICON_SIZE * 0.7))
    return symbol


def build_node_symbol(shape="circle"):
    return QgsMarkerSymbol.createSimple({
        "name": shape,
        "color": "255,255,0,255",
        "outline_color": "0,0,0,255",
        "outline_width": "0.5",
        "size": "4" if shape == "diamond" else "3",
    })


class QGISRedFlowPathsCanvasItem(QgsMapCanvasItem):
    def __init__(self, canvas):
        QgsMapCanvasItem.__init__(self, canvas)
        self._canvas = canvas
        self._entries = []
        self._mapEntries = []
        self._mapCrs = None
        self._keptLabels = set()
        self._labelAreas = None
        self._routeLabels = []
        self._routeLabelRects = []
        self._routeObstacleEntries = []
        self._mapObstacles = None
        self._obstaclesCrs = None
        self.setZValue(100)
        canvas.extentsChanged.connect(self._sync)
        canvas.mapCanvasRefreshed.connect(self._onMapRefreshed)
        self._sync()

    def setEntries(self, entries, kept_labels=None):
        self._entries = list(entries or [])
        self._mapCrs = None
        self._keptLabels = {str(lid) for lid in (kept_labels or ())}
        self._labelAreas = None
        self._sync()

    def setRouteLabels(self, labels, obstacles=None):
        self._routeLabels = list(labels or [])
        self._routeLabelRects = []
        self._routeObstacleEntries = list(obstacles or [])
        self._obstaclesCrs = None
        self.update()

    def routeLabelAt(self, pixel):
        for rect, index in reversed(self._routeLabelRects):
            if rect.contains(QPointF(pixel.x(), pixel.y())):
                return index
        return None

    def dispose(self):
        with suppress(Exception):
            self._canvas.extentsChanged.disconnect(self._sync)
        with suppress(Exception):
            self._canvas.mapCanvasRefreshed.disconnect(self._onMapRefreshed)
        self._entries = []
        self._mapEntries = []
        with suppress(Exception):
            self._canvas.scene().removeItem(self)

    def _sync(self):
        with suppress(Exception):
            self.setRect(self._canvas.extent())
        self.update()

    def _onMapRefreshed(self):
        self._labelAreas = None
        self.update()

    def _keptLabelAreas(self):
        if self._labelAreas is not None:
            return self._labelAreas
        areas = []
        results = None
        with suppress(Exception):
            results = self._canvas.labelingResults()
        if results is not None and self._keptLabels:
            project = QgsProject.instance()
            id_fields = {}
            with suppress(Exception):
                for position in results.allLabels():
                    if getattr(position, "isUnplaced", False):
                        continue
                    layer = project.mapLayer(position.layerID)
                    if layer is None or not hasattr(layer, "geometryType") or int(layer.geometryType()) != 1:
                        continue
                    if layer.id() not in id_fields:
                        id_fields[layer.id()] = QGISRedFieldUtils().getIdFieldName(layer)
                    feature = layer.getFeature(position.featureId)
                    if not feature.isValid() or id_fields[layer.id()] not in feature.fields().names():
                        continue
                    if str(feature.attribute(id_fields[layer.id()])) in self._keptLabels:
                        areas.append(list(position.cornerPoints))
        self._labelAreas = areas
        return areas

    def _veilPath(self, settings):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        converter = settings.mapToPixel()
        for corners in self._keptLabelAreas():
            if len(corners) < 3:
                continue
            polygon = QPolygonF()
            for point in corners:
                pixel = converter.transform(point)
                polygon.append(QPointF(pixel.x(), pixel.y()))
            hole = QPainterPath()
            hole.addPolygon(polygon)
            hole.closeSubpath()
            path = path.subtracted(hole)
        return path

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
        settings = self._canvas.mapSettings()
        try:
            painter.fillPath(self._veilPath(settings), _VEIL_COLOR)
        except Exception:
            painter.fillRect(self.boundingRect(), _VEIL_COLOR)
        context = QgsRenderContext.fromMapSettings(settings)
        context.setPainter(painter)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        fields = QgsFields()
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
        with suppress(Exception):
            self._paintRouteLabels(painter, settings)

    def _routeObstacles(self, destination):
        if self._obstaclesCrs is not None and self._obstaclesCrs == destination:
            return self._mapObstacles
        project = QgsProject.instance()
        parts = []
        for geometry, crs in self._routeObstacleEntries:
            geom = QgsGeometry(geometry)
            if crs is not None and crs.isValid() and destination.isValid() and crs != destination:
                with suppress(Exception):
                    geom.transform(QgsCoordinateTransform(crs, destination, project))
            parts.append(geom)
        self._mapObstacles = QgsGeometry.collectGeometry(parts) if parts else None
        self._obstaclesCrs = destination
        return self._mapObstacles

    def _routeOverlap(self, settings):
        obstacles = self._routeObstacles(settings.destinationCrs())
        if obstacles is None or obstacles.isEmpty():
            return None
        converter = settings.mapToPixel()

        def overlap(rect):
            left, top, right, bottom = rect
            try:
                corners = [converter.toMapCoordinates(int(round(x)), int(round(y)))
                           for x, y in ((left, top), (right, top), (right, bottom), (left, bottom))]
                area = QgsGeometry.fromPolygonXY([corners + corners[:1]])
                if not obstacles.intersects(area):
                    return 0.0
                return max(obstacles.intersection(area).length(), 1e-9)
            except Exception:
                return 0.0

        return overlap

    @staticmethod
    def _unfolded(box, anchor, bounds, width, height):
        left = box.center().x() - width / 2.0
        top = box.center().y() - height / 2.0
        if anchor.y() >= box.bottom():
            top = box.bottom() - height
        elif anchor.y() <= box.top():
            top = box.top()
        elif anchor.x() >= box.right():
            left = box.right() - width
        elif anchor.x() <= box.left():
            left = box.left()
        left = min(max(left, bounds.left() + 2.0), max(bounds.right() - 2.0 - width, bounds.left() + 2.0))
        top = min(max(top, bounds.top() + 2.0), max(bounds.bottom() - 2.0 - height, bounds.top() + 2.0))
        return QRectF(left, top, width, height)

    @staticmethod
    def _calloutPointer(box, anchor):
        if anchor.y() > box.bottom() or anchor.y() < box.top():
            edge = box.bottom() - 1 if anchor.y() > box.bottom() else box.top() + 1
            x = min(max(anchor.x(), box.left() + _LABEL_RADIUS + 4), box.right() - _LABEL_RADIUS - 4)
            return QPolygonF([QPointF(x - 5, edge), QPointF(x + 5, edge), QPointF(anchor.x(), anchor.y())])
        edge = box.right() - 1 if anchor.x() > box.right() else box.left() + 1
        y = min(max(anchor.y(), box.top() + 5), box.bottom() - 5)
        return QPolygonF([QPointF(edge, y - 4), QPointF(edge, y + 4), QPointF(anchor.x(), anchor.y())])

    def _paintRouteLabels(self, painter, settings):
        self._routeLabelRects = []
        if not self._routeLabels:
            return
        project = QgsProject.instance()
        destination = settings.destinationCrs()
        converter = settings.mapToPixel()
        title_font = QFont(painter.font())
        title_font.setBold(True)
        title_font.setPointSizeF(max(title_font.pointSizeF(), 9.0) + 1.0)
        sub_font = QFont(painter.font())
        sub_font.setPointSizeF(max(sub_font.pointSizeF(), 9.0) - 0.5)
        compact_font = QFont(sub_font)
        compact_font.setBold(True)
        title_metrics, sub_metrics = QFontMetricsF(title_font), QFontMetricsF(sub_font)
        compact_metrics = QFontMetricsF(compact_font)

        layouts = []
        for label in self._routeLabels:
            geom = type(label["geometry"])(label["geometry"])
            crs = label.get("crs")
            if crs is not None and crs.isValid() and destination.isValid() and crs != destination:
                with suppress(Exception):
                    geom.transform(QgsCoordinateTransform(crs, destination, project))
            pixel = converter.transform(geom.asPoint())
            title = label.get("title") or ""
            width = compact_metrics.horizontalAdvance(title) + 2 * _COMPACT_PADDING
            height = compact_metrics.height() + 2 * _COMPACT_PADDING
            layouts.append((QPointF(pixel.x(), pixel.y()), width, height, title))

        priority = sorted((i for i in range(len(layouts)) if not self._routeLabels[i].get("dot")),
                          key=lambda i: self._routeLabels[i].get("rank", i))
        bounds = self.boundingRect()
        spots = place_callouts(
            [(layouts[i][0].x(), layouts[i][0].y(), layouts[i][1], layouts[i][2], False) for i in priority],
            (bounds.left() + 2.0, bounds.top() + 2.0, bounds.right() - 2.0, bounds.bottom() - 2.0),
            overlap=self._routeOverlap(settings), gap=_LABEL_POINTER)
        spots = dict(zip(priority, spots))

        for i, label in enumerate(self._routeLabels):
            anchor, width, height, title = layouts[i]
            selected = bool(label.get("selected"))
            tone_fill, tone_border = label.get("tone") or (QColor(255, 255, 255), QColor(150, 150, 150))
            spot = spots.get(i)
            if spot is None:
                if not selected:
                    continue
                spot = (anchor.x() - width / 2.0, anchor.y() - _LABEL_POINTER - height)
            box = QRectF(spot[0], spot[1], width, height)
            subtitle = (label.get("subtitle") or "") if selected else ""
            font, metrics, padding = compact_font, compact_metrics, _COMPACT_PADDING
            lines = []
            if selected:
                font, metrics, padding = title_font, title_metrics, _LABEL_PADDING
                lines = ([subtitle] if subtitle else []) + list(label.get("details") or [])
                box = self._unfolded(
                    box, anchor, bounds,
                    max([metrics.horizontalAdvance(title)] + [sub_metrics.horizontalAdvance(line) for line in lines])
                    + 2 * padding,
                    metrics.height() + sub_metrics.height() * len(lines) + 2 * padding)
            fill = QColor(label["color"]) if selected else QColor(tone_fill)
            border = QColor(label["color"]).darker(130) if selected else QColor(tone_border)
            text = QColor(255, 255, 255) if selected else QColor(60, 60, 60)
            path = QPainterPath()
            path.addRoundedRect(box, _LABEL_RADIUS, _LABEL_RADIUS)
            pointer = QPainterPath()
            pointer.addPolygon(self._calloutPointer(box, anchor))
            pointer.closeSubpath()
            path = path.united(pointer)
            painter.setPen(QPen(border, 1.0))
            painter.setBrush(fill)
            painter.drawPath(path)
            painter.setPen(text)
            painter.setFont(font)
            top = box.top() + padding
            painter.drawText(QRectF(box.left(), top, box.width(), metrics.height()),
                             int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter), title)
            painter.setFont(sub_font)
            for row, line in enumerate(lines):
                painter.drawText(
                    QRectF(box.left(), top + metrics.height() + row * sub_metrics.height(),
                           box.width(), sub_metrics.height()),
                    int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter), line)
            self._routeLabelRects.append((box, label.get("index")))
