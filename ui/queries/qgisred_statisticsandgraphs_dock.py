# -*- coding: utf-8 -*-
from contextlib import suppress
import csv
import json
import math
import os
from datetime import datetime

from qgis.PyQt.QtCore import QEvent, Qt, QSize, QTimer
from qgis.PyQt.QtGui import QBrush, QColor, QIcon
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from qgis.PyQt import uic
from qgis.core import (
    QgsClassificationJenks,
    QgsClassificationPrettyBreaks,
    QgsClassificationQuantile,
    QgsExpression,
    QgsFeatureRequest,
    QgsProject,
)
from qgis.gui import QgsFilterLineEdit, QgsHighlight

from ..analysis.qgisred_results_dock import QGISRedResultsDock
from ...compat import sip
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils
from ...tools.utils.qgisred_results_all_utils import QGISRedResultsAllUtils
from ...tools.utils.qgisred_ui_utils import QGISRED_COMBO_STYLE, QGISRedUIUtils
from .qgisred_statistics_manual_breaks_dialog import QGISRedStatisticsManualBreaksDialog
from .statistics_histogram_widget import StatisticsHistogramWidget

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statisticsandgraphs_dock.ui"))


RESULTS_BRUSH_COLOR = "#FFF8DC"
DARK_BRUSH_COLOR = "#D8D8D8"
ENUM_TEXT_LIMIT = 128
DEFAULT_NUM_CLASSES = 5
CATEGORICAL_FIELD_NAMES = {
    "Material", "Type", "Status", "InstalDate", "Tag",
    "ValveType", "MeterType", "SourceType", "IniStatus", "InstDate",
}

WHITE_STYLE = (
    "QLineEdit { background-color: white; }"
    "QSpinBox, QDoubleSpinBox { background-color: white; }"
)

FIELD_TYPE_MAPPING = {
    "int": "numeric",
    "integer": "numeric",
    "integer64": "numeric",
    "double": "numeric",
    "real": "numeric",
    "long": "numeric",
    "string": "text",
    "date": "numeric",
    "datetime": "numeric",
    "time": "numeric",
    "bool": "listed",
    "boolean": "listed",
}

CONDITIONS_BY_TYPE = {
    "numeric": ["All", ">=", "<=", "=", ">", "<", "≠", "Range"],
    "listed": ["All", "="],
    "text": ["All", "=", "≠", "ILIKE", "NOT ILIKE", "LIKE", "NOT LIKE"],
}

NODE_RESULT_PROPERTIES = ["Pressure", "Head", "Demand", "Quality"]
LINK_RESULT_PROPERTIES = ["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"]
# Link results that only make sense for pipes, not pumps or valves
PIPE_ONLY_RESULT_PROPERTIES = {"Velocity", "UnitHdLoss", "FricFactor", "ReactRate"}

ELEMENT_RESULT_CATEGORY = {
    "qgisred_junctions": "Node",
    "qgisred_reservoirs": "Node",
    "qgisred_tanks": "Node",
    "qgisred_demands": "Node",
    "qgisred_sources": "Node",
    "qgisred_pipes": "Link",
    "qgisred_pumps": "Link",
    "qgisred_valves": "Link",
}

DIGITAL_TWIN_IDENTIFIERS = {"qgisred_serviceconnections", "qgisred_isolationvalves", "qgisred_meters"}

INPUT_ORDER = [
    "qgisred_junctions",
    "qgisred_tanks",
    "qgisred_reservoirs",
    "qgisred_pipes",
    "qgisred_valves",
    "qgisred_pumps",
    "qgisred_demands",
    "qgisred_sources",
]

DIGITAL_TWIN_ORDER = ["qgisred_serviceconnections", "qgisred_isolationvalves", "qgisred_meters"]

ALL_IDENTIFIERS = set(INPUT_ORDER) | set(DIGITAL_TWIN_ORDER)

CUMULATIVE_PROPERTIES = {"Length", "MinVolume", "BaseDem", "BaseDemand", "BaseValue", "Power"}


class _StatisticsHistogramPopoutWindow(QWidget):
    """Floating, resizable window showing an enlarged copy of the histogram."""

    _DEFAULT_SIZE = (760, 540)

    def __init__(self, parent, onClose):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowTitle(self.tr("QGISRed: Statistics on Properties Histogram"))
        self._onClose = onClose
        self._defaultGeometry = None
        self.setMinimumSize(360, 260)
        self.setStyleSheet("background-color: #f8f9fb;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)
        self.chart = StatisticsHistogramWidget(self)
        self.chart.showTitle = True
        self._layout.addWidget(self.chart, 1)

    def attachControls(self, controlsBar):
        self._layout.insertWidget(0, controlsBar)

    def detachControls(self, controlsBar):
        self._layout.removeWidget(controlsBar)

    def applyDefaultGeometry(self):
        width, height = self._DEFAULT_SIZE
        host = self.parent().window() if self.parent() is not None else None
        if host is not None:
            center = host.frameGeometry().center()
            self.setGeometry(center.x() - width // 2, center.y() - height // 2, width, height)
        else:
            self.resize(width, height)
        self._defaultGeometry = self.geometry()

    def closeEvent(self, event):
        callback = self._onClose
        if callback is not None:
            callback()
        super().closeEvent(event)


class QGISRedStatisticsDock(QDockWidget, formClass):
    def __init__(self, iface, parent=None):
        super(QGISRedStatisticsDock, self).__init__(parent or iface.mainWindow())
        self.setupUi(self)
        with suppress(Exception):
            self.mSecondClassGroupBox.setSaveCollapsedState(False)
            self.mFiltersGroupBox.setSaveCollapsedState(False)
        self.mSecondClassGroupBox.setCollapsed(True)
        self.mFiltersGroupBox.setCollapsed(True)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.fieldUtils = QGISRedFieldUtils()
        self.suspendCascade = False
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0
        self.manualBreaks = []
        self.secondManualBreaks = []
        self.isEnumeratedTarget = False
        self._chartBins = []
        self._chartPrettyProperty = ""
        self._chartPropertyUnit = ""
        self._chartXLabel = ""
        self._chartSubtitle = ""
        self._chartTitleBase = ""
        self._chartUseSum = False
        self._analysisContext = None
        self._breaksDirty = False
        self._lastBreaksIssue = None
        self._secondClassBins = []
        self._tableMatrix = None
        self._tableTitleBase = ""
        self._tableBaseWidths = []
        self.connectedLayerNodes = []
        self.connectedGroups = []
        self.layerTreeChangeTimer = QTimer()
        self.layerTreeChangeTimer.setSingleShot(True)
        self.layerTreeChangeTimer.setInterval(100)
        self.layerTreeChangeTimer.timeout.connect(self.doLayerTreeChanged)
        self.resultsDock = None
        self.resultsCurrentTimeText = ""
        self.resultsCurrentStat = ""
        self.resultsDockVisibilityTimer = QTimer()
        self.resultsDockVisibilityTimer.setSingleShot(True)
        self.resultsDockVisibilityTimer.setInterval(150)
        self.resultsDockVisibilityTimer.timeout.connect(self.checkResultsDockClosed)
        self.resultsDockPollTimer = QTimer()
        self.resultsDockPollTimer.setInterval(1500)
        self.resultsDockPollTimer.timeout.connect(self.pollForResultsDock)
        self.previewHighlights = []
        self.filterPreviewTimer = QTimer()
        self.filterPreviewTimer.setSingleShot(True)
        self.filterPreviewTimer.setInterval(150)
        self.filterPreviewTimer.timeout.connect(self.refreshFilterPreview)

        self.setupHistogram()
        self.setupIcons()
        self.applyWhiteStyle()
        valueLineEdit = QgsFilterLineEdit(self.cbValue)
        self.cbValue.setLineEdit(valueLineEdit)
        valueLineEdit.cleared.connect(self.onValueCleared)
        for combo in self.findChildren(QComboBox):
            QGISRedUIUtils.applyComboStyle(combo)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            combo.setMinimumContentsLength(6)
        self.setupConnections()
        self.initializeElementTypes()
        self.loadDefaults()
        self.setupProjectSignals()
        QGISRedUIUtils.applyDockStyle(self, "#388E3C")
        self.tabWidget.setStyleSheet(
            "QWidget#tabConfiguration, QWidget#tabResults { background-color: palette(window); }"
        )
        self.connectResultsDock()
        if self.resultsDock is None:
            self.resultsDockPollTimer.start()

    def closeEvent(self, event):
        self._closeHistogramPopout()
        self.filterPreviewTimer.stop()
        self.removeFilterPreviewHighlights()
        self.resultsDockVisibilityTimer.stop()
        self.disconnectResultsDock()
        self.resultsDockPollTimer.stop()
        self.safeDisconnect(self.mFiltersGroupBox.collapsedStateChanged, self.onCollapsibleGroupToggled)
        self.safeDisconnect(self.mSecondClassGroupBox.collapsedStateChanged, self.onCollapsibleGroupToggled)
        project = QgsProject.instance()
        self.safeDisconnect(project.layersAdded, self.onLayerTreeChanged)
        self.safeDisconnect(project.layersRemoved, self.onLayerTreeChanged)
        self.safeDisconnect(project.readProject, self.onProjectChanged)
        self.safeDisconnect(project.cleared, self.onProjectChanged)
        for layerNode in self.connectedLayerNodes:
            self.disconnectLayerNode(layerNode)
        self.connectedLayerNodes.clear()
        for group in self.connectedGroups:
            self.disconnectGroupSignals(group)
        self.connectedGroups.clear()
        self.layerTreeChangeTimer.stop()
        self.deleteLater()
        super().closeEvent(event)

    def safeDisconnect(self, signal, slot):
        with suppress(TypeError, RuntimeError):
            signal.disconnect(slot)

    def eventFilter(self, obj, event):
        if obj is self.tbExcel.viewport() and event.type() == QEvent.Type.Resize:
            self.stretchTableColumns()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self.stretchTableColumns)

    def setupHistogram(self):
        self.tbExcel.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbExcel.viewport().installEventFilter(self)
        self.histogram = StatisticsHistogramWidget(self.graphWidget)
        self.histogram.setToolTip(self.tr("Mouse wheel: zoom · Drag: pan · Double-click: reset view"))
        layout = QVBoxLayout(self.graphWidget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.histogram)
        self.graphWidget.setLayout(layout)
        self.labelOnlySelectedElements.hide()

        self._histogramPopout = None
        self.btHistogramExpand = QToolButton()
        self.btHistogramExpand.setIcon(QIcon(":/images/iconTsZoomWindow.svg"))
        self.btHistogramExpand.setIconSize(QSize(16, 16))
        self.btHistogramExpand.setAutoRaise(True)
        self.btHistogramExpand.setCheckable(True)
        self.btHistogramExpand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btHistogramExpand.setToolTip(self.tr("Expand histogram to a floating window"))
        self.btHistogramExpand.clicked.connect(self._toggleHistogramPopout)

        statisticIndex = self.verticalLayout_2.indexOf(self.horizontalLayoutStatistic)
        self.verticalLayout_2.removeItem(self.horizontalLayoutStatistic)
        self._statisticControlsBar = QWidget()
        barLayout = QHBoxLayout(self._statisticControlsBar)
        barLayout.setContentsMargins(6, 0, 0, 0)
        barLayout.setSpacing(8)
        barLayout.addWidget(self.labelStatistic)
        barLayout.addWidget(self.cbStatistic)
        barLayout.addWidget(self.labelSecondClassValue)
        barLayout.addWidget(self.cbSecondClassValue)
        self.labelSecondClassUnit = QLabel("")
        self.labelSecondClassUnit.hide()
        barLayout.addWidget(self.labelSecondClassUnit)
        barLayout.addStretch(1)
        barLayout.addWidget(self.btHistogramExpand)
        self.verticalLayout_2.insertWidget(statisticIndex, self._statisticControlsBar)

    def _toggleHistogramPopout(self):
        popout = getattr(self, "_histogramPopout", None)
        if popout is not None and popout.isVisible():
            self._closeHistogramPopout()
        else:
            self._openHistogramPopout()

    def _openHistogramPopout(self):
        if self._histogramPopout is None:
            self._histogramPopout = _StatisticsHistogramPopoutWindow(self, self._onHistogramPopoutClosed)
        if self._histogramPopout._defaultGeometry is None:
            self._histogramPopout.applyDefaultGeometry()
        self.graphWidget.hide()
        self._moveStatisticControlsToPopout()
        self._setHistogramExpandButtonState(True)
        self._histogramPopout.show()
        self._histogramPopout.raise_()
        self._histogramPopout.activateWindow()
        self._feedHistogramPopout()

    def _moveStatisticControlsToPopout(self):
        bar = getattr(self, "_statisticControlsBar", None)
        popout = getattr(self, "_histogramPopout", None)
        if bar is None or popout is None:
            return
        self.verticalLayout_2.removeWidget(bar)
        popout.attachControls(bar)

    def _restoreStatisticControlsToDock(self):
        bar = getattr(self, "_statisticControlsBar", None)
        if bar is None:
            return
        popout = getattr(self, "_histogramPopout", None)
        if popout is not None:
            popout.detachControls(bar)
        graphIndex = self.verticalLayout_2.indexOf(self.graphWidget)
        self.verticalLayout_2.insertWidget(graphIndex, bar)

    def _closeHistogramPopout(self):
        popout = getattr(self, "_histogramPopout", None)
        if popout is not None and popout.isVisible():
            popout.close()
        else:
            self._finishHistogramPopoutClose()

    def _onHistogramPopoutClosed(self):
        self._finishHistogramPopoutClose()

    def _finishHistogramPopoutClose(self):
        self._setHistogramExpandButtonState(False)
        self._restoreStatisticControlsToDock()
        self.graphWidget.show()

    def _setHistogramExpandButtonState(self, expanded):
        self.btHistogramExpand.blockSignals(True)
        self.btHistogramExpand.setChecked(expanded)
        self.btHistogramExpand.blockSignals(False)
        self.btHistogramExpand.setToolTip(
            self.tr("Collapse histogram back to the panel")
            if expanded
            else self.tr("Expand histogram to a floating window")
        )

    def _feedHistogramPopout(self):
        popout = getattr(self, "_histogramPopout", None)
        if popout is None or not popout.isVisible():
            return
        popout.chart.setTitles(self.histogram.title, self.histogram.subtitle)
        popout.chart.setBins(
            self.histogram.bins,
            mode="plain",
            xLabel=self.histogram.xLabel,
            yLabelLeft=self.histogram.yLabelLeft,
            statKey=self.histogram.statKey,
            valueKey=self.histogram.valueKey,
        )

    def clearChart(self):
        self.histogram.clear()
        self.cbStatistic.blockSignals(True)
        self.cbStatistic.clear()
        self.cbStatistic.blockSignals(False)
        self._chartBins = []
        self._chartTitleBase = ""
        self._analysisContext = None
        self._secondClassBins = []
        self._tableMatrix = None
        self.cbSecondClassValue.blockSignals(True)
        self.cbSecondClassValue.clear()
        self.cbSecondClassValue.blockSignals(False)
        self.labelSecondClassValue.hide()
        self.cbSecondClassValue.hide()
        self.labelSecondClassUnit.hide()
        self.cbTableStatistic.blockSignals(True)
        self.cbTableStatistic.clear()
        self.cbTableStatistic.blockSignals(False)
        self.labelTableStatistic.hide()
        self.cbTableStatistic.hide()
        self.labelResultsTime.hide()
        self._tableTitleBase = ""
        self.labelTableTitle.setText("")

    def setupIcons(self):
        self.btImport.setIcon(QIcon(":/images/iconStatisticsImport.svg"))
        self.btImport.setToolTip(self.tr("Import query configuration (.json)"))
        self.btExport.setIcon(QIcon(":/images/iconStatisticsExport.svg"))
        self.btExport.setToolTip(self.tr("Export query configuration (.json)"))
        self.btExcel.setIcon(QIcon(":/images/iconStatisticsExcel.svg"))
        self.btExcel.setToolTip(self.tr("Export table to CSV"))

    def applyWhiteStyle(self):
        for widget in (
            self.leFrom, self.leTo, self.cbClasses, self.cbSecondClasses,
            self.spinIntervalRange, self.spinSecondIntervalRange,
        ):
            widget.setStyleSheet(WHITE_STYLE)

    def setupConnections(self):
        self.cbElementType.currentIndexChanged.connect(self.onElementTypeChanged)
        self.cbElementType.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbElementType))
        self.cbProperty.currentIndexChanged.connect(self.onPropertyChanged)
        self.cbProperty.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbProperty))
        self.cbClassifiedBy.currentIndexChanged.connect(self.onClassifyByChanged)
        self.cbClassifiedBy.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbClassifiedBy))
        self.cbSecondClassifiedBy.currentIndexChanged.connect(self.onSecondClassifyByChanged)
        self.cbSecondClassifiedBy.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbSecondClassifiedBy))
        self.cbSecondRanged.currentIndexChanged.connect(self.onSecondRangedChanged)
        self.cbSecondRanged.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbSecondRanged))
        self.cbRanged.currentIndexChanged.connect(self.onRangedChanged)
        self.cbAttribute.currentIndexChanged.connect(self.onAttributeChanged)
        self.cbAttribute.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbAttribute))
        self.cbCondition.currentIndexChanged.connect(self.onConditionChanged)
        self.cbStatistic.currentIndexChanged.connect(self.onStatisticChanged)
        self.cbStatistic.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbStatistic))
        self.cbTableStatistic.currentIndexChanged.connect(self.onTableStatisticChanged)
        self.cbTableStatistic.currentIndexChanged.connect(lambda: self.updateComboBoxBackground(self.cbTableStatistic))
        self.cbSecondClassValue.currentIndexChanged.connect(self.onSecondClassValueChanged)
        self.btAnalyze.clicked.connect(self.analyze)
        self.btImport.clicked.connect(self.importConfig)
        self.btExport.clicked.connect(self.exportConfig)
        self.btExcel.clicked.connect(self.exportTableCsv)
        self.btManualBreaks.clicked.connect(self.openManualBreaksDialog)
        self.btSecondManualBreaks.clicked.connect(self.openSecondManualBreaksDialog)
        self.mFiltersGroupBox.collapsedStateChanged.connect(self.onCollapsibleGroupToggled)
        self.mSecondClassGroupBox.collapsedStateChanged.connect(self.onCollapsibleGroupToggled)
        self.chkPreview.toggled.connect(self.onFilterPreviewToggled)
        self.mFiltersGroupBox.collapsedStateChanged.connect(self.scheduleFilterPreview)
        self.cbElementType.currentIndexChanged.connect(self.scheduleFilterPreview)
        self.cbAttribute.currentIndexChanged.connect(self.scheduleFilterPreview)
        self.cbCondition.currentIndexChanged.connect(self.scheduleFilterPreview)
        self.cbValue.editTextChanged.connect(self.scheduleFilterPreview)
        self.cbValue.currentIndexChanged.connect(self.scheduleFilterPreview)
        self.leFrom.textChanged.connect(self.scheduleFilterPreview)
        self.leTo.textChanged.connect(self.scheduleFilterPreview)
        self.cbSelectedElements.toggled.connect(self.scheduleFilterPreview)

    def onCollapsibleGroupToggled(self, collapsed):
        if not collapsed:
            QTimer.singleShot(0, self.growDockForExpandedGroups)

    def growDockForExpandedGroups(self):
        # Grow the panel instead of showing a scrollbar when a section expands
        needed = self.scrollAreaWidgetContents.sizeHint().height() - self.scrollArea.viewport().height()
        if needed <= 0:
            return
        if self.isFloating():
            available = self.screen().availableGeometry().height() - self.height()
            if available > 0:
                self.resize(self.width(), self.height() + min(needed, available))
        else:
            self.iface.mainWindow().resizeDocks([self], [self.height() + needed], Qt.Orientation.Vertical)

    def setupProjectSignals(self):
        project = QgsProject.instance()
        project.layersAdded.connect(self.onLayerTreeChanged)
        project.layersRemoved.connect(self.onLayerTreeChanged)
        project.readProject.connect(self.onProjectChanged)
        project.cleared.connect(self.onProjectChanged)
        self.reconnectLayerSignals()

    def reconnectLayerSignals(self):
        for layerNode in self.connectedLayerNodes:
            self.disconnectLayerNode(layerNode)
        self.connectedLayerNodes.clear()
        for group in self.connectedGroups:
            self.disconnectGroupSignals(group)
        self.connectedGroups.clear()
        for identifier in ("qgisred_inputs", "qgisred_results"):
            for group in QGISRedLayerUtils.findGroupsByIdentifier(identifier):
                self.connectGroupSignals(group)
                for layerNode in group.findLayers():
                    self.connectLayerSignals(layerNode)

    def connectGroupSignals(self, group):
        with suppress(Exception):
            group.addedChildren.connect(self.onLayerTreeChanged)
            group.removedChildren.connect(self.onLayerTreeChanged)
            self.connectedGroups.append(group)

    def disconnectGroupSignals(self, group):
        with suppress(Exception):
            self.safeDisconnect(group.addedChildren, self.onLayerTreeChanged)
            self.safeDisconnect(group.removedChildren, self.onLayerTreeChanged)

    def connectLayerSignals(self, layerNode):
        with suppress(Exception):
            layerNode.nameChanged.connect(self.onLayerTreeChanged)
            layer = layerNode.layer()
            if layer is not None:
                layer.dataChanged.connect(self.onLayerTreeChanged)
                layer.featureAdded.connect(self.onLayerTreeChanged)
                layer.featureDeleted.connect(self.onLayerTreeChanged)
                layer.attributeValueChanged.connect(self.onLayerTreeChanged)
                layer.committedAttributeValuesChanges.connect(self.onLayerTreeChanged)
                layer.selectionChanged.connect(self.scheduleFilterPreview)
            self.connectedLayerNodes.append(layerNode)

    def disconnectLayerNode(self, layerNode):
        with suppress(Exception):
            self.safeDisconnect(layerNode.nameChanged, self.onLayerTreeChanged)
            layer = layerNode.layer()
            if layer is not None:
                self.safeDisconnect(layer.dataChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureAdded, self.onLayerTreeChanged)
                self.safeDisconnect(layer.featureDeleted, self.onLayerTreeChanged)
                self.safeDisconnect(layer.attributeValueChanged, self.onLayerTreeChanged)
                self.safeDisconnect(layer.committedAttributeValuesChanges, self.onLayerTreeChanged)
                self.safeDisconnect(layer.selectionChanged, self.scheduleFilterPreview)

    def onLayerTreeChanged(self, *args):
        self.layerTreeChangeTimer.start()

    def doLayerTreeChanged(self):
        state = self.saveCurrentQueryState()
        self.reconnectLayerSignals()
        combos = (
            self.cbElementType, self.cbProperty, self.cbClassifiedBy, self.cbSecondClassifiedBy,
            self.cbRanged, self.cbSecondRanged, self.cbAttribute, self.cbCondition, self.cbValue,
        )
        for combo in combos:
            combo.blockSignals(True)
        try:
            self.initializeElementTypes()
            self.restoreCurrentQueryState(state)
        finally:
            for combo in combos:
                combo.blockSignals(False)
        if not self.renderFromContext():
            self.clearChart()
            self._feedHistogramPopout()
            self.tbExcel.setRowCount(0)
            self.tbExcel.setColumnCount(0)
            self.labelOnlySelectedElements.hide()
        self.scheduleFilterPreview()

    def onProjectChanged(self, *args):
        self.manualBreaks = []
        self.secondManualBreaks = []
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0
        self.removeFilterPreviewHighlights()
        self.clearChart()
        self._feedHistogramPopout()
        self.tbExcel.setRowCount(0)
        self.tbExcel.setColumnCount(0)
        self.labelOnlySelectedElements.hide()
        self.onLayerTreeChanged()

    def isResultsDockAlive(self):
        return self.resultsDock is not None and not sip.isdeleted(self.resultsDock)

    def findResultsDock(self):
        for widget in self.iface.mainWindow().findChildren(QDockWidget):
            if isinstance(widget, QGISRedResultsDock) and not sip.isdeleted(widget) and widget.isVisible():
                return widget
        return None

    def pollForResultsDock(self):
        if self.resultsDock is not None:
            return
        dock = self.findResultsDock()
        if dock is not None:
            self.connectResultsDock(dock)

    def connectResultsDock(self, resultsDock=None):
        if resultsDock is None:
            resultsDock = self.findResultsDock()
        if resultsDock is None:
            return
        if self.isResultsDockAlive() and self.resultsDock is resultsDock:
            return
        if self.resultsDock is not None:
            self.disconnectResultsDock()
        self.resultsDock = resultsDock
        self.resultsDockPollTimer.stop()
        resultsDock.timeTextChanged.connect(self.onResultsTimeChanged)
        resultsDock.statisticsModeChanged.connect(self.onResultsStatisticsChanged)
        resultsDock.resultPropertyChanged.connect(self.onResultsDataChanged)
        resultsDock.simulationFinished.connect(self.onResultsDataChanged)
        resultsDock.visibilityChanged.connect(self.onResultsDockVisibilityChanged)
        if resultsDock._statsMode:
            self.onResultsStatisticsChanged(resultsDock._currentStat)
        else:
            timeText = resultsDock.lbTime.text()
            if timeText:
                self.onResultsTimeChanged(timeText)

    def disconnectResultsDock(self):
        if self.resultsDock is not None:
            if not sip.isdeleted(self.resultsDock):
                self.safeDisconnect(self.resultsDock.timeTextChanged, self.onResultsTimeChanged)
                self.safeDisconnect(self.resultsDock.statisticsModeChanged, self.onResultsStatisticsChanged)
                self.safeDisconnect(self.resultsDock.resultPropertyChanged, self.onResultsDataChanged)
                self.safeDisconnect(self.resultsDock.simulationFinished, self.onResultsDataChanged)
                self.safeDisconnect(self.resultsDock.visibilityChanged, self.onResultsDockVisibilityChanged)
            self.resultsDock = None
        self.resultsCurrentStat = ""
        self.resultsCurrentTimeText = QGISRedLayerUtils.getResultsCurrentTimeText() or self.resultsCurrentTimeText
        self.updateResultsTimeLabel()
        self.resultsDockPollTimer.start()

    def onResultsDockVisibilityChanged(self, visible):
        if not visible:
            self.resultsDockVisibilityTimer.start()
            return
        self.resultsDockVisibilityTimer.stop()
        if self.isResultsDockAlive():
            timeText = self.resultsDock.lbTime.text()
            if timeText:
                self.onResultsTimeChanged(timeText)

    def checkResultsDockClosed(self):
        if self.resultsDock is not None and (sip.isdeleted(self.resultsDock) or not self.resultsDock.isVisible()):
            self.disconnectResultsDock()

    def onResultsTimeChanged(self, timeText):
        if timeText == "NULL":
            timeText = "N/A"
        self.resultsCurrentTimeText = timeText
        self.updateResultsTimeLabel()
        self.refreshAnalysisForResults()

    def onResultsStatisticsChanged(self, statName):
        self.resultsCurrentStat = statName
        self.updateResultsTimeLabel()
        self.refreshAnalysisForResults()

    def onResultsDataChanged(self):
        self._breaksDirty = True
        self.updateResultsTimeLabel()
        self.refreshAnalysisForResults()

    def refreshAnalysisForResults(self):
        if self._analysisContext and self.analysisInvolvesResultProperty():
            self.onLayerTreeChanged()

    def analysisInvolvesResultProperty(self):
        context = self._analysisContext
        if not context:
            return False
        involvedFields = (
            context["propertyField"], context["classifyField"],
            context["secondField"], context.get("attributeField", ""),
        )
        return any(fieldName and self.isResultProperty(fieldName) for fieldName in involvedFields)

    def updateResultsTimeLabel(self):
        if not self.analysisInvolvesResultProperty():
            self.labelResultsTime.hide()
            return
        if self.resultsCurrentStat:
            text = "<b>{} {}</b>".format(self.resultsCurrentStat, self.tr("values for report times"))
        else:
            timeText = QGISRedLayerUtils.getResultsCurrentTimeText() or self.resultsCurrentTimeText
            text = "{}: <b>{}</b>".format(self.tr("Time"), timeText) if timeText else ""
        self.labelResultsTime.setText(text)
        self.labelResultsTime.setVisible(bool(text))

    def saveCurrentQueryState(self):
        return {
            "elementType": self.cbElementType.currentData(Qt.ItemDataRole.UserRole),
            "property": self.cbProperty.currentData(Qt.ItemDataRole.UserRole),
            "classifyBy": self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole),
            "ranged": self.cbRanged.currentData(Qt.ItemDataRole.UserRole),
            "classes": self.cbClasses.value(),
            "interval": self.spinIntervalRange.value(),
            "secondClassifyBy": self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole),
            "secondRanged": self.cbSecondRanged.currentData(Qt.ItemDataRole.UserRole),
            "secondClasses": self.cbSecondClasses.value(),
            "secondInterval": self.spinSecondIntervalRange.value(),
            "secondManualBreaks": list(self.secondManualBreaks),
            "attribute": self.cbAttribute.currentData(Qt.ItemDataRole.UserRole),
            "condition": self.cbCondition.currentData(Qt.ItemDataRole.UserRole),
            "valueText": self.cbValue.currentText(),
            "from": self.leFrom.text(),
            "to": self.leTo.text(),
            "onlySelected": self.cbSelectedElements.isChecked(),
            "manualBreaks": list(self.manualBreaks),
        }

    def restoreCurrentQueryState(self, state):
        self.suspendCascade = True
        elementIndex = self.cbElementType.findData(state.get("elementType")) if state.get("elementType") else -1
        if elementIndex >= 0:
            self.cbElementType.setCurrentIndex(elementIndex)
        self.suspendCascade = False
        self.updateProperties()
        self.updateClassifyBy()
        self.updateSecondClassifyBy()
        self.updateAttributes()

        propertyIndex = self.cbProperty.findData(state.get("property")) if state.get("property") else -1
        if propertyIndex >= 0:
            self.cbProperty.setCurrentIndex(propertyIndex)
        classifyValue = state.get("classifyBy")
        classifyIndex = self.cbClassifiedBy.findData(classifyValue) if classifyValue is not None else -1
        if classifyIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(classifyIndex)
            self.updateRanged()
        rangedIndex = self.cbRanged.findData(state.get("ranged")) if state.get("ranged") else -1
        if rangedIndex >= 0:
            self.cbRanged.setCurrentIndex(rangedIndex)
        classes = state.get("classes")
        if classes:
            self.cbClasses.setValue(int(classes))
        interval = state.get("interval")
        if interval is not None:
            with suppress(TypeError, ValueError):
                self.spinIntervalRange.setValue(float(interval))
        secondValue = state.get("secondClassifyBy")
        secondIndex = self.cbSecondClassifiedBy.findData(secondValue) if secondValue else -1
        if secondIndex >= 0:
            self.cbSecondClassifiedBy.setCurrentIndex(secondIndex)
            self.updateSecondRanged()
        secondRangedIndex = self.cbSecondRanged.findData(state.get("secondRanged")) if state.get("secondRanged") else -1
        if secondRangedIndex >= 0:
            self.cbSecondRanged.setCurrentIndex(secondRangedIndex)
        secondClasses = state.get("secondClasses")
        if secondClasses:
            self.cbSecondClasses.setValue(int(secondClasses))
        secondInterval = state.get("secondInterval")
        if secondInterval is not None:
            with suppress(TypeError, ValueError):
                self.spinSecondIntervalRange.setValue(float(secondInterval))
        self.secondManualBreaks = list(state.get("secondManualBreaks") or [])
        attributeIndex = self.cbAttribute.findData(state.get("attribute") or "")
        if attributeIndex >= 0:
            self.cbAttribute.setCurrentIndex(attributeIndex)
        self.updateConditions()
        conditionIndex = self.cbCondition.findData(state.get("condition")) if state.get("condition") else -1
        if conditionIndex >= 0:
            self.cbCondition.setCurrentIndex(conditionIndex)
        self.updateValueWidget()
        valueText = state.get("valueText")
        if valueText:
            valueIndex = self.cbValue.findText(valueText)
            if valueIndex >= 0:
                self.cbValue.setCurrentIndex(valueIndex)
            else:
                self.cbValue.setEditText(valueText)
        self.leFrom.setText(state.get("from") or "")
        self.leTo.setText(state.get("to") or "")
        self.cbSelectedElements.setChecked(bool(state.get("onlySelected")))
        self.manualBreaks = list(state.get("manualBreaks") or [])
        for combo in (self.cbElementType, self.cbProperty, self.cbClassifiedBy, self.cbRanged,
                      self.cbSecondClassifiedBy, self.cbSecondRanged,
                      self.cbAttribute, self.cbCondition):
            self.updateComboBoxBackground(combo)
        self.onRangedChanged()
        if self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole):
            self.onSecondRangedChanged()

    def updateComboBoxBackground(self, combo):
        # Do not apply to cbValue: its stylesheet is owned by setValueComboPlain
        brush = combo.currentData(Qt.ItemDataRole.BackgroundRole)
        if brush and isinstance(brush, QBrush) and brush.color() != QColor(0, 0, 0, 255):
            color = brush.color().name()
        else:
            color = "white"
        combo.setStyleSheet(QGISRED_COMBO_STYLE + "QComboBox { background-color: %s; }" % color)

    def initializeElementTypes(self):
        self.suspendCascade = True
        self.cbElementType.clear()

        availableLayers = {}
        for layer in QGISRedLayerUtils.getLayersByGroupIdentifier("qgisred_inputs"):
            ident = layer.customProperty("qgisred_identifier")
            if ident in ALL_IDENTIFIERS and ident not in availableLayers:
                availableLayers[ident] = layer.name()
        if not availableLayers:
            # No usable Inputs group: identifiers still live on the layers themselves
            for layer in QgsProject.instance().mapLayers().values():
                ident = layer.customProperty("qgisred_identifier")
                if ident in ALL_IDENTIFIERS and ident not in availableLayers:
                    availableLayers[ident] = layer.name()

        nodeIdent = linkIdent = None
        for layer in QGISRedLayerUtils.getLayersByGroupIdentifier("qgisred_results"):
            ident = layer.customProperty("qgisred_identifier") or ""
            if ident.startswith("qgisred_node") and nodeIdent is None:
                nodeIdent = ident
            elif ident.startswith("qgisred_link") and linkIdent is None:
                linkIdent = ident

        hasResults = nodeIdent or linkIdent
        if hasResults:
            resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
            if nodeIdent:
                self.cbElementType.addItem(self.tr("Nodes"), nodeIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            if linkIdent:
                self.cbElementType.addItem(self.tr("Links"), linkIdent)
                self.cbElementType.setItemData(self.cbElementType.count() - 1, resultsBrush, Qt.ItemDataRole.BackgroundRole)
            self.cbElementType.insertSeparator(self.cbElementType.count())

        addedInput = False
        for ident in INPUT_ORDER:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)
                addedInput = True

        hasTwin = any(ident in availableLayers for ident in DIGITAL_TWIN_ORDER)
        if addedInput and hasTwin:
            self.cbElementType.insertSeparator(self.cbElementType.count())
        for ident in DIGITAL_TWIN_ORDER:
            if ident in availableLayers:
                self.cbElementType.addItem(availableLayers[ident], ident)
        self.suspendCascade = False

    def loadDefaults(self):
        defaultIndex = self.cbElementType.findData("qgisred_pipes")
        if defaultIndex >= 0:
            self.cbElementType.setCurrentIndex(defaultIndex)
        self.onElementTypeChanged()

    def isResultsLayer(self, layer):
        if not layer:
            return False
        ident = layer.customProperty("qgisred_identifier") or ""
        return ident.startswith("qgisred_node") or ident.startswith("qgisred_link")

    def isResultsIdentifier(self, ident):
        return bool(ident) and (ident.startswith("qgisred_node") or ident.startswith("qgisred_link"))

    def getResultsExist(self):
        return bool(QGISRedLayerUtils.getLayersByGroupIdentifier("qgisred_results"))

    def resolveLayer(self):
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        if not elementIdentifier:
            return None
        for layer in QgsProject.instance().mapLayers().values():
            if layer.customProperty("qgisred_identifier") == elementIdentifier:
                return layer
        return None

    def resolveResultsLayer(self, category):
        prefix = "qgisred_node" if category == "Node" else "qgisred_link"
        for layer in QGISRedLayerUtils.getLayersByGroupIdentifier("qgisred_results"):
            ident = layer.customProperty("qgisred_identifier") or ""
            if ident.startswith(prefix):
                return layer
        return None

    def onElementTypeChanged(self):
        if self.suspendCascade:
            return
        self.manualBreaks = []
        self.secondManualBreaks = []
        self.clearChart()
        self._feedHistogramPopout()
        self.tbExcel.setRowCount(0)
        self.tbExcel.setColumnCount(0)
        self.labelOnlySelectedElements.hide()
        self.updateProperties()
        self.updateClassifyBy()
        self.updateSecondClassifyBy()
        self.updateAttributes()

    def onPropertyChanged(self):
        if self.suspendCascade:
            return
        propertyField = self.cbProperty.currentData(Qt.ItemDataRole.UserRole)
        index = self.cbClassifiedBy.findData(propertyField) if propertyField else -1
        if index >= 0:
            self.cbClassifiedBy.setCurrentIndex(index)
        else:
            self.selectFirstUsable(self.cbClassifiedBy)

    def onClassifyByChanged(self):
        if self.suspendCascade:
            return
        self.manualBreaks = []
        self.updateRanged()

    def onSecondClassifyByChanged(self):
        if self.suspendCascade:
            return
        self.secondManualBreaks = []
        self.updateSecondRanged()

    def onRangedChanged(self):
        if self.suspendCascade:
            return
        if not self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole):
            return
        rangedId = self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or ""
        isFixedInterval = rangedId == "FixedInterval"
        isManual = rangedId == "Manual"
        isCategories = rangedId == "Categorized"
        self.cbClasses.setVisible(not isFixedInterval)
        self.labelClasses.setVisible(not isFixedInterval)
        self.spinIntervalRange.setVisible(isFixedInterval)
        self.labelIntervalRange.setVisible(isFixedInterval)
        self.btManualBreaks.setVisible(isManual)
        self.cbClasses.setEnabled(not isCategories)
        if isCategories:
            classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
            layer = self.resolveLayerForClassifyField(classifyField)
            if layer is not None and classifyField:
                distinctCount = len(self.collectUniqueValues(layer, classifyField, limit=10000))
                if distinctCount > 0:
                    self.cbClasses.blockSignals(True)
                    self.cbClasses.setMinimum(1)
                    self.cbClasses.setMaximum(max(distinctCount, 1))
                    self.cbClasses.setValue(distinctCount)
                    self.cbClasses.blockSignals(False)
        else:
            self.cbClasses.setMinimum(2)
            self.cbClasses.setMaximum(50)

    def onSecondRangedChanged(self):
        if self.suspendCascade:
            return
        rangedId = self.cbSecondRanged.currentData(Qt.ItemDataRole.UserRole) or ""
        isFixedInterval = rangedId == "FixedInterval"
        isManual = rangedId == "Manual"
        isCategories = rangedId == "Categorized"
        self.cbSecondClasses.setVisible(not isFixedInterval)
        self.labelSecondClasses.setVisible(not isFixedInterval)
        self.spinSecondIntervalRange.setVisible(isFixedInterval)
        self.labelSecondIntervalRange.setVisible(isFixedInterval)
        self.btSecondManualBreaks.setVisible(isManual)
        self.cbSecondClasses.setEnabled(not isCategories)
        if isCategories:
            classifyField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
            layer = self.resolveLayerForClassifyField(classifyField)
            if layer is not None and classifyField:
                distinctCount = len(self.collectUniqueValues(layer, classifyField, limit=10000))
                if distinctCount > 0:
                    self.cbSecondClasses.blockSignals(True)
                    self.cbSecondClasses.setMinimum(1)
                    self.cbSecondClasses.setMaximum(max(distinctCount, 1))
                    self.cbSecondClasses.setValue(distinctCount)
                    self.cbSecondClasses.blockSignals(False)
        else:
            self.cbSecondClasses.setMinimum(2)
            self.cbSecondClasses.setMaximum(50)

    def onAttributeChanged(self):
        if self.suspendCascade:
            return
        self.updateConditions()

    def onConditionChanged(self):
        if self.suspendCascade:
            return
        self.updateValueWidget()

    def isIdentifierField(self, elementIdentifier, fieldName):
        # Per-layer identifier fields (PipeID, TankID, ...) are detected via the CSV Identifier property
        return self.fieldUtils.getProperty(normalize_element(elementIdentifier or ""), fieldName, translate=False) == "Identifier"

    def updateProperties(self):
        self.suspendCascade = True
        self.cbProperty.clear()
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbProperty)
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q", "type", "nodetype", "linktype"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        skipLower = {"id"} if elementIdentifier == "qgisred_demands" else {"id", "descrip", "description"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        tagField = None
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if lower in skipLower or self.isIdentifierField(elementIdentifier, fieldName):
                continue
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            cat = FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
            isEnum = fieldName in CATEGORICAL_FIELD_NAMES
            if not (cat in ("numeric", "text", "listed") or isEnum):
                continue
            if lower == "tag":
                tagField = field
            else:
                staticFields.append(field)

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop != "Quality"]
        if qualityModel in ("NONE", "AGE", "TRACE"):
            resultProps = [prop for prop in resultProps if prop != "ReactRate"]

        if not isResultsMode:
            for field in staticFields:
                self.addPropertyItem(self.cbProperty, elementIdentifier, field.name())
            if tagField is not None:
                self.addPropertyItem(self.cbProperty, elementIdentifier, tagField.name(), darkBrush)
            if resultProps:
                if self.cbProperty.count() > 0:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
                resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
                for prop in resultProps:
                    self.addResultPropertyItem(self.cbProperty, resultCategory, prop, resultsBrush)
        else:
            if tagField is not None:
                self.addPropertyItem(self.cbProperty, elementIdentifier, tagField.name(), darkBrush)
                if resultProps or staticFields:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
            for field in staticFields:
                self.addPropertyItem(self.cbProperty, elementIdentifier, field.name())
            if resultProps:
                if self.cbProperty.count() > 0:
                    self.cbProperty.insertSeparator(self.cbProperty.count())
                resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
                for prop in resultProps:
                    self.addResultPropertyItem(self.cbProperty, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        self.selectFirstUsable(self.cbProperty)
        self.updateComboBoxBackground(self.cbProperty)

    def updateClassifyBy(self):
        self.suspendCascade = True
        self.cbClassifiedBy.clear()
        self.cbClassifiedBy.addItem(self.tr("None"), "")
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbClassifiedBy)
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q", "type", "nodetype", "linktype"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        skipLower = {"id"} if elementIdentifier == "qgisred_demands" else {"id", "descrip", "description"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        tagField = None
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if lower in skipLower or self.isIdentifierField(elementIdentifier, fieldName):
                continue
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            cat = FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
            isEnum = fieldName in CATEGORICAL_FIELD_NAMES
            if not (cat in ("numeric", "text", "listed") or isEnum):
                continue
            if lower == "tag":
                tagField = field
            else:
                staticFields.append(field)

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop != "Quality"]
        if qualityModel in ("NONE", "AGE", "TRACE"):
            resultProps = [prop for prop in resultProps if prop != "ReactRate"]

        for field in staticFields:
            self.addPropertyItem(self.cbClassifiedBy, elementIdentifier, field.name())
        if tagField is not None:
            self.addPropertyItem(self.cbClassifiedBy, elementIdentifier, tagField.name(), darkBrush)
        if resultProps:
            if self.cbClassifiedBy.count() > 0:
                self.cbClassifiedBy.insertSeparator(self.cbClassifiedBy.count())
            resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
            for prop in resultProps:
                self.addResultPropertyItem(self.cbClassifiedBy, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        propertyField = self.cbProperty.currentData(Qt.ItemDataRole.UserRole)
        defaultIndex = self.cbClassifiedBy.findData(propertyField) if propertyField else -1
        if defaultIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(defaultIndex)
        else:
            self.selectFirstUsable(self.cbClassifiedBy)
        self.updateComboBoxBackground(self.cbClassifiedBy)
        self.updateRanged()

    def updateSecondClassifyBy(self):
        self.suspendCascade = True
        self.cbSecondClassifiedBy.clear()
        self.cbSecondClassifiedBy.addItem(self.tr("None"), "")
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbSecondClassifiedBy)
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q", "type", "nodetype", "linktype"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        skipLower = {"id"} if elementIdentifier == "qgisred_demands" else {"id", "descrip", "description"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        tagField = None
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if lower in skipLower or self.isIdentifierField(elementIdentifier, fieldName):
                continue
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            cat = FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
            isEnum = fieldName in CATEGORICAL_FIELD_NAMES
            if not (cat in ("numeric", "text", "listed") or isEnum):
                continue
            if lower == "tag":
                tagField = field
            else:
                staticFields.append(field)

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop != "Quality"]
        if qualityModel in ("NONE", "AGE", "TRACE"):
            resultProps = [prop for prop in resultProps if prop != "ReactRate"]

        for field in staticFields:
            self.addPropertyItem(self.cbSecondClassifiedBy, elementIdentifier, field.name())
        if tagField is not None:
            self.addPropertyItem(self.cbSecondClassifiedBy, elementIdentifier, tagField.name(), darkBrush)
        if resultProps:
            self.cbSecondClassifiedBy.insertSeparator(self.cbSecondClassifiedBy.count())
            resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
            for prop in resultProps:
                self.addResultPropertyItem(self.cbSecondClassifiedBy, resultCategory, prop, resultsBrush)

        self.cbSecondClassifiedBy.setCurrentIndex(0)
        self.suspendCascade = False
        self.updateComboBoxBackground(self.cbSecondClassifiedBy)
        self.updateSecondRanged()

    def updateSecondRanged(self):
        self.suspendCascade = True
        self.cbSecondRanged.clear()
        classifyField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        hasField = bool(classifyField)
        self.labelSecondRanged.setVisible(hasField)
        self.cbSecondRanged.setVisible(hasField)
        if not hasField:
            self.labelSecondClasses.setVisible(False)
            self.cbSecondClasses.setVisible(False)
            self.labelSecondIntervalRange.setVisible(False)
            self.spinSecondIntervalRange.setVisible(False)
            self.btSecondManualBreaks.setVisible(False)
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbSecondRanged)
            return
        if self.isCategoricalClassifier(classifyField):
            self.cbSecondRanged.addItem(self.tr("Categories"), "Categorized")
        else:
            for identifier, label in (
                ("Categorized", self.tr("Categories")),
                ("EqualInterval", self.tr("Equal Interval")),
                ("FixedInterval", self.tr("Fixed Interval")),
                ("Quantile", self.tr("Equal Count")),
                ("Jenks", self.tr("Natural Breaks")),
                ("Pretty", self.tr("Pretty Breaks")),
                ("Manual", self.tr("Manual")),
            ):
                self.cbSecondRanged.addItem(label, identifier)
            defaultIndex = self.cbSecondRanged.findData("Pretty")
            if defaultIndex >= 0:
                self.cbSecondRanged.setCurrentIndex(defaultIndex)
        self.cbSecondClasses.blockSignals(True)
        self.cbSecondClasses.setMinimum(2)
        self.cbSecondClasses.setMaximum(50)
        if self.cbSecondClasses.value() < 2:
            self.cbSecondClasses.setValue(DEFAULT_NUM_CLASSES)
        self.cbSecondClasses.blockSignals(False)
        self.suspendCascade = False
        self.onSecondRangedChanged()
        self.updateComboBoxBackground(self.cbSecondRanged)

    def updateRanged(self):
        self.suspendCascade = True
        self.cbRanged.clear()
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        hasField = bool(classifyField)
        self.labelRanged.setVisible(hasField)
        self.cbRanged.setVisible(hasField)
        self.mSecondClassGroupBox.setEnabled(hasField)
        if not hasField:
            self.labelClasses.setVisible(False)
            self.cbClasses.setVisible(False)
            self.labelIntervalRange.setVisible(False)
            self.spinIntervalRange.setVisible(False)
            self.btManualBreaks.setVisible(False)
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbRanged)
            return
        if self.isCategoricalClassifier(classifyField):
            self.cbRanged.addItem(self.tr("Categories"), "Categorized")
        else:
            for identifier, label in (
                ("Categorized", self.tr("Categories")),
                ("EqualInterval", self.tr("Equal Interval")),
                ("FixedInterval", self.tr("Fixed Interval")),
                ("Quantile", self.tr("Equal Count")),
                ("Jenks", self.tr("Natural Breaks")),
                ("Pretty", self.tr("Pretty Breaks")),
                ("Manual", self.tr("Manual")),
            ):
                self.cbRanged.addItem(label, identifier)
            defaultIndex = self.cbRanged.findData("Pretty")
            if defaultIndex >= 0:
                self.cbRanged.setCurrentIndex(defaultIndex)
        self.cbClasses.blockSignals(True)
        self.cbClasses.setMinimum(2)
        self.cbClasses.setMaximum(50)
        if self.cbClasses.value() < 2:
            self.cbClasses.setValue(DEFAULT_NUM_CLASSES)
        self.cbClasses.blockSignals(False)
        self.suspendCascade = False
        self.onRangedChanged()

    def updateAttributes(self):
        self.suspendCascade = True
        self.cbAttribute.clear()
        self.cbAttribute.addItem(self.tr("No Filter"), "")
        layer = self.resolveLayer()
        if layer is None:
            self.suspendCascade = False
            self.updateComboBoxBackground(self.cbAttribute)
            self.updateConditions()
            return
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        isResultsMode = self.isResultsLayer(layer)
        resultsBrush = QBrush(QColor(RESULTS_BRUSH_COLOR))
        darkBrush = QBrush(QColor(DARK_BRUSH_COLOR))

        resultsMetaLower = {"time", "statistics", "time_h", "time_d", "time_q", "type", "nodetype", "linktype"}
        resultsFieldsLower = {
            "flow", "flow_unsig", "flow_sig", "velocity", "headloss",
            "unithdloss", "fricfactor", "reactrate", "quality",
            "pressure", "head", "demand", "status",
        }
        idTagLower = {"id", "tag", "descrip"}

        qualityModel = QGISRedProjectUtils.getQualityModel().upper()
        nonChemicalFields = set()
        if qualityModel in ("NONE", "AGE", "TRACE"):
            nonChemicalFields = {
                "qgisred_pipes": {"bulkcoeff", "wallcoeff"},
                "qgisred_tanks": {"reactcoef", "iniquality"},
                "qgisred_reservoirs": {"iniquality"},
                "qgisred_junctions": {"iniquality"},
            }.get(elementIdentifier, set())

        idTagFieldsByKey = {}
        identifierFields = []
        staticFields = []
        for field in layer.fields():
            fieldName = field.name()
            lower = fieldName.lower()
            if isResultsMode and lower in resultsMetaLower:
                continue
            if isResultsMode and lower in resultsFieldsLower:
                continue
            if lower in nonChemicalFields:
                continue
            if lower in idTagLower:
                idTagFieldsByKey[lower] = field
            elif self.isIdentifierField(elementIdentifier, fieldName):
                identifierFields.append(field)
            else:
                staticFields.append(field)

        idTagFields = [idTagFieldsByKey[k] for k in ("id", "tag", "descrip") if k in idTagFieldsByKey]
        insertAt = 1 if "id" in idTagFieldsByKey else 0
        idTagFields[insertAt:insertAt] = identifierFields
        for field in idTagFields:
            self.addPropertyItem(self.cbAttribute, elementIdentifier, field.name(), darkBrush)
        if staticFields and idTagFields:
            self.cbAttribute.insertSeparator(self.cbAttribute.count())
        for field in staticFields:
            self.addPropertyItem(self.cbAttribute, elementIdentifier, field.name())

        resultProps = self.getResultProperties(layer, elementIdentifier)
        if qualityModel == "NONE":
            resultProps = [prop for prop in resultProps if prop != "Quality"]
        if qualityModel in ("NONE", "AGE", "TRACE"):
            resultProps = [prop for prop in resultProps if prop != "ReactRate"]
        if resultProps:
            self.cbAttribute.insertSeparator(self.cbAttribute.count())
            resultCategory = self.resultCategoryFor(elementIdentifier, isResultsMode, layer)
            for prop in resultProps:
                self.addResultPropertyItem(self.cbAttribute, resultCategory, prop, resultsBrush)

        self.suspendCascade = False
        self.updateComboBoxBackground(self.cbAttribute)
        self.updateConditions()

    def updateConditions(self):
        self.suspendCascade = True
        self.cbCondition.clear()
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        hasAttribute = bool(attributeField)
        self.cbCondition.setVisible(hasAttribute)
        self.labelCondition.setVisible(hasAttribute)
        self.valueStack.setVisible(hasAttribute)
        self.labelValue.setVisible(hasAttribute)
        self.labelAttribute.setVisible(hasAttribute)
        if not hasAttribute:
            self.suspendCascade = False
            return
        cat = self.classifyAttributeType(attributeField)
        for option in CONDITIONS_BY_TYPE.get(cat, CONDITIONS_BY_TYPE["text"]):
            self.cbCondition.addItem(option, option)
        if cat == "numeric":
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        elif cat == "listed":
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        else:
            self.cbCondition.setCurrentIndex(self.cbCondition.findData("="))
        self.suspendCascade = False
        self.updateValueWidget()

    def setValueComboPlain(self, plain):
        # Numeric fields take free-typed values, so the empty dropdown is just noise
        if getattr(self, "_valueComboPlain", None) == plain:
            return
        self._valueComboPlain = plain
        style = QGISRED_COMBO_STYLE
        if plain:
            style += "QComboBox::drop-down { width: 0px; border: none; } QComboBox::down-arrow { image: none; width: 0px; }"
        self.cbValue.setStyleSheet(style)

    def updateValueWidget(self):
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if not attributeField:
            return
        cat = self.classifyAttributeType(attributeField)
        self.setValueComboPlain(cat == "numeric")
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        if condition == "All":
            self.valueStack.setCurrentIndex(0)
            self.cbValue.clear()
            return
        if condition == "Range":
            self.valueStack.setCurrentIndex(1)
            return
        self.valueStack.setCurrentIndex(0)
        layer = self.resolveAttributeLayer(attributeField)
        self.cbValue.clear()
        if layer is None:
            return
        if condition in ("=", "≠") and cat in ("listed", "text"):
            uniqueValues = self.collectUniqueValues(layer, attributeField, limit=500)
            self.cbValue.addItem("", "")
            for value in uniqueValues:
                self.cbValue.addItem(str(value), value)
        elif cat == "listed":
            uniqueValues = self.collectUniqueValues(layer, attributeField, limit=500)
            self.cbValue.addItem("", "")
            for value in uniqueValues:
                self.cbValue.addItem(str(value), value)

    def onValueCleared(self):
        # The X button empties the text; the selection must go too or currentData keeps filtering
        self.cbValue.blockSignals(True)
        self.cbValue.setCurrentIndex(-1)
        self.cbValue.clearEditText()
        self.cbValue.blockSignals(False)
        self.scheduleFilterPreview()

    def scheduleFilterPreview(self):
        self.filterPreviewTimer.start()

    def onFilterPreviewToggled(self, checked):
        if checked:
            self.refreshFilterPreview()
        else:
            self.removeFilterPreviewHighlights()

    def refreshFilterPreview(self):
        if self.mFiltersGroupBox.isCollapsed():
            self.removeFilterPreviewHighlights()
            return
        features = self.computeFilterMatchFeatures()
        if features is None:
            features = []
        self.lblMatchCount.setText(self.tr("%d elements match") % len(features))
        self.removeFilterPreviewHighlights()
        if not self.chkPreview.isChecked() or not features:
            return
        layer = self.resolveLayer()
        if layer is None:
            return
        for feature in features:
            geom = feature.geometry()
            if geom is None or geom.isEmpty():
                continue
            highlight = QgsHighlight(self.canvas, geom, layer)
            highlight.setColor(QColor(255, 140, 0))
            highlight.setWidth(3)
            highlight.show()
            self.previewHighlights.append(highlight)

    def computeFilterMatchFeatures(self):
        # Features passing the Filters section (attribute condition + only selected); None = not evaluable
        layer = self.resolveLayer()
        if layer is None:
            return None
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) if condition not in ("", "All") else ""
        layers = self.resolveAnalysisLayers("", "", "", attributeField, quiet=True)
        if layers is None:
            return None
        request = QgsFeatureRequest()
        if self.cbSelectedElements.isChecked():
            selectedIds = layer.selectedFeatureIds()
            if not selectedIds:
                return []
            request.setFilterFids(list(selectedIds))
        expression = self.buildAttributeExpression(layer, quiet=True)
        if expression is False:
            return None
        if expression:
            request.combineFilterExpression(expression)
        filterIds = self.computeJoinFilterIds(layers, attributeField, quiet=True)
        if filterIds is False:
            return None
        baseIdField = layers["baseIdField"]
        features = []
        for feature in layer.getFeatures(request):
            if filterIds is not None and str(feature[baseIdField]) not in filterIds:
                continue
            features.append(feature)
        return features

    def removeFilterPreviewHighlights(self):
        if not self.previewHighlights:
            return
        scene = self.canvas.scene() if self.canvas is not None else None
        for highlight in self.previewHighlights:
            with suppress(Exception):
                highlight.hide()
            if scene is not None:
                with suppress(Exception):
                    scene.removeItem(highlight)
        self.previewHighlights = []
        if self.canvas is not None:
            with suppress(Exception):
                self.canvas.refresh()

    def addPropertyItem(self, combo, elementIdentifier, fieldName, brush=None):
        prettyName = self.fieldUtils.getProperty(normalize_element(elementIdentifier), fieldName) or fieldName
        unit = self.fieldUtils.getUnitAbbreviation(normalize_element(elementIdentifier), fieldName) or ""
        label = "{} ({})".format(prettyName, unit) if unit else prettyName
        combo.addItem(label, fieldName)
        idx = combo.count() - 1
        if brush:
            combo.setItemData(idx, brush, Qt.ItemDataRole.BackgroundRole)

    def addResultPropertyItem(self, combo, resultCategory, prop, brush):
        prettyName = self.fieldUtils.getProperty(normalize_element(resultCategory), prop) or prop
        unit = self.fieldUtils.getUnitAbbreviation(normalize_element(resultCategory), prop) if resultCategory else ""
        label = "{} ({})".format(prettyName, unit) if unit else prettyName
        combo.addItem(label, prop)
        idx = combo.count() - 1
        combo.setItemData(idx, brush, Qt.ItemDataRole.BackgroundRole)

    def selectFirstUsable(self, combo):
        for i in range(combo.count()):
            if combo.itemData(i, Qt.ItemDataRole.UserRole):
                combo.setCurrentIndex(i)
                return
        if combo.count() > 0:
            combo.setCurrentIndex(0)

    def getResultProperties(self, layer, elementIdentifier):
        if self.isResultsLayer(layer):
            ident = layer.customProperty("qgisred_identifier") or ""
            return list(LINK_RESULT_PROPERTIES) if ident.startswith("qgisred_link") else list(NODE_RESULT_PROPERTIES)
        if elementIdentifier in DIGITAL_TWIN_IDENTIFIERS or not self.getResultsExist():
            return []
        category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
        if category == "Link":
            if elementIdentifier in ("qgisred_pumps", "qgisred_valves"):
                return [prop for prop in LINK_RESULT_PROPERTIES if prop not in PIPE_ONLY_RESULT_PROPERTIES]
            return list(LINK_RESULT_PROPERTIES)
        if category == "Node":
            return list(NODE_RESULT_PROPERTIES)
        return []

    def resultCategoryFor(self, elementIdentifier, isResultsMode, layer):
        if isResultsMode:
            ident = layer.customProperty("qgisred_identifier") or ""
            return "Links" if ident.startswith("qgisred_link") else "Nodes"
        cat = ELEMENT_RESULT_CATEGORY.get(elementIdentifier, "")
        return "Links" if cat == "Link" else "Nodes"

    def classifyAttributeType(self, fieldName):
        if not fieldName:
            return "text"
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return "listed"
        layer = self.resolveAttributeLayer(fieldName)
        if layer is None:
            if self.isResultProperty(fieldName):
                return "numeric" if fieldName != "Status" else "listed"
            return "text"
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx >= 0:
            field = layer.fields().field(fieldIdx)
            return FIELD_TYPE_MAPPING.get(field.typeName().lower(), "text")
        if self.isResultProperty(fieldName):
            return "numeric" if fieldName != "Status" else "listed"
        return "text"

    def isResultProperty(self, prop):
        return prop in NODE_RESULT_PROPERTIES or prop in LINK_RESULT_PROPERTIES

    def elementForField(self, elementIdentifier, fieldName):
        if self.isResultProperty(fieldName):
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category is None:
                category = "Link" if (elementIdentifier or "").startswith("qgisred_link") else "Node"
            return "Links" if category == "Link" else "Nodes"
        return normalize_element(elementIdentifier)

    def resultPropertyQualifier(self, elementIdentifier, fieldName):
        # Singular element name used to qualify a dynamic property in titles
        # (e.g. Pumps + Flow -> "Pump Flows") when a concrete element type is
        # selected instead of the generic Nodes/Links results layers.
        if not self.isResultProperty(fieldName) or self.isResultsIdentifier(elementIdentifier):
            return ""
        singulars = {
            "qgisred_pipes": self.tr("Pipe"),
            "qgisred_pumps": self.tr("Pump"),
            "qgisred_valves": self.tr("Valve"),
            "qgisred_junctions": self.tr("Junction"),
            "qgisred_reservoirs": self.tr("Reservoir"),
            "qgisred_tanks": self.tr("Tank"),
            "qgisred_demands": self.tr("Multiple Demand"),
            "qgisred_sources": self.tr("Source"),
        }
        return singulars.get(elementIdentifier, "")

    def isCategoricalClassifier(self, fieldName):
        if not fieldName:
            return False
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return True
        layer = self.resolveLayerForClassifyField(fieldName)
        if layer is None:
            return False
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            return False
        cat = FIELD_TYPE_MAPPING.get(layer.fields().field(fieldIdx).typeName().lower(), "text")
        return cat in ("text", "listed")

    def resolveLayerForClassifyField(self, fieldName):
        layer = self.resolveLayer()
        if layer is None or not fieldName:
            return layer
        if layer.fields().indexFromName(fieldName) >= 0:
            return layer
        if self.isResultProperty(fieldName):
            elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category:
                resultsLayer = self.resolveResultsLayer(category)
                if resultsLayer is not None:
                    return resultsLayer
        return layer

    def resolveAttributeLayer(self, fieldName):
        return self.resolveLayerForClassifyField(fieldName)

    def collectUniqueValues(self, layer, fieldName, limit=200, request=None, idSet=None):
        if layer.fields().indexFromName(fieldName) < 0:
            return []
        idFieldName = self.fieldUtils.getIdFieldName(layer) if idSet is not None else ""
        values = set()
        featureIterator = layer.getFeatures(request) if request is not None else layer.getFeatures()
        for feature in featureIterator:
            if idSet is not None and str(feature[idFieldName]) not in idSet:
                continue
            value = self.fieldValue(feature, fieldName)
            if value is None:
                continue
            values.add(value)
            if len(values) >= limit:
                break
        try:
            return sorted(values)
        except TypeError:
            return sorted(values, key=lambda item: str(item))

    def collectNumericValues(self, layer, fieldName, request=None, idSet=None):
        values = []
        if layer.fields().indexFromName(fieldName) < 0:
            return values
        idFieldName = self.fieldUtils.getIdFieldName(layer) if idSet is not None else ""
        featureIterator = layer.getFeatures(request) if request is not None else layer.getFeatures()
        for feature in featureIterator:
            if idSet is not None and str(feature[idFieldName]) not in idSet:
                continue
            raw = self.fieldValue(feature, fieldName)
            if raw is None:
                continue
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
        values.sort()
        return values

    def numericValuesIssue(self, values):
        # Sorted numeric list used for breaks; None | "empty" | "equal".
        # All-zero counts as empty: zeroed result fields mean no usable data.
        if not values:
            return "empty"
        if values[0] == values[-1]:
            return "empty" if values[0] == 0 else "equal"
        return None

    def breaksIssueSentence(self, elementIdentifier, field, issue):
        pretty = self.fieldUtils.getProperty(self.elementForField(elementIdentifier, field), field) or field
        if issue == "empty":
            return self.tr("Field %s has no values.") % pretty
        return self.tr("Field %s has only equal values.") % pretty

    def showBreaksIssues(self, elementIdentifier, classifyField, firstIssue, secondField, secondIssue):
        sentences = []
        if firstIssue:
            sentences.append(self.breaksIssueSentence(elementIdentifier, classifyField, firstIssue))
        if secondIssue:
            sentences.append(self.breaksIssueSentence(elementIdentifier, secondField, secondIssue))
        if firstIssue:
            sentences.append(self.tr("Cannot classify."))
        else:
            sentences.append(self.tr("Classification will be ignored."))
        QMessageBox.warning(self, self.tr("Classification"), "\n".join(sentences))

    def openManualBreaksDialog(self):
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not classifyField:
            return
        layer = self.resolveLayerForClassifyField(classifyField)
        if layer is None:
            return
        values = self.collectNumericValues(layer, classifyField, request=self.breaksFeatureRequest(layer))
        if self.isResultProperty(classifyField) and self.isResultsLayer(layer):
            allValues = self.collectAllTimesValues(layer, classifyField, None, False)
            if allValues:
                values = allValues
        if not values:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("No numeric values available for the selected classification field."),
            )
            return
        dataMin = values[0]
        dataMax = values[-1]
        dialog = QGISRedStatisticsManualBreaksDialog(
            dataMin,
            dataMax,
            initialBreaks=self.manualBreaks or None,
            initialClassCount=self.cbClasses.value(),
            parent=self,
        )
        if dialog.exec():
            self.manualBreaks = dialog.getBreaks()
            self.cbClasses.blockSignals(True)
            self.cbClasses.setValue(dialog.getClassCount())
            self.cbClasses.blockSignals(False)

    def openSecondManualBreaksDialog(self):
        classifyField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not classifyField:
            return
        layer = self.resolveLayerForClassifyField(classifyField)
        if layer is None:
            return
        values = self.collectNumericValues(layer, classifyField, request=self.breaksFeatureRequest(layer))
        if self.isResultProperty(classifyField) and self.isResultsLayer(layer):
            allValues = self.collectAllTimesValues(layer, classifyField, None, False)
            if allValues:
                values = allValues
        if not values:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("No numeric values available for the selected classification field."),
            )
            return
        dataMin = values[0]
        dataMax = values[-1]
        dialog = QGISRedStatisticsManualBreaksDialog(
            dataMin,
            dataMax,
            initialBreaks=self.secondManualBreaks or None,
            initialClassCount=self.cbSecondClasses.value(),
            parent=self,
        )
        if dialog.exec():
            self.secondManualBreaks = dialog.getBreaks()
            self.cbSecondClasses.blockSignals(True)
            self.cbSecondClasses.setValue(dialog.getClassCount())
            self.cbSecondClasses.blockSignals(False)

    def resolveAnalysisLayers(self, propertyField, classifyField, secondField, attributeField, quiet=False):
        # Split the involved fields between the element layer and the results layer (joined by element id)
        baseLayer = self.resolveLayer()
        if baseLayer is None:
            if not quiet:
                QMessageBox.warning(
                    self,
                    self.tr("No layer"),
                    self.tr("The selected element type has no matching layer in the current project."),
                )
            return None
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
        baseFields = set()
        joinFields = []
        for fieldName in (propertyField, classifyField, secondField, attributeField):
            if not fieldName:
                continue
            if baseLayer.fields().indexFromName(fieldName) >= 0:
                baseFields.add(fieldName)
            elif fieldName not in joinFields:
                joinFields.append(fieldName)
        resultsLayer = None
        if joinFields:
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category is None or any(not self.isResultProperty(fieldName) for fieldName in joinFields):
                if not quiet:
                    QMessageBox.warning(
                        self,
                        self.tr("Layer mismatch"),
                        self.tr("The selected properties must belong to the same element type."),
                    )
                return None
            resultsLayer = self.resolveResultsLayer(category)
            if resultsLayer is None:
                if not quiet:
                    QMessageBox.warning(self, self.tr("No results"), self.tr("Results are not available for this element type."))
                return None
            for fieldName in joinFields:
                if resultsLayer.fields().indexFromName(fieldName) < 0:
                    if not quiet:
                        QMessageBox.warning(
                            self,
                            self.tr("Field missing"),
                            self.tr("Result field '{0}' was not found on the results layer.").format(fieldName),
                        )
                    return None
        return {
            "baseLayer": baseLayer,
            "resultsLayer": resultsLayer,
            "baseFields": baseFields,
            "joinFields": joinFields,
            "baseIdField": self.fieldUtils.getIdFieldName(baseLayer),
        }

    def buildResultValueLookup(self, layers):
        resultsLayer = layers["resultsLayer"]
        joinFields = layers["joinFields"]
        if resultsLayer is None or not joinFields:
            return {}
        idFieldName = self.fieldUtils.getIdFieldName(resultsLayer)
        lookup = {}
        for feature in resultsLayer.getFeatures():
            lookup[str(feature[idFieldName])] = {fieldName: feature[fieldName] for fieldName in joinFields}
        return lookup

    def computeJoinFilterIds(self, layers, attributeField, quiet=False):
        # Ids passing the filters that can only run on the results layer (joined fields)
        resultsLayer = layers["resultsLayer"]
        if resultsLayer is None:
            return None
        expressions = []
        if attributeField and attributeField in layers["joinFields"]:
            expression = self.buildAttributeExpression(resultsLayer, quiet=quiet)
            if expression is False:
                return False
            if expression:
                expressions.append(expression)
        if "Demand" in layers["joinFields"]:
            demandExpression = self.demandExclusionExpression(resultsLayer)
            if demandExpression:
                expressions.append(demandExpression)
        if not expressions:
            return None
        idFieldName = self.fieldUtils.getIdFieldName(resultsLayer)
        request = QgsFeatureRequest().setFilterExpression(" AND ".join("({})".format(e) for e in expressions))
        return {str(feature[idFieldName]) for feature in resultsLayer.getFeatures(request)}

    def collectBaseElementIds(self, layers):
        baseLayer = layers["baseLayer"]
        idFieldName = layers["baseIdField"]
        if baseLayer.fields().indexFromName(idFieldName) < 0:
            return None
        request = self.breaksFeatureRequest(baseLayer)
        featureIterator = baseLayer.getFeatures(request) if request is not None else baseLayer.getFeatures()
        return {str(feature[idFieldName]) for feature in featureIterator}

    def collectAllTimesValues(self, resultsLayer, fieldName, idSet, isCategorical):
        # Values across every time step, so class ranges stay fixed as time advances
        allPath = QGISRedResultsAllUtils.getAllShapefilePathForLayer(resultsLayer)
        if allPath is None:
            return None
        allLayer = QGISRedResultsAllUtils.loadAllLayer(allPath)
        if allLayer is None:
            return None
        allFieldName = QGISRedResultsAllUtils.getAllFieldName(fieldName, allLayer)
        if allFieldName is None:
            return None
        expressions = (self.headLossExclusionExpression(allLayer), self.demandExclusionExpression(allLayer))
        filterExpression = " AND ".join("({})".format(e) for e in expressions if e)
        if isCategorical:
            return QGISRedResultsAllUtils.collectAllUniqueValues(allLayer, allFieldName, idSet=idSet, filterExpression=filterExpression)
        return QGISRedResultsAllUtils.collectAllNumericValues(
            allLayer, allFieldName, idSet=idSet, absolute=fieldName == "Flow", filterExpression=filterExpression,
        )

    def resolveBreaksForField(self, layers, fieldName, rangedId, numClasses, intervalValue, manualBreaks, quiet=False):
        self._lastBreaksIssue = None
        baseLayer = layers["baseLayer"]
        if not self.isResultProperty(fieldName):
            return self.resolveBreaks(baseLayer, fieldName, rangedId, numClasses, intervalValue, manualBreaks, quiet=quiet)
        resultsLayer = baseLayer if self.isResultsLayer(baseLayer) else layers["resultsLayer"]
        if resultsLayer is None:
            return self.resolveBreaks(baseLayer, fieldName, rangedId, numClasses, intervalValue, manualBreaks, quiet=quiet)
        baseIdSet = self.collectBaseElementIds(layers)
        isCategorical = self.isCategoricalClassifier(fieldName) or rangedId == "Categorized"
        values = self.collectAllTimesValues(resultsLayer, fieldName, baseIdSet, isCategorical)
        if values is None:
            # No _All shapefile: fall back to the currently loaded time step
            if isCategorical:
                values = self.collectUniqueValues(resultsLayer, fieldName, limit=10000, request=self.breaksFeatureRequest(resultsLayer), idSet=baseIdSet)
            else:
                values = self.collectNumericValues(resultsLayer, fieldName, request=self.breaksFeatureRequest(resultsLayer), idSet=baseIdSet)
        if isCategorical:
            return {"type": "categorical", "values": [str(value) for value in values]}
        issue = self.numericValuesIssue(values)
        if issue:
            # No dialog here: the caller composes one message covering both classifications
            self._lastBreaksIssue = issue
            return None
        dataMin = values[0]
        dataMax = values[-1]
        edges = self.calculateBreaks(rangedId, values, numClasses, dataMin, dataMax, intervalValue, manualBreaks)
        edges = self.normalizeBreakEdges(edges, dataMin, dataMax)
        if edges is None or len(edges) < 2:
            if not quiet:
                QMessageBox.warning(self, self.tr("Breaks failed"), self.tr("Unable to compute breaks for the chosen method."))
            return None
        return {"type": "breaks", "edges": edges}

    def analyze(self):
        elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole)
        propertyField = self.cbProperty.currentData(Qt.ItemDataRole.UserRole)
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        if not propertyField:
            return
        secondField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) if classifyField else ""
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) if condition not in ("", "All") else ""
        if attributeField and condition != "Range":
            # An empty value means no filter is applied, so the attribute must
            # not count as part of the analysis (e.g. for the results time label)
            valueData = self.cbValue.currentData(Qt.ItemDataRole.UserRole)
            rawValue = valueData if valueData not in (None, "") else self.cbValue.currentText().strip()
            if rawValue in (None, ""):
                attributeField = ""

        layers = self.resolveAnalysisLayers(propertyField, classifyField, secondField, attributeField)
        if layers is None:
            return
        baseLayer = layers["baseLayer"]

        featureRequest = self.buildFeatureRequest(baseLayer)
        if featureRequest is False:
            return
        joinFilterIds = self.computeJoinFilterIds(layers, attributeField)
        if joinFilterIds is False:
            return

        breaks = None
        breaksParams = None
        firstIssue = None
        if classifyField:
            breaksParams = (
                self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or "EqualInterval",
                self.cbClasses.value() or DEFAULT_NUM_CLASSES,
                self.spinIntervalRange.value(),
                list(self.manualBreaks),
            )
            breaks = self.resolveBreaksForField(layers, classifyField, *breaksParams)
            if breaks is None:
                firstIssue = self._lastBreaksIssue
                if firstIssue is None:
                    # Genuine "Breaks failed": dialog already shown inline
                    return
                # Keep going so a both-fields failure yields a single dialog

        secondBreaks = None
        secondBreaksParams = None
        secondIssue = None
        if secondField:
            secondBreaksParams = (
                self.cbSecondRanged.currentData(Qt.ItemDataRole.UserRole) or "EqualInterval",
                self.cbSecondClasses.value() or DEFAULT_NUM_CLASSES,
                self.spinSecondIntervalRange.value(),
                list(self.secondManualBreaks),
            )
            secondBreaks = self.resolveBreaksForField(layers, secondField, *secondBreaksParams)
            if secondBreaks is None:
                secondIssue = self._lastBreaksIssue
                if secondIssue is None:
                    if firstIssue is not None:
                        self.showBreaksIssues(elementIdentifier, classifyField, firstIssue, secondField, None)
                    return

        requestedSecondField = secondField
        if firstIssue or secondIssue:
            self.showBreaksIssues(elementIdentifier, classifyField, firstIssue, secondField, secondIssue)
            if firstIssue:
                return
            # Degrade gracefully: continue as if no second classification was set
            secondField = ""
            secondBreaks = None

        if secondBreaks is not None:
            self._secondClassBins = self.initBins(secondBreaks, self.propertyDecimalsFor(elementIdentifier, secondField))
        else:
            self._secondClassBins = []
        self.populateSecondClassValues(elementIdentifier, secondField)
        self._analysisContext = {
            "propertyLayer": baseLayer,
            "propertyField": propertyField,
            "classifyField": classifyField,
            "breaks": breaks,
            "breaksParams": breaksParams,
            "secondField": secondField,
            "secondFieldRequested": requestedSecondField,
            "secondBreaks": secondBreaks,
            "secondBreaksParams": secondBreaksParams,
            "featureRequest": featureRequest,
            "elementIdentifier": elementIdentifier,
            "attributeField": attributeField,
            "resultsLayer": layers["resultsLayer"],
            "baseFields": layers["baseFields"],
            "joinFields": layers["joinFields"],
            "baseIdField": layers["baseIdField"],
            "resultLookup": self.buildResultValueLookup(layers),
            "attributeFilterIds": joinFilterIds,
        }
        self._breaksDirty = False
        self.renderAnalysis()
        self.updateResultsTimeLabel()
        self.tabWidget.setCurrentIndex(1)
        QTimer.singleShot(0, self.adjustFloatingHeightForReport)

    def adjustFloatingHeightForReport(self):
        # Fit the table up to 5 classes plus the Total row when the panel floats
        if not self.isFloating():
            return
        rowCount = self.tbExcel.rowCount()
        if rowCount == 0:
            return
        visibleRows = min(rowCount, 6)
        neededTableHeight = self.tbExcel.horizontalHeader().height() + 2 * self.tbExcel.frameWidth()
        for row in range(visibleRows):
            neededTableHeight += self.tbExcel.rowHeight(row) or self.tbExcel.verticalHeader().defaultSectionSize()
        delta = neededTableHeight - self.tbExcel.height()
        if delta <= 0:
            return
        available = self.screen().availableGeometry().height() - self.height()
        if available > 0:
            self.resize(self.width(), self.height() + min(delta, available))

    def populateSecondClassValues(self, elementIdentifier, secondField):
        self.cbSecondClassValue.blockSignals(True)
        self.cbSecondClassValue.clear()
        if not secondField:
            self.cbSecondClassValue.blockSignals(False)
            self.labelSecondClassValue.hide()
            self.cbSecondClassValue.hide()
            self.labelSecondClassUnit.hide()
            return
        self.cbSecondClassValue.addItem(self.tr("All groups"), None)
        for index, binData in enumerate(self._secondClassBins):
            self.cbSecondClassValue.addItem(binData.get("label", ""), index)
        self.cbSecondClassValue.setCurrentIndex(0)
        self.cbSecondClassValue.blockSignals(False)
        secondElement = self.elementForField(elementIdentifier, secondField)
        prettySecond = self.fieldUtils.getProperty(secondElement, secondField) or secondField
        self.labelSecondClassValue.setText(prettySecond)
        unit = self.fieldUtils.getUnitAbbreviation(secondElement, secondField) or ""
        self.labelSecondClassUnit.setText(unit)
        self.labelSecondClassUnit.setVisible(bool(unit))
        self.labelSecondClassValue.show()
        self.cbSecondClassValue.show()
        self.updateComboBoxBackground(self.cbSecondClassValue)

    def onSecondClassValueChanged(self):
        if not self._analysisContext:
            return
        self.renderAnalysis(preserveStatistic=True)

    def renderFromContext(self):
        # Passive refresh of the last analysis; False tells the caller to clear instead
        context = self._analysisContext
        if not context:
            return False
        if self.cbElementType.currentData(Qt.ItemDataRole.UserRole) != context["elementIdentifier"]:
            return False
        propertyField = context["propertyField"]
        classifyField = context["classifyField"]
        secondField = context["secondField"]
        # The combos keep showing what the user requested, which may differ from the
        # effective secondField when the classification was degraded to none
        requestedSecondField = context.get("secondFieldRequested", secondField)
        if self.cbProperty.currentData(Qt.ItemDataRole.UserRole) != propertyField:
            return False
        if (self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or "") != (classifyField or ""):
            return False
        if classifyField and (self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or "") != (requestedSecondField or ""):
            return False
        attributeField = context.get("attributeField", "")
        layers = self.resolveAnalysisLayers(propertyField, classifyField, requestedSecondField, attributeField, quiet=True)
        if layers is None:
            return False
        baseLayer = layers["baseLayer"]
        if baseLayer.featureCount() == 0:
            return False
        if self.cbSelectedElements.isChecked() and not baseLayer.selectedFeatureIds():
            return False
        featureRequest = self.buildFeatureRequest(baseLayer)
        if featureRequest is False:
            return False
        joinFilterIds = self.computeJoinFilterIds(layers, attributeField)
        if joinFilterIds is False:
            return False
        if self._breaksDirty:
            # Data changed (new simulation): recompute the ranges of dynamic classifiers
            if classifyField and self.isResultProperty(classifyField):
                breaks = self.resolveBreaksForField(layers, classifyField, *context["breaksParams"], quiet=True)
                if breaks is None:
                    return False
                context["breaks"] = breaks
            if requestedSecondField and self.isResultProperty(requestedSecondField):
                secondBreaks = self.resolveBreaksForField(layers, requestedSecondField, *context["secondBreaksParams"], quiet=True)
                if secondBreaks is None:
                    if self._lastBreaksIssue is None:
                        return False
                    # New data has no usable values: degrade silently to no second classification
                    secondField = ""
                    context["secondField"] = ""
                    context["secondBreaks"] = None
                    self._secondClassBins = []
                    self.populateSecondClassValues(context["elementIdentifier"], "")
                else:
                    # Usable values again (e.g. new simulation): restore the second classification
                    secondField = requestedSecondField
                    context["secondField"] = requestedSecondField
                    context["secondBreaks"] = secondBreaks
                    selectedSecondIndex = self.cbSecondClassValue.currentIndex()
                    self._secondClassBins = self.initBins(secondBreaks, self.propertyDecimalsFor(context["elementIdentifier"], requestedSecondField))
                    self.populateSecondClassValues(context["elementIdentifier"], requestedSecondField)
                    if 0 <= selectedSecondIndex < self.cbSecondClassValue.count():
                        self.cbSecondClassValue.blockSignals(True)
                        self.cbSecondClassValue.setCurrentIndex(selectedSecondIndex)
                        self.cbSecondClassValue.blockSignals(False)
            self._breaksDirty = False
        context["propertyLayer"] = baseLayer
        context["featureRequest"] = featureRequest
        context["resultsLayer"] = layers["resultsLayer"]
        context["baseFields"] = layers["baseFields"]
        context["joinFields"] = layers["joinFields"]
        context["baseIdField"] = layers["baseIdField"]
        context["resultLookup"] = self.buildResultValueLookup(layers)
        context["attributeFilterIds"] = joinFilterIds
        self.renderAnalysis(preserveStatistic=True)
        self.updateResultsTimeLabel()
        return True

    def renderAnalysis(self, preserveStatistic=False):
        context = self._analysisContext
        if not context:
            return
        propertyLayer = context["propertyLayer"]
        propertyField = context["propertyField"]
        classifyField = context["classifyField"]
        breaks = context["breaks"]
        secondField = context["secondField"]
        secondBreaks = context["secondBreaks"]
        featureRequest = context["featureRequest"]
        elementIdentifier = context["elementIdentifier"]

        if not classifyField:
            self.renderUnclassifiedAnalysis(context)
            return

        self.mStatisticsGroupBox.show()
        selectedSecondIndex = None
        if secondField and secondBreaks is not None and self.cbSecondClassValue.currentIndex() > 0:
            selectedSecondIndex = self.cbSecondClassValue.currentIndex() - 1

        self.isEnumeratedTarget = not self.isNumericField(propertyLayer, propertyField)
        bins = self.initBins(breaks, self.propertyDecimalsFor(elementIdentifier, classifyField))
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0

        featureIterator = propertyLayer.getFeatures(featureRequest) if featureRequest is not None else propertyLayer.getFeatures()
        for feature in featureIterator:
            if not self.featurePassesResultFilter(context, feature):
                continue
            if selectedSecondIndex is not None:
                secondValue = self.contextFieldValue(context, feature, secondField)
                if secondValue is None:
                    continue
                if self.findBinIndex(self._secondClassBins, secondValue, secondBreaks["type"]) != selectedSecondIndex:
                    continue
            classValue = self.contextFieldValue(context, feature, classifyField)
            if classValue is None:
                self.lastNullCount += 1
                continue
            binIndex = self.findBinIndex(bins, classValue, breaks["type"])
            if binIndex is None:
                self.lastOutOfRangeCount += 1
                continue
            propertyValue = self.contextFieldValue(context, feature, propertyField)
            if propertyValue is None:
                self.lastNullCount += 1
                continue
            self.accumulateValue(bins[binIndex], propertyValue, propertyValue)

        self.finalizeBins(bins)

        propertyElement = self.elementForField(elementIdentifier, propertyField)
        classifyElement = self.elementForField(elementIdentifier, classifyField)
        prettyProperty = self.fieldUtils.getProperty(propertyElement, propertyField) or propertyField
        prettyClassify = self.fieldUtils.getProperty(classifyElement, classifyField) or classifyField
        propertyUnit = self.fieldUtils.getUnitAbbreviation(propertyElement, propertyField) or ""
        classifyUnit = self.fieldUtils.getUnitAbbreviation(classifyElement, classifyField) or ""

        chartTitle = self.buildChartTitle(context, prettyProperty, prettyClassify, selectedSecondIndex)
        self._tableTitleBase = self.buildTableTitle(context, prettyProperty, prettyClassify, propertyUnit)
        subtitle = self.buildSubtitle(elementIdentifier)
        xLabel = "{} ({})".format(prettyClassify, classifyUnit) if classifyUnit else prettyClassify
        useSum = self.usesSumColumn(propertyField, elementIdentifier)
        self._chartBins = bins
        self._chartPrettyProperty = prettyProperty
        self._chartPropertyUnit = propertyUnit
        self._chartXLabel = xLabel
        self._chartSubtitle = subtitle
        self._chartTitleBase = chartTitle
        self._chartUseSum = useSum
        self.histogram.setTitles(chartTitle, subtitle)
        previousStatistic = self.cbStatistic.currentData(Qt.ItemDataRole.UserRole) if preserveStatistic else None
        self.populateStatisticOptions(bins, useSum)
        if preserveStatistic:
            self.restoreStatisticSelection(previousStatistic)
        self.renderChart()

        if secondField and secondBreaks is not None:
            prettySecond = self.fieldUtils.getProperty(self.elementForField(elementIdentifier, secondField), secondField) or secondField
            self.buildSecondClassMatrix(
                bins, propertyLayer, propertyField, classifyField, breaks, secondField, secondBreaks,
                featureRequest, prettyClassify, prettySecond, prettyProperty,
                useSum, self.propertyDecimalsFor(elementIdentifier, propertyField),
            )
            previousTableStatistic = self.cbTableStatistic.currentData(Qt.ItemDataRole.UserRole) if preserveStatistic else None
            self._fillStatisticCombo(self.cbTableStatistic, self._tableMatrix["allColumn"], useSum)
            if preserveStatistic:
                self._restoreComboSelection(self.cbTableStatistic, previousTableStatistic)
            self.labelTableStatistic.show()
            self.cbTableStatistic.show()
            self.populateMatrixTable()
        else:
            self._tableMatrix = None
            self.labelTableStatistic.hide()
            self.cbTableStatistic.hide()
            self.populateTable(bins, prettyClassify, prettyProperty, propertyUnit, elementIdentifier, propertyField)
        self.updateTableTitle()

    def renderUnclassifiedAnalysis(self, context):
        # No classification: aggregate everything into a single bin and show the table only
        propertyLayer = context["propertyLayer"]
        propertyField = context["propertyField"]
        featureRequest = context["featureRequest"]
        elementIdentifier = context["elementIdentifier"]
        self.isEnumeratedTarget = not self.isNumericField(propertyLayer, propertyField)
        overallBin = self.makeBin(label=self.tr("Total"), lo=None, hi=None, category=None)
        self.lastNullCount = 0
        self.lastOutOfRangeCount = 0
        featureIterator = propertyLayer.getFeatures(featureRequest) if featureRequest is not None else propertyLayer.getFeatures()
        for feature in featureIterator:
            if not self.featurePassesResultFilter(context, feature):
                continue
            propertyValue = self.contextFieldValue(context, feature, propertyField)
            if propertyValue is None:
                self.lastNullCount += 1
                continue
            self.accumulateValue(overallBin, propertyValue, propertyValue)
        self.finalizeBins([overallBin])

        popout = getattr(self, "_histogramPopout", None)
        if popout is not None and popout.isVisible():
            self._closeHistogramPopout()
        self.histogram.clear()
        self._chartBins = []
        self.cbStatistic.blockSignals(True)
        self.cbStatistic.clear()
        self.cbStatistic.blockSignals(False)
        self.mStatisticsGroupBox.hide()

        propertyElement = self.elementForField(elementIdentifier, propertyField)
        prettyProperty = self.fieldUtils.getProperty(propertyElement, propertyField) or propertyField
        propertyUnit = self.fieldUtils.getUnitAbbreviation(propertyElement, propertyField) or ""
        pluralProperty = self.fieldUtils.getPluralProperty(propertyElement, propertyField) or prettyProperty
        qualifier = self.resultPropertyQualifier(elementIdentifier, propertyField)
        if qualifier:
            pluralProperty = "{} {}".format(qualifier, pluralProperty)
        titleProperty = "{} ({})".format(pluralProperty, propertyUnit) if propertyUnit else pluralProperty
        self._tableTitleBase = titleProperty
        self.labelTableTitle.setText("{} {}".format(self.tr("Stats for"), titleProperty))
        self._tableMatrix = None
        self.labelTableStatistic.hide()
        self.cbTableStatistic.hide()
        self.populateTable(
            [overallBin], self.cbElementType.currentText(), prettyProperty, propertyUnit,
            elementIdentifier, propertyField, includeTotal=False,
        )
        self.highlightTotalRow()

    def highlightTotalRow(self):
        for column in range(self.tbExcel.columnCount()):
            item = self.tbExcel.item(0, column)
            if item is None:
                continue
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QBrush(QColor(255, 248, 220)))

    def buildChartTitle(self, context, prettyProperty, prettyClassify, selectedSecondIndex):
        secondField = context["secondField"]
        secondBreaks = context["secondBreaks"]
        elementIdentifier = context["elementIdentifier"]
        propertyElement = self.elementForField(elementIdentifier, context["propertyField"])
        pluralProperty = self.fieldUtils.getPluralProperty(propertyElement, context["propertyField"]) or prettyProperty
        qualifier = self.resultPropertyQualifier(elementIdentifier, context["propertyField"])
        if qualifier:
            pluralProperty = "{} {}".format(qualifier, pluralProperty)
        if context["propertyField"] == context["classifyField"]:
            rangeKind = self.tr("by Categories") if context["breaks"]["type"] == "categorical" else self.tr("by Ranges")
            base = "{} {}".format(pluralProperty, rangeKind)
        else:
            classifyElement = self.elementForField(elementIdentifier, context["classifyField"])
            pluralClassify = self.fieldUtils.getPluralProperty(classifyElement, context["classifyField"]) or prettyClassify
            base = "{} {} {}".format(pluralProperty, self.tr("by"), pluralClassify)
        if not secondField or selectedSecondIndex is None:
            return base
        secondElement = self.elementForField(elementIdentifier, secondField)
        groupLabel = self.cbSecondClassValue.currentText()
        prettySecond = self.fieldUtils.getProperty(secondElement, secondField) or secondField
        if secondBreaks is not None and secondBreaks["type"] != "categorical":
            return "{} {} {} {} {}".format(base, self.tr("for"), prettySecond, self.tr("on Range"), groupLabel)
        return "{} {} {} {}".format(base, self.tr("for"), prettySecond, groupLabel)

    def buildTableTitle(self, context, prettyProperty, prettyClassify, propertyUnit):
        # Fixed title: always shows both classification criteria, independent of
        # the group selected in the histogram (the table shows all groups)
        title = self.buildChartTitle(context, prettyProperty, prettyClassify, None)
        if context["propertyField"] != context["classifyField"]:
            classifyElement = self.elementForField(context["elementIdentifier"], context["classifyField"])
            classifyUnit = self.fieldUtils.getUnitAbbreviation(classifyElement, context["classifyField"]) or ""
            if classifyUnit:
                title = "{} ({})".format(title, classifyUnit)
        secondField = context["secondField"]
        if secondField:
            secondElement = self.elementForField(context["elementIdentifier"], secondField)
            pluralSecond = self.fieldUtils.getPluralProperty(secondElement, secondField) or secondField
            secondUnit = self.fieldUtils.getUnitAbbreviation(secondElement, secondField) or ""
            if secondUnit:
                pluralSecond = "{} ({})".format(pluralSecond, secondUnit)
            title = "{} {} {}".format(title, self.tr("and"), pluralSecond)
        element = self.elementForField(context["elementIdentifier"], context["propertyField"])
        pluralProperty = self.fieldUtils.getPluralProperty(element, context["propertyField"]) or prettyProperty
        qualifier = self.resultPropertyQualifier(context["elementIdentifier"], context["propertyField"])
        if qualifier:
            pluralProperty = "{} {}".format(qualifier, pluralProperty)
        if propertyUnit and title.startswith(pluralProperty):
            title = "{} ({}){}".format(pluralProperty, propertyUnit, title[len(pluralProperty):])
        return title

    def updateTableTitle(self):
        if not self._tableTitleBase:
            return
        if self._tableMatrix is not None:
            prefix = self.cbTableStatistic.currentText() or self.tr("Stats for")
        else:
            prefix = self.tr("Stats for")
        self.labelTableTitle.setText("{} {}".format(prefix, self._tableTitleBase))

    def restoreStatisticSelection(self, previousData):
        self._restoreComboSelection(self.cbStatistic, previousData)

    def _restoreComboSelection(self, combo, previousData):
        if previousData is None:
            return
        for index in range(combo.count()):
            if combo.itemData(index, Qt.ItemDataRole.UserRole) == previousData:
                combo.blockSignals(True)
                combo.setCurrentIndex(index)
                combo.blockSignals(False)
                return

    def populateStatisticOptions(self, bins, useSum):
        self._fillStatisticCombo(self.cbStatistic, bins, useSum)

    def _fillStatisticCombo(self, combo, bins, useSum):
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr("Count"), ("stat", "count"))
        if self.isEnumeratedTarget:
            uniqueValues = set()
            for binData in bins:
                uniqueValues.update(binData["values"].keys())
            for value in sorted(uniqueValues, key=lambda item: str(item)):
                combo.addItem(str(value), ("value", str(value)))
        elif useSum:
            combo.addItem(self.tr("Sum"), ("stat", "sum"))
            combo.addItem(self.tr("Avg"), ("stat", "avg"))
            combo.addItem(self.tr("Min"), ("stat", "min"))
            combo.addItem(self.tr("Max"), ("stat", "max"))
        else:
            combo.addItem(self.tr("Avg"), ("stat", "avg"))
            combo.addItem(self.tr("Min"), ("stat", "min"))
            combo.addItem(self.tr("Max"), ("stat", "max"))
            combo.addItem(self.tr("StdD"), ("stat", "stddev"))
        combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def onStatisticChanged(self):
        if not self._chartBins:
            return
        self.renderChart()

    def onTableStatisticChanged(self):
        if not self._tableMatrix:
            return
        self.updateTableTitle()
        self.populateMatrixTable()

    def renderChart(self):
        kind, key = self.cbStatistic.currentData(Qt.ItemDataRole.UserRole) or ("stat", "count")
        statKey = key if kind == "stat" else "count"
        valueKey = key if kind == "value" else None
        yLabel = self.statisticYLabel(kind, key)
        title = self._chartTitleBase
        if title and kind == "stat" and key != "count":
            title = "{} {}".format(self.cbStatistic.currentText(), title)
        if title:
            self.histogram.setTitles(title, self._chartSubtitle)
        self.histogram.setBins(
            self._chartBins, mode="plain", xLabel=self._chartXLabel,
            yLabelLeft=yLabel, statKey=statKey, valueKey=valueKey,
        )
        self._feedHistogramPopout()

    def statisticYLabel(self, kind, key):
        if kind == "value" or key == "count":
            return self.tr("Count")
        statLabels = {
            "sum": self.tr("Sum"), "avg": self.tr("Avg"), "stddev": self.tr("StdD"),
            "min": self.tr("Min"), "max": self.tr("Max"),
        }
        statLabel = statLabels.get(key, self.tr("Count"))
        if self._chartPropertyUnit:
            return "{} {} ({})".format(statLabel, self._chartPrettyProperty, self._chartPropertyUnit)
        return "{} {}".format(statLabel, self._chartPrettyProperty)

    def isNumericField(self, layer, fieldName):
        if self.isResultProperty(fieldName):
            return fieldName != "Status"
        if fieldName in CATEGORICAL_FIELD_NAMES:
            return False
        fieldIdx = layer.fields().indexFromName(fieldName)
        if fieldIdx < 0:
            return False
        cat = FIELD_TYPE_MAPPING.get(layer.fields().field(fieldIdx).typeName().lower(), "text")
        return cat == "numeric"

    def buildFeatureRequest(self, layer):
        request = QgsFeatureRequest()
        applied = False
        if self.cbSelectedElements.isChecked():
            selectedIds = layer.selectedFeatureIds()
            if not selectedIds:
                QMessageBox.information(
                    self,
                    self.tr("No selection"),
                    self.tr("'Only selected elements' is checked but no features are selected on the active layer."),
                )
                return False
            request.setFilterFids(list(selectedIds))
            applied = True
            self.labelOnlySelectedElements.show()
        else:
            self.labelOnlySelectedElements.hide()

        expression = self.buildAttributeExpression(layer)
        if expression is False:
            return False
        if expression:
            request.combineFilterExpression(expression)
            applied = True

        for exclusion in (self.headLossExclusionExpression(layer), self.demandExclusionExpression(layer)):
            if exclusion:
                request.combineFilterExpression(exclusion)
                applied = True
        return request if applied else None

    def buildAttributeExpression(self, layer, quiet=False):
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if not attributeField:
            return ""
        if layer.fields().indexFromName(attributeField) < 0:
            return ""
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        if condition in ("", "All"):
            return ""
        quotedColumn = QgsExpression.quotedColumnRef(attributeField)
        if attributeField == "Flow":
            quotedColumn = "abs({})".format(quotedColumn)
        if condition == "Range":
            fromText = self.leFrom.text().strip()
            toText = self.leTo.text().strip()
            if not fromText or not toText:
                if not quiet:
                    QMessageBox.warning(self, self.tr("Range filter"), self.tr("Both 'From' and 'To' values are required for a Range filter."))
                return False
            try:
                fromValue = float(fromText)
                toValue = float(toText)
            except ValueError:
                if not quiet:
                    QMessageBox.warning(self, self.tr("Range filter"), self.tr("'From' and 'To' must be numeric."))
                return False
            if attributeField == "Flow":
                fromValue, toValue = sorted((abs(fromValue), abs(toValue)))
            if fromValue > toValue:
                if not quiet:
                    QMessageBox.warning(self, self.tr("Range filter"), self.tr("'From' must be less than or equal to 'To'."))
                return False
            return "{0} >= {1} AND {0} <= {2}".format(quotedColumn, fromValue, toValue)

        valueText = self.cbValue.currentText().strip()
        valueData = self.cbValue.currentData(Qt.ItemDataRole.UserRole)
        rawValue = valueData if valueData not in (None, "") else valueText
        if rawValue in (None, ""):
            return ""
        operatorMap = {"=": "=", "≠": "<>", ">": ">", "<": "<", ">=": ">=", "<=": "<=",
                       "LIKE": " LIKE ", "NOT LIKE": " NOT LIKE ",
                       "ILIKE": " ILIKE ", "NOT ILIKE": " NOT ILIKE "}
        op = operatorMap.get(condition, condition)
        cat = self.classifyAttributeType(attributeField)
        if cat == "numeric":
            try:
                numericValue = float(rawValue)
            except (TypeError, ValueError):
                if not quiet:
                    QMessageBox.warning(self, self.tr("Filter value"), self.tr("Numeric value required for this condition."))
                return False
            if attributeField == "Flow":
                numericValue = abs(numericValue)
            return "{0} {1} {2}".format(quotedColumn, op, numericValue)
        textValue = str(rawValue)
        if condition in ("LIKE", "NOT LIKE", "ILIKE", "NOT ILIKE"):
            quoted = QgsExpression.quotedString("%{}%".format(textValue))
        else:
            quoted = QgsExpression.quotedString(textValue)
        return "{0}{1}{2}".format(quotedColumn, op, quoted)

    def headLossExclusionExpression(self, layer):
        # HeadLoss only applies to pipes, so pumps and valves are left out
        fields = layer.fields()
        if fields.indexFromName("Type") < 0 or fields.indexFromName("HeadLoss") < 0:
            return ""
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        secondField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) if classifyField else ""
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) if condition not in ("", "All") else ""
        involvedFields = (self.cbProperty.currentData(Qt.ItemDataRole.UserRole), classifyField, secondField, attributeField)
        if "HeadLoss" not in involvedFields:
            return ""
        return "{} NOT IN ('PUMP', 'VALVE')".format(QgsExpression.quotedColumnRef("Type"))

    def demandExclusionExpression(self, layer):
        # Demand results only apply to junctions consuming water
        fields = layer.fields()
        if fields.indexFromName("Demand") < 0:
            return ""
        classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole)
        secondField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) if classifyField else ""
        condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) if condition not in ("", "All") else ""
        involvedFields = (self.cbProperty.currentData(Qt.ItemDataRole.UserRole), classifyField, secondField, attributeField)
        if "Demand" not in involvedFields:
            return ""
        expression = "{} > 0".format(QgsExpression.quotedColumnRef("Demand"))
        if fields.indexFromName("Type") >= 0:
            expression = "{} = 'Junction' AND {}".format(QgsExpression.quotedColumnRef("Type"), expression)
        return expression

    def breaksFeatureRequest(self, layer):
        request = None
        for exclusion in (self.headLossExclusionExpression(layer), self.demandExclusionExpression(layer)):
            if exclusion:
                if request is None:
                    request = QgsFeatureRequest()
                request.combineFilterExpression(exclusion)
        return request

    def resolveBreaks(self, layer, classifyField, rangedId, numClasses, intervalValue, manualBreaks, quiet=False):
        breaksRequest = self.breaksFeatureRequest(layer)
        if self.isCategoricalClassifier(classifyField):
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=10000, request=breaksRequest)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        if rangedId == "Categorized":
            distinctValues = self.collectUniqueValues(layer, classifyField, limit=10000, request=breaksRequest)
            return {"type": "categorical", "values": [str(value) for value in distinctValues]}
        numericValues = self.collectNumericValues(layer, classifyField, request=breaksRequest)
        issue = self.numericValuesIssue(numericValues)
        if issue:
            # No dialog here: the caller composes one message covering both classifications
            self._lastBreaksIssue = issue
            return None
        dataMin = numericValues[0]
        dataMax = numericValues[-1]
        edges = self.calculateBreaks(rangedId, numericValues, numClasses, dataMin, dataMax, intervalValue, manualBreaks)
        edges = self.normalizeBreakEdges(edges, dataMin, dataMax)
        if edges is None or len(edges) < 2:
            if not quiet:
                QMessageBox.warning(self, self.tr("Breaks failed"), self.tr("Unable to compute breaks for the chosen method."))
            return None
        return {"type": "breaks", "edges": edges}

    def calculateBreaks(self, rangedId, values, numClasses, dataMin, dataMax, intervalValue, manualBreaks):
        if rangedId == "EqualInterval":
            return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)
        if rangedId == "FixedInterval":
            return self.calculateFixedIntervalBreaks(dataMin, dataMax, intervalValue)
        if rangedId == "Quantile":
            return self.calculateQuantileBreaks(values, numClasses, dataMin)
        if rangedId == "Jenks":
            return self.calculateJenksBreaks(values, numClasses, dataMin)
        if rangedId == "Pretty":
            return self.calculatePrettyBreaks(values, numClasses, dataMin)
        if rangedId == "Manual":
            if not manualBreaks or len(manualBreaks) < 2:
                return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)
            return list(manualBreaks)
        return self.calculateEqualIntervalBreaks(numClasses, dataMin, dataMax)

    def normalizeBreakEdges(self, edges, dataMin, dataMax):
        # Classifiers return duplicate bounds when there are not enough
        # distinct values (e.g. all values identical), which would render
        # as repeated empty ranges
        if not edges:
            return None
        normalized = [edges[0]]
        for edge in edges[1:]:
            if edge != normalized[-1]:
                normalized.append(edge)
        if len(normalized) < 2:
            return [dataMin, dataMax]
        return normalized

    def calculateEqualIntervalBreaks(self, numClasses, dataMin, dataMax):
        step = (dataMax - dataMin) / float(numClasses)
        edges = [dataMin + i * step for i in range(numClasses + 1)]
        edges[-1] = dataMax
        return edges

    def calculateFixedIntervalBreaks(self, dataMin, dataMax, stepValue):
        step = stepValue
        if step <= 0:
            return [dataMin, dataMax]
        edges = [dataMin]
        current = dataMin
        while current < dataMax:
            current += step
            edges.append(current)
        return edges

    def calculateQuantileBreaks(self, values, numClasses, dataMin):
        classifier = QgsClassificationQuantile()
        classes = classifier.classes(values, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def calculateJenksBreaks(self, values, numClasses, dataMin):
        classifier = QgsClassificationJenks()
        classes = classifier.classes(values, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def calculatePrettyBreaks(self, values, numClasses, dataMin):
        classifier = QgsClassificationPrettyBreaks()
        classes = classifier.classes(values, numClasses)
        if not classes:
            return None
        return [dataMin] + [cls.upperBound() for cls in classes]

    def initBins(self, breaks, decimals=None):
        bins = []
        if breaks["type"] == "categorical":
            for value in breaks["values"]:
                bins.append(self.makeBin(label=value if value != "" else self.tr("(empty)"),
                                         lo=None, hi=None, category=value))
            return bins
        edges = breaks["edges"]
        for i in range(len(edges) - 1):
            lowerEdge = edges[i]
            upperEdge = edges[i + 1]
            if lowerEdge == upperEdge:
                label = self.formatNumber(lowerEdge, decimals)
            else:
                label = "{} - {}".format(self.formatNumber(lowerEdge, decimals), self.formatNumber(upperEdge, decimals))
            bins.append(self.makeBin(label=label, lo=lowerEdge, hi=upperEdge, category=None))
        return bins

    def makeBin(self, label, lo, hi, category):
        return {
            "label": label,
            "lo": lo,
            "hi": hi,
            "category": category,
            "count": 0,
            "sum": 0.0,
            "sumOfSquares": 0.0,
            "min": None,
            "max": None,
            "avg": 0.0,
            "stddev": 0.0,
            "values": {},
        }

    def fieldValue(self, feature, fieldName):
        return self.convertFieldValue(fieldName, feature[fieldName])

    def convertFieldValue(self, fieldName, value):
        # Flow is always analyzed as a magnitude, so the sign is dropped
        if fieldName == "Flow" and value is not None:
            try:
                return abs(float(value))
            except (TypeError, ValueError):
                return value
        return value

    def contextFieldValue(self, context, feature, fieldName):
        if fieldName in context["joinFields"]:
            elementId = str(feature[context["baseIdField"]])
            value = context["resultLookup"].get(elementId, {}).get(fieldName)
            return self.convertFieldValue(fieldName, value)
        return self.fieldValue(feature, fieldName)

    def featurePassesResultFilter(self, context, feature):
        filterIds = context.get("attributeFilterIds")
        if filterIds is None:
            return True
        return str(feature[context["baseIdField"]]) in filterIds

    def findBinIndex(self, bins, value, breakType):
        if breakType == "categorical":
            stringValue = str(value)
            for binIndex, binData in enumerate(bins):
                if binData.get("category") == stringValue:
                    return binIndex
            return None
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return None
        for binIndex, binData in enumerate(bins):
            lowerEdge = binData["lo"]
            upperEdge = binData["hi"]
            if binIndex == len(bins) - 1:
                if lowerEdge <= numericValue <= upperEdge:
                    return binIndex
            else:
                if lowerEdge <= numericValue < upperEdge:
                    return binIndex
        return None

    def accumulateValue(self, binData, value, enumeratedValue):
        binData["count"] += 1
        if self.isEnumeratedTarget:
            if enumeratedValue is not None:
                stringValue = str(enumeratedValue)
                binData["values"][stringValue] = binData["values"].get(stringValue, 0) + 1
            return
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return
        binData["sum"] += numericValue
        binData["sumOfSquares"] += numericValue * numericValue
        if binData["min"] is None or numericValue < binData["min"]:
            binData["min"] = numericValue
        if binData["max"] is None or numericValue > binData["max"]:
            binData["max"] = numericValue

    def finalizeBins(self, bins):
        for binData in bins:
            count = binData["count"]
            if count > 0 and not self.isEnumeratedTarget:
                binData["avg"] = binData["sum"] / count
                if count > 1:
                    variance = max(0.0, (binData["sumOfSquares"] - count * binData["avg"] * binData["avg"]) / (count - 1))
                    binData["stddev"] = math.sqrt(variance)

    def combineBins(self, bins):
        combined = self.makeBin(label="", lo=None, hi=None, category=None)
        for binData in bins:
            combined["count"] += binData["count"]
            combined["sum"] += binData["sum"]
            combined["sumOfSquares"] += binData["sumOfSquares"]
            if binData["min"] is not None and (combined["min"] is None or binData["min"] < combined["min"]):
                combined["min"] = binData["min"]
            if binData["max"] is not None and (combined["max"] is None or binData["max"] > combined["max"]):
                combined["max"] = binData["max"]
            for value, count in binData["values"].items():
                combined["values"][value] = combined["values"].get(value, 0) + count
        self.finalizeBins([combined])
        return combined

    def binStatValue(self, binData, statKey, valueKey):
        if valueKey is not None:
            return binData["values"].get(valueKey, 0)
        if statKey == "count":
            return binData["count"]
        if binData["count"] == 0:
            return None
        if statKey == "sum":
            return binData["sum"]
        if statKey == "avg":
            return binData["avg"]
        if statKey == "stddev":
            return binData["stddev"] if binData["count"] > 1 else None
        if statKey == "min":
            return binData["min"]
        if statKey == "max":
            return binData["max"]
        return binData["count"]

    def formatStatCell(self, value, statKey, valueKey, decimals):
        if value is None:
            return ""
        if valueKey is not None or statKey == "count":
            return str(int(value))
        return self.formatNumber(value, decimals)

    def buildSubtitle(self, elementIdentifier):
        parts = []
        attributeField = self.cbAttribute.currentData(Qt.ItemDataRole.UserRole)
        if attributeField:
            prettyAttribute = self.fieldUtils.getProperty(self.elementForField(elementIdentifier, attributeField), attributeField) or attributeField
            condition = self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or ""
            if condition == "Range":
                fromText = self.leFrom.text().strip() or "…"
                toText = self.leTo.text().strip() or "…"
                parts.append("{} {} {} - {}".format(prettyAttribute, self.tr("Range"), fromText, toText))
            elif condition and condition != "All":
                valueText = self.cbValue.currentText().strip()
                if valueText:
                    parts.append("{} {} {}".format(prettyAttribute, condition, valueText))
        if self.cbSelectedElements.isChecked():
            parts.append(self.tr("Only selected elements"))
        notes = []
        if self.lastNullCount:
            notes.append(self.tr("{0} nulls excluded").format(self.lastNullCount))
        if self.lastOutOfRangeCount:
            notes.append(self.tr("{0} out-of-range excluded").format(self.lastOutOfRangeCount))
        if notes:
            parts.append("(" + "; ".join(notes) + ")")
        return "; ".join(parts)

    def formatNumber(self, value, decimals=None):
        if value is None:
            return ""
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return str(value)
        if decimals is not None:
            formatted = "{:.{}f}".format(numericValue, decimals)
            return "0" if formatted == "-0" else formatted
        if numericValue == int(numericValue) and abs(numericValue) < 1e9:
            return str(int(numericValue))
        return "{:g}".format(numericValue)

    def formatLikeAvg(self, value, avgText):
        if value is None:
            return ""
        decimals = len(avgText.split(".")[1]) if "." in avgText else 0
        return "{:.{}f}".format(float(value), decimals)

    def populateTable(self, bins, prettyClassify, prettyProperty, propertyUnit, elementIdentifier, propertyField, groupHeader=None, groupLabel=None, includeTotal=True):
        if self.isEnumeratedTarget:
            self.populateEnumeratedTable(bins, prettyClassify, prettyProperty, includeTotal=includeTotal)
        else:
            self.populateNumericTable(bins, prettyClassify, prettyProperty, propertyField, elementIdentifier, includeTotal=includeTotal)
        if groupHeader is not None and groupLabel is not None:
            self.insertSelectedGroupColumn(groupHeader, groupLabel)

    def insertSelectedGroupColumn(self, header, groupLabel):
        self.tbExcel.insertColumn(1)
        self.tbExcel.setHorizontalHeaderItem(1, QTableWidgetItem(header))
        totalRow = self.tbExcel.rowCount() - 1
        for row in range(self.tbExcel.rowCount()):
            self.setTableItem(row, 1, groupLabel, bold=row == totalRow)
        self.tbExcel.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

    def buildSecondClassMatrix(self, bins, propertyLayer, propertyField, classifyField, breaks, secondField,
                               secondBreaks, featureRequest, prettyClassify, prettySecond,
                               prettyProperty, useSum, propertyDecimals=0):
        rowCount = len(bins)
        colCount = len(self._secondClassBins)
        cells = [[self.makeBin(label="", lo=None, hi=None, category=None) for _ in range(colCount)] for _ in range(rowCount)]
        allColumn = [self.makeBin(label="", lo=None, hi=None, category=None) for _ in range(rowCount)]
        context = self._analysisContext
        featureIterator = propertyLayer.getFeatures(featureRequest) if featureRequest is not None else propertyLayer.getFeatures()
        for feature in featureIterator:
            if not self.featurePassesResultFilter(context, feature):
                continue
            classValue = self.contextFieldValue(context, feature, classifyField)
            if classValue is None:
                continue
            primaryIndex = self.findBinIndex(bins, classValue, breaks["type"])
            if primaryIndex is None:
                continue
            propertyValue = self.contextFieldValue(context, feature, propertyField)
            if propertyValue is None:
                continue
            enumeratedValue = propertyValue
            self.accumulateValue(allColumn[primaryIndex], propertyValue, enumeratedValue)
            secondValue = self.contextFieldValue(context, feature, secondField)
            if secondValue is None:
                continue
            secondIndex = self.findBinIndex(self._secondClassBins, secondValue, secondBreaks["type"])
            if secondIndex is None:
                continue
            self.accumulateValue(cells[primaryIndex][secondIndex], propertyValue, enumeratedValue)
        for row in cells:
            self.finalizeBins(row)
        self.finalizeBins(allColumn)
        self._tableMatrix = {
            "rowLabels": [binData.get("label", "") for binData in bins],
            "secondLabels": [binData.get("label", "") for binData in self._secondClassBins],
            "cells": cells,
            "allColumn": allColumn,
            "useSum": useSum,
            "isEnumeratedTarget": self.isEnumeratedTarget,
            "prettyClassify": prettyClassify,
            "prettySecond": prettySecond,
            "prettyProperty": prettyProperty,
            "decimals": propertyDecimals,
        }

    def populateMatrixTable(self):
        matrix = self._tableMatrix
        if not matrix:
            return
        kind, key = self.cbTableStatistic.currentData(Qt.ItemDataRole.UserRole) or ("stat", "count")
        statKey = key if kind == "stat" else "count"
        valueKey = key if kind == "value" else None
        rowLabels = matrix["rowLabels"]
        secondLabels = matrix["secondLabels"]
        cells = matrix["cells"]
        allColumn = matrix["allColumn"]
        decimals = matrix.get("decimals", 0)
        cornerHeader = "{} / {}".format(
            self.shortPropertyName(matrix["prettyClassify"]), self.shortPropertyName(matrix["prettySecond"])
        )
        headers = [cornerHeader, self.tr("All")] + list(secondLabels)
        self.tbExcel.setColumnCount(len(headers))
        self.tbExcel.setHorizontalHeaderLabels(headers)
        self.tbExcel.setRowCount(len(rowLabels) + 1)

        for rowIndex, label in enumerate(rowLabels):
            self.setTableItem(rowIndex, 0, label)
            allValue = self.binStatValue(allColumn[rowIndex], statKey, valueKey)
            self.setTableItem(rowIndex, 1, self.formatStatCell(allValue, statKey, valueKey, decimals))
            for colIndex, cellBin in enumerate(cells[rowIndex]):
                value = self.binStatValue(cellBin, statKey, valueKey)
                self.setTableItem(rowIndex, colIndex + 2, self.formatStatCell(value, statKey, valueKey, decimals))

        totalRow = len(rowLabels)
        self.setTableItem(totalRow, 0, self.tr("Total"), bold=True)
        allTotal = self.binStatValue(self.combineBins(allColumn), statKey, valueKey)
        self.setTableItem(totalRow, 1, self.formatStatCell(allTotal, statKey, valueKey, decimals), bold=True)
        for colIndex in range(len(secondLabels)):
            columnBins = [cells[rowIndex][colIndex] for rowIndex in range(len(rowLabels))]
            columnTotal = self.binStatValue(self.combineBins(columnBins), statKey, valueKey)
            self.setTableItem(totalRow, colIndex + 2, self.formatStatCell(columnTotal, statKey, valueKey, decimals), bold=True)

        header = self.tbExcel.horizontalHeader()
        header.setMinimumSectionSize(50)
        header.setStretchLastSection(False)
        for column in range(self.tbExcel.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            minimumWidth = 80 if column == 0 else 50
            columnWidth = max(self.tbExcel.sizeHintForColumn(column) + 12, header.sectionSizeHint(column), minimumWidth)
            self.tbExcel.setColumnWidth(column, columnWidth)
        self.captureTableBaseWidths()
        self.tbExcel.verticalHeader().setVisible(False)

    def shortPropertyName(self, name):
        return name if len(name) <= 5 else name[:4] + "."

    def captureTableBaseWidths(self):
        # Content widths are the floor; extra dialog width is shared out on resize
        self._tableBaseWidths = [self.tbExcel.columnWidth(column) for column in range(self.tbExcel.columnCount())]
        self.stretchTableColumns()

    def stretchTableColumns(self):
        baseWidths = self._tableBaseWidths
        if not baseWidths or self.tbExcel.columnCount() != len(baseWidths):
            return
        totalBase = sum(baseWidths)
        if totalBase <= 0:
            return
        extra = self.tbExcel.viewport().width() - totalBase
        if extra <= 0:
            for column, baseWidth in enumerate(baseWidths):
                self.tbExcel.setColumnWidth(column, baseWidth)
            return
        assigned = 0
        for column, baseWidth in enumerate(baseWidths):
            add = extra * baseWidth // totalBase
            if column == len(baseWidths) - 1:
                add = extra - assigned
            assigned += add
            self.tbExcel.setColumnWidth(column, baseWidth + add)

    def populateNumericTable(self, bins, prettyClassify, prettyProperty, propertyField, elementIdentifier, includeTotal=True):
        propertyDecimals = self.propertyDecimalsFor(elementIdentifier, propertyField)
        useSum = self.usesSumColumn(propertyField, elementIdentifier)
        if useSum:
            headers = [prettyClassify, self.tr("Count"), self.tr("Sum"), self.tr("Avg"), self.tr("Min"), self.tr("Max")]
        else:
            headers = [prettyClassify, self.tr("Count"), self.tr("Avg"), self.tr("Min"), self.tr("Max"), self.tr("StdD")]
        self.tbExcel.setColumnCount(len(headers))
        self.tbExcel.setHorizontalHeaderLabels(headers)
        self.tbExcel.setRowCount(len(bins) + (1 if includeTotal else 0))

        totalCount = 0
        totalSum = 0.0
        totalSumOfSquares = 0.0
        totalMin = None
        totalMax = None

        for rowIndex, binData in enumerate(bins):
            avgText = self.formatNumber(binData["avg"], propertyDecimals) if binData["count"] else ""
            self.setTableItem(rowIndex, 0, binData.get("label", ""))
            self.setTableItem(rowIndex, 1, str(binData["count"]))
            minText = self.formatNumber(binData["min"], propertyDecimals) if binData["min"] is not None else ""
            maxText = self.formatNumber(binData["max"], propertyDecimals) if binData["max"] is not None else ""
            if useSum:
                self.setTableItem(rowIndex, 2, self.formatNumber(binData["sum"], propertyDecimals) if binData["count"] else "")
                self.setTableItem(rowIndex, 3, avgText)
                self.setTableItem(rowIndex, 4, minText)
                self.setTableItem(rowIndex, 5, maxText)
            else:
                self.setTableItem(rowIndex, 2, avgText)
                self.setTableItem(rowIndex, 3, minText)
                self.setTableItem(rowIndex, 4, maxText)
                self.setTableItem(rowIndex, 5, self.formatLikeAvg(binData["stddev"], avgText) if binData["count"] > 1 else "")
            totalCount += binData["count"]
            totalSum += binData["sum"]
            totalSumOfSquares += binData["sumOfSquares"]
            if binData["min"] is not None and (totalMin is None or binData["min"] < totalMin):
                totalMin = binData["min"]
            if binData["max"] is not None and (totalMax is None or binData["max"] > totalMax):
                totalMax = binData["max"]

        totalAvg = totalSum / totalCount if totalCount else 0.0
        totalStdDev = 0.0
        if totalCount > 1:
            variance = max(0.0, (totalSumOfSquares - totalCount * totalAvg * totalAvg) / (totalCount - 1))
            totalStdDev = math.sqrt(variance)

        if includeTotal:
            totalRow = len(bins)
            totalAvgText = self.formatNumber(totalAvg, propertyDecimals) if totalCount else ""
            totalMinText = self.formatNumber(totalMin, propertyDecimals) if totalMin is not None else ""
            totalMaxText = self.formatNumber(totalMax, propertyDecimals) if totalMax is not None else ""
            self.setTableItem(totalRow, 0, self.tr("Total"), bold=True)
            self.setTableItem(totalRow, 1, str(totalCount), bold=True)
            if useSum:
                self.setTableItem(totalRow, 2, self.formatNumber(totalSum, propertyDecimals), bold=True)
                self.setTableItem(totalRow, 3, totalAvgText, bold=True)
                self.setTableItem(totalRow, 4, totalMinText, bold=True)
                self.setTableItem(totalRow, 5, totalMaxText, bold=True)
            else:
                self.setTableItem(totalRow, 2, totalAvgText, bold=True)
                self.setTableItem(totalRow, 3, totalMinText, bold=True)
                self.setTableItem(totalRow, 4, totalMaxText, bold=True)
                self.setTableItem(totalRow, 5, self.formatLikeAvg(totalStdDev, totalAvgText) if totalCount > 1 else "", bold=True)

        header = self.tbExcel.horizontalHeader()
        header.setStretchLastSection(False)
        for column in range(self.tbExcel.columnCount()):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            columnWidth = max(self.tbExcel.sizeHintForColumn(column) + 12, header.sectionSizeHint(column), 60)
            self.tbExcel.setColumnWidth(column, columnWidth)
        self.captureTableBaseWidths()
        self.tbExcel.verticalHeader().setVisible(False)

    def populateEnumeratedTable(self, bins, prettyClassify, prettyProperty, includeTotal=True):
        headers = [prettyClassify, self.tr("Count"), prettyProperty]
        self.tbExcel.setColumnCount(len(headers))
        self.tbExcel.setHorizontalHeaderLabels(headers)
        self.tbExcel.setRowCount(len(bins) + (1 if includeTotal else 0))

        totalCount = 0
        totalValues = set()
        for rowIndex, binData in enumerate(bins):
            sortedValues = sorted(binData["values"], key=lambda item: str(item))
            joinedFull = ", ".join(sortedValues)
            joinedDisplay = self.truncateEnumString(joinedFull)
            self.setTableItem(rowIndex, 0, binData.get("label", ""))
            self.setTableItem(rowIndex, 1, str(binData["count"]))
            item = QTableWidgetItem(joinedDisplay)
            item.setToolTip(self.truncateEnumString(joinedFull))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbExcel.setItem(rowIndex, 2, item)
            totalCount += binData["count"]
            totalValues.update(binData["values"])

        if includeTotal:
            totalSorted = sorted(totalValues, key=lambda item: str(item))
            totalJoinedFull = ", ".join(totalSorted)
            totalJoined = self.truncateEnumString(totalJoinedFull)
            totalRow = len(bins)
            self.setTableItem(totalRow, 0, self.tr("Total"), bold=True)
            self.setTableItem(totalRow, 1, str(totalCount), bold=True)
            totalItem = QTableWidgetItem(totalJoined)
            totalItem.setToolTip(self.truncateEnumString(totalJoinedFull))
            totalItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            font = totalItem.font()
            font.setBold(True)
            totalItem.setFont(font)
            totalItem.setBackground(QBrush(QColor(255, 248, 220)))
            self.tbExcel.setItem(totalRow, 2, totalItem)

        header = self.tbExcel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        self._tableBaseWidths = []
        self.tbExcel.verticalHeader().setVisible(False)

    def truncateEnumString(self, text):
        if not text:
            return ""
        if len(text) <= ENUM_TEXT_LIMIT:
            return text
        return text[: ENUM_TEXT_LIMIT - 1] + "…"

    def propertyDecimalsFor(self, elementIdentifier, propertyField):
        return self.fieldUtils.getDecimals(self.elementForField(elementIdentifier, propertyField), propertyField, default=2)

    def usesSumColumn(self, prop, elementIdentifier):
        if prop == "Length" and elementIdentifier == "qgisred_pipes":
            return True
        if prop == "HeadLoss":
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category == "Link" or (elementIdentifier or "").startswith("qgisred_link"):
                return True
        if prop == "BaseDem" and elementIdentifier == "qgisred_junctions":
            return True
        if prop == "BaseValue" and elementIdentifier == "qgisred_demands":
            return True
        if prop == "BaseDemand" and elementIdentifier == "qgisred_serviceconnections":
            return True
        if prop == "Demand":
            category = ELEMENT_RESULT_CATEGORY.get(elementIdentifier)
            if category == "Node" or (elementIdentifier or "").startswith("qgisred_node"):
                return True
        return prop in CUMULATIVE_PROPERTIES

    def setTableItem(self, row, column, text, bold=False):
        item = QTableWidgetItem(text)
        if column > 0:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            item.setBackground(QBrush(QColor(255, 248, 220)))
        self.tbExcel.setItem(row, column, item)

    def importConfig(self):
        fileName, _selectedFilter = QFileDialog.getOpenFileName(
            self,
            self.tr("Import query configuration"),
            str(QgsProject.instance().homePath() or ""),
            "JSON Files (*.json)",
        )
        if not fileName:
            return
        try:
            with open(fileName, "r", encoding="utf-8") as fileHandle:
                data = json.load(fileHandle)
            if data.get("schema") != "qgisred.statistics.v1":
                raise ValueError(self.tr("Unrecognized configuration schema."))
            self.applyConfig(data)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Import failed"), str(ex))

    def applyConfig(self, data):
        self.suspendCascade = True
        elementIndex = self.cbElementType.findData(data.get("elementType", ""))
        if elementIndex >= 0:
            self.cbElementType.setCurrentIndex(elementIndex)
        self.suspendCascade = False
        self.onElementTypeChanged()

        propertyIndex = self.cbProperty.findData(data.get("property", ""))
        if propertyIndex >= 0:
            self.cbProperty.setCurrentIndex(propertyIndex)

        classifyIndex = self.cbClassifiedBy.findData(data.get("classifyBy", ""))
        if classifyIndex >= 0:
            self.cbClassifiedBy.setCurrentIndex(classifyIndex)

        rangedIndex = self.cbRanged.findData(data.get("ranged", ""))
        if rangedIndex >= 0:
            self.cbRanged.setCurrentIndex(rangedIndex)

        classes = data.get("classes")
        if classes is not None:
            self.cbClasses.setValue(int(classes))

        interval = data.get("interval")
        if interval is not None:
            with suppress(TypeError, ValueError):
                self.spinIntervalRange.setValue(float(interval))

        secondClassifyIndex = self.cbSecondClassifiedBy.findData(data.get("secondClassifyBy", ""))
        if secondClassifyIndex >= 0:
            self.cbSecondClassifiedBy.setCurrentIndex(secondClassifyIndex)

        secondRangedIndex = self.cbSecondRanged.findData(data.get("secondRanged", ""))
        if secondRangedIndex >= 0:
            self.cbSecondRanged.setCurrentIndex(secondRangedIndex)

        secondClasses = data.get("secondClasses")
        if secondClasses is not None:
            self.cbSecondClasses.setValue(int(secondClasses))

        secondInterval = data.get("secondInterval")
        if secondInterval is not None:
            with suppress(TypeError, ValueError):
                self.spinSecondIntervalRange.setValue(float(secondInterval))

        # After the classify combos: changing them resets the manual breaks
        self.manualBreaks = list(data.get("manualBreaks") or [])
        self.secondManualBreaks = list(data.get("secondManualBreaks") or [])

        filterData = data.get("filter") or {}
        attributeIndex = self.cbAttribute.findData(filterData.get("attribute", "") or "")
        if attributeIndex >= 0:
            self.cbAttribute.setCurrentIndex(attributeIndex)
        conditionIndex = self.cbCondition.findData(filterData.get("condition", "") or "")
        if conditionIndex >= 0:
            self.cbCondition.setCurrentIndex(conditionIndex)
        self.updateValueWidget()
        valueText = filterData.get("value")
        if valueText is not None:
            valueIndex = self.cbValue.findText(str(valueText))
            if valueIndex >= 0:
                self.cbValue.setCurrentIndex(valueIndex)
            else:
                self.cbValue.setEditText(str(valueText))
        self.leFrom.setText("" if filterData.get("from") is None else str(filterData.get("from")))
        self.leTo.setText("" if filterData.get("to") is None else str(filterData.get("to")))
        self.cbSelectedElements.setChecked(bool(data.get("onlySelected")))

    def exportConfig(self):
        defaultFileName = "qgisred_statistics_query_{}.json".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
        fileName, _selectedFilter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export query configuration"),
            os.path.join(str(QgsProject.instance().homePath() or ""), defaultFileName),
            "JSON Files (*.json)",
        )
        if not fileName:
            return
        try:
            data = {
                "schema": "qgisred.statistics.v1",
                "elementType": self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or "",
                "property": self.cbProperty.currentData(Qt.ItemDataRole.UserRole) or "",
                "classifyBy": self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or "",
                "ranged": self.cbRanged.currentData(Qt.ItemDataRole.UserRole) or "",
                "classes": self.cbClasses.value(),
                "interval": self.spinIntervalRange.value(),
                "manualBreaks": list(self.manualBreaks),
                "secondClassifyBy": self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or "",
                "secondRanged": self.cbSecondRanged.currentData(Qt.ItemDataRole.UserRole) or "",
                "secondClasses": self.cbSecondClasses.value(),
                "secondInterval": self.spinSecondIntervalRange.value(),
                "secondManualBreaks": list(self.secondManualBreaks),
                "filter": {
                    "attribute": self.cbAttribute.currentData(Qt.ItemDataRole.UserRole) or "",
                    "condition": self.cbCondition.currentData(Qt.ItemDataRole.UserRole) or "",
                    "value": self.cbValue.currentText() or None,
                    "from": self.leFrom.text().strip() or None,
                    "to": self.leTo.text().strip() or None,
                },
                "onlySelected": self.cbSelectedElements.isChecked(),
            }
            with open(fileName, "w", encoding="utf-8") as fileHandle:
                json.dump(data, fileHandle, indent=2)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Export failed"), str(ex))

    def exportTableCsv(self):
        if self.tbExcel.rowCount() == 0:
            QMessageBox.information(
                self,
                self.tr("No data"),
                self.tr("Run Analyze before exporting the table."),
            )
            return
        projectName = QgsProject.instance().baseName() or "QGISRed"
        defaultFileName = "{}_statistics_{}.csv".format(projectName, datetime.now().strftime("%Y%m%d_%H%M%S"))
        fileName, _selectedFilter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export table to CSV"),
            os.path.join(str(QgsProject.instance().homePath() or ""), defaultFileName),
            "CSV Files (*.csv)",
        )
        if not fileName:
            return
        try:
            elementIdentifier = self.cbElementType.currentData(Qt.ItemDataRole.UserRole) or ""
            classifyField = self.cbClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or ""
            secondField = self.cbSecondClassifiedBy.currentData(Qt.ItemDataRole.UserRole) or ""
            classifiedByText = self.tr("None")
            if classifyField:
                classifyElement = self.elementForField(elementIdentifier, classifyField)
                classifiedByText = self.fieldUtils.getPluralProperty(classifyElement, classifyField) or classifyField
                classifyUnit = self.fieldUtils.getUnitAbbreviation(classifyElement, classifyField) or ""
                if classifyUnit:
                    classifiedByText = "{} ({})".format(classifiedByText, classifyUnit)
                if secondField and self._tableMatrix:
                    secondElement = self.elementForField(elementIdentifier, secondField)
                    prettySecond = self.fieldUtils.getPluralProperty(secondElement, secondField) or secondField
                    secondUnit = self.fieldUtils.getUnitAbbreviation(secondElement, secondField) or ""
                    if secondUnit:
                        prettySecond = "{} ({})".format(prettySecond, secondUnit)
                    classifiedByText = "{} {} {}".format(classifiedByText, self.tr("and"), prettySecond)
            with open(fileName, "w", newline="", encoding="utf-8") as fileHandle:
                writer = csv.writer(fileHandle)
                fileHandle.write("Project: {}\n".format(projectName))
                fileHandle.write("Element Type: {}\n".format(self.cbElementType.currentText()))
                fileHandle.write("Property: {}\n".format(self.cbProperty.currentText()))
                fileHandle.write("Classified by: {}\n".format(classifiedByText))
                subtitle = self.buildSubtitle(elementIdentifier)
                if subtitle:
                    fileHandle.write("Filter: {}\n".format(subtitle))
                fileHandle.write("\n")
                headers = [
                    self.tbExcel.horizontalHeaderItem(column).text() if self.tbExcel.horizontalHeaderItem(column) else ""
                    for column in range(self.tbExcel.columnCount())
                ]
                writer.writerow(headers)
                for row in range(self.tbExcel.rowCount()):
                    rowData = [
                        self.tbExcel.item(row, column).text() if self.tbExcel.item(row, column) else ""
                        for column in range(self.tbExcel.columnCount())
                    ]
                    writer.writerow(rowData)
        except Exception as ex:
            QMessageBox.critical(self, self.tr("Export failed"), str(ex))
