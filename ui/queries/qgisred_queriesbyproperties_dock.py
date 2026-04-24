# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDockWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QToolButton, QComboBox, QStackedWidget, QLabel
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QBrush, QColor, QIcon, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsFeatureRequest
from qgis.gui import QgsHighlight
import os
from ...compat import sip
from qgis.PyQt.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime
import csv
import math

from ..analysis.qgisred_results_dock import QGISRedResultsDock
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils

# load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),"qgisred_queriesbyproperties_dock.ui"))

class QGISRedQueriesByPropertiesDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(QGISRedQueriesByPropertiesDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.initializeQueriesByProperties()

    def closeEvent(self, event):
        self.resultsDockVisibilityTimer.stop()
        self.resultsDockPollTimer.stop()
        self.disconnectResultsDock()

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

        self.clearHighlights()
        self.clearMapSelection()
        self.lastCombinedExpression = ""
        super().closeEvent(event)

    def hideEvent(self, event):
        self.clearHighlights()
        super().hideEvent(event)

    def clearHighlights(self):
        for h in self.queryHighlights:
            self.canvas.scene().removeItem(h)
        self.queryHighlights.clear()

    def highlightFeatures(self, layer, expression):
        self.clearHighlights()
        if expression:
            featureReq = QgsFeatureRequest().setFilterExpression(expression)
            for feat in layer.getFeatures(featureReq):
                h = QgsHighlight(self.canvas, feat.geometry(), layer)
                h.setColor(QColor("magenta"))
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

    def initializeQueriesByProperties(self):
        self.criteria = []
        self.isResultsMode = False
        self.resultsDock = None
        self.currentResultsTimeText = ""
        self.currentResultsStatText = ""
        self.lastSelectedLayer = None
        self.lastCombinedExpression = ""
        self.queryHighlights = []
        self.queryHasBeenSubmitted = False

        self.resultsDockVisibilityTimer = QTimer()
        self.resultsDockVisibilityTimer.setSingleShot(True)
        self.resultsDockVisibilityTimer.setInterval(150)
        self.resultsDockVisibilityTimer.timeout.connect(self.checkResultsDockClosed)

        self.resultsDockPollTimer = QTimer()
        self.resultsDockPollTimer.setInterval(1500)
        self.resultsDockPollTimer.timeout.connect(self.pollForResultsDock)

        self.connectedLayerNodes = []
        self.connectedGroups = []

        self.layerTreeChangeTimer = QTimer()
        self.layerTreeChangeTimer.setSingleShot(True)
        self.layerTreeChangeTimer.setInterval(100)
        self.layerTreeChangeTimer.timeout.connect(self.doLayerTreeChanged)

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

        self.digitalTwinIdentifiers = {
            'qgisred_serviceconnections', 'qgisred_isolationvalves', 'qgisred_meters'
        }

        self.elementResultCategory = {
            'qgisred_junctions': 'Node',
            'qgisred_reservoirs': 'Node',
            'qgisred_tanks': 'Node',
            'qgisred_demands': 'Node',
            'qgisred_sources': 'Node',
            'qgisred_pipes': 'Link',
            'qgisred_pumps': 'Link',
            'qgisred_valves': 'Link',
        }

        self.nodeResultProperties = ['Pressure', 'Head', 'Demand', 'Quality']
        self.linkResultProperties = ['Flow', 'Velocity', 'HeadLoss', 'UnitHdLoss', 'FricFactor', 'ReactRate', 'Quality']

        self.conditionsByType = {
            'numeric': ['All', '>=', '<=', '=', '>', '<', '≠'],
            'listed': ['All', '='],
            'text': ['All', '=', '≠', 'ILIKE', 'NOT ILIKE', 'LIKE', 'NOT LIKE']
        }

        self.defaultProperties = {
            'Nodes': ['Pressure'],
            'Links': ['Flow'],
            'qgisred_pipes': ['Flow', 'Diameter'],
            'qgisred_valves': ['Flow', 'Diameter'],
            'qgisred_pumps': ['Flow', 'IdHFCurve'],
            'qgisred_junctions': ['Pressure', 'BaseDem'],
            'qgisred_tanks': ['Pressure', 'Elevation'],
            'qgisred_reservoirs': ['Pressure', 'TotalHead'],
            'qgisred_demands': ['BaseValue', 'Pressure'],
            'qgisred_sources': ['Quality', 'Pressure', 'BaseValue'],
            'qgisred_serviceconnections': ['BaseDemand'],
            'qgisred_isolationvalves': ['Status'],
            'qgisred_meters': ['Type'],
        }

        self.fieldTypeMapping = {
            'int': 'numeric',
            'integer': 'numeric',
            'integer64': 'numeric',
            'double': 'numeric',
            'real': 'numeric',
            'long': 'numeric',
            'string': 'text',
            'date': 'numeric',
            'datetime': 'numeric',
            'time': 'numeric',
            'bool': 'listed',
            'boolean': 'listed'
        }

        self.suppressUnitProperties = {
            ('qgisred_valves', 'Setting'),
            ('qgisred_sources', 'BaseValue'),
            ('qgisred_demands', 'BaseValue'),
        }

        self.enumeratedFields = {'IsActive', 'Available'}

        self.tableWidgetCriteria.setColumnCount(2)
        self.tableWidgetCriteria.setHorizontalHeaderLabels(["   Oper   ", "Criteria"])
        self.tableWidgetCriteria.verticalHeader().setVisible(False)
        h = self.tableWidgetCriteria.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.multipleCriteriaComment.setPlaceholderText(self.tr("Optional comment for this set of criteria"))
        self.multipleCriteriaComment.setMaxLength(128)

        # set up statistics table (columns configured dynamically in calculateStatistics)
        # Start empty state at half default height; grows to fit content later
        rowH = self.tableWidgetStatistics.verticalHeader().defaultSectionSize()
        headerH = self.tableWidgetStatistics.horizontalHeader().height()
        self.tableWidgetStatistics.setFixedHeight((headerH + rowH * 2) // 2)

        self.criteria = []
        # track which row (if any) is being edited
        self.editingIndex = None

        self.gridLayout.setColumnStretch(0, 3)
        self.gridLayout.setColumnStretch(1, 2)
        self.gridLayout.setColumnStretch(2, 2)
        self.cbCondition.setMaximumWidth(100)

        for widget in (self.cbElementType, self.cbProperty, self.cbCondition,
                       self.cbValue, self.cbStatisticsFor):
            widget.setStyleSheet(
                "QComboBox { background-color: white; }"
                "QComboBox QAbstractItemView { background-color: white; selection-background-color: #3399ff; selection-color: white; }"
                "QLineEdit { background-color: white; }"
            )

        self.setupValueStack()

        self.initializeElementTypes()
        self.setupConnections()
        self.setupButtonIcons()
        self.mGroupBox.setCollapsed(False)
        self.frameMultipleCriteria.setVisible(False)
        self.multipleCriteriaComment.setVisible(False)
        f = self.radioSingleCriteria.font()
        f.setBold(True)
        self.radioSingleCriteria.setFont(f)
        self.labelStatisticsUnit.setVisible(False)
        self.labelStatisticsUnit.setMaximumWidth(50)
        self.updateProperties()


    def setupButtonIcons(self): #TODO rename to QGISRed folder instead of BID on deploy
        self.btImport.setIcon(QIcon(":/images/iconStatisticsImport.svg"))
        self.btImport.setToolTip(self.tr("Import criteria from file"))
        self.btExport.setIcon(QIcon(":/images/iconStatisticsExport.svg"))
        self.btExport.setToolTip(self.tr("Export criteria to file"))

        self.btCriteriaUp.setIcon(QIcon(":/images/iconStatisticsArrowUp.svg"))
        self.btCriteriaUp.setToolTip(self.tr("Move selected criterion up"))
        self.btCriteriaDown.setIcon(QIcon(":/images/iconStatisticsArrowDown.svg"))
        self.btCriteriaDown.setToolTip(self.tr("Move selected criterion down"))
        self.btCriteriaClear.setIcon(QIcon(":/images/iconStatisticsDelete.svg"))
        self.btCriteriaClear.setToolTip(self.tr("Delete selected criterion"))
        self.btCriteriaSwitch.setToolTip(self.tr("Enable/disable selected criterion"))
        self.btCriteriaEdit.setIcon(QIcon(":/images/iconStatisticsEdit.svg"))
        self.btCriteriaEdit.setToolTip(self.tr("Edit selected criterion"))
        self.btCommentCriteria.setIcon(QIcon(":/images/iconComment.svg"))
        self.btCommentCriteria.setToolTip(self.tr("Show/hide comment for this set of criteria"))
        self.btCommentCriteria.setCheckable(True)
        self.btCommentCriteria.toggled.connect(self.multipleCriteriaComment.setVisible)

        self.iconSwitchEnabled  = QIcon(":/images/iconSwitchEnabled.svg")
        self.iconSwitchDisabled = QIcon(":/images/iconSwitchDisabled.svg")

        self.btCriteriaSwitch.setIcon(self.iconSwitchEnabled)

        self.btExcel.setIcon(QIcon(":/images/iconStatisticsExcel.svg"))
        self.btExcel.setToolTip(self.tr("Export statistics to file"))

    def setupConnections(self):
        # element / property updates
        self.cbElementType.currentIndexChanged.connect(self.onElementTypeChanged)
        self.cbElementType.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbElementType))
        self.cbProperty.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbProperty))
        self.cbProperty.currentIndexChanged.connect(self.updateConditions)
        self.cbProperty.currentIndexChanged.connect(self.updateValues)
        self.cbProperty.currentIndexChanged.connect(self.updateValueUnitLabel)
        # main buttons
        self.btAdd.clicked.connect(lambda: self.addCriterion('+'))
        self.btSubtract.clicked.connect(lambda: self.addCriterion('-'))
        self.btReplace.clicked.connect(self.commitCriterionEdit)
        self.btClearQuery.clicked.connect(self.clearQuery)
        self.btSubmit.clicked.connect(self.runQuery)

        # criteria table buttons
        self.btCriteriaUp.clicked.connect(self.moveCriterionUp)
        self.btCriteriaDown.clicked.connect(self.moveCriterionDown)
        self.btCriteriaClear.clicked.connect(self.clearCriteriaItem)
        self.btCriteriaEdit.setCheckable(True)
        self.btCriteriaEdit.clicked.connect(self.toggleEditCriterion)
        self.btCriteriaSwitch.clicked.connect(self.toggleCriterionEnabled)
        self.tableWidgetCriteria.currentCellChanged.connect(self.onCriteriaSelectionChanged)
        self.tableWidgetCriteria.itemSelectionChanged.connect(self.updateButtonsState)

        # radio criteria mode
        self.radioMultipleCriteria.toggled.connect(self.toggleMultipleCriteria)

        # update submit state as user types in value field
        self.cbValue.textChanged.connect(lambda: self.updateButtonsState())
        self.cbValueList.currentTextChanged.connect(lambda: self.updateButtonsState())
        # update value field enabled state when condition changes
        self.cbCondition.currentIndexChanged.connect(self.onConditionChanged)
        self.cbCondition.currentIndexChanged.connect(self.updateValues)

        # import / export
        self.btImport.clicked.connect(self.importCriteria)
        self.btExport.clicked.connect(self.exportCriteria)
        self.btExcel.clicked.connect(self.exportStatistics)

        # stats property change
        self.cbStatisticsFor.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbStatisticsFor))
        self.cbStatisticsFor.currentIndexChanged.connect(self.onStatisticsForChanged)
        self.cbStatisticsFor.currentIndexChanged.connect(self.updateStatisticsUnitLabel)
        # initial button state
        self.updateButtonsState()

        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)

        root = project.layerTreeRoot()
        for groupName in ("Inputs", "Results"):
            group = root.findGroup(groupName)
            if group:
                self.connectGroupSignals(group)
                for layerNode in group.findLayers():
                    self.connectLayerSignals(layerNode)

    def safeDisconnect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

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
        except (RuntimeError, TypeError):
            pass

    def connectLayerSignals(self, layerNode):
        try:
            layerNode.nameChanged.connect(self.onLayerTreeChanged)
            layer = layerNode.layer()
            if layer:
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
            if layer:
                self.safeDisconnect(layer.dataChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureAdded, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureDeleted, self.onLayerTreeChanged)
                self.safeDisconnect(layer.attributeValueChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.committedAttributeValuesChanges, self.onLayerTreeChanged)
        except (RuntimeError, TypeError):
            pass

    def reconnectLayerSignals(self):
        for layerNode in self.connectedLayerNodes:
            self.disconnectLayerNode(layerNode)
        self.connectedLayerNodes.clear()
        for group in self.connectedGroups:
            self.disconnectGroupSignals(group)
        self.connectedGroups.clear()

        root = QgsProject.instance().layerTreeRoot()
        for groupName in ("Inputs", "Results"):
            group = root.findGroup(groupName)
            if group:
                self.connectGroupSignals(group)
                for layerNode in group.findLayers():
                    self.connectLayerSignals(layerNode)

    def onLayerTreeChanged(self, *args):
        self.layerTreeChangeTimer.start()

    def doLayerTreeChanged(self):
        state = self.saveCurrentQueryState()
        self.reconnectLayerSignals()

        self.cbElementType.blockSignals(True)
        self.cbProperty.blockSignals(True)
        self.cbCondition.blockSignals(True)
        self.cbValue.blockSignals(True)
        self.cbValueList.blockSignals(True)
        try:
            self.initializeElementTypes()
            self.restoreCurrentQueryState(state)
        finally:
            self.cbElementType.blockSignals(False)
            self.cbProperty.blockSignals(False)
            self.cbCondition.blockSignals(False)
            self.cbValue.blockSignals(False)
            self.cbValueList.blockSignals(False)

        self.updateConditions()
        self.updateValues()
        self.setCurrentValueText(state['valueText'])
        self.updateButtonsState()

    def onProjectChanged(self):
        self.criteria = []
        self.clearHighlights()
        self.clearMapSelection()
        self.lastCombinedExpression = ""
        self.queryHasBeenSubmitted = False
        self.tableWidgetStatistics.setRowCount(0)
        self.reloadCriteriaTable()
        self.onLayerTreeChanged()

    def saveCurrentQueryState(self):
        return {
            'elementType': self.cbElementType.currentData(Qt.ItemDataRole.UserRole),
            'property': self.getComboInternalName(self.cbProperty),
            'condition': self.cbCondition.currentText(),
            'valueText': self.currentValueText(),
        }

    def restoreCurrentQueryState(self, state):
        if state.get('elementType'):
            idx = self.findComboByInternalName(self.cbElementType, state['elementType'])
            if idx >= 0:
                self.cbElementType.setCurrentIndex(idx)
                self.updateProperties()
        if state.get('property'):
            idx = self.findComboByInternalName(self.cbProperty, state['property'])
            if idx >= 0:
                self.cbProperty.setCurrentIndex(idx)
        if state.get('condition'):
            idx = self.cbCondition.findText(state['condition'])
            if idx >= 0:
                self.cbCondition.setCurrentIndex(idx)

    def toggleMultipleCriteria(self, visible):
        if visible:
            # Single → Multiple: auto-add current fields as first criterion
            prop = self.getComboInternalName(self.cbProperty)
            cond = self.cbCondition.currentText()
            val_txt = self.currentValueText()
            if prop and cond and (val_txt or cond == 'All'):
                crit = {
                    'property': prop,
                    'condition': cond,
                    'value': self.parseValue(val_txt) if cond != 'All' else '',
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
                propIdx = self.findComboByInternalName(self.cbProperty, first['property'])
                if propIdx >= 0:
                    self.cbProperty.setCurrentIndex(propIdx)
                self.cbCondition.setCurrentText(first['condition'])
                self.setCurrentValueText(str(first['value']))
                self.criteria = []
                self.reloadCriteriaTable()

        self.frameMultipleCriteria.setVisible(visible)
        for radio in (self.radioSingleCriteria, self.radioMultipleCriteria):
            f = radio.font()
            f.setBold(radio.isChecked())
            radio.setFont(f)
        self.updateButtonsState()
        if self.queryHasBeenSubmitted and self.effectiveCriteria():
            self.runQuery()

    def onStatisticsForChanged(self):
        self.updateStatisticsTimeVisibility()
        if self.cbStatisticsFor.isEnabled() and self.lastCombinedExpression:
            self.calculateStatistics()

    def initializeElementTypes(self):
        self.cbElementType.clear()

        # Collect available input layers by identifier
        availableLayers = {}
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputsGroup:
            identifiers = set(self.elementIdentifiers.values())
            for layerNode in inputsGroup.findLayers():
                layer = layerNode.layer()
                if layer and layer.customProperty("qgisred_identifier") in identifiers:
                    availableLayers[layer.customProperty("qgisred_identifier")] = layer.name()

        # Collect results layers
        nodeIdent = linkIdent = None
        resultsGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
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

        # Results first (if they exist)
        if hasResults:
            resultsBrush = QBrush(QColor("#FFF8DC"))
            if nodeIdent:
                self.cbElementType.addItem(self.tr("Nodes"), nodeIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            if linkIdent:
                self.cbElementType.addItem(self.tr("Links"), linkIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            self.cbElementType.insertSeparator(self.cbElementType.count())

        # Input layers in fixed order
        inputOrder = [
            'qgisred_junctions', 'qgisred_tanks', 'qgisred_reservoirs',
            'qgisred_pipes', 'qgisred_valves', 'qgisred_pumps',
            'qgisred_demands', 'qgisred_sources'
        ]
        addedInput = False
        for ident in inputOrder:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)
                addedInput = True

        # Digital twin layers
        digitalTwinOrder = [
            'qgisred_serviceconnections', 'qgisred_isolationvalves', 'qgisred_meters'
        ]
        hasTwin = any(ident in availableLayers for ident in digitalTwinOrder)
        if addedInput and hasTwin:
            self.cbElementType.insertSeparator(self.cbElementType.count())
        for ident in digitalTwinOrder:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)

        self.updateProperties()
        self.updateComboBoxBackground(self.cbElementType)

    def isResultsLayer(self, layer):
        if not layer:
            return False
        ident = layer.customProperty("qgisred_identifier") or ""
        return ident.startswith("qgisred_node") or ident.startswith("qgisred_link")

    def getResultsExist(self):
        resultsGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if not resultsGroup:
            return False
        for layerNode in resultsGroup.findLayers():
            layer = layerNode.layer()
            if layer:
                return True
        return False

    def getVisibleLinkResultProperties(self):
        isStatsMode = self.isResultsDockAlive() and self.resultsDock._statsMode
        if not isStatsMode:
            return list(self.linkResultProperties)
        statName = self.resultsDock._currentStat if self.isResultsDockAlive() else ""
        averageLabel = self.resultsDock.lbl_average if self.isResultsDockAlive() else ""
        if statName == averageLabel:
            return ['Flow_Unsig' if p == 'Flow' else p for p in self.linkResultProperties]
        return list(self.linkResultProperties)

    def getResultProperties(self, layer, qrIdent):
        if self.isResultsMode:
            ident = layer.customProperty("qgisred_identifier") or ""
            isLink = ident.startswith("qgisred_link")
            if isLink:
                return self.getVisibleLinkResultProperties()
            return list(self.nodeResultProperties)
        if qrIdent not in self.digitalTwinIdentifiers and self.getResultsExist():
            resultCategory = self.elementResultCategory.get(qrIdent)
            if resultCategory == 'Link':
                return self.getVisibleLinkResultProperties()
            elif resultCategory == 'Node':
                return list(self.nodeResultProperties)
        return []

    def updateButtonsState(self):
        if self.editingIndex is not None:
            return
        isMultiple = self.radioMultipleCriteria.isChecked()
        if isMultiple:
            has = len(self.criteria) > 0
            row = self.tableWidgetCriteria.currentRow()
            sel = row >= 0 and bool(self.tableWidgetCriteria.selectedIndexes())
            self.btSubtract.setEnabled(has)
            self.btReplace.setEnabled(False)
            self.btSubmit.setEnabled(has)
            self.cbElementType.setEnabled(not has or self.isResultsMode)
            self.btCriteriaUp.setEnabled(sel and row > 0)
            self.btCriteriaDown.setEnabled(sel and row < len(self.criteria) - 1)
            self.btCriteriaClear.setEnabled(sel)
            self.btCriteriaEdit.setEnabled(sel)
            self.btCriteriaSwitch.setEnabled(sel)
        else:
            isAll = self.cbCondition.currentText() == 'All'
            hasValue = isAll or bool(self.currentValueText())
            self.btSubmit.setEnabled(hasValue)
            self.btReplace.setEnabled(False)
            self.cbElementType.setEnabled(True)
            self.btCriteriaUp.setEnabled(False)
            self.btCriteriaDown.setEnabled(False)
            self.btCriteriaClear.setEnabled(False)
            self.btCriteriaEdit.setEnabled(False)
            self.btCriteriaSwitch.setEnabled(False)
        self.btClearQuery.setVisible(True)
        hasStats = self.tableWidgetStatistics.rowCount() > 0
        hasValue = bool(self.currentValueText())
        hasCriteria = len(self.criteria) > 0
        self.btClearQuery.setEnabled(hasStats or hasValue or hasCriteria)
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
        if self.editingIndex is not None:
            self.editingIndex = None
            self.btCriteriaEdit.setChecked(False)

        self.reloadCriteriaTable()
        self.tableWidgetCriteria.clearSelection()

        if not self.criteria:
            self.lastCombinedExpression = ""
            self.clearMapSelection()
            self.tableWidgetStatistics.setRowCount(0)
        self.updateButtonsState()

    def resolveLayer(self):
        """Resolve the current qgisred_identifier from the combobox to a live QgsVectorLayer."""
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        if not qrIdent:
            return None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.customProperty("qgisred_identifier") == qrIdent:
                return layer
        return None

    def resolveResultsLayer(self, category):
        """Find the results layer (Node or Link) from the Results group."""
        prefix = "qgisred_node" if category == "Node" else "qgisred_link"
        resultsGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
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

    def resolveQueryLayer(self, prop):
        """Return the layer that actually contains the given property field."""
        layer = self.resolveLayer()
        if not layer:
            return None
        if layer.fields().indexFromName(prop) >= 0:
            return layer
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        resultCategory = self.elementResultCategory.get(qrIdent)
        if resultCategory and self.isResultProperty(prop):
            return self.resolveResultsLayer(resultCategory)
        return layer

    def onElementTypeChanged(self):
        hasActiveState = (
            self.lastCombinedExpression
            or self.tableWidgetStatistics.rowCount() > 0
            or self.criteria
            or bool(self.currentValueText())
        )
        if hasActiveState:
            self.lastCombinedExpression = ""
            self.setCurrentValueText('')
            self.criteria = []
            self.reloadCriteriaTable()
            self.clearHighlights()
            self.clearMapSelection()
            self.tableWidgetStatistics.setRowCount(0)
        self.queryHasBeenSubmitted = False
        self.updateProperties()

    def updateProperties(self):
        layer = self.resolveLayer()
        if not layer:
            return
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        self.isResultsMode = self.isResultsLayer(layer)
        self.cbProperty.clear()
        self.cbStatisticsFor.clear()
        resultsMetaLower = {'time', 'statistics', 'time_h', 'time_d', 'time_q', 'type'}
        resultsFieldsLower = {
            'flow', 'flow_unsig', 'flow_sig', 'velocity', 'headloss',
            'unithdloss', 'fricfactor', 'reactrate', 'quality',
            'pressure', 'head', 'demand', 'status'
        }
        idTagFieldsLower = {'id', 'tag', 'descrip'}
        idTagOrder = ['id', 'tag', 'descrip']

        staticFields = []
        idTagFieldsByKey = {}
        for field in layer.fields():
            fn = field.name()
            fnl = fn.lower()
            if self.isResultsMode and fnl in resultsMetaLower:
                continue
            if self.isResultsMode and fnl in resultsFieldsLower:
                continue
            if fnl in idTagFieldsLower:
                idTagFieldsByKey[fnl] = field
            else:
                staticFields.append(field)
        idTagFields = [idTagFieldsByKey[k] for k in idTagOrder if k in idTagFieldsByKey]

        resultsBrush = QBrush(QColor("#FFF8DC"))
        darkBrush = QBrush(QColor("#D8D8D8"))
        resultProps = self.getResultProperties(layer, qrIdent)
        fieldUtils = QGISRedFieldUtils()
        if not fieldUtils.showReactRate():
            resultProps = [p for p in resultProps if p != "ReactRate"]
        numericResultProps = [p for p in resultProps if p != 'Status']
        ident = layer.customProperty("qgisred_identifier") or ""
        if ident.startswith("qgisred_node"):
            resultCategory = "Nodes"
        elif ident.startswith("qgisred_link"):
            resultCategory = "Links"
        else:
            cat = self.elementResultCategory.get(qrIdent, "")
            resultCategory = "Nodes" if cat == "Node" else "Links"

        def addResultPropToCombo(combo, prop, brush=None):
            rawProp = "Flow" if prop == "Flow_Unsig" else prop
            prettyName = fieldUtils.getFieldPrettyName(resultCategory, rawProp)
            combo.addItem(prettyName)
            idx = combo.count() - 1
            combo.setItemData(idx, prop, Qt.ItemDataRole.UserRole)
            if brush:
                combo.setItemData(idx, brush, Qt.BackgroundRole)

        def addFieldToCombo(combo, fieldName, brush=None):
            prettyName = fieldUtils.getFieldPrettyName(qrIdent, fieldName)
            combo.addItem(prettyName)
            idx = combo.count() - 1
            combo.setItemData(idx, fieldName, Qt.ItemDataRole.UserRole)
            if brush:
                combo.setItemData(idx, brush, Qt.BackgroundRole)

        if not self.isResultsMode:
            if resultProps:
                for prop in resultProps:
                    addResultPropToCombo(self.cbProperty, prop, resultsBrush)
                if numericResultProps:
                    for prop in numericResultProps:
                        addResultPropToCombo(self.cbStatisticsFor, prop, resultsBrush)
                if idTagFields or staticFields:
                    self.cbProperty.insertSeparator(self.cbProperty.count())

            if idTagFields:
                for field in idTagFields:
                    addFieldToCombo(self.cbProperty, field.name(), darkBrush)
                if staticFields:
                    self.cbProperty.insertSeparator(self.cbProperty.count())

            for field in staticFields:
                addFieldToCombo(self.cbProperty, field.name())
                cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
                if cat == 'numeric':
                    addFieldToCombo(self.cbStatisticsFor, field.name())

            if numericResultProps and self.cbStatisticsFor.count() > len(numericResultProps):
                self.cbStatisticsFor.insertSeparator(len(numericResultProps))
        else:
            if idTagFields:
                for field in idTagFields:
                    addFieldToCombo(self.cbProperty, field.name(), darkBrush)
                if staticFields or resultProps:
                    self.cbProperty.insertSeparator(self.cbProperty.count())

            for field in staticFields:
                addFieldToCombo(self.cbProperty, field.name())
                cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
                if cat == 'numeric':
                    addFieldToCombo(self.cbStatisticsFor, field.name())

            if resultProps:
                self.cbProperty.insertSeparator(self.cbProperty.count())
                for prop in resultProps:
                    addResultPropToCombo(self.cbProperty, prop, resultsBrush)
                if numericResultProps:
                    if self.cbStatisticsFor.count() > 0:
                        self.cbStatisticsFor.insertSeparator(self.cbStatisticsFor.count())
                    for prop in numericResultProps:
                        addResultPropToCombo(self.cbStatisticsFor, prop, resultsBrush)

        if self.cbProperty.count():
            elementText = self.cbElementType.currentText()
            defaults = self.defaultProperties.get(elementText, self.defaultProperties.get(qrIdent, []))
            for defaultProp in defaults:
                idx = self.findComboByInternalName(self.cbProperty, defaultProp)
                if idx >= 0:
                    self.cbProperty.setCurrentIndex(idx)
                    break
            self.updateConditions()
            self.updateValues()
        if self.cbStatisticsFor.count() > 0:
            self.cbStatisticsFor.insertSeparator(self.cbStatisticsFor.count())
        self.cbStatisticsFor.addItem(self.tr("None"))
        self.cbStatisticsFor.setItemData(self.cbStatisticsFor.count() - 1, '_none_', Qt.ItemDataRole.UserRole)

        if self.cbStatisticsFor.count() > 0 and not self.cbStatisticsFor.currentText():
            for i in range(self.cbStatisticsFor.count()):
                if self.cbStatisticsFor.itemText(i):
                    self.cbStatisticsFor.setCurrentIndex(i)
                    break
        self.updateValueUnitLabel()
        self.updateStatisticsUnitLabel()
        self.updateComboBoxBackground(self.cbProperty)
        self.updateComboBoxBackground(self.cbStatisticsFor)

        hasResults = self.isResultsMode or (
            qrIdent not in self.digitalTwinIdentifiers
            and self.getResultsExist()
            and self.elementResultCategory.get(qrIdent) is not None
        )
        if hasResults:
            self.connectResultsDock()
            if self.resultsDock is None:
                if self.isResultsMode:
                    self.fetchTimeFromLayer(layer)
                else:
                    self.fetchTimeFromResultsLayer()
                self.resultsDockPollTimer.start()
        else:
            self.resultsDockPollTimer.stop()
            self.disconnectResultsDock()
        self.updateStatisticsTimeVisibility()

    def updateStatisticsTimeVisibility(self):
        prop = self.getComboInternalName(self.cbStatisticsFor)
        visible = self.isResultProperty(prop) if prop else False
        self.labelResults.setVisible(visible)
        self.lineResults.setVisible(visible)

    def getComboInternalName(self, combo):
        data = combo.currentData(Qt.ItemDataRole.UserRole)
        return data if data else combo.currentText()

    def findComboByInternalName(self, combo, internalName):
        for i in range(combo.count()):
            data = combo.itemData(i, Qt.ItemDataRole.UserRole)
            if data == internalName:
                return i
        return -1

    def isResultProperty(self, prop):
        return prop in self.nodeResultProperties or prop in self.linkResultProperties or prop == 'Flow_Unsig'

    def isNumericProperty(self, prop):
        if self.isResultProperty(prop):
            return prop != 'Status'
        layer = self.resolveLayer()
        if not layer:
            return False
        fieldIdx = layer.fields().indexFromName(prop)
        if fieldIdx < 0:
            return False
        cat = self.fieldTypeMapping.get(layer.fields().field(fieldIdx).typeName().lower(), 'text')
        return cat == 'numeric'

    def usesSumColumn(self, prop, qrIdent=''):
        if prop == 'Length' and qrIdent == 'qgisred_pipes':
            return True
        if prop == 'HeadLoss':
            cat = self.elementResultCategory.get(qrIdent)
            if cat == 'Link' or qrIdent.startswith('qgisred_link'):
                return True
        if prop == 'BaseDem' and qrIdent == 'qgisred_junctions':
            return True
        if prop == 'BaseValue' and qrIdent == 'qgisred_demands':
            return True
        if prop == 'Demand':
            cat = self.elementResultCategory.get(qrIdent)
            if cat == 'Node' or qrIdent.startswith('qgisred_node'):
                return True
        return False

    def setupValueStack(self):
        idx = self.gridLayout.indexOf(self.cbValue)
        row, col, rowSpan, colSpan = self.gridLayout.getItemPosition(idx)
        sizePolicy = self.cbValue.sizePolicy()

        self.cbValueList = QComboBox(self)
        self.cbValueList.setEditable(False)
        self.cbValueList.setSizePolicy(sizePolicy)
        self.cbValueList.setStyleSheet(
            "QComboBox { background-color: white; }"
            "QComboBox QAbstractItemView { background-color: white; selection-background-color: #3399ff; selection-color: white; }"
        )

        self.valueStack = QStackedWidget(self)
        self.valueStack.setSizePolicy(sizePolicy)
        self.gridLayout.removeWidget(self.cbValue)
        self.valueStack.addWidget(self.cbValue)
        self.valueStack.addWidget(self.cbValueList)
        self.gridLayout.addWidget(self.valueStack, row, col, rowSpan, colSpan)

        self.labelValueUnit = QLabel(self)
        self.labelValueUnit.setVisible(False)
        self.gridLayout.addWidget(self.labelValueUnit, row, col + colSpan)

    def updateComboBoxBackground(self, combo):
        brush = combo.currentData(Qt.BackgroundRole)
        if brush and isinstance(brush, QBrush) and brush.color() != QColor(0, 0, 0, 255):
            color = brush.color().name()
        else:
            color = "white"
        combo.setStyleSheet(
            f"QComboBox {{ background-color: {color}; }}"
            "QComboBox QAbstractItemView { background-color: white; selection-background-color: #3399ff; selection-color: white; }"
            "QLineEdit { background-color: white; }"
        )

    def isValueListActive(self):
        return self.valueStack.currentWidget() is self.cbValueList

    def currentValueText(self):
        if self.isValueListActive():
            return self.cbValueList.currentText()
        return self.cbValue.value()

    def setCurrentValueText(self, text):
        text = '' if text is None else str(text)
        if self.isValueListActive():
            i = self.cbValueList.findText(text)
            if i >= 0:
                self.cbValueList.setCurrentIndex(i)
            else:
                self.cbValueList.setCurrentIndex(0)
        self.cbValue.setValue(text)

    def updateConditions(self):
        self.cbCondition.blockSignals(True)
        self.cbCondition.clear()
        prop = self.getComboInternalName(self.cbProperty)
        layer = self.resolveLayer()
        if not layer or not prop:
            self.cbCondition.blockSignals(False)
            return
        fieldIdx = layer.fields().indexFromName(prop)
        if fieldIdx >= 0:
            field = layer.fields().field(fieldIdx)
            cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
        elif self.isResultProperty(prop):
            cat = 'numeric' if prop != 'Status' else 'listed'
        else:
            cat = 'text'
        if prop in self.enumeratedFields:
            cat = 'listed'

        self.cbCondition.addItems(self.conditionsByType.get(cat, self.conditionsByType['text']))

        if cat == 'numeric':
            idx = self.cbCondition.findText('<=')
            if idx >= 0:
                self.cbCondition.setCurrentIndex(idx)
        elif cat == 'text':
            freeTextFields = {'Id', 'Descrip', 'InstalDate', 'InstDate',
                              'Time', 'Time_H', 'Time_Q', 'Time_D'}
            defaultCond = 'ILIKE' if prop in freeTextFields else '='
            idx = self.cbCondition.findText(defaultCond)
            if idx >= 0:
                self.cbCondition.setCurrentIndex(idx)
        self.cbCondition.blockSignals(False)
        self.onConditionChanged()

    def onConditionChanged(self):
        isAll = self.cbCondition.currentText() == 'All'
        self.cbValue.setEnabled(not isAll)
        self.cbValueList.setEnabled(not isAll)
        if isAll:
            self.setCurrentValueText('')
        self.updateButtonsState()

    def updateValues(self):
        prop = self.getComboInternalName(self.cbProperty)
        cond = self.cbCondition.currentText()

        self.cbValue.setCompleter(None)

        useList = False
        strVals = []
        if cond in ('=', '≠'):
            layer = self.resolveQueryLayer(prop)
            if layer:
                fieldIdx = layer.fields().indexFromName(prop)
                if fieldIdx >= 0:
                    field = layer.fields().field(fieldIdx)
                    cat = self.fieldTypeMapping.get(field.typeName().lower(), 'text')
                    if prop in self.enumeratedFields:
                        cat = 'listed'
                    freeTextFields = {'Id', 'Descrip', 'InstalDate', 'InstDate',
                                       'Time', 'Time_H', 'Time_Q', 'Time_D'}
                    if (cat == 'text' and prop not in freeTextFields) or cat == 'listed':
                        uniqueVals = self.getUniqueFieldValues(layer, prop)
                        strVals = sorted({str(v) for v in uniqueVals if v is not None and str(v).strip()})
                        useList = bool(strVals)

        if useList:
            previous = self.cbValueList.currentText() if self.isValueListActive() else self.cbValue.value()
            self.cbValueList.blockSignals(True)
            self.cbValueList.clear()
            self.cbValueList.addItem('')
            self.cbValueList.addItems(strVals)
            i = self.cbValueList.findText(previous)
            self.cbValueList.setCurrentIndex(i if i >= 0 else 0)
            self.cbValueList.blockSignals(False)
            self.valueStack.setCurrentWidget(self.cbValueList)
        else:
            self.valueStack.setCurrentWidget(self.cbValue)

    def updateValueUnitLabel(self):
        prop = self.getComboInternalName(self.cbProperty)
        if not prop:
            self.labelValueUnit.setVisible(False)
            return
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        fieldUtils = QGISRedFieldUtils()
        unit = ""
        if self.isResultProperty(prop):
            category = self.elementResultCategory.get(qrIdent)
            if self.isResultsMode:
                layer = self.resolveLayer()
                ident = (layer.customProperty("qgisred_identifier") or "") if layer else ""
                category = "Link" if ident.startswith("qgisred_link") else "Node"
            if category:
                unit = fieldUtils.getResultPropertyUnit(category, prop)
        else:
            unit = fieldUtils.getFieldUnit(qrIdent, prop)
        if (qrIdent, prop) in self.suppressUnitProperties:
            unit = ""
        if unit:
            self.labelValueUnit.setText(f"{unit}")
            self.labelValueUnit.setVisible(True)
        else:
            self.labelValueUnit.setVisible(False)

    def updateStatisticsUnitLabel(self):
        prop = self.getComboInternalName(self.cbStatisticsFor)
        if not prop:
            self.labelStatisticsUnit.setVisible(False)
            return
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        fieldUtils = QGISRedFieldUtils()
        unit = ""
        if self.isResultProperty(prop):
            category = self.elementResultCategory.get(qrIdent)
            if self.isResultsMode:
                layer = self.resolveLayer()
                ident = (layer.customProperty("qgisred_identifier") or "") if layer else ""
                category = "Link" if ident.startswith("qgisred_link") else "Node"
            if category:
                unit = fieldUtils.getResultPropertyUnit(category, prop)
        else:
            unit = fieldUtils.getFieldUnit(qrIdent, prop)
        if (qrIdent, prop) in self.suppressUnitProperties:
            unit = ""
        if unit:
            metrics = self.labelStatisticsUnit.fontMetrics()
            elided = metrics.elidedText(unit, Qt.TextElideMode.ElideRight, self.labelStatisticsUnit.maximumWidth())
            self.labelStatisticsUnit.setText(elided)
            self.labelStatisticsUnit.setToolTip(unit)
            self.labelStatisticsUnit.setVisible(True)
        else:
            self.labelStatisticsUnit.setToolTip("")
            self.labelStatisticsUnit.setVisible(False)

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

        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        fieldUtils = QGISRedFieldUtils()
        for i, crit in enumerate(self.criteria):
            op = crit.get('operator', '+')
            enabled = crit.get('enabled', True)

            # Operator cell
            operItem = QTableWidgetItem(op)
            operItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            font = QFont()
            font.setPointSize(12)
            operItem.setFont(font)
            if op == '-':
                operItem.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                operItem.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            # Criteria text cell
            rawProp = "Flow" if crit['property'] == "Flow_Unsig" else crit['property']
            displayProp = fieldUtils.getFieldPrettyName(qrIdent, rawProp)
            critText = f"{displayProp} {crit['condition']} {crit['value']}"
            critItem = QTableWidgetItem(critText)
            critItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            critItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            expr = self.buildExpression(crit)
            critItem.setData(Qt.ItemDataRole.UserRole, {'expression': expr, 'operator': op, 'enabled': enabled})

            # Grey out & strike-through if disabled
            if not enabled:
                for item in (operItem, critItem):
                    item.setForeground(QColor(Qt.GlobalColor.gray))
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
        prop    = self.getComboInternalName(self.cbProperty)
        cond    = self.cbCondition.currentText()
        val_txt = self.currentValueText()
        if not prop or not cond:
            return
        if cond != 'All' and not val_txt:
            return
        val  = self.parseValue(val_txt) if cond != 'All' else ''
        crit = {
            'property': prop,
            'condition': cond,
            'value':     val,
            'operator':  operator,
            'enabled':   True
        }
        self.criteria.append(crit)
        self.reloadCriteriaTable()

    def clearQuery(self):
        self.setCurrentValueText('')
        self.lastCombinedExpression = ""
        self.queryHasBeenSubmitted = False
        self.clearHighlights()
        self.clearMapSelection()
        self.tableWidgetStatistics.setRowCount(0)
        if self.radioMultipleCriteria.isChecked():
            self.clearCriteria()
        self.updateButtonsState()

    def clearCriteria(self):
        self.criteria = []
        self.lastCombinedExpression = ""
        self.reloadCriteriaTable()
        self.clearMapSelection()
        self.tableWidgetStatistics.setRowCount(0)

    def buildExpression(self, crit):
        cond = crit['condition']
        if cond == 'All':
            return '1=1'
        fld  = f'"{crit["property"]}"'
        op_map = {'=':'=', '≠':'<>', 'LIKE':' LIKE ', 'NOT LIKE':' NOT LIKE ',
                  'ILIKE':' ILIKE ', 'NOT ILIKE':' NOT ILIKE ',
                  'contains':' LIKE ', 'starts with':' LIKE ', 'ends with':' LIKE '}
        op   = op_map.get(cond, cond)
        val  = crit['value']
        isTextComparison = isinstance(val, str)
        isCaseInsensitive = cond in ('ILIKE', 'NOT ILIKE')
        if isTextComparison:
            if cond in ('LIKE', 'NOT LIKE', 'ILIKE', 'NOT ILIKE', 'contains'):
                val = f"'%{val}%'"
            elif cond == 'starts with': val = f"'{val}%'"
            elif cond == 'ends with':   val = f"'%{val}'"
            else:                       val = f"'{val}'"
        if isTextComparison and not isCaseInsensitive:
            return f"lower({fld}) {op} lower({val})"
        return f"{fld} {op} {val}"

    def buildIdFilter(self, inputLayer):
        ids = []
        for feat in inputLayer.getFeatures():
            fid = feat['Id']
            if fid is not None:
                ids.append(str(fid))
        if not ids:
            return ""
        quoted = ", ".join(f"'{i}'" for i in ids)
        return f'"Id" IN ({quoted})'

    def constrainExpression(self, expression, idFilter):
        if not idFilter:
            return expression
        if not expression:
            return idFilter
        return f"({idFilter}) AND ({expression})"

    def runQuery(self):
        self.queryHasBeenSubmitted = True
        propertyDisplay = self.cbProperty.currentText()
        propertyInternal = self.getComboInternalName(self.cbProperty)
        self.labelStatisticsPropertyFor.setText(self.tr("Statistics of %1 for selected Elements").replace("%1", propertyDisplay))
        statsIdx = self.findComboByInternalName(self.cbStatisticsFor, propertyInternal)
        if statsIdx >= 0:
            self.cbStatisticsFor.setCurrentIndex(statsIdx)
        elif not self.isNumericProperty(propertyInternal):
            noneIdx = self.findComboByInternalName(self.cbStatisticsFor, '_none_')
            if noneIdx >= 0:
                self.cbStatisticsFor.setCurrentIndex(noneIdx)
        self.calculateStatistics()
        self.updateButtonsState()

    def effectiveCriteria(self):
        if self.radioSingleCriteria.isChecked():
            prop = self.getComboInternalName(self.cbProperty)
            cond = self.cbCondition.currentText()
            val_txt = self.currentValueText()
            if not prop or not cond:
                return []
            if cond != 'All' and not val_txt:
                return []
            return [{
                'property': prop,
                'condition': cond,
                'value': self.parseValue(val_txt) if cond != 'All' else '',
                'operator': '+',
                'enabled': True
            }]
        return self.criteria

    def calculateStatistics(self):
        selectedLayer = self.resolveLayer()
        if not selectedLayer:
            return
        qrIdent = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""

        # Clear previous layer's selection if the target layer changed
        if self.lastSelectedLayer is not None and self.lastSelectedLayer is not selectedLayer:
            try:
                if not sip.isdeleted(self.lastSelectedLayer):
                    self.lastSelectedLayer.removeSelection()
            except RuntimeError:
                pass

        targetField = self.getComboInternalName(self.cbStatisticsFor)
        if not targetField:
            return

        effectiveCriteria = self.effectiveCriteria()
        if not effectiveCriteria:
            return

        # Determine query layer: criteria properties may live on the results layer
        criteriaProps = [c['property'] for c in effectiveCriteria if c.get('enabled', True)]
        hasCriteriaResultProp = any(self.isResultProperty(p) for p in criteriaProps)
        targetIsResultProp = self.isResultProperty(targetField)
        if (hasCriteriaResultProp or targetIsResultProp) and not self.isResultsMode:
            resultCategory = self.elementResultCategory.get(qrIdent)
            resultsLayer = self.resolveResultsLayer(resultCategory) if resultCategory else None
        else:
            resultsLayer = None

        # Pick layers: criteria filter on the layer that has their properties,
        # statistics target reads from the layer that has targetField
        criteriaLayer = resultsLayer if hasCriteriaResultProp and resultsLayer else selectedLayer
        statsLayer = resultsLayer if targetIsResultProp and resultsLayer else selectedLayer
        highlightLayer = resultsLayer if resultsLayer else selectedLayer

        # When querying a results layer for a specific input type, restrict by Id
        idFilter = ""
        if resultsLayer and not self.isResultsMode:
            idFilter = self.buildIdFilter(selectedLayer)

        # Determine if target is numeric and if Flow abs should be used
        isNoneTarget = targetField == '_none_'
        targetIsNumeric = False if isNoneTarget else self.isNumericProperty(targetField)
        useAbsValue = not isNoneTarget and targetField in ('Flow', 'Flow_Unsig')

        def extractValue(feat):
            if isNoneTarget:
                return 1
            val = feat[targetField]
            if val is None or str(val) in ('', 'NULL'):
                return None
            if not targetIsNumeric:
                return val
            v = float(val)
            return abs(v) if useAbsValue else v

        # Collect feature values per individual criterion
        statsPerCriterion = []
        for criterion in effectiveCriteria:
            if not criterion.get('enabled', True):
                continue

            filterExpression = self.buildExpression(criterion)
            critLayer = resultsLayer if self.isResultProperty(criterion['property']) and resultsLayer else selectedLayer
            constrainedExpr = self.constrainExpression(filterExpression, idFilter) if critLayer is resultsLayer else filterExpression
            featureRequest = QgsFeatureRequest().setFilterExpression(constrainedExpr)
            if critLayer is statsLayer:
                featureValues = [
                    v for feat in critLayer.getFeatures(featureRequest)
                    if (v := extractValue(feat)) is not None
                ]
            else:
                matchingIds = {
                    str(feat['Id']) for feat in critLayer.getFeatures(featureRequest)
                    if feat['Id'] is not None
                }
                featureValues = [
                    v for feat in statsLayer.getFeatures()
                    if str(feat['Id']) in matchingIds
                    and (v := extractValue(feat)) is not None
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
        highlightExpression = self.constrainExpression(combinedExpression, idFilter) if highlightLayer is resultsLayer else combinedExpression
        self.highlightFeatures(highlightLayer, highlightExpression)

        constrainedCombined = self.constrainExpression(combinedExpression, idFilter) if criteriaLayer is resultsLayer else combinedExpression
        allFeaturesRequest = QgsFeatureRequest().setFilterExpression(constrainedCombined) if constrainedCombined else QgsFeatureRequest()
        if criteriaLayer is statsLayer:
            allFeatureValues = [
                v for feat in criteriaLayer.getFeatures(allFeaturesRequest)
                if (v := extractValue(feat)) is not None
            ]
        else:
            matchingIds = {
                str(feat['Id']) for feat in criteriaLayer.getFeatures(allFeaturesRequest)
                if feat['Id'] is not None
            }
            allFeatureValues = [
                v for feat in statsLayer.getFeatures()
                if str(feat['Id']) in matchingIds
                and (v := extractValue(feat)) is not None
            ]
        statsPerCriterion.append(allFeatureValues)

        # Helper to compute metrics
        def computeMetrics(values):
            count = len(values)
            if not targetIsNumeric:
                return {'count': count}
            totalValue = sum(values) if count else 0
            avgValue = totalValue / count if count else 0
            minValue = min(values) if count else None
            maxValue = max(values) if count else None
            if self.usesSumColumn(targetField, qrIdent):
                lastCol = totalValue
            else:
                variance = sum((v - avgValue) ** 2 for v in values) / count if count else 0
                lastCol = math.sqrt(variance)
            return {
                'count': count, 'avg': avgValue,
                'min': minValue, 'max': maxValue, 'last': lastCol
            }

        # In single mode, only show the combined "All" row
        if self.radioSingleCriteria.isChecked():
            statsResults = [computeMetrics(statsPerCriterion[-1])]
        else:
            statsResults = [computeMetrics(vals) for vals in statsPerCriterion]

        # Configure columns based on property type
        statisticsTable = self.tableWidgetStatistics
        if isNoneTarget:
            columnHeaders = [self.tr("Count")]
            columnKeys = ['count']
        elif targetIsNumeric:
            lastColLabel = self.tr("Sum") if self.usesSumColumn(targetField, qrIdent) else self.tr("StdD")
            columnHeaders = [self.tr("Count"), self.tr("Avg"), self.tr("Min"), self.tr("Max"), lastColLabel]
            columnKeys = ['count', 'avg', 'min', 'max', 'last']
        else:
            columnHeaders = [self.tr("Count")]
            columnKeys = ['count']

        statisticsTable.setColumnCount(len(columnHeaders))
        statisticsTable.setHorizontalHeaderLabels(columnHeaders)
        for i in range(len(columnHeaders)):
            statisticsTable.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        # Show vertical header only when multiple rows
        showCriterionColumn = len(statsResults) > 1
        statisticsTable.verticalHeader().setVisible(showCriterionColumn)
        statisticsTable.setRowCount(len(statsResults))

        for rowIndex, metrics in enumerate(statsResults):
            for colIndex, key in enumerate(columnKeys):
                value = metrics[key]
                cellText = f"{value:.2f}" if isinstance(value, float) else str(value if value is not None else 0)
                tableItem = QTableWidgetItem(cellText)
                tableItem.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                if key == 'count':
                    tableItem.setBackground(QColor("#d0e8ff"))
                    tableItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                statisticsTable.setItem(rowIndex, colIndex, tableItem)

            rowLabel = self.tr("All") if rowIndex == len(statsResults) - 1 else f"Cr{rowIndex+1}"
            statisticsTable.setVerticalHeaderItem(rowIndex, QTableWidgetItem(rowLabel))

        lastRow = statisticsTable.rowCount() - 1
        for col in range(statisticsTable.columnCount()):
            item = statisticsTable.item(lastRow, col)
            if item:
                item.setBackground(QColor("#ffd700") if col == 0 else QColor("#fff8dc"))
        if statisticsTable.verticalHeaderItem(lastRow):
            statisticsTable.verticalHeaderItem(lastRow).setBackground(QColor("#ffd700"))

        # Resize table to fit rows (up to 4-row cap)
        rowH = statisticsTable.verticalHeader().defaultSectionSize()
        headerH = statisticsTable.horizontalHeader().height()
        maxH = headerH + rowH * 4 + 2
        needed = headerH + rowH * len(statsResults) + 2
        statisticsTable.setFixedHeight(min(needed, maxH))
        statisticsTable.scrollToBottom()

    def toggleEditCriterion(self):
        """Switch in and out of edit‐mode on the selected row."""
        if self.btCriteriaEdit.isChecked():
            self.startCriterionEdit()
        else:
            self.cancelCriterionEdit()

    def startCriterionEdit(self):
        row = self.tableWidgetCriteria.currentRow()
        if row < 0:
            # nothing selected → cancel edit
            self.btCriteriaEdit.setChecked(False)
            return

        self.editingIndex = row
        crit = self.criteria[row]

        # load into the controls
        propIdx = self.findComboByInternalName(self.cbProperty, crit['property'])
        if propIdx >= 0:
            self.cbProperty.setCurrentIndex(propIdx)
        self.updateConditions()
        self.cbCondition.setCurrentText(crit['condition'])
        self.updateValues()

        self.setCurrentValueText(crit['value'])

        # disable other actions while editing
        for btn in (
            self.btAdd,
            self.btSubtract,
            self.btCriteriaUp,
            self.btCriteriaDown,
            self.btCriteriaClear,
            self.btCriteriaSwitch,
            self.btSubmit,
            self.btClearQuery,
            self.radioSingleCriteria,
            self.radioMultipleCriteria,
            self.cbElementType,
            self.btExport,
            self.btImport,
            self.btCommentCriteria,
            self.btExcel,
        ):
            btn.setEnabled(False)
        self.btReplace.setEnabled(True)
        self.tableWidgetCriteria.setEnabled(False)

    def cancelCriterionEdit(self):
        self.editingIndex = None
        self.btCriteriaEdit.setChecked(False)
        for btn in (
            self.btAdd,
            self.radioSingleCriteria,
            self.radioMultipleCriteria,
            self.btExport,
            self.btImport,
            self.btCommentCriteria,
            self.btExcel,
        ):
            btn.setEnabled(True)
        self.tableWidgetCriteria.setEnabled(True)
        self.updateButtonsState()

    def commitCriterionEdit(self):
        if self.editingIndex is None:
            return
        # read back the controls
        prop = self.getComboInternalName(self.cbProperty)
        cond = self.cbCondition.currentText()

        val_txt = self.currentValueText()

        val = self.parseValue(val_txt) if cond != 'All' else ''

        # preserve the original operator and enabled state
        original = self.criteria[self.editingIndex]
        op = original['operator']
        enabled = original.get('enabled', True)

        # overwrite the criterion
        self.criteria[self.editingIndex] = {
            'property': prop,
            'condition': cond,
            'value': val,
            'operator': op,
            'enabled': enabled,
        }

        # reset edit state
        self.editingIndex = None
        self.btCriteriaEdit.setChecked(False)

        # re-enable controls that were blanket-disabled during edit
        for btn in (
            self.btAdd,
            self.radioSingleCriteria,
            self.radioMultipleCriteria,
            self.btExport,
            self.btImport,
            self.btCommentCriteria,
            self.btExcel,
        ):
            btn.setEnabled(True)
        self.tableWidgetCriteria.setEnabled(True)

        # refresh table (and Cr1, Cr2… headers)
        self.reloadCriteriaTable()
        # let updateButtonsState restore per-state enable for the rest
        self.updateButtonsState()

    def onCriteriaSelectionChanged(self, row, col):
        if row < 0 or row >= len(self.criteria):
            self.btCriteriaSwitch.setIcon(self.iconSwitchEnabled)
        else:
            enabled = self.criteria[row].get('enabled', True)
            self.btCriteriaSwitch.setIcon(
            self.iconSwitchEnabled  if enabled  else
            self.iconSwitchDisabled )
        self.updateButtonsState()

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
        from qgis.PyQt.QtWidgets import QDockWidget as _QDW
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
        if getattr(self, '_syncingResults', False):
            return
        self._syncingResults = True
        try:
            self._doSyncResultsLabel(resultsDock)
        finally:
            self._syncingResults = False

    def _doSyncResultsLabel(self, resultsDock):
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
        if self.queryHasBeenSubmitted and self.effectiveCriteria():
            self.runQuery()

    def onResultsStatisticsChanged(self, statName):
        self.currentResultsStatText = statName
        if statName:
            self.labelResults.setText(f"{statName} {self.tr('values for report times')}")
        else:
            self.labelResults.setText(self.currentResultsTimeText)
        previousProp = self.getComboInternalName(self.cbProperty)
        self.updateProperties()
        idx = self.findComboByInternalName(self.cbProperty, previousProp)
        if idx >= 0:
            self.cbProperty.setCurrentIndex(idx)
        # Task 7: Only re-run if user has explicitly submitted a query
        if self.queryHasBeenSubmitted and self.effectiveCriteria():
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

    def fetchTimeFromResultsLayer(self):
        resultsGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if not resultsGroup:
            return
        for layerNode in resultsGroup.findLayers():
            layer = layerNode.layer()
            if layer and not sip.isdeleted(layer):
                self.fetchTimeFromLayer(layer)
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
        defaultName = f"QGISRed_Properties_Criterias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        fname, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save criteria file"),
            os.path.join(str(QgsProject.instance().homePath()), defaultName),
            "Text Files (*.txt)"
        )
        if not fname:
            return
        try:
            elementType = self.cbElementType.currentText()
            comment = self.multipleCriteriaComment.text().strip() if self.radioMultipleCriteria.isChecked() else ""
            activeCriteria = self.effectiveCriteria()
            hasDynamicCriterion = any(
                self.isResultProperty(c['property']) for c in activeCriteria
            )
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(f"{elementType}\n")
                if hasDynamicCriterion:
                    timeText = (self.currentResultsTimeText or self.labelResults.text() or "").strip()
                    if timeText:
                        f.write(f"@{timeText}\n")
                if comment:
                    f.write(f"{comment}\n")
                for c in activeCriteria:
                    prefix = "" if c.get('enabled', True) else "#"
                    op = c['operator']
                    prop = c['property']
                    cond = c['condition']
                    val = c['value']
                    if cond == 'All':
                        f.write(f"{prefix}{op}{prop}\n")
                    else:
                        f.write(f"{prefix}{op}{prop} {cond} {val}\n")
            QMessageBox.information(self, self.tr("Export successful"), self.tr("Saved to:\n") + fname)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export failed"), str(e))

    def importCriteria(self):
        fname, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open criteria file"),
            str(QgsProject.instance().homePath()),
            "Text Files (*.txt)"
        )
        if not fname:
            return
        try:
            with open(fname, 'r', encoding='utf-8') as f:
                lines = [line.rstrip('\n') for line in f.readlines()]
            if len(lines) < 1:
                return
            elementType = lines[0]
            for i in range(self.cbElementType.count()):
                if self.cbElementType.itemText(i) == elementType:
                    self.cbElementType.setCurrentIndex(i)
                    break
            parsedCriteria = []
            importedComment = ''
            for line in lines[1:]:
                if not line.strip():
                    continue
                enabled = True
                candidate = line
                if candidate.startswith('#'):
                    enabled = False
                    candidate = candidate[1:]
                if candidate.startswith('@'):
                    continue
                if not candidate or candidate[0] not in ('+', '-'):
                    importedComment = line.strip()
                    continue
                line = candidate
                op = line[0]
                rest = line[1:].strip()
                propEnd = rest.find(' ')
                if propEnd < 0:
                    prop = rest
                    cond = 'All'
                    val = ''
                else:
                    prop = rest[:propEnd]
                    condVal = rest[propEnd + 1:].strip()
                    if not condVal:
                        cond = 'All'
                        val = ''
                    elif condVal.upper().startswith('NOT ILIKE '):
                        cond = 'NOT ILIKE'
                        val = self.parseValue(condVal[10:].strip())
                    elif condVal.upper().startswith('NOT LIKE '):
                        cond = 'NOT LIKE'
                        val = self.parseValue(condVal[9:].strip())
                    else:
                        condParts = condVal.split(None, 1)
                        cond = condParts[0] if condParts else 'All'
                        val = self.parseValue(condParts[1].strip()) if len(condParts) > 1 else ''
                parsedCriteria.append({
                    'property': prop,
                    'condition': cond,
                    'value': val,
                    'operator': op,
                    'enabled': enabled
                })
            useSingle = len(parsedCriteria) == 1
            if useSingle and parsedCriteria:
                c = parsedCriteria[0]
                self.radioSingleCriteria.setChecked(True)
                self.multipleCriteriaComment.setText('')
                propIdx = self.findComboByInternalName(self.cbProperty, c['property'])
                if propIdx >= 0:
                    self.cbProperty.setCurrentIndex(propIdx)
                condIdx = self.cbCondition.findText(c['condition'])
                if condIdx >= 0:
                    self.cbCondition.setCurrentIndex(condIdx)
                self.updateValues()
                self.setCurrentValueText(str(c['value']) if c['value'] != '' else '')
            else:
                self.radioMultipleCriteria.setChecked(True)
                self.criteria = parsedCriteria
                self.multipleCriteriaComment.setText(importedComment)
                self.reloadCriteriaTable()
        except Exception as e:
            QMessageBox.critical(self, self.tr("Import failed"), str(e))

    def exportStatistics(self):
        defaultName = f"QGISRed_Properties_Statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        fname, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Save statistics file"),
            os.path.join(str(QgsProject.instance().homePath()), defaultName),
            "CSV Files (*.csv)"
        )
        if not fname:
            return
        try:
            projectName = QgsProject.instance().baseName()
            activeCriteria = self.effectiveCriteria()
            queryLabel = self.tr("Query") if len(activeCriteria) == 1 else self.tr("Queries")
            timeText = (self.currentResultsTimeText or self.labelResults.text() or "").strip()
            statsProp = self.cbStatisticsFor.currentText()
            hasDynamicCriterion = any(
                self.isResultProperty(c['property']) for c in activeCriteria
            )
            queryHeader = queryLabel + (f" @{timeText}" if timeText and hasDynamicCriterion else "")

            table = self.tableWidgetStatistics
            headers = [
                table.horizontalHeaderItem(col).text() if table.horizontalHeaderItem(col) else ''
                for col in range(table.columnCount())
            ]

            with open(fname, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                f.write(f"Project: {projectName}\n")
                f.write(f"Scenario: base\n")
                if hasDynamicCriterion:
                    f.write(f"{queryHeader}\n")
                f.write(f"Property: {statsProp}\n")
                for c in activeCriteria:
                    op = c['operator']
                    prop = c['property']
                    cond = c['condition']
                    val = c['value']
                    if cond == 'All':
                        f.write(f"{op} {prop}\n")
                    else:
                        f.write(f"{op} {prop} {cond} {val}\n")
                comment = self.multipleCriteriaComment.text().strip() if self.radioMultipleCriteria.isChecked() else ""
                if comment:
                    f.write(f"Comment: {comment}\n")
                f.write("\n")
                writer.writerow(headers)
                for row in range(table.rowCount()):
                    rowdata = [
                        table.item(row, col).text() if table.item(row, col) else ''
                        for col in range(table.columnCount())
                    ]
                    writer.writerow(rowdata)

            QMessageBox.information(self, self.tr("Export successful"), self.tr("Saved to:\n") + fname)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Export failed"), str(e))
