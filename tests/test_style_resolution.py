# -*- coding: utf-8 -*-
"""Resolution order of QML style files: project (network-prefixed) → global → default."""
import os

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils


class _FakeLayer:
    """Records the style path it was asked to load; everything else is a no-op."""

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


def _makeUtils(tmp_path, networkName="Net", globalFolder=None):
    utils = QGISRedStylingUtils(str(tmp_path / "project"), networkName)
    globalFolder = globalFolder if globalFolder is not None else str(tmp_path / "global")
    utils._getQGISRedFolder = lambda: globalFolder
    return utils


def _writeStyle(folder, fileName):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<qgis></qgis>")
    return path


class TestProjectStyleFileNames:
    def test_prefixed_name_comes_first(self, tmp_path):
        utils = _makeUtils(tmp_path)
        assert utils.projectStyleFileNames("Pipes.qml") == ["Net_Pipes.qml", "Pipes.qml"]

    def test_network_name_with_underscore_is_not_stripped(self, tmp_path):
        utils = _makeUtils(tmp_path, networkName="Red_Norte")
        assert utils.projectStyleFileNames("Pipes.qml")[0] == "Red_Norte_Pipes.qml"

    def test_without_network_name_only_the_bare_name(self, tmp_path):
        utils = _makeUtils(tmp_path, networkName="")
        assert utils.projectStyleFileNames("Pipes.qml") == ["Pipes.qml"]


class TestSetStyle:
    def test_prefers_network_prefixed_project_style(self, tmp_path):
        # This is what the legend editor writes (getProjectStyleFilename).
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Net_Pipes.qml")
        _writeStyle(projectFolder, "Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_falls_back_to_unprefixed_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_global_style_is_never_prefixed(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _makeUtils(tmp_path, globalFolder=globalFolder)
        _writeStyle(os.path.join(globalFolder, "layerStyles"), "Net_Pipes.qml")
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_project_style_wins_over_global(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _makeUtils(tmp_path, globalFolder=globalFolder)
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml")
        _writeStyle(os.path.join(globalFolder, "layerStyles"), "Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_falls_back_to_plugin_default(self, tmp_path):
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer()

        utils.setStyle(layer, "Node_Pressure")

        # Underscores are stripped from the style name, and defaults live as .qml.bak.
        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "NodePressure.qml.bak"))

    def test_empty_name_loads_nothing(self, tmp_path):
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer()

        utils.setStyle(layer, "")

        assert layer.loadedPath is None

    def test_style_name_case_does_not_matter(self, tmp_path):
        # openLayer passes input layer names in lowercase ("pipes"), while the legend
        # editor and the shipped defaults capitalise them.
        utils = _makeUtils(tmp_path)
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"), "Net_Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "pipes")

        assert layer.loadedPath == expected

    def test_network_name_case_does_not_matter(self, tmp_path):
        utils = _makeUtils(tmp_path, networkName="NET")
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"), "net_Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Pipes")

        assert layer.loadedPath == expected

    def test_global_style_matches_case_insensitively(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _makeUtils(tmp_path, globalFolder=globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "Pipes.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "pipes")

        assert layer.loadedPath == expected

    def test_missing_default_still_attempts_the_expected_path(self, tmp_path):
        # Result layers are opened as "Base_Node", for which no default QML exists;
        # the call must stay harmless rather than change shape.
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer()

        utils.setStyle(layer, "Base_Node")

        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "BaseNode.qml.bak"))


class TestResolveStylePath:
    def test_prefers_network_prefixed_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Net_pipe_roughness.qml")
        _writeStyle(projectFolder, "pipe_roughness.qml")

        assert utils.resolveStylePath("pipe_roughness.qml") == expected

    def test_falls_back_to_unprefixed_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "pipe_roughness.qml")

        assert utils.resolveStylePath("pipe_roughness.qml") == expected

    def test_falls_back_to_plugin_default(self, tmp_path):
        utils = _makeUtils(tmp_path)

        resolved = utils.resolveStylePath("pipe_roughness.qml")

        assert resolved.endswith(os.path.join("defaults", "layerStyles", "pipe_roughness.qml.bak"))
