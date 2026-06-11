# -*- coding: utf-8 -*-
"""Analysis and results section for QGISRed (model, results dock, time series, export)."""

import os

from qgis.core import QgsRectangle
from qgis.PyQt.QtWidgets import QApplication, QDialog
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsHighlight

from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_filesystem_utils import DIR_RESULTS
from ..tools.utils.qgisred_ui_utils import QGISRedUIUtils
from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ..compat import DIALOG_ACCEPTED
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType
from ..ui.analysis.qgisred_results_dock import QGISRedResultsDock
from ..ui.queries.qgisred_element_explorer_dock import QGISRedElementExplorerDock
from ..ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock
from ..ui.analysis.qgisred_results_data import export_results_to_csv, get_regional_separators


class AnalysisSection:
    @property
    def activeTimeSeriesDock(self):
        return getattr(self, "_activeTimeSeriesDock", None)

    @property
    def timeSeriesDock(self):
        return getattr(self, "_activeTimeSeriesDock", None)

    @property
    def timeSeriesSelection(self):
        dock = self.activeTimeSeriesDock
        return dock.selection if dock is not None else []

    @timeSeriesSelection.setter
    def timeSeriesSelection(self, value):
        dock = self.activeTimeSeriesDock
        if dock is not None:
            dock.selection = value

    @property
    def _timeSeriesSelectionKey(self):
        dock = self.activeTimeSeriesDock
        return dock.selectionKey if dock is not None else None

    @_timeSeriesSelectionKey.setter
    def _timeSeriesSelectionKey(self, value):
        dock = self.activeTimeSeriesDock
        if dock is not None:
            dock.selectionKey = value

    @property
    def lastTimeSeriesLayer(self):
        dock = self.activeTimeSeriesDock
        return dock.lastLayer if dock is not None else None

    @lastTimeSeriesLayer.setter
    def lastTimeSeriesLayer(self, value):
        dock = self.activeTimeSeriesDock
        if dock is not None:
            dock.lastLayer = value

    @property
    def lastTimeSeriesFeature(self):
        dock = self.activeTimeSeriesDock
        return dock.lastFeature if dock is not None else None

    @lastTimeSeriesFeature.setter
    def lastTimeSeriesFeature(self, value):
        dock = self.activeTimeSeriesDock
        if dock is not None:
            dock.lastFeature = value

    @property
    def lastTimeSeriesCategory(self):
        dock = self.activeTimeSeriesDock
        return dock.lastCategory if dock is not None else None

    @lastTimeSeriesCategory.setter
    def lastTimeSeriesCategory(self, value):
        dock = self.activeTimeSeriesDock
        if dock is not None:
            dock.lastCategory = value

    def _resolveTimeSeriesDock(self):
        try:
            dock = self.sender()
        except Exception:
            dock = None
        if isinstance(dock, QGISRedTimeSeriesDock):
            return dock
        return self.activeTimeSeriesDock

    def _restyleTimeSeriesDocks(self):
        active = getattr(self, "_activeTimeSeriesDock", None)
        docks = list(getattr(self, "timeSeriesDocks", []) or [])
        multiple = len(docks) > 1
        for dock in docks:
            try:
                accent = "#0097A7" if (dock is active or not multiple) else "#B0BEC5"
                QGISRedUIUtils.applyDockStyle(dock, accent, backgroundColor="white")
            except Exception:
                pass

    def _applyTimeSeriesMapStateForDock(self, dock):
        if dock is None:
            return
        fids_by_layer = {}
        for it in (getattr(dock, "selection", None) or []):
            layer = it.get("layer")
            fid = it.get("feature_id")
            if layer is None or fid is None:
                continue
            fids_by_layer.setdefault(layer, []).append(fid)
        for layer, fids in fids_by_layer.items():
            try:
                layer.selectByIds(fids)
            except Exception:
                pass
        try:
            self._syncTimeSeriesHighlights(dock.lastLayer, dock.lastFeature, dock=dock)
        except Exception:
            pass

    def _setActiveTimeSeriesDock(self, dock):
        if dock is None:
            return
        previous = getattr(self, "_activeTimeSeriesDock", None)
        if previous is dock:
            return
        self._activeTimeSeriesDock = dock
        if previous is not None:
            try:
                self._clearTimeSeriesHighlight(previous)
            except Exception:
                pass
        self._restyleTimeSeriesDocks()
        try:
            self._clearTimeSeriesMapSelection()
        except Exception:
            pass
        self._applyTimeSeriesMapStateForDock(dock)

    def runAnalysisOptions(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.AnalysisOptions(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        if resMessage == "True":
            self.processCsharpResult("commit", "") #To copy temporal DBF file
            self.readOptions()
        elif resMessage == "commit":
            self.processCsharpResult(resMessage, self.tr("Pipe's roughness converted"))
        elif resMessage == "False":
            self.pushMessage(self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.processCsharpResult(resMessage, "")

    def _outFilePath(self):
        scenario = getattr(self.ResultDockwidget, 'Scenario', 'Base') if self.ResultDockwidget else 'Base'
        return os.path.join(self.ProjectDirectory, DIR_RESULTS, f"{self.NetworkName}_{scenario}.out")

    def _hydFilePath(self):
        scenario = getattr(self.ResultDockwidget, 'Scenario', 'Base') if self.ResultDockwidget else 'Base'
        return os.path.join(self.ProjectDirectory, DIR_RESULTS, f"{self.NetworkName}_{scenario}.hyd")

    def _useHydForTimeSeries(self):
        dock = getattr(self, "ResultDockwidget", None)
        if dock is None:
            return False
        try:
            return bool(dock.isAllCalculationTimesMode())
        except Exception:
            return False

    def _getTimeSeriesSource(self):
        """Return active source metadata for TimeSeries based on Results dock mode."""
        out_path = self._outFilePath()
        if not os.path.exists(out_path):
            return None

        if self._useHydForTimeSeries():
            hyd_path = self._hydFilePath()
            if os.path.exists(hyd_path):
                try:
                    from ..ui.analysis.qgisred_results_hyd import getHyd_Metadata
                    hyd_meta = getHyd_Metadata(hyd_path, out_path)
                    if hyd_meta and hyd_meta.get("hyd_num_periods", 0) > 1:
                        times = list(hyd_meta.get("hyd_times") or [])
                        if not times:
                            start = hyd_meta.get("hyd_report_start", 0)
                            step = hyd_meta.get("hyd_report_step", 0)
                            n = hyd_meta.get("hyd_num_periods", 0)
                            times = [start + i * step for i in range(n)]
                        if times:
                            return {
                                "kind": "hyd",
                                "out_path": out_path,
                                "hyd_path": hyd_path,
                                "times": times,
                                "project_directory": self.ProjectDirectory,
                                "network_name": self.NetworkName,
                            }
                except Exception:
                    pass

        from ..ui.analysis.qgisred_results_binary import getOut_Metadata
        with open(out_path, 'rb') as f:
            meta = getOut_Metadata(f)
        if not meta:
            return None
        start = meta["report_start"]
        step = meta["report_step"]
        times = [start + i * step for i in range(meta["num_periods"])]
        return {
            "kind": "out",
            "out_path": out_path,
            "times": times,
            "project_directory": self.ProjectDirectory,
            "network_name": self.NetworkName,
        }

    def _getSeriesValuesForSource(self, source, category, element_id, prop_internal):
        if source["kind"] == "out":
            from ..ui.analysis.qgisred_results_binary import getOut_TimesNodeProperty, getOut_TimesLinkProperty
            if category == "Node":
                return getOut_TimesNodeProperty(source["out_path"], element_id, prop_internal)
            return getOut_TimesLinkProperty(source["out_path"], element_id, prop_internal)

        from ..ui.analysis.qgisred_results_hyd import getHyd_TimeNodesProperties, getHyd_TimeLinksProperties
        out_path = source["out_path"]
        hyd_path = source["hyd_path"]
        values = []
        for t in source["times"]:
            if category == "Node":
                step_results = getHyd_TimeNodesProperties(hyd_path, out_path, t)
            else:
                step_results = getHyd_TimeLinksProperties(hyd_path, out_path, t)
            v = step_results.get(element_id, {}).get(prop_internal)
            values.append(v)
        return values

    def _arrangeDocksIfVisible(self, visible):
        if not visible:
            return
        QGISRedUIUtils.arrangeDockOrder(
            self.iface.mainWindow(),
            self.ResultDockwidget,
            QGISRedElementExplorerDock._instance,
            getattr(self, 'queriesByPropertiesDock', None),
            getattr(self, 'statisticsDock', None)
        )

    def _onStatisticsModeChanged(self, _stat):
        self.updateMetadata()

    def _initResultsDock(self):
        if self.ResultDockwidget is None:
            self.readOptions()
            self.ResultDockwidget = QGISRedResultsDock(self.iface)
            self.ResultDockwidget.restoreDisplayPreferences(self.ProjectDirectory, self.NetworkName)
            self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ResultDockwidget)
            self.ResultDockwidget.visibilityChanged.connect(self.activeInputGroup)
            self.ResultDockwidget.visibilityChanged.connect(self._arrangeDocksIfVisible)
            self.ResultDockwidget.simulationFinished.connect(self.refreshTimeSeries)
            self.ResultDockwidget.simulationFinished.connect(self._staleLayerManager.forceCheck)
            try:
                self.ResultDockwidget.cbResultTimes.currentIndexChanged.connect(self.refreshTimeSeries)
            except Exception:
                pass
            self.ResultDockwidget.simulationFinished.connect(self.updateMetadata)
            self.ResultDockwidget.resultPropertyChanged.connect(self.updateMetadata)
            self.ResultDockwidget.statisticsModeChanged.connect(self._onStatisticsModeChanged)

    def _ensureResultsDockVisibleForTimeSeries(self):
        self._initResultsDock()
        try:
            self.defineCurrentProject()
        except Exception:
            return

        if not self.isValidProject():
            return
        try:
            has_loaded = bool(getattr(self.ResultDockwidget, "outPath", "")) and bool(self.ResultDockwidget.TimeLabels)
        except Exception:
            has_loaded = False

        if not has_loaded:
            out_path = self._outFilePath()
            if os.path.exists(out_path):
                try:
                    self.ResultDockwidget.loadExistingResults(self.ProjectDirectory, self.NetworkName)
                except Exception:
                    pass

        try:
            self.ResultDockwidget.show()
            self.ResultDockwidget.raise_()
            QGISRedUIUtils.arrangeDockOrder(
                self.iface.mainWindow(),
                self.ResultDockwidget,
                QGISRedElementExplorerDock._instance,
                getattr(self, 'queriesByPropertiesDock', None)
            )
        except Exception:
            pass

    def runModel(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self._initResultsDock()
        self.ResultDockwidget.simulate(self.ProjectDirectory, self.NetworkName)
        QGISRedUIUtils.arrangeDockOrder(
            self.iface.mainWindow(),
            self.ResultDockwidget,
            QGISRedElementExplorerDock._instance,
            getattr(self, 'queriesByPropertiesDock', None),
            getattr(self, 'statisticsDock', None)
        )
        self.connectElementExplorerToResultsDock()

    def runShowResultsDock(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return

        self._initResultsDock()
        QGISRedUIUtils.arrangeDockOrder(
            self.iface.mainWindow(),
            self.ResultDockwidget,
            QGISRedElementExplorerDock._instance,
            getattr(self, 'queriesByPropertiesDock', None),
            getattr(self, 'statisticsDock', None)
        )
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
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        self._initResultsDock()
        QGISRedUIUtils.arrangeDockOrder(
            self.iface.mainWindow(),
            self.ResultDockwidget,
            QGISRedElementExplorerDock._instance,
            getattr(self, 'queriesByPropertiesDock', None),
            getattr(self, 'statisticsDock', None)
        )
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
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ExportToInp(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

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

        results_dir = os.path.join(self.ProjectDirectory, DIR_RESULTS)
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
            self.defineCurrentProject()
            if not self.isValidProject() or self.isLayerOnEdition():
                self.pushMessage(
                    self.tr("Necessary to have a valid project and no layer on edition."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            results_ready = False
            if self.ResultDockwidget:
                out_path = getattr(self.ResultDockwidget, 'outPath', '')
                if out_path and os.path.exists(out_path) and self.ResultDockwidget.isCurrentProject():
                    results_ready = True
            if not results_ready and os.path.exists(self._outFilePath()):
                results_ready = True

            if not results_ready:
                self.pushMessage(
                    self.tr("It is necessary to simulate first."),
                    level=1, duration=5
                )
                self.timeSeriesButton.setChecked(False)
                return

            self._ensureResultsDockVisibleForTimeSeries()

            self.runTimeSeriesSelectPointTool()
            self._ensureTimeSeriesMapToolSignal()
            if not getattr(self, "timeSeriesDocks", None):
                dock = self._createTimeSeriesDock()
            else:
                for d in list(self.timeSeriesDocks):
                    try:
                        d.show()
                    except Exception:
                        pass
                dock = self.activeTimeSeriesDock or self.timeSeriesDocks[-1]
            self._setActiveTimeSeriesDock(dock)
            dock.show()
            dock.raise_()
            dock.setFocus()
            self._restoreTimeSeriesState()
        else:
            if "TimeSeries" in self.myMapTools and self.iface.mapCanvas().mapTool() == self.myMapTools["TimeSeries"]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
            self._clearTimeSeriesHighlight()

    def _createTimeSeriesDock(self):
        if not getattr(self, "timeSeriesDocks", None):
            self.timeSeriesDocks = []
        dock = QGISRedTimeSeriesDock(self.iface)
        self._timeSeriesDockCounter = int(getattr(self, "_timeSeriesDockCounter", 0)) + 1
        base_title = dock.windowTitle() or self.tr("Time series")
        dock.setWindowTitle(f"{base_title} {self._timeSeriesDockCounter}")
        dock.visibilityChanged.connect(self.timeSeriesDockVisibilityChanged)
        dock.destroyed.connect(self._onTimeSeriesDockDestroyed)
        dock.seriesReordered.connect(lambda order, d=dock: self._onTimeSeriesSeriesReordered(order, d))
        dock.seriesRemoved.connect(lambda key, d=dock: self._onTimeSeriesSeriesRemoved(key, d))
        dock.seriesEmphasisChanged.connect(lambda payload, d=dock: self._onTimeSeriesSeriesEmphasisChanged(payload, d))
        dock.curveSettingsChanged.connect(lambda settings, d=dock: self._onTimeSeriesCurveSettingsChanged(settings, d))
        dock.clearAllRequested.connect(lambda d=dock: self._onTimeSeriesClearAllRequested(d))
        dock.exportConfigRequested.connect(lambda path, d=dock: self._onTimeSeriesExportConfig(path, d))
        dock.importConfigRequested.connect(lambda path, d=dock: self._onTimeSeriesImportConfig(path, d))
        dock.globalSystemVariableChosen.connect(lambda key, d=dock: self._onTimeSeriesGlobalSystemVariable(key, d))
        dock.newChartRequested.connect(self._onTimeSeriesNewChartRequested)
        dock.activated.connect(lambda d=dock: self._onTimeSeriesDockActivated(d))
        self.timeSeriesDocks.append(dock)
        self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        try:
            dock.connectResultsDock(self.ResultDockwidget)
        except Exception:
            pass
        return dock

    def _onTimeSeriesNewChartRequested(self):
        anchor = self.activeTimeSeriesDock
        dock = self._createTimeSeriesDock()
        try:
            if anchor is not None and anchor is not dock:
                self.iface.mainWindow().tabifyDockWidget(anchor, dock)
        except Exception:
            pass
        dock.show()
        dock.raise_()
        dock.setFocus()
        self._setActiveTimeSeriesDock(dock)

        def _finishNewChartActivation():
            try:
                dock.raise_()
            except Exception:
                pass
            self._setActiveTimeSeriesDock(dock)

        QTimer.singleShot(0, _finishNewChartActivation)

    def _onTimeSeriesDockActivated(self, dock=None):
        if dock is None:
            dock = self._resolveTimeSeriesDock()
        if dock is not None:
            self._setActiveTimeSeriesDock(dock)

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

    def _onTimeSeriesGlobalSystemVariable(self, variable_key: str, dock=None):
        if dock is None:
            dock = self._resolveTimeSeriesDock()
        self._addTimeSeriesGlobalVariable(str(variable_key or "").strip(), dock=dock)

    def _addTimeSeriesGlobalVariable(self, variable_key: str, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if not variable_key or dock is None:
            return

        from ..ui.analysis.timeseries_globals import (
            GLOBAL_SYSTEM_VARIABLE_KEYS,
            get_global_timeseries,
            global_series_y_display_decimals,
            global_variable_display_label,
            global_variable_legend_label,
        )

        if variable_key not in GLOBAL_SYSTEM_VARIABLE_KEYS:
            return

        prop_internal = variable_key
        prop_display = global_variable_display_label(variable_key)
        y_label_with_unit = global_variable_legend_label(variable_key)

        palette = [
            QColor(0, 120, 215), QColor(220, 57, 18), QColor(16, 150, 24),
            QColor(153, 0, 153), QColor(0, 153, 198), QColor(255, 153, 0),
            QColor(60, 180, 75), QColor(145, 30, 180)
        ]
        element_id = variable_key
        layer_identifier = "global"
        category = "Global"

        existing_idx = None
        for i, it in enumerate(dock.selection):
            if (
                it.get("category") == category
                and it.get("element_id") == element_id
                and it.get("prop_internal") == prop_internal
            ):
                existing_idx = i
                break

        if existing_idx is not None:
            self.pushMessage(
                self.tr("This system variable is already on the chart."),
                level=0,
                duration=3,
            )
            return

        try:
            existing_color = palette[len(dock.selection) % len(palette)]
        except Exception:
            existing_color = QColor(0, 120, 215)

        dock.selection.append({
            "layer": None,
            "layer_identifier": layer_identifier,
            "feature": None,
            "feature_id": None,
            "category": category,
            "element_id": element_id,
            "color": existing_color,
            "prop_internal": prop_internal,
            "prop_display": prop_display,
            "y_label_with_unit": y_label_with_unit,
            "y_display_decimals": global_series_y_display_decimals(variable_key),
            "is_stepped": False,
            "y_categorical_labels": None,
        })

        source = self._getTimeSeriesSource()
        if not source:
            self.pushMessage(self.tr("Results file not found. Please run the model."), level=1)
            dock.selection.pop()
            return
        if not get_global_timeseries(source, variable_key):
            self.pushMessage(self.tr("Could not read the selected system variable."), level=1)
            dock.selection.pop()
            return

        self._renderTimeSeriesSelection(dock)

    def _ensureTimeSeriesMapToolSignal(self):
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

    def _anyTimeSeriesDockVisible(self):
        for dock in (getattr(self, "timeSeriesDocks", None) or []):
            try:
                if dock.isVisible():
                    return True
            except Exception:
                pass
        return False

    def _firstVisibleTimeSeriesDock(self, exclude=None):
        for dock in (getattr(self, "timeSeriesDocks", None) or []):
            if dock is exclude:
                continue
            try:
                if dock.isVisible():
                    return dock
            except Exception:
                pass
        return None

    def _currentVisibleTimeSeriesDock(self):
        active = self.activeTimeSeriesDock
        try:
            if active is not None and active.isVisible():
                return active
        except Exception:
            pass
        return self._firstVisibleTimeSeriesDock() or active

    def _onTimeSeriesDockDestroyed(self, obj=None):
        docks = list(getattr(self, "timeSeriesDocks", None) or [])
        remaining = [d for d in docks if d is not obj]
        self.timeSeriesDocks = remaining
        active = getattr(self, "_activeTimeSeriesDock", None)
        active_alive = any(d is active for d in remaining)
        if active is obj or not active_alive:
            self._activeTimeSeriesDock = remaining[-1] if remaining else None
        try:
            self._clearTimeSeriesMapSelection()
        except Exception:
            pass
        new_active = self.activeTimeSeriesDock
        if new_active is not None:
            self._applyTimeSeriesMapStateForDock(new_active)
        else:
            try:
                self.timeSeriesButton.setChecked(False)
            except Exception:
                pass
        self._restyleTimeSeriesDocks()

    def _onTimeSeriesClearAllRequested(self, dock=None):
        """Clear all curves and return the dock to its initial empty state."""
        if dock is None:
            dock = self._resolveTimeSeriesDock()
        try:
            has_curves = bool(dock is not None and dock._plotHasCurves())
        except Exception:
            has_curves = bool(getattr(dock, "selection", None))
        if not has_curves:
            return

        if not self._confirmTimeSeriesClearSelection():
            return

        from ..ui.analysis.timeseries_actions import clear_all_timeseries
        clear_all_timeseries(self, dock)

    def _confirmTimeSeriesClearSelection(self):
        from qgis.PyQt.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            None,
            self.tr("Clear selection"),
            self.tr("All selected curves will be lost. Continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def timeSeriesDockVisibilityChanged(self, visible):
        dock = self._resolveTimeSeriesDock()
        if dock is None:
            return

        def _apply_visibility_state():
            really_visible = False
            try:
                really_visible = bool(dock.isVisible())
            except Exception:
                really_visible = False
            if not really_visible:
                self._clearTimeSeriesHighlight(dock)
                if dock is self.activeTimeSeriesDock:
                    next_active = self._firstVisibleTimeSeriesDock(exclude=dock)
                    if next_active is not None:
                        self._setActiveTimeSeriesDock(next_active)
                    else:
                        self._activeTimeSeriesDock = None
                        self._restyleTimeSeriesDocks()
                if not self._anyTimeSeriesDockVisible():
                    self.timeSeriesButton.setChecked(False)
                    if (
                        "TimeSeries" in self.myMapTools
                        and self.iface.mapCanvas().mapTool() == self.myMapTools.get("TimeSeries")
                    ):
                        self.iface.mapCanvas().unsetMapTool(self.myMapTools["TimeSeries"])
                    self._clearTimeSeriesMapSelection()
            else:
                self._setActiveTimeSeriesDock(dock)
                self._restoreTimeSeriesState()

        if visible:
            _apply_visibility_state()
        else:
            QTimer.singleShot(0, _apply_visibility_state)

    def _restoreTimeSeriesState(self):
        selection = getattr(self, "timeSeriesSelection", [])
        if not selection:
            return
        fids_by_layer = {}
        for it in selection:
            layer = it.get("layer")
            feat = it.get("feature")
            if layer is None or feat is None:
                continue
            try:
                fids_by_layer.setdefault(layer, []).append(feat.id())
            except Exception:
                pass
        for layer, fids in fids_by_layer.items():
            try:
                layer.selectByIds(fids)
            except Exception:
                pass
        self._syncTimeSeriesHighlights()
        self._renderTimeSeriesSelection()

    def _clearTimeSeriesHighlight(self, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        highlights = getattr(dock, "highlights", None) if dock is not None else None
        canvas = None
        scene = None
        try:
            canvas = self.iface.mapCanvas()
            scene = canvas.scene() if canvas is not None else None
        except Exception:
            scene = None
        if isinstance(highlights, dict):
            for _k, h in list(highlights.items()):
                try:
                    h.hide()
                except Exception:
                    pass
                if scene is not None and h is not None:
                    try:
                        if h.scene() is scene:
                            scene.removeItem(h)
                    except Exception:
                        pass
            highlights.clear()
        if dock is not None:
            dock.highlights = {}
            dock.highlight = None
        if canvas is not None:
            try:
                canvas.refresh()
            except Exception:
                pass

    def _clearTimeSeriesMapSelection(self):
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

    def _setTimeSeriesHighlight(self, layer, feature, color=None, width=5, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if layer is None or feature is None or dock is None:
            return
        try:
            if not isinstance(getattr(dock, "highlights", None), dict):
                dock.highlights = {}
            highlight = QgsHighlight(self.iface.mapCanvas(), feature.geometry(), layer)
            highlight.setColor(color if isinstance(color, QColor) else QColor("blue"))
            highlight.setWidth(int(width) if width else 5)
            highlight.show()
            key = (layer.id(), str(feature.attribute("ID")))
            old = dock.highlights.get(key)
            if old is not None:
                try:
                    old.hide()
                except Exception:
                    pass
            dock.highlights[key] = highlight
            dock.highlight = highlight
        except Exception:
            dock.highlight = None

    def _syncTimeSeriesHighlights(self, last_clicked_layer=None, last_clicked_feature=None, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if dock is None:
            return
        self._clearTimeSeriesHighlight(dock)
        if dock is not self.activeTimeSeriesDock:
            return
        selection = getattr(dock, "selection", None) or []
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
            self._setTimeSeriesHighlight(layer, feat, color=color, width=width, dock=dock)

    def _onTimeSeriesSeriesEmphasisChanged(self, payload: dict, dock=None):
        """Sync legend emphasis (highlight/mute) to map highlights."""
        if dock is None:
            dock = self._resolveTimeSeriesDock()
        if dock is None or dock is not self.activeTimeSeriesDock:
            return
        try:
            highlighted = set((payload or {}).get("highlighted") or [])
            muted = set((payload or {}).get("muted") or [])
        except Exception:
            highlighted = set()
            muted = set()

        selection = getattr(dock, "selection", None) or []
        if not selection:
            return

        # Map series_key -> selection item, using the same key format as the plot.
        key_to_item = {}
        for it in selection:
            li = it.get("layer_identifier") or ""
            eid = it.get("element_id") or ""
            cat = it.get("category") or ""
            prop = it.get("prop_internal") or ""
            k = f"{cat}:{li}:{prop}:{eid}"
            key_to_item[k] = it

        # If legend says nothing is highlighted/muted, revert to default highlight behavior.
        if not highlighted and not muted:
            try:
                self._syncTimeSeriesHighlights(dock.lastLayer, dock.lastFeature, dock=dock)
            except Exception:
                self._syncTimeSeriesHighlights(dock=dock)
            return

        self._clearTimeSeriesHighlight(dock)

        for k, it in key_to_item.items():
            layer = it.get("layer")
            feat = it.get("feature")
            if layer is None or feat is None:
                continue

            base_color = it.get("color") if isinstance(it.get("color"), QColor) else QColor(0, 120, 215)
            c = QColor(base_color)
            width = 5

            if k in highlighted:
                c.setAlpha(255)
                width = 8
            elif k in muted:
                c.setAlpha(60)
                width = 3
            else:
                c.setAlpha(180)
                width = 5

            self._setTimeSeriesHighlight(layer, feat, color=c, width=width, dock=dock)

    def timeSeriesCallback(self, point, modifiers=None, mouse_button=None):
        self.updateTimeSeriesPlot(point, modifiers, mouse_button)

    def _timeSeriesIsAdditive(self, modifiers):
        try:
            if modifiers is None:
                return False
            return bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        except Exception:
            return False

    def _timeSeriesResetSelection(self, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if dock is None:
            return
        dock.selection = []
        dock.selectionKey = None

    def _timeSeriesMapSelectionItems(self, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        return [
            it for it in (getattr(dock, "selection", None) or [])
            if it.get("category") != "Global"
        ]

    def _timeSeriesResetMapSelection(self, dock=None):
        """Remove map-picked curves but keep system global variables."""
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if dock is None:
            return
        dock.selection = [
            it for it in (getattr(dock, "selection", None) or [])
            if it.get("category") == "Global"
        ]
        dock.selectionKey = None

    def _timeSeriesMagnitudeChoices(self, category, dock):
        if dock is None:
            return []
        try:
            if category == "Node":
                raw = [dock.lbl_pressure, dock.lbl_head, dock.lbl_demand, dock.lbl_quality]
            else:
                raw = [
                    dock.lbl_flow,
                    dock.lbl_velocity,
                    dock.lbl_headloss,
                    dock.lbl_unit_headloss,
                    dock.lbl_friction_factor,
                    dock.lbl_status,
                    dock.lbl_reaction_rate,
                    dock.lbl_quality,
                ]
        except Exception:
            return []
        out = []
        for v in raw:
            if not v:
                continue
            s = str(v).strip()
            if not s or s in out:
                continue
            out.append(s)
        return out

    def _timeSeriesPickMagnitudeFromMenu(self, category, dock):
        try:
            from qgis.PyQt.QtWidgets import QMenu
            from qgis.PyQt.QtGui import QCursor
        except Exception:
            return None

        choices = self._timeSeriesMagnitudeChoices(category, dock)
        if not choices:
            return None

        menu = QMenu()
        menu.setTitle(self.tr("Magnitude"))
        actions = []
        for label in choices:
            actions.append(menu.addAction(label))

        selected = menu.exec_(QCursor.pos())
        if selected is None:
            return None
        try:
            return str(selected.text())
        except Exception:
            return None

    def updateTimeSeriesPlot(self, point, modifiers=None, mouse_button=None):
        target = self._currentVisibleTimeSeriesDock()
        if target is None:
            return
        if target is not self.activeTimeSeriesDock:
            self._setActiveTimeSeriesDock(target)
        try:
            if modifiers is not None and bool(modifiers & Qt.KeyboardModifier.ControlModifier):
                return
        except Exception:
            pass
        add_mode = self._timeSeriesIsAdditive(modifiers)
        try:
            is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier) if modifiers is not None else False
        except Exception:
            is_shift = False
        if not hasattr(self, "timeSeriesSelection"):
            self.timeSeriesSelection = []
        if not hasattr(self, "_timeSeriesSelectionKey"):
            self._timeSeriesSelectionKey = None

        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance, point.x() + tolerance, point.y() + tolerance)

        found_feature = None
        category = ""

        layers_to_check = [
            ("qgisred_junctions", "Node"), ("qgisred_tanks", "Node"), ("qgisred_reservoirs", "Node"),
            ("qgisred_pipes", "Link"), ("qgisred_valves", "Link"), ("qgisred_pumps", "Link")
        ]

        for identifier, cat in layers_to_check:
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
            if len(self._timeSeriesMapSelectionItems()) > 1:
                if not self._confirmTimeSeriesClearSelection():
                    return
            self._timeSeriesResetMapSelection()
            self._clearTimeSeriesMapSelection()

        try:
            fid = found_feature.id()
        except Exception:
            fid = None
        element_id = str(found_feature.attribute("ID"))
        layer_identifier = layer.customProperty("qgisred_identifier") if layer else ""

        prop_internal = ""
        prop_display = ""
        is_stepped = False
        y_categorical_labels = None
        y_label_with_unit = ""
        try:
            dock = self.ResultDockwidget if (hasattr(self, 'ResultDockwidget') and self.ResultDockwidget) else None
        except Exception:
            dock = None

        is_right_click = False
        try:
            is_right_click = (mouse_button == Qt.MouseButton.RightButton)
        except Exception:
            is_right_click = False

        if category == "Node":
            if is_right_click:
                picked = self._timeSeriesPickMagnitudeFromMenu(category, dock)
                if not picked:
                    return
                prop_display = picked
            else:
                prop_display = dock.cbNodes.currentText() if dock else self.tr("Pressure")
            node_map = {dock.lbl_pressure: "Pressure", dock.lbl_head: "Head", dock.lbl_demand: "Demand", dock.lbl_quality: "Quality"} if dock else {}
            prop_internal = node_map.get(prop_display, "Pressure")
        else:
            if is_right_click:
                picked = self._timeSeriesPickMagnitudeFromMenu(category, dock)
                if not picked:
                    return
                prop_display = picked
            else:
                prop_display = dock.cbLinks.currentText() if dock else self.tr("Flow")
            link_map = {dock.lbl_flow: "Flow", dock.lbl_velocity: "Velocity", dock.lbl_headloss: "HeadLoss", dock.lbl_unit_headloss: "UnitHdLoss", dock.lbl_friction_factor: "FricFactor", dock.lbl_status: "Status", dock.lbl_reaction_rate: "ReactRate", dock.lbl_quality: "Quality", dock.lbl_signed_flow: "Flow", dock.lbl_unsigned_flow: "Flow"} if dock else {}
            prop_internal = link_map.get(prop_display, "Flow")
            if prop_internal == "Status":
                is_stepped = True
                y_categorical_labels = [self.tr("Closed"), self.tr("Active"), self.tr("Open")]

        unit_abbr = QGISRedFieldUtils().getUnitAbbreviation(normalize_element(category), prop_internal)
        if unit_abbr:
            y_label_with_unit = f"{prop_display} ({unit_abbr})"
        else:
            y_label_with_unit = prop_display

        palette = [
            QColor(0, 120, 215), QColor(220, 57, 18), QColor(16, 150, 24),
            QColor(153, 0, 153), QColor(0, 153, 198), QColor(255, 153, 0),
            QColor(60, 180, 75), QColor(145, 30, 180)
        ]
        existing_color = None
        for it in self.timeSeriesSelection:
            if (
                it.get("layer_identifier") == layer_identifier
                and it.get("element_id") == element_id
                and it.get("category") == category
                and it.get("prop_internal") == prop_internal
            ):
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
            "prop_internal": prop_internal,
            "prop_display": prop_display,
            "y_label_with_unit": y_label_with_unit,
            "is_stepped": bool(is_stepped),
            "y_categorical_labels": y_categorical_labels,
        }

        existing_idx = None
        for i, it in enumerate(self.timeSeriesSelection):
            if (
                it.get("layer_identifier") == layer_identifier
                and it.get("element_id") == element_id
                and it.get("category") == category
                and it.get("prop_internal") == prop_internal
            ):
                existing_idx = i
                break

        if is_shift and existing_idx is not None:
            try:
                self.timeSeriesSelection.pop(existing_idx)
            except Exception:
                pass
            if not self.timeSeriesSelection:
                self._timeSeriesResetSelection()
                self._clearTimeSeriesMapSelection()
                self._clearTimeSeriesHighlight()
                try:
                    self.timeSeriesDock.updatePlotSeries([], "", "", "")
                except Exception:
                    pass
                return

            try:
                remaining_ids = [
                    it.get("feature_id")
                    for it in self.timeSeriesSelection
                    if it.get("layer_identifier") == layer_identifier and it.get("feature_id") is not None
                ]
                if layer is not None:
                    layer.selectByIds(remaining_ids)
            except Exception:
                pass

            self._syncTimeSeriesHighlights(self.lastTimeSeriesLayer, self.lastTimeSeriesFeature)
            self._renderTimeSeriesSelection()
            return

        if existing_idx is None:
            self.timeSeriesSelection.append(sel_item)

        try:
            selected_ids = []
            for it in self.timeSeriesSelection:
                if it.get("layer_identifier") == layer_identifier and it.get("feature_id") is not None:
                    selected_ids.append(it.get("feature_id"))
            if layer and selected_ids:
                layer.selectByIds(selected_ids)
        except Exception:
            pass

        self.lastTimeSeriesFeature = found_feature
        self.lastTimeSeriesCategory = category
        self.lastTimeSeriesLayer = layer
        self._syncTimeSeriesHighlights(layer, found_feature)

        self._renderTimeSeriesSelection()

    def _renderTimeSeriesSelection(self, dock=None):
        dock = dock if dock is not None else self.activeTimeSeriesDock
        if dock is None:
            return
        if not dock.selection:
            return

        source = self._getTimeSeriesSource()
        if not source:
            self.pushMessage(self.tr("Results file not found. Please run the model."), level=1)
            return

        x_data = [t / 3600.0 for t in source["times"]]

        from ..ui.analysis.timeseries_globals import (
            get_global_timeseries,
            global_axis_group_label,
            global_variable_legend_label,
        )

        series = []
        for idx, it in enumerate(dock.selection):
            element_id = it.get("element_id")
            layer = it.get("layer")
            category = it.get("category") or ""
            prop_internal = it.get("prop_internal") or ""
            prop_display = it.get("prop_display") or ""
            y_label_with_unit = it.get("y_label_with_unit") or prop_display
            is_stepped = bool(it.get("is_stepped", False))
            y_categorical_labels = it.get("y_categorical_labels")
            layer_identifier = it.get("layer_identifier") or ""
            if category == "Global":
                y_data = get_global_timeseries(source, prop_internal)
                element_id = it.get("element_id") or prop_internal
            else:
                if not element_id:
                    continue
                y_data = self._getSeriesValuesForSource(source, category, element_id, prop_internal)
            if not y_data:
                continue

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

            label = f"{element_id}"
            legend_type = category
            if category == "Global":
                label = (
                    it.get("legend_label")
                    or it.get("y_label_with_unit")
                    or global_variable_legend_label(prop_internal)
                )
                legend_type = "global"
            elif layer:
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

            series_entry = {
                "x": x_data,
                "y": y_data,
                "label": (it.get("legend_label") or label),
                "color": it.get("color") if isinstance(it.get("color"), QColor) else QColor(0, 120, 215),
                "is_stepped": bool(is_stepped),
                "y_categorical_labels": y_categorical_labels,
                "legend_type": legend_type,
                "series_key": f"{category}:{layer_identifier}:{prop_internal}:{element_id}",
                "magnitude": (
                    global_axis_group_label()
                    if category == "Global"
                    else (y_label_with_unit or prop_display)
                ),
                "y_label_with_unit": y_label_with_unit,
                "line_style": it.get("line_style") or "solid",
                "line_width": it.get("line_width") or 2.0,
                "show_markers": bool(it.get("show_markers", False)),
                "marker_symbol": it.get("marker_symbol") or "circle",
                "marker_size": it.get("marker_size") or 6,
                "marker_color": it.get("marker_color") or it.get("color") or QColor(0, 120, 215),
                "marker_hollow": bool(it.get("marker_hollow", True)),
                "show_point_values": bool(it.get("show_point_values", False)),
                "visible": bool(it.get("visible", True)),
                "muted": bool(it.get("muted", False)),
                "highlighted": bool(it.get("highlighted", False)),
                "emphasis_mode": it.get("emphasis_mode") or "normal",
                "legend_font_family": it.get("legend_font_family") or "",
                "legend_font_size": it.get("legend_font_size") or 8,
            }
            display_decimals = it.get("y_display_decimals")
            if display_decimals is not None:
                series_entry["y_display_decimals"] = display_decimals
            series.append(series_entry)

        if not series:
            return

        translated_time = self.tr("Time")
        dock.updatePlotSeries(series, "", f"{translated_time} (h)", self.tr("Value"))

    def _onTimeSeriesSeriesReordered(self, order_keys, dock=None):
        try:
            if dock is None:
                dock = self._resolveTimeSeriesDock()
            if not order_keys or dock is None or not dock.selection:
                return
            key_to_item = {}
            for it in dock.selection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                cat = it.get("category") or ""
                prop = it.get("prop_internal") or ""
                key_to_item[f"{cat}:{li}:{prop}:{eid}"] = it
            new_sel = []
            for k in order_keys:
                if k in key_to_item:
                    new_sel.append(key_to_item[k])
            for it in dock.selection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                cat = it.get("category") or ""
                prop = it.get("prop_internal") or ""
                k = f"{cat}:{li}:{prop}:{eid}"
                if k not in order_keys:
                    new_sel.append(it)
            dock.selection = new_sel
            self._renderTimeSeriesSelection(dock)
            try:
                self._syncTimeSeriesHighlights(dock.lastLayer, dock.lastFeature, dock=dock)
            except Exception:
                pass
        except Exception:
            return

    def _onTimeSeriesCurveSettingsChanged(self, settings, dock=None):
        try:
            if dock is None:
                dock = self._resolveTimeSeriesDock()
            if not settings or dock is None or not dock.selection:
                return

            key_to_item = {}
            for it in dock.selection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                cat = it.get("category") or ""
                prop = it.get("prop_internal") or ""
                key_to_item[f"{cat}:{li}:{prop}:{eid}"] = it

            for cfg in settings or []:
                k = str((cfg or {}).get("series_key") or "")
                it = key_to_item.get(k)
                if it is None:
                    continue
                label = str((cfg or {}).get("label") or "").strip()
                if label:
                    it["legend_label"] = label
                color = (cfg or {}).get("color")
                qc = QColor(color)
                if qc.isValid():
                    it["color"] = qc
                it["line_style"] = (cfg or {}).get("line_style") or "solid"
                it["line_width"] = (cfg or {}).get("line_width") or 2.0
                it["show_markers"] = bool((cfg or {}).get("show_markers", False))
                it["marker_symbol"] = (cfg or {}).get("marker_symbol") or "circle"
                it["marker_size"] = (cfg or {}).get("marker_size") or 6
                marker_color = (cfg or {}).get("marker_color")
                marker_qc = QColor(marker_color)
                if marker_qc.isValid():
                    it["marker_color"] = marker_qc
                it["marker_hollow"] = bool((cfg or {}).get("marker_hollow", True))
                it["show_point_values"] = bool((cfg or {}).get("show_point_values", False))
                it["visible"] = bool((cfg or {}).get("visible", True))
                it["muted"] = bool((cfg or {}).get("muted", False))
                it["highlighted"] = bool((cfg or {}).get("highlighted", False))
                it["emphasis_mode"] = (cfg or {}).get("emphasis_mode") or "normal"
                it["legend_font_family"] = (cfg or {}).get("legend_font_family") or ""
                it["legend_font_size"] = (cfg or {}).get("legend_font_size") or 8
            try:
                self._syncTimeSeriesHighlights(dock.lastLayer, dock.lastFeature, dock=dock)
            except Exception:
                pass
        except Exception:
            return

    def _onTimeSeriesSeriesRemoved(self, series_key: str, dock=None):
        try:
            k = str(series_key or "").strip()
            if not k:
                return
            if dock is None:
                dock = self._resolveTimeSeriesDock()
            if dock is None or not dock.selection:
                return

            key_to_keep = []
            for it in dock.selection:
                li = it.get("layer_identifier") or ""
                eid = it.get("element_id") or ""
                cat = it.get("category") or ""
                prop = it.get("prop_internal") or ""
                it_key = f"{cat}:{li}:{prop}:{eid}"
                if it_key != k:
                    key_to_keep.append(it)

            if len(key_to_keep) == len(dock.selection):
                return

            dock.selection = key_to_keep

            if not dock.selection:
                self._timeSeriesResetSelection(dock)
                if dock is self.activeTimeSeriesDock:
                    self._clearTimeSeriesMapSelection()
                self._clearTimeSeriesHighlight(dock)
                try:
                    dock.updatePlotSeries([], "", "", "")
                except Exception:
                    pass
                return

            if dock is self.activeTimeSeriesDock:
                try:
                    fids_by_layer = {}
                    for it in dock.selection:
                        layer = it.get("layer")
                        fid = it.get("feature_id")
                        if layer is None or fid is None:
                            continue
                        fids_by_layer.setdefault(layer, []).append(fid)
                    for layer, fids in fids_by_layer.items():
                        try:
                            layer.selectByIds(fids)
                        except Exception:
                            pass
                except Exception:
                    pass

            try:
                self._syncTimeSeriesHighlights(dock.lastLayer, dock.lastFeature, dock=dock)
            except Exception:
                self._syncTimeSeriesHighlights(dock=dock)
            self._renderTimeSeriesSelection(dock)
        except Exception:
            return

    def performTimeSeriesPlotUpdate(self, found_feature, category, layer):
        if found_feature is None:
            return
        element_id = str(found_feature.attribute("ID"))

        prop_internal = ""
        prop_display = ""
        is_stepped = False

        if hasattr(self, 'ResultDockwidget') and self.ResultDockwidget:
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
                    self.ResultDockwidget.lbl_signed_flow: "Flow",
                    self.ResultDockwidget.lbl_unsigned_flow: "Flow",
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

        source = self._getTimeSeriesSource()
        if not source:
            self.pushMessage(self.tr("Results file not found. Please run the model."), level=1)
            return

        y_data = self._getSeriesValuesForSource(source, category, element_id, prop_internal)

        if not y_data:
            return

        x_data = [t / 3600.0 for t in source["times"]]

        element_label = f"{category} {element_id}"
        title = f"{element_label}: {prop_display}"

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
            y_categorical_labels = [self.tr("Closed"), self.tr("Active"), self.tr("Open")]
        else:
            unit_abbr = QGISRedFieldUtils().getUnitAbbreviation(normalize_element(category), prop_internal)
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
        """Refresh plotted curves after new results or a change in the results time mode.

        Refreshes every open chart window. Does not react to the node/link
        magnitude selector: each curve keeps the magnitude chosen when it was
        added on the map.
        """
        for dock in (getattr(self, "timeSeriesDocks", None) or []):
            if getattr(dock, "selection", None):
                self._renderTimeSeriesSelection(dock)

    def _timeSeriesConfigExportCurves(self, dock=None):
        """Build the serializable curve list from the current selection.

        ``dock.selection`` is the source of truth for which curves are
        plotted plus their per-curve styling; the explicit Y axis lives on the
        plotted series, so it is matched back in by ``series_key``.
        """
        dock = dock if dock is not None else self.activeTimeSeriesDock
        yaxis_by_key = {}
        try:
            for s in (dock.plot.series or []):
                key = str(s.get("series_key") or "")
                if key:
                    yaxis_by_key[key] = (s.get("y_axis") or "left")
        except Exception:
            pass

        def _hex(value, fallback="#0078d7"):
            if isinstance(value, QColor):
                return value.name()
            text = str(value or "").strip()
            return text or fallback

        curves = []
        for it in (getattr(dock, "selection", None) or []):
            category = it.get("category") or ""
            layer_identifier = it.get("layer_identifier") or ""
            prop_internal = it.get("prop_internal") or ""
            element_id = it.get("element_id") or ""
            key = f"{category}:{layer_identifier}:{prop_internal}:{element_id}"
            color_hex = _hex(it.get("color"))
            curves.append({
                "category": category,
                "layer_identifier": layer_identifier,
                "element_id": element_id,
                "prop_internal": prop_internal,
                "prop_display": it.get("prop_display") or "",
                "y_label_with_unit": it.get("y_label_with_unit") or "",
                "is_stepped": bool(it.get("is_stepped", False)),
                "y_categorical_labels": it.get("y_categorical_labels"),
                "y_display_decimals": it.get("y_display_decimals"),
                "y_axis": yaxis_by_key.get(key, ""),
                "label": it.get("legend_label") or "",
                "color": color_hex,
                "line_style": it.get("line_style") or "solid",
                "line_width": float(it.get("line_width") or 2.0),
                "show_markers": bool(it.get("show_markers", False)),
                "marker_symbol": it.get("marker_symbol") or "circle",
                "marker_size": int(it.get("marker_size") or 6),
                "marker_color": _hex(it.get("marker_color"), color_hex),
                "marker_hollow": bool(it.get("marker_hollow", True)),
                "show_point_values": bool(it.get("show_point_values", False)),
                "visible": bool(it.get("visible", True)),
                "muted": bool(it.get("muted", False)),
                "highlighted": bool(it.get("highlighted", False)),
                "emphasis_mode": it.get("emphasis_mode") or "normal",
                "legend_font_family": it.get("legend_font_family") or "",
                "legend_font_size": int(it.get("legend_font_size") or 8),
            })
        return curves

    def _onTimeSeriesExportConfig(self, path, dock=None):
        from ..ui.analysis.timeseries_config_io import write_timeseries_config

        if dock is None:
            dock = self._resolveTimeSeriesDock()
        if dock is None or not path:
            return
        if not getattr(dock, "selection", None):
            self.pushMessage(self.tr("No curves to export"), level=1)
            return
        try:
            plot = dock.plot
            write_timeseries_config(
                path,
                self._timeSeriesConfigExportCurves(dock),
                plot._axis_cfg_x,
                plot._axis_cfg_y_left,
                plot._axis_cfg_y_right,
                plot._general_cfg,
            )
        except Exception:
            self.pushMessage(self.tr("The chart configuration could not be exported."), level=2)
            return
        self.pushMessage(self.tr("Chart configuration exported."), level=3)

    def _timeSeriesSelectionFromConfig(self, curves):
        """Rebuild ``timeSeriesSelection`` items from parsed curve dicts.

        Layers and features are resolved once per layer identifier so a config
        with many curves on the same layer stays O(features) rather than
        O(curves * features). Missing layers/features are tolerated (the data is
        read from the results file by element id, not from the layer).
        """
        needed_ids = {}
        for curve in curves:
            identifier = curve.get("layer_identifier") or ""
            if not identifier or identifier == "global":
                continue
            needed_ids.setdefault(identifier, set()).add(str(curve.get("element_id") or ""))

        layer_by_identifier = {}
        feature_by_identifier = {}
        if needed_ids:
            try:
                layers = QGISRedLayerUtils().getLayers()
            except Exception:
                layers = []
            for identifier, ids in needed_ids.items():
                layer = None
                for l in layers:
                    try:
                        if l.customProperty("qgisred_identifier") == identifier:
                            layer = l
                            break
                    except Exception:
                        continue
                layer_by_identifier[identifier] = layer
                feat_map = {}
                if layer is not None:
                    try:
                        for feat in layer.getFeatures():
                            fid_attr = str(feat.attribute("ID"))
                            if fid_attr in ids:
                                feat_map[fid_attr] = feat
                                if len(feat_map) == len(ids):
                                    break
                    except Exception:
                        pass
                feature_by_identifier[identifier] = feat_map

        selection = []
        for curve in curves:
            identifier = curve.get("layer_identifier") or ""
            element_id = str(curve.get("element_id") or "")
            category = curve.get("category") or ""
            is_global = (category == "Global") or (identifier == "global")

            layer = None
            feature = None
            feature_id = None
            if not is_global:
                layer = layer_by_identifier.get(identifier)
                feature = feature_by_identifier.get(identifier, {}).get(element_id)
                if feature is not None:
                    try:
                        feature_id = feature.id()
                    except Exception:
                        feature_id = None

            color = QColor(curve.get("color"))
            if not color.isValid():
                color = QColor(0, 120, 215)
            marker_color = QColor(curve.get("marker_color"))
            if not marker_color.isValid():
                marker_color = color

            item = {
                "layer": layer,
                "layer_identifier": identifier,
                "feature": feature,
                "feature_id": feature_id,
                "category": category,
                "element_id": element_id,
                "color": color,
                "prop_internal": curve.get("prop_internal") or "",
                "prop_display": curve.get("prop_display") or "",
                "y_label_with_unit": curve.get("y_label_with_unit") or "",
                "is_stepped": bool(curve.get("is_stepped", False)),
                "y_categorical_labels": curve.get("y_categorical_labels"),
                "legend_label": curve.get("label") or "",
                "line_style": curve.get("line_style") or "solid",
                "line_width": float(curve.get("line_width") or 2.0),
                "show_markers": bool(curve.get("show_markers", False)),
                "marker_symbol": curve.get("marker_symbol") or "circle",
                "marker_size": int(curve.get("marker_size") or 6),
                "marker_color": marker_color,
                "marker_hollow": bool(curve.get("marker_hollow", True)),
                "show_point_values": bool(curve.get("show_point_values", False)),
                "visible": bool(curve.get("visible", True)),
                "muted": bool(curve.get("muted", False)),
                "highlighted": bool(curve.get("highlighted", False)),
                "emphasis_mode": curve.get("emphasis_mode") or "normal",
                "legend_font_family": curve.get("legend_font_family") or "",
                "legend_font_size": int(curve.get("legend_font_size") or 8),
                "y_axis": (curve.get("y_axis") or "").strip().lower(),
            }
            decimals = curve.get("y_display_decimals")
            if decimals is not None:
                item["y_display_decimals"] = decimals
            selection.append(item)
        return selection

    def _onTimeSeriesImportConfig(self, path, dock=None):
        from ..ui.analysis.timeseries_config_io import read_timeseries_config

        if dock is None:
            dock = self._resolveTimeSeriesDock()
        if dock is None:
            return
        if not path or not os.path.isfile(path):
            self.pushMessage(self.tr("Configuration file not found."), level=1)
            return
        try:
            config = read_timeseries_config(path)
        except Exception:
            self.pushMessage(self.tr("The chart configuration could not be read."), level=2)
            return

        curves = config.get("curves") or []
        selection = self._timeSeriesSelectionFromConfig(curves)

        if dock is self.activeTimeSeriesDock:
            self._clearTimeSeriesMapSelection()
        self._clearTimeSeriesHighlight(dock)
        dock.selection = selection
        dock.selectionKey = None

        plot = dock.plot
        plot._axis_cfg_x = config.get("axis_x")
        plot._axis_cfg_y_left = config.get("axis_y_left")
        plot._axis_cfg_y_right = config.get("axis_y_right")
        plot._general_cfg = config.get("general")

        if selection:
            if dock is self.activeTimeSeriesDock:
                try:
                    fids_by_layer = {}
                    for it in selection:
                        layer = it.get("layer")
                        fid = it.get("feature_id")
                        if layer is None or fid is None:
                            continue
                        fids_by_layer.setdefault(layer, []).append(fid)
                    for layer, fids in fids_by_layer.items():
                        layer.selectByIds(fids)
                except Exception:
                    pass
            try:
                self._syncTimeSeriesHighlights(dock=dock)
            except Exception:
                pass
            self._renderTimeSeriesSelection(dock)
            self._timeSeriesRestoreExplicitYAxis(plot, selection)
        else:
            try:
                dock.updatePlotSeries([], "", "", "")
            except Exception:
                pass

        try:
            plot._updateMinimumWidthForTitle()
        except Exception:
            pass
        try:
            plot.update()
        except Exception:
            pass
        try:
            dock._updateClearToolbarVisibility()
            dock._updatePanAvailability()
        except Exception:
            pass

        self.pushMessage(self.tr("Chart configuration imported."), level=3)

    def _timeSeriesRestoreExplicitYAxis(self, plot, selection):
        """Re-apply each curve's saved Y axis after the auto-by-magnitude pass."""
        yaxis_by_key = {}
        for it in selection:
            axis = (it.get("y_axis") or "").strip().lower()
            if axis in ("left", "right"):
                key = (
                    f"{it.get('category') or ''}:{it.get('layer_identifier') or ''}:"
                    f"{it.get('prop_internal') or ''}:{it.get('element_id') or ''}"
                )
                yaxis_by_key[key] = axis
        if not yaxis_by_key:
            return
        changed = False
        for s in (plot.series or []):
            key = str(s.get("series_key") or "")
            if key in yaxis_by_key:
                s["y_axis"] = yaxis_by_key[key]
                changed = True
        if changed:
            try:
                plot._assignYAxisByMagnitude()
            except Exception:
                pass
