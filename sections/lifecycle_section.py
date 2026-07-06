# -*- coding: utf-8 -*-
"""Lifecycle section for QGISRed (__init__, initGui, unload, dependencies, updates)."""

from contextlib import suppress
import os
import time
import tempfile
import platform
import uuid
import json
import urllib.request
import urllib.parse
import ssl

from qgis.core import QgsProject, QgsMessageLog, QgsApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox, QMenu, QToolButton
from qgis.PyQt.QtCore import Qt, QSettings, QTranslator, qVersion, QCoreApplication, QTimer
from ..compat import QAction, QGIS_INFO

from .. import resources3x  # noqa: F401  (registers Qt resources)
from ..tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from ..ui.general.qgisred_news_dialog import QGISRedNewsDialog
from ..tools.utils.qgisred_stale_layer_manager import StaleLayerManager
from ..tools.utils.qgisred_maptip import QGISRedMapTip


class LifecycleSection:
    """Plugin lifecycle: __init__, tr, action builders, initGui, cleanupDocks, unload,
    setCulture, getVersion, checkDependencies, checkForNews, runNewsDialog,
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
        self.isUnloading = False  # Flag to prevent DLL calls during shutdown

        if not platform.system() == "Windows":
            self.pushMessage(self.tr("QGISRed only works on Windows"), level=2, duration=5)
            return

        # initialize plugin directory (sections/ is one level below the plugin root)
        self.plugin_dir = os.path.dirname(os.path.dirname(__file__))
        # initialize locale
        locale = QgsApplication.locale()[0:2]
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

        # News system state (populated by checkForNews, reused by runNewsDialog)
        self._latestNewsId = None
        self._latestNewsTitle = None
        self._latestNewsHtml = None

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
        self.addQueriesMenu()
        self.addAnalysisMenu()
        self.addDigitalTwinMenu()

        self.addInfoMenu()

        # Connecting QGis Events
        QgsProject.instance().projectSaved.connect(self.runSaveProject)
        QgsProject.instance().cleared.connect(self.runClearedProject)
        QgsProject.instance().layersRemoved.connect(self.runLegendChanged)
        QgsProject.instance().layersAdded.connect(self.runLegendChanged)
        QgsProject.instance().readProject.connect(self.runOpenedQgisProject)

        # MapTools
        self.myMapTools = {}

        # QGISRed dependencies
        self.dllTempFolderFile = os.path.join(QGISRedFileSystemUtils().getQGISRedFolder(), "dllTempFolders.dat")
        QGISRedFileSystemUtils().copyDependencies()
        self.removeTempFolders()
        # QGISRed news
        QTimer.singleShot(2000, self.checkForNews)

        self.gplFolder = os.path.join(os.getenv("APPDATA"), "QGISRed")
        try:  # create directory if does not exist
            os.stat(self.gplFolder)
        except Exception:
            os.mkdir(self.gplFolder)
        self.gplFile = os.path.join(self.gplFolder, "qgisredprojectlist.gpl")

        # SHPs temporal folder
        self.tempFolder = tempfile.mkdtemp(prefix="QGISRed_")
        self.KeyTemp = uuid.uuid4().hex

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
        self.hasToOpenIsolatedSegmentsLayers = False
        self.hasToOpenTreeLayers = False
        self.selectedFids = {}

        self.zoomToFullExtent = False
        self.layerOperationInProgress = False
        self._loading_project = False

        self._staleLayerManager = StaleLayerManager(
            self.iface,
            lambda: (getattr(self, "NetworkName", ""), getattr(self, "ProjectDirectory", ""))
        )

        self.setCulture()
        # QgsMessageLog.logMessage("Culture set to " + definedCulture, "QGISRed", level=0)

        QgsMessageLog.logMessage(self.tr("Loaded sucssesfully"), "QGISRed", level=QGIS_INFO)

        # If a project is already open when the plugin loads, trigger the open handler now
        # (readProject won't fire again for an already-loaded project)
        if QgsProject.instance().fileName():
            QTimer.singleShot(0, self.runOpenedQgisProject)

        self._mapTip = QGISRedMapTip(self.iface)

    def cleanupDocks(self):
        """Disconnects signals and removes all plugin docks to ensure a clean state."""
        with suppress(Exception):
            self._resetResultsEvolutionMapState()
        with suppress(Exception):
            from qgis.PyQt.QtWidgets import QApplication
            QApplication.instance().focusChanged.disconnect(self._onPickPanelFocusChanged)
        docks_to_clean = []
        if self.ResultDockwidget is not None:
            self.disconnectElementExplorerFromResultsDock()
            with suppress(Exception):
                self.ResultDockwidget.visibilityChanged.disconnect(self.activeInputGroup)
                with suppress(Exception):
                    self.ResultDockwidget.visibilityChanged.disconnect(self._arrangeDocksIfVisible)
                with suppress(Exception):
                    self.ResultDockwidget.visibilityChanged.disconnect(self._onResultsDockVisibilityForEvolution)
                if hasattr(self, 'refreshTimeSeries'):
                    with suppress(Exception):
                        self.ResultDockwidget.simulationFinished.disconnect(self.refreshTimeSeries)
                    with suppress(Exception):
                        self.ResultDockwidget.simulationFinished.disconnect(self.updateMetadata)
                    with suppress(Exception):
                        self.ResultDockwidget.resultPropertyChanged.disconnect(self.refreshTimeSeries)
                    with suppress(Exception):
                        self.ResultDockwidget.resultPropertyChanged.disconnect(self.updateMetadata)
                    with suppress(Exception):
                        self.ResultDockwidget.statisticsModeChanged.disconnect(self._onStatisticsModeChanged)
            docks_to_clean.append(('ResultDockwidget', self.ResultDockwidget))
            self.ResultDockwidget = None

        for ts_dock in list(getattr(self, 'timeSeriesDocks', None) or []):
            with suppress(Exception):
                ts_dock.visibilityChanged.disconnect(self.timeSeriesDockVisibilityChanged)
            with suppress(Exception):
                ts_dock.destroyed.disconnect(self._onTimeSeriesDockDestroyed)
            docks_to_clean.append(('timeSeriesDock', ts_dock))
        self.timeSeriesDocks = []
        self._activeTimeSeriesDock = None

        if hasattr(self, 'statisticsDock') and self.statisticsDock is not None:
            docks_to_clean.append(('statisticsDock', self.statisticsDock))
            self.statisticsDock = None

        if hasattr(self, 'queriesByPropertiesDock') and self.queriesByPropertiesDock is not None:
            docks_to_clean.append(('queriesByPropertiesDock', self.queriesByPropertiesDock))
            self.queriesByPropertiesDock = None

        # Also clean up Element Explorer if instance exists
        eeDock = QGISRedElementExplorerDock._instance
        if eeDock is not None:
            docks_to_clean.append(('elementExplorerDock', eeDock))

        for name, dock in docks_to_clean:
            with suppress(Exception):
                dock.close()
                self.iface.removeDockWidget(dock)
                dock.setParent(None)
                dock.deleteLater()

        # Clear Element Explorer singleton reference explicitly
        if eeDock is not None:
            QGISRedElementExplorerDock._instance = None

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        with suppress(Exception):
            self._staleLayerManager.stop()

        # Set flag to prevent DLL calls during shutdown
        self.isUnloading = False

        # Invalidate the DLL instance immediately
        self.gisredDll = None

        # Deactivate all map tools to prevent callbacks during shutdown
        with suppress(Exception):
            if hasattr(self, 'myMapTools'):
                for tool_name, tool in list(self.myMapTools.items()):
                    with suppress(Exception):
                        if tool is not None:
                            if self.iface.mapCanvas().mapTool() is tool:
                                self.iface.mapCanvas().unsetMapTool(tool)
                            tool.deactivate()
                self.myMapTools.clear()

        with suppress(Exception):
            self._mapTip.stop()

        # Disconnect signal handlers to prevent callbacks during cleanup
        with suppress(Exception):
            QgsProject.instance().projectSaved.disconnect(self.runSaveProject)
        with suppress(Exception):
            QgsProject.instance().cleared.disconnect(self.runClearedProject)
        with suppress(Exception):
            QgsProject.instance().layersRemoved.disconnect(self.runLegendChanged)
        with suppress(Exception):
            QgsProject.instance().layersAdded.disconnect(self.runLegendChanged)
        with suppress(Exception):
            QgsProject.instance().readProject.disconnect(self.runOpenedQgisProject)

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
        del self.infoToolbar
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
        with suppress(Exception):
            GISRed.SetCulture(ui_language)

    def getVersion(self, filename, what):
        try:
            import win32api
            pairs = win32api.GetFileVersionInfo(filename, "\\VarFileInfo\\Translation")
            lang, codepage = pairs[0]
            path = "\\StringFileInfo\\%04x%04x\\%s" % (lang, codepage, what)
            return win32api.GetFileVersionInfo(filename, path)
        except Exception:
            return ""

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
                    "QGISRed plugin only runs in Windows OS and requires some dependencies (v{}). Do you want to install them now?").format(self.DependenciesVersion),
                QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
            )
            if request == QMessageBox.StandardButton.Yes:
                if not link.startswith("https://"):
                    return valid
                _ctx = ssl.create_default_context()
                fd, localFile = tempfile.mkstemp(suffix=".msi", prefix="QGISRed_")
                os.close(fd)
                try:
                    with urllib.request.urlopen(link, context=_ctx) as response:  # nosec B310 — link validated startswith("https://") above
                        with open(localFile, "wb") as f:
                            f.write(response.read())
                    os.startfile(localFile)  # nosec B606 — launches the .msi installer just downloaded over verified HTTPS, by design
                    installed = False
                    for _ in range(60):  # 60 × 2 s = 2 min timeout
                        time.sleep(2)
                        QCoreApplication.processEvents()
                        with suppress(Exception):
                            os.remove(localFile)
                            installed = True
                            break
                    if installed:
                        valid = self.checkDependencies()
                        if valid:
                            QGISRedFileSystemUtils().copyDependencies()
                            self.setCulture()
                    else:
                        with suppress(Exception):
                            os.remove(localFile)
                        QMessageBox.warning(
                            self.iface.mainWindow(),
                            self.tr("QGISRed Dependencies"),
                            self.tr("The installation may have failed. Please try again or report the issue in GitHub"),
                        )
                except Exception:
                    with suppress(Exception):
                        os.remove(localFile)

        return valid

    def checkForNews(self, force=False):
        """Fetch language-specific news from the server; show the dialog if the id is new."""
        language = "es" if QgsApplication.locale()[0:2] == "es" else "en"
        news_url = "https://qgisred.upv.es/files/news/" + language + "/news.json"
        _ctx = ssl.create_default_context()
        with suppress(Exception):
            with urllib.request.urlopen(news_url, timeout=10, context=_ctx) as response:  # nosec B310 — news_url is a hardcoded https:// constant
                data = json.loads(response.read().decode("utf-8"))
            news_id = data.get("id", "")
            title = data.get("title", self.tr("QGISRed News"))
            html_url = data.get("html_url", "")
            if not news_id or not html_url:
                return

            # Check if this id was already seen (skip when forced from toolbar)
            if not force:
                seen_file = os.path.join(os.path.join(os.getenv("APPDATA"), "QGISRed"), "seenNews.dat")
                seen_ids = []
                if os.path.exists(seen_file):
                    with open(seen_file, "r", encoding="utf-8") as f:
                        seen_ids = [line.strip() for line in f if line.strip()]
                if news_id in seen_ids:
                    return

            # Resolve html_url relative to the news JSON URL
            resolved_html_url = urllib.parse.urljoin(news_url, html_url)
            if not resolved_html_url.startswith("https://"):
                return
            with urllib.request.urlopen(resolved_html_url, timeout=10, context=_ctx) as response:  # nosec B310 — validated startswith("https://") above
                html_content = response.read().decode("utf-8")

            self._latestNewsId = news_id
            self._latestNewsTitle = title
            self._latestNewsHtml = html_content
            self.runNewsDialog(force=force)

    def runNewsDialog(self, force=False):
        """Open the news dialog. force=True: skip seen-ids check and hide the 'don't show' checkbox."""
        if self._latestNewsHtml is None:
            if not force:
                return
            self.checkForNews(force=True)
            return

        dlg = QGISRedNewsDialog(
            self._latestNewsHtml,
            self._latestNewsTitle or self.tr("QGISRed News"),
            self._latestNewsId or "",
            show_dont_ask=not force,
            parent=self.iface.mainWindow(),
        )
        dlg.exec()
        if dlg.dontShowAgain() and self._latestNewsId:
            seen_file = os.path.join(os.path.join(os.getenv("APPDATA"), "QGISRed"), "seenNews.dat")
            with open(seen_file, "a", encoding="utf-8") as f:
                f.write(self._latestNewsId + "\n")

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
