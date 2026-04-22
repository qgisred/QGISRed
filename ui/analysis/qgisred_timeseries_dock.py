# -*- coding: utf-8 -*-
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple
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

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_timeseries_dock.ui"))

_FONT_FAMILY = "Arial"
_DEFAULT_SERIES_COLOR = QColor(0, 120, 215)
_PLOT_BG_COLOR = QColor(245, 250, 255)
_GRID_COLOR = QColor(220, 232, 245)
_BORDER_COLOR = QColor(200, 200, 200)
_TEXT_DARK = QColor(20, 20, 20)
_TEXT_AXIS = QColor(40, 40, 40)
_TOOLTIP_BORDER = QColor(0, 128, 0)
_TOOLTIP_SEPARATOR = QColor(170, 170, 170)

_AXIS_MAX_TICKS = 30
_LEGEND_ICON_SIZE = 12
_LEGEND_ROW_H = 14
_LEGEND_ROW_GAP = 16
_PLOT_TOP_PAD = 10


def _qfont(size: int, *, bold: bool = False) -> QFont:
    f = QFont(_FONT_FAMILY, size)
    if bold:
        f.setBold(True)
    return f

class TimeSeriesPlotWidget(QWidget):
    seriesOrderChanged = pyqtSignal(list)

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
        self._hover_series_idx = None
        self._legend_drag_candidate_idx = None
        self._legend_drag_active = False
        self._legend_drag_start_pos = None
        self._legend_drop_target_idx = None
        self._legend_pressed_modifiers = None
        self._legend_moved = False
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
            "color": _DEFAULT_SERIES_COLOR,
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
        right_mag = magnitudes[1] if len(magnitudes) > 1 else ""
        for s in self.series:
            m = (s.get("magnitude") or "").strip()
            if right_mag and m == right_mag:
                s["y_axis"] = "right"
            else:
                s["y_axis"] = "left"
        self._y_label_left = left_mag or self.y_label
        self._y_label_right = right_mag
        self._right_axis_active = bool(right_mag)

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
                items.append((idx, (s.get("color") or _DEFAULT_SERIES_COLOR), label, legend_type, magnitude))
        if limit is None:
            return items
        return items[:limit]

    def _legendGroups(self):
        groups = []
        current_mag = None
        current_items = []
        for series_idx, color, label, legend_type, magnitude in self._legendItems():
            mag = magnitude or self.tr("Magnitude")
            if current_mag is None:
                current_mag = mag
            if mag != current_mag:
                groups.append((current_mag, current_items))
                current_mag = mag
                current_items = []
            current_items.append((series_idx, color, label, legend_type))
        if current_mag is not None:
            groups.append((current_mag, current_items))
        return groups

    def _legendRequiredWidth(self):
        groups = self._legendGroups()
        if not groups:
            return 0
        fm = QFontMetrics(_qfont(8))
        fm_hdr = QFontMetrics(_qfont(8, bold=True))
        max_w = 0
        for mag, items in groups:
            w_hdr = fm_hdr.horizontalAdvance(mag)
            if w_hdr > max_w:
                max_w = w_hdr
            for _idx, _color, label, _legend_type in items:
                w_label = fm.horizontalAdvance(label)
                if w_label > max_w:
                    max_w = w_label
        return _LEGEND_ICON_SIZE + 6 + max_w + 12

    def _drawLegendIcon(self, painter, x, y, size, legend_type, color, muted=False, highlighted=False):
        c = QColor(color)
        if muted:
            c.setAlpha(80)
        pen_w = 2 if highlighted else 1
        painter.setPen(QPen(c, pen_w))
        painter.setBrush(Qt.GlobalColor.white)

        t = (legend_type or "").lower()
        cx = x + size / 2
        cy = y + size / 2

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
        painter.drawEllipse(QPointF(cx, cy), (size - 4) / 2, (size - 4) / 2)

    def _drawNoDataMessage(self, painter):
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            self.tr("No data to display, please select an element on the map."),
        )

    def _extract_units_from_label(self):
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
        time_str = f"{sign}24" if (d > 0 and h == 0 and m == 0) else (f"{sign}{h}" if m == 0 else f"{sign}{h}:{m:02d}")
        if d > 0:
            return f"{time_str}\n{sign}{d}d"
        return time_str

    def _expand_range(self, minimum, maximum):
        value_range = maximum - minimum
        if value_range == 0:
            pad = abs(maximum) * 0.1
            if pad == 0:
                pad = 1
            return minimum - pad, maximum + pad
        return minimum - value_range * 0.1, maximum + value_range * 0.1

    def _computeYAxisState(self, all_y, plot_rect, painter):
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
            max_ticks=_AXIS_MAX_TICKS,
        )
        y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return {
            "min_y": y_scale.axis_min,
            "max_y": y_scale.axis_max,
            "num_ticks_y": y_scale.divisions,
            "y_tick_values": y_scale.ticks(),
            "y_step": y_scale.step,
        }

    def _computeYAxisStateFor(self, all_y, y_categorical_labels, plot_rect, painter):
        if y_categorical_labels:
            min_y = 0
            max_y = len(y_categorical_labels) - 1
            min_y, max_y = self._expand_range(min_y, max_y)
            y_tick_values = list(range(len(y_categorical_labels)))
            return {
                "min_y": min_y,
                "max_y": max_y,
                "num_ticks_y": len(y_tick_values) - 1,
                "y_tick_values": y_tick_values,
                "y_step": None,
                "y_categorical_labels": y_categorical_labels,
            }

        min_y, max_y = min(all_y), max(all_y)
        max_ticks_y = estimate_max_ticks(
            plot_rect.height(),
            painter.fontMetrics().height() + 6,
            min_ticks=2,
            max_ticks=_AXIS_MAX_TICKS,
        )
        y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return {
            "min_y": y_scale.axis_min,
            "max_y": y_scale.axis_max,
            "num_ticks_y": y_scale.divisions,
            "y_tick_values": y_scale.ticks(),
            "y_step": y_scale.step,
            "y_categorical_labels": None,
        }

    def _estimateXAxisLabelPixelSize(self, painter, *, has_days: bool) -> float:
        fm = painter.fontMetrics()
        if has_days:
            w_top = fm.horizontalAdvance("24")
            w_bottom = fm.horizontalAdvance("999d")
            return max(w_top, w_bottom) + 18
        return fm.horizontalAdvance("23:59") + 18

    def _computeXAxisState(self, all_x, plot_rect, painter):
        min_x, max_x = min(all_x), max(all_x)
        if max_x == min_x:
            max_x = min_x + 1

        has_days = max_x >= 24
        label_px = self._estimateXAxisLabelPixelSize(painter, has_days=has_days)
        max_ticks_x = estimate_max_ticks(plot_rect.width(), label_px, min_ticks=2, max_ticks=_AXIS_MAX_TICKS)
        x_scale = compute_nice_time_scale_hours(min_x, max_x, max_ticks_x)
        min_x, max_x = x_scale.axis_min, x_scale.axis_max
        x_range = max_x - min_x
        if x_range == 0:
            x_range = 1
        return {
            "min_x": min_x,
            "max_x": max_x,
            "x_range": x_range,
            "x_scale": x_scale,
            "has_days": has_days,
            "label_px": label_px,
        }

    def _to_screen(self, x, y, plot_rect, x_state, y_state):
        sx = plot_rect.left() + (x - x_state["min_x"]) / x_state["x_range"] * plot_rect.width()
        sy = plot_rect.bottom() - (y - y_state["min_y"]) / (y_state["max_y"] - y_state["min_y"]) * plot_rect.height()
        return QPointF(sx, sy)

    def _drawGridAndAxes(self, painter, plot_rect, local_margin_left, right_axis_label_w, x_state, y_state_left, y_state_right=None):
        painter.setFont(_qfont(9))
        pen_grid = QPen(_GRID_COLOR, 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen_grid)

        for i in range(y_state_left["num_ticks_y"] + 1):
            y_cat = y_state_left.get("y_categorical_labels") or self.y_categorical_labels
            if y_cat:
                val_y = i
                label_text = y_cat[i]
            else:
                val_y = y_state_left["y_tick_values"][i]
                label_text = format_number_tick(val_y, y_state_left["y_step"])

            pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state_left)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(
                QRectF(0, pt.y() - 10, local_margin_left - 5, 20),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                label_text,
            )
            painter.setPen(pen_grid)

        if y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            for i in range(y_state_right["num_ticks_y"] + 1):
                y_cat_r = y_state_right.get("y_categorical_labels")
                if y_cat_r:
                    val_y = i
                    label_text = y_cat_r[i]
                else:
                    val_y = y_state_right["y_tick_values"][i]
                    label_text = format_number_tick(val_y, y_state_right["y_step"])
                pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state_right)
                painter.setPen(Qt.GlobalColor.black)
                painter.drawText(
                    QRectF(plot_rect.right() + 5, pt.y() - 10, right_axis_label_w - 10, 20),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    label_text,
                )
                painter.setPen(pen_grid)

        if len(self.data_x) > 1:
            fm_x = painter.fontMetrics()
            has_days = bool(x_state.get("has_days", x_state["max_x"] >= 24))
            tick_h = fm_x.height() * 2 + 4 if has_days else fm_x.height() + 6
            tick_w = float(x_state.get("label_px", self._estimateXAxisLabelPixelSize(painter, has_days=has_days)))
            for val_x in x_state["x_scale"].ticks():
                pt = self._to_screen(val_x, y_state_left["min_y"], plot_rect, x_state, y_state_left)
                painter.setPen(pen_grid)
                painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))

                painter.setPen(Qt.GlobalColor.black)
                label_x = self._format_absolute_time_hours(val_x)
                painter.drawText(
                    QRectF(pt.x() - tick_w / 2, plot_rect.bottom() + 8, tick_w, tick_h),
                    Qt.AlignmentFlag.AlignCenter,
                    label_x,
                )

    def _drawAxisTitles(self, painter, plot_rect, local_margin_left, right_axis_label_w, widget_h):
        painter.setFont(_qfont(9))

        small_font = _qfont(7, bold=False)
        title_pen = QPen(_TEXT_AXIS)

        left_title = (self._y_label_left or self.y_label or "").strip()
        if left_title:
            painter.save()
            painter.setFont(small_font)
            painter.setPen(title_pen)
            painter.translate(local_margin_left / 2 - 15, widget_h / 2)
            painter.rotate(-90)
            painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, left_title)
            painter.restore()

        if self._right_axis_active and right_axis_label_w and right_axis_label_w > 0:
            right_title = (self._y_label_right or "").strip()
            if right_title:
                painter.save()
                painter.setFont(small_font)
                painter.setPen(title_pen)
                title_x = plot_rect.right() + right_axis_label_w + 4
                painter.translate(title_x, widget_h / 2)
                painter.rotate(90)
                painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, right_title)
                painter.restore()

        painter.drawText(
            QRectF(local_margin_left, widget_h - self.margin_bottom + 20, plot_rect.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            self.x_label,
        )

    def _drawSeriesCurves(self, painter, plot_rect, x_state, y_state_left, y_state_right=None):
        if not any(len((s.get("x") or [])) > 1 for s in self.series):
            return

        for s in self.series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            if not xs or not ys or len(xs) < 2:
                continue

            color = s.get("color") or _DEFAULT_SERIES_COLOR
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

            axis = (s.get("y_axis") or "left")
            y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
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
        groups = self._legendGroups()
        if not groups or not self._legend_reserved_w:
            return

        painter.save()
        painter.setFont(_qfont(8))
        x0 = plot_rect.right() + 10 + (self._right_axis_label_w if getattr(self, "_right_axis_label_w", 0) else 0) + 20
        y0 = plot_rect.top() + 10
        max_x = self.width() - 5
        for mag_title, items in groups:
            if x0 >= max_x:
                break
            if (y0 + _LEGEND_ROW_H) > (plot_rect.bottom() - 4):
                break

            painter.setFont(_qfont(8, bold=True))
            painter.setPen(_TEXT_DARK)
            hdr_rect = QRectF(x0, y0, max_x - x0, _LEGEND_ROW_H)
            painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, mag_title)
            y0 += _LEGEND_ROW_GAP

            for series_idx, color, label, legend_type in items:
                if (y0 + _LEGEND_ROW_H) > (plot_rect.bottom() - 4):
                    break
                s = self.series[series_idx]
                muted = bool(s.get("muted", False))
                highlighted = bool(s.get("highlighted", False))

                self._drawLegendIcon(
                    painter,
                    x0,
                    y0 + 1,
                    _LEGEND_ICON_SIZE,
                    legend_type,
                    color,
                    muted=muted,
                    highlighted=highlighted,
                )

                painter.setFont(_qfont(8, bold=highlighted))
                painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
                text_rect = QRectF(x0 + 18, y0, max_x - (x0 + 18), _LEGEND_ROW_H)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                hit_rect = QRectF(x0, y0, self._legend_reserved_w, _LEGEND_ROW_H)
                self._legend_hitboxes.append((hit_rect, series_idx))

                if self._legend_drag_active and self._legend_drop_target_idx == series_idx:
                    painter.setPen(QPen(QColor(30, 30, 30), 2))
                    painter.drawLine(
                        QPointF(hit_rect.left(), hit_rect.top() - 1),
                        QPointF(hit_rect.right(), hit_rect.top() - 1),
                    )
                y0 += _LEGEND_ROW_GAP

            y0 += 6
        painter.restore()

    def _collectHoverTooltipData(self, hover_index, val_x, plot_rect, x_state, y_state_left, y_state_right=None):
        units_str = ""
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

            color = s.get("color") or _DEFAULT_SERIES_COLOR
            muted = bool(s.get("muted", False))
            label = (s.get("label") or "").strip() or self.tr("Series")
            val_y = ys[hover_index]
            series_y_labels = s.get("y_categorical_labels") or (y_state_left.get("y_categorical_labels") if y_state_left else None)
            if series_y_labels:
                try:
                    val_y_str = series_y_labels[int(round(val_y))]
                except Exception:
                    val_y_str = str(val_y)
            else:
                val_y_str = self._format_value_full(val_y)

            tooltip_lines.append((color, muted, f"{label}: ", val_y_str, units_str))
            axis = (s.get("y_axis") or "left")
            y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
            marker_pts.append((color, muted, self._to_screen(val_x, val_y, plot_rect, x_state, y_state)))

        return tooltip_lines, marker_pts

    def _drawHoverOverlay(self, painter, plot_rect, x_state, y_state_left, y_state_right=None):
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

        axis = (hover_series.get("y_axis") or "left")
        y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
        pt_rule = self._to_screen(val_x, y_state["min_y"], plot_rect, x_state, y_state)
        painter.setPen(QPen(QColor(255, 110, 110), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(pt_rule.x(), plot_rect.top()), QPointF(pt_rule.x(), plot_rect.bottom()))

        header_text = self.tr("Time: %1").replace("%1", self._format_absolute_time_hours(val_x))
        tooltip_lines, marker_pts = self._collectHoverTooltipData(
            self.hover_index,
            val_x,
            plot_rect,
            x_state,
            y_state_left,
            y_state_right,
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
        font_tt = _qfont(8)
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
        painter.setPen(QPen(_TOOLTIP_BORDER, 1))
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRect(rect_tt)

        header_x = rect_tt.left() + pad
        header_baseline_y = rect_tt.top() + pad + fm.ascent()
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(font_tt_bold)
        painter.drawText(QPointF(header_x, header_baseline_y), header_text)

        sep_y = rect_tt.top() + pad + line_h + header_gap
        painter.setPen(QPen(_TOOLTIP_SEPARATOR, 1))
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

    def _yTickLabelsForWidth(
        self,
        all_y: Sequence[float],
        y_cat: Optional[Sequence[str]],
        fm: QFontMetrics,
        plot_h: float,
    ) -> List[str]:
        if y_cat:
            return [y_cat[i] for i in range(len(y_cat))]
        if not all_y:
            return []
        min_y, max_y = min(all_y), max(all_y)
        max_ticks_y = estimate_max_ticks(plot_h, fm.height() + 6, min_ticks=2, max_ticks=_AXIS_MAX_TICKS)
        scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return [format_number_tick(v, scale.step) for v in scale.ticks()]

    def _computeLeftMargin(self, all_y_left: Sequence[float], y_cat_left: Optional[Sequence[str]], fm: QFontMetrics, plot_h: float) -> float:
        tick_labels = self._yTickLabelsForWidth(all_y_left, y_cat_left, fm, plot_h)
        if not tick_labels:
            return float(self.margin_left)
        max_label_w = 0
        for label_text in tick_labels:
            max_label_w = max(max_label_w, fm.horizontalAdvance(label_text))
        return max(float(self.margin_left), float(max_label_w + 40))

    def _computeRightAxisLabelWidth(self, all_y_right: Sequence[float], y_cat_right: Optional[Sequence[str]], fm: QFontMetrics, plot_h: float) -> float:
        tick_labels = self._yTickLabelsForWidth(all_y_right, y_cat_right, fm, plot_h)
        if not tick_labels:
            return 0.0
        max_label_w = 0
        for label_text in tick_labels:
            max_label_w = max(max_label_w, fm.horizontalAdvance(label_text))
        return max(0.0, float(max_label_w + 18))

    def getPlotRect(self):
        w = self.width()
        h = self.height()
        
        font = _qfont(9)
        fm = QFontMetrics(font)

        left_series, right_series = self._seriesByAxis()
        _all_x, all_y_left, y_cat_left, _any_stepped_left = self._axisSeriesData(left_series)
        _all_x_r, all_y_right, y_cat_right, _any_stepped_right = self._axisSeriesData(right_series)
        legend_w = self._legendRequiredWidth()
        self._legend_reserved_w = legend_w

        plot_h_est = h - (self.margin_top + _PLOT_TOP_PAD) - self.margin_bottom
        local_margin_left = self._computeLeftMargin(all_y_left, y_cat_left, fm, plot_h_est)
        right_axis_label_w = self._computeRightAxisLabelWidth(all_y_right, y_cat_right, fm, plot_h_est)

        local_margin_bottom = self.margin_bottom
        if self.data_x and len(self.data_x) > 1:
            has_days = max(self.data_x) >= 24
            extra = fm.height() * 2 + 16 if has_days else fm.height() + 20
            local_margin_bottom = max(local_margin_bottom, extra)

        self._right_axis_label_w = right_axis_label_w
        local_margin_right = self.margin_right + right_axis_label_w + (self._legend_reserved_w + 10 if self._legend_reserved_w else 0)
        return QRectF(local_margin_left, self.margin_top + _PLOT_TOP_PAD,
                      w - local_margin_left - local_margin_right,
                      h - (self.margin_top + _PLOT_TOP_PAD) - local_margin_bottom), local_margin_left, right_axis_label_w

    def paintEvent(self, event):
        if not self.series:
            painter = QPainter(self)
            self._drawNoDataMessage(painter)
            return

        painter = QPainter(self)
        painter.setRenderHint(PAINTER_ANTIALIASING)

        w = self.width()
        h = self.height()
        
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        
        if self.title:
            painter.save()
            font_title = _qfont(12, bold=True)
            painter.setFont(font_title)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(0, 0, w, self.margin_top), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, self.title)
            painter.restore()

        all_x, all_y, y_categorical_labels, any_stepped = self._globalSeriesData()

        if not all_x or not all_y:
            self._drawNoDataMessage(painter)
            return
        self.data_x = all_x
        self.data_y = all_y
        self.y_categorical_labels = y_categorical_labels
        self.is_stepped = any_stepped

        plot_rect, local_margin_left, right_axis_label_w = self.getPlotRect()
        self._legend_hitboxes = []

        painter.fillRect(plot_rect, _PLOT_BG_COLOR)

        painter.setPen(QPen(_BORDER_COLOR, 1))
        painter.drawRect(plot_rect)

        left_series, right_series = self._seriesByAxis()
        _lx, all_y_left, y_cat_left, _st_left = self._axisSeriesData(left_series)
        _rx, all_y_right, y_cat_right, _st_right = self._axisSeriesData(right_series)
        y_state_left = self._computeYAxisStateFor(all_y_left, y_cat_left, plot_rect, painter)
        y_state_right = None
        if all_y_right:
            y_state_right = self._computeYAxisStateFor(all_y_right, y_cat_right, plot_rect, painter)
        painter.setFont(_qfont(9))
        x_state = self._computeXAxisState(self.data_x, plot_rect, painter)
        self._drawGridAndAxes(painter, plot_rect, local_margin_left, right_axis_label_w, x_state, y_state_left, y_state_right)

        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())
        if y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            painter.drawLine(plot_rect.bottomRight(), plot_rect.topRight())

        self._drawAxisTitles(painter, plot_rect, local_margin_left, right_axis_label_w, h)
        self._drawSeriesCurves(painter, plot_rect, x_state, y_state_left, y_state_right)
        self._drawLegend(painter, plot_rect)
        self._drawHoverOverlay(painter, plot_rect, x_state, y_state_left, y_state_right)

    def leaveEvent(self, event):
        if self.hover_index is not None:
            self.hover_index = None
            self._hover_series_idx = None
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._beginLegendInteraction(QPointF(event.pos()), event.modifiers())

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._legend_drag_active:
            if self._applyLegendReorder():
                self._resetLegendInteractionState()
                self.update()
                return

        if self._legend_drag_candidate_idx is not None and not self._legend_moved:
            self._applyLegendToggle(int(self._legend_drag_candidate_idx), self._legend_pressed_modifiers)
            self.update()

        self._resetLegendInteractionState()

    def mouseMoveEvent(self, event):    
        if self._legend_drag_candidate_idx is not None and self._legend_drag_start_pos is not None:
            if self._updateLegendDrag(QPointF(event.pos())):
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

    def _beginLegendInteraction(self, pos: QPointF, modifiers) -> None:
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
        self._legend_pressed_modifiers = modifiers
        self._legend_moved = False

    def _updateLegendDrag(self, pos: QPointF) -> bool:
        dx = abs(pos.x() - self._legend_drag_start_pos.x())
        dy = abs(pos.y() - self._legend_drag_start_pos.y())
        if (dx + dy) > 1:
            self._legend_moved = True
        if not self._legend_drag_active and (dx + dy) > 5:
            self._legend_drag_active = True

        if not self._legend_drag_active:
            return False

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
        return True

    def _applyLegendReorder(self) -> bool:
        if self._legend_drag_candidate_idx is None or self._legend_drop_target_idx is None:
            return False
        from_idx = int(self._legend_drag_candidate_idx)
        to_idx = int(self._legend_drop_target_idx)
        if not (0 <= from_idx < len(self.series) and 0 <= to_idx < len(self.series)) or from_idx == to_idx:
            return False

        item = self.series.pop(from_idx)
        insert_at = to_idx - 1 if from_idx < to_idx else to_idx
        insert_at = max(0, min(insert_at, len(self.series)))
        self.series.insert(insert_at, item)
        order = [str(s.get("series_key") or "") for s in self.series]
        self.seriesOrderChanged.emit(order)
        return True

    def _applyLegendToggle(self, clicked_idx: int, modifiers) -> None:
        if not (0 <= clicked_idx < len(self.series)):
            return
        modifiers = modifiers or Qt.KeyboardModifier.NoModifier
        is_ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        is_shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)

        if is_shift:
            for i, s in enumerate(self.series):
                s["highlighted"] = (i == clicked_idx)
                s["muted"] = (i != clicked_idx)
            return

        if is_ctrl:
            s = self.series[clicked_idx]
            s["highlighted"] = not bool(s.get("highlighted", False))
            if s["highlighted"]:
                s["muted"] = False
            return

        s = self.series[clicked_idx]
        s["muted"] = not bool(s.get("muted", False))
        if s["muted"]:
            s["highlighted"] = False

class QGISRedTimeSeriesDock(QDockWidget, FORM_CLASS):
    seriesReordered = pyqtSignal(list)

    def __init__(self, iface, parent=None):
        super(QGISRedTimeSeriesDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        
        self.plot = TimeSeriesPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)
        self.plot.seriesOrderChanged.connect(self.seriesReordered)

        self.lblTitle.hide()
        
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None, series_label=""):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels, series_label)

    def updatePlotSeries(self, series, title, x_label, y_label):
        self.plot.setSeries(series, title, x_label, y_label)
