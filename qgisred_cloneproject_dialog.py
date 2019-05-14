# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedCloneProjectDialog
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_cloneproject_dialog.ui'))

class QGISRedCloneProjectDialog(QDialog, FORM_CLASS):
    NetworkName = ""
    ProjectDirectory = ""
    ProcessDone=False
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedCloneProjectDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
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
        if self.NetworkName=="":
            self.lbMessage.setText("Not valid New Network's Name")
            return
        if self.ProjectDirectory=="":
            self.lbMessage.setText("Not valid Project Directory")
            return
        
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp" )):
            self.lbMessage.setText("There is already a project with this name in this folder.")
            return

        self.ProcessDone = True
        self.close()