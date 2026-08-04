# -*- coding: utf-8 -*-
"""The docks compose with the highlight mixins.

Mixing a plain-Python class in before a Qt base is fragile under the mocked Qt
of the test suite: if the widget base degrades to a MagicMock instance, building
the class raises "metaclass conflict" at *import* time. Importing every dock
that uses a mixin turns that into a failing test instead of a surprise at
runtime — the query docks are otherwise not imported anywhere in the suite.
"""
import pytest

from QGISRed.tools.utils.qgisred_highlight_manager import (
    QGISRedDockActivationMixin,
    QGISRedHighlightOwnerMixin,
)


def _dockClass(module_path, class_name):
    import importlib

    return getattr(importlib.import_module(module_path), class_name)


OWNER_DOCKS = [
    ("QGISRed.ui.queries.qgisred_element_explorer_dock", "QGISRedElementExplorerDock"),
    ("QGISRed.ui.queries.qgisred_queriesbyproperties_dock", "QGISRedQueriesByPropertiesDock"),
    ("QGISRed.ui.queries.qgisred_statisticsandgraphs_dock", "QGISRedStatisticsDock"),
]

ACTIVATION_DOCKS = [
    ("QGISRed.ui.analysis.qgisred_profile_dock", "QGISRedProfileDock"),
    ("QGISRed.ui.analysis.qgisred_timeseries_dock", "QGISRedTimeSeriesDock"),
]


@pytest.mark.parametrize("module_path,class_name", OWNER_DOCKS)
def test_owner_docks_carry_the_protocol(module_path, class_name):
    cls = _dockClass(module_path, class_name)

    assert QGISRedHighlightOwnerMixin in cls.__mro__
    # The mixin has to come first, or QDockWidget's own event handlers win and
    # the dock never reports that the user turned to it.
    assert cls.__mro__.index(QGISRedHighlightOwnerMixin) == 1
    assert cls.highlightOwnerKey != QGISRedHighlightOwnerMixin.highlightOwnerKey


@pytest.mark.parametrize("module_path,class_name", ACTIVATION_DOCKS)
def test_analysis_docks_carry_the_activation_mixin(module_path, class_name):
    cls = _dockClass(module_path, class_name)

    assert QGISRedDockActivationMixin in cls.__mro__
    assert cls.__mro__.index(QGISRedDockActivationMixin) == 1
    # The signal must stay declared on the dock itself: PyQt only registers
    # signals found on the class it is building, not on plain-Python bases.
    assert "activated" in vars(cls)


def test_every_owner_dock_uses_a_distinct_key():
    keys = [_dockClass(m, c).highlightOwnerKey for m, c in OWNER_DOCKS]

    assert len(set(keys)) == len(keys)
