# -*- coding: utf-8 -*-

# Standard library imports
import os

# Third-party imports
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QWidget
from qgis.PyQt import uic

# QGIS imports
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer

# Local imports
from ...compat import NODE_TYPE_LAYER
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_thematicmaps_builder import QGISRedThematicMapsBuilder
from ...tools.utils.qgisred_thematicmaps_queries import buildQueryCatalogue, queryIdentifier

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_thematicmaps_dialog.ui"))


class QGISRedThematicMapsDialog(QDialog, FORM_CLASS):
    iface = None
    NetworkName = ""
    ProjectDirectory = ""

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedThematicMapsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setDialogStyle()
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)
        self.updateCheckboxStates()
        self.tempElementsHide()

    def config(self, iface, projectDirectory, networkName):
        self.iface = iface
        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName
        self.builder = QGISRedThematicMapsBuilder(iface, projectDirectory, networkName)

    def tempElementsHide(self):
        self.gbValves.hide()
        self.gbPumps.hide()
        self.gbTanks.hide()
        self.gbReservoirs.hide()

        self.cbJunctionsPatternDemand.hide()
        self.cbJunctionsEmitterCoeff.hide()
        self.cbJunctionsInitialQuality.hide()
        self.cbJunctionsTag.hide()
        # The hidden third Junctions option keeps its column, so Total Base
        # Demand lines up with the second Pipes option.
        retainingPolicy = self.cbJunctionsPatternDemand.sizePolicy()
        retainingPolicy.setRetainSizeWhenHidden(True)
        self.cbJunctionsPatternDemand.setSizePolicy(retainingPolicy)

        self.cbPipesLossCoeff.hide()
        self.cbPipesInitStatus.hide()
        self.cbPipesBulkCoeff.hide()
        self.cbPipesWallCoeff.hide()
        self.cbPipesTag.hide()

        self.tabWidget.setTabVisible(1, False)

        currentWidth = self.width()
        self.adjustSize()
        self.resize(currentWidth, self.height())

    def setDialogStyle(self):
        self.setWindowIcon(QIcon(":/images/iconThematicMaps.svg"))

        groupBoxes = [
            self.gbPipes,
            self.gbJunctions,
            self.gbValves,
            self.gbPumps,
            self.gbTanks,
            self.gbReservoirs,
            self.gbService,
            self.gbIsolation,
            self.gbMeters
        ]

        for groupBox in groupBoxes:
            self.setGroupBoxStyle(groupBox)

    def setGroupBoxStyle(self, groupBox):
        groupBox.setStyleSheet("font-weight: bold;")
        for widget in groupBox.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")

    def accept(self):
        if QGISRedLayerUtils.findGroupByIdentifier("qgisred_inputs") is None:
            QMessageBox.critical(self, self.tr('Error'), self.tr('Inputs group not found.'))
            return

        selectedQueries = self.getSelectedQueries()
        currentValidIdentifiers = set(queryIdentifier(query) for query in selectedQueries)
        toRemoveIdentifiers = self.initialValidIdentifiers - currentValidIdentifiers

        if not selectedQueries and not toRemoveIdentifiers:
            super().accept()
            return

        # remove old layers (supports both old location under 'Queries' and new under 'Thematic Maps')
        self.builder.removeQueryLayersByIdentifiers(toRemoveIdentifiers)
        if toRemoveIdentifiers and self.iface is not None:
            self.iface.mapCanvas().refresh()

        self.builder.cleanupEmptyQueryGroups()

        # Recreates Inputs if the removals above emptied it out; a project without it
        # cannot host any of the layers built below.
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if utils.getOrCreateGroup("Inputs") is None:
            super().accept()
            return

        self.builder.applyQueries(
            selectedQueries, currentValidIdentifiers - self.initialValidIdentifiers)
        super().accept()

    def updateCheckboxStates(self):
        queriesGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_queries")
        thematicGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_thematicmaps")
        targetGroup = thematicGroup or queriesGroup  # support legacy placement

        checkboxMapping = self.createIdentifierCheckboxMapping()
        if targetGroup:
            self.checkLayersRecursiveByIdentifier(targetGroup, checkboxMapping)

        self.initialValidIdentifiers = (
            QGISRedThematicMapsBuilder.collectExistingIdentifiers(targetGroup) if targetGroup else set())

    def createIdentifierCheckboxMapping(self):
        mapping = {}

        # Tanks mappings
        mapping.update({
            'qgisred_query_tanks_elevation': self.cbTanksElevation,
            'qgisred_query_tanks_diameter': self.cbTanksDiameter,
            'qgisred_query_tanks_volume': self.cbTanksVolume,
            'qgisred_query_tanks_level': self.cbTanksLevel,
            'qgisred_query_tanks_initquality': self.cbTanksInitialQuality,
            'qgisred_query_tanks_bulkcoeff': self.cbTanksBulkCoeff,
            'qgisred_query_tanks_mixmodel': self.cbTanksMixingModel,
            'qgisred_query_tanks_tag': self.cbTanksTag
        })

        # Reservoirs mappings
        mapping.update({
            'qgisred_query_reservoirs_totalhead': self.cbReservoirsTotalHead,
            'qgisred_query_reservoirs_headpattern': self.cbReservoirsHeadPattern,
            'qgisred_query_reservoirs_initquality': self.cbReservoirsInitialQuality,
            'qgisred_query_reservoirs_tag': self.cbReservoirsTag
        })

        # Junctions mappings
        mapping.update({
            'qgisred_query_junctions_elevation': self.cbJunctionsElevation,
            'qgisred_query_junctions_totalbasedemand': self.cbJunctionsBaseDemand,
            'qgisred_query_junctions_patterndemand': self.cbJunctionsPatternDemand,
            'qgisred_query_junctions_emittercoeff': self.cbJunctionsEmitterCoeff,
            'qgisred_query_junctions_initquality': self.cbJunctionsInitialQuality,
            'qgisred_query_junctions_tag': self.cbJunctionsTag
        })

        # Valves mappings
        mapping.update({
            'qgisred_query_valves_type': self.cbValvesType,
            'qgisred_query_valves_diameter': self.cbValvesDiameter,
            'qgisred_query_valves_setting': self.cbValvesSetting,
            'qgisred_query_valves_initstatus': self.cbValvesInitialStatus,
            'qgisred_query_valves_losscoeff': self.cbValvesLossCoeff,
            'qgisred_query_valves_tag': self.cbValvesTag
        })

        # Pumps mappings
        mapping.update({
            'qgisred_query_pumps_type': self.cbPumpsType,
            'qgisred_query_pumps_pumpcurve': self.cbPumpsPumpCurve,
            'qgisred_query_pumps_power': self.cbPumpsPower,
            'qgisred_query_pumps_initstatus': self.cbPumpsInitialStatus,
            'qgisred_query_pumps_speed': self.cbPumpsSpeed,
            'qgisred_query_pumps_effcurve': self.cbPumpsEfficiencyCurve,
            'qgisred_query_pumps_energyprice': self.cbPumpsEnergyPrice,
            'qgisred_query_pumps_tag': self.cbPumpsTag
        })

        # Service Connection, Isolation Valves, and Meters mappings
        mapping.update({
            'qgisred_query_serviceconnection_temporary': self.cbPipesDiameter_3,  # Service Connection
            'qgisred_query_isolationvalves_temporary': self.cbTanksElevation_3,  # Isolation Valves
            'qgisred_query_meters_temporary': self.cbReservoirsTotalHead_3  # Meters
        })

        # Pipes mappings
        mapping.update({
            'qgisred_query_pipes_diameter': self.cbPipesDiameter,
            'qgisred_query_pipes_length': self.cbPipesLength,
            'qgisred_query_pipes_material': self.cbPipesMaterial,
            'qgisred_query_pipes_roughness': self.cbPipesRoughness,
            'qgisred_query_pipes_age': self.cbPipesAge,
            'qgisred_query_pipes_losscoeff': self.cbPipesLossCoeff,
            'qgisred_query_pipes_initstatus': self.cbPipesInitStatus,
            'qgisred_query_pipes_installyear': self.cbPipesInstallationDate,
            'qgisred_query_pipes_bulkcoeff': self.cbPipesBulkCoeff,
            'qgisred_query_pipes_wallcoeff': self.cbPipesWallCoeff,
            'qgisred_query_pipes_tag': self.cbPipesTag
        })

        return mapping

    def checkLayersRecursiveByIdentifier(self, group, identifierMapping):
        if not group:
            return

        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layerIdentifier = layer.customProperty("qgisred_identifier")
                    if layerIdentifier in identifierMapping:
                        checkbox = identifierMapping[layerIdentifier]
                        checkbox.setChecked(True)
                        checkbox.setToolTip(self.tr("Query already exists."))
            elif child.nodeType() == NODE_TYPE_LAYER:
                layers = child.checkedLayers()
                if layers:
                    layer = layers[0]
                    layerIdentifier = layer.customProperty("qgisred_identifier")
                    if layerIdentifier in identifierMapping:
                        checkbox = identifierMapping[layerIdentifier]
                        checkbox.setChecked(True)
                        checkbox.setToolTip(self.tr("Query already exists."))
            elif isinstance(child, QgsLayerTreeGroup):
                self.checkLayersRecursiveByIdentifier(child, identifierMapping)

    def getSelectedQueries(self):
        mapping = self.createIdentifierCheckboxMapping()
        selected = []
        for query in buildQueryCatalogue():
            checkbox = mapping.get(queryIdentifier(query))
            if checkbox is not None and checkbox.isChecked():
                selected.append(query)
        return selected
