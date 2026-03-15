# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os
import webbrowser

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_about_dialog.ui"))


class QGISRedAboutDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedAboutDialog, self).__init__(parent)
        self.setupUi(self)
        self.labelQGISRed.mousePressEvent = self.linkQgisred
        self.labelRedhisp.mousePressEvent = self.linkRedhisp
        self.labelIiama.mousePressEvent = self.linkIiama
        self.labelUpv.mousePressEvent = self.linkUpv
        self.lbManual.mousePressEvent = self.userManual
        self.lbOfflineManual.mousePressEvent = self.offlineManual
        self.lbIssues.mousePressEvent = self.issuesRepository

        from PyQt5.QtCore import QSettings
        locale = QSettings().value("locale/userLocale", "")[0:2]
        if locale == "es":
            self.online_manual = "https://qgisred.gitbook.io/manual-de-usuario"
            self.offline_manual_file = "usermanual_es.pdf"
        else:
            self.online_manual = "https://qgisred.gitbook.io/usermanual"
            self.offline_manual_file = "usermanual_en.pdf"

        # version
        metadata = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.txt")
        if os.path.exists(metadata):
            with open(metadata, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if "version=" in line:
                        self.versionLabel.setText("v." + line.replace("version=", ""))
                        return

    def linkQgisred(self, event):
        webbrowser.open("https://qgisred.upv.es")

    def linkRedhisp(self, event):
        url = "https://www.iiama.upv.es/iiama/en/research/research-groups/hydraulic-networks-and-pressurised-systems.html"
        webbrowser.open(url)

    def linkIiama(self, event):
        webbrowser.open("https://www.iiama.upv.es/iiama/en/")

    def linkUpv(self, event):
        webbrowser.open("http://www.upv.es/index-en.html")

    def userManual(self, event):
        webbrowser.open(self.online_manual)

    def offlineManual(self, event):
        pdf = os.path.join(os.path.dirname(os.path.dirname(__file__)), "manuals", self.offline_manual_file)
        webbrowser.open(pdf)

    def issuesRepository(self, event):
        webbrowser.open("https://github.com/neslerel/QGISRed/issues")
