# -*- coding: utf-8 -*-
import os

from qgis.PyQt.QtWidgets import QDialog, QFileDialog
from qgis.PyQt import uic

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

        # Connections
        self.btnBrowseNodes.clicked.connect(self._browseNodes)
        self.btnBrowseLinks.clicked.connect(self._browseLinks)
        self.buttonBox.accepted.connect(self.accept)
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

    # --- Private helpers ---

    def _display_path(self, abs_path):
        try:
            return os.path.relpath(abs_path, self._project_directory)
        except ValueError:
            return abs_path

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
