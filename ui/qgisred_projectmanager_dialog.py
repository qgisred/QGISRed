# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidgetItem, QDialog
from PyQt5.QtCore import QFileInfo
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer
from qgis.PyQt import uic
from qgis.core import QgsTask, QgsApplication
# Import the code for the dialog
from .qgisred_createproject_dialog import QGISRedCreateProjectDialog
from .qgisred_import_dialog import QGISRedImportDialog
from .qgisred_importproject_dialog import QGISRedImportProjectDialog
from .qgisred_cloneproject_dialog import QGISRedCloneProjectDialog
from ..tools.qgisred_utils import QGISRedUtils

import os
from shutil import copyfile
from xml.etree import ElementTree

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_projectmanager_dialog.ui'))


class QGISRedProjectManagerDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False
    gplFile = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    layerExtensions = [".shp", ".dbf", ".shx", ".prj", ".qpj"]
    ownFiles = ["DefaultValues.dbf", "Options.dbf", "Rules.dbf", "Controls.dbf",
                "Curves.dbf", "Patterns.dbf", "TitleAndNotes.txt"]

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedProjectManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.btCreate.clicked.connect(self.createProject)
        self.btImport.clicked.connect(self.importData)
        self.btOpen.clicked.connect(self.openProject)
        self.btClone.clicked.connect(self.cloneProject)

        self.btLoad.clicked.connect(self.loadProject)
        self.btUnLoad.clicked.connect(self.unloadProject)
        self.btGo2Folder.clicked.connect(self.openFolder)
        # Variables:
        gplFolder = os.path.join(os.getenv('APPDATA'), "QGISRed")
        try:  # create directory if does not exist
            os.stat(gplFolder)
        except Exception:
            os.mkdir(gplFolder)
        self.gplFile = os.path.join(gplFolder, "qgisredprojectlist.gpl")
        # Columns:
        self.twProjectList.setColumnCount(4)
        item = QTableWidgetItem("Network's Name")
        self.twProjectList.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem("Last update")
        self.twProjectList.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem("Creation date")
        self.twProjectList.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem("Folder")
        self.twProjectList.setHorizontalHeaderItem(3, item)
        # Rows:
        self.fillTable()
        self.twProjectList.cellDoubleClicked.connect(self.openProject)

    """Methods"""
    def config(self, ifac, direct, netw, parent):
        self.parent = parent
        self.iface = ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct

        for row in range(0, self.twProjectList.rowCount()):
            isSameProject = self.getUniformedPath(self.ProjectDirectory) == str(self.twProjectList.item(row, 3).text())
            isSameNet = self.NetworkName == str(self.twProjectList.item(row, 0).text())
            if isSameProject and isSameNet:
                self.twProjectList.setCurrentCell(row, 1)
                break

    def fillTable(self):
        self.twProjectList.setRowCount(0)
        if not os.path.exists(self.gplFile):
            f1 = open(self.gplFile, "w+")
            f1.close()
        validLines = []
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

                dateLast = None
                dateCreate = None

                pp = os.path.realpath(os.path.join(values[1], values[0] + "_Metadata.txt"))
                if os.path.exists(pp):
                    validLines.append(x)
                    data = ""
                    with open(pp, 'r', encoding="latin-1") as content_file:
                        data = content_file.read()
                    # Parse data as XML
                    root = ElementTree.fromstring(data)
                    # Get data from nodes
                    for dl in root.iter('DateModification'):
                        dateLast = dl.text
                    for dc in root.iter('DateCreation'):
                        dateCreate = dc.text
                else:
                    pp = os.path.realpath(os.path.join(values[1], values[0] + ".gqp"))  # old file
                    if os.path.exists(pp):
                        validLines.append(x)
                        f2 = open(pp, "r")
                        lines = f2.readlines()
                        if len(lines) >= 2:
                            dateLast = lines[1]
                            dateCreate = lines[0]

                if dateLast is not None and dateCreate is not None:
                    rowPosition = self.twProjectList.rowCount()
                    self.twProjectList.insertRow(rowPosition)
                    self.twProjectList.setItem(rowPosition, 0, QTableWidgetItem(values[0]))
                    self.twProjectList.setItem(rowPosition, 1, QTableWidgetItem(dateLast))
                    self.twProjectList.setItem(rowPosition, 2, QTableWidgetItem(dateCreate))
                    self.twProjectList.setItem(rowPosition, 3, QTableWidgetItem(values[1]))
        f.close()
        f = open(self.gplFile, "w")
        for x in validLines:
            QGISRedUtils().writeFile(f, x)
        f.close()

    def addProjectToTable(self, folder, net):
        folder = self.getUniformedPath(folder)
        dirList = os.listdir(folder)
        if net + "_Pipes.shp" in dirList:
            self.updateMetadata(net, folder)
            file = open(self.gplFile, "a+")
            QGISRedUtils().writeFile(file, net + ";" + folder + "\n")
            file.close()
            self.fillTable()
        else:
            message = "'" + net + "' project is not found in selected folder"
            self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)

    def updateMetadata(self, net, folder):
        filePath = os.path.join(folder, net + "_Metadata.txt")
        isInMetadata = False
        if os.path.exists(filePath):
            with open(filePath, 'r', encoding="latin-1") as content_file:
                isInMetadata = "<Inputs>" in content_file.read()
        if isInMetadata:
            return  # If there is info in metadata file we don't update it
        dirList = os.listdir(folder)
        layersNames = ""
        for layerName in self.ownMainLayers:
            if net + "_" + layerName + ".shp" in dirList:
                layersNames = layersNames + layerName + ";"
        if not layersNames == "":
            layersNames = "[Inputs]" + layersNames.strip(";")
        self.parent.updateMetadata(layersNames, folder, net)

    def clearQGisProject(self, task):
        QgsProject.instance().clear()
        if task is not None:
            return {'task': task.definition()}

    def openProjectInQgis(self, projectDirectory, networkName):
        metadataFile = os.path.join(
            projectDirectory, networkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, 'r', encoding="latin-1") as content_file:
                data = content_file.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for qgs in root.findall('./ThirdParty/QGISRed/QGisProject'):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    QgsProject.instance().read(finfo.filePath())
                    return
            for groups in root.findall('./ThirdParty/QGISRed/Groups'):
                for group in groups:
                    groupName = group.tag
                    root = QgsProject.instance().layerTreeRoot()
                    netGroup = root.addGroup(networkName)
                    treeGroup = netGroup.addGroup(groupName)
                    for lay in group.iter('Layer'):
                        layerName = lay.text
                        layerPath = os.path.join(
                            projectDirectory, networkName + "_" + layerName + ".shp")
                        if not os.path.exists(layerPath):
                            continue
                        if treeGroup is None:
                            vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
                        else:
                            vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                            QgsProject.instance().addMapLayer(vlayer, False)
                            treeGroup.insertChildNode(0, QgsLayerTreeLayer(vlayer))
                        if vlayer is not None:
                            if ".shp" in layerPath:
                                QGISRedUtils().setStyle(vlayer, layerName.lower())
        else:  # old file
            gqpFilename = os.path.join(projectDirectory, networkName + ".gqp")
            if os.path.exists(gqpFilename):
                f = open(gqpFilename, "r")
                lines = f.readlines()
                qgsFile = lines[2]
                if ".qgs" in qgsFile or ".qgz" in qgsFile:
                    finfo = QFileInfo(qgsFile)
                    QgsProject.instance().read(finfo.filePath())
                else:
                    group = None
                    for i in range(2, len(lines)):
                        if "[" in lines[i]:
                            groupName = str(lines[i].strip("[").strip("\r\n").strip("]")).replace(networkName + " ", "")
                            root = QgsProject.instance().layerTreeRoot()
                            netGroup = root.addGroup(networkName)
                            group = netGroup.addGroup(groupName)
                        else:
                            layerPath = lines[i].strip("\r\n")
                            if not os.path.exists(layerPath):
                                continue
                            vlayer = None
                            layerName = os.path.splitext(os.path.basename(layerPath))[0].replace(networkName + "_", "")
                            if group is None:
                                vlayer = self.iface.addVectorLayer(
                                    layerPath, layerName, "ogr")
                            else:
                                vlayer = QgsVectorLayer(
                                    layerPath, layerName, "ogr")
                                QgsProject.instance().addMapLayer(vlayer, False)
                                group.insertChildNode(
                                    0, QgsLayerTreeLayer(vlayer))
                            if vlayer is not None:
                                if ".shp" in layerPath:
                                    names = (os.path.splitext(os.path.basename(layerPath))[0]).split("_")
                                    nameLayer = names[len(names)-1]
                                    QGISRedUtils().setStyle(vlayer, nameLayer.lower())
            else:
                self.iface.messageBar().pushMessage("Warning", "File not found", level=1, duration=5)

    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedUtils().getLayers()

    """MainMethods"""
    def openProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                isSameProject = self.getUniformedPath(self.ProjectDirectory) == str(self.twProjectList.item(row.row(), 3).text())
                isSameNet = self.NetworkName == str(self.twProjectList.item(row.row(), 0).text())
                if isSameProject and isSameNet:
                    self.iface.messageBar().pushMessage("Warning", "Selected project is currently opened.", level=1, duration=5)
                    return
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedUtils().runTask('open project', self.clearQGisProject, self.openProjectProcess)
        else:
            self.iface.messageBar().pushMessage("Warning", "You need to select a valid project to open it.", level=1, duration=5)

    def openProjectProcess(self, exception=None, result=None):
        selectionModel = self.twProjectList.selectionModel()
        for row in selectionModel.selectedRows():
            rowIndex = row.row()
            self.NetworkName = str(self.twProjectList.item(rowIndex, 0).text())
            self.ProjectDirectory = str(self.twProjectList.item(rowIndex, 3).text())
            self.openProjectInQgis(self.ProjectDirectory, self.NetworkName)
            break
        self.close()
        self.ProcessDone = True
        self.parent.readUnits()

    def createProject(self):
        if self.ProjectDirectory == self.parent.TemporalFolder:
            self.createProjectProcess()
        else:
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedUtils().runTask('create project', self.clearQGisProject, self.createProjectProcess)

    def createProjectProcess(self, exception=None, result=None):
        dlg = QGISRedCreateProjectDialog()
        dlg.config(self.iface, "Temporal folder", "Network", self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec_()
        self.parent.readUnits()

        self.ProjectDirectory = dlg.ProjectDirectory
        self.NetworkName = dlg.NetworkName
        self.ProcessDone = True

    def importData(self):
        if self.ProjectDirectory == self.parent.TemporalFolder:
            self.importDataProcess()
        else:
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedUtils().runTask('import project', self.clearQGisProject, self.importDataProcess)

    def importDataProcess(self, exception=None, result=None):
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec_()
        self.parent.readUnits()
        result = dlg.ProcessDone
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.ProcessDone = True

    def cloneProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainName = str(self.twProjectList.item(row.row(), 0).text())
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                dlg = QGISRedCloneProjectDialog()
                # Run the dialog event loop
                dlg.exec_()
                result = dlg.ProcessDone
                if result:
                    if mainName == dlg.NetworkName:
                        message = "Selected project has the same Network's Name. Plase, set another name."
                        self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)
                    else:
                        for layerName in self.ownMainLayers:
                            layerPath = os.path.join(mainFolder, mainName + "_" + layerName)
                            # Extensions
                            for ext in self.layerExtensions:
                                if os.path.exists(layerPath + ext):
                                    name = dlg.NetworkName + "_" + layerName + ext
                                    copyfile(layerPath + ext, os.path.join(dlg.ProjectDirectory, name))
                        for fileName in self.ownFiles:
                            filePath = os.path.join(mainFolder, mainName + "_" + fileName)
                            if os.path.exists(filePath):
                                copyfile(filePath, os.path.join(dlg.ProjectDirectory, dlg.NetworkName + "_" + fileName))

                        self.addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)
                break
        else:
            self.iface.messageBar().pushMessage("Warning", "There is no a selected project to clone.", level=1, duration=5)

    def loadProject(self):
        dlg = QGISRedImportProjectDialog()
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)

    def unloadProject(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                isSameProject = self.getUniformedPath(self.ProjectDirectory) == str(self.twProjectList.item(row.row(), 3).text())
                isSameNet = self.NetworkName == str(self.twProjectList.item(row.row(), 0).text())
                if isSameProject and isSameNet:
                    self.iface.messageBar().pushMessage("Warning", "Current project can not be unloaded.", level=1, duration=5)
                    return
                if os.path.exists(self.gplFile):
                    f = open(self.gplFile, "r")
                    lines = f.readlines()
                    f.close()
                    f = open(self.gplFile, "w")
                    i = 0
                    for line in lines:
                        if not i == row.row():
                            QGISRedUtils().writeFile(f, line)
                        i = i+1
                    f.close()
            self.fillTable()

    def openFolder(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                os.startfile(mainFolder)
