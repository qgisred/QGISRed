# -*- coding: utf-8 -*-
import csv
import json
import math
import os
from datetime import datetime

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QBrush, QColor, QIcon
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
)
from qgis.PyQt import uic
from qgis.core import QgsExpression, QgsFeatureRequest, QgsProject

from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from .statistics_histogram_widget import StatisticsHistogramWidget
from .statistics_metadata import (
    DEFAULT_NUM_CLASSES,
    ELEMENT_PROPERTIES,
    ELEMENT_TYPE_ORDER,
    NUM_CLASSES_CHOICES,
    getPropertyMode,
    getRangedOptions,
    getRangedPreset,
    isCategoricalField,
)

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statisticsandgraphs_dock.ui"))


class QGISRedStatisticsAndPlotsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsAndPlotsDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.fieldUtils = QGISRedFieldUtils()
        self.suspendCascade = False
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0

        self.setupHistogram()
        self.setupIcons()
        self.setupConnections()
        self.populateElementTypes()
        self.loadDefaults()

    def safeDisconnect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def setupHistogram(self):
        self.histogram = StatisticsHistogramWidget(self.graphWidget)
        layout = QVBoxLayout(self.graphWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.histogram)
        self.graphWidget.setLayout(layout)
        self.labelOnlySelectedElements.hide()

    def setupIcons(self):
        self.btImport.setIcon(QIcon(":/images/iconStatisticsImport.svg"))
        self.btImport.setToolTip(self.tr("Import query configuration (.json)"))
        self.btExport.setIcon(QIcon(":/images/iconStatisticsExport.svg"))
        self.btExport.setToolTip(self.tr("Export query configuration (.json)"))
        self.btExcel.setIcon(QIcon(":/images/iconStatisticsExcel.svg"))
        self.btExcel.setToolTip(self.tr("Export table to CSV"))

    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.onElementTypeChanged)
        self.cbProperty.currentIndexChanged.connect(self.onPropertyChanged)
        self.cbClassifiedBy.currentIndexChanged.connect(self.onClassifyByChanged)
        self.cbRanged.currentIndexChanged.connect(self.onRangedChanged)
        self.cbAttribute.currentIndexChanged.connect(self.onAttributeChanged)
        self.btAnalyze.clicked.connect(self.analyze)
        self.btImport.clicked.connect(self.importConfig)
        self.btExport.clicked.connect(self.exportConfig)
        self.btExcel.clicked.connect(self.exportTableCsv)

    def disconnectSignals(self):
        self.safeDisconnect(self.cbElementType.currentIndexChanged, self.onElementTypeChanged)
        self.safeDisconnect(self.cbProperty.currentIndexChanged, self.onPropertyChanged)
        self.safeDisconnect(self.cbClassifiedBy.currentIndexChanged, self.onClassifyByChanged)
        self.safeDisconnect(self.cbRanged.currentIndexChanged, self.onRangedChanged)
        self.safeDisconnect(self.cbAttribute.currentIndexChanged, self.onAttributeChanged)
        self.safeDisconnect(self.btAnalyze.clicked, self.analyze)
        self.safeDisconnect(self.btImport.clicked, self.importConfig)
        self.safeDisconnect(self.btExport.clicked, self.exportConfig)
        self.safeDisconnect(self.btExcel.clicked, self.exportTableCsv)

    def populateElementTypes(self):
        self.suspendCascade = True
        self.cbElementType.clear()
        for elementIdentifier in ELEMENT_TYPE_ORDER:
            self.cbElementType.addItem(self.displayNameForIdentifier(elementIdentifier), elementIdentifier)
        self.suspendCascade = False

    def displayNameForIdentifier(self, elementIdentifier):
        names = {
            "qgisred_pipes": self.tr("Pipes"),
            "qgisred_junctions": self.tr("Junctions"),
            "qgisred_tanks": self.tr("Tanks"),
            "qgisred_reservoirs": self.tr("Reservoirs"),
            "qgisred_valves": self.tr("Valves"),
            "qgisred_pumps": self.tr("Pumps"),
            "qgisred_serviceconnections": self.tr("Service Connections"),
            "qgisred_isolationvalves": self.tr("Isolation Valves"),
        }
        return names.get(elementIdentifier, elementIdentifier)
