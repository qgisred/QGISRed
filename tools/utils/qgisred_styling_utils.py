# -*- coding: utf-8 -*-
import os
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
    QgsMapLayerLegend
)
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
from qgis.utils import iface as _iface


def _plugin_root():
    """Returns the plugin root directory (two levels up from tools/utils/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


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
            return

        # 2- global style
        stylePath = os.path.join(self._getQGISRedFolder(), "defaults", "layerStyles")
        qmlPath = os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            layer.setLabelsEnabled(False)
            return

        # 3- default style
        pluginPath = _plugin_root()
        defaultStylePath = os.path.join(pluginPath, "defaults", "layerStyles")
        qmlPath = os.path.join(defaultStylePath, name + ".qml.bak")
        layer.loadNamedStyle(qmlPath)
        layer.setLabelsEnabled(False)

    def setSectorsStyle(self, layer):
        # get unique values
        field = "Class"
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors
            field = "SubNet"
            fni = layer.fields().indexFromName(field)

        uniqueValues = layer.dataProvider().uniqueValues(fni)
        uniqueValues = sorted(uniqueValues)

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbolLayer = None
            if layer.geometryType() == 0:  # Point
                layerStyle = dict()
                layerStyle["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layerStyle["size"] = str(2)
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(2)
                lineSymbol.setColor(QColor(randrange(0, 256), randrange(0, 256), randrange(0, 256)))
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            # create renderer object
            category = QgsRendererCategory(uniqueValue, symbol, str(uniqueValue))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRenderer(renderer)
        layer.setLabelsEnabled(False)
    
    def setTreeStyle(self, layer):
        # get unique values
        field = "ArcType"
        fni = layer.fields().indexFromName(field)
        uniqueValues = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for uniqueValue in uniqueValues:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            symbolLayer = None
            if layer.geometryType() == 0:  # Point
                layerStyle = dict()
                layerStyle["color"] = "%d, %d, %d" % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
                layerStyle["size"] = str(2)
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                try:  # From QGis 3.30
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)  # Pixels
                except:
                    lineSymbol.setWidthUnit(2)  # Pixels
                lineSymbol.setWidth(3)
                lineSymbol.setColor(QColor(178, 47, 60))
                if "Branch" in uniqueValue:
                    lineSymbol.setColor(QColor(22, 139, 251))
                else:
                    lineSymbol.setPenStyle(Qt.PenStyle.DashLine)
                    lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)

            # replace default symbol layer with the configured one
            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

            # translated legend label
            if "Branch" in uniqueValue:
                label = self.tr("Branches")
            else:
                label = self.tr("Chords")

            category = QgsRendererCategory(uniqueValue, symbol, label)
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(field, categories)

        # assign the created renderer to the layer
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
