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
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer 
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeNode
from win32api import GetFileVersionInfo, LOWORD, HIWORD
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu, QFileDialog, QToolButton
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from qgis.core import Qgis, QgsTask, QgsApplication
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
from .qgisred_utils import QGISRedUtils
from .qgisred_movenodes import QGISRedMoveNodesTool
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
    DependenciesVersion ="1.0.7.1"

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

    def add_action(
        self,
        icon_path,
        text,
        callback,
        menubar,
        toolbar,
        checable=False,
        actionBase=None,
        createDrop=False,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):

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
        icon_path = ':/plugins/QGISRed/images/iconProjectManager.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Project manager'),
            callback=self.runProjectManager,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconCreateProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create/Edit project'),
            callback=self.runNewProject,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconImport.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Import data...'),
            callback=self.runImport,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconOptions.png' 
        opt = self.add_action(
            icon_path,
            text=self.tr(u'Options (future versions)...'),
            callback=self.runImport,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        opt.setEnabled(False)
        
        icon_path = ':/plugins/QGISRed/images/iconValidate.png' 
        validateDropButton = self.add_action(
            icon_path,
            text=self.tr(u'Validate Data'),
            callback=self.runCheckDataM,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconCommit.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Commit'),
            callback=self.runCheckDataC,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            actionBase = validateDropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        # icon_path = ':/plugins/QGISRed/images/iconSaveProject.png'
        # self.add_action(
            # icon_path,
            # text=self.tr(u'Save project'),
            # callback=self.runSaveProject,
            # menubar=self.qgisredmenu,
            # toolbar=self.toolbar,
            # parent=self.iface.mainWindow())
        
        """Data Submenu ans toolbar"""
        self.qgisredmenuDataTools = self.qgisredmenu.addMenu(self.tr('Data'))
        self.qgisredmenuDataTools.setIcon(QIcon(':/plugins/QGISRed/images/iconData.png'))
        #Toolbar
        self.toolbarData = self.iface.addToolBar(self.tr(u'QGISRed Data Tools'))
        self.toolbarData.setObjectName(self.tr(u'QGISRed Data Tools'))
        self.toolbarData.setVisible(False)
        icon_path = ':/plugins/QGISRed/images/iconSummary.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Summary'),
            callback=self.runAbstract,
            menubar=self.qgisredmenuDataTools,
            toolbar=self.toolbarData,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLinePlot.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Edit Patterns and Curves'),
            callback=self.runPatternsCurves,
            menubar=self.qgisredmenuDataTools,
            toolbar=self.toolbarData,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconRules.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Edit Controls'),
            callback=self.runControls,
            menubar=self.qgisredmenuDataTools,
            toolbar=self.toolbarData,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconEditProperties.png' 
        self.editElementButton = self.add_action(
            icon_path,
            text=self.tr(u'Edit Element Properties'),
            callback=self.runSelectPointProperties,
            menubar=self.qgisredmenuDataTools,
            toolbar=self.toolbarData,
            checable=True,
            parent=self.iface.mainWindow())
        
        """Toolbar and submenus"""
        #Tools Menu
        self.qgisredmenuTools = self.qgisredmenu.addMenu(self.tr('Tools'))
        self.qgisredmenuTools.setIcon(QIcon(':/plugins/QGISRed/images/iconTools.png'))
        """Layaout Submenu"""
        self.qgisredmenuPathTools = self.qgisredmenuTools.addMenu(self.tr('Layout'))
        self.qgisredmenuPathTools.setIcon(QIcon(':/plugins/QGISRed/images/iconVerticesM.png'))
        #Toolbar
        self.toolbarLayout = self.iface.addToolBar(self.tr(u'QGISRed Layout Tools'))
        self.toolbarLayout.setObjectName(self.tr(u'QGISRed Layout Tools'))
        self.toolbarLayout.setVisible(False)
        icon_path = ':/plugins/QGISRed/images/iconMoveElements.png' 
        self.moveElementsButton = self.add_action(
            icon_path,
            text=self.tr(u'Move node elements'),
            callback=self.runMoveElements,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            checable=True,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddValve.png' 
        self.insertValveButton = self.add_action(
            icon_path,
            text=self.tr(u'Insert Valve in Pipe'),
            callback=self.runSelectValvePoint,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            checable=True,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconAddPump.png' 
        self.insertPumpButton = self.add_action(
            icon_path,
            text=self.tr(u'Insert Pump in Pipe'),
            callback=self.runSelectPumpPoint,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            checable=True,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconDeleteValvePump.png' 
        self.removeValvePumpButton = self.add_action(
            icon_path,
            text=self.tr(u'Remove Valve or Pump'),
            callback=self.runSelectValvePumpPoint,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            checable=True,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconSplitPipe.png' 
        self.splitPipeButton = self.add_action(
            icon_path,
            text=self.tr(u'Split Pipe'),
            callback=self.runSelectSplitPoint,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            checable=True,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check overlapping elements'),
            callback=self.runCheckCoordinatesM,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconOverloadC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Remove overlapping elements'),
            callback=self.runCheckCoordinatesC,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconVerticesM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check for simplifying link vertices'),
            callback=self.runSimplifyVerticesM,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconVerticesC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Simplify link vertices'),
            callback=self.runSimplifyVerticesC,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check T Connections'),
            callback=self.runCheckTConncetionsM,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconTconnectionsC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Create T Connections'),
            callback=self.runCheckTConncetionsC,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconJoinM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check for joining consecutive pipes (diameter, material and year)'),
            callback=self.runCheckJoinPipesM,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconJoinC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Join consecutive pipes (diameter, material and year)'),
            callback=self.runCheckJoinPipesC,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconConnectivityM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check connectivity'),
            callback=self.runCheckConnectivityM,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconConnectivityC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Delete issolated subzones'),
            callback=self.runCheckConnectivityC,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarLayout,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        """Properties Submenu"""
        self.qgisredmenuPropertiesTools = self.qgisredmenuTools.addMenu(self.tr('Properties'))
        self.qgisredmenuPropertiesTools.setIcon(QIcon(':/plugins/QGISRed/images/iconDiameters.png'))
        self.toolbarProperties = self.iface.addToolBar(self.tr(u'QGISRed Properties Tools'))
        self.toolbarProperties.setObjectName(self.tr(u'QGISRed Properties Tools'))
        self.toolbarProperties.setVisible(False)
        icon_path = ':/plugins/QGISRed/images/iconLengthM.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'Check pipe lengths'),
            callback=self.runCheckLengthsM,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconLengthC.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Change pipe lengths'),
            callback=self.runCheckLengthsC,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDiameters.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check diameters'),
            callback=self.runCheckDiameters,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconMaterial.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check pipe materials'),
            callback=self.runCheckMaterials,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check pipe installation dates'),
            callback=self.runCheckInstallationDates,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconRoughness.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Set Roughness coefficient (from Material and Date)'),
            callback=self.runSetRoughness,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconInterpolate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Interpolate elevation from .asc files'),
            callback=self.runElevationInterpolation,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconStatus.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Set pipe\'s initial status from issolated valves'),
            callback=self.runSetPipeStatus,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarProperties,
            parent=self.iface.mainWindow())
        
        """Components Submenu"""
        self.qgisredmenuComponentsTools = self.qgisredmenuTools.addMenu(self.tr('Components'))
        self.qgisredmenuComponentsTools.setIcon(QIcon(':/plugins/QGISRed/images/iconConnections.png'))
        self.toolbarComponents = self.iface.addToolBar(self.tr(u'QGISRed Components Tools'))
        self.toolbarComponents.setObjectName(self.tr(u'QGISRed Components Tools'))
        self.toolbarComponents.setVisible(False)
        icon_path = ':/plugins/QGISRed/images/iconConnections.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add connections to the model'),
            callback=self.runAddConnections,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarComponents,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconHydrants.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add hydrants to the model'),
            callback=self.runAddHydrants,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarComponents,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconPurges.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add purge valves to the model'),
            callback=self.runAddPurgeValves,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarComponents,
            parent=self.iface.mainWindow())
        
        """Sectorization Submenu"""
        self.qgisredmenuSectorsTools = self.qgisredmenuTools.addMenu(self.tr('Sectorization'))
        self.qgisredmenuSectorsTools.setIcon(QIcon(':/plugins/QGISRed/images/iconDemandSector.png'))
        self.toolbarSectorization = self.iface.addToolBar(self.tr(u'QGISRed Sectorization Tools'))
        self.toolbarSectorization.setObjectName(self.tr(u'QGISRed Sectorization Tools'))
        self.toolbarSectorization.setVisible(False)
        icon_path = ':/plugins/QGISRed/images/iconHydraulic.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Obtain hydraulic sectors'),
            callback=self.runHydraulicSectors,
            menubar=self.qgisredmenuSectorsTools,
            toolbar=self.toolbarSectorization,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDemandSector.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Obtain demand sectors'),
            callback=self.runDemandSectors,
            menubar=self.qgisredmenuSectorsTools,
            toolbar=self.toolbarSectorization,
            parent=self.iface.mainWindow())
        
        #Data
        icon_path = ':/plugins/QGISRed/images/iconData.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Data Toolbar'),
            callback=self.runDataToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        #Tools
        icon_path = ':/plugins/QGISRed/images/iconTools.png' 
        dropButton = self.add_action(
            icon_path,
            text=self.tr(u'All Toolbars'),
            callback=self.runToolbars,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            createDrop = True,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconToolsLayout.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Layout Toolbar'),
            callback=self.runLayoutToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconToolsProperties.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Properties Toolbar'),
            callback=self.runPropertiesToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconToolsComponents.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Components Toolbar'),
            callback=self.runComponentsToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        icon_path = ':/plugins/QGISRed/images/iconToolsSectorization.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Sectorization Toolbar'),
            callback=self.runSectorizationToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            actionBase = dropButton,
            add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        #Export
        # icon_path = ':/plugins/QGISRed/images/iconExport.png' 
        # exportDropButton = self.add_action(
            # icon_path,
            # text=self.tr(u'Export to...'),
            # callback=self.runExportInp,
            # menubar=self.qgisredmenu,
            # toolbar=self.toolbar,
            # createDrop = True,
            # add_to_toolbar =False,
            # add_to_menu = False,
            # parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconShpToInp.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Export to INP'),
            callback=self.runExportInp,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            # actionBase = exportDropButton,
            # add_to_toolbar =False,
            parent=self.iface.mainWindow())
        
        #Run and Results
        icon_path = ':/plugins/QGISRed/images/iconFlash.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Run model'),
            callback=self.runModel,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        # icon_path = ':/plugins/QGISRed/images/iconResults.png' 
        # self.add_action(
            # icon_path,
            # text=self.tr(u'Result options'),
            # callback=self.runShowResults,
            # menubar=self.qgisredmenu,
            # toolbar=self.toolbar,
            # actionBase = runDropButton,
            # add_to_toolbar =False,
            # add_to_menu = False,
            # parent=self.iface.mainWindow())
        
        #About
        icon_path = ':/plugins/QGISRed/images/iconAbout.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'About...'),
            callback=self.runAbout,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        self.issuesLayers = []
        for name in self.ownMainLayers:
            self.issuesLayers.append(name + "_Issues")
        
        self.pointElementTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointElementTool.canvasClicked.connect(self.runProperties)
        self.pointElementTool.deactivated.connect(self.runUnselectPointProperties)
        self.pointValveTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointValveTool.canvasClicked.connect(self.runInsertValve)
        self.pointValveTool.deactivated.connect(self.runUnselectValvePoint)
        self.pointPumpTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointPumpTool.canvasClicked.connect(self.runInsertPump)
        self.pointPumpTool.deactivated.connect(self.runUnselectPumpPoint)
        self.pointValvePumpTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointValvePumpTool.canvasClicked.connect(self.runRemoveValvePump)
        self.pointValvePumpTool.deactivated.connect(self.runUnselectValvePumpPoint)
        self.pointSplitTool = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointSplitTool.canvasClicked.connect(self.runSplitPipe)
        self.pointSplitTool.deactivated.connect(self.runUnselectSplitPoint)
        
        
        self.checkDependencies()
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
        del self.toolbarLayout
        del self.toolbarProperties
        del self.toolbarComponents
        del self.toolbarSectorization
        
        if self.qgisredmenuSectorsTools:
            self.qgisredmenuSectorsTools.menuAction().setVisible(False)
        if self.qgisredmenuComponentsTools:
            self.qgisredmenuComponentsTools.menuAction().setVisible(False)
        if self.qgisredmenuPropertiesTools:
            self.qgisredmenuPropertiesTools.menuAction().setVisible(False)
        if self.qgisredmenuPathTools:
            self.qgisredmenuPathTools.menuAction().setVisible(False)
        if self.qgisredmenuTools:
            self.qgisredmenuTools.menuAction().setVisible(False)
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
            raise Exception('')

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

    """Main methods"""
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
            self.ResultDockwidget.config(self.ProjectDirectory, self.NetworkName, b.replace("[TimeLabels]",""))
            self.ResultDockwidget.show()
            return
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=5)
        
        if self.ResultDockwidget is not None: #If some error, close the dock
            self.ResultDockwidget.close()

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

    """Tools"""
    def runToolbars(self):
        vis = self.toolbarLayout.isVisible() or self.toolbarProperties.isVisible() or self.toolbarComponents.isVisible() or self.toolbarSectorization.isVisible()
        self.toolbarLayout.setVisible(not vis)
        self.toolbarProperties.setVisible(not vis)
        self.toolbarComponents.setVisible(not vis)
        self.toolbarSectorization.setVisible(not vis)

    def runLayoutToolbar(self):
        self.toolbarLayout.setVisible(not self.toolbarLayout.isVisible())

    def runPropertiesToolbar(self):
        self.toolbarProperties.setVisible(not self.toolbarProperties.isVisible())

    def runComponentsToolbar(self):
        self.toolbarComponents.setVisible(not self.toolbarComponents.isVisible())

    def runSectorizationToolbar(self):
        self.toolbarSectorization.setVisible(not self.toolbarSectorization.isVisible())

    """Data"""
    def runDataToolbar(self):
        self.toolbarData.setVisible(not self.toolbarData.isVisible())

    def runAbstract(self):
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
        print(self.x)
        print(self.y)
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.EditElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditElements.restype = c_char_p
        b = mydll.EditElements(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.tempFolder.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
    def runMoveElements(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        
        if type(self.iface.mapCanvas().mapTool()) is QGISRedMoveNodesTool:
            self.iface.mapCanvas().unsetMapTool(self.moveNodesTool)
        else:
            self.moveNodesTool = QGISRedMoveNodesTool(self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName)
            self.iface.mapCanvas().setMapTool(self.moveNodesTool)
            self.setCursor(Qt.CrossCursor)

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
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.InsertValve(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        b = mydll.InsertValve(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.InsertPump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        b = mydll.InsertPump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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

    def runSelectValvePumpPoint(self):
        #Take account the mouse click on QGis:
        if self.iface.mapCanvas().mapTool() is self.pointValvePumpTool:
            self.iface.mapCanvas().unsetMapTool(self.pointValvePumpTool)
            self.runUnselectValvePumpPoint()
        else:
            self.iface.mapCanvas().setMapTool(self.pointValvePumpTool)
            self.removeValvePumpButton.setChecked(True)

    def runUnselectValvePumpPoint(self):
        self.removeValvePumpButton.setChecked(False)

    def runRemoveValvePump(self, point, button):
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
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveValvePump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveValvePump.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.RemoveValvePump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
        b= "".join(map(chr, b)) #bytes to string
        QApplication.restoreOverrideCursor()
        
        #Message
        runAgain=False
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Pump not over any valve or pump"), level=1, duration=5)
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
            task1 = QgsTask.fromFunction("", self.removeLayers, on_finished=self.runRemoveValvePumpProcess)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runRemoveValvePumpProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.RemoveValvePump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveValvePump.restype = c_char_p
        b = mydll.RemoveValvePump(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
                self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Valve/Pump removed"), level=3, duration=5)
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
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        step = "step2"
        # if toCommit:
            # step = "step2"
        b = mydll.SplitPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), step.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        b = mydll.SplitPipe(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Process.encode('utf-8'), self.x.encode('utf-8'), self.y.encode('utf-8'))
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
        self.extent = self.iface.mapCanvas().extent()
        #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
        task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runSetRoughnessProcess, wait_time=0)
        task1.run()
        QgsApplication.taskManager().addTask(task1)

    def runSetRoughnessProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
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
        task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeComplementaryLayers, on_finished=self.runSetPipeStatusProcess, wait_time=0)
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
        
        self.ElecationFiles = ""
        qfd = QFileDialog()
        path = ""
        filter = "asc(*.asc)"
        f = QFileDialog.getOpenFileNames(qfd, "Select ASC file", path, filter)
        if not f[1]=="":
            for fil in f:
                self.ElecationFiles = self.ElecationFiles + fil + ";"
            
            #Process
            self.extent = self.iface.mapCanvas().extent()
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runElevationInterpolationProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runElevationInterpolationProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QGISRedUtils().setCurrentDirectory()
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ElevationInterpolation.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ElevationInterpolation.restype = c_char_p
        b = mydll.ElevationInterpolation(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.ElecationFiles.encode('utf-8'))
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
        task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeHydraulicSectors, on_finished=self.runHydraulicSectorsProcess, wait_time=0)
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
        task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeHydraulicSectors, on_finished=self.runDemandSectorsProcess, wait_time=0)
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