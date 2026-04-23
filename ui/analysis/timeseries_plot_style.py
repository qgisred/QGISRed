# -*- coding: utf-8 -*-
from qgis.PyQt.QtGui import QColor, QFont


FONT_FAMILY = "Arial"

DEFAULT_SERIES_COLOR = QColor(0, 120, 215)
PLOT_BG_COLOR = QColor(245, 250, 255)
GRID_COLOR = QColor(220, 232, 245)
BORDER_COLOR = QColor(200, 200, 200)
TEXT_DARK = QColor(20, 20, 20)
TEXT_AXIS = QColor(40, 40, 40)
TOOLTIP_BORDER = QColor(0, 128, 0)
TOOLTIP_SEPARATOR = QColor(170, 170, 170)

AXIS_MAX_TICKS = 30
LEGEND_ICON_SIZE = 12
LEGEND_ROW_H = 14
LEGEND_ROW_GAP = 16
PLOT_TOP_PAD = 10


def qfont(size: int, *, bold: bool = False) -> QFont:
    f = QFont(FONT_FAMILY, size)
    if bold:
        f.setBold(True)
    return f

