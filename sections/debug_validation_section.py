# -*- coding: utf-8 -*-
"""Debug and validation section for QGISRed (network checks, commit, connectivity, sectors)."""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..ui.debug.qgisred_toolLength_dialog import QGISRedLengthToolDialog
from ..ui.debug.qgisred_toolConnectivity_dialog import QGISRedConnectivityToolDialog


class DebugValidationSection:
    """Commit, overlapping elements, simplify vertices, join pipes, T-connections,
    connectivity, length/diameter/material/date checks, hydraulic sectors."""

    def runCommit(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Commit(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("Input data is valid"))

    def runCheckOverlappingElements(self):
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
        resMessage = GISRed.CheckOverlappingElements(
            self.ProjectDirectory, self.NetworkName, self.tempFolder, self.nodeIds, self.linkIds
        )
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No overlapping elements found"))

    def runSimplifyVertices(self):
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
        resMessage = GISRed.CheckAlignedVertices(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No aligned vertices to delete"))

    def runCheckJoinPipes(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckJoinPipes(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No pipes to join"))

    def runCheckTConncetions(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckTConnections(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No T connections to create"))

    def runCheckConnectivityM(self):
        self.runCheckConnectivity()

    def runCheckConnectivityC(self):
        self.runCheckConnectivity(True)

    def runCheckConnectivity(self, toCommit=False):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        linesToDelete = "0"
        if toCommit:
            dlg = QGISRedConnectivityToolDialog()
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if result:
                linesToDelete = dlg.Lines
            else:
                return

        step = "check"
        if toCommit:
            step = "commit"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckConnectivity(self.ProjectDirectory, self.NetworkName, linesToDelete, step, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenConnectivityLayers = False
        if resMessage == "True":
            self.pushMessage(self.tr("Info"), self.tr("Only one zone"), level=3, duration=5)
        elif resMessage == "False":
            pass
        elif resMessage == "shps":
            self.hasToOpenConnectivityLayers = True
        elif resMessage == "commit/shps":
            self.hasToOpenNewLayers = True
            self.hasToOpenConnectivityLayers = True
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.savedExtent = self.iface.mapCanvas().extent()
        if self.hasToOpenNewLayers and self.hasToOpenConnectivityLayers:
            QGISRedLayerUtils().runTask(self.removeLayersAndConnectivity, self.runOpenTemporaryFiles)
        elif self.hasToOpenConnectivityLayers:
            QGISRedLayerUtils().runTask(self.removeLayersConnectivity, self.runOpenTemporaryFiles)

    def runCheckLengths(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        dlg = QGISRedLengthToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        if dlg.ProcessDone:
            # Process
            if not self.getSelectedFeaturesIds():
                return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.CheckLengths(
                self.ProjectDirectory, self.NetworkName, dlg.Tolerance, self.tempFolder, self.linkIds
            )
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, self.tr("No pipe length out of tolerance"))

    def runCheckDiameters(self):
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
        resMessage = GISRed.CheckDiameters(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.pushMessage(
                self.tr("Info"), self.tr("No issues on diameter checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runCheckMaterials(self):
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
        resMessage = GISRed.CheckMaterials(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.pushMessage(
                self.tr("Info"), self.tr("No issues on materials checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runCheckInstallationDates(self):
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
        resMessage = GISRed.CheckInstallationDates(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.pushMessage(
                self.tr("Info"), self.tr("No issues on installation dates checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runHydraulicSectors(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.Sectors = "HydraulicSectors"
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.HydarulicSectors(self.ProjectDirectory, self.NetworkName, self.tempFolder)
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
            self.pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.savedExtent = self.iface.mapCanvas().extent()
        if self.hasToOpenSectorLayers:
            QGISRedLayerUtils().runTask(self.removeSectorLayers, self.runOpenTemporaryFiles)
