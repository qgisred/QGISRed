# -*- coding: utf-8 -*-

import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox
from PyQt5 import sip
from qgis.PyQt import uic

from qgis.core import QgsVectorLayer, QgsMessageLog, Qgis
from qgis.core import QgsVectorLayer

from ..tools.qgisred_utils import QGISRedUtils

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

class QGISRedLegendsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLegendsDialog, self).__init__(parent)
        self.setupUi(self)
        self.config()
        self.gbLegends.setEnabled(bool(self.cbLegendLayer.currentLayer())) 

        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.reject)

        self.btIntervals.clicked.connect(self.classifyEqualInterval)
        self.btQuantiles.clicked.connect(self.classifyQuantiles)
        self.btBreaks.clicked.connect(self.classifyNaturalBreaks)
        
        self.btLoadDefault.clicked.connect(self.loadDefaultStyle)
        self.btSaveGlobal.clicked.connect(self.saveGlobalStyle)

    def config(self):
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))
    
    def onLayerChanged(self, layer):
        if layer and isinstance(layer, QgsVectorLayer):
            QgsMessageLog.logMessage(f"Legend tab: Layer '{layer.name()}' selected.", "QGISRed", Qgis.Info)
            self.gbLegends.setEnabled(True)
            self.gbLegends.setTitle(self.tr(f"Legend for {layer.name()}"))
            print(f"Legend tab: Layer '{layer.name()}' selected.", "QGISRed")
            # TODO: Add logic to populate the table view (self.tableView)
        else:
            self.gbLegends.setEnabled(False)
            self.gbLegends.setTitle(self.tr("Legend"))

    def applyLegend(self):
        selectedLayer = self.cbLegendLayer.currentLayer()
        if not selectedLayer:
            QMessageBox.warning(self, "No Layer", "Please select a layer first.")
            return
            
        QgsMessageLog.logMessage(f"Applying legend to '{selectedLayer.name()}'...", "QGISRed", Qgis.Info)
        # TODO: Implement the logic to read the table view and apply the symbology.
        print("Apply Legend button clicked!")

    def classifyEqualInterval(self):
        pass
        
    def classifyQuantiles(self):
        pass

    def classifyNaturalBreaks(self):
        pass

    def saveGlobalStyle(self):
        pass

    def loadDefaultStyle(self):
        pass