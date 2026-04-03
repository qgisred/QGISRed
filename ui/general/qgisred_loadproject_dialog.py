# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner

from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_loadproject_dialog.ui"))


class QGISRedImportProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    NetworkName = ""
    ProjectDirectory = ""
    File = ""
    IsFile = True
    ProcessDone = False

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedImportProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btAccept.clicked.connect(self.accept)
        
        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        selected_directory = QGISRedFileSystemUtils().getUniformedPath(selected_directory)
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            # self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory
            self.createNetworkList()

    def createNetworkList(self):
        self.cbNetworkName.clear()
        for f in os.listdir(self.ProjectDirectory):
            if "_Pipes.shp" in f:
                self.cbNetworkName.addItem(f.replace("_Pipes.shp", ""))
        if self.cbNetworkName.count() > 0:
            self.cbNetworkName.setCurrentIndex(0)

    def accept(self):
        valid = True
        self.NetworkName = self.cbNetworkName.currentText()
        if self.NetworkName == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid Project Name"), level=1)
            valid = False
        if self.ProjectDirectory == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid Project Folder"), level=1)
            valid = False

        if valid:
            self.ProcessDone = True
            self.close()
