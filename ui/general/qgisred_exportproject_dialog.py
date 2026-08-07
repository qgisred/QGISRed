# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtWidgets import (
    QDialog, QFileDialog, QMessageBox, QTreeWidgetItem, QHeaderView, QCheckBox,
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt import uic

from ...tools.utils.qgisred_ui_utils import QGISRedBanner, QGISRedUIUtils
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_project_export import (
    QGISRedProjectPackage, STRUCTURE_PARENT, SCOPE_OUTSIDE, SCOPE_REMOTE,
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_exportproject_dialog.ui"))


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
        self._groupCheckboxes = {}   # content-group key -> QCheckBox, built in _fillContentGroups
        self._groupNodes = {}        # groupPath tuple -> QTreeWidgetItem, built in _fillExternalData
        self._layerNodes = []        # (QTreeWidgetItem, ExternalItem)
        self._updatingTree = False   # guards the itemChanged signal while propagating ticks

        self.messageBar = QGISRedBanner.inject(self, self.verticalLayout)

        self.tbZipName.setText(plan.networkName)
        self.tbTargetFolder.setText(QGISRedFileSystemUtils().getDownloadsFolder())

        self._fillContentGroups()
        self._fillExternalData()
        self._refreshEstimate()

        self.btSelectFolder.clicked.connect(self.selectFolder)
        self.cbIncludeExternalData.toggled.connect(self._onMasterToggled)
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
        return {key for key, checkbox in self._groupCheckboxes.items() if checkbox.isChecked()}

    @property
    def externalSources(self):
        """The source paths the user ticked. Nodes sharing a file are kept in step, so reading any
        of them is enough."""
        return {
            item.source
            for node, item in self._layerNodes
            if node.checkState(0) == Qt.CheckState.Checked
        }

    @property
    def includeExternalData(self):
        """The gate. With it off nothing complementary travels, whatever the tree still shows."""
        return self.cbIncludeExternalData.isChecked() and bool(self.externalSources)

    @property
    def openFolder(self):
        return self.cbOpenFolder.isChecked()

    """Rendering"""

    def pushMessage(self, title, text, level=0, duration=5):
        self.messageBar.pushMessage(title, text, level, duration)

    def _formatSize(self, sizeBytes):
        return QGISRedUIUtils.formatSize(sizeBytes)

    def _fillContentGroups(self):
        """Builds one checkbox per content group. The set of folders is discovered per project, so
        the checkboxes are created here rather than declared in the .ui."""
        self.lbBaseLayers.setText(
            self.tr("Base layers — always included (%1 files, %2)")
            .replace("%1", str(self._plan.baseFileCount))
            .replace("%2", self._formatSize(self._plan.baseSizeBytes))
        )
        for group in self._plan.contentGroups:
            checkbox = QCheckBox(self.gbContent)
            if group.exists:
                checkbox.setChecked(group.key in self._plan.includeGroups)
                checkbox.setText(
                    self.tr("%1 (%2 files, %3)")
                    .replace("%1", group.dirName)
                    .replace("%2", str(group.fileCount))
                    .replace("%3", self._formatSize(group.sizeBytes))
                )
            else:
                checkbox.setChecked(False)
                checkbox.setEnabled(False)
                checkbox.setText(self.tr("%1 — no data").replace("%1", group.dirName))
            checkbox.toggled.connect(self._onSelectionChanged)
            self.verticalLayoutContent.addWidget(checkbox)
            self._groupCheckboxes[group.key] = checkbox

    def _fillExternalData(self):
        """Mirrors the QGIS layers panel: the complementary layers in their own group hierarchy,
        so they can be picked one by one or a whole group at a time."""
        items = [i for i in self._plan.externalItems if i.scope != SCOPE_REMOTE]
        if not items:
            self.gbExternal.setVisible(False)
            return

        tree = self.twExternalData
        tree.setHeaderLabels([self.tr("Layer"), self.tr("Location"), self.tr("Status")])
        self._groupNodes = {}      # groupPath tuple -> QTreeWidgetItem
        self._layerNodes = []      # (QTreeWidgetItem, ExternalItem)

        for item in items:
            for groupPath, layerName in (item.placements or [((), item.displayName)]):
                node = QTreeWidgetItem(self._groupNodeFor(groupPath))
                node.setText(0, layerName)
                node.setText(1, item.source)
                node.setToolTip(0, layerName)
                node.setToolTip(1, item.source)   # the cell elides; the tooltip never does
                if item.scope == SCOPE_OUTSIDE:
                    # Greyed out, not merely unresponsive: the row has to look as inert as it is
                    node.setFlags(Qt.ItemFlag.NoItemFlags)
                    node.setCheckState(0, Qt.CheckState.Unchecked)
                else:
                    node.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                                  | Qt.ItemFlag.ItemIsUserCheckable)
                    node.setCheckState(0, Qt.CheckState.Checked)
                self._layerNodes.append((node, item))

        self._refreshExternalStatus()
        self._refreshGroupCheckStates()
        hasSelectable = any(i.scope != SCOPE_OUTSIDE for _n, i in self._layerNodes)
        self.cbIncludeExternalData.blockSignals(True)
        self.cbIncludeExternalData.setChecked(hasSelectable)
        self.cbIncludeExternalData.blockSignals(False)
        self.cbIncludeExternalData.setToolTip(
            "" if hasSelectable else
            self.tr("None of the complementary layers can be exported from their current location.")
        )
        tree.setEnabled(self.cbIncludeExternalData.isChecked())
        tree.expandAll()
        header = tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tree.itemChanged.connect(self._onExternalItemChanged)

    def _groupNodeFor(self, groupPath):
        """Returns (creating if needed) the node for a group path; the tree root for an empty one."""
        parent = self.twExternalData.invisibleRootItem()
        path = ()
        for name in groupPath:
            path = path + (name,)
            node = self._groupNodes.get(path)
            if node is None:
                node = QTreeWidgetItem(parent)
                node.setText(0, name)
                node.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
                              | Qt.ItemFlag.ItemIsUserCheckable)
                node.setCheckState(0, Qt.CheckState.Checked)
                self._groupNodes[path] = node
            parent = node
        return parent

    def _layerNodesUnder(self, groupNode):
        return [(node, item) for node, item in self._layerNodes if self._isDescendant(node, groupNode)]

    @staticmethod
    def _isDescendant(node, ancestor):
        parent = node.parent()
        while parent is not None:
            if parent is ancestor:
                return True
            parent = parent.parent()
        return False

    def _refreshExternalStatus(self):
        """Fills the Status column. Kept short — the long explanation goes in the tooltip."""
        gateOpen = self.cbIncludeExternalData.isChecked()
        for node, item in self._layerNodes:
            if not gateOpen and item.scope != SCOPE_OUTSIDE:
                # The tick is preserved but nothing travels, so the column must not claim otherwise
                node.setText(2, self.tr("Not included"))
                node.setToolTip(2, self.tr("Whoever imports the project is expected to have it already."))
            elif item.scope == SCOPE_OUTSIDE:
                node.setText(2, self.tr("Not exportable"))
                node.setToolTip(2, self.tr(
                    "It is outside the project folder and its parent folder. Move it with the file "
                    "explorer into the project folder (or next to it) and reopen the project to "
                    "relink it."
                ))
            elif node.checkState(0) == Qt.CheckState.Checked:
                node.setText(2, self.tr("Included"))
                node.setToolTip(2, self.tr("It will travel inside the ZIP file."))
            else:
                node.setText(2, self.tr("Not included"))
                node.setToolTip(2, self.tr("Whoever imports the project is expected to have it already."))

    def _refreshGroupCheckStates(self):
        """A group reflects its layers: checked, unchecked, or partially checked."""
        for node in self._groupNodes.values():
            children = self._layerNodesUnder(node)
            selectable = [n for n, i in children if i.scope != SCOPE_OUTSIDE]
            if not selectable:
                # Nothing under it can be exported, so the group is greyed out like its children
                node.setFlags(Qt.ItemFlag.NoItemFlags)
                node.setCheckState(0, Qt.CheckState.Unchecked)
                continue
            checked = [n for n in selectable if n.checkState(0) == Qt.CheckState.Checked]
            if len(checked) == len(selectable):
                state = Qt.CheckState.Checked
            elif checked:
                state = Qt.CheckState.PartiallyChecked
            else:
                state = Qt.CheckState.Unchecked
            node.setCheckState(0, state)

    def _setNodeChecked(self, node, checked):
        if not bool(node.flags() & Qt.ItemFlag.ItemIsUserCheckable):
            return
        node.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)

    def _onExternalItemChanged(self, node, column):
        """Propagates a tick: groups drive their layers, and layers sharing a file stay in step."""
        if column != 0 or self._updatingTree:
            return
        self._updatingTree = True
        try:
            checked = node.checkState(0) == Qt.CheckState.Checked
            groupPath = next((p for p, n in self._groupNodes.items() if n is node), None)
            if groupPath is not None:
                for child, _item in self._layerNodesUnder(node):
                    self._setNodeChecked(child, checked)
            else:
                self._linkNodesSharingTheSameFile(node, checked)
            self._refreshGroupCheckStates()
            self._refreshExternalStatus()
        finally:
            self._updatingTree = False
        self._onSelectionChanged()

    def _linkNodesSharingTheSameFile(self, node, checked):
        """A file travels or it does not, so every node pointing at it moves together.

        Warns when unticking one that is also used elsewhere, since the other group loses it too.
        """
        item = next((i for n, i in self._layerNodes if n is node), None)
        if item is None:
            return
        twins = [n for n, i in self._layerNodes if i is item and n is not node]
        for twin in twins:
            self._setNodeChecked(twin, checked)
        if twins and not checked:
            self.pushMessage(
                self.tr("Warning"),
                self.tr("'%1' is used in more than one group. Leaving it out removes it from all of them.")
                .replace("%1", node.text(0)),
                level=1,
                duration=6,
            )

    def _onMasterToggled(self, checked):
        """The group checkbox gates the whole block: unticked, nothing is exported and the tree is
        disabled. The per-layer ticks are left as they were, so they come back if it is re-enabled."""
        self.twExternalData.setEnabled(checked)
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
