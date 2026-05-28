# -*- coding: utf-8 -*-
"""Distribution histogram helpers and dock mixin for simulation results."""
from __future__ import annotations

import re

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QHBoxLayout, QVBoxLayout
from qgis.core import (
    NULL,
    QgsCategorizedSymbolRenderer,
    QgsGraduatedSymbolRenderer,
    QgsRuleBasedRenderer,
)

from ...tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL
from .results_distribution_widget import ResultsDistributionWidget


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


def _feature_value_for_classification(feature, field_name):
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

    for feature in layer.getFeatures():
        value = _feature_value_for_classification(feature, field_name)
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


class _ResultsDistributionMixin:
    _DISTRIBUTION_CHECKBOX_TEMPLATE = "Show the %1 Distribution"

    def _setupDistributionCharts(self):
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
        self._updateDistributionCheckboxLabels()
        self._syncDistributionPanelVisibility()

    def _compactDistributionOptionControls(self):
        label_style = "font-weight: bold; font-size: 8pt; color: #303030;"
        for label in (self.lbDistributionFrequency, self.lbDistributionCumulative):
            label.setStyleSheet(label_style)
            label.setMinimumWidth(0)
            label.setMaximumWidth(72)

        for combo in (self.cbDistributionFrequency, self.cbDistributionCumulative):
            self._applyDistributionComboStyle(combo)

        parent_layout = self.verticalLayout_DistributionChart
        freq_row = self.horizontalLayout_DistributionFrequency
        cum_row = self.horizontalLayout_DistributionCumulative

        merged = QHBoxLayout()
        merged.setSpacing(8)
        merged.setContentsMargins(6, 0, 0, 0)

        while freq_row.count():
            item = freq_row.takeAt(0)
            if item.widget():
                merged.addWidget(item.widget())
            elif item.layout():
                merged.addLayout(item.layout())
            elif item.spacerItem():
                merged.addItem(item.spacerItem())

        merged.addSpacing(4)

        while cum_row.count():
            item = cum_row.takeAt(0)
            if item.widget():
                merged.addWidget(item.widget())
            elif item.layout():
                merged.addLayout(item.layout())
            elif item.spacerItem():
                merged.addItem(item.spacerItem())

        merged.addStretch(1)

        parent_index = parent_layout.indexOf(freq_row)
        parent_layout.removeItem(freq_row)
        parent_layout.removeItem(cum_row)
        parent_layout.insertLayout(parent_index, merged)

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
        self._refreshDistributionChartsIfNeeded()

    def _distributionCumulativeChanged(self):
        if self._activeDistributionLayerType() is None:
            return
        self._refreshDistributionChartsIfNeeded()

    def _distributionMagnitudeLabel(self, layer_type):
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks
        if combobox.currentIndex() <= 0:
            return ""
        return combobox.currentText()

    def _distributionCheckboxText(self, layer_type):
        magnitude = self._distributionMagnitudeLabel(layer_type)
        if not magnitude:
            return self.tr(self._DISTRIBUTION_CHECKBOX_TEMPLATE).replace("%1", "…")
        return self.tr(self._DISTRIBUTION_CHECKBOX_TEMPLATE).replace("%1", magnitude)

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
        show_panel = active is not None
        self.distributionChartContainer.setVisible(show_panel)
        self.nodeDistributionChartHost.setVisible(active == "Node")
        self.linkDistributionChartHost.setVisible(active == "Link")

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
        chart.setBins(
            bins,
            bar_mode=self._distributionBarMode(),
            cumulative_mode=self._distributionCumulativeMode(),
            xLabel=x_label,
            yLabelLeft=self._distributionYAxisLabel(),
            yLabelRight=self._distributionCumulativeYAxisLabel(),
        )
        chart.updateGeometry()

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
