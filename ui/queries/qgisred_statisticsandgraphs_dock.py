# -*- coding: utf-8 -*-
import os

from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QGraphicsView, QGraphicsScene
from qgis.PyQt import uic

# load UI
formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statisticsandgraphs_dock.ui"))

class QGISRedStatisticsAndPlotsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsAndPlotsDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.setupGraphicsView()

    def setupGraphicsView(self):
        """Set up the QGraphicsView inside the graphWidget QWidget placeholder."""
        # Create the graphics scene
        self.scene = QGraphicsScene()

        # Create the graphics view
        self.graphicsView = QGraphicsView(self.scene)

        # Configure the view properties
        self.graphicsView.setRenderHint(QPainter.Antialiasing)
        self.graphicsView.setDragMode(QGraphicsView.ScrollHandDrag)

        # Create a layout for the graphWidget and add the graphics view
        layout = QVBoxLayout(self.graphWidget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.addWidget(self.graphicsView)

        # Set the layout to the graphWidget
        self.graphWidget.setLayout(layout)
