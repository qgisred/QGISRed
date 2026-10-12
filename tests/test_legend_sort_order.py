# -*- coding: utf-8 -*-
"""Categorized classes can be added in ascending or descending order of their values.

The order is chosen next to the class buttons, applies to the values still to classify and
to "Add all values", is saved with the legend strategy and is honoured again when a saved
strategy rebuilds the classes from the data. NULL and #NA always stay last.
"""
import pytest

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

from .conftest import REAL_QGIS


class FakeSortOrderCombo:
    def __init__(self, order="ascending"):
        self.items = [("Ascending", "ascending"), ("Descending", "descending")]
        self.index = 0 if order == "ascending" else 1
        self.blocked = []

    def currentData(self):
        return self.items[self.index][1]

    def findData(self, data):
        return next((index for index, (_text, value) in enumerate(self.items) if value == data), -1)

    def setCurrentIndex(self, index):
        self.index = index

    def blockSignals(self, blocked):
        self.blocked.append(blocked)


class FakeFeature:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, field):
        return self.value


class FakeLayer:
    def __init__(self, values):
        self.values = values

    def fields(self):
        class _Fields:
            def indexOf(self, name):
                return 0
        return _Fields()

    def getFeatures(self):
        return [FakeFeature(value) for value in self.values]

    def customProperty(self, key):
        return "qgisred_pipes"


def _dialog(order="ascending", values=("b", "a", None, "c")):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.cbSortOrder = FakeSortOrderCombo(order)
    dialog.currentLayer = FakeLayer(values)
    dialog.currentFieldName = "Material"
    dialog.availableUniqueValues = []
    return dialog


class TestSortingTheValues:
    def test_ascending_is_the_default(self):
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        assert dialog.isDescendingOrder() is False

    def test_values_come_ascending_with_the_special_ones_last(self):
        assert _dialog("ascending").getUniqueValuesFromLayer() == ["a", "b", "c", "NULL"]

    def test_values_come_descending_with_the_special_ones_still_last(self):
        assert _dialog("descending").getUniqueValuesFromLayer() == ["c", "b", "a", "NULL"]

    def test_changing_the_order_resorts_the_values_still_to_classify(self):
        dialog = _dialog("ascending")
        dialog.availableUniqueValues = ["a", "b", "NULL", "c"]
        dialog.cbSortOrder.setCurrentIndex(1)

        dialog.onSortOrderChanged()

        assert dialog.availableUniqueValues == ["c", "b", "a", "NULL"]


class TestSavingTheOrder:
    def _strategyDialog(self, order):
        dialog = _dialog(order)
        dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
        dialog.buildColorsPart = lambda: {"source": "random"}
        return dialog

    @pytest.mark.parametrize("order", ["ascending", "descending"])
    def test_the_strategy_carries_the_order(self, order):
        strategy = self._strategyDialog(order).buildCategoricalStrategy(["colors"])
        assert strategy["sortOrder"] == order

    def test_loading_a_strategy_selects_its_order_and_resorts(self):
        dialog = _dialog("ascending")
        dialog.availableUniqueValues = ["a", "b"]

        dialog.restoreSortOrderUi("descending")

        assert dialog.cbSortOrder.currentData() == "descending"
        assert dialog.availableUniqueValues == ["b", "a"]
        assert dialog.cbSortOrder.blocked == [True, False]

    def test_a_strategy_without_an_order_leaves_the_combo_alone(self):
        dialog = _dialog("descending")
        dialog.restoreSortOrderUi(None)
        assert dialog.cbSortOrder.currentData() == "descending"


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
class TestReplayingTheOrder:
    def _classValues(self, strategy):
        layer = _materialLayer(["PVC", "AC", "FD"])
        QGISRedStylingUtils("", "").applyLegendStrategy(layer, strategy)
        return [category.value() for category in layer.renderer().categories()]

    def _strategy(self, **extra):
        strategy = {"schema": "qgisred.legendStrategy.v2", "mode": "categorized", "field": "Material",
                    "parts": ["colors"], "colors": {"source": "random"}}
        strategy.update(extra)
        return strategy

    def test_a_descending_strategy_rebuilds_the_classes_descending(self):
        assert self._classValues(self._strategy(sortOrder="descending")) == ["PVC", "FD", "AC"]

    def test_an_ascending_strategy_rebuilds_them_ascending(self):
        assert self._classValues(self._strategy(sortOrder="ascending")) == ["AC", "FD", "PVC"]

    def test_a_strategy_saved_before_the_option_stays_ascending(self):
        assert self._classValues(self._strategy()) == ["AC", "FD", "PVC"]
