# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor, QFontMetrics
from qgis.PyQt.QtWidgets import QSizePolicy, QWidget

from .results_distribution_renderer import ResultsDistributionRenderer
from ...tools.utils.qgisred_axis_scale_utils import compute_nice_scale, estimate_max_ticks, format_number_tick
from .timeseries_plot_style import qfont

PANEL_BG_COLOR = QColor(248, 249, 251)


class ResultsDistributionWidget(QWidget):
    """Read-only distribution sketch for the results dock (no title, no interaction)."""

    def __init__(self, parent=None):
        super(ResultsDistributionWidget, self).__init__(parent)
        self.title = ""
        self.subtitle = ""
        self.bins = []
        self.bar_mode = "plain"
        self.cumulative_mode = None
        self.xLabel = ""
        self.yLabelLeft = ""
        self.yLabelRight = ""
        self.hoverIndex = None
        self._barRects = []
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._renderer = ResultsDistributionRenderer()
        # Enabled dynamically by the results dock when a single chart is shown.
        self.show_title = False
        self.show_subtitle = False
        self.outer_fill_color = PANEL_BG_COLOR
        self.marginLeft = 48
        self.marginRight = 12
        self.marginTop = 6
        self.marginBottom = 40
        self.setMinimumSize(180, 140)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setBins(
        self,
        bins,
        bar_mode="plain",
        cumulative_mode=None,
        xLabel="",
        yLabelLeft="",
        yLabelRight="",
        mode=None,
        title=None,
        subtitle=None,
    ):
        if mode is not None and bar_mode == "plain":
            bar_mode = mode if mode in ("plain", "relative") else "plain"

        if title is not None:
            self.title = title or ""
        if subtitle is not None:
            self.subtitle = subtitle or ""

        self.bins = list(bins or [])
        self.bar_mode = bar_mode if bar_mode in ("plain", "relative") else "plain"
        self.cumulative_mode = cumulative_mode if cumulative_mode in ("absolute", "relative") else None
        self.xLabel = xLabel or ""
        self.yLabelLeft = yLabelLeft or ""
        self.yLabelRight = yLabelRight or ""
        self._totalCount = sum(bin_data.get("count", 0) for bin_data in self.bins)
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._fitMargins()
        self.update()

    def clear(self):
        self.title = ""
        self.subtitle = ""
        self.bins = []
        self.bar_mode = "plain"
        self.cumulative_mode = None
        self.xLabel = ""
        self.yLabelLeft = ""
        self.yLabelRight = ""
        self._totalCount = 0
        self.hoverIndex = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self.update()

    def resizeEvent(self, event):
        super(ResultsDistributionWidget, self).resizeEvent(event)
        self._fitMargins()
        self.update()

    def _fitMargins(self):
        # Title/subtitle occupy the top area above the plot.
        top = 6
        if getattr(self, "show_title", False) and getattr(self, "title", ""):
            top = 26
            if getattr(self, "show_subtitle", False) and getattr(self, "subtitle", ""):
                top = 40
        self.marginTop = top

        tick_font = qfont(9)
        font_metrics = QFontMetrics(tick_font)
        label_height = font_metrics.height() + 4
        plot_height = max(40, self.height() - self.marginTop - self.marginBottom)
        plot_width = max(40, self.width() - self.marginLeft - self.marginRight)

        max_tick_label_width = 32
        if self.bins:
            if self.bar_mode == "relative":
                total = self._totalCount or 1
                values = [(bin_data.get("count", 0) / float(total)) * 100.0 for bin_data in self.bins]
            else:
                values = [bin_data.get("count", 0) for bin_data in self.bins]
            data_min = min(values + [0.0])
            data_max = max(values + [0.0])
            if data_max == data_min:
                data_max = data_min + 1.0
            max_ticks = estimate_max_ticks(plot_height, label_height, max_ticks=8)
            scale = compute_nice_scale(data_min, data_max, max_ticks, include_zero=True)
            for tick_value in scale.ticks():
                label = format_number_tick(tick_value, scale.step)
                max_tick_label_width = max(max_tick_label_width, font_metrics.horizontalAdvance(label))

        self.marginLeft = max(40, min(76, max_tick_label_width + 14))

        max_right_tick_width = 0
        if self.cumulative_mode in ("absolute", "relative"):
            cumulative_max = 100.0 if self.cumulative_mode == "relative" else float(max(self._totalCount, 1))
            max_ticks = estimate_max_ticks(plot_height, label_height, max_ticks=8)
            right_scale = compute_nice_scale(0.0, cumulative_max, max_ticks, include_zero=True)
            for tick_value in right_scale.ticks():
                label = format_number_tick(tick_value, right_scale.step)
                max_right_tick_width = max(max_right_tick_width, font_metrics.horizontalAdvance(label))
            if self.yLabelRight:
                title_font = qfont(self._renderer._AXIS_TITLE_FONT_SIZE, bold=True)
                # Reserve enough width so the right-axis title doesn't overlap tick labels.
                # Using the full title width (not half) avoids collisions in narrow panels.
                max_right_tick_width = max(
                    max_right_tick_width,
                    QFontMetrics(title_font).horizontalAdvance(self.yLabelRight),
                )

        # Allow a bit more right margin than the previous hard cap (56px) so
        # 2–3 digit tick labels don't collide with the right-axis title.
        self.marginRight = max(12, min(84, max_right_tick_width + 18)) if self.cumulative_mode else max(
            8, min(18, max(8, plot_width // 30))
        )

        max_class_label_width = 0
        for bin_data in self.bins:
            class_label = bin_data.get("label", "")
            if class_label:
                max_class_label_width = max(
                    max_class_label_width,
                    font_metrics.horizontalAdvance(class_label),
                )

        bottom_for_classes = label_height + 20
        if max_class_label_width > 0 and plot_width > 0:
            slot_width = plot_width / max(len(self.bins), 1)
            if max_class_label_width > slot_width * 0.9:
                bottom_for_classes = label_height + 28

        self.marginBottom = max(34, min(64, bottom_for_classes + (8 if self.xLabel else 0)))

    def getPlotRect(self):
        from qgis.PyQt.QtCore import QRectF

        x = self.marginLeft
        y = self.marginTop
        width = max(0, self.width() - self.marginLeft - self.marginRight)
        height = max(0, self.height() - self.marginTop - self.marginBottom)
        return QRectF(x, y, width, height)

    def paintEvent(self, event):
        from qgis.PyQt.QtGui import QPainter

        painter = QPainter(self)
        self._renderer.render(self, painter)

    def wheelEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        event.ignore()
