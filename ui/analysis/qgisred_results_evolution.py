# -*- coding: utf-8 -*-
from __future__ import annotations

from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QHBoxLayout, QToolButton, QVBoxLayout, QWidget


class _EvolutionControlsBar(QWidget):
    def __init__(self, tank_toggle_button, expand_button, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(tank_toggle_button)
        layout.addStretch(1)
        layout.addWidget(expand_button)


class _EvolutionPopoutWindow(QWidget):
    _DEFAULT_SIZE = (760, 540)

    def __init__(self, parent, on_close):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self._on_close = on_close
        self._default_geometry = None
        self.setMinimumSize(360, 260)
        self.setStyleSheet("background-color: #f8f9fb;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)

        from .results_evolution_widget import ResultsEvolutionPlotWidget

        self.chart = ResultsEvolutionPlotWidget(self)
        self._layout.addWidget(self.chart, 1)

    def attachControls(self, controls_bar):
        self._layout.insertWidget(0, controls_bar)

    def detachControls(self, controls_bar):
        self._layout.removeWidget(controls_bar)

    def applyDefaultGeometry(self):
        width, height = self._DEFAULT_SIZE
        host = self.parent().window() if self.parent() is not None else None
        if host is not None:
            center = host.frameGeometry().center()
            self.setGeometry(center.x() - width // 2, center.y() - height // 2, width, height)
        else:
            self.resize(width, height)
        self._default_geometry = self.geometry()

    def closeEvent(self, event):
        callback = self._on_close
        if callback is not None:
            callback()
        super().closeEvent(event)


class _ResultsEvolutionMixin:
    def _setupEvolutionCharts(self):
        self._evolution_popout = None
        self._evolution_series_cache = {}
        self._evolution_cursor_hours = None
        panel_bg = "#f8f9fb"
        self.evolutionChartContainer.setStyleSheet(
            "QWidget#evolutionChartContainer {{ background-color: {0}; }}".format(panel_bg)
        )
        self.nodeEvolutionChartHost.setStyleSheet("background-color: {};".format(panel_bg))
        self.linkEvolutionChartHost.setStyleSheet("background-color: {};".format(panel_bg))

        from .results_evolution_widget import ResultsEvolutionPlotWidget

        self._node_evolution_chart = ResultsEvolutionPlotWidget(self.nodeEvolutionChartHost)
        self._link_evolution_chart = ResultsEvolutionPlotWidget(self.linkEvolutionChartHost)
        node_layout = QVBoxLayout(self.nodeEvolutionChartHost)
        node_layout.setContentsMargins(0, 0, 0, 0)
        node_layout.addWidget(self._node_evolution_chart)
        link_layout = QVBoxLayout(self.linkEvolutionChartHost)
        link_layout.setContentsMargins(0, 0, 0, 0)
        link_layout.addWidget(self._link_evolution_chart)

        self._buildEvolutionControlsBar()

        self.cbNodeEvolution.clicked.connect(self.nodeEvolutionClicked)
        self.cbLinkEvolution.clicked.connect(self.linkEvolutionClicked)
        try:
            self.visibilityChanged.connect(self._onEvolutionDockVisibilityChanged)
        except Exception:
            pass
        self._updateEvolutionCheckboxLabels()
        self._syncEvolutionPanelVisibility()

    def _buildEvolutionControlsBar(self):
        self.btEvolutionTankToggle = QToolButton()
        self.btEvolutionTankToggle.setObjectName("btEvolutionTankToggle")
        self.btEvolutionTankToggle.setAutoRaise(False)
        self.btEvolutionTankToggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btEvolutionTankToggle.setStyleSheet(
            "QToolButton#btEvolutionTankToggle {"
            " border: 1px solid #9aa7b4; border-radius: 4px;"
            " padding: 2px 12px; background-color: #ffffff;"
            " color: #1f2a36; font-weight: bold; }"
            "QToolButton#btEvolutionTankToggle:hover {"
            " background-color: #eaf1f8; border-color: #5b86b0; }"
            "QToolButton#btEvolutionTankToggle:pressed {"
            " background-color: #d7e2ee; }"
        )
        self.btEvolutionTankToggle.setVisible(False)
        self.btEvolutionTankToggle.clicked.connect(self._onEvolutionTankToggleClicked)

        self.btEvolutionExpand = QToolButton()
        self.btEvolutionExpand.setObjectName("btEvolutionExpand")
        self.btEvolutionExpand.setIcon(QIcon(":/images/iconTsZoomWindow.svg"))
        self.btEvolutionExpand.setIconSize(QSize(16, 16))
        self.btEvolutionExpand.setAutoRaise(True)
        self.btEvolutionExpand.setCheckable(True)
        self.btEvolutionExpand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btEvolutionExpand.setToolTip(self.tr("Expand chart to a floating window"))
        self.btEvolutionExpand.clicked.connect(self._toggleEvolutionPopout)

        self._evolution_controls_bar = _EvolutionControlsBar(
            self.btEvolutionTankToggle, self.btEvolutionExpand
        )
        self.verticalLayout_EvolutionChart.insertWidget(0, self._evolution_controls_bar)

    def _activeEvolutionLayerType(self):
        if self.cbNodeEvolution.isChecked():
            return "Node"
        if self.cbLinkEvolution.isChecked():
            return "Link"
        return None

    def _activateExclusiveResultsChart(self, which):
        evolution_was_active = self._activeEvolutionLayerType() is not None
        boxes = {
            "NodeDist": self.cbNodeDistribution,
            "LinkDist": self.cbLinkDistribution,
            "NodeEvo": self.cbNodeEvolution,
            "LinkEvo": self.cbLinkEvolution,
        }
        for key, checkbox in boxes.items():
            if key != which and checkbox.isChecked():
                checkbox.blockSignals(True)
                checkbox.setChecked(False)
                checkbox.blockSignals(False)
        self._syncDistributionPanelVisibility()
        self._syncEvolutionPanelVisibility()
        if which not in ("NodeEvo", "LinkEvo") and evolution_was_active:
            self.evolutionPickCancelled.emit()

    def nodeEvolutionClicked(self):
        if self.cbNodeEvolution.isChecked():
            if self.cbNodes.currentIndex() <= 0:
                self.cbNodeEvolution.setChecked(False)
                return
            if not self.validationsOpenResult():
                self.cbNodeEvolution.setChecked(False)
                return
            self._activateExclusiveResultsChart("NodeEvo")
            self.ensureResultsLayersAreOpen()
            self._syncEvolutionPanelVisibility()
            self.evolutionPickRequested.emit("Node")
        else:
            self._syncEvolutionPanelVisibility()
            self.evolutionPickCancelled.emit()

    def linkEvolutionClicked(self):
        if self.cbLinkEvolution.isChecked():
            if self.cbLinks.currentIndex() <= 0:
                self.cbLinkEvolution.setChecked(False)
                return
            if not self.validationsOpenResult():
                self.cbLinkEvolution.setChecked(False)
                return
            self._activateExclusiveResultsChart("LinkEvo")
            self.ensureResultsLayersAreOpen()
            self._syncEvolutionPanelVisibility()
            self.evolutionPickRequested.emit("Link")
        else:
            self._syncEvolutionPanelVisibility()
            self.evolutionPickCancelled.emit()

    def _evolutionCheckboxText(self, layer_type):
        if layer_type == "Node":
            return self.tr("Show Node Evolution")
        return self.tr("Show Link Evolution")

    def _updateEvolutionCheckboxLabels(self):
        self.cbNodeEvolution.setText(self._evolutionCheckboxText("Node"))
        self.cbLinkEvolution.setText(self._evolutionCheckboxText("Link"))
        node_enabled = self.cbNodes.currentIndex() > 0
        link_enabled = self.cbLinks.currentIndex() > 0
        self.cbNodeEvolution.setEnabled(node_enabled)
        self.cbLinkEvolution.setEnabled(link_enabled)
        if not node_enabled and self.cbNodeEvolution.isChecked():
            self.cbNodeEvolution.setChecked(False)
            self.evolutionPickCancelled.emit()
        if not link_enabled and self.cbLinkEvolution.isChecked():
            self.cbLinkEvolution.setChecked(False)
            self.evolutionPickCancelled.emit()
        self._syncEvolutionPanelVisibility()

    def _syncEvolutionPanelVisibility(self):
        active = self._activeEvolutionLayerType()
        popout = getattr(self, "_evolution_popout", None)
        expanded = popout is not None and popout.isVisible()
        if active is None and expanded:
            self._closeEvolutionPopout()
            return
        if expanded:
            return
        self.evolutionChartContainer.setVisible(active is not None)
        self._applySmallEvolutionVisibility()

    def _applySmallEvolutionVisibility(self):
        active = self._activeEvolutionLayerType()
        self.nodeEvolutionChartHost.setVisible(active == "Node")
        self.linkEvolutionChartHost.setVisible(active == "Link")

    def _activeEvolutionChart(self):
        active = self._activeEvolutionLayerType()
        if active == "Node":
            return self._node_evolution_chart
        if active == "Link":
            return self._link_evolution_chart
        return None

    def setEvolutionSeries(
        self, layer_type, x_hours, y_values, title="", x_label="", y_label="",
        is_stepped=False, y_categorical_labels=None,
    ):
        chart = self._node_evolution_chart if layer_type == "Node" else self._link_evolution_chart
        chart.setData(
            x_hours, y_values, title=title, x_label=x_label, y_label=y_label,
            is_stepped=is_stepped, y_categorical_labels=y_categorical_labels,
        )
        self._evolution_series_cache[layer_type] = dict(
            x=x_hours, y=y_values, title=title, x_label=x_label, y_label=y_label,
            is_stepped=is_stepped, y_categorical_labels=y_categorical_labels,
        )
        if self._evolution_cursor_hours is not None:
            chart.setSyncedCursorTimeHours(self._evolution_cursor_hours)
        self._feedEvolutionPopout(layer_type)

    def clearEvolutionChart(self, layer_type=None):
        for key in (("Node", "Link") if layer_type is None else (layer_type,)):
            chart = self._node_evolution_chart if key == "Node" else self._link_evolution_chart
            chart.setData([], [], title="")
            self._evolution_series_cache.pop(key, None)
        if layer_type is None or layer_type == self._activeEvolutionLayerType():
            self._feedEvolutionPopout(self._activeEvolutionLayerType())

    def setEvolutionCursorHours(self, hours):
        self._evolution_cursor_hours = hours
        charts = [self._node_evolution_chart, self._link_evolution_chart]
        popout = getattr(self, "_evolution_popout", None)
        if popout is not None and popout.isVisible():
            charts.append(popout.chart)
        for chart in charts:
            if hours is None:
                chart.clearSyncedCursor()
            else:
                chart.setSyncedCursorTimeHours(hours)

    def setEvolutionTankToggle(self, visible, label="", tooltip=""):
        self.btEvolutionTankToggle.setVisible(bool(visible))
        if visible:
            self.btEvolutionTankToggle.setText(label or "")
            self.btEvolutionTankToggle.setToolTip(tooltip or label or "")

    def _onEvolutionTankToggleClicked(self):
        self.evolutionTankToggleRequested.emit("")

    def _toggleEvolutionPopout(self):
        popout = getattr(self, "_evolution_popout", None)
        if popout is not None and popout.isVisible():
            self._closeEvolutionPopout()
        else:
            self._openEvolutionPopout()

    def _openEvolutionPopout(self):
        active = self._activeEvolutionLayerType()
        if active is None:
            self._setEvolutionExpandButtonState(False)
            return
        if self._evolution_popout is None:
            self._evolution_popout = _EvolutionPopoutWindow(self, self._onEvolutionPopoutClosed)
        if self._evolution_popout._default_geometry is None:
            self._evolution_popout.applyDefaultGeometry()
        self._moveEvolutionControlsToPopout()
        self._setEvolutionExpandButtonState(True)
        self._evolution_popout.show()
        self._evolution_popout.raise_()
        self._evolution_popout.activateWindow()
        self._feedEvolutionPopout(active)

    def _closeEvolutionPopout(self):
        popout = getattr(self, "_evolution_popout", None)
        if popout is not None and popout.isVisible():
            popout.close()
        else:
            self._finishEvolutionPopoutClose()

    def _onEvolutionPopoutClosed(self):
        self._finishEvolutionPopoutClose()

    def _finishEvolutionPopoutClose(self):
        self._setEvolutionExpandButtonState(False)
        self._restoreEvolutionControlsToDock()

    def _onEvolutionDockVisibilityChanged(self, visible):
        if not visible:
            self._closeEvolutionPopout()

    def _setEvolutionExpandButtonState(self, expanded):
        button = getattr(self, "btEvolutionExpand", None)
        if button is None:
            return
        button.blockSignals(True)
        button.setChecked(expanded)
        button.blockSignals(False)
        button.setToolTip(
            self.tr("Collapse chart back to the panel")
            if expanded
            else self.tr("Expand chart to a floating window")
        )

    def _moveEvolutionControlsToPopout(self):
        bar = getattr(self, "_evolution_controls_bar", None)
        popout = getattr(self, "_evolution_popout", None)
        if bar is None or popout is None:
            return
        self.verticalLayout_EvolutionChart.removeWidget(bar)
        popout.attachControls(bar)
        self.evolutionChartContainer.setVisible(False)

    def _restoreEvolutionControlsToDock(self):
        bar = getattr(self, "_evolution_controls_bar", None)
        popout = getattr(self, "_evolution_popout", None)
        if bar is not None:
            if popout is not None:
                popout.detachControls(bar)
            self.verticalLayout_EvolutionChart.insertWidget(0, bar)
        self.evolutionChartContainer.setVisible(self._activeEvolutionLayerType() is not None)
        self._applySmallEvolutionVisibility()

    def _feedEvolutionPopout(self, layer_type):
        popout = getattr(self, "_evolution_popout", None)
        if popout is None or not popout.isVisible():
            return
        if layer_type is None or layer_type != self._activeEvolutionLayerType():
            return
        cached = self._evolution_series_cache.get(layer_type)
        if cached is None:
            popout.chart.setData([], [], title="")
            return
        popout.chart.setData(
            cached["x"], cached["y"], title=cached["title"], x_label=cached["x_label"],
            y_label=cached["y_label"], is_stepped=cached["is_stepped"],
            y_categorical_labels=cached["y_categorical_labels"],
        )
        popout.setWindowTitle(cached["title"] or self.tr("Evolution"))
        if self._evolution_cursor_hours is not None:
            popout.chart.setSyncedCursorTimeHours(self._evolution_cursor_hours)
