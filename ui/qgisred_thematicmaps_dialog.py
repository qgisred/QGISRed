# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox
from PyQt5.QtGui import QIcon, QColor
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt import uic
import os
import random

from qgis.core import (
    QgsProject,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsVectorLayer,
    QgsCategorizedSymbolRenderer,
    QgsRendererCategory,
    QgsLayerTreeNode,
    QgsUnitTypes,
    QgsSymbol,
    QgsField,
    QgsExpression,
    edit,
    QgsVectorFileWriter
)

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

        for query in queries:
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

    def get_project_units(self):
        units, ok = QgsProject.instance().readEntry("QGISRed", "project_units", "LPS")

        # International Units
        international_units = ["LPS", "LPM", "MLD", "CMH", "CMD"]

        # American Units 
        american_units = ["CFS", "GPM", "MGD", "IMGD", "AFD"]

        print("units: ", units)
        if units in american_units:
            return 'feet'
        elif units in international_units:
            return 'meters'
        else:
            # Default to meters
            return 'meters'

    def get_selected_queries(self):
        units = self.get_project_units()
        queries = []

        if self.cbPipesDiameter.isChecked():
            queries.append({
                'layer_name': 'Pipe Diameters',
                'field': 'Diameter',
                'qml_file': f'pipesDiameter_{units}.qml.bak',
                'file_name': f'diameter_{units}',
                'tooltip_prefix': 'Diam'
            })

        if self.cbPipesLength.isChecked():
            queries.append({
                'layer_name': 'Pipe Lengths',
                'field': 'Length',
                'qml_file': f'pipesLength_{units}.qml.bak',
                'file_name': f'length_{units}',
                'tooltip_prefix': 'Len'
            })

        if self.cbPipesMaterial.isChecked():
            queries.append({
                'layer_name': 'Pipe Materials',
                'field': 'Material',
                'qml_file': 'pipesMaterials.qml.bak',
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

        main_layer_path = main_layer.source()
        main_layer_dir = os.path.dirname(main_layer_path)
        main_layer_dir = os.path.normpath(main_layer_dir)
        main_layer_basename = os.path.splitext(os.path.basename(main_layer_path))[0]

        new_layer_filename = f"{main_layer_basename}_query_{file_name}.shp"
        new_layer_path = os.path.join(main_layer_dir, new_layer_filename)
        new_layer_path = os.path.normpath(new_layer_path)
        
        # Remove existing layer if present
        existing_layer = None
        for child in queries_group.children():
            if isinstance(child, QgsLayerTreeLayer) and child.name() == layer_name:
                existing_layer = child
                break

        if existing_layer is not None:
            if os.path.exists(new_layer_path):
                QgsVectorFileWriter.deleteShapeFile(new_layer_path)

        fields = main_layer.fields()
        crs = main_layer.crs()
        geometry_type = main_layer.wkbType()

        writer = QgsVectorFileWriter(
            new_layer_path,
            'UTF-8',
            fields,
            geometry_type,
            crs,
            'ESRI Shapefile'
        )

        if writer.hasError() != QgsVectorFileWriter.NoError:
            return

        features = main_layer.getFeatures()
        for feature in features:
            writer.addFeature(feature)

        del writer

        new_layer = QgsVectorLayer(new_layer_path, layer_name, 'ogr')
        if not new_layer.isValid():
            return

        project = QgsProject.instance()
        project.addMapLayer(new_layer, False)

        if field == 'Material':
            self.apply_categorized_renderer(new_layer, field)
        else:
            self.load_qml_style(new_layer, qml_file)

        # Add the virtual field 'Year'
        # instal_date_index = new_layer.fields().indexFromName('InstalDate')
        # if instal_date_index != -1:
        #     with edit(new_layer):
        #         expression = QgsExpression('substr("InstalDate", 1, 4)')
        #         new_layer.addExpressionField(expression.expression(), QgsField('Year', QVariant.String))

        layer_tree_layer = queries_group.addLayer(new_layer)

        self.assign_labels(new_layer, field)

        html_map_tip = f'<html><body><p>{tooltip_prefix} [% "{field}" %] </p></body></html>'
        new_layer.setMapTipTemplate(html_map_tip)

        layer_tree_layer.setCustomProperty("showFeatureCount", True)

    def apply_categorized_renderer(self, layer, field):
        material_field_index = layer.fields().indexFromName(field)
        if material_field_index == -1:
            QMessageBox.critical(self, 'Error', f'{field} field not found in Pipes layer.')
            return

        unique_values = layer.uniqueValues(material_field_index)
        categories = []

        for value in unique_values:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            random_color = QColor.fromRgb(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            symbol.setColor(random_color)
            symbol.setWidth(0.6)
            category = QgsRendererCategory(value, symbol, str(value))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        layer.setRenderer(renderer)

    def load_qml_style(self, layer, qml_file):
        qml_path = os.path.join(os.path.dirname(__file__), '..', 'layerStyles', qml_file)
        if os.path.exists(qml_path):
            layer.loadNamedStyle(qml_path)
            layer.triggerRepaint()

    def assign_labels(self, layer, field):
        layer.setLabelsEnabled(True)
        labeling = layer.labeling()
        if labeling is not None:
            label_settings = labeling.clone()
            label_settings.fieldName = field
            layer.setLabeling(label_settings)
