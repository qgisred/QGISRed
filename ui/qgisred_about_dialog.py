# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRedAboutDialog
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
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_about_dialog.ui'))


class QGISRedAboutDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedAboutDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.labelRedhisp.mousePressEvent = self.linkRedhisp
        self.labelIiama.mousePressEvent = self.linkIiama
        self.labelUpv.mousePressEvent = self.linkUpv

    def linkRedhisp(self, event):
        webbrowser.open('http://www.redhisp.upv.es')

    def linkIiama(self, event):
        webbrowser.open('http://www.iiama.upv.es')

    def linkUpv(self, event):
        webbrowser.open('http://www.upv.es')