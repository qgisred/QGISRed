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
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QFileDialog, QDialog
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
    from .qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from qgis.gui import QgsGenericProjectionSelector
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QTableWidgetItem, QFileDialog, QDialog
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
    from qgis.core import QgsMapLayerRegistry
    from qgisred_utils import QGISRedUtils

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
        self.gplFile = os.path.dirname(__file__) + "\\qgisredprojectlist.gpl"
        
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
        if self.cbIsolatedValves.isChecked() and not self.isLayerOpened("IssolatedValves"):
            list = list + "issolatedvalve" + ";"
        if self.cbCeckValves.isChecked() and not self.isLayerOpened("CheckValves"):
            list = list + "checkvalve"+ ";"
        if self.cbHydrants.isChecked() and not self.isLayerOpened("Hydrants"):
            list = list + "hydrant"+ ";"
        if self.cbPurgeValves.isChecked() and not self.isLayerOpened("PurgeValves"):
            list = list + "purgevalve"+ ";"
        if self.cbAirReleases.isChecked() and not self.isLayerOpened("AirReleases"):
            list = list + "airrelease"+ ";"
        if self.cbConnections.isChecked() and not self.isLayerOpened("Connections"):
            list = list + "connection"+ ";"
        if self.cbManometers.isChecked() and not self.isLayerOpened("Manometers"):
            list = list + "manometer"+ ";"
        if self.cbFlowmeters.isChecked() and not self.isLayerOpened("Flowmeters"):
            list = list + "flowmeter"+ ";"
        if self.cbCountmeters.isChecked() and not self.isLayerOpened("Countmeters"):
            list = list + "countmeter"+ ";"
        if self.cbLevelmeters.isChecked() and not self.isLayerOpened("Levelmeters"):
            list = list + "levelmeter"+ ";"
        return list

    def removeComplementaryLayers(self):
        if not self.cbIsolatedValves.isChecked():
            self.removeLayer("IssolatedValves")
        if not self.cbCeckValves.isChecked():
            self.removeLayer("CheckValves")
        if not self.cbHydrants.isChecked():
            self.removeLayer("Hydrants")
        if not self.cbPurgeValves.isChecked():
            self.removeLayer("PurgeValves")
        if not self.cbAirReleases.isChecked():
            self.removeLayer("AirReleases")
        if not self.cbConnections.isChecked():
            self.removeLayer("Connections")
        if not self.cbManometers.isChecked():
            self.removeLayer("Manometers")
        if not self.cbFlowmeters.isChecked():
            self.removeLayer("Flowmeters")
        if not self.cbCountmeters.isChecked():
            self.removeLayer("Countmeters")
        if not self.cbLevelmeters.isChecked():
            self.removeLayer("Levelmeters")
        return list

    def removeLayer(self, id):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0])== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + id + ".shp"):
                try: #QGis 3.x
                    QgsProject.instance().removeMapLayers([layer.id()])
                except: #QGis 2.x
                    QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])

    def openElementsLayers(self, group, new):
        if new:
            self.openLayer(group, "Curves", "csv")
            self.openLayer(group, "Controls", "csv")
            self.openLayer(group, "Patterns", "csv")
            self.openLayer(group, "Rules", "csv")
            self.openLayer(group, "Options", "csv")
            self.openLayer(group, "PropertyValues", "csv")
        
        if self.cbPipes.isChecked():
            if not self.isLayerOpened("Pipes"):
                self.openLayer(group,"Pipes", style="pipes", type="line")
        if self.cbValves.isChecked():
            if not self.isLayerOpened("Valves"):
                self.openLayer(group,"Valves", style="valves", type="line")
        if self.cbPumps.isChecked():
            if not self.isLayerOpened("Pumps"):
                self.openLayer(group,"Pumps", style="pumps", type="line")
        if self.cbJunctions.isChecked():
            if not self.isLayerOpened("Junctions"):
                self.openLayer(group,"Junctions", style="junctions")
        if self.cbTanks.isChecked():
            if not self.isLayerOpened("Tanks"):
                self.openLayer(group,"Tanks", style="tanks")
        if self.cbReservoirs.isChecked():
            if not self.isLayerOpened("Reservoirs"):
                self.openLayer(group,"Reservoirs", style="reservoirs")
        
        self.iface.mapCanvas().refresh()

    def openComplementaryLayers(self, group):
        if self.cbIsolatedValves.isChecked():
            if not self.isLayerOpened("IssolatedValves"):
                self.openLayer(group,"IssolatedValves")
        if self.cbCeckValves.isChecked():
            if not self.isLayerOpened("CheckValves"):
                self.openLayer(group,"CheckValves")
        if self.cbHydrants.isChecked():
            if not self.isLayerOpened("Hydrants"):
                self.openLayer(group,"Hydrants")
        if self.cbPurgeValves.isChecked():
            if not self.isLayerOpened("PurgeValves"):
                self.openLayer(group,"PurgeValves")
        if self.cbAirReleases.isChecked():
            if not self.isLayerOpened("AirReleases"):
                self.openLayer(group,"AirReleases")
        if self.cbConnections.isChecked():
            if not self.isLayerOpened("Connections"):
                self.openLayer(group,"Connections")
        if self.cbManometers.isChecked():
            if not self.isLayerOpened("Manometers"):
                self.openLayer(group,"Manometers")
        if self.cbFlowmeters.isChecked():
            if not self.isLayerOpened("Flowmeters"):
                self.openLayer(group,"Flowmeters")
        if self.cbCountmeters.isChecked():
            if not self.isLayerOpened("Countmeters"):
                self.openLayer(group,"Countmeters")
        if self.cbLevelmeters.isChecked():
            if not self.isLayerOpened("Levelmeters"):
                self.openLayer(group,"Levelmeters")

    def isLayerOpened(self, name):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory.replace("/","\\"), self.NetworkName + "_" + name + ".shp"):
                return True
        return False

    def openLayer(self, group, name, ext="shp", style="", type="point"):
        layerName = self.NetworkName + "_" + name
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + "." + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + "." + ext), name, "ogr")
            if not ext == "csv":
                vlayer.setCrs(self.CRS)
                if not style=="":
                    QGISRedUtils().setStyle(vlayer, style, type)
            try: #QGis 3.x
                QgsProject.instance().addMapLayer(vlayer, group is None)
            except: #QGis 2.x
                QgsMapLayerRegistry.instance().addMapLayer(vlayer, group is None)
            group.insertChildNode(0, QgsLayerTreeLayer(vlayer))

    def createProject(self):
        isValid = self.validationsCreateProject()
        if isValid==True:
            os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
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
            
            if b=="True":
                self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
                file = open(self.gplFile, "a+")
                QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + '\n')
                file.close()
            elif b=="False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
            else:
                self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
            
            os.startfile(self.ProjectDirectory)
            self.close()
            self.ProcessDone = True

    def editProject(self):
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        self.removeComplementaryLayers()
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
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
        
        os.startfile(self.ProjectDirectory)
        self.close()
        self.ProcessDone = True