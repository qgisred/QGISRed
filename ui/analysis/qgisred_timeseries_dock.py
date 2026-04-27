# -*- coding: utf-8 -*-
import os
from typing import List
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QWidget, QHBoxLayout, QToolButton, QFrame
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, pyqtSignal, QSize
from qgis.PyQt.QtGui import QColor, QPainter, QFontMetrics, QIcon
from qgis.PyQt import uic
from qgis.core import QgsApplication

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
        self.setMinimumSize(220, 170)
        self._legend_reserved_w = 0
        self._legend_hitboxes = []
        self._legend_delete_hitboxes = []
        self._hover_series_idx = None
        self._legend = LegendInteractionController(self)
        self._renderer = TimeSeriesPlotRenderer()
        self._y_label_left = ""
        self._y_label_right = ""
        self._right_axis_active = False
        self._right_axis_label_w = 0

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False, y_categorical_labels=None, series_label=""):
        self.data_x = x
        self.data_y = y
        self.title = title
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
        self._right_axis_active = bool(right_mags)

    def setSeries(self, series, title="", x_label="Time", y_label="Value"):
        self.series = series or []
        self._normalizeSeriesState()
        self.title = title
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
        for s in axis_series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
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
        # Group by magnitude across the whole legend, not only contiguous blocks.
        # This avoids duplicated magnitude headers when series order interleaves magnitudes.
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
            # Do not break plot interaction if signal emission fails.
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

        # Reset hover/selection state if it now points outside bounds.
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

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._legend.begin(QPointF(event.pos()), event.modifiers())

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
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

        min_x, max_x = min(xs), max(xs)
        x_range = max_x - min_x
        if x_range <= 0: x_range = 1
        
        try:
            rel_x = (mouse_pos.x() - plot_rect.left()) / plot_rect.width()
            target_x = min_x + rel_x * x_range
            
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

        self._initToolbar()
        
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)
        self.plot.seriesOrderChanged.connect(self.seriesReordered)
        self.plot.seriesRemoved.connect(self.seriesRemoved)
        self.plot.seriesEmphasisChanged.connect(self.seriesEmphasisChanged)

        self.lblTitle.hide()
        
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")

    def _initToolbar(self) -> None:
        try:
            container = QWidget(self)
            hl = QHBoxLayout(container)
            hl.setContentsMargins(0, 0, 0, 0)
            hl.setSpacing(0)
            container.setFixedHeight(40)

            self.btnClearAll = QToolButton(container)
            self.btnClearAll.setObjectName("btnClearAllTimeSeries")
            # Prefer filesystem path so we don't require regenerating resources3x.py.
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "images", "iconBroom.svg"))
            self.btnClearAll.setIcon(QIcon(icon_path))
            # Use translations when available; otherwise fallback by locale so
            # users don't see English if the .qm isn't regenerated yet.
            tooltip = self.tr("Clear all curves")
            if tooltip == "Clear all curves":
                try:
                    lang = (QgsApplication.locale() or "")[:2].lower()
                except Exception:
                    lang = ""
                tooltip = {
                    "es": "Borrar todas las curvas",
                    "fr": "Effacer toutes les courbes",
                    "pt": "Apagar todas as curvas",
                }.get(lang, tooltip)
            self.btnClearAll.setToolTip(tooltip)
            self.btnClearAll.setAutoRaise(True)
            self.btnClearAll.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            self.btnClearAll.setIconSize(QSize(30, 30))
            self.btnClearAll.setFixedSize(QSize(40, 40))
            self.btnClearAll.setStyleSheet(
                "QToolButton {"
                "  border: 1px solid #d0d0d0;"
                "  border-radius: 4px;"
                "  background-color: #ffffff;"
                "  padding: 6px;"
                "}"
                "QToolButton:hover { background-color: #f3f3f3; border-color: #c2c2c2; }"
                "QToolButton:pressed { background-color: #e9e9e9; border-color: #b8b8b8; }"
                "QToolButton:focus { border: 1px solid #3399ff; }"
            )
            self.btnClearAll.clicked.connect(self.clearAllRequested)

            hl.addWidget(self.btnClearAll, 0, Qt.AlignmentFlag.AlignLeft)

            sep = QFrame(container)
            sep.setFrameShape(QFrame.Shape.VLine)
            sep.setFrameShadow(QFrame.Shadow.Plain)
            sep.setLineWidth(1)
            sep.setMidLineWidth(0)
            sep.setStyleSheet("QFrame { color: #d0d0d0; }")
            sep.setFixedHeight(28)
            hl.addWidget(sep, 0, Qt.AlignmentFlag.AlignVCenter)

            hl.addStretch(1)

            # Insert at the very top of the dock.
            try:
                self.verticalLayout.insertWidget(0, container)
            except Exception:
                self.verticalLayout.addWidget(container)
        except Exception:
            # Do not break dock creation if UI layout changes.
            return

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)

    def updatePlotSeries(self, series, title, x_label, y_label):
        self.plot.setSeries(series, title, x_label, y_label)
