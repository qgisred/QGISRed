# -*- coding: utf-8 -*-
import os
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import QDockWidget, QMessageBox, QLineEdit, QListWidgetItem
from qgis.PyQt import uic
from PyQt5.QtCore import Qt, QEvent, pyqtSlot
from qgis.core import QgsProject, QgsGeometry, QgsPointXY, QgsRectangle, QgsVectorLayer, QgsSettings, QgsFeature, QgsLayerMetadata
from qgis.utils import iface
from qgis.gui import QgsHighlight

from ..tools.qgisred_utils import QGISRedUtils

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_findElements_dock.ui"))

class QGISRedFindElementsDock(QDockWidget, FORM_CLASS):
    _instance = None

    # -------------------------------------------------------------------------
    # Singleton & Initialization / Setup
    # -------------------------------------------------------------------------
    @classmethod
    def getInstance(cls, parent=None):
        if cls._instance is None:
            cls._instance = cls(parent)
        return cls._instance

    def __init__(self, parent=None):
        if QGISRedFindElementsDock._instance is not None:
            raise Exception("QGISRedFindElementsDock is a singleton! Use getInstance() instead.")
        super(QGISRedFindElementsDock, self).__init__(parent)
        self.setupUi(self)
        self.listWidget.installEventFilter(self)
        self.setObjectName("QGISRedFindElementsDock")
        self.setFloating(False)
        if parent:
            parent.addDockWidget(Qt.LeftDockWidgetArea, self)

        # Element types, identifiers, and singular forms
        self.element_types = [
            self.tr('Pipes'),
            self.tr('Junctions'),
            self.tr('Multiple Demands'),
            self.tr('Reservoirs'),
            self.tr('Tanks'),
            self.tr('Pumps'),
            self.tr('Valves'),
            self.tr('Sources'),
            self.tr('Service Connections'),
            self.tr('Isolation Valves'),
            self.tr('Meters')
        ]
        self.element_identifiers = {
            'Pipes': 'qgisred_pipes', 
            'Junctions': 'qgisred_junctions',
            'Multiple Demands': 'qgisred_demands',
            'Reservoirs': 'qgisred_reservoirs',
            'Tanks': 'qgisred_tanks',
            'Pumps': 'qgisred_pumps',
            'Valves': 'qgisred_valves',
            'Sources': 'qgisred_sources',
            'Service Connections': 'qgisred_serviceconnections',
            'Isolation Valves': 'qgisred_isolationvalves',
            'Meters': 'qgisred_meters'
        }
        self.singular_forms = {
            self.tr("Pipes"): self.tr("Pipe"),
            self.tr("Junctions"): self.tr("Junction"),
            self.tr("Multiple Demands"): self.tr("Multiple Demand"),
            self.tr("Reservoirs"): self.tr("Reservoir"),
            self.tr("Tanks"): self.tr("Tank"),
            self.tr("Pumps"): self.tr("Pump"),
            self.tr("Valves"): self.tr("Valve"),
            self.tr("Sources"): self.tr("Source"),
            self.tr("Service Connections"): self.tr("Service Connection"),
            self.tr("Isolation Valves"): self.tr("Isolation Valve"),
            self.tr("Meters"): self.tr("Meter")
        }

        # Used for caching element IDs and highlight objects
        self.original_ids = []
        self.adjacent_highlights = []
        self.main_highlight = None
        self.current_selected_highlight = None 

        # Layer groups for adjacency purposes
        self.link_layers = ["qgisred_pipes", "qgisred_pumps", "qgisred_valves"]
        self.node_layers = ["qgisred_reservoirs", "qgisred_tanks", "qgisred_junctions", 
                            "qgisred_sources", "qgisred_demands", "qgisred_meters", "qgisred_isolationvalves"]
        self.special_layers = ["qgisred_serviceconnections"]
        self.sources_and_demands = ["qgisred_sources", "qgisred_demands"]

        self.setDockStyle()
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.labelFoundElement.setFont(font)
        self.labelFoundElement.setWordWrap(True)

        self.setupConnections()
        self.initializeCustomLayerProperties()
        self.initializeElementTypes()
        self.labelFoundElement.setText("")

        settings = QgsSettings()
        if settings.contains("QGISRed/FindElements/geometry"):
            self.restoreGeometry(settings.value("QGISRed/FindElements/geometry"))

    def sizeHint(self):
        return self.minimumSize()

    def setDockStyle(self):
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFindElements.png')
        self.setWindowIcon(QIcon(icon_path))
        search_icon = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFilter.png'))
        self.leElementMask.addAction(search_icon, QLineEdit.LeadingPosition)
        self.cbElementType.setStyleSheet("QComboBox { background-color: white; }")
        self.cbElementId.setStyleSheet("QComboBox { background-color: white; }")

    def initializeCustomLayerProperties(self):
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            return
        for layer_node in inputs_group.findLayers():
            layer_name = layer_node.name()
            for element_type, identifier in self.element_identifiers.items():
                if layer_name == element_type:
                    layer_obj = layer_node.layer()
                    if not layer_obj:
                        continue
                    layer_obj.setCustomProperty("qgisred_identifier", identifier)
                    layer_metadata = QgsLayerMetadata()
                    layer_metadata.setIdentifier(identifier)
                    layer_obj.setMetadata(layer_metadata)

    def initializeElementTypes(self):
        self.cbElementType.clear()
        available_types = self.getAvailableElementTypes()
        self.cbElementType.addItems(available_types)

    def setDefaultValue(self):
        self.clearAll()

        pipes_layer = self.getLayerByIdentifier("qgisred_pipes")
        if not pipes_layer:
            return

        pipes_layer_name = pipes_layer.name()
        self.cbElementType.setCurrentText(pipes_layer_name)
        self.updateElementIds()

    # -------------------------------------------------------------------------
    # Event Filter and Signal Connections
    # -------------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if obj == self.listWidget and (
            event.type() == QEvent.FocusOut or 
            (event.type() == QEvent.KeyPress and event.key() == Qt.Key_Escape)
        ):
            self.listWidget.clearSelection()
            self.listWidget.setCurrentRow(-1)
        return super(QGISRedFindElementsDock, self).eventFilter(obj, event)

    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.updateElementIds)
        self.leElementMask.textChanged.connect(self.filterElementIds)
        self.btFind.clicked.connect(self.onFindButtonClicked)
        self.listWidget.itemClicked.connect(self.onListItemSingleClicked)
        self.listWidget.itemDoubleClicked.connect(self.onListItemDoubleClicked)
        self.btClear.clicked.connect(self.clearAll)
        self.cbElementId.currentIndexChanged.connect(self.onElementIdChanged)

        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)

        root = project.layerTreeRoot()
        inputs_group = root.findGroup("Inputs")
        if inputs_group:
            inputs_group.addedChildren.connect(self.onLayerTreeChanged)
            inputs_group.removedChildren.connect(self.onLayerTreeChanged)
            for layer_node in inputs_group.findLayers():
                self.connectLayerSignals(layer_node)

    # -------------------------------------------------------------------------
    # Public/User-Facing Methods
    # -------------------------------------------------------------------------
    @pyqtSlot(int)
    def onElementIdChanged(self, index):
        self.labelFoundElement.setText("")
        self.listWidget.clear()

    @pyqtSlot()
    def onFindButtonClicked(self):
        if self.listWidget.currentItem():
            self.onListItemDoubleClicked(self.listWidget.currentItem())
        else:
            self.findElement()

    @pyqtSlot()
    def findElement(self):
        self.clearHighlights()
        self.clearAllLayerSelections()
        self.listWidget.clear()

        selected_type = self.cbElementType.currentText()
        selected_id = self.extractNodeId(self.cbElementId.currentText())
        element_identifier = self.element_identifiers.get(selected_type)

        if not selected_id:
            self.labelFoundElement.setText("")
            return

        layer = self.getLayerForElementType(selected_type)
        found_feature = None
        found_feature_layer = None

        if layer:
            if layer.customProperty("qgisred_identifier") in self.sources_and_demands:
                found_feature, found_feature_layer = self.findSourceOrDemandForNodeId(selected_id)
            else:
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == selected_id:
                        found_feature = feature
                        found_feature_layer = layer
                        break

        if not found_feature:
            QMessageBox.information(self, self.tr("Info"), self.tr("Feature not found"))
            return

        self.updateFoundElementLabel(selected_id, found_feature_layer)
        highlight = QgsHighlight(iface.mapCanvas(), found_feature.geometry(), layer)
        highlight.setColor(QColor("red"))
        highlight.setWidth(5)
        highlight.show()
        self.main_highlight = highlight
        self.adjustMapView(found_feature)

        identifier = layer.customProperty("qgisred_identifier")
        if self.isLineElement(layer):
            self.findAdjacentNodesByGeometry(found_feature)
        elif identifier == "qgisred_meters":
            self.findMeterAdjacency(found_feature, layer)
        elif identifier == "qgisred_isolationvalves":
            self.findIsolationValveAdjacency(found_feature, layer)
        elif identifier == "qgisred_serviceconnections":
            self.findServiceConnectionAdjacency(found_feature, layer)
        else:
            self.findAdjacentLinksByGeometry(found_feature, layer)
        self.sortListWidgetItems()

    @pyqtSlot()
    def updateElementIds(self):
        self.cbElementId.clear()
        self.original_ids.clear()
        self.labelFoundElement.setText("")

        layer = self.getLayerForElementType(self.cbElementType.currentText())
        if layer:
            for f in layer.getFeatures():
                id_val = self.getFeatureIdValue(f, layer, True)
                if id_val:
                    self.original_ids.append(id_val)
            self.original_ids = sorted(set(self.original_ids))

        if self.leElementMask.text():
            self.filterElementIds()
        else:
            self.cbElementId.addItems(self.original_ids)

    @pyqtSlot()
    def filterElementIds(self):
        mask = self.leElementMask.text().strip()
        self.cbElementId.clear()
        if mask:
            filtered_items = [self.tr(item) for item in self.original_ids if mask.lower() in item.lower()]
        else:
            filtered_items = self.original_ids
        self.cbElementId.addItems(filtered_items)

    def clearAll(self):
        self.clearHighlights()
        self.clearAllLayerSelections()
        self.leElementMask.clear()
        self.cbElementId.setCurrentIndex(0)
        self.labelFoundElement.setText("")
        self.listWidget.clear()

    def onListItemSingleClicked(self, item):
        if self.current_selected_highlight:
            self.current_selected_highlight.hide()
            self.current_selected_highlight = None

        singular_type, selected_id, _ = self.extractTypeAndId(item.text())
        if not singular_type or not selected_id:
            return

        element_identifier = None
        for plural, singular in self.singular_forms.items():
            if singular == singular_type:
                element_identifier = self.element_identifiers.get(plural)
                break
        if not element_identifier:
            element_identifier = self.getIdentifierFromLayerName(singular_type)

        matching_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == element_identifier
        ]
        for layer in matching_layers:
            for feature in layer.getFeatures():
                if self.getFeatureIdValue(feature, layer) == selected_id:
                    highlight = QgsHighlight(iface.mapCanvas(), feature.geometry(), layer)
                    highlight.setColor(QColor("orange"))
                    highlight.setWidth(5)
                    highlight.show()
                    self.current_selected_highlight = highlight
                    return

    def onListItemDoubleClicked(self, item):
        item_text = item.text()
        self.leElementMask.clear()
        singular_type, selected_id, full_id = self.extractTypeAndId(item_text)
        if not singular_type or not selected_id:
            return
        element_type = None
        for plural, singular in self.singular_forms.items():
            if singular == singular_type:
                element_type = plural
                break
        if not element_type:
            element_type = singular_type
        self.cbElementType.setCurrentText(element_type)
        index = self.cbElementId.findText(full_id)
        if index >= 0:
            self.cbElementId.setCurrentIndex(index)
        self.findElement()

    def closeEvent(self, event):
        root = QgsProject.instance().layerTreeRoot()
        inputs_group = root.findGroup("Inputs")
        if inputs_group:
            try:
                inputs_group.addedChildren.disconnect(self.onLayerTreeChanged)
                inputs_group.removedChildren.disconnect(self.onLayerTreeChanged)
                for layer_node in inputs_group.findLayers():
                    self.disconnectLayerSignals(layer_node.layer())
            except Exception:
                pass
        settings = QgsSettings()
        settings.setValue("QGISRed/FindElements/geometry", self.saveGeometry())
        self.clearHighlights()
        self.clearAllLayerSelections()
        QGISRedFindElementsDock._instance = None
        super(QGISRedFindElementsDock, self).closeEvent(event)

    def onProjectClosed(self):
        self.clearHighlights()
        self.clearAllLayerSelections()

    # -------------------------------------------------------------------------
    # Highlight and Map View Adjustment Methods
    # -------------------------------------------------------------------------
    def clearHighlights(self):
        if self.main_highlight:
            self.main_highlight.hide()
            self.main_highlight = None
        for h in self.adjacent_highlights:
            h.hide()
        self.adjacent_highlights.clear()
        if self.current_selected_highlight:
            self.current_selected_highlight.hide()
            self.current_selected_highlight = None

        canvas = iface.mapCanvas()
        scene = canvas.scene()
        for item in scene.items():
            if isinstance(item, QgsHighlight):
                item.hide()
                scene.removeItem(item)
                del item
        canvas.refresh()

    def clearAllLayerSelections(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def adjustMapView(self, feature):
        canvas = iface.mapCanvas()
        current_extent = canvas.extent()
        geom = feature.geometry()
        feature_extent = geom.boundingBox()
        map_width = current_extent.width()
        map_height = current_extent.height()
        feat_width = feature_extent.width()
        feat_height = feature_extent.height()
        is_point = (feat_width == 0 and feat_height == 0)
        feat_largest_dim = max(feat_width, feat_height)
        map_largest_dim = max(map_width, map_height)
        ratio = feat_largest_dim / map_largest_dim if map_largest_dim != 0 else 1
        center = feature_extent.center()
        if not is_point:
            if ratio > 0.25:
                factor = ratio / 0.25
                new_width = map_width * factor
                new_height = map_height * factor
                new_extent = self.recenterExtent(new_width, new_height, center.x(), center.y())
            elif ratio < 0.05:
                factor = 0.05 / ratio
                new_width = map_width / factor
                new_height = map_height / factor
                new_extent = self.recenterExtent(new_width, new_height, center.x(), center.y())
            else:
                new_extent = QgsRectangle(current_extent)
        else:
            new_extent = QgsRectangle(current_extent)
        new_extent = self.applyMinimalPan(new_extent, feature_extent)
        canvas.setExtent(new_extent)
        canvas.refresh()

    def recenterExtent(self, new_width, new_height, center_x, center_y):
        half_w = new_width / 2.0
        half_h = new_height / 2.0
        return QgsRectangle(center_x - half_w, center_y - half_h, center_x + half_w, center_y + half_h)

    def applyMinimalPan(self, current_extent, feature_extent):
        margin_x = current_extent.width() * 0.1
        margin_y = current_extent.height() * 0.1
        left_dist = feature_extent.xMinimum() - current_extent.xMinimum()
        right_dist = current_extent.xMaximum() - feature_extent.xMaximum()
        top_dist = current_extent.yMaximum() - feature_extent.yMaximum()
        bottom_dist = feature_extent.yMinimum() - current_extent.yMinimum()
        new_extent = QgsRectangle(current_extent)
        if left_dist < margin_x:
            shift = margin_x - left_dist
            new_extent.setXMinimum(new_extent.xMinimum() - shift)
            new_extent.setXMaximum(new_extent.xMaximum() - shift)
        if right_dist < margin_x:
            shift = margin_x - right_dist
            new_extent.setXMinimum(new_extent.xMinimum() + shift)
            new_extent.setXMaximum(new_extent.xMaximum() + shift)
        if top_dist < margin_y:
            shift = margin_y - top_dist
            new_extent.setYMinimum(new_extent.yMinimum() + shift)
            new_extent.setYMaximum(new_extent.yMaximum() + shift)
        if bottom_dist < margin_y:
            shift = margin_y - bottom_dist
            new_extent.setYMinimum(new_extent.yMinimum() - shift)
            new_extent.setYMaximum(new_extent.yMaximum() - shift)
        return new_extent

    # -------------------------------------------------------------------------
    # Helper Methods: Layers, IDs, and Geometry
    # -------------------------------------------------------------------------
    def getAvailableElementTypes(self):
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            return []
        available_types = []
        checked_layers = inputs_group.checkedLayers()
        for element, identifier in self.element_identifiers.items():
            for layer in checked_layers:
                if layer and layer.customProperty("qgisred_identifier") == identifier:
                    available_types.append(layer.name())
                    break
        return available_types

    def getLayerForElementType(self, element_type):
        project = QgsProject.instance()
        layers = project.mapLayersByName(element_type)
        return layers[0] if layers else None

    def getLayerByIdentifier(self, identifier):
        for layer in self.getCheckedInputGroupLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                return layer
        return None

    def getCheckedInputGroupLayers(self):
        inputs_group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputs_group:
            return []
        checked_layers = inputs_group.checkedLayers()
        ordered_layers = sorted(
            checked_layers,
            key=lambda lyr: self.element_types.index(lyr.name()) if lyr.name() in self.element_types else 999
        )
        return ordered_layers

    def getFeatureIdValue(self, feature, layer, special_naming=False):
        if not layer:
            return "Id"
        identifier = layer.customProperty("qgisred_identifier")
        if identifier in self.sources_and_demands:
            node_feature, node_layer = self.findOverlappedNode(feature, layer, supported_only=True)
            if node_feature:
                node_id = self.extractNodeId(node_feature.attribute("Id"))
                if special_naming:
                    singular = self.singular_forms.get(node_layer.name(), node_layer.name())
                    suffix = "(Source)" if identifier == "qgisred_sources" else "(Mult.Dem)"
                    return f"{singular} {node_id} {suffix}"
                return str(node_id)
            return ""
        else:
            value = feature.attribute("Id")
            id_str = str(value) if value is not None else ""
            if special_naming and identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                suffixes = []
                source_layer = self.getLayerByIdentifier("qgisred_sources")
                if source_layer:
                    for src_feat in source_layer.getFeatures():
                        if self.areOverlappedPoints(feature.geometry(), src_feat.geometry()):
                            suffixes.append("(Source)")
                            break
                if identifier == "qgisred_junctions":
                    demand_layer = self.getLayerByIdentifier("qgisred_demands")
                    if demand_layer:
                        for dmnd_feat in demand_layer.getFeatures():
                            if self.areOverlappedPoints(feature.geometry(), dmnd_feat.geometry()):
                                suffixes.append("(Mult.Dem)")
                                break
                if suffixes:
                    id_str += " " + " ".join(suffixes)
            return id_str

    def extractNodeId(self, text):
        text = text.replace(" (Source)", "").replace(" (Mult.Dem)", "")
        parts = text.strip().split()
        return parts[-1] if len(parts) > 1 else text

    def extractTypeAndId(self, text):
        original_text = text.strip()
        text_clean = original_text.replace(" (Source)", "").replace(" (Mult.Dem)", "").strip()
        sorted_singulars = sorted(self.singular_forms.values(), key=len, reverse=True)
        for singular in sorted_singulars:
            if text_clean.startswith(singular + " "):
                selected_id = text_clean[len(singular):].strip()
                full_id = original_text[len(singular):].strip() if original_text.startswith(singular + " ") else selected_id
                return singular, selected_id, full_id
        parts = text_clean.split(" ", 1)
        if len(parts) < 2:
            return None, None, None
        singular = parts[0]
        selected_id = parts[1].strip()
        full_id = original_text[len(singular):].strip() if original_text.startswith(singular + " ") else selected_id
        return singular, selected_id, full_id

    def getIdentifierFromLayerName(self, layer_name):
        layers = QgsProject.instance().mapLayersByName(layer_name)
        if layers:
            return layers[0].customProperty("qgisred_identifier", None)
        return None

    def areOverlappedPoints(self, point1, point2, tolerance=1e-9):
        return point1.distance(point2) < tolerance

    def updateFoundElementLabel(self, selected_id, layer=None):
        if not selected_id:
            self.labelFoundElement.setText("")
            return

        if layer and layer.customProperty("qgisred_identifier") in self.sources_and_demands:
            node_layer, node_feature = self.findNodeLayer(selected_id)
        elif layer:
            node_feature = None
            for feat in layer.getFeatures():
                if self.getFeatureIdValue(feat, layer) == selected_id:
                    node_feature = feat
                    break
            node_layer = layer if node_feature else None
        else:
            node_layer, node_feature = self.findNodeLayer(selected_id)

        if node_layer and node_feature:
            suffixes = []
            node_identifier = node_layer.customProperty("qgisred_identifier", "")
            if node_identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                source_layer = self.getLayerByIdentifier("qgisred_sources")
                if source_layer:
                    for src_feat in source_layer.getFeatures():
                        if (not src_feat.geometry().isEmpty() and
                            self.areOverlappedPoints(node_feature.geometry(), src_feat.geometry())):
                            suffixes.append("(Source)")
                            break
            if node_identifier == "qgisred_junctions":
                demand_layer = self.getLayerByIdentifier("qgisred_demands")
                if demand_layer:
                    for dmnd_feat in demand_layer.getFeatures():
                        if (not dmnd_feat.geometry().isEmpty() and
                            self.areOverlappedPoints(node_feature.geometry(), dmnd_feat.geometry())):
                            suffixes.append("(Mult.Dem)")
                            break
            singular_node_type = self.singular_forms.get(node_layer.name(), node_layer.name())
            suffix_str = " ".join(suffixes)
            self.labelFoundElement.setText(self.tr(f"{singular_node_type} {selected_id} {suffix_str}".strip()))
        else:
            element_type = self.cbElementType.currentText()
            singular_element_type = self.singular_forms.get(element_type, element_type)
            self.labelFoundElement.setText(self.tr(f"{singular_element_type} {selected_id}"))

    def findNodeLayer(self, node_id):
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.node_layers:
                if identifier in self.sources_and_demands:
                    continue
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == node_id:
                        return layer, feature
        return None, None

    def findOverlappedNode(self, point_feature, current_layer, supported_only=False):
        feature_geom = point_feature.geometry()
        if feature_geom.isEmpty():
            return None, None
        feature_point = feature_geom.asPoint()
        feature_point_geom = QgsGeometry.fromPointXY(feature_point)
        tolerance = 1e-6
        if supported_only:
            supported_ids = ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]
            for node_layer in self.getCheckedInputGroupLayers():
                if node_layer == current_layer:
                    continue
                node_identifier = node_layer.customProperty("qgisred_identifier", "")
                if node_identifier not in supported_ids:
                    continue
                for node_feature in node_layer.getFeatures():
                    node_geom = node_feature.geometry()
                    if node_geom.isEmpty():
                        continue
                    node_point_geom = QgsGeometry.fromPointXY(node_geom.asPoint())
                    if self.areOverlappedPoints(feature_point_geom, node_point_geom):
                        return node_feature, node_layer
            return None, None
        else:
            for node_layer in self.getCheckedInputGroupLayers():
                if node_layer == current_layer:
                    continue
                node_identifier = node_layer.customProperty("qgisred_identifier", "")
                if node_identifier in self.node_layers and node_identifier not in self.sources_and_demands:
                    for node_feature in node_layer.getFeatures():
                        node_geom = node_feature.geometry()
                        if node_geom.isEmpty():
                            continue
                        node_point_geom = QgsGeometry.fromPointXY(node_geom.asPoint())
                        if self.areOverlappedPoints(feature_point_geom, node_point_geom):
                            return node_feature, node_layer
            return None, None

    def findSourceOrDemandForNodeId(self, node_id):
        node_layer, node_feat = self.findNodeLayer(node_id)
        if not node_layer or not node_feat:
            return None, None 
        node_geom = node_feat.geometry()
        if node_geom.isEmpty():
            return None, None 
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.sources_and_demands: 
                for feat in layer.getFeatures():
                    feat_geom = feat.geometry()
                    if feat_geom.isEmpty():
                        continue
                    if self.areOverlappedPoints(node_geom, feat_geom):
                        return feat, layer
        return None, None

    def isLineElement(self, layer):
        return layer.customProperty("qgisred_identifier") in self.link_layers
    
    # -------------------------------------------------------------------------
    # Adjacency Methods
    # -------------------------------------------------------------------------
    def addAdjacencyItem(self, item_text, identifier):
        new_item = QListWidgetItem(self.tr(item_text))
        new_item.setData(Qt.UserRole, identifier)
        self.listWidget.addItem(new_item)

    def sortListWidgetItems(self):
        items = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            items.append((item.text(), item.data(Qt.UserRole)))
        self.listWidget.clear()

        def sort_key(entry):
            _, iden = entry
            try:
                return list(self.element_identifiers.values()).index(iden)
            except ValueError:
                return len(self.element_identifiers)
        for text, identifier in sorted(items, key=sort_key):
            new_item = QListWidgetItem(text)
            new_item.setData(Qt.UserRole, identifier)
            self.listWidget.addItem(new_item)

    def addServiceConnectionAdjacencies(self, current_geom, tolerance):
        service_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_serviceconnections"
        ]
        for layer in service_layers:
            for feat in layer.getFeatures():
                service_geom = feat.geometry()
                if service_geom.isEmpty():
                    continue
                if current_geom.intersects(service_geom) or current_geom.distance(service_geom) < tolerance:
                    service_id = self.getFeatureIdValue(feat, layer)
                    singular = self.singular_forms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {service_id}", layer.customProperty("qgisred_identifier"))

    def addIsolationValveAdjacencies(self, current_geom, tolerance):
        isolation_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_isolationvalves"
        ]
        for layer in isolation_layers:
            for feat in layer.getFeatures():
                iso_geom = feat.geometry()
                if iso_geom.isEmpty():
                    continue
                if current_geom.intersects(iso_geom) or current_geom.distance(iso_geom) < tolerance:
                    iso_id = self.getFeatureIdValue(feat, layer)
                    singular = self.singular_forms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {iso_id}", layer.customProperty("qgisred_identifier"))

    def findAdjacentNodesByGeometry(self, line_feature):
        geom = line_feature.geometry()
        if geom.isEmpty():
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            line_points = parts[0] if parts else []
        else:
            line_points = geom.asPolyline()
        if not line_points:
            return
        line_geom = QgsGeometry.fromPolylineXY(line_points)
        tolerance = 1e-6
        found_nodes = []
        node_layers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") in (self.node_layers + self.special_layers)
        ]
        for node_layer in node_layers:
            if node_layer.geometryType() != 0:
                continue
            identifier = node_layer.customProperty("qgisred_identifier", "")
            if identifier in self.sources_and_demands:
                continue
            for f in node_layer.getFeatures():
                node_geom = f.geometry()
                if node_geom.isEmpty():
                    continue
                if line_geom.distance(node_geom) < tolerance:
                    node_id = self.getFeatureIdValue(f, node_layer)
                    layer_name = node_layer.name()
                    singular = self.singular_forms.get(layer_name, layer_name)
                    node_suffixes = []
                    if identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                        source_layer = self.getLayerByIdentifier("qgisred_sources")
                        if source_layer:
                            for src_feat in source_layer.getFeatures():
                                if self.areOverlappedPoints(node_geom, src_feat.geometry()):
                                    node_suffixes.append("(Source)")
                                    break
                        if identifier == "qgisred_junctions":
                            demand_layer = self.getLayerByIdentifier("qgisred_demands")
                            if demand_layer:
                                for dmnd_feat in demand_layer.getFeatures():
                                    if self.areOverlappedPoints(node_geom, dmnd_feat.geometry()):
                                        node_suffixes.append("(Mult.Dem)")
                                        break
                    suffix_str = " " + " ".join(node_suffixes) if node_suffixes else ""
                    node_info = f"{singular} {node_id}{suffix_str}"
                    found_nodes.append((node_layer, f, node_info))
        for node_layer, f, node_info in found_nodes:
            self.addAdjacencyItem(node_info, node_layer.customProperty("qgisred_identifier", ""))
        self.addServiceConnectionAdjacencies(line_geom, tolerance)

    def findAdjacentLinksByGeometry(self, node_feature, layer):
        node_geom = node_feature.geometry()
        if node_geom.isEmpty():
            return
        node_point = QgsPointXY(node_geom.asPoint())
        node_g = QgsGeometry.fromPointXY(node_point)
        tolerance = 1e-9
        found_links = []
        link_layers = [
            lyr for lyr in self.getCheckedInputGroupLayers()
            if lyr.customProperty("qgisred_identifier") in (self.link_layers + ["qgisred_meters"])
        ]
        for link_layer in link_layers:
            ident = link_layer.customProperty("qgisred_identifier", "")
            if ident in self.link_layers:
                if link_layer.geometryType() != 1:
                    continue
                for f in link_layer.getFeatures():
                    link_geom = f.geometry()
                    if link_geom.isMultipart():
                        parts = link_geom.asMultiPolyline()
                        line_points = parts[0] if parts else []
                    else:
                        line_points = link_geom.asPolyline()
                    if not line_points:
                        continue
                    if (node_g.distance(link_geom) < tolerance or
                        self.areOverlappedPoints(node_g, QgsGeometry.fromPointXY(line_points[0])) or
                        self.areOverlappedPoints(node_g, QgsGeometry.fromPointXY(line_points[-1]))):
                        link_id = self.getFeatureIdValue(f, link_layer)
                        layer_name = link_layer.name()
                        singular = self.singular_forms.get(layer_name, layer_name)
                        found_links.append((link_layer, f, f"{singular} {link_id}"))
            elif ident == "qgisred_meters":
                if link_layer.geometryType() != 0:
                    continue
                for f in link_layer.getFeatures():
                    meter_geom = f.geometry()
                    if meter_geom.isEmpty():
                        continue
                    if node_g.distance(meter_geom) < tolerance:
                        meter_id = self.getFeatureIdValue(f, link_layer)
                        layer_name = link_layer.name()
                        singular = self.singular_forms.get(layer_name, layer_name)
                        found_links.append((link_layer, f, f"{singular} {meter_id}"))
        for link_layer, f, link_info in found_links:
            self.addAdjacencyItem(link_info, link_layer.customProperty("qgisred_identifier"))
        self.addServiceConnectionAdjacencies(node_g, tolerance)
        if layer.customProperty("qgisred_identifier") == "qgisred_junctions":
            self.addIsolationValveAdjacencies(node_g, tolerance)

    def findServiceConnectionAdjacency(self, feature, current_layer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            if not parts or not parts[0]:
                return
            line_points = parts[0]
        else:
            line_points = geom.asPolyline()
        if not line_points:
            return
        endpoints = [QgsPointXY(line_points[0]), QgsPointXY(line_points[-1])]
        tolerance = 1e-6
        for pt in endpoints:
            dummy_feature = QgsFeature()
            dummy_feature.setGeometry(QgsGeometry.fromPointXY(pt))
            node_feature, node_layer = self.findOverlappedNode(dummy_feature, current_layer)
            if node_feature and node_layer.customProperty("qgisred_identifier") == "qgisred_junctions":
                junction_item_text = self.getFeatureIdValue(node_feature, node_layer, True)
                singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
                junction_full_name = singular_name + ' ' + junction_item_text
                self.addAdjacencyItem(junction_full_name, node_layer.customProperty("qgisred_identifier"))
                return
        for pt in endpoints:
            pt_geom = QgsGeometry.fromPointXY(pt)
            for lyr in self.getCheckedInputGroupLayers():
                if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                    for f in lyr.getFeatures():
                        pipe_geom = f.geometry()
                        if pipe_geom.isEmpty():
                            continue
                        if pt_geom.distance(pipe_geom) < tolerance:
                            pipe_id = self.getFeatureIdValue(f, lyr)
                            singular = self.singular_forms.get(lyr.name(), lyr.name())
                            full_name = f"{singular} {pipe_id}"
                            self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                            return

    def findIsolationValveAdjacency(self, feature, current_layer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        tolerance = 1e-6
        node_feature, node_layer = self.findOverlappedNode(feature, current_layer)
        if node_feature and node_layer.customProperty("qgisred_identifier") == "qgisred_junctions":
            node_item_text = self.getFeatureIdValue(node_feature, node_layer, True)
            singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
            node_full_name = singular_name + ' ' + node_item_text
            self.addAdjacencyItem(node_full_name, node_layer.customProperty("qgisred_identifier"))
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                for f in lyr.getFeatures():
                    pipe_geom = f.geometry()
                    if pipe_geom.isEmpty():
                        continue
                    if geom.distance(pipe_geom) < tolerance:
                        pipe_id = self.getFeatureIdValue(f, lyr)
                        singular = self.singular_forms.get(lyr.name(), lyr.name())
                        full_name = f"{singular} {pipe_id}"
                        self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                        return

    def findMeterAdjacency(self, feature, current_layer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        tolerance = 1e-6
        node_feature, node_layer = self.findOverlappedNode(feature, current_layer)
        if node_feature:
            node_id = self.getFeatureIdValue(node_feature, node_layer, True)
            singular_name = self.singular_forms.get(node_layer.name(), node_layer.name())
            node_item_text = singular_name + ' ' + node_id
            self.addAdjacencyItem(node_item_text, node_layer.customProperty("qgisred_identifier"))
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") != "qgisred_meters":
                for f in lyr.getFeatures():
                    link_geom = f.geometry()
                    if link_geom.isEmpty():
                        continue
                    if geom.distance(link_geom) < tolerance:
                        adj_id = self.getFeatureIdValue(f, lyr)
                        singular = self.singular_forms.get(lyr.name(), lyr.name())
                        full_name = f"{singular} {adj_id}"
                        self.addAdjacencyItem(full_name, lyr.customProperty("qgisred_identifier"))
                        return

    # -------------------------------------------------------------------------
    # Signal Connection Helpers
    # -------------------------------------------------------------------------
    def connectLayerSignals(self, layer_node):
        try:
            layer_node.nameChanged.connect(self.onLayerTreeChanged)
            if layer_node.layer():
                layer = layer_node.layer()
                layer.dataChanged.connect(self.onLayerTreeChanged)
                layer.featureAdded.connect(self.updateElementIds)
                layer.featureDeleted.connect(self.updateElementIds)
                layer.visibilityChanged.connect(self.onLayerTreeChanged)
        except Exception:
            pass

    def disconnectLayerSignals(self, layer):
        try:
            if hasattr(layer, 'nameChanged'):
                try:
                    layer.nameChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
            if hasattr(layer, 'dataChanged'):
                try:
                    layer.dataChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
            if hasattr(layer, 'visibilityChanged'):
                try:
                    layer.visibilityChanged.disconnect(self.onLayerTreeChanged)
                except Exception:
                    pass
        except Exception:
            pass

    def onLayerTreeChanged(self):
        current_type = self.cbElementType.currentText()
        current_id = self.extractNodeId(self.cbElementId.currentText())
        self.initializeCustomLayerProperties()
        self.initializeElementTypes()
        type_index = self.cbElementType.findText(current_type)
        if type_index >= 0:
            self.cbElementType.setCurrentIndex(type_index)
            id_index = self.cbElementId.findText(current_id)
            if id_index >= 0:
                self.cbElementId.setCurrentIndex(id_index)
    
    def onProjectChanged(self):
        self.clearAll()
        self.onLayerTreeChanged()
