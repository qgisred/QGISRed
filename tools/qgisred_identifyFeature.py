from ..ui.qgisred_elementproperties_dock import QGISRedElementsPropertyDock
from qgis.gui import QgsMapToolIdentify, QgsHighlight
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtCore import Qt


class QGISRedIdentifyFeature(QgsMapToolIdentify):
    def __init__(self, canvas, toggle_action=None):
        super().__init__(canvas)
        self.canvas = canvas
        self.toggle_action = toggle_action
        self.currentHighlight = None
        self.dock = None
        self.setupConnections()

    def clearHighlights(self):
        if self.currentHighlight is not None:
            self.currentHighlight.hide()
            self.currentHighlight = None

    def closeDock(self):
        if self.dock:
            self.dock.close()

    def disconnectProjectSignals(self):
        project = QgsProject.instance()
        try:
            project.readProject.disconnect(self.deactivate)
        except Exception:
            pass
        try:
            project.cleared.disconnect(self.deactivate)
        except Exception:
            pass

    def setActionUnchecked(self):
        if self.toggle_action:
            self.toggle_action.setChecked(False)

    def setupConnections(self):
        project = QgsProject.instance()
        project.readProject.connect(self.deactivate)
        project.cleared.connect(self.deactivate)

    def canvasReleaseEvent(self, event):
        all_features = self.identify(event.x(), event.y(), self.TopDownAll)
        if not all_features:
            return

        handlers = {
            'qgisred_meters': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleMeters'),
            'qgisred_isolationvalves': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleIsolationValves'),
            'qgisred_valves': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleValves'),
            'qgisred_pumps': (['tabData', 'tabResults', 'tabCurves', 'tabPatterns', 'tabControls'], 'handlePumps'),
            'qgisred_junctions': (['tabData', 'tabResults', 'tabPatterns', 'tabControls'], 'handleJunctions'),
            'qgisred_tanks': (['tabData', 'tabResults', 'tabCurves', 'tabPatterns', 'tabControls'], 'handleTanks'),
            'qgisred_reservoirs': (['tabData', 'tabResults', 'tabPatterns', 'tabControls'], 'handleReservoirs'),
            'qgisred_pipes': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handlePipes'),
            'qgisred_serviceconnections': (['tabData', 'tabResults', 'tabCurves', 'tabControls'], 'handleServiceConnections')
        }

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

        if not selected_handler:
            top_result = all_features[0]
            selected_feature = top_result.mFeature
            selected_layer = top_result.mLayer

        for lyr in QgsProject.instance().mapLayers().values():
            if isinstance(lyr, QgsVectorLayer):
                lyr.removeSelection()
        selected_layer.select(selected_feature.id())

        self.clearHighlights()
        self.currentHighlight = QgsHighlight(self.canvas, selected_feature.geometry(), selected_layer)
        self.currentHighlight.setColor(Qt.red)
        self.currentHighlight.setWidth(4)
        self.currentHighlight.setFillColor(Qt.transparent)
        self.currentHighlight.show()

        self.dock = QGISRedElementsPropertyDock.getInstance(iface.mainWindow())
        if not self.dock.isVisible():
            iface.addDockWidget(Qt.RightDockWidgetArea, self.dock)

        if selected_handler:
            tabs, method_name = selected_handler
            getattr(self.dock, method_name)(selected_layer, selected_feature, tabs)
        else:
            self.dock.loadFeature(selected_layer, selected_feature)

        self.dock.show()
        self.dock.raise_()
        self.dock.activateWindow()

    def deactivate(self):
        self.canvas.unsetMapTool(self.canvas.mapTool())
        self.clearHighlights()
        self.closeDock()
        self.disconnectProjectSignals()
        self.setActionUnchecked()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.deactivate()
