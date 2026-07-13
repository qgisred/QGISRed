# -*- coding: utf-8 -*-
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QDialog, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton, QColorDialog,
    QDialogButtonBox, QGridLayout, QScrollArea
)

from .profile_chart_settings import (
    ProfileAxisSettings, ProfileGeneralSettings, ProfileCurveStyle,
    LINE_STYLES, LEGEND_POSITIONS, clone_axis, clone_general, clone_curve_overrides,
)


class QGISRedProfileChartOptionsDialog(QDialog):
    def __init__(self, plot_widget, parent=None):
        super(QGISRedProfileChartOptionsDialog, self).__init__(parent)
        self._plot = plot_widget
        self.setWindowTitle(self.tr("QGISRed: Chart options"))
        self.setMinimumWidth(460)

        self._cfg_x = clone_axis(plot_widget._axis_cfg_x)
        self._cfg_y = clone_axis(plot_widget._axis_cfg_y)
        self._cfg_y_right = clone_axis(plot_widget._axis_cfg_y_right)
        self._cfg_gen = clone_general(plot_widget._general_cfg)
        self._overrides = clone_curve_overrides(plot_widget._curve_overrides)
        self._has_right_axis = plot_widget._hasRightAxis()

        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)
        tabs.addTab(self._buildAxesTab(), self.tr("Axes"))
        tabs.addTab(self._buildCurvesTab(), self.tr("Curves"))
        tabs.addTab(self._buildLegendTab(), self.tr("Legend"))
        tabs.addTab(self._buildGeneralTab(), self.tr("General"))
        layout.addWidget(tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply,
            self)
        buttons.accepted.connect(self._onOk)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        layout.addWidget(buttons)

    # ---- axis tab ----
    def _buildAxesTab(self):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        self._x_widgets = self._buildAxisGroup(layout, self.tr("X axis (distance)"), self._cfg_x)
        self._y_widgets = self._buildAxisGroup(layout, self.tr("Y axis (left)"), self._cfg_y)
        self._y_right_widgets = None
        if self._has_right_axis:
            self._y_right_widgets = self._buildAxisGroup(layout, self.tr("Y axis (right)"), self._cfg_y_right)
        layout.addStretch(1)
        return tab

    def _buildAxisGroup(self, parent_layout, title, cfg):
        group = QGroupBox(title)
        form = QFormLayout(group)
        widgets = {}

        widgets["title"] = QLineEdit(cfg.title)
        form.addRow(self.tr("Title:"), widgets["title"])

        widgets["auto"] = QCheckBox(self.tr("Auto scale"))
        widgets["auto"].setChecked(cfg.auto_scale)
        form.addRow("", widgets["auto"])

        widgets["min"] = self._spin(cfg.fixed_min)
        form.addRow(self.tr("Minimum:"), widgets["min"])
        widgets["max"] = self._spin(cfg.fixed_max)
        form.addRow(self.tr("Maximum:"), widgets["max"])

        widgets["grid"] = QCheckBox(self.tr("Show grid"))
        widgets["grid"].setChecked(cfg.show_grid)
        form.addRow("", widgets["grid"])

        def sync_enabled():
            manual = not widgets["auto"].isChecked()
            widgets["min"].setEnabled(manual)
            widgets["max"].setEnabled(manual)
        widgets["auto"].toggled.connect(lambda _c: sync_enabled())
        sync_enabled()

        parent_layout.addWidget(group)
        return widgets

    def _spin(self, value):
        spin = QDoubleSpinBox()
        spin.setRange(-1e9, 1e9)
        spin.setDecimals(3)
        spin.setValue(float(value))
        return spin

    # ---- curves tab ----
    def _buildCurvesTab(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        holder = QWidget()
        vbox = QVBoxLayout(holder)

        self._curve_widgets = {}
        for series in getattr(self._plot, "_series", []):
            label = series["label"]
            style = self._overrides.get(label) or ProfileCurveStyle(
                color_hex=series["color"].name() if isinstance(series["color"], QColor) else "",
                width=series.get("base_width", series.get("width", 2.0)),
            )
            group = QGroupBox(label)
            form = QFormLayout(group)

            base = series["color"] if isinstance(series["color"], QColor) else QColor("#1f77b4")
            color_btn = self._colorButton(style.color_hex or base.name(), self.tr("Curve color"))
            form.addRow(self.tr("Color"), color_btn)

            style_combo = QComboBox()
            style_labels = {
                "solid": self.tr("Solid"),
                "dashed": self.tr("Dashed"),
                "dotted": self.tr("Dotted"),
            }
            for key in LINE_STYLES:
                style_combo.addItem(style_labels.get(key, key))
            if style.line_style in LINE_STYLES:
                style_combo.setCurrentIndex(LINE_STYLES.index(style.line_style))
            form.addRow(self.tr("Line style"), style_combo)

            width_spin = QDoubleSpinBox()
            width_spin.setRange(0.5, 8.0)
            width_spin.setSingleStep(0.5)
            width_spin.setValue(float(style.width))
            form.addRow(self.tr("Width"), width_spin)

            markers_chk = QCheckBox()
            markers_chk.setChecked(bool(style.show_markers))
            form.addRow(self.tr("Markers"), markers_chk)

            marker_spin = QDoubleSpinBox()
            marker_spin.setRange(1.0, 12.0)
            marker_spin.setSingleStep(0.5)
            marker_spin.setValue(float(style.marker_size))
            form.addRow(self.tr("Marker size"), marker_spin)

            self._curve_widgets[label] = {
                "color": color_btn, "style": style_combo, "width": width_spin,
                "markers": markers_chk, "marker_size": marker_spin,
            }
            vbox.addWidget(group)

        vbox.addStretch(1)
        scroll.setWidget(holder)
        return scroll

    # ---- legend tab ----
    def _buildLegendTab(self):
        tab = QWidget(self)
        form = QFormLayout(tab)

        self._chk_legend = QCheckBox(self.tr("Show legend"))
        self._chk_legend.setChecked(self._cfg_gen.show_legend)
        form.addRow("", self._chk_legend)

        self._legend_pos_keys = list(LEGEND_POSITIONS)
        self._legend_pos = QComboBox()
        pos_labels = {"left": self.tr("Left"), "center": self.tr("Center"), "right": self.tr("Right")}
        for key in self._legend_pos_keys:
            self._legend_pos.addItem(pos_labels.get(key, key))
        if self._cfg_gen.legend_position in self._legend_pos_keys:
            self._legend_pos.setCurrentIndex(self._legend_pos_keys.index(self._cfg_gen.legend_position))
        form.addRow(self.tr("Position:"), self._legend_pos)

        self._legend_font = QSpinBox()
        self._legend_font.setRange(6, 16)
        self._legend_font.setValue(int(self._cfg_gen.legend_font_size))
        form.addRow(self.tr("Font size:"), self._legend_font)

        self._legend_symbol = QSpinBox()
        self._legend_symbol.setRange(8, 40)
        self._legend_symbol.setValue(int(self._cfg_gen.legend_symbol_size))
        form.addRow(self.tr("Symbol size:"), self._legend_symbol)

        self._legend_frame = QCheckBox(self.tr("Show frame"))
        self._legend_frame.setChecked(self._cfg_gen.legend_show_frame)
        form.addRow("", self._legend_frame)

        self._legend_bg_btn = self._colorButton(self._cfg_gen.legend_bg_hex, self.tr("Background color"))
        form.addRow(self.tr("Background:"), self._legend_bg_btn)
        return tab

    # ---- general tab ----
    def _buildGeneralTab(self):
        tab = QWidget(self)
        form = QFormLayout(tab)
        self._bg_btn = self._colorButton(self._cfg_gen.plot_bg_hex, self.tr("Background color"))
        form.addRow(self.tr("Plot background:"), self._bg_btn)
        return tab

    # ---- color button helper ----
    def _colorButton(self, hex_str, title):
        btn = QPushButton()
        btn.setFixedWidth(60)
        self._setButtonColor(btn, hex_str)
        btn.clicked.connect(lambda: self._pickColor(btn, title))
        return btn

    def _setButtonColor(self, btn, hex_str):
        color = QColor(hex_str) if hex_str else QColor()
        btn._hex = color.name() if color.isValid() else ""
        if color.isValid():
            btn.setStyleSheet("background-color: %s; border: 1px solid #888;" % color.name())
        else:
            btn.setStyleSheet("")

    def _pickColor(self, btn, title):
        initial = QColor(getattr(btn, "_hex", "") or "#000000")
        color = QColorDialog.getColor(initial, self, title)
        if color.isValid():
            self._setButtonColor(btn, color.name())

    # ---- apply ----
    def _apply(self):
        self._cfg_x.title = self._x_widgets["title"].text()
        self._cfg_x.auto_scale = self._x_widgets["auto"].isChecked()
        self._cfg_x.fixed_min = self._x_widgets["min"].value()
        self._cfg_x.fixed_max = self._x_widgets["max"].value()
        self._cfg_x.show_grid = self._x_widgets["grid"].isChecked()

        self._cfg_y.title = self._y_widgets["title"].text()
        self._cfg_y.auto_scale = self._y_widgets["auto"].isChecked()
        self._cfg_y.fixed_min = self._y_widgets["min"].value()
        self._cfg_y.fixed_max = self._y_widgets["max"].value()
        self._cfg_y.show_grid = self._y_widgets["grid"].isChecked()

        if self._y_right_widgets is not None:
            self._cfg_y_right.title = self._y_right_widgets["title"].text()
            self._cfg_y_right.auto_scale = self._y_right_widgets["auto"].isChecked()
            self._cfg_y_right.fixed_min = self._y_right_widgets["min"].value()
            self._cfg_y_right.fixed_max = self._y_right_widgets["max"].value()
            self._cfg_y_right.show_grid = self._y_right_widgets["grid"].isChecked()

        self._cfg_gen.show_legend = self._chk_legend.isChecked()
        self._cfg_gen.plot_bg_hex = getattr(self._bg_btn, "_hex", "") or self._cfg_gen.plot_bg_hex
        self._cfg_gen.legend_position = self._legend_pos_keys[self._legend_pos.currentIndex()]
        self._cfg_gen.legend_font_size = self._legend_font.value()
        self._cfg_gen.legend_symbol_size = self._legend_symbol.value()
        self._cfg_gen.legend_show_frame = self._legend_frame.isChecked()
        self._cfg_gen.legend_bg_hex = getattr(self._legend_bg_btn, "_hex", "")

        overrides = {}
        for label, widgets in self._curve_widgets.items():
            overrides[label] = ProfileCurveStyle(
                color_hex=getattr(widgets["color"], "_hex", ""),
                width=widgets["width"].value(),
                line_style=LINE_STYLES[widgets["style"].currentIndex()],
                show_markers=widgets["markers"].isChecked(),
                marker_size=widgets["marker_size"].value(),
            )

        self._plot._axis_cfg_x = clone_axis(self._cfg_x)
        self._plot._axis_cfg_y = clone_axis(self._cfg_y)
        self._plot._axis_cfg_y_right = clone_axis(self._cfg_y_right)
        self._plot._general_cfg = clone_general(self._cfg_gen)
        self._plot._curve_overrides = overrides
        self._plot.applyChartSettings()

    def _onOk(self):
        self._apply()
        self.accept()
