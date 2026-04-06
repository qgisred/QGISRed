# -*- coding: utf-8 -*-
"""Queries and exploration section for QGISRed."""

from qgis.PyQt.QtCore import Qt

from ..ui.queries.qgisred_thematicmaps_dialog import QGISRedThematicMapsDialog
from ..ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from ..ui.queries.qgisred_queriesbyproperties_dock import QGISRedQueriesByPropertiesDock
from ..ui.queries.qgisred_statisticsandgraphs_dock import QGISRedStatisticsAndPlotsDock
from ..tools.map_tools.qgisred_identifyFeature import QGISRedIdentifyFeature


class QueriesSection:
    """Thematic maps, element explorer, queries by attributes, statistics, legends."""

    def isToolAlreadyActive(self, toolKey, action):
        # Returns True if toolKey is already the active map tool, keeping the action checked
        if toolKey in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[toolKey]:
            action.setChecked(True)
            return True
        return False

    def switchToIdentifyTool(self, toolKey, action, useElementPropertiesDock, dock):
        # Cleans up old tool, creates a new QGISRedIdentifyFeature, and re-highlights on the dock
        try:
            oldTool = self.myMapTools.get(toolKey)
            if oldTool:
                oldTool.disconnectDockSignals()
                oldTool.disconnectProjectSignals()
                oldTool.removeVertexMarkers()

            self.myMapTools[toolKey] = QGISRedIdentifyFeature(
                self.iface.mapCanvas(),
                action,
                useElementPropertiesDock=useElementPropertiesDock,
                dock=dock,
                cursor=action.icon().pixmap(24, 24)
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[toolKey])
            if dock:
                dock.reHighlightCurrentElement()
                dock.refreshCurrentElement()
        except Exception:
            action.setChecked(False)

    def connectElementExplorerToResultsDock(self):
        """Connect the Element Explorer results tab to the Results Dock."""
        eeDock = QGISRedElementExplorerDock._instance
        if eeDock is not None and self.ResultDockwidget is not None:
            eeDock.connectResultsDock(self.ResultDockwidget)

    def disconnectElementExplorerFromResultsDock(self):
        """Disconnect the Element Explorer results tab from the Results Dock."""
        eeDock = QGISRedElementExplorerDock._instance
        if eeDock is not None:
            eeDock.disconnectResultsDock()

    """Main methods"""
    def runThematicMaps(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        dlg = QGISRedThematicMapsDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        dlg.exec()

    def runFindElements(self):
        if not self.validateProject(self.openFindElementsDialog):
            return

        existingDock = QGISRedElementExplorerDock._instance

        # Unset map tool if it was one of the search tools, as this button doesn't use tools
        currentTool = self.iface.mapCanvas().mapTool()
        if currentTool and type(currentTool).__name__ == "QGISRedIdentifyFeature":
            self.iface.mapCanvas().unsetMapTool(currentTool)

        if existingDock:
            existingDock.show()
            existingDock.raise_()
            existingDock.activateWindow()
            # Expand Find Elements and ensure it's visible
            existingDock.updateCollapsibleWidgetsState(collapseFindElements=False)
            existingDock.scrollToTop()
            dock = existingDock
        else:
            try:
                dock = QGISRedElementExplorerDock.getInstance(
                    self.iface.mapCanvas(),
                    self.iface.mainWindow(),
                    showFindElements=True,
                    showElementProperties=False
                )

                self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
                dock.show()
                dock.raise_()
                dock.activateWindow()
                dock.onLayerTreeChanged()
                dock.setDefaultValue()
                dock.updateCollapsibleWidgetsState(collapseFindElements=False, collapseConnectedElements=True)
            except Exception:
                self.openFindElementsDialog.setChecked(False)
                return

        self.connectElementExplorerToResultsDock()
        self.openFindElementsDialog.setChecked(False) # Not a tool, don't keep it checked

    def runElementsProperty(self):
        if not self.validateProject(self.openElementsPropertyDialog):
            return

        existingDock = QGISRedElementExplorerDock._instance

        tool = "identifyFeatureElementProperties"
        if self.isToolAlreadyActive(tool, self.openElementsPropertyDialog):
            self.openElementsPropertyDialog.setChecked(False)
            currentTool = self.iface.mapCanvas().mapTool()
            if currentTool:
                self.iface.mapCanvas().unsetMapTool(currentTool)
            return

        if existingDock:
            existingDock.show()
            existingDock.raise_()
            existingDock.activateWindow()
            existingDock.updateCollapsibleWidgetsState(collapseElementProperties=False, collapseFindElements=True)
            existingDock.scrollToElementProperties()
            dock = existingDock
        else:
            try:
                dock = QGISRedElementExplorerDock.getInstance(
                    self.iface.mapCanvas(),
                    self.iface.mainWindow(),
                    showFindElements=True,
                    showElementProperties=True
                )
                self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
                dock.show()
                dock.raise_()
                dock.activateWindow()
                dock.onLayerTreeChanged()
                dock.setDefaultValue()
                dock.updateCollapsibleWidgetsState(collapseElementProperties=False, collapseFindElements=True)
            except Exception:
                self.openElementsPropertyDialog.setChecked(False)
                return

        self.connectElementExplorerToResultsDock()
        self.switchToIdentifyTool(tool, self.openElementsPropertyDialog, True, dock)

    def runQueriesByProperties(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.queriesByPropertiesDock = QGISRedQueriesByPropertiesDock(self.iface)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.queriesByPropertiesDock)

    def runStatisticsAndPlots(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.statisticsAndPlotsDock = QGISRedStatisticsAndPlotsDock(self.iface)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.statisticsAndPlotsDock)
