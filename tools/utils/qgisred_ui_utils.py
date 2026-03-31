# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFrame, QLabel, QHBoxLayout, QPushButton, QGridLayout
from PyQt5.QtCore import QTimer


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
