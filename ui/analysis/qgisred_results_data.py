# -*- coding: utf-8 -*-
import os

from qgis.core import NULL
from qgis.PyQt.QtCore import QCoreApplication
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils

# Average flow is split into Flow_Unsig and Flow_Sig; both use Flow's decimal setting.
_STAT_VAR_ALIASES = {
    "Flow_Unsig": "Flow",
    "Flow_Sig":   "Flow",
}

# Display names for Average-stat-specific link fields (used when reloading project metadata).
_RESULT_FIELD_DISPLAY_NAMES = {
    "Flow_Sig":   "Flow (Signed)",
    "Flow_Unsig": "Flow (Unsigned)",
}

# All result field names that may appear in Node/Link result layers.
_NODE_RESULT_FIELD_NAMES = [
    "Time", "Pressure", "Head", "Demand", "FullDem", "DemDeficit",
    "Leaks", "EmittFlow", "Quality", "Statistics", "Time_H", "Time_D", "Time_Q",
]
_LINK_RESULT_FIELD_NAMES = [
    "Time", "Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss",
    "FricFactor", "Energy", "ReactRate", "Quality", "Statistics",
    "Time_H", "Time_Q", "Flow_Sig", "Flow_Unsig",
]


def _compute_result_visible_fields(layer_type, stat_en, quality_simulated):
    """Return the set of result field names that should be visible.

    ``stat_en`` is an English key: 'NONE', 'MAXIMUM', 'MINIMUM', 'AVERAGE',
    'RANGE', 'STDDEV'.  Pass 'NONE' (or '') for normal time-step mode.
    """
    visible = set()
    stat_up = (stat_en or "NONE").strip().upper()
    is_stats = stat_up != "NONE"

    if not is_stats:
        visible.add("Time")
        if layer_type == "Node":
            visible.update(["Pressure", "Head", "Demand"])
            if quality_simulated:
                visible.add("Quality")
        else:
            visible.update(["Status", "Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor"])
            if quality_simulated:
                visible.update(["ReactRate", "Quality"])
    else:
        visible.add("Statistics")
        if layer_type == "Node":
            visible.update(["Pressure", "Head", "Demand"])
            if quality_simulated:
                visible.add("Quality")
            if stat_up in ("MAXIMUM", "MINIMUM"):
                visible.update(["Time_H", "Time_D"])
                if quality_simulated:
                    visible.add("Time_Q")
        else:
            visible.update(["Flow", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor"])
            if quality_simulated:
                visible.update(["ReactRate", "Quality"])
            if stat_up == "AVERAGE":
                visible.discard("Flow")
                visible.update(["Flow_Unsig", "Flow_Sig"])
            if stat_up in ("MAXIMUM", "MINIMUM"):
                visible.add("Time_H")
                if quality_simulated:
                    visible.add("Time_Q")
    return visible


def infer_stat_en_from_layer(layer):
    """Read the Statistics field from the first feature and return the English key.

    The Statistics field is written with the UI's translated label (e.g. 'Promedio'
    for Spanish). We re-translate the known English labels at runtime to match.
    Returns 'NONE' if the field is absent or empty.
    """
    stat_idx = layer.fields().indexOf("Statistics")
    if stat_idx < 0:
        return "NONE"
    feat = next(layer.getFeatures(), None)
    if feat is None:
        return "NONE"
    val = str(feat.attribute(stat_idx) or "").strip()
    if not val:
        return "NONE"
    val_upper = val.upper()
    for en_label, en_key in [
        ("Maximum", "MAXIMUM"), ("Minimum", "MINIMUM"),
        ("Average", "AVERAGE"), ("Range", "RANGE"), ("StdDev", "STDDEV"),
    ]:
        tr = QCoreApplication.translate("QGISRedResultsDock", en_label)
        if val_upper == tr.upper():
            return en_key
    # Last resort: direct uppercase match (English UI)
    return val_upper if val_upper in ("MAXIMUM", "MINIMUM", "AVERAGE", "RANGE", "STDDEV") else "MAXIMUM"


def apply_result_column_visibility(layer, layer_type, stat_en, quality_simulated):
    """Apply attribute table column visibility for a result layer.

    Callable without the results dock.  ``layer_type`` is 'Node' or 'Link'.
    ``stat_en`` is an English key (see ``_compute_result_visible_fields``).
    """
    from ...compat import ATCOL_TYPE_FIELD

    all_result_upper = {n[:10].upper() for n in _NODE_RESULT_FIELD_NAMES + _LINK_RESULT_FIELD_NAMES}
    visible = _compute_result_visible_fields(layer_type, stat_en, quality_simulated)
    visible_upper = {v[:10].upper() for v in visible}

    config = layer.attributeTableConfig()
    config.update(layer.fields())
    columns = config.columns()
    for i in range(len(columns)):
        col = columns[i]
        col_upper = col.name.upper()
        if col_upper in all_result_upper:
            columns[i].hidden = col_upper not in visible_upper
            columns[i].type = ATCOL_TYPE_FIELD
    config.setColumns(columns)
    layer.setAttributeTableConfig(config)

from .qgisred_results_binary import (
    getOut_TimeNodesProperties, getOut_TimeLinksProperties,
    getOut_StatNodesProperties, getOut_StatLinksProperties,
    getOut_Metadata,
)
from .qgisred_results_hyd import (
    getHyd_TimeNodesProperties,
    getHyd_TimeLinksProperties,
    getHyd_StatNodesProperties,
    getHyd_StatLinksProperties,
    getHyd_Metadata,
)


def seconds_to_time_str(seconds):
    """Convert seconds to 'Nd h:MM[:SS]' format; omits :SS when seconds == 0."""
    d = seconds // 86400
    rem = seconds % 86400
    h = rem // 3600
    m = (rem % 3600) // 60
    s = rem % 60
    time_part = f"{h}:{m:02d}" if s == 0 else f"{h}:{m:02d}:{s:02d}"
    if d == 0:
        return time_part
    return f"{d}d {time_part}"


def seconds_to_time_str_no_seconds(seconds):
    h = seconds // 3600
    rem = seconds % 3600
    m = (rem % 3600) // 60
    return f"{h}:{m:02d}"


def seconds_to_csv_time_str(seconds):
    """Convert seconds to 'h:MM:SS' format without days (total hours), for CSV export."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"


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

    lbl_singlePeriod = QCoreApplication.translate("QGISRedResultsDock", "Single Period")

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
        time_str = seconds_to_csv_time_str(time_secs) if num_periods > 1 else lbl_singlePeriod

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
        QCoreApplication.translate("QGISRedResultsDock", "Results exported to CSV"),
        level=3, duration=5
    )


class _ResultsDataMixin:
    """Mixin for QGISRedResultsDock: loading and populating result data from the .out binary file."""

    def _isAllCalculationTimesMode(self):
        return hasattr(self, "cbResultTimes") and self.cbResultTimes.currentIndex() == 1

    def _getOutResultsPath(self):
        return os.path.join(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + ".out")

    def _getHydResultsPath(self):
        return os.path.join(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + ".hyd")

    def _getHydMetaIfUsable(self):
        out_path = self._getOutResultsPath()
        hyd_path = self._getHydResultsPath()
        if not (os.path.exists(out_path) and os.path.exists(hyd_path)):
            return None
        hyd_meta = getHyd_Metadata(hyd_path, out_path)
        if hyd_meta is None:
            return None
        # Treat .hyd as usable only when it really provides temporal detail.
        if hyd_meta.get("hyd_num_periods", 0) <= 1:
            return None
        return hyd_meta

    def _elapsedTextToSeconds(self, elapsed_text):
        if elapsed_text == self.lbl_singlePeriod:
            return 0
        try:
            if "d" in elapsed_text:
                parts = elapsed_text.split(" ")
                days = int(parts[0].replace("d", ""))
                hms = parts[1].split(":")
                if len(hms) == 2:
                    return days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60
                return days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
            hms = elapsed_text.split(":")
            if len(hms) == 2:
                return int(hms[0]) * 3600 + int(hms[1]) * 60
            return int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
        except Exception:
            return 0

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

    def _readTimeLabelsFromOut(self, all_calc=None):
        """Read time labels from selected results backend (.out or .hyd).

        all_calc: True → force .hyd, False → force .out, None → use current cbResultTimes state.
        """
        try:
            out_path = self._getOutResultsPath()
            use_all = self._isAllCalculationTimesMode() if all_calc is None else all_calc
            if use_all:
                hyd_meta = self._getHydMetaIfUsable()
                if hyd_meta is not None:
                    n = hyd_meta["hyd_num_periods"]
                    times = hyd_meta.get("hyd_times") or []
                    if times:
                        return ";".join(seconds_to_time_str(t) for t in times)
                    start = hyd_meta["hyd_report_start"]
                    step = hyd_meta["hyd_report_step"]
                    return ";".join(seconds_to_time_str(start + i * step) for i in range(n))

            with open(out_path, "rb") as f:
                meta = getOut_Metadata(f)
            if meta is None:
                return self.lbl_singlePeriod
            n = meta["num_periods"]
            if n <= 1:
                return self.lbl_singlePeriod
            start = meta["report_start"]
            step = meta["report_step"]
            labels = []
            for i in range(n):
                labels.append(seconds_to_time_str(start + i * step))
            return ";".join(labels)
        except Exception:
            return self.lbl_singlePeriod

    def loadReportFile(self):
        rpt_path = os.path.join(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + ".rpt")
        if os.path.exists(rpt_path):
            with open(rpt_path, "r", errors="replace") as f:
                self.textEditReport.setPlainText(f.read())

    def completeResultLayers(self):
        """Populates result layers from selected backend (.out/.hyd)."""
        if not self.isCurrentProject():
            return

        idx = self.cbTimes.currentIndex()
        elapsed_text = (
            self.TimeLabels[idx]
            if 0 <= idx < len(self.TimeLabels)
            else self.cbTimes.currentText()
        )
        # Derive display text from current mode (civil / continuous / elapsed)
        if getattr(self, 'civilMode', False) and getattr(self, '_civilLabels', []):
            time_text = (
                self._civilLabels[idx]
                if 0 <= idx < len(self._civilLabels)
                else elapsed_text
            )
        elif getattr(self, 'continuousHoursMode', False):
            time_text = self._toContinuousHours(elapsed_text)
        else:
            time_text = elapsed_text
        time_seconds = self._elapsedTextToSeconds(elapsed_text)
        out_path = self._getOutResultsPath()
        hyd_path = self._getHydResultsPath()
        use_hyd = self._isAllCalculationTimesMode() and (self._getHydMetaIfUsable() is not None)

        if use_hyd:
            backend_nodes = lambda t: getHyd_TimeNodesProperties(hyd_path, out_path, t)
            backend_links = lambda t: getHyd_TimeLinksProperties(hyd_path, out_path, t)
        else:
            backend_nodes = lambda t: getOut_TimeNodesProperties(out_path, t)
            backend_links = lambda t: getOut_TimeLinksProperties(out_path, t)

        if not os.path.exists(out_path):
            return

        field_utils = QGISRedFieldUtils()
        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue

            # Fetch results from binary file
            if layerName == "Node":
                results = backend_nodes(time_seconds)
                if use_hyd and not results:
                    results = getOut_TimeNodesProperties(out_path, time_seconds)
            else:
                results = backend_links(time_seconds)
                if use_hyd and not results:
                    results = getOut_TimeLinksProperties(out_path, time_seconds)

            if not results:
                continue

            first_id = next(iter(results))
            variables = list(results[first_id].keys())
            field_indices = self._buildFieldIndexMap(target_layer, variables)
            time_field_idx = target_layer.fields().indexOf("Time")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                id_field_idx = 0  # fallback to first field

            element = "Nodes" if layerName == "Node" else "Links"
            user_dec = (
                getattr(self, '_labelNodeDecimals', None) if layerName == "Node"
                else getattr(self, '_labelLinkDecimals', None)
            )
            attribute_updates = {}
            for feature in target_layer.getFeatures():
                feature_id = str(feature.attributes()[id_field_idx])
                if feature_id in results:
                    updates = {}
                    if time_field_idx != -1:
                        updates[time_field_idx] = time_text
                    for var, val in results[feature_id].items():
                        var_key = var[:10]
                        if val is not None and isinstance(val, (int, float)):
                            dec = user_dec if user_dec is not None else field_utils.getDecimals(element, var_key)
                            val = round(float(val), dec)
                        updates[field_indices[var_key]] = val
                    attribute_updates[feature.id()] = updates

            self._applyAttributeUpdates(target_layer, attribute_updates)

            # Apply visibility AFTER populating
            self.updateFieldsVisibility(target_layer, layerName, stats_mode=False)

    def _updateTimeFieldInLayers(self):
        """Rewrites only the 'Time' field in result layers to match the current display format."""
        if self._statsMode:
            return
        idx = self.cbTimes.currentIndex()
        elapsed_text = (
            self.TimeLabels[idx]
            if 0 <= idx < len(self.TimeLabels)
            else ""
        )
        if not elapsed_text:
            return
        if getattr(self, 'civilMode', False) and getattr(self, '_civilLabels', []):
            time_text = (
                self._civilLabels[idx]
                if 0 <= idx < len(self._civilLabels)
                else elapsed_text
            )
        elif getattr(self, 'continuousHoursMode', False):
            time_text = self._toContinuousHours(elapsed_text)
        else:
            time_text = elapsed_text

        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue
            time_field_idx = target_layer.fields().indexOf("Time")
            if time_field_idx == -1:
                continue
            attribute_updates = {
                feature.id(): {time_field_idx: time_text}
                for feature in target_layer.getFeatures()
            }
            self._applyAttributeUpdates(target_layer, attribute_updates)

    def completeStatsLayers(self):
        """Populates the attribute tables of result layers with statistics from the selected backend.
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
        out_path = self._getOutResultsPath()
        hyd_path = self._getHydResultsPath()
        use_hyd = self._isAllCalculationTimesMode() and (self._getHydMetaIfUsable() is not None)
        if not os.path.exists(out_path):
            return

        # For Min/Max: which variable provides the time-of-occurrence for each node/link field.
        #   Node: Pressure and Head share Time_H; Demand → Time_D; Quality → Time_Q
        #   Link: Flow, Velocity, HeadLoss, UnitHdLoss share Time_H; Quality → Time_Q
        _TIME_PROVIDER = {
            "Node": {"Pressure": "Time_H", "Demand": "Time_D", "Quality": "Time_Q"},
            "Link": {"Flow": "Time_H", "Quality": "Time_Q"},
        }

        field_utils = QGISRedFieldUtils()
        for layerName in ["Node", "Link"]:
            target_layer = self._findResultLayer(layerName)
            if not target_layer:
                continue

            if use_hyd and layerName == "Node":
                results = getHyd_StatNodesProperties(hyd_path, out_path, stat)
            elif use_hyd and layerName == "Link":
                results = getHyd_StatLinksProperties(hyd_path, out_path, stat)
            elif layerName == "Node":
                results = getOut_StatNodesProperties(out_path, stat)
            else:
                results = getOut_StatLinksProperties(out_path, stat)

            if use_hyd and not results:
                if layerName == "Node":
                    results = getOut_StatNodesProperties(out_path, stat)
                else:
                    results = getOut_StatLinksProperties(out_path, stat)

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

            element = "Nodes" if layerName == "Node" else "Links"
            user_dec = (
                getattr(self, '_labelNodeDecimals', None) if layerName == "Node"
                else getattr(self, '_labelLinkDecimals', None)
            )
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
                        raw_val = val["Value"] if val is not None else None
                        if raw_val is not None and isinstance(raw_val, (int, float)):
                            csv_field = _STAT_VAR_ALIASES.get(var, var)[:10]
                            dec = user_dec if user_dec is not None else field_utils.getDecimals(element, csv_field)
                            raw_val = round(float(raw_val), dec)
                        updates[field_indices[var_key]] = raw_val
                        if is_min_max and var_key in time_field_indices and time_field_indices[var_key] != -1:
                            t = val["Time"] if val is not None else None
                            updates[time_field_indices[var_key]] = seconds_to_time_str(t) if t is not None else None
                attribute_updates[feature.id()] = updates

            self._applyAttributeUpdates(target_layer, attribute_updates)

            # Apply visibility AFTER populating
            self.updateFieldsVisibility(target_layer, layerName, stats_mode=True, stat=stat_label)

