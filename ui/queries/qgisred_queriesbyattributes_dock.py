# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QToolButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest
from qgis.gui import QgsHighlight
import os
from PyQt5 import sip
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime
import csv

from ..analysis.qgisred_results_dock import QGISRedResultsDock

# load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),"qgisred_queriesbyattributes_dock.ui"))

class QGISRedQueriesByAttributesDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(QGISRedQueriesByAttributesDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.initializeQueriesByAttributes()

    def closeEvent(self, event):
        self.resultsDockVisibilityTimer.stop()
        self.resultsDockPollTimer.stop()
        self.disconnectResultsDock()
        self.clearMapSelection()
        super().closeEvent(event)

    def clearHighlights(self):
        for h in self.queryHighlights:
            h.hide()
        self.queryHighlights.clear()

    def highlightFeatures(self, layer, expression):
        self.clearHighlights()
        if expression:
            featureReq = QgsFeatureRequest().setFilterExpression(expression)
            for feat in layer.getFeatures(featureReq):
                h = QgsHighlight(self.canvas, feat.geometry(), layer)
                h.setColor(QColor("red"))
                h.setWidth(5)
                h.show()
                self.queryHighlights.append(h)
            self.lastSelectedLayer = layer
        else:
            self.lastSelectedLayer = None
        self.canvas.refresh()

    def clearMapSelection(self):
        self.clearHighlights()
        if self.lastSelectedLayer is not None:
            try:
                if not sip.isdeleted(self.lastSelectedLayer):
                    self.lastSelectedLayer.removeSelection()
            except RuntimeError:
                pass
            self.lastSelectedLayer = None
            self.canvas.refresh()

    def initializeQueriesByAttributes(self):
        self.criteria = []
        self.currentlyReplacingIndex = None
        self.isResultsMode = False
        self.resultsDock = None
        self.currentResultsTimeText = ""
        self.currentResultsStatText = ""
        self.lastSelectedLayer = None
        self.lastCombinedExpression = ""
        self.queryHighlights = []

        self.resultsDockVisibilityTimer = QTimer()
        self.resultsDockVisibilityTimer.setSingleShot(True)
        self.resultsDockVisibilityTimer.setInterval(150)
        self.resultsDockVisibilityTimer.timeout.connect(self.checkResultsDockClosed)

        self.resultsDockPollTimer = QTimer()
        self.resultsDockPollTimer.setInterval(1500)
        self.resultsDockPollTimer.timeout.connect(self.pollForResultsDock)

        self.elementIdentifiers = {
            'Pipes': 'qgisred_pipes',
            'Junctions': 'qgisred_junctions',
            'Demands': 'qgisred_demands',
            'Reservoirs': 'qgisred_reservoirs',
            'Tanks': 'qgisred_tanks',
            'Pumps': 'qgisred_pumps',
            'Valves': 'qgisred_valves',
            'Sources': 'qgisred_sources',
            'Service Connections': 'qgisred_serviceconnections',
            'Isolation Valves': 'qgisred_isolationvalves',
            'Meters': 'qgisred_meters'
        }

        self.conditionsByType = {
            'numeric': ['>=', '<=', '=', '>', '<', '≠'],
            'listed': ['=']
        }

        self.fieldTypeMapping = {
            'int': 'numeric',
            'double': 'numeric',
            'string': 'listed',
            'date': 'numeric',
            'datetime': 'numeric',
            'time': 'numeric',
            'bool': 'listed'
        }

        self.tableWidgetCriteria.setColumnCount(2)
        self.tableWidgetCriteria.setHorizontalHeaderLabels(["   Oper   ", "Criteria"])
        self.tableWidgetCriteria.verticalHeader().setVisible(False)
        h = self.tableWidgetCriteria.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)

        # set up statistics table
        if self.tableWidgetStatistics.columnCount() == 0:
            self.tableWidgetStatistics.setColumnCount(5)
            self.tableWidgetStatistics.setHorizontalHeaderLabels(
                ["Count", "Sum", "Avg", "Min", "Max"]
            )
            for i in range(5):
                self.tableWidgetStatistics.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.Stretch
                )


        self.criteria = []
        self.currentlyReplacingIndex = None
        # track which row (if any) is being edited
        self.editingIndex = None

        self.initializeElementTypes()
        self.setupConnections()
        self.setupButtonIcons()
        self.mGroupBox.setCollapsed(False)
        self.frameMultipleCriteria.setVisible(False)
        f = self.radioSingleCriteria.font()
        f.setBold(True)
        self.radioSingleCriteria.setFont(f)


    def setupButtonIcons(self): #TODO rename to QGISRed folder instead of BID on deploy
        self.btImport.setIcon(QIcon(":/images/iconStatisticsImport.svg"))
        self.btExport.setIcon(QIcon(":/images/iconStatisticsExport.svg"))

        self.btCriteriaUp.setIcon(QIcon(":/images/iconStatisticsArrowUp.svg"))
        self.btCriteriaDown.setIcon(QIcon(":/images/iconStatisticsArrowDown.svg"))
        self.btCriteriaClear.setIcon(QIcon(":/images/iconStatisticsDelete.svg"))
        self.btCriteriaEdit.setIcon(QIcon(":/images/iconStatisticsEdit.svg"))

        self.iconSwitchEnabled  = QIcon(":/images/iconSwitchEnabled.svg")
        self.iconSwitchDisabled = QIcon(":/images/iconSwitchDisabled.svg")

        self.btCriteriaSwitch.setIcon(self.iconSwitchEnabled)

        self.btExcel.setIcon(QIcon(":/images/iconStatisticsExcel.svg"))

    def setupConnections(self):
        # element / property updates
        self.cbElementType.currentIndexChanged.connect(self.updateProperties)
        self.cbProperty.currentIndexChanged.connect(self.updateValues)
        # main buttons
        self.btAdd.clicked.connect(lambda: self.addCriterion('+'))
        self.btSubtract.clicked.connect(lambda: self.addCriterion('-'))
        self.btReplace.clicked.connect(self.replaceCriterion)
        self.btClear.clicked.connect(self.clearCriteria)
        self.btSubmit.clicked.connect(self.runQuery)

        # criteria table buttons
        self.btCriteriaUp.clicked.connect(self.moveCriterionUp)
        self.btCriteriaDown.clicked.connect(self.moveCriterionDown)
        self.btCriteriaClear.clicked.connect(self.clearCriteriaItem)
        self.btCriteriaEdit.setCheckable(True)
        self.btCriteriaEdit.clicked.connect(self.toggleEditCriterion)
        self.btCriteriaSwitch.clicked.connect(self.toggleCriterionEnabled)
        self.tableWidgetCriteria.currentCellChanged.connect(self.onCriteriaSelectionChanged)

        # radio criteria mode
        self.radioMultipleCriteria.toggled.connect(self.toggleMultipleCriteria)

        # update submit state as user types in value field
        self.cbValue.textChanged.connect(lambda: self.updateButtonsState())

        # export
        self.btExport.clicked.connect(self.exportCriteria)
        self.btExcel.clicked.connect(self.exportStatistics)

        # stats property change
        self.cbStatisticsFor.currentIndexChanged.connect(self.onStatisticsForChanged)
        # initial button state
        self.updateButtonsState()

    def toggleMultipleCriteria(self, visible):
        if visible:
            # Single → Multiple: auto-add current fields as first criterion
            prop = self.cbProperty.currentText()
            cond = self.cbCondition.currentText()
            val_txt = self.cbValue.value()
            if prop and cond and val_txt:
                crit = {
                    'property': prop,
                    'condition': cond,
                    'value': self.parseValue(val_txt),
                    'operator': '+',
                    'enabled': True
                }
                self.criteria.insert(0, crit)
                self.reloadCriteriaTable()
        else:
            # Multiple → Single: confirm if losing criteria
            if len(self.criteria) > 1:
                reply = QMessageBox.question(
                    self,
                    self.tr("Switch to Single Criteria"),
                    self.tr("Switching to single criteria will discard all criteria except the first one. Proceed?"),
                    QMessageBox.Ok | QMessageBox.Cancel,
                    QMessageBox.Cancel
                )
                if reply == QMessageBox.Cancel:
                    # revert to multiple without re-triggering this handler
                    self.radioMultipleCriteria.blockSignals(True)
                    self.radioMultipleCriteria.setChecked(True)
                    self.radioMultipleCriteria.blockSignals(False)
                    return
            # Populate single fields from first criterion if available
            if self.criteria:
                first = self.criteria[0]
                self.cbProperty.setCurrentText(first['property'])
                self.cbCondition.setCurrentText(first['condition'])
                self.cbValue.setValue(str(first['value']))
                self.criteria = []
                self.reloadCriteriaTable()

        self.frameMultipleCriteria.setVisible(visible)
        for radio in (self.radioSingleCriteria, self.radioMultipleCriteria):
            f = radio.font()
            f.setBold(radio.isChecked())
            radio.setFont(f)
        self.updateButtonsState()

    def onStatisticsForChanged(self):
        if self.cbStatisticsFor.isEnabled():
            self.calculateStatistics()

    def initializeElementTypes(self):
        self.cbElementType.clear()
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputsGroup:
            identifiers = set(self.elementIdentifiers.values())
            for layerNode in inputsGroup.findLayers():
                layer = layerNode.layer()
                if layer and layer.customProperty("qgisred_identifier") in identifiers:
                    self.cbElementType.addItem(layer.name(), layer.customProperty("qgisred_identifier"))
        resultsGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if resultsGroup:
            nodeIdent = linkIdent = None
            for layerNode in resultsGroup.findLayers():
                layer = layerNode.layer()
                if not layer:
                    continue
                ident = layer.customProperty("qgisred_identifier") or ""
                if ident.startswith("qgisred_node") and nodeIdent is None:
                    nodeIdent = ident
                elif ident.startswith("qgisred_link") and linkIdent is None:
                    linkIdent = ident
            if nodeIdent:
                self.cbElementType.addItem(self.tr("Nodes"), nodeIdent)
            if linkIdent:
                self.cbElementType.addItem(self.tr("Lines"), linkIdent)
        self.updateProperties()

    def isResultsLayer(self, layer):
        if not layer:
            return False
        ident = layer.customProperty("qgisred_identifier") or ""
        return ident.startswith("qgisred_node") or ident.startswith("qgisred_link")

    def updateButtonsState(self):
        isMultiple = self.radioMultipleCriteria.isChecked()
        if isMultiple:
            has = len(self.criteria) > 0
            sel = self.tableWidgetCriteria.currentRow() >= 0
            self.btSubtract.setEnabled(has)
            self.btReplace.setEnabled(has and sel)
            self.btClear.setEnabled(has)
            self.btSubmit.setEnabled(has)
            self.cbElementType.setEnabled(not has or self.isResultsMode)
        else:
            hasValue = bool(self.cbValue.value())
            self.btSubmit.setEnabled(hasValue)
            self.cbElementType.setEnabled(True)
        self.cbStatisticsFor.setEnabled(self.btSubmit.isEnabled())

    def moveCriterionUp(self):
        row = self.tableWidgetCriteria.currentRow()
        if row > 0:
            self.criteria[row - 1], self.criteria[row] = (
                self.criteria[row],
                self.criteria[row - 1],
            )
            self.reloadCriteriaTable()
            self.tableWidgetCriteria.selectRow(row - 1)

    def moveCriterionDown(self):
        row = self.tableWidgetCriteria.currentRow()
        if 0 <= row < len(self.criteria) - 1:
            self.criteria[row], self.criteria[row + 1] = (
                self.criteria[row + 1],
                self.criteria[row],
            )
            self.reloadCriteriaTable()
            self.tableWidgetCriteria.selectRow(row + 1)

    def clearCriteriaItem(self):
        row = self.tableWidgetCriteria.currentRow()
        if row >= 0:
            self.criteria.pop(row)
        else:
            self.criteria = []
        self.currentlyReplacingIndex = None

        self.reloadCriteriaTable()

        self.tableWidgetCriteria.clearSelection()

    def resolveLayer(self):
        """Resolve the current qgisred_identifier from the combobox to a live QgsVectorLayer."""
        qrIdent = self.cbElementType.currentData(Qt.UserRole)
        if not qrIdent:
            return None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.customProperty("qgisred_identifier") == qrIdent:
                return layer
        return None

    def updateProperties(self):
        layer = self.resolveLayer()
        if not layer:
            return
        self.isResultsMode = self.isResultsLayer(layer)
        self.cbProperty.clear()
        self.cbStatisticsFor.clear()
        excludedLower = {'id', 'descrip'}
        resultsMetaLower = {'time', 'statistics', 'time_h', 'time_d', 'time_q', 'type'}
        for field in layer.fields():
            fn = field.name()
            fnl = fn.lower()
            if fnl in excludedLower:
                continue
            if self.isResultsMode and fnl in resultsMetaLower:
                continue
            self.cbProperty.addItem(fn)
            self.cbStatisticsFor.addItem(fn)
        if self.cbProperty.count():
            self.updateConditions()
            self.updateValues()
        self.labelResults.setVisible(self.isResultsMode)
        self.lineResults.setVisible(self.isResultsMode)
        if self.isResultsMode:
            self.connectResultsDock()
            if self.resultsDock is None:
                self.fetchTimeFromLayer(layer)
                self.resultsDockPollTimer.start()
        else:
            self.resultsDockPollTimer.stop()
            self.disconnectResultsDock()

    def updateConditions(self):
        self.cbCondition.clear()
        prop = self.cbProperty.currentText()
        layer = self.resolveLayer()
        if not layer or not prop:
            return
        field = layer.fields().field(prop)
        cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')

        self.cbCondition.addItems(self.conditionsByType.get('numeric', [])) #all numeric for now

    def updateValues(self):
        ...
        # self.cbValue.clear()
        # prop = self.cbProperty.currentText()
        # layer = self.resolveLayer()
        # if not layer or not prop:
        #     return
        # field = layer.fields().field(prop)
        # cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
        # if cat == 'boolean':
        #     self.cbValue.addItems(['true','false'])
        # elif cat == 'numeric':
        #     mn, mx = self.getFieldMinMax(layer, prop)
        #     if mn is not None and mx is not None:
        #         interval = (mx - mn) / 5.0
        #         for i in range(5):
        #             start = mn + i*interval
        #             end   = mn + (i+1)*interval
        #             if i == 4:
        #                 end = mx
        #             self.cbValue.addItem(f"{start:.2f} - {end:.2f}")
        # else:
        #     vals = self.getUniqueFieldValues(layer, prop)
        #     for v in vals:
        #         if v is not None:
        #             self.cbValue.addItem(str(v))

    def getFieldMinMax(self, layer, name):
        mn = mx = None
        idx = layer.fields().indexFromName(name)
        if idx < 0:
            return None, None
        for f in layer.getFeatures():
            val = f[name]
            if val is not None:
                mn = mx = val
                break
        for f in layer.getFeatures():
            val = f[name]
            if val is not None:
                mn = min(mn, val)
                mx = max(mx, val)
        return mn, mx

    def getUniqueFieldValues(self, layer, name):
        vals = set()
        idx = layer.fields().indexFromName(name)
        if idx < 0:
            return []
        for f in layer.getFeatures():
            vals.add(f[name])
        return sorted(vals)

    def parseValue(self, txt):
        try:
            return int(txt)
        except ValueError:
            try:
                return float(txt)
            except ValueError:
                return txt

    def reloadCriteriaTable(self):
        tbl = self.tableWidgetCriteria
        # Ensure two columns: operator and criteria text
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["  Oper  ", "Criteria"])
        # One row per criterion
        tbl.setRowCount(len(self.criteria))
        tbl.verticalHeader().setVisible(True)

        for i, crit in enumerate(self.criteria):
            op = crit.get('operator', '+')
            enabled = crit.get('enabled', True)

            # Operator cell
            operItem = QTableWidgetItem(op)
            operItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            font = QFont()
            font.setPointSize(12)
            operItem.setFont(font)
            if op == '-':
                operItem.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            else:
                operItem.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)

            # Criteria text cell
            critText = f"{crit['property']} {crit['condition']} {crit['value']}"
            critItem = QTableWidgetItem(critText)
            critItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            critItem.setTextAlignment(Qt.AlignCenter)
            expr = self.buildExpression(crit)
            critItem.setData(Qt.UserRole, {'expression': expr, 'operator': op, 'enabled': enabled})

            # Grey out & strike-through if disabled
            if not enabled:
                for item in (operItem, critItem):
                    item.setForeground(QColor(Qt.gray))
                    f2 = item.font()
                    f2.setStrikeOut(True)
                    item.setFont(f2)

            tbl.setItem(i, 0, operItem)
            tbl.setItem(i, 1, critItem)

            # Label the row header (Cr1, Cr2...)
            label = f"Cr{i+1}"
            tbl.setVerticalHeaderItem(i, QTableWidgetItem(label))

        # Update state of buttons based on new selection / criteria
        self.updateButtonsState()


    def addCriterion(self, operator):
        prop    = self.cbProperty.currentText()
        cond    = self.cbCondition.currentText()
        val_txt = self.cbValue.value()
        if not prop or not cond or not val_txt:
            return
        val  = self.parseValue(val_txt)
        crit = {
            'property': prop,
            'condition': cond,
            'value':     val,
            'operator':  operator,
            'enabled':   True
        }
        if self.currentlyReplacingIndex is None:
            self.criteria.append(crit)
        else:
            # preserve the original operator (and enabled flag)
            old = self.criteria[self.currentlyReplacingIndex]
            crit['operator'] = old['operator']
            crit['enabled']  = old.get('enabled', True)
            self.criteria[self.currentlyReplacingIndex] = crit
            self.currentlyReplacingIndex = None
        self.reloadCriteriaTable()

    def replaceCriterion(self):
        row = self.tableWidgetCriteria.currentRow()
        if self.currentlyReplacingIndex is None:
            if row < 0:
                return
            crit = self.criteria[row]
            self.currentlyReplacingIndex = row
            self.cbProperty .setCurrentText(crit['property'])
            self.cbCondition.setCurrentText(crit['condition'])
            self.cbValue.setValue(str(crit['value']))
            self.btAdd.setEnabled(False)
            self.btSubtract.setEnabled(False)
            self.btClear.setEnabled(False)
            self.cbStatisticsFor.setEnabled(False)
        else:
            self.addCriterion(self.criteria[self.currentlyReplacingIndex]['operator'])

    def clearCriteria(self):
        self.criteria = []
        self.currentlyReplacingIndex = None
        self.lastCombinedExpression = ""
        self.reloadCriteriaTable()
        self.clearMapSelection()
        self.tableWidgetStatistics.setRowCount(0)

    def buildExpression(self, crit):
        fld  = f'"{crit["property"]}"'
        cond = crit['condition']
        op_map = {'=':'=', '≠':'<>', 'contains':' LIKE ', 'starts with':' LIKE ', 'ends with':' LIKE '}
        op   = op_map.get(cond, cond)
        val  = crit['value']
        if isinstance(val, str):
            if cond == 'contains':    val = f"'%{val}%'"
            elif cond == 'starts with': val = f"'{val}%'"
            elif cond == 'ends with':   val = f"'%{val}'"
            else:                       val = f"'{val}'"
        return f"{fld} {op} {val}"

    def runQuery(self):
        property = self.cbProperty.currentText()
        #self.labelStatisticsProperty.setText(property)
        self.labelStatisticsPropertyFor.setText(self.tr(f"Statistics of {property} for selected Elements"))
        self.calculateStatistics()

    def effectiveCriteria(self):
        if self.radioSingleCriteria.isChecked():
            prop = self.cbProperty.currentText()
            cond = self.cbCondition.currentText()
            val_txt = self.cbValue.value()
            if not prop or not cond or not val_txt:
                return []
            return [{
                'property': prop,
                'condition': cond,
                'value': self.parseValue(val_txt),
                'operator': '+',
                'enabled': True
            }]
        return self.criteria

    def calculateStatistics(self):
        selectedLayer = self.resolveLayer()
        if not selectedLayer:
            return

        # Clear previous layer's selection if the target layer changed
        if self.lastSelectedLayer is not None and self.lastSelectedLayer is not selectedLayer:
            try:
                if not sip.isdeleted(self.lastSelectedLayer):
                    self.lastSelectedLayer.removeSelection()
            except RuntimeError:
                pass

        targetField = self.cbStatisticsFor.currentText()
        if not targetField:
            return

        effectiveCriteria = self.effectiveCriteria()
        if not effectiveCriteria:
            return

        # Collect feature values per individual criterion
        statsPerCriterion = []
        for criterion in effectiveCriteria:
            if not criterion.get('enabled', True):
                continue

            filterExpression = self.buildExpression(criterion)
            featureRequest = QgsFeatureRequest().setFilterExpression(filterExpression)
            featureValues = [
                float(feat[targetField])
                for feat in selectedLayer.getFeatures(featureRequest)
                if feat[targetField] is not None
                and str(feat[targetField]) not in ('', 'NULL')
            ]
            statsPerCriterion.append(featureValues)

        # Build include/exclude expressions
        includeExpressions = [
            self.buildExpression(crit)
            for crit in effectiveCriteria
            if crit['operator'] == '+' and crit.get('enabled', True)
        ]
        excludeExpressions = [
            self.buildExpression(crit)
            for crit in effectiveCriteria
            if crit['operator'] == '-' and crit.get('enabled', True)
        ]
        inclusionExpressionString = ' OR '.join(includeExpressions)
        exclusionExpressionString = ' AND '.join(excludeExpressions)

        combinedExpression = ' AND '.join(filter(None, [
            inclusionExpressionString,
            f"NOT ({exclusionExpressionString})" if exclusionExpressionString else ''
        ]))
        self.lastCombinedExpression = combinedExpression
        self.highlightFeatures(selectedLayer, combinedExpression)

        allFeaturesRequest = QgsFeatureRequest().setFilterExpression(combinedExpression) if combinedExpression else QgsFeatureRequest()
        allFeatureValues = [
            float(feat[targetField])
            for feat in selectedLayer.getFeatures(allFeaturesRequest)
            if feat[targetField] is not None
            and str(feat[targetField]) not in ('', 'NULL')
        ]
        statsPerCriterion.append(allFeatureValues)

        # Helper to compute metrics
        def computeMetrics(values):
            count = len(values)
            totalValue = sum(values) if count else 0
            averageValue = totalValue / count if count else 0
            minValue = min(values) if count else None
            maxValue = max(values) if count else None
            return count, totalValue, averageValue, minValue, maxValue

        statsResults = [computeMetrics(vals) for vals in statsPerCriterion]

        # Populate the table
        statisticsTable = self.tableWidgetStatistics
        statisticsTable.setRowCount(len(statsResults))
        statisticsTable.verticalHeader().setVisible(True)

        for rowIndex, (count, totalValue, averageValue, minValue, maxValue) in enumerate(statsResults):
            for colIndex, value in enumerate((count, totalValue, averageValue, minValue, maxValue)):
                cellText = f"{value:.2f}" if isinstance(value, float) else str(value)
                tableItem = QTableWidgetItem(cellText)
                tableItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                statisticsTable.setItem(rowIndex, colIndex, tableItem)

            rowLabel = "All" if rowIndex == len(statsResults) - 1 else f"Cr{rowIndex+1}"
            statisticsTable.setVerticalHeaderItem(rowIndex, QTableWidgetItem(rowLabel))

        lastRow = statisticsTable.rowCount() - 1
        for col in range(statisticsTable.columnCount()):
            item = statisticsTable.item(lastRow, col)
            if item:
                item.setBackground(QColor(Qt.yellow))
        statisticsTable.verticalHeaderItem(lastRow).setBackground(QColor(Qt.yellow))


    def toggleEditCriterion(self):
        """Switch in and out of edit‐mode on the selected row."""
        if self.btCriteriaEdit.isChecked():
            self.startCriterionEdit()
        else:
            self.commitCriterionEdit()

    def startCriterionEdit(self):
        row = self.tableWidgetCriteria.currentRow()
        if row < 0:
            # nothing selected → cancel edit
            self.btCriteriaEdit.setChecked(False)
            return

        self.editingIndex = row
        crit = self.criteria[row]

        # load into the controls
        self.cbProperty.setCurrentText(crit['property'])
        self.updateConditions()
        self.cbCondition.setCurrentText(crit['condition'])
        self.updateValues()

        # cbValue may be a QLineEdit (QgsFilterLineEdit) or spinbox or combo:
        val = crit['value']
        if hasattr(self.cbValue, 'setText'):
            # line‐edit style
            self.cbValue.setText(str(val))
        else:
            # spinbox style
            try:
                self.cbValue.setValue(val)
            except Exception:
                # combo‐box fallback
                idx = self.cbValue.findText(str(val))
                if idx >= 0:
                    self.cbValue.setCurrentIndex(idx)

        # disable other actions while editing
        for btn in (
            self.btAdd,
            self.btSubtract,
            self.btCriteriaUp,
            self.btCriteriaDown,
            self.btCriteriaClear,
            self.btSubmit,
        ):
            btn.setEnabled(False)

    def commitCriterionEdit(self):
        # read back the controls
        prop = self.cbProperty.currentText()
        cond = self.cbCondition.currentText()

        if hasattr(self.cbValue, 'text'):
            val_txt = self.cbValue.text()
        else:
            try:
                val_txt = self.cbValue.value()
            except Exception:
                val_txt = self.cbValue.currentText()

        val = self.parseValue(val_txt)

        # preserve the original operator
        op = self.criteria[self.editingIndex]['operator']

        # overwrite the criterion
        self.criteria[self.editingIndex] = {
            'property': prop,
            'condition': cond,
            'value': val,
            'operator': op,
        }

        # reset edit state
        self.editingIndex = None
        self.btCriteriaEdit.setChecked(False)

        # re-enable buttons
        for btn in (
            self.btAdd,
            self.btSubtract,
            self.btCriteriaUp,
            self.btCriteriaDown,
            self.btCriteriaClear,
            self.btSubmit,
        ):
            btn.setEnabled(True)

        # refresh table (and Cr1, Cr2… headers)
        self.reloadCriteriaTable()

    def moveCriterionUp(self):
        row = self.tableWidgetCriteria.currentRow()
        if row > 0:
            self.criteria[row - 1], self.criteria[row] = (
                self.criteria[row],
                self.criteria[row - 1],
            )
            self.reloadCriteriaTable()
            self.tableWidgetCriteria.selectRow(row - 1)

    def moveCriterionDown(self):
        row = self.tableWidgetCriteria.currentRow()
        if 0 <= row < len(self.criteria) - 1:
            self.criteria[row], self.criteria[row + 1] = (
                self.criteria[row + 1],
                self.criteria[row],
            )
            self.reloadCriteriaTable()
            self.tableWidgetCriteria.selectRow(row + 1)

    def onCriteriaSelectionChanged(self, row, col):
        if row < 0 or row >= len(self.criteria):
            self.btCriteriaSwitch.setIcon(self.iconSwitchDisabled)
        else:
            enabled = self.criteria[row].get('enabled', True)
            self.btCriteriaSwitch.setIcon(
            self.iconSwitchEnabled  if enabled  else
            self.iconSwitchDisabled )

    def toggleCriterionEnabled(self):
        row = self.tableWidgetCriteria.currentRow()
        if not (0 <= row < len(self.criteria)):
            return

        crit = self.criteria[row]
        crit['enabled'] = not crit.get('enabled', True)

        is_enabled = crit['enabled']

        self.btCriteriaSwitch.setIcon(
            self.iconSwitchEnabled  if is_enabled  else
            self.iconSwitchDisabled
        )

        self.reloadCriteriaTable()

    # --- Results dock integration ---

    def isResultsDockAlive(self):
        return self.resultsDock is not None and not sip.isdeleted(self.resultsDock)

    def findResultsDock(self):
        from PyQt5.QtWidgets import QDockWidget as _QDW
        for widget in self.iface.mainWindow().findChildren(_QDW):
            if isinstance(widget, QGISRedResultsDock) and not sip.isdeleted(widget) and widget.isVisible():
                return widget
        return None

    def pollForResultsDock(self):
        if self.resultsDock is not None:
            return
        dock = self.findResultsDock()
        if dock is not None:
            self.connectResultsDock(dock)

    def syncResultsLabel(self, resultsDock):
        if sip.isdeleted(resultsDock):
            return
        if resultsDock._statsMode:
            self.onResultsStatisticsChanged(resultsDock._currentStat)
        else:
            timeText = resultsDock.lbTime.text()
            if timeText:
                self.onResultsTimeChanged(timeText)

    def connectResultsDock(self, resultsDock=None):
        if resultsDock is None:
            resultsDock = self.findResultsDock()
        if resultsDock is None:
            return
        if self.isResultsDockAlive() and self.resultsDock is resultsDock:
            self.syncResultsLabel(resultsDock)
            return
        if self.resultsDock is not None:
            self.disconnectResultsDock()
        self.resultsDock = resultsDock
        self.resultsDockPollTimer.stop()
        resultsDock.timeTextChanged.connect(self.onResultsTimeChanged)
        resultsDock.statisticsModeChanged.connect(self.onResultsStatisticsChanged)
        resultsDock.resultPropertyChanged.connect(self.onResultsPropertyChanged)
        resultsDock.visibilityChanged.connect(self.onResultsDockVisibilityChanged)
        self.syncResultsLabel(resultsDock)

    def disconnectResultsDock(self):
        if self.resultsDock is not None:
            if not sip.isdeleted(self.resultsDock):
                try:
                    self.resultsDock.timeTextChanged.disconnect(self.onResultsTimeChanged)
                except (TypeError, RuntimeError):
                    pass
                try:
                    self.resultsDock.statisticsModeChanged.disconnect(self.onResultsStatisticsChanged)
                except (TypeError, RuntimeError):
                    pass
                try:
                    self.resultsDock.resultPropertyChanged.disconnect(self.onResultsPropertyChanged)
                except (TypeError, RuntimeError):
                    pass
                try:
                    self.resultsDock.visibilityChanged.disconnect(self.onResultsDockVisibilityChanged)
                except (TypeError, RuntimeError):
                    pass
            self.resultsDock = None
        self.currentResultsStatText = ""
        # Fall back to layer time instead of clearing
        layer = self.resolveLayer()
        if layer and self.isResultsLayer(layer):
            self.fetchTimeFromLayer(layer)
            self.resultsDockPollTimer.start()
        else:
            self.currentResultsTimeText = ""
            self.labelResults.setText("")

    def onResultsTimeChanged(self, timeText):
        self.currentResultsTimeText = timeText
        self.labelResults.setText(timeText)
        if self.effectiveCriteria() and self.isResultsMode:
            self.runQuery()

    def onResultsStatisticsChanged(self, statName):
        self.currentResultsStatText = statName
        if statName:
            self.labelResults.setText(f"{statName} {self.tr('values for report times')}")
        else:
            self.labelResults.setText(self.currentResultsTimeText)
        if self.effectiveCriteria() and self.isResultsMode:
            self.runQuery()

    def onResultsPropertyChanged(self):
        self.reapplySelection()

    def reapplySelection(self):
        if not self.lastCombinedExpression or not self.isResultsMode:
            return
        selectedLayer = self.resolveLayer()
        if not selectedLayer:
            return
        self.highlightFeatures(selectedLayer, self.lastCombinedExpression)

    def onResultsDockVisibilityChanged(self, visible):
        if not self.isResultsDockAlive():
            self.disconnectResultsDock()
            return
        if not visible:
            self.resultsDockVisibilityTimer.start()
            return
        self.resultsDockVisibilityTimer.stop()
        timeText = self.resultsDock.lbTime.text()
        if timeText:
            self.onResultsTimeChanged(timeText)

    def checkResultsDockClosed(self):
        if not self.isResultsDockAlive():
            self.disconnectResultsDock()
        elif not self.resultsDock.isVisible():
            self.disconnectResultsDock()

    def fetchTimeFromLayer(self, layer):
        if layer is None or sip.isdeleted(layer):
            return
        stat_idx = layer.fields().indexFromName("Statistics")
        time_idx = layer.fields().indexFromName("Time")
        if stat_idx < 0 and time_idx < 0:
            return
        for feat in layer.getFeatures():
            stat_val = feat.attribute(stat_idx) if stat_idx >= 0 else None
            time_val = feat.attribute(time_idx) if time_idx >= 0 else None
            if stat_val and str(stat_val).strip():
                self.currentResultsStatText = str(stat_val)
                self.labelResults.setText(f"{stat_val} {self.tr('values for report times')}")
                return
            if time_val and str(time_val).strip():
                self.currentResultsTimeText = str(time_val)
                self.currentResultsStatText = ""
                self.labelResults.setText(self.currentResultsTimeText)
                return

    # --- Export ---

    def exportTableWidgetCsv(self, table, prefix):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            str(QgsProject.instance().homePath())
        )
        if not folder:
            return

        # 2) build filename
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = os.path.join(folder, f"{prefix}_{ts}.csv")

        try:
            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = [
                    table.horizontalHeaderItem(col).text()
                        if table.horizontalHeaderItem(col) else ''
                    for col in range(table.columnCount())
               ]
                writer.writerow(headers)

                for row in range(table.rowCount()):
                    rowdata = [
                        table.item(row, col).text()
                            if table.item(row, col) else ''
                        for col in range(table.columnCount())
                    ]
                    writer.writerow(rowdata)

            QMessageBox.information(self, "Export successful", f"Saved to:\n{fname}")
        except Exception as e:
            QMessageBox.critical(self, "Export failed", str(e))

    def exportCriteria(self):
        self.exportTableWidgetCsv(self.tableWidgetCriteria, "QGISRed_Criterias")

    def exportStatistics(self):
        self.exportTableWidgetCsv(self.tableWidgetStatistics, "QGISRed_Statistics")
