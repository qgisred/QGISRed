# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_toolConnections_dialog.ui"))


class QGISRedServiceConnectionsToolDialog(QDialog, FORM_CLASS):
    # Common variables
    ProcessDone = False
    AsPipes = False

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedServiceConnectionsToolDialog, self).__init__(parent)
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.cancel)

    def accept(self):
        if self.rbPipes.isChecked():
            self.AsPipes = True
        self.ProcessDone = True
        self.close()

    def cancel(self):
        self.ProcessDone = False
        self.close()
