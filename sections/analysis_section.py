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
                self.timeSeriesDock.seriesReordered.connect(self._onTimeSeriesSeriesReordered)
                self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.timeSeriesDock)
            self._ensureTimeSeriesMapToolSignal()
            self.timeSeriesDock.show()
            self.timeSeriesDock.raise_()
            self.timeSeriesDock.setFocus()
            try:
                last_feat = getattr(self, "lastTimeSeriesFeature", None)
                last_layer = getattr(self, "lastTimeSeriesLayer", None)
                if last_feat is not None and last_layer is not None:
                    self._setTimeSeriesHighlight(last_layer, last_feat)
            except Exception:
                pass
        else:
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools["TimeSeries"]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
            self._clearTimeSeriesHighlight()

    def runTimeSeriesSelectPointTool(self):
        self.myMapTools["TimeSeries"] = QGISRedSelectPointTool(
            self.timeSeriesButton,
            self,
            self.timeSeriesCallback,
            SelectPointType.Line,
            cursor=":/images/iconTimeSeries.svg",
            pass_modifiers=True
        )
        self.iface.mapCanvas().setMapTool(self.myMapTools["TimeSeries"])

    def _ensureTimeSeriesMapToolSignal(self):
        """Clear highlight when TimeSeries tool is no longer the active map tool."""
        if getattr(self, "_timeSeriesMapToolSignalConnected", False):
            return
        try:
            self.iface.mapCanvas().mapToolSet.connect(self._onMapToolSetForTimeSeries)
            self._timeSeriesMapToolSignalConnected = True
        except Exception:
            self._timeSeriesMapToolSignalConnected = False

    def _onMapToolSetForTimeSeries(self, tool):
        try:
            ts_tool = self.myMapTools.get("TimeSeries")
        except Exception:
            ts_tool = None
        if ts_tool is None:
            self._clearTimeSeriesHighlight()
            self._clearTimeSeriesMapSelection()
            return
        if tool is not ts_tool:
            self._clearTimeSeriesHighlight()
            self._clearTimeSeriesMapSelection()

    def _onTimeSeriesDockDestroyed(self, *_args):
        self.timeSeriesDock = None
        self._clearTimeSeriesHighlight()
        self._clearTimeSeriesMapSelection()

    def timeSeriesDockVisibilityChanged(self, visible):
        if not visible:
            self.timeSeriesButton.setChecked(False)
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools.get("TimeSeries"):
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
            self._clearTimeSeriesHighlight()
            self._clearTimeSeriesMapSelection()

    def _clearTimeSeriesHighlight(self):
        # Clear all stored highlights for Time Series selections
        highlights = getattr(self, "timeSeriesHighlights", None)
        if isinstance(highlights, dict):
            for _k, h in list(highlights.items()):
                try:
                    h.hide()
                except Exception:
                    pass
            highlights.clear()
        self.timeSeriesHighlights = {}
        self.timeSeriesHighlight = None

    def _clearTimeSeriesMapSelection(self):
        """Clear QGIS feature selection performed by the Time Series tool."""
        try:
            layers = QGISRedLayerUtils().getLayers()
        except Exception:
            layers = []
        for l in layers:
            try:
                identifier = l.customProperty("qgisred_identifier")
            except Exception:
                identifier = None
            if identifier in (
                "qgisred_junctions", "qgisred_tanks", "qgisred_reservoirs",
                "qgisred_pipes", "qgisred_valves", "qgisred_pumps"
            ):
                try:
                    l.removeSelection()
                except Exception:
                    pass

    def _setTimeSeriesHighlight(self, layer, feature, color=None, width=5):
        """Add/update highlight for a single feature (does not clear others)."""
        if layer is None or feature is None:
            return
        try:
            if not hasattr(self, "timeSeriesHighlights") or not isinstance(self.timeSeriesHighlights, dict):
                self.timeSeriesHighlights = {}
            highlight = QgsHighlight(self.iface.mapCanvas(), feature.geometry(), layer)
            highlight.setColor(color if isinstance(color, QColor) else QColor("blue"))
            highlight.setWidth(int(width) if width else 5)
            highlight.show()
            key = (layer.id(), str(feature.attribute("ID")))
            # Replace previous highlight for same key
            old = self.timeSeriesHighlights.get(key)
            if old is not None:
                try:
                    old.hide()
                except Exception:
                    pass
            self.timeSeriesHighlights[key] = highlight
            self.timeSeriesHighlight = highlight
        except Exception:
            self.timeSeriesHighlight = None

    def _syncTimeSeriesHighlights(self, last_clicked_layer=None, last_clicked_feature=None):
        """Ensure all selected items keep a visible highlight."""
        # Rebuild highlights from current selection for simplicity/robustness
        self._clearTimeSeriesHighlight()
        selection = getattr(self, "timeSeriesSelection", None) or []
        if not selection:
            return

        for idx, it in enumerate(selection):
            layer = it.get("layer")
            feat = it.get("feature")
            if layer is None or feat is None:
                continue
            is_last = (layer is last_clicked_layer) and (feat is last_clicked_feature)
            color = it.get("color") if isinstance(it.get("color"), QColor) else QColor(0, 120, 215)
            width = 7 if is_last else 5
            self._setTimeSeriesHighlight(layer, feat, color=color, width=width)

    def timeSeriesCallback(self, point, modifiers=None):
        self.updateTimeSeriesPlot(point, modifiers)

    def _timeSeriesIsAdditive(self, modifiers):
        try:
            if modifiers is None:
                return False
            return bool(modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier))
        except Exception:
            return False

    def _timeSeriesResetSelection(self):
        self.timeSeriesSelection = []
        self._timeSeriesSelectionKey = None

    def updateTimeSeriesPlot(self, point, modifiers=None):
        if not hasattr(self, 'timeSeriesDock') or self.timeSeriesDock is None:
            return
        add_mode = self._timeSeriesIsAdditive(modifiers)
        try:
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier) if modifiers is not None else False
        except Exception:
            is_shift = False
        if not hasattr(self, "timeSeriesSelection"):
            self.timeSeriesSelection = []
        if not hasattr(self, "_timeSeriesSelectionKey"):
            self._timeSeriesSelectionKey = None

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

        if not add_mode:
            self._timeSeriesResetSelection()
            self._clearTimeSeriesMapSelection()

        # Append new selection if not already present
        try:
            fid = found_feature.id()
        except Exception:
            fid = None
        element_id = str(found_feature.attribute("ID"))
        layer_identifier = layer.customProperty("qgisred_identifier") if layer else ""

        # Stable color per element (do not depend on current order)
        palette = [
            QColor(0, 120, 215), QColor(220, 57, 18), QColor(16, 150, 24),
            QColor(153, 0, 153), QColor(0, 153, 198), QColor(255, 153, 0),
            QColor(60, 180, 75), QColor(145, 30, 180)
        ]
        existing_color = None
        for it in self.timeSeriesSelection:
            if it.get("layer_identifier") == layer_identifier and it.get("element_id") == element_id:
                existing_color = it.get("color")
                break
        if existing_color is None:
            try:
                existing_color = palette[len(self.timeSeriesSelection) % len(palette)]
            except Exception:
                existing_color = QColor(0, 120, 215)
        sel_item = {
            "layer": layer,
            "layer_identifier": layer_identifier,
            "feature": found_feature,
            "feature_id": fid,
            "category": category,
            "element_id": element_id,
            "color": existing_color,
        }

        # Check if already selected (for shift-toggle)
        existing_idx = None
        for i, it in enumerate(self.timeSeriesSelection):
            if it.get("layer_identifier") == layer_identifier and it.get("element_id") == element_id:
                existing_idx = i
                break

        # Shift+click toggles: if already selected, remove it and refresh
        if is_shift and existing_idx is not None:
            try:
                self.timeSeriesSelection.pop(existing_idx)
            except Exception:
                pass
            if not self.timeSeriesSelection:
                self._timeSeriesResetSelection()
                self._clearTimeSeriesMapSelection()
                self._clearTimeSeriesHighlight()
                # Clear plot
                try:
                    self.timeSeriesDock.updatePlotSeries([], "", "", "")
                except Exception:
                    pass
                return

            # Update map selection for the relevant layer
            try:
                remaining_ids = [it.get("feature_id") for it in self.timeSeriesSelection if it.get("layer_identifier") == layer_identifier and it.get("feature_id") is not None]
                if layer is not None:
                    layer.selectByIds(remaining_ids)
            except Exception:
                pass

            # Keep highlights and plot in sync
            self._syncTimeSeriesHighlights(self.lastTimeSeriesLayer, self.lastTimeSeriesFeature)
            self._renderTimeSeriesSelection()
            return

        # Set/validate selection key: (category, layer_identifier, prop_internal)
        key = self._getCurrentTimeSeriesKey(category, layer)
        if key is None:
            return
        if self._timeSeriesSelectionKey is None:
            self._timeSeriesSelectionKey = key
        elif self._timeSeriesSelectionKey != key:
            self.pushMessage(
                self.tr("To overlay curves, keep the same element type and the same result magnitude."),
                level=1, duration=5
            )
            return

        if existing_idx is None:
            self.timeSeriesSelection.append(sel_item)

        # Keep QGIS selection in sync (real map selection)
        try:
            selected_ids = []
            for it in self.timeSeriesSelection:
                if it.get("layer_identifier") == layer_identifier and it.get("feature_id") is not None:
                    selected_ids.append(it.get("feature_id"))
            if layer and selected_ids:
                layer.selectByIds(selected_ids)
        except Exception:
            pass

        # Keep highlights for all selected elements (and emphasize last clicked)
        self.lastTimeSeriesFeature = found_feature
        self.lastTimeSeriesCategory = category
        self.lastTimeSeriesLayer = layer
        self._syncTimeSeriesHighlights(layer, found_feature)

        self._renderTimeSeriesSelection()

    def _getCurrentTimeSeriesKey(self, category, layer):
        """Return (category, layer_identifier, prop_internal, prop_display, is_stepped, y_categorical_labels, y_label_with_unit)."""
        prop_internal = ""
        prop_display = ""
        is_stepped = False
        y_categorical_labels = None
        y_label_with_unit = ""

        if not (hasattr(self, 'ResultDockwidget') and self.ResultDockwidget):
            self.pushMessage(self.tr("Results panel not available."), level=1, duration=5)
            return None

        if category == "Node":
            prop_display = self.ResultDockwidget.cbNodes.currentText()
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
                y_categorical_labels = [self.tr("Closed"), self.tr("Active"), self.tr("Open")]

        unit_abbr = QGISRedFieldUtils().getResultPropertyUnit(category, prop_internal)
        if unit_abbr:
            y_label_with_unit = f"{prop_display} ({unit_abbr})"
        else:
            y_label_with_unit = prop_display

        layer_identifier = layer.customProperty("qgisred_identifier") if layer else ""
        return (category, layer_identifier, prop_internal, prop_display, is_stepped, y_categorical_labels, y_label_with_unit)

    def _renderTimeSeriesSelection(self):
        if not self.timeSeriesSelection:
            return
        if self._timeSeriesSelectionKey is None:
            return

        category, layer_identifier, prop_internal, prop_display, is_stepped, y_categorical_labels, y_label_with_unit = self._timeSeriesSelectionKey

        out_path = getattr(self.ResultDockwidget, "outPath", "")
        if not os.path.exists(out_path):
            self.pushMessage(self.tr("Results file not found. Please run the model."), level=1)
            return

        from ..ui.analysis.qgisred_results_binary import getOut_TimesNodeProperty, getOut_TimesLinkProperty, getOut_Metadata

        # X values (hours)
        with open(out_path, 'rb') as f:
            meta = getOut_Metadata(f)
            report_start = meta["report_start"]
            report_step = meta["report_step"]
            num_periods = meta["num_periods"]
            x_data = [(report_start + i * report_step) / 3600.0 for i in range(num_periods)]

        series = []
        for idx, it in enumerate(self.timeSeriesSelection):
            element_id = it.get("element_id")
            layer = it.get("layer")
            if not element_id:
                continue
            if category == "Node":
                y_data = getOut_TimesNodeProperty(out_path, element_id, prop_internal)
            else:
                y_data = getOut_TimesLinkProperty(out_path, element_id, prop_internal)
            if not y_data:
                continue

            # Status mapping if needed
            if prop_internal == "Status":
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
                        mapped_data.append(0)
                y_data = mapped_data

            # Label uses specific type if available
            label = f"{element_id}"
            legend_type = category
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
                label = f"{specific_type} {element_id}"
                legend_type = identifier or category

            series.append({
                "x": x_data,
                "y": y_data,
                "label": label,
                "color": it.get("color") if isinstance(it.get("color"), QColor) else QColor(0, 120, 215),
                "is_stepped": bool(is_stepped),
                "y_categorical_labels": y_categorical_labels,
                "legend_type": legend_type,
                "series_key": f"{layer_identifier}:{element_id}",
            })

        if not series:
            return

        translated_time = self.tr("Time")
        title = f"{prop_display}"
        self.timeSeriesDock.updatePlotSeries(series, title, f"{translated_time} (h)", y_label_with_unit)

    def _onTimeSeriesSeriesReordered(self, order_keys):
        """Reorder selected elements based on legend drag & drop."""
        try:
            if not order_keys or not hasattr(self, "timeSeriesSelection") or not self.timeSeriesSelection:
                return
            key_to_item = {}
            for it in self.timeSeriesSelection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                key_to_item[f"{li}:{eid}"] = it
            new_sel = []
            for k in order_keys:
                if k in key_to_item:
                    new_sel.append(key_to_item[k])
            # Keep any items not present (e.g. legend limit) at the end
            for it in self.timeSeriesSelection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                k = f"{li}:{eid}"
                if k not in order_keys:
                    new_sel.append(it)
            self.timeSeriesSelection = new_sel
            self._renderTimeSeriesSelection()
            # Preserve highlights emphasis on last clicked
            try:
                self._syncTimeSeriesHighlights(self.lastTimeSeriesLayer, self.lastTimeSeriesFeature)
            except Exception:
                pass
        except Exception:
            return

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

        element_label = f"{category} {element_id}"
        title = f"{element_label}: {prop_display}"

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
            element_label = f"{specific_type} {element_id}"
            title = f"{element_label} - {prop_display}"

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
        self.timeSeriesDock.updatePlot(
            x_data,
            y_data,
            title,
            f"{translated_time} (h)",
            y_label_with_unit,
            is_stepped,
            y_categorical_labels,
            element_label,
        )

    def refreshTimeSeries(self):
        if hasattr(self, 'timeSeriesDock') and self.timeSeriesDock:
            # Nothing selected yet
            if not hasattr(self, "lastTimeSeriesFeature") or not hasattr(self, "lastTimeSeriesCategory") or not hasattr(self, "lastTimeSeriesLayer"):
                return
            if hasattr(self, "timeSeriesSelection") and self.timeSeriesSelection:
                # Recompute key and rerender all series for current magnitude
                try:
                    key = self._getCurrentTimeSeriesKey(self.lastTimeSeriesCategory, self.lastTimeSeriesLayer)
                    if key is not None:
                        self._timeSeriesSelectionKey = key
                        self._renderTimeSeriesSelection()
                        return
                except Exception:
                    pass
            self.performTimeSeriesPlotUpdate(self.lastTimeSeriesFeature, self.lastTimeSeriesCategory, self.lastTimeSeriesLayer)
