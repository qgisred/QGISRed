# -*- coding: utf-8 -*-
"""Analysis and results section for QGISRed (model, results dock, time series, export)."""

import os

from qgis.core import QgsRectangle
from qgis.PyQt.QtWidgets import QApplication, QDialog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsHighlight

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ..compat import DIALOG_ACCEPTED
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType
from ..ui.analysis.qgisred_results_dock import QGISRedResultsDock
from ..ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock
from ..ui.analysis.qgisred_results_data import export_results_to_csv, get_regional_separators


class AnalysisSection:
    """Analysis options, model simulation, results dock, time series, export to INP.

    Note: runModel connects self.ResultDockwidget.visibilityChanged to self.activeInputGroup,
    which is defined in LayerManagementSection.
    """

    def runAnalysisOptions(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.AnalysisOptions(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if "True" in resMessage:
            resMessage = resMessage.replace("True:", "")
            self.unitsAction.setText("QGISRed: " + resMessage)
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.savedExtent = self.iface.mapCanvas().extent()
            self.removingLayers = True
            QGISRedLayerUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "commit":
            self.processCsharpResult(resMessage, "Pipe's roughness converted")
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage == "Cancelled":
            pass
        else:
            self.pushMessage(resMessage, level=2, duration=5)

    def _outFilePath(self):
        scenario = getattr(self.ResultDockwidget, 'Scenario', 'Base') if self.ResultDockwidget else 'Base'
        return os.path.join(self.ProjectDirectory, "Results", f"{self.NetworkName}_{scenario}.out")

    def _initResultsDock(self):
        if self.ResultDockwidget is None:
            self.readOptions()
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ResultDockwidget)
            # activeInputGroup is defined in LayerManagementSection
            self.ResultDockwidget.visibilityChanged.connect(self.activeInputGroup)
            self.ResultDockwidget.simulationFinished.connect(self.refreshTimeSeries)
            self.ResultDockwidget.resultPropertyChanged.connect(self.refreshTimeSeries)

    def runModel(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self._initResultsDock()
        self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        self.connectElementExplorerToResultsDock()

    def runShowResultsDock(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return

        self._initResultsDock()
        if not getattr(self.ResultDockwidget, 'outPath', '') or not self.ResultDockwidget.TimeLabels:
            if os.path.exists(self._outFilePath()):
                self.ResultDockwidget.loadExistingResults(self.ProjectDirectory, self.NetworkName)
            else:
                self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        else:
            self.ResultDockwidget.openAllResultsProcess()
            self.ResultDockwidget.show()
            self.ResultDockwidget.raise_()
        self.connectElementExplorerToResultsDock()
        self.ResultDockwidget.tabWidget.setCurrentIndex(0)

    def runOpenStatusReport(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self._initResultsDock()
        if not getattr(self.ResultDockwidget, 'outPath', '') or not self.ResultDockwidget.TimeLabels:
            if os.path.exists(self._outFilePath()):
                self.ResultDockwidget.loadExistingResults(self.ProjectDirectory, self.NetworkName)
            else:
                self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        else:
            self.ResultDockwidget.openAllResultsProcess()
            self.ResultDockwidget.show()
            self.ResultDockwidget.raise_()
        self.connectElementExplorerToResultsDock()
        self.ResultDockwidget.tabWidget.setCurrentIndex(1)

    def runExportInp(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ExportToInp(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.pushMessage(self.tr("INP file successfully exported"), level=3, duration=5)
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif not resMessage == "Cancelled":
            self.pushMessage(resMessage, level=2, duration=5)

    def runExportResultsToCsv(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        scenario = getattr(self.ResultDockwidget, 'Scenario', 'Base') if self.ResultDockwidget else 'Base'
        if not os.path.exists(self._outFilePath()):
            self.pushMessage(self.tr("No simulation results found"), level=1, duration=5)
            return

        results_dir = os.path.join(self.ProjectDirectory, "Results")
        base = "{}_{}".format(self.NetworkName, scenario)
        default_nodes = os.path.join(results_dir, base + "_Nodes.csv")
        default_links = os.path.join(results_dir, base + "_Links.csv")
        list_sep, decimal_sep = get_regional_separators()
        binary_path = self._outFilePath()
        from ..ui.analysis.qgisred_export_csv_dialog import QGISRedExportCsvDialog
        dlg = QGISRedExportCsvDialog(
            default_nodes, default_links, list_sep, decimal_sep,
            self.ProjectDirectory, parent=self.iface.mainWindow()
        )
        if dlg.exec() != DIALOG_ACCEPTED:
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            export_results_to_csv(
                binary_path, dlg.nodes_path, dlg.links_path,
                self.iface, dlg.list_sep, dlg.decimal_sep
            )
        finally:
            QApplication.restoreOverrideCursor()

    def runTimeSeries(self):
        if self.timeSeriesButton.isChecked():
            # 1. Basic Validations
            self.defineCurrentProject()
            if not self.isValidProject() or self.isLayerOnEdition():
                self.pushMessage(
                    self.tr("Necessary to have a valid project and no layer on edition."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            # 2. Results Validation
            results_ready = False
            if self.ResultDockwidget:
                out_path = getattr(self.ResultDockwidget, 'outPath', '')
                if out_path and os.path.exists(out_path) and self.ResultDockwidget.isCurrentProject():
                    results_ready = True
            if not results_ready and os.path.exists(self._outFilePath()):
                self._initResultsDock()
                self.ResultDockwidget.loadExistingResults(self.ProjectDirectory, self.NetworkName)
                self.ResultDockwidget.hide()
                self.connectElementExplorerToResultsDock()
                results_ready = True

            if not results_ready:
                self.pushMessage(
                    self.tr("It is necessary to simulate first."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            self.runTimeSeriesSelectPointTool()
            if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
                self.timeSeriesDock = QGISRedTimeSeriesDock(self.iface)
                self.timeSeriesDock.visibilityChanged.connect(self.timeSeriesDockVisibilityChanged)
                self.timeSeriesDock.destroyed.connect(self._onTimeSeriesDockDestroyed)
                self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.timeSeriesDock)
            self._ensureTimeSeriesMapToolSignal()
            self.timeSeriesDock.show()
            self.timeSeriesDock.raise_()
            self.timeSeriesDock.setFocus()
        else:
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools["TimeSeries"]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
            self._clearTimeSeriesHighlight()

    def runTimeSeriesSelectPointTool(self):
        self.myMapTools["TimeSeries"] = QGISRedSelectPointTool(self.timeSeriesButton, self, self.timeSeriesCallback, SelectPointType.Line, cursor=":/images/iconTimeSeries.svg")
        self.iface.mapCanvas().setMapTool(self.myMapTools["TimeSeries"])

    def _ensureTimeSeriesMapToolSignal(self):
        """Clear highlight when TimeSeries tool is no longer the active map tool."""
        if getattr(self, "_timeSeriesMapToolSignalConnected", False):
            return
        try:
            self.iface.mapCanvas().mapToolSet.connect(self._onMapToolSetForTimeSeries)
            self._timeSeriesMapToolSignalConnected = True
        except Exception:
            # Some test/mocked environments may not expose this signal.
            self._timeSeriesMapToolSignalConnected = False

    def _onMapToolSetForTimeSeries(self, tool):
        try:
            ts_tool = self.myMapTools.get("TimeSeries")
        except Exception:
            ts_tool = None
        if ts_tool is None:
            self._clearTimeSeriesHighlight()
            return
        if tool is not ts_tool:
            self._clearTimeSeriesHighlight()

    def _onTimeSeriesDockDestroyed(self, *_args):
        self.timeSeriesDock = None
        self._clearTimeSeriesHighlight()

    def timeSeriesDockVisibilityChanged(self, visible):
        if not visible:
            self.timeSeriesButton.setChecked(False)
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools.get("TimeSeries"):
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
            self._clearTimeSeriesHighlight()

    def _clearTimeSeriesHighlight(self):
        highlight = getattr(self, "timeSeriesHighlight", None)
        if highlight is not None:
            try:
                highlight.hide()
            except Exception:
                pass
        self.timeSeriesHighlight = None

    def _setTimeSeriesHighlight(self, layer, feature):
        self._clearTimeSeriesHighlight()
        if layer is None or feature is None:
            return
        try:
            highlight = QgsHighlight(self.iface.mapCanvas(), feature.geometry(), layer)
            highlight.setColor(QColor("blue"))
            highlight.setWidth(5)
            highlight.show()
            self.timeSeriesHighlight = highlight
        except Exception:
            self.timeSeriesHighlight = None

    def timeSeriesCallback(self, point):
        self.updateTimeSeriesPlot(point)

    def updateTimeSeriesPlot(self, point):
        if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
            return

        # Identify element
        # Tolerance in map units
        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance, point.x() + tolerance, point.y() + tolerance)

        found_feature = None
        category = "" # "Node" or "Link"

        # Priority layers by their QGISRed identifier
        layers_to_check = [
            ("qgisred_junctions", "Node"), ("qgisred_tanks", "Node"), ("qgisred_reservoirs", "Node"),
            ("qgisred_pipes", "Link"), ("qgisred_valves", "Link"), ("qgisred_pumps", "Link")
        ]

        for identifier, cat in layers_to_check:
            # Find layer by identifier
            layer = None
            for l in QGISRedLayerUtils().getLayers():
                if l.customProperty("qgisred_identifier") == identifier:
                    layer = l
                    break

            if layer:
                for feature in layer.getFeatures(rect):
                    found_feature = feature
                    category = cat
                    break
            if found_feature: break

        if not found_feature:
            self.pushMessage(self.tr("No network element found at this location."), level=1)
            return

        self.lastTimeSeriesFeature = found_feature
        self.lastTimeSeriesCategory = category
        self.lastTimeSeriesLayer = layer
        self._setTimeSeriesHighlight(layer, found_feature)
        self.performTimeSeriesPlotUpdate(found_feature, category, layer)

    def performTimeSeriesPlotUpdate(self, found_feature, category, layer):
        if found_feature is None:
            return
        element_id = str(found_feature.attribute("ID"))

        # Get current magnitude from resultsDock
        prop_internal = ""
        prop_display = ""
        is_stepped = False

        if hasattr(self, 'ResultDockwidget') and self.ResultDockwidget:
            if category == "Node":
                prop_display = self.ResultDockwidget.cbNodes.currentText()
                # Map display name to internal
                mapping = {
                    self.ResultDockwidget.lbl_pressure: "Pressure",
                    self.ResultDockwidget.lbl_head: "Head",
                    self.ResultDockwidget.lbl_demand: "Demand",
                    self.ResultDockwidget.lbl_quality: "Quality"
                }
                prop_internal = mapping.get(prop_display, "Pressure")
            else:
                prop_display = self.ResultDockwidget.cbLinks.currentText()
                mapping = {
                    self.ResultDockwidget.lbl_flow: "Flow",
                    self.ResultDockwidget.lbl_velocity: "Velocity",
                    self.ResultDockwidget.lbl_headloss: "HeadLoss",
                    self.ResultDockwidget.lbl_unit_headloss: "UnitHdLoss",
                    self.ResultDockwidget.lbl_friction_factor: "FricFactor",
                    self.ResultDockwidget.lbl_status: "Status",
                    self.ResultDockwidget.lbl_reaction_rate: "ReactRate",
                    self.ResultDockwidget.lbl_quality: "Quality",
                    self.ResultDockwidget.lbl_signed_flow: "Flow",
                    self.ResultDockwidget.lbl_unsigned_flow: "Flow"
                }
                prop_internal = mapping.get(prop_display, "Flow")
                if prop_internal == "Status":
                    is_stepped = True

        out_path = getattr(self.ResultDockwidget, "outPath", "")
        if not os.path.exists(out_path):
            self.pushMessage(self.tr("Results file not found. Please run the model."), level=1)
            return

        from ..ui.analysis.qgisred_results_binary import getOut_TimesNodeProperty, getOut_TimesLinkProperty, getOut_Metadata

        y_data = []
        if category == "Node":
            y_data = getOut_TimesNodeProperty(out_path, element_id, prop_internal)
        else:
            y_data = getOut_TimesLinkProperty(out_path, element_id, prop_internal)

        if not y_data:
            return

        # Simple time series (hours)
        with open(out_path, 'rb') as f:
            meta = getOut_Metadata(f)
            report_start = meta["report_start"]
            report_step = meta["report_step"]
            num_periods = meta["num_periods"]
            x_data = [(report_start + i * report_step) / 3600.0 for i in range(num_periods)]

        title = f"{category} {element_id}: {prop_display}"

        # Refine title with specific type from layer if possible
        if layer:
            identifier = layer.customProperty("qgisred_identifier")
            type_mapping = {
                "qgisred_junctions": self.tr("Junction"),
                "qgisred_tanks": self.tr("Tank"),
                "qgisred_reservoirs": self.tr("Reservoir"),
                "qgisred_pipes": self.tr("Pipe"),
                "qgisred_valves": self.tr("Valve"),
                "qgisred_pumps": self.tr("Pump")
            }
            specific_type = type_mapping.get(identifier, category)
            title = f"{specific_type} {element_id} - {prop_display}"

        y_categorical_labels = None
        y_label_with_unit = prop_display
        if prop_internal == "Status":
            is_stepped = True
            # Map category strings to numbers: Closed -> 0, Active -> 1, Open -> 2
            mapped_data = []
            for status in y_data:
                status_upper = str(status).upper()
                if "CLOSED" in status_upper:
                    mapped_data.append(0)
                elif "ACTIVE" in status_upper:
                    mapped_data.append(1)
                elif "OPEN" in status_upper:
                    mapped_data.append(2)
                else:
                    mapped_data.append(0) # Default to closed if unknown
            y_data = mapped_data
            y_categorical_labels = [self.tr("Closed"), self.tr("Active"), self.tr("Open")]
        else:
            unit_abbr = QGISRedFieldUtils().getResultPropertyUnit(category, prop_internal)
            if unit_abbr:
                y_label_with_unit = f"{prop_display} ({unit_abbr})"

        translated_time = self.tr("Time")
        self.timeSeriesDock.updatePlot(x_data, y_data, title, f"{translated_time} (h)", y_label_with_unit, is_stepped, y_categorical_labels)

    def refreshTimeSeries(self):
        if hasattr(self, 'timeSeriesDock') and self.timeSeriesDock:
            self.performTimeSeriesPlotUpdate(self.lastTimeSeriesFeature, self.lastTimeSeriesCategory, self.lastTimeSeriesLayer)
