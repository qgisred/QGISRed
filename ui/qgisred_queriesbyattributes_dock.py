# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtCore import Qt
from qgis.PyQt import uic
from ..tools.qgisred_utils import QGISRedUtils
import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_queriesbyattributes_dock.ui"))

class QGISRedQueriesByAttributesDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(QGISRedQueriesByAttributesDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self) 
        self.iface = iface
        self.canvas = iface.mapCanvas()

    def resizeToMinimumHeight(self):
        self.layout().activate()
        self.adjustSize()
