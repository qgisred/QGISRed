# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath, QFontMetrics
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
            num_ticks_y = 5
            if self.y_categorical_labels:
                num_ticks_y = len(self.y_categorical_labels) - 1
            
            for i in range(num_ticks_y + 1):
                if self.y_categorical_labels:
                    label_text = self.y_categorical_labels[i]
                else:
                    val_y = min_y + i * (max_y - min_y) / num_ticks_y
                    label_text = f"{val_y:.2f}"
                
                label_w = fm.horizontalAdvance(label_text)
                if label_w > max_label_w:
                    max_label_w = label_w
            
            local_margin_left = max_label_w + 40
            if local_margin_left < 60: local_margin_left = 60
            
        return QRectF(local_margin_left, self.margin_top + 10, 
                      w - local_margin_left - self.margin_right, 
                      h - (self.margin_top + 10) - self.margin_bottom), local_margin_left

    def paintEvent(self, event):
        if not self.data_x or not self.data_y:
            painter = QPainter(self)
            painter.drawText(self.rect(), Qt.AlignCenter, self.tr("No data to display, please select an element on the map."))
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        
        # Draw Background
        painter.fillRect(self.rect(), Qt.white)
        
        # Draw Title
        if self.title:
            painter.save()
            font_title = QFont("Arial", 12)
            font_title.setBold(True)
            painter.setFont(font_title)
            painter.setPen(Qt.black)
            painter.drawText(QRectF(0, 0, w, self.margin_top), Qt.AlignCenter | Qt.AlignBottom, self.title)
            painter.restore()

        plot_rect, local_margin_left = self.getPlotRect()

        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(plot_rect)

        # Prepare Y axis scaling
        if self.y_categorical_labels:
            min_y = 0
            max_y = len(self.y_categorical_labels) - 1
            num_ticks_y = max_y
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

        # Calculate X scale
        min_x, max_x = min(self.data_x), max(self.data_x)
        x_range = max_x - min_x
        if x_range == 0: x_range = 1

        def to_screen(x, y):
            sx = plot_rect.left() + (x - min_x) / x_range * plot_rect.width()
            sy = plot_rect.bottom() - (y - min_y) / (max_y - min_y) * plot_rect.height()
            return QPointF(sx, sy)

        # Draw Grid & Axes
        painter.setFont(QFont("Arial", 9))
        pen_grid = QPen(QColor(235, 235, 235), 1, Qt.SolidLine)
        painter.setPen(pen_grid)
        
        # Horizontal lines (Y axis)
        for i in range(num_ticks_y + 1):
            if self.y_categorical_labels:
                val_y = i 
                label_text = self.y_categorical_labels[i]
            else:
                val_y = min_y + i * (max_y - min_y) / num_ticks_y
                label_text = f"{val_y:.2f}"
                
            pt = to_screen(min_x, val_y)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.black)
            # Draw text relative to dynamic margin
            painter.drawText(QRectF(0, pt.y() - 10, local_margin_left - 5, 20), Qt.AlignRight | Qt.AlignVCenter, label_text)
            painter.setPen(pen_grid)

        # Vertical lines (X axis)
        if len(self.data_x) > 1:
            # We want to use values from data_x to ensure they are "real" time steps
            # but if there are too many, we take a subset
            max_ticks_x = 10
            step = max(1, len(self.data_x) // max_ticks_x)
            tick_indices = list(range(0, len(self.data_x), step))
            # Ensure last point is included if not already
            if (len(self.data_x) - 1) not in tick_indices:
                tick_indices.append(len(self.data_x) - 1)
                
            for idx in tick_indices:
                val_x = self.data_x[idx]
                pt = to_screen(val_x, min_y)
                painter.setPen(pen_grid)
                painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))
                
                painter.setPen(Qt.black)
                label_x = f"{int(val_x)}" if abs(val_x - int(val_x)) < 0.001 else f"{val_x:.1f}"
                painter.drawText(QRectF(pt.x() - 30, plot_rect.bottom() + 5, 60, 20), Qt.AlignCenter, label_x)

        # Main Axes
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())

        # Axis Title labels
        painter.setFont(QFont("Arial", 9))
        painter.save()
        # Position title centered in the left margin area, but offset from labels
        painter.translate(15, h/2)
        painter.rotate(-90)
        painter.drawText(QRectF(-100, -15, 200, 30), Qt.AlignCenter, self.y_label)
        painter.restore()
        
        painter.drawText(QRectF(local_margin_left, h - self.margin_bottom + 20, plot_rect.width(), 20), Qt.AlignCenter, self.x_label)

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
            
            # Crosshair
            painter.setPen(QPen(QColor(200, 200, 200), 1, Qt.DashLine))
            painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            
            # Highlight point
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            painter.setBrush(Qt.white)
            painter.drawEllipse(pt, 4, 4)
            
            # Tooltip box
            if self.y_categorical_labels:
                val_y_str = self.y_categorical_labels[int(round(val_y))]
            else:
                val_y_str = f"{val_y:.2f}"
            text = f"T: {val_x:.2f} h\nV: {val_y_str}"
            font_tt = QFont("Arial", 8)
            painter.setFont(font_tt)
            fm = painter.fontMetrics()
            
            # Use flags to correctly handle multi-line text bonding box
            rect_tt = fm.boundingRect(self.rect(), Qt.AlignCenter, text)
            rect_tt.adjust(-5, -5, 5, 5)
            
            # Position tooltip box
            tt_x = int(pt.x() + 10)
            tt_y = int(pt.y() - 10 - rect_tt.height())
            
            # Keep inside widget
            if tt_x + rect_tt.width() > w: 
                tt_x = int(pt.x() - 10 - rect_tt.width())
            if tt_y < 0: 
                tt_y = int(pt.y() + 10)
            
            rect_tt.moveTo(tt_x, tt_y)
            
            painter.setPen(QPen(Qt.black, 1))
            painter.setBrush(QColor(255, 255, 225)) # Light yellow
            painter.drawRect(rect_tt)
            painter.drawText(rect_tt, Qt.AlignCenter, text)

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
