# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog, QApplication
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsCoordinateReferenceSystem
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector
from qgis.core import QgsTask, QgsApplication

from ..tools.qgisred_utils import QGISRedUtils

import os
import tempfile
from ctypes import c_char_p, WinDLL
from xml.etree import ElementTree

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_newproject_dialog.ui'))


class QGISRedNewProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    CRS = None
    ProcessDone = False
    gplFile = ""
    TemporalFolder = "Temporal folder"

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedNewProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.btCreateProject.clicked.connect(self.createProject)
        self.btEditProject.clicked.connect(self.editProject)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btSelectCRS.clicked.connect(self.selectCRS)
        # Variables:
        gplFolder = os.path.join(os.getenv('APPDATA'), "QGISRed")
        try:  # create directory if does not exist
            os.stat(gplFolder)
        except Exception:
            os.mkdir(gplFolder)
        self.gplFile = os.path.join(gplFolder, "qgisredprojectlist.gpl")

    def config(self, ifac, direct, netw):
        self.iface = ifac
        self.CRS = self.iface.mapCanvas().mapSettings().destinationCrs()
        if self.CRS.srsid() == 0:
            self.CRS = QgsCoordinateReferenceSystem()
            self.CRS.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        self.tbCRS.setText(self.CRS.description())
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)
        newProject = self.ProjectDirectory == self.TemporalFolder
        if newProject:
            self.setWindowTitle("QGISRed: Create Project")
            self.resize(462, 100)
        else:
            self.setWindowTitle("QGISRed: Edit Project")
        self.gbInfo.setVisible(not newProject)
        self.gbElements.setVisible(not newProject)
        self.btSelectDirectory.setVisible(newProject)
        self.btCreateProject.setVisible(newProject)
        self.btEditProject.setVisible(not newProject)
        self.tbNetworkName.setReadOnly(not newProject)
        if not newProject:
            self.setProperties()
            self.readTitleAndNotes()

    def setProperties(self):
        if self.btCreateProject.isVisible():
            self.setDefaultElements()
        else:
            dirList = os.listdir(self.ProjectDirectory)
            self.cbPipes.setChecked(self.NetworkName + "_Pipes.shp" in dirList)
            self.cbJunctions.setChecked(self.NetworkName + "_Junctions.shp" in dirList)
            self.cbTanks.setChecked(self.NetworkName + "_Tanks.shp" in dirList)
            self.cbReservoirs.setChecked(self.NetworkName + "_Reservoirs.shp" in dirList)
            self.cbValves.setChecked(self.NetworkName + "_Valves.shp" in dirList)
            self.cbPumps.setChecked(self.NetworkName + "_Pumps.shp" in dirList)
            self.cbPipes.setEnabled(not self.NetworkName + "_Pipes.shp" in dirList)
            self.cbJunctions.setEnabled(not self.NetworkName + "_Junctions.shp" in dirList)
            self.cbTanks.setEnabled(not self.NetworkName + "_Tanks.shp" in dirList)
            self.cbReservoirs.setEnabled(not self.NetworkName + "_Reservoirs.shp" in dirList)
            self.cbValves.setEnabled(not self.NetworkName + "_Valves.shp" in dirList)
            self.cbPumps.setEnabled(not self.NetworkName + "_Pumps.shp" in dirList)
            # others
            self.cbDemands.setChecked(self.NetworkName + "_Demands.shp" in dirList)
            self.cbSources.setChecked(self.NetworkName + "_Sources.shp" in dirList)
            self.cbIsolatedValves.setChecked(self.NetworkName + "_IsolationValves.shp" in dirList)
            self.cbHydrants.setChecked(self.NetworkName + "_Hydrants.shp" in dirList)
            self.cbPurgeValves.setChecked(self.NetworkName + "_WashoutValves.shp" in dirList)
            self.cbAirReleases.setChecked(self.NetworkName + "_AirReleaseValves.shp" in dirList)
            self.cbConnections.setChecked(self.NetworkName + "_ServiceConnections.shp" in dirList)
            self.cbManometers.setChecked(self.NetworkName + "_Manometers.shp" in dirList)
            self.cbFlowmeters.setChecked(self.NetworkName + "_Flowmeters.shp" in dirList)
            self.cbCountmeters.setChecked(self.NetworkName + "_Countermeters.shp" in dirList)
            self.cbLevelmeters.setChecked(self.NetworkName + "_LevelSensors.shp" in dirList)

    def setDefaultElements(self):
        self.cbPipes.setChecked(True)
        self.cbJunctions.setChecked(True)
        self.cbTanks.setChecked(True)
        self.cbReservoirs.setChecked(True)
        self.cbValves.setChecked(True)
        self.cbPumps.setChecked(True)

        self.cbDemands.setChecked(False)
        self.cbSources.setChecked(False)

        self.cbIsolatedValves.setChecked(False)
        self.cbHydrants.setChecked(False)
        self.cbPurgeValves.setChecked(False)
        self.cbAirReleases.setChecked(False)
        self.cbConnections.setChecked(False)
        self.cbManometers.setChecked(False)
        self.cbFlowmeters.setChecked(False)
        self.cbCountmeters.setChecked(False)
        self.cbLevelmeters.setChecked(False)

    def readTitleAndNotes(self):
        filePath = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if not os.path.exists(filePath):  # old versions
            filePath = os.path.join(self.ProjectDirectory, self.NetworkName + "_TitleAndNotes.txt")

        if os.path.exists(filePath):
            # Read data as text plain to include the encoding
            data = ""
            with open(filePath, 'r', encoding="latin-1") as content_file:
                data = content_file.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for title in root.iter('Title'):
                self.tbScenarioName.setText(title.text)
            for notes in root.iter('Notes'):
                self.tbNotes.setText(notes.text)

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory
            self.NetworkName = self.tbNetworkName.text()
            self.setProperties()

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_():
            crsId = projSelector.crs().srsid()
            if not crsId == 0:
                self.CRS = QgsCoordinateReferenceSystem()
                self.CRS.createFromId(crsId, QgsCoordinateReferenceSystem.InternalCrsId)
                self.tbCRS.setText(self.CRS.description())

    def getInputGroup(self):
        # Same method in qgisred_plugin
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def createElementsList(self):
        myList = ""
        if self.cbPipes.isEnabled() and self.cbPipes.isChecked():
            myList = myList + "pipe" + ";"
        if self.cbJunctions.isEnabled() and self.cbJunctions.isChecked():
            myList = myList + "junction" + ";"
        if self.cbTanks.isEnabled() and self.cbTanks.isChecked():
            myList = myList + "tank" + ";"
        if self.cbReservoirs.isEnabled() and self.cbReservoirs.isChecked():
            myList = myList + "reservoir" + ";"
        if self.cbValves.isEnabled() and self.cbValves.isChecked():
            myList = myList + "valve" + ";"
        if self.cbPumps.isEnabled() and self.cbPumps.isChecked():
            myList = myList + "pump" + ";"
        return myList

    def createComplementaryList(self):
        myList = ""
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.cbDemands.isChecked() and not utils.isLayerOpened("Demands"):
            myList = myList + "demand" + ";"
        if self.cbSources.isChecked() and not utils.isLayerOpened("Sources"):
            myList = myList + "source" + ";"

        if self.cbIsolatedValves.isChecked() and not utils.isLayerOpened("IsolationValves"):
            myList = myList + "isolationdvalve" + ";"
        if self.cbHydrants.isChecked() and not utils.isLayerOpened("Hydrants"):
            myList = myList + "hydrant" + ";"
        if self.cbPurgeValves.isChecked() and not utils.isLayerOpened("WashoutValves"):
            myList = myList + "washoutvalve" + ";"
        if self.cbAirReleases.isChecked() and not utils.isLayerOpened("AirReleaseValves"):
            myList = myList + "airreleasevalve" + ";"
        if self.cbConnections.isChecked() and not utils.isLayerOpened("ServiceConnections"):
            myList = myList + "serviceconnection" + ";"
        if self.cbManometers.isChecked() and not utils.isLayerOpened("Manometers"):
            myList = myList + "manometer" + ";"
        if self.cbFlowmeters.isChecked() and not utils.isLayerOpened("Flowmeters"):
            myList = myList + "flowmeter" + ";"
        if self.cbCountmeters.isChecked() and not utils.isLayerOpened("Countermeters"):
            myList = myList + "countermeter" + ";"
        if self.cbLevelmeters.isChecked() and not utils.isLayerOpened("LevelSensors"):
            myList = myList + "levelsensor" + ";"
        return myList

    def removeComplementaryLayers(self, task, wait_time):
        myList = []
        if not self.cbDemands.isChecked():
            myList.append("Demands")
        if not self.cbSources.isChecked():
            myList.append("Sources")

        if not self.cbIsolatedValves.isChecked():
            myList.append("IsolationValves")
        if not self.cbHydrants.isChecked():
            myList.append("Hydrants")
        if not self.cbPurgeValves.isChecked():
            myList.append("WashoutValves")
        if not self.cbAirReleases.isChecked():
            myList.append("AirReleaseValves")
        if not self.cbConnections.isChecked():
            myList.append("ServiceConnections")
        if not self.cbManometers.isChecked():
            myList.append("Manometers")
        if not self.cbFlowmeters.isChecked():
            myList.append("Flowmeters")
        if not self.cbCountmeters.isChecked():
            myList.append("Countermeters")
        if not self.cbLevelmeters.isChecked():
            myList.append("LevelSensors")

        QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface).removeLayers(myList)
        raise Exception('')

    def openElementsLayers(self, group, new):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)

        if self.cbPipes.isChecked():
            if not utils.isLayerOpened("Pipes"):
                utils.openLayer(self.CRS, group, "Pipes")
        if self.cbValves.isChecked():
            if not utils.isLayerOpened("Valves"):
                utils.openLayer(self.CRS, group, "Valves")
        if self.cbPumps.isChecked():
            if not utils.isLayerOpened("Pumps"):
                utils.openLayer(self.CRS, group, "Pumps")
        if self.cbJunctions.isChecked():
            if not utils.isLayerOpened("Junctions"):
                utils.openLayer(self.CRS, group, "Junctions")
        if self.cbTanks.isChecked():
            if not utils.isLayerOpened("Tanks"):
                utils.openLayer(self.CRS, group, "Tanks")
        if self.cbReservoirs.isChecked():
            if not utils.isLayerOpened("Reservoirs"):
                utils.openLayer(self.CRS, group, "Reservoirs")

    def openComplementaryLayers(self, group):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.cbDemands.isChecked():
            if not utils.isLayerOpened("Demands"):
                utils.openLayer(self.CRS, group, "Demands", toEnd=True)
        if self.cbSources.isChecked():
            if not utils.isLayerOpened("Sources"):
                utils.openLayer(self.CRS, group, "Sources", toEnd=True)

        if self.cbIsolatedValves.isChecked():
            if not utils.isLayerOpened("IsolationValves"):
                utils.openLayer(self.CRS, group, "IsolationValves", toEnd=True)
        if self.cbHydrants.isChecked():
            if not utils.isLayerOpened("Hydrants"):
                utils.openLayer(self.CRS, group, "Hydrants", toEnd=True)
        if self.cbPurgeValves.isChecked():
            if not utils.isLayerOpened("WashoutValves"):
                utils.openLayer(self.CRS, group, "WashoutValves", toEnd=True)
        if self.cbAirReleases.isChecked():
            if not utils.isLayerOpened("AirReleaseValves"):
                utils.openLayer(self.CRS, group, "AirReleaseValves", toEnd=True)
        if self.cbConnections.isChecked():
            if not utils.isLayerOpened("ServiceConnections"):
                utils.openLayer(self.CRS, group, "ServiceConnections", toEnd=True)
        if self.cbManometers.isChecked():
            if not utils.isLayerOpened("Manometers"):
                utils.openLayer(self.CRS, group, "Manometers", toEnd=True)
        if self.cbFlowmeters.isChecked():
            if not utils.isLayerOpened("Flowmeters"):
                utils.openLayer(self.CRS, group, "Flowmeters", toEnd=True)
        if self.cbCountmeters.isChecked():
            if not utils.isLayerOpened("Countermeters"):
                utils.openLayer(self.CRS, group, "Countermeters", toEnd=True)
        if self.cbLevelmeters.isChecked():
            if not utils.isLayerOpened("LevelSensors"):
                utils.openLayer(self.CRS, group, "LevelSensors", toEnd=True)

    def validationsCreateProject(self):
        self.NetworkName = self.tbNetworkName.text()
        if len(self.NetworkName) == 0:
            self.iface.messageBar().pushMessage("Validations", "The network's name is not valid", level=1)
            return False
        self.ProjectDirectory = self.tbProjectDirectory.text()
        if len(self.ProjectDirectory) == 0 or self.ProjectDirectory == self.TemporalFolder:
            self.ProjectDirectory = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names())
        else:
            if not os.path.exists(self.ProjectDirectory):
                self.iface.messageBar().pushMessage("Validations", "The project directory does not exist", level=1)
                return False
            else:
                dirList = os.listdir(self.ProjectDirectory)
                layers = ["Pipes", "Junctions", "Tanks", "Reservoirs", "Valves", "Pumps", "IsolationValves", "Hydrants",
                          "WashoutValves", "AirReleaseValves", "ServiceConnections", "Manometers", "Flowmeters",
                          "Countermeters", "LevelSensors"]
                for layer in layers:
                    if self.NetworkName + "_" + layer + ".shp" in dirList:
                        message = "The project directory has some file to selected network's name"
                        self.iface.messageBar().pushMessage("Validations", message, level=1)
                        return False

        if len(self.tbScenarioName.text()) == 0:
            self.iface.messageBar().pushMessage("Validations", "The scenario's name is not valid", level=1)
            return False
        return True

    def createProject(self):
        # Validations
        isValid = self.validationsCreateProject()
        if isValid is True:
            scnName = self.tbScenarioName.text()
            notes = self.tbNotes.toPlainText().strip().strip("\n")

            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QGISRedUtils().setCurrentDirectory()
            complElements = self.createComplementaryList()

            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.CreateProject.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.CreateProject.restype = c_char_p
            b = mydll.CreateProject(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
                'utf-8'), complElements.encode('utf-8'), scnName.encode('utf-8'), notes.encode('utf-8'))
            b = "".join(map(chr, b))  # bytes to string

            # Open layers
            self.iface.mapCanvas().setDestinationCrs(self.CRS)
            inputGroup = self.getInputGroup()
            self.openComplementaryLayers(inputGroup)
            self.openElementsLayers(inputGroup, True)
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            utils.orderLayers(inputGroup)
            QApplication.restoreOverrideCursor()

            # Message
            if b == "True":
                self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=5)
                file = open(self.gplFile, "a+")
                QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + '\n')
                file.close()
            elif b == "False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
            else:
                self.iface.messageBar().pushMessage("Error", b, level=2, duration=5)

            self.close()
            self.ProcessDone = True

    def editProject(self):
        task1 = QgsTask.fromFunction("", self.removeComplementaryLayers, on_finished=self.editProjectProcess, wait_time=0)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def editProjectProcess(self, exception=None, result=None):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()

        complElements = self.createComplementaryList()
        elements = self.createElementsList()
        scnName = self.tbScenarioName.text()
        notes = self.tbNotes.toPlainText().strip().strip("\n")

        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditProject.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditProject.restype = c_char_p
        b = mydll.EditProject(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode(
            'utf-8'), complElements.encode('utf-8'), scnName.encode('utf-8'), notes.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        # Open layers
        inputGroup = self.getInputGroup()
        if inputGroup is not None:
            for treeLayer in inputGroup.findLayers():
                treeLayer.layer().setCrs(self.CRS)
        self.openElementsLayers(inputGroup, False)
        self.openComplementaryLayers(inputGroup)
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.orderLayers(inputGroup)

        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=5)

        self.close()
        self.ProcessDone = True
