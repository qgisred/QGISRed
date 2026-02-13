# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest
import os

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
        # storage for user-defined criteria
        self.criteria = []
        self.currentlyReplacingIndex = None

        # map element names to identifiers
        self.elementIdentifiers = {
            'Pipes': 'qgisred_pipes',
            'Junctions': 'qgisred_junctions',
            'Multiple Demands': 'qgisred_demands',
            'Reservoirs': 'qgisred_reservoirs',
            'Tanks': 'qgisred_tanks',
            'Pumps': 'qgisred_pumps',
            'Valves': 'qgisred_valves',
            'Sources': 'qgisred_sources',
            'Service Connections': 'qgisred_serviceconnections',
            'Isolation Valves': 'qgisred_isolationvalves',
            'Meters': 'qgisred_meters'
        }

        # condition types by field category
        self.conditionsByType = {
            'numeric': ['=', '>', '<'], #'>=', '<=', '≠'],
            'text': ['=', '≠', 'contains', 'starts with', 'ends with'],
            'date': ['=', '>', '<', '>=', '<=', '≠'],
            'boolean': ['is true', 'is false']
        }

        # QGIS field type to our categories
        self.fieldTypeMapping = {
            'int': 'numeric',
            'double': 'numeric',
            'string': 'text',
            'date': 'date',
            'datetime': 'date',
            'time': 'date',
            'bool': 'boolean'
        }

        # set up criteria table
        if self.tableWidgetCriteria.columnCount() == 0:
            self.tableWidgetCriteria.setColumnCount(1)
            self.tableWidgetCriteria.setHorizontalHeaderLabels(["Query Conditions"])
            self.tableWidgetCriteria.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # set up statistics table
        if self.tableWidgetStatistics.columnCount() == 0:
            self.tableWidgetStatistics.setColumnCount(5)
            self.tableWidgetStatistics.setHorizontalHeaderLabels(["Count","Sum","Avg","Min","Max"])
            for i in range(5):
                self.tableWidgetStatistics.horizontalHeader().setSectionResizeMode(i, QHeaderView.Stretch)

        self.initializeElementTypes()
        self.setupConnections()

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
        # stats property change
        self.cbStatisticsFor.currentIndexChanged.connect(self.calculateStatistics)
        # initial button state
        self.updateButtonsState()

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

    def updateProperties(self):
        layer = self.cbElementType.currentData(Qt.UserRole)
        if not layer:
            return
        self.cbProperty.clear()
        for field in layer.fields():
            fn = field.name()
            if fn.lower() not in ('id','descrip'):
                self.cbProperty.addItem(fn)
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
        self.cbValue.clear()
        prop = self.cbProperty.currentText()
        layer = self.cbElementType.currentData(Qt.UserRole)
        if not layer or not prop:
            return
        field = layer.fields().field(prop)
        cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
        if cat == 'boolean':
            self.cbValue.addItems(['true','false'])
        elif cat == 'numeric':
            mn, mx = self.getFieldMinMax(layer, prop)
            if mn is not None and mx is not None:
                interval = (mx - mn) / 5.0
                for i in range(5):
                    start = mn + i*interval
                    end   = mn + (i+1)*interval
                    if i == 4:
                        end = mx
                    self.cbValue.addItem(f"{start:.2f} - {end:.2f}")
        else:
            vals = self.getUniqueFieldValues(layer, prop)
            for v in vals:
                if v is not None:
                    self.cbValue.addItem(str(v))

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
        tbl.setRowCount(0)
        for i, c in enumerate(self.criteria):
            op  = c.get('operator', '+')
            txt = f"{op} {c['property']} {c['condition']} {c['value']}"
            item = QTableWidgetItem(txt)
            item.setTextAlignment(Qt.AlignCenter)
            tbl.insertRow(i)
            tbl.setItem(i, 0, item)
        self.updateButtonsState()

    def addCriterion(self, operator):
        prop    = self.cbProperty.currentText()
        cond    = self.cbCondition.currentText()
        val_txt = self.cbValue.currentText()
        if not prop or not cond or not val_txt:
            return
        val  = self.parseValue(val_txt)
        crit = {'property': prop, 'condition': cond, 'value': val, 'operator': operator}
        if self.currentlyReplacingIndex is None:
            self.criteria.append(crit)
        else:
            op = self.criteria[self.currentlyReplacingIndex]['operator']
            crit['operator'] = op
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
            self.cbValue.setCurrentText(str(crit['value']))
            self.btAdd.setEnabled(False)
            self.btSubtract.setEnabled(False)
            self.btClear.setEnabled(False)
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
        ...

    def calculateStatistics(self):
        ...

    def closeEvent(self, event):
        self.clearCriteria()
        layer = self.cbElementType.currentData(Qt.UserRole)
        if layer:
            layer.removeSelection()
        super(QGISRedQueriesByAttributesDock, self).closeEvent(event)
