# -*- coding: utf-8 -*-
"""Tool output layers find the styles the legend editor saves for them.

Connectivity, sectors, isolated segments, trees and Demand Builder keep their data in a
sub-folder of the project, and their layer utils is built on that sub-folder. The legend
editor saves project styles in the project root, so the lookup has to go there too, and
it has to ask for the same file name the editor writes.
"""
import os
from unittest.mock import MagicMock

import pytest

from QGISRed.tools.utils.qgisred_auxiliary_layers import AUXILIARY_LAYER_TYPES, composeBaseName
from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from QGISRed.tools.utils.qgisred_styling_utils import CONNECTIVITY_STYLE_NAME
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _writeStyle(folder, fileName):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<qgis></qgis>")
    return path


class _FakeLayer:
    def __init__(self, source=""):
        self.loadedPath = None
        self.layerSource = source
        self.repainted = False

    def loadNamedStyle(self, path):
        self.loadedPath = path

    def setLabelsEnabled(self, enabled):
        pass

    def labelsEnabled(self):
        return False

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

    def source(self):
        return self.layerSource

    def fields(self):
        return []

    def triggerRepaint(self):
        self.repainted = True


def _connectivityUtils(tmp_path, globalFolder):
    """Layer utils as openConnectivityLayer builds it, with a real style lookup behind it."""
    projectRoot = str(tmp_path / "project")
    subFolder = os.path.join(projectRoot, "Issues", "Connectivity")
    utils = QGISRedLayerUtils(subFolder, "Net", MagicMock(), projectRoot)
    styling = utils._styling()
    styling._getQGISRedFolder = lambda: globalFolder
    styling.fillCategoriesFromData = lambda layer, field: None
    return utils, styling, projectRoot


class TestProjectRoot:
    def test_it_defaults_to_the_layers_folder(self, tmp_path):
        utils = QGISRedLayerUtils(str(tmp_path), "Net", MagicMock())

        assert utils.ProjectRoot == str(tmp_path)
        assert utils._styling().ProjectDirectory == str(tmp_path)

    def test_styles_are_looked_up_in_the_root_not_in_the_sub_folder(self, tmp_path):
        subFolder = str(tmp_path / "Queries" / "Trees")
        utils = QGISRedLayerUtils(subFolder, "Net", MagicMock(), str(tmp_path))

        assert utils.LayersDirectory == subFolder
        assert utils._styling().ProjectDirectory == str(tmp_path)


class TestConnectivityStyleLookup:
    def test_the_project_style_saved_by_the_editor_is_loaded(self, tmp_path):
        utils, styling, projectRoot = _connectivityUtils(tmp_path, str(tmp_path / "global"))
        expected = _writeStyle(os.path.join(projectRoot, "layerStyles"), "Net_ConnectLinks.qml")
        layer = _FakeLayer()

        utils._applyConnectivityStyle(styling, layer, "Connectivity_Links")

        assert layer.loadedPath == expected

    def test_the_global_style_is_loaded_when_the_project_has_none(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils, styling, _ = _connectivityUtils(tmp_path, globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "ConnectLinks.qml")
        layer = _FakeLayer()

        utils._applyConnectivityStyle(styling, layer, "Connectivity_Links")

        assert layer.loadedPath == expected

    def test_the_shipped_default_is_loaded_when_nothing_is_saved(self, tmp_path):
        # It used to ask for ConnectivityLinks.qml.bak, which does not exist, so the layer
        # kept the default QGIS line instead of the shipped 0.6 mm one.
        utils, styling, _ = _connectivityUtils(tmp_path, str(tmp_path / "global"))
        layer = _FakeLayer()

        utils._applyConnectivityStyle(styling, layer, "Connectivity_Links")

        assert layer.loadedPath == os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", "ConnectLinks.qml.bak")
        assert os.path.exists(layer.loadedPath)

    def test_the_subnets_are_filled_in_after_the_style(self):
        styling = MagicMock()
        layer = MagicMock()

        QGISRedLayerUtils.__new__(QGISRedLayerUtils)._applyConnectivityStyle(styling, layer, "Connectivity_Links")

        styling.setStyle.assert_called_once_with(layer, CONNECTIVITY_STYLE_NAME)
        styling.fillCategoriesFromData.assert_called_once_with(layer, "SubNet")


class TestRuntimeAndEditorAskForTheSameFile:
    """The name openLayer passes to setStyle, reduced the way setStyle reduces it, must be
    the name the legend editor saves under — for every tool output family."""

    RUNTIME_NAMES = [
        ("qgisred_connectivity_links", CONNECTIVITY_STYLE_NAME),
        ("qgisred_hydraulicsectors_links", "HydraulicSectors_Links"),
        ("qgisred_hydraulicsectors_nodes", "HydraulicSectors_Nodes"),
        ("qgisred_hydraulicsectors_isolateddemands", "HydraulicSectors_IsolatedDemands"),
        ("qgisred_demandsectors_links", "DemandSectors_Links"),
        ("qgisred_demandsectors_nodes", "DemandSectors_Nodes"),
        ("qgisred_isolatedsegments_links", "isolatedsegments_links"),
        ("qgisred_isolatedsegments_nodes", "isolatedsegments_nodes"),
        ("qgisred_isolatedsegments_isolateddemands", "isolatedsegments_isolateddemands"),
        ("qgisred_tree_links", "Tree_Links"),
        ("qgisred_tree_nodes", "Tree_Nodes"),
        ("qgisred_demandbuilder_consumptionpoints", "DemandBuilder_ConsumptionPoints"),
        ("qgisred_demandbuilder_demandlinks", "DemandBuilder_DemandLinks"),
        ("qgisred_demandbuilder_sectors", "DemandBuilder_Sectors"),
    ]

    @pytest.mark.parametrize("identifier, runtimeName", RUNTIME_NAMES)
    def test_names_match(self, identifier, runtimeName):
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)

        editorName = dialog.getStyleNameForIdentifier(identifier)

        assert editorName.lower() == runtimeName.replace("_", "").lower()

    @pytest.mark.parametrize("layerType", AUXILIARY_LAYER_TYPES, ids=lambda layerType: layerType.key)
    def test_the_demand_builder_runtime_names_are_the_identifier_tokens(self, layerType):
        # setDemandBuilderStyle asks setStyle for the type's identifierToken
        assert (layerType.identifier, layerType.identifierToken) in self.RUNTIME_NAMES


def _demandBuilderUtils(tmp_path, globalFolder):
    """Layer utils as the Layer Manager builds it for the themes, with a real style lookup behind it."""
    projectRoot = str(tmp_path / "project")
    subFolder = os.path.join(projectRoot, "Auxiliary Layers", "DemandBuilder")
    utils = QGISRedLayerUtils(subFolder, "Net", MagicMock(), projectRoot)
    styling = utils._styling()
    styling._getQGISRedFolder = lambda: globalFolder
    return styling, subFolder, projectRoot


class TestDemandBuilderStyleLookup:
    """The themes of one type share its global and shipped style, and may each keep a project style."""

    def _theme(self, subFolder, fileName):
        return _FakeLayer(os.path.join(subFolder, fileName))

    def test_a_theme_loads_its_own_project_style(self, tmp_path):
        styling, subFolder, projectRoot = _demandBuilderUtils(tmp_path, str(tmp_path / "global"))
        expected = _writeStyle(os.path.join(projectRoot, "layerStyles"), "Net_DemandBuilderSectors_Barrios.qml")
        layer = self._theme(subFolder, "Net_DemandBuilder_Sectors_Barrios.shp")

        styling.setDemandBuilderStyle(layer, "Net_DemandBuilder_Sectors_Barrios")

        assert layer.loadedPath == expected

    def test_a_theme_ignores_the_project_style_of_another_theme(self, tmp_path):
        styling, subFolder, projectRoot = _demandBuilderUtils(tmp_path, str(tmp_path / "global"))
        _writeStyle(os.path.join(projectRoot, "layerStyles"), "Net_DemandBuilderSectors_Barrios.qml")
        layer = self._theme(subFolder, "Net_DemandBuilder_Sectors_Centro.shp")

        styling.setDemandBuilderStyle(layer, "Net_DemandBuilder_Sectors_Centro")

        assert layer.loadedPath == os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", "DemandBuilderSectors.qml.bak")
        assert os.path.exists(layer.loadedPath)

    def test_the_global_style_is_shared_by_every_theme(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        styling, subFolder, _ = _demandBuilderUtils(tmp_path, globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "DemandBuilderSectors.qml")
        first = self._theme(subFolder, "Net_DemandBuilder_Sectors_Barrios.shp")
        second = self._theme(subFolder, "Net_DemandBuilder_Sectors_Centro.shp")

        styling.setDemandBuilderStyle(first)
        styling.setDemandBuilderStyle(second)

        assert first.loadedPath == expected
        assert second.loadedPath == expected

    def test_the_file_the_editor_saves_is_the_file_the_theme_loads(self, tmp_path):
        styling, subFolder, projectRoot = _demandBuilderUtils(tmp_path, str(tmp_path / "global"))
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.networkName = "Net"
        dialog.currentLayer = MagicMock()
        dialog.currentLayer.customProperty.side_effect = (
            lambda key, *a: {"qgisred_identifier": "qgisred_demandbuilder_sectors"}.get(key))
        dialog.currentLayer.source.return_value = os.path.join(subFolder, "Net_DemandBuilder_Sectors_Barrios.shp")
        fileName = dialog.getProjectStyleFilename(dialog.getStyleNameForIdentifier("qgisred_demandbuilder_sectors"))
        expected = _writeStyle(os.path.join(projectRoot, "layerStyles"), fileName)
        layer = self._theme(subFolder, "Net_DemandBuilder_Sectors_Barrios.shp")

        styling.setDemandBuilderStyle(layer)

        assert layer.loadedPath == expected

    @pytest.mark.parametrize("layerType", AUXILIARY_LAYER_TYPES, ids=lambda layerType: layerType.key)
    def test_every_type_ships_a_default_style(self, tmp_path, layerType):
        styling, subFolder, _ = _demandBuilderUtils(tmp_path, str(tmp_path / "global"))
        layer = self._theme(subFolder, composeBaseName("Net", layerType, "Padron") + ".shp")

        styling.setDemandBuilderStyle(layer)

        assert os.path.dirname(layer.loadedPath) == os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")
        assert os.path.exists(layer.loadedPath)
        assert layer.repainted
