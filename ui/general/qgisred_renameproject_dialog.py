# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_renameproject_dialog.ui"))


class QGISRedRenameProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    NetworkName = ""
    OldNetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False

    def __init__(self, parent=None, oldName="", project=""):
        """Constructor."""
        super(QGISRedRenameProjectDialog, self).__init__(parent)
        self.OldNetworkName = oldName
        self.ProjectDirectory = project
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)

    def accept(self):
        self.NetworkName = self.tbNetworkName.text().strip()
        if self.NetworkName == "":
            self.lbMessage.setText(self.tr("Not valid New Project Name"))
            return
        if self.NetworkName == self.OldNetworkName:
            self.lbMessage.setText(self.tr("Project name can not be the same that the original"))
            return

        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")):
            self.lbMessage.setText(self.tr("There is already a project with this name in the project folder."))
            return

        self.ProcessDone = True
        self.close()
