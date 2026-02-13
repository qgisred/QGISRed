# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDialog, QWidget, QMessageBox
from PyQt5.QtGui import QIcon
from qgis.PyQt import uic
import os

from qgis.core import (
    QgsProject,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
    QgsVectorLayer,
    QgsGraduatedSymbolRenderer,
    QgsCategorizedSymbolRenderer,
    QgsMessageLog,
    Qgis,
    QgsExpression
)
from qgis.utils import iface

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
        # Some design aspects of the dialog in Python can only be done via code
        # Set dialog icon
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconThematicMaps.png')
        self.setWindowIcon(QIcon(icon_path))

        # Set group boxes' titles to bold
        self.gbPipes.setStyleSheet("font-weight: bold;")
        self.gbJunctions.setStyleSheet("font-weight: bold;")
        self.gbValves.setStyleSheet("font-weight: bold;")
        self.gbPumps.setStyleSheet("font-weight: bold;")
        self.gbTanks.setStyleSheet("font-weight: bold;")
        self.gbReservoirs.setStyleSheet("font-weight: bold;")

        # Set widgets inside the group boxes to normal weight
        for widget in self.gbPipes.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbJunctions.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbValves.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbPumps.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbTanks.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")
        for widget in self.gbReservoirs.findChildren(QWidget):
            widget.setStyleSheet("font-weight: normal;")

    def accept(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()

        if isinstance(root, QgsLayerTreeGroup):
            root_group = root
        else:
            root_group = root.rootGroup()

        inputs_group = root_group.findGroup('Inputs')
        if inputs_group is None:
            QMessageBox.critical(self, 'Error', 'Inputs group not found.')
            return

        inputs_parent = inputs_group.parent()
        if inputs_parent is None:
            inputs_parent = root_group

        queries_group = root_group.findGroup('Queries')
        if queries_group is None:
            inputs_group_index = inputs_parent.children().index(inputs_group)
            queries_group = inputs_parent.insertGroup(inputs_group_index, 'Queries')
        else:
            if queries_group.parent() != inputs_parent:
                old_parent = queries_group.parent()
                old_parent.removeChildNode(queries_group)
                inputs_parent.insertChildNode(0, queries_group)

        pipes_layer = None
        for child in inputs_group.children():
            if isinstance(child, QgsLayerTreeLayer) and child.name() == 'Pipes':
                pipes_layer = child.layer()
                break

        if pipes_layer is None:
            QMessageBox.critical(self, 'Error', 'Pipes layer not found in Inputs group.')
            return

        #Pipes queries
        queries = []

        if self.cbPipesDiameter.isChecked():
            queries.append({
                'layer_name': 'Pipe Diameters',
                'field': 'Diameter',
                'qml_file': 'test2.qml.bak',
                'tooltip_prefix': 'Diam'
            })

        if self.cbPipesLength.isChecked():
            queries.append({
                'layer_name': 'Pipe Lengths',
                'field': 'Length',
                'qml_file': 'pipes.qml.bak',
                'tooltip_prefix': 'Long'
            })

        if self.cbPipesMaterial.isChecked():
            queries.append({
                'layer_name': 'Pipe Materials',
                'field': 'Material',
                'qml_file': 'pipes.qml.bak',
                'tooltip_prefix': 'Mat '
            })

        for query in queries:
            layer_name = query['layer_name']
            field = query['field']
            qml_file = query['qml_file']
            tooltip_prefix = query['tooltip_prefix']

            existing_layer = None
            for child in queries_group.children():
                if isinstance(child, QgsLayerTreeLayer) and child.name() == layer_name:
                    existing_layer = child
                    break

            if existing_layer is not None:
                queries_group.removeChildNode(existing_layer)

            new_layer = QgsVectorLayer(pipes_layer.source(), layer_name, pipes_layer.providerType())

            project.addMapLayer(new_layer, False)
            queries_group.addLayer(new_layer)

            qml_path = os.path.join(os.path.dirname(__file__), '..', 'layerStyles', qml_file)
            if os.path.exists(qml_path):
                new_layer.loadNamedStyle(qml_path)
                new_layer.triggerRepaint()

            # Assign labels
            new_layer.setLabelsEnabled(False)
            labeling = new_layer.labeling()
            if labeling is not None:
                label_settings = labeling.clone()
                label_settings.fieldName = field
                new_layer.setLabeling(label_settings)

            # Assign map tooltips
            html_map_tip = f'<html><body><p>{tooltip_prefix} [% "{field}" %]</p></body></html>'
            new_layer.setMapTipTemplate(html_map_tip)

        # Close
        super(QGISRedThematicMapsDialog, self).accept()
