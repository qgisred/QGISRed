# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QEvent, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtWidgets import QDockWidget, QWidget, QMessageBox, QLineEdit, QListWidgetItem, QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsVectorLayer, QgsSettings, QgsGeometry, QgsPointXY, QgsRectangle, QgsFeature, QgsLayerMetadata, QgsSpatialIndex
from qgis.utils import iface
from qgis.gui import QgsHighlight

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_element_explorer_dock.ui"))

class QGISRedElementExplorerDock(QDockWidget, FORM_CLASS):
    _instance = None
    dockVisibilityChanged = pyqtSignal(bool)
    findElementsDockVisibilityChanged = pyqtSignal(bool)
    elementPropertiesDockVisibilityChanged = pyqtSignal(bool)
    dockFocusChanged = pyqtSignal(bool)
    dockClosed = pyqtSignal(bool)

    # ------------------------------
    # Initialization and Setup Methods
    # ------------------------------
    @classmethod
    def getInstance(cls, canvas, parent=None, showFindElements=True, showElementProperties=True):
        if cls._instance is None or not cls._instance.isVisible():
            if cls._instance is not None:
                try:
                    cls._instance.deleteLater()
                except RuntimeError:
                    pass
            cls._instance = cls(canvas, parent, showFindElements, showElementProperties)
        return cls._instance

    def __init__(self, canvas, parent=None, showFindElements=True, showElementProperties=True):
        if self._instance is not None:
            raise Exception(f"{self.__class__.__name__} is a singleton! Use getInstance() instead.")
        super(self.__class__, self).__init__(parent)
        self.setupUi(self)
        self.setupEventFilters() 
        self.setObjectName(self.__class__.__name__)
        self.setFloating(False)
        iface.addDockWidget(Qt.RightDockWidgetArea, self)

        self.canvas = canvas
        self.findElementsVisible = showFindElements
        self.elementPropertiesVisible = showElementProperties

        self.elementTypes = [
            self.tr('Pipes'),
            self.tr('Junctions'),
            self.tr('Demands'),
            self.tr('Reservoirs'),
            self.tr('Tanks'),
            self.tr('Pumps'),
            self.tr('Valves'),
            self.tr('Sources'),
            self.tr('Service Connections'),
            self.tr('Isolation Valves'),
            self.tr('Meters')
        ]
        
        self.elementIdentifiers = {
            'Pipes': 'qgisred_pipes', 
            'Junctions': 'qgisred_junctions',
            'Demands': 'qgisred_demands',
            'Reservoirs': 'qgisred_reservoirs',
            'Tanks': 'qgisred_tanks',
            'Pumps': 'qgisred_pumps',
            'Valves': 'qgisred_valves',
            'Sources': 'qgisred_sources',
            'Service Connections': 'qgisred_serviceconnections',
            'Isolation Valves': 'qgisred_isolationvalves',
            'Meters': 'qgisred_meters'
        }
        
        self.singularForms = {
            self.tr("Pipes"): self.tr("Pipe"),
            self.tr("Junctions"): self.tr("Junction"),
            self.tr("Demands"): self.tr("Demand"),
            self.tr("Reservoirs"): self.tr("Reservoir"),
            self.tr("Tanks"): self.tr("Tank"),
            self.tr("Pumps"): self.tr("Pump"),
            self.tr("Valves"): self.tr("Valve"),
            self.tr("Sources"): self.tr("Source"),
            self.tr("Service Connections"): self.tr("Service Connection"),
            self.tr("Isolation Valves"): self.tr("Isolation Valve"),
            self.tr("Meters"): self.tr("Meter")
        }
        
        self.originalIds = []
        self.adjacentHighlights = []
        self.mainHighlight = None
        self.currentSelectedHighlight = None
        self.dictOfElementIds = {}
        self.currentLayer = None
        self.currentFeature = None

        # Add spatial index cache for node layers
        self.nodeLayerSpatialIndices = {}  # {layer_id: (QgsSpatialIndex, layer)}
        self.sourcesDemandToNodeCache = {}  # {(layer_identifier, feature_id): (node_id, node_layer_name)}

        self.spoilerElementProperties = None 
        self.spoilerFindElements = None

        self.linkLayers = ["qgisred_pipes", "qgisred_pumps", "qgisred_valves"]
        self.nodeLayers = ["qgisred_reservoirs", "qgisred_tanks", "qgisred_junctions", 
                           "qgisred_sources", "qgisred_demands", "qgisred_meters", "qgisred_isolationvalves"]
        self.specialLayers = ["qgisred_serviceconnections"]
        self.sourcesAndDemands = ["qgisred_sources", "qgisred_demands"]

        if hasattr(self, 'listWidget'):
            self.listWidget.installEventFilter(self)
        
        if hasattr(self, 'labelFoundElement'):
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            self.labelFoundElement.setFont(font)
            self.labelFoundElement.setWordWrap(True)
            self.labelFoundElement.setText("")

        if hasattr(self, 'labelFoundElementTag'):
            self.labelFoundElementTag.setWordWrap(True)
            self.labelFoundElementTag.setText("")
            self.labelFoundElementTag.hide()
            self.isTagVisible = False

        if hasattr(self, 'labelFoundElementDescription'):
            self.labelFoundElementDescription.setWordWrap(True)
            self.labelFoundElementDescription.setText("")
            self.labelFoundElementDescription.hide()
            self.isDescVisible = False

        self.setDockStyle()
        self.setupConnections()
        
        if hasattr(self, 'initializeCustomLayerProperties'):
            self.initializeCustomLayerProperties()
        
        if hasattr(self, 'initializeElementTypes'):
            self.initializeElementTypes()

        self.mElementPropertiesGroupBox.setCollapsed(True)
        self.mFindElementsGroupBox.setCollapsed(True)
        self.trackCollapsibleWidgetsEvents()
        
        self.topLevelChanged.connect(self.onTopLevelChanged)

    def trackCollapsibleWidgetsEvents(self):
        self.mElementPropertiesGroupBox.collapsedStateChanged.connect(self.onElementPropertiesToggled)
        self.mFindElementsGroupBox.collapsedStateChanged.connect(self.onFindElementsToggled)

    def updateCollapsibleWidgetsState(self, collapseElementProperties=None, collapseFindElements=None):
        self.mElementPropertiesGroupBox.blockSignals(True)
        self.mFindElementsGroupBox.blockSignals(True)

        if collapseElementProperties is not None:
            self.mElementPropertiesGroupBox.setCollapsed(collapseElementProperties)

        if collapseFindElements is not None:
            self.mFindElementsGroupBox.setCollapsed(collapseFindElements)

        ep_collapsed = self.mElementPropertiesGroupBox.isCollapsed()
        fe_collapsed = self.mFindElementsGroupBox.isCollapsed()

        if ep_collapsed and fe_collapsed:
            self.close()
            return
        
        if not fe_collapsed and ep_collapsed:
            self.moveWidgetsToFindElements()
        else:
            self.moveWidgetsToElementProperties()

        self.mElementPropertiesGroupBox.blockSignals(False)
        self.mFindElementsGroupBox.blockSignals(False)

    def onTopLevelChanged(self, floating):
        if floating:
            QTimer.singleShot(50, self.resizeToMinimumHeight)

    # ------------------------------
    # Collapsible Widgets Handlers
    # ------------------------------
    def onElementPropertiesToggled(self, collapsed):
        if collapsed:
            self.moveWidgetsToFindElements()
        else:
            self.moveWidgetsToElementProperties()
            
    def onFindElementsToggled(self, collapsed):
        if collapsed:
            self.moveWidgetsToElementProperties()
        else:
            if self.mElementPropertiesGroupBox.isCollapsed():
                self.moveWidgetsToFindElements()

    def moveWidgetsToElementProperties(self):
        widgets = [self.labelFoundElement, self.labelFoundElementTag, self.labelFoundElementDescription, self.mConnectedElementsGroupBox]

        for widget in widgets:
            currentParent = widget.parent()
            if currentParent and currentParent.layout():
                currentParent.layout().removeWidget(widget)

        targetLayout = self.elementPropertiesLayout
        line = self.lineEp
        index = targetLayout.indexOf(line)

        for i, widget in enumerate(widgets):
            targetLayout.insertWidget(index + 1 + i, widget)
            widget.show()

        self.labelFoundElementTag.setVisible(self.isTagVisible)
        self.labelFoundElementDescription.setVisible(self.isDescVisible)

        if self.isFloating():
            QTimer.singleShot(50, self.resetScrollPosition)

    def moveWidgetsToFindElements(self):
        widgets = [self.labelFoundElement, self.labelFoundElementTag, self.labelFoundElementDescription, self.mConnectedElementsGroupBox]

        for widget in widgets:
            currentParent = widget.parent()
            if currentParent and currentParent.layout():
                currentParent.layout().removeWidget(widget)

        targetLayout = self.findElementsLayout
        line = self.line
        index = targetLayout.indexOf(line)

        for i, widget in enumerate(widgets):
            targetLayout.insertWidget(index + 1 + i, widget)
            widget.show()

        self.labelFoundElementTag.setVisible(self.isTagVisible)
        self.labelFoundElementDescription.setVisible(self.isDescVisible)

        if self.isFloating():
            QTimer.singleShot(50, self.resetScrollPosition)

    def resetScrollPosition(self):
        # Reset the scroll area position to the top
        if hasattr(self, 'scrollArea'):
            self.scrollArea.ensureVisible(0, 0, 0, 0)

    # ------------------------------
    # Event Filter Setup
    # ------------------------------
    def setupEventFilters(self):
        mainWidget = self.widget()
        self.installEventFilterRecursive(mainWidget)

    def installEventFilterRecursive(self, widget):
        if widget:
            widget.installEventFilter(self)
            for child in widget.children():
                if isinstance(child, QWidget):
                    self.installEventFilterRecursive(child)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.FocusIn:
            if obj != self and self.isAncestorOf(obj):
                self.reestablishIdentifyTool()
        return super(QGISRedElementExplorerDock, self).eventFilter(obj, event)

    def reestablishIdentifyTool(self):
        from ..tools.qgisred_identifyFeature import QGISRedIdentifyFeature
        currentTool = self.canvas.mapTool()
        if not isinstance(currentTool, QGISRedIdentifyFeature):
            self.dockFocusChanged.emit(True)

    # ------------------------------
    # UI and Dock Styling Methods
    # ------------------------------
    def resizeToMinimumHeight(self):
        self.layout().activate()
        self.adjustSize()

    def setDockStyle(self):
        iconName = 'iconFindElements.png' if 'Find' in self.__class__.__name__ else 'iconElementProperties.png'
        iconPath = os.path.join(os.path.dirname(__file__), '..', 'images', iconName)
        self.setWindowIcon(QIcon(iconPath))
        
        if hasattr(self, 'leElementMask'):
            searchIcon = QIcon(os.path.join(os.path.dirname(__file__), '..', 'images', 'iconFilter.png'))
            self.leElementMask.addAction(searchIcon, QLineEdit.LeadingPosition)
        
        if hasattr(self, 'cbElementType'):
            self.cbElementType.setStyleSheet("QComboBox { background-color: white; }")
        if hasattr(self, 'cbElementId'):
            self.cbElementId.setStyleSheet("QComboBox { background-color: white; }")

        self.tempHideOtherTabs()

    def tempHideOtherTabs(self):
        self.tabWidget.setTabVisible(1, False)
        self.tabWidget.setTabVisible(2, False)
        self.tabWidget.setTabVisible(3, False)
        self.tabWidget.setTabVisible(4, False)

    def setComponentVisibility(self, showFindElements, showElementProperties):
        self.findElementsVisible = showFindElements
        self.elementPropertiesVisible = showElementProperties
        
        self.findElementsDockVisibilityChanged.emit(showFindElements)
        self.elementPropertiesDockVisibilityChanged.emit(showElementProperties)
        
        if not showFindElements and not showElementProperties and not self.isFloating():
            self.close()

    def openIdentifyForFindDock(self):
        from ..tools.qgisred_identifyFeature import QGISRedIdentifyFeature
        self.identifyTool = QGISRedIdentifyFeature(self.canvas, useFindDock=True)
        self.canvas.setMapTool(self.identifyTool)

    @pyqtSlot()
    def toggleFloating(self):
        self.setFloating(not self.isFloating())

    def onDockVisibilityChanged(self, visible):
        if self.isFloating():
            return
        
        findDockVisible = self.frameFindElements.isVisible() 
        elementPropertiesVisible = self.frameElementProperties.isVisible()

        if not findDockVisible and not elementPropertiesVisible:
            self.close()
            return
        
        self.setComponentVisibility(findDockVisible, elementPropertiesVisible)
        self.findElementsDockVisibilityChanged.emit(findDockVisible)
        self.elementPropertiesDockVisibilityChanged.emit(elementPropertiesVisible)
        self.resizeToMinimumHeight()

    # ------------------------------
    # Connection Setup Methods
    # ------------------------------
    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.updateElementIds)
        self.leElementMask.textChanged.connect(self.filterElementIds)
        self.btFind.clicked.connect(self.onFindButtonClicked)
        self.listWidget.itemClicked.connect(self.onListItemSingleClicked)
        self.listWidget.itemDoubleClicked.connect(self.onListItemDoubleClicked)
        self.btClear.clicked.connect(self.clearAll)
        self.cbElementId.currentIndexChanged.connect(self.onElementIdChanged)           
        self.btReload.clicked.connect(self.initializeElementTypes)

        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)

        root = project.layerTreeRoot()
        inputsGroup = root.findGroup("Inputs")
        if inputsGroup:
            inputsGroup.addedChildren.connect(self.onLayerTreeChanged)
            inputsGroup.removedChildren.connect(self.onLayerTreeChanged)
            for layerNode in inputsGroup.findLayers():
                self.connectLayerSignals(layerNode)

    def connectLayerSignals(self, layerNode):
        try:
            layerNode.nameChanged.connect(self.onLayerTreeChanged)
            if layerNode.layer():
                layer = layerNode.layer()
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

    # ------------------------------
    # Clear and Reset Methods
    # ------------------------------
    def clearAll(self):
        self.clearHighlights()
        self.clearAllLayerSelections()

        # Clear all caches
        self.nodeLayerSpatialIndices.clear()
        self.sourcesDemandToNodeCache.clear()
        if hasattr(self, 'sourceDemandIdCache'):
            self.sourceDemandIdCache.clear()

        if hasattr(self, 'leElementMask'):
            self.leElementMask.clear()
        if hasattr(self, 'cbElementId') and self.cbElementId.count() > 0:
            self.cbElementId.setCurrentIndex(0)
        if hasattr(self, 'labelFoundElement'):
            self.labelFoundElement.setText("")
        if hasattr(self, 'labelFoundElementTag'):
            self.labelFoundElementTag.setText("")
        if hasattr(self, 'labelFoundElementDescription'):
            self.labelFoundElementDescription.setText("")
        if hasattr(self, 'listWidget'):
            self.listWidget.clear()
        if hasattr(self, 'dataTableWidget'):
            self.dataTableWidget.clear()
            self.setDataTableWidgetColumns()

    def clearAllLayerSelections(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def clearHighlights(self):
        if self.mainHighlight:
            self.mainHighlight.hide()
            self.mainHighlight = None
        for h in self.adjacentHighlights:
            h.hide()
        self.adjacentHighlights.clear()
        if self.currentSelectedHighlight:
            self.currentSelectedHighlight.hide()
            self.currentSelectedHighlight = None

        canvas = iface.mapCanvas()
        scene = canvas.scene()
        for item in scene.items():
            if isinstance(item, QgsHighlight):
                item.hide()
                scene.removeItem(item)
                del item
        canvas.refresh()

    def closeEvent(self, event):
        try:
            self.dockVisibilityChanged.emit(False)
            self.dockClosed.emit(True)
            
            settings = QgsSettings()
            settings.setValue("QGISRed/ElementsExplorer/geometry", self.saveGeometry())
            settings.setValue("QGISRed/ElementsExplorer/floating", self.isFloating())

            # ----- Disconnect all signals -----
            # Project signals
            project = QgsProject.instance()
            self.safeDisconnect(project.layersAdded, self.onLayerTreeChanged)
            self.safeDisconnect(project.layersRemoved, self.onLayerTreeChanged)
            self.safeDisconnect(project.readProject, self.onProjectChanged)
            self.safeDisconnect(project.cleared, self.onProjectChanged)
            
            # Layer tree signals
            root = project.layerTreeRoot()
            inputsGroup = root.findGroup("Inputs")
            if inputsGroup:
                self.safeDisconnect(inputsGroup.addedChildren, self.onLayerTreeChanged)
                self.safeDisconnect(inputsGroup.removedChildren, self.onLayerTreeChanged)
                for layerNode in inputsGroup.findLayers():
                    self.disconnectLayerSignals(layerNode.layer())
            
            self.safeDisconnect(self.cbElementType.currentIndexChanged, self.updateElementIds)
            self.safeDisconnect(self.leElementMask.textChanged, self.filterElementIds)
            self.safeDisconnect(self.btFind.clicked, self.onFindButtonClicked)
            self.safeDisconnect(self.listWidget.itemClicked, self.onListItemSingleClicked)
            self.safeDisconnect(self.listWidget.itemDoubleClicked, self.onListItemDoubleClicked)
            self.safeDisconnect(self.btClear.clicked, self.clearAll)
            self.safeDisconnect(self.cbElementId.currentIndexChanged, self.onElementIdChanged)
            self.safeDisconnect(self.btReload.clicked, self.initializeElementTypes)
            
            self.safeDisconnect(self.mElementPropertiesGroupBox.collapsedStateChanged, self.onElementPropertiesToggled)
            self.safeDisconnect(self.mFindElementsGroupBox.collapsedStateChanged, self.onFindElementsToggled)
            
            self.removeEventFiltersRecursive(self.widget())
            self.clearHighlights()
            self.clearAllLayerSelections()
            
            self.canvas = None
            self.identifyTool = None
            self.currentLayer = None
            self.currentFeature = None
            self.mainHighlight = None
            self.adjacentHighlights = []
            self.currentSelectedHighlight = None
            self.dictOfElementIds = {}

            self.__class__._instance = None
            super(QDockWidget, self).closeEvent(event)
            self.deleteLater()
        except Exception as e:
            self.__class__._instance = None
            super(QDockWidget, self).closeEvent(event)

    def safeDisconnect(self, signal, slot):
        try:
            signal.disconnect(slot)
        except (TypeError, RuntimeError):
            pass

    def removeEventFiltersRecursive(self, widget):
        if widget:
            widget.removeEventFilter(self)
            for child in widget.children():
                if isinstance(child, QWidget):
                    self.removeEventFiltersRecursive(child)

    # ------------------------------
    # Layer and Project Event Methods
    # ------------------------------
    def onLayerTreeChanged(self):
        # Clear caches when layer tree changes
        self.nodeLayerSpatialIndices.clear()
        self.sourcesDemandToNodeCache.clear()
        if hasattr(self, 'sourceDemandIdCache'):
            self.sourceDemandIdCache.clear()

        currentType = self.cbElementType.currentText()
        currentId = self.extractNodeId(self.cbElementId.currentText())
        self.initializeCustomLayerProperties()
        self.initializeElementTypes()
        typeIndex = self.cbElementType.findText(currentType)
        if typeIndex >= 0:
            self.cbElementType.setCurrentIndex(typeIndex)
            idIndex = self.cbElementId.findText(currentId)
            if idIndex >= 0:
                self.cbElementId.setCurrentIndex(idIndex)

    def onProjectClosed(self):
        self.clearHighlights()
        self.clearAllLayerSelections()
    
    def onProjectChanged(self):
        # Clear caches when project changes
        self.nodeLayerSpatialIndices.clear()
        self.sourcesDemandToNodeCache.clear()
        if hasattr(self, 'sourceDemandIdCache'):
            self.sourceDemandIdCache.clear()

        self.clearAll()
        self.onLayerTreeChanged()

    # ------------------------------
    # Element Type and Identifier Initialization
    # ------------------------------
    def initializeCustomLayerProperties(self):
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputsGroup:
            return
        for layerNode in inputsGroup.findLayers():
            layerName = layerNode.name()
            for elementType, identifier in self.elementIdentifiers.items():
                if layerName == elementType:
                    layerObj = layerNode.layer()
                    if not layerObj:
                        continue
                    layerObj.setCustomProperty("qgisred_identifier", identifier)
                    layerMetadata = QgsLayerMetadata()
                    layerMetadata.setIdentifier(identifier)
                    layerObj.setMetadata(layerMetadata)

    def initializeElementTypes(self):
        self.cbElementType.clear()
        availableTypes = self.getAvailableElementTypes()
        self.cbElementType.addItems(availableTypes)
        self.initializeElementIdsCache()

    def initializeElementIdsCache(self):
        """Initialize element IDs cache with optimized batch processing"""
        # Build all spatial indices and caches upfront
        self.buildNodeLayerSpatialIndices()
        self.buildSourceDemandCacheBatch()

        availableTypes = self.getAvailableElementTypes()
        for elementType in availableTypes:
            layer = self.getLayerForElementType(elementType)
            if layer:
                identifier = layer.customProperty("qgisred_identifier")

                if identifier in self.sourcesAndDemands:
                    # Use pre-built cache for sources/demands
                    ids = self.getCachedSourceDemandIds(identifier)
                else:
                    # Regular features - extract IDs directly without special naming
                    ids = self.extractLayerIdsDirect(layer, identifier)

                self.dictOfElementIds[elementType] = sorted(set(ids))
            else:
                self.dictOfElementIds[elementType] = []

    def buildSourceDemandCacheBatch(self):
        """Pre-compute all source/demand to node relationships in batch"""
        self.sourcesDemandToNodeCache.clear()
        self.sourceDemandIdCache = {'qgisred_sources': [], 'qgisred_demands': []}

        # Get source and demand layers
        sourceLayer = self.getLayerByIdentifier("qgisred_sources")
        demandLayer = self.getLayerByIdentifier("qgisred_demands")

        # Process sources
        if sourceLayer:
            for feature in sourceLayer.getFeatures():
                cacheKey = ('qgisred_sources', feature.id())
                nodeFeature, nodeLayer = self.findOverlappingNodeOptimized(feature.geometry())

                if nodeFeature and nodeLayer:
                    nodeId = self.extractNodeId(nodeFeature.attribute("Id"))
                    nodeLayerName = nodeLayer.name()
                    self.sourcesDemandToNodeCache[cacheKey] = (nodeId, nodeLayerName)

                    # Build display string for cache
                    singular = self.singularForms.get(nodeLayerName, nodeLayerName)
                    displayId = f"{singular} {nodeId} (Source)"
                    self.sourceDemandIdCache['qgisred_sources'].append(displayId)
                else:
                    self.sourcesDemandToNodeCache[cacheKey] = (None, None)

        # Process demands
        if demandLayer:
            for feature in demandLayer.getFeatures():
                cacheKey = ('qgisred_demands', feature.id())
                nodeFeature, nodeLayer = self.findOverlappingNodeOptimized(feature.geometry())

                if nodeFeature and nodeLayer:
                    nodeId = self.extractNodeId(nodeFeature.attribute("Id"))
                    nodeLayerName = nodeLayer.name()
                    self.sourcesDemandToNodeCache[cacheKey] = (nodeId, nodeLayerName)

                    # Build display string for cache
                    singular = self.singularForms.get(nodeLayerName, nodeLayerName)
                    displayId = f"{singular} {nodeId} (Mult.Dem)"
                    self.sourceDemandIdCache['qgisred_demands'].append(displayId)
                else:
                    self.sourcesDemandToNodeCache[cacheKey] = (None, None)

    def getCachedSourceDemandIds(self, identifier):
        """Get cached IDs for sources/demands without recomputing"""
        return self.sourceDemandIdCache.get(identifier, [])

    def extractLayerIdsDirect(self, layer, identifier):
        """Extract IDs directly from layer without special naming logic"""
        ids = []

        # For node layers that might have source/demand suffixes
        if identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
            # Pre-build sets of geometries for fast lookup
            sourceGeoms = set()
            demandGeoms = set()

            sourceLayer = self.getLayerByIdentifier("qgisred_sources")
            if sourceLayer:
                for srcFeat in sourceLayer.getFeatures():
                    if not srcFeat.geometry().isEmpty():
                        sourceGeoms.add(srcFeat.geometry().asWkt())

            if identifier == "qgisred_junctions":
                demandLayer = self.getLayerByIdentifier("qgisred_demands")
                if demandLayer:
                    for dmndFeat in demandLayer.getFeatures():
                        if not dmndFeat.geometry().isEmpty():
                            demandGeoms.add(dmndFeat.geometry().asWkt())

            # Process features with pre-built geometry sets
            for feature in layer.getFeatures():
                value = feature.attribute("Id")
                idStr = str(value) if value is not None else ""

                if not feature.geometry().isEmpty():
                    featWkt = feature.geometry().asWkt()
                    suffixes = []

                    if featWkt in sourceGeoms:
                        suffixes.append("(Source)")
                    if featWkt in demandGeoms:
                        suffixes.append("(Mult.Dem)")

                    if suffixes:
                        idStr += " " + " ".join(suffixes)

                ids.append(idStr)
        else:
            # Simple ID extraction for other layers
            for feature in layer.getFeatures():
                value = feature.attribute("Id")
                if value is not None:
                    ids.append(str(value))

        return ids

    def setDefaultValue(self):
        self.clearAll()

        pipesLayer = self.getLayerByIdentifier("qgisred_pipes")
        if not pipesLayer:
            return

        pipesLayerName = pipesLayer.name()
        self.cbElementType.setCurrentText(pipesLayerName)
        self.updateElementIds()

    # ------------------------------
    # Element Finding and Updating Methods
    # ------------------------------
    @pyqtSlot(int)
    def onElementIdChanged(self, index):
        self.labelFoundElement.setText("")
        self.labelFoundElementTag.setText("")
        self.labelFoundElementTag.hide()
        self.isTagVisible = False
        self.labelFoundElementDescription.setText("")
        self.labelFoundElementDescription.hide()
        self.isDescVisible = False
        self.listWidget.clear()
        self.dataTableWidget.clear()
        self.setDataTableWidgetColumns()

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

        selectedType = self.cbElementType.currentText()
        selectedId = self.extractNodeId(self.cbElementId.currentText())
        elementIdentifier = self.elementIdentifiers.get(selectedType)

        if not selectedId:
            self.labelFoundElement.setText("")
            return

        layer = self.getLayerForElementType(selectedType)
        foundFeature = None
        foundFeatureLayer = None

        if layer:
            if layer.customProperty("qgisred_identifier") in self.sourcesAndDemands:
                foundFeature, foundFeatureLayer = self.findSourceOrDemandForNodeId(selectedId)
            else:
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == selectedId:
                        foundFeature = feature
                        foundFeatureLayer = layer
                        break

        if not foundFeature:
            QMessageBox.information(self, self.tr("Info"), self.tr("Feature not found"))
            return

        self.currentLayer = foundFeatureLayer
        self.currentFeature = foundFeature

        finalTitleText = self.updateFoundElementLabel(selectedId, foundFeatureLayer)
        highlight = QgsHighlight(iface.mapCanvas(), foundFeature.geometry(), layer)
        highlight.setColor(QColor("red"))
        highlight.setWidth(5)
        highlight.show()
        self.mainHighlight = highlight
        self.adjustMapView(foundFeature)

        identifier = layer.customProperty("qgisred_identifier")
        if self.isLineElement(layer):
            self.findAdjacentNodesByGeometry(foundFeature)
        elif identifier == "qgisred_meters":
            self.findMeterAdjacency(foundFeature, layer)
        elif identifier == "qgisred_isolationvalves":
            self.findIsolationValveAdjacency(foundFeature, layer)
        elif identifier == "qgisred_serviceconnections":
            self.findServiceConnectionAdjacency(foundFeature, layer)
        else:
            self.findAdjacentLinksByGeometry(foundFeature, layer)
        self.sortListWidgetItems()
        self.loadFeature(layer, foundFeature, finalTitleText)

    @pyqtSlot()
    def updateElementIds(self):
        self.cbElementId.clear()
        self.labelFoundElement.setText("")
        
        selectedType = self.cbElementType.currentText()
        ids = self.dictOfElementIds.get(selectedType, [])
        
        mask = self.leElementMask.text().strip()
        if mask:
            filteredIds = [id for id in ids if mask.lower() in id.lower()]
            self.cbElementId.addItems(filteredIds)
        else:
            self.cbElementId.addItems(ids)

    @pyqtSlot()
    def filterElementIds(self):
        mask = self.leElementMask.text().strip()
        self.cbElementId.clear()
        selectedType = self.cbElementType.currentText()
        ids = self.dictOfElementIds.get(selectedType, [])
        if mask:
            filteredIds = [id for id in ids if mask.lower() in id.lower()]
        else:
            filteredIds = ids
        self.cbElementId.addItems(filteredIds)

    def onListItemSingleClicked(self, item):
        if self.currentSelectedHighlight:
            self.currentSelectedHighlight.hide()
            self.currentSelectedHighlight = None

        singularType, selectedId, _ = self.extractTypeAndId(item.text())
        if not singularType or not selectedId:
            return

        elementIdentifier = None
        for plural, singular in self.singularForms.items():
            if singular == singularType:
                elementIdentifier = self.elementIdentifiers.get(plural)
                break
        if not elementIdentifier:
            elementIdentifier = self.getIdentifierFromLayerName(singularType)

        matchingLayers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == elementIdentifier
        ]
        for layer in matchingLayers:
            for feature in layer.getFeatures():
                if self.getFeatureIdValue(feature, layer) == selectedId:
                    highlight = QgsHighlight(iface.mapCanvas(), feature.geometry(), layer)
                    highlight.setColor(QColor("orange"))
                    highlight.setWidth(5)
                    highlight.show()
                    self.currentSelectedHighlight = highlight
                    return

    def onListItemDoubleClicked(self, item):
        itemText = item.text()
        self.leElementMask.clear()
        singularType, selectedId, fullId = self.extractTypeAndId(itemText)
        if not singularType or not selectedId:
            return
        elementType = None
        for plural, singular in self.singularForms.items():
            if singular == singularType:
                elementType = plural
                break
        if not elementType:
            elementType = singularType
        self.cbElementType.setCurrentText(elementType)
        index = self.cbElementId.findText(fullId)
        if index >= 0:
            self.cbElementId.setCurrentIndex(index)
        self.findElement()

    # ------------------------------
    # Map and Feature Display Methods
    # ------------------------------
    def populateDataTableWidget(self):
        self.dataTableWidget.clearContents()
        self.dataTableWidget.setShowGrid(False)
        self.dataTableWidget.setStyleSheet("QTableWidget::item { padding: 1px; }")
        
        self.dataTableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        fields = self.currentLayer.fields()
        attributes = self.currentFeature.attributes()
        numFields = len(fields)
        self.dataTableWidget.setRowCount(numFields)
        self.setDataTableWidgetColumns()

        header = self.dataTableWidget.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStyleSheet("QHeaderView::section { font-weight: bold; }")
        
        self.dataTableWidget.verticalHeader().setDefaultSectionSize(20)
        
        totalWidth = self.dataTableWidget.viewport().width() + 20 
        self.dataTableWidget.setColumnWidth(0, totalWidth // 2)
        self.dataTableWidget.setColumnWidth(1, totalWidth // 2)
        
        self.dataTableWidget.verticalHeader().setVisible(False)
        
        for row, field in enumerate(fields):
            fieldItem = QTableWidgetItem(field.name())
            valueItem = QTableWidgetItem(str(attributes[row]))
            self.dataTableWidget.setItem(row, 0, fieldItem)
            self.dataTableWidget.setItem(row, 1, valueItem)

    def setDataTableWidgetColumns(self):
        self.dataTableWidget.setColumnCount(2)
        self.dataTableWidget.setHorizontalHeaderLabels(["Property", "Value"])

    def loadFeature(self, layer, feature, featureIdText=""):
        if not layer or not feature:
            return

        self.currentLayer = layer
        self.currentFeature = feature
        layer.selectByIds([feature.id()])
        self.populateDataTableWidget()

        if feature.fields().indexFromName("Tag") != -1:
            featureTag = feature.attribute("Tag")
        else:
            featureTag = ""

        if feature.fields().indexFromName("Descrip") != -1:
            featureDescription = feature.attribute("Descrip")
        else:
            featureDescription = "" 

        self.labelFoundElement.setText(f"{featureIdText}")
        self.labelFoundElement.setStyleSheet("font-weight: bold; font-size: 12pt;")

        if featureTag and str(featureTag).strip() != "":
            self.labelFoundElementTag.setText(str(featureTag))
            self.labelFoundElementTag.show()
            self.isTagVisible = True
        else:
            self.labelFoundElementTag.hide()
            self.isTagVisible = False

        if featureDescription and str(featureDescription).strip() != "":
            self.labelFoundElementDescription.setText(str(featureDescription))
            self.labelFoundElementDescription.show()
            self.isDescVisible = True
        else:
            self.labelFoundElementDescription.hide()
            self.isDescVisible = False


    def appendFeatureProperties(self, feature, labelSuffix=""):
        if not hasattr(self, 'dataTableWidget'):
            return
        fields = feature.fields()
        attributes = feature.attributes()
        currentRowCount = self.dataTableWidget.rowCount()
        newRowCount = currentRowCount + len(fields)
        self.dataTableWidget.setRowCount(newRowCount)
        for i, field in enumerate(fields):
            fieldName = f"{field.name()} ({labelSuffix})"
            fieldItem = QTableWidgetItem(fieldName)
            valueItem = QTableWidgetItem(str(attributes[i]))
            self.dataTableWidget.setItem(currentRowCount + i, 0, fieldItem)
            self.dataTableWidget.setItem(currentRowCount + i, 1, valueItem)

    def handleJunctions(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handlePipes(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handlePumps(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleReservoirs(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleTanks(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleValves(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
    
    def handleMeters(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleIsolationValves(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)

    def handleServiceConnections(self, layer, feature, tabs):
        self.setupTabs(tabs)
        self.loadFeature(layer, feature)
    
    def setupTabs(self, visibleTabs):
        ...

    def adjustMapView(self, feature):
        canvas = iface.mapCanvas()
        currentExtent = canvas.extent()
        geom = feature.geometry()
        featureExtent = geom.boundingBox()
        mapWidth = currentExtent.width()
        mapHeight = currentExtent.height()
        featWidth = featureExtent.width()
        featHeight = featureExtent.height()
        isPoint = (featWidth == 0 and featHeight == 0)
        featLargestDim = max(featWidth, featHeight)
        mapLargestDim = max(mapWidth, mapHeight)
        ratio = featLargestDim / mapLargestDim if mapLargestDim != 0 else 1
        center = featureExtent.center()
        if not isPoint:
            if ratio > 0.25:
                factor = ratio / 0.25
                newWidth = mapWidth * factor
                newHeight = mapHeight * factor
                newExtent = self.recenterExtent(newWidth, newHeight, center.x(), center.y())
            elif ratio < 0.05:
                factor = 0.05 / ratio
                newWidth = mapWidth / factor
                newHeight = mapHeight / factor
                newExtent = self.recenterExtent(newWidth, newHeight, center.x(), center.y())
            else:
                newExtent = QgsRectangle(currentExtent)
        else:
            newExtent = QgsRectangle(currentExtent)
        newExtent = self.applyMinimalPan(newExtent, featureExtent)
        canvas.setExtent(newExtent)
        canvas.refresh()

    def recenterExtent(self, newWidth, newHeight, centerX, centerY):
        halfW = newWidth / 2.0
        halfH = newHeight / 2.0
        rect = QgsRectangle(centerX - halfW, centerY - halfH, centerX + halfW, centerY + halfH)
        return rect

    def applyMinimalPan(self, currentExtent, featureExtent):
        marginX = currentExtent.width() * 0.1
        marginY = currentExtent.height() * 0.1
        leftDist = featureExtent.xMinimum() - currentExtent.xMinimum()
        rightDist = currentExtent.xMaximum() - featureExtent.xMaximum()
        topDist = currentExtent.yMaximum() - featureExtent.yMaximum()
        bottomDist = featureExtent.yMinimum() - currentExtent.yMinimum()
        newExtent = QgsRectangle(currentExtent)
        if leftDist < marginX:
            shift = marginX - leftDist
            newExtent.setXMinimum(newExtent.xMinimum() - shift)
            newExtent.setXMaximum(newExtent.xMaximum() - shift)
        if rightDist < marginX:
            shift = marginX - rightDist
            newExtent.setXMinimum(newExtent.xMinimum() + shift)
            newExtent.setXMaximum(newExtent.xMaximum() + shift)
        if topDist < marginY:
            shift = marginY - topDist
            newExtent.setYMinimum(newExtent.yMinimum() + shift)
            newExtent.setYMaximum(newExtent.yMaximum() + shift)
        if bottomDist < marginY:
            shift = marginY - bottomDist
            newExtent.setYMinimum(newExtent.yMinimum() - shift)
            newExtent.setYMaximum(newExtent.yMaximum() - shift)
        return newExtent

    # ------------------------------
    # Utility Functions
    # ------------------------------
    def buildNodeLayerSpatialIndices(self):
        """Build spatial indices for all node layers for fast lookup"""
        self.nodeLayerSpatialIndices.clear()
        supportedIds = ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]

        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in supportedIds:
                # Create spatial index for this layer
                spatialIndex = QgsSpatialIndex()
                for feature in layer.getFeatures():
                    if not feature.geometry().isEmpty():
                        spatialIndex.addFeature(feature)
                self.nodeLayerSpatialIndices[layer.id()] = (spatialIndex, layer)

    def findOverlappingNodeOptimized(self, pointGeom, excludeLayer=None):
        """Find node that overlaps with given point geometry using spatial index"""
        if pointGeom.isEmpty():
            return None, None

        point = pointGeom.asPoint()
        searchRect = QgsRectangle(point.x() - 1e-6, point.y() - 1e-6,
                                  point.x() + 1e-6, point.y() + 1e-6)

        for layerId, (spatialIndex, layer) in self.nodeLayerSpatialIndices.items():
            if excludeLayer and layer == excludeLayer:
                continue

            # Get candidate features from spatial index
            candidateIds = spatialIndex.intersects(searchRect)

            for fid in candidateIds:
                feature = layer.getFeature(fid)
                if not feature.geometry().isEmpty():
                    if self.areOverlappedPoints(pointGeom, feature.geometry()):
                        return feature, layer

        return None, None

    def getAvailableElementTypes(self):
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputsGroup:
            return []
        availableTypes = []
        checkedLayers = inputsGroup.checkedLayers()
        for element, identifier in self.elementIdentifiers.items():
            for layer in checkedLayers:
                if layer and layer.customProperty("qgisred_identifier") == identifier:
                    availableTypes.append(layer.name())
                    break
        return availableTypes

    def getLayerForElementType(self, elementType):
        project = QgsProject.instance()
        layers = project.mapLayersByName(elementType)
        layerFound = layers[0] if layers else None
        return layerFound

    def getLayerByIdentifier(self, identifier):
        for layer in self.getCheckedInputGroupLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                return layer
        return None

    def getFeatureIdValue(self, feature, layer, specialNaming=False):
        if not layer:
            return "Id"

        identifier = layer.customProperty("qgisred_identifier")

        if identifier in self.sourcesAndDemands:
            # Check cache first
            cacheKey = (identifier, feature.id())

            if cacheKey not in self.sourcesDemandToNodeCache:
                # Not in cache, compute it
                # Ensure spatial indices are built
                if not self.nodeLayerSpatialIndices:
                    self.buildNodeLayerSpatialIndices()

                # Use optimized spatial search
                nodeFeature, nodeLayer = self.findOverlappingNodeOptimized(feature.geometry())

                if nodeFeature and nodeLayer:
                    nodeId = self.extractNodeId(nodeFeature.attribute("Id"))
                    nodeLayerName = nodeLayer.name()
                    self.sourcesDemandToNodeCache[cacheKey] = (nodeId, nodeLayerName)
                else:
                    self.sourcesDemandToNodeCache[cacheKey] = (None, None)

            # Get from cache
            nodeId, nodeLayerName = self.sourcesDemandToNodeCache[cacheKey]

            if nodeId:
                if specialNaming:
                    singular = self.singularForms.get(nodeLayerName, nodeLayerName)
                    suffix = "(Source)" if identifier == "qgisred_sources" else "(Mult.Dem)"
                    return f"{singular} {nodeId} {suffix}"
                return str(nodeId)
            return ""
        else:
            # Original code for non-source/demand features
            value = feature.attribute("Id")
            idStr = str(value) if value is not None else ""

            if specialNaming and identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                suffixes = []
                # Build spatial indices if needed for source/demand overlap check
                if not self.nodeLayerSpatialIndices:
                    self.buildNodeLayerSpatialIndices()

                sourceLayer = self.getLayerByIdentifier("qgisred_sources")
                if sourceLayer:
                    for srcFeat in sourceLayer.getFeatures():
                        if self.areOverlappedPoints(feature.geometry(), srcFeat.geometry()):
                            suffixes.append("(Source)")
                            break

                if identifier == "qgisred_junctions":
                    demandLayer = self.getLayerByIdentifier("qgisred_demands")
                    if demandLayer:
                        for dmndFeat in demandLayer.getFeatures():
                            if self.areOverlappedPoints(feature.geometry(), dmndFeat.geometry()):
                                suffixes.append("(Mult.Dem)")
                                break

                if suffixes:
                    idStr += " " + " ".join(suffixes)

            return idStr

    def extractNodeId(self, text):
        text = text.replace(" (Source)", "").replace(" (Mult.Dem)", "")
        parts = text.strip().split()
        result = parts[-1] if len(parts) > 1 else text
        return result

    def extractTypeAndId(self, text):
        originalText = text.strip()
        textClean = originalText.replace(" (Source)", "").replace(" (Mult.Dem)", "").strip()
        sortedSingulars = sorted(self.singularForms.values(), key=len, reverse=True)
        for singular in sortedSingulars:
            if textClean.startswith(singular + " "):
                selectedId = textClean[len(singular):].strip()
                fullId = originalText[len(singular):].strip() if originalText.startswith(singular + " ") else selectedId
                return singular, selectedId, fullId
        parts = textClean.split(" ", 1)
        if len(parts) < 2:
            return None, None, None
        singular = parts[0]
        selectedId = parts[1].strip()
        fullId = originalText[len(singular):].strip() if originalText.startswith(singular + " ") else selectedId
        return singular, selectedId, fullId

    def getIdentifierFromLayerName(self, layerName):
        layers = QgsProject.instance().mapLayersByName(layerName)
        if layers:
            result = layers[0].customProperty("qgisred_identifier", None)
            return result
        return None

    def areOverlappedPoints(self, point1, point2, tolerance=1e-9):
        return point1.distance(point2) < tolerance

    def updateFoundElementLabel(self, selectedId, layer=None):
        if not selectedId:
            self.labelFoundElement.setText("")
            return

        if layer and layer.customProperty("qgisred_identifier") in self.sourcesAndDemands:
            nodeLayer, nodeFeat = self.findNodeLayer(selectedId)
        elif layer:
            nodeFeat = None
            for feat in layer.getFeatures():
                if self.getFeatureIdValue(feat, layer) == selectedId:
                    nodeFeat = feat
                    break
            nodeLayer = layer if nodeFeat else None
        else:
            nodeLayer, nodeFeat = self.findNodeLayer(selectedId)

        if nodeLayer and nodeFeat:
            suffixes = []
            nodeIdentifier = nodeLayer.customProperty("qgisred_identifier", "")
            if nodeIdentifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                sourceLayer = self.getLayerByIdentifier("qgisred_sources")
                if sourceLayer:
                    for srcFeat in sourceLayer.getFeatures():
                        if (not srcFeat.geometry().isEmpty() and
                            self.areOverlappedPoints(nodeFeat.geometry(), srcFeat.geometry())):
                            suffixes.append("(Source)")
                            break
            if nodeIdentifier == "qgisred_junctions":
                demandLayer = self.getLayerByIdentifier("qgisred_demands")
                if demandLayer:
                    for dmndFeat in demandLayer.getFeatures():
                        if (not dmndFeat.geometry().isEmpty() and
                            self.areOverlappedPoints(nodeFeat.geometry(), dmndFeat.geometry())):
                            suffixes.append("(Mult.Dem)")
                            break
            singularNodeType = self.singularForms.get(nodeLayer.name(), nodeLayer.name())
            suffixStr = " ".join(suffixes)
            finalText = self.tr(f"{singularNodeType} {selectedId} {suffixStr}".strip())
            self.labelFoundElement.setText(finalText)
        else:
            elementType = self.cbElementType.currentText()
            singularElementType = self.singularForms.get(elementType, elementType)
            finalText = self.tr(f"{singularElementType} {selectedId}")
            self.labelFoundElement.setText(finalText)

        return finalText

    def findNodeLayer(self, nodeId):
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.nodeLayers:
                if identifier in self.sourcesAndDemands:
                    continue
                for feature in layer.getFeatures():
                    if self.getFeatureIdValue(feature, layer) == nodeId:
                        return layer, feature
        return None, None

    def findOverlappedNode(self, pointFeature, currentLayer, supportedOnly=False):
        featureGeom = pointFeature.geometry()
        if featureGeom.isEmpty():
            return None, None
        featurePoint = featureGeom.asPoint()
        featurePointGeom = QgsGeometry.fromPointXY(featurePoint)
        tolerance = 1e-6
        if supportedOnly:
            supportedIds = ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]
            for nodeLayer in self.getCheckedInputGroupLayers():
                if nodeLayer == currentLayer:
                    continue
                nodeIdentifier = nodeLayer.customProperty("qgisred_identifier", "")
                if nodeIdentifier not in supportedIds:
                    continue
                for nodeFeature in nodeLayer.getFeatures():
                    nodeGeom = nodeFeature.geometry()
                    if nodeGeom.isEmpty():
                        continue
                    nodePointGeom = QgsGeometry.fromPointXY(nodeGeom.asPoint())
                    if self.areOverlappedPoints(featurePointGeom, nodePointGeom):
                        return nodeFeature, nodeLayer
            return None, None
        else:
            for nodeLayer in self.getCheckedInputGroupLayers():
                if nodeLayer == currentLayer:
                    continue
                nodeIdentifier = nodeLayer.customProperty("qgisred_identifier", "")
                if nodeIdentifier in self.nodeLayers and nodeIdentifier not in self.sourcesAndDemands:
                    for nodeFeature in nodeLayer.getFeatures():
                        nodeGeom = nodeFeature.geometry()
                        if nodeGeom.isEmpty():
                            continue
                        nodePointGeom = QgsGeometry.fromPointXY(nodeGeom.asPoint())
                        if self.areOverlappedPoints(featurePointGeom, nodePointGeom):
                            return nodeFeature, nodeLayer
            return None, None

    def findSourceOrDemandForNodeId(self, nodeId):
        nodeLayer, nodeFeat = self.findNodeLayer(nodeId)
        if not nodeLayer or not nodeFeat:
            return None, None 
        nodeGeom = nodeFeat.geometry()
        if nodeGeom.isEmpty():
            return None, None 
        for layer in self.getCheckedInputGroupLayers():
            identifier = layer.customProperty("qgisred_identifier", "")
            if identifier in self.sourcesAndDemands: 
                for feat in layer.getFeatures():
                    featGeom = feat.geometry()
                    if featGeom.isEmpty():
                        continue
                    if self.areOverlappedPoints(nodeGeom, featGeom):
                        return feat, layer
        return None, None

    def isLineElement(self, layer):
        result = layer.customProperty("qgisred_identifier") in self.linkLayers
        return result

    def addAdjacencyItem(self, itemText, identifier):
        newItem = QListWidgetItem(self.tr(itemText))
        newItem.setData(Qt.UserRole, identifier)
        self.listWidget.addItem(newItem)

    def sortListWidgetItems(self):
        items = []
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            items.append((item.text(), item.data(Qt.UserRole)))
        self.listWidget.clear()

        def sortKey(entry):
            _, iden = entry
            try:
                return list(self.elementIdentifiers.values()).index(iden)
            except ValueError:
                return len(self.elementIdentifiers)
        for text, identifier in sorted(items, key=sortKey):
            newItem = QListWidgetItem(text)
            newItem.setData(Qt.UserRole, identifier)
            self.listWidget.addItem(newItem)

    def addServiceConnectionAdjacencies(self, currentGeom, tolerance):
        serviceLayers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_serviceconnections"
        ]
        for layer in serviceLayers:
            for feat in layer.getFeatures():
                serviceGeom = feat.geometry()
                if serviceGeom.isEmpty():
                    continue
                if currentGeom.intersects(serviceGeom) or currentGeom.distance(serviceGeom) < tolerance:
                    serviceId = self.getFeatureIdValue(feat, layer)
                    singular = self.singularForms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {serviceId}", layer.customProperty("qgisred_identifier"))

    def addIsolationValveAdjacencies(self, currentGeom, tolerance):
        isolationLayers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") == "qgisred_isolationvalves"
        ]
        for layer in isolationLayers:
            for feat in layer.getFeatures():
                isoGeom = feat.geometry()
                if isoGeom.isEmpty():
                    continue
                if currentGeom.intersects(isoGeom) or currentGeom.distance(isoGeom) < tolerance:
                    isoId = self.getFeatureIdValue(feat, layer)
                    singular = self.singularForms.get(layer.name(), layer.name())
                    self.addAdjacencyItem(f"{singular} {isoId}", layer.customProperty("qgisred_identifier"))

    def findAdjacentNodesByGeometry(self, lineFeature):
        geom = lineFeature.geometry()
        if geom.isEmpty():
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            linePoints = parts[0] if parts else []
        else:
            linePoints = geom.asPolyline()
        if not linePoints:
            return
        lineGeom = QgsGeometry.fromPolylineXY(linePoints)
        tolerance = 1e-6
        foundNodes = []
        nodeLayers = [
            layer for layer in self.getCheckedInputGroupLayers()
            if layer.customProperty("qgisred_identifier") in (self.nodeLayers + self.specialLayers)
        ]
        for nodeLayer in nodeLayers:
            if nodeLayer.geometryType() != 0:
                continue
            identifier = nodeLayer.customProperty("qgisred_identifier", "")
            if identifier in self.sourcesAndDemands:
                continue
            for f in nodeLayer.getFeatures():
                nodeGeom = f.geometry()
                if nodeGeom.isEmpty():
                    continue
                if lineGeom.distance(nodeGeom) < tolerance:
                    nodeId = self.getFeatureIdValue(f, nodeLayer)
                    layerName = nodeLayer.name()
                    singular = self.singularForms.get(layerName, layerName)
                    nodeSuffixes = []
                    if identifier in ["qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks"]:
                        sourceLayer = self.getLayerByIdentifier("qgisred_sources")
                        if sourceLayer:
                            for srcFeat in sourceLayer.getFeatures():
                                if self.areOverlappedPoints(nodeGeom, srcFeat.geometry()):
                                    nodeSuffixes.append("(Source)")
                                    break
                        if identifier == "qgisred_junctions":
                            demandLayer = self.getLayerByIdentifier("qgisred_demands")
                            if demandLayer:
                                for dmndFeat in demandLayer.getFeatures():
                                    if self.areOverlappedPoints(nodeGeom, dmndFeat.geometry()):
                                        nodeSuffixes.append("(Mult.Dem)")
                                        break
                    suffixStr = " " + " ".join(nodeSuffixes) if nodeSuffixes else ""
                    nodeInfo = f"{singular} {nodeId}{suffixStr}"
                    foundNodes.append((nodeLayer, f, nodeInfo))
        for nodeLayer, f, nodeInfo in foundNodes:
            self.addAdjacencyItem(nodeInfo, nodeLayer.customProperty("qgisred_identifier", ""))
        self.addServiceConnectionAdjacencies(lineGeom, tolerance)

    def findAdjacentLinksByGeometry(self, nodeFeature, layer):
        nodeGeom = nodeFeature.geometry()
        if nodeGeom.isEmpty():
            return
        nodePoint = QgsPointXY(nodeGeom.asPoint())
        nodeG = QgsGeometry.fromPointXY(nodePoint)
        tolerance = 1e-9
        foundLinks = []
        linkLayers = [
            lyr for lyr in self.getCheckedInputGroupLayers()
            if lyr.customProperty("qgisred_identifier") in (self.linkLayers + ["qgisred_meters"])
        ]
        for linkLayer in linkLayers:
            ident = linkLayer.customProperty("qgisred_identifier", "")
            if ident in self.linkLayers:
                if linkLayer.geometryType() != 1:
                    continue
                for f in linkLayer.getFeatures():
                    linkGeom = f.geometry()
                    if linkGeom.isMultipart():
                        parts = linkGeom.asMultiPolyline()
                        linePoints = parts[0] if parts else []
                    else:
                        linePoints = linkGeom.asPolyline()
                    if not linePoints:
                        continue
                    if (nodeG.distance(linkGeom) < tolerance or
                        self.areOverlappedPoints(nodeG, QgsGeometry.fromPointXY(linePoints[0])) or
                        self.areOverlappedPoints(nodeG, QgsGeometry.fromPointXY(linePoints[-1]))):
                        linkId = self.getFeatureIdValue(f, linkLayer)
                        layerName = linkLayer.name()
                        singular = self.singularForms.get(layerName, layerName)
                        foundLinks.append((linkLayer, f, f"{singular} {linkId}"))
            elif ident == "qgisred_meters":
                if linkLayer.geometryType() != 0:
                    continue
                for f in linkLayer.getFeatures():
                    meterGeom = f.geometry()
                    if meterGeom.isEmpty():
                        continue
                    if nodeG.distance(meterGeom) < tolerance:
                        meterId = self.getFeatureIdValue(f, linkLayer)
                        layerName = linkLayer.name()
                        singular = self.singularForms.get(layerName, layerName)
                        foundLinks.append((linkLayer, f, f"{singular} {meterId}"))
        for linkLayer, f, linkInfo in foundLinks:
            self.addAdjacencyItem(linkInfo, linkLayer.customProperty("qgisred_identifier"))
        self.addServiceConnectionAdjacencies(nodeG, tolerance)
        if layer.customProperty("qgisred_identifier") == "qgisred_junctions":
            self.addIsolationValveAdjacencies(nodeG, tolerance)

    def findServiceConnectionAdjacency(self, feature, currentLayer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        if geom.isMultipart():
            parts = geom.asMultiPolyline()
            if not parts or not parts[0]:
                return
            linePoints = parts[0]
        else:
            linePoints = geom.asPolyline()
        if not linePoints:
            return
        endpoints = [QgsPointXY(linePoints[0]), QgsPointXY(linePoints[-1])]
        tolerance = 1e-6
        for pt in endpoints:
            dummyFeature = QgsFeature()
            dummyFeature.setGeometry(QgsGeometry.fromPointXY(pt))
            nodeFeature, nodeLayer = self.findOverlappedNode(dummyFeature, currentLayer)
            if nodeFeature and nodeLayer.customProperty("qgisred_identifier") == "qgisred_junctions":
                junctionItemText = self.getFeatureIdValue(nodeFeature, nodeLayer, True)
                singularName = self.singularForms.get(nodeLayer.name(), nodeLayer.name())
                junctionFullName = singularName + ' ' + junctionItemText
                self.addAdjacencyItem(junctionFullName, nodeLayer.customProperty("qgisred_identifier"))
                return
        for pt in endpoints:
            ptGeom = QgsGeometry.fromPointXY(pt)
            for lyr in self.getCheckedInputGroupLayers():
                if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                    for f in lyr.getFeatures():
                        pipeGeom = f.geometry()
                        if pipeGeom.isEmpty():
                            continue
                        if ptGeom.distance(pipeGeom) < tolerance:
                            pipeId = self.getFeatureIdValue(f, lyr)
                            singular = self.singularForms.get(lyr.name(), lyr.name())
                            fullName = f"{singular} {pipeId}"
                            self.addAdjacencyItem(fullName, lyr.customProperty("qgisred_identifier"))
                            return

    def findIsolationValveAdjacency(self, feature, currentLayer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        tolerance = 1e-6
        nodeFeature, nodeLayer = self.findOverlappedNode(feature, currentLayer)
        if nodeFeature and nodeLayer.customProperty("qgisred_identifier") == "qgisred_junctions":
            nodeItemText = self.getFeatureIdValue(nodeFeature, nodeLayer, True)
            singularName = self.singularForms.get(nodeLayer.name(), nodeLayer.name())
            nodeFullName = singularName + ' ' + nodeItemText
            self.addAdjacencyItem(nodeFullName, nodeLayer.customProperty("qgisred_identifier"))
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") == "qgisred_pipes":
                for f in lyr.getFeatures():
                    pipeGeom = f.geometry()
                    if pipeGeom.isEmpty():
                        continue
                    if geom.distance(pipeGeom) < tolerance:
                        pipeId = self.getFeatureIdValue(f, lyr)
                        singular = self.singularForms.get(lyr.name(), lyr.name())
                        fullName = f"{singular} {pipeId}"
                        self.addAdjacencyItem(fullName, lyr.customProperty("qgisred_identifier"))
                        return

    def findMeterAdjacency(self, feature, currentLayer):
        geom = feature.geometry()
        if geom.isEmpty():
            return
        tolerance = 1e-6
        nodeFeature, nodeLayer = self.findOverlappedNode(feature, currentLayer)
        if nodeFeature:
            nodeId = self.getFeatureIdValue(nodeFeature, nodeLayer, True)
            singularName = self.singularForms.get(nodeLayer.name(), nodeLayer.name())
            nodeItemText = singularName + ' ' + nodeId
            self.addAdjacencyItem(nodeItemText, nodeLayer.customProperty("qgisred_identifier"))
            return
        for lyr in self.getCheckedInputGroupLayers():
            if lyr.customProperty("qgisred_identifier") != "qgisred_meters":
                for f in lyr.getFeatures():
                    linkGeom = f.geometry()
                    if linkGeom.isEmpty():
                        continue
                    if geom.distance(linkGeom) < tolerance:
                        adjId = self.getFeatureIdValue(f, lyr)
                        singular = self.singularForms.get(lyr.name(), lyr.name())
                        fullName = f"{singular} {adjId}"
                        self.addAdjacencyItem(fullName, lyr.customProperty("qgisred_identifier"))
                        return

    def findFeature(self, layer, feature):
        elementTypeText = layer.name()
        self.cbElementType.setCurrentText(elementTypeText)
        
        self.updateElementIds()
        
        featureIdText = self.getFeatureIdValue(feature, layer, specialNaming=True)
        
        index = self.cbElementId.findText(featureIdText)
        if index >= 0:
            self.cbElementId.setCurrentIndex(index)

        self.clearHighlights()
        self.clearAllLayerSelections()
        self.listWidget.clear()

        finalTitleText = self.updateFoundElementLabel(featureIdText, layer)

        highlight = QgsHighlight(iface.mapCanvas(), feature.geometry(), layer)
        highlight.setColor(QColor("red"))
        highlight.setWidth(5)
        highlight.show()
        self.mainHighlight = highlight

        self.adjustMapView(feature)
        
        identifier = layer.customProperty("qgisred_identifier")
        if self.isLineElement(layer):
            self.findAdjacentNodesByGeometry(feature)
        elif identifier == "qgisred_meters":
            self.findMeterAdjacency(feature, layer)
        elif identifier == "qgisred_isolationvalves":
            self.findIsolationValveAdjacency(feature, layer)
        elif identifier == "qgisred_serviceconnections":
            self.findServiceConnectionAdjacency(feature, layer)
        else:
            self.findAdjacentLinksByGeometry(feature, layer)
        
        self.sortListWidgetItems()

        self.loadFeature(layer, feature, finalTitleText)

    def getCheckedInputGroupLayers(self):
        inputsGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if not inputsGroup:
            return []
        return inputsGroup.checkedLayers()
