# -*- coding: utf-8 -*-
"""Order sorts the categorized classes as soon as it is chosen.

The entry sits below Classes on the right side with Current, Ascending and Descending.
Choosing an order reorders the table rows by value at once (Current leaves them alone), NULL,
#NA and Other Values stay last, classes added later take their place in the order, the
arrows move a class by hand (which sets the order back to Current), the order is saved with
the legend strategy, can be chosen again in the save dialog, and is honoured when a saved
strategy rebuilds the classes from the data.
"""
import pytest

import QGISRed.ui.project.qgisred_custom_dialogs as customDialogsModule
import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.ui.project.qgisred_custom_dialogs import QGISRedSaveStrategyDialog
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

from .conftest import REAL_QGIS


class FakeClassOrderCombo:
    def __init__(self, order="none", items=None):
        self.items = items or [("Current", "none"), ("Ascending", "ascending"), ("Descending", "descending")]
        self.index = self.findData(order)
        self.enabled = True
        self.signalsBlocked = False
        self.onChange = None

    def currentData(self):
        return self.items[self.index][1]

    def currentIndex(self):
        return self.index

    def findData(self, data):
        return next((index for index, (_text, value) in enumerate(self.items) if value == data), -1)

    def setCurrentIndex(self, index):
        changed = index != self.index
        self.index = index
        if changed and self.onChange and not self.signalsBlocked:
            self.onChange()

    def blockSignals(self, blocked):
        self.signalsBlocked = blocked

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
        self.selected = None

    def rowCount(self):
        return len(self.rows)

    def cellWidget(self, row, column):
        return FakeValueCell(self.rows[row]) if column == 3 else None

    def setUpdatesEnabled(self, enabled):
        pass

    def blockSignals(self, blocked):
        pass

    def selectRow(self, row):
        self.selected = row


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
    dialog.updateButtonStates = lambda: None
    dialog.cbClassOrder.onChange = dialog.onClassOrderChanged
    return dialog


class TestChoosingAnOrderSortsAtOnce:
    def test_ascending_sorts_the_table_when_chosen(self):
        dialog = _dialog("none", ["b", "c", "a"])
        dialog.cbClassOrder.setCurrentIndex(dialog.cbClassOrder.findData("ascending"))
        assert dialog.tableView.rows == ["a", "b", "c"] and dialog.edited is True

    def test_descending_sorts_the_table_when_chosen(self):
        dialog = _dialog("ascending", ["a", "b", "c"])
        dialog.cbClassOrder.setCurrentIndex(dialog.cbClassOrder.findData("descending"))
        assert dialog.tableView.rows == ["c", "b", "a"]

    def test_current_keeps_the_rows_as_they_are(self):
        dialog = _dialog("ascending", ["a", "b", "c"])
        dialog.cbClassOrder.setCurrentIndex(dialog.cbClassOrder.findData("none"))
        assert dialog.tableView.rows == ["a", "b", "c"] and dialog.edited is False

    def test_restoring_a_saved_order_only_moves_the_selector(self):
        dialog = _dialog("none", ["b", "a"])
        dialog.restoreClassOrderUi("ascending")
        assert dialog.currentClassOrder() == "ascending" and dialog.tableView.rows == ["b", "a"]


class TestMovingAClassByHand:
    def _movingDialog(self, order, values, selected):
        dialog = _dialog(order, values)
        dialog.getSelectedRows = lambda: [selected]
        return dialog

    def test_the_class_moves_up_and_stays_selected(self):
        dialog = self._movingDialog("none", ["a", "b", "c"], 2)
        dialog.moveClassUp()
        assert dialog.tableView.rows == ["a", "c", "b"] and dialog.tableView.selected == 1 and dialog.edited

    def test_the_class_moves_down(self):
        dialog = self._movingDialog("none", ["a", "b", "c"], 0)
        dialog.moveClassDown()
        assert dialog.tableView.rows == ["b", "a", "c"]

    def test_a_hand_made_order_sets_the_order_back_to_current_without_sorting(self):
        dialog = self._movingDialog("ascending", ["a", "b", "c"], 0)
        dialog.moveClassDown()
        assert dialog.currentClassOrder() == "none" and dialog.tableView.rows == ["b", "a", "c"]

    def test_the_first_class_does_not_move_up(self):
        dialog = self._movingDialog("none", ["a", "b"], 0)
        dialog.moveClassUp()
        assert dialog.tableView.rows == ["a", "b"] and dialog.edited is False

    def test_other_values_stays_last(self):
        dialog = self._movingDialog("none", ["a", "b", "Other Values"], 1)
        dialog.moveClassDown()
        assert dialog.tableView.rows == ["a", "b", "Other Values"]
        dialog = self._movingDialog("none", ["a", "b", "Other Values"], 2)
        dialog.moveClassUp()
        assert dialog.tableView.rows == ["a", "b", "Other Values"]


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
    dialog.cbClasses = FakeClassOrderCombo("current", items=[("Current", "current"), ("All", "all")])
    dialog.cbClasses.onChange = dialog.onClassesScopeChanged
    for name in ("updateButtonStates", "handleColorLogicOnClassChange", "handleSizeLogicOnClassChange",
                 "updateClassCount", "removeOtherValuesRows", "refreshAllLegendLabels", "updateClassCountLimits"):
        setattr(dialog, name, lambda *args, **kwargs: None)
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


class TestCurrentOrAllClasses:
    """All gives every value of the layer a class; Current keeps the classes shown."""

    def _all(self, dialog):
        dialog.cbClasses.setCurrentIndex(dialog.cbClasses.findData("all"))

    def test_all_adds_every_missing_value(self):
        dialog = _addingDialog("none", ["a"], ["b", "c"])
        self._all(dialog)
        assert dialog.tableView.rows == ["a", "b", "c"] and dialog.currentClassesScope() == "all"

    def test_adding_the_last_value_by_hand_selects_all(self):
        dialog = _addingDialog("none", ["a"], ["b"])
        dialog.executeAddClass()
        assert dialog.currentClassesScope() == "all"

    def test_adding_a_value_while_others_are_missing_stays_on_current(self):
        dialog = _addingDialog("none", ["a"], ["b", "c"])
        dialog.executeAddClass()
        assert dialog.currentClassesScope() == "current"

    def test_removing_a_class_goes_back_to_current(self):
        dialog = _addingDialog("none", ["a", "b"], [])
        self._all(dialog)
        dialog.getSelectedRows = lambda: [1]
        dialog.removeCategoricalRows = lambda rows: [
            dialog.availableUniqueValues.append(dialog.tableView.rows.pop(row)) for row in rows]
        dialog.removeClass()
        assert dialog.tableView.rows == ["a"] and dialog.currentClassesScope() == "current"

    def test_values_left_out_keep_current(self):
        dialog = _addingDialog("none", ["a"], ["b"])
        dialog.classifyMissingUniqueValues = lambda: None
        self._all(dialog)
        assert dialog.currentClassesScope() == "current"

    def test_current_can_be_chosen_with_every_value_classified(self):
        dialog = _addingDialog("none", ["a"], [])
        dialog.cbClasses.index = dialog.cbClasses.findData("all")
        dialog.cbClasses.setCurrentIndex(dialog.cbClasses.findData("current"))
        assert dialog.currentClassesScope() == "current" and dialog.tableView.rows == ["a"]

    @pytest.mark.parametrize("available, enabled", [(["b"], True), ([], False)])
    def test_the_plus_button_is_disabled_once_every_value_has_its_class(self, available, enabled):
        dialog = _addingDialog("none", ["a"], available)
        dialog.btClassPlus = FakeCheckBox()
        dialog.updateAddButtonState(True, False, False, 1, None)
        assert dialog.btClassPlus.enabled is enabled

    @pytest.mark.parametrize("parts, available, scope", [
        (["allValues"], [], "all"),
        (["colors"], [], "all"),
        (["allValues"], ["b"], "current"),
        (["allClasses", "colors"], [], "current"),
        ([], [], "current"),
    ])
    def test_a_saved_style_selects_its_scope(self, parts, available, scope):
        dialog = _addingDialog("none", ["a"], available)
        dialog.cbClasses.index = dialog.cbClasses.findData("all" if scope == "current" else "current")
        dialog.restoreClassesScopeUi(parts)
        assert dialog.currentClassesScope() == scope


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

    def test_the_tick_is_shown_for_every_categorical_legend_none_included(self):
        assert self._saveDialog(order="descending").hasClassOrder() is True
        assert self._saveDialog(order="none").hasClassOrder() is True
        assert self._saveDialog(isCategorical=False).hasClassOrder() is False
        assert self._saveDialog(order="none").selectedClassOrder() == "none"
        assert self._saveDialog(order="none").sortsClasses() is False

    @pytest.mark.parametrize("order, text", [
        ("none", "Order: kept as shown"), ("ascending", "Order: Ascending"), ("descending", "Order: Descending"),
    ])
    def test_the_entry_reads_like_the_other_parts(self, monkeypatch, order, text):
        class TextCheckBox(FakeCheckBox):
            def __init__(self, label):
                super().__init__()
                self.label = label

        monkeypatch.setattr(customDialogsModule, "QCheckBox", TextCheckBox)
        dialog = QGISRedSaveStrategyDialog.__new__(QGISRedSaveStrategyDialog)
        dialog.tr = lambda source: source
        dialog.classOrder = order
        assert dialog.createClassOrderCheckBox().label == text


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
