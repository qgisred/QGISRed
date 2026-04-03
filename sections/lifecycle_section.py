# -*- coding: utf-8 -*-
"""Lifecycle section for QGISRed (__init__, initGui, unload, dependencies, updates)."""

import os
import tempfile
import platform
import subprocess
import base64
import webbrowser
import urllib.request
import ssl
from ctypes import windll, c_uint16, c_uint, wstring_at, byref, cast
from ctypes import create_string_buffer, c_void_p, Structure, POINTER

from qgis.core import QgsProject, QgsMessageLog, QgsApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox, QMenu, QToolButton
from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, qVersion, QCoreApplication
from ..compat import QAction, QGIS_INFO

from .. import resources3x  # noqa: F401  (registers Qt resources)
from ..tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock


class LANGANDCODEPAGE(Structure):
    _fields_ = [("wLanguage", c_uint16), ("wCodePage", c_uint16)]


class LifecycleSection:
    """Plugin lifecycle: __init__, tr, action builders, initGui, cleanupDocks, unload,
    setCulture, getVersion, checkDependencies, checkForUpdates, openNewFeaturesWebpage,
    removeTempFolders."""

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
            self.pushMessage(self.tr("QGISRed only works on Windows"), level=2, duration=5)
            return

        # initialize plugin directory (sections/ is one level below the plugin root)
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))
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
        self.unitsButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        icon = QIcon(":/images/iconGeneralMenu.svg")
        self.unitsAction = QAction(icon, "QGISRed: LPS | H-W", None)
        self.unitsAction.setToolTip(self.tr("Click to change it"))
        self.unitsAction.triggered.connect(self.runAnalysisOptions)
        self.actions.append(self.unitsAction)
        self.unitsButton.setDefaultAction(self.unitsAction)
        self.iface.mainWindow().statusBar().addWidget(self.unitsButton)

        # To allow downloads from qgisred web page
        ssl._create_default_https_context = ssl._create_unverified_context

    # All contexts that pylupdate5 assigns to section classes (since they are not QObject
    # subclasses, self.tr() always resolves here via MRO instead of using the class name).
    _SECTION_CONTEXTS = [
        "QGISRed",
        "MenuSection",
        "LifecycleSection",
        "AnalysisSection",
        "DebugValidationSection",
        "DigitalTwinSection",
        "LayerManagementSection",
        "NetworkEditingSection",
        "ProjectManagementSection",
        "ToolsSection",
        "UtilsSection",
    ]

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        Searches all section contexts because pylupdate5 assigns each class its own
        context, but self.tr() always resolves to this method via Python's MRO.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        for ctx in self._SECTION_CONTEXTS:
            result = QCoreApplication.translate(ctx, message)
            if result != message:
                return result
        return message


    def _make_action(self, icon_path, text, callback, checkable=False, enabled_flag=True, parent=None):
        """Create a QAction, connect its callback and register it in self.actions."""
        action = QAction(QIcon(icon_path), text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable)
        self.actions.append(action)
        return action

    def setup_dropdown_button(self, action, button, toolbar):
        """Configure *button* (QToolButton) as a dropdown and add it as a widget to *toolbar*.
        Creates a fresh QMenu for the button. The header action itself is NOT added
        to the popup menu (the arrow opens the children, not itself).
        """
        menu = QMenu()
        button.setMenu(menu)
        button.setDefaultAction(action)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        toolbar.addWidget(button)

    def add_to_group(self, action, submenu, toolbar=None):
        """Add *action* to *submenu* (menubar entry) and optionally to a floating *toolbar*."""
        submenu.addAction(action)
        if toolbar is not None:
            toolbar.addAction(action)

    def add_to_dropdown(self, action, button):
        """Append *action* to the popup menu of an existing QToolButton.
        Can be called multiple times to register the same action in several dropdowns.
        """
        menu = button.menu()
        if menu is None:
            menu = QMenu()
            button.setMenu(menu)
            button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        menu.addAction(action)
        button.setMenu(menu)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

    def add_simple_action(self, icon_path, text, callback, menu, toolbar, checkable=False, enabled_flag=True, parent=None):
        """Create an action and add it directly to *menu* and *toolbar* (no dropdowns)."""
        action = self._make_action(icon_path, text, callback, checkable=checkable, enabled_flag=enabled_flag, parent=parent)
        menu.addAction(action)
        toolbar.addAction(action)
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
        self.add_simple_action(
            ":/images/iconAbout.svg", self.tr("About..."), self.runAbout,
            self.qgisredmenu, self.toolbar, parent=self.iface.mainWindow(),
        )
        # Report issues
        self.add_simple_action(
            ":/images/iconGitHub.svg", self.tr("Report issues or comments..."), self.runReportIssues,
            self.qgisredmenu, self.toolbar, parent=self.iface.mainWindow(),
        )

        # Connecting QGis Events
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)
        QgsProject.instance().layersRemoved.connect(self.runLegendChanged)
        QgsProject.instance().readProject.connect(self.runOpenedQgisProject)

        # MapTools
        self.myMapTools = {}

        # QGISRed dependencies
        self.dllTempFolderFile = os.path.join(QGISRedFileSystemUtils().getQGISRedFolder(), "dllTempFolders.dat")
        QGISRedFileSystemUtils().copyDependencies()
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
        self.savedExtent = None
        self.removingLayers = False

        self.setCulture()
        # QgsMessageLog.logMessage("Culture set to " + definedCulture, "QGISRed", level=0)

        QgsMessageLog.logMessage(self.tr("Loaded sucssesfully"), "QGISRed", level=QGIS_INFO)

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
                    except Exception:
                        pass
                    try:
                        self.ResultDockwidget.resultPropertyChanged.disconnect(self.refreshTimeSeries)
                    except Exception:
                        pass
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

        QGISRedFileSystemUtils().removeFolder(self.tempFolder)

        if QGISRedFileSystemUtils.DllTempoFolder is not None:
            with open(self.dllTempFolderFile, "a+") as file:
                file.write(QGISRedFileSystemUtils.DllTempoFolder + "\n")

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

    def setCulture(self):
        ui_language = QgsApplication.locale()
        try:
            GISRed.SetCulture(ui_language)
        except Exception:
            pass

    def getVersion(self, filename, what):
        _UNKNOWN_VERSION = "0.0.0.0"  # DLL version fallback string, not a network address  # nosec B104
        wstr_file = wstring_at(filename)
        size = windll.version.GetFileVersionInfoSizeW(wstr_file, None)
        if size == 0:
            return _UNKNOWN_VERSION

        buffer = create_string_buffer(size)
        if windll.version.GetFileVersionInfoW(wstr_file, None, size, buffer) == 0:
            return _UNKNOWN_VERSION

        value = c_void_p(0)
        value_size = c_uint(0)
        ret = windll.version.VerQueryValueW(buffer, wstring_at(r"\VarFileInfo\Translation"), byref(value), byref(value_size))
        if ret == 0:
            return _UNKNOWN_VERSION
        lcp = cast(value, POINTER(LANGANDCODEPAGE))
        language = "{0:04x}{1:04x}".format(lcp.contents.wLanguage, lcp.contents.wCodePage)

        res = windll.version.VerQueryValueW(
            buffer, wstring_at("\\StringFileInfo\\" + language + "\\" + what), byref(value), byref(value_size)
        )

        if res == 0:
            return _UNKNOWN_VERSION
        return wstring_at(value.value, value_size.value - 1)

    def checkDependencies(self):
        valid = False
        gisredDir = QGISRedFileSystemUtils().getGISRedDllFolder()
        if os.path.isdir(gisredDir):
            currentVersion = self.getVersion(os.path.join(gisredDir, "GISRed.QGISRed.dll"), "FileVersion")
            if currentVersion == self.DependenciesVersion:
                valid = True
        if not valid:
            link = "https://qgisred.upv.es/files/dependencies/" + self.DependenciesVersion + "/QGISRed_Installation.msi"
            request = QMessageBox.question(
                self.iface.mainWindow(),
                self.tr("QGISRed Dependencies"),
                self.tr(
                    "QGISRed plugin only runs in Windows OS and requires some dependencies (v{}). Do you want to install them now?").format(self.DependenciesVersion) +
                    "\n\n" + self.tr("At the end, the QGISRed web page will be open to show the news, where you can also register if you wish to receive the newsletters."),
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
                        os.startfile(uninstallFile)

                localFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".msi"
                try:
                    if not link.startswith("https://"):
                        return valid
                    urllib.request.urlretrieve(link, localFile)
                    subprocess.run(["msiexec", "/i", localFile], check=False)
                    os.remove(localFile)
                except Exception:
                    pass
                valid = self.checkDependencies()
                if valid:
                    QGISRedFileSystemUtils().copyDependencies()
                    self.setCulture()

        return valid

    def checkForUpdates(self):
        link = "https://qgisred.upv.es/files/versions.txt"
        tempLocalFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".txt"
        try:
            # Read online file
            if not link.startswith("https://"):
                return
            urllib.request.urlretrieve(link, tempLocalFile)
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
                            "QGISRed plugin has a new version ({}). You can upgrade it from the QGis plugin manager. Do you want to remember it again?"
                        ).format(contents),
                        QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                    )

                    # If user don't want to remember a local file is written with this version
                    if response == QMessageBox.No:
                        f = open(fileVersions, "w+")
                        f.write(contents + "\n")
                        f.close()
            os.remove(tempLocalFile)
        except Exception:
            pass

    def openNewFeaturesWebpage(self):
        language = "en"
        if QgsApplication.instance().locale() == "es":
            language = "es"
        link = "https://qgisred.upv.es/files/news_" + language
        tempLocalFile = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names()) + ".txt"
        try:
            # Read online file
            if not link.startswith("https://"):
                return
            urllib.request.urlretrieve(link, tempLocalFile)
            f = open(tempLocalFile, "r")
            url = f.readline()
            f.close()
            webbrowser.open(url)
            return url
        except Exception:
            pass

    def removeTempFolders(self):
        if not os.path.exists(self.dllTempFolderFile):
            return
        allDeleted = True
        with open(self.dllTempFolderFile, "r") as file:
            lines = file.readlines()
            for line in lines:
                filePath = line.strip("\n")
                if not QGISRedFileSystemUtils().removeFolder(filePath):
                    allDeleted = False
        if allDeleted:
            os.remove(self.dllTempFolderFile)
