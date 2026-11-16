# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock

import pytest

_LIB_NAMES = {"win32": "GISRed.QGISRed.dll", "darwin": "GISRed.QGISRed.dylib", "linux": "GISRed.QGISRed.so"}


@pytest.fixture
def make_section():
    # Imported here, not at module level: importing the sections package at collection time
    # breaks the stubs other test modules install. The fixture also runs before the test
    # fakes sys.platform, which urllib.request reads on its first import.
    from QGISRed.sections.lifecycle_section import LifecycleSection

    def _make(installed_version="1.0.0.0", required_version="1.0.0.0"):
        section = object.__new__(LifecycleSection)
        section.iface = MagicMock()
        section.DependenciesVersion = required_version
        section.tr = lambda text: text
        section.getVersion = MagicMock(return_value=installed_version)
        return section

    return _make


@pytest.mark.parametrize("os_name", sorted(_LIB_NAMES))
class TestDependenciesInstalled:
    def test_missing_library_is_not_installed(self, os_name, make_section, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "platform", os_name)
        assert make_section()._dependenciesInstalled(str(tmp_path)) is False

    def test_same_version_is_installed(self, os_name, make_section, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "platform", os_name)
        (tmp_path / _LIB_NAMES[os_name]).write_bytes(b"")
        assert make_section("1.0.19.1", "1.0.19.1")._dependenciesInstalled(str(tmp_path)) is True

    def test_older_version_is_not_installed(self, os_name, make_section, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "platform", os_name)
        (tmp_path / _LIB_NAMES[os_name]).write_bytes(b"")
        assert make_section("1.0.18.1", "1.0.19.1")._dependenciesInstalled(str(tmp_path)) is False

