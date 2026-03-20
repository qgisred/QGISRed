# -*- coding: utf-8 -*-
"""Menu section for QGISRed (build all toolbars/menus, toolbar visibility toggles, about/report)."""

import webbrowser

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QToolButton

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

    SegmentTreeSection:
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
        self.generalToolbar.visibilityChanged.connect(self.changeGeneralToolbarVisibility)
        self.generalToolbar.setVisible(False)
        #    #Buttons
        generalDropButton = QToolButton()
        icon_path = ":/images/iconGeneralMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("General"),
            callback=self.runGeneralToolbar,
            menubar=self.generalMenu,
            add_to_menu=False,
            toolbar=self.toolbar,
            dropButton=generalDropButton,
            addActionToDrop=False,
            checkable=True,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.generalDropButton = generalDropButton

        icon_path = ":/images/iconProjectManager.svg"
        self.add_action(
            icon_path,
            text=self.tr("Project manager..."),
            callback=self.runProjectManager,
            menubar=self.generalMenu,
            toolbar=self.generalToolbar,
            actionBase=generalDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconOpenProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Open project..."),
            callback=self.runCanOpenProject,
            menubar=self.generalMenu,
            toolbar=self.generalToolbar,
            actionBase=generalDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCreateProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Create project..."),
            callback=self.runCanCreateProject,
            menubar=self.generalMenu,
            toolbar=self.generalToolbar,
            actionBase=generalDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconImportProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Import project..."),
            callback=self.runCanImportData,
            menubar=self.generalMenu,
            toolbar=self.generalToolbar,
            actionBase=generalDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addProjectMenu(self):
        #    #Menu
        self.projectMenu = self.qgisredmenu.addMenu(self.tr("Project"))
        self.projectMenu.setIcon(QIcon(":/images/iconProjectMenu.svg"))
        #    #Toolbar
        self.projectToolbar = self.iface.addToolBar(self.tr("QGISRed Project"))
        self.projectToolbar.setObjectName(self.tr("QGISRed Project"))
        self.projectToolbar.visibilityChanged.connect(self.changeProjectToolbarVisibility)
        self.projectToolbar.setVisible(False)
        #    #Buttons
        projectDropButton = QToolButton()
        icon_path = ":/images/iconProjectMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Project"),
            callback=self.runProjectToolbar,
            menubar=self.projectMenu,
            add_to_menu=False,
            toolbar=self.toolbar,
            dropButton=projectDropButton,
            checkable=True,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.projectDropButton = projectDropButton

        icon_path = ":/images/iconSummary.svg"
        self.add_action(
            icon_path,
            text=self.tr("Summary..."),
            callback=self.runSummary,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAddData.svg"
        self.add_action(
            icon_path,
            text=self.tr("Add data by import..."),
            callback=self.runCanAddData,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconLayerManagement.svg"
        self.add_action(
            icon_path,
            text=self.tr("Layer manager..."),
            callback=self.runEditProject,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconThematicMaps.svg"
        self.add_action(
            icon_path,
            text=self.tr("Legend editor..."),
            callback=self.runLegends,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        projectDropButton.menu().addSeparator()
        self.projectToolbar.addSeparator()
        self.projectMenu.addSeparator()
        icon_path = ":/images/iconProjectSettings.svg"
        self.add_action(
            icon_path,
            text=self.tr("Project settings..."),
            callback=self.runSettings,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconDefaultMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Default values..."),
            callback=self.runDefaultValues,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconMaterials.svg"
        self.add_action(
            icon_path,
            text=self.tr("Materials Table..."),
            callback=self.runMaterials,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        projectDropButton.menu().addSeparator()
        self.projectToolbar.addSeparator()
        self.projectMenu.addSeparator()
        icon_path = ":/images/iconSaveProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Save project"),
            callback=self.runSaveActionProject,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconBackUpProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Project backup"),
            callback=self.runCreateBackup,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCloseProject.svg"
        self.add_action(
            icon_path,
            text=self.tr("Close project"),
            callback=self.runCloseProject,
            menubar=self.projectMenu,
            toolbar=self.projectToolbar,
            actionBase=projectDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addEditMenu(self):
        #    #Menu
        self.editionMenu = self.qgisredmenu.addMenu(self.tr("Edition"))
        self.editionMenu.setIcon(QIcon(":/images/iconEditMenu.svg"))
        #    #Toolbar
        self.editionToolbar = self.iface.addToolBar(self.tr("QGISRed Edition"))
        self.editionToolbar.setObjectName(self.tr("QGISRed Edition"))
        self.editionToolbar.visibilityChanged.connect(self.changeEditionToolbarVisibility)
        self.editionToolbar.setVisible(False)

        #    #Buttons
        editDropButton = QToolButton()
        icon_path = ":/images/iconEditMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Edition"),
            callback=self.runEditionToolbar,
            menubar=self.editionMenu,
            add_to_menu=False,
            checkable=True,
            toolbar=self.toolbar,
            dropButton=editDropButton,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.editDropButton = editDropButton

        icon_path = ":/images/iconAddPipe.svg"
        self.addPipeButton = self.add_action(
            icon_path,
            text=self.tr("Add pipe"),
            callback=self.runPaintPipe,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAddTank.svg"
        self.addTankButton = self.add_action(
            icon_path,
            text=self.tr("Add tank"),
            callback=self.runSelectTankPoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAddReservoir.svg"
        self.addReservoirButton = self.add_action(
            icon_path,
            text=self.tr("Add reservoir"),
            callback=self.runSelectReservoirPoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAddValve.svg"
        self.insertValveButton = self.add_action(
            icon_path,
            text=self.tr("Insert valve in pipe"),
            callback=self.runSelectValvePoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAddPump.svg"
        self.insertPumpButton = self.add_action(
            icon_path,
            text=self.tr("Insert pump in pipe"),
            callback=self.runSelectPumpPoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        editDropButton.menu().addSeparator()
        self.editionToolbar.addSeparator()
        self.editionMenu.addSeparator()
        icon_path = ":/images/iconMultipleSelection.svg"
        self.selectElementsButton = self.add_action(
            icon_path,
            text=self.tr("Select multiple elements"),
            callback=self.runSelectElements,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconMoveNodes.svg"
        self.moveElementsButton = self.add_action(
            icon_path,
            text=self.tr("Move nodes"),
            callback=self.runMoveElements,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconEditVertices.svg"
        self.moveVertexsButton = self.add_action(
            icon_path,
            text=self.tr("Edit link vertices"),
            callback=self.runEditLinkGeometry,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconReverseElements.svg"
        self.reverseLinkButton = self.add_action(
            icon_path,
            text=self.tr("Reverse elements"),
            callback=self.canReverseLink,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconSplitJoinPipes.svg"
        self.splitPipeButton = self.add_action(
            icon_path,
            text=self.tr("Split/Join pipes"),
            callback=self.runSelectSplitPoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconMergeSplitJunctions.svg"
        self.mergeSplitJunctionButton = self.add_action(
            icon_path,
            text=self.tr("Merge/Dissolve junctions"),
            callback=self.runSelectPointToMergeSplit,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCreateRemoveTConnections.svg"
        self.createReverseTconButton = self.add_action(
            icon_path,
            text=self.tr("Create/Remove T connections"),
            callback=self.runSelectPointToTconnections,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCreateRemoveCrossings.svg"
        self.createReverseCrossButton = self.add_action(
            icon_path,
            text=self.tr("Create/Remove crossings"),
            callback=self.runSelectPointToCrossings,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconMoveElements.svg"
        self.moveValvePumpButton = self.add_action(
            icon_path,
            text=self.tr("Move valves/pumps"),
            callback=self.runSelectValvePumpPoints,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconChangeStatus.svg"
        self.changeStatusButton = self.add_action(
            icon_path,
            text=self.tr("Change element status"),
            callback=self.runSelectElementStatusPoint,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconDeleteElements.svg"
        self.removeElementsButton = self.add_action(
            icon_path,
            text=self.tr("Delete elements"),
            callback=self.canDeleteElements,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        editDropButton.menu().addSeparator()
        self.editionToolbar.addSeparator()
        self.editionMenu.addSeparator()
        icon_path = ":/images/iconEditMenu.svg"
        self.editElementButton = self.add_action(
            icon_path,
            text=self.tr("Edit element properties..."),
            callback=self.runSelectPointProperties,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconPatternsAndCurves.svg"
        self.add_action(
            icon_path,
            text=self.tr("Edit patterns and curves..."),
            callback=self.runPatternsCurves,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconControlsAndRules.svg"
        self.add_action(
            icon_path,
            text=self.tr("Edit controls..."),
            callback=self.runControls,
            menubar=self.editionMenu,
            toolbar=self.editionToolbar,
            actionBase=editDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addDebugMenu(self):
        #    #Menu
        self.debugMenu = self.qgisredmenu.addMenu(self.tr("Debug"))
        self.debugMenu.setIcon(QIcon(":/images/iconDebugMenu.svg"))
        #    #Toolbar
        self.debugToolbar = self.iface.addToolBar(self.tr("QGISRed Debug"))
        self.debugToolbar.setObjectName(self.tr("QGISRed Debug"))
        self.debugToolbar.visibilityChanged.connect(self.changeDebugToolbarVisibility)
        self.debugToolbar.setVisible(False)
        #    #Buttons
        debugDropButton = QToolButton()
        icon_path = ":/images/iconDebugMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Debug"),
            callback=self.runDebugToolbar,
            menubar=self.debugMenu,
            add_to_menu=False,
            checkable=True,
            toolbar=self.toolbar,
            dropButton=debugDropButton,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.debugDropButton = debugDropButton

        icon_path = ":/images/iconDebugMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check && Commit data"),
            callback=self.runCommit,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconRemoveOverlappings.svg"
        self.add_action(
            icon_path,
            text=self.tr("Remove overlapping elements"),
            callback=self.runCheckOverlappingElements,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconSimplifyVertices.svg"
        self.add_action(
            icon_path,
            text=self.tr("Simplify link vertices"),
            callback=self.runSimplifyVertices,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconJoinPipes.svg"
        self.add_action(
            icon_path,
            text=self.tr("Join consecutive pipes (diameter, material and year)"),
            callback=self.runCheckJoinPipes,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCreateTConnections.svg"
        self.add_action(
            icon_path,
            text=self.tr("Create T Connections"),
            callback=self.runCheckTConncetions,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCheckConnectivity.svg"
        dropButton = QToolButton()
        self.add_action(
            icon_path,
            text=self.tr("Check connectivity"),
            callback=self.runCheckConnectivityM,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            dropButton=dropButton,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconDeleteIsolatedAreas.svg"
        self.add_action(
            icon_path,
            text=self.tr("Delete issolated subzones"),
            callback=self.runCheckConnectivityC,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=dropButton,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        dropButton.menu().addSeparator()
        self.debugToolbar.addSeparator()
        self.debugMenu.addSeparator()
        icon_path = ":/images/iconCheckPipeLengths.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check pipe lengths"),
            callback=self.runCheckLengths,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCheckDiameters.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check diameters"),
            callback=self.runCheckDiameters,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCheckMaterials.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check pipe materials"),
            callback=self.runCheckMaterials,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconCheckInstalationDates.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check pipe installation dates"),
            callback=self.runCheckInstallationDates,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        dropButton.menu().addSeparator()
        self.debugToolbar.addSeparator()
        self.debugMenu.addSeparator()
        icon_path = ":/images/iconCheckHydraulicSectors.svg"
        self.add_action(
            icon_path,
            text=self.tr("Check hydraulic sectors"),
            callback=self.runHydraulicSectors,
            menubar=self.debugMenu,
            toolbar=self.debugToolbar,
            actionBase=debugDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addToolsMenu(self):
        #    #Menu
        self.toolsMenu = self.qgisredmenu.addMenu(self.tr("Tools"))
        self.toolsMenu.setIcon(QIcon(":/images/iconToolsMenu.svg"))
        #    #Toolbar
        self.toolsToolbar = self.iface.addToolBar(self.tr("QGISRed Tools"))
        self.toolsToolbar.setObjectName(self.tr("QGISRed Tools"))
        self.toolsToolbar.visibilityChanged.connect(self.changeToolsToolbarVisibility)
        self.toolsToolbar.setVisible(False)
        #    #Buttons
        toolDropButton = QToolButton()
        icon_path = ":/images/iconToolsMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Tools"),
            callback=self.runToolsToolbar,
            menubar=self.toolsMenu,
            add_to_menu=False,
            checkable=True,
            toolbar=self.toolbar,
            dropButton=toolDropButton,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.toolsDropButton = toolDropButton

        icon_path = ":/images/iconCalculatePipeLengths.svg"
        self.add_action(
            icon_path,
            text=self.tr("Automatically Calculate Pipe Lengths"),
            callback=self.runCalculateLengths,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconInterpolateNodeElevations.svg"
        self.add_action(
            icon_path,
            text=self.tr("Interpolate elevation from .asc files..."),
            callback=self.runElevationInterpolation,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconSetRoughnessFromMaterialDate.svg"
        self.add_action(
            icon_path,
            text=self.tr("Set roughness coefficient (from Material and Date)"),
            callback=self.runSetRoughness,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconConvertRoughnessCoeff.svg"
        self.add_action(
            icon_path,
            text=self.tr("Convert roughness coefficient"),
            callback=self.runConvertRoughness,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        toolDropButton.menu().addSeparator()
        self.toolsToolbar.addSeparator()
        self.toolsMenu.addSeparator()
        icon_path = ":/images/iconDemandBuilder.svg"
        self.add_action(
            icon_path,
            text=self.tr("Nodal Demand Builder..."),
            callback=self.runDemandsManager,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconScenarioBuilder.svg"
        self.add_action(
            icon_path,
            text=self.tr("Scenario Builder..."),
            callback=self.runScenarioManager,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconIsolatedSegments.svg"
        self.isolatedSegmentsButton = self.add_action(
            icon_path,
            text=self.tr("Isolated Segments"),
            callback=self.runIsolatedSegments,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        toolDropButton.menu().addSeparator()
        self.toolsToolbar.addSeparator()
        self.toolsMenu.addSeparator()
        icon_path = ":/images/iconDemandSectors.svg"
        self.add_action(
            icon_path,
            text=self.tr("Obtain demand sectors"),
            callback=self.runDemandSectors,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconGraphTree.svg"
        self.add_action(
            icon_path,
            text=self.tr("Tree Graph..."),
            callback=self.runTree,
            menubar=self.toolsMenu,
            toolbar=self.toolsToolbar,
            actionBase=toolDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addAnalysisMenu(self):
        #    #Menu
        self.analysisMenu = self.qgisredmenu.addMenu(self.tr("Analysis"))
        self.analysisMenu.setIcon(QIcon(":/images/iconAnalysisMenu.svg"))
        #    #Toolbar
        self.analysisToolbar = self.iface.addToolBar(self.tr("QGISRed Analysis"))
        self.analysisToolbar.setObjectName(self.tr("QGISRed Analysis"))
        self.analysisToolbar.visibilityChanged.connect(self.changeAnalysisToolbarVisibility)
        self.analysisToolbar.setVisible(False)
        #    #Buttons
        analysisDropButton = QToolButton()
        icon_path = ":/images/iconAnalysisMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Analysis"),
            callback=self.runAnalysisToolbar,
            menubar=self.analysisMenu,
            add_to_menu=False,
            toolbar=self.toolbar,
            dropButton=analysisDropButton,
            checkable=True,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.analysisDropButton = analysisDropButton

        icon_path = ":/images/iconAnalysisMenu.svg"
        dropButton = QToolButton()
        self.add_action(
            icon_path,
            text=self.tr("Run model"),
            callback=self.runModel,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=analysisDropButton,
            dropButton=dropButton,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconResultsBrowser.svg"
        self.add_action(
            icon_path,
            text=self.tr("Results browser"),
            callback=self.runShowResultsDock,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=dropButton,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAnalysisMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Status report"),
            callback=self.runOpenStatusReport,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=dropButton,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        icon_path = ":/images/iconAnalysisOptions.svg"
        self.add_action(
            icon_path,
            text=self.tr("Analysis options..."),
            callback=self.runAnalysisOptions,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=analysisDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        analysisDropButton.menu().addSeparator()
        self.analysisToolbar.addSeparator()
        self.analysisMenu.addSeparator()
        icon_path = ":/images/iconTimeSeries.svg"
        self.timeSeriesButton = self.add_action(
            icon_path,
            text=self.tr("Time Series"),
            callback=self.runTimeSeries,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=analysisDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        analysisDropButton.menu().addSeparator()
        self.analysisToolbar.addSeparator()
        self.analysisMenu.addSeparator()
        icon_path = ":/images/iconExportToEpanet.svg"
        self.add_action(
            icon_path,
            text=self.tr("Export to Epanet"),
            callback=self.runExportInp,
            menubar=self.analysisMenu,
            toolbar=self.analysisToolbar,
            actionBase=analysisDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addDigitalTwinMenu(self):
        #    #Menu
        self.dtMenu = self.qgisredmenu.addMenu(self.tr("Digital Twin"))
        self.dtMenu.setIcon(QIcon(":/images/iconDigitalTwinMenu.svg"))
        #    #Toolbar
        self.dtToolbar = self.iface.addToolBar(self.tr("QGISRed Digital Twin"))
        self.dtToolbar.setObjectName(self.tr("QGISRed Digital Twin"))
        self.dtToolbar.visibilityChanged.connect(self.changeDtToolbarVisibility)
        self.dtToolbar.setVisible(False)
        #    #Buttons
        dtDropButton = QToolButton()
        icon_path = ":/images/iconDigitalTwinMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Digital Twin"),
            callback=self.runDtToolbar,
            menubar=self.dtMenu,
            add_to_menu=False,
            checkable=True,
            toolbar=self.toolbar,
            dropButton=dtDropButton,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.dtDropButton = dtDropButton

        icon_path = ":/images/iconAddConnection.svg"
        self.addServConnButton = self.add_action(
            icon_path,
            text=self.tr("Add service connection"),
            callback=self.runPaintServiceConnection,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddIsolationValve.svg"
        self.addIsolationValveButton = self.add_action(
            icon_path,
            text=self.tr("Add isolation valve"),
            callback=self.runSelectIsolationValvePoint,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        # Create submenu for the main menu
        self.meterSubMenu = self.dtMenu.addMenu(self.tr("Add Meter"))
        self.meterSubMenu.setIcon(QIcon(":/images/iconAddDefaultMeter.svg"))

        # Create a separate submenu for the toolbar dropdown
        self.meterSubMenuToolbar = QMenu(self.tr("Add Meter"), self.iface.mainWindow())
        act_toolbar_meter = self.dtDropButton.menu().addMenu(self.meterSubMenuToolbar)
        act_toolbar_meter.setIcon(QIcon(":/images/iconAddDefaultMeter.svg"))

        self.currentMeter = "Undefined"
        self.addMeterDropButton = QToolButton()
        self.addMeterDropButton.setPopupMode(QToolButton.InstantPopup)  # Optional: open menu on click
        icon_path = ":/images/iconAddDefaultMeter.svg"
        self.add_action(
            icon_path,
            text=self.tr("Add meter"),
            callback=self.runSelectDefaultMeterPoint,
            add_to_menu=False,
            menubar=None,
            toolbar=self.dtToolbar,
            actionBase=None,  # Changed: no flat action in dtDropButton menu
            addActionToDrop=False,
            add_to_toolbar=False,
            checkable=True,
            dropButton=self.addMeterDropButton,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddAutometer.svg"
        self.addAutoMeterButton = self.add_action(
            icon_path,
            text=self.tr("Add automatic meter"),
            callback=self.runSelectAutoMeterPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )
        self.addMeterDropButton.setDefaultAction(self.addAutoMeterButton)

        icon_path = ":/images/iconAddManometer.svg"
        self.addManometerButton = self.add_action(
            icon_path,
            text=self.tr("Add manometer"),
            callback=self.runSelectManometerPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddFlowmeter.svg"
        self.addFlowmeterButton = self.add_action(
            icon_path,
            text=self.tr("Add flowmeter"),
            callback=self.runSelectFlowmeterPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddCountermeter.svg"
        self.addCountermeterButton = self.add_action(
            icon_path,
            text=self.tr("Add countermeter"),
            callback=self.runSelectCountermeterPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddLevelSensor.svg"
        self.addLevelSensorButton = self.add_action(
            icon_path,
            text=self.tr("Add level sensor"),
            callback=self.runSelectLevelSensorPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddDiffManometer.svg"
        self.addDifferentialManometerButton = self.add_action(
            icon_path,
            text=self.tr("Add differential manometer"),
            callback=self.runSelectDifferentialManometerPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddQualitySensor.svg"
        self.addQualitySensorButton = self.add_action(
            icon_path,
            text=self.tr("Add quality sensor"),
            callback=self.runSelectQualitySensorPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddEnergySensor.svg"
        self.addEnergySensorButton = self.add_action(
            icon_path,
            text=self.tr("Add energy sensor"),
            callback=self.runSelectEnergySensorPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddStatusSensor.svg"
        self.addStatusSensorButton = self.add_action(
            icon_path,
            text=self.tr("Add status sensor"),
            callback=self.runSelectStatusSensorPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddValveOpening.svg"
        self.addValveOpeningButton = self.add_action(
            icon_path,
            text=self.tr("Add valve opening"),
            callback=self.runSelectValveOpeningPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconAddTachometer.svg"
        self.addTachometerButton = self.add_action(
            icon_path,
            text=self.tr("Add tachometer"),
            callback=self.runSelectTachometerPoint,
            menubar=self.meterSubMenu,
            toolbar=self.dtToolbar,
            actionBase=self.addMeterDropButton,
            add_to_toolbar=False,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

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

        icon_path = ":/images/iconLoadMeterReadings.svg"
        self.add_action(
            icon_path,
            text=self.tr("Load meter readings..."),
            callback=self.runLoadReadings,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconSetPipeStatusFromValves.svg"
        self.add_action(
            icon_path,
            text=self.tr("Set pipe's initial status from isolation valves"),
            callback=self.runSetPipeStatus,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

        icon_path = ":/images/iconLoadFieldData.svg"
        self.add_action(
            icon_path,
            text=self.tr("Load field data..."),
            callback=self.runLoadScada,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

        dtDropButton.menu().addSeparator()
        self.dtMenu.addSeparator()
        self.dtToolbar.addSeparator()

        icon_path = ":/images/iconIncorporateConnectionsToModel.svg"
        self.add_action(
            icon_path,
            text=self.tr("Convert service connections into pipes/nodes"),
            callback=self.runAddConnections,
            menubar=self.dtMenu,
            toolbar=self.dtToolbar,
            actionBase=dtDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

    def addQueriesMenu(self):
        #    #Menu
        self.queriesMenu = self.qgisredmenu.addMenu(self.tr("Queries"))
        self.queriesMenu.setIcon(QIcon(":/images/iconQueriesMenu.svg"))
        #    #Toolbar
        self.queriesToolbar = self.iface.addToolBar(self.tr("QGISRed Queries"))
        self.queriesToolbar.setObjectName(self.tr("QGISRed Queries"))
        self.queriesToolbar.visibilityChanged.connect(self.changeQueriesToolbarVisibility)
        self.queriesToolbar.setVisible(False)
        #    #Buttons
        queriesDropButton = QToolButton()
        icon_path = ":/images/iconQueriesMenu.svg"
        self.add_action(
            icon_path,
            text=self.tr("Queries"),
            callback=self.runQueriesToolbar,
            menubar=self.queriesMenu,
            add_to_menu=False,
            toolbar=self.toolbar,
            dropButton=queriesDropButton,
            checkable=True,
            addActionToDrop=False,
            add_to_toolbar=False,
            parent=self.iface.mainWindow(),
        )
        self.queriesDropButton = queriesDropButton
        # Find Elements by ID
        icon_path = ":/images/iconFindElements.svg"
        self.openFindElementsDialog = self.add_action(
            icon_path,
            text=self.tr("Find Elements by ID..."),
            callback=self.runFindElements,
            menubar=self.queriesMenu,
            toolbar=self.queriesToolbar,
            actionBase=queriesDropButton,
            add_to_toolbar=True,
            checkable=True,
            parent=self.iface.mainWindow(),
        )

        # # Elements Properties
        icon_path = ":/images/iconElementProperties.svg"
        self.openElementsPropertyDialog = self.add_action(
            icon_path,
            text=self.tr("Element Properties..."),
            callback=self.runElementsProperty,
            menubar=self.queriesMenu,
            toolbar=self.queriesToolbar,
            actionBase=queriesDropButton,
            checkable=True,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        # Thematic Maps
        icon_path = ":/images/iconThematicMaps.svg"
        self.openThematicMapsDialog = self.add_action(
            icon_path,
            text=self.tr("Thematic Maps..."),
            callback=self.runThematicMaps,
            menubar=self.queriesMenu,
            toolbar=self.queriesToolbar,
            actionBase=queriesDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        # # Queries by Attributes
        icon_path = ":/images/iconQueryByAttributes.svg"
        self.openLiveQueriesDialog = self.add_action(
            icon_path,
            text=self.tr("Queries by Attributes..."),
            callback=self.runQueriesByAttributes,
            menubar=self.queriesMenu,
            toolbar=self.queriesToolbar,
            actionBase=queriesDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )
        # # Statistics & Plots
        icon_path = ":/images/iconStatisticsAndPlots.svg"
        self.openStatisticsAndPlotsDialog = self.add_action(
            icon_path,
            text=self.tr("Statistics && Plots..."),
            callback=self.runStatisticsAndPlots,
            menubar=self.queriesMenu,
            toolbar=self.queriesToolbar,
            actionBase=queriesDropButton,
            add_to_toolbar=True,
            parent=self.iface.mainWindow(),
        )

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
        dlg.exec_()

    def runReportIssues(self):
        webbrowser.open("https://github.com/qgisred/QGISRed/issues")
