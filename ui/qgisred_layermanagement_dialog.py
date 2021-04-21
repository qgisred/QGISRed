# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt
from qgis.core import QgsCoordinateReferenceSystem
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_layermanagement_dialog.ui'))


class QGISRedLayerManagementDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLayerManagementDialog, self).__init__(parent)
        self.setupUi(self)
        self.btAccept.clicked.connect(self.accept)
        self.btSelectCRS.clicked.connect(self.selectCRS)

        self.btPipes.clicked.connect(lambda: self.createElement("Pipes"))
        self.btJunctions.clicked.connect(lambda: self.createElement("Junctions"))
        self.btTanks.clicked.connect(lambda: self.createElement("Tanks"))
        self.btReservoirs.clicked.connect(lambda: self.createElement("Reservoirs"))
        self.btValves.clicked.connect(lambda: self.createElement("Valves"))
        self.btPumps.clicked.connect(lambda: self.createElement("Pumps"))
        self.btDemands.clicked.connect(lambda: self.createElement("Demands", True))
        self.btSources.clicked.connect(lambda: self.createElement("Sources", True))
        self.btIsolatedValves.clicked.connect(lambda: self.createElement("IsolationValves", True))
        self.btHydrants.clicked.connect(lambda: self.createElement("Hydrants", True))
        self.btPurgeValves.clicked.connect(lambda: self.createElement("WashoutValves", True))
        self.btAirReleases.clicked.connect(lambda: self.createElement("AirReleaseValves", True))
        self.btConnections.clicked.connect(lambda: self.createElement("ServiceConnections", True))
        self.btMeters.clicked.connect(lambda: self.createElement("Meters", True))

    def config(self, ifac, direct, netw, parent):
        self.iface = ifac
        self.parent = parent

        utils = QGISRedUtils(direct, netw, ifac)
        self.crs = utils.getProjectCrs()
        self.originalCrs = self.crs
        self.tbCRS.setText(self.crs.description())

        self.NetworkName = netw
        self.ProjectDirectory = direct

        self.setProperties()

    def setProperties(self):
        dirList = os.listdir(self.ProjectDirectory)
        # Visibilities
        self.btPipes.setVisible(not self.NetworkName + "_Pipes.shp" in dirList)
        self.btJunctions.setVisible(not self.NetworkName + "_Junctions.shp" in dirList)
        self.btTanks.setVisible(not self.NetworkName + "_Tanks.shp" in dirList)
        self.btReservoirs.setVisible(not self.NetworkName + "_Reservoirs.shp" in dirList)
        self.btValves.setVisible(not self.NetworkName + "_Valves.shp" in dirList)
        self.btPumps.setVisible(not self.NetworkName + "_Pumps.shp" in dirList)
        self.btDemands.setVisible(not self.NetworkName + "_Demands.shp" in dirList)
        self.btSources.setVisible(not self.NetworkName + "_Sources.shp" in dirList)
        self.btIsolatedValves.setVisible(not self.NetworkName + "_IsolationValves.shp" in dirList)
        self.btHydrants.setVisible(not self.NetworkName + "_Hydrants.shp" in dirList)
        self.btPurgeValves.setVisible(not self.NetworkName + "_WashoutValves.shp" in dirList)
        self.btAirReleases.setVisible(not self.NetworkName + "_AirReleaseValves.shp" in dirList)
        self.btConnections.setVisible(not self.NetworkName + "_ServiceConnections.shp" in dirList)
        self.btMeters.setVisible(not self.NetworkName + "_Meters.shp" in dirList)

        # Enables
        self.cbIsolatedValves.setEnabled(self.NetworkName + "_IsolationValves.shp" in dirList)
        self.cbHydrants.setEnabled(self.NetworkName + "_Hydrants.shp" in dirList)
        self.cbPurgeValves.setEnabled(self.NetworkName + "_WashoutValves.shp" in dirList)
        self.cbAirReleases.setEnabled(self.NetworkName + "_AirReleaseValves.shp" in dirList)
        self.cbConnections.setEnabled(self.NetworkName + "_ServiceConnections.shp" in dirList)
        self.cbMeters.setEnabled(self.NetworkName + "_Meters.shp" in dirList)

        # Los básicos: Enables and checked
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        hasLayer = utils.isLayerOpened("Pipes")
        self.cbPipes.setChecked(hasLayer)
        self.cbPipes.setEnabled(self.NetworkName + "_Pipes.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Junctions")
        self.cbJunctions.setChecked(hasLayer)
        self.cbJunctions.setEnabled(self.NetworkName + "_Junctions.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Tanks")
        self.cbTanks.setChecked(hasLayer)
        self.cbTanks.setEnabled(self.NetworkName + "_Tanks.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Reservoirs")
        self.cbReservoirs.setChecked(hasLayer)
        self.cbReservoirs.setEnabled(self.NetworkName + "_Reservoirs.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Valves")
        self.cbValves.setChecked(hasLayer)
        self.cbValves.setEnabled(self.NetworkName + "_Valves.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Pumps")
        self.cbPumps.setChecked(hasLayer)
        self.cbPumps.setEnabled(self.NetworkName + "_Pumps.shp" in dirList and not hasLayer)

        hasLayer = utils.isLayerOpened("Demands")
        self.cbDemands.setChecked(hasLayer)
        self.cbDemands.setEnabled(self.NetworkName + "_Demands.shp" in dirList and not hasLayer)
        hasLayer = utils.isLayerOpened("Sources")
        self.cbSources.setChecked(hasLayer)
        self.cbSources.setEnabled(self.NetworkName + "_Sources.shp" in dirList and not hasLayer)

        # Checked
        self.cbIsolatedValves.setChecked(utils.isLayerOpened("IsolationValves"))
        self.cbHydrants.setChecked(utils.isLayerOpened("Hydrants"))
        self.cbPurgeValves.setChecked(utils.isLayerOpened("WashoutValves"))
        self.cbAirReleases.setChecked(utils.isLayerOpened("AirReleaseValves"))
        self.cbConnections.setChecked(utils.isLayerOpened("ServiceConnections"))
        self.cbMeters.setChecked(utils.isLayerOpened("Meters"))

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_():
            crsId = projSelector.crs().srsid()
            if not crsId == 0:
                self.crs = QgsCoordinateReferenceSystem()
                self.crs.createFromId(crsId, QgsCoordinateReferenceSystem.InternalCrsId)
                self.tbCRS.setText(self.crs.description())

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedUtils().getLayers()

    def isInLegend(self, layerName):
        openedLayers = self.getLayers()
        for layer in openedLayers:
            layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
            if self.getLayerPath(layer) == layerPath:
                return True
        return False

    def createElementsList(self):
        if self.cbPipes.isChecked():
            self.layers.append("Pipes")
        if self.cbJunctions.isChecked():
            self.layers.append("Junctions")
        if self.cbTanks.isChecked():
            self.layers.append("Tanks")
        if self.cbReservoirs.isChecked():
            self.layers.append("Reservoirs")
        if self.cbValves.isChecked():
            self.layers.append("Valves")
        if self.cbPumps.isChecked():
            self.layers.append("Pumps")

    def createComplementaryList(self):
        if self.cbDemands.isChecked():
            self.layers.append("Demands")
        if self.cbSources.isChecked():
            self.layers.append("Sources")

        if self.cbIsolatedValves.isChecked():
            self.layers.append("Isolation Valves")
        if self.cbHydrants.isChecked():
            self.layers.append("Hydrants")
        if self.cbPurgeValves.isChecked():
            self.layers.append("Washout Valves")
        if self.cbAirReleases.isChecked():
            self.layers.append("AirRelease Valves")
        if self.cbConnections.isChecked():
            self.layers.append("Service Connections")
        if self.cbMeters.isChecked():
            self.layers.append("Meters")

    def createElement(self, layerName, complementary=False):
        layer = "" if complementary else layerName
        complLayer = layerName if complementary else ""
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CreateLayer(self.ProjectDirectory, self.NetworkName, layer, complLayer)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            self.parent.openElementLayer(layerName)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)
        self.close()

    def accept(self):
        self.layers = []
        self.createElementsList()
        self.createComplementaryList()
        epsg = None
        if not self.crs.srsid() == self.originalCrs.srsid():
            epsg = self.crs.authid().replace("EPSG:", "")
        self.parent.openRemoveSpecificLayers(self.layers, epsg)
        self.close()
