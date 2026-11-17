# -*- coding: utf-8 -*-
import os
import sys
import types
from unittest.mock import MagicMock

import pytest

import QGISRed

if "QGISRed.sections" not in sys.modules:
    _pkg = types.ModuleType("QGISRed.sections")
    _pkg.__path__ = [os.path.join(os.path.dirname(QGISRed.__file__), "sections")]
    sys.modules["QGISRed.sections"] = _pkg

from QGISRed.sections.profile_section import ProfileSection, ProfileState


class _Dummy(ProfileSection):
    pass


def _panel(section):
    state = ProfileState()
    state.reference_nodes = ["N1", "N2"]
    state.dock = MagicMock()
    state.dock._state = state
    state.dock.visibleRegion.return_value.isEmpty.return_value = False
    section._profiles.append(state)
    return state


@pytest.fixture
def section():
    s = _Dummy()
    s.iface = MagicMock()
    s.myMapTools = {}
    s._profiles = []
    s._restyleProfileDocks = MagicMock()
    s._clearProfileMapHover = MagicMock()
    s._rearmProfileMapTool = MagicMock()
    closing, other = _panel(s), _panel(s)
    s._activeProfile = closing
    return s, closing, other


def test_deleting_on_close_removes_the_profile_and_keeps_the_others(section):
    s, closing, other = section
    s._askChartCloseChoice = MagicMock(return_value="delete")

    assert s._onProfileDockCloseRequested(closing.dock) is True

    assert s._profiles == [other]
    assert s._activeProfile is other
    closing.dock.deleteLater.assert_called_once()
    other.dock.deleteLater.assert_not_called()


def test_keeping_on_close_leaves_the_profile_available_and_cancel_aborts(section):
    s, closing, _other = section

    s._askChartCloseChoice = MagicMock(return_value="keep")
    assert s._onProfileDockCloseRequested(closing.dock) is True
    s._askChartCloseChoice = MagicMock(return_value="cancel")
    assert s._onProfileDockCloseRequested(closing.dock) is False

    assert closing in s._profiles
    closing.dock.deleteLater.assert_not_called()
