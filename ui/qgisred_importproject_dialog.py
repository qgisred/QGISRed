# -*- coding: utf-8 -*-
from qgis.PyQt import QtGui, uic
try: #QGis 3.x
    from PyQt5.QtWidgets import QFileDialog, QDialog
except: #QGis 2.x
    from PyQt4.QtGui import QFileDialog, QDialog

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_importproject_dialog.ui'))

class QGISRedImportProjectDialog(QDialog, FORM_CLASS):
    #Common variables
    NetworkName = ""
    ProjectDirectory = ""
    File=""
    IsFile=True
    ProcessDone=False
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedImportProjectDialog, self).__init__(parent)
        self.setupUi(self)
        self.btSelectFile.clicked.connect(self.selectFile)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btAccept.clicked.connect(self.accept)
        self.rbFile.clicked.connect(self.rbSelected)
        self.rbNameFolder.clicked.connect(self.rbSelected)
        self.rbSelected()

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory()
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory

    def selectFile(self):
        qfd = QFileDialog()
        path = ""
        filter = "gqp(*.gqp)"
        f = QFileDialog.getOpenFileName(qfd, "Select GQP file", path, filter)
        if isinstance(f, tuple): #QGis 3.x
            f = f[0]
        if not f=="":
            self.tbFile.setText(f)
            self.tbFile.setCursorPosition(0)
            self.File = f

    def rbSelected(self):
        self.tbFile.setEnabled(self.rbFile.isChecked())
        self.btSelectFile.setEnabled(self.rbFile.isChecked())
        self.tbNetworkName.setEnabled(not self.rbFile.isChecked())
        self.tbProjectDirectory.setEnabled(not self.rbFile.isChecked())
        self.btSelectDirectory.setEnabled(not self.rbFile.isChecked())

    def accept(self):
        valid = True
        if self.rbFile.isChecked():
            if self.File=="":
                self.lbMessage.setText("GQP file not valid")
                valid = False
        else:
            self.NetworkName = self.tbNetworkName.text()
            if self.NetworkName=="":
                self.lbMessage.setText("Not valid Network's Name")
                valid=False
            if self.ProjectDirectory=="":
                self.lbMessage.setText("Not valid Project Directory")
                valid=False
        
        if valid:
            self.IsFile = self.rbFile.isChecked()
            self.ProcessDone = True
            self.close()