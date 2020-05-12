# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog, QApplication
from PyQt5.QtCore import Qt
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_createproject_dialog.ui'))


class QGISRedCreateProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    gplFile = ""
    TemporalFolder = "Temporal folder"

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedCreateProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.btCreateProject.clicked.connect(self.createProject)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btSelectCRS.clicked.connect(self.selectCRS)
        # Variables:
        gplFolder = os.path.join(os.getenv('APPDATA'), "QGISRed")
        try:  # create directory if does not exist
            os.stat(gplFolder)
        except Exception:
            os.mkdir(gplFolder)
        self.gplFile = os.path.join(gplFolder, "qgisredprojectlist.gpl")

    def config(self, ifac, direct, netw, parent):
        self.iface = ifac
        self.parent = parent
        utils = QGISRedUtils(direct, netw, ifac)
        self.crs = utils.getProjectCrs()
        self.tbCRS.setText(self.crs.description())
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory
            self.NetworkName = self.tbNetworkName.text()

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_():
            crsId = projSelector.crs().srsid()
            if not crsId == 0:
                self.crs = QgsCoordinateReferenceSystem()
                self.crs.createFromId(crsId, QgsCoordinateReferenceSystem.InternalCrsId)
                self.tbCRS.setText(self.crs.description())

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

        return True

    def createProject(self):
        # Validations
        isValid = self.validationsCreateProject()
        if isValid is True:
            epsg = self.crs.authid().replace("EPSG:", "")
            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.CreateProject(self.ProjectDirectory, self.NetworkName, epsg)
            QApplication.restoreOverrideCursor()

            # Message
            if resMessage == "True":
                self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=5)
                # Project manager list
                file = open(self.gplFile, "a+")
                QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + '\n')
                file.close()

                # open layers
                self.parent.openElementLayers(None, self.NetworkName, self.ProjectDirectory)
            elif resMessage == "False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
            else:
                self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

            self.close()
