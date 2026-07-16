# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.qgisred_profile_dock import (
    PROFILE_VARIABLES,
    PROFILE_SECONDARY_VARIABLE_KEYS,
    secondary_variable_keys,
)


def _keys():
    return [key for _display, key in PROFILE_VARIABLES]


def _display_of(wanted):
    return next(display for display, key in PROFILE_VARIABLES if key == wanted)


def test_head_option_mentions_elevation():
    assert _display_of("Head") == "Head + Elevation"


def test_head_loss_comes_before_quality():
    keys = _keys()
    assert keys.index("HeadLoss") < keys.index("Quality")


def test_primary_offers_every_variable():
    assert _keys() == ["Elevation", "Head", "Pressure", "HeadLoss", "Quality"]


def test_secondary_never_offers_elevation_or_head():
    for primary in _keys():
        offered = secondary_variable_keys(primary)
        assert "Elevation" not in offered
        assert "Head" not in offered


def test_secondary_excludes_the_primary():
    assert "Pressure" not in secondary_variable_keys("Pressure")
    assert "Quality" not in secondary_variable_keys("Quality")
    assert "HeadLoss" not in secondary_variable_keys("HeadLoss")


def test_secondary_with_head_primary_keeps_all_allowed():
    assert secondary_variable_keys("Head") == ["Pressure", "HeadLoss", "Quality"]


def test_secondary_with_pressure_primary_drops_pressure():
    assert secondary_variable_keys("Pressure") == ["HeadLoss", "Quality"]


def test_secondary_keeps_primary_combo_order():
    assert secondary_variable_keys("Elevation") == list(PROFILE_SECONDARY_VARIABLE_KEYS)
