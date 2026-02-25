from ..ui.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor
from qgis.core import QgsPointXY, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapCanvasSnappingUtils


class QGISRedIdentifyFeature(QgsMapToolIdentify):
    _instance = None
    dockVisibilityChanged = pyqtSignal(bool)
    findElementsDockVisibilityChanged = pyqtSignal(bool)
    elementPropertiesDockVisibilityChanged = pyqtSignal(bool)
    dockFocusChanged = pyqtSignal(bool)

    # -------------------------------
    # Initialization and Setup Methods
    # -------------------------------
    def __init__(self, canvas, button, toggleAction=None, useElementPropertiesDock=True, dock=None):
        super().__init__(canvas)
        self.canvas = canvas
        self.setAction(button)
        self.toggleAction = toggleAction
        self.useElementPropertiesDock = useElementPropertiesDock
        self.currentHighlight = None
        self.dock = dock
        self.ignoreNextRelease = False
        self.setupConnections()
        self.startVertexes()
        self.resetProperties()
        self.setDockConnections()

    def setDock(self):
        self.dock = QGISRedElementExplorerDock.getInstance(
            self.canvas,
            iface.mainWindow(),
            showFindElements=True,
            showElementProperties=True
        )

        if self.useElementPropertiesDock:
            self.dock.updateCollapsibleWidgetsState(collapseElementProperties=False)
            
        self.setDockConnections()
    
    def setDockConnections(self):
        if self.dock is not None:
            self.dock.dockClosed.connect(self.onDockClosed)

    def onDockClosed(self, closed):
        if closed:
            self.deactivate()
            if self.canvas.mapTool() == self:
                self.canvas.unsetMapTool(self)

    def resetProperties(self):
        self.firstPoint = None
        self.startMarker.hide()
        self.endMarker.hide()
        self.objectSnapped = None

    def setupConnections(self):
        project = QgsProject.instance()
        project.readProject.connect(self.deactivate)
        project.cleared.connect(self.deactivate)

    def configSnapper(self):
        self.snapper = QgsMapCanvasSnappingUtils(self.canvas)
        self.snapper.setMapSettings(self.canvas.mapSettings())
        config = QgsSnappingConfig(QgsProject.instance())
        config.setType(2)
        config.setMode(QgsSnappingConfig.SnappingMode.AllLayers)
        config.setTolerance(10)
        config.setUnits(QgsTolerance.UnitType.Pixels)
        config.setEnabled(True)
        self.snapper.setConfig(config)

    def startVertexes(self):
        self.startMarker = QgsVertexMarker(self.canvas)
        self.startMarker.setColor(QColor(255, 87, 51))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE) 
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.canvas)
        self.endMarker.setColor(QColor(0, 128, 0))
        self.endMarker.setIconSize(15)
        self.endMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE)
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()
        self.firstPoint = None

        self.snapper = None
    
    # -------------------------------
    # Feature Handling Methods
    # -------------------------------
    def getHandlers(self):
        return {
            'qgisred_meters': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleMeters'),
            'qgisred_isolationvalves': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleIsolationValves'),
            'qgisred_junctions': (['tabData', 'tabResults', 'tabPatterns', 'tabControls'], 'handleJunctions'),
            'qgisred_valves': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleValves'),
            'qgisred_pumps': (['tabData', 'tabResults', 'tabCurves', 'tabPatterns', 'tabControls'], 'handlePumps'),
            'qgisred_tanks': (['tabData', 'tabResults', 'tabCurves', 'tabPatterns', 'tabControls'], 'handleTanks'),
            'qgisred_reservoirs': (['tabData', 'tabResults', 'tabPatterns', 'tabControls'], 'handleReservoirs'),
            'qgisred_pipes': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handlePipes'),
            'qgisred_serviceconnections': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleServiceConnections')
        }

    def getFeatureByPriority(self, allFeatures):
        handlers = self.getHandlers()
        selectedFeature = None
        selectedLayer = None
        selectedHandler = None

        for identifierKey, handlerData in handlers.items():
            for result in allFeatures:
                identifier = result.mLayer.customProperty("qgisred_identifier")
                if identifier == identifierKey:
                    selectedFeature = result.mFeature
                    selectedLayer = result.mLayer
                    selectedHandler = handlerData
                    break
            if selectedHandler:
                break

        if not selectedHandler and allFeatures:
            topResult = allFeatures[0]
            selectedFeature = topResult.mFeature
            selectedLayer = topResult.mLayer

        return selectedLayer, selectedFeature, selectedHandler

    def getSortedFeatures(self, allFeatures):
        handlers = self.getHandlers()
        sortedResults = []
        for result in allFeatures:
            identifier = result.mLayer.customProperty("qgisred_identifier")
            if identifier in handlers:
                priority = list(handlers.keys()).index(identifier)
            else:
                priority = len(handlers)
            sortedResults.append((priority, result))
        sortedResults.sort(key=lambda x: x[0])
        return sortedResults

    def clearSelections(self):
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def selectFeature(self, layer, feature):
        layer.select(feature.id())

    def highlightFeature(self, layer, feature):
        self.clearHighlights()
        self.currentHighlight = QgsHighlight(self.canvas, feature.geometry(), layer)
        self.currentHighlight.setColor(Qt.red)
        self.currentHighlight.setWidth(4)
        self.currentHighlight.setFillColor(Qt.transparent)
        self.currentHighlight.show()

    def clearHighlights(self):
        if self.currentHighlight is not None:
            self.currentHighlight.hide()
            self.currentHighlight = None

        canvas = iface.mapCanvas()
        scene = canvas.scene()
        for item in scene.items():
            if isinstance(item, QgsHighlight):
                item.hide()
                scene.removeItem(item)
                del item
        canvas.refresh()
        self.clearSelections()

    # -------------------------------
    # Dock Handling Methods
    # -------------------------------
    def showFeatureInDock(self, layer, feature, handler=None):
        if self.dock is None:
            self.setDock()

        wasHidden = not self.dock.isVisible()
        if wasHidden:
            iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.show()
            self.dock.raise_()
            self.dock.activateWindow()

        self.dock.findFeature(layer, feature)

        if wasHidden and self.useElementPropertiesDock:
            self.dock.scrollToElementProperties()

    def closeDock(self):
        if self.dock:
            self.dock.close()

    # -------------------------------
    # Map Tool Event Handlers
    # -------------------------------
    def canvasReleaseEvent(self, event):
        if self.ignoreNextRelease:
            self.ignoreNextRelease = False
            return

        allFeatures = self.identify(event.x(), event.y(), self.TopDownAll)
        if not allFeatures:
            return

        selectedLayer, selectedFeature, selectedHandler = self.getFeatureByPriority(allFeatures)

        self.clearSelections()
        self.selectFeature(selectedLayer, selectedFeature)
        self.highlightFeature(selectedLayer, selectedFeature)
        self.showFeatureInDock(selectedLayer, selectedFeature, selectedHandler)

    def canvasDoubleClickEvent(self, event):
        self.ignoreNextRelease = True

        allFeatures = self.identify(event.x(), event.y(), self.TopDownAll)
        if not allFeatures:
            return

        sortedResults = self.getSortedFeatures(allFeatures)
        if len(sortedResults) < 2:
            self.canvasReleaseEvent(event)
            return

        secondResult = sortedResults[1][1]
        selectedFeature = secondResult.mFeature
        selectedLayer = secondResult.mLayer

        handlers = self.getHandlers()
        identifier = selectedLayer.customProperty("qgisred_identifier")
        selectedHandler = handlers.get(identifier, None)

        self.clearSelections()
        self.selectFeature(selectedLayer, selectedFeature)
        self.highlightFeature(selectedLayer, selectedFeature)
        self.showFeatureInDock(selectedLayer, selectedFeature, selectedHandler)

    def canvasMoveEvent(self, event):
        match = self.snapper.snapToMap(self.toMapCoordinates(event.pos()))
        if match.isValid():
            self.objectSnapped = match
            if self.firstPoint is None:
                self.startMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.startMarker.show()
            else:
                self.endMarker.setCenter(QgsPointXY(match.point().x(), match.point().y()))
                self.endMarker.show()
        else:
            self.startMarker.hide()
            self.endMarker.hide()
            self.objectSnapped = None

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.deactivate()

    # -------------------------------
    # Activation and Deactivation Methods
    # -------------------------------
    def activate(self):
        QgsMapTool.activate(self)
        self.configSnapper()

    def setIdentifyFeatureAsMapTool(self):
        self.canvas.setMapTool(self)

    def disconnectProjectSignals(self):
        project = QgsProject.instance()
        try:
            project.readProject.disconnect(self.deactivate)
        except Exception as e:
            pass
        try:
            project.cleared.disconnect(self.deactivate)
        except Exception as e:
            pass

    def setActionUnchecked(self):
        if self.toggleAction:
            self.toggleAction.setChecked(False)

    def deactivate(self):
        self.clearHighlights()
        
        if self.startMarker:
            self.startMarker.hide()
        if self.endMarker:
            self.endMarker.hide()

        self.resetProperties()
        
        self.disconnectProjectSignals()
        self.setActionUnchecked()
        
        QgsMapToolIdentify.deactivate(self)
