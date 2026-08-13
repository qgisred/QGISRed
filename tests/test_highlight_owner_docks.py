# -*- coding: utf-8 -*-
"""The docks compose with the highlight mixins.

Mixing a plain-Python class in before a Qt base is fragile under the mocked Qt
of the test suite: if the widget base degrades to a MagicMock instance, building
the class raises "metaclass conflict" at *import* time. Importing every dock
that uses a mixin turns that into a failing test instead of a surprise at
runtime — the query docks are otherwise not imported anywhere in the suite.
"""
import pytest

from qgis.PyQt.QtCore import QEvent

from QGISRed.tools.utils.qgisred_highlight_manager import (
    _ACTIVATION_EVENTS,
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


@pytest.mark.parametrize("module_path,class_name", OWNER_DOCKS + ACTIVATION_DOCKS)
def test_every_dock_watches_activation_over_its_whole_window(module_path, class_name):
    """Wiring the mixin is not enough: watchDockActivation() has to be called.

    Without it only the widgets that happen to take the keyboard focus report
    the user turning to the panel, which is how "the highlights only swap when
    I click inside the chart" happened.
    """
    import importlib
    import inspect

    source = inspect.getsource(importlib.import_module(module_path))

    assert "watchDockActivation()" in source


class _FakeDockBase:
    """Stands in for QDockWidget: the mixins chain up to it."""

    def eventFilter(self, obj, event):
        return False


class _FakeDock(QGISRedDockActivationMixin, _FakeDockBase):
    def __init__(self):
        self.activations = 0

    def emitActivated(self):
        self.activations += 1


class _FakeEvent:
    def __init__(self, event_type):
        self._type = event_type

    def type(self):
        return self._type


def test_a_press_on_any_child_widget_activates_the_dock():
    dock = _FakeDock()

    # The child, not the dock, is what Qt delivers the press to.
    dock.eventFilter(object(), _FakeEvent(QEvent.Type.MouseButtonPress))

    assert dock.activations == 1


def test_a_tab_becoming_the_current_one_activates_the_dock():
    """Tabbed docks are re-stacked, never hidden and shown, so showEvent is
    silent and visibilityChanged is the only report of the tab change."""
    dock = _FakeDock()

    dock._onActivationVisibilityChanged(True)

    assert dock.activations == 1


def test_dropping_behind_another_panel_does_not_activate_the_dock():
    dock = _FakeDock()

    dock._onActivationVisibilityChanged(False)

    assert dock.activations == 0


def test_returning_to_qgis_does_not_activate_every_panel_at_once():
    # WindowActivate reaches every widget of the window, so honouring it would
    # let the last dock to receive it win the canvas by accident.
    assert QEvent.Type.WindowActivate not in _ACTIVATION_EVENTS
    assert QEvent.Type.MouseButtonPress in _ACTIVATION_EVENTS
    assert QEvent.Type.NonClientAreaMouseButtonPress in _ACTIVATION_EVENTS
    assert QEvent.Type.FocusIn in _ACTIVATION_EVENTS
