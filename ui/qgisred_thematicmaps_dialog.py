# -*- coding: utf-8 -*-

# Standard library imports
import os

# Third-party imports
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox, QWidget
from qgis.PyQt import uic

# QGIS imports
from qgis.core import QgsAttributeTableConfig, QgsLayerTreeGroup, QgsLayerTreeLayer, QgsLayerTreeNode, QgsProject
from qgis.core import QgsVectorFileWriter, QgsVectorLayer, QgsVectorLayerCache
from qgis.gui import QgsAttributeTableFilterModel, QgsAttributeTableModel, QgsAttributeTableView
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

    def setDialogStyle(self):
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(icon_path))

        group_boxes = [
            self.gbPipes,
            self.gbJunctions,
            self.gbValves,
            self.gbPumps,
            self.gbTanks,
            self.gbReservoirs
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
            QMessageBox.critical(self, 'Error', 'Pipes layer not found in Inputs group.')
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

    def get_selected_queries(self):
        units = QGISRedUtils().getUnits()
        queries = []

        if self.cbPipesDiameter.isChecked():
            queries.append({
                'layer_name': 'Pipe Diameters',
                'field': 'Diameter',
                'qml_file': f'pipes_diameters_{units}.qml.bak',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbPipesLength.isChecked():
            queries.append({
                'layer_name': 'Pipe Lengths',
                'field': 'Length',
                'qml_file': f'pipes_lengths_{units}.qml.bak',
                'file_name': f'length_{units}',
                'tooltip_prefix': 'Len'
            })

        if self.cbPipesMaterial.isChecked():
            queries.append({
                'layer_name': 'Pipe Materials',
                'field': 'Material',
                'qml_file': 'pipes_materials.qml.bak',
                'file_name': 'material',
                'tooltip_prefix': 'Mat '
            })

        return queries

    def process_query(self, query, main_layer, queries_group):
        layer_name = query['layer_name']
        field = query['field']
        qml_file = query['qml_file']
        tooltip_prefix = query['tooltip_prefix']
        file_name = query['file_name']
        
        self.check_existing_layer(queries_group, layer_name)
        derived_layer = self.create_derived_layer(main_layer, layer_name, field)
    
        self.load_qml_style(derived_layer, qml_file)
        derived_layer.setLabelsEnabled(False)

        if field == 'Material':
            QGISRedUtils().apply_categorized_renderer(derived_layer, field)

        QgsProject.instance().addMapLayer(derived_layer, False) 
        
        self.hide_fields(derived_layer, field)
        
        if queries_group:
            layer_tree_layer = queries_group.insertLayer(0, derived_layer)
            layer_tree_layer.setCustomProperty("showFeatureCount", True)

        main_layer.dataChanged.connect(lambda: self.sync_layers(main_layer, derived_layer))
        main_layer.styleChanged.connect(lambda: self.sync_layers(main_layer, derived_layer))
        derived_layer.dataChanged.connect(lambda: derived_layer.triggerRepaint())
        
        #derived_layer.setReadOnly(True)
        
        return derived_layer

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
            
            QgsProject.instance().removeMapLayer(existing_layer.layerId())
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
            layer.setCustomProperty("styleURI", qml_path)
            layer.loadNamedStyle(qml_path)
            layer.triggerRepaint()

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

    def hide_fields(self, layer, fieldname):
        config = layer.attributeTableConfig()
        columns = config.columns()
        
        fields_to_keep = ['Id', fieldname]
        
        for column in columns:
            column.hidden = column.name not in fields_to_keep
        
        config.setColumns(columns)
        
        layer_cache = QgsVectorLayerCache(layer, layer.featureCount())

        source_model = QgsAttributeTableModel(layer_cache)
        source_model.loadLayer()
        
        attribute_table_view = QgsAttributeTableView()
        attribute_table_filter_model = QgsAttributeTableFilterModel(iface.mapCanvas(), source_model)
        
        layer.setAttributeTableConfig(config)
        attribute_table_filter_model.setAttributeTableConfig(config)
        attribute_table_view.setAttributeTableConfig(config)