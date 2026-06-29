# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt, QTimer, QVariant
from qgis.PyQt.QtGui import QBrush, QColor, QDoubleValidator, QIcon
from qgis.PyQt.QtWidgets import QComboBox, QDialog, QMessageBox, QStackedWidget

from qgis.core import (
    QgsCoordinateTransform,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsFeatureRequest,
    QgsGeometry,
    QgsProject,
)
from qgis.gui import QgsHighlight

from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ...tools.utils.qgisred_ui_utils import QGISRedBanner, QGISRED_COMBO_STYLE
from ...tools.map_tools.qgisred_groupEditRegion import QGISRedGroupEditRegionTool


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_groupedit_dialog.ui"))


_elementLayerOrder = [
    "qgisred_junctions",
    "qgisred_pipes",
    "qgisred_tanks",
    "qgisred_reservoirs",
    "qgisred_pumps",
    "qgisred_valves",
    "qgisred_serviceconnections",
    "qgisred_isolationvalves",
]

_readonlyFields = {
    "qgisred_pipes": {"Length"},
}

_enumFields = {
    "qgisred_pipes":           {"IniStatus": ["OPEN", "CLOSED", "CV"]},
    "qgisred_pumps":           {"IniStatus": ["OPEN", "CLOSED"]},
    "qgisred_valves":          {"IniStatus": ["OPEN", "CLOSED"], "Type": ["PRV", "PSV", "PBV", "FCV", "TCV", "GPV"]},
    "qgisred_isolationvalves": {"IniStatus": ["OPEN", "CLOSED"]},
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

# Page indices in stackedValue (must match the .ui order).
_pageNumber = 0
_pageText = 1
_pageEnum = 2
_pageFindReplace = 3

# Property items matching these (case-insensitive) get the grey background used
# in Statistics / Queries by Properties for identifier-style fields.
_idTagFields = {"id", "tag", "descrip"}
_darkBrushColor = "#D8D8D8"

# Filter condition sets by field category, mirroring Queries by Properties.
_conditionsByType = {
    "numeric": ["All", ">=", "<=", "=", ">", "<", "≠"],
    "listed":  ["All", "="],
    "text":    ["All", "=", "≠", "ILIKE", "NOT ILIKE", "LIKE", "NOT LIKE"],
}

# Free-text fields keep a typed value (no unique-value combobox) and default to ILIKE.
_freeTextFields = {"Id", "Descrip", "InstalDate", "InstDate", "Time", "Time_H", "Time_Q", "Time_D"}

# Preferred property to preselect per element type, mirroring Queries by Properties.
# The first entry that exists as an editable field is selected.
_defaultProperties = {
    "qgisred_pipes":              ["Flow", "Diameter"],
    "qgisred_valves":             ["Flow", "Diameter"],
    "qgisred_pumps":              ["Flow", "IdHFCurve"],
    "qgisred_junctions":          ["Pressure", "BaseDem"],
    "qgisred_tanks":              ["Pressure", "Elevation"],
    "qgisred_reservoirs":         ["Pressure", "TotalHead"],
    "qgisred_serviceconnections": ["BaseDemand"],
    "qgisred_isolationvalves":    ["Status"],
}

# Light highlight with dark text so the hovered dropdown item stays readable on macOS.
_comboSelectionOverride = "QComboBox QAbstractItemView { selection-background-color: #DCE6F5; selection-color: #202020; }"


class QGISRedGroupEditDialog(QDialog, FORM_CLASS):
    """Bulk-edit dialog for QGISRed network elements (EPANET Group Edit-style)."""

    def __init__(self, parent=None):
        super(QGISRedGroupEditDialog, self).__init__(parent)
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/images/iconGroupEdit.svg"))
        self._applyStyle()
        self._setupFilterValueStack()

        self.iface = None
        self.canvas = None
        self.fieldUtils = QGISRedFieldUtils()
        self.layersByIdentifier = {}
        self.regionFids = []
        self.regionTool = None
        self._previousMapTool = None
        self.previewHighlights = []

        self.banner = QGISRedBanner.inject(self, self.rootLayout)

        self.cbScope.addItem(self.tr("Whole network"), "whole")
        self.cbScope.addItem(self.tr("Currently selected features"), "selected")
        self.cbScope.addItem(self.tr("Within polygon region..."), "region")

        self._countTimer = QTimer(self)
        self._countTimer.setSingleShot(True)
        self._countTimer.setInterval(150)
        self._countTimer.timeout.connect(self._refreshAffectedCount)

        self._connectSignals()

    """Public API"""

    def config(self, iface, projectDirectory, networkName):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName
        self.fieldUtils = QGISRedFieldUtils(projectDirectory, networkName, iface)
        self._populateElementTypes()

    def closeEvent(self, event):
        self._clearPreview()
        self._restoreMapTool()
        super(QGISRedGroupEditDialog, self).closeEvent(event)

    """Setup"""

    def _applyStyle(self):
        self.setStyleSheet(
            "QDialog { background-color: #f8f9fb; }"
            "QLineEdit, QSpinBox, QDoubleSpinBox { background-color: white; }"
        )
        for combo in self.findChildren(QComboBox):
            combo.setStyleSheet(QGISRED_COMBO_STYLE + _comboSelectionOverride)

    def _connectSignals(self):
        self.cbElementType.currentIndexChanged.connect(self._onElementTypeChanged)
        self.cbScope.currentIndexChanged.connect(self._onScopeChanged)
        self.btPickRegion.clicked.connect(self._onPickRegion)
        self.chkFilter.toggled.connect(self._onFilterToggled)
        self.cbFilterProperty.currentIndexChanged.connect(self._onFilterPropertyChanged)
        self.cbFilterOperator.currentIndexChanged.connect(self._onFilterConditionChanged)
        self.cbFilterOperator.currentIndexChanged.connect(self._updateFilterValues)
        self.leFilterValue.textChanged.connect(self._scheduleCount)
        self.cbFilterValueList.currentTextChanged.connect(self._scheduleCount)
        self.cbProperty.currentIndexChanged.connect(self._onPropertyChanged)
        self.cbAction.currentIndexChanged.connect(self._onActionChanged)
        self.btPreview.clicked.connect(self._onPreview)
        self.btApply.clicked.connect(self._onApply)
        self.btClose.clicked.connect(self.reject)

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
            self.btPreview.setEnabled(False)
            return

        self.cbElementType.setCurrentIndex(0)
        self._onElementTypeChanged()

    def _elementDisplayName(self, identifier):
        nameMap = {
            "qgisred_junctions":          self.tr("Junctions"),
            "qgisred_pipes":              self.tr("Pipes"),
            "qgisred_tanks":              self.tr("Tanks"),
            "qgisred_reservoirs":         self.tr("Reservoirs"),
            "qgisred_pumps":              self.tr("Pumps"),
            "qgisred_valves":             self.tr("Valves"),
            "qgisred_serviceconnections": self.tr("Service Connections"),
            "qgisred_isolationvalves":    self.tr("Isolation Valves"),
        }
        return nameMap.get(identifier, identifier)

    """Element type / property wiring"""

    def _onElementTypeChanged(self):
        self.regionFids = []
        layer = self._currentLayer()
        if layer is None:
            return
        self._populatePropertyCombos(layer)
        self._onPropertyChanged()
        self._onFilterPropertyChanged()
        self._scheduleCount()

    def _populatePropertyCombos(self, layer):
        identifier = layer.customProperty("qgisred_identifier")
        readonly = _readonlyFields.get(identifier, set())
        editable = []
        filterable = []
        for field in layer.fields():
            name = field.name()
            if name in readonly or name.lower() == "geometry":
                continue
            pretty = self.fieldUtils.getProperty(normalize_element(identifier), name)
            editable.append((name, pretty, field))
            filterable.append((name, pretty, field))

        self.cbProperty.blockSignals(True)
        self.cbProperty.clear()
        for name, pretty, field in editable:
            self.cbProperty.addItem(pretty, name)
        self._setPropertyItemBackgrounds(self.cbProperty)
        self._selectDefaultProperty(self.cbProperty, identifier)
        self.cbProperty.blockSignals(False)

        self.cbFilterProperty.blockSignals(True)
        self.cbFilterProperty.clear()
        for name, pretty, field in filterable:
            self.cbFilterProperty.addItem(pretty, name)
        self._setPropertyItemBackgrounds(self.cbFilterProperty)
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

    def _setPropertyItemBackgrounds(self, combo):
        for index in range(combo.count()):
            fieldName = combo.itemData(index)
            if fieldName and str(fieldName).lower() in _idTagFields:
                combo.setItemData(index, QBrush(QColor(_darkBrushColor)), Qt.ItemDataRole.BackgroundRole)

    def _updateComboBackground(self, combo):
        brush = combo.currentData(Qt.ItemDataRole.BackgroundRole)
        if brush and isinstance(brush, QBrush) and brush.color() != QColor(0, 0, 0, 255):
            color = brush.color().name()
        else:
            color = "white"
        combo.setStyleSheet(QGISRED_COMBO_STYLE + _comboSelectionOverride + "QComboBox { background-color: %s; }" % color)

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
        enumValues = _enumFields.get(identifier, {}).get(fieldName)

        self.cbAction.blockSignals(True)
        self.cbAction.clear()
        if enumValues is not None:
            for key, label, kind in _enumActions:
                self.cbAction.addItem(self.tr(label), (key, kind))
            self.cbEnum.clear()
            self.cbEnum.addItems(enumValues)
        elif field.isNumeric():
            for key, label, kind in _numericActions:
                self.cbAction.addItem(self.tr(label), (key, kind))
        else:
            for key, label, kind in _textActions:
                self.cbAction.addItem(self.tr(label), (key, kind))
        self.cbAction.blockSignals(False)
        self._updateUnitLabel(identifier, fieldName, field)
        self._onActionChanged()

    def _onActionChanged(self):
        data = self.cbAction.currentData()
        if not data:
            return
        _key, kind = data
        if kind == "numeric":
            self.stackedValue.setCurrentIndex(_pageNumber)
        elif kind == "text":
            self.stackedValue.setCurrentIndex(_pageText)
        elif kind == "enum":
            self.stackedValue.setCurrentIndex(_pageEnum)
        elif kind == "findReplace":
            self.stackedValue.setCurrentIndex(_pageFindReplace)
        self._scheduleCount()

    def _updateUnitLabel(self, identifier, fieldName, field):
        unit = ""
        if field.isNumeric():
            try:
                unit = self.fieldUtils.getUnitAbbreviation(normalize_element(identifier), fieldName) or ""
            except Exception:
                unit = ""
        self.lblUnit.setText(unit)
        decimals = 4
        try:
            decimals = max(2, self.fieldUtils.getDecimals(normalize_element(identifier), fieldName, default=4))
        except Exception:
            pass
        self.sbNumber.setDecimals(decimals)

    """Filter wiring"""

    def _setupFilterValueStack(self):
        idx = self.filterGrid.indexOf(self.leFilterValue)
        row, col, rowSpan, colSpan = self.filterGrid.getItemPosition(idx)
        sizePolicy = self.leFilterValue.sizePolicy()

        self.cbFilterValueList = QComboBox(self)
        self.cbFilterValueList.setEditable(False)
        self.cbFilterValueList.setSizePolicy(sizePolicy)
        self.cbFilterValueList.setStyleSheet(QGISRED_COMBO_STYLE + _comboSelectionOverride)

        self.filterValueStack = QStackedWidget(self)
        self.filterValueStack.setSizePolicy(sizePolicy)
        self.filterGrid.removeWidget(self.leFilterValue)
        self.filterValueStack.addWidget(self.leFilterValue)
        self.filterValueStack.addWidget(self.cbFilterValueList)
        self.filterGrid.addWidget(self.filterValueStack, row, col, rowSpan, colSpan)

    def _onFilterToggled(self, checked):
        self.cbFilterProperty.setEnabled(checked)
        self.cbFilterOperator.setEnabled(checked)
        self._onFilterConditionChanged()

    def _onFilterPropertyChanged(self):
        layer = self._currentLayer()
        if layer is None or self.cbFilterProperty.currentData() is None:
            return
        self._updateComboBackground(self.cbFilterProperty)
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
        elif category == "listed":
            defaultCondition = "="
        else:
            defaultCondition = "ILIKE" if fieldName in _freeTextFields else "="
        defaultIndex = self.cbFilterOperator.findText(defaultCondition)
        if defaultIndex >= 0:
            self.cbFilterOperator.setCurrentIndex(defaultIndex)
        self.cbFilterOperator.blockSignals(False)
        self._onFilterConditionChanged()
        self._updateFilterValues()

    def _onFilterConditionChanged(self):
        isAll = self.cbFilterOperator.currentText() == "All"
        enabled = (not isAll) and self.chkFilter.isChecked()
        self.leFilterValue.setEnabled(enabled)
        self.cbFilterValueList.setEnabled(enabled)
        if isAll:
            self._setCurrentFilterValueText("")
        self._scheduleCount()

    def _updateFilterValues(self):
        fieldName = self.cbFilterProperty.currentData()
        condition = self.cbFilterOperator.currentText()
        layer = self._currentLayer()
        useList = False
        strValues = []
        if layer is not None and fieldName and condition in ("=", "≠"):
            field = layer.fields().field(fieldName)
            if not field.isNumeric() and fieldName not in _freeTextFields:
                uniqueValues = self._getUniqueFilterValues(layer, fieldName)
                strValues = sorted({str(v) for v in uniqueValues if v is not None and str(v).strip()})
                useList = bool(strValues)
        if useList:
            previous = self._currentFilterValueText()
            self.cbFilterValueList.blockSignals(True)
            self.cbFilterValueList.clear()
            self.cbFilterValueList.addItem("")
            self.cbFilterValueList.addItems(strValues)
            i = self.cbFilterValueList.findText(previous)
            self.cbFilterValueList.setCurrentIndex(i if i >= 0 else 0)
            self.cbFilterValueList.blockSignals(False)
            self.filterValueStack.setCurrentWidget(self.cbFilterValueList)
        else:
            self.filterValueStack.setCurrentWidget(self.leFilterValue)

    """Scope / region picker"""

    def _onScopeChanged(self):
        scope = self.cbScope.currentData()
        self.btPickRegion.setEnabled(scope == "region")
        if scope != "region":
            self.regionFids = []
        self._scheduleCount()

    def _onPickRegion(self):
        if self.canvas is None:
            return
        self._previousMapTool = self.canvas.mapTool()
        self.regionTool = QGISRedGroupEditRegionTool(self.canvas)
        self.regionTool.regionPicked.connect(self._onRegionPicked)
        self.regionTool.regionCancelled.connect(self._onRegionCancelled)
        self.canvas.setMapTool(self.regionTool)
        self.hide()

    def _onRegionPicked(self, polygonGeom):
        layer = self._currentLayer()
        self.regionFids = []
        if layer is not None and polygonGeom is not None:
            try:
                self.regionFids = self._featuresInPolygon(layer, polygonGeom)
            except Exception as e:
                self.banner.pushMessage(self.tr("Region"),
                                        self.tr("Failed to compute region: %s") % str(e),
                                        level=2, duration=6)
        self._restoreMapTool()
        self.show()
        self.raise_()
        self.activateWindow()
        self._scheduleCount()

    def _onRegionCancelled(self):
        self._restoreMapTool()
        self.show()
        self.raise_()
        self.activateWindow()

    def _restoreMapTool(self):
        if self.canvas is None:
            return
        try:
            if self._previousMapTool is not None:
                self.canvas.setMapTool(self._previousMapTool)
            else:
                current = self.canvas.mapTool()
                if isinstance(current, QGISRedGroupEditRegionTool):
                    self.canvas.unsetMapTool(current)
        except Exception:
            pass
        self._previousMapTool = None
        self.regionTool = None

    def _featuresInPolygon(self, layer, polygonGeom):
        canvasCrs = self.canvas.mapSettings().destinationCrs()
        layerCrs = layer.crs()
        geom = QgsGeometry(polygonGeom)
        if canvasCrs.isValid() and layerCrs.isValid() and canvasCrs != layerCrs:
            transform = QgsCoordinateTransform(canvasCrs, layerCrs, QgsProject.instance())
            geom.transform(transform)
        bbox = geom.boundingBox()
        request = QgsFeatureRequest().setFilterRect(bbox)
        fids = []
        for f in layer.getFeatures(request):
            fg = f.geometry()
            if fg is not None and not fg.isEmpty() and geom.intersects(fg):
                fids.append(f.id())
        return fids

    """Affected count and matching"""

    def _scheduleCount(self):
        self._countTimer.start()

    def _refreshAffectedCount(self):
        layer = self._currentLayer()
        if layer is None:
            self.lblAffectedCount.setText(self.tr("0 elements match"))
            return
        try:
            features = self._matchingFeatures(layer)
        except Exception:
            features = []
        self.lblAffectedCount.setText(self.tr("%d elements match") % len(features))

    def _candidateFids(self, layer):
        scope = self.cbScope.currentData()
        if scope == "selected":
            return list(layer.selectedFeatureIds())
        if scope == "region":
            return list(self.regionFids)
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

        if not self.chkFilter.isChecked():
            return features

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

    def _onPreview(self):
        self._clearPreview()
        layer = self._currentLayer()
        if layer is None:
            return
        try:
            features = self._matchingFeatures(layer)
        except Exception as e:
            self.banner.pushMessage(self.tr("Preview"), str(e), level=2, duration=5)
            return
        if not features:
            self.banner.pushMessage(self.tr("Preview"),
                                    self.tr("No elements match the current target and filter."),
                                    level=1, duration=4)
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
        self.banner.pushMessage(self.tr("Preview"),
                                self.tr("Highlighted %d elements on the map.") % len(features),
                                level=0, duration=4)

    def _clearPreview(self):
        for highlight in self.previewHighlights:
            try:
                self.canvas.scene().removeItem(highlight)
            except Exception:
                pass
        self.previewHighlights = []

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

        identifier = layer.customProperty("qgisred_identifier")
        if not self._confirmApply(identifier, fieldName, actionKind, edits, layer):
            return

        self._commitEdits(layer, fieldName, edits)

    def _computeEdits(self, features, fieldName, actionKey, actionKind, layer):
        field = layer.fields().field(fieldName)
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
            text = self.leText.text()
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

    def _confirmApply(self, identifier, fieldName, actionKind, edits, layer):
        prettyField = self.fieldUtils.getProperty(normalize_element(identifier), fieldName)
        elementName = self._elementDisplayName(identifier)
        count = len(edits)

        rangeLine = ""
        warningLine = ""
        if actionKind == "numeric":
            oldValues = [e[1] for e in edits if self._coerceFloat(e[1]) is not None]
            newValues = [e[2] for e in edits if isinstance(e[2], (int, float))]
            if oldValues and newValues:
                oldFloats = [self._coerceFloat(v) for v in oldValues]
                rangeLine = self.tr("Current range: %.4g → %.4g") % (min(oldFloats), max(oldFloats))
                rangeLine += "\n" + self.tr("New range:     %.4g → %.4g") % (min(newValues), max(newValues))
            bounds = _softBounds.get((identifier, fieldName))
            if bounds is not None:
                lo, hi = bounds
                outOfRange = 0
                for v in newValues:
                    if (lo is not None and v < lo) or (hi is not None and v > hi):
                        outOfRange += 1
                if outOfRange:
                    warningLine = self.tr("Warning: %d value(s) fall outside the typical range for this field.") % outOfRange

        bodyLines = [
            self.tr("Will modify %s for %d %s.") % (prettyField, count, elementName),
        ]
        if rangeLine:
            bodyLines.append("")
            bodyLines.append(rangeLine)
        if warningLine:
            bodyLines.append("")
            bodyLines.append(warningLine)
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

    def _commitEdits(self, layer, fieldName, edits):
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("Field not found in layer."),
                                    level=2, duration=6)
            return
        if not layer.startEditing():
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("Could not start editing the layer."),
                                    level=2, duration=6)
            return
        layer.beginEditCommand("Group Edit")
        try:
            for fid, _oldVal, newVal in edits:
                layer.changeAttributeValue(fid, fieldIdx, newVal)
        except Exception as e:
            layer.destroyEditCommand()
            layer.rollBack()
            self.banner.pushMessage(self.tr("Apply"), str(e), level=2, duration=6)
            return
        layer.endEditCommand()
        if not layer.commitChanges():
            self.banner.pushMessage(self.tr("Apply"),
                                    self.tr("Failed to commit changes: %s") % "; ".join(layer.commitErrors()),
                                    level=2, duration=8)
            return
        layer.triggerRepaint()
        self._clearPreview()
        self.banner.pushMessage(self.tr("Apply"),
                                self.tr("Updated %d elements.") % len(edits),
                                level=0, duration=5)
        self._refreshAffectedCount()

    """Helpers"""

    def _currentLayer(self):
        identifier = self.cbElementType.currentData()
        if identifier is None:
            return None
        return self.layersByIdentifier.get(identifier)

    def _isFilterValueListActive(self):
        return self.filterValueStack.currentWidget() is self.cbFilterValueList

    def _currentFilterValueText(self):
        if self._isFilterValueListActive():
            return self.cbFilterValueList.currentText()
        return self.leFilterValue.text()

    def _setCurrentFilterValueText(self, text):
        text = "" if text is None else str(text)
        if self._isFilterValueListActive():
            i = self.cbFilterValueList.findText(text)
            self.cbFilterValueList.setCurrentIndex(i if i >= 0 else 0)
        self.leFilterValue.setText(text)

    def _getUniqueFilterValues(self, layer, fieldName):
        values = set()
        if layer.fields().indexFromName(fieldName) < 0:
            return []
        for f in layer.getFeatures():
            values.add(f[fieldName])
        return sorted(values)


class _GroupEditError(Exception):
    pass
