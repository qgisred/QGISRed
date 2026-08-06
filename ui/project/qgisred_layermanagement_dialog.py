# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (
    QDialog, QApplication, QLayout, QTableWidgetItem, QMessageBox,
    QComboBox, QLineEdit, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QStyledItemDelegate, QWIDGETSIZE_MAX,
)
from qgis.PyQt.QtCore import Qt, QCoreApplication, QTimer
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector
from qgis.core import QgsVectorLayer

from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils, LAYER_TYPE_CONFIG
from ...tools.utils.qgisred_ui_utils import QGISRedBanner
from ...tools.utils.qgisred_auxiliary_layers import (
    AUXILIARY_LAYER_TYPES, DEFAULT_BASE_DEMAND_FIELD,
    composeBaseName, deleteTheme, isValidThemeName, listThemes, parseBaseName,
)
from ...tools.utils.qgisred_base_demand_fields import (
    MAX_FIELD_NAME_LENGTH, NAME_DUPLICATE, NAME_INVALID, NAME_TOO_LONG,
    applyFieldChanges, baseDemandFieldNames, planFieldChanges, suggestFieldName, validateRows,
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


# The only type whose base demand columns can be managed.
CONSUMPTION_POINTS_KEY = "Consumptions"

_AUXILIARY_TYPE_LABELS = {
    "Consumptions": "Consumption Points",
    "Links": "Demand Links",
    "Sectors": "Demand Sectors",
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


class _FieldNameDelegate(QStyledItemDelegate):
    """Caps the editor at what a DBF column name holds.

    The limit is enforced again when the dialog is accepted, but stopping the keystroke is
    what makes it understood: being told afterwards that a name is too long only teaches
    the user to count characters.
    """

    def createEditor(self, parent, option, index):
        editor = super(_FieldNameDelegate, self).createEditor(parent, option, index)
        self.capEditor(editor)
        return editor

    @staticmethod
    def capEditor(editor):
        """Limit whatever editor Qt handed us, when it is one that can be limited."""
        if hasattr(editor, "setMaxLength"):
            editor.setMaxLength(MAX_FIELD_NAME_LENGTH)


class _BaseDemandFieldsDialog(QDialog):
    """Lists a consumption points theme's base demand columns, and edits them.

    Names are edited in place: the client described adding and renaming as two buttons,
    but both come down to typing a name, so the list is editable and Accept applies
    whatever changed. Each row remembers the name it arrived with, which is what tells a
    rename from a delete plus an add — a rename keeps the column's values.
    """

    MINIMUM_WIDTH = 350

    def __init__(self, fieldNames, themeName="", parent=None):
        super(_BaseDemandFieldsDialog, self).__init__(parent)
        self.setWindowTitle(self.tr("Base demand fields"))
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.themeName = themeName

        self.lstFields = QListWidget(self)
        # Held on the instance: a delegate the widget does not own is collected away.
        self.nameDelegate = _FieldNameDelegate(self.lstFields)
        self.lstFields.setItemDelegate(self.nameDelegate)
        for name in fieldNames:
            self._appendRow(name, original=name)

        self.btAdd = QPushButton("+", self)
        self.btRemove = QPushButton("-", self)
        self.btAdd.setMaximumWidth(30)
        self.btRemove.setMaximumWidth(30)
        self.btAdd.setToolTip(self.tr("Add a base demand field"))
        self.btRemove.setToolTip(self.tr("Delete the selected field"))
        self.btAdd.clicked.connect(self.addRow)
        self.btRemove.clicked.connect(self.removeRow)

        self.btAccept = QPushButton(self.tr("Accept"), self)
        self.btCancel = QPushButton(self.tr("Cancel"), self)
        self.btAccept.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)

        sideButtons = QVBoxLayout()
        sideButtons.addWidget(self.btAdd)
        sideButtons.addWidget(self.btRemove)
        sideButtons.addStretch()

        listRow = QHBoxLayout()
        listRow.addWidget(self.lstFields)
        listRow.addLayout(sideButtons)

        buttonRow = QHBoxLayout()
        buttonRow.addStretch()
        buttonRow.addWidget(self.btAccept)
        buttonRow.addWidget(self.btCancel)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.headerText(), self))
        layout.addLayout(listRow)
        layout.addLayout(buttonRow)

        # Names are checked when this dialog is accepted, so the complaint has to appear
        # here: reporting it from the parent would mean the edits are already discarded.
        self.messageBar = QGISRedBanner.inject(self, layout)

    def headerText(self):
        """Names the theme being edited: several can be open and they all look alike."""
        if self.themeName:
            return self.tr("Fields holding a base demand of %1:").replace("%1", self.themeName)
        return self.tr("Fields holding a base demand:")

    def _appendRow(self, text, original=None):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        # None marks a row that is not backed by a column yet.
        item.setData(Qt.ItemDataRole.UserRole, original)
        self.lstFields.addItem(item)
        return item

    def addRow(self):
        # Offer the next free name in the family, still open for editing.
        item = self._appendRow(suggestFieldName([name for _original, name in self.rows()]))
        self.lstFields.setCurrentItem(item)
        self.lstFields.editItem(item)

    def removeRow(self):
        row = self.lstFields.currentRow()
        if row < 0:
            return
        if self.lstFields.count() <= 1:
            # The theme would have nowhere left to hold a demand.
            return
        self.lstFields.takeItem(row)

    def rows(self):
        """(originalName or None, newName) per row, in display order."""
        result = []
        for row in range(self.lstFields.count()):
            item = self.lstFields.item(row)
            result.append((item.data(Qt.ItemDataRole.UserRole), item.text().strip()))
        return result

    def fieldError(self, error, name):
        if error == NAME_TOO_LONG:
            return self.tr("Field names may hold at most %1 characters").replace(
                "%1", str(MAX_FIELD_NAME_LENGTH))
        if error == NAME_DUPLICATE:
            return self.tr("There is already a field called %1").replace("%1", name)
        if error == NAME_INVALID:
            return self.tr("%1 is not a valid field name").replace("%1", name)
        return self.tr("The theme needs at least one base demand field")

    def accept(self):
        """Refuse to close on a name that cannot be used, so the edits are not lost."""
        error, name = validateRows(self.rows())
        if error:
            self.messageBar.pushMessage(self.tr("Warning"), self.fieldError(error, name), level=1)
            return
        super(_BaseDemandFieldsDialog, self).accept()


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
        # The dialog may be enlarged but never squashed: SetMinimumSize keeps the layout's
        # own minimum as the floor, so nothing is ever cut off and the window still grows
        # to fit the banner when a message appears.
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setSizeGripEnabled(True)

        self.elements = [
            _Element(name, getattr(self, checkBox), getattr(self, button), complementary)
            for name, checkBox, button, complementary in _ELEMENTS
        ]
        for element in self.elements:
            element.createButton.clicked.connect(lambda _checked=False, e=element: self.createElement(e))

        self.btAddAuxiliary.clicked.connect(self.createAuxiliaryTheme)
        self.btRemoveAuxiliary.clicked.connect(self.deleteAuxiliaryTheme)
        self.btConfigAuxiliary.clicked.connect(self.configureBaseDemandFields)
        self.tbAuxiliary.itemSelectionChanged.connect(self.updateAuxiliaryButtons)
        # The checkbox gets a column of its own, so the theme name starts where the header
        # says it does instead of behind a tick.
        self.tbAuxiliary.setColumnWidth(0, 26)

    def showEvent(self, event):
        """Freeze the size the dialog has always opened at as its minimum, then let go.

        The themes table carries a height cap in the .ui, and that cap is what decides how
        tall the dialog opens. Pinning the tabs to that first hint keeps the window from
        being dragged any smaller than it used to be, and once the floor is in place the
        cap can go: the table is then the part that takes the room when the user enlarges.
        """
        super(QGISRedLayerManagementDialog, self).showEvent(event)
        if self.tbAuxiliary.maximumHeight() >= QWIDGETSIZE_MAX:
            return  # already done on a previous showing

        openingSize = self.sizeHint()
        self.tabElements.setMinimumSize(self.tabElements.sizeHint())
        self.tbAuxiliary.setMaximumHeight(QWIDGETSIZE_MAX)
        self.resize(openingSize)

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
        return os.path.join(self.ProjectDirectory, LAYER_TYPE_CONFIG["DemandBuilder"]["subdir"])

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

        self.updateAuxiliaryButtons()

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

        # Compared against the themes on disk rather than against the composed path: the
        # file names were shortened, so a theme created under the old convention lives at
        # a different path yet is the same theme to the user.
        existing = {
            (existingType.key, existingName.lower())
            for existingType, existingName, _path in listThemes(self.auxiliaryFolder(), self.NetworkName)
        }
        path = os.path.join(
            self.auxiliaryFolder(),
            composeBaseName(self.NetworkName, layerType, themeName) + ".shp",
        )
        if (layerType.key, themeName.lower()) in existing or os.path.exists(path):
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
        self.parent.syncAuxiliaryThemes([path], load=True)
        self.fillAuxiliaryTable()

    def selectedAuxiliaryRow(self):
        """(item, path, layerType) of the selected row, or (None, "", None)."""
        row = self.tbAuxiliary.currentRow()
        item = self.tbAuxiliary.item(row, 0) if row >= 0 else None
        if item is None:
            return None, "", None
        path = item.data(Qt.ItemDataRole.UserRole)
        layerType, _ = parseBaseName(os.path.splitext(os.path.basename(path))[0], self.NetworkName)
        return item, path, layerType

    def updateAuxiliaryButtons(self):
        """Base demand fields only exist on consumption points themes.

        Hidden rather than disabled: a greyed-out button invites the user to work out why
        it is greyed out, and for the other two types there is nothing to explain.
        """
        _item, _path, layerType = self.selectedAuxiliaryRow()
        self.btConfigAuxiliary.setVisible(layerType is not None and layerType.key == CONSUMPTION_POINTS_KEY)

    def configureBaseDemandFields(self):
        _item, path, layerType = self.selectedAuxiliaryRow()
        if layerType is None or layerType.key != CONSUMPTION_POINTS_KEY:
            return

        # Edit the open layer when there is one, so QGIS sees the new columns straight
        # away; otherwise work on the file through a throwaway layer.
        layer = self.utils._findLayerByPath(path)
        wasOpen = layer is not None
        if layer is None:
            layer = QgsVectorLayer(path, os.path.basename(path), "ogr")
            if not layer.isValid():
                self.pushMessage(self.tr("Error"), self.tr("The theme could not be read"), level=2)
                return

        originalNames = baseDemandFieldNames([field.name() for field in layer.fields()])
        _layerType, themeName = parseBaseName(
            os.path.splitext(os.path.basename(path))[0], self.NetworkName)

        dialog = _BaseDemandFieldsDialog(originalNames, themeName, self)
        if not dialog.exec():
            return

        # The dialog refuses to close on a name that cannot be used, so these rows are sound.
        renames, additions, deletions = planFieldChanges(originalNames, dialog.rows())
        if not (renames or additions or deletions):
            return

        if deletions:
            question = self.tr("The selected fields and all their values will be deleted. Continue?")
            if QMessageBox.question(self, self.tr("Delete fields"), question) != QMessageBox.StandardButton.Yes:
                return

        # Rebuilding an OGR provider under a running render job crashes QGIS.
        QGISRedLayerUtils().stopRenderingForRemoval(self.iface)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        failure = applyFieldChanges(layer, renames, additions, deletions)
        QApplication.restoreOverrideCursor()

        if failure:
            self.pushMessage(self.tr("Error"), failure, level=2)
            return

        if wasOpen:
            # Point labels are driven by a base demand field, so the style has to follow.
            self.parent.syncAuxiliaryThemes([path], load=True)

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
        self.parent.syncAuxiliaryThemes([path], load=False)
        # removeMapLayer only schedules the layer's destruction, so at this point the file
        # is still open and deleting it would fail with "in use". One turn of the event
        # loop is what actually releases the OGR handle — same reason _deleteOldResultFiles
        # defers too.
        QTimer.singleShot(0, lambda: self.deleteThemeFiles(path))

    def deleteThemeFiles(self, path):
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
