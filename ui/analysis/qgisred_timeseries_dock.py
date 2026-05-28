# -*- coding: utf-8 -*-
import csv
import math
import os
from typing import List
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QRubberBand,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from qgis.PyQt.QtCore import QCoreApplication, QEvent, Qt, QPointF, QRect, QRectF, pyqtSignal, QSize
from qgis.PyQt.QtGui import QColor, QFont, QPainter, QFontMetrics, QIcon, QPixmap
from qgis.PyQt import uic
from qgis.core import QgsApplication

from ...compat import DIALOG_ACCEPTED
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils

from .qgisred_timeseries_axis_dialog import TimeSeriesAxisOptionsDialog
from .timeseries_axis_settings import default_axis_settings, default_general_settings
from .timeseries_plot_layout import PlotLayoutCalculator
from .timeseries_legend_interaction import LegendInteractionController
from .timeseries_plot_renderer import TimeSeriesPlotRenderer
from .timeseries_plot_style import DEFAULT_SERIES_COLOR, LEGEND_ICON_SIZE, LEGEND_ROW_GAP, PLOT_TOP_PAD, qfont
from .timeseries_time_utils import (
    civil_time_parts,
    format_civil_time,
    format_elapsed_time,
    simulation_start_clock_seconds,
)

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
    zoomWindowModeChanged = pyqtSignal(bool)
    cursorTimeChanged = pyqtSignal(float)

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
        self._left_axis_active = True
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
        self._start_clock_seconds = 0
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
        gen = getattr(self, "_general_cfg", None)
        title = ""
        if gen is not None and (getattr(gen, "title", "") or "").strip():
            title = (gen.title or "").strip()
        if not title:
            title = (self.title or "").strip()
        if not title:
            title = self.tr("Time evolution curves")
        if gen is not None:
            title_size = max(5, min(int(getattr(gen, "title_font_size", 10) or 10), 48))
            title_font = QFont(gen.resolved_title_font_family(), title_size)
            title_font.setBold(True)
        else:
            title_font = qfont(10, bold=True)
        title_w = QFontMetrics(title_font).horizontalAdvance(title)
        pad = 24
        min_w = max(int(self._base_min_w), int(title_w + pad))
        try:
            cur_min_w = int(self.minimumWidth())
        except Exception:
            cur_min_w = 0
        if cur_min_w == min_w:
            return
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
            "marker_hollow": True,
            "show_point_values": False,
            "legend_font_family": "",
            "legend_font_size": 8,
            "series_key": series_label or "",
        }]
        self._y_label_left = self.y_label
        self._y_label_right = ""
        self._y_magnitudes_left = [self.y_label] if (self.y_label or "").strip() else []
        self._y_magnitudes_right = []
        self._left_axis_active = bool(self._y_magnitudes_left)
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
            if "marker_hollow" not in s:
                s["marker_hollow"] = True
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

    def _magnitude_axis(self, magnitude: str) -> str:
        mag = (magnitude or "").strip()
        for s in self.series:
            if (s.get("magnitude") or "").strip() == mag:
                axis = (s.get("y_axis") or "").strip().lower()
                if axis in ("left", "right"):
                    return axis
        return "left"

    def _assignYAxisByMagnitude(self) -> None:
        magnitudes: List[str] = []
        for s in self.series:
            m = (s.get("magnitude") or "").strip()
            if m and m not in magnitudes:
                magnitudes.append(m)

        has_explicit = any((s.get("y_axis") or "").strip().lower() in ("left", "right") for s in self.series)
        if not has_explicit and magnitudes:
            left_mag = magnitudes[0]
            right_mags = set(magnitudes[1:])
            for s in self.series:
                m = (s.get("magnitude") or "").strip()
                s["y_axis"] = "right" if m in right_mags else "left"
        else:
            for s in self.series:
                axis = (s.get("y_axis") or "").strip().lower()
                s["y_axis"] = axis if axis in ("left", "right") else "left"

        left_mags: List[str] = []
        right_mags: List[str] = []
        seen_left = set()
        seen_right = set()
        for mag in magnitudes:
            if self._magnitude_axis(mag) == "right":
                if mag not in seen_right:
                    right_mags.append(mag)
                    seen_right.add(mag)
            elif mag not in seen_left:
                left_mags.append(mag)
                seen_left.add(mag)

        if not left_mags and not right_mags and (self.y_label or "").strip():
            left_mags = [(self.y_label or "").strip()]

        self._y_magnitudes_left = left_mags
        self._y_magnitudes_right = right_mags
        self._y_label_left = ", ".join(left_mags)
        self._y_label_right = ", ".join(right_mags)
        self._left_axis_active = bool(left_mags)
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
            if not self._seriesIsDrawn(s):
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

    def _seriesIsDrawn(self, series_dict) -> bool:
        return bool(series_dict.get("visible", True)) or bool(series_dict.get("show_markers", False))

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
        legend_pos = (getattr(gen, "legend_position", "") or "right").strip() if gen is not None else "right"
        if legend_pos in ("top", "bottom"):
            return max(0, int(self.width() - self.margin_left - self.margin_right))
        sym = int(getattr(gen, "legend_symbol_size", LEGEND_ICON_SIZE) or LEGEND_ICON_SIZE) if gen is not None else LEGEND_ICON_SIZE
        sym = max(6, min(sym, 24))
        if legend_pos in ("right", "left"):
            item_col_w = max((self._legendItemWidth(series_idx, label, sym) for _mag, items in groups for series_idx, _color, label, _legend_type in items), default=40.0)
            header_w = max((QFontMetrics(qfont(8, bold=True)).horizontalAdvance(str(mag)) + 12 for mag, _items in groups), default=40)
            cols = 2 if self._legendSideNeedsTwoColumns() else 1
            gap = 8
            return int(max(float(header_w), cols * float(item_col_w) + (cols - 1) * gap) + 12)
        cols = 1
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

    def _legendItemWidth(self, series_idx, label, sym: int) -> float:
        row_font = qfont(8)
        try:
            if 0 <= int(series_idx) < len(self.series):
                s = self.series[int(series_idx)]
                fam = (s.get("legend_font_family") or "").strip()
                size = max(6, min(int(s.get("legend_font_size") or 8), 32))
                row_font = qfont(size)
                if fam:
                    row_font.setFamily(fam)
        except Exception:
            row_font = qfont(8)
        btn_w = 10
        return float(sym + 6 + QFontMetrics(row_font).horizontalAdvance(label) + btn_w + 8)

    def _legendHorizontalGroupRows(self, mag_title, items, frame_w: float, sym: int) -> int:
        frame_w = max(1.0, float(frame_w))
        gap = 8.0
        header_w = float(QFontMetrics(qfont(8, bold=True)).horizontalAdvance(str(mag_title)) + 12)
        item_widths = [self._legendItemWidth(series_idx, label, sym) for series_idx, _color, label, _legend_type in items]
        inline_w = header_w + sum(item_widths) + gap * len(item_widths)
        if inline_w <= frame_w:
            return 1
        item_rows = 0
        cur_w = 0.0
        for item_w in item_widths:
            if cur_w <= 0:
                item_rows += 1
                cur_w = item_w
            elif cur_w + gap + item_w > frame_w:
                item_rows += 1
                cur_w = item_w
            else:
                cur_w += gap + item_w
        return max(2, 1 + item_rows)

    def _legendSideAvailableHeight(self) -> float:
        top = float(getattr(self, "margin_top", 40) + PLOT_TOP_PAD)
        bottom = float(getattr(self, "margin_bottom", 40))
        return max(float(_LEGEND_ROW_GAP), float(self.height()) - top - bottom)

    def _legendSideNeedsTwoColumns(self) -> bool:
        groups = self._legendGroups()
        if not groups:
            return False
        usable_h = max(float(_LEGEND_ROW_GAP), self._legendSideAvailableHeight() - 20.0)
        max_rows = max(1, int(usable_h // float(_LEGEND_ROW_GAP)))
        single_rows = sum(1 + len(items) + 1 for _mag, items in groups)
        return single_rows > max_rows

    def _legendRequiredHeight(self) -> int:
        groups = self._legendGroups()
        if not groups:
            return 0
        gen = getattr(self, "_general_cfg", None)
        sym = int(getattr(gen, "legend_symbol_size", LEGEND_ICON_SIZE) or LEGEND_ICON_SIZE) if gen is not None else LEGEND_ICON_SIZE
        sym = max(6, min(sym, 24))
        legend_pos = (getattr(gen, "legend_position", "") or "right").strip() if gen is not None else "right"
        if legend_pos in ("top", "bottom"):
            available_w = max(1.0, float(self._legendRequiredWidth()))
            frame_w = available_w / float(max(1, len(groups)))
            max_rows = max(self._legendHorizontalGroupRows(mag, items, frame_w, sym) for mag, items in groups)
            top_pad = 10
            bottom_pad = 10
            return int(top_pad + max_rows * _LEGEND_ROW_GAP + bottom_pad)
        cols = 1

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
            if self._seriesIsDrawn(s) and bool(s.get("highlighted", False)):
                return i
        for i, s in enumerate(self.series):
            if self._seriesIsDrawn(s) and not bool(s.get("muted", False)):
                return i
        for i, s in enumerate(self.series):
            if self._seriesIsDrawn(s):
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
        try:
            self.cursorTimeChanged.emit(float(value))
        except Exception:
            pass

    def clearSyncedCursor(self) -> None:
        if self._synced_cursor_time_hours is not None:
            self._synced_cursor_time_hours = None
            self.update()

    def setStartClockSeconds(self, seconds) -> None:
        try:
            value = int(seconds) % 86400
        except Exception:
            value = 0
        if self._start_clock_seconds == value:
            return
        self._start_clock_seconds = value
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
        changed = self._zoom_window_mode != bool(enabled)
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
        if changed:
            self.zoomWindowModeChanged.emit(self._zoom_window_mode)

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
            self.setZoomWindowMode(False)
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
                try:
                    self.cursorTimeChanged.emit(float(xs[best_idx]))
                except Exception:
                    pass
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
        self._tableVisible = False
        self._syncTableToCursor = False
        self._syncCursorToTable = False
        self._tableSeconds = []
        self._tableSecondsToRow = {}
        self._tableUpdatingSelection = False
        self._plotUpdatingCursor = False
        self._tableAutoSizedSignature = None

        self._initToolbar()
        self._updateMinimumWidthForDockTitle()
        
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        self._initPlotAndTableLayout()
        self.plot.seriesOrderChanged.connect(self.seriesReordered)
        self.plot.seriesOrderChanged.connect(self._onSeriesOrderChanged)
        self.plot.seriesRemoved.connect(self.seriesRemoved)
        self.plot.seriesEmphasisChanged.connect(self.seriesEmphasisChanged)
        self.plot.viewChanged.connect(self._onPlotViewChanged)
        self.plot.zoomWindowModeChanged.connect(self._onPlotZoomWindowModeChanged)
        self.plot.cursorTimeChanged.connect(self._onPlotCursorTimeChanged)

        self.lblTitle.hide()
        
        QGISRedUIUtils.applyDockStyle(self, "#0097A7", backgroundColor="white")
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
                btn.setIcon(icon)
                btn.setToolTip(tooltip)
                btn.setAutoRaise(True)
                btn.setCheckable(checkable)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
                btn.setIconSize(QSize(16, 16))
                btn.setFixedSize(QSize(22, 22))
                btn.setStyleSheet(btn_style)
                return btn

            self.btnPan = _make_btn("btnPanTimeSeries", QIcon(":/images/iconTsPan.svg"), self.tr("Pan"), checkable=True)
            self.btnPan.toggled.connect(self._onPanToggled)
            hl.addWidget(self.btnPan, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomWindow = _make_btn("btnZoomWindowTimeSeries", QIcon(":/images/iconTsZoomWindow.svg"), self.tr("Zoom window"), checkable=True)
            self.btnZoomWindow.toggled.connect(self._onZoomWindowToggled)
            hl.addWidget(self.btnZoomWindow, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomIn = _make_btn("btnZoomInTimeSeries", QIcon(":/images/iconTsZoomIn.svg"), self.tr("Zoom in"))
            self.btnZoomIn.clicked.connect(self._onZoomInClicked)
            hl.addWidget(self.btnZoomIn, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnZoomOut = _make_btn("btnZoomOutTimeSeries", QIcon(":/images/iconTsZoomOut.svg"), self.tr("Zoom out"))
            self.btnZoomOut.clicked.connect(self._onZoomOutClicked)
            hl.addWidget(self.btnZoomOut, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnFit = _make_btn("btnFitTimeSeries", QIcon(":/images/iconTsFit.svg"), self.tr("Zoom to full extent"))
            self.btnFit.clicked.connect(self._onFitClicked)
            hl.addWidget(self.btnFit, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnSyncCursor = _make_btn("btnSyncCursorTimeSeries", QIcon(":/images/iconTsSyncCursor.svg"), self.tr("Sync cursor with Results panel"), checkable=True)
            self.btnSyncCursor.toggled.connect(self._onSyncCursorToggled)
            hl.addWidget(self.btnSyncCursor, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnAxes = _make_btn("btnAxesTimeSeries", QIcon(":/images/iconTsAxes.svg"), self.tr("Chart options"))
            self.btnAxes.clicked.connect(self._onAxisOptionsClicked)
            hl.addWidget(self.btnAxes, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnExportImage = _make_btn("btnExportImageTimeSeries", QIcon(":/images/iconTsExportImage.svg"), self.tr("Export chart as image"))
            self.btnExportImage.clicked.connect(self._onExportImageClicked)
            hl.addWidget(self.btnExportImage, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnExportCsv = _make_btn("btnExportCsvTimeSeries", QIcon(":/images/iconTsExportCsv.svg"), self.tr("Export chart points to CSV"))
            self.btnExportCsv.clicked.connect(self._onExportCsvClicked)
            hl.addWidget(self.btnExportCsv, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnToggleTable = _make_btn("btnToggleTableTimeSeries", QIcon(":/images/iconTsExportCsv.svg"), self.tr("Show/Hide values table"), checkable=True)
            self.btnToggleTable.toggled.connect(self._onToggleTableToggled)
            hl.addWidget(self.btnToggleTable, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnSyncTable = _make_btn("btnSyncTableTimeSeries", QIcon(":/images/iconTsSyncCursor.svg"), self.tr("Sync cursor with selected table row"), checkable=True)
            self.btnSyncTable.toggled.connect(self._onSyncTableToggled)
            self.btnSyncTable.setEnabled(False)
            hl.addWidget(self.btnSyncTable, 0, Qt.AlignmentFlag.AlignLeft)

            self.btnClearAll = _make_btn("btnClearAllTimeSeries", QIcon(":/images/iconTsClearAll.svg"), self.tr("Clear all curves"))
            self.btnClearAll.clicked.connect(self.clearAllRequested)
            hl.addWidget(self.btnClearAll, 0, Qt.AlignmentFlag.AlignLeft)
            hl.addStretch(1)

            try:
                self.verticalLayout.insertWidget(0, container)
            except Exception:
                self.verticalLayout.addWidget(container)
        except Exception:
            return

    def _initPlotAndTableLayout(self) -> None:
        try:
            splitter = QSplitter(Qt.Orientation.Horizontal, self.chartContainer)
            splitter.setChildrenCollapsible(False)
            self._splitter = splitter

            left = QWidget(splitter)
            left_layout = QVBoxLayout(left)
            left_layout.setContentsMargins(0, 0, 0, 0)
            left_layout.addWidget(self.plot)
            left.setLayout(left_layout)
            self._plotPane = left

            table = QTableWidget(splitter)
            table.setObjectName("timeSeriesValuesTable")
            table.setAlternatingRowColors(True)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSortingEnabled(False)
            table.verticalHeader().setVisible(False)
            # Keep all columns sized by their own content/title; do not stretch
            # the last one (it made the third column look disproportionately wide).
            table.horizontalHeader().setStretchLastSection(False)
            try:
                table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            except Exception:
                pass
            table.itemSelectionChanged.connect(self._onTableSelectionChanged)
            self._table = table
            table.hide()

            layout = QVBoxLayout(self.chartContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(splitter)
            self.chartContainer.setLayout(layout)
        except Exception:
            layout = QVBoxLayout(self.chartContainer)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.plot)
            self.chartContainer.setLayout(layout)
            self._splitter = None
            self._plotPane = None
            self._table = None

    def _onToggleTableToggled(self, checked: bool) -> None:
        self._setTableVisible(bool(checked))

    def _setTableVisible(self, visible: bool) -> None:
        self._tableVisible = bool(visible)
        table = getattr(self, "_table", None)
        if table is None:
            return
        if self._tableVisible:
            table.show()
            try:
                self._fitTablePaneToContents()
            except Exception:
                pass
            btn_sync = getattr(self, "btnSyncTable", None)
            if btn_sync is not None and btn_sync.isEnabled() and not btn_sync.isChecked():
                btn_sync.setChecked(True)
        else:
            table.hide()
        self._updateTableSyncAvailability()

    def _onSyncTableToggled(self, checked: bool) -> None:
        self._syncTableToCursor = bool(checked)
        self._syncCursorToTable = bool(checked)
        if self._syncTableToCursor:
            self._onTableSelectionChanged()

    def _updateTableSyncAvailability(self) -> None:
        btn = getattr(self, "btnSyncTable", None)
        if btn is None:
            return
        can = bool(self._tableVisible and self._plotHasCurves() and getattr(self, "_table", None) is not None and bool(self._tableSeconds))
        btn.setEnabled(can)
        if can and self._tableVisible and not btn.isChecked():
            btn.setChecked(True)
        if not can and btn.isChecked():
            btn.setChecked(False)
            self._syncTableToCursor = False
            self._syncCursorToTable = False

    def _tableRequiredWidth(self) -> int:
        table = getattr(self, "_table", None)
        if table is None:
            return 280
        try:
            cols = int(table.columnCount())
        except Exception:
            cols = 0
        if cols <= 0:
            return 280
        total = 0
        for c in range(cols):
            try:
                total += int(table.columnWidth(c))
            except Exception:
                pass
        try:
            total += int(table.frameWidth()) * 2
        except Exception:
            pass
        try:
            total += int(table.verticalScrollBar().sizeHint().width())
        except Exception:
            total += 16
        # Padding for grid + header margins.
        total += 20
        return max(240, total)

    def _fitTablePaneToContents(self) -> None:
        splitter = getattr(self, "_splitter", None)
        if splitter is None:
            return
        total_w = max(1, int(self.width()))
        # Reserve enough width for chart interaction area.
        max_right = max(240, total_w - 280)
        desired_right = min(self._tableRequiredWidth(), max_right)
        desired_left = max(200, total_w - desired_right)
        splitter.setSizes([desired_left, desired_right])

    @staticmethod
    def _format_elapsed_hhmm(hours: float) -> str:
        try:
            total_seconds = int(round(float(hours) * 3600.0))
        except Exception:
            return ""
        sign = "-" if total_seconds < 0 else ""
        abs_s = abs(total_seconds)
        total_h = abs_s // 3600
        mm = (abs_s % 3600) // 60
        return f"{sign}{int(total_h)}:{int(mm):02d}"

    def _format_elapsed_time_col1(self, hours: float) -> str:
        cfg = getattr(self.plot, "_axis_cfg_x", None)
        hour_format = (getattr(cfg, "x_hour_format", "") or "hm").strip()
        if hour_format == "h":
            try:
                h = float(hours)
            except Exception:
                return ""
            if not math.isfinite(h):
                return ""
            return f"{h:.2f}"
        return self._format_elapsed_hhmm(hours)

    def _format_civil_time_col2(self, hours: float) -> str:
        start_clock = int(getattr(self.plot, "_start_clock_seconds", 0) or 0)
        parts = civil_time_parts(hours, start_clock)
        if parts is None:
            return ""
        d, h24, m, s = parts
        suffix = "am" if int(h24) < 12 else "pm"
        h12 = int(h24) % 12 or 12
        if int(s) != 0:
            tod = f"{h12}:{int(m):02d}:{int(s):02d}{suffix}"
        elif int(m) != 0:
            tod = f"{h12}:{int(m):02d}{suffix}"
        else:
            tod = f"{h12}{suffix}"
        return f"{int(d)}d {tod}" if int(d) > 0 else tod

    def _series_column_header(self, series_dict) -> str:
        try:
            element_id, element_type = self._seriesElementInfo(series_dict)
        except Exception:
            element_id, element_type = ("", "")
        magnitude = (series_dict.get("magnitude") or "").strip()
        left = " ".join([t for t in [element_type, element_id] if t]).strip()
        if left and magnitude:
            return f"{left} - {magnitude}"
        return left or magnitude or (series_dict.get("label") or "").strip() or self.tr("Value")

    def _rebuildValuesTable(self) -> None:
        table = getattr(self, "_table", None)
        if table is None:
            return
        splitter = getattr(self, "_splitter", None)
        prev_sizes = None
        if splitter is not None and self._tableVisible:
            try:
                prev_sizes = list(splitter.sizes())
            except Exception:
                prev_sizes = None
        self._tableSeconds = []
        self._tableSecondsToRow = {}

        if not self._plotHasCurves():
            table.setRowCount(0)
            table.setColumnCount(0)
            self._updateTableSyncAvailability()
            return

        base_series = None
        for s in self.plot.series or []:
            if self.plot._seriesIsDrawn(s):
                base_series = s
                break
        if base_series is None:
            table.setRowCount(0)
            table.setColumnCount(0)
            self._updateTableSyncAvailability()
            return

        xs = list(base_series.get("x", []) or [])
        if not xs:
            table.setRowCount(0)
            table.setColumnCount(0)
            self._updateTableSyncAvailability()
            return

        drawn_series = [s for s in (self.plot.series or []) if self.plot._seriesIsDrawn(s)]
        col_count = 2 + len(drawn_series)
        table.setColumnCount(col_count)

        headers = [
            self.tr("Time (h)"),
            self.tr("Time of day"),
        ] + [self._series_column_header(s) for s in drawn_series]
        table.setHorizontalHeaderLabels(headers)
        current_signature = tuple(headers)

        _start_clock_seconds = int(getattr(self.plot, "_start_clock_seconds", 0) or 0)
        table.setRowCount(len(xs))
        for row, xh in enumerate(xs):
            try:
                sec = int(round(float(xh) * 3600.0))
            except Exception:
                sec = None
            if sec is not None:
                self._tableSeconds.append(sec)
                if sec not in self._tableSecondsToRow:
                    self._tableSecondsToRow[sec] = row

            it0 = QTableWidgetItem(self._format_elapsed_time_col1(xh))
            it0.setTextAlignment(int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))
            table.setItem(row, 0, it0)

            _ = _start_clock_seconds
            it1 = QTableWidgetItem(self._format_civil_time_col2(xh))
            it1.setTextAlignment(int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))
            table.setItem(row, 1, it1)

            for j, s in enumerate(drawn_series):
                ys = s.get("y", []) or []
                v = ys[row] if row < len(ys) else None
                display_v = self._seriesDisplayValue(s, v)
                cell_txt = "" if display_v is None else str(display_v)
                item = QTableWidgetItem(cell_txt)
                item.setTextAlignment(int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))
                table.setItem(row, 2 + j, item)

        if current_signature != self._tableAutoSizedSignature:
            try:
                table.resizeColumnsToContents()
            except Exception:
                pass
            self._tableAutoSizedSignature = current_signature
            if self._tableVisible:
                try:
                    self._fitTablePaneToContents()
                    prev_sizes = None
                except Exception:
                    pass

        if prev_sizes:
            try:
                splitter.setSizes(prev_sizes)
            except Exception:
                pass
        self._updateTableSyncAvailability()

    def _onTableSelectionChanged(self) -> None:
        if not self._syncTableToCursor:
            return
        if self._tableUpdatingSelection or self._plotUpdatingCursor:
            return
        table = getattr(self, "_table", None)
        if table is None:
            return
        rows = table.selectionModel().selectedRows() if table.selectionModel() is not None else []
        if not rows:
            return
        try:
            row = int(rows[0].row())
        except Exception:
            return
        if row < 0 or row >= len(self._tableSeconds):
            try:
                base = None
                for s in self.plot.series or []:
                    if self.plot._seriesIsDrawn(s):
                        base = s
                        break
                if base is None:
                    return
                xs = base.get("x", []) or []
                if not (0 <= row < len(xs)):
                    return
                hours = float(xs[row])
            except Exception:
                return
        else:
            try:
                hours = float(self._tableSeconds[row]) / 3600.0
            except Exception:
                return
        self._plotUpdatingCursor = True
        try:
            self.plot.setSyncedCursorTimeHours(hours)
        finally:
            self._plotUpdatingCursor = False

    def _onPlotCursorTimeChanged(self, hours: float) -> None:
        if not (self._tableVisible and self._syncCursorToTable):
            return
        if self._tableUpdatingSelection or self._plotUpdatingCursor:
            return
        table = getattr(self, "_table", None)
        if table is None:
            return
        try:
            sec = int(round(float(hours) * 3600.0))
        except Exception:
            return
        row = self._tableSecondsToRow.get(sec)
        if row is None:
            return
        self._tableUpdatingSelection = True
        try:
            table.selectRow(int(row))
            table.scrollToItem(table.item(int(row), 0), QAbstractItemView.ScrollHint.PositionAtCenter)
        except Exception:
            pass
        finally:
            self._tableUpdatingSelection = False

    def _onPanToggled(self, checked: bool) -> None:
        if hasattr(self, "btnZoomWindow") and self.btnZoomWindow is not None and checked and self.btnZoomWindow.isChecked():
            self.btnZoomWindow.setChecked(False)
        self.plot.setPanMode(checked)

    def _onZoomWindowToggled(self, checked: bool) -> None:
        if hasattr(self, "btnPan") and self.btnPan is not None and checked and self.btnPan.isChecked():
            self.btnPan.setChecked(False)
        self.plot.setZoomWindowMode(checked)

    def _onPlotZoomWindowModeChanged(self, enabled: bool) -> None:
        btn = getattr(self, "btnZoomWindow", None)
        if btn is None or btn.isChecked() == enabled:
            return
        was_blocked = btn.blockSignals(True)
        try:
            btn.setChecked(enabled)
        finally:
            btn.blockSignals(was_blocked)

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
            self._rebuildValuesTable()
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def _showMessage(self, text: str, level: int = 0, duration: int = 5) -> None:
        QGISRedUIUtils.showGlobalMessage(self.iface, text, level=level, duration=duration)

    def connectResultsDock(self, results_dock) -> None:
        if self._resultsDock is results_dock:
            self._syncCurrentResultsTime()
            self._syncFormatFromResultsDock()
            self._updateClearToolbarVisibility()
            self._refreshStartClockSeconds()
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
            self._syncFormatFromResultsDock()
        self._refreshStartClockSeconds()
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
        self.plot.setStartClockSeconds(0)
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self.btnSyncCursor.setChecked(False)
        self._updateClearToolbarVisibility()

    def _onResultsTimeTextChanged(self, time_text: str) -> None:
        self._lastResultsTimeText = time_text or ""
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._applySyncedTimeText(self._lastResultsTimeText)
        self._syncFormatFromResultsDock()

    def _syncFormatFromResultsDock(self) -> None:
        dock = self._resultsDock
        if dock is None:
            return
        civil = getattr(dock, "civilMode", False)
        am_pm = getattr(dock, "amPmFormat", False)
        continuous = getattr(dock, "continuousHoursMode", False)
        if civil:
            self.plot._axis_cfg_x.x_hour_format = "hm_ampm" if am_pm else "hm"
            self.plot._axis_cfg_x.x_day_format = "split_days"
        else:
            self.plot._axis_cfg_x.x_hour_format = "elapsed_hm"
            self.plot._axis_cfg_x.x_day_format = "total_hours" if continuous else "split_days"
        self.plot.update()
        self._rebuildValuesTable()

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

    def _refreshStartClockSeconds(self) -> None:
        dock = getattr(self, "_resultsDock", None)
        if dock is None:
            self.plot.setStartClockSeconds(0)
            return
        start_seconds = simulation_start_clock_seconds(
            getattr(dock, "ProjectDirectory", "") or "",
            getattr(dock, "NetworkName", "") or "",
            getattr(dock, "outPath", "") or "",
        )
        self.plot.setStartClockSeconds(start_seconds)

    def _formatCsvCivilTime(self, hours) -> str:
        return format_civil_time(hours, getattr(self.plot, "_start_clock_seconds", 0), include_seconds=True)

    def _formatCsvTimeForAxisOptions(self, hours, decimal_sep: str) -> str:
        cfg = getattr(self.plot, "_axis_cfg_x", None)
        hour_format = (getattr(cfg, "x_hour_format", "") or "hm").strip()
        day_format = (getattr(cfg, "x_day_format", "") or "split_days").strip()
        if hour_format in ("hm", "hm_ampm", "tod_hm", "tod_ampm"):
            return format_civil_time(
                hours,
                getattr(self.plot, "_start_clock_seconds", 0),
                include_seconds=True,
                am_pm=hour_format in ("hm_ampm", "tod_ampm"),
            )
        return format_elapsed_time(
            hours,
            hour_format=hour_format,
            day_format=day_format,
            include_seconds=True,
            decimal_sep=decimal_sep,
        )

    def _seriesCsvDecimalPlaces(self, series_dict):
        if series_dict.get("y_categorical_labels"):
            return None
        try:
            parts = str(series_dict.get("series_key") or "").split(":")
            if len(parts) < 3 or not parts[2]:
                return None
            return QGISRedFieldUtils().getDecimals(normalize_element(parts[0]), parts[2])
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
        self._refreshStartClockSeconds()

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

        from .qgisred_results_data import get_regional_separators

        list_sep, decimal_sep = get_regional_separators()
        rows = []
        for s in self.plot.series or []:
            if not self.plot._seriesIsDrawn(s):
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
                    self._formatCsvTimeForAxisOptions(xs[i], decimal_sep),
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
                    self.tr("Formatted Time"),
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
                "marker_hollow": bool(s.get("marker_hollow", True)),
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
        toggle_btn = getattr(self, "btnToggleTable", None)
        if toggle_btn is not None:
            toggle_btn.setEnabled(bool(has_curves))
            if not has_curves and toggle_btn.isChecked():
                toggle_btn.setChecked(False)
                self._setTableVisible(False)
        sync_btn = getattr(self, "btnSyncCursor", None)
        if sync_btn is not None:
            sync_btn.setEnabled(bool(has_curves and self._resultsDock is not None))
            if not sync_btn.isEnabled() and sync_btn.isChecked():
                sync_btn.setChecked(False)
        self._updateTableSyncAvailability()

    def _onPlotViewChanged(self) -> None:
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def _onSeriesOrderChanged(self, _order) -> None:
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self._refreshStartClockSeconds()
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._syncCurrentResultsTime()
        self._rebuildValuesTable()
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()

    def updatePlotSeries(self, series, title, x_label, y_label):
        self._refreshStartClockSeconds()
        self.plot.setSeries(series, title, x_label, y_label)
        if hasattr(self, "btnSyncCursor") and self.btnSyncCursor is not None and self.btnSyncCursor.isChecked():
            self._syncCurrentResultsTime()
        self._rebuildValuesTable()
        self._updateClearToolbarVisibility()
        self._updatePanAvailability()
