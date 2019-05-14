# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedImportProjectDialog
                                 A QGIS plugin
 Some util tools for GISRed
                             -------------------
        begin                : 2019-03-26
        git sha              : $Format:%H$
        copyright            : (C) 2019 by REDHISP (UPV)
        email                : fmartine@hma.upv.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsCoordinateReferenceSystem
from qgis.PyQt import QtGui, uic

try: #QGis 3.x
    from qgis.gui import QgsProjectionSelectionTreeWidget
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QFileDialog, QDialog
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
except: #QGis 2.x
    from qgis.gui import QgsGenericProjectionSelector
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QTableWidgetItem, QFileDialog, QDialog
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo
    from qgis.core import QgsMapLayerRegistry

import os
from ctypes import*
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_importproject_dialog.ui'))

class QGISRedImportProjectDialog(QDialog, FORM_CLASS):
    NetworkName = ""
    ProjectDirectory = ""
    File=""
    IsFile=True
    ProcessDone=False
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedImportProjectDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
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