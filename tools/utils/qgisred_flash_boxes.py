# -*- coding: utf-8 -*-
"""Thin red boxes drawn over map points for a few seconds."""
from contextlib import suppress

from qgis.core import QgsGeometry, QgsRectangle
from qgis.gui import QgsRubberBand
from qgis.PyQt.QtCore import QTimer
from qgis.PyQt.QtGui import QColor

from ...compat import WKB_POLYGON_GEOMETRY

BOX_COLOR = (255, 0, 0)
BOX_WIDTH = 1
BOX_HALF_SIZE_PIXELS = 10
BOX_DURATION_MS = 6000
EXTENT_MARGIN_RATIO = 0.15
MIN_EXTENT_PIXELS = 200


def boundingExtent(points, canvasExtentSize, marginRatio=EXTENT_MARGIN_RATIO):
    """Rectangle (xmin, ymin, xmax, ymax) that contains all points with a margin.

    A single point, or points on a line, are given a margin based on the current canvas size so the
    result is never degenerate.
    """
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    width, height = xmax - xmin, ymax - ymin
    base = max(canvasExtentSize) * 0.10
    marginX = width * marginRatio if width > 0 else base
    marginY = height * marginRatio if height > 0 else base
    return xmin - marginX, ymin - marginY, xmax + marginX, ymax + marginY


class QGISRedFlashBoxes:
    def __init__(self, canvas, durationMs=BOX_DURATION_MS):
        self._canvas = canvas
        self._bands = []
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(durationMs)
        self._timer.timeout.connect(self.clear)

    def show(self, points):
        """Draw one box around each point (QgsPointXY in canvas CRS) and clear them after the duration."""
        self.clear()
        half = self._canvas.mapUnitsPerPixel() * BOX_HALF_SIZE_PIXELS
        for point in points:
            band = QgsRubberBand(self._canvas, WKB_POLYGON_GEOMETRY)
            band.setColor(QColor(*BOX_COLOR))
            band.setFillColor(QColor(0, 0, 0, 0))
            band.setWidth(BOX_WIDTH)
            box = QgsRectangle(point.x() - half, point.y() - half, point.x() + half, point.y() + half)
            band.setToGeometry(QgsGeometry.fromRect(box), None)
            self._bands.append(band)
        if self._bands:
            self._timer.start()

    def clear(self):
        self._timer.stop()
        for band in self._bands:
            with suppress(Exception):
                band.reset()
                self._canvas.scene().removeItem(band)
        self._bands = []
