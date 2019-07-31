# -*- coding: utf-8 -*-
from qgis.PyQt import QtGui, uic
try: #QGis 3.x
    from PyQt5.QtWidgets import QDialog
except: #QGis 2.x
    from PyQt4.QtGui import QDialog

import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_about_dialog.ui'))

class QGISRedAboutDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedAboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.labelRedhisp.mousePressEvent = self.linkRedhisp
        self.labelIiama.mousePressEvent = self.linkIiama
        self.labelUpv.mousePressEvent = self.linkUpv
        self.lbManual.mousePressEvent = self.userManual
        self.lbManual_es.mousePressEvent = self.userManualEs

    def linkRedhisp(self, event):
        webbrowser.open('http://www.redhisp.upv.es')

    def linkIiama(self, event):
        webbrowser.open('http://www.iiama.upv.es')

    def linkUpv(self, event):
        webbrowser.open('http://www.upv.es')

    def userManual(self, event):
        pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usermanual_en.pdf')
        webbrowser.open(pdf)

    def userManualEs(self, event):
        pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usermanual_es.pdf')
        webbrowser.open(pdf)