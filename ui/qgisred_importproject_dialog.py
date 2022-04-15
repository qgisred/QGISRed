# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_importproject_dialog.ui"))


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
        self.rbSelected()

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory

    def rbSelected(self):
        self.tbNetworkName.setEnabled(True)
        self.tbProjectDirectory.setEnabled(True)
        self.btSelectDirectory.setEnabled(True)

    def accept(self):
        valid = True
        self.NetworkName = self.tbNetworkName.text()
        if self.NetworkName == "":
            self.lbMessage.setText("Not valid Network's Name")
            valid = False
        if self.ProjectDirectory == "":
            self.lbMessage.setText("Not valid Project Directory")
            valid = False

        if valid:
            self.ProcessDone = True
            self.close()
