# -*- coding: utf-8 -*-
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def section():
    from QGISRed.sections.analysis_section import AnalysisSection

    s = AnalysisSection.__new__(AnalysisSection)
    s.iface = MagicMock()
    s.myMapTools = {}
    s.timeSeriesButton = MagicMock()
    s.timeSeriesDocks = [MagicMock(), MagicMock()]
    s._activeTimeSeriesDock = s.timeSeriesDocks[0]
    return s


def test_deleting_on_close_removes_the_chart_and_keeps_the_others(section):
    closing, other = section.timeSeriesDocks
    other.visibleRegion.return_value.isEmpty.return_value = False
    section._askTimeSeriesCloseChoice = MagicMock(return_value="delete")

    assert section._onTimeSeriesDockCloseRequested(closing) is True

    assert section.timeSeriesDocks == [other]
    assert section.activeTimeSeriesDock is other
    closing.deleteLater.assert_called_once()
    other.deleteLater.assert_not_called()


def test_keeping_on_close_leaves_the_chart_available_and_cancel_aborts(section):
    closing = section.timeSeriesDocks[0]

    section._askTimeSeriesCloseChoice = MagicMock(return_value="keep")
    assert section._onTimeSeriesDockCloseRequested(closing) is True
    section._askTimeSeriesCloseChoice = MagicMock(return_value="cancel")
    assert section._onTimeSeriesDockCloseRequested(closing) is False

    assert closing in section.timeSeriesDocks
    closing.deleteLater.assert_not_called()
