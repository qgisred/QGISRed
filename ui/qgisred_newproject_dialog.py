# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedNewProjectDialog
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
    from qgis.core import Qgis, QgsTask, QgsApplication
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QFileDialog, QDialog, QApplication
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, Qt
    from ..qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from qgis.gui import QgsGenericProjectionSelector
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QTableWidgetItem, QFileDialog, QDialog, QApplication
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, Qt
    from qgis.core import QgsMapLayerRegistry, QGis as Qgis
    from ..qgisred_utils import QGISRedUtils

import os
from ctypes import*
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_newproject_dialog.ui'))

class QGISRedNewProjectDialog(QDialog, FORM_CLASS):
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    CRS= None
    ProcessDone= False
    gplFile=""
    TemporalFolder = "Temporal folder"
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedNewProjectDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.btCreateProject.clicked.connect(self.createProject)
        self.btEditProject.clicked.connect(self.editProject)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btSelectCRS.clicked.connect(self.selectCRS)
        #Variables:
        self.gplFile = os.path.join(os.path.dirname(os.path.dirname(__file__)) , "qgisredprojectlist.gpl")
        
    def config(self, ifac, direct, netw):
        self.iface=ifac
        try: #QGis 3.x
            self.CRS = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            self.CRS = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if self.CRS.srsid()==0:
            self.CRS = QgsCoordinateReferenceSystem()
            self.CRS.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        self.tbCRS.setText(self.CRS.description())
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)
        newProject = self.ProjectDirectory==self.TemporalFolder
        self.btSelectDirectory.setVisible(newProject)
        self.btCreateProject.setVisible(newProject)
        self.btEditProject.setVisible(not newProject)
        self.tbNetworkName.setReadOnly(not newProject)
        if not newProject:
            self.setProperties()
        
    def setProperties(self):
        if self.btCreateProject.isVisible():
            self.setDefaultElements()
        else:
            dirList = os.listdir(self.ProjectDirectory)
            self.cbPipes.setChecked(self.NetworkName + "_Pipes.shp" in dirList)
            self.cbJunctions.setChecked(self.NetworkName + "_Junctions.shp" in dirList)
            self.cbTanks.setChecked(self.NetworkName + "_Tanks.shp" in dirList)
            self.cbReservoirs.setChecked(self.NetworkName + "_Reservoirs.shp" in dirList)
            self.cbValves.setChecked(self.NetworkName + "_Valves.shp" in dirList)
            self.cbPumps.setChecked(self.NetworkName + "_Pumps.shp" in dirList)
            self.cbPipes.setEnabled(not self.NetworkName + "_Pipes.shp" in dirList)
            self.cbJunctions.setEnabled(not self.NetworkName + "_Junctions.shp" in dirList)
            self.cbTanks.setEnabled(not self.NetworkName + "_Tanks.shp" in dirList)
            self.cbReservoirs.setEnabled(not self.NetworkName + "_Reservoirs.shp" in dirList)
            self.cbValves.setEnabled(not self.NetworkName + "_Valves.shp" in dirList)
            self.cbPumps.setEnabled(not self.NetworkName + "_Pumps.shp" in dirList)
            #resto
            self.cbIsolatedValves.setChecked(self.NetworkName + "_IssolatedValves.shp" in dirList)
            self.cbCeckValves.setChecked(self.NetworkName + "_CheckValves.shp" in dirList)
            self.cbHydrants.setChecked(self.NetworkName + "_Hydrants.shp" in dirList)
            self.cbPurgeValves.setChecked(self.NetworkName + "_PurgeValves.shp" in dirList)
            self.cbAirReleases.setChecked(self.NetworkName + "_AirReleases.shp" in dirList)
            self.cbConnections.setChecked(self.NetworkName + "_Connections.shp" in dirList)
            self.cbManometers.setChecked(self.NetworkName + "_Manometers.shp" in dirList)
            self.cbFlowmeters.setChecked(self.NetworkName + "_Flowmeters.shp" in dirList)
            self.cbCountmeters.setChecked(self.NetworkName + "_Countmeters.shp" in dirList)
            self.cbLevelmeters.setChecked(self.NetworkName + "_Levelmeters.shp" in dirList)

    def setDefaultElements(self):
        self.cbPipes.setChecked(True)
        self.cbJunctions.setChecked(True)
        self.cbTanks.setChecked(True)
        self.cbReservoirs.setChecked(True)
        self.cbValves.setChecked(True)
        self.cbPumps.setChecked(True)
        
        self.cbIsolatedValves.setChecked(False)
        self.cbCeckValves.setChecked(False)
        self.cbHydrants.setChecked(False)
        self.cbPurgeValves.setChecked(False)
        self.cbAirReleases.setChecked(False)
        self.cbConnections.setChecked(False)
        self.cbManometers.setChecked(False)
        self.cbFlowmeters.setChecked(False)
        self.cbCountmeters.setChecked(False)
        self.cbLevelmeters.setChecked(False)
    
    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory
            self.NetworkName = self.tbNetworkName.text()
            self.setProperties()
        
    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_():
            try: #QGis 3.x
                crsId = projSelector.crs().srsid()
            except: #QGis 2.x
                crsId = projSelector.selectedCrsId()
            if not crsId==0:
                self.CRS = QgsCoordinateReferenceSystem()
                self.CRS.createFromId(crsId, QgsCoordinateReferenceSystem.InternalCrsId)
                self.tbCRS.setText(self.CRS.description())

    def validationsCreateProject(self):
        self.NetworkName = self.tbNetworkName.text()
        if len(self.NetworkName)==0:
            self.iface.messageBar().pushMessage("Validations", "The network's name is not valid", level=1)
            return False
        self.ProjectDirectory = self.tbProjectDirectory.text()
        if len(self.ProjectDirectory)==0 or self.ProjectDirectory==self.TemporalFolder:
            self.ProjectDirectory=tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names())
        else:
            if not os.path.exists(self.ProjectDirectory):
                self.iface.messageBar().pushMessage("Validations", "The project directory does not exist", level=1)
                return False
            else:
                dirList = os.listdir(self.ProjectDirectory)
                layers = ["Pipes", "Junctions", "Tanks", "Reservoirs", "Valves", "Pumps", "IssolatedValves", "CheckValves" ,"Hydrants", "PurgeValves", "AirReleases", "Connections", "Manometers", "Flowmeters", "Countmeters", "Levelmeters"]
                for layer in layers:
                    if self.NetworkName + "_" + layer + ".shp" in dirList:
                        self.iface.messageBar().pushMessage("Validations", "The project directory has some file to selected network's name", level=1)
                        return False
        return True

    def createElementsList(self):
        list =""
        if self.cbPipes.isEnabled() and self.cbPipes.isChecked():
            list = list + "pipe" + ";"
        if self.cbJunctions.isEnabled() and self.cbJunctions.isChecked():
            list = list + "junction" + ";"
        if self.cbTanks.isEnabled() and self.cbTanks.isChecked():
            list = list + "tank" + ";"
        if self.cbReservoirs.isEnabled() and self.cbReservoirs.isChecked():
            list = list + "reservoir" + ";"
        if self.cbValves.isEnabled() and self.cbValves.isChecked():
            list = list + "valve" + ";"
        if self.cbPumps.isEnabled() and self.cbPumps.isChecked():
            list = list + "pump" + ";"
        return list

    def createComplementaryList(self):
        list = ""
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.cbIsolatedValves.isChecked() and not utils.isLayerOpened("IssolatedValves"):
            list = list + "issolatedvalve" + ";"
        if self.cbCeckValves.isChecked() and not utils.isLayerOpened("CheckValves"):
            list = list + "checkvalve"+ ";"
        if self.cbHydrants.isChecked() and not utils.isLayerOpened("Hydrants"):
            list = list + "hydrant"+ ";"
        if self.cbPurgeValves.isChecked() and not utils.isLayerOpened("PurgeValves"):
            list = list + "purgevalve"+ ";"
        if self.cbAirReleases.isChecked() and not utils.isLayerOpened("AirReleases"):
            list = list + "airrelease"+ ";"
        if self.cbConnections.isChecked() and not utils.isLayerOpened("Connections"):
            list = list + "connection"+ ";"
        if self.cbManometers.isChecked() and not utils.isLayerOpened("Manometers"):
            list = list + "manometer"+ ";"
        if self.cbFlowmeters.isChecked() and not utils.isLayerOpened("Flowmeters"):
            list = list + "flowmeter"+ ";"
        if self.cbCountmeters.isChecked() and not utils.isLayerOpened("Countmeters"):
            list = list + "countmeter"+ ";"
        if self.cbLevelmeters.isChecked() and not utils.isLayerOpened("Levelmeters"):
            list = list + "levelmeter"+ ";"
        return list

    def removeComplementaryLayers(self, task, wait_time):
        list = []
        if not self.cbIsolatedValves.isChecked():
            list.append("IssolatedValves")
        if not self.cbCeckValves.isChecked():
            list.append("CheckValves")
        if not self.cbHydrants.isChecked():
            list.append("Hydrants")
        if not self.cbPurgeValves.isChecked():
            list.append("PurgeValves")
        if not self.cbAirReleases.isChecked():
            list.append("AirReleases")
        if not self.cbConnections.isChecked():
            list.append("Connections")
        if not self.cbManometers.isChecked():
            list.append("Manometers")
        if not self.cbFlowmeters.isChecked():
            list.append("Flowmeters")
        if not self.cbCountmeters.isChecked():
            list.append("Countmeters")
        if not self.cbLevelmeters.isChecked():
            list.append("Levelmeters")
        
        QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface).removeLayers(list)
        raise Exception('')

    def openElementsLayers(self, group, new):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if new:
            files = ["Curves", "Controls", "Patterns", "Rules", "Options", "DefaultValues"]
            for file in files:
                utils.openLayer(self.CRS, group, file, ext=".dbf")

        if self.cbPipes.isChecked():
            if not utils.isLayerOpened("Pipes"):
                utils.openLayer(self.CRS, group,"Pipes")
        if self.cbValves.isChecked():
            if not utils.isLayerOpened("Valves"):
                utils.openLayer(self.CRS, group,"Valves")
        if self.cbPumps.isChecked():
            if not utils.isLayerOpened("Pumps"):
                utils.openLayer(self.CRS, group,"Pumps")
        if self.cbJunctions.isChecked():
            if not utils.isLayerOpened("Junctions"):
                utils.openLayer(self.CRS, group,"Junctions")
        if self.cbTanks.isChecked():
            if not utils.isLayerOpened("Tanks"):
                utils.openLayer(self.CRS, group,"Tanks")
        if self.cbReservoirs.isChecked():
            if not utils.isLayerOpened("Reservoirs"):
                utils.openLayer(self.CRS, group,"Reservoirs")

    def openComplementaryLayers(self, group):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.cbIsolatedValves.isChecked():
            if not utils.isLayerOpened("IssolatedValves"):
                utils.openLayer(self.CRS, group,"IssolatedValves")
        if self.cbCeckValves.isChecked():
            if not utils.isLayerOpened("CheckValves"):
                utils.openLayer(self.CRS, group,"CheckValves")
        if self.cbHydrants.isChecked():
            if not utils.isLayerOpened("Hydrants"):
                utils.openLayer(self.CRS, group,"Hydrants")
        if self.cbPurgeValves.isChecked():
            if not utils.isLayerOpened("PurgeValves"):
                utils.openLayer(self.CRS, group,"PurgeValves")
        if self.cbAirReleases.isChecked():
            if not utils.isLayerOpened("AirReleases"):
                utils.openLayer(self.CRS, group,"AirReleases")
        if self.cbConnections.isChecked():
            if not utils.isLayerOpened("Connections"):
                utils.openLayer(self.CRS, group,"Connections")
        if self.cbManometers.isChecked():
            if not utils.isLayerOpened("Manometers"):
                utils.openLayer(self.CRS, group,"Manometers")
        if self.cbFlowmeters.isChecked():
            if not utils.isLayerOpened("Flowmeters"):
                utils.openLayer(self.CRS, group,"Flowmeters")
        if self.cbCountmeters.isChecked():
            if not utils.isLayerOpened("Countmeters"):
                utils.openLayer(self.CRS, group,"Countmeters")
        if self.cbLevelmeters.isChecked():
            if not utils.isLayerOpened("Levelmeters"):
                utils.openLayer(self.CRS, group,"Levelmeters")

    def createProject(self):
        isValid = self.validationsCreateProject()
        if isValid==True:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
            complElements = self.createComplementaryList()

            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.CreateProject.argtypes = (c_char_p, c_char_p, c_char_p)
            mydll.CreateProject.restype = c_char_p
            b = mydll.CreateProject(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), complElements.encode('utf-8'))
            try: #QGis 3.x
                b= "".join(map(chr, b)) #bytes to string
            except:  #QGis 2.x
                b=b
            self.iface.mapCanvas().setDestinationCrs(self.CRS)
            
            root = QgsProject.instance().layerTreeRoot()
            group = root.addGroup(self.NetworkName + " Inputs")

            self.openElementsLayers(group, True)
            self.openComplementaryLayers(group)
            
            QApplication.restoreOverrideCursor()
            
            if b=="True":
                self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
                file = open(self.gplFile, "a+")
                QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + '\n')
                file.close()
            elif b=="False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
            else:
                self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
            
            self.close()
            self.ProcessDone = True

    def editProject(self):
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeComplementaryLayers(None,0)
            except:
                pass
            self.editProjectProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(u'Remove layers', self.removeComplementaryLayers, on_finished=self.editProjectProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def editProjectProcess(self, exception=None, result=None):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        
        complElements = self.createComplementaryList()
        elements = self.createElementsList()
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditProject.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditProject.restype = c_char_p
        b = mydll.EditProject(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'), complElements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b

        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName +" Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        if dataGroup is not None:
            for treeLayer in dataGroup.findLayers():
                treeLayer.layer().setCrs(self.CRS)
        self.openElementsLayers(dataGroup, False)
        self.openComplementaryLayers(dataGroup)
        
        QApplication.restoreOverrideCursor()
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
        
        self.close()
        self.ProcessDone = True