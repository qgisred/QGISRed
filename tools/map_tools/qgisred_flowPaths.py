# -*- coding: utf-8 -*-
"""Map tool of the upstream / downstream routes.

Unlike QGISRedSelectPointTool, a click away from every node is meaningful here:
it clears the routes. So the tool reports every left click, snapped or not,
and leaves deciding what was hit to its owner.
"""
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool

from ..utils.qgisred_styling_utils import create_combined_cursor


class QGISRedFlowPathsTool(QgsMapTool):
    def __init__(self, button, parent, method, cursor=None):
        QgsMapTool.__init__(self, parent.iface.mapCanvas())
        self.canvas = parent.iface.mapCanvas()
        self.iface = parent.iface
        self.parent = parent
        self.method = method
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
        if event.button() == Qt.MouseButton.LeftButton:
            self.method(QgsPointXY(self.toMapCoordinates(event.pos())))
        elif event.button() == Qt.MouseButton.RightButton:
            self.canvas.unsetMapTool(self)
