# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from qgis.PyQt.QtCore import Qt, QPointF, QRectF
from qgis.PyQt.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QFontMetrics
from ...compat import PAINTER_ANTIALIASING
from .qgisred_results_data import seconds_to_time_str
from ...tools.utils.qgisred_axis_scale_utils import (
    compute_nice_scale,
    compute_nice_time_scale_hours,
    estimate_max_ticks,
    format_number_tick,
    format_time_tick_hours,
)
from qgis.PyQt import uic

# Load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_timeseries_dock.ui"))

class TimeSeriesPlotWidget(QWidget):
    def __init__(self, parent=None):
        super(TimeSeriesPlotWidget, self).__init__(parent)
        self.data_x = []
        self.data_y = []
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

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False, y_categorical_labels=None):
        self.data_x = x
        self.data_y = y
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.is_stepped = is_stepped
        self.y_categorical_labels = y_categorical_labels
        self.update()

    def update(self):
        # Trigger recalculation of margins if needed before painting
        super(TimeSeriesPlotWidget, self).update()

    def getPlotRect(self):
        w = self.width()
        h = self.height()
        
        # Calculate max label width to adjust margin dynamically
        # We use a temporary font to measure
        font = QFont("Arial", 9)
        fm = QFontMetrics(font)
        
        if not self.data_y:
            local_margin_left = 60
        else:
            if self.y_categorical_labels:
                min_y = 0
                max_y = len(self.y_categorical_labels) - 1
            else:
                min_y, max_y = min(self.data_y), max(self.data_y)
            
            y_range = max_y - min_y
            if y_range == 0:
                min_y -= 1
                max_y += 1
            else:
                min_y -= y_range * 0.1
                max_y += y_range * 0.1
                
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
            # 2 líneas + padding para que no pise el label del eje X
            local_margin_bottom = max(local_margin_bottom, fm.height() * 2 + 28)

        return QRectF(local_margin_left, self.margin_top + 10,
                      w - local_margin_left - self.margin_right, 
                      h - (self.margin_top + 10) - local_margin_bottom), local_margin_left

    def paintEvent(self, event):
        if not self.data_x or not self.data_y:
            painter = QPainter(self)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.tr("No data to display, please select an element on the map."))
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

        plot_rect, local_margin_left = self.getPlotRect()

        # Draw plot area background (very light blue)
        painter.fillRect(plot_rect, QColor(245, 250, 255))

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(plot_rect)

        # Prepare Y axis scaling
        if self.y_categorical_labels:
            min_y = 0
            max_y = len(self.y_categorical_labels) - 1
            num_ticks_y = max_y
            y_tick_values = list(range(num_ticks_y + 1))
        else:
            min_y, max_y = min(self.data_y), max(self.data_y)
            num_ticks_y = 5
            
        y_range = max_y - min_y
        if y_range == 0:
            min_y -= 1
            max_y += 1
        else:
            min_y -= y_range * 0.1
            max_y += y_range * 0.1

        if not self.y_categorical_labels:
            max_ticks_y = estimate_max_ticks(plot_rect.height(), painter.fontMetrics().height() + 6, min_ticks=2, max_ticks=10)
            y_scale = compute_nice_scale(min_y, max_y, max_ticks_y)
            min_y, max_y = y_scale.axis_min, y_scale.axis_max
            num_ticks_y = y_scale.divisions
            y_tick_values = y_scale.ticks()

        # Calculate X scale
        min_x, max_x = min(self.data_x), max(self.data_x)
        if max_x == min_x:
            max_x = min_x + 1

        max_ticks_x = estimate_max_ticks(plot_rect.width(), 60, min_ticks=2, max_ticks=12)
        x_scale = compute_nice_time_scale_hours(min_x, max_x, max_ticks_x)
        min_x, max_x = x_scale.axis_min, x_scale.axis_max
        x_range = max_x - min_x
        if x_range == 0:
            x_range = 1

        def to_screen(x, y):
            sx = plot_rect.left() + (x - min_x) / x_range * plot_rect.width()
            sy = plot_rect.bottom() - (y - min_y) / (max_y - min_y) * plot_rect.height()
            return QPointF(sx, sy)

        # Draw Grid & Axes
        painter.setFont(QFont("Arial", 9))
        pen_grid = QPen(QColor(220, 232, 245), 1, Qt.PenStyle.SolidLine)
        painter.setPen(pen_grid)
        
        # Horizontal lines (Y axis)
        for i in range(num_ticks_y + 1):
            if self.y_categorical_labels:
                val_y = i
                label_text = self.y_categorical_labels[i]
            else:
                val_y = y_tick_values[i]
                label_text = format_number_tick(val_y, y_scale.step)
                
            pt = to_screen(min_x, val_y)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.GlobalColor.black)
            # Draw text relative to dynamic margin
            painter.drawText(QRectF(0, pt.y() - 10, local_margin_left - 5, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_text)
            painter.setPen(pen_grid)

        # Vertical lines (X axis)
        if len(self.data_x) > 1:
            fm_x = painter.fontMetrics()
            tick_h = fm_x.height() * 2 + 6
            for val_x in x_scale.ticks():
                pt = to_screen(val_x, min_y)
                painter.setPen(pen_grid)
                painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))

                painter.setPen(Qt.GlobalColor.black)
                label_x = format_time_tick_hours(val_x, x_scale.step)
                painter.drawText(QRectF(pt.x() - 40, plot_rect.bottom() + 8, 80, tick_h), Qt.AlignmentFlag.AlignCenter, label_x)

        # Main Axes
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())

        # Axis Title labels
        painter.setFont(QFont("Arial", 9))
        painter.save()
        # Position title properly within the dynamic margin area
        painter.translate(local_margin_left / 2 - 15, h/2)
        painter.rotate(-90)
        painter.drawText(QRectF(-100, -15, 200, 30), Qt.AlignmentFlag.AlignCenter, self.y_label)
        painter.restore()
        
        painter.drawText(QRectF(local_margin_left, h - self.margin_bottom + 20, plot_rect.width(), 20), Qt.AlignmentFlag.AlignCenter, self.x_label)

        # Draw Curve
        hover_pt = None
        if len(self.data_x) > 1:
            pen_curve = QPen(QColor(0, 120, 215), 2)
            painter.setPen(pen_curve)
            path = QPainterPath()
            
            start_pt = to_screen(self.data_x[0], self.data_y[0])
            path.moveTo(start_pt)
            
            for i in range(1, len(self.data_x)):
                next_pt = to_screen(self.data_x[i], self.data_y[i])
                if self.is_stepped:
                    path.lineTo(next_pt.x(), start_pt.y())
                    path.lineTo(next_pt)
                else:
                    path.lineTo(next_pt)
                start_pt = next_pt
            
            painter.drawPath(path)

        # Tooltip / Hover Logic
        if self.hover_index is not None and 0 <= self.hover_index < len(self.data_x):
            val_x = self.data_x[self.hover_index]
            val_y = self.data_y[self.hover_index]
            pt = to_screen(val_x, val_y)
            
            # Crosshair (Soft Red / Coral)
            painter.setPen(QPen(QColor(255, 110, 110), 1, Qt.PenStyle.DashLine))
            painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            
            # Highlight point
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawEllipse(pt, 4, 4)
            
            # Tooltip box
            if self.y_categorical_labels:
                val_y_str = self.y_categorical_labels[int(round(val_y))]
            else:
                val_y_str = f"{val_y:.2f}"
            
            total_seconds = int(round(val_x * 3600))
            time_str = seconds_to_time_str(total_seconds)

            # Try to infer units from y_label, e.g. "Caudal (m³/s)" or "Caudal [m³/s]"
            units = ""
            y_label = self.y_label or ""
            if "(" in y_label and ")" in y_label:
                start = y_label.rfind("(")
                end = y_label.rfind(")")
                if 0 <= start < end:
                    units = y_label[start + 1 : end].strip()
            elif "[" in y_label and "]" in y_label:
                start = y_label.rfind("[")
                end = y_label.rfind("]")
                if 0 <= start < end:
                    units = y_label[start + 1 : end].strip()

            font_tt = QFont("Arial", 8)
            font_tt_bold = QFont(font_tt)
            font_tt_bold.setBold(True)
            fm = QFontMetrics(font_tt)
            fm_bold = QFontMetrics(font_tt_bold)

            units_str = f" {units}" if units else ""
            line1_w = fm_bold.horizontalAdvance(val_y_str) + fm.horizontalAdvance(units_str)
            line2_w = fm.horizontalAdvance(time_str)
            text_w = max(line1_w, line2_w)

            pad = 5
            gap = 2
            text_h = fm.height() * 2 + gap
            rect_tt = QRectF(0, 0, text_w + pad * 2, text_h + pad * 2)
            
            # Position tooltip box
            tt_x = int(pt.x() + 10)
            tt_y = int(pt.y() - 10 - rect_tt.height())
            
            # Keep inside widget
            if tt_x + rect_tt.width() > w: 
                tt_x = int(pt.x() - 10 - rect_tt.width())
            if tt_y < 0: 
                tt_y = int(pt.y() + 10)
            
            rect_tt.moveTo(tt_x, tt_y)
            
            painter.setPen(QPen(QColor(0, 128, 0), 1))
            painter.setBrush(Qt.GlobalColor.white)
            painter.drawRect(rect_tt)

            # Draw centered lines manually to allow mixed weight on line 1
            cx = rect_tt.center().x()
            x1 = cx - (line1_w / 2.0)
            y1 = rect_tt.top() + pad + fm.ascent()

            painter.setFont(font_tt_bold)
            painter.setPen(Qt.GlobalColor.black)
            painter.drawText(QPointF(x1, y1), val_y_str)

            if units_str:
                x_units = x1 + fm_bold.horizontalAdvance(val_y_str)
                painter.setFont(font_tt)
                painter.drawText(QPointF(x_units, y1), units_str)

            y2 = y1 + fm.height() + gap
            x2 = cx - (line2_w / 2.0)
            painter.setFont(font_tt)
            painter.drawText(QPointF(x2, y2), time_str)

    def leaveEvent(self, event):
        if self.hover_index is not None:
            self.hover_index = None
            self.update()

    def mouseMoveEvent(self, event):
        if not self.data_x or len(self.data_x) < 2:
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
                self.update()
            return

        # Calculate scales to reverse map
        min_x, max_x = min(self.data_x), max(self.data_x)
        x_range = max_x - min_x
        if x_range <= 0: x_range = 1
        
        # Find nearest point in data_x
        try:
            rel_x = (mouse_pos.x() - plot_rect.left()) / plot_rect.width()
            target_x = min_x + rel_x * x_range
            
            # Simple linear search for nearest index (more robust than binary for small data)
            best_idx = 0
            min_dist = abs(self.data_x[0] - target_x)
            for i in range(1, len(self.data_x)):
                dist = abs(self.data_x[i] - target_x)
                if dist < min_dist:
                    min_dist = dist
                    best_idx = i
            
            if self.hover_index != best_idx:
                self.hover_index = best_idx
                self.update()
        except ZeroDivisionError:
            pass

class QGISRedTimeSeriesDock(QDockWidget, FORM_CLASS):
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

        # Increase title font size
        self.lblTitle.hide()
        
        # Set white background for the dock and container
        self.setStyleSheet("background-color: white; border: none;")
        self.chartContainer.setStyleSheet("background-color: white;")

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False, y_categorical_labels=None):
        self.plot.setData(x, y, title, x_label, y_label, is_stepped, y_categorical_labels)
