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
                             QCheckBox, QDoubleSpinBox)
from PyQt5.QtCore import QVariant, Qt, QTimer, QObject, QEvent
from qgis.PyQt import uic

# QGIS imports
from qgis.core import (QgsProject, QgsVectorLayer, QgsMessageLog, Qgis,
                       QgsGraduatedSymbolRenderer, QgsCategorizedSymbolRenderer,
                       QgsRendererRange, QgsRendererCategory, QgsSymbol,
                       QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGradientColorRamp,
                       QgsClassificationJenks, QgsClassificationPrettyBreaks,
                       QgsStyle, QgsPresetSchemeColorRamp, QgsColorRamp)
from qgis.gui import QgsColorButton
from qgis.utils import iface

# Local imports
from ..tools.qgisred_utils import QGISRedUtils
from .qgisred_custom_dialogs import RangeEditDialog, SymbolColorSelectorWithCheckbox

# Load UI
formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

class RowSelectionFilter(QObject):
    """
    Event filter to ensure clicking a cell widget selects the underlying table row.
    """
    def __init__(self, table):
        super(RowSelectionFilter, self).__init__(table)
        self.table = table

    def eventFilter(self, widget, event):
        if event.type() == QEvent.FocusIn:
            # Find the widget's position in the table
            index = self.table.indexAt(widget.pos())
            if index.isValid():
                self.table.selectRow(index.row())
                # Ensure the selection color shows immediately
                self.table.viewport().update()
        return False

class QGISRedLegendsDialog(QDialog, formClass):
    FIELD_TYPE_NUMERIC = 'numeric'
    FIELD_TYPE_CATEGORICAL = 'categorical'
    FIELD_TYPE_UNKNOWN = 'unknown'
    ALLOWED_GROUP_IDENTIFIERS = ["qgisred_thematicmaps"]

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
        self.style = None  # QGISRed style database

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

    def initUi(self):
        """Initialize UI components."""
        self.configWindow()
        self.setupTableView()
        self.populateClassificationModes()
        self.populateGroups()
        self.setupClassCountField()

        # NEW: Setup Advanced Color and Size UI
        self.setupAdvancedUi()
        self.loadStyleDatabase()
        self.applyConsistentStyling()

        self.labelIntervalRange.setVisible(False)
        self.spinIntervalRange.setVisible(False)

        # Install event filter on dialog to detect clicks outside table
        self.installEventFilter(self)

    def configWindow(self):
        """Configure window appearance."""
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))
        self.setWindowTitle("QGISRed Legend Editor")
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)

        self.btClassPlus.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))


    def setupTableView(self):
        """Configure table columns and visual style."""
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(["Symbol", "Size", "Value", "Legend"])

        # Initialize Event Filter for row selection logic
        self.rowSelectionFilter = RowSelectionFilter(self.tableView)

        header = self.tableView.horizontalHeader()

        # 0: Symbol (Fixed Icon size)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableView.setColumnWidth(0, 50)

        # 1: Size (Fixed small width)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableView.setColumnWidth(1, 60)

        # 2: Value (Stretch - takes up available space)
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        # 3: Legend (Stretch - takes up available space)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

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
        """Configure read-only class count field."""
        self.leClassCount.setReadOnly(True)
        self.leClassCount.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.leClassCount.setStyleSheet("QSpinBox { background-color: #F0F0F0; color: #808080; }")

    def setupAdvancedUi(self):
        self.cbSizes.addItems(["Manual", "Equal", "Linear", "Quadratic", "Exponential"])
        self.cbSizes.currentIndexChanged.connect(self.onSizeModeChanged)
        self.spinSizeEqual.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMax.valueChanged.connect(self.applySizeLogic)
        self.ckSizeInvert.toggled.connect(self.applySizeLogic)

        self.cbColors.addItems(["Manual", "Equal", "Random", "Ramp", "Palette"])
        self.cbColors.currentIndexChanged.connect(self.onColorModeChanged)
        self.btColorEqual.setColor(QColor("red"))
        self.btColorEqual.colorChanged.connect(self.applyColorLogic)
        self.cbColorRampPalette.currentIndexChanged.connect(self.applyColorLogic)
        self.ckColorInvert.toggled.connect(self.applyColorLogic)

        # Setup refresh colors button
        self.btRefreshColors.setIcon(QIcon(":/images/themes/default/mActionRefresh.svg"))
        self.btRefreshColors.clicked.connect(self.applyColorLogic)

        self.onSizeModeChanged()
        self.onColorModeChanged()

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
        self.cbSizes.setStyleSheet(editableComboStyle)
        self.cbColors.setStyleSheet(editableComboStyle)
        self.cbColorRampPalette.setStyleSheet(editableComboStyle)

        # Apply to spin boxes
        self.spinIntervalRange.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeEqual.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeMin.setStyleSheet(editableSpinBoxStyle)
        self.spinSizeMax.setStyleSheet(editableSpinBoxStyle)

        # Apply to checkboxes
        #self.ckSizeInvert.setStyleSheet(editableCheckBoxStyle)
        #self.ckColorInvert.setStyleSheet(editableCheckBoxStyle)

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
        self.tableView.itemSelectionChanged.connect(self.updateButtonStates)
        self.tableView.itemClicked.connect(lambda item: self.tableView.selectRow(item.row()) if item else None)

        # Connect to layer tree view to track layer selection changes
        if iface and iface.layerTreeView():
            self.layerTreeViewConnection = iface.layerTreeView().currentLayerChanged.connect(self.onQgisLayerSelectionChanged)

    def loadInitialState(self):
        """Preselect group/layer and set initial state."""
        self.preselectGroupAndLayer()
        self.frameLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.labelFrameLegends.setText(self.tr("Legend"))
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())
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
        allowed = self.getRenderableLayersInSelectedGroup()
        allLayers = list(QgsProject.instance().mapLayers().values())
        excepted = [l for l in allLayers if l not in allowed]

        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(excepted)

        if allowed:
            self.cbLegendLayer.setLayer(allowed[0])
        else:
            # Explicitly set to None if no renderable layers exist in this group
            self.cbLegendLayer.setLayer(None)

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
            self.currentLayer = layer
            self.originalRenderer = layer.renderer().clone() if layer.renderer() else None
            self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)

            self.frameLegends.setEnabled(True)

            # Get Units and update Label
            baseTitle = self.tr(f"Legend for {layer.name()}")
            units = self.getLayerUnits()

            if units:
                self.labelFrameLegends.setText(f"{baseTitle} | Units: {units}")
            else:
                self.labelFrameLegends.setText(baseTitle)

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

    def onCellDoubleClicked(self, row, column):
        """Route double click to specific editors."""
        if column == 2 and self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.openRangeEditor(row)

    # --- Advanced Size & Color UI Logic ---

    def onSizeModeChanged(self):
        """Handle size mode change."""
        mode = self.cbSizes.currentText()
        self.spinSizeEqual.setVisible(mode == "Equal")
        self.spinSizeMin.setVisible(mode in ["Linear", "Quadratic", "Exponential"])
        self.spinSizeMax.setVisible(mode in ["Linear", "Quadratic", "Exponential"])
        self.ckSizeInvert.setVisible(mode != "Manual" and mode != "Equal")
        self.applySizeLogic()

    def onColorModeChanged(self):
        """Handle color mode change."""
        mode = self.cbColors.currentText()
        self.btColorEqual.setVisible(mode == "Equal")
        self.cbColorRampPalette.setVisible(mode in ["Ramp", "Palette"])
        self.ckColorInvert.setVisible(mode in ["Ramp", "Palette"])
        self.btRefreshColors.setVisible(mode == "Random")

        if mode == "Ramp":
            self.populateRamps()
        elif mode == "Palette":
            self.populatePalettes()

        self.applyColorLogic()

    def populateRamps(self):
        """Populate color ramps from style database."""
        self.cbColorRampPalette.blockSignals(True)
        self.cbColorRampPalette.clear()

        if self.style:
            # Load Gradient Ramps from Style
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsGradientColorRamp):
                    self.cbColorRampPalette.addItem(name, ramp)

        # If no ramps found, add default gradient
        if self.cbColorRampPalette.count() == 0:
            defaultRamp = QgsGradientColorRamp(QColor(0, 0, 255), QColor(255, 0, 0))
            self.cbColorRampPalette.addItem("Default (Blue to Red)", defaultRamp)

        self.cbColorRampPalette.blockSignals(False)

    def populatePalettes(self):
        """Populate color palettes from style database."""
        self.cbColorRampPalette.blockSignals(True)
        self.cbColorRampPalette.clear()

        if self.style:
            # Load Preset Schemes (Palettes)
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                # QGIS treats Palettes as PresetSchemeColorRamp
                if isinstance(ramp, QgsPresetSchemeColorRamp):
                    self.cbColorRampPalette.addItem(name, ramp)

        # If no palettes found, create a default one
        if self.cbColorRampPalette.count() == 0:
            # Create a simple default palette
            defaultColors = [QColor(255, 0, 0), QColor(0, 255, 0), QColor(0, 0, 255),
                           QColor(255, 255, 0), QColor(255, 0, 255), QColor(0, 255, 255)]
            defaultPalette = QgsPresetSchemeColorRamp(defaultColors)
            self.cbColorRampPalette.addItem("Default Palette", defaultPalette)

        self.cbColorRampPalette.blockSignals(False)

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
            sw = self.tableView.cellWidget(r, 1)  # Size Widget
            cw = self.tableView.cellWidget(r, 0)  # Color/Symbol Widget
            if sw:
                sw.blockSignals(True)
                sw.setText(f"{sizes[r]:.2f}")
                sw.blockSignals(False)
            if cw:
                cw.updateSymbolSize(sizes[r], isLine)

    def applyColorLogic(self):
        """Apply color algorithm based on selected mode."""
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
            colors = [self.generateRandomColor() for _ in range(rows)]

        elif mode == "Ramp":
            ramp = self.cbColorRampPalette.currentData()
            if isinstance(ramp, QgsGradientColorRamp):
                colors = self.algorithmRamp(ramp, rows)
            else:
                colors = [self.generateRandomColor() for _ in range(rows)]

        elif mode == "Palette":
            palette = self.cbColorRampPalette.currentData()
            if isinstance(palette, QgsPresetSchemeColorRamp):
                colors = self.algorithmPalette(palette, rows)
            else:
                colors = [self.generateRandomColor() for _ in range(rows)]

        # Apply Inversion for Ramp/Palette
        if mode in ["Ramp", "Palette"] and self.ckColorInvert.isChecked():
            colors.reverse()

        # Update Table
        for r in range(rows):
            cw = self.tableView.cellWidget(r, 0)
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

        # If cbGroups is empty (no valid groups found),
        # explicitly clear the dependent layer combo and reset the UI.
        if self.cbGroups.count() == 0:
            self.cbLegendLayer.blockSignals(True)
            # Except all layers to ensure the combo appears empty
            self.cbLegendLayer.setExceptedLayerList(list(QgsProject.instance().mapLayers().values()))
            self.cbLegendLayer.setLayer(None)
            self.cbLegendLayer.blockSignals(False)

            # Force the UI to update to the 'no layer' state
            self.onLayerChanged(None)

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

        # Color
        cw = SymbolColorSelectorWithCheckbox(self.tableView, geom, symbol.color(), visible, "")
        cw.colorSelector.setEnabled(self.isEditing)
        size = symbol.width() if geom == "line" else symbol.size()
        cw.updateSymbolSize(size, geom == "line")
        # Ensure custom widget background doesn't block selection
        cw.setAutoFillBackground(False)
        self.tableView.setCellWidget(row, 0, cw)

        # Size
        sw = QLineEdit(str(size))
        sw.setEnabled(self.isEditing)
        sw.setAlignment(Qt.AlignCenter)
        sw.setStyleSheet(baseStyle)
        sw.installEventFilter(self.rowSelectionFilter)  # Install filter
        sw.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))
        self.tableView.setCellWidget(row, 1, sw)

        # Value
        vw = QLineEdit(valText)
        vw.setReadOnly(True)
        vw.setAlignment(Qt.AlignCenter)

        if isReadOnlyVal:
            vw.setStyleSheet(readOnlyStyle)
        else:
            # If numeric, it looks like regular text but is read-only until dbl-click
            vw.setStyleSheet(baseStyle)
            vw.mouseDoubleClickEvent = lambda _event, r=row: self.openRangeEditor(r)

        vw.installEventFilter(self.rowSelectionFilter)  # Install filter
        self.tableView.setCellWidget(row, 2, vw)

        # Legend
        lw = QLineEdit(legendText)
        lw.setEnabled(self.isEditing)
        lw.setStyleSheet(baseStyle)
        lw.installEventFilter(self.rowSelectionFilter)  # Install filter
        self.tableView.setCellWidget(row, 3, lw)

    def getUniqueValuesFromLayer(self):
        """Fetch unique values for categorical field."""
        if not self.currentLayer or not self.currentFieldName: return []
        idx = self.currentLayer.fields().indexOf(self.currentFieldName)
        if idx < 0: return []
        
        vals = set()
        for f in self.currentLayer.getFeatures():
            v = f[self.currentFieldName]
            vals.add(str(v) if v is not None else "NULL")
        
        lst = sorted(list(vals))
        if "NULL" in lst: # Move NULL to front
            lst.remove("NULL")
            lst.insert(0, "NULL")
        return lst

    # --- Table Manipulation ---

    def addClass(self):
        """Handle add class button click with double-click detection."""
        if not self.currentLayer: return
        
        if self.btClassPlusClickTimer and self.btClassPlusClickTimer.isActive():
            self.btClassPlusClickTimer.stop()
            self.btClassPlusClickTimer = None
            self.btClassPlusAddBefore = True
            self.executeAddClass()
            self.btClassPlusAddBefore = False
        else:
            self.btClassPlusClickTimer = QTimer()
            self.btClassPlusClickTimer.setSingleShot(True)
            self.btClassPlusClickTimer.timeout.connect(self._onSingleClickAdd)
            self.btClassPlusClickTimer.start(400)

    def _onSingleClickAdd(self):
        self.btClassPlusClickTimer = None
        self.btClassPlusAddBefore = False
        self.executeAddClass()

    def executeAddClass(self):
        """Route add logic."""
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.addCategoricalClass()
        else:
            self.addNumericClass()
            # Don't re-apply classification method - let manual changes stand
            # Classification is only applied when user changes the mode dropdown
        self.updateButtonStates()

        # NEW: Re-apply generic logic
        self.applyColorLogic()
        self.applySizeLogic()

    def addNumericClass(self):
        """Add numeric range."""
        sel = self.getSelectedRows()
        row = sel[0] if sel and len(sel) == 1 else self.tableView.rowCount()
        if sel and not self.btClassPlusAddBefore: row += 1 # After selection
        
        lower, upper = self.calculateInitialRangeForNewRow(row)
        self.tableView.insertRow(row)
        
        sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        sym.setColor(self.generateRandomColor())
        
        self.setRowWidgets(row, sym, True, f"{lower:.2f} - {upper:.2f}", f"{lower:.2f} - {upper:.2f}", self.getGeometryHint())
        self.updateAdjacentRowsAfterInsertion(row, lower, upper)
        
        self.tableView.clearSelection()
        self.tableView.selectRow(row)
        self.updateClassCount()

    def addCategoricalClass(self):
        """Add categorical value."""
        if not self.availableUniqueValues:
            if not self.hasOtherValuesCategory():
                self.ensureOtherValuesCategory()
            else:
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
        
        disp = str(val)
        self.setRowWidgets(row, sym, True, disp, disp, self.getGeometryHint(), isReadOnlyVal=True)
        
        self.tableView.clearSelection()
        self.tableView.selectRow(row)
        self.updateClassCount()

    def removeClass(self):
        """Remove selected classes."""
        rows = sorted(self.getSelectedRows(), reverse=True)
        if not rows: return

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            for r in rows:
                w = self.tableView.cellWidget(r, 2)
                if isinstance(w, QLineEdit):
                    val = w.text()
                    if val != self.tr("Other Values") and val in self.usedUniqueValues:
                        self.usedUniqueValues.remove(val)
                        self.availableUniqueValues.append(val)
                self.tableView.removeRow(r)
            self.availableUniqueValues.sort()
        else:
            lowest = rows[-1]
            for r in rows: self.tableView.removeRow(r)
            self.mergeAdjacentRowsAfterDeletion(lowest)
            # Don't re-apply classification method - let manual changes stand

        self.updateClassCount()
        self.updateButtonStates()

        # NEW: Re-apply generic logic
        self.applyColorLogic()
        self.applySizeLogic()

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
        for c in range(4):
            w = self.tableView.cellWidget(row, c)
            if isinstance(w, SymbolColorSelectorWithCheckbox):
                data.append(('cw', w.color(), w.isChecked(), w.colorSelector.symbolSize))
            elif isinstance(w, QLineEdit):
                # For column 2 (Value), check if it has double-click handler (numeric) or not (categorical)
                hasDoubleClick = c == 2 and hasattr(w, 'mouseDoubleClickEvent') and w.mouseDoubleClickEvent.__name__ == '<lambda>'
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
            if dtype == 'cw':
                cw = SymbolColorSelectorWithCheckbox(self.tableView, geom, d[1], d[2], "")
                cw.colorSelector.setEnabled(self.isEditing)
                cw.updateSymbolSize(d[3], geom=="line")
                cw.setAutoFillBackground(False)  # Ensure custom widget background doesn't block selection
                self.tableView.setCellWidget(row, c, cw)
            elif dtype == 'le':
                le = QLineEdit(d[1])
                le.setEnabled(self.isEditing)
                hasDoubleClick = d[3] if len(d) > 3 else False
                if d[2]:
                    le.setReadOnly(True)
                    if c == 2:  # Value column
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
                if c == 1:
                    le.setAlignment(Qt.AlignCenter)
                    le.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))

                # Install event filter for row selection
                le.installEventFilter(self.rowSelectionFilter)
                self.tableView.setCellWidget(row, c, le)

    # --- Numeric Logic & Classification ---

    def calculateInitialRangeForNewRow(self, row):
        """Determine smart default range for new row."""
        total = self.tableView.rowCount()
        if row == 0:
            if total > 0:
                first = self.getRangeValues(0)
                return (first[0] - 1.0, first[0]) if first else (0.0, 1.0)
            return 0.0, 1.0
        elif row >= total:
            last = self.getRangeValues(total - 1)
            return (last[1], last[1] + 1.0) if last else (0.0, 1.0)
        else:
            prev = self.getRangeValues(row - 1)
            nxt = self.getRangeValues(row) # Technically row before insertion becomes next
            if prev and nxt:
                mid = (prev[1] + nxt[0]) / 2.0
                return prev[1], mid
        return 0.0, 1.0

    def getRangeValues(self, row):
        """Parse range string from table."""
        widget = self.tableView.cellWidget(row, 2)
        if not isinstance(widget, QLineEdit): return None
        try:
            parts = widget.text().split(' - ')
            return float(parts[0]), float(parts[1])
        except: return None

    def updateAdjacentRowsAfterInsertion(self, row, newLower, newUpper):
        """Maintain contiguity after insert."""
        if row > 0: self.updateRangeValue(row - 1, None, newLower)
        if row < self.tableView.rowCount() - 1: self.updateRangeValue(row + 1, newUpper, None)

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
        vw = self.tableView.cellWidget(row, 2)
        if isinstance(vw, QLineEdit):
            vw.setText(txt)
        # Update legend if it matched old range
        lw = self.tableView.cellWidget(row, 3)
        if isinstance(lw, QLineEdit) and lw.text().replace(" ","") == f"{curr[0]:.2f}-{curr[1]:.2f}".replace(" ",""):
            lw.setText(txt)

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

        # Apply
        for i in range(num):
            l, u = breaks[i], breaks[i+1]
            txt = f"{l:.2f} - {u:.2f}"
            vw = self.tableView.cellWidget(i, 2)
            if isinstance(vw, QLineEdit):
                vw.setText(txt)

            lw = self.tableView.cellWidget(i, 3)
            if isinstance(lw, QLineEdit): lw.setText(txt)

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
        curr = self.getRangeValues(row)
        if not curr: return
        
        dlg = RangeEditDialog(curr[0], curr[1], self)
        if dlg.exec_():
            nl, nu = dlg.getValues()
            nl, nu, clamped = self.validateAndClampRange(row, nl, nu)
            if clamped:
                QMessageBox.warning(self, "Adjusted", "Range adjusted for contiguity.")
            self.updateRangeValue(row, nl, nu)
            
            # Update neighbors
            if row > 0: self.updateRangeValue(row - 1, None, nl)
            if row < self.tableView.rowCount() - 1: self.updateRangeValue(row + 1, nu, None)

    def validateAndClampRange(self, row, nl, nu):
        """Ensure ranges stay ordered and contiguous."""
        clamped = False
        if nl >= nu:
            nu = nl + 0.01
            clamped = True
        
        if row > 0:
            prev = self.getRangeValues(row - 1)
            if prev and nl < prev[0]:
                nl = prev[0]
                clamped = True
        
        if row < self.tableView.rowCount() - 1:
            nxt = self.getRangeValues(row + 1)
            if nxt and nu > nxt[1]:
                nu = nxt[1]
                clamped = True
                
        return nl, nu, clamped

    def onSizeChanged(self, row, text):
        """Live update of preview size."""
        try:
            s = float(text)
            cw = self.tableView.cellWidget(row, 0)
            if isinstance(cw, SymbolColorSelectorWithCheckbox):
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
                cw = self.tableView.cellWidget(r, 0)
                lw = self.tableView.cellWidget(r, 3)
                sw = self.tableView.cellWidget(r, 1)
                
                sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
                sym.setColor(cw.color())
                try:
                    s = float(sw.text())
                    if self.currentLayer.geometryType() == 1: sym.setWidth(s)
                    else: sym.setSize(s)
                except: pass
                
                rng = QgsRendererRange(vals[0], vals[1], sym, lw.text())
                rng.setRenderState(cw.isChecked())
                ranges.append(rng)
            
            if ranges: self.currentLayer.setRenderer(QgsGraduatedSymbolRenderer(self.currentFieldName, ranges))

        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            cats = []
            for r in range(self.tableView.rowCount()):
                cw = self.tableView.cellWidget(r, 0)
                lw = self.tableView.cellWidget(r, 3)
                vw = self.tableView.cellWidget(r, 2)
                sw = self.tableView.cellWidget(r, 1)
                
                val = vw.text() if isinstance(vw, QLineEdit) else ""
                label = lw.text()
                
                realVal = val
                if val == "NULL": realVal = None
                elif val == "" and label in [self.tr("Other Values"), "Other Values"]: realVal = ""
                
                sym = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
                sym.setColor(cw.color())
                try:
                    s = float(sw.text())
                    if self.currentLayer.geometryType() == 1: sym.setWidth(s)
                    else: sym.setSize(s)
                except: pass
                
                cat = QgsRendererCategory(realVal, sym, label)
                cat.setRenderState(cw.isChecked())
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
        
        if not os.path.exists(path): return
        self.currentLayer.loadNamedStyle(path)
        self.currentLayer.triggerRepaint()
        self.onLayerChanged(self.currentLayer)

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

    def getSelectedRows(self):
        return [i.row() for i in self.tableView.selectionModel().selectedRows()]

    def updateClassCount(self):
        self.leClassCount.setValue(self.tableView.rowCount())

    def updateButtonStates(self):
        if not self.currentLayer: return
        sel = len(self.getSelectedRows())
        isCat = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
        isFixed = self.currentFieldType == self.FIELD_TYPE_NUMERIC and self.cbMode.currentData() == "FixedInterval"

        # Respect FixedInterval mode - buttons should stay disabled
        if isFixed:
            self.btClassPlus.setEnabled(False)
            self.btClassMinus.setEnabled(False)
        elif isCat:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())
            self.btClassMinus.setEnabled(sel >= 1)
            self.btUp.setEnabled(sel == 1 and self.getSelectedRows()[0] > 0)
            self.btDown.setEnabled(sel == 1 and self.getSelectedRows()[0] < self.tableView.rowCount() - 1)
        else:
            # Numeric mode (not FixedInterval)
            self.btClassPlus.setEnabled(True)
            self.btClassMinus.setEnabled(sel >= 1)
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)

    def updateAddClassButtonState(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())

    def hasOtherValuesCategory(self):
        for r in range(self.tableView.rowCount()):
            w = self.tableView.cellWidget(r, 3)
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
        """Handle clicks outside the table to clear selection."""
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

        # Clean up parent reference to allow garbage collection
        if self.parent and hasattr(self.parent, 'legendsDialog'):
            self.parent.legendsDialog = None

        super().closeEvent(event)