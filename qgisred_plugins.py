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
#Import resources
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
from .tools.qgisred_movenodes import QGISRedMoveNodesTool
from .tools.qgisred_multilayerSelection import QGISRedUtilsMultiLayerSelection
from .tools.qgisred_createPipe import QGISRedCreatePipeTool

# Others imports
import os
import datetime
import time
import tempfile
import platform
import base64
import shutil
from ctypes import*

#MessageBar Levels
# Info 0
# Warning 1
# Critical 2
# Success 3

class QGISRed:
    """QGIS Plugin Implementation."""
    #Common variables
    ResultDockwidget = None
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs", "Demands", "Sources"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns"]
    TemporalFolder = "Temporal folder"
    DependenciesVersion ="1.0.8.1"

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
        
        if not platform.system()=="Windows":
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("QGISRed only works in Windows"), level=2, duration=5)
            return
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'qgisred_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        #Toolbar
        self.toolbar = self.iface.addToolBar(u'QGISRed')
        self.toolbar.setObjectName(u'QGISRed')
        #Menu
        self.qgisredmenu = QMenu("&QGISRed", self.iface.mainWindow().menuBar())
        actions = self.iface.mainWindow().menuBar().actions()
        lastAction = actions[-1]
        self.iface.mainWindow().menuBar().insertMenu(lastAction, self.qgisredmenu )

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
                #actionBase.setDefaultAction(action)
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
            #self.iface.addPluginToMenu(self.menu,action)
            menubar.addAction(action)

        self.actions.append(action)

        if createDrop:
            return dropButton
        return action

    def initGui(self):
        if not platform.system()=="Windows":
            return
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        """Main buttons"""
        #File
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
            toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconProjectManager.png'
        self.add_action(icon_path, text=self.tr(u'Project manager'), callback=self.runProjectManager, menubar=self.fileMenu, toolbar=self.fileToolbar,
            actionBase = fileDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        self.add_action(icon_path, text=self.tr(u'Create project'), callback=self.runNewProject, menubar=self.fileMenu, toolbar=self.fileToolbar,
            actionBase = fileDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconImport.png'
        self.add_action(icon_path, text=self.tr(u'Import data'), callback=self.runImport, menubar=self.fileMenu, toolbar=self.fileToolbar,
            actionBase = fileDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCloseProject.png'
        self.add_action(icon_path, text=self.tr(u'Close project'), callback=self.runCloseProject, menubar=self.fileMenu, toolbar=self.fileToolbar,
            actionBase = fileDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        
        #Project
        #    #Menu
        self.projectMenu = self.qgisredmenu.addMenu(self.tr('Project'))
        self.projectMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconCreateProject.png'))
        #    #Toolbar
        self.projectToolbar = self.iface.addToolBar(self.tr(u'QGISRed Project'))
        self.projectToolbar.setObjectName(self.tr(u'QGISRed Project'))
        self.projectToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        projectDropButton = self.add_action(icon_path, text=self.tr(u'Project'), callback=self.runProjectToolbar, menubar=self.projectMenu, add_to_menu=False,
            toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        self.add_action(icon_path, text=self.tr(u'Edit project'), callback=self.runNewProject, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconEditOptions.png'
        self.add_action(icon_path, text=self.tr(u'Options'), callback=self.runEditOptions, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDefaultValues.png'
        self.add_action(icon_path, text=self.tr(u'Default Values'), callback=self.runDefaultValues, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSummary.png'
        self.add_action(icon_path, text=self.tr(u'Summary'), callback=self.runSummary, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconFlash.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Run Model'), callback=self.runModel, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconResults.png'
        self.add_action(icon_path, text=self.tr(u'Show Results Browser'), callback=self.runShowResultsDock, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconShpToInp.png'
        self.add_action(icon_path, text=self.tr(u'Export to INP'), callback=self.runExportInp, menubar=self.projectMenu, toolbar=self.projectToolbar,
            actionBase = projectDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        
        #Edit
        #    #Menu
        self.editionMenu = self.qgisredmenu.addMenu(self.tr('Edition'))
        self.editionMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconEdit.png'))
        #    #Toolbar
        self.editionToolbar = self.iface.addToolBar(self.tr(u'QGISRed Edition'))
        self.editionToolbar.setObjectName(self.tr(u'QGISRed Edition'))
        self.editionToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconEdit.png'
        editDropButton = self.add_action(icon_path, text=self.tr(u'Edition'), callback=self.runEditionToolbar, menubar=self.editionMenu, add_to_menu=False,
            toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPipe.png'
        self.addPipeButton = self.add_action(icon_path, text=self.tr(u'Add Pipe'), callback=self.runPaintPipe, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddTank.png'
        self.addTankButton = self.add_action(icon_path, text=self.tr(u'Add Tank'), callback=self.runSelectTankPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddReservoir.png'
        self.addReservoirButton = self.add_action(icon_path, text=self.tr(u'Add Reservoir'), callback=self.runSelectReservoirPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddValve.png'
        self.insertValveButton = self.add_action(icon_path, text=self.tr(u'Insert Valve in Pipe'), callback=self.runSelectValvePoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPump.png'
        self.insertPumpButton = self.add_action(icon_path, text=self.tr(u'Insert Pump in Pipe'), callback=self.runSelectPumpPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        self.editionToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconSelection.png'
        self.selectElementsButton = self.add_action(icon_path, text=self.tr(u'Select multiple elements'), callback=self.runSelectElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMoveElements.png'
        self.moveElementsButton = self.add_action(icon_path, text=self.tr(u'Move node elements'), callback=self.runMoveElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSplitPipe.png'
        self.splitPipeButton = self.add_action(icon_path, text=self.tr(u'Split Pipe'), callback=self.runSelectSplitPoint, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDeleteElements.png'
        self.removeElementsButton = self.add_action(icon_path, text=self.tr(u'Delete elements'), callback=self.runDeleteElements, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        self.editionToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconEdit.png'
        self.editElementButton = self.add_action(icon_path, text=self.tr(u'Edit Element Properties'), callback=self.runSelectPointProperties, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, checable=True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLinePlot.png'
        self.add_action(icon_path, text=self.tr(u'Edit Patterns and Curves'), callback=self.runPatternsCurves, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRules.png'
        self.add_action(icon_path, text=self.tr(u'Edit Controls'), callback=self.runControls, menubar=self.editionMenu, toolbar=self.editionToolbar,
            actionBase = editDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        
        
        #Verifications
        #    #Menu
        self.verificationsMenu = self.qgisredmenu.addMenu(self.tr('Verifications'))
        self.verificationsMenu.setIcon(QIcon(':/plugins/QGISRed/images/iconVerifications.png'))
        #    #Toolbar
        self.verificationsToolbar = self.iface.addToolBar(self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setObjectName(self.tr(u'QGISRed Verifications'))
        self.verificationsToolbar.setVisible(False)
        #    #Buttons
        icon_path = ':/plugins/QGISRed/images/iconVerifications.png'
        verificationsDropButton = self.add_action(icon_path, text=self.tr(u'Verifications'), callback=self.runVerificationsToolbar, menubar=self.verificationsMenu, add_to_menu=False,
            toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconValidate.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Validate General Data'), callback=self.runCheckDataM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconCommit.png'
        self.add_action(icon_path, text=self.tr(u'Commit changes'), callback=self.runCheckDataC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check overlapping elements'), callback=self.runCheckCoordinatesM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadC.png'
        self.add_action(icon_path, text=self.tr(u'Remove overlapping elements'), callback=self.runCheckCoordinatesC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconVerticesM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check for simplifying link vertices'), callback=self.runSimplifyVerticesM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconVerticesC.png'
        self.add_action(icon_path, text=self.tr(u'Simplify link vertices'), callback=self.runSimplifyVerticesC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconJoinM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check for joining consecutive pipes (diameter, material and year)'), callback=self.runCheckJoinPipesM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconJoinC.png'
        self.add_action(icon_path, text=self.tr(u'Join consecutive pipes (diameter, material and year)'), callback=self.runCheckJoinPipesC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check T Connections'), callback=self.runCheckTConncetionsM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsC.png'
        self.add_action(icon_path, text=self.tr(u'Create T Connections'), callback=self.runCheckTConncetionsC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check connectivity'), callback=self.runCheckConnectivityM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityC.png'
        self.add_action(icon_path, text=self.tr(u'Delete issolated subzones'), callback=self.runCheckConnectivityC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLengthM.png'
        dropButton = self.add_action(icon_path, text=self.tr(u'Check pipe lengths'), callback=self.runCheckLengthsM, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, createDrop= True, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLengthC.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Change pipe lengths'), callback=self.runCheckLengthsC, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = dropButton, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDiameters.png'
        self.add_action(icon_path, text=self.tr(u'Check diameters'), callback=self.runCheckDiameters, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconMaterial.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe materials'), callback=self.runCheckMaterials, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDate.png'
        self.add_action(icon_path, text=self.tr(u'Check pipe installation dates'), callback=self.runCheckInstallationDates, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydraulic.png'
        self.verificationsToolbar.addSeparator()
        self.add_action(icon_path, text=self.tr(u'Obtain hydraulic sectors'), callback=self.runHydraulicSectors, menubar=self.verificationsMenu, toolbar=self.verificationsToolbar,
            actionBase = verificationsDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        
        #Tools
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
            toolbar=self.toolbar, createDrop = True, addActionToDrop = False, add_to_toolbar =False, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRoughness.png'
        self.add_action(icon_path, text=self.tr(u'Set Roughness coefficient (from Material and Date)'), callback=self.runSetRoughness, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconInterpolate.png'
        self.add_action(icon_path, text=self.tr(u'Interpolate elevation from .asc files'), callback=self.runElevationInterpolation, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconStatus.png'
        self.add_action(icon_path, text=self.tr(u'Set pipe\'s initial status from issolated valves'), callback=self.runSetPipeStatus, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        self.toolsToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconConnections.png'
        self.add_action(icon_path, text=self.tr(u'Add connections to the model'), callback=self.runAddConnections, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconHydrants.png'
        self.add_action(icon_path, text=self.tr(u'Add hydrants to the model'), callback=self.runAddHydrants, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconPurges.png'
        self.add_action(icon_path, text=self.tr(u'Add purge valves to the model'), callback=self.runAddPurgeValves, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        self.toolsToolbar.addSeparator()
        icon_path = ':/plugins/QGISRed/images/iconDemandSector.png'
        self.add_action(icon_path, text=self.tr(u'Obtain demand sectors'), callback=self.runDemandSectors, menubar=self.toolsMenu, toolbar=self.toolsToolbar,
            actionBase = toolDropButton, add_to_toolbar =True, parent=self.iface.mainWindow())
        
        #About
        icon_path = ':/plugins/QGISRed/images/iconAbout.png'
        self.add_action(icon_path, text=self.tr(u'About...'), callback=self.runAbout, menubar=self.qgisredmenu, toolbar=self.toolbar, parent=self.iface.mainWindow())
        
        """Other options"""
        #Saving QGis project
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)
        
        #Issue layers
        self.issuesLayers = []
        for name in self.ownMainLayers:
            self.issuesLayers.append(name + "_Issues")
        
        #MapTools
        self.pointElementTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointElementTool.canvasClicked.connect(self.runProperties)
        self.pointElementTool.deactivated.connect(self.runUnselectPointProperties)
        self.pointValveTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointValveTool.canvasClicked.connect(self.runInsertValve)
        self.pointValveTool.deactivated.connect(self.runUnselectValvePoint)
        self.pointPumpTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointPumpTool.canvasClicked.connect(self.runInsertPump)
        self.pointPumpTool.deactivated.connect(self.runUnselectPumpPoint)
        self.pointTankTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointTankTool.canvasClicked.connect(self.runAddTank)
        self.pointTankTool.deactivated.connect(self.runUnselectTankPoint)
        self.pointReservoirTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointReservoirTool.canvasClicked.connect(self.runAddReservoir)
        self.pointReservoirTool.deactivated.connect(self.runUnselectReservoirPoint)
        self.pointDeleteElementTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointDeleteElementTool.canvasClicked.connect(self.runDeleteElement)
        self.pointDeleteElementTool.deactivated.connect(self.runUnselectDeleteElementPoint)
        self.pointSplitTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointSplitTool.canvasClicked.connect(self.runSplitPipe)
        self.pointSplitTool.deactivated.connect(self.runUnselectSplitPoint)
        
        #QGISRed dependencies
        self.checkDependencies()
        
        #SHPs temporal folder
        self.tempFolder = os.path.join(os.path.join(os.popen('echo %appdata%').read().strip(), "QGISRed"),"TempFiles")
        try: #create directory if does not exist
            os.stat(self.tempFolder)
        except:
            os.mkdir(self.tempFolder) 

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        dirpath = os.path.join(tempfile._get_default_tempdir(), "qgisred" + self.KeyTemp)
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            shutil.rmtree(dirpath)
        
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

    def createGqpFile(self):
        """Write a .gqp file with datetimes and opened files (or QGis project)"""
        gqp = os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")
        creationDate=""
        if os.path.exists(gqp):
            f= open(gqp, "r")
            lines = f.readlines()
            if len(lines)>=1:
                creationDate = lines[0].strip("\r\n")
            f.close()
        f = open(gqp, "w+")
        if creationDate=="":
            creationDate = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(creationDate + '\n')
        f.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
        
        qgsFilename =QgsProject.instance().fileName()
        if not qgsFilename=="":
            QGISRedUtils().writeFile(f, qgsFilename)
        else:
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
            #Inputs
            groupName = "Inputs"
            dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
            if dataGroup is None:
                f.write("[NoGroup]\n")
                for layer in reversed(layers):
                    QGISRedUtils().writeFile(f, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')
            else:
                QGISRedUtils().writeFile(f, "[Inputs]\n")
                self.writeLayersOfGroups(groupName, f, layers)
        f.close()

    def writeLayersOfGroups(self, groupName, file, layers):
        """Write the layer path in a file"""
        root = QgsProject.instance().layerTreeRoot()
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if not parent is None:
                if parent.parent().name() == groupName:
                    QGISRedUtils().writeFile(file, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')

    def defineCurrentProject(self):
        """Identifying the QGISRed current project"""
        self.NetworkName ="Network"
        self.ProjectDirectory = self.TemporalFolder
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            layerUri= layer.dataProvider().dataSourceUri().split("|")[0]
            for layerName in self.ownMainLayers:
                if "_" + layerName in layerUri:
                    self.ProjectDirectory = os.path.dirname(layerUri)
                    vectName = os.path.splitext(os.path.basename(layerUri))[0].split("_")
                    name =""
                    for part in vectName:
                        if part in self.ownMainLayers:
                            break
                        name = name + part + "_"
                    name = name.strip("_")
                    self.NetworkName = name
                    return

    def isOpenedProject(self):
        if self.isLayerOnEdition():
            return False
        qgsFilename =QgsProject.instance().fileName()
        if not qgsFilename=="":
            if QgsProject.instance().isDirty():
                #Save and continue
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("The project has changes. Please save them before continuing."), level=1)
                return False
            else:
                #Close the project and continue?
                reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Opened project'), self.tr('Do you want to close the current project and continue?'), QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers())>0:
                #Close files and continue?
                reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Opened layers'), self.tr('Do you want to close the current layers and continue?'), QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def isLayerOnEdition(self):
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for layer in layers:
            if layer.isEditable():
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some layer is in Edit Mode. Please, commit it before continuing."), level=1)
                return True
        return False

    def removeLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        raise Exception('')

    def removeDBFs(self, task, dbfs):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(dbfs, ".dbf")
        #task.finished(True)
        raise Exception('')

    def removeResultsLayers(self, task):
        resultsDirct = os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(resultsDirct, self.NetworkName + "_Base", self.iface)
        utils.removeLayers(self.resultsLayersToRemove)
        raise Exception('')

    def removeIssuesLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)
        raise Exception('')

    def removeLayersConnectivity(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.issuesLayers)
        utils.removeLayer("Links_Connectivity")
        self.removeEmptyQuerySubGroup("Connectivity")
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def removeHydraulicSectors(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(["Links_" + self.Sectors, "Nodes_" + self.Sectors])
        
        name = self.NetworkName + " Hydraulic Sectors"
        if "Demand" in self.Sectors:
            name = self.NetworkName + " Demand Sectors"
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(name)
        if not dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            root.removeChildNode(dataGroup)
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def removeComplementaryLayers(self, task):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        
        utils.removeLayers(self.complementaryLayers)
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def openElementLayers(self, task):
        if not self.opendedLayers:
            self.opendedLayers=True
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            if crs.srsid()==0:
                crs = QgsCoordinateReferenceSystem()
                crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
            #Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, crs, self.ownMainLayers, self.ownFiles)
            self.createGqpFile()
            
            self.setSelectedFeaturesById()
            raise Exception('')

    def activeInputGroup(self):
        if self.ResultDockwidget is None:
            return
        group = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if group is not None:
            group.setItemVisibilityChecked(not self.ResultDockwidget.isVisible())
        group = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if group is not None:
            group.setItemVisibilityChecked(self.ResultDockwidget.isVisible())

    def getInputGroup(self):
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def getQueryGroup(self):
        queryGroup = QgsProject.instance().layerTreeRoot().findGroup("Queries")
        if queryGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            queryGroup = netGroup.insertGroup(0,"Queries")
        return queryGroup

    def getIssuesGroup(self):
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Issues")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            inputGroup = netGroup.insertGroup(0,"Issues")
        return inputGroup

    def removeEmptyIssuesGroup(self):
        netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
        if netGroup is not None:
            issuesGroup = netGroup.findGroup("Issues")
            if issuesGroup is not None:
                if len(issuesGroup.findLayers())==0:
                    netGroup.removeChildNode(issuesGroup)

    def removeEmptyQuerySubGroup(self, name):
        netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
        if netGroup is not None:
            queryGroup = netGroup.findGroup("Queries")
            if queryGroup is not None:
                querySubGroup = queryGroup.findGroup(name)
                if querySubGroup is not None:
                    if len(querySubGroup.findLayers())==0:
                        queryGroup.removeChildNode(querySubGroup)
                if len(queryGroup.findLayers())==0:
                    netGroup.removeChildNode(queryGroup)

    def createBackup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.saveBackup(self.KeyTemp)

    def checkDependencies(self):
        valid = False
        gisredDir= QGISRedUtils().getGISRedFolder()
        if os.path.isdir(gisredDir):
            try:
                info = GetFileVersionInfo (os.path.join(gisredDir,"GISRed.QGisPlugins.dll"), "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                currentVersion = str(HIWORD(ms)) + "." + str(LOWORD(ms)) + "." + str(HIWORD(ls)) + "." + str(LOWORD(ls))
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
            link = '\"http://www.redhisp.webs.upv.es/files/QGISRed/' + self.DependenciesVersion + '/Installation_' + plat + '_' + lang + '.msi\"'
            request = QMessageBox.question(self.iface.mainWindow(), self.tr('QGISRed Dependencies'), self.tr('QGISRed plugin only runs in Windows OS and needs some dependencies (' + self.DependenciesVersion + '). Do you want to download and authomatically install them?'), QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No))
            if request == QMessageBox.Yes:
                import urllib.request
                localFile= tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".msi"
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
        if self.extent is not None:
            self.iface.mapCanvas().setExtent(self.extent)
            self.iface.mapCanvas().refresh()
            self.extent = None

    def getTolerance(self):
        #DPI
        LOGPIXELSX = 88
        user32 = windll.user32
        user32.SetProcessDPIAware()
        dc = user32.GetDC(0)
        pix_per_inch = windll.gdi32.GetDeviceCaps(dc, LOGPIXELSX)
        user32.ReleaseDC(0, dc)
        
        #CanvasPixels
        unitsPerPixel = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() # x WidthPixels --> m/px * px = metros
        #25.4 mm == inch
        un = 25.4/pix_per_inch # x WidthPixels -- > mm/px x px = mm
        #1mm * unitsPerPixel / un -->tolerance
        tolerance = 1 * unitsPerPixel/un
        return tolerance

    def getSelectedFeaturesIds(self):
        linkIdsList = []
        nodeIdsList = []
        self.selectedFids = {}
        
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                if layerName == "Sources" or layerName=="Demands":
                    continue
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/","\\"):
                    fids = []
                    for feature in layer.getSelectedFeatures():
                        fids.append(feature.id())
                        if layer.geometryType()==0:
                            nodeIdsList.append(str(feature['Id']))
                        else:
                            linkIdsList.append(str(feature['Id']))
                    self.selectedFids[layerName] = fids
        
        if 'NULL' in nodeIdsList or 'NULL' in linkIdsList:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some Ids are not defined. Commit before and try again."), level=1, duration=5)
            return False
        #Generate concatenate string for links and nodes
        self.linkIds = ""
        for id in linkIdsList:
            self.linkIds = self.linkIds + id + ';'
        self.nodeIds = ""
        for id in nodeIdsList:
            self.nodeIds = self.nodeIds + id + ';'
        return True

    def setSelectedFeaturesById(self):
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        mylayersNames = self.ownMainLayers
        for layer in layers:
            for layerName in mylayersNames:
                if layerName == "Sources" or layerName=="Demands":
                    continue
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + layerName + ".shp").replace("/","\\"):
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
        self.verificationsToolbar.setVisible(not self.verificationsToolbar.isVisible())

    def runToolsToolbar(self):
        self.toolsToolbar.setVisible(not self.toolsToolbar.isVisible())

    """File"""
    def runProjectManager(self):
        if not self.checkDependencies(): return
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            self.createGqpFile()

    def runNewProject(self):
        if not self.checkDependencies(): return
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        else:
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
            self.createGqpFile()

    def runImport(self):
        if not self.checkDependencies(): return
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        else:
            if self.isLayerOnEdition():
                return
        # show the dialog
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)

        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.createGqpFile()

    def runCloseProject(self):
        self.iface.newProject(True)

    def runCheckDataM(self):
        self.runCheckData()

    def runCheckDataC(self):
        self.runCheckData(True)

    def runCheckData(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        #os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckData.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckData.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.CheckData(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Input data is valid"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckDataProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCheckDataProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckDataProcess(self, exception=None, result=None):
        #Backup
        # if self.Process == "commit":
            # self.createBackup()
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckData.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckData.restype = c_char_p
        b = mydll.CheckData(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            #CRS
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            if crs.srsid()==0:
                crs = QgsCoordinateReferenceSystem()
                crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
            #Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Successful commit"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.createGqpFile()

    def runClearedProject(self):
        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()

    def runExportInp(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif not b=="Canceled":
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runModel(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
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
        layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        for nameLayer in myLayers:
            for layer in layers:
                    if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(resultPath, self.NetworkName + "_Base_" + nameLayer + ".shp").replace("/","\\"):
                        self.resultsLayersToRemove.append(nameLayer)
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction("", self.removeResultsLayers, on_finished=self.runModelProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runModelProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Compute.argtypes = (c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        elif b.startswith("[TimeLabels]"):
            #Open dock
            if self.ResultDockwidget is None:
                self.ResultDockwidget = QGISRedResultsDock(self.iface)
                self.iface.addDockWidget(Qt.RightDockWidgetArea, self.ResultDockwidget)
                self.ResultDockwidget.visibilityChanged.connect(self.activeInputGroup)
            self.ResultDockwidget.config(self.ProjectDirectory, self.NetworkName, b.replace("[TimeLabels]",""), self.resultsLayersToRemove)
            self.ResultDockwidget.show()
            group = self.getInputGroup()
            if group is not None:
                group.setItemVisibilityChecked(False)
            return
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=5)
        
        if self.ResultDockwidget is not None: #If some error, close the dock
            self.ResultDockwidget.close()

    def runShowResultsDock(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.ResultDockwidget is None:
            self.runModel()
        else:
            self.ResultDockwidget.show()

    def runShowResults(self):
        if not self.checkDependencies(): return
        #Open dock
        if self.ResultDockwidget is None:
            self.runModel()
        else:
            #Validations
            self.defineCurrentProject()
            if self.ProjectDirectory == self.TemporalFolder:
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
                return
            if not (self.NetworkName == self.ResultDockwidget.NetworkName and self.ProjectDirectory == self.ResultDockwidget.ProjectDirectory):
                self.runModel()
                return
            self.ResultDockwidget.show()

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()

    def runSummary(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AbstractReport.argtypes = (c_char_p, c_char_p)
        mydll.AbstractReport.restype = c_char_p
        b = mydll.AbstractReport(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runDefaultValues(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditDefaultValues.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditDefaultValues.restype = c_char_p
        b = mydll.EditDefaultValues(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction('Dismiss this message', self.removeLayers, on_finished=self.runDefaultValuesProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="Cancel":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runDefaultValuesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runEditOptions(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditOptions.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditOptions.restype = c_char_p
        b = mydll.EditOptions(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction('Dismiss this message', self.removeLayers, on_finished=self.runEditOptionsProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="Cancel":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runEditOptionsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runPatternsCurves(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditPatternsCurves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditPatternsCurves.restype = c_char_p
        b = mydll.EditPatternsCurves(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction('Dismiss this message', self.removeLayers, on_finished=self.runPatternsCurvesProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="Cancel":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runPatternsCurvesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runControls(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditControls.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditControls.restype = c_char_p
        b = mydll.EditControls(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction('Dismiss this message', self.removeLayers, on_finished=self.runControlsProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="Cancel":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runControlsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectPointProperties(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointElementTool:
            self.iface.mapCanvas().unsetMapTool(self.pointElementTool)
            self.runUnselectPointProperties()
        else:
            self.pointElementTool.setCursor(Qt.WhatsThisCursor)
            self.iface.mapCanvas().setMapTool(self.pointElementTool)
            self.editElementButton.setChecked(True)

    def runUnselectPointProperties(self):
        self.editElementButton.setChecked(False)

    def runProperties(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditElements.restype = c_char_p
        b = mydll.EditElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction('Dismiss this message', self.removeLayers, on_finished=self.runPropertiesProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="Cancel":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runPropertiesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ReplaceTemporalLayers.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ReplaceTemporalLayers.restype = c_char_p
        b = mydll.ReplaceTemporalLayers(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass #self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    """Layaout"""
    def runSelectElements(self):
        if type(self.iface.mapCanvas().mapTool()) is QGISRedUtilsMultiLayerSelection:
            self.iface.mapCanvas().unsetMapTool(self.selectElementsTool)
        else:
            self.selectElementsTool = QGISRedUtilsMultiLayerSelection(self.iface.mapCanvas(), self.selectElementsButton)
            self.iface.mapCanvas().setMapTool(self.selectElementsTool)

    def runMoveElements(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        
        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveNodesTool:
            self.iface.mapCanvas().unsetMapTool(self.moveNodesTool)
        else:
            if self.isLayerOnEdition():
                return
            self.moveNodesTool = QGISRedMoveNodesTool(self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.moveNodesTool)
            self.setCursor(Qt.CrossCursor)

    def runDeleteElements(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        
        if not self.getSelectedFeaturesIds():
            return
        if self.nodeIds=="" and self.linkIds == "":
            self.runSelectDeleteElementPoint()
            return
        
        self.removeElementsButton.setChecked(False)
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElements.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.RemoveElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.nodeIds.encode('utf-8'), self.linkIds.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("..."), level=1, duration=5) #used?
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runDeleteElementsProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runDeleteElementsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElements.restype = c_char_p
        b = mydll.RemoveElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.nodeIds.encode('utf-8'), self.linkIds.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        if self.Process == "commit":
            self.opendedLayers=False
            self.selectedFids ={}
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Delete elements process finished"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectDeleteElementPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointDeleteElementTool:
            self.iface.mapCanvas().unsetMapTool(self.pointDeleteElementTool)
            self.runUnselectDeleteElementPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointDeleteElementTool)
            self.removeElementsButton.setChecked(True)

    def runUnselectDeleteElementPoint(self):
        self.removeElementsButton.setChecked(False)

    def runDeleteElement(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveElementByPoint.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElementByPoint.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.RemoveElementByPoint(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Point not over any element"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runDeleteElementProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runDeleteElementProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveElementByPoint.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElementByPoint.restype = c_char_p
        b = mydll.RemoveElementByPoint(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Element removed"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runPaintPipe(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        
        if type(self.iface.mapCanvas().mapTool()) is QGISRedCreatePipeTool:
            self.createPipeTool.deactivated.disconnect(self.runCreatePipe)
            self.iface.mapCanvas().unsetMapTool(self.createPipeTool)
        else:
            if self.isLayerOnEdition():
                self.addPipeButton.setChecked(False)
                return
            self.createPipeTool = QGISRedCreatePipeTool(self.addPipeButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.createPipeTool.deactivated.connect(self.runCreatePipe)
            self.iface.mapCanvas().setMapTool(self.createPipeTool)

    def runCreatePipe(self):
        if self.createPipeTool.createdPipe:
            self.createPipeTool.createdPipe = False
            self.pipePoint =""
            for p in self.createPipeTool.mousePoints:
                self.pipePoint = self.pipePoint + str(p.x()) + ":" + str(p.y()) + ";"
            #C#Process:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QGISRedUtils().setCurrentDirectory()
            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.AddPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.AddPipe.restype = c_char_p
            step = "step2"
            # if toCommit:
                # step = "step2"
            b = mydll.AddPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.pipePoint.encode('utf-8'))
            b= "".join(map(chr, b)) #bytes to string
            QApplication.restoreOverrideCursor()
            
            #Message
            runAgain=False
            if b=="True":
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Pipe added"), level=1, duration=5)
            elif b=="False":
                pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
            elif b=="shps":
                runAgain=True
            elif b=="commit":
                runAgain=True
            else:
                self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
            
            #self.iface.mapCanvas().unsetMapTool(self.pointValveTool)
            
            # if not toCommit: #open shps of issues
                # if runAgain:
                    # #Process
                    # self.Process=b
                    # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                    # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                    # task1.run()
                    # QgsApplication.taskManager().addTask(task1)
            # else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCreatePipeProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCreatePipeProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddPipe.restype = c_char_p
        b = mydll.AddPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.pipePoint.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Pipe added"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectValvePoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointValveTool:
            self.iface.mapCanvas().unsetMapTool(self.pointValveTool)
            self.runUnselectValvePoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointValveTool)
            self.insertValveButton.setChecked(True)

    def runUnselectValvePoint(self):
        self.insertValveButton.setChecked(False)

    def runInsertValve(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.InsertValve(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Valve not over any pipe"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        #self.iface.mapCanvas().unsetMapTool(self.pointValveTool)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runInsertValveProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runInsertValveProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        b = mydll.InsertValve(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Valve inserted in pipe"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectPumpPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointPumpTool:
            self.iface.mapCanvas().unsetMapTool(self.pointPumpTool)
            self.runUnselectPumpPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointPumpTool)
            self.insertPumpButton.setChecked(True)

    def runUnselectPumpPoint(self):
        self.insertPumpButton.setChecked(False)

    def runInsertPump(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.InsertPump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Pump not over any pipe"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runInsertPumpProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runInsertPumpProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        b = mydll.InsertPump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Pump inserted in pipe"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectTankPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointTankTool:
            self.iface.mapCanvas().unsetMapTool(self.pointTankTool)
            self.runUnselectTankPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointTankTool)
            self.addTankButton.setChecked(True)

    def runUnselectTankPoint(self):
        self.addTankButton.setChecked(False)

    def runAddTank(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddTank.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddTank.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.AddTank(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("New Tank not over any node"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        #self.iface.mapCanvas().unsetMapTool(self.pointValveTool)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runAddTankProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddTankProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddTank.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddTank.restype = c_char_p
        b = mydll.AddTank(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Tank added"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectReservoirPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointReservoirTool:
            self.iface.mapCanvas().unsetMapTool(self.pointReservoirTool)
            self.runUnselectReservoirPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointReservoirTool)
            self.addReservoirButton.setChecked(True)

    def runUnselectReservoirPoint(self):
        self.addReservoirButton.setChecked(False)

    def runAddReservoir(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddReservoir.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddReservoir.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.AddReservoir(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Reservoir not over any end point of links"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runAddReservoirProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddReservoirProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddReservoir.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddReservoir.restype = c_char_p
        b = mydll.AddReservoir(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Reservoir added"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSelectSplitPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointSplitTool:
            self.iface.mapCanvas().unsetMapTool(self.pointSplitTool)
            self.runUnselectSplitPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointSplitTool)
            self.splitPipeButton.setChecked(True)

    def runUnselectSplitPoint(self):
        self.splitPipeButton.setChecked(False)

    def runSplitPipe(self, point, button):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.x = str(point.x())
        self.y = str(point.y())
        self.tolerance = str(self.getTolerance())
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.SplitPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Point not over any pipe"), level=1, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
                # #Process
                # self.Process=b
                # #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                # task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                # task1.run()
                # QgsApplication.taskManager().addTask(task1)
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runSplitPipeProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runSplitPipeProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        b = mydll.SplitPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'), self.tolerance.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Pipe splitted"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckCoordinatesM(self):
        self.runCheckCoordinates()

    def runCheckCoordinatesC(self):
        self.runCheckCoordinates(True)

    def runCheckCoordinates(self, toCommit = False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckCoordinates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckCoordinates.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.CheckCoordinates(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No overlapping elements found"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckCoordinatesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCheckCoordinatesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckCoordinatesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckCoordinates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckCoordinates.restype = c_char_p
        b = mydll.CheckCoordinates(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        

        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            #CRS
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            if crs.srsid()==0:
                crs = QgsCoordinateReferenceSystem()
                crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
            #Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Overlapping removed"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSimplifyVerticesM(self):
        self.runSimplifyVertices()

    def runSimplifyVerticesC(self):
        self.runSimplifyVertices(True)

    def runSimplifyVertices(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ChechkAlignedVertices.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ChechkAlignedVertices.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.ChechkAlignedVertices(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No aligned vertices to delete"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runSimplifyVerticesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runSimplifyVerticesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runSimplifyVerticesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ChechkAlignedVertices.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ChechkAlignedVertices.restype = c_char_p
        b = mydll.ChechkAlignedVertices(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            #CRS
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
            if crs.srsid()==0:
                crs = QgsCoordinateReferenceSystem()
                crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
            #Open layers
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Links vertices simplified"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckTConncetionsM(self):
        self.runCheckTConncetions()

    def runCheckTConncetionsC(self):
        self.runCheckTConncetions(True)

    def runCheckTConncetions(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckTConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckTConnections.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.CheckTConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No T connections to create"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCreateTConncetionsProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCreateTConncetionsProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCreateTConncetionsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckTConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckTConnections.restype = c_char_p
        b = mydll.CheckTConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("T connections created"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckJoinPipesM(self):
        self.runCheckJoinPipes()

    def runCheckJoinPipesC(self):
        self.runCheckJoinPipes(True)

    def runCheckJoinPipes(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckJoinPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckJoinPipes.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.CheckJoinPipes(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No pipes to join"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckJoinPipesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCheckJoinPipesProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckJoinPipesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckJoinPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckJoinPipes.restype = c_char_p
        b = mydll.CheckJoinPipes(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Pipes joined"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckConnectivityM(self):
        self.runCheckConnectivity()

    def runCheckConnectivityC(self):
        self.runCheckConnectivity(True)

    def runCheckConnectivity(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.LinesToDelete="0"
        if toCommit:
            dlg = QGISRedConnectivityToolDialog()
            # Run the dialog event loop
            dlg.exec_()
            result = dlg.ProcessDone
            if result:
                self.LinesToDelete = dlg.Lines
            else:
                return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckConnectivity.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        step = "step1"
        if toCommit:
            step = "step2"
        b = mydll.CheckConnectivity(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), "0".encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Only one zone"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        if not toCommit: #open shps of issues
            if runAgain:
                #Process
                self.Process=b
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayersConnectivity, on_finished=self.runCheckConnectivityProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)
        else:
            if runAgain:
                #Process
                self.Process=b
                self.extent = self.iface.mapCanvas().extent()
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCheckConnectivityProcess)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckConnectivityProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckConnectivity.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        b = mydll.CheckConnectivity(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.LinesToDelete.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
            self.removeEmptyIssuesGroup()
            if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_Connectivity.shp")):
                #Group
                connGroup = QgsProject.instance().layerTreeRoot().findGroup("Connectivity")
                if connGroup is None:
                    queryGroup = self.getQueryGroup()
                    connGroup = queryGroup.insertGroup(0,"Connectivity")
                utils.openLayer(crs, connGroup, "Links_Connectivity")
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Remove zones with less than {} pipes".format(self.Lines)), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues and Connectivity created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckLengthsM(self):
        self.runCheckLengths()

    def runCheckLengthsC(self):
        self.runCheckLengths(True)

    def runCheckLengths(self, toCommit=False):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        dlg = QGISRedLengthToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.Tolerance = dlg.Tolerance
            #Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            QGISRedUtils().setCurrentDirectory()
            mydll = WinDLL("GISRed.QGisPlugins.dll")
            mydll.CheckLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
            mydll.CheckLengths.restype = c_char_p
            step = "step1"
            if toCommit:
                step = "step2"
            b = mydll.CheckLengths(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Tolerance.encode('utf-8'), step.encode('utf-8'))
            b= "".join(map(chr, b)) #bytes to string
            
            QApplication.restoreOverrideCursor()
            
            #Message
            runAgain=False
            if b=="True":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No one pipe's length out of tolerance"), level=3, duration=5)
            elif b=="False":
                pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
            elif b=="shps":
                runAgain=True
            elif b=="commit":
                runAgain=True
            else:
                self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
            
            if not toCommit: #open shps of issues
                if runAgain:
                    #Process
                    self.Process=b
                    #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                    task1 = QgsTask.fromFunction("", self.removeIssuesLayers, on_finished=self.runCheckLengthsProcess)
                    task1.run()
                    QgsApplication.taskManager().addTask(task1)
            else:
                if runAgain:
                    #Process
                    self.Process=b
                    self.extent = self.iface.mapCanvas().extent()
                    #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                    task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runCheckLengthsProcess)
                    task1.run()
                    QgsApplication.taskManager().addTask(task1)

    def runCheckLengthsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckLengths.restype = c_char_p
        b = mydll.CheckLengths(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Tolerance.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Pipe's lengths modified"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckDiameters(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckDiameters.argtypes = (c_char_p, c_char_p)
        mydll.CheckDiameters.restype = c_char_p
        b = mydll.CheckDiameters(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on diameter checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some diameters have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckMaterials(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckMaterials.argtypes = (c_char_p, c_char_p)
        mydll.CheckMaterials.restype = c_char_p
        b = mydll.CheckMaterials(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on materials checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some materials have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckInstallationDates(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckInstallationDates.argtypes = (c_char_p, c_char_p)
        mydll.CheckInstallationDates.restype = c_char_p
        b = mydll.CheckInstallationDates(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on installation dates checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some installation dates have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSetRoughness(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        # if not self.getSelectedFeaturesIds():
            # return
        self.extent = self.iface.mapCanvas().extent()
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction(self.tr(u'Dismiss this message'), self.removeLayers, on_finished=self.runSetRoughnessProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runSetRoughnessProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p)#, c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))#, self.nodeIds.encode('utf-8'), self.linkIds.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues occurred in the roughness coefficient estimation"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the roughness coefficient estimation"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSetPipeStatus(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_IssolatedValves.shp")):
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Does not exist Issolated Valves SHP file"), level=1, duration=5)
            return
        
        #Process
        self.complementaryLayers = ["IssolatedValves"]
        self.extent = self.iface.mapCanvas().extent()
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction(self.tr(u'Dismiss this message'), self.removeComplementaryLayers, on_finished=self.runSetPipeStatusProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runSetPipeStatusProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetInitialStatusPipes.argtypes = (c_char_p, c_char_p)
        mydll.SetInitialStatusPipes.restype = c_char_p
        b = mydll.SetInitialStatusPipes(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Does not exist issolated valves to assign pipe\'s initial status"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after initial status setting"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddConnections(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Connections.shp")):
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Does not exist Connections SHP file"), level=1, duration=5)
            return
        
        #Question
        self.reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Add connections to the model'), self.tr('Do you want to include connections as pipes (Yes) or only as nodes (No)?'), QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel))
        if self.reply == QMessageBox.Cancel:
            return
            
        asNode = "true"
        if self.reply == QMessageBox.Yes: #Pipes
            asNode = "false"
        #Process
        self.complementaryLayers = ["Connections"]
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddConnections.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.AddConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), asNode.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No Connections to include in the model"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeComplementaryLayers, on_finished=self.runAddConnectionsProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddConnectionsProcess(self, exception=None, result=None):
        asNode = "true"
        if self.reply == QMessageBox.Yes: #Pipes
            asNode = "false"
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddConnections.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        b = mydll.AddConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), asNode.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, crs, self.complementaryLayers, [])
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Connections included in the model"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddHydrants(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Hydrants.shp")):
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Does not exist Hydrants SHP file"), level=1, duration=5)
            return
        
        #Process
        self.complementaryLayers = ["Hydrants"]
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.AddHydrants(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No Hydrants to include in the model"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeComplementaryLayers, on_finished=self.runAddHydrantsProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddHydrantsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        b = mydll.AddHydrants(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, crs, self.complementaryLayers, [])
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Hydrants included in the model"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddPurgeValves(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        if not os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_PurgeValves.shp")):
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Does not exist Purge Valves SHP file"), level=1, duration=5)
            return
        
        #Process
        self.complementaryLayers = ["PurgeValves"]
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPurgeValves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddPurgeValves.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.AddPurgeValves(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No Purge Valves to include in the model"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif b=="shps":
            runAgain=True
        elif b=="commit":
            runAgain=True
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)
        
        # if not toCommit: #open shps of issues
            # if runAgain:
        # else:
        if runAgain:
            #Process
            self.Process=b
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction("", self.removeComplementaryLayers, on_finished=self.runAddPurgeValvesProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddPurgeValvesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPurgeValves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddPurgeValves.restype = c_char_p
        b = mydll.AddPurgeValves(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if self.Process == "commit":
            inputGroup = self.getInputGroup()
            utils.openElementsLayers(inputGroup, crs, self.complementaryLayers, [])
            self.opendedLayers=False
            task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
            task1.run()
            QgsApplication.taskManager().addTask(task1)
        else:
            issuesGroup = self.getIssuesGroup()
            utils.openIssuesLayers(issuesGroup, crs, self.issuesLayers)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            if self.Process == "commit":
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Purge Valves included in the model"), level=3, duration=5)
            else:
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("SHPs of issues created"), level=3, duration=5)
        elif b=="False":
            pass #self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runElevationInterpolation(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.ElevationFiles = ""
        qfd = QFileDialog()
        path = ""
        filter = "asc(*.asc)"
        f = QFileDialog.getOpenFileNames(qfd, "Select ASC file", path, filter)
        if not f[1]=="":
            for fil in f[0]:
                self.ElevationFiles = self.ElevationFiles + fil + ";"
            
            #Process
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Dismiss this message'), self.removeLayers, on_finished=self.runElevationInterpolationProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runElevationInterpolationProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ElevationInterpolation.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ElevationInterpolation.restype = c_char_p
        b = mydll.ElevationInterpolation(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.ElevationFiles.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        self.opendedLayers=False
        task1 = QgsTask.fromFunction('Dismiss this message', self.openElementLayers, on_finished=self.setExtent)
        task1.run()
        QgsApplication.taskManager().addTask(task1)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after elevation interpolation"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runHydraulicSectors(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.Sectors= "HydraulicSectors"
        #Process
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction(self.tr(u'Dismiss this message'), self.removeHydraulicSectors, on_finished=self.runHydraulicSectorsProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runHydraulicSectorsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            #Group
            hydrGroup = QgsProject.instance().layerTreeRoot().findGroup("Hydraulic Sectors")
            if hydrGroup is None:
                queryGroup = self.getQueryGroup()
                hydrGroup = queryGroup.insertGroup(0,"Hydraulic Sectors")
            
            utils.openLayer(crs, hydrGroup, "Nodes_" + self.Sectors, sectors=True)
            utils.openLayer(crs, hydrGroup, "Links_" + self.Sectors, sectors=True)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No hydraulic sectors analisys done"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after hydraulic sectors analisys"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runDemandSectors(self):
        if not self.checkDependencies(): return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.Sectors= "DemandSectors"
        #Process
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction(self.tr(u'Dismiss this message'), self.removeHydraulicSectors, on_finished=self.runDemandSectorsProcess)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runDemandSectorsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.DemandSectors.argtypes = (c_char_p, c_char_p)
        mydll.DemandSectors.restype = c_char_p
        b = mydll.DemandSectors(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        
        #CRS
        crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            #Group
            demGroup = QgsProject.instance().layerTreeRoot().findGroup("Demand Sectors")
            if demGroup is None:
                queryGroup = self.getQueryGroup()
                demGroup = queryGroup.insertGroup(0,"Demand Sectors")
            
            utils.openLayer(crs, demGroup, "Nodes_" + self.Sectors, sectors=True)
            utils.openLayer(crs, demGroup, "Links_" + self.Sectors, sectors=True)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No demand sectors analisys done"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after demand sectors analisys"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)