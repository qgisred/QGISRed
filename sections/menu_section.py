# -*- coding: utf-8 -*-
"""Menu section for QGISRed (build all toolbars/menus, toolbar visibility toggles, about/report)."""

import webbrowser

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMenu, QToolButton

from ..ui.general.qgisred_about_dialog import QGISRedAboutDialog


class MenuSection:
    """Build all QGISRed menus and toolbars.

    This section creates the following ``self.*Button`` / ``self.*DropButton`` attributes used
    by other sections:

    NetworkEditingSection:
        addPipeButton, addTankButton, addReservoirButton, insertValveButton, insertPumpButton,
        selectElementsButton, moveElementsButton, moveVertexsButton, reverseLinkButton,
        splitPipeButton, mergeSplitJunctionButton, createReverseTconButton, createReverseCrossButton,
        moveValvePumpButton, changeStatusButton, removeElementsButton, editElementButton,
        editDropButton

    DigitalTwinSection:
        addServConnButton, addIsolationValveButton, addMeterDropButton,
        addAutoMeterButton, addManometerButton, addFlowmeterButton, addCountermeterButton,
        addLevelSensorButton, addDifferentialManometerButton, addQualitySensorButton,
        addEnergySensorButton, addStatusSensorButton, addValveOpeningButton, addTachometerButton,
        dtDropButton, meterSubMenu, meterSubMenuToolbar, currentMeter

    AnalysisSection:
        timeSeriesButton, analysisDropButton

    ToolsSection:
        isolatedSegmentsButton

    QueriesSection:
        openFindElementsDialog, openElementsPropertyDialog, openThematicMapsDialog,
        openLiveQueriesDialog, openStatisticsAndPlotsDialog

    ProjectManagementSection / LayerManagementSection:
        unitsAction (set in addProjectMenu via setUnits)

    General drop buttons:
        generalDropButton, projectDropButton, debugDropButton, toolsDropButton,
        analysisDropButton, dtDropButton, queriesDropButton
    """

    def addGeneralMenu(self):
        #    #Menu
        self.generalMenu = self.qgisredmenu.addMenu(self.tr("General"))
        self.generalMenu.setIcon(QIcon(":/images/iconGeneralMenu.svg"))
        #    #Toolbar
        self.generalToolbar = self.iface.addToolBar(self.tr("QGISRed General"))
        self.generalToolbar.setObjectName(self.tr("QGISRed General"))
        self.generalToolbar.setVisible(False)
        #    #Buttons
        generalDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconGeneralMenu.svg", 
            self.tr("General"), 
            self.runGeneralToolbar,
            checkable=True, parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, generalDropButton, self.toolbar)
        self.generalDropButton = generalDropButton
        self.generalToolbar.visibilityChanged.connect(self.changeGeneralToolbarVisibility)

        action = self._make_action(
            ":/images/iconProjectManager.svg", 
            self.tr("Project manager..."), 
            self.runProjectManager,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.generalMenu, self.generalToolbar)
        self.add_to_dropdown(action, generalDropButton)

        action = self._make_action(
            ":/images/iconOpenProject.svg", 
            self.tr("Open project..."), 
            self.runCanOpenProject,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.generalMenu, self.generalToolbar)
        self.add_to_dropdown(action, generalDropButton)

        action = self._make_action(
            ":/images/iconCreateProject.svg", 
            self.tr("Create project..."), 
            self.runCanCreateProject,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.generalMenu, self.generalToolbar)
        self.add_to_dropdown(action, generalDropButton)

        action = self._make_action(
            ":/images/iconImportProject.svg", 
            self.tr("Import project..."), 
            self.runCanImportData,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.generalMenu, self.generalToolbar)
        self.add_to_dropdown(action, generalDropButton)

    def addProjectMenu(self):
        #    #Menu
        self.projectMenu = self.qgisredmenu.addMenu(self.tr("Project"))
        self.projectMenu.setIcon(QIcon(":/images/iconProjectMenu.svg"))
        #    #Toolbar
        self.projectToolbar = self.iface.addToolBar(self.tr("QGISRed Project"))
        self.projectToolbar.setObjectName(self.tr("QGISRed Project"))
        self.projectToolbar.setVisible(False)
        #    #Buttons
        projectDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconProjectMenu.svg", 
            self.tr("Project"), 
            self.runProjectToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, projectDropButton, self.toolbar)
        self.projectDropButton = projectDropButton
        self.projectToolbar.visibilityChanged.connect(self.changeProjectToolbarVisibility)

        action = self._make_action(
            ":/images/iconSummary.svg", 
            self.tr("Summary..."), 
            self.runSummary,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconAddData.svg", 
            self.tr("Add data by import..."), 
            self.runCanAddData,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconLayerManagement.svg", 
            self.tr("Layer manager..."), 
            self.runLayerManagement,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconThematicMaps.svg", 
            self.tr("Legend editor..."), 
            self.runLegends,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        projectDropButton.menu().addSeparator()
        self.projectToolbar.addSeparator()
        self.projectMenu.addSeparator()

        action = self._make_action(
            ":/images/iconProjectSettings.svg", 
            self.tr("Project settings..."), 
            self.runSettings,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconDefaultValues.svg", 
            self.tr("Default values..."), 
            self.runDefaultValues,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconMaterials.svg", 
            self.tr("Materials table..."), 
            self.runMaterials,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        projectDropButton.menu().addSeparator()
        self.projectToolbar.addSeparator()
        self.projectMenu.addSeparator()

        action = self._make_action(
            ":/images/iconSaveProject.svg", 
            self.tr("Save project map"), 
            self.runSaveActionProject,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconBackUpProject.svg", 
            self.tr("Project backup"), 
            self.runCreateBackup,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

        action = self._make_action(
            ":/images/iconCloseProject.svg", 
            self.tr("Close project"), 
            self.runCloseProject,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.projectMenu, self.projectToolbar)
        self.add_to_dropdown(action, projectDropButton)

    def addEditMenu(self):
        #    #Menu
        self.editionMenu = self.qgisredmenu.addMenu(self.tr("Edition"))
        self.editionMenu.setIcon(QIcon(":/images/iconEditMenu.svg"))
        #    #Toolbar
        self.editionToolbar = self.iface.addToolBar(self.tr("QGISRed Edition"))
        self.editionToolbar.setObjectName(self.tr("QGISRed Edition"))
        self.editionToolbar.setVisible(False)

        #    #Buttons
        editDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconEditMenu.svg", 
            self.tr("Edition"), 
            self.runEditionToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, editDropButton, self.toolbar)
        self.editDropButton = editDropButton
        self.editionToolbar.visibilityChanged.connect(self.changeEditionToolbarVisibility)

        self.addPipeButton = self._make_action(
            ":/images/iconAddPipe.svg", self.tr("Add pipe"), self.runPaintPipe,
            checkable=True, parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addPipeButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.addPipeButton, editDropButton)

        self.addTankButton = self._make_action(
            ":/images/iconAddTank.svg", 
            self.tr("Add tank"), 
            self.runSelectTankPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addTankButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.addTankButton, editDropButton)

        self.addReservoirButton = self._make_action(
            ":/images/iconAddReservoir.svg", 
            self.tr("Add reservoir"), 
            self.runSelectReservoirPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addReservoirButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.addReservoirButton, editDropButton)

        self.insertValveButton = self._make_action(
            ":/images/iconAddValve.svg", 
            self.tr("Insert valve in pipe"), 
            self.runSelectValvePoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.insertValveButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.insertValveButton, editDropButton)

        self.insertPumpButton = self._make_action(
            ":/images/iconAddPump.svg", 
            self.tr("Insert pump in pipe"), 
            self.runSelectPumpPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.insertPumpButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.insertPumpButton, editDropButton)

        editDropButton.menu().addSeparator()
        self.editionToolbar.addSeparator()
        self.editionMenu.addSeparator()

        self.selectElementsButton = self._make_action(
            ":/images/iconMultipleSelection.svg", 
            self.tr("Select multiple elements"), 
            self.runSelectElements,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.selectElementsButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.selectElementsButton, editDropButton)

        self.moveElementsButton = self._make_action(
            ":/images/iconMoveNodes.svg", 
            self.tr("Move nodes"), 
            self.runMoveElements,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.moveElementsButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.moveElementsButton, editDropButton)

        self.moveVertexsButton = self._make_action(
            ":/images/iconEditVertices.svg", 
            self.tr("Edit link vertices"), 
            self.runEditLinkGeometry,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.moveVertexsButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.moveVertexsButton, editDropButton)

        self.reverseLinkButton = self._make_action(
            ":/images/iconReverseElements.svg", 
            self.tr("Reverse elements"), 
            self.canReverseLink,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.reverseLinkButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.reverseLinkButton, editDropButton)

        self.splitPipeButton = self._make_action(
            ":/images/iconSplitJoinPipes.svg", 
            self.tr("Split/Join pipes"), 
            self.runSelectSplitPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.splitPipeButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.splitPipeButton, editDropButton)

        self.mergeSplitJunctionButton = self._make_action(
            ":/images/iconMergeSplitJunctions.svg", 
            self.tr("Merge/Dissolve junctions"), 
            self.runSelectPointToMergeSplit,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.mergeSplitJunctionButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.mergeSplitJunctionButton, editDropButton)

        self.createReverseTconButton = self._make_action(
            ":/images/iconCreateRemoveTConnections.svg", 
            self.tr("Create/Remove T connections"), 
            self.runSelectPointToTconnections,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.createReverseTconButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.createReverseTconButton, editDropButton)

        self.createReverseCrossButton = self._make_action(
            ":/images/iconCreateRemoveCrossings.svg", 
            self.tr("Create/Remove crossings"), 
            self.runSelectPointToCrossings,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.createReverseCrossButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.createReverseCrossButton, editDropButton)

        self.moveValvePumpButton = self._make_action(
            ":/images/iconMoveElements.svg", 
            self.tr("Move valves/pumps"), 
            self.runSelectValvePumpPoints,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.moveValvePumpButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.moveValvePumpButton, editDropButton)

        self.changeStatusButton = self._make_action(
            ":/images/iconChangeStatus.svg", 
            self.tr("Change element status"), 
            self.runSelectElementStatusPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.changeStatusButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.changeStatusButton, editDropButton)

        self.removeElementsButton = self._make_action(
            ":/images/iconDeleteElements.svg", 
            self.tr("Delete elements"), 
            self.canDeleteElements,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.removeElementsButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.removeElementsButton, editDropButton)

        editDropButton.menu().addSeparator()
        self.editionToolbar.addSeparator()
        self.editionMenu.addSeparator()

        self.editElementButton = self._make_action(
            ":/images/iconEditMenu.svg", 
            self.tr("Edit element properties..."), 
            self.runSelectPointProperties,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.editElementButton, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(self.editElementButton, editDropButton)

        action = self._make_action(
            ":/images/iconPatternsAndCurves.svg", 
            self.tr("Edit patterns and curves..."), 
            self.runPatternsCurves,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(action, editDropButton)

        action = self._make_action(
            ":/images/iconControlsAndRules.svg", 
            self.tr("Edit controls..."), 
            self.runControls,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.editionMenu, self.editionToolbar)
        self.add_to_dropdown(action, editDropButton)

    def addDebugMenu(self):
        #    #Menu
        self.debugMenu = self.qgisredmenu.addMenu(self.tr("Debug"))
        self.debugMenu.setIcon(QIcon(":/images/iconDebugMenu.svg"))
        #    #Toolbar
        self.debugToolbar = self.iface.addToolBar(self.tr("QGISRed Debug"))
        self.debugToolbar.setObjectName(self.tr("QGISRed Debug"))
        self.debugToolbar.setVisible(False)
        #    #Buttons
        debugDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconDebugMenu.svg", 
            self.tr("Debug"), 
            self.runDebugToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, debugDropButton, self.toolbar)
        self.debugDropButton = debugDropButton
        self.debugToolbar.visibilityChanged.connect(self.changeDebugToolbarVisibility)

        action = self._make_action(
            ":/images/iconDebugMenu.svg", 
            self.tr("Check && commit data"), 
            self.runCommit,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconRemoveOverlappings.svg", 
            self.tr("Remove overlapping elements"), 
            self.runCheckOverlappingElements,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconSimplifyVertices.svg", 
            self.tr("Simplify link vertices"), 
            self.runSimplifyVertices,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconJoinPipes.svg", 
            self.tr("Join consecutive pipes (= diameter, material and year)"), 
            self.runCheckJoinPipes,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconCreateTConnections.svg", 
            self.tr("Create T connections"), 
            self.runCheckTConncetions,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        # Connectivity sub-dropdown
        dropButton = QToolButton()
        action = self._make_action(
            ":/images/iconCheckConnectivity.svg", 
            self.tr("Check connectivity"), 
            self.runCheckConnectivityM,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu)
        self.add_to_dropdown(action, debugDropButton)
        self.setup_dropdown_button(action, dropButton, self.debugToolbar)
        self.add_to_dropdown(action, dropButton)

        action = self._make_action(
            ":/images/iconDeleteIsolatedAreas.svg", 
            self.tr("Delete issolated subzones"), 
            self.runCheckConnectivityC,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu)
        self.add_to_dropdown(action, dropButton)

        debugDropButton.menu().addSeparator()
        self.debugToolbar.addSeparator()
        self.debugMenu.addSeparator()

        action = self._make_action(
            ":/images/iconCheckPipeLengths.svg", 
            self.tr("Check pipe lengths"), 
            self.runCheckLengths,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconCheckDiameters.svg", 
            self.tr("Check diameters"), 
            self.runCheckDiameters,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconCheckMaterials.svg", 
            self.tr("Check pipe materials"), 
            self.runCheckMaterials,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        action = self._make_action(
            ":/images/iconCheckInstalationDates.svg", 
            self.tr("Check pipe installation dates"), 
            self.runCheckInstallationDates,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

        debugDropButton.menu().addSeparator()
        self.debugToolbar.addSeparator()
        self.debugMenu.addSeparator()

        action = self._make_action(
            ":/images/iconCheckHydraulicSectors.svg", 
            self.tr("Check hydraulic sectors"), 
            self.runHydraulicSectors,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.debugMenu, self.debugToolbar)
        self.add_to_dropdown(action, debugDropButton)

    def addToolsMenu(self):
        #    #Menu
        self.toolsMenu = self.qgisredmenu.addMenu(self.tr("Tools"))
        self.toolsMenu.setIcon(QIcon(":/images/iconToolsMenu.svg"))
        #    #Toolbar
        self.toolsToolbar = self.iface.addToolBar(self.tr("QGISRed Tools"))
        self.toolsToolbar.setObjectName(self.tr("QGISRed Tools"))
        self.toolsToolbar.setVisible(False)
        #    #Buttons
        toolDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconToolsMenu.svg", 
            self.tr("Tools"), 
            self.runToolsToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, toolDropButton, self.toolbar)
        self.toolsDropButton = toolDropButton
        self.toolsToolbar.visibilityChanged.connect(self.changeToolsToolbarVisibility)

        action = self._make_action(
            ":/images/iconCalculatePipeLengths.svg", 
            self.tr("Automatically calculate pipe lengths"), 
            self.runCalculateLengths,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        action = self._make_action(
            ":/images/iconInterpolateNodeElevations.svg", 
            self.tr("Interpolate elevation from .asc files..."), 
            self.runElevationInterpolation,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        action = self._make_action(
            ":/images/iconSetRoughnessFromMaterialDate.svg", 
            self.tr("Set roughness coefficients (from Material and Date)"), 
            self.runSetRoughness,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        action = self._make_action(
            ":/images/iconConvertRoughnessCoeff.svg", 
            self.tr("Convert roughness coefficients..."), 
            self.runConvertRoughness,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        toolDropButton.menu().addSeparator()
        self.toolsToolbar.addSeparator()
        self.toolsMenu.addSeparator()

        action = self._make_action(
            ":/images/iconDemandBuilder.svg", 
            self.tr("Nodal demand builder..."), 
            self.runDemandsManager,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        action = self._make_action(
            ":/images/iconScenarioBuilder.svg", 
            self.tr("Scenario builder..."), 
            self.runScenarioManager,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        self.isolatedSegmentsButton = self._make_action(
            ":/images/iconIsolatedSegments.svg", 
            self.tr("Isolated segments..."), 
            self.runIsolatedSegments,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.isolatedSegmentsButton, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(self.isolatedSegmentsButton, toolDropButton)

        toolDropButton.menu().addSeparator()
        self.toolsToolbar.addSeparator()
        self.toolsMenu.addSeparator()

        action = self._make_action(
            ":/images/iconDemandSectors.svg", 
            self.tr("Obtain demand sectors"), 
            self.runDemandSectors,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

        action = self._make_action(
            ":/images/iconGraphTree.svg", 
            self.tr("Minimum Cost Tree..."), 
            self.runTree,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.toolsMenu, self.toolsToolbar)
        self.add_to_dropdown(action, toolDropButton)

    def addAnalysisMenu(self):
        #    #Menu
        self.analysisMenu = self.qgisredmenu.addMenu(self.tr("Analysis"))
        self.analysisMenu.setIcon(QIcon(":/images/iconAnalysisMenu.svg"))
        #    #Toolbar
        self.analysisToolbar = self.iface.addToolBar(self.tr("QGISRed Analysis"))
        self.analysisToolbar.setObjectName(self.tr("QGISRed Analysis"))
        self.analysisToolbar.setVisible(False)
        #    #Buttons
        analysisDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconAnalysisMenu.svg", 
            self.tr("Analysis"), 
            self.runAnalysisToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, analysisDropButton, self.toolbar)
        self.analysisDropButton = analysisDropButton
        self.analysisToolbar.visibilityChanged.connect(self.changeAnalysisToolbarVisibility)

        # Run model sub-dropdown (groups Run model / Results browser / Status report)
        dropButton = QToolButton()
        action = self._make_action(
            ":/images/iconAnalysisMenu.svg", 
            self.tr("Run model"), 
            self.runModel,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu)
        self.add_to_dropdown(action, analysisDropButton)
        self.setup_dropdown_button(action, dropButton, self.analysisToolbar)
        self.add_to_dropdown(action, dropButton)

        action = self._make_action(
            ":/images/iconResultsBrowser.svg", 
            self.tr("Results browser"), 
            self.runShowResultsDock,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu)
        self.add_to_dropdown(action, dropButton)
        self.add_to_dropdown(action, analysisDropButton)

        action = self._make_action(
            ":/images/iconAnalysisMenu.svg", 
            self.tr("Status report"), 
            self.runOpenStatusReport,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu)
        self.add_to_dropdown(action, dropButton)
        self.add_to_dropdown(action, analysisDropButton)

        action = self._make_action(
            ":/images/iconAnalysisOptions.svg", 
            self.tr("Analysis options..."), 
            self.runAnalysisOptions,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu, self.analysisToolbar)
        self.add_to_dropdown(action, analysisDropButton)

        analysisDropButton.menu().addSeparator()
        self.analysisToolbar.addSeparator()
        self.analysisMenu.addSeparator()

        self.timeSeriesButton = self._make_action(
            ":/images/iconTimeSeries.svg", 
            self.tr("Time series..."), 
            self.runTimeSeries,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.timeSeriesButton, self.analysisMenu, self.analysisToolbar)
        self.add_to_dropdown(self.timeSeriesButton, analysisDropButton)

        analysisDropButton.menu().addSeparator()
        self.analysisToolbar.addSeparator()
        self.analysisMenu.addSeparator()

        action = self._make_action(
            ":/images/iconExportResultsToCsv.svg",
            self.tr("Export results to CSV..."),
            self.runExportResultsToCsv,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu, self.analysisToolbar)
        self.add_to_dropdown(action, analysisDropButton)

        action = self._make_action(
            ":/images/iconExportToEpanet.svg", 
            self.tr("Export model to INP..."), 
            self.runExportInp,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.analysisMenu, self.analysisToolbar)
        self.add_to_dropdown(action, analysisDropButton)    

    def addDigitalTwinMenu(self):
        #    #Menu
        self.dtMenu = self.qgisredmenu.addMenu(self.tr("Digital Twin"))
        self.dtMenu.setIcon(QIcon(":/images/iconDigitalTwinMenu.svg"))
        #    #Toolbar
        self.dtToolbar = self.iface.addToolBar(self.tr("QGISRed Digital Twin"))
        self.dtToolbar.setObjectName(self.tr("QGISRed Digital Twin"))
        self.dtToolbar.setVisible(False)
        #    #Buttons
        dtDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconDigitalTwinMenu.svg", 
            self.tr("Digital Twin"), 
            self.runDtToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, dtDropButton, self.toolbar)
        self.dtDropButton = dtDropButton
        self.dtToolbar.visibilityChanged.connect(self.changeDtToolbarVisibility)

        self.addServConnButton = self._make_action(
            ":/images/iconAddConnection.svg", 
            self.tr("Add service connection"), 
            self.runPaintServiceConnection,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addServConnButton, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(self.addServConnButton, dtDropButton)

        self.addIsolationValveButton = self._make_action(
            ":/images/iconAddIsolationValve.svg", 
            self.tr("Add isolation valve"), 
            self.runSelectIsolationValvePoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addIsolationValveButton, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(self.addIsolationValveButton, dtDropButton)

        # Create submenu for the main menu
        self.meterSubMenu = self.dtMenu.addMenu(self.tr("Add meter"))
        self.meterSubMenu.setIcon(QIcon(":/images/iconAddDefaultMeter.svg"))

        # Create a separate submenu for the toolbar dropdown
        self.meterSubMenuToolbar = QMenu(self.tr("Add meter"), self.iface.mainWindow())
        act_toolbar_meter = self.dtDropButton.menu().addMenu(self.meterSubMenuToolbar)
        act_toolbar_meter.setIcon(QIcon(":/images/iconAddDefaultMeter.svg"))

        self.currentMeter = "Undefined"
        self.addMeterDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconAddDefaultMeter.svg", 
            self.tr("Add meter"), 
            self.runSelectDefaultMeterPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, self.addMeterDropButton, self.dtToolbar)

        self.addAutoMeterButton = self._make_action(
            ":/images/iconAddAutometer.svg", 
            self.tr("Add automatic meter"), 
            self.runSelectAutoMeterPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addAutoMeterButton, self.meterSubMenu)
        self.add_to_dropdown(self.addAutoMeterButton, self.addMeterDropButton)
        self.addMeterDropButton.setDefaultAction(self.addAutoMeterButton)

        self.addManometerButton = self._make_action(
            ":/images/iconAddManometer.svg", 
            self.tr("Add manometer"), 
            self.runSelectManometerPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addManometerButton, self.meterSubMenu)
        self.add_to_dropdown(self.addManometerButton, self.addMeterDropButton)

        self.addFlowmeterButton = self._make_action(
            ":/images/iconAddFlowmeter.svg", 
            self.tr("Add flowmeter"), 
            self.runSelectFlowmeterPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addFlowmeterButton, self.meterSubMenu)
        self.add_to_dropdown(self.addFlowmeterButton, self.addMeterDropButton)

        self.addCountermeterButton = self._make_action(
            ":/images/iconAddCountermeter.svg", 
            self.tr("Add countermeter"), 
            self.runSelectCountermeterPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addCountermeterButton, self.meterSubMenu)
        self.add_to_dropdown(self.addCountermeterButton, self.addMeterDropButton)

        self.addLevelSensorButton = self._make_action(
            ":/images/iconAddLevelSensor.svg", 
            self.tr("Add level sensor"), 
            self.runSelectLevelSensorPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addLevelSensorButton, self.meterSubMenu)
        self.add_to_dropdown(self.addLevelSensorButton, self.addMeterDropButton)

        self.addDifferentialManometerButton = self._make_action(
            ":/images/iconAddDiffManometer.svg", 
            self.tr("Add differential manometer"), 
            self.runSelectDifferentialManometerPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addDifferentialManometerButton, self.meterSubMenu)
        self.add_to_dropdown(self.addDifferentialManometerButton, self.addMeterDropButton)

        self.addQualitySensorButton = self._make_action(
            ":/images/iconAddQualitySensor.svg", 
            self.tr("Add quality sensor"), 
            self.runSelectQualitySensorPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addQualitySensorButton, self.meterSubMenu)
        self.add_to_dropdown(self.addQualitySensorButton, self.addMeterDropButton)

        self.addEnergySensorButton = self._make_action(
            ":/images/iconAddEnergySensor.svg", 
            self.tr("Add energy sensor"), 
            self.runSelectEnergySensorPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addEnergySensorButton, self.meterSubMenu)
        self.add_to_dropdown(self.addEnergySensorButton, self.addMeterDropButton)

        self.addStatusSensorButton = self._make_action(
            ":/images/iconAddStatusSensor.svg", 
            self.tr("Add status sensor"), 
            self.runSelectStatusSensorPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addStatusSensorButton, self.meterSubMenu)
        self.add_to_dropdown(self.addStatusSensorButton, self.addMeterDropButton)

        self.addValveOpeningButton = self._make_action(
            ":/images/iconAddValveOpening.svg", 
            self.tr("Add valve opening"), 
            self.runSelectValveOpeningPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addValveOpeningButton, self.meterSubMenu)
        self.add_to_dropdown(self.addValveOpeningButton, self.addMeterDropButton)

        self.addTachometerButton = self._make_action(
            ":/images/iconAddTachometer.svg", 
            self.tr("Add tachometer"), 
            self.runSelectTachometerPoint,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.addTachometerButton, self.meterSubMenu)
        self.add_to_dropdown(self.addTachometerButton, self.addMeterDropButton)

        # Add all meter actions to the toolbar submenu
        for a in [
            self.addAutoMeterButton,
            self.addManometerButton,
            self.addFlowmeterButton,
            self.addCountermeterButton,
            self.addLevelSensorButton,
            self.addDifferentialManometerButton,
            self.addQualitySensorButton,
            self.addEnergySensorButton,
            self.addStatusSensorButton,
            self.addValveOpeningButton,
            self.addTachometerButton,
        ]:
            self.meterSubMenuToolbar.addAction(a)

        dtDropButton.menu().addSeparator()
        self.dtMenu.addSeparator()
        self.dtToolbar.addSeparator()

        action = self._make_action(
            ":/images/iconLoadMeterReadings.svg", 
            self.tr("Load meter readings..."), 
            self.runLoadReadings,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(action, dtDropButton)

        action = self._make_action(
            ":/images/iconSetPipeStatusFromValves.svg", 
            self.tr("Set pipe's initial status from isolation valves"), 
            self.runSetPipeStatus,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(action, dtDropButton)

        action = self._make_action(
            ":/images/iconLoadFieldData.svg", 
            self.tr("Load field data..."), 
            self.runLoadScada,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(action, dtDropButton)

        dtDropButton.menu().addSeparator()
        self.dtMenu.addSeparator()
        self.dtToolbar.addSeparator()

        action = self._make_action(
            ":/images/iconIncorporateConnectionsToModel.svg", 
            self.tr("Convert service connections into pipes/nodes"), 
            self.runAddConnections,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(action, self.dtMenu, self.dtToolbar)
        self.add_to_dropdown(action, dtDropButton)

    def addQueriesMenu(self):
        #    #Menu
        self.queriesMenu = self.qgisredmenu.addMenu(self.tr("Queries"))
        self.queriesMenu.setIcon(QIcon(":/images/iconQueriesMenu.svg"))
        #    #Toolbar
        self.queriesToolbar = self.iface.addToolBar(self.tr("QGISRed Queries"))
        self.queriesToolbar.setObjectName(self.tr("QGISRed Queries"))
        self.queriesToolbar.setVisible(False)
        #    #Buttons
        queriesDropButton = QToolButton()
        action = self._make_action(
            ":/images/iconQueriesMenu.svg", 
            self.tr("Queries"), 
            self.runQueriesToolbar,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.setup_dropdown_button(action, queriesDropButton, self.toolbar)
        self.queriesDropButton = queriesDropButton
        self.queriesToolbar.visibilityChanged.connect(self.changeQueriesToolbarVisibility)

        self.openFindElementsDialog = self._make_action(
            ":/images/iconFindElements.svg", 
            self.tr("Find elements by ID..."), 
            self.runFindElements,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.openFindElementsDialog, self.queriesMenu, self.queriesToolbar)
        self.add_to_dropdown(self.openFindElementsDialog, queriesDropButton)

        self.openElementsPropertyDialog = self._make_action(
            ":/images/iconElementProperties.svg", 
            self.tr("Element properties..."), 
            self.runElementsProperty,
            checkable=True, 
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.openElementsPropertyDialog, self.queriesMenu, self.queriesToolbar)
        self.add_to_dropdown(self.openElementsPropertyDialog, queriesDropButton)

        self.openThematicMapsDialog = self._make_action(
            ":/images/iconThematicMaps.svg", 
            self.tr("Thematic maps..."), 
            self.runThematicMaps,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.openThematicMapsDialog, self.queriesMenu, self.queriesToolbar)
        self.add_to_dropdown(self.openThematicMapsDialog, queriesDropButton)

        self.openLiveQueriesDialog = self._make_action(
            ":/images/iconQueryByProperties.svg",
            self.tr("Queries by properties..."),
            self.runQueriesByProperties,
            parent=self.iface.mainWindow(),
        )
        self.add_to_group(self.openLiveQueriesDialog, self.queriesMenu, self.queriesToolbar)
        self.add_to_dropdown(self.openLiveQueriesDialog, queriesDropButton)

        # self.openStatisticsAndPlotsDialog = self._make_action(
        #     ":/images/iconStatisticsAndPlots.svg", 
        #     self.tr("Statistics && Plots..."), 
        #     self.runStatisticsAndPlots,
        #     parent=self.iface.mainWindow(),
        # )
        # self.add_to_group(self.openStatisticsAndPlotsDialog, self.queriesMenu, self.queriesToolbar)
        # self.add_to_dropdown(self.openStatisticsAndPlotsDialog, queriesDropButton)

    """Toolbar visibility toggles"""

    def runGeneralToolbar(self):
        self.generalToolbar.setVisible(not self.generalToolbar.isVisible())

    def changeGeneralToolbarVisibility(self, status):
        self.generalDropButton.setChecked(status)

    def runProjectToolbar(self):
        self.projectToolbar.setVisible(not self.projectToolbar.isVisible())

    def changeProjectToolbarVisibility(self, status):
        self.projectDropButton.setChecked(status)

    def runEditionToolbar(self):
        self.editionToolbar.setVisible(not self.editionToolbar.isVisible())

    def changeEditionToolbarVisibility(self, status):
        self.editDropButton.setChecked(status)

    def runDebugToolbar(self):
        self.debugToolbar.setVisible(not self.debugToolbar.isVisible())

    def changeDebugToolbarVisibility(self, status):
        self.debugDropButton.setChecked(status)

    def runToolsToolbar(self):
        self.toolsToolbar.setVisible(not self.toolsToolbar.isVisible())

    def changeToolsToolbarVisibility(self, status):
        self.toolsDropButton.setChecked(status)

    def runAnalysisToolbar(self):
        self.analysisToolbar.setVisible(not self.analysisToolbar.isVisible())

    def changeAnalysisToolbarVisibility(self, status):
        self.analysisDropButton.setChecked(status)

    def runDtToolbar(self):
        self.dtToolbar.setVisible(not self.dtToolbar.isVisible())

    def changeDtToolbarVisibility(self, status):
        self.dtDropButton.setChecked(status)

    def runQueriesToolbar(self):
        self.queriesToolbar.setVisible(not self.queriesToolbar.isVisible())

    def changeQueriesToolbarVisibility(self, status):
        self.queriesDropButton.setChecked(status)

    def updateCheckables(self):
        self.generalDropButton.setChecked(self.generalToolbar.isVisible())
        self.projectDropButton.setChecked(self.projectToolbar.isVisible())
        self.editDropButton.setChecked(self.editionToolbar.isVisible())
        self.debugDropButton.setChecked(self.debugToolbar.isVisible())
        self.toolsDropButton.setChecked(self.toolsToolbar.isVisible())
        self.analysisDropButton.setChecked(self.analysisToolbar.isVisible())
        self.dtDropButton.setChecked(self.dtToolbar.isVisible())
        self.queriesDropButton.setChecked(self.queriesToolbar.isVisible())

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec()

    def runReportIssues(self):
        webbrowser.open("https://github.com/qgisred/QGISRed/issues")
