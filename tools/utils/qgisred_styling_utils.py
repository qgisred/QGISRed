# -*- coding: utf-8 -*-
import math
import os
import json
import random
from random import randrange

from qgis.PyQt.QtCore import QCoreApplication, Qt
from ...compat import PAINTER_ANTIALIASING
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsVectorLayer, QgsSymbol, Qgis, QgsLayerTreeGroup,
    QgsLineSymbol, QgsSimpleLineSymbolLayer, QgsSimpleMarkerSymbolLayer,
    QgsRendererCategory, QgsCategorizedSymbolRenderer, QgsVectorLayerCache, NULL,
    QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer, QgsProject, QgsRenderContext,
    QgsMapLayerLegend, QgsMessageLog, QgsStyle
)
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.utils import iface as _iface


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


_DEMAND_SECTOR_COLOR_CACHE = {}


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
        try:
            ratio = iface.mainWindow().devicePixelRatioF()
        except Exception:
            pass

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

    def setStyle(self, layer, name):
        if name == "":
            return
        name = name.replace("_", "") if name else ""

        # 1- project style
        projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
        qmlPath = os.path.join(projectStylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            layer.setLabelsEnabled(False)
            self.applyStrategyFromLayer(layer)
            self.translateRendererLabels(layer)
            return

        # 2- global style
        stylePath = os.path.join(self._getQGISRedFolder(), "defaults", "layerStyles")
        qmlPath = os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            layer.setLabelsEnabled(False)
            self.applyStrategyFromLayer(layer)
            self.translateRendererLabels(layer)
            return

        # 3- default style
        pluginPath = _plugin_root()
        defaultStylePath = os.path.join(pluginPath, "defaults", "layerStyles")
        qmlPath = os.path.join(defaultStylePath, name + ".qml.bak")
        layer.loadNamedStyle(qmlPath)
        layer.setLabelsEnabled(False)
        self.applyStrategyFromLayer(layer)
        self.translateRendererLabels(layer)

    def resolveStylePath(self, qmlFile):
        projectPath = os.path.join(self.ProjectDirectory, "layerStyles", qmlFile)
        if os.path.exists(projectPath):
            return projectPath
        globalPath = os.path.join(self._getQGISRedFolder(), "layerStyles", qmlFile)
        if os.path.exists(globalPath):
            return globalPath
        return os.path.join(_plugin_root(), "defaults", "layerStyles", qmlFile + ".bak")

    def applyStrategyFromLayer(self, layer):
        rawStrategy = layer.customProperty("qgisred_legend_strategy")
        if not rawStrategy:
            return
        try:
            strategy = json.loads(rawStrategy)
            self.applyLegendStrategy(layer, strategy)
        except Exception as ex:
            QgsMessageLog.logMessage(
                self.tr("Failed to apply legend strategy for layer %1: %2")
                    .replace("%1", layer.name()).replace("%2", str(ex)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )

    def applyLegendStrategy(self, layer, strategy):
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

        field = strategy.get("field")
        if not field:
            return
        fieldIndex = layer.fields().indexFromName(field)
        if fieldIndex == -1:
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

        if "intervals" in parts and mode == "graduated":
            self.applyGraduatedClassification(layer, field, self.resolveIntervalsBlock(strategy))

        if "colors" in parts:
            colorsBlock = self.resolveColorsBlock(strategy)
            if mode == "categorized":
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
            try:
                context = QgsRenderContext()
                symbols = renderer.symbols(context)
                if symbols:
                    return symbols[0].clone()
            except Exception:
                pass
        return QgsSymbol.defaultSymbol(layer.geometryType())

    def cloneRendererRamp(self, layer):
        renderer = layer.renderer()
        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            ramp = renderer.sourceColorRamp()
            if ramp:
                return ramp.clone()
        return QgsStyle.defaultStyle().colorRamp("Spectral")

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
            ramp = QgsStyle.defaultStyle().colorRamp(rampName)
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
        for index, value in enumerate(nonNullValues):
            symbol = templateSymbol.clone()
            color = self.resolveCategoryColor(value, index, valueCount, ramp, invertRamp)
            symbol.setColor(color)
            categories.append(QgsRendererCategory(value, symbol, self._translateCategoryLabel(value)))

        if nullValues:
            symbol = templateSymbol.clone()
            symbol.setColor(QColor.fromRgb(192, 192, 192))
            categories.append(QgsRendererCategory(nullValues[0], symbol, "#NA"))

        layer.setRenderer(QgsCategorizedSymbolRenderer(field, categories))

    def applyGraduatedColors(self, layer, colorsBlock):
        renderer = layer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return
        rampName = colorsBlock.get("rampName")
        invertRamp = colorsBlock.get("invertRamp", False)
        if not rampName:
            return
        ramp = QgsStyle.defaultStyle().colorRamp(rampName)
        if ramp is None:
            QgsMessageLog.logMessage(
                self.tr("Color ramp '%1' not found; colors strategy skipped")
                    .replace("%1", str(rampName)),
                "QGISRed",
                Qgis.MessageLevel.Warning,
            )
            return
        if invertRamp:
            ramp.invert()

        ranges = renderer.ranges()
        rangeCount = max(len(ranges), 1)
        for index in range(len(ranges)):
            position = 0.0 if rangeCount <= 1 else index / float(rangeCount - 1)
            symbol = ranges[index].symbol().clone()
            symbol.setColor(ramp.color(position))
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

    def resolveCategoryColor(self, value, index, valueCount, ramp, invertRamp):
        if ramp is not None:
            position = 0.0 if valueCount <= 1 else index / float(valueCount - 1)
            if invertRamp:
                position = 1.0 - position
            return ramp.color(position)
        seededRandom = random.Random(hash(str(value)))
        return QColor.fromRgb(
            seededRandom.randint(0, 255),
            seededRandom.randint(0, 255),
            seededRandom.randint(0, 255),
        )

    def _translateCategoryLabel(self, value):
        if isinstance(value, str):
            if value == "Undefined":
                return self.tr("Undefined") 
            if value == "ClosedLinks":
                return self.tr("Closed Links")
        return str(value)

    def translateRendererLabels(self, layer):
        renderer = layer.renderer()
        if renderer is None:
            return

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            categories = []
            for category in renderer.categories():
                categories.append(
                    QgsRendererCategory(
                        category.value(),
                        category.symbol().clone(),
                        self._translateCategoryLabel(category.value()),
                    )
                )
            layer.setRenderer(QgsCategorizedSymbolRenderer(renderer.classAttribute(), categories))

        elif isinstance(renderer, QgsRuleBasedRenderer):
            self._translateRuleLabels(renderer.rootRule())

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
                color_map[uniqueValue] = QColor(
                    randrange(0, 256),
                    randrange(0, 256),
                    randrange(0, 256),
                )

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbolLayer = None
            value_color = color_map.get(uniqueValue, QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256)))

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
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except Exception:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(2)
                lineSymbol.setColor(value_color)
                symbol.appendSymbolLayer(lineSymbol)

            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            category = QgsRendererCategory(uniqueValue, symbol, self._translateCategoryLabel(uniqueValue))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setLabelsEnabled(False)
    
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

        for value in nonNullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            if value in existingCategories:
                symbol.setColor(existingCategories[value])
            else:
                randomColor = QColor.fromRgb(
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255)
                )
                symbol.setColor(randomColor)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        if nullValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            darkGray = QColor.fromRgb(192, 192, 192)
            symbol.setColor(darkGray)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(nullValues[0], symbol, str("#NA"))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)
        layer.saveNamedStyle(qmlFile)

    def hideFields(self, layer, fieldname):
        config = layer.attributeTableConfig()
        columns = config.columns()

        fieldsToKeep = ['Id', fieldname]

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
                try:
                    # Most layers respond to setColor
                    sl.setColor(QColor(192, 192, 192))
                    if hasattr(sl, "setStrokeColor"):
                        sl.setStrokeColor(QColor(160, 160, 160))
                except:
                    pass
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
            # QgsGraduatedSymbolRenderer skips NULL features entirely, so we
            # must convert to rule-based. We build the rules manually instead of
            # using convertFromRenderer() because convertFromRenderer wraps the
            # classAttribute in double quotes (treating it as a field name), which
            # breaks when classAttribute is an expression like abs(Flow).
            class_attr = renderer.classAttribute()
            ranges = renderer.ranges()
            root_rule = QgsRuleBasedRenderer.Rule(None)

            for i, r in enumerate(ranges):
                rule = QgsRuleBasedRenderer.Rule(r.symbol().clone())
                rule.setLabel(r.label())
                lo, hi = r.lowerValue(), r.upperValue()
                # First range: inclusive lower bound; subsequent: exclusive lower bound
                lo_op = ">=" if i == 0 else ">"
                expr = f"({class_attr}) {lo_op} {lo} AND ({class_attr}) <= {hi}"
                rule.setFilterExpression(expr)
                root_rule.appendChild(rule)

            null_rule = QgsRuleBasedRenderer.Rule(null_symbol.clone())
            null_rule.setIsElse(True)
            null_rule.setLabel(_NULL_RULE_LABEL)
            root_rule.appendChild(null_rule)

            new_renderer = QgsRuleBasedRenderer(root_rule)
            layer.setRenderer(new_renderer)

            # Hide the NULL rule from the legend.
            layer.setLegend(_NullHiddenLegend(layer))
