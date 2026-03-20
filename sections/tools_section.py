# -*- coding: utf-8 -*-
"""Tools section for QGISRed (lengths, roughness, elevation, demands, scenarios)."""

from PyQt5.QtWidgets import QApplication, QFileDialog
from PyQt5.QtCore import Qt

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed


class ToolsSection:
    """Calculate lengths, set/convert roughness, interpolate elevation, demand sectors, scenario/demands manager."""

    def runDemandsManager(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.getSelectedFeaturesIds()
        ids = ""
        if "Junctions" in self.selectedIds:
            ids = "Junctions:" + str(self.selectedIds["Junctions"]) + ";"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.DemandsManager(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")
        self.selectedFids = {}

    def runScenarioManager(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ScenarioManager(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runCalculateLengths(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CalculateLengths(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runSetRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SetRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runConvertRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ConvertRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runElevationInterpolation(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.ElevationFiles = ""
        qfd = QFileDialog()
        path = ""
        filter = "asc(*.asc)"
        f = QFileDialog.getOpenFileNames(qfd, "Select ASC file", path, filter)
        if not f[1] == "":
            for fil in f[0]:
                self.ElevationFiles = self.ElevationFiles + fil + ";"

            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.ElevationInterpolation(
                self.ProjectDirectory, self.NetworkName, self.tempFolder, self.ElevationFiles
            )
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, self.tr("Any elevation has been estimated"))

    def runDemandSectors(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.Sectors = "DemandSectors"
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.DemandSectors(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        if resMessage == "False":
            pass
        elif resMessage == "shps":
            self.hasToOpenSectorLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.extent = QGISRedUtils().getProjectExtent()
        if self.hasToOpenSectorLayers:
            QGISRedUtils().runTask(self.removeSectorLayers, self.runOpenTemporaryFiles)
