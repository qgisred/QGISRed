# -*- coding: utf-8 -*-

# Standard library imports
import os
import math

# Third-party imports
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtWidgets import (QDialog, QMessageBox, QWidget, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QComboBox, QLineEdit, QPushButton,
                           QCheckBox, QHBoxLayout, QAbstractItemView)
from PyQt5 import sip
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant, Qt

# QGIS imports
from qgis.core import (QgsLayerTreeGroup, QgsLayerTreeLayer, QgsLayerTreeNode, 
                       QgsProject, QgsVectorFileWriter, QgsVectorLayer, 
                       QgsMessageLog, Qgis, QgsPalLayerSettings, 
                       QgsVectorLayerSimpleLabeling, QgsTextFormat,
                       QgsFeatureRenderer, QgsGraduatedSymbolRenderer,
                       QgsCategorizedSymbolRenderer, QgsRendererRange,
                       QgsRendererCategory, QgsSymbol, QgsClassificationQuantile,
                       QgsClassificationEqualInterval, QgsClassificationJenks,
                       QgsFeatureRequest, QgsExpression)
from qgis.utils import iface
from qgis.gui import QgsColorButton

# Local imports
from ..tools.qgisred_utils import QGISRedUtils

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
        self.isEditing = False  # For future implementation
        
        # Store original renderer for cancel operations
        self.originalRenderer = None
        
        self.config()
        self.setupTableView()
        
        # Set initial UI state
        self.gbLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.gbLegends.setTitle(self.tr("Legend"))
        self.initializeUiVisibility()

        # Connect signals
        self.connectSignals()
        
        # Initialize with current layer if any
        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())

    def config(self):
        """Configure dialog window."""
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))
    
    def setupTableView(self):
        """Setup the table widget with appropriate columns."""
        # Import QHeaderView and QAbstractItemView from PyQt5.QtWidgets
        from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

        # Note: tableView is actually a QTableWidget after UI fix
        # Setup columns for QTableWidget
        self.tableView.setColumnCount(5)  # Checkbox, Color, Size, Value, Legend
        self.tableView.setHorizontalHeaderLabels(["", "Color", "Size", "Value", "Legend"])

        # --- DELETED ---
        # self.tableView.setColumnWidth(0, 30)
        # self.tableView.setColumnWidth(1, 80)
        # self.tableView.setColumnWidth(2, 60)
        # self.tableView.setColumnWidth(3, 100)
        # self.tableView.setColumnWidth(4, 150)
        # ---------------

        # --- ADDED ---
        # Get the horizontal header and set the resize mode to stretch
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        # -------------
        
        # Hide checkbox column initially (only for categorical with up/down buttons)
        # Note: When stretched, this column will still take up space unless hidden.
        self.tableView.setColumnHidden(0, True)

        # Set selection behavior
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setAlternatingRowColors(True)
    
    def connectSignals(self):
        """Connect all widget signals."""
        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.cancelAndClose)

        # Classification buttons (numeric only)
        self.btIntervals.clicked.connect(self.classifyEqualInterval)
        self.btQuantiles.clicked.connect(self.classifyQuantiles)
        self.btBreaks.clicked.connect(self.classifyNaturalBreaks)
        
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
        
        # Table item changed for single checkbox selection
        self.tableView.itemChanged.connect(self.onTableItemChanged)
    
    def initializeUiVisibility(self):
        """Initialize the visibility of UI elements at startup."""
        # Hide all classification-related buttons initially
        self.btIntervals.setVisible(False)
        self.btQuantiles.setVisible(False)
        self.btBreaks.setVisible(False)
        self.btClassPlus.setVisible(False)
        self.btClassMinus.setVisible(False)
        self.btUp.setVisible(False)
        self.btDown.setVisible(False)
        self.labelClass.setVisible(False)  # "Classes" label
        
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
        
        # Classification method buttons - visible only for numeric
        self.btIntervals.setVisible(isNumeric)
        self.btQuantiles.setVisible(isNumeric)
        self.btBreaks.setVisible(isNumeric)
        
        # Class management buttons - visible for both
        self.btClassPlus.setVisible(hasField)
        self.btClassMinus.setVisible(hasField)
        self.labelClass.setVisible(hasField)
        
        # Up/Down buttons - visible only for categorical
        self.btUp.setVisible(isCategorical)
        self.btDown.setVisible(isCategorical)
        
        # Show/hide checkbox column for categorical
        self.tableView.setColumnHidden(0, not isCategorical)
        
        # Update label text
        if isNumeric:
            self.labelClass.setText(self.tr("Classes"))
        elif isCategorical:
            self.labelClass.setText(self.tr("Classes"))
        
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
            
            # Enable legend group and update title
            self.gbLegends.setEnabled(True)
            self.gbLegends.setTitle(self.tr(f"Legend for {layer.name()}"))
            
            # Update UI based on detected field type
            self.updateUIBasedOnFieldType()
            
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
        else:
            self.gbLegends.setEnabled(False)
            self.gbLegends.setTitle(self.tr("Legend"))
            self.currentLayer = None
            self.currentFieldType = self.FIELD_TYPE_UNKNOWN
            self.currentFieldName = None
            self.clearTable()
            self.updateUIBasedOnFieldType()
    
    def clearTable(self):
        """Clear the table view."""
        self.tableView.setRowCount(0)
    
    def populateNumericLegend(self):
        """Populate the legend table for numeric fields."""
        if not self.currentLayer:
            return
            
        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return
            
        # Clear existing table
        self.clearTable()
        
        # Get ranges
        ranges = renderer.ranges()
        
        # Add rows for each range
        for i, rangeItem in enumerate(ranges):
            self.tableView.insertRow(i)
            
            # Checkbox (hidden for numeric)
            checkboxItem = QTableWidgetItem()
            checkboxItem.setCheckState(Qt.Unchecked)
            self.tableView.setItem(i, 0, checkboxItem)
            
            # Color
            colorButton = QgsColorButton()
            colorButton.setColor(rangeItem.symbol().color())
            colorButton.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 1, colorButton)
            
            # Size (line width or point size)
            sizeEdit = QLineEdit()
            if self.currentLayer.geometryType() == 1:  # Line
                sizeEdit.setText(str(rangeItem.symbol().width()))
            else:  # Point
                sizeEdit.setText(str(rangeItem.symbol().size()))
            sizeEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 2, sizeEdit)
            
            # Value (range)
            valueText = f"{rangeItem.lowerValue():.2f} - {rangeItem.upperValue():.2f}"
            valueItem = QTableWidgetItem(valueText)
            valueItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.tableView.setItem(i, 3, valueItem)
            
            # Legend
            legendEdit = QLineEdit(rangeItem.label())
            legendEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 4, legendEdit)
        
        QgsMessageLog.logMessage(
            f"Populated numeric legend with {len(ranges)} classes", 
            "QGISRed", Qgis.Info
        )
    
    def populateCategoricalLegend(self):
        """Populate the legend table for categorical fields."""
        if not self.currentLayer:
            return
            
        renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            return
            
        # Clear existing table
        self.clearTable()
        
        # Get categories
        categories = renderer.categories()
        
        # Add rows for each category
        for i, category in enumerate(categories):
            self.tableView.insertRow(i)
            
            # Checkbox (for selection with up/down buttons)
            checkboxItem = QTableWidgetItem()
            checkboxItem.setCheckState(Qt.Unchecked)
            self.tableView.setItem(i, 0, checkboxItem)
            
            # Color
            colorButton = QgsColorButton()
            colorButton.setColor(category.symbol().color())
            colorButton.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 1, colorButton)
            
            # Size
            sizeEdit = QLineEdit()
            if self.currentLayer.geometryType() == 1:  # Line
                sizeEdit.setText(str(category.symbol().width()))
            else:  # Point
                sizeEdit.setText(str(category.symbol().size()))
            sizeEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 2, sizeEdit)
            
            # Value (category value) - ComboBox for editing
            if self.isEditing:
                valueCombo = QComboBox()
                valueCombo.addItem(str(category.value()))
                self.tableView.setCellWidget(i, 3, valueCombo)
            else:
                valueItem = QTableWidgetItem(str(category.value()))
                valueItem.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.tableView.setItem(i, 3, valueItem)
            
            # Legend
            legendEdit = QLineEdit(category.label())
            legendEdit.setEnabled(self.isEditing)
            self.tableView.setCellWidget(i, 4, legendEdit)
        
        QgsMessageLog.logMessage(
            f"Populated categorical legend with {len(categories)} classes", 
            "QGISRed", Qgis.Info
        )
    
    def onTableItemChanged(self, item):
        """Handle table item changes, particularly for checkbox selection."""
        # Only handle checkbox column (column 0) for categorical legends
        if (self.currentFieldType == self.FIELD_TYPE_CATEGORICAL and 
            item and item.column() == 0 and 
            item.checkState() == Qt.Checked):
            
            # Uncheck all other checkboxes (single selection)
            for row in range(self.tableView.rowCount()):
                if row != item.row():
                    otherItem = self.tableView.item(row, 0)
                    if otherItem:
                        otherItem.setCheckState(Qt.Unchecked)
    
    def getSelectedRow(self):
        """Get the currently selected row (for categorical)."""
        for row in range(self.tableView.rowCount()):
            item = self.tableView.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                return row
        return -1
    
    def moveClassUp(self):
        """Move selected class up (categorical only)."""
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return
            
        selectedRow = self.getSelectedRow()
        if selectedRow <= 0:  # Can't move first row up
            return
            
        # Swap rows in table
        self.swapTableRows(selectedRow, selectedRow - 1)
        
        # Update checkbox selection
        self.tableView.item(selectedRow, 0).setCheckState(Qt.Unchecked)
        self.tableView.item(selectedRow - 1, 0).setCheckState(Qt.Checked)
        
        QgsMessageLog.logMessage("Moved class up", "QGISRed", Qgis.Info)
    
    def moveClassDown(self):
        """Move selected class down (categorical only)."""
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return
            
        selectedRow = self.getSelectedRow()
        if selectedRow < 0 or selectedRow >= self.tableView.rowCount() - 1:
            return
            
        # Swap rows in table
        self.swapTableRows(selectedRow, selectedRow + 1)
        
        # Update checkbox selection
        self.tableView.item(selectedRow, 0).setCheckState(Qt.Unchecked)
        self.tableView.item(selectedRow + 1, 0).setCheckState(Qt.Checked)
        
        QgsMessageLog.logMessage("Moved class down", "QGISRed", Qgis.Info)
    
    def swapTableRows(self, row1, row2):
        """Swap two rows in the table."""
        if row1 < 0 or row2 < 0 or row1 >= self.tableView.rowCount() or row2 >= self.tableView.rowCount():
            return
            
        # Store data from both rows
        row1Data = []
        row2Data = []
        
        for col in range(self.tableView.columnCount()):
            # Get items
            item1 = self.tableView.item(row1, col)
            item2 = self.tableView.item(row2, col)
            
            # Get widgets
            widget1 = self.tableView.cellWidget(row1, col)
            widget2 = self.tableView.cellWidget(row2, col)
            
            # Store data
            if item1:
                row1Data.append(('item', item1.text(), item1.checkState() if col == 0 else None))
            elif widget1:
                if isinstance(widget1, QgsColorButton):
                    row1Data.append(('color', widget1.color()))
                elif isinstance(widget1, QLineEdit):
                    row1Data.append(('text', widget1.text()))
                elif isinstance(widget1, QComboBox):
                    row1Data.append(('combo', widget1.currentText()))
                else:
                    row1Data.append(None)
            else:
                row1Data.append(None)
                
            if item2:
                row2Data.append(('item', item2.text(), item2.checkState() if col == 0 else None))
            elif widget2:
                if isinstance(widget2, QgsColorButton):
                    row2Data.append(('color', widget2.color()))
                elif isinstance(widget2, QLineEdit):
                    row2Data.append(('text', widget2.text()))
                elif isinstance(widget2, QComboBox):
                    row2Data.append(('combo', widget2.currentText()))
                else:
                    row2Data.append(None)
            else:
                row2Data.append(None)
        
        # Swap the data
        for col in range(self.tableView.columnCount()):
            # Clear both cells
            self.tableView.setItem(row1, col, None)
            self.tableView.setItem(row2, col, None)
            self.tableView.removeCellWidget(row1, col)
            self.tableView.removeCellWidget(row2, col)
            
            # Set row2 data to row1
            if row2Data[col]:
                dataType, *data = row2Data[col]
                if dataType == 'item':
                    item = QTableWidgetItem(data[0])
                    if col == 0 and data[1] is not None:
                        item.setCheckState(data[1])
                    self.tableView.setItem(row1, col, item)
                elif dataType == 'color':
                    widget = QgsColorButton()
                    widget.setColor(data[0])
                    widget.setEnabled(self.isEditing)
                    self.tableView.setCellWidget(row1, col, widget)
                elif dataType == 'text':
                    widget = QLineEdit(data[0])
                    widget.setEnabled(self.isEditing)
                    self.tableView.setCellWidget(row1, col, widget)
                elif dataType == 'combo':
                    widget = QComboBox()
                    widget.addItem(data[0])
                    self.tableView.setCellWidget(row1, col, widget)
            
            # Set row1 data to row2
            if row1Data[col]:
                dataType, *data = row1Data[col]
                if dataType == 'item':
                    item = QTableWidgetItem(data[0])
                    if col == 0 and data[1] is not None:
                        item.setCheckState(data[1])
                    self.tableView.setItem(row2, col, item)
                elif dataType == 'color':
                    widget = QgsColorButton()
                    widget.setColor(data[0])
                    widget.setEnabled(self.isEditing)
                    self.tableView.setCellWidget(row2, col, widget)
                elif dataType == 'text':
                    widget = QLineEdit(data[0])
                    widget.setEnabled(self.isEditing)
                    self.tableView.setCellWidget(row2, col, widget)
                elif dataType == 'combo':
                    widget = QComboBox()
                    widget.addItem(data[0])
                    self.tableView.setCellWidget(row2, col, widget)
    
    def addClass(self):
        """Add a new class to the legend."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            # Add a new numeric range
            rowCount = self.tableView.rowCount()
            self.tableView.insertRow(rowCount)
            
            # Add default widgets
            checkboxItem = QTableWidgetItem()
            checkboxItem.setCheckState(Qt.Unchecked)
            self.tableView.setItem(rowCount, 0, checkboxItem)
            
            colorButton = QgsColorButton()
            colorButton.setColor(QColor(128, 128, 128))
            self.tableView.setCellWidget(rowCount, 1, colorButton)
            
            sizeEdit = QLineEdit("1.0")
            self.tableView.setCellWidget(rowCount, 2, sizeEdit)
            
            valueItem = QTableWidgetItem("0.0 - 0.0")
            self.tableView.setItem(rowCount, 3, valueItem)
            
            legendEdit = QLineEdit("New Class")
            self.tableView.setCellWidget(rowCount, 4, legendEdit)
            
            QgsMessageLog.logMessage("Added new numeric class", "QGISRed", Qgis.Info)
            
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            # Check if there are values left to add
            # TODO: Check available values from field
            
            rowCount = self.tableView.rowCount()
            self.tableView.insertRow(rowCount)
            
            # Add default widgets
            checkboxItem = QTableWidgetItem()
            checkboxItem.setCheckState(Qt.Unchecked)
            self.tableView.setItem(rowCount, 0, checkboxItem)
            
            colorButton = QgsColorButton()
            colorButton.setColor(QColor(128, 128, 128))
            self.tableView.setCellWidget(rowCount, 1, colorButton)
            
            sizeEdit = QLineEdit("1.0")
            self.tableView.setCellWidget(rowCount, 2, sizeEdit)
            
            valueItem = QTableWidgetItem("Other")
            self.tableView.setItem(rowCount, 3, valueItem)
            
            legendEdit = QLineEdit("New Category")
            self.tableView.setCellWidget(rowCount, 4, legendEdit)
            
            QgsMessageLog.logMessage("Added new categorical class", "QGISRed", Qgis.Info)
    
    def removeClass(self):
        """Remove selected class from the legend."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        # Don't allow removing if only one class remains
        if self.tableView.rowCount() <= 1:
            QMessageBox.warning(
                self, 
                "Cannot Remove", 
                "At least one class must remain in the legend."
            )
            return
        
        # For categorical, remove selected row
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            selectedRow = self.getSelectedRow()
            if selectedRow >= 0:
                self.tableView.removeRow(selectedRow)
                QgsMessageLog.logMessage(f"Removed class at row {selectedRow}", "QGISRed", Qgis.Info)
        else:
            # For numeric, remove first class
            self.tableView.removeRow(0)
            QgsMessageLog.logMessage("Removed first class", "QGISRed", Qgis.Info)
    
    def classifyEqualInterval(self):
        """Apply equal interval classification (numeric only)."""
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return
        
        # Get min/max values from field
        fieldName = self.currentFieldName
        if not fieldName:
            return
            
        # Calculate statistics
        fieldIdx = self.currentLayer.fields().indexOf(fieldName)
        if fieldIdx < 0:
            return
            
        minVal = self.currentLayer.minimumValue(fieldIdx)
        maxVal = self.currentLayer.maximumValue(fieldIdx)
        
        if minVal is None or maxVal is None:
            return
            
        # Get number of classes from table
        numClasses = self.tableView.rowCount()
        if numClasses < 2:
            numClasses = 5  # Default
            
        # Calculate equal intervals
        interval = (maxVal - minVal) / numClasses
        
        # Update table with new ranges
        for i in range(numClasses):
            lower = minVal + (i * interval)
            upper = minVal + ((i + 1) * interval)
            
            # Update value column
            valueText = f"{lower:.2f} - {upper:.2f}"
            if self.tableView.item(i, 3):
                self.tableView.item(i, 3).setText(valueText)
            
            # Update legend if empty
            legendWidget = self.tableView.cellWidget(i, 4)
            if isinstance(legendWidget, QLineEdit) and not legendWidget.text():
                legendWidget.setText(valueText)
        
        QgsMessageLog.logMessage(
            f"Applied equal interval classification with {numClasses} classes", 
            "QGISRed", Qgis.Info
        )
    
    def classifyQuantiles(self):
        """Apply quantile classification (numeric only)."""
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return
            
        fieldName = self.currentFieldName
        if not fieldName:
            return
            
        # Get all values
        values = []
        for feature in self.currentLayer.getFeatures():
            val = feature[fieldName]
            if val is not None:
                values.append(val)
        
        if not values:
            return
            
        values.sort()
        
        # Get number of classes
        numClasses = self.tableView.rowCount()
        if numClasses < 2:
            numClasses = 5
            
        # Calculate quantiles
        quantileSize = len(values) / numClasses
        
        # Update table with quantile ranges
        for i in range(numClasses):
            lowerIdx = int(i * quantileSize)
            upperIdx = int((i + 1) * quantileSize) - 1
            
            if upperIdx >= len(values):
                upperIdx = len(values) - 1
                
            lower = values[lowerIdx]
            upper = values[upperIdx]
            
            # Update value column
            valueText = f"{lower:.2f} - {upper:.2f}"
            if self.tableView.item(i, 3):
                self.tableView.item(i, 3).setText(valueText)
            
            # Update legend if empty
            legendWidget = self.tableView.cellWidget(i, 4)
            if isinstance(legendWidget, QLineEdit) and not legendWidget.text():
                legendWidget.setText(valueText)
        
        QgsMessageLog.logMessage(
            f"Applied quantile classification with {numClasses} classes", 
            "QGISRed", Qgis.Info
        )
    
    def classifyNaturalBreaks(self):
        """Apply natural breaks (Jenks) classification (numeric only)."""
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return
        
        # This would require implementing Jenks natural breaks algorithm
        # For now, just log the action
        QgsMessageLog.logMessage(
            "Natural breaks classification not fully implemented yet", 
            "QGISRed", Qgis.Warning
        )
        
        # Could use QgsClassificationJenks from QGIS API
        # Implementation would be similar to quantiles but using Jenks algorithm
    
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
            
        # Create new ranges from table
        ranges = []
        for row in range(self.tableView.rowCount()):
            # Get values from table
            valueText = self.tableView.item(row, 3).text()
            if " - " in valueText:
                parts = valueText.split(" - ")
                lower = float(parts[0])
                upper = float(parts[1])
            else:
                continue
                
            # Get color
            colorWidget = self.tableView.cellWidget(row, 1)
            if isinstance(colorWidget, QgsColorButton):
                color = colorWidget.color()
            else:
                color = QColor(128, 128, 128)
            
            # Get label
            legendWidget = self.tableView.cellWidget(row, 4)
            if isinstance(legendWidget, QLineEdit):
                label = legendWidget.text()
            else:
                label = valueText
            
            # Create symbol
            symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
            symbol.setColor(color)
            
            # Get size
            sizeWidget = self.tableView.cellWidget(row, 2)
            if isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    if self.currentLayer.geometryType() == 1:  # Line
                        symbol.setWidth(size)
                    else:  # Point
                        symbol.setSize(size)
                except:
                    pass
            
            # Create range
            rangeItem = QgsRendererRange(lower, upper, symbol, label)
            ranges.append(rangeItem)
        
        # Create and apply renderer
        if ranges:
            renderer = QgsGraduatedSymbolRenderer(self.currentFieldName, ranges)
            self.currentLayer.setRenderer(renderer)
    
    def applyCategoricalLegend(self):
        """Apply categorical legend from table to layer."""
        if not self.currentLayer or not self.currentFieldName:
            return
            
        # Create categories from table
        categories = []
        for row in range(self.tableView.rowCount()):
            # Get value
            valueWidget = self.tableView.cellWidget(row, 3)
            if isinstance(valueWidget, QComboBox):
                value = valueWidget.currentText()
            else:
                valueItem = self.tableView.item(row, 3)
                value = valueItem.text() if valueItem else ""
            
            # Get color
            colorWidget = self.tableView.cellWidget(row, 1)
            if isinstance(colorWidget, QgsColorButton):
                color = colorWidget.color()
            else:
                color = QColor(128, 128, 128)
            
            # Get label
            legendWidget = self.tableView.cellWidget(row, 4)
            if isinstance(legendWidget, QLineEdit):
                label = legendWidget.text()
            else:
                label = value
            
            # Create symbol
            symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
            symbol.setColor(color)
            
            # Get size
            sizeWidget = self.tableView.cellWidget(row, 2)
            if isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    if self.currentLayer.geometryType() == 1:  # Line
                        symbol.setWidth(size)
                    else:  # Point
                        symbol.setSize(size)
                except:
                    pass
            
            # Create category
            category = QgsRendererCategory(value, symbol, label)
            categories.append(category)
        
        # Create and apply renderer
        if categories:
            renderer = QgsCategorizedSymbolRenderer(self.currentFieldName, categories)
            self.currentLayer.setRenderer(renderer)
    
    def saveProjectStyle(self):
        """Save the current style for the project."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
            
        # Get project directory
        utils = QGISRedUtils()
        projectDir = utils.ProjectDirectory
        if not projectDir:
            projectPath = QgsProject.instance().fileName()
            if projectPath:
                projectDir = os.path.dirname(projectPath)
            else:
                QMessageBox.warning(self, "No Project", "Please save the project first.")
                return
        
        # Create layerStyles subfolder if it doesn't exist
        stylesDir = os.path.join(projectDir, "layerStyles")
        if not os.path.exists(stylesDir):
            os.makedirs(stylesDir)
        
        # Generate filename based on layer identifier
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            layerIdentifier = self.currentLayer.name().lower().replace(" ", "_")
        
        qmlPath = os.path.join(stylesDir, f"{layerIdentifier}.qml")
        
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
        
        # Get plugin layerStyles folder
        stylesDir = os.path.join(self.pluginFolder, "layerStyles")
        if not os.path.exists(stylesDir):
            os.makedirs(stylesDir)
        
        # Generate filename
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            layerIdentifier = self.currentLayer.name().lower().replace(" ", "_")
        
        qmlPath = os.path.join(stylesDir, f"{layerIdentifier}.qml")
        
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
        
        # Get default styles folder
        defaultsDir = os.path.join(self.pluginFolder, "layerStyles", "Defaults")
        
        # Generate filename
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            layerIdentifier = self.currentLayer.name().lower().replace(" ", "_")
        
        qmlPath = os.path.join(defaultsDir, f"{layerIdentifier}.qml.back")
        
        if not os.path.exists(qmlPath):
            QMessageBox.warning(
                self, 
                "Default Style Not Found", 
                f"Default style not found for this layer type."
            )
            return
        
        # Apply style directly to layer (as per document - no Apply button in first implementation)
        self.currentLayer.loadNamedStyle(qmlPath)
        self.currentLayer.triggerRepaint()
        
        # Refresh the display
        self.onLayerChanged(self.currentLayer)
        
        QgsMessageLog.logMessage(
            f"Loaded default style from: {qmlPath}", 
            "QGISRed", Qgis.Info
        )
    
    def loadGlobalStyle(self):
        """Load the global style."""
        if not self.currentLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
        
        # Get plugin layerStyles folder
        stylesDir = os.path.join(self.pluginFolder, "layerStyles")
        
        # Generate filename
        layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
        if not layerIdentifier:
            layerIdentifier = self.currentLayer.name().lower().replace(" ", "_")
        
        qmlPath = os.path.join(stylesDir, f"{layerIdentifier}.qml")
        
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
