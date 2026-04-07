# -*- coding: utf-8 -*-
"""
compat.py — Dual QGIS 3.x / 4.x compatibility shim for QGISRed.

QGIS 3.x uses Qt5/PyQt5; QGIS 4.x uses Qt6/PyQt6.
This module centralises every API difference that cannot be solved by a
mechanical `from PyQt5.* → from qgis.PyQt.*` rename so that the rest of
the plugin code stays clean.

Usage in other plugin files:
    from .compat import sip, QAction, QVariantString, QGIS_WARNING, ...
    from ..compat import sip, ...   (from sub-packages)
"""

# ---------------------------------------------------------------------------
# sip — PyQt5 bundles it as PyQt5.sip; PyQt6 as PyQt6.sip.
# qgis.PyQt re-exports it in both versions.
# ---------------------------------------------------------------------------
try:
    from qgis.PyQt import sip
except ImportError:
    import sip  # fallback bare import

# ---------------------------------------------------------------------------
# QAction — moved from QtWidgets (Qt5) to QtGui (Qt6).
# ---------------------------------------------------------------------------
try:
    from qgis.PyQt.QtGui import QAction       # Qt6 / PyQt6
except ImportError:
    from qgis.PyQt.QtWidgets import QAction   # Qt5 / PyQt5

# ---------------------------------------------------------------------------
# QVariant type constants.
# In PyQt5 / QGIS 3, QVariant exposes .String, .Double, .Int, .LongLong.
# In PyQt6 / QGIS 4, those attributes are removed; use QMetaType.Type instead.
# ---------------------------------------------------------------------------
try:
    from qgis.PyQt.QtCore import QVariant as _QVariant
    QVariantString   = _QVariant.String
    QVariantDouble   = _QVariant.Double
    QVariantInt      = _QVariant.Int
    QVariantLongLong = _QVariant.LongLong
except AttributeError:
    # PyQt6: QVariant still exists but enum members are gone
    from qgis.PyQt.QtCore import QMetaType
    QVariantString   = QMetaType.Type.QString
    QVariantDouble   = QMetaType.Type.Double
    QVariantInt      = QMetaType.Type.Int
    QVariantLongLong = QMetaType.Type.LongLong

# ---------------------------------------------------------------------------
# QgsMapLayer layer-type constants.
# QGIS 3: QgsMapLayer.RasterLayer / VectorLayer (flat enum)
# QGIS 4: QgsMapLayer.LayerType.RasterLayer / VectorLayer (scoped enum)
# ---------------------------------------------------------------------------
from qgis.core import QgsMapLayer as _QgsMapLayer

try:
    LAYER_TYPE_RASTER = _QgsMapLayer.RasterLayer
    LAYER_TYPE_VECTOR = _QgsMapLayer.VectorLayer
except AttributeError:
    LAYER_TYPE_RASTER = _QgsMapLayer.LayerType.RasterLayer
    LAYER_TYPE_VECTOR = _QgsMapLayer.LayerType.VectorLayer

# ---------------------------------------------------------------------------
# Qgis message-level constants.
# QGIS 3: Qgis.Info / Warning / Critical (flat)
# QGIS 4: Qgis.MessageLevel.Info / Warning / Critical (scoped)
# ---------------------------------------------------------------------------
from qgis.core import Qgis as _Qgis

try:
    QGIS_INFO     = _Qgis.MessageLevel.Info
    QGIS_WARNING  = _Qgis.MessageLevel.Warning
    QGIS_CRITICAL = _Qgis.MessageLevel.Critical
    QGIS_SUCCESS  = _Qgis.MessageLevel.Success
except AttributeError:
    QGIS_INFO     = _Qgis.Info
    QGIS_WARNING  = _Qgis.Warning
    QGIS_CRITICAL = _Qgis.Critical
    QGIS_SUCCESS  = _Qgis.Success

# ---------------------------------------------------------------------------
# QgsWkbTypes geometry-type constants.
# QgsWkbTypes is removed in QGIS 4; use Qgis.GeometryType instead.
# ---------------------------------------------------------------------------
try:
    from qgis.core import QgsWkbTypes as _QgsWkbTypes
    WKB_LINE_GEOMETRY  = _QgsWkbTypes.LineGeometry
    WKB_POINT_GEOMETRY = _QgsWkbTypes.PointGeometry
except (ImportError, AttributeError):
    WKB_LINE_GEOMETRY  = _Qgis.GeometryType.Line
    WKB_POINT_GEOMETRY = _Qgis.GeometryType.Point

# ---------------------------------------------------------------------------
# QStyle enum constants used by the custom combobox widget.
# QGIS 3 / Qt5: QStyle.CC_ComboBox / CE_ComboBoxLabel (flat)
# QGIS 4 / Qt6: QStyle.ComplexControl.CC_ComboBox /
#               QStyle.ControlElement.CE_ComboBoxLabel (scoped)
# ---------------------------------------------------------------------------
from qgis.PyQt.QtWidgets import QStyle as _QStyle

try:
    STYLE_CC_COMBOBOX      = _QStyle.CC_ComboBox
    STYLE_CE_COMBOBOXLABEL = _QStyle.CE_ComboBoxLabel
except AttributeError:
    STYLE_CC_COMBOBOX      = _QStyle.ComplexControl.CC_ComboBox
    STYLE_CE_COMBOBOXLABEL = _QStyle.ControlElement.CE_ComboBoxLabel

# ---------------------------------------------------------------------------
# QgsAttributeTableConfig column-type constants.
# QGIS 3: QgsAttributeTableConfig.Field / Actions (flat)
# QGIS 4: QgsAttributeTableConfig.Type.Field / Actions (scoped)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# QPainter render-hint constants.
# QGIS 3 / Qt5: QPainter.Antialiasing (flat)
# QGIS 4 / Qt6: QPainter.RenderHint.Antialiasing (scoped)
# ---------------------------------------------------------------------------
from qgis.PyQt.QtGui import QPainter as _QPainter

try:
    PAINTER_ANTIALIASING = _QPainter.Antialiasing
except AttributeError:
    PAINTER_ANTIALIASING = _QPainter.RenderHint.Antialiasing

# ---------------------------------------------------------------------------
# QgsSnappingConfig snapping-type constants.
# QGIS 3: QgsSnappingConfig.Vertex / Segment (flat)
# QGIS 4: QgsSnappingConfig.SnappingType.Vertex / Segment (scoped)
# ---------------------------------------------------------------------------
from qgis.core import QgsSnappingConfig as _QgsSnap

try:
    SNAP_TYPE_VERTEX  = _QgsSnap.Vertex
    SNAP_TYPE_SEGMENT = _QgsSnap.Segment
    SNAP_TYPE_BOTH    = _QgsSnap.VertexAndSegment
except AttributeError:
    SNAP_TYPE_VERTEX  = _QgsSnap.SnappingType.Vertex
    SNAP_TYPE_SEGMENT = _QgsSnap.SnappingType.Segment
    SNAP_TYPE_BOTH    = _QgsSnap.SnappingType.VertexAndSegment

from qgis.core import QgsAttributeTableConfig as _QgsATC
from qgis.PyQt.QtWidgets import QDialog as _QDialog

try:
    ATCOL_TYPE_FIELD   = _QgsATC.Field
    ATCOL_TYPE_ACTION  = _QgsATC.Action
except AttributeError:
    ATCOL_TYPE_FIELD   = _QgsATC.Type.Field
    ATCOL_TYPE_ACTION  = _QgsATC.Type.Action

try:
    DIALOG_ACCEPTED = _QDialog.Accepted
    DIALOG_REJECTED = _QDialog.Rejected
except AttributeError:
    DIALOG_ACCEPTED = _QDialog.DialogCode.Accepted
    DIALOG_REJECTED = _QDialog.DialogCode.Rejected
