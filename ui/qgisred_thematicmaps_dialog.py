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
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedThematicMapsDialog, self).__init__(parent)
        self.setupUi(self)
        self.setDialogStyle()
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)
        self.updateCheckboxStates()

    def setDialogStyle(self):
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(icon_path))

        group_boxes = [
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

        for group_box in group_boxes:
            self.setGroupBoxStyle(group_box)

    def setGroupBoxStyle(self, group_box):
        group_box.setStyleSheet("font-weight: bold;")
        for widget in group_box.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")

    def accept(self):
        root_group = self.get_root_group()

        inputs_group = self.find_group_by_name(root_group, 'Inputs')
        if inputs_group is None:
            QMessageBox.critical(self, 'Error', 'Inputs group not found.')
            return

        queries_group = self.get_or_create_queries_group(root_group, inputs_group)

        pipes_layer = self.find_layer_in_group(inputs_group, 'Pipes')
        if pipes_layer is None:
            return

        queries = self.get_selected_queries()

        for query in reversed(queries):
            self.process_query(query, pipes_layer, queries_group)

        # Close dialog
        super(QGISRedThematicMapsDialog, self).accept()

    def get_root_group(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        if isinstance(root, QgsLayerTreeGroup):
            return root
        else:
            return root.rootGroup()

    def find_group_by_name(self, parent_group, group_name):
        return parent_group.findGroup(group_name)

    def get_or_create_queries_group(self, root_group, inputs_group):
        inputs_parent = inputs_group.parent()
        if inputs_parent is None:
            inputs_parent = root_group

        queries_group = self.find_group_by_name(root_group, 'Queries')
        if queries_group is None:
            inputs_group_index = inputs_parent.children().index(inputs_group)
            queries_group = inputs_parent.insertGroup(inputs_group_index, 'Queries')
        else:
            if queries_group.parent() != inputs_parent:
                old_parent = queries_group.parent()
                old_parent.removeChildNode(queries_group)
                inputs_parent.insertChildNode(0, queries_group)
        return queries_group

    def find_layer_in_group(self, group, layer_name):
        for child in group.children():
            if child.nodeType() == QgsLayerTreeNode.NodeLayer and child.name() == layer_name and child.checkedLayers():
                return child.checkedLayers()[0]
            elif isinstance(child, QgsLayerTreeLayer) and child.name() == layer_name:
                return child.layer()
            elif isinstance(child, QgsLayerTreeGroup):
                layer = self.find_layer_in_group(child, layer_name)
                if layer is not None:
                    return layer
        return None

    def process_query(self, query, main_layer, queries_group):
        layer_name = query['layer_name']
        field = query['field']
        qml_file = query['qml_file']
        tooltip_prefix = query['tooltip_prefix']
        
        existing_layer, layer_position = self.find_layer_recursively(queries_group, layer_name)
        parent_group = queries_group
        layer_position = 0
        
        if existing_layer is not None:
            try:
                parent_group = existing_layer.parent()
                
                layer_id = None
                if isinstance(existing_layer, QgsLayerTreeLayer) and existing_layer.layer():
                    layer_id = existing_layer.layer().id()
                elif existing_layer.nodeType() == QgsLayerTreeNode.NodeLayer and existing_layer.checkedLayers():
                    layer_id = existing_layer.checkedLayers()[0].id()
                    
                if layer_id and QgsProject.instance().mapLayer(layer_id):
                    QgsProject.instance().removeMapLayer(layer_id)
                    
                if parent_group and not sip.isdeleted(parent_group):
                    parent_group.removeChildNode(existing_layer)
                    
            except Exception as e:
                print(f"Error removing layer: {e}")
        
        derived_layer = self.create_derived_layer(main_layer, layer_name, field)
        
        qml_path = self.load_qml_style(derived_layer, qml_file)
        derived_layer.setLabelsEnabled(False)
        derived_layer.setCustomProperty("query_field", field)
        
        if field == 'Material':
            QGISRedUtils().apply_categorized_renderer(derived_layer, field, qml_path)
            #self.set_labels_with_null_handling(derived_layer, field, qml_path)

        QgsProject.instance().addMapLayer(derived_layer, False)
        QGISRedUtils().hide_fields(derived_layer, field)

        if parent_group and not sip.isdeleted(parent_group):
            layer_tree_layer = parent_group.insertLayer(layer_position, derived_layer)
            layer_tree_layer.setCustomProperty("showFeatureCount", True)
        
        main_layer.dataChanged.connect(lambda: self.sync_layers(main_layer, derived_layer))
        main_layer.styleChanged.connect(lambda: self.sync_layers(main_layer, derived_layer))
        derived_layer.dataChanged.connect(lambda: derived_layer.triggerRepaint())
        derived_layer.setReadOnly(True)

        return derived_layer

    def find_layer_recursively(self, parent_group, layer_name):
        if not parent_group:
            return None, None
            
        for i, child in enumerate(parent_group.children()):
            if isinstance(child, QgsLayerTreeLayer):
                if child.name() == layer_name:
                    return child, i
            elif isinstance(child, QgsLayerTreeGroup):
                found_layer, found_position = self.find_layer_recursively(child, layer_name)
                if found_layer is not None:
                    return found_layer, found_position
        
        return None, None
    
    def sync_layers(self, main_layer, derived_layer):
        derived_layer.dataProvider().forceReload()
        new_renderer = main_layer.renderer().clone()
        derived_layer.setRenderer(new_renderer)
        derived_layer.triggerRepaint()

    def check_existing_layer(self, queries_group, layer_name, layer_path=None):
        existing_layer = None
        for child in queries_group.children():
            if isinstance(child, QgsLayerTreeLayer) and child.name() == layer_name:
                existing_layer = child
                break
        
        if existing_layer is not None:
            if layer_path and os.path.exists(layer_path):
                QgsVectorFileWriter.deleteShapeFile(layer_path)
            
            QgsProject.instance().removeMapLayer(existing_layer.id())
            return True
        
        return False

    def create_derived_layer(self, source_layer, new_layer_name, field):
        uri = source_layer.source()
        
        geometry_type = source_layer.geometryType()
        provider_type = source_layer.providerType()
        
        derived_layer = QgsVectorLayer(uri, new_layer_name, provider_type)
        
        if not derived_layer.isValid():
            raise Exception(f"Failed to create derived layer from {source_layer.name()}")

        derived_layer.setCrs(source_layer.crs())
        
        return derived_layer

    def load_qml_style(self, layer, qml_file):
        qml_path = os.path.join(os.path.dirname(__file__), '..', 'layerStyles', qml_file)
        if os.path.exists(qml_path):
            layer.loadNamedStyle(qml_path)
            layer.setCustomProperty("styleURI", qml_path)
            layer.triggerRepaint()
        return qml_path
    
    def assign_labels(self, layer, field, ):
        layer.setLabelsEnabled(True)
        labeling = layer.labeling()
        if labeling is not None:
            label_settings = labeling.clone()
            label_settings.fieldName = field
            layer.setLabeling(label_settings)

    def sync_symbology(self, main_layer, derived_layer):
        if derived_layer and main_layer:
            new_renderer = main_layer.renderer().clone()
            derived_layer.setRenderer(new_renderer)
            derived_layer.triggerRepaint()

    def set_labels_with_null_handling(self, layer, field_name, qml_file_path): 
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        # Create the label expression using coalesce to handle NULL values
        expression = f"""
                    CASE
                        WHEN "{field_name}" IS NULL THEN '#NA'
                        ELSE "{field_name}"
                    END
        """
        # Set up label settings
        label_settings = QgsPalLayerSettings()
        label_settings.fieldName = expression
        label_settings.isExpression = True
        label_settings.placement= QgsPalLayerSettings.OverPoint
        # Apply labeling to the layer
        labeling = QgsVectorLayerSimpleLabeling(label_settings)
        layer.setLabeling(labeling)

        layer.triggerRepaint()
    
    def updateCheckboxStates(self):
        root = QgsProject.instance().layerTreeRoot()
        queries_group = self.find_group_by_name(root, 'Queries')
        
        if not queries_group:
            return

        checkbox_mapping = {
            'Tank Elevations': self.cbTanksElevation,
            'Tank Diameters': self.cbTanksDiameter,
            'Tank Volumes': self.cbTanksVolume,
            'Tank Levels': self.cbTanksLevel,
            'Tank Initial Quality': self.cbTanksInitialQuality,
            'Tank Bulk Coefficient': self.cbTanksBulkCoeff,
            'Tank Mixing Models': self.cbTanksMixingModel,
            'Tank Tags': self.cbTanksTag,
            'Reservoir Total Head': self.cbReservoirsTotalHead,
            'Reservoir Head Patterns': self.cbReservoirsHeadPattern,
            'Reservoir Initial Quality': self.cbReservoirsInitialQuality,
            'Reservoir Tags': self.cbReservoirsTag,
            'Junction Elevations': self.cbJunctionsElevation,
            'Junction Base Demands': self.cbJunctionsBaseDemand,
            'Junction Pattern Demands': self.cbJunctionsPatternDemand,
            'Junction Emitter Coefficients': self.cbJunctionsEmitterCoeff,
            'Junction Initial Quality': self.cbJunctionsInitialQuality,
            'Junction Tags': self.cbJunctionsTag,
            'Valve Types': self.cbValvesType,
            'Valve Diameters': self.cbValvesDiameter,
            'Valve Settings': self.cbValvesSetting,
            'Valve Initial Status': self.cbValvesInitialStatus,
            'Valve Loss Coefficients': self.cbValvesLossCoeff,
            'Valve Tags': self.cbValvesTag,
            'Pump Types': self.cbPumpsType,
            'Pump Curves': self.cbPumpsPumpCurve,
            'Pump Power': self.cbPumpsPower,
            'Pump Initial Status': self.cbPumpsInitialStatus,
            'Pump Speed': self.cbPumpsSpeed,
            'Pump Efficiency Curves': self.cbPumpsEfficiencyCurve,
            'Pump Energy Price': self.cbPumpsEnergyPrice,
            'Pump Tags': self.cbPumpsTag,
            'Service Connection': self.cbPipesDiameter_3,
            'Isolation Valves': self.cbTanksElevation_3,
            'Meters': self.cbReservoirsTotalHead_3,
            'Pipe Diameters': self.cbPipesDiameter,
            'Pipe Lengths': self.cbPipesLength,
            'Pipe Materials': self.cbPipesMaterial,
            'Pipe Roughness': self.cbPipesRoughness,
            'Pipe Age': self.cbPipesAge,
            'Pipe Loss Coefficient': self.cbPipesLossCoeff,
            'Pipe Initial Status': self.cbPipesInitStatus,
            'Pipe Installation Date': self.cbPipesInstallationDate,
            'Pipe Bulk Coefficient': self.cbPipesBulkCoeff,
            'Pipe Wall Coefficient': self.cbPipesWallCoeff,
            'Pipe Tags': self.cbPipesTag
        }

        self.check_layers_recursive(queries_group, checkbox_mapping)

    def check_layers_recursive(self, group, checkbox_mapping):
        if not group:
            return

        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer_name = child.name()
                if layer_name in checkbox_mapping:
                    checkbox = checkbox_mapping[layer_name]
                    checkbox.setEnabled(False)
                    checkbox.setToolTip("Query already exists.")
            elif isinstance(child, QgsLayerTreeGroup):
                self.check_layers_recursive(child, checkbox_mapping)

    def get_selected_queries(self):
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
                'qml_file': f'pipe_diameters_{units}.qml',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbPipesLength.isChecked():
            queries.append({
                'layer_name': 'Pipe Lengths',
                'field': 'Length',
                'qml_file': f'pipe_lengths_{units}.qml',
                'file_name': f'length_{units}',
                'tooltip_prefix': 'Len'
            })

        if self.cbPipesMaterial.isChecked():
            queries.append({
                'layer_name': 'Pipe Materials',
                'field': 'Material',
                'qml_file': 'pipe_materials.qml',
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