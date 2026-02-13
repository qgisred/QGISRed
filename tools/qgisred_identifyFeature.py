from ..ui.qgisred_unified_find_properties import QGISRedElementsExplorerDock
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

class QGISRedIdentifyFeature(QgsMapToolIdentify):
    _instance = None
    dockVisibilityChanged = pyqtSignal(bool)
    findElementsDockVisibilityChanged = pyqtSignal(bool)
    elementPropertiesDockVisibilityChanged = pyqtSignal(bool)
    dockFocusChanged = pyqtSignal(bool)

    def __init__(self, canvas, button, toggle_action=None, useElementPropertiesDock=True):
        print("QGISRedIdentifyFeature.__init__: Initializing")
        super().__init__(canvas)
        self.canvas = canvas
        self.setAction(button)
        self.toggle_action = toggle_action
        self.useElementPropertiesDock = useElementPropertiesDock
        self.currentHighlight = None
        self.dock = None
        self.ignoreNextRelease = False
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setupConnections()

    # -----------------------
    # Helper Methods
    # -----------------------
    def getHandlers(self):
        print("getHandlers: Returning handlers dictionary")
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

    def clearSelections(self):
        print("clearSelections: Clearing selections on all vector layers")
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def highlightFeature(self, layer, feature):
        print("highlightFeature: Highlighting feature on layer", layer.name() if hasattr(layer, "name") else layer)
        self.clearHighlights()
        self.currentHighlight = QgsHighlight(self.canvas, feature.geometry(), layer)
        self.currentHighlight.setColor(Qt.red)
        self.currentHighlight.setWidth(4)
        self.currentHighlight.setFillColor(Qt.transparent)
        self.currentHighlight.show()
    
    def showFeatureInDock(self, layer, feature, handler=None):
        print("showFeatureInDock: Showing feature in dock")
        self.dock = QGISRedElementsExplorerDock.getInstance(
            self.canvas, 
            iface.mainWindow(),
            show_find_elements=True,
            show_element_properties=True
        )


        if self.dock is None:
            print("showFeatureInDock: No dock available")
            return
        
        if not self.dock.isVisible():
            print("showFeatureInDock: Dock is not visible; adding and showing dock")
            iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.show()
            self.dock.raise_()
            self.dock.activateWindow()
            
        print("showFeatureInDock: Finding feature in dock")
        self.dock.findFeature(layer, feature)
        
        # if hasattr(self.dock, 'dockFocusChanged'):
        #     print("connected")
        #     self.dock.dockFocusChanged.connect(self.setIdentifyFeatureAsMapTool)

        # if hasattr(self.dock, 'dockVisibilityChanged'):
        #     print("showFeatureInDock: Connecting dockVisibilityChanged signal")
        #     self.dock.dockVisibilityChanged.connect(self.deactivate)
        
        # if hasattr(self.dock, 'elementPropertiesDockVisibilityChanged'):
        #     self.dock.elementPropertiesDockVisibilityChanged.connect(self.setUseElementProperties)

        # if hasattr(self.dock, 'findElementsDockVisibilityChanged'):
        #     self.dock.findElementsDockVisibilityChanged.connect(self.setFindElementsVisibility)
    
        # if hasattr(self.dock, 'dockFocusChanged'):
        #     print("showFeatureInDock: Connecting dockVisibilityChanged signal")
        #     self.dock.dockFocusChanged.connect(self.deactivate)

    def setIdentifyFeatureAsMapTool(self):
        self.canvas.setMapTool(self)

    def selectFeature(self, layer, feature):
        print("selectFeature: Selecting feature with id", feature.id())
        layer.select(feature.id())

    def getFeatureByPriority(self, all_features):
        print("getFeatureByPriority: Determining feature by priority")
        handlers = self.getHandlers()
        selected_feature = None
        selected_layer = None
        selected_handler = None

        for identifier_key, handler_data in handlers.items():
            for result in all_features:
                identifier = result.mLayer.customProperty("qgisred_identifier")
                if identifier == identifier_key:
                    selected_feature = result.mFeature
                    selected_layer = result.mLayer
                    selected_handler = handler_data
                    print("getFeatureByPriority: Selected feature with identifier", identifier_key)
                    break
            if selected_handler:
                break

        if not selected_handler and all_features:
            print("getFeatureByPriority: No handler found; defaulting to first feature")
            top_result = all_features[0]
            selected_feature = top_result.mFeature
            selected_layer = top_result.mLayer

        return selected_layer, selected_feature, selected_handler

    def getSortedFeatures(self, all_features):
        print("getSortedFeatures: Sorting features based on handler priority")
        handlers = self.getHandlers()
        sorted_results = []
        for result in all_features:
            identifier = result.mLayer.customProperty("qgisred_identifier")
            if identifier in handlers:
                priority = list(handlers.keys()).index(identifier)
            else:
                priority = len(handlers)
            sorted_results.append((priority, result))
        sorted_results.sort(key=lambda x: x[0])
        print("getSortedFeatures: Sorted results based on priority")
        return sorted_results

    # -----------------------
    # Additional Methods
    # -----------------------
    # def clearHighlights(self):
    #     if self.currentHighlight is not None:
    #         print("clearHighlights: Clearing current highlight")
    #         self.currentHighlight.hide()
    #         self.currentHighlight = None

    def clearHighlights(self):
        if self.currentHighlight is not None:
            print("clearHighlights: Clearing current highlight")
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
        print("Exiting clearHighlights")
        self.clearSelections()

    def closeDock(self):
        if self.dock:
            print("closeDock: Closing dock")
            self.dock.close()

    def disconnectProjectSignals(self):
        print("disconnectProjectSignals: Disconnecting project signals")
        project = QgsProject.instance()
        try:
            project.readProject.disconnect(self.deactivate)
            print("disconnectProjectSignals: Disconnected readProject signal")
        except Exception as e:
            print("disconnectProjectSignals: Exception disconnecting readProject:", e)
        try:
            project.cleared.disconnect(self.deactivate)
            print("disconnectProjectSignals: Disconnected cleared signal")
        except Exception as e:
            print("disconnectProjectSignals: Exception disconnecting cleared:", e)

    def setActionUnchecked(self):
        if self.toggle_action:
            print("setActionUnchecked: Unchecking toggle action")
            self.toggle_action.setChecked(False)

    def setupConnections(self):
        print("setupConnections: Setting up project connections")
        project = QgsProject.instance()
        project.readProject.connect(self.deactivate)
        project.cleared.connect(self.deactivate)

    # -----------------------
    # Event Handlers
    # -----------------------
    def canvasReleaseEvent(self, event):
        print("canvasReleaseEvent: Mouse released at", event.x(), event.y())
        if self.ignoreNextRelease:
            print("canvasReleaseEvent: Ignoring release due to flag")
            self.ignoreNextRelease = False
            return

        all_features = self.identify(event.x(), event.y(), self.TopDownAll)
        print("canvasReleaseEvent: Found", len(all_features), "features")
        if not all_features:
            return

        selected_layer, selected_feature, selected_handler = self.getFeatureByPriority(all_features)

        self.clearSelections()
        self.selectFeature(selected_layer, selected_feature)
        self.highlightFeature(selected_layer, selected_feature)
        self.showFeatureInDock(selected_layer, selected_feature, selected_handler)

    def canvasDoubleClickEvent(self, event):
        print("canvasDoubleClickEvent: Mouse double-clicked at", event.x(), event.y())
        self.ignoreNextRelease = True

        all_features = self.identify(event.x(), event.y(), self.TopDownAll)
        print("canvasDoubleClickEvent: Found", len(all_features), "features")
        if not all_features:
            return

        sorted_results = self.getSortedFeatures(all_features)
        if len(sorted_results) < 2:
            print("canvasDoubleClickEvent: Less than 2 features found, using single click logic")
            self.canvasReleaseEvent(event)
            return

        second_result = sorted_results[1][1]
        selected_feature = second_result.mFeature
        selected_layer = second_result.mLayer

        handlers = self.getHandlers()
        identifier = selected_layer.customProperty("qgisred_identifier")
        selected_handler = handlers.get(identifier, None)
    
        self.clearSelections()
        self.selectFeature(selected_layer, selected_feature)
        self.highlightFeature(selected_layer, selected_feature)
        self.showFeatureInDock(selected_layer, selected_feature, selected_handler)

    def deactivate(self):
        print("deactivate: Deactivating identify feature tool")
        self.clearHighlights()
        self.disconnectProjectSignals()
        self.setActionUnchecked()

        QgsMapToolIdentify.deactivate(self)

    def keyReleaseEvent(self, e):
        print("keyReleaseEvent: Key released:", e.key())
        if e.key() == Qt.Key_Escape:
            print("keyReleaseEvent: Escape key detected; deactivating tool")
            self.deactivate()

    def setUseElementProperties(self, value):
        # print("setUseElementProperties: Setting useElementPropertiesDock to", value)
        # self.elementPropertiesDockVisibilityChanged.emit(value)
        self.useElementPropertiesDock = value

    def setFindElementsVisibility(self, value):
        self.findElementsDockVisibilityChanged.emit(value)

    def setElementPropertiesVisibility(self, value):
        self.elementPropertiesDockVisibilityChanged.emit(value)
    