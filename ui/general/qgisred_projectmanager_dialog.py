# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QTableWidgetItem, QDialog, QFileDialog, QMessageBox, QApplication
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont
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

import os
from shutil import copyfile, copytree, rmtree
from xml.etree import ElementTree  # nosec B314 — parses local project files only, no external input
from zipfile import ZipFile, ZIP_DEFLATED


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
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        item = QTableWidgetItem(self.tr("Name"))
        self.twProjectList.setHorizontalHeaderItem(0, item)
        item = QTableWidgetItem(self.tr("Last update"))
        self.twProjectList.setHorizontalHeaderItem(1, item)
        item = QTableWidgetItem(self.tr("Creation date"))
        self.twProjectList.setHorizontalHeaderItem(2, item)
        item = QTableWidgetItem(self.tr("Folder"))
        self.twProjectList.setHorizontalHeaderItem(3, item)

        self.twProjectList.cellDoubleClicked.connect(self.openProject)

    """Methods"""

    def config(self, ifac, direct, netw, parent):
        self.parent = parent
        self.iface = ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.utils = QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

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

                    isSameProject = self.getUniformedPath(self.ProjectDirectory) == self.getUniformedPath(values[1])
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

    def addProjectToTable(self, folder, net):
        folder = self.getUniformedPath(folder)
        dirList = os.listdir(folder)
        isPipes = net + "_Pipes.shp" in dirList
        isMetadata = net + "_Metadata.txt" in dirList
        if isPipes:
            if not isMetadata:
                self.updateMetadata(net, folder)
            
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
            
            self.fillTable()
            self.twProjectList.setCurrentCell(0, 1)  # Select first row (newly added)
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

    def clearQGisProject(self):
        QgsProject.instance().clear()

    def getUniformedPath(self, path):
        return self.utils.getUniformedPath(path)

    def getLayerPath(self, layer):
        return self.utils.getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return self.utils.generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

    def _getQGisProjectBase(self, folder, networkName):
        """Returns the stem path (no extensions) of the QGIS project file, or None if not set."""
        metadataFile = os.path.join(folder, networkName + "_Metadata.txt")
        if not os.path.exists(metadataFile):
            return None
        try:
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)
            for qgs in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if qgs.text and (".qgs" in qgs.text or ".qgz" in qgs.text):
                    qgisPath = qgs.text
                    if not os.path.isabs(qgisPath):
                        qgisPath = os.path.normpath(os.path.join(folder, qgisPath))
                    return self._stripAllExtensions(self.getUniformedPath(qgisPath))
        except Exception:
            pass
        return None

    def _renameQGisProjectFiles(self, qgisBase, newName, projectPath):
        """Renames the QGIS project file and its backups, then updates the metadata XML."""
        parentDir = os.path.dirname(qgisBase)
        oldBaseName = os.path.basename(qgisBase)
        try:
            newQgisPath = None
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self._stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(oldBaseName):]
                        newFilepath = os.path.join(parentDir, newName + extensions)
                        try:
                            copyfile(filepath, newFilepath)
                            os.remove(filepath)
                            if newQgisPath is None and (extensions.startswith(".qgs") or extensions.startswith(".qgz")):
                                newQgisPath = newFilepath
                        except Exception:
                            pass
            if newQgisPath is not None:
                self._updateMetadataQGisProject(projectPath, newName, newQgisPath)
        except Exception:
            pass
        return newQgisPath

    def _findQGisProjectFile(self, qgisBase):
        """Returns the actual .qgz or .qgs path from a stem, or None if not found."""
        for ext in ('.qgz', '.qgs'):
            p = qgisBase + ext
            if os.path.exists(p):
                return p
        return None

    def _updateQGisProjectContent(self, qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None):
        """Updates layer references inside a .qgs or .qgz project file after renaming/moving."""
        try:
            if qgisPath.endswith('.qgz'):
                self._updateQGisZipContent(qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir)
            elif qgisPath.endswith('.qgs'):
                self._updateQGisXmlContent(qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir)
        except Exception:
            pass

    def _updateQGisXmlContent(self, qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None):
        with open(qgisPath, 'r', encoding='utf-8') as f:
            content = f.read()
        content = self._applyQGisReplacements(content, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir)
        with open(qgisPath, 'w', encoding='utf-8') as f:
            f.write(content)

    def _updateQGisZipContent(self, qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None):
        files = {}
        with ZipFile(qgisPath, 'r') as zin:
            for name in zin.namelist():
                files[name] = zin.read(name)
        for name in list(files.keys()):
            if name.endswith('.qgs'):
                xml = files[name].decode('utf-8')
                xml = self._applyQGisReplacements(xml, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir)
                files[name] = xml.encode('utf-8')
        with ZipFile(qgisPath, 'w', ZIP_DEFLATED) as zout:
            for name, data in files.items():
                zout.writestr(name, data)

    def _applyQGisReplacements(self, content, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None):
        import re

        oldFolderNorm = os.path.normcase(os.path.normpath(oldFolder))
        newFolderNorm = os.path.normpath(newFolder)

        def replacePathInValue(val):
            """Given a path value from the XML (may be absolute or relative), return the updated value."""
            # Normalize to absolute for comparison
            if os.path.isabs(val):
                absPath = os.path.normcase(os.path.normpath(val))
                wasRelative = False
            elif oldQgisDir:
                absPath = os.path.normcase(os.path.normpath(os.path.join(oldQgisDir, val)))
                wasRelative = True
            else:
                return val

            # Check if this path is inside the old project folder
            if not absPath.startswith(oldFolderNorm):
                return val

            # Rebuild the absolute path with the new folder
            suffix = absPath[len(oldFolderNorm):]  # e.g. \Results\test130_Base_Link.shp
            newAbsPath = newFolderNorm + suffix

            # Apply name prefix replacement on the filename part
            head, tail = os.path.split(newAbsPath)
            tail = tail.replace(oldName + '_', newName + '_')
            newAbsPath = os.path.join(head, tail)

            # Return in the same form (relative or absolute) as the original
            if not wasRelative:
                return newAbsPath.replace('\\', '/')
            else:
                rel = os.path.relpath(newAbsPath, newQgisDir if newQgisDir else oldQgisDir)
                return rel.replace('\\', '/')

        # Replace path values in XML attributes (source="..." url="..." filename="...")
        content = re.sub(r'(source|url|filename)(=)(")([^"]+)(")',
                         lambda m: m.group(1) + m.group(2) + m.group(3) + replacePathInValue(m.group(4)) + m.group(5),
                         content)
        content = re.sub(r"(source|url|filename)(=)(')([^']+)(')",
                         lambda m: m.group(1) + m.group(2) + m.group(3) + replacePathInValue(m.group(4)) + m.group(5),
                         content)

        # Replace path values in <datasource>...</datasource> element content
        content = re.sub(r'(<datasource>)([^<]+)(</datasource>)',
                         lambda m: m.group(1) + replacePathInValue(m.group(2)) + m.group(3),
                         content)

        # Name prefix replacement for any remaining occurrences (e.g. layer IDs, titles)
        if oldName != newName:
            content = content.replace(oldName + '_', newName + '_')

        # Custom property identifier: value="qgisred_oldName" (no trailing underscore)
        if oldName != newName:
            content = content.replace('value="qgisred_' + oldName + '"', 'value="qgisred_' + newName + '"')

        # Layer group name in the legend (stored as name="oldName" on the root network group)
        if oldName != newName:
            content = content.replace('name="' + oldName + '"', 'name="' + newName + '"')

        return content

    def _updateMetadataQGisProject(self, projectPath, networkName, newQgisPath):
        """Updates the <QGisProject> node in the metadata file to point to newQgisPath."""
        metadataFile = os.path.join(projectPath, networkName + "_Metadata.txt")
        if not os.path.exists(metadataFile):
            return
        try:
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)
            updated = False
            for node in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if node.text and (".qgs" in node.text or ".qgz" in node.text):
                    node.text = os.path.relpath(newQgisPath, projectPath)
                    updated = True
            if updated:
                with open(metadataFile, "w", encoding="latin-1") as mf:
                    mf.write(ElementTree.tostring(xmlRoot, encoding="unicode"))
        except Exception:
            pass

    def _stripAllExtensions(self, path):
        """Strips all extensions from a path (e.g. 'foo.qgz.bak' -> 'foo')."""
        while True:
            base, ext = os.path.splitext(path)
            if not ext:
                break
            path = base
        return path

    def removeFilesFromFolder(self, folder, networkName, _qgisProjectBase=None):
        folder = self.getUniformedPath(folder)

        if _qgisProjectBase is None:
            _qgisProjectBase = self._getQGisProjectBase(folder, networkName)

        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath):
                shouldDelete = f.startswith(networkName + "_")
                if not shouldDelete and _qgisProjectBase is not None:
                    shouldDelete = os.path.normcase(self._stripAllExtensions(filepath)) == os.path.normcase(_qgisProjectBase)
                
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
                    self.removeFilesFromFolder(filepath, networkName, _qgisProjectBase)

        try:
            if len(os.listdir(folder)) == 0:
                os.rmdir(folder)
        except Exception:
            pass

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
                self.utils.writeFile(f, name + ";" + directory + "\n")
                rowIndex = rowIndex + 1
            f.close()
        else:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Please, select a row project to move."), level=1, duration=5)

    def quitProject(self, remove=False):
        ok, projectNetwork, projectPath, rowIndex = self.getSelectedRowInfo()
        if ok:
            isSameProject = self.getUniformedPath(self.ProjectDirectory) == projectPath
            isSameNet = self.NetworkName == projectNetwork
            if isSameProject and isSameNet:
                if remove:
                    self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Current project cannot be removed"), level=1, duration=5)
                else: 
                    self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Current project cannot be unloaded"), level=1, duration=5)
                return

            if remove:
                request = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("QGISRed"),
                    self.tr("Project will be removed completely from your computer. Are you sure?"),
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
                        self.utils.writeFile(f, line)
                    i = i + 1
                f.close()
            self.fillTable()
        else:
            word = "unload"
            if remove:
                word = "remove"
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr(f"You need to select a project to {word} it."), level=1, duration=5
            )

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
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Selected project is currently opened."), level=1, duration=5)
                return
            valid = self.parent.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.openProjectProcess)
        else:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("You need to select a project to open it."), level=1, duration=5)

    def openProjectProcess(self):
        ok, name, project, _ = self.getSelectedRowInfo()
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
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.createProjectProcess)

    def createProjectProcess(self):
        dlg = QGISRedCreateProjectDialog()
        dlg.config(self.iface, "Temporal folder", "Network", self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec_()
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
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.importDataProcess)

    def importDataProcess(self):
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self.parent)
        # Run the dialog event loop
        self.close()
        dlg.exec_()

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

            io = QGISRedProjectIO(project, name, self.iface)
            io.saveFilesInZip(zipPath)
            self.iface.messageBar().pushMessage("QGISRed", self.tr("Zip file stored in: ") + zipPath, level=0, duration=5)
            return
        else:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("You need to select a project to export it."), level=1, duration=5)

    def cloneProject(self):
        ok, mainName, mainFolder, _ = self.getSelectedRowInfo()
        if ok:
            dlg = QGISRedCloneProjectDialog()
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if result:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                self._copyProjectFiles(mainFolder, mainName, dlg.NetworkName, dlg.ProjectDirectory)

                qgisBase = self._getQGisProjectBase(mainFolder, mainName)
                if qgisBase:
                    oldQgisDir = os.path.dirname(qgisBase)
                    newQgisPath = self._copyQGisProjectFiles(qgisBase, dlg.NetworkName, dlg.ProjectDirectory)
                    if newQgisPath:
                        self._updateQGisProjectContent(
                            newQgisPath, mainName, dlg.NetworkName,
                            mainFolder, dlg.ProjectDirectory,
                            oldQgisDir, dlg.ProjectDirectory,
                        )
                        self._updateMetadataQGisProject(dlg.ProjectDirectory, dlg.NetworkName, newQgisPath)
                QApplication.restoreOverrideCursor()

                self.addProjectToTable(dlg.ProjectDirectory, dlg.NetworkName)
        else:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("You need to select a project to clone."), level=1, duration=5)

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
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Current project can not be renamed."), level=1, duration=5)
                return
            qgisBase = self._getQGisProjectBase(projectPath, projectNetwork)
            dlg = QGISRedRenameProjectDialog(None, projectNetwork, projectPath, qgisBase)
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if not result:
                return
            newName = dlg.NetworkName
            QApplication.setOverrideCursor(Qt.WaitCursor)
            oldProjectPath = projectPath
            self.renameFiles(projectPath, projectNetwork, newName)
            newQgisPath = None
            if dlg.RenameQGISProject and qgisBase:
                newQgisPath = self._renameQGisProjectFiles(qgisBase, newName, projectPath)
            if os.path.basename(projectPath) == projectNetwork:
                newProjectPath = os.path.join(os.path.dirname(projectPath), newName)
                try:
                    os.rename(projectPath, newProjectPath)
                    projectPath = self.getUniformedPath(newProjectPath)
                    if newQgisPath:
                        newQgisPath = self.getUniformedPath(newQgisPath.replace(oldProjectPath, projectPath))
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
                    qgisFileToUpdate = self._findQGisProjectFile(renamedBase)
                else:
                    qgisFileToUpdate = None
                    newQgisDir = None
                if qgisFileToUpdate and os.path.exists(qgisFileToUpdate):
                    self._updateQGisProjectContent(qgisFileToUpdate, projectNetwork, newName, oldProjectPath, projectPath, oldQgisDir, newQgisDir)
            self.twProjectList.setItem(rowIndex, 0, QTableWidgetItem(newName))
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
                    self.utils.writeFile(f, newName + ";" + projectPath + "\n")
                i = i + 1
            f.close()

            self.iface.messageBar().pushMessage("QGISRed", self.tr("Project name has been renamed to ") + newName, level=0, duration=5)
        else:
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("You need to select a project to change its name."), level=1, duration=5
            )

    def moveProject(self):
        ok, projectNetwork, projectPath, rowIndex = self.getSelectedRowInfo()
        if not ok:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("You need to select a project to move it."), level=1, duration=5)
            return
        isSameProject = self.getUniformedPath(self.ProjectDirectory) == projectPath
        isSameNet = self.NetworkName == projectNetwork
        if isSameProject and isSameNet:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Current project can not be moved."), level=1, duration=5)
            return

        qgisBase = self._getQGisProjectBase(projectPath, projectNetwork)
        dlg = QGISRedMoveProjectDialog(None, projectPath, projectNetwork, qgisBase)
        dlg.exec_()
        if not dlg.ProcessDone:
            return

        targetDir = self.getUniformedPath(dlg.TargetDirectory)
        QApplication.setOverrideCursor(Qt.WaitCursor)

        oldProjectPath = projectPath
        oldQgisDir = os.path.dirname(qgisBase) if qgisBase else None
        newQgisPath = None

        if dlg.MoveProjectFiles:
            self._moveProjectFiles(projectPath, projectNetwork, targetDir)
            projectPath = targetDir
            self.twProjectList.setItem(rowIndex, 3, QTableWidgetItem(projectPath))

        if dlg.MoveQGISProject and qgisBase:
            newQgisPath = self._moveQGisProjectFiles(qgisBase, targetDir)
            if newQgisPath:
                self._updateMetadataQGisProject(projectPath, projectNetwork, newQgisPath)

        # Update internal layer paths in the QGIS project file.
        # In all cases the .qgz/.qgs must be updated because either the layers moved,
        # the .qgz/.qgs moved (changing relative paths), or both.
        #   A) Both moved   → update the .qgz/.qgs at its new location; layers at new folder
        #   B) Only project files moved → .qgz/.qgs stays in place; layers at new folder
        #   C) Only .qgz/.qgs moved → update the .qgz/.qgs at its new location;
        #                             layers stayed, but relative paths from the new .qgz location changed
        if qgisBase:
            qgisFileMoved = newQgisPath is not None  # True when _moveQGisProjectFiles succeeded
            if qgisFileMoved:
                # Cases A and C: .qgz/.qgs is now at its new location
                qgisFileToUpdate = newQgisPath
                newQgisDir = os.path.dirname(newQgisPath)
            elif dlg.MoveProjectFiles:
                # Case B: layers moved but .qgz/.qgs stayed — update it in place
                qgisFileToUpdate = self._findQGisProjectFile(qgisBase)
                newQgisDir = oldQgisDir  # .qgz/.qgs did not move
            else:
                qgisFileToUpdate = None
                newQgisDir = None
            if qgisFileToUpdate and os.path.exists(qgisFileToUpdate):
                self._updateQGisProjectContent(qgisFileToUpdate, projectNetwork, projectNetwork, oldProjectPath, projectPath, oldQgisDir, newQgisDir)

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
        self.iface.messageBar().pushMessage("QGISRed", self.tr("Project has been moved to ") + targetDir, level=0, duration=5)

    def _copyProjectFiles(self, folder, oldName, newName, targetDir):
        folder = self.getUniformedPath(folder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and f.startswith(oldName + "_"):
                try:
                    destName = f.replace(oldName + "_", newName + "_", 1)
                    copyfile(filepath, os.path.join(targetDir, destName))
                except Exception:
                    pass
            elif os.path.isdir(filepath):
                if f.lower() == "layerstyles":
                    try:
                        destLayerStyles = os.path.join(targetDir, f)
                        if os.path.exists(destLayerStyles):
                            rmtree(destLayerStyles)
                        copytree(filepath, destLayerStyles)
                    except Exception:
                        pass
                else:
                    subTarget = os.path.join(targetDir, f)
                    os.makedirs(subTarget, exist_ok=True)
                    self._copyProjectFiles(filepath, oldName, newName, subTarget)

    def _moveProjectFiles(self, folder, networkName, targetDir):
        folder = self.getUniformedPath(folder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and f.startswith(networkName + "_"):
                try:
                    copyfile(filepath, os.path.join(targetDir, f))
                    os.remove(filepath)
                except Exception:
                    pass
            elif os.path.isdir(filepath):
                if f.lower() == "layerstyles": # Temportal fix
                    try:
                        destLayerStyles = os.path.join(targetDir, f)
                        if os.path.exists(destLayerStyles):
                            rmtree(destLayerStyles)
                        copytree(filepath, destLayerStyles)
                        rmtree(filepath)
                    except Exception:
                        pass
                else:
                    subTarget = os.path.join(targetDir, f)
                    os.makedirs(subTarget, exist_ok=True)
                    self._moveProjectFiles(filepath, networkName, subTarget)
                    try:
                        if not os.listdir(filepath):
                            os.rmdir(filepath)
                    except Exception:
                        pass
        try:
            if folder != self.getUniformedPath(targetDir) and not os.listdir(folder):
                os.rmdir(folder)
        except Exception:
            pass

    def _moveQGisProjectFiles(self, qgisBase, targetDir):
        parentDir = os.path.dirname(qgisBase)
        baseName = os.path.basename(qgisBase)
        newQgisPath = None
        try:
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self._stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(baseName):]
                        newFilepath = os.path.join(targetDir, f)
                        try:
                            copyfile(filepath, newFilepath)
                            os.remove(filepath)
                            if newQgisPath is None and (extensions.startswith(".qgs") or extensions.startswith(".qgz")):
                                newQgisPath = newFilepath
                        except Exception:
                            pass
            try:
                if self.getUniformedPath(parentDir) != self.getUniformedPath(targetDir) and not os.listdir(parentDir):
                    os.rmdir(parentDir)
            except Exception:
                pass
        except Exception:
            pass
        return newQgisPath

    def _copyQGisProjectFiles(self, qgisBase, newName, targetDir):
        """Copies all QGIS project files (.qgs/.qgz and backups) to targetDir,
        renaming them with newName as the prefix. Returns the new .qgz/.qgs path, or None."""
        parentDir = os.path.dirname(qgisBase)
        oldBaseName = os.path.basename(qgisBase)
        newQgisPath = None
        try:
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self._stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(oldBaseName):]
                        newFilepath = os.path.join(targetDir, newName + extensions)
                        try:
                            copyfile(filepath, newFilepath)
                            if newQgisPath is None and (extensions.startswith(".qgs") or extensions.startswith(".qgz")):
                                newQgisPath = newFilepath
                        except Exception:
                            pass
        except Exception:
            pass
        return newQgisPath

    def openFolder(self):
        selectionModel = self.twProjectList.selectionModel()
        if selectionModel.hasSelection():
            for row in selectionModel.selectedRows():
                mainFolder = str(self.twProjectList.item(row.row(), 3).text())
                os.startfile(mainFolder)
        else:
            message = self.tr("You need to select a project to open its folder.")
            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)