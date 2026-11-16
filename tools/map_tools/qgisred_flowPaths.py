# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsPointXY
from qgis.gui import QgsMapTool

from ..utils.qgisred_styling_utils import create_combined_cursor


class QGISRedFlowPathsTool(QgsMapTool):
    def __init__(self, button, parent, method, cursor=None, doubleClickMethod=None, rightClickMethod=None,
                 escapeMethod=None):
        QgsMapTool.__init__(self, parent.iface.mapCanvas())
        self.canvas = parent.iface.mapCanvas()
        self.iface = parent.iface
        self.parent = parent
        self.method = method
        self.doubleClickMethod = doubleClickMethod
        self.rightClickMethod = rightClickMethod
        self.escapeMethod = escapeMethod
        self._skipRelease = False
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
        if event.button() not in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            return
        if self._skipRelease:
            self._skipRelease = False
            return
        point = QgsPointXY(self.toMapCoordinates(event.pos()))
        if event.button() == Qt.MouseButton.RightButton and self.rightClickMethod is not None:
            if self.rightClickMethod(point):
                return
        self.method(point)

    def canvasDoubleClickEvent(self, event):
        if getattr(self.parent, "isUnloading", False) or self.doubleClickMethod is None:
            return
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton):
            self._skipRelease = True
            self.doubleClickMethod(QgsPointXY(self.toMapCoordinates(event.pos())))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.escapeMethod is not None \
                and not getattr(self.parent, "isUnloading", False):
            self.escapeMethod()
            event.accept()
            return
        QgsMapTool.keyPressEvent(self, event)
