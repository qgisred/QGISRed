# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QTimer
from PyQt5.QtGui import QPixmap
from qgis.PyQt import uic
from qgis.core import (
    QgsProject, QgsLayerTreeGroup, QgsField, QgsAttributeTableConfig, QgsRenderContext, NULL,
)
from qgis.gui import QgsDualView
import sip

from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils
from ...tools.qgisred_dependencies import QGISRedDependencies as GISRed

from .qgisred_results_rendering import _ResultsRenderingMixin, time_field_name
from .qgisred_results_data import _ResultsDataMixin

import os
import glob as _glob

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_results_dock.ui"))

NODE_RESULT_FIELDS = [
    ("Time", "String", 15),
    ("Statistics", "String", 15),
    ("Pressure", "Double"),
    ("Head", "Double"),
    ("Time_H", "String", 15),
    ("Demand", "Double"),
    ("Time_D", "String", 15),
    ("Quality", "Double"),
    ("Time_Q", "String", 15),
]

LINK_RESULT_FIELDS = [
    ("Time", "String", 15),
    ("Statistics", "String", 15),
    ("Status", "String"),
    ("Flow", "Double"),
    ("Flow_Unsig", "Double"),
    ("Flow_Sig", "Double"),
    ("Velocity", "Double"),
    ("HeadLoss", "Double"),
    ("UnitHdLoss", "Double"),
    ("Time_H", "String", 15),
    ("FricFactor", "Double"),
    ("ReactRate", "Double"),
    ("Quality", "Double"),
    ("Time_Q", "String", 15),
]

class QGISRedResultsDock(QDockWidget, FORM_CLASS, _ResultsRenderingMixin, _ResultsDataMixin):
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
        self.lbl_permanent       = self.tr("Permanent")
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

        comboStyle = """
            QComboBox { 
                background-color: white; 
                combobox-popup: 0;
            }
            QComboBox QAbstractItemView {
                selection-background-color: #3574F0;
                selection-color: white;
                outline: none;
                max-height: 250px;
                qproperty-verticalScrollBarPolicy: ScrollBarAsNeeded;
            }
        """

        self.btMoreTime.clicked.connect(self.nextTime)
        self.btEndTime.clicked.connect(self.endTime)
        self.btLessTime.clicked.connect(self.previousTime)
        self.btInitTime.clicked.connect(self.initTime)
        self.cbTimes.setStyleSheet(comboStyle)
        self.cbTimes.view().setVerticalScrollBarPolicy(0)
        self.cbTimes.currentIndexChanged.connect(self.timeChanged)
        self.timeSlider.valueChanged.connect(self.sliderChanged)
        self.timeSlider.sliderMoved.connect(self.sliderDragging)
        self.debounceTimer = QTimer()
        self.debounceTimer.setSingleShot(True)
        self.debounceTimer.timeout.connect(self.applySliderTime)

        self.populateResultStatsComboboxes()
        self.populateVariableComboboxes()

        self.cbStatistics.currentIndexChanged.connect(self.statisticsChanged)

        self.cbLinks.currentIndexChanged.connect(self.linksChanged)
        self.cbNodes.currentIndexChanged.connect(self.nodesChanged)
        self.cbLinkLabels.clicked.connect(self.linkLabelsClicked)
        self.cbNodeLabels.clicked.connect(self.nodeLabelsClicked)
        self.cbFlowDirections.clicked.connect(self.flowDirectionsClicked)

        self.displayingLinkField = ""
        self.displayingNodeField = ""
        self._statsMode = False
        self._currentStat = self.lbl_none

        self.statsDisplayWidget.setVisible(False)
        self.timeDisplayWidget.setVisible(True)

        # Maps combobox display text → layer field name (keys use self.tr to support translations)
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

        # Stale results warning
        self._resultsStale = False
        self._staleCheckTimer = QTimer()
        self._staleCheckTimer.setInterval(5000)
        self._staleCheckTimer.timeout.connect(self._checkResultsStale)
        self.visibilityChanged.connect(self._onVisibilityChanged)
        _pixmap = QPixmap(":/images/iconWarning.svg").scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbWarnIcon.setPixmap(_pixmap)

    """Methods"""

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
        else:
            self._staleCheckTimer.stop()

    def _markResultsStale(self):
        self._resultsStale = True
        self._updateStaleWarning()

    def _updateStaleWarning(self):
        self.staleWarningWidget.setVisible(self._resultsStale)

    # ------------------------------------------------------------------

    def populateResultStatsComboboxes(self):
        self.cbResultTimes.addItems([self.tr("Report times")])
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
        QGISRedUIUtils.showGlobalMessage(self.iface, self.lbl_warning, message, level=1, duration=5)
        self.close()
        return False
    
    def updateQualityItemComboboxes(self):
        self.cbLinks.currentIndexChanged.disconnect(self.linksChanged)
        self.cbNodes.currentIndexChanged.disconnect(self.nodesChanged)
        try:
            if self.isQualitySimulated:
                if self.cbNodes.findText(self.lbl_quality) == -1:
                    self.cbNodes.addItem(self.lbl_quality)
                if self.cbLinks.findText(self.lbl_quality) == -1:
                    self.cbLinks.addItem(self.lbl_quality)
            else:
                node_q_idx = self.cbNodes.findText(self.lbl_quality)
                if node_q_idx != -1:
                    self.cbNodes.removeItem(node_q_idx)
                link_q_idx = self.cbLinks.findText(self.lbl_quality)
                if link_q_idx != -1:
                    self.cbLinks.removeItem(link_q_idx)
        finally:
            self.cbLinks.currentIndexChanged.connect(self.linksChanged)
            self.cbNodes.currentIndexChanged.connect(self.nodesChanged)

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
        return os.path.join(self.ProjectDirectory, "Results")

    """Layers and Groups"""
    def getLayers(self):
        return QGISRedLayerUtils().getLayers()

    def openLayerResults(self, scenario, nameLayer=None):
        resultPath = self.getResultsPath()
        utils = QGISRedLayerUtils(resultPath, self.NetworkName + "_" + scenario, self.iface)
        resultGroup = self.getResultGroup()
        group = resultGroup.findGroup(scenario)
        if group is None:
            group = resultGroup.addGroup(scenario)
            QGISRedLayerUtils.setGroupIdentifier(group, scenario)

        openedLayersPaths = [self.getLayerPath(l) for l in self.getLayers()]

        files = [nameLayer] if nameLayer else ["Node", "Link"]
        for file in files:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + scenario + "_" + file + ".shp")
            # Ensure Shapefile exists
            if not os.path.exists(resultLayerPath):
                QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("Warning"), self.tr("{} results not found").format(self.tr(file)), level=1)
                continue

            # Open layer if not already open
            if resultLayerPath not in openedLayersPaths:
                utils.openLayer(group, file, results=True)
                # Ensure all possible fields are created in the correct order
                for layer in self.getLayers():
                    if self.getLayerPath(layer) == resultLayerPath:
                        self.prepareResultFields(layer, file)
                        break

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
        else:
            fields_def = LINK_RESULT_FIELDS
            
        existing_fields = layer.fields().names()
        new_fields = []
        
        type_map = {
            "String": QVariant.String,
            "Double": QVariant.Double
        }
        
        for name, type_str, *extra in fields_def:
            if name not in existing_fields:
                qgs_type = type_map.get(type_str, QVariant.String)
                length = extra[0] if extra else 0
                if length:
                    new_fields.append(QgsField(name=name, type=qgs_type, len=length))
                else:
                    new_fields.append(QgsField(name=name, type=qgs_type))
        
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
                columns[i].type = 0  # treat as a field column

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

        for nameLayer in ["Node", "Link"]:
            if self._findResultLayer(nameLayer):
                if "Link" in nameLayer:
                    self.cbLinks.setCurrentIndex(1)  # Default to first result
                else:
                    self.cbNodes.setCurrentIndex(1)  # Default to first result
        self.Computing = False

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

    def _flowDirectionField(self):
        """Return the link field name whose sign determines arrow direction, or None if N/A."""
        if not self._statsMode:
            return "Flow"
        if self._currentStat in (self.lbl_minimum, self.lbl_maximum):
            return "Flow"
        if self._currentStat == self.lbl_average:
            return "Flow_Sig"
        return None  # Range, StdDev — no direction concept

    def _setModeWidgetsVisibility(self, is_stats_mode, is_temporal=True):
        """Show/hide time vs statistics widgets according to the current display mode."""
        self.statsDisplayWidget.setVisible(is_stats_mode)
        self.timeDisplayWidget.setVisible(not is_stats_mode)
        self.cbFlowDirections.setVisible(self._flowDirectionField() is not None)
        self.timeControlsWidget.setVisible(not is_stats_mode and is_temporal)

    def _computeVisibleFields(self, layer_type, stats_mode, stat=None):
        """Return the set of result field names that should be visible for the given mode."""
        visible = set()
        if not stats_mode:
            visible.add("Time")
            if layer_type == "Node":
                visible.update(["Pressure", "Head", "Demand", "Quality"])
            else:
                visible.update(["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"])
        else:
            visible.add("Statistics")
            if layer_type == "Node":
                visible.update(["Pressure", "Head", "Demand", "Quality"])
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible.update(["Time_H", "Time_D", "Time_Q"])
            else:
                visible.update(["Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"])
                if stat == self.lbl_average:
                    visible.discard("Flow")
                    visible.update(["Flow_Unsig", "Flow_Sig"])
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible.update(["Time_H", "Time_Q"])
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
        
        if new_stat != self.lbl_none:
            self._statsMode = True
            self.updateLinksComboboxForStat(new_stat)
            result_times = self.cbResultTimes.currentText()
            self.lbStatName.setText(self.stat_variables.get(new_stat, new_stat))
            self.lbStatDesc.setText(self.tr("for {}").format(result_times.lower()))
            if self.cbFlowDirections.isChecked() and self._flowDirectionField() is None:
                self.cbFlowDirections.setChecked(False)
            self._setModeWidgetsVisibility(True)
        else:
            self._statsMode = False
            self.updateLinksComboboxForStat(self.lbl_none)
            self.lbTime.setText(self.cbTimes.currentText())
            self._setModeWidgetsVisibility(False, is_temporal=self.cbTimes.count() > 1)

        # 3. Heavy operations (only if not computing)
        if not self.Computing:
            QApplication.setOverrideCursor(Qt.WaitCursor)
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

    def linksChanged(self):
        if self.Computing:
            return

        if self.cbLinks.currentIndex() == 0:
            self.displayingLinkField = ""
            self.removeResultLayer("Link")
            return

        if not self.validationsOpenResult():
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.saveCurrentRender()
            self.ensureResultsLayersAreOpen()

            # Update visibility when variable changes
            link_layer = self._findResultLayer("Link")
            if link_layer:
                self.updateFieldsVisibility(link_layer, "Link", self._statsMode, self._currentStat)

            self.paintIntervalTimeResults(True)
        finally:
            QApplication.restoreOverrideCursor()
        self.resultPropertyChanged.emit()

    def nodesChanged(self):
        if self.Computing:
            return

        if self.cbNodes.currentIndex() == 0:
            self.displayingNodeField = ""
            self.removeResultLayer("Node")
            return

        if not self.validationsOpenResult():
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            self.saveCurrentRender()
            self.ensureResultsLayersAreOpen()

            # Update visibility when variable changes
            node_layer = self._findResultLayer("Node")
            if node_layer:
                self.updateFieldsVisibility(node_layer, "Node", self._statsMode, self._currentStat)

            self.paintIntervalTimeResults(True)
        finally:
            QApplication.restoreOverrideCursor()
        self.resultPropertyChanged.emit()

    def nodeLabelsClicked(self):
        self.updateLabels("Node")

    def linkLabelsClicked(self):
        self.updateLabels("Link")

    def flowDirectionsClicked(self):
        if not self.validationsOpenResult():
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

    def sliderChanged(self):
        if self.timeSlider.isSliderDown():
            return
        if not self.timeSlider.value() == self.cbTimes.currentIndex():
            self.cbTimes.setCurrentIndex(self.timeSlider.value())

    def sliderDragging(self, value):
        self.lbTime.setText(self.TimeLabels[value])
        self.timeTextChanged.emit(self.TimeLabels[value])
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

        QApplication.setOverrideCursor(Qt.WaitCursor)
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
                message = self.tr("No {} results are available").format(self.tr(layerName))
                QGISRedUIUtils.showGlobalMessage(self.iface, self.lbl_warning, message, level=1, duration=5)
                return False

        return True

    def ensureResultsLayersAreOpen(self):
        """Open result layers that are needed based on combobox state but not yet open."""
        if not self.isCurrentProject():
            return

        self.Scenario = "Base"
        layer_combobox = {"Node": self.cbNodes, "Link": self.cbLinks}
        for nameLayer in ["Node", "Link"]:
            # Don't open a layer if its variable combobox is set to None
            if layer_combobox[nameLayer].currentIndex() == 0:
                continue

            if self._findResultLayer(nameLayer) is None:
                self.openLayerResults(self.Scenario, nameLayer)

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

        # Remove results layers previous to simulate
        QGISRedLayerUtils().runTask(self.removeResults, self.simulationProcess)

    def simulationProcess(self):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Compute(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "False":
            QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
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
            # Hide all sibling groups except Results
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is not None:
                for child in netGroup.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        groupId = child.customProperty("qgisred_identifier")
                        if groupId != "qgisred_results" and child.name() != "Results":
                            child.setItemVisibilityChecked(False)
            return
        else:
            QGISRedUIUtils.showGlobalMessage(self.iface, self.tr("Error"), resMessage, level=2, duration=5)

        # If some error, close the dock
        self.close()

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
        self.saveCurrentRender()
        self.loadReportFile()
        self.updateQualityOptions()
        self.updateQualityItemComboboxes()
        self.applyStatisticFromOptions()
        labels = self._readTimeLabelsFromOut()
        self.openBaseResults(labels)
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
        qualityModel, _ = QgsProject.instance().readEntry("QGISRed", "project_qualitymodel", "Chemical")
        self.isQualitySimulated = qualityModel.upper() != "NONE"

    def openBaseResults(self, labels):
        # Select comboboxes item
        if self.cbLinks.currentIndex() == 0:
            self.cbLinks.setCurrentIndex(1)
        if self.cbNodes.currentIndex() == 0:
            self.cbNodes.setCurrentIndex(1)

        # Time labels
        time_label_list = labels.split(";")
        self.TimeLabels = []
        self.cbTimes.clear()
        if len(time_label_list) == 1:
            self.TimeLabels.append(self.lbl_permanent)
            self.cbTimes.addItem(self.lbl_permanent)
        else:
            for item in time_label_list:
                self.TimeLabels.append(item)
                self.cbTimes.addItem(item)

        self.cbTimes.setCurrentIndex(0)
        self.timeSlider.setValue(0)
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        # Configure visibilities
        in_stats = self._statsMode
        if not in_stats:
            self.lbTime.setText(self.TimeLabels[0])
        self._setModeWidgetsVisibility(in_stats, is_temporal=len(time_label_list) > 1)

        self.Computing = False

        # Open results
        self.openAllResults()

    def openAllResults(self):
        if not self.validationsOpenResult():
            return

        # Task is necessary because after remove layers, DBF files are in use. With the task,
        # the remove process finishs and filer are not in use
        QGISRedLayerUtils().runTask(self.removeResults, self.openAllResultsProcess)

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


