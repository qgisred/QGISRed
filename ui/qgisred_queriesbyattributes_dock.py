# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QFont  
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest
import os
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime
import csv

from ..tools.qgisred_utils import QGISRedUtils

# load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),"qgisred_queriesbyattributes_dock.ui"))

class QGISRedQueriesByAttributesDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(QGISRedQueriesByAttributesDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.initializeQueriesByAttributes()

    def initializeQueriesByAttributes(self):
        self.criteria = []
        self.currentlyReplacingIndex = None

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


    def setupButtonIcons(self): #TODO rename to QGISRed folder instead of BID on deploy
        self.btImport.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsImport.png"))
        self.btExport.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsExport.png"))

        self.btCriteriaUp.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsArrowUp.png"))
        self.btCriteriaDown.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsArrowDown.png"))
        self.btCriteriaClear.setIcon(QIcon(":/plugins/QGISRed-BID-BID/images/iconStatisticsDelete.png"))
        self.btCriteriaEdit.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsEdit.png"))

        self.iconSwitchEnabled  = QIcon(":/plugins/QGISRed-BID/images/iconSwitchEnabled.png")
        self.iconSwitchDisabled = QIcon(":/plugins/QGISRed-BID/images/iconSwitchDisabled.png")

        self.btCriteriaSwitch.setIcon(self.iconSwitchEnabled)

        self.btExcel.setIcon(QIcon(":/plugins/QGISRed-BID/images/iconStatisticsExcel.png"))

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

        # export
        self.btExport.clicked.connect(self.exportCriteria)
        self.btExcel.clicked.connect(self.exportStatistics)

        # stats property change
        self.cbStatisticsFor.currentIndexChanged.connect(self.onStatisticsForChanged)
        # initial button state
        self.updateButtonsState()

    def onStatisticsForChanged(self):
        if self.cbStatisticsFor.isEnabled():
            self.calculateStatistics()

    def initializeElementTypes(self):
        self.cbElementType.clear()
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputsGroup:
            checkedLayers = inputsGroup.checkedLayers()
            for element, identifier in self.elementIdentifiers.items():
                for layer in checkedLayers:
                    if layer and layer.customProperty("qgisred_identifier") == identifier:
                        self.cbElementType.addItem(layer.name(), layer)
        self.updateProperties()

    def updateButtonsState(self):
        has = len(self.criteria) > 0
        sel = self.tableWidgetCriteria.currentRow() >= 0
        self.btSubtract.setEnabled(has)
        self.btReplace.setEnabled(has and sel)
        self.btClear.setEnabled(has)
        self.btSubmit.setEnabled(has)
        self.cbElementType.setEnabled(not has)
        self.cbStatisticsFor.setEnabled(has)

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

    def updateProperties(self):
        layer = self.cbElementType.currentData(Qt.UserRole)
        if not layer:
            return
        self.cbProperty.clear()
        self.cbStatisticsFor.clear()
        #self.cbStatisticsFor.addItem("")
        for field in layer.fields():
            fn = field.name()
            if fn.lower() not in ('id','descrip'):
                self.cbProperty.addItem(fn)
                self.cbStatisticsFor.addItem(fn)
        if self.cbProperty.count():
            self.updateConditions()
            self.updateValues()

    def updateConditions(self):
        self.cbCondition.clear()
        prop = self.cbProperty.currentText()
        layer = self.cbElementType.currentData(Qt.UserRole)
        if not layer or not prop:
            return
        field = layer.fields().field(prop)
        cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
        
        self.cbCondition.addItems(self.conditionsByType.get('numeric', [])) #all numeric for now

    def updateValues(self):
        ...
        # self.cbValue.clear()
        # prop = self.cbProperty.currentText()
        # layer = self.cbElementType.currentData(Qt.UserRole)
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
        self.reloadCriteriaTable()
        layer = self.cbElementType.currentData(Qt.UserRole)
        if layer:
            layer.removeSelection()
        self.tableWidgetStatistics.setRowCount(0)

    def buildExpression(self, crit):
        fld  = f'"{crit["property"]}"'
        cond = crit['condition']
        op_map = {'=':'=', '≠':'<>', 'contains':' LIKE ', 'starts \with':' LIKE ', 'ends with':' LIKE '}
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

    def calculateStatistics(self):
        selectedLayer = self.cbElementType.currentData(Qt.UserRole)
        if not selectedLayer:
            return

        targetField = self.cbStatisticsFor.currentText()
        if not targetField:
            return

        # Collect feature values per individual criterion
        statsPerCriterion = []
        for criterion in self.criteria:
            if not criterion.get('enabled', True):
                continue

            filterExpression = self.buildExpression(criterion)
            featureRequest = QgsFeatureRequest().setFilterExpression(filterExpression)
            featureValues = [
                feat[targetField]
                for feat in selectedLayer.getFeatures(featureRequest)
                if feat[targetField] is not None
            ]
            statsPerCriterion.append(featureValues)

        # Build include/exclude expressions
        includeExpressions = [
            self.buildExpression(crit)
            for crit in self.criteria
            if crit['operator'] == '+'
        ]
        excludeExpressions = [
            self.buildExpression(crit)
            for crit in self.criteria
            if crit['operator'] == '-'
        ]
        inclusionExpressionString = ' OR '.join(includeExpressions)
        exclusionExpressionString = ' AND '.join(excludeExpressions)

        combinedExpression = ' AND '.join(filter(None, [
            inclusionExpressionString,
            f"NOT ({exclusionExpressionString})" if exclusionExpressionString else ''
        ]))
        allFeaturesRequest = QgsFeatureRequest().setFilterExpression(combinedExpression)
        allFeatureValues = [
            feat[targetField]
            for feat in selectedLayer.getFeatures(allFeaturesRequest)
            if feat[targetField] is not None
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