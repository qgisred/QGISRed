# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_cloneproject_dialog.ui"))


class QGISRedCloneProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedCloneProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btAccept.clicked.connect(self.accept)
        
        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            # self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory

    def accept(self):
        self.NetworkName = self.tbNetworkName.text()
        if self.NetworkName == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid New Project Name"), level=1)
            return
        if self.ProjectDirectory == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid Project Folder"), level=1)
            return

        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")):
            self.pushMessage(self.tr("Validations"), self.tr("There is already a project with this name in the selected project folder."), level=1)
            return

        self.ProcessDone = True
        self.close()
