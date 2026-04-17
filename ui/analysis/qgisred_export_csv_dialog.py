# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtWidgets import QDialog, QFileDialog
from qgis.PyQt import uic
from ...tools.utils.qgisred_ui_utils import QGISRedBanner

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_export_csv_dialog.ui"))


class QGISRedExportCsvDialog(QDialog, FORM_CLASS):
    def __init__(self, nodes_path, links_path, list_sep, decimal_sep, project_directory, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._project_directory = project_directory
        self._nodes_abs = nodes_path
        self._links_abs = links_path

        # Populate path displays
        self.leNodesPath.setText(self._display_path(nodes_path))
        self.leLinksPath.setText(self._display_path(links_path))

        # Populate combos
        self._list_sep_values = [";", ",", "\t", " "]
        self._decimal_sep_values = [".", ","]
        for label in [self.tr("; (semicolon)"), self.tr(", (comma)"), self.tr("Tab"), self.tr("Space")]:
            self.cbListSep.addItem(label)
        for label in [self.tr(". (period)"), self.tr(", (comma)")]:
            self.cbDecimalSep.addItem(label)

        if list_sep in self._list_sep_values:
            self.cbListSep.setCurrentIndex(self._list_sep_values.index(list_sep))
        if decimal_sep in self._decimal_sep_values:
            self.cbDecimalSep.setCurrentIndex(self._decimal_sep_values.index(decimal_sep))

        # Banner for inline validation messages
        self._banner = QGISRedBanner.inject(self, self.verticalLayout)

        # Combos disabled by default (system defaults, checkbox unchecked)
        self._setSeparatorEditable(False)

        # Connections
        self.btnBrowseNodes.clicked.connect(self._browseNodes)
        self.btnBrowseLinks.clicked.connect(self._browseLinks)
        self.chkCustomSeparators.toggled.connect(self._setSeparatorEditable)
        self.buttonBox.accepted.connect(self._onAccepted)
        self.buttonBox.rejected.connect(self.reject)

    @property
    def nodes_path(self):
        return self._nodes_abs

    @property
    def links_path(self):
        return self._links_abs

    @property
    def list_sep(self):
        return self._list_sep_values[self.cbListSep.currentIndex()]

    @property
    def decimal_sep(self):
        return self._decimal_sep_values[self.cbDecimalSep.currentIndex()]

    def _setSeparatorEditable(self, enabled):
        self.cbDecimalSep.setEnabled(enabled)
        self.cbListSep.setEnabled(enabled)
        self.lblDecimalSep.setEnabled(enabled)
        self.lblListSep.setEnabled(enabled)

    def _onAccepted(self):
        if self.decimal_sep == self.list_sep:
            self._banner.pushMessage(
                self.tr("Validations"),
                self.tr("The decimal separator and the list separator cannot be the same character."),
                level=1, duration=0
            )
            return
        self.accept()

    # --- Private helpers ---

    def _display_path(self, abs_path):
        if not abs_path:
            return ""
        try:
            # Check if it is inside the project directory
            rel = os.path.relpath(abs_path, self._project_directory)
            if rel.startswith(".."):
                # Outside: show absolute path (without ../..)
                return os.path.abspath(abs_path).replace("\\", "/")
            else:
                # Inside: show relative path starting with ../
                # We achieve this by making it relative to the parent of the project directory
                proj_part = os.path.basename(os.path.abspath(self._project_directory).rstrip(os.path.sep))
                return os.path.join("..", proj_part, rel).replace("\\", "/")
        except Exception:
            return abs_path.replace("\\", "/")

    def _browse(self, current_abs, line_edit, setter):
        qfd = QFileDialog()
        path, _ = QFileDialog.getSaveFileName(
            qfd, self.tr("Select CSV file"), current_abs, "CSV (*.csv)"
        )
        if path:
            setter(path)
            line_edit.setText(self._display_path(path))

    def _browseNodes(self):
        self._browse(self._nodes_abs, self.leNodesPath, lambda p: setattr(self, "_nodes_abs", p))

    def _browseLinks(self):
        self._browse(self._links_abs, self.leLinksPath, lambda p: setattr(self, "_links_abs", p))
