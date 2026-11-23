# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QInputDialog, QLabel, QListWidget, QListWidgetItem, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from . import featured_values_config as fv_config


class QGISRedFeaturedValuesDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = fv_config.default_config()
        self.nodeIds = []
        self.linkIds = []
        self.signals = {}
        self._loading = False

        self.setWindowTitle(self.tr("Featured Values Manager"))
        self.setWindowIcon(QIcon(":/images/iconFeaturedValues.svg"))
        self.setModal(False)
        self.setSizeGripEnabled(True)

        layout = QVBoxLayout(self)
        self.cbVisible = QCheckBox(self.tr("Show featured values on the map"))
        layout.addWidget(self.cbVisible)
        tabs = QTabWidget()
        layout.addWidget(tabs, 1)

        values = QWidget()
        valuesLayout = QVBoxLayout(values)
        valuesLayout.addWidget(self._buildSimulatedGroup())
        valuesLayout.addWidget(self._buildMeasuredGroup())
        valuesLayout.addWidget(self._buildItemsGroup(), 1)
        tabs.addTab(values, self.tr("Values"))

        appearance = QWidget()
        appearanceLayout = QHBoxLayout(appearance)
        appearanceLayout.addWidget(self._buildDisplayGroup(), 1)
        appearanceLayout.addWidget(self._buildFormatGroup(), 1)
        tabs.addTab(appearance, self.tr("Display"))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)
        self.resize(600, 460)

        self.cbVisible.toggled.connect(self._onDisplayChanged)

    @staticmethod
    def _compactCombo(combo):
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(8)

    def _buildSimulatedGroup(self):
        group = QGroupBox(self.tr("Simulated values"))
        grid = QGridLayout(group)
        self.cbElement = QComboBox()
        self.cbElement.addItem(self.tr("Nodes"), fv_config.NODE)
        self.cbElement.addItem(self.tr("Links"), fv_config.LINK)
        self.cbField = QComboBox()
        self.cbElementId = QComboBox()
        self.cbElementId.setEditable(True)
        self.cbElementId.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._compactCombo(self.cbElementId)
        self.btAddSimulated = QPushButton(self.tr("Add"))
        self.btPick = QPushButton(self.tr("Pick on map"))
        self.btPick.setCheckable(True)
        grid.addWidget(QLabel(self.tr("Element")), 0, 0)
        grid.addWidget(QLabel(self.tr("Magnitude")), 0, 1)
        grid.addWidget(QLabel(self.tr("ID")), 0, 2)
        grid.addWidget(self.cbElement, 1, 0)
        grid.addWidget(self.cbField, 1, 1)
        grid.addWidget(self.cbElementId, 1, 2)
        grid.addWidget(self.btAddSimulated, 1, 3)
        grid.addWidget(self.btPick, 1, 4)
        grid.setColumnStretch(2, 1)
        self.cbElement.currentIndexChanged.connect(self._fillElementWidgets)
        self.btAddSimulated.clicked.connect(self._onAddSimulated)
        self.btPick.toggled.connect(self._onPickToggled)
        return group

    def _buildMeasuredGroup(self):
        self.gbMeasured = QGroupBox(self.tr("Field data"))
        row = QHBoxLayout(self.gbMeasured)
        self.cbSignal = QComboBox()
        self._compactCombo(self.cbSignal)
        self.btAddSignal = QPushButton(self.tr("Add"))
        self.btAddAllSignals = QPushButton(self.tr("Add all with data"))
        self.lbNoSignals = QLabel(self.tr("The project has no signals with field data."))
        row.addWidget(self.lbNoSignals)
        row.addWidget(self.cbSignal, 1)
        row.addWidget(self.btAddSignal)
        row.addWidget(self.btAddAllSignals)
        self.btAddSignal.clicked.connect(self._onAddSignal)
        self.btAddAllSignals.clicked.connect(self._onAddAllSignals)
        return self.gbMeasured

    def _buildItemsGroup(self):
        group = QGroupBox(self.tr("Featured values"))
        layout = QVBoxLayout(group)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            self.tr("Value"), self.tr("Element"), self.tr("ID"), self.tr("Magnitude"), self.tr("Level"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(80)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)
        buttons = QHBoxLayout()
        self.btRemove = QPushButton(self.tr("Remove"))
        self.btZoom = QPushButton(self.tr("Zoom to"))
        self.btBookmark = QPushButton(self.tr("Create bookmark..."))
        buttons.addWidget(self.btRemove)
        buttons.addStretch(1)
        buttons.addWidget(self.btZoom)
        buttons.addWidget(self.btBookmark)
        layout.addLayout(buttons)
        self.btRemove.clicked.connect(self._onRemove)
        self.btZoom.clicked.connect(self._onZoom)
        self.btBookmark.clicked.connect(self._onBookmark)
        return group

    def _buildDisplayGroup(self):
        group = QGroupBox(self.tr("Values to show"))
        layout = QVBoxLayout(group)
        kinds = QHBoxLayout()
        self.cbShowSimulated = QCheckBox(self.tr("Simulated"))
        self.cbShowMeasured = QCheckBox(self.tr("Measured"))
        kinds.addWidget(self.cbShowSimulated)
        kinds.addWidget(self.cbShowMeasured)
        kinds.addStretch(1)
        layout.addLayout(kinds)
        self.lwMagnitudes = QListWidget()
        self.lwMagnitudes.setMinimumHeight(50)
        layout.addWidget(self.lwMagnitudes)
        levels = QHBoxLayout()
        self.sbMaxLevel = QSpinBox()
        self.sbMaxLevel.setRange(1, fv_config.MAX_LEVEL)
        levels.addWidget(QLabel(self.tr("Show up to level")))
        levels.addWidget(self.sbMaxLevel)
        levels.addStretch(1)
        layout.addLayout(levels)
        self.cbZoomDependent = QCheckBox(self.tr("Reveal the lower levels when zooming in"))
        layout.addWidget(self.cbZoomDependent)
        self.cbShowSimulated.toggled.connect(self._onDisplayChanged)
        self.cbShowMeasured.toggled.connect(self._onDisplayChanged)
        self.lwMagnitudes.itemChanged.connect(self._onDisplayChanged)
        self.sbMaxLevel.valueChanged.connect(self._onDisplayChanged)
        self.cbZoomDependent.toggled.connect(self._onDisplayChanged)
        return group

    def _buildFormatGroup(self):
        group = QGroupBox(self.tr("Format"))
        form = QFormLayout(group)
        self.sbFontSize = QSpinBox()
        self.sbFontSize.setRange(6, 24)
        self.cbSimulatedStyle = QComboBox()
        self.cbMeasuredStyle = QComboBox()
        for combo in (self.cbSimulatedStyle, self.cbMeasuredStyle):
            combo.addItem(self.tr("Text only"), fv_config.STYLE_PLAIN)
            combo.addItem(self.tr("Text with halo"), fv_config.STYLE_HALO)
            combo.addItem(self.tr("Opaque background"), fv_config.STYLE_OPAQUE)
            combo.addItem(self.tr("Frame"), fv_config.STYLE_FRAME)
        self.cbShowId = QCheckBox(self.tr("Show the element ID"))
        self.cbShowUnits = QCheckBox(self.tr("Show the units"))
        form.addRow(self.tr("Font size"), self.sbFontSize)
        form.addRow(self.tr("Simulated"), self.cbSimulatedStyle)
        form.addRow(self.tr("Measured"), self.cbMeasuredStyle)
        form.addRow(self.cbShowId)
        form.addRow(self.cbShowUnits)
        self.sbFontSize.valueChanged.connect(self._onDisplayChanged)
        self.cbSimulatedStyle.currentIndexChanged.connect(self._onDisplayChanged)
        self.cbMeasuredStyle.currentIndexChanged.connect(self._onDisplayChanged)
        self.cbShowId.toggled.connect(self._onDisplayChanged)
        self.cbShowUnits.toggled.connect(self._onDisplayChanged)
        return group

    def setData(self, config, nodeIds, linkIds, signals):
        self._loading = True
        try:
            self.config = config
            self.nodeIds = list(nodeIds)
            self.linkIds = list(linkIds)
            self.signals = signals
            display = config["display"]
            self.cbVisible.setChecked(display["visible"])
            self.cbShowSimulated.setChecked(display["showSimulated"])
            self.cbShowMeasured.setChecked(display["showMeasured"])
            self.sbMaxLevel.setValue(display["maxLevel"])
            self.cbZoomDependent.setChecked(display["zoomDependent"])
            self.sbFontSize.setValue(display["fontSize"])
            self.cbSimulatedStyle.setCurrentIndex(self.cbSimulatedStyle.findData(display["simulatedStyle"]))
            self.cbMeasuredStyle.setCurrentIndex(self.cbMeasuredStyle.findData(display["measuredStyle"]))
            self.cbShowId.setChecked(display["showId"])
            self.cbShowUnits.setChecked(display["showUnits"])
            self._fillElementWidgets()
            self._fillSignals()
            self._fillTable()
            self._fillMagnitudes()
        finally:
            self._loading = False

    def currentElement(self):
        return self.cbElement.currentData()

    def setPicking(self, active):
        self.btPick.blockSignals(True)
        self.btPick.setChecked(active)
        self.btPick.blockSignals(False)

    def _fillElementWidgets(self):
        element = self.currentElement()
        fields = fv_config.NODE_FIELDS if element == fv_config.NODE else fv_config.LINK_FIELDS
        self.cbField.clear()
        for field in fields:
            self.cbField.addItem(self.controller.featuredValuesFieldName(element, field), field)
        self.cbElementId.clear()
        self.cbElementId.addItems(self.nodeIds if element == fv_config.NODE else self.linkIds)
        self.cbElementId.setCurrentIndex(-1)
        self.cbElementId.setEditText("")

    def _signalText(self, signal):
        parts = [signal["id"]]
        if signal.get("meter"):
            parts.append(signal["meter"])
        if signal.get("magnitude"):
            parts.append(signal["magnitude"])
        return " · ".join(parts)

    def _fillSignals(self):
        self.cbSignal.clear()
        for signal_id in sorted(self.signals, key=str.lower):
            signal = self.signals[signal_id]
            if signal.get("file"):
                self.cbSignal.addItem(self._signalText(signal), signal_id)
        has_signals = self.cbSignal.count() > 0
        self.lbNoSignals.setVisible(not has_signals)
        for widget in (self.cbSignal, self.btAddSignal, self.btAddAllSignals):
            widget.setVisible(has_signals)

    def _itemTexts(self, item):
        if item["kind"] == fv_config.KIND_SIGNAL:
            signal = next((value for key, value in self.signals.items() if key.lower() == item["signal"].lower()), {})
            return [self.tr("Measured"), signal.get("meter", ""), item["signal"], signal.get("magnitude", "")]
        element = self.tr("Node") if item["element"] == fv_config.NODE else self.tr("Link")
        magnitude = self.controller.featuredValuesFieldName(item["element"], item["field"])
        return [self.tr("Simulated"), element, item["id"], magnitude]

    def _fillTable(self):
        self.table.setRowCount(0)
        for row, item in enumerate(self.config["items"]):
            self.table.insertRow(row)
            for column, text in enumerate(self._itemTexts(item)):
                self.table.setItem(row, column, QTableWidgetItem(text))
            level = QSpinBox()
            level.setRange(1, fv_config.MAX_LEVEL)
            level.setValue(item["level"])
            level.valueChanged.connect(lambda value, target=item: self._onLevelChanged(target, value))
            self.table.setCellWidget(row, 4, level)

    def _fillMagnitudes(self):
        hidden = set(self.config["display"]["hiddenMagnitudes"])
        keys = []
        for row in self.controller.featuredValuesRows():
            if row["magnitude"] not in keys:
                keys.append(row["magnitude"])
        self.lwMagnitudes.blockSignals(True)
        self.lwMagnitudes.clear()
        for key in keys:
            entry = QListWidgetItem(self.controller.featuredValuesMagnitudeName(key))
            entry.setData(Qt.ItemDataRole.UserRole, key)
            entry.setFlags(entry.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            entry.setCheckState(Qt.CheckState.Unchecked if key in hidden else Qt.CheckState.Checked)
            self.lwMagnitudes.addItem(entry)
        self.lwMagnitudes.blockSignals(False)

    def _itemsChanged(self):
        self._fillTable()
        self._fillMagnitudes()
        self.controller.featuredValuesConfigChanged()

    def addSimulated(self, element, elementId):
        item = {
            "kind": fv_config.KIND_SIMULATED, "element": element, "id": elementId,
            "field": self.cbField.currentData(), "level": 1,
        }
        if fv_config.add_item(self.config, item):
            self._itemsChanged()

    def _onAddSimulated(self):
        element = self.currentElement()
        element_id = self.cbElementId.currentText().strip()
        known = self.nodeIds if element == fv_config.NODE else self.linkIds
        if element_id in known:
            self.addSimulated(element, element_id)

    def _onAddSignal(self):
        signal_id = self.cbSignal.currentData()
        if signal_id and fv_config.add_item(
                self.config, {"kind": fv_config.KIND_SIGNAL, "signal": signal_id, "level": 1}):
            self._itemsChanged()

    def _onAddAllSignals(self):
        added = False
        for index in range(self.cbSignal.count()):
            item = {"kind": fv_config.KIND_SIGNAL, "signal": self.cbSignal.itemData(index), "level": 1}
            added = fv_config.add_item(self.config, item) or added
        if added:
            self._itemsChanged()

    def _selectedItems(self):
        rows = sorted({index.row() for index in self.table.selectionModel().selectedRows()})
        return [self.config["items"][row] for row in rows if row < len(self.config["items"])]

    def _onRemove(self):
        selected = self._selectedItems()
        if not selected:
            return
        self.config["items"][:] = [item for item in self.config["items"]
                                   if not any(item is chosen for chosen in selected)]
        self._itemsChanged()

    def _onZoom(self):
        selected = self._selectedItems() or list(self.config["items"])
        if selected:
            self.controller.featuredValuesZoomTo(selected)

    def _onBookmark(self):
        selected = self._selectedItems() or list(self.config["items"])
        if not selected:
            return
        ids = []
        for item in selected:
            name = item.get("id") or item.get("signal")
            if name not in ids:
                ids.append(name)
        default = self.tr("Featured values: %1").replace("%1", ", ".join(ids[:4]))
        name, accepted = QInputDialog.getText(self, self.tr("Create bookmark"), self.tr("Bookmark name"), text=default)
        if accepted and name.strip():
            self.controller.featuredValuesBookmark(selected, name.strip())

    def _onLevelChanged(self, item, value):
        item["level"] = value
        self.controller.featuredValuesConfigChanged()

    def _onPickToggled(self, checked):
        if checked:
            self.controller.featuredValuesStartPicking()
        else:
            self.controller.featuredValuesStopPicking()

    def _onDisplayChanged(self, *_args):
        if self._loading:
            return
        display = self.config["display"]
        display["visible"] = self.cbVisible.isChecked()
        display["showSimulated"] = self.cbShowSimulated.isChecked()
        display["showMeasured"] = self.cbShowMeasured.isChecked()
        display["hiddenMagnitudes"] = [
            self.lwMagnitudes.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.lwMagnitudes.count())
            if self.lwMagnitudes.item(index).checkState() != Qt.CheckState.Checked
        ]
        display["maxLevel"] = self.sbMaxLevel.value()
        display["zoomDependent"] = self.cbZoomDependent.isChecked()
        display["fontSize"] = self.sbFontSize.value()
        display["simulatedStyle"] = self.cbSimulatedStyle.currentData()
        display["measuredStyle"] = self.cbMeasuredStyle.currentData()
        display["showId"] = self.cbShowId.isChecked()
        display["showUnits"] = self.cbShowUnits.isChecked()
        self.controller.featuredValuesConfigChanged()

    def closeEvent(self, event):
        self.controller.featuredValuesStopPicking()
        super().closeEvent(event)
