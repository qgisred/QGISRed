# -*- coding: utf-8 -*-

# Standard library imports
import os
import random

# Third-party imports
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QAbstractItemView

from PyQt5 import sip
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant, Qt, QTimer

# QGIS imports
from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, QgsGraduatedSymbolRenderer
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererRange, QgsRendererCategory, QgsSymbol
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer
from qgis.core import QgsGradientColorRamp, QgsClassificationJenks, QgsClassificationPrettyBreaks

# Local imports
from ..tools.qgisred_utils import QGISRedUtils
from .qgisred_custom_dialogs import RangeEditDialog, SymbolColorSelectorWithCheckbox, SymbolEditDialog

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

class QGISRedLegendsDialog(QDialog, formClass):
    # Class constants for field types
    FIELD_TYPE_NUMERIC = 'numeric'
    FIELD_TYPE_CATEGORICAL = 'categorical'
    FIELD_TYPE_UNKNOWN = 'unknown'
    
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLegendsDialog, self).__init__(parent)
        self.setupUi(self)
        
        # Initialize class variables
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.currentFieldName = None
        self.currentLayer = None
        self.pluginFolder = os.path.dirname(os.path.dirname(__file__))
        self.isEditing = True #False  # For future implementation

        # Store original renderer for cancel operations
        self.originalRenderer = None

        # Track available unique values for categorical legends
        self.availableUniqueValues = []
        self.usedUniqueValues = []

        # Track double-click state for btClassPlus
        self.btClassPlusClickTimer = None
        self.btClassPlusAddBefore = False
        
        self.config()
        self.setupTableView()
        self.populateClassificationModes()

        self.populateGroups()
        self.onGroupChanged()

        # Set initial UI state
        self.frameLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.labelFrameLegends.setText(self.tr("Legend"))
        self.initializeUiVisibility()

        # Connect signals
        self.connectSignals()

        # Initialize with current layer if any
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())

        # Initialize class count and make it read-only
        self.setupClassCountField()
        self.updateClassCount()

        # Connect table selection changed signal
        self.tableView.itemSelectionChanged.connect(self.updateButtonStates)

        # Connect item clicked to ensure full row selection
        self.tableView.itemClicked.connect(self.onTableItemClicked)

    def setupClassCountField(self):
        """Configure the class count field to be read-only and greyed out."""
        self.leClassCount.setReadOnly(True)
        self.leClassCount.setStyleSheet("QLineEdit { background-color: #F0F0F0; color: #808080; }")

    def config(self):
        """Configure dialog window."""
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))

        # Set QGIS-style icons for plus/minus buttons
        self.btClassPlus.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))
        self.btClassPlus.setText("")
        self.btClassMinus.setText("")
    
    def setupTableView(self):
        self.tableView.setColumnCount(4)  # Symbol (with checkbox), Size, Value, Legend
        self.tableView.setHorizontalHeaderLabels(["Symbol", "Size", "Value", "Legend"])

        # Get the horizontal header
        header = self.tableView.horizontalHeader()

        # Set column 0 (Symbol with checkbox) to Fixed
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.tableView.setColumnWidth(0, 50)

        # Set column 1 (Size) to Fixed size
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.tableView.setColumnWidth(1, 60)

        # Set column 2 (Value) to Fixed size
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.tableView.setColumnWidth(2, 100)

        # Set column 3 (Legend) to Stretch
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        # Set selection behavior - Enable multi-row selection
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Remove alternating row colors
        self.tableView.setAlternatingRowColors(False)
        # Set edit trigger to require editing current item (click to select, click again to edit)
        self.tableView.setEditTriggers(QAbstractItemView.EditKeyPressed | QAbstractItemView.SelectedClicked)

        # Hide vertical header (row indexes)
        self.tableView.verticalHeader().setVisible(False)

        # Remove grid lines
        self.tableView.setShowGrid(False)

        # Set white background, remove borders, and style selection
        self.tableView.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: transparent;
                border: none;
                selection-background-color: #3399ff;
                selection-color: white;
            }
            QTableWidget::item {
                border: none;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #3399ff;
                color: white;
            }
        """)

    def populateClassificationModes(self):
        """Populate cbMode with available QGIS classification methods."""
        self.cbMode.blockSignals(True)
        self.cbMode.clear()

        # Add blank option for manual mode (no automatic classification)
        self.cbMode.addItem("", None)

        # Manually add the standard QGIS classification methods
        # These are the most commonly used methods in QGIS
        methods = [
            ("EqualInterval", "Equal Interval"),
            ("Quantile", "Quantile (Equal Count)"),
            ("Jenks", "Natural Breaks (Jenks)"),
            ("StdDev", "Standard Deviation"),
            ("Pretty", "Pretty Breaks")
        ]

        for methodId, displayName in methods:
            self.cbMode.addItem(displayName, methodId)

        self.cbMode.blockSignals(False)

        QgsMessageLog.logMessage(
            f"Populated classification modes with {self.cbMode.count()} options",
            "QGISRed", Qgis.Info
        )
    
    def connectSignals(self):
        """Connect all widget signals."""
        self.cbGroups.currentIndexChanged.connect(self.onGroupChanged)

        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.cancelAndClose)

        # Classification mode selector (numeric only)
        self.cbMode.currentIndexChanged.connect(self.onModeChanged)

        # Class management buttons
        self.btClassPlus.clicked.connect(self.addClass)
        self.btClassMinus.clicked.connect(self.removeClass)

        # Up/Down buttons (categorical only)
        self.btUp.clicked.connect(self.moveClassUp)
        self.btDown.clicked.connect(self.moveClassDown)

        # Save/Load buttons
        self.btSaveProject.clicked.connect(self.saveProjectStyle)
        self.btSaveGlobal.clicked.connect(self.saveGlobalStyle)
        self.btLoadDefault.clicked.connect(self.loadDefaultStyle)
        self.btLoadGlobal.clicked.connect(self.loadGlobalStyle)

        # Connect double-click for editing
        self.tableView.cellDoubleClicked.connect(self.onCellDoubleClicked)
    
    def onTableItemClicked(self, item):
        """Handle item click to ensure entire row is selected."""
        if item:
            row = item.row()
            self.tableView.selectRow(row)

    def connectCheckboxSignal(self, colorWidget):
        """Connect checkbox state change signal for visibility changes.

        Args:
            colorWidget: SymbolColorSelectorWithCheckbox instance
        """
        # Checkbox now only represents visibility, not selection
        # Reserved for future visibility implementation
        pass
    
    def onGroupChanged(self):
        """
        When a group is chosen, filter cbLegendLayer to only show layers in that group
        that have a defined renderer we can edit (Graduated or Categorized).
        """
        # compute allowed layers
        allowedLayers = self.getRenderableLayersInSelectedGroup()

        # whitelist via excepted list (exclude everything NOT allowed)
        allLayers = list(QgsProject.instance().mapLayers().values())
        excepted = [lyr for lyr in allLayers if lyr not in allowedLayers]

        # apply filter to the layer combo
        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(excepted)
        # try to select first valid layer
        if allowedLayers:
            self.cbLegendLayer.setLayer(allowedLayers[0])
        self.cbLegendLayer.blockSignals(False)

        # update legend panel state
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())
        else:
            self.onLayerChanged(None)

    def populateGroups(self):
        """
        Fill cbGroups with only specific groups defined in ALLOWED_GROUP_IDENTIFIERS.
        Shows only the group name (not full path). Stores the group's unique path in itemData.
        Excludes root.
        """
        # Define which groups to include by their qgisred_identifier custom property
        # Easily add or remove identifiers here
        ALLOWED_GROUP_IDENTIFIERS = [
            "qgisred_thematicmaps",
            # "qgisred_results",  # Uncomment to add more groups
            # "qgisred_queries",
        ]

        root = QgsProject.instance().layerTreeRoot()
        self.cbGroups.blockSignals(True)
        self.cbGroups.clear()

        def groupHasLayers(group: QgsLayerTreeGroup) -> bool:
            for child in group.children():
                if isinstance(child, QgsLayerTreeLayer):
                    return True
                if isinstance(child, QgsLayerTreeGroup) and groupHasLayers(child):
                    return True
            return False

        def walk(group: QgsLayerTreeGroup, pathParts):
            # Only add if we have a path (skip root) and group identifier is in allowed list
            if pathParts and groupHasLayers(group):
                # Check if the current group has a matching qgisred_identifier
                groupIdentifier = group.customProperty("qgisred_identifier")
                if groupIdentifier in ALLOWED_GROUP_IDENTIFIERS:
                    pathStr = " / ".join(pathParts)
                    displayName = pathParts[-1]
                    self.cbGroups.addItem(displayName, pathStr)
            for child in group.children():
                if isinstance(child, QgsLayerTreeGroup):
                    walk(child, pathParts + [child.name()])

        # Start walking from root
        walk(root, [])

        # pick first item if available
        if self.cbGroups.count() > 0:
            self.cbGroups.setCurrentIndex(0)

        self.cbGroups.blockSignals(False)
    
    def getRenderableLayersInSelectedGroup(self):
        """
        Return only the layers that are DIRECTLY in the selected group (not in subgroups)
        and have a Graduated or Categorized renderer.
        """
        selectedPath = self.cbGroups.currentData()
        if not selectedPath:
            return []

        # Find the group by its path
        root = QgsProject.instance().layerTreeRoot()
        pathParts = [part.strip() for part in selectedPath.split("/")]
        
        targetGroup = root
        for partName in pathParts:
            found = False
            for child in targetGroup.children():
                if isinstance(child, QgsLayerTreeGroup) and child.name() == partName:
                    targetGroup = child
                    found = True
                    break
            if not found:
                return []

        # Collect only DIRECT layer children (not in subgroups)
        renderableLayers = []
        for child in targetGroup.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer and isinstance(layer, QgsVectorLayer):
                    renderer = layer.renderer()
                    if renderer and renderer.type() in ("graduatedSymbol", "categorizedSymbol"):
                        renderableLayers.append(layer)

        return renderableLayers

    def getLayersInGroup(self, groupPath: str):
        """
        Collect layers that belong to the group identified by its 'Parent / Child' path.
        If groupPath is None or empty, treat it as the root.
        """
        root = QgsProject.instance().layerTreeRoot()
        target = root
        if groupPath:
            # descend by names split by ' / '
            for part in groupPath.split(" / "):
                child = next((c for c in target.children()
                              if isinstance(c, QgsLayerTreeGroup) and c.name() == part), None)
                if child is None:
                    return []
                target = child

        result = []
        def collect(group: QgsLayerTreeGroup):
            for child in group.children():
                if isinstance(child, QgsLayerTreeLayer):
                    result.append(child.layer())
                elif isinstance(child, QgsLayerTreeGroup):
                    collect(child)
        collect(target)
        # Keep only unique, existing layers
        return [lyr for lyr in result if lyr]

    def onCellDoubleClicked(self, row, column):
        """Handle double-click on cells to open appropriate editors."""
        # Column 0: Symbol editor (open symbol dialog with color and size)
        if column == 0:
            self.openSymbolEditor(row)
            return

        # Column 2: Value editor (only for numeric fields with ranges)
        if column == 2 and self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.openRangeEditor(row)
            return

    def openSymbolEditor(self, row):
        """Open the symbol editor dialog to edit color and size."""
        if not self.currentLayer:
            return

        # Get current color
        colorWidget = self.tableView.cellWidget(row, 0)
        if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
            currentColor = colorWidget.colorSelector.color()
        else:
            currentColor = QColor(128, 128, 128)

        # Get current size
        sizeWidget = self.tableView.cellWidget(row, 1)
        if isinstance(sizeWidget, QLineEdit):
            try:
                currentSize = float(sizeWidget.text())
            except ValueError:
                currentSize = 1.0
        else:
            currentSize = 1.0

        # Determine if it's width (for lines) or size (for points/polygons)
        isWidth = (self.currentLayer.geometryType() == 1)

        # Open dialog
        dialog = SymbolEditDialog(currentColor, currentSize, isWidth, self)
        if dialog.exec_():
            newColor, newSize = dialog.getValues()

            # Update color
            if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
                colorWidget.colorSelector.setColor(newColor)
                colorWidget.colorSelector.updateSymbolSize(newSize, isWidth)

            # Update size field
            if isinstance(sizeWidget, QLineEdit):
                sizeWidget.setText(str(newSize))

    def openRangeEditor(self, row):
        """Open the range editor dialog for a numeric row."""
        valueItem = self.tableView.item(row, 2)
        if not valueItem:
            return

        originalValueText = valueItem.text()
        try:
            lowerStr, upperStr = originalValueText.split(' - ')
            lowerVal = float(lowerStr)
            upperVal = float(upperStr)
        except (ValueError, IndexError):
            QgsMessageLog.logMessage(f"Could not parse range value: {originalValueText}", "QGISRed", Qgis.Warning)
            return

        dialog = RangeEditDialog(lowerVal, upperVal, self)
        if dialog.exec_():
            newLower, newUpper = dialog.getValues()

            if newLower >= newUpper:
                QMessageBox.warning(self, self.tr("Invalid Range"), self.tr("Lower value must be less than upper value."))
                return

            # Update the current row's value item
            newValueText = f"{newLower:.2f} - {newUpper:.2f}"
            valueItem.setText(newValueText)
            
            # Update the current row's legend widget if it matches the old value
            legendWidget = self.tableView.cellWidget(row, 3)
            if isinstance(legendWidget, QLineEdit) and legendWidget.text() == originalValueText:
                legendWidget.setText(newValueText)

            # Adjust the PREVIOUS row, if it exists
            if row > 0:
                prevItem = self.tableView.item(row - 1, 2)
                if prevItem:
                    try:
                        prevText = prevItem.text()
                        prevLowerStr, _ = prevText.split(' - ')
                        newPrevText = f"{float(prevLowerStr):.2f} - {newLower:.2f}"
                        prevItem.setText(newPrevText)

                        prevLegendWidget = self.tableView.cellWidget(row - 1, 3)
                        if isinstance(prevLegendWidget, QLineEdit) and prevLegendWidget.text() == prevText:
                            prevLegendWidget.setText(newPrevText)
                    except (ValueError, IndexError):
                        QgsMessageLog.logMessage(f"Could not parse and adjust previous range: {prevItem.text()}", "QGISRed", Qgis.Warning)

            # Adjust the NEXT row, if it exists
            if row < self.tableView.rowCount() - 1:
                nextItem = self.tableView.item(row + 1, 2)
                if nextItem:
                    try:
                        nextText = nextItem.text()
                        _, nextUpperStr = nextText.split(' - ')
                        newNextText = f"{newUpper:.2f} - {float(nextUpperStr):.2f}"
                        nextItem.setText(newNextText)

                        nextLegendWidget = self.tableView.cellWidget(row + 1, 3)
                        if isinstance(nextLegendWidget, QLineEdit) and nextLegendWidget.text() == nextText:
                            nextLegendWidget.setText(newNextText)
                    except (ValueError, IndexError):
                        QgsMessageLog.logMessage(f"Could not parse and adjust next range: {nextItem.text()}", "QGISRed", Qgis.Warning)

    def onSizeChanged(self, row, text):
        """Handle size field changes and update symbol preview."""
        if not self.currentLayer or not text:
            return

        try:
            size = float(text)
            if size <= 0:
                return
        except ValueError:
            return

        # Get the color widget in the same row
        colorWidget = self.tableView.cellWidget(row, 0)

        # Extract the actual color selector if it's wrapped
        if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
            actualColorSelector = colorWidget.colorSelector
        else:
            return

        # Update symbol size
        if self.currentLayer.geometryType() == 1:  # Line
            actualColorSelector.updateSymbolSize(size, isWidth=True)
        else:  # Point or Polygon
            actualColorSelector.updateSymbolSize(size, isWidth=False)

    def updateClassCount(self):
        """Update the class count display."""
        count = self.tableView.rowCount()
        self.leClassCount.setText(str(count))

    def initializeUiVisibility(self):
        """Initialize the visibility of UI elements at startup."""
        # Hide all classification-related buttons initially
        self.btClassPlus.setVisible(False)
        self.btClassMinus.setVisible(False)
        self.btUp.setVisible(False)
        self.btDown.setVisible(False)
        self.labelClass.setVisible(False)  # "Classes" label
        self.leClassCount.setVisible(False)  # Class count field

        # Hide mode selector initially (shown only for numeric fields)
        self.cbMode.setVisible(False)
        self.labelMode.setVisible(False)

        # Hide label initially
        self.labelFrameLegends.setVisible(False)

        # Initially hide Apply button (as per document - read-only first implementation)
        self.btApplyLegend.setVisible(self.isEditing)
    
    def detectFieldType(self, layer):
        """
        Detect if the layer's symbology field is numeric or categorical.
        
        Args:
            layer: QgsVectorLayer object
            
        Returns:
            tuple: (field_type, field_name)
        """
        if not layer:
            return self.FIELD_TYPE_UNKNOWN, None
            
        renderer = layer.renderer()
        fieldName = None
        fieldType = self.FIELD_TYPE_UNKNOWN
        
        # Check renderer type
        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            fieldName = renderer.classAttribute()
            fieldType = self.FIELD_TYPE_NUMERIC
            QgsMessageLog.logMessage(
                f"Detected graduated symbology on field '{fieldName}'", 
                "QGISRed", Qgis.Info
            )
            
        elif isinstance(renderer, QgsCategorizedSymbolRenderer):
            fieldName = renderer.classAttribute()
            # Check if the field itself is numeric or not
            if fieldName:
                fields = layer.fields()
                field = fields.field(fieldName)
                if field:
                    fieldTypeVariant = field.type()
                    if fieldTypeVariant in [QVariant.Int, QVariant.Double, QVariant.LongLong]:
                        fieldType = self.FIELD_TYPE_NUMERIC
                    else:
                        fieldType = self.FIELD_TYPE_CATEGORICAL
            else:
                fieldType = self.FIELD_TYPE_CATEGORICAL
                
            QgsMessageLog.logMessage(
                f"Detected categorized symbology on field '{fieldName}' (type: {fieldType})", 
                "QGISRed", Qgis.Info
            )
        else:
            QgsMessageLog.logMessage(
                "No graduated or categorized symbology detected", 
                "QGISRed", Qgis.Info
            )
            
        return fieldType, fieldName
    
    def updateUIBasedOnFieldType(self):
        """Show/hide UI elements based on the current field type."""
        isNumeric = (self.currentFieldType == self.FIELD_TYPE_NUMERIC)
        isCategorical = (self.currentFieldType == self.FIELD_TYPE_CATEGORICAL)
        hasField = isNumeric or isCategorical

        # Classification mode selector - visible only for numeric
        self.cbMode.setVisible(isNumeric)
        self.labelMode.setVisible(isNumeric)

        # Class management buttons - visible for both numeric and categorical
        self.btClassPlus.setVisible(hasField)
        self.btClassMinus.setVisible(hasField)
        self.labelClass.setVisible(hasField)
        self.leClassCount.setVisible(hasField)

        # Up/Down buttons - visible only for categorical
        self.btUp.setVisible(isCategorical)
        self.btDown.setVisible(isCategorical)

        # Label visibility
        self.labelFrameLegends.setVisible(hasField)

        # Note: Checkbox is now integrated into the symbol widget for categorical

        # Update label text
        if isNumeric:
            self.labelClass.setText(self.tr("Classes"))
        elif isCategorical:
            self.labelClass.setText(self.tr("Classes"))

        # Update Plus button state for categorical
        if isCategorical:
            self.updateAddClassButtonState()

        QgsMessageLog.logMessage(
            f"UI updated for field type: {self.currentFieldType}",
            "QGISRed", Qgis.Info
        )
    
    def onLayerChanged(self, layer):
        """Handle layer change event."""
        if layer and isinstance(layer, QgsVectorLayer):
            # Store current layer and its original renderer
            self.currentLayer = layer
            self.originalRenderer = layer.renderer().clone() if layer.renderer() else None

            # Detect field type from current symbology
            self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)

            # Enable legend frame and update label
            self.frameLegends.setEnabled(True)
            self.labelFrameLegends.setText(self.tr(f"Legend for {layer.name()}"))

            # Update UI based on detected field type
            self.updateUIBasedOnFieldType()

            # Reset mode selector to blank (manual mode) for numeric fields
            if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
                self.cbMode.blockSignals(True)
                self.cbMode.setCurrentIndex(0)  # Select blank option
                self.cbMode.blockSignals(False)

            # Populate the table view
            if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
                self.populateNumericLegend()
            elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
                self.populateCategoricalLegend()
            else:
                self.clearTable()

            QgsMessageLog.logMessage(
                f"Layer '{layer.name()}' selected. Field type: {self.currentFieldType}, Field name: {self.currentFieldName}",
                "QGISRed", Qgis.Info
            )
            self.updateButtonStates()
        else:
            self.frameLegends.setEnabled(False)
            self.labelFrameLegends.setText(self.tr("Legend"))
            self.labelFrameLegends.setVisible(False)
            self.currentLayer = None
            self.currentFieldType = self.FIELD_TYPE_UNKNOWN
            self.currentFieldName = None
            self.availableUniqueValues = []
            self.usedUniqueValues = []
            self.clearTable()
            self.updateUIBasedOnFieldType()
    
    def clearTable(self):
        """Clear the table view."""
        self.tableView.setRowCount(0)
        self.updateClassCount()
    
    def getUniqueValuesFromLayer(self):
        """
        Retrieve all unique values from the symbology field, including NULL.
        Returns a list of unique values.
        """
        if not self.currentLayer or not self.currentFieldName:
            return []
        
        fieldIndex = self.currentLayer.fields().indexOf(self.currentFieldName)
        if fieldIndex < 0:
            return []
        
        uniqueValues = set()
        for feature in self.currentLayer.getFeatures():
            value = feature[self.currentFieldName]
            # Convert NULL to "NULL" string for display
            if value is None or value == QVariant():
                uniqueValues.add(None)
            else:
                uniqueValues.add(str(value))
        
        # Convert to sorted list (None first if present)
        valuesList = list(uniqueValues)
        if None in valuesList:
            valuesList.remove(None)
            valuesList.sort()
            valuesList.insert(0, None)
        else:
            valuesList.sort()
        
        return valuesList
    
    def initializeCategoricalLegend(self):
        """Initialize an empty categorical legend with "Other Values" as default."""
        self.clearTable()

        # Add "Other Values" as the default category
        self.ensureOtherValuesCategory()

        # Get all unique values
        allUniqueValues = self.getUniqueValuesFromLayer()
        self.availableUniqueValues = allUniqueValues
        self.usedUniqueValues = []

        QgsMessageLog.logMessage(
            "Initialized categorical legend with 'Other Values' category",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()
        self.updateButtonStates()
    
    def updateAddClassButtonState(self):
        """Enable or disable the Add Class button based on available values."""
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            hasAvailableValues = len(self.availableUniqueValues) > 0
            self.btClassPlus.setEnabled(hasAvailableValues)
            
            if not hasAvailableValues:
                QgsMessageLog.logMessage(
                    "All unique values have been used - Add Class button disabled",
                    "QGISRed", Qgis.Info
                )
    
    def populateNumericLegend(self):
        """Populate the legend table for numeric fields."""
        if not self.currentLayer:
            return

        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return

        self.clearTable()

        ranges = renderer.ranges()
        geomHint = self.getGeometryHint()

        for i, rangeItem in enumerate(ranges):
            self.tableView.insertRow(i)

            # Get visibility state from range's render state
            isVisible = rangeItem.renderState()

            # Color (SymbolColorSelectorWithCheckbox for numeric)
            colorWidget = SymbolColorSelectorWithCheckbox(
                parent=self.tableView,
                geometryHint=geomHint,
                initialColor=rangeItem.symbol().color(),
                checked=isVisible,
                checkboxLabel=""
            )
            colorWidget.colorSelector.setEnabled(self.isEditing)

            # Set initial symbol size from renderer
            if self.currentLayer.geometryType() == 1:  # Line
                colorWidget.updateSymbolSize(rangeItem.symbol().width(), isWidth=True)
            else:  # Point or Polygon
                colorWidget.updateSymbolSize(rangeItem.symbol().size(), isWidth=False)

            self.connectCheckboxSignal(colorWidget)
            self.tableView.setCellWidget(i, 0, colorWidget)

            # Size (line width or point size; polygons treated like point size as per legacy behavior)
            sizeEdit = QLineEdit()
            if self.currentLayer.geometryType() == 1:
                sizeEdit.setText(str(rangeItem.symbol().width()))
            else:
                sizeEdit.setText(str(rangeItem.symbol().size()))
            sizeEdit.setEnabled(self.isEditing)
            sizeEdit.setAlignment(Qt.AlignCenter)
            sizeEdit.textChanged.connect(lambda text, row=i: self.onSizeChanged(row, text))
            self.tableView.setCellWidget(i, 1, sizeEdit)

            # Value (range)
            valueText = f"{rangeItem.lowerValue():.2f} - {rangeItem.upperValue():.2f}"
            valueItem = QTableWidgetItem(valueText)
            valueItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableView.setItem(i, 2, valueItem)

            # Legend
            legendEdit = QLineEdit(rangeItem.label())
            legendEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 3, legendEdit)

        QgsMessageLog.logMessage(
            f"Populated numeric legend with {len(ranges)} classes",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()

    def populateCategoricalLegend(self):
        """Populate the legend table for categorical fields from existing renderer.
        Ensures "Other Values" category is present and at the end."""
        if not self.currentLayer:
            return

        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            self.initializeCategoricalLegend()
            return

        self.clearTable()

        categories = renderer.categories()
        geomHint = self.getGeometryHint()

        allUniqueValues = self.getUniqueValuesFromLayer()
        self.usedUniqueValues = []

        hasOtherValues = False
        otherValuesCategory = None
        otherValuesIndex = -1

        for i, category in enumerate(categories):
            if category.label() in [self.tr("Other Values"), "Other Values"] or category.value() == "":
                hasOtherValues = True
                otherValuesCategory = category
                otherValuesIndex = i
                continue

            rowIndex = self.tableView.rowCount()
            self.tableView.insertRow(rowIndex)

            catValue = category.value()
            if catValue is None or catValue == QVariant():
                displayValue = "NULL"
                actualValue = None
            else:
                displayValue = str(catValue)
                actualValue = displayValue

            if actualValue in allUniqueValues:
                self.usedUniqueValues.append(actualValue)

            # Get visibility state from category's render state
            isVisible = category.renderState()

            colorWidget = SymbolColorSelectorWithCheckbox(
                parent=self.tableView,
                geometryHint=geomHint,
                initialColor=category.symbol().color(),
                checked=isVisible,
                checkboxLabel=""
            )
            colorWidget.colorSelector.setEnabled(self.isEditing)

            if self.currentLayer.geometryType() == 1:
                colorWidget.updateSymbolSize(category.symbol().width(), isWidth=True)
            else:
                colorWidget.updateSymbolSize(category.symbol().size(), isWidth=False)

            self.connectCheckboxSignal(colorWidget)
            self.tableView.setCellWidget(rowIndex, 0, colorWidget)

            sizeEdit = QLineEdit()
            if self.currentLayer.geometryType() == 1:
                sizeEdit.setText(str(category.symbol().width()))
            else:
                sizeEdit.setText(str(category.symbol().size()))
            sizeEdit.setEnabled(self.isEditing)
            sizeEdit.setAlignment(Qt.AlignCenter)
            sizeEdit.textChanged.connect(lambda text, row=rowIndex: self.onSizeChanged(row, text))
            self.tableView.setCellWidget(rowIndex, 1, sizeEdit)

            valueEdit = QLineEdit(displayValue)
            valueEdit.setReadOnly(True)
            valueEdit.setStyleSheet("QLineEdit { background-color: #F8F8F8; color: #808080; }")
            self.tableView.setCellWidget(rowIndex, 2, valueEdit)

            legendEdit = QLineEdit(category.label())
            legendEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(rowIndex, 3, legendEdit)

        if hasOtherValues and otherValuesCategory:
            rowIndex = self.tableView.rowCount()
            self.tableView.insertRow(rowIndex)

            # Get visibility state from category's render state
            isVisible = otherValuesCategory.renderState()

            colorWidget = SymbolColorSelectorWithCheckbox(
                parent=self.tableView,
                geometryHint=geomHint,
                initialColor=otherValuesCategory.symbol().color(),
                checked=isVisible,
                checkboxLabel=""
            )
            colorWidget.colorSelector.setEnabled(self.isEditing)

            if self.currentLayer.geometryType() == 1:
                colorWidget.updateSymbolSize(otherValuesCategory.symbol().width(), isWidth=True)
            else:
                colorWidget.updateSymbolSize(otherValuesCategory.symbol().size(), isWidth=False)

            self.connectCheckboxSignal(colorWidget)
            self.tableView.setCellWidget(rowIndex, 0, colorWidget)

            sizeEdit = QLineEdit()
            if self.currentLayer.geometryType() == 1:
                sizeEdit.setText(str(otherValuesCategory.symbol().width()))
            else:
                sizeEdit.setText(str(otherValuesCategory.symbol().size()))
            sizeEdit.setEnabled(self.isEditing)
            sizeEdit.setAlignment(Qt.AlignCenter)
            sizeEdit.textChanged.connect(lambda text, row=rowIndex: self.onSizeChanged(row, text))
            self.tableView.setCellWidget(rowIndex, 1, sizeEdit)

            valueEdit = QLineEdit(self.tr("Other Values"))
            valueEdit.setReadOnly(True)
            valueEdit.setStyleSheet("QLineEdit { background-color: #F8F8F8; color: #808080; }")
            self.tableView.setCellWidget(rowIndex, 2, valueEdit)

            legendEdit = QLineEdit(otherValuesCategory.label())
            legendEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(rowIndex, 3, legendEdit)
        else:
            self.ensureOtherValuesCategory()

        self.availableUniqueValues = [v for v in allUniqueValues if v not in self.usedUniqueValues]

        QgsMessageLog.logMessage(
            f"Populated categorical legend with {self.tableView.rowCount()} classes (including Other Values)",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()
        self.updateButtonStates()
    
    def getSelectedRows(self):
        """Get the list of currently selected row indices."""
        selectedRows = []
        for index in self.tableView.selectionModel().selectedRows():
            selectedRows.append(index.row())
        return selectedRows
    
    def moveClassUp(self):
        """Move selected class up (categorical only, single selection required)."""
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return

        selectedRows = self.getSelectedRows()

        if len(selectedRows) != 1:
            return

        selectedRow = selectedRows[0]
        if selectedRow <= 0:
            return

        self.swapTableRows(selectedRow, selectedRow - 1)

        self.tableView.clearSelection()
        self.tableView.selectRow(selectedRow - 1)

        QgsMessageLog.logMessage("Moved class up", "QGISRed", Qgis.Info)
        self.updateButtonStates()
    
    def moveClassDown(self):
        """Move selected class down (categorical only, single selection required)."""
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return

        selectedRows = self.getSelectedRows()

        if len(selectedRows) != 1:
            return

        selectedRow = selectedRows[0]
        if selectedRow < 0 or selectedRow >= self.tableView.rowCount() - 1:
            return

        self.swapTableRows(selectedRow, selectedRow + 1)

        self.tableView.clearSelection()
        self.tableView.selectRow(selectedRow + 1)

        QgsMessageLog.logMessage("Moved class down", "QGISRed", Qgis.Info)
        self.updateButtonStates()
    
    def swapTableRows(self, row1, row2):
        """Swap two rows in the table."""
        if row1 < 0 or row2 < 0 or row1 >= self.tableView.rowCount() or row2 >= self.tableView.rowCount():
            return

        row1Data = []
        row2Data = []

        for col in range(self.tableView.columnCount()):
            item1 = self.tableView.item(row1, col)
            item2 = self.tableView.item(row2, col)

            widget1 = self.tableView.cellWidget(row1, col)
            widget2 = self.tableView.cellWidget(row2, col)

            # Row 1 snapshot
            if item1:
                row1Data.append(('item', item1.text(), None))
            elif widget1:
                if isinstance(widget1, SymbolColorSelectorWithCheckbox):
                    row1Data.append(('color_with_checkbox', widget1.color(), widget1.isChecked()))
                elif isinstance(widget1, QLineEdit):
                    row1Data.append(('text', widget1.text(), widget1.isReadOnly()))
                elif isinstance(widget1, QComboBox):
                    row1Data.append(('combo', widget1.currentText()))
                else:
                    row1Data.append(None)
            else:
                row1Data.append(None)

            # Row 2 snapshot
            if item2:
                row2Data.append(('item', item2.text(), None))
            elif widget2:
                if isinstance(widget2, SymbolColorSelectorWithCheckbox):
                    row2Data.append(('color_with_checkbox', widget2.color(), widget2.isChecked()))
                elif isinstance(widget2, QLineEdit):
                    row2Data.append(('text', widget2.text(), widget2.isReadOnly()))
                elif isinstance(widget2, QComboBox):
                    row2Data.append(('combo', widget2.currentText()))
                else:
                    row2Data.append(None)
            else:
                row2Data.append(None)

        # Swap
        for col in range(self.tableView.columnCount()):
            self.tableView.setItem(row1, col, None)
            self.tableView.setItem(row2, col, None)
            self.tableView.removeCellWidget(row1, col)
            self.tableView.removeCellWidget(row2, col)

            # Move row2 -> row1
            if row2Data[col]:
                dataType, *data = row2Data[col]
                if dataType == 'item':
                    item = QTableWidgetItem(data[0])
                    self.tableView.setItem(row1, col, item)
                elif dataType == 'color_with_checkbox':
                    widget = SymbolColorSelectorWithCheckbox(parent=self.tableView, geometryHint=self.getGeometryHint(), initialColor=data[0], checked=data[1])
                    widget.colorSelector.setEnabled(self.isEditing)
                    self.connectCheckboxSignal(widget)
                    self.tableView.setCellWidget(row1, col, widget)
                elif dataType == 'text':
                    widget = QLineEdit(data[0])
                    widget.setEnabled(self.isEditing)
                    if col == 1:  # Size column (now column 1)
                        widget.setAlignment(Qt.AlignCenter)
                    elif col == 2:  # Value column (now column 2) - check if should be read-only
                        if len(data) > 1 and data[1]:  # data[1] is isReadOnly
                            widget.setReadOnly(True)
                            widget.setStyleSheet("QLineEdit { background-color: white; }")
                    self.tableView.setCellWidget(row1, col, widget)
                elif dataType == 'combo':
                    widget = QComboBox()
                    widget.addItem(data[0])
                    self.tableView.setCellWidget(row1, col, widget)

            # Move row1 -> row2
            if row1Data[col]:
                dataType, *data = row1Data[col]
                if dataType == 'item':
                    item = QTableWidgetItem(data[0])
                    self.tableView.setItem(row2, col, item)
                elif dataType == 'color_with_checkbox':
                    widget = SymbolColorSelectorWithCheckbox(parent=self.tableView, geometryHint=self.getGeometryHint(), initialColor=data[0], checked=data[1])
                    widget.colorSelector.setEnabled(self.isEditing)
                    self.connectCheckboxSignal(widget)
                    self.tableView.setCellWidget(row2, col, widget)
                elif dataType == 'text':
                    widget = QLineEdit(data[0])
                    widget.setEnabled(self.isEditing)
                    if col == 1:  # Size column (now column 1)
                        widget.setAlignment(Qt.AlignCenter)
                    elif col == 2:  # Value column (now column 2) - check if should be read-only
                        if len(data) > 1 and data[1]:  # data[1] is isReadOnly
                            widget.setReadOnly(True)
                            widget.setStyleSheet("QLineEdit { background-color: white; }")
                    self.tableView.setCellWidget(row2, col, widget)
                elif dataType == 'combo':
                    widget = QComboBox()
                    widget.addItem(data[0])
                    self.tableView.setCellWidget(row2, col, widget)

    def addClass(self):
        """Add a new class to the legend with random colors.
        For numeric classes: single-click adds after selected row, double-click adds before.
        """
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.addCategoricalClass()
            self.updateButtonStates()
        else:
            # Handle double-click detection for numeric classes
            if self.btClassPlusClickTimer is not None and self.btClassPlusClickTimer.isActive():
                # This is a double-click - add before
                self.btClassPlusClickTimer.stop()
                self.btClassPlusClickTimer = None
                self.btClassPlusAddBefore = True
                self.addNumericClass()
                self.btClassPlusAddBefore = False
                # If a classification mode is selected, reapply it with the new class count
                methodId = self.cbMode.currentData()
                if methodId is not None:
                    self.applyClassificationMethod(methodId)
                self.updateButtonStates()
            else:
                # This is a single-click - wait to see if another click comes
                self.btClassPlusClickTimer = QTimer()
                self.btClassPlusClickTimer.setSingleShot(True)
                self.btClassPlusClickTimer.timeout.connect(self.onClassPlusSingleClick)
                self.btClassPlusClickTimer.start(400)  # 250ms double-click interval
                return  # Don't add yet, wait for timer

    def onClassPlusSingleClick(self):
        """Handle single-click on btClassPlus (add after selected row)."""
        self.btClassPlusClickTimer = None
        self.btClassPlusAddBefore = False
        self.addNumericClass()
        # If a classification mode is selected, reapply it with the new class count
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            methodId = self.cbMode.currentData()
            if methodId is not None:
                self.applyClassificationMethod(methodId)
        self.updateButtonStates()

    def addNumericClass(self):
        """Add a new numeric class with random color.
        Position depends on selection and btClassPlusAddBefore flag:
        - If btClassPlusAddBefore is True (double-click): insert before selected row
        - If btClassPlusAddBefore is False (single-click): insert after selected row
        - If no selection: add at end
        """
        geomHint = self.getGeometryHint()

        # Determine insertion position based on selection
        selectedRows = self.getSelectedRows()
        if selectedRows and len(selectedRows) == 1:
            selectedRow = selectedRows[0]
            if self.btClassPlusAddBefore:
                # Double-click: insert before selected row
                insertRow = selectedRow
            else:
                # Single-click: insert after selected row
                insertRow = selectedRow + 1
        else:
            # No selection or multiple selections: add at end
            insertRow = self.tableView.rowCount()

        self.tableView.insertRow(insertRow)

        randomColor = self.generateRandomColor()

        colorWidget = SymbolColorSelectorWithCheckbox(
            parent=self.tableView,
            geometryHint=geomHint,
            initialColor=randomColor,
            checked=True,  # New classes default to visible
            checkboxLabel=""
        )
        colorWidget.colorSelector.setEnabled(self.isEditing)
        self.connectCheckboxSignal(colorWidget)
        self.tableView.setCellWidget(insertRow, 0, colorWidget)

        sizeEdit = QLineEdit("1.0")
        sizeEdit.setAlignment(Qt.AlignCenter)
        sizeEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(insertRow, 1, sizeEdit)

        valueItem = QTableWidgetItem("0.0 - 0.0")
        self.tableView.setItem(insertRow, 2, valueItem)

        legendEdit = QLineEdit("New Class")
        legendEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(insertRow, 3, legendEdit)

        # Clear selection and select the newly added row
        self.tableView.clearSelection()
        self.tableView.selectRow(insertRow)

        positionMsg = "at end"
        if selectedRows and len(selectedRows) == 1:
            if self.btClassPlusAddBefore:
                positionMsg = f"before row {selectedRows[0]}"
            else:
                positionMsg = f"after row {selectedRows[0]}"

        QgsMessageLog.logMessage(f"Added new numeric class {positionMsg} with random color", "QGISRed", Qgis.Info)
        self.updateClassCount()
    
    def addCategoricalClass(self):
        """Add a new categorical class from available unique values.
        Order: First add all unique values (NULL first if present), then Other Values."""
        # Check if there are available unique values to add
        if not self.availableUniqueValues:
            # No more unique values, only add "Other Values" if it doesn't exist
            if not self.hasOtherValuesCategory():
                self.ensureOtherValuesCategory()
                self.updateClassCount()
                self.updateButtonStates()
            else:
                QMessageBox.information(
                    self,
                    "No Available Values",
                    "All unique values from the layer have been used."
                )
            return

        # Add the next unique value (NULL first if present, since getUniqueValuesFromLayer sorts it that way)
        nextValue = self.availableUniqueValues.pop(0)
        self.usedUniqueValues.append(nextValue)

        if nextValue is None:
            displayValue = "NULL"
            legendText = self.tr("(null)")
        else:
            displayValue = str(nextValue)
            legendText = str(nextValue)

        # Insert before "Other Values" if it exists, otherwise at the end
        if self.hasOtherValuesCategory():
            rowCount = self.tableView.rowCount() - 1
        else:
            rowCount = self.tableView.rowCount()

        geomHint = self.getGeometryHint()
        self.tableView.insertRow(rowCount)

        randomColor = self.generateRandomColor()

        colorWidget = SymbolColorSelectorWithCheckbox(
            parent=self.tableView,
            geometryHint=geomHint,
            initialColor=randomColor,
            checked=True,  # New categories default to visible
            checkboxLabel=""
        )
        colorWidget.colorSelector.setEnabled(self.isEditing)
        self.connectCheckboxSignal(colorWidget)
        self.tableView.setCellWidget(rowCount, 0, colorWidget)

        sizeEdit = QLineEdit("1.0")
        sizeEdit.setAlignment(Qt.AlignCenter)
        sizeEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(rowCount, 1, sizeEdit)

        valueEdit = QLineEdit(displayValue)
        valueEdit.setReadOnly(True)
        valueEdit.setStyleSheet("QLineEdit { background-color: #F8F8F8; color: #808080; }")
        self.tableView.setCellWidget(rowCount, 2, valueEdit)

        legendEdit = QLineEdit(legendText)
        legendEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(rowCount, 3, legendEdit)

        QgsMessageLog.logMessage(
            f"Added categorical class with value '{displayValue}' and random color",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()
        self.updateButtonStates()

    def removeClass(self):
        """Remove selected class(es) from the legend.
        Supports multi-row deletion."""
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.removeCategoricalClasses()
        else:
            self.removeNumericClasses()
            # If a classification mode is selected, reapply it with the new class count
            if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
                methodId = self.cbMode.currentData()
                if methodId is not None:
                    self.applyClassificationMethod(methodId)

        self.updateButtonStates()
    
    def removeNumericClasses(self):
        """Remove selected numeric classes (supports multi-selection)."""
        selectedRows = []
        for index in self.tableView.selectionModel().selectedRows():
            selectedRows.append(index.row())

        if not selectedRows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more classes to remove."
            )
            return

        selectedRows.sort(reverse=True)

        for row in selectedRows:
            self.tableView.removeRow(row)

        QgsMessageLog.logMessage(
            f"Removed {len(selectedRows)} numeric class(es)",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()
    
    def removeCategoricalClasses(self):
        """Remove selected categorical classes (supports multi-selection).
        Returns removed values to the available pool."""
        selectedRows = self.getSelectedRows()

        if not selectedRows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more classes to remove."
            )
            return

        rowsToRemove = selectedRows

        if not rowsToRemove:
            return

        rowsToRemove.sort(reverse=True)

        for row in rowsToRemove:
            valueWidget = self.tableView.cellWidget(row, 2)
            if isinstance(valueWidget, QLineEdit):
                displayValue = valueWidget.text()

                if displayValue == "NULL":
                    actualValue = None
                elif displayValue != self.tr("Other Values"):
                    actualValue = displayValue
                else:
                    actualValue = None

                if actualValue in self.usedUniqueValues:
                    self.usedUniqueValues.remove(actualValue)
                    self.availableUniqueValues.append(actualValue)

            self.tableView.removeRow(row)

        if None in self.availableUniqueValues:
            self.availableUniqueValues.remove(None)
            self.availableUniqueValues.sort()
            self.availableUniqueValues.insert(0, None)
        else:
            self.availableUniqueValues.sort()

        QgsMessageLog.logMessage(
            f"Removed {len(rowsToRemove)} categorical class(es)",
            "QGISRed", Qgis.Info
        )

        self.updateClassCount()
    
    def onModeChanged(self):
        """Handle classification mode change."""
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return

        # Get the selected method ID
        methodId = self.cbMode.currentData()

        if methodId is None:
            # Blank option selected - manual mode, no automatic reclassification
            QgsMessageLog.logMessage(
                "Manual mode selected - no automatic classification",
                "QGISRed", Qgis.Info
            )
            return

        # Apply the selected classification method
        self.applyClassificationMethod(methodId)

    def applyClassificationMethod(self, methodId):
        """Apply a classification method to the current numeric layer.

        Args:
            methodId: The QGIS classification method ID (e.g., 'EqualInterval', 'Quantile', 'Jenks')
        """
        if not self.currentLayer or not self.currentFieldName:
            return

        # Get number of classes from current table
        numClasses = self.tableView.rowCount()
        if numClasses < 2:
            numClasses = 5  # Default

        # Get field index
        fieldIdx = self.currentLayer.fields().indexOf(self.currentFieldName)
        if fieldIdx < 0:
            return

        # Get all values from the field
        values = []
        for feature in self.currentLayer.getFeatures():
            val = feature[self.currentFieldName]
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass

        if not values:
            QgsMessageLog.logMessage(
                "No valid numeric values found in field",
                "QGISRed", Qgis.Warning
            )
            return

        values.sort()
        minVal = min(values)
        maxVal = max(values)

        # Calculate class breaks based on the selected method
        breaks = []
        try:
            if methodId == "EqualInterval":
                # Equal Interval
                interval = (maxVal - minVal) / numClasses
                breaks = [minVal + (i * interval) for i in range(numClasses + 1)]

            elif methodId == "Quantile":
                # Quantile (Equal Count)
                breaks = [minVal]
                for i in range(1, numClasses):
                    idx = int((i / numClasses) * len(values))
                    if idx < len(values):
                        breaks.append(values[idx])
                breaks.append(maxVal)

            elif methodId == "Jenks":
                # Natural Breaks - Use QGIS's implementation
                method = QgsClassificationJenks()
                method.setLabelFormat("%1 - %2")
                classes = method.classes(self.currentLayer, self.currentFieldName, numClasses)
                breaks = [minVal] + [cls.upperBound() for cls in classes]

            elif methodId == "StdDev":
                # Standard Deviation
                import statistics
                mean = statistics.mean(values)
                stddev = statistics.stdev(values) if len(values) > 1 else 0

                # Create breaks at mean ± stddev intervals
                breaks = [minVal]
                halfClasses = numClasses // 2
                for i in range(-halfClasses, halfClasses + 1):
                    val = mean + (i * stddev)
                    if minVal < val < maxVal:
                        breaks.append(val)
                breaks.append(maxVal)
                breaks = sorted(set(breaks))[:numClasses + 1]

            elif methodId == "Pretty":
                # Pretty Breaks - Use QGIS's implementation
                method = QgsClassificationPrettyBreaks()
                method.setLabelFormat("%1 - %2")
                classes = method.classes(self.currentLayer, self.currentFieldName, numClasses)
                breaks = [minVal] + [cls.upperBound() for cls in classes]

            else:
                QgsMessageLog.logMessage(
                    f"Unknown classification method: {methodId}",
                    "QGISRed", Qgis.Warning
                )
                return

        except Exception as e:
            QgsMessageLog.logMessage(
                f"Error calculating breaks: {str(e)}",
                "QGISRed", Qgis.Warning
            )
            return

        # Ensure we have the right number of breaks
        if len(breaks) < numClasses + 1:
            QgsMessageLog.logMessage(
                f"Not enough breaks generated: {len(breaks)} < {numClasses + 1}",
                "QGISRed", Qgis.Warning
            )
            return

        # Create Blue to Red gradient color ramp
        blueColor = QColor(0, 0, 255)  # Blue for low values
        redColor = QColor(255, 0, 0)   # Red for high values
        colorRamp = QgsGradientColorRamp(blueColor, redColor)

        # Update table with new ranges and colors
        currentRowCount = self.tableView.rowCount()
        neededRowCount = numClasses

        # Adjust row count if needed
        if neededRowCount > currentRowCount:
            # Add rows
            for i in range(currentRowCount, neededRowCount):
                self.addNumericClass()
        elif neededRowCount < currentRowCount:
            # Remove rows from the end
            for i in range(currentRowCount - 1, neededRowCount - 1, -1):
                self.tableView.removeRow(i)

        # Apply classification to table rows
        for i in range(numClasses):
            lower = breaks[i]
            upper = breaks[i + 1]

            # Update value column
            valueText = f"{lower:.2f} - {upper:.2f}"
            if self.tableView.item(i, 2):
                self.tableView.item(i, 2).setText(valueText)
            else:
                valueItem = QTableWidgetItem(valueText)
                valueItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tableView.setItem(i, 2, valueItem)

            # Calculate color from gradient (0.0 to 1.0 across the range)
            ratio = i / max(1, numClasses - 1)
            color = colorRamp.color(ratio)

            # Update color widget
            colorWidget = self.tableView.cellWidget(i, 0)
            if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
                colorWidget.setColor(color)

            # Update legend text
            legendWidget = self.tableView.cellWidget(i, 3)
            if isinstance(legendWidget, QLineEdit):
                legendWidget.setText(valueText)

        self.updateClassCount()

        # Get method display name
        methodNames = {
            "EqualInterval": "Equal Interval",
            "Quantile": "Quantile",
            "Jenks": "Natural Breaks (Jenks)",
            "StdDev": "Standard Deviation",
            "Pretty": "Pretty Breaks"
        }
        methodName = methodNames.get(methodId, methodId)

        QgsMessageLog.logMessage(
            f"Applied {methodName} classification with {numClasses} classes",
            "QGISRed", Qgis.Info
        )
    
    def applyLegend(self):
        """Apply the legend from the table to the layer."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.applyNumericLegend()
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.applyCategoricalLegend()
        
        # Refresh the map
        self.currentLayer.triggerRepaint()
        
        QgsMessageLog.logMessage(
            f"Applied legend to layer '{self.currentLayer.name()}'", 
            "QGISRed", Qgis.Info
        )
    
    def applyNumericLegend(self):
        """Apply numeric legend from table to layer."""
        if not self.currentLayer or not self.currentFieldName:
            return

        ranges = []
        for row in range(self.tableView.rowCount()):
            # Range values
            valueText = self.tableView.item(row, 2).text()
            if " - " not in valueText:
                continue
            parts = valueText.split(" - ")
            lower = float(parts[0])
            upper = float(parts[1])

            # Color and visibility from checkbox widget
            colorWidget = self.tableView.cellWidget(row, 0)
            isVisible = True  # Default to visible
            if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
                color = colorWidget.color()
                isVisible = colorWidget.isChecked()  # Checkbox controls visibility
            else:
                color = QColor(128, 128, 128)

            # Label
            legendWidget = self.tableView.cellWidget(row, 3)
            label = legendWidget.text() if isinstance(legendWidget, QLineEdit) else valueText

            # Symbol
            symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
            symbol.setColor(color)

            # Size
            sizeWidget = self.tableView.cellWidget(row, 1)
            if isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    if self.currentLayer.geometryType() == 1:
                        symbol.setWidth(size)
                    else:
                        symbol.setSize(size)
                except Exception:
                    pass

            rangeObj = QgsRendererRange(lower, upper, symbol, label)
            rangeObj.setRenderState(isVisible)
            ranges.append(rangeObj)

        if ranges:
            renderer = QgsGraduatedSymbolRenderer(self.currentFieldName, ranges)
            self.currentLayer.setRenderer(renderer)

    def applyCategoricalLegend(self):
        """Apply categorical legend from table to layer.
        Ensures "Other Values" category properly catches all unmatched values."""
        if not self.currentLayer or not self.currentFieldName:
            return

        categories = []
        otherValuesCategory = None

        for row in range(self.tableView.rowCount()):
            legendWidget = self.tableView.cellWidget(row, 3)
            legendText = legendWidget.text() if isinstance(legendWidget, QLineEdit) else ""

            valueWidget = self.tableView.cellWidget(row, 2)
            if isinstance(valueWidget, QLineEdit):
                displayValue = valueWidget.text()

                if displayValue == self.tr("Other Values") or legendText in [self.tr("Other Values"), "Other Values"]:
                    value = ""
                elif displayValue == "NULL":
                    value = None
                else:
                    value = displayValue
            else:
                valueItem = self.tableView.item(row, 2)
                value = valueItem.text() if valueItem else ""

            # Get color and visibility from checkbox widget
            colorWidget = self.tableView.cellWidget(row, 0)
            isVisible = True  # Default to visible
            if isinstance(colorWidget, SymbolColorSelectorWithCheckbox):
                color = colorWidget.color()
                isVisible = colorWidget.isChecked()  # Checkbox controls visibility: checked = visible, unchecked = hidden
            elif isinstance(colorWidget, SymbolColorSelector):
                color = colorWidget.color()
            else:
                color = QColor(128, 128, 128)

            label = legendText

            symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
            symbol.setColor(color)

            sizeWidget = self.tableView.cellWidget(row, 1)
            if isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    if self.currentLayer.geometryType() == 1:
                        symbol.setWidth(size)
                    else:
                        symbol.setSize(size)
                except Exception:
                    pass

            if value == "" and legendText in [self.tr("Other Values"), "Other Values"]:
                otherValuesCategory = QgsRendererCategory(value, symbol, label)
                otherValuesCategory.setRenderState(isVisible)
            else:
                category = QgsRendererCategory(value, symbol, label)
                category.setRenderState(isVisible)
                categories.append(category)

        if otherValuesCategory:
            categories.append(otherValuesCategory)

        if categories:
            renderer = QgsCategorizedSymbolRenderer(self.currentFieldName, categories)
            self.currentLayer.setRenderer(renderer)

            QgsMessageLog.logMessage(
                f"Applied categorical legend with {len(categories)} categories",
                "QGISRed", Qgis.Info
            )


    def saveProjectStyle(self):
        """Save the current style for the project."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
            
        # Get layer identifier
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            QMessageBox.warning(self, "No Identifier", "Layer does not have a QGISRed identifier.")
            return
        
        # Get element name from identifier using utils
        utils = QGISRedUtils()
        elementName = utils.identifierToElementName.get(layerIdentifier)
        if not elementName:
            QMessageBox.warning(self, "Unknown Layer Type", "Unable to determine layer type.")
            return
        
        # Remove spaces from element name: Isolation Valves -> IsolationValves
        fileName = elementName.replace(" ", "")
        
        # Get project directory
        projectDir = utils.ProjectDirectory
        if not projectDir:
            projectPath = QgsProject.instance().fileName()
            if projectPath:
                projectDir = os.path.dirname(projectPath)
            else:
                QMessageBox.warning(self, "No Project", "Please save the project first.")
                return
        
        # Create layerStyles subfolder if it doesn't exist
        stylesDir = os.path.join(projectDir, "layerStyles")  # Note: matches the folder name in utils
        if not os.path.exists(stylesDir):
            os.makedirs(stylesDir)
        
        qmlPath = os.path.join(stylesDir, f"{fileName}.qml")

        # Check if file exists
        if os.path.exists(qmlPath):
            reply = QMessageBox.question(
                self, 
                "Overwrite Style", 
                f"Style file already exists. Overwrite it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Save style
        self.currentLayer.saveNamedStyle(qmlPath)
        
        QMessageBox.information(
            self, 
            "Style Saved", 
            f"Style saved for the current project."
        )
        
        QgsMessageLog.logMessage(
            f"Saved project style to: {qmlPath}", 
            "QGISRed", Qgis.Info
        )

    def saveGlobalStyle(self):
        """Save the current style as global default."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        # Get layer identifier
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            QMessageBox.warning(self, "No Identifier", "Layer does not have a QGISRed identifier.")
            return
        
        # Get element name from identifier using utils
        utils = QGISRedUtils()
        elementName = utils.identifierToElementName.get(layerIdentifier)
        if not elementName:
            QMessageBox.warning(self, "Unknown Layer Type", "Unable to determine layer type.")
            return
        
        fileName = elementName.replace(" ", "")
        
        # Get plugin layerStyles folder
        stylesDir = os.path.join(self.pluginFolder, "layerStyles")
        if not os.path.exists(stylesDir):
            os.makedirs(stylesDir)
        
        qmlPath = os.path.join(stylesDir, f"{fileName}.qml")

        # Check if file exists
        if os.path.exists(qmlPath):
            reply = QMessageBox.question(
                self, 
                "Overwrite Global Style", 
                f"This will overwrite the global style for all future projects. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Save style
        self.currentLayer.saveNamedStyle(qmlPath)
        
        QMessageBox.information(
            self, 
            "Global Style Saved", 
            f"Style saved globally for future projects."
        )
        
        QgsMessageLog.logMessage(
            f"Saved global style to: {qmlPath}", 
            "QGISRed", Qgis.Info
        )

    def loadDefaultStyle(self):
        """Load the default style."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        # Get layer identifier
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            QMessageBox.warning(self, "No Identifier", "Layer does not have a QGISRed identifier.")
            return
        
        # Get element name from identifier using utils
        utils = QGISRedUtils()
        elementName = utils.identifierToElementName.get(layerIdentifier)
        if not elementName:
            QMessageBox.warning(self, "Unknown Layer Type", "Unable to determine layer type.")
            return
        
        fileName = elementName.replace(" ", "")
        
        # Get default styles folder
        defaultsDir = os.path.join(self.pluginFolder, "defaults", "layerStyles")
        
        qmlPath = os.path.join(defaultsDir, f"{fileName}.qml.bak")

        if not os.path.exists(qmlPath):
            QMessageBox.warning(
                self, 
                "Default Style Not Found", 
                f"Default style not found for this layer type."
            )
            return
        
        # Apply style directly to layer
        self.currentLayer.loadNamedStyle(qmlPath)
        self.currentLayer.triggerRepaint()
        
        # Refresh the display
        self.onLayerChanged(self.currentLayer)
        
        QMessageBox.information(
            self, 
            "Default Style Loaded", 
            f"Default style loaded successfully."
        )
        
        QgsMessageLog.logMessage(
            f"Loaded default style from: {qmlPath}", 
            "QGISRed", Qgis.Info
        )

    def loadGlobalStyle(self):
        """Load the global style."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        # Get layer identifier
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            QMessageBox.warning(self, "No Identifier", "Layer does not have a QGISRed identifier.")
            return
        
        # Get element name from identifier using utils
        utils = QGISRedUtils()
        elementName = utils.identifierToElementName.get(layerIdentifier)
        if not elementName:
            QMessageBox.warning(self, "Unknown Layer Type", "Unable to determine layer type.")
            return
        
        fileName = elementName.replace(" ", "")
        
        # Get plugin layerStyles folder
        stylesDir = os.path.join(self.pluginFolder, "layerStyles")
        
        qmlPath = os.path.join(stylesDir, f"{fileName}.qml")

        if not os.path.exists(qmlPath):
            QMessageBox.warning(
                self, 
                "Global Style Not Found", 
                f"Global style not found for this layer type."
            )
            return
        
        # Apply style directly to layer
        self.currentLayer.loadNamedStyle(qmlPath)
        self.currentLayer.triggerRepaint()
        
        # Refresh the display
        self.onLayerChanged(self.currentLayer)
        
        QMessageBox.information(
            self, 
            "Global Style Loaded", 
            f"Global style loaded successfully."
        )
        
        QgsMessageLog.logMessage(
            f"Loaded global style from: {qmlPath}", 
            "QGISRed", Qgis.Info
        )
        
    def cancelAndClose(self):
        """Cancel changes and close dialog."""
        # Restore original renderer if it was changed
        if self.currentLayer and self.originalRenderer and self.isEditing:
            self.currentLayer.setRenderer(self.originalRenderer.clone())
            self.currentLayer.triggerRepaint()
        
        self.reject()

    def getGeometryHint(self) -> str:
        """
        Returns one of: 'marker', 'line', 'fill' according to currentLayer geometry.
        """
        if not self.currentLayer:
            return "fill"
        gt = self.currentLayer.geometryType()
        if gt == 0:
            return "marker"
        if gt == 1:
            return "line"
        return "fill"

    def generateRandomColor(self):
        """
        Generate a random bright color for new symbols.
        Returns a QColor with good visibility.
        """
        hue = random.randint(0, 359)
        saturation = random.randint(70, 100)
        lightness = random.randint(40, 70)

        color = QColor()
        color.setHsl(hue, saturation * 255 // 100, lightness * 255 // 100)
        return color

    def updateButtonStates(self):
        """
        Central method to update all button states based on current selection and context.
        Handles both multi-selection for deletion and single selection for move operations.
        """
        if not self.currentLayer:
            self.btClassPlus.setEnabled(False)
            self.btClassMinus.setEnabled(False)
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)
            return

        # Get selected rows from table selection (works for both numeric and categorical)
        selectedRows = self.getSelectedRows()
        selectedCount = len(selectedRows)

        # Minus button is enabled if any row is selected
        self.btClassMinus.setEnabled(selectedCount >= 1)

        # Plus button logic
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            hasOtherValues = self.hasOtherValuesCategory()
            availableCount = len(self.availableUniqueValues)
            self.btClassPlus.setEnabled(availableCount > 0 or not hasOtherValues)
        else:
            # Always enabled for numeric
            self.btClassPlus.setEnabled(True)

        # Up/Down buttons (categorical only)
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            # Only enable if exactly one row is selected
            if selectedCount == 1:
                selectedRow = selectedRows[0]
                totalRows = self.tableView.rowCount()
                self.btUp.setEnabled(selectedRow > 0)
                self.btDown.setEnabled(selectedRow < totalRows - 1)
            else:
                self.btUp.setEnabled(False)
                self.btDown.setEnabled(False)
        else:
            # Disabled for numeric
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)

        QgsMessageLog.logMessage(
            f"Button states updated - Selected: {selectedCount}, Plus: {self.btClassPlus.isEnabled()}, "
            f"Minus: {self.btClassMinus.isEnabled()}, Up: {self.btUp.isEnabled()}, Down: {self.btDown.isEnabled()}",
            "QGISRed", Qgis.Info
        )

    def hasOtherValuesCategory(self):
        """
        Check if the table already has an "Other Values" category.
        Returns True if found, False otherwise.
        """
        for row in range(self.tableView.rowCount()):
            legendWidget = self.tableView.cellWidget(row, 3)
            if isinstance(legendWidget, QLineEdit):
                legendText = legendWidget.text()
                if legendText in [self.tr("Other Values"), "Other Values", "Other values"]:
                    return True
        return False

    def getOtherValuesRepresentation(self):
        """
        Returns list of values that would be represented by 'Other Values' category.
        This includes all field values not explicitly listed in the legend.
        """
        if not self.currentLayer or not self.currentFieldName:
            return []

        allUniqueValues = self.getUniqueValuesFromLayer()

        explicitlyListed = []
        for row in range(self.tableView.rowCount()):
            legendWidget = self.tableView.cellWidget(row, 3)
            if isinstance(legendWidget, QLineEdit):
                legendText = legendWidget.text()
                if legendText in [self.tr("Other Values"), "Other Values"]:
                    continue

            valueWidget = self.tableView.cellWidget(row, 2)
            if isinstance(valueWidget, QLineEdit):
                displayValue = valueWidget.text()
                if displayValue == "NULL":
                    actualValue = None
                else:
                    actualValue = displayValue
                explicitlyListed.append(actualValue)

        otherValues = [v for v in allUniqueValues if v not in explicitlyListed]
        return otherValues

    def ensureOtherValuesCategory(self):
        """
        Ensure that "Other Values" category exists as the last row.
        Adds it if missing, updates it if needed.
        """
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return

        if self.hasOtherValuesCategory():
            self.moveOtherValuesToEnd()
            return

        geomHint = self.getGeometryHint()
        rowCount = self.tableView.rowCount()
        self.tableView.insertRow(rowCount)

        randomColor = self.generateRandomColor()
        colorWidget = SymbolColorSelectorWithCheckbox(
            parent=self.tableView,
            geometryHint=geomHint,
            initialColor=randomColor,
            checked=True,  # New "Other Values" category defaults to visible
            checkboxLabel=""
        )
        colorWidget.colorSelector.setEnabled(self.isEditing)
        self.connectCheckboxSignal(colorWidget)
        self.tableView.setCellWidget(rowCount, 0, colorWidget)

        sizeEdit = QLineEdit("1.0")
        sizeEdit.setAlignment(Qt.AlignCenter)
        sizeEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(rowCount, 1, sizeEdit)

        valueEdit = QLineEdit(self.tr("Other Values"))
        valueEdit.setReadOnly(True)
        valueEdit.setStyleSheet("QLineEdit { background-color: #F8F8F8; color: #808080; }")
        self.tableView.setCellWidget(rowCount, 2, valueEdit)

        legendEdit = QLineEdit(self.tr("Other Values"))
        legendEdit.setEnabled(self.isEditing)
        self.tableView.setCellWidget(rowCount, 3, legendEdit)

    def moveOtherValuesToEnd(self):
        """
        Find "Other Values" row and move it to the end if it's not already there.
        """
        otherValuesRow = -1
        for row in range(self.tableView.rowCount()):
            legendWidget = self.tableView.cellWidget(row, 3)
            if isinstance(legendWidget, QLineEdit):
                if legendWidget.text() in [self.tr("Other Values"), "Other Values"]:
                    otherValuesRow = row
                    break

        if otherValuesRow >= 0 and otherValuesRow < self.tableView.rowCount() - 1:
            lastRow = self.tableView.rowCount() - 1
            while otherValuesRow < lastRow:
                self.swapTableRows(otherValuesRow, otherValuesRow + 1)
                otherValuesRow += 1