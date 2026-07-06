# -*- coding: utf-8 -*-
from contextlib import suppress
import re

from qgis.core import (
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat,
    QgsProperty, QgsRenderContext,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer, QgsRendererRange,
    QgsProject, Qgis, QgsSymbolLayer,
)
from qgis.PyQt.QtGui import QColor, QFont

from ...tools.utils.qgisred_styling_utils import QGISRedStylingUtils, _NULL_RULE_LABEL, _NullHiddenLegend
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils

# Compatibility shims for QgsSymbolLayer property enums (may be scoped in QGIS 4.x)
try:
    _SL_PROP_SIZE = QgsSymbolLayer.PropertySize
except AttributeError:
    try:
        _SL_PROP_SIZE = QgsSymbolLayer.Property.Size
    except AttributeError:
        _SL_PROP_SIZE = 9  # historical fallback

try:
    _SL_PROP_STROKE_WIDTH = QgsSymbolLayer.PropertyStrokeWidth
except AttributeError:
    try:
        _SL_PROP_STROKE_WIDTH = QgsSymbolLayer.Property.StrokeWidth
    except AttributeError:
        _SL_PROP_STROKE_WIDTH = 6  # historical fallback

try:
    _SL_PROP_STROKE_COLOR = QgsSymbolLayer.PropertyStrokeColor
except AttributeError:
    try:
        _SL_PROP_STROKE_COLOR = QgsSymbolLayer.Property.StrokeColor
    except AttributeError:
        _SL_PROP_STROKE_COLOR = 4  # historical fallback

# Base sizes from the node and link result QML files. These are the values when factor = 1.0.
_BASE_PIPE_WIDTH       = 0.26  # mm — SimpleLine width in LinkFlow.qml (and other link styles)
_BASE_ARROW_SIZE       = 3.0   # mm — arrow sub-symbol in setArrowsVisibility
_BASE_JUNCTION_SIZE    = 2.0   # mm — SimpleMarker for junctions in NodePressure.qml
_BASE_SPECIAL_SIZE     = 7.0   # mm — SvgMarker for tanks/reservoirs in NodePressure.qml
_BASE_VALVE_PUMP_SIZE  = 6.0   # mm — SvgMarker for pumps/valves in LinkFlow.qml (indices 1, 2)


def _build_node_size_expr(expr, junction_str, special_str):
    """Build a node symbol-layer size expression from type keywords in expr.

    junction_str / special_str can be a plain number ("2.0") or any QGIS expression
    string (e.g. 'scale_linear(...)').  The result is always rebuilt from scratch so
    it is correct regardless of whether expr is already a scale_linear call or an
    absolute-size expression.
    """
    s = expr.strip()
    has_tank = "'TANK'" in s
    has_res  = "'RESERVOIR'" in s
    if has_tank and not has_res:
        return f"if(Type ='TANK', {special_str}, 0)"
    if has_res and not has_tank:
        return f"if(Type ='RESERVOIR', {special_str}, 0)"
    if has_tank and has_res:
        return f"if(Type ='RESERVOIR' or Type='TANK', 0, {junction_str})"
    return junction_str


def _apply_proportional_node_size(expr, field, field_min, field_max, junction_size, special_size):
    """Build a scale_linear expression for a node symbol layer in proportional mode.

    The factor size is the floor (minimum actual value → factor size).
    The maximum actual value gets 2 × factor size, so nodes remain proportional
    without becoming excessively large.
    Falls back to absolute sizes when the range is degenerate (min == max).
    """
    fmin = round(field_min, 6)
    fmax = round(field_max, 6)
    if fmin == fmax:
        return _build_node_size_expr(expr, str(junction_size), str(special_size))
    j_max = round(junction_size * 2, 6)
    s_max = round(special_size  * 2, 6)
    scale_j = f'scale_linear("{field}", {fmin}, {fmax}, {junction_size}, {j_max})'
    scale_s = f'scale_linear("{field}", {fmin}, {fmax}, {special_size}, {s_max})'
    return _build_node_size_expr(expr, scale_j, scale_s)


def _apply_absolute_node_size(expr, junction_size, special_size):
    """Rewrite a node symbol-layer size expression with absolute target sizes.

    Recognises the three patterns used in node result QML files:
      Tank:       if(Type ='TANK', N, 0)                        → N = special_size
      Reservoir:  if(Type ='RESERVOIR', N, 0)                   → N = special_size
      Junction:   if(Type ='RESERVOIR' or Type='TANK', 0, N)    → N = junction_size
    The replacement is always absolute (not relative to the current N), so calling
    this function repeatedly with the same arguments is idempotent.
    """
    s = expr.strip()
    has_tank = "'TANK'" in s
    has_res  = "'RESERVOIR'" in s
    if has_tank and not has_res:
        # if(Type ='TANK', SIZE, 0)  — replace SIZE before ,0)
        return re.sub(r',\s*\d+(?:\.\d+)?,\s*0\)', f', {special_size},0)', s)
    if has_res and not has_tank:
        # if(Type ='RESERVOIR', SIZE, 0)  — same pattern
        return re.sub(r',\s*\d+(?:\.\d+)?,\s*0\)', f', {special_size},0)', s)
    if has_tank and has_res:
        # if(Type ='RESERVOIR' or Type='TANK', 0, SIZE)  — replace SIZE at end
        return re.sub(r',\s*\d+(?:\.\d+)?\s*\)$', f',{junction_size})', s)
    return s


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
                message = self.tr("Some issue occurred in the process of saving the style of the layer %1").replace("%1", self.tr(nameLayer))
                QGISRedUIUtils.showGlobalMessage(self.iface, message, level=1, duration=5)

        self.Renders[self.Scenario] = scenario_renders

    def paintIntervalTimeResults(self, setRender=False):
        if not self._statsMode:
            idx = self.cbTimes.currentIndex()
            elapsed_text = (
                self.TimeLabels[idx]
                if hasattr(self, "TimeLabels") and 0 <= idx < len(self.TimeLabels)
                else self.cbTimes.currentText()
            )
            self._updateCivilDisplay(elapsed_text)
            self.timeTextChanged.emit(elapsed_text)

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
                        display_name = self.tr("Link %1").replace("%1", selected_variable_text)
                else:
                    if self.cbNodes.currentIndex() > 0:
                        selected_variable_text = self.cbNodes.currentText()
                        field = self._node_field_map.get(selected_variable_text, "")
                        display_name = self.tr("Node %1").replace("%1", selected_variable_text)

                if field:
                    if not setRender:
                        # Time-only change: renderer and style are already correct, just repaint
                        layer_to_paint.triggerRepaint()
                        continue

                    # Store BEFORE setGraduatedPalette so applySymbolScaleFactors
                    # picks up the correct field name when in proportional mode.
                    if "Link" in nameLayer: self.displayingLinkField = field
                    else: self.displayingNodeField = field

                    self.setGraduatedPalette(layer_to_paint, field, setRender, nameLayer)

                    # Persist variable in the QGIS project so updateMetadata can read it.
                    # Storing on the layer itself is unreliable because orderResultLayers
                    # clones Link layers and clone() does not copy custom properties.
                    layer_type = "Link" if "Link" in nameLayer else "Node"
                    QgsProject.instance().writeEntry("QGISRed", f"results_{self.Scenario}_{layer_type}", field)

                    # Set layer name in legend
                    layer_to_paint.setName(display_name)

                    # Configure map tip
                    is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self.lbl_maximum, self.lbl_minimum)
                    time_field = time_field_name(field, nameLayer) if is_min_max_stat else None

                    element = "Nodes" if "Node" in nameLayer else "Links"
                    unit_field = "Flow" if field in ("Flow_Sig", "Flow_Unsig") else field
                    unit = QGISRedFieldUtils().getUnitAbbreviation(element, unit_field)
                    unit_suffix = " " + unit if unit else ""

                    value_expr = 'abs("Flow")' if field == "Flow" else '"' + field + '"'

                    if self._statsMode and time_field:
                        time_expr = '"' + time_field + '"'
                    elif not self._statsMode:
                        time_expr = '"Time"'
                    else:
                        time_expr = None

                    _TYPE_KEYS = ["JUNCTION", "RESERVOIR", "TANK", "PIPE", "PUMP", "VALVE"]
                    cases = " ".join(
                        "WHEN \"Type\" = '" + k + "' THEN '" + self.tr(k.title()) + "'"
                        for k in _TYPE_KEYS
                    )
                    type_id_expr = '[% (CASE ' + cases + ' ELSE "Type" END) || \' \' || "Id" %]'

                    tip_lines = ['<b>' + selected_variable_text + '</b>', type_id_expr]
                    if time_expr:
                        tip_lines.append('[% ' + time_expr + ' %]')
                    tip_lines.append('[% ' + value_expr + ' %]' + unit_suffix)
                    layer_to_paint.setMapTipTemplate('<br>'.join(tip_lines))

                    # Configure layer labels
                    self.setLayerLabels(layer_to_paint, field, time_field)

        if hasattr(self, "_refreshDistributionChartsIfNeeded"):
            self._refreshDistributionChartsIfNeeded()
        if hasattr(self, "_updateEvolutionCheckboxLabels"):
            self._updateEvolutionCheckboxLabels()

    def setLayerLabels(self, layer, fieldName, time_field=None):
        node_labels_enabled = layer.geometryType() == 0 and self.cbNodeLabels.isChecked()
        link_labels_enabled = layer.geometryType() == 1 and self.cbLinkLabels.isChecked()
        if not (node_labels_enabled or link_labels_enabled):
            return

        font_size = getattr(self, '_labelFontSize', 10)
        is_node = layer.geometryType() == 0
        sp = getattr(self, 'spNodeDecimals' if is_node else 'spLinkDecimals', None)
        decimals = sp.value() if sp else 2
        color_by_range = getattr(self, '_labelColorByRange', False)
        show_id = getattr(self, '_labelShowId', False)

        layer_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()
        text_format.setFont(QFont("Arial"))
        text_format.setSize(font_size)
        try:
            text_format.setSizeUnit(Qgis.RenderUnit.RenderPoints)
        except AttributeError:
            from qgis.core import QgsUnitTypes
            text_format.setSizeUnit(QgsUnitTypes.RenderPoints)

        text_format.setColor(QColor("black"))
        if color_by_range:
            color_expr = self._buildRangeColorExpression(layer, fieldName)
            if color_expr:
                from qgis.core import QgsPropertyCollection
                prop = QgsProperty.fromExpression(color_expr)
                ddp = QgsPropertyCollection()
                ddp.setProperty(QgsPalLayerSettings.Color, prop)
                layer_settings.setDataDefinedProperties(ddp)

        layer_settings.setFormat(text_format)

        # Build value expression — format_number ensures fixed decimal places (respects locale)
        if time_field:
            value_expr = f'format_number(round("{fieldName}", {decimals}), {decimals}) || \' - \' || "{time_field}"'
        elif fieldName == "Flow":
            value_expr = f'format_number(abs("Flow"), {decimals})'
        else:
            value_expr = f'format_number("{fieldName}", {decimals})'

        if show_id:
            element = "Nodes" if is_node else "Links"
            unit_field = "Flow" if fieldName in ("Flow_Sig", "Flow_Unsig") else fieldName
            unit = QGISRedFieldUtils().getUnitAbbreviation(element, unit_field)
            unit_suffix = f' || \' {unit}\'' if unit else ''

            _TYPE_KEYS = ["JUNCTION", "RESERVOIR", "TANK", "PIPE", "PUMP", "VALVE"]
            cases = " ".join(
                f"WHEN \"Type\" = '{k}' THEN '{self.tr(k.title())}'"
                for k in _TYPE_KEYS
            )
            line1 = f'(CASE {cases} ELSE "Type" END) || \' \' || "Id"'

            if time_field:
                raw_val = f'format_number(round("{fieldName}", {decimals}), {decimals})'
                line2 = f'{raw_val}{unit_suffix} || \' - \' || "{time_field}"'
            elif fieldName == "Flow":
                line2 = f'format_number(abs("Flow"), {decimals}){unit_suffix}'
            else:
                line2 = f'format_number("{fieldName}", {decimals}){unit_suffix}'

            full_expr = f'({line1}) || \'\\n\' || ({line2})'
        else:
            full_expr = value_expr

        layer_settings.fieldName = full_expr
        layer_settings.isExpression = True
        layer_settings.placement = QgsPalLayerSettings.Line
        layer_settings.enabled = True
        labels = QgsVectorLayerSimpleLabeling(layer_settings)
        layer.setLabeling(labels)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    def _buildRangeColorExpression(self, layer, fieldName):
        """Build a CASE WHEN expression to color label text matching the graduated renderer ranges."""
        renderer = layer.renderer()
        # applyNullStyle wraps graduated renderers in QgsRuleBasedRenderer;
        # extract the embedded graduated renderer from child rules when needed.
        if isinstance(renderer, QgsRuleBasedRenderer):
            return self._buildRangeColorExpressionFromRules(renderer, fieldName)
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return None
        return self._buildRangeColorExpressionFromGraduated(renderer, fieldName)

    def _buildRangeColorExpressionFromGraduated(self, renderer, fieldName):
        actual_field = 'abs("Flow")' if fieldName == "Flow" else f'"{fieldName}"'
        parts = []
        for r in renderer.ranges():
            hex_color = r.symbol().color().name()
            lo, hi = r.lowerValue(), r.upperValue()
            parts.append(
                f'WHEN {actual_field} >= {lo} AND {actual_field} <= {hi} THEN \'{hex_color}\''
            )
        if not parts:
            return None
        return 'CASE ' + ' '.join(parts) + ' ELSE \'#000000\' END'

    def _buildRangeColorExpressionFromRules(self, renderer, fieldName):
        """Build color expression from QgsRuleBasedRenderer child rules (post applyNullStyle)."""
        actual_field = 'abs("Flow")' if fieldName == "Flow" else f'"{fieldName}"'
        parts = []
        for rule in renderer.rootRule().children():
            if rule.label() == _NULL_RULE_LABEL:
                continue
            sym = rule.symbol()
            if sym is None:
                continue
            hex_color = sym.color().name()
            # applyNullStyle uses ">=" for i==0 and ">" for all subsequent ranges.
            # Match both forms to extract lo/hi bounds.
            expr = rule.filterExpression()
            m = re.search(r'>=? *([\d.eE+\-]+).*?<= *([\d.eE+\-]+)', expr or "")
            if m:
                lo, hi = m.group(1), m.group(2)
                parts.append(
                    f'WHEN {actual_field} >= {lo} AND {actual_field} <= {hi} THEN \'{hex_color}\''
                )
        if not parts:
            return None
        return 'CASE ' + ' '.join(parts) + ' ELSE \'#000000\' END'

    def applySymbolScaleFactors(self, layer):
        """Apply Appearance-tab factors to result layer symbols using absolute target sizes.

        When _proportional is True, sizes scale with the displayed field value using
        scale_linear expressions; the factor still controls the maximum size.
        Sizes are always computed as BASE_SIZE × factor, so repeated calls with the same
        arguments are idempotent and no state about the previous call needs to be tracked.
        """
        is_line  = layer.geometryType() == 1
        is_point = layer.geometryType() == 0
        if not is_line and not is_point:
            return

        pipe_factor   = getattr(self, '_pipeFactor',   1.0)
        symbol_factor = getattr(self, '_symbolFactor', 1.0)
        arrow_factor  = getattr(self, '_arrowFactor',  1.0)

        target_pipe_width  = round(_BASE_PIPE_WIDTH      * pipe_factor,   6)
        target_arrow_size  = round(_BASE_ARROW_SIZE      * arrow_factor,  6)
        target_junction    = round(_BASE_JUNCTION_SIZE   * symbol_factor, 6)
        target_special     = round(_BASE_SPECIAL_SIZE    * symbol_factor, 6)
        target_valve_pump  = round(_BASE_VALVE_PUMP_SIZE * pipe_factor, 6)

        proportional = getattr(self, '_proportional', False)
        field = (self.displayingNodeField if is_point else self.displayingLinkField) or ""
        can_be_proportional = proportional and bool(field) and field != "Status"

        # Pre-compute field range once (used by all rules in the loop).
        prop_field_min = prop_field_max = prop_field_max_abs = 0.0
        if can_be_proportional:
            try:
                field_idx = layer.fields().indexOf(field)
                if field_idx >= 0:
                    prop_field_min = layer.minimumValue(field_idx) or 0.0
                    prop_field_max = layer.maximumValue(field_idx) or 0.0
                    prop_field_max_abs = max(abs(prop_field_min), abs(prop_field_max))
                else:
                    can_be_proportional = False
            except Exception:
                can_be_proportional = False

        renderer = layer.renderer()
        if not isinstance(renderer, QgsRuleBasedRenderer):
            return  # result layers are always rule-based after applyNullStyle

        new_renderer = renderer.clone()
        for rule in new_renderer.rootRule().children():
            sym = rule.symbol()
            if sym is None:
                continue
            if is_line:
                # Pipe width — direct absolute assignment
                sym.setWidth(target_pipe_width)
                # Proportional pipe width via data-defined property on the main line symbol layer.
                sl0 = sym.symbolLayer(0)
                if sl0 is not None:
                    with suppress(Exception):
                        if can_be_proportional and prop_field_max_abs > 0:
                            pipe_max = round(target_pipe_width * 4, 6)
                            prop_expr = (
                                f'scale_linear(abs("{field}"), 0, {prop_field_max_abs},'
                                f' {target_pipe_width}, {pipe_max})'
                            )
                            sl0.setDataDefinedProperty(
                                _SL_PROP_STROKE_WIDTH,
                                QgsProperty.fromExpression(prop_expr))
                        else:
                            sl0.setDataDefinedProperty(
                                _SL_PROP_STROKE_WIDTH, QgsProperty())
                # Pump/valve SVG icon sizes (MarkerLine at indices 1, 2).
                # Scale with pipe_factor since they are link elements.
                for icon_idx in (1, 2):
                    with suppress(Exception):
                        sl = sym.symbolLayer(icon_idx)
                        if sl is None:
                            continue
                        sub = sl.subSymbol()
                        if sub is None:
                            continue
                        # Mechanism A: sub-symbol data-defined size
                        dd = sub.dataDefinedSize()
                        if dd.isActive():
                            old_expr = dd.expressionString()
                            new_expr = re.sub(r',\s*\d+(?:\.\d+)?,\s*0\)', f',{target_valve_pump},0)', old_expr)
                            if new_expr != old_expr:
                                sub.setDataDefinedSize(QgsProperty.fromExpression(new_expr))
                        # Mechanism B: SvgMarker layer data-defined property
                        svg_sl = sub.symbolLayer(0)
                        if svg_sl is not None:
                            ddp = svg_sl.dataDefinedProperties()
                            sp = ddp.property(0)
                            if sp.isActive():
                                old_expr = sp.expressionString()
                                new_expr = re.sub(r',\s*\d+(?:\.\d+)?,\s*0\)', f',{target_valve_pump},0)', old_expr)
                                if new_expr != old_expr:
                                    ddp.setProperty(0, QgsProperty.fromExpression(new_expr))
                                    svg_sl.setDataDefinedProperties(ddp)
                # Arrow sizes — absolute replacement in the data-defined expression
                for arrow_idx in (3, 4):
                    with suppress(Exception):
                        sl = sym.symbolLayer(arrow_idx)
                        if sl is None:
                            continue
                        sub = sl.subSymbol()
                        if sub is None:
                            continue
                        size_prop = sub.dataDefinedSize()
                        if not size_prop.isActive():
                            continue
                        old_expr = size_prop.expressionString()
                        # Replace any existing size constant with target_arrow_size.
                        # Pattern matches ",N,0)" in "if(Type='PIPE', if(Flow>0,N,0),0)".
                        new_expr = re.sub(
                            r',\s*\d+(?:\.\d+)?,\s*0\)',
                            f',{target_arrow_size},0)',
                            old_expr,
                        )
                        if new_expr != old_expr:
                            sub.setDataDefinedSize(QgsProperty.fromExpression(new_expr))
            elif is_point:
                # Node sizes are set via data-defined expressions on each symbol layer.
                # sym.setSize() has no effect because those expressions override it.
                node_border = getattr(self, '_nodeBorder', False)
                for sl_idx in range(sym.symbolLayerCount()):
                    with suppress(Exception):
                        sl = sym.symbolLayer(sl_idx)
                        if sl is None:
                            continue
                        ddp = sl.dataDefinedProperties()
                        size_prop = ddp.property(_SL_PROP_SIZE)
                        if size_prop.isActive():
                            old_expr = size_prop.expressionString()
                            if can_be_proportional:
                                new_expr = _apply_proportional_node_size(
                                    old_expr, field,
                                    prop_field_min, prop_field_max,
                                    target_junction, target_special)
                            else:
                                new_expr = _build_node_size_expr(
                                    old_expr, str(target_junction), str(target_special))
                            if new_expr != old_expr:
                                ddp.setProperty(_SL_PROP_SIZE, QgsProperty.fromExpression(new_expr))
                                sl.setDataDefinedProperties(ddp)
                        # Border: use data-defined properties (works for both SvgMarker and
                        # SimpleMarker without relying on hasattr, same mechanism as pipe width).
                        # Tank QML has white outline_color so we must also force the color.
                        # SVG markers (7 mm symbols) use a thicker border than SimpleMarker (2 mm).
                        with suppress(Exception):
                            if node_border:
                                is_svg = 'Svg' in type(sl).__name__
                                width_expr = "1.0" if is_svg else "0.6"
                                sl.setDataDefinedProperty(
                                    _SL_PROP_STROKE_WIDTH,
                                    QgsProperty.fromExpression(width_expr))
                                sl.setDataDefinedProperty(
                                    _SL_PROP_STROKE_COLOR,
                                    QgsProperty.fromExpression("'#000000'"))
                            else:
                                sl.setDataDefinedProperty(
                                    _SL_PROP_STROKE_WIDTH, QgsProperty())
                                sl.setDataDefinedProperty(
                                    _SL_PROP_STROKE_COLOR, QgsProperty())

        layer.setRenderer(new_renderer)
        layer.triggerRepaint()
        if hasattr(self, 'iface') and self.iface:
            self.iface.mapCanvas().refresh()

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
                utils.setStyle(layer, qmlName)
                renderer = layer.renderer()

            if hasRender and isinstance(ranges, QgsRuleBasedRenderer.Rule):
                try:
                    renderer = QgsRuleBasedRenderer(ranges.clone())
                except:
                    message = self.tr("Some issue occurred in the process of applying the style to the layer %1").replace("%1", self.tr(nameLayer))
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
                utils.setStyle(layer, qmlName)
                renderer = layer.renderer()

            if hasRender and isinstance(ranges, list):
                renderer = QgsGraduatedSymbolRenderer(field, ranges)

            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer.setClassAttribute(field)

        # Update arrow visibility
        with suppress(Exception):
            flow_field = self._flowDirectionField()
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, flow_field)

        layer.setRenderer(renderer)
        QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface).applyNullStyle(layer)

        final_renderer = layer.renderer()
        if isinstance(final_renderer, QgsRuleBasedRenderer):
            final_labels = {c.label() for c in final_renderer.rootRule().children()}
            if not any(_NULL_RULE_LABEL in lbl for lbl in final_labels):
                if isinstance(layer.legend(), _NullHiddenLegend):
                    layer.setLegend(_NullHiddenLegend(layer))

        self.applySymbolScaleFactors(layer)
        layer.triggerRepaint()

        # It does not work in QGIS 4 (no other option found)
        node = QgsProject.instance().layerTreeRoot().findLayer(layer)
        if node and not node.isExpanded():
            node.setExpanded(True)
