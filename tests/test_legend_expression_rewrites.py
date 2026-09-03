# -*- coding: utf-8 -*-
"""In-place expression rewrites the legend editor applies to the shipped input styles.

Every editable colour/size is a with_variable() declaration at the top of the
expression. Fixtures are the exact expressions from defaults/layerStyles/*.qml.bak
(guarded below): the editor must change only the declared value it edits and keep
the rest of the expression untouched.
"""
import os
import xml.etree.ElementTree as ET

import pytest

import QGISRed.ui.project.qgisred_custom_dialogs as customDialogsModule
import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSymbolColorSelector
from QGISRed.ui.project.qgisred_legends_dialog import (
    ISOLATION_VALVE_FILL_TEMPLATE,
    QGISRedLegendsDialog,
    formatExpressionNumber,
    meterStyleVariable,
    parseCategoricalRuleFilter,
    scaleNumericLiterals,
    styleVariablePattern,
    substituteCapturedGroup,
)

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DEMAND = "coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseDemand'))"
BASE_VALUE = "coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseValue'))"
METER_TYPE = "coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type'))"

PIPE_COLOR = (
    "with_variable('openPipeColor', '#0f1291', with_variable('closedPipeColor', '#ff0f13', "
    "if(IniStatus is NULL, @openPipeColor, if(IniStatus != 'CLOSED', @openPipeColor, @closedPipeColor))))"
)
PIPE_CV_SIZE = "with_variable('cvPipeSize', 5, if(IniStatus is NULL, 0, if(IniStatus != 'CV', 0, @cvPipeSize)))"
PUMP_COLOR = (
    "with_variable('openPumpColor', '#85b66f', with_variable('closedPumpColor', '#ff0f13', "
    "if(IniStatus is NULL, @openPumpColor, if(IniStatus != 'CLOSED', @openPumpColor, @closedPumpColor))))"
)
VALVE_COLOR = (
    "with_variable('openValveColor', '#85b66f', with_variable('closedValveColor', '#ff0f13', "
    "with_variable('activeValveColor', '#ff9900', if(IniStatus is NULL, @openValveColor, "
    "if(IniStatus = 'CLOSED', @closedValveColor, if(IniStatus != 'ACTIVE', @openValveColor, @activeValveColor))))))"
)
JUNCTION_COLOR = (
    "with_variable('positiveDemandJunctionColor', '#fdbf6f', with_variable('negativeDemandJunctionColor', '#78b3dc', "
    "with_variable('noDemandJunctionColor', '#ffffff', if(BaseDem is NULL, @noDemandJunctionColor, "
    "if(BaseDem > 0, @positiveDemandJunctionColor, "
    "if(BaseDem < 0, @negativeDemandJunctionColor, @noDemandJunctionColor))))))"
)
JUNCTION_EMITTER_SIZE = (
    "with_variable('emitterJunctionSize', 2.2, with_variable('negativeDemandEmitterJunctionSize', 4, "
    "if(EmittCoef > 0, if(BaseDem is NULL, @emitterJunctionSize, if(BaseDem > 0, @emitterJunctionSize, "
    "if(BaseDem < 0, @negativeDemandEmitterJunctionSize, @emitterJunctionSize))), 0)))"
)
JUNCTION_BASE_SIZE = (
    "with_variable('junctionSize', 1.3, with_variable('negativeDemandJunctionSize', 3.5, "
    "if(EmittCoef > 0, 0, if(BaseDem is NULL, @junctionSize, if(BaseDem > 0, @junctionSize, "
    "if(BaseDem < 0, @negativeDemandJunctionSize, @junctionSize))))))"
)
SOURCE_STROKE = (
    "if(@id is NULL, NULL, with_variable('massSourceColor', '#d17123', "
    "with_variable('flowpacedSourceColor', '#23d146', "
    "with_variable('concenSourceColor', '#0d20ed', with_variable('setpointSourceColor', '#cb0f96', "
    "with_variable('noQualitySourceColor', '#9d979d', "
    "with_variable('bq', coalesce(attribute($currentfeature,'SourceQual'),attribute($currentfeature,'BaseValue')), "
    "with_variable('st', coalesce(attribute($currentfeature,'SourceType'),attribute($currentfeature,'Type')), "
    "if(@bq is NULL or @bq = 0, @noQualitySourceColor, if(@st = 'MASS', @massSourceColor, "
    "if(@st = 'FLOWPACED', @flowpacedSourceColor, "
    "if(@st = 'CONCEN', @concenSourceColor, @setpointSourceColor))))))))))))"
)
SERVICE_CONNECTION_STROKE = (
    "with_variable('activeServiceConnectionColor', '#85b66f', "
    "with_variable('inactiveServiceConnectionColor', '#ff0f13', "
    "if(IsActive is NULL, @activeServiceConnectionColor, "
    "if(IsActive > 0, @activeServiceConnectionColor, @inactiveServiceConnectionColor))))"
)
SERVICE_CONNECTION_FILL = (
    "if(@id is NULL, NULL, with_variable('activeDemandServiceConnectionColor', '#b7dfa3', "
    "with_variable('inactiveDemandServiceConnectionColor', '#c7cbc5', "
    "with_variable('noDemandServiceConnectionColor', '#ffffff', if(" + BASE_DEMAND + " > 0, "
    "if(IsActive is NULL or IsActive > 0, @activeDemandServiceConnectionColor, @inactiveDemandServiceConnectionColor), "
    "@noDemandServiceConnectionColor)))))"
)
DEMANDS_FILL = (
    "if(@id is NULL, NULL, with_variable('positiveDemandColor', '#fdbf6f', "
    "with_variable('negativeDemandColor', '#a6cee3', "
    "with_variable('noDemandColor', '#ffffff', with_variable('bd', " + BASE_VALUE + ", "
    "if(@bd is NULL, @noDemandColor, if(@bd > 0, @positiveDemandColor, "
    "if(@bd < 0, @negativeDemandColor, @noDemandColor))))))))"
)
DEMANDS_SIZE = (
    "if(@id is NULL, NULL, with_variable('demandSize', 1.6, with_variable('negativeDemandSize', 3.5, "
    "with_variable('bd', " + BASE_VALUE + ", "
    "if(@bd is NULL, @demandSize, if(@bd > 0, @demandSize, if(@bd < 0, @negativeDemandSize, @demandSize)))))))"
)
METER_COLORS = {
    "EnergySensor": "#fdf47b",
    "ValveOpening": "#ccd3b5",
    "DifferentialManometer": "#8de3c2",
    "StatusSensor": "#eeab68",
    "Tachometer": "#f7c7ac",
    "Countermeter": "#82d5f6",
    "Flowmeter": "#b8e7fa",
    "QualitySensor": "#bcb7ef",
    "LevelSensor": "#edbde8",
    "Manometer": "#baf4c9",
}
METER_STROKE = (
    "with_variable('meterStrokeColor', '#232323', with_variable('inactiveMeterStrokeColor', '#999999', "
    "if(IsActive is NULL, @meterStrokeColor, if(IsActive != 0, @meterStrokeColor, @inactiveMeterStrokeColor))))"
)


def meterFill(meterType):
    variable = meterStyleVariable(meterType, "Color")
    return (
        f"with_variable('{variable}', '{METER_COLORS[meterType]}', with_variable('inactiveMeterColor', '#cccccc', "
        f"if(IsActive is NULL, @{variable}, if(IsActive != 0, @{variable}, @inactiveMeterColor))))"
    )


def meterSize(meterType):
    variable = meterStyleVariable(meterType, "Size")
    nullSize = "@" + variable if meterType == "Manometer" else "0"
    return (
        f"if(@id is NULL, NULL, with_variable('{variable}', 5, with_variable('mt', {METER_TYPE}, "
        f"if(@mt is NULL, {nullSize}, if(@mt = '{meterType}', @{variable}, 0)))))"
    )


# ---------------------------------------------------------------------------
# Fakes: plain objects, so hasattr() answers honestly (unlike the Qt stubs).
# ---------------------------------------------------------------------------

class FakeQgsProperty:
    ExpressionBasedProperty = object()

    def __init__(self, expr=None):
        self.expr = expr

    def __bool__(self):
        # Mirrors the real QgsProperty: a default-constructed one is falsy.
        return self.expr is not None

    @classmethod
    def fromExpression(cls, expr):
        return cls(expr)

    def propertyType(self):
        return type(self).ExpressionBasedProperty

    def expressionString(self):
        return self.expr


# The shims, not QgsSymbolLayer.PropertyFillColor: that spelling is QGIS 3 only and
# the modules under test read the keys from compat.py (see test_legend_expression_compat).
FILL_KEY = legendsModule.SL_PROP_FILL_COLOR
STROKE_KEY = legendsModule.SL_PROP_STROKE_COLOR
SIZE_KEY = legendsModule.SL_PROP_SIZE
WIDTH_KEY = legendsModule.SL_PROP_WIDTH


class FakeSymbolLayer:
    """A symbol layer with data-defined expressions, a base size/width and colors."""

    def __init__(self, layerType="SimpleMarker", expressions=None, subSymbol=None, size=1.0):
        self._layerType = layerType
        self._subSymbol = subSymbol
        self._props = {key: FakeQgsProperty(expr) for key, expr in (expressions or {}).items()}
        self._size = size
        self._width = size
        self.colorCalls = []
        self.strokeColorCalls = []

    def dataDefinedProperties(self):
        layer = self

        class _Collection:
            def property(self, key):
                return layer._props.get(key)

        return _Collection()

    def setDataDefinedProperty(self, key, prop):
        self._props[key] = prop

    def expression(self, key):
        prop = self._props.get(key)
        return prop.expr if prop else None

    def layerType(self):
        return self._layerType

    def subSymbol(self):
        return self._subSymbol

    def size(self):
        return self._size

    def setSize(self, size):
        self._size = size

    def width(self):
        return self._width

    def setWidth(self, width):
        self._width = width

    def setColor(self, color):
        self.colorCalls.append(color)

    def setStrokeColor(self, color):
        self.strokeColorCalls.append(color)


class FakeSymbol:
    def __init__(self, layers):
        self._layers = layers
        self.baseColor = None

    def symbolLayerCount(self):
        return len(self._layers)

    def symbolLayer(self, i):
        return self._layers[i]

    def setColor(self, color):
        self.baseColor = color


class FakeHexColor:
    def __init__(self, hexName):
        self._hexName = hexName

    def name(self):
        return self._hexName


class FakeLayer:
    def __init__(self, identifier):
        self._identifier = identifier

    def customProperty(self, key):
        return self._identifier if key == "qgisred_identifier" else None


def _dialog(monkeypatch, identifier, variant=None):
    monkeypatch.setattr(legendsModule, "QgsProperty", FakeQgsProperty)
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentLayer = FakeLayer(identifier)
    dialog.getSelectedVariant = lambda: variant
    return dialog


def declared(expr, name, isText=True):
    match = styleVariablePattern(name, isText).search(expr)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# The variable declarations themselves
# ---------------------------------------------------------------------------

class TestStyleVariablePattern:
    def test_text_pattern_captures_the_bare_literal(self):
        assert declared(PIPE_COLOR, "openPipeColor") == "#0f1291"
        assert declared(PIPE_COLOR, "closedPipeColor") == "#ff0f13"

    def test_number_pattern_captures_the_number(self):
        assert declared(PIPE_CV_SIZE, "cvPipeSize", isText=False) == "5"
        assert declared(JUNCTION_EMITTER_SIZE, "emitterJunctionSize", isText=False) == "2.2"

    def test_each_pattern_matches_only_its_own_declaration(self):
        assert declared(PIPE_CV_SIZE, "openPipeColor") is None
        assert declared(PIPE_COLOR, "cvPipeSize", isText=False) is None
        assert declared(JUNCTION_BASE_SIZE, "junctionSize", isText=False) == "1.3"
        assert declared(JUNCTION_BASE_SIZE, "negativeDemandJunctionSize", isText=False) == "3.5"

    def test_substitution_changes_only_the_declared_value(self):
        newExpr, changed = substituteCapturedGroup(PIPE_COLOR, styleVariablePattern("openPipeColor", True), "#123456")
        assert changed
        assert newExpr.count("'#123456'") == 1 and "#0f1291" not in newExpr
        assert "with_variable('closedPipeColor', '#ff0f13'" in newExpr
        assert newExpr.count("@openPipeColor") == 2
        assert newExpr.endswith("if(IniStatus != 'CLOSED', @openPipeColor, @closedPipeColor))))")

    def test_substitution_is_idempotent(self):
        pattern = styleVariablePattern("cvPipeSize", False)
        once, _ = substituteCapturedGroup(PIPE_CV_SIZE, pattern, "6.667")
        assert once == (
            "with_variable('cvPipeSize', 6.667, if(IniStatus is NULL, 0, if(IniStatus != 'CV', 0, @cvPipeSize)))"
        )
        twice, changed = substituteCapturedGroup(once, pattern, "10")
        assert changed and "with_variable('cvPipeSize', 10," in twice and "6.667" not in twice

    def test_coalesce_wrappers_survive_a_substitution(self):
        pattern = styleVariablePattern("activeDemandServiceConnectionColor", True)
        newExpr, changed = substituteCapturedGroup(SERVICE_CONNECTION_FILL, pattern, "#123456")
        assert changed and BASE_DEMAND in newExpr and newExpr.startswith("if(@id is NULL, NULL, ")

    def test_meter_variable_names(self):
        assert meterStyleVariable("EnergySensor", "Color") == "energySensorMeterColor"
        assert meterStyleVariable("Manometer", "Size") == "manometerMeterSize"


# ---------------------------------------------------------------------------
# The shipped .qml.bak files carry exactly these expressions
# ---------------------------------------------------------------------------

def _dataDefinedExpressions(layerElement):
    """{property name: expression} of a QML symbol layer's data-defined properties."""
    properties = layerElement.find("data_defined_properties/Option/Option[@name='properties']")
    if properties is None:
        return {}
    return {
        option.get("name"): option.find("Option[@name='expression']").get("value")
        for option in properties.findall("Option")
    }


def _rendererLayers(fileName):
    """[(class, {property: expression}, [sub-symbol layers])] of the shipped renderer symbol."""
    path = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", fileName)
    symbol = ET.parse(path).getroot().find("renderer-v2/symbols/symbol")

    def describe(layerElement):
        subLayers = [describe(sub) for sub in layerElement.findall("symbol/layer")]
        return layerElement.get("class"), _dataDefinedExpressions(layerElement), subLayers

    return [describe(layerElement) for layerElement in symbol.findall("layer")]


class TestShippedStyles:
    def test_pipes(self):
        layers = _rendererLayers("Pipes.qml.bak")
        (line, lineExprs, _), (markerLine, markerLineExprs, [(marker, markerExprs, _)]) = layers
        assert (line, markerLine, marker) == ("SimpleLine", "MarkerLine", "SvgMarker")
        assert lineExprs["outlineColor"] == PIPE_COLOR
        assert lineExprs["customDash"] == "if(IniStatus = 'CLOSED', '5;2', '5000;0')"
        assert markerLineExprs == {"width": PIPE_CV_SIZE}
        assert markerExprs == {"fillColor": PIPE_COLOR, "size": PIPE_CV_SIZE}

    @pytest.mark.parametrize("fileName, colorExpr", [("Pumps.qml.bak", PUMP_COLOR), ("Valves.qml.bak", VALVE_COLOR)])
    def test_pumps_and_valves(self, fileName, colorExpr):
        (_, lineExprs, _), (_, markerLineExprs, [(_, markerExprs, _)]) = _rendererLayers(fileName)
        assert lineExprs["outlineColor"] == colorExpr
        assert markerLineExprs == {}
        assert markerExprs == {"fillColor": colorExpr}

    def test_junctions(self):
        (_, emitterExprs, _), (_, baseExprs, _) = _rendererLayers("Junctions.qml.bak")
        assert emitterExprs == {"fillColor": JUNCTION_COLOR, "size": JUNCTION_EMITTER_SIZE}
        assert baseExprs == {"fillColor": JUNCTION_COLOR, "size": JUNCTION_BASE_SIZE}

    def test_sources(self):
        [(_, exprs, _)] = _rendererLayers("Sources.qml.bak")
        assert exprs == {"outlineColor": SOURCE_STROKE}

    def test_isolation_valves_match_the_repair_template(self):
        [(_, exprs, _)] = _rendererLayers("IsolationValves.qml.bak")
        assert exprs == {"fillColor": ISOLATION_VALVE_FILL_TEMPLATE}

    def test_service_connections(self):
        (_, lineExprs, _), (_, _, [(_, markerExprs, _)]) = _rendererLayers("ServiceConnections.qml.bak")
        assert lineExprs["outlineColor"] == SERVICE_CONNECTION_STROKE
        assert markerExprs == {"fillColor": SERVICE_CONNECTION_FILL, "outlineColor": SERVICE_CONNECTION_STROKE}

    def test_multiple_demands(self):
        (_, outerExprs, _), (_, innerExprs, _) = _rendererLayers("demands.qml.bak")
        assert outerExprs == {}
        assert innerExprs == {"fillColor": DEMANDS_FILL, "size": DEMANDS_SIZE}

    def test_meters_one_layer_per_type(self):
        layers = _rendererLayers("Meters.qml.bak")
        assert len(layers) == len(QGISRedLegendsDialog.METER_TYPES) == 10
        seen = set()
        for _, exprs, _ in layers:
            meterType = next(t for t in METER_COLORS if f"'{t}'" in exprs["width"])
            seen.add(meterType)
            assert exprs == {
                "fillColor": meterFill(meterType), "outlineColor": METER_STROKE, "width": meterSize(meterType)
            }
        assert seen == set(QGISRedLegendsDialog.METER_TYPES)


# ---------------------------------------------------------------------------
# What the dialog reads for the swatch and the size cell
# ---------------------------------------------------------------------------

class TestInputVariables:
    @pytest.mark.parametrize("identifier, variant, expected", [
        ("qgisred_pipes", None, ("openPipeColor",)),
        ("qgisred_pumps", None, ("openPumpColor",)),
        ("qgisred_valves", None, ("openValveColor",)),
        ("qgisred_junctions", "positive", ("positiveDemandJunctionColor",)),
        ("qgisred_junctions", "negative", ("negativeDemandJunctionColor",)),
        ("qgisred_demands", None, ("positiveDemandColor",)),
        ("qgisred_isolationvalves", None, ("openIsolationValveColor",)),
        ("qgisred_serviceconnections", "line", ("activeServiceConnectionColor",)),
        ("qgisred_serviceconnections", "circle", ("activeDemandServiceConnectionColor",)),
        ("qgisred_sources", "FLOWPACED", ("flowpacedSourceColor",)),
        ("qgisred_meters", "Flowmeter", ("flowmeterMeterColor",)),
        ("qgisred_tanks", None, ()),
    ])
    def test_color_variables(self, monkeypatch, identifier, variant, expected):
        assert _dialog(monkeypatch, identifier, variant).inputColorVariables(identifier) == expected

    def test_all_meter_types_when_no_type_is_selected(self, monkeypatch):
        variables = _dialog(monkeypatch, "qgisred_meters").inputColorVariables("qgisred_meters")
        assert len(variables) == 10 and "manometerMeterColor" in variables

    def test_size_variables_show_the_selected_scenario_first(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_junctions", "negative")
        assert dialog.inputSizeVariables("qgisred_junctions")[0] == "negativeDemandJunctionSize"
        dialog = _dialog(monkeypatch, "qgisred_meters", "Tachometer")
        assert dialog.inputSizeVariables("qgisred_meters") == ("tachometerMeterSize",)
        assert _dialog(monkeypatch, "qgisred_pipes").inputSizeVariables("qgisred_pipes") == ()

    def test_reads_the_declared_color_and_size(self, monkeypatch):
        monkeypatch.setattr(legendsModule, "QColor", lambda hexName: hexName)
        dialog = _dialog(monkeypatch, "qgisred_junctions", "negative")
        symbol = FakeSymbol([FakeSymbolLayer(expressions={FILL_KEY: JUNCTION_COLOR, SIZE_KEY: JUNCTION_BASE_SIZE})])
        assert dialog._readInputLayerColor(symbol, "qgisred_junctions") == "#78b3dc"
        assert dialog._readInputLayerSize(symbol) == 3.5

    def test_reads_nothing_from_a_style_without_declarations(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_pipes")
        legacy = "if(IniStatus is NULL, '#0f1291', '#ff0f13')"
        symbol = FakeSymbol([FakeSymbolLayer("SimpleLine", {STROKE_KEY: legacy})])
        assert dialog._readInputLayerColor(symbol, "qgisred_pipes") is None
        assert dialog._readInputLayerSize(symbol) is None


# ---------------------------------------------------------------------------
# Appliers
# ---------------------------------------------------------------------------

class TestPipesApplier:
    def _apply(self, monkeypatch, color, size):
        marker = FakeSymbolLayer("SvgMarker", {FILL_KEY: PIPE_COLOR, SIZE_KEY: PIPE_CV_SIZE})
        markerLine = FakeSymbolLayer("MarkerLine", {WIDTH_KEY: PIPE_CV_SIZE}, subSymbol=FakeSymbol([marker]))
        line = FakeSymbolLayer("SimpleLine", {STROKE_KEY: PIPE_COLOR}, size=1.5)
        _dialog(monkeypatch, "qgisred_pipes")._applyPipesLegend(FakeSymbol([line, markerLine]), color, size)
        return line, markerLine, marker

    def test_color_reaches_the_line_stroke_and_the_cv_marker_fill(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, FakeHexColor("#123456"), None)
        for expr in (line.expression(STROKE_KEY), marker.expression(FILL_KEY)):
            assert declared(expr, "openPipeColor") == "#123456"
            assert declared(expr, "closedPipeColor") == "#ff0f13"
        assert markerLine.expression(WIDTH_KEY) == PIPE_CV_SIZE
        assert line.width() == 1.5

    def test_size_sets_the_line_width_and_scales_both_cv_declarations(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, None, 2.0)
        assert line.width() == 2.0
        for expr in (markerLine.expression(WIDTH_KEY), marker.expression(SIZE_KEY)):
            assert declared(expr, "cvPipeSize", isText=False) == "6.667"
            assert expr.endswith("if(IniStatus is NULL, 0, if(IniStatus != 'CV', 0, @cvPipeSize)))")
        assert line.expression(STROKE_KEY) == PIPE_COLOR

    def test_the_shipped_width_keeps_the_shipped_cv_size(self, monkeypatch):
        _line, markerLine, _marker = self._apply(monkeypatch, None, QGISRedLegendsDialog.PIPE_DEFAULT_WIDTH)
        assert markerLine.expression(WIDTH_KEY) == PIPE_CV_SIZE


class TestPumpsAndValvesApplier:
    @pytest.mark.parametrize("identifier, colorExpr, applier, variable, fixed", [
        ("qgisred_pumps", PUMP_COLOR, "_applyPumpsLegend", "openPumpColor", ("closedPumpColor",)),
        ("qgisred_valves", VALVE_COLOR, "_applyValvesLegend", "openValveColor",
         ("closedValveColor", "activeValveColor")),
    ])
    def test_only_the_open_color_changes_on_line_and_marker(self, monkeypatch, identifier, colorExpr, applier, variable,
                                                            fixed):
        marker = FakeSymbolLayer("SvgMarker", {FILL_KEY: colorExpr}, size=5)
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        line = FakeSymbolLayer("SimpleLine", {STROKE_KEY: colorExpr}, size=1.5)
        getattr(_dialog(monkeypatch, identifier), applier)(FakeSymbol([line, markerLine]), FakeHexColor("#123456"), 3.0)
        for expr in (line.expression(STROKE_KEY), marker.expression(FILL_KEY)):
            assert declared(expr, variable) == "#123456"
            for name in fixed:
                assert declared(expr, name) == declared(colorExpr, name)
        assert line.width() == 3.0
        assert marker.size() == 10  # 5 mm at 1.5 px, scaled with the line


class TestJunctionsApplier:
    def _symbol(self):
        emitter = FakeSymbolLayer(expressions={FILL_KEY: JUNCTION_COLOR, SIZE_KEY: JUNCTION_EMITTER_SIZE}, size=1.3)
        base = FakeSymbolLayer(expressions={FILL_KEY: JUNCTION_COLOR, SIZE_KEY: JUNCTION_BASE_SIZE}, size=1.3)
        return FakeSymbol([emitter, base]), emitter, base

    def test_positive_scenario_colors_only_the_positive_branch(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        dialog = _dialog(monkeypatch, "qgisred_junctions", "positive")
        dialog._applyJunctionsLegend(symbol, FakeHexColor("#123456"), None)
        for expr in (emitter.expression(FILL_KEY), base.expression(FILL_KEY)):
            assert declared(expr, "positiveDemandJunctionColor") == "#123456"
            assert declared(expr, "negativeDemandJunctionColor") == "#78b3dc"
            assert declared(expr, "noDemandJunctionColor") == "#ffffff"

    def test_negative_scenario_colors_only_the_negative_branch(self, monkeypatch):
        symbol, emitter, _base = self._symbol()
        dialog = _dialog(monkeypatch, "qgisred_junctions", "negative")
        dialog._applyJunctionsLegend(symbol, FakeHexColor("#123456"), None)
        assert declared(emitter.expression(FILL_KEY), "negativeDemandJunctionColor") == "#123456"
        assert declared(emitter.expression(FILL_KEY), "positiveDemandJunctionColor") == "#fdbf6f"

    def test_size_scales_every_size_variable_from_the_shown_one(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "positive")._applyJunctionsLegend(symbol, None, 2.6)
        assert declared(base.expression(SIZE_KEY), "junctionSize", isText=False) == "2.6"
        assert declared(base.expression(SIZE_KEY), "negativeDemandJunctionSize", isText=False) == "7"
        assert declared(emitter.expression(SIZE_KEY), "emitterJunctionSize", isText=False) == "4.4"
        assert declared(emitter.expression(SIZE_KEY), "negativeDemandEmitterJunctionSize", isText=False) == "8"
        assert emitter.size() == base.size() == 2.6  # base sizes follow, for the legend icon
        assert emitter.expression(SIZE_KEY).endswith("@emitterJunctionSize))), 0)))")

    def test_negative_scenario_scales_from_the_negative_size(self, monkeypatch):
        symbol, _emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "negative")._applyJunctionsLegend(symbol, None, 7.0)
        assert declared(base.expression(SIZE_KEY), "negativeDemandJunctionSize", isText=False) == "7"
        assert declared(base.expression(SIZE_KEY), "junctionSize", isText=False) == "2.6"

    def test_an_untouched_size_is_a_no_op(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "positive")._applyJunctionsLegend(symbol, None, 1.3)
        assert base.expression(SIZE_KEY) == JUNCTION_BASE_SIZE and emitter.expression(SIZE_KEY) == JUNCTION_EMITTER_SIZE


class TestDemandsApplier:
    def _symbol(self):
        outer = FakeSymbolLayer(size=2.8)
        inner = FakeSymbolLayer(expressions={FILL_KEY: DEMANDS_FILL, SIZE_KEY: DEMANDS_SIZE}, size=1.6)
        return FakeSymbol([outer, inner]), outer, inner

    def test_color_goes_to_the_positive_branch_only(self, monkeypatch):
        symbol, outer, inner = self._symbol()
        _dialog(monkeypatch, "qgisred_demands")._applyDemandsLegend(symbol, FakeHexColor("#123456"), None)
        assert declared(inner.expression(FILL_KEY), "positiveDemandColor") == "#123456"
        assert declared(inner.expression(FILL_KEY), "negativeDemandColor") == "#a6cee3"
        assert inner.expression(FILL_KEY).startswith("if(@id is NULL, NULL, ")
        assert BASE_VALUE in inner.expression(FILL_KEY)
        assert outer.colorCalls == []

    def test_size_scales_both_symbols(self, monkeypatch):
        symbol, outer, inner = self._symbol()
        _dialog(monkeypatch, "qgisred_demands")._applyDemandsLegend(symbol, None, 3.2)
        assert declared(inner.expression(SIZE_KEY), "demandSize", isText=False) == "3.2"
        assert declared(inner.expression(SIZE_KEY), "negativeDemandSize", isText=False) == "7"
        assert outer.size() == 5.6 and inner.size() == 3.2


class TestMetersApplier:
    def _symbol(self):
        layers = [
            FakeSymbolLayer("SvgMarker", {FILL_KEY: meterFill(t), STROKE_KEY: METER_STROKE, WIDTH_KEY: meterSize(t)})
            for t in ("EnergySensor", "Flowmeter", "Manometer")
        ]
        return FakeSymbol(layers), layers

    def test_selected_type_changes_only_its_own_layer(self, monkeypatch):
        symbol, (energy, flow, mano) = self._symbol()
        _dialog(monkeypatch, "qgisred_meters", "Flowmeter")._applyMetersLegend(symbol, FakeHexColor("#123456"), 7)
        assert declared(flow.expression(FILL_KEY), "flowmeterMeterColor") == "#123456"
        assert declared(flow.expression(WIDTH_KEY), "flowmeterMeterSize", isText=False) == "7"
        assert energy.expression(FILL_KEY) == meterFill("EnergySensor")
        assert mano.expression(WIDTH_KEY) == meterSize("Manometer")
        for layer in (energy, flow, mano):
            assert layer.expression(STROKE_KEY) == METER_STROKE
            assert declared(layer.expression(FILL_KEY), "inactiveMeterColor") == "#cccccc"

    def test_all_types_set_every_color_and_size(self, monkeypatch):
        symbol, layers = self._symbol()
        _dialog(monkeypatch, "qgisred_meters")._applyMetersLegend(symbol, FakeHexColor("#123456"), 6.5)
        for layer, meterType in zip(layers, ("EnergySensor", "Flowmeter", "Manometer")):
            assert declared(layer.expression(FILL_KEY), meterStyleVariable(meterType, "Color")) == "#123456"
            assert declared(layer.expression(WIDTH_KEY), meterStyleVariable(meterType, "Size"), isText=False) == "6.5"
        # The Manometer NULL branch follows its own variable, the others stay hidden
        assert "if(@mt is NULL, @manometerMeterSize," in layers[2].expression(WIDTH_KEY)
        assert "if(@mt is NULL, 0," in layers[1].expression(WIDTH_KEY)


class TestServiceConnectionsApplier:
    def _symbol(self):
        expressions = {FILL_KEY: SERVICE_CONNECTION_FILL, STROKE_KEY: SERVICE_CONNECTION_STROKE}
        marker = FakeSymbolLayer("SimpleMarker", expressions, size=1.5)
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        line = FakeSymbolLayer("SimpleLine", {STROKE_KEY: SERVICE_CONNECTION_STROKE}, size=1.4)
        return FakeSymbol([line, markerLine]), line, marker

    def test_line_variant_colors_the_active_stroke_of_line_and_circle(self, monkeypatch):
        symbol, line, marker = self._symbol()
        color = FakeHexColor("#123456")
        _dialog(monkeypatch, "qgisred_serviceconnections", "line")._applyServiceConnectionsLegend(symbol, color, None)
        for expr in (line.expression(STROKE_KEY), marker.expression(STROKE_KEY)):
            assert declared(expr, "activeServiceConnectionColor") == "#123456"
            assert declared(expr, "inactiveServiceConnectionColor") == "#ff0f13"
        assert marker.expression(FILL_KEY) == SERVICE_CONNECTION_FILL
        assert line.colorCalls == [color] and marker.strokeColorCalls == [color] and marker.colorCalls == []

    def test_circle_variant_colors_the_active_demand_fill_only(self, monkeypatch):
        symbol, line, marker = self._symbol()
        color = FakeHexColor("#123456")
        _dialog(monkeypatch, "qgisred_serviceconnections", "circle")._applyServiceConnectionsLegend(symbol, color, None)
        assert declared(marker.expression(FILL_KEY), "activeDemandServiceConnectionColor") == "#123456"
        assert declared(marker.expression(FILL_KEY), "inactiveDemandServiceConnectionColor") == "#c7cbc5"
        assert declared(marker.expression(FILL_KEY), "noDemandServiceConnectionColor") == "#ffffff"
        assert line.expression(STROKE_KEY) == SERVICE_CONNECTION_STROKE
        assert marker.colorCalls == [color] and line.colorCalls == [] and marker.strokeColorCalls == []

    def test_size_scales_the_line_and_the_dot_together(self, monkeypatch):
        symbol, line, marker = self._symbol()
        _dialog(monkeypatch, "qgisred_serviceconnections", "line")._applyServiceConnectionsLegend(symbol, None, 2.8)
        assert line.width() == 2.8 and marker.size() == 3


class TestIsolationValvesApplier:
    def test_only_the_open_color_changes(self, monkeypatch):
        layer = FakeSymbolLayer(expressions={FILL_KEY: ISOLATION_VALVE_FILL_TEMPLATE})
        symbol = FakeSymbol([layer])
        color = FakeHexColor("#123456")
        _dialog(monkeypatch, "qgisred_isolationvalves")._applyIsolationValvesLegend(symbol, color, None)
        expr = layer.expression(FILL_KEY)
        assert declared(expr, "openIsolationValveColor") == "#123456"
        assert declared(expr, "closedIsolationValveColor") == "#ff1313"
        assert declared(expr, "lossIsolationValveColor") == "#f6b912"
        assert declared(expr, "unavailableIsolationValveColor") == "#7d8b8f"
        assert "coalesce(attribute($currentfeature,'IniStatus'),attribute($currentfeature,'Status'))" in expr
        assert symbol.baseColor is color  # panel icon follows the picked color

    def test_lost_expression_is_restored_with_the_picked_color(self, monkeypatch):
        layer = FakeSymbolLayer()
        _dialog(monkeypatch, "qgisred_isolationvalves")._applyIsolationValvesLegend(
            FakeSymbol([layer]), FakeHexColor("#123456"), None
        )
        restored = layer.expression(FILL_KEY)
        assert declared(restored, "openIsolationValveColor") == "#123456"
        assert "'CLOSED'" in restored and '"Available" != 0' in restored


class TestSourcesApplier:
    def test_only_the_selected_type_changes(self, monkeypatch):
        layer = FakeSymbolLayer(expressions={STROKE_KEY: SOURCE_STROKE})
        _dialog(monkeypatch, "qgisred_sources", "CONCEN")._applySourcesLegend(
            FakeSymbol([layer]), FakeHexColor("#123456"), None
        )
        expr = layer.expression(STROKE_KEY)
        assert declared(expr, "concenSourceColor") == "#123456"
        assert declared(expr, "massSourceColor") == "#d17123"
        assert declared(expr, "flowpacedSourceColor") == "#23d146"
        assert declared(expr, "setpointSourceColor") == "#cb0f96"
        assert declared(expr, "noQualitySourceColor") == "#9d979d"
        assert "with_variable('bq', coalesce(" in expr and "with_variable('st', coalesce(" in expr


class TestDemandsSwatchPreview:
    """The Multiple Demands swatch colors only the inner (expression-driven)
    circle; the decorative outer circle keeps its own color."""

    def _selector(self, monkeypatch):
        monkeypatch.setattr(customDialogsModule, "QgsProperty", FakeQgsProperty)
        # No fill-key patch needed: both modules read the same SL_PROP_FILL_COLOR shim.
        assert customDialogsModule.SL_PROP_FILL_COLOR == FILL_KEY
        return QGISRedSymbolColorSelector.__new__(QGISRedSymbolColorSelector)

    def test_only_the_inner_expression_layer_takes_the_color(self, monkeypatch):
        selector = self._selector(monkeypatch)
        outer = FakeSymbolLayer()
        inner = FakeSymbolLayer(expressions={FILL_KEY: DEMANDS_FILL})
        colored = selector.applyColorToExpressionLayers(FakeSymbol([outer, inner]), "PICKED")
        assert colored
        assert inner.colorCalls == ["PICKED"]
        assert outer.colorCalls == []
        # The preview clone drops the expression so the picked color is visible
        assert inner.expression(FILL_KEY) is None

    def test_reports_when_no_layer_carries_an_expression(self, monkeypatch):
        selector = self._selector(monkeypatch)
        assert selector.applyColorToExpressionLayers(FakeSymbol([FakeSymbolLayer()]), "PICKED") is False


class TestRuleFilters:
    """The five HydraulicSectorsLinks rule filters, including the ClosedLinks split."""

    @pytest.mark.parametrize("filterExpr, value", [
        ("\"Class\" = 'H-Q'", "H-Q"),
        ("\"Class\" = 'H-nQ'", "H-nQ"),
        ("\"Class\" = 'nH-Q'", "nH-Q"),
        ("\"Class\" = 'nH-nQ' AND \"SubNet\" <> 'ClosedLinks'", "nH-nQ"),
        ("\"Class\" = 'nH-nQ' AND \"SubNet\" = 'ClosedLinks'", "ClosedLinks"),
    ])
    def test_hydraulic_sectors_filters(self, filterExpr, value):
        assert parseCategoricalRuleFilter(filterExpr) == ("Class", value)

    @pytest.mark.parametrize("filterExpr", [
        "(Pressure) >= 0 AND (Pressure) <= 10",
        "ELSE",
        "",
        None,
        "\"Class\" IN ('a', 'b')",
    ])
    def test_non_categorical_filters_are_rejected(self, filterExpr):
        assert parseCategoricalRuleFilter(filterExpr) is None


class TestScaling:
    def test_tree_nodes_expression(self):
        assert scaleNumericLiterals("if(\"NodeType\" = 'Tank', 7, 0)", 1.5) == "if(\"NodeType\" = 'Tank', 10.5, 0)"

    def test_zero_branches_stay_zero(self):
        assert scaleNumericLiterals("if (EmittCoef>0, 0, 1.3)", 2) == "if (EmittCoef>0, 0, 2.6)"

    def test_quoted_values_are_not_scaled(self):
        assert scaleNumericLiterals("if(\"Type\" = 'Zone2', 4, 0)", 2) == "if(\"Type\" = 'Zone2', 8, 0)"

    def test_number_formatting(self):
        assert formatExpressionNumber(2.0) == "2"
        assert formatExpressionNumber(3.2000000001) == "3.2"
        assert formatExpressionNumber(10.5) == "10.5"
