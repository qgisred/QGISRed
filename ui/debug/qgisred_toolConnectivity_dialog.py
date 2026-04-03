# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_toolConnectivity_dialog.ui"))


class QGISRedConnectivityToolDialog(QDialog, FORM_CLASS):
    # Common variables
    Lines = "5"
    Remove = False
    Export = False
    ProcessDone = False

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedConnectivityToolDialog, self).__init__(parent)
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.tbLines.setText(self.Lines)
        
        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        self.Lines = self.tbLines.text()
        if self.Lines == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid number for lines"), level=1)
            return
        try:
            _ = float(self.Lines)
        except Exception:
            self.pushMessage(self.tr("Validations"), self.tr("Not numeric number of lines"), level=1)
            return
        self.ProcessDone = True
        self.close()
