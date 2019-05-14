# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QGISRed
                                 A QGIS plugin
 Some util tools for GISRed
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
from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsLayerTreeNode

try: #QGis 3.x
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QAction, QMessageBox, QApplication
    from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
    #Import resources
    from . import resources3x
    # Import the code for the dialog
    from .qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
    from .qgisred_newproject_dialog import QGISRedNewProjectDialog
    from .qgisred_import_dialog import QGISRedImportDialog
    from .qgisred_exportinp_dialog import QGISRedExportInpDialog
    from .qgisred_about_dialog import QGISRedAboutDialog
    from .qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from PyQt4.QtGui import QAction, QMessageBox, QIcon, QApplication
    from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
    from qgis.core import QgsMapLayerRegistry
    #Import resources
    import resources2x
    # Import the code for the dialog
    from qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
    from qgisred_newproject_dialog import QGISRedNewProjectDialog
    from qgisred_import_dialog import QGISRedImportDialog
    from qgisred_exportinp_dialog import QGISRedExportInpDialog
    from qgisred_about_dialog import QGISRedAboutDialog
    from qgisred_utils import QGISRedUtils

# Others imports
import os
import os.path
import datetime
from time import strftime
from ctypes import*

#MessageBar Levels
# Info 0
# Warning 1
# Critical 2
# Success 3

class QGISRed:
    """QGIS Plugin Implementation."""
    #Project variables
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    ownFiles = ["Curves", "Controls", "Patterns", "Rules", "Options", "PropertyValues"]
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
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'qgisred_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QGISRed')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QGISRed')
        self.toolbar.setObjectName(u'QGISRed')

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
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QGISRed/iconProjectManager.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QGISRed project manager'),
            callback=self.runProjectManager,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconSaveProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Save QGISRed project'),
            callback=self.runSaveProject,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconCreateProject.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Create/Edit QGISRed project'),
            callback=self.runNewProject,
            parent=self.iface.mainWindow())
        
        icon_path = ':/plugins/QGISRed/iconImport.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Import to SHPs'),
            callback=self.runImport,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconValidate.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Validate Model'),
            callback=self.runValidateModel,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconCommit.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Commit'),
            callback=self.runCommit,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconShpToInp.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Export model to INP'),
            callback=self.runExportInp,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconRunModel.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'Run model && show results'),
            callback=self.runModel,
            parent=self.iface.mainWindow())

        icon_path = ':/plugins/QGISRed/iconAbout.png' 
        self.add_action(
            icon_path,
            text=self.tr(u'About...'),
            callback=self.runAbout,
            parent=self.iface.mainWindow())
        
        from shutil import copyfile
        import platform
        if "64bit" in str(platform.architecture()):
            folder = "x64"
        else:
            folder = "x86"
        currentDirectory = os.path.join(os.path.dirname(__file__), "dlls")
        plataformDirectory = os.path.join(currentDirectory, folder)
        copyfile(os.path.join(plataformDirectory, "shapelib.dll"), os.path.join(currentDirectory, "shapelib.dll"))
        copyfile(os.path.join(plataformDirectory, "GISRed.QGisPlugins.dll"), os.path.join(currentDirectory, "GISRed.QGisPlugins.dll"))

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QGISRed'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def createGqpFile(self):
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
        root = QgsProject.instance().layerTreeRoot()
        for layer in reversed(layers):
            parent = root.findLayer(layer.id())
            if not parent is None:
                if parent.parent().name() == groupName:
                    QGISRedUtils().writeFile(file, layer.dataProvider().dataSourceUri().split("|")[0] + '\n')

    def defineCurrentProject(self):
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
                #Guardar y continuar
                self.iface.messageBar().pushMessage("Warning", "The project has changes. Please save them before continuing.", level=1)
            else:
                #Cerrar proyecto y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened project', 'Do you want to close the current project and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        else:
            if len(self.iface.mapCanvas().layers())>0:
                #Cerrar archivos y continuar?
                reply = QMessageBox.question(self.iface.mainWindow(), 'Opened layers', 'Do you want to close the current layers and continue?', QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    QgsProject.instance().clear()
                    return True
                else:
                    return False
        return True

    def isLayerOnEdition(self):
        for layer in self.iface.mapCanvas().layers():
            if layer.isEditable():
                self.iface.messageBar().pushMessage("Warning", "Some layer is in Edit Mode. Plase, commit it before continuing.", level=1)
                return True
        return False

    def runProjectManager(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        # show the dialog
        dlg = QGISRedProjectManagerDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)

        # Run the dialog event loop
        dlg.exec_()
        # See if OK was pressed
        result = dlg.ProcessDone
        if result:
            self.NetworkName = dlg.NetworkName
            self.ProjectDirectory = dlg.ProjectDirectory
            self.createGqpFile()

    def runSaveProject(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
        else:
            self.createGqpFile()

    def runNewProject(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        # show the dialog
        dlg = QGISRedNewProjectDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)
        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        # See if OK was pressed
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.createGqpFile()

    def runImport(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            if not self.isOpenedProject():
                return
        # show the dialog
        dlg = QGISRedImportDialog()
        dlg.config(self.iface, self.ProjectDirectory, self.NetworkName)

        # Run the dialog event loop
        dlg.exec_()
        result = dlg.ProcessDone
        # See if OK was pressed
        if result:
            self.ProjectDirectory = dlg.ProjectDirectory
            self.NetworkName = dlg.NetworkName
            self.createGqpFile()

    def runValidateModel(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.ValidateModel.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ValidateModel.restype = c_char_p
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        b = mydll.ValidateModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Topology is valid", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def runCommit(self):
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
            return
        if self.isLayerOnEdition():
            return
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        #Remove layers
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        utils.removeLayers(self.ownMainLayers)
        utils.removeLayers(self.ownFiles, ".csv")
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CommitModel.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CommitModel.restype = c_char_p
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        b = mydll.CommitModel(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), elements.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Group
        dataGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName + " Inputs")
        if dataGroup is None:
            root = QgsProject.instance().layerTreeRoot()
            dataGroup = root.addGroup(self.NetworkName + " Inputs")
        
        #Open layers
        try: #QGis 3.x
            crs = self.iface.mapCanvas().mapSettings().destinationCrs()
        except: #QGis 2.x
            crs = self.iface.mapCanvas().mapRenderer().destinationCrs()
        if crs.srsid()==0:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(3452, QgsCoordinateReferenceSystem.InternalCrsId)
        utils.openElementsLayers(dataGroup, crs, self.ownMainLayers, self.ownFiles)
        QApplication.restoreOverrideCursor()
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Successful commit", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def runExportInp(self):
        """Run method that performs all the real work"""
        self.defineCurrentProject()
        if self.ProjectDirectory == self.TemporalFolder:
            self.iface.messageBar().pushMessage("Warning", "No valid project is opened", level=1, duration=10)
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
        
        if b=="True":
            self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        elif not b=="Canceled":
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def runModel(self):
        pass

    def runAbout(self):
        # show the dialog
        dlg = QGISRedAboutDialog()
        dlg.exec_()