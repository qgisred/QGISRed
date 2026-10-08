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


def _sectorsTheme(sectorIds, idField="SectorID:integer"):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY

    layer = QgsVectorLayer(
        "Polygon?crs=EPSG:25830&field=%s&field=Category:string" % idField, "sectors", "memory")
    provider = layer.dataProvider()
    for index, sectorId in enumerate(sectorIds):
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromPolygonXY([[
            QgsPointXY(index, 0), QgsPointXY(index + 1, 0), QgsPointXY(index + 1, 1), QgsPointXY(index, 0)]]))
        feature.setAttributes([sectorId, "Cat"])
        provider.addFeature(feature)
    layer.updateExtents()
    layer.loadNamedStyle(os.path.join(SHIPPED, "DemandBuilderSectors.qml.bak"))
    return layer


def _rgb(color):
    return color.red(), color.green(), color.blue()


def _classColours(layer):
    categories = layer.renderer().categories()
    return {category.value(): _rgb(category.symbol().color()) for category in categories}


def _paletteNames():
    return [color.name() for color in QGISRedStylingUtils().demandBuilderPaletteColors()]


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

    def test_the_values_take_the_sequential_palette_in_order(self):
        layer = _pointsTheme(["Ind", "Dom", "", "Com"])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        categories = layer.renderer().categories()
        names = [category.symbol().color().name() for category in categories]
        assert [category.value() for category in categories] == ["Uncategorized", "Com", "Dom", "Ind"]
        assert names[1:] == _paletteNames()[:3]

    def test_the_palette_is_the_default_sequential_palette_of_the_library(self):
        from QGISRed.tools.utils.qgisred_styling_utils import PALETTE_KIND_SEQUENTIAL, DEMAND_BUILDER_PALETTE_NAME

        QGISRedStylingUtils.ensureStyleDatabase()

        assert QGISRedStylingUtils.findColorRampKind(DEMAND_BUILDER_PALETTE_NAME) == PALETTE_KIND_SEQUENTIAL
        assert len(_paletteNames()) >= 10

    def test_the_palette_is_read_from_the_library_ramp(self):
        from qgis.core import QgsPresetSchemeColorRamp
        from qgis.PyQt.QtGui import QColor

        styling = QGISRedStylingUtils()
        styling.findColorRamp = lambda name: QgsPresetSchemeColorRamp([QColor("#123456"), QColor("#654321")])

        assert [color.name() for color in styling.demandBuilderPaletteColors()] == ["#123456", "#654321"]

    def test_without_the_library_ramp_the_palette_is_the_shipped_one(self):
        from QGISRed.tools.utils.qgisred_styling_utils import DEMAND_BUILDER_FALLBACK_COLORS

        styling = QGISRedStylingUtils()
        styling.findColorRamp = lambda name: None

        assert [color.name() for color in styling.demandBuilderPaletteColors()] == list(DEMAND_BUILDER_FALLBACK_COLORS)

    def test_more_values_than_colours_start_the_palette_over(self):
        count = len(_paletteNames()) + 2
        layer = _pointsTheme(["V%02d" % index for index in range(count)])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        names = [category.symbol().color().name() for category in layer.renderer().categories()]
        assert names[:2] == names[-2:]

    def test_a_new_value_skips_the_colours_the_saved_classes_already_use(self):
        from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererCategory
        from qgis.PyQt.QtGui import QColor

        layer = _pointsTheme(["Dom", "Ind"])
        shipped = layer.renderer()
        saved = shipped.sourceSymbol().clone()
        saved.setColor(QColor(_paletteNames()[0]))
        renderer = QgsCategorizedSymbolRenderer(shipped.classAttribute(), [QgsRendererCategory("Dom", saved, "Dom")])
        renderer.setSourceSymbol(shipped.sourceSymbol().clone())
        layer.setRenderer(renderer)

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        names = {category.value(): category.symbol().color().name() for category in layer.renderer().categories()}
        assert names["Ind"] == _paletteNames()[1]

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
        assert colours["Ind"] == _rgb(QGISRedStylingUtils().demandBuilderPaletteColors()[0])

    def test_a_single_symbol_style_of_an_older_editor_becomes_the_class_template(self):
        from qgis.core import QgsSingleSymbolRenderer
        from qgis.PyQt.QtGui import QColor

        layer = _pointsTheme(["Dom", ""])
        template = layer.renderer().sourceSymbol().clone()
        template.setColor(QColor(0, 0, 200))
        template.setSize(4.5)
        layer.setRenderer(QgsSingleSymbolRenderer(template))

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, True)

        renderer = layer.renderer()
        assert renderer.type() == "categorizedSymbol"
        assert renderer.classAttribute() == QGISRedStylingUtils.demandBuilderClassExpression("Category")
        assert [category.value() for category in renderer.categories()] == ["Uncategorized", "Dom"]
        assert all(abs(category.symbol().size() - 4.5) < 1e-9 for category in renderer.categories())


class TestSectors:
    def test_the_shipped_sectors_style_classifies_by_sector_id(self):
        layer = _sectorsTheme([])

        assert layer.renderer().type() == "categorizedSymbol"
        assert "SectorID" in layer.renderer().classAttribute()
        assert "Category" not in layer.renderer().classAttribute()

    def test_numeric_sector_ids_become_classes_with_uncategorized_first(self):
        from qgis.core import NULL

        layer = _sectorsTheme([3, 1, NULL, 3])

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, False)

        categories = layer.renderer().categories()
        assert [category.value() for category in categories] == ["Uncategorized", "1", "3"]
        assert _rgb(categories[0].symbol().color()) == (255, 165, 0)
        assert categories[0].symbol().symbolLayer(0).layerType() == "SimpleFill"

    def test_a_sectors_file_without_sector_id_falls_back_to_category(self):
        layer = _sectorsTheme(["Zona A"], idField="Zone:string")

        QGISRedStylingUtils().completeDemandBuilderStyle(layer, False)

        renderer = layer.renderer()
        assert renderer.classAttribute() == QGISRedStylingUtils.demandBuilderClassExpression("Category")
        assert [category.value() for category in renderer.categories()] == ["Cat"]

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
