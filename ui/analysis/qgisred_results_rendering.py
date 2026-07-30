# -*- coding: utf-8 -*-
from contextlib import contextmanager, suppress
import re

from qgis.core import (
    QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat,
    QgsTextBackgroundSettings,
    QgsProperty, QgsRenderContext,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer,
    QgsProject, QgsMessageLog,
)
from qgis.PyQt.QtCore import QSizeF
from qgis.PyQt.QtGui import QColor, QFont

from ...compat import (
    RENDER_UNIT_POINTS, RENDER_UNIT_MILLIMETERS,
    TEXT_BG_SHAPE_RECTANGLE, TEXT_BG_SIZE_BUFFER,
    PAL_PROPERTY_COLOR, PAL_PROPERTY_LABEL_DISTANCE,
    PAL_PLACEMENT_LINE, PAL_PLACEMENT_AROUND_POINT,
    SL_PROP_SIZE, SL_PROP_STROKE_COLOR, SL_PROP_STROKE_WIDTH,
    QGIS_WARNING,
)
from ...tools.utils.qgisred_styling_utils import QGISRedStylingUtils, _NULL_RULE_LABEL, _NullHiddenLegend
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ...tools.utils.qgisred_result_fields import resultIdField, resultTypeField
from .qgisred_results_data import resultStyleName

# Default label text colors (used unless the user picks "By range" or overrides them in
# Appearance). Dark tones close to black so labels stay legible, but distinguishable
# between element types: nodes in dark gray, links in dark navy blue.
_DEFAULT_NODE_LABEL_COLOR = QColor(51, 51, 51)
_DEFAULT_LINK_LABEL_COLOR = QColor(10, 20, 60)

# Base sizes from the node and link result QML files. These are the values when factor = 1.0.
_BASE_PIPE_WIDTH       = 0.26  # mm — SimpleLine width in LinkFlow.qml (and other link styles)
_BASE_ARROW_SIZE       = 3.0   # mm — arrow sub-symbol in setArrowsVisibility
_BASE_JUNCTION_SIZE    = 2.0   # mm — SimpleMarker for junctions in NodePressure.qml
_BASE_SPECIAL_SIZE     = 7.0   # mm — SvgMarker for tanks/reservoirs in NodePressure.qml
_BASE_VALVE_PUMP_SIZE  = 6.0   # mm — SvgMarker for pumps/valves in LinkFlow.qml (indices 1, 2)

# Label separation (mm) from the geometry it belongs to. The link label is pushed out far
# enough that its (optionally opaque) background never overlaps the symbol drawn on the
# line: half the symbol's perpendicular extent + a clearance margin. Pumps and valves get
# a larger distance than pipes because their SVG icon is much bigger than a flow arrow.
_LABEL_CLEARANCE       = 1.0   # mm — gap between the symbol edge and the label box
_LABEL_BG_BUFFER       = 1.0   # mm — must match the QgsTextBackgroundSettings buffer size


def _build_node_size_expr(expr, junction_str, special_str, type_field="Type"):
    """Build a node symbol-layer size expression from type keywords in expr.

    junction_str / special_str can be a plain number ("2.0") or any QGIS expression
    string (e.g. 'scale_linear(...)').  The result is always rebuilt from scratch so
    it is correct regardless of whether expr is already a scale_linear call or an
    absolute-size expression.
    ``type_field`` is the layer's element-type column: NodeType on layers written by a
    recent DLL, Type on projects simulated before the rename.
    """
    s = expr.strip()
    has_tank = "'TANK'" in s
    has_res  = "'RESERVOIR'" in s
    t = f'"{type_field}"'
    if has_tank and not has_res:
        return f"if({t} ='TANK', {special_str}, 0)"
    if has_res and not has_tank:
        return f"if({t} ='RESERVOIR', {special_str}, 0)"
    if has_tank and has_res:
        return f"if({t} ='RESERVOIR' or {t}='TANK', 0, {junction_str})"
    return junction_str


def _apply_proportional_node_size(expr, field, field_min, field_max, junction_size, special_size,
                                  type_field="Type"):
    """Build a scale_linear expression for a node symbol layer in proportional mode.

    The factor size is the floor (minimum actual value → factor size).
    The maximum actual value gets 2 × factor size, so nodes remain proportional
    without becoming excessively large.
    Falls back to absolute sizes when the range is degenerate (min == max).
    """
    fmin = round(field_min, 6)
    fmax = round(field_max, 6)
    if fmin == fmax:
        return _build_node_size_expr(expr, str(junction_size), str(special_size), type_field)
    j_max = round(junction_size * 2, 6)
    s_max = round(special_size  * 2, 6)
    scale_j = f'scale_linear("{field}", {fmin}, {fmax}, {junction_size}, {j_max})'
    scale_s = f'scale_linear("{field}", {fmin}, {fmax}, {special_size}, {s_max})'
    return _build_node_size_expr(expr, scale_j, scale_s, type_field)


def _apply_absolute_node_size(expr, junction_size, special_size):
    """Rewrite a node symbol-layer size expression with absolute target sizes.

    Recognises the three patterns used in node result QML files:
      Tank:       if(Type ='TANK', N, 0)                        → N = special_size
      Reservoir:  if(Type ='RESERVOIR', N, 0)                   → N = special_size
      Junction:   if(Type ='RESERVOIR' or Type='TANK', 0, N)    → N = junction_size
    The type column may equally be NodeType or a coalesce() over both names; only the
    'TANK'/'RESERVOIR' literals and the trailing size constant are matched.
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


# Readers for the sizes the writers above put into symbol expressions. They live next to
# them so both halves stay in step: every pattern written by _build_node_size_expr or by
# the re.sub calls in applySymbolScaleFactors has a reader here.
_SIZE_BEFORE_ZERO = re.compile(r',\s*(\d+(?:\.\d+)?)\s*,\s*0\)')
_SIZE_AT_END = re.compile(r',\s*(\d+(?:\.\d+)?)\s*\)\s*$')


def _read_size_before_zero(expr):
    """Size in ", N, 0)" — how tanks, reservoirs, pump/valve icons and arrows carry theirs."""
    match = _SIZE_BEFORE_ZERO.search(expr or "")
    return float(match.group(1)) if match else None


def read_node_base_sizes(expr):
    """(junction, special) sizes held by a node size expression; either may be None.

    Mirrors _build_node_size_expr: the tank-only and reservoir-only forms carry the special
    size before ", 0)", while the combined form carries the junction size last. Anything
    else — a scale_linear from proportional mode, say — yields nothing rather than a guess.
    """
    s = (expr or "").strip()
    has_tank = "'TANK'" in s
    has_res = "'RESERVOIR'" in s
    if has_tank and has_res:
        match = _SIZE_AT_END.search(s)
        return (float(match.group(1)) if match else None), None
    if has_tank or has_res:
        return None, _read_size_before_zero(s)
    with suppress(ValueError):
        return float(s), None
    return None, None


def apply_junction_size(expr, junction_size):
    """Set the junction size in a node size expression, leaving tanks and reservoirs alone.

    For the legend editor, whose single Size column edits the marker drawn for junctions:
    the tank and reservoir size lives in its own expression and has its own Appearance
    factor, so an expression carrying that one is returned untouched. Anything unrecognised
    is left alone too, rather than overwritten with a number that may not belong there.
    """
    s = (expr or "").strip()
    has_tank = "'TANK'" in s
    has_res = "'RESERVOIR'" in s
    if has_tank and has_res:
        return _SIZE_AT_END.sub(f", {junction_size})", s)
    if has_tank or has_res:
        return s
    with suppress(ValueError):
        float(s)
        return str(junction_size)
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

    # Text color for each magnitude label, keyed by internal field name (stable
    # across languages) so the user can identify the displayed variable by color.
    _MAGNITUDE_COLORS = {
        # Nodes
        "Pressure": "#2f8f5b",    # verde esmeralda (presión; el verde con más contraste)
        "Head": "#b5981f",        # ocre/ámbar (más oscuro e intenso que el ocre previo)
        "Demand": "#67add9",      # azul claro (distinto del azul de Flow)
        "Quality": "#8d5a99",     # morado (calidad en nudos)
        # Links
        "Flow": "#1f78b4",        # azul
        "Flow_Unsig": "#1f78b4",  # azul
        "Flow_Sig": "#1f78b4",    # azul
        "Velocity": "#e17da2",    # magenta
        "HeadLoss": "#729b6f",    # verde apagado (pérdidas totales; distinto de presión y de Head)
        "UnitHdLoss": "#becf50",  # verde claro (pérdidas unitarias)
        "FricFactor": "#52828f",  # gris
        "Status": "#e77148",      # naranja
        "ReactRate": "#e8718d",   # rosa
    }
    # Overrides applied only to link layers for field names shared with nodes, so the
    # link variant is distinguishable when both element types show the same magnitude
    # (e.g. quality on nodes and on links at the same time).
    _MAGNITUDE_LINK_COLORS = {
        "Quality": "#b18ec9",     # violeta claro (calidad en líneas; distinto del morado de nudos)
    }
    _MAGNITUDE_DEFAULT_COLOR = "#000000"

    # The most used magnitudes: their labels are drawn in bold so they stand out from the
    # rest, whatever color they end up with (fixed magnitude color or colored by range).
    _BOLD_NODE_FIELDS = ("Head", "Pressure", "Quality")
    _BOLD_LINK_FIELDS = ("Flow", "Flow_Sig", "Flow_Unsig")

    def _magnitudeColor(self, field, is_node):
        """Return the label color (hex string) for a magnitude, or None if the field has
        no assigned color. Link layers get the link-specific override when one exists for
        a field name shared with nodes."""
        if not is_node:
            override = self._MAGNITUDE_LINK_COLORS.get(field)
            if override:
                return override
        return self._MAGNITUDE_COLORS.get(field)

    def _isBoldMagnitude(self, field, is_node):
        """True when the magnitude is one of the most used ones (heads, pressures and
        quality on nodes; flow on links), whose labels are highlighted in bold."""
        return field in (self._BOLD_NODE_FIELDS if is_node else self._BOLD_LINK_FIELDS)

    # Renderer types worth remembering. A result layer only ever shows a single symbol
    # while it is being opened, before any style reaches it, and caching that would
    # overwrite a real entry with an empty one.
    _CACHEABLE_RENDERERS = ("graduatedSymbol", "RuleRenderer", "categorizedSymbol")

    def _getRenderStorageKey(self, layer_path, var_key):
        """Build the cache key used to store/retrieve a renderer for a given layer and variable."""
        prefix = f"stat_{self._currentStat}|" if self._statsMode else "time|"
        return f"{prefix}{layer_path}|{var_key}"

    def _lookupCachedRenderer(self, layer, db_field_name):
        """Renderer remembered for this layer and variable, already cloned, or None."""
        cached = self.Renders.get(
            self._getRenderStorageKey(self.getLayerPath(layer), db_field_name))
        if cached is None:
            return None
        with suppress(Exception):
            return cached.clone()
        return None

    def rememberCurrentRender(self, layer):
        """Snapshot the renderer about to be replaced, under the key it was applied with.

        Called right before a layer is restyled, which is the one moment its current look
        can be lost — whoever produced it, this dock or the user through the QGIS
        symbology panel. The key comes from what was recorded when that renderer was
        applied, not from the current state: the statistic and the variable have often
        already moved on by the time we get here.
        """
        layer_path = self.getLayerPath(layer)
        storage_key = self._renderKeyInUse.get(layer_path)
        if not storage_key:
            return
        renderer = layer.renderer()
        with suppress(Exception):
            if renderer is not None and renderer.type() in self._CACHEABLE_RENDERERS:
                self.Renders[storage_key] = renderer.clone()

    def forgetRenderKey(self, layer_path):
        """Drop the key bound to a layer that is going away.

        Its path can come back as a brand new layer, and the stale key would make the
        next snapshot store that empty layer over a style the user had built.
        """
        self._renderKeyInUse.pop(layer_path, None)

    def clearRenderCache(self):
        """Forget every remembered renderer. Called when the project changes."""
        self.Renders.clear()
        self._renderKeyInUse.clear()
        self._styleBaseSizes.clear()
        self._watchedLayers.clear()

    # ------------------------------------------------------------------
    # Base sizes: what the style says before any Appearance factor is applied
    # ------------------------------------------------------------------

    # Fallbacks for a style that does not state a size, and for the factory styles this
    # plugin ships, whose numbers these are. Reading the style is what makes a factor of
    # 1.0 mean "leave it as the style drew it" instead of "go back to the values below".
    _FALLBACK_BASE_SIZES = {
        "pipe": _BASE_PIPE_WIDTH,
        "arrow": _BASE_ARROW_SIZE,
        "junction": _BASE_JUNCTION_SIZE,
        "special": _BASE_SPECIAL_SIZE,
        "valvePump": _BASE_VALVE_PUMP_SIZE,
    }

    @staticmethod
    def _readDataDefinedSize(symbol, index):
        """Size carried by the data-defined expression of a sub-symbol, or None."""
        with suppress(Exception):
            symbolLayer = symbol.symbolLayer(index)
            sub = symbolLayer.subSymbol() if symbolLayer is not None else None
            if sub is None:
                return None
            prop = sub.dataDefinedSize()
            if prop.isActive():
                return _read_size_before_zero(prop.expressionString())
        return None

    def readStyleBaseSizes(self, layer, renderer):
        """Sizes the style itself states, read before any factor is written over them.

        Only what is found is returned; applySymbolScaleFactors fills the rest from
        _FALLBACK_BASE_SIZES. Must run on a renderer straight from the style file — one
        restored from the render cache already carries the factors baked in, and taking
        that as the base would multiply them again on every pass.
        """
        sizes = {}
        symbols = None
        with suppress(Exception):
            symbols = renderer.symbols(QgsRenderContext())
        if not symbols:
            return sizes
        symbol = symbols[0]

        if layer.geometryType() == 1:
            with suppress(Exception):
                symbolLayer = symbol.symbolLayer(0)
                if symbolLayer is not None and hasattr(symbolLayer, "width"):
                    sizes["pipe"] = symbolLayer.width()
            for index in (1, 2):
                size = self._readDataDefinedSize(symbol, index)
                if size is not None:
                    sizes["valvePump"] = size
                    break
            for index in (3, 4):
                size = self._readDataDefinedSize(symbol, index)
                if size is not None:
                    sizes["arrow"] = size
                    break
        elif layer.geometryType() == 0:
            for index in range(symbol.symbolLayerCount()):
                with suppress(Exception):
                    symbolLayer = symbol.symbolLayer(index)
                    prop = symbolLayer.dataDefinedProperties().property(SL_PROP_SIZE)
                    if not prop.isActive():
                        continue
                    junction, special = read_node_base_sizes(prop.expressionString())
                    if junction is not None:
                        sizes["junction"] = junction
                    if special is not None:
                        sizes["special"] = special
        return sizes

    # Which Appearance factor scales each size, for dividing it back out.
    _SIZE_FACTORS = {
        "pipe": "_pipeFactor",
        "arrow": "_arrowFactor",
        "junction": "_symbolFactor",
        "special": "_specialFactor",
        "valvePump": "_valvePumpFactor",
    }

    def rememberStyleBaseSizes(self, layer, variable, renderer, scaled=False):
        """Record the sizes a style states, for this layer and variable.

        Keyed per variable, like the render cache: each one loads its own QML, and a
        hand-made NodeDemand.qml may well state different sizes than NodePressure.qml.

        `scaled` says whether what is being read already went through the Appearance
        factors. A style straight from its file has not — its numbers are the base. A
        renderer the user just edited has, because the editor works on what is drawn, so
        its numbers are base × factor and the factor is divided back out. Getting this
        backwards is what makes symbols grow on every pass.
        """
        sizes = self.readStyleBaseSizes(layer, renderer)
        if scaled:
            sizes = {name: value / factor for name, value, factor in (
                (name, value, getattr(self, self._SIZE_FACTORS[name], 1.0) or 1.0)
                for name, value in sizes.items())}
        if sizes:
            self._styleBaseSizes[self._getRenderStorageKey(self.getLayerPath(layer), variable)] = sizes

    @contextmanager
    def writingOwnStyle(self):
        """Mark our own renderer writes so the watcher does not read them back as a base.

        Counted rather than boolean: applySymbolScaleFactors guards its own write and is
        also called from inside setGraduatedPalette, which guards a wider block.
        """
        self._writingOwnStyle += 1
        try:
            yield
        finally:
            self._writingOwnStyle -= 1

    def watchRendererChanges(self, layer):
        """Follow a result layer's renderer so styles set from outside redefine the base.

        The legend editor and QGIS's own symbology panel both end in setRenderer, and
        neither goes through this dock. Without this, a style set that way would keep being
        scaled against the sizes of the file it replaced.
        """
        layerId = layer.id()
        if layerId in self._watchedLayers:
            return
        with suppress(Exception):
            layer.rendererChanged.connect(lambda lyr=layer: self.onLayerRendererChanged(lyr))
            self._watchedLayers.add(layerId)

    def onLayerRendererChanged(self, layer):
        """Take a renderer set from outside this dock as the new base for its variable."""
        if self._writingOwnStyle:
            return
        layer_path = self.getLayerPath(layer)
        storage_key = self._renderKeyInUse.get(layer_path)
        if not storage_key:
            return
        variable = storage_key.rsplit("|", 1)[-1]
        with suppress(Exception):
            self.rememberStyleBaseSizes(layer, variable, layer.renderer(), scaled=True)

    def baseSizesFor(self, layer):
        """Sizes to scale the Appearance factors against for what this layer shows now."""
        sizes = dict(self._FALLBACK_BASE_SIZES)
        storage_key = self._renderKeyInUse.get(self.getLayerPath(layer))
        if storage_key:
            sizes.update(self._styleBaseSizes.get(storage_key, {}))
        return sizes

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

                    # Captured BEFORE overwriting displaying*Field below, so setGraduatedPalette
                    # can tell whether the variable actually changed (it needs the OLD value).
                    previously_displayed = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField

                    # Store BEFORE setGraduatedPalette so applySymbolScaleFactors
                    # picks up the correct field name when in proportional mode.
                    if "Link" in nameLayer:
                        self.displayingLinkField = field
                    else:
                        self.displayingNodeField = field

                    self.setGraduatedPalette(layer_to_paint, field, setRender, nameLayer, previously_displayed)

                    # Persist variable in the QGIS project so updateMetadata can read it.
                    # Storing on the layer itself is unreliable because orderResultLayers
                    # clones Link layers and clone() does not copy custom properties.
                    layer_type = "Link" if "Link" in nameLayer else "Node"
                    QgsProject.instance().writeEntry("QGISRed", f"results_{self.Scenario}_{layer_type}", field)

                    # Set layer name in legend
                    layer_to_paint.setName(display_name)

                    # Configure map tip
                    time_field = None
                    stat_prefix = ""
                    if self._statsMode:
                        current_stat = self.cbStatistics.currentText()
                        if current_stat in (self.lbl_maximum, self.lbl_minimum):
                            time_field = time_field_name(field, nameLayer)
                        # Prefix the value with the statistic being shown
                        stat_prefix = {
                            self.lbl_maximum: self.tr("Max"),
                            self.lbl_minimum: self.tr("Min"),
                            self.lbl_average: self.tr("Avg"),
                            self.lbl_range: self.tr("Rng"),
                            self.lbl_std_deviation: self.tr("Std"),
                        }.get(current_stat, "")
                        if stat_prefix:
                            stat_prefix += " "

                    element = "Nodes" if "Node" in nameLayer else "Links"
                    unit_field = "Flow" if field in ("Flow_Sig", "Flow_Unsig") else field
                    unit = QGISRedFieldUtils().getUnitAbbreviation(element, unit_field)
                    unit_suffix = " " + unit if unit else ""

                    self._setMagnitudeLabel(nameLayer, selected_variable_text, unit, field)

                    if field == "Flow":
                        value_expr = 'abs("Flow")'
                    elif field == "Status":
                        # The map label groups the states into Closed/Active; the tooltip
                        # shows all 13 as stored. The map tip is HTML, so the comparison
                        # signs in 'Closed (Q<0)' would be read as a tag and swallow the
                        # rest of the line — they have to travel as entities.
                        value_expr = 'replace("Status", array(\'<\', \'>\'), array(\'&lt;\', \'&gt;\'))'
                    else:
                        value_expr = '"' + field + '"'

                    # NodeType/LinkType and NodeID/LinkID on layers written by a recent DLL;
                    # Type/Id on projects that have not been simulated since the rename.
                    type_col = '"' + resultTypeField(layer_to_paint, default="Type") + '"'
                    id_col = '"' + resultIdField(layer_to_paint) + '"'
                    _TYPE_KEYS = ["JUNCTION", "RESERVOIR", "TANK", "PIPE", "PUMP", "VALVE"]
                    cases = " ".join(
                        "WHEN " + type_col + " = '" + k + "' THEN '" + self.tr(k.title()) + "'"
                        for k in _TYPE_KEYS
                    )
                    type_id_expr = '[% (CASE ' + cases + ' ELSE ' + type_col + ' END) || \' \' || ' + id_col + ' %]'

                    tip_lines = ['<b>' + selected_variable_text + '</b>', type_id_expr]
                    tip_lines.append(stat_prefix + '[% ' + value_expr + ' %]' + unit_suffix)
                    if time_field:
                        tip_lines.append('@ [% "' + time_field + '" %]')
                    layer_to_paint.setMapTipTemplate('<br>'.join(tip_lines))

                    # Configure layer labels (occurrence time is shown only in the tooltip)
                    self.setLayerLabels(layer_to_paint, field)

        if hasattr(self, "_refreshDistributionChartsIfNeeded"):
            self._refreshDistributionChartsIfNeeded()
        if hasattr(self, "_updateEvolutionCheckboxLabels"):
            self._updateEvolutionCheckboxLabels()

    def _refreshMagnitudeLabels(self):
        """Set the Nodes/Links magnitude+unit labels from the current combo
        state, without re-rendering. Used on restore, where the combos are
        populated but paintIntervalTimeResults() is not called."""
        for nameLayer in ["Node", "Link"]:
            if "Link" in nameLayer:
                combo, field_map = self.cbLinks, self._link_field_map
                element = "Links"
            else:
                combo, field_map = self.cbNodes, self._node_field_map
                element = "Nodes"

            if combo.currentIndex() <= 0:
                self._setMagnitudeLabel(nameLayer, "", "")
                continue

            selected_variable_text = combo.currentText()
            field = field_map.get(selected_variable_text, "")
            unit = ""
            if field:
                unit_field = "Flow" if field in ("Flow_Sig", "Flow_Unsig") else field
                unit = QGISRedFieldUtils().getUnitAbbreviation(element, unit_field)
            self._setMagnitudeLabel(nameLayer, selected_variable_text, unit, field)

    def _setMagnitudeLabel(self, nameLayer, magnitudeText, unit, field=""):
        """Show the currently displayed magnitude (bold, in its own color) and its
        unit (smaller, not bold, in parentheses) next to the Nodes/Links header.
        The color is keyed by field name so the user can identify the variable by color."""
        label = self.lbNodesMagnitude if "Node" in nameLayer else self.lbLinksMagnitude
        if not magnitudeText:
            label.setText("")
            return
        color = self._magnitudeColor(field, "Node" in nameLayer) or self._MAGNITUDE_DEFAULT_COLOR
        text = f'<span style="font-size:12pt; font-weight:bold; color:{color};">{magnitudeText}</span>'
        if unit:
            text += f' <span style="font-size:10pt; font-weight:normal; color:{color};">({unit})</span>'
        label.setText(text)

    def setLayerLabels(self, layer, fieldName):
        is_node = layer.geometryType() == 0
        is_link = layer.geometryType() == 1
        if not (is_node or is_link):
            return

        # The label content is split across the two tabs: the *value* is toggled from the
        # Results tab (label checkbox + a selected variable) and the *Id* from the Appearance
        # tab (Show Node/Link ID). Any combination is valid — value only, Id only, both, or
        # neither (in which case labels are turned off here).
        value_checkbox = self.cbNodeLabels if is_node else self.cbLinkLabels
        show_value = value_checkbox.isChecked() and bool(fieldName)
        show_id = getattr(self, '_labelShowNodeId' if is_node else '_labelShowLinkId', False)

        if not (show_value or show_id):
            layer.setLabelsEnabled(False)
            layer.triggerRepaint()
            return

        font_size = getattr(self, '_labelFontSize', 10)
        sp = getattr(self, 'spNodeDecimals' if is_node else 'spLinkDecimals', None)
        decimals = sp.value() if sp else 2
        color_by_range = getattr(self, '_labelColorByRange', False)

        # The most used magnitudes are highlighted in bold. When the Id is also shown the
        # label is HTML, so the bold is applied with <b> tags around the value only (the Id
        # line stays regular) and the base font must remain non-bold.
        bold_value = show_value and self._isBoldMagnitude(fieldName, is_node)

        layer_settings = QgsPalLayerSettings()
        text_format = QgsTextFormat()
        font = QFont("Arial")
        font.setBold(bold_value and not show_id)
        text_format.setFont(font)
        text_format.setSize(font_size)
        text_format.setSizeUnit(RENDER_UNIT_POINTS)

        label_bg_color = getattr(self, '_labelBgColor', None)
        if getattr(self, '_labelBgColorLocked', False):
            label_bg_color = getattr(self, '_bgColor', None)
        if label_bg_color:
            bg_settings = QgsTextBackgroundSettings()
            bg_settings.setEnabled(True)
            bg_settings.setType(TEXT_BG_SHAPE_RECTANGLE)
            bg_settings.setSizeType(TEXT_BG_SIZE_BUFFER)
            bg_settings.setSize(QSizeF(_LABEL_BG_BUFFER, _LABEL_BG_BUFFER))
            bg_settings.setSizeUnit(RENDER_UNIT_MILLIMETERS)
            bg_settings.setFillColor(label_bg_color)
            text_format.setBackground(bg_settings)

        # Status is a categorical string field, not a numeric range — skip the
        # graduated "By range" color expression, which assumes numeric ranges.
        is_status_field = fieldName == "Status"

        color_expr = None
        if show_value and color_by_range and not is_status_field:
            color_expr = self._buildRangeColorExpression(layer, fieldName)

        # Color the label text by magnitude (same palette as the header label) so the
        # user identifies the variable by color. Fall back to the neutral defaults.
        mag_color = self._magnitudeColor(fieldName, is_node)
        if mag_color:
            default_color = QColor(mag_color)
        else:
            default_color = _DEFAULT_NODE_LABEL_COLOR if is_node else _DEFAULT_LINK_LABEL_COLOR

        from qgis.core import QgsPropertyCollection
        ddp = QgsPropertyCollection()

        if show_id:
            text_format.setAllowHtmlFormatting(True)
        else:
            text_format.setColor(default_color)
            if color_expr:
                ddp.setProperty(PAL_PROPERTY_COLOR, QgsProperty.fromExpression(color_expr))

        layer_settings.setFormat(text_format)

        # Build the value sub-expression — format_number ensures fixed decimal places (respects
        # locale). The occurrence time (Max/Min stats) is never shown in the label; it lives in
        # the tooltip. value_inner is None when the value is not being shown (Id-only labels).
        is_flow_field = fieldName in ("Flow", "Flow_Sig")
        value_inner = None
        if show_value:
            if is_status_field:
                # Status is categorical: group the 13 link states into just two labels.
                # Any "Closed" state (incl. "Temp Closed") -> "Closed"; "Active"/"Active
                # (Rev Pump)" -> "Active". "Open*" states match no WHEN, so the CASE
                # returns NULL and QGIS paints no label for them. Comparison uses the
                # English values stored by _resolve_link_status; output is translated.
                closed_txt = self.tr("Closed")
                active_txt = self.tr("Active")
                value_inner = (
                    f"CASE WHEN \"Status\" LIKE '%Closed%' THEN '{closed_txt}' "
                    f"WHEN \"Status\" LIKE 'Active%' THEN '{active_txt}' END"
                )
            elif is_flow_field:
                value_inner = f'format_number(abs("{fieldName}"), {decimals})'
            else:
                value_inner = f'format_number("{fieldName}", {decimals})'

        # The Id line is always black; the value line is colored by range (or the symbol color).
        # Id (top) and value (bottom) live in <div> blocks so HTML rendering forces a line break.
        # The column is NodeID/LinkID after the DLL rename and Id on older result layers.
        id_col = '"' + resultIdField(layer) + '"'
        id_line = '\'<span style="color:#000000;">\' || ' + id_col + ' || \'</span>\''

        if show_id and show_value:
            # <b>/</b> keep the bold on the value line only — the Id line above stays regular.
            b_open, b_close = ("<b>", "</b>") if bold_value else ("", "")
            if color_expr:
                value_line = (
                    f"\'<span style=\"color:\' || ({color_expr}) || \';\">{b_open}\' "
                    f"|| coalesce({value_inner}, \'\') || \'{b_close}</span>\'"
                )
            else:
                sym_color = default_color.name()
                with suppress(Exception):
                    sym_color = layer.renderer().symbol().color().name()
                value_line = (
                    f"\'<span style=\"color:{sym_color};\">{b_open}\' "
                    f"|| coalesce({value_inner}, \'\') || \'{b_close}</span>\'"
                )
            full_expr = f"'<div>' || ({id_line}) || '</div><div>' || ({value_line}) || '</div>'"
        elif show_id:
            # Id only — labels appear even with no variable selected or the value label off.
            full_expr = id_line
        else:
            # Value only (non-HTML; text color handled by text_format / data-defined property).
            full_expr = value_inner

        layer_settings.fieldName = full_expr
        layer_settings.isExpression = True
        layer_settings.enabled = True

        type_col = '"' + resultTypeField(layer, default="Type") + '"'
        if is_node:
            layer_settings.placement = PAL_PLACEMENT_AROUND_POINT
            junction_dist, special_dist = self._nodeLabelDistances(bool(label_bg_color))
            layer_settings.dist = junction_dist
            # Tanks and reservoirs use a much larger SVG marker than junctions, so they
            # need their labels pushed further out to clear it.
            ddp.setProperty(
                PAL_PROPERTY_LABEL_DISTANCE,
                QgsProperty.fromExpression(
                    f"CASE WHEN {type_col} IN ('TANK', 'RESERVOIR') THEN {special_dist}"
                    f" ELSE {junction_dist} END"
                ),
            )
        else:
            layer_settings.placement = PAL_PLACEMENT_LINE
            pipe_dist, valve_pump_dist = self._linkLabelDistances(bool(label_bg_color))
            layer_settings.dist = pipe_dist
            # A single `dist` cannot clear both a flow arrow and a pump/valve icon, which are
            # far bigger. Data-defined LabelDistance pushes only those two types further out.
            ddp.setProperty(
                PAL_PROPERTY_LABEL_DISTANCE,
                QgsProperty.fromExpression(
                    f"CASE WHEN {type_col} IN ('PUMP', 'VALVE') THEN {valve_pump_dist}"
                    f" ELSE {pipe_dist} END"
                ),
            )
        layer_settings.distUnits = RENDER_UNIT_MILLIMETERS
        layer_settings.setDataDefinedProperties(ddp)
        labels = QgsVectorLayerSimpleLabeling(layer_settings)
        layer.setLabeling(labels)
        layer.setLabelsEnabled(True)
        layer.triggerRepaint()

    def _labelMargin(self, has_background):
        """Gap (mm) to leave between the symbol edge and the label, background included."""
        return _LABEL_CLEARANCE + (_LABEL_BG_BUFFER if has_background else 0.0)

    def _linkLabelDistances(self, has_background):
        """Perpendicular label offsets (mm) for pipes and for pumps/valves.

        Each is half the perpendicular extent of the symbol painted on the link plus the
        label background buffer and a fixed clearance, so an opaque label box never covers
        the flow arrow (pipes) or the SVG icon (pumps/valves). Both track the Appearance
        factors, since the symbols they must clear scale with them.
        """
        margin = self._labelMargin(has_background)

        arrow_factor = getattr(self, '_arrowFactor', 1.0)
        valve_pump_factor = getattr(self, '_valvePumpFactor', 1.0)

        show_arrows = False
        with suppress(Exception):
            show_arrows = self.cbFlowDirections.isChecked()

        pipe_dist = margin
        if show_arrows:
            pipe_dist = _BASE_ARROW_SIZE * arrow_factor / 2.0 + margin
        valve_pump_dist = _BASE_VALVE_PUMP_SIZE * valve_pump_factor / 2.0 + margin
        # Pumps/valves are never closer than pipes, whatever the factor combination.
        valve_pump_dist = max(valve_pump_dist, pipe_dist)
        return round(pipe_dist, 3), round(valve_pump_dist, 3)

    def _nodeLabelDistances(self, has_background):
        """Label offsets (mm) for junctions and for tanks/reservoirs.

        Same rule as the link offsets: half the symbol's radius plus the margin. In
        proportional mode the renderer grows node markers up to 2x their factor size,
        so the offset accounts for that worst case and the label stays clear of the
        largest symbol on the layer.
        """
        margin = self._labelMargin(has_background)

        symbol_factor = getattr(self, '_symbolFactor', 1.0)
        special_factor = getattr(self, '_specialFactor', 1.0)
        growth = 2.0 if getattr(self, '_proportional', False) else 1.0

        junction_dist = _BASE_JUNCTION_SIZE * symbol_factor * growth / 2.0 + margin
        special_dist = _BASE_SPECIAL_SIZE * special_factor * growth / 2.0 + margin
        return round(junction_dist, 3), round(special_dist, 3)

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
        actual_field = f'abs("{fieldName}")' if fieldName in ("Flow", "Flow_Sig") else f'"{fieldName}"'
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
        actual_field = f'abs("{fieldName}")' if fieldName in ("Flow", "Flow_Sig") else f'"{fieldName}"'
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
        Sizes are always computed as base × factor and assigned absolutely, so repeated
        calls with the same arguments are idempotent and no state about the previous call
        needs tracking. The base is what the style itself states (see baseSizesFor), so a
        factor of 1.0 means "as the style drew it" and not "back to the shipped values".
        """
        is_line  = layer.geometryType() == 1
        is_point = layer.geometryType() == 0
        if not is_line and not is_point:
            return

        pipe_factor       = getattr(self, '_pipeFactor',      1.0)
        symbol_factor     = getattr(self, '_symbolFactor',    1.0)
        special_factor    = getattr(self, '_specialFactor',   1.0)
        valve_pump_factor = getattr(self, '_valvePumpFactor', 1.0)
        arrow_factor      = getattr(self, '_arrowFactor',     1.0)

        base = self.baseSizesFor(layer)
        target_pipe_width  = round(base["pipe"]      * pipe_factor,       6)
        target_arrow_size  = round(base["arrow"]     * arrow_factor,      6)
        target_junction    = round(base["junction"]  * symbol_factor,     6)
        target_special     = round(base["special"]   * special_factor,    6)
        target_valve_pump  = round(base["valvePump"] * valve_pump_factor, 6)

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

        sizing_method = "setWidth" if is_line else "setSize"

        new_renderer = renderer.clone()
        mismatched = 0
        for rule in new_renderer.rootRule().children():
            sym = rule.symbol()
            if sym is None:
                continue
            if not hasattr(sym, sizing_method):
                mismatched += 1
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
                                SL_PROP_STROKE_WIDTH,
                                QgsProperty.fromExpression(prop_expr))
                        else:
                            sl0.setDataDefinedProperty(
                                SL_PROP_STROKE_WIDTH, QgsProperty())
                # Pump/valve SVG icon sizes (MarkerLine at indices 1, 2). They have their own
                # factor so the icons can be resized without touching the pipe line width.
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
                hide_junction_border = getattr(self, '_nodeBorder', False)
                type_field = resultTypeField(layer, default="Type")
                for sl_idx in range(sym.symbolLayerCount()):
                    with suppress(Exception):
                        sl = sym.symbolLayer(sl_idx)
                        if sl is None:
                            continue
                        ddp = sl.dataDefinedProperties()
                        size_prop = ddp.property(SL_PROP_SIZE)
                        if size_prop.isActive():
                            old_expr = size_prop.expressionString()
                            if can_be_proportional:
                                new_expr = _apply_proportional_node_size(
                                    old_expr, field,
                                    prop_field_min, prop_field_max,
                                    target_junction, target_special, type_field)
                            else:
                                new_expr = _build_node_size_expr(
                                    old_expr, str(target_junction), str(target_special), type_field)
                            if new_expr != old_expr:
                                ddp.setProperty(SL_PROP_SIZE, QgsProperty.fromExpression(new_expr))
                                sl.setDataDefinedProperties(ddp)
                        # Junction border: SimpleMarker junctions render a thin black outline
                        # by default (outline_width=0 is still a visible cosmetic hairline in
                        # Qt, not "no line"). Reservoirs/tanks use SvgMarker and already have
                        # no border by default, so this option only ever touches junctions.
                        with suppress(Exception):
                            if 'Svg' in type(sl).__name__:
                                continue
                            if hide_junction_border:
                                sl.setDataDefinedProperty(
                                    SL_PROP_STROKE_COLOR,
                                    QgsProperty.fromExpression("color_rgba(0,0,0,0)"))
                            else:
                                sl.setDataDefinedProperty(
                                    SL_PROP_STROKE_COLOR, QgsProperty())

        if mismatched:
            QgsMessageLog.logMessage(
                self.tr("%1 symbols of layer %2 do not match its geometry and were not resized")
                    .replace("%1", str(mismatched)).replace("%2", layer.name()),
                "QGISRed",
                QGIS_WARNING,
            )

        with self.writingOwnStyle():
            layer.setRenderer(new_renderer)
        layer.triggerRepaint()
        if hasattr(self, 'iface') and self.iface:
            self.iface.mapCanvas().refresh()

    def setArrowsVisibility(self, symbol, layer, field):
        prop = QgsProperty()
        try:
            if layer.geometryType() == 1 and self.cbFlowDirections.isChecked():
                # Show arrows in pipes
                type_col = '"' + resultTypeField(layer, default="Type") + '"'
                arrow_symbol_layer = symbol.symbolLayer(3)  # arrow positive flow
                prop.setExpressionString("if(" + type_col + "='PIPE', if(" + field + ">0,3,0),0)")
                arrow_symbol_layer.subSymbol().setDataDefinedSize(prop)
                arrow_symbol_layer = symbol.symbolLayer(4)  # arrow negative flow
                prop.setExpressionString("if(" + type_col + "='PIPE', if(" + field + "<0,3,0),0)")
                arrow_symbol_layer.subSymbol().setDataDefinedSize(prop)
            else:
                # Hide arrows
                prop.setExpressionString("0")
                symbol.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
                symbol.symbolLayer(4).subSymbol().setDataDefinedSize(prop)
        except Exception:
            self.cbFlowDirections.setChecked(False)
            self.cbFlowDirections.setEnabled(False)

    def _warnIfNoClasses(self, renderer, db_field_name, nameLayer):
        """Log when the renderer ends up with no classes at all.

        The field is now always the one selected in the comboboxes, so an empty
        classification means the column really has no values: the statistic was not
        written to the layer. On the map that is indistinguishable from a styling
        problem, hence the trace in the QGISRed log.
        """
        if not isinstance(renderer, QgsGraduatedSymbolRenderer) or renderer.ranges():
            return
        QgsMessageLog.logMessage(
            self.tr("No values to classify in field '%1' of layer %2: the legend was left empty")
                .replace("%1", db_field_name).replace("%2", self.tr(nameLayer)),
            "QGISRed",
            QGIS_WARNING,
        )

    def setGraduatedPalette(self, layer, field, setRender, nameLayer, previously_displayed=None):
        # Whatever the layer looks like right now is about to be replaced, so this is the
        # last chance to remember it — including anything the user changed by hand.
        if setRender:
            self.rememberCurrentRender(layer)

        renderer = layer.renderer()
        db_field_name = field  # column name as stored in the DBF
        qmlName = resultStyleName(nameLayer, db_field_name)
        if field == "Flow":
            field = "abs(" + field + ")"

        is_status = (db_field_name == "Status")
        cached = self._lookupCachedRenderer(layer, db_field_name) if setRender else None

        utils = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

        # Ensure correct renderer type
        if cached is not None:
            renderer = cached
        elif is_status:
            # Load the QML unless the current renderer already belongs to Status (i.e. we
            # were displaying something else before this call).
            if previously_displayed != db_field_name:
                utils.setStyle(layer, qmlName, field=db_field_name)
                renderer = layer.renderer()
        else:
            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer_correct = renderer.classAttribute() == field and len(renderer.ranges()) > 0
            elif isinstance(renderer, QgsRuleBasedRenderer):
                renderer_correct = (previously_displayed == db_field_name)
            else:
                renderer_correct = False

            if not renderer_correct:
                # The QML is shared by several variables (Flow, Flow_Sig and Flow_Unsig all
                # use LinkFlow.qml), so the style's own legend strategy would classify the
                # column it was saved with. Pass the field actually selected in the combobox
                # so the classification is built over the values about to be displayed.
                utils.setStyle(layer, qmlName, field=field)
                renderer = layer.renderer()

        # A cached renderer already classifies the right column: it was captured while that
        # very variable was on screen.
        if cached is None and isinstance(renderer, QgsGraduatedSymbolRenderer):
            renderer.setClassAttribute(field)
            self._warnIfNoClasses(renderer, db_field_name, nameLayer)

        # Read what the style states before anything writes over it. Skipped for a cached
        # renderer: that one already carries the factors, and taking it as the base would
        # multiply them again. It has to happen before the arrows are rebuilt below, which
        # replaces their size outright.
        if cached is None:
            self.rememberStyleBaseSizes(layer, db_field_name, renderer)

        # Update arrow visibility
        with suppress(Exception):
            flow_field = self._flowDirectionField()
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, flow_field)

        with self.writingOwnStyle():
            layer.setRenderer(renderer)
            QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface).applyNullStyle(layer)

        # Bind the layer to the key this renderer belongs to, so the next restyle knows
        # where to file it away without having to guess the state it was applied under.
        self._renderKeyInUse[self.getLayerPath(layer)] = self._getRenderStorageKey(
            self.getLayerPath(layer), db_field_name)
        self.watchRendererChanges(layer)

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
