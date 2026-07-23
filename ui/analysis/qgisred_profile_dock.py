# -*- coding: utf-8 -*-
from contextlib import suppress

from qgis.PyQt.QtCore import Qt, QSize, QRect, QEvent, pyqtSignal
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QComboBox, QLabel, QFrame,
    QSplitter, QTableWidget, QTableWidgetItem, QAbstractItemView, QFileDialog, QHeaderView, QMenu,
    QDialog, QDialogButtonBox, QPlainTextEdit, QScrollArea
)

from .qgisred_profile_plot import ProfilePlotWidget

_ACCENT = "#00838F"


PROFILE_VARIABLES = [
    ("Elevation", "Elevation"),
    ("Head + Elevation", "Head"),
    ("Pressure", "Pressure"),
    ("Accumulated head loss", "HeadLoss"),
    ("Quality", "Quality"),
]

PROFILE_SECONDARY_VARIABLE_KEYS = ("Pressure", "HeadLoss", "Quality")

_PROFILE_VARIABLE_DISPLAYS = {key: display for display, key in PROFILE_VARIABLES}


def secondary_variable_keys(primary_key):
    return [
        key
        for _display, key in PROFILE_VARIABLES
        if key in PROFILE_SECONDARY_VARIABLE_KEYS and key != primary_key
    ]


_BTN_STYLE = (
    "QToolButton {"
    "  border: 1px solid #c8c8c8;"
    "  border-radius: 3px;"
    "  background-color: #f8f8f8;"
    "  padding: 1px;"
    "}"
    "QToolButton:hover { background-color: #f0f0f0; border-color: #bdbdbd; }"
    "QToolButton:pressed { background-color: #e6e6e6; border-color: #b4b4b4; }"
    "QToolButton:checked { background-color: #d0e4f7; border-color: #3399ff; }"
    "QToolButton:focus { border: 1px solid #3399ff; }"
)

_MENU_BTN_STYLE = _BTN_STYLE + "QToolButton::menu-indicator { image: none; width: 0px; }"


class QGISRedProfileDock(QDockWidget):
    editModeToggled = pyqtSignal(bool)
    clearRequested = pyqtSignal()
    variableChanged = pyqtSignal(str)
    secondaryVariableChanged = pyqtSignal(str)
    symbolsToggled = pyqtSignal(bool)
    envelopeModeChanged = pyqtSignal(str)
    exportConfigRequested = pyqtSignal(str)
    importConfigRequested = pyqtSignal(str)
    newPanelRequested = pyqtSignal()
    activated = pyqtSignal()
    curveDeleteRequested = pyqtSignal(str)

    def __init__(self, iface, parent=None):
        super(QGISRedProfileDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle(self.tr("QGISRed: Longitudinal profile"))
        self.setObjectName("QGISRedProfileDock")
        self._chartComment = ""
        self._defaultConfigPath = ""
        self._buildUi()
        with suppress(Exception):
            from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils
            QGISRedUIUtils.applyDockStyle(self, _ACCENT, backgroundColor="white")

    def _buildUi(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        toolbar_widget = QWidget(container)
        self._toolbarBox = toolbar_widget
        toolbar_widget.setObjectName("profileToolbar")
        toolbar_widget.setMinimumHeight(34)
        toolbar_widget.setStyleSheet(
            "QWidget#profileToolbar {"
            "  background-color: #efefef;"
            "  border: 1px solid #d2d2d2;"
            "  border-radius: 4px;"
            "}"
        )
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(6, 3, 6, 3)
        toolbar.setSpacing(3)

        self.btnNewPanel = self._makeIconButton(toolbar_widget, ":/images/iconAddData.svg",
                                                self.tr("New profile panel"))
        self.btnNewPanel.clicked.connect(self.newPanelRequested)
        toolbar.addWidget(self.btnNewPanel)
        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnEdit = self._makeIconButton(
            toolbar_widget, ":/images/pencil.svg",
            self.tr("Edit trajectories: click nodes to trace, right-click a node for its options"),
            checkable=True)
        self.btnEdit.toggled.connect(self._onEditToggled)
        toolbar.addWidget(self.btnEdit)

        self.btnHelp = self._makeIconButton(
            toolbar_widget, ":/images/iconAbout.svg",
            self.tr("How to edit trajectories"))
        self.btnHelp.clicked.connect(self.showEditHelp)
        toolbar.addWidget(self.btnHelp)

        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnZoomWindow = self._makeIconButton(toolbar_widget, ":/images/iconTsZoomWindow.svg",
                                                  self.tr("Zoom window"), checkable=True)
        self.btnZoomWindow.toggled.connect(self._onZoomWindowToggled)
        toolbar.addWidget(self.btnZoomWindow)

        self.btnPan = self._makeIconButton(toolbar_widget, ":/images/iconTsPan.svg", self.tr("Pan"), checkable=True)
        self.btnPan.toggled.connect(self._onPanToggled)
        toolbar.addWidget(self.btnPan)

        self.btnZoomIn = self._makeIconButton(toolbar_widget, ":/images/iconTsZoomIn.svg", self.tr("Zoom in"))
        self.btnZoomIn.clicked.connect(self._onZoomIn)
        toolbar.addWidget(self.btnZoomIn)

        self.btnZoomOut = self._makeIconButton(toolbar_widget, ":/images/iconTsZoomOut.svg", self.tr("Zoom out"))
        self.btnZoomOut.clicked.connect(self._onZoomOut)
        toolbar.addWidget(self.btnZoomOut)

        self.btnFit = self._makeIconButton(toolbar_widget, ":/images/iconTsFit.svg", self.tr("Zoom to full extent"))
        self.btnFit.clicked.connect(self._onFit)
        toolbar.addWidget(self.btnFit)

        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnLabels = self._makeIconButton(toolbar_widget, ":/images/iconProfileLabels.svg",
                                              self.tr("Show the variable value at each declared profile point"),
                                              checkable=True)
        self.btnLabels.toggled.connect(self._onToggleValueLabels)
        toolbar.addWidget(self.btnLabels)

        self.btnSymbols = self._makeIconButton(toolbar_widget, ":/images/iconProfileSymbols.svg",
                                               self.tr("Show element symbols and flow direction along the profile"),
                                               checkable=True)
        self.btnSymbols.toggled.connect(self.symbolsToggled)
        toolbar.addWidget(self.btnSymbols)

        self.btnEnvelope = self._makeMenuButton(
            toolbar_widget, ":/images/iconProfileEnvelope.svg",
            self.tr("Show the maximum and minimum at each node over the whole simulation"))
        self._envelopeActions = {}
        envelope_menu = QMenu(self.btnEnvelope)
        envelope_modes = [
            ("off", self.tr("Off")),
            ("band", self.tr("Shaded band only")),
            ("lines", self.tr("Boundary lines only")),
            ("both", self.tr("Band and lines")),
        ]
        for mode, label in envelope_modes:
            action = envelope_menu.addAction(label)
            action.setCheckable(True)
            action.triggered.connect(lambda _checked=False, m=mode: self._onEnvelopeModeSelected(m))
            self._envelopeActions[mode] = action
        self._envelopeActions["off"].setChecked(True)
        self.btnEnvelope.setMenu(envelope_menu)
        toolbar.addWidget(self.btnEnvelope)

        self.btnChartOptions = self._makeIconButton(toolbar_widget, ":/images/iconTsAxes.svg",
                                                    self.tr("Chart options"))
        self.btnChartOptions.clicked.connect(self._onChartOptions)
        toolbar.addWidget(self.btnChartOptions)

        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnTable = self._makeIconButton(toolbar_widget, ":/images/iconTsTable.svg",
                                             self.tr("Show/Hide values table"), checkable=True)
        self.btnTable.toggled.connect(self._onToggleTable)
        toolbar.addWidget(self.btnTable)

        self.btnExportCsv = self._makeIconButton(toolbar_widget, ":/images/iconTsExportCsv.svg",
                                                 self.tr("Export values to CSV"))
        self.btnExportCsv.clicked.connect(self._onExportCsv)
        toolbar.addWidget(self.btnExportCsv)

        self.btnExportImage = self._makeIconButton(toolbar_widget, ":/images/iconTsExportImage.svg",
                                                   self.tr("Save chart as image"))
        self.btnExportImage.clicked.connect(self._onExportImage)
        toolbar.addWidget(self.btnExportImage)

        self.btnExportConfig = self._makeIconButton(toolbar_widget, ":/images/iconStatisticsExport.svg",
                                                    self.tr("Export profile configuration"))
        self.btnExportConfig.clicked.connect(self._onExportConfigClicked)
        toolbar.addWidget(self.btnExportConfig)

        self.btnImportConfig = self._makeIconButton(toolbar_widget, ":/images/iconStatisticsImport.svg",
                                                    self.tr("Import profile configuration"))
        self.btnImportConfig.clicked.connect(self._onImportConfigClicked)
        toolbar.addWidget(self.btnImportConfig)

        self.btnEditComment = self._makeIconButton(toolbar_widget, ":/images/iconComment.svg",
                                                   self.tr("Edit chart description"))
        self.btnEditComment.clicked.connect(self._onEditCommentClicked)
        toolbar.addWidget(self.btnEditComment)

        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnClear = self._makeIconButton(toolbar_widget, ":/images/iconTsClearAll.svg",
                                             self.tr("Remove the current profile path"))
        self.btnClear.clicked.connect(self.clearRequested)
        toolbar.addWidget(self.btnClear)

        toolbar.addSpacing(10)
        variable_label = QLabel(self.tr("Variable:"), toolbar_widget)
        variable_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        toolbar.addWidget(variable_label)

        self.cbVariable = QComboBox(toolbar_widget)
        for _display, key in PROFILE_VARIABLES:
            self.cbVariable.addItem(self._variableDisplayText(key), key)
        default_index = next((i for i, (_d, key) in enumerate(PROFILE_VARIABLES) if key == "Head"), 0)
        self.cbVariable.setCurrentIndex(default_index)
        self.cbVariable.currentIndexChanged.connect(self._onVariableChanged)
        toolbar.addWidget(self.cbVariable)

        secondary_label = QLabel(self.tr("2nd axis:"), toolbar_widget)
        secondary_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        toolbar.addWidget(secondary_label)

        self.cbSecondary = QComboBox(toolbar_widget)
        self._rebuildSecondaryVariables()
        self.cbSecondary.currentIndexChanged.connect(self._onSecondaryChanged)
        toolbar.addWidget(self.cbSecondary)

        toolbar.addStretch(1)

        toolbar_scroll = QScrollArea(container)
        toolbar_scroll.setObjectName("profileToolbarScroll")
        toolbar_scroll.setWidgetResizable(True)
        toolbar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        toolbar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        toolbar_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        toolbar_scroll.setStyleSheet(
            "QScrollArea#profileToolbarScroll { background: transparent; border: none; }"
            "QScrollBar:horizontal { height: 8px; }"
        )
        toolbar_scroll.setWidget(toolbar_widget)
        toolbar_scroll.setFixedHeight(44)
        layout.addWidget(toolbar_scroll)

        self._splitter = QSplitter(Qt.Orientation.Horizontal, container)
        self._splitter.setChildrenCollapsible(False)

        # Table pane goes first (left); the plot follows on the right.
        self.table = QTableWidget(self._splitter)
        self.table.setObjectName("profileValuesTable")
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        with suppress(Exception):
            hdr_font = self.table.horizontalHeader().font()
            hdr_font.setBold(True)
            self.table.horizontalHeader().setFont(hdr_font)
        self.table.horizontalHeader().setStyleSheet(
            "QHeaderView::section {"
            "  font-weight: 700;"
            "  background-color: #f5f5f5;"
            "  padding: 2px 6px;"
            "  border: 1px solid #c8c8c8;"
            "}"
        )
        self.table.setStyleSheet("QTableWidget { gridline-color: #c8c8c8; }")
        with suppress(Exception):
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.hide()
        self._splitter.addWidget(self.table)

        self.plot = ProfilePlotWidget(self._splitter)
        self.plot.setEmptyText(self.tr("Turn on 'Edit trajectories' and click nodes on the map"))
        self.plot.cursorNodeChanged.connect(self._onCursorNode)
        self.plot.curveDeleteRequested.connect(self.curveDeleteRequested)
        self.table.currentCellChanged.connect(self._onTableRowChanged)
        self._splitter.addWidget(self.plot)

        self._splitter.setStretchFactor(0, 0)
        self._splitter.setStretchFactor(1, 1)

        layout.addWidget(self._splitter, 1)
        self.setWidget(container)
        self._updateChartActionsEnabled()

        with suppress(Exception):
            self.plot.installEventFilter(self)
            self.table.installEventFilter(self)
            self._toolbarBox.installEventFilter(self)

    def eventFilter(self, obj, event):
        with suppress(Exception):
            if event is not None and event.type() == QEvent.Type.MouseButtonPress:
                self.activated.emit()
        return super(QGISRedProfileDock, self).eventFilter(obj, event)

    def mousePressEvent(self, event):
        with suppress(Exception):
            self.activated.emit()
        super(QGISRedProfileDock, self).mousePressEvent(event)

    def focusInEvent(self, event):
        with suppress(Exception):
            self.activated.emit()
        super(QGISRedProfileDock, self).focusInEvent(event)

    def showEvent(self, event):
        super(QGISRedProfileDock, self).showEvent(event)
        with suppress(Exception):
            self.activated.emit()

    def _makeIconButton(self, parent, icon_path, tooltip, checkable=False):
        button = QToolButton(parent)
        button.setIcon(QIcon(icon_path))
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        button.setCheckable(checkable)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(QSize(24, 24))
        button.setStyleSheet(_BTN_STYLE)
        return button

    def _makeMenuButton(self, parent, icon_path, tooltip):
        button = QToolButton(parent)
        button.setIcon(QIcon(icon_path))
        button.setToolTip(tooltip)
        button.setAutoRaise(True)
        button.setCheckable(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        button.setIconSize(QSize(16, 16))
        button.setFixedSize(QSize(24, 24))
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        button.setStyleSheet(_MENU_BTN_STYLE)
        return button

    def _separator(self, parent):
        line = QFrame(parent)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _variableDisplayText(self, key):
        if key == "Quality" and getattr(self, "_qualityDisplayName", ""):
            return self._qualityDisplayName
        return self.tr(_PROFILE_VARIABLE_DISPLAYS.get(key, key))

    def _rebuildSecondaryVariables(self):
        previous = self.currentSecondaryVariableKey() if self.cbSecondary.count() else ""
        primary = self.currentVariableKey()
        self.cbSecondary.blockSignals(True)
        self.cbSecondary.clear()
        self.cbSecondary.addItem(self.tr("None"), "")
        for key in secondary_variable_keys(primary):
            self.cbSecondary.addItem(self._variableDisplayText(key), key)
        target = self.cbSecondary.findData(previous) if previous else 0
        self.cbSecondary.setCurrentIndex(target if target >= 0 else 0)
        self.cbSecondary.blockSignals(False)

    def currentVariableKey(self):
        key = self.cbVariable.currentData()
        return key if key else "Elevation"

    def currentSecondaryVariableKey(self):
        return self.cbSecondary.currentData() or ""

    def setSecondaryVariableKey(self, key):
        self.cbSecondary.blockSignals(True)
        target = self.cbSecondary.findData(key or "")
        self.cbSecondary.setCurrentIndex(target if target >= 0 else 0)
        self.cbSecondary.blockSignals(False)

    def setQualityDisplayName(self, name):
        self._qualityDisplayName = name or ""
        with suppress(Exception):
            index = self.cbVariable.findData("Quality")
            if index >= 0:
                self.cbVariable.setItemText(index, self._variableDisplayText("Quality"))
            self._rebuildSecondaryVariables()

    def setEditMode(self, on):
        self._setCheckedSilently(self.btnEdit, bool(on))
        self.editModeToggled.emit(bool(on))

    def isEditMode(self):
        return self.btnEdit.isChecked()

    def setSeries(self, series, title, x_label, y_label, y_right_label=""):
        self.plot.setLabels(title, x_label, y_label, y_right_label)
        self.plot.setSeries(series)
        self._updateChartActionsEnabled()

    def setSymbols(self, symbols):
        self.plot.setSymbols(symbols)

    def clearSymbols(self):
        self.plot.clearSymbols()

    def setEnvelope(self, max_points, min_points, mode="both", labels=None):
        self.plot.setEnvelope(max_points, min_points, mode, labels)

    def currentEnvelopeMode(self):
        for mode, action in self._envelopeActions.items():
            if action.isChecked():
                return mode
        return "off"

    def _onEnvelopeModeSelected(self, mode):
        for m, action in self._envelopeActions.items():
            action.setChecked(m == mode)
        self.btnEnvelope.setChecked(mode != "off")
        self.envelopeModeChanged.emit(mode)

    def clearEnvelope(self):
        self.plot.clearEnvelope()

    def setStableRanges(self, left_points, right_points):
        self.plot.setStableRanges(left_points, right_points)

    def clearPlot(self):
        self.plot.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self._updateChartActionsEnabled()

    def resetControls(self):
        self._setCheckedSilently(self.btnZoomWindow, False)
        self.plot.setZoomWindowMode(False)
        self._setCheckedSilently(self.btnPan, False)
        self.plot.setPanMode(False)
        self.setLabelsChecked(False)
        self.setSymbolsChecked(False)
        self.setEnvelopeModeState("off")
        self._setCheckedSilently(self.btnTable, False)
        self.table.setVisible(False)
        self._updateChartActionsEnabled()

    @staticmethod
    def _setCheckedSilently(button, checked):
        button.blockSignals(True)
        button.setChecked(checked)
        button.blockSignals(False)

    def _updateChartActionsEnabled(self):
        has_data = bool(getattr(self.plot, "_series", []))
        for button in (self.btnClear,
                       self.btnZoomWindow, self.btnPan, self.btnZoomIn, self.btnZoomOut, self.btnFit,
                       self.btnLabels, self.btnSymbols, self.btnEnvelope, self.btnChartOptions,
                       self.btnTable, self.btnExportCsv, self.btnExportImage,
                       self.btnExportConfig, self.btnEditComment):
            button.setEnabled(has_data)
        self.table.setVisible(has_data and self.btnTable.isChecked())

    def _onCursorNode(self, index):
        if not self.table.isVisible():
            return
        if index is None or index < 0 or index >= self.table.rowCount():
            return
        if self.table.currentRow() != index:
            self.table.selectRow(index)
        with suppress(Exception):
            self.table.scrollToItem(self.table.item(index, 0))

    def _onTableRowChanged(self, current_row, current_column=0, previous_row=-1, previous_column=-1):
        self.plot.setCursorNode(current_row)

    def setTableData(self, headers, rows):
        self.table.clear()
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem("" if value is None else str(value))
                if c >= 1:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()

    def _onToggleTable(self, checked):
        self.table.setVisible(checked)
        if checked:
            total = max(self._splitter.width(), 600)
            table_w = min(max(240, int(total * 0.28)), 360)
            self._splitter.setSizes([table_w, max(200, total - table_w)])

    def _chartHasCurves(self):
        return bool(getattr(self.plot, "_series", []))

    def _notify(self, text, level=3):
        with suppress(Exception):
            self.iface.messageBar().pushMessage("QGISRed", text, level=level, duration=4)

    def _headerText(self, column):
        item = self.table.horizontalHeaderItem(column)
        return item.text() if item is not None else ""

    def _onExportCsv(self):
        import os
        import csv
        if self.table.rowCount() == 0 or self.table.columnCount() == 0:
            self._notify(self.tr("There are no values to export"), level=1)
            return
        default_path = os.path.join(os.path.expanduser("~"), "longitudinal_profile.csv")
        path, _selected = QFileDialog.getSaveFileName(
            self, self.tr("Export values to CSV"), default_path, self.tr("CSV file (*.csv)"))
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        list_sep, decimal_sep = ",", "."
        with suppress(Exception):
            from .qgisred_results_data import get_regional_separators
            list_sep, decimal_sep = get_regional_separators()
        if list_sep == decimal_sep:
            list_sep = ";"
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f, delimiter=list_sep)
                writer.writerow([self._headerText(c) for c in range(self.table.columnCount())])
                for r in range(self.table.rowCount()):
                    row = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        text = item.text() if item is not None else ""
                        if c >= 1 and decimal_sep != ".":
                            text = text.replace(".", decimal_sep)
                        row.append(text)
                    writer.writerow(row)
        except Exception:
            self._notify(self.tr("The values could not be exported"), level=2)
            return
        self._notify(self.tr("Values exported to CSV"))

    def _onExportImage(self):
        import os
        if not self._chartHasCurves():
            self._notify(self.tr("There is no chart to export"), level=1)
            return
        filters = [self.tr("PNG image (*.png)"), self.tr("SVG image (*.svg)")]
        default_path = os.path.join(os.path.expanduser("~"), "longitudinal_profile.png")
        path, _selected = QFileDialog.getSaveFileName(
            self, self.tr("Save chart as image"), default_path, ";;".join(filters))
        if not path:
            return
        try:
            if path.lower().endswith(".svg"):
                self._saveChartSvg(path)
            else:
                if not path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    path += ".png"
                self._renderPlotToPixmap().save(path)
        except Exception:
            self._notify(self.tr("The chart image could not be saved"), level=2)
            return
        self._notify(self.tr("Chart image saved"))

    def _renderPlotToPixmap(self):
        pixmap = QPixmap(self.plot.size())
        pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap)
        self.plot.render(painter)
        painter.end()
        return pixmap

    def _saveChartSvg(self, path):
        try:
            from qgis.PyQt.QtSvg import QSvgGenerator
        except Exception:
            QSvgGenerator = None
        if QSvgGenerator is None:
            self._renderPlotToPixmap().save(path[:-4] + ".png")
            return
        generator = QSvgGenerator()
        generator.setFileName(path)
        generator.setSize(self.plot.size())
        generator.setViewBox(QRect(0, 0, self.plot.width(), self.plot.height()))
        painter = QPainter(generator)
        self.plot.render(painter)
        painter.end()

    def _onEditToggled(self, checked):
        self.editModeToggled.emit(bool(checked))

    def showEditHelp(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("How to edit trajectories"))
        layout = QVBoxLayout(dlg)
        scroll = QScrollArea(dlg)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QLabel(self._editHelpHtml(), dlg)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        body.setAlignment(Qt.AlignmentFlag.AlignTop)
        body.setContentsMargins(4, 4, 4, 4)
        scroll.setWidget(body)
        layout.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, dlg)
        buttons.rejected.connect(dlg.reject)
        buttons.accepted.connect(dlg.accept)
        layout.addWidget(buttons)
        dlg.resize(520, 460)
        dlg.exec()

    def _editHelpHtml(self):
        rows = [
            (self.tr("Trace the first path"),
             self.tr("Turn on Edit, click the pass nodes one after another, and right-click to finish "
                     "(just like drawing a pipe in QGISRed).")),
            (self.tr("Extend a path"),
             self.tr("Right-click its end node and keep clicking nodes to prolong it; right-click to finish.")),
            (self.tr("Declare a pass node"),
             self.tr("Right-click an intermediate node of any current path (one that is not a pass node yet).")),
            (self.tr("Move a pass node"),
             self.tr("Right-click it, choose Move, then click a free node (it may be a bifurcation, a branch "
                     "end, or the tree origin).")),
            (self.tr("Remove a pass node"),
             self.tr("Right-click it and choose Delete. A bifurcation cannot be removed directly.")),
            (self.tr("Create a branch"),
             self.tr("Right-click any pass node, then click the new branch nodes one after another "
                     "(without repeating a node already declared); right-click to finish.")),
            (self.tr("Remove a branch"),
             self.tr("Delete its pass nodes from the far end toward the origin. When only the branch end is "
                     "left, deleting it removes the whole branch.")),
        ]
        intro = self.tr("Everything starts with the single Edit trajectories button. While editing is on, "
                        "clicking and right-clicking network nodes builds and reshapes the paths. Turn it off "
                        "and moving over a trajectory only tracks it and shows information on the chart.")
        items = "".join("<li><b>{0}.</b> {1}</li>".format(title, text) for title, text in rows)
        return "<p>{0}</p><ul>{1}</ul>".format(intro, items)

    def _onChartOptions(self):
        from .qgisred_profile_chart_options_dialog import QGISRedProfileChartOptionsDialog
        dialog = QGISRedProfileChartOptionsDialog(self.plot, self)
        dialog.exec()

    def _onToggleValueLabels(self, checked):
        self.plot.setShowValueLabels(checked)

    def _onPanToggled(self, checked):
        if checked and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        self.plot.setPanMode(checked)

    def _onZoomWindowToggled(self, checked):
        if checked and self.btnPan.isChecked():
            self.btnPan.setChecked(False)
        self.plot.setZoomWindowMode(checked)

    def _onZoomIn(self):
        self.plot.zoomIn()

    def _onZoomOut(self):
        self.plot.zoomOut()

    def _onFit(self):
        self.plot.fitView()

    def _onVariableChanged(self, _index):
        self._rebuildSecondaryVariables()
        self.variableChanged.emit(self.currentVariableKey())

    def _onSecondaryChanged(self, _index):
        self.secondaryVariableChanged.emit(self.currentSecondaryVariableKey())

    def _configDefaultPath(self, for_export):
        import os
        base = self._defaultConfigPath or os.path.join(
            os.path.expanduser("~"), "LongitudinalProfile_Config.cfg")
        if not for_export:
            return base
        with suppress(Exception):
            from .profile_config_io import next_available_config_name
            directory = os.path.dirname(base)
            existing = os.listdir(directory) if directory and os.path.isdir(directory) else []
            return os.path.join(directory, next_available_config_name(os.path.basename(base), existing))
        return base

    def _onExportConfigClicked(self):
        path, _selected = QFileDialog.getSaveFileName(
            self, self.tr("Export profile configuration"),
            self._configDefaultPath(True), self.tr("Configuration file (*.cfg)"))
        if not path:
            return
        if not path.lower().endswith(".cfg"):
            path += ".cfg"
        self.exportConfigRequested.emit(path)

    def _onImportConfigClicked(self):
        import os
        start = self._configDefaultPath(False)
        start_dir = os.path.dirname(start) if start else os.path.expanduser("~")
        path, _selected = QFileDialog.getOpenFileName(
            self, self.tr("Import profile configuration"),
            start_dir, self.tr("Configuration file (*.cfg)"))
        if not path:
            return
        self.importConfigRequested.emit(path)

    def _onEditCommentClicked(self):
        MAX = 256
        dlg = QDialog(self)
        dlg.setWindowTitle(self.tr("Chart description"))
        layout = QVBoxLayout(dlg)
        info = QLabel(self.tr("Describe the chart content (up to 256 characters):"), dlg)
        info.setWordWrap(True)
        layout.addWidget(info)
        editor = QPlainTextEdit(dlg)
        editor.setPlainText(self._chartComment or "")
        editor.setTabChangesFocus(True)
        layout.addWidget(editor)
        counter = QLabel(dlg)
        counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(counter)

        def _enforce():
            text = editor.toPlainText()
            if len(text) > MAX:
                pos = editor.textCursor().position()
                editor.blockSignals(True)
                editor.setPlainText(text[:MAX])
                editor.blockSignals(False)
                cursor = editor.textCursor()
                cursor.setPosition(min(pos, MAX))
                editor.setTextCursor(cursor)
            counter.setText("{}/{}".format(len(editor.toPlainText()), MAX))

        editor.textChanged.connect(_enforce)
        _enforce()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dlg)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        dlg.resize(420, 220)
        if dlg.exec():
            self._chartComment = editor.toPlainText().strip()[:MAX]

    def comment(self):
        return self._chartComment or ""

    def setComment(self, text):
        self._chartComment = (text or "")[:256]

    def setVariableKey(self, key):
        index = self.cbVariable.findData(key)
        if index < 0:
            return
        self.cbVariable.blockSignals(True)
        self.cbVariable.setCurrentIndex(index)
        self.cbVariable.blockSignals(False)
        self._rebuildSecondaryVariables()

    def setSymbolsChecked(self, on):
        self._setCheckedSilently(self.btnSymbols, bool(on))

    def setLabelsChecked(self, on):
        self._setCheckedSilently(self.btnLabels, bool(on))
        self.plot.setShowValueLabels(bool(on))

    def setEnvelopeModeState(self, mode):
        mode = mode or "off"
        for m, action in self._envelopeActions.items():
            action.setChecked(m == mode)
        self.btnEnvelope.setChecked(mode != "off")
