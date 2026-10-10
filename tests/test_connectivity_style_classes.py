# -*- coding: utf-8 -*-
"""The connectivity links layer completes its shipped style with one class per subnet.

The shipped QML is a legend by SubNet with only the grey "Other" class; once the check
runs, every subnet id becomes a class coloured in order from the default Sequential
palette, so each subnet can be told apart on the map.
"""
import os

import pytest

from .conftest import REAL_QGIS

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

pytestmark = pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS renderers")

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")


def _connectivityLayer(subnets):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY

    layer = QgsVectorLayer("LineString?crs=EPSG:25830&field=Id:string&field=SubNet:string", "links", "memory")
    provider = layer.dataProvider()
    for index, subnet in enumerate(subnets):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(index, 0), QgsPointXY(index + 1, 0)]))
        feature.setAttributes(["P%d" % index, subnet])
        provider.addFeature(feature)
    layer.updateExtents()
    layer.loadNamedStyle(os.path.join(SHIPPED, "ConnectLinks.qml.bak"))
    return layer


def _paletteNames():
    return [color.name() for color in QGISRedStylingUtils().demandBuilderPaletteColors()]


def _classNames(layer):
    return {category.value(): category.symbol().color().name() for category in layer.renderer().categories()}


class TestSubnetClasses:
    def test_the_shipped_style_is_a_legend_by_subnet_with_only_the_other_class(self):
        layer = _connectivityLayer([])

        assert layer.renderer().type() == "categorizedSymbol"
        assert layer.renderer().classAttribute() == "SubNet"
        assert [category.value() for category in layer.renderer().categories()] == [""]
        assert layer.renderer().sourceColorRamp() is None

    def test_each_subnet_takes_the_sequential_palette_in_order(self):
        layer = _connectivityLayer(["2", "1", "3", "1"])

        QGISRedStylingUtils().fillCategoriesFromData(layer, "SubNet")

        categories = layer.renderer().categories()
        assert [category.value() for category in categories] == ["", "1", "2", "3"]
        assert [category.symbol().color().name() for category in categories[1:]] == _paletteNames()[:3]

    def test_more_subnets_than_colours_start_the_palette_over(self):
        count = len(_paletteNames()) + 2
        layer = _connectivityLayer(["%02d" % index for index in range(count)])

        QGISRedStylingUtils().fillCategoriesFromData(layer, "SubNet")

        names = [category.symbol().color().name() for category in layer.renderer().categories()[1:]]
        assert names[:2] == names[-2:]

    def test_a_subnet_saved_in_the_style_keeps_its_colour_and_the_others_skip_it(self):
        from qgis.core import QgsRendererCategory
        from qgis.PyQt.QtGui import QColor

        layer = _connectivityLayer(["1", "2"])
        renderer = layer.renderer()
        saved = renderer.sourceSymbol().clone()
        saved.setColor(QColor(_paletteNames()[0]))
        renderer.addCategory(QgsRendererCategory("1", saved, "1"))

        QGISRedStylingUtils().fillCategoriesFromData(layer, "SubNet")

        names = _classNames(layer)
        assert names["1"] == _paletteNames()[0]
        assert names["2"] == _paletteNames()[1]

    def test_the_subnet_symbols_keep_the_shipped_line_look(self):
        layer = _connectivityLayer(["1"])
        template = layer.renderer().sourceSymbol().clone()

        QGISRedStylingUtils().fillCategoriesFromData(layer, "SubNet")

        categories = layer.renderer().categories()
        symbol = categories[1].symbol()
        assert symbol.symbolLayer(0).layerType() == template.symbolLayer(0).layerType()
        assert symbol.symbolLayer(0).width() == template.symbolLayer(0).width()
