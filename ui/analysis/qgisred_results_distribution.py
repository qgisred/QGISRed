# -*- coding: utf-8 -*-
"""Distribution histogram helpers and dock mixin for simulation results."""
from __future__ import annotations

import re
from bisect import bisect_right

from qgis.PyQt.QtCore import QCoreApplication, QSize, Qt
from qgis.PyQt.QtGui import QColor, QIcon
from qgis.PyQt.QtWidgets import QHBoxLayout, QToolButton, QVBoxLayout, QWidget
from qgis.core import (
    NULL,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer,
)

from ...tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from .qgisred_node_demand_utils import junction_positive_node_demand
from .results_distribution_widget import ResultsDistributionWidget

# Head loss magnitudes apply to pipes only (pumps/valves lack UnitHdLoss in .out).
_PIPE_ONLY_LINK_FIELDS = frozenset({"HeadLoss", "UnitHdLoss"})


def _format_edge(value):
    if value is None:
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number == 0:
        return "0.00"
    magnitude = abs(number)
    if magnitude >= 1000 or magnitude < 0.01:
        return "{:.4g}".format(number)
    return "{:.2f}".format(number)


def _format_range_label(lower, upper):
    return "{} - {}".format(_format_edge(lower), _format_edge(upper))


def _make_bin(label, lower=None, upper=None, category=None, color=None, mid=None):
    return {
        "label": label,
        "lo": lower,
        "hi": upper,
        "mid": mid,
        "category": category,
        "color": color,
        "count": 0,
        "sum": 0.0,
        "avg": 0.0,
    }


def _finalize_bin(bin_data):
    count = bin_data["count"]
    if count > 0:
        bin_data["avg"] = bin_data["sum"] / count
    if bin_data.get("mid") is None:
        lower = bin_data.get("lo")
        upper = bin_data.get("hi")
        if lower is not None and upper is not None:
            bin_data["mid"] = (float(lower) + float(upper)) / 2.0


def _rule_based_as_graduated(renderer):
    if not isinstance(renderer, QgsRuleBasedRenderer):
        return None
    rules = [rule for rule in renderer.rootRule().children() if _NULL_RULE_LABEL not in rule.label()]
    if not rules:
        return None
    match = re.match(r'\((.+?)\)\s*>=', rules[0].filterExpression())
    if not match:
        return None
    class_attr = match.group(1)
    ranges = []
    for rule in rules:
        numbers = re.findall(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', rule.filterExpression())
        if len(numbers) >= 2:
            lower = float(numbers[0])
            upper = float(numbers[1])
            ranges.append({
                "label": rule.label(),
                "lo": lower,
                "hi": upper,
                "color": rule.symbol().color(),
                "category": None,
            })
    if not ranges:
        return None
    return class_attr, ranges


def _parse_category_from_filter(expression, field_name):
    if not expression:
        return None
    pattern = r'"' + re.escape(field_name) + r'"\s*=\s*\'([^\']*)\''
    match = re.search(pattern, expression)
    if match:
        return match.group(1)
    return None


def extract_legend_classes(layer, field_name):
    if layer is None or not field_name:
        return [], None

    renderer = layer.renderer()
    classes = []

    if isinstance(renderer, QgsGraduatedSymbolRenderer):
        for range_item in renderer.ranges():
            label = (range_item.label() or "").strip()
            if not label:
                label = _format_range_label(range_item.lowerValue(), range_item.upperValue())
            classes.append(_make_bin(
                label,
                range_item.lowerValue(),
                range_item.upperValue(),
                color=range_item.symbol().color(),
            ))
        return classes, "numeric"

    if isinstance(renderer, QgsRuleBasedRenderer):
        graduated = _rule_based_as_graduated(renderer)
        if graduated:
            for class_data in graduated[1]:
                classes.append(_make_bin(
                    class_data["label"],
                    class_data["lo"],
                    class_data["hi"],
                    color=class_data["color"],
                ))
            return classes, "numeric"

        for rule in renderer.rootRule().children():
            if _NULL_RULE_LABEL in rule.label():
                continue
            category = _parse_category_from_filter(rule.filterExpression(), field_name)
            classes.append(_make_bin(
                rule.label(),
                category=category if category is not None else rule.label(),
                color=rule.symbol().color(),
            ))
        if classes:
            return classes, "categorical"
        return [], None

    if isinstance(renderer, QgsCategorizedSymbolRenderer):
        for category in renderer.categories():
            label = (category.label() or "").strip()
            if not label:
                label = str(category.value())
            classes.append(_make_bin(
                label,
                category=category.value(),
                color=category.symbol().color(),
            ))
        return classes, "categorical"

    return [], None


def _layer_identifier(layer):
    if layer is None:
        return None
    return layer.customProperty("qgisred_identifier") or None


def _include_feature_for_distribution(feature, field_name, layer_identifier=None):
    """Exclude non-pipe links for head-loss magnitudes and non-junction Demand values."""
    if field_name == "Demand":
        return junction_positive_node_demand(feature, layer_identifier) is not None
    if field_name not in _PIPE_ONLY_LINK_FIELDS:
        return True
    field_names = feature.fields().names()
    if "UnitHdLoss" not in field_names:
        return True
    unit_headloss = feature["UnitHdLoss"]
    return unit_headloss is not None and unit_headloss != NULL


def _feature_value_for_classification(feature, field_name, layer_identifier=None):
    if field_name == "Demand":
        return junction_positive_node_demand(feature, layer_identifier)
    if field_name not in feature.fields().names():
        return None
    raw = feature[field_name]
    if raw is None or raw == NULL:
        return None
    if field_name == "Flow":
        try:
            return abs(float(raw))
        except (TypeError, ValueError):
            return None
    if field_name == "Status":
        return str(raw)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return str(raw)


def _find_class_index(classes, mode, value):
    if mode == "categorical":
        string_value = str(value)
        for index, class_data in enumerate(classes):
            category = class_data.get("category")
            if category is not None and str(category) == string_value:
                return index
        return None

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    for index, class_data in enumerate(classes):
        lower_edge = class_data["lo"]
        upper_edge = class_data["hi"]
        if lower_edge is None or upper_edge is None:
            continue
        if index == len(classes) - 1:
            if lower_edge <= numeric_value <= upper_edge:
                return index
        elif lower_edge <= numeric_value < upper_edge:
            return index
    return None


def build_distribution_bins(layer, field_name):
    if layer is None or not field_name:
        return [], ""

    if field_name == "Status":
        return _build_link_status_bins(layer), ""

    classes, mode = extract_legend_classes(layer, field_name)
    if not classes or mode is None:
        return [], field_name

    bins = []
    for class_index, class_data in enumerate(classes):
        mid = class_data.get("mid")
        if mid is None and class_data.get("lo") is not None and class_data.get("hi") is not None:
            mid = (float(class_data["lo"]) + float(class_data["hi"])) / 2.0
        elif mid is None:
            mid = float(class_index)
        bins.append(_make_bin(
            class_data["label"],
            class_data.get("lo"),
            class_data.get("hi"),
            class_data.get("category"),
            class_data.get("color"),
            mid=mid,
        ))

    layer_identifier = _layer_identifier(layer)
    for feature in layer.getFeatures():
        if not _include_feature_for_distribution(feature, field_name, layer_identifier):
            continue
        value = _feature_value_for_classification(feature, field_name, layer_identifier)
        if value is None:
            continue
        class_index = _find_class_index(bins, mode, value)
        if class_index is None:
            continue
        bins[class_index]["count"] += 1
        if mode == "numeric":
            try:
                bins[class_index]["sum"] += float(value)
            except (TypeError, ValueError):
                pass

    for bin_data in bins:
        _finalize_bin(bin_data)

    return bins, ""


def build_cumulative_points(layer, field_name, sample_count=100):
    """Return cumulative counts over a continuous numeric axis for the given field."""
    if layer is None or not field_name:
        return []

    values = []
    layer_identifier = _layer_identifier(layer)
    for feature in layer.getFeatures():
        if not _include_feature_for_distribution(feature, field_name, layer_identifier):
            continue
        value = _feature_value_for_classification(feature, field_name, layer_identifier)
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue

    if not values:
        return []

    values.sort()
    value_min = values[0]
    value_max = values[-1]
    if value_min == value_max:
        return [{"x": value_min, "count": len(values)}]

    samples = max(2, int(sample_count))
    span = value_max - value_min
    points = []
    for index in range(samples):
        threshold = value_min + span * (index / float(samples - 1))
        points.append({
            "x": threshold,
            "count": bisect_right(values, threshold),
        })
    return points


def _histogram_status_label(key):
    return QCoreApplication.translate("QGISRedResultsDock", key)


def _build_link_status_bins(layer):
    """
    Simplified Status distribution for link results:
    only Closed / Open / Active, grouping the detailed renderer classes.
    """

    def _bin(category_key, color):
        return _make_bin(_histogram_status_label(category_key), category=category_key, color=color)

    def _status_group(value):
        status = "" if value is None or value == NULL else str(value).upper()
        if "CLOSED" in status:
            return "Closed"
        if "OPEN" in status:
            return "Open"
        if "ACTIVE" in status:
            return "Active"
        return None

    # Colors chosen to be consistent and readable on light backgrounds.
    bins = [
        _bin("Closed", QColor(198, 40, 40)),  # red
        _bin("Open", QColor(46, 125, 50)),  # green
        _bin("Active", QColor(245, 124, 0)),  # orange
    ]
    idx = {b["category"]: i for i, b in enumerate(bins)}

    for feature in layer.getFeatures():
        raw_status = feature["Status"]
        chosen = _status_group(raw_status)
        bin_index = idx.get(chosen)
        if bin_index is None:
            continue
        bins[bin_index]["count"] += 1

    running = 0
    for b in bins:
        running += b.get("count", 0)
        b["cumulative_count"] = running
        _finalize_bin(b)
    return bins


class _DistributionPopoutWindow(QWidget):
    """Floating, resizable window showing an enlarged copy of the active histogram."""

    _DEFAULT_SIZE = (760, 540)

    def __init__(self, parent, on_close):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Window)
        self._on_close = on_close
        self._default_geometry = None
        self.setMinimumSize(360, 260)
        self.setStyleSheet("background-color: #f8f9fb;")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)

        self.chart = ResultsDistributionWidget(self)
        self.chart.show_title = True
        self.chart.show_subtitle = False
        self._layout.addWidget(self.chart, 1)

    def attachControls(self, controls_bar):
        self._layout.insertWidget(0, controls_bar)

    def detachControls(self, controls_bar):
        self._layout.removeWidget(controls_bar)

    def applyDefaultGeometry(self):
        width, height = self._DEFAULT_SIZE
        host = self.parent().window() if self.parent() is not None else None
        if host is not None:
            center = host.frameGeometry().center()
            self.setGeometry(center.x() - width // 2, center.y() - height // 2, width, height)
        else:
            self.resize(width, height)
        self._default_geometry = self.geometry()

    def closeEvent(self, event):
        callback = self._on_close
        if callback is not None:
            callback()
        super().closeEvent(event)


class _DistributionControlsBar(QWidget):
    """Frequency + Cumulative controls in one row when wide enough, two rows otherwise."""

    # Keep controls on a single line even in narrow docks.
    _MERGE_THRESHOLD = 0

    def __init__(self, freq_label, freq_combo, cum_label, cum_combo, expand_button=None, parent=None):
        super().__init__(parent)
        self._fl = freq_label
        self._fc = freq_combo
        self._cl = cum_label
        self._cc = cum_combo
        self._eb = expand_button
        self._merged = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self._row1 = QHBoxLayout()
        self._row2 = QHBoxLayout()
        outer.addLayout(self._row1)
        outer.addLayout(self._row2)

        self._apply(merged=False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        merged = event.size().width() >= self._MERGE_THRESHOLD
        if merged != self._merged:
            self._apply(merged)

    def _apply(self, merged):
        self._merged = merged
        while self._row1.count():
            self._row1.takeAt(0)
        while self._row2.count():
            self._row2.takeAt(0)

        if merged:
            self._row1.setContentsMargins(6, 0, 0, 0)
            self._row1.setSpacing(8)
            self._row1.addWidget(self._fl)
            self._row1.addWidget(self._fc)
            self._row1.addSpacing(8)
            self._row1.addWidget(self._cl)
            self._row1.addWidget(self._cc)
            if self._eb is not None:
                self._row1.addSpacing(4)
                self._row1.addWidget(self._eb)
            self._row1.addStretch(1)
        else:
            self._row1.setContentsMargins(6, 0, 0, 0)
            self._row1.setSpacing(8)
            self._row1.addWidget(self._fl)
            self._row1.addWidget(self._fc)
            self._row1.addStretch(1)
            self._row2.setContentsMargins(6, 4, 0, 0)
            self._row2.setSpacing(8)
            self._row2.addWidget(self._cl)
            self._row2.addWidget(self._cc)
            if self._eb is not None:
                self._row2.addSpacing(4)
                self._row2.addWidget(self._eb)
            self._row2.addStretch(1)


class _ResultsDistributionMixin:
    _DISTRIBUTION_TITLE_TEMPLATE = "%1 frequency%2"

    def _setupDistributionCharts(self):
        self._distribution_popout = None
        panel_bg = "#f8f9fb"
        self.distributionChartContainer.setStyleSheet(
            "QWidget#distributionChartContainer {{ background-color: {0}; }}".format(panel_bg)
        )
        self.nodeDistributionChartHost.setStyleSheet("background-color: {};".format(panel_bg))
        self.linkDistributionChartHost.setStyleSheet("background-color: {};".format(panel_bg))

        self._node_distribution_chart = ResultsDistributionWidget(self.nodeDistributionChartHost)
        self._link_distribution_chart = ResultsDistributionWidget(self.linkDistributionChartHost)
        node_layout = QVBoxLayout(self.nodeDistributionChartHost)
        node_layout.setContentsMargins(0, 0, 0, 0)
        node_layout.addWidget(self._node_distribution_chart)
        link_layout = QVBoxLayout(self.linkDistributionChartHost)
        link_layout.setContentsMargins(0, 0, 0, 0)
        link_layout.addWidget(self._link_distribution_chart)

        self.lbl_distribution_absolute = self.tr("Absolute")
        self.lbl_distribution_relative = self.tr("Relative")
        self.lbl_distribution_count = self.tr("Count")
        self.lbl_distribution_percent = "%"
        self.cbDistributionFrequency.addItem(self.lbl_distribution_absolute, "absolute")
        self.cbDistributionFrequency.addItem(self.lbl_distribution_relative, "relative")
        self.cbDistributionFrequency.currentIndexChanged.connect(self._distributionFrequencyChanged)

        self.lbl_distribution_none = self.tr("None")
        self.cbDistributionCumulative.addItem(self.lbl_distribution_none, "none")
        self.cbDistributionCumulative.addItem(self.lbl_distribution_absolute, "absolute")
        self.cbDistributionCumulative.addItem(self.lbl_distribution_relative, "relative")
        self.cbDistributionCumulative.currentIndexChanged.connect(self._distributionCumulativeChanged)

        self._compactDistributionOptionControls()

        self.cbNodeDistribution.clicked.connect(self.nodeDistributionClicked)
        self.cbLinkDistribution.clicked.connect(self.linkDistributionClicked)
        try:
            self.visibilityChanged.connect(self._onDistributionDockVisibilityChanged)
        except Exception:
            pass
        self._updateDistributionCheckboxLabels()
        self._syncDistributionPanelVisibility()

    def _distributionChartTitle(self, layer_type):
        """Return a chart title including variable + units, e.g. 'Flow frequency (gpm)'."""
        field_name = self._distributionFieldForLayer(layer_type)
        if not field_name:
            return ""

        element = normalize_element(layer_type)  # 'Node' -> 'Nodes', 'Link' -> 'Links'
        fu = QGISRedFieldUtils()
        prop = fu.getProperty(element, field_name, translate=True) or self._distributionMagnitudeLabel(layer_type)
        unit = fu.getUnitAbbreviation(element, field_name) or ""
        unit_part = f" ({unit})" if unit else ""
        return self.tr(self._DISTRIBUTION_TITLE_TEMPLATE).replace("%1", prop).replace("%2", unit_part)

    def _compactDistributionOptionControls(self):
        label_style = "font-weight: bold; font-size: 8pt; color: #303030;"
        for label in (self.lbDistributionFrequency, self.lbDistributionCumulative):
            label.setStyleSheet(label_style)
            label.setMinimumWidth(0)
            # Keep labels compact so both combos fit on one row in narrow layouts.
            label.setMaximumWidth(42)

        # Shorten label text to free horizontal space.
        self.lbDistributionFrequency.setText(self.tr("Freq"))
        self.lbDistributionCumulative.setText(self.tr("Cumul"))

        for combo in (self.cbDistributionFrequency, self.cbDistributionCumulative):
            self._applyDistributionComboStyle(combo)
            combo.setMaximumWidth(78)

        self.btDistributionExpand = QToolButton()
        self.btDistributionExpand.setObjectName("btDistributionExpand")
        self.btDistributionExpand.setIcon(QIcon(":/images/iconTsZoomWindow.svg"))
        self.btDistributionExpand.setIconSize(QSize(16, 16))
        self.btDistributionExpand.setAutoRaise(True)
        self.btDistributionExpand.setCheckable(True)
        self.btDistributionExpand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btDistributionExpand.setToolTip(self.tr("Expand histogram to a floating window"))
        self.btDistributionExpand.clicked.connect(self._toggleDistributionPopout)

        parent_layout = self.verticalLayout_DistributionChart
        freq_row = self.horizontalLayout_DistributionFrequency
        cum_row = self.horizontalLayout_DistributionCumulative

        freq_index = parent_layout.indexOf(freq_row)
        parent_layout.removeItem(freq_row)
        parent_layout.removeItem(cum_row)

        self._dist_controls_bar = _DistributionControlsBar(
            self.lbDistributionFrequency,
            self.cbDistributionFrequency,
            self.lbDistributionCumulative,
            self.cbDistributionCumulative,
            expand_button=self.btDistributionExpand,
        )
        parent_layout.insertWidget(freq_index, self._dist_controls_bar)

    def _distributionBarMode(self):
        frequency_id = self.cbDistributionFrequency.currentData(Qt.ItemDataRole.UserRole)
        if frequency_id == "relative":
            return "relative"
        return "plain"

    def _distributionCumulativeMode(self):
        cumulative_id = self.cbDistributionCumulative.currentData(Qt.ItemDataRole.UserRole)
        if cumulative_id in ("absolute", "relative"):
            return cumulative_id
        return None

    def _isStatusDistributionActive(self):
        active = self._activeDistributionLayerType()
        return active is not None and self._distributionFieldForLayer(active) == "Status"

    def _setDistributionFrequencyMode(self, mode):
        index = self.cbDistributionFrequency.findData(mode, Qt.ItemDataRole.UserRole)
        if index >= 0 and self.cbDistributionFrequency.currentIndex() != index:
            self.cbDistributionFrequency.blockSignals(True)
            self.cbDistributionFrequency.setCurrentIndex(index)
            self.cbDistributionFrequency.blockSignals(False)

    def _setDistributionCumulativeMode(self, mode):
        index = self.cbDistributionCumulative.findData(mode, Qt.ItemDataRole.UserRole)
        if index >= 0 and self.cbDistributionCumulative.currentIndex() != index:
            self.cbDistributionCumulative.blockSignals(True)
            self.cbDistributionCumulative.setCurrentIndex(index)
            self.cbDistributionCumulative.blockSignals(False)

    def _syncStatusDistributionModesFromFrequency(self):
        if not self._isStatusDistributionActive() or self._distributionCumulativeMode() is None:
            return
        mode = "relative" if self._distributionBarMode() == "relative" else "absolute"
        self._setDistributionCumulativeMode(mode)

    def _syncStatusDistributionModesFromCumulative(self):
        if not self._isStatusDistributionActive():
            return
        mode = self._distributionCumulativeMode()
        if mode is not None:
            self._setDistributionFrequencyMode(mode)

    def _distributionYAxisLabel(self):
        if self._distributionBarMode() == "relative":
            return self.lbl_distribution_percent
        return self.lbl_distribution_count

    def _distributionCumulativeYAxisLabel(self):
        if self._distributionCumulativeMode() == "relative":
            return self.lbl_distribution_percent
        return self.lbl_distribution_count

    def _distributionFrequencyChanged(self):
        if self._activeDistributionLayerType() is None:
            return
        self._syncStatusDistributionModesFromFrequency()
        self._refreshDistributionChartsIfNeeded()

    def _distributionCumulativeChanged(self):
        if self._activeDistributionLayerType() is None:
            return
        self._syncStatusDistributionModesFromCumulative()
        self._refreshDistributionChartsIfNeeded()

    def _distributionMagnitudeLabel(self, layer_type):
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks
        if combobox.currentIndex() <= 0:
            return ""
        return combobox.currentText()

    def _distributionCheckboxText(self, layer_type):
        if layer_type == "Node":
            return self.tr("Show Node Histogram")
        return self.tr("Show Link Histogram")

    def _updateDistributionCheckboxLabels(self):
        self.cbNodeDistribution.setText(self._distributionCheckboxText("Node"))
        self.cbLinkDistribution.setText(self._distributionCheckboxText("Link"))
        node_enabled = self.cbNodes.currentIndex() > 0
        link_enabled = self.cbLinks.currentIndex() > 0
        self.cbNodeDistribution.setEnabled(node_enabled)
        self.cbLinkDistribution.setEnabled(link_enabled)
        if not node_enabled and self.cbNodeDistribution.isChecked():
            self.cbNodeDistribution.setChecked(False)
        if not link_enabled and self.cbLinkDistribution.isChecked():
            self.cbLinkDistribution.setChecked(False)
        self._syncDistributionPanelVisibility()

    def _activeDistributionLayerType(self):
        if self.cbNodeDistribution.isChecked():
            return "Node"
        if self.cbLinkDistribution.isChecked():
            return "Link"
        return None

    def _syncDistributionPanelVisibility(self):
        active = self._activeDistributionLayerType()
        popout = getattr(self, "_distribution_popout", None)
        expanded = popout is not None and popout.isVisible()
        if active is None and expanded:
            self._closeDistributionPopout()
            return
        if expanded:
            return
        self.distributionChartContainer.setVisible(active is not None)
        self._applySmallChartVisibility()

    def _applySmallChartVisibility(self):
        active = self._activeDistributionLayerType()
        self.nodeDistributionChartHost.setVisible(active == "Node")
        self.linkDistributionChartHost.setVisible(active == "Link")

    def _toggleDistributionPopout(self):
        popout = getattr(self, "_distribution_popout", None)
        if popout is not None and popout.isVisible():
            self._closeDistributionPopout()
        else:
            self._openDistributionPopout()

    def _openDistributionPopout(self):
        active = self._activeDistributionLayerType()
        if active is None:
            self._setExpandButtonState(False)
            return
        if self._distribution_popout is None:
            self._distribution_popout = _DistributionPopoutWindow(self, self._onDistributionPopoutClosed)
        if self._distribution_popout._default_geometry is None:
            self._distribution_popout.applyDefaultGeometry()
        self._moveControlsToPopout()
        self._setExpandButtonState(True)
        self._distribution_popout.show()
        self._distribution_popout.raise_()
        self._distribution_popout.activateWindow()
        self._refreshDistributionChart(active)

    def _closeDistributionPopout(self):
        popout = getattr(self, "_distribution_popout", None)
        if popout is not None and popout.isVisible():
            popout.close()
        else:
            self._finishPopoutClose()

    def _onDistributionPopoutClosed(self):
        self._finishPopoutClose()

    def _finishPopoutClose(self):
        self._setExpandButtonState(False)
        self._restoreControlsToDock()

    def _onDistributionDockVisibilityChanged(self, visible):
        if not visible:
            self._closeDistributionPopout()

    def _setExpandButtonState(self, expanded):
        button = getattr(self, "btDistributionExpand", None)
        if button is None:
            return
        button.blockSignals(True)
        button.setChecked(expanded)
        button.blockSignals(False)
        button.setToolTip(
            self.tr("Collapse histogram back to the panel")
            if expanded
            else self.tr("Expand histogram to a floating window")
        )

    def _moveControlsToPopout(self):
        bar = getattr(self, "_dist_controls_bar", None)
        popout = getattr(self, "_distribution_popout", None)
        if bar is None or popout is None:
            return
        self.verticalLayout_DistributionChart.removeWidget(bar)
        popout.attachControls(bar)
        self.distributionChartContainer.setVisible(False)

    def _restoreControlsToDock(self):
        bar = getattr(self, "_dist_controls_bar", None)
        popout = getattr(self, "_distribution_popout", None)
        if bar is not None:
            if popout is not None:
                popout.detachControls(bar)
            self.verticalLayout_DistributionChart.insertWidget(0, bar)
        active = self._activeDistributionLayerType()
        self.distributionChartContainer.setVisible(active is not None)
        self._applySmallChartVisibility()

    def _feedDistributionPopout(self, layer_type, bins, bin_kwargs):
        popout = getattr(self, "_distribution_popout", None)
        if popout is None or not popout.isVisible():
            return
        if layer_type != self._activeDistributionLayerType():
            return
        popout.chart.show_title = True
        popout.chart.show_subtitle = False
        popout.chart.setBins(bins, **bin_kwargs)
        popout.setWindowTitle(bin_kwargs.get("title") or self.tr("Histogram"))

    def _distributionFieldForLayer(self, layer_type):
        if layer_type == "Node":
            field_map = self._node_field_map
            combobox = self.cbNodes
            return self.displayingNodeField or field_map.get(combobox.currentText(), "")
        field_map = self._link_field_map
        combobox = self.cbLinks
        return self.displayingLinkField or field_map.get(combobox.currentText(), "")

    def _refreshDistributionChart(self, layer_type):
        chart = self._node_distribution_chart if layer_type == "Node" else self._link_distribution_chart
        checkbox = self.cbNodeDistribution if layer_type == "Node" else self.cbLinkDistribution
        if not checkbox.isChecked():
            chart.clear()
            return

        if not self.validationsOpenResult():
            chart.clear()
            return

        layer = self._findResultLayer(layer_type)
        field_name = self._distributionFieldForLayer(layer_type)
        bins, x_label = build_distribution_bins(layer, field_name)
        is_status = field_name == "Status"
        if is_status and self._distributionCumulativeMode() is not None:
            self._syncStatusDistributionModesFromCumulative()
        cumulative_points = (
            build_cumulative_points(layer, field_name)
            if self._distributionCumulativeMode() in ("absolute", "relative") and not is_status
            else []
        )
        if cumulative_points and field_name and field_name != "Status":
            element = normalize_element(layer_type)
            fu = QGISRedFieldUtils()
            x_label = fu.getProperty(element, field_name, translate=True) or field_name
        bin_kwargs = dict(
            bar_mode=self._distributionBarMode(),
            cumulative_mode=self._distributionCumulativeMode(),
            cumulative_points=cumulative_points,
            xLabel=x_label,
            yLabelLeft=self._distributionYAxisLabel(),
            yLabelRight=self._distributionCumulativeYAxisLabel(),
            title=self._distributionChartTitle(layer_type),
        )
        chart.show_title = True
        chart.show_subtitle = False
        chart.setBins(bins, **bin_kwargs)
        chart.updateGeometry()
        self._feedDistributionPopout(layer_type, bins, bin_kwargs)

    def _refreshDistributionChartsIfNeeded(self):
        self._updateDistributionCheckboxLabels()
        if self.cbNodeDistribution.isChecked():
            self._refreshDistributionChart("Node")
        if self.cbLinkDistribution.isChecked():
            self._refreshDistributionChart("Link")

    def nodeDistributionClicked(self):
        if self.cbNodeDistribution.isChecked():
            self.cbLinkDistribution.blockSignals(True)
            self.cbLinkDistribution.setChecked(False)
            self.cbLinkDistribution.blockSignals(False)
            if self.cbNodes.currentIndex() <= 0:
                self.cbNodeDistribution.setChecked(False)
                return
            if not self.validationsOpenResult():
                self.cbNodeDistribution.setChecked(False)
                return
            self.ensureResultsLayersAreOpen()
        self._syncDistributionPanelVisibility()
        self._refreshDistributionChart("Node")
        if not self.cbNodeDistribution.isChecked():
            self._node_distribution_chart.clear()

    def linkDistributionClicked(self):
        if self.cbLinkDistribution.isChecked():
            self.cbNodeDistribution.blockSignals(True)
            self.cbNodeDistribution.setChecked(False)
            self.cbNodeDistribution.blockSignals(False)
            if self.cbLinks.currentIndex() <= 0:
                self.cbLinkDistribution.setChecked(False)
                return
            if not self.validationsOpenResult():
                self.cbLinkDistribution.setChecked(False)
                return
            self.ensureResultsLayersAreOpen()
        self._syncDistributionPanelVisibility()
        self._refreshDistributionChart("Link")
        if not self.cbLinkDistribution.isChecked():
            self._link_distribution_chart.clear()
