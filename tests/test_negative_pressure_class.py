# -*- coding: utf-8 -*-
"""The negative-pressure class draws its junctions larger, and the Appearance factors keep it so.

NodePressureSI/US give the class below zero a white 2.5 mm junction while the other
classes use 2 mm. applySymbolScaleFactors writes absolute sizes into every rule, so it
has to carry that difference per class; the grey "no value" rule and a proportional
on/off toggle must not flatten or inflate it either.
"""
import os
import re

import pytest
from unittest.mock import MagicMock, patch

from QGISRed.tests.conftest import REAL_QGIS
from QGISRed.ui.analysis.qgisred_results_rendering import _ResultsRenderingMixin

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESSURE_STYLE = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", "NodePressureSI.qml.bak")
LAYER_PATH = "C:/proj/Results/Net_Base_Node.shp"


class _SizesDock(_ResultsRenderingMixin):
    def __init__(self):
        self.Renders = {}
        self._renderKeyInUse = {}
        self._styleBaseSizes = {}
        self._watchedLayers = set()
        self._writingOwnStyle = 0
        self._statsMode = False
        self._currentStat = None
        self._symbolFactor = 1.0
        self._specialFactor = 1.0
        self._pipeFactor = 1.0
        self._valvePumpFactor = 1.0
        self._arrowFactor = 1.0
        self._proportional = False
        self._nodeBorder = False
        self.displayingNodeField = "Pressure"
        self.displayingLinkField = None
        self.iface = None

    def tr(self, text):
        return text

    def getLayerPath(self, layer):
        return LAYER_PATH


def _junctionSizes(layer):
    """Junction size literal written in each rule, in rule order (None for the grey rule's label)."""
    from QGISRed.compat import SL_PROP_SIZE

    sizes = []
    for rule in layer.renderer().rootRule().children():
        circle = rule.symbol().symbolLayer(4)
        expression = circle.dataDefinedProperties().property(SL_PROP_SIZE).expressionString()
        match = re.search(r"0,\s*([\d.]+)\)+\s*$", expression)
        sizes.append((rule.label(), float(match.group(1)) if match else expression))
    return sizes


@pytest.fixture
def pressureLayer():
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY
    from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

    layer = QgsVectorLayer("Point?crs=EPSG:3857&field=NodeType:string&field=Pressure:double", "nodes", "memory")
    features = []
    for index, (nodeType, pressure) in enumerate((("JUNCTION", -2.0), ("JUNCTION", 25.0), ("TANK", 60.0))):
        feature = QgsFeature(layer.fields())
        feature.setAttribute("NodeType", nodeType)
        feature.setAttribute("Pressure", pressure)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    assert layer.loadNamedStyle(PRESSURE_STYLE)[1]
    return layer, QGISRedStylingUtils()


def _dockOnFreshStyle(layer, utils):
    """What setGraduatedPalette does around the sizes: remember the base, then the grey rule."""
    dock = _SizesDock()
    dock._renderKeyInUse[LAYER_PATH] = dock._getRenderStorageKey(LAYER_PATH, "Pressure")
    dock.rememberStyleBaseSizes(layer, "Pressure", layer.renderer())
    utils.applyNullStyle(layer)
    return dock


@pytest.fixture(autouse=True)
def siProject():
    with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as project:
        project.instance.return_value.readEntry.side_effect = (
            lambda section, key, default="": (("LPS", True) if key == "project_units" else (default, False)))
        yield project


@pytest.mark.skipif(not REAL_QGIS, reason="loads the shipped style on a real layer and rewrites real symbols")
class TestNegativePressureClassSize:
    def test_the_style_states_a_two_millimetre_junction_and_the_ratio_of_the_first_class(self, pressureLayer):
        layer, utils = pressureLayer
        dock = _SizesDock()

        sizes = dock.readStyleBaseSizes(layer, layer.renderer())

        assert sizes["junction"] == 2.0
        assert sizes["special"] == 8.0
        assert sizes["junctionRatios"] == [1.25, 1.0, 1.0, 1.0, 1.0, 1.0]

    def test_two_passes_keep_the_first_class_a_quarter_larger_and_the_grey_rule_regular(self, pressureLayer):
        layer, utils = pressureLayer
        dock = _dockOnFreshStyle(layer, utils)
        dock._symbolFactor = 2.0

        dock.applySymbolScaleFactors(layer)
        dock.applySymbolScaleFactors(layer)

        sizes = _junctionSizes(layer)
        assert [size for _label, size in sizes] == [5.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
        assert sizes[0][0] == "< 0"

    def test_a_proportional_toggle_does_not_flatten_or_inflate_the_classes(self, pressureLayer):
        layer, utils = pressureLayer
        dock = _dockOnFreshStyle(layer, utils)

        dock._proportional = True
        dock.applySymbolScaleFactors(layer)
        dock._proportional = False
        dock.applySymbolScaleFactors(layer)

        assert [size for _label, size in _junctionSizes(layer)] == [2.5, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]

    def test_by_range_label_colours_never_paint_white_text(self, pressureLayer):
        layer, utils = pressureLayer
        dock = _dockOnFreshStyle(layer, utils)

        expression = dock._buildRangeColorExpression(layer, "Pressure")

        assert "#ffffff" not in expression
        assert "'#333333'" in expression

    def test_by_range_label_colours_cover_the_open_ended_rules_of_newer_qgis(self, pressureLayer):
        layer, utils = pressureLayer
        dock = _dockOnFreshStyle(layer, utils)
        rules = layer.renderer().rootRule().children()
        rules[0].setFilterExpression('"Pressure" <= -0.0050000000000000')
        rules[5].setFilterExpression('"Pressure" > 49.9949999999999974')

        expression = dock._buildRangeColorExpression(layer, "Pressure")

        assert expression.count("WHEN") == 6
        assert "\"Pressure\" <= -0.005 THEN '#333333'" in expression
        assert "\"Pressure\" >= 49.995 AND" in expression


class TestLegibleLabelColour:
    def test_a_white_class_colour_falls_back_to_the_default_text_colour(self):
        assert _ResultsRenderingMixin._legibleLabelColor("#ffffff") == "#333333"
        assert _ResultsRenderingMixin._legibleLabelColor("#ffffbf") == "#333333"

    def test_the_palette_colours_are_kept(self):
        for color in ("#0084ff", "#00ffff", "#00ff00", "#ffd800", "#ff5d00"):
            assert _ResultsRenderingMixin._legibleLabelColor(color) == color

    def test_anything_that_is_not_a_colour_passes_through(self):
        anything = MagicMock()
        assert _ResultsRenderingMixin._legibleLabelColor(anything) is anything
