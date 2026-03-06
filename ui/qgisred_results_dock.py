# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsField
from PyQt5.QtCore import Qt, QVariant, QTimer
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsTextFormat
from qgis.core import QgsProperty, QgsRenderContext
from qgis.core import QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.qgisred_results import (
    getOut_TimeNodesProperties, getOut_TimeLinksProperties,
    getOut_StatNodesProperties, getOut_StatLinksProperties,
)


import os
from shutil import copyfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_results_dock.ui"))

def seconds_to_time_str(seconds):
    """Convert seconds to 'NNd HH:MM:SS' format."""
    d = seconds // 86400
    rem = seconds % 86400
    h = rem // 3600
    m = (rem % 3600) // 60
    s = rem % 60
    return f"{d:02d}d {h:02d}:{m:02d}:{s:02d}"


def time_field_name(var_name):
    """Return the time-companion field name for a variable: 'Time_' + uppercase letters."""
    uppers = ''.join(c for c in var_name if c.isupper())
    return ("Time_" + uppers)[:10]


class QGISRedResultsDock(QDockWidget, FORM_CLASS):
    # Signals
    timeTextChanged = pyqtSignal(str)

    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    Renders = {}
    Computing = False
    TimeLabels = []

    def __init__(self, iface):
        """Constructor."""
        super(QGISRedResultsDock, self).__init__(iface.mainWindow())
        self.iface = iface
        self.setupUi(self)

        # Translated labels
        self._lbl_none            = self.tr("None")
        self._lbl_maximum         = self.tr("Maximum")
        self._lbl_minimum         = self.tr("Minimum")
        self._lbl_mean            = self.tr("Mean")
        self._lbl_warning         = self.tr("Warning")
        self._lbl_permanent       = self.tr("Permanent")
        self._lbl_pressure        = self.tr("Pressure")
        self._lbl_head            = self.tr("Head")
        self._lbl_demand          = self.tr("Demand")
        self._lbl_quality         = self.tr("Quality")
        self._lbl_flow            = self.tr("Flow")
        self._lbl_velocity        = self.tr("Velocity")
        self._lbl_headloss        = self.tr("HeadLoss")
        self._lbl_unit_headloss   = self.tr("Unit HeadLoss")
        self._lbl_friction_factor = self.tr("Friction Factor")
        self._lbl_status          = self.tr("Status")
        self._lbl_reaction_rate   = self.tr("Reaction Rate")
        self._lbl_signed_flow     = self.tr("Signed Flow")
        self._lbl_unsigned_flow   = self.tr("Unsigned Flow")

        self.btMoreTime.clicked.connect(self.nextTime)
        self.btEndTime.clicked.connect(self.endTime)
        self.btLessTime.clicked.connect(self.previousTime)
        self.btInitTime.clicked.connect(self.initTime)
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

        self.statsDisplayWidget.setVisible(False)
        self.timeDisplayWidget.setVisible(True)

    """Methods"""
    def populateResultStatsComboboxes(self):
        self.cbResultTimes.addItems([self.tr("Report times")])
        self.cbStatistics.addItems([
            self._lbl_none,
            self._lbl_maximum,
            self._lbl_minimum,
            self.tr("Range"),
            self._lbl_mean,
            self.tr("Standard Deviation"),
        ])

    def populateVariableComboboxes(self):
        node_variables = [
            self._lbl_none,
            self._lbl_pressure,
            self._lbl_head,
            self._lbl_demand,
            self._lbl_quality,
        ]
        link_variables = [
            self._lbl_none,
            self._lbl_flow,
            self._lbl_velocity,
            self._lbl_headloss,
            self._lbl_unit_headloss,
            self._lbl_friction_factor,
            self._lbl_status,
            self._lbl_reaction_rate,
            self._lbl_quality,
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
        self.iface.messageBar().pushMessage(self._lbl_warning, message, level=1, duration=5)
        self.close()
        return False
    
    def updateLinksComboboxForStat(self, stat):
        """Adjusts cbLinks items when entering/leaving statistics mode.

        In any stat mode: removes 'Status' (categorical, not meaningful).
        In Mean mode: replaces 'Flow' with 'Flow Unsig' and inserts 'Flow Sig' below.
        On restore (stat == 'None'): reverses all changes.
        """
        self.cbLinks.currentIndexChanged.disconnect(self.linksChanged)
        try:
            current_text = self.cbLinks.currentText()

            if stat != self._lbl_none:
                # Remove Status if present
                status_idx = self.cbLinks.findText(self._lbl_status)
                if status_idx != -1:
                    self.cbLinks.removeItem(status_idx)

                if stat == self._lbl_mean:
                    flow_idx = self.cbLinks.findText(self._lbl_flow)
                    if flow_idx != -1:
                        self.cbLinks.setItemText(flow_idx, self._lbl_unsigned_flow)
                        self.cbLinks.insertItem(flow_idx + 1, self._lbl_signed_flow)
                        if current_text == self._lbl_flow:
                            self.cbLinks.setCurrentIndex(flow_idx)
                else:
                    # Entering non-Mean stat from Mean: remove Signed Flow, rename Unsigned Flow → Flow
                    flow_sig_idx = self.cbLinks.findText(self._lbl_signed_flow)
                    if flow_sig_idx != -1:
                        self.cbLinks.removeItem(flow_sig_idx)
                    flow_unsig_idx = self.cbLinks.findText(self._lbl_unsigned_flow)
                    if flow_unsig_idx != -1:
                        self.cbLinks.setItemText(flow_unsig_idx, self._lbl_flow)
                        if current_text in (self._lbl_unsigned_flow, self._lbl_signed_flow):
                            self.cbLinks.setCurrentIndex(flow_unsig_idx)
            else:
                # Restore: remove Signed Flow, rename Unsigned Flow → Flow
                flow_sig_idx = self.cbLinks.findText(self._lbl_signed_flow)
                if flow_sig_idx != -1:
                    self.cbLinks.removeItem(flow_sig_idx)
                flow_unsig_idx = self.cbLinks.findText(self._lbl_unsigned_flow)
                if flow_unsig_idx != -1:
                    self.cbLinks.setItemText(flow_unsig_idx, self._lbl_flow)
                    if current_text in (self._lbl_unsigned_flow, self._lbl_signed_flow):
                        self.cbLinks.setCurrentIndex(flow_unsig_idx)

                # Re-insert Status between Friction Factor and Reaction Rate
                frict_idx = self.cbLinks.findText(self._lbl_friction_factor)
                if frict_idx != -1 and self.cbLinks.findText(self._lbl_status) == -1:
                    self.cbLinks.insertItem(frict_idx + 1, self._lbl_status)
        finally:
            self.cbLinks.currentIndexChanged.connect(self.linksChanged)

    """Paths"""
    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getResultsPath(self):
        return os.path.join(self.ProjectDirectory, "Results")

    """Layers and Groups"""
    def getLayers(self):
        return QGISRedUtils().getLayers()

    def openLayerResults(self, scenario, nameLayer=None):
        resultPath = self.getResultsPath()
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + scenario, self.iface)
        resultGroup = self.getResultGroup()
        group = resultGroup.findGroup(scenario)
        if group is None:
            group = resultGroup.addGroup(scenario)
            QGISRedUtils.setGroupIdentifier(group, scenario)

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

    def removeResults(self):
        resultPath = self.getResultsPath()
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + self.Scenario, self.iface)
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
        # Same method in qgisred_newproject_dialog and qgisred_plugins
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def getResultGroup(self):
        resultGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if resultGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            resultGroup = netGroup.insertGroup(0, "Results")
            QGISRedUtils.setGroupIdentifier(resultGroup, "Results")
        resultGroup.setItemVisibilityChecked(True)
        return resultGroup

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
            
                    mode_prefix = f"stat_{self.cbStatistics.currentText()}|" if self._statsMode else "time|"
                    storage_key = mode_prefix + openedLayerPath + "|" + var_key
                    renderer = layer.renderer()
                    try:
                        if renderer.type() == "graduatedSymbol":
                            dictSce[storage_key] = renderer.ranges()
                        elif renderer.type() == "RuleRenderer":
                            dictSce[storage_key] = renderer.rootRule().clone()
                    except:
                        message = self.tr("Some issue occurred in the process of saving the style of the layer").format(self.tr(nameLayer))
                        self.iface.messageBar().pushMessage(self._lbl_warning, message, level=1, duration=5)
                    
        self.Renders[self.Scenario] = dictSce

    def paintIntervalTimeResults(self, setRender=False):
        if not self._statsMode:
            time_text = self.cbTimes.currentText()
            self.lbTime.setText(time_text)
            self.timeTextChanged.emit(time_text)

        # Maps combobox display text → layer field name (keys use self.tr to support translations)
        _LINK_FIELD_MAP = {
            self._lbl_flow: "Flow", self._lbl_unsigned_flow: "FlowUnsig", self._lbl_signed_flow: "FlowSig",
            self._lbl_velocity: "Velocity", self._lbl_headloss: "HeadLoss", self._lbl_unit_headloss: "UnitHdLoss",
            self._lbl_friction_factor: "FricFactor", self._lbl_status: "Status",
            self._lbl_reaction_rate: "ReactRate", self._lbl_quality: "Quality",
        }
        _NODE_FIELD_MAP = {
            self._lbl_pressure: "Pressure", self._lbl_head: "Head",
            self._lbl_demand: "Demand", self._lbl_quality: "Quality",
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
                    is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self._lbl_maximum, self._lbl_minimum)
                    time_field = time_field_name(field) if is_min_max_stat else None
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
        qmlField = "Flow" if rawField in ("FlowSig", "FlowUnsig") else rawField
        if field == "Flow":
            field = "abs(" + field + ")"
        
        is_status = (rawField == "Status")
        hasRender = False
        ranges = None
        
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        
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
                    self.iface.messageBar().pushMessage(self._lbl_warning, message, level=1, duration=5)
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
        if self.Computing:
            return

        statistic = self.cbStatistics.currentText()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            if statistic != self._lbl_none:
                self.saveCurrentRender()
                self._statsMode = True
                self.updateLinksComboboxForStat(statistic)
                result_times = self.cbResultTimes.currentText().lower()
                self.lbStatName.setText(f"{statistic} values")
                self.lbStatDesc.setText(f"for {result_times}")
                self.timeDisplayWidget.setVisible(False)
                self.statsDisplayWidget.setVisible(True)
                self.timeControlsWidget.setVisible(False)
                if self.validationsOpenResult():
                    self.ensureResultsLayersAreOpen()
                    self.clearResultFields()
                    self.completeStatsLayers()
                    self.paintIntervalTimeResults(True)

            else:
                self.saveCurrentRender()
                self._statsMode = False
                self.updateLinksComboboxForStat(self._lbl_none)
                self.statsDisplayWidget.setVisible(False)
                is_temporal = self.cbTimes.count() > 1
                self.timeDisplayWidget.setVisible(True)
                self.lbTime.setText(self.cbTimes.currentText())
                self.timeControlsWidget.setVisible(is_temporal)
                if self.validationsOpenResult():
                    self.ensureResultsLayersAreOpen()
                    self.clearResultFields()
                    self.completeResultLayers()
                    self.paintIntervalTimeResults(True)
        finally:
            QApplication.restoreOverrideCursor()

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
            self.paintIntervalTimeResults(True)
        finally:
            QApplication.restoreOverrideCursor()

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
            self.paintIntervalTimeResults(True)
        finally:
            QApplication.restoreOverrideCursor()

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

        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
                if checkbox.isChecked():
                    idx = combobox.currentIndex()
                    if idx > 0:
                        field = layer.fields().at(idx + 2).name()
                        is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (self._lbl_maximum, self._lbl_minimum)
                        time_field = time_field_name(field) if is_min_max_stat else None
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
                self.iface.messageBar().pushMessage(self._lbl_warning, message, level=1, duration=5)
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
        QGISRedUtils().runTask(self.removeResults, self.simulationProcess)

    def simulationProcess(self):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Compute(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage.startswith("[TimeLabels]"):
            self.openBaseResults(resMessage.replace("[TimeLabels]", ""))
            self.show()
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
            self.TimeLabels.append(self._lbl_permanent)
            self.cbTimes.addItem(self._lbl_permanent)
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
        QGISRedUtils().runTask(self.removeResults, self.openAllResultsProcess)

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

        # Activate map tips
        self.iface.actionMapTips().setChecked(True)

    def clearResultFields(self):
        """Removes result fields (from the first 'Time' or 'Stat' column onward) from both result layers."""
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
            candidates = [target_layer.fields().indexOf(f) for f in ("Time", "Stat")]
            candidates = [i for i in candidates if i != -1]
            if not candidates:
                continue
            start_idx = min(candidates)
            fields_to_delete = list(range(start_idx, target_layer.fields().count()))
            target_layer.dataProvider().deleteAttributes(fields_to_delete)
            target_layer.updateFields()
        self.displayingLinkField = ""
        self.displayingNodeField = ""

    def completeResultLayers(self):
        """Populates the attribute tables of the result layers with data from the .out file."""
        if not self.isCurrentProject():
            return

        # 1. Parse time strings like "00d 01:23:45" to seconds
        time_text = self.cbTimes.currentText()
        if time_text == self._lbl_permanent:
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

            # 2. Check and add missing fields
            first_id = next(iter(results))
            variables = list(v[:10] for v in results[first_id].keys())
            existing_fields = target_layer.fields().names()
            new_fields = []
            
            # Ensure "Time" field exists
            if "Time" not in existing_fields:
                new_fields.append(QgsField("Time", QVariant.String, "", 15))

            for var in variables:
                if var not in existing_fields:
                    if var == "Status":
                        new_fields.append(QgsField(var, QVariant.String))
                    else:
                        new_fields.append(QgsField(var, QVariant.Double))

            if new_fields:
                target_layer.dataProvider().addAttributes(new_fields)
                target_layer.updateFields()

            # 3. Update features
            # Get field indices
            field_indices = {}
            for var in variables:
                field_indices[var] = target_layer.fields().indexOf(var)
            
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

    def completeStatsLayers(self):
        """Populates the attribute tables of result layers with statistics from the .out file.
        Always clears existing result fields first so the column set matches the chosen statistic.
        """
        if not self.isCurrentProject():
            return

        self.clearResultFields()

        stat = self.cbStatistics.currentText()
        is_min_max = stat in (self._lbl_maximum, self._lbl_minimum)
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

            # For Min/Max, build companion time field names: "Time_" + uppercase letters of var
            time_field_map = {}  # var_key -> time_field_name
            if is_min_max:
                for var in results[first_id].keys():
                    var_key = var[:10]
                    time_field_map[var_key] = time_field_name(var)

            # Always add fields (clearResultFields already removed them)
            new_fields = [QgsField("Stat", QVariant.String, "", 15)]
            for var in variables:
                new_fields.append(QgsField(var, QVariant.Double))
                if is_min_max and var in time_field_map:
                    new_fields.append(QgsField(time_field_map[var], QVariant.String, "", 15))
            target_layer.dataProvider().addAttributes(new_fields)
            target_layer.updateFields()

            field_indices = {var: target_layer.fields().indexOf(var) for var in variables}
            time_field_indices = {}
            if is_min_max:
                for var_key, tf_name in time_field_map.items():
                    time_field_indices[var_key] = target_layer.fields().indexOf(tf_name)
            stat_field_idx = target_layer.fields().indexOf("Stat")
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
                    updates[stat_field_idx] = stat
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
