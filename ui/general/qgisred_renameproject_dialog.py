# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_renameproject_dialog.ui"))


class QGISRedRenameProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    NetworkName = ""
    OldNetworkName = ""
    ProjectDirectory = ""
    ProcessDone = False
    RenameQGISProject = False

    def __init__(self, parent=None, oldName="", project="", qgisProjectBase=None):
        """Constructor."""
        super(QGISRedRenameProjectDialog, self).__init__(parent)
        self.OldNetworkName = oldName
        self.ProjectDirectory = project
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.cbRenameQGISProject.setVisible(qgisProjectBase is not None)
        if qgisProjectBase is not None:
            self.resize(self.width(), self.height() + self.cbRenameQGISProject.sizeHint().height() + 6)
        
        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        self.NetworkName = self.tbNetworkName.text().strip()
        if self.NetworkName == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid New Project Name"), level=1)
            return
        if self.NetworkName == self.OldNetworkName:
            self.pushMessage(self.tr("Validations"), self.tr("Project name can not be the same that the original"), level=1)
            return

        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Pipes.shp")):
            self.pushMessage(self.tr("Validations"), self.tr("There is already a project with this name in the project folder."), level=1)
            return

        self.RenameQGISProject = self.cbRenameQGISProject.isChecked()
        self.ProcessDone = True
        self.close()
