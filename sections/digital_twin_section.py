# -*- coding: utf-8 -*-
"""Digital twin section for QGISRed (service connections, isolation valves, meters)."""

import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool
from ..tools.map_tools.qgisred_createConnection import QGISRedCreateConnectionTool
from ..ui.digitaltwin.qgisred_toolConnections_dialog import QGISRedServiceConnectionsToolDialog


class DigitalTwinSection:
    """Service connections, isolation valves, meters, hydrants, washout valves."""

    def runPaintServiceConnection(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.addServConnButton.setChecked(False)
            return

        tool = "createConnection"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.addServConnButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedCreateConnectionTool(
                self.addServConnButton,
                self.iface,
                self.ProjectDirectory,
                self.NetworkName,
                self.runCreateServiceConnection,
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateServiceConnection(self, points):
        pipePoints = ""
        for p in points:
            p = self.transformPoint(p)
            pipePoints = pipePoints + str(p.x()) + ":" + str(p.y()) + ";"
        # Process:
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddConnection(self.ProjectDirectory, self.NetworkName, self.tempFolder, pipePoints)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "Service Connection added")

    def runSelectIsolationValvePoint(self):
        tool = "pointIsolationValve"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addIsolationValveButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addIsolationValveButton, self, self.runAddIsolationValve, 2, cursor=":/images/iconAddIsolationValve.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddIsolationValve(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddIsolationValve(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectMeterPoint(self, action=None):
        tool = "pointMeter" + self.currentMeter
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            action.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(action, self, self.runAddMeter, 2, cursor=action.icon().pixmap(24, 24))
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runSelectDefaultMeterPoint(self):
        self.runSelectMeterPoint(self.addMeterDropButton.defaultAction())

    def runSelectAutoMeterPoint(self):
        self.currentMeter = "Undefined"
        self.addMeterDropButton.setDefaultAction(self.addAutoMeterButton)
        self.runSelectMeterPoint(self.addAutoMeterButton)

    def runSelectManometerPoint(self):
        self.currentMeter = "Manometer"
        self.addMeterDropButton.setDefaultAction(self.addManometerButton)
        self.runSelectMeterPoint(self.addManometerButton)

    def runSelectFlowmeterPoint(self):
        self.currentMeter = "Flowmeter"
        self.addMeterDropButton.setDefaultAction(self.addFlowmeterButton)
        self.runSelectMeterPoint(self.addFlowmeterButton)

    def runSelectCountermeterPoint(self):
        self.currentMeter = "Countermeter"
        self.addMeterDropButton.setDefaultAction(self.addCountermeterButton)
        self.runSelectMeterPoint(self.addCountermeterButton)

    def runSelectLevelSensorPoint(self):
        self.currentMeter = "LevelSensor"
        self.addMeterDropButton.setDefaultAction(self.addLevelSensorButton)
        self.runSelectMeterPoint(self.addLevelSensorButton)

    def runSelectDifferentialManometerPoint(self):
        self.currentMeter = "DifferentialManometer"
        self.addMeterDropButton.setDefaultAction(self.addDifferentialManometerButton)
        self.runSelectMeterPoint(self.addDifferentialManometerButton)

    def runSelectQualitySensorPoint(self):
        self.currentMeter = "QualitySensor"
        self.addMeterDropButton.setDefaultAction(self.addQualitySensorButton)
        self.runSelectMeterPoint(self.addQualitySensorButton)

    def runSelectEnergySensorPoint(self):
        self.currentMeter = "EnergySensor"
        self.addMeterDropButton.setDefaultAction(self.addEnergySensorButton)
        self.runSelectMeterPoint(self.addEnergySensorButton)

    def runSelectStatusSensorPoint(self):
        self.currentMeter = "StatusSensor"
        self.addMeterDropButton.setDefaultAction(self.addStatusSensorButton)
        self.runSelectMeterPoint(self.addStatusSensorButton)

    def runSelectValveOpeningPoint(self):
        self.currentMeter = "ValveOpening"
        self.addMeterDropButton.setDefaultAction(self.addValveOpeningButton)
        self.runSelectMeterPoint(self.addValveOpeningButton)

    def runSelectTachometerPoint(self):
        self.currentMeter = "Tachometer"
        self.addMeterDropButton.setDefaultAction(self.addTachometerButton)
        self.runSelectMeterPoint(self.addTachometerButton)

    def runAddMeter(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["Meters"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddMeter(self.ProjectDirectory, self.NetworkName, self.tempFolder, point, self.currentMeter)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runLoadReadings(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.LoadReadings(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runLoadScada(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        self.especificComplementaryLayers = ["Meters"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.LoadScada(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSetPipeStatus(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_IsolationValves.shp")):
            self.pushMessage(
                self.tr("The Isolation Valves SHP file does not exist"), level=1, duration=5
            )
            return

        # Process
        self.especificComplementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SetInitialStatusPipes(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runAddConnections(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_ServiceConnections.shp")):
            self.pushMessage(
                self.tr("The Service Connections SHP file does not exist"), level=1, duration=5
            )
            return

        # Question
        dlg = QGISRedServiceConnectionsToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        if not dlg.ProcessDone:
            return

        asNode = "true"
        if dlg.AsPipes:
            asNode = "false"

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddConnections(self.ProjectDirectory, self.NetworkName, asNode, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No Service Connections to include in the model")
