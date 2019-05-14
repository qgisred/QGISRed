# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedExportInpDialog
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_exportinp_dialog.ui'))


class QGISRedExportInpDialog(QDialog, FORM_CLASS):
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    InpFile=""
    CRS= None
    ProcessDone= False
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedExportInpDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.btCreateInp.clicked.connect(self.createInp)
        self.btSelectInp.clicked.connect(self.selectINP)

    def config(self, ifac, direct, netw):
        self.iface=ifac
        self.ProcessDone = False
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.InpFile =""
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)
        newProject = self.ProjectDirectory=="Temporal folder"
        self.btCreateInp.setVisible(not newProject)
        self.lbMessage.setVisible(newProject)
    
    def selectINP(self):
        qfd = QFileDialog()
        path = ""
        filter = "inp(*.inp)"
        f = QFileDialog.getSaveFileName(qfd, "Save INP file", path, filter)
        if isinstance(f, tuple): #QGis 3.x
            f = f[0]
        if not f=="":
            self.InpFile = f
            self.tbInpFile.setText(f)
            self.tbInpFile.setCursorPosition(0)

    def validationsCreateProject(self):
        if len(self.NetworkName)==0:
            self.iface.messageBar().pushMessage("Validations", "The network's name is not valid", level=1)
            return False
        if not os.path.exists(self.ProjectDirectory):
            self.iface.messageBar().pushMessage("Validations", "The project directory does not exist", level=1)
            return False
        self.InpFile = self.tbInpFile.text()
        if len(self.InpFile)==0:
            self.iface.messageBar().pushMessage("Validations", "INP file is not valid", level=1)
            return False
        return True

    def createInp(self):
        isValid = self.validationsCreateProject()
        if isValid==True:
            os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))

            elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"

            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.ExportToInp.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.ExportToInp.restype = c_char_p
            b = mydll.ExportToInp(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.InpFile.encode('utf-8'), elements.encode('utf-8'))
            try: #QGis 3.x
                b= "".join(map(chr, b)) #bytes to string
            except:  #QGis 2.x
                b=b
            
            if b=="True":
                self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
            elif b=="False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
            else:
                self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
            
            os.startfile(os.path.dirname(self.InpFile))
            self.close()
            self.ProcessDone = True