# -*- coding: utf-8 -*-
import os
import sys
import types

import QGISRed

# sections/__init__.py pulls in the Windows-only DLL bridge at import time, so
# stub the package and load profile_section on its own (pure Python).
if "QGISRed.sections" not in sys.modules:
    _pkg = types.ModuleType("QGISRed.sections")
    _pkg.__path__ = [os.path.join(os.path.dirname(QGISRed.__file__), "sections")]
    sys.modules["QGISRed.sections"] = _pkg

from QGISRed.sections.profile_section import ProfileSection, ProfileState


class _Dummy(ProfileSection):
    pass


def test_defaults_when_no_active_profile():
    d = _Dummy()
    d._activeProfile = None
    assert d._profileReferenceNodes == []
    assert d._profileBranches == []
    assert d._profilePath is None
    assert d._profileShowSymbols is False
    assert d._profileEnvelopeMode == "off"
    assert d._profileReportStep == 3600


def test_proxy_reads_and_writes_active_state():
    d = _Dummy()
    state = ProfileState()
    d._activeProfile = state
    d._profileReferenceNodes = ["N1", "N2"]
    d._profileShowSymbols = True
    d._profileEnvelopeMode = "band"
    assert state.reference_nodes == ["N1", "N2"]
    assert state.show_symbols is True
    assert state.envelope_mode == "band"
    assert d._profileReferenceNodes == ["N1", "N2"]


def test_two_states_are_independent():
    d = _Dummy()
    a = ProfileState()
    b = ProfileState()

    d._activeProfile = a
    d._profileReferenceNodes = ["A1"]
    d._profileEnvelopeMode = "lines"

    d._activeProfile = b
    d._profileReferenceNodes = ["B1", "B2"]

    assert a.reference_nodes == ["A1"]
    assert a.envelope_mode == "lines"
    assert b.reference_nodes == ["B1", "B2"]
    assert b.envelope_mode == "off"

    d._activeProfile = a
    assert d._profileReferenceNodes == ["A1"]


def test_setter_noop_when_no_active():
    d = _Dummy()
    d._activeProfile = None
    d._profileReferenceNodes = ["X"]
    assert d._profileReferenceNodes == []
