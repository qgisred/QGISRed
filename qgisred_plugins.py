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
from qgis.core import QgsProject, QgsVectorLayer
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu, QFileDialog, QToolButton
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.core import QgsMessageLog, QgsCoordinateTransform
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
from .tools.qgisred_utils import QGISRedUtils
from .tools.qgisred_dependencies import QGISRedDependencies as GISRed
from .tools.qgisred_moveNodes import QGISRedMoveNodesTool
from .tools.qgisred_multilayerSelection import QGISRedMultiLayerSelection
from .tools.qgisred_createPipe import QGISRedCreatePipeTool
from .tools.qgisred_createConnection import QGISRedCreateConnectionTool
from .tools.qgisred_moveVertexs import QGISRedMoveVertexsTool
from .tools.qgisred_selectPoint import QGISRedSelectPointTool
from .tools.qgisred_editConnections import QGISRedEditConnectionsTool
# Others imports
import os
import tempfile
import platform
import base64
import shutil
import webbrowser
import urllib.request
from ctypes import windll, c_uint16, c_uint, wstring_at, byref, cast
from ctypes import create_string_buffer, c_void_p, Structure, POINTER
# MessageBar Levels: Info 0, Warning 1, Critical 2, Success 3


class QGISRed:
    """QGISRed Plugin Implementation."""
    # Common variables
    ResultDockwidget = None
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns", "Materials"]
    especificComplementaryLayers = []
    complementaryLayers = ["IsolationValves", "Hydrants", "WashoutValves",
                           "AirReleaseValves", "ServiceConnections", "Meters"]
    TemporalFolder = "Temporal folder"
    DependenciesVersion = "1.0.13.1"
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

        if not platform.system() == "Windows":
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("QGISRed only works in Windows"),
                                                level=2, duration=5)
            return

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir, 'i18n', 'qgisred_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        # Toolbar
        self.toolbar = self.iface.addToolBar(u'QGISRed')
        self.toolbar.setObjectName(u'QGISRed')
        # Menu
        self.qgisredmenu = QMenu("&QGISRed", self.iface.mainWindow().menuBar())
        actions = self.iface.mainWindow().menuBar().actions()
        lastAction = actions[-1]
        self.iface.mainWindow().menuBar().insertMenu(lastAction, self.qgisredmenu)
        # Status Bar
        self.unitsButton = QToolButton()
        self.unitsButton.setToolButtonStyle(2)
        icon = QIcon(':/plugins/QGISRed/images/qgisred32.png')
        self.unitsAction = QAction(icon, "QGISRed: LPS | H-W", None)
        self.unitsAction.setToolTip("Click to change it")
        self.unitsAction.triggered.connect(self.runAnalysisOptions)
        self.actions.append(self.unitsAction)
        self.unitsButton.setDefaultAction(self.unitsAction)
        self.iface.mainWindow().statusBar().addWidget(self.unitsButton)

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QGISRed', message)

    def add_action(self, icon_path, text, callback, menubar, toolbar,
                   checable=False, actionBase=None, createDrop=False, addActionToDrop=True,
                   enabled_flag=True, add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        # Create the dialog (after translation) and keep reference
        self.dlg = QGISRedCreateProjectDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checable)

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

        dropButton = QToolButton()
        if createDrop:
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
            # self.iface.addPluginToMenu(self.menu,action)
            menubar.addAction(action)

        self.actions.append(action)

        if createDrop:
            return dropButton
        return action

    def addFileMenu(self):
        #    #Menu
        self.fileMenu = self.qgisredmenu.addMenu(self.tr('File'))
        self.fileMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconData.png'))
        #    #Toolbar
        self.fileToolbar = self.iface.addToolBar(self.tr(u'QGISRed File'))
        self.fileToolbar.setObjectName(self.tr(u'QGISRed File'))
        self.fileToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconData.png'
        fileDropButton = self.add_action(icon_path, text=self.tr(u'File'), callback=self.runFileToolbar,
                                         menubar=self.fileMenu, add_to_menu=False, toolbar=self.toolbar,
                                         createDrop=True, addActionToDrop=False,
                                         add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconProjectManager.png'
        self.add_action(icon_path, text=self.tr(u'Project manager'), callback=self.runProjectManager,
                        menubar=self.fileMenu, toolbar=self.fileToolbar, actionBase=fileDropButton,
                        add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLayers.png'
        self.add_action(icon_path, text=self.tr(u'Create project'), callback=self.runCanCreateProject,
                        menubar=self.fileMenu, toolbar=self.fileToolbar, actionBase=fileDropButton,
                        add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconImport.png'
        self.add_action(icon_path, text=self.tr(u'Import data'), callback=self.runCanImportData,
                        menubar=self.fileMenu, toolbar=self.fileToolbar, actionBase=fileDropButton,
                        add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLock.png'
        self.add_action(icon_path, text=self.tr(u'Create backup'), callback=self.runCreateBackup,
                        menubar=self.fileMenu, toolbar=self.fileToolbar, actionBase=fileDropButton,
                        add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCloseProject.png'
        self.add_action(icon_path, text=self.tr(u'Close project'), callback=self.runCloseProject,
                        menubar=self.fileMenu, toolbar=self.fileToolbar, actionBase=fileDropButton,
                        add_to_toolbar=True, parent=self.iface.mainWindow())

    def addProjectMenu(self):
        #    #Menu
        self.projectMenu = self.qgisredmenu.addMenu(self.tr('Project'))
        self.projectMenu.setIcon(QIcon(':/plugins/QGISRed/images/qgisred32.png'))
        #    #Toolbar
        self.projectToolbar = self.iface.addToolBar(
            self.tr(u'QGISRed Project'))
        self.projectToolbar.setObjectName(self.tr(u'QGISRed Project'))
        self.projectToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/qgisred32.png'
        projectDropButton = self.add_action(icon_path, text=self.tr(u'Project'), callback=self.runProjectToolbar,
                                            menubar=self.projectMenu, add_to_menu=False, toolbar=self.toolbar,
                                            createDrop=True,
                                            addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSettings.png'
        self.add_action(icon_path, text=self.tr(u'Project settings'), callback=self.runSettings,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLayerManagement.png'
        self.add_action(icon_path, text=self.tr(u'Layer management'), callback=self.runEditProject,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddData.png'
        self.add_action(icon_path, text=self.tr(u'Add data'), callback=self.runCanAddData, menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydraulicOptions.png'
        self.add_action(icon_path, text=self.tr(u'Analysis options'), callback=self.runAnalysisOptions,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDefaultValues.png'
        self.add_action(icon_path, text=self.tr(u'Default values'), callback=self.runDefaultValues,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMaterials.png'
        self.add_action(icon_path, text=self.tr(u'Materials table'), callback=self.runMaterials,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSummary.png'
        self.add_action(icon_path, text=self.tr(u'Summary'), callback=self.runSummary, menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconFlash.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Run model'), callback=self.runModel,
                                     menubar=self.projectMenu,
                                     toolbar=self.projectToolbar, actionBase=projectDropButton, createDrop=True,
                                     add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconResults.png'
        self.add_action(icon_path, text=self.tr(u'Show results browser'), callback=self.runShowResultsDock,
                        menubar=self.projectMenu, toolbar=self.projectToolbar, actionBase=dropButton,
                        add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconExportEpanet.png'
        self.add_action(icon_path, text=self.tr(u'Export to Epanet'), callback=self.runExportInp,
                        menubar=self.projectMenu,
                        toolbar=self.projectToolbar, actionBase=projectDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())

    def addEditMenu(self):
        #    #Menu
        self.editionMenu = self.qgisredmenu.addMenu(self.tr('Edition'))
        self.editionMenu.setIcon(
            QIcon(':/plugins/QGISRed/images/iconEdit.png'))
        #    #Toolbar
        self.editionToolbar = self.iface.addToolBar(
            self.tr(u'QGISRed Edition'))
        self.editionToolbar.setObjectName(self.tr(u'QGISRed Edition'))
        self.editionToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconEdit.png'
        editDropButton = self.add_action(icon_path, text=self.tr(u'Edition'), callback=self.runEditionToolbar,
                                         menubar=self.editionMenu, add_to_menu=False,
                                         toolbar=self.toolbar, createDrop=True, addActionToDrop=False,
                                         add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPipe.png'
        self.addPipeButton = self.add_action(icon_path, text=self.tr(u'Add pipe'), callback=self.runPaintPipe,
                                             menubar=self.editionMenu, toolbar=self.editionToolbar,
                                             actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                             parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddTank.png'
        self.addTankButton = self.add_action(icon_path, text=self.tr(u'Add tank'), callback=self.runSelectTankPoint,
                                             menubar=self.editionMenu, toolbar=self.editionToolbar,
                                             actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                             parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddReservoir.png'
        self.addReservoirButton = self.add_action(icon_path, text=self.tr(u'Add reservoir'),
                                                  callback=self.runSelectReservoirPoint,
                                                  menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                  actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                  parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddValve.png'
        self.insertValveButton = self.add_action(icon_path, text=self.tr(u'Insert valve in pipe'),
                                                 callback=self.runSelectValvePoint, menubar=self.editionMenu,
                                                 toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                 parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPump.png'
        self.insertPumpButton = self.add_action(icon_path, text=self.tr(u'Insert pump in pipe'),
                                                callback=self.runSelectPumpPoint, menubar=self.editionMenu,
                                                toolbar=self.editionToolbar,
                                                actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                parent=self.iface.mainWindow())

        self.editionToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconSelection.png'
        self.selectElementsButton = self.add_action(icon_path, text=self.tr(u'Select multiple elements'),
                                                    callback=self.runSelectElements, menubar=self.editionMenu,
                                                    toolbar=self.editionToolbar,
                                                    actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                    parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveElements.png'
        self.moveElementsButton = self.add_action(icon_path, text=self.tr(u'Move node elements'),
                                                  callback=self.runMoveElements, menubar=self.editionMenu,
                                                  toolbar=self.editionToolbar,
                                                  actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                  parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveVertexs.png'
        self.moveVertexsButton = self.add_action(icon_path, text=self.tr(u'Edit link vertices'),
                                                 callback=self.runEditVertexs, menubar=self.editionMenu,
                                                 toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                 parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconReverseLink.png'
        self.reverseLinkButton = self.add_action(icon_path, text=self.tr(u'Reverse link'),
                                                 callback=self.canReverseLink, menubar=self.editionMenu,
                                                 toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                 parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSplitPipe.png'
        self.splitPipeButton = self.add_action(icon_path, text=self.tr(u'Split/Join pipe/s'),
                                               callback=self.runSelectSplitPoint, menubar=self.editionMenu,
                                               toolbar=self.editionToolbar,
                                               actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                               parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMergeSplitJunction.png'
        self.mergeSplitJunctionButton = self.add_action(icon_path, text=self.tr(u'Merge/Split junctions'),
                                                        callback=self.runSelectPointToMergeSplit,
                                                        menubar=self.editionMenu,
                                                        toolbar=self.editionToolbar,
                                                        actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateRevTconn.png'
        self.createReverseTconButton = self.add_action(icon_path, text=self.tr(u'Create/Reverse T connections'),
                                                       callback=self.runSelectPointToTconnections,
                                                       menubar=self.editionMenu,
                                                       toolbar=self.editionToolbar,
                                                       actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                       parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateRevCrossings.png'
        self.createReverseCrossButton = self.add_action(icon_path, text=self.tr(u'Create/Reverse crossings'),
                                                        callback=self.runSelectPointToCrossings,
                                                        menubar=self.editionMenu,
                                                        toolbar=self.editionToolbar,
                                                        actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveValvePump.png'
        self.moveValvePumpButton = self.add_action(icon_path, text=self.tr(u'Move valve/pump to another pipe'),
                                                   callback=self.runSelectValvePumpPoints, menubar=self.editionMenu,
                                                   toolbar=self.editionToolbar,
                                                   actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                   parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDeleteElements.png'
        self.removeElementsButton = self.add_action(icon_path, text=self.tr(u'Delete elements'),
                                                    callback=self.canDeleteElements, menubar=self.editionMenu,
                                                    toolbar=self.editionToolbar,
                                                    actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                    parent=self.iface.mainWindow())
        self.editionToolbar.addSeparator()

        icon_path = ':/plugins/QGISRed/images/iconEdit.png'
        self.editElementButton = self.add_action(icon_path, text=self.tr(u'Edit element properties'),
                                                 callback=self.runSelectPointProperties, menubar=self.editionMenu,
                                                 toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True,
                                                 parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLinePlot.png'
        self.add_action(icon_path, text=self.tr(u'Edit patterns and curves'),
                        callback=self.runPatternsCurves, menubar=self.editionMenu, toolbar=self.editionToolbar,
                        actionBase=editDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRules.png'
        self.add_action(icon_path, text=self.tr(u'Edit controls'),
                        callback=self.runControls, menubar=self.editionMenu, toolbar=self.editionToolbar,
                        actionBase=editDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

    def addVerificationsMenu(self):
        #    #Menu
        self.verificationsMenu = self.qgisredmenu.addMenu(
            self.tr('Verifications'))
        self.verificationsMenu.setIcon(
            QIcon(':/plugins/QGISRed/images/iconCommit.png'))
        #    #Toolbar
        self.verificationsToolbar = self.iface.addToolBar(
            self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setObjectName(
            self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconCommit.png'
        verificationsDropButton = self.add_action(icon_path, text=self.tr(u'Verifications'),
                                                  callback=self.runVerificationsToolbar, menubar=self.verificationsMenu,
                                                  add_to_menu=False,
                                                  toolbar=self.toolbar, createDrop=True, addActionToDrop=False,
                                                  add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCommit.png'
        self.add_action(icon_path, text=self.tr(u'Commit changes'), callback=self.runCommit,
                        menubar=self.verificationsMenu,
                        toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadC.png'
        self.add_action(icon_path, text=self.tr(u'Remove overlapping elements'),
                        callback=self.runCheckOverlappingElements,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconVerticesC.png'
        self.add_action(icon_path, text=self.tr(u'Simplify link vertices'), callback=self.runSimplifyVertices,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconJoinC.png'
        self.add_action(icon_path, text=self.tr(u'Join consecutive pipes (diameter, material and year)'),
                        callback=self.runCheckJoinPipes, menubar=self.verificationsMenu,
                        toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsC.png'
        self.add_action(icon_path, text=self.tr(u'Create T Connections'), callback=self.runCheckTConncetions,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check connectivity'),
                                     callback=self.runCheckConnectivityM,
                                     menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                                     actionBase=verificationsDropButton, createDrop=True, add_to_toolbar=False,
                                     parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityC.png'
        self.add_action(icon_path, text=self.tr(u'Delete issolated subzones'), callback=self.runCheckConnectivityC,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=dropButton, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLengthC.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Check pipe lengths'), callback=self.runCheckLengths,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDiameters.png'
        self.add_action(icon_path, text=self.tr(u'Check diameters'), callback=self.runCheckDiameters,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMaterial.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe materials'), callback=self.runCheckMaterials,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDate.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe installation dates'),
                        callback=self.runCheckInstallationDates,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydraulic.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Obtain hydraulic sectors'), callback=self.runHydraulicSectors,
                        menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

    def addToolsMenu(self):
        #    #Menu
        self.toolsMenu = self.qgisredmenu.addMenu(self.tr('Tools'))
        self.toolsMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconTools.png'))
        #    #Toolbar
        self.toolsToolbar = self.iface.addToolBar(self.tr(u'QGISRed Tools'))
        self.toolsToolbar.setObjectName(self.tr(u'QGISRed Tools'))
        self.toolsToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconTools.png'
        toolDropButton = self.add_action(icon_path, text=self.tr(u'Tools'), callback=self.runToolsToolbar,
                                         menubar=self.toolsMenu, add_to_menu=False,
                                         toolbar=self.toolbar, createDrop=True, addActionToDrop=False,
                                         add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDemands.png'
        self.add_action(icon_path, text=self.tr(u'Demands manager'),
                        callback=self.runDemandsManager, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRoughness.png'
        self.add_action(icon_path, text=self.tr(u'Set roughness coefficient (from Material and Date)'),
                        callback=self.runSetRoughness, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRoughnessConvert.png'
        self.add_action(icon_path, text=self.tr(u'Convert roughness coefficient'),
                        callback=self.runConvertRoughness, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconInterpolate.png'
        self.add_action(icon_path, text=self.tr(u'Interpolate elevation from .asc files'),
                        callback=self.runElevationInterpolation, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        self.toolsToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconDemandSector.png'
        self.add_action(icon_path, text=self.tr(u'Obtain demand sectors'), callback=self.runDemandSectors,
                        menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTree.png'
        self.add_action(icon_path, text=self.tr(u'Minimum Spanning Tree'), callback=self.runTree,
                        menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

    def addDigitalTwinMenu(self):
        #    #Menu
        self.dtMenu = self.qgisredmenu.addMenu(self.tr('Digital Twin'))
        self.dtMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconDigitalTwin.png'))
        #    #Toolbar
        self.dtToolbar = self.iface.addToolBar(self.tr(u'QGISRed Digital Twin'))
        self.dtToolbar.setObjectName(self.tr(u'QGISRed Digital Twin'))
        self.dtToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconDigitalTwin.png'
        dtDropButton = self.add_action(icon_path, text=self.tr(u'Digital Twin'), callback=self.runDtToolbar,
                                       menubar=self.dtMenu, add_to_menu=False,
                                       toolbar=self.toolbar, createDrop=True, addActionToDrop=False,
                                       add_to_toolbar=False, parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/images/iconAddConnection.png'
        self.addServConnButton = self.add_action(icon_path, text=self.tr(u'Add service connection'),
                                                 callback=self.runPaintServiceConnection,
                                                 menubar=self.dtMenu, toolbar=self.dtToolbar,
                                                 actionBase=dtDropButton, add_to_toolbar=True, checable=True,
                                                 parent=self.iface.mainWindow())
        self.dtToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconEditConnection.png'
        self.editServConnButton = self.add_action(icon_path, text=self.tr(u'Edit service connection path'),
                                                  callback=self.runEditServiceConnectionPath,
                                                  menubar=self.dtMenu, toolbar=self.dtToolbar,
                                                  actionBase=dtDropButton, add_to_toolbar=True, checable=True,
                                                  parent=self.iface.mainWindow())
        self.dtToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconSetReadings.png'
        self.add_action(icon_path, text=self.tr(u'Load meter readings'),
                        callback=self.runLoadReadings, menubar=self.dtMenu,
                        toolbar=self.dtToolbar, actionBase=dtDropButton, add_to_toolbar=True,
                        parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconStatus.png'
        self.add_action(icon_path, text=self.tr(u'Set pipe\'s initial status from isolation valves'),
                        callback=self.runSetPipeStatus, menubar=self.dtMenu, toolbar=self.dtToolbar,
                        actionBase=dtDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        self.dtToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconConnections.png'
        self.add_action(icon_path, text=self.tr(u'Add service connections to the model'),
                        callback=self.runAddConnections, menubar=self.dtMenu, toolbar=self.dtToolbar,
                        actionBase=dtDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydrants.png'
        self.add_action(icon_path, text=self.tr(u'Add hydrants to the model'), callback=self.runAddHydrants,
                        menubar=self.dtMenu, toolbar=self.dtToolbar,
                        actionBase=dtDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconPurges.png'
        self.add_action(icon_path, text=self.tr(u'Add washout valves to the model'), callback=self.runAddPurgeValves,
                        menubar=self.dtMenu, toolbar=self.dtToolbar,
                        actionBase=dtDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

    def initGui(self):
        if not platform.system() == "Windows":
            return

        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.addFileMenu()
        self.addProjectMenu()
        self.addEditMenu()
        self.addVerificationsMenu()
        self.addToolsMenu()
        self.addDigitalTwinMenu()

        # About
        icon_path = ':/plugins/QGISRed/images/iconAbout.png'
        self.add_action(icon_path, text=self.tr(u'About...'), callback=self.runAbout,
                        menubar=self.qgisredmenu, toolbar=self.toolbar, parent=self.iface.mainWindow())
        # Report issues
        icon_path = ':/plugins/QGISRed/images/iconGitHub.png'
        self.add_action(icon_path, text=self.tr(u'Report issues or comments...'), callback=self.runReportIssues,
                        menubar=self.qgisredmenu, toolbar=self.toolbar, parent=self.iface.mainWindow())

        # Connecting QGis Events
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)
        QgsProject.instance().layersRemoved.connect(self.runLegendChanged)
        QgsProject.instance().readProject.connect(self.runOpenedQgisProject)

        # MapTools
        self.myMapTools = {}

        # QGISRed dependencies
        self.dllTempFolderFile = os.path.join(QGISRedUtils().getGISRedFolder(), "dllTempFolders.dat")
        QGISRedUtils().copyDependencies()
        self.removeTempFolders()
        # QGISRed updates
        self.checkForUpdates()

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

        QgsMessageLog.logMessage("Loaded sucssesfully", 'QGISRed', level=0)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # dirpath = os.path.join(tempfile._get_default_tempdir(), "qgisred" + self.KeyTemp)
        # if os.path.exists(dirpath) and os.path.isdir(dirpath):
        # shutil.rmtree(dirpath)
        if os.path.exists(self.tempFolder) and os.path.isdir(self.tempFolder):
            shutil.rmtree(self.tempFolder)

        if QGISRedUtils.DllTempoFolder is not None:
            with open(self.dllTempFolderFile, 'a+') as file:
                file.write(QGISRedUtils.DllTempoFolder + '\n')

        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()
            self.iface.removeDockWidget(self.ResultDockwidget)
            self.ResultDockwidget = None

        for action in self.actions:
            self.iface.removeToolBarIcon(action)

        # remove the toolbar
        del self.toolbar
        del self.fileToolbar
        del self.projectToolbar
        del self.editionToolbar
        del self.verificationsToolbar
        del self.toolsToolbar
        del self.dtToolbar

        # remove statusbar label
        self.iface.mainWindow().statusBar().removeWidget(self.unitsButton)

        # remove menus
        if self.fileMenu:
            self.fileMenu.menuAction().setVisible(False)
        if self.projectMenu:
            self.projectMenu.menuAction().setVisible(False)
        if self.editionMenu:
            self.editionMenu.menuAction().setVisible(False)
        if self.verificationsMenu:
            self.verificationsMenu.menuAction().setVisible(False)
        if self.toolsMenu:
            self.toolsMenu.menuAction().setVisible(False)
        if self.dtMenu:
            self.dtMenu.menuAction().setVisible(False)
        if self.qgisredmenu:
            self.qgisredmenu.menuAction().setVisible(False)

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
        ret = windll.version.VerQueryValueW(buffer, wstring_at(r"\VarFileInfo\Translation"),
                                            byref(value), byref(value_size))
        if ret == 0:
            return "0.0.0.0"
        lcp = cast(value, POINTER(LANGANDCODEPAGE))
        language = "{0:04x}{1:04x}".format(lcp.contents.wLanguage, lcp.contents.wCodePage)

        res = windll.version.VerQueryValueW(buffer, wstring_at("\\StringFileInfo\\" + language + "\\" + what),
                                            byref(value), byref(value_size))

        if res == 0:
            return "0.0.0.0"
        return wstring_at(value.value, value_size.value - 1)

    def checkDependencies(self):
        valid = False
        gisredDir = QGISRedUtils().getGISRedDllFolder()
        if os.path.isdir(gisredDir):
            currentVersion = self.getVersion(os.path.join(gisredDir, "GISRed.QGisPlugins.dll"), 'FileVersion')
            if currentVersion == self.DependenciesVersion:
                valid = True
        if not valid:
            link = '\"http://www.redhisp.webs.upv.es/files/QGISRed/' + \
                self.DependenciesVersion + '/QGISRed_Installation.msi\"'
            firstPartMessage = 'QGISRed plugin only runs in Windows OS and needs some dependencies ('
            request = QMessageBox.question(self.iface.mainWindow(), self.tr('QGISRed Dependencies'),
                                           self.tr(firstPartMessage +
                                           self.DependenciesVersion +
                                           '). Do you want to download and authomatically install them?'),
                                           QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No))
            if request == QMessageBox.Yes:
                localFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".msi"
                try:
                    urllib.request.urlretrieve(link.strip('\'"'), localFile)
                    os.system(localFile)
                    os.remove(localFile)
                except Exception:
                    pass
                valid = self.checkDependencies()
                if valid:
                    QGISRedUtils().copyDependencies()

        return valid

    def checkForUpdates(self):
        link = '\"http://www.redhisp.webs.upv.es/files/QGISRed/newVersions.txt\"'
        tempLocalFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".txt"
        try:
            # Read online file
            urllib.request.urlretrieve(link.strip('\'"'), tempLocalFile)
            f = open(tempLocalFile, "r")
            contents = f.read()  # 0.11
            f.close()
            newVersion = contents
            if len(contents.split(".")) == 2:
                newVersion += ".0"  # 0.11.0
            newVersion = "1." + newVersion  # 1.0.11.0
            if(int(newVersion.replace(".", "")) > int(self.DependenciesVersion.replace(".", ""))):
                # Read local file with versions that user don't want to remember
                fileVersions = os.path.join(os.path.join(os.getenv('APPDATA'), "QGISRed"), "updateVersions.dat")
                oldVersions = ""
                if os.path.exists(fileVersions):
                    f = open(fileVersions, "r")
                    oldVersions = f.read()
                    f.close()
                # Review if in local file is the current online version
                if contents not in oldVersions:
                    response = QMessageBox.question(self.iface.mainWindow(), self.tr('QGISRed Updates'),
                                                    self.tr("QGISRed plugin has a new version (" + contents +
                                                            "). You can upgrade it from the QGis plugin manager." +
                                                            "Do you want to remember it again?"),
                                                    QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No))
                    webbrowser.open('https://tr.im/qgisredplugin')
                    # If user don't want to remember a local file is written with this version
                    if response == QMessageBox.No:
                        f = open(fileVersions, "w+")
                        f.write(contents + '\n')
                        f.close()
            os.remove(tempLocalFile)
        except Exception:
            pass

    def removeTempFolders(self):
        if not os.path.exists(self.dllTempFolderFile):
            return
        allDeleted = True
        with open(self.dllTempFolderFile, 'r') as file:
            lines = file.readlines()
            for line in lines:
                filePath = line.strip('\n')
                try:
                    if os.path.exists(filePath) and os.path.isdir(filePath):
                        shutil.rmtree(filePath)
                except Exception:
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
                question = 'Do you want to close the current project and continue?'
                reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Opened project'),
                                             self.tr(question), QMessageBox.Yes, QMessageBox.No)
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
                self.iface.messageBar().pushMessage("Warning",
                                                    "Some layer is in Edit Mode. Plase, commit it before continuing.",
                                                    level=1, duration=5)
                return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                self.iface.messageBar().pushMessage("Warning",
                                                    "The project has changes. Please save them before continuing.",
                                                    level=1, duration=5)
                return False
            else:
                # Close project and continue?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened project',
                                             'Do you want to close the current project and continue?',
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers()) > 0:
                # Close files and continue?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened layers',
                                             'Do you want to close the current layers and continue?',
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def clearQGisProject(self, task):
        QgsProject.instance().clear()
        if task is not None:
            return {'task': task.definition()}

    def isValidProject(self):
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"),
                                                level=1, duration=5)
            return False
        return True

    def isLayerOnEdition(self):
        layers = self.getLayers()
        for layer in layers:
            if layer.isEditable():
                message = "Some layer is in Edit Mode. Please, commit it before continuing."
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(message), level=1)
                return True
        return False

    def readUnits(self, folder="", network=""):
        if folder == "" and network == "":
            self.defineCurrentProject()
        units = "LPS"
        headloss = "D-W"
        if self.ProjectDirectory == "Temporal Folder":
            return
        dbf = QgsVectorLayer(os.path.join(self.ProjectDirectory, self.NetworkName + "_Options.dbf"), "Options", "ogr")
        for feature in dbf.getFeatures():
            attrs = feature.attributes()
            if attrs[1] == "UNITS":
                units = attrs[2]
            if attrs[1] == "HEADLOSS":
                headloss = attrs[2]

        self.unitsAction.setText("QGISRed: " + units + " | " + headloss)
        del dbf

    """Remove Layers"""
    def removeLayers(self, task=None):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        if task is not None:
            return {'task': task.definition()}

    def removeDBFs(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownFiles, ".dbf")
        if task is not None:
            return {'task': task.definition()}

    def removeIssuesLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)
        if task is not None:
            return {'task': task.definition()}

    def removeLayersAndIssuesLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayers(self.issuesLayers)
        if task is not None:
            return {'task': task.definition()}

    def removeIssuesLayersFiles(self):
        dirList = os.listdir(self.ProjectDirectory)
        for fi in dirList:
            if "_Issues." in fi:
                os.remove(os.path.join(self.ProjectDirectory, fi))

    def removeLayersConnectivity(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")
        if task is not None:
            return {'task': task.definition()}

    def removeLayersAndConnectivity(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.especificComplementaryLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")
        if task is not None:
            return {'task': task.definition()}

    def removeSectorLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(["Links_" + self.Sectors, "Nodes_" + self.Sectors])
        self.removeEmptyQuerySubGroup("Sectors")
        if task is not None:
            return {'task': task.definition()}

    """Open Layers"""
    def openRemoveSpecificLayers(self, layers, epsg):
        self.especificComplementaryLayers = self.complementaryLayers
        self.extent = self.iface.mapCanvas().extent()
        self.specificEpsg = epsg
        self.specificLayers = layers
        self.removingLayers = True
        QGISRedUtils().runTask('update specific layers', self.removeLayers, self.openSpecificLayers)

    def openSpecificLayers(self, exception=None, result=None):
        self.especificComplementaryLayers = []
        if self.specificEpsg is not None:
            self.runChangeCrs()

        self.opendedLayers = False
        QGISRedUtils().runTask('update extent', self.openSpecificLayersProcess, self.setExtent)

    def openSpecificLayersProcess(self, task):
        if not self.opendedLayers:
            self.opendedLayers = True
            # Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, self.specificLayers)
            self.updateMetadata()
            self.removingLayers = False
            if task is not None:
                return {'task': task.definition()}

    def openElementLayer(self, nameLayer):
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputGroup = self.getInputGroup()
        utils.openElementsLayers(inputGroup, [nameLayer])
        self.updateMetadata()

    def openElementLayers(self, task, net="", folder=""):
        if not self.opendedLayers:
            if not net == "" and not folder == "":
                self.NetworkName = net
                self.ProjectDirectory = folder

            self.opendedLayers = True
            # Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, self.ownMainLayers)
            utils.openElementsLayers(inputGroup, self.especificComplementaryLayers)

            self.especificComplementaryLayers = []

            self.updateMetadata()

            self.setSelectedFeaturesById()
            if task is not None:
                return {'task': task.definition()}

    def openIssuesLayers(self):
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        issuesGroup = self.getIssuesGroup()
        utils.openIssuesLayers(issuesGroup, self.issuesLayers)

    def openConnectivityLayer(self):
        # Group
        connGroup = QgsProject.instance().layerTreeRoot().findGroup("Connectivity")
        if connGroup is None:
            queryGroup = self.getQueryGroup()
            connGroup = queryGroup.insertGroup(0, "Connectivity")
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openLayer(connGroup, "Links_Connectivity")

    def openSectorLayers(self):
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            # Group
            hydrGroup = QgsProject.instance().layerTreeRoot().findGroup("Sectors")
            if hydrGroup is None:
                queryGroup = self.getQueryGroup()
                hydrGroup = queryGroup.insertGroup(0, "Sectors")

            utils.openLayer(hydrGroup, "Nodes_" + self.Sectors, sectors=True)
            utils.openLayer(hydrGroup, "Links_" + self.Sectors, sectors=True)

    """Groups"""
    def activeInputGroup(self):
        if self.ResultDockwidget is None:
            return
        group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if group is not None:
            group.setItemVisibilityChecked(
                not self.ResultDockwidget.isVisible())
        group = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if group is not None:
            group.setItemVisibilityChecked(self.ResultDockwidget.isVisible())

    def getInputGroup(self):
        # Same method in qgisred_newproject_dialog and qgisred_results_dock
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def getQueryGroup(self):
        queryGroup = QgsProject.instance().layerTreeRoot().findGroup("Queries")
        if queryGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            queryGroup = netGroup.insertGroup(0, "Queries")
        return queryGroup

    def getIssuesGroup(self):
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Issues")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            inputGroup = netGroup.insertGroup(0, "Issues")
        return inputGroup

    def removeEmptyIssuesGroup(self):
        netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
        if netGroup is not None:
            issuesGroup = netGroup.findGroup("Issues")
            if issuesGroup is not None:
                if len(issuesGroup.findLayers()) == 0:
                    netGroup.removeChildNode(issuesGroup)

    def removeEmptyQuerySubGroup(self, name):
        netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
        if netGroup is not None:
            queryGroup = netGroup.findGroup("Queries")
            if queryGroup is not None:
                querySubGroup = queryGroup.findGroup(name)
                if querySubGroup is not None:
                    if len(querySubGroup.findLayers()) == 0:
                        queryGroup.removeChildNode(querySubGroup)
                if len(queryGroup.findLayers()) == 0:
                    netGroup.removeChildNode(queryGroup)

    """Others"""
    def getComplementaryLayersOpened(self):
        complementary = []
        groupName = "Inputs"
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
        if dataGroup is not None:
            layers = self.getLayers()
            root = QgsProject.instance().layerTreeRoot()
            for layer in layers:
                parent = root.findLayer(layer.id())
                if parent is not None:
                    if parent.parent().name() == groupName:
                        rutaLayer = self.getLayerPath(layer)
                        layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName+"_", "")
                        if not self.ownMainLayers.__contains__(layerName):
                            complementary.append(layerName)
        return complementary

    def blockLayers(self, readonly):
        layers = self.getLayers()
        for layer in layers:
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
                layersNames = qgsFilename
            else:
                layers = self.getLayers()
                # Inputs
                groupName = "Inputs"
                dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
                if dataGroup is not None:
                    layersNames = layersNames + "[Inputs]"
                    layersNames = layersNames + \
                        self.writeLayersOfGroups(groupName, layers)
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
                    layerName = os.path.splitext(os.path.basename(rutaLayer))[0].replace(self.NetworkName+"_", "")
                    paths = paths + layerName + ';'
        return paths

    def setCursor(self, shape):
        cursor = QCursor()
        cursor.setShape(shape)
        self.iface.mapCanvas().setCursor(cursor)

    def setExtent(self, exception=None, result=None):
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
        un = 25.4/pix_per_inch  # x WidthPixels -- > mm/px x px = mm
        # 1mm * unitsPerPixel / un -->tolerance
        tolerance = 1 * unitsPerPixel/un
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
                if layerName == "Sources" or layerName == "Demands":
                    continue
                if self.getLayerPath(layer) == layerPath:
                    fids = []
                    ids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        id = str(feature['Id'])
                        if id == 'NULL':
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
                    if (len(fids) > 0):
                        self.selectedFids[layerName] = fids
                    if (len(ids) > 0):
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
                        id = str(feature['Id'])
                        if id == 'NULL':
                            message = self.tr("Some Ids are not defined. Commit before and try again.")
                            self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                            self.selectedFids = {}
                            return False
                        ids.append(id)
                    if (len(fids) > 0):
                        self.selectedFids[layerName] = fids
                    if (len(ids) > 0):
                        self.selectedIds[layerName] = ids

        # Generate concatenate string for links and nodes
        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ';'
        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ';'
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
                    if (layerName in self.selectedFids):
                        layer.selectByIds(self.selectedFids[layerName])

    def doNothing(self, task):
        if task is not None:
            return {'task': task.definition()}

    def transformPoint(self, point):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        pipesCrs = utils.getProjectCrs()
        projectCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
        xform = QgsCoordinateTransform(projectCrs, pipesCrs, QgsProject.instance())
        return xform.transform(point)

    """Main methods"""
    """Toolbars"""
    def runFileToolbar(self):
        self.fileToolbar.setVisible(not self.fileToolbar.isVisible())

    def runProjectToolbar(self):
        self.projectToolbar.setVisible(not self.projectToolbar.isVisible())

    def runEditionToolbar(self):
        self.editionToolbar.setVisible(not self.editionToolbar.isVisible())

    def runVerificationsToolbar(self):
        self.verificationsToolbar.setVisible(
            not self.verificationsToolbar.isVisible())

    def runToolsToolbar(self):
        self.toolsToolbar.setVisible(not self.toolsToolbar.isVisible())

    def runDtToolbar(self):
        self.dtToolbar.setVisible(not self.dtToolbar.isVisible())

    def runExperimentalToolbar(self):
        self.experimentalToolbar.setVisible(not self.experimentalToolbar.isVisible())

    """Common"""
    def runOpenTemporaryFiles(self, exception=None, result=None):
        if self.hasToOpenIssuesLayers:
            self.removeIssuesLayersFiles()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReplaceTemporalFiles(self.ProjectDirectory, self.tempFolder)
        self.readUnits(self.ProjectDirectory, self.NetworkName)

        if self.hasToOpenNewLayers:
            self.opendedLayers = False
            QGISRedUtils().runTask('update layers', self.openElementLayers, self.setExtent)
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

        # Message
        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def processCsharpResult(self, b, message):
        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        if b == "True":
            if not message == "":
                self.iface.messageBar().pushMessage(self.tr("Information"),
                                                    self.tr(message), level=3, duration=5)
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
        self.extent = self.iface.mapCanvas().extent()
        if self.hasToOpenNewLayers and self.hasToOpenIssuesLayers:
            QGISRedUtils().runTask('update plus issue layers', self.removeLayersAndIssuesLayers,
                                   self.runOpenTemporaryFiles)
        elif self.hasToOpenNewLayers:
            QGISRedUtils().runTask('update layers', self.removeLayers, self.runOpenTemporaryFiles)
        elif self.hasToOpenIssuesLayers:
            QGISRedUtils().runTask('update issue layers', self.removeIssuesLayers, self.runOpenTemporaryFiles)

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()

    def runReportIssues(self):
        webbrowser.open('https://github.com/neslerel/QGISRed/issues')

    """File"""
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

    def runCanCreateProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runCreateProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                QGISRedUtils().runTask('create project', self.clearQGisProject, self.runCreateProject)

    def runCreateProject(self, exception=None, result=None):
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
                QGISRedUtils().runTask('import project', self.clearQGisProject, self.runImport)

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

    def runImport(self, exception=None, result=None):
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

    def runChangeCrs(self):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ChangeCrs(self.ProjectDirectory, self.NetworkName, self.specificEpsg)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            pass
        elif resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

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
            self.iface.messageBar().pushMessage(self.tr("Info"), self.tr("Project options updated"),
                                                level=0, duration=5)
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
        self.iface.messageBar().pushMessage("QGISRed", "Backup stored in: " + path, level=0, duration=5)

    def runOpenedQgisProject(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            return
        self.readUnits(self.ProjectDirectory, self.NetworkName)

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.updateMetadata()

    def runClearedProject(self):
        self.gisredDll = None
        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()

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
            self.extent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedUtils().runTask('remove dbfs', self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "commit":
            self.processCsharpResult(resMessage, "Pipe's roughness converted")
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
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
            self.extent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedUtils().runTask('remove dbfs', self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"),
                                                level=1, duration=5)
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
            self.extent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedUtils().runTask('remove dbfs', self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"),
                                                level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
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
        self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)

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
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "INP file successfully exported"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif not resMessage == "Cancelled":
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runLegendChanged(self):
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
                self.addPipeButton, self.iface, self.ProjectDirectory, self.NetworkName, self.runCreatePipe)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.addTankButton, self, self.runAddTank)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.addReservoirButton, self, self.runAddReservoir)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.insertValveButton, self, self.runInsertValve, 2)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.insertPumpButton, self, self.runInsertPump, 2)
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
            self.myMapTools[tool] = QGISRedMultiLayerSelection(self.iface, self.iface.mapCanvas(),
                                                               self.selectElementsButton)
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
                self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CrossCursor)

    def runEditVertexs(self):
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
            self.myMapTools[tool] = QGISRedMoveVertexsTool(
                self.moveVertexsButton, self.iface, self.ProjectDirectory, self.NetworkName)
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
        if self.linkIds == "":
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.reverseLinkButton, self, self.runReverseLink, 2)
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

        pointText = ""
        if point is not None:
            point = self.transformPoint(point)
            pointText = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReverseLink(self.ProjectDirectory, self.NetworkName, self.tempFolder,
                                        pointText, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectSplitPoint(self):
        tool = "pointSplit"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.splitPipeButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.splitPipeButton, self, self.runSplitPipe, 2)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.mergeSplitJunctionButton, self, self.runMergeSplitPoints, 3)
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
                self.createReverseTconButton, self, self.runCreateRemoveTconnections, 5)
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
        resMessage = GISRed.CreateReverseTConnection(self.ProjectDirectory, self.NetworkName, self.tempFolder,
                                                     point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToCrossings(self):
        tool = "createReverseCross"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.createReverseCrossButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.createReverseCrossButton, self, self.runCreateRemoveCrossings, 2)
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
        resMessage = GISRed.CreateReverseCrossings(self.ProjectDirectory, self.NetworkName, self.tempFolder,
                                                   point1, tolerance)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectValvePumpPoints(self):
        tool = "moveValvePump"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.moveValvePumpButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.moveValvePumpButton, self, self.runMoveValvePump, 4)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.removeElementsButton, self, self.runDeleteElement, 2)
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
        resMessage = GISRed.RemoveElements(self.ProjectDirectory, self.NetworkName, self.tempFolder,
                                           pointText, ids)
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
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.editElementButton, self, self.runProperties, 2)
            self.myMapTools[tool].setCursor(Qt.WhatsThisCursor)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runProperties(self, point):
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
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        if (self.gisredDll is None):
            self.gisredDll = GISRed.CreateInstance()
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.EditElements(self.gisredDll, self.ProjectDirectory,
                                         self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        if not resMessage == "Select":
            self.processCsharpResult(resMessage, "")
            self.gisredDll = None
            self.blockLayers(False)
        else:
            self.blockLayers(True)

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

    """Verifications"""
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

        self.processCsharpResult(resMessage, "Input data is valid")

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
        resMessage = GISRed.CheckOverlappingElements(self.ProjectDirectory, self.NetworkName, self.tempFolder,
                                                     self.nodeIds, self.linkIds)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No overlapping elements found")

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

        self.processCsharpResult(resMessage, "No aligned vertices to delete")

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

        self.processCsharpResult(resMessage, "No pipes to join")

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

        self.processCsharpResult(resMessage, "No T connections to create")

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
        resMessage = GISRed.CheckConnectivity(self.ProjectDirectory, self.NetworkName, linesToDelete,
                                              step, self.tempFolder)
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
        self.extent = self.iface.mapCanvas().extent()
        if self.hasToOpenNewLayers and self.hasToOpenConnectivityLayers:
            QGISRedUtils().runTask('update layers and connectivity', self.removeLayersAndConnectivity,
                                   self.runOpenTemporaryFiles)
        elif self.hasToOpenConnectivityLayers:
            QGISRedUtils().runTask('update connectivity', self.removeLayersConnectivity, self.runOpenTemporaryFiles)

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
            resMessage = GISRed.CheckLengths(self.ProjectDirectory, self.NetworkName,
                                             dlg.Tolerance, self.tempFolder, self.linkIds)
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, "No one pipe's length out of tolerance")

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
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on diameter checking"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on materials checking"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on installation dates checking"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
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
        self.extent = self.iface.mapCanvas().extent()
        if self.hasToOpenSectorLayers:
            QGISRedUtils().runTask('update sectors', self.removeSectorLayers, self.runOpenTemporaryFiles)

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

        self.processCsharpResult(resMessage, "No issues ocurred")

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

        self.processCsharpResult(resMessage, "No issues ocurred")

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
            resMessage = GISRed.ElevationInterpolation(self.ProjectDirectory, self.NetworkName,
                                                       self.tempFolder, self.ElevationFiles)
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(resMessage, "Any elevation has been estimated")

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
        self.extent = self.iface.mapCanvas().extent()
        if self.hasToOpenSectorLayers:
            QGISRedUtils().runTask('update sectors', self.removeSectorLayers, self.runOpenTemporaryFiles)

    """Digital Twin"""
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
                self.addServConnButton, self.iface, self.ProjectDirectory, self.NetworkName,
                self.runCreateServiceConnection)
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

    def runEditServiceConnectionPath(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.editServConnButton.setChecked(False)
            return

        tool = "editConnection"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.editServConnButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedEditConnectionsTool(
                self.editServConnButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CrossCursor)

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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Does not exist Isolation Valves SHP file"), level=1, duration=5)
            return

        # Process
        self.especificComplementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.SetInitialStatusPipes(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "Any isolation valve change status of pipes")

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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Does not exist ServiceConnections SHP file"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Does not exist Hydrants SHP file"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Does not exist Washout Valves SHP file"), level=1, duration=5)
            return

        # Process
        self.especificComplementaryLayers = ["WashoutValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AddWashoutValves(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "No Washout Valves to include in the model")

    """Minimum Spanning Tree"""
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
            self.treeName = resMessage.split('^')[1]
            self.removingLayers = True
            QGISRedUtils().runTask('update tree layers', self.removeTreeLayers, self.runTreeProcess)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runTreeProcess(self, exception=None, result=None):
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
        treeGroup = QgsProject.instance().layerTreeRoot().findGroup("Tree: " + self.treeName)
        if treeGroup is None:
            queryGroup = self.getQueryGroup()
            treeGroup = queryGroup.insertGroup(0, "Tree: " + self.treeName)
        return treeGroup

    def removeTreeLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(["Links_Tree_" + self.treeName, "Nodes_Tree_" + self.treeName])

        self.removeEmptyQuerySubGroup("Tree")
        if task is not None:
            return {'task': task.definition()}
