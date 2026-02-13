# -*- coding: utf-8 -*-

# Standard library imports
import os
import random
import math
import statistics

# Third-party imports
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtWidgets import (QDialog, QMessageBox, QHeaderView,
                             QComboBox, QLineEdit, QAbstractItemView, QLabel,
                             QWidget, QHBoxLayout, QPushButton, QVBoxLayout)
from PyQt5.QtCore import QVariant, Qt, QTimer
from qgis.PyQt import uic

# QGIS imports
from qgis.core import (QgsProject, QgsVectorLayer, QgsMessageLog, Qgis, 
                       QgsGraduatedSymbolRenderer, QgsCategorizedSymbolRenderer, 
                       QgsRendererRange, QgsRendererCategory, QgsSymbol, 
                       QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGradientColorRamp, 
                       QgsClassificationJenks, QgsClassificationPrettyBreaks)
from qgis.utils import iface

# Local imports
from ..tools.qgisred_utils import QGISRedUtils
from .qgisred_custom_dialogs import RangeEditDialog, SymbolColorSelectorWithCheckbox

# Load UI
formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

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
        self.dragPosition = None
        self.layerTreeViewConnection = None

    def initUi(self):
        """Initialize UI components."""
        self.configWindow()
        self.setupTableView()
        self.populateClassificationModes()
        self.populateGroups()
        self.setupClassCountField()
        self.labelIntervalRange.setVisible(False)
        self.spinIntervalRange.setVisible(False)
        #self.initializeUiVisibility()

    def configWindow(self):
        """Configure window appearance and custom title bar."""
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setupCustomTitleBar()
        self.btClassPlus.setIcon(QIcon(":/images/themes/default/symbologyAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/themes/default/symbologyRemove.svg"))

    def setupCustomTitleBar(self):
        """Build custom title bar."""
        titleBar = QWidget(self)
        titleBar.setStyleSheet("background-color: rgb(215, 215, 215);")
        
        titleLabel = QLabel("QGISRed Legend Editor", titleBar)
        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(9)
        titleLabel.setFont(titleFont)
        titleLabel.setStyleSheet("color: rgb(25, 64, 75); background-color: transparent;")

        closeButton = QPushButton("x", titleBar)
        closeButton.setFixedSize(20, 20)
        closeButton.setStyleSheet("QPushButton { background-color: transparent; color: rgb(25, 64, 75); font-weight: bold; border: none; } QPushButton:hover { background-color: rgb(195, 195, 195); }")
        closeButton.clicked.connect(self.close)

        layout = QHBoxLayout(titleBar)
        layout.setContentsMargins(10, 0, 5, 0)
        layout.addWidget(titleLabel)
        layout.addStretch()
        layout.addWidget(closeButton)

        mainLayout = self.layout()
        oldContent = mainLayout.itemAt(0).widget()
        mainLayout.removeWidget(oldContent)
        
        newContainer = QVBoxLayout()
        newContainer.setContentsMargins(0, 0, 0, 0)
        newContainer.setSpacing(0)
        newContainer.addWidget(titleBar)
        newContainer.addWidget(oldContent)
        
        wrapper = QWidget()
        wrapper.setLayout(newContainer)
        mainLayout.addWidget(wrapper)

        self.titleBar = titleBar
        self.titleBar.mousePressEvent = self.titleBarMousePressEvent
        self.titleBar.mouseMoveEvent = self.titleBarMouseMoveEvent

    def setupTableView(self):
        """Configure table columns and visual style."""
        self.tableView.setColumnCount(4)
        self.tableView.setHorizontalHeaderLabels(["Symbol", "Size", "Value", "Legend"])
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.tableView.setColumnWidth(0, 50)
        self.tableView.setColumnWidth(1, 60)
        self.tableView.setColumnWidth(2, 100)
        
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tableView.setAlternatingRowColors(False)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setShowGrid(False)
        self.tableView.setStyleSheet("QTableWidget { background-color: white; border: none; selection-background-color: #3399ff; selection-color: white; } QTableWidget::item { border: none; }")

    def setupClassCountField(self):
        """Configure read-only class count field."""
        self.leClassCount.setReadOnly(True)
        self.leClassCount.setStyleSheet("QLineEdit { background-color: #F0F0F0; color: #808080; }")

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

    def titleBarMousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def titleBarMouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.dragPosition:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()

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
        self.cbLegendLayer.blockSignals(False)
        self.onLayerChanged(self.cbLegendLayer.currentLayer())

    def onLayerChanged(self, layer):
        """Handle layer selection change."""
        if layer and isinstance(layer, QgsVectorLayer):
            self.currentLayer = layer
            self.originalRenderer = layer.renderer().clone() if layer.renderer() else None
            self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)
            
            self.frameLegends.setEnabled(True)
            self.labelFrameLegends.setText(self.tr(f"Legend for {layer.name()}"))
            self.updateUiBasedOnFieldType()
            
            if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
                self.cbMode.blockSignals(True)
                self.cbMode.setCurrentIndex(0)
                self.cbMode.blockSignals(False)
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
        # Color
        cw = SymbolColorSelectorWithCheckbox(self.tableView, geom, symbol.color(), visible, "")
        cw.colorSelector.setEnabled(self.isEditing)
        size = symbol.width() if geom == "line" else symbol.size()
        cw.updateSymbolSize(size, geom == "line")
        self.tableView.setCellWidget(row, 0, cw)
        
        # Size
        sw = QLineEdit(str(size))
        sw.setEnabled(self.isEditing)
        sw.setAlignment(Qt.AlignCenter)
        sw.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))
        self.tableView.setCellWidget(row, 1, sw)
        
        # Value
        vw = QLineEdit(valText)
        vw.setReadOnly(True)
        vw.setAlignment(Qt.AlignCenter)
        if isReadOnlyVal:
            vw.setStyleSheet("QLineEdit { background-color: white; color: #808080; border: none; }")
        else:
            vw.setStyleSheet("QLineEdit { background-color: white; color: #404040; border: none; }")
            vw.mouseDoubleClickEvent = lambda _event, r=row: self.openRangeEditor(r)
        self.tableView.setCellWidget(row, 2, vw)

        # Legend
        lw = QLineEdit(legendText)
        lw.setEnabled(self.isEditing)
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
            mid = self.cbMode.currentData()
            if mid: self.applyClassificationMethod(mid)
        self.updateButtonStates()

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
            if self.cbMode.currentData(): self.applyClassificationMethod(self.cbMode.currentData())

        self.updateClassCount()
        self.updateButtonStates()

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
        geom = self.getGeometryHint()
        for c, d in enumerate(data):
            if not d: continue
            dtype = d[0]
            if dtype == 'cw':
                cw = SymbolColorSelectorWithCheckbox(self.tableView, geom, d[1], d[2], "")
                cw.colorSelector.setEnabled(self.isEditing)
                cw.updateSymbolSize(d[3], geom=="line")
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
                            le.setStyleSheet("QLineEdit { background-color: white; color: #404040; border: none; }")
                            le.mouseDoubleClickEvent = lambda _event, r=row: self.openRangeEditor(r)
                        else:  # Categorical - truly read-only
                            le.setStyleSheet("QLineEdit { background-color: white; color: #808080; border: none; }")
                    else:  # Other read-only columns
                        le.setStyleSheet("QLineEdit { background-color: #F8F8F8; color: #808080; }")
                if c == 1:
                    le.setAlignment(Qt.AlignCenter)
                    le.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))
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
            breaks = [minV] + [vals[int(i/num * len(vals))] for i in range(1, num)] + [maxV]
        elif methodId == "Jenks":
            m = QgsClassificationJenks()
            m.setLabelFormat("%1 - %2")
            c = m.classes(self.currentLayer, self.currentFieldName, num)
            breaks = [minV] + [x.upperBound() for x in c]
        elif methodId == "StdDev":
            mu = statistics.mean(vals)
            sd = statistics.stdev(vals) if len(vals) > 1 else 0
            breaks = sorted(list(set([minV, maxV] + [mu + i*sd for i in range(-num//2, num//2 + 1) if minV < mu + i*sd < maxV])))
            num = len(breaks) - 1
        elif methodId == "Pretty":
            m = QgsClassificationPrettyBreaks()
            c = m.classes(self.currentLayer, self.currentFieldName, num)
            breaks = [minV] + [x.upperBound() for x in c]

        if len(breaks) < 2: return

        # Adjust row count
        while self.tableView.rowCount() < num: self.addNumericClass()
        while self.tableView.rowCount() > num: self.tableView.removeRow(self.tableView.rowCount()-1)

        # Apply
        ramp = QgsGradientColorRamp(QColor(0,0,255), QColor(255,0,0))
        for i in range(num):
            l, u = breaks[i], breaks[i+1]
            txt = f"{l:.2f} - {u:.2f}"
            vw = self.tableView.cellWidget(i, 2)
            if isinstance(vw, QLineEdit):
                vw.setText(txt)

            col = ramp.color(i / max(1, num - 1))
            cw = self.tableView.cellWidget(i, 0)
            if isinstance(cw, SymbolColorSelectorWithCheckbox): cw.setColor(col)

            lw = self.tableView.cellWidget(i, 3)
            if isinstance(lw, QLineEdit): lw.setText(txt)
        
        self.updateClassCount()

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
        
        name = QGISRedUtils().identifierToElementName.get(ident)
        if not name: return
        
        fname = name.replace(" ", "") + ".qml"
        
        if globalStyle:
            folder = os.path.join(self.pluginFolder, "layerStyles")
        else:
            proj = QgsProject.instance().fileName()
            folder = os.path.join(os.path.dirname(proj), "layerStyles") if proj else None
            
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

    def _loadStyle(self, isDefault):
        if not self.currentLayer: return
        ident = self.currentLayer.customProperty("qgisred_identifier")
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
        
        self.btClassMinus.setEnabled(sel >= 1)
        if isCat:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())
            self.btUp.setEnabled(sel == 1 and self.getSelectedRows()[0] > 0)
            self.btDown.setEnabled(sel == 1 and self.getSelectedRows()[0] < self.tableView.rowCount() - 1)
        else:
            self.btClassPlus.setEnabled(True)
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
        if self.hasOtherValuesCategory(): return
        self.addCategoricalClass() # Logic handles creating 'Other' if empty vals

    def cancelAndClose(self):
        if self.currentLayer and self.originalRenderer and self.isEditing:
            self.currentLayer.setRenderer(self.originalRenderer.clone())
            self.currentLayer.triggerRepaint()
        self.reject()

    def closeEvent(self, event):
        """Clean up connections when dialog is closed."""
        # Disconnect layer tree view signal
        if self.layerTreeViewConnection and iface and iface.layerTreeView():
            try:
                iface.layerTreeView().currentLayerChanged.disconnect(self.onQgisLayerSelectionChanged)
            except:
                pass
        super().closeEvent(event)