# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QTableWidgetItem, QDialog, QFileDialog, QMessageBox, QApplication
from qgis.PyQt.QtCore import Qt, QDateTime
from qgis.PyQt.QtGui import QFont
from qgis.core import QgsProject
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QHeaderView

# Import the code for the dialog
from .qgisred_createproject_dialog import QGISRedCreateProjectDialog
from .qgisred_import_dialog import QGISRedImportDialog
from .qgisred_loadproject_dialog import QGISRedImportProjectDialog
from .qgisred_cloneproject_dialog import QGISRedCloneProjectDialog
from .qgisred_renameproject_dialog import QGISRedRenameProjectDialog
from .qgisred_moveproject_dialog import QGISRedMoveProjectDialog
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_project_io import QGISRedProjectIO
from ...tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
from ...tools.utils.qgisred_ui_utils import QGISRedBanner

import os
from shutil import rmtree
from xml.etree import ElementTree  # nosec B314 — parses local project files only, no external input


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_projectmanager_dialog.ui"))


class QGISRedProjectManagerDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False
    gplFile = ""
    utils = None
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]

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
        self.btMove.clicked.connect(self.moveProject)
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
        header = self.twProjectList.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        item = QTableWidgetItem(self.tr("Name"))
        self.twProjectList.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem(self.tr("Last update"))
        self.twProjectList.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem(self.tr("Creation date"))
        self.twProjectList.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem(self.tr("Folder"))
        self.twProjectList.setHorizontalHeaderItem(3, item)

        self.twProjectList.cellDoubleClicked.connect(self.openProject)

        self.messageBar = QGISRedBanner.inject(self, self.gridLayout_2)

    def config(self, ifac, direct, netw, parent):
        self.parent = parent
        self.iface = ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.utils = QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

        # Rows:
        self._fillTable()

    """Helpers"""
    def _getUniformedPath(self, path):
        return self.utils.getUniformedPath(path)

    def _removeFilesFromFolder(self, folder, networkName, _qgisProjectBase=None):
        folder = self._getUniformedPath(folder)
        io = self._getIO(folder, networkName)

        if _qgisProjectBase is None:
            _qgisProjectBase = io.getQGisProjectBase(folder, networkName)

        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath):
                shouldDelete = f.startswith(networkName + "_")
                if not shouldDelete and _qgisProjectBase is not None:
                    shouldDelete = os.path.normcase(io.stripAllExtensions(filepath)) == os.path.normcase(_qgisProjectBase)

                if shouldDelete:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
            elif os.path.isdir(filepath):
                if os.path.basename(filepath).lower() == "layerstyles": # Temporal fix
                    try:
                        rmtree(filepath)
                    except Exception:
                        pass
                else:
                    self._removeFilesFromFolder(filepath, networkName, _qgisProjectBase)

        try:
            if len(os.listdir(folder)) == 0:
                os.rmdir(folder)
        except Exception:
            pass

    def _getIO(self, projectPath=None, networkName=None):
        return QGISRedProjectIO(projectPath or self.ProjectDirectory, networkName or self.NetworkName, self.iface)

    """Helpers for Table/UI"""
    def _takeRow(self, rowIndex):
        rowItems = []
        columns = self.twProjectList.columnCount()
        col = 0
        while col < columns:
            rowItems.append(self.twProjectList.takeItem(rowIndex, col))
            col += 1
        return rowItems

    def _setRow(self, rowIndex, rowItems):
        columns = self.twProjectList.columnCount()
        col = 0
        while col < columns:
            self.twProjectList.setItem(rowIndex, col, rowItems[col])
            col += 1

    def _getSelectedRowInfo(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                project = str(self.twProjectList.item(row.row(), 3).text())
                name = str(self.twProjectList.item(row.row(), 0).text())
                return True, name, project, row.row()
        return False, "", "", -1

    def _fillTable(self):
        font = QFont()
        font.setBold(True)

        self.twProjectList.setRowCount(0)
        if not os.path.exists(self.gplFile):
            f1 = open(self.gplFile, "w+")
            f1.close()
        validLines = []
        f = open(self.gplFile, "r")

        # Preserve order while removing duplicates
        notDuplicateLines = []
        seen = set()
        for value in f:
            value = value.strip()  # Remove trailing whitespace/newlines early
            if value and value not in seen:  # Check for non-empty and not duplicate
                notDuplicateLines.append(value + "\n")  # Re-add newline for consistency
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
                    validLines.append(x.rstrip("\n"))  # Store without newline for clean writing
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
                        validLines.append(x.rstrip("\n"))  # Store without newline for clean writing
                        f2 = open(metadataFile, "r")
                        lines = f2.readlines()
                        if len(lines) >= 2:
                            dateLast = lines[1]
                            dateCreate = lines[0]

                if dateLast is not None and dateCreate is not None:
                    rowPosition = self.twProjectList.rowCount()
                    self.twProjectList.insertRow(rowPosition)
                    self.twProjectList.setItem(rowPosition, 0, QTableWidgetItem(values[0]))
                    dateL = QTableWidgetItem()
                    dateL.setData(0, QDateTime.fromString(dateLast, 'dd/MM/yyyy HH:mm:ss'))
                    self.twProjectList.setItem(rowPosition, 1, dateL)
                    dateC = QTableWidgetItem()
                    dateC.setData(0, QDateTime.fromString(dateCreate, 'dd/MM/yyyy HH:mm:ss'))
                    self.twProjectList.setItem(rowPosition, 2, dateC)
                    self.twProjectList.setItem(rowPosition, 3, QTableWidgetItem(values[1]))

                    isSameProject = self._getUniformedPath(self.ProjectDirectory) == self._getUniformedPath(values[1])
                    isSameNet = self.NetworkName == values[0]
                    if isSameProject and isSameNet:
                        self.twProjectList.setCurrentCell(rowPosition, 1)
                        for column in range(0, self.twProjectList.columnCount()):
                            self.twProjectList.item(rowPosition, column).setFont(font)

        f.close()
        # Rewrite file with valid lines only, preserving order
        f = open(self.gplFile, "w")
        for x in validLines:
            f.write(x + "\n")
        f.close()

    def _addProjectToTable(self, folder, net):
        folder = self._getUniformedPath(folder)
        dirList = os.listdir(folder)
        isPipes = net + "_Pipes.shp" in dirList
        isMetadata = net + "_Metadata.txt" in dirList
        if isPipes:
            if not isMetadata:
                self._updateMetadata(net, folder)

            # Add project to beginning of gpl file
            newEntry = net + ";" + folder

            # Read existing entries
            existingEntries = []
            if os.path.exists(self.gplFile):
                with open(self.gplFile, "r") as f:
                    existingEntries = [line.strip() for line in f if line.strip() and line.strip() != newEntry]

            # Write new entry at the beginning, followed by existing entries
            with open(self.gplFile, "w") as f:
                f.write(newEntry + "\n")
                for entry in existingEntries:
                    f.write(entry + "\n")

            self._fillTable()
            self.twProjectList.setCurrentCell(0, 1)  # Select first row (newly added)
            self.twProjectList.setFocus()
        else:
            message = "'" + net + "' project is not found in selected folder"
            self.pushMessage("Warning", message, level=1, duration=5)

    def _updateMetadata(self, net, folder):
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

    def _clearQGisProject(self):
        QgsProject.instance().clear()

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    """Main methods"""
    def up(self):
        self.moveUpDown(True)

    def down(self):
        self.moveUpDown(False)

    def moveUpDown(self, up):
        ok, _, _, sourceRow = self._getSelectedRowInfo()
        if ok:
            destRow = sourceRow - 1
            if not up:
                destRow = sourceRow + 1
            rows = self.twProjectList.rowCount()
            if destRow < 0 or destRow >= rows:
                self.twProjectList.setFocus()
                return

            sourceItems = self._takeRow(sourceRow)
            destItems = self._takeRow(destRow)

            self._setRow(sourceRow, destItems)
            self._setRow(destRow, sourceItems)

            self.twProjectList.setCurrentCell(destRow, 1)
            self.twProjectList.setFocus()

            f = open(self.gplFile, "w")
            rowIndex = 0
            while rowIndex < rows:
                name = str(self.twProjectList.item(rowIndex, 0).text())
                directory = str(self.twProjectList.item(rowIndex, 3).text())
                self.utils.writeFile(f, name + ";" + directory + "\n")
                rowIndex = rowIndex + 1
            f.close()
        else:
            self.pushMessage(self.tr("Warning"), self.tr("Please, select a row project to move."), level=1, duration=5)

    def openFolder(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                os.startfile(mainFolder)
        else:
            message = self.tr("You need to select a project to open its folder.")
            self.pushMessage(self.tr("Warning"), message, level=1, duration=5)

    def openProject(self):
        ok, name, project, _ = self._getSelectedRowInfo()
        if ok:
            isSameProject = self._getUniformedPath(self.ProjectDirectory) == project
            isSameNet = self.NetworkName == name
            if isSameProject and isSameNet:
                self.pushMessage(self.tr("Warning"), self.tr("Selected project is currently opened."), level=1, duration=5)
                return
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self._clearQGisProject, self.openProjectProcess)
        else:
            self.pushMessage(self.tr("Warning"), self.tr("You need to select a project to open it."), level=1, duration=5)

    def openProjectProcess(self):
        ok, name, project, _ = self._getSelectedRowInfo()
        if ok:
            self.NetworkName = name
            self.ProjectDirectory = project

            # Move opened project to top of the list
            openedEntry = name + ";" + project
            existingEntries = []
            if os.path.exists(self.gplFile):
                with open(self.gplFile, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and line != openedEntry:
                            existingEntries.append(line)

            # Write opened project at the beginning
            with open(self.gplFile, "w") as f:
                f.write(openedEntry + "\n")
                for entry in existingEntries:
                    f.write(entry + "\n")

            io = QGISRedProjectIO(self.ProjectDirectory, self.NetworkName, self.iface)
            io.openProjectInQgis()
            QGISRedIdentifierUtils(self.ProjectDirectory, self.NetworkName, self.iface).enforceAllIdentifiers()
            self.close()
            self.ProcessDone = True
            self.parent.readOptions()
            self.parent.suggestQgsProjectFilename()

    def createProject(self):
        if self.ProjectDirectory == self.parent.TemporalFolder:
            self.createProjectProcess()
        else:
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self._clearQGisProject, self.createProjectProcess)

    def createProjectProcess(self):
        dlg = QGISRedCreateProjectDialog()
        dlg.config(self.iface, "Temporal folder", "Network", self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec()
        self.parent.readOptions()

        self.ProjectDirectory = dlg.ProjectDirectory
        self.NetworkName = dlg.NetworkName
        self.ProcessDone = True

    def importData(self):
        if self.ProjectDirectory == self.parent.TemporalFolder:
            self.importDataProcess()
        else:
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self._clearQGisProject, self.importDataProcess)

    def importDataProcess(self):
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec()

    def exportData(self):
        ok, name, project, _ = self._getSelectedRowInfo()
        if ok:
            # Ask for a zip file
            qfd = QFileDialog()
            path = ""
            filter = "zip(*.zip)"
            f = QFileDialog.getSaveFileName(qfd, "Zip file to export project", path, filter)
            zipPath = f[0]
            if zipPath == "":
                return

            io = QGISRedProjectIO(project, name, self.iface)
            io.exportProjectToZip(zipPath)
            self.pushMessage("QGISRed", self.tr("Zip file stored in: ") + zipPath, level=0, duration=5)
            return
        else:
            self.pushMessage(self.tr("Warning"), self.tr("You need to select a project to export it."), level=1, duration=5)

    def loadProject(self):
        dlg = QGISRedImportProjectDialog()
        # Run the dialog event loop
        dlg.exec()
        result = dlg.ProcessDone
        if result:
            self._addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)

    def unloadProject(self):
        self.quitProject()

    def removeProject(self):
        self.quitProject(True)

    def quitProject(self, remove=False):
        ok, projectNetwork, projectPath, rowIndex = self._getSelectedRowInfo()
        if ok:
            isSameProject = self._getUniformedPath(self.ProjectDirectory) == projectPath
            isSameNet = self.NetworkName == projectNetwork
            if isSameProject and isSameNet:
                if remove:
                    self.pushMessage(self.tr("Warning"), self.tr("Current project cannot be removed"), level=1, duration=5)
                else:
                    self.pushMessage(self.tr("Warning"), self.tr("Current project cannot be unloaded"), level=1, duration=5)
                return

            if remove:
                request = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("QGISRed"),
                    self.tr("Project will be removed completely from your computer. Are you sure?"),
                    QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                )
                if request == QMessageBox.Yes:
                    self._removeFilesFromFolder(projectPath, projectNetwork)
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
                        self.utils.writeFile(f, line)
                    i = i + 1
                f.close()
            self._fillTable()
        else:
            word = "unload"
            if remove:
                word = "remove"
            self.pushMessage(
                self.tr("Warning"), self.tr(f"You need to select a project to {word} it."), level=1, duration=5
            )

    def cloneProject(self):
        ok, mainName, mainFolder, _ = self._getSelectedRowInfo()
        if ok:
            io = self._getIO(mainFolder, mainName)
            dlg = QGISRedCloneProjectDialog()
            # Run the dialog event loop
            dlg.exec()
            result = dlg.ProcessDone
            if result:
                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                io.processProjectFiles(mainFolder, mainName, dlg.NetworkName, dlg.ProjectDirectory, deleteSource=False)

                qgisBase = io.getQGisProjectBase(mainFolder, mainName)
                if qgisBase:
                    oldQgisDir = os.path.dirname(qgisBase)
                    newQgisPath = io.processQGisProjectFiles(qgisBase, dlg.NetworkName, dlg.ProjectDirectory, deleteSource=False)
                    if newQgisPath:
                        io.updateQGisProjectContent(
                            newQgisPath, mainName, dlg.NetworkName,
                            mainFolder, dlg.ProjectDirectory,
                            oldQgisDir, dlg.ProjectDirectory,
                        )
                        io.updateMetadataQGisProject(dlg.ProjectDirectory, dlg.NetworkName, newQgisPath)
                QApplication.restoreOverrideCursor()

                self._addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)
        else:
            self.pushMessage(self.tr("Warning"), self.tr("You need to select a project to clone."), level=1, duration=5)

    def changeName(self):
        ok, projectNetwork, projectPath, rowIndex = self._getSelectedRowInfo()
        if ok:
            isSameProject = self._getUniformedPath(self.ProjectDirectory) == projectPath
            isSameNet = self.NetworkName == projectNetwork
            if isSameProject and isSameNet:
                self.pushMessage(self.tr("Warning"), self.tr("Current project can not be renamed."), level=1, duration=5)
                return
            io = self._getIO(projectPath, projectNetwork)
            qgisBase = io.getQGisProjectBase(projectPath, projectNetwork)
            dlg = QGISRedRenameProjectDialog(None, projectNetwork, projectPath, qgisBase)
            # Run the dialog event loop
            dlg.exec()
            result = dlg.ProcessDone
            if not result:
                return
            newProjectName = dlg.NewNetworkName if dlg.RenameProject else None
            newQgisBasename = dlg.NewQGISName if dlg.RenameQGISProject else None
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            oldProjectPath = projectPath
            metadataFiles = [f for f in os.listdir(projectPath) if f.endswith("_Metadata.txt")]
            canRenameFolder = os.path.basename(projectPath) == projectNetwork and len(metadataFiles) == 1
            newQgisPath = None
            if newQgisBasename and qgisBase:
                parentDir = os.path.dirname(qgisBase)
                newQgisPath = io.processQGisProjectFiles(qgisBase, newQgisBasename, parentDir, deleteSource=True)
            if dlg.RenameBackups:
                backupsFolder = os.path.join(projectPath, "backups")
                if os.path.isdir(backupsFolder):
                    oldPrefix = projectNetwork + "_"
                    newPrefix = (newProjectName or projectNetwork) + "_"
                    for f in os.listdir(backupsFolder):
                        if f.startswith(oldPrefix) and f.endswith(".zip"):
                            zipPath = os.path.join(backupsFolder, f)
                            # 1. Rename inner files
                            io.renameFilesInZip(zipPath, oldPrefix, newPrefix)
                            # 2. Rename zip file itself
                            newZipName = f.replace(oldPrefix, newPrefix, 1)
                            newZipPath = os.path.join(backupsFolder, newZipName)
                            try:
                                os.rename(zipPath, newZipPath)
                            except Exception:
                                pass
            if newProjectName:
                io.processProjectFiles(projectPath, projectNetwork, newProjectName, projectPath, deleteSource=True, excludeDirs=['backups'])
            if newQgisPath:
                io.updateMetadataQGisProject(projectPath, newProjectName or projectNetwork, newQgisPath)
            if newProjectName and canRenameFolder:
                newProjectPath = os.path.join(os.path.dirname(projectPath), newProjectName)
                try:
                    os.rename(projectPath, newProjectPath)
                    projectPath = self._getUniformedPath(newProjectPath)
                    if newQgisPath:
                        newQgisPath = self._getUniformedPath(newQgisPath.replace(oldProjectPath, projectPath))
                    self.twProjectList.setItem(rowIndex, 3, QTableWidgetItem(projectPath))
                except Exception:
                    pass
            if qgisBase:
                oldQgisDir = os.path.dirname(qgisBase)
                if newQgisPath and os.path.exists(newQgisPath):
                    # .qgz was renamed (and possibly moved if folder was also renamed)
                    newQgisDir = os.path.dirname(newQgisPath)
                    qgisFileToUpdate = newQgisPath
                elif oldProjectPath != projectPath:
                    # folder was renamed but .qgz was not — update it in its new location
                    renamedBase = qgisBase.replace(oldProjectPath, projectPath)
                    newQgisDir = os.path.dirname(renamedBase)
                    qgisFileToUpdate = io.findQGisProjectFile(renamedBase)
                else:
                    qgisFileToUpdate = None
                    newQgisDir = None
                if qgisFileToUpdate and os.path.exists(qgisFileToUpdate):
                    effectiveName = newProjectName or projectNetwork
                    io.updateQGisProjectContent(qgisFileToUpdate, projectNetwork, effectiveName, oldProjectPath, projectPath, oldQgisDir, newQgisDir)
            effectiveName = newProjectName or projectNetwork
            self.twProjectList.setItem(rowIndex, 0, QTableWidgetItem(effectiveName))
            QApplication.restoreOverrideCursor()

            f = open(self.gplFile, "r")
            lines = f.readlines()
            f.close()
            f = open(self.gplFile, "w")
            i = 0
            for line in lines:
                if not i == rowIndex:
                    self.utils.writeFile(f, line)
                else:
                    self.utils.writeFile(f, effectiveName + ";" + projectPath + "\n")
                i = i + 1
            f.close()

            self.pushMessage("QGISRed", self.tr("Project name has been renamed to ") + effectiveName, level=0, duration=5)
        else:
            self.pushMessage(
                self.tr("Warning"), self.tr("You need to select a project to change its name."), level=1, duration=5
            )

    def moveProject(self):
        ok, projectNetwork, projectPath, rowIndex = self._getSelectedRowInfo()
        if not ok:
            self.pushMessage(self.tr("Warning"), self.tr("You need to select a project to move it."), level=1, duration=5)
            return
        io = self._getIO(projectPath, projectNetwork)
        isSameProject = self._getUniformedPath(self.ProjectDirectory) == projectPath
        isSameNet = self.NetworkName == projectNetwork
        if isSameProject and isSameNet:
            self.pushMessage(self.tr("Warning"), self.tr("Current project can not be moved."), level=1, duration=5)
            return

        qgisBase = io.getQGisProjectBase(projectPath, projectNetwork)
        dlg = QGISRedMoveProjectDialog(None, projectPath, projectNetwork, qgisBase)
        dlg.exec()
        if not dlg.ProcessDone:
            return

        targetDir = self._getUniformedPath(dlg.TargetDirectory)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        oldProjectPath = projectPath
        oldQgisDir = os.path.dirname(qgisBase) if qgisBase else None
        newQgisPath = None

        if dlg.MoveProjectFiles:
            io.processProjectFiles(projectPath, projectNetwork, projectNetwork, targetDir, deleteSource=True)
            projectPath = targetDir
            self.twProjectList.setItem(rowIndex, 3, QTableWidgetItem(projectPath))

        if dlg.MoveQGISProject and qgisBase:
            newQgisPath = io.processQGisProjectFiles(qgisBase, os.path.basename(qgisBase), targetDir, deleteSource=True)
            if newQgisPath:
                io.updateMetadataQGisProject(projectPath, projectNetwork, newQgisPath)

        # Update internal layer paths in the QGIS project file.
        # In all cases the .qgz/.qgs must be updated because either the layers moved,
        # the .qgz/.qgs moved (changing relative paths), or both.
        #   A) Both moved   → update the .qgz/.qgs at its new location; layers at new folder
        #   B) Only project files moved → .qgz/.qgs stays in place; layers at new folder
        #   C) Only .qgz/.qgs moved → update the .qgz/.qgs at its new location;
        #                             layers stayed, but relative paths from the new .qgz location changed
        if qgisBase:
            qgisFileMoved = newQgisPath is not None  # True when _processQGisProjectFiles succeeded
            if qgisFileMoved:
                # Cases A and C: .qgz/.qgs is now at its new location
                qgisFileToUpdate = newQgisPath
                newQgisDir = os.path.dirname(newQgisPath)
            elif dlg.MoveProjectFiles:
                # Case B: layers moved but .qgz/.qgs stayed — update it in place
                qgisFileToUpdate = io.findQGisProjectFile(qgisBase)
                newQgisDir = oldQgisDir  # .qgz/.qgs did not move
            else:
                qgisFileToUpdate = None
                newQgisDir = None
            if qgisFileToUpdate and os.path.exists(qgisFileToUpdate):
                io.updateQGisProjectContent(qgisFileToUpdate, projectNetwork, projectNetwork, oldProjectPath, projectPath, oldQgisDir, newQgisDir)

        f = open(self.gplFile, "r")
        lines = f.readlines()
        f.close()
        f = open(self.gplFile, "w")
        for i, line in enumerate(lines):
            if i != rowIndex:
                self.utils.writeFile(f, line)
            else:
                self.utils.writeFile(f, projectNetwork + ";" + projectPath + "\n")
        f.close()

        QApplication.restoreOverrideCursor()
        self.pushMessage("QGISRed", self.tr("Project has been moved to ") + targetDir, level=0, duration=5)
