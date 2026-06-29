# -*- coding: utf-8 -*-
"""Layer management section for QGISRed (open/remove layers, groups, metadata, processCsharpResult)."""

import os
import shutil

from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeLayer
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import Qt

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
from ..tools.utils.qgisred_filesystem_utils import (
    DIR_ISSUES, DIR_QUERIES,
    LAYER_TYPE_CONFIG,
)
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
        issuesFolder = os.path.join(self.ProjectDirectory, DIR_ISSUES)
        utils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)

    def removeLayersAndIssuesLayers(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        issuesFolder = os.path.join(self.ProjectDirectory, DIR_ISSUES)
        issuesUtils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        issuesUtils.removeLayers(self.issuesLayers)

    def removeIssuesLayersFiles(self):
        issuesFolder = os.path.join(self.ProjectDirectory, DIR_ISSUES)
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
        utils.removeLayer("Connectivity_Links")
        self.removeEmptyQuerySubGroup("Connectivity")

    def removeLayersAndConnectivity(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayer("Connectivity_Links")
        self.removeEmptyQuerySubGroup("Connectivity")

    def getSectorFolder(self):
        return os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG[self.Sectors]["subdir"])

    def removeSectorLayers(self):
        sectorFolder = self.getSectorFolder()
        utils = QGISRedLayerUtils(sectorFolder, self.NetworkName, self.iface)
        utils.removeLayers([self.Sectors + "_Links", self.Sectors + "_Nodes"])
        sectorGroupName = self.getSectorGroupName()
        self.removeEmptyQuerySubGroup(sectorGroupName)


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
        issuesFolder = os.path.join(self.ProjectDirectory, DIR_ISSUES)
        utils = QGISRedLayerUtils(issuesFolder, self.NetworkName, self.iface)
        issuesGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Issues"])
        utils.openIssuesLayers(issuesGroup, self.issuesLayers)

    def openConnectivityLayer(self):
        cfg = LAYER_TYPE_CONFIG["Connectivity"]
        connFolder = os.path.join(self.ProjectDirectory, cfg["subdir"])
        utils = QGISRedLayerUtils(connFolder, self.NetworkName, self.iface)
        connGroup = utils.getOrCreateNestedGroup([self.NetworkName] + cfg["tree_path"])
        utils.openLayer(connGroup, "Connectivity_Links")

    def openSectorLayers(self):
        cfg = LAYER_TYPE_CONFIG[self.Sectors]
        sectorFolder = os.path.join(self.ProjectDirectory, cfg["subdir"])
        utils = QGISRedLayerUtils(sectorFolder, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(sectorFolder, self.NetworkName + "_" + self.Sectors + "_Links.shp")):
            sectorGroup = utils.getOrCreateNestedGroup([self.NetworkName] + cfg["tree_path"])
            utils.openLayer(sectorGroup, self.Sectors + "_Links", **cfg["flags"])
            utils.openLayer(sectorGroup, self.Sectors + "_Nodes", **cfg["flags"])
            if self.Sectors == "HydraulicSectors":
                utils.openLayer(sectorGroup, "HydraulicSectors_IsolatedDemands", **cfg["flags"])
                utils.removeEmptyLayersInGroup(sectorGroup, exceptions=[])

    def openIsolatedSegmentsLayers(self):
        isoGroup = self.getIsolatedSegmentsGroup()
        isoFolder = os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["IsolatedSegments"]["subdir"])
        utils = QGISRedLayerUtils(isoFolder, self.NetworkName, self.iface)
        utils.openLayer(isoGroup, "IsolatedSegments_Links")
        utils.openLayer(isoGroup, "IsolatedSegments_Nodes")
        utils.openLayer(isoGroup, "IsolatedSegments_IsolatedDemands")

    def getIsolatedSegmentsGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName] + LAYER_TYPE_CONFIG["IsolatedSegments"]["tree_path"])

    def getDemandsBuilderGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName] + LAYER_TYPE_CONFIG["DemandsBuilder"]["tree_path"])

    def openDemandsBuilderLayers(self):
        demandsBuilderGroup = self.getDemandsBuilderGroup()
        isoFolder = os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["DemandsBuilder"]["subdir"])
        utils = QGISRedLayerUtils(isoFolder, self.NetworkName, self.iface)
        identifiers = QGISRedIdentifierUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self._demandsBuilderExtraPaths:
            for path in self._demandsBuilderExtraPaths:
                if not os.path.exists(path):
                    continue
                reloaded_layer = utils._tryReloadExistingLayer(path)
                displayName = os.path.splitext(os.path.basename(path))[0]
                if reloaded_layer:
                    self._applyDemandsBuilderStyle(reloaded_layer)
                    if not reloaded_layer.customProperty("qgisred_identifier"):
                        identifiers.setLayerIdentifier(reloaded_layer, displayName)
                    continue
                vlayer = QgsVectorLayer(path, displayName, "ogr")
                if not vlayer.isValid():
                    continue
                self._applyDemandsBuilderStyle(vlayer)
                identifiers.setLayerIdentifier(vlayer, displayName)
                translatedName = identifiers.getTranslatedNameForIdentifier(vlayer.customProperty("qgisred_identifier"))
                if translatedName:
                    vlayer.setName(translatedName)
                QgsProject.instance().addMapLayer(vlayer, False)
                demandsBuilderGroup.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            self._demandsBuilderExtraPaths = []

    def getDemandSectorsGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup(
            [self.NetworkName] + LAYER_TYPE_CONFIG["DemandSectors"]["tree_path"]
        )


    def getDemandSectorizationGroup(self, sectorizationName):
        demandSectorsGroup = self.getDemandSectorsGroup()

        sectorizationGroup = demandSectorsGroup.findGroup(sectorizationName)
        if sectorizationGroup is None:
            sectorizationGroup = demandSectorsGroup.addGroup(sectorizationName)

        return sectorizationGroup

    def openTreeLayers(self):
        treeGroup = self.getTreeGroup()
        treeFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, "Trees")
        utils = QGISRedLayerUtils(treeFolder, self.NetworkName, self.iface)
        utils.openTreeLayer(treeGroup, "Links", self.treeName, link=True)
        utils.openTreeLayer(treeGroup, "Nodes", self.treeName)

    def getTreeGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        # Use the tree name directly as the final subgroup (no "Tree: " prefix)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Trees", self.treeName])

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
        return LAYER_TYPE_CONFIG.get(self.Sectors, {"tree_path": ["Sectors"]})["tree_path"][-1]

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

    def processCsharpResult(self, b, message, layerType="issues"):
        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        self.hasToOpenConnectivityLayers = False
        self.hasToOpenIsolatedSegmentsLayers = False
        self.hasToOpenDemandsBuilderLayers = False
        self.hasToOpenTreeLayers = False
        self._demandsBuilderExtraPaths = []
        self._demandsBuilderNewBaseDemandFieldName = ""

        def parse_extra_parts(result):
            parts = result.split("^")
            extra_paths = []
            base_demand_field = ""

            if len(parts) > 1:
                extra_paths = [
                    p for p in parts[1].split(";")
                    if p.strip()
                ]

            for part in parts[2:]:
                if part.startswith("baseDemandField="):
                    base_demand_field = part.split("=", 1)[1].strip()

            return extra_paths, base_demand_field

        if b == "True":
            if message != "":
                self.pushMessage(self.tr(message), level=3, duration=5)

        elif b == "False" or b == "Cancelled":
            pass

        elif b == "commit":
            self.hasToOpenNewLayers = True

        elif b.startswith("commit^"):
            self.hasToOpenNewLayers = True

            for part in b.split("^")[1:]:
                if part.startswith("baseDemandField="):
                    self._demandsBuilderNewBaseDemandFieldName = (
                        part.split("=", 1)[1].strip()
                    )

        elif b == "shps":
            if layerType == "sectors":
                self.hasToOpenSectorLayers = True
            elif layerType == "connectivity":
                self.hasToOpenConnectivityLayers = True
            elif layerType == "isolatedSegments":
                self.hasToOpenIsolatedSegmentsLayers = True
            elif layerType == "tree":
                self.hasToOpenTreeLayers = True
            elif layerType == "demandsBuilder":
                self.hasToOpenDemandsBuilderLayers = True
            else:
                self.hasToOpenIssuesLayers = True

        elif b.startswith("commit/shps"):
            self.hasToOpenNewLayers = True

            if layerType == "sectors":
                self.hasToOpenSectorLayers = True
            elif layerType == "connectivity":
                self.hasToOpenConnectivityLayers = True
            elif layerType == "isolatedSegments":
                self.hasToOpenIsolatedSegmentsLayers = True
            elif layerType == "tree":
                self.hasToOpenTreeLayers = True
            elif layerType == "demandsBuilder":
                self.hasToOpenDemandsBuilderLayers = True
                (
                    self._demandsBuilderExtraPaths,
                    self._demandsBuilderNewBaseDemandFieldName
                ) = parse_extra_parts(b)
            else:
                self.hasToOpenIssuesLayers = True

        else:
            self.pushMessage(b, level=2, duration=5)

        if (
            self.hasToOpenNewLayers
            or self.hasToOpenIssuesLayers
            or self.hasToOpenSectorLayers
            or self.hasToOpenConnectivityLayers
            or self.hasToOpenIsolatedSegmentsLayers
            or self.hasToOpenTreeLayers
            or self.hasToOpenDemandsBuilderLayers
        ):
            self.layerOperationInProgress = True
            self.runOpenTemporaryFiles()
        else:
            self.layerOperationInProgress = False

        self._staleLayerManager.forceCheck()

    def runOpenTemporaryFiles(self):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

        activeLayerId = self.iface.activeLayer().id() if self.iface.activeLayer() else None

        resMessage = GISRed.ReplaceTemporalFiles(self.ProjectDirectory, self.tempFolder)

        if self.hasToOpenIssuesLayers:
            issuesFolder = os.path.join(self.ProjectDirectory, DIR_ISSUES)
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
            connFolder = os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["Connectivity"]["subdir"])
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
            sectorFolder = self.getSectorFolder()
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

        if self.hasToOpenIsolatedSegmentsLayers:
            isoFolder = os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["IsolatedSegments"]["subdir"])
            os.makedirs(isoFolder, exist_ok=True)
            for fi in os.listdir(self.ProjectDirectory):
                if fi.startswith(self.NetworkName) and "IsolatedSegments" in fi:
                    src = os.path.join(self.ProjectDirectory, fi)
                    dst = os.path.join(isoFolder, fi)
                    shutil.copy2(src, dst)
                    os.remove(src)
            self.openIsolatedSegmentsLayers()
            self.hasToOpenIsolatedSegmentsLayers = False

        if self.hasToOpenDemandsBuilderLayers:
            isoFolder = os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["DemandsBuilder"]["subdir"])
            os.makedirs(isoFolder, exist_ok=True)
            auxFolder = os.path.join(self.ProjectDirectory, "_aux_DemandsBuilder")
            if os.path.isdir(auxFolder):
                extraByName = {os.path.splitext(os.path.basename(p))[0]: os.path.dirname(p) for p in self._demandsBuilderExtraPaths}
                for fi in os.listdir(auxFolder):
                    dstDir = extraByName.get(os.path.splitext(fi)[0])
                    if dstDir:
                        shutil.copy2(os.path.join(auxFolder, fi), os.path.join(dstDir, fi))
                shutil.rmtree(auxFolder)
            # Old code to remove...
            for fi in os.listdir(self.ProjectDirectory):
                if fi.startswith(self.NetworkName) and "DemandsBuilder" in fi:
                    src = os.path.join(self.ProjectDirectory, fi)
                    dst = os.path.join(isoFolder, fi)
                    shutil.copy2(src, dst)
                    os.remove(src)
            # --------
            self.openDemandsBuilderLayers()
            self.hasToOpenDemandsBuilderLayers = False

        if self.hasToOpenTreeLayers:
            treeFolder = os.path.join(self.ProjectDirectory, DIR_QUERIES, "Trees")
            os.makedirs(treeFolder, exist_ok=True)

            auxTreeFolder = os.path.join(self.ProjectDirectory, "_aux_Trees")

            if os.path.isdir(auxTreeFolder):
                for fi in os.listdir(auxTreeFolder):
                    src = os.path.join(auxTreeFolder, fi)
                    dst = os.path.join(treeFolder, fi)
                    shutil.copy2(src, dst)

                shutil.rmtree(auxTreeFolder)

            self.openTreeLayers()
            self.hasToOpenTreeLayers = False

        if activeLayerId:
            activeLayer = QgsProject.instance().mapLayer(activeLayerId)
            if activeLayer:
                self.iface.setActiveLayer(activeLayer)

        QApplication.restoreOverrideCursor()
        self.layerOperationInProgress = False
        self.updateMetadata()

        if resMessage == "True":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def getComplementaryLayersOpened(self):
        complementary = []
        inputGroup = self.getInputGroup()
        if inputGroup is None:
            return complementary
        for child in inputGroup.children():
            layer = child.layer() if hasattr(child, "layer") else None
            if layer is None:
                continue
            rutaLayer = self.getLayerPath(layer)
            layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName + "_", "")
            if layerName not in self.ownMainLayers:
                complementary.append(layerName)
        return complementary

    def blockLayers(self, readonly):
        layers = self.getLayers()
        for layer in layers:
            # Skip non-vector layers (like rasters or annotation layers)
            if not layer or not isinstance(layer, QgsVectorLayer):
                continue

            layer.setReadOnly(readonly)

