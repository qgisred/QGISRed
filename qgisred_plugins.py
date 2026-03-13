# -*- coding: utf-8 -*-
"""
/***************************************************************************
                                  QGISRed
 Tool for helping the hydraulic engineer in the task of modelling a water
 distribution network and in the decision-making process
                              -------------------
        begin                : 2019-03-26
        copyright            : (C) 2019 by REDHISP (UPV)
        email                : fmartine@hma.upv.es
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# Import QGis
from qgis.core import QgsProject, QgsVectorLayer, QgsMapLayer, QgsLayerTreeLayer, QgsRectangle
from qgis.core import QgsMessageLog, QgsCoordinateTransform, QgsApplication, QgsLayerTreeGroup, QgsLayerTreeNode
from PyQt5.QtGui import QIcon, QCursor, QPixmap
from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu, QFileDialog, QToolButton
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt5.QtXml import QDomDocument


# Import resources
from . import resources3x

# Import other plugin code
from .ui.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
from .ui.qgisred_createproject_dialog import QGISRedCreateProjectDialog
from .ui.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog
from .ui.qgisred_import_dialog import QGISRedImportDialog
from .ui.qgisred_about_dialog import QGISRedAboutDialog
from .ui.qgisred_results_dock import QGISRedResultsDock
from .ui.qgisred_toolLength_dialog import QGISRedLengthToolDialog
from .ui.qgisred_toolConnections_dialog import QGISRedServiceConnectionsToolDialog
from .ui.qgisred_toolConnectivity_dialog import QGISRedConnectivityToolDialog
from .ui.qgisred_loadproject_dialog import QGISRedImportProjectDialog
from .ui.qgisred_thematicmaps_dialog import QGISRedThematicMapsDialog
from .ui.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from .ui.qgisred_queriesbyattributes_dock import QGISRedQueriesByAttributesDock
from .ui.qgisred_statisticsandgraphs_dock import QGISRedStatisticsAndPlotsDock
from .ui.qgisred_timeseries_dock import QGISRedTimeSeriesDock
from .ui.qgisred_legends_dialog import QGISRedLegendsDialog
from .tools.qgisred_utils import QGISRedUtils
from .tools.qgisred_dependencies import QGISRedDependencies as GISRed
from .tools.qgisred_moveNodes import QGISRedMoveNodesTool
from .tools.qgisred_multilayerSelection import QGISRedMultiLayerSelection
from .tools.qgisred_createPipe import QGISRedCreatePipeTool
from .tools.qgisred_createConnection import QGISRedCreateConnectionTool
from .tools.qgisred_editLinksGeometry import QGISRedEditLinksGeometryTool
from .tools.qgisred_selectPoint import QGISRedSelectPointTool
from .tools.qgisred_identifyFeature import QGISRedIdentifyFeature

# Others imports
import os
import json
import tempfile
import platform
import base64
import shutil
import webbrowser
import urllib.request
import ssl
from ctypes import windll, c_uint16, c_uint, wstring_at, byref, cast
from ctypes import create_string_buffer, c_void_p, Structure, POINTER


class QGISRed:
    """QGISRed Plugin Implementation."""

    # Common variables
    ResultDockwidget = None
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns", "Materials", "Signals"]
    especificComplementaryLayers = []
    complementaryLayers = ["IsolationValves", "Hydrants", "WashoutValves", "AirReleaseValves", "ServiceConnections", "Meters"]
    TemporalFolder = "Temporal folder"
    DependenciesVersion = "1.0.17.1"
    gisredDll = None

    """Basic"""

    def __init__(self, iface):
        """Constructor.
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.storeQLRSucess = False
        self.isUnloading = False  # Flag to prevent DLL calls during shutdown

        if not platform.system() == "Windows":
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("QGISRed only works on Windows"), level=2, duration=5)
            return

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(self.plugin_dir, "i18n", "qgisred_{}.qm".format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > "4.3.3":
                QCoreApplication.installTranslator(self.translator)

        self.iface.initializationCompleted.connect(self.updateCheckables)
        # Declare instance attributes
        self.actions = []
        # Menu
        self.qgisredmenu = QMenu("&QGISRed", self.iface.mainWindow().menuBar())
        actions = self.iface.mainWindow().menuBar().actions()
        lastAction = actions[-1]
        self.iface.mainWindow().menuBar().insertMenu(lastAction, self.qgisredmenu)
        # Toolbar
        self.toolbar = self.iface.addToolBar("QGISRed")
        self.toolbar.setObjectName("QGISRed")
        # Status Bar
        self.unitsButton = QToolButton()
        self.unitsButton.setToolButtonStyle(2)
        icon = QIcon(":/images/iconGeneralMenu.svg")
        self.unitsAction = QAction(icon, "QGISRed: LPS | H-W", None)
        self.unitsAction.setToolTip(self.tr("Click to change it"))
        self.unitsAction.triggered.connect(self.runAnalysisOptions)
        self.actions.append(self.unitsAction)
        self.unitsButton.setDefaultAction(self.unitsAction)
        self.iface.mainWindow().statusBar().addWidget(self.unitsButton)

        # To allow downloads from qgisred web page
        ssl._create_default_https_context = ssl._create_unverified_context

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate("QGISRed", message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        menubar,
        toolbar,
        checkable=False,
        actionBase=None,
        dropButton=None,
        addActionToDrop=True,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if actionBase is not None:
            menu = actionBase.menu()
            if menu is not None:
                menu.addAction(action)
                actionBase.setMenu(menu)
                # actionBase.setDefaultAction(action)
                actionBase.setPopupMode(QToolButton.MenuButtonPopup)

        if dropButton is not None:
            menu = QMenu()
            if addActionToDrop:
                menu.addAction(action)
            dropButton.setMenu(menu)
            dropButton.setDefaultAction(action)
            dropButton.setPopupMode(QToolButton.MenuButtonPopup)
            toolbar.addWidget(dropButton)

        if add_to_toolbar:
            toolbar.addAction(action)

        if add_to_menu:
            menubar.addAction(action)

        self.actions.append(action)

        return action

    def initGui(self):
        if not platform.system() == "Windows":
            return

        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.addGeneralMenu()
        self.addProjectMenu()
        self.addEditMenu()
        self.addDebugMenu()
        self.addToolsMenu()
        self.addAnalysisMenu()
        self.addDigitalTwinMenu()
        self.addQueriesMenu()

        # About
        icon_path = ":/images/iconAbout.svg"
        self.add_action(
            icon_path,
            text=self.tr("About..."),
            callback=self.runAbout,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow(),
        )
        # Report issues
        icon_path = ":/images/iconGitHub.svg"
        self.add_action(
            icon_path,
            text=self.tr("Report issues or comments..."),
            callback=self.runReportIssues,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow(),
        )

        # Connecting QGis Events
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)
        QgsProject.instance().layersRemoved.connect(self.runLegendChanged)
        QgsProject.instance().readProject.connect(self.runOpenedQgisProject)

        # MapTools
        self.myMapTools = {}

        # QGISRed dependencies
        self.dllTempFolderFile = os.path.join(QGISRedUtils().getQGISRedFolder(), "dllTempFolders.dat")
        QGISRedUtils().copyDependencies()
        self.removeTempFolders()
        # QGISRed updates
        self.checkForUpdates()

        self.gplFolder = os.path.join(os.getenv("APPDATA"), "QGISRed")
        try:  # create directory if does not exist
            os.stat(self.gplFolder)
        except Exception:
            os.mkdir(self.gplFolder)
        self.gplFile = os.path.join(self.gplFolder, "qgisredprojectlist.gpl")

        # SHPs temporal folder
        self.tempFolder = tempfile._get_default_tempdir() + "\\QGISRed_" + next(tempfile._get_candidate_names())
        try:  # create directory if does not exist
            os.stat(self.tempFolder)
        except Exception:
            os.mkdir(self.tempFolder)
        self.KeyTemp = str(base64.b64encode(os.urandom(16)))

        # Issue layers
        self.issuesLayers = []
        for name in self.ownMainLayers:
            self.issuesLayers.append(name + "_Issues")
        for name in self.complementaryLayers:
            self.issuesLayers.append(name + "_Issues")
            
        # Open layers options
        self.hasToOpenConnectivityLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        self.selectedFids = {}

        self.zoomToFullExtent = False
        self.removingLayers = False        


        self.setCulture()
        # QgsMessageLog.logMessage("Culture set to " + definedCulture, "QGISRed", level=0)

        QgsMessageLog.logMessage(self.tr("Loaded sucssesfully"), "QGISRed", level=0)
  
    def cleanupDocks(self):
        """Disconnects signals and removes all plugin docks to ensure a clean state."""
        docks_to_clean = []
        if self.ResultDockwidget is not None:
            self.disconnectElementExplorerFromResultsDock()
            try:
                self.ResultDockwidget.visibilityChanged.disconnect(self.activeInputGroup)
                if hasattr(self, 'refreshTimeSeries'):
                    try:
                        self.ResultDockwidget.simulationFinished.disconnect(self.refreshTimeSeries)
                    except Exception: pass
                    try:
                        self.ResultDockwidget.resultPropertyChanged.disconnect(self.refreshTimeSeries)
                    except Exception: pass
            except Exception:
                pass
            docks_to_clean.append(('ResultDockwidget', self.ResultDockwidget))
            self.ResultDockwidget = None

        if hasattr(self, 'timeSeriesDock') and self.timeSeriesDock is not None:
            try:
                self.timeSeriesDock.visibilityChanged.disconnect(self.timeSeriesDockVisibilityChanged)
            except Exception:
                pass
            docks_to_clean.append(('timeSeriesDock', self.timeSeriesDock))
            self.timeSeriesDock = None

        if hasattr(self, 'statisticsAndPlotsDock') and self.statisticsAndPlotsDock is not None:
            docks_to_clean.append(('statisticsAndPlotsDock', self.statisticsAndPlotsDock))
            self.statisticsAndPlotsDock = None

        if hasattr(self, 'queriesByAttributesDock') and self.queriesByAttributesDock is not None:
            docks_to_clean.append(('queriesByAttributesDock', self.queriesByAttributesDock))
            self.queriesByAttributesDock = None

        # Also clean up Element Explorer if instance exists
        eeDock = QGISRedElementExplorerDock._instance
        if eeDock is not None:
            docks_to_clean.append(('elementExplorerDock', eeDock))

        for name, dock in docks_to_clean:
            try:
                dock.close()
                self.iface.removeDockWidget(dock)
                dock.setParent(None)
                dock.deleteLater()
            except Exception:
                pass
        
        # Clear Element Explorer singleton reference explicitly
        if eeDock is not None:
            QGISRedElementExplorerDock._instance = None

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # Set flag to prevent DLL calls during shutdown
        self.isUnloading = False

        # Invalidate the DLL instance immediately
        self.gisredDll = None

        # Deactivate all map tools to prevent callbacks during shutdown
        try:
            if hasattr(self, 'myMapTools'):
                for tool_name, tool in list(self.myMapTools.items()):
                    try:
                        if tool is not None:
                            if self.iface.mapCanvas().mapTool() is tool:
                                self.iface.mapCanvas().unsetMapTool(tool)
                            tool.deactivate()
                    except Exception:
                        pass
                self.myMapTools.clear()
        except Exception:
            pass

        # Disconnect signal handlers to prevent callbacks during cleanup
        try:
            QgsProject.instance().projectSaved.disconnect(self.runSaveProject)
        except Exception:
            pass
        try:
            QgsProject.instance().cleared.disconnect(self.runClearedProject)
        except Exception:
            pass
        try:
            QgsProject.instance().layersRemoved.disconnect(self.runLegendChanged)
        except Exception:
            pass
        try:
            QgsProject.instance().readProject.disconnect(self.runOpenedQgisProject)
        except Exception:
            pass

        QGISRedUtils().removeFolder(self.tempFolder)

        if QGISRedUtils.DllTempoFolder is not None:
            with open(self.dllTempFolderFile, "a+") as file:
                file.write(QGISRedUtils.DllTempoFolder + "\n")

        # Cleanup Docks
        self.cleanupDocks()

        for action in self.actions:
            self.iface.removeToolBarIcon(action)

        # remove the toolbar
        del self.toolbar
        del self.generalToolbar
        del self.projectToolbar
        del self.editionToolbar
        del self.debugToolbar
        del self.toolsToolbar
        del self.analysisToolbar
        del self.dtToolbar
        del self.queriesToolbar

        # remove statusbar label
        self.iface.mainWindow().statusBar().removeWidget(self.unitsButton)

        # remove menus
        if self.generalMenu:
            self.generalMenu.menuAction().setVisible(False)
        if self.projectMenu:
            self.projectMenu.menuAction().setVisible(False)
        if self.editionMenu:
            self.editionMenu.menuAction().setVisible(False)
        if self.debugMenu:
            self.debugMenu.menuAction().setVisible(False)
        if self.toolsMenu:
            self.toolsMenu.menuAction().setVisible(False)
        if self.analysisMenu:
            self.analysisMenu.menuAction().setVisible(False)
        if self.dtMenu:
            self.dtMenu.menuAction().setVisible(False)
        if self.queriesMenu:
            self.queriesMenu.menuAction().setVisible(False)
        if self.qgisredmenu:
            self.qgisredmenu.menuAction().setVisible(False)

    """Create menus"""

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
            text=self.tr("Save map"),
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

    """Version & DLLs"""

    def setCulture(self):
        ui_language = QgsApplication.locale()
        try:
            GISRed.SetCulture(ui_language)
        except Exception:
            pass

    def getVersion(self, filename, what):
        class LANGANDCODEPAGE(Structure):
            _fields_ = [("wLanguage", c_uint16), ("wCodePage", c_uint16)]

        wstr_file = wstring_at(filename)
        size = windll.version.GetFileVersionInfoSizeW(wstr_file, None)
        if size == 0:
            return "0.0.0.0"

        buffer = create_string_buffer(size)
        if windll.version.GetFileVersionInfoW(wstr_file, None, size, buffer) == 0:
            return "0.0.0.0"

        value = c_void_p(0)
        value_size = c_uint(0)
        ret = windll.version.VerQueryValueW(buffer, wstring_at(r"\VarFileInfo\Translation"), byref(value), byref(value_size))
        if ret == 0:
            return "0.0.0.0"
        lcp = cast(value, POINTER(LANGANDCODEPAGE))
        language = "{0:04x}{1:04x}".format(lcp.contents.wLanguage, lcp.contents.wCodePage)

        res = windll.version.VerQueryValueW(
            buffer, wstring_at("\\StringFileInfo\\" + language + "\\" + what), byref(value), byref(value_size)
        )

        if res == 0:
            return "0.0.0.0"
        return wstring_at(value.value, value_size.value - 1)

    def checkDependencies(self):
        valid = False
        gisredDir = QGISRedUtils().getGISRedDllFolder()
        if os.path.isdir(gisredDir):
            currentVersion = self.getVersion(os.path.join(gisredDir, "GISRed.QGisPlugins.dll"), "FileVersion")
            if currentVersion == self.DependenciesVersion:
                valid = True
        if not valid:
            link = '"https://qgisred.upv.es/files/dependencies/' + self.DependenciesVersion + '/QGISRed_Installation.msi"'
            request = QMessageBox.question(
                self.iface.mainWindow(),
                self.tr("QGISRed Dependencies"),
                self.tr(
                    "QGISRed plugin only runs in Windows OS and requires some dependencies (v"
                    + self.DependenciesVersion
                    + "). Do you want to install them now?\n\nAt the end, the QGISRed web page will be open to show the news, "
                    "where you can also register if you wish to receive the newsletters."
                ),
                QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
            )
            if request == QMessageBox.Yes:
                self.openNewFeaturesWebpage()
                # Remove previous dependencies version
                if not self.DependenciesVersion.endswith(".0"):
                    uninstallFile = os.path.join(
                        os.path.join(os.path.join(os.getenv("APPDATA"), "QGISRed"), "dlls"), "Uninstall.msi.lnk"
                    )
                    if os.path.exists(uninstallFile):
                        os.system(uninstallFile)

                localFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".msi"
                try:
                    urllib.request.urlretrieve(link.strip("'\""), localFile)
                    os.system(localFile)
                    os.remove(localFile)
                except Exception:
                    pass
                valid = self.checkDependencies()
                if valid:
                    QGISRedUtils().copyDependencies()
                    self.setCulture()

        return valid

    def checkForUpdates(self):
        link = '"https://qgisred.upv.es/files/versions.txt"'
        tempLocalFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".txt"
        try:
            # Read online file
            urllib.request.urlretrieve(link.strip("'\""), tempLocalFile)
            f = open(tempLocalFile, "r")
            contents = f.read()  # 0.11
            f.close()
            newVersion = contents
            if len(contents.split(".")) == 2:
                newVersion += ".0"  # 0.11.0
            newVersion = "1." + newVersion  # 1.0.11.0
            if int(newVersion.replace(".", "")) > int(self.DependenciesVersion.replace(".", "")):
                # Read local file with versions that user don't want to remember
                fileVersions = os.path.join(os.path.join(os.getenv("APPDATA"), "QGISRed"), "updateVersions.dat")
                oldVersions = ""
                if os.path.exists(fileVersions):
                    f = open(fileVersions, "r")
                    oldVersions = f.read()
                    f.close()
                # Review if in local file is the current online version
                if contents not in oldVersions:
                    response = QMessageBox.question(
                        self.iface.mainWindow(),
                        self.tr("QGISRed Updates"),
                        self.tr(
                            "QGISRed plugin has a new version ("
                            + contents
                            + "). You can upgrade it from the QGis plugin manager. "
                            + "Do you want to remember it again?"
                        ),
                        QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                    )

                    # If user don't want to remember a local file is written with this version
                    if response == QMessageBox.No:
                        f = open(fileVersions, "w+")
                        f.write(contents + "\n")
                        f.close()
            os.remove(tempLocalFile)
        except:
            pass

    def openNewFeaturesWebpage(self):
        language = "en"
        if QgsApplication.instance().locale() == "es":
            language = "es"
        link = "https://qgisred.upv.es/files/news_" + language
        tempLocalFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".txt"
        try:
            # Read online file
            urllib.request.urlretrieve(link.strip("'\""), tempLocalFile)
            f = open(tempLocalFile, "r")
            url = f.readline()
            f.close()
            webbrowser.open(url)
            return url
        except:
            pass

    def removeTempFolders(self):
        if not os.path.exists(self.dllTempFolderFile):
            return
        allDeleted = True
        with open(self.dllTempFolderFile, "r") as file:
            lines = file.readlines()
            for line in lines:
                filePath = line.strip("\n")
                if not QGISRedUtils().removeFolder(filePath):
                    allDeleted = False
        if allDeleted:
            os.remove(self.dllTempFolderFile)

    """Project"""

    def defineCurrentProject(self):
        """Identifying the QGISRed current project"""
        self.NetworkName = "Network"
        self.ProjectDirectory = self.TemporalFolder
        layerName = "Pipes"
        layers = self.getLayers()
        for layer in layers:
            layerUri = self.getLayerPath(layer)
            if "_" + layerName in layerUri:
                self.ProjectDirectory = os.path.dirname(layerUri)
                fileNameWithoutExt = os.path.splitext(os.path.basename(layerUri))[0]
                self.NetworkName = fileNameWithoutExt.replace("_" + layerName, "")

    def isOpenedProjectOld(self):
        if self.isLayerOnEdition():
            return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                message = "The project has changes. Please save them before continuing."
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(message), level=1)
                return False
            else:
                # Close the project and continue?
                question = "Do you want to close the current project and continue?"
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    self.tr("Opened project"),
                    self.tr(question),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def isOpenedProject(self):
        layers = self.getLayers()
        for layer in layers:
            if layer.isEditable():
                self.iface.messageBar().pushMessage(
                    self.tr("Warning"), self.tr("Some layer is in Edit Mode. Plase, commit it before continuing."), level=1, duration=5
                )
                return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                self.iface.messageBar().pushMessage(
                    self.tr("Warning"), self.tr("The project has changes. Please save them before continuing."), level=1, duration=5
                )
                return False
            else:
                # Close project and continue?
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    QCoreApplication.translate("QGISRed", "Open project"),
                    QCoreApplication.translate("QGISRed", "Do you want to close the current project and continue?"),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers()) > 0:
                # Close files and continue?
                reply = QMessageBox.question(
                    self.iface.mainWindow(),
                    QCoreApplication.translate("QGISRed", "Open layers"),
                    QCoreApplication.translate("QGISRed", "Do you want to close the current layers and continue?"),
                    QMessageBox.Yes,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def clearQGisProject(self):
        QgsProject.instance().clear()

    def isValidProject(self):
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return False
        return True

    def isLayerOnEdition(self):
        layers = self.getLayers()
        for layer in layers:
            # Skip non-vector layers (like rasters or annotation layers)
            if not isinstance(layer, QgsVectorLayer):
                continue
        
            if layer.customProperty("qgisred_identifier") and layer.isEditable():
                message = "Some layer is in Edit Mode. Please, commit it before continuing."
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(message), level=1)
                return True
                
        return False

    def readUnits(self, folder="", network=""):
        if folder == "" and network == "":
            self.defineCurrentProject()
        units = "LPS"
        headloss = "D-W"
        qualityModel = "Chemical"
        massUnits = "mg/L"
        if self.ProjectDirectory == "Temporal Folder":
            return
        dbf = QgsVectorLayer(os.path.join(self.ProjectDirectory, self.NetworkName + "_Options.dbf"), "Options", "ogr")
        for feature in dbf.getFeatures():
            attrs = feature.attributes()
            if attrs[1] == "UNITS":
                units = attrs[2]
            if attrs[1] == "HEADLOSS":
                headloss = attrs[2]
            if attrs[1] == "QUALITY":
                qualityModel = attrs[2]
            if attrs[1] == "MASSUNITS":
                massUnits = attrs[2]

        QgsProject.instance().writeEntry("QGISRed", "project_units", units)
        QgsProject.instance().writeEntry("QGISRed", "project_headloss", headloss)
        QgsProject.instance().writeEntry("QGISRed", "project_qualitymodel", qualityModel)
        QgsProject.instance().writeEntry("QGISRed", "project_massunits", massUnits)

        self.unitsAction.setText("QGISRed: " + units + " | " + headloss)
        del dbf

    """Remove Layers"""

    def removeLayers(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)

    def removeDBFs(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownFiles, ".dbf")

    def removeIssuesLayers(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)

    def removeLayersAndIssuesLayers(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayers(self.issuesLayers)

    def removeIssuesLayersFiles(self):
        dirList = os.listdir(self.ProjectDirectory)
        for fi in dirList:
            if "_Issues." in fi:
                os.remove(os.path.join(self.ProjectDirectory, fi))

    def removeLayersConnectivity(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")

    def removeLayersAndConnectivity(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")

    def removeSectorLayers(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(["Links_" + self.Sectors, "Nodes_" + self.Sectors])
        sectorGroupName = self.getSectorGroupName()
        self.removeEmptyQuerySubGroup(sectorGroupName)

    """Open Layers"""
    def openRemoveSpecificLayers(self, layers, epsg):
        self.especificComplementaryLayers = self.complementaryLayers
        self.extent = QGISRedUtils().getProjectExtent()
        self.specificEpsg = epsg
        self.specificLayers = layers
        self.removingLayers = True
        QGISRedUtils().runTask(self.removeLayers, self.openSpecificLayers)

    def openSpecificLayers(self):
        self.especificComplementaryLayers = []
        if self.specificEpsg is not None:
            self.runChangeCrs()

        self.opendedLayers = False
        QGISRedUtils().runTask(self.openSpecificLayersProcess, self.setExtent)

    def openSpecificLayersProcess(self):
        if not self.opendedLayers:
            self.opendedLayers = True
            # Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, self.specificLayers)
            self.updateMetadata()
            self.removingLayers = False

    def openElementLayer(self, nameLayer):
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputGroup = self.getInputGroup()
        utils.openElementsLayers(inputGroup, [nameLayer])
        self.updateMetadata()

    def openElementLayers(self, net="", folder=""):
        # Allow overriding project/network if provided
        if not net == "" and not folder == "":
            self.NetworkName = net
            self.ProjectDirectory = folder

        # Prepare for opening
        self.opendedLayers = False
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputGroup = self.getInputGroup()

        if self.storeQLRSucess:
            utils.loadProjectFromQLR()
            inputGroup = self.getInputGroup()
            proccessPerformed = False
            for layer_name in self.ownMainLayers + self.especificComplementaryLayers:
                if not utils.isLayerOpened(layer_name):
                    utils.openElementsLayers(inputGroup, [layer_name])
                    proccessPerformed = True
            if not proccessPerformed:
                utils.openElementsLayers(inputGroup, self.ownMainLayers + self.especificComplementaryLayers, processOnly=True)
        else:
            for layer_name in self.ownMainLayers + self.especificComplementaryLayers:
                utils.openElementsLayers(inputGroup, [layer_name])

        # Reset any scenario‑specific list
        self.especificComplementaryLayers = []

        # Always remove the one project‑level QLR file if it was created
        utils.deleteProjectQLR()
        utils.removeEmptyLayersInGroup(inputGroup)

        self.updateMetadata()

    
    def openInputLayers(self, projectDir, networkName):
        # Open layers
        utils = QGISRedUtils(projectDir, networkName, self.iface)
        inputGroup = self.getInputGroup()
        utils.openElementsLayers(inputGroup, self.ownMainLayers)

    def openIssuesLayers(self):
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        issuesGroup = self.getIssuesGroup()
        utils.openIssuesLayers(issuesGroup, self.issuesLayers)

    def openConnectivityLayer(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        connGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Connectivity"])
        utils.openLayer(connGroup, "Links_Connectivity")

    def openSectorLayers(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            sectorGroupName = self.getSectorGroupName()
            sectorGroup = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", sectorGroupName])
            utils.openLayer(sectorGroup, "Links_" + self.Sectors, sectors=True)
            utils.openLayer(sectorGroup, "Nodes_" + self.Sectors, sectors=True)

    """Groups"""

    def activeInputGroup(self):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if self.ResultDockwidget is None:
            return
        try:
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            group = utils.getOrCreateGroup("Inputs")
            if group is not None:
                group.setItemVisibilityChecked(not self.ResultDockwidget.isVisible())
            group = utils.getOrCreateGroup("Results")
            if group is not None:
                group.setItemVisibilityChecked(self.ResultDockwidget.isVisible())
        except Exception:
            pass

    def getInputGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Inputs")

    def getQueryGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Queries")

    def getIssuesGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Issues")

    def removeEmptyIssuesGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        root = QgsProject.instance().layerTreeRoot()
        issuesGroup = utils._findGroupByNameRecursive(root, "Issues")
        if issuesGroup is not None:
            if len(issuesGroup.findLayers()) == 0:
                parent = issuesGroup.parent()
                if parent is not None:
                    parent.removeChildNode(issuesGroup)

    def getSectorGroupName(self):
        if self.Sectors == "HydraulicSectors":
            return "Hydraulic Sectors"
        elif self.Sectors == "DemandSectors":
            return "Demand Sectors"
        else:
            return "Sectors"

    def removeEmptyQuerySubGroup(self, name):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        root = QgsProject.instance().layerTreeRoot()
        querySubGroup = utils._findGroupByNameRecursive(root, name)
        if querySubGroup is not None:
            if len(querySubGroup.findLayers()) == 0:
                parent = querySubGroup.parent()
                if parent is not None:
                    parent.removeChildNode(querySubGroup)
        queryGroup = utils._findGroupByNameRecursive(root, "Queries")
        if queryGroup is not None:
            if len(queryGroup.findLayers()) == 0 and len(queryGroup.children()) == 0:
                parent = queryGroup.parent()
                if parent is not None:
                    parent.removeChildNode(queryGroup)

    """Others"""

    def processCsharpResult(self, b, message):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        self.storeQLRSucess, _ = utils.saveProjectAsQLR()
        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        if b == "True":
            if not message == "":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(message), level=3, duration=5)
        elif b == "False" or b == "Cancelled":
            pass
        elif b == "commit":
            self.hasToOpenNewLayers = True
        elif b == "shps":
            self.hasToOpenIssuesLayers = True
        elif b == "commit/shps":
            self.hasToOpenNewLayers = True
            self.hasToOpenIssuesLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

        self.removingLayers = True
        self.extent = QGISRedUtils().getProjectExtent()
        if self.hasToOpenNewLayers and self.hasToOpenIssuesLayers:
            QGISRedUtils().runTask(self.removeLayersAndIssuesLayers, self.runOpenTemporaryFiles)
        elif self.hasToOpenNewLayers:
            QGISRedUtils().runTask(self.removeLayers, self.runOpenTemporaryFiles)
        elif self.hasToOpenIssuesLayers:
            QGISRedUtils().runTask(self.removeIssuesLayers, self.runOpenTemporaryFiles)

    def runOpenTemporaryFiles(self):
        if self.hasToOpenIssuesLayers:
            self.removeIssuesLayersFiles()

        QApplication.setOverrideCursor(Qt.WaitCursor)

        resMessage = GISRed.ReplaceTemporalFiles(self.ProjectDirectory, self.tempFolder)

        self.readUnits(self.ProjectDirectory, self.NetworkName)

        if self.hasToOpenNewLayers:
            self.opendedLayers = False
            QGISRedUtils().runTask(self.openElementLayers, self.setExtent)
            self.openNewLayers = False

        if self.hasToOpenIssuesLayers:
            self.openIssuesLayers()
            self.hasToOpenIssuesLayers = False

        if self.hasToOpenConnectivityLayers:
            self.openConnectivityLayer()
            self.hasToOpenConnectivityLayers = False

        if self.hasToOpenSectorLayers:
            self.openSectorLayers()
            self.hasToOpenSectorLayers = False

        QApplication.restoreOverrideCursor()
        self.removingLayers = False

        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def getComplementaryLayersOpened(self):
        complementary = []
        groupName = "Inputs"
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
        if dataGroup is not None:
            layers = self.getLayers()
            root = QgsProject.instance().layerTreeRoot()
            for layer in layers:
                if not layer:
                    continue
                parent = root.findLayer(layer.id())
                if parent is not None:
                    if parent.parent().name() == groupName:
                        rutaLayer = self.getLayerPath(layer)
                        layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName + "_", "")
                        if not self.ownMainLayers.__contains__(layerName):
                            complementary.append(layerName)
        return complementary

    def blockLayers(self, readonly):
        layers = self.getLayers()
        for layer in layers:
            # Skip non-vector layers (like rasters or annotation layers)
            if not layer or not isinstance(layer, QgsVectorLayer):
                continue

            layer.setReadOnly(readonly)

    def updateMetadata(self, layersNames="", project="", net=""):
        if not self.checkDependencies():
            return

        # Validations
        if project == "" and net == "":  # Comes from ProjectManager
            self.defineCurrentProject()
            if not self.isValidProject():
                return
            project = self.ProjectDirectory
            net = self.NetworkName

        if layersNames == "":
            qgsFilename = QgsProject.instance().fileName()
            if not qgsFilename == "":
                layersNames = os.path.relpath(qgsFilename, project)
            else:
                layers = self.getLayers()
                # Inputs
                groupName = "Inputs"
                dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
                if dataGroup is not None:
                    layersNames = layersNames + "[Inputs]"
                    layersNames = layersNames + self.writeLayersOfGroups(groupName, layers)
                    layersNames = layersNames.strip(";")

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        GISRed.UpdateMetadata(project, net, layersNames)
        QApplication.restoreOverrideCursor()

    def writeLayersOfGroups(self, groupName, layers):
        root = QgsProject.instance().layerTreeRoot()
        paths = ""
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if parent is not None:
                if parent.parent().name() == groupName:
                    rutaLayer = self.getLayerPath(layer)
                    layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName + "_", "")
                    paths = paths + layerName + ";"
        return paths

    def setCursor(self, shape):
        cursor = QCursor()
        cursor.setShape(shape)
        self.iface.mapCanvas().setCursor(cursor)

    def setExtent(self):
        if self.zoomToFullExtent:
            self.iface.mapCanvas().zoomToFullExtent()
            self.iface.mapCanvas().refresh()
            self.zoomToFullExtent = False
        else:
            if self.extent is not None:
                self.iface.mapCanvas().setExtent(self.extent)
                self.iface.mapCanvas().refresh()
                self.extent = None

    def getTolerance(self):
        # DPI
        LOGPIXELSX = 88
        user32 = windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        pix_per_inch = windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
        user32.ReleaseDC(0, dc)

        # CanvasPixels
        unitsPerPixel = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel()
        # x WidthPixels --> m/px * px = metros
        # 25.4 mm == inch
        un = 25.4 / pix_per_inch  # x WidthPixels -- > mm/px x px = mm
        # 1mm * unitsPerPixel / un -->tolerance
        tolerance = 1 * unitsPerPixel / un
        return tolerance

    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getLayers(self):
        return QGISRedUtils().getLayers()

    def getSelectedFeaturesIds(self):
        linkIdsList = []
        nodeIdsList = []
        self.selectedFids = {}
        self.selectedIds = {}

        layers = self.getLayers()
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if layerName == "Sources" or layerName == "Demands": #TODO
                    continue
                if self.getLayerPath(layer) == layerPath:
                    fids = []
                    ids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        id = str(feature["Id"])
                        if id == "NULL":
                            message = self.tr("Some Ids are not defined. Commit before and try again.")
                            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                            self.selectedFids = {}
                            return False
                        if layer.geometryType() == 0:
                            ids.append(id)
                            nodeIdsList.append(id)
                        else:
                            ids.append(id)
                            linkIdsList.append(id)
                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids
                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        # if 'NULL' in nodeIdsList or 'NULL' in linkIdsList:
        #     self.iface.messageBar().pushMessage(self.tr("Warning"),
        #                                         self.tr("Some Ids are not defined. Commit before and try again."),
        #                                         level=1, duration=5)
        #     return False

        mylayersNames = self.complementaryLayers
        for layer in layers:
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if self.getLayerPath(layer) == layerPath:
                    fids = []
                    ids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        id = str(feature["Id"])
                        if id == "NULL":
                            message = self.tr("Some Ids are not defined. Commit before and try again.")
                            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                            self.selectedFids = {}
                            return False
                        ids.append(id)
                    if len(fids) > 0:
                        self.selectedFids[layerName] = fids
                    if len(ids) > 0:
                        self.selectedIds[layerName] = ids

        # Generate concatenate string for links and nodes
        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ";"
        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ";"
        return True

    def setSelectedFeaturesById(self):
        layers = self.getLayers()
        mylayersNames = self.ownMainLayers
        for layer in layers:
            openedLayerPath = self.getLayerPath(layer)
            for layerName in mylayersNames:
                layerPath = self.generatePath(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp")
                if layerName == "Sources" or layerName == "Demands":
                    continue
                if openedLayerPath == layerPath:
                    if layerName in self.selectedFids:
                        layer.selectByIds(self.selectedFids[layerName])

    def zoomToElementFromProperties(self, layerName, elementId):
        layers = self.getLayers()
        layer = None
        
        layer_identifier = f"qgisred_{layerName.lower()}"
        
        for la in layers:
            if la.customProperty("qgisred_identifier") == layer_identifier:
                layer = la
                break
                
        if layer:
            features = layer.getFeatures('"Id"=\'' + elementId + "'")
            for feat in features:
                box = feat.geometry().boundingBox()
                self.iface.mapCanvas().setExtent(box)
                self.iface.mapCanvas().refresh()
                return

    def doNothing(self, task=None):
        if task is not None:
            return {"task": task.definition()}

    def transformPoint(self, point):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        pipesCrs = utils.getProjectCrs()
        projectCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        xform = QgsCoordinateTransform(projectCrs, pipesCrs, QgsProject.instance())
        return xform.transform(point)

    """MAIN METHODS"""

    """Toolbars"""

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

    def runExperimentalToolbar(self):
        self.experimentalToolbar.setVisible(not self.experimentalToolbar.isVisible())

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
        webbrowser.open("https://github.com/neslerel/QGISRed/issues")

    """General"""

    def runProjectManager(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)

        # if we need to create project
        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}

        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory

    def runCanOpenProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runOpenProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedUtils().runTask(self.clearQGisProject, self.runOpenProject)

    def runOpenProject(self):
        if not self.checkDependencies():
            return

        if not self.ProjectDirectory == self.TemporalFolder:
            QgsProject.instance().clear()
            self.defineCurrentProject()

        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}

        dlg = QGISRedImportProjectDialog()
        icon_path = ":/images/iconOpenProject.svg"
        dlg.setWindowIcon(QIcon(icon_path))
        dlg.setWindowTitle("QGISRed: Open project")
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            # Write .gql file
            QGISRedUtils().addProjectToGplFile(self.gplFile, self.NetworkName, self.ProjectDirectory)
            # Open files
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            utils.openProjectInQgis()
            utils.enforceAllIdentifiers()

            self.readUnits()

    def runCanCreateProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runCreateProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedUtils().runTask(self.clearQGisProject, self.runCreateProject)

    def runCreateProject(self):
        if not self.checkDependencies():
            return

        if not self.ProjectDirectory == self.TemporalFolder:
            QgsProject.instance().clear()
            self.defineCurrentProject()

        self.opendedLayers = False
        self.especificComplementaryLayers = []
        self.selectedFids = {}
        dlg = QGISRedCreateProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        dlg.exec_()
        self.readUnits()

    def runCanImportData(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runImport()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedUtils().runTask(self.clearQGisProject, self.runImport)

    def runCanAddData(self):
        if not self.checkDependencies():
            return

        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return
        self.runImport()

    def runImport(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            if self.isLayerOnEdition():
                return
        # show the dialog
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)

        # Run the dialog event loop
        dlg.exec_()

    def runCloseProject(self):
        self.iface.newProject(True)

    def runSaveActionProject(self):
        self.iface.mainWindow().findChild(QAction, "mActionSaveProject").trigger()
        self.iface.messageBar().pushMessage(self.tr("Info"), self.tr("Project saved"), level=0, duration=5)

    def runChangeCrs(self):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ChangeCrs(self.ProjectDirectory, self.NetworkName, self.specificEpsg)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            pass
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    """Project"""

    def runSettings(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.EditSettings(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(self.tr("Info"), self.tr("Project options updated"), level=0, duration=5)
        elif resMessage == "False":
            warningMessage = self.tr("Some issues occurred in the process")
            self.iface.messageBar().pushMessage(self.tr("Warning"), warningMessage, level=1, duration=5)
        elif resMessage == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runEditProject(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return
        # show the dialog
        dlg = QGISRedLayerManagementDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        # Run the dialog event loop
        dlg.exec_()

    def runCreateBackup(self):
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        path = utils.saveBackup()
        self.iface.messageBar().pushMessage("QGISRed", self.tr("Backup stored in: " + path), level=0, duration=5)

    def runOpenedQgisProject(self):
        # Reset the unloading flag since we're opening a new project
        self.isUnloading = False
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            return
        
        self.readUnits(self.ProjectDirectory, self.NetworkName)
        
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.assignLayerIdentifiers()

        QGISRedUtils().addProjectToGplFile(self.gplFile, self.NetworkName, self.ProjectDirectory)
        
        layers = self.getLayers()
        
        root = QgsProject.instance().layerTreeRoot()
        inputs_group = root.findGroup("Inputs")
        
        if inputs_group:
            input_layers = []
            for child in inputs_group.children():
                if isinstance(child, QgsLayerTreeLayer):
                    input_layers.append(child.layer())

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.updateMetadata()

    def runClearedProject(self):
        # Set flag to prevent DLL calls during shutdown
        self.isUnloading = False

        # Invalidate the DLL instance
        self.gisredDll = None

        # Deactivate all map tools to prevent callbacks during cleanup
        try:
            if hasattr(self, 'myMapTools'):
                for tool_name, tool in list(self.myMapTools.items()):
                    try:
                        if tool is not None:
                            if self.iface.mapCanvas().mapTool() is tool:
                                self.iface.mapCanvas().unsetMapTool(tool)
                            tool.deactivate()
                    except Exception:
                        pass
                self.myMapTools.clear()
        except Exception:
            pass

        # Disconnect and close all dock widgets
        self.cleanupDocks()

    def runAnalysisOptions(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AnalysisOptions(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if "True" in resMessage:
            resMessage = resMessage.replace("True:", "")
            self.unitsAction.setText("QGISRed: " + resMessage)
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = QGISRedUtils().getProjectExtent()
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "commit":
            self.processCsharpResult(resMessage, "Pipe's roughness converted")
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runDefaultValues(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.DefaultValues(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = QGISRedUtils().getProjectExtent()
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runMaterials(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Materials(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = QGISRedUtils().getProjectExtent()
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runSummary(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Summary(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            pass
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runModel(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Results Dock
        if self.ResultDockwidget is None:
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.ResultDockwidget)
            self.ResultDockwidget.visibilityChanged.connect(self.activeInputGroup)
            self.ResultDockwidget.simulationFinished.connect(self.refreshTimeSeries)
            self.ResultDockwidget.resultPropertyChanged.connect(self.refreshTimeSeries)
        self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        self.connectElementExplorerToResultsDock()

    def runShowResultsDock(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.ResultDockwidget is None:
            self.runModel()
        else:
            self.ResultDockwidget.show()
            self.ResultDockwidget.raise_()
            self.connectElementExplorerToResultsDock()
        self.ResultDockwidget.tabWidget.setCurrentIndex(0)

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

    def runOpenStatusReport(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Open Results dock and switch to Report tab
        if self.ResultDockwidget is None:
            self.runModel()
        else:
            self.ResultDockwidget.show()
            self.ResultDockwidget.raise_()
            self.connectElementExplorerToResultsDock()
        self.ResultDockwidget.tabWidget.setCurrentIndex(1)

    def runExportInp(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ExportToInp(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(
                self.tr("Information"), self.tr("INP file successfully exported"), level=3, duration=5
            )
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif not resMessage == "Cancelled":
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runTimeSeries(self):
        if self.timeSeriesButton.isChecked():
            # 1. Basic Validations
            self.defineCurrentProject()
            if not self.isValidProject() or self.isLayerOnEdition():
                self.iface.messageBar().pushMessage(
                    self.tr("Time Series"), 
                    self.tr("Necessary to have a valid project and no layer on edition."), 
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            # 2. Results Validation
            results_ready = False
            if hasattr(self, 'ResultDockwidget') and self.ResultDockwidget:
                # check if results dock matches current project
                if self.ResultDockwidget.isCurrentProject():
                    # check if .out file exists
                    out_path = getattr(self.ResultDockwidget, "outPath", "")
                    if out_path and os.path.exists(out_path):
                        results_ready = True

            if not results_ready:
                self.iface.messageBar().pushMessage(
                    self.tr("Time Series"), 
                    self.tr("It is necessary to simulate first."), 
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            self.runTimeSeriesSelectPointTool()
            if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
                self.timeSeriesDock = QGISRedTimeSeriesDock(self.iface)
                self.timeSeriesDock.visibilityChanged.connect(self.timeSeriesDockVisibilityChanged)
                self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.timeSeriesDock)
            self.timeSeriesDock.show()
            self.timeSeriesDock.raise_()
            self.timeSeriesDock.setFocus()
        else:
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools["TimeSeries"]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])

    def runTimeSeriesSelectPointTool(self):
        self.myMapTools["TimeSeries"] = QGISRedSelectPointTool(self.timeSeriesButton, self, self.timeSeriesCallback, 2, cursor=":/images/iconTimeSeries.svg")
        self.iface.mapCanvas().setMapTool(self.myMapTools["TimeSeries"])

    def timeSeriesDockVisibilityChanged(self, visible):
        if not visible:
            self.timeSeriesButton.setChecked(False)
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools.get("TimeSeries"):
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])

    def timeSeriesCallback(self, point):
        self.updateTimeSeriesPlot(point)

    def updateTimeSeriesPlot(self, point):
        if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
            return

        # Identify element
        # Tolerance in map units
        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance, point.x() + tolerance, point.y() + tolerance)
        
        found_feature = None
        category = "" # "Node" or "Link"
        
        # Priority layers by their QGISRed identifier
        layers_to_check = [
            ("qgisred_junctions", "Node"), ("qgisred_tanks", "Node"), ("qgisred_reservoirs", "Node"),
            ("qgisred_pipes", "Link"), ("qgisred_valves", "Link"), ("qgisred_pumps", "Link")
        ]
        
        for identifier, cat in layers_to_check:
            # Find layer by identifier
            layer = None
            for l in QGISRedUtils().getLayers():
                if l.customProperty("qgisred_identifier") == identifier:
                    layer = l
                    break
            
            if layer:
                for feature in layer.getFeatures(rect):
                    found_feature = feature
                    category = cat
                    break
            if found_feature: break
            
        if not found_feature:
            self.iface.messageBar().pushMessage(self.tr("Time Series"), self.tr("No network element found at this location."), level=1)
            return

        self.lastTimeSeriesFeature = found_feature
        self.lastTimeSeriesCategory = category
        self.lastTimeSeriesLayer = layer
        self.performTimeSeriesPlotUpdate(found_feature, category, layer)

    def getUnitSystem(self):
        """Determine if the project uses SI or US units based on the status bar text."""
        if hasattr(self, 'unitsAction'):
            text = self.unitsAction.text()
            # Common US units in EPANET: CFS, GPM, MGD, IMGD, AFD
            us_flow_units = ["CFS", "GPM", "MGD", "IMGD", "AFD"]
            for unit in us_flow_units:
                if unit in text.upper():
                    return "US"
        return "SI"

    def getPropertyUnit(self, category, prop_internal):
        """Fetch the unit abbreviation for a property from qgisred_units.json."""
        try:
            if not category or not prop_internal:
                return ""
                
            units_path = os.path.join(self.plugin_dir, "defaults", "qgisred_units.json")
            if not os.path.exists(units_path):
                return ""
            
            with open(units_path, "r", encoding="utf-8") as f:
                units_data = json.load(f)
            
            system = self.getUnitSystem()
            
            # Map internal property names to JSON keys
            prop_map = {
                ("Node", "Pressure"): "qgisred_results_node_pressure",
                ("Node", "Head"): "qgisred_results_node_head",
                ("Node", "Demand"): "qgisred_results_node_demand",
                ("Node", "Quality"): "qgisred_results_node_quality",
                ("Link", "Flow"): "qgisred_results_link_flow",
                ("Link", "Velocity"): "qgisred_results_link_velocity",
                ("Link", "HeadLoss"): "qgisred_results_link_headloss",
                ("Link", "UnitHdLoss"): "qgisred_results_link_unitheadloss",
                ("Link", "FricFactor"): "qgisred_results_link_frictionfactor",
                ("Link", "ReactRate"): "qgisred_results_link_reactrate",
                ("Link", "Quality"): "qgisred_results_link_quality"
            }
            
            key = prop_map.get((category, prop_internal))
            if not key:
                return ""
                
            cat_key = "Nodes" if category == "Node" else "Links"
            prop_data = units_data.get(cat_key, {}).get(key, {})
            
            unit_info = prop_data.get(system)
            if not unit_info:
                return ""
                
            abbr = unit_info.get("abbr", "")
            name = unit_info.get("name", "")
            
            if name == "Same as Flow" or not abbr or abbr == "-":
                # Recursively get flow units
                flow_key = "qgisred_results_link_flow"
                flow_data = units_data.get("Links", {}).get(flow_key, {}).get(system, {})
                return flow_data.get("abbr", "")
                
            return abbr
        except Exception:
            return ""

    def performTimeSeriesPlotUpdate(self, found_feature, category, layer):
        if found_feature is None:
            return
        element_id = str(found_feature.attribute("ID"))
        
        # Get current magnitude from resultsDock
        prop_internal = ""
        prop_display = ""
        is_stepped = False
        
        if hasattr(self, 'ResultDockwidget') and self.ResultDockwidget:
            if category == "Node":
                prop_display = self.ResultDockwidget.cbNodes.currentText()
                # Map display name to internal
                mapping = {
                    self.ResultDockwidget.lbl_pressure: "Pressure",
                    self.ResultDockwidget.lbl_head: "Head",
                    self.ResultDockwidget.lbl_demand: "Demand",
                    self.ResultDockwidget.lbl_quality: "Quality"
                }
                prop_internal = mapping.get(prop_display, "Pressure")
            else:
                prop_display = self.ResultDockwidget.cbLinks.currentText()
                mapping = {
                    self.ResultDockwidget.lbl_flow: "Flow",
                    self.ResultDockwidget.lbl_velocity: "Velocity",
                    self.ResultDockwidget.lbl_headloss: "HeadLoss",
                    self.ResultDockwidget.lbl_unit_headloss: "UnitHdLoss",
                    self.ResultDockwidget.lbl_friction_factor: "FricFactor",
                    self.ResultDockwidget.lbl_status: "Status",
                    self.ResultDockwidget.lbl_reaction_rate: "ReactRate",
                    self.ResultDockwidget.lbl_quality: "Quality",
                    self.ResultDockwidget.lbl_signed_flow: "Flow",
                    self.ResultDockwidget.lbl_unsigned_flow: "Flow"
                }
                prop_internal = mapping.get(prop_display, "Flow")
                if prop_internal == "Status":
                    is_stepped = True

        out_path = getattr(self.ResultDockwidget, "outPath", "")
        if not os.path.exists(out_path):
            self.iface.messageBar().pushMessage(self.tr("Time Series"), self.tr("Results file not found. Please run the model."), level=1)
            return
            
        from .tools.qgisred_results import getOut_TimesNodeProperty, getOut_TimesLinkProperty, _get_out_file_metadata
        
        y_data = []
        if category == "Node":
            y_data = getOut_TimesNodeProperty(out_path, element_id, prop_internal)
        else:
            y_data = getOut_TimesLinkProperty(out_path, element_id, prop_internal)
            
        if not y_data:
            return

        # Simple time series (hours)
        with open(out_path, 'rb') as f:
            meta = _get_out_file_metadata(f)
            report_start = meta["report_start"]
            report_step = meta["report_step"]
            num_periods = meta["num_periods"]
            x_data = [(report_start + i * report_step) / 3600.0 for i in range(num_periods)]

        title = f"{category} {element_id}: {prop_display}"
        
        # Refine title with specific type from layer if possible
        if layer:
            identifier = layer.customProperty("qgisred_identifier")
            type_mapping = {
                "qgisred_junctions": self.tr("Junction"),
                "qgisred_tanks": self.tr("Tank"),
                "qgisred_reservoirs": self.tr("Reservoir"),
                "qgisred_pipes": self.tr("Pipe"),
                "qgisred_valves": self.tr("Valve"),
                "qgisred_pumps": self.tr("Pump")
            }
            specific_type = type_mapping.get(identifier, category)
            title = f"{specific_type} {element_id} - {prop_display}"

        y_categorical_labels = None
        y_label_with_unit = prop_display
        if prop_internal == "Status":
            is_stepped = True
            # Map category strings to numbers: Closed -> 0, Active -> 1, Open -> 2
            mapped_data = []
            for status in y_data:
                status_upper = str(status).upper()
                if "CLOSED" in status_upper:
                    mapped_data.append(0)
                elif "ACTIVE" in status_upper:
                    mapped_data.append(1)
                elif "OPEN" in status_upper:
                    mapped_data.append(2)
                else:
                    mapped_data.append(0) # Default to closed if unknown
            y_data = mapped_data
            y_categorical_labels = [self.tr("Closed"), self.tr("Active"), self.tr("Open")]
        else:
            unit_abbr = self.getPropertyUnit(category, prop_internal)
            if unit_abbr:
                y_label_with_unit = f"{prop_display} ({unit_abbr})"

        self.timeSeriesDock.updatePlot(x_data, y_data, title, self.tr("Time") + " (h)", y_label_with_unit, is_stepped, y_categorical_labels)

    def refreshTimeSeries(self):
        if hasattr(self, 'timeSeriesDock') and self.timeSeriesDock:
            self.performTimeSeriesPlotUpdate(self.lastTimeSeriesFeature, self.lastTimeSeriesCategory, self.lastTimeSeriesLayer)

    def runLegendChanged(self):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if not self.removingLayers:
            # Validations
            self.defineCurrentProject()
            if self.ProjectDirectory == self.TemporalFolder:
                return

            if not self.checkDependencies():
                return

            self.updateMetadata()

    """Edition"""

    def runPaintPipe(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.addPipeButton.setChecked(False)
            return

        tool = "createPipe"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.addPipeButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedCreatePipeTool(
                self.addPipeButton, self.iface, self.ProjectDirectory, self.NetworkName, self.runCreatePipe
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreatePipe(self, points):
        pipePoints = ""
        for p in points:
            p = self.transformPoint(p)
            pipePoints = pipePoints + str(p.x()) + ":" + str(p.y()) + ";"
        # Process:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddPipe(self.ProjectDirectory, self.NetworkName, self.tempFolder, pipePoints)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "Pipe added")

    def runSelectTankPoint(self):
        tool = "pointTank"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addTankButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addTankButton, self, self.runAddTank)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddTank(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddTank(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectReservoirPoint(self):
        tool = "pointReservoir"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addReservoirButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addReservoirButton, self, self.runAddReservoir)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddReservoir(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddReservoir(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectValvePoint(self):
        tool = "pointValve"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.insertValveButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.insertValveButton, self, self.runInsertValve, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runInsertValve(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.InsertValve(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPumpPoint(self):
        tool = "pointPump"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.insertPumpButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.insertPumpButton, self, self.runInsertPump, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runInsertPump(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.InsertPump(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectElements(self):
        tool = "selectElements"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            self.myMapTools[tool] = QGISRedMultiLayerSelection(self.iface, self.iface.mapCanvas(), self.selectElementsButton)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMoveElements(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveElementsButton.setChecked(False)
            return

        oldTool = "moveVertexs"
        if oldTool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[oldTool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[oldTool])

        tool = "moveNodes"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.moveElementsButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedMoveNodesTool(
                self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CrossCursor)

    def runEditLinkGeometry(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveVertexsButton.setChecked(False)
            return

        oldTool = "moveNodes"
        if oldTool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[oldTool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[oldTool])

        tool = "moveVertexs"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.moveVertexsButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedEditLinksGeometryTool(
                self.moveVertexsButton, self.iface, self.ProjectDirectory, self.NetworkName
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CrossCursor)

    def canReverseLink(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.reverseLinkButton.setChecked(False)
            return

        if not self.getSelectedFeaturesIds():
            self.reverseLinkButton.setChecked(False)
            return

        if self.linkIds == "" and not "ServiceConnections" in self.selectedIds:
            self.runSelectReverseLinkPoint()
            return
        self.reverseLinkButton.setChecked(False)

        if self.isLayerOnEdition():
            return

        self.runReverseLink(None)

    def runSelectReverseLinkPoint(self):
        tool = "pointReverseLink"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.reverseLinkButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.reverseLinkButton, self, self.runReverseLink, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runReverseLink(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        ids = ""
        pointText = ""
        if point is not None:
            point = self.transformPoint(point)
            pointText = str(point.x()) + ":" + str(point.y())
        else:
            for key in self.selectedIds:
                ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReverseLink(self.ProjectDirectory, self.NetworkName, self.tempFolder, pointText, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectSplitPoint(self):
        tool = "pointSplit"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.splitPipeButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.splitPipeButton, self, self.runSplitPipe, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runSplitPipe(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SplitPipe(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToMergeSplit(self):
        tool = "mergeSplitPoint"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.mergeSplitJunctionButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.mergeSplitJunctionButton, self, self.runMergeSplitPoints, 3)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMergeSplitPoints(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = self.transformPoint(point2)
            point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SplitMergeJunction(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToTconnections(self):
        tool = "createReverseTconn"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.createReverseTconButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.createReverseTconButton, self, self.runCreateRemoveTconnections, 5
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateRemoveTconnections(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = self.transformPoint(point2)
            point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CreateReverseTConnection(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToCrossings(self):
        tool = "createReverseCross"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.createReverseCrossButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.createReverseCrossButton, self, self.runCreateRemoveCrossings, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateRemoveCrossings(self, point1):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        # Important, no snapping in crossings
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CreateReverseCrossings(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, tolerance)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectValvePumpPoints(self):
        tool = "moveValvePump"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.moveValvePumpButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.moveValvePumpButton, self, self.runMoveValvePump, 4)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMoveValvePump(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point2 = self.transformPoint(point2)
        point1 = str(point1.x()) + ":" + str(point1.y())
        point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.MoveValvePump(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectElementStatusPoint(self):
        tool = "pointElementStatus"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.changeStatusButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.changeStatusButton, self, self.runChangeStatus, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runChangeStatus(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["IsolationValves", "Meters", "ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ChangeStatus(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def canDeleteElements(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.removeElementsButton.setChecked(False)
            return

        if not self.getSelectedFeaturesIds():
            self.removeElementsButton.setChecked(False)
            return
        if len(self.selectedIds) == 0:
            self.runSelectDeleteElementPoint()
            return
        self.removeElementsButton.setChecked(False)

        if self.isLayerOnEdition():
            return

        self.runDeleteElement(None)

    def runSelectDeleteElementPoint(self):
        tool = "pointDeleteElement"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.removeElementsButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.removeElementsButton, self, self.runDeleteElement, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runDeleteElement(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        pointText = ""
        if point is not None:
            point = self.transformPoint(point)
            pointText = str(point.x()) + ":" + str(point.y())

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.RemoveElements(self.ProjectDirectory, self.NetworkName, self.tempFolder, pointText, ids)
        QApplication.restoreOverrideCursor()

        self.selectedFids = {}
        self.processCsharpResult(resMessage, "")

    def runSelectPointProperties(self):
        tool = "pointElement"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.editElementButton.setChecked(False)
        else:
            self.gisredDll = None
            self.myMapTools[tool] = QGISRedSelectPointTool(self.editElementButton, self, self.runProperties, 2, cursor=":/images/pencil.svg", icon_size=24)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runProperties(self, point):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not point == "":
            point = self.transformPoint(point)
            point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        if self.gisredDll is None:
            self.gisredDll = GISRed.CreateInstance()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.EditElements(self.gisredDll, self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        if resMessage == "Select":
            self.blockLayers(True)
        elif resMessage.startswith("["):
            self.blockLayers(True)
            comp = resMessage.split("]")
            layerName = comp[0].replace("[", "")
            elementId = comp[1]
            self.zoomToElementFromProperties(layerName, elementId)

            self.runProperties("")
        else:
            self.processCsharpResult(resMessage, "")
            self.gisredDll = None
            self.blockLayers(False)

    def runPatternsCurves(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.EditPatternsCurves(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runControls(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.EditControls(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    """Debug"""

    def runCommit(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Commit(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, QCoreApplication.translate("QGISRed", "Input data is valid"))

    def runCheckOverlappingElements(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckOverlappingElements(
            self.ProjectDirectory, self.NetworkName, self.tempFolder, self.nodeIds, self.linkIds
        )
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, QCoreApplication.translate("QGISRed", "No overlapping elements found"))

    def runSimplifyVertices(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckAlignedVertices(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, QCoreApplication.translate("QGISRed", "No aligned vertices to delete"))

    def runCheckJoinPipes(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckJoinPipes(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, QCoreApplication.translate("QGISRed", "No pipes to join"))

    def runCheckTConncetions(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckTConnections(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, QCoreApplication.translate("QGISRed", "No T connections to create"))

    def runCheckConnectivityM(self):
        self.runCheckConnectivity()

    def runCheckConnectivityC(self):
        self.runCheckConnectivity(True)

    def runCheckConnectivity(self, toCommit=False):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        linesToDelete = "0"
        if toCommit:
            dlg = QGISRedConnectivityToolDialog()
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if result:
                linesToDelete = dlg.Lines
            else:
                return

        step = "check"
        if toCommit:
            step = "commit"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckConnectivity(self.ProjectDirectory, self.NetworkName, linesToDelete, step, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenConnectivityLayers = False
        if resMessage == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Only one zone"), level=3, duration=5)
        elif resMessage == "False":
            pass
        elif resMessage == "shps":
            self.hasToOpenConnectivityLayers = True
        elif resMessage == "commit/shps":
            self.hasToOpenNewLayers = True
            self.hasToOpenConnectivityLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.extent = QGISRedUtils().getProjectExtent()
        if self.hasToOpenNewLayers and self.hasToOpenConnectivityLayers:
            QGISRedUtils().runTask(self.removeLayersAndConnectivity, self.runOpenTemporaryFiles)
        elif self.hasToOpenConnectivityLayers:
            QGISRedUtils().runTask(self.removeLayersConnectivity, self.runOpenTemporaryFiles)

    def runCheckLengths(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        dlg = QGISRedLengthToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        if dlg.ProcessDone:
            # Process
            if not self.getSelectedFeaturesIds():
                return
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.CheckLengths(
                self.ProjectDirectory, self.NetworkName, dlg.Tolerance, self.tempFolder, self.linkIds
            )
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, self.tr("No one pipe's length out of tolerance"))

    def runCheckDiameters(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckDiameters(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(
                self.tr("Information"), QCoreApplication.translate("QGISRed", "No issues on diameter checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runCheckMaterials(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckMaterials(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(
                self.tr("Information"), self.tr("No issues on materials checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runCheckInstallationDates(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CheckInstallationDates(self.ProjectDirectory, self.NetworkName, self.linkIds)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(
                self.tr("Information"), self.tr("No issues on installation dates checking"), level=3, duration=5
            )
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runHydraulicSectors(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.Sectors = "HydraulicSectors"
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.HydarulicSectors(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        if resMessage == "False":
            pass
        elif resMessage == "shps":
            self.hasToOpenSectorLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.extent = QGISRedUtils().getProjectExtent()
        if self.hasToOpenSectorLayers:
            QGISRedUtils().runTask(self.removeSectorLayers, self.runOpenTemporaryFiles)

    """Tools"""

    def runDemandsManager(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.getSelectedFeaturesIds()
        ids = ""
        if "Junctions" in self.selectedIds:
            ids = "Junctions:" + str(self.selectedIds["Junctions"]) + ";"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.DemandsManager(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")
        self.selectedFids = {}

    def runScenarioManager(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ScenarioManager(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runIsolatedSegments(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        resMessage = "Select"
        tool = "pointIsolatedSegment"
        if point == True or point == False:
            point = ""
            self.gisredDll = None
        if not point == "":
            point = self.transformPoint(point)
            point = str(point.x()) + ":" + str(point.y())

            # Process
            if self.gisredDll is None:
                self.gisredDll = GISRed.CreateInstance()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.IsolatedSegments(self.gisredDll, self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
            QApplication.restoreOverrideCursor()

        if resMessage == "False" or resMessage == "Cancelled":
            return
        elif resMessage == "Select":
            self.blockLayers(True)
            self.myMapTools[tool] = QGISRedSelectPointTool(self.isolatedSegmentsButton, self, self.runIsolatedSegments, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
        elif "shps" in resMessage:
            if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
                self.isolatedSegmentsButton.setChecked(False)
            self.gisredDll = None
            self.blockLayers(False)
            # self.treeName = resMessage.split("^")[1]
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeIsolatedSegmentsLayers, self.runLoadIsolatedSegmentLayers)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runLoadIsolatedSegmentLayers(self):
        # Process
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        try:  # create directory if does not exist
            os.stat(queriesFolder)
        except Exception:
            os.mkdir(queriesFolder)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReplaceTemporalFiles(queriesFolder, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.openIsolatedSegmentsLayers()
        self.removingLayers = False

        # Message
        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def openIsolatedSegmentsLayers(self):
        # Open layers
        isoaltedSegmentsGroup = self.getIsolatedSegmentsGroup()
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        utils = QGISRedUtils(queriesFolder, self.NetworkName, self.iface)
        utils.openIsolatedSegmentsLayer(isoaltedSegmentsGroup, "Links")
        utils.openIsolatedSegmentsLayer(isoaltedSegmentsGroup, "Nodes")

    def getIsolatedSegmentsGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Isolated Segments"])

    def removeIsolatedSegmentsLayers(self):
        path = os.path.join(self.ProjectDirectory, "Queries")
        utils = QGISRedUtils(path, self.NetworkName, self.iface)
        utils.removeLayers(["IsolatedSegments_Links", "IsolatedSegments_Nodes"])

    def runCalculateLengths(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CalculateLengths(self.ProjectDirectory, self.NetworkName, self.tempFolder, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runSetRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SetRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runConvertRoughness(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        if not self.getSelectedFeaturesIds():
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ConvertRoughness(self.ProjectDirectory, self.NetworkName, self.tempFolder, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, self.tr("No issues ocurred"))

    def runElevationInterpolation(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.ElevationFiles = ""
        qfd = QFileDialog()
        path = ""
        filter = "asc(*.asc)"
        f = QFileDialog.getOpenFileNames(qfd, "Select ASC file", path, filter)
        if not f[1] == "":
            for fil in f[0]:
                self.ElevationFiles = self.ElevationFiles + fil + ";"

            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.ElevationInterpolation(
                self.ProjectDirectory, self.NetworkName, self.tempFolder, self.ElevationFiles
            )
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, self.tr("Any elevation has been estimated"))

    def runDemandSectors(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.Sectors = "DemandSectors"
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.DemandSectors(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        if resMessage == "False":
            pass
        elif resMessage == "shps":
            self.hasToOpenSectorLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

        self.removingLayers = True
        self.extent = QGISRedUtils().getProjectExtent()
        if self.hasToOpenSectorLayers:
            QGISRedUtils().runTask(self.removeSectorLayers, self.runOpenTemporaryFiles)

    """"""

    def runPaintServiceConnection(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.addServConnButton.setChecked(False)
            return

        tool = "createConnection"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.addServConnButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedCreateConnectionTool(
                self.addServConnButton,
                self.iface,
                self.ProjectDirectory,
                self.NetworkName,
                self.runCreateServiceConnection,
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateServiceConnection(self, points):
        pipePoints = ""
        for p in points:
            p = self.transformPoint(p)
            pipePoints = pipePoints + str(p.x()) + ":" + str(p.y()) + ";"
        # Process:
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddConnection(self.ProjectDirectory, self.NetworkName, self.tempFolder, pipePoints)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "Service Connection added")

    def runSelectIsolationValvePoint(self):
        tool = "pointIsolationValve"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addIsolationValveButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addIsolationValveButton, self, self.runAddIsolationValve, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddIsolationValve(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddIsolationValve(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectMeterPoint(self, action=None):
        tool = "pointMeter" + self.currentMeter
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            action.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(action, self, self.runAddMeter, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runSelectDefaultMeterPoint(self):
        self.runSelectMeterPoint(self.addMeterDropButton.defaultAction())

    def runSelectAutoMeterPoint(self):
        self.currentMeter = "Undefined"
        self.addMeterDropButton.setDefaultAction(self.addAutoMeterButton)
        self.runSelectMeterPoint(self.addAutoMeterButton)

    def runSelectManometerPoint(self):
        self.currentMeter = "Manometer"
        self.addMeterDropButton.setDefaultAction(self.addManometerButton)
        self.runSelectMeterPoint(self.addManometerButton)

    def runSelectFlowmeterPoint(self):
        self.currentMeter = "Flowmeter"
        self.addMeterDropButton.setDefaultAction(self.addFlowmeterButton)
        self.runSelectMeterPoint(self.addFlowmeterButton)

    def runSelectCountermeterPoint(self):
        self.currentMeter = "Countermeter"
        self.addMeterDropButton.setDefaultAction(self.addCountermeterButton)
        self.runSelectMeterPoint(self.addCountermeterButton)

    def runSelectLevelSensorPoint(self):
        self.currentMeter = "LevelSensor"
        self.addMeterDropButton.setDefaultAction(self.addLevelSensorButton)
        self.runSelectMeterPoint(self.addLevelSensorButton)

    def runSelectDifferentialManometerPoint(self):
        self.currentMeter = "DifferentialManometer"
        self.addMeterDropButton.setDefaultAction(self.addDifferentialManometerButton)
        self.runSelectMeterPoint(self.addDifferentialManometerButton)

    def runSelectQualitySensorPoint(self):
        self.currentMeter = "QualitySensor"
        self.addMeterDropButton.setDefaultAction(self.addQualitySensorButton)
        self.runSelectMeterPoint(self.addQualitySensorButton)

    def runSelectEnergySensorPoint(self):
        self.currentMeter = "EnergySensor"
        self.addMeterDropButton.setDefaultAction(self.addEnergySensorButton)
        self.runSelectMeterPoint(self.addEnergySensorButton)

    def runSelectStatusSensorPoint(self):
        self.currentMeter = "StatusSensor"
        self.addMeterDropButton.setDefaultAction(self.addStatusSensorButton)
        self.runSelectMeterPoint(self.addStatusSensorButton)

    def runSelectValveOpeningPoint(self):
        self.currentMeter = "ValveOpening"
        self.addMeterDropButton.setDefaultAction(self.addValveOpeningButton)
        self.runSelectMeterPoint(self.addValveOpeningButton)

    def runSelectTachometerPoint(self):
        self.currentMeter = "Tachometer"
        self.addMeterDropButton.setDefaultAction(self.addTachometerButton)
        self.runSelectMeterPoint(self.addTachometerButton)

    def runAddMeter(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["Meters"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddMeter(self.ProjectDirectory, self.NetworkName, self.tempFolder, point, self.currentMeter)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runLoadReadings(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_ServiceConnections.shp")):
        #     self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
        #         "Does not exist ServiceConnections SHP file"), level=1, duration=5)
        #     return

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.LoadReadings(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runLoadScada(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        self.especificComplementaryLayers = ["Meters"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.LoadScada(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSetPipeStatus(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_IsolationValves.shp")):
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Does not exist Isolation Valves SHP file"), level=1, duration=5
            )
            return

        # Process
        self.especificComplementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SetInitialStatusPipes(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runAddConnections(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_ServiceConnections.shp")):
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Does not exist ServiceConnections SHP file"), level=1, duration=5
            )
            return

        # Question
        dlg = QGISRedServiceConnectionsToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        if not dlg.ProcessDone:
            return

        asNode = "true"
        if dlg.AsPipes:
            asNode = "false"

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddConnections(self.ProjectDirectory, self.NetworkName, asNode, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No Service Connections to include in the model")

    def runAddHydrants(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Hydrants.shp")):
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Does not exist Hydrants SHP file"), level=1, duration=5
            )
            return

        # Process
        self.especificComplementaryLayers = ["Hydrants"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddHydrants(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No Hydrants to include in the model")

    def runAddPurgeValves(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_WashoutValves.shp")):
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Does not exist Washout Valves SHP file"), level=1, duration=5
            )
            return

        # Process
        self.especificComplementaryLayers = ["WashoutValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddWashoutValves(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No Washout Valves to include in the model")

    """Tree Graph"""

    def runTree(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = ""
        if point is not False:
            point = self.transformPoint(point)
            point1 = str(point.x()) + ":" + str(point.y())

        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Tree(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1)
        QApplication.restoreOverrideCursor()

        # Action
        if resMessage == "False" or resMessage == "Cancelled":
            return
        elif resMessage == "Select":
            self.selectPointToTree()
        elif "shps" in resMessage:
            self.treeName = resMessage.split("^")[1]
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeTreeLayers, self.runTreeProcess)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runTreeProcess(self):
        # Process
        treeFolder = os.path.join(self.ProjectDirectory, "Trees")
        try:  # create directory if does not exist
            os.stat(treeFolder)
        except Exception:
            os.mkdir(treeFolder)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReplaceTemporalFiles(treeFolder, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.openTreeLayers()
        self.removingLayers = False

        # Message
        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def selectPointToTree(self):
        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(None, self, self.runTree, 1)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def openTreeLayers(self):
        # Open layers
        treeGroup = self.getTreeGroup()
        treeFolder = os.path.join(self.ProjectDirectory, "Trees")
        utils = QGISRedUtils(treeFolder, self.NetworkName, self.iface)
        utils.openTreeLayer(treeGroup, "Links", self.treeName, link=True)
        utils.openTreeLayer(treeGroup, "Nodes", self.treeName)
        group = self.getInputGroup()
        if group is not None:
            group.setItemVisibilityChecked(False)

    def getTreeGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Tree: " + self.treeName])

    def removeTreeLayers(self):
        treePath = os.path.join(self.ProjectDirectory, "Trees")
        utils = QGISRedUtils(treePath, self.NetworkName, self.iface)
        utils.removeLayers(["Links_Tree_" + self.treeName, "Nodes_Tree_" + self.treeName])
        self.removeEmptyQuerySubGroup("Tree")

    # ======================================
    #              NEW BUTTONS - BID
    # --------------------------------------

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
        dlg.exec_()
    
    def validateProject(self, action):
        # Validates dependencies and project, unchecks action on failure
        if not self.checkDependencies():
            action.setChecked(False)
            return False
        self.defineCurrentProject()
        if not self.isValidProject() or self.isLayerOnEdition():
            action.setChecked(False)
            return False
        return True

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
                dock=dock
            )
            self.myMapTools[toolKey].setCursor(Qt.WhatsThisCursor)
            self.iface.mapCanvas().setMapTool(self.myMapTools[toolKey])
            if dock:
                dock.reHighlightCurrentElement()
                dock.refreshCurrentElement()
        except Exception:
            action.setChecked(False)

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

                self.iface.addDockWidget(Qt.RightDockWidgetArea, dock)
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
                self.iface.addDockWidget(Qt.RightDockWidgetArea, dock)
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

    def runQueriesByAttributes(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.queriesByAttributesDock = QGISRedQueriesByAttributesDock(self.iface)
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.queriesByAttributesDock)
    
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
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.statisticsAndPlotsDock)

    def runLegends(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.legendsDialog = QGISRedLegendsDialog()
        self.legendsDialog.config(self.iface, self.ProjectDirectory, self.NetworkName, self)
        self.legendsDialog.show()