# -*- coding: utf-8 -*-
from unittest.mock import patch

from QGISRed.ui.queries.statistics_histogram_layout import (
    adaptive_axis_tick_font_size,
    cap_bottom_margin,
    rotated_x_label_extra_height,
    x_tick_labels_need_rotation,
)


class _StubFontMetrics:
    """Métricas fijas para probar la lógica sin depender de QFontMetrics real/mockeado."""

    _HEIGHT_BY_SIZE = {6: 9, 7: 10, 8: 11, 9: 12}

    def __init__(self, tick_font_size=9):
        self._tick_font_size = int(tick_font_size)

    def height(self):
        return self._HEIGHT_BY_SIZE.get(self._tick_font_size, 12)

    def descent(self):
        return 2

    def horizontalAdvance(self, text):
        return max(8, 7 * len(str(text)))


class TestAdaptiveAxisTickFontSize:
    def test_scales_down_for_small_panels(self):
        assert adaptive_axis_tick_font_size(160, 140) == 6
        assert adaptive_axis_tick_font_size(400, 300) == 9


class TestRotatedLabelLayout:
    @patch("QGISRed.ui.queries.statistics_histogram_layout.QFontMetrics")
    @patch("QGISRed.ui.queries.statistics_histogram_layout.qfont")
    def test_rotation_detected_from_label_width(self, mock_qfont, mock_fm_cls):
        def qfont_side_effect(size, **kwargs):
            return type("Font", (), {"tick_font_size": size})()

        mock_qfont.side_effect = qfont_side_effect
        mock_fm_cls.side_effect = lambda font: _StubFontMetrics(getattr(font, "tick_font_size", 9))

        bins = [{"label": "Very long class label"}]
        assert x_tick_labels_need_rotation(bins, plot_width=80, tick_font_size=9)

    def test_cap_bottom_margin_preserves_minimum_plot_height(self):
        # Narrow cumulative panel: bottom margin must not consume the whole chart.
        capped = cap_bottom_margin(140, margin_top=24, base_bottom=34, rotated_extra=70)
        assert capped <= 63
        assert 140 - 24 - capped >= 48


class TestRotatedLabelExtraHeight:
    @patch("QGISRed.ui.queries.statistics_histogram_layout.QFontMetrics")
    @patch("QGISRed.ui.queries.statistics_histogram_layout.qfont")
    def test_smaller_font_needs_less_vertical_space(self, mock_qfont, mock_fm_cls):
        def qfont_side_effect(size, **kwargs):
            return type("Font", (), {"tick_font_size": size})()

        mock_qfont.side_effect = qfont_side_effect
        mock_fm_cls.side_effect = lambda font: _StubFontMetrics(getattr(font, "tick_font_size", 9))

        large = rotated_x_label_extra_height(9, 80, has_x_label=True)
        small = rotated_x_label_extra_height(6, 80, has_x_label=True)
        assert small < large
