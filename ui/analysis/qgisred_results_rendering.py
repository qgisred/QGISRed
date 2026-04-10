# -*- coding: utf-8 -*-
import re

from qgis.core import (
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat,
    QgsProperty, QgsRenderContext,
    QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer, QgsRendererRange,
    QgsProject,
)
from qgis.PyQt.QtGui import QColor, QFont

from ...tools.utils.qgisred_styling_utils import QGISRedStylingUtils, _NULL_RULE_LABEL, _NullHiddenLegend
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils


def time_field_name(var_name, layer_type):
    """Return the time-companion field name for a variable based on layer type."""
    if layer_type == "Node":
        mapping = {
            "Pressure": "Time_H",
            "Head": "Time_H",
            "Demand": "Time_D",
            "Quality": "Time_Q"
        }
    else:  # Link
        mapping = {
            "Flow": "Time_H",
            "Velocity": "Time_H",
            "HeadLoss": "Time_H",
            "UnitHdLoss": "Time_H",
            "Quality": "Time_Q"
        }
    return mapping.get(var_name)


class _ResultsRenderingMixin:
    """Mixin for QGISRedResultsDock: symbology, rendering and layer style management."""

    def _getRenderStorageKey(self, layer_path, var_key):
        """Build the cache key used to store/retrieve a renderer for a given layer and variable."""
        prefix = f"stat_{self._currentStat}|" if self._statsMode else "time|"
        return f"{prefix}{layer_path}|{var_key}"

    def _lookupCachedRenderer(self, layer, db_field_name):
        """Look up any previously saved renderer for this layer and variable in the render cache.

        Returns (ranges, has_render) where ranges is the cached renderer data (or None)
        and has_render is True when a cached renderer was found.
        """
        render_cache = self.Renders.get(self.Scenario)
        layer_path = self.getLayerPath(layer)
        storage_key = self._getRenderStorageKey(layer_path, db_field_name)
        ranges = None
        has_render = False

        if render_cache is None:
            # Scenario not found — fall back to Base scenario
            base_render_cache = self.Renders.get("Base")
            if base_render_cache is not None:
                base_key = self._getRenderStorageKey(
                    layer_path.replace("_" + self.Scenario + "_", "_Base_"), db_field_name
                )
                ranges = base_render_cache.get(base_key)
                if ranges is not None:
                    has_render = True
        else:
            ranges = render_cache.get(storage_key)
            if ranges is not None:
                has_render = True
            else:
                # Current scenario has no entry — fall back to Base scenario
                base_render_cache = self.Renders.get("Base")
                if base_render_cache is not None:
                    base_key = self._getRenderStorageKey(
                        layer_path.replace("_" + self.Scenario + "_", "_Base_"), db_field_name
                    )
                    ranges = base_render_cache.get(base_key)
                    if ranges is not None:
                        has_render = True

        return ranges, has_render

    def saveCurrentRender(self):
        scenario_renders = self.Renders.get(self.Scenario, {})

        for nameLayer in ["Node", "Link"]:
            layer = self._findResultLayer(nameLayer)
            if not layer:
                continue

            var_key = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
            if not var_key:
                continue

            layer_path = self.getLayerPath(layer)
            storage_key = self._getRenderStorageKey(layer_path, var_key)
            renderer = layer.renderer()
            try:
                if renderer.type() == "graduatedSymbol":
                    scenario_renders[storage_key] = renderer.ranges()
                elif renderer.type() == "RuleRenderer":
                    root = renderer.rootRule()
                    children = root.children()
                    child_labels = {c.label() for c in children}
                    if any(_NULL_RULE_LABEL in lbl for lbl in child_labels):
                        if var_key != "Status":
                            ranges = []
                            for rule in children:
                                if _NULL_RULE_LABEL in rule.label():
                                    continue
                                m = re.search(r'[>]=? ?([\d.eE+\-]+) AND .+?<= ?([\d.eE+\-]+)', rule.filterExpression())
                                if m:
                                    ranges.append(QgsRendererRange(float(m.group(1)), float(m.group(2)), rule.symbol().clone(), rule.label()))
                            if ranges:
                                scenario_renders[storage_key] = ranges
                    else:
                        scenario_renders[storage_key] = root.clone()
            except:
                message = self.tr("Some issue occurred in the process of saving the style of the layer").format(self.tr(nameLayer))
                QGISRedUIUtils.showGlobalMessage(self.iface, message, level=1, duration=5)

        self.Renders[self.Scenario] = scenario_renders

    def paintIntervalTimeResults(self, setRender=False):
        if not self._statsMode:
            time_text = self.cbTimes.currentText()
            self.lbTime.setText(time_text)
            self.timeTextChanged.emit(time_text)

        for nameLayer in ["Node", "Link"]:
            layer_to_paint = self._findResultLayer(nameLayer)

            if layer_to_paint:
                field = ""
                display_name = ""
                selected_variable_text = ""
                if "Link" in nameLayer:
                    if self.cbLinks.currentIndex() > 0:
                        selected_variable_text = self.cbLinks.currentText()
                        field = self._link_field_map.get(selected_variable_text, "")
                        display_name = self.tr("Link {}").format(selected_variable_text)
                else:
                    if self.cbNodes.currentIndex() > 0:
                        selected_variable_text = self.cbNodes.currentText()
                        field = self._node_field_map.get(selected_variable_text, "")
                        display_name = self.tr("Node {}").format(selected_variable_text)

                if field:
                    self.setGraduatedPalette(layer_to_paint, field, setRender, nameLayer)

                    # Store current displayed variable
                    if "Link" in nameLayer: self.displayingLinkField = field
                    else: self.displayingNodeField = field

                    # Set layer name in legend
                    layer_to_paint.setName(display_name)

                    # Configure map tip
                    is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self.lbl_maximum, self.lbl_minimum)
                    time_field = time_field_name(field, nameLayer) if is_min_max_stat else None
                    if time_field:
                        tip = selected_variable_text + ': [% "' + field + '" || \' - \' || "' + time_field + '" %]'
                    else:
                        tip = selected_variable_text + ': [% "' + field + '" %]'
                    layer_to_paint.setMapTipTemplate(tip)

                    # Configure layer labels
                    self.setLayerLabels(layer_to_paint, field, time_field)

    def setLayerLabels(self, layer, fieldName, time_field=None):
        node_labels_enabled = layer.geometryType() == 0 and self.cbNodeLabels.isChecked()
        link_labels_enabled = layer.geometryType() == 1 and self.cbLinkLabels.isChecked()
        if node_labels_enabled or link_labels_enabled:
            layer_settings = QgsPalLayerSettings()
            layer_settings.formatNumbers = True
            layer_settings.decimals = 2
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 10))
            color = "black"
            text_format.setColor(QColor(color))
            layer_settings.setFormat(text_format)

            if time_field:
                layer_settings.fieldName = f'round("{fieldName}", 2) || \' - \' || "{time_field}"'
                layer_settings.isExpression = True
            elif fieldName == "Flow":
                layer_settings.fieldName = 'abs("Flow")'
                layer_settings.isExpression = True
            else:
                layer_settings.fieldName = fieldName
                layer_settings.isExpression = False

            layer_settings.placement = QgsPalLayerSettings.Line
            layer_settings.enabled = True
            labels = QgsVectorLayerSimpleLabeling(layer_settings)
            layer.setLabeling(labels)
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()

    def setArrowsVisibility(self, symbol, layer, field):
        prop = QgsProperty()
        try:
            if layer.geometryType() == 1 and self.cbFlowDirections.isChecked():
                # Show arrows in pipes
                arrow_symbol_layer = symbol.symbolLayer(3)  # arrow positive flow
                prop.setExpressionString("if(Type='PIPE', if(" + field + ">0,3,0),0)")
                arrow_symbol_layer.subSymbol().setDataDefinedSize(prop)
                arrow_symbol_layer = symbol.symbolLayer(4)  # arrow negative flow
                prop.setExpressionString("if(Type='PIPE', if(" + field + "<0,3,0),0)")
                arrow_symbol_layer.subSymbol().setDataDefinedSize(prop)
            else:
                # Hide arrows
                prop.setExpressionString("0")
                symbol.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
                symbol.symbolLayer(4).subSymbol().setDataDefinedSize(prop)
        except:
            self.cbFlowDirections.setChecked(False)
            self.cbFlowDirections.setEnabled(False)

    def setGraduatedPalette(self, layer, field, setRender, nameLayer):
        renderer = layer.renderer()
        db_field_name = field  # column name as stored in the DBF
        qml_field_name = "Flow" if db_field_name in ("Flow_Sig", "Flow_Unsig") else db_field_name
        if field == "Flow":
            field = "abs(" + field + ")"

        is_status = (db_field_name == "Status")
        ranges, hasRender = self._lookupCachedRenderer(layer, db_field_name) if setRender else (None, False)

        utils = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

        # Ensure correct renderer type
        if is_status:
            # Load QML when we have no cached render and the current renderer does not already
            # belong to Status.
            displaying = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
            if not hasRender and displaying != db_field_name:
                qmlName = nameLayer.split("_")[0] + "_" + db_field_name
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()

            if hasRender and isinstance(ranges, QgsRuleBasedRenderer.Rule):
                try:
                    renderer = QgsRuleBasedRenderer(ranges.clone())
                except:
                    message = self.tr("Some issue occurred in the process of applying the style to the layer").format(self.tr(nameLayer))
                    QGISRedUIUtils.showGlobalMessage(self.iface, message, level=1, duration=5)
                    return
        else:
            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer_correct = renderer.classAttribute() == field and len(renderer.ranges()) > 0
            elif isinstance(renderer, QgsRuleBasedRenderer):
                displaying = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
                renderer_correct = (displaying == db_field_name)
            else:
                renderer_correct = False

            if not hasRender and not renderer_correct:
                qmlName = nameLayer.split("_")[0] + "_" + qml_field_name
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()

            if hasRender and isinstance(ranges, list):
                renderer = QgsGraduatedSymbolRenderer(field, ranges)

            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer.setClassAttribute(field)

        # Update arrow visibility
        try:
            flow_field = self._flowDirectionField()
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, flow_field)
        except:
            pass

        layer.setRenderer(renderer)
        QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface).applyNullStyle(layer)

        final_renderer = layer.renderer()
        if isinstance(final_renderer, QgsRuleBasedRenderer):
            final_labels = {c.label() for c in final_renderer.rootRule().children()}
            if not any(_NULL_RULE_LABEL in lbl for lbl in final_labels):
                if isinstance(layer.legend(), _NullHiddenLegend):
                    layer.setLegend(_NullHiddenLegend(layer))

        layer.triggerRepaint()

        # It does not work in QGIS 4 (no other option found)
        node = QgsProject.instance().layerTreeRoot().findLayer(layer)
        if node and not node.isExpanded():
            node.setExpanded(True)
