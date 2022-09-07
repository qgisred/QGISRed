# -*- coding: utf-8 -*-
from genericpath import isdir
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import QFileInfo, Qt
from PyQt5.QtGui import QFont
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer
from qgis.PyQt import uic

# Import the code for the dialog
from .qgisred_createproject_dialog import QGISRedCreateProjectDialog
from .qgisred_import_dialog import QGISRedImportDialog
from .qgisred_importproject_dialog import QGISRedImportProjectDialog
from .qgisred_cloneproject_dialog import QGISRedCloneProjectDialog
from .qgisred_renameproject_dialog import QGISRedRenameProjectDialog
from ..tools.qgisred_utils import QGISRedUtils

import os
import shutil
from shutil import copyfile
from xml.etree import ElementTree
from zipfile import ZipFile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_projectmanager_dialog.ui"))


class QGISRedProjectManagerDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False
    gplFile = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    complementaryLayers = ["IsolationValves", "Hydrants", "WashoutValves", "AirReleaseValves", "ServiceConnections", "Meters"]
    layerExtensions = [".shp", ".dbf", ".shx", ".prj", ".qpj"]
    ownFiles = [
        "DefaultValues.dbf",
        "Options.dbf",
        "Rules.dbf",
        "Controls.dbf",
        "Curves.dbf",
        "Patterns.dbf",
        "TitleAndNotes.txt",
        "Metadata.txt",
    ]

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedProjectManagerDialog, self).__init__(parent)
        self.setupUi(self)
        self.btUp.clicked.connect(self.up)
        self.btDown.clicked.connect(self.down)

        self.btOpen.clicked.connect(self.openProject)
        self.btCreate.clicked.connect(self.createProject)
        self.btImport.clicked.connect(self.importData)
        self.btExport.clicked.connect(self.exportData)
        self.btClone.clicked.connect(self.cloneProject)
        self.btRemove.clicked.connect(self.removeProject)

        self.btLoad.clicked.connect(self.loadProject)
        self.btUnLoad.clicked.connect(self.unloadProject)
        self.btChangeName.clicked.connect(self.changeName)
        self.btGo2Folder.clicked.connect(self.openFolder)
        # Variables:
        gplFolder = os.path.join(os.getenv("APPDATA"), "QGISRed")
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

        self.twProjectList.cellDoubleClicked.connect(self.openProject)

    """Methods"""

    def config(self, ifac, direct, netw, parent):
        self.parent = parent
        self.iface = ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct

        # Rows:
        self.fillTable()

    def fillTable(self):
        font = QFont()
        font.setBold(True)

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

                metadataFile = os.path.realpath(os.path.join(values[1], values[0] + "_Metadata.txt"))
                pipeFile = os.path.realpath(os.path.join(values[1], values[0] + "_Pipes.shp"))
                if os.path.exists(metadataFile) and os.path.exists(pipeFile):
                    validLines.append(x)
                    data = ""
                    with open(metadataFile, "r", encoding="latin-1") as content_file:
                        data = content_file.read()
                    # Parse data as XML
                    root = ElementTree.fromstring(data)
                    # Get data from nodes
                    for dl in root.iter("DateModification"):
                        dateLast = dl.text
                    for dc in root.iter("DateCreation"):
                        dateCreate = dc.text
                else:
                    metadataFile = os.path.realpath(os.path.join(values[1], values[0] + ".gqp"))  # old file
                    if os.path.exists(metadataFile) and os.path.exists(pipeFile):
                        validLines.append(x)
                        f2 = open(metadataFile, "r")
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

                    isSameProject = self.getUniformedPath(self.ProjectDirectory) == self.getUniformedPath(values[1])
                    isSameNet = self.NetworkName == values[0]
                    if isSameProject and isSameNet:
                        self.twProjectList.setCurrentCell(rowPosition, 1)
                        for column in range(0, self.twProjectList.columnCount()):
                            self.twProjectList.item(rowPosition, column).setFont(font)

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
            self.twProjectList.setCurrentCell(self.twProjectList.rowCount() - 1, 1)
            self.twProjectList.setFocus()
        else:
            message = "'" + net + "' project is not found in selected folder"
            self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)

    def updateMetadata(self, net, folder):
        filePath = os.path.join(folder, net + "_Metadata.txt")
        isInMetadata = False
        if os.path.exists(filePath):
            with open(filePath, "r", encoding="latin-1") as content_file:
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
            return {"task": task.definition()}

    def openProjectInQgis(self, projectDirectory, networkName):
        metadataFile = os.path.join(projectDirectory, networkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, "r", encoding="latin-1") as content_file:
                data = content_file.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for qgs in root.findall("./ThirdParty/QGISRed/QGisProject"):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    QgsProject.instance().read(finfo.filePath())
                    return
            for groups in root.findall("./ThirdParty/QGISRed/Groups"):
                for group in groups:
                    groupName = group.tag
                    root = QgsProject.instance().layerTreeRoot()
                    netGroup = root.addGroup(networkName)
                    treeGroup = netGroup.addGroup(groupName)
                    for lay in group.iter("Layer"):
                        layerName = lay.text
                        layerPath = os.path.join(projectDirectory, networkName + "_" + layerName + ".shp")
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
                                vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
                            else:
                                vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                                QgsProject.instance().addMapLayer(vlayer, False)
                                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
                            if vlayer is not None:
                                if ".shp" in layerPath:
                                    names = (os.path.splitext(os.path.basename(layerPath))[0]).split("_")
                                    nameLayer = names[len(names) - 1]
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

    def removeFilesFromFolder(self, folder, networkName):
        folder = self.getUniformedPath(folder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and os.path.join(folder, networkName + "_") in filepath:
                try:
                    os.remove(filepath)
                except:
                    pass
            elif os.path.isdir(filepath):
                self.removeFilesFromFolder(filepath, networkName)
        if len(os.listdir(folder)) == 0:
            os.rmdir(folder)

    def renameFiles(self, folder, oldName, newName):
        folder = self.getUniformedPath(folder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and os.path.join(folder, oldName + "_") in filepath:
                try:
                    copyfile(r"" + filepath, r"" + filepath.replace(oldName + "_", newName + "_"))
                    os.remove(filepath)
                except:
                    pass
            elif os.path.isdir(filepath):
                self.renameFiles(filepath, oldName, newName)

    def takeRow(self, rowIndex):
        rowItems = []
        columns = self.twProjectList.columnCount()
        col = 0
        while col < columns:
            rowItems.append(self.twProjectList.takeItem(rowIndex, col))
            col += 1
        return rowItems

    def setRow(self, rowIndex, rowItems):
        columns = self.twProjectList.columnCount()
        col = 0
        while col < columns:
            self.twProjectList.setItem(rowIndex, col, rowItems[col])
            col += 1

    def move(self, up):
        ok, _, _, sourceRow = self.getSelectedRowInfo()
        if ok:
            destRow = sourceRow - 1
            if not up:
                destRow = sourceRow + 1
            rows = self.twProjectList.rowCount()
            if destRow < 0 or destRow >= rows:
                self.twProjectList.setFocus()
                return

            sourceItems = self.takeRow(sourceRow)
            destItems = self.takeRow(destRow)

            self.setRow(sourceRow, destItems)
            self.setRow(destRow, sourceItems)

            self.twProjectList.setCurrentCell(destRow, 1)
            self.twProjectList.setFocus()

            f = open(self.gplFile, "w")
            rowIndex = 0
            while rowIndex < rows:
                name = str(self.twProjectList.item(rowIndex, 0).text())
                directory = str(self.twProjectList.item(rowIndex, 3).text())
                QGISRedUtils().writeFile(f, name + ";" + directory + "\n")
                rowIndex = rowIndex + 1
            f.close()
        else:
            self.iface.messageBar().pushMessage("Warning", "Please, select a row project to move.", level=1, duration=5)

    def quitProject(self, remove=False):
        ok, projectNetwork, projectPath, rowIndex = self.getSelectedRowInfo()
        if ok:
            isSameProject = self.getUniformedPath(self.ProjectDirectory) == projectPath
            isSameNet = self.NetworkName == projectNetwork
            if isSameProject and isSameNet:
                word = "unloaded"
                if remove:
                    word = "removed"
                self.iface.messageBar().pushMessage("Warning", "Current project can not be " + word + ".", level=1, duration=5)
                return

            if remove:
                request = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("QGISRed"),
                    self.tr("Project will be remove completely from your computer. Are you sure?"),
                    QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                )
                if request == QMessageBox.Yes:
                    self.removeFilesFromFolder(projectPath, projectNetwork)
                else:
                    return
            else:
                request = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("QGISRed"),
                    self.tr(
                        "Project will be unloaded from this list, but will remain in your computer. You could add it back using the Load button. Do you want to continue?"
                    ),
                    QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                )
                if request == QMessageBox.No:
                    return

            if os.path.exists(self.gplFile):
                f = open(self.gplFile, "r")
                lines = f.readlines()
                f.close()
                f = open(self.gplFile, "w")
                i = 0
                for line in lines:
                    if not i == rowIndex:
                        QGISRedUtils().writeFile(f, line)
                    i = i + 1
                f.close()
            self.fillTable()

    def getSelectedRowInfo(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                project = str(self.twProjectList.item(row.row(), 3).text())
                name = str(self.twProjectList.item(row.row(), 0).text())
                return True, name, project, row.row()
        return False, "", "", -1

    """MainMethods"""

    def up(self):
        self.move(True)

    def down(self):
        self.move(False)

    def openProject(self):
        ok, name, project, _ = self.getSelectedRowInfo()
        if ok:
            isSameProject = self.getUniformedPath(self.ProjectDirectory) == project
            isSameNet = self.NetworkName == name
            if isSameProject and isSameNet:
                self.iface.messageBar().pushMessage("Warning", "Selected project is currently opened.", level=1, duration=5)
                return
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedUtils().runTask("open project", self.clearQGisProject, self.openProjectProcess, True)
        else:
            self.iface.messageBar().pushMessage("Warning", "You need to select a valid project to open it.", level=1, duration=5)

    def openProjectProcess(self, exception=None, result=None):
        ok, name, project, _ = self.getSelectedRowInfo()
        if ok:
            self.NetworkName = name
            self.ProjectDirectory = project
            self.openProjectInQgis(self.ProjectDirectory, self.NetworkName)
            self.close()
            self.ProcessDone = True
            self.parent.readUnits()

    def createProject(self):
        if self.ProjectDirectory == self.parent.TemporalFolder:
            self.createProjectProcess()
        else:
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedUtils().runTask("create project", self.clearQGisProject, self.createProjectProcess)

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
                QGISRedUtils().runTask("import project", self.clearQGisProject, self.importDataProcess)

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

    def exportData(self):
        ok, name, project, _ = self.getSelectedRowInfo()
        if ok:
            # Ask for a zip file
            qfd = QFileDialog()
            path = ""
            filter = "zip(*.zip)"
            f = QFileDialog.getSaveFileName(qfd, "Zip file to export project", path, filter)
            zipPath = f[0]
            if zipPath == "":
                return

            utils = QGISRedUtils(project, name, self.iface)
            files = utils.getFilePaths()
            with ZipFile(zipPath, "w") as zip:
                # writing each file one by one
                for file in files:
                    if self.getUniformedPath(project) + "\\" + name + "_" in file:
                        zip.write(file, file.replace(self.getUniformedPath(project), ""))

            self.iface.messageBar().pushMessage("QGISRed", "Zip file stored in: " + zipPath, level=0, duration=5)
            return
        else:
            self.iface.messageBar().pushMessage("Warning", "You need to select a project to export it.", level=1, duration=5)

    def cloneProject(self):
        ok, mainName, mainFolder, _ = self.getSelectedRowInfo()
        if ok:
            dlg = QGISRedCloneProjectDialog()
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if result:
                for layerName in self.ownMainLayers:
                    layerPath = os.path.join(mainFolder, mainName + "_" + layerName)
                    # Extensions
                    for ext in self.layerExtensions:
                        if os.path.exists(layerPath + ext):
                            name = dlg.NetworkName + "_" + layerName + ext
                            copyfile(r"" + layerPath + ext, r"" + os.path.join(dlg.ProjectDirectory, name))

                for layerName in self.complementaryLayers:
                    layerPath = os.path.join(mainFolder, mainName + "_" + layerName)
                    # Extensions
                    for ext in self.layerExtensions:
                        if os.path.exists(layerPath + ext):
                            name = dlg.NetworkName + "_" + layerName + ext
                            copyfile(r"" + layerPath + ext, r"" + os.path.join(dlg.ProjectDirectory, name))

                for fileName in self.ownFiles:
                    filePath = os.path.join(mainFolder, mainName + "_" + fileName)
                    if os.path.exists(filePath):
                        copyfile(r"" + filePath, r"" + os.path.join(dlg.ProjectDirectory, dlg.NetworkName + "_" + fileName))

                self.addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)
        else:
            self.iface.messageBar().pushMessage("Warning", "There is no a selected project to clone.", level=1, duration=5)

    def removeProject(self):
        self.quitProject(True)

    def loadProject(self):
        dlg = QGISRedImportProjectDialog()
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)

    def unloadProject(self):
        self.quitProject()

    def changeName(self):
        ok, projectNetwork, projectPath, rowIndex = self.getSelectedRowInfo()
        if ok:
            isSameProject = self.getUniformedPath(self.ProjectDirectory) == projectPath
            isSameNet = self.NetworkName == projectNetwork
            if isSameProject and isSameNet:
                self.iface.messageBar().pushMessage("Warning", "Current project can not be renamed.", level=1, duration=5)
                return
            dlg = QGISRedRenameProjectDialog(None, projectNetwork, projectPath)
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if not result:
                return
            newName = dlg.NetworkName
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.renameFiles(projectPath, projectNetwork, newName)
            self.twProjectList.setItem(rowIndex, 0, QTableWidgetItem(newName))
            QApplication.restoreOverrideCursor()

            f = open(self.gplFile, "r")
            lines = f.readlines()
            f.close()
            f = open(self.gplFile, "w")
            i = 0
            for line in lines:
                if not i == rowIndex:
                    QGISRedUtils().writeFile(f, line)
                else:
                    QGISRedUtils().writeFile(f, newName + ";" + projectPath)
                i = i + 1
            f.close()

            self.iface.messageBar().pushMessage("QGISRed", "Network's name has been renamed to " + newName, level=0, duration=5)

    def openFolder(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                os.startfile(mainFolder)
        else:
            message = "Any selected project to open its folder. Please, select one."
            self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)
