# -*- coding: utf-8 -*-
from contextlib import suppress
import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QDate, QEvent, QSize, Qt, QTimer, QVariant
from qgis.PyQt.QtGui import QBrush, QColor, QDoubleValidator, QIcon
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QComboBox,
    QDialog,
    QDockWidget,
    QLayout,
    QListView,
    QMessageBox,
    QStackedWidget,
    QToolBar,
    QToolButton,
)

from qgis.core import (
    QgsApplication,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeatureRequest,
    QgsProject,
    QgsSettings,
    QgsVectorLayer,
)
from qgis.gui import QgsHighlight

from ...compat import QAction
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_ui_utils import QGISRedBanner, QGISRED_COMBO_STYLE


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_groupedit_dialog.ui"))


_elementLayerOrder = [
    "qgisred_junctions",
    "qgisred_demands",
    "qgisred_pipes",
    "qgisred_tanks",
    "qgisred_reservoirs",
    "qgisred_pumps",
    "qgisred_valves",
    "qgisred_sources",
    "qgisred_serviceconnections",
    "qgisred_isolationvalves",
    "qgisred_meters",
]

_readonlyFields = {}

_enumFields = {
    "qgisred_pipes":           {"IniStatus": ["OPEN", "CLOSED", "CV"]},
    "qgisred_pumps":           {"IniStatus": ["OPEN", "CLOSED"]},
    "qgisred_valves":          {"IniStatus": ["OPEN", "CLOSED"],
                                "Type":      ["PRV", "PSV", "PBV", "FCV", "TCV", "GPV"],
                                "ValveType": ["PRV", "PSV", "PBV", "FCV", "TCV", "GPV"]},
    "qgisred_isolationvalves": {"Status": ["OPEN", "CLOSED"], "IniStatus": ["OPEN", "CLOSED"]},
}

# Soft bounds: warn (not block) when computed value falls outside.
# None means unbounded on that side.
_softBounds = {
    ("qgisred_pipes", "Diameter"):     (0.0, None),
    ("qgisred_pipes", "RoughCoeff"):   (0.0, None),
    ("qgisred_pipes", "LossCoeff"):    (0.0, None),
    ("qgisred_pipes", "Age"):          (0.0, None),
    ("qgisred_junctions", "EmittCoef"): (0.0, None),
    ("qgisred_tanks", "Diameter"):     (0.0, None),
    ("qgisred_tanks", "MinVolume"):    (0.0, None),
    ("qgisred_tanks", "IniLevel"):     (0.0, None),
    ("qgisred_valves", "Diameter"):    (0.0, None),
}


# Action keys ordered for the action combo. Each entry: (key, label, kind)
# kind: 'numeric' / 'text' / 'findReplace'
_numericActions = [
    ("replace",   "Replace with",   "numeric"),
    ("multiply",  "Multiply by",    "numeric"),
    ("add",       "Add",            "numeric"),
    ("subtract",  "Subtract",       "numeric"),
    ("divide",    "Divide by",      "numeric"),
    ("clampMin", "Clamp minimum to", "numeric"),
    ("clampMax", "Clamp maximum to", "numeric"),
]
_textActions = [
    ("set",          "Set to",          "text"),
    ("prepend",      "Prepend",         "text"),
    ("append",       "Append",          "text"),
    ("findReplace", "Find and replace", "findReplace"),
]
_enumActions = [
    ("replace", "Replace with", "enum"),
]
_dateActions = [
    ("set", "Set to", "date"),
]

# Page indices in stackedValue (must match the .ui order).
_pageNumber = 0
_pageText = 1
_pageEnum = 2
_pageFindReplace = 3
_pageDate = 4

# Property items matching these (case-insensitive) get the grey background used
# in Statistics / Queries by Properties for identifier-style fields. Identifier
# fields themselves (Id, PipeID, JunctionID, ...) are detected via the CSV property.
_idTagFields = {"tag", "descrip"}
_darkBrushColor = "#D8D8D8"

# Filter condition sets by field category, mirroring Queries by Properties.
_conditionsByType = {
    "numeric": ["All", ">=", "<=", "=", ">", "<", "≠"],
    "listed":  ["All", "="],
    "text":    ["All", "=", "≠", "ILIKE", "NOT ILIKE", "LIKE", "NOT LIKE"],
}

# Item data marking the NULL entry in the filter value list.
_nullFilterData = "__qgisred_null__"

# Free-text fields keep a typed value (no unique-value combobox) and default to ILIKE.
_freeTextFields = {"Descrip", "InstalDate", "InstDate", "Time", "Time_H", "Time_Q", "Time_D"}

# Fields whose Do value offers a combobox sourced from a global_defaults DBF instead of a typed input.
_materialFields = {"Material"}

# Curve reference fields -> required curve type, used to list only matching declared curves from
# {Network}_Curves.dbf. Stored Type values (PUMP/VOLUME/EFFICIENCY/HEADLOSS) are compared case-insensitively.
_curveTypeByField = {
    "IdVolCurve": "volume",
    "VolCurveID": "volume",
    "IdHFCurve":  "pump",
    "PumpCurvID": "pump",
    "IdEffiCur":  "efficiency",
    "EffiCurvID": "efficiency",
    "IdHeadLoss": "headloss",
    "HeadLossID": "headloss",
}
# Pattern reference fields -> accepted pattern types, used to list only matching declared patterns
# from {Network}_Patterns.dbf. Keyed by (identifier, fieldName) because the same field name means a
# different pattern type per element (e.g. IdPattern is quality on Sources but demand on Demands).
_patternTypeByField = {
    ("qgisred_junctions", "IdPattDem"):          ("demand",),
    ("qgisred_junctions", "DemPattID"):          ("demand",),
    ("qgisred_demands", "IdPattern"):            ("demand",),
    ("qgisred_demands", "IdDemPatt"):            ("demand",),
    ("qgisred_sources", "IdPattern"):            ("quality",),
    ("qgisred_sources", "IdQualPatt"):           ("quality",),
    ("qgisred_reservoirs", "IdHeadPatt"):        ("head",),
    ("qgisred_reservoirs", "HeadPattID"):        ("head",),
    ("qgisred_pumps", "IdSpeedPat"):             ("speed", "velocity"),
    ("qgisred_pumps", "IdPricePat"):             ("price",),
    ("qgisred_pumps", "PricePatID"):             ("price",),
    ("qgisred_serviceconnections", "Pattern"):   ("demand",),
    ("qgisred_serviceconnections", "DemPattID"): ("demand",),
}

# Numeric fields that intentionally show no unit (mirrors Queries by Properties).
_suppressUnitProperties = {
    ("qgisred_valves", "Setting"),
    ("qgisred_sources", "BaseValue"),
    ("qgisred_sources", "SourceQual"),
    ("qgisred_demands", "BaseValue"),
    ("qgisred_demands", "BaseDem"),
}

# Preferred property to preselect per element type.
# The first entry that exists as an editable field is selected.
_defaultProperties = {
    "qgisred_pipes":              ["Diameter"],
    "qgisred_pumps":              ["PumpCurvID", "IdHFCurve"],
    "qgisred_valves":             ["Diameter"],
    "qgisred_junctions":          ["BaseDem"],
    "qgisred_tanks":              ["IniLevel"],
    "qgisred_reservoirs":         ["Head", "TotalHead"],
    "qgisred_serviceconnections": ["Diameter"],
    "qgisred_isolationvalves":    ["IniStatus", "Status"],
    "qgisred_meters":             ["MeterType", "Type"],
    "qgisred_sources":            ["SourceQual", "BaseValue"],
}

# Blue highlight with white text, matching the Queries by Attributes dropdowns. A styled popup view
# is forced via setView() in _styleCombo so the color is honoured uniformly and survives the per-field
# restyle, instead of dropdowns falling back to the native popup that ignores selection-background-color.
_comboSelectionOverride = "QComboBox QAbstractItemView { selection-background-color: #3399ff; selection-color: white; }"


class QGISRedGroupEditDialog(QDialog, FORM_CLASS):
    """Bulk-edit dialog for QGISRed network elements (EPANET Group Edit-style)."""

    def __init__(self, parent=None):
        super(QGISRedGroupEditDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/images/iconGroupEdit.svg"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        self._applyStyle()
        self._setupFilterValueStack()
        self._setupTextValueStack()
        self._setupDateCalendarButton()
        for button in (self.btAccept, self.btCancel, self.btApply):
            button.setAutoDefault(False)
            button.setDefault(False)

        self.iface = None
        self.canvas = None
        self.fieldUtils = QGISRedFieldUtils()
        self.layersByIdentifier = {}
        self.previewHighlights = []
        self._previewNeedsRefresh = False
        self.editedLayers = []
        self.openedAttributeTables = {}
        self._countSignalLayers = []

        self.banner = QGISRedBanner.inject(self, self.rootLayout)

        self._countTimer = QTimer(self)
        self._countTimer.setSingleShot(True)
        self._countTimer.setInterval(150)
        self._countTimer.timeout.connect(self._refreshAffectedCount)

        self._valuesTimer = QTimer(self)
        self._valuesTimer.setSingleShot(True)
        self._valuesTimer.setInterval(300)
        self._valuesTimer.timeout.connect(self._refreshValueLists)

        self._connectSignals()
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.rootLayout.setColumnStretch(0, 1)
        self.targetGrid.setColumnStretch(1, 1)
        self.actionGrid.setColumnStretch(1, 1)

    """Public API"""

    def config(self, iface, projectDirectory, networkName):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName
        self.fieldUtils = QGISRedFieldUtils(projectDirectory, networkName, iface)
        self._populateElementTypes()

    def closeEvent(self, event):
        super(QGISRedGroupEditDialog, self).closeEvent(event)
        if event.isAccepted():
            self._removePreviewHighlights()
            self._disconnectCountSignals()

    def reject(self):
        if self._hasPendingChanges():
            reply = QMessageBox.question(
                self,
                self.tr("Edit properties by group"),
                self.tr("All changes made will be discarded. Continue?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self._rollbackEdits()
        self._closeAttributeTables()
        self._removePreviewHighlights()
        self._disconnectCountSignals()
        super(QGISRedGroupEditDialog, self).reject()

    def hideEvent(self, event):
        self._hidePreviewHighlights()
        super(QGISRedGroupEditDialog, self).hideEvent(event)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ActivationChange:
            if self.isActiveWindow():
                self._restorePreviewHighlights()
            else:
                self._hidePreviewHighlights()
        super(QGISRedGroupEditDialog, self).changeEvent(event)

    """Setup"""

    def _applyStyle(self):
        self.setStyleSheet(
            "QDialog { background-color: #f8f9fb; }"
            "QGroupBox { font-weight: bold; }"
            "QLineEdit, QSpinBox, QDoubleSpinBox {"
            " background-color: white;"
            " color: #202020;"
            " border: 1px solid #bdbdbd;"
            " border-radius: 2px;"
            " padding: 0 4px 0 5px;"
            " min-height: 18px;"
            " max-height: 20px;"
            " font-size: 8pt;"
            " }"
        )
        for combo in self.findChildren(QComboBox):
            self._styleCombo(combo)

    def _styleCombo(self, combo, background="white"):
        combo.setStyleSheet(
            QGISRED_COMBO_STYLE + _comboSelectionOverride + "QComboBox { background-color: %s; }" % background
        )
        combo.setView(QListView(combo))

    def _connectSignals(self):
        self.cbElementType.currentIndexChanged.connect(self._onElementTypeChanged)
        self.chkOnlySelected.toggled.connect(self._onOnlySelectedChanged)
        self.cbFilterProperty.currentIndexChanged.connect(self._onFilterPropertyChanged)
        self.cbFilterOperator.currentIndexChanged.connect(self._onFilterConditionChanged)
        self.cbFilterOperator.currentIndexChanged.connect(self._updateFilterValues)
        self.leFilterValue.textChanged.connect(self._scheduleCount)
        self.cbFilterValueList.currentTextChanged.connect(self._scheduleCount)
        self.leFilterValue.textChanged.connect(self._syncDateFromFilter)
        self.cbFilterValueList.currentTextChanged.connect(self._syncDateFromFilter)
        self.cbProperty.currentIndexChanged.connect(self._onPropertyChanged)
        self.cbAction.currentIndexChanged.connect(self._onActionChanged)
        self.chkPreview.toggled.connect(self._onPreviewToggled)
        self.btApply.clicked.connect(self._onApply)
        self.btAccept.clicked.connect(self._onAccept)
        self.btCancel.clicked.connect(self.reject)

    def _populateElementTypes(self):
        self.layersByIdentifier = {}
        for layer in QgsProject.instance().mapLayers().values():
            identifier = layer.customProperty("qgisred_identifier")
            if identifier in _elementLayerOrder:
                self.layersByIdentifier[identifier] = layer

        self.cbElementType.blockSignals(True)
        self.cbElementType.clear()
        for identifier in _elementLayerOrder:
            if identifier not in self.layersByIdentifier:
                continue
            if identifier == "qgisred_demands" and self.layersByIdentifier[identifier].featureCount() <= 0:
                continue
            label = self._elementDisplayName(identifier)
            self.cbElementType.addItem(label, identifier)
        self.cbElementType.blockSignals(False)

        if self.cbElementType.count() == 0:
            self.banner.pushMessage(
                self.tr("No layers"),
                self.tr("No QGISRed network layers found in the project."),
                level=2, duration=8,
            )
            self.btApply.setEnabled(False)
            self.chkPreview.setEnabled(False)
            return

        self.cbElementType.setCurrentIndex(0)
        self._onElementTypeChanged()

    def _elementDisplayName(self, identifier):
        nameMap = {
            "qgisred_junctions":          self.tr("Junctions"),
            "qgisred_demands":            self.tr("Multiple Demands"),
            "qgisred_pipes":              self.tr("Pipes"),
            "qgisred_tanks":              self.tr("Tanks"),
            "qgisred_reservoirs":         self.tr("Reservoirs"),
            "qgisred_pumps":              self.tr("Pumps"),
            "qgisred_valves":             self.tr("Valves"),
            "qgisred_sources":            self.tr("Sources"),
            "qgisred_serviceconnections": self.tr("Service Connections"),
            "qgisred_isolationvalves":    self.tr("Isolation Valves"),
            "qgisred_meters":             self.tr("Meters"),
        }
        return nameMap.get(identifier, identifier)

    """Element type / property wiring"""

    def _onElementTypeChanged(self):
        layer = self._currentLayer()
        if layer is None:
            return
        self._populatePropertyCombos(layer)
        self._onPropertyChanged()
        self._onFilterPropertyChanged()
        self._connectCountSignals()
        self._scheduleCount()

    def _populatePropertyCombos(self, layer):
        identifier = layer.customProperty("qgisred_identifier")
        readonly = _readonlyFields.get(identifier, set())
        editable = []
        filterable = []
        for field in layer.fields():
            name = field.name()
            if name.lower() == "geometry":
                continue
            pretty = self.fieldUtils.getProperty(normalize_element(identifier), name)
            if name not in readonly:
                editable.append((name, pretty, field))
            filterable.append((name, pretty, field))

        self.cbProperty.blockSignals(True)
        self.cbProperty.clear()
        for name, pretty, field in editable:
            self.cbProperty.addItem(pretty, name)
        self._setPropertyItemBackgrounds(self.cbProperty, identifier)
        self._selectDefaultProperty(self.cbProperty, identifier)
        self.cbProperty.blockSignals(False)

        self.cbFilterProperty.blockSignals(True)
        self.cbFilterProperty.clear()
        for name, pretty, field in filterable:
            self.cbFilterProperty.addItem(pretty, name)
        self._setPropertyItemBackgrounds(self.cbFilterProperty, identifier)
        self._selectDefaultProperty(self.cbFilterProperty, identifier)
        self.cbFilterProperty.blockSignals(False)

        self._updateComboBackground(self.cbProperty)
        self._updateComboBackground(self.cbFilterProperty)

    def _selectDefaultProperty(self, combo, identifier):
        for defaultProp in _defaultProperties.get(identifier, []):
            index = combo.findData(defaultProp)
            if index >= 0:
                combo.setCurrentIndex(index)
                return

    def _setPropertyItemBackgrounds(self, combo, identifier):
        for index in range(combo.count()):
            fieldName = combo.itemData(index)
            if not fieldName:
                continue
            if str(fieldName).lower() in _idTagFields or self._isIdentifierField(identifier, fieldName):
                combo.setItemData(index, QBrush(QColor(_darkBrushColor)), Qt.ItemDataRole.BackgroundRole)

    def _updateComboBackground(self, combo):
        brush = combo.currentData(Qt.ItemDataRole.BackgroundRole)
        if brush and isinstance(brush, QBrush) and brush.color() != QColor(0, 0, 0, 255):
            color = brush.color().name()
        else:
            color = "white"
        self._styleCombo(combo, color)

    def _onPropertyChanged(self):
        layer = self._currentLayer()
        if layer is None:
            return
        self._updateComboBackground(self.cbProperty)
        identifier = layer.customProperty("qgisred_identifier")
        fieldName = self.cbProperty.currentData()
        if not fieldName:
            return
        field = layer.fields().field(fieldName)
        kind = self._propertyValueKind(identifier, fieldName, field)

        self.cbAction.blockSignals(True)
        self.cbAction.clear()
        if kind.startswith("enum"):
            for key, label, actionKind in _enumActions:
                self.cbAction.addItem(self.tr(label), (key, actionKind))
            self._populateEnumValues(identifier, fieldName, kind)
        elif kind == "date":
            for key, label, actionKind in _dateActions:
                self.cbAction.addItem(self.tr(label), (key, actionKind))
            self._populateDateValues(layer, fieldName)
        elif kind == "numeric":
            for key, label, actionKind in _numericActions:
                self.cbAction.addItem(self.tr(label), (key, actionKind))
        else:
            for key, label, actionKind in _textActions:
                self.cbAction.addItem(self.tr(label), (key, actionKind))
        self.cbAction.blockSignals(False)
        self._updateUnitLabel(identifier, fieldName, field)
        self._onActionChanged()

    def _propertyValueKind(self, identifier, fieldName, field):
        if _enumFields.get(identifier, {}).get(fieldName) is not None:
            return "enum-fixed"
        if fieldName in _materialFields:
            return "enum-material"
        if fieldName in _curveTypeByField:
            return "enum-curve"
        if (identifier, fieldName) in _patternTypeByField:
            return "enum-pattern"
        if self._isDateField(identifier, fieldName):
            return "date"
        if field.isNumeric():
            return "numeric"
        return "text"

    def _isDateField(self, identifier, fieldName):
        try:
            return self.fieldUtils.isDateField(normalize_element(identifier), fieldName)
        except Exception:
            return False

    def _populateEnumValues(self, identifier, fieldName, kind):
        if kind == "enum-fixed":
            values = list(_enumFields.get(identifier, {}).get(fieldName, []))
        elif kind == "enum-material":
            values = self._dbfFieldValues(fieldName)
        elif kind == "enum-curve":
            values = self._declaredCurveOrPatternValues(self._projectDbfPath("Curves"), _curveTypeByField.get(fieldName))
        elif kind == "enum-pattern":
            values = self._declaredCurveOrPatternValues(
                self._projectDbfPath("Patterns"), _patternTypeByField.get((identifier, fieldName))
            )
        else:
            values = []
        previous = self.cbEnum.currentText()
        self.cbEnum.blockSignals(True)
        self.cbEnum.clear()
        self.cbEnum.addItems(values)
        index = self.cbEnum.findText(previous)
        if index >= 0:
            self.cbEnum.setCurrentIndex(index)
        self.cbEnum.blockSignals(False)

    def _populateDateValues(self, layer, fieldName):
        rawValues = self._getUniqueFieldValues(layer, fieldName)
        values = sorted({str(v) for v in rawValues if v is not None and str(v).strip()})
        previous = self.cbDate.currentText()
        self.cbDate.blockSignals(True)
        self.cbDate.clear()
        for value in values:
            self.cbDate.addItem(self._formatDateDisplay(value), value)
        index = self.cbDate.findText(previous)
        if index >= 0:
            self.cbDate.setCurrentIndex(index)
        self.cbDate.blockSignals(False)
        if index < 0:
            self._setDateValue(self._defaultDateValue())

    def _setupDateCalendarButton(self):
        iconPath = os.path.join(os.path.dirname(__file__), "..", "..", "images", "iconCalendar.svg")
        self.btDateCalendar = QToolButton(self)
        self.btDateCalendar.setIcon(QIcon(iconPath))
        self.btDateCalendar.setIconSize(QSize(16, 16))
        self.btDateCalendar.setFixedSize(20, 20)
        self.btDateCalendar.setAutoRaise(True)
        self.btDateCalendar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btDateCalendar.setToolTip(self.tr("Pick a date from a calendar"))
        self.btDateCalendar.clicked.connect(self._openDateCalendar)
        self.hlDate.addWidget(self.btDateCalendar)

        self.dateCalendar = QCalendarWidget(self)
        self.dateCalendar.setWindowFlags(Qt.WindowType.Popup)
        self.dateCalendar.clicked.connect(self._onCalendarDateClicked)

    def _openDateCalendar(self):
        currentDate = self._dateFromText(self.cbDate.currentText())
        if currentDate is None:
            currentDate = self._defaultDateValue()
        self.dateCalendar.setSelectedDate(currentDate)
        self.dateCalendar.move(self.btDateCalendar.mapToGlobal(self.btDateCalendar.rect().bottomLeft()))
        self.dateCalendar.show()

    def _onCalendarDateClicked(self, date):
        self.dateCalendar.hide()
        self._setDateValue(date)

    def _syncDateFromFilter(self):
        if self.stackedValue.currentIndex() != _pageDate:
            return
        filterDate = self._filterSelectedDate()
        if filterDate is not None:
            self._setDateValue(filterDate)

    def _filterSelectedDate(self):
        layer = self._currentLayer()
        fieldName = self.cbFilterProperty.currentData()
        if layer is None or not fieldName:
            return None
        identifier = layer.customProperty("qgisred_identifier")
        if not self._isDateField(identifier, fieldName):
            return None
        if self.cbFilterOperator.currentText() == "All":
            return None
        return self._dateFromText(self._currentFilterValueText())

    def _defaultDateValue(self):
        filterDate = self._filterSelectedDate()
        if filterDate is not None:
            return filterDate
        count = self.cbDate.count()
        if count > 0:
            middle = (count - 1) // 2
            middleDate = self._dateFromText(str(self.cbDate.itemData(middle) or self.cbDate.itemText(middle)))
            if middleDate is not None:
                return middleDate
        return QDate(1980, 1, 1)

    def _setDateValue(self, date):
        rawValue = date.toString("yyyyMMdd")
        index = self.cbDate.findData(rawValue)
        if index >= 0:
            self.cbDate.setCurrentIndex(index)
        else:
            self.cbDate.setEditText(self._formatDateDisplay(rawValue))

    def _dateFromText(self, text):
        digits = self._parseDateInput(text)
        if len(digits) == 8 and digits.isdigit():
            date = QDate(int(digits[0:4]), int(digits[4:6]), int(digits[6:8]))
            if date.isValid():
                return date
        return None

    def _projectDbfPath(self, suffix):
        projectDirectory = getattr(self, "ProjectDirectory", None)
        networkName = getattr(self, "NetworkName", None)
        if not projectDirectory or not networkName:
            return ""
        return os.path.join(projectDirectory, "%s_%s.dbf" % (networkName, suffix))

    def _declaredCurveOrPatternValues(self, path, expectedTypes):
        if not path or not os.path.exists(path):
            return []
        if isinstance(expectedTypes, str):
            expectedTypes = (expectedTypes,)
        layer = QgsVectorLayer(path, "groupedit_cp", "ogr")
        if not layer.isValid():
            return []
        fieldNames = [f.name() for f in layer.fields()]
        if not fieldNames:
            return []
        idField = next((name for name in fieldNames if name.lower().endswith("id")), fieldNames[0])
        typeField = next((name for name in fieldNames if name.lower().endswith("type")), None)
        # The declared type is the first non-empty Type value among an id's rows; continuation
        # rows carry an empty Type. Ids never typed count as undefined.
        typeById = {}
        orderedIds = []
        for feature in layer.getFeatures():
            idValue = feature[idField]
            if idValue is None:
                continue
            text = str(idValue).strip()
            if not text:
                continue
            if text not in typeById:
                typeById[text] = ""
                orderedIds.append(text)
            if typeField is not None and not typeById[text]:
                typeValue = feature[typeField]
                if typeValue is not None:
                    typeById[text] = str(typeValue).strip().lower()
        if typeField is None or expectedTypes is None:
            return orderedIds
        return [idText for idText in orderedIds
                if typeById[idText] in expectedTypes or typeById[idText] in ("", "undefined")]

    def _onActionChanged(self):
        data = self.cbAction.currentData()
        if not data:
            return
        actionKey, kind = data
        if kind == "numeric":
            self.stackedValue.setCurrentIndex(_pageNumber)
        elif kind == "text":
            self._updateTextValues()
            self.stackedValue.setCurrentIndex(_pageText)
        elif kind == "enum":
            self.stackedValue.setCurrentIndex(_pageEnum)
        elif kind == "date":
            self.stackedValue.setCurrentIndex(_pageDate)
        elif kind == "findReplace":
            self.stackedValue.setCurrentIndex(_pageFindReplace)
        self._updateUnitVisibility(actionKey, kind)
        self._scheduleCount()

    def _updateTextValues(self):
        fieldName = self.cbProperty.currentData()
        strValues = self._dbfFieldValues(fieldName) if fieldName else []
        if strValues:
            previous = self._currentTextValue()
            self.cbTextValueList.blockSignals(True)
            self.cbTextValueList.clear()
            self.cbTextValueList.addItem("")
            self.cbTextValueList.addItems(strValues)
            i = self.cbTextValueList.findText(previous)
            self.cbTextValueList.setCurrentIndex(i if i >= 0 else 0)
            self.cbTextValueList.blockSignals(False)
            self.textValueStack.setCurrentWidget(self.cbTextValueList)
        else:
            self.textValueStack.setCurrentWidget(self.leText)

    def _dbfFieldValues(self, fieldName):
        if fieldName not in _materialFields:
            return []
        language = "es" if QgsApplication.locale()[0:2] == "es" else "en"
        folder = os.path.join(QGISRedFileSystemUtils().getQGISRedFolder(), "global_defaults")
        path = os.path.join(folder, "Materials_%s.dbf" % language)
        if not os.path.exists(path):
            return []
        layer = QgsVectorLayer(path, "Materials", "ogr")
        if not layer.isValid():
            return []
        values = []
        for feature in layer.getFeatures():
            value = feature["Abbrev"]
            if value is not None and str(value).strip():
                values.append(str(value).strip())
        return values

    def _updateUnitLabel(self, identifier, fieldName, field):
        unit = ""
        if field.isNumeric() and (identifier, fieldName) not in _suppressUnitProperties:
            try:
                unit = self.fieldUtils.getUnitAbbreviation(normalize_element(identifier), fieldName) or ""
            except Exception:
                unit = ""
        self.lblUnit.setText(unit)
        decimals = 4
        with suppress(Exception):
            decimals = max(2, self.fieldUtils.getDecimals(normalize_element(identifier), fieldName, default=4))
        self.sbNumber.setDecimals(decimals)

    def _updateUnitVisibility(self, actionKey, kind):
        showUnit = kind == "numeric" and actionKey not in ("multiply", "divide")
        self.lblUnit.setVisible(showUnit)

    """Filter wiring"""

    def _setupFilterValueStack(self):
        idx = self.filterGrid.indexOf(self.leFilterValue)
        row, col, rowSpan, colSpan = self.filterGrid.getItemPosition(idx)
        sizePolicy = self.leFilterValue.sizePolicy()

        self.cbFilterValueList = QComboBox(self)
        self.cbFilterValueList.setEditable(False)
        self.cbFilterValueList.setSizePolicy(sizePolicy)
        self._styleCombo(self.cbFilterValueList)

        self.filterValueStack = QStackedWidget(self)
        self.filterValueStack.setSizePolicy(sizePolicy)
        self.filterGrid.removeWidget(self.leFilterValue)
        self.filterValueStack.addWidget(self.leFilterValue)
        self.filterValueStack.addWidget(self.cbFilterValueList)
        self.filterGrid.addWidget(self.filterValueStack, row, col, rowSpan, colSpan)

    def _setupTextValueStack(self):
        sizePolicy = self.leText.sizePolicy()
        self.cbTextValueList = QComboBox(self)
        self.cbTextValueList.setEditable(False)
        self.cbTextValueList.setSizePolicy(sizePolicy)
        self._styleCombo(self.cbTextValueList)

        self.textValueStack = QStackedWidget(self)
        self.textValueStack.setSizePolicy(sizePolicy)
        self.hlText.removeWidget(self.leText)
        self.textValueStack.addWidget(self.leText)
        self.textValueStack.addWidget(self.cbTextValueList)
        self.hlText.addWidget(self.textValueStack)

    def _onFilterPropertyChanged(self):
        layer = self._currentLayer()
        if layer is None or self.cbFilterProperty.currentData() is None:
            return
        self._updateComboBackground(self.cbFilterProperty)
        identifier = layer.customProperty("qgisred_identifier")
        fieldName = self.cbFilterProperty.currentData()
        field = layer.fields().field(fieldName)
        if field.isNumeric():
            category = "numeric"
            self.leFilterValue.setValidator(QDoubleValidator(self))
        else:
            category = "text"
            self.leFilterValue.setValidator(None)
        self.cbFilterOperator.blockSignals(True)
        self.cbFilterOperator.clear()
        self.cbFilterOperator.addItems(_conditionsByType[category])
        if category == "numeric":
            defaultCondition = "<="
        elif self._isDateField(identifier, fieldName):
            defaultCondition = "="
        elif self._isFreeTextField(identifier, fieldName):
            defaultCondition = "ILIKE"
        else:
            defaultCondition = "="
        defaultIndex = self.cbFilterOperator.findText(defaultCondition)
        if defaultIndex >= 0:
            self.cbFilterOperator.setCurrentIndex(defaultIndex)
        self.cbFilterOperator.blockSignals(False)
        self._onFilterConditionChanged()
        self._updateFilterValues()

    def _onFilterConditionChanged(self):
        isAll = self.cbFilterOperator.currentText() == "All"
        self.leFilterValue.setEnabled(not isAll)
        self.cbFilterValueList.setEnabled(not isAll)
        if isAll:
            self._setCurrentFilterValueText("")
        self._scheduleCount()

    def _updateFilterValues(self):
        fieldName = self.cbFilterProperty.currentData()
        condition = self.cbFilterOperator.currentText()
        layer = self._currentLayer()
        useList = False
        isDate = False
        hasNull = False
        strValues = []
        if layer is not None and fieldName and condition in ("=", "≠"):
            identifier = layer.customProperty("qgisred_identifier")
            field = layer.fields().field(fieldName)
            isDate = self._isDateField(identifier, fieldName)
            if isDate or (not field.isNumeric() and not self._isFreeTextField(identifier, fieldName)):
                uniqueValues = self._getUniqueFieldValues(layer, fieldName)
                hasNull = any(self._isNullValue(v) for v in uniqueValues)
                strValues = sorted({str(v) for v in uniqueValues if not self._isNullValue(v) and str(v).strip()})
                useList = bool(strValues) or hasNull
        if useList:
            previous = self._currentFilterValueText()
            self.cbFilterValueList.blockSignals(True)
            self.cbFilterValueList.clear()
            self.cbFilterValueList.addItem("")
            if hasNull:
                self.cbFilterValueList.addItem("NULL", _nullFilterData)
            for value in strValues:
                self.cbFilterValueList.addItem(self._formatDateDisplay(value) if isDate else value, value)
            i = self.cbFilterValueList.findData(previous)
            self.cbFilterValueList.setCurrentIndex(i if i >= 0 else 0)
            self.cbFilterValueList.blockSignals(False)
            self.filterValueStack.setCurrentWidget(self.cbFilterValueList)
        else:
            self.filterValueStack.setCurrentWidget(self.leFilterValue)

    """Scope / selection"""

    def _onOnlySelectedChanged(self):
        self._connectCountSignals()
        self._scheduleCount()

    def _connectCountSignals(self):
        self._disconnectCountSignals()
        elementLayer = self._currentLayer()
        if elementLayer is not None:
            with suppress(Exception):
                elementLayer.selectionChanged.connect(self._scheduleCount)
                elementLayer.layerModified.connect(self._scheduleValuesRefresh)
                self._countSignalLayers.append(elementLayer)

    def _disconnectCountSignals(self):
        for layer in self._countSignalLayers:
            self.safeDisconnect(layer.selectionChanged, self._scheduleCount)
            self.safeDisconnect(layer.layerModified, self._scheduleValuesRefresh)
        self._countSignalLayers = []

    def safeDisconnect(self, signal, slot):
        with suppress(TypeError, RuntimeError):
            signal.disconnect(slot)

    """Affected count and matching"""

    def _scheduleCount(self):
        self._countTimer.start()

    def _scheduleValuesRefresh(self):
        self._valuesTimer.start()

    def _refreshValueLists(self):
        layer = self._currentLayer()
        if layer is None:
            return
        self._updateFilterValues()
        fieldName = self.cbProperty.currentData()
        if fieldName and self.stackedValue.currentIndex() == _pageDate:
            self._populateDateValues(layer, fieldName)
        self._scheduleCount()

    def _refreshAffectedCount(self):
        layer = self._currentLayer()
        if layer is None:
            self.lblAffectedCount.setText(self.tr("0 elements match"))
            self._refreshPreview([])
            return
        try:
            features = self._matchingFeatures(layer)
        except Exception:
            features = []
        self.lblAffectedCount.setText(self.tr("%d elements match") % len(features))
        self._refreshPreview(features)

    def _candidateFids(self, layer):
        if self.chkOnlySelected.isChecked():
            return list(layer.selectedFeatureIds())
        return None  # whole layer

    def _matchingFeatures(self, layer):
        candidate = self._candidateFids(layer)
        if candidate is None:
            request = QgsFeatureRequest()
        else:
            if not candidate:
                return []
            request = QgsFeatureRequest().setFilterFids(candidate)
        features = list(layer.getFeatures(request))

        expression = self._buildFilterExpression(layer)
        if expression is None:
            return features

        context = QgsExpressionContext()
        context.appendScope(QgsExpressionContextUtils.layerScope(layer))
        if not expression.prepare(context):
            return features
        matched = []
        for f in features:
            context.setFeature(f)
            if bool(expression.evaluate(context)):
                matched.append(f)
        return matched

    def _buildFilterExpression(self, layer):
        fieldName = self.cbFilterProperty.currentData()
        condition = self.cbFilterOperator.currentText()
        if not fieldName or not condition or condition == "All":
            return None
        rawValue = self._currentFilterValueText().strip()
        if rawValue == "":
            return None
        field = layer.fields().field(fieldName)
        column = QgsExpression.quotedColumnRef(fieldName)
        if self._isFilterValueListActive() and self.cbFilterValueList.currentData() == _nullFilterData:
            if condition == "≠":
                return QgsExpression("%s IS NOT NULL" % column)
            return QgsExpression("%s IS NULL" % column)
        if field.isNumeric():
            try:
                literal = repr(float(rawValue))
            except ValueError:
                return None
            operator = "<>" if condition == "≠" else condition
            return QgsExpression("%s %s %s" % (column, operator, literal))
        literal = QgsExpression.quotedString(rawValue)
        if condition == "=":
            return QgsExpression("lower(%s) = lower(%s)" % (column, literal))
        if condition == "≠":
            return QgsExpression("lower(%s) <> lower(%s)" % (column, literal))
        wildcard = QgsExpression.quotedString("%%%s%%" % rawValue)
        if condition == "LIKE":
            return QgsExpression("%s LIKE %s" % (column, wildcard))
        if condition == "NOT LIKE":
            return QgsExpression("%s NOT LIKE %s" % (column, wildcard))
        if condition == "ILIKE":
            return QgsExpression("%s ILIKE %s" % (column, wildcard))
        if condition == "NOT ILIKE":
            return QgsExpression("%s NOT ILIKE %s" % (column, wildcard))
        return None

    """Preview"""

    def _onPreviewToggled(self, checked):
        if checked:
            self._refreshPreview()
        else:
            self._removePreviewHighlights()

    def _refreshPreview(self, features=None):
        if not self.chkPreview.isChecked():
            self._removePreviewHighlights()
            return
        if not self.isActiveWindow():
            self._previewNeedsRefresh = True
            return
        self._removePreviewHighlights()
        self._previewNeedsRefresh = False
        layer = self._currentLayer()
        if layer is None:
            return
        if features is None:
            try:
                features = self._matchingFeatures(layer)
            except Exception:
                return
        for f in features:
            geom = f.geometry()
            if geom is None or geom.isEmpty():
                continue
            highlight = QgsHighlight(self.canvas, geom, layer)
            highlight.setColor(QColor(255, 140, 0))
            highlight.setWidth(3)
            highlight.show()
            self.previewHighlights.append(highlight)

    def _hidePreviewHighlights(self):
        for highlight in self.previewHighlights:
            with suppress(Exception):
                highlight.hide()

    def _restorePreviewHighlights(self):
        if self._previewNeedsRefresh:
            self._refreshPreview()
            return
        for highlight in self.previewHighlights:
            with suppress(Exception):
                highlight.show()

    def _removePreviewHighlights(self):
        if not self.previewHighlights:
            return
        scene = self.canvas.scene() if self.canvas is not None else None
        for highlight in self.previewHighlights:
            with suppress(Exception):
                highlight.hide()
            if scene is not None:
                with suppress(Exception):
                    scene.removeItem(highlight)
        self.previewHighlights = []
        if self.canvas is not None:
            with suppress(Exception):
                self.canvas.refresh()

    """Apply"""

    def _onApply(self):
        layer = self._currentLayer()
        if layer is None:
            return
        fieldName = self.cbProperty.currentData()
        if not fieldName:
            return
        actionData = self.cbAction.currentData()
        if not actionData:
            return
        actionKey, actionKind = actionData

        try:
            features = self._matchingFeatures(layer)
        except Exception as e:
            self.banner.pushMessage(self.tr("Apply"), str(e), level=2, duration=6)
            return
        if not features:
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("No elements match the current target and filter."),
                                    level=1, duration=5)
            return

        try:
            edits = self._computeEdits(features, fieldName, actionKey, actionKind, layer)
        except _GroupEditError as e:
            self.banner.pushMessage(self.tr("Apply"), str(e), level=2, duration=6)
            return

        if not self._applyEdits(layer, fieldName, edits):
            return
        identifier = layer.customProperty("qgisred_identifier")
        self._warnSoftBounds(identifier, fieldName, edits)
        self._openAttributeTable(layer, [fid for fid, _oldVal, _newVal in edits])

    def _computeEdits(self, features, fieldName, actionKey, actionKind, layer):
        edits = []  # list of (fid, oldValue, newValue)
        if actionKind == "numeric":
            try:
                operand = float(self.sbNumber.value())
            except Exception:
                raise _GroupEditError(self.tr("Invalid numeric value."))
            if actionKey == "divide" and operand == 0.0:
                raise _GroupEditError(self.tr("Divide by zero is not allowed."))
            for f in features:
                oldRaw = f[fieldName]
                oldVal = self._coerceFloat(oldRaw)
                newVal = self._applyNumericOp(oldVal, operand, actionKey)
                edits.append((f.id(), oldRaw, newVal))
        elif actionKind == "text":
            text = self._currentTextValue()
            for f in features:
                oldRaw = f[fieldName]
                oldStr = "" if oldRaw is None else str(oldRaw)
                if actionKey == "set":
                    newVal = text
                elif actionKey == "prepend":
                    newVal = text + oldStr
                elif actionKey == "append":
                    newVal = oldStr + text
                else:
                    newVal = oldStr
                edits.append((f.id(), oldRaw, newVal))
        elif actionKind == "findReplace":
            findText = self.leFind.text()
            replaceText = self.leReplace.text()
            if findText == "":
                raise _GroupEditError(self.tr("Find text cannot be empty."))
            for f in features:
                oldRaw = f[fieldName]
                oldStr = "" if oldRaw is None else str(oldRaw)
                newVal = oldStr.replace(findText, replaceText)
                edits.append((f.id(), oldRaw, newVal))
        elif actionKind == "enum":
            newVal = self.cbEnum.currentText()
            for f in features:
                oldRaw = f[fieldName]
                edits.append((f.id(), oldRaw, newVal))
        elif actionKind == "date":
            newVal = self._parseDateInput(self.cbDate.currentText())
            for f in features:
                oldRaw = f[fieldName]
                edits.append((f.id(), oldRaw, newVal))
        return edits

    def _applyNumericOp(self, oldVal, operand, actionKey):
        if actionKey == "replace":
            return operand
        if oldVal is None:
            oldVal = 0.0
        if actionKey == "multiply":
            return oldVal * operand
        if actionKey == "add":
            return oldVal + operand
        if actionKey == "subtract":
            return oldVal - operand
        if actionKey == "divide":
            return oldVal / operand
        if actionKey == "clampMin":
            return max(oldVal, operand)
        if actionKey == "clampMax":
            return min(oldVal, operand)
        return oldVal

    def _coerceFloat(self, value):
        if value is None:
            return None
        if isinstance(value, QVariant) and value.isNull():
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _warnSoftBounds(self, identifier, fieldName, edits):
        bounds = _softBounds.get((identifier, fieldName))
        if bounds is None:
            return
        lo, hi = bounds
        outOfRange = 0
        for _fid, _oldVal, newVal in edits:
            if not isinstance(newVal, (int, float)):
                continue
            if (lo is not None and newVal < lo) or (hi is not None and newVal > hi):
                outOfRange += 1
        if outOfRange:
            self.banner.pushMessage(
                self.tr("Apply"),
                self.tr("Warning: %d value(s) fall outside the typical range for this field.") % outOfRange,
                level=1, duration=6,
            )

    def _applyEdits(self, layer, fieldName, edits):
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("Field not found in layer."),
                                    level=2, duration=6)
            return False
        if not layer.isEditable() and not layer.startEditing():
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("Could not start editing the layer."),
                                    level=2, duration=6)
            return False
        layer.beginEditCommand("Group Edit")
        try:
            for fid, _oldVal, newVal in edits:
                layer.changeAttributeValue(fid, fieldIdx, newVal)
        except Exception as e:
            layer.destroyEditCommand()
            self.banner.pushMessage(self.tr("Apply"), str(e), level=2, duration=6)
            return False
        layer.endEditCommand()
        if layer not in self.editedLayers:
            self.editedLayers.append(layer)
        layer.triggerRepaint()
        self.banner.pushMessage(self.tr("Apply"),
                                self.tr("Changing %d elements.") % len(edits),
                                level=0, duration=5)
        self._refreshAffectedCount()
        return True

    def _openAttributeTable(self, layer, fids):
        layer.selectByIds(fids)
        existingDialogs = self._existingAttributeTables(layer)
        if existingDialogs:
            dialog = next((d for d in existingDialogs if self._enclosingDock(d) is not None), existingDialogs[0])
            for duplicate in existingDialogs:
                if duplicate is not dialog:
                    self._closeAttributeTable(duplicate)
            self.openedAttributeTables[layer.id()] = dialog
            with suppress(RuntimeError):
                self._raiseAttributeTable(dialog)
            return
        settings = QgsSettings()
        previousDocked = settings.value("qgis/dockAttributeTable", False, type=bool)
        settings.setValue("qgis/dockAttributeTable", True)
        try:
            dialog = self.iface.showAttributeTable(layer)
        finally:
            settings.setValue("qgis/dockAttributeTable", previousDocked)
        if dialog is not None:
            self.openedAttributeTables[layer.id()] = dialog
            self._dockAttributeTable(dialog)
            self._stackAttributeTables(dialog)
            self._raiseAttributeTable(dialog)

    def _dockAttributeTable(self, dialog):
        if self._enclosingDock(dialog) is not None:
            return
        dockAction = self._findDockAction(dialog)
        if dockAction is not None and not dockAction.isChecked():
            dockAction.setChecked(True)

    def _stackAttributeTables(self, dialog):
        dock = self._enclosingDock(dialog)
        if dock is None:
            return
        for otherDialog in self.openedAttributeTables.values():
            if otherDialog is dialog:
                continue
            with suppress(RuntimeError):
                otherDock = self._enclosingDock(otherDialog)
                if otherDock is not None and otherDock is not dock:
                    self.iface.mainWindow().tabifyDockWidget(otherDock, dock)
                    return

    def _findDockAction(self, dialog):
        dockAction = dialog.findChild(QAction, "mActionDockUndock")
        if dockAction is not None:
            return dockAction
        # Newer QGIS creates the dock action unnamed and appends it last to the table toolbar
        toolbar = dialog.findChild(QToolBar, "mToolbar")
        if toolbar is None:
            return None
        for toolbarAction in reversed(toolbar.actions()):
            if toolbarAction.isCheckable():
                return toolbarAction
        return None

    def _raiseAttributeTable(self, dialog):
        selectedOnTop = dialog.findChild(QAction, "mActionSelectedToTop")
        if selectedOnTop is not None and not selectedOnTop.isChecked():
            selectedOnTop.setChecked(True)
        dock = self._enclosingDock(dialog)
        if dock is not None:
            dock.show()
            dock.raise_()
        else:
            dialog.show()
            dialog.raise_()

    def _enclosingDock(self, widget):
        parent = widget.parent()
        while parent is not None:
            if isinstance(parent, QDockWidget):
                return parent
            parent = parent.parent()
        return None

    def _onAccept(self):
        if self._hasPendingChanges():
            summaryLines = self._pendingChangesSummary()
            if summaryLines and not self._confirmAccept(summaryLines):
                return
        elif not self._applyBeforeAccept():
            return
        for layer in self.editedLayers:
            if layer.isEditable() and not layer.commitChanges():
                self.banner.pushMessage(self.tr("Accept"),
                                        self.tr("Failed to commit changes: %s") % "; ".join(layer.commitErrors()),
                                        level=2, duration=8)
                return
        self.editedLayers = []
        self._removePreviewHighlights()
        self._disconnectCountSignals()
        self.accept()

    def _hasPendingChanges(self):
        for layer in self.editedLayers:
            if layer.isEditable() and layer.editBuffer() and layer.editBuffer().changedAttributeValues():
                return True
        return False

    def _applyBeforeAccept(self):
        layer = self._currentLayer()
        if layer is None:
            return True
        fieldName = self.cbProperty.currentData()
        actionData = self.cbAction.currentData()
        if not fieldName or not actionData:
            return True
        actionKey, actionKind = actionData
        try:
            features = self._matchingFeatures(layer)
        except Exception as e:
            self.banner.pushMessage(self.tr("Accept"), str(e), level=2, duration=6)
            return False
        if not features:
            return True
        try:
            edits = self._computeEdits(features, fieldName, actionKey, actionKind, layer)
        except _GroupEditError as e:
            self.banner.pushMessage(self.tr("Accept"), str(e), level=2, duration=6)
            return False
        identifier = layer.customProperty("qgisred_identifier")
        prettyField = self.fieldUtils.getProperty(normalize_element(identifier), fieldName)
        summaryLine = "- %s: %s (%d %s)" % (self._elementDisplayName(identifier), prettyField,
                                            len(edits), self.tr("elements"))
        if not self._confirmAccept([summaryLine]):
            return False
        if not self._applyEdits(layer, fieldName, edits):
            return False
        self._warnSoftBounds(identifier, fieldName, edits)
        self._openAttributeTable(layer, [fid for fid, _oldVal, _newVal in edits])
        return True

    def _pendingChangesSummary(self):
        lines = []
        for layer in self.editedLayers:
            if not layer.isEditable():
                continue
            changed = layer.editBuffer().changedAttributeValues()
            if not changed:
                continue
            identifier = layer.customProperty("qgisred_identifier")
            fieldIndexes = set()
            for attributes in changed.values():
                fieldIndexes.update(attributes.keys())
            prettyFields = [
                self.fieldUtils.getProperty(normalize_element(identifier), layer.fields().at(index).name())
                for index in sorted(fieldIndexes)
            ]
            lines.append("- %s: %s (%d %s)" % (self._elementDisplayName(identifier), ", ".join(prettyFields),
                                               len(changed), self.tr("elements")))
        return lines

    def _confirmAccept(self, summaryLines):
        bodyLines = [self.tr("The following changes will be saved:"), ""]
        bodyLines.extend(summaryLines)
        bodyLines.append("")
        bodyLines.append(self.tr("Continue?"))
        reply = QMessageBox.question(
            self,
            self.tr("Edit properties by group"),
            "\n".join(bodyLines),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _rollbackEdits(self):
        for layer in self.editedLayers:
            if layer.isEditable():
                layer.rollBack()
                layer.triggerRepaint()
        self.editedLayers = []

    """Helpers"""

    def _closeAttributeTables(self):
        for widget in self._attributeTableWidgets():
            layer = self._attributeTableLayer(widget)
            if layer is not None:
                layer.removeSelection()
            self._closeAttributeTable(widget)
        self.openedAttributeTables = {}

    def _attributeTableWidgets(self):
        widgets = list(QApplication.topLevelWidgets())
        if self.iface is not None:
            widgets += self.iface.mainWindow().findChildren(QDialog)
        tables = []
        for widget in widgets:
            with suppress(RuntimeError):
                if widget.metaObject().className() == "QgsAttributeTableDialog":
                    tables.append(widget)
        return tables

    def _existingAttributeTables(self, layer):
        # QGIS names every attribute table "QgsAttributeTableDialog/<layerId>", so this also
        # finds tables the user opened from the layers panel.
        objectName = "QgsAttributeTableDialog/%s" % layer.id()
        return [widget for widget in self._attributeTableWidgets() if widget.objectName() == objectName]

    def _attributeTableLayer(self, widget):
        prefix = "QgsAttributeTableDialog/"
        objectName = widget.objectName()
        if objectName.startswith(prefix):
            return QgsProject.instance().mapLayer(objectName[len(prefix):])
        return None

    def _closeAttributeTable(self, widget):
        with suppress(RuntimeError):
            dock = self._enclosingDock(widget)
            widget.close()
            if dock is not None:
                dock.close()

    def _currentLayer(self):
        identifier = self.cbElementType.currentData()
        if identifier is None:
            return None
        return self.layersByIdentifier.get(identifier)

    def _isFilterValueListActive(self):
        return self.filterValueStack.currentWidget() is self.cbFilterValueList

    def _currentFilterValueText(self):
        if self._isFilterValueListActive():
            data = self.cbFilterValueList.currentData()
            return str(data) if data is not None else self.cbFilterValueList.currentText()
        return self.leFilterValue.text()

    def _isIdentifierField(self, identifier, fieldName):
        return self.fieldUtils.getProperty(normalize_element(identifier), fieldName, translate=False) == "Identifier"

    def _isFreeTextField(self, identifier, fieldName):
        if identifier == "qgisred_demands" and fieldName == "Descrip":
            return False
        return fieldName in _freeTextFields or self._isIdentifierField(identifier, fieldName)

    def _formatDateDisplay(self, rawValue):
        text = "" if rawValue is None else str(rawValue).strip()
        if len(text) == 8 and text.isdigit():
            return "%s-%s-%s" % (text[0:4], text[4:6], text[6:8])
        return text

    def _parseDateInput(self, text):
        text = (text or "").strip()
        digits = text.replace("-", "")
        if len(digits) == 8 and digits.isdigit():
            return digits
        return text

    def _setCurrentFilterValueText(self, text):
        text = "" if text is None else str(text)
        if self._isFilterValueListActive():
            i = self.cbFilterValueList.findText(text)
            self.cbFilterValueList.setCurrentIndex(i if i >= 0 else 0)
        self.leFilterValue.setText(text)

    def _isNullValue(self, value):
        return value is None or (hasattr(value, "isNull") and value.isNull())

    def _getUniqueFieldValues(self, layer, fieldName):
        values = set()
        if layer.fields().indexFromName(fieldName) < 0:
            return []
        for f in layer.getFeatures():
            values.add(f[fieldName])
        return sorted(values)

    def _isTextValueListActive(self):
        return self.textValueStack.currentWidget() is self.cbTextValueList

    def _currentTextValue(self):
        if self._isTextValueListActive():
            return self.cbTextValueList.currentText()
        return self.leText.text()


class _GroupEditError(Exception):
    pass
