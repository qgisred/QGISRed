# -*- coding: utf-8 -*-
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QLabel, QToolButton
from PyQt5.QtWidgets import QTableWidgetItem, QHeaderView, QStyle, QAbstractItemView
from PyQt5.QtCore import pyqtSlot, Qt, QEvent
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsSettings
from qgis.utils import iface

from .qgisred_findElements_dock import QGISRedFindElementsDock

FORM_CLASS, _ = uic.loadUiType( os.path.join(os.path.dirname(__file__), "qgisred_elementproperties_dialog.ui") )

class QGISRedElementsPropertyDock(QDockWidget, FORM_CLASS):
    _instance = None

    @classmethod
    def getInstance(cls, parent=None):
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def __init__(self, canvas, parent=None):
        if QGISRedElementsPropertyDock._instance is not None:
            raise Exception("QGISRedElementsPropertyDock is a singleton! Use getInstance() instead.")
        super(QGISRedElementsPropertyDock, self).__init__(parent)
        self.setupUi(self)
        self.setObjectName("QGISRedElementsPropertyDock")
        self.setFloating(False)
        self.setDockStyle()
        self.setupConnections()
        self.initCustomTitleBar()

        self.canvas = canvas

        self.singular_forms = {
            self.tr("Pipes"): self.tr("Pipe"),
            self.tr("Junctions"): self.tr("Junction"),
            self.tr("Multiple Demands"): self.tr("Multiple Demand"),
            self.tr("Reservoirs"): self.tr("Reservoir"),
            self.tr("Tanks"): self.tr("Tank"),
            self.tr("Pumps"): self.tr("Pump"),
            self.tr("Valves"): self.tr("Valve"),
            self.tr("Sources"): self.tr("Source"),
            self.tr("Service Connections"): self.tr("Service Connection"),
            self.tr("Isolation Valves"): self.tr("Isolation Valve"),
            self.tr("Meters"): self.tr("Meter")
        }

        self.original_ids = []
        self.adjacent_highlights = []
        self.main_highlight = None
        self.current_selected_highlight = None
        self.findElemetsdock = None
        self.currentLayer = None
        self.currentFeature = None

        settings = QgsSettings()
        if settings.contains("QGISRed/ElementProperties/geometry"):
            self.restoreGeometry(settings.value("QGISRed/ElementProperties/geometry"))
    
    def closeEvent(self, event):
        settings = QgsSettings()
        settings.setValue("QGISRed/ElementProperties/geometry", self.saveGeometry())
        self.clearHighlights()
        self.clearAllLayerSelections()
        QGISRedElementsPropertyDock._instance = None
        super(QGISRedElementsPropertyDock, self).closeEvent(event)

    @pyqtSlot()
    def clearAll(self):
        self.clearHighlights()
        self.clearAllLayerSelections()

    def clearAllLayerSelections(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def clearHighlights(self):
        pass

    def initCustomTitleBar(self):
        titleBar = QWidget(self)
        layout = QHBoxLayout(titleBar)
        layout.setContentsMargins(5, 0, 5, 0)

        self.titleLabel = QLabel(self.windowTitle(), titleBar)
        self.titleLabel.setStyleSheet("font-weight: normal")
        self.titleLabel.setText("Element Properties")
        layout.addWidget(self.titleLabel)
        layout.addStretch()

        findButton = QToolButton(titleBar)
        icon_find = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFindElements.png'))
        findButton.setIcon(icon_find)
        findButton.setToolTip("Find Elements by ID")
        findButton.clicked.connect(self.openFindElemetsDock)
        layout.addWidget(findButton)

        self.floatButton = QToolButton(titleBar)
        float_icon = self.style().standardIcon(QStyle.SP_TitleBarNormalButton)
        self.floatButton.setIcon(float_icon)
        self.floatButton.setToolTip("Float")
        self.floatButton.clicked.connect(self.toggleFloating)
        layout.addWidget(self.floatButton)

        self.closeButton = QToolButton(titleBar)
        close_icon = self.style().standardIcon(QStyle.SP_TitleBarCloseButton)
        self.closeButton.setIcon(close_icon)
        self.closeButton.setToolTip("Close")
        self.closeButton.clicked.connect(self.close)
        layout.addWidget(self.closeButton)

        self.setTitleBarWidget(titleBar)

    def onProjectClosed(self):
        self.clearHighlights()
        self.clearAllLayerSelections()

    @pyqtSlot()
    def openFindElemetsDock(self):
        existing_docks = self.canvas.findChildren(QGISRedFindElementsDock)
        if existing_docks:
            dock = existing_docks[0]
            if dock.isVisible():
                dock.close()
                return
            iface.addDockWidget(Qt.RightDockWidgetArea, dock)
            dock.show()
            dock.raise_()
            dock.activateWindow()
            if self.currentLayer and self.currentFeature:
                dock.findFeature(self.currentLayer, self.currentFeature)
            iface.mainWindow().splitDockWidget(dock, self, Qt.Vertical)
        else:
            self.findElemetsdock = QGISRedFindElementsDock.getInstance(self.canvas)
            iface.addDockWidget(Qt.RightDockWidgetArea, self.findElemetsdock)
            if self.currentLayer and self.currentFeature:
                self.findElemetsdock.findFeature(self.currentLayer, self.currentFeature)
            self.findElemetsdock.show()
            iface.mainWindow().splitDockWidget(self.findElemetsdock, self, Qt.Vertical)


    def populatedataTableWidget(self):
        if not hasattr(self, 'dataTableWidget'):
            return
        
        self.dataTableWidget.clearContents()
        self.dataTableWidget.setShowGrid(False)
        self.dataTableWidget.setStyleSheet("QTableWidget::item { padding: 1px; }")
        
        self.dataTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        fields = self.currentLayer.fields()
        attributes = self.currentFeature.attributes()
        num_fields = len(fields)
        self.dataTableWidget.setRowCount(num_fields)
        self.dataTableWidget.setColumnCount(2)
        self.dataTableWidget.setHorizontalHeaderLabels(["Property", "Value"])
        
        header = self.dataTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStyleSheet("QHeaderView::section { font-weight: bold; }")
        
        self.dataTableWidget.verticalHeader().setDefaultSectionSize(20)
        
        total_width = self.dataTableWidget.viewport().width() + 20 
        self.dataTableWidget.setColumnWidth(0, total_width // 2)
        self.dataTableWidget.setColumnWidth(1, total_width // 2)
        
        self.dataTableWidget.verticalHeader().setVisible(False)
        
        for row, field in enumerate(fields):
            field_item = QTableWidgetItem(field.name())
            value_item = QTableWidgetItem(str(attributes[row]))
            self.dataTableWidget.setItem(row, 0, field_item)
            self.dataTableWidget.setItem(row, 1, value_item)

    def setDockStyle(self):
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconElementsProperties.png')
        self.setWindowIcon(QIcon(icon_path))

    def setupConnections(self):
        pass

    def setupTabs(self, visible_tabs):
        ...
        #TODO Only data tab for now, rest is hidden
        # tabs_info = {
        #     "tabData": self.tabData,
        #     "tabResults": self.tabResults,
        #     "tabCurves": self.tabCurves,
        #     "tabPatterns": self.tabPatterns,
        #     "tabControls": self.tabControls
        # }
        # for tab_name, tab_widget in tabs_info.items():
        #     if tab_widget is None:
        #         continue
        #     tab_index = self.tabWidget.indexOf(tab_widget)
        #     if tab_index == -1:
        #         continue
        #     else:
        #         self.tabWidget.setTabVisible(tab_index, tab_name in visible_tabs)

    @pyqtSlot()
    def toggleFloating(self):
        self.setFloating(not self.isFloating())

    def handleJunctions(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handlePipes(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handlePumps(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleReservoirs(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleTanks(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleValves(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
    
    def handleMeters(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleIsolationValves(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleServiceConnections(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def getCheckedInputGroupLayers(self):
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            return []
        return inputs_group.checkedLayers()

    def findOverlappingFeatures(self, target_feature, search_identifier):
        overlapping_features = []
        target_geom = target_feature.geometry()
        
        for layer in self.getCheckedInputGroupLayers():
            if layer.customProperty("qgisred_identifier") == search_identifier:
                for feat in layer.getFeatures():
                    if target_geom.intersects(feat.geometry()):
                        overlapping_features.append(feat)
        return overlapping_features

    def loadFeature(self, layer, feature):
        if not layer or not feature:
            return

        self.currentLayer = layer
        self.currentFeature = feature
        layer.selectByIds([feature.id()])
        self.populatedataTableWidget()

        base_title = f"{self.singular_forms.get(layer.name(), layer.name())} {feature.attribute('Id')}"
        suffix_source = ""
        suffix_demand = ""

        id_property = layer.customProperty("qgisred_identifier")
        if id_property in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
            source_features = self.findOverlappingFeatures(feature, "qgisred_sources")
            if source_features:
                suffix_source = "(Source)"
                for src_feat in source_features:
                    self.appendFeatureProperties(src_feat, "Source")
            if id_property == "qgisred_junctions":
                demand_features = self.findOverlappingFeatures(feature, "qgisred_demands")
                if demand_features:
                    suffix_demand = "(Mult.Dem)"
                    for dem_feat in demand_features:
                        self.appendFeatureProperties(dem_feat, "Mult.Dem")

        self.labelFoundElement.setText(f"{base_title} {suffix_source}{suffix_demand}")
        self.labelFoundElement.setStyleSheet("font-weight: bold; font-size: 12pt;")

    def appendFeatureProperties(self, feature, label_suffix=""):
        if not hasattr(self, 'dataTableWidget'):
            return
        fields = feature.fields()
        attributes = feature.attributes()
        current_row_count = self.dataTableWidget.rowCount()
        new_row_count = current_row_count + len(fields)
        self.dataTableWidget.setRowCount(new_row_count)
        for i, field in enumerate(fields):
            # Append the label suffix to the field name.
            field_name = f"{field.name()} ({label_suffix})"
            field_item = QTableWidgetItem(field_name)
            value_item = QTableWidgetItem(str(attributes[i]))
            self.dataTableWidget.setItem(current_row_count + i, 0, field_item)
            self.dataTableWidget.setItem(current_row_count + i, 1, value_item)
