# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_moveproject_dialog.ui"))


class QGISRedMoveProjectDialog(QDialog, FORM_CLASS):
    # Common variables
    TargetDirectory = ""
    MoveProjectFiles = True
    MoveQGISProject = False
    ProcessDone = False

    def __init__(self, parent=None, projectPath="", networkName="", qgisProjectBase=None):
        """Constructor."""
        super(QGISRedMoveProjectDialog, self).__init__(parent)
        self._projectPath = os.path.normcase(os.path.normpath(projectPath)) if projectPath else ""
        self._networkName = networkName
        self._hasQGisProject = qgisProjectBase is not None
        self.setupUi(self)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btAccept.clicked.connect(self.accept)
        self.cbMoveQGISProject.setVisible(self._hasQGisProject)
        if self._hasQGisProject:
            self.resize(self.width(), self.height() + self.cbMoveQGISProject.sizeHint().height() + 6)

    def selectDirectory(self):
        d = QFileDialog.getExistingDirectory()
        if not d:
            return
        self.tbTargetDirectory.setText(d)
        self.TargetDirectory = d
        self.lbMessage.setText("")
        sameDir = os.path.normcase(os.path.normpath(d)) == self._projectPath
        if sameDir:
            self.cbMoveProjectFiles.setChecked(False)
            self.cbMoveProjectFiles.setEnabled(False)
        elif not self.cbMoveProjectFiles.isEnabled():
            # was disabled only because of same-dir — re-enable it, but don't override a manual uncheck
            self.cbMoveProjectFiles.setChecked(True)
            self.cbMoveProjectFiles.setEnabled(True)

    def accept(self):
        if self.TargetDirectory == "":
            self.lbMessage.setText(self.tr("Not valid Target Folder"))
            return
        sameDir = os.path.normcase(os.path.normpath(self.TargetDirectory)) == self._projectPath
        if sameDir and not self._hasQGisProject:
            self.lbMessage.setText(self.tr("Cannot move to the same directory."))
            return
        if self.cbMoveProjectFiles.isChecked() and not sameDir:
            if os.path.exists(os.path.join(self.TargetDirectory, self._networkName + "_Pipes.shp")):
                self.lbMessage.setText(self.tr("There is already a project with this name in the target folder."))
                return
        if not self.cbMoveProjectFiles.isChecked() and not self.cbMoveQGISProject.isChecked():
            self.lbMessage.setText(self.tr("Select at least one option."))
            return
        self.MoveProjectFiles = self.cbMoveProjectFiles.isChecked()
        self.MoveQGISProject = self.cbMoveQGISProject.isChecked()
        self.ProcessDone = True
        self.close()
