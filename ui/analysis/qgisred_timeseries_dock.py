# -*- coding: utf-8 -*-
import csv
import math
import os
from typing import List
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QRubberBand, QFileDialog
from qgis.PyQt.QtCore import QCoreApplication, QEvent, Qt, QPointF, QRect, QRectF, pyqtSignal, QSize
from qgis.PyQt.QtGui import QColor, QPainter, QFontMetrics, QIcon, QPixmap
from qgis.PyQt import uic
from qgis.core import QgsApplication

from ...compat import DIALOG_ACCEPTED
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils

from .qgisred_timeseries_axis_dialog import TimeSeriesAxisOptionsDialog
from .qgisred_results_data import get_regional_separators
from .timeseries_axis_settings import default_axis_settings, default_general_settings
from .timeseries_plot_layout import PlotLayoutCalculator
from .timeseries_legend_interaction import LegendInteractionController
from .timeseries_plot_renderer import TimeSeriesPlotRenderer
from .timeseries_plot_style import DEFAULT_SERIES_COLOR, LEGEND_ICON_SIZE, LEGEND_ROW_GAP, qfont

try:
    from qgis.PyQt.QtSvg import QSvgGenerator
except Exception:
    QSvgGenerator = None

try:
    _LEGEND_ROW_GAP = int(LEGEND_ROW_GAP)
except Exception:
    _LEGEND_ROW_GAP = 16

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_timeseries_dock.ui"))

class TimeSeriesPlotWidget(QWidget):
    _MIN_VIEW_HOURS = 1.0

    seriesOrderChanged = pyqtSignal(list)
    seriesRemoved = pyqtSignal(str)
    seriesEmphasisChanged = pyqtSignal(dict)
    viewChanged = pyqtSignal()

    def tr(self, message: str) -> str:
        return QCoreApplication.translate("TimeSeriesPlotWidget", message)

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
        self._base_min_w = 260
        self._base_min_h = 220
        self.setMinimumSize(self._base_min_w, self._base_min_h)
        self._legend_reserved_w = 0
        self._legend_reserved_h = 0
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
        self._zoom_window_mode = False
        self._zoom_window_active = False
        self._zoom_window_start_pos = None
        self._zoom_rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self._synced_cursor_time_hours = None
        self._axis_cfg_x = default_axis_settings()
        self._axis_cfg_y_left = default_axis_settings()
        self._axis_cfg_y_right = default_axis_settings()
        self._general_cfg = default_general_settings()
        self._updateMinimumWidthForTitle()

    def _clearHoverState(self, repaint: bool = False) -> None:
        had_hover = self.hover_index is not None or self._hover_series_idx is not None
        self.hover_index = None
        self._hover_series_idx = None
        if repaint and had_hover:
            self.update()

    def _updateMinimumWidthForTitle(self) -> None:
        title = (self.title or "").strip()
        if not title:
            title = self.tr("Time evolution curves")
        title_font = qfont(10, bold=True)
        title_w = QFontMetrics(title_font).horizontalAdvance(title)
        pad = 24
        min_w = max(int(self._base_min_w), int(title_w + pad))
        if hasattr(self, "setMinimumWidth"):
            self.setMinimumWidth(min_w)
        else:
            try:
                cur_min_h = int(getattr(self, "minimumHeight", lambda: self._base_min_h)())
            except Exception:
                cur_min_h = int(self._base_min_h)
            self.setMinimumSize(min_w, max(int(self._base_min_h), cur_min_h))

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
            "emphasis_mode": "normal",
            "visible": True,
            "line_style": "solid",
            "line_width": 2.0,
            "show_markers": False,
            "marker_symbol": "circle",
            "marker_size": 6,
            "marker_color": DEFAULT_SERIES_COLOR,
            "show_point_values": False,
            "legend_font_family": "",
            "legend_font_size": 8,
            "series_key": series_label or "",
        }]
        self._y_label_left = self.y_label
        self._y_label_right = ""
        self._y_magnitudes_left = [self.y_label] if (self.y_label or "").strip() else []
        self._y_magnitudes_right = []
        self._right_axis_active = False
        self._view_x_min = None
        self._view_x_max = None
        self._updateMinimumWidthForTitle()
        self.update()

    def _normalizeSeriesState(self) -> None:
        for s in self.series:
            if "muted" not in s:
                s["muted"] = False
            if "highlighted" not in s:
                s["highlighted"] = False
            if "visible" not in s:
                s["visible"] = True
            if "emphasis_mode" not in s:
                if bool(s.get("highlighted", False)):
                    s["emphasis_mode"] = "highlighted"
                elif bool(s.get("muted", False)):
                    s["emphasis_mode"] = "muted"
                else:
                    s["emphasis_mode"] = "normal"
            if "line_style" not in s:
                s["line_style"] = "solid"
            if "line_width" not in s:
                s["line_width"] = 2.0
            if "show_markers" not in s:
                s["show_markers"] = False
            if "marker_symbol" not in s:
                s["marker_symbol"] = "circle"
            if "marker_size" not in s:
                s["marker_size"] = 6
            if "marker_color" not in s:
                s["marker_color"] = s.get("color") or DEFAULT_SERIES_COLOR
            if "show_point_values" not in s:
                s["show_point_values"] = False
            if "legend_font_family" not in s:
                s["legend_font_family"] = ""
            if "legend_font_size" not in s:
                s["legend_font_size"] = 8
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
        self._updateMinimumWidthForTitle()

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
            if not bool(s.get("visible", True)):
                continue
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
        gen = getattr(self, "_general_cfg", None)
        sym = int(getattr(gen, "legend_symbol_size", LEGEND_ICON_SIZE) or LEGEND_ICON_SIZE) if gen is not None else LEGEND_ICON_SIZE
        sym = max(6, min(sym, 24))
        cols = int(getattr(gen, "legend_columns", 1) or 1) if gen is not None else 1
        cols = max(1, min(cols, 6))
        fm_hdr = QFontMetrics(qfont(8, bold=True))
        max_w = 0
        for mag, items in groups:
            w_hdr = fm_hdr.horizontalAdvance(mag)
            if w_hdr > max_w:
                max_w = w_hdr
            for _idx, _color, label, _legend_type in items:
                row_font = qfont(8)
                try:
                    if 0 <= int(_idx) < len(self.series):
                        s = self.series[int(_idx)]
                        fam = (s.get("legend_font_family") or "").strip()
                        size = max(6, min(int(s.get("legend_font_size") or 8), 32))
                        row_font = qfont(size)
                        if fam:
                            row_font.setFamily(fam)
                except Exception:
                    row_font = qfont(8)
                w_label = QFontMetrics(row_font).horizontalAdvance(label)
                if w_label > max_w:
                    max_w = w_label
        btn_w = 10
        col_w = sym + 6 + max_w + btn_w + 16
        gap = 8
        return int(cols * col_w + (cols - 1) * gap)

    def _legendRequiredHeight(self) -> int:
        groups = self._legendGroups()
        if not groups:
            return 0
        gen = getattr(self, "_general_cfg", None)
        cols = int(getattr(gen, "legend_columns", 1) or 1) if gen is not None else 1
        cols = max(1, min(cols, 6))

        row_steps = 0
        for _mag, items in groups:
            row_steps += 1
            row_steps += len(items)
            row_steps += 1

        import math

        rows_per_col = int(math.ceil(float(row_steps) / float(cols))) if cols > 0 else row_steps
        top_pad = 10
        bottom_pad = 10
        return int(top_pad + rows_per_col * _LEGEND_ROW_GAP + bottom_pad)

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
            if bool(s.get("visible", True)) and bool(s.get("highlighted", False)):
                return i
        for i, s in enumerate(self.series):
            if bool(s.get("visible", True)) and not bool(s.get("muted", False)):
                return i
        for i, s in enumerate(self.series):
            if bool(s.get("visible", True)):
                return i
        return None

    def _nearestDataIndex(self, xs, target_x):
        best_idx = 0
        min_dist = abs(xs[0] - target_x)
        for i in range(1, len(xs)):
            dist = abs(xs[i] - target_x)
            if dist < min_dist:
                min_dist = dist
                best_idx = i
        return best_idx

    def setSyncedCursorTimeHours(self, hours) -> None:
        try:
            value = float(hours)
        except Exception:
            self.clearSyncedCursor()
            return
        if not math.isfinite(value):
            self.clearSyncedCursor()
            return
        self._synced_cursor_time_hours = value
        self.update()

    def clearSyncedCursor(self) -> None:
        if self._synced_cursor_time_hours is not None:
            self._synced_cursor_time_hours = None
            self.update()

    def _getCurrentXRange(self):
        if not getattr(self, "_axis_cfg_x", None).auto_scale:
            lo, hi = float(self._axis_cfg_x.fixed_min), float(self._axis_cfg_x.fixed_max)
            if hi <= lo:
                hi = lo + 1.0
            return lo, hi
        if self._view_x_min is not None and self._view_x_max is not None:
            return self._view_x_min, self._view_x_max
        last = getattr(self, "_last_x_state", None)
        if last:
            return last["min_x"], last["max_x"]
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

    def _simulationXBounds(self):
        all_data_x = []
        try:
            for s in self.series or []:
                all_data_x.extend(s.get("x", []) or [])
        except Exception:
            all_data_x = []
        if not all_data_x:
            return 0.0, 1.0
        try:
            max_x = float(max(all_data_x))
        except Exception:
            max_x = 1.0
        if not math.isfinite(max_x):
            max_x = 1.0
        if max_x <= 0.0:
            max_x = 1.0
        return 0.0, max_x

    def _clampViewToSimulationBounds(self, new_min: float, new_max: float):
        sim_min, sim_max = self._simulationXBounds()
        if new_max <= new_min:
            return None, None
        min_view_range = max(0.0, float(getattr(self, "_MIN_VIEW_HOURS", 0.0) or 0.0))
        view_range = new_max - new_min
        sim_range = sim_max - sim_min
        if 0.0 < view_range < min_view_range < sim_range:
            center = (new_min + new_max) / 2.0
            half = min_view_range / 2.0
            new_min = center - half
            new_max = center + half
            view_range = min_view_range
        if view_range >= sim_range:
            return None, None
        if new_min < sim_min:
            new_min = sim_min
            new_max = new_min + view_range
        if new_max > sim_max:
            new_max = sim_max
            new_min = new_max - view_range
        if new_min < sim_min:
            new_min = sim_min
        if new_max > sim_max:
            new_max = sim_max
        return new_min, new_max

    def _minimumZoomRange(self) -> float:
        min_view_range = max(0.0, float(getattr(self, "_MIN_VIEW_HOURS", 0.0) or 0.0))
        sim_min, sim_max = self._simulationXBounds()
        sim_range = max(0.0, sim_max - sim_min)
        if sim_range <= 0.0:
            return min_view_range
        if min_view_range <= 0.0:
            return 0.0
        return min(min_view_range, sim_range)

    def resetView(self):
        self._view_x_min = None
        self._view_x_max = None
        self._last_x_state = None
        self.update()
        self.viewChanged.emit()

    def zoomIn(self, factor=1.5):
        if not self.series:
            return
        if not self._axis_cfg_x.auto_scale:
            return
        x_min, x_max = self._getCurrentXRange()
        current_range = x_max - x_min
        min_range = self._minimumZoomRange()
        if min_range > 0.0 and current_range <= min_range + 1e-9:
            return
        cx = (x_min + x_max) / 2.0
        new_range = current_range / factor
        if min_range > 0.0:
            new_range = max(new_range, min_range)
        half = new_range / 2.0
        new_min, new_max = cx - half, cx + half
        new_min, new_max = self._clampViewToSimulationBounds(new_min, new_max)
        self._view_x_min = new_min
        self._view_x_max = new_max
        self._last_x_state = None
        self.hover_index = None
        self.update()
        self.viewChanged.emit()

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
        new_min, new_max = self._clampViewToSimulationBounds(new_min, new_max)
        self._view_x_min = new_min
        self._view_x_max = new_max
        self._last_x_state = None
        self.hover_index = None
        self.update()
        self.viewChanged.emit()

    def setPanMode(self, enabled: bool):
        self._pan_mode = enabled
        self._pan_active = False
        self._pan_start_pos = None
        self._pan_start_view = None
        if enabled:
            self.setZoomWindowMode(False)
        if enabled:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.unsetCursor()

    def setZoomWindowMode(self, enabled: bool) -> None:
        self._zoom_window_mode = bool(enabled)
        self._zoom_window_active = False
        self._zoom_window_start_pos = None
        try:
            self._zoom_rubber_band.hide()
        except Exception:
            pass
        if enabled:
            self._pan_mode = False
            self._pan_active = False
            self._pan_start_pos = None
            self._pan_start_view = None
            self._clearHoverState(repaint=True)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            if not self._pan_mode:
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
        current_range = x_max - x_min
        min_range = self._minimumZoomRange()
        if delta > 0 and min_range > 0.0 and current_range <= min_range + 1e-9:
            event.accept()
            return
        rel_x = (mouse_pos.x() - plot_rect.left()) / plot_rect.width()
        mouse_x = x_min + rel_x * current_range
        new_range = current_range / factor
        if delta > 0 and min_range > 0.0:
            new_range = max(new_range, min_range)
        new_min = mouse_x - rel_x * new_range
        new_max = new_min + new_range
        new_min, new_max = self._clampViewToSimulationBounds(new_min, new_max)
        self._view_x_min = new_min
        self._view_x_max = new_max
        self._last_x_state = None
        self.hover_index = None
        self.update()
        self.viewChanged.emit()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._zoom_window_mode:
                if not self._axis_cfg_x.auto_scale:
                    return
                plot_rect, _, _ = self.getPlotRect()
                if plot_rect.contains(QPointF(event.pos())):
                    self._zoom_window_active = True
                    self._zoom_window_start_pos = QPointF(event.pos())
                    self._clearHoverState(repaint=True)
                    self._zoom_rubber_band.setGeometry(QRectF(self._zoom_window_start_pos, self._zoom_window_start_pos).toRect())
                    self._zoom_rubber_band.show()
                return
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
        if self._zoom_window_active:
            self._zoom_window_active = False
            try:
                self._zoom_rubber_band.hide()
            except Exception:
                pass
            if event.button() == Qt.MouseButton.LeftButton and self._axis_cfg_x.auto_scale:
                plot_rect, _, _ = self.getPlotRect()
                if plot_rect.width() > 0:
                    start = self._zoom_window_start_pos
                    end = QPointF(event.pos())
                    if start is not None:
                        left_px = min(start.x(), end.x())
                        right_px = max(start.x(), end.x())
                        sel_w = right_px - left_px
                        if sel_w >= 6:
                            x_min, x_max = self._getCurrentXRange()
                            x_range = x_max - x_min
                            rel_l = (left_px - plot_rect.left()) / plot_rect.width()
                            rel_r = (right_px - plot_rect.left()) / plot_rect.width()
                            rel_l = max(0.0, min(1.0, rel_l))
                            rel_r = max(0.0, min(1.0, rel_r))
                            new_min = x_min + rel_l * x_range
                            new_max = x_min + rel_r * x_range
                            new_min, new_max = self._clampViewToSimulationBounds(new_min, new_max)
                            self._view_x_min = new_min
                            self._view_x_max = new_max
                            self._last_x_state = None
                            self.hover_index = None
                            self.update()
                            self.viewChanged.emit()
            self._zoom_window_start_pos = None
            return

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
        if self._zoom_window_mode and not self._zoom_window_active:
            self._clearHoverState(repaint=True)
            return

        if self._zoom_window_active and self._zoom_window_start_pos is not None:
            plot_rect, _, _ = self.getPlotRect()
            if plot_rect.contains(QPointF(self._zoom_window_start_pos)) and plot_rect.contains(QPointF(event.pos())):
                start = self._zoom_window_start_pos
                cur = QPointF(event.pos())
                rect = QRectF(start, cur).normalized()
                self._zoom_rubber_band.setGeometry(rect.toRect())
            else:
                start = self._zoom_window_start_pos
                cur = QPointF(event.pos())
                rect = QRectF(start, cur).normalized()
                self._zoom_rubber_band.setGeometry(rect.toRect())
            return

        if self._pan_active and self._pan_start_pos is not None:
            if not self._axis_cfg_x.auto_scale:
                return
            plot_rect, _, _ = self.getPlotRect()
            if plot_rect.width() > 0:
                dx_px = event.pos().x() - self._pan_start_pos.x()
                x_min0, x_max0 = self._pan_start_view
                x_range = x_max0 - x_min0
                dx_data = -dx_px / plot_rect.width() * x_range
                new_min = x_min0 + dx_data
                new_max = x_max0 + dx_data
                new_min, new_max = self._clampViewToSimulationBounds(new_min, new_max)
                self._view_x_min = new_min
                self._view_x_max = new_max
                self._last_x_state = None
                self.hover_index = None
                self.update()
                self.viewChanged.emit()
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
    curveSettingsChanged = pyqtSignal(list)
    clearAllRequested = pyqtSignal()

    def __init__(self, iface, parent=None):
        super(QGISRedTimeSeriesDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        self._toolbarWidget = None
        self._resultsDock = None
        self._lastResultsTimeText = ""

        self._initToolbar()
        self._updateMinimumWidthForDockTitle()
        
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)
        self.plot.seriesOrderChanged.connect(self.seriesReordered)
        self.plot.seriesOrderChanged.connect(self._onSeriesOrderChanged)
        self.plot.seriesRemoved.connect(self.seriesRemoved)
        self.plot.seriesEmphasisChanged.connect(self.seriesEmphasisChanged)
        self.plot.viewChanged.connect(self._onPlotViewChanged)

        self.lblTitle.hide()
        
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def _updateMinimumWidthForDockTitle(self) -> None:
        title = (self.windowTitle() or "").strip()
        if not title:
            return
        fm = QFontMetrics(self.font())
        extra = 260
        min_w = int(fm.horizontalAdvance(title) + extra)
        if min_w > 0:
            self.setMinimumWidth(max(int(self.minimumWidth()), min_w))

    def changeEvent(self, event) -> None:
        try:
            if event is not None and event.type() == QEvent.Type.LanguageChange:
                self.retranslateUi(self)
                self._updateMinimumWidthForDockTitle()
        except Exception:
            pass
        super(QGISRedTimeSeriesDock, self).changeEvent(event)

    def event(self, event):
        try:
            if event is not None and event.type() == QEvent.Type.WindowTitleChange:
                self._updateMinimumWidthForDockTitle()
        except Exception:
            pass
        return super(QGISRedTimeSeriesDock, self).event(event)

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

            self.btnPan = _make_btn("btnPanTimeSeries", "mActionPan.svg", self.tr("Pan"), checkable=True)
            self.btnPan.toggled.connect(self._onPanToggled)
            hl.addWidget(self.btnPan, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomWindow = _make_btn("btnZoomWindowTimeSeries", "mActionZoomToLayer.svg", self.tr("Zoom window"), checkable=True)
            self.btnZoomWindow.toggled.connect(self._onZoomWindowToggled)
            hl.addWidget(self.btnZoomWindow, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomIn = _make_btn("btnZoomInTimeSeries", "mActionZoomIn.svg", self.tr("Zoom in"))
            self.btnZoomIn.clicked.connect(self._onZoomInClicked)
            hl.addWidget(self.btnZoomIn, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomOut = _make_btn("btnZoomOutTimeSeries", "mActionZoomOut.svg", self.tr("Zoom out"))
            self.btnZoomOut.clicked.connect(self._onZoomOutClicked)
            hl.addWidget(self.btnZoomOut, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnFit = _make_btn("btnFitTimeSeries", "mActionZoomFullExtent.svg", self.tr("Zoom to full extent"))
            self.btnFit.clicked.connect(self._onFitClicked)
            hl.addWidget(self.btnFit, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnSyncCursor = QToolButton(container)
            self.btnSyncCursor.setObjectName("btnSyncCursorTimeSeries")
            sync_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "images", "iconTimeSeries.svg"))
            self.btnSyncCursor.setIcon(QIcon(sync_icon_path))
            self.btnSyncCursor.setToolTip(self.tr("Sync cursor with Results panel"))
            self.btnSyncCursor.setAutoRaise(True)
            self.btnSyncCursor.setCheckable(True)
            self.btnSyncCursor.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.btnSyncCursor.setIconSize(QSize(16, 16))
            self.btnSyncCursor.setFixedSize(QSize(22, 22))
            self.btnSyncCursor.setStyleSheet(btn_style)
            self.btnSyncCursor.toggled.connect(self._onSyncCursorToggled)
            hl.addWidget(self.btnSyncCursor, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnAxes = _make_btn("btnAxesTimeSeries", "mActionOptions.svg", self.tr("Chart options"))
            self.btnAxes.clicked.connect(self._onAxisOptionsClicked)
            hl.addWidget(self.btnAxes, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnExportImage = _make_btn("btnExportImageTimeSeries", "mActionSaveMapAsImage.svg", self.tr("Export chart as image"))
            self.btnExportImage.clicked.connect(self._onExportImageClicked)
            hl.addWidget(self.btnExportImage, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnExportCsv = QToolButton(container)
            self.btnExportCsv.setObjectName("btnExportCsvTimeSeries")
            csv_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "images", "iconExportResultsToCsv.svg"))
            self.btnExportCsv.setIcon(QIcon(csv_icon_path))
            self.btnExportCsv.setToolTip(self.tr("Export chart points to CSV"))
            self.btnExportCsv.setAutoRaise(True)
            self.btnExportCsv.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.btnExportCsv.setIconSize(QSize(16, 16))
            self.btnExportCsv.setFixedSize(QSize(22, 22))
            self.btnExportCsv.setStyleSheet(btn_style)
            self.btnExportCsv.clicked.connect(self._onExportCsvClicked)
            hl.addWidget(self.btnExportCsv, 0, Qt.AlignmentFlag.AlignLeft)

            hl.addWidget(self.btnClearAll, 0, Qt.AlignmentFlag.AlignLeft)
            hl.addStretch(1)

            try:
                self.verticalLayout.insertWidget(0, container)
            except Exception:
                self.verticalLayout.addWidget(container)
        except Exception:
            return

    def _onPanToggled(self, checked: bool) -> None:
        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and checked and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        self.plot.setPanMode(checked)

    def _onZoomWindowToggled(self, checked: bool) -> None:
        if hasattr(self, "btnPan") and self.btnPan is not None and checked and self.btnPan.isChecked():
            self.btnPan.setChecked(False)
        self.plot.setZoomWindowMode(checked)

    def _onZoomInClicked(self) -> None:
        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        self.plot.zoomIn()

    def _onZoomOutClicked(self) -> None:
        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        self.plot.zoomOut()

    def _onFitClicked(self) -> None:
        self.plot.resetView()
        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        if hasattr(self, "btnPan") and self.btnPan.isChecked():
            self.btnPan.setChecked(False)

    def _onSyncCursorToggled(self, checked: bool) -> None:
        if checked:
            if self._resultsDock is None:
                self._showMessage(self.tr("Results panel is not available"), level=1)
                if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None:
                    self.btnSyncCursor.setChecked(False)
                return
            self._syncCurrentResultsTime()
        else:
            self.plot.clearSyncedCursor()

    def _onAxisOptionsClicked(self) -> None:
        # Keep a stable top-level parent even when this dock is floating.
        dlg = TimeSeriesAxisOptionsDialog(self.plot, self.iface.mainWindow())
        if dlg.exec() == DIALOG_ACCEPTED:
            self._emitCurveSettingsChanged()
            if not self.plot._axis_cfg_x.auto_scale:
                if hasattr(self, "btnPan") and self.btnPan.isChecked():
                    self.btnPan.setChecked(False)
                self.plot.setPanMode(False)
                if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and self.btnZoomWindow.isChecked():
                    self.btnZoomWindow.setChecked(False)
                self.plot.setZoomWindowMode(False)
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def _showMessage(self, text: str, level: int = 0, duration: int = 5) -> None:
        QGISRedUIUtils.showGlobalMessage(self.iface, text, level=level, duration=duration)

    def connectResultsDock(self, results_dock) -> None:
        if self._resultsDock is results_dock:
            self._syncCurrentResultsTime()
            self._updateClearToolbarVisibility()
            return

        if self._resultsDock is not None:
            try:
                self._resultsDock.timeTextChanged.disconnect(self._onResultsTimeTextChanged)
            except Exception:
                pass

        self._resultsDock = results_dock
        if self._resultsDock is not None:
            try:
                self._resultsDock.timeTextChanged.connect(self._onResultsTimeTextChanged)
            except Exception:
                pass
            self._syncCurrentResultsTime()
        self._updateClearToolbarVisibility()

    def disconnectResultsDock(self) -> None:
        if self._resultsDock is not None:
            try:
                self._resultsDock.timeTextChanged.disconnect(self._onResultsTimeTextChanged)
            except Exception:
                pass
        self._resultsDock = None
        self._lastResultsTimeText = ""
        self.plot.clearSyncedCursor()
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self.btnSyncCursor.setChecked(False)
        self._updateClearToolbarVisibility()

    def _onResultsTimeTextChanged(self, time_text: str) -> None:
        self._lastResultsTimeText = time_text or ""
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._applySyncedTimeText(self._lastResultsTimeText)

    def _syncCurrentResultsTime(self) -> None:
        time_text = self._lastResultsTimeText
        if not time_text and self._resultsDock is not None:
            try:
                time_text = self._resultsDock.lbTime.text()
            except Exception:
                time_text = ""
        self._lastResultsTimeText = time_text or ""
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._applySyncedTimeText(self._lastResultsTimeText)
        else:
            self.plot.clearSyncedCursor()

    def _applySyncedTimeText(self, time_text: str) -> None:
        hours = self._parseResultsTimeTextToHours(time_text)
        if hours is None:
            self.plot.clearSyncedCursor()
            return
        self.plot.setSyncedCursorTimeHours(hours)

    def _parseResultsTimeTextToHours(self, time_text: str):
        text = (time_text or "").strip()
        if not text:
            return None
        if self._resultsDock is not None:
            try:
                if text == self._resultsDock.lbl_singlePeriod:
                    return 0.0
            except Exception:
                pass
        if text == self.tr("Single Period"):
            return 0.0

        try:
            days = 0
            hms_text = text
            if "d" in text:
                parts = text.split()
                if len(parts) < 2:
                    return None
                days = int(parts[0].replace("d", ""))
                hms_text = parts[1]
            hms = hms_text.split(":")
            if len(hms) != 3:
                return None
            total_seconds = days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
            return total_seconds / 3600.0
        except Exception:
            return None

    def _safeExportBaseName(self) -> str:
        title = (getattr(self.plot, "title", "") or "").strip()
        if not title:
            title = self.tr("Time evolution curves")
        safe = []
        for ch in title:
            if ch.isalnum() or ch in ("-", "_"):
                safe.append(ch)
            elif ch.isspace():
                safe.append("_")
        name = "".join(safe).strip("_")
        return name or "time_series"

    def _selectedFilterExtension(self, selected_filter: str) -> str:
        if ".svg" in selected_filter:
            return ".svg"
        if ".jpg" in selected_filter or ".jpeg" in selected_filter:
            return ".jpg"
        if ".bmp" in selected_filter:
            return ".bmp"
        if ".tif" in selected_filter or ".tiff" in selected_filter:
            return ".tif"
        return ".png"

    def _pathWithExtension(self, path: str, selected_filter: str) -> str:
        root, ext = os.path.splitext(path)
        if ext:
            return path
        return path + self._selectedFilterExtension(selected_filter)

    def _onExportImageClicked(self) -> None:
        if not self._plotHasCurves():
            self._showMessage(self.tr("No curves to export"), level=1)
            return

        filters = [
            self.tr("PNG image (*.png)"),
            self.tr("JPEG image (*.jpg *.jpeg)"),
            self.tr("BMP image (*.bmp)"),
            self.tr("TIFF image (*.tif *.tiff)"),
        ]
        if QSvgGenerator is not None:
            filters.append(self.tr("SVG image (*.svg)"))

        default_path = os.path.join(os.path.expanduser("~"), self._safeExportBaseName() + ".png")
        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export chart as image"),
            default_path,
            ";;".join(filters),
        )
        if not path:
            return
        path = self._pathWithExtension(path, selected_filter)

        if path.lower().endswith(".svg"):
            if QSvgGenerator is None:
                self._showMessage(self.tr("SVG export is not available"), level=1)
                return
            generator = QSvgGenerator()
            generator.setFileName(path)
            generator.setSize(self.plot.size())
            generator.setViewBox(QRect(0, 0, self.plot.width(), self.plot.height()))
            generator.setTitle((getattr(self.plot, "title", "") or self.tr("Time evolution curves")).strip())
            painter = QPainter(generator)
            self.plot.render(painter)
            painter.end()
        else:
            pixmap = QPixmap(self.plot.size())
            pixmap.fill(Qt.GlobalColor.white)
            painter = QPainter(pixmap)
            self.plot.render(painter)
            painter.end()
            if not pixmap.save(path):
                self._showMessage(self.tr("The chart image could not be exported"), level=2)
                return

        self._showMessage(self.tr("Chart image exported"), level=3)

    def _seriesElementInfo(self, series_dict):
        series_key = str(series_dict.get("series_key") or "")
        parts = series_key.split(":")
        if len(parts) >= 4:
            category = parts[0]
            element_id = parts[3]
        else:
            category = str(series_dict.get("legend_type") or "")
            element_id = str(series_dict.get("label") or "")

        type_mapping = {
            "qgisred_junctions": self.tr("Junction"),
            "qgisred_tanks": self.tr("Tank"),
            "qgisred_reservoirs": self.tr("Reservoir"),
            "qgisred_pipes": self.tr("Pipe"),
            "qgisred_valves": self.tr("Valve"),
            "qgisred_pumps": self.tr("Pump"),
            "Node": self.tr("Node"),
            "Link": self.tr("Link"),
        }
        legend_type = str(series_dict.get("legend_type") or category)
        return element_id, type_mapping.get(legend_type, type_mapping.get(category, legend_type))

    def _formatCsvValue(self, value, decimal_sep: str, decimal_places=None) -> str:
        if value is None:
            return ""
        try:
            f = float(value)
            if not math.isfinite(f):
                return ""
            if decimal_places is None:
                text = format(f, ".12g")
            else:
                dec = max(0, int(decimal_places))
                text = f"{f:.{dec}f}"
        except Exception:
            text = str(value)
        if decimal_sep != ".":
            text = text.replace(".", decimal_sep)
        return text

    def _formatCsvCivilTime(self, hours) -> str:
        try:
            total_seconds = int(round(float(hours) * 3600.0))
        except Exception:
            return ""
        seconds_in_day = total_seconds % 86400
        h = seconds_in_day // 3600
        m = (seconds_in_day % 3600) // 60
        s = seconds_in_day % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def _seriesCsvDecimalPlaces(self, series_dict):
        if series_dict.get("y_categorical_labels"):
            return None

        series_key = str(series_dict.get("series_key") or "")
        parts = series_key.split(":")
        if len(parts) < 3:
            return None

        category = parts[0]
        prop_internal = parts[2]
        if category not in ("Node", "Link") or not prop_internal:
            return None

        try:
            return QGISRedFieldUtils().getResultPropertyDecimals(category, prop_internal)
        except Exception:
            return None

    def _seriesDisplayValue(self, series_dict, value) -> object:
        labels = series_dict.get("y_categorical_labels")
        if labels:
            try:
                return labels[int(round(float(value)))]
            except Exception:
                return value
        return value

    def _onExportCsvClicked(self) -> None:
        if not self._plotHasCurves():
            self._showMessage(self.tr("No curves to export"), level=1)
            return

        default_path = os.path.join(os.path.expanduser("~"), self._safeExportBaseName() + ".csv")
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            self.tr("Export chart points to CSV"),
            default_path,
            self.tr("CSV file (*.csv)"),
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"

        list_sep, decimal_sep = get_regional_separators()
        rows = []
        for s in self.plot.series or []:
            if not bool(s.get("visible", True)):
                continue
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            n = min(len(xs), len(ys))
            if n <= 0:
                continue
            element_id, element_type = self._seriesElementInfo(s)
            magnitude = (s.get("magnitude") or self.plot.y_label or "").strip()
            series_label = (s.get("label") or "").strip()
            value_decimals = self._seriesCsvDecimalPlaces(s)
            for i in range(n):
                rows.append([
                    element_id,
                    element_type,
                    magnitude,
                    series_label,
                    self._formatCsvValue(xs[i], decimal_sep),
                    self._formatCsvCivilTime(xs[i]),
                    self._formatCsvValue(self._seriesDisplayValue(s, ys[i]), decimal_sep, value_decimals),
                ])

        if not rows:
            self._showMessage(self.tr("No chart points to export"), level=1)
            return

        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=list_sep)
                writer.writerow([
                    self.tr("Id"),
                    self.tr("Type"),
                    self.tr("Magnitude"),
                    self.tr("Curve Name"),
                    self.tr("Time (h)"),
                    self.tr("Civil Time"),
                    self.tr("Value"),
                ])
                writer.writerows(rows)
        except Exception:
            self._showMessage(self.tr("The CSV file could not be exported"), level=2)
            return

        self._showMessage(self.tr("Chart points exported to CSV"), level=3)

    def _emitCurveSettingsChanged(self) -> None:
        settings = []
        for s in self.plot.series or []:
            key = str(s.get("series_key") or "").strip()
            if not key:
                continue
            settings.append({
                "series_key": key,
                "label": (s.get("label") or "").strip(),
                "color": s.get("color"),
                "line_style": s.get("line_style") or "solid",
                "line_width": s.get("line_width") or 2.0,
                "show_markers": bool(s.get("show_markers", False)),
                "marker_symbol": s.get("marker_symbol") or "circle",
                "marker_size": s.get("marker_size") or 6,
                "marker_color": s.get("marker_color") or s.get("color"),
                "show_point_values": bool(s.get("show_point_values", False)),
                "visible": bool(s.get("visible", True)),
                "muted": bool(s.get("muted", False)),
                "highlighted": bool(s.get("highlighted", False)),
                "emphasis_mode": s.get("emphasis_mode") or "normal",
                "legend_font_family": s.get("legend_font_family") or "",
                "legend_font_size": s.get("legend_font_size") or 8,
            })
        self.curveSettingsChanged.emit(settings)

    def _updatePanAvailability(self) -> None:
        if not hasattr(self, "btnPan") or self.btnPan is None:
            return
        if not self._plotHasCurves():
            self.btnPan.setEnabled(False)
        elif not getattr(self.plot, "_axis_cfg_x", None) or not bool(self.plot._axis_cfg_x.auto_scale):
            self.btnPan.setEnabled(False)
        else:
            self.btnPan.setEnabled(bool(self._plotIsZoomed()))

        if not self.btnPan.isEnabled() and self.btnPan.isChecked():
            self.btnPan.setChecked(False)
            self.plot.setPanMode(False)

        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None:
            self.btnZoomWindow.setEnabled(bool(self._plotHasCurves()) and bool(getattr(self.plot, "_axis_cfg_x", None) and self.plot._axis_cfg_x.auto_scale))
            if not self.btnZoomWindow.isEnabled() and self.btnZoomWindow.isChecked():
                self.btnZoomWindow.setChecked(False)
                self.plot.setZoomWindowMode(False)

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

    def _plotIsZoomed(self) -> bool:
        return (getattr(self.plot, "_view_x_min", None) is not None) and (getattr(self.plot, "_view_x_max", None) is not None)

    def _updateClearToolbarVisibility(self) -> None:
        if self._toolbarWidget is None:
            return
        self._toolbarWidget.setVisible(True)
        has_curves = self._plotHasCurves()
        auto_scale_x = bool(getattr(self.plot, "_axis_cfg_x", None) and self.plot._axis_cfg_x.auto_scale)
        is_zoomed = self._plotIsZoomed()
        for btn_name in ("btnClearAll", "btnZoomIn", "btnZoomOut", "btnFit"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                if btn_name == "btnClearAll":
                    btn.setEnabled(bool(has_curves))
                elif btn_name == "btnZoomOut":
                    btn.setEnabled(bool(has_curves and auto_scale_x and is_zoomed))
                else:
                    btn.setEnabled(bool(has_curves and auto_scale_x))
        for btn_name in ("btnAxes", "btnExportImage", "btnExportCsv"):
            btn = getattr(self, btn_name, None)
            if btn is not None:
                btn.setEnabled(bool(has_curves))
        sync_btn = getattr(self, "btnSyncCursor", None)
        if sync_btn is not None:
            sync_btn.setEnabled(bool(has_curves and self._resultsDock is not None))
            if not sync_btn.isEnabled() and sync_btn.isChecked():
                sync_btn.setChecked(False)

    def _onPlotViewChanged(self) -> None:
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def _onSeriesOrderChanged(self, _order) -> None:
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._syncCurrentResultsTime()
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def updatePlotSeries(self, series, title, x_label, y_label):
        self.plot.setSeries(series, title, x_label, y_label)
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._syncCurrentResultsTime()
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()
