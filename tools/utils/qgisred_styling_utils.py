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
    QgsMapLayerLegend, QgsSingleSymbolRenderer
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

    def setResultStyle(self, layer, name=""):
        # Convert result layer name to QML filename (e.g., "Link_Flow" -> "LinkFlow")
        qmlName = name.replace("_", "") if name else ""

        # Search order: project folder -> layerStyles -> defaults/layerStyles
        if qmlName:
            # 1- project style
            projectStylePath = os.path.join(self.ProjectDirectory, "layerStyles")
            qmlPath = os.path.join(projectStylePath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                layer.setLabelsEnabled(False)
                return

            # 2- global style
            globalStylesPath = os.path.join(self._getQGISRedFolder(), "defaults", "layerStyles")
            qmlPath = os.path.join(globalStylesPath, qmlName + ".qml")
            if os.path.exists(qmlPath):
                layer.loadNamedStyle(qmlPath)
                layer.setLabelsEnabled(False)
                return

            # 3- default style
            pluginPath = _plugin_root()
            defaultStylePath = os.path.join(pluginPath, "defaults", "layerStyles")
            qmlPath = os.path.join(defaultStylePath, qmlName + ".qml.bak")
            layer.loadNamedStyle(qmlPath)
            layer.setLabelsEnabled(False)

    def setSectorsStyle(self, layer):
        # get unique values
        field = "Class"
        fni = layer.fields().indexFromName(field)

        if fni == -1:  # Hydraulic sectors without Class field
            field = "SubNet"
            fni = layer.fields().indexFromName(field)

        uniqueValues = layer.dataProvider().uniqueValues(fni)
        uniqueValues = sorted(uniqueValues)

        class_colors = {
            "H-Q": "77, 255, 136",
            "H-nQ": "128, 255, 255",
            "nH-nQ": "255, 255, 179",
            "nH-Q": "255, 166, 77"
        }

        if layer.geometryType() == 0:
            categories = []
            for uniqueValue in uniqueValues:
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())

                layerStyle = dict()
                if field == "Class" and str(uniqueValue) in class_colors:
                    layerStyle["color"] = class_colors[str(uniqueValue)]
                else:
                    layerStyle["color"] = "%d, %d, %d" % (
                        randrange(0, 256), randrange(0, 256), randrange(0, 256))

                layerStyle["size"] = str(2)
                symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
                if symbolLayer is not None:
                    symbol.changeSymbolLayer(0, symbolLayer)

                category = QgsRendererCategory(uniqueValue, symbol, str(uniqueValue))
                categories.append(category)

            renderer = QgsCategorizedSymbolRenderer(field, categories)
            if renderer is not None:
                layer.setRenderer(renderer)
            layer.setLabelsEnabled(False)
            return

        root_rule = QgsRuleBasedRenderer.Rule(None)

        for class_value, color_str in class_colors.items():
            rgb = [int(x.strip()) for x in color_str.split(",")]

            # Special rule: nH-nQ + ClosedLinks -> black
            if class_value == "nH-nQ":
                black_symbol = QgsLineSymbol().createSimple({})
                black_symbol.deleteSymbolLayer(0)

                black_line = QgsSimpleLineSymbolLayer()
                try:
                    black_line.setWidthUnit(Qgis.RenderUnit.RenderPixels)
                except:
                    black_line.setWidthUnit(2)
                black_line.setWidth(2)
                black_line.setColor(QColor(153, 153, 153))
                black_symbol.appendSymbolLayer(black_line)

                black_rule = QgsRuleBasedRenderer.Rule(black_symbol)
                black_rule.setLabel("nH-nQ ClosedLinks")
                black_rule.setFilterExpression("\"Class\" = 'nH-nQ' AND \"SubNet\" = 'ClosedLinks'")
                root_rule.appendChild(black_rule)

                normal_symbol = QgsLineSymbol().createSimple({})
                normal_symbol.deleteSymbolLayer(0)

                normal_line = QgsSimpleLineSymbolLayer()
                try:
                    normal_line.setWidthUnit(Qgis.RenderUnit.RenderPixels)
                except:
                    normal_line.setWidthUnit(2)
                normal_line.setWidth(2)
                normal_line.setColor(QColor(rgb[0], rgb[1], rgb[2]))
                normal_symbol.appendSymbolLayer(normal_line)

                normal_rule = QgsRuleBasedRenderer.Rule(normal_symbol)
                normal_rule.setLabel("nH-nQ")
                normal_rule.setFilterExpression("\"Class\" = 'nH-nQ' AND \"SubNet\" <> 'ClosedLinks'")
                root_rule.appendChild(normal_rule)

            else:
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)

                lineSymbol = QgsSimpleLineSymbolLayer()
                try:
                    lineSymbol.setWidthUnit(Qgis.RenderUnit.RenderPixels)
                except:
                    lineSymbol.setWidthUnit(2)
                lineSymbol.setWidth(2)
                lineSymbol.setColor(QColor(rgb[0], rgb[1], rgb[2]))
                symbol.appendSymbolLayer(lineSymbol)

                rule = QgsRuleBasedRenderer.Rule(symbol)
                rule.setLabel(class_value)
                rule.setFilterExpression(f"\"Class\" = '{class_value}'")
                root_rule.appendChild(rule)

        renderer = QgsRuleBasedRenderer(root_rule)
        layer.setRenderer(renderer)
        layer.setLabelsEnabled(False)
    
    def setIsolatedDemandsStyle(self, layer):
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())

        if layer.geometryType() == 0:  # Point
            layerStyle = {
                "name": "circle",
                "color": "0,0,0,0",             
                "outline_color": "255,0,0",   
                "outline_width": "0.9",       
                "size": "3"
            }
            symbolLayer = QgsSimpleMarkerSymbolLayer.create(layerStyle)
            if symbolLayer is not None:
                symbol.changeSymbolLayer(0, symbolLayer)

        renderer = QgsSingleSymbolRenderer(symbol)
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

    def setIsolatedSegmentsStyle(self, layer):
        stylePath = os.path.join(_plugin_root(), "defaults", "layerStyles")

        # default style
        if layer.geometryType() == 0:  # Point
            qmlBasePath = os.path.join(stylePath, "isolatedSegmentsNodes.qml.bak")
        else:
            qmlBasePath = os.path.join(stylePath, "isolatedSegmentsLinks.qml.bak")
        layer.loadNamedStyle(qmlBasePath)
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
