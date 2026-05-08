# -*- coding: utf-8 -*-
import csv
import json
import math
import os
from datetime import datetime

from qgis.PyQt.QtCore import Qt
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
from qgis.core import QgsExpression, QgsFeatureRequest, QgsProject

from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from .statistics_histogram_widget import StatisticsHistogramWidget
from .statistics_metadata import (
    DEFAULT_NUM_CLASSES,
    ELEMENT_PROPERTIES,
    ELEMENT_TYPE_ORDER,
    NUM_CLASSES_CHOICES,
    getPropertyMode,
    getRangedOptions,
    getRangedPreset,
    isCategoricalField,
)

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statisticsandgraphs_dock.ui"))


class QGISRedStatisticsAndPlotsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsAndPlotsDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.fieldUtils = QGISRedFieldUtils()
        self.suspendCascade = False
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0

        self.setupHistogram()
        self.setupIcons()
        self.setupConnections()
        self.populateElementTypes()
        self.loadDefaults()

    def safeDisconnect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def setupHistogram(self):
        self.histogram = StatisticsHistogramWidget(self.graphWidget)
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

    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.onElementTypeChanged)
        self.cbProperty.currentIndexChanged.connect(self.onPropertyChanged)
        self.cbClassifiedBy.currentIndexChanged.connect(self.onClassifyByChanged)
        self.cbRanged.currentIndexChanged.connect(self.onRangedChanged)
        self.cbAttribute.currentIndexChanged.connect(self.onAttributeChanged)
        self.btAnalyze.clicked.connect(self.analyze)
        self.btImport.clicked.connect(self.importConfig)
        self.btExport.clicked.connect(self.exportConfig)
        self.btExcel.clicked.connect(self.exportTableCsv)

    def disconnectSignals(self):
        self.safeDisconnect(self.cbElementType.currentIndexChanged, self.onElementTypeChanged)
        self.safeDisconnect(self.cbProperty.currentIndexChanged, self.onPropertyChanged)
        self.safeDisconnect(self.cbClassifiedBy.currentIndexChanged, self.onClassifyByChanged)
        self.safeDisconnect(self.cbRanged.currentIndexChanged, self.onRangedChanged)
        self.safeDisconnect(self.cbAttribute.currentIndexChanged, self.onAttributeChanged)
        self.safeDisconnect(self.btAnalyze.clicked, self.analyze)
        self.safeDisconnect(self.btImport.clicked, self.importConfig)
        self.safeDisconnect(self.btExport.clicked, self.exportConfig)
        self.safeDisconnect(self.btExcel.clicked, self.exportTableCsv)

    def populateElementTypes(self):
        self.suspendCascade = True
        self.cbElementType.clear()
        for elementIdentifier in ELEMENT_TYPE_ORDER:
            self.cbElementType.addItem(self.displayNameForIdentifier(elementIdentifier), elementIdentifier)
        self.suspendCascade = False

    def displayNameForIdentifier(self, elementIdentifier):
        names = {
            "qgisred_pipes": self.tr("Pipes"),
            "qgisred_junctions": self.tr("Junctions"),
            "qgisred_tanks": self.tr("Tanks"),
            "qgisred_reservoirs": self.tr("Reservoirs"),
            "qgisred_valves": self.tr("Valves"),
            "qgisred_pumps": self.tr("Pumps"),
            "qgisred_serviceconnections": self.tr("Service Connections"),
            "qgisred_isolationvalves": self.tr("Isolation Valves"),
        }
        return names.get(elementIdentifier, elementIdentifier)

    def loadDefaults(self):
        defaultIndex = self.cbElementType.findData("qgisred_pipes")
        if defaultIndex >= 0:
            self.cbElementType.setCurrentIndex(defaultIndex)
        self.onElementTypeChanged()
        propertyIndex = self.cbProperty.findData("Length")
        if propertyIndex >= 0:
            self.cbProperty.setCurrentIndex(propertyIndex)
        classifyIndex = self.cbClassifiedBy.findData("Diameter")
        if classifyIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(classifyIndex)

    def onElementTypeChanged(self):
        if self.suspendCascade:
            return
        self.suspendCascade = True
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        meta = ELEMENT_PROPERTIES.get(elementIdentifier, {"properties": [], "classifyBy": []})
        self.populateFieldCombo(self.cbProperty, elementIdentifier, meta["properties"])
        self.populateFieldCombo(self.cbClassifiedBy, elementIdentifier, meta["classifyBy"])
        self.populateAttributeCombo(elementIdentifier)
        self.suspendCascade = False
        self.onClassifyByChanged()
        self.onAttributeChanged()
        self.histogram.clear()
        self.tbExcel.setRowCount(0)
        self.labelOnlySelectedElements.hide()

    def onPropertyChanged(self):
        if self.suspendCascade:
            return

    def onClassifyByChanged(self):
        if self.suspendCascade:
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        self.suspendCascade = True
        self.cbRanged.clear()
        for option in getRangedOptions(elementIdentifier, classifyField):
            self.cbRanged.addItem(self.tr(option), option)
        self.cbClasses.clear()
        for classCount in NUM_CLASSES_CHOICES:
            self.cbClasses.addItem(str(classCount), classCount)
        defaultClassesIndex = self.cbClasses.findData(DEFAULT_NUM_CLASSES)
        if defaultClassesIndex >= 0:
            self.cbClasses.setCurrentIndex(defaultClassesIndex)
        self.suspendCascade = False
        self.onRangedChanged()

    def onRangedChanged(self):
        if self.suspendCascade:
            return
        rangedMode = self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or ""
        self.cbClasses.setEnabled(rangedMode == "Auto")

    def onAttributeChanged(self):
        if self.suspendCascade:
            return
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        self.cbValueRange.clear()
        self.leFrom.clear()
        self.leTo.clear()
        if not attributeField:
            self.cbValueRange.setEnabled(False)
            self.leFrom.setEnabled(False)
            self.leTo.setEnabled(False)
            return
        self.cbValueRange.addItem(self.tr("(any)"), "")
        layer = self.resolveLayer()
        if layer is not None:
            for value in self.collectUniqueValues(layer, attributeField, limit=200):
                self.cbValueRange.addItem(str(value), value)
        self.cbValueRange.setEnabled(True)
        if isCategoricalField(attributeField):
            self.leFrom.setEnabled(False)
            self.leTo.setEnabled(False)
        else:
            self.leFrom.setEnabled(True)
            self.leTo.setEnabled(True)

    def populateFieldCombo(self, combo, elementIdentifier, fieldNames):
        combo.clear()
        for fieldName in fieldNames:
            combo.addItem(self.fieldDisplayLabel(elementIdentifier, fieldName), fieldName)

    def populateAttributeCombo(self, elementIdentifier):
        meta = ELEMENT_PROPERTIES.get(elementIdentifier, {})
        attributeFields = list(dict.fromkeys((meta.get("properties") or []) + (meta.get("classifyBy") or [])))
        self.cbAttribute.clear()
        self.cbAttribute.addItem(self.tr("(no filter)"), "")
        for fieldName in attributeFields:
            self.cbAttribute.addItem(self.fieldDisplayLabel(elementIdentifier, fieldName), fieldName)

    def fieldDisplayLabel(self, elementIdentifier, fieldName):
        prettyName = self.fieldUtils.getFieldPrettyName(elementIdentifier, fieldName) or fieldName
        unit = self.fieldUtils.getFieldUnit(elementIdentifier, fieldName) or ""
        if unit:
            return "{} ({})".format(prettyName, unit)
        return prettyName

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

    def resolveLayer(self):
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        if not elementIdentifier:
            return None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.customProperty("qgisred_identifier") == elementIdentifier:
                return layer
        return None

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

        attributeExpression = self.buildAttributeExpression(layer)
        if attributeExpression:
            request.combineFilterExpression(attributeExpression)
            applied = True
        return request if applied else None

    def buildAttributeExpression(self, layer):
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if not attributeField:
            return ""
        if layer.fields().indexFromName(attributeField) < 0:
            return ""
        quotedColumn = QgsExpression.quotedColumnRef(attributeField)
        clauses = []
        valueData = self.cbValueRange.currentData(Qt.ItemDataRole.UserRole)
        valueText = self.cbValueRange.currentText()
        if valueData not in (None, ""):
            clauses.append("{} = {}".format(quotedColumn, self.quoteValue(valueData)))
        elif valueText and valueText != self.tr("(any)"):
            clauses.append("{} = {}".format(quotedColumn, self.quoteValue(valueText)))
        if self.leFrom.isEnabled():
            fromText = self.leFrom.text().strip()
            if fromText:
                try:
                    clauses.append("{} >= {}".format(quotedColumn, float(fromText)))
                except ValueError:
                    pass
        if self.leTo.isEnabled():
            toText = self.leTo.text().strip()
            if toText:
                try:
                    clauses.append("{} <= {}".format(quotedColumn, float(toText)))
                except ValueError:
                    pass
        return " AND ".join(clauses)

    def quoteValue(self, value):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return QgsExpression.quotedString(str(value))

    def resolveBreaks(self, layer, elementIdentifier, classifyField):
        if isCategoricalField(classifyField):
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=500)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        rangedMode = self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or "Auto"
        if rangedMode == "Preset":
            preset = getRangedPreset(elementIdentifier, classifyField)
            if preset and preset.get("type") == "breaks":
                return {"type": "breaks", "edges": list(preset["values"])}
            rangedMode = "Auto"
        if rangedMode == "Distinct":
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=500)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        numClasses = self.cbClasses.currentData(Qt.ItemDataRole.UserRole) or DEFAULT_NUM_CLASSES
        edges = self.computeAutoBreaks(layer, classifyField, numClasses)
        if edges is None:
            return None
        return {"type": "breaks", "edges": edges}

    def computeAutoBreaks(self, layer, classifyField, numClasses):
        if layer.fields().indexFromName(classifyField) < 0:
            return None
        valueMin = None
        valueMax = None
        for feature in layer.getFeatures():
            rawValue = feature[classifyField]
            if rawValue is None:
                continue
            try:
                numericValue = float(rawValue)
            except (TypeError, ValueError):
                continue
            if valueMin is None or numericValue < valueMin:
                valueMin = numericValue
            if valueMax is None or numericValue > valueMax:
                valueMax = numericValue
        if valueMin is None or valueMax is None:
            return None
        if valueMin == valueMax:
            valueMax = valueMin + 1.0
        step = (valueMax - valueMin) / float(numClasses)
        edges = [valueMin + i * step for i in range(numClasses + 1)]
        edges[-1] = valueMax
        return edges

    def initBins(self, breaks):
        bins = []
        if breaks["type"] == "categorical":
            for value in breaks["values"]:
                bins.append({
                    "label": value if value != "" else self.tr("(empty)"),
                    "lo": None,
                    "hi": None,
                    "category": value,
                    "count": 0,
                    "sum": 0.0,
                    "sumOfSquares": 0.0,
                    "min": None,
                    "max": None,
                    "avg": 0.0,
                    "stddev": 0.0,
                })
            return bins
        edges = breaks["edges"]
        for i in range(len(edges) - 1):
            lowerEdge = edges[i]
            upperEdge = edges[i + 1]
            label = "{} - {}".format(self.formatNumber(lowerEdge), self.formatNumber(upperEdge))
            bins.append({
                "label": label,
                "lo": lowerEdge,
                "hi": upperEdge,
                "category": None,
                "count": 0,
                "sum": 0.0,
                "sumOfSquares": 0.0,
                "min": None,
                "max": None,
                "avg": 0.0,
                "stddev": 0.0,
            })
        return bins

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
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            numericValue = None
        binData["count"] += 1
        if numericValue is not None:
            binData["sum"] += numericValue
            binData["sumOfSquares"] += numericValue * numericValue
            if binData["min"] is None or numericValue < binData["min"]:
                binData["min"] = numericValue
            if binData["max"] is None or numericValue > binData["max"]:
                binData["max"] = numericValue

    def finalizeBins(self, bins):
        for binData in bins:
            count = binData["count"]
            if count > 0:
                binData["avg"] = binData["sum"] / count
                if count > 1:
                    variance = max(0.0, (binData["sumOfSquares"] - count * binData["avg"] * binData["avg"]) / (count - 1))
                    binData["stddev"] = math.sqrt(variance)
                else:
                    binData["stddev"] = 0.0
            else:
                binData["avg"] = 0.0
                binData["stddev"] = 0.0
                binData["min"] = None
                binData["max"] = None
