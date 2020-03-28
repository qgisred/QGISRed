# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
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
        self.lbIssues.mousePressEvent = self.issuesRepository
        # version
        metadata = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), 'metadata.txt')
        if os.path.exists(metadata):
            f = open(metadata, "r")
            lines = f.readlines()
            for line in lines:
                if "version=" in line:
                    self.versionLabel.setText(
                        "v." + line.replace("version=", ""))
                    return

    def linkRedhisp(self, event):
        url = 'https://www.iiama.upv.es/iiama/en/research/research-groups/hydraulic-networks-and-pressurised-systems.html'
        webbrowser.open(url)

    def linkIiama(self, event):
        webbrowser.open('https://www.iiama.upv.es/iiama/en/')

    def linkUpv(self, event):
        webbrowser.open('http://www.upv.es/index-en.html')

    def userManual(self, event):
        pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usermanual_en.pdf')
        webbrowser.open(pdf)

    def userManualEs(self, event):
        pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'usermanual_es.pdf')
        webbrowser.open(pdf)

    def issuesRepository(self, event):
        webbrowser.open('https://github.com/neslerel/QGISRed/issues')
