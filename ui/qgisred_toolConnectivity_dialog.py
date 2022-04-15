# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
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

    def accept(self):
        self.Lines = self.tbLines.text()
        if self.Lines == "":
            self.lbMessage.setText("Not valid number for lines")
            return
        try:
            _ = float(self.Lines)
        except Exception:
            self.lbMessage.setText("Not numeric number of lines")
            return
        self.ProcessDone = True
        self.close()
