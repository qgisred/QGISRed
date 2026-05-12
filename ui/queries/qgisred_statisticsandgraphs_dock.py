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


class QGISRedStatisticsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsDock, self).__init__(parent or iface.mainWindow())
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
        if layer.fields().indexFromName(propertyField) < 0:
            QMessageBox.warning(
                self,
                self.tr("Field missing"),
                self.tr("Property field '{0}' was not found on the layer.").format(propertyField),
            )
            return
        if layer.fields().indexFromName(classifyField) < 0:
            QMessageBox.warning(
                self,
                self.tr("Field missing"),
                self.tr("Classification field '{0}' was not found on the layer.").format(classifyField),
            )
            return

        propertyMode = getPropertyMode(propertyField)
        featureRequest = self.buildFeatureRequest(layer)
        if featureRequest is False:
            return

        breaks = self.resolveBreaks(layer, elementIdentifier, classifyField)
        if breaks is None:
            return
        bins = self.initBins(breaks)
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0

        featureIterator = layer.getFeatures(featureRequest) if featureRequest is not None else layer.getFeatures()
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

        prettyProperty = self.fieldUtils.getFieldPrettyName(elementIdentifier, propertyField) or propertyField
        prettyClassify = self.fieldUtils.getFieldPrettyName(elementIdentifier, classifyField) or classifyField
        propertyUnit = self.fieldUtils.getFieldUnit(elementIdentifier, propertyField) or ""
        classifyUnit = self.fieldUtils.getFieldUnit(elementIdentifier, classifyField) or ""

        title = "{} ({} {})".format(prettyProperty, self.tr("by"), prettyClassify)
        subtitle = self.buildSubtitle(elementIdentifier)
        xLabel = "{} ({})".format(prettyClassify, classifyUnit) if classifyUnit else prettyClassify
        if propertyMode in ("cumulative", "intensive"):
            yLabel = "{} ({})".format(prettyProperty, propertyUnit) if propertyUnit else prettyProperty
        else:
            yLabel = self.tr("Count")

        self.histogram.setTitles(title, subtitle)
        self.histogram.setBins(bins, mode=propertyMode, xLabel=xLabel, yLabelLeft=yLabel)

        self.populateTable(bins, prettyClassify)
        try:
            self.mGroupBox.setCollapsed(False)
        except Exception:
            pass

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

    def buildSubtitle(self, elementIdentifier):
        parts = []
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if attributeField:
            prettyAttribute = self.fieldUtils.getFieldPrettyName(elementIdentifier, attributeField) or attributeField
            valueData = self.cbValueRange.currentData(Qt.ItemDataRole.UserRole)
            valueText = self.cbValueRange.currentText()
            if valueData not in (None, ""):
                parts.append("{} = {}".format(prettyAttribute, valueData))
            elif valueText and valueText != self.tr("(any)"):
                parts.append("{} = {}".format(prettyAttribute, valueText))
            fromText = self.leFrom.text().strip() if self.leFrom.isEnabled() else ""
            toText = self.leTo.text().strip() if self.leTo.isEnabled() else ""
            if fromText or toText:
                parts.append("{} {} - {}".format(prettyAttribute, fromText or "…", toText or "…"))
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
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numericValue == int(numericValue) and abs(numericValue) < 1e9:
            return str(int(numericValue))
        return "{:g}".format(numericValue)

    def populateTable(self, bins, prettyClassify):
        headers = [
            prettyClassify,
            self.tr("Count"),
            self.tr("Sum"),
            self.tr("Avg"),
            self.tr("Min"),
            self.tr("Max"),
            self.tr("StdDev"),
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
            self.setTableItem(rowIndex, 2, self.formatNumber(binData["sum"]))
            self.setTableItem(rowIndex, 3, self.formatNumber(binData["avg"]) if binData["count"] else "")
            self.setTableItem(rowIndex, 4, self.formatNumber(binData["min"]) if binData["min"] is not None else "")
            self.setTableItem(rowIndex, 5, self.formatNumber(binData["max"]) if binData["max"] is not None else "")
            self.setTableItem(rowIndex, 6, self.formatNumber(binData["stddev"]) if binData["count"] > 1 else "")
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
        self.setTableItem(totalRow, 2, self.formatNumber(totalSum), bold=True)
        self.setTableItem(totalRow, 3, self.formatNumber(totalAvg) if totalCount else "", bold=True)
        self.setTableItem(totalRow, 4, self.formatNumber(totalMin) if totalMin is not None else "", bold=True)
        self.setTableItem(totalRow, 5, self.formatNumber(totalMax) if totalMax is not None else "", bold=True)
        self.setTableItem(totalRow, 6, self.formatNumber(totalStdDev) if totalCount > 1 else "", bold=True)

        header = self.tbExcel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, self.tbExcel.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(False)
        self.tbExcel.verticalHeader().setVisible(False)

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
            classesIndex = self.cbClasses.findData(int(classes))
            if classesIndex >= 0:
                self.cbClasses.setCurrentIndex(classesIndex)

        filterData = data.get("filter") or {}
        attributeIndex = self.cbAttribute.findData(filterData.get("attribute", "") or "")
        if attributeIndex >= 0:
            self.cbAttribute.setCurrentIndex(attributeIndex)
        valueIndex = self.cbValueRange.findData(filterData.get("value", "") or "")
        if valueIndex >= 0:
            self.cbValueRange.setCurrentIndex(valueIndex)
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
                "classes": self.cbClasses.currentData(Qt.ItemDataRole.UserRole),
                "filter": {
                    "attribute": self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) or "",
                    "value": self.cbValueRange.currentData(Qt.ItemDataRole.UserRole) or "",
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
