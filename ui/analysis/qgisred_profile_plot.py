# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt, QPointF, QRectF
from qgis.PyQt.QtGui import QPainter, QColor, QPen, QBrush, QFont, QFontMetrics, QPolygonF
from qgis.PyQt.QtWidgets import QWidget, QSizePolicy

from ...tools.utils.qgisred_axis_scale_utils import compute_nice_scale, format_number_tick
from ...tools.utils.qgisred_profile_plot_utils import (
    profile_line_segments,
    cursor_snapshot,
    format_profile_value,
)


PALETTE = [
    QColor(31, 119, 180),
    QColor(214, 39, 40),
    QColor(44, 160, 44),
    QColor(255, 127, 14),
    QColor(148, 103, 189),
    QColor(140, 86, 75),
]


class ProfilePlotWidget(QWidget):
    def __init__(self, parent=None):
        super(ProfilePlotWidget, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(240)
        self.setMouseTracking(True)
        self._series = []
        self._title = ""
        self._x_label = ""
        self._y_label = ""
        self._empty_text = ""
        self._hover_x = None
        self._show_value_labels = False

    def setEmptyText(self, text):
        self._empty_text = text
        self.update()

    def setShowValueLabels(self, show):
        self._show_value_labels = bool(show)
        self.update()

    def setLabels(self, title, x_label, y_label):
        self._title = title or ""
        self._x_label = x_label or ""
        self._y_label = y_label or ""
        self.update()

    def setSeries(self, series):
        normalized = []
        for i, s in enumerate(series):
            points = [
                (float(d), None if v is None else float(v))
                for d, v in s.get("points", [])
            ]
            normalized.append({
                "label": s.get("label", ""),
                "color": s.get("color") or PALETTE[i % len(PALETTE)],
                "points": points,
                "reference": set(s.get("reference_indices", set())),
                "width": float(s.get("width", 2.0)),
            })
        self._series = normalized
        self.update()

    def clear(self):
        self._series = []
        self._hover_x = None
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
        if not xs:
            return None
        return min(xs), max(xs), min(ys), max(ys)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        full = QRectF(self.rect())
        painter.fillRect(full, QColor(255, 255, 255))

        left, right, top, bottom = 64.0, 18.0, 34.0, 48.0
        plot = QRectF(left, top, max(1.0, full.width() - left - right), max(1.0, full.height() - top - bottom))

        bounds = self._dataBounds()
        if bounds is None:
            painter.setPen(QColor(130, 130, 130))
            painter.drawText(full, Qt.AlignmentFlag.AlignCenter, self._empty_text)
            painter.end()
            return

        xmin, xmax, ymin, ymax = bounds
        x_scale = compute_nice_scale(xmin, xmax, 8)
        y_scale = compute_nice_scale(ymin, ymax, 6)
        x0, x1 = x_scale.axis_min, x_scale.axis_max
        y0, y1 = y_scale.axis_min, y_scale.axis_max
        if x1 == x0:
            x1 = x0 + 1.0
        if y1 == y0:
            y1 = y0 + 1.0

        def px(d):
            return plot.left() + (d - x0) / (x1 - x0) * plot.width()

        def py(v):
            return plot.bottom() - (v - y0) / (y1 - y0) * plot.height()

        painter.fillRect(plot, QColor(250, 252, 255))

        grid_pen = QPen(QColor(223, 233, 244))
        grid_pen.setWidthF(1.0)
        tick_pen = QPen(QColor(120, 130, 145))
        painter.setFont(QFont("Arial", 8))

        for t in y_scale.ticks():
            y = py(t)
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(tick_pen)
            painter.drawText(QRectF(0, y - 8, left - 6, 16),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                             format_number_tick(t, y_scale.step))

        for t in x_scale.ticks():
            x = px(t)
            painter.setPen(grid_pen)
            painter.drawLine(QPointF(x, plot.top()), QPointF(x, plot.bottom()))
            painter.setPen(tick_pen)
            painter.drawText(QRectF(x - 40, plot.bottom() + 4, 80, 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                             format_number_tick(t, x_scale.step))

        painter.setPen(QPen(QColor(150, 160, 175), 1.2))
        painter.drawRect(plot)

        for s in self._series:
            self._drawSeries(painter, s, px, py)

        if self._show_value_labels and self._series:
            self._drawValueLabels(painter, self._series[0], px, py)

        self._drawTitleAndAxisLabels(painter, full, plot)
        self._drawLegend(painter, plot)
        self._drawCursor(painter, plot, px, py, x0, x1)
        painter.end()

    def _drawSeries(self, painter, s, px, py):
        color = s["color"]
        points = s["points"]

        pen = QPen(color)
        pen.setWidthF(s["width"])
        painter.setPen(pen)
        for segment in profile_line_segments(points):
            poly = QPolygonF([QPointF(px(d), py(v)) for d, v in segment])
            painter.drawPolyline(poly)

        reference = s["reference"]
        for idx, (d, v) in enumerate(points):
            if v is None:
                continue
            center = QPointF(px(d), py(v))
            if idx in reference:
                painter.setPen(QPen(QColor(255, 255, 255), 1.2))
                painter.setBrush(QBrush(color))
                painter.drawEllipse(center, 4.0, 4.0)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawEllipse(center, 2.2, 2.2)

    def _drawValueLabels(self, painter, s, px, py):
        painter.setFont(QFont("Arial", 8))
        fm = QFontMetrics(painter.font())
        for idx, (d, v) in enumerate(s["points"]):
            if v is None or idx not in s["reference"]:
                continue
            text = format_profile_value(v)
            width = fm.horizontalAdvance(text) + 8
            rect = QRectF(px(d) - width / 2.0, py(v) - 22, width, 14)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 225)))
            painter.drawRoundedRect(rect, 3, 3)
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def _drawTitleAndAxisLabels(self, painter, full, plot):
        painter.setPen(QColor(30, 30, 30))
        if self._title:
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(QRectF(0, 4, full.width(), 22),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._title)
        painter.setFont(QFont("Arial", 8))
        if self._x_label:
            painter.drawText(QRectF(plot.left(), full.height() - 16, plot.width(), 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self._x_label)
        if self._y_label:
            painter.save()
            painter.translate(14, plot.center().y())
            painter.rotate(-90)
            painter.drawText(QRectF(-plot.height() / 2, -10, plot.height(), 14),
                             Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter, self._y_label)
            painter.restore()

    def _drawLegend(self, painter, plot):
        if not self._series:
            return
        painter.setFont(QFont("Arial", 8))
        fm = QFontMetrics(painter.font())
        x = plot.left() + 10
        y = plot.top() + 8
        box = 22
        for s in self._series:
            label = s["label"] or ""
            w = box + 4 + fm.horizontalAdvance(label) + 12
            painter.fillRect(QRectF(x - 4, y - 2, w, 16), QColor(255, 255, 255, 210))
            pen = QPen(s["color"])
            pen.setWidthF(s["width"])
            painter.setPen(pen)
            painter.drawLine(QPointF(x, y + 6), QPointF(x + box, y + 6))
            painter.setPen(QColor(40, 40, 40))
            painter.drawText(QPointF(x + box + 4, y + 9), label)
            y += 18

    def _drawCursor(self, painter, plot, px, py, x0, x1):
        if self._hover_x is None or not self._series:
            return
        if not (plot.left() <= self._hover_x <= plot.right()):
            return
        data_x = x0 + (self._hover_x - plot.left()) / plot.width() * (x1 - x0)
        snapshot = cursor_snapshot(self._series, data_x)
        if snapshot is None:
            return

        line_x = px(snapshot["distance"])
        painter.setPen(QPen(QColor(120, 120, 120), 1.0, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(line_x, plot.top()), QPointF(line_x, plot.bottom()))

        index = snapshot["index"]
        for s in self._series:
            points = s["points"]
            if index < len(points) and points[index][1] is not None:
                d, v = points[index]
                painter.setPen(QPen(QColor(255, 255, 255), 1.5))
                painter.setBrush(QBrush(s["color"]))
                painter.drawEllipse(QPointF(px(d), py(v)), 4.5, 4.5)

        self._drawReadout(painter, plot, line_x, snapshot)

    def _drawReadout(self, painter, plot, line_x, snapshot):
        painter.setFont(QFont("Arial", 8))
        fm = QFontMetrics(painter.font())
        rows = [(None, "{}: {}".format(self._x_label or "Distance",
                                       format_profile_value(snapshot["distance"])))]
        for entry in snapshot["entries"]:
            rows.append((entry["color"], "{}: {}".format(entry["label"], format_profile_value(entry["value"]))))

        text_width = max(fm.horizontalAdvance(text) for _color, text in rows)
        width = text_width + 26
        height = len(rows) * 15 + 8

        bx = line_x + 12
        if bx + width > plot.right():
            bx = line_x - 12 - width
        bx = max(plot.left() + 2, min(bx, plot.right() - width - 2))
        by = plot.top() + 6

        painter.setPen(QPen(QColor(180, 190, 200)))
        painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
        painter.drawRoundedRect(QRectF(bx, by, width, height), 4, 4)

        ty = by + 6
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

    def mouseMoveEvent(self, event):
        self._hover_x = event.position().x() if hasattr(event, "position") else event.x()
        self.update()
        super(ProfilePlotWidget, self).mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_x = None
        self.update()
        super(ProfilePlotWidget, self).leaveEvent(event)
