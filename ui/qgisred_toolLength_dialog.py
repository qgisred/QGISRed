# -*- coding: utf-8 -*-
from qgis.PyQt import QtGui, uic
try: #QGis 3.x
    from PyQt5.QtWidgets import QFileDialog, QDialog
except: #QGis 2.x
    from PyQt4.QtGui import QFileDialog, QDialog

import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_toolLength_dialog.ui'))

class QGISRedLengthToolDialog(QDialog, FORM_CLASS):
    #Common variables
    Tolerance = "10"
    Modify = False
    ProcessDone=False
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLengthToolDialog, self).__init__(parent)
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.tbTolerance.setText(self.Tolerance)

    def accept(self):
        self.Tolerance = self.tbTolerance.text()
        if self.Tolerance=="":
            self.lbMessage.setText("Not valid Tolerance")
            return
        try:
            a = float(self.Tolerance)
        except:
            self.lbMessage.setText("Not numeric Tolerance")
            return
        self.Modify = self.cbModify.isChecked()

        self.ProcessDone = True
        self.close()