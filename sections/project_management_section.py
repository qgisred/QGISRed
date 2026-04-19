# -*- coding: utf-8 -*-
"""Project management section for QGISRed (define project, open/create/import, settings, backup)."""

import os

from qgis.core import QgsProject, QgsVectorLayer, QgsLayerTreeLayer
from qgis.PyQt.QtWidgets import QApplication, QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, QCoreApplication, QTimer
from ..compat import QAction

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
from ..tools.utils.qgisred_project_io import QGISRedProjectIO
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..ui.general.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
from ..ui.general.qgisred_createproject_dialog import QGISRedCreateProjectDialog
from ..ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog
from ..ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from ..ui.general.qgisred_import_dialog import QGISRedImportDialog
from ..ui.general.qgisred_loadproject_dialog import QGISRedImportProjectDialog


class ProjectManagementSection:
    """Define/validate project, open/create/import/close project, settings, CRS, backup."""

    def defineCurrentProject(self):
        """Identifying the QGISRed current project"""
        self.NetworkName = "Network"
        self.ProjectDirectory = self.TemporalFolder
        layerName = "Pipes"
        layers = self.getLayers()
        for layer in layers:
            layerUri = self.getLayerPath(layer)
            if "_" + layerName in layerUri:
                self.ProjectDirectory = os.path.dirname(layerUri)
                fileNameWithoutExt = os.path.splitext(os.path.basename(layerUri))[0]
                self.NetworkName = fileNameWithoutExt.replace("_" + layerName, "")

    def isOpenedProject(self, push_fn=None):
        if push_fn is None:
            push_fn = lambda msg, level=0, duration=5: self.pushMessage(msg, level=level, duration=duration)
        layers = self.getLayers()
        for layer in layers:
            if layer.isEditable():
                push_fn(
                    self.tr("Some layer is in Edit Mode. Plase, commit it before continuing."), level=1, duration=5
                )
                return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                push_fn(
                    self.tr("The project has changes. Please save them before continuing."), level=1, duration=5
                )
                return False
            else:
                # Close project and continue?
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("Open project"),
                    self.tr("Do you want to close the current project and continue?"),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers()) > 0:
                # Close files and continue?
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("Open layers"),
                    self.tr("Do you want to close the current layers and continue?"),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def validateProject(self, action):
        # Validates dependencies and project, unchecks action on failure
        if not self.checkDependencies():
            action.setChecked(False)
            return False
        self.defineCurrentProject()
        if not self.isValidProject() or self.isLayerOnEdition():
            action.setChecked(False)
            return False
        return True

    def isValidProject(self):
        if self.ProjectDirectory == self.TemporalFolder:
            self.pushMessage(self.tr("No valid project is opened"), level=1, duration=5)
            return False
        return True

    def isLayerOnEdition(self):
        layers = self.getLayers()
        for layer in layers:
            # Skip non-vector layers (like rasters or annotation layers)
            if not isinstance(layer, QgsVectorLayer):
                continue

            if layer.customProperty("qgisred_identifier") and layer.isEditable():
                message = "Some layer is in Edit Mode. Please, commit it before continuing."
                self.pushMessage(self.tr(message), level=1)
                return True

        return False


    def runOpenedQgisProject(self):
        # Reset the unloading flag since we're opening a new project
        self.isUnloading = False
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            return

        self.readOptions(self.ProjectDirectory, self.NetworkName)

        # Snapshot which layers lack a QGISRed identifier BEFORE assignLayerIdentifiers
        # runs — this is how we detect old projects where identifiers were never saved.
        style_snapshot = self._collectStyleSnapshot()

        identifiers = QGISRedIdentifierUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        identifiers.assignLayerIdentifiers()

        QGISRedProjectIO().addProjectToGplFile(self.gplFile, self.NetworkName, self.ProjectDirectory)

        root = QgsProject.instance().layerTreeRoot()
        inputs_group = root.findGroup("Inputs")

        if inputs_group:
            for child in inputs_group.children():
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer:
                        identifier = layer.customProperty("qgisred_identifier")
                        translatedName = identifiers.getTranslatedNameForIdentifier(identifier)
                        if translatedName and layer.name() != translatedName:
                            layer.setName(translatedName)

        # Defer style application to after QgsProject.read() fully unwinds —
        # calling setLegend() during readProject signal crashes QGIS 4.
        QTimer.singleShot(0, lambda: self._applyStyleUpdates(style_snapshot))

    def suggestQgsProjectFilename(self):
        """If a valid QGISRed project is open and the QGIS project has no filename yet,
        set the last project directory so the native Save As dialog opens there by default."""
        if self.ProjectDirectory != self.TemporalFolder and not QgsProject.instance().fileName():
            from qgis.core import QgsSettings
            QgsSettings().setValue("UI/lastProjectDir", self.ProjectDirectory)

    def clearQGisProject(self):
        QgsProject.instance().clear()

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.updateMetadata()
            self.pushMessage(self.tr("Map project saved"), level=0, duration=5)

    def runClearedProject(self):
        # Set flag to prevent DLL calls during shutdown
        self.isUnloading = False

        # Invalidate the DLL instance
        self.gisredDll = None

        # Deactivate all map tools to prevent callbacks during cleanup
        try:
            if hasattr(self, 'myMapTools'):
                for tool_name, tool in list(self.myMapTools.items()):
                    try:
                        if tool is not None:
                            if self.iface.mapCanvas().mapTool() is tool:
                                self.iface.mapCanvas().unsetMapTool(tool)
                            tool.deactivate()
                    except Exception:
                        pass
                self.myMapTools.clear()
        except Exception:
            pass

        # Disconnect and close all dock widgets
        self.cleanupDocks()


    """Read/Write methods"""
    def readOptions(self, folder="", network=""):
        if folder == "" and network == "":
            self.defineCurrentProject()
        units = "LPS"
        headloss = "D-W"
        qualityModel = "Chemical"
        concentrationUnits = "mg/L"
        statistics = "None"
        if self.ProjectDirectory == "Temporal Folder":
            return
        dbf = QgsVectorLayer(os.path.join(self.ProjectDirectory, self.NetworkName + "_Options.dbf"), "Options", "ogr")
        for feature in dbf.getFeatures():
            attrs = feature.attributes()
            if attrs[1].upper() == "UNITS":
                units = attrs[2]
            if attrs[0].upper() == "HYDRAULICS" and attrs[1].upper() == "HEADLOSS":
                headloss = attrs[2]
            if attrs[1].upper() == "QUALITY TYPE":
                qualityModel = attrs[2]
            if attrs[1].upper() == "CONCENTRATION UNITS":
                concentrationUnits = attrs[2]
            if attrs[1].upper() == "STATISTIC":
                statistics = attrs[2]

        QgsProject.instance().writeEntry("QGISRed", "project_units", units)
        QgsProject.instance().writeEntry("QGISRed", "project_headloss", headloss)
        QgsProject.instance().writeEntry("QGISRed", "project_qualitymodel", qualityModel)
        QgsProject.instance().writeEntry("QGISRed", "project_concentrationunits", concentrationUnits)
        QgsProject.instance().writeEntry("QGISRed", "project_statistics", statistics)

        del dbf

        self.setUnits()

    def setUnits(self):
        units = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")[0]
        headloss = QgsProject.instance().readEntry("QGISRed", "project_headloss", "D-W")[0]
        self.unitsAction.setText("QGISRed: " + units + " | " + headloss)

    def updateMetadata(self, layersNames="", project="", net=""):
        if not self.checkDependencies():
            return

        # Validations
        if project == "" and net == "":  # Comes from ProjectManager
            self.defineCurrentProject()
            if not self.isValidProject():
                return
            project = self.ProjectDirectory
            net = self.NetworkName

        if layersNames == "":
            qgsFilename = QgsProject.instance().fileName()
            if not qgsFilename == "":
                layersNames = os.path.relpath(qgsFilename, project)
            else:
                layers = self.getLayers()
                # Inputs
                groupName = "Inputs"
                dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
                if dataGroup is not None:
                    layersNames = layersNames + "[Inputs]"
                    layersNames = layersNames + self.writeLayersOfGroups(groupName, layers)
                    layersNames = layersNames.strip(";")

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        GISRed.UpdateMetadata(project, net, layersNames)
        QApplication.restoreOverrideCursor()

    def writeLayersOfGroups(self, groupName, layers):
        root = QgsProject.instance().layerTreeRoot()
        paths = ""
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if parent is not None:
                if parent.parent().name() == groupName:
                    rutaLayer = self.getLayerPath(layer)
                    layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName + "_", "")
                    paths = paths + layerName + ";"
        return paths

    def runChangeCrs(self):
        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ChangeCrs(self.ProjectDirectory, self.NetworkName, self.specificEpsg)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            pass
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.pushMessage(resMessage, level=2, duration=5)


    """Main methods"""
    def runProjectManager(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)

        # if we need to create project
        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}

        # Run the dialog event loop
        dlg.exec()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory

    def runCanOpenProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runOpenProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.runOpenProject)

    def runOpenProject(self):
        if not self.checkDependencies():
            return

        if not self.ProjectDirectory == self.TemporalFolder:
            QgsProject.instance().clear()
            self.defineCurrentProject()

        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}

        dlg = QGISRedImportProjectDialog()
        icon_path = ":/images/iconOpenProject.svg"
        dlg.setWindowIcon(QIcon(icon_path))
        dlg.setWindowTitle(self.tr("QGISRed: Open project"))
        # Run the dialog event loop
        dlg.exec()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            # Write .gql file
            QGISRedProjectIO().addProjectToGplFile(self.gplFile, self.NetworkName, self.ProjectDirectory)
            # Open files
            io = QGISRedProjectIO(self.ProjectDirectory, self.NetworkName, self.iface)
            io.openProjectInQgis()
            QGISRedIdentifierUtils(self.ProjectDirectory, self.NetworkName, self.iface).enforceAllIdentifiers()

            self.readOptions()
            self.suggestQgsProjectFilename()

    def runCanCreateProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runCreateProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.runCreateProject)

    def runCreateProject(self):
        if not self.checkDependencies():
            return

        if not self.ProjectDirectory == self.TemporalFolder:
            QgsProject.instance().clear()
            self.defineCurrentProject()

        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}
        dlg = QGISRedCreateProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        dlg.exec()
        self.readOptions()
        self.suggestQgsProjectFilename()

    def runCanImportData(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runImport()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedLayerUtils().runTask(self.clearQGisProject, self.runImport)

    def runImport(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            if self.isLayerOnEdition():
                return
        # show the dialog
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)

        # Run the dialog event loop
        dlg.exec()
        self.suggestQgsProjectFilename()

    def runSummary(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.Summary(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            pass
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def runCanAddData(self):
        if not self.checkDependencies():
            return

        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return
        self.runImport()

    def runLayerManagement(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return
        # show the dialog
        dlg = QGISRedLayerManagementDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        # Run the dialog event loop
        dlg.exec()

    def runLegends(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.legendsDialog = QGISRedLegendsDialog()
        self.legendsDialog.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        self.legendsDialog.show()

    def runSettings(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.EditSettings(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.pushMessage(self.tr("Project options updated"), level=0, duration=5)
        elif resMessage == "False":
            warningMessage = self.tr("Some issues occurred in the process")
            self.pushMessage(warningMessage, level=1, duration=5)
        elif resMessage == "Cancelled":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def runDefaultValues(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.DefaultValues(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.savedExtent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedLayerUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage == "Cancelled":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def runMaterials(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.Materials(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.savedExtent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedLayerUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage == "Cancelled":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def runSaveActionProject(self):
        self.defineCurrentProject()
        if self.ProjectDirectory != self.TemporalFolder and not QgsProject.instance().fileName():
            from qgis.PyQt.QtWidgets import QFileDialog
            suggested = os.path.join(self.ProjectDirectory, self.NetworkName + ".qgz")
            path, _ = QFileDialog.getSaveFileName(
                None, self.tr("Save QGIS project"), suggested, self.tr("QGIS Projects (*.qgz *.qgs)")
            )
            if path:
                QgsProject.instance().write(path)
        else:
            self.iface.mainWindow().findChild(QAction, "mActionSaveProject").trigger()

    def runCreateBackup(self):
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        io = QGISRedProjectIO(self.ProjectDirectory, self.NetworkName, self.iface)
        path = io.saveBackup()
        self.pushMessage(self.tr("Backup stored in:") + " " + path, level=3, duration=5)

    def _collectStyleSnapshot(self):
        """Collect which layers need style updates BEFORE assignLayerIdentifiers() runs.

        Returns a dict with:
          - inputs_to_restyle: list of (layer_id, style_name) for Inputs layers without identifier
          - results_no_id:     True if any Results layer has no identifier (re-simulation needed)
          - results_with_id:   list of layer_ids for Results layers that need NullRule applied
        """
        snapshot = {"inputs_to_restyle": [], "results_no_id": False, "results_with_id": []}
        root = QgsProject.instance().layerTreeRoot()

        inputs_group = root.findGroup("Inputs")
        if inputs_group:
            for tree_item in inputs_group.findLayers():
                layer = tree_item.layer()
                if not layer or layer.customProperty("qgisred_identifier"):
                    continue
                uri = layer.dataProvider().dataSourceUri()
                filename = os.path.splitext(os.path.basename(uri.split("|")[0]))[0]
                prefix = self.NetworkName + "_"
                if filename.startswith(prefix):
                    element_name = filename[len(prefix):]
                    snapshot["inputs_to_restyle"].append((layer.id(), element_name.lower()))

        results_group = root.findGroup("Results")
        if results_group:
            for tree_item in results_group.findLayers():
                layer = tree_item.layer()
                if not layer:
                    continue
                if not layer.customProperty("qgisred_identifier"):
                    snapshot["results_no_id"] = True
                else:
                    snapshot["results_with_id"].append(layer.id())

        return snapshot

    def _applyStyleUpdates(self, snapshot):
        """Apply style updates deferred from project open (runs after QgsProject.read() unwinds)."""
        from ..tools.utils.qgisred_styling_utils import QGISRedStylingUtils

        styling = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        project = QgsProject.instance()

        for layer_id, style_name in snapshot["inputs_to_restyle"]:
            layer = project.mapLayer(layer_id)
            if layer:
                styling.setStyle(layer, style_name)
                layer.triggerRepaint()

        for layer_id in snapshot["results_with_id"]:
            layer = project.mapLayer(layer_id)
            if layer:
                styling.applyNullStyle(layer)
                layer.triggerRepaint()

        if snapshot["results_no_id"]:
            self.pushMessage(
                self.tr("Simulation results need to be reloaded. Please run the simulation again."),
                level=1,
                duration=10,
            )

    def runCloseProject(self):
        self.iface.newProject(True)
