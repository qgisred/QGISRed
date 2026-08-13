# -*- coding: utf-8 -*-
"""A panel the user clicks becomes the current one even with nothing to draw.

canActivate() stops a dock that has nothing to show from taking the canvas away from one
that is using it. It was also swallowing the user's own clicks: an Element Explorer opened
but with no element identified yet could never become the current panel, so its title
stayed grey and its identify tool was never re-armed. Clicking now overrules it; a dock
merely re-shown by a layout change still does not.
"""
from QGISRed.tools.utils.qgisred_highlight_manager import (
    QGISRedHighlightManager,
    QGISRedHighlightOwnerMixin,
)


class _Base:
    """Stands in for QDockWidget."""

    def focusInEvent(self, event):
        pass

    def mousePressEvent(self, event):
        pass

    def showEvent(self, event):
        pass


class _EmptyDock(QGISRedHighlightOwnerMixin, _Base):
    """Nothing identified yet, so nothing to put back on the map."""

    highlightOwnerKey = "elementExplorer"

    def __init__(self):
        self.restored = 0
        self.accent = None

    def highlightWidget(self):
        return None

    def canActivate(self):
        return False

    def redrawMapHighlights(self):
        self.restored += 1

    def applyHighlightAccent(self, isActive):
        self.accent = isActive


class _BusyDock(QGISRedHighlightOwnerMixin, _Base):
    """A chart with series on the map."""

    highlightOwnerKey = "timeseries"

    def __init__(self):
        self.drawn = True
        self.accent = True

    def highlightWidget(self):
        return None

    def clearMapHighlights(self):
        self.drawn = False

    def applyHighlightAccent(self, isActive):
        self.accent = isActive


def _world():
    manager = QGISRedHighlightManager()
    manager._connectSignals = lambda: None
    empty, busy = _EmptyDock(), _BusyDock()
    manager.register(empty)
    manager.register(busy)
    manager.activate(busy)
    return manager, empty, busy


def test_clicking_an_empty_panel_makes_it_the_current_one():
    manager, empty, busy = _world()

    empty.mousePressEvent(None)

    assert manager.activeOwner() is empty
    assert empty.accent is True
    assert busy.accent is False
    assert busy.drawn is False   # the map empties, as agreed


def test_a_layout_change_does_not_let_an_empty_panel_take_the_canvas():
    """Why the guard is still there: re-docking a panel is not the user turning to it."""
    manager, empty, busy = _world()

    empty.showEvent(None)

    assert manager.activeOwner() is busy
    assert busy.drawn is True
