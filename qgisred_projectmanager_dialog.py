# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedProjectManagerDialog
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
    from qgis.gui import QgsProjectionSelectionTreeWidget
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QFileDialog, QDialog
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
    # Import the code for the dialog
    from .qgisred_newproject_dialog import QGISRedNewProjectDialog
    from .qgisred_importproject_dialog import QGISRedImportProjectDialog
    from .qgisred_cloneproject_dialog import QGISRedCloneProjectDialog
    from .qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from qgis.gui import QgsGenericProjectionSelector
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QTableWidgetItem, QFileDialog, QDialog
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
    from qgis.core import QgsMapLayerRegistry
    # Import the code for the dialog
    from qgisred_newproject_dialog import QGISRedNewProjectDialog
    from qgisred_importproject_dialog import QGISRedImportProjectDialog
    from qgisred_cloneproject_dialog import QGISRedCloneProjectDialog
    from qgisred_utils import QGISRedUtils

import os
import datetime
from time import strftime
from shutil import copyfile



FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_projectmanager_dialog.ui'))

class QGISRedProjectManagerDialog(QDialog, FORM_CLASS):
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone= False
    gplFile=""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    #Create complementary layers
    layerExtensions = [".shp", ".dbf", ".shx", ".prj", ".qpj"]
    ownFiles = ["Curves.csv", "Controls.csv", "Patterns.csv", "Rules.csv", "Options.csv", "PropertyValues.csv", "TitleAndNotes.txt" ]
    
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedProjectManagerDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.btCreate.clicked.connect(self.createProject)
        self.btDelete.clicked.connect(self.deleteProject)
        self.btImport.clicked.connect(self.importProject)
        self.btOpen.clicked.connect(self.openProject)
        self.btClone.clicked.connect(self.cloneProject)
        self.btGo2Folder.clicked.connect(self.openFolder)
        #Variables:
        self.gplFile = os.path.dirname(__file__) + "\\qgisredprojectlist.gpl"
        #Columns:
        self.twProjectList.setColumnCount(4)
        item = QTableWidgetItem("Network's Name")
        self.twProjectList.setHorizontalHeaderItem(0,item)
        item = QTableWidgetItem("Last update")
        self.twProjectList.setHorizontalHeaderItem(1,item)
        item = QTableWidgetItem("Creation date")
        self.twProjectList.setHorizontalHeaderItem(2,item)
        item = QTableWidgetItem("Folder")
        self.twProjectList.setHorizontalHeaderItem(3,item)
        #Rows:
        self.fillTable()

    def config(self, ifac, direct, netw):
        self.iface=ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct

        for row in range(0,self.twProjectList.rowCount()):
            if self.ProjectDirectory.replace("/","\\") == str(self.twProjectList.item(row,3).text()) and self.NetworkName == str(self.twProjectList.item(row,0).text()):
                self.twProjectList.setCurrentCell(row, 1)
                break

    def fillTable(self):
        self.twProjectList.setRowCount(0)
        if not os.path.exists(self.gplFile):
            f1 = open(self.gplFile, "w+")
            f1.close()
        validLines= []
        f = open(self.gplFile, "r")
        
        notDuplicateLines = []
        seen = set()
        for value in f:
            if value not in seen:
                notDuplicateLines.append(value)
                seen.add(value)
        
        for x in notDuplicateLines:
            values = x.split(";")
            if len(values) == 2:
                values[1] = values[1].rstrip("\r\n")
                pp = os.path.realpath(os.path.join(values[1], values[0] + ".gqp"))
                if os.path.exists(pp):
                    validLines.append(x)
                    f2= open (pp, "r")
                    lines = f2.readlines()
                    if len(lines)>= 2:
                        rowPosition = self.twProjectList.rowCount()
                        self.twProjectList.insertRow(rowPosition)
                        self.twProjectList.setItem(rowPosition , 0, QTableWidgetItem(values[0]))
                        self.twProjectList.setItem(rowPosition , 1, QTableWidgetItem(lines[1]))
                        self.twProjectList.setItem(rowPosition , 2, QTableWidgetItem(lines[0]))
                        self.twProjectList.setItem(rowPosition , 3, QTableWidgetItem(values[1]))
        f.close()
        f = open(self.gplFile, "w")
        for x in validLines:
            QGISRedUtils().writeFile(f, x)
        f.close()

    def addProjectToTable(self, file, folder, net):
        valid = True
        if not file=="":
            folder= os.path.dirname(file)
            net = os.path.splitext(os.path.basename(file))[0]
        else:
            valid=False
            dirList = os.listdir(folder)
            for layerName in self.ownMainLayers:
                valid = valid or net + "_" + layerName + ".shp" in dirList
            if valid:
                self.createGqpFile(net,folder)
        if valid:
            file = open(self.gplFile, "a+")
            QGISRedUtils().writeFile(file, net + ";" + folder.replace("/","\\") + "\n")
            file.close()
            self.fillTable()

    def createGqpFile(self, net, folder):
        f = open(os.path.join(folder, net + ".gqp"), "w+")
        f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        QGISRedUtils().writeFile(f, "[" + net + " Inputs]\n")
        dirList = os.listdir(folder)
        for fileName in self.ownFiles:
            if ".csv" in fileName:
                if net + "_" + fileName in dirList:
                    QGISRedUtils().writeFile(f, os.path.join(folder, net + "_" + fileName) + '\n')
        for layerName in self.ownMainLayers:
            if net + "_" + layerName + ".shp" in dirList:
                QGISRedUtils().writeFile(f, os.path.join(folder, net + "_" + layerName + ".shp") + '\n')
        f.close()

    def isOpenedProject(self):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if layer.isEditable():
                self.iface.messageBar().pushMessage("Warning", "Some layer is in Edit Mode. Plase, commit it before continuing.", level=1)
                return False
        qgsFilename =QgsProject.instance().fileName()
        if not qgsFilename=="":
            if QgsProject.instance().isDirty():
                #Guardar y continuar
                self.iface.messageBar().pushMessage("Warning", "The project has changes. Please save them before continuing.", level=1)
                return False
            else:
                #Cerrar proyecto y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened project', 'Do you want to close the current project and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers())>0:
                #Cerrar archivos y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened layers', 'Do you want to close the current layers and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def createProject(self):
        valid = self.isOpenedProject()
        if valid:
            dlg = GISRedNewProjectDialog()
            dlg.config(self.iface, "Temporal folder", "Network")
            # Run the dialog event loop
            self.close()
            dlg.exec_()
            result = dlg.ProcessDone
            # See if OK was pressed
            if result:
                self.ProjectDirectory = dlg.ProjectDirectory
                self.NetworkName = dlg.NetworkName
                self.ProcessDone = True

    def deleteProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                if self.ProjectDirectory.replace("/","\\") == str(self.twProjectList.item(row.row(),3).text()) and self.NetworkName == str(self.twProjectList.item(row.row(),0).text()):
                    self.iface.messageBar().pushMessage("Warning", "Current project can not be deleted.", level=1)
                    return
                if os.path.exists(self.gplFile):
                    f = open(self.gplFile, "r")
                    lines = f.readlines()
                    f.close()
                    f = open(self.gplFile, "w")
                    i=0
                    for line in lines:
                        if not i==row.row():
                            QGISRedUtils().writeFile(f, line)
                        i=i+1
                    f.close()
            self.fillTable()

    def importProject(self):
        dlg = GISRedImportProjectDialog()
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        # See if OK was pressed
        if result:
            path=""
            name=""
            valid = True
            if dlg.IsFile:
                self.addProjectToTable(dlg.File, "", "")
            else:
                self.addProjectToTable("", dlg.ProjectDirectory, dlg.NetworkName)

    def openProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            valid = self.isOpenedProject()
            if valid:
                for row in selectionModel.selectedRows():
                    rowIndex = row.row()
                    network = str(self.twProjectList.item(rowIndex, 0).text())
                    gqpFilename = os.path.join(str(self.twProjectList.item(rowIndex, 3).text()), network + ".gqp")
                    if os.path.exists(gqpFilename):
                        f = open(gqpFilename, "r")
                        lines = f.readlines()
                        qgsFile = lines[2]
                        if ".qgs" in qgsFile or ".qgz" in qgsFile:
                            finfo = QFileInfo(qgsFile)
                            try: #QGis 3.x
                                QgsProject.instance().read(finfo.filePath())
                            except: #QGis 2.x
                                QgsProject.instance().read(finfo)
                        else:
                            group = None
                            for i in range(2, len(lines)):
                                if "[" in lines[i]:
                                    dataGroup = str(lines[i].strip("[").strip("\r\n").strip("]"))
                                    root = QgsProject.instance().layerTreeRoot()
                                    group = root.addGroup(dataGroup)
                                else:
                                    layerPath= lines[i].strip("\r\n")
                                    vlayer = None
                                    layerName = os.path.splitext(os.path.basename(layerPath))[0].replace(network + "_", "")
                                    if group is None:
                                        vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
                                    else:
                                        vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                                        try: #QGis 3.x
                                            QgsProject.instance().addMapLayer(vlayer, False)
                                        except: #QGis 2.x
                                            QgsMapLayerRegistry.instance().addMapLayer(vlayer, False)
                                        group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
                                    if not vlayer is None:
                                        if ".shp" in layerPath:
                                            type = "point"
                                            if "Valves" in layerPath or "Pumps" in layerPath:
                                                type= "line"
                                            names = (os.path.splitext(os.path.basename(layerPath))[0]).split("_")
                                            style = names[len(names)-1]
                                            QGISRedUtils().setStyle(vlayer, style, type)
                    else:
                        self.iface.messageBar().pushMessage("Warning", "File not found", level=1)
                    break
                self.close()
        else:
            self.iface.messageBar().pushMessage("Warning", "You need to select a valid project to open it.", level=1)

    def cloneProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainName= str(self.twProjectList.item(row.row(), 0).text())
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                dlg = GISRedCloneProjectDialog()
                # Run the dialog event loop
                dlg.exec_()
                result = dlg.ProcessDone
                # See if OK was pressed
                if result:
                    if mainName == dlg.NetworkName:
                        self.iface.messageBar().pushMessage("Warning", "Selected project has the same Network's Name. Plase, set another name.", level=1)
                    else:
                        for layerName in self.ownMainLayers:
                            layerPath = os.path.join(mainFolder, mainName + "_" + layerName)
                            #Extensions
                            for ext in self.layerExtensions:
                                if os.path.exists(layerPath + ext):
                                    copyfile(layerPath + ext, os.path.join(dlg.ProjectDirectory, dlg.NetworkName + "_" + layerName + ext))
                        for fileName in self.ownFiles:
                            filePath = os.path.join(mainFolder, mainName + "_" + fileName)
                            if os.path.exists(filePath):
                                    copyfile(filePath, os.path.join(dlg.ProjectDirectory, dlg.NetworkName + "_" + fileName))

                        self.addProjectToTable("", dlg.ProjectDirectory, dlg.NetworkName)
                break
        else:
            self.iface.messageBar().pushMessage("Warning", "There is no a selected project to clone.", level=1)

    def openFolder(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                os.startfile(mainFolder)