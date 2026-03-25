# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPixmap
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsField, QgsVectorLayer, QgsAttributeTableConfig
from qgis.gui import QgsDualView
import sip
from PyQt5.QtCore import Qt, QVariant, QTimer, QObject
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsTextFormat
from qgis.core import QgsProperty, QgsRenderContext, NULL
from qgis.core import QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer

from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from ...tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ...tools.qgisred_results import (
    getOut_TimeNodesProperties, getOut_TimeLinksProperties,
    getOut_StatNodesProperties, getOut_StatLinksProperties,
    get_out_file_metadata,
)


import os
import glob as _glob
from shutil import copyfile

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

class QGISRedResultsDock(QDockWidget, FORM_CLASS):
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
        self.iface.messageBar().pushMessage(self.lbl_warning, message, level=1, duration=5)
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
                self.iface.messageBar().pushMessage(self.tr("Results"), self.tr("{} results not found").format(self.tr(file)), level=1)
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
        resultPath = self.getResultsPath()
        resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
                QgsProject.instance().removeMapLayer(layer.id())
                break

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
        
        # Result fields in 10-char format
        node_fields_upper = [f[0][:10].upper() for f in NODE_RESULT_FIELDS]
        link_fields_upper = [f[0][:10].upper() for f in LINK_RESULT_FIELDS]
        all_result_fields_upper = set(node_fields_upper + link_fields_upper)
        
        visible_results = set()
        if not stats_mode:
            visible_results.add("Time")
            if layer_type == "Node":
                visible_results.update(["Pressure", "Head", "Demand", "Quality"])
            else:
                visible_results.update(["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"])
        else:
            visible_results.add("Statistics")
            if layer_type == "Node":
                visible_results.update(["Pressure", "Head", "Demand", "Quality"])
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible_results.update(["Time_H", "Time_D", "Time_Q"])
            else:
                visible_results.update(["Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor", "ReactRate", "Quality"])
                if stat == self.lbl_average:
                    visible_results.discard("Flow")
                    visible_results.update(["Flow_Unsig", "Flow_Sig"])
                if stat in (self.lbl_maximum, self.lbl_minimum):
                    visible_results.update(["Time_H", "Time_Q"])
        truncated_visible_upper = {v[:10].upper() for v in visible_results}

        # Ensure we don't hide columns that are NOT result fields (e.g., ID, Name)
        columns = config.columns()
        for i in range(len(columns)):
            col = columns[i]
            col_name_upper = col.name.upper()
            if col_name_upper in all_result_fields_upper:
                # Result field: set hidden state based on mode
                columns[i].hidden = not col_name_upper in truncated_visible_upper
                # Ensure it's treated as a field column
                columns[i].type = 0
        
        config.setColumns(columns)
        layer.setAttributeTableConfig(config)
        
        # Surgical refresh: ONLY update windows already open
        # NOTE: allWidgets() returns Qt base types (QStackedWidget, QDialog).
        # We must use sip.cast() to get the real QGIS type and access layer().
        if not self.Computing:
            layer_id = layer.id()
            refreshed_count = 0
            
            cast_map = {
                "QgsDualView": QgsDualView,
            }
            for widget in QApplication.instance().allWidgets():
                cls = widget.metaObject().className()
                if cls not in cast_map:
                    continue
                try:
                    typed = sip.cast(widget, cast_map[cls])
                    # layer() no está en QgsDualView en QGIS 3.4, pero masterModel().layer() sí
                    w_layer = typed.masterModel().layer()
                    if w_layer and w_layer.id() == layer_id:
                        typed.setAttributeTableConfig(config)
                        refreshed_count += 1
                except Exception:
                    pass


            
            if refreshed_count > 0:
                QApplication.processEvents()


    def forceFinalFieldsVisibility(self):
        """Re-applies visibility to all result layers after everything has settled."""
        resultPath = self.getResultsPath()
        for layerName in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp")
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    self.updateFieldsVisibility(layer, layerName, self._statsMode, self._currentStat)

    def clearResultFields(self):
        """Clears the values of result fields instead of deleting them to preserve order."""
        resultPath = self.getResultsPath()
        openedLayers = self.getLayers()
        for layerName in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp")
            target_layer = None
            for layer in openedLayers:
                if self.getLayerPath(layer) == resultLayerPath:
                    target_layer = layer
                    break
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
        resultPath = self.getResultsPath()
        layers = self.getLayers()

        self.Computing = True
        self.cbLinks.setCurrentIndex(0)
        self.cbNodes.setCurrentIndex(0)

        for nameLayer in ["Node", "Link"]:
            layerResult = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openLayerPath = self.getLayerPath(layer)
                if openLayerPath == layerResult:
                    if "Link" in nameLayer:
                        self.cbLinks.setCurrentIndex(1) # Default to first result
                    else:
                        self.cbNodes.setCurrentIndex(1) # Default to first result
        self.Computing = False

    """Symbology"""
    def saveCurrentRender(self):
        openedLayers = self.getLayers()
        resultPath = self.getResultsPath()
        dictSce = self.Renders.get(self.Scenario)
        if dictSce is None:
            dictSce = {}

        resultLayersName = ["Node", "Link"]   
        for nameLayer in resultLayersName:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in openedLayers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    # Use the field that IS currently displayed on the layer
                    var_key = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
                    
                    if not var_key:
                        continue
            
                    mode_prefix = f"stat_{self._currentStat}|" if self._statsMode else "time|"
                    storage_key = mode_prefix + openedLayerPath + "|" + var_key
                    renderer = layer.renderer()
                    try:
                        if renderer.type() == "graduatedSymbol":
                            dictSce[storage_key] = renderer.ranges()
                        elif renderer.type() == "RuleRenderer":
                            dictSce[storage_key] = renderer.rootRule().clone()
                    except:
                        message = self.tr("Some issue occurred in the process of saving the style of the layer").format(self.tr(nameLayer))
                        self.iface.messageBar().pushMessage(self.lbl_warning, message, level=1, duration=5)
                    
        self.Renders[self.Scenario] = dictSce

    def paintIntervalTimeResults(self, setRender=False):
        if not self._statsMode:
            time_text = self.cbTimes.currentText()
            self.lbTime.setText(time_text)
            self.timeTextChanged.emit(time_text)

        # Maps combobox display text → layer field name (keys use self.tr to support translations)
        _LINK_FIELD_MAP = {
            self.lbl_flow: "Flow", self.lbl_unsigned_flow: "Flow_Unsig", self.lbl_signed_flow: "Flow_Sig",
            self.lbl_velocity: "Velocity", self.lbl_headloss: "HeadLoss", self.lbl_unit_headloss: "UnitHdLoss",
            self.lbl_friction_factor: "FricFactor", self.lbl_status: "Status",
            self.lbl_reaction_rate: "ReactRate", self.lbl_quality: "Quality",
        }
        _NODE_FIELD_MAP = {
            self.lbl_pressure: "Pressure", self.lbl_head: "Head",
            self.lbl_demand: "Demand", self.lbl_quality: "Quality",
        }

        resultPath = self.getResultsPath()
        for nameLayer in ["Node", "Link"]:
            layer_to_paint = None
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            # Check if layer is already open
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    layer_to_paint = layer
                    break

            if layer_to_paint:
                field = ""
                disp_name = ""
                var_translated = ""
                if "Link" in nameLayer:
                    if self.cbLinks.currentIndex() > 0:
                        var_translated = self.cbLinks.currentText()
                        field = _LINK_FIELD_MAP.get(var_translated, "")
                        disp_name = self.tr("Link {}").format(var_translated)
                else:
                    if self.cbNodes.currentIndex() > 0:
                        var_translated = self.cbNodes.currentText()
                        field = _NODE_FIELD_MAP.get(var_translated, "")
                        disp_name = self.tr("Node {}").format(var_translated)

                if field:
                    self.setGraduadedPalette(layer_to_paint, field, setRender, nameLayer)

                    # Store current displayed variable
                    if "Link" in nameLayer: self.displayingLinkField = field
                    else: self.displayingNodeField = field

                    # Set layer name in legend
                    layer_to_paint.setName(disp_name)

                    # Configure map tip
                    is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self.lbl_maximum, self.lbl_minimum)
                    time_field = time_field_name(field, nameLayer) if is_min_max_stat else None
                    if time_field:
                        tip = var_translated + ': [% "' + field + '" || \' - \' || "' + time_field + '" %]'
                    else:
                        tip = var_translated + ': [% "' + field + '" %]'
                    layer_to_paint.setMapTipTemplate(tip)

                    # Configure layer labels
                    self.setLayerLabels(layer_to_paint, field, time_field)

    def setLayerLabels(self, layer, fieldName, time_field=None):
        firstCondition = layer.geometryType() == 0 and self.cbNodeLabels.isChecked()
        secondCondition = layer.geometryType() == 1 and self.cbLinkLabels.isChecked()
        if firstCondition or secondCondition:
            layer_settings = QgsPalLayerSettings()
            layer_settings.formatNumbers = True
            layer_settings.decimals = 2
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 10))
            color = "black"
            # if secondCondition:
            #     color = "blue"
            text_format.setColor(QColor(color))
            layer_settings.setFormat(text_format)

            if time_field:
                layer_settings.fieldName = f'round("{fieldName}", 2) || \' - \' || "{time_field}"'
                layer_settings.isExpression = True
            elif fieldName == "Flow":
                layer_settings.fieldName = 'abs("Flow")'
                layer_settings.isExpression = True
            else:
                layer_settings.fieldName = fieldName
                layer_settings.isExpression = False

            layer_settings.placement = QgsPalLayerSettings.Line
            layer_settings.enabled = True
            labels = QgsVectorLayerSimpleLabeling(layer_settings)
            layer.setLabeling(labels)
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()

    def setArrowsVisibility(self, symbol, layer, field):
        prop = QgsProperty()
        try:
            if layer.geometryType() == 1 and self.cbFlowDirections.isChecked():
                # Show arrows in pipes
                ss = symbol.symbolLayer(3)  # arrow positive flow
                prop.setExpressionString("if(Type='PIPE', if(" + field + ">0,3,0),0)")
                ss.subSymbol().setDataDefinedSize(prop)
                ss = symbol.symbolLayer(4)  # arrow negative flow
                prop.setExpressionString("if(Type='PIPE', if(" + field + "<0,3,0),0)")
                ss.subSymbol().setDataDefinedSize(prop)
            else:
                # Hide arrows
                prop.setExpressionString("0")
                symbol.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
                symbol.symbolLayer(4).subSymbol().setDataDefinedSize(prop)
        except:
            self.cbFlowDirections.setChecked(False)
            self.cbFlowDirections.setEnabled(False)

    def setGraduadedPalette(self, layer, field, setRender, nameLayer):
        renderer = layer.renderer()
        rawField = field  # column name
        qmlField = "Flow" if rawField in ("Flow_Sig", "Flow_Unsig") else rawField
        if field == "Flow":
            field = "abs(" + field + ")"
        
        is_status = (rawField == "Status")
        hasRender = False
        ranges = None
        
        utils = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

        if setRender:  # Just opened a layer or changed variable
            dictRend = self.Renders.get(self.Scenario)
            layerPath = self.getLayerPath(layer)
            mode_prefix = f"stat_{self.cbStatistics.currentText()}|" if self._statsMode else "time|"
            storage_key = mode_prefix + layerPath + "|" + rawField

            if dictRend is None:
                dictRend = self.Renders.get("Base")
                if dictRend is not None:
                    base_storage_key = mode_prefix + layerPath.replace("_" + self.Scenario + "_", "_Base_") + "|" + rawField
                    ranges = dictRend.get(base_storage_key)
                    if ranges is not None:
                        hasRender = True
            else:
                ranges = dictRend.get(storage_key)
                if ranges is not None:
                    hasRender = True
                else:
                    dictRendBase = self.Renders.get("Base")
                    if dictRendBase is not None:
                        base_storage_key = mode_prefix + layerPath.replace("_" + self.Scenario + "_", "_Base_") + "|" + rawField
                        ranges = dictRendBase.get(base_storage_key)
                        if ranges is not None:
                            hasRender = True
        # Ensure correct renderer type
        if is_status:
            # Check if we need to load default QML
            if not hasRender and not isinstance(renderer, QgsRuleBasedRenderer):
                qmlName = nameLayer.split("_")[0] + "_" + rawField 
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()
            
            if hasRender and isinstance(ranges, QgsRuleBasedRenderer.Rule):
                try:
                    renderer = QgsRuleBasedRenderer(ranges.clone())
                except:
                    message = self.tr("Some issue occurred in the process of applying the style to the layer").format(self.tr(layerName))
                    self.iface.messageBar().pushMessage(self.lbl_warning, message, level=1, duration=5)
                    return
        else:
            # Check if we need to load default QML
            # We load it if there's no saved render AND (it's not graduated OR it's the wrong variable)
            wrong_variable = isinstance(renderer, QgsGraduatedSymbolRenderer) and renderer.classAttribute() != field
            if not hasRender and (not isinstance(renderer, QgsGraduatedSymbolRenderer) or len(renderer.ranges()) == 0 or wrong_variable):
                qmlName = nameLayer.split("_")[0] + "_" + qmlField 
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()
                
            if hasRender and isinstance(ranges, list):
                renderer = QgsGraduatedSymbolRenderer(field, ranges)
            
            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer.setClassAttribute(field)

        # Update arrow visibility
        try:
            # Arrows always use the Flow field (index 2 in layer)
            flow_field = layer.fields().at(2).name() 
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, flow_field)
        except:
            pass

        layer.setRenderer(renderer)
        layer.triggerRepaint()


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
            self.timeDisplayWidget.setVisible(False)
            self.statsDisplayWidget.setVisible(True)
            self.timeControlsWidget.setVisible(False)
            if self.cbFlowDirections.isChecked():
                self.cbFlowDirections.setChecked(False)
            self.cbFlowDirections.setVisible(False)
        else:
            self._statsMode = False
            self.updateLinksComboboxForStat(self.lbl_none)
            self.statsDisplayWidget.setVisible(False)
            is_temporal = self.cbTimes.count() > 1
            self.timeDisplayWidget.setVisible(True)
            self.cbFlowDirections.setVisible(True)
            self.lbTime.setText(self.cbTimes.currentText())
            self.timeControlsWidget.setVisible(is_temporal)

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
            resultPath = self.getResultsPath()
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_Link.shp")
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    self.updateFieldsVisibility(layer, "Link", self._statsMode, self._currentStat)
                    break

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
            resultPath = self.getResultsPath()
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_Node.shp")
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    self.updateFieldsVisibility(layer, "Node", self._statsMode, self._currentStat)
                    break

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

        resultLayerPath = self.generatePath(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + "_Link.shp")
        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
                layer_to_paint = layer
                break
        if layer_to_paint:
            renderer = layer_to_paint.renderer()
            symbols = renderer.symbols(QgsRenderContext())
            flow_field = layer_to_paint.fields().at(2).name()  # Flow field
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

        resultPath = self.getResultsPath()
        resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layer_type + ".shp")
        
        checkbox = self.cbNodeLabels if layer_type == "Node" else self.cbLinkLabels
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks

        _LINK_FIELD_MAP = {
            self.lbl_flow: "Flow", self.lbl_unsigned_flow: "Flow_Unsig", self.lbl_signed_flow: "Flow_Sig",
            self.lbl_velocity: "Velocity", self.lbl_headloss: "HeadLoss", self.lbl_unit_headloss: "UnitHdLoss",
            self.lbl_friction_factor: "FricFactor", self.lbl_status: "Status",
            self.lbl_reaction_rate: "ReactRate", self.lbl_quality: "Quality",
        }
        _NODE_FIELD_MAP = {
            self.lbl_pressure: "Pressure", self.lbl_head: "Head",
            self.lbl_demand: "Demand", self.lbl_quality: "Quality",
        }
        field_map = _LINK_FIELD_MAP if layer_type == "Link" else _NODE_FIELD_MAP

        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
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
                self.iface.messageBar().pushMessage(self.lbl_warning, message, level=1, duration=5)
                return False

        return True

    def ensureResultsLayersAreOpen(self):
        # Ensure result layers are opened
        if not self.isCurrentProject():
            return

        self.Scenario = "Base"
        resultPath = self.getResultsPath()
        layer_combobox = {"Node": self.cbNodes, "Link": self.cbLinks}
        for nameLayer in ["Node", "Link"]:
            # Don't open a layer if its variable combobox is set to None
            if layer_combobox[nameLayer].currentIndex() == 0:
                continue

            layer_to_paint = None
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")

            # Check if layer is already open
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    layer_to_paint = layer
                    break

            # If the layer is not open, open it!
            if layer_to_paint is None:
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
            self.iface.messageBar().pushMessage("Warning", self.tr("Some issues occurred in the process"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

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

    def _readTimeLabelsFromOut(self):
        """Read time step labels from existing .out file (same format as GISRed.Compute returns)."""
        try:
            with open(self.outPath, 'rb') as f:
                meta = get_out_file_metadata(f)
            if meta is None:
                return self.lbl_permanent
            n = meta["num_periods"]
            if n <= 1:
                return self.lbl_permanent
            start = meta["report_start"]
            step = meta["report_step"]
            labels = []
            for i in range(n):
                labels.append(seconds_to_time_str(start + i * step))
            return ";".join(labels)
        except Exception:
            return self.lbl_permanent

    def loadReportFile(self):
        rpt_path = os.path.join(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + ".rpt")
        if os.path.exists(rpt_path):
            with open(rpt_path, "r", errors="replace") as f:
                self.textEditReport.setPlainText(f.read())

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
        mylist = labels.split(";")
        self.TimeLabels = []
        self.cbTimes.clear()
        if len(mylist) == 1:
            self.TimeLabels.append(self.lbl_permanent)
            self.cbTimes.addItem(self.lbl_permanent)
        else:
            for item in mylist:
                self.TimeLabels.append(item)
                self.cbTimes.addItem(item)

        self.cbTimes.setCurrentIndex(0)
        self.timeSlider.setValue(0)
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        # Configure Visibilities
        in_stats = self._statsMode
        self.statsDisplayWidget.setVisible(in_stats)
        self.timeDisplayWidget.setVisible(not in_stats)
        if not in_stats:
            self.lbTime.setText(self.TimeLabels[0])
        self.timeControlsWidget.setVisible(not in_stats and len(mylist) > 1)

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

    def completeResultLayers(self):
        """Populates the attribute tables of the result layers with data from the .out file."""
        if not self.isCurrentProject():
            return

        # 1. Parse time strings like "00d 01:23:45" to seconds
        time_text = self.cbTimes.currentText()
        if time_text == self.lbl_permanent:
            time_seconds = 0
        else:
            try:
                # Format: "00d 00:00:00"
                parts = time_text.split(" ")
                days = int(parts[0].replace("d", ""))
                hms = parts[1].split(":")
                time_seconds = days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
            except Exception:
                time_seconds = 0

        resultPath = self.getResultsPath()
        binary_path = os.path.join(resultPath, self.NetworkName + "_" + self.Scenario + ".out")
        if not os.path.exists(binary_path):
            return

        openedLayers = self.getLayers()
        for layerName in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp")
            target_layer = None
            for layer in openedLayers:
                if self.getLayerPath(layer) == resultLayerPath:
                    target_layer = layer
                    break

            if not target_layer:
                continue

            # Fetch results from binary file
            if layerName == "Node":
                results = getOut_TimeNodesProperties(binary_path, time_seconds)
            else:
                results = getOut_TimeLinksProperties(binary_path, time_seconds)
            
            if not results:
                continue

            # 3. Update features
            first_id = next(iter(results))
            variables = list(results[first_id].keys())
            
            # Get field indices
            field_indices = {}
            for var in variables:
                # Shapefile fields are limited to 10 chars
                field_indices[var] = target_layer.fields().indexOf(var[:10])
            
            time_field_idx = target_layer.fields().indexOf("Time")
            
            # Find Id field index (assuming it's called "Id")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                # fallback to first field if "Id" not found
                id_field_idx = 0

            attribute_updates = {}
            for feature in target_layer.getFeatures():
                elem_id = str(feature.attributes()[id_field_idx])
                if elem_id in results:
                    elem_results = results[elem_id]
                    updates = {}
                    if time_field_idx != -1:
                        updates[time_field_idx] = time_text
                    
                    for var, val in elem_results.items():
                        updates[field_indices[var[:10]]] = val
                    attribute_updates[feature.id()] = updates

            # Apply updates via provider (more efficient for batch)
            if attribute_updates:
                target_layer.dataProvider().changeAttributeValues(attribute_updates)
                target_layer.dataProvider().dataChanged.emit()
                target_layer.triggerRepaint()
            
            # Apply visibility AFTER populating
            self.updateFieldsVisibility(target_layer, layerName, stats_mode=False)

    def completeStatsLayers(self):
        """Populates the attribute tables of result layers with statistics from the .out file.
        Always clears existing result fields first so the column set matches the chosen statistic.
        """
        if not self.isCurrentProject():
            return

        self.clearResultFields()

        stat_label = self.cbStatistics.currentText()
        stat_label_to_en = {
            self.lbl_maximum:       "Maximum",
            self.lbl_minimum:       "Minimum",
            self.lbl_range:         "Range",
            self.lbl_average:       "Average",
            self.lbl_std_deviation: "StdDev",
        }
        stat = stat_label_to_en.get(stat_label, stat_label)
        is_min_max = stat_label in (self.lbl_maximum, self.lbl_minimum)
        resultPath = self.getResultsPath()
        binary_path = os.path.join(resultPath, self.NetworkName + "_" + self.Scenario + ".out")
        if not os.path.exists(binary_path):
            return

        openedLayers = self.getLayers()
        for layerName in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp")
            target_layer = None
            for layer in openedLayers:
                if self.getLayerPath(layer) == resultLayerPath:
                    target_layer = layer
                    break

            if not target_layer:
                continue
            if layerName == "Node":
                results = getOut_StatNodesProperties(binary_path, stat)
            else:
                results = getOut_StatLinksProperties(binary_path, stat)

            if not results:
                continue

            first_id = next(iter(results))
            variables = list(v[:10] for v in results[first_id].keys())

            # For Min/Max: time columns per layer type.
            #   Node: Time_H after Head (shared Pressure+Head), Time_D, Time_Q individual
            #   Link: Time_H after UnitHdLoss (shared Flow/Velocity/HeadLoss/UnitHdLoss),
            #         Time_FF, Time_RR, Time_Q individual
            _TIME_FIELD_AFTER = {
                "Node": {"Head": "Time_H", "Demand": "Time_D", "Quality": "Time_Q"},
                "Link": {"UnitHdLoss": "Time_H", "Quality": "Time_Q"},
            }
            _TIME_PROVIDER = {
                "Node": {"Pressure": "Time_H", "Demand": "Time_D", "Quality": "Time_Q"},
                "Link": {"Flow": "Time_H", "Quality": "Time_Q"},
            }
            time_field_after  = _TIME_FIELD_AFTER.get(layerName, {})
            time_field_provider = _TIME_PROVIDER.get(layerName, {})

            first_id = next(iter(results))
            variables = list(results[first_id].keys())

            field_indices = {var: target_layer.fields().indexOf(var[:10]) for var in variables}
            time_field_indices = {}
            if is_min_max:
                for provider_var, tf_name in time_field_provider.items():
                    time_field_indices[provider_var] = target_layer.fields().indexOf(tf_name)
            stat_field_idx = target_layer.fields().indexOf("Statistics")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                id_field_idx = 0

            attribute_updates = {}
            for feature in target_layer.getFeatures():
                elem_id = str(feature.attributes()[id_field_idx])
                if elem_id not in results:
                    continue
                updates = {}
                if stat_field_idx != -1:
                    updates[stat_field_idx] = stat_label
                for var, val in results[elem_id].items():
                    var_key = var[:10]
                    if var_key in field_indices and field_indices[var_key] != -1:
                        updates[field_indices[var_key]] = val["Value"] if val is not None else None
                        if is_min_max and var_key in time_field_indices and time_field_indices[var_key] != -1:
                            t = val["Time"] if val is not None else None
                            updates[time_field_indices[var_key]] = seconds_to_time_str(t) if t is not None else None
                attribute_updates[feature.id()] = updates

            if attribute_updates:
                target_layer.dataProvider().changeAttributeValues(attribute_updates)
                target_layer.dataProvider().dataChanged.emit()
                target_layer.triggerRepaint()
            
            # Apply visibility AFTER populating
            self.updateFieldsVisibility(target_layer, layerName, stats_mode=True, stat=stat_label)


"""Helpers"""
def seconds_to_time_str(seconds):
    """Convert seconds to 'NNd HH:MM:SS' format."""
    d = seconds // 86400
    rem = seconds % 86400
    h = rem // 3600
    m = (rem % 3600) // 60
    s = rem % 60
    return f"{d:02d}d {h:02d}:{m:02d}:{s:02d}"


def time_field_name(var_name, layer_type):
    """Return the time-companion field name for a variable based on layer type."""
    if layer_type == "Node":
        mapping = {
            "Pressure": "Time_H",
            "Head": "Time_H",
            "Demand": "Time_D",
            "Quality": "Time_Q"
        }
    else:  # Link
        mapping = {
            "Flow": "Time_H",
            "Velocity": "Time_H",
            "HeadLoss": "Time_H",
            "UnitHdLoss": "Time_H",
            "Quality": "Time_Q"
        }
    return mapping.get(var_name)

