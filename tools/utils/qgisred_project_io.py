# -*- coding: utf-8 -*-
import os
import datetime
import json
from zipfile import ZipFile
from xml.etree import ElementTree  # nosec B314 — parses local project files only, no external input

from PyQt5.QtCore import QCoreApplication, QFileInfo
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsVectorLayer,
    QgsLayerDefinition
)


class QGISRedProjectIO:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def tr(self, message):
        return QCoreApplication.translate("InputLayerNames", message)

    def _fs(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _styling(self):
        from .qgisred_styling_utils import QGISRedStylingUtils
        return QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _layers(self):
        from .qgisred_layer_utils import QGISRedLayerUtils
        return QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)

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
                            self.tr("QGISRed project"),
                            self.tr("We cannot find the qgis project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group."),
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
                self.iface.messageBar().pushMessage("Warning", "File not found", level=1, duration=5)

    def saveFilesInZip(self, zipPath):
        fs = self._fs()
        filePaths = []
        for f in os.listdir(self.ProjectDirectory):
            filepath = os.path.join(self.ProjectDirectory, f)
            if os.path.isfile(filepath):
                filePaths.append(fs.getUniformedPath(filepath))

        with ZipFile(zipPath, "w") as zipFile:
            for file in filePaths:
                if fs.getUniformedPath(self.ProjectDirectory) + "\\" + self.NetworkName + "_" in file:
                    zipFile.write(file, file.replace(fs.getUniformedPath(self.ProjectDirectory), ""))

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
