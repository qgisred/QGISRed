# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QObject, QEvent


class QGISRedCloseGuard(QObject):
    """Lets the plugin veto or take over the QGIS main window close before QGIS asks to save."""

    def __init__(self, beforeClose, parent=None):
        super().__init__(parent)
        self._beforeClose = beforeClose

    def eventFilter(self, watched, event):
        if event.type() != QEvent.Type.Close:
            return False
        if self._beforeClose():
            return False
        event.ignore()
        return True
