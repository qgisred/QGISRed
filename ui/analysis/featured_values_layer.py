# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QSizeF
from qgis.PyQt.QtGui import QColor, QFont
from qgis.core import (
    QgsCategorizedSymbolRenderer, QgsFeature, QgsField, QgsGeometry, QgsMarkerSymbol, QgsPalLayerSettings,
    QgsProject, QgsProperty, QgsPropertyCollection, QgsRendererCategory, QgsRuleBasedLabeling,
    QgsTextBackgroundSettings, QgsTextBufferSettings, QgsTextFormat, QgsVectorLayer,
)

from ...compat import (
    FIELD_TYPE_DOUBLE, FIELD_TYPE_INT, FIELD_TYPE_STRING, PAL_PLACEMENT_OVER_POINT, PAL_PROPERTY_COLOR,
    PAL_PROPERTY_OFFSET_XY, PAL_PROPERTY_PRIORITY, PAL_PROPERTY_SHAPE_FILL_COLOR,
    PAL_PROPERTY_SHAPE_STROKE_COLOR, PAL_PROPERTY_SHOW, PAL_QUADRANT_LEFT, PAL_QUADRANT_RIGHT, PEN_JOIN_ROUND,
    RENDER_UNIT_MILLIMETERS, RENDER_UNIT_POINTS, TEXT_BG_SHAPE_RECTANGLE, TEXT_BG_SIZE_BUFFER,
)
from .featured_values_config import STYLE_FRAME, STYLE_HALO, STYLE_OPAQUE

IDENTIFIER = "qgisred_featuredvalues"

_FIELDS = (
    ("Id", FIELD_TYPE_STRING), ("Type", FIELD_TYPE_STRING), ("Magnitude", FIELD_TYPE_STRING),
    ("Signal", FIELD_TYPE_STRING), ("SimValue", FIELD_TYPE_DOUBLE), ("MeasValue", FIELD_TYPE_DOUBLE),
    ("SimText", FIELD_TYPE_STRING), ("MeasText", FIELD_TYPE_STRING), ("Level", FIELD_TYPE_INT),
    ("Row", FIELD_TYPE_INT), ("Color", FIELD_TYPE_STRING), ("Contrast", FIELD_TYPE_STRING),
)
_BACKGROUND_BUFFER = 0.8
_HALO_SIZE = 0.8
_FRAME_WIDTH = 0.4
_MARKER_SIZE = 1.8
_LABEL_GAP = 2.0


def contrast_color(hex_color):
    color = QColor(hex_color)
    luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255.0
    return "#000000" if luminance > 0.6 else "#ffffff"


def find_layer():
    for layer in QgsProject.instance().mapLayers().values():
        if layer.customProperty("qgisred_identifier") == IDENTIFIER:
            return layer
    return None


def create_layer(crs, name):
    layer = QgsVectorLayer("Point?crs=" + crs.authid(), name, "memory")
    if not crs.authid():
        layer.setCrs(crs)
    layer.dataProvider().addAttributes([QgsField(field_name, field_type) for field_name, field_type in _FIELDS])
    layer.updateFields()
    layer.setCustomProperty("qgisred_identifier", IDENTIFIER)
    layer.setCustomProperty("skipMemoryLayersCheck", 1)
    return layer


def set_records(layer, records):
    provider = layer.dataProvider()
    provider.truncate()
    fields = layer.fields()
    features = []
    for record in records:
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromPointXY(record["point"]))
        for field_name, _ in _FIELDS:
            feature.setAttribute(field_name, record.get(field_name))
        features.append(feature)
    provider.addFeatures(features)
    layer.updateExtents()
    layer.triggerRepaint()


def _text_format(style, font_size):
    text_format = QgsTextFormat()
    font = QFont("Arial")
    font.setBold(True)
    text_format.setFont(font)
    text_format.setSize(font_size)
    text_format.setSizeUnit(RENDER_UNIT_POINTS)
    if style == STYLE_HALO:
        halo = QgsTextBufferSettings()
        halo.setEnabled(True)
        halo.setSize(_HALO_SIZE)
        halo.setSizeUnit(RENDER_UNIT_MILLIMETERS)
        halo.setColor(QColor("#ffffff"))
        halo.setJoinStyle(PEN_JOIN_ROUND)
        text_format.setBuffer(halo)
    elif style in (STYLE_OPAQUE, STYLE_FRAME):
        background = QgsTextBackgroundSettings()
        background.setEnabled(True)
        background.setType(TEXT_BG_SHAPE_RECTANGLE)
        background.setSizeType(TEXT_BG_SIZE_BUFFER)
        background.setSize(QSizeF(_BACKGROUND_BUFFER, _BACKGROUND_BUFFER))
        background.setSizeUnit(RENDER_UNIT_MILLIMETERS)
        background.setFillColor(QColor("#ffffff"))
        background.setStrokeColor(QColor("#ffffff"))
        background.setStrokeWidth(_FRAME_WIDTH if style == STYLE_FRAME else 0.0)
        background.setStrokeWidthUnit(RENDER_UNIT_MILLIMETERS)
        text_format.setBackground(background)
    return text_format


def _row_height(font_size):
    return round(font_size * 0.3528 * 1.25 + 2 * _BACKGROUND_BUFFER + 0.6, 3)


def _label_settings(text_field, style, quadrant, direction, display, network_size):
    settings = QgsPalLayerSettings()
    settings.fieldName = text_field
    settings.isExpression = False
    settings.enabled = True
    settings.placement = PAL_PLACEMENT_OVER_POINT
    settings.quadOffset = quadrant
    settings.offsetUnits = RENDER_UNIT_MILLIMETERS
    settings.setFormat(_text_format(style, display["fontSize"]))

    properties = QgsPropertyCollection()
    properties.setProperty(PAL_PROPERTY_OFFSET_XY, QgsProperty.fromExpression(
        "'{},' || to_string(\"Row\" * {})".format(direction * _LABEL_GAP, _row_height(display["fontSize"]))))
    properties.setProperty(PAL_PROPERTY_PRIORITY, QgsProperty.fromExpression('max(0, 11 - 2 * "Level")'))
    if display.get("zoomDependent") and network_size > 0:
        zoom_ratio = ("max(1, {!r} / max(bounds_width(@map_extent), bounds_height(@map_extent), 1e-9))"
                      .format(network_size))
        properties.setProperty(PAL_PROPERTY_SHOW, QgsProperty.fromExpression(
            '"Level" <= 1 + log(2, {}) + 1e-9'.format(zoom_ratio)))
    if style == STYLE_OPAQUE:
        properties.setProperty(PAL_PROPERTY_COLOR, QgsProperty.fromField("Contrast"))
        properties.setProperty(PAL_PROPERTY_SHAPE_FILL_COLOR, QgsProperty.fromField("Color"))
        properties.setProperty(PAL_PROPERTY_SHAPE_STROKE_COLOR, QgsProperty.fromField("Color"))
    else:
        properties.setProperty(PAL_PROPERTY_COLOR, QgsProperty.fromField("Color"))
        if style == STYLE_FRAME:
            properties.setProperty(PAL_PROPERTY_SHAPE_STROKE_COLOR, QgsProperty.fromField("Color"))
    settings.setDataDefinedProperties(properties)
    return settings


def apply_labeling(layer, display, network_size, simulated_title, measured_title):
    root = QgsRuleBasedLabeling.Rule(None)
    simulated = _label_settings("SimText", display["simulatedStyle"], PAL_QUADRANT_LEFT, -1, display, network_size)
    measured = _label_settings("MeasText", display["measuredStyle"], PAL_QUADRANT_RIGHT, 1, display, network_size)
    root.appendChild(QgsRuleBasedLabeling.Rule(simulated, 0, 0, "\"SimText\" <> ''", simulated_title))
    root.appendChild(QgsRuleBasedLabeling.Rule(measured, 0, 0, "\"MeasText\" <> ''", measured_title))
    layer.setLabeling(QgsRuleBasedLabeling(root))
    layer.setLabelsEnabled(True)


def apply_renderer(layer, magnitudes):
    categories = []
    for name, color in magnitudes:
        symbol = QgsMarkerSymbol.createSimple({
            "name": "circle", "color": color, "outline_color": "#ffffff",
            "outline_width": "0.3", "size": str(_MARKER_SIZE),
        })
        categories.append(QgsRendererCategory(name, symbol, name))
    layer.setRenderer(QgsCategorizedSymbolRenderer("Magnitude", categories))
