# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
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
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .timeseries_axis_settings import TimeSeriesAxisSettings, TimeSeriesGeneralSettings, clone_axis_settings, clone_general_settings


class TimeSeriesAxisOptionsDialog(QDialog):
    _MIN_DIALOG_WIDTH = 560
    _MIN_DIALOG_HEIGHT = 480
    _LONG_FIELD_WIDTH = 360
    _FORM_FIELD_WIDTH = 280
    _FONT_FIELD_WIDTH = 260

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
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._tabs = tabs
        self._axes_tabs = axes_tabs
        self._tab_general = tab_general
        self._tab_legend = tab_legend
        self._tab_curves = tab_curves
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

    def _add_form_row(self, form: QFormLayout, label_text: str, field: QWidget) -> None:
        form.addRow(self._make_form_label(label_text), field)

    def _compact_group(self, grp: QGroupBox) -> QGroupBox:
        grp.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        return grp

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
        tabs.addTab(self._build_tab(self._cfg_x, show_decimals=False, is_time_axis=True), self.tr("Time (X)"))
        tabs.addTab(self._build_tab(self._cfg_yl, show_decimals=True, is_time_axis=False), self.tr("Y left"))
        tabs.addTab(self._build_tab(self._cfg_yr, show_decimals=True, is_time_axis=False), self.tr("Y right"))
        lay.addWidget(tabs, 1)

        return w, tabs

    def _build_curves_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        w._curve_rows = []
        if not self._curve_cfg:
            info = QLabel(self.tr("No curves available."))
            info.setWordWrap(True)
            info.setStyleSheet("color: palette(mid);")
            lay.addWidget(info)
            return w

        for idx, curve in enumerate(self._curve_cfg):
            label = (curve.get("label") or "").strip() or self.tr("Series")
            grp = self._compact_group(QGroupBox(label))
            form = QFormLayout(grp)
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

            ed_label = QLineEdit()
            ed_label.setText(label)
            ed_label.setClearButtonEnabled(True)
            ed_label.setMinimumHeight(26)
            self._limit_field_width(ed_label, self._LONG_FIELD_WIDTH)

            font_combo = QFontComboBox()
            font_combo.setMaxVisibleItems(8)
            self._limit_field_width(font_combo, self._FONT_FIELD_WIDTH)
            fam = (curve.get("legend_font_family") or "").strip()
            if fam:
                font_combo.setCurrentFont(QFont(fam))

            sp_font_size = QSpinBox()
            sp_font_size.setRange(6, 32)
            sp_font_size.setValue(max(6, min(int(curve.get("legend_font_size") or 8), 32)))

            picked = QColor(curve.get("color") or "#0078d7")
            if not picked.isValid():
                picked = QColor("#0078d7")
            btn_color = QPushButton()

            def refresh_color_button(btn=btn_color, color=picked):
                btn.setText(color.name(QColor.NameFormat.HexRgb))

            refresh_color_button()
            btn_color.setMinimumHeight(28)
            self._limit_field_width(btn_color, self._FORM_FIELD_WIDTH)

            def pick_color(_checked=False, btn=btn_color, row_idx=idx):
                current = w._curve_rows[row_idx]["color"]
                nc = QColorDialog.getColor(current, self, self.tr("Curve color"))
                if nc.isValid():
                    w._curve_rows[row_idx]["color"] = nc
                    btn.setText(nc.name(QColor.NameFormat.HexRgb))

            btn_color.clicked.connect(pick_color)

            cb_style = QComboBox()
            cb_style.addItem(self.tr("Solid"), "solid")
            cb_style.addItem(self.tr("Dashed"), "dash")
            cb_style.addItem(self.tr("Dotted"), "dot")
            cb_style.addItem(self.tr("Dash-dot"), "dashdot")
            cur_style = (curve.get("line_style") or "solid").strip()
            idx_style = cb_style.findData(cur_style)
            cb_style.setCurrentIndex(idx_style if idx_style >= 0 else 0)
            self._limit_field_width(cb_style, self._FORM_FIELD_WIDTH)

            sp_width = QDoubleSpinBox()
            sp_width.setRange(0.5, 12.0)
            sp_width.setDecimals(1)
            sp_width.setSingleStep(0.5)
            sp_width.setValue(max(0.5, min(float(curve.get("line_width") or 2.0), 12.0)))

            chk_markers = QCheckBox(self.tr("Show step point markers"))
            chk_markers.setChecked(bool(curve.get("show_markers", False)))

            cb_marker_symbol = QComboBox()
            cb_marker_symbol.addItem(self.tr("Circle"), "circle")
            cb_marker_symbol.addItem(self.tr("Square"), "square")
            cb_marker_symbol.addItem(self.tr("Triangle"), "triangle")
            cb_marker_symbol.addItem(self.tr("Diamond"), "diamond")
            cb_marker_symbol.addItem(self.tr("Cross"), "cross")
            cur_marker_symbol = (curve.get("marker_symbol") or "circle").strip()
            idx_marker_symbol = cb_marker_symbol.findData(cur_marker_symbol)
            cb_marker_symbol.setCurrentIndex(idx_marker_symbol if idx_marker_symbol >= 0 else 0)
            self._limit_field_width(cb_marker_symbol, self._FORM_FIELD_WIDTH)

            sp_marker_size = QSpinBox()
            sp_marker_size.setRange(2, 24)
            sp_marker_size.setValue(max(2, min(int(curve.get("marker_size") or 6), 24)))

            marker_color_raw = curve.get("marker_color") or curve.get("color") or "#0078d7"
            picked_marker = QColor(marker_color_raw)
            if not picked_marker.isValid():
                picked_marker = QColor("#0078d7")
            btn_marker_color = QPushButton()

            def refresh_marker_color_button(btn=btn_marker_color, color=picked_marker):
                btn.setText(color.name(QColor.NameFormat.HexRgb))

            refresh_marker_color_button()
            btn_marker_color.setMinimumHeight(28)
            self._limit_field_width(btn_marker_color, self._FORM_FIELD_WIDTH)

            def pick_marker_color(_checked=False, btn=btn_marker_color, row_idx=idx):
                current = w._curve_rows[row_idx]["marker_color"]
                nc = QColorDialog.getColor(current, self, self.tr("Marker color"))
                if nc.isValid():
                    w._curve_rows[row_idx]["marker_color"] = nc
                    btn.setText(nc.name(QColor.NameFormat.HexRgb))

            btn_marker_color.clicked.connect(pick_marker_color)

            chk_point_values = QCheckBox(self.tr("Show step point values as text"))
            chk_point_values.setChecked(bool(curve.get("show_point_values", False)))

            chk_visible = QCheckBox(self.tr("Visible"))
            chk_visible.setChecked(bool(curve.get("visible", True)))
            chk_muted = QCheckBox(self.tr("Dimmed"))
            chk_muted.setChecked(bool(curve.get("muted", False)))
            chk_highlighted = QCheckBox(self.tr("Highlighted"))
            chk_highlighted.setChecked(bool(curve.get("highlighted", False)))

            def sync_emphasis(row_idx=idx):
                row = w._curve_rows[row_idx]
                if row["highlighted"].isChecked() and row["muted"].isChecked():
                    row["muted"].setChecked(False)

            def sync_muted(row_idx=idx):
                row = w._curve_rows[row_idx]
                if row["muted"].isChecked() and row["highlighted"].isChecked():
                    row["highlighted"].setChecked(False)

            chk_highlighted.toggled.connect(lambda _checked, row_idx=idx: sync_emphasis(row_idx))
            chk_muted.toggled.connect(lambda _checked, row_idx=idx: sync_muted(row_idx))

            def sync_marker_options(row_idx=idx):
                row = w._curve_rows[row_idx]
                enabled = bool(row["show_markers"].isChecked())
                row["marker_symbol"].setEnabled(enabled)
                row["marker_size"].setEnabled(enabled)
                row["marker_color_btn"].setEnabled(enabled)

            chk_markers.toggled.connect(lambda _checked, row_idx=idx: sync_marker_options(row_idx))

            self._add_form_row(form, self.tr("Legend name:"), ed_label)
            self._add_form_row(form, self.tr("Legend font:"), font_combo)
            self._add_form_row(form, self.tr("Legend font size:"), sp_font_size)
            self._add_form_row(form, self.tr("Color:"), btn_color)
            self._add_form_row(form, self.tr("Line style:"), cb_style)
            self._add_form_row(form, self.tr("Line width:"), sp_width)
            form.addRow("", chk_markers)
            self._add_form_row(form, self.tr("Marker symbol:"), cb_marker_symbol)
            self._add_form_row(form, self.tr("Marker size:"), sp_marker_size)
            self._add_form_row(form, self.tr("Marker color:"), btn_marker_color)
            form.addRow("", chk_point_values)
            form.addRow("", chk_visible)
            form.addRow("", chk_muted)
            form.addRow("", chk_highlighted)
            lay.addWidget(grp)

            w._curve_rows.append({
                "label": ed_label,
                "font_family": font_combo,
                "font_size": sp_font_size,
                "color": picked,
                "style": cb_style,
                "width": sp_width,
                "show_markers": chk_markers,
                "marker_symbol": cb_marker_symbol,
                "marker_size": sp_marker_size,
                "marker_color": picked_marker,
                "marker_color_btn": btn_marker_color,
                "show_point_values": chk_point_values,
                "visible": chk_visible,
                "muted": chk_muted,
                "highlighted": chk_highlighted,
            })
            sync_marker_options(idx)

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

            def refresh():
                if chk_default.isChecked():
                    btn.setText(f"{self.tr('Default')}: {default_color.name(QColor.NameFormat.HexRgb)}")
                else:
                    btn.setText(picked.name(QColor.NameFormat.HexRgb))

            def pick_color():
                nonlocal picked
                nc = QColorDialog.getColor(picked, self, title)
                if nc.isValid():
                    picked = nc
                    chk_default.setChecked(False)
                    refresh()

            btn.clicked.connect(pick_color)
            chk_default.toggled.connect(lambda _checked: refresh())
            refresh()

            def value():
                return "" if chk_default.isChecked() else picked.name(QColor.NameFormat.HexRgb)

            return btn, chk_default, value

        title_grp = self._compact_group(QGroupBox(self.tr("Plot title")))
        title_lay = QVBoxLayout(title_grp)
        ed_title = QLineEdit()
        ed_title.setText((cfg.title or "").strip())
        ed_title.setPlaceholderText(self.tr("Leave empty to use the default title"))
        ed_title.setClearButtonEnabled(True)
        ed_title.setMinimumHeight(26)
        self._limit_field_width(ed_title, self._LONG_FIELD_WIDTH)
        title_lay.addWidget(ed_title)
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

        btn_widget_bg, chk_widget_bg_default, widget_bg_value = make_color_picker(
            cfg.widget_bg_hex,
            cfg.widget_bg_qcolor(),
            default_cfg.widget_bg_qcolor(),
            self.tr("Widget background"),
        )
        self._add_form_row(colors_form, self.tr("Widget background:"), btn_widget_bg)
        colors_form.addRow("", chk_widget_bg_default)

        btn_plot_bg, chk_plot_bg_default, plot_bg_value = make_color_picker(
            cfg.plot_bg_hex,
            cfg.plot_bg_qcolor(),
            default_cfg.plot_bg_qcolor(),
            self.tr("Plot background"),
        )
        self._add_form_row(colors_form, self.tr("Plot background:"), btn_plot_bg)
        colors_form.addRow("", chk_plot_bg_default)
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

        btn_frame, chk_frame_default, frame_color_value = make_color_picker(
            cfg.frame_color_hex,
            cfg.frame_qcolor(),
            default_cfg.frame_qcolor(),
            self.tr("Frame color"),
        )
        sp_w = QSpinBox()
        sp_w.setRange(0, 6)
        sp_w.setSpecialValueText(self.tr("Default"))
        sp_w.setValue(max(0, min(int(cfg.frame_width or 0), 6)))
        self._add_form_row(frame_form, self.tr("Color:"), btn_frame)
        frame_form.addRow("", chk_frame_default)
        self._add_form_row(frame_form, self.tr("Width:"), sp_w)
        lay.addWidget(frame_grp)

        w._gen_title = ed_title
        w._gen_widget_bg_value = widget_bg_value
        w._gen_plot_bg_value = plot_bg_value
        w._gen_frame_color_value = frame_color_value
        w._gen_frame_w = sp_w
        return w

    def _build_legend_tab(self, cfg: TimeSeriesGeneralSettings) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

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
        cb_pos.addItem(self.tr("Inside — top right"), "inside_top_right")
        cb_pos.addItem(self.tr("Inside — top left"), "inside_top_left")
        cb_pos.addItem(self.tr("Inside — bottom right"), "inside_bottom_right")
        cb_pos.addItem(self.tr("Inside — bottom left"), "inside_bottom_left")
        cur_pos = (getattr(cfg, "legend_position", "") or "right").strip()
        idx_pos = cb_pos.findData(cur_pos)
        cb_pos.setCurrentIndex(idx_pos if idx_pos >= 0 else 0)
        self._limit_field_width(cb_pos, self._FORM_FIELD_WIDTH)

        chk_frame = QCheckBox(self.tr("Draw frame"))
        chk_frame.setChecked(bool(getattr(cfg, "legend_show_frame", False)))
        chk_bg = QCheckBox(self.tr("Fill background"))
        chk_bg.setChecked(bool(getattr(cfg, "legend_show_background", False)))

        sp_sym = QSpinBox()
        sp_sym.setRange(6, 24)
        sp_sym.setValue(max(6, min(int(getattr(cfg, "legend_symbol_size", 12) or 12), 24)))

        sp_cols = QSpinBox()
        sp_cols.setRange(1, 6)
        sp_cols.setValue(max(1, int(getattr(cfg, "legend_columns", 1) or 1)))

        self._add_form_row(legend_form, self.tr("Position:"), cb_pos)
        self._add_form_row(legend_form, self.tr("Columns:"), sp_cols)
        self._add_form_row(legend_form, self.tr("Symbol size:"), sp_sym)
        legend_form.addRow("", chk_bg)
        legend_form.addRow("", chk_frame)
        lay.addWidget(legend_grp)

        w._legend_pos = cb_pos
        w._legend_frame = chk_frame
        w._legend_bg = chk_bg
        w._legend_sym = sp_sym
        w._legend_cols = sp_cols
        return w

    def _build_tab(self, cfg: TimeSeriesAxisSettings, *, show_decimals: bool, is_time_axis: bool) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

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
            combo_hour.addItem(self.tr("HH:mm"), "hm")
            combo_hour.addItem(self.tr("HH:mm:ss"), "hms")
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

        title_grp = self._compact_group(QGroupBox(self.tr("Axis title")))
        title_lay = QVBoxLayout(title_grp)
        title_edit = QLineEdit()
        title_edit.setText(cfg.title)
        title_edit.setPlaceholderText(self.tr("Leave empty for default label"))
        title_edit.setMinimumHeight(26)
        title_edit.setClearButtonEnabled(True)
        self._limit_field_width(title_edit, self._LONG_FIELD_WIDTH)
        title_lay.addWidget(title_edit)
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
        sp_min.setDecimals(6)
        sp_min.setValue(float(cfg.fixed_min))
        sp_min.setMinimumWidth(140)

        sp_max = QDoubleSpinBox()
        sp_max.setRange(-1e12, 1e12)
        sp_max.setDecimals(6)
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

        sp_size = QSpinBox()
        sp_size.setRange(5, 48)
        sp_size.setValue(int(cfg.tick_font_size))
        sp_size.setMinimumWidth(80)

        font_combo = QFontComboBox()
        font_combo.setMaxVisibleItems(8)
        self._limit_field_width(font_combo, self._FONT_FIELD_WIDTH)
        fam = (cfg.tick_font_family or "").strip()
        if fam:
            font_combo.setCurrentFont(QFont(fam))

        self._add_form_row(tick_form, self.tr("Font size:"), sp_size)
        self._add_form_row(tick_form, self.tr("Font:"), font_combo)

        w._picked_color = QColor(cfg.tick_qcolor())
        btn_color = QPushButton()

        def refresh_color_btn():
            btn_color.setText(f"{self.tr('Tick color')}: {w._picked_color.name(QColor.NameFormat.HexRgb)}")

        refresh_color_btn()

        def pick_color():
            nc = QColorDialog.getColor(w._picked_color, self, self.tr("Tick color"))
            if nc.isValid():
                w._picked_color = nc
                refresh_color_btn()

        btn_color.clicked.connect(pick_color)
        btn_color.setMinimumHeight(28)
        self._add_form_row(tick_form, self.tr("Color:"), btn_color)
        lay.addWidget(tick_grp)

        dec_grp = self._compact_group(QGroupBox(self.tr("Numeric format")))
        dec_lay = QVBoxLayout(dec_grp)
        sp_dec = QSpinBox()
        sp_dec.setRange(-1, 10)
        sp_dec.setSpecialValueText(self.tr("Auto"))
        sp_dec.setValue(-1 if cfg.decimal_places < 0 else int(cfg.decimal_places))
        if show_decimals:
            dec_lay.addWidget(QLabel(self.tr("Decimal places for Y tick values (-1 = automatic).")))
            dec_lay.addWidget(sp_dec)
        else:
            sp_dec.hide()
            dec_lay.addWidget(
                QLabel(self.tr("The time axis uses clock-style labels; decimals do not apply here."))
            )
        lay.addWidget(dec_grp)

        def sync_fixed_enabled():
            auto = combo_scale.currentIndex() == 0
            sp_min.setEnabled(not auto)
            sp_max.setEnabled(not auto)
            sp_div.setEnabled(not auto)

        combo_scale.currentIndexChanged.connect(lambda _i: sync_fixed_enabled())
        sync_fixed_enabled()

        w._title_edit = title_edit
        w._combo_scale = combo_scale
        w._sp_min = sp_min
        w._sp_max = sp_max
        w._sp_div = sp_div
        w._chk_grid = chk_grid
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
        cfg.auto_scale = tab._combo_scale.currentIndex() == 0
        cfg.fixed_min = float(tab._sp_min.value())
        cfg.fixed_max = float(tab._sp_max.value())
        cfg.fixed_divisions = int(tab._sp_div.value())
        cfg.show_grid = tab._chk_grid.isChecked()
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

    def _on_accept(self) -> None:
        gen_tab = self._tab_general
        legend_tab = self._tab_legend
        self._cfg_gen.title = gen_tab._gen_title.text().strip()
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
        self._cfg_gen.legend_symbol_size = int(legend_tab._legend_sym.value())
        self._cfg_gen.legend_columns = int(legend_tab._legend_cols.value())

        self._read_tab(self._axes_tabs.widget(0), self._cfg_x)
        self._read_tab(self._axes_tabs.widget(1), self._cfg_yl)
        self._read_tab(self._axes_tabs.widget(2), self._cfg_yr)
        self._read_curves_tab(self._tab_curves)
        if not self._cfg_x.auto_scale:
            self._plot._view_x_min = None
            self._plot._view_x_max = None
        self._plot._axis_cfg_x = self._cfg_x
        self._plot._axis_cfg_y_left = self._cfg_yl
        self._plot._axis_cfg_y_right = self._cfg_yr
        self._plot._general_cfg = self._cfg_gen
        self._plot.update()
        self.accept()

    def _read_curves_tab(self, tab: QWidget) -> None:
        rows = getattr(tab, "_curve_rows", []) or []
        if not rows:
            return
        series = getattr(self._plot, "series", []) or []
        for idx, row in enumerate(rows):
            if idx >= len(series):
                break
            s = series[idx]
            s["label"] = row["label"].text().strip() or self.tr("Series")
            s["legend_font_family"] = row["font_family"].currentFont().family()
            s["legend_font_size"] = int(row["font_size"].value())
            s["color"] = row["color"].name(QColor.NameFormat.HexRgb)
            try:
                s["line_style"] = str(row["style"].currentData() or "solid")
            except Exception:
                s["line_style"] = "solid"
            s["line_width"] = float(row["width"].value())
            s["show_markers"] = bool(row["show_markers"].isChecked())
            try:
                s["marker_symbol"] = str(row["marker_symbol"].currentData() or "circle")
            except Exception:
                s["marker_symbol"] = "circle"
            s["marker_size"] = int(row["marker_size"].value())
            s["marker_color"] = row["marker_color"].name(QColor.NameFormat.HexRgb)
            s["show_point_values"] = bool(row["show_point_values"].isChecked())
            s["visible"] = bool(row["visible"].isChecked())
            s["muted"] = bool(row["muted"].isChecked())
            s["highlighted"] = bool(row["highlighted"].isChecked())
            if s["highlighted"]:
                s["muted"] = False
        try:
            self._plot._emitSeriesEmphasisChanged()
        except Exception:
            pass
