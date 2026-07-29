# -*- coding: utf-8 -*-

import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsProject
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from qgis.PyQt.QtGui import QColor, QIcon
from ...tools.qgisred_dependencies import (
    QGISRedDependencies as GISRed
)
from qgis.PyQt.QtWidgets import (
    QDialog,
    QInputDialog,
    QMessageBox,
    QTreeWidgetItem,
)

from ...tools.utils.qgisred_ui_utils import (
    QGISRedBanner,
    QGISRED_COMBO_STYLE,
)


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(
        os.path.dirname(__file__),
        "qgisred_demandsectorbuilder_dialog.ui"
    )
)


_themeOrder = [
    "Frontiers",
    "Links",
    "Nodes",
    "MultiLines",
    "MultiNodes",
    "Polygons",
]


class QGISRedDemandSectorBuilderDialog(QDialog, FORM_CLASS):

    def __init__(self, parent=None):
        super(QGISRedDemandSectorBuilderDialog, self).__init__(parent)

        self.setupUi(self)

        self.setWindowIcon(QIcon(":/images/iconDemandSectorBuilder.svg"))

        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowCloseButtonHint
        )

        self.iface = None
        self.canvas = None

        self.ProjectDirectory = ""
        self.NetworkName = ""

        self.banner = QGISRedBanner.inject(self, self.rootLayout)

        self._applyStyle()

        self._connectSignals()

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    def config(
            self,
            iface,
            projectDirectory,
            networkName):

        self.iface = iface
        self.canvas = iface.mapCanvas()

        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName

        self._loadSectorizations()

    # ----------------------------------------------------------
    # Setup
    # ----------------------------------------------------------

    def _applyStyle(self):

        self.setStyleSheet(
            "QDialog { background-color: #f8f9fb; }"
            "QGroupBox { font-weight: bold; }"
            "QComboBox {"
            " background-color: white;"
            "}"
            "QPushButton {"
            " min-width: 110px;"
            "}"
        )

        for combo in (
            self.cbSectorization,
            self.cbFromTheme,
            self.cbToTheme,
            self.cbCheckTheme,
            self.cbSourceTheme,
        ):
            combo.setStyleSheet(QGISRED_COMBO_STYLE)

    # ----------------------------------------------------------
    # Loading
    # ----------------------------------------------------------

    def _extractCollection(
            self,
            result,
            possibleKeys):

        if result is None:
            return []

        if isinstance(result, (list, tuple, set)):
            return list(result)

        if isinstance(result, dict):

            for key in possibleKeys:

                value = result.get(key)

                if isinstance(
                    value,
                    (list, tuple, set)
                ):
                    return list(value)

            return []

        for attributeName in possibleKeys:

            value = getattr(
                result,
                attributeName,
                None
            )

            if isinstance(
                value,
                (list, tuple, set)
            ):
                return list(value)

        try:
            if not isinstance(result, str):
                return list(result)

        except TypeError:
            pass

        return []

    def _loadSectorizations(self):

        previousSectorization = (
            self.cbSectorization.currentText().strip()
        )

        self.cbSectorization.blockSignals(True)
        self.cbSectorization.clear()

        sectorizationsFolder = os.path.join(
            self.ProjectDirectory,
            "Auxiliary Layers",
            "DemandSectors"
        )

        sectorizations = []

        if os.path.isdir(sectorizationsFolder):

            sectorizations = sorted(
                [
                    folderName
                    for folderName in os.listdir(sectorizationsFolder)
                    if os.path.isdir(
                        os.path.join(
                            sectorizationsFolder,
                            folderName
                        )
                    )
                ],
                key=str.lower
            )

        names = []

        for sectorization in sectorizations:

            if isinstance(sectorization, str):
                name = sectorization.strip()

            elif isinstance(sectorization, dict):
                name = str(
                    sectorization.get(
                        "name",
                        sectorization.get(
                            "Name",
                            ""
                        )
                    )
                ).strip()

            else:
                name = str(
                    getattr(
                        sectorization,
                        "Name",
                        getattr(
                            sectorization,
                            "name",
                            ""
                        )
                    )
                ).strip()

            if name and name not in names:
                names.append(name)

        names.sort(key=str.lower)

        self.cbSectorization.addItems(names)
        self.cbSectorization.blockSignals(False)

        if previousSectorization:
            self._selectComboText(
                self.cbSectorization,
                previousSectorization
            )

        if (
            self.cbSectorization.currentIndex() < 0 and
            self.cbSectorization.count() > 0
        ):
            self.cbSectorization.setCurrentIndex(0)

        self._refreshCurrentThemes()
        self._updateControls()

    def _refreshCurrentThemes(self):

        previouslySelectedTheme = (
            self._selectedCurrentTheme()
        )

        self.twCurrentThemes.clear()

        sectorization = self._currentSectorization()

        if not sectorization:
            self._refreshCombos({})
            self._updateControls()
            return

        result = self._callBuilderMethod(
            "GetDemandSectorThemes",
            projectDirectory=self.ProjectDirectory,
            networkName=self.NetworkName,
            sectorizationName=sectorization
        )

        themeStatuses = self._extractThemeStatuses(
            result
        )

        for theme in _themeOrder:

            item = QTreeWidgetItem(
                self.twCurrentThemes
            )

            item.setText(0, theme)

            status = themeStatuses.get(
                theme.lower(),
                "missing"
            )

            self._setThemeItemStatus(
                item,
                status
            )

        self._refreshCombos(themeStatuses)

        if previouslySelectedTheme:
            self._selectTreeTheme(
                previouslySelectedTheme
            )

        if (
            not self.twCurrentThemes.selectedItems() and
            self.twCurrentThemes.topLevelItemCount() > 0
        ):
            firstItem = (
                self.twCurrentThemes.topLevelItem(0)
            )

            self.twCurrentThemes.setCurrentItem(
                firstItem
            )

        self._updateControls()

    def _extractThemeStatuses(self, result):

        statuses = {}

        themes = self._extractCollection(
            result,
            (
                "themes",
                "Themes",
                "items",
                "Items",
                "data",
                "Data",
            )
        )

        if isinstance(result, dict):

            directThemeDictionary = all(
                str(key).lower() in [
                    theme.lower()
                    for theme in _themeOrder
                ]
                for key in result.keys()
            )

            if directThemeDictionary:

                for theme, status in result.items():

                    statuses[
                        str(theme).strip().lower()
                    ] = self._normaliseThemeStatus(
                        status
                    )

                return statuses

        for themeData in themes:

            if isinstance(themeData, str):

                statuses[
                    themeData.strip().lower()
                ] = "filled"

                continue

            if isinstance(themeData, dict):

                name = themeData.get(
                    "themeType",
                    themeData.get(
                        "ThemeType",
                        themeData.get(
                            "name",
                            themeData.get(
                                "Name",
                                ""
                            )
                        )
                    )
                )

                status = themeData.get(
                    "status",
                    themeData.get(
                        "Status",
                        themeData.get(
                            "state",
                            themeData.get(
                                "State",
                                "missing"
                            )
                        )
                    )
                )

            else:

                name = getattr(
                    themeData,
                    "ThemeType",
                    getattr(
                        themeData,
                        "themeType",
                        getattr(
                            themeData,
                            "Name",
                            getattr(
                                themeData,
                                "name",
                                ""
                            )
                        )
                    )
                )

                status = getattr(
                    themeData,
                    "Status",
                    getattr(
                        themeData,
                        "status",
                        getattr(
                            themeData,
                            "State",
                            getattr(
                                themeData,
                                "state",
                                "missing"
                            )
                        )
                    )
                )

            name = str(name or "").strip()

            if not name:
                continue

            statuses[name.lower()] = (
                self._normaliseThemeStatus(status)
            )

        return statuses

    def _refreshCombos(
            self,
            themeStatuses=None):

        if themeStatuses is None:
            themeStatuses = {}

        previousFrom = (
            self.cbFromTheme.currentText().strip()
        )

        previousTo = (
            self.cbToTheme.currentText().strip()
        )

        previousCheck = (
            self.cbCheckTheme.currentText().strip()
        )

        previousSource = (
            self.cbSourceTheme.currentText().strip()
        )

        filledThemes = []
        existingThemes = []
        destinationThemes = []

        for theme in _themeOrder:

            status = self._normaliseThemeStatus(
                themeStatuses.get(
                    theme.lower(),
                    "missing"
                )
            )

            if status == "filled":
                filledThemes.append(theme)

            if status != "missing":
                existingThemes.append(theme)

            if status in ("missing", "empty"):
                destinationThemes.append(theme)

        self._fillThemeCombo(
            self.cbFromTheme,
            filledThemes,
            previousFrom
        )

        self._fillThemeCombo(
            self.cbToTheme,
            destinationThemes,
            previousTo
        )

        self._fillThemeCombo(
            self.cbCheckTheme,
            existingThemes,
            previousCheck
        )

        self._fillThemeCombo(
            self.cbSourceTheme,
            filledThemes,
            previousSource
        )

    def _fillThemeCombo(
            self,
            combo,
            themes,
            previousText=""):

        combo.blockSignals(True)
        combo.clear()

        for theme in themes:
            combo.addItem(theme, theme)

        combo.blockSignals(False)

        if previousText:
            self._selectComboText(
                combo,
                previousText
            )

        if (
            combo.currentIndex() < 0 and
            combo.count() > 0
        ):
            combo.setCurrentIndex(0)

        # ----------------------------------------------------------
    # Signals
    # ----------------------------------------------------------

    def _connectSignals(self):

        self.btCreateSectorization.clicked.connect(
            self._onCreateSectorization
        )

        self.btDeleteSectorization.clicked.connect(
            self._onDeleteSectorization
        )

        self.btCreateTheme.clicked.connect(
            self._onCreateTheme
        )

        self.btDeleteTheme.clicked.connect(
            self._onDeleteTheme
        )

        self.btCreateComplete.clicked.connect(
            self._onCreateComplete
        )

        self.btCheckTheme.clicked.connect(
            self._onCheck
        )

        self.btUpdateThemes.clicked.connect(
            self._onUpdate
        )

        self.btClose.clicked.connect(
            self.close
        )

        self.cbSectorization.currentIndexChanged.connect(
            self._onSectorizationChanged
        )

        self.twCurrentThemes.itemSelectionChanged.connect(
            self._onThemeSelectionChanged
        )

    # ----------------------------------------------------------
    # Sectorization selection
    # ----------------------------------------------------------

    def _onSectorizationChanged(self, index=-1):

        self._refreshCurrentThemes()
        self._updateControls()

    # ----------------------------------------------------------
    # Create sectorization
    # ----------------------------------------------------------

    def _onCreateSectorization(self):

        name, accepted = QInputDialog.getText(
            self,
            self.tr("Create demand sectorization"),
            self.tr("Sectorization name:")
        )

        if not accepted:
            return

        name = name.strip()

        if not name:
            self._showWarning(
                self.tr("Create demand sectorization"),
                self.tr("The sectorization name cannot be empty.")
            )
            return

        existingNames = [
            self.cbSectorization.itemText(index).strip()
            for index in range(self.cbSectorization.count())
        ]

        if any(
            existing.lower() == name.lower()
            for existing in existingNames
        ):
            self._showWarning(
                self.tr("Create demand sectorization"),
                self.tr(
                    "A demand sectorization with this name already exists."
                )
            )
            return

        result = self._callBuilderMethod(
            "CreateDemandSectorization",
            sectorizationName=name
        )

        resultText = str(result or "").strip()

        status, separator, payload = resultText.partition("^")

        if status.strip().lower() != "success":

            errorMessage = (
                payload.strip()
                if separator
                else resultText
            )

            self._showError(
                self.tr("Create demand sectorization"),
                errorMessage
            )
            return

        createdSectorizationName = payload.strip()

        if not createdSectorizationName:
            createdSectorizationName = name

        self._loadSectorizations()

        self._selectComboText(
            self.cbSectorization,
            createdSectorizationName
        )

        self._openSectorizationGroup(
            createdSectorizationName
        )

        self._refreshCurrentThemes()

    # ----------------------------------------------------------
    # Delete sectorization
    # ----------------------------------------------------------

    def _onDeleteSectorization(self):

        sectorization = self._currentSectorization()

        if not sectorization:
            self._showWarning(
                self.tr("Delete demand sectorization"),
                self.tr("Select a demand sectorization first.")
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("Delete demand sectorization"),
            self.tr(
                'The demand sectorization "%s" and all its themes '
                "will be deleted.\n\nContinue?"
            ) % sectorization,
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._callBuilderMethod(
            "DeleteDemandSectorization",
            sectorizationName=sectorization
        )

        if not self._operationSucceeded(result):
            self._showOperationResult(
                self.tr("Delete demand sectorization"),
                result,
                errorByDefault=True
            )
            return

        self._showOperationResult(
            self.tr("Delete demand sectorization"),
            result
        )

        self._loadSectorizations()

    # ----------------------------------------------------------
    # Create theme
    # ----------------------------------------------------------

    def _onCreateTheme(self):

        sectorization = self._currentSectorization()
        theme = self._selectedCurrentTheme()

        if not sectorization:
            self._showWarning(
                self.tr("Create demand sector theme"),
                self.tr("Select a demand sectorization first.")
            )
            return

        if not theme:
            self._showWarning(
                self.tr("Create demand sector theme"),
                self.tr("Select a theme in the current themes list.")
            )
            return

        status = self._selectedCurrentThemeStatus()

        if status and status.lower() != "missing":
            self._showWarning(
                self.tr("Create demand sector theme"),
                self.tr(
                    'The theme "%s" already exists in the selected '
                    "sectorization."
                ) % theme
            )
            return

        result = self._callBuilderMethod(
            "CreateRemoveDemandSectorTheme",
            sectorizationName=sectorization,
            themeType=theme,
            createTheme=True
        )

        if not self._operationSucceeded(result):
            self._showOperationResult(
                self.tr("Create demand sector theme"),
                result,
                errorByDefault=True
            )
            return

        self._showOperationResult(
            self.tr("Create demand sector theme"),
            result
        )

        self._refreshProjectLayers()
        self._refreshCurrentThemes()
        self._selectTreeTheme(theme)

    # ----------------------------------------------------------
    # Delete theme
    # ----------------------------------------------------------

    def _onDeleteTheme(self):

        sectorization = self._currentSectorization()
        theme = self._selectedCurrentTheme()

        if not sectorization:
            self._showWarning(
                self.tr("Delete demand sector theme"),
                self.tr("Select a demand sectorization first.")
            )
            return

        if not theme:
            self._showWarning(
                self.tr("Delete demand sector theme"),
                self.tr("Select a theme in the current themes list.")
            )
            return

        status = self._selectedCurrentThemeStatus()

        if not status or status.lower() == "missing":
            self._showWarning(
                self.tr("Delete demand sector theme"),
                self.tr(
                    'The theme "%s" does not exist in the selected '
                    "sectorization."
                ) % theme
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("Delete demand sector theme"),
            self.tr(
                'The theme "%s" will be removed from the demand '
                'sectorization "%s".\n\nContinue?'
            ) % (theme, sectorization),
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._callBuilderMethod(
            "CreateRemoveDemandSectorTheme",
            sectorizationName=sectorization,
            themeType=theme,
            createTheme=False
        )

        if not self._operationSucceeded(result):
            self._showOperationResult(
                self.tr("Delete demand sector theme"),
                result,
                errorByDefault=True
            )
            return

        self._showOperationResult(
            self.tr("Delete demand sector theme"),
            result
        )

        self._refreshProjectLayers()
        self._refreshCurrentThemes()
        self._selectTreeTheme(theme)

    # ----------------------------------------------------------
    # Create / Complete
    # ----------------------------------------------------------

    def _onCreateComplete(self):

        sectorization = self._currentSectorization()
        fromTheme = self.cbFromTheme.currentData()
        toTheme = self.cbToTheme.currentData()

        if not sectorization:
            self._showWarning(
                self.tr("Create or complete demand sector theme"),
                self.tr("Select a demand sectorization first.")
            )
            return

        if not fromTheme:
            fromTheme = self.cbFromTheme.currentText().strip()

        if not toTheme:
            toTheme = self.cbToTheme.currentText().strip()

        if not fromTheme or not toTheme:
            self._showWarning(
                self.tr("Create or complete demand sector theme"),
                self.tr("Select both the source and destination themes.")
            )
            return

        if fromTheme.lower() == toTheme.lower():
            self._showWarning(
                self.tr("Create or complete demand sector theme"),
                self.tr(
                    "The source and destination themes must be different."
                )
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("Create or complete demand sector theme"),
            self.tr(
                'The theme "%s" will be created or completed using '
                '"%s" as the source theme.\n\nContinue?'
            ) % (toTheme, fromTheme),
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._callBuilderMethod(
            "CreateCompleteDemandSectorTheme",
            sectorizationName=sectorization,
            sourceThemeType=fromTheme,
            destinationThemeType=toTheme
        )

        if not self._operationSucceeded(result):
            self._showOperationResult(
                self.tr("Create or complete demand sector theme"),
                result,
                errorByDefault=True
            )
            return

        self._showOperationResult(
            self.tr("Create or complete demand sector theme"),
            result
        )

        self._refreshProjectLayers()
        self._refreshCurrentThemes()
        self._selectTreeTheme(toTheme)

    # ----------------------------------------------------------
    # Check theme
    # ----------------------------------------------------------

    def _onCheck(self):

        sectorization = self._currentSectorization()
        theme = self.cbCheckTheme.currentData()

        if not theme:
            theme = self.cbCheckTheme.currentText().strip()

        if not sectorization:
            self._showWarning(
                self.tr("Check demand sector theme"),
                self.tr("Select a demand sectorization first.")
            )
            return

        if not theme:
            self._showWarning(
                self.tr("Check demand sector theme"),
                self.tr("Select a theme to check.")
            )
            return

        result = self._callBuilderMethod(
            "CheckDemandSectorTheme",
            sectorizationName=sectorization,
            themeType=theme
        )

        self._showOperationResult(
            self.tr("Check demand sector theme"),
            result,
            errorByDefault=not self._operationSucceeded(result),
            alwaysShow=True
        )

        self._refreshCurrentThemes()
        self._selectTreeTheme(theme)

    # ----------------------------------------------------------
    # Update themes
    # ----------------------------------------------------------

    def _onUpdate(self):

        sectorization = self._currentSectorization()
        sourceTheme = self.cbSourceTheme.currentData()

        if not sourceTheme:
            sourceTheme = self.cbSourceTheme.currentText().strip()

        if not sectorization:
            self._showWarning(
                self.tr("Update demand sector themes"),
                self.tr("Select a demand sectorization first.")
            )
            return

        if not sourceTheme:
            self._showWarning(
                self.tr("Update demand sector themes"),
                self.tr("Select a source theme.")
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("Update demand sector themes"),
            self.tr(
                'The remaining demand sector themes will be updated '
                'using "%s" as the source theme.\n\n'
                "Existing sector information may be replaced.\n\n"
                "Continue?"
            ) % sourceTheme,
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        result = self._callBuilderMethod(
            "UpdateDemandSectorThemesFromSource",
            sectorizationName=sectorization,
            sourceThemeType=sourceTheme
        )

        if not self._operationSucceeded(result):
            self._showOperationResult(
                self.tr("Update demand sector themes"),
                result,
                errorByDefault=True
            )
            return

        self._showOperationResult(
            self.tr("Update demand sector themes"),
            result
        )

        self._refreshProjectLayers()
        self._refreshCurrentThemes()

    # ----------------------------------------------------------
    # Theme selection
    # ----------------------------------------------------------

    def _onThemeSelectionChanged(self):

        theme = self._selectedCurrentTheme()

        if theme:
            self._selectComboText(self.cbCheckTheme, theme)

        self._updateControls()

        # ----------------------------------------------------------
    # Current values
    # ----------------------------------------------------------

    def _currentSectorization(self):

        if self.cbSectorization.currentIndex() < 0:
            return ""

        return self.cbSectorization.currentText().strip()

    def _selectedCurrentThemeItem(self):

        selectedItems = self.twCurrentThemes.selectedItems()

        if not selectedItems:
            return None

        return selectedItems[0]

    def _selectedCurrentTheme(self):

        item = self._selectedCurrentThemeItem()

        if item is None:
            return ""

        return item.text(0).strip()

    def _selectedCurrentThemeStatus(self):

        item = self._selectedCurrentThemeItem()

        if item is None:
            return ""

        return item.text(1).strip()

    # ----------------------------------------------------------
    # Selection helpers
    # ----------------------------------------------------------

    def _selectComboText(
            self,
            combo,
            text):

        if combo is None:
            return False

        text = str(text or "").strip()

        if not text:
            combo.setCurrentIndex(-1)
            return False

        for index in range(combo.count()):

            itemText = combo.itemText(index).strip()
            itemData = combo.itemData(index)

            if itemText.lower() == text.lower():
                combo.setCurrentIndex(index)
                return True

            if (
                itemData is not None and
                str(itemData).strip().lower() == text.lower()
            ):
                combo.setCurrentIndex(index)
                return True

        return False

    def _selectTreeTheme(self, theme):

        theme = str(theme or "").strip()

        if not theme:
            self.twCurrentThemes.clearSelection()
            return False

        for index in range(
                self.twCurrentThemes.topLevelItemCount()):

            item = self.twCurrentThemes.topLevelItem(index)

            if item.text(0).strip().lower() != theme.lower():
                continue

            self.twCurrentThemes.setCurrentItem(item)
            item.setSelected(True)
            self.twCurrentThemes.scrollToItem(item)

            return True

        return False

    # ----------------------------------------------------------
    # Controls state
    # ----------------------------------------------------------

    def _updateControls(self):

        hasSectorization = bool(
            self._currentSectorization()
        )

        selectedTheme = self._selectedCurrentTheme()
        selectedStatus = self._normaliseThemeStatus(
            self._selectedCurrentThemeStatus()
        )

        hasSelectedTheme = bool(selectedTheme)

        themeExists = (
            hasSelectedTheme and
            selectedStatus != "missing"
        )

        themeIsMissing = (
            hasSelectedTheme and
            selectedStatus == "missing"
        )

        self.btDeleteSectorization.setEnabled(
            hasSectorization
        )

        self.twCurrentThemes.setEnabled(
            hasSectorization
        )

        self.btCreateTheme.setEnabled(
            hasSectorization and
            themeIsMissing
        )

        self.btDeleteTheme.setEnabled(
            hasSectorization and
            themeExists
        )

        self.cbFromTheme.setEnabled(
            hasSectorization
        )

        self.cbToTheme.setEnabled(
            hasSectorization
        )

        self.btCreateComplete.setEnabled(
            hasSectorization and
            self.cbFromTheme.count() > 0 and
            self.cbToTheme.count() > 0
        )

        self.cbCheckTheme.setEnabled(
            hasSectorization
        )

        self.btCheckTheme.setEnabled(
            hasSectorization and
            self.cbCheckTheme.count() > 0
        )

        self.cbSourceTheme.setEnabled(
            hasSectorization
        )

        self.btUpdateThemes.setEnabled(
            hasSectorization and
            self.cbSourceTheme.count() > 0
        )

    # ----------------------------------------------------------
    # Theme status
    # ----------------------------------------------------------

    def _normaliseThemeStatus(self, status):

        status = str(status or "").strip().lower()

        if status in (
            "filled",
            "complete",
            "completed",
            "sectorized",
            "sectorised",
            "valid",
            "ok",
        ):
            return "filled"

        if status in (
            "empty",
            "incomplete",
            "not filled",
            "notfilled",
        ):
            return "empty"

        if status in (
            "missing",
            "not found",
            "notfound",
            "does not exist",
            "none",
            "",
        ):
            return "missing"

        return status

    def _themeStatusText(self, status):

        status = self._normaliseThemeStatus(status)

        if status == "filled":
            return self.tr("Filled")

        if status == "empty":
            return self.tr("Empty")

        if status == "missing":
            return self.tr("Missing")

        return str(status or "")

    def _setThemeItemStatus(
            self,
            item,
            status):

        normalisedStatus = self._normaliseThemeStatus(
            status
        )

        item.setText(
            1,
            self._themeStatusText(normalisedStatus)
        )

        if normalisedStatus == "filled":
            colour = QColor(40, 140, 70)

        elif normalisedStatus == "empty":
            colour = QColor(190, 125, 15)

        else:
            colour = QColor(170, 55, 55)

        item.setForeground(1, colour)

        item.setData(
            1,
            Qt.ItemDataRole.UserRole,
            normalisedStatus
        )

    # ----------------------------------------------------------
    # Result handling
    # ----------------------------------------------------------

    def _operationSucceeded(self, result):

        if result is None:
            return False

        if isinstance(result, bool):
            return result

        if isinstance(result, int):
            return result >= 0

        if isinstance(result, str):

            text = result.strip().lower()

            if not text:
                return True

            failureWords = (
                "error",
                "failed",
                "failure",
                "exception",
                "invalid",
                "not possible",
                "cannot",
            )

            return not any(
                word in text
                for word in failureWords
            )

        if isinstance(result, dict):

            for key in (
                "success",
                "Success",
                "succeeded",
                "Succeeded",
                "ok",
                "Ok",
            ):
                if key in result:
                    return bool(result[key])

            for key in (
                "error",
                "Error",
                "exception",
                "Exception",
            ):
                if result.get(key):
                    return False

            return True

        for attributeName in (
            "Success",
            "success",
            "Succeeded",
            "succeeded",
            "Ok",
            "ok",
        ):

            if hasattr(result, attributeName):
                return bool(
                    getattr(result, attributeName)
                )

        for attributeName in (
            "Error",
            "error",
            "Exception",
            "exception",
        ):

            if (
                hasattr(result, attributeName) and
                getattr(result, attributeName)
            ):
                return False

        return True

    def _resultMessage(self, result):

        if result is None:
            return ""

        if isinstance(result, str):
            return result.strip()

        if isinstance(result, dict):

            for key in (
                "message",
                "Message",
                "description",
                "Description",
                "error",
                "Error",
            ):
                value = result.get(key)

                if value:
                    return str(value).strip()

            return ""

        for attributeName in (
            "Message",
            "message",
            "Description",
            "description",
            "Error",
            "error",
        ):

            if not hasattr(result, attributeName):
                continue

            value = getattr(result, attributeName)

            if value:
                return str(value).strip()

        return ""

    def _showOperationResult(
            self,
            title,
            result,
            errorByDefault=False,
            alwaysShow=False):

        success = self._operationSucceeded(result)
        message = self._resultMessage(result)

        if not message:

            if success:
                message = self.tr(
                    "The operation was completed successfully."
                )

            else:
                message = self.tr(
                    "The operation could not be completed."
                )

        if success and not errorByDefault:

            if alwaysShow:
                QMessageBox.information(
                    self,
                    title,
                    message
                )
            else:
                self._showInfo(title, message)

            return

        self._showError(title, message)

    # ----------------------------------------------------------
    # Messages
    # ----------------------------------------------------------

    def _showInfo(
            self,
            title,
            message):

        if self.banner is not None:

            for methodName in (
                "showInfo",
                "showMessage",
                "info",
            ):

                method = getattr(
                    self.banner,
                    methodName,
                    None
                )

                if not callable(method):
                    continue

                try:
                    method(message)
                    return

                except TypeError:
                    try:
                        method(title, message)
                        return
                    except TypeError:
                        pass

        QMessageBox.information(
            self,
            title,
            message
        )

    def _showWarning(
            self,
            title,
            message):

        if self.banner is not None:

            for methodName in (
                "showWarning",
                "warning",
            ):

                method = getattr(
                    self.banner,
                    methodName,
                    None
                )

                if not callable(method):
                    continue

                try:
                    method(message)
                    return

                except TypeError:
                    try:
                        method(title, message)
                        return
                    except TypeError:
                        pass

        QMessageBox.warning(
            self,
            title,
            message
        )

    def _showError(
            self,
            title,
            message):

        if self.banner is not None:

            for methodName in (
                "showError",
                "error",
            ):

                method = getattr(
                    self.banner,
                    methodName,
                    None
                )

                if not callable(method):
                    continue

                try:
                    method(message)
                    return

                except TypeError:
                    try:
                        method(title, message)
                        return
                    except TypeError:
                        pass

        QMessageBox.critical(
            self,
            title,
            message
        )

    # ----------------------------------------------------------
    # Project refresh
    # ----------------------------------------------------------

    def _refreshProjectLayers(self):

        project = QgsProject.instance()

        for layer in project.mapLayers().values():

            try:
                layer.reload()
            except Exception as exception:
                print(
                    "Could not reload layer "
                    f"{layer.name()}: {exception}"
                )

            try:
                layer.triggerRepaint()
            except Exception as exception:
                print(
                    "Could not repaint layer "
                    f"{layer.name()}: {exception}"
                )

        if self.canvas is not None:

            try:
                self.canvas.refresh()
            except Exception as exception:
                print(
                    "Could not refresh map canvas: "
                    f"{exception}"
                )

    # ----------------------------------------------------------
    # Builder API
    # ----------------------------------------------------------

    # ----------------------------------------------------------
    # Demand Sector Builder API
    # ----------------------------------------------------------

    def _callBuilderMethod(self, methodName, **arguments):

        try:

            if methodName == "GetDemandSectorizations":

                return GISRed.GetDemandSectorizations(
                    self.ProjectDirectory,
                    self.NetworkName
                )

            if methodName == "CreateDemandSectorization":

                return GISRed.CreateDemandSectorization(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", "")
                )

            if methodName == "DeleteDemandSectorization":

                return GISRed.DeleteDemandSectorization(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", "")
                )

            if methodName == "GetDemandSectorThemes":

                return GISRed.GetDemandSectorThemes(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", "")
                )

            if methodName == "CreateRemoveDemandSectorTheme":

                return GISRed.CreateRemoveDemandSectorTheme(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", ""),
                    arguments.get(
                        "themeType",
                        arguments.get("themeName", "")
                    )
                )

            if methodName == "CheckDemandSectorTheme":

                return GISRed.CheckDemandSectorTheme(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", ""),
                    arguments.get(
                        "themeType",
                        arguments.get("themeName", "")
                    )
                )

            if methodName == "CreateCompleteDemandSectorTheme":

                return GISRed.CreateCompleteDemandSectorTheme(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", ""),
                    arguments.get(
                        "sourceThemeType",
                        arguments.get("fromTheme", "")
                    ),
                    arguments.get(
                        "destinationThemeType",
                        arguments.get("toTheme", "")
                    )
                )

            if methodName == "UpdateDemandSectorThemesFromSource":

                return GISRed.UpdateDemandSectorThemesFromSource(
                    self.ProjectDirectory,
                    self.NetworkName,
                    arguments.get("sectorizationName", ""),
                    arguments.get(
                        "sourceThemeType",
                        arguments.get("sourceTheme", "")
                    )
                )

            return {
                "success": False,
                "message": self.tr(
                    'The Demand Sector Builder method "%s" '
                    "is not available."
                ) % methodName,
            }

        except Exception as exception:

            return {
                "success": False,
                "message": str(exception),
            }

    def _openSectorizationGroup(self, sectorizationName):

        sectorizationName = str(
            sectorizationName or ""
        ).strip()

        if not sectorizationName:
            return

        sectorizationGroup = self.getDemandSectorizationGroup(
            sectorizationName
        )

        sectorizationGroup.setExpanded(True)

        parentGroup = sectorizationGroup.parent()

        while parentGroup is not None:

            if hasattr(parentGroup, "setExpanded"):
                parentGroup.setExpanded(True)

            parentGroup = parentGroup.parent()

        if self.iface is not None:

            layerTreeView = self.iface.layerTreeView()

            layerTreeView.setCurrentNode(
                sectorizationGroup
            )

    def getDemandSectorsGroup(self):

        utils = QGISRedLayerUtils(
            self.ProjectDirectory,
            self.NetworkName,
            self.iface
        )

        return utils.getOrCreateNestedGroup(
            [
                self.NetworkName,
                "Auxiliary Layers",
                "DemandSectors"
            ]
        )

    def getDemandSectorizationGroup(self, sectorizationName):
        demandSectorsGroup = self.getDemandSectorsGroup()

        sectorizationGroup = (
            demandSectorsGroup.findGroup(
                sectorizationName
            )
        )

        if sectorizationGroup is None:

            sectorizationGroup = (
                demandSectorsGroup.addGroup(
                    sectorizationName
                )
            )

        return sectorizationGroup