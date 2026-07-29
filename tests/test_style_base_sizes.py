# -*- coding: utf-8 -*-
"""Sizes the Appearance factors scale against.

They used to be constants copied from the shipped QML files, so with a style of one's own
a factor of 1.0 meant "back to the factory sizes" instead of "leave it as the style drew
it". Now they are read from the style itself.
"""
from unittest.mock import MagicMock

import pytest

from QGISRed.ui.analysis.qgisred_results_rendering import (
    _ResultsRenderingMixin, read_node_base_sizes,
    _BASE_PIPE_WIDTH, _BASE_ARROW_SIZE, _BASE_JUNCTION_SIZE, _BASE_SPECIAL_SIZE,
    _BASE_VALVE_PUMP_SIZE,
)

LAYER_PATH = "C:/proj/Results/Net_Base_Link.shp"
LINE, POINT = 1, 0


class _BaseSizesDock(_ResultsRenderingMixin):
    def __init__(self):
        self.Renders = {}
        self._renderKeyInUse = {}
        self._styleBaseSizes = {}
        self._watchedLayers = set()
        self._writingOwnStyle = 0
        self._statsMode = False
        self._currentStat = None

    def getLayerPath(self, layer):
        return LAYER_PATH


def _layer(geometryType):
    layer = MagicMock()
    layer.geometryType.return_value = geometryType
    return layer


def _dataDefinedSub(expression):
    """A marker-line symbol layer whose sub-symbol carries a data-defined size."""
    prop = MagicMock()
    prop.isActive.return_value = True
    prop.expressionString.return_value = expression
    sub = MagicMock()
    sub.dataDefinedSize.return_value = prop
    symbolLayer = MagicMock()
    symbolLayer.subSymbol.return_value = sub
    return symbolLayer


def _nodeSymbolLayer(expression):
    prop = MagicMock()
    prop.isActive.return_value = True
    prop.expressionString.return_value = expression
    symbolLayer = MagicMock()
    symbolLayer.dataDefinedProperties.return_value.property.return_value = prop
    return symbolLayer


def _renderer(symbolLayers, width=None):
    symbol = MagicMock()
    symbol.symbolLayerCount.return_value = len(symbolLayers)
    symbol.symbolLayer.side_effect = lambda i: symbolLayers[i] if i < len(symbolLayers) else None
    if width is not None:
        symbolLayers[0].width.return_value = width
    renderer = MagicMock()
    renderer.symbols.return_value = [symbol]
    return renderer


class TestReadNodeBaseSizes:
    """Every shape _build_node_size_expr writes has to be readable back."""

    def test_tank_only_carries_the_special_size(self):
        assert read_node_base_sizes('if("Type" =\'TANK\', 7.0, 0)') == (None, 7.0)

    def test_reservoir_only_carries_the_special_size(self):
        assert read_node_base_sizes('if("Type" =\'RESERVOIR\', 9, 0)') == (None, 9.0)

    def test_the_combined_form_carries_the_junction_size_last(self):
        assert read_node_base_sizes('if("Type" =\'RESERVOIR\' or "Type"=\'TANK\', 0, 2.5)') == (2.5, None)

    def test_a_bare_number_is_the_junction_size(self):
        assert read_node_base_sizes("3.0") == (3.0, None)

    def test_a_proportional_expression_yields_nothing_rather_than_a_guess(self):
        junction, special = read_node_base_sizes('scale_linear("Pressure", 0, 50, 2, 4)')

        assert (junction, special) == (None, None)


class TestReadStyleBaseSizes:
    def test_a_line_style_states_pipe_icon_and_arrow_sizes(self):
        dock = _BaseSizesDock()
        renderer = _renderer([
            MagicMock(),                                             # 0 pipe line
            _dataDefinedSub("if(\"Type\"='PUMP', 6.0, 0)"),          # 1 pump icon
            _dataDefinedSub("if(\"Type\"='VALVE', 6.0, 0)"),         # 2 valve icon
            _dataDefinedSub("if(\"Type\"='PIPE', if(Flow>0,3.0,0),0)"),   # 3 arrow
            _dataDefinedSub("if(\"Type\"='PIPE', if(Flow<0,3.0,0),0)"),   # 4 arrow
        ], width=0.4)

        sizes = dock.readStyleBaseSizes(_layer(LINE), renderer)

        assert sizes == {"pipe": 0.4, "valvePump": 6.0, "arrow": 3.0}

    def test_a_node_style_states_junction_and_special_sizes(self):
        dock = _BaseSizesDock()
        renderer = _renderer([
            _nodeSymbolLayer('if("Type" =\'RESERVOIR\' or "Type"=\'TANK\', 0, 2.5)'),
            _nodeSymbolLayer('if("Type" =\'TANK\', 8.0, 0)'),
        ])

        sizes = dock.readStyleBaseSizes(_layer(POINT), renderer)

        assert sizes == {"junction": 2.5, "special": 8.0}

    def test_a_renderer_with_no_symbols_states_nothing(self):
        dock = _BaseSizesDock()
        renderer = MagicMock()
        renderer.symbols.return_value = []

        assert dock.readStyleBaseSizes(_layer(LINE), renderer) == {}


class TestBaseSizesFor:
    def test_without_a_reading_the_shipped_values_are_used(self):
        # Keeps every path that never loaded a style behaving exactly as before.
        dock = _BaseSizesDock()

        assert dock.baseSizesFor(_layer(LINE)) == {
            "pipe": _BASE_PIPE_WIDTH,
            "arrow": _BASE_ARROW_SIZE,
            "junction": _BASE_JUNCTION_SIZE,
            "special": _BASE_SPECIAL_SIZE,
            "valvePump": _BASE_VALVE_PUMP_SIZE,
        }

    def test_what_the_style_states_wins_over_the_shipped_value(self):
        dock = _BaseSizesDock()
        dock._renderKeyInUse[LAYER_PATH] = dock._getRenderStorageKey(LAYER_PATH, "Velocity")
        renderer = _renderer([MagicMock()], width=1.5)

        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", renderer)

        base = dock.baseSizesFor(_layer(LINE))
        assert base["pipe"] == 1.5
        assert base["arrow"] == _BASE_ARROW_SIZE, "sizes the style is silent about keep their fallback"

    def test_each_variable_keeps_its_own_reading(self):
        # Velocity and Flow load different QML files, which may state different sizes.
        dock = _BaseSizesDock()
        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", _renderer([MagicMock()], width=1.5))
        dock.rememberStyleBaseSizes(_layer(LINE), "Flow", _renderer([MagicMock()], width=0.3))

        dock._renderKeyInUse[LAYER_PATH] = dock._getRenderStorageKey(LAYER_PATH, "Flow")

        assert dock.baseSizesFor(_layer(LINE))["pipe"] == 0.3

    @pytest.mark.parametrize("factor, expected", [(1.0, 1.5), (2.0, 3.0), (0.5, 0.75)])
    def test_a_factor_of_one_leaves_the_style_alone(self, factor, expected):
        # This is the whole point: 1.0 used to snap a 1.5 mm pipe back to 0.26 mm.
        dock = _BaseSizesDock()
        dock._renderKeyInUse[LAYER_PATH] = dock._getRenderStorageKey(LAYER_PATH, "Velocity")
        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", _renderer([MagicMock()], width=1.5))

        assert round(dock.baseSizesFor(_layer(LINE))["pipe"] * factor, 6) == expected

    def test_clearing_the_cache_forgets_the_readings_too(self):
        dock = _BaseSizesDock()
        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", _renderer([MagicMock()], width=1.5))

        dock.clearRenderCache()

        assert dock._styleBaseSizes == {}


class TestStylesSetFromOutside:
    """The legend editor and QGIS's symbology panel edit what is drawn, factors included.

    Their numbers are base × factor, so the factor has to be divided back out; reading them
    as-is is what would make symbols grow on every pass.
    """

    def _dock(self, pipeFactor=2.0):
        dock = _BaseSizesDock()
        dock._pipeFactor = pipeFactor
        dock._renderKeyInUse[LAYER_PATH] = dock._getRenderStorageKey(LAYER_PATH, "Velocity")
        return dock

    def test_the_factor_is_divided_back_out(self):
        dock = self._dock(pipeFactor=2.0)
        # Style base 0.26 with factor 2 is drawn at 0.52; that is what the editor shows.
        drawn = _renderer([MagicMock()], width=0.52)

        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", drawn, scaled=True)

        assert dock.baseSizesFor(_layer(LINE))["pipe"] == 0.26

    def test_leaving_the_size_alone_changes_nothing_on_the_map(self):
        dock = self._dock(pipeFactor=2.0)
        drawn = _renderer([MagicMock()], width=0.52)

        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", drawn, scaled=True)

        assert dock.baseSizesFor(_layer(LINE))["pipe"] * dock._pipeFactor == 0.52

    def test_what_the_user_types_is_what_gets_drawn(self):
        dock = self._dock(pipeFactor=2.0)
        typed = _renderer([MagicMock()], width=1.0)

        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", typed, scaled=True)

        assert dock.baseSizesFor(_layer(LINE))["pipe"] * dock._pipeFactor == 1.0

    def test_our_own_writes_are_ignored(self):
        # applySymbolScaleFactors writes base × factor; taking that as the base would
        # square the factor on the next pass.
        dock = self._dock(pipeFactor=2.0)
        dock.rememberStyleBaseSizes(_layer(LINE), "Velocity", _renderer([MagicMock()], width=0.26))
        layer = _layer(LINE)
        layer.renderer.return_value = _renderer([MagicMock()], width=0.52)

        with dock.writingOwnStyle():
            dock.onLayerRendererChanged(layer)

        assert dock.baseSizesFor(layer)["pipe"] == 0.26

    def test_an_outside_change_is_picked_up(self):
        dock = self._dock(pipeFactor=2.0)
        layer = _layer(LINE)
        layer.renderer.return_value = _renderer([MagicMock()], width=0.52)

        dock.onLayerRendererChanged(layer)

        assert dock.baseSizesFor(layer)["pipe"] == 0.26

    def test_a_layer_we_never_styled_is_ignored(self):
        dock = _BaseSizesDock()
        layer = _layer(LINE)
        layer.renderer.return_value = _renderer([MagicMock()], width=0.52)

        dock.onLayerRendererChanged(layer)

        assert dock._styleBaseSizes == {}

    def test_a_layer_is_only_watched_once(self):
        dock = _BaseSizesDock()
        layer = _layer(LINE)
        layer.id.return_value = "layer-1"

        dock.watchRendererChanges(layer)
        dock.watchRendererChanges(layer)

        assert layer.rendererChanged.connect.call_count == 1
