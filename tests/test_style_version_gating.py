# -*- coding: utf-8 -*-
"""A project/global .qml stamped older than a family's forced minimum is ignored.

qgisred_style_version is the per-.qml stamp (QGISRedStylingUtils.stampStyleVersion);
_FORCED_STYLE_RESET is the per-family minimum below which setStyle/setSavedStyle/
resolveStylePath treat a saved style as if it didn't exist. The table ships empty, so
every test here installs its own entries via monkeypatch.
"""
import os

import pytest

from QGISRed.tools.utils import qgisred_styling_utils
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils


class _FakeLayer:
    def __init__(self):
        self.loadedPath = None

    def loadNamedStyle(self, path):
        self.loadedPath = path

    def setLabelsEnabled(self, enabled):
        pass

    def customProperty(self, name):
        return None

    def renderer(self):
        return None

    def mapTipTemplate(self):
        return ""

    def labeling(self):
        return None

    def setMapTipTemplate(self, template):
        pass


def _styling(tmp_path, networkName="Net", globalFolder=None):
    utils = QGISRedStylingUtils(str(tmp_path / "project"), networkName)
    utils._getQGISRedFolder = lambda: globalFolder or str(tmp_path / "global")
    return utils


def _writeStyle(folder, fileName):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<qgis></qgis>")
    return path


def _writeStyleWithVersion(folder, fileName, version):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(
            '<qgis>'
            '<customproperties>'
            '<Option type="Map">'
            '<Option name="qgisred_style_version" value="%s" type="QString"/>'
            '</Option>'
            '</customproperties>'
            '</qgis>' % version
        )
    return path


@pytest.fixture(autouse=True)
def _emptyForcedResetTable(monkeypatch):
    """Every test installs its own entries; nothing should leak between tests."""
    monkeypatch.setattr(qgisred_styling_utils, "_FORCED_STYLE_RESET", {})


class TestVersionCompare:
    @pytest.mark.parametrize("a, b, expected", [
        ("0.9", "0.10", -1),
        ("0.10", "0.9", 1),
        ("0.21", "0.21.0", 0),
        ("0.21.0", "0.21", 0),
        ("1.0.0", "1.0.0", 0),
        ("0.0.0", "0.1.0", -1),
        ("", "0.0.0", 0),
        ("0.9.3", "0.9", 1),
    ])
    def test_numeric_comparison(self, a, b, expected):
        assert QGISRedStylingUtils._compareVersions(a, b) == expected

    def test_garbage_segments_parse_as_zero(self):
        assert QGISRedStylingUtils._parseVersionTuple("0.x.1") == (0, 0, 1)
        assert QGISRedStylingUtils._parseVersionTuple("") == (0,)
        assert QGISRedStylingUtils._parseVersionTuple(None) == (0,)


class TestReadStyleVersion:
    def test_missing_stamp_reads_as_zero(self, tmp_path):
        path = _writeStyle(str(tmp_path), "Plain.qml")
        assert QGISRedStylingUtils._readStyleVersion(path) == "0.0.0"

    def test_stamped_version_is_read_back(self, tmp_path):
        path = _writeStyleWithVersion(str(tmp_path), "Stamped.qml", "0.21.0")
        assert QGISRedStylingUtils._readStyleVersion(path) == "0.21.0"

    def test_missing_file_reads_as_zero(self, tmp_path):
        missing = str(tmp_path / "Nowhere.qml")
        assert QGISRedStylingUtils._readStyleVersion(missing) == "0.0.0"


class TestForcedStyleResetOnSetStyle:
    def test_obsolete_project_style_falls_through_to_global(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipes", "0.21.0")
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        _writeStyleWithVersion(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml", "0.20.0")
        expected = _writeStyleWithVersion(os.path.join(globalFolder, "layerStyles"), "Pipes.qml", "0.21.0")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_both_obsolete_falls_through_to_factory_default(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipes", "0.21.0")
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        _writeStyleWithVersion(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml", "0.20.0")
        _writeStyleWithVersion(os.path.join(globalFolder, "layerStyles"), "Pipes.qml", "0.1.0")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "Pipes.qml.bak"))

    def test_style_at_the_floor_still_loads(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipes", "0.21.0")
        utils = _styling(tmp_path)
        expected = _writeStyleWithVersion(
            os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml", "0.21.0")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_unstamped_style_is_treated_as_legacy_and_forced(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipes", "0.21.0")
        utils = _styling(tmp_path)
        _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "Pipes.qml.bak"))

    def test_a_family_with_no_entry_is_never_gated(self, tmp_path):
        utils = _styling(tmp_path)
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected


class TestForcedStyleResetOnSetSavedStyle:
    def test_obsolete_project_style_falls_through_to_global(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "demandsectorslinks", "0.21.0")
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        _writeStyleWithVersion(
            os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_DemandSectorsLinks.qml", "0.20.0")
        expected = _writeStyleWithVersion(
            os.path.join(globalFolder, "layerStyles"), "DemandSectorsLinks.qml", "0.21.0")

        layer = _FakeLayer()
        assert utils.setSavedStyle(layer, "DemandSectors_Links") is True
        assert layer.loadedPath == expected

    def test_everything_obsolete_returns_false_instead_of_loading(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "demandsectorslinks", "0.21.0")
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        _writeStyleWithVersion(
            os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_DemandSectorsLinks.qml", "0.1.0")
        _writeStyleWithVersion(
            os.path.join(globalFolder, "layerStyles"), "DemandSectorsLinks.qml", "0.1.0")

        layer = _FakeLayer()
        assert utils.setSavedStyle(layer, "DemandSectors_Links") is False
        assert layer.loadedPath is None


class TestForcedStyleResetOnResolveStylePath:
    def test_obsolete_project_style_falls_through_to_default(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipe_roughness", "0.21.0")
        utils = _styling(tmp_path)
        _writeStyleWithVersion(
            os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_pipe_roughness.qml", "0.20.0")

        resolved = utils.resolveStylePath("pipe_roughness.qml")

        assert resolved.endswith(os.path.join("defaults", "layerStyles", "pipe_roughness.qml.bak"))

    def test_style_at_the_floor_still_resolves(self, tmp_path, monkeypatch):
        monkeypatch.setitem(qgisred_styling_utils._FORCED_STYLE_RESET, "pipe_roughness", "0.21.0")
        utils = _styling(tmp_path)
        expected = _writeStyleWithVersion(
            os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_pipe_roughness.qml", "0.21.0")

        resolved = utils.resolveStylePath("pipe_roughness.qml")

        assert resolved == expected
