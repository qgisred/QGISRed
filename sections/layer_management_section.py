# -*- coding: utf-8 -*-
"""Layer management section for QGISRed (open/remove layers, groups, metadata, processCsharpResult)."""

import os
import shutil

from qgis.core import QgsProject, QgsVectorLayer
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import Qt

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed


class LayerManagementSection:
    """Open/remove layers, group management, processCsharpResult, metadata, blockLayers."""

    """Remove Layers"""

    def removeLayers(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)

    def removeIssuesLayers(self):
        issuesFolder = os.path.join(self.ProjectDirectory, "Issues")
        utils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)

    def removeLayersAndIssuesLayers(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        issuesFolder = os.path.join(self.ProjectDirectory, "Issues")
        issuesUtils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        issuesUtils.removeLayers(self.issuesLayers)

    def removeIssuesLayersFiles(self):
        issuesFolder = os.path.join(self.ProjectDirectory, "Issues")
        if os.path.exists(issuesFolder):
            for fi in os.listdir(issuesFolder):
                if "_Issues." in fi:
                    os.remove(os.path.join(issuesFolder, fi))
        # Clean up any legacy files in the project root (pre-folder era)
        for fi in os.listdir(self.ProjectDirectory):
            if "_Issues." in fi:
                os.remove(os.path.join(self.ProjectDirectory, fi))

    def removeLayersConnectivity(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")

    def removeLayersAndConnectivity(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")

    def removeSectorLayers(self):
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        utils = QGISRedLayerUtils(queriesFolder, self.NetworkName, self.iface)
        utils.removeLayers(["Links_" + self.Sectors, "Nodes_" + self.Sectors])
        sectorGroupName = self.getSectorGroupName()
        self.removeEmptyQuerySubGroup(sectorGroupName)

    def removeSectorLayersFiles(self):
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        if os.path.exists(queriesFolder):
            for fi in os.listdir(queriesFolder):
                if ("_" + self.Sectors + ".") in fi:
                    os.remove(os.path.join(queriesFolder, fi))

    """Open Layers"""

    def openRemoveSpecificLayers(self, layers, epsg):
        self.especificComplementaryLayers = self.complementaryLayers
        self.specificEpsg = epsg
        self.specificLayers = layers
        self.layerOperationInProgress = True
        QGISRedLayerUtils().runTask(self.removeLayers, self.openSpecificLayers)

    def openSpecificLayers(self):
        self.especificComplementaryLayers = []
        if self.specificEpsg is not None:
            self.runChangeCrs()

        self.opendedLayers = False
        QGISRedLayerUtils().runTask(self.openSpecificLayersProcess, self.setExtent)

    def openSpecificLayersProcess(self):
        if not self.opendedLayers:
            self.opendedLayers = True
            # Open layers
            utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, self.specificLayers)
            self.updateMetadata()
            self.layerOperationInProgress = False

    def openElementLayer(self, nameLayer):
        # Open layers
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputGroup = self.getInputGroup()
        utils.openElementsLayers(inputGroup, [nameLayer])
        self.updateMetadata()

    def openElementLayers(self, net="", folder=""):
        # Allow overriding project/network if provided
        if not net == "" and not folder == "":
            self.NetworkName = net
            self.ProjectDirectory = folder

        # Prepare for opening
        self.opendedLayers = False
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Inputs"])

        for layer_name in self.ownMainLayers + self.especificComplementaryLayers:
            utils.openElementsLayers(inputGroup, [layer_name])

        utils.removeEmptyLayersInGroup(inputGroup)
        # Reset any scenario‑specific list
        self.especificComplementaryLayers = []

        self.updateMetadata()

    def openInputLayers(self, projectDir, networkName):
        # Open layers
        utils = QGISRedLayerUtils(projectDir, networkName, self.iface)
        inputGroup = self.getInputGroup()
        utils.openElementsLayers(inputGroup, self.ownMainLayers)

    def openIssuesLayers(self):
        # Open layers
        issuesFolder = os.path.join(self.ProjectDirectory, "Issues")
        utils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        issuesGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Issues"])
        utils.openIssuesLayers(issuesGroup, self.issuesLayers)

    def openConnectivityLayer(self):
        connFolder = os.path.join(self.ProjectDirectory, "Queries", "Connectivity")
        utils = QGISRedLayerUtils(connFolder, self.NetworkName, self.iface)
        connGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Connectivity"])
        utils.openLayer(connGroup, "Links_Connectivity")

    def openSectorLayers(self):
        sectorFolder = os.path.join(self.ProjectDirectory, "Queries", self.Sectors)
        utils = QGISRedLayerUtils(sectorFolder, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(sectorFolder, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            sectorGroupName = self.getSectorGroupName()
            sectorGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", sectorGroupName])
            utils.openLayer(sectorGroup, "Links_" + self.Sectors, sectors=True)
            utils.openLayer(sectorGroup, "Nodes_" + self.Sectors, sectors=True)
            if self.Sectors == "HydraulicSectors":
                utils.openLayer(sectorGroup, "IsolatedDemands_HydraulicSectors", sectors=True)
                utils.removeEmptyLayersInGroup(sectorGroup, exceptions=[])

    """Groups"""

    def runLegendChanged(self, *args):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if not self.layerOperationInProgress:
            # Validations
            self.defineCurrentProject()
            if self.ProjectDirectory == self.TemporalFolder:
                return

            if not self.checkDependencies():
                return

            self.updateMetadata()

    def activeInputGroup(self):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if self.ResultDockwidget is None:
            return
        try:
            utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            group = utils.getOrCreateGroup("Inputs")
            if group is not None:
                group.setItemVisibilityChecked(not self.ResultDockwidget.isVisible())
            group = utils.getOrCreateGroup("Results")
            if group is not None:
                group.setItemVisibilityChecked(self.ResultDockwidget.isVisible())
        except Exception:
            pass

    def getInputGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Inputs")

    def getQueryGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Queries")

    def getIssuesGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Issues")

    def removeEmptyIssuesGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        root = QgsProject.instance().layerTreeRoot()
        issuesGroup = utils._findGroupByNameRecursive(root, "Issues")
        if issuesGroup is not None:
            if len(issuesGroup.findLayers()) == 0:
                parent = issuesGroup.parent()
                if parent is not None:
                    parent.removeChildNode(issuesGroup)

    def getSectorGroupName(self):
        if self.Sectors == "HydraulicSectors":
            return "Hydraulic Sectors"
        elif self.Sectors == "DemandSectors":
            return "Demand Sectors"
        else:
            return "Sectors"

    def removeEmptyQuerySubGroup(self, name):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        root = QgsProject.instance().layerTreeRoot()
        querySubGroup = utils._findGroupByNameRecursive(root, name)
        if querySubGroup is not None:
            if len(querySubGroup.findLayers()) == 0:
                parent = querySubGroup.parent()
                if parent is not None:
                    parent.removeChildNode(querySubGroup)
        queryGroup = utils._findGroupByNameRecursive(root, "Queries")
        if queryGroup is not None:
            if len(queryGroup.findLayers()) == 0 and len(queryGroup.children()) == 0:
                parent = queryGroup.parent()
                if parent is not None:
                    parent.removeChildNode(queryGroup)

    """Others"""

    def processCsharpResult(self, b, message, layerType="issues", onOpenLayers=None):
        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        self.hasToOpenConnectivityLayers = False
        if b == "True":
            if not message == "":
                self.pushMessage(self.tr(message), level=3, duration=5)
        elif b == "False" or b == "Cancelled":
            pass
        elif b == "commit":
            self.hasToOpenNewLayers = True
        elif b == "shps":
            if layerType == "sectors":
                self.hasToOpenSectorLayers = True
            elif layerType == "connectivity":
                self.hasToOpenConnectivityLayers = True
            else:
                self.hasToOpenIssuesLayers = True
        elif b == "commit/shps":
            self.hasToOpenNewLayers = True
            if layerType == "sectors":
                self.hasToOpenSectorLayers = True
            elif layerType == "connectivity":
                self.hasToOpenConnectivityLayers = True
            else:
                self.hasToOpenIssuesLayers = True
        else:
            self.pushMessage(b, level=2, duration=5)

        if self.hasToOpenNewLayers or self.hasToOpenIssuesLayers or self.hasToOpenSectorLayers or self.hasToOpenConnectivityLayers:
            self.layerOperationInProgress = True
            openFn = onOpenLayers if onOpenLayers else self.runOpenTemporaryFiles
            openFn()
        else:
            self.layerOperationInProgress = False

    def runOpenTemporaryFiles(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        resMessage = GISRed.ReplaceTemporalFiles(self.ProjectDirectory, self.tempFolder)

        if self.hasToOpenIssuesLayers:
            issuesFolder = os.path.join(self.ProjectDirectory, "Issues")
            if not os.path.exists(issuesFolder):
                os.mkdir(issuesFolder)
            for fi in os.listdir(self.ProjectDirectory):
                if "_Issues." in fi:
                    src = os.path.join(self.ProjectDirectory, fi)
                    dst = os.path.join(issuesFolder, fi)
                    # Overwrite in-place so existing QGIS handles remain valid
                    shutil.copy2(src, dst)
                    os.remove(src)

        self.readOptions(self.ProjectDirectory, self.NetworkName)

        if self.hasToOpenNewLayers:
            self.openElementLayers()
            self.setExtent()
            self.openNewLayers = False

        if self.hasToOpenIssuesLayers:
            self.openIssuesLayers()
            self.hasToOpenIssuesLayers = False

        if self.hasToOpenConnectivityLayers:
            connFolder = os.path.join(self.ProjectDirectory, "Queries", "Connectivity")
            os.makedirs(connFolder, exist_ok=True)
            for fi in os.listdir(self.ProjectDirectory):
                if fi.startswith(self.NetworkName) and "Connectivity" in fi:
                    src = os.path.join(self.ProjectDirectory, fi)
                    dst = os.path.join(connFolder, fi)
                    shutil.copy2(src, dst)
                    os.remove(src)
            self.openConnectivityLayer()
            self.hasToOpenConnectivityLayers = False

        if self.hasToOpenSectorLayers:
            sectorFolder = os.path.join(self.ProjectDirectory, "Queries", self.Sectors)
            os.makedirs(sectorFolder, exist_ok=True)
            for fi in os.listdir(self.ProjectDirectory):
                if fi.startswith(self.NetworkName) and "Sectors" in fi:
                    src = os.path.join(self.ProjectDirectory, fi)
                    dst = os.path.join(sectorFolder, fi)
                    # Overwrite in-place so existing QGIS handles remain valid
                    shutil.copy2(src, dst)
                    os.remove(src)
            self.openSectorLayers()
            self.hasToOpenSectorLayers = False

        QApplication.restoreOverrideCursor()
        self.layerOperationInProgress = False
        self.updateMetadata()

        if resMessage == "True":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def getComplementaryLayersOpened(self):
        complementary = []
        groupName = "Inputs"
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
        if dataGroup is not None:
            layers = self.getLayers()
            root = QgsProject.instance().layerTreeRoot()
            for layer in layers:
                if not layer:
                    continue
                parent = root.findLayer(layer.id())
                if parent is not None:
                    if parent.parent().name() == groupName:
                        rutaLayer = self.getLayerPath(layer)
                        layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName + "_", "")
                        if not self.ownMainLayers.__contains__(layerName):
                            complementary.append(layerName)
        return complementary

    def blockLayers(self, readonly):
        layers = self.getLayers()
        for layer in layers:
            # Skip non-vector layers (like rasters or annotation layers)
            if not layer or not isinstance(layer, QgsVectorLayer):
                continue

            layer.setReadOnly(readonly)

