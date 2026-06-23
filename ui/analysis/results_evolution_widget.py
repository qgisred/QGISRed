# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QRectF, QSize, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolButton

from .qgisred_timeseries_dock import TimeSeriesPlotWidget


_ICON_BUTTON_STYLE = (
    "QToolButton {"
    " border: 1px solid #9aa7b4; border-radius: 4px;"
    " padding: 2px; background-color: rgba(255, 255, 255, 0.92); }"
    "QToolButton:hover { background-color: #eaf1f8; border-color: #5b86b0; }"
    "QToolButton:pressed { background-color: #d7e2ee; }"
)


class ResultsEvolutionPlotWidget(TimeSeriesPlotWidget):
    expandClicked = pyqtSignal()

    def __init__(self, parent=None):
        super(ResultsEvolutionPlotWidget, self).__init__(parent)
        self._simplified_cursor_only = True
        self._base_min_w = 180
        self._base_min_h = 150
        self.setMinimumSize(self._base_min_w, self._base_min_h)
        self.margin_top = 22
        self.margin_left = 40
        self.margin_right = 10
        self.margin_bottom = 32

        self._expandButton = QToolButton(self)
        self._expandButton.setObjectName("evolutionExpandOverlay")
        self._expandButton.setIcon(QIcon(":/images/iconTsZoomWindow.svg"))
        self._expandButton.setIconSize(QSize(15, 15))
        self._expandButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expandButton.setStyleSheet(_ICON_BUTTON_STYLE)
        self._expandButton.clicked.connect(self.expandClicked)

        self._updateMinimumWidthForTitle()
        self._positionOverlayButtons()

    def setData(self, x, y, title="", x_label="Time", y_label="Value", is_stepped=False, y_categorical_labels=None, series_label=""):
        super(ResultsEvolutionPlotWidget, self).setData(
            x, y, title=title, x_label=x_label, y_label=y_label,
            is_stepped=is_stepped, y_categorical_labels=y_categorical_labels, series_label=series_label,
        )
        self._y_label_left = ""
        self._positionOverlayButtons()

    def getPlotRect(self):
        plot_rect, local_margin_left, right_axis_label_w = super(ResultsEvolutionPlotWidget, self).getPlotRect()
        new_left = max(30.0, float(local_margin_left) - 26.0)
        delta = float(local_margin_left) - new_left
        if delta > 0:
            plot_rect = QRectF(plot_rect.left() - delta, plot_rect.top(), plot_rect.width() + delta, plot_rect.height())
        return plot_rect, new_left, right_axis_label_w

    def resizeEvent(self, event):
        super(ResultsEvolutionPlotWidget, self).resizeEvent(event)
        self._positionOverlayButtons()

    def _positionOverlayButtons(self):
        try:
            margin = 4
            top = margin
            right = self.width() - margin
            rect, _, _ = self.getPlotRect()
            if rect.width() > 0 and rect.height() > 0:
                top = int(rect.top()) + 3
                right = int(rect.right()) - 3
            self._expandButton.adjustSize()
            self._expandButton.move(max(margin, right - self._expandButton.width()), top)
            self._expandButton.raise_()
        except Exception:
            pass

    def setExpandState(self, expanded, expand_tip="", collapse_tip=""):
        self._expandButton.setToolTip(collapse_tip if expanded else expand_tip)

    def _legendGroups(self):
        return []

    def wheelEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        event.ignore()

    def contextMenuEvent(self, event):
        event.ignore()
