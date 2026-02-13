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
        self.tempElementsHide()

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
        
        current_width = self.width()
        self.adjustSize()
        self.resize(current_width, self.height())

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

        selected_queries = self.get_selected_queries()
        current_valid_identifiers = set(
            f"qgisred_query_{query['field'].lower()}_{query['tooltip_prefix'].lower()}"
            for query in selected_queries
        )
        to_remove_identifiers = self.initial_valid_identifiers - current_valid_identifiers

        if not selected_queries and not to_remove_identifiers:
            super().accept()
            return

        self.remove_query_layers_by_identifiers(to_remove_identifiers)

        queries_group = self.find_group_by_name(root_group, 'Queries')
        if queries_group and not queries_group.children():
            parent = queries_group.parent()
            if parent:
                parent.removeChildNode(queries_group)

        if selected_queries:
            queries_group = self.get_or_create_queries_group(root_group, inputs_group)
            pipes_layer = self.find_layer_in_group(inputs_group, 'Pipes')
            if pipes_layer is None:
                return

            new_queries = [
                query for query in selected_queries
                if f"qgisred_query_{query['field'].lower()}_{query['tooltip_prefix'].lower()}" 
                in (current_valid_identifiers - self.initial_valid_identifiers)
            ]

            for query in reversed(new_queries):
                self.process_query(query, pipes_layer, queries_group)

        super().accept()

    def remove_query_layers_by_identifiers(self, identifiers_to_remove):
        if not identifiers_to_remove:
            return
        root = QgsProject.instance().layerTreeRoot()
        queries_group = self.find_group_by_name(root, 'Queries')
        if queries_group:
            self.recursiveremove_by_identifiers(queries_group, identifiers_to_remove)

    def recursiveremove_by_identifiers(self, group, identifiers):
        for child in list(group.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layer_id = layer.customProperty("qgisred_identifier")
                    if layer_id in identifiers:
                        QgsProject.instance().removeMapLayer(layer.id())
            elif isinstance(child, QgsLayerTreeGroup):
                self.recursiveremove_by_identifiers(child, identifiers)

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
        
        # Generate a unique identifier for the layer
        layer_identifier = f"qgisred_query_{field.lower()}_{tooltip_prefix.lower()}"
        
        # Find existing layer by identifier instead of name
        existing_layer, layer_position = self.find_layer_by_identifier(queries_group, layer_identifier)
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
        
        derived_layer.setCustomProperty("query_field", field)
        
        qml_path = self.load_qml_style(derived_layer, qml_file)
        derived_layer.setLabelsEnabled(False)
        
        if field == 'Material':
            QGISRedUtils().apply_categorized_renderer(derived_layer, field, qml_path)

        derived_layer.setCustomProperty("qgisred_identifier", layer_identifier)
        
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
    
    def find_layer_by_identifier(self, parent_group, identifier):
        if not parent_group:
            return None, None
            
        for i, child in enumerate(parent_group.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layer_identifier = child.customProperty("qgisred_identifier")
                if layer_identifier == identifier:
                    return child, i
            elif isinstance(child, QgsLayerTreeGroup):
                found_layer, found_position = self.find_layer_by_identifier(child, identifier)
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

        checkbox_mapping = self.create_identifier_checkbox_mapping()
        if queries_group:
            self.check_layers_recursive_by_identifier(queries_group, checkbox_mapping)
        
        self.initial_valid_identifiers = self.collect_existing_identifiers(queries_group) if queries_group else set()

    def collect_existing_identifiers(self, group):
        identifiers = set()
        def recursive_collect(g):
            for child in g.children():
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer:
                        identifier = layer.customProperty("qgisred_identifier")
                        if identifier:
                            identifiers.add(identifier)
                elif isinstance(child, QgsLayerTreeGroup):
                    recursive_collect(child)  # FIXED: Pass 'child' instead of 'g'
        recursive_collect(group)
        return identifiers

    def create_identifier_checkbox_mapping(self):
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

    def check_layers_recursive_by_identifier(self, group, identifier_mapping):
        if not group:
            return

        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layer_identifier = layer.customProperty("qgisred_identifier")
                    if layer_identifier in identifier_mapping:
                        checkbox = identifier_mapping[layer_identifier]
                        checkbox.setChecked(True)
                        checkbox.setToolTip("Query already exists.")
            elif child.nodeType() == QgsLayerTreeNode.NodeLayer:
                layers = child.checkedLayers()
                if layers:
                    layer = layers[0]
                    layer_identifier = layer.customProperty("qgisred_identifier")
                    if layer_identifier in identifier_mapping:
                        checkbox = identifier_mapping[layer_identifier]
                        checkbox.setChecked(True)
                        checkbox.setToolTip("Query already exists.")
            elif isinstance(child, QgsLayerTreeGroup):
                self.check_layers_recursive_by_identifier(child, identifier_mapping)

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