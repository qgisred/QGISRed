# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
import math
import os

from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QButtonGroup,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .timeseries_axis_settings import TimeSeriesAxisSettings, TimeSeriesGeneralSettings, clone_axis_settings, clone_general_settings
from .timeseries_plot_style import FONT_FAMILY


class TimeSeriesAxisOptionsDialog(QDialog):
    _MIN_DIALOG_WIDTH = 560
    _MIN_DIALOG_HEIGHT = 480
    _LONG_FIELD_WIDTH = 360
    _FORM_FIELD_WIDTH = 280
    _FONT_FIELD_WIDTH = 260
    _LIVE_UPDATE_SETTINGS_KEY = "QGISRed/timeseries_chart_live_update"

    def __init__(self, plot_widget, parent=None):
        win = parent.window() if parent is not None else None
        super().__init__(win if win is not None else parent)
        self._plot = plot_widget
        self.setWindowTitle(self.tr("QGISRed: Chart options"))
        self.setMinimumSize(self._MIN_DIALOG_WIDTH, self._MIN_DIALOG_HEIGHT)
        self.setSizeGripEnabled(True)

        self._cfg_x = clone_axis_settings(plot_widget._axis_cfg_x)
        self._cfg_yl = clone_axis_settings(plot_widget._axis_cfg_y_left)
        self._cfg_yr = clone_axis_settings(plot_widget._axis_cfg_y_right)
        self._cfg_gen = clone_general_settings(getattr(plot_widget, "_general_cfg", TimeSeriesGeneralSettings()))
        self._curve_cfg = [dict(s) for s in (getattr(plot_widget, "series", []) or [])]
        self._snapshot_x = clone_axis_settings(plot_widget._axis_cfg_x)
        self._snapshot_yl = clone_axis_settings(plot_widget._axis_cfg_y_left)
        self._snapshot_yr = clone_axis_settings(plot_widget._axis_cfg_y_right)
        self._snapshot_gen = clone_general_settings(getattr(plot_widget, "_general_cfg", TimeSeriesGeneralSettings()))
        self._snapshot_series = copy.deepcopy(getattr(plot_widget, "series", []) or [])
        self._dirty_applied = False
        self._ui_dirty = False
        self._live_apply_timer = QTimer(self)
        self._live_apply_timer.setSingleShot(True)
        self._live_apply_timer.timeout.connect(self._apply_options_if_live)

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        content_scroll = QScrollArea(self)
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget(content_scroll)
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(10)
        content_lay.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget(self)
        tab_general = self._build_general_tab(self._cfg_gen)
        tabs.addTab(tab_general, self.tr("General"))
        axes_tab, axes_tabs = self._build_axes_tab()
        tabs.addTab(axes_tab, self.tr("Axes"))
        tab_legend = self._build_legend_tab(self._cfg_gen)
        tabs.addTab(tab_legend, self.tr("Legend"))
        tab_curves = self._build_curves_tab()
        tabs.addTab(tab_curves, self.tr("Curves"))

        content_lay.addWidget(tabs)
        content_scroll.setWidget(content)
        root.addWidget(content_scroll, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        apply_button = buttons.addButton(QDialogButtonBox.StandardButton.Apply)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        apply_button.clicked.connect(self._apply_options)

        self._chk_live_update = QCheckBox(self.tr("Live update"))
        self._chk_live_update.setChecked(self._load_live_update_pref())
        self._chk_live_update.toggled.connect(self._on_live_update_toggled)

        footer = QWidget(self)
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(0, 0, 0, 0)
        footer_lay.setSpacing(12)
        footer_lay.addWidget(self._chk_live_update)
        footer_lay.addStretch(1)
        footer_lay.addWidget(buttons)
        root.addWidget(footer)

        self._tabs = tabs
        self._axes_tabs = axes_tabs
        self._tab_general = tab_general
        self._tab_legend = tab_legend
        self._tab_curves = tab_curves
        self._connect_live_update_signals(content)
        self._configure_initial_geometry()

    def _make_form_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        return lbl

    def _limit_field_width(self, field: QWidget, width=None) -> QWidget:
        field.setMaximumWidth(int(width or self._FORM_FIELD_WIDTH))
        try:
            field.setSizePolicy(QSizePolicy.Policy.Preferred, field.sizePolicy().verticalPolicy())
        except Exception:
            pass
        return field

    def _show_color_on_button(self, btn: QPushButton, color: QColor) -> None:
        hex_color = color.name(QColor.NameFormat.HexRgb)
        btn.setText("")
        btn.setToolTip("")
        btn.setStyleSheet(
            "QPushButton {"
            f"background-color: {hex_color};"
            "border: 1px solid palette(mid);"
            "border-radius: 2px;"
            "}"
        )

    def _add_form_row(self, form: QFormLayout, label_text: str, field: QWidget) -> None:
        form.addRow(self._make_form_label(label_text), field)

    def _compact_group(self, grp: QGroupBox) -> QGroupBox:
        grp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        return grp

    def _load_live_update_pref(self) -> bool:
        try:
            from qgis.core import QgsSettings

            return bool(QgsSettings().value(self._LIVE_UPDATE_SETTINGS_KEY, False, type=bool))
        except Exception:
            return False

    def _save_live_update_pref(self, enabled: bool) -> None:
        try:
            from qgis.core import QgsSettings

            QgsSettings().setValue(self._LIVE_UPDATE_SETTINGS_KEY, bool(enabled))
        except Exception:
            pass

    def _schedule_live_apply(self, *_args) -> None:
        if bool(getattr(self._tab_curves, "_curve_loading", False)):
            return
        if not self._chk_live_update.isChecked():
            self._ui_dirty = True
            return
        self._live_apply_timer.start(80)

    def _apply_options_if_live(self) -> None:
        if self._chk_live_update.isChecked():
            self._apply_options()

    def _on_live_update_toggled(self, checked: bool) -> None:
        self._save_live_update_pref(checked)
        if checked and self._ui_dirty:
            self._apply_options()
            self._ui_dirty = False

    def _connect_live_update_signals(self, root: QWidget) -> None:
        for spin in root.findChildren(QSpinBox):
            spin.valueChanged.connect(self._schedule_live_apply)
        for spin in root.findChildren(QDoubleSpinBox):
            spin.valueChanged.connect(self._schedule_live_apply)
        for combo in root.findChildren(QComboBox):
            combo.currentIndexChanged.connect(self._schedule_live_apply)
        for chk in root.findChildren(QCheckBox):
            chk.toggled.connect(self._schedule_live_apply)
        for edit in root.findChildren(QLineEdit):
            edit.textChanged.connect(self._schedule_live_apply)
        for radio in root.findChildren(QRadioButton):
            radio.toggled.connect(self._schedule_live_apply)
        for font_combo in root.findChildren(QFontComboBox):
            try:
                font_combo.currentFontChanged.connect(self._schedule_live_apply)
            except Exception:
                pass
        for grp in root.findChildren(QGroupBox):
            if grp.isCheckable():
                grp.toggled.connect(self._schedule_live_apply)

    def _restore_snapshot(self) -> None:
        self._plot._axis_cfg_x = clone_axis_settings(self._snapshot_x)
        self._plot._axis_cfg_y_left = clone_axis_settings(self._snapshot_yl)
        self._plot._axis_cfg_y_right = clone_axis_settings(self._snapshot_yr)
        self._plot._general_cfg = clone_general_settings(self._snapshot_gen)
        series = getattr(self._plot, "series", []) or []
        for idx, snap in enumerate(self._snapshot_series):
            if idx >= len(series):
                break
            if isinstance(snap, dict):
                series[idx].clear()
                series[idx].update(copy.deepcopy(snap))
        self._plot._updateMinimumWidthForTitle()
        self._plot.update()
        try:
            self._plot._emitSeriesEmphasisChanged()
        except Exception:
            pass

    def reject(self) -> None:
        if self._dirty_applied:
            self._restore_snapshot()
        super().reject()

    def _build_text_style_row(self, *, font_family: str, font_size: int, color: QColor, color_title: str, on_changed=None):
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(8)

        font_combo = QFontComboBox()
        font_combo.setMaxVisibleItems(8)
        font_combo.setMinimumWidth(150)
        font_combo.setMaximumWidth(self._FONT_FIELD_WIDTH)
        fam = (font_family or "").strip()
        if fam:
            font_combo.setCurrentFont(QFont(fam))

        sp_size = QSpinBox()
        sp_size.setRange(5, 48)
        sp_size.setValue(max(5, min(int(font_size or 10), 48)))
        sp_size.setMinimumWidth(64)
        sp_size.setMaximumWidth(80)

        picked_color = QColor(color)
        if not picked_color.isValid():
            picked_color = QColor("#000000")
        btn_color = QPushButton()
        btn_color.setMinimumHeight(28)
        btn_color.setMinimumWidth(46)
        self._show_color_on_button(btn_color, picked_color)
        row._text_style_color = picked_color

        def pick_color():
            current = getattr(row, "_text_style_color", picked_color)
            nc = QColorDialog.getColor(current, self, color_title)
            if nc.isValid():
                row._text_style_color = nc
                self._show_color_on_button(btn_color, nc)
                if callable(on_changed):
                    on_changed()

        btn_color.clicked.connect(pick_color)

        row_lay.addWidget(QLabel(self.tr("Font:")))
        row_lay.addWidget(font_combo, 1)
        row_lay.addWidget(QLabel(self.tr("Size:")))
        row_lay.addWidget(sp_size)
        row_lay.addWidget(QLabel(self.tr("Color:")))
        row_lay.addWidget(btn_color)
        row_lay.addStretch(1)
        return row, font_combo, sp_size

    def _configure_initial_geometry(self) -> None:
        max_w = max(self._MIN_DIALOG_WIDTH, 700)
        max_h = max(self._MIN_DIALOG_HEIGHT, 720)
        try:
            screen = self.screen() or QApplication.primaryScreen()
            if screen is not None:
                available = screen.availableGeometry()
                max_w = max(self._MIN_DIALOG_WIDTH, int(available.width() * 0.85))
                max_h = max(self._MIN_DIALOG_HEIGHT, int(available.height() * 0.92))
                self.setMaximumSize(max_w, max_h)
        except Exception:
            pass

        try:
            self.layout().activate()
        except Exception:
            pass

        time_axis_h = self._MIN_DIALOG_HEIGHT
        try:
            time_axis_h = int(self._axes_tabs.widget(0).sizeHint().height())
        except Exception:
            pass
        target_h = min(max_h, max(self._MIN_DIALOG_HEIGHT, time_axis_h + 150))
        self.resize(min(max_w, self.minimumWidth()), target_h)

    def _build_axes_tab(self) -> tuple[QWidget, QTabWidget]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        tabs = QTabWidget(w)
        x_title = self.tr("Axis X Time")
        y_left_title = self.tr("Axis Y left")
        y_right_title = self.tr("Axis Y right")
        self._tab_axis_x = self._build_tab(self._cfg_x, axis_title=x_title, show_decimals=False, is_time_axis=True)
        self._tab_axis_yl = None
        self._tab_axis_yr = None

        tabs.addTab(self._tab_axis_x, x_title)
        if self._axis_is_used("left"):
            self._tab_axis_yl = self._build_tab(self._cfg_yl, axis_title=y_left_title, show_decimals=True, is_time_axis=False)
            tabs.addTab(self._tab_axis_yl, y_left_title)
        if self._axis_is_used("right"):
            self._tab_axis_yr = self._build_tab(self._cfg_yr, axis_title=y_right_title, show_decimals=True, is_time_axis=False)
            tabs.addTab(self._tab_axis_yr, y_right_title)
        lay.addWidget(tabs, 1)

        return w, tabs

    def _axis_is_used(self, side: str) -> bool:
        try:
            left_series, right_series = self._plot._seriesByAxis()
        except Exception:
            left_series, right_series = [], []
            for series in getattr(self._plot, "series", []) or []:
                if (series.get("y_axis") or "left") == "right":
                    right_series.append(series)
                else:
                    left_series.append(series)
        return bool(right_series if side == "right" else left_series)

    def _current_auto_scale_values(self, *, is_time_axis: bool, cfg: TimeSeriesAxisSettings):
        if is_time_axis:
            state = getattr(self._plot, "_last_x_state", None) or getattr(self._plot, "_last_auto_x_state", None)
            min_key, max_key = "min_x", "max_x"
            divisions = None
            if state:
                ticks = state.get("x_tick_values") or []
                if len(ticks) >= 2:
                    divisions = len(ticks) - 1
                scale = state.get("x_scale")
                if divisions is None and scale is not None:
                    divisions = getattr(scale, "divisions", None)
        else:
            state_name = "_last_y_state_left" if cfg is self._cfg_yl else "_last_y_state_right"
            state = getattr(self._plot, state_name, None)
            min_key, max_key = "min_y", "max_y"
            divisions = state.get("num_ticks_y") if state else None

        if not state:
            return None

        try:
            axis_min = float(state[min_key])
            axis_max = float(state[max_key])
        except Exception:
            return None

        if not math.isfinite(axis_min) or not math.isfinite(axis_max) or axis_max <= axis_min:
            return None

        try:
            divisions = int(divisions)
        except Exception:
            divisions = int(getattr(cfg, "fixed_divisions", 5) or 5)
        divisions = max(1, min(30, divisions))
        return axis_min, axis_max, divisions

    def _build_curves_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        if not self._curve_cfg:
            info = QLabel(self.tr("No curves available."))
            info.setWordWrap(True)
            info.setStyleSheet("color: palette(mid);")
            lay.addWidget(info)
            return w

        def curve_magnitude(curve):
            return (curve.get("magnitude") or self._plot.y_label or self.tr("Magnitude")).strip() or self.tr("Magnitude")

        def curve_label(curve):
            return (curve.get("label") or "").strip() or self.tr("Series")

        def clamp_int(value, default, lo, hi):
            try:
                n = int(value)
            except Exception:
                n = default
            return max(lo, min(n, hi))

        def clamp_float(value, default, lo, hi):
            try:
                n = float(value)
            except Exception:
                n = default
            return max(lo, min(n, hi))

        def configure_form(form: QFormLayout) -> None:
            form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            form.setHorizontalSpacing(12)
            form.setVerticalSpacing(8)
            try:
                form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            except Exception:
                pass
            try:
                form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
            except AttributeError:
                form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        w._curve_rows = []
        w._curve_current_idx = -1
        w._curve_loading = False

        selector_grp = self._compact_group(QGroupBox(self.tr("Select curve")))
        selector_lay = QHBoxLayout(selector_grp)
        selector_lay.setContentsMargins(8, 8, 8, 8)
        selector_lay.setSpacing(10)

        combo_magnitude = QComboBox()
        combo_curve = QComboBox()
        self._limit_field_width(combo_magnitude, self._LONG_FIELD_WIDTH)
        self._limit_field_width(combo_curve, self._LONG_FIELD_WIDTH)

        magnitudes = []
        for curve in self._curve_cfg:
            magnitude = curve_magnitude(curve)
            if magnitude not in magnitudes:
                magnitudes.append(magnitude)
        for magnitude in magnitudes:
            combo_magnitude.addItem(magnitude, magnitude)

        selector_lay.addWidget(QLabel(self.tr("Magnitude:")))
        selector_lay.addWidget(combo_magnitude, 1)
        selector_lay.addWidget(QLabel(self.tr("Curve:")))
        selector_lay.addWidget(combo_curve, 1)
        lay.addWidget(selector_grp)

        title = QLabel()
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        lay.addWidget(title)

        row = {}
        ed_label = QLineEdit()
        ed_label.setClearButtonEnabled(True)
        ed_label.setMinimumHeight(26)
        self._limit_field_width(ed_label, self._LONG_FIELD_WIDTH)

        font_combo = QFontComboBox()
        font_combo.setMaxVisibleItems(8)
        self._limit_field_width(font_combo, self._FONT_FIELD_WIDTH)

        sp_font_size = QSpinBox()
        sp_font_size.setRange(6, 32)

        color = QColor("#0078d7")
        btn_color = QPushButton()
        btn_color.setMinimumHeight(28)
        self._limit_field_width(btn_color, self._FORM_FIELD_WIDTH)

        def pick_color(_checked=False):
            nc = QColorDialog.getColor(row["color"], self, self.tr("Curve color"))
            if nc.isValid():
                row["color"] = nc
                self._show_color_on_button(btn_color, nc)
                self._schedule_live_apply()

        btn_color.clicked.connect(pick_color)

        cb_style = QComboBox()
        cb_style.addItem(self.tr("Solid"), "solid")
        cb_style.addItem(self.tr("Dashed"), "dash")
        cb_style.addItem(self.tr("Dotted"), "dot")
        cb_style.addItem(self.tr("Dash-dot"), "dashdot")
        self._limit_field_width(cb_style, self._FORM_FIELD_WIDTH)

        sp_width = QDoubleSpinBox()
        sp_width.setRange(0.5, 12.0)
        sp_width.setDecimals(1)
        sp_width.setSingleStep(0.5)

        rb_normal = QRadioButton(self.tr("Normal"))
        rb_muted = QRadioButton(self.tr("Dimmed"))
        rb_highlighted = QRadioButton(self.tr("Highlighted"))
        emphasis_group = QButtonGroup(w)
        emphasis_group.addButton(rb_normal)
        emphasis_group.addButton(rb_muted)
        emphasis_group.addButton(rb_highlighted)
        emphasis_row = QWidget()
        emphasis_lay = QHBoxLayout(emphasis_row)
        emphasis_lay.setContentsMargins(0, 0, 0, 0)
        emphasis_lay.setSpacing(10)
        emphasis_lay.addWidget(rb_normal)
        emphasis_lay.addWidget(rb_muted)
        emphasis_lay.addWidget(rb_highlighted)
        emphasis_lay.addStretch(1)

        cb_marker_symbol = QComboBox()
        cb_marker_symbol.addItem(self.tr("Circle"), "circle")
        cb_marker_symbol.addItem(self.tr("Square"), "square")
        cb_marker_symbol.addItem(self.tr("Triangle"), "triangle")
        cb_marker_symbol.addItem(self.tr("Diamond"), "diamond")
        cb_marker_symbol.addItem(self.tr("Cross"), "cross")
        self._limit_field_width(cb_marker_symbol, self._FORM_FIELD_WIDTH)

        sp_marker_size = QSpinBox()
        sp_marker_size.setRange(2, 24)

        marker_color = QColor("#0078d7")
        btn_marker_color = QPushButton()
        btn_marker_color.setMinimumHeight(28)
        self._limit_field_width(btn_marker_color, self._FORM_FIELD_WIDTH)

        def pick_marker_color(_checked=False):
            nc = QColorDialog.getColor(row["marker_color"], self, self.tr("Marker color"))
            if nc.isValid():
                row["marker_color"] = nc
                self._show_color_on_button(btn_marker_color, nc)
                self._schedule_live_apply()

        btn_marker_color.clicked.connect(pick_marker_color)

        legend_grp = self._compact_group(QGroupBox(self.tr("Legend")))
        legend_form = QFormLayout(legend_grp)
        configure_form(legend_form)
        self._add_form_row(legend_form, self.tr("Name:"), ed_label)
        self._add_form_row(legend_form, self.tr("Font:"), font_combo)
        self._add_form_row(legend_form, self.tr("Size:"), sp_font_size)
        lay.addWidget(legend_grp)

        style_grp = self._compact_group(QGroupBox(self.tr("Line Style")))
        style_grp.setCheckable(True)
        style_form = QFormLayout(style_grp)
        configure_form(style_form)
        self._add_form_row(style_form, self.tr("Line:"), cb_style)
        self._add_form_row(style_form, self.tr("Color:"), btn_color)
        self._add_form_row(style_form, self.tr("Width:"), sp_width)
        style_form.addRow("", emphasis_row)
        lay.addWidget(style_grp)

        markers_grp = self._compact_group(QGroupBox(self.tr("Markers")))
        markers_grp.setCheckable(True)
        markers_form = QFormLayout(markers_grp)
        configure_form(markers_form)
        self._add_form_row(markers_form, self.tr("Symbol:"), cb_marker_symbol)
        self._add_form_row(markers_form, self.tr("Size:"), sp_marker_size)
        self._add_form_row(markers_form, self.tr("Color:"), btn_marker_color)
        lay.addWidget(markers_grp)

        row.update({
            "label": ed_label,
            "font_family": font_combo,
            "font_size": sp_font_size,
            "color": color,
            "color_btn": btn_color,
            "style": cb_style,
            "width": sp_width,
            "visible": style_grp,
            "normal": rb_normal,
            "muted": rb_muted,
            "highlighted": rb_highlighted,
            "show_markers": markers_grp,
            "marker_symbol": cb_marker_symbol,
            "marker_size": sp_marker_size,
            "marker_color": marker_color,
            "marker_color_btn": btn_marker_color,
        })
        w._curve_rows.append(row)

        def sync_marker_options():
            enabled = bool(markers_grp.isChecked())
            cb_marker_symbol.setEnabled(enabled)
            sp_marker_size.setEnabled(enabled)
            btn_marker_color.setEnabled(enabled)

        def sync_emphasis_options():
            enabled = bool(style_grp.isChecked())
            rb_normal.setEnabled(enabled)
            rb_muted.setEnabled(enabled)
            rb_highlighted.setEnabled(enabled)

        def current_emphasis_mode():
            if rb_highlighted.isChecked():
                return "highlighted"
            if rb_muted.isChecked():
                return "muted"
            return "normal"

        def apply_emphasis_mode(curve, mode):
            curve["emphasis_mode"] = mode
            if mode == "highlighted":
                curve["highlighted"] = True
                curve["muted"] = False
            elif mode == "muted":
                curve["highlighted"] = False
                curve["muted"] = True
            else:
                curve["highlighted"] = False
                curve["muted"] = False

        def store_current_curve():
            idx = int(getattr(w, "_curve_current_idx", -1))
            if idx < 0 or idx >= len(self._curve_cfg) or bool(getattr(w, "_curve_loading", False)):
                return
            curve = self._curve_cfg[idx]
            curve["label"] = ed_label.text().strip() or self.tr("Series")
            curve["legend_font_family"] = font_combo.currentFont().family()
            curve["legend_font_size"] = int(sp_font_size.value())
            curve["color"] = row["color"].name(QColor.NameFormat.HexRgb)
            try:
                curve["line_style"] = str(cb_style.currentData() or "solid")
            except Exception:
                curve["line_style"] = "solid"
            curve["line_width"] = float(sp_width.value())
            curve["visible"] = bool(style_grp.isChecked())
            apply_emphasis_mode(curve, current_emphasis_mode())
            curve["show_markers"] = bool(markers_grp.isChecked())
            try:
                curve["marker_symbol"] = str(cb_marker_symbol.currentData() or "circle")
            except Exception:
                curve["marker_symbol"] = "circle"
            curve["marker_size"] = int(sp_marker_size.value())
            curve["marker_color"] = row["marker_color"].name(QColor.NameFormat.HexRgb)

        def refresh_curve_combo(selected_idx=None):
            current_magnitude = combo_magnitude.currentData()
            combo_curve.blockSignals(True)
            combo_curve.clear()
            first_idx = None
            selected_combo_idx = 0
            for idx, curve in enumerate(self._curve_cfg):
                if curve_magnitude(curve) != current_magnitude:
                    continue
                if first_idx is None:
                    first_idx = idx
                combo_curve.addItem(curve_label(curve), idx)
                if selected_idx == idx:
                    selected_combo_idx = combo_curve.count() - 1
            if combo_curve.count() > 0:
                combo_curve.setCurrentIndex(selected_combo_idx)
            combo_curve.blockSignals(False)
            return first_idx

        def load_curve(idx):
            if idx is None or idx < 0 or idx >= len(self._curve_cfg):
                return
            w._curve_loading = True
            w._curve_current_idx = idx
            curve = self._curve_cfg[idx]
            magnitude = curve_magnitude(curve)
            label = curve_label(curve)
            title.setText(f"{magnitude} - {label}")

            ed_label.setText(label)
            fam = (curve.get("legend_font_family") or "").strip()
            font_combo.setCurrentFont(QFont(fam or FONT_FAMILY))
            sp_font_size.setValue(clamp_int(curve.get("legend_font_size") or 8, 8, 6, 32))

            line_color = QColor(curve.get("color") or "#0078d7")
            if not line_color.isValid():
                line_color = QColor("#0078d7")
            row["color"] = line_color
            self._show_color_on_button(btn_color, line_color)

            idx_style = cb_style.findData((curve.get("line_style") or "solid").strip())
            cb_style.setCurrentIndex(idx_style if idx_style >= 0 else 0)
            sp_width.setValue(clamp_float(curve.get("line_width") or 2.0, 2.0, 0.5, 12.0))
            style_grp.setChecked(bool(curve.get("visible", True)))
            emphasis_mode = str(curve.get("emphasis_mode") or "normal").strip()
            if emphasis_mode == "highlighted":
                rb_highlighted.setChecked(True)
            elif emphasis_mode == "muted":
                rb_muted.setChecked(True)
            else:
                rb_normal.setChecked(True)
            sync_emphasis_options()

            markers_grp.setChecked(bool(curve.get("show_markers", False)))
            idx_marker_symbol = cb_marker_symbol.findData((curve.get("marker_symbol") or "circle").strip())
            cb_marker_symbol.setCurrentIndex(idx_marker_symbol if idx_marker_symbol >= 0 else 0)
            sp_marker_size.setValue(clamp_int(curve.get("marker_size") or 6, 6, 2, 24))
            marker_color_raw = curve.get("marker_color") or curve.get("color") or "#0078d7"
            marker_qcolor = QColor(marker_color_raw)
            if not marker_qcolor.isValid():
                marker_qcolor = QColor("#0078d7")
            row["marker_color"] = marker_qcolor
            self._show_color_on_button(btn_marker_color, marker_qcolor)
            sync_marker_options()
            w._curve_loading = False

        def select_curve_from_combo():
            store_current_curve()
            idx = combo_curve.currentData()
            if idx is not None:
                load_curve(int(idx))

        def select_magnitude():
            store_current_curve()
            first_idx = refresh_curve_combo()
            if first_idx is not None:
                load_curve(int(combo_curve.currentData()))

        def update_current_label(text):
            if bool(getattr(w, "_curve_loading", False)):
                return
            idx = int(getattr(w, "_curve_current_idx", -1))
            if idx < 0 or idx >= len(self._curve_cfg):
                return
            label = text.strip() or self.tr("Series")
            self._curve_cfg[idx]["label"] = label
            title.setText(f"{curve_magnitude(self._curve_cfg[idx])} - {label}")
            combo_idx = combo_curve.findData(idx)
            if combo_idx >= 0:
                combo_curve.setItemText(combo_idx, label)

        combo_magnitude.currentIndexChanged.connect(lambda _i: select_magnitude())
        combo_curve.currentIndexChanged.connect(lambda _i: select_curve_from_combo())
        ed_label.textChanged.connect(update_current_label)
        markers_grp.toggled.connect(lambda _checked: sync_marker_options())
        style_grp.toggled.connect(lambda _checked: sync_emphasis_options())
        w._curve_store_current = store_current_curve

        refresh_curve_combo()
        if combo_curve.count() > 0:
            load_curve(int(combo_curve.currentData()))

        return w

    def _build_general_tab(self, cfg: TimeSeriesGeneralSettings) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        default_cfg = TimeSeriesGeneralSettings()

        def make_color_picker(current_raw: str, current_color: QColor, default_color: QColor, title: str):
            picked = QColor(current_color)
            if not picked.isValid():
                picked = QColor(default_color)

            btn = QPushButton()
            chk_default = QCheckBox(self.tr("Use default"))
            chk_default.setChecked(not (current_raw or "").strip())
            row = QWidget()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)
            row_lay.addWidget(btn, 1)
            row_lay.addWidget(chk_default)
            row_lay.addStretch(1)

            def refresh():
                if chk_default.isChecked():
                    self._show_color_on_button(btn, default_color)
                else:
                    self._show_color_on_button(btn, picked)

            def pick_color():
                nonlocal picked
                nc = QColorDialog.getColor(picked, self, title)
                if nc.isValid():
                    picked = nc
                    chk_default.setChecked(False)
                    refresh()
                    self._schedule_live_apply()

            btn.clicked.connect(pick_color)

            def on_default_toggled(_checked):
                refresh()
                self._schedule_live_apply()

            chk_default.toggled.connect(on_default_toggled)
            refresh()

            def value():
                return "" if chk_default.isChecked() else picked.name(QColor.NameFormat.HexRgb)

            return row, value

        title_grp = self._compact_group(QGroupBox(self.tr("Plot title")))
        title_lay = QVBoxLayout(title_grp)
        ed_title = QLineEdit()
        ed_title.setText((cfg.title or "").strip())
        ed_title.setPlaceholderText(self.tr("Leave empty to use the default title"))
        ed_title.setClearButtonEnabled(True)
        ed_title.setMinimumHeight(26)
        self._limit_field_width(ed_title, self._LONG_FIELD_WIDTH)
        title_lay.addWidget(ed_title)
        title_style_row, title_font_combo, title_size_spin = self._build_text_style_row(
            font_family=getattr(cfg, "title_font_family", ""),
            font_size=getattr(cfg, "title_font_size", 10),
            color=cfg.title_qcolor(),
            color_title=self.tr("Plot title color"),
            on_changed=self._schedule_live_apply,
        )
        title_lay.addWidget(title_style_row)
        lay.addWidget(title_grp)

        colors_grp = self._compact_group(QGroupBox(self.tr("Colors")))
        colors_form = QFormLayout(colors_grp)
        colors_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        colors_form.setHorizontalSpacing(12)
        colors_form.setVerticalSpacing(8)
        try:
            colors_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass

        widget_bg_row, widget_bg_value = make_color_picker(
            cfg.widget_bg_hex,
            cfg.widget_bg_qcolor(),
            default_cfg.widget_bg_qcolor(),
            self.tr("Widget background"),
        )
        self._add_form_row(colors_form, self.tr("Widget background:"), widget_bg_row)

        plot_bg_row, plot_bg_value = make_color_picker(
            cfg.plot_bg_hex,
            cfg.plot_bg_qcolor(),
            default_cfg.plot_bg_qcolor(),
            self.tr("Plot background"),
        )
        self._add_form_row(colors_form, self.tr("Plot background:"), plot_bg_row)
        lay.addWidget(colors_grp)

        frame_grp = self._compact_group(QGroupBox(self.tr("Frame")))
        frame_form = QFormLayout(frame_grp)
        frame_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        frame_form.setHorizontalSpacing(12)
        frame_form.setVerticalSpacing(8)
        try:
            frame_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass

        frame_color_row, frame_color_value = make_color_picker(
            cfg.frame_color_hex,
            cfg.frame_qcolor(),
            default_cfg.frame_qcolor(),
            self.tr("Frame color"),
        )
        sp_w = QSpinBox()
        sp_w.setRange(0, 6)
        sp_w.setSpecialValueText(self.tr("Default"))
        sp_w.setValue(max(0, min(int(cfg.frame_width or 0), 6)))
        self._add_form_row(frame_form, self.tr("Color:"), frame_color_row)
        self._add_form_row(frame_form, self.tr("Width:"), sp_w)
        lay.addWidget(frame_grp)

        w._gen_title = ed_title
        w._gen_widget_bg_value = widget_bg_value
        w._gen_plot_bg_value = plot_bg_value
        w._gen_frame_color_value = frame_color_value
        w._gen_frame_w = sp_w
        w._gen_title_font_combo = title_font_combo
        w._gen_title_size = title_size_spin
        w._gen_title_style_row = title_style_row
        return w

    def _build_legend_tab(self, cfg: TimeSeriesGeneralSettings) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)
        default_cfg = TimeSeriesGeneralSettings()

        def make_color_picker(current_raw: str, current_color: QColor, default_color: QColor, title: str):
            picked = QColor(current_color)
            if not picked.isValid():
                picked = QColor(default_color)

            btn = QPushButton()
            chk_default = QCheckBox(self.tr("Use default"))
            chk_default.setChecked(not (current_raw or "").strip())
            row = QWidget()
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)
            row_lay.addWidget(btn, 1)
            row_lay.addWidget(chk_default)
            row_lay.addStretch(1)

            def refresh():
                if chk_default.isChecked():
                    self._show_color_on_button(btn, default_color)
                else:
                    self._show_color_on_button(btn, picked)

            def pick_color():
                nonlocal picked
                nc = QColorDialog.getColor(picked, self, title)
                if nc.isValid():
                    picked = nc
                    chk_default.setChecked(False)
                    refresh()
                    self._schedule_live_apply()

            btn.clicked.connect(pick_color)

            def on_default_toggled(_checked):
                refresh()
                self._schedule_live_apply()

            chk_default.toggled.connect(on_default_toggled)
            refresh()

            def value():
                return "" if chk_default.isChecked() else picked.name(QColor.NameFormat.HexRgb)

            return row, value

        legend_grp = self._compact_group(QGroupBox(self.tr("Legend")))
        legend_form = QFormLayout(legend_grp)
        legend_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        legend_form.setHorizontalSpacing(12)
        legend_form.setVerticalSpacing(8)
        try:
            legend_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass

        cb_pos = QComboBox()
        cb_pos.addItem(self.tr("Right (outside)"), "right")
        cb_pos.addItem(self.tr("Left (outside)"), "left")
        cb_pos.addItem(self.tr("Top (outside)"), "top")
        cb_pos.addItem(self.tr("Bottom (outside)"), "bottom")
        cur_pos = (getattr(cfg, "legend_position", "") or "right").strip()
        idx_pos = cb_pos.findData(cur_pos)
        cb_pos.setCurrentIndex(idx_pos if idx_pos >= 0 else 0)
        self._limit_field_width(cb_pos, self._FORM_FIELD_WIDTH)

        chk_frame = QCheckBox(self.tr("Draw frame"))
        chk_frame.setChecked(bool(getattr(cfg, "legend_show_frame", False)))
        chk_bg = QCheckBox(self.tr("Fill background"))
        chk_bg.setChecked(bool(getattr(cfg, "legend_show_background", False)))
        bg_color_row, bg_color_value = make_color_picker(
            getattr(cfg, "legend_bg_hex", ""),
            cfg.legend_bg_qcolor(),
            default_cfg.legend_bg_qcolor(),
            self.tr("Legend background"),
        )
        sp_sym = QSpinBox()
        sp_sym.setRange(6, 24)
        sp_sym.setValue(max(6, min(int(getattr(cfg, "legend_symbol_size", 12) or 12), 24)))

        self._add_form_row(legend_form, self.tr("Position:"), cb_pos)
        self._add_form_row(legend_form, self.tr("Symbol size:"), sp_sym)
        legend_form.addRow("", chk_bg)
        self._add_form_row(legend_form, self.tr("Background color:"), bg_color_row)
        bg_color_label = legend_form.labelForField(bg_color_row)

        def sync_legend_bg_controls(checked: bool) -> None:
            bg_color_row.setEnabled(checked)
            if bg_color_label is not None:
                bg_color_label.setEnabled(checked)

        sync_legend_bg_controls(chk_bg.isChecked())
        chk_bg.toggled.connect(sync_legend_bg_controls)
        legend_form.addRow("", chk_frame)
        lay.addWidget(legend_grp)

        w._legend_pos = cb_pos
        w._legend_frame = chk_frame
        w._legend_bg = chk_bg
        w._legend_bg_color_value = bg_color_value
        w._legend_sym = sp_sym
        return w

    def _build_tab(self, cfg: TimeSeriesAxisSettings, *, axis_title: str, show_decimals: bool, is_time_axis: bool) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel(axis_title)
        title_font = QFont(title.font())
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addWidget(title)

        title_grp = self._compact_group(QGroupBox(self.tr("Title")))
        title_lay = QVBoxLayout(title_grp)
        title_edit = QLineEdit()
        title_edit.setText(cfg.title)
        title_edit.setPlaceholderText(self.tr("Leave empty for default label"))
        title_edit.setMinimumHeight(26)
        title_edit.setClearButtonEnabled(True)
        self._limit_field_width(title_edit, self._LONG_FIELD_WIDTH)
        title_lay.addWidget(title_edit)
        title_style_row, title_font_combo, title_size_spin = self._build_text_style_row(
            font_family=getattr(cfg, "title_font_family", ""),
            font_size=getattr(cfg, "title_font_size", 10),
            color=cfg.title_qcolor(),
            color_title=self.tr("Axis title color"),
            on_changed=self._schedule_live_apply,
        )
        title_lay.addWidget(title_style_row)
        lay.addWidget(title_grp)

        scale_group = self._compact_group(QGroupBox(self.tr("Scale")))
        scale_form = QFormLayout(scale_group)
        scale_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        scale_form.setHorizontalSpacing(12)
        scale_form.setVerticalSpacing(8)
        try:
            scale_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass
        try:
            scale_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        except AttributeError:
            scale_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        combo_scale = QComboBox()
        combo_scale.addItem(self.tr("Automatic"), True)
        combo_scale.addItem(self.tr("Fixed (min, max, divisions)"), False)
        combo_scale.setCurrentIndex(0 if cfg.auto_scale else 1)
        combo_scale.setMinimumWidth(180)
        self._limit_field_width(combo_scale, self._FORM_FIELD_WIDTH)
        self._add_form_row(scale_form, self.tr("Mode:"), combo_scale)

        sp_min = QDoubleSpinBox()
        sp_min.setRange(-1e12, 1e12)
        sp_min.setValue(float(cfg.fixed_min))
        sp_min.setMinimumWidth(140)

        sp_max = QDoubleSpinBox()
        sp_max.setRange(-1e12, 1e12)
        sp_max.setValue(float(cfg.fixed_max))
        sp_max.setMinimumWidth(140)

        sp_div = QSpinBox()
        sp_div.setRange(1, 30)
        sp_div.setValue(int(cfg.fixed_divisions))
        sp_div.setMinimumWidth(100)

        self._add_form_row(scale_form, self.tr("Minimum:"), sp_min)
        self._add_form_row(scale_form, self.tr("Maximum:"), sp_max)
        self._add_form_row(scale_form, self.tr("Divisions:"), sp_div)
        lay.addWidget(scale_group)

        grid_grp = self._compact_group(QGroupBox(self.tr("Grid")))
        grid_lay = QVBoxLayout(grid_grp)
        chk_grid = QCheckBox(self.tr("Show grid lines for this axis"))
        chk_grid.setChecked(cfg.show_grid)
        grid_lay.addWidget(chk_grid)
        lay.addWidget(grid_grp)

        tick_grp = self._compact_group(QGroupBox(self.tr("Tick labels")))
        tick_form = QFormLayout(tick_grp)
        tick_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_form.setHorizontalSpacing(12)
        tick_form.setVerticalSpacing(8)
        try:
            tick_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        except Exception:
            pass
        try:
            tick_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        except AttributeError:
            tick_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        font_combo = QFontComboBox()
        font_combo.setMaxVisibleItems(8)
        self._limit_field_width(font_combo, self._FONT_FIELD_WIDTH)
        fam = (cfg.tick_font_family or "").strip()
        if fam:
            font_combo.setCurrentFont(QFont(fam))

        sp_size = QSpinBox()
        sp_size.setRange(5, 48)
        sp_size.setValue(int(cfg.tick_font_size))
        sp_size.setMinimumWidth(80)

        self._add_form_row(tick_form, self.tr("Font:"), font_combo)
        self._add_form_row(tick_form, self.tr("Size:"), sp_size)

        chk_tick_marks = QCheckBox(self.tr("Show tick marks outside the axis"))
        chk_tick_marks.setChecked(bool(getattr(cfg, "show_tick_marks", False)))
        tick_form.addRow("", chk_tick_marks)

        w._picked_color = QColor(cfg.tick_qcolor())
        btn_color = QPushButton()

        def refresh_color_btn():
            self._show_color_on_button(btn_color, w._picked_color)

        refresh_color_btn()

        def pick_color():
            nc = QColorDialog.getColor(w._picked_color, self, self.tr("Tick color"))
            if nc.isValid():
                w._picked_color = nc
                refresh_color_btn()
                self._schedule_live_apply()

        btn_color.clicked.connect(pick_color)
        btn_color.setMinimumHeight(28)
        self._add_form_row(tick_form, self.tr("Color:"), btn_color)
        lay.addWidget(tick_grp)

        sp_dec = QSpinBox()
        sp_dec.setRange(-1, 10)
        sp_dec.setSpecialValueText(self.tr("Auto"))
        sp_dec.setValue(-1 if cfg.decimal_places < 0 else int(cfg.decimal_places))
        if show_decimals:
            dec_grp = self._compact_group(QGroupBox(self.tr("Numeric format")))
            dec_lay = QVBoxLayout(dec_grp)
            dec_lay.addWidget(QLabel(self.tr("Decimal places for Y tick values:")))
            dec_lay.addWidget(sp_dec)
            lay.addWidget(dec_grp)
        else:
            sp_dec.hide()

        if is_time_axis:
            time_grp = self._compact_group(QGroupBox(self.tr("Time format")))
            time_form = QFormLayout(time_grp)
            time_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            time_form.setHorizontalSpacing(12)
            time_form.setVerticalSpacing(8)
            try:
                time_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
            except Exception:
                pass

            combo_hour = QComboBox()
            combo_hour.addItem(self.tr("hh"), "h")
            combo_hour.addItem(self.tr("hh:mm"), "hm")
            cur_h = (getattr(cfg, "x_hour_format", "") or "hm").strip()
            idx_h = combo_hour.findData(cur_h)
            combo_hour.setCurrentIndex(idx_h if idx_h >= 0 else 0)
            self._limit_field_width(combo_hour, self._FORM_FIELD_WIDTH)

            combo_days = QComboBox()
            combo_days.addItem(self.tr("Days as 1d, 2d…"), "split_days")
            combo_days.addItem(self.tr("Accumulate days into hours (>24)"), "total_hours")
            cur_d = (getattr(cfg, "x_day_format", "") or "split_days").strip()
            idx_d = combo_days.findData(cur_d)
            combo_days.setCurrentIndex(idx_d if idx_d >= 0 else 0)
            self._limit_field_width(combo_days, self._FORM_FIELD_WIDTH)

            self._add_form_row(time_form, self.tr("Hour:"), combo_hour)
            self._add_form_row(time_form, self.tr("Days:"), combo_days)
            lay.addWidget(time_grp)

        def sync_fixed_enabled():
            auto = combo_scale.currentIndex() == 0
            sp_min.setEnabled(not auto)
            sp_max.setEnabled(not auto)
            sp_div.setEnabled(not auto)

        def apply_auto_scale_defaults():
            vals = self._current_auto_scale_values(is_time_axis=is_time_axis, cfg=cfg)
            if vals is None:
                return
            axis_min, axis_max, divisions = vals
            sp_min.setValue(float(axis_min))
            sp_max.setValue(float(axis_max))
            sp_div.setValue(int(divisions))

        if cfg.auto_scale:
            apply_auto_scale_defaults()

        def on_scale_changed(_i):
            if combo_scale.currentIndex() != 0:
                apply_auto_scale_defaults()
            sync_fixed_enabled()

        combo_scale.currentIndexChanged.connect(on_scale_changed)
        sync_fixed_enabled()

        w._title_edit = title_edit
        w._title_font_combo = title_font_combo
        w._title_size = title_size_spin
        w._title_style_row = title_style_row
        w._combo_scale = combo_scale
        w._sp_min = sp_min
        w._sp_max = sp_max
        w._sp_div = sp_div
        w._chk_grid = chk_grid
        w._chk_tick_marks = chk_tick_marks
        w._sp_size = sp_size
        w._font_combo = font_combo
        w._sp_dec = sp_dec
        w._is_time_axis = bool(is_time_axis)
        if is_time_axis:
            w._combo_hour = combo_hour
            w._combo_days = combo_days
        return w

    def _read_tab(self, tab: QWidget, cfg: TimeSeriesAxisSettings) -> None:
        cfg.title = tab._title_edit.text().strip()
        cfg.title_font_family = tab._title_font_combo.currentFont().family()
        cfg.title_font_size = int(tab._title_size.value())
        title_color = getattr(tab._title_style_row, "_text_style_color", QColor("#000000"))
        cfg.title_color_hex = title_color.name(QColor.NameFormat.HexRgb) if isinstance(title_color, QColor) else "#000000"
        cfg.auto_scale = tab._combo_scale.currentIndex() == 0
        cfg.fixed_min = float(tab._sp_min.value())
        cfg.fixed_max = float(tab._sp_max.value())
        cfg.fixed_divisions = int(tab._sp_div.value())
        cfg.show_grid = tab._chk_grid.isChecked()
        cfg.show_tick_marks = bool(tab._chk_tick_marks.isChecked())
        cfg.tick_font_size = int(tab._sp_size.value())
        cfg.tick_font_family = tab._font_combo.currentFont().family()
        cfg.tick_color_hex = tab._picked_color.name(QColor.NameFormat.HexRgb)
        if tab._sp_dec.isVisible():
            dv = int(tab._sp_dec.value())
            cfg.decimal_places = -1 if dv < 0 else dv
        else:
            cfg.decimal_places = -1

        if getattr(tab, "_is_time_axis", False):
            try:
                cfg.x_hour_format = str(tab._combo_hour.currentData() or "hm")
            except Exception:
                cfg.x_hour_format = "hm"
            try:
                cfg.x_day_format = str(tab._combo_days.currentData() or "split_days")
            except Exception:
                cfg.x_day_format = "split_days"

    def _apply_options(self) -> None:
        gen_tab = self._tab_general
        legend_tab = self._tab_legend
        self._cfg_gen.title = gen_tab._gen_title.text().strip()
        self._cfg_gen.title_font_family = gen_tab._gen_title_font_combo.currentFont().family()
        self._cfg_gen.title_font_size = int(gen_tab._gen_title_size.value())
        gen_title_color = getattr(gen_tab._gen_title_style_row, "_text_style_color", QColor("#000000"))
        self._cfg_gen.title_color_hex = gen_title_color.name(QColor.NameFormat.HexRgb) if isinstance(gen_title_color, QColor) else "#000000"
        self._cfg_gen.widget_bg_hex = gen_tab._gen_widget_bg_value()
        self._cfg_gen.plot_bg_hex = gen_tab._gen_plot_bg_value()
        self._cfg_gen.frame_color_hex = gen_tab._gen_frame_color_value()
        self._cfg_gen.frame_width = int(gen_tab._gen_frame_w.value())
        try:
            self._cfg_gen.legend_position = str(legend_tab._legend_pos.currentData() or "right")
        except Exception:
            self._cfg_gen.legend_position = "right"
        self._cfg_gen.legend_show_frame = bool(legend_tab._legend_frame.isChecked())
        self._cfg_gen.legend_show_background = bool(legend_tab._legend_bg.isChecked())
        self._cfg_gen.legend_bg_hex = legend_tab._legend_bg_color_value()
        self._cfg_gen.legend_symbol_size = int(legend_tab._legend_sym.value())

        self._read_tab(self._tab_axis_x, self._cfg_x)
        if self._tab_axis_yl is not None:
            self._read_tab(self._tab_axis_yl, self._cfg_yl)
        if self._tab_axis_yr is not None:
            self._read_tab(self._tab_axis_yr, self._cfg_yr)
        self._read_curves_tab(self._tab_curves)
        if not self._cfg_x.auto_scale:
            self._plot._view_x_min = None
            self._plot._view_x_max = None
        self._plot._axis_cfg_x = self._cfg_x
        self._plot._axis_cfg_y_left = self._cfg_yl
        self._plot._axis_cfg_y_right = self._cfg_yr
        self._plot._general_cfg = self._cfg_gen
        self._plot._updateMinimumWidthForTitle()
        self._plot.update()
        self._dirty_applied = True
        self._ui_dirty = False

    def _on_accept(self) -> None:
        self._apply_options()
        self.accept()

    def _read_curves_tab(self, tab: QWidget) -> None:
        store_current = getattr(tab, "_curve_store_current", None)
        if callable(store_current):
            store_current()
        rows = getattr(tab, "_curve_rows", []) or []
        if not rows:
            return
        series = getattr(self._plot, "series", []) or []
        for idx, curve in enumerate(self._curve_cfg):
            if idx >= len(series):
                break
            s = series[idx]
            s["label"] = (curve.get("label") or "").strip() or self.tr("Series")
            s["legend_font_family"] = curve.get("legend_font_family") or ""
            s["legend_font_size"] = int(curve.get("legend_font_size") or 8)
            s["color"] = curve.get("color") or "#0078d7"
            s["line_style"] = curve.get("line_style") or "solid"
            s["line_width"] = float(curve.get("line_width") or 2.0)
            s["visible"] = bool(curve.get("visible", True))
            emphasis_mode = str(curve.get("emphasis_mode") or "normal").strip()
            s["emphasis_mode"] = emphasis_mode if emphasis_mode in ("muted", "highlighted") else "normal"
            s["show_markers"] = bool(curve.get("show_markers", False))
            s["marker_symbol"] = curve.get("marker_symbol") or "circle"
            s["marker_size"] = int(curve.get("marker_size") or 6)
            s["marker_color"] = curve.get("marker_color") or curve.get("color") or "#0078d7"
            s["show_point_values"] = bool(curve.get("show_point_values", False))
            s["muted"] = bool(curve.get("muted", False))
            s["highlighted"] = bool(curve.get("highlighted", False))
            if s["highlighted"]:
                s["muted"] = False
        try:
            self._plot._emitSeriesEmphasisChanged()
        except Exception:
            pass
