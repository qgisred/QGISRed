# -*- coding: utf-8 -*-
"""Class Order sorts the categorized classes when the legend is applied.

The entry sits below Classes on the right side with None, Ascending and Descending. Apply
reorders the table rows by value (None leaves them alone), NULL, #NA and Other Values stay
last, the order is saved with the legend strategy, can be chosen again in the save dialog,
and is honoured when a saved strategy rebuilds the classes from the data.
"""
import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSaveStrategyDialog
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

from .conftest import REAL_QGIS


class FakeClassOrderCombo:
    def __init__(self, order="none"):
        self.items = [("None", "none"), ("Ascending", "ascending"), ("Descending", "descending")]
        self.index = self.findData(order)
        self.enabled = True

    def currentData(self):
        return self.items[self.index][1]

    def findData(self, data):
        return next((index for index, (_text, value) in enumerate(self.items) if value == data), -1)

    def setCurrentIndex(self, index):
        self.index = index

    def isEnabled(self):
        return self.enabled

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)


class FakeValueCell:
    def __init__(self, text):
        self._text = text

    def text(self):
        return self._text


class FakeTable:
    """Rows are their value cell; the dialog moves them through getRowData/setRowData."""

    def __init__(self, values):
        self.rows = list(values)

    def rowCount(self):
        return len(self.rows)

    def cellWidget(self, row, column):
        return FakeValueCell(self.rows[row]) if column == 3 else None

    def setUpdatesEnabled(self, enabled):
        pass

    def blockSignals(self, blocked):
        pass


@pytest.fixture(autouse=True)
def valueCellsAreLineEdits(monkeypatch):
    monkeypatch.setattr(legendsModule, "QLineEdit", FakeValueCell)


def _dialog(order, values):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.tr = lambda text: text
    dialog.cbClassOrder = FakeClassOrderCombo(order)
    dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL
    dialog.tableView = FakeTable(values)
    dialog.edited = False
    dialog.getRowData = lambda row: ("row", dialog.tableView.rows[row])
    dialog.setRowData = lambda row, data: dialog.tableView.rows.__setitem__(row, data[1])
    dialog.markLegendEdited = lambda: setattr(dialog, "edited", True)
    return dialog


class TestSortingTheRowsOnApply:
    def test_the_order_is_read_from_the_combo(self):
        assert _dialog("none", []).currentClassOrder() == "none"

    def test_none_leaves_the_rows_as_they_are(self):
        dialog = _dialog("none", ["b", "a", "c"])
        dialog.sortTableRowsByClassOrder()
        assert dialog.tableView.rows == ["b", "a", "c"] and dialog.edited is False

    def test_ascending_sorts_the_rows_with_the_special_ones_last(self):
        dialog = _dialog("ascending", ["NULL", "b", "Other Values", "a", "c"])
        dialog.sortTableRowsByClassOrder()
        assert dialog.tableView.rows == ["a", "b", "c", "NULL", "Other Values"] and dialog.edited is True

    def test_descending_sorts_the_rows_with_the_special_ones_still_last(self):
        dialog = _dialog("descending", ["b", "#NA", "a", "c"])
        dialog.sortTableRowsByClassOrder()
        assert dialog.tableView.rows == ["c", "b", "a", "#NA"]

    def test_numbers_sort_as_numbers_so_sector_2_comes_before_10(self):
        dialog = _dialog("ascending", ["10", "2", "1"])
        dialog.sortTableRowsByClassOrder()
        assert dialog.tableView.rows == ["1", "2", "10"]

    def test_rows_already_in_order_are_not_marked_edited(self):
        dialog = _dialog("ascending", ["a", "b", "NULL"])
        dialog.sortTableRowsByClassOrder()
        assert dialog.edited is False

    def test_only_categorized_legends_are_sorted(self):
        dialog = _dialog("ascending", ["b", "a"])
        dialog.currentFieldType = QGISRedLegendsDialog.FIELD_TYPE_NUMERIC
        dialog.sortTableRowsByClassOrder()
        assert dialog.tableView.rows == ["b", "a"]


def _addingDialog(order, values, available):
    """A dialog whose class creation appends the next available value as a row."""
    dialog = _dialog(order, values)
    dialog.currentLayer = object()
    dialog.availableUniqueValues = list(available)
    dialog.addClassBeforeSelection = False
    dialog.addCategoricalClass = lambda: dialog.tableView.rows.append(dialog.availableUniqueValues.pop(0))
    for name in ("updateButtonStates", "handleColorLogicOnClassChange", "handleSizeLogicOnClassChange",
                 "updateClassCount", "removeOtherValuesRows"):
        setattr(dialog, name, lambda: None)
    return dialog


class TestNewClassesTakeTheirPlaceInTheOrder:
    def test_an_added_class_is_sorted_in_with_the_others(self):
        dialog = _addingDialog("ascending", ["a", "c"], ["b"])
        dialog.executeAddClass()
        assert dialog.tableView.rows == ["a", "b", "c"]

    def test_with_no_order_the_added_class_stays_where_it_was_put(self):
        dialog = _addingDialog("none", ["c", "a"], ["b"])
        dialog.executeAddClass()
        assert dialog.tableView.rows == ["c", "a", "b"]

    def test_adding_all_values_sorts_the_whole_table(self):
        dialog = _addingDialog("descending", ["b"], ["a", "c", "NULL"])
        dialog.classifyMissingUniqueValues()
        assert dialog.tableView.rows == ["c", "b", "a", "NULL"]


class TestSavingTheOrder:
    def _strategyDialog(self, order):
        dialog = _dialog(order, [])
        dialog.currentFieldName = "Material"
        dialog.buildColorsPart = lambda: {"source": "random"}
        return dialog

    @pytest.mark.parametrize("order", ["none", "ascending", "descending"])
    def test_the_strategy_carries_the_order(self, order):
        strategy = self._strategyDialog(order).buildCategoricalStrategy(["colors"])
        assert strategy["classOrder"] == order

    def test_loading_a_strategy_selects_its_order(self):
        dialog = _dialog("none", [])
        dialog.restoreClassOrderUi("descending")
        assert dialog.cbClassOrder.currentData() == "descending"

    def test_a_strategy_without_an_order_leaves_the_combo_alone(self):
        dialog = _dialog("ascending", [])
        dialog.restoreClassOrderUi(None)
        assert dialog.cbClassOrder.currentData() == "ascending"


class FakeCheckBox:
    def __init__(self, checked=False):
        self._checked = checked
        self.enabled = True

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = bool(checked)

    def isEnabled(self):
        return self.enabled

    def setEnabled(self, enabled):
        self.enabled = bool(enabled)

    def setToolTip(self, text):
        pass


class TestTheSaveDialogEntry:
    """A tick that keeps the order chosen in the editor, offered for every automatic legend."""

    def _saveDialog(self, automatic=True, order="ascending", ticked=True, isCategorical=True):
        dialog = QGISRedSaveStrategyDialog.__new__(QGISRedSaveStrategyDialog)
        dialog.isCategorical = isCategorical
        dialog.classOrder = order
        dialog.partOptions = {part: ("", "") for part in ("structural", "sizes", "colors")}
        dialog.rbAutomaticLegend = FakeCheckBox(automatic)
        dialog.ckStructural = FakeCheckBox(False)
        dialog.ckSizes = FakeCheckBox(False)
        dialog.ckColors = FakeCheckBox(True)
        dialog.ckClassOrder = FakeCheckBox(ticked)
        dialog.updatePartsEnabled()
        return dialog

    def test_the_order_is_offered_for_an_automatic_legend(self):
        dialog = self._saveDialog()
        assert dialog.ckClassOrder.enabled is True and dialog.selectedClassOrder() == "ascending"

    def test_the_tick_is_greyed_and_the_order_none_for_a_fixed_legend(self):
        dialog = self._saveDialog(automatic=False)
        assert dialog.ckClassOrder.enabled is False and dialog.selectedClassOrder() == "none"

    def test_an_unticked_order_is_not_saved(self):
        assert self._saveDialog(ticked=False).selectedClassOrder() == "none"

    def test_the_tick_is_only_shown_when_the_editor_has_an_order(self):
        assert self._saveDialog(order="descending").hasClassOrder() is True
        assert self._saveDialog(order="none").hasClassOrder() is False
        assert self._saveDialog(isCategorical=False).hasClassOrder() is False
        assert self._saveDialog(order="none").selectedClassOrder() == "none"


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
        assert self._classValues(self._strategy(classOrder="descending")) == ["PVC", "FD", "AC"]

    def test_an_ascending_strategy_rebuilds_them_ascending(self):
        assert self._classValues(self._strategy(classOrder="ascending")) == ["AC", "FD", "PVC"]

    def test_a_strategy_without_an_order_stays_ascending(self):
        assert self._classValues(self._strategy()) == ["AC", "FD", "PVC"]
