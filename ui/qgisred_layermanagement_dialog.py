# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import Qt
from qgis.core import QgsCoordinateReferenceSystem, QgsVectorLayer, QgsProject
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_layermanagement_dialog.ui"))


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
        self.btCancel.clicked.connect(self.reject)
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
        self.btConnections.clicked.connect(lambda: self.createElement("ServiceConnections", True))
        self.btMeters.clicked.connect(lambda: self.createElement("Meters", True))
        
        # Initialize layer name mapping
        self.layer_name_mapping = {}
        self.element_to_display_name = {}

    def config(self, ifac, direct, netw, parent):
        self.iface = ifac
        self.parent = parent

        utils = QGISRedUtils(direct, netw, ifac)
        self.crs = utils.getProjectCrs()
        self.originalCrs = self.crs
        self.tbCRS.setText(self.crs.description())

        self.NetworkName = netw
        self.ProjectDirectory = direct
        
        # Build layer name mapping from Inputs group
        self.buildLayerNameMapping()
        
        # Set properties with updated names
        self.setProperties()

    def buildLayerNameMapping(self):
        self.layer_name_mapping.clear()
        self.element_to_display_name.clear()
        
        element_identifiers = {
            'Pipes': 'qgisred_pipes',
            'Junctions': 'qgisred_junctions',
            'Tanks': 'qgisred_tanks',
            'Reservoirs': 'qgisred_reservoirs',
            'Valves': 'qgisred_valves',
            'Pumps': 'qgisred_pumps',
            'Demands': 'qgisred_demands',
            'Sources': 'qgisred_sources',
            'IsolationValves': 'qgisred_isolationvalves',
            'ServiceConnections': 'qgisred_serviceconnections',
            'Meters': 'qgisred_meters'
        }
        
        root = QgsProject.instance().layerTreeRoot()
        input_group = root.findGroup("Inputs")
        
        if not input_group:
            for element_type in element_identifiers:
                self.element_to_display_name[element_type] = self.getLayerNameToLegend(element_type)
            return
        
        input_layers = []
        for child in input_group.children():
            if hasattr(child, 'layer'):
                layer = child.layer()
                if layer:
                    input_layers.append(layer)
        
        for layer in input_layers:
            layer_identifier = layer.customProperty("qgisred_identifier")
            
            if layer_identifier:
                for element_type, identifier in element_identifiers.items():
                    if identifier == layer_identifier:
                        actual_name = layer.name()
                        self.layer_name_mapping[element_type] = actual_name
                        self.element_to_display_name[element_type] = actual_name
                        break
        
        for element_type in element_identifiers:
            if element_type not in self.element_to_display_name:
                self.element_to_display_name[element_type] = self.getLayerNameToLegend(element_type)

    def updateCheckboxText(self, checkbox, element_type):
        display_name = self.element_to_display_name.get(element_type, self.getLayerNameToLegend(element_type))
        # Preserve the ID format if it exists in the original text
        current_text = checkbox.text()
        if "Id:" in current_text:
            # Extract ID part and combine with new name
            id_part = current_text.split("Id:")[1].strip() if "Id:" in current_text else ""
            if id_part:
                checkbox.setText(f"{display_name} Id: {id_part}")
            else:
                checkbox.setText(display_name)
        else:
            checkbox.setText(display_name)

    def setProperties(self):
        dirList = os.listdir(self.ProjectDirectory)
        
        # Update checkbox texts with actual layer names
        self.updateCheckboxText(self.cbPipes, "Pipes")
        self.updateCheckboxText(self.cbJunctions, "Junctions")
        self.updateCheckboxText(self.cbTanks, "Tanks")
        self.updateCheckboxText(self.cbReservoirs, "Reservoirs")
        self.updateCheckboxText(self.cbValves, "Valves")
        self.updateCheckboxText(self.cbPumps, "Pumps")
        self.updateCheckboxText(self.cbDemands, "Demands")
        self.updateCheckboxText(self.cbSources, "Sources")
        self.updateCheckboxText(self.cbIsolatedValves, "IsolationValves")
        self.updateCheckboxText(self.cbConnections, "ServiceConnections")
        self.updateCheckboxText(self.cbMeters, "Meters")
        
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
        self.btConnections.setVisible(not self.NetworkName + "_ServiceConnections.shp" in dirList)
        self.btMeters.setVisible(not self.NetworkName + "_Meters.shp" in dirList)

        # Enables
        self.cbIsolatedValves.setEnabled(self.NetworkName + "_IsolationValves.shp" in dirList)
        self.cbConnections.setEnabled(self.NetworkName + "_ServiceConnections.shp" in dirList)
        self.cbMeters.setEnabled(self.NetworkName + "_Meters.shp" in dirList)

        # Los básicos: Enables and checked
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        
        # Check if layers are opened using their identifiers
        # Pipes remains exception: cannot be deselected
        hasLayer = self.isLayerOpenedByIdentifier("Pipes")
        self.cbPipes.setChecked(hasLayer)
        self.cbPipes.setEnabled(self.NetworkName + "_Pipes.shp" in dirList and not hasLayer)

        # For all other basic elements, always enable the checkbox (allowing the user to deselect to remove the layer)
        hasLayer = self.isLayerOpenedByIdentifier("Junctions")
        self.cbJunctions.setChecked(hasLayer)
        self.cbJunctions.setEnabled(self.NetworkName + "_Junctions.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Tanks")
        self.cbTanks.setChecked(hasLayer)
        self.cbTanks.setEnabled(self.NetworkName + "_Tanks.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Reservoirs")
        self.cbReservoirs.setChecked(hasLayer)
        self.cbReservoirs.setEnabled(self.NetworkName + "_Reservoirs.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Valves")
        self.cbValves.setChecked(hasLayer)
        self.cbValves.setEnabled(self.NetworkName + "_Valves.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Pumps")
        self.cbPumps.setChecked(hasLayer)
        self.cbPumps.setEnabled(self.NetworkName + "_Pumps.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Demands")
        self.cbDemands.setChecked(hasLayer)
        self.cbDemands.setEnabled(self.NetworkName + "_Demands.shp" in dirList)

        hasLayer = self.isLayerOpenedByIdentifier("Sources")
        self.cbSources.setChecked(hasLayer)
        self.cbSources.setEnabled(self.NetworkName + "_Sources.shp" in dirList)

        # Checked
        self.cbIsolatedValves.setChecked(self.isLayerOpenedByIdentifier("IsolationValves"))
        self.cbConnections.setChecked(self.isLayerOpenedByIdentifier("ServiceConnections"))
        self.cbMeters.setChecked(self.isLayerOpenedByIdentifier("Meters"))

    def isLayerOpenedByIdentifier(self, element_type):
        element_identifiers = {
            'Pipes': 'qgisred_pipes',
            'Junctions': 'qgisred_junctions',
            'Tanks': 'qgisred_tanks',
            'Reservoirs': 'qgisred_reservoirs',
            'Valves': 'qgisred_valves',
            'Pumps': 'qgisred_pumps',
            'Demands': 'qgisred_demands',
            'Sources': 'qgisred_sources',
            'IsolationValves': 'qgisred_isolationvalves',
            'ServiceConnections': 'qgisred_serviceconnections',
            'Meters': 'qgisred_meters'
        }
        
        target_identifier = element_identifiers.get(element_type)
        if not target_identifier:
            return False
        
        # Check all layers for the identifier
        layers = QGISRedUtils().getLayers()
        for layer in layers:
            layer_identifier = layer.customProperty("qgisred_identifier")
            if layer_identifier == target_identifier:
                return True
        
        # Fallback to checking by path for backward compatibility
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.isLayerOpened(element_type)

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

    def getLayerNameToLegend(self, original):
        upperIndex = []
        for x in range(len(original)):
            if original[x].isupper():
                upperIndex.append(x)
        upperIndex = upperIndex[::-1]
        for ind in upperIndex:
            if ind != 0:
                original = original[:ind] + " " + original[ind:]

        if "Demands" in original:
            original = "Multiple Demands"
        return original

    def isInLegend(self, layerName):
        openedLayers = self.getLayers()
        
        for layer in openedLayers:
            # Should translate here
            originalName = QGISRedUtils().getOriginalNameFromLayerName(layerName)
            layerPath = self.generatePath(self.ProjectDirectory, 
                                        self.NetworkName + "_" + originalName + ".shp")
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