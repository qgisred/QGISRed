# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QComboBox, QLabel, QFrame
)

from .qgisred_profile_plot import ProfilePlotWidget


PROFILE_VARIABLES = [
    ("Elevation", "Elevation"),
    ("Head", "Head"),
    ("Pressure", "Pressure"),
    ("Quality", "Quality"),
    ("Accumulated head loss", "HeadLoss"),
]


class QGISRedProfileDock(QDockWidget):
    profileModeChanged = pyqtSignal(str)
    clearRequested = pyqtSignal()
    variableChanged = pyqtSignal(str)
    symbolsToggled = pyqtSignal(bool)

    def __init__(self, iface, parent=None):
        super(QGISRedProfileDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle(self.tr("Longitudinal profile"))
        self.setObjectName("QGISRedProfileDock")
        self._suppress_mode_signal = False
        self._modeButtons = {}
        self._buildUi()

    def _buildUi(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.btnPick = self._addModeButton(toolbar, "pick", self.tr("Pick path"),
                                           self.tr("Click network nodes on the map to build the profile path"))
        self.btnAdd = self._addModeButton(toolbar, "add", self.tr("Add point"),
                                          self.tr("Convert an intermediate node of the path into a profile point"))
        self.btnRemove = self._addModeButton(toolbar, "remove", self.tr("Remove point"),
                                             self.tr("Remove a declared profile point"))
        self.btnMove = self._addModeButton(toolbar, "move", self.tr("Move point"),
                                           self.tr("Move a profile point: click it, then its new position"))

        toolbar.addWidget(self._separator(container))

        self.btnClear = QToolButton(container)
        self.btnClear.setText(self.tr("Clear"))
        self.btnClear.setToolTip(self.tr("Remove the current profile path"))
        self.btnClear.clicked.connect(self.clearRequested)
        toolbar.addWidget(self.btnClear)

        self.btnLabels = QToolButton(container)
        self.btnLabels.setText(self.tr("Show values"))
        self.btnLabels.setToolTip(self.tr("Show the variable value at each declared profile point"))
        self.btnLabels.setCheckable(True)
        self.btnLabels.toggled.connect(self._onToggleValueLabels)
        toolbar.addWidget(self.btnLabels)

        self.btnSymbols = QToolButton(container)
        self.btnSymbols.setText(self.tr("Symbols"))
        self.btnSymbols.setToolTip(self.tr("Show element symbols and flow direction along the profile"))
        self.btnSymbols.setCheckable(True)
        self.btnSymbols.toggled.connect(self.symbolsToggled)
        toolbar.addWidget(self.btnSymbols)

        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel(self.tr("Variable:"), container))

        self.cbVariable = QComboBox(container)
        for display, _key in PROFILE_VARIABLES:
            self.cbVariable.addItem(self.tr(display))
        default_index = next((i for i, (_d, key) in enumerate(PROFILE_VARIABLES) if key == "Head"), 0)
        self.cbVariable.setCurrentIndex(default_index)
        self.cbVariable.currentIndexChanged.connect(self._onVariableChanged)
        toolbar.addWidget(self.cbVariable)

        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.plot = ProfilePlotWidget(container)
        self.plot.setEmptyText(self.tr("Enable 'Pick path' and click nodes on the map"))
        layout.addWidget(self.plot, 1)

        self.setWidget(container)

    def _addModeButton(self, toolbar, mode, text, tooltip):
        button = QToolButton(self.widget() if self.widget() else None)
        button.setText(text)
        button.setToolTip(tooltip)
        button.setCheckable(True)
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
