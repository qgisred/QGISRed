# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QCoreApplication, QPointF, QRectF, Qt
from qgis.PyQt.QtGui import QColor, QFontMetrics
from qgis.PyQt.QtWidgets import QSizePolicy, QWidget

from ..queries.statistics_histogram_layout import (
    adaptive_axis_tick_font_size,
    cap_bottom_margin,
    cumulative_right_axis_margin,
    longest_x_label_width,
    rotated_x_label_extra_height,
    x_tick_labels_need_rotation,
)
from .results_distribution_renderer import ResultsDistributionRenderer
from ...tools.utils.qgisred_axis_scale_utils import compute_nice_scale, estimate_max_ticks, format_number_tick
from .timeseries_plot_style import qfont

PANEL_BG_COLOR = QColor(248, 249, 251)


def resolve_distribution_hover_at(widget, cursor_pos):
    """Return (hover_index, hover_segment, curve_sample) for a cursor position."""
    plot_rect = widget.getPlotRect()
    if not widget.bins or not plot_rect.contains(cursor_pos):
        return None, None, None

    # When the cumulative curve crosses a bar, prefer the curve tooltip:
    # bar values are easier to read elsewhere; cumulative values are not.
    if widget._hasCumulativeCurve():
        curve_sample = widget._renderer.hitTestCumulativeCurve(widget, cursor_pos, plot_rect)
        if curve_sample is not None:
            return None, "curve", curve_sample

    if widget._barRects:
        bar_hit = widget._hoverBarAt(cursor_pos, plot_rect)
        if bar_hit[0] is not None:
            return bar_hit[0], bar_hit[1], None

    return None, None, None


def resolve_hover_bar_at(bar_rects, cumulative_bar_rects, has_cumulative_bars, cursor_pos, plot_rect):
    """Return (bin_index, segment) for a cursor over a bar column.

    Detection spans the whole column height (not just the drawn bar) so that
    small or zero-count bars are easy to point at. Direct coordinate comparison
    avoids QRectF.intersected(), which returns a null rect for empty bars. When
    a cumulative bar covers the cursor, the segment still distinguishes
    frequency from cumulative.
    """
    plot_top = plot_rect.top()
    plot_bottom = plot_rect.bottom()
    cursor_x = cursor_pos.x()
    cursor_y = cursor_pos.y()
    if not (plot_top <= cursor_y <= plot_bottom):
        return None, None
    for bin_index, bar_rect in enumerate(bar_rects):
        bar_left = max(bar_rect.left(), plot_rect.left())
        bar_right = min(bar_rect.right(), plot_rect.right())
        if bar_right <= bar_left or not (bar_left <= cursor_x <= bar_right):
            continue

        cum_top = cum_bottom = None
        cum_has_height = False
        if has_cumulative_bars and bin_index < len(cumulative_bar_rects):
            cumulative_rect = cumulative_bar_rects[bin_index]
            if cumulative_rect is not None:
                cum_top = max(cumulative_rect.top(), plot_top)
                cum_bottom = min(cumulative_rect.bottom(), plot_bottom)
                cum_has_height = cum_bottom > cum_top

        if cum_has_height:
            if cum_top <= cursor_y <= cum_bottom:
                freq_top = bar_rect.top()
                frequency_top = freq_top if bar_rect.bottom() > freq_top else cum_bottom + 1
                if cursor_y < frequency_top:
                    return bin_index, "cumulative"
                return bin_index, "frequency"
            continue

        return bin_index, "frequency"

    return None, None


class ResultsDistributionWidget(QWidget):
    """Distribution histogram for the results dock (hover tooltips, no zoom/pan)."""

    _TICK_CHAR_WIDTH = 6.0

    def tr(self, message):
        return QCoreApplication.translate("ResultsDistributionWidget", message)

    def __init__(self, parent=None):
        super(ResultsDistributionWidget, self).__init__(parent)
        self.title = ""
        self.subtitle = ""
        self.bins = []
        self.cumulative_points = []
        self.bar_mode = "plain"
        self.cumulative_mode = None
        self.xLabel = ""
        self.yLabelLeft = ""
        self.yLabelRight = ""
        self.hoverIndex = None
        self.hoverSegment = None
        self.hoverCurveSample = None
        self._barRects = []
        self._cumulativeBarRects = []
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._renderer = ResultsDistributionRenderer()
        self.setMouseTracking(True)
        # Enabled dynamically by the results dock when a single chart is shown.
        self.show_title = False
        self.show_subtitle = False
        self.show_x_axis_title = False
        self.outer_fill_color = PANEL_BG_COLOR
        self.marginLeft = 48
        self.marginRight = 12
        self.marginTop = 6
        self.marginBottom = 40
        self._axisTickFontSize = 9
        self._rotatedLabelExtra = 0
        self.setMinimumSize(180, 192)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setBins(
        self,
        bins,
        bar_mode="plain",
        cumulative_mode=None,
        cumulative_points=None,
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
        self.cumulative_points = list(cumulative_points or [])
        self.bar_mode = bar_mode if bar_mode in ("plain", "relative", "none") else "plain"
        self.cumulative_mode = cumulative_mode if cumulative_mode in ("absolute", "relative") else None
        self.xLabel = xLabel or ""
        self.yLabelLeft = yLabelLeft or ""
        self.yLabelRight = yLabelRight or ""
        self._totalCount = sum(bin_data.get("count", 0) for bin_data in self.bins)
        self.hoverIndex = None
        self.hoverSegment = None
        self.hoverCurveSample = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._fitMargins()
        self.update()

    def clear(self):
        self.title = ""
        self.subtitle = ""
        self.bins = []
        self.cumulative_points = []
        self.bar_mode = "plain"
        self.cumulative_mode = None
        self.xLabel = ""
        self.yLabelLeft = ""
        self.yLabelRight = ""
        self._totalCount = 0
        self.hoverIndex = None
        self.hoverSegment = None
        self.hoverCurveSample = None
        self.zoomFactor = 1.0
        self.panOffset = 0.0
        self._fitMargins()
        self.update()

    def axisTickFontSize(self):
        return self._axisTickFontSize

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
        has_cumulative_points = self.cumulative_mode in ("absolute", "relative") and self.cumulative_points
        has_cumulative_bars = (
            self.cumulative_mode in ("absolute", "relative")
            and not self.cumulative_points
            and any("cumulative_count" in bin_data for bin_data in self.bins)
        )
        if has_cumulative_points:
            top += 18
        self.marginTop = top

        self._axisTickFontSize = adaptive_axis_tick_font_size(self.width(), self.height()) + 1
        tick_font = qfont(self._axisTickFontSize)
        font_metrics = QFontMetrics(tick_font)
        label_height = font_metrics.height() + 4
        plot_height = max(40, self.height() - self.marginTop - self.marginBottom)
        plot_width = max(40, self.width() - self.marginLeft - self.marginRight)

        max_tick_label_width = 0
        if self.bins:
            if self.bar_mode == "relative":
                total = self._totalCount or 1
                values = [(bin_data.get("count", 0) / float(total)) * 100.0 for bin_data in self.bins]
                if has_cumulative_bars:
                    values.extend(
                        (bin_data.get("cumulative_count", 0) / float(total)) * 100.0
                        for bin_data in self.bins
                    )
            else:
                values = [bin_data.get("count", 0) for bin_data in self.bins]
                if has_cumulative_bars:
                    values.extend(bin_data.get("cumulative_count", 0) for bin_data in self.bins)
            data_min = min(values + [0.0])
            data_max = max(values + [0.0])
            if data_max == data_min:
                data_max = data_min + 1.0
            max_ticks = estimate_max_ticks(plot_height, label_height, max_ticks=8)
            scale = compute_nice_scale(data_min, data_max, max_ticks, include_zero=True)
            for tick_value in scale.ticks():
                label = format_number_tick(tick_value, scale.step)
                max_tick_label_width = max(max_tick_label_width, font_metrics.horizontalAdvance(label))

        title_strip = 22 if self.yLabelLeft else 4
        self.marginLeft = max(34, min(76, title_strip + max_tick_label_width + 9))

        if has_cumulative_points:
            cumulative_max = 100.0 if self.cumulative_mode == "relative" else float(max(self._totalCount, 1))
            max_ticks = estimate_max_ticks(plot_height, label_height, max_ticks=8)
            right_scale = compute_nice_scale(0.0, cumulative_max, max_ticks, include_zero=True)
            right_tick_labels = [
                format_number_tick(tick_value, right_scale.step) for tick_value in right_scale.ticks()
            ]
            self.marginRight = cumulative_right_axis_margin(
                self._axisTickFontSize,
                right_tick_labels,
                self.yLabelRight,
                min_margin=40,
                max_margin=96,
            )
        else:
            self.marginRight = max(8, min(18, max(8, plot_width // 30)))

        plot_width = max(0, self.width() - self.marginLeft - self.marginRight)
        rotate = x_tick_labels_need_rotation(self.bins, plot_width, self._axisTickFontSize, self._TICK_CHAR_WIDTH)
        show_x_title = bool(self.xLabel) and self.show_x_axis_title
        base_bottom = label_height + (18 if rotate else 12)
        if show_x_title and not rotate:
            base_bottom += font_metrics.height() + 4
        self.marginBottom = max(30, min(52, base_bottom))

        if rotate:
            max_label_width = longest_x_label_width(self.bins, self._axisTickFontSize)
            rotated_extra = rotated_x_label_extra_height(
                self._axisTickFontSize,
                max_label_width,
                has_x_label=show_x_title,
            )
            self._rotatedLabelExtra = cap_bottom_margin(
                self.height(),
                self.marginTop,
                self.marginBottom,
                rotated_extra,
            ) - self.marginBottom
        else:
            self._rotatedLabelExtra = 0

    def xTickLabelsNeedRotation(self):
        plot_width = max(0, self.width() - self.marginLeft - self.marginRight)
        return x_tick_labels_need_rotation(self.bins, plot_width, self._axisTickFontSize, self._TICK_CHAR_WIDTH)

    def getPlotRect(self):
        x = self.marginLeft
        y = self.marginTop
        width = max(0, self.width() - self.marginLeft - self.marginRight)
        bottom_margin = self.marginBottom + self._rotatedLabelExtra
        height = max(0, self.height() - self.marginTop - bottom_margin)
        return QRectF(x, y, width, height)

    def paintEvent(self, event):
        from qgis.PyQt.QtGui import QPainter

        painter = QPainter(self)
        self._renderer.render(self, painter)

    def wheelEvent(self, event):
        event.ignore()

    def leaveEvent(self, event):
        if self.hoverIndex is not None or self.hoverSegment is not None or self.hoverCurveSample is not None:
            self.hoverIndex = None
            self.hoverSegment = None
            self.hoverCurveSample = None
            self.update()

    def _curveHoverKey(self, curve_sample):
        if curve_sample is None:
            return None
        return (round(curve_sample["screen_x"]), round(curve_sample["screen_y"]))

    def mouseMoveEvent(self, event):
        cursor_pos = QPointF(event.pos())
        new_index, new_segment, new_curve = self._hoverAt(cursor_pos)
        if (
            new_index != self.hoverIndex
            or new_segment != self.hoverSegment
            or self._curveHoverKey(new_curve) != self._curveHoverKey(self.hoverCurveSample)
        ):
            self.hoverIndex = new_index
            self.hoverSegment = new_segment
            self.hoverCurveSample = new_curve
            self.update()

    def _hasCumulativeBars(self):
        return (
            self.cumulative_mode in ("absolute", "relative")
            and not self.cumulative_points
            and any(bin_data.get("cumulative_count") is not None for bin_data in self.bins)
        )

    def _hasCumulativeCurve(self):
        return (
            self.cumulative_mode in ("absolute", "relative")
            and bool(self.cumulative_points)
        )

    def _hoverAt(self, cursor_pos):
        return resolve_distribution_hover_at(self, cursor_pos)

    def _hoverBarAt(self, cursor_pos, plot_rect):
        return resolve_hover_bar_at(
            self._barRects,
            self._cumulativeBarRects,
            self._hasCumulativeBars(),
            cursor_pos,
            plot_rect,
        )
