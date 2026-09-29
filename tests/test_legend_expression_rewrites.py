# -*- coding: utf-8 -*-
"""In-place expression rewrites the legend editor applies to the shipped input styles.

Every editable colour/size is a with_variable() declaration at the top of the
expression. Fixtures are the exact expressions from defaults/layerStyles/*.qml.bak
(guarded below): the editor must change only the declared value it edits and keep
the rest of the expression untouched.
"""
import base64
import os
import xml.etree.ElementTree as ET

import pytest

import QGISRed.ui.project.qgisred_custom_dialogs as customDialogsModule
import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSymbolColorSelector
from QGISRed.ui.project.qgisred_legends_dialog import (
    ISOLATION_VALVE_FILL_TEMPLATE,
    QGISRedLegendsDialog,
    elementSizePattern,
    formatExpressionNumber,
    meterStyleVariable,
    parseCategoricalRuleFilter,
    scaleCapturedNumbers,
    scaleNumericLiterals,
    styleVariablePattern,
    substituteCapturedGroup,
)

from .conftest import REAL_QGIS

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_DEMAND = "coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseDemand'))"
BASE_VALUE = "coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseValue'))"
METER_TYPE = "coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type'))"

PIPE_COLOR = (
    "with_variable('openPipeColor', '#0f1291', with_variable('closedPipeColor', '#ff0f13', "
    "if(IniStatus is NULL, @openPipeColor, if(IniStatus != 'CLOSED', @openPipeColor, @closedPipeColor))))"
)
PIPE_CV_SIZE = "with_variable('cvPipeSize', 6, if(IniStatus is NULL, 0, if(IniStatus != 'CV', 0, @cvPipeSize)))"
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
    "with_variable('emitterJunctionSize', 2.7, with_variable('negativeDemandEmitterJunctionSize', 4, "
    "if(EmittCoef > 0, if(BaseDem is NULL, @emitterJunctionSize, if(BaseDem > 0, @emitterJunctionSize, "
    "if(BaseDem < 0, @negativeDemandEmitterJunctionSize, @emitterJunctionSize))), 0)))"
)
JUNCTION_BASE_SIZE = (
    "with_variable('junctionSize', 1.6, with_variable('negativeDemandJunctionSize', 3.5, "
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
SOURCE_SIZE = (
    "if(@id is NULL, NULL, with_variable('massSourceSize', 3, with_variable('flowpacedSourceSize', 3, "
    "with_variable('concenSourceSize', 3, with_variable('setpointSourceSize', 3, "
    "with_variable('st', coalesce(attribute($currentfeature,'SourceType'),attribute($currentfeature,'Type')), "
    "if(@st = 'MASS', @massSourceSize, if(@st = 'FLOWPACED', @flowpacedSourceSize, "
    "if(@st = 'CONCEN', @concenSourceSize, @setpointSourceSize)))))))))"
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


class FakeSvgLayer(FakeSymbolLayer):
    """An SvgMarker layer embedding an SVG whose root carries the given id (qgisred_water / qgisred_frame)."""

    def __init__(self, svgId, color="BASE"):
        super().__init__("SvgMarker", size=7)
        self._svgId = svgId
        self._color = color

    def path(self):
        svg = f'<svg id="{self._svgId}"></svg>'
        return "base64:" + base64.b64encode(svg.encode("utf-8")).decode("ascii")

    def color(self):
        return self._color


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
        assert declared(PIPE_CV_SIZE, "cvPipeSize", isText=False) == "6"
        assert declared(JUNCTION_EMITTER_SIZE, "emitterJunctionSize", isText=False) == "2.7"

    def test_each_pattern_matches_only_its_own_declaration(self):
        assert declared(PIPE_CV_SIZE, "openPipeColor") is None
        assert declared(PIPE_COLOR, "cvPipeSize", isText=False) is None
        assert declared(JUNCTION_BASE_SIZE, "junctionSize", isText=False) == "1.6"
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
        assert exprs == {"outlineColor": SOURCE_STROKE, "size": SOURCE_SIZE}

    @pytest.mark.parametrize("fileName", ["Reservoirs.qml.bak", "Tanks.qml.bak"])
    def test_reservoirs_and_tanks_stack_a_water_and_a_frame_svg(self, fileName):
        path = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", fileName)
        symbol = ET.parse(path).getroot().find("renderer-v2/symbols/symbol")
        svgIds = []
        for layerElement in symbol.findall("layer"):
            assert layerElement.get("class") == "SvgMarker"
            encoded = layerElement.find("Option/Option[@name='name']").get("value")
            content = base64.b64decode(encoded[len("base64:"):]).decode("utf-8")
            svgIds.append("qgisred_water" if 'id="qgisred_water"' in content else "qgisred_frame")
        assert svgIds == ["qgisred_water", "qgisred_frame"]

    def test_isolation_valves_match_the_repair_template(self):
        [(_, exprs, _)] = _rendererLayers("IsolationValves.qml.bak")
        assert exprs == {"fillColor": ISOLATION_VALVE_FILL_TEMPLATE}

    def test_service_connections(self):
        (_, lineExprs, _), (_, _, [(_, markerExprs, _)]) = _rendererLayers("ServiceConnections.qml.bak")
        assert lineExprs["outlineColor"] == SERVICE_CONNECTION_STROKE
        assert markerExprs == {"fillColor": SERVICE_CONNECTION_FILL, "outlineColor": SERVICE_CONNECTION_STROKE}

    def test_multiple_demands(self):
        (_, outerExprs, _), (_, innerExprs, _) = _rendererLayers("Demands.qml.bak")
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
        ("qgisred_pipes", "line", ("openPipeColor",)),
        ("qgisred_pipes", "marker", ("openPipeColor",)),
        ("qgisred_pumps", None, ("openPumpColor",)),
        ("qgisred_pumps", "marker", ("openPumpColor",)),
        ("qgisred_valves", None, ("openValveColor",)),
        ("qgisred_valves", "line", ("openValveColor",)),
        ("qgisred_junctions", None, ()),
        ("qgisred_junctions", "positive", ("positiveDemandJunctionColor",)),
        ("qgisred_junctions", "negative", ("negativeDemandJunctionColor",)),
        ("qgisred_demands", None, ("positiveDemandColor",)),
        ("qgisred_isolationvalves", None, ("openIsolationValveColor",)),
        ("qgisred_serviceconnections", None, ("activeServiceConnectionColor",)),
        ("qgisred_serviceconnections", "line", ("activeServiceConnectionColor",)),
        ("qgisred_serviceconnections", "circle", ("activeDemandServiceConnectionColor",)),
        ("qgisred_sources", None, ("massSourceColor", "flowpacedSourceColor", "concenSourceColor", "setpointSourceColor")),
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
        assert _dialog(monkeypatch, "qgisred_pipes", "line").inputSizeVariables("qgisred_pipes") == ()
        assert _dialog(monkeypatch, "qgisred_pipes", "marker").inputSizeVariables("qgisred_pipes") == ("cvPipeSize",)

    def test_junction_sizes_split_by_demand_sign_and_join_under_all(self, monkeypatch):
        assert _dialog(monkeypatch, "qgisred_junctions", "positive").inputSizeVariables("qgisred_junctions") == (
            "junctionSize", "emitterJunctionSize"
        )
        assert _dialog(monkeypatch, "qgisred_junctions", "negative").inputSizeVariables("qgisred_junctions") == (
            "negativeDemandJunctionSize", "negativeDemandEmitterJunctionSize"
        )
        assert len(_dialog(monkeypatch, "qgisred_junctions").inputSizeVariables("qgisred_junctions")) == 4

    def test_source_sizes_one_per_type_and_all_of_them_under_all_types(self, monkeypatch):
        assert _dialog(monkeypatch, "qgisred_sources", "CONCEN").inputSizeVariables("qgisred_sources") == (
            "concenSourceSize",
        )
        allTypes = _dialog(monkeypatch, "qgisred_sources").inputSizeVariables("qgisred_sources")
        assert allTypes[0] == "massSourceSize" and len(allTypes) == 4

    @pytest.mark.parametrize("identifier, variant, locked", [
        ("qgisred_sources", None, False),
        ("qgisred_sources", "MASS", False),
        ("qgisred_junctions", None, True),
        ("qgisred_junctions", "positive", False),
        ("qgisred_serviceconnections", None, False),
        ("qgisred_pipes", None, False),
        ("qgisred_meters", None, False),
        ("qgisred_meters", "Flowmeter", False),
        ("qgisred_tanks", None, False),
        ("qgisred_reservoirs", None, False),
        ("qgisred_tree_nodes", None, True),
        ("qgisred_tree_nodes", "junction", False),
        ("qgisred_tree_nodes", "root", False),
        ("qgisred_isolatedsegments_links", None, True),
    ])
    def test_color_lock_follows_the_selected_variant(self, monkeypatch, identifier, variant, locked):
        assert _dialog(monkeypatch, identifier, variant).isColorLocked() is locked

    def test_marker_component_covers_link_icons_and_the_demand_circle(self, monkeypatch):
        assert _dialog(monkeypatch, "qgisred_valves", "marker").isMarkerComponentSelected()
        assert _dialog(monkeypatch, "qgisred_serviceconnections", "circle").isMarkerComponentSelected()
        assert not _dialog(monkeypatch, "qgisred_serviceconnections", "line").isMarkerComponentSelected()
        assert not _dialog(monkeypatch, "qgisred_serviceconnections").isMarkerComponentSelected()

    def test_reads_the_marker_size_inside_the_marker_line(self, monkeypatch):
        marker = FakeSymbolLayer("SvgMarker", size=5)
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        symbol = FakeSymbol([FakeSymbolLayer("SimpleLine", size=1.5), markerLine])
        dialog = _dialog(monkeypatch, "qgisred_pumps", "marker")
        assert dialog._readMarkerLineMarkerSize(symbol) == 5
        assert dialog._markerLineSubSymbol(symbol) is markerLine.subSymbol()
        assert dialog._markerLineSubSymbol(FakeSymbol([FakeSymbolLayer("SimpleLine")])) is None
        assert dialog.isLinkMarkerComponentSelected()
        assert not _dialog(monkeypatch, "qgisred_pumps", "line").isLinkMarkerComponentSelected()
        assert not _dialog(monkeypatch, "qgisred_serviceconnections", "marker").isLinkMarkerComponentSelected()


class TestVariantItems:
    def _items(self, monkeypatch, identifier):
        dialog = _dialog(monkeypatch, identifier)
        dialog.tr = lambda text: text
        return dialog.inputVariantItems(identifier)

    @pytest.mark.parametrize("identifier", ["qgisred_pipes", "qgisred_pumps", "qgisred_valves"])
    def test_links_offer_all_line_and_marker(self, monkeypatch, identifier):
        label, items = self._items(monkeypatch, identifier)
        assert label == "Component"
        assert items == [("All", None), ("Line", "line"), ("Marker", "marker")]

    def test_sources_offer_all_types_first(self, monkeypatch):
        label, items = self._items(monkeypatch, "qgisred_sources")
        assert label == "Source Type"
        assert items[0] == ("All types", None)
        assert [data for _, data in items[1:]] == list(QGISRedLegendsDialog.SOURCE_TYPES)

    def test_junctions_offer_all_then_the_demand_signs(self, monkeypatch):
        label, items = self._items(monkeypatch, "qgisred_junctions")
        assert label == "Demand"
        assert items == [("All", None), ("Positive (> 0)", "positive"), ("Negative (< 0)", "negative")]

    def test_service_connections_offer_all_line_and_demand_circle(self, monkeypatch):
        label, items = self._items(monkeypatch, "qgisred_serviceconnections")
        assert label == "Component"
        assert items == [("All", None), ("Line", "line"), ("Demand circle", "circle")]

    @pytest.mark.parametrize("identifier", ["qgisred_reservoirs", "qgisred_tanks"])
    def test_reservoirs_and_tanks_have_no_selector(self, monkeypatch, identifier):
        assert self._items(monkeypatch, identifier) is None

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

    def test_reads_the_water_color_of_a_tank(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_tanks")
        symbol = FakeSymbol([FakeSvgLayer("qgisred_water", color="WATER"), FakeSvgLayer("qgisred_frame", color="FRAME")])
        assert dialog._readWaterMarkerColor(symbol) == "WATER"
        assert dialog._readWaterMarkerColor(FakeSymbol([FakeSvgLayer("qgisred_frame")])) is None


class FakeStyledLayer:
    def __init__(self, identifier, symbol, rendererType="singleSymbol"):
        self._identifier = identifier
        self._symbol = symbol
        self._rendererType = rendererType

    def customProperty(self, key):
        return self._identifier if key == "qgisred_identifier" else None

    def renderer(self):
        layer = self

        class _Renderer:
            def type(self):
                return layer._rendererType

            def symbol(self):
                return layer._symbol

        return _Renderer()


class TestEditableInputStyle:
    """Styles saved by older builds declare no variables: the editor restores the default first."""

    def test_the_shipped_declarations_are_editable(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_pipes")
        marker = FakeSymbolLayer("SvgMarker", {FILL_KEY: PIPE_COLOR, SIZE_KEY: PIPE_CV_SIZE})
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        symbol = FakeSymbol([FakeSymbolLayer("SimpleLine", {STROKE_KEY: PIPE_COLOR}), markerLine])
        assert dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_pipes", symbol))

    def test_a_legacy_expression_is_not(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_pipes")
        legacy = "if(IniStatus is NULL, '#0f1291', '#ff0f13')"
        symbol = FakeSymbol([FakeSymbolLayer("SimpleLine", {STROKE_KEY: legacy})])
        assert not dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_pipes", symbol))

    def test_every_declared_variable_must_be_there(self, monkeypatch):
        # A Sources style from before the per-type sizes has the colors but not the sizes
        dialog = _dialog(monkeypatch, "qgisred_sources")
        symbol = FakeSymbol([FakeSymbolLayer(expressions={STROKE_KEY: SOURCE_STROKE})])
        assert not dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_sources", symbol))
        symbol = FakeSymbol([FakeSymbolLayer(expressions={STROKE_KEY: SOURCE_STROKE, SIZE_KEY: SOURCE_SIZE})])
        assert dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_sources", symbol))

    def test_tanks_need_the_split_water_and_frame_icon(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_tanks")
        split = FakeSymbol([FakeSvgLayer("qgisred_water"), FakeSvgLayer("qgisred_frame")])
        assert dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_tanks", split))
        single = FakeSymbol([FakeSymbolLayer("SvgMarker")])
        assert not dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_tanks", single))

    def test_meters_check_every_type(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_meters")
        layers = [
            FakeSymbolLayer("SvgMarker", {FILL_KEY: meterFill(t), STROKE_KEY: METER_STROKE, WIDTH_KEY: meterSize(t)})
            for t in QGISRedLegendsDialog.METER_TYPES
        ]
        assert dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_meters", FakeSymbol(layers)))
        assert not dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_meters", FakeSymbol(layers[:-1])))

    def test_only_single_symbol_renderers_are_checked(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_pipes")
        assert dialog.hasEditableInputStyle(FakeStyledLayer("qgisred_pipes", FakeSymbol([]), "categorizedSymbol"))


# ---------------------------------------------------------------------------
# Appliers
# ---------------------------------------------------------------------------

class TestPipesApplier:
    def _apply(self, monkeypatch, color, size, component=None, cvSize=PIPE_CV_SIZE):
        marker = FakeSymbolLayer("SvgMarker", {FILL_KEY: PIPE_COLOR, SIZE_KEY: cvSize})
        markerLine = FakeSymbolLayer("MarkerLine", {WIDTH_KEY: cvSize}, subSymbol=FakeSymbol([marker]))
        line = FakeSymbolLayer("SimpleLine", {STROKE_KEY: PIPE_COLOR}, size=0.8)
        _dialog(monkeypatch, "qgisred_pipes", component)._applyPipesLegend(FakeSymbol([line, markerLine]), color, size)
        return line, markerLine, marker

    def test_line_component_changes_only_the_line(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, FakeHexColor("#123456"), 2.0, "line")
        assert line.width() == 2.0
        assert declared(line.expression(STROKE_KEY), "openPipeColor") == "#123456"
        assert marker.expression(FILL_KEY) == PIPE_COLOR
        assert markerLine.expression(WIDTH_KEY) == PIPE_CV_SIZE
        assert marker.expression(SIZE_KEY) == PIPE_CV_SIZE

    def test_marker_component_changes_only_the_cv_marker(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, FakeHexColor("#123456"), 7, "marker")
        assert line.width() == 0.8
        assert line.expression(STROKE_KEY) == PIPE_COLOR
        assert declared(marker.expression(FILL_KEY), "openPipeColor") == "#123456"
        for expr in (markerLine.expression(WIDTH_KEY), marker.expression(SIZE_KEY)):
            assert declared(expr, "cvPipeSize", isText=False) == "7"

    def test_color_reaches_the_line_stroke_and_the_cv_marker_fill(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, FakeHexColor("#123456"), None)
        for expr in (line.expression(STROKE_KEY), marker.expression(FILL_KEY)):
            assert declared(expr, "openPipeColor") == "#123456"
            assert declared(expr, "closedPipeColor") == "#ff0f13"
        assert markerLine.expression(WIDTH_KEY) == PIPE_CV_SIZE
        assert line.width() == 0.8

    def test_size_sets_the_line_width_and_scales_both_cv_declarations(self, monkeypatch):
        line, markerLine, marker = self._apply(monkeypatch, None, 1.6)
        assert line.width() == 1.6
        for expr in (markerLine.expression(WIDTH_KEY), marker.expression(SIZE_KEY)):
            assert declared(expr, "cvPipeSize", isText=False) == "12"
            assert expr.endswith("if(IniStatus is NULL, 0, if(IniStatus != 'CV', 0, @cvPipeSize)))")
        assert line.expression(STROKE_KEY) == PIPE_COLOR

    def test_an_untouched_width_keeps_the_cv_size(self, monkeypatch):
        _line, markerLine, _marker = self._apply(monkeypatch, None, 0.8)
        assert markerLine.expression(WIDTH_KEY) == PIPE_CV_SIZE

    def test_a_cv_size_the_user_chose_keeps_its_proportion_to_the_line(self, monkeypatch):
        # It used to be rebuilt from the shipped 5 mm, throwing the user's own size away.
        ownCvSize = PIPE_CV_SIZE.replace("'cvPipeSize', 6,", "'cvPipeSize', 7,")
        _line, markerLine, marker = self._apply(monkeypatch, None, 1.6, cvSize=ownCvSize)
        for expr in (markerLine.expression(WIDTH_KEY), marker.expression(SIZE_KEY)):
            assert declared(expr, "cvPipeSize", isText=False) == "14"


PUMPS_AND_VALVES = pytest.mark.parametrize("identifier, colorExpr, applier, variable, fixed", [
    ("qgisred_pumps", PUMP_COLOR, "_applyPumpsLegend", "openPumpColor", ("closedPumpColor",)),
    ("qgisred_valves", VALVE_COLOR, "_applyValvesLegend", "openValveColor",
     ("closedValveColor", "activeValveColor")),
])


class TestPumpsAndValvesApplier:
    def _apply(self, monkeypatch, identifier, colorExpr, applier, component=None, markerSize=5, size=1.6):
        marker = FakeSymbolLayer("SvgMarker", {FILL_KEY: colorExpr}, size=markerSize)
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        line = FakeSymbolLayer("SimpleLine", {STROKE_KEY: colorExpr}, size=0.8)
        dialog = _dialog(monkeypatch, identifier, component)
        getattr(dialog, applier)(FakeSymbol([line, markerLine]), FakeHexColor("#123456"), size)
        return line, marker

    @PUMPS_AND_VALVES
    def test_only_the_open_color_changes_on_line_and_marker(self, monkeypatch, identifier, colorExpr, applier, variable,
                                                            fixed):
        line, marker = self._apply(monkeypatch, identifier, colorExpr, applier)
        for expr in (line.expression(STROKE_KEY), marker.expression(FILL_KEY)):
            assert declared(expr, variable) == "#123456"
            for name in fixed:
                assert declared(expr, name) == declared(colorExpr, name)
        assert line.width() == 1.6
        assert marker.size() == 10  # the line doubled, so did the icon on it

    @PUMPS_AND_VALVES
    def test_an_icon_size_the_user_chose_keeps_its_proportion_to_the_line(self, monkeypatch, identifier, colorExpr,
                                                                         applier, variable, fixed):
        # It used to be rebuilt from the shipped 5 mm, throwing the user's own size away.
        _line, marker = self._apply(monkeypatch, identifier, colorExpr, applier, markerSize=8)
        assert marker.size() == 16

    @PUMPS_AND_VALVES
    def test_an_untouched_width_leaves_the_icon_alone(self, monkeypatch, identifier, colorExpr, applier, variable,
                                                      fixed):
        line, marker = self._apply(monkeypatch, identifier, colorExpr, applier, markerSize=8, size=0.8)
        assert (line.width(), marker.size()) == (0.8, 8)

    @PUMPS_AND_VALVES
    def test_line_component_leaves_the_marker_alone(self, monkeypatch, identifier, colorExpr, applier, variable, fixed):
        line, marker = self._apply(monkeypatch, identifier, colorExpr, applier, "line")
        assert line.width() == 1.6
        assert declared(line.expression(STROKE_KEY), variable) == "#123456"
        assert marker.size() == 5
        assert marker.expression(FILL_KEY) == colorExpr

    @PUMPS_AND_VALVES
    def test_marker_component_leaves_the_line_alone(self, monkeypatch, identifier, colorExpr, applier, variable, fixed):
        line, marker = self._apply(monkeypatch, identifier, colorExpr, applier, "marker")
        assert line.width() == 0.8
        assert line.expression(STROKE_KEY) == colorExpr
        assert marker.size() == 1.6
        assert declared(marker.expression(FILL_KEY), variable) == "#123456"


class TestJunctionsApplier:
    def _symbol(self):
        emitter = FakeSymbolLayer(expressions={FILL_KEY: JUNCTION_COLOR, SIZE_KEY: JUNCTION_EMITTER_SIZE}, size=1.6)
        base = FakeSymbolLayer(expressions={FILL_KEY: JUNCTION_COLOR, SIZE_KEY: JUNCTION_BASE_SIZE}, size=1.6)
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

    def test_all_scales_every_size_variable_from_the_shown_one(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions")._applyJunctionsLegend(symbol, None, 3.2)
        assert declared(base.expression(SIZE_KEY), "junctionSize", isText=False) == "3.2"
        assert declared(base.expression(SIZE_KEY), "negativeDemandJunctionSize", isText=False) == "7"
        assert declared(emitter.expression(SIZE_KEY), "emitterJunctionSize", isText=False) == "5.4"
        assert declared(emitter.expression(SIZE_KEY), "negativeDemandEmitterJunctionSize", isText=False) == "8"
        assert emitter.size() == base.size() == 3.2  # base sizes follow, for the legend icon
        assert emitter.expression(SIZE_KEY).endswith("@emitterJunctionSize))), 0)))")

    def test_all_never_takes_a_color(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions")._applyJunctionsLegend(symbol, FakeHexColor("#123456"), None)
        assert emitter.expression(FILL_KEY) == JUNCTION_COLOR and base.expression(FILL_KEY) == JUNCTION_COLOR

    def test_positive_scenario_scales_the_positive_sizes_only(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "positive")._applyJunctionsLegend(symbol, None, 3.2)
        assert declared(base.expression(SIZE_KEY), "junctionSize", isText=False) == "3.2"
        assert declared(base.expression(SIZE_KEY), "negativeDemandJunctionSize", isText=False) == "3.5"
        assert declared(emitter.expression(SIZE_KEY), "emitterJunctionSize", isText=False) == "5.4"
        assert declared(emitter.expression(SIZE_KEY), "negativeDemandEmitterJunctionSize", isText=False) == "4"
        assert emitter.size() == base.size() == 3.2

    def test_negative_scenario_scales_the_negative_sizes_only(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "negative")._applyJunctionsLegend(symbol, None, 7.0)
        assert declared(base.expression(SIZE_KEY), "negativeDemandJunctionSize", isText=False) == "7"
        assert declared(base.expression(SIZE_KEY), "junctionSize", isText=False) == "1.6"
        assert declared(emitter.expression(SIZE_KEY), "negativeDemandEmitterJunctionSize", isText=False) == "8"
        assert declared(emitter.expression(SIZE_KEY), "emitterJunctionSize", isText=False) == "2.7"
        assert emitter.size() == base.size() == 1.6  # the panel icon keeps the positive size

    def test_an_untouched_size_is_a_no_op(self, monkeypatch):
        symbol, emitter, base = self._symbol()
        _dialog(monkeypatch, "qgisred_junctions", "positive")._applyJunctionsLegend(symbol, None, 1.6)
        assert base.expression(SIZE_KEY) == JUNCTION_BASE_SIZE and emitter.expression(SIZE_KEY) == JUNCTION_EMITTER_SIZE


class TestDemandsApplier:
    def _symbol(self):
        outer = FakeSymbolLayer(size=3.2)
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
        assert outer.size() == 6.4 and inner.size() == 3.2


class TestMetersApplier:
    METER_TYPES = ("Countermeter", "Flowmeter", "Manometer")

    def _symbol(self):
        layers = [
            FakeSymbolLayer("SvgMarker", {FILL_KEY: meterFill(t), STROKE_KEY: METER_STROKE, WIDTH_KEY: meterSize(t)})
            for t in self.METER_TYPES
        ]
        return FakeSymbol(layers), layers

    def _declaredSize(self, layer, meterType):
        return declared(layer.expression(WIDTH_KEY), meterStyleVariable(meterType, "Size"), isText=False)

    def test_selected_type_changes_only_its_own_layer(self, monkeypatch):
        symbol, (counter, flow, mano) = self._symbol()
        _dialog(monkeypatch, "qgisred_meters", "Flowmeter")._applyMetersLegend(symbol, FakeHexColor("#123456"), 7)
        assert declared(flow.expression(FILL_KEY), "flowmeterMeterColor") == "#123456"
        assert self._declaredSize(flow, "Flowmeter") == "7"
        assert counter.expression(FILL_KEY) == meterFill("Countermeter")
        assert mano.expression(WIDTH_KEY) == meterSize("Manometer")
        for layer in (counter, flow, mano):
            assert layer.expression(STROKE_KEY) == METER_STROKE
            assert declared(layer.expression(FILL_KEY), "inactiveMeterColor") == "#cccccc"

    def test_all_types_take_one_color_and_scale_every_size(self, monkeypatch):
        symbol, layers = self._symbol()
        _dialog(monkeypatch, "qgisred_meters", "Flowmeter")._applyMetersLegend(symbol, None, 10)
        _dialog(monkeypatch, "qgisred_meters")._applyMetersLegend(symbol, FakeHexColor("#123456"), 6.5)
        for layer, meterType in zip(layers, self.METER_TYPES):
            assert declared(layer.expression(FILL_KEY), meterStyleVariable(meterType, "Color")) == "#123456"
        # 5 mm to 6.5 mm is 130 %: the type the user had made larger stays larger
        assert [self._declaredSize(layer, t) for layer, t in zip(layers, self.METER_TYPES)] == ["6.5", "13", "6.5"]
        # The Manometer NULL branch follows its own variable, the others stay hidden
        assert "if(@mt is NULL, @manometerMeterSize," in layers[2].expression(WIDTH_KEY)
        assert "if(@mt is NULL, 0," in layers[1].expression(WIDTH_KEY)

    def test_all_types_left_at_the_current_size_change_nothing(self, monkeypatch):
        symbol, layers = self._symbol()
        _dialog(monkeypatch, "qgisred_meters", "Flowmeter")._applyMetersLegend(symbol, None, 10)
        _dialog(monkeypatch, "qgisred_meters")._applyMetersLegend(symbol, None, 5)
        assert [self._declaredSize(layer, t) for layer, t in zip(layers, self.METER_TYPES)] == ["5", "10", "5"]


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

    def test_all_colors_the_strokes_and_softens_the_circle_fill(self, monkeypatch):
        monkeypatch.setattr(legendsModule, "softenColor", lambda color: FakeHexColor("#abcdef"))
        symbol, line, marker = self._symbol()
        color = FakeHexColor("#123456")
        _dialog(monkeypatch, "qgisred_serviceconnections")._applyServiceConnectionsLegend(symbol, color, None)
        for expr in (line.expression(STROKE_KEY), marker.expression(STROKE_KEY)):
            assert declared(expr, "activeServiceConnectionColor") == "#123456"
        assert declared(marker.expression(FILL_KEY), "activeDemandServiceConnectionColor") == "#abcdef"
        assert declared(marker.expression(FILL_KEY), "inactiveDemandServiceConnectionColor") == "#c7cbc5"
        assert line.colorCalls == [color] and marker.strokeColorCalls == [color]
        assert [c.name() for c in marker.colorCalls] == ["#abcdef"]

    def test_all_scales_the_line_and_the_circle_together(self, monkeypatch):
        symbol, line, marker = self._symbol()
        _dialog(monkeypatch, "qgisred_serviceconnections")._applyServiceConnectionsLegend(symbol, None, 2.8)
        assert line.width() == 2.8 and marker.size() == 3

    def test_line_variant_resizes_the_line_only(self, monkeypatch):
        symbol, line, marker = self._symbol()
        _dialog(monkeypatch, "qgisred_serviceconnections", "line")._applyServiceConnectionsLegend(symbol, None, 2.8)
        assert line.width() == 2.8 and marker.size() == 1.5

    def test_circle_variant_resizes_the_circle_only(self, monkeypatch):
        symbol, line, marker = self._symbol()
        _dialog(monkeypatch, "qgisred_serviceconnections", "circle")._applyServiceConnectionsLegend(symbol, None, 3)
        assert line.width() == 1.4 and marker.size() == 3


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

    def _symbol(self):
        layer = FakeSymbolLayer(expressions={STROKE_KEY: SOURCE_STROKE, SIZE_KEY: SOURCE_SIZE}, size=3)
        return FakeSymbol([layer]), layer

    def test_one_type_takes_its_own_size(self, monkeypatch):
        symbol, layer = self._symbol()
        _dialog(monkeypatch, "qgisred_sources", "CONCEN")._applySourcesLegend(symbol, None, 5)
        expr = layer.expression(SIZE_KEY)
        assert declared(expr, "concenSourceSize", isText=False) == "5"
        for name in ("massSourceSize", "flowpacedSourceSize", "setpointSourceSize"):
            assert declared(expr, name, isText=False) == "3"
        assert expr.startswith("if(@id is NULL, NULL, ") and expr.endswith("@setpointSourceSize)))))))))")
        assert layer.size() == 3  # the panel icon follows All types only

    def test_all_types_scale_every_type_from_the_size_it_has(self, monkeypatch):
        symbol, layer = self._symbol()
        # Types already differ: 3 mm to 6 mm is 200 %, which each type takes from its own size
        _dialog(monkeypatch, "qgisred_sources", "CONCEN")._applySourcesLegend(symbol, None, 4)
        _dialog(monkeypatch, "qgisred_sources")._applySourcesLegend(symbol, None, 6)
        expr = layer.expression(SIZE_KEY)
        for name in ("massSourceSize", "flowpacedSourceSize", "setpointSourceSize"):
            assert declared(expr, name, isText=False) == "6"
        assert declared(expr, "concenSourceSize", isText=False) == "8"
        assert layer.size() == 6
        assert layer.expression(STROKE_KEY) == SOURCE_STROKE

    def test_all_types_left_at_the_current_size_change_nothing(self, monkeypatch):
        symbol, layer = self._symbol()
        _dialog(monkeypatch, "qgisred_sources", "CONCEN")._applySourcesLegend(symbol, None, 4)
        changed = layer.expression(SIZE_KEY)
        _dialog(monkeypatch, "qgisred_sources")._applySourcesLegend(symbol, None, 3)
        assert layer.expression(SIZE_KEY) == changed and layer.size() == 3

    def test_all_types_take_one_uniform_color(self, monkeypatch):
        symbol, layer = self._symbol()
        _dialog(monkeypatch, "qgisred_sources")._applySourcesLegend(symbol, FakeHexColor("#123456"), None)
        expr = layer.expression(STROKE_KEY)
        for name in ("massSourceColor", "flowpacedSourceColor", "concenSourceColor", "setpointSourceColor"):
            assert declared(expr, name) == "#123456"
        assert declared(expr, "noQualitySourceColor") == "#9d979d"
        assert layer.expression(SIZE_KEY) == SOURCE_SIZE


class TestMetersColorApplier:
    def _symbol(self):
        layers = [FakeSymbolLayer("SvgMarker", expressions={FILL_KEY: meterFill(t)}) for t in ("Flowmeter", "Manometer")]
        return FakeSymbol(layers), layers

    def test_one_type_colors_its_own_layer_only(self, monkeypatch):
        symbol, (flowmeter, manometer) = self._symbol()
        _dialog(monkeypatch, "qgisred_meters", "Flowmeter")._applyMetersLegend(symbol, FakeHexColor("#123456"), None)
        assert declared(flowmeter.expression(FILL_KEY), "flowmeterMeterColor") == "#123456"
        assert manometer.expression(FILL_KEY) == meterFill("Manometer")

    def test_all_types_take_one_uniform_color(self, monkeypatch):
        symbol, (flowmeter, manometer) = self._symbol()
        _dialog(monkeypatch, "qgisred_meters")._applyMetersLegend(symbol, FakeHexColor("#123456"), None)
        assert declared(flowmeter.expression(FILL_KEY), "flowmeterMeterColor") == "#123456"
        assert declared(manometer.expression(FILL_KEY), "manometerMeterColor") == "#123456"
        assert declared(manometer.expression(FILL_KEY), "inactiveMeterColor") == "#cccccc"


class TestProportionalSizeDiscard:
    """Leaving Proportional to Value drops the scale_polynomial expression on Apply, nothing else."""

    PROPORTIONAL = 'coalesce(scale_polynomial("Pressure", minimum("Pressure"), maximum("Pressure"), 1, 5, 0.57), 1)'

    def test_only_the_proportional_expression_goes(self, monkeypatch):
        proportional = FakeSymbolLayer(expressions={SIZE_KEY: self.PROPORTIONAL, FILL_KEY: JUNCTION_COLOR})
        junction = FakeSymbolLayer(expressions={SIZE_KEY: JUNCTION_BASE_SIZE})
        _dialog(monkeypatch, "qgisred_node_pressure").clearProportionalSizeExpression(FakeSymbol([proportional, junction]))
        assert proportional.expression(SIZE_KEY) is None
        assert proportional.expression(FILL_KEY) == JUNCTION_COLOR
        assert junction.expression(SIZE_KEY) == JUNCTION_BASE_SIZE

    def test_line_widths_are_cleared_too(self, monkeypatch):
        line = FakeSymbolLayer("SimpleLine", expressions={legendsModule.SL_PROP_STROKE_WIDTH: self.PROPORTIONAL})
        _dialog(monkeypatch, "qgisred_link_flow").clearProportionalSizeExpression(FakeSymbol([line]))
        assert line.expression(legendsModule.SL_PROP_STROKE_WIDTH) is None


class TestWaterMarkerApplier:
    """Reservoirs and tanks: the color fills the water half of the icon, the frame stays as it is."""

    def test_color_reaches_the_water_layer_only(self, monkeypatch):
        water, frame = FakeSvgLayer("qgisred_water"), FakeSvgLayer("qgisred_frame")
        dialog = _dialog(monkeypatch, "qgisred_reservoirs")
        dialog._applyWaterMarkerLegend(FakeSymbol([water, frame]), "PICKED", None)
        assert water.colorCalls == ["PICKED"] and frame.colorCalls == []

    def test_size_goes_through_the_whole_symbol(self, monkeypatch):
        dialog = _dialog(monkeypatch, "qgisred_tanks")
        dialog.sizes = []
        dialog.applySizeToSymbol = lambda symbol, size: dialog.sizes.append(size)
        dialog._applyWaterMarkerLegend(FakeSymbol([FakeSvgLayer("qgisred_water")]), None, 9)
        assert dialog.sizes == [9]


class FakeTreeMarker(FakeSymbolLayer):
    """A Tree nodes SimpleMarker layer (circle or star) sized by its node type."""

    def __init__(self, name, nodeType, literal, size):
        super().__init__(expressions={SIZE_KEY: f"if(\"NodeType\" = '{nodeType}', {literal}, 0)"}, size=size)
        self._name = name

    def properties(self):
        return {"name": self._name}


class TestTreeNodesApplier:
    def _symbol(self):
        circle = FakeTreeMarker("circle", "Junction", 2, 2)
        star = FakeTreeMarker("star", "ROOT", 8, 4)
        return FakeSymbol([circle, star]), circle, star

    def test_junctions_color_the_circle_stroke_and_size_the_circle_only(self, monkeypatch):
        symbol, circle, star = self._symbol()
        _dialog(monkeypatch, "qgisred_tree_nodes", "junction")._applyTreeNodesLegend(symbol, "PICKED", 3)
        assert circle.strokeColorCalls == ["PICKED"] and circle.colorCalls == []
        assert circle.expression(SIZE_KEY) == "if(\"NodeType\" = 'Junction', 3, 0)" and circle.size() == 3
        assert star.expression(SIZE_KEY) == "if(\"NodeType\" = 'ROOT', 8, 0)" and star.size() == 4

    def test_root_node_colors_the_star_fill_and_sizes_the_star_only(self, monkeypatch):
        symbol, circle, star = self._symbol()
        _dialog(monkeypatch, "qgisred_tree_nodes", "root")._applyTreeNodesLegend(symbol, "PICKED", 12)
        assert star.colorCalls == ["PICKED"] and star.strokeColorCalls == []
        assert star.expression(SIZE_KEY) == "if(\"NodeType\" = 'ROOT', 12, 0)" and star.size() == 6
        assert circle.expression(SIZE_KEY) == "if(\"NodeType\" = 'Junction', 2, 0)" and circle.size() == 2

    def test_all_scales_every_node_from_the_circle_and_keeps_colors(self, monkeypatch):
        symbol, circle, star = self._symbol()
        _dialog(monkeypatch, "qgisred_tree_nodes")._applyTreeNodesLegend(symbol, "PICKED", 4)
        assert circle.colorCalls == circle.strokeColorCalls == star.colorCalls == []
        assert circle.expression(SIZE_KEY) == "if(\"NodeType\" = 'Junction', 4, 0)" and circle.size() == 4
        assert star.expression(SIZE_KEY) == "if(\"NodeType\" = 'ROOT', 16, 0)" and star.size() == 8

    def test_an_untouched_size_is_a_no_op(self, monkeypatch):
        symbol, circle, star = self._symbol()
        _dialog(monkeypatch, "qgisred_tree_nodes", "root")._applyTreeNodesLegend(symbol, None, 8)
        assert star.size() == 4 and circle.size() == 2

    def test_reads_the_size_of_the_selected_node(self, monkeypatch):
        symbol, _circle, _star = self._symbol()
        assert _dialog(monkeypatch, "qgisred_tree_nodes", "root")._readAnchorSize(symbol) == 8
        assert _dialog(monkeypatch, "qgisred_tree_nodes", "junction")._readAnchorSize(symbol) == 2
        assert _dialog(monkeypatch, "qgisred_tree_nodes")._readAnchorSize(symbol) == 2


class TestFactorCell:
    """With the selector on All the size cell shows a percent of the sizes the layer is drawn with."""

    def _dialog(self, monkeypatch, identifier, variant=None, fieldType="single"):
        dialog = _dialog(monkeypatch, identifier, variant)
        dialog.currentFieldType = fieldType
        return dialog

    @pytest.mark.parametrize("identifier, variant, fieldType, expected", [
        ("qgisred_pipes", None, "single", True),
        ("qgisred_pipes", "line", "single", False),
        ("qgisred_junctions", None, "single", True),
        ("qgisred_junctions", "positive", "single", False),
        ("qgisred_meters", None, "single", True),
        ("qgisred_tree_nodes", None, "single", True),
        ("qgisred_tree_nodes", "root", "single", False),
        ("qgisred_isolatedsegments_links", None, "single", True),
        ("qgisred_isolatedsegments_links", "PUMP", "single", False),
        ("qgisred_isolatedsegments_nodes", None, "categorical", False),
        ("qgisred_demands", None, "single", False),
        ("qgisred_tanks", None, "single", False),
        ("qgisred_pipes", None, "numeric", False),
    ])
    def test_which_cells_show_a_percent(self, monkeypatch, identifier, variant, fieldType, expected):
        assert self._dialog(monkeypatch, identifier, variant, fieldType).isFactorCell() is expected

    def test_a_layer_shows_a_percent_exactly_when_it_has_a_selector(self, monkeypatch):
        identifiers = QGISRedLegendsDialog.INPUT_LAYER_IDENTIFIERS | QGISRedLegendsDialog.EDITABLE_QUERY_IDENTIFIERS
        for identifier in identifiers:
            dialog = self._dialog(monkeypatch, identifier)
            dialog.tr = lambda text: text
            assert (dialog.inputVariantItems(identifier) is not None) == dialog.isFactorCell(), identifier

    def test_the_percent_of_a_link_stands_for_its_line_width(self, monkeypatch):
        marker = FakeSymbolLayer("SvgMarker", size=6)
        markerLine = FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([marker]))
        symbol = FakeSymbol([FakeSymbolLayer("SimpleLine", size=0.8), markerLine])
        assert self._dialog(monkeypatch, "qgisred_pumps").currentSymbolSize(symbol, "line") == 0.8
        assert self._dialog(monkeypatch, "qgisred_pumps", "marker").currentSymbolSize(symbol, "line") == 6

    def test_the_percent_of_the_junctions_stands_for_the_size_they_declare(self, monkeypatch):
        symbol = FakeSymbol([FakeSymbolLayer(expressions={SIZE_KEY: JUNCTION_BASE_SIZE}, size=1.6)])
        assert self._dialog(monkeypatch, "qgisred_junctions").currentSymbolSize(symbol, "marker") == 1.6

    def test_the_percent_of_the_tree_nodes_stands_for_the_junction_circle(self, monkeypatch):
        symbol = FakeSymbol([FakeTreeMarker("circle", "Junction", 2, 2), FakeTreeMarker("star", "ROOT", 8, 4)])
        assert self._dialog(monkeypatch, "qgisred_tree_nodes").currentSymbolSize(symbol, "marker") == 2


ISOLATED_LINK_TYPE = "coalesce(attribute($currentfeature,'LinkType'),attribute($currentfeature,'ElemType'))"
ISOLATED_NODE_TYPE = "coalesce(attribute($currentfeature,'NodeType'),attribute($currentfeature,'ElemType'))"
ISOLATED_DEMANDS_SIZE = (
    "CASE WHEN \"ElemType\" = 'JUNCTION' THEN 3 WHEN \"ElemType\" = 'CONNECTION' THEN 2 ELSE 2 END"
)
STROKE_WIDTH_KEY = legendsModule.SL_PROP_STROKE_WIDTH


def isolatedLinkSize(linkType, size):
    return f"if(@id is NULL, NULL, if({ISOLATED_LINK_TYPE}='{linkType}', {size}, 0))"


def isolatedIconSize(nodeType, size):
    return f"if(@id is NULL, NULL, if({ISOLATED_NODE_TYPE} ='{nodeType}', {size}, 0))"


def isolatedMarkerSize(nodeType, size):
    return f"if(@id is NULL, NULL, if({ISOLATED_NODE_TYPE} !='{nodeType}', 0,{size}))"


def inOneLine(expression):
    return " ".join(expression.split())


class TestShippedElementStyles:
    """The element selector reads the sizes out of exactly these shipped expressions."""

    def test_isolated_segments_links(self):
        connectionLine, connectionCircle, pipeLine, pump, valve = _rendererLayers("IsolatedSegmentsLinks.qml.bak")
        assert connectionLine[1]["outlineWidth"] == isolatedLinkSize("SERVICECONNECTION", 1.1)
        assert connectionCircle[2][0][1]["size"] == isolatedLinkSize("SERVICECONNECTION", 2)
        assert pipeLine[0] == "SimpleLine" and "outlineWidth" not in pipeLine[1]
        assert pump[2][0][1]["size"] == isolatedLinkSize("PUMP", 6)
        assert valve[2][0][1]["size"] == isolatedLinkSize("VALVE", 6)


    @pytest.mark.parametrize("fileName", [
        "IsolatedSegmentsIsolatedDemands.qml.bak", "HydraulicSectorsIsolatedDemands.qml.bak",
    ])
    def test_isolated_demands(self, fileName):
        [(_, exprs, _)] = _rendererLayers(fileName)
        assert inOneLine(exprs["size"]) == ISOLATED_DEMANDS_SIZE


class TestElementSizePattern:
    @pytest.mark.parametrize("expression, elementType, size", [
        (isolatedLinkSize("PUMP", 6), "PUMP", "6"),
        (isolatedLinkSize("SERVICECONNECTION", 1.1), "SERVICECONNECTION", "1.1"),
        (ISOLATED_DEMANDS_SIZE, "JUNCTION", "3"),
        (ISOLATED_DEMANDS_SIZE, "CONNECTION", "2"),
    ])
    def test_captures_the_size_of_the_element_type(self, expression, elementType, size):
        match = elementSizePattern(elementType).search(expression)
        assert match.group(match.lastindex) == size

    def test_another_element_type_is_not_matched(self):
        assert elementSizePattern("VALVE").search(isolatedLinkSize("PUMP", 6)) is None
        assert elementSizePattern("PIPE").search(ISOLATED_DEMANDS_SIZE) is None

    def test_scaling_changes_the_size_of_that_element_type_only(self):
        scaled = scaleCapturedNumbers(ISOLATED_DEMANDS_SIZE, elementSizePattern("CONNECTION"), 1.5)
        assert scaled == ISOLATED_DEMANDS_SIZE.replace("'CONNECTION' THEN 2", "'CONNECTION' THEN 3")
        scaled = scaleCapturedNumbers(isolatedLinkSize("PUMP", 6), elementSizePattern("PUMP"), 1.25)
        assert scaled == isolatedLinkSize("PUMP", 7.5)


class TestElementsApplier:
    """Isolated Segments: the Element selector resizes one element type and leaves the others."""

    def _links(self):
        connectionCircle = FakeSymbolLayer(expressions={SIZE_KEY: isolatedLinkSize("SERVICECONNECTION", 2)}, size=2)
        pump = FakeSymbolLayer("SvgMarker", {SIZE_KEY: isolatedLinkSize("PUMP", 6)}, size=6)
        valve = FakeSymbolLayer("SvgMarker", {SIZE_KEY: isolatedLinkSize("VALVE", 6)}, size=6)
        layers = {
            "connectionLine": FakeSymbolLayer(
                "SimpleLine", {STROKE_WIDTH_KEY: isolatedLinkSize("SERVICECONNECTION", 1.1)}, size=1.4),
            "connectionCircle": connectionCircle,
            "pipeLine": FakeSymbolLayer("SimpleLine", size=1.4),
            "pump": pump,
            "valve": valve,
        }
        symbol = FakeSymbol([
            layers["connectionLine"],
            FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([connectionCircle])),
            layers["pipeLine"],
            FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([pump])),
            FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([valve])),
        ])
        return symbol, layers

    def _apply(self, monkeypatch, identifier, elementType, symbol, color=None, size=None):
        _dialog(monkeypatch, identifier, elementType)._applyElementsLegend(symbol, color, size)

    @pytest.mark.parametrize("elementType, size", [
        ("PIPE", 1.4), ("SERVICECONNECTION", 1.1), ("PUMP", 6), ("VALVE", 6), (None, None),
    ])
    def test_reads_the_size_of_each_link_element(self, monkeypatch, elementType, size):
        dialog = _dialog(monkeypatch, "qgisred_isolatedsegments_links", elementType)
        assert dialog._readAnchorSize(self._links()[0]) == size

    def test_pumps_resize_their_icon_only(self, monkeypatch):
        symbol, layers = self._links()
        self._apply(monkeypatch, "qgisred_isolatedsegments_links", "PUMP", symbol, size=9)
        assert layers["pump"].expression(SIZE_KEY) == isolatedLinkSize("PUMP", 9) and layers["pump"].size() == 9
        assert layers["valve"].expression(SIZE_KEY) == isolatedLinkSize("VALVE", 6) and layers["valve"].size() == 6
        assert layers["pipeLine"].width() == 1.4

    def test_service_connections_resize_their_line_and_keep_the_circle_in_proportion(self, monkeypatch):
        symbol, layers = self._links()
        self._apply(monkeypatch, "qgisred_isolatedsegments_links", "SERVICECONNECTION", symbol, size=2.2)
        assert layers["connectionLine"].expression(STROKE_WIDTH_KEY) == isolatedLinkSize("SERVICECONNECTION", 2.2)
        assert layers["connectionCircle"].expression(SIZE_KEY) == isolatedLinkSize("SERVICECONNECTION", 4)
        assert layers["pipeLine"].width() == 1.4 and layers["pump"].size() == 6

    def test_pipes_resize_the_line_no_expression_gates(self, monkeypatch):
        symbol, layers = self._links()
        self._apply(monkeypatch, "qgisred_isolatedsegments_links", "PIPE", symbol, size=2.8)
        assert layers["pipeLine"].width() == 2.8
        assert layers["connectionLine"].width() == 1.4
        assert layers["connectionLine"].expression(STROKE_WIDTH_KEY) == isolatedLinkSize("SERVICECONNECTION", 1.1)

    def test_an_untouched_size_is_a_no_op(self, monkeypatch):
        pump = FakeSymbolLayer("SvgMarker", {SIZE_KEY: isolatedLinkSize("PUMP", 6)}, size=2)
        symbol = FakeSymbol([FakeSymbolLayer("MarkerLine", subSymbol=FakeSymbol([pump]))])
        self._apply(monkeypatch, "qgisred_isolatedsegments_links", "PUMP", symbol, size=6)
        assert pump.expression(SIZE_KEY) == isolatedLinkSize("PUMP", 6)
        assert pump.size() == 2

    def test_the_status_colors_of_an_element_stay(self, monkeypatch):
        symbol, layers = self._links()
        self._apply(monkeypatch, "qgisred_isolatedsegments_links", "PUMP", symbol, color="PICKED")
        assert layers["pump"].colorCalls == layers["pump"].strokeColorCalls == []

    def test_isolated_demands_resize_one_element_and_color_their_ring_under_all(self, monkeypatch):
        ring = FakeSymbolLayer(expressions={SIZE_KEY: ISOLATED_DEMANDS_SIZE}, size=3)
        identifier = "qgisred_isolatedsegments_isolateddemands"
        self._apply(monkeypatch, identifier, "CONNECTION", FakeSymbol([ring]), color="PICKED", size=3)
        assert ring.expression(SIZE_KEY) == ISOLATED_DEMANDS_SIZE.replace("'CONNECTION' THEN 2", "'CONNECTION' THEN 3")
        assert ring.size() == 3 and ring.strokeColorCalls == []  # the panel icon follows the junctions
        self._apply(monkeypatch, identifier, "JUNCTION", FakeSymbol([ring]), size=4.5)
        assert "'JUNCTION' THEN 4.5" in ring.expression(SIZE_KEY) and ring.size() == 4.5
        self._apply(monkeypatch, identifier, None, FakeSymbol([ring]), color="PICKED")
        assert ring.strokeColorCalls == ["PICKED"] and ring.colorCalls == []

    @pytest.mark.parametrize("identifier, elementType, locked", [
        ("qgisred_isolatedsegments_links", "PUMP", True),
        ("qgisred_isolatedsegments_links", None, True),
        ("qgisred_isolatedsegments_isolateddemands", None, False),
        ("qgisred_isolatedsegments_isolateddemands", "JUNCTION", True),
        ("qgisred_hydraulicsectors_isolateddemands", None, False),
    ])
    def test_only_the_fixed_colors_can_be_picked(self, monkeypatch, identifier, elementType, locked):
        assert _dialog(monkeypatch, identifier, elementType).isColorLocked() is locked


def _shippedClasses(fileName):
    """(renderer element, [(value, label, [layer elements])]) of a shipped categorized legend."""
    path = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", fileName)
    renderer = ET.parse(path).getroot().find("renderer-v2")
    symbols = {symbol.get("name"): symbol for symbol in renderer.findall("symbols/symbol")}
    classes = [
        (category.get("value"), category.get("label"), symbols[category.get("symbol")].findall("layer"))
        for category in renderer.findall("categories/category")
    ]
    return renderer, classes


def _option(layerElement, name):
    return layerElement.find("Option/Option[@name='%s']" % name).get("value")


def _optionColor(layerElement, name):
    red, green, blue = _option(layerElement, name).split(",")[:3]
    return "#%02x%02x%02x" % (int(red), int(green), int(blue))


def _embeddedSvg(layerElement):
    return base64.b64decode(_option(layerElement, "name")[len("base64:"):]).decode("utf-8")


ISOLATED_NODES_STYLE = "IsolatedSegmentsNodes.qml.bak"
ISOLATED_NODES_CLASS = (
    "with_variable('nodeType', " + ISOLATED_NODE_TYPE + ", "
    "with_variable('status', attribute($currentfeature,'Status'), "
    "CASE WHEN @nodeType = 'ISOLATIONVALVE' AND @status IN "
    "('NOW CLOSED', 'TO RECOVER', 'OPEN', 'TO CLOSE', 'NOT AVAILABLE', 'TO OPEN') "
    "THEN @nodeType || ' ' || @status "
    "WHEN @nodeType = 'JUNCTION' AND @status = 'TO RECOVER' THEN @nodeType || ' ' || @status "
    "ELSE @nodeType END))"
)
# (class, marker, color of the part the class edits, size): what the single symbol of older
# builds drew for each node type and status
ISOLATED_NODE_CLASSES = [
    ("JUNCTION", "circle", "#ff9900", 2),
    ("JUNCTION TO RECOVER", "circle", "#e7ca65", 2),
    ("ISOLATIONVALVE NOW CLOSED", "circle", "#ff0f13", 2),
    ("ISOLATIONVALVE TO RECOVER", "circle", "#e7ca65", 2),
    ("ISOLATIONVALVE OPEN", "circle", "#12b425", 2),
    ("ISOLATIONVALVE TO CLOSE", "circle", "#ff00ff", 2),
    ("ISOLATIONVALVE NOT AVAILABLE", "circle", "#7d8b8f", 2),
    ("ISOLATIONVALVE TO OPEN", "circle", "#00ffee", 2),
    ("ISOLATIONVALVE", "circle", "#0f1291", 2),
    ("TANK", "icon", "#ff00ff", 7),
    ("RESERVOIR", "icon", "#ff00ff", 7),
    ("INCIDENCE", "star", "#d7b419", 6),
]
ISOLATED_NODE_COLORS = {value: color for value, _marker, color, _size in ISOLATED_NODE_CLASSES}
COLOR_PARTS = QGISRedLegendsDialog.ISOLATED_NODE_COLOR_PARTS
FRAME_SHADE = "#9f009f"


def colorPartOf(classValue):
    return COLOR_PARTS[classValue.split(" ")[0]]


class FakeClassTable:
    """The rows of a categorized legend, each a {column: widget}."""

    def __init__(self, rows):
        self.rows = rows

    def rowCount(self):
        return len(self.rows)

    def cellWidget(self, row, column):
        return self.rows[row].get(column)


class FakeCellContainer:
    """The widget a cell centers its swatch in."""

    def __init__(self, widget):
        self.widget = widget

    def findChild(self, widgetClass):
        return self.widget if isinstance(self.widget, widgetClass) else None


class TestShippedIsolatedNodesLegend:
    """Isolated Segments nodes: one class per node type and status, each with its marker."""

    def test_it_classifies_the_node_type_and_the_status(self):
        renderer, _classes = _shippedClasses(ISOLATED_NODES_STYLE)
        assert renderer.get("type") == "categorizedSymbol"
        assert renderer.get("attr") == ISOLATED_NODES_CLASS

    def test_the_classes_carry_the_names_the_plugin_translates(self):
        _renderer, classes = _shippedClasses(ISOLATED_NODES_STYLE)
        utils = QGISRedStylingUtils("", "")
        utils.tr = lambda text: text
        assert [value for value, _label, _layers in classes] == [entry[0] for entry in ISOLATED_NODE_CLASSES]
        assert {value: label for value, label, _layers in classes} == utils.isolatedNodeClassNames()

    def test_every_node_type_says_which_part_its_color_paints(self):
        nodeTypes = {value.split(" ")[0] for value, _marker, _color, _size in ISOLATED_NODE_CLASSES}
        assert nodeTypes == set(COLOR_PARTS)

    @pytest.mark.parametrize("value, marker, color, size", ISOLATED_NODE_CLASSES)
    def test_each_class_draws_its_marker_at_its_size(self, value, marker, color, size):
        layers = next(layers for shipped, _label, layers in _shippedClasses(ISOLATED_NODES_STYLE)[1] if shipped == value)
        if marker == "icon":
            assert [layer.get("class") for layer in layers] == ["SvgMarker", "SvgMarker"]
        else:
            assert [(layer.get("class"), _option(layer, "name")) for layer in layers] == [("SimpleMarker", marker)]
        assert [float(_option(layer, "size")) for layer in layers] == [size] * len(layers)
        assert [_dataDefinedExpressions(layer) for layer in layers] == [{}] * len(layers)

    @pytest.mark.parametrize("value, marker, color, size", ISOLATED_NODE_CLASSES)
    def test_each_class_is_colored_on_the_part_the_editor_edits(self, value, marker, color, size):
        layers = next(layers for shipped, _label, layers in _shippedClasses(ISOLATED_NODES_STYLE)[1] if shipped == value)
        colorPart = colorPartOf(value)
        if colorPart == "water":
            water, frame = layers
            assert 'id="qgisred_water"' in _embeddedSvg(water) and 'id="qgisred_frame"' in _embeddedSvg(frame)
            assert (_optionColor(water, "color"), _optionColor(frame, "color")) == (color, FRAME_SHADE)
            return
        fill, stroke = _optionColor(layers[0], "color"), _optionColor(layers[0], "outline_color")
        expected = {"stroke": ("#ffffff", color), "fillAndStroke": (color, color), "fill": (color, "#000000")}
        assert (fill, stroke) == expected[colorPart]


class FakePickedColor:
    def darker(self, factor):
        return ("darker", factor)


class TestIsolatedNodesColorParts:
    """The color of a class paints one part of its marker: what the swatch previews and Apply writes."""

    def _dialog(self, monkeypatch, identifier=QGISRedLegendsDialog.ISOLATED_NODES_IDENTIFIER):
        return _dialog(monkeypatch, identifier)

    @pytest.mark.parametrize("value", [entry[0] for entry in ISOLATED_NODE_CLASSES])
    def test_a_class_goes_by_its_node_type(self, monkeypatch, value):
        assert self._dialog(monkeypatch).classColorPart(value) == colorPartOf(value)

    def test_the_classes_of_any_other_layer_have_no_part(self, monkeypatch):
        assert self._dialog(monkeypatch, "qgisred_hydraulicsectors_nodes").classColorPart("JUNCTION") is None
        assert self._dialog(monkeypatch).classColorPart("Other Values") is None

    @pytest.mark.parametrize("colorPart, fills, strokes", [
        ("stroke", [], ["PICKED"]),
        ("fill", ["PICKED"], []),
        ("fillAndStroke", ["PICKED"], ["PICKED"]),
    ])
    def test_a_plain_marker_takes_the_color_on_that_part_only(self, monkeypatch, colorPart, fills, strokes):
        marker = FakeSymbolLayer()
        self._dialog(monkeypatch).applyMarkerPartColor(FakeSymbol([marker]), "PICKED", colorPart)
        assert (marker.colorCalls, marker.strokeColorCalls) == (fills, strokes)

    def test_an_icon_takes_the_color_on_its_water_and_a_darker_shade_on_its_frame(self, monkeypatch):
        water, frame = FakeSvgLayer("qgisred_water"), FakeSvgLayer("qgisred_frame")
        picked = FakePickedColor()
        self._dialog(monkeypatch).applyMarkerPartColor(FakeSymbol([water, frame]), picked, "water")
        assert water.colorCalls == [picked] and frame.colorCalls == [("darker", 160)]

    def test_the_nodes_are_no_longer_a_single_symbol_with_a_selector(self, monkeypatch):
        dialog = self._dialog(monkeypatch)
        dialog.tr = lambda text: text
        assert dialog.inputVariantItems(QGISRedLegendsDialog.ISOLATED_NODES_IDENTIFIER) is None
        assert not dialog.isSizeOnlyQueryLayer() and not dialog.isElementLayer() and not dialog.isColorLocked()


@pytest.mark.skipif(not REAL_QGIS, reason="reads and paints the symbols QGIS builds from the shipped style")
class TestIsolatedNodesLegendInQgis:
    STYLE_PATH = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", ISOLATED_NODES_STYLE)

    def _layer(self, typeField="NodeType"):
        from qgis.core import QgsVectorLayer
        uri = "Point?crs=EPSG:3857&field=Id:string&field=%s:string&field=Status:string" % typeField
        layer = QgsVectorLayer(uri, "nodes", "memory")
        layer.setCustomProperty("qgisred_identifier", QGISRedLegendsDialog.ISOLATED_NODES_IDENTIFIER)
        self._dialogOn(layer).loadStyleKeepingLabelVisibility(self.STYLE_PATH)
        return layer

    def _dialogOn(self, layer):
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.currentLayer = layer
        return dialog

    def test_loading_the_style_keeps_the_identity_of_the_layer(self):
        # The file was saved with no custom properties: QGIS drops the ones of the layer it lands on
        layer = self._layer()
        assert layer.renderer().type() == "categorizedSymbol"
        assert layer.customProperty("qgisred_identifier") == QGISRedLegendsDialog.ISOLATED_NODES_IDENTIFIER

    def _classSymbols(self, layer):
        return [(category.value(), category.symbol().clone()) for category in layer.renderer().categories()]

    @pytest.mark.parametrize("typeField", ["NodeType", "ElemType"])
    @pytest.mark.parametrize("nodeType, status, expected", [
        ("JUNCTION", "ISOLATED", "JUNCTION"),
        ("JUNCTION", None, "JUNCTION"),
        ("JUNCTION", "TO RECOVER", "JUNCTION TO RECOVER"),
        ("ISOLATIONVALVE", "NOW CLOSED", "ISOLATIONVALVE NOW CLOSED"),
        ("ISOLATIONVALVE", "TO RECOVER", "ISOLATIONVALVE TO RECOVER"),
        ("ISOLATIONVALVE", "OPEN", "ISOLATIONVALVE OPEN"),
        ("ISOLATIONVALVE", "TO CLOSE", "ISOLATIONVALVE TO CLOSE"),
        ("ISOLATIONVALVE", "NOT AVAILABLE", "ISOLATIONVALVE NOT AVAILABLE"),
        ("ISOLATIONVALVE", "TO OPEN", "ISOLATIONVALVE TO OPEN"),
        ("ISOLATIONVALVE", "CLOSED", "ISOLATIONVALVE"),
        ("ISOLATIONVALVE", None, "ISOLATIONVALVE"),
        ("TANK", "TO RECOVER", "TANK"),
        ("RESERVOIR", None, "RESERVOIR"),
        ("INCIDENCE", None, "INCIDENCE"),
    ])
    def test_each_node_falls_in_the_class_of_its_type_and_status(self, typeField, nodeType, status, expected):
        from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, QgsFeature
        layer = self._layer(typeField)
        feature = QgsFeature(layer.fields())
        feature.setAttributes(["1", nodeType, status])
        context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        context.setFeature(feature)
        expression = QgsExpression(layer.renderer().classAttribute())
        assert expression.evaluate(context) == expected
        assert not expression.hasEvalError(), expression.evalErrorString()

    def test_the_swatch_shows_the_color_each_class_is_drawn_with(self):
        layer = self._layer()
        dialog = self._dialogOn(layer)
        shown = {
            value: dialog.readMarkerPartColor(symbol, dialog.classColorPart(value)).name()
            for value, symbol in self._classSymbols(layer)
        }
        assert shown == ISOLATED_NODE_COLORS

    def test_a_picked_color_paints_its_part_and_reads_back(self):
        from qgis.PyQt.QtGui import QColor
        layer = self._layer()
        dialog = self._dialogOn(layer)
        picked = QColor("#123456")
        for value, symbol in self._classSymbols(layer):
            colorPart = dialog.classColorPart(value)
            dialog.applyClassColor(symbol, value, picked)
            assert dialog.readMarkerPartColor(symbol, colorPart).name() == "#123456", value
            first = symbol.symbolLayer(0)
            if colorPart == "stroke":
                assert first.color().name() == "#ffffff", value
            elif colorPart == "fill":
                assert first.strokeColor().name() == "#000000", value
            elif colorPart == "fillAndStroke":
                assert first.color().name() == first.strokeColor().name() == "#123456", value
            else:
                assert symbol.symbolLayer(1).color().name() == picked.darker(160).name(), value

    def test_the_swatch_previews_what_apply_paints(self):
        from qgis.PyQt.QtGui import QColor
        layer = self._layer()
        dialog = self._dialogOn(layer)
        for value, symbol in self._classSymbols(layer):
            colorPart = dialog.classColorPart(value)
            applied = symbol.clone()
            dialog.applyClassColor(applied, value, QColor("#123456"))
            shown = []

            class RecordingSwatch(QGISRedSymbolColorSelector):
                def setSymbol(self, previewSymbol):
                    shown.append(previewSymbol.clone())

            RecordingSwatch(
                None, "marker", QColor("#123456"), actualSymbol=symbol,
                colorApplier=lambda preview, picked, part=colorPart: dialog.applyMarkerPartColor(preview, picked, part),
            )
            previewed = shown[-1]
            for index in range(applied.symbolLayerCount()):
                drawn, shown = applied.symbolLayer(index), previewed.symbolLayer(index)
                assert shown.color().name() == drawn.color().name(), value
                assert shown.strokeColor().name() == drawn.strokeColor().name(), value

    def test_apply_paints_the_picked_color_on_the_part_of_each_class(self):
        from qgis.PyQt.QtGui import QColor
        from qgis.PyQt.QtWidgets import QLineEdit
        layer = self._layer()
        dialog = self._dialogOn(layer)
        dialog.tr = lambda text: text
        dialog._sourceRuleRenderer = None
        dialog.discardProportionalSizes = False
        dialog.currentSizeMode = lambda: "Manual"
        dialog.currentFieldName = layer.renderer().classAttribute()
        rows = []
        for value, symbol in self._classSymbols(layer):
            swatch = QGISRedSymbolColorSelector(None, "marker", QColor("#123456"), actualSymbol=symbol)
            rows.append({1: FakeCellContainer(swatch), 2: QLineEdit("3"), 3: QLineEdit(value), 4: QLineEdit(value)})
        dialog.tableView = FakeClassTable(rows)

        renderer = dialog.buildCategoricalRenderer()

        assert [category.value() for category in renderer.categories()] == list(ISOLATED_NODE_COLORS)
        for category in renderer.categories():
            colorPart = dialog.classColorPart(category.value())
            assert dialog.readMarkerPartColor(category.symbol(), colorPart).name() == "#123456", category.value()
            if colorPart == "stroke":
                assert category.symbol().symbolLayer(0).color().name() == "#ffffff", category.value()

    def _shoutedClassNames(self, monkeypatch):
        monkeypatch.setattr(QGISRedStylingUtils, "tr", lambda utils, text: text.upper())
        return [name.upper() for name in QGISRedStylingUtils("", "").isolatedNodeClassNames().values()]

    def test_a_loaded_style_shows_the_classes_in_the_language_of_the_user(self, monkeypatch):
        expected = self._shoutedClassNames(monkeypatch)
        layer = self._layer()
        dialog = self._dialogOn(layer)
        dialog.restoreResultNullClass = lambda: None
        dialog.showAppliedLayerStyle = lambda: None

        dialog.applyStyleFileToLayer(self.STYLE_PATH)

        assert [category.label() for category in layer.renderer().categories()] == expected

    def test_the_single_symbol_of_an_older_version_gets_the_shipped_legend_back(self, monkeypatch):
        from qgis.core import QgsMarkerSymbol, QgsSingleSymbolRenderer
        expected = self._shoutedClassNames(monkeypatch)
        layer = self._layer()
        layer.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "circle"})))
        dialog = self._dialogOn(layer)
        dialog.pluginFolder = PLUGIN_ROOT
        assert dialog.hasLegacySingleSymbol(layer)

        dialog.restoreEditableInputStyle()

        assert not dialog.hasLegacySingleSymbol(layer)
        assert [category.value() for category in layer.renderer().categories()] == list(ISOLATED_NODE_COLORS)
        assert [category.label() for category in layer.renderer().categories()] == expected
        assert dialog.restoredLegacyStyle


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
