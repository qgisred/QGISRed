# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def section(monkeypatch):
    from QGISRed.sections import analysis_section

    monkeypatch.setattr(analysis_section, "QGISRedTimeSeriesDock", lambda iface: MagicMock())
    s = analysis_section.AnalysisSection.__new__(analysis_section.AnalysisSection)
    s.iface = MagicMock()
    s.ResultDockwidget = None
    s._registerTimeSeriesHighlightOwner = MagicMock()
    return s


def _anchor(floating=False):
    anchor = MagicMock()
    anchor.isFloating.return_value = floating
    return anchor


def test_new_chart_is_tabified_without_being_added_beside_the_anchor(section):
    anchor = _anchor()

    dock = section._createTimeSeriesDock(tabifyWith=anchor)

    section.iface.mainWindow.return_value.tabifyDockWidget.assert_called_once_with(anchor, dock)
    section.iface.addDockWidget.assert_not_called()


def test_first_chart_is_added_to_the_bottom_area(section):
    section._createTimeSeriesDock()

    section.iface.addDockWidget.assert_called_once()
    section.iface.mainWindow.return_value.tabifyDockWidget.assert_not_called()


def test_floating_anchor_falls_back_to_the_bottom_area(section):
    section._createTimeSeriesDock(tabifyWith=_anchor(floating=True))

    section.iface.addDockWidget.assert_called_once()
    section.iface.mainWindow.return_value.tabifyDockWidget.assert_not_called()
