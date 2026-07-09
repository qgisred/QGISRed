# -*- coding: utf-8 -*-
from contextlib import suppress

from qgis.PyQt.QtCore import Qt, QSize, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QComboBox, QLabel, QFrame
)

from .qgisred_profile_plot import ProfilePlotWidget

_ACCENT = "#00838F"


PROFILE_VARIABLES = [
    ("Elevation", "Elevation"),
    ("Head", "Head"),
    ("Pressure", "Pressure"),
    ("Quality", "Quality"),
    ("Accumulated head loss", "HeadLoss"),
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


class QGISRedProfileDock(QDockWidget):
    profileModeChanged = pyqtSignal(str)
    clearRequested = pyqtSignal()
    variableChanged = pyqtSignal(str)
    symbolsToggled = pyqtSignal(bool)
    envelopeToggled = pyqtSignal(bool)

    def __init__(self, iface, parent=None):
        super(QGISRedProfileDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle(self.tr("QGISRed: Longitudinal profile"))
        self.setObjectName("QGISRedProfileDock")
        self._suppress_mode_signal = False
        self._modeButtons = {}
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

        self.btnPick = self._addModeButton(toolbar_widget, toolbar, "pick", ":/images/iconProfilePick.svg",
                                           self.tr("Click network nodes on the map to build the profile path"))
        self.btnAdd = self._addModeButton(toolbar_widget, toolbar, "add", ":/images/iconProfileAddNode.svg",
                                          self.tr("Convert an intermediate node of the path into a profile point"))
        self.btnRemove = self._addModeButton(toolbar_widget, toolbar, "remove", ":/images/iconProfileRemoveNode.svg",
                                             self.tr("Remove a declared profile point"))
        self.btnMove = self._addModeButton(toolbar_widget, toolbar, "move", ":/images/iconProfileMoveNode.svg",
                                           self.tr("Move a profile point: click it, then its new position"))
        self.btnBranch = self._addModeButton(toolbar_widget, toolbar, "branch", ":/images/iconProfileBranch.svg",
                                             self.tr("Add a branch: click a node of the profile, then the branch endpoints"))

        toolbar.addWidget(self._separator(toolbar_widget))

        self.btnClear = self._makeIconButton(toolbar_widget, ":/images/iconTsClearAll.svg",
                                             self.tr("Remove the current profile path"))
        self.btnClear.clicked.connect(self.clearRequested)
        toolbar.addWidget(self.btnClear)

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

        self.btnEnvelope = self._makeIconButton(toolbar_widget, ":/images/iconProfileEnvelope.svg",
                                                self.tr("Show the maximum and minimum at each node over the whole simulation"),
                                                checkable=True)
        self.btnEnvelope.toggled.connect(self.envelopeToggled)
        toolbar.addWidget(self.btnEnvelope)

        toolbar.addSpacing(10)
        variable_label = QLabel(self.tr("Variable:"), toolbar_widget)
        variable_label.setStyleSheet("QLabel { background: transparent; border: none; }")
        toolbar.addWidget(variable_label)

        self.cbVariable = QComboBox(toolbar_widget)
        for display, _key in PROFILE_VARIABLES:
            self.cbVariable.addItem(self.tr(display))
        default_index = next((i for i, (_d, key) in enumerate(PROFILE_VARIABLES) if key == "Head"), 0)
        self.cbVariable.setCurrentIndex(default_index)
        self.cbVariable.currentIndexChanged.connect(self._onVariableChanged)
        toolbar.addWidget(self.cbVariable)

        toolbar.addStretch(1)
        layout.addWidget(toolbar_widget)

        self.plot = ProfilePlotWidget(container)
        self.plot.setEmptyText(self.tr("Enable 'Pick path' and click nodes on the map"))
        layout.addWidget(self.plot, 1)

        self.setWidget(container)

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

    def _addModeButton(self, parent, toolbar, mode, icon_path, tooltip):
        button = self._makeIconButton(parent, icon_path, tooltip, checkable=True)
        button.toggled.connect(lambda checked, m=mode: self._onModeToggled(m, checked))
        toolbar.addWidget(button)
        self._modeButtons[mode] = button
        return button

    def _separator(self, parent):
        line = QFrame(parent)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def currentVariableKey(self):
        index = self.cbVariable.currentIndex()
        if 0 <= index < len(PROFILE_VARIABLES):
            return PROFILE_VARIABLES[index][1]
        return "Elevation"

    def setActiveMode(self, mode):
        self._suppress_mode_signal = True
        for m, button in self._modeButtons.items():
            button.setChecked(m == mode)
        self._suppress_mode_signal = False

    def setSeries(self, series, title, x_label, y_label):
        self.plot.setLabels(title, x_label, y_label)
        self.plot.setSeries(series)

    def setSymbols(self, node_kinds, link_info):
        self.plot.setSymbols(node_kinds, link_info)

    def clearSymbols(self):
        self.plot.clearSymbols()

    def setEnvelope(self, max_points, min_points):
        self.plot.setEnvelope(max_points, min_points)

    def clearEnvelope(self):
        self.plot.clearEnvelope()

    def clearPlot(self):
        self.plot.clear()

    def _onModeToggled(self, mode, checked):
        if self._suppress_mode_signal:
            return
        if checked:
            self._suppress_mode_signal = True
            for other, button in self._modeButtons.items():
                if other != mode:
                    button.setChecked(False)
            self._suppress_mode_signal = False
            self.profileModeChanged.emit(mode)
        elif not any(button.isChecked() for button in self._modeButtons.values()):
            self.profileModeChanged.emit("")

    def _onToggleValueLabels(self, checked):
        self.plot.setShowValueLabels(checked)

    def _onVariableChanged(self, _index):
        self.variableChanged.emit(self.currentVariableKey())
