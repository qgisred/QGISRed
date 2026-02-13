# -*- coding: utf-8 -*- 
from PyQt5.QtWidgets import QDialog, QWidget
from PyQt5.QtGui import QIcon
from qgis.PyQt import uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_thematicmaps_dialog.ui"))

class QGISRedThematicMapsDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedThematicMapsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setDialogStyle()
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)

    def setDialogStyle(self):
        #Some design aspects of the dialog in Python can only be done via code
        #Set dialog icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(icon_path))

        # Set group boxes' titles to bold
        self.gbPipes.setStyleSheet("font-weight: bold;")
        self.gbJunctions.setStyleSheet("font-weight: bold;")
        self.gbValves.setStyleSheet("font-weight: bold;")
        self.gbPumps.setStyleSheet("font-weight: bold;")
        self.gbTanks.setStyleSheet("font-weight: bold;")
        self.gbReservoirs.setStyleSheet("font-weight: bold;")

        # Set widgets inside the group boxes to normal weight
        for widget in self.gbPipes.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbJunctions.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbValves.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbPumps.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbTanks.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbReservoirs.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
    
    def accept(self):
        ...