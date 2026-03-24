# -*- coding: utf-8 -*-
"""Analysis and results section for QGISRed (model, results dock, time series, export)."""

import os
import json

from qgis.core import QgsRectangle
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool
from ..ui.analysis.qgisred_results_dock import QGISRedResultsDock
from ..ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock


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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.AnalysisOptions(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        # Message
        if "True" in resMessage:
            resMessage = resMessage.replace("True:", "")
            self.unitsAction.setText("QGISRed: " + resMessage)
            self.hasToOpenNewLayers = False
            self.hasToOpenIssuesLayers = False
            self.extent = QGISRedLayerUtils().getProjectExtent()
            self.removingLayers = True
            QGISRedLayerUtils().runTask(self.removeDBFs, self.runOpenTemporaryFiles)
        elif resMessage == "commit":
            self.processCsharpResult(resMessage, "Pipe's roughness converted")
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif resMessage == "Cancelled":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runModel(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Results Dock
        if self.ResultDockwidget is None:
            self.readOptions()
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.ResultDockwidget)
            # activeInputGroup is defined in LayerManagementSection
            self.ResultDockwidget.visibilityChanged.connect(self.activeInputGroup)
            self.ResultDockwidget.simulationFinished.connect(self.refreshTimeSeries)
            self.ResultDockwidget.resultPropertyChanged.connect(self.refreshTimeSeries)
        self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        self.connectElementExplorerToResultsDock()

    def runShowResultsDock(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.ResultDockwidget is None:
            self.runModel()
        else:
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

        # Open Results dock and switch to Report tab
        if self.ResultDockwidget is None:
            self.runModel()
        else:
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
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ExportToInp(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "True":
            self.iface.messageBar().pushMessage(
                self.tr("Information"), self.tr("INP file successfully exported"), level=3, duration=5
            )
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(
                self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5
            )
        elif not resMessage == "Cancelled":
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runTimeSeries(self):
        if self.timeSeriesButton.isChecked():
            # 1. Basic Validations
            self.defineCurrentProject()
            if not self.isValidProject() or self.isLayerOnEdition():
                self.iface.messageBar().pushMessage(
                    self.tr("Time Series"),
                    self.tr("Necessary to have a valid project and no layer on edition."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            # 2. Results Validation
            results_ready = False
            if hasattr(self, 'ResultDockwidget') and self.ResultDockwidget:
                # check if results dock matches current project
                if self.ResultDockwidget.isCurrentProject():
                    # check if .out file exists
                    out_path = getattr(self.ResultDockwidget, "outPath", "")
                    if out_path and os.path.exists(out_path):
                        results_ready = True

            if not results_ready:
                self.iface.messageBar().pushMessage(
                    self.tr("Time Series"),
                    self.tr("It is necessary to simulate first."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            self.runTimeSeriesSelectPointTool()
            if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
                self.timeSeriesDock = QGISRedTimeSeriesDock(self.iface)
                self.timeSeriesDock.visibilityChanged.connect(self.timeSeriesDockVisibilityChanged)
                self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.timeSeriesDock)
            self.timeSeriesDock.show()
            self.timeSeriesDock.raise_()
            self.timeSeriesDock.setFocus()
        else:
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools["TimeSeries"]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])

    def runTimeSeriesSelectPointTool(self):
        self.myMapTools["TimeSeries"] = QGISRedSelectPointTool(self.timeSeriesButton, self, self.timeSeriesCallback, 2, cursor=":/images/iconTimeSeries.svg")
        self.iface.mapCanvas().setMapTool(self.myMapTools["TimeSeries"])

    def timeSeriesDockVisibilityChanged(self, visible):
        if not visible:
            self.timeSeriesButton.setChecked(False)
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools.get("TimeSeries"):
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])

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
            self.iface.messageBar().pushMessage(self.tr("Time Series"), self.tr("No network element found at this location."), level=1)
            return

        self.lastTimeSeriesFeature = found_feature
        self.lastTimeSeriesCategory = category
        self.lastTimeSeriesLayer = layer
        self.performTimeSeriesPlotUpdate(found_feature, category, layer)

    def getUnitSystem(self):
        """Determine if the project uses SI or US units based on the status bar text."""
        if hasattr(self, 'unitsAction'):
            text = self.unitsAction.text()
            # Common US units in EPANET: CFS, GPM, MGD, IMGD, AFD
            us_flow_units = ["CFS", "GPM", "MGD", "IMGD", "AFD"]
            for unit in us_flow_units:
                if unit in text.upper():
                    return "US"
        return "SI"

    def getPropertyUnit(self, category, prop_internal):
        """Fetch the unit abbreviation for a property from qgisred_units.json."""
        try:
            if not category or not prop_internal:
                return ""

            units_path = os.path.join(self.plugin_dir, "defaults", "qgisred_units.json")
            if not os.path.exists(units_path):
                return ""

            with open(units_path, "r", encoding="utf-8") as f:
                units_data = json.load(f)

            system = self.getUnitSystem()

            # Map internal property names to JSON keys
            prop_map = {
                ("Node", "Pressure"): "qgisred_results_node_pressure",
                ("Node", "Head"): "qgisred_results_node_head",
                ("Node", "Demand"): "qgisred_results_node_demand",
                ("Node", "Quality"): "qgisred_results_node_quality",
                ("Link", "Flow"): "qgisred_results_link_flow",
                ("Link", "Velocity"): "qgisred_results_link_velocity",
                ("Link", "HeadLoss"): "qgisred_results_link_headloss",
                ("Link", "UnitHdLoss"): "qgisred_results_link_unitheadloss",
                ("Link", "FricFactor"): "qgisred_results_link_frictionfactor",
                ("Link", "ReactRate"): "qgisred_results_link_reactrate",
                ("Link", "Quality"): "qgisred_results_link_quality"
            }

            key = prop_map.get((category, prop_internal))
            if not key:
                return ""

            cat_key = "Nodes" if category == "Node" else "Links"
            prop_data = units_data.get(cat_key, {}).get(key, {})

            unit_info = prop_data.get(system)
            if not unit_info:
                return ""

            abbr = unit_info.get("abbr", "")
            name = unit_info.get("name", "")

            if name == "Same as Flow" or not abbr or abbr == "-":
                # Recursively get flow units
                flow_key = "qgisred_results_link_flow"
                flow_data = units_data.get("Links", {}).get(flow_key, {}).get(system, {})
                return flow_data.get("abbr", "")

            return abbr
        except Exception:
            return ""

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
            self.iface.messageBar().pushMessage(self.tr("Time Series"), self.tr("Results file not found. Please run the model."), level=1)
            return

        from ..tools.qgisred_results import getOut_TimesNodeProperty, getOut_TimesLinkProperty, _get_out_file_metadata

        y_data = []
        if category == "Node":
            y_data = getOut_TimesNodeProperty(out_path, element_id, prop_internal)
        else:
            y_data = getOut_TimesLinkProperty(out_path, element_id, prop_internal)

        if not y_data:
            return

        # Simple time series (hours)
        with open(out_path, 'rb') as f:
            meta = _get_out_file_metadata(f)
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
            unit_abbr = self.getPropertyUnit(category, prop_internal)
            if unit_abbr:
                y_label_with_unit = f"{prop_display} ({unit_abbr})"

        translated_time = self.tr("Time")
        self.timeSeriesDock.updatePlot(x_data, y_data, title, f"{translated_time} (h)", y_label_with_unit, is_stepped, y_categorical_labels)

    def refreshTimeSeries(self):
        if hasattr(self, 'timeSeriesDock') and self.timeSeriesDock:
            self.performTimeSeriesPlotUpdate(self.lastTimeSeriesFeature, self.lastTimeSeriesCategory, self.lastTimeSeriesLayer)
