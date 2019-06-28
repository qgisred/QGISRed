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

from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer 
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeNode
try: #QGis 3.x
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QApplication, QMenu, QFileDialog
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
except: #QGis 2.x
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QApplication, QMenu, QFileDialog
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
    from qgis.core import QgsMapLayerRegistry, QGis as Qgis
    #Import resources
    import resources2x
    # Import the code for the dialog
    from ui.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
    from ui.qgisred_newproject_dialog import QGISRedNewProjectDialog
    from ui.qgisred_import_dialog import QGISRedImportDialog
    from ui.qgisred_about_dialog import QGISRedAboutDialog
    from ui.qgisred_results_dock import QGISRedResultsDock
    from ui.qgisred_toolLength_dialog import QGISRedLengthToolDialog
    from ui.qgisred_toolConnectivity_dialog import QGISRedConnectivityToolDialog
    from qgisred_utils import QGISRedUtils

# Others imports
import os
import datetime
import time
import tempfile
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
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns"]
    TemporalFolder = "Temporal folder"

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
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
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param menubar: Menu where the action should be added
        :type menubar: QMenu

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = QGISRedNewProjectDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            toolbar.addAction(action)

        if add_to_menu:
            #self.iface.addPluginToMenu(self.menu,action)
            menubar.addAction(action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        #Create buttons/actions
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
            text=self.tr(u'Import to SHPs'),
            callback=self.runImport,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconValidate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Validate Data'),
            callback=self.runValidateModel,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconCommit.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Commit'),
            callback=self.runCommit,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconSaveProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Save project'),
            callback=self.runSaveProject,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconTools.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Tools'),
            callback=self.runToolbar,
            menubar=None,
            add_to_menu=False,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        #Toolbar
        self.toolbarTools = self.iface.addToolBar(u'QGISRed Tools')
        self.toolbarTools.setObjectName(u'QGISRed Tools')
        self.toolbarTools.setVisible(False)
        #Tools Menu
        self.qgisredmenuTools = self.qgisredmenu.addMenu(self.tr('Tools'))
        self.qgisredmenuTools.setIcon(QIcon(':/plugins/QGISRed/images/iconTools.png'))
        #Layaout Submenu
        self.qgisredmenuPathTools = self.qgisredmenuTools.addMenu(self.tr('Layout'))
        self.qgisredmenuPathTools.setIcon(QIcon(':/plugins/QGISRed/images/iconVertices.png'))
        icon_path = ':/plugins/QGISRed/images/iconDuplicate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check overlapping elements'),
            callback=self.runCheckCoordinates,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconVertices.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Simplify link vertices'),
            callback=self.runSimplifyVertices,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconTconnections.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Create T Connections'),
            callback=self.runCreateTConncetions,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconJoin.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Join consecutive pipes (diameter, material and year)'),
            callback=self.runJoinPipes,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconConnectivity.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check connectivity'),
            callback=self.runCheckConnectivity,
            menubar=self.qgisredmenuPathTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        #Properties Submenu
        self.qgisredmenuPropertiesTools = self.qgisredmenuTools.addMenu(self.tr('Properties'))
        self.qgisredmenuPropertiesTools.setIcon(QIcon(':/plugins/QGISRed/images/iconDiameters.png'))
        icon_path = ':/plugins/QGISRed/images/iconLength.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check pipe lengths'),
            callback=self.runCheckLengths,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDiameters.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check diameters'),
            callback=self.runCheckDiameters,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconMaterial.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check pipe materials'),
            callback=self.runCheckMaterials,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Check pipe installation dates'),
            callback=self.runCheckInstallationDates,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconRoughness.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Set Roughness coefficient (from Material and Date)'),
            callback=self.runSetRoughness,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconStatus.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Set pipe\'s initial status from issolated valves'),
            callback=self.runSetPipeStatus,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconInterpolate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Interpolate elevation from .asc files'),
            callback=self.runElevationInterpolation,
            menubar=self.qgisredmenuPropertiesTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        #Components Submenu
        self.qgisredmenuComponentsTools = self.qgisredmenuTools.addMenu(self.tr('Components'))
        self.qgisredmenuComponentsTools.setIcon(QIcon(':/plugins/QGISRed/images/iconConnections.png'))
        icon_path = ':/plugins/QGISRed/images/iconConnections.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add connections to the model'),
            callback=self.runAddConnections,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconHydrants.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add hydrants to the model'),
            callback=self.runAddHydrants,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconPurges.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Add purge valves to the model'),
            callback=self.runAddPurgeValves,
            menubar=self.qgisredmenuComponentsTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        #Components Submenu
        self.qgisredmenuSectorsTools = self.qgisredmenuTools.addMenu(self.tr('Sectorization'))
        self.qgisredmenuSectorsTools.setIcon(QIcon(':/plugins/QGISRed/images/iconDemandSector.png'))
        icon_path = ':/plugins/QGISRed/images/iconHydraulic.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Obtain hydraulic sectors'),
            callback=self.runHydraulicSectors,
            menubar=self.qgisredmenuSectorsTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconDemandSector.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Obtain demand sectors'),
            callback=self.runDemandSectors,
            menubar=self.qgisredmenuSectorsTools,
            toolbar=self.toolbarTools,
            parent=self.iface.mainWindow())
        
        #Export and run
        icon_path = ':/plugins/QGISRed/images/iconShpToInp.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Export model to INP'),
            callback=self.runExportInp,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconRunModel.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Run model && show results'),
            callback=self.runModel,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/images/iconAbout.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'About...'),
            callback=self.runAbout,
            menubar=self.qgisredmenu,
            toolbar=self.toolbar,
            parent=self.iface.mainWindow())
        
        #Copy necessary files regarding os architecture
        from shutil import copyfile
        import platform
        if "64bit" in str(platform.architecture()):
            folder = "x64"
        else:
            folder = "x86"
        currentDirectory = os.path.join(os.path.dirname(__file__), "dlls")
        plataformDirectory = os.path.join(currentDirectory, folder)
        try:
            copyfile(os.path.join(plataformDirectory, "shapelib.dll"), os.path.join(currentDirectory, "shapelib.dll"))
            copyfile(os.path.join(plataformDirectory, "epanet2.dll"), os.path.join(currentDirectory, "epanet2.dll"))
            copyfile(os.path.join(plataformDirectory, "GISRed.QGisPlugins.dll"), os.path.join(currentDirectory, "GISRed.QGisPlugins.dll"))
            if folder == "x64":
                copyfile(os.path.join(plataformDirectory, "ucrtbased.dll"), os.path.join(currentDirectory, "ucrtbased.dll"))
                copyfile(os.path.join(plataformDirectory, "vcruntime140d.dll"), os.path.join(currentDirectory, "vcruntime140d.dll"))
        except:
            pass
        
        QgsProject.instance().projectSaved.connect(self.runSaveProject)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        if self.ResultDockwidget is not None:
            self.ResultDockwidget.close()
            self.iface.removeDockWidget(self.ResultDockwidget)
            self.ResultDockwidget = None
        
        for action in self.actions:
            #self.iface.removePluginMenu(self.tr(u'&QGISRed'), action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        del self.toolbarTools
        
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
            try: #QGis 3.x
                layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
            except: #QGis 2.x
                layers = self.iface.legendInterface().layers()
            #Inputs
            groupName = self.NetworkName + " Inputs"
            dataGroup = QgsProject.instance().layerTreeRoot().findGroup(groupName)
            if dataGroup is None:
                f.write("[NoGroup]\n")
                for layer in reversed(layers):
                    QGISRedUtils().writeFile(f, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')
            else:
                QGISRedUtils().writeFile(f, "[" + self.NetworkName + " Inputs]\n")
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
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
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
        for layer in self.iface.mapCanvas().layers():
            if layer.isEditable():
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some layer is in Edit Mode. Plase, commit it before continuing."), level=1)
                return True
        return False

    def removeLayers(self, task, wait_time):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def removeLayersConnectivity(self, task, wait_time):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        
        utils.removeLayer("Links_Connectivity")
        
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Connectivity")
        if not dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            root.removeChildNode(dataGroup)
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def removeHydraulicSectors(self, task, wait_time):
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

    def removeComplementaryLayers(self, task, wait_time):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".dbf")
        
        utils.removeLayers(self.complementaryLayers)
        raise Exception('') #Avoiding errors with v3.x with shps and dbfs in use after deleting (use of QTasks)

    def runProjectManager(self):
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

    def runValidateModel(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ValidateModel.argtypes = (c_char_p, c_char_p)
        mydll.ValidateModel.restype = c_char_p
        b = mydll.ValidateModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        #Messages
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Input data is valid"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in data validation"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCommit(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runCommitProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runCommitProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runCommitProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CommitModel.argtypes = (c_char_p, c_char_p)
        mydll.CommitModel.restype = c_char_p
        b = mydll.CommitModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Successful commit"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the commit process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSaveProject(self):
        self.defineCurrentProject()
        if not self.ProjectDirectory == self.TemporalFolder:
            self.createGqpFile()

    def runExportInp(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif not b=="Canceled":
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runModel(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        #Open dock
        if self.ResultDockwidget is None:
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.ResultDockwidget)
        self.ResultDockwidget.config(self.ProjectDirectory, self.NetworkName)
        self.ResultDockwidget.show()

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()

    """Tools"""
    def runToolbar(self):
        # show the dialog
        self.toolbarTools.setVisible(not self.toolbarTools.isVisible())

    def runCheckCoordinates(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Question
        self.reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Check overlapping elements'), 'Do you want commit the changes?', QMessageBox.Yes, QMessageBox.No)
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runCheckCoordinatesProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runCheckCoordinatesProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runCheckCoordinatesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckCoordinates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckCoordinates.restype = c_char_p
        commit = "false"
        if self.reply == QMessageBox.Yes:
            commit = "true"
        b = mydll.CheckCoordinates(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), commit.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No overlapping elements found"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSimplifyVertices(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runSimplifyVerticesProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runSimplifyVerticesProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runSimplifyVerticesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.DeleteAlignedVertices.argtypes = (c_char_p, c_char_p)
        mydll.DeleteAlignedVertices.restype = c_char_p
        b = mydll.DeleteAlignedVertices(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Simplify link vertices completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCreateTConncetions(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runCreateTConncetionsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runCreateTConncetionsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runCreateTConncetionsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateTConnections.argtypes = (c_char_p, c_char_p)
        mydll.CreateTConnections.restype = c_char_p
        b = mydll.CreateTConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No T Connections created"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some connection have been created"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckLengths(self):
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
            if dlg.Modify:
                self.Modify = "true"
            else:
                self.Modify= "false"
            #Process
            if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
                try:
                    self.removeLayers(None,0)
                except:
                    pass
                self.runCheckLengthsProcess()
            else:  #QGis 3.x
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runCheckLengthsProcess, wait_time=0)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckLengthsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckLengths.restype = c_char_p
        b = mydll.CheckLengths(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Tolerance.encode('utf-8'), self.Modify.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No lengths out of tolerance"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some length differences are bigger than tolerance"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckDiameters(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckDiameters.argtypes = (c_char_p, c_char_p)
        mydll.CheckDiameters.restype = c_char_p
        b = mydll.CheckDiameters(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on diameter checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some diameters have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckMaterials(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckMaterials.argtypes = (c_char_p, c_char_p)
        mydll.CheckMaterials.restype = c_char_p
        b = mydll.CheckMaterials(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on materials checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some materials have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckInstallationDates(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckInstallationDates.argtypes = (c_char_p, c_char_p)
        mydll.CheckInstallationDates.restype = c_char_p
        b = mydll.CheckInstallationDates(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues on installation dates checking"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some installation dates have unexpected values"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSetRoughness(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runSetRoughnessProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runSetRoughnessProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runSetRoughnessProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues occurred in the roughness coefficient estimation"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the roughness coefficient estimation"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runJoinPipes(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeLayers(None,0)
            except:
                pass
            self.runJoinPipesProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runJoinPipesProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runJoinPipesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.JoinPipes.argtypes = (c_char_p, c_char_p)
        mydll.JoinPipes.restype = c_char_p
        b = mydll.JoinPipes(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No issues occurred joining pipes"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred joining pipes"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runCheckConnectivity(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        dlg = QGISRedConnectivityToolDialog()
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        if result:
            self.ConnectivityDialog = dlg
            #Process
            if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
                try:
                    self.removeLayersConnectivity(None,0)
                except:
                    pass
                self.runCheckConnectivityProcess()
            else:  #QGis 3.x
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayersConnectivity, on_finished=self.runCheckConnectivityProcess, wait_time=0)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runCheckConnectivityProcess(self, exception=None, result=None):
        lines = self.ConnectivityDialog.Lines
        if not self.ConnectivityDialog.Remove:
            lines = "0"
        if self.ConnectivityDialog.Export:
            export = "true"
        else:
            export = "false"
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CheckConnectivity.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        b = mydll.CheckConnectivity(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), export.encode('utf-8'), lines.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        if self.ConnectivityDialog.Export:
            if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_Connectivity.shp")):
                #Group
                dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Connectivity")
                if dataGroup is None:
                    root = QgsProject.instance().layerTreeRoot()
                    dataGroup = root.insertGroup(0,self.NetworkName + " Connectivity")
                
                utils.openLayer(crs, dataGroup, "Links_Connectivity")
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No connectivity analisys done"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after connectivity analisys"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runSetPipeStatus(self):
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
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeComplementaryLayers(None,0)
            except:
                pass
            self.runSetPipeStatusProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeComplementaryLayers, on_finished=self.runSetPipeStatusProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runSetPipeStatusProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.SetInitialStatusPipes.argtypes = (c_char_p, c_char_p)
        mydll.SetInitialStatusPipes.restype = c_char_p
        b = mydll.SetInitialStatusPipes(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.complementaryLayers, [])
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Does not exist issolated valves to assign pipe\'s initial status"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after initial status setting"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddConnections(self):
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
        self.reply = QMessageBox.question(self.iface.mainWindow(), self.tr('Add connections to the model'), 'Do you want to include connections as pipes (Yes) or only as nodes (No)?', QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel)
        if self.reply == QMessageBox.Cancel:
            return
        #Process
        self.complementaryLayers = ["Connections"]
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeComplementaryLayers(None,0)
            except:
                pass
            self.runAddConnectionsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeComplementaryLayers, on_finished=self.runAddConnectionsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddConnectionsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        
        asNode = "true"
        if self.reply == QMessageBox.Yes: #Pipes
            asNode = "false"
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        b = mydll.AddConnections(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), asNode.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.complementaryLayers, [])
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Does not exist connections to include in the model"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after adding connections"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddHydrants(self):
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
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeComplementaryLayers(None,0)
            except:
                pass
            self.runAddHydrantsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeComplementaryLayers, on_finished=self.runAddHydrantsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddHydrantsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        b = mydll.AddHydrants(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.complementaryLayers, [])
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Does not exist hydrants to include in the model"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after adding hyddrants"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runAddPurgeValves(self):
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
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeComplementaryLayers(None,0)
            except:
                pass
            self.runAddPurgeValvesProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeComplementaryLayers, on_finished=self.runAddPurgeValvesProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runAddPurgeValvesProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.AddPurgeValves.argtypes = (c_char_p, c_char_p)
        mydll.AddPurgeValves.restype = c_char_p
        b = mydll.AddPurgeValves(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.complementaryLayers, [])
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Does not exist purge valves to include in the model"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after adding purge valves"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runElevationInterpolation(self):
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
        if len(f)>0:
            for fil in f:
                self.ElecationFiles = self.ElecationFiles + fil + ";"
            
            #Process
            if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
                try:
                    self.removeLayers(None,0)
                except:
                    pass
                self.runElevationInterpolationProcess()
            else:  #QGis 3.x
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeLayers, on_finished=self.runElevationInterpolationProcess, wait_time=0)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def runElevationInterpolationProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ElevationInterpolation.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ElevationInterpolation.restype = c_char_p
        b = mydll.ElevationInterpolation(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.ElecationFiles.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after elevation interpolation"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runHydraulicSectors(self):
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.Sectors= "HydraulicSectors"
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeHydraulicSectors(None,0)
            except:
                pass
            self.runHydraulicSectorsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeHydraulicSectors, on_finished=self.runHydraulicSectorsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runHydraulicSectorsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            #Group
            dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Hydraulic Sectors")
            if dataGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                dataGroup = root.insertGroup(0,self.NetworkName + " Hydraulic Sectors")
            
            utils.openLayer(crs, dataGroup, "Nodes_" + self.Sectors)
            utils.openLayer(crs, dataGroup, "Links_" + self.Sectors)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No hydraulic sectors analisys done"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after hydraulic sectors analisys"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)

    def runDemandSectors(self):
        return
        #Validations
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No valid project is opened"), level=1, duration=5)
            return
        if self.isLayerOnEdition():
            return
        
        self.Sectors= "DemandSectors"
        #Process
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeHydraulicSectors(None,0)
            except:
                pass
            self.runDemandSectorsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(self.tr(u'Remove layers'), self.removeHydraulicSectors, on_finished=self.runDemandSectorsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def runDemandSectorsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(__file__), "dlls"))
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #CRS
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        #Open layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if os.path.exists(os.path.join(self.ProjectDirectory, self.NetworkName + "_Links_" + self.Sectors + ".shp")):
            #Group
            dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Demand Sectors")
            if dataGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                dataGroup = root.insertGroup(0,self.NetworkName + " Demand Sectors")
            
            utils.openLayer(crs, dataGroup, "Nodes_" + self.Sectors)
            utils.openLayer(crs, dataGroup, "Links_" + self.Sectors)
        
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("No demand sectors analisys done"), level=3, duration=5) #never is going to be true
        elif b=="False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some messages are available after demand sectors analisys"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), b, level=2, duration=5)