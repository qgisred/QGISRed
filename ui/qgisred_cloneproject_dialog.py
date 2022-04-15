# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
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

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory

    def accept(self):
        self.NetworkName = self.tbNetworkName.text()
        if self.NetworkName == "":
            self.lbMessage.setText("Not valid New Network's Name")
            return
        if self.ProjectDirectory == "":
            self.lbMessage.setText("Not valid Project Directory")
            return

        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")):
            self.lbMessage.setText("There is already a project with this name in this folder.")
            return

        self.ProcessDone = True
        self.close()
