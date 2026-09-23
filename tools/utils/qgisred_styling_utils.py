# -*- coding: utf-8 -*-
from contextlib import suppress
import base64
import filecmp
import hashlib
import math
import os
import json
import random
import shutil
import sqlite3
import zlib
from random import randrange

from qgis.PyQt.QtCore import QCoreApplication
from ...compat import PAINTER_ANTIALIASING, PAL_PROPERTY_COLOR, PAL_PLACEMENT_LINE
from ...compat import RENDER_UNIT_MILLIMETERS, RENDER_UNIT_PIXELS, RENDER_UNIT_POINTS
from ...compat import SL_PROP_SIZE, SL_PROP_STROKE_WIDTH, SL_PROP_WIDTH, STYLE_ENTITY_COLORRAMP
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsVectorLayer, QgsSymbol, Qgis,
    QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsVectorLayerCache, NULL,
    QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer, QgsRenderContext,
    QgsMapLayerLegend, QgsMessageLog, QgsStyle, QgsExpression, QgsProject,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsProperty,
    QgsVectorLayerSimpleLabeling, QgsLimitedRandomColorRamp
)
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.utils import iface as _iface

from .qgisred_base_demand_fields import resolveBaseDemandField
from .qgisred_field_utils import QGISRedFieldUtils
from .qgisred_legend_rule_utils import scaleNumericLiterals
from .qgisred_valve_types import getValveTypeName


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/).

    realpath matters here: dev checkouts import this module through a `QGISRed ->
    git_repo` symlink (see tests/conftest.py) so `import QGISRed...` matches a real
    install, and __file__ preserves that symlinked path rather than resolving it.
    """
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


_DEMAND_SECTOR_COLOR_CACHE = {}

STYLE_DATABASE_NAME = "qgisred_symbology_style.db"
CONNECTIVITY_STYLE_NAME = "ConnectLinks"

# Kinds of color ramps and palettes, spelled like the tags scripts/build_style_db.py gives
# them in the style database. A ramp is told apart by its number of colors; a palette by
# how its colors reach the classes: Spread distributes them over the classes keeping the
# first and the last, Sequential hands them out in the order they are declared, Labeled
# gives each class the color labeled with its value.
RAMP_KIND_TWO_COLORS = "2 colors Ramps"
RAMP_KIND_THREE_COLORS = "3 colors Ramps"
RAMP_KIND_MORE_COLORS = "More than 3 colors Ramps"
PALETTE_KIND_SPREAD = "Spread Palettes"
PALETTE_KIND_SEQUENTIAL = "Sequential Palettes"
PALETTE_KIND_LABELED = "Labeled Palettes"
RAMP_KINDS = (RAMP_KIND_TWO_COLORS, RAMP_KIND_THREE_COLORS, RAMP_KIND_MORE_COLORS)
PALETTE_KINDS = (PALETTE_KIND_SPREAD, PALETTE_KIND_SEQUENTIAL, PALETTE_KIND_LABELED)

# Root ids stamped on the two halves of a split tank/reservoir icon
# (see defaults/layerStyles/icons/*_frame.svg and *_water.svg) -- see _isFrameSvgLayer.
FRAME_SVG_MARKER = 'id="qgisred_frame"'
WATER_SVG_MARKER = 'id="qgisred_water"'
FRAME_DARKEN_FACTOR = 160


def create_combined_cursor(icon, iface=None, icon_size=24):
    """Create a cursor with a slender arrow and a custom icon at the bottom-right.

    icon: str resource path, QPixmap, or QCursor (returned as-is).
    iface: optional QGIS iface, used for devicePixelRatioF (falls back to 1.0).
    icon_size: size in logical pixels for the overlaid icon (default 24).
    """
    from qgis.PyQt.QtGui import QCursor, QPixmap, QPainter, QPainterPath, QPen, QColor
    from qgis.PyQt.QtCore import Qt

    if isinstance(icon, QCursor):
        return icon

    ratio = 1.0
    if iface is not None:
        with suppress(Exception):
            ratio = iface.mainWindow().devicePixelRatioF()

    canvas_size = max(32, 12 + icon_size)
    pixmap = QPixmap(int(canvas_size * ratio), int(canvas_size * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(PAINTER_ANTIALIASING, True)

    path = QPainterPath()
    path.moveTo(0, 0)
    path.lineTo(0, 15)
    path.lineTo(4, 11)
    path.lineTo(6, 16)
    path.lineTo(8, 15)
    path.lineTo(6, 10.5)
    path.lineTo(11, 11)
    path.closeSubpath()

    painter.setPen(QPen(QColor(Qt.GlobalColor.black), 0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
    painter.setBrush(Qt.GlobalColor.white)
    painter.drawPath(path)

    icon_pixmap = icon if isinstance(icon, QPixmap) else QPixmap(icon)
    if not icon_pixmap.isNull():
        scaled = icon_pixmap.scaled(
            int(icon_size * ratio), int(icon_size * ratio),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        scaled.setDevicePixelRatio(ratio)
        offset = 11 if icon_size > 20 else 13
        painter.drawPixmap(offset, offset, scaled)

    painter.end()
    return QCursor(pixmap, 0, 0)


# Sentinel label used to identify the hidden NULL/else rule across calls.
_NULL_RULE_LABEL = "__qgisred_null__"


class _NullHiddenLegend(QgsMapLayerLegend):
    """Vector legend wrapper that hides the NULL/else rule from the legend panel."""

    def __init__(self, layer):
        super().__init__()
        self._layer = layer
        # Delegate to a default legend; keep the reference so it is not GC'd.
        self._default = QgsMapLayerLegend.defaultVectorLegend(layer)
        # The legend panel listens to this object, not to the one being wrapped, and only
        # the wrapped one hears about renderer changes. Without the relay the panel keeps
        # showing the classes of the previous style until something installs a new legend
        # — which is why the map updated on Apply but the legend did not.
        with suppress(Exception):
            self._default.itemsChanged.connect(self.itemsChanged)

    def createLayerTreeModelLegendNodes(self, nodeLayer):
        from qgis.PyQt import sip
        nodes = self._default.createLayerTreeModelLegendNodes(nodeLayer)
        result = [n for n in nodes if _NULL_RULE_LABEL not in str(n.data(0))]  # 0 == Qt.DisplayRole
        for n in result:
            sip.transferto(n, None)
        return result


class QGISRedStylingUtils:
    defaultSvgPathText = "defaultSvgPath"

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def tr(self, message):
        return QCoreApplication.translate("QGISRedStylingUtils", message)

    def _getQGISRedFolder(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).getQGISRedFolder()

    def projectStyleFileNames(self, qmlFile, variant=""):
        """File names to probe in the project's layerStyles folder, best match first.

        A project style belongs to one network, so it is stored prefixed with the network
        name (``Net_Pipes.qml``) — that is what the legend editor writes. The bare name is
        still accepted afterwards, both for styles saved before the prefix existed and for
        folders shared by hand between networks.
        """
        qmlFile = self.variantStyleFileName(qmlFile, variant)
        if self.NetworkName:
            return [self.NetworkName + "_" + qmlFile, qmlFile]
        return [qmlFile]

    @staticmethod
    def variantStyleFileName(fileName, variant):
        # Trees share one identifier, so each one's project style carries its tree name.
        if not variant:
            return fileName
        stem, extension = os.path.splitext(fileName)
        return stem + "_" + variant + extension

    @staticmethod
    def findStyleFile(folder, fileNames):
        """Path of the first of `fileNames` present in `folder`, matched in lowercase.

        The same style is spelled differently depending on who asks: openLayer passes
        "pipes", the legend editor writes "Pipes.qml" and the shipped defaults are
        capitalised. Comparing in lowercase resolves all of them the same way instead of
        relying on the file system being case-insensitive.
        Returns None when none of them exists.
        """
        try:
            entries = {entry.lower(): entry for entry in os.listdir(folder)}
        except OSError:
            return None
        for fileName in fileNames:
            entry = entries.get(fileName.lower())
            if entry is not None:
                return os.path.join(folder, entry)
        return None

    def _loadStyleFile(self, layer, qmlPath, field):
        layer.loadNamedStyle(qmlPath)
        layer.setLabelsEnabled(False)
        self.applyStrategyFromLayer(layer, field)
        self.convertRendererSizesToMillimeters(layer)
        self.translateRendererLabels(layer)

    def setStyle(self, layer, name, field=None, variant=""):
        """Load the QML style called `name` on `layer`.

        field: column (or expression) the legend must classify, when the caller knows it.
        It overrides the field recorded inside the style's legend strategy — see
        applyLegendStrategy.
        variant: narrows the project style to one layer among several sharing `name`
        (a tree's name); global and default styles stay common to all of them.
        """
        if name == "":
            return
        name = name.replace("_", "") if name else ""

        # 1- project style (network-prefixed first, see projectStyleFileNames)
        projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
        qmlPath = self.findStyleFile(projectStylePath, self.projectStyleFileNames(name + ".qml", variant))
        if qmlPath:
            self._loadStyleFile(layer, qmlPath, field)
            return

        # 2- global style (shared by every network, so never prefixed)
        stylePath = os.path.join(self._getQGISRedFolder(), "layerStyles")
        qmlPath = self.findStyleFile(stylePath, [name + ".qml"])
        if qmlPath:
            self._loadStyleFile(layer, qmlPath, field)
            return

        # 3- default style
        defaultStylePath = os.path.join(_plugin_root(), "defaults", "layerStyles")
        defaultName = name + ".qml.bak"
        qmlPath = self.findStyleFile(defaultStylePath, [defaultName])
        self._loadStyleFile(layer, qmlPath or os.path.join(defaultStylePath, defaultName), field)

    def setSavedStyle(self, layer, name, field=None):
        """Load the project or global style for `name` if there is one. True when applied.

        Unlike setStyle it does not fall through to the styles shipped with the plugin: it
        answers whether the user saved one of their own. That is what lets the families
        whose look is computed rather than shipped — demand sectors and their random
        colours — keep generating it while still honouring a saved style.
        """
        if not name:
            return False
        name = name.replace("_", "")
        candidates = (
            (os.path.join(self.ProjectDirectory, "layerStyles"), self.projectStyleFileNames(name + ".qml")),
            (os.path.join(self._getQGISRedFolder(), "layerStyles"), [name + ".qml"]),
        )
        for folder, fileNames in candidates:
            qmlPath = self.findStyleFile(folder, fileNames)
            if qmlPath:
                self._loadStyleFile(layer, qmlPath, field)
                return True
        return False

    def resolveStylePath(self, qmlFile):
        projectFolder = os.path.join(self.ProjectDirectory, "layerStyles")
        projectPath = self.findStyleFile(projectFolder, self.projectStyleFileNames(qmlFile))
        if projectPath:
            return projectPath
        globalPath = self.findStyleFile(os.path.join(self._getQGISRedFolder(), "layerStyles"), [qmlFile])
        if globalPath:
            return globalPath
        return os.path.join(_plugin_root(), "defaults", "layerStyles", qmlFile + ".bak")

    def applyStrategyFromLayer(self, layer, field=None):
        rawStrategy = layer.customProperty("qgisred_legend_strategy")
        if not rawStrategy:
            return
        try:
            strategy = json.loads(rawStrategy)
            self.applyLegendStrategy(layer, strategy, field)
        except Exception as ex:
            QgsMessageLog.logMessage(
                self.tr("Failed to apply legend strategy for layer %1: %2")
                    .replace("%1", layer.name()).replace("%2", str(ex)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )

    @staticmethod
    def isFieldReference(text):
        """True when `text` names a column, False when it is an expression like abs(Flow).

        Graduated renderers classify expressions just as well as columns, so an
        expression must not be rejected as a missing field.
        """
        with suppress(Exception):
            return QgsExpression(text).isField()
        return "(" not in text

    def applyLegendStrategy(self, layer, strategy, field=None):
        """Apply a stored legend strategy to `layer`.

        field: what the caller wants classified. It takes precedence over the field
        recorded in the strategy, because the caller knows the current state and the
        strategy only knows the state at the time the style was saved. The results dock
        relies on this: in Average mode links display Flow_Unsig / Flow_Sig while the
        style was saved classifying Flow, a column that stays NULL in that mode -
        classifying it produces a renderer with no classes and an empty legend.
        """
        if not isinstance(strategy, dict):
            return
        schema = strategy.get("schema")
        if schema not in ("qgisred.legendStrategy.v1", "qgisred.legendStrategy.v2"):
            QgsMessageLog.logMessage(
                self.tr("Unsupported legend strategy schema: %1")
                    .replace("%1", str(schema)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )
            return

        field = field or strategy.get("field")
        if not field:
            return
        fieldIndex = layer.fields().indexFromName(field)
        if fieldIndex == -1 and self.isFieldReference(field):
            QgsMessageLog.logMessage(
                self.tr("Legend strategy field '%1' not found on layer '%2'")
                    .replace("%1", field).replace("%2", layer.name()),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )
            return

        parts = self.resolveStrategyParts(strategy)
        if not parts:
            return

        mode = strategy.get("mode")

        if "allClasses" in parts and mode == "categorized":
            self.applyAllClassesSnapshot(layer, field, strategy.get("allClasses") or {})

        if "intervals" in parts and mode == "graduated":
            self.applyGraduatedClassification(layer, field, self.resolveIntervalsBlock(strategy))

        if "colors" in parts:
            colorsBlock = self.resolveColorsBlock(strategy)
            if mode == "categorized":
                if "allClasses" in parts:
                    # Classes are pinned by the snapshot: recolor them in place
                    # instead of rebuilding the renderer from the data.
                    self.applyCategorizedColorsInPlace(layer, colorsBlock)
                elif fieldIndex != -1:
                    # The rebuild reads unique values through the field index, so it
                    # only applies to real columns (fieldIndex == -1 means an expression here).
                    self.applyCategorizedColors(layer, field, fieldIndex, colorsBlock)
            elif mode == "graduated":
                self.applyGraduatedColors(layer, colorsBlock)

        if "sizes" in parts:
            self.applySizesStrategy(layer, strategy.get("sizes") or {})

        layer.triggerRepaint()
        layer.setLabelsEnabled(False)

    def resolveStrategyParts(self, strategy):
        parts = strategy.get("parts")
        if isinstance(parts, list):
            return parts
        mode = strategy.get("mode")
        if mode == "graduated":
            return ["intervals", "colors"]
        if mode == "categorized":
            return ["colors"]
        return []

    def resolveIntervalsBlock(self, strategy):
        block = strategy.get("intervals")
        if isinstance(block, dict):
            return block
        legacy = strategy.get("graduated") or {}
        return {
            "classificationMode": legacy.get("classificationMode"),
            "classes": legacy.get("classes"),
        }

    def resolveColorsBlock(self, strategy):
        block = strategy.get("colors")
        if isinstance(block, dict):
            return block
        legacy = strategy.get("graduated") or strategy.get("categorized") or {}
        source = legacy.get("colorSource")
        if not source and legacy.get("rampName"):
            source = "ramp"
        return {
            "source": source,
            "rampName": legacy.get("rampName"),
            "invertRamp": legacy.get("invertRamp", False),
        }

    def applyGraduatedClassification(self, layer, field, intervalsBlock):
        classificationMode = intervalsBlock.get("classificationMode")
        classes = int(intervalsBlock.get("classes") or 5)

        modeEnum = self.graduatedModeEnum(classificationMode)
        if modeEnum is None:
            QgsMessageLog.logMessage(
                self.tr("Unsupported classification mode: %1")
                    .replace("%1", str(classificationMode)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )
            return

        templateSymbol = self.cloneRendererTemplateSymbol(layer)
        ramp = self.cloneRendererRamp(layer)

        renderer = QgsGraduatedSymbolRenderer.createRenderer(
            layer, field, classes, modeEnum, templateSymbol, ramp
        )
        if renderer is None:
            return
        layer.setRenderer(renderer)

    def cloneRendererTemplateSymbol(self, layer):
        renderer = layer.renderer()
        if renderer is not None:
            with suppress(Exception):
                context = QgsRenderContext()
                symbols = renderer.symbols(context)
                if symbols:
                    return symbols[0].clone()
        return QgsSymbol.defaultSymbol(layer.geometryType())

    def cloneRendererRamp(self, layer):
        renderer = layer.renderer()
        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            ramp = renderer.sourceColorRamp()
            if ramp:
                return ramp.clone()
        return QgsStyle.defaultStyle().colorRamp("Spectral")

    def applyAllClassesSnapshot(self, layer, field, allClassesBlock):
        # loadNamedStyle already restores the exact classes with full symbology; only rebuild as a fallback.
        renderer = layer.renderer()
        if isinstance(renderer, QgsCategorizedSymbolRenderer) and renderer.classAttribute() == field:
            return
        classes = allClassesBlock.get("classes")
        if not isinstance(classes, list):
            return
        templateSymbol = self.cloneRendererTemplateSymbol(layer)
        geometryType = layer.geometryType()
        categories = []
        for classInfo in classes:
            symbol = templateSymbol.clone()
            color = QColor(classInfo.get("color"))
            if color.isValid():
                self._setSymbolColor(symbol, color)
            size = classInfo.get("size")
            if size is not None:
                if geometryType == 1:
                    symbol.setWidth(float(size))
                elif geometryType == 0:
                    symbol.setSize(float(size))
            rawValue = classInfo.get("value")
            value = NULL if rawValue is None else rawValue
            label = classInfo.get("label") or str(rawValue)
            category = QgsRendererCategory(value, symbol, label)
            renderState = classInfo.get("render")
            if renderState is not None:
                category.setRenderState(bool(renderState))
            categories.append(category)
        if categories:
            layer.setRenderer(QgsCategorizedSymbolRenderer(field, categories))

    def applyCategorizedColors(self, layer, field, fieldIndex, colorsBlock):
        source = colorsBlock.get("source") or "random"
        rampName = colorsBlock.get("rampName")
        invertRamp = colorsBlock.get("invertRamp", False)

        uniqueValues = sorted(
            layer.dataProvider().uniqueValues(fieldIndex),
            key=lambda value: ("" if value == NULL else str(value)),
        )
        nonNullValues = [value for value in uniqueValues if value != NULL]
        nullValues = [value for value in uniqueValues if value == NULL]

        ramp = None
        if source == "ramp" and rampName:
            ramp = self.findColorRamp(rampName)
            if ramp is None:
                QgsMessageLog.logMessage(
                    self.tr("Color ramp '%1' not found; falling back to random colors")
                        .replace("%1", rampName),
                    "QGISRed",
                    Qgis.MessageLevel.Warning,
                )

        templateSymbol = self.cloneRendererTemplateSymbol(layer)
        categories = []
        valueCount = max(len(nonNullValues), 1)
        kind = self.findColorRampKind(rampName) if ramp is not None else None
        for index, value in enumerate(nonNullValues):
            symbol = templateSymbol.clone()
            color = self.resolveCategoryColor(value, index, valueCount, ramp, invertRamp, kind)
            self._setSymbolColor(symbol, color)
            categories.append(QgsRendererCategory(value, symbol, self._translateCategoryLabel(value, field)))

        if nullValues:
            symbol = templateSymbol.clone()
            self._setSymbolColor(symbol, QColor.fromRgb(192, 192, 192))
            categories.append(QgsRendererCategory(nullValues[0], symbol, "#NA"))

        layer.setRenderer(QgsCategorizedSymbolRenderer(field, categories))

    def applyCategorizedColorsInPlace(self, layer, colorsBlock):
        """Recolor the existing categories without rebuilding the renderer.

        Used when the classes are pinned by an allClasses snapshot: values,
        labels, order and render states must survive, only colors change. NULL
        categories keep the grey #NA convention and the '' catch-all keeps its
        saved color; ramp positions are computed over the real categories only.
        """
        renderer = layer.renderer()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            return

        source = colorsBlock.get("source") or "random"
        rampName = colorsBlock.get("rampName")
        invertRamp = colorsBlock.get("invertRamp", False)

        ramp = None
        if source == "ramp" and rampName:
            ramp = self.findColorRamp(rampName)
            if ramp is None:
                QgsMessageLog.logMessage(
                    self.tr("Color ramp '%1' not found; falling back to random colors")
                        .replace("%1", rampName),
                    "QGISRed",
                    Qgis.MessageLevel.Warning,
                )

        categories = renderer.categories()
        realIndexes = [
            index for index, category in enumerate(categories)
            if category.value() != NULL and category.value() != ""
        ]
        realCount = max(len(realIndexes), 1)
        kind = self.findColorRampKind(rampName) if ramp is not None else None
        for position, index in enumerate(realIndexes):
            category = categories[index]
            symbol = category.symbol().clone()
            color = self.resolveCategoryColor(category.value(), position, realCount, ramp, invertRamp, kind)
            self._setSymbolColor(symbol, color)
            renderer.updateCategorySymbol(index, symbol)
        for index, category in enumerate(categories):
            if category.value() == NULL:
                symbol = category.symbol().clone()
                self._setSymbolColor(symbol, QColor.fromRgb(192, 192, 192))
                renderer.updateCategorySymbol(index, symbol)

    def applyGraduatedColors(self, layer, colorsBlock):
        renderer = layer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return
        rampName = colorsBlock.get("rampName")
        invertRamp = colorsBlock.get("invertRamp", False)
        if not rampName:
            return
        ramp = self.findColorRamp(rampName)
        if ramp is None:
            QgsMessageLog.logMessage(
                self.tr("Color ramp '%1' not found; colors strategy skipped")
                    .replace("%1", str(rampName)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )
            return

        kind = self.findColorRampKind(rampName)
        if kind == PALETTE_KIND_LABELED:
            # Labeled palettes match a value to a discrete category; a graduated legend has
            # numeric ranges instead, which never match, so spread the palette by position.
            kind = PALETTE_KIND_SPREAD
        ranges = renderer.ranges()
        rangeCount = max(len(ranges), 1)
        for index in range(len(ranges)):
            color = self.rampClassColor(ramp, kind, ranges[index].label(), index, rangeCount, invertRamp)
            if color is None:
                continue
            symbol = ranges[index].symbol().clone()
            self._setSymbolColor(symbol, color)
            renderer.updateRangeSymbol(index, symbol)

    def applySizesStrategy(self, layer, sizesBlock):
        renderer = layer.renderer()
        sizeMode = sizesBlock.get("mode") or "Manual"
        if sizeMode == "Manual":
            return

        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            ranges = renderer.ranges()
            sizes = self.computeSizesForCount(len(ranges), sizesBlock)
            for index in range(len(ranges)):
                symbol = ranges[index].symbol().clone()
                self.applySizeToSymbol(layer, symbol, sizes[index])
                renderer.updateRangeSymbol(index, symbol)
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            categories = renderer.categories()
            sizes = self.computeSizesForCount(len(categories), sizesBlock)
            for index in range(len(categories)):
                symbol = categories[index].symbol().clone()
                self.applySizeToSymbol(layer, symbol, sizes[index])
                renderer.updateCategorySymbol(index, symbol)

    def computeSizesForCount(self, count, sizesBlock):
        if count <= 0:
            return []
        mode = sizesBlock.get("mode") or "Manual"
        if mode == "Equal":
            return [float(sizesBlock.get("value") or 0.0)] * count

        minSize = float(sizesBlock.get("min") or 0.0)
        maxSize = float(sizesBlock.get("max") or 0.0)
        invert = bool(sizesBlock.get("invert"))

        tValues = [i / max(1, count - 1) for i in range(count)]
        if invert:
            tValues.reverse()

        sizes = []
        for t in tValues:
            if mode == "Linear":
                sizes.append(minSize + t * (maxSize - minSize))
            elif mode == "Quadratic":
                sizes.append(minSize + (t * t) * (maxSize - minSize))
            elif mode == "Exponential":
                if count > 1:
                    factor = (math.exp(t) - 1) / (math.exp(1) - 1)
                    sizes.append(minSize + factor * (maxSize - minSize))
                else:
                    sizes.append(minSize)
            else:
                # "Proportional to Value" needs per-feature averages — fall back to Linear.
                sizes.append(minSize + t * (maxSize - minSize))
        return sizes

    def applySizeToSymbol(self, layer, symbol, size):
        if layer.geometryType() == 1:
            symbol.setWidth(size)
        else:
            symbol.setSize(size)

    # Screen pixels at the 96 dpi the old styles were drawn for, and typographic points.
    UNIT_TO_MILLIMETERS = {RENDER_UNIT_PIXELS: 25.4 / 96, RENDER_UNIT_POINTS: 25.4 / 72}

    # value getter, value setter, unit getter, unit setter, data-defined sizes in that unit
    SIZE_UNIT_ACCESSORS = (
        ("width", "setWidth", "widthUnit", "setWidthUnit", (SL_PROP_STROKE_WIDTH, SL_PROP_WIDTH)),
        ("size", "setSize", "sizeUnit", "setSizeUnit", (SL_PROP_SIZE,)),
        ("strokeWidth", "setStrokeWidth", "strokeWidthUnit", "setStrokeWidthUnit", (SL_PROP_STROKE_WIDTH,)),
        ("offset", "setOffset", "offsetUnit", "setOffsetUnit", ()),
    )

    @classmethod
    def convertSymbolSizesToMillimeters(cls, symbol):
        """Rewrite the pixel and point sizes of `symbol` in millimetres, keeping its look.

        Returns the factor of the first size converted, or None when nothing had to change.
        """
        appliedFactor = None
        for symbolLayer in symbol.symbolLayers():
            subSymbol = symbolLayer.subSymbol()
            for accessor in cls.SIZE_UNIT_ACCESSORS:
                # A marker line reports its marker's size as its width: the sub symbol owns it.
                if subSymbol is not None and accessor[0] == "width":
                    continue
                factor = cls._convertSizeToMillimeters(symbolLayer, accessor)
                appliedFactor = appliedFactor or factor
            if subSymbol is not None:
                factor = cls.convertSymbolSizesToMillimeters(subSymbol)
                appliedFactor = appliedFactor or factor
        return appliedFactor

    @classmethod
    def _convertSizeToMillimeters(cls, symbolLayer, accessor):
        getter, setter, unitGetter, unitSetter, propertyKeys = accessor
        if not hasattr(symbolLayer, unitGetter):
            return None
        factor = cls.UNIT_TO_MILLIMETERS.get(getattr(symbolLayer, unitGetter)())
        if factor is None:
            return None
        value = getattr(symbolLayer, getter)()
        # Marker offsets are points (x, y), every other size is a plain number.
        converted = round(value * factor, 3) if isinstance(value, (int, float)) else value * factor
        getattr(symbolLayer, setter)(converted)
        getattr(symbolLayer, unitSetter)(RENDER_UNIT_MILLIMETERS)
        for propertyKey in propertyKeys:
            cls._scaleDataDefinedSize(symbolLayer, propertyKey, factor)
        return factor

    @staticmethod
    def _scaleDataDefinedSize(symbolLayer, propertyKey, factor):
        sizeProperty = symbolLayer.dataDefinedProperties().property(propertyKey)
        if sizeProperty and sizeProperty.isActive() and sizeProperty.expressionString():
            scaledExpression = scaleNumericLiterals(sizeProperty.expressionString(), factor)
            symbolLayer.setDataDefinedProperty(propertyKey, QgsProperty.fromExpression(scaledExpression))

    def convertRendererSizesToMillimeters(self, layer):
        """Bring a style saved in pixels or points to millimetres. True when the layer changed."""
        renderer = layer.renderer()
        if renderer is None:
            return False
        # The live symbols are owned by the layer: convert a copy and hand it back whole.
        converted = renderer.clone()
        symbols = list(converted.symbols(QgsRenderContext()))
        sourceSymbol = converted.sourceSymbol() if hasattr(converted, "sourceSymbol") else None
        if sourceSymbol is not None:
            symbols.append(sourceSymbol)
        appliedFactor = None
        for symbol in symbols:
            factor = self.convertSymbolSizesToMillimeters(symbol)
            appliedFactor = appliedFactor or factor
        if appliedFactor is None:
            return False
        layer.setRenderer(converted)
        self._convertStrategySizesToMillimeters(layer, appliedFactor)
        return True

    def _convertStrategySizesToMillimeters(self, layer, factor):
        # A strategy saved before sizes were in millimetres carries no unit: scale it once.
        rawStrategy = layer.customProperty("qgisred_legend_strategy")
        if not rawStrategy:
            return
        strategy = json.loads(rawStrategy)
        sizesBlock = strategy.get("sizes")
        if not isinstance(sizesBlock, dict) or sizesBlock.get("unit"):
            return
        for key in ("value", "min", "max"):
            sizesBlock[key] = round(float(sizesBlock.get(key) or 0.0) * factor, 3)
        sizesBlock["unit"] = "MM"
        layer.setCustomProperty("qgisred_legend_strategy", json.dumps(strategy))

    @staticmethod
    def _svgLayerContent(symbolLayer):
        """SVG text of an SvgMarker layer, embedded ("base64:...") or read from its file; "" otherwise.

        Duck-typed on path() (only SvgMarker/RasterMarker layers have it) rather than
        isinstance(), since the class is a MagicMock stand-in under the mocked test environment.
        """
        getPath = getattr(symbolLayer, "path", None)
        if not callable(getPath):
            return ""
        try:
            path = getPath() or ""
            if path.startswith("base64:"):
                return base64.b64decode(path[len("base64:"):]).decode("utf-8", "ignore")
            with open(path, "r", encoding="utf-8") as svgFile:
                return svgFile.read()
        except Exception:
            return ""

    @classmethod
    def _isFrameSvgLayer(cls, symbolLayer):
        """True for the "frame" half of a split tank/reservoir results icon.

        Tank/reservoir results icons are two stacked SvgMarker layers (water + frame,
        see defaults/layerStyles/icons/*Results_*.svg) so the frame can render a darker
        shade of the same colour instead of flattening the whole icon to one flat blob.
        The frame SVG is identified by a stamped root id, read back either from an
        embedded base64 style ("base64:...") or from a plain file path.
        """
        return FRAME_SVG_MARKER in cls._svgLayerContent(symbolLayer)

    @classmethod
    def isWaterSvgLayer(cls, symbolLayer):
        """True for the "water" half of a split tank/reservoir icon, the one the Legend Editor colours."""
        return WATER_SVG_MARKER in cls._svgLayerContent(symbolLayer)

    @classmethod
    def _setSymbolColor(cls, symbol, color):
        """Colour every layer of `symbol` with `color`, except tank/reservoir frame
        layers, which get a darker shade so the icon keeps its silhouette instead of
        turning into a single flat-coloured blob (see _isFrameSvgLayer)."""
        for index in range(symbol.symbolLayerCount()):
            symbolLayer = symbol.symbolLayer(index)
            target = color.darker(FRAME_DARKEN_FACTOR) if cls._isFrameSvgLayer(symbolLayer) else color
            with suppress(Exception):
                symbolLayer.setColor(target)

    def resolveCategoryColor(self, value, index, valueCount, ramp, invertRamp, kind=None):
        if ramp is not None:
            color = self.rampClassColor(ramp, kind, value, index, valueCount, invertRamp)
            if color is not None:
                return color
        # crc32, not hash(): str hashes are salted per process, and the color
        # must stay the same for a given value across QGIS restarts.
        seed = zlib.crc32(str(value).encode("utf-8"))
        seededRandom = random.Random(seed)  # nosec B311 — cosmetic category color, not security-sensitive
        return QColor.fromRgb(
            seededRandom.randint(0, 255),
            seededRandom.randint(0, 255),
            seededRandom.randint(0, 255),
        )

    def rampClassColor(self, ramp, kind, value, index, classCount, invertRamp):
        """Color of one class out of a ramp or a palette, following its kind.

        None when a Labeled palette has no color for `value`. Inverting hands the same
        colors out in the opposite order, which a Labeled palette has no use for.
        """
        if kind == PALETTE_KIND_LABELED:
            namedColors = ramp.fetchColors()
            match = self.labeledPaletteIndex([label for _, label in namedColors], value)
            return None if match is None else QColor(namedColors[match][0])
        if invertRamp:
            index = classCount - 1 - index
        if kind == PALETTE_KIND_SEQUENTIAL:
            colors = ramp.colors()
            return None if not colors else QColor(colors[index % len(colors)])
        if kind == PALETTE_KIND_SPREAD:
            colors = ramp.colors()
            if not colors:
                return None
            return self.paletteColorAt(colors, self.spreadPalettePosition(len(colors), classCount, index))
        return ramp.color(0.0 if classCount <= 1 else index / float(classCount - 1))

    @staticmethod
    def spreadPalettePosition(colorCount, classCount, index):
        """Where a class falls along a Spread palette; first and last colors are always taken.

        With no more classes than colors it lands on a real color of the palette; with more
        classes than colors it falls between two of them, to be blended.
        """
        if classCount <= 1 or colorCount <= 1:
            return 0.0
        position = index * (colorCount - 1) / float(classCount - 1)
        if classCount <= colorCount:
            return float(math.floor(position + 0.5))
        return min(position, float(colorCount - 1))

    @staticmethod
    def paletteColorAt(colors, position):
        lower = int(math.floor(position))
        share = position - lower
        if share < 1e-9 or lower + 1 >= len(colors):
            return QColor(colors[lower])
        first, second = colors[lower], colors[lower + 1]
        return QColor(
            int(round(first.red() + (second.red() - first.red()) * share)),
            int(round(first.green() + (second.green() - first.green()) * share)),
            int(round(first.blue() + (second.blue() - first.blue()) * share)),
        )

    @staticmethod
    def labeledPaletteIndex(labels, value):
        """Index of the palette color labeled with `value`, or None.

        A label lists every spelling of its value separated by commas ("CI, FG, FF"); case
        does not matter, and a missing value goes by the label NULL.
        """
        wanted = "null" if value is None or value == NULL or str(value).strip() in ("", "#NA") else str(value)
        wanted = wanted.strip().lower()
        for index, label in enumerate(labels):
            if wanted in [alias.strip().lower() for alias in label.split(",")]:
                return index
        return None

    @staticmethod
    def colorRampKind(style, rampName):
        """Kind of a ramp or palette of `style`: counted for a ramp, read from its tags for a palette."""
        ramp = style.colorRamp(rampName)
        if ramp is None:
            return None
        if hasattr(ramp, "stops"):
            colorCount = len(ramp.stops()) + 2
            if colorCount == 2:
                return RAMP_KIND_TWO_COLORS
            return RAMP_KIND_THREE_COLORS if colorCount == 3 else RAMP_KIND_MORE_COLORS
        tags = style.tagsOfSymbol(STYLE_ENTITY_COLORRAMP, rampName)
        return next((kind for kind in PALETTE_KINDS if kind in tags), PALETTE_KIND_SPREAD)

    def _translateCategoryLabel(self, value, field=None):
        if isinstance(value, str):
            if value == "Uncategorized":
                return self.tr("Uncategorized")
            if value == "ClosedLinks":
                return self.tr("Closed Links")
            if field in ("Type", "ValveType"):
                return getValveTypeName(value)
            if field == "ArcType":
                if value == "Branch":
                    return self.tr("Branches")
                if value == "Chord":
                    return self.tr("Chords")
        return str(value)

    def translateRendererLabels(self, layer):
        renderer = layer.renderer()
        if renderer is None:
            return

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            # Only translate the special values; custom labels and per-class
            # visibility must survive (pinned allClasses snapshots rely on it).
            categories = []
            classAttribute = renderer.classAttribute()
            for category in renderer.categories():
                translated = self._translateCategoryLabel(category.value(), classAttribute)
                label = translated if translated != str(category.value()) else category.label()
                rebuilt = QgsRendererCategory(category.value(), category.symbol().clone(), label)
                rebuilt.setRenderState(category.renderState())
                categories.append(rebuilt)
            layer.setRenderer(self._rebuildCategorizedRenderer(renderer, categories))

        elif isinstance(renderer, QgsRuleBasedRenderer):
            self._translateRuleLabels(renderer.rootRule())

    @staticmethod
    def _rebuildCategorizedRenderer(renderer, categories):
        # The source symbol and ramp are the template for categories added later from data.
        rebuilt = QgsCategorizedSymbolRenderer(renderer.classAttribute(), categories)
        if renderer.sourceSymbol() is not None:
            rebuilt.setSourceSymbol(renderer.sourceSymbol().clone())
        if renderer.sourceColorRamp() is not None:
            rebuilt.setSourceColorRamp(renderer.sourceColorRamp().clone())
        return rebuilt

    def _translateRuleLabels(self, rule):
        if rule is None:
            return
        label = self._translateCategoryLabel(rule.label())
        if label != rule.label():
            rule.setLabel(label)
        for child in rule.children():
            self._translateRuleLabels(child)

    def graduatedModeEnum(self, classificationMode):
        mapping = {
            "EqualInterval": QgsGraduatedSymbolRenderer.EqualInterval,
            "Quantile": QgsGraduatedSymbolRenderer.Quantile,
            "Jenks": QgsGraduatedSymbolRenderer.Jenks,
            "StdDev": QgsGraduatedSymbolRenderer.StdDev,
            "Pretty": QgsGraduatedSymbolRenderer.Pretty,
        }
        return mapping.get(classificationMode)

    def _colorForDemandCategory(self, category):
        text = "" if category is None else str(category).strip()

        if text == "" or text.lower() in ("null", "undefined"):
            return QColor("orange")

        digest = hashlib.md5(text.lower().encode("utf-8"), usedforsecurity=False).hexdigest()
        color = QColor()
        color.setHsv(int(digest[:8], 16) % 360, 180, 220)
        return color

    def setDemandBuilderStyle(self, layer, sourceName="", baseDemandField=""):
        """Paint a Demand Builder auxiliary layer: a colour per Category, plus labels.

        Like the demand sectors', this look is computed from the layer's own values rather
        than loaded from a QML, so it has to be reapplied every time the layer is opened —
        which is why openLayer carries a flag for it instead of the callers remembering.

        `sourceName` is the file's own name: by the time a layer reaches here its display
        name may already be the translated one, and the isolated-demands connections are
        told apart by their file name.

        `baseDemandField` is what the DLL just reported, when it reported anything. It is
        only a hint: the column the point labels end up showing is resolved against the
        layer itself.
        """
        name = sourceName or layer.name()
        if "IsolatedDemandsServiceConnections" in name:
            self.setStyle(layer, "DemandBuilderIsolatedDemandsServiceConnections")
            layer.triggerRepaint()
            return

        # A style saved from the Legends Editor wins over the computed look, like sectors.
        if layer.geometryType() in (0, 1):
            savedName = "DemandBuilder_ConsumptionPoints" if layer.geometryType() == 0 else "DemandBuilder_DemandLinks"
            if self.setSavedStyle(layer, savedName):
                layer.triggerRepaint()
                return

        geomType = layer.geometryType()
        fieldIndex = layer.fields().indexFromName("Category")

        uniqueCats = set()
        hasUncategorized = False

        if fieldIndex != -1:
            for feature in layer.getFeatures():
                rawCat = feature[fieldIndex]
                text = "" if rawCat is None else str(rawCat).strip()
                if text == "" or text.lower() in ("null", "undefined"):
                    hasUncategorized = True
                else:
                    uniqueCats.add(text)

            categories = []
            if hasUncategorized:
                uncategorized = QgsSymbol.defaultSymbol(geomType)
                uncategorized.setColor(QColor("orange"))
                categories.append(QgsRendererCategory("Uncategorized", uncategorized, "Uncategorized"))

            for cat in sorted(uniqueCats):
                symbol = QgsSymbol.defaultSymbol(geomType)
                symbol.setColor(self._colorForDemandCategory(cat))
                categories.append(QgsRendererCategory(cat, symbol, cat))

            categoryExpression = (
                "CASE "
                "WHEN \"Category\" IS NULL "
                "OR trim(\"Category\") = '' "
                "OR lower(trim(\"Category\")) IN ('null', 'undefined') "
                "THEN 'Uncategorized' "
                "ELSE trim(\"Category\") "
                "END"
            )
            layer.setRenderer(QgsCategorizedSymbolRenderer(categoryExpression, categories))
            self.translateRendererLabels(layer)
        else:
            symbol = QgsSymbol.defaultSymbol(geomType)
            if geomType == 0:
                symbol.setColor(QColor("orange"))
            elif geomType == 1:
                symbol.setColor(QColor("blue"))
            layer.setRenderer(QgsSingleSymbolRenderer(symbol))

        labelSettings = QgsPalLayerSettings()
        textFormat = QgsTextFormat()
        textFormat.setSize(10)
        labelSettings.setFormat(textFormat)

        # Labels take the colour of their category, so they read against their own symbol.
        if fieldIndex != -1:
            colorExpression = "CASE "
            if hasUncategorized:
                colorExpression += (
                    "WHEN \"Category\" IS NULL OR trim(\"Category\") = '' "
                    "OR lower(trim(\"Category\")) IN ('null', 'undefined') THEN 'orange' "
                )
            for cat in sorted(uniqueCats):
                safeCat = cat.replace("'", "''")
                hexColor = self._colorForDemandCategory(cat).name()
                colorExpression += f"WHEN trim(\"Category\") = '{safeCat}' THEN '{hexColor}' "
            colorExpression += "ELSE 'gray' END"
            labelSettings.dataDefinedProperties().setProperty(
                PAL_PROPERTY_COLOR, QgsProperty.fromExpression(colorExpression)
            )

        if geomType == 1:
            if layer.fields().indexFromName("%Dem") != -1:
                labelSettings.fieldName = '"%Dem" || \' %\''
                labelSettings.isExpression = True
                labelSettings.enabled = True
                labelSettings.placement = PAL_PLACEMENT_LINE
                layer.setLabelsEnabled(True)
                layer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))
        elif geomType == 0:
            # Not the name the DLL reported unless the layer really carries it: a theme
            # opened from the project or from the layer manager arrives with no name at
            # all, and its columns are the user's to name (see resolveBaseDemandField).
            labelField = resolveBaseDemandField([f.name() for f in layer.fields()], baseDemandField)
            if labelField:
                pointTextFormat = QgsTextFormat()
                pointTextFormat.setSize(12)
                pointTextFormat.setColor(QColor("black"))
                labelSettings.setFormat(pointTextFormat)
                labelSettings.fieldName = f'"{labelField}"'
                labelSettings.isExpression = True
                labelSettings.enabled = True
                layer.setLabelsEnabled(True)
                layer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))

        layer.triggerRepaint()

    def setSectorsStyle(self, layer):
        # get unique values
        field = "Class"
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors
            field = "SubNet"
            fni = layer.fields().indexFromName(field)

        uniqueValues = layer.dataProvider().uniqueValues(fni)
        uniqueValues = sorted(uniqueValues)

        cache_key = (self.ProjectDirectory or "", self.NetworkName or "", field)
        if cache_key not in _DEMAND_SECTOR_COLOR_CACHE:
            _DEMAND_SECTOR_COLOR_CACHE[cache_key] = {}
        color_map = _DEMAND_SECTOR_COLOR_CACHE[cache_key]

        # add missing values to the shared color map
        for uniqueValue in uniqueValues:
            if uniqueValue not in color_map:
                color_map[uniqueValue] = QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256))  # nosec B311 — cosmetic sector color, not security-sensitive

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbolLayer = None
            value_color = color_map.get(uniqueValue, QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256)))  # nosec B311 — cosmetic sector color, not security-sensitive

            if layer.geometryType() == 0:  # Point
                layerStyle = {
                    "color": "%d, %d, %d" % (value_color.red(), value_color.green(), value_color.blue()),
                    "size": str(2),
                }
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidth(1.1)
                lineSymbol.setColor(value_color)
                symbol.appendSymbolLayer(lineSymbol)

            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            category = QgsRendererCategory(uniqueValue, symbol, self._translateCategoryLabel(uniqueValue, field))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setLabelsEnabled(False)

    def fillCategoriesFromData(self, layer, field):
        """Add a category for every value of `field` the loaded style does not list yet.

        The style (shipped or saved by the user) carries the look — source symbol, colour
        ramp, map tip — but the values only exist once the data is computed, so they are
        appended here. Categories already in the style keep their own colour.
        """
        renderer = layer.renderer()
        fieldIndex = layer.fields().indexFromName(field)
        if not isinstance(renderer, QgsCategorizedSymbolRenderer) or fieldIndex == -1:
            return
        knownValues = {category.value() for category in renderer.categories()}
        uniqueValues = sorted(layer.dataProvider().uniqueValues(fieldIndex))
        newValues = [value for value in uniqueValues if value not in knownValues]
        if not newValues:
            return

        ramp = renderer.sourceColorRamp()
        categories = list(renderer.categories())
        template = renderer.sourceSymbol() or (categories[-1].symbol() if categories else None)
        if template is None:
            return
        if isinstance(ramp, QgsLimitedRandomColorRamp):  # one distinct colour per new value
            ramp.setCount(len(newValues))
        for position, value in enumerate(newValues):
            symbol = template.clone()
            if ramp is not None:
                symbol.setColor(ramp.color(position / max(len(newValues) - 1, 1)))
            categories.append(QgsRendererCategory(value, symbol, self._translateCategoryLabel(value, field)))

        layer.setRenderer(self._rebuildCategorizedRenderer(renderer, categories))

    @staticmethod
    def developmentStyleDatabasePath():
        """The style database tracked in git. Only a checkout has it: the release ZIP
        leaves it out, so a released plugin reads the installer's copy instead."""
        return os.path.join(_plugin_root(), "defaults", STYLE_DATABASE_NAME + ".bak")

    @staticmethod
    def styleDatabasePath():
        """The style database QGIS opens.

        In a checkout it is the .db regenerated beside the tracked .bak, never the .bak
        itself: QGIS keeps whatever it opens locked for the whole session, and Windows would
        then refuse the `git pull` that rewrites it. The regenerated file is invisible to git
        (.gitignore carries *.db), so it can be locked with no consequence.
        """
        if os.path.exists(QGISRedStylingUtils.developmentStyleDatabasePath()):
            return os.path.join(_plugin_root(), "defaults", STYLE_DATABASE_NAME)
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return os.path.join(QGISRedFileSystemUtils().getDefaultsFolder(), STYLE_DATABASE_NAME)

    @staticmethod
    def ensureStyleDatabase():
        """Regenerate the working .db from the tracked .bak. Called once per plugin load.

        The .bak is the source of truth and nothing of the user's lives in the copy. Content
        is compared first rather than blindly rewriting: QGIS holds the working copy open for
        the whole session once it is registered (see unregisterStyleDatabaseFromProject), and
        whether that handle is actually released on a same-instance plugin reload is outside
        this plugin's control. Skipping the write when nothing changed keeps the ordinary
        reload — which never touches the .bak — from tripping the locked-file warning below
        for no reason. A released plugin has no .bak and this does nothing: there the
        installer's database is opened where it lies, outside any checkout.

        os.replace is what keeps a second QGIS instance safe when the .bak did change — it
        fails rather than writing under the handle that instance still holds, and the instance
        keeps reading a valid database until the next start.
        """
        developmentPath = QGISRedStylingUtils.developmentStyleDatabasePath()
        if not os.path.exists(developmentPath):
            return
        workingPath = QGISRedStylingUtils.styleDatabasePath()
        if os.path.exists(workingPath) and filecmp.cmp(developmentPath, workingPath, shallow=False):
            return
        stagedPath = "%s.%d.new" % (workingPath, os.getpid())
        try:
            shutil.copy2(developmentPath, stagedPath)
            os.replace(stagedPath, workingPath)
        except OSError:
            with suppress(OSError):
                os.remove(stagedPath)
            # Silence here would read as "my change did not take": say who is holding it.
            QgsMessageLog.logMessage(
                QCoreApplication.translate(
                    "QGISRedStylingUtils",
                    "Another QGIS instance is using the style database: it keeps the previous "
                    "one. Close the other instance and restart QGIS to pick up the changes.",
                ),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )

    @staticmethod
    def unregisterStyleDatabaseFromProject():
        """Drop the database from the Style Manager so QGIS releases its file handle.

        Without this a plugin reload cannot refresh the working copy in a checkout: this very
        QGIS would still hold the .db open and Windows would refuse the replace.
        """
        currentKey = os.path.normcase(os.path.normpath(QGISRedStylingUtils.styleDatabasePath()))
        styleSettings = QgsProject.instance().styleSettings()
        registered = list(styleSettings.styleDatabasePaths())
        remaining = [path for path in registered
                     if os.path.normcase(os.path.normpath(path)) != currentKey]
        if remaining != registered:
            styleSettings.setStyleDatabasePaths(remaining)

    def getMaterialColorFromDb(self, materialValue):
        databasePath = QGISRedStylingUtils.styleDatabasePath()
        if not os.path.exists(databasePath):
            return None
        with suppress(sqlite3.Error):
            connection = sqlite3.connect(databasePath)
            try:
                row = connection.execute(
                    "SELECT color FROM materialColors WHERE label = ?", (materialValue,)
                ).fetchone()
                return row[0] if row else None
            finally:
                connection.close()
        return None

    @classmethod
    def findColorRampKind(cls, rampName):
        pluginStyle = QgsStyle()
        databasePath = QGISRedStylingUtils.styleDatabasePath()
        if os.path.exists(databasePath) and pluginStyle.load(databasePath) and pluginStyle.colorRamp(rampName) is not None:
            return cls.colorRampKind(pluginStyle, rampName)
        return cls.colorRampKind(QgsStyle.defaultStyle(), rampName)

    @staticmethod
    def findColorRamp(rampName):
        # Saved legend strategies name a ramp of the QGISRed database; the user
        # default style is only a fallback and is never written to.
        pluginStyle = QgsStyle()
        databasePath = QGISRedStylingUtils.styleDatabasePath()
        if os.path.exists(databasePath) and pluginStyle.load(databasePath):
            ramp = pluginStyle.colorRamp(rampName)
            if ramp is not None:
                return ramp
        return QgsStyle.defaultStyle().colorRamp(rampName)

    @staticmethod
    def registerStyleDatabaseInProject():
        """List this machine's QGISRed database in the Style Manager, and only this one.

        A project stores the style database paths it was saved with, so it comes back
        carrying whichever path the machine that saved it used — a plugin checkout, another
        install root, another user's home. None of those resolve here, and the list is only
        ever appended to, so without pruning a project would collect one dead entry per
        machine it travels to.
        """
        databasePath = QGISRedStylingUtils.styleDatabasePath()
        currentKey = os.path.normcase(os.path.normpath(databasePath))
        styleSettings = QgsProject.instance().styleSettings()
        registered = list(styleSettings.styleDatabasePaths())

        ourName = STYLE_DATABASE_NAME.lower()
        kept = [path for path in registered
                if os.path.basename(path).lower() != ourName
                or os.path.normcase(os.path.normpath(path)) == currentKey]
        if os.path.exists(databasePath) and currentKey not in [
                os.path.normcase(os.path.normpath(path)) for path in kept]:
            kept.append(databasePath)
        # Rewriting an unchanged list would mark the project dirty on every open.
        if kept != registered:
            styleSettings.setStyleDatabasePaths(kept)

    def applyCategorizedRenderer(self, layer, field, qmlFile):
        fieldIndex = layer.fields().indexFromName(field)

        if fieldIndex == -1:
            raise ValueError(self.tr("%1 field not found in layer %2").replace("%1", field).replace("%2", layer.name()))

        uniqueValues = layer.uniqueValues(fieldIndex)
        categories = []

        existingCategories = {}
        if qmlFile and os.path.exists(qmlFile):
            tempLayer = QgsVectorLayer(layer.source(), layer.name(), layer.providerType())
            tempLayer.loadNamedStyle(qmlFile)
            renderer = tempLayer.renderer()

            if isinstance(renderer, QgsCategorizedSymbolRenderer):
                for cat in renderer.categories():
                    existingCategories[cat.value()] = cat.symbol().color()

        nonNullValues = [value for value in uniqueValues if value != NULL]
        nullValues = [value for value in uniqueValues if value == NULL]

        # The fixed material palette only backs the shipped default style; a project
        # or global style saved from the Legends dialog must prevail over it.
        isDefaultStyle = bool(qmlFile) and qmlFile.endswith(".qml.bak")

        for value in nonNullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            paletteColor = None
            if isDefaultStyle and field == "Material":
                materialKey = str(value).strip().lower()
                paletteColor = self.getMaterialColorFromDb(materialKey)
            if value in existingCategories:
                symbol.setColor(existingCategories[value])
            elif paletteColor is not None:
                symbol.setColor(QColor(paletteColor))
            else:
                randomColor = QColor.fromRgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))  # nosec B311 — cosmetic category color, not security-sensitive
                symbol.setColor(randomColor)
            symbol.setWidth(0.8)
            category = QgsRendererCategory(value, symbol, self._translateCategoryLabel(value, field))
            categories.append(category)

        if nullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            lightGray = QColor.fromRgb(238, 238, 238)
            symbol.setColor(lightGray)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(nullValues[0], symbol, str("#NA"))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)
        # .qml.bak files are the plugin's shipped defaults and must never be rewritten.
        if qmlFile and not qmlFile.endswith(".qml.bak"):
            layer.saveNamedStyle(qmlFile)

    def hideFields(self, layer, fieldname, idFieldName=None):
        config = layer.attributeTableConfig()
        columns = config.columns()

        # The identity column's name is per-layer (ValveID, PumpID, ...) on a project
        # exported by the current DLL, not the legacy bare "Id" this used to hardcode.
        # getIdFieldName() resolves it from the layer's own qgisred_identifier property;
        # callers whose layer doesn't carry that (e.g. a derived query layer tagged with
        # its own query identifier instead) must resolve it themselves and pass it in.
        if idFieldName is None:
            idFieldName = QGISRedFieldUtils().getIdFieldName(layer)
        fieldnames = [fieldname] if isinstance(fieldname, str) else list(fieldname)
        fieldsToKeep = [idFieldName] + fieldnames

        for column in columns:
            column.hidden = column.name not in fieldsToKeep

        config.setColumns(columns)

        layerCache = QgsVectorLayerCache(layer, layer.featureCount())

        sourceModel = QgsAttributeTableModel(layerCache)
        sourceModel.loadLayer()

        attributeTableView = QgsAttributeTableView()
        attributeTableFilterModel = QgsAttributeTableFilterModel(_iface.mapCanvas(), sourceModel)

        layer.setAttributeTableConfig(config)
        attributeTableFilterModel.setAttributeTableConfig(config)
        attributeTableView.setAttributeTableConfig(config)

    def applyNullStyle(self, layer):
        """Add a gray symbol for NULL values mimicking the original style complexity recursively."""
        renderer = layer.renderer()
        if renderer is None:
            return

        # If already rule-based (NullRule was applied in a previous session), the
        # _NullHiddenLegend wrapper is not serialized to .qgs, so re-attach it.
        if isinstance(renderer, QgsRuleBasedRenderer):
            for rule in renderer.rootRule().children():
                if _NULL_RULE_LABEL in rule.label():
                    layer.setLegend(_NullHiddenLegend(layer))
                    break
            return

        def make_gray(symbol):
            if not symbol:
                return
            for i in range(symbol.symbolLayerCount()):
                sl = symbol.symbolLayer(i)
                with suppress(Exception):
                    # Most layers respond to setColor
                    sl.setColor(QColor(192, 192, 192))
                    if hasattr(sl, "setStrokeColor"):
                        sl.setStrokeColor(QColor(160, 160, 160))
                # Handle sub-symbols recursively (needed for arrows, marker lines, etc.)
                if hasattr(sl, "subSymbol") and sl.subSymbol():
                    make_gray(sl.subSymbol())

        # Obtain a template symbol from the existing renderer to preserve complexity
        context = QgsRenderContext()
        symbols = renderer.symbols(context)
        if symbols:
            null_symbol = symbols[0].clone()
            make_gray(null_symbol)
        else:
            null_symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            null_symbol.setColor(QColor(192, 192, 192))

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            # For categorized, we stay consistent
            found = False
            for cat in renderer.categories():
                if cat.value() == NULL or cat.label() == "#NA":
                    found = True
                    break
            if not found:
                category = QgsRendererCategory(NULL, null_symbol.clone(), "#NA", True)
                renderer.addCategory(category)
                layer.setRenderer(renderer.clone())

        elif isinstance(renderer, QgsGraduatedSymbolRenderer):
            # QgsGraduatedSymbolRenderer skips NULL features entirely, so we need an
            # explicit rule-based renderer with a catch-all NULL rule.
            #
            # Converted with QGIS's own convertFromRenderer() -- the exact code path
            # QGIS's "Convert to... > Rule-based" panel action uses -- rather than
            # rebuilding the rule tree by hand (cloning every range's symbol, building
            # Rule objects and appendChild()ing them one by one, as this used to do):
            # that manual reconstruction was isolated as the source of intermittent
            # native access-violation crashes in QGIS's own legend-preview code,
            # reproduced reliably right after the first simulate on a small network.
            # convertFromRenderer is exercised by every QGIS user who has ever used
            # that panel button, so it is far less likely to carry this kind of bug.
            class_attr = renderer.classAttribute()
            new_renderer = QgsRuleBasedRenderer.convertFromRenderer(renderer)
            if new_renderer is None:
                return  # conversion failed for some reason; leave the graduated renderer as-is

            # convertFromRenderer() quotes classAttribute as if it were a plain field
            # name (the original reason this function avoided it), which breaks when
            # it is actually an expression like abs(Flow): the generated filter ends
            # up comparing against a field literally named "abs(Flow)". Patch the
            # quoted literal back into a parenthesized expression in every rule --
            # string-only, no renderer/symbol object manipulation involved.
            quoted_attr = '"' + class_attr + '"'
            if quoted_attr != class_attr:
                for rule in new_renderer.rootRule().children():
                    expr = rule.filterExpression()
                    if quoted_attr in expr:
                        rule.setFilterExpression(expr.replace(quoted_attr, "(" + class_attr + ")"))

            null_rule = QgsRuleBasedRenderer.Rule(null_symbol.clone())
            null_rule.setIsElse(True)
            null_rule.setLabel(_NULL_RULE_LABEL)
            new_renderer.rootRule().appendChild(null_rule)

            layer.setRenderer(new_renderer)

            # Hide the NULL rule from the legend.
            layer.setLegend(_NullHiddenLegend(layer))
