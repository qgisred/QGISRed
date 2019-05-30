# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedResultsDock
                                 A QGIS plugin
 Some util tools for GISRed
                             -------------------
        begin                : 2019-03-26
        git sha              : $Format:%H$
        copyright            : (C) 2019 by REDHISP (UPV)
        email                : fmartine@hma.upv.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsCoordinateReferenceSystem
from qgis.PyQt import QtGui, uic

try: #QGis 3.x
    from qgis.gui import QgsProjectionSelectionDialog  as QgsGenericProjectionSelector 
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QFileDialog, QDockWidget, QApplication
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, Qt
    from ..qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from qgis.gui import QgsGenericProjectionSelector
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QTableWidgetItem, QFileDialog, QDockWidget, QApplication
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, Qt
    from qgis.core import QgsMapLayerRegistry
    from ..qgisred_utils import QGISRedUtils

import os
from ctypes import*
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_results_dock.ui'))


class QGISRedResultsDock(QDockWidget, FORM_CLASS):
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    Results= {}
    Variables=""
    TimeIndex = ""
    Time = ""

    def __init__(self, iface):
        """Constructor."""
        super(QGISRedResultsDock, self).__init__(iface.mainWindow())
        self.iface = iface
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.btCompute.clicked.connect(self.compute)
        self.btShow.clicked.connect(self.showResults)
        self.rbVariables.toggled.connect(self.radioButtonsChanged)
        self.rbTimes.toggled.connect(self.radioButtonsChanged)

    def config(self, direct, netw):
        #self.ProcessDone = False
        if not (self.NetworkName == netw and self.ProjectDirectory == direct):
            self.Results={}
            self.tbScenario.setText("Base")
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)

    def radioButtonsChanged(self, enabled):
        self.gbVariables.setEnabled(self.rbVariables.isChecked())
        self.gbTimes.setEnabled(self.rbTimes.isChecked())

    def isCurrentProject(self):
        currentNetwork =""
        currentDirectory = ""
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            layerUri= layer.dataProvider().dataSourceUri().split("|")[0]
            self.CRS = layer.crs()
            for layerName in self.ownMainLayers:
                if "_" + layerName in layerUri:
                    currentDirectory = os.path.dirname(layerUri)
                    vectName = os.path.splitext(os.path.basename(layerUri))[0].split("_")
                    name =""
                    for part in vectName:
                        if part in self.ownMainLayers:
                            break
                        name = name + part + "_"
                    name = name.strip("_")
                    currentNetwork = name
                    if self.NetworkName == currentNetwork and self.ProjectDirectory == currentDirectory:
                        return True
                    else:
                        self.iface.messageBar().pushMessage("Warning", "The current project has been changed. Please, try again.", level=1, duration=10)
                        self.close()
                        return False

        self.iface.messageBar().pushMessage("Warning", "The current project has been changed. Please, try again.", level=1, duration=10)
        self.close()
        return False

    def openRemoveResults(self, scenario, open):
        list = []
        resultPath= os.path.join(self.ProjectDirectory, "Results")
        
        if self.rbVariables.isChecked():
            if self.cbFlow.isChecked():
                list.append("Link_" + "Flow")
            if self.cbVelocity.isChecked():
                list.append("Link_" + "Velocity")
            if self.cbHeadLoss.isChecked():
                list.append("Link_" + "HeadLoss")
            if self.cbPressure.isChecked():
                list.append("Node_" + "Pressure")
            if self.cbHead.isChecked():
                list.append("Node_" + "Head")
        else:
            list.append("Node_" + self.cbTimes.currentText())
            list.append("Link_" + self.cbTimes.currentText())
        
        utils = QGISRedUtils(resultPath, self.NetworkName +"_" + scenario, self.iface)
        if open:
            group = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName +" " + scenario + " Results")
            if group is None:
                root = QgsProject.instance().layerTreeRoot()
                group = root.insertGroup(0,self.NetworkName +" " + scenario + " Results")
            for file in list:
                utils.openLayer(self.CRS, group, file)
        else:
            utils.removeLayers(list)

    def setVariablesTimes(self):
        self.Variables=""
        self.TimeIndex=""
        if self.rbVariables.isChecked():
            if self.cbFlow.isChecked():
                self.Variables=self.Variables + "Flow_Link;"
            if self.cbVelocity.isChecked():
                self.Variables=self.Variables + "Velocity_Link;"
            if self.cbHeadLoss.isChecked():
                self.Variables=self.Variables + "HeadLoss_Link;"
            if self.cbPressure.isChecked():
                self.Variables=self.Variables + "Pressure_Node;"
            if self.cbHead.isChecked():
                self.Variables=self.Variables + "Head_Node;"
            if self.Variables=="":
                self.iface.messageBar().pushMessage("Validations", "No variable results selected", level=1)
                return False
        else:
            #ver el indice del combobox
            self.TimeIndex = str(self.cbTimes.currentIndex())
            if self.TimeIndex=="" or self.TimeIndex == "-1":
                self.iface.messageBar().pushMessage("Validations", "No time results selected", level=1)
                return False
            self.Time = self.cbTimes.currentText()
        return True

    def compute(self):
        if not self.isCurrentProject():
            return
        
        scenario = self.tbScenario.text()
        if len(scenario)==0:
            self.iface.messageBar().pushMessage("Validations", "The scenario name is not valid", level=1)
            return False
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Compute.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), scenario.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()

        if b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        elif b.startswith("Message"):
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
        else:
            list = b.split(';')
            self.Results[scenario]= list[0]
            del list[0]
            self.cbTimes.clear()
            self.cbTimes.addItems(list)
            self.showResults()

    def showResults(self):
        if not self.isCurrentProject():
            return

        scenario = self.tbScenario.text()
        resultPath = self.Results.get(scenario)
        if resultPath is None:
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=10)
            return

        if not self.setVariablesTimes():
            return

        self.openRemoveResults(scenario, False)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateResults.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateResults.restype = c_char_p
        b = mydll.CreateResults(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), scenario.encode('utf-8'), resultPath.encode('utf-8'), self.Variables.encode('utf-8'), self.TimeIndex.encode('utf-8'), self.Time.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b

        self.openRemoveResults(scenario, True)
        QApplication.restoreOverrideCursor()
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)