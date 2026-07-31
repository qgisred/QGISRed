# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (
    QDialog, QApplication, QLayout, QTableWidgetItem, QMessageBox,
    QComboBox, QLineEdit, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
)
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector

from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils, LAYER_TYPE_CONFIG
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
from ...tools.utils.qgisred_auxiliary_layers import (
    AUXILIARY_LAYER_TYPES, DEFAULT_BASE_DEMAND_FIELD,
    composeBaseName, deleteTheme, isValidThemeName, listThemes,
)
from ...tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_layermanagement_dialog.ui"))

# Element name, checkbox, create button, and which GISRed.CreateLayer argument the
# element travels in. The name doubles as the shapefile suffix and, lowercased, as the
# qgisred_identifier suffix, so it must stay free of spaces.
_ELEMENTS = (
    ("Pipes", "cbPipes", "btPipes", False),
    ("Junctions", "cbJunctions", "btJunctions", False),
    ("Tanks", "cbTanks", "btTanks", False),
    ("Reservoirs", "cbReservoirs", "btReservoirs", False),
    ("Valves", "cbValves", "btValves", False),
    ("Pumps", "cbPumps", "btPumps", False),
    ("Demands", "cbDemands", "btDemands", True),
    ("Sources", "cbSources", "btSources", True),
    ("IsolationValves", "cbIsolatedValves", "btIsolatedValves", True),
    ("ServiceConnections", "cbConnections", "btConnections", True),
    ("Meters", "cbMeters", "btMeters", True),
)


class _Element:
    """One managed element type and the widgets that stand for it in the dialog."""

    def __init__(self, name, checkBox, createButton, complementary):
        self.name = name
        self.identifier = "qgisred_" + name.lower()
        self.checkBox = checkBox
        self.createButton = createButton
        self.complementary = complementary
        # The .ui text, already translated by setupUi. Used whenever the layer is not
        # open and there is no real layer name to show instead.
        self.defaultText = checkBox.text()


_AUXILIARY_TYPE_LABELS = {
    "ConsumptionPoints": "Consumption Points",
    "DemandLinks": "Demand Links",
    "Sectors": "Sectors",
}


def auxiliaryTypeLabel(layerType):
    """Translated name of an auxiliary theme type.

    The context is spelled out because the label is looked up by key: self.tr() on a
    variable is invisible to lupdate, so the three sources are declared literally in
    tools/qgisred_translatable_strings.py instead.
    """
    return QCoreApplication.translate("AuxiliaryTypeNames", _AUXILIARY_TYPE_LABELS[layerType.key])


class _NewAuxiliaryThemeDialog(QDialog):
    """Asks for the type and the name of a new Demand Builder theme.

    The client asked for a file dialog, but the file name is not the user's to choose: it
    carries the network prefix and the type token that together identify the theme (see
    qgisred_auxiliary_layers). Asking only for the two parts that *are* theirs keeps the
    convention out of their hands and out of the error messages.
    """

    def __init__(self, parent=None):
        super(_NewAuxiliaryThemeDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("New auxiliary theme"))

        self.cbType = QComboBox(self)
        for layerType in AUXILIARY_LAYER_TYPES:
            self.cbType.addItem(auxiliaryTypeLabel(layerType), layerType.key)
        self.tbName = QLineEdit(self)

        self.btAccept = QPushButton(self.tr("Accept"), self)
        self.btCancel = QPushButton(self.tr("Cancel"), self)
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)

        typeRow = QHBoxLayout()
        typeRow.addWidget(QLabel(self.tr("Type:"), self))
        typeRow.addWidget(self.cbType)

        nameRow = QHBoxLayout()
        nameRow.addWidget(QLabel(self.tr("Name:"), self))
        nameRow.addWidget(self.tbName)

        buttonRow = QHBoxLayout()
        buttonRow.addStretch()
        buttonRow.addWidget(self.btAccept)
        buttonRow.addWidget(self.btCancel)

        layout = QVBoxLayout(self)
        layout.addLayout(typeRow)
        layout.addLayout(nameRow)
        layout.addLayout(buttonRow)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

    def selection(self):
        """(layerType, themeName) chosen by the user."""
        key = self.cbType.currentData()
        layerType = next(t for t in AUXILIARY_LAYER_TYPES if t.key == key)
        return layerType, self.tbName.text().strip()


class QGISRedLayerManagementDialog(QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedLayerManagementDialog, self).__init__(parent)
        self.setupUi(self)

        self.iface = None
        self.NetworkName = ""
        self.ProjectDirectory = ""

        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)
        self.btSelectCRS.clicked.connect(self.selectCRS)

        self.messageBar = QGISRedBanner.inject(self, self.gridLayout)
        # Every row is a fixed-height checkbox, so there is nothing worth resizing. This
        # also keeps the dialog honest when the banner appears: SetFixedSize re-reads the
        # layout's hint, so the window grows to fit the message instead of squashing the
        # tabs, and shrinks back when it hides.
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.elements = [
            _Element(name, getattr(self, checkBox), getattr(self, button), complementary)
            for name, checkBox, button, complementary in _ELEMENTS
        ]
        for element in self.elements:
            element.createButton.clicked.connect(lambda _checked=False, e=element: self.createElement(e))

        self.btAddAuxiliary.clicked.connect(self.createAuxiliaryTheme)
        self.btRemoveAuxiliary.clicked.connect(self.deleteAuxiliaryTheme)
        # The checkbox gets a column of its own, so the theme name starts where the header
        # says it does instead of behind a tick.
        self.tbAuxiliary.setColumnWidth(0, 26)

    def config(self, ifac, direct, netw, parent):
        self.iface = ifac
        self.parent = parent
        self.NetworkName = netw
        self.ProjectDirectory = direct

        self.utils = QGISRedLayerUtils(direct, netw, ifac)
        self.crs = self.utils.getProjectCrs()
        self.originalCrs = self.crs
        self.tbCRS.setText(self.crs.description())

        self.setProperties()

    """Element rows"""

    def getOpenLayersByIdentifier(self):
        """Map qgisred_identifier -> open layer for everything currently in the project."""
        found = {}
        for layer in self.utils.getLayers():
            identifier = layer.customProperty("qgisred_identifier")
            if identifier and identifier not in found:
                found[identifier] = layer
        return found

    def setProperties(self):
        """Refresh every row against what is on disk and what is open in QGIS."""
        existingFiles = set(os.listdir(self.ProjectDirectory))
        openLayers = self.getOpenLayersByIdentifier()

        for element in self.elements:
            onDisk = self.NetworkName + "_" + element.name + ".shp" in existingFiles
            layer = openLayers.get(element.identifier)
            # Projects saved before identifiers existed can only be matched by path.
            isOpen = layer is not None or self.utils.isLayerOpened(element.name)

            # The create button and the checkbox are exclusive: the button materialises
            # the missing shapefile, the checkbox decides whether an existing one loads.
            element.createButton.setVisible(not onDisk)
            element.checkBox.setChecked(isOpen)
            element.checkBox.setText(layer.name() if layer is not None else element.defaultText)
            # Pipes carry the network: once loaded they may not be unloaded.
            locked = element.name == "Pipes" and isOpen
            element.checkBox.setEnabled(onDisk and not locked)

        self.fillAuxiliaryTable()

    """Demand Builder auxiliary themes"""

    def auxiliaryFolder(self):
        return os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["DemandsBuilder"]["subdir"])

    def uniformedPath(self, path):
        """Spell a path the way getLayerPath does, so the two can be compared."""
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface).getUniformedPath(path)

    def openLayerPaths(self):
        """Normalised paths of every layer currently in the project."""
        fs = QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        paths = set()
        for layer in self.utils.getLayers():
            path = fs.getLayerPath(layer)
            if path:
                paths.add(os.path.normcase(path))
        return paths

    def fillAuxiliaryTable(self):
        """One row per theme on disk, checked when that theme is loaded in QGIS."""
        openPaths = self.openLayerPaths()
        themes = listThemes(self.auxiliaryFolder(), self.NetworkName)

        self.tbAuxiliary.setRowCount(len(themes))
        for row, (layerType, themeName, path) in enumerate(themes):
            # getLayerPath resolves the real path, so the listed one must be resolved too
            # or nothing here would ever be recognised as loaded.
            path = self.uniformedPath(path)

            check = QTableWidgetItem("")
            check.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
            )
            loaded = os.path.normcase(path) in openPaths
            check.setCheckState(Qt.CheckState.Checked if loaded else Qt.CheckState.Unchecked)
            check.setData(Qt.ItemDataRole.UserRole, path)
            self.tbAuxiliary.setItem(row, 0, check)

            # A theme with no name of its own is the one the Demands Manager writes.
            self.tbAuxiliary.setItem(row, 1, QTableWidgetItem(themeName or self.tr("(default)")))
            self.tbAuxiliary.setItem(row, 2, QTableWidgetItem(auxiliaryTypeLabel(layerType)))

    def auxiliaryRowPaths(self, onlyChecked=False):
        paths = []
        for row in range(self.tbAuxiliary.rowCount()):
            item = self.tbAuxiliary.item(row, 0)
            if item is None:
                continue
            if onlyChecked and item.checkState() != Qt.CheckState.Checked:
                continue
            paths.append(item.data(Qt.ItemDataRole.UserRole))
        return paths

    def createAuxiliaryTheme(self):
        dialog = _NewAuxiliaryThemeDialog(self)
        if not dialog.exec():
            return
        layerType, themeName = dialog.selection()

        if not isValidThemeName(themeName):
            self.pushMessage(self.tr("Warning"), self.tr("The theme name is not valid"), level=1)
            return

        path = os.path.join(
            self.auxiliaryFolder(),
            composeBaseName(self.NetworkName, layerType, themeName) + ".shp",
        )
        if os.path.exists(path):
            self.pushMessage(self.tr("Warning"), self.tr("A theme with that name already exists"), level=1)
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CreateAuxiliaryLayer(
            self.ProjectDirectory, self.NetworkName, layerType.key, path, DEFAULT_BASE_DEMAND_FIELD
        )
        QApplication.restoreOverrideCursor()

        if resMessage == "False":
            self.pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1)
            return
        if resMessage != "True":
            self.pushMessage(self.tr("Error"), resMessage, level=2)
            return

        # Created themes come back loaded, like the create button of the other tabs.
        self.parent.openAuxiliaryThemes([path])
        self.fillAuxiliaryTable()

    def deleteAuxiliaryTheme(self):
        row = self.tbAuxiliary.currentRow()
        item = self.tbAuxiliary.item(row, 0) if row >= 0 else None
        if item is None:
            self.pushMessage(self.tr("Warning"), self.tr("Select the theme to delete"), level=1)
            return

        path = item.data(Qt.ItemDataRole.UserRole)
        question = self.tr("The theme and its files will be deleted. Continue?")
        if QMessageBox.question(self, self.tr("Delete theme"), question) != QMessageBox.StandardButton.Yes:
            return

        # Unload first: on Windows a shapefile QGIS still holds cannot be removed.
        self.parent.closeAuxiliaryThemes([path])
        error = deleteTheme(path)
        if error:
            self.pushMessage(self.tr("Error"), error, level=2)
        self.fillAuxiliaryTable()

    """Actions"""

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if not projSelector.exec():
            return
        crs = projSelector.crs()
        if not crs.isValid():
            return
        # The DLL reprojects from an EPSG code alone. A custom CRS reaches it as a
        # "USER:xxxxx" identifier it cannot resolve, so refuse it here instead.
        if not crs.authid().startswith("EPSG:"):
            self.pushMessage(
                self.tr("Warning"),
                self.tr("Only coordinate systems with an EPSG code are supported"),
                level=1,
            )
            return
        self.crs = crs
        self.tbCRS.setText(self.crs.description())

    def createElement(self, element):
        layer = "" if element.complementary else element.name
        complLayer = element.name if element.complementary else ""
        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CreateLayer(self.ProjectDirectory, self.NetworkName, layer, complLayer)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            self.parent.openElementLayer(element.name)
            # The row now has a shapefile and an open layer. Redraw it and stay open, so
            # several elements can be created in one visit and any message stays readable.
            self.setProperties()
        elif resMessage == "False":
            self.pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1)
        else:
            self.pushMessage(self.tr("Error"), resMessage, level=2)

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def accept(self):
        selected = [element.name for element in self.elements if element.checkBox.isChecked()]
        managed = [element.name for element in self.elements]

        epsg = None
        if self.crs != self.originalCrs:
            epsg = self.crs.authid().replace("EPSG:", "")

        # Auxiliary themes first: the input path defers its own work to the next event
        # loop turn and closes it with updateMetadata, which must see the final tree.
        self.parent.applyAuxiliaryLayerSelection(
            self.auxiliaryRowPaths(onlyChecked=True), self.auxiliaryRowPaths()
        )
        self.parent.applyInputLayerSelection(selected, managed, epsg)

        super(QGISRedLayerManagementDialog, self).accept()
