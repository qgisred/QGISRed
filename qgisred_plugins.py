# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRed
                                 A QGIS plugin
 Tool for helping the hydraulic engineer in the task of modelling a water 
 distribution network and in the decision-making process
                              -------------------
        begin                : 2019-03-26
        git sha              : $Format:%H$
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

from qgis.gui import QgsMessageBar, QgsMapToolEmitPoint
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsCoordinateReferenceSystem
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeNode
from win32api import GetFileVersionInfo, LOWORD, HIWORD
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu, QFileDialog, QToolButton
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.core import Qgis, QgsTask, QgsApplication, QgsFeatureRequest, QgsExpression
# Import resources
from . import resources3x
# Import the code for the dialog
from .ui.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
from .ui.qgisred_newproject_dialog import QGISRedNewProjectDialog
from .ui.qgisred_import_dialog import QGISRedImportDialog
from .ui.qgisred_about_dialog import QGISRedAboutDialog
from .ui.qgisred_results_dock import QGISRedResultsDock
from .ui.qgisred_toolLength_dialog import QGISRedLengthToolDialog
from .ui.qgisred_toolConnectivity_dialog import QGISRedConnectivityToolDialog
from .tools.qgisred_utils import QGISRedUtils
from .tools.qgisred_moveNodes import QGISRedMoveNodesTool
from .tools.qgisred_multilayerSelection import QGISRedUtilsMultiLayerSelection
from .tools.qgisred_createPipe import QGISRedCreatePipeTool
from .tools.qgisred_moveVertexs import QGISRedMoveVertexsTool
from .tools.qgisred_selectPoint import QGISRedSelectPointTool

# Others imports
import os
import datetime
import time
import tempfile
import platform
import base64
import shutil
from ctypes import*

# MessageBar Levels
# Info 0
# Warning 1
# Critical 2
# Success 3


class QGISRed:
    """QGIS Plugin Implementation."""
    # Common variables
    ResultDockwidget = None
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands",
                     "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    ownFiles = ["DefaultValues", "Options",
                "Rules", "Controls", "Curves", "Patterns"]
    complementaryLayers = []
    TemporalFolder = "Temporal folder"
    DependenciesVersion = "1.0.9.0"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.KeyTemp = str(base64.b64encode(os.urandom(16)))

        if not platform.system() == "Windows":
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr(
                "QGISRed only works in Windows"), level=2, duration=5)
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
        self.dlg = QGISRedNewProjectDialog()

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

    def initGui(self):
        if not platform.system() == "Windows":
            return
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        """Main buttons"""
        # File
        #    #Menu
        self.fileMenu = self.qgisredmenu.addMenu(self.tr('File'))
        self.fileMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconData.png'))
        #    #Toolbar
        self.fileToolbar = self.iface.addToolBar(self.tr(u'QGISRed File'))
        self.fileToolbar.setObjectName(self.tr(u'QGISRed File'))
        self.fileToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconData.png'
        fileDropButton = self.add_action(icon_path, text=self.tr(u'File'), callback=self.runFileToolbar, menubar=self.fileMenu, add_to_menu=False,
                                         toolbar=self.toolbar, createDrop=True, addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconProjectManager.png'
        self.add_action(icon_path, text=self.tr(u'Project manager'), callback=self.runProjectManager, menubar=self.fileMenu, toolbar=self.fileToolbar,
                        actionBase=fileDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        self.add_action(icon_path, text=self.tr(u'Create project'), callback=self.runCanCreateProject, menubar=self.fileMenu, toolbar=self.fileToolbar,
                        actionBase=fileDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconImport.png'
        self.add_action(icon_path, text=self.tr(u'Import data'), callback=self.runImport, menubar=self.fileMenu, toolbar=self.fileToolbar,
                        actionBase=fileDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCloseProject.png'
        self.add_action(icon_path, text=self.tr(u'Close project'), callback=self.runCloseProject, menubar=self.fileMenu, toolbar=self.fileToolbar,
                        actionBase=fileDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

        # Project
        #    #Menu
        self.projectMenu = self.qgisredmenu.addMenu(self.tr('Project'))
        self.projectMenu.setIcon(
            QIcon(':/plugins/QGISRed/images/iconEditProject.png'))
        #    #Toolbar
        self.projectToolbar = self.iface.addToolBar(
            self.tr(u'QGISRed Project'))
        self.projectToolbar.setObjectName(self.tr(u'QGISRed Project'))
        self.projectToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconEditProject.png'
        projectDropButton = self.add_action(icon_path, text=self.tr(u'Project'), callback=self.runProjectToolbar, menubar=self.projectMenu, add_to_menu=False,
                                            toolbar=self.toolbar, createDrop=True, addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconEditProject.png'
        self.add_action(icon_path, text=self.tr(u'Edit project'), callback=self.runEditProject, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=projectDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconEditOptions.png'
        self.add_action(icon_path, text=self.tr(u'Options'), callback=self.runEditOptions, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=projectDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDefaultValues.png'
        self.add_action(icon_path, text=self.tr(u'Default Values'), callback=self.runDefaultValues, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=projectDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSummary.png'
        self.add_action(icon_path, text=self.tr(u'Summary'), callback=self.runSummary, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=projectDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconFlash.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Run Model'), callback=self.runModel, menubar=self.projectMenu, toolbar=self.projectToolbar,
                                     actionBase=projectDropButton, createDrop=True, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconResults.png'
        self.add_action(icon_path, text=self.tr(u'Show Results Browser'), callback=self.runShowResultsDock, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=dropButton, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconShpToInp.png'
        self.add_action(icon_path, text=self.tr(u'Export to INP'), callback=self.runExportInp, menubar=self.projectMenu, toolbar=self.projectToolbar,
                        actionBase=projectDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

        # Edit
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
        editDropButton = self.add_action(icon_path, text=self.tr(u'Edition'), callback=self.runEditionToolbar, menubar=self.editionMenu, add_to_menu=False,
                                         toolbar=self.toolbar, createDrop=True, addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPipe.png'
        self.addPipeButton = self.add_action(icon_path, text=self.tr(u'Add Pipe'), callback=self.runPaintPipe, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                             actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddTank.png'
        self.addTankButton = self.add_action(icon_path, text=self.tr(u'Add Tank'), callback=self.runSelectTankPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                             actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddReservoir.png'
        self.addReservoirButton = self.add_action(icon_path, text=self.tr(u'Add Reservoir'), callback=self.runSelectReservoirPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                  actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddValve.png'
        self.insertValveButton = self.add_action(icon_path, text=self.tr(u'Insert Valve in Pipe'), callback=self.runSelectValvePoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPump.png'
        self.insertPumpButton = self.add_action(icon_path, text=self.tr(u'Insert Pump in Pipe'), callback=self.runSelectPumpPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        self.editionToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconSelection.png'
        self.selectElementsButton = self.add_action(icon_path, text=self.tr(u'Select multiple elements'), callback=self.runSelectElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                    actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveElements.png'
        self.moveElementsButton = self.add_action(icon_path, text=self.tr(u'Move node elements'), callback=self.runMoveElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                  actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveVertexs.png'
        self.moveVertexsButton = self.add_action(icon_path, text=self.tr(u'Edit link vertexes'), callback=self.runEditVertexs, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconReverseLink.png'
        self.reverseLinkButton = self.add_action(icon_path, text=self.tr(u'Reverse link'), callback=self.canReverseLink, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSplitPipe.png'
        self.splitPipeButton = self.add_action(icon_path, text=self.tr(u'Split/Join Pipe/s'), callback=self.runSelectSplitPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                               actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMergeSplitJunction.png'
        self.mergeSplitJunctionButton = self.add_action(icon_path, text=self.tr(u'Merge/Split junctions'), callback=self.runSelectPointToMergeSplit, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                        actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateRevTconn.png'
        self.createReverseTconButton = self.add_action(icon_path, text=self.tr(u'Create/Reverse T connections'), callback=self.runSelectPointToTconnections, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                       actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateRevCrossings.png'
        self.createReverseCrossButton = self.add_action(icon_path, text=self.tr(u'Create/Reverse Crossings'), callback=self.runSelectPointToCrossings, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                        actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveValvePump.png'
        self.moveValvePumpButton = self.add_action(icon_path, text=self.tr(u'Move Valve/Pump to another pipe'), callback=self.runSelectValvePumpPoints, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                   actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDeleteElements.png'
        self.removeElementsButton = self.add_action(icon_path, text=self.tr(u'Delete elements'), callback=self.canDeleteElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                    actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        self.editionToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconEdit.png'
        self.editElementButton = self.add_action(icon_path, text=self.tr(u'Edit Element Properties'), callback=self.runSelectPointProperties, menubar=self.editionMenu, toolbar=self.editionToolbar,
                                                 actionBase=editDropButton, add_to_toolbar=True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLinePlot.png'
        self.add_action(icon_path, text=self.tr(u'Edit Patterns and Curves'), callback=self.runPatternsCurves, menubar=self.editionMenu, toolbar=self.editionToolbar,
                        actionBase=editDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRules.png'
        self.add_action(icon_path, text=self.tr(u'Edit Controls'), callback=self.runControls, menubar=self.editionMenu, toolbar=self.editionToolbar,
                        actionBase=editDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

        # Verifications
        #    #Menu
        self.verificationsMenu = self.qgisredmenu.addMenu(
            self.tr('Verifications'))
        self.verificationsMenu.setIcon(
            QIcon(':/plugins/QGISRed/images/iconVerifications.png'))
        #    #Toolbar
        self.verificationsToolbar = self.iface.addToolBar(
            self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setObjectName(
            self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconVerifications.png'
        verificationsDropButton = self.add_action(icon_path, text=self.tr(u'Verifications'), callback=self.runVerificationsToolbar, menubar=self.verificationsMenu, add_to_menu=False,
                                                  toolbar=self.toolbar, createDrop=True, addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCommit.png'
        self.add_action(icon_path, text=self.tr(u'Commit changes'), callback=self.runCommit, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadC.png'
        self.add_action(icon_path, text=self.tr(u'Remove overlapping elements'), callback=self.runCheckCoordinates, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconVerticesC.png'
        self.add_action(icon_path, text=self.tr(u'Simplify link vertices'), callback=self.runSimplifyVertices, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconJoinC.png'
        self.add_action(icon_path, text=self.tr(u'Join consecutive pipes (diameter, material and year)'), callback=self.runCheckJoinPipes, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsC.png'
        self.add_action(icon_path, text=self.tr(u'Create T Connections'), callback=self.runCheckTConncetions, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check connectivity'), callback=self.runCheckConnectivityM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                                     actionBase=verificationsDropButton, createDrop=True, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityC.png'
        self.add_action(icon_path, text=self.tr(u'Delete issolated subzones'), callback=self.runCheckConnectivityC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=dropButton, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLengthC.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Change pipe lengths'), callback=self.runCheckLengths, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDiameters.png'
        self.add_action(icon_path, text=self.tr(u'Check diameters'), callback=self.runCheckDiameters, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMaterial.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe materials'), callback=self.runCheckMaterials, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDate.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe installation dates'), callback=self.runCheckInstallationDates, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydraulic.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Obtain hydraulic sectors'), callback=self.runHydraulicSectors, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
                        actionBase=verificationsDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())

        # Tools
        #    #Menu
        self.toolsMenu = self.qgisredmenu.addMenu(self.tr('Tools'))
        self.toolsMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconTools.png'))
        #    #Toolbar
        self.toolsToolbar = self.iface.addToolBar(self.tr(u'QGISRed Tools'))
        self.toolsToolbar.setObjectName(self.tr(u'QGISRed Tools'))
        self.toolsToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconTools.png'
        toolDropButton = self.add_action(icon_path, text=self.tr(u'Tools'), callback=self.runToolsToolbar, menubar=self.toolsMenu, add_to_menu=False,
                                         toolbar=self.toolbar, createDrop=True, addActionToDrop=False, add_to_toolbar=False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRoughness.png'
        self.add_action(icon_path, text=self.tr(u'Set Roughness coefficient (from Material and Date)'), callback=self.runSetRoughness, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconInterpolate.png'
        self.add_action(icon_path, text=self.tr(u'Interpolate elevation from .asc files'), callback=self.runElevationInterpolation, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconStatus.png'
        self.add_action(icon_path, text=self.tr(u'Set pipe\'s initial status from isolation valves'), callback=self.runSetPipeStatus, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        self.toolsToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconConnections.png'
        self.add_action(icon_path, text=self.tr(u'Add service connections to the model'), callback=self.runAddConnections, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydrants.png'
        self.add_action(icon_path, text=self.tr(u'Add hydrants to the model'), callback=self.runAddHydrants, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconPurges.png'
        self.add_action(icon_path, text=self.tr(u'Add washout valves to the model'), callback=self.runAddPurgeValves, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        self.toolsToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconDemandSector.png'
        self.add_action(icon_path, text=self.tr(u'Obtain demand sectors'), callback=self.runDemandSectors, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
                        actionBase=toolDropButton, add_to_toolbar=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTree.png'

        # #Experimental
        # #    #Menu
        # self.experimentalMenu = self.qgisredmenu.addMenu(self.tr('Experimenta'))
        # self.experimentalMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconTree.png'))
        # #    #Toolbar
        # self.experimentalToolbar = self.iface.addToolBar(self.tr(u'QGISRed Experimental'))
        # self.experimentalToolbar.setObjectName(self.tr(u'QGISRed Experimental'))
        # self.experimentalToolbar.setVisible(False)
        # #    #Buttons
        # icon_path = ':/plugins/QGISRed/images/iconTree.png'
        # expDropButton = self.add_action(icon_path, text=self.tr(u'Experimental'), callback=self.runExperimentalToolbar, menubar=self.experimentalMenu, add_to_menu=False,
        #     toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        # icon_path = ':/plugins/QGISRed/images/iconTree.png'
        # self.add_action(icon_path, text=self.tr(u'Obtain Tree'), callback=self.runTree, menubar=self.experimentalMenu, toolbar=self.experimentalToolbar,
        #     actionBase = expDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())

        # About
        icon_path = ':/plugins/QGISRed/images/iconAbout.png'
        self.add_action(icon_path, text=self.tr(u'About...'), callback=self.runAbout,
                        menubar=self.qgisredmenu, toolbar=self.toolbar, parent=self.iface.mainWindow())

        """Other options"""
        # Saving QGis project
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)

        # Issue layers
        self.issuesLayers = []
        for name in self.ownMainLayers:
            self.issuesLayers.append(name + "_Issues")

        # MapTools
        self.pointElementTool = None
        self.pointValveTool = None
        self.pointPumpTool = None
        self.pointTankTool = None
        self.pointReservoirTool = None
        self.pointDeleteElementTool = None
        self.pointSplitTool = None
        self.pointReverseLinkTool = None
        self.moveValvePumpTool = None
        self.mergeSplitPointTool = None
        self.createReverseTconnTool = None
        self.createReverseCrossTool = None
        self.selectTreePointTool = None

        # QGISRed dependencies
        self.checkDependencies()

        # SHPs temporal folder
        self.tempFolder = tempfile._get_default_tempdir() + "\\QGISRed_" + \
            next(tempfile._get_candidate_names())
        try:  # create directory if does not exist
            os.stat(self.tempFolder)
        except:
            os.mkdir(self.tempFolder)

        self.hasToOpenConnectivityLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False

        self.zoomToFullExtent = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        # dirpath = os.path.join(tempfile._get_default_tempdir(), "qgisred" + self.KeyTemp)
        # if os.path.exists(dirpath) and os.path.isdir(dirpath):
        # shutil.rmtree(dirpath)
        if os.path.exists(self.tempFolder) and os.path.isdir(self.tempFolder):
            shutil.rmtree(self.tempFolder)

        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()
            self.iface.removeDockWidget(self.ResultDockwidget)
            self.ResultDockwidget = None

        for action in self.actions:
            #self.iface.removePluginMenu(self.tr(u'&QGISRed'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        del self.fileToolbar
        del self.projectToolbar
        del self.editionToolbar
        del self.verificationsToolbar
        del self.toolsToolbar

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
        if self.qgisredmenu:
            self.qgisredmenu.menuAction().setVisible(False)

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
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance(
                ).layerTreeRoot().findLayers()]
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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.UpdateMetadata.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.UpdateMetadata.restype = c_char_p
        b = mydll.UpdateMetadata(project.encode(
            'utf-8'), net.encode('utf-8'), layersNames.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        QApplication.restoreOverrideCursor()

    def writeLayersOfGroups(self, groupName, layers):
        root = QgsProject.instance().layerTreeRoot()
        paths = ""
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if not parent is None:
                if parent.parent().name() == groupName:
                    rutaLayer = layer.dataProvider(
                    ).dataSourceUri().split("|")[0]
                    paths = paths + \
                        os.path.splitext(os.path.basename(rutaLayer))[
                            0].replace(self.NetworkName+"_", "") + ';'
        return paths

    def defineCurrentProject(self):
        """Identifying the QGISRed current project"""
        self.NetworkName = "Network"
        self.ProjectDirectory = self.TemporalFolder
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            layerUri = layer.dataProvider().dataSourceUri().split("|")[0]
            for layerName in self.ownMainLayers:
                if "_" + layerName in layerUri:
                    self.ProjectDirectory = os.path.dirname(layerUri)
                    vectName = os.path.splitext(os.path.basename(layerUri))[
                        0].split("_")
                    name = ""
                    for part in vectName:
                        if part in self.ownMainLayers:
                            break
                        name = name + part + "_"
                    name = name.strip("_")
                    self.NetworkName = name
                    return

    def isOpenedProjectOld(self):
        if self.isLayerOnEdition():
            return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                    "The project has changes. Please save them before continuing."), level=1)
                return False
            else:
                # Close the project and continue?
                reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Opened project'), self.tr(
                    'Do you want to close the current project and continue?'), QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        # else:
            # if len(self.iface.mapCanvas().layers())>0:
                # #Close files and continue?
                # reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Opened layers'), self.tr('Do you want to close the current layers and continue?'), QMessageBox.Yes, QMessageBox.No)
                # if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    # return True
                # else:
                    # return False
        return True

    def isOpenedProject(self):
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            if layer.isEditable():
                self.iface.messageBar().pushMessage("Warning",
                                                    "Some layer is in Edit Mode. Plase, commit it before continuing.", level=1, duration=5)
                return False
        qgsFilename = QgsProject.instance().fileName()
        if not qgsFilename == "":
            if QgsProject.instance().isDirty():
                # Save and continue
                self.iface.messageBar().pushMessage("Warning",
                                                    "The project has changes. Please save them before continuing.", level=1, duration=5)
                return False
            else:
                # Close project and continue?
                reply = QMessageBox.question(self.iface.mainWindow(
                ), 'Opened project', 'Do you want to close the current project and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers()) > 0:
                # Close files and continue?
                reply = QMessageBox.question(self.iface.mainWindow(
                ), 'Opened layers', 'Do you want to close the current layers and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def clearQGisProject(self, task):
        QgsProject.instance().clear()
        raise Exception('')

    def isValidProject(self):
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "No valid project is opened"), level=1, duration=5)
            return False
        return True

    def isLayerOnEdition(self):
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            if layer.isEditable():
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                    "Some layer is in Edit Mode. Please, commit it before continuing."), level=1)
                return True
        return False

    def doNothing(self, task):
        raise Exception('')

    """Remove Layers"""

    def removeLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.complementaryLayers)
        raise Exception('')

    def removeDBFs(self, task, dbfs):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(dbfs, ".dbf")
        # task.finished(True)
        raise Exception('')

    def removeResultsLayers(self, task):
        resultsDirct = os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(
            resultsDirct, self.NetworkName + "_Base", self.iface)
        utils.removeLayers(self.resultsLayersToRemove)
        raise Exception('')

    def removeIssuesLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)
        raise Exception('')

    def removeLayersAndIssuesLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.complementaryLayers)
        utils.removeLayers(self.issuesLayers)
        raise Exception('')

    def removeIssuesLayersFiles(self):
        dirList = os.listdir(self.ProjectDirectory)
        for fi in dirList:
            if "_Issues." in fi:
                os.remove(os.path.join(self.ProjectDirectory, fi))

    def removeLayersConnectivity(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        # utils.removeLayers(self.issuesLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")
        # Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)
        raise Exception('')

    def removeLayersAndConnectivity(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        utils.removeLayers(self.complementaryLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")
        raise Exception('')

    def removeSectorLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(["Links_" + self.Sectors, "Nodes_" + self.Sectors])

        self.removeEmptyQuerySubGroup("Sectors")
        # Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)
        raise Exception('')

    """Open Layers"""

    def openElementLayers(self, task):
        if not self.opendedLayers:
            self.opendedLayers = True
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            if crs.srsid() == 0:
                crs = QgsCoordinateReferenceSystem()
                crs.createFromId(
                    3452, QgsCoordinateReferenceSystem.InternalCrsId)
            # Open layers
            utils = QGISRedUtils(self.ProjectDirectory,
                                 self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(
                inputGroup, crs, self.ownMainLayers, self.ownFiles)
            utils.openElementsLayers(
                inputGroup, crs, self.complementaryLayers, [])
            self.updateMetadata()

            self.setSelectedFeaturesById()
            raise Exception('')

    def openIssuesLayers(self):
        # CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        issuesGroup = self.getIssuesGroup()
        utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)

    def openConnectivityLayer(self):
        # CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        # Group
        connGroup = QgsProject.instance().layerTreeRoot().findGroup("Connectivity")
        if connGroup is None:
            queryGroup = self.getQueryGroup()
            connGroup = queryGroup.insertGroup(0, "Connectivity")
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.openLayer(crs, connGroup, "Links_Connectivity")

    def openSectorLayers(self):
        # CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        # Open layers
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            # Group
            hydrGroup = QgsProject.instance().layerTreeRoot().findGroup("Sectors")
            if hydrGroup is None:
                queryGroup = self.getQueryGroup()
                hydrGroup = queryGroup.insertGroup(0, "Sectors")

            utils.openLayer(crs, hydrGroup, "Nodes_" +
                            self.Sectors, sectors=True)
            utils.openLayer(crs, hydrGroup, "Links_" +
                            self.Sectors, sectors=True)

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
        # Same method in qgisred_newproject_dialog
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

    def createBackup(self):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.saveBackup(self.KeyTemp)

    def checkDependencies(self):
        valid = False
        gisredDir = QGISRedUtils().getGISRedFolder()
        if os.path.isdir(gisredDir):
            try:
                info = GetFileVersionInfo(os.path.join(
                    gisredDir, "GISRed.QGisPlugins.dll"), "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                currentVersion = str(HIWORD(
                    ms)) + "." + str(LOWORD(ms)) + "." + str(HIWORD(ls)) + "." + str(LOWORD(ls))
            except:
                currentVersion = "0.0.0.0"
            if currentVersion == self.DependenciesVersion:
                valid = True
        if not valid:
            locale = QSettings().value("locale/userLocale")
            if "es" in locale:
                lang = "es-ES"
            else:
                lang = "en-US"
            if "64bit" in str(platform.architecture()):
                plat = 'x64'
            else:
                plat = 'x86'
            link = '\"http://www.redhisp.webs.upv.es/files/QGISRed/' + \
                self.DependenciesVersion + '/Installation_' + plat + '_' + lang + '.msi\"'
            request = QMessageBox.question(self.iface.mainWindow(), self.tr('QGISRed Dependencies'), self.tr('QGISRed plugin only runs in Windows OS and needs some dependencies (' +
                                                                                                             self.DependenciesVersion + '). Do you want to download and authomatically install them?'), QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No))
            if request == QMessageBox.Yes:
                import urllib.request
                localFile = tempfile._get_default_tempdir(
                ) + "\\" + next(tempfile._get_candidate_names()) + ".msi"
                try:
                    urllib.request.urlretrieve(link.strip('\'"'), localFile)
                    os.system(localFile)
                    os.remove(localFile)
                except:
                    pass
                valid = self.checkDependencies()
        return valid

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
        unitsPerPixel = self.iface.mapCanvas().getCoordinateTransform(
        ).mapUnitsPerPixel()  # x WidthPixels --> m/px * px = metros
        # 25.4 mm == inch
        un = 25.4/pix_per_inch  # x WidthPixels -- > mm/px x px = mm
        # 1mm * unitsPerPixel / un -->tolerance
        tolerance = 1 * unitsPerPixel/un
        return tolerance

    def getSelectedFeaturesIds(self):
        linkIdsList = []
        nodeIdsList = []
        self.selectedFids = {}

        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                if layerName == "Sources" or layerName == "Demands":
                    continue
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/", "\\"):
                    fids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        if layer.geometryType() == 0:
                            nodeIdsList.append(str(feature['Id']))
                        else:
                            linkIdsList.append(str(feature['Id']))
                    self.selectedFids[layerName] = fids

        if 'NULL' in nodeIdsList or 'NULL' in linkIdsList:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some Ids are not defined. Commit before and try again."), level=1, duration=5)
            return False
        # Generate concatenate string for links and nodes
        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ';'
        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ';'
        return True

    def setSelectedFeaturesById(self):
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                if layerName == "Sources" or layerName == "Demands":
                    continue
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/", "\\"):
                    if (layerName in self.selectedFids):
                        layer.selectByIds(self.selectedFids[layerName])

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

    def runExperimentalToolbar(self):
        self.experimentalToolbar.setVisible(
            not self.experimentalToolbar.isVisible())

    """Common"""

    def runOpenTemporaryFiles(self, exception=None, result=None):
        if self.hasToOpenIssuesLayers:
            self.removeIssuesLayersFiles()
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        if self.hasToOpenNewLayers:
            self.opendedLayers = False
            task1 = QgsTask.fromFunction(
                'Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
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

        # Message
        if b == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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

        if self.hasToOpenNewLayers and self.hasToOpenIssuesLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeLayersAndIssuesLayers, on_finished=self.runOpenTemporaryFiles)
        elif self.hasToOpenNewLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeLayers, on_finished=self.runOpenTemporaryFiles)
        elif self.hasToOpenIssuesLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeIssuesLayers, on_finished=self.runOpenTemporaryFiles)
        else:
            # Not to run task
            return
        self.extent = self.iface.mapCanvas().extent()
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()

    """File"""

    def runProjectManager(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName, self)

        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            # self.updateMetadata()
            pass

    def runCanCreateProject(self):
        if not self.checkDependencies():
            return

        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.runCreateProject()
        else:
            valid = self.isOpenedProject()
            if valid:
                task1 = QgsTask.fromFunction(
                    '', self.clearQGisProject, on_finished=self.runCreateProject)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCreateProject(self, exception=None, result=None):
        if not self.checkDependencies():
            return

        if not self.ProjectDirectory == self.TemporalFolder:
            QgsProject.instance().clear()
            self.defineCurrentProject()
        dlg = QGISRedNewProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            # self.updateMetadata()

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
        result = dlg.ProcessDone
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            #self.updateMetadata(self.ProjectDirectory, self.NetworkName)

    def runCloseProject(self):
        self.iface.newProject(True)

    """Project"""

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
        dlg = QGISRedNewProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            # self.updateMetadata()

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.updateMetadata()

    def runClearedProject(self):
        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()

    def runEditOptions(self):
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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditOptions.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditOptions.restype = c_char_p
        b = mydll.EditOptions(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = self.iface.mapCanvas().extent()
            task1 = QgsTask.fromFunction(
                'Dismiss this message', self.doNothing, on_finished=self.runOpenTemporaryFiles)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif b == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditDefaultValues.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditDefaultValues.restype = c_char_p
        b = mydll.EditDefaultValues(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = self.iface.mapCanvas().extent()
            task1 = QgsTask.fromFunction(
                'Dismiss this message', self.doNothing, on_finished=self.runOpenTemporaryFiles)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif b == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AbstractReport.argtypes = (c_char_p, c_char_p)
        mydll.AbstractReport.restype = c_char_p
        b = mydll.AbstractReport(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        # Message
        if b == "True":
            pass  # self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runModel(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self.resultsLayersToRemove = []
        myLayers = []
        myLayers.append("Link_" + "Flow")
        myLayers.append("Link_" + "Velocity")
        myLayers.append("Link_" + "HeadLoss")
        myLayers.append("Link_" + "Quaility")
        myLayers.append("Node_" + "Pressure")
        myLayers.append("Node_" + "Head")
        myLayers.append("Node_" + "Demand")
        myLayers.append("Node_" + "Quaility")
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        layers = [tree_layer.layer()
                  for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for nameLayer in myLayers:
            for layer in layers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/", "\\") == os.path.join(resultPath, self.NetworkName + "_Base_" + nameLayer + ".shp").replace("/", "\\"):
                    self.resultsLayersToRemove.append(nameLayer)

        task1 = QgsTask.fromFunction(
            "", self.removeResultsLayers, on_finished=self.runModelProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runModelProcess(self, exception=None, result=None):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Compute.argtypes = (c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Message
        if b == "False":
            self.iface.messageBar().pushMessage(
                "Warning", "Some issues occurred in the process", level=1, duration=5)
        elif b.startswith("[TimeLabels]"):
            # Open dock
            if self.ResultDockwidget is None:
                self.ResultDockwidget = QGISRedResultsDock(self.iface)
                self.iface.addDockWidget(
                    Qt.RightDockWidgetArea, self.ResultDockwidget)
                self.ResultDockwidget.visibilityChanged.connect(
                    self.activeInputGroup)
            self.ResultDockwidget.config(self.ProjectDirectory, self.NetworkName, b.replace(
                "[TimeLabels]", ""), self.resultsLayersToRemove)
            self.ResultDockwidget.show()
            group = self.getInputGroup()
            if group is not None:
                group.setItemVisibilityChecked(False)
            return
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=5)

        if self.ResultDockwidget is not None:  # If some error, close the dock
            self.ResultDockwidget.close()

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

    def runShowResults(self):
        if not self.checkDependencies():
            return
        # Open dock
        if self.ResultDockwidget is None:
            self.runModel()
        else:
            # Validations
            self.defineCurrentProject()
            if not self.isValidProject():
                return
            if not (self.NetworkName == self.ResultDockwidget.NetworkName and self.ProjectDirectory == self.ResultDockwidget.ProjectDirectory):
                self.runModel()
                return
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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        # Message
        if b == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "INP file successfully exported"), level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif not b == "Cancelled":
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    """Edition"""

    def runPaintPipe(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.addPipeButton.setChecked(False)
            return

        if type(self.iface.mapCanvas().mapTool()) is QGISRedCreatePipeTool:
            # self.createPipeTool.deactivated.disconnect(self.runCreatePipe)
            self.iface.mapCanvas().unsetMapTool(self.createPipeTool)
        else:
            if self.isLayerOnEdition():
                self.addPipeButton.setChecked(False)
                return
            self.createPipeTool = QGISRedCreatePipeTool(
                self.addPipeButton, self.iface, self.ProjectDirectory, self.NetworkName, self)
            # self.createPipeTool.deactivated.connect(self.runCreatePipe)
            self.iface.mapCanvas().setMapTool(self.createPipeTool)

    def runCreatePipe(self, points):
        self.pipePoint = ""
        for p in points:
            self.pipePoint = self.pipePoint + \
                str(p.x()) + ":" + str(p.y()) + ";"
        # C#Process:
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddPipe.restype = c_char_p
        b = mydll.AddPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), self.pipePoint.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "Pipe added")

    def runSelectTankPoint(self):
        # Take account the mouse click on QGis:
        if self.pointTankTool is None:
            self.pointTankTool = QGISRedSelectPointTool(
                self.addTankButton, self, self.runAddTank)
            self.iface.mapCanvas().setMapTool(self.pointTankTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointTankTool:
            self.iface.mapCanvas().unsetMapTool(self.pointTankTool)
            self.addTankButton.setChecked(False)
        else:
            self.pointTankTool = QGISRedSelectPointTool(
                self.addTankButton, self, self.runAddTank)
            self.iface.mapCanvas().setMapTool(self.pointTankTool)

    def runAddTank(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddTank.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddTank.restype = c_char_p
        b = mydll.AddTank(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'), "0.01".encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectReservoirPoint(self):
        # Take account the mouse click on QGis:
        if self.pointReservoirTool is None:
            self.pointReservoirTool = QGISRedSelectPointTool(
                self.addReservoirButton, self, self.runAddReservoir)
            self.iface.mapCanvas().setMapTool(self.pointReservoirTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointReservoirTool:
            self.iface.mapCanvas().unsetMapTool(self.pointReservoirTool)
            self.addReservoirButton.setChecked(False)
        else:
            self.pointReservoirTool = QGISRedSelectPointTool(
                self.addReservoirButton, self, self.runAddReservoir)
            self.iface.mapCanvas().setMapTool(self.pointReservoirTool)

    def runAddReservoir(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddReservoir.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddReservoir.restype = c_char_p
        b = mydll.AddReservoir(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'), "0.01".encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectValvePoint(self):
        # Take account the mouse click on QGis:
        if self.pointValveTool is None:
            self.pointValveTool = QGISRedSelectPointTool(
                self.insertValveButton, self, self.runInsertValve, 2)
            self.iface.mapCanvas().setMapTool(self.pointValveTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointValveTool:
            self.iface.mapCanvas().unsetMapTool(self.pointValveTool)
            self.insertValveButton.setChecked(False)
        else:
            self.pointValveTool = QGISRedSelectPointTool(
                self.insertValveButton, self, self.runInsertValve, 2)
            self.iface.mapCanvas().setMapTool(self.pointValveTool)

    def runInsertValve(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertValve.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p

        b = mydll.InsertValve(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'), "0.01".encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectPumpPoint(self):
        # Take account the mouse click on QGis:
        if self.pointPumpTool is None:
            self.pointPumpTool = QGISRedSelectPointTool(
                self.insertPumpButton, self, self.runInsertPump, 2)
            self.iface.mapCanvas().setMapTool(self.pointPumpTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointPumpTool:
            self.iface.mapCanvas().unsetMapTool(self.pointPumpTool)
            self.insertPumpButton.setChecked(False)
        else:
            self.pointPumpTool = QGISRedSelectPointTool(
                self.insertPumpButton, self, self.runInsertPump, 2)
            self.iface.mapCanvas().setMapTool(self.pointPumpTool)

    def runInsertPump(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertPump.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        b = mydll.InsertPump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'), "0.01".encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectElements(self):
        if type(self.iface.mapCanvas().mapTool()) is QGISRedUtilsMultiLayerSelection:
            self.iface.mapCanvas().unsetMapTool(self.selectElementsTool)
        else:
            self.selectElementsTool = QGISRedUtilsMultiLayerSelection(
                self.iface, self.iface.mapCanvas(), self.selectElementsButton)
            self.iface.mapCanvas().setMapTool(self.selectElementsTool)

    def runMoveElements(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveElementsButton.setChecked(False)
            return

        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveVertexsTool:
            self.iface.mapCanvas().unsetMapTool(self.moveVertexsTool)

        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveNodesTool:
            self.iface.mapCanvas().unsetMapTool(self.moveNodesTool)
        else:
            if self.isLayerOnEdition():
                self.moveElementsButton.setChecked(False)
                return
            self.moveNodesTool = QGISRedMoveNodesTool(
                self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.moveNodesTool)
            self.setCursor(Qt.CrossCursor)

    def runEditVertexs(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveVertexsButton.setChecked(False)
            return

        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveNodesTool:
            self.iface.mapCanvas().unsetMapTool(self.moveNodesTool)

        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveVertexsTool:
            self.iface.mapCanvas().unsetMapTool(self.moveVertexsTool)
        else:
            if self.isLayerOnEdition():
                self.moveVertexsButton.setChecked(False)
                return
            self.moveVertexsTool = QGISRedMoveVertexsTool(
                self.moveVertexsButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.moveVertexsTool)
            self.setCursor(Qt.CrossCursor)

    def canReverseLink(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.runUnselectReverseLinkPoint()
            return

        if not self.getSelectedFeaturesIds():
            self.runUnselectReverseLinkPoint()
            return
        if self.linkIds == "":
            self.runSelectReverseLinkPoint()
            return
        self.runUnselectReverseLinkPoint()

        if self.isLayerOnEdition():
            return

        self.runReverseLink(None, None)

    def runSelectReverseLinkPoint(self):
        # Take account the mouse click on QGis:
        if self.pointReverseLinkTool is None:
            self.pointReverseLinkTool = QGISRedSelectPointTool(
                self.reverseLinkButton, self, self.runReverseLink, 2)
            self.iface.mapCanvas().setMapTool(self.pointReverseLinkTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointReverseLinkTool:
            self.iface.mapCanvas().unsetMapTool(self.pointReverseLinkTool)
            self.reverseLinkButton.setChecked(False)
        else:
            self.pointReverseLinkTool = QGISRedSelectPointTool(
                self.reverseLinkButton, self, self.runReverseLink, 2)
            self.iface.mapCanvas().setMapTool(self.pointReverseLinkTool)

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
        tolerance = "0"
        if point is not None:
            pointText = str(point.x()) + ":" + str(point.y())
            tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReverseLink.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ReverseLink.restype = c_char_p
        b = mydll.ReverseLink(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode(
            'utf-8'), pointText.encode('utf-8'), tolerance.encode('utf-8'), self.linkIds.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        #self.selectedFids = {}
        self.processCsharpResult(b, "")

    def runSelectSplitPoint(self):
        # Take account the mouse click on QGis:
        if self.pointSplitTool is None:
            self.pointSplitTool = QGISRedSelectPointTool(
                self.splitPipeButton, self, self.runSplitPipe, 2)
            self.iface.mapCanvas().setMapTool(self.pointSplitTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointSplitTool:
            self.iface.mapCanvas().unsetMapTool(self.pointSplitTool)
            self.splitPipeButton.setChecked(False)
        else:
            self.pointSplitTool = QGISRedSelectPointTool(
                self.splitPipeButton, self, self.runSplitPipe, 2)
            self.iface.mapCanvas().setMapTool(self.pointSplitTool)

    def runSplitPipe(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        b = mydll.SplitPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectPointToMergeSplit(self):
        # Take account the mouse click on QGis:
        if self.mergeSplitPointTool is None:
            self.mergeSplitPointTool = QGISRedSelectPointTool(
                self.mergeSplitJunctionButton, self, self.runMergeSplitPoints, 3)
            self.iface.mapCanvas().setMapTool(self.mergeSplitPointTool)
            return

        if self.iface.mapCanvas().mapTool() is self.mergeSplitPointTool:
            self.iface.mapCanvas().unsetMapTool(self.mergeSplitPointTool)
            self.mergeSplitJunctionButton.setChecked(False)
        else:
            self.mergeSplitPointTool = QGISRedSelectPointTool(
                self.mergeSplitJunctionButton, self, self.runMergeSplitPoints, 3)
            self.iface.mapCanvas().setMapTool(self.mergeSplitPointTool)

    def runMergeSplitPoints(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = str(point2.x()) + ":" + str(point2.y())
        #tolerance = str(self.getTolerance())
        print(point1)
        print(point2)
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SplitMergeJunction.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitMergeJunction.restype = c_char_p
        b = mydll.SplitMergeJunction(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point1.encode('utf-8'), point2.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectPointToTconnections(self):
        # Take account the mouse click on QGis:
        if self.createReverseTconnTool is None:
            self.createReverseTconnTool = QGISRedSelectPointTool(
                self.createReverseTconButton, self, self.runCreateRemoveTconnections, 5)
            self.iface.mapCanvas().setMapTool(self.createReverseTconnTool)
            return

        if self.iface.mapCanvas().mapTool() is self.createReverseTconnTool:
            self.iface.mapCanvas().unsetMapTool(self.createReverseTconnTool)
            self.createReverseTconButton.setChecked(False)
        else:
            self.createReverseTconnTool = QGISRedSelectPointTool(
                self.createReverseTconButton, self, self.runCreateRemoveTconnections, 5)
            self.iface.mapCanvas().setMapTool(self.createReverseTconnTool)

    def runCreateRemoveTconnections(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = str(point2.x()) + ":" + str(point2.y())
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateReverseTConnection.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseTConnection.restype = c_char_p
        b = mydll.CreateReverseTConnection(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point1.encode('utf-8'), point2.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectPointToCrossings(self):
        # Take account the mouse click on QGis:
        if self.createReverseCrossTool is None:
            self.createReverseCrossTool = QGISRedSelectPointTool(
                self.createReverseCrossButton, self, self.runCreateRemoveCrossings, 2)
            self.iface.mapCanvas().setMapTool(self.createReverseCrossTool)
            return

        if self.iface.mapCanvas().mapTool() is self.createReverseCrossTool:
            self.iface.mapCanvas().unsetMapTool(self.createReverseCrossTool)
            self.createReverseCrossButton.setChecked(False)
        else:
            self.createReverseCrossTool = QGISRedSelectPointTool(
                self.createReverseCrossButton, self, self.runCreateRemoveCrossings, 2)
            self.iface.mapCanvas().setMapTool(self.createReverseCrossTool)

    def runCreateRemoveCrossings(self, point1):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = str(point1.x()) + ":" + str(point1.y())
        tolerance = str(self.getTolerance())
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateReverseCrossings.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseCrossings.restype = c_char_p
        b = mydll.CreateReverseCrossings(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point1.encode('utf-8'), tolerance.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

    def runSelectValvePumpPoints(self):
        # Take account the mouse click on QGis:
        if self.moveValvePumpTool is None:
            self.moveValvePumpTool = QGISRedSelectPointTool(
                self.moveValvePumpButton, self, self.runMoveValvePump, 4)
            self.iface.mapCanvas().setMapTool(self.moveValvePumpTool)
            return

        if self.iface.mapCanvas().mapTool() is self.moveValvePumpTool:
            self.iface.mapCanvas().unsetMapTool(self.moveValvePumpTool)
            self.moveValvePumpButton.setChecked(False)
        else:
            self.moveValvePumpTool = QGISRedSelectPointTool(
                self.moveValvePumpButton, self, self.runMoveValvePump, 4)
            self.iface.mapCanvas().setMapTool(self.moveValvePumpTool)

    def runMoveValvePump(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = str(point1.x()) + ":" + str(point1.y())
        point2 = str(point2.x()) + ":" + str(point2.y())
        #tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.MoveValvePump.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.MoveValvePump.restype = c_char_p
        b = mydll.MoveValvePump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point1.encode('utf-8'), point2.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

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
        if self.nodeIds == "" and self.linkIds == "":
            self.runSelectDeleteElementPoint()
            return
        self.removeElementsButton.setChecked(False)

        if self.isLayerOnEdition():
            return

        self.runDeleteElement(None)

    def runSelectDeleteElementPoint(self):
        # Take account the mouse click on QGis:
        if self.pointDeleteElementTool is None:
            self.pointDeleteElementTool = QGISRedSelectPointTool(
                self.removeElementsButton, self, self.runDeleteElement, 2)
            self.iface.mapCanvas().setMapTool(self.pointDeleteElementTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointDeleteElementTool:
            self.iface.mapCanvas().unsetMapTool(self.pointDeleteElementTool)
            self.removeElementsButton.setChecked(False)
        else:
            self.pointDeleteElementTool = QGISRedSelectPointTool(
                self.removeElementsButton, self, self.runDeleteElement, 2)
            self.iface.mapCanvas().setMapTool(self.pointDeleteElementTool)

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
        tolerance = "0"
        if point is not None:
            pointText = str(point.x()) + ":" + str(point.y())
            tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveElements.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElements.restype = c_char_p
        b = mydll.RemoveElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode(
            'utf-8'), pointText.encode('utf-8'), tolerance.encode('utf-8'), self.nodeIds.encode('utf-8'), self.linkIds.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.selectedFids = {}
        self.processCsharpResult(b, "")

    def runSelectPointProperties(self):
        # Take account the mouse click on QGis:
        if self.pointElementTool is None:
            self.pointElementTool = QGISRedSelectPointTool(
                self.editElementButton, self, self.runProperties, 2)
            self.pointElementTool.setCursor(Qt.WhatsThisCursor)
            self.iface.mapCanvas().setMapTool(self.pointElementTool)
            return

        if self.iface.mapCanvas().mapTool() is self.pointElementTool:
            self.iface.mapCanvas().unsetMapTool(self.pointElementTool)
            self.editElementButton.setChecked(False)
        else:
            self.pointElementTool = QGISRedSelectPointTool(
                self.editElementButton, self, self.runProperties, 2)
            self.pointElementTool.setCursor(Qt.WhatsThisCursor)
            self.iface.mapCanvas().setMapTool(self.pointElementTool)

    def runProperties(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = str(point.x()) + ":" + str(point.y())
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditElements.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditElements.restype = c_char_p
        b = mydll.EditElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point.encode('utf-8'), tolerance.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditPatternsCurves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditPatternsCurves.restype = c_char_p
        b = mydll.EditPatternsCurves(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditControls.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditControls.restype = c_char_p
        b = mydll.EditControls(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string

        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "")

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
        print(self.tempFolder)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Commit.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Commit.restype = c_char_p
        b = mydll.Commit(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "Input data is valid")

    def runCheckCoordinates(self):
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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckCoordinates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckCoordinates.restype = c_char_p
        b = mydll.CheckCoordinates(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No overlapping elements found")

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ChechkAlignedVertices.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ChechkAlignedVertices.restype = c_char_p
        b = mydll.ChechkAlignedVertices(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No aligned vertices to delete")

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckJoinPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckJoinPipes.restype = c_char_p
        b = mydll.CheckJoinPipes(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No pipes to join")

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckTConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckTConnections.restype = c_char_p
        b = mydll.CheckTConnections(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No T connections to create")

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

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckConnectivity.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        step = "check"
        if toCommit:
            step = "commit"
        b = mydll.CheckConnectivity(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), linesToDelete.encode('utf-8'), step.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenConnectivityLayers = False
        if b == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"),
                                                self.tr("Only one zone"), level=3, duration=5)
        elif b == "False":
            pass
        elif b == "shps":
            self.hasToOpenConnectivityLayers = True
        elif b == "commit/shps":
            self.hasToOpenNewLayers = True
            self.hasToOpenConnectivityLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

        if self.hasToOpenNewLayers and self.hasToOpenConnectivityLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeLayersAndConnectivity, on_finished=self.runOpenTemporaryFiles)
        elif self.hasToOpenConnectivityLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeLayersConnectivity, on_finished=self.runOpenTemporaryFiles)
        else:
            # Not to run task
            return
        self.extent = self.iface.mapCanvas().extent()
        task1.run()
        QgsApplication.taskManager().addTask(task1)

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
        result = dlg.ProcessDone
        if result:
            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QGISRedUtils().setCurrentDirectory()
            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.CheckLengths.argtypes = (
                c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.CheckLengths.restype = c_char_p
            b = mydll.CheckLengths(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
                'utf-8'), dlg.Tolerance.encode('utf-8'), self.tempFolder.encode('utf-8'))
            b = "".join(map(chr, b))  # bytes to string
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(
                b, "No one pipe's length out of tolerance")

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckDiameters.argtypes = (c_char_p, c_char_p)
        mydll.CheckDiameters.restype = c_char_p
        b = mydll.CheckDiameters(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on diameter checking"), level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif b == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckMaterials.argtypes = (c_char_p, c_char_p)
        mydll.CheckMaterials.restype = c_char_p
        b = mydll.CheckMaterials(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on materials checking"), level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif b == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckInstallationDates.argtypes = (c_char_p, c_char_p)
        mydll.CheckInstallationDates.restype = c_char_p
        b = mydll.CheckInstallationDates(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Message
        if b == "True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr(
                "No issues on installation dates checking"), level=3, duration=5)
        elif b == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr(
                "Some issues occurred in the process"), level=1, duration=5)
        elif b == "pass":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        if b == "False":
            pass
        elif b == "shps":
            self.hasToOpenSectorLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

        if self.hasToOpenSectorLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeSectorLayers, on_finished=self.runOpenTemporaryFiles)
        else:
            # Not to run task
            return
        self.extent = self.iface.mapCanvas().extent()
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    """Tools"""

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
        # if not self.getSelectedFeaturesIds():
          # return
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        # , c_char_p, c_char_p)
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'),
                               self.tempFolder.encode('utf-8'))  # , self.nodeIds.encode('utf-8'), self.linkIds.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No issues ocurred")

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
            QGISRedUtils().setCurrentDirectory()
            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.ElevationInterpolation.argtypes = (
                c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.ElevationInterpolation.restype = c_char_p
            b = mydll.ElevationInterpolation(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
                'utf-8'), self.tempFolder.encode('utf-8'), self.ElevationFiles.encode('utf-8'))
            b = "".join(map(chr, b))  # bytes to string
            QApplication.restoreOverrideCursor()

            self.processCsharpResult(b, "Any elevation has been estimated")

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
        self.complementaryLayers = ["IsolationValves"]
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetInitialStatusPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.SetInitialStatusPipes.restype = c_char_p
        b = mydll.SetInitialStatusPipes(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(
            b, "Any isolation valve change status of pipes")

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
        self.reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Add  service connections to the model'), self.tr(
            'Do you want to include service connections as pipes (Yes) or only as nodes (No)?'), QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel))
        if self.reply == QMessageBox.Cancel:
            return

        asNode = "true"
        if self.reply == QMessageBox.Yes:  # Pipes
            asNode = "false"
        # Process
        self.complementaryLayers = ["ServiceConnections"]

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddConnections.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        b = mydll.AddConnections(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), asNode.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(
            b, "No Service Connections to include in the model")

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
        self.complementaryLayers = ["Hydrants"]

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        b = mydll.AddHydrants(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(b, "No Hydrants to include in the model")

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
        self.complementaryLayers = ["WashoutValves"]

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPurgeValves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddPurgeValves.restype = c_char_p
        b = mydll.AddPurgeValves(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(
            b, "No Washout Valves to include in the model")

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
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.DemandSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DemandSectors.restype = c_char_p
        b = mydll.DemandSectors(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Action
        self.hasToOpenNewLayers = False
        self.hasToOpenIssuesLayers = False
        self.hasToOpenSectorLayers = False
        if b == "False":
            pass
        elif b == "shps":
            self.hasToOpenSectorLayers = True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

        if self.hasToOpenSectorLayers:
            task1 = QgsTask.fromFunction(
                "", self.removeSectorLayers, on_finished=self.runOpenTemporaryFiles)
        else:
            # Not to run task
            return
        self.extent = self.iface.mapCanvas().extent()
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    """Experimental"""

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
        if not point == False:
            point1 = str(point.x()) + ":" + str(point.y())

        if self.iface.mapCanvas().mapTool() is self.selectTreePointTool:
            self.iface.mapCanvas().unsetMapTool(self.selectTreePointTool)

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Tree.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.Tree.restype = c_char_p
        b = mydll.Tree(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode(
            'utf-8'), self.tempFolder.encode('utf-8'), point1.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        # Action
        if b == "False" or b == "Cancelled":
            return
        elif b == "Select":
            self.selectPointToTree()
        elif "shps" in b:
            self.treeName = b.split('^')[1]
            task1 = QgsTask.fromFunction(
                "", self.removeTreeLayers, on_finished=self.runTreeProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runTreeProcess(self, exception=None, result=None):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode(
            'utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b = "".join(map(chr, b))  # bytes to string
        QApplication.restoreOverrideCursor()

        self.openTreeLayers()

        # Message
        if b == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def selectPointToTree(self):
        if self.iface.mapCanvas().mapTool() is self.selectTreePointTool:
            self.iface.mapCanvas().unsetMapTool(self.selectTreePointTool)
        else:
            self.selectTreePointTool = QGISRedSelectPointTool(
                None, self, self.runTree, 1)
            self.iface.mapCanvas().setMapTool(self.selectTreePointTool)

    def openTreeLayers(self):
        # CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid() == 0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        # Open layers
        treeGroup = self.getTreeGroup()
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.openLayer(crs, treeGroup, "Links_Tree",
                        tree=True)  # Use self.treeName
        utils.openLayer(crs, treeGroup, "Nodes_Tree")  # Use self.treeName
        group = self.getInputGroup()
        if group is not None:
            group.setItemVisibilityChecked(False)

    def getTreeGroup(self):
        treeGroup = QgsProject.instance().layerTreeRoot().findGroup("Tree")
        if treeGroup is None:
            queryGroup = self.getQueryGroup()
            treeGroup = queryGroup.insertGroup(0, "Tree")
        return treeGroup

    def removeTreeLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory,
                             self.NetworkName, self.iface)
        utils.removeLayers(["Links_Tree", "Nodes_Tree"])

        self.removeEmptyQuerySubGroup("Tree")
        # Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)
        raise Exception('')
