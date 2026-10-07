# -*- coding: utf-8 -*-
"""A Demand Builder theme completes its shipped style with the classes of its data.

The shipped QML is a legend by Category with no classes; on load the values of the layer
become classes coloured as the look was programmed, and the labels follow their class.
"""
import os

import pytest

from .conftest import REAL_QGIS

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS renderers")

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")


def _pointsTheme(categories):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY

    layer = QgsVectorLayer(
        "Point?crs=EPSG:25830&field=DemID:string&field=Category:string&field=Fact2024:double", "theme", "memory")
    provider = layer.dataProvider()
    for index, category in enumerate(categories):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
        feature.setAttributes(["D%d" % index, category, 1.0])
        provider.addFeature(feature)
    layer.updateExtents()
    layer.loadNamedStyle(os.path.join(SHIPPED, "DemandBuilderConsumptionPoints.qml.bak"))
    return layer


def _rgb(color):
    return color.red(), color.green(), color.blue()


def _classColours(layer):
    categories = layer.renderer().categories()
    return {category.value(): _rgb(category.symbol().color()) for category in categories}


class TestClassesFromData:
    def test_the_shipped_style_is_a_legend_by_category_without_classes(self):
        layer = _pointsTheme([])

        assert layer.renderer().type() == "categorizedSymbol"
        assert layer.renderer().categories() == []
        assert "Category" in layer.renderer().classAttribute()

    def test_uncategorized_comes_first_in_orange_then_the_values_sorted(self):
        layer = _pointsTheme(["Ind", "", "Dom", None])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        categories = layer.renderer().categories()
        assert [category.value() for category in categories] == ["Uncategorized", "Dom", "Ind"]
        assert _rgb(categories[0].symbol().color()) == (255, 165, 0)

    def test_a_value_gets_the_same_hashed_colour_in_every_theme(self):
        styling = QGISRedStylingUtils()
        first = _pointsTheme(["Dom"])
        second = _pointsTheme(["Ind", "Dom"])

        styling.completeDemandBuilderStyle(first, True)
        styling.completeDemandBuilderStyle(second, True)

        assert _classColours(first)["Dom"] == _classColours(second)["Dom"]
        assert _classColours(first)["Dom"] == _rgb(styling._colorForDemandCategory("Dom"))
        assert _classColours(second)["Dom"] != _classColours(second)["Ind"]

    def test_a_class_saved_in_the_style_keeps_its_colour(self):
        from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory
        from qgis.PyQt.QtGui import QColor

        layer = _pointsTheme(["Dom", "Ind"])
        shipped = layer.renderer()
        saved = shipped.sourceSymbol().clone()
        saved.setColor(QColor(200, 0, 0))
        renderer = QgsCategorizedSymbolRenderer(shipped.classAttribute(), [QgsRendererCategory("Dom", saved, "Dom")])
        renderer.setSourceSymbol(shipped.sourceSymbol().clone())
        layer.setRenderer(renderer)

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        colours = _classColours(layer)
        assert colours["Dom"] == (200, 0, 0)
        assert colours["Ind"] == _rgb(QGISRedStylingUtils()._colorForDemandCategory("Ind"))

    def test_the_classes_draw_the_default_marker_of_qgis(self):
        layer = _pointsTheme(["Dom"])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        categories = layer.renderer().categories()
        symbol = categories[0].symbol()
        assert symbol.symbolLayer(0).layerType() == "SimpleMarker"
        assert abs(symbol.size() - 2.0) < 1e-9


class TestLabels:
    def test_labels_take_the_colour_of_their_class(self):
        from QGISRed.compat import PAL_PROPERTY_COLOR

        layer = _pointsTheme(["Dom", ""])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        categories = layer.renderer().categories()
        names = {category.value(): category.symbol().color().name() for category in categories}
        expression = layer.labeling().settings().dataDefinedProperties().property(PAL_PROPERTY_COLOR).expressionString()
        assert "THEN '%s'" % names["Dom"] in expression
        assert "THEN '%s'" % names["Uncategorized"] in expression

    def test_the_point_label_is_the_base_demand_column_and_shown(self):
        layer = _pointsTheme(["Dom"])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        assert layer.labelsEnabled()
        assert layer.labeling().settings().fieldName == "Fact2024"
