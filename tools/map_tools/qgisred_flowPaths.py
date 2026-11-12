# -*- coding: utf-8 -*-
"""Map tool of the upstream / downstream routes.

Unlike QGISRedSelectPointTool, clicks away from every node are meaningful
here (a double click clears the routes). So the tool reports every click and
double click, left or right, snapped or not, and leaves deciding what was hit
to its owner.
"""
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool

from ..utils.qgisred_styling_utils import create_combined_cursor


class QGISRedFlowPathsTool(QgsMapTool):
    def __init__(self, button, parent, method, cursor=None, doubleClickMethod=None):
        QgsMapTool.__init__(self, parent.iface.mapCanvas())
        self.canvas = parent.iface.mapCanvas()
        self.iface = parent.iface
        self.parent = parent
        self.method = method
        self.doubleClickMethod = doubleClickMethod
        self.setAction(button)
        self.custom_cursor = (
            create_combined_cursor(cursor, self.iface, 24) if cursor else Qt.CursorShape.CrossCursor
        )

    def activate(self):
        if getattr(self.parent, "isUnloading", False):
            return
        QgsMapTool.activate(self)
        self.canvas.setCursor(self.custom_cursor)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return False

    def canvasReleaseEvent(self, event):
        if getattr(self.parent, "isUnloading", False):
            return
        # Both buttons do the same.
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.method(QgsPointXY(self.toMapCoordinates(event.pos())))

    def canvasDoubleClickEvent(self, event):
        if getattr(self.parent, "isUnloading", False) or self.doubleClickMethod is None:
            return
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self.doubleClickMethod(QgsPointXY(self.toMapCoordinates(event.pos())))
