# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox, QTableWidgetItem, QHeaderView
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic

from ...tools.utils.qgisred_ui_utils import QGISRedBanner, QGISRedUIUtils
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_project_export import (
    QGISRedProjectPackage, STRUCTURE_PARENT, SCOPE_OUTSIDE, SCOPE_REMOTE,
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_exportproject_dialog.ui"))

# Content-group key → checkbox object name in the .ui
GROUP_CHECKBOXES = {
    "results": "cbResults",
    "issues": "cbIssues",
    "queries": "cbQueries",
    "auxiliary": "cbAuxiliary",
}


class QGISRedExportProjectDialog(QDialog, FORM_CLASS):
    """Asks where to write the ZIP and what to put in it.

    The caller builds the ExportPlan; this dialog only renders it and validates the user's input.
    """

    # Kept constant so the window does not jump sideways when a banner appears or a group is hidden
    DIALOG_WIDTH = 620

    def __init__(self, plan, package=None, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._plan = plan
        self._package = package or QGISRedProjectPackage(plan.projectDirectory, plan.networkName)
        self._warningsConfirmed = False
        self._externalRows = []

        self.messageBar = QGISRedBanner.inject(self, self.verticalLayout)

        self.tbZipName.setText(plan.networkName)
        self.tbTargetFolder.setText(QGISRedFileSystemUtils().getDownloadsFolder())

        self._fillContentGroups()
        self._fillExternalData()
        self._refreshEstimate()

        self.btSelectFolder.clicked.connect(self.selectFolder)
        self.cbIncludeExternalData.toggled.connect(self._onMasterToggled)
        for objectName in GROUP_CHECKBOXES.values():
            getattr(self, objectName).toggled.connect(self._onSelectionChanged)
        self.tbZipName.textChanged.connect(self._resetWarnings)
        self.buttonBox.accepted.connect(self._onAccepted)
        self.buttonBox.rejected.connect(self.reject)

        # Raise the banner before sizing, so its height is taken into account.
        if plan.qgisPath is None:
            self.pushMessage(
                self.tr("Warning"),
                self.tr(
                    "No QGIS project file was found, so the map appearance will not be exported. "
                    "Save the QGIS project inside the project folder to include it."
                ),
                level=1,
                duration=0,
            )

        # Hidden groups would leave a hole, so shrink to what is actually shown — but only
        # vertically: the width stays put whether or not a banner is up, and the banner wraps
        # onto a second line instead of widening the window.
        self.setMinimumWidth(self.DIALOG_WIDTH)
        self.adjustSize()
        self.resize(self.DIALOG_WIDTH, self.height())

    """Public results"""

    @property
    def zipPath(self):
        return QGISRedProjectPackage.buildZipPath(self.tbTargetFolder.text(), self.tbZipName.text())

    @property
    def includeGroups(self):
        return {key for key, name in GROUP_CHECKBOXES.items() if getattr(self, name).isChecked()}

    @property
    def externalSources(self):
        """The source paths the user ticked, one per complementary layer."""
        return {
            item.source
            for row, item in enumerate(self._externalRows)
            if self._isRowChecked(row)
        }

    @property
    def includeExternalData(self):
        return bool(self.externalSources)

    @property
    def openFolder(self):
        return self.cbOpenFolder.isChecked()

    """Rendering"""

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def _formatSize(self, sizeBytes):
        return QGISRedUIUtils.formatSize(sizeBytes)

    def _fillContentGroups(self):
        self.lbBaseLayers.setText(
            self.tr("Base layers — always included (%1 files, %2)")
            .replace("%1", str(self._plan.baseFileCount))
            .replace("%2", self._formatSize(self._plan.baseSizeBytes))
        )
        groupsByKey = {g.key: g for g in self._plan.contentGroups}
        for key, objectName in GROUP_CHECKBOXES.items():
            checkbox = getattr(self, objectName)
            group = groupsByKey.get(key)
            label = group.dirName if group else key
            if group is None or not group.exists:
                checkbox.setChecked(False)
                checkbox.setEnabled(False)
                checkbox.setText(self.tr("%1 — no data").replace("%1", label))
                continue
            checkbox.setChecked(key in self._plan.includeGroups)
            checkbox.setEnabled(True)
            checkbox.setText(
                self.tr("%1 (%2 files, %3)")
                .replace("%1", label)
                .replace("%2", str(group.fileCount))
                .replace("%3", self._formatSize(group.sizeBytes))
            )

    def _fillExternalData(self):
        items = [i for i in self._plan.externalItems if i.scope != SCOPE_REMOTE]
        self._externalRows = items
        if not items:
            self.gbExternal.setVisible(False)
            return

        table = self.twExternalData
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels([self.tr("Layer"), self.tr("Location"), self.tr("Status")])
        table.setRowCount(len(items))
        table.verticalHeader().setVisible(False)
        for row, item in enumerate(items):
            exportable = item.scope != SCOPE_OUTSIDE

            # The tick lives in the Layer cell: one checkbox per layer, so a 2 GB DTM can be left
            # out while the small cartography still travels.
            layerCell = QTableWidgetItem(item.displayName)
            flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            if exportable:
                flags |= Qt.ItemFlag.ItemIsUserCheckable
            layerCell.setFlags(flags)
            layerCell.setCheckState(Qt.CheckState.Checked if exportable else Qt.CheckState.Unchecked)
            layerCell.setToolTip(item.displayName)
            table.setItem(row, 0, layerCell)

            locationCell = QTableWidgetItem(item.source)
            locationCell.setToolTip(item.source)  # the cell elides; the tooltip never does
            table.setItem(row, 1, locationCell)

            statusCell = QTableWidgetItem("")
            table.setItem(row, 2, statusCell)

        # Status text must exist before sizing, or ResizeToContents measures an empty column.
        self._refreshExternalStatus()
        # Every row may be out of scope, in which case the master must not look checked.
        self._syncMasterCheckbox()
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.itemChanged.connect(self._onExternalItemChanged)

    def _refreshExternalStatus(self):
        """Fills the Status column. Kept short — the long explanation goes in the tooltip."""
        for row, item in enumerate(self._externalRows):
            cell = self.twExternalData.item(row, 2)
            if cell is None:
                continue
            if item.scope == SCOPE_OUTSIDE:
                cell.setText(self.tr("Not exportable"))
                cell.setToolTip(
                    self.tr(
                        "It is outside the project folder and its parent folder. Move it with the file "
                        "explorer into the project folder (or next to it) and reopen the project to "
                        "relink it."
                    )
                )
            elif self._isRowChecked(row):
                cell.setText(self.tr("Included"))
                cell.setToolTip(self.tr("It will travel inside the ZIP file."))
            else:
                cell.setText(self.tr("Not included"))
                cell.setToolTip(self.tr("Whoever imports the project is expected to have it already."))

    def _isRowChecked(self, row):
        cell = self.twExternalData.item(row, 0)
        return cell is not None and cell.checkState() == Qt.CheckState.Checked

    def _setRowChecked(self, row, checked):
        cell = self.twExternalData.item(row, 0)
        if cell is None or not bool(cell.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        cell.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _onExternalItemChanged(self, item):
        """A single layer was ticked or unticked: sync the master checkbox and the totals."""
        if item.column() != 0:
            return
        self._syncMasterCheckbox()
        self._onSelectionChanged()

    def _syncMasterCheckbox(self):
        anyChecked = any(self._isRowChecked(row) for row in range(len(self._externalRows)))
        if self.cbIncludeExternalData.isChecked() != anyChecked:
            self.cbIncludeExternalData.blockSignals(True)
            self.cbIncludeExternalData.setChecked(anyChecked)
            self.cbIncludeExternalData.blockSignals(False)

    def _onMasterToggled(self, checked):
        """The group checkbox is a select-all / select-none shortcut over the rows."""
        table = self.twExternalData
        table.blockSignals(True)
        for row in range(len(self._externalRows)):
            self._setRowChecked(row, checked)
        table.blockSignals(False)
        self._onSelectionChanged()

    def _refreshEstimate(self):
        self._package.applySelection(self._plan, self.includeExternalData, self.includeGroups,
                                     self.externalSources)
        self.lbSizeEstimate.setText(
            self.tr("Estimated size: %1").replace("%1", self._formatSize(self._plan.selectedSizeBytes()))
        )
        self.lbStructure.setText(self.tr("ZIP content: %1").replace("%1", self._describeStructure()))

    def _describeStructure(self):
        plan = self._plan
        projectFolder = os.path.basename(os.path.normpath(plan.projectDirectory))
        if plan.structure != STRUCTURE_PARENT:
            return self.tr("a single folder %1 holding everything").replace("%1", projectFolder + os.sep)

        entries = []
        if plan.qgisPath:
            entries.append(os.path.basename(plan.qgisPath))
        entries.append(projectFolder + os.sep)
        seen = set()
        for item in plan.inScopeItems:
            if not item.relPath:
                continue
            top = item.relPath.split("/")[0]
            if top == projectFolder or top in seen:
                continue
            seen.add(top)
            entries.append(top + os.sep)
        return " + ".join(entries)

    """Interaction"""

    def _resetWarnings(self):
        self._warningsConfirmed = False

    def _onSelectionChanged(self):
        self._resetWarnings()
        self._refreshExternalStatus()
        self._refreshEstimate()

    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Select the folder for the ZIP file"), self.tbTargetFolder.text()
        )
        if folder:
            self.tbTargetFolder.setText(folder)
            self._resetWarnings()

    def _pendingWarnings(self):
        """Non-blocking issues the user must acknowledge before the export runs."""
        warnings = []
        if self._plan.outOfScopeItems:
            warnings.append(
                self.tr(
                    "%1 complementary layer(s) are outside the project folder and its parent, so they "
                    "will NOT be exported. Move them into the project folder (or next to it) with the "
                    "file explorer and reopen the project to relink them."
                ).replace("%1", str(len(self._plan.outOfScopeItems)))
            )
        omitted = self._plan.omittedGroups
        if omitted and self._plan.qgisPath:
            warnings.append(
                self.tr(
                    "The QGIS project references layers in %1. Whoever imports it will have to locate "
                    "or remove them."
                ).replace("%1", ", ".join(g.dirName for g in omitted))
            )
        return warnings

    def _onAccepted(self):
        name = self.tbZipName.text().strip()
        if not name:
            self.pushMessage(self.tr("Validations"), self.tr("Enter a name for the ZIP file"), level=1, duration=0)
            return
        if not QGISRedProjectPackage.sanitizeZipFileName(name):
            self.pushMessage(self.tr("Validations"), self.tr("The file name is not valid"), level=1, duration=0)
            return

        folder = self.tbTargetFolder.text().strip()
        if not folder or not os.path.isdir(folder):
            self.pushMessage(self.tr("Validations"), self.tr("Select an existing folder"), level=1, duration=0)
            return
        if not os.access(folder, os.W_OK):
            self.pushMessage(self.tr("Validations"), self.tr("The selected folder is not writable"),
                             level=1, duration=0)
            return

        zipPath = self.zipPath
        if os.path.exists(zipPath):
            request = QMessageBox.question(
                self,
                self.tr("QGISRed"),
                self.tr("The file already exists. Do you want to overwrite it?"),
                QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
            )
            if request != QMessageBox.StandardButton.Yes:
                return

        warnings = self._pendingWarnings()
        if warnings and not self._warningsConfirmed:
            self._warningsConfirmed = True
            self.pushMessage(
                self.tr("Warning"),
                " ".join(warnings) + " " + self.tr("Press OK again to export anyway."),
                level=1,
                duration=0,
            )
            return

        self.accept()
