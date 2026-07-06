# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QToolButton, QComboBox, QLabel
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
    pickPathRequested = pyqtSignal()
    pickPathCancelled = pyqtSignal()
    clearRequested = pyqtSignal()
    variableChanged = pyqtSignal(str)

    def __init__(self, iface, parent=None):
        super(QGISRedProfileDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle(self.tr("Longitudinal profile"))
        self.setObjectName("QGISRedProfileDock")
        self._suppress_pick_signal = False
        self._buildUi()

    def _buildUi(self):
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self.btnPick = QToolButton(container)
        self.btnPick.setText(self.tr("Pick path"))
        self.btnPick.setToolTip(self.tr("Click network nodes on the map to build the profile path"))
        self.btnPick.setCheckable(True)
        self.btnPick.toggled.connect(self._onPickToggled)
        toolbar.addWidget(self.btnPick)

        self.btnClear = QToolButton(container)
        self.btnClear.setText(self.tr("Clear"))
        self.btnClear.setToolTip(self.tr("Remove the current profile path"))
        self.btnClear.clicked.connect(self.clearRequested)
        toolbar.addWidget(self.btnClear)

        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel(self.tr("Variable:"), container))

        self.cbVariable = QComboBox(container)
        for display, _key in PROFILE_VARIABLES:
            self.cbVariable.addItem(self.tr(display))
        self.cbVariable.currentIndexChanged.connect(self._onVariableChanged)
        toolbar.addWidget(self.cbVariable)

        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.plot = ProfilePlotWidget(container)
        self.plot.setEmptyText(self.tr("Enable 'Pick path' and click nodes on the map"))
        layout.addWidget(self.plot, 1)

        self.setWidget(container)

    def currentVariableKey(self):
        idx = self.cbVariable.currentIndex()
        if 0 <= idx < len(PROFILE_VARIABLES):
            return PROFILE_VARIABLES[idx][1]
        return "Elevation"

    def setPickActive(self, active):
        self._suppress_pick_signal = True
        self.btnPick.setChecked(bool(active))
        self._suppress_pick_signal = False

    def setSeries(self, series, title, x_label, y_label):
        self.plot.setLabels(title, x_label, y_label)
        self.plot.setSeries(series)

    def clearPlot(self):
        self.plot.clear()

    def _onPickToggled(self, checked):
        if self._suppress_pick_signal:
            return
        if checked:
            self.pickPathRequested.emit()
        else:
            self.pickPathCancelled.emit()

    def _onVariableChanged(self, _idx):
        self.variableChanged.emit(self.currentVariableKey())
