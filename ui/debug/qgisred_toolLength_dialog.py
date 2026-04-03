# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
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
        
        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        self.Tolerance = self.tbTolerance.text()
        if self.Tolerance == "":
            self.pushMessage(self.tr("Validations"), self.tr("Not valid Tolerance"), level=1)
            return
        try:
            _ = float(self.Tolerance)
        except Exception:
            self.pushMessage(self.tr("Validations"), self.tr("Not numeric Tolerance"), level=1)
            return

        self.ProcessDone = True
        self.close()
