# -*- coding: utf-8 -*-

import os
import random
import math
import statistics

from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QDialog, QMessageBox, QHeaderView, QLineEdit, QAbstractItemView
from PyQt5.QtWidgets import QCheckBox, QSpinBox, QApplication, QProgressDialog, QWidget, QHBoxLayout
from PyQt5.QtCore import QVariant, Qt, QTimer, QEvent
from qgis.PyQt import uic

from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, QgsGraduatedSymbolRenderer
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererRange, QgsRendererCategory, QgsSymbol
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGradientColorRamp, QgsClassificationJenks
from qgis.core import QgsClassificationPrettyBreaks, QgsStyle, QgsPresetSchemeColorRamp, QgsProperty, QgsSymbolLayer
from qgis.utils import iface

from ..tools.qgisred_utils import QGISRedUtils
from .qgisred_custom_dialogs import QGISRedRangeEditDialog, QGISRedSymbolColorSelector
from .qgisred_custom_dialogs import QGISRedColorRampSelector, QGISRedRowSelectionFilter
from .qgisred_custom_dialogs import QGISRedPaletteEmulator, QGISRedSizePaletteEmulator

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

class QGISRedLegendsDialog(QDialog, formClass):
    FIELD_TYPE_NUMERIC = "numeric"
    FIELD_TYPE_CATEGORICAL = "categorical"
    FIELD_TYPE_UNKNOWN = "unknown"

    WARN_CLASSES = 50
    MAX_CLASSES = 1000

    ALLOWED_GROUP_IDENTIFIERS = [
        "qgisred_thematicmaps",
        "qgisred_results",
        "qgisred_demandsectors",
        "qgisred_inputs"
    ]

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, parent=None):
        super(QGISRedLegendsDialog, self).__init__(parent)
        self.setupUi(self)
        self.initializeProperties()
        self.initializeUi()
        self.connectSignals()
        self.loadInitialState()

    def initializeProperties(self):
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.currentFieldName = None
        self.currentLayer = None
        self.pluginFolder = os.path.dirname(os.path.dirname(__file__))
        self.isEditing = True
        self.originalRenderer = None
        self.availableUniqueValues = []
        self.usedUniqueValues = []
        self.addClassClickTimer = None
        self.addClassBeforeSelection = False
        self.layerTreeViewConnection = None
        self.layerTreeRoot = None
        self.style = None
        self.lastValidLayerId = None

        self.parentPlugin = None
        self.qgisInterface = None
        self.projectDirectory = ""
        self.networkName = ""
        self.utils = None
        self.paletteEmulator = QGISRedPaletteEmulator(self)
        self.sizePaletteEmulator = QGISRedSizePaletteEmulator(self)
        self.previousClassificationMode = None
        self.previousSizeMode = None

    # ============================================================
    # RESULTS LAYER DETECTION AND VALUE EXTRACTION
    # ============================================================

    def isResultsLayer(self):
        """Check if the current layer is a results layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            return False
        return identifier.startswith("qgisred_link_") or identifier.startswith("qgisred_node_")

    def isLinkResultLayer(self):
        """Check if current layer is a Link result layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_link_")

    def isNodeResultLayer(self):
        """Check if current layer is a Node result layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_node_")

    def getResultFieldMapping(self):
        """Map layer identifier to field name in the 'All' shapefile."""
        mapping = {
            "qgisred_link_flow": "Flow",
            "qgisred_link_velocity": "Velocity",
            "qgisred_link_headloss": "HeadLoss",
            "qgisred_link_unitheadloss": "UnitHeadLo",
            "qgisred_link_status": "Status",
            "qgisred_link_quality": "Quality",
            "qgisred_node_demand": "Demand",
            "qgisred_node_head": "Head",
            "qgisred_node_pressure": "Pressure",
            "qgisred_node_quality": "Quality",
        }
        if not self.currentLayer:
            return None
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return mapping.get(identifier)

    def getResultsAllShapefilePath(self):
        """Get path to the corresponding 'All' shapefile for results layers."""
        if not self.projectDirectory or not self.networkName:
            return None

        resultsDir = os.path.join(self.projectDirectory, "Results")

        if self.isLinkResultLayer():
            return os.path.join(resultsDir, f"{self.networkName}_Base_Link_All.shp")
        elif self.isNodeResultLayer():
            return os.path.join(resultsDir, f"{self.networkName}_Base_Node_All.shp")
        return None

    def loadResultsAllLayer(self):
        """Load the 'All' shapefile as a temporary QgsVectorLayer."""
        shapefilePath = self.getResultsAllShapefilePath()
        if not shapefilePath or not os.path.exists(shapefilePath):
            return None

        layer = QgsVectorLayer(shapefilePath, "temp_results_all", "ogr")
        return layer if layer.isValid() else None

    def getResultsNumericValues(self):
        """Get numeric values from the 'All' shapefile for results layers."""
        allLayer = self.loadResultsAllLayer()
        if not allLayer:
            return []

        fieldName = self.getResultFieldMapping()
        if not fieldName:
            del allLayer
            return []

        fieldIdx = allLayer.fields().indexOf(fieldName)
        if fieldIdx < 0:
            del allLayer
            return []

        values = []
        for feature in allLayer.getFeatures():
            try:
                val = float(feature[fieldName])
                values.append(val)
            except:
                pass

        del allLayer
        return sorted(values)

    def getResultsUniqueValues(self):
        """Get unique values from the 'All' shapefile for categorical results."""
        allLayer = self.loadResultsAllLayer()
        if not allLayer:
            return []

        fieldName = self.getResultFieldMapping()
        if not fieldName:
            del allLayer
            return []

        fieldIdx = allLayer.fields().indexOf(fieldName)
        if fieldIdx < 0:
            del allLayer
            return []

        values = set()
        for feature in allLayer.getFeatures():
            value = feature[fieldName]
            values.add(str(value) if value is not None else "NULL")

        specialValues = ["NULL", "#NA"]
        regularValues = [v for v in values if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in values]

        del allLayer
        return sorted(regularValues) + foundSpecials

    def config(self, qgisInterface, projectDirectory, networkName, parentPlugin):
        self.parentPlugin = parentPlugin
        self.qgisInterface = qgisInterface
        self.projectDirectory = projectDirectory
        self.networkName = networkName
        self.utils = QGISRedUtils(projectDirectory, networkName, qgisInterface)

        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())

    # ============================================================
    # UI INITIALIZATION
    # ============================================================

    def initializeUi(self):
        self.configureWindow()
        self.setupTableView()
        self.populateClassificationModes()
        self.populateLegendTypes()
        self.populateGroups()
        self.setupClassCountField()
        self.setupClassifyAllButton()
        self.setupAdvancedUi()
        self.loadStyleDatabase()
        self.applyConsistentStyling()
        self.setupTooltips()
        self.hideIntervalControls()
        self.installEventFilter(self)
        self.btClassPlus.installEventFilter(self)

    def configureWindow(self):
        iconPath = os.path.join(os.path.dirname(__file__), "..", "images", "iconThematicMaps.png")
        self.setWindowIcon(QIcon(iconPath))
        self.setWindowTitle("QGISRed Legend Editor")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.btClassPlus.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))

    def setupTableView(self):
        self.tableView.setColumnCount(5)
        self.tableView.setHorizontalHeaderLabels(["", "Color", "Size", "Value", "Legend"])
        self.rowSelectionFilter = QGISRedRowSelectionFilter(self.tableView)

        header = self.tableView.horizontalHeader()

        # Visibility checkbox
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableView.setColumnWidth(0, 30)

        # Color
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableView.setColumnWidth(1, 40)

        # Size
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableView.setColumnWidth(2, 60)

        header.setSectionResizeMode(3, QHeaderView.Stretch) # Value
        header.setSectionResizeMode(4, QHeaderView.Stretch) # Legend

        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableView.setAlternatingRowColors(False)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setShowGrid(True)
        self.applyTableStylesheet()

    def applyTableStylesheet(self):
        stylesheet = """
            QTableWidget {background-color: white;gridline-color: #d0d0d0;
            selection-background-color: #3399ff;selection-color: white;border: 1px solid #d0d0d0;}
            QTableWidget::item {border-bottom: 1px solid #d0d0d0;padding: 0px;}
            QTableWidget::item:selected {background-color: #3399ff;}
            QHeaderView::section {background-color: #f0f0f0;padding: 4px;border: 1px solid #d0d0d0;}
        """
        self.tableView.setStyleSheet(stylesheet)

    def setupClassCountField(self):
        self.leClassCount.setMinimum(0)
        self.leClassCount.setMaximum(self.MAX_CLASSES)
        self.leClassCount.valueChanged.connect(self.onClassCountChanged)
        self.setClassCountEditable(False)

    def setupClassifyAllButton(self):
        iconPath = os.path.join(os.path.dirname(__file__), "..", "images", "iconClassifyAll.png")
        self.btClassifyAll.setIcon(QIcon(iconPath))
        self.btClassifyAll.setToolTip(self.tr("Classify All Unique Values"))
        self.btClassifyAll.clicked.connect(self.classifyAllUniqueValues)

    def setupAdvancedUi(self):
        self.setupSizeControls()
        self.setupColorControls()
        self.setupColorRampButton()
        self.onSizeModeChanged()
        self.onColorModeChanged()

    def setupSizeControls(self):
        sizeModes = [
            "Manual",
            "Equal",
            "Linear",
            "Quadratic",
            "Exponential",
            "Proportional to Value",
        ]

        self.cbSizes.addItems(sizeModes)
        self.cbSizes.currentIndexChanged.connect(self.onSizeModeChanged)
        self.spinSizeEqual.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.spinSizeMax.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMax.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.ckSizeInvert.toggled.connect(self.applySizeLogic)
        self.updateSizeSpinBoxConstraints()

    def setupColorControls(self):
        colorModes = ["Manual", "Equal", "Random", "Ramp", "Palette"]
        self.cbColors.addItems(colorModes)
        self.cbColors.currentIndexChanged.connect(self.onColorModeChanged)
        self.btColorEqual.setColor(QColor("red"))
        self.btColorEqual.colorChanged.connect(self.applyColorLogic)
        self.ckColorInvert.toggled.connect(self.applyColorLogic)
        self.btRefreshColors.setIcon(QIcon(":/images/themes/default/mActionRefresh.svg"))
        self.btRefreshColors.clicked.connect(lambda: self.applyColorLogic(forceRefresh=True))

    def setupColorRampButton(self):
        self.btnColorRamp = QGISRedColorRampSelector(self)
        self.btnColorRamp.setVisible(False)
        self.palletesHorizontalLayout.addStretch(1)
        self.palletesHorizontalLayout.addWidget(self.btnColorRamp)
        self.palletesHorizontalLayout.addStretch(1)
        self.btnColorRamp.rampChanged.connect(self.onCustomColorChanged)

    def applyConsistentStyling(self):
        comboStyle = "QComboBox { background-color: white; }"
        spinStyle = (
            "QSpinBox { background-color: white; } "
            "QDoubleSpinBox { background-color: white; }"
        )

        self.cbGroups.setStyleSheet(comboStyle)
        self.cbLegendLayer.setStyleSheet(comboStyle)
        self.cbMode.setStyleSheet(comboStyle)
        self.cbLegendsType.setStyleSheet(comboStyle)
        self.cbSizes.setStyleSheet(comboStyle)
        self.cbColors.setStyleSheet(comboStyle)

        self.spinIntervalRange.setStyleSheet(spinStyle)
        self.spinSizeEqual.setStyleSheet(spinStyle)
        self.spinSizeMin.setStyleSheet(spinStyle)
        self.spinSizeMax.setStyleSheet(spinStyle)

    def setupTooltips(self):
        self.btUp.setToolTip(self.tr("Move selected class up"))
        self.btDown.setToolTip(self.tr("Move selected class down"))
        self.btClassMinus.setToolTip(self.tr("Remove selected class(es)"))
        self.btClassifyAll.setToolTip(self.tr("Add all unique values as separate classes"))

        if hasattr(self, "btRefreshColors"):
            self.btRefreshColors.setToolTip(self.tr("Refresh color ramp"))

        self.btLoadDefault.setToolTip(self.tr("Load default style for this layer"))
        self.btLoadGlobal.setToolTip(self.tr("Load style from global database"))
        self.btSaveGlobal.setToolTip(self.tr("Save current style to global database"))
        self.btLoadProject.setToolTip(self.tr("Load style from project database"))
        self.btSaveProject.setToolTip(self.tr("Save current style to project database"))
        self.btApplyLegend.setToolTip(self.tr("Apply changes to layer"))
        self.btCancelLegend.setToolTip(self.tr("Cancel and close dialog"))

    def hideIntervalControls(self):
        self.labelIntervalRange.setVisible(False)
        self.spinIntervalRange.setVisible(False)

    def loadStyleDatabase(self):
        self.style = QgsStyle()
        dbPath = os.path.join(self.pluginFolder, "defaults", "symbology-style_QGISRed.db")

        if os.path.exists(dbPath):
            try:
                success = self.style.createDatabase(dbPath) or self.style.load(
                    dbPath
                )
                if not success:
                    QgsMessageLog.logMessage(
                        f"Failed to load style database: {dbPath}",
                        "QGISRed",
                        Qgis.Warning,
                    )
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error loading style database: {str(e)}",
                    "QGISRed",
                    Qgis.Warning,
                )
        else:
            QgsMessageLog.logMessage(
                f"Style database not found: {dbPath}",
                "QGISRed",
                Qgis.Info,
            )

    # ============================================================
    # SIGNAL CONNECTIONS
    # ============================================================

    def connectSignals(self):
        self.cbGroups.currentIndexChanged.connect(self.onGroupChanged)
        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.cancelAndClose)
        self.cbMode.currentIndexChanged.connect(self.onModeChanged)
        self.cbLegendsType.currentIndexChanged.connect(self.onLegendTypeChanged)
        self.spinIntervalRange.valueChanged.connect(self.onIntervalRangeChanged)
        self.btClassPlus.clicked.connect(self.onAddClassClicked)
        self.btClassMinus.clicked.connect(self.removeClass)
        self.btUp.clicked.connect(self.moveClassUp)
        self.btDown.clicked.connect(self.moveClassDown)
        self.btSaveProject.clicked.connect(self.saveProjectStyle)
        self.btSaveGlobal.clicked.connect(self.saveGlobalStyle)
        self.btLoadDefault.clicked.connect(self.loadDefaultStyle)
        self.btLoadGlobal.clicked.connect(self.loadGlobalStyle)
        self.btLoadProject.clicked.connect(self.loadProjectStyle)
        self.tableView.cellDoubleClicked.connect(self.onCellDoubleClicked)
        self.tableView.itemSelectionChanged.connect(self.updateButtonStates)
        self.connectLayerTreeSignal()

    def connectLayerTreeSignal(self):
        if iface and iface.layerTreeView():
            self.layerTreeViewConnection = iface.layerTreeView().currentLayerChanged.connect(self.onQgisLayerSelectionChanged)

    def loadInitialState(self):
        self.preselectGroupAndLayer()
        self.frameLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.labelFrameLegends.setText(self.tr("Legend"))

        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())
            self.populateLegendTypes(self.cbLegendLayer.currentLayer())

        self.updateClassCount()

    # ============================================================
    # EVENT HANDLERS - LAYER AND GROUP
    # ============================================================

    def onQgisLayerSelectionChanged(self, layer):
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        layerNode = QgsProject.instance().layerTreeRoot().findLayer(layer)
        if not layerNode or not layerNode.isVisible():
            return

        groupPath = self.findGroupPathForLayer(layerNode)
        if not groupPath:
            return

        if layer.renderer().type() not in ("graduatedSymbol", "categorizedSymbol"):
            return

        currentGroupPath = self.cbGroups.currentData()
        if currentGroupPath != groupPath:
            self.setGroupByPath(groupPath)
            self.onGroupChanged()

        if self.cbLegendLayer.currentLayer() != layer:
            self.cbLegendLayer.setLayer(layer)

    def onGroupChanged(self):
        allowedLayers = self.getRenderableLayersInSelectedGroup()
        allLayers = list(QgsProject.instance().mapLayers().values())
        exceptedLayers = [layer for layer in allLayers if layer not in allowedLayers]

        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(exceptedLayers)

        targetLayer = self.determineTargetLayer(allowedLayers)

        self.cbLegendLayer.setLayer(targetLayer)
        self.cbLegendLayer.blockSignals(False)
        self.onLayerChanged(self.cbLegendLayer.currentLayer())

    def determineTargetLayer(self, allowedLayers):
        currentLayer = self.cbLegendLayer.currentLayer()
        targetLayer = None

        activeNode = self.getActiveLayerFromTree()
        if activeNode:
            activeLayer = activeNode.layer()
            if activeLayer in allowedLayers:
                targetLayer = activeLayer

        if targetLayer is None and self.lastValidLayerId:
            for layer in allowedLayers:
                if layer.id() == self.lastValidLayerId:
                    targetLayer = layer
                    break

        if targetLayer is None and currentLayer and currentLayer in allowedLayers:
            targetLayer = currentLayer

        if targetLayer is None and allowedLayers:
            targetLayer = allowedLayers[0]

        return targetLayer

    def onLayerChanged(self, layer):
        if layer and isinstance(layer, QgsVectorLayer):
            self.handleValidLayerSelection(layer)
        else:
            self.resetToEmptyState()

    def handleValidLayerSelection(self, layer):
        self.lastValidLayerId = layer.id()
        self.currentLayer = layer
        self.originalRenderer = layer.renderer().clone() if layer.renderer() else None
        self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)
        self.frameLegends.setEnabled(True)

        self.updateFrameLegendLabel(layer)
        self.populateLegendTypes(layer)
        self.syncLegendTypeComboBox(layer)
        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        self.populateLegendTable()
        self.updateButtonStates()

    def updateFrameLegendLabel(self, layer):
        baseTitle = self.tr(f"Legend for {layer.name()}")
        units = self.getLayerUnits()

        if units:
            self.labelFrameLegends.setText(f"{baseTitle} | {units} units")
        else:
            self.labelFrameLegends.setText(baseTitle)

    def syncLegendTypeComboBox(self, layer):
        rendererType = layer.renderer().type()
        index = self.cbLegendsType.findData(rendererType)

        if index != -1:
            self.cbLegendsType.blockSignals(True)
            self.cbLegendsType.setCurrentIndex(index)
            self.cbLegendsType.blockSignals(False)

    def populateLegendTable(self):
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.populateNumericLegend()
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.populateCategoricalLegend()
        else:
            self.clearTable()

    # ============================================================
    # EVENT HANDLERS - MODE AND TYPE CHANGES
    # ============================================================

    def onModeChanged(self):
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return

        self.updateUiBasedOnFieldType()
        methodId = self.cbMode.currentData()

        if self.previousClassificationMode is None and methodId is not None:
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)

        # Capture anchor sizes when transitioning TO automatic interval mode while size mode is manual
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        wasManualIntervalMode = self.previousClassificationMode is None or self.previousClassificationMode == "Manual"
        isNowAutomaticIntervalMode = methodId is not None and methodId != "Manual"

        if wasManualIntervalMode and isNowAutomaticIntervalMode and sizeMode == "Manual":
            currentSizes = self.collectCurrentTableSizes()
            if len(currentSizes) >= 2:
                self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)

        self.previousClassificationMode = methodId

        if not methodId:
            return

        if methodId == "FixedInterval":
            self.calculateOptimalInterval()

        self.applyClassificationMethod(methodId)

    def onIntervalRangeChanged(self):
        if self.cbMode.currentData() == "FixedInterval":
            self.applyClassificationMethod("FixedInterval")

    def onLegendTypeChanged(self):
        if not self.currentLayer or not self.currentFieldName:
            return

        newType = self.cbLegendsType.currentData()
        currentType = self.currentLayer.renderer().type() if self.currentLayer.renderer() else None

        if newType == currentType:
            return

        field = self.currentFieldName

        if newType == "categorizedSymbol":
            if not self.validateCategorizedConversion(field, currentType):
                return
            self.convertToCategorized(field)
            self.currentFieldType = self.FIELD_TYPE_CATEGORICAL
            self.currentFieldName = field

        elif newType == "graduatedSymbol":
            self.convertToGraduated(field)
            self.currentFieldType, self.currentFieldName = self.detectFieldType(
                self.currentLayer
            )
        else:
            self.currentFieldType, self.currentFieldName = self.detectFieldType(
                self.currentLayer
            )

        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        self.populateLegendTable()
        self.updateButtonStates()
        self.currentLayer.triggerRepaint()

    def validateCategorizedConversion(self, field, currentType):
        """Validates if conversion to categorized renderer is allowed based on unique value count."""
        fieldIdx = self.currentLayer.fields().indexOf(field)
        if fieldIdx < 0:
            return True

        uniqueValues = self.currentLayer.uniqueValues(fieldIdx)
        uniqueCount = len([v for v in uniqueValues if v is not None and str(v) != "NULL"])

        if uniqueCount > self.MAX_CLASSES:
            QMessageBox.critical(
                self,
                self.tr("Too Many Classes"),
                self.tr(
                    f"The field '{field}' has {uniqueCount} unique values.\n"
                    f"The maximum allowed is {self.MAX_CLASSES}.\n"
                    f"Please filter the data or choose a different field."
                ),
            )
            self.revertLegendTypeComboBox(currentType)
            return False

        if uniqueCount > self.WARN_CLASSES:
            reply = QMessageBox.question(
                self,
                self.tr("High Class Count Warning"),
                self.tr(
                    f"The field '{field}' has {uniqueCount} unique values.\n"
                    f"Creating a categorized legend with more than {self.WARN_CLASSES} classes "
                    f"may affect performance and readability.\n\n"
                    f"Do you want to proceed?"
                ),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply == QMessageBox.No:
                self.revertLegendTypeComboBox(currentType)
                return False

        return True

    def revertLegendTypeComboBox(self, previousType):
        self.cbLegendsType.blockSignals(True)
        idx = self.cbLegendsType.findData(previousType)
        if idx >= 0:
            self.cbLegendsType.setCurrentIndex(idx)
        self.cbLegendsType.blockSignals(False)

    def onClassCountChanged(self, newValue):
        if not self.currentLayer or not self.modeHasVariableClassCount():
            return

        currentCount = self.tableView.rowCount()
        if newValue == currentCount:
            return

        self.leClassCount.blockSignals(True)

        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.adjustNumericClassCount(newValue, currentCount)
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.adjustCategoricalClassCount(newValue, currentCount)

        self.leClassCount.blockSignals(False)

    def adjustNumericClassCount(self, newValue, currentCount):
        isRemoval = newValue < currentCount

        if newValue > currentCount:
            while self.tableView.rowCount() < newValue:
                self.addNumericClass()
        elif newValue < currentCount:
            while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                self.tableView.removeRow(self.tableView.rowCount() - 1)

        self.leClassCount.setValue(self.tableView.rowCount())

        modeId = self.cbMode.currentData()
        if modeId and modeId not in [None, "Manual"] and newValue > currentCount:
            self.applyClassificationMethod(modeId)
        else:
            self.handleColorLogicOnClassChange()
            self.handleSizeLogicOnClassChange(isRemoval=isRemoval)

    def adjustCategoricalClassCount(self, newValue, currentCount):
        isRemoval = newValue < currentCount

        if newValue > currentCount:
            while (
                self.tableView.rowCount() < newValue and self.availableUniqueValues
            ):
                self.addCategoricalClass()
        elif newValue < currentCount:
            while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                self.removeCategoricalRow(self.tableView.rowCount() - 1)

        self.leClassCount.setValue(self.tableView.rowCount())
        self.updateClassCountLimits()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange(isRemoval=isRemoval)

    def onCellDoubleClicked(self, row, column):
        if column == 2 and self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.openRangeEditor(row)

    # ============================================================
    # EVENT HANDLERS - SIZE AND COLOR
    # ============================================================

    def onSizeModeChanged(self):
        mode = self.cbSizes.currentText()
        showEqual = mode == "Equal"
        showMinMax = mode in [
            "Linear",
            "Quadratic",
            "Exponential",
            "Proportional to Value",
        ]

        self.spinSizeEqual.setVisible(showEqual)
        self.labelSizeValue.setVisible(showEqual)
        self.spinSizeMin.setVisible(showMinMax)
        self.spinSizeMax.setVisible(showMinMax)
        self.labelSpinMin.setVisible(showMinMax)
        self.labelSpinMax.setVisible(showMinMax)
        self.ckSizeInvert.setVisible(mode != "Manual" and mode != "Equal")

        # Capture anchor sizes when transitioning TO manual while interval mode is automatic
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"
        wasAutomaticSizeMode = self.previousSizeMode is not None and self.previousSizeMode != "Manual"

        if mode == "Manual" and wasAutomaticSizeMode and isAutomaticIntervalMode:
            currentSizes = self.collectCurrentTableSizes()
            if len(currentSizes) >= 2:
                self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)

        self.previousSizeMode = mode

        self.applySizeLogic()

    def onColorModeChanged(self):
        mode = self.cbColors.currentText()
        self.btColorEqual.setVisible(mode == "Equal")

        isRampOrPalette = mode in ["Ramp", "Palette"]
        self.btnColorRamp.setVisible(isRampOrPalette)
        self.ckColorInvert.setVisible(isRampOrPalette)
        self.btRefreshColors.setVisible(mode == "Random")

        if isRampOrPalette:
            self.syncColorRampButton()

        self.applyColorLogic()

    def onCustomColorChanged(self, ramp):
        self.applyColorLogic()

    def onRowColorChanged(self, _color):
        """Handles when a user manually changes a row's color via the color picker.

        When in automatic interval mode with manual colors, updates the palette
        emulator with current colors so subsequent class additions/removals
        will interpolate from the updated palette.
        """
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and colorMode == "Manual":
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)

    def updateSizeSpinBoxConstraints(self):
        minVal = self.spinSizeMin.value()
        maxVal = self.spinSizeMax.value()

        self.spinSizeMin.blockSignals(True)
        self.spinSizeMax.blockSignals(True)

        self.spinSizeMin.setMaximum(maxVal)
        self.spinSizeMax.setMinimum(minVal)

        self.spinSizeMin.blockSignals(False)
        self.spinSizeMax.blockSignals(False)

    # ============================================================
    # SIZE LOGIC
    # ============================================================

    def applySizeLogic(self):
        if not hasattr(self, "cbSizes"):
            return

        mode = self.cbSizes.currentText()
        if mode == "Manual" or self.tableView.rowCount() == 0:
            return

        rows = self.tableView.rowCount()
        sizes = self.calculateSizesForMode(mode, rows)
        self.applySizesToTable(sizes)

    def calculateSizesForMode(self, mode, rows):
        if mode == "Equal":
            return [self.spinSizeEqual.value()] * rows

        if mode == "Proportional to Value":
            return self.calculateProportionalSizes(rows)

        return self.calculateInterpolatedSizes(mode, rows)

    def calculateProportionalSizes(self, rows):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()

        rangeAverageValues = []
        for row in range(rows):
            rangeValues = self.getRangeValues(row)
            if rangeValues:
                lowerBound, upperBound = rangeValues
                rangeAverageValues.append((lowerBound + upperBound) / 2.0)
            else:
                rangeAverageValues.append(0.0)

        globalValueMin, globalValueMax = self.getLayerMinMax()

        sizes = []
        for averageValue in rangeAverageValues:
            calculatedSize = self.computeProportionalSize(minSize, maxSize, globalValueMin, globalValueMax, averageValue)
            sizes.append(calculatedSize)

        if self.ckSizeInvert.isChecked():
            sizes.reverse()

        return sizes

    def computeProportionalSize(self, minSize, maxSize, globalValueMin, globalValueMax, averageValue):
        valueRange = globalValueMax - globalValueMin
        if valueRange == 0:
            return minSize

        calculatedSize = minSize + ((maxSize - minSize) / valueRange) * (averageValue - globalValueMin)
        return max(minSize, min(maxSize, calculatedSize))

    def calculateInterpolatedSizes(self, mode, rows):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()

        tValues = [i / max(1, rows - 1) for i in range(rows)]

        if self.ckSizeInvert.isChecked():
            tValues.reverse()

        sizes = []
        for t in tValues:
            if mode == "Linear":
                sizes.append(minSize + t * (maxSize - minSize))
            elif mode == "Quadratic":
                sizes.append(minSize + (t * t) * (maxSize - minSize))
            elif mode == "Exponential":
                if rows > 1:
                    factor = (math.exp(t) - 1) / (math.exp(1) - 1)
                    sizes.append(minSize + factor * (maxSize - minSize))
                else:
                    sizes.append(minSize)

        return sizes

    def applySizesToTable(self, sizes):
        isLine = self.getGeometryHint() == "line"

        for row in range(self.tableView.rowCount()):
            sizeWidget = self.tableView.cellWidget(row, 2)
            colorContainer = self.tableView.cellWidget(row, 1)
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            if sizeWidget:
                sizeWidget.blockSignals(True)
                sizeWidget.setText(f"{sizes[row]:.2f}")
                sizeWidget.blockSignals(False)

            if colorWidget:
                colorWidget.updateSymbolSize(sizes[row], isLine)

    # ============================================================
    # COLOR LOGIC
    # ============================================================

    def applyColorLogic(self, forceRefresh=False, previousColors=None):
        if not hasattr(self, "cbColors"):
            return

        mode = self.cbColors.currentText()
        rows = self.tableView.rowCount()

        if rows == 0:
            return

        if mode == "Manual":
            if previousColors and len(previousColors) >= 2:
                colors = self.calculateEmulatedPaletteColors(rows, previousColors)
                self.applyColorsToTable(colors)
            return

        colors = self.calculateColorsForMode(mode, rows, forceRefresh)
        self.applyColorsToTable(colors)

    def calculateColorsForMode(self, mode, rows, forceRefresh):
        if mode == "Equal":
            return [self.btColorEqual.color()] * rows

        if mode == "Random":
            return self.calculateRandomColors(rows, forceRefresh)

        if mode == "Ramp":
            return self.calculateRampColors(rows)

        if mode == "Palette":
            return self.calculatePaletteColors(rows)

        return [self.generateRandomColor() for _ in range(rows)]

    def calculateRandomColors(self, rows, forceRefresh):
        if forceRefresh:
            return [self.generateRandomColor() for _ in range(rows)]

        colors = []
        for row in range(rows):
            existingColor = self.getRowColor(row)
            if existingColor and existingColor.isValid():
                colors.append(existingColor)
            else:
                colors.append(self.generateRandomColor())
        return colors

    def calculateRampColors(self, rows):
        ramp = self.btnColorRamp.getActiveRampClone()
        if isinstance(ramp, QgsGradientColorRamp):
            colors = self.algorithmRamp(ramp, rows)
        else:
            colors = [self.generateRandomColor() for _ in range(rows)]

        if self.ckColorInvert.isChecked():
            colors.reverse()

        return colors

    def calculatePaletteColors(self, rows):
        palette = self.btnColorRamp.getActiveRampClone()
        if isinstance(palette, QgsPresetSchemeColorRamp):
            colors = self.algorithmPalette(palette, rows)
        else:
            colors = [self.generateRandomColor() for _ in range(rows)]

        if self.ckColorInvert.isChecked():
            colors.reverse()

        return colors

    def calculateEmulatedPaletteColors(self, rows, previousColors):
        """Generates interpolated colors using the palette emulator from existing colors."""
        if self.paletteEmulator.getPaletteCount() >= 2:
            pass
        elif previousColors and len(previousColors) >= 2:
            self.paletteEmulator.setPaletteFromQColors(previousColors)
        else:
            self.paletteEmulator.reset()
            return [self.generateRandomColor() for _ in range(rows)]

        self.paletteEmulator.generate(rows)

        return self.paletteEmulator.getQColorList()

    def applyColorsToTable(self, colors):
        for row in range(self.tableView.rowCount()):
            colorContainer = self.tableView.cellWidget(row, 1)
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if colorWidget:
                colorWidget.setSelectorColor(colors[row])

    def collectCurrentTableColors(self):
        """Collects all current colors from the table rows."""
        colors = []
        for row in range(self.tableView.rowCount()):
            color = self.getRowColor(row)
            if color and color.isValid():
                colors.append(color)
        return colors

    def collectCurrentTableSizes(self):
        """Collects all current sizes from the table rows."""
        sizes = []
        for row in range(self.tableView.rowCount()):
            sizeWidget = self.tableView.cellWidget(row, 2)
            if sizeWidget and isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    sizes.append(size)
                except (ValueError, TypeError):
                    sizes.append(0.0)
        return sizes

    def handleColorLogicOnClassChange(self):
        """Handles color logic when adding or removing classes.

        When in automatic interval mode with manual colors, regenerates
        the palette emulation based on current colors and applies it.
        Otherwise, falls back to standard color logic.
        """
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and colorMode == "Manual":
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)
                rows = self.tableView.rowCount()
                if rows > 0:
                    colors = self.calculateEmulatedPaletteColors(rows, currentColors)
                    self.applyColorsToTable(colors)
            return

        self.applyColorLogic()

    def handleSizeLogicOnClassChange(self, isRemoval=False):
        """Handles size logic when adding or removing classes.

        When in automatic interval mode with manual sizes:
        - For removal: Updates the palette anchors with current sizes (don't regenerate)
        - For addition: Generates interpolated sizes from existing palette
        Otherwise, falls back to standard size logic.
        """
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and sizeMode == "Manual":
            if isRemoval:
                currentSizes = self.collectCurrentTableSizes()
                if len(currentSizes) >= 2:
                    self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)
            else:
                if self.sizePaletteEmulator.isValidPalette():
                    rows = self.tableView.rowCount()
                    if rows > 0:
                        sizes = self.sizePaletteEmulator.generate(rows)
                        if sizes:
                            self.applySizesToTable(sizes)
            return

        self.applySizeLogic()

    def algorithmPalette(self, paletteRamp, numClasses):
        """Interpolates colors from a discrete palette for the specified number of classes."""
        if numClasses < 1:
            return []

        palColors = paletteRamp.colors()
        if not palColors:
            return [QColor("black")] * numClasses

        numColPaleta = len(palColors)

        increment = 0.0
        if numClasses > 1:
            increment = (numColPaleta - 1) / (numClasses - 1)

        indColor = []
        for i in range(numClasses):
            idx = int(math.floor(increment * i))
            idx = max(0, min(idx, numColPaleta - 1))
            indColor.append(idx)

        finalColors = [QColor()] * numClasses

        i = 0
        while i < numClasses:
            currentPalIdx = indColor[i]

            j = i
            while j < numClasses and indColor[j] == currentPalIdx:
                j += 1

            groupSize = j - i

            colorStart = palColors[currentPalIdx]
            if currentPalIdx + 1 < numColPaleta:
                colorEnd = palColors[currentPalIdx + 1]
            else:
                colorEnd = colorStart

            for k in range(groupSize):
                globalIdx = i + k
                factor = (k) / (groupSize + 1) if (groupSize + 1) > 0 else 0

                r = int(
                    colorStart.red()
                    + (colorEnd.red() - colorStart.red()) * factor
                )
                g = int(
                    colorStart.green()
                    + (colorEnd.green() - colorStart.green()) * factor
                )
                b = int(
                    colorStart.blue()
                    + (colorEnd.blue() - colorStart.blue()) * factor
                )

                finalColors[globalIdx] = QColor(r, g, b)

            i = j

        return finalColors

    def algorithmRamp(self, gradientRamp, numClasses):
        if numClasses < 1:
            return []

        colors = []
        for i in range(numClasses):
            position = 0.0
            if numClasses > 1:
                position = i / (numClasses - 1)
            colors.append(gradientRamp.color(position))

        return colors

    def syncColorRampButton(self):
        self.btnColorRamp.clearRamps()
        mode = self.cbColors.currentText()

        if mode == "Ramp":
            ramps = self.loadGradientRampsFromStyle()
        elif mode == "Palette":
            ramps = self.loadPaletteRampsFromStyle()
        else:
            return

        if ramps:
            self.btnColorRamp.addColorRamps(ramps)
            firstName = list(ramps.keys())[0]
            self.btnColorRamp.setActiveRampByName(firstName)

    def loadGradientRampsFromStyle(self):
        ramps = {}

        if self.style:
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsGradientColorRamp):
                    ramps[name] = ramp

        if not ramps:
            ramps["Default (Blue to Red)"] = QgsGradientColorRamp(QColor(0, 0, 255), QColor(255, 0, 0))
            ramps["Default (Green to Yellow)"] = QgsGradientColorRamp(QColor(0, 128, 0), QColor(255, 255, 0))

        return ramps

    def loadPaletteRampsFromStyle(self):
        ramps = {}

        if self.style:
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsPresetSchemeColorRamp):
                    ramps[name] = ramp

        if not ramps:
            primaryColors = [
                QColor(255, 0, 0),
                QColor(0, 255, 0),
                QColor(0, 0, 255),
                QColor(255, 255, 0),
                QColor(255, 0, 255),
                QColor(0, 255, 255),
            ]
            ramps["Primary Colors"] = QgsPresetSchemeColorRamp(primaryColors)

            warmColors = [
                QColor(255, 87, 51),
                QColor(255, 140, 0),
                QColor(255, 195, 0),
                QColor(220, 60, 60),
                QColor(255, 165, 79),
                QColor(238, 130, 98),
            ]
            ramps["Warm Colors"] = QgsPresetSchemeColorRamp(warmColors)

        return ramps

    # ============================================================
    # LAYER AND GROUP MANAGEMENT
    # ============================================================

    def populateGroups(self):
        self.cbGroups.blockSignals(True)
        self.cbGroups.clear()

        groups = []
        self.collectGroupsRecursive(QgsProject.instance().layerTreeRoot(), [], groups)

        for name, path, _ in groups:
            self.cbGroups.addItem(name, path)

        self.cbGroups.blockSignals(False)

        if self.cbGroups.count() == 0:
            self.handleEmptyGroupState()

    def handleEmptyGroupState(self):
        self.cbGroups.setCurrentIndex(-1)

        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(list(QgsProject.instance().mapLayers().values()))
        self.cbLegendLayer.setLayer(None)
        self.cbLegendLayer.blockSignals(False)

        self.frameLegends.setEnabled(False)
        self.labelFrameLegends.setText(self.tr("Legend"))
        self.onLayerChanged(None)

    def collectGroupsRecursive(self, parent, pathParts, results):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                currentPath = pathParts + [child.name()]
                identifier = child.customProperty("qgisred_identifier")

                if (
                    child.isVisible()
                    and identifier in self.ALLOWED_GROUP_IDENTIFIERS
                ):
                    isResultsGroup = identifier == "qgisred_results" # Results group bypasses empty layer check (layers are in subgroups)
                    if isResultsGroup or self.groupHasVisibleLayers(child):
                        results.append((currentPath[-1], " / ".join(currentPath), child))

                self.collectGroupsRecursive(child, currentPath, results)

    def groupHasVisibleLayers(self, group):
        return any(
            isinstance(child, QgsLayerTreeLayer) and child.isVisible()
            for child in group.children()
        )

    def getRenderableLayersInSelectedGroup(self):
        path = self.cbGroups.currentData()
        if not path:
            return []

        group = self.findGroupByPath(path)
        if not group:
            return []

        # Check if this is a qgisred_results group to enable recursive layer collection
        identifier = group.customProperty("qgisred_identifier")
        isResultsGroup = identifier == "qgisred_results"

        layers = []
        self.collectRenderableLayersRecursive(group, layers, isResultsGroup)

        return layers

    def collectRenderableLayersRecursive(self, group, layers, recurseIntoSubgroups):
        """Collects renderable layers from a group, optionally recursing into subgroups."""
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer) and child.isVisible():
                layer = child.layer()
                if (
                    layer
                    and isinstance(layer, QgsVectorLayer)
                    and layer.renderer().type()
                    in ("graduatedSymbol", "categorizedSymbol")
                ):
                    layers.append(layer)
            elif isinstance(child, QgsLayerTreeGroup) and recurseIntoSubgroups:
                # Recursively collect layers from nested subgroups
                self.collectRenderableLayersRecursive(child, layers, recurseIntoSubgroups)

    def findGroupByPath(self, pathStr):
        current = QgsProject.instance().layerTreeRoot()
        for part in pathStr.split(" / "):
            found = next((child for child in current.children() if isinstance(child, QgsLayerTreeGroup) and child.name().strip() == part.strip()), None)
            if not found:
                return None
            current = found
        return current

    def preselectGroupAndLayer(self):
        if not self.cbGroups.count():
            return

        activeLayer = self.getActiveLayerFromTree()
        targetGroup = None
        targetLayer = None

        if activeLayer:
            targetGroup = self.findGroupPathForLayer(activeLayer)
            if targetGroup:
                targetLayer = activeLayer.layer()

        if not targetGroup:
            targetGroup = self.cbGroups.itemData(0)

        self.setGroupByPath(targetGroup)
        self.onGroupChanged()

        if targetLayer:
            self.cbLegendLayer.setLayer(targetLayer)
        else:
            layers = self.getRenderableLayersInSelectedGroup()
            if layers:
                self.cbLegendLayer.setLayer(layers[0])

    def getActiveLayerFromTree(self):
        if iface and iface.layerTreeView():
            selectedLayers = iface.layerTreeView().selectedLayers()
            if selectedLayers:
                return QgsProject.instance().layerTreeRoot().findLayer(selectedLayers[0])
        return None

    def findGroupPathForLayer(self, layerNode):
        parent = layerNode.parent()
        while parent and not isinstance(parent, QgsLayerTreeGroup):
            parent = parent.parent()

        if isinstance(parent, QgsLayerTreeGroup):
            path = self.buildGroupPath(parent)
            for i in range(self.cbGroups.count()):
                if self.cbGroups.itemData(i) == path:
                    return path

        return None

    def buildGroupPath(self, group):
        parts = []
        current = group
        while current and current.parent():
            parts.insert(0, current.name())
            current = current.parent()
        return " / ".join(parts)

    def setGroupByPath(self, path):
        for i in range(self.cbGroups.count()):
            if self.cbGroups.itemData(i) == path:
                self.cbGroups.setCurrentIndex(i)
                break

    # ============================================================
    # TABLE POPULATION
    # ============================================================

    def populateClassificationModes(self):
        self.cbMode.blockSignals(True)
        self.cbMode.clear()
        self.cbMode.addItem("Manual", None)

        modes = [
            ("EqualInterval", "Equal Interval"),
            ("FixedInterval", "Fixed Interval"),
            ("Quantile", "Quantile (Equal Count)"),
            ("Jenks", "Natural Breaks (Jenks)"),
            ("StdDev", "Standard Deviation"),
            ("Pretty", "Pretty Breaks"),
        ]

        for modeId, modeName in modes:
            self.cbMode.addItem(self.tr(modeName), modeId)

        self.cbMode.blockSignals(False)

    def populateLegendTypes(self, layer=None):
        self.cbLegendsType.blockSignals(True)
        self.cbLegendsType.clear()

        if not layer:
            self.addDefaultLegendTypes()
        else:
            self.addLayerSpecificLegendTypes(layer)

        self.cbLegendsType.blockSignals(False)

    def addDefaultLegendTypes(self):
        self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")
        self.cbLegendsType.addItem(self.tr("Categorized"), "categorizedSymbol")
        self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")

    def addLayerSpecificLegendTypes(self, layer):
        layerIdentifier = layer.customProperty("qgisred_identifier")
        currentRendererType = layer.renderer().type() if layer.renderer() else "singleSymbol"

        supportsCategorized = False
        if self.utils:
            supportsCategorized = self.utils.getLayerSupportsCategorized(layerIdentifier)

        if supportsCategorized:
            self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif currentRendererType == "categorizedSymbol":
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif currentRendererType == "graduatedSymbol":
            self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
        else:
            self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")

    def detectFieldType(self, layer):
        renderer = layer.renderer()

        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            return self.FIELD_TYPE_NUMERIC, renderer.classAttribute()

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            fieldName = renderer.classAttribute()
            fieldIdx = layer.fields().indexOf(fieldName)

            if fieldIdx >= 0 and layer.fields().field(fieldIdx).type() in [
                QVariant.Int,
                QVariant.Double,
                QVariant.LongLong,
            ]:
                return self.FIELD_TYPE_NUMERIC, fieldName

            return self.FIELD_TYPE_CATEGORICAL, fieldName

        return self.FIELD_TYPE_UNKNOWN, None

    def resetToEmptyState(self):
        self.frameLegends.setEnabled(False)
        self.labelFrameLegends.setVisible(False)
        self.currentLayer = None
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.clearTable()
        self.updateUiBasedOnFieldType()

    def clearTable(self):
        self.tableView.setRowCount(0)
        self.updateClassCount()

    def populateNumericLegend(self):
        if not self.currentLayer:
            return

        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return

        self.clearTable()
        geometryHint = self.getGeometryHint()

        for i, rangeItem in enumerate(renderer.ranges()):
            self.tableView.insertRow(i)
            valueText = f"{rangeItem.lowerValue():.2f} - {rangeItem.upperValue():.2f}"

            self.setRowWidgets(
                i,
                rangeItem.symbol(),
                rangeItem.renderState(),
                valueText,
                rangeItem.label(),
                geometryHint,
            )

        self.updateClassCount()

    def populateCategoricalLegend(self):
        if not self.currentLayer:
            return

        renderer = self.currentLayer.renderer()
        self.clearTable()

        self.usedUniqueValues = []
        self.availableUniqueValues = self.getUniqueValuesFromLayer()

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            categories = renderer.categories()
            otherCategory = None
            geometryHint = self.getGeometryHint()

            for category in categories:
                if category.value() == "" or category.label() in [
                    self.tr("Other Values"),
                    "Other Values",
                ]:
                    otherCategory = category
                    continue

                valueStr = str(category.value()) if category.value() is not None else "NULL"

                if valueStr in self.availableUniqueValues:
                    self.usedUniqueValues.append(valueStr)

                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(
                    row,
                    category.symbol(),
                    category.renderState(),
                    valueStr,
                    category.label(),
                    geometryHint,
                    isReadOnlyValue=True,
                )

            if otherCategory:
                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(
                    row,
                    otherCategory.symbol(),
                    otherCategory.renderState(),
                    self.tr("Other Values"),
                    otherCategory.label(),
                    geometryHint,
                    isReadOnlyValue=True,
                )

        self.availableUniqueValues = [v for v in self.availableUniqueValues if v not in self.usedUniqueValues]
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def setRowWidgets(
        self,
        row,
        symbol,
        visible,
        valueText,
        legendText,
        geometryHint,
        isReadOnlyValue=False,
    ):
        self.setCheckboxWidget(row, visible)
        self.setColorWidget(row, symbol, geometryHint)
        self.setSizeWidget(row, symbol, geometryHint)
        self.setValueWidget(row, valueText, isReadOnlyValue)
        self.setLegendWidget(row, legendText)

    def setCheckboxWidget(self, row, visible):
        checkbox = QCheckBox(self.tableView)
        checkbox.setChecked(visible)
        checkbox.installEventFilter(self.rowSelectionFilter)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(checkbox, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, 0, container)

    def setColorWidget(self, row, symbol, geometryHint):
        # For marker symbols, symbol.color() doesn't reliably return fill color
        # Get color from symbol layer instead
        if symbol.symbolLayerCount() > 0:
            color = symbol.symbolLayer(0).color()
        else:
            color = symbol.color()

        colorSelector = QGISRedSymbolColorSelector(
            self.tableView,
            geometryHint,
            color,
            True,
            "Pick color",
            doubleClickOnly=True,
        )
        colorSelector.setEnabled(self.isEditing)
        colorSelector.colorChanged.connect(self.onRowColorChanged)

        size = symbol.width() if geometryHint == "line" else symbol.size()
        colorSelector.updateSymbolSize(size, geometryHint == "line")
        colorSelector.setAutoFillBackground(False)
        colorSelector.setFixedSize(30, 20)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        colorSelector.installEventFilter(self.rowSelectionFilter)
        layout.addStretch()
        layout.addWidget(colorSelector, 0, Qt.AlignVCenter)
        layout.addStretch()
        container.setAutoFillBackground(False)
        container.installEventFilter(self.rowSelectionFilter)

        self.tableView.setCellWidget(row, 1, container)

    def setSizeWidget(self, row, symbol, geometryHint):
        size = symbol.width() if geometryHint == "line" else symbol.size()
        sizeWidget = QLineEdit(str(size))
        sizeWidget.setEnabled(self.isEditing)
        sizeWidget.setAlignment(Qt.AlignCenter)
        sizeWidget.setStyleSheet(self.getBaseLineEditStyle())
        sizeWidget.installEventFilter(self.rowSelectionFilter)
        sizeWidget.textChanged.connect(lambda text, r=row: self.onSizeChanged(r, text))

        self.tableView.setCellWidget(row, 2, sizeWidget)

    def setValueWidget(self, row, valueText, isReadOnlyValue):
        valueWidget = QLineEdit(valueText)
        valueWidget.setReadOnly(True)
        valueWidget.setAlignment(Qt.AlignCenter)

        if isReadOnlyValue:
            valueWidget.setStyleSheet(self.getReadOnlyLineEditStyle())
        else:
            valueWidget.setStyleSheet(self.getBaseLineEditStyle())
            valueWidget.mouseDoubleClickEvent = lambda event, r=row: self.openRangeEditor(r)

        valueWidget.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, 3, valueWidget)

    def setLegendWidget(self, row, legendText):
        legendWidget = QLineEdit(legendText)
        legendWidget.setEnabled(self.isEditing)
        legendWidget.setStyleSheet(self.getBaseLineEditStyle())
        legendWidget.installEventFilter(self.rowSelectionFilter)

        self.tableView.setCellWidget(row, 4, legendWidget)

    def getBaseLineEditStyle(self):
        return """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #2b2b2b;
            }
            QLineEdit:focus {
                border: 1px solid #3399ff;
            }
        """

    def getReadOnlyLineEditStyle(self):
        return """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #808080;
            }
        """

    def getUniqueValuesFromLayer(self):
        if not self.currentLayer or not self.currentFieldName:
            return []

        # For results layers, get values from the All shapefile
        if self.isResultsLayer():
            resultsValues = self.getResultsUniqueValues()
            if resultsValues:
                return resultsValues

        # Original implementation for non-results layers
        fieldIdx = self.currentLayer.fields().indexOf(self.currentFieldName)
        if fieldIdx < 0:
            return []

        values = set()
        for feature in self.currentLayer.getFeatures():
            value = feature[self.currentFieldName]
            values.add(str(value) if value is not None else "NULL")

        specialValues = ["NULL", "#NA"]
        regularValues = [v for v in values if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in values]

        return sorted(regularValues) + foundSpecials

    # ============================================================
    # CLASS MANIPULATION - ADD
    # ============================================================

    def onAddClassClicked(self):
        if not self.currentLayer:
            return

        if self.addClassClickTimer and self.addClassClickTimer.isActive():
            self.addClassClickTimer.stop()
            self.addClassClickTimer = None

            if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
                self.ensureOtherValuesCategory()
            return

        self.addClassClickTimer = QTimer()
        self.addClassClickTimer.setSingleShot(True)
        self.addClassClickTimer.timeout.connect(self.onSingleClickAdd)
        self.addClassClickTimer.start(250)

    def onSingleClickAdd(self):
        self.addClassClickTimer = None
        self.addClassBeforeSelection = False
        self.executeAddClass()

    def executeAddClass(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.addCategoricalClass()
        else:
            self.addNumericClass()
            modeId = self.cbMode.currentData()
            if modeId and modeId != "Manual" and modeId != "FixedInterval":
                self.applyClassificationMethod(modeId)

        self.updateButtonStates()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange()

    def addNumericClass(self):
        if self.tableView.rowCount() >= self.MAX_CLASSES:
            self.showMaxClassesError()
            return

        selectedRows = self.getSelectedRows()
        if len(selectedRows) > 1:
            self.tableView.clearSelection()
            selectedRows = []

        insertionRow = self.calculateNumericInsertionRow(selectedRows)
        lower, upper = self.calculateInitialRangeForNewRow(insertionRow)

        modeId = self.cbMode.currentData()
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        isManualMode = modeId is None or modeId == "Manual"

        if isManualMode and colorMode == "Manual":
            newColor = self.getSmartColorForNewRow(insertionRow)
        else:
            newColor = self.generateRandomColor()

        if isManualMode and sizeMode == "Manual":
            smartSize = self.getSmartSizeForNewRow(insertionRow)
        else:
            smartSize = None

        self.tableView.insertRow(insertionRow)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(newColor)

        if smartSize is not None:
            if self.currentLayer.geometryType() == 1:
                symbol.setWidth(smartSize)
            else:
                symbol.setSize(smartSize)
        else:
            self.setDefaultSymbolSize(symbol)

        valueText = f"{lower:.2f} - {upper:.2f}"
        self.setRowWidgets(
            insertionRow,
            symbol,
            True,
            valueText,
            valueText,
            self.getGeometryHint(),
        )

        self.updateAdjacentRowsAfterInsertion(insertionRow, lower, upper)

        if isManualMode and sizeMode == "Manual":
            self.smoothEdgeSizeAfterInsertion(insertionRow)

        self.tableView.clearSelection()
        self.tableView.selectRow(insertionRow)
        self.updateClassCount()
        self.refreshAllLegendLabels()

    def calculateNumericInsertionRow(self, selectedRows):
        if selectedRows and len(selectedRows) == 1:
            row = selectedRows[0]
            if not self.addClassBeforeSelection:
                row += 1
            return row
        return self.tableView.rowCount()

    def addCategoricalClass(self):
        if self.tableView.rowCount() >= self.MAX_CLASSES:
            self.showMaxClassesError()
            return

        if not self.availableUniqueValues:
            QMessageBox.information(self, "Info", "All values used.")
            return

        value = self.availableUniqueValues.pop(0)
        self.usedUniqueValues.append(value)

        insertionRow = self.calculateCategoricalInsertionRow()

        self.tableView.insertRow(insertionRow)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(self.generateRandomColor())
        self.setDefaultSymbolSize(symbol)

        displayValue = str(value)
        unitAbbr = self.getCurrentLayerUnitAbbr()
        legendText = f"{value} {unitAbbr}" if unitAbbr else displayValue

        self.setRowWidgets(
            insertionRow,
            symbol,
            True,
            displayValue,
            legendText,
            self.getGeometryHint(),
            isReadOnlyValue=True,
        )

        self.tableView.clearSelection()
        self.tableView.selectRow(insertionRow)
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def calculateCategoricalInsertionRow(self):
        selectedRows = self.getSelectedRows()
        insertionRow = self.tableView.rowCount()

        if self.hasOtherValuesCategory():
            insertionRow -= 1

        if selectedRows and len(selectedRows) == 1:
            selectedWidget = self.tableView.cellWidget(selectedRows[0], 3)
            if isinstance(selectedWidget, QLineEdit) and selectedWidget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                insertionRow = selectedRows[0]
            elif self.addClassBeforeSelection:
                insertionRow = selectedRows[0]
            else:
                insertionRow = selectedRows[0] + 1

        return insertionRow

    def setDefaultSymbolSize(self, symbol):
        geometryType = self.currentLayer.geometryType()
        if geometryType == 0:
            symbol.setSize(3)
        elif geometryType == 1:
            symbol.setWidth(0.4)
        else:
            symbol.setSize(1.5)

    def classifyAllUniqueValues(self):
        uniqueCountToAdd = len(self.availableUniqueValues)

        if uniqueCountToAdd == 0:
            QMessageBox.information(
                self, self.tr("Info"), self.tr("All values are already classified.")
            )
            return

        currentCount = self.tableView.rowCount()
        totalPotential = currentCount + uniqueCountToAdd

        if totalPotential > self.MAX_CLASSES:
            QMessageBox.critical(
                self,
                self.tr("Limit Exceeded"),
                self.tr(
                    f"Adding {uniqueCountToAdd} classes would result in {totalPotential} total classes,\n"
                    f"which exceeds the maximum limit of {self.MAX_CLASSES}."
                ),
            )
            return

        self.tableView.setUpdatesEnabled(False)
        self.tableView.blockSignals(True)

        progress = None
        useProgress = uniqueCountToAdd > self.WARN_CLASSES

        if useProgress:
            progress = QProgressDialog(
                self.tr("Adding classes..."),
                self.tr("Cancel"),
                0,
                uniqueCountToAdd,
                self,
            )
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

        try:
            count = 0
            while self.availableUniqueValues:
                self.addCategoricalClass()
                count += 1

                if useProgress:
                    progress.setValue(count)
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        break

            self.removeOtherValuesRows()

        finally:
            if progress:
                progress.close()

            self.tableView.blockSignals(False)
            self.tableView.setUpdatesEnabled(True)

            self.updateClassCount()
            self.updateButtonStates()
            self.handleColorLogicOnClassChange()
            self.handleSizeLogicOnClassChange()

    def removeOtherValuesRows(self):
        for row in reversed(range(self.tableView.rowCount())):
            widget = self.tableView.cellWidget(row, 3)
            if isinstance(widget, QLineEdit) and widget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                self.tableView.removeRow(row)

    def showMaxClassesError(self):
        QMessageBox.critical(
            self,
            self.tr("Limit Exceeded"),
            self.tr(f"Maximum of {self.MAX_CLASSES} classes reached."),
        )

    # ============================================================
    # CLASS MANIPULATION - REMOVE AND MOVE
    # ============================================================

    def removeClass(self):
        rows = sorted(self.getSelectedRows(), reverse=True)
        if not rows:
            return

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.removeCategoricalRows(rows)
        else:
            self.removeNumericRows(rows)

        self.updateClassCount()
        self.refreshAllLegendLabels()
        self.updateButtonStates()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange(isRemoval=True)

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.updateClassCountLimits()

    def removeCategoricalRows(self, rows):
        for row in rows:
            widget = self.tableView.cellWidget(row, 3)
            if isinstance(widget, QLineEdit):
                value = widget.text()
                if (
                    value != self.tr("Other Values")
                    and value in self.usedUniqueValues
                ):
                    self.usedUniqueValues.remove(value)
                    self.availableUniqueValues.append(value)
            self.tableView.removeRow(row)

        self.sortAvailableUniqueValues()

    def removeNumericRows(self, rows):
        lowestRow = rows[-1]
        for row in rows:
            self.tableView.removeRow(row)
        self.mergeAdjacentRowsAfterDeletion(lowestRow)

    def removeCategoricalRow(self, row):
        widget = self.tableView.cellWidget(row, 3)
        if isinstance(widget, QLineEdit):
            value = widget.text()
            if value != self.tr("Other Values") and value in self.usedUniqueValues:
                self.usedUniqueValues.remove(value)
                self.availableUniqueValues.append(value)

        self.tableView.removeRow(row)
        self.sortAvailableUniqueValues()
        self.updateButtonStates()

    def sortAvailableUniqueValues(self):
        specialValues = ["NULL", "#NA"]
        regularValues = [value for value in self.availableUniqueValues if value not in specialValues]
        foundSpecials = [value for value in specialValues if value in self.availableUniqueValues]
        self.availableUniqueValues = sorted(regularValues) + foundSpecials

    def moveClassUp(self):
        self.moveRow(-1)

    def moveClassDown(self):
        self.moveRow(1)

    def moveRow(self, offset):
        rows = self.getSelectedRows()
        if len(rows) != 1:
            return

        row = rows[0]
        if not (0 <= row + offset < self.tableView.rowCount()):
            return

        self.swapTableRows(row, row + offset)
        self.tableView.selectRow(row + offset)

    def swapTableRows(self, row1, row2):
        data1 = self.getRowData(row1)
        data2 = self.getRowData(row2)
        self.setRowData(row1, data2)
        self.setRowData(row2, data1)

    def getRowData(self, row):
        data = []

        for column in range(5):
            widget = self.tableView.cellWidget(row, column)

            if column == 0:
                data.append(self.extractCheckboxData(widget))
            elif column == 1:
                data.append(self.extractColorSelectorData(widget))
            elif isinstance(widget, QLineEdit):
                hasDoubleClick = (
                    column == 3
                    and hasattr(widget, "mouseDoubleClickEvent")
                    and widget.mouseDoubleClickEvent.__name__ == "<lambda>"
                )
                data.append(("le", widget.text(), widget.isReadOnly(), hasDoubleClick))
            else:
                data.append(None)

        return data

    def extractCheckboxData(self, widget):
        if widget:
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                return ("ck", checkbox.isChecked())
        return None

    def extractColorSelectorData(self, widget):
        if widget:
            colorSelector = widget.findChild(QGISRedSymbolColorSelector)
            if colorSelector:
                return (
                    "cs",
                    colorSelector.activeColor,
                    colorSelector.currentSymbolSize,
                    colorSelector.geometryType,
                )
        return None

    def setRowData(self, row, data):
        for column, columnData in enumerate(data):
            if not columnData:
                continue

            dataType = columnData[0]

            if dataType == "ck":
                self.recreateCheckboxWidget(row, column, columnData[1])
            elif dataType == "cs":
                self.recreateColorSelectorWidget(row, column, columnData)
            elif dataType == "le":
                self.recreateLineEditWidget(row, column, columnData)

    def recreateCheckboxWidget(self, row, column, isChecked):
        checkbox = QCheckBox(self.tableView)
        checkbox.setChecked(isChecked)
        checkbox.installEventFilter(self.rowSelectionFilter)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(checkbox, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, column, container)

    def recreateColorSelectorWidget(self, row, column, data):
        color = data[1]
        symbolSize = data[2]
        geometryHint = data[3]

        colorSelector = QGISRedSymbolColorSelector(
            self.tableView,
            geometryHint,
            color,
            True,
            "Pick color",
            doubleClickOnly=True,
        )
        colorSelector.setEnabled(self.isEditing)
        colorSelector.updateSymbolSize(symbolSize, geometryHint == "line")
        colorSelector.setAutoFillBackground(False)
        colorSelector.setFixedSize(30, 20)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(colorSelector)
        layout.addStretch()
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, column, container)

    def recreateLineEditWidget(self, row, column, data):
        text = data[1]
        isReadOnly = data[2]
        hasDoubleClick = data[3] if len(data) > 3 else False

        lineEdit = QLineEdit(text)
        lineEdit.setEnabled(self.isEditing)

        if isReadOnly:
            lineEdit.setReadOnly(True)
            if column == 3:
                lineEdit.setAlignment(Qt.AlignCenter)
                if hasDoubleClick:
                    lineEdit.setStyleSheet(self.getBaseLineEditStyle())
                    lineEdit.mouseDoubleClickEvent = (
                        lambda event, r=row: self.openRangeEditor(r)
                    )
                else:
                    lineEdit.setStyleSheet(self.getReadOnlyLineEditStyle())
            else:
                lineEdit.setStyleSheet(self.getBaseLineEditStyle())
        else:
            lineEdit.setStyleSheet(self.getBaseLineEditStyle())

        if column == 2:
            lineEdit.setAlignment(Qt.AlignCenter)
            lineEdit.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))

        lineEdit.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, column, lineEdit)

    # ============================================================
    # NUMERIC CLASSIFICATION LOGIC
    # ============================================================

    def calculateInitialRangeForNewRow(self, row):
        """Determines range for new row using half-splitting logic for contiguous ranges."""
        total = self.tableView.rowCount()

        if total == 0:
            return self.getLayerMinMax()

        if total == 1:
            return self.calculateSplitRangeForSingleRow(row)

        return self.calculateSplitRangeForMultipleRows(row, total)

    def calculateSplitRangeForSingleRow(self, row):
        existing = self.getRangeValues(0)
        if existing:
            lower, upper = existing
            mid = (lower + upper) / 2.0
            if row == 0:
                return (lower, mid)
            else:
                return (mid, upper)
        return self.getLayerMinMax()

    def calculateSplitRangeForMultipleRows(self, row, total):
        if row == 0:
            splitRow = 0
        elif row >= total:
            splitRow = total - 1
        else:
            if self.addClassBeforeSelection:
                splitRow = row
            else:
                splitRow = row - 1

        targetRange = self.getRangeValues(splitRow)
        if targetRange:
            lower, upper = targetRange
            mid = (lower + upper) / 2.0

            if row <= splitRow:
                return (lower, mid)
            else:
                return (mid, upper)

        return self.getLayerMinMax()

    def getLayerMinMax(self):
        values = self.getNumericValues()
        if values and len(values) > 0:
            return (min(values), max(values))
        return (0.0, 1.0)

    def getRangeValues(self, row):
        widget = self.tableView.cellWidget(row, 3)
        if not isinstance(widget, QLineEdit):
            return None
        try:
            parts = widget.text().split(" - ")
            return float(parts[0]), float(parts[1])
        except:
            return None

    def updateAdjacentRowsAfterInsertion(self, row, newLower, newUpper):
        total = self.tableView.rowCount()

        if total == 2:
            self.handleTwoRowInsertion(row, newLower, newUpper)
            return

        if row > 0:
            prevRange = self.getRangeValues(row - 1)
            if prevRange:
                prevLower, prevUpper = prevRange
                if abs(prevUpper - newLower) < 0.0001 or prevUpper > newLower:
                    self.updateRangeValue(row - 1, None, newLower)

        if row < total - 1:
            nextRange = self.getRangeValues(row + 1)
            if nextRange:
                nextLower, nextUpper = nextRange
                if abs(nextLower - newUpper) < 0.0001 or nextLower < newUpper:
                    self.updateRangeValue(row + 1, newUpper, None)

    def handleTwoRowInsertion(self, row, newLower, newUpper):
        range0 = self.getRangeValues(0)
        range1 = self.getRangeValues(1)

        if range0 and range1:
            if row == 0:
                self.updateRangeValue(1, newUpper, None)
            else:
                self.updateRangeValue(0, None, newLower)

    def mergeAdjacentRowsAfterDeletion(self, rowPos):
        if rowPos > 0 and rowPos < self.tableView.rowCount():
            currentRange = self.getRangeValues(rowPos)
            if currentRange:
                self.updateRangeValue(rowPos - 1, None, currentRange[0])

    def updateRangeValue(self, row, newLower=None, newUpper=None):
        currentRange = self.getRangeValues(row)
        if not currentRange:
            return

        lower, upper = currentRange

        if newLower is not None:
            lower = newLower
        if newUpper is not None:
            upper = newUpper

        text = f"{lower:.2f} - {upper:.2f}"
        valueWidget = self.tableView.cellWidget(row, 3)

        if isinstance(valueWidget, QLineEdit):
            valueWidget.setText(text)

        self.updateLegendsValues(row, lower, upper)

    def updateLegendsValues(self, row, lower, upper):
        legendWidget = self.tableView.cellWidget(row, 4)
        if not isinstance(legendWidget, QLineEdit):
            return

        unitAbbr = self.getCurrentLayerUnitAbbr()
        totalRows = self.tableView.rowCount()
        decimalPlaces = self.calculateDecimalPlaces(totalRows)
        formatString = f"{{:.{decimalPlaces}f}}"

        if row == 0:
            newLegendText = self.formatFirstRowLegend(upper, formatString, unitAbbr)
        elif row == totalRows - 1:
            newLegendText = self.formatLastRowLegend(lower, formatString, unitAbbr)
        else:
            newLegendText = self.formatMiddleRowLegend(lower, upper, formatString, unitAbbr)

        legendWidget.setText(newLegendText)

    def calculateDecimalPlaces(self, totalRows):
        values = self.getNumericValues()
        if values and len(values) > 0:
            minValue, maxValue = min(values), max(values)
            try:
                precision = self.calculateLegendRoundingPrecision(minValue, maxValue, totalRows)
                return max(0, -precision)
            except ValueError:
                return 2
        return 2

    def formatFirstRowLegend(self, upper, formatString, unitAbbr):
        if unitAbbr:
            return f"< {formatString.format(upper)} {unitAbbr}"
        return f"< {formatString.format(upper)}"

    def formatLastRowLegend(self, lower, formatString, unitAbbr):
        if unitAbbr:
            return f"> {formatString.format(lower)} {unitAbbr}"
        return f"> {formatString.format(lower)}"

    def formatMiddleRowLegend(self, lower, upper, formatString, unitAbbr):
        if unitAbbr:
            return f"{formatString.format(lower)} < {formatString.format(upper)} {unitAbbr}"
        return f"{formatString.format(lower)} < {formatString.format(upper)}"

    def refreshAllLegendLabels(self):
        for row in range(self.tableView.rowCount()):
            values = self.getRangeValues(row)
            if values:
                self.updateLegendsValues(row, values[0], values[1])

    def calculateLegendRoundingPrecision(self, minValue, maxValue, intervals=10):
        """Calculates optimal rounding precision for legend values based on data range and interval count."""
        if intervals <= 0:
            raise ValueError("intervals must be > 0")
        if maxValue < minValue:
            raise ValueError("maxValue must be >= minValue")

        increment = (maxValue - minValue) / intervals
        meanAbs = (abs(minValue) + abs(maxValue)) / 2.0

        m1 = math.floor(math.log10(meanAbs) - 2 + 0.5) if meanAbs > 0 else 0
        m2 = math.floor(math.log10(increment)) if increment > 0 else 0

        return min(m1, m2)

    def calculateOptimalInterval(self):
        values = self.getNumericValues()
        if not values:
            return

        valueRange = max(values) - min(values)
        if valueRange == 0:
            self.spinIntervalRange.setValue(1.0)
            return

        target = valueRange / 5.0
        magnitude = math.floor(math.log10(target))
        mantissa = target / (10**magnitude)

        if mantissa <= 1.5:
            niceValue = 1
        elif mantissa <= 3:
            niceValue = 2
        elif mantissa <= 7:
            niceValue = 5
        else:
            niceValue = 10

        self.spinIntervalRange.blockSignals(True)
        self.spinIntervalRange.setValue(niceValue * (10**magnitude))
        self.spinIntervalRange.blockSignals(False)

    def applyClassificationMethod(self, methodId):
        """Applies the selected classification algorithm to generate class breaks."""
        values = self.getNumericValues()
        if not values:
            return

        numClasses = self.tableView.rowCount() or 5
        minValue, maxValue = min(values), max(values)

        previousColors = self.collectCurrentTableColors()

        breaks = self.calculateBreaksForMethod(methodId, values, numClasses, minValue, maxValue)

        if len(breaks) < 2:
            return

        numClasses = len(breaks) - 1
        self.adjustTableRowCount(numClasses)
        self.applyBreaksToTable(breaks, numClasses, minValue, maxValue)

        self.updateClassCount()
        self.applyColorLogic(previousColors=previousColors)
        self.handleSizeLogicOnClassChange()

    def calculateBreaksForMethod(self, methodId, values, numClasses, minValue, maxValue):
        if methodId == "EqualInterval":
            return self.calculateEqualIntervalBreaks(numClasses, minValue, maxValue)

        if methodId == "FixedInterval":
            return self.calculateFixedIntervalBreaks(minValue, maxValue)

        if methodId == "Quantile":
            return self.calculateQuantileBreaks(values, numClasses, minValue, maxValue)

        if methodId == "Jenks":
            return self.calculateJenksBreaks(numClasses, minValue)

        if methodId == "StdDev":
            return self.calculateStdDevBreaks(values, numClasses, minValue, maxValue)

        if methodId == "Pretty":
            return self.calculatePrettyBreaks(numClasses, minValue)

        return []

    def calculateEqualIntervalBreaks(self, numClasses, minValue, maxValue):
        step = (maxValue - minValue) / numClasses
        return [minValue + i * step for i in range(numClasses + 1)]

    def calculateFixedIntervalBreaks(self, minValue, maxValue):
        step = self.spinIntervalRange.value()
        breaks = [minValue]
        current = minValue
        while current < maxValue:
            current += step
            breaks.append(current)
        return breaks

    def calculateQuantileBreaks(self, values, numClasses, minValue, maxValue):
        breaks = [minValue]
        for i in range(1, numClasses):
            index = min(int(i / numClasses * len(values)), len(values) - 1)
            breaks.append(values[index])
        breaks.append(maxValue)
        return breaks

    def calculateJenksBreaks(self, numClasses, minValue):
        # For results layers, use values from All shapefile
        if self.isResultsLayer():
            allLayer = self.loadResultsAllLayer()
            fieldName = self.getResultFieldMapping()
            if allLayer and fieldName:
                classifier = QgsClassificationJenks()
                classifier.setLabelFormat("%1 - %2")
                classes = classifier.classes(allLayer, fieldName, numClasses)
                del allLayer
                return [minValue] + [cls.upperBound() for cls in classes]

        # Original implementation for non-results layers
        classifier = QgsClassificationJenks()
        classifier.setLabelFormat("%1 - %2")
        classes = classifier.classes(self.currentLayer, self.currentFieldName, numClasses)
        return [minValue] + [cls.upperBound() for cls in classes]

    def calculateStdDevBreaks(self, values, numClasses, minValue, maxValue):
        mean = statistics.mean(values)
        stdDev = statistics.stdev(values) if len(values) > 1 else 0

        breaks = [minValue, maxValue]
        for i in range(-numClasses // 2, numClasses // 2 + 1):
            breakValue = mean + i * stdDev
            if minValue < breakValue < maxValue:
                breaks.append(breakValue)

        return sorted(list(set(breaks)))

    def calculatePrettyBreaks(self, numClasses, minValue):
        # For results layers, use values from All shapefile
        if self.isResultsLayer():
            allLayer = self.loadResultsAllLayer()
            fieldName = self.getResultFieldMapping()
            if allLayer and fieldName:
                classifier = QgsClassificationPrettyBreaks()
                classes = classifier.classes(allLayer, fieldName, numClasses)
                del allLayer
                return [minValue] + [cls.upperBound() for cls in classes]

        # Original implementation for non-results layers
        classifier = QgsClassificationPrettyBreaks()
        classes = classifier.classes(self.currentLayer, self.currentFieldName, numClasses)
        return [minValue] + [cls.upperBound() for cls in classes]

    def adjustTableRowCount(self, targetCount):
        while self.tableView.rowCount() < targetCount:
            self.addNumericClass()
        while self.tableView.rowCount() > targetCount:
            self.tableView.removeRow(self.tableView.rowCount() - 1)

    def applyBreaksToTable(self, breaks, numClasses, minValue, maxValue):
        try:
            precision = self.calculateLegendRoundingPrecision(minValue, maxValue, numClasses)
            decimalPlaces = max(0, -precision)
        except ValueError:
            decimalPlaces = 2

        formatString = f"{{:.{decimalPlaces}f}}"
        unitAbbr = self.getCurrentLayerUnitAbbr()

        for i in range(numClasses):
            lower, upper = breaks[i], breaks[i + 1]
            valueText = f"{formatString.format(lower)} - {formatString.format(upper)}"

            valueWidget = self.tableView.cellWidget(i, 3)
            if isinstance(valueWidget, QLineEdit):
                valueWidget.setText(valueText)

            legendText = self.formatLegendForBreaks(i, numClasses, lower, upper, formatString, unitAbbr)
            legendWidget = self.tableView.cellWidget(i, 4)
            if isinstance(legendWidget, QLineEdit):
                legendWidget.setText(legendText)

    def formatLegendForBreaks(self, index, numClasses, lower, upper, formatString, unitAbbr):
        if index == 0:
            return self.formatFirstRowLegend(upper, formatString, unitAbbr)
        if index == numClasses - 1:
            return self.formatLastRowLegend(lower, formatString, unitAbbr)
        return self.formatMiddleRowLegend(lower, upper, formatString, unitAbbr)

    def getNumericValues(self):
        if not self.currentLayer or not self.currentFieldName:
            return []

        # For results layers, get values from the All shapefile
        if self.isResultsLayer():
            resultsValues = self.getResultsNumericValues()
            if resultsValues:
                return resultsValues

        # Original implementation for non-results layers
        values = []
        for feature in self.currentLayer.getFeatures():
            try:
                values.append(float(feature[self.currentFieldName]))
            except:
                pass

        return sorted(values)

    # ============================================================
    # RANGE EDITING
    # ============================================================

    def openRangeEditor(self, row):
        modeId = self.cbMode.currentData()
        if modeId and modeId != "Manual":
            return

        currentRange = self.getRangeValues(row)
        if not currentRange:
            return

        unitAbbr = self.getCurrentLayerUnitAbbr()
        dialog = QGISRedRangeEditDialog(currentRange[0], currentRange[1], self, unitAbbreviation=unitAbbr)

        if dialog.exec_():
            newLower, newUpper = dialog.getRangeValues()

            if not self.validateRangeEdit(row, newLower, newUpper):
                return

            self.updateRangeValue(row, newLower, newUpper)

            if row > 0:
                self.updateRangeValue(row - 1, None, newLower)
            if row < self.tableView.rowCount() - 1:
                self.updateRangeValue(row + 1, newUpper, None)

            if self.cbSizes.currentText() == "Proportional to Value":
                self.applySizeLogic()

    def validateRangeEdit(self, row, newLower, newUpper):
        if newLower >= newUpper:
            QMessageBox.warning(
                self, "Invalid Range", "Min value must be less than Max value."
            )
            return False

        if row > 0:
            prevRange = self.getRangeValues(row - 1)
            if prevRange and newLower < prevRange[0]:
                QMessageBox.warning(
                    self,
                    "Range Overflow",
                    f"New minimum ({newLower}) is smaller than the previous row's minimum ({prevRange[0]}).\nCannot apply changes.",
                )
                return False

        if row < self.tableView.rowCount() - 1:
            nextRange = self.getRangeValues(row + 1)
            if nextRange and newUpper > nextRange[1]:
                QMessageBox.warning(
                    self,
                    "Range Overflow",
                    f"New maximum ({newUpper}) is larger than the next row's maximum ({nextRange[1]}).\nCannot apply changes.",
                )
                return False

        return True

    def onSizeChanged(self, row, text):
        try:
            size = float(text)
            colorContainer = self.tableView.cellWidget(row, 1)
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if colorWidget:
                colorWidget.updateSymbolSize(size, self.currentLayer.geometryType() == 1)

            # Update size palette when in automatic interval mode with manual sizes
            sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
            modeId = self.cbMode.currentData()
            isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

            if isAutomaticIntervalMode and sizeMode == "Manual":
                currentSizes = self.collectCurrentTableSizes()
                if len(currentSizes) >= 2:
                    self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)
        except:
            pass

    # ============================================================
    # RENDERER CONVERSION
    # ============================================================

    def convertToCategorized(self, field):
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return

        uniqueValues = sorted(layer.uniqueValues(fieldIdx))
        categories = []

        unitAbbr = self.getUnitAbbrForLayer()

        for value in uniqueValues:
            if value is None or str(value) == "NULL":
                continue

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            color = self.generateRandomHsvColor()
            symbol.setColor(color)
            self.setSymbolSizeForGeometry(symbol, layer.geometryType())

            label = str(value)
            if unitAbbr:
                label = f"{value} {unitAbbr}"

            category = QgsRendererCategory(value, symbol, label)
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)

    def convertToGraduated(self, field):
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return

        minVal = layer.minimumValue(fieldIdx)
        maxVal = layer.maximumValue(fieldIdx)

        if minVal is None or maxVal is None:
            return

        numClasses = 5
        interval = (maxVal - minVal) / numClasses
        ranges = []

        startColor = QColor(0, 255, 0)
        endColor = QColor(255, 0, 0)

        for i in range(numClasses):
            lower = minVal + (i * interval)
            upper = minVal + ((i + 1) * interval)

            color = self.interpolateColor(startColor, endColor, i, numClasses)

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            self.setSymbolSizeForGeometry(symbol, layer.geometryType())

            label = f"{lower:.1f} - {upper:.1f}"
            rangeObj = QgsRendererRange(lower, upper, symbol, label)
            ranges.append(rangeObj)

        renderer = QgsGraduatedSymbolRenderer(field, ranges)
        layer.setRenderer(renderer)

    def interpolateColor(self, startColor, endColor, index, total):
        t = index / max(1, total - 1)
        return QColor(
            int(startColor.red() + t * (endColor.red() - startColor.red())),
            int(startColor.green() + t * (endColor.green() - startColor.green())),
            int(startColor.blue() + t * (endColor.blue() - startColor.blue())),
        )

    def setSymbolSizeForGeometry(self, symbol, geometryType):
        if geometryType == 1:
            symbol.setWidth(0.6)
        else:
            symbol.setSize(2.5)

    def applyColorToSymbol(self, symbol, color):
        """Applies color to all layers of a symbol, preserving its structure."""
        for i in range(symbol.symbolLayerCount()):
            symbolLayer = symbol.symbolLayer(i)
            symbolLayer.setColor(color)
            # Also set stroke color for fill symbols to maintain consistency
            if hasattr(symbolLayer, 'setStrokeColor'):
                symbolLayer.setStrokeColor(color)
            # Handle sub-symbols (e.g., marker line's marker symbol)
            if hasattr(symbolLayer, 'subSymbol') and symbolLayer.subSymbol():
                self.applyColorToSymbol(symbolLayer.subSymbol(), color)

    def applySizeToSymbol(self, symbol, size):
        """Applies size to a symbol, preserving its structure."""
        isLine = self.currentLayer.geometryType() == 1
        if isLine:
            symbol.setWidth(size)
        else:
            symbol.setSize(size)

    def getUnitAbbrForLayer(self):
        if self.utils:
            layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
            if layerIdentifier:
                return self.utils.getUnitAbbreviationForLayer(layerIdentifier)
        return ""

    def generateRandomHsvColor(self):
        return QColor.fromHsv(
            random.randint(0, 359),
            random.randint(150, 255),
            random.randint(150, 255),
        )

    # ============================================================
    # APPLY AND SAVE LEGEND
    # ============================================================

    def applyLegend(self):
        if not self.currentLayer:
            return

        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.applyNumericLegend()
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.applyCategoricalLegend()

        self.currentLayer.triggerRepaint()

    def applyNumericLegend(self):
        ranges = []
        isProportionalMode = self.cbSizes.currentText() == "Proportional to Value"

        # Get existing renderer to clone symbols from (preserving complex symbol structures)
        existingRenderer = self.currentLayer.renderer()
        existingRanges = existingRenderer.ranges() if isinstance(existingRenderer, QgsGraduatedSymbolRenderer) else []

        for row in range(self.tableView.rowCount()):
            values = self.getRangeValues(row)
            if not values:
                continue

            checkboxContainer = self.tableView.cellWidget(row, 0)
            colorContainer = self.tableView.cellWidget(row, 1)
            legendWidget = self.tableView.cellWidget(row, 4)
            sizeWidget = self.tableView.cellWidget(row, 2)

            checkbox = checkboxContainer.findChild(QCheckBox) if checkboxContainer else None
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            # Clone existing symbol to preserve complex structure, fallback to default
            if row < len(existingRanges) and existingRanges[row].symbol():
                symbol = existingRanges[row].symbol().clone()
            else:
                symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())

            if colorWidget:
                self.applyColorToSymbol(symbol, colorWidget.activeColor)

            try:
                size = float(sizeWidget.text())
                self.applySizeToSymbol(symbol, size)
            except:
                pass

            if isProportionalMode:
                self.applyProportionalSizeExpression(symbol)

            rangeObj = QgsRendererRange(
                values[0], values[1], symbol, legendWidget.text()
            )
            rangeObj.setRenderState(checkbox.isChecked() if checkbox else True)
            ranges.append(rangeObj)

        if ranges:
            self.currentLayer.setRenderer(QgsGraduatedSymbolRenderer(self.currentFieldName, ranges))

    def applyProportionalSizeExpression(self, symbol):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()
        _, globalValueMax = self.getLayerMinMax()

        if globalValueMax == 0:
            return

        fieldName = self.currentFieldName
        isLine = self.currentLayer.geometryType() == 1

        if self.ckSizeInvert.isChecked():
            expression = f'{maxSize} - ("{fieldName}" / {globalValueMax}) * ({maxSize} - {minSize})'
        else:
            expression = f'{minSize} + ("{fieldName}" / {globalValueMax}) * ({maxSize} - {minSize})'

        sizeProperty = QgsProperty.fromExpression(expression)

        for i in range(symbol.symbolLayerCount()):
            symbolLayer = symbol.symbolLayer(i)
            if isLine:
                symbolLayer.setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, sizeProperty)
            else:
                symbolLayer.setDataDefinedProperty(QgsSymbolLayer.PropertySize, sizeProperty)

    def applyCategoricalLegend(self):
        categories = []

        # Get existing renderer to clone symbols from (preserving complex symbol structures)
        existingRenderer = self.currentLayer.renderer()
        existingCategories = existingRenderer.categories() if isinstance(existingRenderer, QgsCategorizedSymbolRenderer) else []

        # Build a map of value -> symbol for quick lookup
        existingSymbolMap = {}
        for cat in existingCategories:
            catValue = str(cat.value()) if cat.value() is not None else "NULL"
            existingSymbolMap[catValue] = cat.symbol()

        for row in range(self.tableView.rowCount()):
            checkboxContainer = self.tableView.cellWidget(row, 0)
            colorContainer = self.tableView.cellWidget(row, 1)
            legendWidget = self.tableView.cellWidget(row, 4)
            valueWidget = self.tableView.cellWidget(row, 3)
            sizeWidget = self.tableView.cellWidget(row, 2)

            checkbox = checkboxContainer.findChild(QCheckBox) if checkboxContainer else None
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            value = valueWidget.text() if isinstance(valueWidget, QLineEdit) else ""
            label = legendWidget.text()

            realValue = self.determineRealCategoricalValue(value, label)

            # Clone existing symbol to preserve complex structure, fallback to default
            lookupKey = value if value not in [self.tr("Other Values"), "Other Values"] else ""
            if lookupKey in existingSymbolMap and existingSymbolMap[lookupKey]:
                symbol = existingSymbolMap[lookupKey].clone()
            else:
                symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())

            if colorWidget:
                self.applyColorToSymbol(symbol, colorWidget.activeColor)

            try:
                size = float(sizeWidget.text())
                self.applySizeToSymbol(symbol, size)
            except:
                pass

            category = QgsRendererCategory(realValue, symbol, label)
            category.setRenderState(checkbox.isChecked() if checkbox else True)
            categories.append(category)

        if categories:
            self.currentLayer.setRenderer(QgsCategorizedSymbolRenderer(self.currentFieldName, categories))

    def determineRealCategoricalValue(self, value, label):
        if value == "NULL":
            return None
        if value == "" and label in [self.tr("Other Values"), "Other Values"]:
            return ""
        return value

    # ============================================================
    # STYLE MANAGEMENT
    # ============================================================

    def saveProjectStyle(self):
        self.saveStyle(globalStyle=False)

    def saveGlobalStyle(self):
        self.saveStyle(globalStyle=True)

    def saveStyle(self, globalStyle):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            return

        name = self.getElementNameForIdentifier(identifier)
        if not name:
            return

        filename = name.replace(" ", "") + ".qml"
        folder = self.getStyleFolder(globalStyle)

        if not folder:
            return

        if not os.path.exists(folder):
            os.makedirs(folder)

        path = os.path.join(folder, filename)

        if os.path.exists(path):
            reply = QMessageBox.question(
                self,
                "Overwrite",
                "Overwrite style?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        self.currentLayer.saveNamedStyle(path)
        QMessageBox.information(self, "Saved", f"Style saved to {path}")

    def loadDefaultStyle(self):
        self.loadStyle(isDefault=True)

    def loadGlobalStyle(self):
        self.loadStyle(isDefault=False)

    def loadProjectStyle(self):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        name = self.getElementNameForIdentifier(identifier)

        if not name:
            return

        filename = name.replace(" ", "") + ".qml"
        projectDir = self.getProjectDirectoryFromUtils()

        if not projectDir:
            QMessageBox.warning(self, "No Project", "Project directory not set.")
            return

        folder = os.path.join(projectDir, "layerStyles")
        path = os.path.join(folder, filename)

        if not os.path.exists(path):
            QMessageBox.warning(self, "Not Found", f"Style file not found: {path}")
            return

        self.currentLayer.loadNamedStyle(path)
        self.currentLayer.triggerRepaint()
        self.onLayerChanged(self.currentLayer)
        QMessageBox.information(self, "Loaded", f"Style loaded from {path}")

    def loadStyle(self, isDefault):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        name = self.getElementNameForIdentifier(identifier)

        if not name:
            return

        filename = name.replace(" ", "") + ".qml" + (".bak" if isDefault else "")
        subfolder = os.path.join("defaults", "layerStyles") if isDefault else "layerStyles"
        path = os.path.join(self.pluginFolder, subfolder, filename)

        if not os.path.exists(path):
            QMessageBox.warning(self, "Not Found", f"Style file not found: {path}")
            return

        self.currentLayer.loadNamedStyle(path)
        self.currentLayer.triggerRepaint()
        self.onLayerChanged(self.currentLayer)
        QMessageBox.information(self, "Loaded", f"Style loaded from {path}")

    def getElementNameForIdentifier(self, identifier):
        if self.utils:
            return self.utils.identifierToElementName.get(identifier)
        return QGISRedUtils().identifierToElementName.get(identifier)

    def getStyleFolder(self, globalStyle):
        if globalStyle:
            return os.path.join(self.pluginFolder, "layerStyles")

        projectDir = self.getProjectDirectoryFromUtils()
        if not projectDir:
            QMessageBox.warning(self, "No Project", "Project directory not set.")
            return None

        return os.path.join(projectDir, "layerStyles")

    def getProjectDirectoryFromUtils(self):
        if self.utils:
            return self.utils.getProjectDirectory()
        return self.projectDirectory

    # ============================================================
    # UI STATE MANAGEMENT
    # ============================================================

    def resetAllModesToManual(self):
        self.cbMode.blockSignals(True)
        self.cbMode.setCurrentIndex(0)
        self.cbMode.blockSignals(False)

        self.cbSizes.blockSignals(True)
        self.cbSizes.setCurrentIndex(0)
        self.cbSizes.blockSignals(False)

        self.cbColors.blockSignals(True)
        self.cbColors.setCurrentIndex(0)
        self.cbColors.blockSignals(False)

        self.onSizeModeChanged()
        self.onColorModeChanged()

    def updateUiBasedOnFieldType(self):
        isNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC
        isCategorical = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
        isFixedInterval = isNumeric and self.cbMode.currentData() == "FixedInterval"
        isManualNumeric = isNumeric and (
            self.cbMode.currentData() is None
            or self.cbMode.currentData() == "Manual"
        )

        self.updateModeVisibility(isNumeric, isFixedInterval)
        self.updateClassButtonsVisibility(isCategorical, isNumeric, isFixedInterval)
        self.updateNavigationButtonsVisibility(isCategorical)
        self.updateClassCountEditability(isCategorical, isNumeric, isManualNumeric)
        self.updateAddClassTooltip(isCategorical, isNumeric)

        if isCategorical:
            self.updateAddClassButtonState()

        if self.currentFieldType != self.FIELD_TYPE_UNKNOWN:
            self.applySizeLogic()
            self.applyColorLogic()

    def updateModeVisibility(self, isNumeric, isFixedInterval):
        self.cbMode.setVisible(isNumeric)
        self.labelMode.setVisible(isNumeric)
        self.labelIntervalRange.setVisible(isFixedInterval)
        self.spinIntervalRange.setVisible(isFixedInterval)

    def updateClassButtonsVisibility(self, isCategorical, isNumeric, isFixedInterval):
        self.btClassPlus.setVisible(isCategorical or isNumeric)
        self.btClassMinus.setVisible(isCategorical or isNumeric)
        self.btClassPlus.setEnabled(not isFixedInterval)
        self.btClassMinus.setEnabled(not isFixedInterval)
        self.labelClass.setVisible(isCategorical or isNumeric)
        self.leClassCount.setVisible(isCategorical or isNumeric)
        self.labelFrameLegends.setVisible(isNumeric or isCategorical)
        self.btClassifyAll.setVisible(isCategorical)

    def updateNavigationButtonsVisibility(self, isCategorical):
        self.btUp.setVisible(isCategorical)
        self.btDown.setVisible(isCategorical)

    def updateClassCountEditability(self, isCategorical, isNumeric, isManualNumeric):
        if isCategorical:
            self.setClassCountEditable(False)
            self.updateClassCountLimits()
        elif isNumeric:
            self.setClassCountEditable(not isManualNumeric and self.modeHasVariableClassCount())
        else:
            self.setClassCountEditable(False)

    def updateAddClassTooltip(self, isCategorical, isNumeric):
        if isCategorical:
            self.btClassPlus.setToolTip(
                self.tr(
                    'Right-click: Add a new item above the current selection\n'
                    'Left-click: Add a new item below the current selection\n'
                    'Double-click: Add "Other values" option'
                )
            )
        elif isNumeric:
            self.btClassPlus.setToolTip(
                self.tr(
                    "Right-click: Add a new item above the current selection\n"
                    "Left-click: Add a new item below the current selection"
                )
            )

    def setClassCountEditable(self, editable):
        if editable:
            self.leClassCount.setReadOnly(False)
            self.leClassCount.setButtonSymbols(QSpinBox.UpDownArrows)
            self.leClassCount.setStyleSheet(
                "QSpinBox { background-color: white; color: #2b2b2b; }"
            )
        else:
            self.leClassCount.setReadOnly(True)
            self.leClassCount.setButtonSymbols(QSpinBox.NoButtons)
            self.leClassCount.setStyleSheet(
                "QSpinBox { background-color: #F0F0F0; color: #808080; }"
            )

    def modeHasVariableClassCount(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return True

        modeId = self.cbMode.currentData()
        fixedModes = ["FixedInterval", "StdDev"]
        return modeId not in fixedModes

    def updateClassCountLimits(self):
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return

        currentCount = self.tableView.rowCount()
        maxPossible = currentCount + len(self.availableUniqueValues)

        if not self.hasOtherValuesCategory():
            maxPossible += 1

        self.leClassCount.blockSignals(True)
        self.leClassCount.setMinimum(0)
        self.leClassCount.setMaximum(maxPossible)
        self.leClassCount.blockSignals(False)

    def updateButtonStates(self):
        if not self.currentLayer:
            return

        selectedRows = self.getSelectedRows()
        selectionCount = len(selectedRows)
        isCategorical = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL

        modeId = self.cbMode.currentData()
        isManualNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC and (
            modeId is None or modeId == "Manual"
        )
        isAutoNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC and not isManualNumeric

        self.updateAddButtonState(isCategorical, isAutoNumeric, isManualNumeric, selectionCount, modeId)
        self.updateRemoveButtonState(modeId, selectionCount)
        self.updateMoveButtonsState(isCategorical, selectionCount, selectedRows)

    def updateAddButtonState(self, isCategorical, isAutoNumeric, isManualNumeric, selectionCount, modeId):
        if modeId == "FixedInterval":
            self.btClassPlus.setEnabled(False)
            return

        if isCategorical:
            if selectionCount > 1:
                self.btClassPlus.setEnabled(False)
            else:
                self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())
        elif isAutoNumeric:
            self.btClassPlus.setEnabled(True)
        else:
            self.btClassPlus.setEnabled(selectionCount <= 1)

    def updateRemoveButtonState(self, modeId, selectionCount):
        if modeId == "FixedInterval":
            self.btClassMinus.setEnabled(False)
        else:
            self.btClassMinus.setEnabled(selectionCount >= 1)

    def updateMoveButtonsState(self, isCategorical, selectionCount, selectedRows):
        if isCategorical:
            canMove = selectionCount == 1
            if canMove:
                rowIndex = selectedRows[0]
                self.btUp.setEnabled(rowIndex > 0)
                self.btDown.setEnabled(rowIndex < self.tableView.rowCount() - 1)
            else:
                self.btUp.setEnabled(False)
                self.btDown.setEnabled(False)
        else:
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)

    def updateAddClassButtonState(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())

    def updateClassCount(self):
        self.leClassCount.setValue(self.tableView.rowCount())

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def getLayerUnits(self):
        if not self.utils:
            return ""

        try:
            return self.utils.getUnits()
        except:
            return ""

    def getGeometryHint(self):
        if not self.currentLayer:
            return "fill"

        geometryType = self.currentLayer.geometryType()
        if geometryType == 0:
            return "marker"
        if geometryType == 1:
            return "line"
        return "fill"

    def generateRandomColor(self):
        color = QColor()
        color.setHsl(
            random.randint(0, 359),
            random.randint(178, 255),
            random.randint(102, 178),
        )
        return color

    def getRowColor(self, row):
        if row < 0 or row >= self.tableView.rowCount():
            return None

        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector)
            if colorWidget:
                return colorWidget.activeColor
        return None

    def setRowColor(self, row, color):
        if row < 0 or row >= self.tableView.rowCount():
            return

        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector)
            if colorWidget:
                colorWidget.setSelectorColor(color)

    def getRowSize(self, row):
        """Gets the size value from a table row."""
        if row < 0 or row >= self.tableView.rowCount():
            return None

        sizeWidget = self.tableView.cellWidget(row, 2)
        if sizeWidget and isinstance(sizeWidget, QLineEdit):
            try:
                return float(sizeWidget.text())
            except (ValueError, TypeError):
                return None
        return None

    def setRowSize(self, row, size):
        """Sets the size value for a table row."""
        if row < 0 or row >= self.tableView.rowCount():
            return

        sizeWidget = self.tableView.cellWidget(row, 2)
        if sizeWidget and isinstance(sizeWidget, QLineEdit):
            sizeWidget.blockSignals(True)
            sizeWidget.setText(f"{size:.2f}")
            sizeWidget.blockSignals(False)

            colorContainer = self.tableView.cellWidget(row, 1)
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if colorWidget:
                colorWidget.updateSymbolSize(size, self.getGeometryHint() == "line")

    def getDefaultSize(self):
        """Returns the default size based on geometry type."""
        if not self.currentLayer:
            return 0.4

        geometryType = self.currentLayer.geometryType()
        if geometryType == 0:
            return 3.0
        elif geometryType == 1:
            return 0.4
        else:
            return 1.5

    def calculateIntermediateColor(self, color1, color2):
        return QColor(
            (color1.red() + color2.red()) // 2,
            (color1.green() + color2.green()) // 2,
            (color1.blue() + color2.blue()) // 2,
        )

    def calculateComplementaryColor(self, color):
        h, s, l, a = color.getHsl()
        complementaryHue = (h + 180) % 360
        complementaryColor = QColor()
        complementaryColor.setHsl(complementaryHue, s, l, a)
        return complementaryColor

    def getSmartColorForNewRow(self, insertionRow):
        """Determines intelligent color for new row based on position and existing colors."""
        rowCount = self.tableView.rowCount()

        if rowCount == 0:
            return self.generateRandomColor()

        if rowCount == 1:
            firstColor = self.getRowColor(0)
            if firstColor:
                return self.calculateComplementaryColor(firstColor)
            return self.generateRandomColor()

        if insertionRow == 0:
            firstColor = self.getRowColor(0)
            return firstColor if firstColor else self.generateRandomColor()

        if insertionRow >= rowCount:
            lastColor = self.getRowColor(rowCount - 1)
            return lastColor if lastColor else self.generateRandomColor()

        prevColor = self.getRowColor(insertionRow - 1)
        nextColor = self.getRowColor(insertionRow)

        if prevColor and nextColor:
            return self.calculateIntermediateColor(prevColor, nextColor)
        if prevColor:
            return prevColor
        if nextColor:
            return nextColor

        return self.generateRandomColor()

    def getSmartSizeForNewRow(self, insertionRow):
        """Determines intelligent size for new row based on position and existing sizes."""
        rowCount = self.tableView.rowCount()

        if rowCount == 0:
            return self.getDefaultSize()

        if rowCount == 1:
            existingSize = self.getRowSize(0)
            return existingSize if existingSize is not None else self.getDefaultSize()

        if insertionRow == 0:
            firstSize = self.getRowSize(0)
            return firstSize if firstSize is not None else self.getDefaultSize()

        if insertionRow >= rowCount:
            lastSize = self.getRowSize(rowCount - 1)
            return lastSize if lastSize is not None else self.getDefaultSize()

        prevSize = self.getRowSize(insertionRow - 1)
        nextSize = self.getRowSize(insertionRow)

        if prevSize is not None and nextSize is not None:
            return (prevSize + nextSize) / 2.0
        if prevSize is not None:
            return prevSize
        if nextSize is not None:
            return nextSize

        return self.getDefaultSize()

    def smoothEdgeColorAfterInsertion(self, insertedRow):
        """Applies edge color smoothing after insertion when there are 3+ classes."""
        rowCount = self.tableView.rowCount()

        if rowCount < 3:
            return

        if insertedRow == 0:
            self.smoothFirstRowInsertion(rowCount)
        elif insertedRow == rowCount - 1:
            self.smoothLastRowInsertion(rowCount)

    def smoothFirstRowInsertion(self, rowCount):
        newFirstColor = self.getRowColor(0)
        lastColor = self.getRowColor(rowCount - 1)

        if newFirstColor and lastColor:
            interpolatedColor = self.calculateIntermediateColor(newFirstColor, lastColor)
            self.setRowColor(1, interpolatedColor)

    def smoothLastRowInsertion(self, rowCount):
        newLastColor = self.getRowColor(rowCount - 1)

        antepenultimateColor = None
        if rowCount >= 3:
            antepenultimateColor = self.getRowColor(rowCount - 3)

        if newLastColor and antepenultimateColor:
            interpolatedColor = self.calculateIntermediateColor(newLastColor, antepenultimateColor)
            self.setRowColor(rowCount - 2, interpolatedColor)

    def smoothEdgeSizeAfterInsertion(self, insertedRow):
        """Applies edge size smoothing after insertion when there are 3+ classes."""
        rowCount = self.tableView.rowCount()

        if rowCount < 3:
            return

        if insertedRow == 0:
            self.smoothFirstRowSizeInsertion(rowCount)
        elif insertedRow == rowCount - 1:
            self.smoothLastRowSizeInsertion(rowCount)

    def smoothFirstRowSizeInsertion(self, rowCount):
        """Interpolate old first (now second) between new first and last."""
        newFirstSize = self.getRowSize(0)
        lastSize = self.getRowSize(rowCount - 1)

        if newFirstSize is not None and lastSize is not None:
            interpolatedSize = (newFirstSize + lastSize) / 2.0
            self.setRowSize(1, interpolatedSize)

    def smoothLastRowSizeInsertion(self, rowCount):
        """Interpolate old last (now second-to-last) between first and new last."""
        firstSize = self.getRowSize(0)
        newLastSize = self.getRowSize(rowCount - 1)

        if firstSize is not None and newLastSize is not None:
            interpolatedSize = (firstSize + newLastSize) / 2.0
            self.setRowSize(rowCount - 2, interpolatedSize)

    def getSelectedRows(self):
        return [idx.row() for idx in self.tableView.selectionModel().selectedRows()]

    def hasOtherValuesCategory(self):
        for row in range(self.tableView.rowCount()):
            widget = self.tableView.cellWidget(row, 4)
            if isinstance(widget, QLineEdit) and widget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                return True
        return False

    def ensureOtherValuesCategory(self):
        if self.hasOtherValuesCategory():
            return

        row = self.tableView.rowCount()
        self.tableView.insertRow(row)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(self.generateRandomColor())

        self.setRowWidgets(
            row,
            symbol,
            True,
            self.tr("Other Values"),
            self.tr("Other Values"),
            self.getGeometryHint(),
            isReadOnlyValue=True,
        )

        self.updateClassCount()

    def getCurrentLayerUnitAbbr(self):
        if not self.currentLayer or not self.utils:
            return ""

        layerIdent = self.currentLayer.customProperty("qgisred_identifier")
        if layerIdent:
            return self.utils.getUnitAbbreviationForLayer(layerIdent)
        return ""

    # ============================================================
    # DIALOG LIFECYCLE
    # ============================================================

    def cancelAndClose(self):
        self.close()

    def eventFilter(self, obj, event):
        if obj == self.btClassPlus and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton and self.btClassPlus.isEnabled():
                self.addClassBeforeSelection = True
                self.executeAddClass()
                self.addClassBeforeSelection = False
                return True

        if obj == self and event.type() == QEvent.MouseButtonPress:
            clickPos = event.pos()
            tableGeometry = self.tableView.geometry()
            if not tableGeometry.contains(clickPos):
                self.tableView.clearSelection()

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.disconnectLayerTreeSignal()
        self.cleanupParentReference()
        super().closeEvent(event)

    def disconnectLayerTreeSignal(self):
        if self.layerTreeViewConnection and iface and iface.layerTreeView():
            try:
                iface.layerTreeView().currentLayerChanged.disconnect(self.onQgisLayerSelectionChanged)
            except:
                pass

    def cleanupParentReference(self):
        if self.parentPlugin and hasattr(self.parentPlugin, "legendsDialog"):
            self.parentPlugin.legendsDialog = None