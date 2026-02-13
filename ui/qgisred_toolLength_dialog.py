# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_toolLength_dialog.ui"))


class QGISRedLengthToolDialog(QDialog, FORM_CLASS):
    # Common variables
    Tolerance = "10"
    ProcessDone = False

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLengthToolDialog, self).__init__(parent)
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.tbTolerance.setText(self.Tolerance)

    def accept(self):
        self.Tolerance = self.tbTolerance.text()
        if self.Tolerance == "":
            self.lbMessage.setText(self.tr("Not valid Tolerance"))
            return
        try:
            _ = float(self.Tolerance)
        except Exception:
            self.lbMessage.setText(self.tr("Not numeric Tolerance"))
            return

        self.ProcessDone = True
        self.close()
