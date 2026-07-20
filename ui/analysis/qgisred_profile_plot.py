# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, QSize, pyqtSignal
from qgis.PyQt.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics, QPolygonF
from qgis.PyQt.QtWidgets import QWidget, QSizePolicy

from ...tools.utils.qgisred_axis_scale_utils import compute_nice_scale, format_number_tick
from ...tools.utils.qgisred_profile_plot_utils import (
    profile_line_segments,
    cursor_snapshot,
    nearest_visible_point,
    format_profile_value,
    profile_data_area,
    resolve_envelope_mode,
    truncate_id,
    profile_x_range,
    MAIN_PATH_KEY,
    nearest_path_key,
    path_key_for_node_id,
    series_for_path,
    series_path_key,
    series_path_keys,
)
from .profile_chart_settings import ProfileAxisSettings, ProfileGeneralSettings

_LINE_STYLES = {
    "solid": Qt.PenStyle.SolidLine,
    "dashed": Qt.PenStyle.DashLine,
    "dotted": Qt.PenStyle.DotLine,
}


PALETTE = [
    QColor(31, 119, 180),
    QColor(214, 39, 40),
    QColor(44, 160, 44),
    QColor(255, 127, 14),
    QColor(148, 103, 189),
    QColor(140, 86, 75),
]

ENVELOPE_FILL = QColor(230, 159, 0)
ENVELOPE_LINE = QColor(184, 111, 0)

_ELEMENT_SVG_FILES = {
    "pump": "pumps.svg",
    "valve": "valves.svg",
    "tank": "tanks.svg",
    "reservoir": "reservoirs.svg",
}

_ELEMENT_SVG_COLORS = {
    "pump": (QColor(60, 70, 90), QColor(255, 255, 255)),
    "valve": (QColor(60, 70, 90), QColor(255, 255, 255)),
    "tank": (QColor(120, 179, 220), QColor(40, 48, 60)),
    "reservoir": (QColor(120, 179, 220), QColor(40, 48, 60)),
}


class ProfilePlotWidget(QWidget):
    cursorNodeChanged = pyqtSignal(int)
    cursorNodeIdChanged = pyqtSignal(str)
    curveDeleteRequested = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ProfilePlotWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(160)
        self.setMouseTracking(True)
        self._series = []
        self._title = ""
        self._x_label = ""
        self._y_label = ""
        self._y_right_label = ""
        self._empty_text = ""
        self._hover_x = None
        self._hover_y = None
        self._hover_node_index = -1
        self._hover_node_id = ""
        self._cursor_node_index = None
        self._cursor_data_x = None
        self._cursor_path_key = None
        self._show_value_labels = False
        self._symbols = None
        self._envelope = None
        self._view_x = None
        self._pan_mode = False
        self._zoom_window_mode = False
        self._last_plot = None
        self._last_area = None
        self._last_view = None
        self._last_px = None
        self._last_py_of = None
        self._drag_start = None
        self._drag_start_view = None
        self._zoom_rect = None
        self._axis_cfg_x = ProfileAxisSettings()
        self._axis_cfg_y = ProfileAxisSettings()
        self._axis_cfg_y_right = ProfileAxisSettings()
        self._general_cfg = ProfileGeneralSettings()
        self._curve_overrides = {}

    def sizeHint(self):
        return QSize(640, 320)

    def setEmptyText(self, text):
        self._empty_text = text
        self.update()

    def setShowValueLabels(self, show):
        self._show_value_labels = bool(show)
        self.update()

    def setSymbols(self, node_kinds, link_info):
        self._symbols = {"nodes": node_kinds or [], "links": link_info or []}
        self.update()

    def clearSymbols(self):
        self._symbols = None
        self.update()

    def setEnvelope(self, max_points, min_points, mode="both", labels=None):
        if not max_points or not min_points or mode == "off":
            self._envelope = None
        else:
            labels = labels or {}
            self._envelope = {
                "max": [(float(d), None if v is None else float(v)) for d, v in max_points],
                "min": [(float(d), None if v is None else float(v)) for d, v in min_points],
                "mode": mode,
                "max_label": labels.get("max", "Maxima"),
                "min_label": labels.get("min", "Minima"),
                "band_label": labels.get("band", "Envelope"),
            }
        self.update()

    def clearEnvelope(self):
        self._envelope = None
        self.update()

    def setCursorNode(self, index):
        new_index = index if (index is not None and index >= 0) else None
        if new_index != self._cursor_node_index or self._cursor_data_x is not None:
            self._cursor_node_index = new_index
            self._cursor_data_x = None
            self._cursor_path_key = MAIN_PATH_KEY if new_index is not None else None
            self.update()

    def setCursorDistance(self, distance, node_id=None):
        path_key = path_key_for_node_id(self._series, node_id)
        if (distance != self._cursor_data_x or self._cursor_node_index is not None
                or path_key != self._cursor_path_key):
            self._cursor_data_x = distance
            self._cursor_node_index = None
            self._cursor_path_key = path_key
            self.update()

    def setLabels(self, title, x_label, y_label, y_right_label=""):
        self._title = title or ""
        self._x_label = x_label or ""
        self._y_label = y_label or ""
        self._y_right_label = y_right_label or ""
        self.update()

    def setSeries(self, series):
        normalized = []
        for i, s in enumerate(series):
            points = [
                (float(d), None if v is None else float(v))
                for d, v in s.get("points", [])
            ]
            base_color = s.get("color") or PALETTE[i % len(PALETTE)]
            base_width = float(s.get("width", 2.0))
            entry = {
                "label": s.get("label", ""),
                "display_label": s.get("display_label") or s.get("label", ""),
                "readout_label": s.get("readout_label") or "",
                "path_key": series_path_key(s),
                "path_label": s.get("path_label") or "",
                "color": base_color,
                "base_color": base_color,
                "base_width": base_width,
                "points": points,
                "reference": set(s.get("reference_indices", set())),
                "node_ids": list(s.get("node_ids", [])),
                "y_axis": "right" if s.get("y_axis") == "right" else "left",
                "fill": bool(s.get("fill", True)),
                "deletable": bool(s.get("deletable", False)),
                "width": base_width,
                "line_style": "solid",
                "show_markers": True,
                "marker_size": 2.5,
            }
            self._applyCurveOverride(entry)
            normalized.append(entry)
        self._series = normalized
        self.update()

    def _applyCurveOverride(self, entry):
        override = self._curve_overrides.get(entry["label"])
        if override is None:
            return
        if override.color_hex:
            color = QColor(override.color_hex)
            if color.isValid():
                entry["color"] = color
        entry["width"] = float(override.width)
        entry["line_style"] = override.line_style
        entry["show_markers"] = bool(override.show_markers)
        entry["marker_size"] = float(override.marker_size)

    def applyChartSettings(self):
        for entry in self._series:
            entry["color"] = entry.get("base_color", entry["color"])
            entry["width"] = entry.get("base_width", 2.0)
            entry["line_style"] = "solid"
            entry["show_markers"] = True
            entry["marker_size"] = 2.5
            self._applyCurveOverride(entry)
        self.update()

    def clear(self):
        self._series = []
        self._hover_x = None
        self._hover_y = None
        self._hover_node_index = -1
        self._cursor_node_index = None
        self._cursor_data_x = None
        self._cursor_path_key = None
        self._symbols = None
        self._envelope = None
        self._view_x = None
        self._zoom_rect = None
        self.update()

    def _dataBounds(self):
        xs = []
        ys = []
        for s in self._series:
            for d, v in s["points"]:
                if v is None:
                    continue
                xs.append(d)
                ys.append(v)
        if self._envelope is not None:
            for boundary in ("max", "min"):
                for d, v in self._envelope[boundary]:
                    if v is None:
                        continue
                    xs.append(d)
                    ys.append(v)
        if not xs:
            return None
        return min(xs), max(xs), min(ys), max(ys)

    def _currentView(self):
        bounds = self._dataBounds()
        if bounds is None:
            return None
        if self._view_x is not None:
            x0, x1 = self._view_x
        elif not self._axis_cfg_x.auto_scale:
            x0, x1 = self._axis_cfg_x.fixed_min, self._axis_cfg_x.fixed_max
        else:
            x0, x1 = profile_x_range(bounds[0], bounds[1])
        if x1 == x0:
            x1 = x0 + 1.0
        y0, y1 = self._autoYForAxis(x0, x1, "left")
        return (x0, x1, y0, y1)

    def _hasRightAxis(self):
        return any(s.get("y_axis", "left") == "right" for s in self._series)

    def _fullXRange(self):
        bounds = self._dataBounds()
        if bounds is None:
            return None
        return profile_x_range(bounds[0], bounds[1])

    def _autoYForAxis(self, x0, x1, which):
        cfg = self._axis_cfg_y_right if which == "right" else self._axis_cfg_y
        if not cfg.auto_scale:
            y0, y1 = cfg.fixed_min, cfg.fixed_max
            if y1 == y0:
                y1 = y0 + 1.0
            return y0, y1
        values = []
        for s in self._series:
            if s.get("y_axis", "left") != which:
                continue
            for d, v in s["points"]:
                if v is not None and x0 - 1e-9 <= d <= x1 + 1e-9:
                    values.append(v)
        if which == "left" and self._envelope is not None:
            for boundary in ("max", "min"):
                for d, v in self._envelope[boundary]:
                    if v is not None and x0 - 1e-9 <= d <= x1 + 1e-9:
                        values.append(v)
        if not values:
            for s in self._series:
                if s.get("y_axis", "left") == which:
                    values.extend(v for _d, v in s["points"] if v is not None)
        if values:
            ymin, ymax = min(values), max(values)
        else:
            bounds = self._dataBounds()
            if bounds is None:
                return (0.0, 1.0)
            ymin, ymax = bounds[2], bounds[3]
        ys = compute_nice_scale(ymin, ymax, 6)
        y0, y1 = ys.axis_min, ys.axis_max
        if y1 == y0:
            y1 = y0 + 1.0
        return y0, y1

    def _clampX(self, x0, x1):
        full = self._fullXRange()
        if full is None:
            return None
        lo, hi = full
        view_range = x1 - x0
        if view_range <= 0 or view_range >= hi - lo:
            return None
        if x0 < lo:
            x0, x1 = lo, lo + view_range
        if x1 > hi:
            x0, x1 = hi - view_range, hi
        return (max(lo, x0), min(hi, x1))

    def setPanMode(self, on):
        self._pan_mode = bool(on)
        if on:
            self._zoom_window_mode = False
        self._updateNavCursor()

    def setZoomWindowMode(self, on):
        self._zoom_window_mode = bool(on)
        if on:
            self._pan_mode = False
        self._zoom_rect = None
        self._updateNavCursor()

    def _updateNavCursor(self):
        if self._pan_mode:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif self._zoom_window_mode:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.unsetCursor()

    def fitView(self):
        self._view_x = None
        self.update()

    def zoomIn(self):
        self._zoomAroundCenter(1.0 / 1.5)

    def zoomOut(self):
        self._zoomAroundCenter(1.5)

    def _zoomAroundCenter(self, factor):
        view = self._currentView()
        if view is None:
            return
        x0, x1 = view[0], view[1]
        center = (x0 + x1) / 2.0
        half = (x1 - x0) / 2.0 * factor
        self._view_x = self._clampX(center - half, center + half)
        self.update()

    def _pixelToData(self, pixel_x, pixel_y):
        area = self._last_area
        if area is None or self._last_view is None:
            return None
        if area.width() <= 0 or area.height() <= 0:
            return None
        x0, x1, y0, y1 = self._last_view
        data_x = x0 + (pixel_x - area.left()) / area.width() * (x1 - x0)
        data_y = y0 + (area.bottom() - pixel_y) / area.height() * (y1 - y0)
        return data_x, data_y

    def _dataXAt(self, pixel_x):
        area = self._last_area
        plot = self._last_plot
        if pixel_x is None or area is None or plot is None or self._last_view is None:
            return None
        if area.width() <= 0 or not (plot.left() <= pixel_x <= plot.right()):
            return None
        x0, x1 = self._last_view[0], self._last_view[1]
        return x0 + (pixel_x - area.left()) / area.width() * (x1 - x0)

    def _drawZoomRect(self, painter, plot):
        if self._zoom_rect is None:
            return
        p1, p2 = self._zoom_rect
        left = min(p1.x(), p2.x())
        right = max(p1.x(), p2.x())
        rect = QRectF(left, plot.top(), right - left, plot.height()).intersected(plot)
        painter.setPen(QPen(QColor(60, 120, 200), 1.0, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(60, 120, 200, 40)))
        painter.drawRect(rect)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        full = QRectF(self.rect())
        painter.fillRect(full, QColor(255, 255, 255))

        has_right = self._hasRightAxis()
        left, right, top, bottom = 64.0, (58.0 if has_right else 18.0), 54.0, 48.0
        plot = QRectF(left, top, max(1.0, full.width() - left - right), max(1.0, full.height() - top - bottom))

        self._legend_delete_hitboxes = []
        view = self._currentView()
        if view is None:
            painter.setPen(QColor(130, 130, 130))
            painter.drawText(full, Qt.AlignmentFlag.AlignCenter, self._empty_text)
            painter.end()
            return

        x0, x1, y0, y1 = view
        area = self._dataArea(plot)
        self._last_plot = plot
        self._last_area = area
        self._last_view = view
        x_scale = compute_nice_scale(x0, x1, 8)
        y_scale = compute_nice_scale(y0, y1, 6)

        yr0 = yr1 = None
        yr_scale = None
        if has_right:
            yr0, yr1 = self._autoYForAxis(x0, x1, "right")
            yr_scale = compute_nice_scale(yr0, yr1, 6)

        def px(d):
            return area.left() + (d - x0) / (x1 - x0) * area.width()

        def py(v):
            return area.bottom() - (v - y0) / (y1 - y0) * area.height()

        def py_r(v):
            return area.bottom() - (v - yr0) / (yr1 - yr0) * area.height()

        def py_of(s):
            return py_r if (has_right and s.get("y_axis", "left") == "right") else py

        self._last_px = px
        self._last_py_of = py_of

        painter.fillRect(plot, self._plotBgColor())

        grid_pen = QPen(QColor(223, 233, 244))
        grid_pen.setWidthF(1.0)
        tick_pen = QPen(QColor(120, 130, 145))
        painter.setFont(QFont("Arial", 8))

        for t in y_scale.ticks():
            if t < y0 - 1e-9 or t > y1 + 1e-9:
                continue
            y = py(t)
            if self._axis_cfg_y.show_grid:
                painter.setPen(grid_pen)
                painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(tick_pen)
            painter.drawText(QRectF(0, y - 8, left - 6, 16),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             format_number_tick(t, y_scale.step))

        if has_right and yr_scale is not None:
            for t in yr_scale.ticks():
                if t < yr0 - 1e-9 or t > yr1 + 1e-9:
                    continue
                y = py_r(t)
                painter.setPen(tick_pen)
                painter.drawText(QRectF(plot.right() + 6, y - 8, right - 8, 16),
                                 Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                                 format_number_tick(t, yr_scale.step))

        for t in x_scale.ticks():
            if t < x0 - 1e-9 or t > x1 + 1e-9:
                continue
            x = px(t)
            if self._axis_cfg_x.show_grid:
                painter.setPen(grid_pen)
                painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.setPen(tick_pen)
            painter.drawText(QRectF(x - 40, plot.bottom() + 4, 80, 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                             format_number_tick(t, x_scale.step))

        painter.setPen(QPen(QColor(150, 160, 175), 1.2))
        painter.drawRect(plot)

        painter.save()
        painter.setClipRect(plot)
        if self._envelope is not None:
            self._drawEnvelope(painter, px, py)
        for s in self._series:
            self._drawSeries(painter, s, px, py_of(s), plot.bottom())
        self._drawNodeVerticalLines(painter, plot, px, py_of)
        if self._symbols is not None and self._series:
            self._drawSymbols(painter, self._series[0], px, py_of(self._series[0]))
        if self._show_value_labels and self._series:
            for s in self._series:
                self._drawValueLabels(painter, s, px, py_of(s), plot)
        self._drawCursor(painter, plot, px, py_of)
        painter.restore()

        self._drawTitleAndAxisLabels(painter, full, plot)
        if self._general_cfg.show_legend:
            self._drawLegend(painter, plot)
        self._drawZoomRect(painter, plot)
        painter.end()

    def _dataArea(self, plot):
        left, top, right, bottom = profile_data_area(plot.left(), plot.top(), plot.right(), plot.bottom())
        return QRectF(left, top, right - left, bottom - top)

    def _plotBgColor(self):
        color = QColor(self._general_cfg.plot_bg_hex)
        return color if color.isValid() else QColor(250, 252, 255)

    def _drawEnvelope(self, painter, px, py):
        show_band, show_lines = resolve_envelope_mode(self._envelope.get("mode", "both"))
        max_points = self._envelope["max"]
        min_points = self._envelope["min"]

        if show_band:
            band = QColor(ENVELOPE_FILL)
            band.setAlpha(55)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(band))
            run = []
            for i in range(min(len(max_points), len(min_points))):
                d, vmax = max_points[i]
                _d, vmin = min_points[i]
                if vmax is None or vmin is None:
                    self._fillBand(painter, run, px, py)
                    run = []
                else:
                    run.append((d, vmax, vmin))
            self._fillBand(painter, run, px, py)

        if show_lines:
            painter.setPen(QPen(ENVELOPE_LINE, 1.2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for points in (max_points, min_points):
                for segment in profile_line_segments(points):
                    painter.drawPolyline(QPolygonF([QPointF(px(d), py(v)) for d, v in segment]))

    def _fillBand(self, painter, run, px, py):
        if len(run) < 2:
            return
        top = [QPointF(px(d), py(vmax)) for d, vmax, _vmin in run]
        bottom = [QPointF(px(d), py(vmin)) for d, _vmax, vmin in reversed(run)]
        painter.drawPolygon(QPolygonF(top + bottom))

    def _drawNodeVerticalLines(self, painter, plot, px, py_of):
        if not self._series:
            return
        tops = {}
        for s in self._series:
            py = py_of(s)
            for pd, pv in s["points"]:
                if pv is None:
                    continue
                y = py(pv)
                key = round(pd, 6)
                if key not in tops or y < tops[key]:
                    tops[key] = y
        base = self._series[0]
        reference = base.get("reference", set())
        thin = QPen(QColor(178, 168, 192), 0.6)
        thick = QPen(QColor(126, 110, 150), 1.2)
        for idx, (d, _v) in enumerate(base["points"]):
            top_y = tops.get(round(d, 6))
            if top_y is None:
                continue
            x = px(d)
            painter.setPen(thick if idx in reference else thin)
            painter.drawLine(QPointF(x, plot.bottom()), QPointF(x, top_y))

    def _drawSeries(self, painter, s, px, py, baseline_y):
        color = s["color"]
        points = s["points"]
        segments = profile_line_segments(points)

        if s.get("fill", True):
            fill = QColor(color)
            fill.setAlpha(45)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(fill))
            for segment in segments:
                top = [QPointF(px(d), py(v)) for d, v in segment]
                polygon = QPolygonF(top + [QPointF(top[-1].x(), baseline_y), QPointF(top[0].x(), baseline_y)])
                painter.drawPolygon(polygon)

        pen = QPen(color)
        pen.setWidthF(s["width"])
        pen.setStyle(_LINE_STYLES.get(s.get("line_style", "solid"), Qt.PenStyle.SolidLine))
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for segment in segments:
            painter.drawPolyline(QPolygonF([QPointF(px(d), py(v)) for d, v in segment]))

        if not s.get("show_markers", True):
            return
        marker_size = s.get("marker_size", 2.5)
        reference = s["reference"]
        painter.setBrush(QBrush(color))
        for idx, (d, v) in enumerate(points):
            if v is None:
                continue
            cx, cy = px(d), py(v)
            if idx in reference:
                painter.setPen(QPen(QColor(255, 255, 255), 1.0))
                m = marker_size + 3.5
                painter.drawPolygon(QPolygonF([
                    QPointF(cx, cy - m), QPointF(cx + m, cy),
                    QPointF(cx, cy + m), QPointF(cx - m, cy),
                ]))
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                r = max(1.8, marker_size)
                painter.drawEllipse(QPointF(cx, cy), r, r)

    def _drawSymbols(self, painter, s, px, py):
        points = s["points"]
        node_kinds = self._symbols.get("nodes", [])
        link_info = self._symbols.get("links", [])

        for i, info in enumerate(link_info):
            if i + 1 >= len(points):
                break
            d0, v0 = points[i]
            d1, v1 = points[i + 1]
            if v0 is None or v1 is None:
                continue
            x0, y0 = px(d0), py(v0)
            x1, y1 = px(d1), py(v1)
            self._drawFlowArrow(painter, x0, y0, x1, y1, info.get("direction", 0))
            kind = info.get("kind", "pipe")
            if kind in ("pump", "valve"):
                mx = (x0 + x1) / 2.0
                my = (y0 + y1) / 2.0 - 12.0
                if not self._drawElementIcon(painter, mx, my, kind, 18.0):
                    if kind == "pump":
                        self._drawPumpGlyph(painter, mx, my)
                    else:
                        self._drawValveGlyph(painter, mx, my)

        for idx, (d, v) in enumerate(points):
            if v is None:
                continue
            kind = node_kinds[idx] if idx < len(node_kinds) else "junction"
            self._drawNodeGlyph(painter, px(d), py(v), kind)

    def _elementSvgImage(self, kind, size):
        if not hasattr(self, "_svg_images"):
            self._svg_images = {}
        cache_key = (kind, int(size))
        if cache_key in self._svg_images:
            return self._svg_images[cache_key]
        image = None
        filename = _ELEMENT_SVG_FILES.get(kind)
        if filename:
            try:
                import os
                from qgis.core import QgsApplication

                fill, stroke = _ELEMENT_SVG_COLORS.get(kind, (QColor(60, 70, 90), QColor(255, 255, 255)))
                path = os.path.join(os.path.dirname(__file__), "..", "..",
                                    "defaults", "layerStyles", "icons", filename)
                result = QgsApplication.svgCache().svgAsImage(
                    path, float(size), fill, stroke, 0.4, 1.0)
                img = result[0] if isinstance(result, tuple) else result
                if img is not None and not img.isNull():
                    image = img
            except Exception:
                image = None
        self._svg_images[cache_key] = image
        return image

    def _drawElementIcon(self, painter, x, y, kind, size):
        image = self._elementSvgImage(kind, size)
        if image is None:
            return False
        half = size / 2.0
        painter.drawImage(QRectF(x - half, y - half, size, size), image)
        return True

    def _drawNodeGlyph(self, painter, x, y, kind):
        if kind in ("reservoir", "tank") and self._drawElementIcon(painter, x, y, kind, 18.0):
            return
        outline = QPen(QColor(40, 48, 60), 1.2)
        if kind == "reservoir":
            painter.setPen(outline)
            painter.setBrush(QBrush(QColor(120, 179, 220)))
            painter.drawPolygon(QPolygonF([
                QPointF(x - 7, y - 6), QPointF(x + 7, y - 6),
                QPointF(x + 4, y + 6), QPointF(x - 4, y + 6),
            ]))
        elif kind == "tank":
            painter.setPen(outline)
            painter.setBrush(QBrush(QColor(120, 179, 220)))
            painter.drawRect(QRectF(x - 6, y - 6, 12, 12))
            painter.drawLine(QPointF(x - 6, y - 2), QPointF(x + 6, y - 2))
        else:
            painter.setPen(QPen(QColor(255, 255, 255), 1.0))
            painter.setBrush(QBrush(QColor(60, 70, 90)))
            painter.drawPolygon(QPolygonF([
                QPointF(x, y - 5), QPointF(x + 5, y), QPointF(x, y + 5), QPointF(x - 5, y)
            ]))

    def _drawPumpGlyph(self, painter, x, y):
        r = 7.0
        painter.setPen(QPen(QColor(40, 48, 60), 1.3))
        painter.setBrush(QBrush(QColor(46, 160, 44)))
        painter.drawEllipse(QPointF(x, y), r, r)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawPolygon(QPolygonF([
            QPointF(x - 3.0, y - 3.5), QPointF(x - 3.0, y + 3.5), QPointF(x + 4.0, y),
        ]))

    def _drawValveGlyph(self, painter, x, y):
        painter.setPen(QPen(QColor(40, 48, 60), 1.2))
        painter.setBrush(QBrush(QColor(214, 90, 40)))
        painter.drawPolygon(QPolygonF([
            QPointF(x - 7, y - 6), QPointF(x - 7, y + 6), QPointF(x, y),
        ]))
        painter.drawPolygon(QPolygonF([
            QPointF(x + 7, y - 6), QPointF(x + 7, y + 6), QPointF(x, y),
        ]))

    def _drawFlowArrow(self, painter, x0, y0, x1, y1, direction):
        if direction == 0:
            return
        dx = x1 - x0
        dy = y1 - y0
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1e-6:
            return
        ux = dx / length
        uy = dy / length
        if direction < 0:
            ux = -ux
            uy = -uy
        mx = (x0 + x1) / 2.0
        my = (y0 + y1) / 2.0
        perp_x = -uy
        perp_y = ux
        tip = QPointF(mx + ux * 5.0, my + uy * 5.0)
        base1 = QPointF(mx - ux * 3.0 + perp_x * 3.0, my - uy * 3.0 + perp_y * 3.0)
        base2 = QPointF(mx - ux * 3.0 - perp_x * 3.0, my - uy * 3.0 - perp_y * 3.0)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawPolygon(QPolygonF([tip, base1, base2]))

    def _drawValueLabels(self, painter, s, px, py, plot):
        painter.setFont(QFont("Arial", 8))
        fm = QFontMetrics(painter.font())
        text_color = s.get("color") if isinstance(s.get("color"), QColor) else QColor(40, 40, 40)
        for idx, (d, v) in enumerate(s["points"]):
            if v is None or idx not in s["reference"]:
                continue
            text = format_profile_value(v)
            width = fm.horizontalAdvance(text) + 8
            x_left = max(plot.left(), min(px(d) - width / 2.0, plot.right() - width))
            y_top = py(v) - 22
            if y_top < plot.top():
                y_top = py(v) + 8
            rect = QRectF(x_left, y_top, width, 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 225)))
            painter.drawRoundedRect(rect, 3, 3)
            painter.setPen(text_color)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _drawTitleAndAxisLabels(self, painter, full, plot):
        painter.setPen(QColor(30, 30, 30))
        if self._title:
            tfont = QFont("Arial", 9)
            tfont.setBold(True)
            painter.setFont(tfont)
            painter.drawText(QRectF(plot.left(), 4, plot.width(), 16),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._title)
        painter.setFont(QFont("Arial", 8))
        x_title = self._axis_cfg_x.title or self._x_label
        y_title = self._axis_cfg_y.title or self._y_label
        if x_title:
            painter.drawText(QRectF(plot.left(), full.height() - 16, plot.width(), 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, x_title)
        if y_title:
            painter.save()
            painter.translate(14, plot.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-plot.height() / 2, -10, plot.height(), 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, y_title)
            painter.restore()
        y_right_title = self._axis_cfg_y_right.title or self._y_right_label
        if y_right_title and self._hasRightAxis():
            painter.save()
            painter.translate(full.width() - 12, plot.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-plot.height() / 2, -10, plot.height(), 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, y_right_title)
            painter.restore()

    def _legendEntries(self):
        entries = []
        seen_labels = set()
        for s in self._series:
            label = s["label"] or ""
            if label in seen_labels:
                continue
            seen_labels.add(label)
            entries.append({"label": s.get("display_label") or label, "curve_key": label, "kind": "line",
                            "color": s["color"], "width": s["width"], "dashed": False,
                            "deletable": s.get("deletable", False)})
        if self._envelope is not None:
            show_band, show_lines = resolve_envelope_mode(self._envelope.get("mode", "both"))
            if show_lines:
                entries.append({"label": self._envelope["max_label"], "kind": "line",
                                "color": QColor(ENVELOPE_LINE), "width": 1.2, "dashed": True})
                entries.append({"label": self._envelope["min_label"], "kind": "line",
                                "color": QColor(ENVELOPE_LINE), "width": 1.2, "dashed": True})
            elif show_band:
                fill = QColor(ENVELOPE_FILL)
                fill.setAlpha(120)
                entries.append({"label": self._envelope["band_label"], "kind": "band", "color": fill})
        return entries

    def _drawLegend(self, painter, plot):
        entries = self._legendEntries()
        self._legend_delete_hitboxes = []
        if not entries:
            return
        cfg = self._general_cfg
        box = max(6, int(cfg.legend_symbol_size))
        gap = 14
        del_w = 16
        painter.setFont(QFont("Arial", max(6, int(cfg.legend_font_size))))
        fm = QFontMetrics(painter.font())
        widths = [box + 4 + fm.horizontalAdvance(e["label"]) + (del_w if e.get("deletable") else 0)
                  for e in entries]
        total = sum(widths) + gap * max(0, len(entries) - 1)
        if cfg.legend_position == "left":
            x = plot.left() + 4
        elif cfg.legend_position == "right":
            x = plot.right() - total - 4
        else:
            x = plot.left() + max(0.0, (plot.width() - total) / 2.0)
        gap_below = 10.0
        row_h = fm.height() + 6.0
        frame_bottom = plot.top() - gap_below
        frame_top = frame_bottom - row_h
        cy = (frame_top + frame_bottom) / 2.0

        bg_hex = (cfg.legend_bg_hex or "").strip()
        if cfg.legend_show_frame or bg_hex:
            rect = QRectF(x - 6, frame_top, total + 12, row_h)
            painter.setBrush(QBrush(QColor(bg_hex)) if bg_hex else Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(150, 160, 175), 1.0) if cfg.legend_show_frame else Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 3, 3)

        baseline = cy + (fm.ascent() - fm.descent()) / 2.0
        for i, e in enumerate(entries):
            if e["kind"] == "band":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(e["color"]))
                painter.drawRect(QRectF(x, cy - 4, box, 8))
            else:
                style = Qt.PenStyle.DashLine if e.get("dashed") else Qt.PenStyle.SolidLine
                painter.setPen(QPen(e["color"], e["width"], style))
                painter.drawLine(QPointF(x, cy), QPointF(x + box, cy))
            painter.setPen(QColor(40, 40, 40))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawText(QPointF(x + box + 4, baseline), e["label"])
            if e.get("deletable"):
                cxd = x + box + 4 + fm.horizontalAdvance(e["label"]) + 7
                painter.setPen(QPen(QColor(20, 20, 20), 1.1))
                painter.drawLine(QPointF(cxd - 2.3, cy - 2.3), QPointF(cxd + 2.3, cy + 2.3))
                painter.drawLine(QPointF(cxd - 2.3, cy + 2.3), QPointF(cxd + 2.3, cy - 2.3))
                self._legend_delete_hitboxes.append(
                    (QRectF(cxd - 6, cy - 6, 12, 12), e.get("curve_key") or e["label"]))
            x += widths[i] + gap

    def _nearestPathKeyAt(self, x, y):
        if x is None or y is None or self._last_px is None or self._last_py_of is None:
            return None
        if len(series_path_keys(self._series)) < 2:
            return None
        entries = []
        for s in self._series:
            py = self._last_py_of(s)
            entries.append({
                "path_key": series_path_key(s),
                "pixels": [None if v is None else (self._last_px(d), py(v)) for d, v in s["points"]],
            })
        return nearest_path_key(entries, x, y)

    def _activePathKey(self):
        if self._hover_x is not None and self._dataXAt(self._hover_x) is not None:
            return self._nearestPathKeyAt(self._hover_x, self._hover_y)
        return self._cursor_path_key

    def _cursorSnapshot(self):
        if not self._series:
            return None
        data_x = self._dataXAt(self._hover_x)
        if data_x is None and self._cursor_data_x is not None:
            data_x = self._cursor_data_x
        elif data_x is None and self._cursor_node_index is not None:
            base = self._series[0]["points"]
            if 0 <= self._cursor_node_index < len(base):
                data_x = base[self._cursor_node_index][0]
        if data_x is None:
            return None
        active = series_for_path(self._series, self._activePathKey())
        snapshot = cursor_snapshot(active, data_x)
        if snapshot is None:
            return None
        return snapshot, active

    def _drawCursor(self, painter, plot, px, py_of):
        result = self._cursorSnapshot()
        if result is None:
            return
        snapshot, active = result

        snap_x = snapshot["distance"]
        line_x = px(snap_x)
        painter.setPen(QPen(QColor(120, 120, 120), 1.0, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(line_x, plot.top()), QPointF(line_x, plot.bottom()))

        for s in active:
            candidate = nearest_visible_point(s["points"], snap_x)
            if candidate is None:
                continue
            _si, d, v = candidate
            painter.setPen(QPen(QColor(255, 255, 255), 1.5))
            painter.setBrush(QBrush(s["color"]))
            painter.drawEllipse(QPointF(px(d), py_of(s)(v)), 4.5, 4.5)

        self._drawReadout(painter, plot, line_x, snapshot)

    def _readoutTitle(self, snapshot):
        if len(series_path_keys(self._series)) < 2:
            return ""
        return snapshot.get("path_label") or ""

    def _drawReadout(self, painter, plot, line_x, snapshot):
        painter.setFont(QFont("Arial", 8))
        fm = QFontMetrics(painter.font())
        title = self._readoutTitle(snapshot)
        title_font = QFont("Arial", 8)
        title_font.setBold(True)
        title_h = QFontMetrics(title_font).height() + 4 if title else 0
        rows = []
        node_id = snapshot.get("node_id")
        if node_id:
            rows.append((None, "ID: {}".format(truncate_id(node_id))))
        rows.append((None, "{}: {}".format(self._x_label or "Distance",
                                           format_profile_value(snapshot["distance"]))))
        for entry in snapshot["entries"]:
            rows.append((entry["color"], "{}: {}".format(entry["label"], format_profile_value(entry["value"]))))

        text_width = max(fm.horizontalAdvance(text) for _color, text in rows)
        if title:
            text_width = max(text_width, QFontMetrics(title_font).horizontalAdvance(title))
        width = text_width + 26
        height = len(rows) * 15 + 8 + title_h

        bx = line_x + 12
        if bx + width > plot.right():
            bx = line_x - 12 - width
        bx = max(plot.left() + 2, min(bx, plot.right() - width - 2))
        by = plot.top() + 6

        painter.setPen(QPen(QColor(180, 190, 200)))
        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.drawRoundedRect(QRectF(bx, by, width, height), 4, 4)

        ty = by + 6
        if title:
            painter.setFont(title_font)
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(QRectF(bx + 6, ty, width - 12, title_h),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, title)
            painter.setFont(QFont("Arial", 8))
            ty += title_h
        for color, text in rows:
            if color is not None:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawRect(QRectF(bx + 6, ty + 3, 9, 9))
                text_x = bx + 20
            else:
                text_x = bx + 6
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(QPointF(text_x, ty + 11), text)
            ty += 15

    @staticmethod
    def _eventPos(event):
        if hasattr(event, "position"):
            pos = event.position()
            return pos.x(), pos.y()
        return event.x(), event.y()

    def mousePressEvent(self, event):
        x, y = self._eventPos(event)
        if event.button() == Qt.MouseButton.LeftButton:
            for rect, label in getattr(self, "_legend_delete_hitboxes", []) or []:
                if rect.contains(QPointF(x, y)):
                    self.curveDeleteRequested.emit(label)
                    return
        if event.button() == Qt.MouseButton.LeftButton and self._zoom_window_mode:
            self._zoom_rect = (QPointF(x, y), QPointF(x, y))
        elif event.button() == Qt.MouseButton.LeftButton and self._pan_mode:
            self._drag_start = (x, y)
            self._drag_start_view = self._currentView()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super(ProfilePlotWidget, self).mousePressEvent(event)

    def _emitCursorNode(self):
        index = -1
        node_id = ""
        if self._series and self._dataXAt(self._hover_x) is not None:
            result = self._cursorSnapshot()
            if result is not None:
                snapshot = result[0]
                if snapshot.get("path_key") == MAIN_PATH_KEY:
                    index = snapshot["index"]
                node_id = snapshot.get("node_id") or ""
        if index != self._hover_node_index:
            self._hover_node_index = index
            if index >= 0:
                self.cursorNodeChanged.emit(index)
        if node_id != self._hover_node_id:
            self._hover_node_id = node_id
            self.cursorNodeIdChanged.emit(node_id)

    def mouseMoveEvent(self, event):
        x, y = self._eventPos(event)
        if self._zoom_rect is not None:
            self._zoom_rect = (self._zoom_rect[0], QPointF(x, y))
            self._hover_x = None
            self._hover_y = None
            self.update()
        elif self._drag_start is not None and self._drag_start_view is not None:
            self._panTo(x, y)
        elif self._pan_mode or self._zoom_window_mode:
            self._hover_x = None
            self._hover_y = None
            self.update()
        else:
            self._hover_x = x
            self._hover_y = y
            self.update()
        self._emitCursorNode()
        super(ProfilePlotWidget, self).mouseMoveEvent(event)

    def _panTo(self, x, y):
        area = self._last_area
        if area is None or area.width() <= 0 or self._drag_start_view is None:
            return
        x0, x1 = self._drag_start_view[0], self._drag_start_view[1]
        start_x = self._drag_start[0]
        delta_x = (x - start_x) / area.width() * (x1 - x0)
        self._view_x = self._clampX(x0 - delta_x, x1 - delta_x)
        self.update()

    def mouseReleaseEvent(self, event):
        if self._zoom_rect is not None:
            self._applyZoomRect()
            self._zoom_rect = None
            self.update()
        if self._drag_start is not None:
            self._drag_start = None
            self._drag_start_view = None
            if self._pan_mode:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        super(ProfilePlotWidget, self).mouseReleaseEvent(event)

    def _applyZoomRect(self):
        p1, p2 = self._zoom_rect
        if abs(p2.x() - p1.x()) < 4:
            return
        a = self._pixelToData(p1.x(), p1.y())
        b = self._pixelToData(p2.x(), p2.y())
        if a is None or b is None:
            return
        x0, x1 = sorted((a[0], b[0]))
        if x1 - x0 <= 0:
            return
        self._view_x = self._clampX(x0, x1)

    def wheelEvent(self, event):
        x, y = self._eventPos(event)
        data = self._pixelToData(x, y)
        view = self._currentView()
        if data is None or view is None:
            super(ProfilePlotWidget, self).wheelEvent(event)
            return
        delta = event.angleDelta().y() if hasattr(event, "angleDelta") else 0
        factor = (1.0 / 1.3) if delta > 0 else 1.3
        x0, x1 = view[0], view[1]
        data_x = data[0]
        self._view_x = self._clampX(data_x + (x0 - data_x) * factor, data_x + (x1 - data_x) * factor)
        self.update()

    def leaveEvent(self, event):
        self._hover_x = None
        self._hover_y = None
        self.update()
        self._emitCursorNode()
        super(ProfilePlotWidget, self).leaveEvent(event)
