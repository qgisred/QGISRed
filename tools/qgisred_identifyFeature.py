from ..ui.qgisred_unified_find_properties import QGISRedElementsExplorerDock
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QCursor, QPixmap
from qgis.core import QgsPointXY, QgsProject, QgsSnappingConfig, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMapCanvasSnappingUtils



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
        self.setupConnections()

        self.startMarker = QgsVertexMarker(self.canvas)
        self.startMarker.setColor(QColor(255, 87, 51))
        self.startMarker.setIconSize(15)
        self.startMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE)  # or ICON_CROSS, ICON_X
        self.startMarker.setPenWidth(3)
        self.startMarker.hide()

        self.endMarker = QgsVertexMarker(self.canvas)
        self.endMarker.setColor(QColor(0, 128, 0))
        self.endMarker.setIconSize(15)
        self.endMarker.setIconType(QgsVertexMarker.ICON_TRIANGLE)  # or ICON_CROSS, ICON_X
        self.endMarker.setPenWidth(3)
        self.endMarker.hide()
        self.firstPoint = None

        self.snapper = None
        self.resetProperties()

    def resetProperties(self):
        self.firstPoint = None
        self.startMarker.hide()
        self.endMarker.hide()
        self.objectSnapped = None

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
        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()

    def highlightFeature(self, layer, feature):
        self.clearHighlights()
        self.currentHighlight = QgsHighlight(self.canvas, feature.geometry(), layer)
        self.currentHighlight.setColor(Qt.red)
        self.currentHighlight.setWidth(4)
        self.currentHighlight.setFillColor(Qt.transparent)
        self.currentHighlight.show()
    
    def showFeatureInDock(self, layer, feature, handler=None):
        self.dock = QGISRedElementsExplorerDock.getInstance(
            self.canvas, 
            iface.mainWindow(),
            show_find_elements=True,
            show_element_properties=True
        )

        if self.dock is None:
            return
        
        if not self.dock.isVisible():
            iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)
            self.dock.show()
            self.dock.raise_()
            self.dock.activateWindow()

        self.dock.findFeature(layer, feature)

    def activate(self):
        QgsMapTool.activate(self)
        self.configSnapper()

    def setIdentifyFeatureAsMapTool(self):
        self.canvas.setMapTool(self)

    def selectFeature(self, layer, feature):
        layer.select(feature.id())

    def getFeatureByPriority(self, all_features):
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
                    break
            if selected_handler:
                break

        if not selected_handler and all_features:
            top_result = all_features[0]
            selected_feature = top_result.mFeature
            selected_layer = top_result.mLayer

        return selected_layer, selected_feature, selected_handler

    def getSortedFeatures(self, all_features):
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
        return sorted_results


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

    def closeDock(self):
        if self.dock:
            self.dock.close()

    def disconnectProjectSignals(self):
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
            self.toggle_action.setChecked(False)

    def setupConnections(self):
        project = QgsProject.instance()
        project.readProject.connect(self.deactivate)
        project.cleared.connect(self.deactivate)

    def canvasReleaseEvent(self, event):
        if self.ignoreNextRelease:
            self.ignoreNextRelease = False
            return

        all_features = self.identify(event.x(), event.y(), self.TopDownAll)
        if not all_features:
            return

        selected_layer, selected_feature, selected_handler = self.getFeatureByPriority(all_features)

        self.clearSelections()
        self.selectFeature(selected_layer, selected_feature)
        self.highlightFeature(selected_layer, selected_feature)
        self.showFeatureInDock(selected_layer, selected_feature, selected_handler)
        #self.resetProperties()

    def canvasDoubleClickEvent(self, event):
        self.ignoreNextRelease = True

        all_features = self.identify(event.x(), event.y(), self.TopDownAll)
        if not all_features:
            return

        sorted_results = self.getSortedFeatures(all_features)
        if len(sorted_results) < 2:
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
        self.clearHighlights()
        self.disconnectProjectSignals()
        self.setActionUnchecked()

        QgsMapToolIdentify.deactivate(self)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.deactivate()
    
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
