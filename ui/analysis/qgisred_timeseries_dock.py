# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, pyqtSignal
from qgis.PyQt.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QFontMetrics, QPolygonF
from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    compute_nice_time_scale_hours,
    estimate_max_ticks,
    format_number_tick,
)
from qgis.PyQt import uic

# Load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_timeseries_dock.ui"))

class TimeSeriesPlotWidget(QWidget):
    seriesOrderChanged = pyqtSignal(list)  # list of series_key in new order

    def __init__(self, parent=None):
        super(TimeSeriesPlotWidget, self).__init__(parent)
        # Backwards-compatible single-series storage
        self.data_x = []
        self.data_y = []
        # Multi-series storage: list of dicts with keys:
        # x, y, label, color, is_stepped, y_categorical_labels
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
        self.y_categorical_labels = None # Optional list of strings for Y ticks
        self.setMouseTracking(True)
        self._legend_reserved_w = 0
        self._legend_hitboxes = []  # list of (QRectF, series_index)
        self._hover_series_idx = None
        self._legend_drag_candidate_idx = None
        self._legend_drag_active = False
        self._legend_drag_start_pos = None
        self._legend_drop_target_idx = None
        self._legend_pressed_modifiers = None
        self._legend_moved = False

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False, y_categorical_labels=None, series_label=""):
        self.data_x = x
        self.data_y = y
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.is_stepped = is_stepped
        self.y_categorical_labels = y_categorical_labels
        # Also set multi-series with a single entry
        self.series = [{
            "x": x,
            "y": y,
            "label": series_label or "",
            "color": QColor(0, 120, 215),
            "is_stepped": is_stepped,
            "y_categorical_labels": y_categorical_labels,
            "muted": False,
            "highlighted": False,
            "series_key": series_label or "",
        }]
        self.update()

    def setSeries(self, series, title="", x_label="Time", y_label="Value"):
        self.series = series or []
        # Normalize per-series interaction state
        for s in self.series:
            if "muted" not in s:
                s["muted"] = False
            if "highlighted" not in s:
                s["highlighted"] = False
            if "series_key" not in s:
                s["series_key"] = ""
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        # Keep single-series fields coherent for legacy helpers
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

    def update(self):
        # Trigger recalculation of margins if needed before painting
        super(TimeSeriesPlotWidget, self).update()

    def _globalSeriesData(self):
        """Compute global x/y lists and shared categorical labels (if any)."""
        if not self.series:
            return [], [], None, False

        all_x = []
        all_y = []
        y_categorical_labels = None
        any_categorical = False
        any_stepped = False

        for s in self.series:
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

        # Use categorical labels only if all series share the same labels
        if any_categorical:
            for s in self.series:
                if s.get("y_categorical_labels") != y_categorical_labels:
                    y_categorical_labels = None
                    break

        return all_x, all_y, y_categorical_labels, any_stepped

    def _legendItems(self, limit=None):
        items = []
        for idx, s in enumerate(self.series):
            label = (s.get("label") or "").strip()
            if label:
                legend_type = (s.get("legend_type") or "").strip()
                items.append((idx, (s.get("color") or QColor(0, 120, 215)), label, legend_type))
        if limit is None:
            return items
        return items[:limit]

    def _legendRequiredWidth(self):
        items = self._legendItems()
        if not items:
            return 0
        fm = QFontMetrics(QFont("Arial", 8))
        max_w = 0
        for _idx, _color, label, _legend_type in items:
            w_label = fm.horizontalAdvance(label)
            if w_label > max_w:
                max_w = w_label
        # icon (12px) + gap (6px) + label + padding (12px)
        return 12 + 6 + max_w + 12

    def _drawLegendIcon(self, painter, x, y, size, legend_type, color, muted=False, highlighted=False):
        """Draw a small icon matching the element type."""
        c = QColor(color)
        if muted:
            c.setAlpha(80)
        pen_w = 2 if highlighted else 1
        painter.setPen(QPen(c, pen_w))
        painter.setBrush(Qt.GlobalColor.white)

        t = (legend_type or "").lower()
        cx = x + size / 2
        cy = y + size / 2

        # Default: small line (for unknown)
        if "qgisred_pipes" in t or t == "link" or "pipe" in t:
            painter.drawLine(QPointF(x, cy), QPointF(x + size, cy))
            return
        if "qgisred_valves" in t or "valve" in t:
            painter.drawLine(QPointF(x + 2, y + 2), QPointF(x + size - 2, y + size - 2))
            painter.drawLine(QPointF(x + size - 2, y + 2), QPointF(x + 2, y + size - 2))
            return
        if "qgisred_pumps" in t or "pump" in t:
            tri = QPolygonF([QPointF(x + 2, y + 2), QPointF(x + size - 2, cy), QPointF(x + 2, y + size - 2)])
            painter.drawPolygon(tri)
            return
        if "qgisred_tanks" in t or "tank" in t:
            painter.drawRect(QRectF(x + 2, y + 2, size - 4, size - 4))
            return
        if "qgisred_reservoirs" in t or "reservoir" in t:
            diamond = QPolygonF([QPointF(cx, y + 2), QPointF(x + size - 2, cy), QPointF(cx, y + size - 2), QPointF(x + 2, cy)])
            painter.drawPolygon(diamond)
            return
        # Junctions and generic nodes: circle
        painter.drawEllipse(QPointF(cx, cy), (size - 4) / 2, (size - 4) / 2)

    def _drawNoDataMessage(self, painter):
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.tr("No data to display, please select an element on the map."),
        )

    def _extract_units_from_label(self):
        """Infer units from labels like 'Flow (m3/s)' or 'Flow [m3/s]'."""
        y_label = self.y_label or ""
        unit_delimiters = [("(", ")"), ("[", "]")]
        for start_char, end_char in unit_delimiters:
            if start_char in y_label and end_char in y_label:
                start = y_label.rfind(start_char)
                end = y_label.rfind(end_char)
                if 0 <= start < end:
                    return y_label[start + 1 : end].strip()
        return ""

    def _format_absolute_time_hours(self, hours):
        total_seconds = int(round(hours * 3600))
        sign = "-" if total_seconds < 0 else ""
        abs_seconds = abs(total_seconds)
        d = abs_seconds // 86400
        rem = abs_seconds % 86400
        h = rem // 3600
        m = (rem % 3600) // 60
        if d > 0:
            return f"{sign}{d}d {h:02d}:{m:02d}"
        return f"{sign}{h}:{m:02d}"

    def _expand_range(self, minimum, maximum):
        value_range = maximum - minimum
        if value_range == 0:
            pad = abs(maximum) * 0.1
            if pad == 0:
                pad = 1
            return minimum - pad, maximum + pad
        return minimum - value_range * 0.1, maximum + value_range * 0.1

    def _computeYAxisState(self, all_y, plot_rect, painter):
        """Build all Y-axis values needed by render blocks."""
        if self.y_categorical_labels:
            min_y = 0
            max_y = len(self.y_categorical_labels) - 1
            min_y, max_y = self._expand_range(min_y, max_y)
            y_tick_values = list(range(len(self.y_categorical_labels)))
            return {
                "min_y": min_y,
                "max_y": max_y,
                "num_ticks_y": len(y_tick_values) - 1,
                "y_tick_values": y_tick_values,
                "y_step": None,
            }

        min_y, max_y = min(all_y), max(all_y)
        max_ticks_y = estimate_max_ticks(
            plot_rect.height(),
            painter.fontMetrics().height() + 6,
            min_ticks=2,
            max_ticks=10,
        )
        y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return {
            "min_y": y_scale.axis_min,
            "max_y": y_scale.axis_max,
            "num_ticks_y": y_scale.divisions,
            "y_tick_values": y_scale.ticks(),
            "y_step": y_scale.step,
        }

    def _computeXAxisState(self, all_x, plot_rect):
        min_x, max_x = min(all_x), max(all_x)
        if max_x == min_x:
            max_x = min_x + 1

        max_ticks_x = estimate_max_ticks(plot_rect.width(), 60, min_ticks=2, max_ticks=12)
        x_scale = compute_nice_time_scale_hours(min_x, max_x, max_ticks_x)
        min_x, max_x = x_scale.axis_min, x_scale.axis_max
        x_range = max_x - min_x
        if x_range == 0:
            x_range = 1
        return {"min_x": min_x, "max_x": max_x, "x_range": x_range, "x_scale": x_scale}

    def _to_screen(self, x, y, plot_rect, x_state, y_state):
        sx = plot_rect.left() + (x - x_state["min_x"]) / x_state["x_range"] * plot_rect.width()
        sy = plot_rect.bottom() - (y - y_state["min_y"]) / (y_state["max_y"] - y_state["min_y"]) * plot_rect.height()
        return QPointF(sx, sy)

    def _drawGridAndAxes(self, painter, plot_rect, local_margin_left, x_state, y_state):
        painter.setFont(QFont("Arial", 9))
        pen_grid = QPen(QColor(220, 232, 245), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen_grid)

        # Horizontal lines (Y axis)
        for i in range(y_state["num_ticks_y"] + 1):
            if self.y_categorical_labels:
                val_y = i
                label_text = self.y_categorical_labels[i]
            else:
                val_y = y_state["y_tick_values"][i]
                label_text = format_number_tick(val_y, y_state["y_step"])

            pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(
                QRectF(0, pt.y() - 10, local_margin_left - 5, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label_text,
            )
            painter.setPen(pen_grid)

        # Vertical lines (X axis)
        if len(self.data_x) > 1:
            fm_x = painter.fontMetrics()
            tick_h = fm_x.height() + 6
            for val_x in x_state["x_scale"].ticks():
                pt = self._to_screen(val_x, y_state["min_y"], plot_rect, x_state, y_state)
                painter.setPen(pen_grid)
                painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))

                painter.setPen(Qt.GlobalColor.black)
                label_x = self._format_absolute_time_hours(val_x)
                painter.drawText(
                    QRectF(pt.x() - 40, plot_rect.bottom() + 8, 80, tick_h),
                    Qt.AlignmentFlag.AlignCenter,
                    label_x,
                )

    def _drawAxisTitles(self, painter, plot_rect, local_margin_left, widget_h):
        painter.setFont(QFont("Arial", 9))
        painter.save()
        painter.translate(local_margin_left / 2 - 15, widget_h / 2)
        painter.rotate(-90)
        painter.drawText(QRectF(-100, -15, 200, 30), Qt.AlignmentFlag.AlignCenter, self.y_label)
        painter.restore()
        painter.drawText(
            QRectF(local_margin_left, widget_h - self.margin_bottom + 20, plot_rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self.x_label,
        )

    def _drawSeriesCurves(self, painter, plot_rect, x_state, y_state):
        if not any(len((s.get("x") or [])) > 1 for s in self.series):
            return

        for s in self.series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            if not xs or not ys or len(xs) < 2:
                continue

            color = s.get("color") or QColor(0, 120, 215)
            is_stepped = bool(s.get("is_stepped", False))
            muted = bool(s.get("muted", False))
            highlighted = bool(s.get("highlighted", False))
            draw_color = QColor(color)
            width = 2
            if muted:
                draw_color.setAlpha(70)
                width = 1
            if highlighted:
                draw_color.setAlpha(255)
                width = 3

            painter.setPen(QPen(draw_color, width))
            path = QPainterPath()

            start_pt = self._to_screen(xs[0], ys[0], plot_rect, x_state, y_state)
            path.moveTo(start_pt)
            for i in range(1, len(xs)):
                next_pt = self._to_screen(xs[i], ys[i], plot_rect, x_state, y_state)
                if is_stepped:
                    path.lineTo(next_pt.x(), start_pt.y())
                    path.lineTo(next_pt)
                else:
                    path.lineTo(next_pt)
                start_pt = next_pt

            painter.drawPath(path)

    def _drawLegend(self, painter, plot_rect):
        legend_items = self._legendItems()
        if not legend_items or not self._legend_reserved_w:
            return

        painter.save()
        painter.setFont(QFont("Arial", 8))
        x0 = plot_rect.right() + 10
        y0 = plot_rect.top() + 10
        max_x = self.width() - 5
        for series_idx, color, label, legend_type in legend_items:
            if x0 >= max_x:
                break
            if (y0 + 14) > (plot_rect.bottom() - 4):
                break
            s = self.series[series_idx]
            muted = bool(s.get("muted", False))
            highlighted = bool(s.get("highlighted", False))

            self._drawLegendIcon(
                painter,
                x0,
                y0 + 1,
                12,
                legend_type,
                color,
                muted=muted,
                highlighted=highlighted,
            )

            font = QFont("Arial", 8)
            font.setBold(highlighted)
            painter.setFont(font)
            painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
            text_rect = QRectF(x0 + 18, y0, max_x - (x0 + 18), 14)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
            hit_rect = QRectF(x0, y0, self._legend_reserved_w, 14)
            self._legend_hitboxes.append((hit_rect, series_idx))

            if self._legend_drag_active and self._legend_drop_target_idx == series_idx:
                painter.setPen(QPen(QColor(30, 30, 30), 2))
                painter.drawLine(
                    QPointF(hit_rect.left(), hit_rect.top() - 1),
                    QPointF(hit_rect.right(), hit_rect.top() - 1),
                )
            y0 += 16
        painter.restore()

    def _collectHoverTooltipData(self, hover_index, val_x, plot_rect, x_state, y_state):
        units = self._extract_units_from_label()
        units_str = f" {units}" if units else ""
        tooltip_lines = []
        marker_pts = []

        for s in self.series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            if not xs or not ys or len(xs) <= hover_index or len(ys) <= hover_index:
                continue

            try:
                if abs(float(xs[hover_index]) - float(val_x)) > 1e-6:
                    continue
            except Exception:
                continue

            color = s.get("color") or QColor(0, 120, 215)
            muted = bool(s.get("muted", False))
            label = (s.get("label") or "").strip() or self.tr("Series")
            val_y = ys[hover_index]
            series_y_labels = s.get("y_categorical_labels") or self.y_categorical_labels
            if series_y_labels:
                try:
                    val_y_str = series_y_labels[int(round(val_y))]
                except Exception:
                    val_y_str = str(val_y)
            else:
                try:
                    val_y_str = f"{float(val_y):.2f}"
                except Exception:
                    val_y_str = str(val_y)

            tooltip_lines.append((color, muted, f"{label}: ", val_y_str, units_str))
            marker_pts.append((color, muted, self._to_screen(val_x, val_y, plot_rect, x_state, y_state)))

        return tooltip_lines, marker_pts

    def _drawHoverOverlay(self, painter, plot_rect, x_state, y_state):
        hover_series = None
        if self._hover_series_idx is not None and 0 <= self._hover_series_idx < len(self.series):
            hover_series = self.series[self._hover_series_idx]
        if hover_series is not None and self.hover_index is not None:
            xs0 = hover_series.get("x", []) or []
            ys0 = hover_series.get("y", []) or []
            if not xs0 or not ys0 or not (0 <= self.hover_index < len(xs0)):
                hover_series = None

        if hover_series is None or self.hover_index is None:
            return

        xs0 = hover_series.get("x", []) or []
        val_x = xs0[self.hover_index]

        pt_rule = self._to_screen(val_x, y_state["min_y"], plot_rect, x_state, y_state)
        painter.setPen(QPen(QColor(255, 110, 110), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(pt_rule.x(), plot_rect.top()), QPointF(pt_rule.x(), plot_rect.bottom()))

        header_text = f"{self.tr('Tiempo')}: {self._format_absolute_time_hours(val_x)}"
        tooltip_lines, marker_pts = self._collectHoverTooltipData(
            self.hover_index,
            val_x,
            plot_rect,
            x_state,
            y_state,
        )

        for color, muted, pt in marker_pts:
            c = QColor(color)
            if muted:
                c.setAlpha(90)
            painter.setPen(QPen(c, 2))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(pt, 4, 4)

        hover_val_y = None
        try:
            hover_val_y = (hover_series.get("y", []) or [])[self.hover_index]
        except Exception:
            hover_val_y = None

        self._drawTooltipBox(
            painter,
            header_text,
            tooltip_lines,
            val_x,
            hover_val_y,
            plot_rect,
            x_state,
            y_state,
        )

    def _drawTooltipBox(self, painter, header_text, tooltip_lines, val_x, hover_val_y, plot_rect, x_state, y_state):
        painter.save()
        font_tt = QFont("Arial", 8)
        font_tt_bold = QFont(font_tt)
        font_tt_bold.setBold(True)
        painter.setFont(font_tt)
        fm = painter.fontMetrics()
        fm_bold = QFontMetrics(font_tt_bold)

        header_w = fm_bold.horizontalAdvance(header_text)
        series_max_w = 0
        for _c, _m, prefix, value, suffix in tooltip_lines:
            row_w = (
                fm.horizontalAdvance(prefix)
                + fm_bold.horizontalAdvance(value)
                + fm.horizontalAdvance(suffix)
            )
            series_max_w = max(series_max_w, row_w)

        bullet_extra = 16 if tooltip_lines else 0
        max_w = max(header_w, series_max_w + bullet_extra)

        line_h = fm.height()
        pad = 5
        header_gap = 3
        separator_gap = 3
        content_h = (line_h * len(tooltip_lines)) if tooltip_lines else line_h
        rect_h = pad * 2 + line_h + header_gap + 1 + separator_gap + content_h
        rect_w = max_w + pad * 2

        pt_hover = self._to_screen(
            val_x,
            hover_val_y if hover_val_y is not None else y_state["min_y"],
            plot_rect,
            x_state,
            y_state,
        )
        tt_x = int(pt_hover.x() + 10)
        tt_y = int(pt_hover.y() - 10 - rect_h)
        if tt_x + rect_w > self.width():
            tt_x = int(pt_hover.x() - 10 - rect_w)
        if tt_y < 0:
            tt_y = int(pt_hover.y() + 10)
        if tt_x < 0:
            tt_x = 0
        if tt_y + rect_h > self.height():
            tt_y = max(0, self.height() - int(rect_h) - 1)

        rect_tt = QRectF(tt_x, tt_y, rect_w, rect_h)
        painter.setPen(QPen(QColor(0, 128, 0), 1))
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRect(rect_tt)

        header_x = rect_tt.left() + pad
        header_baseline_y = rect_tt.top() + pad + fm.ascent()
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(font_tt_bold)
        painter.drawText(QPointF(header_x, header_baseline_y), header_text)

        sep_y = rect_tt.top() + pad + line_h + header_gap
        painter.setPen(QPen(QColor(170, 170, 170), 1))
        painter.drawLine(
            QPointF(rect_tt.left() + pad, sep_y),
            QPointF(rect_tt.right() - pad, sep_y),
        )

        x_text = rect_tt.left() + pad
        y_text = sep_y + separator_gap
        for color, muted, prefix, value, suffix in tooltip_lines:
            bullet_c = QColor(color)
            if muted:
                bullet_c.setAlpha(90)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bullet_c)
            painter.drawEllipse(QPointF(x_text + 5, y_text + line_h / 2), 3, 3)
            painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
            baseline_y = y_text + fm.ascent()
            text_x = x_text + 14
            painter.setFont(font_tt)
            painter.drawText(QPointF(text_x, baseline_y), prefix)
            text_x += fm.horizontalAdvance(prefix)
            painter.setFont(font_tt_bold)
            painter.drawText(QPointF(text_x, baseline_y), value)
            text_x += fm_bold.horizontalAdvance(value)
            painter.setFont(font_tt)
            painter.drawText(QPointF(text_x, baseline_y), suffix)
            y_text += line_h

        painter.restore()

    def _resetLegendInteractionState(self):
        self._legend_drag_candidate_idx = None
        self._legend_drag_start_pos = None
        self._legend_drag_active = False
        self._legend_drop_target_idx = None
        self._legend_pressed_modifiers = None
        self._legend_moved = False

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
        w = self.width()
        h = self.height()
        
        # Calculate max label width to adjust margin dynamically
        # We use a temporary font to measure
        font = QFont("Arial", 9)
        fm = QFontMetrics(font)

        _all_x, all_y, y_categorical_labels, _any_stepped = self._globalSeriesData()
        legend_w = self._legendRequiredWidth()
        # Reserve space on the right for the legend (outside plot)
        self._legend_reserved_w = legend_w

        if not all_y:
            local_margin_left = 60
        else:
            if y_categorical_labels:
                min_y = 0
                max_y = len(y_categorical_labels) - 1
            else:
                min_y, max_y = min(all_y), max(all_y)

            max_label_w = 0
            if self.y_categorical_labels:
                num_ticks_y = len(self.y_categorical_labels) - 1
                tick_values = list(range(num_ticks_y + 1))
                tick_labels = [self.y_categorical_labels[i] for i in tick_values]
            else:
                plot_h_est = h - (self.margin_top + 10) - self.margin_bottom
                max_ticks_y = estimate_max_ticks(plot_h_est, fm.height() + 6, min_ticks=2, max_ticks=10)
                scale = compute_nice_scale(min_y, max_y, max_ticks_y)
                tick_values = scale.ticks()
                tick_labels = [format_number_tick(v, scale.step) for v in tick_values]

            for label_text in tick_labels:
                label_w = fm.horizontalAdvance(label_text)
                if label_w > max_label_w:
                    max_label_w = label_w
            
            local_margin_left = max_label_w + 40
            if local_margin_left < 60: local_margin_left = 60
            
        # Ajuste de margen inferior si el eje X usa etiquetas en 2 líneas (tiempo)
        local_margin_bottom = self.margin_bottom
        if self.data_x and len(self.data_x) > 1:
            local_margin_bottom = max(local_margin_bottom, fm.height() + 20)

        local_margin_right = self.margin_right + (self._legend_reserved_w + 10 if self._legend_reserved_w else 0)
        return QRectF(local_margin_left, self.margin_top + 10,
                      w - local_margin_left - local_margin_right,
                      h - (self.margin_top + 10) - local_margin_bottom), local_margin_left

    def paintEvent(self, event):
        if not self.series:
            painter = QPainter(self)
            self._drawNoDataMessage(painter)
            return

        painter = QPainter(self)
        painter.setRenderHint(PAINTER_ANTIALIASING)

        w = self.width()
        h = self.height()
        
        # Draw Background
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        
        # Draw Title
        if self.title:
            painter.save()
            font_title = QFont("Arial", 12)
            font_title.setBold(True)
            painter.setFont(font_title)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(0, 0, w, self.margin_top), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, self.title)
            painter.restore()

        all_x, all_y, y_categorical_labels, any_stepped = self._globalSeriesData()

        if not all_x or not all_y:
            self._drawNoDataMessage(painter)
            return
        # Keep fields coherent for any legacy uses
        self.data_x = all_x
        self.data_y = all_y
        self.y_categorical_labels = y_categorical_labels
        self.is_stepped = any_stepped

        plot_rect, local_margin_left = self.getPlotRect()
        self._legend_hitboxes = []

        # Draw plot area background (very light blue)
        painter.fillRect(plot_rect, QColor(245, 250, 255))

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(plot_rect)

        y_state = self._computeYAxisState(all_y, plot_rect, painter)
        x_state = self._computeXAxisState(self.data_x, plot_rect)
        self._drawGridAndAxes(painter, plot_rect, local_margin_left, x_state, y_state)

        # Main Axes
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())

        self._drawAxisTitles(painter, plot_rect, local_margin_left, h)
        self._drawSeriesCurves(painter, plot_rect, x_state, y_state)
        self._drawLegend(painter, plot_rect)
        self._drawHoverOverlay(painter, plot_rect, x_state, y_state)

    def leaveEvent(self, event):
        if self.hover_index is not None:
            self.hover_index = None
            self._hover_series_idx = None
            self.update()

    def mousePressEvent(self, event):
        # Legend interaction: click to mute/highlight; drag to reorder
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = QPointF(event.pos())
        clicked_idx = None
        for rect, series_idx in self._legend_hitboxes:
            if rect.contains(pos):
                clicked_idx = series_idx
                break
        if clicked_idx is None:
            return

        self._legend_drag_candidate_idx = clicked_idx
        self._legend_drag_start_pos = QPointF(pos)
        self._legend_drag_active = False
        self._legend_drop_target_idx = clicked_idx
        self._legend_pressed_modifiers = event.modifiers()
        self._legend_moved = False
        # Important: do NOT apply click actions here; wait for release.

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._legend_drag_active and self._legend_drag_candidate_idx is not None and self._legend_drop_target_idx is not None:
            from_idx = int(self._legend_drag_candidate_idx)
            to_idx = int(self._legend_drop_target_idx)
            if 0 <= from_idx < len(self.series) and 0 <= to_idx < len(self.series) and from_idx != to_idx:
                item = self.series.pop(from_idx)
                # Insert before the target's current position after pop
                insert_at = to_idx
                if from_idx < to_idx:
                    insert_at = max(0, to_idx - 1)
                self.series.insert(insert_at, item)
                # Notify new order upstream using stable series_key
                order = [str(s.get("series_key") or "") for s in self.series]
                self.seriesOrderChanged.emit(order)
            self._resetLegendInteractionState()
            self.update()
            return

        # No reorder: treat as click on legend item (only if there was no movement)
        if self._legend_drag_candidate_idx is not None and not self._legend_moved:
            clicked_idx = int(self._legend_drag_candidate_idx)
            if 0 <= clicked_idx < len(self.series):
                modifiers = self._legend_pressed_modifiers or Qt.KeyboardModifier.NoModifier
                is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
                is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

                # Shift-click: highlight only this curve (others muted)
                if is_shift:
                    for i, s in enumerate(self.series):
                        s["highlighted"] = (i == clicked_idx)
                        s["muted"] = (i != clicked_idx)
                    self.update()
                # Ctrl-click: toggle highlight without muting others
                elif is_ctrl:
                    s = self.series[clicked_idx]
                    s["highlighted"] = not bool(s.get("highlighted", False))
                    if s["highlighted"]:
                        s["muted"] = False
                    self.update()
                else:
                    # Plain click: toggle muted; clear highlight if muted
                    s = self.series[clicked_idx]
                    s["muted"] = not bool(s.get("muted", False))
                    if s["muted"]:
                        s["highlighted"] = False
                    self.update()

        # Reset drag/click state
        self._resetLegendInteractionState()

    def mouseMoveEvent(self, event):
        # If dragging a legend item, update drop target
        if self._legend_drag_candidate_idx is not None and self._legend_drag_start_pos is not None:
            pos = QPointF(event.pos())
            dx = abs(pos.x() - self._legend_drag_start_pos.x())
            dy = abs(pos.y() - self._legend_drag_start_pos.y())
            if (dx + dy) > 1:
                self._legend_moved = True
            if not self._legend_drag_active and (dx + dy) > 5:
                self._legend_drag_active = True

            if self._legend_drag_active:
                # Find nearest legend row by Y (more forgiving than rect.contains)
                target = self._legend_drop_target_idx
                best_dist = None
                for rect, series_idx in self._legend_hitboxes:
                    cy = rect.center().y()
                    d = abs(pos.y() - cy)
                    if best_dist is None or d < best_dist:
                        best_dist = d
                        target = series_idx
                if target != self._legend_drop_target_idx:
                    self._legend_drop_target_idx = target
                    self.update()
                return

        # Otherwise, normal hover behavior
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
        
        # Guard against zero or negative dimensions
        if w <= (self.margin_left + self.margin_right) or h <= (self.margin_top + 10 + self.margin_bottom):
            return

        plot_rect, local_margin_left = self.getPlotRect()
        
        if not plot_rect.contains(QPointF(mouse_pos)):
            if self.hover_index is not None:
                self.hover_index = None
                self._hover_series_idx = None
                self.update()
            return

        # Calculate scales to reverse map
        min_x, max_x = min(xs), max(xs)
        x_range = max_x - min_x
        if x_range <= 0: x_range = 1
        
        # Find nearest point in data_x
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
    seriesReordered = pyqtSignal(list)  # list of series_key in new order

    def __init__(self, iface, parent=None):
        super(QGISRedTimeSeriesDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        
        # Create the custom plot widget and add it to the container
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)
        self.plot.seriesOrderChanged.connect(self.seriesReordered)

        # Increase title font size
        self.lblTitle.hide()
        
        # Set white background for the dock and container
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)

    def updatePlotSeries(self, series, title, x_label, y_label):
        self.plot.setSeries(series, title, x_label, y_label)
