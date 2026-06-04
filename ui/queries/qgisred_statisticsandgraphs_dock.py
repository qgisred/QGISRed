# -*- coding: utf-8 -*-
import csv
import json
import math
import os
from datetime import datetime

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QBrush, QColor, QIcon
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)
from qgis.PyQt import uic
from qgis.core import (
    QgsClassificationJenks,
    QgsClassificationPrettyBreaks,
    QgsClassificationQuantile,
    QgsExpression,
    QgsFeatureRequest,
    QgsProject,
)

from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils
from .qgisred_statistics_manual_breaks_dialog import QGISRedStatisticsManualBreaksDialog
from .statistics_histogram_widget import StatisticsHistogramWidget

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statisticsandgraphs_dock.ui"))


RESULTS_BRUSH_COLOR = "#FFF8DC"
DARK_BRUSH_COLOR = "#D8D8D8"
ENUM_TEXT_LIMIT = 128
DEFAULT_NUM_CLASSES = 5
CATEGORICAL_FIELD_NAMES = {"Material", "Type", "Status", "InstalDate", "Tag"}

WHITE_STYLE = (
    "QComboBox { background-color: white; }"
    "QComboBox QAbstractItemView { background-color: white; selection-background-color: #3399ff; selection-color: white; }"
    "QLineEdit { background-color: white; }"
    "QSpinBox, QDoubleSpinBox { background-color: white; }"
)

FIELD_TYPE_MAPPING = {
    "int": "numeric",
    "integer": "numeric",
    "integer64": "numeric",
    "double": "numeric",
    "real": "numeric",
    "long": "numeric",
    "string": "text",
    "date": "numeric",
    "datetime": "numeric",
    "time": "numeric",
    "bool": "listed",
    "boolean": "listed",
}

CONDITIONS_BY_TYPE = {
    "numeric": ["All", ">=", "<=", "=", ">", "<", "≠", "Range"],
    "listed": ["All", "="],
    "text": ["All", "=", "≠", "ILIKE", "NOT ILIKE", "LIKE", "NOT LIKE"],
}

NODE_RESULT_PROPERTIES = ["Pressure", "Head", "Demand", "Quality"]
LINK_RESULT_PROPERTIES = ["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"]

ELEMENT_RESULT_CATEGORY = {
    "qgisred_junctions": "Node",
    "qgisred_reservoirs": "Node",
    "qgisred_tanks": "Node",
    "qgisred_demands": "Node",
    "qgisred_sources": "Node",
    "qgisred_pipes": "Link",
    "qgisred_pumps": "Link",
    "qgisred_valves": "Link",
}

DIGITAL_TWIN_IDENTIFIERS = {"qgisred_serviceconnections", "qgisred_isolationvalves", "qgisred_meters"}

INPUT_ORDER = [
    "qgisred_junctions",
    "qgisred_tanks",
    "qgisred_reservoirs",
    "qgisred_pipes",
    "qgisred_valves",
    "qgisred_pumps",
    "qgisred_demands",
    "qgisred_sources",
]

DIGITAL_TWIN_ORDER = ["qgisred_serviceconnections", "qgisred_isolationvalves", "qgisred_meters"]

ALL_IDENTIFIERS = set(INPUT_ORDER) | set(DIGITAL_TWIN_ORDER)

CUMULATIVE_PROPERTIES = {"Length", "MinVolume", "BaseDem", "BaseDemand", "BaseValue", "Power"}


class QGISRedStatisticsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        try:
            self.mGroupBox.setSaveCollapsedState(False)
        except Exception:
            pass
        self.mGroupBox.setCollapsed(True)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.fieldUtils = QGISRedFieldUtils()
        self.suspendCascade = False
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0
        self.manualBreaks = []
        self.isEnumeratedTarget = False
        self.connectedLayerNodes = []
        self.connectedGroups = []
        self.layerTreeChangeTimer = QTimer()
        self.layerTreeChangeTimer.setSingleShot(True)
        self.layerTreeChangeTimer.setInterval(100)
        self.layerTreeChangeTimer.timeout.connect(self.doLayerTreeChanged)

        self.setupHistogram()
        self.setupIcons()
        self.applyWhiteStyle()
        self.setupConnections()
        self.initializeElementTypes()
        self.loadDefaults()
        self.setupProjectSignals()
        QGISRedUIUtils.applyDockStyle(self, "#388E3C")

        from qgis.PyQt.QtWidgets import QComboBox
        for combo in self.findChildren(QComboBox):
            QGISRedUIUtils.applyComboStyle(combo)

    def closeEvent(self, event):
        project = QgsProject.instance()
        self.safeDisconnect(project.layersAdded, self.onLayerTreeChanged)
        self.safeDisconnect(project.layersRemoved, self.onLayerTreeChanged)
        self.safeDisconnect(project.readProject, self.onProjectChanged)
        self.safeDisconnect(project.cleared, self.onProjectChanged)
        for layerNode in self.connectedLayerNodes:
            self.disconnectLayerNode(layerNode)
        self.connectedLayerNodes.clear()
        for group in self.connectedGroups:
            self.disconnectGroupSignals(group)
        self.connectedGroups.clear()
        self.layerTreeChangeTimer.stop()
        self.deleteLater()
        super().closeEvent(event)

    def safeDisconnect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def setupHistogram(self):
        self.histogram = StatisticsHistogramWidget(self.graphWidget)
        self.histogram.setToolTip(self.tr("Mouse wheel: zoom · Drag: pan · Double-click: reset view"))
        layout = QVBoxLayout(self.graphWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.histogram)
        self.graphWidget.setLayout(layout)
        self.labelOnlySelectedElements.hide()

    def setupIcons(self):
        self.btImport.setIcon(QIcon(":/images/iconStatisticsImport.svg"))
        self.btImport.setToolTip(self.tr("Import query configuration (.json)"))
        self.btExport.setIcon(QIcon(":/images/iconStatisticsExport.svg"))
        self.btExport.setToolTip(self.tr("Export query configuration (.json)"))
        self.btExcel.setIcon(QIcon(":/images/iconStatisticsExcel.svg"))
        self.btExcel.setToolTip(self.tr("Export table to CSV"))

    def applyWhiteStyle(self):
        for widget in (
            self.cbElementType, self.cbProperty, self.cbClassifiedBy, self.cbRanged,
            self.cbAttribute, self.cbCondition, self.cbValue, self.leFrom, self.leTo,
            self.cbClasses, self.spinIntervalRange,
        ):
            widget.setStyleSheet(WHITE_STYLE)

    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.onElementTypeChanged)
        self.cbElementType.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbElementType))
        self.cbProperty.currentIndexChanged.connect(self.onPropertyChanged)
        self.cbProperty.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbProperty))
        self.cbClassifiedBy.currentIndexChanged.connect(self.onClassifyByChanged)
        self.cbClassifiedBy.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbClassifiedBy))
        self.cbRanged.currentIndexChanged.connect(self.onRangedChanged)
        self.cbAttribute.currentIndexChanged.connect(self.onAttributeChanged)
        self.cbCondition.currentIndexChanged.connect(self.onConditionChanged)
        self.btAnalyze.clicked.connect(self.analyze)
        self.btImport.clicked.connect(self.importConfig)
        self.btExport.clicked.connect(self.exportConfig)
        self.btExcel.clicked.connect(self.exportTableCsv)
        self.btManualBreaks.clicked.connect(self.openManualBreaksDialog)

    def setupProjectSignals(self):
        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)
        self.reconnectLayerSignals()

    def reconnectLayerSignals(self):
        for layerNode in self.connectedLayerNodes:
            self.disconnectLayerNode(layerNode)
        self.connectedLayerNodes.clear()
        for group in self.connectedGroups:
            self.disconnectGroupSignals(group)
        self.connectedGroups.clear()
        for identifier in ("qgisred_inputs", "qgisred_results"):
            group = QGISRedLayerUtils.findGroupByIdentifier(identifier)
            if group:
                self.connectGroupSignals(group)
                for layerNode in group.findLayers():
                    self.connectLayerSignals(layerNode)

    def connectGroupSignals(self, group):
        try:
            group.addedChildren.connect(self.onLayerTreeChanged)
            group.removedChildren.connect(self.onLayerTreeChanged)
            self.connectedGroups.append(group)
        except Exception:
            pass

    def disconnectGroupSignals(self, group):
        try:
            self.safeDisconnect(group.addedChildren, self.onLayerTreeChanged)
            self.safeDisconnect(group.removedChildren, self.onLayerTreeChanged)
        except Exception:
            pass

    def connectLayerSignals(self, layerNode):
        try:
            layerNode.nameChanged.connect(self.onLayerTreeChanged)
            layer = layerNode.layer()
            if layer is not None:
                layer.dataChanged.connect(self.onLayerTreeChanged)
                layer.featureAdded.connect(self.onLayerTreeChanged)
                layer.featureDeleted.connect(self.onLayerTreeChanged)
                layer.attributeValueChanged.connect(self.onLayerTreeChanged)
                layer.committedAttributeValuesChanges.connect(self.onLayerTreeChanged)
            self.connectedLayerNodes.append(layerNode)
        except Exception:
            pass

    def disconnectLayerNode(self, layerNode):
        try:
            self.safeDisconnect(layerNode.nameChanged, self.onLayerTreeChanged)
            layer = layerNode.layer()
            if layer is not None:
                self.safeDisconnect(layer.dataChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureAdded, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureDeleted, self.onLayerTreeChanged)
                self.safeDisconnect(layer.attributeValueChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.committedAttributeValuesChanges, self.onLayerTreeChanged)
        except Exception:
            pass

    def onLayerTreeChanged(self, *args):
        self.layerTreeChangeTimer.start()

    def doLayerTreeChanged(self):
        state = self.saveCurrentQueryState()
        self.reconnectLayerSignals()
        combos = (
            self.cbElementType, self.cbProperty, self.cbClassifiedBy, self.cbRanged,
            self.cbAttribute, self.cbCondition, self.cbValue,
        )
        for combo in combos:
            combo.blockSignals(True)
        try:
            self.initializeElementTypes()
            self.restoreCurrentQueryState(state)
        finally:
            for combo in combos:
                combo.blockSignals(False)
        self.histogram.clear()
        self.tbExcel.setRowCount(0)
        self.tbExcel.setColumnCount(0)
        self.labelOnlySelectedElements.hide()

    def onProjectChanged(self, *args):
        self.manualBreaks = []
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0
        self.histogram.clear()
        self.tbExcel.setRowCount(0)
        self.tbExcel.setColumnCount(0)
        self.labelOnlySelectedElements.hide()
        self.onLayerTreeChanged()

    def saveCurrentQueryState(self):
        return {
            "elementType": self.cbElementType.currentData(Qt.ItemDataRole.UserRole),
            "property": self.cbProperty.currentData(Qt.ItemDataRole.UserRole),
            "classifyBy": self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole),
            "ranged": self.cbRanged.currentData(Qt.ItemDataRole.UserRole),
            "classes": self.cbClasses.value(),
            "interval": self.spinIntervalRange.value(),
            "attribute": self.cbAttribute.currentData(Qt.ItemDataRole.UserRole),
            "condition": self.cbCondition.currentData(Qt.ItemDataRole.UserRole),
            "valueText": self.cbValue.currentText(),
            "from": self.leFrom.text(),
            "to": self.leTo.text(),
            "onlySelected": self.cbSelectedElements.isChecked(),
            "manualBreaks": list(self.manualBreaks),
        }

    def restoreCurrentQueryState(self, state):
        self.suspendCascade = True
        elementIndex = self.cbElementType.findData(state.get("elementType")) if state.get("elementType") else -1
        if elementIndex >= 0:
            self.cbElementType.setCurrentIndex(elementIndex)
        self.suspendCascade = False
        self.updateProperties()
        self.updateClassifyBy()
        self.updateAttributes()

        propertyIndex = self.cbProperty.findData(state.get("property")) if state.get("property") else -1
        if propertyIndex >= 0:
            self.cbProperty.setCurrentIndex(propertyIndex)
        classifyIndex = self.cbClassifiedBy.findData(state.get("classifyBy")) if state.get("classifyBy") else -1
        if classifyIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(classifyIndex)
            self.updateRanged()
        rangedIndex = self.cbRanged.findData(state.get("ranged")) if state.get("ranged") else -1
        if rangedIndex >= 0:
            self.cbRanged.setCurrentIndex(rangedIndex)
        classes = state.get("classes")
        if classes:
            self.cbClasses.setValue(int(classes))
        interval = state.get("interval")
        if interval is not None:
            try:
                self.spinIntervalRange.setValue(float(interval))
            except (TypeError, ValueError):
                pass
        attributeIndex = self.cbAttribute.findData(state.get("attribute") or "")
        if attributeIndex >= 0:
            self.cbAttribute.setCurrentIndex(attributeIndex)
        self.updateConditions()
        conditionIndex = self.cbCondition.findData(state.get("condition")) if state.get("condition") else -1
        if conditionIndex >= 0:
            self.cbCondition.setCurrentIndex(conditionIndex)
        self.updateValueWidget()
        valueText = state.get("valueText")
        if valueText:
            valueIndex = self.cbValue.findText(valueText)
            if valueIndex >= 0:
                self.cbValue.setCurrentIndex(valueIndex)
            else:
                self.cbValue.setEditText(valueText)
        self.leFrom.setText(state.get("from") or "")
        self.leTo.setText(state.get("to") or "")
        self.cbSelectedElements.setChecked(bool(state.get("onlySelected")))
        self.manualBreaks = list(state.get("manualBreaks") or [])
        for combo in (self.cbElementType, self.cbProperty, self.cbClassifiedBy, self.cbRanged,
                      self.cbAttribute, self.cbCondition):
            self.updateComboBoxBackground(combo)
        self.onRangedChanged()

    def updateComboBoxBackground(self, combo):
        brush = combo.currentData(Qt.ItemDataRole.BackgroundRole)
        if brush and isinstance(brush, QBrush) and brush.color() != QColor(0, 0, 0, 255):
            color = brush.color().name()
        else:
            color = "white"
        combo.setStyleSheet(
            f"QComboBox {{ background-color: {color}; }}"
            "QComboBox QAbstractItemView { background-color: white; selection-background-color: #3399ff; selection-color: white; }"
            "QLineEdit { background-color: white; }"
        )

    def initializeElementTypes(self):
        self.suspendCascade = True
        self.cbElementType.clear()

        availableLayers = {}
        inputsGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_inputs")
        if inputsGroup:
            for layerNode in inputsGroup.findLayers():
                layer = layerNode.layer()
                if layer and layer.customProperty("qgisred_identifier") in ALL_IDENTIFIERS:
                    availableLayers[layer.customProperty("qgisred_identifier")] = layer.name()

        nodeIdent = linkIdent = None
        resultsGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_results")
        if resultsGroup:
            for layerNode in resultsGroup.findLayers():
                layer = layerNode.layer()
                if not layer:
                    continue
                ident = layer.customProperty("qgisred_identifier") or ""
                if ident.startswith("qgisred_node") and nodeIdent is None:
                    nodeIdent = ident
                elif ident.startswith("qgisred_link") and linkIdent is None:
                    linkIdent = ident

        hasResults = nodeIdent or linkIdent
        if hasResults:
            resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
            if nodeIdent:
                self.cbElementType.addItem(self.tr("Nodes"), nodeIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            if linkIdent:
                self.cbElementType.addItem(self.tr("Links"), linkIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            self.cbElementType.insertSeparator(self.cbElementType.count())

        addedInput = False
        for ident in INPUT_ORDER:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)
                addedInput = True

        hasTwin = any(ident in availableLayers for ident in DIGITAL_TWIN_ORDER)
        if addedInput and hasTwin:
            self.cbElementType.insertSeparator(self.cbElementType.count())
        for ident in DIGITAL_TWIN_ORDER:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)
        self.suspendCascade = False

    def loadDefaults(self):
        defaultIndex = self.cbElementType.findData("qgisred_pipes")
        if defaultIndex >= 0:
            self.cbElementType.setCurrentIndex(defaultIndex)
        self.onElementTypeChanged()

    def isResultsLayer(self, layer):
        if not layer:
            return False
        ident = layer.customProperty("qgisred_identifier") or ""
        return ident.startswith("qgisred_node") or ident.startswith("qgisred_link")

    def isResultsIdentifier(self, ident):
        return bool(ident) and (ident.startswith("qgisred_node") or ident.startswith("qgisred_link"))

    def getResultsExist(self):
        resultsGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_results")
        if not resultsGroup:
            return False
        for layerNode in resultsGroup.findLayers():
            if layerNode.layer():
                return True
        return False

    def resolveLayer(self):
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        if not elementIdentifier:
            return None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.customProperty("qgisred_identifier") == elementIdentifier:
                return layer
        return None

    def resolveResultsLayer(self, category):
        prefix = "qgisred_node" if category == "Node" else "qgisred_link"
        resultsGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_results")
        if not resultsGroup:
            return None
        for layerNode in resultsGroup.findLayers():
            layer = layerNode.layer()
            if not layer:
                continue
            ident = layer.customProperty("qgisred_identifier") or ""
            if ident.startswith(prefix):
                return layer
        return None

    def onElementTypeChanged(self):
        if self.suspendCascade:
            return
        self.manualBreaks = []
        self.histogram.clear()
        self.tbExcel.setRowCount(0)
        self.tbExcel.setColumnCount(0)
        self.labelOnlySelectedElements.hide()
        self.updateProperties()
        self.updateClassifyBy()
        self.updateAttributes()

    def onPropertyChanged(self):
        if self.suspendCascade:
            return

    def onClassifyByChanged(self):
        if self.suspendCascade:
            return
        self.manualBreaks = []
        self.updateRanged()

    def onRangedChanged(self):
        if self.suspendCascade:
            return
        rangedId = self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or ""
        isFixedInterval = rangedId == "FixedInterval"
        isManual = rangedId == "Manual"
        isCategories = rangedId == "Categorized"
        self.cbClasses.setVisible(not isFixedInterval)
        self.labelClasses.setVisible(not isFixedInterval)
        self.spinIntervalRange.setVisible(isFixedInterval)
        self.labelIntervalRange.setVisible(isFixedInterval)
        self.btManualBreaks.setVisible(isManual)
        self.cbClasses.setEnabled(not isCategories)
        if isCategories:
            classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
            layer = self.resolveLayerForClassifyField(classifyField)
            if layer is not None and classifyField:
                distinctCount = len(self.collectUniqueValues(layer, classifyField, limit=10000))
                if distinctCount > 0:
                    self.cbClasses.blockSignals(True)
                    self.cbClasses.setMinimum(1)
                    self.cbClasses.setMaximum(max(distinctCount, 1))
                    self.cbClasses.setValue(distinctCount)
                    self.cbClasses.blockSignals(False)
        else:
            self.cbClasses.setMinimum(2)
            self.cbClasses.setMaximum(50)

    def onAttributeChanged(self):
        if self.suspendCascade:
            return
        self.updateConditions()

    def onConditionChanged(self):
        if self.suspendCascade:
            return
        self.updateValueWidget()

    def updateProperties(self):
        self.suspendCascade = True
        self.cbProperty.clear()
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbProperty)
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        skipLower = {"id", "descrip", "description"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        tagField = None
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if lower in skipLower:
                continue
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            cat = FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
            isEnum = fieldName in CATEGORICAL_FIELD_NAMES
            if not (cat == "numeric" or isEnum):
                continue
            if lower == "tag":
                tagField = field
            else:
                staticFields.append(field)

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop not in ("Quality", "ReactRate")]

        if not isResultsMode:
            for field in staticFields:
                self.addPropertyItem(self.cbProperty, elementIdentifier, field.name())
            if tagField is not None:
                self.addPropertyItem(self.cbProperty, elementIdentifier, tagField.name(), darkBrush)
            if resultProps:
                if self.cbProperty.count() > 0:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
                resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
                for prop in resultProps:
                    self.addResultPropertyItem(self.cbProperty, resultCategory, prop, resultsBrush)
        else:
            if tagField is not None:
                self.addPropertyItem(self.cbProperty, elementIdentifier, tagField.name(), darkBrush)
                if resultProps or staticFields:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
            for field in staticFields:
                self.addPropertyItem(self.cbProperty, elementIdentifier, field.name())
            if resultProps:
                if self.cbProperty.count() > 0:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
                resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
                for prop in resultProps:
                    self.addResultPropertyItem(self.cbProperty, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        self.selectFirstUsable(self.cbProperty)
        self.updateComboBoxBackground(self.cbProperty)

    def updateClassifyBy(self):
        self.suspendCascade = True
        self.cbClassifiedBy.clear()
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbClassifiedBy)
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        skipLower = {"id", "descrip", "description"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        tagField = None
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if lower in skipLower:
                continue
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            cat = FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
            isEnum = fieldName in CATEGORICAL_FIELD_NAMES
            if not (cat == "numeric" or isEnum):
                continue
            if lower == "tag":
                tagField = field
            else:
                staticFields.append(field)

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop not in ("Quality", "ReactRate")]

        for field in staticFields:
            self.addPropertyItem(self.cbClassifiedBy, elementIdentifier, field.name())
        if tagField is not None:
            self.addPropertyItem(self.cbClassifiedBy, elementIdentifier, tagField.name(), darkBrush)
        if resultProps:
            if self.cbClassifiedBy.count() > 0:
                self.cbClassifiedBy.insertSeparator(self.cbClassifiedBy.count())
            resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
            for prop in resultProps:
                self.addResultPropertyItem(self.cbClassifiedBy, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        defaultIndex = self.cbClassifiedBy.findData("Diameter")
        if defaultIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(defaultIndex)
        else:
            self.selectFirstUsable(self.cbClassifiedBy)
        self.updateComboBoxBackground(self.cbClassifiedBy)
        self.updateRanged()

    def updateRanged(self):
        self.suspendCascade = True
        self.cbRanged.clear()
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not classifyField:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbRanged)
            return
        if self.isCategoricalClassifier(classifyField):
            self.cbRanged.addItem(self.tr("Categories"), "Categorized")
        else:
            for identifier, label in (
                ("Categorized", self.tr("Categories")),
                ("EqualInterval", self.tr("Equal Interval")),
                ("FixedInterval", self.tr("Fixed Interval")),
                ("Quantile", self.tr("Equal Count")),
                ("Jenks", self.tr("Natural Breaks")),
                ("Pretty", self.tr("Pretty Breaks")),
                ("Manual", self.tr("Manual")),
            ):
                self.cbRanged.addItem(label, identifier)
            defaultIndex = self.cbRanged.findData("EqualInterval")
            if defaultIndex >= 0:
                self.cbRanged.setCurrentIndex(defaultIndex)
        self.cbClasses.blockSignals(True)
        self.cbClasses.setMinimum(2)
        self.cbClasses.setMaximum(50)
        if self.cbClasses.value() < 2:
            self.cbClasses.setValue(DEFAULT_NUM_CLASSES)
        self.cbClasses.blockSignals(False)
        self.suspendCascade = False
        self.onRangedChanged()

    def updateAttributes(self):
        self.suspendCascade = True
        self.cbAttribute.clear()
        self.cbAttribute.addItem(self.tr("(no filter)"), "")
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbAttribute)
            self.updateConditions()
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        idTagLower = {"id", "tag", "descrip"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        idTagFieldsByKey = {}
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            if lower in idTagLower:
                idTagFieldsByKey[lower] = field
            else:
                staticFields.append(field)

        for key in ("id", "tag", "descrip"):
            if key in idTagFieldsByKey:
                self.addPropertyItem(self.cbAttribute, elementIdentifier, idTagFieldsByKey[key].name(), darkBrush)
        if staticFields and idTagFieldsByKey:
            self.cbAttribute.insertSeparator(self.cbAttribute.count())
        for field in staticFields:
            self.addPropertyItem(self.cbAttribute, elementIdentifier, field.name())

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop not in ("Quality", "ReactRate")]
        if resultProps:
            self.cbAttribute.insertSeparator(self.cbAttribute.count())
            resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
            for prop in resultProps:
                self.addResultPropertyItem(self.cbAttribute, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        self.updateComboBoxBackground(self.cbAttribute)
        self.updateConditions()

    def updateConditions(self):
        self.suspendCascade = True
        self.cbCondition.clear()
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        hasAttribute = bool(attributeField)
        self.cbCondition.setVisible(hasAttribute)
        self.labelCondition.setVisible(hasAttribute)
        self.valueStack.setVisible(hasAttribute)
        self.labelValue.setVisible(hasAttribute)
        if not hasAttribute:
            self.suspendCascade = False
            return
        cat = self.classifyAttributeType(attributeField)
        for option in CONDITIONS_BY_TYPE.get(cat, CONDITIONS_BY_TYPE["text"]):
            self.cbCondition.addItem(option, option)
        if cat == "numeric":
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        elif cat == "listed":
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        else:
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        self.suspendCascade = False
        self.updateValueWidget()

    def updateValueWidget(self):
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if not attributeField:
            return
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        if condition == "All":
            self.valueStack.setCurrentIndex(0)
            self.cbValue.clear()
            return
        if condition == "Range":
            self.valueStack.setCurrentIndex(1)
            return
        self.valueStack.setCurrentIndex(0)
        layer = self.resolveAttributeLayer(attributeField)
        self.cbValue.clear()
        if layer is None:
            return
        cat = self.classifyAttributeType(attributeField)
        if condition in ("=", "≠") and cat in ("listed", "text"):
            uniqueValues = self.collectUniqueValues(layer, attributeField, limit=500)
            self.cbValue.addItem("", "")
            for value in uniqueValues:
                self.cbValue.addItem(str(value), value)
        elif cat == "listed":
            uniqueValues = self.collectUniqueValues(layer, attributeField, limit=500)
            self.cbValue.addItem("", "")
            for value in uniqueValues:
                self.cbValue.addItem(str(value), value)

    def addPropertyItem(self, combo, elementIdentifier, fieldName, brush=None):
        prettyName = self.fieldUtils.getProperty(normalize_element(elementIdentifier), fieldName) or fieldName
        unit = self.fieldUtils.getUnitAbbreviation(normalize_element(elementIdentifier), fieldName) or ""
        label = "{} ({})".format(prettyName, unit) if unit else prettyName
        combo.addItem(label, fieldName)
        idx = combo.count() - 1
        if brush:
            combo.setItemData(idx, brush, Qt.ItemDataRole.BackgroundRole)

    def addResultPropertyItem(self, combo, resultCategory, prop, brush):
        prettyName = self.fieldUtils.getProperty(normalize_element(resultCategory), prop) or prop
        unit = self.fieldUtils.getUnitAbbreviation(normalize_element(resultCategory), prop) if resultCategory else ""
        label = "{} ({})".format(prettyName, unit) if unit else prettyName
        combo.addItem(label, prop)
        idx = combo.count() - 1
        combo.setItemData(idx, brush, Qt.ItemDataRole.BackgroundRole)

    def selectFirstUsable(self, combo):
        for i in range(combo.count()):
            if combo.itemData(i, Qt.ItemDataRole.UserRole):
                combo.setCurrentIndex(i)
                return
        if combo.count() > 0:
            combo.setCurrentIndex(0)

    def getResultProperties(self, layer, elementIdentifier):
        if self.isResultsLayer(layer):
            ident = layer.customProperty("qgisred_identifier") or ""
            return list(LINK_RESULT_PROPERTIES) if ident.startswith("qgisred_link") else list(NODE_RESULT_PROPERTIES)
        if elementIdentifier in DIGITAL_TWIN_IDENTIFIERS or not self.getResultsExist():
            return []
        category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
        if category == "Link":
            return list(LINK_RESULT_PROPERTIES)
        if category == "Node":
            return list(NODE_RESULT_PROPERTIES)
        return []

    def resultCategoryFor(self, elementIdentifier, isResultsMode, layer):
        if isResultsMode:
            ident = layer.customProperty("qgisred_identifier") or ""
            return "Links" if ident.startswith("qgisred_link") else "Nodes"
        cat = ELEMENT_RESULT_CATEGORY.get(elementIdentifier, "")
        return "Links" if cat == "Link" else "Nodes"

    def classifyAttributeType(self, fieldName):
        if not fieldName:
            return "text"
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return "listed"
        layer = self.resolveAttributeLayer(fieldName)
        if layer is None:
            if self.isResultProperty(fieldName):
                return "numeric" if fieldName != "Status" else "listed"
            return "text"
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx >= 0:
            field = layer.fields().field(fieldIdx)
            return FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
        if self.isResultProperty(fieldName):
            return "numeric" if fieldName != "Status" else "listed"
        return "text"

    def isResultProperty(self, prop):
        return prop in NODE_RESULT_PROPERTIES or prop in LINK_RESULT_PROPERTIES

    def isCategoricalClassifier(self, fieldName):
        if not fieldName:
            return False
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return True
        layer = self.resolveLayerForClassifyField(fieldName)
        if layer is None:
            return False
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            return False
        cat = FIELD_TYPE_MAPPING.get(layer.fields().field(fieldIdx).typeName().lower(), "text")
        return cat == "text"

    def resolveLayerForClassifyField(self, fieldName):
        layer = self.resolveLayer()
        if layer is None or not fieldName:
            return layer
        if layer.fields().indexFromName(fieldName) >= 0:
            return layer
        if self.isResultProperty(fieldName):
            elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category:
                resultsLayer = self.resolveResultsLayer(category)
                if resultsLayer is not None:
                    return resultsLayer
        return layer

    def resolveAttributeLayer(self, fieldName):
        return self.resolveLayerForClassifyField(fieldName)

    def collectUniqueValues(self, layer, fieldName, limit=200):
        if layer.fields().indexFromName(fieldName) < 0:
            return []
        values = set()
        for feature in layer.getFeatures():
            value = feature[fieldName]
            if value is None:
                continue
            values.add(value)
            if len(values) >= limit:
                break
        try:
            return sorted(values)
        except TypeError:
            return sorted(values, key=lambda item: str(item))

    def collectNumericValues(self, layer, fieldName):
        values = []
        if layer.fields().indexFromName(fieldName) < 0:
            return values
        for feature in layer.getFeatures():
            raw = feature[fieldName]
            if raw is None:
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
        values.sort()
        return values

    def openManualBreaksDialog(self):
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not classifyField:
            return
        layer = self.resolveLayerForClassifyField(classifyField)
        if layer is None:
            return
        values = self.collectNumericValues(layer, classifyField)
        if not values:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("No numeric values available for the selected classification field."),
            )
            return
        dataMin = values[0]
        dataMax = values[-1]
        dialog = QGISRedStatisticsManualBreaksDialog(
            dataMin,
            dataMax,
            initialBreaks=self.manualBreaks or None,
            initialClassCount=self.cbClasses.value(),
            parent=self,
        )
        if dialog.exec():
            self.manualBreaks = dialog.getBreaks()
            self.cbClasses.blockSignals(True)
            self.cbClasses.setValue(dialog.getClassCount())
            self.cbClasses.blockSignals(False)

    def analyze(self):
        layer = self.resolveLayer()
        if layer is None:
            QMessageBox.warning(
                self,
                self.tr("No layer"),
                self.tr("The selected element type has no matching layer in the current project."),
            )
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        propertyField = self.cbProperty.currentData(Qt.ItemDataRole.UserRole)
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not propertyField or not classifyField:
            return

        propertyLayer = self.resolveLayerForClassifyField(propertyField)
        classifyLayer = self.resolveLayerForClassifyField(classifyField)
        if propertyLayer is None or classifyLayer is None:
            QMessageBox.warning(self, self.tr("No layer"), self.tr("Cannot resolve the data layer for the selected fields."))
            return
        if propertyLayer is not classifyLayer:
            QMessageBox.warning(
                self,
                self.tr("Layer mismatch"),
                self.tr("Property and classification fields must come from the same layer."),
            )
            return

        if propertyLayer.fields().indexFromName(propertyField) < 0:
            QMessageBox.warning(self, self.tr("Field missing"), self.tr("Property field '{0}' was not found on the layer.").format(propertyField))
            return
        if classifyLayer.fields().indexFromName(classifyField) < 0:
            QMessageBox.warning(self, self.tr("Field missing"), self.tr("Classification field '{0}' was not found on the layer.").format(classifyField))
            return

        featureRequest = self.buildFeatureRequest(propertyLayer)
        if featureRequest is False:
            return

        breaks = self.resolveBreaks(propertyLayer, classifyField)
        if breaks is None:
            return

        self.isEnumeratedTarget = not self.isNumericField(propertyLayer, propertyField)
        bins = self.initBins(breaks)
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0

        featureIterator = propertyLayer.getFeatures(featureRequest) if featureRequest is not None else propertyLayer.getFeatures()
        for feature in featureIterator:
            classValue = feature[classifyField]
            propertyValue = feature[propertyField]
            if classValue is None or propertyValue is None:
                self.lastNullCount += 1
                continue
            binIndex = self.findBinIndex(bins, classValue, breaks["type"])
            if binIndex is None:
                self.lastOutOfRangeCount += 1
                continue
            self.accumulateValue(bins[binIndex], propertyValue)

        self.finalizeBins(bins)

        prettyProperty = self.fieldUtils.getProperty(normalize_element(elementIdentifier), propertyField) or propertyField
        prettyClassify = self.fieldUtils.getProperty(normalize_element(elementIdentifier), classifyField) or classifyField
        propertyUnit = self.fieldUtils.getUnitAbbreviation(normalize_element(elementIdentifier), propertyField) or ""
        classifyUnit = self.fieldUtils.getUnitAbbreviation(normalize_element(elementIdentifier), classifyField) or ""

        title = "{} ({} {})".format(prettyProperty, self.tr("by"), prettyClassify)
        subtitle = self.buildSubtitle(elementIdentifier)
        xLabel = "{} ({})".format(prettyClassify, classifyUnit) if classifyUnit else prettyClassify
        if propertyUnit and not self.isEnumeratedTarget:
            yLabel = "{} ({})".format(prettyProperty, propertyUnit)
        else:
            yLabel = self.tr("Count")
        self.histogram.setTitles(title, subtitle)
        self.histogram.setBins(bins, mode="plain", xLabel=xLabel, yLabelLeft=yLabel)

        self.populateTable(bins, prettyClassify, prettyProperty, propertyUnit, elementIdentifier, propertyField)

    def isNumericField(self, layer, fieldName):
        if self.isResultProperty(fieldName):
            return fieldName != "Status"
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return False
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            return False
        cat = FIELD_TYPE_MAPPING.get(layer.fields().field(fieldIdx).typeName().lower(), "text")
        return cat == "numeric"

    def buildFeatureRequest(self, layer):
        request = QgsFeatureRequest()
        applied = False
        if self.cbSelectedElements.isChecked():
            selectedIds = layer.selectedFeatureIds()
            if not selectedIds:
                QMessageBox.information(
                    self,
                    self.tr("No selection"),
                    self.tr("'Only selected elements' is checked but no features are selected on the active layer."),
                )
                return False
            request.setFilterFids(list(selectedIds))
            applied = True
            self.labelOnlySelectedElements.show()
        else:
            self.labelOnlySelectedElements.hide()

        expression = self.buildAttributeExpression(layer)
        if expression is False:
            return False
        if expression:
            request.combineFilterExpression(expression)
            applied = True
        return request if applied else None

    def buildAttributeExpression(self, layer):
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if not attributeField:
            return ""
        if layer.fields().indexFromName(attributeField) < 0:
            return ""
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        if condition in ("", "All"):
            return ""
        quotedColumn = QgsExpression.quotedColumnRef(attributeField)
        if condition == "Range":
            fromText = self.leFrom.text().strip()
            toText = self.leTo.text().strip()
            if not fromText or not toText:
                QMessageBox.warning(self, self.tr("Range filter"), self.tr("Both 'From' and 'To' values are required for a Range filter."))
                return False
            try:
                fromValue = float(fromText)
                toValue = float(toText)
            except ValueError:
                QMessageBox.warning(self, self.tr("Range filter"), self.tr("'From' and 'To' must be numeric."))
                return False
            if fromValue > toValue:
                QMessageBox.warning(self, self.tr("Range filter"), self.tr("'From' must be less than or equal to 'To'."))
                return False
            return "{0} >= {1} AND {0} <= {2}".format(quotedColumn, fromValue, toValue)

        valueText = self.cbValue.currentText().strip()
        valueData = self.cbValue.currentData(Qt.ItemDataRole.UserRole)
        rawValue = valueData if valueData not in (None, "") else valueText
        if rawValue in (None, ""):
            return ""
        operatorMap = {"=": "=", "≠": "<>", ">": ">", "<": "<", ">=": ">=", "<=": "<=",
                       "LIKE": " LIKE ", "NOT LIKE": " NOT LIKE ",
                       "ILIKE": " ILIKE ", "NOT ILIKE": " NOT ILIKE "}
        op = operatorMap.get(condition, condition)
        cat = self.classifyAttributeType(attributeField)
        if cat == "numeric":
            try:
                numericValue = float(rawValue)
            except (TypeError, ValueError):
                QMessageBox.warning(self, self.tr("Filter value"), self.tr("Numeric value required for this condition."))
                return False
            return "{0} {1} {2}".format(quotedColumn, op, numericValue)
        textValue = str(rawValue)
        if condition in ("LIKE", "NOT LIKE", "ILIKE", "NOT ILIKE"):
            quoted = QgsExpression.quotedString("%{}%".format(textValue))
        else:
            quoted = QgsExpression.quotedString(textValue)
        return "{0}{1}{2}".format(quotedColumn, op, quoted)

    def resolveBreaks(self, layer, classifyField):
        if self.isCategoricalClassifier(classifyField):
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=10000)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        rangedId = self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or "EqualInterval"
        if rangedId == "Categorized":
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=10000)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        numericValues = self.collectNumericValues(layer, classifyField)
        if not numericValues:
            QMessageBox.warning(self, self.tr("No data"), self.tr("No numeric values available for classification."))
            return None
        dataMin = numericValues[0]
        dataMax = numericValues[-1]
        if dataMin == dataMax:
            dataMax = dataMin + 1.0
        numClasses = self.cbClasses.value() or DEFAULT_NUM_CLASSES
        edges = self.calculateBreaks(rangedId, layer, classifyField, numericValues, numClasses, dataMin, dataMax)
        if edges is None or len(edges) < 2:
            QMessageBox.warning(self, self.tr("Breaks failed"), self.tr("Unable to compute breaks for the chosen method."))
            return None
        return {"type": "breaks", "edges": edges}

    def calculateBreaks(self, rangedId, layer, classifyField, values, numClasses, dataMin, dataMax):
        if rangedId == "EqualInterval":
            return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)
        if rangedId == "FixedInterval":
            return self.calculateFixedIntervalBreaks(dataMin, dataMax)
        if rangedId == "Quantile":
            return self.calculateQuantileBreaks(layer, classifyField, numClasses, dataMin)
        if rangedId == "Jenks":
            return self.calculateJenksBreaks(layer, classifyField, numClasses, dataMin)
        if rangedId == "Pretty":
            return self.calculatePrettyBreaks(layer, classifyField, numClasses, dataMin)
        if rangedId == "Manual":
            if not self.manualBreaks or len(self.manualBreaks) < 2:
                return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)
            return list(self.manualBreaks)
        return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)

    def calculateEqualIntervalBreaks(self, numClasses, dataMin, dataMax):
        step = (dataMax - dataMin) / float(numClasses)
        edges = [dataMin + i * step for i in range(numClasses + 1)]
        edges[-1] = dataMax
        return edges

    def calculateFixedIntervalBreaks(self, dataMin, dataMax):
        step = self.spinIntervalRange.value()
        if step <= 0:
            return [dataMin, dataMax]
        edges = [dataMin]
        current = dataMin
        while current < dataMax:
            current += step
            edges.append(current)
        return edges

    def calculateQuantileBreaks(self, layer, fieldName, numClasses, dataMin):
        classifier = QgsClassificationQuantile()
        classes = classifier.classes(layer, fieldName, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def calculateJenksBreaks(self, layer, fieldName, numClasses, dataMin):
        classifier = QgsClassificationJenks()
        classes = classifier.classes(layer, fieldName, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def calculatePrettyBreaks(self, layer, fieldName, numClasses, dataMin):
        classifier = QgsClassificationPrettyBreaks()
        classes = classifier.classes(layer, fieldName, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def initBins(self, breaks):
        bins = []
        if breaks["type"] == "categorical":
            for value in breaks["values"]:
                bins.append(self.makeBin(label=value if value != "" else self.tr("(empty)"),
                                         lo=None, hi=None, category=value))
            return bins
        edges = breaks["edges"]
        for i in range(len(edges) - 1):
            lowerEdge = edges[i]
            upperEdge = edges[i + 1]
            label = "{} - {}".format(self.formatNumber(lowerEdge), self.formatNumber(upperEdge))
            bins.append(self.makeBin(label=label, lo=lowerEdge, hi=upperEdge, category=None))
        return bins

    def makeBin(self, label, lo, hi, category):
        return {
            "label": label,
            "lo": lo,
            "hi": hi,
            "category": category,
            "count": 0,
            "sum": 0.0,
            "sumOfSquares": 0.0,
            "min": None,
            "max": None,
            "avg": 0.0,
            "stddev": 0.0,
            "values": set(),
        }

    def findBinIndex(self, bins, value, breakType):
        if breakType == "categorical":
            stringValue = str(value)
            for binIndex, binData in enumerate(bins):
                if binData.get("category") == stringValue:
                    return binIndex
            return None
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return None
        for binIndex, binData in enumerate(bins):
            lowerEdge = binData["lo"]
            upperEdge = binData["hi"]
            if binIndex == len(bins) - 1:
                if lowerEdge <= numericValue <= upperEdge:
                    return binIndex
            else:
                if lowerEdge <= numericValue < upperEdge:
                    return binIndex
        return None

    def accumulateValue(self, binData, value):
        binData["count"] += 1
        if self.isEnumeratedTarget:
            if value is not None:
                binData["values"].add(str(value))
            return
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return
        binData["sum"] += numericValue
        binData["sumOfSquares"] += numericValue * numericValue
        if binData["min"] is None or numericValue < binData["min"]:
            binData["min"] = numericValue
        if binData["max"] is None or numericValue > binData["max"]:
            binData["max"] = numericValue

    def finalizeBins(self, bins):
        for binData in bins:
            count = binData["count"]
            if count > 0 and not self.isEnumeratedTarget:
                binData["avg"] = binData["sum"] / count
                if count > 1:
                    variance = max(0.0, (binData["sumOfSquares"] - count * binData["avg"] * binData["avg"]) / (count - 1))
                    binData["stddev"] = math.sqrt(variance)

    def buildSubtitle(self, elementIdentifier):
        parts = []
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if attributeField:
            prettyAttribute = self.fieldUtils.getProperty(normalize_element(elementIdentifier), attributeField) or attributeField
            condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
            if condition == "Range":
                fromText = self.leFrom.text().strip() or "…"
                toText = self.leTo.text().strip() or "…"
                parts.append("{} {} {} - {}".format(prettyAttribute, self.tr("Range"), fromText, toText))
            elif condition and condition != "All":
                valueText = self.cbValue.currentText().strip()
                if valueText:
                    parts.append("{} {} {}".format(prettyAttribute, condition, valueText))
        if self.cbSelectedElements.isChecked():
            parts.append(self.tr("Only selected elements"))
        notes = []
        if self.lastNullCount:
            notes.append(self.tr("{0} nulls excluded").format(self.lastNullCount))
        if self.lastOutOfRangeCount:
            notes.append(self.tr("{0} out-of-range excluded").format(self.lastOutOfRangeCount))
        if notes:
            parts.append("(" + "; ".join(notes) + ")")
        return "; ".join(parts)

    def formatNumber(self, value):
        if value is None:
            return ""
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numericValue == int(numericValue) and abs(numericValue) < 1e9:
            return str(int(numericValue))
        return "{:g}".format(numericValue)

    def populateTable(self, bins, prettyClassify, prettyProperty, propertyUnit, elementIdentifier, propertyField):
        if self.isEnumeratedTarget:
            self.populateEnumeratedTable(bins, prettyClassify, prettyProperty)
        else:
            self.populateNumericTable(bins, prettyClassify, prettyProperty, propertyField, elementIdentifier)

    def populateNumericTable(self, bins, prettyClassify, prettyProperty, propertyField, elementIdentifier):
        useSum = self.usesSumColumn(propertyField, elementIdentifier)
        lastLabel = self.tr("Sum") if useSum else self.tr("StdD")
        headers = [
            prettyClassify,
            self.tr("Count"),
            self.tr("Avg"),
            self.tr("Min"),
            self.tr("Max"),
            lastLabel,
        ]
        self.tbExcel.setColumnCount(len(headers))
        self.tbExcel.setHorizontalHeaderLabels(headers)
        self.tbExcel.setRowCount(len(bins) + 1)

        totalCount = 0
        totalSum = 0.0
        totalSumOfSquares = 0.0
        totalMin = None
        totalMax = None

        for rowIndex, binData in enumerate(bins):
            self.setTableItem(rowIndex, 0, binData.get("label", ""))
            self.setTableItem(rowIndex, 1, str(binData["count"]))
            self.setTableItem(rowIndex, 2, self.formatNumber(binData["avg"]) if binData["count"] else "")
            self.setTableItem(rowIndex, 3, self.formatNumber(binData["min"]) if binData["min"] is not None else "")
            self.setTableItem(rowIndex, 4, self.formatNumber(binData["max"]) if binData["max"] is not None else "")
            if useSum:
                self.setTableItem(rowIndex, 5, self.formatNumber(binData["sum"]) if binData["count"] else "")
            else:
                self.setTableItem(rowIndex, 5, self.formatNumber(binData["stddev"]) if binData["count"] > 1 else "")
            totalCount += binData["count"]
            totalSum += binData["sum"]
            totalSumOfSquares += binData["sumOfSquares"]
            if binData["min"] is not None and (totalMin is None or binData["min"] < totalMin):
                totalMin = binData["min"]
            if binData["max"] is not None and (totalMax is None or binData["max"] > totalMax):
                totalMax = binData["max"]

        totalAvg = totalSum / totalCount if totalCount else 0.0
        totalStdDev = 0.0
        if totalCount > 1:
            variance = max(0.0, (totalSumOfSquares - totalCount * totalAvg * totalAvg) / (totalCount - 1))
            totalStdDev = math.sqrt(variance)

        totalRow = len(bins)
        self.setTableItem(totalRow, 0, self.tr("Total"), bold=True)
        self.setTableItem(totalRow, 1, str(totalCount), bold=True)
        self.setTableItem(totalRow, 2, self.formatNumber(totalAvg) if totalCount else "", bold=True)
        self.setTableItem(totalRow, 3, self.formatNumber(totalMin) if totalMin is not None else "", bold=True)
        self.setTableItem(totalRow, 4, self.formatNumber(totalMax) if totalMax is not None else "", bold=True)
        if useSum:
            self.setTableItem(totalRow, 5, self.formatNumber(totalSum), bold=True)
        else:
            self.setTableItem(totalRow, 5, self.formatNumber(totalStdDev) if totalCount > 1 else "", bold=True)

        header = self.tbExcel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, self.tbExcel.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        self.tbExcel.verticalHeader().setVisible(False)

    def populateEnumeratedTable(self, bins, prettyClassify, prettyProperty):
        headers = [prettyClassify, self.tr("Count"), prettyProperty]
        self.tbExcel.setColumnCount(len(headers))
        self.tbExcel.setHorizontalHeaderLabels(headers)
        self.tbExcel.setRowCount(len(bins) + 1)

        totalCount = 0
        totalValues = set()
        for rowIndex, binData in enumerate(bins):
            sortedValues = sorted(binData["values"], key=lambda item: str(item))
            joinedFull = ", ".join(sortedValues)
            joinedDisplay = self.truncateEnumString(joinedFull)
            self.setTableItem(rowIndex, 0, binData.get("label", ""))
            self.setTableItem(rowIndex, 1, str(binData["count"]))
            item = QTableWidgetItem(joinedDisplay)
            item.setToolTip(self.truncateEnumString(joinedFull))
            self.tbExcel.setItem(rowIndex, 2, item)
            totalCount += binData["count"]
            totalValues.update(binData["values"])

        totalSorted = sorted(totalValues, key=lambda item: str(item))
        totalJoinedFull = ", ".join(totalSorted)
        totalJoined = self.truncateEnumString(totalJoinedFull)
        totalRow = len(bins)
        self.setTableItem(totalRow, 0, self.tr("Total"), bold=True)
        self.setTableItem(totalRow, 1, str(totalCount), bold=True)
        totalItem = QTableWidgetItem(totalJoined)
        totalItem.setToolTip(self.truncateEnumString(totalJoinedFull))
        font = totalItem.font()
        font.setBold(True)
        totalItem.setFont(font)
        totalItem.setBackground(QBrush(QColor(255, 248, 220)))
        self.tbExcel.setItem(totalRow, 2, totalItem)

        header = self.tbExcel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        self.tbExcel.verticalHeader().setVisible(False)

    def truncateEnumString(self, text):
        if not text:
            return ""
        if len(text) <= ENUM_TEXT_LIMIT:
            return text
        return text[: ENUM_TEXT_LIMIT - 1] + "…"

    def usesSumColumn(self, prop, elementIdentifier):
        if prop == "Length" and elementIdentifier == "qgisred_pipes":
            return True
        if prop == "HeadLoss":
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category == "Link" or (elementIdentifier or "").startswith("qgisred_link"):
                return True
        if prop == "BaseDem" and elementIdentifier == "qgisred_junctions":
            return True
        if prop == "BaseValue" and elementIdentifier == "qgisred_demands":
            return True
        if prop == "BaseDemand" and elementIdentifier == "qgisred_serviceconnections":
            return True
        if prop == "Demand":
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category == "Node" or (elementIdentifier or "").startswith("qgisred_node"):
                return True
        return prop in CUMULATIVE_PROPERTIES

    def setTableItem(self, row, column, text, bold=False):
        item = QTableWidgetItem(text)
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QBrush(QColor(255, 248, 220)))
        self.tbExcel.setItem(row, column, item)

    def importConfig(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(
            self,
            self.tr("Import query configuration"),
            str(QgsProject.instance().homePath() or ""),
            "JSON Files (*.json)",
        )
        if not fileName:
            return
        try:
            with open(fileName, "r", encoding="utf-8") as fileHandle:
                data = json.load(fileHandle)
            if data.get("schema") != "qgisred.statistics.v1":
                raise ValueError(self.tr("Unrecognized configuration schema."))
            self.applyConfig(data)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Import failed"), str(ex))

    def applyConfig(self, data):
        self.suspendCascade = True
        elementIndex = self.cbElementType.findData(data.get("elementType", ""))
        if elementIndex >= 0:
            self.cbElementType.setCurrentIndex(elementIndex)
        self.suspendCascade = False
        self.onElementTypeChanged()

        propertyIndex = self.cbProperty.findData(data.get("property", ""))
        if propertyIndex >= 0:
            self.cbProperty.setCurrentIndex(propertyIndex)

        classifyIndex = self.cbClassifiedBy.findData(data.get("classifyBy", ""))
        if classifyIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(classifyIndex)

        rangedIndex = self.cbRanged.findData(data.get("ranged", ""))
        if rangedIndex >= 0:
            self.cbRanged.setCurrentIndex(rangedIndex)

        classes = data.get("classes")
        if classes is not None:
            self.cbClasses.setValue(int(classes))

        interval = data.get("interval")
        if interval is not None:
            try:
                self.spinIntervalRange.setValue(float(interval))
            except (TypeError, ValueError):
                pass

        filterData = data.get("filter") or {}
        attributeIndex = self.cbAttribute.findData(filterData.get("attribute", "") or "")
        if attributeIndex >= 0:
            self.cbAttribute.setCurrentIndex(attributeIndex)
        conditionIndex = self.cbCondition.findData(filterData.get("condition", "") or "")
        if conditionIndex >= 0:
            self.cbCondition.setCurrentIndex(conditionIndex)
        self.updateValueWidget()
        valueText = filterData.get("value")
        if valueText is not None:
            valueIndex = self.cbValue.findText(str(valueText))
            if valueIndex >= 0:
                self.cbValue.setCurrentIndex(valueIndex)
            else:
                self.cbValue.setEditText(str(valueText))
        self.leFrom.setText("" if filterData.get("from") is None else str(filterData.get("from")))
        self.leTo.setText("" if filterData.get("to") is None else str(filterData.get("to")))
        self.cbSelectedElements.setChecked(bool(data.get("onlySelected")))

    def exportConfig(self):
        defaultFileName = "qgisred_statistics_query_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
        fileName, _selectedFilter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export query configuration"),
            os.path.join(str(QgsProject.instance().homePath() or ""), defaultFileName),
            "JSON Files (*.json)",
        )
        if not fileName:
            return
        try:
            data = {
                "schema": "qgisred.statistics.v1",
                "elementType": self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or "",
                "property": self.cbProperty.currentData(Qt.ItemDataRole.UserRole) or "",
                "classifyBy": self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or "",
                "ranged": self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or "",
                "classes": self.cbClasses.value(),
                "interval": self.spinIntervalRange.value(),
                "filter": {
                    "attribute": self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) or "",
                    "condition": self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or "",
                    "value": self.cbValue.currentText() or None,
                    "from": self.leFrom.text().strip() or None,
                    "to": self.leTo.text().strip() or None,
                },
                "onlySelected": self.cbSelectedElements.isChecked(),
            }
            with open(fileName, "w", encoding="utf-8") as fileHandle:
                json.dump(data, fileHandle, indent=2)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Export failed"), str(ex))

    def exportTableCsv(self):
        if self.tbExcel.rowCount() == 0:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("Run Analyze before exporting the table."),
            )
            return
        projectName = QgsProject.instance().baseName() or "QGISRed"
        defaultFileName = "{}_statistics_{}.csv".format(projectName, datetime.now().strftime("%Y%m%d_%H%M%S"))
        fileName, _selectedFilter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export table to CSV"),
            os.path.join(str(QgsProject.instance().homePath() or ""), defaultFileName),
            "CSV Files (*.csv)",
        )
        if not fileName:
            return
        try:
            elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
            propertyField = self.cbProperty.currentData(Qt.ItemDataRole.UserRole) or ""
            classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or ""
            with open(fileName, "w", newline="", encoding="utf-8") as fileHandle:
                writer = csv.writer(fileHandle)
                fileHandle.write("Project: {}\n".format(projectName))
                fileHandle.write("Element Type: {}\n".format(elementIdentifier))
                fileHandle.write("Property: {}\n".format(propertyField))
                fileHandle.write("Classified by: {}\n".format(classifyField))
                subtitle = self.buildSubtitle(elementIdentifier)
                if subtitle:
                    fileHandle.write("Filter: {}\n".format(subtitle))
                fileHandle.write("\n")
                headers = [
                    self.tbExcel.horizontalHeaderItem(column).text() if self.tbExcel.horizontalHeaderItem(column) else ""
                    for column in range(self.tbExcel.columnCount())
                ]
                writer.writerow(headers)
                for row in range(self.tbExcel.rowCount()):
                    rowData = [
                        self.tbExcel.item(row, column).text() if self.tbExcel.item(row, column) else ""
                        for column in range(self.tbExcel.columnCount())
                    ]
                    writer.writerow(rowData)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Export failed"), str(ex))
