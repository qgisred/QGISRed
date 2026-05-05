# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFont, QIcon, QPixmap
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QComboBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .timeseries_axis_settings import TimeSeriesAxisSettings, TimeSeriesGeneralSettings, clone_axis_settings, clone_general_settings


def _qgisred_icon_path() -> str:
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "images", "qgisred.svg"))


class TimeSeriesAxisOptionsDialog(QDialog):
    def __init__(self, plot_widget, parent=None):
        win = parent.window() if parent is not None else None
        super().__init__(win if win is not None else parent)
        self._plot = plot_widget
        self.setWindowTitle(self.tr("QGISRed — axis options"))
        self.resize(440, 480)
        self.setMinimumWidth(400)

        ip = _qgisred_icon_path()
        if os.path.isfile(ip):
            self.setWindowIcon(QIcon(ip))

        self._cfg_x = clone_axis_settings(plot_widget._axis_cfg_x)
        self._cfg_yl = clone_axis_settings(plot_widget._axis_cfg_y_left)
        self._cfg_yr = clone_axis_settings(plot_widget._axis_cfg_y_right)
        self._cfg_gen = clone_general_settings(getattr(plot_widget, "_general_cfg", TimeSeriesGeneralSettings()))

        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        root.addWidget(self._build_header(ip))

        tabs = QTabWidget(self)
        tabs.addTab(self._build_general_tab(self._cfg_gen), self.tr("General"))

        axes_tab, axes_tabs = self._build_axes_tab()
        tabs.addTab(axes_tab, self.tr("Axes"))
        root.addWidget(tabs, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._tabs = tabs
        self._axes_tabs = axes_tabs

    def _build_axes_tab(self) -> tuple[QWidget, QTabWidget]:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        lay.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget(w)
        tabs.addTab(self._build_tab(self._cfg_x, show_decimals=False), self.tr("Time (X)"))
        tabs.addTab(self._build_tab(self._cfg_yl, show_decimals=True), self.tr("Y left"))
        tabs.addTab(self._build_tab(self._cfg_yr, show_decimals=True), self.tr("Y right"))
        lay.addWidget(tabs, 1)

        return w, tabs

    def _build_general_tab(self, cfg: TimeSeriesGeneralSettings) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)

        title_grp = QGroupBox(self.tr("Plot title"))
        title_lay = QVBoxLayout(title_grp)
        ed_title = QLineEdit()
        ed_title.setText((cfg.title or "").strip())
        ed_title.setPlaceholderText(self.tr("Leave empty to use the default title"))
        ed_title.setClearButtonEnabled(True)
        ed_title.setMinimumHeight(26)
        title_lay.addWidget(ed_title)
        lay.addWidget(title_grp)

        colors_grp = QGroupBox(self.tr("Colors"))
        colors_form = QFormLayout(colors_grp)
        colors_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        colors_form.setHorizontalSpacing(12)
        colors_form.setVerticalSpacing(8)

        w._picked_widget_bg = QColor(cfg.widget_bg_qcolor())
        btn_widget_bg = QPushButton()

        def refresh_widget_bg():
            btn_widget_bg.setText(w._picked_widget_bg.name(QColor.NameFormat.HexRgb))

        refresh_widget_bg()

        def pick_widget_bg():
            nc = QColorDialog.getColor(w._picked_widget_bg, self, self.tr("Widget background"))
            if nc.isValid():
                w._picked_widget_bg = nc
                refresh_widget_bg()

        btn_widget_bg.clicked.connect(pick_widget_bg)
        colors_form.addRow(self.tr("Widget background:"), btn_widget_bg)

        w._picked_plot_bg = QColor(cfg.plot_bg_qcolor())
        btn_plot_bg = QPushButton()

        def refresh_plot_bg():
            btn_plot_bg.setText(w._picked_plot_bg.name(QColor.NameFormat.HexRgb))

        refresh_plot_bg()

        def pick_plot_bg():
            nc = QColorDialog.getColor(w._picked_plot_bg, self, self.tr("Plot background"))
            if nc.isValid():
                w._picked_plot_bg = nc
                refresh_plot_bg()

        btn_plot_bg.clicked.connect(pick_plot_bg)
        colors_form.addRow(self.tr("Plot background:"), btn_plot_bg)
        lay.addWidget(colors_grp)

        frame_grp = QGroupBox(self.tr("Frame"))
        frame_form = QFormLayout(frame_grp)
        frame_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        frame_form.setHorizontalSpacing(12)
        frame_form.setVerticalSpacing(8)

        w._picked_frame = QColor(cfg.frame_qcolor())
        btn_frame = QPushButton()

        def refresh_frame():
            btn_frame.setText(w._picked_frame.name(QColor.NameFormat.HexRgb))

        refresh_frame()

        def pick_frame():
            nc = QColorDialog.getColor(w._picked_frame, self, self.tr("Frame color"))
            if nc.isValid():
                w._picked_frame = nc
                refresh_frame()

        btn_frame.clicked.connect(pick_frame)
        sp_w = QSpinBox()
        sp_w.setRange(1, 6)
        sp_w.setValue(max(1, int(cfg.frame_width or 1)))
        frame_form.addRow(self.tr("Color:"), btn_frame)
        frame_form.addRow(self.tr("Width:"), sp_w)
        lay.addWidget(frame_grp)

        lay.addStretch(1)

        w._gen_title = ed_title
        w._gen_frame_w = sp_w
        return w

    def _build_header(self, icon_path: str) -> QWidget:
        w = QWidget()
        row = QHBoxLayout(w)
        row.setContentsMargins(0, 0, 0, 4)
        row.setSpacing(12)
        if os.path.isfile(icon_path):
            logo = QLabel()
            pm = QPixmap(icon_path)
            if not pm.isNull():
                logo.setPixmap(pm.scaled(48, 48, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            logo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            row.addWidget(logo, 0, Qt.AlignmentFlag.AlignTop)
        text_col = QVBoxLayout()
        title = QLabel(self.tr("Axis appearance"))
        f = title.font()
        f.setPointSize(max(f.pointSize(), 11))
        f.setBold(True)
        title.setFont(f)
        subtitle = QLabel(self.tr("Configure labels, scale, grid and tick style for each axis."))
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: palette(mid);")
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        row.addLayout(text_col, 1)
        return w

    def _build_tab(self, cfg: TimeSeriesAxisSettings, *, show_decimals: bool) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(8, 8, 8, 8)

        title_grp = QGroupBox(self.tr("Axis title"))
        title_lay = QVBoxLayout(title_grp)
        title_edit = QLineEdit()
        title_edit.setText(cfg.title)
        title_edit.setPlaceholderText(self.tr("Leave empty for default label"))
        title_edit.setMinimumHeight(26)
        title_edit.setClearButtonEnabled(True)
        title_lay.addWidget(title_edit)
        lay.addWidget(title_grp)

        scale_group = QGroupBox(self.tr("Scale"))
        scale_form = QFormLayout(scale_group)
        scale_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        scale_form.setHorizontalSpacing(12)
        scale_form.setVerticalSpacing(8)
        try:
            scale_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        except AttributeError:
            scale_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        combo_scale = QComboBox()
        combo_scale.addItem(self.tr("Automatic"), True)
        combo_scale.addItem(self.tr("Fixed (min, max, divisions)"), False)
        combo_scale.setCurrentIndex(0 if cfg.auto_scale else 1)
        combo_scale.setMinimumWidth(220)
        scale_form.addRow(self.tr("Mode:"), combo_scale)

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

        scale_form.addRow(self.tr("Minimum:"), sp_min)
        scale_form.addRow(self.tr("Maximum:"), sp_max)
        scale_form.addRow(self.tr("Divisions:"), sp_div)
        lay.addWidget(scale_group)

        grid_grp = QGroupBox(self.tr("Grid"))
        grid_lay = QVBoxLayout(grid_grp)
        chk_grid = QCheckBox(self.tr("Show grid lines for this axis"))
        chk_grid.setChecked(cfg.show_grid)
        grid_lay.addWidget(chk_grid)
        lay.addWidget(grid_grp)

        tick_grp = QGroupBox(self.tr("Tick labels"))
        tick_form = QFormLayout(tick_grp)
        tick_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        tick_form.setHorizontalSpacing(12)
        tick_form.setVerticalSpacing(8)
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
        font_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        fam = (cfg.tick_font_family or "").strip()
        if fam:
            font_combo.setCurrentFont(QFont(fam))

        tick_form.addRow(self.tr("Font size:"), sp_size)
        tick_form.addRow(self.tr("Font:"), font_combo)

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
        tick_form.addRow(self.tr("Color:"), btn_color)
        lay.addWidget(tick_grp)

        dec_grp = QGroupBox(self.tr("Numeric format"))
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

        lay.addStretch(1)

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

    def _on_accept(self) -> None:
        gen_tab = self._tabs.widget(0)
        self._cfg_gen.title = gen_tab._gen_title.text().strip()
        self._cfg_gen.widget_bg_hex = gen_tab._picked_widget_bg.name(QColor.NameFormat.HexRgb)
        self._cfg_gen.plot_bg_hex = gen_tab._picked_plot_bg.name(QColor.NameFormat.HexRgb)
        self._cfg_gen.frame_color_hex = gen_tab._picked_frame.name(QColor.NameFormat.HexRgb)
        self._cfg_gen.frame_width = int(gen_tab._gen_frame_w.value())

        self._read_tab(self._axes_tabs.widget(0), self._cfg_x)
        self._read_tab(self._axes_tabs.widget(1), self._cfg_yl)
        self._read_tab(self._axes_tabs.widget(2), self._cfg_yr)
        if not self._cfg_x.auto_scale:
            self._plot._view_x_min = None
            self._plot._view_x_max = None
        self._plot._axis_cfg_x = self._cfg_x
        self._plot._axis_cfg_y_left = self._cfg_yl
        self._plot._axis_cfg_y_right = self._cfg_yr
        self._plot._general_cfg = self._cfg_gen
        self._plot.update()
        self.accept()
