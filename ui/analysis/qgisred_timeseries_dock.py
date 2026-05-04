# -*- coding: utf-8 -*-
import math
import os
from typing import List
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QHBoxLayout, QToolButton
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, pyqtSignal, QSize
from qgis.PyQt.QtGui import QColor, QPainter, QFontMetrics, QIcon
from qgis.PyQt import uic
from qgis.core import QgsApplication

from ...compat import DIALOG_ACCEPTED

from .qgisred_timeseries_axis_dialog import TimeSeriesAxisOptionsDialog
from .timeseries_axis_settings import default_axis_settings, default_general_settings
from .timeseries_plot_layout import PlotLayoutCalculator
from .timeseries_legend_interaction import LegendInteractionController
from .timeseries_plot_renderer import TimeSeriesPlotRenderer
from .timeseries_plot_style import DEFAULT_SERIES_COLOR, LEGEND_ICON_SIZE, qfont

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_timeseries_dock.ui"))

class TimeSeriesPlotWidget(QWidget):
    seriesOrderChanged = pyqtSignal(list)
    seriesRemoved = pyqtSignal(str)
    seriesEmphasisChanged = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(TimeSeriesPlotWidget, self).__init__(parent)
        self.data_x = []
        self.data_y = []
        self.series = []
        self.title = ""
        self.x_label = "Time"
        self.y_label = "Value"
        self.is_stepped = False
        self.margin_left = 60
        self.margin_right = 20
        self.margin_top = 40
        self.margin_bottom = 40
        self.hover_index = None
        self.y_categorical_labels = None
        self.setMouseTracking(True)
        self.setMinimumSize(260, 170)
        self._legend_reserved_w = 0
        self._legend_hitboxes = []
        self._legend_delete_hitboxes = []
        self._hover_series_idx = None
        self._legend = LegendInteractionController(self)
        self._renderer = TimeSeriesPlotRenderer()
        self._y_label_left = ""
        self._y_label_right = ""
        self._y_magnitudes_left = []
        self._y_magnitudes_right = []
        self._right_axis_active = False
        self._right_axis_label_w = 0
        self._view_x_min = None
        self._view_x_max = None
        self._pan_mode = False
        self._pan_active = False
        self._pan_start_pos = None
        self._pan_start_view = None
        self._axis_cfg_x = default_axis_settings()
        self._axis_cfg_y_left = default_axis_settings()
        self._axis_cfg_y_right = default_axis_settings()
        self._general_cfg = default_general_settings()

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False, y_categorical_labels=None, series_label=""):
        self.data_x = x
        self.data_y = y
        self.title = title if (title or "").strip() else self.tr("Time evolution curves")
        self.x_label = x_label
        self.y_label = y_label
        self.is_stepped = is_stepped
        self.y_categorical_labels = y_categorical_labels
        self.series = [{
            "x": x,
            "y": y,
            "label": series_label or "",
            "color": DEFAULT_SERIES_COLOR,
            "is_stepped": is_stepped,
            "y_categorical_labels": y_categorical_labels,
            "muted": False,
            "highlighted": False,
            "series_key": series_label or "",
        }]
        self._y_label_left = self.y_label
        self._y_label_right = ""
        self._y_magnitudes_left = [self.y_label] if (self.y_label or "").strip() else []
        self._y_magnitudes_right = []
        self._right_axis_active = False
        self._view_x_min = None
        self._view_x_max = None
        self.update()

    def _normalizeSeriesState(self) -> None:
        for s in self.series:
            if "muted" not in s:
                s["muted"] = False
            if "highlighted" not in s:
                s["highlighted"] = False
            if "series_key" not in s:
                s["series_key"] = ""
            if "y_axis" not in s:
                s["y_axis"] = ""

    def _assignYAxisByMagnitude(self) -> None:
        magnitudes: List[str] = []
        for s in self.series:
            m = (s.get("magnitude") or "").strip()
            if m and m not in magnitudes:
                magnitudes.append(m)
        left_mag = magnitudes[0] if magnitudes else ""
        right_mags = magnitudes[1:] if len(magnitudes) > 1 else []
        for s in self.series:
            m = (s.get("magnitude") or "").strip()
            if right_mags and m in right_mags:
                s["y_axis"] = "right"
            else:
                s["y_axis"] = "left"
        self._y_label_left = left_mag or self.y_label
        self._y_label_right = ", ".join(right_mags)
        self._y_magnitudes_left = [left_mag] if left_mag else ([self.y_label] if (self.y_label or "").strip() else [])
        self._y_magnitudes_right = right_mags[:]
        self._right_axis_active = bool(right_mags)

    def setSeries(self, series, title="", x_label="Time", y_label="Value"):
        self.hover_index = None
        self._hover_series_idx = None
        self._resetLegendInteractionState()
        self.series = series or []
        self._normalizeSeriesState()
        self.title = title if (title or "").strip() else self.tr("Time evolution curves")
        self.x_label = x_label
        self.y_label = y_label
        self._assignYAxisByMagnitude()

        if len(self.series) == 1:
            self.data_x = self.series[0].get("x", [])
            self.data_y = self.series[0].get("y", [])
            self.is_stepped = bool(self.series[0].get("is_stepped", False))
            self.y_categorical_labels = self.series[0].get("y_categorical_labels", None)
        else:
            self.data_x = []
            self.data_y = []
            self.is_stepped = False
            self.y_categorical_labels = None
        self._view_x_min = None
        self._view_x_max = None
        self.update()

    def _seriesByAxis(self):
        left = []
        right = []
        for s in self.series:
            if (s.get("y_axis") or "left") == "right":
                right.append(s)
            else:
                left.append(s)
        return left, right

    def _axisSeriesData(self, axis_series):
        if not axis_series:
            return [], [], None, False
        all_x = []
        all_y = []
        y_categorical_labels = None
        any_categorical = False
        any_stepped = False

        def as_finite_float(v):
            if v is None:
                return None
            try:
                f = float(v)
            except Exception:
                return None
            if not math.isfinite(f):
                return None
            return f

        for s in axis_series:
            xs_raw = s.get("x", []) or []
            ys_raw = s.get("y", []) or []

            n = min(len(xs_raw), len(ys_raw))
            xs = []
            ys = []
            for i in range(n):
                x = as_finite_float(xs_raw[i])
                y = as_finite_float(ys_raw[i])
                if x is None or y is None:
                    continue
                xs.append(x)
                ys.append(y)

            s["x"] = xs
            s["y"] = ys

            if xs and ys:
                all_x.extend(xs)
                all_y.extend(ys)
            if s.get("y_categorical_labels"):
                any_categorical = True
                y_categorical_labels = s.get("y_categorical_labels")
            if s.get("is_stepped"):
                any_stepped = True
        if any_categorical:
            for s in axis_series:
                if s.get("y_categorical_labels") != y_categorical_labels:
                    y_categorical_labels = None
                    break
        return all_x, all_y, y_categorical_labels, any_stepped

    def _format_value_full(self, value):
        if value is None:
            return ""
        try:
            v = float(value)
            s = format(v, ".3g")
            if s in ("-0", "-0.0", "-0.00"):
                s = "0"
            return s
        except Exception:
            return str(value)

    def _series_value_for_legend(self, s):
        ys = s.get("y", []) or []
        if not ys:
            return None

        try:
            hi = self.hover_index
            if hi is not None and 0 <= int(hi) < len(ys):
                v = ys[int(hi)]
                if v is not None:
                    return v
        except Exception:
            pass

        for v in reversed(ys):
            if v is not None:
                return v
        return None

    def _legendDisplayLabel(self, series_dict):
        base = (series_dict.get("label") or "").strip() or self.tr("Series")
        series_y_labels = series_dict.get("y_categorical_labels") or self.y_categorical_labels
        v = self._series_value_for_legend(series_dict)
        if v is None:
            return base
        if series_y_labels:
            try:
                v_str = series_y_labels[int(round(v))]
            except Exception:
                v_str = str(v)
        else:
            v_str = self._format_value_full(v)
        return f"{base}: {v_str}"

    def update(self):
        super(TimeSeriesPlotWidget, self).update()

    def _globalSeriesData(self):
        return self._axisSeriesData(self.series)

    def _legendItems(self, limit=None):
        items = []
        for idx, s in enumerate(self.series):
            label = (s.get("label") or "").strip()
            if label:
                legend_type = (s.get("legend_type") or "").strip()
                magnitude = (s.get("magnitude") or "").strip()
                items.append((idx, (s.get("color") or DEFAULT_SERIES_COLOR), label, legend_type, magnitude))
        if limit is None:
            return items
        return items[:limit]

    def _legendGroups(self):
        grouped = {}
        for series_idx, color, label, legend_type, magnitude in self._legendItems():
            mag = (magnitude or self.tr("Magnitude")).strip()
            if mag not in grouped:
                grouped[mag] = []
            grouped[mag].append((series_idx, color, label, legend_type))
        return list(grouped.items())

    def _legendRequiredWidth(self):
        groups = self._legendGroups()
        if not groups:
            return 0
        fm = QFontMetrics(qfont(8))
        fm_hdr = QFontMetrics(qfont(8, bold=True))
        max_w = 0
        for mag, items in groups:
            w_hdr = fm_hdr.horizontalAdvance(mag)
            if w_hdr > max_w:
                max_w = w_hdr
            for _idx, _color, label, _legend_type in items:
                w_label = fm.horizontalAdvance(label)
                if w_label > max_w:
                    max_w = w_label
        return LEGEND_ICON_SIZE + 6 + max_w + 12

    def _resetLegendInteractionState(self):
        self._legend.reset()

    def _emitSeriesEmphasisChanged(self) -> None:
        try:
            highlighted = []
            muted = []
            for s in self.series or []:
                k = str(s.get("series_key") or "")
                if not k:
                    continue
                if bool(s.get("highlighted", False)):
                    highlighted.append(k)
                if bool(s.get("muted", False)):
                    muted.append(k)
            self.seriesEmphasisChanged.emit({"highlighted": highlighted, "muted": muted})
        except Exception:
            return

    def removeSeries(self, series_idx: int) -> bool:
        try:
            idx = int(series_idx)
        except Exception:
            return False
        if not (0 <= idx < len(self.series)):
            return False

        try:
            removed_key = str(self.series[idx].get("series_key") or "")
        except Exception:
            removed_key = ""

        self.series.pop(idx)
        self._assignYAxisByMagnitude()

        if self._hover_series_idx is not None and self._hover_series_idx >= len(self.series):
            self._hover_series_idx = None
        if self.hover_index is not None and not self.series:
            self.hover_index = None

        order = [str(s.get("series_key") or "") for s in self.series]
        self.seriesOrderChanged.emit(order)
        if removed_key:
            self.seriesRemoved.emit(removed_key)
        return True

    def _resolveHoverSeriesIndex(self):
        for i, s in enumerate(self.series):
            if bool(s.get("highlighted", False)):
                return i
        for i, s in enumerate(self.series):
            if not bool(s.get("muted", False)):
                return i
        return 0 if self.series else None

    def _nearestDataIndex(self, xs, target_x):
        best_idx = 0
        min_dist = abs(xs[0] - target_x)
        for i in range(1, len(xs)):
            dist = abs(xs[i] - target_x)
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        return best_idx

    def _getCurrentXRange(self):
        if not getattr(self, "_axis_cfg_x", None).auto_scale:
            lo, hi = float(self._axis_cfg_x.fixed_min), float(self._axis_cfg_x.fixed_max)
            if hi <= lo:
                hi = lo + 1.0
            return lo, hi
        last = getattr(self, "_last_x_state", None)
        if last:
            return last["min_x"], last["max_x"]
        if self._view_x_min is not None and self._view_x_max is not None:
            return self._view_x_min, self._view_x_max
        all_data_x = []
        for s in self.series:
            all_data_x.extend(s.get("x", []) or [])
        if not all_data_x:
            return 0.0, 1.0
        auto_min = min(all_data_x)
        auto_max = max(all_data_x)
        if auto_max == auto_min:
            auto_max = auto_min + 1.0
        return auto_min, auto_max

    def resetView(self):
        self._view_x_min = None
        self._view_x_max = None
        self._last_x_state = None
        self.update()

    def zoomIn(self, factor=1.5):
        if not self.series:
            return
        if not self._axis_cfg_x.auto_scale:
            return
        x_min, x_max = self._getCurrentXRange()
        cx = (x_min + x_max) / 2.0
        half = (x_max - x_min) / (2.0 * factor)
        self._view_x_min = cx - half
        self._view_x_max = cx + half
        self._last_x_state = None
        self.hover_index = None
        self.update()

    def zoomOut(self, factor=1.5):
        if not self.series:
            return
        if not self._axis_cfg_x.auto_scale:
            return
        x_min, x_max = self._getCurrentXRange()
        cx = (x_min + x_max) / 2.0
        half = (x_max - x_min) * factor / 2.0
        new_min = cx - half
        new_max = cx + half
        auto_state = getattr(self, "_last_auto_x_state", None)
        if auto_state:
            auto_min, auto_max = auto_state["min_x"], auto_state["max_x"]
        else:
            all_data_x = []
            for s in self.series:
                all_data_x.extend(s.get("x", []) or [])
            auto_min = min(all_data_x) if all_data_x else 0.0
            auto_max = max(all_data_x) if all_data_x else 1.0
        if new_min <= auto_min and new_max >= auto_max:
            self._view_x_min = None
            self._view_x_max = None
            self._last_x_state = None
            self.hover_index = None
            self.update()
            return
        self._view_x_min = new_min
        self._view_x_max = new_max
        self._last_x_state = None
        self.hover_index = None
        self.update()

    def setPanMode(self, enabled: bool):
        self._pan_mode = enabled
        self._pan_active = False
        self._pan_start_pos = None
        self._pan_start_view = None
        if enabled:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.unsetCursor()

    def getPlotRect(self):
        return PlotLayoutCalculator.compute_plot_rect(self)

    def paintEvent(self, event):
        painter = QPainter(self)
        self._renderer.render(self, painter)

    def leaveEvent(self, event):
        if self.hover_index is not None:
            self.hover_index = None
            self._hover_series_idx = None
            self.update()

    def wheelEvent(self, event):
        if not self.series:
            return
        if not self._axis_cfg_x.auto_scale:
            return
        plot_rect, _, _ = self.getPlotRect()
        mouse_pos = event.pos()
        if not plot_rect.contains(QPointF(mouse_pos)):
            return
        delta = event.angleDelta().y()
        if delta == 0:
            return
        factor = 1.3 if delta > 0 else 1.0 / 1.3
        x_min, x_max = self._getCurrentXRange()
        rel_x = (mouse_pos.x() - plot_rect.left()) / plot_rect.width()
        mouse_x = x_min + rel_x * (x_max - x_min)
        new_range = (x_max - x_min) / factor
        new_min = mouse_x - rel_x * new_range
        new_max = new_min + new_range
        if factor < 1.0:
            auto_state = getattr(self, "_last_auto_x_state", None)
            if auto_state:
                auto_min, auto_max = auto_state["min_x"], auto_state["max_x"]
            else:
                all_data_x = []
                for s in self.series:
                    all_data_x.extend(s.get("x", []) or [])
                auto_min = min(all_data_x) if all_data_x else 0.0
                auto_max = max(all_data_x) if all_data_x else 1.0
            if new_min <= auto_min and new_max >= auto_max:
                self._view_x_min = None
                self._view_x_max = None
                self._last_x_state = None
                self.hover_index = None
                self.update()
                event.accept()
                return
        self._view_x_min = new_min
        self._view_x_max = new_max
        self._last_x_state = None
        self.hover_index = None
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._pan_mode:
                if not self._axis_cfg_x.auto_scale:
                    return
                plot_rect, _, _ = self.getPlotRect()
                if plot_rect.contains(QPointF(event.pos())):
                    self._pan_active = True
                    self._pan_start_pos = QPointF(event.pos())
                    self._pan_start_view = self._getCurrentXRange()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return
            self._legend.begin(QPointF(event.pos()), event.modifiers())
        elif event.button() == Qt.MouseButton.MiddleButton:
            if not self._axis_cfg_x.auto_scale:
                return
            plot_rect, _, _ = self.getPlotRect()
            if plot_rect.contains(QPointF(event.pos())):
                self._pan_active = True
                self._pan_start_pos = QPointF(event.pos())
                self._pan_start_view = self._getCurrentXRange()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)

    def mouseReleaseEvent(self, event):
        if self._pan_active:
            self._pan_active = False
            self._pan_start_pos = None
            self._pan_start_view = None
            if self._pan_mode:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.unsetCursor()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if self._pan_mode:
            return

        if self._legend.drag_active and self._legend.apply_reorder_if_needed():
            self._resetLegendInteractionState()
            self.update()
            return

        if self._legend.apply_delete_if_click():
            self.update()
            self._resetLegendInteractionState()
            return

        if self._legend.apply_toggle_if_click():
            self.update()
            self._emitSeriesEmphasisChanged()

        self._resetLegendInteractionState()

    def mouseMoveEvent(self, event):
        if self._pan_active and self._pan_start_pos is not None:
            if not self._axis_cfg_x.auto_scale:
                return
            plot_rect, _, _ = self.getPlotRect()
            if plot_rect.width() > 0:
                dx_px = event.pos().x() - self._pan_start_pos.x()
                x_min0, x_max0 = self._pan_start_view
                x_range = x_max0 - x_min0
                dx_data = -dx_px / plot_rect.width() * x_range
                self._view_x_min = x_min0 + dx_data
                self._view_x_max = x_max0 + dx_data
                self._last_x_state = None
                self.hover_index = None
                self.update()
            return

        if self._pan_mode:
            return

        if self._legend.update_drag(QPointF(event.pos())):
            return

        if not self.series:
            return

        hover_idx = self._resolveHoverSeriesIndex()
        if hover_idx is None:
            return

        xs = self.series[hover_idx].get("x", []) or []
        if not xs or len(xs) < 2:
            return

        mouse_pos = event.pos()
        w = self.width()
        h = self.height()

        if w <= (self.margin_left + self.margin_right) or h <= (self.margin_top + 10 + self.margin_bottom):
            return

        plot_rect, local_margin_left, _right_axis_label_w = self.getPlotRect()

        if not plot_rect.contains(QPointF(mouse_pos)):
            if self.hover_index is not None:
                self.hover_index = None
                self._hover_series_idx = None
                self.update()
            return

        x_min, x_max = self._getCurrentXRange()
        x_range = x_max - x_min
        if x_range <= 0:
            x_range = 1

        try:
            rel_x = (mouse_pos.x() - plot_rect.left()) / plot_rect.width()
            target_x = x_min + rel_x * x_range

            best_idx = self._nearestDataIndex(xs, target_x)

            if self.hover_index != best_idx or self._hover_series_idx != hover_idx:
                self.hover_index = best_idx
                self._hover_series_idx = hover_idx
                self.update()
        except ZeroDivisionError:
            pass


class QGISRedTimeSeriesDock(QDockWidget, FORM_CLASS):
    seriesReordered = pyqtSignal(list)
    seriesRemoved = pyqtSignal(str)
    seriesEmphasisChanged = pyqtSignal(dict)
    clearAllRequested = pyqtSignal()

    def __init__(self, iface, parent=None):
        super(QGISRedTimeSeriesDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        self._toolbarWidget = None

        self._initToolbar()
        
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)
        self.plot.seriesOrderChanged.connect(self.seriesReordered)
        self.plot.seriesOrderChanged.connect(self._onSeriesOrderChanged)
        self.plot.seriesRemoved.connect(self.seriesRemoved)
        self.plot.seriesEmphasisChanged.connect(self.seriesEmphasisChanged)

        self.lblTitle.hide()
        
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")
        self._updateClearToolbarVisibility()

    def _initToolbar(self) -> None:
        try:
            container = QWidget(self)
            self._toolbarWidget = container
            hl = QHBoxLayout(container)
            hl.setContentsMargins(4, 2, 4, 2)
            hl.setSpacing(2)
            container.setFixedHeight(28)
            container.setStyleSheet(
                "QWidget {"
                "  background-color: #efefef;"
                "  border: 1px solid #d2d2d2;"
                "  border-radius: 4px;"
                "}"
            )

            btn_style = (
                "QToolButton {"
                "  border: 1px solid #c8c8c8;"
                "  border-radius: 3px;"
                "  background-color: #f8f8f8;"
                "  padding: 1px;"
                "}"
                "QToolButton:hover { background-color: #f0f0f0; border-color: #bdbdbd; }"
                "QToolButton:pressed { background-color: #e6e6e6; border-color: #b4b4b4; }"
                "QToolButton:checked { background-color: #d0e4f7; border-color: #3399ff; }"
                "QToolButton:focus { border: 1px solid #3399ff; }"
            )

            def _make_btn(name, icon, tooltip, checkable=False):
                btn = QToolButton(container)
                btn.setObjectName(name)
                btn.setIcon(QgsApplication.getThemeIcon(icon))
                btn.setToolTip(tooltip)
                btn.setAutoRaise(True)
                btn.setCheckable(checkable)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                btn.setIconSize(QSize(16, 16))
                btn.setFixedSize(QSize(22, 22))
                btn.setStyleSheet(btn_style)
                return btn

            self.btnClearAll = QToolButton(container)
            self.btnClearAll.setObjectName("btnClearAllTimeSeries")
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "images", "iconClear.svg"))
            self.btnClearAll.setIcon(QIcon(icon_path))
            self.btnClearAll.setToolTip(self.tr("Clear all curves"))
            self.btnClearAll.setAutoRaise(True)
            self.btnClearAll.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.btnClearAll.setIconSize(QSize(16, 16))
            self.btnClearAll.setFixedSize(QSize(22, 22))
            self.btnClearAll.setStyleSheet(btn_style)
            self.btnClearAll.clicked.connect(self.clearAllRequested)
            hl.addWidget(self.btnClearAll, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnPan = _make_btn("btnPanTimeSeries", "mActionPan.svg", self.tr("Pan"), checkable=True)
            self.btnPan.toggled.connect(self._onPanToggled)
            hl.addWidget(self.btnPan, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomIn = _make_btn("btnZoomInTimeSeries", "mActionZoomIn.svg", self.tr("Zoom in"))
            self.btnZoomIn.clicked.connect(lambda: self.plot.zoomIn())
            hl.addWidget(self.btnZoomIn, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomOut = _make_btn("btnZoomOutTimeSeries", "mActionZoomOut.svg", self.tr("Zoom out"))
            self.btnZoomOut.clicked.connect(lambda: self.plot.zoomOut())
            hl.addWidget(self.btnZoomOut, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnFit = _make_btn("btnFitTimeSeries", "mActionZoomFullExtent.svg", self.tr("Zoom to full extent"))
            self.btnFit.clicked.connect(self._onFitClicked)
            hl.addWidget(self.btnFit, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnAxes = _make_btn("btnAxesTimeSeries", "mActionOptions.svg", self.tr("Axis options…"))
            self.btnAxes.clicked.connect(self._onAxisOptionsClicked)
            hl.addWidget(self.btnAxes, 0, Qt.AlignmentFlag.AlignLeft)

            hl.addStretch(1)

            try:
                self.verticalLayout.insertWidget(0, container)
            except Exception:
                self.verticalLayout.addWidget(container)
        except Exception:
            return

    def _onPanToggled(self, checked: bool) -> None:
        self.plot.setPanMode(checked)

    def _onFitClicked(self) -> None:
        self.plot.resetView()
        if hasattr(self, "btnPan") and self.btnPan.isChecked():
            self.btnPan.setChecked(False)

    def _onAxisOptionsClicked(self) -> None:
        dlg = TimeSeriesAxisOptionsDialog(self.plot, self.window())
        if dlg.exec() == DIALOG_ACCEPTED and not self.plot._axis_cfg_x.auto_scale:
            if hasattr(self, "btnPan") and self.btnPan.isChecked():
                self.btnPan.setChecked(False)
            self.plot.setPanMode(False)

    def _plotHasCurves(self) -> bool:
        try:
            for s in self.plot.series or []:
                xs = s.get("x", []) or []
                ys = s.get("y", []) or []
                if xs and ys:
                    return True
        except Exception:
            return False
        return False

    def _updateClearToolbarVisibility(self) -> None:
        if self._toolbarWidget is None:
            return
        self._toolbarWidget.setVisible(self._plotHasCurves())

    def _onSeriesOrderChanged(self, _order) -> None:
        self._updateClearToolbarVisibility()

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)
        self._updateClearToolbarVisibility()

    def updatePlotSeries(self, series, title, x_label, y_label):
        self.plot.setSeries(series, title, x_label, y_label)
        self._updateClearToolbarVisibility()
