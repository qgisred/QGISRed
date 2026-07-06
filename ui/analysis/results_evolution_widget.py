# -*- coding: utf-8 -*-
from contextlib import suppress
from qgis.PyQt.QtCore import QRectF, QSize, Qt, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QToolButton

from .qgisred_timeseries_dock import TimeSeriesPlotWidget


_ICON_BUTTON_STYLE = (
    "QToolButton {"
    " border: 1px solid #9aa7b4; border-radius: 3px;"
    " padding: 1px; background-color: rgba(255, 255, 255, 0.92); }"
    "QToolButton:hover { background-color: #eaf1f8; border-color: #5b86b0; }"
    "QToolButton:pressed { background-color: #d7e2ee; }"
)

_DOCK_AXIS_FONT_SIZE = 8
_POPOUT_AXIS_FONT_SIZE = 11


class ResultsEvolutionPlotWidget(TimeSeriesPlotWidget):
    expandClicked = pyqtSignal()

    def __init__(self, parent=None, expanded=False):
        super(ResultsEvolutionPlotWidget, self).__init__(parent)
        self._simplified_cursor_only = True
        self._applyAxisFontSize(_POPOUT_AXIS_FONT_SIZE if expanded else _DOCK_AXIS_FONT_SIZE)
        self._base_min_w = 180
        self._base_min_h = 120
        self.setMinimumSize(self._base_min_w, self._base_min_h)
        self.margin_top = 22
        self.margin_left = 40
        self.margin_right = 10
        self.margin_bottom = 32

        self._expandButton = QToolButton(self)
        self._expandButton.setObjectName("evolutionExpandOverlay")
        self._expandButton.setIcon(QIcon(":/images/iconTsZoomWindow.svg"))
        self._expandButton.setIconSize(QSize(12, 12))
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
        if not (x and y):
            self._y_label_left = ""
        self._positionOverlayButtons()

    def _applyAxisFontSize(self, size):
        size = int(size)
        for cfg in (self._axis_cfg_x, self._axis_cfg_y_left, self._axis_cfg_y_right):
            if cfg is None:
                continue
            cfg.tick_font_size = size
            cfg.title_font_size = size

    def getPlotRect(self):
        plot_rect, local_margin_left, right_axis_label_w = super(ResultsEvolutionPlotWidget, self).getPlotRect()
        if not (self._y_label_left or "").strip():
            return plot_rect, local_margin_left, right_axis_label_w
        new_left = max(30.0, float(local_margin_left) - 24.0)
        delta = float(local_margin_left) - new_left
        if delta > 0:
            plot_rect = QRectF(plot_rect.left() - delta, plot_rect.top(), plot_rect.width() + delta, plot_rect.height())
        return plot_rect, new_left, right_axis_label_w

    def resizeEvent(self, event):
        super(ResultsEvolutionPlotWidget, self).resizeEvent(event)
        self._positionOverlayButtons()

    def _positionOverlayButtons(self):
        with suppress(Exception):
            margin = 2
            self._expandButton.adjustSize()
            expand_w = self._expandButton.width()
            right = self.width() - margin
            self._expandButton.move(max(margin, right - expand_w), margin)
            self._expandButton.raise_()

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
