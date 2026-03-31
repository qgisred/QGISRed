# -*- coding: utf-8 -*-
import os
import datetime
import json
import shutil
import tempfile
import re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree  # nosec B314 — parses local project files only, no external input
import urllib.parse

from PyQt5.QtCore import QCoreApplication, QFileInfo
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsVectorLayer,
    QgsLayerDefinition
)
from .qgisred_ui_utils import QGISRedUIUtils


class QGISRedProjectIO:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    """Interal Helpers"""
    def _tr(self, message):
        return QCoreApplication.translate("QGISRedProjectIO", message)

    def _fs(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _styling(self):
        from .qgisred_styling_utils import QGISRedStylingUtils
        return QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _layers(self):
        from .qgisred_layer_utils import QGISRedLayerUtils
        return QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _applyQGisReplacements(self, content, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None, collectExternal=False):
        """Standard path replacement in QGIS project XML. 
        If collectExternal is True, it will also copy external layers to newFolder/ExternalLayers."""
        oldFolderNorm = os.path.normcase(os.path.normpath(oldFolder))
        newFolderNorm = os.path.normpath(newFolder)
        externalLayersDir = os.path.join(newFolderNorm, "ExternalLayers")
        
        def replacePathInValue(val):
            # QGIS paths in XML can be URL-encoded and might start with file://
            val = urllib.parse.unquote(val)
            if val.startswith('file:///'):
                val = val[8:]
            elif val.startswith('file://'):
                val = val[7:]
            
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
            if absPath.startswith(oldFolderNorm):
                # ... internal layer logic ...
                suffix = absPath[len(oldFolderNorm):]
                newAbsPath = newFolderNorm + suffix
                head, tail = os.path.split(newAbsPath)
                oldNamePrefix = oldName + '_'
                newNamePrefix = newName + '_'
                isStandardProjectFile = os.path.basename(absPath).startswith(oldNamePrefix)
                
                if not isStandardProjectFile and os.path.isfile(absPath) and oldFolderNorm != os.path.normcase(newFolderNorm):
                    try:
                        os.makedirs(head, exist_ok=True)
                        # Copy file and companions
                        basePath = self.stripAllExtensions(absPath)
                        parent = os.path.dirname(absPath)
                        for f in os.listdir(parent):
                            current_file_path = os.path.join(parent, f)
                            if os.path.normcase(self.stripAllExtensions(current_file_path)) == os.path.normcase(basePath):
                                shutil.copy2(current_file_path, os.path.join(head, f))
                    except Exception:
                        pass

                if oldName != newName:
                    tail = tail.replace(oldNamePrefix, newNamePrefix)
                newAbsPath = os.path.join(head, tail)
                
                # Use relative path if the original was relative OR if we are exporting (collectExternal=True)
                if wasRelative or collectExternal:
                    rel = os.path.relpath(newAbsPath, newQgisDir if newQgisDir else oldQgisDir)
                    return rel.replace('\\', '/')
                else:
                    return newAbsPath.replace('\\', '/')
            
            # If it's external and we want to collect it:
            if collectExternal:
                # Check if it's a local file
                cleanPath = absPath
                if '|' in cleanPath:
                    cleanPath = cleanPath.split('|')[0]
                
                if os.path.isfile(cleanPath):
                    os.makedirs(externalLayersDir, exist_ok=True)
                    basePath = self.stripAllExtensions(cleanPath)
                    parent = os.path.dirname(cleanPath)
                    try:
                        for f in os.listdir(parent):
                            current_file_path = os.path.join(parent, f)
                            if os.path.normcase(self.stripAllExtensions(current_file_path)) == os.path.normcase(basePath):
                                shutil.copy2(current_file_path, os.path.join(externalLayersDir, f))
                    except Exception:
                        pass
                    
                    suffix = ""
                    if '|' in absPath:
                        suffix = absPath[absPath.find('|'):]
                        
                    newExternalPath = os.path.join(externalLayersDir, os.path.basename(cleanPath)) + suffix
                    
                    # When collecting external layers (export), the path MUST be relative to the project
                    # to ensure the ZIP is portable.
                    rel = os.path.relpath(newExternalPath, newQgisDir if newQgisDir else oldQgisDir)
                    return rel.replace('\\', '/')

            # If it's external and we don't want to collect it, we might still 
            # need to update the relative path if the original was relative.
            if not collectExternal and wasRelative:
                targetQgisDir = newQgisDir if newQgisDir else oldQgisDir
                try:
                    rel = os.path.relpath(absPath, targetQgisDir)
                    return rel.replace('\\', '/')
                except ValueError:
                    # Occurs if on different drives on Windows
                    pass

            return val

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

        if oldName != newName:
            content = content.replace(oldName + '_', newName + '_' )
            content = content.replace('value="qgisred_' + oldName + '"', 'value="qgisred_' + newName + '"')
            content = content.replace('name="' + oldName + '"', 'name="' + newName + '"')

        return content

    """File Helpers"""
    def stripAllExtensions(self, path):
        """Strips all extensions from a path (e.g. 'foo.qgz.bak' -> 'foo')."""
        while True:
            base, ext = os.path.splitext(path)
            if not ext:
                break
            path = base
        return path

    def getQGisProjectBase(self, folder, networkName):
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
                    return self.stripAllExtensions(self._fs().getUniformedPath(qgisPath))
        except Exception:
            pass
        return None

    def findQGisProjectFile(self, qgisBase):
        """Returns the full path to the .qgs/.qgz file for a given base path."""
        if not qgisBase:
            return None
        if os.path.exists(qgisBase + ".qgz"):
            return qgisBase + ".qgz"
        if os.path.exists(qgisBase + ".qgs"):
            return qgisBase + ".qgs"
        return None

    def processProjectFiles(self, folder, oldName, newName, targetDir, deleteSource=False):
        """Copies/moves project files (oldName_*) and layerStyles recursively to targetDir."""
        folder = self._fs().getUniformedPath(folder)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir, exist_ok=True)
            
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and f.startswith(oldName + "_"):
                try:
                    destName = f.replace(oldName + "_", newName + "_", 1)
                    shutil.copy2(filepath, os.path.join(targetDir, destName))
                    if deleteSource:
                        os.remove(filepath)
                except Exception:
                    pass
            elif os.path.isdir(filepath):
                if f.lower() == "layerstyles":
                    try:
                        destLayerStyles = os.path.join(targetDir, f)
                        if self._fs().getUniformedPath(filepath) != self._fs().getUniformedPath(destLayerStyles):
                            if os.path.exists(destLayerStyles):
                                shutil.rmtree(destLayerStyles)
                            shutil.copytree(filepath, destLayerStyles)
                            if deleteSource:
                                shutil.rmtree(filepath)
                    except Exception:
                        pass
                else:
                    subTarget = os.path.join(targetDir, f)
                    if self._fs().getUniformedPath(folder) != self._fs().getUniformedPath(targetDir):
                         os.makedirs(subTarget, exist_ok=True)
                    self.processProjectFiles(filepath, oldName, newName, subTarget, deleteSource)
                    if deleteSource:
                        try:
                            if not os.listdir(filepath):
                                os.rmdir(filepath)
                        except Exception:
                            pass
        if deleteSource:
            try:
                if self._fs().getUniformedPath(folder) != self._fs().getUniformedPath(targetDir) and not os.listdir(folder):
                    os.rmdir(folder)
            except Exception:
                pass

    def processQGisProjectFiles(self, qgisBase, newName, targetDir, deleteSource=False):
        """Copies/moves QGIS project files (.qgz/.qgs and backups) to targetDir.
        Returns the new relative path of the .qgz/.qgs file."""
        parentDir = os.path.dirname(qgisBase)
        oldBaseName = os.path.basename(qgisBase)
        newQgisPath = None
        try:
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self.stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(oldBaseName):]
                        newFilepath = os.path.join(targetDir, newName + extensions)
                        try:
                            shutil.copy2(filepath, newFilepath)
                            if deleteSource:
                                os.remove(filepath)
                            if newQgisPath is None and (f.endswith(".qgs") or f.endswith(".qgz")):
                                newQgisPath = newFilepath
                        except Exception:
                            pass
            if deleteSource:
                try:
                    if self._fs().getUniformedPath(parentDir) != self._fs().getUniformedPath(targetDir) and not os.listdir(parentDir):
                        os.rmdir(parentDir)
                except Exception:
                    pass
        except Exception:
            pass
        return newQgisPath

    def updateQGisProjectContent(self, qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None, collectExternal=False):
        """Updates internal project references."""
        try:
            if qgisPath.endswith('.qgz'):
                files = {}
                with ZipFile(qgisPath, 'r') as zin:
                    for name in zin.namelist():
                        files[name] = zin.read(name)
                for name in list(files.keys()):
                    if name.endswith('.qgs'):
                        xml = files[name].decode('utf-8')
                        xml = self._applyQGisReplacements(xml, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir, collectExternal)
                        files[name] = xml.encode('utf-8')
                with ZipFile(qgisPath, 'w', ZIP_DEFLATED) as zout:
                    for name, data in files.items():
                        zout.writestr(name, data)
            elif qgisPath.endswith('.qgs'):
                with open(qgisPath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = self._applyQGisReplacements(content, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir, collectExternal)
                with open(qgisPath, 'w', encoding='utf-8') as f:
                    f.write(content)
        except Exception:
            pass

    """Methods"""
    def updateMetadataQGisProject(self, projectPath, networkName, newQgisPath):
        """Updates the <QGisProject> node in the metadata file."""
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

    def openProjectInQgis(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, "r", encoding="latin-1") as contentFile:
                data = contentFile.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for qgs in root.findall("./ThirdParty/QGISRed/QGisProject"):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    qgisPath = finfo.filePath()
                    if not os.path.isfile(qgisPath):  # Create absolute path
                        currentDirectory = os.getcwd()
                        os.chdir(self.ProjectDirectory)
                        qgisPath = os.path.abspath(qgisPath)
                        os.chdir(currentDirectory)

                    if os.path.exists(qgisPath):
                        QgsProject.instance().read(qgisPath)
                    else:
                        request = QMessageBox.question(
                            self.iface.mainWindow(),
                            self._tr("QGISRed project"),
                            self._tr("We cannot find the qgis project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group."),
                            QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                        )
                        if request == QMessageBox.Yes:
                            qfd = QFileDialog()
                            filter = "qgz(*.qgz)"
                            f = QFileDialog.getOpenFileName(qfd, "Select QGis file", "", filter)
                            qgisPath = f[0]
                            if not qgisPath == "":
                                QgsProject.instance().read(qgisPath)
                        else:
                            layers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
                            self._layers().openGroupLayers("Inputs", layers)
                    return
            for groups in root.findall("./ThirdParty/QGISRed/Groups"):
                for group in groups:
                    groupName = group.tag
                    layers = []
                    for lay in group.iter("Layer"):
                        layers.append(lay.text)
                    self._layers().openGroupLayers(groupName, layers)

        else:  # old file
            gqpFilename = os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")
            if os.path.exists(gqpFilename):
                f = open(gqpFilename, "r")
                lines = f.readlines()
                qgsFile = lines[2]
                if ".qgs" in qgsFile or ".qgz" in qgsFile:
                    finfo = QFileInfo(qgsFile)
                    QgsProject.instance().read(finfo.filePath())
                else:
                    styling = self._styling()
                    group = None
                    for i in range(2, len(lines)):
                        if "[" in lines[i]:
                            groupName = str(lines[i].strip("[").strip("\r\n").strip("]")).replace(self.NetworkName + " ", "")
                            root = QgsProject.instance().layerTreeRoot()
                            netGroup = root.insertGroup(0, self.NetworkName)
                            group = netGroup.insertGroup(0, groupName)
                        else:
                            layerPath = lines[i].strip("\r\n")
                            if not os.path.exists(layerPath):
                                continue
                            vlayer = None
                            layerName = os.path.splitext(os.path.basename(layerPath))[0].replace(self.NetworkName + "_", "")
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
                                    styling.setStyle(vlayer, nameLayer.lower())
            else:
                QGISRedUIUtils.showGlobalMessage(self.iface, "Warning", "File not found", level=1, duration=5)

    """Zip"""
    def saveFilesInZip(self, zipPath):
        fs = self._fs()
        filePaths = []
        for f in os.listdir(self.ProjectDirectory):
            filepath = os.path.join(self.ProjectDirectory, f)
            if os.path.isfile(filepath):
                filePaths.append(fs.getUniformedPath(filepath))

        with ZipFile(zipPath, "w", ZIP_DEFLATED) as zipFile:
            for file in filePaths:
                if self._fs().getUniformedPath(self.ProjectDirectory) + os.sep + self.NetworkName + "_" in file:
                    zipFile.write(file, file.replace(self._fs().getUniformedPath(self.ProjectDirectory), ""))

    def exportProjectToZip(self, zipPath):
        """Comprehensive export of the project to a ZIP file."""
        with tempfile.TemporaryDirectory() as tempDir:
            # 1. Copy project files (no rename, no delete)
            self.processProjectFiles(self.ProjectDirectory, self.NetworkName, self.NetworkName, tempDir, deleteSource=False)
            
            # 2. Handle QGIS project
            qgisBase = self.getQGisProjectBase(self.ProjectDirectory, self.NetworkName)
            if qgisBase:
                oldQgisDir = os.path.dirname(qgisBase)
                relQgisDir = os.path.relpath(oldQgisDir, self.ProjectDirectory)
                targetQgisDir = os.path.normpath(os.path.join(tempDir, relQgisDir))
                os.makedirs(targetQgisDir, exist_ok=True)
                
                newQgisPath = self.processQGisProjectFiles(qgisBase, self.NetworkName, targetQgisDir, deleteSource=False)
                if newQgisPath:
                    self.updateQGisProjectContent(
                        newQgisPath, self.NetworkName, self.NetworkName,
                        self.ProjectDirectory, tempDir,
                        oldQgisDir, targetQgisDir,
                        collectExternal=True
                    )
                    self.updateMetadataQGisProject(tempDir, self.NetworkName, newQgisPath)
            
            # 3. ZIP everything in tempDir
            zipDir = os.path.dirname(zipPath)
            if not os.path.exists(zipDir):
                os.makedirs(zipDir, exist_ok=True)
                
            with ZipFile(zipPath, "w", ZIP_DEFLATED) as zout:
                for root, dirs, files in os.walk(tempDir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, tempDir)
                        zout.write(full_path, rel_path)

    def unzipFile(self, zipfile, directory):
        with ZipFile(zipfile, "r") as zipRef:
            zipRef.extractall(directory)

    def saveBackup(self):
        dirpath = os.path.join(self.ProjectDirectory, "backups")
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except Exception:
                pass

        timeString = datetime.datetime.now().timestamp()
        zipPath = os.path.join(dirpath, self.NetworkName + "_" + str(timeString) + ".zip")

        self.saveFilesInZip(zipPath)
        return zipPath

    """QLR Operations"""
    def getProjectGuid(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            try:
                with open(metadataFile, "r", encoding="latin-1") as f:
                    data = f.read()
                root = ElementTree.fromstring(data)
                guidNode = root.find("Guid")
                if guidNode is not None and guidNode.text:
                    return guidNode.text
            except Exception:
                pass
        return self.NetworkName

    def getQLRFolder(self):
        qlrFolder = os.path.join(self._fs().getQGISRedFolder(), "qlr")
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)
        return qlrFolder

    def saveProjectAsQLR(self):
        qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)

        savedCount = 0
        layers = self._layers().getLayers()
        root = QgsProject.instance().layerTreeRoot()
        layerMeta = {}

        for layer in layers:
            identifier = layer.customProperty("qgisred_identifier")
            if not identifier:
                continue

            layerNode = root.findLayer(layer.id())
            if not layerNode:
                continue

            parent = layerNode.parent()
            groupPath = []
            current = parent
            while current and current != root:
                groupPath.insert(0, current.name())
                current = current.parent()

            position = 0
            if parent:
                for i, child in enumerate(parent.children()):
                    if child == layerNode:
                        position = i
                        break

            layerMeta[identifier] = {
                "group_path": groupPath,
                "position": position,
                "name": layer.name()
            }

            qlrFilename = f"{identifier}.qlr"
            qlrPath = os.path.join(qlrFolder, qlrFilename)

            try:
                success = QgsLayerDefinition.exportLayerDefinition(qlrPath, [layerNode])
                if success:
                    savedCount += 1
            except Exception:
                continue

        if savedCount > 0:
            metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
            with open(metadataPath, 'w') as f:
                json.dump(layerMeta, f, indent=2)

        return (savedCount > 0, qlrFolder)

    def loadProjectFromQLR(self, qlrFolder=None):
        if qlrFolder is None:
            qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())

        if not os.path.exists(qlrFolder):
            return False

        qlrFiles = [f for f in os.listdir(qlrFolder) if f.endswith('.qlr')]
        if not qlrFiles:
            return False

        layerMeta = {}
        metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
        if os.path.exists(metadataPath):
            with open(metadataPath, 'r') as f:
                layerMeta = json.load(f)

        self._layers().removePluginLayers()

        loadedLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for qlrFile in qlrFiles:
            qlrPath = os.path.join(qlrFolder, qlrFile)
            identifier = qlrFile.replace('.qlr', '')

            try:
                success = QgsLayerDefinition().loadLayerDefinition(
                    qlrPath,
                    QgsProject.instance(),
                    root
                )
                if success:
                    for layer in self._layers().getLayers():
                        if layer.customProperty("qgisred_identifier") == identifier:
                            loadedLayers.append((layer, identifier))
                            break
            except Exception:
                continue

        for layer, identifier in loadedLayers:
            metadata = layerMeta.get(identifier, {})
            groupPath = metadata.get("group_path", [])
            position = metadata.get("position", 0)

            targetGroup = root
            for groupName in groupPath:
                existingGroup = targetGroup.findGroup(groupName)
                if existingGroup:
                    targetGroup = existingGroup
                else:
                    targetGroup = targetGroup.insertGroup(0, groupName)

            layerNode = root.findLayer(layer.id())
            if layerNode and targetGroup != root:
                clonedNode = layerNode.clone()
                numChildren = len(targetGroup.children())
                insertPos = min(position, numChildren)
                targetGroup.insertChildNode(insertPos, clonedNode)

                if layerNode.parent():
                    layerNode.parent().removeChildNode(layerNode)

        return len(loadedLayers) > 0

    def deleteProjectQLR(self, qlrFolder=None):
        if qlrFolder is None:
            qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())

        if not os.path.exists(qlrFolder):
            return False

        deletedAny = False

        for filename in os.listdir(qlrFolder):
            if filename.endswith('.qlr') or filename == 'layer_metadata.json':
                try:
                    os.remove(os.path.join(qlrFolder, filename))
                    deletedAny = True
                except Exception:
                    pass

        try:
            if not os.listdir(qlrFolder):
                os.rmdir(qlrFolder)
        except Exception:
            pass

        return deletedAny

    def addProjectToGplFile(self, gplFile, networkName='', projectDirectory='', rawEntryLine=None):
        projectDirectory = self._fs().getUniformedPath(projectDirectory)
        newEntry = rawEntryLine or f"{networkName};{projectDirectory}"
        newEntry = newEntry.strip()

        existingEntries = []
        if os.path.exists(gplFile):
            with open(gplFile, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line != newEntry:
                        existingEntries.append(line)

        with open(gplFile, "w") as f:
            f.write(newEntry + "\n")
            for entry in existingEntries:
                f.write(entry + "\n")
