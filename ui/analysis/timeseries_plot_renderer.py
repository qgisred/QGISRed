# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import re
from qgis.PyQt.QtCore import QCoreApplication, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QPen, QPolygonF

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    compute_nice_time_scale_hours,
    estimate_max_ticks,
    format_number_tick,
)

from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, normalize_element
from .timeseries_axis_settings import TimeSeriesAxisSettings, build_fixed_linear_scale
from .timeseries_time_utils import civil_time_parts, format_civil_time, merge_time_of_day_x_ticks
from .timeseries_plot_style import (
    AXIS_MAX_TICKS,
    BORDER_COLOR,
    DEFAULT_SERIES_COLOR,
    GRID_COLOR,
    LEGEND_ICON_SIZE,
    LEGEND_POINT_SYMBOL_SIZE_MAX,
    LEGEND_OUTSIDE_BOTTOM_EXTRA,
    LEGEND_OUTSIDE_TOP_EXTRA,
    LEGEND_ROW_GAP,
    LEGEND_ROW_H,
    PLOT_BG_COLOR,
    PLOT_TOP_PAD,
    TEXT_DARK,
    TOOLTIP_BORDER,
    TOOLTIP_SEPARATOR,
    qfont,
)


class TimeSeriesPlotRenderer:
    _UNIT_RE = re.compile(r"\(([^()]+)\)\s*$")
    _UNIT_ANY_RE = re.compile(r"\(([^()]+)\)")
    _TOOLTIP_DECIMAL_LIMIT = 100_000.0
    _AXIS_TICK_FONT_SIZE = 10
    _AXIS_TITLE_FONT_SIZE = 10
    _TOOLTIP_ICON_SIZE = 8
    _HOVER_MARKER_ICON_SIZE = 10
    _TIME_TOKEN_RE = re.compile(r"^(-?\d+)([dhms])$")
    _POINT_VALUE_MIN_SPACING_PX = 52.0

    def _extract_unit_from_magnitude(self, magnitude: str) -> str:
        magnitude = (magnitude or "").strip()
        if not magnitude:
            return ""
        units = [u.strip() for u in self._UNIT_ANY_RE.findall(magnitude)]
        if not units:
            return ""
        seen = set()
        out = []
        for u in units:
            if not u or u in seen:
                continue
            seen.add(u)
            out.append(u)
        return ", ".join(out)

    def _axis_title_from_magnitude(self, magnitude: str) -> str:
        raw = (magnitude or "").strip()
        unit = self._extract_unit_from_magnitude(raw)
        return unit or raw

    def _axis_title_for_count(self, title_raw: str, magnitude_count: int) -> str:
        raw = (title_raw or "").strip()
        if not raw:
            return ""
        if magnitude_count <= 1:
            return raw
        if magnitude_count > 2:
            return self._axis_title_from_magnitude(raw)
        return raw

    def render(self, widget, painter: QPainter) -> None:
        if not widget.series:
            widget._last_y_state_left = None
            widget._last_y_state_right = None
            self._draw_no_data_message(widget, painter)
            return

        painter.setRenderHint(PAINTER_ANTIALIASING)
        w = widget.width()
        h = widget.height()

        gen = getattr(widget, "_general_cfg", None)
        if gen is not None:
            painter.fillRect(widget.rect(), gen.widget_bg_qcolor())
        else:
            painter.fillRect(widget.rect(), Qt.GlobalColor.white)

        all_x, all_y, y_categorical_labels, any_stepped = widget._axisSeriesData(widget.series)
        if not all_x or not all_y:
            widget._last_y_state_left = None
            widget._last_y_state_right = None
            self._draw_no_data_message(widget, painter)
            return

        widget.data_x = all_x
        widget.data_y = all_y
        widget.y_categorical_labels = y_categorical_labels
        widget.is_stepped = any_stepped

        plot_rect, local_margin_left, right_axis_label_w = widget.getPlotRect()
        widget._legend_hitboxes = []
        widget._legend_delete_hitboxes = []

        title_txt = ""
        if gen is not None and (getattr(gen, "title", "") or "").strip():
            title_txt = (gen.title or "").strip()
        elif widget.title:
            title_txt = widget.title

        if title_txt:
            painter.save()
            if gen is not None:
                title_size = max(5, min(int(getattr(gen, "title_font_size", 10) or 10), 48))
                title_font = QFont(gen.resolved_title_font_family(), title_size)
                title_color = gen.title_qcolor()
            else:
                title_font = qfont(10)
                title_color = QColor("#000000")
            title_font.setBold(True)
            painter.setFont(title_font)
            painter.setPen(QPen(title_color, 1))
            title_area_h = max(float(widget.margin_top), float(plot_rect.top() - PLOT_TOP_PAD))
            painter.drawText(
                QRectF(plot_rect.left(), 0, plot_rect.width(), title_area_h),
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom,
                title_txt,
            )
            painter.restore()

        if gen is not None:
            painter.fillRect(plot_rect, gen.plot_bg_qcolor())
            painter.setPen(QPen(gen.frame_qcolor(), max(1, int(getattr(gen, "frame_width", 1) or 1))))
        else:
            painter.fillRect(plot_rect, PLOT_BG_COLOR)
            painter.setPen(QPen(BORDER_COLOR, 1))
        painter.drawRect(plot_rect)

        left_series, right_series = widget._seriesByAxis()
        _lx, all_y_left, y_cat_left, _st_left = widget._axisSeriesData(left_series)
        _rx, all_y_right, y_cat_right, _st_right = widget._axisSeriesData(right_series)
        left_active = bool(getattr(widget, "_left_axis_active", True))
        right_active = bool(getattr(widget, "_right_axis_active", False))
        y_state_left = None
        if left_active:
            y_state_left = self._compute_y_axis_state(widget, all_y_left, y_cat_left, plot_rect, painter, y_axis_side="left")
        y_state_right = None
        if right_active:
            y_state_right = self._compute_y_axis_state(widget, all_y_right, y_cat_right, plot_rect, painter, y_axis_side="right")
        widget._last_y_state_left = y_state_left
        widget._last_y_state_right = y_state_right
        y_state_primary = y_state_left if y_state_left is not None else y_state_right

        painter.setFont(qfont(9))
        x_state = self._compute_x_axis_state(widget, widget.data_x, plot_rect, painter)
        widget._last_x_state = x_state
        if (
            getattr(widget, "_axis_cfg_x", None) is not None
            and widget._axis_cfg_x.auto_scale
            and widget._view_x_min is None
            and widget._view_x_max is None
        ):
            widget._last_auto_x_state = x_state
        self._draw_grid_and_axes(
            widget,
            painter,
            plot_rect,
            local_margin_left,
            right_axis_label_w,
            x_state,
            y_state_left,
            y_state_right,
            y_state_primary=y_state_primary,
        )

        if gen is not None:
            axis_pen = QPen(gen.frame_qcolor(), max(1, int(getattr(gen, "frame_width", 1) or 1)))
        else:
            axis_pen = QPen(Qt.GlobalColor.black, 2)
        painter.setPen(axis_pen)
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())
        if y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            painter.drawLine(plot_rect.bottomRight(), plot_rect.topRight())

        self._draw_axis_titles(
            widget,
            painter,
            plot_rect,
            local_margin_left,
            right_axis_label_w,
            h,
            y_state_left,
            y_state_right,
            left_active=left_active,
            right_active=right_active,
        )
        self._draw_series_curves(widget, painter, plot_rect, x_state, y_state_left, y_state_right)
        self._draw_legend(widget, painter, plot_rect, x_state)
        self._draw_hover_overlay(widget, painter, plot_rect, x_state, y_state_left, y_state_right)

    def _draw_no_data_message(self, widget, painter: QPainter) -> None:
        painter.drawText(widget.rect(), Qt.AlignmentFlag.AlignCenter, QCoreApplication.translate("TimeSeriesPlotWidget", "No data to display, please select an element on the map."))

    def _tick_qfont(self, cfg: TimeSeriesAxisSettings, *, bold: bool = False) -> QFont:
        f = QFont(cfg.resolved_font_family(), max(5, min(int(cfg.tick_font_size), 48)))
        f.setBold(bold)
        return f

    def _title_qfont(self, cfg: TimeSeriesAxisSettings, *, bold: bool = False) -> QFont:
        f = QFont(cfg.resolved_title_font_family(), max(5, min(int(getattr(cfg, "title_font_size", 10) or 10), 48)))
        f.setBold(bold)
        return f

    def _line_pen_style(self, style: str):
        t = (style or "solid").strip().lower()
        if t == "dash":
            return Qt.PenStyle.DashLine
        if t == "dot":
            return Qt.PenStyle.DotLine
        if t == "dashdot":
            return Qt.PenStyle.DashDotLine
        return Qt.PenStyle.SolidLine

    def _series_qcolor(self, color, fallback=DEFAULT_SERIES_COLOR) -> QColor:
        c = QColor(color or fallback)
        if not c.isValid():
            c = QColor(fallback)
        return c

    def _marker_symbol(self, symbol: str) -> str:
        t = (symbol or "circle").strip().lower()
        if t in ("circle", "square", "triangle", "diamond", "cross"):
            return t
        return "circle"

    @staticmethod
    def _label_boxes_overlap(ax: float, ay: float, aw: float, ah: float, bx: float, by: float, bw: float, bh: float) -> bool:
        return not (ax + aw < bx or bx + bw < ax or ay + ah < by or by + bh < ay)

    def _series_result_decimal_places(self, s) -> Optional[int]:
        if s.get("y_categorical_labels"):
            return None
        try:
            parts = str(s.get("series_key") or "").split(":")
            if len(parts) < 3 or not parts[2]:
                return None
            return QGISRedFieldUtils().getDecimals(normalize_element(parts[0]), parts[2])
        except Exception:
            return None

    def _format_value_with_decimal_places(self, value, decimal_places: Optional[int] = None) -> str:
        if value is None:
            return ""
        if decimal_places is None:
            return self._format_value_full(value)
        try:
            v = float(value)
            dec = max(0, int(decimal_places))
            return f"{v:.{dec}f}"
        except (TypeError, ValueError):
            return str(value)

    def _point_value_text(self, s, value) -> str:
        series_y_labels = s.get("y_categorical_labels")
        if series_y_labels:
            try:
                return str(series_y_labels[int(round(value))])
            except Exception:
                return str(value)
        return self._format_value_with_decimal_places(value, self._series_result_decimal_places(s))

    def _select_point_value_label_indices(
        self,
        points: Sequence[QPointF],
        texts: Sequence[str],
        fm: QFontMetrics,
        plot_rect: QRectF,
        *,
        x_off: float,
        y_off: float,
        min_spacing_px: Optional[float] = None,
    ) -> List[int]:
        n = min(len(points), len(texts))
        if n <= 0:
            return []

        pad = 3.0
        required_x_gap = min(
            96.0,
            max(
                float(fm.horizontalAdvance(texts[i])) + 2.0 * pad + 4.0
                for i in range(n)
            ),
        )
        base_spacing = max(
            float(min_spacing_px or self._POINT_VALUE_MIN_SPACING_PX),
            float(plot_rect.width()) / 24.0,
        )

        point_gaps = []
        for i in range(1, n):
            gap = abs(float(points[i].x()) - float(points[i - 1].x()))
            if gap > 0.5:
                point_gaps.append(gap)
        min_point_gap = min(point_gaps) if point_gaps else float(plot_rect.width())

        # Zoom in: puntos más separados en pantalla → probar todas las etiquetas.
        if min_point_gap >= required_x_gap * 0.65:
            candidates = list(range(n))
        else:
            label_spacing = max(required_x_gap, min(base_spacing, min_point_gap * 0.85))
            max_labels = max(2, min(n, int(float(plot_rect.width()) // label_spacing)))
            if n <= max_labels:
                candidates = list(range(n))
            else:
                candidates = []
                x0 = float(points[0].x())
                x1 = float(points[-1].x())
                if abs(x1 - x0) < 1.0:
                    step = max(1, n // max_labels)
                    candidates = list(range(0, n, step))[:max_labels]
                else:
                    for k in range(max_labels):
                        target_x = x0 + (x1 - x0) * float(k) / float(max(max_labels - 1, 1))
                        best_i = min(range(n), key=lambda i: abs(float(points[i].x()) - target_x))
                        if best_i not in candidates:
                            candidates.append(best_i)

        selected: List[int] = []
        occupied: List[Tuple[float, float, float, float]] = []
        plot_left = float(plot_rect.left())
        plot_right = float(plot_rect.right())
        plot_top = float(plot_rect.top())
        plot_bottom = float(plot_rect.bottom())
        for i in sorted(candidates, key=lambda idx: float(points[idx].x())):
            pt = points[i]
            px = float(pt.x())
            py = float(pt.y())
            if not (plot_left <= px <= plot_right and plot_top <= py <= plot_bottom):
                continue
            text = texts[i]
            tw = min(96.0, max(4.0, float(fm.horizontalAdvance(text))))
            th = min(24.0, max(8.0, float(fm.height())))
            x = px + float(x_off)
            y = py + float(y_off) - float(fm.descent())
            rx = x - pad
            ry = y - th - pad
            rw = tw + 2.0 * pad
            rh = th + 2.0 * pad
            if any(self._label_boxes_overlap(rx, ry, rw, rh, ox, oy, ow, oh) for ox, oy, ow, oh in occupied):
                continue
            selected.append(i)
            occupied.append((rx, ry, rw, rh))
        return selected

    def _select_marker_indices(
        self,
        points: Sequence[QPointF],
        plot_rect: QRectF,
        marker_size: float,
        *,
        is_stepped: bool = False,
        ys: Optional[Sequence[float]] = None,
    ) -> List[int]:
        n = len(points)
        if n <= 0:
            return []
        if is_stepped and ys is not None and len(ys) >= n:
            indices = [0]
            for i in range(1, n):
                try:
                    if ys[i] != ys[i - 1]:
                        indices.append(i)
                except Exception:
                    continue
            if n > 1 and indices[-1] != n - 1:
                indices.append(n - 1)
            return indices
        min_spacing = max(float(marker_size) * 1.75, self._POINT_VALUE_MIN_SPACING_PX)
        texts = [""] * n
        fm = QFontMetrics(qfont(8))
        return self._select_point_value_label_indices(
            points,
            texts,
            fm,
            plot_rect,
            x_off=0.0,
            y_off=0.0,
            min_spacing_px=min_spacing,
        )

    def _draw_point_marker(
        self,
        painter: QPainter,
        pt: QPointF,
        size: float,
        symbol: str,
        color: QColor,
        *,
        hollow: bool = True,
        emphasized: bool = False,
    ) -> None:
        r = max(1.0, float(size) / 2.0)
        if emphasized:
            r = min(r + 1.25, 14.0)
        pen_w = 2.4 if emphasized else 1.4
        painter.setPen(QPen(color, pen_w))
        if hollow:
            painter.setBrush(QColor(255, 255, 255))
        else:
            painter.setBrush(color)
        t = self._marker_symbol(symbol)
        if t == "cross":
            painter.drawLine(QPointF(pt.x() - r, pt.y() - r), QPointF(pt.x() + r, pt.y() + r))
            painter.drawLine(QPointF(pt.x() - r, pt.y() + r), QPointF(pt.x() + r, pt.y() - r))
            return
        if t == "square":
            painter.drawRect(QRectF(pt.x() - r, pt.y() - r, 2 * r, 2 * r))
        elif t == "triangle":
            painter.drawPolygon(QPolygonF([
                QPointF(pt.x(), pt.y() - r),
                QPointF(pt.x() + r, pt.y() + r),
                QPointF(pt.x() - r, pt.y() + r),
            ]))
        elif t == "diamond":
            painter.drawPolygon(QPolygonF([
                QPointF(pt.x(), pt.y() - r),
                QPointF(pt.x() + r, pt.y()),
                QPointF(pt.x(), pt.y() + r),
                QPointF(pt.x() - r, pt.y()),
            ]))
        else:
            painter.drawEllipse(pt, r, r)

    def _legend_row_font(self, s, *, bold: bool = False) -> QFont:
        try:
            size = max(6, min(int(s.get("legend_font_size") or 8), 32))
        except Exception:
            size = 8
        f = qfont(size, bold=bold)
        fam = (s.get("legend_font_family") or "").strip()
        if fam:
            f.setFamily(fam)
        return f

    def _expand_range(self, minimum: float, maximum: float) -> Tuple[float, float]:
        value_range = maximum - minimum
        if value_range == 0:
            pad = abs(maximum) * 0.1
            if pad == 0:
                pad = 1
            return minimum - pad, maximum + pad
        return minimum - value_range * 0.1, maximum + value_range * 0.1

    def _compute_y_axis_state(self, widget, all_y, y_categorical_labels, plot_rect, painter, *, y_axis_side: str = "left"):
        cfg = widget._axis_cfg_y_left if y_axis_side == "left" else widget._axis_cfg_y_right
        painter.save()
        painter.setFont(self._tick_qfont(cfg))
        fm_h = painter.fontMetrics().height()
        dec = cfg.decimal_places_or_none()

        if y_categorical_labels:
            min_y = 0
            max_y = len(y_categorical_labels) - 1
            min_y, max_y = self._expand_range(min_y, max_y)
            y_tick_values = list(range(len(y_categorical_labels)))
            painter.restore()
            return {
                "min_y": min_y,
                "max_y": max_y,
                "num_ticks_y": len(y_tick_values) - 1,
                "y_tick_values": y_tick_values,
                "y_step": None,
                "y_categorical_labels": y_categorical_labels,
                "axis_cfg": cfg,
                "decimals": dec,
            }

        if not all_y:
            painter.restore()
            return {
                "min_y": 0.0,
                "max_y": 1.0,
                "num_ticks_y": 1,
                "y_tick_values": [0.0, 1.0],
                "y_step": 0.5,
                "y_categorical_labels": None,
                "axis_cfg": cfg,
                "decimals": dec,
            }

        min_y, max_y = min(all_y), max(all_y)
        if cfg.auto_scale:
            max_ticks_y = estimate_max_ticks(plot_rect.height(), fm_h + 6, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
            y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
        else:
            lo, hi = float(cfg.fixed_min), float(cfg.fixed_max)
            if hi <= lo:
                hi = lo + 1.0
            y_scale = build_fixed_linear_scale(lo, hi, cfg.fixed_divisions)
        painter.restore()
        return {
            "min_y": y_scale.axis_min,
            "max_y": y_scale.axis_max,
            "num_ticks_y": y_scale.divisions,
            "y_tick_values": y_scale.ticks(),
            "y_step": y_scale.step,
            "y_categorical_labels": None,
            "axis_cfg": cfg,
            "decimals": dec,
        }

    def _is_time_of_day_format(self, hour_format: str) -> bool:
        return (hour_format or "").strip() in ("hm", "hm_ampm", "tod_hm", "tod_ampm")

    def _estimate_x_axis_label_px(self, painter, *, has_days: bool, hour_format: str = "hm", x_precision: str = "hms") -> float:
        fm = painter.fontMetrics()
        hour_format = (hour_format or "hm").strip()
        x_precision = (x_precision or "hms").strip()
        if x_precision == "h":
            if hour_format in ("hm_ampm", "tod_ampm"):
                time_sample = "12 pm"
            elif hour_format == "elapsed_hm":
                time_sample = "999"
            else:
                time_sample = "23"
        elif hour_format in ("hm_ampm", "tod_ampm"):
            time_sample = "12:59 pm"
        elif hour_format == "elapsed_hm":
            time_sample = "999:59"
        else:
            time_sample = "999" if hour_format == "h" else "23:59"
        if has_days:
            w_top = fm.horizontalAdvance(time_sample)
            w_bottom = fm.horizontalAdvance("999d")
            return max(w_top, w_bottom) + 18
        return fm.horizontalAdvance(time_sample) + 18

    def _format_time_axis_tick(self, hours: float, *, hour_format: str, day_format: str, start_clock_seconds: int = 0, x_precision: str = "hms") -> str:
        total_seconds = int(round(hours * 3600))
        sign = "-" if total_seconds < 0 else ""
        abs_seconds = abs(total_seconds)
        d = abs_seconds // 86400
        rem = abs_seconds % 86400
        h = rem // 3600
        m = (rem % 3600) // 60
        s = rem % 60

        hour_format = (hour_format or "auto").strip()
        if hour_format == "hms":
            hour_format = "hm"
        day_format = (day_format or "split_days").strip()
        x_precision = (x_precision or "hms").strip()

        if self._is_time_of_day_format(hour_format):
            parts = civil_time_parts(hours, start_clock_seconds)
            if parts is None:
                return ""
            d, h, m, s = parts
            am_pm = hour_format in ("hm_ampm", "tod_ampm")
            if s > 0:
                if am_pm:
                    sfx = "am" if h < 12 else "pm"
                    dh = h % 12 or 12
                    top = f"{dh}:{m:02d}:{s:02d} {sfx}"
                else:
                    top = f"{h}:{m:02d}:{s:02d}"
            elif x_precision == "h":
                if am_pm:
                    suffix = "am" if h < 12 else "pm"
                    dh = h % 12 or 12
                    top = f"{dh} {suffix}"
                else:
                    top = f"{h}"
            else:
                if am_pm:
                    suffix = "am" if h < 12 else "pm"
                    dh = h % 12 or 12
                    top = f"{dh}:{m:02d} {suffix}"
                else:
                    top = f"{h}:{m:02d}"
            if day_format == "split_days" and d > 0 and h == 0 and m == 0 and s == 0:
                if x_precision == "hms":
                    return f"{sign}{d}d {top}"
                return f"{top}\n{d}d"
            return top

        if day_format == "total_hours":
            total_h = abs_seconds // 3600
            if s > 0:
                return f"{sign}{total_h}:{m:02d}:{s:02d}"
            if hour_format == "h" or x_precision == "h":
                return f"{sign}{total_h}"
            if hour_format == "auto" and m == 0:
                return f"{sign}{total_h}"
            return f"{sign}{total_h}:{m:02d}"

        if s > 0:
            top = f"{sign}{h}:{m:02d}:{s:02d}"
        elif hour_format == "h" or x_precision == "h":
            top = f"{sign}{h}"
        elif hour_format == "auto":
            top = f"{sign}{h}" if m == 0 else f"{sign}{h}:{m:02d}"
        else:
            top = f"{sign}{h}:{m:02d}"
        if d > 0 and h == 0 and m == 0 and s == 0:
            if x_precision == "hms":
                return f"{sign}{d}d {top}"
            return f"{top}\n{sign}{d}d"
        return top

    def _compute_x_axis_state(self, widget, all_x, plot_rect, painter):
        cfg = widget._axis_cfg_x
        painter.save()
        painter.setFont(self._tick_qfont(cfg))
        data_min, data_max = min(all_x), max(all_x)
        if data_max == data_min:
            data_max = data_min + 1

        if cfg.auto_scale:
            min_x, max_x = data_min, data_max
            view_x_min = getattr(widget, "_view_x_min", None)
            view_x_max = getattr(widget, "_view_x_max", None)
            has_explicit_view = view_x_min is not None and view_x_max is not None
            if view_x_min is not None:
                min_x = view_x_min
            if view_x_max is not None:
                max_x = view_x_max
            if max_x <= min_x:
                max_x = min_x + 1
        else:
            min_x, max_x = float(cfg.fixed_min), float(cfg.fixed_max)
            has_explicit_view = False
            if max_x <= min_x:
                max_x = min_x + 1

        hour_format = (getattr(cfg, "x_hour_format", "") or "hm").strip()
        day_format = (getattr(cfg, "x_day_format", "") or "split_days").strip()
        x_precision = (getattr(cfg, "x_precision", "hms") or "hms").strip()
        start_clock_seconds = int(getattr(widget, "_start_clock_seconds", 0) or 0)
        if self._is_time_of_day_format(hour_format):
            min_civil = civil_time_parts(min_x, start_clock_seconds)
            max_civil = civil_time_parts(max_x, start_clock_seconds)
            has_days = (
                day_format == "split_days"
                and min_civil is not None
                and max_civil is not None
                and max_civil[0] > min_civil[0]
            )
        else:
            has_days = (max_x >= 24) and (day_format == "split_days")
        label_px = self._estimate_x_axis_label_px(painter, has_days=has_days, hour_format=hour_format, x_precision=x_precision)
        if cfg.auto_scale:
            max_ticks_x = estimate_max_ticks(plot_rect.width(), label_px, min_ticks=2, max_ticks=AXIS_MAX_TICKS)
            x_scale = compute_nice_time_scale_hours(min_x, max_x, max_ticks_x)
            # Keep plot bounds exactly on data/view range (no extra margin to the right).
            # Use the nice scale only to generate readable ticks.
            eps = 1e-9
            x_tick_values = [t for t in x_scale.ticks() if (min_x - eps) <= t <= (max_x + eps)]
        else:
            x_scale = build_fixed_linear_scale(min_x, max_x, cfg.fixed_divisions)
            x_tick_values = x_scale.ticks()
        x_range = max_x - min_x
        if has_days and self._is_time_of_day_format(hour_format):
            plot_w = max(float(plot_rect.width()), 1.0)
            min_sep_hours = (label_px / plot_w) * max(x_range, 1e-9) * 1.05
            x_tick_values = merge_time_of_day_x_ticks(
                x_tick_values,
                min_hours=min_x,
                max_hours=max_x,
                start_clock_seconds=start_clock_seconds,
                min_sep_hours=min_sep_hours,
            )
        if x_range == 0:
            x_range = 1
        painter.restore()
        return {
            "min_x": min_x,
            "max_x": max_x,
            "x_range": x_range,
            "x_scale": x_scale,
            "x_tick_values": x_tick_values,
            "has_days": has_days,
            "label_px": label_px,
            "axis_cfg": cfg,
            "start_clock_seconds": start_clock_seconds,
            "x_precision": x_precision,
        }

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
        s = rem % 60

        parts = []
        if d > 0:
            parts.append((str(d), "d"))
            if h == 0 and m == 0 and s == 0:
                pass
            else:
                parts.append((str(h), "h"))
                if m > 0 or s > 0:
                    parts.append((str(m), "m"))
                if s > 0:
                    parts.append((str(s), "s"))
        else:
            if h == 0 and m == 0 and s > 0:
                parts.append((str(s), "s"))
            else:
                parts.append((str(h), "h"))
                if m > 0 or s > 0:
                    parts.append((str(m), "m"))
                if s > 0:
                    parts.append((str(s), "s"))

        if not parts:
            parts = [("0", "h")]

        rendered = []
        for i, (num, unit) in enumerate(parts):
            if i == 0 and sign:
                rendered.append(f"{sign}{num}{unit}")
            else:
                rendered.append(f"{num}{unit}")
        return " ".join(rendered)

    def _build_styled_footer_segments(self, instant_text: str):
        template = QCoreApplication.translate("TimeSeriesPlotWidget", "Time: %1")
        if "%1" in template:
            prefix, suffix = template.split("%1", 1)
        else:
            prefix, suffix = (template + " "), ""

        segments = []
        if prefix:
            segments.append((prefix, False))

        tokens = [t for t in (instant_text or "").split(" ") if t]
        for i, token in enumerate(tokens):
            m = self._TIME_TOKEN_RE.match(token)
            if m:
                segments.append((m.group(1), True))
                segments.append((m.group(2), False))
            else:
                segments.append((token, False))
            if i < len(tokens) - 1:
                segments.append((" ", False))

        if suffix:
            segments.append((suffix, False))
        return segments

    def _format_absolute_time_hours_axis(
        self,
        hours: float,
        *,
        hour_format: str = "auto",
        day_format: str = "split_days",
        start_clock_seconds: int = 0,
        x_precision: str = "hm",
    ) -> str:
        return self._format_time_axis_tick(
            hours,
            hour_format=hour_format,
            day_format=day_format,
            start_clock_seconds=start_clock_seconds,
            x_precision=x_precision,
        )

    def _format_tick_number(self, value: float, step: float, dec: int | None) -> str:
        if dec is None:
            return format_number_tick(value, step)
        try:
            return format_number_tick(value, step, decimal_places=dec)
        except TypeError:
            return format_number_tick(value, step)

    def _draw_grid_and_axes(
        self,
        widget,
        painter,
        plot_rect,
        local_margin_left,
        right_axis_label_w,
        x_state,
        y_state_left,
        y_state_right=None,
        *,
        y_state_primary=None,
    ):
        cfg_x = x_state.get("axis_cfg") or widget._axis_cfg_x
        y_state_primary = y_state_primary or y_state_left or y_state_right
        pen_grid = QPen(GRID_COLOR, 1, Qt.PenStyle.SolidLine)
        pen_grid_day_start = QPen(QColor(185, 195, 205), 1, Qt.PenStyle.SolidLine)
        pen_grid_day_start.setWidthF(1.2)
        tick_mark_len = 5.0

        if y_state_left is not None:
            cfg_yl = y_state_left.get("axis_cfg") or widget._axis_cfg_y_left
            painter.setFont(self._tick_qfont(cfg_yl))
            dec_yl = y_state_left.get("decimals")

            for i in range(y_state_left["num_ticks_y"] + 1):
                y_cat = y_state_left.get("y_categorical_labels") or widget.y_categorical_labels
                if y_cat:
                    val_y = i
                    label_text = y_cat[i]
                else:
                    val_y = y_state_left["y_tick_values"][i]
                    y_step = y_state_left.get("y_step") or 1.0
                    label_text = self._format_tick_number(val_y, y_step, dec_yl)

                pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state_left)
                if cfg_yl.show_grid:
                    painter.setPen(pen_grid)
                    painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
                painter.setPen(QPen(cfg_yl.tick_qcolor(), 1))
                if getattr(cfg_yl, "show_tick_marks", False):
                    painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.left() - tick_mark_len, pt.y()))
                painter.setFont(self._tick_qfont(cfg_yl))
                painter.drawText(QRectF(0, pt.y() - 10, local_margin_left - 5, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)

        if y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            cfg_yr = y_state_right.get("axis_cfg") or widget._axis_cfg_y_right
            dec_yr = y_state_right.get("decimals")
            painter.setFont(self._tick_qfont(cfg_yr))
            for i in range(y_state_right["num_ticks_y"] + 1):
                y_cat_r = y_state_right.get("y_categorical_labels")
                if y_cat_r:
                    val_y = i
                    label_text = y_cat_r[i]
                else:
                    val_y = y_state_right["y_tick_values"][i]
                    y_step_r = y_state_right.get("y_step") or 1.0
                    label_text = self._format_tick_number(val_y, y_step_r, dec_yr)
                pt = self._to_screen(x_state["min_x"], val_y, plot_rect, x_state, y_state_right)
                if cfg_yr.show_grid:
                    painter.setPen(pen_grid)
                    painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
                painter.setPen(QPen(cfg_yr.tick_qcolor(), 1))
                if getattr(cfg_yr, "show_tick_marks", False):
                    painter.drawLine(QPointF(plot_rect.right(), pt.y()), QPointF(plot_rect.right() + tick_mark_len, pt.y()))
                painter.setFont(self._tick_qfont(cfg_yr))
                painter.drawText(QRectF(plot_rect.right() + 5, pt.y() - 10, right_axis_label_w - 10, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label_text)

        if len(widget.data_x) > 1:
            tick_font_regular = self._tick_qfont(cfg_x)
            tick_font_bold = self._tick_qfont(cfg_x, bold=True)
            painter.setFont(tick_font_regular)
            fm_x = painter.fontMetrics()
            has_days = bool(x_state.get("has_days", x_state["max_x"] >= 24))
            tick_h = fm_x.height() * 2 + 4 if has_days else fm_x.height() + 6
            hour_format = (getattr(cfg_x, "x_hour_format", "") or "hm").strip()
            day_format = (getattr(cfg_x, "x_day_format", "") or "split_days").strip()
            x_precision = str(x_state.get("x_precision", getattr(cfg_x, "x_precision", "hms")) or "hms").strip()
            tick_w = float(x_state.get("label_px", self._estimate_x_axis_label_px(painter, has_days=has_days, hour_format=hour_format, x_precision=x_precision)))
            start_clock_seconds = int(x_state.get("start_clock_seconds", getattr(widget, "_start_clock_seconds", 0) or 0))
            for val_x in x_state.get("x_tick_values", x_state["x_scale"].ticks()):
                if y_state_primary is None:
                    continue
                pt = self._to_screen(val_x, y_state_primary["min_y"], plot_rect, x_state, y_state_primary)

                is_day_start = False
                if has_days:
                    if self._is_time_of_day_format(hour_format):
                        parts = civil_time_parts(val_x, start_clock_seconds)
                        is_day_start = bool(parts is not None and parts[0] > 0 and parts[1] == 0 and parts[2] == 0 and parts[3] == 0)
                    else:
                        mod_24 = val_x % 24.0
                        is_day_start = abs(mod_24) < 1e-6 or abs(mod_24 - 24.0) < 1e-6
                if cfg_x.show_grid:
                    painter.setPen(pen_grid_day_start if is_day_start else pen_grid)
                    painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))

                painter.setPen(QPen(cfg_x.tick_qcolor(), 1))
                if getattr(cfg_x, "show_tick_marks", False):
                    painter.drawLine(QPointF(pt.x(), plot_rect.bottom()), QPointF(pt.x(), plot_rect.bottom() + tick_mark_len))
                label_x = self._format_absolute_time_hours_axis(
                    val_x,
                    hour_format=hour_format,
                    day_format=day_format,
                    start_clock_seconds=start_clock_seconds,
                    x_precision=x_precision,
                )
                rect = QRectF(pt.x() - tick_w / 2, plot_rect.bottom() + 8, tick_w, tick_h)
                if "\n" in label_x:
                    top, bottom = (label_x.split("\n", 1) + [""])[:2]
                    if not is_day_start:
                        bottom = ""
                    fm_reg = QFontMetrics(tick_font_regular)
                    fm_bold = QFontMetrics(tick_font_bold)
                    pad_y = 0

                    painter.setFont(tick_font_regular)
                    painter.drawText(
                        QRectF(rect.left(), rect.top() + pad_y, rect.width(), fm_reg.height()),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                        top,
                    )

                    if bottom:
                        painter.setFont(tick_font_bold)
                        painter.drawText(
                            QRectF(rect.left(), rect.top() + pad_y + fm_reg.height(), rect.width(), fm_bold.height()),
                            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                            bottom,
                        )
                else:
                    painter.setFont(tick_font_regular)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, label_x)

    def _max_y_tick_label_width(self, painter, widget, y_state) -> float:
        if not y_state:
            return 0.0
        cfg = y_state.get("axis_cfg")
        if cfg is None:
            return 0.0
        painter.save()
        painter.setFont(self._tick_qfont(cfg))
        fm = painter.fontMetrics()
        dec = y_state.get("decimals")
        labels = []
        y_cat = y_state.get("y_categorical_labels") or widget.y_categorical_labels
        if y_cat:
            labels = [str(label) for label in y_cat]
        else:
            y_step = y_state.get("y_step") or 1.0
            labels = [self._format_tick_number(value, y_step, dec) for value in y_state.get("y_tick_values", [])]
        max_width = max((fm.horizontalAdvance(label) for label in labels), default=0)
        painter.restore()
        return float(max_width)

    def _draw_axis_titles(
        self,
        widget,
        painter,
        plot_rect,
        local_margin_left,
        right_axis_label_w,
        widget_h,
        y_state_left=None,
        y_state_right=None,
        *,
        left_active=True,
        right_active=False,
    ):
        cfg_x = widget._axis_cfg_x
        cfg_yl = widget._axis_cfg_y_left
        cfg_yr = widget._axis_cfg_y_right

        left_title = ""
        if left_active and y_state_left is not None:
            left_title = (cfg_yl.title or "").strip()
            if not left_title:
                left_title_raw = (widget._y_label_left or "").strip()
                left_count = len(getattr(widget, "_y_magnitudes_left", []) or [])
                left_title = self._axis_title_for_count(left_title_raw, left_count)
        if left_title:
            painter.save()
            painter.setFont(self._title_qfont(cfg_yl))
            painter.setPen(QPen(cfg_yl.title_qcolor(), 1))
            title_fm = QFontMetrics(self._title_qfont(cfg_yl))
            label_w = self._max_y_tick_label_width(painter, widget, y_state_left)
            title_gap = 10.0
            title_x = float(plot_rect.left()) - 5.0 - label_w - title_gap - float(title_fm.height()) / 2.0
            painter.translate(max(0.0, title_x), widget_h / 2)
            painter.rotate(-90)
            painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, left_title)
            painter.restore()

        if right_active and y_state_right is not None and right_axis_label_w and right_axis_label_w > 0:
            right_title = (cfg_yr.title or "").strip()
            if not right_title:
                right_title_raw = (widget._y_label_right or "").strip()
                right_count = len(getattr(widget, "_y_magnitudes_right", []) or [])
                right_title = self._axis_title_for_count(right_title_raw, right_count)
            if right_title:
                painter.save()
                painter.setFont(self._title_qfont(cfg_yr))
                painter.setPen(QPen(cfg_yr.title_qcolor(), 1))
                title_fm = QFontMetrics(self._title_qfont(cfg_yr))
                label_w = self._max_y_tick_label_width(painter, widget, y_state_right)
                title_gap = 10.0
                title_x = float(plot_rect.right()) + 5.0 + label_w + title_gap + float(title_fm.height()) / 2.0
                painter.translate(title_x, widget_h / 2)
                painter.rotate(-90)
                painter.drawText(QRectF(-120, -10, 240, 20), Qt.AlignmentFlag.AlignCenter, right_title)
                painter.restore()

        fm_x = QFontMetrics(self._tick_qfont(cfg_x))
        last_x_state = getattr(widget, "_last_x_state", None)
        has_days = bool(last_x_state.get("has_days", False)) if isinstance(last_x_state, dict) else bool(widget.data_x and max(widget.data_x) >= 24)
        tick_h = fm_x.height() * 2 + 4 if has_days else fm_x.height() + 6
        tick_top_pad = 8
        title_gap = 2
        fm_title_x = QFontMetrics(self._title_qfont(cfg_x))
        title_h = fm_title_x.height() + 2
        bottom_pad = 6
        title_top = plot_rect.bottom() + tick_top_pad + tick_h + title_gap

        min_y = plot_rect.bottom() + 4
        max_y = max(min_y, float(widget_h - bottom_pad - title_h))
        title_top = min(float(title_top), max_y)
        title_top = max(float(title_top), float(min_y))
        x_title = (cfg_x.title or widget.x_label or "").strip()
        if x_title:
            painter.setFont(self._title_qfont(cfg_x))
            painter.setPen(QPen(cfg_x.title_qcolor(), 1))
            painter.drawText(
                QRectF(local_margin_left, title_top, plot_rect.width(), title_h),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                x_title,
            )

    def _draw_series_curves(self, widget, painter, plot_rect, x_state, y_state_left, y_state_right=None):
        if not any((s.get("x") or []) and (s.get("y") or []) for s in widget.series):
            return

        painter.save()
        painter.setClipRect(plot_rect)

        for s in widget.series:
            line_visible = bool(s.get("visible", True))
            markers_visible = bool(s.get("show_markers", False))
            if not (line_visible or markers_visible):
                continue
            xs = s.get("x", []) or []
            ys = s.get("y", []) or []
            n = min(len(xs), len(ys))
            if n <= 0:
                continue

            color = s.get("color") or DEFAULT_SERIES_COLOR
            is_stepped = bool(s.get("is_stepped", False))
            muted = bool(s.get("muted", False))
            highlighted = bool(s.get("highlighted", False))
            draw_color = self._series_qcolor(color)
            try:
                width = max(0.5, min(float(s.get("line_width") or 2.0), 12.0))
            except Exception:
                width = 2.0
            if muted:
                draw_color.setAlpha(70)
                width = max(0.5, width * 0.6)
            if highlighted:
                draw_color.setAlpha(255)
                width = min(width + 1.0, 14.0)

            axis = (s.get("y_axis") or "left")
            y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
            points = [self._to_screen(xs[i], ys[i], plot_rect, x_state, y_state) for i in range(n)]

            if line_visible and n > 1:
                painter.setPen(QPen(draw_color, width, self._line_pen_style(s.get("line_style") or "solid")))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                path = QPainterPath()
                start_pt = points[0]
                path.moveTo(start_pt)
                for i in range(1, n):
                    next_pt = points[i]
                    if is_stepped:
                        path.lineTo(next_pt.x(), start_pt.y())
                        path.lineTo(next_pt)
                    else:
                        path.lineTo(next_pt)
                    start_pt = next_pt

                painter.drawPath(path)

            marker_color = self._series_qcolor(s.get("marker_color") or color, color)
            if muted:
                marker_color.setAlpha(70)
            elif highlighted:
                marker_color.setAlpha(255)
            try:
                marker_size = max(2.0, min(float(s.get("marker_size") or 6), 24.0))
            except Exception:
                marker_size = 6.0
            if highlighted:
                marker_size = min(marker_size + 1.0, 26.0)

            label_indices: List[int] = []
            value_label_texts: List[str] = []
            if bool(s.get("show_point_values", False)) and y_state is not None:
                font_lbl = qfont(8, bold=highlighted)
                fm_lbl = QFontMetrics(font_lbl)
                x_off = marker_size / 2.0 + 3.0
                y_off = -marker_size / 2.0 - 2.0
                value_label_texts = [self._point_value_text(s, ys[i]) for i in range(n)]
                label_indices = self._select_point_value_label_indices(
                    points,
                    value_label_texts,
                    fm_lbl,
                    plot_rect,
                    x_off=x_off,
                    y_off=y_off,
                )
            labeled = set(label_indices)

            if markers_visible:
                marker_symbol = str(s.get("marker_symbol") or "circle").strip()
                marker_hollow = bool(s.get("marker_hollow", True))
                painter.save()
                for i in range(n):
                    self._draw_point_marker(
                        painter,
                        points[i],
                        marker_size,
                        marker_symbol,
                        marker_color,
                        hollow=marker_hollow,
                        emphasized=i in labeled,
                    )
                painter.restore()

            if label_indices and y_state is not None:
                font_lbl = qfont(8, bold=highlighted)
                painter.setFont(font_lbl)
                fm_lbl = QFontMetrics(font_lbl)
                painter.setPen(marker_color)
                x_off = marker_size / 2.0 + 3.0
                y_off = -marker_size / 2.0 - 2.0
                for i in label_indices:
                    pt = points[i]
                    painter.drawText(
                        QPointF(pt.x() + x_off, pt.y() + y_off - fm_lbl.descent()),
                        value_label_texts[i],
                    )

        painter.restore()

    def _draw_legend_icon(
        self,
        painter,
        x,
        y,
        size,
        legend_type,
        color,
        muted=False,
        highlighted=False,
        line_style="solid",
        line_width=2.0,
        visible=True,
    ):
        c = QColor(color)
        if not visible:
            c.setAlpha(45)
        elif muted:
            c.setAlpha(80)
        try:
            pen_w = max(1.0, min(float(line_width or 2.0), 12.0))
        except Exception:
            pen_w = 2.0
        if highlighted:
            pen_w = min(pen_w + 1.0, 14.0)
        painter.setPen(QPen(c, pen_w, self._line_pen_style(line_style)))
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
        point_size = min(float(size), float(LEGEND_POINT_SYMBOL_SIZE_MAX))
        painter.drawEllipse(QPointF(cx, cy), (point_size - 4) / 2, (point_size - 4) / 2)

    def _draw_legend(self, widget, painter, plot_rect, x_state=None):
        groups = widget._legendGroups()
        if not groups:
            return

        gen = getattr(widget, "_general_cfg", None)
        legend_pos = (getattr(gen, "legend_position", "") or "right").strip() if gen is not None else "right"
        cols = 1
        sym = int(getattr(gen, "legend_symbol_size", LEGEND_ICON_SIZE) or LEGEND_ICON_SIZE) if gen is not None else LEGEND_ICON_SIZE
        sym = max(6, min(sym, 24))
        show_bg = bool(getattr(gen, "legend_show_background", False)) if gen is not None else False
        show_frame = bool(getattr(gen, "legend_show_frame", False)) if gen is not None else False

        if legend_pos in ("right", "left") and not getattr(widget, "_legend_reserved_w", 0):
            return
        if legend_pos in ("top", "bottom") and not getattr(widget, "_legend_reserved_h", 0):
            return

        painter.save()
        painter.setFont(qfont(8))
        btn_w = 10
        gap_cols = 8

        try:
            legend_w = float(widget._legendRequiredWidth())
            legend_h = float(widget._legendRequiredHeight())
        except Exception:
            legend_w = float(getattr(widget, "_legend_reserved_w", 0) or 0)
            legend_h = float(getattr(widget, "_legend_reserved_h", 0) or 0)

        if legend_pos in ("right", "left"):
            legend_w = float(getattr(widget, "_legend_reserved_w", legend_w) or legend_w)
            legend_h = float(plot_rect.height())
        if legend_pos in ("top", "bottom"):
            legend_w = float(plot_rect.width())
            legend_h = float(getattr(widget, "_legend_reserved_h", legend_h) or legend_h)

        pad = 6
        if legend_pos == "right":
            x0 = plot_rect.right() + 10 + (widget._right_axis_label_w if getattr(widget, "_right_axis_label_w", 0) else 0) + 20
            y0 = plot_rect.top() + pad
        elif legend_pos == "left":
            x0 = pad
            y0 = plot_rect.top() + pad
        elif legend_pos == "top":
            y0 = (plot_rect.top() - LEGEND_OUTSIDE_TOP_EXTRA - legend_h) + pad
            x0 = plot_rect.left() + pad
        elif legend_pos == "bottom":
            cfg_x = getattr(widget, "_axis_cfg_x", None)
            fm_x = QFontMetrics(self._tick_qfont(cfg_x)) if cfg_x is not None else QFontMetrics(qfont(10))
            has_days = bool(x_state.get("has_days", False)) if isinstance(x_state, dict) else bool(widget.data_x and max(widget.data_x) >= 24)
            tick_h = fm_x.height() * 2 + 4 if has_days else fm_x.height() + 6
            x_axis_bottom = plot_rect.bottom() + 8 + tick_h
            x_title = ((getattr(cfg_x, "title", "") if cfg_x is not None else "") or widget.x_label or "").strip()
            if x_title:
                x_axis_bottom += 2 + fm_x.height() + 2
            y0 = x_axis_bottom + LEGEND_OUTSIDE_BOTTOM_EXTRA
            x0 = plot_rect.left() + pad
        elif legend_pos == "inside_top_left":
            x0 = plot_rect.left() + pad
            y0 = plot_rect.top() + pad
        elif legend_pos == "inside_top_right":
            x0 = plot_rect.right() - legend_w + pad
            y0 = plot_rect.top() + pad
        elif legend_pos == "inside_bottom_left":
            x0 = plot_rect.left() + pad
            y0 = plot_rect.bottom() - legend_h + pad
        else:
            x0 = plot_rect.right() - legend_w + pad
            y0 = plot_rect.bottom() - legend_h + pad

        x0 = max(0.0, float(x0))
        y0 = max(0.0, float(y0))

        if show_bg or show_frame:
            rect_box = QRectF(x0 - pad, y0 - pad, max(0.0, legend_w), max(0.0, legend_h))
            if show_bg:
                bg = gen.legend_bg_qcolor() if gen is not None else QColor(245, 250, 255)
                painter.setBrush(bg)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
            if show_frame:
                frame_c = gen.frame_qcolor() if gen is not None else QColor(120, 120, 120)
                painter.setPen(QPen(frame_c, 1))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect_box)

        if legend_pos in ("right", "left"):
            content_rect = QRectF(x0, y0, max(0.0, legend_w - 2 * pad), max(0.0, legend_h - 2 * pad))
            painter.setClipRect(QRectF(x0 - pad, y0 - pad, max(0.0, legend_w), max(0.0, legend_h)))
            gap_cols = 8.0
            btn_w = 10
            btn_pad = 0
            item_col_w = max(40.0, max((widget._legendItemWidth(series_idx, label, sym) for _mag, items in groups for series_idx, _color, label, _legend_type in items), default=40.0))
            try:
                use_two_cols = bool(widget._legendSideNeedsTwoColumns())
            except Exception:
                use_two_cols = False
            item_cols = 2 if use_two_cols else 1
            item_col_w = min(item_col_w, max(40.0, (content_rect.width() - (item_cols - 1) * gap_cols) / float(item_cols)))

            def draw_item(series_idx, color, label, legend_type, cx, cy, col_w):
                if not (0 <= int(series_idx) < len(widget.series)):
                    return
                s = widget.series[int(series_idx)]
                muted = bool(s.get("muted", False))
                highlighted = bool(s.get("highlighted", False))
                line_visible = bool(s.get("visible", True))
                markers_visible = bool(s.get("show_markers", False))
                visible = line_visible or markers_visible
                icon_y = cy + (LEGEND_ROW_H - sym) / 2.0
                self._draw_legend_icon(
                    painter,
                    cx,
                    icon_y,
                    sym,
                    legend_type,
                    color,
                    muted=muted,
                    highlighted=highlighted,
                    line_style=s.get("line_style") or "solid",
                    line_width=s.get("line_width") or 2.0,
                    visible=visible,
                )

                row_font = self._legend_row_font(s, bold=highlighted)
                painter.setFont(row_font)
                if not visible:
                    painter.setPen(QColor(0, 0, 0, 75))
                else:
                    painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
                text_left = cx + sym + 6
                label_w = QFontMetrics(row_font).horizontalAdvance(label)
                max_text_w = max(0.0, (cx + col_w - btn_w - btn_pad) - text_left)
                text_draw_w = min(float(label_w), max_text_w)
                text_rect = QRectF(text_left, cy, max(0.0, text_draw_w), LEGEND_ROW_H)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

                hit_rect = QRectF(cx, cy, max(0.0, col_w), LEGEND_ROW_H)
                widget._legend_hitboxes.append((hit_rect, int(series_idx)))
                delete_x = min(cx + col_w - btn_w, text_left + text_draw_w + 2)
                delete_rect = QRectF(max(cx, delete_x), cy, btn_w, LEGEND_ROW_H)
                widget._legend_delete_hitboxes.append((delete_rect, int(series_idx)))
                painter.setFont(qfont(8, bold=True))
                painter.setPen(QColor(0, 0, 0, 120) if muted else QColor(60, 60, 60))
                painter.drawText(delete_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, "×")

                if widget._legend.drag_active and widget._legend.drop_target_idx == int(series_idx):
                    painter.setPen(QPen(QColor(30, 30, 30), 2))
                    painter.drawLine(QPointF(hit_rect.left(), hit_rect.top() - 1), QPointF(hit_rect.right(), hit_rect.top() - 1))

            cur_y = float(content_rect.top())
            max_y = float(content_rect.bottom())
            for mag_title, items in groups:
                if cur_y + LEGEND_ROW_H > max_y:
                    break
                painter.setFont(qfont(8, bold=True))
                painter.setPen(TEXT_DARK)
                painter.drawText(QRectF(content_rect.left(), cur_y, content_rect.width(), LEGEND_ROW_H), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(mag_title))
                group_item_start_y = cur_y + float(LEGEND_ROW_GAP)
                y_cols = [group_item_start_y for _ in range(item_cols)]

                for item_idx, (series_idx, color, label, legend_type) in enumerate(items):
                    col = 0
                    if item_cols > 1 and y_cols[0] + LEGEND_ROW_H > max_y:
                        col = 1
                    elif item_cols > 1 and item_idx >= (len(items) + 1) // 2:
                        col = 1
                    cx = float(content_rect.left() + col * (item_col_w + gap_cols))
                    cy = y_cols[col]
                    if cy + LEGEND_ROW_H > max_y:
                        continue
                    draw_item(series_idx, color, label, legend_type, cx, cy, item_col_w)
                    y_cols[col] += float(LEGEND_ROW_GAP)
                cur_y = max(y_cols) + float(LEGEND_ROW_GAP)
            painter.restore()
            return

        if legend_pos in ("top", "bottom"):
            row_right_pad = 4
            btn_w = 10
            btn_pad = 0
            gap = 8.0
            frame_w = max(1.0, (legend_w - 2 * pad) / float(max(1, len(groups))))

            def item_width(series_idx, label):
                if not (0 <= int(series_idx) < len(widget.series)):
                    return 0.0
                s = widget.series[int(series_idx)]
                row_font = self._legend_row_font(s, bold=bool(s.get("highlighted", False)))
                label_w = QFontMetrics(row_font).horizontalAdvance(label)
                return float(sym + 6 + label_w + btn_w + 8)

            for group_idx, (mag_title, items) in enumerate(groups):
                frame_x = float(x0 + group_idx * frame_w)
                frame_right = float(x0 + (group_idx + 1) * frame_w - row_right_pad)
                y_row = float(y0)
                painter.setFont(qfont(8, bold=True))
                header_w = float(QFontMetrics(qfont(8, bold=True)).horizontalAdvance(str(mag_title)) + 12)
                inline_w = header_w + sum(item_width(series_idx, label) for series_idx, _color, label, _legend_type in items) + gap * len(items)
                inline = inline_w <= max(1.0, frame_w - row_right_pad)

                header_rect = QRectF(frame_x, y_row, max(0.0, frame_right - frame_x), LEGEND_ROW_H)
                painter.setPen(TEXT_DARK)
                painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(mag_title))

                cur_x = frame_x + header_w if inline else frame_x
                if not inline:
                    y_row += float(LEGEND_ROW_GAP)

                for series_idx, color, label, legend_type in items:
                    if not (0 <= int(series_idx) < len(widget.series)):
                        continue
                    s = widget.series[int(series_idx)]
                    item_w = item_width(series_idx, label)
                    if cur_x > frame_x and cur_x + item_w > frame_right:
                        y_row += float(LEGEND_ROW_GAP)
                        cur_x = frame_x

                    muted = bool(s.get("muted", False))
                    highlighted = bool(s.get("highlighted", False))
                    line_visible = bool(s.get("visible", True))
                    markers_visible = bool(s.get("show_markers", False))
                    visible = line_visible or markers_visible
                    icon_y = y_row + (LEGEND_ROW_H - sym) / 2.0
                    self._draw_legend_icon(
                        painter,
                        cur_x,
                        icon_y,
                        sym,
                        legend_type,
                        color,
                        muted=muted,
                        highlighted=highlighted,
                        line_style=s.get("line_style") or "solid",
                        line_width=s.get("line_width") or 2.0,
                        visible=visible,
                    )

                    row_font = self._legend_row_font(s, bold=highlighted)
                    painter.setFont(row_font)
                    if not visible:
                        painter.setPen(QColor(0, 0, 0, 75))
                    else:
                        painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
                    text_left = cur_x + sym + 6
                    max_text_w = max(0.0, (frame_right - btn_w - btn_pad) - text_left)
                    label_w = QFontMetrics(row_font).horizontalAdvance(label)
                    text_draw_w = min(float(label_w), max_text_w)
                    text_rect = QRectF(text_left, y_row, max(0.0, text_draw_w), LEGEND_ROW_H)
                    painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

                    hit_rect = QRectF(cur_x, y_row, max(0.0, item_w), LEGEND_ROW_H)
                    widget._legend_hitboxes.append((hit_rect, int(series_idx)))
                    delete_x = min(frame_right - btn_w, text_left + text_draw_w + 2)
                    delete_rect = QRectF(max(cur_x, delete_x), y_row, btn_w, LEGEND_ROW_H)
                    widget._legend_delete_hitboxes.append((delete_rect, int(series_idx)))
                    painter.setFont(qfont(8, bold=True))
                    painter.setPen(QColor(0, 0, 0, 120) if muted else QColor(60, 60, 60))
                    painter.drawText(delete_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, "×")

                    if widget._legend.drag_active and widget._legend.drop_target_idx == int(series_idx):
                        painter.setPen(QPen(QColor(30, 30, 30), 2))
                        painter.drawLine(QPointF(hit_rect.left(), hit_rect.top() - 1), QPointF(hit_rect.right(), hit_rect.top() - 1))
                    cur_x += item_w + gap
            painter.restore()
            return

        col_w = (legend_w - (cols - 1) * gap_cols) / float(cols) if cols > 0 else legend_w
        col_w = max(40.0, float(col_w))
        row_right_pad = 4
        max_x = x0 + legend_w - row_right_pad
        btn_w = 10
        btn_pad = 0

        rows = []
        for mag_title, items in groups:
            rows.append(("header", mag_title, None))
            for series_idx, color, label, legend_type in items:
                rows.append(("item", (series_idx, color, label, legend_type), None))
            rows.append(("gap", None, None))

        import math

        rows_per_col = int(math.ceil(len(rows) / float(cols))) if cols > 0 else len(rows)
        rows_per_col = max(1, rows_per_col)

        def col_origin(c: int) -> float:
            return float(x0 + c * (col_w + gap_cols))

        base_y = float(y0)
        for i, row in enumerate(rows):
            c = int(i // rows_per_col)
            r = int(i % rows_per_col)
            if c >= cols:
                break
            cx0 = col_origin(c)
            cy0 = base_y + r * float(LEGEND_ROW_GAP)

            row_right = min(float(max_x), float(cx0 + col_w))
            if row[0] == "header":
                painter.setFont(qfont(8, bold=True))
                painter.setPen(TEXT_DARK)
                hdr_rect = QRectF(cx0, cy0, max(0.0, row_right - cx0), LEGEND_ROW_H)
                painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(row[1]))
                continue
            if row[0] == "gap":
                continue

            series_idx, color, label, legend_type = row[1]
            if not (0 <= int(series_idx) < len(widget.series)):
                continue
            s = widget.series[int(series_idx)]
            muted = bool(s.get("muted", False))
            highlighted = bool(s.get("highlighted", False))
            line_visible = bool(s.get("visible", True))
            markers_visible = bool(s.get("show_markers", False))
            visible = line_visible or markers_visible
            line_style = s.get("line_style") or "solid"
            line_width = s.get("line_width") or 2.0

            icon_y = cy0 + (LEGEND_ROW_H - sym) / 2.0
            self._draw_legend_icon(
                painter,
                cx0,
                icon_y,
                sym,
                legend_type,
                color,
                muted=muted,
                highlighted=highlighted,
                line_style=line_style,
                line_width=line_width,
                visible=visible,
            )

            row_font = self._legend_row_font(s, bold=highlighted)
            painter.setFont(row_font)
            if not visible:
                painter.setPen(QColor(0, 0, 0, 75))
            else:
                painter.setPen(QColor(0, 0, 0, 120) if muted else Qt.GlobalColor.black)
            text_left = cx0 + sym + 6
            label_w = QFontMetrics(row_font).horizontalAdvance(label)
            max_text_w = max(0.0, (row_right - btn_w - btn_pad) - text_left)
            text_draw_w = min(float(label_w), max_text_w)
            text_rect = QRectF(text_left, cy0, max(0.0, text_draw_w), LEGEND_ROW_H)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label)

            hit_rect = QRectF(cx0, cy0, max(0.0, col_w), LEGEND_ROW_H)
            widget._legend_hitboxes.append((hit_rect, int(series_idx)))

            delete_x = min(row_right - btn_w, text_left + text_draw_w + 2)
            delete_rect = QRectF(max(cx0, delete_x), cy0, btn_w, LEGEND_ROW_H)
            widget._legend_delete_hitboxes.append((delete_rect, int(series_idx)))
            painter.setFont(qfont(8, bold=True))
            painter.setPen(QColor(0, 0, 0, 120) if muted else QColor(60, 60, 60))
            painter.drawText(delete_rect, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter, "×")

            if widget._legend.drag_active and widget._legend.drop_target_idx == int(series_idx):
                painter.setPen(QPen(QColor(30, 30, 30), 2))
                painter.drawLine(QPointF(hit_rect.left(), hit_rect.top() - 1), QPointF(hit_rect.right(), hit_rect.top() - 1))
        painter.restore()

    def _format_value_full(self, value):
        if value is None:
            return ""
        try:
            v = float(value)
            if v == 0.0:
                return "0"
            av = abs(v)
            if 0 < av < self._TOOLTIP_DECIMAL_LIMIT:
                s = format(v, ".3f")
                if "." in s:
                    s = s.rstrip("0").rstrip(".")
            else:
                s = format(v, ".3e")
            if s in ("-0", "-0.0", "-0.00"):
                s = "0"
            return s
        except Exception:
            return str(value)

    def _collect_hover_tooltip_data(self, widget, hover_index, val_x, plot_rect, x_state, y_state_left, y_state_right=None):
        tooltip_lines = []
        marker_pts = []

        for s in widget.series:
            if not (bool(s.get("visible", True)) or bool(s.get("show_markers", False))):
                continue
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
            label = (s.get("label") or "").strip() or QCoreApplication.translate("TimeSeriesPlotWidget", "Series")
            val_y = ys[hover_index]
            series_y_labels = s.get("y_categorical_labels") or (y_state_left.get("y_categorical_labels") if y_state_left else None)
            if series_y_labels:
                try:
                    val_y_str = series_y_labels[int(round(val_y))]
                except Exception:
                    val_y_str = str(val_y)
            else:
                val_y_str = self._point_value_text(s, val_y)

            unit_suffix = ""
            try:
                magnitude = (s.get("magnitude") or "").strip()
                m = self._UNIT_RE.search(magnitude) if magnitude else None
                if m:
                    unit_suffix = f" {m.group(1).strip()}"
            except Exception:
                unit_suffix = ""

            legend_type = (s.get("legend_type") or "").strip()
            tooltip_lines.append((color, muted, legend_type, f"{label}: ", val_y_str, unit_suffix))
            axis = (s.get("y_axis") or "left")
            y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
            marker_pts.append((color, muted, legend_type, self._to_screen(val_x, val_y, plot_rect, x_state, y_state)))

        return tooltip_lines, marker_pts

    def _draw_tooltip_box(self, widget, painter, footer_segments, tooltip_lines, val_x, hover_val_y, plot_rect, x_state, y_state):
        painter.save()
        font_tt = qfont(8)
        font_tt_bold = QFont(font_tt)
        font_tt_bold.setBold(True)
        painter.setFont(font_tt)
        fm = painter.fontMetrics()
        fm_bold = QFontMetrics(font_tt_bold)

        footer_w = 0
        for text, is_bold in footer_segments:
            footer_w += (fm_bold if is_bold else fm).horizontalAdvance(text)
        series_max_w = 0
        for _c, _m, _legend_type, prefix, value, suffix in tooltip_lines:
            row_w = fm.horizontalAdvance(prefix) + fm_bold.horizontalAdvance(value) + fm.horizontalAdvance(suffix)
            series_max_w = max(series_max_w, row_w)

        bullet_extra = 16 if tooltip_lines else 0
        footer_indent = 14
        max_w = max(footer_w + footer_indent, series_max_w + bullet_extra)

        line_h = fm.height()
        pad = 5
        separator_gap = 3
        content_h = line_h * len(tooltip_lines)
        if tooltip_lines:
            rect_h = pad * 2 + content_h + separator_gap + 1 + separator_gap + line_h
        else:
            rect_h = pad * 2 + line_h
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

        x_text = rect_tt.left() + pad
        y_text = rect_tt.top() + pad

        for color, muted, legend_type, prefix, value, suffix in tooltip_lines:
            icon_size = self._TOOLTIP_ICON_SIZE
            icon_x = x_text + 1
            icon_y = y_text + (line_h - icon_size) / 2
            self._draw_legend_icon(
                painter,
                icon_x,
                icon_y,
                icon_size,
                legend_type,
                color,
                muted=muted,
                highlighted=False,
            )
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

        if tooltip_lines:
            sep_y = y_text + separator_gap
            painter.setPen(QPen(TOOLTIP_SEPARATOR, 1))
            painter.drawLine(QPointF(rect_tt.left() + pad, sep_y), QPointF(rect_tt.right() - pad, sep_y))
            y_text = sep_y + separator_gap

        footer_x = rect_tt.left() + pad + footer_indent
        footer_baseline_y = y_text + fm.ascent()
        painter.setPen(Qt.GlobalColor.black)
        cursor_x = footer_x
        for text, is_bold in footer_segments:
            painter.setFont(font_tt_bold if is_bold else font_tt)
            painter.drawText(QPointF(cursor_x, footer_baseline_y), text)
            cursor_x += (fm_bold if is_bold else fm).horizontalAdvance(text)

        painter.restore()

    def _draw_hover_overlay(self, widget, painter, plot_rect, x_state, y_state_left, y_state_right=None):
        hover_series = None
        hover_index = widget.hover_index
        if widget._hover_series_idx is not None and 0 <= widget._hover_series_idx < len(widget.series):
            hover_series = widget.series[widget._hover_series_idx]
            if not (bool(hover_series.get("visible", True)) or bool(hover_series.get("show_markers", False))):
                hover_series = None
        if hover_series is not None and hover_index is not None:
            xs0 = hover_series.get("x", []) or []
            ys0 = hover_series.get("y", []) or []
            if not xs0 or not ys0 or not (0 <= hover_index < len(xs0)):
                hover_series = None

        if hover_series is None or hover_index is None:
            synced_time = getattr(widget, "_synced_cursor_time_hours", None)
            if synced_time is None:
                return
            try:
                synced_time = float(synced_time)
            except Exception:
                return
            if synced_time < x_state["min_x"] or synced_time > x_state["max_x"]:
                return
            try:
                sync_series_idx = widget._resolveHoverSeriesIndex()
            except Exception:
                sync_series_idx = None
            if sync_series_idx is None or not (0 <= sync_series_idx < len(widget.series)):
                return
            hover_series = widget.series[sync_series_idx]
            xs0 = hover_series.get("x", []) or []
            ys0 = hover_series.get("y", []) or []
            if not xs0 or not ys0:
                return
            try:
                hover_index = widget._nearestDataIndex(xs0, synced_time)
            except Exception:
                return

        xs0 = hover_series.get("x", []) or []
        val_x = xs0[hover_index]

        axis = (hover_series.get("y_axis") or "left")
        y_state = y_state_right if (axis == "right" and y_state_right is not None) else y_state_left
        pt_rule = self._to_screen(val_x, y_state["min_y"], plot_rect, x_state, y_state)
        rule_x = max(float(plot_rect.left()), min(float(plot_rect.right()), float(pt_rule.x())))
        painter.setPen(QPen(QColor(255, 110, 110), 1, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(rule_x, plot_rect.top()), QPointF(rule_x, plot_rect.bottom()))

        cfg_x = getattr(widget, "_axis_cfg_x", None)
        instant_text = self._format_absolute_time_hours_axis(
            val_x,
            hour_format=getattr(cfg_x, "x_hour_format", "hm") if cfg_x else "hm",
            day_format=getattr(cfg_x, "x_day_format", "split_days") if cfg_x else "split_days",
            start_clock_seconds=getattr(widget, "_start_clock_seconds", 0),
            x_precision="hms",
        )
        footer_segments = self._build_styled_footer_segments(instant_text)
        tooltip_lines, marker_pts = self._collect_hover_tooltip_data(widget, hover_index, val_x, plot_rect, x_state, y_state_left, y_state_right)

        painter.save()
        painter.setClipRect(plot_rect)
        for color, muted, legend_type, pt in marker_pts:
            icon_size = self._HOVER_MARKER_ICON_SIZE
            self._draw_legend_icon(
                painter,
                pt.x() - icon_size / 2,
                pt.y() - icon_size / 2,
                icon_size,
                legend_type,
                color,
                muted=muted,
                highlighted=False,
            )
        painter.restore()

        hover_val_y = None
        try:
            hover_val_y = (hover_series.get("y", []) or [])[hover_index]
        except Exception:
            hover_val_y = None

        self._draw_tooltip_box(widget, painter, footer_segments, tooltip_lines, val_x, hover_val_y, plot_rect, x_state, y_state)

