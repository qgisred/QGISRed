# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QGridLayout
from qgis.PyQt.QtCore import Qt, QTimer
from ...compat import QGIS_INFO, QGIS_WARNING, QGIS_CRITICAL, QGIS_SUCCESS


class QGISRedBanner(QFrame):
    """
    A reusable message banner for QGISRed dialogs.
    """
    def __init__(self, parent=None):
        super(QGISRedBanner, self).__init__(parent)
        self.setVisible(False)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.lblMessage = QLabel(self)
        self.layout.addWidget(self.lblMessage)
        self.btClose = QPushButton("X", self)
        self.btClose.setFixedSize(20, 20)
        self.btClose.setStyleSheet("font-weight: bold; border: none; background: transparent; cursor: pointer;")
        self.btClose.clicked.connect(self.hide)
        self.layout.addWidget(self.btClose)

    def pushMessage(self, title, text, level=0, duration=5):
        """
        Shows a message in the banner.
        level: 0=Info/Success (Green), 1=Warning (Yellow), 2=Critical (Red)
        """
        self.lblMessage.setText(f"<b>{title}:</b> {text}")
        if level == 0:  # Success / Info (Green)
            self.setStyleSheet("background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 4px;")
        elif level == 1:  # Warning (Yellow)
            self.setStyleSheet("background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; border-radius: 4px;")
        elif level == 2:  # Critical / Error (Red)
            self.setStyleSheet("background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; border-radius: 4px;")
        else:  # Default (Gray)
            self.setStyleSheet("background-color: #e2e3e5; color: #383d41; border: 1px solid #d6d8db; border-radius: 4px;")

        self.show()
        if duration > 0:
            QTimer.singleShot(duration * 1000, self.hide)

    @staticmethod
    def inject(dialog, layout):
        """
        Helper method to inject the banner at the top of a layout.
        If it's a QGridLayout, it attempts to shift the content at (0,0) down.
        """
        banner = QGISRedBanner(dialog)
        if isinstance(layout, QGridLayout):
            item = layout.itemAtPosition(0, 0)
            if item:
                widget = item.widget()
                internal_layout = item.layout()
                layout.removeItem(item)
                if widget:
                    layout.addWidget(widget, 1, 0)
                elif internal_layout:
                    layout.addLayout(internal_layout, 1, 0)
            layout.addWidget(banner, 0, 0)
        else:
            # For QVBoxLayout and similar, insert at the beginning
            layout.insertWidget(0, banner)
        return banner


class QGISRedUIUtils:
    @staticmethod
    def arrangeDockOrder(mainWindow, resultsDock, explorerDock, queriesDock):
        """Enforce dock vertical order: Results (top) > Element Explorer > Queries by Properties (bottom).

        Skips floating docks — only repositions docks anchored to the main window.
        """
        def _docked(dock):
            return dock is not None and dock.isVisible() and not dock.isFloating()

        results = resultsDock if _docked(resultsDock) else None
        explorer = explorerDock if _docked(explorerDock) else None
        queries = queriesDock if _docked(queriesDock) else None

        if results and explorer:
            mainWindow.splitDockWidget(results, explorer, Qt.Orientation.Vertical)
        if explorer and queries:
            mainWindow.splitDockWidget(explorer, queries, Qt.Orientation.Vertical)
        elif results and queries:
            mainWindow.splitDockWidget(results, queries, Qt.Orientation.Vertical)

    @staticmethod
    def showGlobalMessage(iface, text, level=0, duration=5):
        """
        Standardized global QGIS message bar call for QGISRed.
        level: 0=Info, 1=Warning, 2=Error, 3=Success
        """
        if iface is None:
            return
        # Integer to Qgis.MessageLevel mapping for v3/v4 compatibility
        levels = {
            0: QGIS_INFO,
            1: QGIS_WARNING,
            2: QGIS_CRITICAL,
            3: QGIS_SUCCESS
        }
        qgis_level = levels.get(level, QGIS_INFO)
        iface.messageBar().pushMessage("QGISRed", text, level=qgis_level, duration=duration)
