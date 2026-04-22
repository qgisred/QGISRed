# -*- coding: utf-8 -*-
import math

import pytest


from QGISRed.tools.utils.qgisred_axis_scale_utils import (
    NiceScale,
    compute_nice_scale,
    compute_nice_time_scale_hours,
    estimate_max_ticks,
    format_number_tick,
    format_time_tick_hours,
)


class TestEstimateMaxTicks:
    def test_label_size_zero_returns_max(self):
        assert estimate_max_ticks(200, 0) == 12
        assert estimate_max_ticks(200, -1) == 12

    def test_respects_bounds(self):
        assert estimate_max_ticks(10, 100, min_ticks=2, max_ticks=12) == 2
        assert estimate_max_ticks(10_000, 10, min_ticks=2, max_ticks=12) == 12

    def test_reasonable_middle_value(self):
        assert estimate_max_ticks(120, 30, min_ticks=2, max_ticks=12) == 4


class TestComputeNiceScale:
    def test_degenerate_range_is_padded(self):
        s = compute_nice_scale(5, 5, max_ticks=6)
        assert isinstance(s, NiceScale)
        assert s.axis_min < 5 < s.axis_max
        assert s.step > 0
        assert len(s.ticks()) == s.divisions + 1

    def test_include_zero_expands_domain(self):
        s = compute_nice_scale(10, 11, max_ticks=5, include_zero=True)
        assert s.axis_min <= 0.0 <= s.axis_max

    def test_covers_data_and_tick_budget(self):
        data_min, data_max = -3.2, 9.7
        max_ticks = 7
        s = compute_nice_scale(data_min, data_max, max_ticks=max_ticks)
        assert s.axis_min <= data_min
        assert s.axis_max >= data_max
        assert len(s.ticks()) <= max_ticks

    def test_ticks_are_monotonic(self):
        s = compute_nice_scale(0.1, 0.9, max_ticks=6)
        ticks = s.ticks()
        assert ticks == sorted(ticks)
        assert all(ticks[i + 1] > ticks[i] for i in range(len(ticks) - 1))


class TestComputeNiceTimeScaleHours:
    def test_step_is_positive_and_integer_hours(self):
        s = compute_nice_time_scale_hours(0.0, 7.0, max_ticks=6)
        assert s.step > 0
        assert abs(s.step - round(s.step)) < 1e-9

    def test_tick_budget_is_respected(self):
        s = compute_nice_time_scale_hours(0.0, 24.0 * 10.0, max_ticks=6)  # 10 days
        assert len(s.ticks()) <= 6

    def test_degenerate_range_is_extended(self):
        s = compute_nice_time_scale_hours(12.0, 12.0, max_ticks=4)
        assert s.axis_max > s.axis_min
        assert s.step > 0


class TestFormatTimeTickHours:
    def test_formats_hours_and_days(self):
        assert format_time_tick_hours(0.0) == "00:00\n0d"
        assert format_time_tick_hours(25.0) == "01:00\n1d"

    def test_rounds_minutes_when_step_has_minutes(self):
        assert format_time_tick_hours(1.5, step_hours=2.4).startswith("01:30")


class TestFormatNumberTick:
    @pytest.mark.parametrize(
        "value, step, expected",
        [
            (10.2, 5.0, "10"),         
            (1.234, 0.1, "1.2"),       
            (1.234, 0.01, "1.23"),     
            (1.23456, 0.0001, "1.2346"),  
        ],
    )
    def test_formats_reasonably(self, value, step, expected):
        assert format_number_tick(value, step) == expected

    def test_step_zero_falls_back_to_str(self):
        assert format_number_tick(1.234, 0.0) == "1.234"

    def test_non_finite_step_falls_back_to_str(self):
        assert format_number_tick(1.234, float("inf")) == "1.234"
        assert format_number_tick(1.234, float("nan")) == "1.234"

