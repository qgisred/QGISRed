# -*- coding: utf-8 -*-

# Standard library imports
import os

# Third-party imports
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget
from PyQt5 import sip
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QVariant

# QGIS imports
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsLayerTreeNode, QgsProject
from qgis.core import QgsVectorFileWriter, QgsVectorLayer
from qgis.core import QgsProject, QgsVectorLayer, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat
from qgis.utils import iface

# Local imports
from ..tools.qgisred_utils import QGISRedUtils

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

    def tempElementsHide(self):
        self.gbJunctions.hide()
        self.gbValves.hide()
        self.gbPumps.hide()
        self.gbTanks.hide()
        self.gbReservoirs.hide()

        self.cbPipesRoughness.hide()
        self.cbPipesAge.hide()
        self.cbPipesLossCoeff.hide()
        self.cbPipesInitStatus.hide()
        self.cbPipesInstallationDate.hide()
        self.cbPipesBulkCoeff.hide()
        self.cbPipesWallCoeff.hide()
        self.cbPipesTag.hide()
        
        self.tabWidget.setTabVisible(1, False)
        
        currentWidth = self.width()
        self.adjustSize()
        self.resize(currentWidth, self.height())

    def setDialogStyle(self):
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(iconPath))

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
        rootGroup = self.getRootGroup()
        inputsGroup = self.findGroupByName(rootGroup, 'Inputs')
        if inputsGroup is None:
            QMessageBox.critical(self, self.tr('Error'),'Inputs ' + self.tr('group not found.'))
            return

        selectedQueries = self.getSelectedQueries()
        currentValidIdentifiers = set(
            f"qgisred_query_{query['field'].lower()}_{query['tooltip_prefix'].lower()}"
            for query in selectedQueries
        )
        toRemoveIdentifiers = self.initialValidIdentifiers - currentValidIdentifiers

        if not selectedQueries and not toRemoveIdentifiers:
            super().accept()
            return

        # remove old layers (supports both old location under 'Queries' and new under 'Thematic Maps')
        self.removeQueryLayersByIdentifiers(toRemoveIdentifiers)

        # cleanup empty groups first
        queriesGroup = self.findGroupByName(rootGroup, 'Queries')
        if queriesGroup:
            thematicGroup = self.findGroupByName(queriesGroup, 'Thematic Maps')
            if thematicGroup and not thematicGroup.children():
                queriesGroup.removeChildNode(thematicGroup)
            if not queriesGroup.children():
                parent = queriesGroup.parent()
                if parent:
                    parent.removeChildNode(queriesGroup)

        if selectedQueries:
            # now ensure Queries → Thematic Maps hierarchy exists
            thematicGroup = self.getOrCreateQueriesGroup(rootGroup, inputsGroup)

            pipesLayer = self.findLayerInGroup(inputsGroup, 'Pipes', 'qgisred_pipes')
            print("pipesLayer : ", pipesLayer)
            if pipesLayer is None:
                super().accept()
                return

            newQueries = [
                query for query in selectedQueries
                if f"qgisred_query_{query['field'].lower()}_{query['tooltip_prefix'].lower()}" 
                in (currentValidIdentifiers - self.initialValidIdentifiers)
            ]

            for query in reversed(newQueries):
                self.processQuery(query, pipesLayer, thematicGroup)

        super().accept()

    def removeQueryLayersByIdentifiers(self, identifiersToRemove):
        if not identifiersToRemove:
            return
        root = QgsProject.instance().layerTreeRoot()

        # Prefer Queries → Thematic Maps, but fall back to Queries (for legacy layers)
        queriesGroup = self.findGroupByName(root, 'Queries')
        targetGroup = None
        if queriesGroup:
            thematicGroup = self.findGroupByName(queriesGroup, 'Thematic Maps')
            targetGroup = thematicGroup or queriesGroup

        if targetGroup:
            self.recursiveRemoveByIdentifiers(targetGroup, identifiersToRemove)

            # tidy up if groups become empty
            if thematicGroup and not thematicGroup.children():
                queriesGroup.removeChildNode(thematicGroup)
            if queriesGroup and not queriesGroup.children():
                parent = queriesGroup.parent()
                if parent:
                    parent.removeChildNode(queriesGroup)

    def recursiveRemoveByIdentifiers(self, group, identifiers):
        for child in list(group.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layerId = layer.customProperty("qgisred_identifier")
                    if layerId in identifiers:
                        QgsProject.instance().removeMapLayer(layer.id())
            elif isinstance(child, QgsLayerTreeGroup):
                self.recursiveRemoveByIdentifiers(child, identifiers)

    def getRootGroup(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        if isinstance(root, QgsLayerTreeGroup):
            return root
        else:
            return root.rootGroup()

    def findGroupByName(self, parentGroup, groupName):
        return parentGroup.findGroup(groupName)

    def getOrCreateQueriesGroup(self, rootGroup, inputsGroup):
        inputsParent = inputsGroup.parent()
        if inputsParent is None:
            inputsParent = rootGroup
        networkName = inputsParent.name() if inputsParent != rootGroup else ""
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if networkName:
            return utils.getOrCreateNestedGroup([networkName, "Queries", "Thematic Maps"])
        else:
            return utils.getOrCreateNestedGroup(["Queries", "Thematic Maps"])

    def findLayerInGroup(self, group, layerName=None, custom_property=None):
        for child in group.children():
            if custom_property:
                # Search by custom property
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer and layer.customProperty('qgisred_identifier') == custom_property:
                        return layer
            else:
                # Search by layer name (original behavior)
                if child.nodeType() == QgsLayerTreeNode.NodeLayer and child.name() == layerName and child.checkedLayers():
                    return child.checkedLayers()[0]
                elif isinstance(child, QgsLayerTreeLayer) and child.name() == layerName:
                    return child.layer()
            
            # Recursively search in subgroups
            if isinstance(child, QgsLayerTreeGroup):
                layer = self.findLayerInGroup(child, layerName, custom_property)
                if layer is not None:
                    return layer
        return None
    
    def processQuery(self, query, mainLayer, queriesGroup):
        layerName = query['layer_name']
        field = query['field']
        qmlFile = query['qml_file']
        tooltipPrefix = query['tooltip_prefix']
        
        # Generate a unique identifier for the layer
        layerIdentifier = f"qgisred_query_{field.lower()}_{tooltipPrefix.lower()}"
        
        # Find existing layer by identifier instead of name
        existingLayer, layerPosition = self.findLayerByIdentifier(queriesGroup, layerIdentifier)
        parentGroup = queriesGroup
        layerPosition = 0
        
        if existingLayer is not None:
            try:
                parentGroup = existingLayer.parent()
                
                layerId = None
                if isinstance(existingLayer, QgsLayerTreeLayer) and existingLayer.layer():
                    layerId = existingLayer.layer().id()
                elif existingLayer.nodeType() == QgsLayerTreeNode.NodeLayer and existingLayer.checkedLayers():
                    layerId = existingLayer.checkedLayers()[0].id()
                    
                if layerId and QgsProject.instance().mapLayer(layerId):
                    QgsProject.instance().removeMapLayer(layerId)
                    
                if parentGroup and not sip.isdeleted(parentGroup):
                    parentGroup.removeChildNode(existingLayer)
                    
            except Exception as e:
                print(f"Error removing layer: {e}")
        
        derivedLayer = self.createDerivedLayer(mainLayer, layerName, field)
        
        derivedLayer.setCustomProperty("query_field", field)
        
        qmlPath = self.loadQmlStyle(derivedLayer, qmlFile)
        derivedLayer.setLabelsEnabled(False)
        
        if field == 'Material':
            QGISRedUtils().apply_categorized_renderer(derivedLayer, field, qmlPath)

        derivedLayer.setCustomProperty("qgisred_identifier", layerIdentifier)
        
        QgsProject.instance().addMapLayer(derivedLayer, False)
        QGISRedUtils().hide_fields(derivedLayer, field)

        if parentGroup and not sip.isdeleted(parentGroup):
            layerTreeLayer = parentGroup.insertLayer(layerPosition, derivedLayer)
            layerTreeLayer.setCustomProperty("showFeatureCount", True)

        mainLayer.dataChanged.connect(lambda: self.syncLayers(mainLayer, derivedLayer))
        mainLayer.styleChanged.connect(lambda: self.syncLayers(mainLayer, derivedLayer))
        derivedLayer.dataChanged.connect(lambda: derivedLayer.triggerRepaint())
        derivedLayer.setReadOnly(True)

        return derivedLayer
    
    def findLayerByIdentifier(self, parentGroup, identifier):
        if not parentGroup:
            return None, None
            
        for i, child in enumerate(parentGroup.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layerIdentifier = child.customProperty("qgisred_identifier")
                if layerIdentifier == identifier:
                    return child, i
            elif isinstance(child, QgsLayerTreeGroup):
                foundLayer, foundPosition = self.findLayerByIdentifier(child, identifier)
                if foundLayer is not None:
                    return foundLayer, foundPosition
        
        return None, None
    
    def syncLayers(self, mainLayer, derivedLayer):
        derivedLayer.dataProvider().forceReload()
        newRenderer = mainLayer.renderer().clone()
        derivedLayer.setRenderer(newRenderer)
        derivedLayer.triggerRepaint()

    def checkExistingLayer(self, queriesGroup, layerName, layerPath=None):
        existingLayer = None
        for child in queriesGroup.children():
            if isinstance(child, QgsLayerTreeLayer) and child.name() == layerName:
                existingLayer = child
                break
        
        if existingLayer is not None:
            if layerPath and os.path.exists(layerPath):
                QgsVectorFileWriter.deleteShapeFile(layerPath)
            
            QgsProject.instance().removeMapLayer(existingLayer.id())
            return True
        
        return False

    def createDerivedLayer(self, sourceLayer, newLayerName, field):
        uri = sourceLayer.source()
        
        geometryType = sourceLayer.geometryType()
        providerType = sourceLayer.providerType()
        
        derivedLayer = QgsVectorLayer(uri, newLayerName, providerType)
        
        if not derivedLayer.isValid():
            raise Exception(self.tr(f"Failed to create derived layer from {sourceLayer.name()}"))

        derivedLayer.setCrs(sourceLayer.crs())
        
        return derivedLayer

    def loadQmlStyle(self, layer, qmlFile):
        # Convert qmlFile to .qml.bak format if not already
        if not qmlFile.endswith('.qml.bak'):
            qmlFile = qmlFile.replace('.qml', '.qml.bak')

        qmlPath = os.path.join(os.path.dirname(__file__), '..', 'defaults', 'layerStyles', qmlFile)
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            layer.setCustomProperty("styleURI", qmlPath)
            layer.triggerRepaint()
        return qmlPath
    
    def assignLabels(self, layer, field, ):
        layer.setLabelsEnabled(True)
        labeling = layer.labeling()
        if labeling is not None:
            labelSettings = labeling.clone()
            labelSettings.fieldName = field
            layer.setLabeling(labelSettings)

    def syncSymbology(self, mainLayer, derivedLayer):
        if derivedLayer and mainLayer:
            newRenderer = mainLayer.renderer().clone()
            derivedLayer.setRenderer(newRenderer)
            derivedLayer.triggerRepaint()

    def setLabelsWithNullHandling(self, layer, fieldName, qmlFilePath): 
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        # Create the label expression using coalesce to handle NULL values
        expression = f"""
                    CASE
                        WHEN "{fieldName}" IS NULL THEN '#NA'
                        ELSE "{fieldName}"
                    END
        """
        # Set up label settings
        labelSettings = QgsPalLayerSettings()
        labelSettings.fieldName = expression
        labelSettings.isExpression = True
        labelSettings.placement= QgsPalLayerSettings.OverPoint
        # Apply labeling to the layer
        labeling = QgsVectorLayerSimpleLabeling(labelSettings)
        layer.setLabeling(labeling)

        layer.triggerRepaint()
    
    def updateCheckboxStates(self):
        root = QgsProject.instance().layerTreeRoot()
        queriesGroup = self.findGroupByName(root, 'Queries')
        thematicGroup = self.findGroupByName(queriesGroup, 'Thematic Maps') if queriesGroup else None
        targetGroup = thematicGroup or queriesGroup  # support legacy placement

        checkboxMapping = self.createIdentifierCheckboxMapping()
        if targetGroup:
            self.checkLayersRecursiveByIdentifier(targetGroup, checkboxMapping)

        self.initialValidIdentifiers = self.collectExistingIdentifiers(targetGroup) if targetGroup else set()

    def collectExistingIdentifiers(self, group):
        identifiers = set()
        def recursiveCollect(g):
            for child in g.children():
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer:
                        identifier = layer.customProperty("qgisred_identifier")
                        if identifier:
                            identifiers.add(identifier)
                elif isinstance(child, QgsLayerTreeGroup):
                    recursiveCollect(child)  # FIXED: Pass 'child' instead of 'g'
        recursiveCollect(group)
        return identifiers

    def createIdentifierCheckboxMapping(self):
        mapping = {}
        
        # Tanks mappings
        mapping.update({
            'qgisred_query_elevation_elev': self.cbTanksElevation,
            'qgisred_query_diameter_diam': self.cbTanksDiameter,
            'qgisred_query_volume_vol': self.cbTanksVolume,
            'qgisred_query_level_level': self.cbTanksLevel,
            'qgisred_query_initquality_quality': self.cbTanksInitialQuality,
            'qgisred_query_bulkcoeff_bulk': self.cbTanksBulkCoeff,
            'qgisred_query_mixmodel_mix': self.cbTanksMixingModel,
            'qgisred_query_tag_tag': self.cbTanksTag
        })

        # Reservoirs mappings
        mapping.update({
            'qgisred_query_totalhead_head': self.cbReservoirsTotalHead,
            'qgisred_query_headpattern_pattern': self.cbReservoirsHeadPattern,
            'qgisred_query_initquality_quality': self.cbReservoirsInitialQuality,
            'qgisred_query_tag_tag': self.cbReservoirsTag
        })

        # Junctions mappings
        mapping.update({
            'qgisred_query_elevation_elev': self.cbJunctionsElevation,
            'qgisred_query_basedemand_demand': self.cbJunctionsBaseDemand,
            'qgisred_query_patterndemand_pattern': self.cbJunctionsPatternDemand,
            'qgisred_query_emittercoeff_emitter': self.cbJunctionsEmitterCoeff,
            'qgisred_query_initquality_quality': self.cbJunctionsInitialQuality,
            'qgisred_query_tag_tag': self.cbJunctionsTag
        })

        # Valves mappings
        mapping.update({
            'qgisred_query_type_type': self.cbValvesType,
            'qgisred_query_diameter_diam': self.cbValvesDiameter,
            'qgisred_query_setting_set': self.cbValvesSetting,
            'qgisred_query_initstatus_status': self.cbValvesInitialStatus,
            'qgisred_query_losscoeff_loss': self.cbValvesLossCoeff,
            'qgisred_query_tag_tag': self.cbValvesTag
        })

        # Pumps mappings
        mapping.update({
            'qgisred_query_type_type': self.cbPumpsType,
            'qgisred_query_pumpcurve_curve': self.cbPumpsPumpCurve,
            'qgisred_query_power_power': self.cbPumpsPower,
            'qgisred_query_initstatus_status': self.cbPumpsInitialStatus,
            'qgisred_query_speed_speed': self.cbPumpsSpeed,
            'qgisred_query_effcurve_eff': self.cbPumpsEfficiencyCurve,
            'qgisred_query_energyprice_price': self.cbPumpsEnergyPrice,
            'qgisred_query_tag_tag': self.cbPumpsTag
        })

        # Service Connection, Isolation Valves, and Meters mappings
        mapping.update({
            'qgisred_query_temporary_temp': self.cbPipesDiameter_3,  # Service Connection
            'qgisred_query_temporary_temp': self.cbTanksElevation_3,  # Isolation Valves
            'qgisred_query_temporary_temp': self.cbReservoirsTotalHead_3  # Meters
        })

        # Pipes mappings
        mapping.update({
            'qgisred_query_diameter_diam': self.cbPipesDiameter,
            'qgisred_query_length_len': self.cbPipesLength,
            'qgisred_query_material_mat': self.cbPipesMaterial,
            'qgisred_query_roughness_rough': self.cbPipesRoughness,
            'qgisred_query_age_age': self.cbPipesAge,
            'qgisred_query_losscoeff_loss': self.cbPipesLossCoeff,
            'qgisred_query_initstatus_status': self.cbPipesInitStatus,
            'qgisred_query_installdate_inst': self.cbPipesInstallationDate,
            'qgisred_query_bulkcoeff_bulk': self.cbPipesBulkCoeff,
            'qgisred_query_wallcoeff_wall': self.cbPipesWallCoeff,
            'qgisred_query_tag_tag': self.cbPipesTag
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
            elif child.nodeType() == QgsLayerTreeNode.NodeLayer:
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
        units = QGISRedUtils().getUnits()
        queries = []

        # Tanks and Reservoirs queries (top)
        # Tanks queries
        if self.cbTanksElevation.isChecked():
            queries.append({
                'layer_name': 'Tank Elevations',
                'field': 'Elevation',
                'qml_file': f'tank_elevations_{units}.qml',
                'file_name': f'elevation_{units}',
                'tooltip_prefix': 'Elev'
            })

        if self.cbTanksDiameter.isChecked():
            queries.append({
                'layer_name': 'Tank Diameters',
                'field': 'Diameter',
                'qml_file': f'tank_diameters_{units}.qml',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbTanksVolume.isChecked():
            queries.append({
                'layer_name': 'Tank Volumes',
                'field': 'Volume',
                'qml_file': f'tank_volumes_{units}.qml',
                'file_name': f'volume_{units}',
                'tooltip_prefix': 'Vol'
            })

        if self.cbTanksLevel.isChecked():
            queries.append({
                'layer_name': 'Tank Levels',
                'field': 'Level',
                'qml_file': f'tank_levels_{units}.qml',
                'file_name': f'level_{units}',
                'tooltip_prefix': 'Level'
            })

        if self.cbTanksInitialQuality.isChecked():
            queries.append({
                'layer_name': 'Tank Initial Quality',
                'field': 'InitQuality',
                'qml_file': 'tank_init_quality.qml',
                'file_name': 'init_quality',
                'tooltip_prefix': 'Quality'
            })

        if self.cbTanksBulkCoeff.isChecked():
            queries.append({
                'layer_name': 'Tank Bulk Coefficient',
                'field': 'BulkCoeff',
                'qml_file': 'tank_bulk_coeff.qml',
                'file_name': 'bulk_coeff',
                'tooltip_prefix': 'Bulk'
            })

        if self.cbTanksMixingModel.isChecked():
            queries.append({
                'layer_name': 'Tank Mixing Models',
                'field': 'MixModel',
                'qml_file': 'tank_mixing_model.qml',
                'file_name': 'mixing_model',
                'tooltip_prefix': 'Mix'
            })

        if self.cbTanksTag.isChecked():
            queries.append({
                'layer_name': 'Tank Tags',
                'field': 'Tag',
                'qml_file': 'tank_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        # Reservoirs queries
        if self.cbReservoirsTotalHead.isChecked():
            queries.append({
                'layer_name': 'Reservoir Total Head',
                'field': 'TotalHead',
                'qml_file': f'reservoir_total_head_{units}.qml',
                'file_name': f'total_head_{units}',
                'tooltip_prefix': 'Head'
            })

        if self.cbReservoirsHeadPattern.isChecked():
            queries.append({
                'layer_name': 'Reservoir Head Patterns',
                'field': 'HeadPattern',
                'qml_file': 'reservoir_head_pattern.qml',
                'file_name': 'head_pattern',
                'tooltip_prefix': 'Pattern'
            })

        if self.cbReservoirsInitialQuality.isChecked():
            queries.append({
                'layer_name': 'Reservoir Initial Quality',
                'field': 'InitQuality',
                'qml_file': 'reservoir_init_quality.qml',
                'file_name': 'init_quality',
                'tooltip_prefix': 'Quality'
            })

        if self.cbReservoirsTag.isChecked():
            queries.append({
                'layer_name': 'Reservoir Tags',
                'field': 'Tag',
                'qml_file': 'reservoir_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        # Junctions queries (second from top)
        if self.cbJunctionsElevation.isChecked():
            queries.append({
                'layer_name': 'Junction Elevations',
                'field': 'Elevation',
                'qml_file': f'junction_elevation_{units}.qml',
                'file_name': f'elevation_{units}',
                'tooltip_prefix': 'Elev'
            })

        if self.cbJunctionsBaseDemand.isChecked():
            queries.append({
                'layer_name': 'Junction Base Demands',
                'field': 'BaseDemand',
                'qml_file': 'junction_base_demand.qml',
                'file_name': 'base_demand',
                'tooltip_prefix': 'Demand'
            })

        if self.cbJunctionsPatternDemand.isChecked():
            queries.append({
                'layer_name': 'Junction Pattern Demands',
                'field': 'PatternDemand',
                'qml_file': 'junction_pattern_demand.qml',
                'file_name': 'pattern_demand',
                'tooltip_prefix': 'Pattern'
            })

        if self.cbJunctionsEmitterCoeff.isChecked():
            queries.append({
                'layer_name': 'Junction Emitter Coefficients',
                'field': 'EmitterCoeff',
                'qml_file': 'junction_emitter_coeff.qml',
                'file_name': 'emitter_coeff',
                'tooltip_prefix': 'Emitter'
            })

        if self.cbJunctionsInitialQuality.isChecked():
            queries.append({
                'layer_name': 'Junction Initial Quality',
                'field': 'InitQuality',
                'qml_file': 'junction_init_quality.qml',
                'file_name': 'init_quality',
                'tooltip_prefix': 'Quality'
            })

        if self.cbJunctionsTag.isChecked():
            queries.append({
                'layer_name': 'Junction Tags',
                'field': 'Tag',
                'qml_file': 'junction_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        # Valves and Pumps queries (third from top)
        # Valves queries
        if self.cbValvesType.isChecked():
            queries.append({
                'layer_name': 'Valve Types',
                'field': 'Type',
                'qml_file': 'valve_types.qml',
                'file_name': 'type',
                'tooltip_prefix': 'Type'
            })

        if self.cbValvesDiameter.isChecked():
            queries.append({
                'layer_name': 'Valve Diameters',
                'field': 'Diameter',
                'qml_file': f'valve_diameters_{units}.qml',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbValvesSetting.isChecked():
            queries.append({
                'layer_name': 'Valve Settings',
                'field': 'Setting',
                'qml_file': 'valve_settings.qml',
                'file_name': 'setting',
                'tooltip_prefix': 'Set'
            })

        if self.cbValvesInitialStatus.isChecked():
            queries.append({
                'layer_name': 'Valve Initial Status',
                'field': 'InitStatus',
                'qml_file': 'valve_init_status.qml',
                'file_name': 'init_status',
                'tooltip_prefix': 'Status'
            })

        if self.cbValvesLossCoeff.isChecked():
            queries.append({
                'layer_name': 'Valve Loss Coefficients',
                'field': 'LossCoeff',
                'qml_file': 'valve_loss_coeff.qml',
                'file_name': 'loss_coeff',
                'tooltip_prefix': 'Loss'
            })

        if self.cbValvesTag.isChecked():
            queries.append({
                'layer_name': 'Valve Tags',
                'field': 'Tag',
                'qml_file': 'valve_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        # Pumps queries
        if self.cbPumpsType.isChecked():
            queries.append({
                'layer_name': 'Pump Types',
                'field': 'Type',
                'qml_file': 'pump_types.qml',
                'file_name': 'type',
                'tooltip_prefix': 'Type'
            })

        if self.cbPumpsPumpCurve.isChecked():
            queries.append({
                'layer_name': 'Pump Curves',
                'field': 'PumpCurve',
                'qml_file': 'pump_curves.qml',
                'file_name': 'pump_curve',
                'tooltip_prefix': 'Curve'
            })

        if self.cbPumpsPower.isChecked():
            queries.append({
                'layer_name': 'Pump Power',
                'field': 'Power',
                'qml_file': 'pump_power.qml',
                'file_name': 'power',
                'tooltip_prefix': 'Power'
            })

        if self.cbPumpsInitialStatus.isChecked():
            queries.append({
                'layer_name': 'Pump Initial Status',
                'field': 'InitStatus',
                'qml_file': 'pump_init_status.qml',
                'file_name': 'init_status',
                'tooltip_prefix': 'Status'
            })

        if self.cbPumpsSpeed.isChecked():
            queries.append({
                'layer_name': 'Pump Speed',
                'field': 'Speed',
                'qml_file': 'pump_speed.qml',
                'file_name': 'speed',
                'tooltip_prefix': 'Speed'
            })

        if self.cbPumpsEfficiencyCurve.isChecked():
            queries.append({
                'layer_name': 'Pump Efficiency Curves',
                'field': 'EffCurve',
                'qml_file': 'pump_efficiency_curves.qml',
                'file_name': 'efficiency_curve',
                'tooltip_prefix': 'Eff'
            })

        if self.cbPumpsEnergyPrice.isChecked():
            queries.append({
                'layer_name': 'Pump Energy Price',
                'field': 'EnergyPrice',
                'qml_file': 'pump_energy_price.qml',
                'file_name': 'energy_price',
                'tooltip_prefix': 'Price'
            })

        if self.cbPumpsTag.isChecked():
            queries.append({
                'layer_name': 'Pump Tags',
                'field': 'Tag',
                'qml_file': 'pump_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        # Service Connections queries
        if self.cbPipesDiameter_3.isChecked():
            queries.append({
                'layer_name': 'Service Connection',
                'field': 'Temporary',
                'qml_file': 'service_connection.qml',
                'file_name': 'temporary',
                'tooltip_prefix': 'Temp'
            })

        # Isolation Valves queries
        if self.cbTanksElevation_3.isChecked():
            queries.append({
                'layer_name': 'Isolation Valves',
                'field': 'Temporary',
                'qml_file': 'isolation_valves.qml',
                'file_name': 'temporary',
                'tooltip_prefix': 'Temp'
            })

        # Meters queries
        if self.cbReservoirsTotalHead_3.isChecked():
            queries.append({
                'layer_name': 'Meters',
                'field': 'Temporary',
                'qml_file': 'meters.qml',
                'file_name': 'temporary',
                'tooltip_prefix': 'Temp'
            })

        # Pipes queries (bottom)
        if self.cbPipesDiameter.isChecked():
            queries.append({
                'layer_name': 'Pipe Diameters',
                'field': 'Diameter',
                'qml_file': f'PipeDiameters{units}.qml',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbPipesLength.isChecked():
            queries.append({
                'layer_name': 'Pipe Lengths',
                'field': 'Length',
                'qml_file': f'PipeLengths{units}.qml',
                'file_name': f'length_{units}',
                'tooltip_prefix': 'Len'
            })

        if self.cbPipesMaterial.isChecked():
            queries.append({
                'layer_name': 'Pipe Materials',
                'field': 'Material',
                'qml_file': 'PipeMaterials.qml',
                'file_name': 'material',
                'tooltip_prefix': 'Mat'
            })

        if self.cbPipesRoughness.isChecked():
            queries.append({
                'layer_name': 'Pipe Roughness',
                'field': 'Roughness',
                'qml_file': 'pipe_roughness.qml',
                'file_name': 'roughness',
                'tooltip_prefix': 'Rough'
            })

        if self.cbPipesAge.isChecked():
            queries.append({
                'layer_name': 'Pipe Age',
                'field': 'Age',
                'qml_file': 'pipe_age.qml',
                'file_name': 'age',
                'tooltip_prefix': 'Age'
            })

        if self.cbPipesLossCoeff.isChecked():
            queries.append({
                'layer_name': 'Pipe Loss Coefficient',
                'field': 'LossCoeff',
                'qml_file': 'pipe_loss_coeff.qml',
                'file_name': 'loss_coeff',
                'tooltip_prefix': 'Loss'
            })

        if self.cbPipesInitStatus.isChecked():
            queries.append({
                'layer_name': 'Pipe Initial Status',
                'field': 'InitStatus',
                'qml_file': 'pipe_init_status.qml',
                'file_name': 'init_status',
                'tooltip_prefix': 'Status'
            })

        if self.cbPipesInstallationDate.isChecked():
            queries.append({
                'layer_name': 'Pipe Installation Date',
                'field': 'InstallDate',
                'qml_file': 'pipe_install_date.qml',
                'file_name': 'install_date',
                'tooltip_prefix': 'Inst'
            })

        if self.cbPipesBulkCoeff.isChecked():
            queries.append({
                'layer_name': 'Pipe Bulk Coefficient',
                'field': 'BulkCoeff',
                'qml_file': 'pipe_bulk_coeff.qml',
                'file_name': 'bulk_coeff',
                'tooltip_prefix': 'Bulk'
            })

        if self.cbPipesWallCoeff.isChecked():
            queries.append({
                'layer_name': 'Pipe Wall Coefficient',
                'field': 'WallCoeff',
                'qml_file': 'pipe_wall_coeff.qml',
                'file_name': 'wall_coeff',
                'tooltip_prefix': 'Wall'
            })

        if self.cbPipesTag.isChecked():
            queries.append({
                'layer_name': 'Pipe Tags',
                'field': 'Tag',
                'qml_file': 'pipe_tags.qml',
                'file_name': 'tags',
                'tooltip_prefix': 'Tag'
            })

        return queries