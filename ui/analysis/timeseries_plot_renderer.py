# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from qgis.PyQt.QtCore import QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    compute_nice_time_scale_hours,
    estimate_max_ticks,
    format_number_tick,
)

from .timeseries_plot_style import (
    AXIS_MAX_TICKS,
    BORDER_COLOR,
    DEFAULT_SERIES_COLOR,
    GRID_COLOR,
    LEGEND_ICON_SIZE,
    LEGEND_ROW_GAP,
    LEGEND_ROW_H,
    PLOT_BG_COLOR,
    TEXT_AXIS,
    TEXT_DARK,
    TOOLTIP_BORDER,
    TOOLTIP_SEPARATOR,
    qfont,
)


class TimeSeriesPlotRenderer:
    def render(self, widget, painter: QPainter) -> None:
        if not widget.series:
            self._draw_no_data_message(widget, painter)
            return

        painter.setRenderHint(PAINTER_ANTIALIASING)
        w = widget.width()
        h = widget.height()

        painter.fillRect(widget.rect(), Qt.GlobalColor.white)

        if widget.title:
            painter.save()
            painter.setFont(qfont(12, bold=True))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(0, 0, w, widget.margin_top), Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, widget.title)
            painter.restore()

        all_x, all_y, y_categorical_labels, any_stepped = widget._axisSeriesData(widget.series)
        if not all_x or not all_y:
            self._draw_no_data_message(widget, painter)
            return

        widget.data_x = all_x
        widget.data_y = all_y
        widget.y_categorical_labels = y_categorical_labels
        widget.is_stepped = any_stepped

        plot_rect, local_margin_left, right_axis_label_w = widget.getPlotRect()
        widget._legend_hitboxes = []

        painter.fillRect(plot_rect, PLOT_BG_COLOR)
        painter.setPen(QPen(BORDER_COLOR, 1))
        painter.drawRect(plot_rect)

        left_series, right_series = widget._seriesByAxis()
        _lx, all_y_left, y_cat_left, _st_left = widget._axisSeriesData(left_series)
        _rx, all_y_right, y_cat_right, _st_right = widget._axisSeriesData(right_series)
        y_state_left = self._compute_y_axis_state(widget, all_y_left, y_cat_left, plot_rect, painter)
        y_state_right = None
        if all_y_right:
            y_state_right = self._compute_y_axis_state(widget, all_y_right, y_cat_right, plot_rect, painter)

        painter.setFont(qfont(9))
        x_state = self._compute_x_axis_state(widget, widget.data_x, plot_rect, painter)
        self._draw_grid_and_axes(widget, painter, plot_rect, local_margin_left, right_axis_label_w, x_state, y_state_left, y_state_right)

        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())
        if y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            painter.drawLine(plot_rect.bottomRight(), plot_rect.topRight())

        self._draw_axis_titles(widget, painter, plot_rect, local_margin_left, right_axis_label_w, h)
        self._draw_series_curves(widget, painter, plot_rect, x_state, y_state_left, y_state_right)
        self._draw_legend(widget, painter, plot_rect)
        self._draw_hover_overlay(widget, painter, plot_rect, x_state, y_state_left, y_state_right)

    def _draw_no_data_message(self, widget, painter: QPainter) -> None:
        painter.drawText(widget.rect(), Qt.AlignmentFlag.AlignCenter, widget.tr("No data to display, please select an element on the map."))

    def _expand_range(self, minimum: float, maximum: float) -> Tuple[float, float]:
        value_range = maximum - minimum
        if value_range == 0:
            pad = abs(maximum) * 0.1
            if pad == 0:
                pad = 1
            return minimum - pad, maximum + pad
        return minimum - value_range * 0.1, maximum + value_range * 0.1

    def _compute_y_axis_state(self, widget, all_y, y_categorical_labels, plot_rect, painter):
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
        max_ticks_y = estimate_max_ticks(plot_rect.height(), painter.fontMetrics().height() + 6, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
        y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        return {
            "min_y": y_scale.axis_min,
            "max_y": y_scale.axis_max,
            "num_ticks_y": y_scale.divisions,
            "y_tick_values": y_scale.ticks(),
            "y_step": y_scale.step,
            "y_categorical_labels": None,
        }

    def _estimate_x_axis_label_px(self, painter, *, has_days: bool) -> float:
        fm = painter.fontMetrics()
        if has_days:
            w_top = fm.horizontalAdvance("24")
            w_bottom = fm.horizontalAdvance("999d")
            return max(w_top, w_bottom) + 18
        return fm.horizontalAdvance("23:59") + 18

    def _compute_x_axis_state(self, widget, all_x, plot_rect, painter):
        min_x, max_x = min(all_x), max(all_x)
        if max_x == min_x:
            max_x = min_x + 1
        has_days = max_x >= 24
        label_px = self._estimate_x_axis_label_px(painter, has_days=has_days)
        max_ticks_x = estimate_max_ticks(plot_rect.width(), label_px, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
        x_scale = compute_nice_time_scale_hours(min_x, max_x, max_ticks_x)
        min_x, max_x = x_scale.axis_min, x_scale.axis_max
        x_range = max_x - min_x
        if x_range == 0:
            x_range = 1
        return {"min_x": min_x, "max_x": max_x, "x_range": x_range, "x_scale": x_scale, "has_days": has_days, "label_px": label_px}

    def _to_screen(self, x, y, plot_rect, x_state, y_state):
        sx = plot_rect.left() + (x - x_state["min_x"]) / x_state["x_range"] * plot_rect.width()
        sy = plot_rect.bottom() - (y - y_state["min_y"]) / (y_state["max_y"] - y_state["min_y"]) * plot_rect.height()
        return QPointF(sx, sy)

    def _format_absolute_time_hours(self, hours: float) -> str:
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

    def _draw_grid_and_axes(self, widget, painter, plot_rect, local_margin_left, right_axis_label_w, x_state, y_state_left, y_state_right=None):
        painter.setFont(qfont(9))
        pen_grid = QPen(GRID_COLOR, 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen_grid)

        for i in range(y_state_left["num_ticks_y"] + 1):
            y_cat = y_state_left.get("y_categorical_labels") or widget.y_categorical_labels
            if y_cat:
                val_y = i
                label_text = y_cat[i]
            else:
                val_y = y_state_left["y_tick_values"][i]
                label_text = format_number_tick(val_y, y_state_left["y_step"])

            pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state_left)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QRectF(0, pt.y() - 10, local_margin_left - 5, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)
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
                painter.drawText(QRectF(plot_rect.right() + 5, pt.y() - 10, right_axis_label_w - 10, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label_text)
                painter.setPen(pen_grid)

        if len(widget.data_x) > 1:
            fm_x = painter.fontMetrics()
            has_days = bool(x_state.get("has_days", x_state["max_x"] >= 24))
            tick_h = fm_x.height() * 2 + 4 if has_days else fm_x.height() + 6
            tick_w = float(x_state.get("label_px", self._estimate_x_axis_label_px(painter, has_days=has_days)))
            for val_x in x_state["x_scale"].ticks():
                pt = self._to_screen(val_x, y_state_left["min_y"], plot_rect, x_state, y_state_left)
                painter.setPen(pen_grid)
                painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))

                painter.setPen(Qt.GlobalColor.black)
                label_x = self._format_absolute_time_hours(val_x)
                painter.drawText(QRectF(pt.x() - tick_w / 2, plot_rect.bottom() + 8, tick_w, tick_h), Qt.AlignmentFlag.AlignCenter, label_x)

    def _draw_axis_titles(self, widget, painter, plot_rect, local_margin_left, right_axis_label_w, widget_h):
        painter.setFont(qfont(9))

        small_font = qfont(7, bold=False)
        title_pen = QPen(TEXT_AXIS)

        left_title = (widget._y_label_left or widget.y_label or "").strip()
        if left_title:
            painter.save()
            painter.setFont(small_font)
            painter.setPen(title_pen)
            painter.translate(local_margin_left / 2 - 15, widget_h / 2)
            painter.rotate(-90)
            painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, left_title)
            painter.restore()

        if widget._right_axis_active and right_axis_label_w and right_axis_label_w > 0:
            right_title = (widget._y_label_right or "").strip()
            if right_title:
                painter.save()
                painter.setFont(small_font)
                painter.setPen(title_pen)
                title_x = plot_rect.right() + right_axis_label_w + 4
                painter.translate(title_x, widget_h / 2)
                painter.rotate(90)
                painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, right_title)
                painter.restore()

        painter.drawText(QRectF(local_margin_left, widget_h - widget.margin_bottom + 20, plot_rect.width(), 20), Qt.AlignmentFlag.AlignCenter, widget.x_label)

    def _draw_series_curves(self, widget, painter, plot_rect, x_state, y_state_left, y_state_right=None):
        if not any(len((s.get("x") or [])) > 1 for s in widget.series):
            return

        for s in widget.series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            if not xs or not ys or len(xs) < 2:
                continue

            color = s.get("color") or DEFAULT_SERIES_COLOR
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

    def _draw_legend_icon(self, painter, x, y, size, legend_type, color, muted=False, highlighted=False):
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

    def _draw_legend(self, widget, painter, plot_rect):
        groups = widget._legendGroups()
        if not groups or not widget._legend_reserved_w:
            return

        painter.save()
        painter.setFont(qfont(8))
        x0 = plot_rect.right() + 10 + (widget._right_axis_label_w if getattr(widget, "_right_axis_label_w", 0) else 0) + 20
        y0 = plot_rect.top() + 10
        max_x = widget.width() - 5
        for mag_title, items in groups:
            if x0 >= max_x:
                break
            if (y0 + LEGEND_ROW_H) > (plot_rect.bottom() - 4):
                break

            painter.setFont(qfont(8, bold=True))
            painter.setPen(TEXT_DARK)
            hdr_rect = QRectF(x0, y0, max_x - x0, LEGEND_ROW_H)
            painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, mag_title)
            y0 += LEGEND_ROW_GAP

            for series_idx, color, label, legend_type in items:
                if (y0 + LEGEND_ROW_H) > (plot_rect.bottom() - 4):
                    break
                s = widget.series[series_idx]
                muted = bool(s.get("muted", False))
                highlighted = bool(s.get("highlighted", False))

                self._draw_legend_icon(painter, x0, y0 + 1, LEGEND_ICON_SIZE, legend_type, color, muted=muted, highlighted=highlighted)

                painter.setFont(qfont(8, bold=highlighted))
                painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
                text_rect = QRectF(x0 + 18, y0, max_x - (x0 + 18), LEGEND_ROW_H)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)
                hit_rect = QRectF(x0, y0, widget._legend_reserved_w, LEGEND_ROW_H)
                widget._legend_hitboxes.append((hit_rect, series_idx))

                if widget._legend.drag_active and widget._legend.drop_target_idx == series_idx:
                    painter.setPen(QPen(QColor(30, 30, 30), 2))
                    painter.drawLine(QPointF(hit_rect.left(), hit_rect.top() - 1), QPointF(hit_rect.right(), hit_rect.top() - 1))

                y0 += LEGEND_ROW_GAP

            y0 += 6
        painter.restore()

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

    def _collect_hover_tooltip_data(self, widget, hover_index, val_x, plot_rect, x_state, y_state_left, y_state_right=None):
        tooltip_lines = []
        marker_pts = []

        for s in widget.series:
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            if not xs or not ys or len(xs) <= hover_index or len(ys) <= hover_index:
                continue

            try:
                if abs(float(xs[hover_index]) - float(val_x)) > 1e-6:
                    continue
            except Exception:
                continue

            color = s.get("color") or DEFAULT_SERIES_COLOR
            muted = bool(s.get("muted", False))
            label = (s.get("label") or "").strip() or widget.tr("Series")
            val_y = ys[hover_index]
            series_y_labels = s.get("y_categorical_labels") or (y_state_left.get("y_categorical_labels") if y_state_left else None)
            if series_y_labels:
                try:
                    val_y_str = series_y_labels[int(round(val_y))]
                except Exception:
                    val_y_str = str(val_y)
            else:
                val_y_str = self._format_value_full(val_y)

            tooltip_lines.append((color, muted, f"{label}: ", val_y_str, ""))
            axis = (s.get("y_axis") or "left")
            y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
            marker_pts.append((color, muted, self._to_screen(val_x, val_y, plot_rect, x_state, y_state)))

        return tooltip_lines, marker_pts

    def _draw_tooltip_box(self, widget, painter, header_text, tooltip_lines, val_x, hover_val_y, plot_rect, x_state, y_state):
        painter.save()
        font_tt = qfont(8)
        font_tt_bold = QFont(font_tt)
        font_tt_bold.setBold(True)
        painter.setFont(font_tt)
        fm = painter.fontMetrics()
        fm_bold = QFontMetrics(font_tt_bold)

        header_w = fm_bold.horizontalAdvance(header_text)
        series_max_w = 0
        for _c, _m, prefix, value, suffix in tooltip_lines:
            row_w = fm.horizontalAdvance(prefix) + fm_bold.horizontalAdvance(value) + fm.horizontalAdvance(suffix)
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

        pt_hover = self._to_screen(val_x, hover_val_y if hover_val_y is not None else y_state["min_y"], plot_rect, x_state, y_state)
        tt_x = int(pt_hover.x() + 10)
        tt_y = int(pt_hover.y() - 10 - rect_h)
        if tt_x + rect_w > widget.width():
            tt_x = int(pt_hover.x() - 10 - rect_w)
        if tt_y < 0:
            tt_y = int(pt_hover.y() + 10)
        if tt_x < 0:
            tt_x = 0
        if tt_y + rect_h > widget.height():
            tt_y = max(0, widget.height() - int(rect_h) - 1)

        rect_tt = QRectF(tt_x, tt_y, rect_w, rect_h)
        painter.setPen(QPen(TOOLTIP_BORDER, 1))
        painter.setBrush(Qt.GlobalColor.white)
        painter.drawRect(rect_tt)

        header_x = rect_tt.left() + pad
        header_baseline_y = rect_tt.top() + pad + fm.ascent()
        painter.setPen(Qt.GlobalColor.black)
        painter.setFont(font_tt_bold)
        painter.drawText(QPointF(header_x, header_baseline_y), header_text)

        sep_y = rect_tt.top() + pad + line_h + header_gap
        painter.setPen(QPen(TOOLTIP_SEPARATOR, 1))
        painter.drawLine(QPointF(rect_tt.left() + pad, sep_y), QPointF(rect_tt.right() - pad, sep_y))

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

    def _draw_hover_overlay(self, widget, painter, plot_rect, x_state, y_state_left, y_state_right=None):
        hover_series = None
        if widget._hover_series_idx is not None and 0 <= widget._hover_series_idx < len(widget.series):
            hover_series = widget.series[widget._hover_series_idx]
        if hover_series is not None and widget.hover_index is not None:
            xs0 = hover_series.get("x", []) or []
            ys0 = hover_series.get("y", []) or []
            if not xs0 or not ys0 or not (0 <= widget.hover_index < len(xs0)):
                hover_series = None

        if hover_series is None or widget.hover_index is None:
            return

        xs0 = hover_series.get("x", []) or []
        val_x = xs0[widget.hover_index]

        axis = (hover_series.get("y_axis") or "left")
        y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
        pt_rule = self._to_screen(val_x, y_state["min_y"], plot_rect, x_state, y_state)
        painter.setPen(QPen(QColor(255, 110, 110), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(pt_rule.x(), plot_rect.top()), QPointF(pt_rule.x(), plot_rect.bottom()))

        header_text = widget.tr("Time: %1").replace("%1", self._format_absolute_time_hours(val_x))
        tooltip_lines, marker_pts = self._collect_hover_tooltip_data(widget, widget.hover_index, val_x, plot_rect, x_state, y_state_left, y_state_right)

        for color, muted, pt in marker_pts:
            c = QColor(color)
            if muted:
                c.setAlpha(90)
            painter.setPen(QPen(c, 2))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(pt, 4, 4)

        hover_val_y = None
        try:
            hover_val_y = (hover_series.get("y", []) or [])[widget.hover_index]
        except Exception:
            hover_val_y = None

        self._draw_tooltip_box(widget, painter, header_text, tooltip_lines, val_x, hover_val_y, plot_rect, x_state, y_state)

