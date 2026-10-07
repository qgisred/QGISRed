# -*- coding: utf-8 -*-
"""Resolution order of QML style files: project (network-prefixed) → global → default."""
import os

import pytest

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils


class _FakeLayer:
    """Records the style path it was asked to load and the label visibility; everything else is a no-op."""

    def __init__(self, fileShowsLabels=False):
        self.loadedPath = None
        self.fileShowsLabels = fileShowsLabels
        self.labelsShown = None

    def loadNamedStyle(self, path):
        self.loadedPath = path
        # What a real load reads from the file
        self.labelsShown = self.fileShowsLabels

    def setLabelsEnabled(self, enabled):
        self.labelsShown = enabled

    def labelsEnabled(self):
        return self.labelsShown

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

    def test_a_variant_is_added_as_a_suffix(self, tmp_path):
        utils = _makeUtils(tmp_path)
        assert utils.projectStyleFileNames("TreeLinks.qml", "J5_Union") == [
            "Net_TreeLinks_J5_Union.qml", "TreeLinks_J5_Union.qml"]


class TestPerTreeProjectStyle:
    """Every tree shares one identifier, so its project style is told apart by the tree name."""

    def test_a_tree_loads_its_own_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Net_TreeLinks_J5_Union.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Tree_Links", variant="J5_Union")

        assert layer.loadedPath == expected

    def test_a_tree_ignores_the_style_of_another_tree(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        _writeStyle(projectFolder, "Net_TreeLinks_J5_Union.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Tree_Links", variant="T12")

        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "TreeLinks.qml.bak"))

    def test_the_global_style_is_shared_by_every_tree(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _makeUtils(tmp_path, globalFolder=globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "TreeLinks.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "Tree_Links", variant="J5_Union")

        assert layer.loadedPath == expected


class TestPerThemeProjectStyle:
    """Demand Builder themes of one type share one identifier, so the theme name tells their project styles apart."""

    def test_a_theme_loads_its_own_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Net_DemandBuilderConsumptionPoints_Padron.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "DemandBuilder_ConsumptionPoints", variant="Padron")

        assert layer.loadedPath == expected

    def test_a_theme_ignores_the_style_of_another_theme(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        _writeStyle(projectFolder, "Net_DemandBuilderConsumptionPoints_Padron.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "DemandBuilder_ConsumptionPoints", variant="Censo")

        assert layer.loadedPath.endswith(
            os.path.join("defaults", "layerStyles", "DemandBuilderConsumptionPoints.qml.bak"))

    def test_an_unnamed_theme_takes_the_plain_project_style(self, tmp_path):
        utils = _makeUtils(tmp_path)
        projectFolder = os.path.join(str(tmp_path / "project"), "layerStyles")
        expected = _writeStyle(projectFolder, "Net_DemandBuilderConsumptionPoints.qml")

        layer = _FakeLayer()
        utils.setStyle(layer, "DemandBuilder_ConsumptionPoints", variant="")

        assert layer.loadedPath == expected


class TestLabelVisibility:
    """Loading a style hides the labels, unless the caller asks to keep what the file says."""

    def test_labels_are_hidden_by_default(self, tmp_path):
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer(fileShowsLabels=True)

        utils.setStyle(layer, "Pipes")

        assert layer.labelsShown is False

    @pytest.mark.parametrize("fileShowsLabels", [True, False])
    def test_the_file_decides_when_asked(self, tmp_path, fileShowsLabels):
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer(fileShowsLabels=fileShowsLabels)

        utils.setStyle(layer, "Pipes", keepLabelVisibility=True)

        assert layer.labelsShown is fileShowsLabels


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

        utils.setStyle(layer, "Node_PressureSI")

        # Underscores are stripped from the style name, and defaults live as .qml.bak.
        assert layer.loadedPath.endswith(os.path.join("defaults", "layerStyles", "NodePressureSI.qml.bak"))
        assert os.path.exists(layer.loadedPath)

    @pytest.mark.parametrize("name", [
        "NodePressureSI", "NodePressureUS", "NodeHead", "NodeDemand", "NodeChlorine", "NodeChemical", "NodeTrace",
        "NodeAge", "LinkFlow", "LinkVelocitySI", "LinkVelocityUS", "LinkHeadLossSI", "LinkHeadLossUS",
        "LinkUnitHdLoss", "LinkFricFactor", "LinkReactRate", "LinkChlorine", "LinkChemical", "LinkTrace", "LinkAge",
        "LinkStatus",
    ])
    def test_every_result_style_the_dock_can_ask_for_ships(self, tmp_path, name):
        # The fallback path is built whether or not the file exists, so its presence is checked here.
        utils = _makeUtils(tmp_path)
        layer = _FakeLayer()

        utils.setStyle(layer, name)

        assert os.path.exists(layer.loadedPath), layer.loadedPath

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
