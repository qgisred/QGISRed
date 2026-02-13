# -*- coding: utf-8 -*-

# Standard library imports
import os
import random
import math
import statistics

# Third-party imports
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (QDialog, QMessageBox, QHeaderView,
                             QComboBox, QLineEdit, QAbstractItemView,
                             QCheckBox, QDoubleSpinBox, QSpinBox, QApplication, QProgressDialog,
                             QWidget, QHBoxLayout)
from PyQt5.QtCore import (QVariant, Qt, QTimer, QObject, QEvent,
                          QItemSelectionModel, QItemSelection, QPoint)
from qgis.PyQt import uic

# QGIS imports
from qgis.core import (QgsProject, QgsVectorLayer, QgsMessageLog, Qgis,
                       QgsGraduatedSymbolRenderer, QgsCategorizedSymbolRenderer,
                       QgsRendererRange, QgsRendererCategory, QgsSymbol,
                       QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGradientColorRamp,
                       QgsClassificationJenks, QgsClassificationPrettyBreaks,
                       QgsStyle, QgsPresetSchemeColorRamp, QgsColorRamp)
from qgis.gui import QgsColorButton, QgsColorRampButton
from qgis.utils import iface

# Local imports
from ..tools.qgisred_utils import QGISRedUtils
from .qgisred_custom_dialogs import QGISRedRangeEditDialog, QGISRedSymbolColorSelector, QGISRedColorRampSelector, QGISRedRowSelectionFilter

# Load UI
formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

class QGISRedLegendsDialog(QDialog, formClass):
    FIELD_TYPE_NUMERIC = 'numeric'
    FIELD_TYPE_CATEGORICAL = 'categorical'
    FIELD_TYPE_UNKNOWN = 'unknown'
    
    # Class Count Limits
    WARN_CLASSES = 50
    MAX_CLASSES = 1000

    # Task 4.3: Add 'qgisred_results' to allowed groups
    ALLOWED_GROUP_IDENTIFIERS = ["qgisred_thematicmaps", "qgisred_results", "qgisred_demandsectors"]

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLegendsDialog, self).__init__(parent)
        self.setupUi(self)
        self.initProperties()
        self.initUi()
        self.connectSignals()
        self.loadInitialState()

    def initProperties(self):
        """Initialize class properties."""
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.currentFieldName = None
        self.currentLayer = None
        self.pluginFolder = os.path.dirname(os.path.dirname(__file__))
        self.isEditing = True
        self.originalRenderer = None
        self.availableUniqueValues = []
        self.usedUniqueValues = []
        self.btClassPlusClickTimer = None
        self.btClassPlusAddBefore = False
        self.layerTreeViewConnection = None
        self.layerTreeRoot = None  # NEW: Store reference to layer tree root
        self.style = None  # QGISRed style database

        # NEW: Track the last successfully selected layer ID
        self.lastValidLayerId = None

        # Plugin context properties (set via config method)
        self.parent = None
        self.iface = None
        self.ProjectDirectory = ""
        self.NetworkName = ""
        self.utils = None

    def config(self, ifac, direct, netw, parent):
        """Configure dialog with parent plugin context."""
        self.parent = parent
        self.iface = ifac
        self.ProjectDirectory = direct
        self.NetworkName = netw

        # Create utils instance
        self.utils = QGISRedUtils(direct, netw, ifac)

        # Refresh current layer to populate legend types now that utils is available
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())

    def initUi(self):
        """Initialize UI components."""
        self.configWindow()
        self.setupTableView()
        self.populateClassificationModes()
        self.populateLegendTypes()
        self.populateGroups()
        self.setupClassCountField()
        self.setupClassifyAllButton()

        # NEW: Setup Advanced Color and Size UI
        self.setupAdvancedUi()
        self.loadStyleDatabase()
        self.applyConsistentStyling()
        self.setupTooltips()

        self.labelIntervalRange.setVisible(False)
        self.spinIntervalRange.setVisible(False)

        # Install event filter on dialog to detect clicks outside table
        self.installEventFilter(self)

        # TASK 5.1: Install event filter on Plus button for Right-Click detection
        self.btClassPlus.installEventFilter(self)

    def configWindow(self):
        """Configure window appearance."""
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))
        self.setWindowTitle("QGISRed Legend Editor")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)

        self.btClassPlus.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))


    def setupTableView(self):
        """Configure table columns and visual style."""
        self.tableView.setColumnCount(5)
        self.tableView.setHorizontalHeaderLabels(["", "Color", "Size", "Value", "Legend"])

        # Initialize Event Filter for row selection logic
        self.rowSelectionFilter = QGISRedRowSelectionFilter(self.tableView)

        header = self.tableView.horizontalHeader()

        # 0: Checkbox (Fixed small width, unnamed column)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableView.setColumnWidth(0, 30)

        # 1: Symbol/Color (Fixed Icon size)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableView.setColumnWidth(1, 40)

        # 2: Size (Fixed small width)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableView.setColumnWidth(2, 60)

        # 3: Value (Stretch - takes up available space)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        # 4: Legend (Stretch - takes up available space)
        header.setSectionResizeMode(4, QHeaderView.Stretch)

        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableView.setAlternatingRowColors(False)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setShowGrid(True)

        # CSS Update:
        # 1. gridline-color defines the grid.
        # 2. selection-background-color defines the blue highlight.
        # 3. We remove widget-specific borders here to let the grid show.
        self.tableView.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #d0d0d0;
                selection-background-color: #3399ff;
                selection-color: white;
                border: 1px solid #d0d0d0;
            }
            QTableWidget::item {
                border-bottom: 1px solid #d0d0d0;
                padding: 0px;
            }
            QTableWidget::item:selected {
                background-color: #3399ff;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d0d0d0;
            }
        """)

    def setupClassCountField(self):
        """Configure class count field with conditional editability."""
        self.leClassCount.setMinimum(0)
        self.leClassCount.setMaximum(self.MAX_CLASSES)
        self.leClassCount.valueChanged.connect(self.onClassCountChanged)
        self.setClassCountEditable(False)

    def setClassCountEditable(self, editable):
        """Set class count spinbox editability and appearance."""
        if editable:
            self.leClassCount.setReadOnly(False)
            self.leClassCount.setButtonSymbols(QSpinBox.UpDownArrows)
            self.leClassCount.setStyleSheet("QSpinBox { background-color: white; color: #2b2b2b; }")
        else:
            self.leClassCount.setReadOnly(True)
            self.leClassCount.setButtonSymbols(QSpinBox.NoButtons)
            self.leClassCount.setStyleSheet("QSpinBox { background-color: #F0F0F0; color: #808080; }")

    def modeHasVariableClassCount(self):
        """Determine if the current mode allows variable class count."""
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return True
        
        modeId = self.cbMode.currentData()
        fixedModes = ["FixedInterval", "StdDev"]
        return modeId not in fixedModes

    def onClassCountChanged(self, newValue):
        """Handle spin box value change to add/remove classes."""
        if not self.currentLayer:
            return
        
        if not self.modeHasVariableClassCount():
            return
        
        currentCount = self.tableView.rowCount()
        if newValue == currentCount:
            return
        
        self.leClassCount.blockSignals(True)
        
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            if newValue > currentCount:
                while self.tableView.rowCount() < newValue:
                    self.addNumericClass()
            elif newValue < currentCount:
                while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                    self.tableView.removeRow(self.tableView.rowCount() - 1)
            
            self.leClassCount.setValue(self.tableView.rowCount())
            self.leClassCount.blockSignals(False)
            
            modeId = self.cbMode.currentData()
            if modeId and modeId not in [None, "Manual"] and newValue > currentCount:
                self.applyClassificationMethod(modeId)
        
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            if newValue > currentCount:
                while self.tableView.rowCount() < newValue and self.availableUniqueValues:
                    self.addCategoricalClass()
            elif newValue < currentCount:
                while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                    self._removeCategoricalRow(self.tableView.rowCount() - 1)
            
            self.leClassCount.setValue(self.tableView.rowCount())
            self.leClassCount.blockSignals(False)
            self.updateClassCountLimits()

    def setupAdvancedUi(self):
        self.cbSizes.addItems(["Manual", "Equal", "Linear", "Quadratic", "Exponential", "Proportional to Value"])
        self.cbSizes.currentIndexChanged.connect(self.onSizeModeChanged)
        self.spinSizeEqual.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.spinSizeMax.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMax.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.ckSizeInvert.toggled.connect(self.applySizeLogic)

        # Initialize constraints
        self.updateSizeSpinBoxConstraints()

        self.cbColors.addItems(["Manual", "Equal", "Random", "Ramp", "Palette"])
        self.cbColors.currentIndexChanged.connect(self.onColorModeChanged)
        self.btColorEqual.setColor(QColor("red"))
        self.btColorEqual.colorChanged.connect(self.applyColorLogic)
        self.ckColorInvert.toggled.connect(self.applyColorLogic)

        # Setup refresh colors button
        self.btRefreshColors.setIcon(QIcon(":/images/themes/default/mActionRefresh.svg"))
        self.btRefreshColors.clicked.connect(lambda: self.applyColorLogic(forceRefresh=True))

        self.setupColorRampButton()

        self.onSizeModeChanged()
        self.onColorModeChanged()

    def setupColorRampButton(self):
        """Initialize and add QGISRedColorRampSelector to the UI."""
        self.btnColorRamp = QGISRedColorRampSelector(self)
        self.btnColorRamp.setVisible(False)
        # Add with horizontal centering using stretch spacers
        self.palletesHorizontalLayout.addStretch(1)
        self.palletesHorizontalLayout.addWidget(self.btnColorRamp)
        self.palletesHorizontalLayout.addStretch(1)
        # Connect signal to handle ramp changes
        self.btnColorRamp.colorRampChanged.connect(self.onCustomColorRampChanged)
    
    def onCustomColorRampChanged(self, ramp):
        """Handle color ramp change from custom selector."""
        # Apply the selected ramp to the current color logic
        self.applyColorLogic()

    def setupClassifyAllButton(self):
        # Ensure icon exists or fallback
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconClassifyAll.png')
        self.btClassifyAll.setIcon(QIcon(iconPath))

        self.btClassifyAll.setToolTip(self.tr("Classify All Unique Values"))
        self.btClassifyAll.clicked.connect(self.classifyAll)

    def applyConsistentStyling(self):
        """Apply consistent white backgrounds to all editable widgets and standardize appearance."""
        # Define standard styles
        editableComboStyle = "QComboBox { background-color: white; }"
        editableSpinBoxStyle = "QSpinBox { background-color: white; } QDoubleSpinBox { background-color: white; }"
        editableCheckBoxStyle = "QCheckBox { background-color: white; }"

        # Apply to combo boxes
        self.cbGroups.setStyleSheet(editableComboStyle)
        self.cbLegendLayer.setStyleSheet(editableComboStyle)
        self.cbMode.setStyleSheet(editableComboStyle)
        self.cbLegendsType.setStyleSheet(editableComboStyle)
        self.cbSizes.setStyleSheet(editableComboStyle)
        self.cbColors.setStyleSheet(editableComboStyle)

        # Apply to spin boxes
        self.spinIntervalRange.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeEqual.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeMin.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeMax.setStyleSheet(editableSpinBoxStyle)

        # Apply to checkboxes
        #self.ckSizeInvert.setStyleSheet(editableCheckBoxStyle)
        #self.ckColorInvert.setStyleSheet(editableCheckBoxStyle)

    def setupTooltips(self):
        """Setup tooltips for all buttons with translation support."""
        # Navigation buttons
        self.btUp.setToolTip(self.tr("Move selected class up"))
        self.btDown.setToolTip(self.tr("Move selected class down"))
        
        # Class management buttons (dynamic tooltips set in updateUiBasedOnFieldType)
        self.btClassMinus.setToolTip(self.tr("Remove selected class(es)"))
        
        # Classification button
        self.btClassifyAll.setToolTip(self.tr("Add all unique values as separate classes"))
        
        # Color refresh button
        if hasattr(self, 'btRefreshColors'):
            self.btRefreshColors.setToolTip(self.tr("Refresh color ramp"))
        
        # Style management buttons
        self.btLoadDefault.setToolTip(self.tr("Load default style for this layer"))
        self.btLoadGlobal.setToolTip(self.tr("Load style from global database"))
        self.btSaveGlobal.setToolTip(self.tr("Save current style to global database"))
        self.btLoadProject.setToolTip(self.tr("Load style from project database"))
        self.btSaveProject.setToolTip(self.tr("Save current style to project database"))
        
        # Action buttons
        self.btApplyLegend.setToolTip(self.tr("Apply changes to layer"))
        self.btCancelLegend.setToolTip(self.tr("Cancel and close dialog"))


    def loadStyleDatabase(self):
        """Loads the proprietary QGISRed style database."""
        self.style = QgsStyle()
        dbPath = os.path.join(self.pluginFolder, "defaults", "symbology-style_QGISRed.db")

        # Try to load the style database
        if os.path.exists(dbPath):
            try:
                # For QGIS 3, try loading directly
                success = self.style.createDatabase(dbPath) or self.style.load(dbPath)
                if not success:
                    QgsMessageLog.logMessage(
                        f"Failed to load style database: {dbPath}",
                        "QGISRed",
                        Qgis.Warning
                    )
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error loading style database: {str(e)}",
                    "QGISRed",
                    Qgis.Warning
                )
        else:
            QgsMessageLog.logMessage(
                f"Style database not found: {dbPath}",
                "QGISRed",
                Qgis.Info
            )

    def connectSignals(self):
        """Wire up all UI signals."""
        self.cbGroups.currentIndexChanged.connect(self.onGroupChanged)
        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.cancelAndClose)
        self.cbMode.currentIndexChanged.connect(self.onModeChanged)
        self.cbLegendsType.currentIndexChanged.connect(self.onLegendTypeChanged)
        self.spinIntervalRange.valueChanged.connect(self.onIntervalRangeChanged)
        self.btClassPlus.clicked.connect(self.addClass)
        self.btClassMinus.clicked.connect(self.removeClass)
        self.btUp.clicked.connect(self.moveClassUp)
        self.btDown.clicked.connect(self.moveClassDown)
        self.btSaveProject.clicked.connect(self.saveProjectStyle)
        self.btSaveGlobal.clicked.connect(self.saveGlobalStyle)
        self.btLoadDefault.clicked.connect(self.loadDefaultStyle)
        self.btLoadGlobal.clicked.connect(self.loadGlobalStyle)
        self.btLoadProject.clicked.connect(self.loadProjectStyle)
        self.tableView.cellDoubleClicked.connect(self.onCellDoubleClicked)

        # CHANGED: Use itemSelectionChanged to handle state updates.
        # REMOVED: itemClicked connection (native behavior handles selection better).
        self.tableView.itemSelectionChanged.connect(self.updateButtonStates)

        # Connect to layer tree view to track layer selection changes
        if iface and iface.layerTreeView():
            self.layerTreeViewConnection = iface.layerTreeView().currentLayerChanged.connect(self.onQgisLayerSelectionChanged)

        # # --- NEW: Project and Tree Signals ---
        # # Watch for global visibility changes (recursive from root)
        # self.layerTreeRoot = QgsProject.instance().layerTreeRoot()
        # self.layerTreeRoot.visibilityChanged.connect(self.onTreeNodeVisibilityChanged)

        # # Watch for layer additions and removals
        # QgsProject.instance().layersWillBeRemoved.connect(self.onLayersWillBeRemoved)
        # QgsProject.instance().layersAdded.connect(self.onProjectLayersChanged)
        # QgsProject.instance().layersRemoved.connect(self.onProjectLayersChanged)

    def loadInitialState(self):
        """Preselect group/layer and set initial state."""
        self.preselectGroupAndLayer()
        self.frameLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.labelFrameLegends.setText(self.tr("Legend"))
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())
            # Populate legend types based on the current layer's support
            self.populateLegendTypes(self.cbLegendLayer.currentLayer())
        self.updateClassCount()

    # --- Event Handlers ---

    def onQgisLayerSelectionChanged(self, layer):
        """Handle layer selection change from QGIS layer tree."""
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        # Check if the layer is in an allowed group and has the right renderer type
        layerNode = QgsProject.instance().layerTreeRoot().findLayer(layer)
        if not layerNode:
            return

        # --- FIX START: Check visibility before proceeding ---
        # If the clicked layer is not visible, do nothing.
        # This preserves the current state of the dialog instead of blanking it out.
        if not layerNode.isVisible():
            return
        # --- FIX END ---

        groupPath = self.findGroupPathForLayer(layerNode)
        if not groupPath:
            return

        # Check if layer has graduated or categorized renderer
        if layer.renderer().type() not in ("graduatedSymbol", "categorizedSymbol"):
            return

        # Update the group selection if needed
        currentGroupPath = self.cbGroups.currentData()
        if currentGroupPath != groupPath:
            self.setGroupByPath(groupPath)
            self.onGroupChanged()

        # Update the layer selection if needed
        if self.cbLegendLayer.currentLayer() != layer:
            self.cbLegendLayer.setLayer(layer)

    def onGroupChanged(self):
        """Filter layer combo when group selection changes."""
        # 1. Get layers valid for this group (must be visible and correct type)
        allowed = self.getRenderableLayersInSelectedGroup()
        allLayers = list(QgsProject.instance().mapLayers().values())
        excepted = [l for l in allLayers if l not in allowed]

        # 2. Prepare the dropdown
        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(excepted)

        # 3. Intelligent Selection Logic
        current_layer = self.cbLegendLayer.currentLayer()
        target_layer = None

        # --- NEW PRIORITY: Check for Active Layer First ---
        # If the user has a layer selected in the TOC, and that layer is visible
        # and belongs to this group, prioritize it.
        active_node = self.getActiveLayerFromTree()
        if active_node:
            active_lyr = active_node.layer()
            # Check if this active layer is in our allowed list (visible & in current group)
            if active_lyr in allowed:
                target_layer = active_lyr

        # Priority A: If the memory (lastValidLayerId) is now available, restore it.
        # (Only if we didn't find an active layer above)
        if target_layer is None and self.lastValidLayerId:
            for lyr in allowed:
                if lyr.id() == self.lastValidLayerId:
                    target_layer = lyr
                    break

        # Priority B: If current selection is still valid, keep it.
        # (Only if we didn't find the 'active' or 'restored' layer)
        if target_layer is None and current_layer and current_layer in allowed:
            target_layer = current_layer

        # Priority C: Default to the first available layer
        if target_layer is None and allowed:
            target_layer = allowed[0]

        # Apply selection
        self.cbLegendLayer.setLayer(target_layer)
        self.cbLegendLayer.blockSignals(False)

        # Trigger UI update
        self.onLayerChanged(self.cbLegendLayer.currentLayer())

    def resetAllModesToManual(self):
        """Reset classification, size, and color modes to Manual."""
        # Reset classification mode
        self.cbMode.blockSignals(True)
        self.cbMode.setCurrentIndex(0)  # Manual
        self.cbMode.blockSignals(False)

        # Reset size mode
        self.cbSizes.blockSignals(True)
        self.cbSizes.setCurrentIndex(0)  # Manual
        self.cbSizes.blockSignals(False)

        # Reset color mode
        self.cbColors.blockSignals(True)
        self.cbColors.setCurrentIndex(0)  # Manual
        self.cbColors.blockSignals(False)

        # Trigger UI updates for size and color modes
        self.onSizeModeChanged()
        self.onColorModeChanged()

    def onLayerChanged(self, layer):
        """Handle layer selection change."""
        if layer and isinstance(layer, QgsVectorLayer):
            # NEW: Update memory of the last valid selection
            self.lastValidLayerId = layer.id()

            self.currentLayer = layer
            self.originalRenderer = layer.renderer().clone() if layer.renderer() else None
            self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)

            self.frameLegends.setEnabled(True)

            # Get Units and update Label
            baseTitle = self.tr(f"Legend for {layer.name()}")
            units = self.getLayerUnits()

            if units:
                self.labelFrameLegends.setText(f"{baseTitle} | {units} units")
            else:
                self.labelFrameLegends.setText(baseTitle)

            # Populate legend types based on layer support
            self.populateLegendTypes(layer)

            # Update Legend Type Combobox to current renderer
            rType = layer.renderer().type()
            index = self.cbLegendsType.findData(rType)
            if index != -1:
                self.cbLegendsType.blockSignals(True)
                self.cbLegendsType.setCurrentIndex(index)
                self.cbLegendsType.blockSignals(False)

            self.resetAllModesToManual()
            self.updateUiBasedOnFieldType()

            if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
                self.populateNumericLegend()
            elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
                self.populateCategoricalLegend()
            else:
                self.clearTable()
            self.updateButtonStates()
        else:
            # Note: We DO NOT clear self.lastValidLayerId here.
            # We want to remember what was selected before it became None (hidden).
            self.resetToEmptyState()

    def onModeChanged(self):
        """Handle classification mode change."""
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer: return
        self.updateUiBasedOnFieldType()
        methodId = self.cbMode.currentData()
        if not methodId: return
        if methodId == "FixedInterval":
            self.calculateOptimalInterval()
        self.applyClassificationMethod(methodId)

    def onIntervalRangeChanged(self):
        """Handle spin box change for fixed interval."""
        if self.cbMode.currentData() == "FixedInterval":
            self.applyClassificationMethod("FixedInterval")

    def onLegendTypeChanged(self):
        """Handle legend type change (Graduated <-> Categorized)."""
        if not self.currentLayer or not self.currentFieldName:
            return
        
        newType = self.cbLegendsType.currentData()
        currentType = self.currentLayer.renderer().type() if self.currentLayer.renderer() else None
        
        # If type hasn't actually changed, do nothing
        if newType == currentType:
            return
        
        field = self.currentFieldName
        
        if newType == "categorizedSymbol":
            # Check unique value count before converting to categorized
            fieldIdx = self.currentLayer.fields().indexOf(field)
            if fieldIdx >= 0:
                uniqueValues = self.currentLayer.uniqueValues(fieldIdx)
                uniqueCount = len([v for v in uniqueValues if v is not None and str(v) != 'NULL'])
                
                if uniqueCount > self.MAX_CLASSES:
                    QMessageBox.critical(
                        self,
                        self.tr("Too Many Classes"),
                        self.tr(f"The field '{field}' has {uniqueCount} unique values.\n"
                                f"The maximum allowed is {self.MAX_CLASSES}.\n"
                                f"Please filter the data or choose a different field.")
                    )
                    # Revert combo box
                    self.cbLegendsType.blockSignals(True)
                    idx = self.cbLegendsType.findData(currentType)
                    if idx >= 0:
                        self.cbLegendsType.setCurrentIndex(idx)
                    self.cbLegendsType.blockSignals(False)
                    return

                if uniqueCount > self.WARN_CLASSES:
                    reply = QMessageBox.question(
                        self,
                        self.tr("High Class Count Warning"),
                        self.tr(f"The field '{field}' has {uniqueCount} unique values.\n"
                                f"Creating a categorized legend with more than {self.WARN_CLASSES} classes may "
                                f"affect performance and readability.\n\n"
                                f"Do you want to proceed?"),
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.No:
                        # Revert combo box to current renderer type
                        self.cbLegendsType.blockSignals(True)
                        idx = self.cbLegendsType.findData(currentType)
                        if idx >= 0:
                            self.cbLegendsType.setCurrentIndex(idx)
                        self.cbLegendsType.blockSignals(False)
                        return
            
            # Convert to categorized: use unique values from the field
            self.convertToCategorized(field)
            # Force field type to CATEGORICAL for categorized renderer
            self.currentFieldType = self.FIELD_TYPE_CATEGORICAL
            self.currentFieldName = field
        elif newType == "graduatedSymbol":
            # Convert to graduated: create default ranges
            self.convertToGraduated(field)
            # Update field type from renderer
            self.currentFieldType, self.currentFieldName = self.detectFieldType(self.currentLayer)
        else:
            # Update field type from renderer
            self.currentFieldType, self.currentFieldName = self.detectFieldType(self.currentLayer)
        
        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        
        # Repopulate the table based on explicit type
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.populateNumericLegend()
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.populateCategoricalLegend()
        else:
            self.clearTable()
        
        self.updateButtonStates()
        self.currentLayer.triggerRepaint()

    def convertToCategorized(self, field):
        """Convert current layer to categorized renderer using unique field values."""
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return
        
        uniqueValues = sorted(layer.uniqueValues(fieldIdx))
        categories = []
        
        # Get unit abbreviation if available
        unitAbbr = ""
        if self.utils:
            layerIdentifier = layer.customProperty("qgisred_identifier")
            if layerIdentifier:
                unitAbbr = self.utils.getUnitAbbreviationForLayer(layerIdentifier)
        
        for value in uniqueValues:
            if value is None or str(value) == 'NULL':
                continue
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            # Generate a random color for each category
            color = QColor.fromHsv(
                random.randint(0, 359),
                random.randint(150, 255),
                random.randint(150, 255)
            )
            symbol.setColor(color)
            if layer.geometryType() == 1:  # Line
                symbol.setWidth(0.6)
            else:
                symbol.setSize(2.5)
            
            # Create label with unit abbreviation if available
            label = str(value)
            if unitAbbr:
                label = f"{value} {unitAbbr}"
            
            category = QgsRendererCategory(value, symbol, label)
            categories.append(category)
        
        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)

    def convertToGraduated(self, field):
        """Convert current layer to graduated renderer using equal intervals."""
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return
        
        # Get min/max values
        minVal = layer.minimumValue(fieldIdx)
        maxVal = layer.maximumValue(fieldIdx)
        
        if minVal is None or maxVal is None:
            return
        
        # Create 5 classes by default
        numClasses = 5
        interval = (maxVal - minVal) / numClasses
        ranges = []
        
        # Create a color ramp (blue to red)
        startColor = QColor(0, 255, 0)  # Green
        endColor = QColor(255, 0, 0)    # Red
        
        for i in range(numClasses):
            lower = minVal + (i * interval)
            upper = minVal + ((i + 1) * interval)
            
            # Interpolate color
            t = i / max(1, numClasses - 1)
            color = QColor(
                int(startColor.red() + t * (endColor.red() - startColor.red())),
                int(startColor.green() + t * (endColor.green() - startColor.green())),
                int(startColor.blue() + t * (endColor.blue() - startColor.blue()))
            )
            
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            if layer.geometryType() == 1:  # Line
                symbol.setWidth(0.6)
            else:
                symbol.setSize(2.5)
            
            label = f"{lower:.1f} - {upper:.1f}"
            rangeObj = QgsRendererRange(lower, upper, symbol, label)
            ranges.append(rangeObj)
        
        renderer = QgsGraduatedSymbolRenderer(field, ranges)
        layer.setRenderer(renderer)

    def onCellDoubleClicked(self, row, column):
        """Route double click to specific editors."""
        if column == 2 and self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.openRangeEditor(row)

    def onTreeNodeVisibilityChanged(self, node):
        """
        Handle visibility changes in the layer tree.
        Triggered when any node (Group or Layer) is checked/unchecked.
        """
        # Save state
        currentGroupPath = self.cbGroups.currentData()

        # 1. Refresh Groups (handles cases where a Group was hidden/shown)
        self.populateGroups()

        # 2. Restore Group Selection if it still exists
        if currentGroupPath:
            # Check if the path still exists in the refreshed combo
            index = self.cbGroups.findData(currentGroupPath)
            if index != -1:
                self.setGroupByPath(currentGroupPath)
            elif self.cbGroups.count() > 0:
                self.cbGroups.setCurrentIndex(0)

        # 3. Refresh Layer List and trigger Restoration Logic
        # This calls onGroupChanged, which now contains the logic to
        # check self.lastValidLayerId and restore selection if the layer became visible.
        self.onGroupChanged()

    def onLayersWillBeRemoved(self, layerIds):
        """
        Handle layer deletion *before* it happens to prevent crashes.
        """
        # Check if the currently selected layer is about to be deleted
        if self.currentLayer and self.currentLayer.id() in layerIds:
            # Explicitly clear the reference to prevent accessing a deleted C++ object
            self.currentLayer = None
            self.cbLegendLayer.blockSignals(True)
            self.cbLegendLayer.setLayer(None)
            self.cbLegendLayer.blockSignals(False)
            self.resetToEmptyState()

    def onProjectLayersChanged(self, layers):
        """
        Handle layers added or removed (after the removal is complete).
        """
        # Save the currently selected group path so we can try to restore it
        currentGroupPath = self.cbGroups.currentData()

        # Re-populate the groups combo (in case a group was added/removed or emptied)
        self.populateGroups()

        # Try to restore the previous group selection
        if currentGroupPath:
            self.setGroupByPath(currentGroupPath)

        # Trigger update of the layer list
        self.onGroupChanged()

    # --- Advanced Size & Color UI Logic ---

    def onSizeModeChanged(self):
        """Handle size mode change."""
        mode = self.cbSizes.currentText()
        showEqual = mode == "Equal"
        showMinMax = mode in ["Linear", "Quadratic", "Exponential", "Proportional to Value"]
        self.spinSizeEqual.setVisible(showEqual)
        self.labelSizeValue.setVisible(showEqual)
        self.spinSizeMin.setVisible(showMinMax)
        self.spinSizeMax.setVisible(showMinMax)
        self.labelSpinMin.setVisible(showMinMax)
        self.labelSpinMax.setVisible(showMinMax)
        self.ckSizeInvert.setVisible(mode != "Manual" and mode != "Equal")
        self.applySizeLogic()

    def updateSizeSpinBoxConstraints(self):
        minVal = self.spinSizeMin.value()
        maxVal = self.spinSizeMax.value()

        self.spinSizeMin.blockSignals(True)
        self.spinSizeMax.blockSignals(True)

        self.spinSizeMin.setMaximum(maxVal)
        self.spinSizeMax.setMinimum(minVal)

        self.spinSizeMin.blockSignals(False)
        self.spinSizeMax.blockSignals(False)

    def syncColorRampButton(self):
        """Update CustomColorRampSelector with ramps from style database."""
        # Clear existing ramps
        self.btnColorRamp.clearRamps()
        
        mode = self.cbColors.currentText()
        
        if mode == "Ramp":
            # Load gradient ramps
            ramps = self.loadGradientRampsFromStyle()
        elif mode == "Palette":
            # Load palette ramps
            ramps = self.loadPaletteRampsFromStyle()
        else:
            return
        
        # Add ramps to the custom selector
        if ramps:
            self.btnColorRamp.addColorRamps(ramps)
            # Set first ramp as default
            first_name = list(ramps.keys())[0]
            self.btnColorRamp.setCurrentRamp(first_name)
        
    def onColorModeChanged(self):
        """Handle color mode change."""
        mode = self.cbColors.currentText()
        self.btColorEqual.setVisible(mode == "Equal")
        
        isRampOrPalette = mode in ["Ramp", "Palette"]
        self.btnColorRamp.setVisible(isRampOrPalette)
        
        self.ckColorInvert.setVisible(isRampOrPalette)
        self.btRefreshColors.setVisible(mode == "Random")

        if isRampOrPalette:
            self.syncColorRampButton()

        self.applyColorLogic()

    def loadGradientRampsFromStyle(self):
        """Load gradient color ramps from style database."""
        ramps = {}
        
        if self.style:
            # Load Gradient Ramps from Style
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsGradientColorRamp):
                    ramps[name] = ramp

        # If no ramps found, add 2 fallback gradients
        if not ramps:
            ramps["Default (Blue to Red)"] = QgsGradientColorRamp(QColor(0, 0, 255), QColor(255, 0, 0))
            ramps["Default (Green to Yellow)"] = QgsGradientColorRamp(QColor(0, 128, 0), QColor(255, 255, 0))

        return ramps

    def loadPaletteRampsFromStyle(self):
        """Load palette color schemes from style database."""
        ramps = {}
        
        if self.style:
            # Load Preset Schemes (Palettes)
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                # QGIS treats Palettes as PresetSchemeColorRamp
                if isinstance(ramp, QgsPresetSchemeColorRamp):
                    ramps[name] = ramp

        # If no palettes found, create 2 fallback palettes
        if not ramps:
            primaryColors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
                             QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)]
            ramps["Primary Colors"] = QgsPresetSchemeColorRamp(primaryColors)
            
            warmColors = [QColor(255, 87, 51), QColor(255, 140, 0), QColor(255, 195, 0),
                          QColor(220, 60, 60), QColor(255, 165, 79), QColor(238, 130, 98)]
            ramps["Warm Colors"] = QgsPresetSchemeColorRamp(warmColors)

        return ramps

    # --- Mathematical Algorithms ---

    def applySizeLogic(self):
        """Apply size algorithm based on selected mode."""
        if not hasattr(self, 'cbSizes'):
            return

        mode = self.cbSizes.currentText()
        if mode == "Manual" or self.tableView.rowCount() == 0:
            return

        rows = self.tableView.rowCount()
        sizes = []

        if mode == "Equal":
            val = self.spinSizeEqual.value()
            sizes = [val] * rows
        elif mode == "Proportional to Value":
            # Proportional to Value mode - size scales based on actual range values
            minSize = self.spinSizeMin.value()
            maxSize = self.spinSizeMax.value()

            # Calculate average value for each range (midpoint between lower and upper bounds)
            rangeAverageValues = []
            for row in range(rows):
                rangeValues = self.getRangeValues(row)
                if rangeValues:
                    lowerBound, upperBound = rangeValues
                    rangeAverageValues.append((lowerBound + upperBound) / 2.0)
                else:
                    rangeAverageValues.append(0.0)

            # Determine global min from first average, and max from the lower bound of last class
            if rangeAverageValues:
                globalValueMin = min(rangeAverageValues)
                # Get the lower bound of the last class as globalValueMax
                lastClassRange = self.getRangeValues(rows - 1)
                if lastClassRange:
                    globalValueMax = lastClassRange[0]  # Lower bound of last class
                else:
                    globalValueMax = max(rangeAverageValues)
            else:
                globalValueMin = 0.0
                globalValueMax = 1.0

            # Apply proportional algorithm to each range
            for averageValue in rangeAverageValues:
                calculatedSize = self.calculateProportionalSize(minSize, maxSize, globalValueMin, globalValueMax, averageValue)
                sizes.append(calculatedSize)

            # Apply inversion if checked
            if self.ckSizeInvert.isChecked():
                sizes.reverse()
        else:
            min_s = self.spinSizeMin.value()
            max_s = self.spinSizeMax.value()

            # Normalize 0..1
            t_values = [i / max(1, rows - 1) for i in range(rows)]

            if self.ckSizeInvert.isChecked():
                t_values.reverse()

            for t in t_values:
                if mode == "Linear":
                    # y = min + t * (max - min)
                    sizes.append(min_s + t * (max_s - min_s))
                elif mode == "Quadratic":
                    # y = min + t^2 * (max - min)
                    sizes.append(min_s + (t * t) * (max_s - min_s))
                elif mode == "Exponential":
                    # Simple exponential interpolation mapping
                    # y = min + (e^t - 1)/(e - 1) * (max - min)
                    if rows > 1:
                        factor = (math.exp(t) - 1) / (math.exp(1) - 1)
                        sizes.append(min_s + factor * (max_s - min_s))
                    else:
                        sizes.append(min_s)

        # Apply to Table
        isLine = self.getGeometryHint() == "line"
        for r in range(rows):
            sw = self.tableView.cellWidget(r, 2)  # Size Widget (column 2)
            colorContainer = self.tableView.cellWidget(r, 1)  # Color container (column 1)
            cw = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if sw:
                sw.blockSignals(True)
                sw.setText(f"{sizes[r]:.2f}")
                sw.blockSignals(False)
            if cw:
                cw.updateSymbolSize(sizes[r], isLine)

    def calculateProportionalSize(self, minSize, maxSize, globalValueMin, globalValueMax, averageValue):
        """
        Calculate proportional size based on the average value of a range.

        Args:
            minSize: Minimum size (from spinSizeMin)
            maxSize: Maximum size (from spinSizeMax)
            globalValueMin: Minimum average value across all ranges
            globalValueMax: Maximum average value across all ranges
            averageValue: Average value of the current range

        Returns:
            float: The calculated size proportional to the value
        """
        if globalValueMax == globalValueMin:
            return minSize

        normalizedPosition = (averageValue - globalValueMin) / (globalValueMax - globalValueMin)
        normalizedPosition = max(0.0, min(1.0, normalizedPosition))

        return minSize + normalizedPosition * (maxSize - minSize)

    def applyColorLogic(self, forceRefresh=False):
        """Apply color algorithm based on selected mode.
        
        Args:
            forceRefresh: If True, regenerate all colors even for existing rows (used by refresh button).
        """
        if not hasattr(self, 'cbColors'):
            return

        mode = self.cbColors.currentText()
        if mode == "Manual" or self.tableView.rowCount() == 0:
            return

        rows = self.tableView.rowCount()
        colors = []

        if mode == "Equal":
            c = self.btColorEqual.color()
            colors = [c] * rows

        elif mode == "Random":
            if forceRefresh:
                # Force refresh: generate new random colors for all rows
                colors = [self.generateRandomColor() for _ in range(rows)]
            else:
                # Preserve existing colors; only generate new random colors for rows without valid colors
                colors = []
                for r in range(rows):
                    existingColor = self.getRowColor(r)
                    if existingColor and existingColor.isValid():
                        colors.append(existingColor)
                    else:
                        colors.append(self.generateRandomColor())

        elif mode == "Ramp":
            ramp = self.btnColorRamp.currentRamp()
            if isinstance(ramp, QgsGradientColorRamp):
                colors = self.algorithmRamp(ramp, rows)
            else:
                colors = [self.generateRandomColor() for _ in range(rows)]

        elif mode == "Palette":
            palette = self.btnColorRamp.currentRamp()
            if isinstance(palette, QgsPresetSchemeColorRamp):
                colors = self.algorithmPalette(palette, rows)
            else:
                colors = [self.generateRandomColor() for _ in range(rows)]

        # Apply Inversion for Ramp/Palette
        if mode in ["Ramp", "Palette"] and self.ckColorInvert.isChecked():
            colors.reverse()

        # Update Table
        for r in range(rows):
            colorContainer = self.tableView.cellWidget(r, 1)  # Color container (column 1)
            cw = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if cw:
                cw.setColor(colors[r])

    def algorithmPalette(self, paletteRamp, numClasses):
        """
        Port of 'Colores_Paleta' VB Algorithm.
        Interpolates or Picks from a discrete list of colors.
        """
        if numClasses < 1:
            return []

        # 1. Extract Colors from QGIS Preset Ramp
        palColors = paletteRamp.colors()
        if not palColors:
            return [QColor("black")] * numClasses

        numColPaleta = len(palColors)

        # 2. Calculate Increment
        increment = 0.0
        if numClasses > 1:
            increment = (numColPaleta - 1) / (numClasses - 1)

        # 3. Assign Indices (IndColor)
        ind_color = []  # Indices into palColors
        for i in range(numClasses):
            idx = int(math.floor(increment * i))
            # Clamp
            idx = max(0, min(idx, numColPaleta - 1))
            ind_color.append(idx)

        # 4. Grouping and Interpolation
        final_colors = [QColor()] * numClasses

        # Iterate through groups of identical indices
        i = 0
        while i < numClasses:
            current_pal_idx = ind_color[i]

            # Find the end of this group
            j = i
            while j < numClasses and ind_color[j] == current_pal_idx:
                j += 1

            # Group range is [i, j-1]
            group_size = j - i

            # Determine Start and End Colors
            c_start = palColors[current_pal_idx]

            # End color is the palette color at the NEXT index (if it exists)
            if current_pal_idx + 1 < numColPaleta:
                c_end = palColors[current_pal_idx + 1]
            else:
                c_end = c_start  # Last group repeats color

            # Interpolate within the group
            for k in range(group_size):
                global_idx = i + k

                # Interpolation factor
                factor = (k) / (group_size + 1) if (group_size + 1) > 0 else 0

                r = int(c_start.red() + (c_end.red() - c_start.red()) * factor)
                g = int(c_start.green() + (c_end.green() - c_start.green()) * factor)
                b = int(c_start.blue() + (c_end.blue() - c_start.blue()) * factor)

                final_colors[global_idx] = QColor(r, g, b)

            i = j  # Move to next group

        return final_colors

    def algorithmRamp(self, gradientRamp, numClasses):
        """
        Port of 'Colores_Rampa' VB Algorithm.
        Interpolates based on positions 0..100 (converted to 0..1 for QGIS).
        """
        if numClasses < 1:
            return []

        colors = []
        for i in range(numClasses):
            # Calculate position (0.0 to 1.0)
            position = 0.0
            if numClasses > 1:
                position = i / (numClasses - 1)

            colors.append(gradientRamp.color(position))

        return colors

    # --- Layer & Group Logic ---

    def populateGroups(self):
        """Populate group selector from QGIS layer tree."""
        self.cbGroups.blockSignals(True)
        self.cbGroups.clear()

        groups = []
        self.collectGroupsRecursive(QgsProject.instance().layerTreeRoot(), [], groups)

        for name, path, _ in groups:
            self.cbGroups.addItem(name, path)

        self.cbGroups.blockSignals(False)

        # Fix 4.1: Strictly handle empty state
        if self.cbGroups.count() == 0:
            # Force empty index
            self.cbGroups.setCurrentIndex(-1)

            # Explicitly clear dependent layer combo
            self.cbLegendLayer.blockSignals(True)
            self.cbLegendLayer.setExceptedLayerList(list(QgsProject.instance().mapLayers().values()))
            self.cbLegendLayer.setLayer(None)
            self.cbLegendLayer.blockSignals(False)

            # Disable the main frame since no valid selection exists
            self.frameLegends.setEnabled(False)
            self.labelFrameLegends.setText(self.tr("Legend"))

            # Clear internal state
            self.onLayerChanged(None)

        # Note: If count > 0, the previous selection logic (preselectGroupAndLayer)
        # or the user's interaction will handle the selection.

    def collectGroupsRecursive(self, parent, pathParts, results):
        """Recursively collect allowed groups."""
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                currentPath = pathParts + [child.name()]
                if child.isVisible() and child.customProperty("qgisred_identifier") in self.ALLOWED_GROUP_IDENTIFIERS:
                    if self.groupHasVisibleLayers(child):
                        results.append((currentPath[-1], " / ".join(currentPath), child))
                self.collectGroupsRecursive(child, currentPath, results)

    def groupHasVisibleLayers(self, group):
        """Check if group has visible direct child layers."""
        return any(isinstance(c, QgsLayerTreeLayer) and c.isVisible() for c in group.children())

    def getRenderableLayersInSelectedGroup(self):
        """Get visible Graduated/Categorized layers in selected group."""
        path = self.cbGroups.currentData()
        if not path: return []
        
        group = self.findGroupByPath(path)
        if not group: return []
        
        layers = []
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer) and child.isVisible():
                lyr = child.layer()
                if lyr and isinstance(lyr, QgsVectorLayer) and lyr.renderer().type() in ("graduatedSymbol", "categorizedSymbol"):
                    layers.append(lyr)
        return layers

    def findGroupByPath(self, pathStr):
        """Traverse tree to find group by path string."""
        curr = QgsProject.instance().layerTreeRoot()
        for part in pathStr.split(" / "):
            found = next((c for c in curr.children() if isinstance(c, QgsLayerTreeGroup) and c.name().strip() == part.strip()), None)
            if not found: return None
            curr = found
        return curr

    def preselectGroupAndLayer(self):
        """Attempt to select current active layer or default."""
        if not self.cbGroups.count(): return
        
        activeLayer = self.getActiveLayerFromTree()
        targetGroup, targetLayer = None, None

        if activeLayer:
            targetGroup = self.findGroupPathForLayer(activeLayer)
            if targetGroup: targetLayer = activeLayer.layer()

        if not targetGroup:
            targetGroup = self.cbGroups.itemData(0)
            
        self.setGroupByPath(targetGroup)
        self.onGroupChanged()
        
        if targetLayer:
            self.cbLegendLayer.setLayer(targetLayer)
        else:
            layers = self.getRenderableLayersInSelectedGroup()
            if layers: self.cbLegendLayer.setLayer(layers[0])

    def getActiveLayerFromTree(self):
        """Get currently selected layer node."""
        if iface and iface.layerTreeView():
            sel = iface.layerTreeView().selectedLayers()
            if sel: return QgsProject.instance().layerTreeRoot().findLayer(sel[0])
        return None

    def findGroupPathForLayer(self, layerNode):
        """Find combo box data path for a layer node."""
        parent = layerNode.parent()
        while parent and not isinstance(parent, QgsLayerTreeGroup):
            parent = parent.parent()
        
        if isinstance(parent, QgsLayerTreeGroup):
            path = self.buildGroupPath(parent)
            for i in range(self.cbGroups.count()):
                if self.cbGroups.itemData(i) == path: return path
        return None

    def buildGroupPath(self, group):
        """Build path string from group node."""
        parts = []
        curr = group
        while curr and curr.parent():
            parts.insert(0, curr.name())
            curr = curr.parent()
        return " / ".join(parts)

    def setGroupByPath(self, path):
        """Set combo box index by data path."""
        for i in range(self.cbGroups.count()):
            if self.cbGroups.itemData(i) == path:
                self.cbGroups.setCurrentIndex(i)
                break

    # --- Table Population & Helpers ---

    def populateClassificationModes(self):
        """Populate mode combo box."""
        self.cbMode.blockSignals(True)
        self.cbMode.clear()
        self.cbMode.addItem("Manual", None)
        modes = [("EqualInterval", "Equal Interval"), ("FixedInterval", "Fixed Interval"),
                 ("Quantile", "Quantile (Equal Count)"), ("Jenks", "Natural Breaks (Jenks)"),
                 ("StdDev", "Standard Deviation"), ("Pretty", "Pretty Breaks")]
        for id, name in modes: self.cbMode.addItem(self.tr(name), id)
        self.cbMode.blockSignals(False)

    def populateLegendTypes(self, layer=None):
        """Populate legend type combo box based on layer support."""
        self.cbLegendsType.blockSignals(True)
        self.cbLegendsType.clear()
        
        if not layer:
            # Default: show all types
            self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")
            self.cbLegendsType.addItem(self.tr("Categorized"), "categorizedSymbol")
            self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
        else:
            # Get layer identifier and check support
            layerIdentifier = layer.customProperty("qgisred_identifier")
            currentRendererType = layer.renderer().type() if layer.renderer() else "singleSymbol"
            
            # Check if layer supports categorized
            supportsCategorized = False
            if self.utils:
                supportsCategorized = self.utils.getLayerSupportsCategorized(layerIdentifier)
            
            if supportsCategorized:
                print("Supports")
                # Layer supports both graduated and categorized (like diameter)
                self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
                self.cbLegendsType.addItem(self.tr("Categorized"), "categorizedSymbol")
            elif currentRendererType == "categorizedSymbol":
                # Categorized-only layer (like material)
                self.cbLegendsType.addItem(self.tr("Categorized"), "categorizedSymbol")
            elif currentRendererType == "graduatedSymbol":
                # Graduated-only layer (like length)
                self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
            else:
                # Default fallback: show current type
                self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")
        
        self.cbLegendsType.blockSignals(False)

    def detectFieldType(self, layer):
        """Determine if layer uses numeric or categorical renderer."""
        r = layer.renderer()
        if isinstance(r, QgsGraduatedSymbolRenderer):
            return self.FIELD_TYPE_NUMERIC, r.classAttribute()
        elif isinstance(r, QgsCategorizedSymbolRenderer):
            fname = r.classAttribute()
            fidx = layer.fields().indexOf(fname)
            if fidx >= 0 and layer.fields().field(fidx).type() in [QVariant.Int, QVariant.Double, QVariant.LongLong]:
                return self.FIELD_TYPE_NUMERIC, fname
            return self.FIELD_TYPE_CATEGORICAL, fname
        return self.FIELD_TYPE_UNKNOWN, None

    def resetToEmptyState(self):
        """Reset dialog when no layer is selected."""
        self.frameLegends.setEnabled(False)
        self.labelFrameLegends.setVisible(False)
        self.currentLayer = None
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.clearTable()
        self.updateUiBasedOnFieldType()

    def updateUiBasedOnFieldType(self):
        """Toggle UI elements based on field type."""
        isNum = self.currentFieldType == self.FIELD_TYPE_NUMERIC
        isCat = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
        isFixed = isNum and self.cbMode.currentData() == "FixedInterval"
        isManual = isNum and (self.cbMode.currentData() is None or self.cbMode.currentData() == "Manual")

        self.cbMode.setVisible(isNum)
        self.labelMode.setVisible(isNum)
        self.labelIntervalRange.setVisible(isFixed)
        self.spinIntervalRange.setVisible(isFixed)

        self.btClassPlus.setVisible(isCat or isNum)
        self.btClassMinus.setVisible(isCat or isNum)
        self.btClassPlus.setEnabled(not isFixed)
        self.btClassMinus.setEnabled(not isFixed)

        self.labelClass.setVisible(isCat or isNum)
        self.leClassCount.setVisible(isCat or isNum)
        self.btUp.setVisible(isCat)
        self.btDown.setVisible(isCat)
        self.labelFrameLegends.setVisible(isNum or isCat)

        self.btClassifyAll.setVisible(isCat)

        # Toggle class count editability based on mode
        if isCat:
            # For categorized: always display-only (no spin buttons)
            self.setClassCountEditable(False)
            self.updateClassCountLimits()
        elif isNum:
            # For numeric: disable editing when in Manual mode, enable for other variable-count modes
            self.setClassCountEditable(not isManual and self.modeHasVariableClassCount())
        else:
            self.setClassCountEditable(False)
        
        # Update tooltip based on layer type
        if isCat:
            self.btClassPlus.setToolTip(
                self.tr("Right-click: Add a new item above the current selection\n"
                        "Left-click: Add a new item below the current selection\n"
                        "Double-click: Add \"Other values\" option")
            )
        elif isNum:
            self.btClassPlus.setToolTip(
                self.tr("Right-click: Add a new item above the current selection\n"
                        "Left-click: Add a new item below the current selection")
            )


        if isCat: self.updateAddClassButtonState()

        # NEW: Refresh color/size logic when field changes
        if self.currentFieldType != self.FIELD_TYPE_UNKNOWN:
            self.applySizeLogic()
            self.applyColorLogic()

    def clearTable(self):
        self.tableView.setRowCount(0)
        self.updateClassCount()

    def populateNumericLegend(self):
        """Fill table from Graduated renderer."""
        if not self.currentLayer: return
        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer): return
        
        self.clearTable()
        geom = self.getGeometryHint()
        
        for i, rng in enumerate(renderer.ranges()):
            self.tableView.insertRow(i)
            self.setRowWidgets(i, rng.symbol(), rng.renderState(), 
                               f"{rng.lowerValue():.2f} - {rng.upperValue():.2f}", 
                               rng.label(), geom)
        self.updateClassCount()

    def populateCategoricalLegend(self):
        """Fill table from Categorized renderer."""
        if not self.currentLayer: return
        renderer = self.currentLayer.renderer()
        self.clearTable()
        
        self.usedUniqueValues = []
        self.availableUniqueValues = self.getUniqueValuesFromLayer()
        
        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            categories = renderer.categories()
            otherCat = None
            geom = self.getGeometryHint()
            
            for cat in categories:
                if cat.value() == "" or cat.label() in [self.tr("Other Values"), "Other Values"]:
                    otherCat = cat
                    continue
                
                valStr = str(cat.value()) if cat.value() is not None else "NULL"
                if valStr in self.availableUniqueValues: 
                    self.usedUniqueValues.append(valStr)
                
                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(row, cat.symbol(), cat.renderState(), valStr, cat.label(), geom, isReadOnlyVal=True)
            
            if otherCat:
                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(row, otherCat.symbol(), otherCat.renderState(), self.tr("Other Values"), otherCat.label(), geom, isReadOnlyVal=True)

        self.availableUniqueValues = [v for v in self.availableUniqueValues if v not in self.usedUniqueValues]
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def setRowWidgets(self, row, symbol, visible, valText, legendText, geom, isReadOnlyVal=False):
        """Helper to create and set widgets for a row."""

        # Common style for inner widgets: Transparent background so Table selection shows through
        baseStyle = """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #2b2b2b;
            }
            QLineEdit:focus {
                border: 1px solid #3399ff; /* Visual cue when editing */
            }
        """

        readOnlyStyle = """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #808080;
            }
        """

        # Column 0: Checkbox (visibility toggle)
        ckw = QCheckBox(self.tableView)
        ckw.setChecked(visible)
        ckw.installEventFilter(self.rowSelectionFilter)
        # Create a container widget to center the checkbox (matching original style)
        containerWidget = QWidget(self.tableView)
        containerLayout = QHBoxLayout(containerWidget)
        containerLayout.setContentsMargins(0, 0, 0, 0)
        containerLayout.setSpacing(2)
        containerLayout.addWidget(ckw, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        containerWidget.setAutoFillBackground(False)
        self.tableView.setCellWidget(row, 0, containerWidget)

        # Column 1: Color/Symbol (centered, double-click to open dialog)
        cw = QGISRedSymbolColorSelector(self.tableView, geom, symbol.color(), True, "Pick color", doubleClickOnly=True)
        cw.setEnabled(self.isEditing)
        size = symbol.width() if geom == "line" else symbol.size()
        cw.updateSymbolSize(size, geom == "line")
        cw.setAutoFillBackground(False)
        cw.setFixedSize(30, 20)
        # Create a container to center the color widget horizontally
        colorContainer = QWidget(self.tableView)
        colorLayout = QHBoxLayout(colorContainer)
        colorLayout.setContentsMargins(0, 0, 0, 0)
        colorLayout.setSpacing(0)
        cw.installEventFilter(self.rowSelectionFilter)
        colorLayout.addStretch()
        colorLayout.addWidget(cw, 0, Qt.AlignVCenter)
        colorLayout.addStretch()
        colorContainer.setAutoFillBackground(False)
        self.tableView.setCellWidget(row, 1, colorContainer)
        colorContainer.installEventFilter(self.rowSelectionFilter)

        # Column 2: Size
        sw = QLineEdit(str(size))
        sw.setEnabled(self.isEditing)
        sw.setAlignment(Qt.AlignCenter)
        sw.setStyleSheet(baseStyle)
        sw.installEventFilter(self.rowSelectionFilter)
        sw.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))
        self.tableView.setCellWidget(row, 2, sw)

        # Column 3: Value
        vw = QLineEdit(valText)
        vw.setReadOnly(True)
        vw.setAlignment(Qt.AlignCenter)

        if isReadOnlyVal:
            vw.setStyleSheet(readOnlyStyle)
        else:
            # If numeric, it looks like regular text but is read-only until dbl-click
            vw.setStyleSheet(baseStyle)
            vw.mouseDoubleClickEvent = lambda _event, r=row: self.openRangeEditor(r)

        vw.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, 3, vw)

        # Column 4: Legend
        lw = QLineEdit(legendText)
        lw.setEnabled(self.isEditing)
        lw.setStyleSheet(baseStyle)
        lw.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, 4, lw)

    def getUniqueValuesFromLayer(self):
        """Fetch unique values for categorical field."""
        if not self.currentLayer or not self.currentFieldName: return []
        idx = self.currentLayer.fields().indexOf(self.currentFieldName)
        if idx < 0: return []
        
        vals = set()
        for f in self.currentLayer.getFeatures():
            v = f[self.currentFieldName]
            vals.add(str(v) if v is not None else "NULL")
        
        # Special values that should be added last (before "Other Values")
        specialValues = ["NULL", "#NA"]
        
        # Separate special values from regular values
        regularVals = [v for v in vals if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in vals]
        
        # Sort regular values, then append special values at the end
        lst = sorted(regularVals) + foundSpecials
        return lst

    def _sortAvailableUniqueValues(self):
        """Sort availableUniqueValues keeping NULL and #NA at the end."""
        specialValues = ["NULL", "#NA"]
        regularVals = [v for v in self.availableUniqueValues if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in self.availableUniqueValues]
        self.availableUniqueValues = sorted(regularVals) + foundSpecials

    # --- Table Manipulation ---

    def addClass(self):
        """
        Handle add class button click.
        TASK 5.1: Left Click (Single) -> Add Below.
        TASK 5.2: Double Click -> Classify All (Categorical Only).
        """
        if not self.currentLayer: return

        # If timer is running, this is the second click (Double Click)
        if self.btClassPlusClickTimer and self.btClassPlusClickTimer.isActive():
            self.btClassPlusClickTimer.stop()
            self.btClassPlusClickTimer = None

            # TASK 5.2: Double Click triggers Classify All for Categorical
            if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
                self.ensureOtherValuesCategory()
            else:
                # For numeric, ignore double-click to prevent adding two classes
                return
        else:
            # First click: Start timer to wait for potential second click
            self.btClassPlusClickTimer = QTimer()
            self.btClassPlusClickTimer.setSingleShot(True)
            self.btClassPlusClickTimer.timeout.connect(self._onSingleClickAdd)
            # 250ms is standard system double-click interval
            self.btClassPlusClickTimer.start(250)

    def _onSingleClickAdd(self):
        """Timer timeout: It was just a single click."""
        self.btClassPlusClickTimer = None
        self.btClassPlusAddBefore = False  # Default: Add Below
        self.executeAddClass()

    def classifyAll(self):
        """TASK 5.2: Add all available unique values at once."""
        unique_count_to_add = len(self.availableUniqueValues)
        if unique_count_to_add == 0:
            QMessageBox.information(self, self.tr("Info"), self.tr("All values are already classified."))
            return

        # Check Limits
        current_count = self.tableView.rowCount()
        # "Other" category might be removed, but let's be conservative with the count check
        total_potential = current_count + unique_count_to_add
        
        if total_potential > self.MAX_CLASSES:
             QMessageBox.critical(
                self,
                self.tr("Limit Exceeded"),
                self.tr(f"Adding {unique_count_to_add} classes would result in {total_potential} total classes,\n"
                        f"which exceeds the maximum limit of {self.MAX_CLASSES}.")
            )
             return

        # Disable updates for performance
        self.tableView.setUpdatesEnabled(False)
        self.tableView.blockSignals(True)

        progress = None
        use_progress = unique_count_to_add > self.WARN_CLASSES

        if use_progress:
            progress = QProgressDialog(self.tr("Adding classes..."), self.tr("Cancel"), 0, unique_count_to_add, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

        try:
            # Loop while there are still values available
            # addCategoricalClass modifies self.availableUniqueValues internally
            count = 0
            while self.availableUniqueValues:
                self.addCategoricalClass()
                count += 1
                
                if use_progress:
                    progress.setValue(count)
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        break

            for r in reversed(range(self.tableView.rowCount())):
                w = self.tableView.cellWidget(r, 3)
                if isinstance(w, QLineEdit) and w.text() in [self.tr("Other Values"), "Other Values"]:
                    self.tableView.removeRow(r)

        finally:
            if progress:
                progress.close()
            
            self.tableView.blockSignals(False)
            self.tableView.setUpdatesEnabled(True)

            # Final UI refresh
            self.updateClassCount()
            self.updateButtonStates()
            self.applyColorLogic()
            self.applySizeLogic()

    def executeAddClass(self):
        """Route add logic."""
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.addCategoricalClass()
        else:
            self.addNumericClass()

            # --- FIX START: Re-apply Automatic Classification ---
            # If the mode is NOT Manual (and not Fixed Interval, though that button is usually disabled),
            # we should re-calculate the breaks for the new class count (N+1).
            modeId = self.cbMode.currentData()
            if modeId and modeId != "Manual" and modeId != "FixedInterval":
                self.applyClassificationMethod(modeId)
            # --- FIX END ---

        self.updateButtonStates()

        # Re-apply generic logic
        self.applyColorLogic()
        self.applySizeLogic()

    def addNumericClass(self):
        """Add numeric range."""
        if self.tableView.rowCount() >= self.MAX_CLASSES:
             QMessageBox.critical(self, self.tr("Limit Exceeded"), self.tr(f"Maximum of {self.MAX_CLASSES} classes reached."))
             return

        sel = self.getSelectedRows()

        # --- FIX START: Handle Multi-Selection ---
        # If multiple rows are selected, we treat it as "Append to End"
        # rather than trying to insert relative to the selection.
        if len(sel) > 1:
            self.tableView.clearSelection()
            sel = []  # Clear this so it falls through to the 'Append' logic below
        # --- FIX END ---

        # Calculate insertion index
        if sel and len(sel) == 1:
            row = sel[0]
            if not self.btClassPlusAddBefore:
                row += 1 # Insert After selection
        else:
            row = self.tableView.rowCount() # Append to end

        lower, upper = self.calculateInitialRangeForNewRow(row)
        
        # Determine color based on mode settings
        modeId = self.cbMode.currentData()
        colorMode = self.cbColors.currentText() if hasattr(self, 'cbColors') else "Manual"
        
        # Use smart color when both intervals and colors are in Manual mode
        if (modeId == "Manual" or modeId is None) and colorMode == "Manual":
            newColor = self.getSmartColorForNewRow(row)
        else:
            newColor = self.generateRandomColor()
        
        self.tableView.insertRow(row)

        sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        sym.setColor(newColor)

        # Set default size
        if self.currentLayer.geometryType() == 0:  # Point
            sym.setSize(3)
        elif self.currentLayer.geometryType() == 1:  # Line
            sym.setWidth(0.4)
        else:  # Polygon
            sym.setSize(1.5)

        self.setRowWidgets(row, sym, True, f"{lower:.2f} - {upper:.2f}", f"{lower:.2f} - {upper:.2f}", self.getGeometryHint())
        self.updateAdjacentRowsAfterInsertion(row, lower, upper)
        
        # Edge color smoothing: recolor the old edge row using interpolation
        if (modeId == "Manual" or modeId is None) and colorMode == "Manual":
            self.smoothEdgeColorAfterInsertion(row)

        self.tableView.clearSelection()
        self.tableView.selectRow(row)
        self.tableView.selectRow(row)
        self.updateClassCount()
        
        # Refresh all legend labels to apply correct rounding for the new number of classes
        self.refreshAllLegendLabels()

    def addCategoricalClass(self):
        """Add categorical value."""
        if self.tableView.rowCount() >= self.MAX_CLASSES:
             QMessageBox.critical(self, self.tr("Limit Exceeded"), self.tr(f"Maximum of {self.MAX_CLASSES} classes reached."))
             return

        if not self.availableUniqueValues:
            QMessageBox.information(self, "Info", "All values used.")
            return

        val = self.availableUniqueValues.pop(0)
        self.usedUniqueValues.append(val)
        
        sel = self.getSelectedRows()
        row = self.tableView.rowCount()
        if self.hasOtherValuesCategory(): row -= 1
        
        if sel and len(sel) == 1:
            item3 = self.tableView.cellWidget(sel[0], 3)
            if isinstance(item3, QLineEdit) and item3.text() in [self.tr("Other Values"), "Other Values"]:
                row = sel[0] # Insert before 'Other'
            elif self.btClassPlusAddBefore:
                row = sel[0]
            else:
                row = sel[0] + 1

        self.tableView.insertRow(row)
        sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        sym.setColor(self.generateRandomColor())

        # Set default size
        if self.currentLayer.geometryType() == 0:  # Point
            sym.setSize(3)
        elif self.currentLayer.geometryType() == 1:  # Line
            sym.setWidth(0.4)
        else:  # Polygon
            sym.setSize(1.5)

        disp = str(val)
        # Add unit abbreviation to legend if available
        unitAbbr = self.getCurrentLayerUnitAbbr()
        legendText = f"{val} {unitAbbr}" if unitAbbr else disp
        self.setRowWidgets(row, sym, True, disp, legendText, self.getGeometryHint(), isReadOnlyVal=True)
        
        self.tableView.clearSelection()
        self.tableView.selectRow(row)
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def removeClass(self):
        """Remove selected classes."""
        rows = sorted(self.getSelectedRows(), reverse=True)
        if not rows: return

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            for r in rows:
                w = self.tableView.cellWidget(r, 3)
                if isinstance(w, QLineEdit):
                    val = w.text()
                    if val != self.tr("Other Values") and val in self.usedUniqueValues:
                        self.usedUniqueValues.remove(val)
                        self.availableUniqueValues.append(val)
                self.tableView.removeRow(r)
            self._sortAvailableUniqueValues()
        else:
            lowest = rows[-1]
            for r in rows: self.tableView.removeRow(r)
            self.mergeAdjacentRowsAfterDeletion(lowest)
            # Don't re-apply classification method - let manual changes stand

        self.updateClassCount()
        
        # Refresh all legend labels to apply correct rounding for the new number of classes
        self.refreshAllLegendLabels()
        
        self.updateButtonStates()

        # NEW: Re-apply generic logic
        self.applyColorLogic()
        self.applySizeLogic()
        
        # Update spinbox limits for categorized layers
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.updateClassCountLimits()

    def _removeCategoricalRow(self, row):
        """Remove a single categorical row and return its value to available pool."""
        w = self.tableView.cellWidget(row, 3)
        if isinstance(w, QLineEdit):
            val = w.text()
            if val != self.tr("Other Values") and val in self.usedUniqueValues:
                self.usedUniqueValues.remove(val)
                self.availableUniqueValues.append(val)
        self.tableView.removeRow(row)
        self._sortAvailableUniqueValues()
        self.updateButtonStates()

    def updateClassCountLimits(self):
        """Update spinbox limits for categorized layers based on available unique values."""
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

    def moveClassUp(self):
        self._moveRow(-1)

    def moveClassDown(self):
        self._moveRow(1)

    def _moveRow(self, offset):
        """Helper to move single row."""
        rows = self.getSelectedRows()
        if len(rows) != 1: return
        r = rows[0]
        if not (0 <= r + offset < self.tableView.rowCount()): return
        self.swapTableRows(r, r + offset)
        self.tableView.selectRow(r + offset)

    def swapTableRows(self, r1, r2):
        """Swap widgets and content of two rows."""
        d1 = self._getRowData(r1)
        d2 = self._getRowData(r2)
        self._setRowData(r1, d2)
        self._setRowData(r2, d1)

    def _getRowData(self, row):
        """Extract all widget data from a row."""
        data = []
        for c in range(5):  # Now we have 5 columns (0-4)
            w = self.tableView.cellWidget(row, c)
            if c == 0:
                # Column 0: Container with checkbox
                if w:
                    checkbox = w.findChild(QCheckBox)
                    if checkbox:
                        data.append(('ck', checkbox.isChecked()))
                    else:
                        data.append(None)
                else:
                    data.append(None)
            elif c == 1:
                # Column 1: Container with QGISRedSymbolColorSelector
                if w:
                    colorSelector = w.findChild(QGISRedSymbolColorSelector)
                    if colorSelector:
                        data.append(('cs', colorSelector.color(), colorSelector.symbolSize, colorSelector.geometryHint()))
                    else:
                        data.append(None)
                else:
                    data.append(None)
            elif isinstance(w, QLineEdit):
                # Columns 2, 3, 4: Line edits
                # For column 3 (Value), check if it has double-click handler (numeric) or not (categorical)
                hasDoubleClick = c == 3 and hasattr(w, 'mouseDoubleClickEvent') and w.mouseDoubleClickEvent.__name__ == '<lambda>'
                data.append(('le', w.text(), w.isReadOnly(), hasDoubleClick))
            else:
                data.append(None)
        return data

    def _setRowData(self, row, data):
        """Recreate row widgets from data."""

        # Common style for inner widgets: Transparent background so Table selection shows through
        baseStyle = """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #2b2b2b;
            }
            QLineEdit:focus {
                border: 1px solid #3399ff; /* Visual cue when editing */
            }
        """

        readOnlyStyle = """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #808080;
            }
        """

        geom = self.getGeometryHint()
        for c, d in enumerate(data):
            if not d: continue
            dtype = d[0]

            if dtype == 'ck':
                # Column 0: Checkbox in container
                ckw = QCheckBox(self.tableView)
                ckw.setChecked(d[1])
                ckw.installEventFilter(self.rowSelectionFilter)
                containerWidget = QWidget(self.tableView)
                containerLayout = QHBoxLayout(containerWidget)
                containerLayout.setContentsMargins(0, 0, 0, 0)
                containerLayout.setSpacing(2)
                containerLayout.addWidget(ckw, 0, Qt.AlignVCenter | Qt.AlignHCenter)
                containerWidget.setAutoFillBackground(False)
                self.tableView.setCellWidget(row, c, containerWidget)

            elif dtype == 'cs':
                # Column 1: QGISRedSymbolColorSelector in container
                color = d[1]
                symbolSize = d[2]
                geomHint = d[3]

                cw = QGISRedSymbolColorSelector(self.tableView, geomHint, color, True, "Pick color", doubleClickOnly=True)
                cw.setEnabled(self.isEditing)
                cw.updateSymbolSize(symbolSize, geomHint == "line")
                cw.setAutoFillBackground(False)
                cw.setFixedSize(30, 20)

                colorContainer = QWidget(self.tableView)
                colorLayout = QHBoxLayout(colorContainer)
                colorLayout.setContentsMargins(0, 0, 0, 0)
                colorLayout.setSpacing(0)
                colorLayout.addStretch()
                colorLayout.addWidget(cw)
                colorLayout.addStretch()
                colorContainer.setAutoFillBackground(False)
                self.tableView.setCellWidget(row, c, colorContainer)

            elif dtype == 'le':
                # Columns 2, 3, 4: Line edits
                le = QLineEdit(d[1])
                le.setEnabled(self.isEditing)
                hasDoubleClick = d[3] if len(d) > 3 else False

                if d[2]:  # isReadOnly
                    le.setReadOnly(True)
                    if c == 3:  # Value column
                        le.setAlignment(Qt.AlignCenter)
                        if hasDoubleClick:  # Numeric - editable via double-click
                            le.setStyleSheet(baseStyle)
                            le.mouseDoubleClickEvent = lambda _event, r=row: self.openRangeEditor(r)
                        else:  # Categorical - truly read-only
                            le.setStyleSheet(readOnlyStyle)
                    else:  # Other read-only columns
                        le.setStyleSheet(baseStyle)
                else:
                    # Editable columns (Size and Legend) - standardized transparent background
                    le.setStyleSheet(baseStyle)

                if c == 2:  # Size column
                    le.setAlignment(Qt.AlignCenter)
                    le.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))

                # Install event filter for row selection
                le.installEventFilter(self.rowSelectionFilter)
                self.tableView.setCellWidget(row, c, le)

    # --- Numeric Logic & Classification ---

    def calculateInitialRangeForNewRow(self, row):
        """
        Determine deterministic range for new row using half-splitting logic.
        
        Rules:
        - If no rows exist → create [min, max] from layer data
        - If 1 row exists → split that row in half at midpoint
        - For further additions → split the selected row's range in half
        """
        total = self.tableView.rowCount()
        
        # Case 1: No rows exist - create first class with [min, max] from layer
        if total == 0:
            return self._getLayerMinMax()
        
        # Case 2: 1 row exists - we need to split it
        if total == 1:
            existing = self.getRangeValues(0)
            if existing:
                lower, upper = existing
                mid = (lower + upper) / 2.0
                # The new row will be inserted, and we'll update the existing row
                if row == 0:
                    # Inserting before: new row gets [lower, mid], existing gets [mid, upper]
                    return (lower, mid)
                else:
                    # Inserting after: existing stays [lower, mid], new row gets [mid, upper]
                    return (mid, upper)
            return self._getLayerMinMax()
        
        # Case 3: Multiple rows - split the selected or target row in half
        # Determine which row to split based on insertion position
        if row == 0:
            # Inserting at the beginning - split the first row
            splitRow = 0
        elif row >= total:
            # Inserting at the end - split the last row
            splitRow = total - 1
        else:
            # Inserting in the middle
            if self.btClassPlusAddBefore:
                # Add Before: split the row we're inserting before
                splitRow = row
            else:
                # Add After: split the row we're inserting after
                splitRow = row - 1
        
        targetRange = self.getRangeValues(splitRow)
        if targetRange:
            lower, upper = targetRange
            mid = (lower + upper) / 2.0
            
            if row <= splitRow:
                # Inserting before/at split position: new row gets lower half [lower, mid]
                return (lower, mid)
            else:
                # Inserting after split position: new row gets upper half [mid, upper]
                return (mid, upper)
        
        # Fallback
        return self._getLayerMinMax()
    
    def _getLayerMinMax(self):
        """Get min and max values from the current layer's numeric field."""
        vals = self.getNumericValues()
        if vals and len(vals) > 0:
            return (min(vals), max(vals))
        return (0.0, 1.0)

    def getRangeValues(self, row):
        """Parse range string from table."""
        widget = self.tableView.cellWidget(row, 3)  # Value Widget (column 3)
        if not isinstance(widget, QLineEdit): return None
        try:
            parts = widget.text().split(' - ')
            return float(parts[0]), float(parts[1])
        except: return None

    def updateAdjacentRowsAfterInsertion(self, row, newLower, newUpper):
        """
        Maintain contiguity after insert using half-splitting logic.
        
        When a row is split:
        - Update the adjacent row to the other half of the original range
        - Ensure neighbors maintain proper contiguity
        """
        total = self.tableView.rowCount()
        
        # Handle 2-row case (just split from single row)
        if total == 2:
            # One row was split into two - ensure proper ranges
            # Row 0 should end where Row 1 starts
            r0 = self.getRangeValues(0)
            r1 = self.getRangeValues(1)
            if r0 and r1:
                # If the new row is row 0, update row 1 to start at newUpper
                # If the new row is row 1, update row 0 to end at newLower
                if row == 0:
                    self.updateRangeValue(1, newUpper, None)
                else:
                    self.updateRangeValue(0, None, newLower)
            return
        
        # General case: Update the row that was split to its remaining half
        if row > 0:
            prevRange = self.getRangeValues(row - 1)
            if prevRange:
                prevLower, prevUpper = prevRange
                # If we took the upper half from prev, update prev to end at newLower
                if abs(prevUpper - newLower) < 0.0001 or prevUpper > newLower:
                    self.updateRangeValue(row - 1, None, newLower)
                    
        if row < total - 1:
            nextRange = self.getRangeValues(row + 1)
            if nextRange:
                nextLower, nextUpper = nextRange
                # If we took the lower half from next, update next to start at newUpper
                if abs(nextLower - newUpper) < 0.0001 or nextLower < newUpper:
                    self.updateRangeValue(row + 1, newUpper, None)

    def mergeAdjacentRowsAfterDeletion(self, rowPos):
        """Fill gap after delete."""
        if rowPos > 0 and rowPos < self.tableView.rowCount():
            curr = self.getRangeValues(rowPos)
            if curr: self.updateRangeValue(rowPos - 1, None, curr[0])

    def updateRangeValue(self, row, newLower=None, newUpper=None):
        """Update specific bounds of a row."""
        curr = self.getRangeValues(row)
        if not curr: return
        l, u = curr
        if newLower is not None: l = newLower
        if newUpper is not None: u = newUpper

        txt = f"{l:.2f} - {u:.2f}"
        vw = self.tableView.cellWidget(row, 3)  # Value Widget (column 3)
        if isinstance(vw, QLineEdit):
            vw.setText(txt)
        
        # Update legend text
        self.updateLegendsValues(row, l, u)

    def updateLegendsValues(self, row, lower, upper):
        """Update legend text for a row based on its position (first, middle, or last)."""
        lw = self.tableView.cellWidget(row, 4)  # Legend Widget (column 4)
        if not isinstance(lw, QLineEdit):
            return
            
        unitAbbr = self.getCurrentLayerUnitAbbr()
        totalRows = self.tableView.rowCount()
        
        # Calculate optimal rounding precision based on all values in the table
        vals = self.getNumericValues()
        if vals and len(vals) > 0:
            minV, maxV = min(vals), max(vals)
            try:
                m = self.calculateLegendRoundingPrecision(minV, maxV, totalRows)
                # Convert m to number of decimal places (negative m means more decimals)
                decimalPlaces = max(0, -m)
            except ValueError:
                decimalPlaces = 2  # Fallback to 2 decimal places
        else:
            decimalPlaces = 2  # Default fallback
        
        # Create format string based on calculated decimal places
        fmt = f"{{:.{decimalPlaces}f}}"
        
        if row == 0:
            # First row: "< {upper} {units}"
            if unitAbbr:
                newLegendTxt = f"< {fmt.format(upper)} {unitAbbr}"
            else:
                newLegendTxt = f"< {fmt.format(upper)}"
        elif row == totalRows - 1:
            # Last row: "> {lower} {units}"
            if unitAbbr:
                newLegendTxt = f"> {fmt.format(lower)} {unitAbbr}"
            else:
                newLegendTxt = f"> {fmt.format(lower)}"
        else:
            # Middle rows: "{lower} < {upper} {units}"
            if unitAbbr:
                newLegendTxt = f"{fmt.format(lower)} < {fmt.format(upper)} {unitAbbr}"
            else:
                newLegendTxt = f"{fmt.format(lower)} < {fmt.format(upper)}"
        lw.setText(newLegendTxt)

    def refreshAllLegendLabels(self):
        """Re-calculate and apply optimal rounding to all legend rows."""
        for r in range(self.tableView.rowCount()):
            vals = self.getRangeValues(r)
            if vals:
                self.updateLegendsValues(r, vals[0], vals[1])

    def getCurrentLayerUnitAbbr(self):
        """Get unit abbreviation for current layer from utils."""
        if not self.currentLayer or not self.utils:
            return ""
        layerIdent = self.currentLayer.customProperty("qgisred_identifier")
        if layerIdent:
            return self.utils.getUnitAbbreviationForLayer(layerIdent)
        return ""

    def calculateLegendRoundingPrecision(self, minValue, maxValue, intervals=10):
        """
        Calculate the optimal rounding precision for legend values.
        
        Args:
            minValue: Minimum value of the field
            maxValue: Maximum value of the field
            intervals: Number of classes/intervals (default: 10)
            
        Returns:
            int: The rounding precision exponent 'm'. 
                 - m = 0 means round to integers
                 - m = -1 means 1 decimal place
                 - m = -2 means 2 decimal places
                 - m = 1 means round to tens
                 - m = 2 means round to hundreds
                 
        Raises:
            ValueError: If intervals <= 0 or maxValue < minValue
        """
        if intervals <= 0:
            raise ValueError("intervals must be > 0")
        if maxValue < minValue:
            raise ValueError("maxValue must be >= minValue")

        increment = (maxValue - minValue) / intervals
        meanAbs = (abs(minValue) + abs(maxValue)) / 2.0

        m1 = math.floor(math.log10(meanAbs) - 2 + 0.5) if meanAbs > 0 else 0
        m2 = math.floor(math.log10(increment)) if increment > 0 else 0
        m = min(m1, m2)
        
        return m

    def calculateOptimalInterval(self):
        """Calculate nice interval for ~5 classes."""
        vals = self.getNumericValues()
        if not vals: return
        rng = max(vals) - min(vals)
        if rng == 0: 
            self.spinIntervalRange.setValue(1.0)
            return
            
        target = rng / 5.0
        mag = math.floor(math.log10(target))
        man = target / (10 ** mag)
        
        if man <= 1.5: nice = 1
        elif man <= 3: nice = 2
        elif man <= 7: nice = 5
        else: nice = 10
        
        self.spinIntervalRange.blockSignals(True)
        self.spinIntervalRange.setValue(nice * (10 ** mag))
        self.spinIntervalRange.blockSignals(False)

    def applyClassificationMethod(self, methodId):
        """Apply algorithm to generate classes."""
        vals = self.getNumericValues()
        if not vals: return
        
        num = self.tableView.rowCount() or 5
        minV, maxV = min(vals), max(vals)
        breaks = []

        if methodId == "EqualInterval":
            step = (maxV - minV) / num
            breaks = [minV + i*step for i in range(num + 1)]
        elif methodId == "FixedInterval":
            step = self.spinIntervalRange.value()
            breaks = [minV]
            curr = minV
            while curr < maxV:
                curr += step
                breaks.append(curr)
            num = len(breaks) - 1
        elif methodId == "Quantile":
            breaks = [minV] + [vals[min(int(i/num * len(vals)), len(vals) - 1)] for i in range(1, num)] + [maxV]
        elif methodId == "Jenks":
            m = QgsClassificationJenks()
            m.setLabelFormat("%1 - %2")
            c = m.classes(self.currentLayer, self.currentFieldName, num)
            breaks = [minV] + [x.upperBound() for x in c]
            num = len(breaks) - 1
        elif methodId == "StdDev":
            mu = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0
            breaks = sorted(list(set([minV, maxV] + [mu + i*sd for i in range(-num//2, num//2 + 1) if minV < mu + i*sd < maxV])))
            num = len(breaks) - 1
        elif methodId == "Pretty":
            m = QgsClassificationPrettyBreaks()
            c = m.classes(self.currentLayer, self.currentFieldName, num)
            breaks = [minV] + [x.upperBound() for x in c]
            num = len(breaks) - 1

        if len(breaks) < 2: return
        # Adjust row count
        while self.tableView.rowCount() < num: self.addNumericClass()
        while self.tableView.rowCount() > num: self.tableView.removeRow(self.tableView.rowCount()-1)

        # Calculate optimal rounding precision for legend formatting
        try:
            m = self.calculateLegendRoundingPrecision(minV, maxV, num)
            decimalPlaces = max(0, -m)
        except ValueError:
            decimalPlaces = 2  # Fallback
        
        fmt = f"{{:.{decimalPlaces}f}}"
        unitAbbr = self.getCurrentLayerUnitAbbr()

        # Apply breaks and update legends with rounding precision
        for i in range(num):
            l, u = breaks[i], breaks[i+1]
            txt = f"{fmt.format(l)} - {fmt.format(u)}"
            vw = self.tableView.cellWidget(i, 3)  # Value Widget (column 3)
            if isinstance(vw, QLineEdit):
                vw.setText(txt)

            # Format legend based on position (first, middle, last)
            lw = self.tableView.cellWidget(i, 4)  # Legend Widget (column 4)
            if isinstance(lw, QLineEdit):
                if i == 0:
                    # First row: "< {upper} {units}"
                    if unitAbbr:
                        legendTxt = f"< {fmt.format(u)} {unitAbbr}"
                    else:
                        legendTxt = f"< {fmt.format(u)}"
                elif i == num - 1:
                    # Last row: "> {lower} {units}"
                    if unitAbbr:
                        legendTxt = f"> {fmt.format(l)} {unitAbbr}"
                    else:
                        legendTxt = f"> {fmt.format(l)}"
                else:
                    # Middle rows: "{lower} < {upper} {units}"
                    if unitAbbr:
                        legendTxt = f"{fmt.format(l)} < {fmt.format(u)} {unitAbbr}"
                    else:
                        legendTxt = f"{fmt.format(l)} < {fmt.format(u)}"
                lw.setText(legendTxt)

        self.updateClassCount()

        # NEW: Re-apply generic logic after classification
        self.applyColorLogic()
        self.applySizeLogic()

    def getNumericValues(self):
        """Get list of float values from layer."""
        if not self.currentLayer or not self.currentFieldName: return []
        vals = []
        for f in self.currentLayer.getFeatures():
            try: vals.append(float(f[self.currentFieldName]))
            except: pass
        return sorted(vals)

    # --- Editing Logic ---

    def openRangeEditor(self, row):
        """Open range dialog."""
        # Check if we are in Manual mode
        modeId = self.cbMode.currentData()
        if modeId and modeId != "Manual":
            # Optional: Show a message or just silently return
            # QMessageBox.information(self, "Mode Restriction", "Please switch to 'Manual' mode to edit range values values.")
            return

        curr = self.getRangeValues(row)
        if not curr: return
        
        # Get unit abbreviation for current layer (supports diameters and lengths)
        unitAbbr = ""
        if self.currentLayer and self.utils:
            layerIdent = self.currentLayer.customProperty("qgisred_identifier")
            if layerIdent:
                unitAbbr = self.utils.getUnitAbbreviationForLayer(layerIdent)
        
        dlg = QGISRedRangeEditDialog(curr[0], curr[1], self, unitAbbr=unitAbbr)
        if dlg.exec_():
            nl, nu = dlg.getValues()

            # Sanity check for the range itself
            if nl >= nu:
                QMessageBox.warning(self, "Invalid Range", "Min value must be less than Max value.")
                return

            # Check overflow against previous row
            if row > 0:
                prev = self.getRangeValues(row - 1)
                if prev and nl < prev[0]:
                    QMessageBox.warning(self, "Range Overflow", f"New minimum ({nl}) is smaller than the previous row's minimum ({prev[0]}).\nCannot apply changes.")
                    return

            # Check overflow against next row
            if row < self.tableView.rowCount() - 1:
                nxt = self.getRangeValues(row + 1)
                if nxt and nu > nxt[1]:
                    QMessageBox.warning(self, "Range Overflow", f"New maximum ({nu}) is larger than the next row's maximum ({nxt[1]}).\nCannot apply changes.")
                    return

            # If we passed checks, apply update
            self.updateRangeValue(row, nl, nu)
            
            # Update neighbors to maintain contiguity
            if row > 0: self.updateRangeValue(row - 1, None, nl)
            if row < self.tableView.rowCount() - 1: self.updateRangeValue(row + 1, nu, None)

    def onSizeChanged(self, row, text):
        """Live update of preview size."""
        try:
            s = float(text)
            colorContainer = self.tableView.cellWidget(row, 1)  # Color container (column 1)
            cw = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if cw:
                cw.updateSymbolSize(s, self.currentLayer.geometryType() == 1)
        except: pass

    # --- Saving/Applying ---

    def applyLegend(self):
        """Apply current table state to layer renderer."""
        if not self.currentLayer: return
        
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            ranges = []
            for r in range(self.tableView.rowCount()):
                vals = self.getRangeValues(r)
                if not vals: continue
                ckContainer = self.tableView.cellWidget(r, 0)  # Checkbox container (column 0)
                colorContainer = self.tableView.cellWidget(r, 1)  # Color container (column 1)
                lw = self.tableView.cellWidget(r, 4)  # Legend Widget (column 4)
                sw = self.tableView.cellWidget(r, 2)  # Size Widget (column 2)
                
                # Get checkbox from container
                ckw = ckContainer.findChild(QCheckBox) if ckContainer else None
                # Get color widget from container
                cw = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
                
                sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
                if cw:
                    sym.setColor(cw.color())
                try:
                    s = float(sw.text())
                    if self.currentLayer.geometryType() == 1: sym.setWidth(s)
                    else: sym.setSize(s)
                except: pass
                
                rng = QgsRendererRange(vals[0], vals[1], sym, lw.text())
                rng.setRenderState(ckw.isChecked() if ckw else True)
                ranges.append(rng)
            
            if ranges: self.currentLayer.setRenderer(QgsGraduatedSymbolRenderer(self.currentFieldName, ranges))

        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            cats = []
            for r in range(self.tableView.rowCount()):
                ckContainer = self.tableView.cellWidget(r, 0)  # Checkbox container (column 0)
                colorContainer = self.tableView.cellWidget(r, 1)  # Color container (column 1)
                lw = self.tableView.cellWidget(r, 4)  # Legend Widget (column 4)
                vw = self.tableView.cellWidget(r, 3)  # Value Widget (column 3)
                sw = self.tableView.cellWidget(r, 2)  # Size Widget (column 2)
                
                # Get checkbox from container
                ckw = ckContainer.findChild(QCheckBox) if ckContainer else None
                # Get color widget from container
                cw = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
                
                val = vw.text() if isinstance(vw, QLineEdit) else ""
                label = lw.text()
                
                realVal = val
                if val == "NULL": realVal = None
                elif val == "" and label in [self.tr("Other Values"), "Other Values"]: realVal = ""
                
                sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
                if cw:
                    sym.setColor(cw.color())
                try:
                    s = float(sw.text())
                    if self.currentLayer.geometryType() == 1: sym.setWidth(s)
                    else: sym.setSize(s)
                except: pass
                
                cat = QgsRendererCategory(realVal, sym, label)
                cat.setRenderState(ckw.isChecked() if ckw else True)
                cats.append(cat)
                
            if cats: self.currentLayer.setRenderer(QgsCategorizedSymbolRenderer(self.currentFieldName, cats))
            
        self.currentLayer.triggerRepaint()

    def saveProjectStyle(self):
        self._saveStyle(globalStyle=False)

    def saveGlobalStyle(self):
        self._saveStyle(globalStyle=True)

    def _saveStyle(self, globalStyle):
        if not self.currentLayer: return
        ident = self.currentLayer.customProperty("qgisred_identifier")
        if not ident: return

        # Use utils instance instead of creating new QGISRedUtils
        if self.utils:
            name = self.utils.identifierToElementName.get(ident)
        else:
            name = QGISRedUtils().identifierToElementName.get(ident)
        if not name: return

        fname = name.replace(" ", "") + ".qml"

        if globalStyle:
            folder = os.path.join(self.pluginFolder, "layerStyles")
        else:
            # Use utils to get project directory
            if self.utils:
                projectDir = self.utils.getProjectDirectory()
            else:
                projectDir = self.ProjectDirectory

            if not projectDir:
                QMessageBox.warning(self, "No Project", "Project directory not set.")
                return

            folder = os.path.join(projectDir, "layerStyles")

        if not folder: return
        if not os.path.exists(folder): os.makedirs(folder)

        path = os.path.join(folder, fname)
        if os.path.exists(path):
            if QMessageBox.question(self, "Overwrite", "Overwrite style?", QMessageBox.Yes|QMessageBox.No) != QMessageBox.Yes: return

        self.currentLayer.saveNamedStyle(path)
        QMessageBox.information(self, "Saved", f"Style saved to {path}")

    def loadDefaultStyle(self):
        self._loadStyle(isDefault=True)

    def loadGlobalStyle(self):
        self._loadStyle(isDefault=False)

    def loadProjectStyle(self):
        """Load style from project-specific location."""
        if not self.currentLayer:
            return
        ident = self.currentLayer.customProperty("qgisred_identifier")

        # Use utils instance instead of creating new QGISRedUtils
        if self.utils:
            name = self.utils.identifierToElementName.get(ident)
        else:
            name = QGISRedUtils().identifierToElementName.get(ident)
        if not name:
            return

        fname = name.replace(" ", "") + ".qml"

        # Use utils to get project directory
        if self.utils:
            projectDir = self.utils.getProjectDirectory()
        else:
            projectDir = self.ProjectDirectory

        if not projectDir:
            QMessageBox.warning(self, "No Project", "Project directory not set.")
            return

        folder = os.path.join(projectDir, "layerStyles")
        path = os.path.join(folder, fname)

        if not os.path.exists(path):
            QMessageBox.warning(self, "Not Found", f"Style file not found: {path}")
            return

        self.currentLayer.loadNamedStyle(path)
        self.currentLayer.triggerRepaint()
        self.onLayerChanged(self.currentLayer)
        QMessageBox.information(self, "Loaded", f"Style loaded from {path}")

    def _loadStyle(self, isDefault):
        if not self.currentLayer: return
        ident = self.currentLayer.customProperty("qgisred_identifier")

        # Use utils instance instead of creating new QGISRedUtils
        if self.utils:
            name = self.utils.identifierToElementName.get(ident)
        else:
            name = QGISRedUtils().identifierToElementName.get(ident)
        if not name: return

        fname = name.replace(" ", "") + ".qml" + (".bak" if isDefault else "")
        sub = os.path.join("defaults", "layerStyles") if isDefault else "layerStyles"
        path = os.path.join(self.pluginFolder, sub, fname)

        if not os.path.exists(path):
            QMessageBox.warning(self, "Not Found", f"Style file not found: {path}")
            return

        self.currentLayer.loadNamedStyle(path)
        self.currentLayer.triggerRepaint()
        self.onLayerChanged(self.currentLayer)
        QMessageBox.information(self, "Loaded", f"Style loaded from {path}")

    # --- Utilities ---

    def getLayerUnits(self):
        """
        Helper to retrieve units from QGISRedUtils (returns 'SI' or 'US').
        """
        if not self.utils:
            return ""

        try:
            return self.utils.getUnits()
        except:
            return ""

    def getGeometryHint(self):
        if not self.currentLayer: return "fill"
        gt = self.currentLayer.geometryType()
        return "marker" if gt == 0 else "line" if gt == 1 else "fill"

    def generateRandomColor(self):
        c = QColor()
        c.setHsl(random.randint(0, 359), random.randint(178, 255), random.randint(102, 178))
        return c

    def getRowColor(self, row):
        """Get the color from a specific row's color widget."""
        if row < 0 or row >= self.tableView.rowCount():
            return None
        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            cw = colorContainer.findChild(QGISRedSymbolColorSelector)
            if cw:
                return cw.color()
        return None

    def calculateIntermediateColor(self, color1, color2):
        """Calculate the intermediate color between two colors."""
        r = (color1.red() + color2.red()) // 2
        g = (color1.green() + color2.green()) // 2
        b = (color1.blue() + color2.blue()) // 2
        return QColor(r, g, b)

    def calculateComplementaryColor(self, color):
        """Calculate the complementary color (opposite on the color wheel)."""
        h, s, l, a = color.getHsl()
        # Add 180 degrees to hue for complementary color (opposite on color wheel)
        complementary_h = (h + 180) % 360
        complementary_color = QColor()
        complementary_color.setHsl(complementary_h, s, l, a)
        return complementary_color

    def getSmartColorForNewRow(self, insertionRow):
        """
        Determine the color for a new row based on its position when both
        intervals and colors are in manual mode.

        Rules:
        - First class (rowCount == 0): totally random color
        - Second class (rowCount == 1): complementary color of the first class
        - If inserting between two classes: use intermediate color of neighbors
        - If inserting at end (last class): use color of current last class
        - If inserting at first position:
            - If 2+ existing classes: use color of current first class
        """
        rowCount = self.tableView.rowCount()

        # Empty table - first class gets totally random color
        if rowCount == 0:
            return self.generateRandomColor()

        # Single row - second class gets complementary color of first
        if rowCount == 1:
            firstColor = self.getRowColor(0)
            if firstColor:
                return self.calculateComplementaryColor(firstColor)
            else:
                return self.generateRandomColor()
        
        # Inserting at position 0 (first)
        if insertionRow == 0:
            # Use the color of the current first row (which will become second)
            firstColor = self.getRowColor(0)
            return firstColor if firstColor else self.generateRandomColor()
        
        # Inserting at end (after all existing rows)
        if insertionRow >= rowCount:
            # Use the color of the current last row
            lastColor = self.getRowColor(rowCount - 1)
            return lastColor if lastColor else self.generateRandomColor()
        
        # Inserting between two existing rows
        prevColor = self.getRowColor(insertionRow - 1)
        nextColor = self.getRowColor(insertionRow)
        
        if prevColor and nextColor:
            return self.calculateIntermediateColor(prevColor, nextColor)
        elif prevColor:
            return prevColor
        elif nextColor:
            return nextColor
        else:
            return self.generateRandomColor()

    def smoothEdgeColorAfterInsertion(self, insertedRow):
        """
        Apply edge color smoothing after insertion when there are ≥3 classes.
        
        When inserting at the top:
        - New first row already has the old first's color
        - Old first (now row 1) gets interpolated color between new first and last
        
        When inserting at the bottom:
        - New last row already has the old last's color  
        - Old last (now second-to-last) gets interpolated color between
          new last and the antepenultimate (row before old last)
        """
        rowCount = self.tableView.rowCount()
        
        # Need at least 3 classes for edge smoothing to apply
        if rowCount < 3:
            return
        
        # Case: Inserted at first position (row 0)
        if insertedRow == 0:
            # Old first is now at row 1
            newFirstColor = self.getRowColor(0)  # New first row color (same as old first was)
            lastColor = self.getRowColor(rowCount - 1)  # Last row color
            
            if newFirstColor and lastColor:
                interpolatedColor = self.calculateIntermediateColor(newFirstColor, lastColor)
                self.setRowColor(1, interpolatedColor)
        
        # Case: Inserted at last position (after all existing rows)
        elif insertedRow == rowCount - 1:
            # Old last is now at row (rowCount - 2)
            newLastColor = self.getRowColor(rowCount - 1)  # New last row color (same as old last was)
            
            # Antepenultimate is the row before old last, which is now at (rowCount - 3)
            if rowCount >= 3:
                antepenultimateColor = self.getRowColor(rowCount - 3)
            else:
                antepenultimateColor = None
            
            if newLastColor and antepenultimateColor:
                interpolatedColor = self.calculateIntermediateColor(newLastColor, antepenultimateColor)
                self.setRowColor(rowCount - 2, interpolatedColor)

    def setRowColor(self, row, color):
        """Set the color of a specific row's color widget."""
        if row < 0 or row >= self.tableView.rowCount():
            return
        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            cw = colorContainer.findChild(QGISRedSymbolColorSelector)
            if cw:
                cw.setColor(color)

    def getSelectedRows(self):
        return [i.row() for i in self.tableView.selectionModel().selectedRows()]

    def updateClassCount(self):
        self.leClassCount.setValue(self.tableView.rowCount())

    def updateButtonStates(self):
        if not self.currentLayer: return

        selected_rows = self.getSelectedRows()
        sel_count = len(selected_rows)

        isCat = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL

        # Check specific numeric modes
        modeId = self.cbMode.currentData()
        # TASK 5.3: Distinguish Manual vs Automatic numeric modes
        isManualNumeric = (self.currentFieldType == self.FIELD_TYPE_NUMERIC and (modeId is None or modeId == "Manual"))
        isAutoNumeric = (self.currentFieldType == self.FIELD_TYPE_NUMERIC and not isManualNumeric)

        # 1. Logic for 'Add' button
        if isCat:
            # Categorical logic: Disable on multi-selection
            if sel_count > 1:
                self.btClassPlus.setEnabled(False)
            else:
                self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())

        elif isAutoNumeric:
            # TASK 5.3: Keep Plus Button Active in Automatic Modes
            # Always enable add button in automatic modes (Equal, Jenks, Fixed Interval, etc)
            # Adding a class triggers re-calculation of the algorithm
            self.btClassPlus.setEnabled(True)

        else:  # Manual Numeric
            # Disable if multiple rows selected (cannot determine where to insert easily)
            self.btClassPlus.setEnabled(sel_count <= 1)

        # 2. Logic for removal button
        # Fixed Interval disables removal (maintains original behavior)
        if modeId == "FixedInterval":
            self.btClassMinus.setEnabled(False)
        else:
            self.btClassMinus.setEnabled(sel_count >= 1)

        # 3. Logic for Reordering (Only allowed for Categorical with single selection)
        if isCat:
            can_move = (sel_count == 1)
            if can_move:
                row_idx = selected_rows[0]
                self.btUp.setEnabled(row_idx > 0)
                self.btDown.setEnabled(row_idx < self.tableView.rowCount() - 1)
            else:
                self.btUp.setEnabled(False)
                self.btDown.setEnabled(False)
        else:
            # Numeric mode doesn't allow manual reordering (values are sorted by definition)
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)

    def updateAddClassButtonState(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())

    def hasOtherValuesCategory(self):
        for r in range(self.tableView.rowCount()):
            w = self.tableView.cellWidget(r, 4)  # Legend Widget (column 4)
            if isinstance(w, QLineEdit) and w.text() in [self.tr("Other Values"), "Other Values"]: return True
        return False

    def ensureOtherValuesCategory(self):
        """Add 'Other Values' category if it doesn't exist."""
        if self.hasOtherValuesCategory():
            return

        # Create "Other Values" category directly without recursion
        row = self.tableView.rowCount()
        self.tableView.insertRow(row)

        sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        sym.setColor(self.generateRandomColor())

        self.setRowWidgets(row, sym, True, self.tr("Other Values"), self.tr("Other Values"),
                          self.getGeometryHint(), isReadOnlyVal=True)

        self.updateClassCount()

    def cancelAndClose(self):
        if self.currentLayer and self.originalRenderer and self.isEditing:
            self.currentLayer.setRenderer(self.originalRenderer.clone())
            self.currentLayer.triggerRepaint()
        self.reject()

    def eventFilter(self, obj, event):
        """Handle clicks outside the table to clear selection and right-click on Plus button."""

        # Logic for Right-Click on '+' Button
        if obj == self.btClassPlus and event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.RightButton:
                if self.btClassPlus.isEnabled():
                    # TASK 5.1 & User Request:
                    # Right Click + Row Selected = Add class ABOVE (for both Numeric and Categorical)
                    # Note: "Classify All" for Categorical is now handled via Double-Click in addClass()

                    self.btClassPlusAddBefore = True  # Set flag to add ABOVE
                    self.executeAddClass()            # Execute addition (routes to addCategoricalClass or addNumericClass)
                    self.btClassPlusAddBefore = False # Reset flag

                    return True  # Consume event

        # Handle clicks outside the table to clear selection
        if obj == self and event.type() == QEvent.MouseButtonPress:
            # Check if the click is outside the tableView
            clickPos = event.pos()
            tableGeometry = self.tableView.geometry()
            if not tableGeometry.contains(clickPos):
                # Click is outside the table, clear selection
                self.tableView.clearSelection()

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Clean up connections when dialog is closed."""
        # Disconnect layer tree view signal
        if self.layerTreeViewConnection and iface and iface.layerTreeView():
            try:
                iface.layerTreeView().currentLayerChanged.disconnect(self.onQgisLayerSelectionChanged)
            except:
                pass

        # --- NEW: Disconnect Project/Tree signals ---
        try:
            if hasattr(self, 'layerTreeRoot') and self.layerTreeRoot:
                self.layerTreeRoot.visibilityChanged.disconnect(self.onTreeNodeVisibilityChanged)
            QgsProject.instance().layersWillBeRemoved.disconnect(self.onLayersWillBeRemoved)
            QgsProject.instance().layersAdded.disconnect(self.onProjectLayersChanged)
            QgsProject.instance().layersRemoved.disconnect(self.onProjectLayersChanged)
        except:
            pass
        # --------------------------------------------

        # Clean up parent reference to allow garbage collection
        if self.parent and hasattr(self.parent, 'legendsDialog'):
            self.parent.legendsDialog = None

        super().closeEvent(event)