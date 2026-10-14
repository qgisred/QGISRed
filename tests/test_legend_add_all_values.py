# -*- coding: utf-8 -*-
"""The "Add all values" part of an automatic legend: the classes saved with the style keep
their look, and every value the layer has gained since is added as a class when the style
is loaded, whatever the colors are set to."""
import pytest

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

from .conftest import REAL_QGIS


class TestLoadingInTheEditor:
    def _dialog(self):
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
        dialog.getCurrentRendererType = lambda: "categorizedSymbol"
        dialog.restoreClassOrderUi = lambda order: None
        dialog.calls = []
        dialog.classifyMissingUniqueValues = lambda: dialog.calls.append("add values")
        dialog.restoreSizesUi = lambda block: dialog.calls.append("sizes")
        return dialog

    def _strategy(self, parts):
        return {"schema": "qgisred.legendStrategy.v2", "mode": "categorized", "field": "Material",
                "parts": parts, "sizes": {"mode": "Equal"}}

    def test_the_missing_values_are_added_before_the_other_parts(self):
        dialog = self._dialog()
        dialog.applyStrategyToDialog(self._strategy(["allValues", "sizes"]))
        assert dialog.calls == ["add values", "sizes"]

    def test_pinned_classes_are_never_completed(self):
        dialog = self._dialog()
        dialog.applyStrategyToDialog(self._strategy(["allClasses", "sizes"]))
        assert dialog.calls == ["sizes"]


def _materialLayer(values):
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

    layer = QgsVectorLayer("Point?crs=EPSG:3857&field=Material:string", "nodes", "memory")
    features = []
    for index, value in enumerate(values):
        feature = QgsFeature(layer.fields())
        feature.setAttribute("Material", value)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
        features.append(feature)
    layer.dataProvider().addFeatures(features)
    layer.updateExtents()
    return layer


@pytest.mark.skipif(not REAL_QGIS, reason="needs real renderers")
class TestLoadingOntoTheLayer:
    def _savedLayer(self, values):
        from qgis.core import QgsCategorizedSymbolRenderer, QgsMarkerSymbol, QgsRendererCategory
        from qgis.PyQt.QtGui import QColor

        layer = _materialLayer(values)
        symbol = QgsMarkerSymbol.createSimple({"color": "255,0,0,255", "size": "3.5"})
        renderer = QgsCategorizedSymbolRenderer("Material", [QgsRendererCategory("PVC", symbol, "PVC pipes")])
        renderer.setSourceSymbol(QgsMarkerSymbol.createSimple({"color": "0,0,255,255", "size": "3.5"}))
        layer.setRenderer(renderer)
        assert layer.renderer().categories()[0].symbol().color() == QColor(255, 0, 0)
        return layer

    def _strategy(self, parts):
        return {"schema": "qgisred.legendStrategy.v2", "mode": "categorized", "field": "Material", "parts": parts}

    def test_the_saved_class_keeps_its_look_and_the_new_values_are_added(self):
        layer = self._savedLayer(["PVC", "AC", "FD", "AC"])

        QGISRedStylingUtils("", "").applyLegendStrategy(layer, self._strategy(["allValues"]))

        categories = layer.renderer().categories()
        assert [category.value() for category in categories] == ["PVC", "AC", "FD"]
        assert categories[0].label() == "PVC pipes" and categories[0].symbol().color().name() == "#ff0000"
        assert categories[1].symbol().size() == 3.5 and categories[2].symbol().size() == 3.5

    def test_each_new_value_always_gets_the_same_colour(self):
        first = self._savedLayer(["PVC", "AC"])
        second = self._savedLayer(["PVC", "AC"])
        for layer in (first, second):
            QGISRedStylingUtils("", "").applyLegendStrategy(layer, self._strategy(["allValues"]))
        assert first.renderer().categories()[1].symbol().color() == second.renderer().categories()[1].symbol().color()
        assert first.renderer().categories()[1].symbol().color().name() != "#ff0000"

    def test_a_null_value_becomes_the_grey_na_class(self):
        layer = self._savedLayer(["PVC", None])

        QGISRedStylingUtils("", "").applyLegendStrategy(layer, self._strategy(["allValues"]))

        categories = layer.renderer().categories()
        assert categories[-1].label() == "#NA" and categories[-1].symbol().color().name() == "#c0c0c0"

    def test_nothing_changes_when_every_value_has_its_class(self):
        layer = self._savedLayer(["PVC"])
        QGISRedStylingUtils("", "").applyLegendStrategy(layer, self._strategy(["allValues"]))
        assert [category.value() for category in layer.renderer().categories()] == ["PVC"]
