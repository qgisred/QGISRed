# -*- coding: utf-8 -*-
import webbrowser

from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QCheckBox, QPushButton
from qgis.PyQt.QtCore import QUrl, Qt
from qgis.PyQt.QtGui import QIcon


class QGISRedNewsDialog(QDialog):
    def __init__(self, html_content, title, news_id, show_dont_ask=True, parent=None):
        super().__init__(parent)
        self._news_id = news_id
        self.setWindowTitle(title)
        self.setWindowIcon(QIcon(":/images/iconNews.svg"))
        self.resize(750, 520)
        self.setMinimumSize(500, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.anchorClicked.connect(self._openLink)
        self._browser.setHtml(html_content)
        layout.addWidget(self._browser)

        bottom = QHBoxLayout()
        self._checkDontShow = QCheckBox(self.tr("Don't show this news again"))
        self._checkDontShow.setVisible(show_dont_ask)
        bottom.addWidget(self._checkDontShow)
        bottom.addStretch()
        closeBtn = QPushButton(self.tr("Close"))
        closeBtn.setDefault(True)
        closeBtn.clicked.connect(self.accept)
        bottom.addWidget(closeBtn)
        layout.addLayout(bottom)

    def _openLink(self, url: QUrl):
        webbrowser.open(url.toString())

    def dontShowAgain(self):
        return self._checkDontShow.isChecked()

    def newsId(self):
        return self._news_id
