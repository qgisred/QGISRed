# -*- coding: utf-8 -*-
import os

from qgis.core import NULL
from qgis.PyQt.QtCore import QCoreApplication
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils

from .qgisred_results_binary import (
    getOut_TimeNodesProperties, getOut_TimeLinksProperties,
    getOut_StatNodesProperties, getOut_StatLinksProperties,
    getOut_Metadata,
)


def seconds_to_time_str(seconds):
    """Convert seconds to 'NNd HH:MM:SS' format."""
    d = seconds // 86400
    rem = seconds % 86400
    h = rem // 3600
    m = (rem % 3600) // 60
    s = rem % 60
    return f"{d:02d}d {h:02d}:{m:02d}:{s:02d}"


def get_regional_separators():
    """Return (list_separator, decimal_separator) from Windows regional settings, with fallback."""
    list_sep = ","
    decimal_sep = "."
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\International")
        list_sep = winreg.QueryValueEx(key, "sList")[0] or list_sep
        decimal_sep = winreg.QueryValueEx(key, "sDecimal")[0] or decimal_sep
        winreg.CloseKey(key)
    except Exception:
        import locale
        decimal_sep = locale.localeconv().get("decimal_point", ".") or "."
    return list_sep, decimal_sep


def export_results_to_csv(binary_path, nodes_path, links_path, iface, list_sep, decimal_sep):
    """Export all simulation time steps to two CSV files (Nodes and Links)."""
    import csv

    lbl_permanent = QCoreApplication.translate("QGISRedResultsDock", "Permanent")

    def _fmt(value):
        if value is None or value == "":
            return ""
        if isinstance(value, float):
            return str(value).replace(".", decimal_sep)
        return value

    if not os.path.exists(binary_path):
        return

    with open(binary_path, 'rb') as f:
        meta = getOut_Metadata(f, include_lengths=False)
    if not meta:
        return

    num_periods = meta["num_periods"]
    report_start = meta["report_start"]
    report_step = meta["report_step"]
    node_ids = meta["node_ids"]
    link_ids = meta["link_ids"]
    node_types = meta["node_types"]
    link_types = meta["link_types"]

    node_type_names = {0: "Junction", 1: "Reservoir", 2: "Tank"}
    link_type_names = {0: "Pipe", 1: "Pipe", 2: "Pump", 3: "Valve", 4: "Valve", 5: "Valve", 6: "Valve", 7: "Valve", 8: "Valve"}

    node_rows = []
    link_rows = []
    node_props_keys = None
    link_props_keys = None

    for i in range(max(num_periods, 1)):
        time_secs = report_start + i * report_step
        time_str = seconds_to_time_str(time_secs) if num_periods > 1 else lbl_permanent

        node_data = getOut_TimeNodesProperties(binary_path, time_secs)
        link_data = getOut_TimeLinksProperties(binary_path, time_secs)

        if node_props_keys is None and node_data:
            node_props_keys = list(next(iter(node_data.values())).keys())
        if link_props_keys is None and link_data:
            link_props_keys = list(next(iter(link_data.values())).keys())

        for j, nid in enumerate(node_ids):
            props = node_data.get(nid, {})
            row = [nid, node_type_names.get(node_types[j], ""), time_str]
            row += [_fmt(props.get(k)) for k in (node_props_keys or [])]
            node_rows.append(row)

        for j, lid in enumerate(link_ids):
            props = link_data.get(lid, {})
            row = [lid, link_type_names.get(link_types[j], ""), time_str]
            row += [_fmt(props.get(k)) for k in (link_props_keys or [])]
            link_rows.append(row)

    with open(nodes_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=list_sep)
        writer.writerow(["Id", "Type", "Time"] + (node_props_keys or []))
        writer.writerows(node_rows)

    with open(links_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=list_sep)
        writer.writerow(["Id", "Type", "Time"] + (link_props_keys or []))
        writer.writerows(link_rows)

    QGISRedUIUtils.showGlobalMessage(
        iface,
        "Results exported to CSV",
        level=3, duration=5
    )


class _ResultsDataMixin:
    """Mixin for QGISRedResultsDock: loading and populating result data from the .out binary file."""

    def _buildFieldIndexMap(self, layer, variables):
        """Return a dict mapping each variable name to its field index in the layer.
        Shapefile field names are capped at 10 characters."""
        return {var: layer.fields().indexOf(var[:10]) for var in variables}

    def _applyAttributeUpdates(self, layer, updates_dict):
        """Write a batch of attribute updates to the layer's data provider and trigger repaint."""
        if updates_dict:
            layer.dataProvider().changeAttributeValues(updates_dict)
            layer.dataProvider().dataChanged.emit()
            layer.triggerRepaint()

    def _readTimeLabelsFromOut(self):
        """Read time step labels from existing .out file (same format as GISRed.Compute returns)."""
        try:
            with open(self.outPath, 'rb') as f:
                meta = getOut_Metadata(f)
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

    def completeResultLayers(self):
        """Populates the attribute tables of the result layers with data from the .out file."""
        if not self.isCurrentProject():
            return

        # Parse time strings like "00d 01:23:45" to seconds
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

        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue

            # Fetch results from binary file
            if layerName == "Node":
                results = getOut_TimeNodesProperties(binary_path, time_seconds)
            else:
                results = getOut_TimeLinksProperties(binary_path, time_seconds)

            if not results:
                continue

            first_id = next(iter(results))
            variables = list(results[first_id].keys())
            field_indices = self._buildFieldIndexMap(target_layer, variables)
            time_field_idx = target_layer.fields().indexOf("Time")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                id_field_idx = 0  # fallback to first field

            attribute_updates = {}
            for feature in target_layer.getFeatures():
                feature_id = str(feature.attributes()[id_field_idx])
                if feature_id in results:
                    updates = {}
                    if time_field_idx != -1:
                        updates[time_field_idx] = time_text
                    for var, val in results[feature_id].items():
                        updates[field_indices[var[:10]]] = val
                    attribute_updates[feature.id()] = updates

            self._applyAttributeUpdates(target_layer, attribute_updates)

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

        # For Min/Max: which variable provides the time-of-occurrence for each node/link field.
        #   Node: Pressure and Head share Time_H; Demand → Time_D; Quality → Time_Q
        #   Link: Flow, Velocity, HeadLoss, UnitHdLoss share Time_H; Quality → Time_Q
        _TIME_PROVIDER = {
            "Node": {"Pressure": "Time_H", "Demand": "Time_D", "Quality": "Time_Q"},
            "Link": {"Flow": "Time_H", "Quality": "Time_Q"},
        }

        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue

            if layerName == "Node":
                results = getOut_StatNodesProperties(binary_path, stat)
            else:
                results = getOut_StatLinksProperties(binary_path, stat)

            if not results:
                continue

            first_id = next(iter(results))
            variables = list(results[first_id].keys())
            field_indices = self._buildFieldIndexMap(target_layer, variables)

            time_field_provider = _TIME_PROVIDER.get(layerName, {})
            time_field_indices = {}
            if is_min_max:
                for provider_variable, time_col_name in time_field_provider.items():
                    time_field_indices[provider_variable] = target_layer.fields().indexOf(time_col_name)

            stat_field_idx = target_layer.fields().indexOf("Statistics")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                id_field_idx = 0

            attribute_updates = {}
            for feature in target_layer.getFeatures():
                feature_id = str(feature.attributes()[id_field_idx])
                if feature_id not in results:
                    continue
                updates = {}
                if stat_field_idx != -1:
                    updates[stat_field_idx] = stat_label
                for var, val in results[feature_id].items():
                    var_key = var[:10]
                    if var_key in field_indices and field_indices[var_key] != -1:
                        updates[field_indices[var_key]] = val["Value"] if val is not None else None
                        if is_min_max and var_key in time_field_indices and time_field_indices[var_key] != -1:
                            t = val["Time"] if val is not None else None
                            updates[time_field_indices[var_key]] = seconds_to_time_str(t) if t is not None else None
                attribute_updates[feature.id()] = updates

            self._applyAttributeUpdates(target_layer, attribute_updates)

            # Apply visibility AFTER populating
            self.updateFieldsVisibility(target_layer, layerName, stats_mode=True, stat=stat_label)

