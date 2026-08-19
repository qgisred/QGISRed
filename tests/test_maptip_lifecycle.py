# -*- coding: utf-8 -*-
"""Letting go of the canvas when the tip is stopped.

The tip filters events on the map canvas and on every child QGIS builds under it. Those
widgets outlive the plugin, so a filter left installed on one of them keeps calling back
into an instance whose QLabel has already been destroyed — and restoring a minimised QGIS
window sends a show event to all of them at once, which is where it used to blow up with
"wrapped C/C++ object of type QLabel has been deleted".
"""
import importlib
import sys

from .conftest import REAL_QGIS
from unittest.mock import MagicMock, patch


class _QObjectStub:
    """`class QGISRedMapTip(QObject)` needs a real type as base, not the mocked module
    attribute — otherwise the class statement yields something that cannot be built."""

    def __init__(self, *args, **kwargs):
        pass


if not REAL_QGIS:
    # Replacing the real QObject would leave every module imported afterwards with
    # a stub base class.
    sys.modules["qgis.PyQt.QtCore"].QObject = _QObjectStub

_MODULE = "QGISRed.tools.utils.qgisred_maptip."
QGISRedMapTip = importlib.reload(importlib.import_module(_MODULE.rstrip("."))).QGISRedMapTip


class _FakeSip:
    @staticmethod
    def isdeleted(obj):
        return getattr(obj, "deleted", False)


class _FakeLabel:
    """A QLabel wrapper that raises like PyQt once the C++ object is gone."""

    def __init__(self):
        self.deleted = False

    def _check(self):
        if self.deleted:
            raise RuntimeError("wrapped C/C++ object of type QLabel has been deleted")

    def isVisible(self):
        self._check()
        return True

    def hide(self):
        self._check()

    def deleteLater(self):
        self.deleted = True


class _FakeWidget:
    def __init__(self):
        self.filters = []
        self.deleted = False

    def isWidgetType(self):
        return True

    def installEventFilter(self, obj):
        self.filters.append(obj)

    def removeEventFilter(self, obj):
        if obj in self.filters:
            self.filters.remove(obj)


def _tip(watched=()):
    """An instance in the state __init__ leaves it in, without building any Qt object."""
    tip = QGISRedMapTip.__new__(QGISRedMapTip)
    tip._iface = MagicMock()
    tip._hoverPoint = None
    tip._label = _FakeLabel()
    tip._showTimer = MagicMock()
    tip._hideTimer = MagicMock()
    tip._watched = []
    for widget in watched:
        tip._watch(widget)
    return tip


def _showEvent():
    event = MagicMock()
    event.type.return_value = "Show"
    return event


class TestWatching:
    def test_watched_widgets_are_remembered(self):
        widget = _FakeWidget()
        tip = _tip([widget])
        assert widget.filters == [tip] and tip._watched == [widget]

    def test_the_same_widget_is_only_recorded_once(self):
        """ChildAdded can fire for a widget the initial sweep already picked up."""
        widget = _FakeWidget()
        tip = _tip([widget, widget])
        assert tip._watched == [widget]


class TestStop:
    def test_filters_are_removed_from_every_watched_widget(self):
        widgets = [_FakeWidget(), _FakeWidget()]
        tip = _tip(widgets)
        with patch(_MODULE + "sip", _FakeSip):
            tip.stop()
        assert all(not widget.filters for widget in widgets)
        assert tip._watched == []

    def test_a_widget_already_destroyed_is_skipped(self):
        alive, dead = _FakeWidget(), _FakeWidget()
        tip = _tip([dead, alive])
        dead.deleted = True
        with patch(_MODULE + "sip", _FakeSip):
            tip.stop()
        assert dead.filters == [tip] and not alive.filters

    def test_a_failing_disconnect_still_releases_the_widgets(self):
        """One guard per step: the removals must not hang off an earlier failure."""
        widget = _FakeWidget()
        tip = _tip([widget])
        tip._iface.mapCanvas().xyCoordinates.disconnect.side_effect = TypeError("not connected")
        with patch(_MODULE + "sip", _FakeSip):
            tip.stop()
        assert not widget.filters


class TestEventsAfterStop:
    def test_a_show_event_after_stop_is_ignored(self):
        """What minimising and restoring the window delivers to a stale filter."""
        widget = _FakeWidget()
        tip = _tip([widget])
        with patch(_MODULE + "sip", _FakeSip):
            tip.stop()
            assert tip.eventFilter(widget, _showEvent()) is False

    def test_a_label_destroyed_behind_our_back_is_not_touched(self):
        """stop() drops the reference, but Qt can destroy the widget on its own."""
        widget = _FakeWidget()
        tip = _tip([widget])
        tip._label.deleted = True
        with patch(_MODULE + "sip", _FakeSip):
            assert tip.eventFilter(widget, _showEvent()) is False
            tip._hideLabel()          # must not raise either
            tip._onMove(MagicMock())
            tip._query()
