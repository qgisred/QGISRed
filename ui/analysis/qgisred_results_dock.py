# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDockWidget, QApplication, QColorDialog
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer, QCoreApplication
from qgis.PyQt.QtGui import QPixmap, QIcon, QColor
from qgis.PyQt import uic
from qgis.core import (
    QgsProject, QgsLayerTreeGroup, QgsField, QgsAttributeTableConfig, QgsRenderContext, NULL,
)
from qgis.gui import QgsDualView
from ...compat import sip, QVariantString, QVariantDouble, ATCOL_TYPE_FIELD

from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils, DIR_RESULTS
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils, QGISRED_COMBO_STYLE
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils
from ...tools.qgisred_dependencies import QGISRedDependencies as GISRed

from .qgisred_results_rendering import _ResultsRenderingMixin, time_field_name
from .qgisred_results_data import (_ResultsDataMixin, _STAT_VAR_ALIASES,
                                    NODE_RESULT_FIELDS, LINK_RESULT_FIELDS)
from .qgisred_results_distribution import _ResultsDistributionMixin
from .qgisred_results_appearance import _ResultsAppearanceMixin
from .timeseries_time_utils import simulation_start_clock_seconds, format_civil_time

import os
import glob as _glob
import shutil
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_results_dock.ui"))

class QGISRedResultsDock(
    QDockWidget, FORM_CLASS,
    _ResultsRenderingMixin, _ResultsDataMixin, _ResultsDistributionMixin, _ResultsAppearanceMixin,
):
    # Signals
    timeTextChanged = pyqtSignal(str)
    statisticsModeChanged = pyqtSignal(str)
    simulationFinished = pyqtSignal()
    resultPropertyChanged = pyqtSignal()

    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    Renders = {}
    Computing = False
    TimeLabels = []
    outPath = ""
    _RESULTS_CONTEXTS = [
        "QGISRedResultsDock",
        "_ResultsRenderingMixin",
        "_ResultsDataMixin",
        "QGISRed",
        "AnalysisSection",
    ]

    def tr(self, message):
        """Get the translation for a string searching across multiple results-related contexts."""
        for ctx in self._RESULTS_CONTEXTS:
            result = QCoreApplication.translate(ctx, message)
            if result != message:
                return result
        return message


    def __init__(self, iface):
        """Constructor."""
        super(QGISRedResultsDock, self).__init__(iface.mainWindow())
        self.iface = iface
        self.setupUi(self)

        # Translated labels
        self.lbl_none            = self.tr("None")
        self.lbl_maximum         = self.tr("Maximum")
        self.lbl_minimum         = self.tr("Minimum")
        self.lbl_range           = self.tr("Range")
        self.lbl_average         = self.tr("Average")
        self.lbl_std_deviation   = self.tr("StdDev")
        self.lbl_warning         = self.tr("Warning")
        self.lbl_singlePeriod       = self.tr("Single Period")
        self.lbl_step_times      = self.tr("Step times")
        self.lbl_all_calc_times  = self.tr("All calculation times")
        self.lbl_pressure        = self.tr("Pressure")
        self.lbl_head            = self.tr("Head")
        self.lbl_demand          = self.tr("Demand")
        self.lbl_quality         = self.tr("Quality")
        self.lbl_flow            = self.tr("Flow")
        self.lbl_velocity        = self.tr("Velocity")
        self.lbl_headloss        = self.tr("HeadLoss")
        self.lbl_unit_headloss   = self.tr("Unit HeadLoss")
        self.lbl_friction_factor = self.tr("Friction Factor")
        self.lbl_status          = self.tr("Status")
        self.lbl_reaction_rate   = self.tr("Reaction Rate")
        self.lbl_signed_flow     = self.tr("Flow (Signed)")
        self.lbl_unsigned_flow   = self.tr("Flow (Unsigned)")

        self.stat_variables = {
            self.lbl_maximum: self.tr("Maximum values"),
            self.lbl_minimum: self.tr("Minimum values"),
            self.lbl_range: self.tr("Range values"),
            self.lbl_average: self.tr("Average values"),
            self.lbl_std_deviation: self.tr("Standard deviation values"),
        }

        self.btMoreTime.clicked.connect(self.nextTime)
        self.btEndTime.clicked.connect(self.endTime)
        self.btLessTime.clicked.connect(self.previousTime)
        self.btInitTime.clicked.connect(self.initTime)
        self._applyResultsComboStyle(self.cbTimes)
        self.cbTimes.currentIndexChanged.connect(self.timeChanged)
        self.timeSlider.valueChanged.connect(self.sliderChanged)
        self.timeSlider.sliderMoved.connect(self.sliderDragging)
        self.debounceTimer = QTimer()
        self.debounceTimer.setSingleShot(True)
        self.debounceTimer.timeout.connect(self.applySliderTime)

        self.populateResultStatsComboboxes()
        self.populateVariableComboboxes()
        self.cbResultTimes.currentIndexChanged.connect(self.resultTimesModeChanged)

        self.cbStatistics.currentIndexChanged.connect(self.statisticsChanged)

        self.cbLinks.currentIndexChanged.connect(self.linksChanged)
        self.cbNodes.currentIndexChanged.connect(self.nodesChanged)
        self.cbLinkLabels.clicked.connect(self.linkLabelsClicked)
        self.cbNodeLabels.clicked.connect(self.nodeLabelsClicked)
        self.cbFlowDirections.clicked.connect(self.flowDirectionsClicked)

        # Appearance tab — set symbology label text via tr() so they pick up translations
        self.lbSymbolFactor.setText(self.tr("Nodes") + ":")
        self.lbPipeFactor.setText(self.tr("Links") + ":")
        self.lbArrowFactor.setText(self.tr("Arrows") + ":")

        # Appearance tab — hidden by default, shown only via btAppearance
        self._appearanceTabTitle = self.tabWidget.tabText(2)
        self.tabWidget.removeTab(2)
        self.tabWidget.currentChanged.connect(self._onTabChanged)

        # Appearance tab connections
        self.btAppearance.clicked.connect(self._showAppearanceTab)
        self.spFontSize.valueChanged.connect(self._onLabelStyleChanged)
        self.spNodeDecimals.valueChanged.connect(self._onDecimalsChanged)
        self.spLinkDecimals.valueChanged.connect(self._onDecimalsChanged)
        self.rbColorByRange.toggled.connect(self._onLabelStyleChanged)
        self.cbShowId.clicked.connect(self._onLabelStyleChanged)
        self.dspPipeFactor.valueChanged.connect(self._onSymbolFactorChanged)
        self.dspSymbolFactor.valueChanged.connect(self._onSymbolFactorChanged)
        self.dspArrowFactor.valueChanged.connect(self._onSymbolFactorChanged)
        self.btBgColor.clicked.connect(self._onBgColorClicked)
        self.btClearBgColor.clicked.connect(self._onClearBgColor)
        self.btResetAppearance.clicked.connect(self._onResetAppearance)

        self._setupDistributionCharts()

        self.displayingLinkField = ""
        self.displayingNodeField = ""
        self._statsMode = False
        self._currentStat = self.lbl_none
        self._flowDirectionsUserState = False

        # Appearance tab state
        self._labelFontSize = 10
        self._varDecimals = {}
        self._labelColorByRange = False
        self._labelShowId = False
        self._pipeFactor = 1.0
        self._symbolFactor = 1.0
        self._arrowFactor = 1.0
        self._bgColor = None          # QColor or None
        self._savedBgColor = None     # in-memory only; not persisted

        self.civilMode = False
        self.amPmFormat = False
        self.continuousHoursMode = False
        self._civilLabels = []
        self._startClockSeconds = 0
        self._iconCivil = QIcon(":/images/iconResultsClockCivil.svg")
        self._iconElapsed = QIcon(":/images/iconResultsElapsedTime.svg")
        self._iconAmPm = QIcon(":/images/iconResultsAmPm.svg")
        self._icon24h = QIcon(":/images/iconResults24h.svg")
        self._iconContinuousHrs = QIcon(":/images/iconResultsContinuousHrs.svg")
        self._iconSplitDays = QIcon(":/images/iconResultsSplitDays.svg")
        self.btToggleCivil.setIcon(self._iconCivil)
        self.btAmPm.setIcon(self._iconAmPm)
        self.btElapsedFormat.setIcon(self._iconContinuousHrs)

        self.btToggleCivil.clicked.connect(self.toggleCivilMode)
        self.btAmPm.clicked.connect(self.toggleAmPm)
        self.btElapsedFormat.clicked.connect(self.toggleElapsedFormat)
        self._updateTimeButtonTooltips()

        self._iconGoToStart = QIcon(":/images/iconResultsGoToStart.svg")
        self._iconStepBackward = QIcon(":/images/iconResultsStepBackward.svg")
        self._iconPlayBackward = QIcon(":/images/iconResultsPlayBackward.svg")
        self._iconPause = QIcon(":/images/iconResultsPause.svg")
        self._iconPlayForward = QIcon(":/images/iconResultsPlayForward.svg")
        self._iconStepForward = QIcon(":/images/iconResultsStepForward.svg")
        self._iconGoToEnd = QIcon(":/images/iconResultsGoToEnd.svg")
        self._iconLoop = QIcon(":/images/iconResultsLoop.svg")
        self._iconAppearance = QIcon(":/images/iconProjectSettings.svg")
        self.btAppearance.setIcon(self._iconAppearance)

        self.btInitTime.setIcon(self._iconGoToStart)
        self.btLessTime.setIcon(self._iconStepBackward)
        self.btMoreTime.setIcon(self._iconStepForward)
        self.btEndTime.setIcon(self._iconGoToEnd)
        self.btPlayForward.setIcon(self._iconPlayForward)
        self.btPlayBackward.setIcon(self._iconPlayBackward)
        self.btAnimLoop.setIcon(self._iconLoop)

        self._animPlaying = False
        self._animDirection = 1
        self._animTimer = QTimer()
        self._animTimer.setSingleShot(True)
        self._animTimer.timeout.connect(self._animStep)
        self.btPlayForward.clicked.connect(self._onPlayForwardClicked)
        self.btPlayBackward.clicked.connect(self._onPlayBackwardClicked)
        self.sliderAnimSpeed.valueChanged.connect(self._onAnimSpeedChanged)

        self.statsDisplayWidget.setVisible(False)
        self.timeDisplayWidget.setVisible(True)

        self._showReactRate = True

        # Maps combobox display text → layer field name (keys use self.tr to support translations)
        self._rebuildFieldMaps()

        # Stale results warning
        self._resultsStale = False
        self._staleCheckTimer = QTimer()
        self._staleCheckTimer.setInterval(5000)
        self._staleCheckTimer.timeout.connect(self._checkResultsStale)
        self.visibilityChanged.connect(self._onVisibilityChanged)
        _pixmap = QPixmap(":/images/iconWarning.svg").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbWarnIcon.setPixmap(_pixmap)

        QGISRedUIUtils.applyDockStyle(self, "#1976D2")

        from qgis.PyQt.QtWidgets import QComboBox
        for combo in self.findChildren(QComboBox):
            self._applyResultsComboStyle(combo)

    """Methods"""

    def _applyResultsComboStyle(self, combo):
        QGISRedUIUtils.applyComboStyle(combo)

    def _applyDistributionComboStyle(self, combo):
        from qgis.PyQt.QtWidgets import QComboBox, QSizePolicy

        QGISRedUIUtils.applyComboStyle(combo)
        combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        combo.setMaximumWidth(92)
        combo.setMinimumContentsLength(7)
        combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )

    def _rebuildFieldMaps(self):
        """Rebuild display-label → field-name maps. Call after lbl_quality changes."""
        self._node_field_map = {
            self.lbl_pressure: "Pressure", self.lbl_head: "Head",
            self.lbl_demand: "Demand", self.lbl_quality: "Quality",
        }
        self._link_field_map = {
            self.lbl_flow: "Flow", self.lbl_unsigned_flow: "Flow_Unsig", self.lbl_signed_flow: "Flow_Sig",
            self.lbl_velocity: "Velocity", self.lbl_headloss: "HeadLoss", self.lbl_unit_headloss: "UnitHdLoss",
            self.lbl_friction_factor: "FricFactor", self.lbl_status: "Status",
            self.lbl_reaction_rate: "ReactRate", self.lbl_quality: "Quality",
        }

    """Stale results detection"""
    def _getNetworkFiles(self):
        """Return all network shapefiles and dbf files (excluding Results/).
        Note: _Metadata.txt is excluded — it gets updated by internal operations
        (e.g. opening layers) unrelated to user edits, causing false positives."""
        p = self.ProjectDirectory
        n = self.NetworkName
        return (
            _glob.glob(os.path.join(p, f"{n}_*.shp")) +
            _glob.glob(os.path.join(p, f"{n}_*.dbf"))
        )

    def _checkResultsStale(self):
        """Compare .out mtime with network files; mark stale if any network file is newer."""
        if not os.path.exists(self.outPath):
            return
        out_mtime = os.path.getmtime(self.outPath)
        if any(os.path.getmtime(f) > out_mtime for f in self._getNetworkFiles()):
            self._markResultsStale()

    def _startStaleCheckTimer(self):
        self._resultsStale = False
        self._updateStaleWarning()
        self._checkResultsStale()
        if self.isVisible():
            self._staleCheckTimer.start()

    def _stopStaleCheckTimer(self):
        self._staleCheckTimer.stop()

    def _onVisibilityChanged(self, visible):
        if visible:
            if self.outPath and os.path.exists(self.outPath):
                self._staleCheckTimer.start()
            if getattr(self, '_bgColor', None):
                self._applyBgColor()
        else:
            self._staleCheckTimer.stop()
            self._stopAnimation()
            if self._savedBgColor is not None:
                self.iface.mapCanvas().setCanvasColor(self._savedBgColor)
                self._savedBgColor = None
                self.iface.mapCanvas().refresh()

    def _markResultsStale(self):
        self._resultsStale = True
        self._updateStaleWarning()

    def _updateStaleWarning(self):
        self.staleWarningWidget.setVisible(self._resultsStale)

    # ------------------------------------------------------------------

    def populateResultStatsComboboxes(self):
        self.cbResultTimes.addItems([self.lbl_step_times, self.lbl_all_calc_times])
        self.cbStatistics.addItems([
            self.lbl_none,
            self.lbl_maximum,
            self.lbl_minimum,
            self.lbl_range,
            self.lbl_average,
            self.lbl_std_deviation,
        ])

    def populateVariableComboboxes(self):
        node_variables = [
            self.lbl_none,
            self.lbl_pressure,
            self.lbl_head,
            self.lbl_demand,
            self.lbl_quality,
        ]
        link_variables = [
            self.lbl_none,
            self.lbl_flow,
            self.lbl_velocity,
            self.lbl_headloss,
            self.lbl_unit_headloss,
            self.lbl_friction_factor,
            self.lbl_status,
            self.lbl_reaction_rate,
            self.lbl_quality,
        ]
        self.cbNodes.addItems(node_variables)
        self.cbLinks.addItems(link_variables)

    def isCurrentProject(self):
        """Verifies if the loaded 'Pipes' layer matches the dock's project and network."""
        # Define the expected 'Pipes' layer path for the current project context
        expected_pipes_path = self.generatePath(self.ProjectDirectory, f"{self.NetworkName}_Pipes.shp")
        
        # Check if any loaded layer matches the expected path
        is_correct_project = any(self.getLayerPath(layer) == expected_pipes_path for layer in self.getLayers())
        
        if is_correct_project:
            return True

        # If project mismatch, warn user and close the dock
        message = self.tr("The current project has been changed. Please, try again.")
        QGISRedUIUtils.showGlobalMessage(self.iface, message, level=1, duration=5)
        self.close()
        return False
    
    def updateQualityItemComboboxes(self):
        self.cbLinks.currentIndexChanged.disconnect(self.linksChanged)
        self.cbNodes.currentIndexChanged.disconnect(self.nodesChanged)
        try:
            hide_quality_for_all_times = self.isAllCalculationTimesMode()
            if self.isQualitySimulated and not hide_quality_for_all_times:
                if self.cbNodes.findText(self.lbl_quality) == -1:
                    self.cbNodes.addItem(self.lbl_quality)
                if self._showReactRate:
                    if self.cbLinks.findText(self.lbl_reaction_rate) == -1:
                        # Re-insert Reaction Rate before Quality
                        q_idx = self.cbLinks.findText(self.lbl_quality)
                        if q_idx != -1:
                            self.cbLinks.insertItem(q_idx, self.lbl_reaction_rate)
                        else:
                            self.cbLinks.addItem(self.lbl_reaction_rate)
                else:
                    # Age / Trace: ReactRate has no meaning — remove it
                    rr_idx = self.cbLinks.findText(self.lbl_reaction_rate)
                    if rr_idx != -1:
                        self.cbLinks.removeItem(rr_idx)
                if self.cbLinks.findText(self.lbl_quality) == -1:
                    self.cbLinks.addItem(self.lbl_quality)
            else:
                node_q_idx = self.cbNodes.findText(self.lbl_quality)
                if node_q_idx != -1:
                    self.cbNodes.removeItem(node_q_idx)
                link_rr_idx = self.cbLinks.findText(self.lbl_reaction_rate)
                if link_rr_idx != -1:
                    self.cbLinks.removeItem(link_rr_idx)
                link_q_idx = self.cbLinks.findText(self.lbl_quality)
                if link_q_idx != -1:
                    self.cbLinks.removeItem(link_q_idx)
        finally:
            self.cbLinks.currentIndexChanged.connect(self.linksChanged)
            self.cbNodes.currentIndexChanged.connect(self.nodesChanged)

    def isAllCalculationTimesMode(self):
        return self.cbResultTimes.currentIndex() == 1

    def updateLinksComboboxForStat(self, stat):
        """Adjusts cbLinks items when entering/leaving statistics mode.

        In any stat mode: removes 'Status' (categorical, not meaningful).
        In Average mode: replaces 'Flow' with 'Flow Unsig' and inserts 'Flow Sig' below.
        On restore (stat == 'None'): reverses all changes.
        """
        self.cbLinks.currentIndexChanged.disconnect(self.linksChanged)
        try:
            current_text = self.cbLinks.currentText()

            if stat != self.lbl_none:
                # Remove Status if present
                status_idx = self.cbLinks.findText(self.lbl_status)
                if status_idx != -1:
                    self.cbLinks.removeItem(status_idx)

                if stat == self.lbl_average:
                    flow_idx = self.cbLinks.findText(self.lbl_flow)
                    if flow_idx != -1:
                        self.cbLinks.setItemText(flow_idx, self.lbl_unsigned_flow)
                        self.cbLinks.insertItem(flow_idx + 1, self.lbl_signed_flow)
                        if current_text == self.lbl_flow:
                            self.cbLinks.setCurrentIndex(flow_idx)
                else:
                    # Entering non-Average stat from Average: remove Signed Flow, rename Unsigned Flow → Flow
                    flow_sig_idx = self.cbLinks.findText(self.lbl_signed_flow)
                    if flow_sig_idx != -1:
                        self.cbLinks.removeItem(flow_sig_idx)
                    flow_unsig_idx = self.cbLinks.findText(self.lbl_unsigned_flow)
                    if flow_unsig_idx != -1:
                        self.cbLinks.setItemText(flow_unsig_idx, self.lbl_flow)
                        if current_text in (self.lbl_unsigned_flow, self.lbl_signed_flow):
                            self.cbLinks.setCurrentIndex(flow_unsig_idx)
            else:
                # Restore: remove Signed Flow, rename Unsigned Flow → Flow
                flow_sig_idx = self.cbLinks.findText(self.lbl_signed_flow)
                if flow_sig_idx != -1:
                    self.cbLinks.removeItem(flow_sig_idx)
                flow_unsig_idx = self.cbLinks.findText(self.lbl_unsigned_flow)
                if flow_unsig_idx != -1:
                    self.cbLinks.setItemText(flow_unsig_idx, self.lbl_flow)
                    if current_text in (self.lbl_unsigned_flow, self.lbl_signed_flow):
                        self.cbLinks.setCurrentIndex(flow_unsig_idx)

                # Re-insert Status between Friction Factor and Reaction Rate
                frict_idx = self.cbLinks.findText(self.lbl_friction_factor)
                if frict_idx != -1 and self.cbLinks.findText(self.lbl_status) == -1:
                    self.cbLinks.insertItem(frict_idx + 1, self.lbl_status)
        finally:
            self.cbLinks.currentIndexChanged.connect(self.linksChanged)

    """Paths"""
    def getUniformedPath(self, path):
        return QGISRedFileSystemUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedFileSystemUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedFileSystemUtils().generatePath(folder, fileName)

    def getResultsPath(self):
        return os.path.join(self.ProjectDirectory, DIR_RESULTS)

    """Layers and Groups"""
    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

    def openOrReloadLayerResults(self, scenario, nameLayer=None):
        resultPath = self.getResultsPath()
        utils = QGISRedLayerUtils(resultPath, self.NetworkName + "_" + scenario, self.iface)
        # Navigation utils uses the plain NetworkName so getOrCreateNestedGroup can match
        # the network root group and apply group-visibility logic along the path.
        navUtils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        group = navUtils.getOrCreateNestedGroup([self.NetworkName, "Results", scenario])

        files = [nameLayer] if nameLayer else ["Node", "Link"]
        for file in files:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + scenario + "_" + file + ".shp")
            # Ensure Shapefile exists
            if not os.path.exists(resultLayerPath):
                QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("%1 results not found").replace("%1", self.tr(file)), level=1)
                continue

            existingLayer = next(
                (l for l in self.getLayers() if self.getLayerPath(l) == resultLayerPath), None
            )
            if existingLayer is None:
                # Layer not open yet — open it fresh and prepare its fields
                utils.openLayer(group, file, results=True)
                existingLayer = next(
                    (l for l in self.getLayers() if self.getLayerPath(l) == resultLayerPath), None
                )
            else:
                # Layer already open — reload OGR data (new shapefile written in-place).
                # The DLL writes only base fields; copy2 overwrites the DBF, so the
                # extra result fields added by prepareResultFields are gone.
                # updateFields() syncs the layer's field cache with the provider so that
                # prepareResultFields() correctly detects the missing fields and re-adds them.
                existingLayer.dataProvider().reloadData()
                existingLayer.updateExtents()
                existingLayer.updateFields()
            if existingLayer is not None:
                # Ensure all possible fields are created in the correct order
                self.prepareResultFields(existingLayer, file)

    def removeResults(self):
        resultPath = self.getResultsPath()
        utils = QGISRedLayerUtils(resultPath, self.NetworkName + "_" + self.Scenario, self.iface)
        utils.removeLayers(["Node", "Link"])

    def removeResultLayer(self, nameLayer):
        """Remove a specific result layer from the QGIS legend."""
        self.Scenario = "Base"
        layer = self._findResultLayer(nameLayer)
        if layer:
            QgsProject.instance().removeMapLayer(layer.id())
            self.iface.mapCanvas().refresh()

    def getInputGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateGroup("Inputs")

    def getResultGroup(self):
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        group = utils.getOrCreateGroup("Results")
        group.setItemVisibilityChecked(True)
        return group

    """Fields"""
    def prepareResultFields(self, layer, layer_type):
        """Ensures that all possible result fields exist in the layer in a fixed order."""
        if layer_type == "Node":
            fields_def = NODE_RESULT_FIELDS
            element = "Nodes"
        else:
            fields_def = LINK_RESULT_FIELDS
            element = "Links"

        field_utils = QGISRedFieldUtils()
        existing_fields = layer.fields().names()
        new_fields = []

        type_map = {
            "String": QVariantString,
            "Double": QVariantDouble
        }

        for name, type_str, *extra in fields_def:
            if name not in existing_fields:
                qgs_type = type_map.get(type_str, QVariantString)
                field = QgsField(name, qgs_type)
                if type_str == "Double":
                    field.setLength(20)  # DBF width 20 prevents truncation of large values
                    csv_name = _STAT_VAR_ALIASES.get(name, name)
                    user_dec = getattr(self, '_varDecimals', {}).get(csv_name, None)
                    dec = user_dec if user_dec is not None else field_utils.getDecimals(element, csv_name)
                    field.setPrecision(dec)
                else:
                    length = extra[0] if extra else 0
                    if length:
                        field.setLength(length)
                new_fields.append(field)
        
        if new_fields:
            layer.dataProvider().addAttributes(new_fields)
            layer.updateFields()

    def updateFieldsVisibility(self, layer, layer_type, stats_mode, stat=None):
        """Controls which result fields are visible in the attribute table."""
        config = layer.attributeTableConfig()
        config.update(layer.fields())

        # Result fields in 10-char format (used to avoid hiding non-result columns like ID/Name)
        node_fields_upper = [f[0][:10].upper() for f in NODE_RESULT_FIELDS]
        link_fields_upper = [f[0][:10].upper() for f in LINK_RESULT_FIELDS]
        all_result_fields_upper = set(node_fields_upper + link_fields_upper)

        visible_results = self._computeVisibleFields(layer_type, stats_mode, stat)
        truncated_visible_upper = {v[:10].upper() for v in visible_results}

        # Apply visibility only to result columns; leave ID/Name columns untouched
        columns = config.columns()
        for i in range(len(columns)):
            col = columns[i]
            col_name_upper = col.name.upper()
            if col_name_upper in all_result_fields_upper:
                columns[i].hidden = col_name_upper not in truncated_visible_upper
                columns[i].type = ATCOL_TYPE_FIELD

        config.setColumns(columns)
        layer.setAttributeTableConfig(config)

        # Surgical refresh: only update attribute table windows already open
        if not self.Computing:
            self._applyFieldVisibilityToOpenTables(layer, config)


    def forceFinalFieldsVisibility(self):
        """Re-applies visibility to all result layers after everything has settled."""
        for layerName in ["Node", "Link"]:
            layer = self._findResultLayer(layerName)
            if layer:
                self.updateFieldsVisibility(layer, layerName, self._statsMode, self._currentStat)

    def clearResultFields(self):
        """Clears the values of result fields instead of deleting them to preserve order."""
        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue
            
            # Identify result fields from constants
            fields_def = NODE_RESULT_FIELDS if layerName == "Node" else LINK_RESULT_FIELDS
            fields_to_clear = [f[0] for f in fields_def]
            
            field_indices = []
            for f_name in fields_to_clear:
                idx = target_layer.fields().indexOf(f_name)
                if idx != -1:
                    field_indices.append(idx)
            
            if not field_indices:
                continue
                
            attribute_updates = {}
            for feature in target_layer.getFeatures():
                updates = {idx: NULL for idx in field_indices}
                attribute_updates[feature.id()] = updates
                
            if attribute_updates:
                target_layer.dataProvider().changeAttributeValues(attribute_updates)
                target_layer.dataProvider().dataChanged.emit()
                target_layer.triggerRepaint()
                
        self.displayingLinkField = ""
        self.displayingNodeField = ""

    """UI Elements"""
    def restoreElementsCb(self):
        self.Scenario = "Base"
        self.Computing = True
        self.cbLinks.setCurrentIndex(0)
        self.cbNodes.setCurrentIndex(0)
        self.cbNodeDistribution.setChecked(False)
        self.cbLinkDistribution.setChecked(False)
        self._syncDistributionPanelVisibility()

        for nameLayer in ["Node", "Link"]:
            if self._findResultLayer(nameLayer):
                if "Link" in nameLayer:
                    self.cbLinks.setCurrentIndex(1)  # Default to first result
                else:
                    self.cbNodes.setCurrentIndex(1)  # Default to first result
        self.Computing = False

    """Appearance tab visibility"""

    def _showAppearanceTab(self):
        if self.tabWidget.indexOf(self.tabAppearance) == -1:
            self.tabWidget.addTab(self.tabAppearance, self._appearanceTabTitle)
        self.tabWidget.setCurrentWidget(self.tabAppearance)

    def _onTabChanged(self, index):
        if self.tabWidget.currentWidget() is not self.tabAppearance:
            app_idx = self.tabWidget.indexOf(self.tabAppearance)
            if app_idx != -1:
                self.tabWidget.removeTab(app_idx)

    """Private helpers"""

    def _findResultLayer(self, nameLayer, scenario=None):
        """Return the opened result layer for the given name, or None if not open."""
        scenario = scenario or self.Scenario
        result_path = self.generatePath(
            self.getResultsPath(),
            f"{self.NetworkName}_{scenario}_{nameLayer}.shp"
        )
        for layer in self.getLayers():
            if self.getLayerPath(layer) == result_path:
                return layer
        return None

    def _setComboByField(self, combo, field_map, field_name):
        """Set combo to the item whose field_map value equals field_name. No-op if not found."""
        for label, field in field_map.items():
            if field == field_name:
                idx = combo.findText(label)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
                    return

    def _indexInLabels(self, target, labels_str, civil=False, am_pm=False, continuous=False):
        """Return the index of target in labels_str (';'-separated elapsed strings) after formatting.
        Returns -1 if not found. Requires self._startClockSeconds to be set for civil mode.
        """
        labels = [l for l in labels_str.split(";") if l]
        if civil:
            formatted = [
                format_civil_time(
                    self._elapsedTextToHours(l) or 0.0,
                    self._startClockSeconds,
                    include_seconds=True,
                    am_pm=am_pm,
                )
                for l in labels
            ]
        elif continuous:
            formatted = [self._toContinuousHours(l) for l in labels]
        else:
            formatted = labels
        try:
            return formatted.index(target)
        except ValueError:
            return -1

    def _resolveRestoreTime(self, restore_time):
        """Determine the best (labels_str, use_all_calc, fmt_tuple, time_idx) for restore_time.

        Search order for ambiguous times (h ≤ 23, no suffix, no day prefix):
          1. elapsed  + step-times
          2. elapsed  + all-calc-times
          3. civil 24h + step-times
          4. civil 24h + all-calc-times
        Clearly-identified formats (AM/PM, continuous h>23, "Nd ") only try their natural mode.
        Requires self._startClockSeconds to be set.
        """
        step_labels = self._readTimeLabelsFromOut(all_calc=False)

        if not restore_time or restore_time == self.lbl_singlePeriod:
            return step_labels, False, (False, False, False), 0

        t = restore_time.strip()
        is_ampm = t.upper().endswith("AM") or t.upper().endswith("PM")
        has_days = "d " in t
        try:
            h = int(t.split(":")[0])
            is_continuous = h > 23 and not is_ampm
        except (ValueError, IndexError):
            is_continuous = False

        if is_ampm:
            mode_candidates = [(True, True, False)]
        elif has_days:
            mode_candidates = [(False, False, False)]
        elif is_continuous:
            mode_candidates = [(False, False, True)]
        else:
            # Ambiguous (h ≤ 23): try elapsed first, then civil 24h
            mode_candidates = [(False, False, False), (True, False, False)]

        all_calc_labels = None
        for fmt in mode_candidates:
            civil, am_pm_flag, cont = fmt
            for use_all in (False, True):
                if use_all:
                    if all_calc_labels is None:
                        all_calc_labels = self._readTimeLabelsFromOut(all_calc=True)
                    if all_calc_labels == step_labels:
                        continue  # no .hyd or identical → skip
                    lbls = all_calc_labels
                else:
                    lbls = step_labels
                idx = self._indexInLabels(restore_time, lbls, civil=civil, am_pm=am_pm_flag, continuous=cont)
                if idx >= 0:
                    return lbls, use_all, fmt, idx

        return step_labels, False, (False, False, False), 0

    def _collectSavedState(self):
        """Read dock display state from open result layers and persisted project entries.

        Must be called after setProjectInfo (needs Scenario/NetworkName/ProjectDirectory).
        Returns a dict with keys:
          node_field, link_field  – variable field names (from QgsProject entries)
          stat_text               – cbStatistics item text read from layer 'Statistics' field
          time                    – raw stored 'Time' attribute value (may be formatted)
          node_labels, link_labels, flow_dirs – UI checkbox states
        All values are empty/False/None if no saved state exists.
        """
        scenario = self.Scenario or "Base"
        result = {
            "node_field": "",
            "link_field": "",
            "stat_text": "",
            "time": "",
            "node_labels": False,
            "link_labels": False,
            "flow_dirs": False,
        }

        result["node_field"] = QgsProject.instance().readEntry("QGISRed", f"results_{scenario}_Node", "")[0]
        result["link_field"] = QgsProject.instance().readEntry("QGISRed", f"results_{scenario}_Link", "")[0]

        if not result["node_field"] and not result["link_field"]:
            return result

        node_layer = self._findResultLayer("Node")
        link_layer = self._findResultLayer("Link")

        # Read stat and time from the attribute table of any open result layer
        for layer in (node_layer, link_layer):
            if layer is None:
                continue
            stat_idx = layer.fields().indexOf("Statistics")
            time_idx = layer.fields().indexOf("Time")
            for feature in layer.getFeatures():
                attrs = feature.attributes()
                if not result["stat_text"] and stat_idx >= 0:
                    v = attrs[stat_idx]
                    if v and v != NULL:
                        result["stat_text"] = str(v)
                if not result["time"] and time_idx >= 0:
                    v = attrs[time_idx]
                    if v and v != NULL:
                        result["time"] = str(v)
                break
            if result["stat_text"] and result["time"]:
                break

        # Labels from layer state
        if node_layer:
            result["node_labels"] = node_layer.labelsEnabled()
        if link_layer:
            result["link_labels"] = link_layer.labelsEnabled()

        # Flow directions from persisted project entry (written by flowDirectionsClicked)
        flow_val = QgsProject.instance().readEntry("QGISRed", "results_flow_directions", "false")[0]
        result["flow_dirs"] = flow_val.strip().lower() == "true"

        return result

    def restoreDisplayPreferences(self, projectDir, networkName):
        """Restore variable combos and time-display mode from the previous session.

        Called right after dock creation (before simulate or loadExistingResults).
        loadExistingResults will do its own full restore (including time index) afterwards;
        simulate will keep the combos as-is and reset the time index to 0.
        """
        self.setProjectInfo(projectDir, networkName)
        restore = self._collectSavedState()
        if not restore["node_field"] and not restore["link_field"]:
            return
        self.cbNodes.blockSignals(True)
        self._setComboByField(self.cbNodes, self._node_field_map, restore["node_field"])
        self.cbNodes.blockSignals(False)
        self.cbLinks.blockSignals(True)
        self._setComboByField(self.cbLinks, self._link_field_map, restore["link_field"])
        self.cbLinks.blockSignals(False)
        self.displayingNodeField = restore["node_field"]
        self.displayingLinkField = restore["link_field"]
        self.cbNodeLabels.setChecked(restore["node_labels"])
        self.cbLinkLabels.setChecked(restore["link_labels"])
        self._flowDirectionsUserState = restore["flow_dirs"]
        if restore["flow_dirs"] and self._flowDirectionField() is not None:
            self.cbFlowDirections.setChecked(True)
        self._updateDistributionCheckboxLabels()
        if restore["time"]:
            self._startClockSeconds = simulation_start_clock_seconds(
                self.ProjectDirectory, self.NetworkName,
                binary_path=os.path.join(self.getResultsPath(),
                                         f"{self.NetworkName}_{self.Scenario}.out"),
            )
            _, _, fmt, _ = self._resolveRestoreTime(restore["time"])
            self.civilMode, self.amPmFormat, self.continuousHoursMode = fmt

    def setProjectInfo(self, projectDir, networkName):
        """Set project/network/outPath without touching the UI or loading layers.
        Used by TimeSeries when only outPath is needed."""
        self.ProjectDirectory = projectDir
        self.NetworkName = networkName
        self.Scenario = "Base"
        self.outPath = os.path.join(self.getResultsPath(), f"{self.NetworkName}_{self.Scenario}.out")

    def loadExistingResults(self, projectDir, networkName):
        """Load results from an existing .out file without running GISRed.Compute."""
        self.setProjectInfo(projectDir, networkName)
        restore = self._collectSavedState()

        self.saveCurrentRender()
        self.loadReportFile()
        self.updateQualityOptions()
        self.updateQualityItemComboboxes()  # adjusts combo content (Quality, ReactRate)

        # Set _startClockSeconds early so _resolveRestoreTime can build civil labels
        self._startClockSeconds = simulation_start_clock_seconds(
            self.ProjectDirectory, self.NetworkName,
            binary_path=os.path.join(self.getResultsPath(),
                                     f"{self.NetworkName}_{self.Scenario}.out"),
        )

        if restore["node_field"] or restore["link_field"]:
            # ── Restore path ────────────────────────────────────────────────────────
            # Data and rendering are already in the shapefile/layer style — only
            # restore UI state silently (no signal handlers fired) and set up
            # the time display. No data re-read or re-render needed.

            stat_text = restore["stat_text"]
            if stat_text:
                self._statsMode = True
                self._currentStat = stat_text
                self.updateLinksComboboxForStat(stat_text)  # manages its own signal blocking
                if restore["link_field"]: #Flow_Sign and Flow_Unsig requirement
                    self.cbLinks.blockSignals(True)
                    self._setComboByField(self.cbLinks, self._link_field_map, restore["link_field"])
                    self.cbLinks.blockSignals(False)
                idx = self.cbStatistics.findText(stat_text)
                if idx >= 0:
                    self.cbStatistics.blockSignals(True)
                    self.cbStatistics.setCurrentIndex(idx)
                    self.cbStatistics.blockSignals(False)
                self.lbStatName.setText(self.stat_variables.get(stat_text, stat_text))
                self.lbStatDesc.setText(self.tr("for %1").replace("%1", self.cbResultTimes.currentText().lower()))
            else:
                self._statsMode = False
                self._currentStat = self.lbl_none

            # cbNodes, cbLinks, displayingNodeField/LinkField, civilMode/amPmFormat/continuousHoursMode
            # are already set by restoreDisplayPreferences() called from _initResultsDock.

            final_labels, use_all_calc, fmt, time_idx = self._resolveRestoreTime(restore["time"])
            if use_all_calc:
                self.cbResultTimes.blockSignals(True)
                self.cbResultTimes.setCurrentIndex(1)
                self.cbResultTimes.blockSignals(False)
                self.updateQualityItemComboboxes()
            self._applyTimeDisplay(final_labels, restore_format=fmt, restore_idx=time_idx)
            self.Computing = False
            self.iface.actionMapTips().setChecked(True)
        else:
            # ── Default path: no saved state ─────────────────────────────────────────
            self.applyStatisticFromOptions()
            self.openBaseResults(self._readTimeLabelsFromOut())
        self._loadAppearanceSettings()
        self._startStaleCheckTimer()
        self.show()
        self.simulationFinished.emit()
        netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
        if netGroup is not None:
            for child in netGroup.children():
                if isinstance(child, QgsLayerTreeGroup):
                    groupId = child.customProperty("qgisred_identifier")
                    if groupId != "qgisred_results" and child.name() != "Results":
                        child.setItemVisibilityChecked(False)

    def applyStatisticFromOptions(self):
        statistic_value, _ = QgsProject.instance().readEntry("QGISRed", "project_statistics", "NONE")

        stat_map = {
            "NONE": self.lbl_none,
            "MAXIMUM": self.lbl_maximum,
            "MINIMUM": self.lbl_minimum,
            "RANGE": self.lbl_range,
            "AVERAGE": self.lbl_average,
        }
        translated_stat = stat_map.get(statistic_value.strip().upper(), self.lbl_none)
        idx = self.cbStatistics.findText(translated_stat)
        if idx >= 0 and self.cbStatistics.currentIndex() != idx:
            self.cbStatistics.setCurrentIndex(idx)

    def updateQualityOptions(self):
        self.isQualitySimulated = QGISRedProjectUtils.getQualityModel().upper() != "NONE"

        new_lbl = QGISRedProjectUtils.getQualityDisplayName() if self.isQualitySimulated else self.tr("Quality")
        self._showReactRate = QGISRedProjectUtils.showReactRate() if self.isQualitySimulated else False

        if new_lbl != self.lbl_quality:
            # Rename existing combo items in place before updating the label
            for cb in (self.cbNodes, self.cbLinks):
                idx = cb.findText(self.lbl_quality)
                if idx != -1:
                    cb.setItemText(idx, new_lbl)
            self.lbl_quality = new_lbl
            self._rebuildFieldMaps()

    def _flowDirectionField(self):
        """Return the link field name whose sign determines arrow direction, or None if N/A."""
        if not self._statsMode:
            return "Flow"
        current_link = self.cbLinks.currentText()
        if self._currentStat in (self.lbl_minimum, self.lbl_maximum):
            return {
                self.lbl_flow:          "Flow",
                self.lbl_velocity:      "Velocity",
                self.lbl_headloss:      "HeadLoss",
                self.lbl_unit_headloss: "UnitHdLoss",
            }.get(current_link)
        if self._currentStat == self.lbl_average:
            return "Flow_Sig" if current_link == self.lbl_signed_flow else None
        return None  # Range, StdDev — no direction concept

    def _setModeWidgetsVisibility(self, is_stats_mode, is_temporal=True):
        """Show/hide time vs statistics widgets according to the current display mode."""
        self.statsDisplayWidget.setVisible(is_stats_mode)
        self.timeDisplayWidget.setVisible(not is_stats_mode)
        has_direction = self._flowDirectionField() is not None
        self.cbFlowDirections.setVisible(has_direction)
        if has_direction:
            self.cbFlowDirections.setEnabled(True)
            self.cbFlowDirections.setChecked(self._flowDirectionsUserState)
        self.timeControlsWidget.setVisible(not is_stats_mode and is_temporal)

    """Civil time display helpers"""

    def _updateTimeButtonTooltips(self):
        self.btToggleCivil.setToolTip(self.tr("Elapsed time") if self.civilMode else self.tr("Civil hour"))
        self.btAmPm.setToolTip(self.tr("24h format") if self.amPmFormat else self.tr("am/pm format"))
        self.btElapsedFormat.setToolTip(self.tr("dd hh:mm:ss format") if self.continuousHoursMode else self.tr("HH:mm:ss format"))

    def _elapsedTextToHours(self, text):
        text = (text or "").strip()
        if not text or text == self.lbl_singlePeriod:
            return 0.0
        try:
            days = 0
            hms_text = text
            if "d" in text:
                parts = text.split()
                days = int(parts[0].replace("d", ""))
                hms_text = parts[1]
            hms = hms_text.split(":")
            if len(hms) == 2:
                return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60) / 3600.0
            if len(hms) != 3:
                return None
            return (days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])) / 3600.0
        except Exception:
            return None

    def _buildCivilLabels(self):
        if not self.TimeLabels or (len(self.TimeLabels) == 1 and self.TimeLabels[0] == self.lbl_singlePeriod):
            return []
        return [
            format_civil_time(
                self._elapsedTextToHours(t) or 0.0,
                self._startClockSeconds,
                include_seconds=True,
                am_pm=self.amPmFormat,
            )
            for t in self.TimeLabels
        ]

    def _toContinuousHours(self, elapsed_text):
        """Convert 'Xd H:MM:SS' or 'H:MM:SS' to total-hours 'H:MM:SS' with no day prefix."""
        if elapsed_text == self.lbl_singlePeriod:
            return elapsed_text
        hours = self._elapsedTextToHours(elapsed_text)
        if hours is None:
            return elapsed_text
        total_seconds = round(hours * 3600)
        total_h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        if s == 0:
            return f"{total_h}:{m:02d}"
        return f"{total_h}:{m:02d}:{s:02d}"

    def _updateCivilDisplay(self, elapsed_text):
        is_single = (elapsed_text == self.lbl_singlePeriod)
        has_multiple = len(self.TimeLabels) > 1

        if self.civilMode and self._civilLabels:
            hours = self._elapsedTextToHours(elapsed_text)
            civil_text = format_civil_time(
                hours or 0.0, self._startClockSeconds,
                include_seconds=True, am_pm=self.amPmFormat,
            )
            self.lbTime.setText(civil_text)
        elif self.continuousHoursMode:
            self.lbTime.setText(self._toContinuousHours(elapsed_text))
        else:
            self.lbTime.setText(elapsed_text)

        show_toggle = not is_single and has_multiple
        self.btToggleCivil.setVisible(show_toggle)
        self.btAmPm.setVisible(show_toggle and self.civilMode)
        self.btElapsedFormat.setVisible(show_toggle and not self.civilMode)

    def _refreshComboboxItems(self):
        current_index = self.cbTimes.currentIndex()
        self.cbTimes.blockSignals(True)
        try:
            self.cbTimes.clear()
            if self.civilMode and self._civilLabels:
                labels = self._civilLabels
            elif self.continuousHoursMode:
                labels = [self._toContinuousHours(t) for t in self.TimeLabels]
            else:
                labels = self.TimeLabels
            for lbl in labels:
                self.cbTimes.addItem(lbl)
            self.cbTimes.setCurrentIndex(current_index)
        finally:
            self.cbTimes.blockSignals(False)

    def toggleCivilMode(self):
        self.civilMode = not self.civilMode
        self.btToggleCivil.setIcon(self._iconElapsed if self.civilMode else self._iconCivil)
        self._updateTimeButtonTooltips()
        self._refreshComboboxItems()
        idx = self.cbTimes.currentIndex()
        elapsed = self.TimeLabels[idx] if 0 <= idx < len(self.TimeLabels) else ""
        self._updateCivilDisplay(elapsed)
        self._updateTimeFieldInLayers()
        self.timeTextChanged.emit(elapsed)

    def toggleElapsedFormat(self):
        self.continuousHoursMode = not self.continuousHoursMode
        self.btElapsedFormat.setIcon(self._iconSplitDays if self.continuousHoursMode else self._iconContinuousHrs)
        self._updateTimeButtonTooltips()
        self._refreshComboboxItems()
        idx = self.cbTimes.currentIndex()
        elapsed = self.TimeLabels[idx] if 0 <= idx < len(self.TimeLabels) else ""
        self._updateCivilDisplay(elapsed)
        self._updateTimeFieldInLayers()
        self.timeTextChanged.emit(elapsed)

    def toggleAmPm(self):
        self.amPmFormat = not self.amPmFormat
        self.btAmPm.setIcon(self._icon24h if self.amPmFormat else self._iconAmPm)
        self._updateTimeButtonTooltips()
        self._civilLabels = self._buildCivilLabels()
        if self.civilMode:
            self._refreshComboboxItems()
        idx = self.cbTimes.currentIndex()
        elapsed = self.TimeLabels[idx] if 0 <= idx < len(self.TimeLabels) else ""
        self._updateCivilDisplay(elapsed)
        self._updateTimeFieldInLayers()
        self.timeTextChanged.emit(elapsed)

    def _computeVisibleFields(self, layer_type, stats_mode, stat=None):
        """Return the set of result field names that should be visible for the given mode."""
        visible = set()
        all_calc_times = self.isAllCalculationTimesMode()
        if not stats_mode:
            visible.add("Time")
            if layer_type == "Node":
                visible.update(["Pressure", "Head", "Demand"])
                if self.isQualitySimulated and not all_calc_times:
                    visible.add("Quality")
            else:
                visible.update(["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor"])
                if self.isQualitySimulated and not all_calc_times:
                    visible.update(["ReactRate", "Quality"])
        else:
            visible.add("Statistics")
            if layer_type == "Node":
                visible.update(["Pressure", "Head", "Demand"])
                if self.isQualitySimulated:
                    visible.add("Quality")
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible.update(["Time_H", "Time_D"])
                    if self.isQualitySimulated:
                        visible.add("Time_Q")
            else:
                visible.update(["Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor"])
                if self.isQualitySimulated:
                    visible.update(["ReactRate", "Quality"])
                if stat == self.lbl_average:
                    visible.discard("Flow")
                    visible.update(["Flow_Unsig", "Flow_Sig"])
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible.add("Time_H")
                    if self.isQualitySimulated:
                        visible.add("Time_Q")
        return visible

    def _applyFieldVisibilityToOpenTables(self, layer, config):
        """Refresh attribute table config in any attribute table window already open for this layer."""
        layer_id = layer.id()
        refreshed_count = 0
        cast_map = {"QgsDualView": QgsDualView}
        for widget in QApplication.instance().allWidgets():
            cls = widget.metaObject().className()
            if cls not in cast_map:
                continue
            try:
                typed = sip.cast(widget, cast_map[cls])
                # layer() is not in QgsDualView in QGIS 3.4, but masterModel().layer() is
                w_layer = typed.masterModel().layer()
                if w_layer and w_layer.id() == layer_id:
                    typed.setAttributeTableConfig(config)
                    refreshed_count += 1
            except Exception:
                pass
        if refreshed_count > 0:
            QApplication.processEvents()

    """Clicked events"""
    def statisticsChanged(self):
        # 1. First, save render BEFORE updating state to new statistic (only if not computing)
        if not self.Computing:
            self.saveCurrentRender()

        # 2. Update state and UI
        new_stat = self.cbStatistics.currentText()
        self._currentStat = new_stat

        _stat_en_key = {
            self.lbl_maximum:       "MAXIMUM",
            self.lbl_minimum:       "MINIMUM",
            self.lbl_range:         "RANGE",
            self.lbl_average:       "AVERAGE",
            self.lbl_std_deviation: "STDDEV",
        }
        QgsProject.instance().writeEntry(
            "QGISRed", "project_statistics", _stat_en_key.get(new_stat, "NONE")
        )

        if new_stat != self.lbl_none:
            self._stopAnimation()
            self._statsMode = True
            self.updateLinksComboboxForStat(new_stat)
            result_times = self.cbResultTimes.currentText()
            self.lbStatName.setText(self.stat_variables.get(new_stat, new_stat))
            self.lbStatDesc.setText(self.tr("for %1").replace("%1", result_times.lower()))
            if self.cbFlowDirections.isVisible():
                self._flowDirectionsUserState = self.cbFlowDirections.isChecked()
            self._setModeWidgetsVisibility(True)
        else:
            self._statsMode = False
            self.updateLinksComboboxForStat(self.lbl_none)
            idx = self.cbTimes.currentIndex()
            elapsed = self.TimeLabels[idx] if 0 <= idx < len(self.TimeLabels) else ""
            self._updateCivilDisplay(elapsed)
            self._setModeWidgetsVisibility(False, is_temporal=self.cbTimes.count() > 1)

        # 3. Heavy operations (only if not computing)
        if not self.Computing:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                if self.validationsOpenResult():
                    self.ensureResultsLayersAreOpen()
                    self.clearResultFields()
                    if self._statsMode:
                        self.completeStatsLayers()
                    else:
                        self.completeResultLayers()
                    self.paintIntervalTimeResults(True)
                    
                    # Defer final visibility application to ensure the layer is fully ready
                    # This fixes the issue where opening the table too fast shows all columns
                    QTimer.singleShot(200, self.forceFinalFieldsVisibility)
            finally:
                QApplication.restoreOverrideCursor()
        self.statisticsModeChanged.emit(new_stat if self._statsMode else "")

    def resultTimesModeChanged(self):
        if self.Computing:
            return
        # Ignore mode toggles until project/network/results are initialized.
        if not self.NetworkName or not self.ProjectDirectory or not os.path.exists(self.outPath):
            return

        # Keep variable combos aligned with selected temporal backend.
        self.updateQualityItemComboboxes()

        if self._statsMode:
            result_times = self.cbResultTimes.currentText()
            self.lbStatDesc.setText(self.tr("for %1").replace("%1", result_times.lower()))
            self.resultPropertyChanged.emit()
            return

        labels = self._readTimeLabelsFromOut()
        self.openBaseResults(labels)
        self.resultPropertyChanged.emit()

    def linksChanged(self):
        if self.Computing:
            return

        if self.cbLinks.currentIndex() == 0:
            self.displayingLinkField = ""
            self.removeResultLayer("Link")
            self._updateDistributionCheckboxLabels()
            return

        if not self.validationsOpenResult():
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.saveCurrentRender()
            if self.cbFlowDirections.isVisible():
                self._flowDirectionsUserState = self.cbFlowDirections.isChecked()
            has_direction = self._flowDirectionField() is not None
            self.cbFlowDirections.setVisible(has_direction)
            if has_direction:
                self.cbFlowDirections.setEnabled(True)
                self.cbFlowDirections.setChecked(self._flowDirectionsUserState)
            self.ensureResultsLayersAreOpen()

            # Update visibility when variable changes
            link_layer = self._findResultLayer("Link")
            if link_layer:
                self.updateFieldsVisibility(link_layer, "Link", self._statsMode, self._currentStat)

            self._resetDecimalsForVariable(
                self._link_field_map.get(self.cbLinks.currentText(), ""), "Links", "Link"
            )
            self.paintIntervalTimeResults(True)
            QTimer.singleShot(300, self.forceFinalFieldsVisibility)
        finally:
            QApplication.restoreOverrideCursor()
        self.resultPropertyChanged.emit()

    def nodesChanged(self):
        if self.Computing:
            return

        if self.cbNodes.currentIndex() == 0:
            self.displayingNodeField = ""
            self.removeResultLayer("Node")
            self._updateDistributionCheckboxLabels()
            return

        if not self.validationsOpenResult():
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.saveCurrentRender()
            self.ensureResultsLayersAreOpen()

            # Update visibility when variable changes
            node_layer = self._findResultLayer("Node")
            if node_layer:
                self.updateFieldsVisibility(node_layer, "Node", self._statsMode, self._currentStat)

            self._resetDecimalsForVariable(
                self._node_field_map.get(self.cbNodes.currentText(), ""), "Nodes", "Node"
            )
            self.paintIntervalTimeResults(True)
            QTimer.singleShot(300, self.forceFinalFieldsVisibility)
        finally:
            QApplication.restoreOverrideCursor()
        self.resultPropertyChanged.emit()

    def nodeLabelsClicked(self):
        self.updateLabels("Node")

    def linkLabelsClicked(self):
        self.updateLabels("Link")

    def flowDirectionsClicked(self):
        self._flowDirectionsUserState = self.cbFlowDirections.isChecked()
        if not self.validationsOpenResult():
            QgsProject.instance().writeEntry(
                "QGISRed", "results_flow_directions",
                "true" if self.cbFlowDirections.isChecked() else "false",
            )
            return

        self.ensureResultsLayersAreOpen()

        layer_to_paint = self._findResultLayer("Link")
        if layer_to_paint:
            renderer = layer_to_paint.renderer()
            symbols = renderer.symbols(QgsRenderContext())
            flow_field = self._flowDirectionField()
            for symbol in symbols:
                self.setArrowsVisibility(symbol, layer_to_paint, flow_field)

            layer_to_paint.setRenderer(renderer)
            layer_to_paint.triggerRepaint()

        QgsProject.instance().writeEntry(
            "QGISRed", "results_flow_directions",
            "true" if self.cbFlowDirections.isChecked() else "false",
        )

    def nextTime(self):
        index = self.cbTimes.currentIndex()
        if self.cbTimes.count() - 1 == index:
            self.cbTimes.setCurrentIndex(0)
        else:
            self.cbTimes.setCurrentIndex(index + 1)

    def endTime(self):
        self.cbTimes.setCurrentIndex(self.cbTimes.count() - 1)

    def initTime(self):
        self.cbTimes.setCurrentIndex(0)

    def previousTime(self):
        index = self.cbTimes.currentIndex()
        if index == 0:
            self.cbTimes.setCurrentIndex(self.cbTimes.count() - 1)
        else:
            self.cbTimes.setCurrentIndex(index - 1)

    def _animIntervalMs(self):
        return max(100, 2000 - (self.sliderAnimSpeed.value() - 1) * 200)

    def _onPlayForwardClicked(self):
        if self._animPlaying and self._animDirection == 1:
            self._stopAnimation()
        else:
            self._startAnimation(1)

    def _onPlayBackwardClicked(self):
        if self._animPlaying and self._animDirection == -1:
            self._stopAnimation()
        else:
            self._startAnimation(-1)

    def _startAnimation(self, direction):
        self._stopAnimation()
        self._animDirection = direction
        self._animPlaying = True
        if direction == 1:
            self.btPlayForward.setIcon(self._iconPause)
            self.btPlayForward.setChecked(True)
            self.btPlayBackward.setIcon(self._iconPlayBackward)
            self.btPlayBackward.setChecked(False)
        else:
            self.btPlayBackward.setIcon(self._iconPause)
            self.btPlayBackward.setChecked(True)
            self.btPlayForward.setIcon(self._iconPlayForward)
            self.btPlayForward.setChecked(False)
        self._animTimer.start(self._animIntervalMs())

    def _stopAnimation(self):
        if not self._animPlaying:
            return
        self._animPlaying = False
        self._animTimer.stop()
        self.btPlayForward.setIcon(self._iconPlayForward)
        self.btPlayForward.setChecked(False)
        self.btPlayBackward.setIcon(self._iconPlayBackward)
        self.btPlayBackward.setChecked(False)

    def _animStep(self):
        if not self._animPlaying:
            return
        index = self.cbTimes.currentIndex()
        count = self.cbTimes.count()
        if self._animDirection == 1:
            next_index = index + 1
            if next_index >= count:
                if self.btAnimLoop.isChecked():
                    next_index = 0
                else:
                    self._stopAnimation()
                    return
        else:
            next_index = index - 1
            if next_index < 0:
                if self.btAnimLoop.isChecked():
                    next_index = count - 1
                else:
                    self._stopAnimation()
                    return
        self.cbTimes.setCurrentIndex(next_index)
        if self._animPlaying:
            self._animTimer.start(self._animIntervalMs())

    def _onAnimSpeedChanged(self, value):
        if self._animPlaying:
            self._animTimer.stop()
            self._animTimer.start(self._animIntervalMs())

    def sliderChanged(self):
        if self.timeSlider.isSliderDown():
            return
        if not self.timeSlider.value() == self.cbTimes.currentIndex():
            self.cbTimes.setCurrentIndex(self.timeSlider.value())

    def sliderDragging(self, value):
        elapsed_text = self.TimeLabels[value]
        self._updateCivilDisplay(elapsed_text)
        self.timeTextChanged.emit(elapsed_text)
        self.debounceTimer.start(500)

    def applySliderTime(self):
        index = self.timeSlider.value()
        if index != self.cbTimes.currentIndex():
            self.cbTimes.setCurrentIndex(index)
        else:
            self.timeChanged()

    def timeChanged(self):
        if self.Computing:
            return
        if self._statsMode:
            return

        if not self.validationsOpenResult():
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            self.ensureResultsLayersAreOpen()

            value = self.cbTimes.currentIndex()
            self.timeSlider.setValue(value)

            self.completeResultLayers()

            self.paintIntervalTimeResults(False)
        finally:
            QApplication.restoreOverrideCursor()

    """Main methods"""
    def updateLabels(self, layer_type):
        if not self.validationsOpenResult():
            return

        self.ensureResultsLayersAreOpen()

        checkbox = self.cbNodeLabels if layer_type == "Node" else self.cbLinkLabels
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks
        field_map = self._link_field_map if layer_type == "Link" else self._node_field_map

        layer = self._findResultLayer(layer_type)
        if layer:
            if checkbox.isChecked():
                if combobox.currentIndex() > 0:
                    field = field_map.get(combobox.currentText(), "")
                    if field:
                        is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self.lbl_maximum, self.lbl_minimum)
                        time_field = time_field_name(field, layer_type) if is_min_max_stat else None
                        self.setLayerLabels(layer, field, time_field)
            else:
                layer.setLabelsEnabled(False)
                layer.triggerRepaint()

    def validationsOpenResult(self):
        if not self.isCurrentProject():
            return False

        self.Scenario = "Base"
        resultsPath = self.getResultsPath()
        resultLayersName = ["Node", "Link"]
        for layerName in resultLayersName:
            filename = self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp"
            resultPath = os.path.join(resultsPath, filename)
            if not os.path.exists(resultPath):
                message = self.tr("No %1 results are available").replace("%1", self.tr(layerName))
                QGISRedUIUtils.showGlobalMessage(self.iface, message, level=1, duration=5)
                return False

        return True

    def ensureResultsLayersAreOpen(self):
        """Open or reload result layers based on combobox state."""
        if not self.isCurrentProject():
            return

        self.Scenario = "Base"
        layer_combobox = {"Node": self.cbNodes, "Link": self.cbLinks}
        for nameLayer in ["Node", "Link"]:
            # Don't open a layer if its variable combobox is set to None
            if layer_combobox[nameLayer].currentIndex() == 0:
                continue

            self.openOrReloadLayerResults(self.Scenario, nameLayer)

    def simulate(self, direct, netw):
        self.Computing = True
        self._stopStaleCheckTimer()
        # If there is a new project, reset options
        if not (self.NetworkName == netw and self.ProjectDirectory == direct):
            self.NetworkName = netw
            self.ProjectDirectory = direct

        # Project info
        self.NetworkName = netw
        self.ProjectDirectory = direct

        # Create list with results layers opened
        self.Scenario = "Base"
        self.saveCurrentRender()

        # Run simulation — result layers stay open and are refreshed in-place
        self.simulationProcess()

    def simulationProcess(self):
        # Write results to a temp folder so the DLL never deletes files that other
        # QGIS instances may have open. Python then copies them in-place into Results/,
        # keeping the existing inodes valid for any other open handle.
        tempFolder = tempfile.mkdtemp(prefix="QGISRed_")
        try:
            resMessage = GISRed.Compute(self.ProjectDirectory, self.NetworkName, tempFolder)

            if resMessage == "True":
                resultsPath = self.getResultsPath()
                if not os.path.exists(resultsPath):
                    os.makedirs(resultsPath)
                for fname in os.listdir(tempFolder):
                    shutil.copy2(os.path.join(tempFolder, fname), os.path.join(resultsPath, fname))
        finally:
            shutil.rmtree(tempFolder, ignore_errors=True)

        # Message
        if resMessage == "Cancelled":
            return
        elif resMessage == "False":
            QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage == "True":
            self.outPath = os.path.join(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + ".out")
            self.loadReportFile()
            self.updateQualityOptions()
            self.updateQualityItemComboboxes()
            self.applyStatisticFromOptions()
            self.openBaseResults(self._readTimeLabelsFromOut())
            self._startStaleCheckTimer()
            self.show()
            self.simulationFinished.emit()
            return
        else:
            QGISRedUIUtils.showGlobalMessage(self.iface, resMessage, level=2, duration=5)

        # If some error, close the dock
        self.close()

    def _applyTimeDisplay(self, labels, restore_format=None, restore_idx=None):
        """Set up TimeLabels, cbTimes and all time-display state. Does NOT load or clear data.

        restore_format: (civilMode, amPmFormat, continuousHoursMode) tuple or None to keep current.
        restore_idx:    pre-resolved index into TimeLabels; 0 if omitted.
        """
        time_label_list = labels.split(";")
        self.TimeLabels = []
        self.cbTimes.blockSignals(True)
        self.cbTimes.clear()
        if len(time_label_list) == 1:
            self.TimeLabels.append(self.lbl_singlePeriod)
            self.cbTimes.addItem(self.lbl_singlePeriod)
        else:
            for item in time_label_list:
                self.TimeLabels.append(item)
                self.cbTimes.addItem(item)
        self.cbTimes.blockSignals(False)

        self._startClockSeconds = simulation_start_clock_seconds(
            self.ProjectDirectory, self.NetworkName,
            binary_path=os.path.join(self.getResultsPath(),
                                     f"{self.NetworkName}_{self.Scenario}.out"),
        )

        if restore_format is not None:
            self.civilMode, self.amPmFormat, self.continuousHoursMode = restore_format
        self._civilLabels = self._buildCivilLabels()
        self.btAmPm.setIcon(self._icon24h if self.amPmFormat else self._iconAmPm)
        self.btElapsedFormat.setIcon(self._iconSplitDays if self.continuousHoursMode else self._iconContinuousHrs)
        self.btToggleCivil.setIcon(self._iconElapsed if self.civilMode else self._iconCivil)
        self._updateTimeButtonTooltips()

        self._refreshComboboxItems()
        final_idx = restore_idx if restore_idx is not None else 0
        self.cbTimes.blockSignals(True)
        self.cbTimes.setCurrentIndex(final_idx)
        self.cbTimes.blockSignals(False)
        self.timeSlider.blockSignals(True)
        self.timeSlider.setValue(final_idx)
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        self.timeSlider.blockSignals(False)

        in_stats = self._statsMode
        if not in_stats:
            self._updateCivilDisplay(self.TimeLabels[final_idx])
        self._setModeWidgetsVisibility(in_stats, is_temporal=len(time_label_list) > 1)

    def openBaseResults(self, labels):
        # Select comboboxes item (only when still at "None")
        if self.cbLinks.currentIndex() == 0:
            self.cbLinks.setCurrentIndex(1)
        if self.cbNodes.currentIndex() == 0:
            self.cbNodes.setCurrentIndex(1)

        self._applyTimeDisplay(labels)

        self.Computing = False

        # Open results
        self.openAllResults()

    def openAllResults(self):
        if not self.validationsOpenResult():
            return

        self.openAllResultsProcess()

    def openAllResultsProcess(self):
        # Ensure result layers are opened
        self.ensureResultsLayersAreOpen()

        # Complete attribute table with results (stats or time-step depending on current mode)
        self.clearResultFields()
        if self._statsMode:
            self.completeStatsLayers()
        else:
            self.completeResultLayers()

        self.paintIntervalTimeResults(True)

        # Defer final visibility application to ensure the layer is fully ready
        QTimer.singleShot(200, self.forceFinalFieldsVisibility)

        # Activate map tips
        self.iface.actionMapTips().setChecked(True)


