# -*- coding: utf-8 -*-
import os
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
from qgis.PyQt import uic

# Load UI
FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_evolutioncurves_dock.ui"))

class EvolutionPlotWidget(QWidget):
    def __init__(self, parent=None):
        super(EvolutionPlotWidget, self).__init__(parent)
        self.data_x = []
        self.data_y = []
        self.title = ""
        self.x_label = "Time"
        self.y_label = "Value"
        self.is_stepped = False
        self.margin_left = 60
        self.margin_right = 20
        self.margin_top = 10
        self.margin_bottom = 40

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False):
        self.data_x = x
        self.data_y = y
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.is_stepped = is_stepped
        self.update()

    def paintEvent(self, event):
        if not self.data_x or not self.data_y:
            painter = QPainter(self)
            painter.drawText(self.rect(), Qt.AlignCenter, "No data to display")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        plot_rect = QRectF(self.margin_left, self.margin_top, 
                           w - self.margin_left - self.margin_right, 
                           h - self.margin_top - self.margin_bottom)

        # Calculate scales
        min_x, max_x = min(self.data_x), max(self.data_x)
        min_y, max_y = min(self.data_y), max(self.data_y)
        
        # Add small margin to Y axis
        y_range = max_y - min_y
        if y_range == 0:
            min_y -= 1
            max_y += 1
        else:
            min_y -= y_range * 0.1
            max_y += y_range * 0.1

        x_range = max_x - min_x
        if x_range == 0: x_range = 1

        def to_screen(x, y):
            sx = plot_rect.left() + (x - min_x) / x_range * plot_rect.width()
            sy = plot_rect.bottom() - (y - min_y) / (max_y - min_y) * plot_rect.height()
            return QPointF(sx, sy)

        # Draw Grid & Axes
        pen_grid = QPen(QColor(220, 220, 220), 1, Qt.DashLine)
        painter.setPen(pen_grid)
        
        # Horizontal lines (Y axis)
        num_ticks_y = 5
        for i in range(num_ticks_y + 1):
            val_y = min_y + i * (max_y - min_y) / num_ticks_y
            pt = to_screen(min_x, val_y)
            painter.drawLine(QPointF(plot_rect.left(), pt.y()), QPointF(plot_rect.right(), pt.y()))
            painter.setPen(Qt.black)
            painter.drawText(QRectF(0, pt.y() - 10, self.margin_left - 5, 20), Qt.AlignRight | Qt.AlignVCenter, f"{val_y:.2f}")
            painter.setPen(pen_grid)

        # Vertical lines (X axis)
        num_ticks_x = 6
        for i in range(num_ticks_x + 1):
            val_x = min_x + i * x_range / num_ticks_x
            pt = to_screen(val_x, min_y)
            painter.drawLine(QPointF(pt.x(), plot_rect.top()), QPointF(pt.x(), plot_rect.bottom()))
            painter.setPen(Qt.black)
            painter.drawText(QRectF(pt.x() - 30, plot_rect.bottom() + 5, 60, 20), Qt.AlignCenter, f"{val_x:.1f}")
            painter.setPen(pen_grid)

        # Main Axes
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.bottomRight())
        painter.drawLine(plot_rect.bottomLeft(), plot_rect.topLeft())

        painter.setFont(QFont("Arial", 9))
        painter.save()
        painter.translate(15, h/2)
        painter.rotate(-90)
        painter.drawText(QRectF(-100, -15, 200, 30), Qt.AlignCenter, self.y_label)
        painter.restore()
        
        painter.drawText(QRectF(self.margin_left, h - self.margin_bottom + 20, plot_rect.width(), 20), Qt.AlignCenter, self.x_label)

        # Draw Curve
        if len(self.data_x) > 1:
            pen_curve = QPen(QColor(0, 120, 215), 2)
            painter.setPen(pen_curve)
            path = QPainterPath()
            
            start_pt = to_screen(self.data_x[0], self.data_y[0])
            path.moveTo(start_pt)
            
            for i in range(1, len(self.data_x)):
                next_pt = to_screen(self.data_x[i], self.data_y[i])
                if self.is_stepped:
                    # Constant between points: horizontal then vertical
                    path.lineTo(next_pt.x(), start_pt.y())
                    path.lineTo(next_pt)
                else:
                    path.lineTo(next_pt)
                start_pt = next_pt
            
            painter.drawPath(path)

class QGISRedEvolutionCurvesDock(QDockWidget, FORM_CLASS):
    def __init__(self, iface, parent=None):
        super(QGISRedEvolutionCurvesDock, self).__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        
        # Create the custom plot widget and add it to the container
        self.plot = EvolutionPlotWidget(self.chartContainer)
        layout = QVBoxLayout(self.chartContainer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot)
        self.chartContainer.setLayout(layout)

    def updatePlot(self, x, y, title, x_label, y_label, is_stepped=False):
        self.lblTitle.setText(title)
        self.plot.setData(x, y, title, x_label, y_label, is_stepped)
