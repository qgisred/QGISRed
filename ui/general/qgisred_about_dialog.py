# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsApplication

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
        self.labelBidImage.mousePressEvent = self.linkBidImage
        self.labelUpv.mousePressEvent = self.linkUpv
        locale = QgsApplication.locale()[0:2]
        # BID URL
        if locale == "es":
            self.bid_url = "https://www.iadb.org/es"
        elif locale == "pt":
            self.bid_url = "https://www.iadb.org/pt-br"
        elif locale == "fr":
            self.bid_url = "https://www.iadb.org/fr"
        else:
            self.bid_url = "https://www.iadb.org/en"

        # version
        metadata = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "metadata.txt")
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

    def linkBidImage(self, event):
        webbrowser.open(self.bid_url)

    def linkUpv(self, event):
        webbrowser.open("http://www.upv.es/index-en.html")
