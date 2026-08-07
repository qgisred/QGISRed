# -*- coding: utf-8 -*-
"""Thematic-map layers share their shapefile with an input layer, so committing an
edit to that file must reload and repaint them automatically — without touching the
thematic symbology that gives them their meaning."""
from unittest.mock import MagicMock

from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
from QGISRed.tools.utils import qgisred_layer_utils as layer_utils_module
from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from QGISRed.ui.queries.qgisred_thematicmaps_dialog import QGISRedThematicMapsDialog
from QGISRed.ui.edition import qgisred_groupedit_dialog as groupedit_module


PIPES_PATH = "/proj/Net_Pipes.shp"
JUNCTIONS_PATH = "/proj/Net_Junctions.shp"

_uniform = QGISRedFileSystemUtils().getUniformedPath


def _mockLayer(identifier, path):
    layer = MagicMock()
    layer.customProperty.side_effect = (
        lambda name, *a: identifier if name == "qgisred_identifier" else None)
    layer.dataProvider.return_value.dataSourceUri.return_value = path
    return layer


def _utils(layers):
    utils = QGISRedLayerUtils("/proj", "Net", MagicMock())
    utils.getLayers = lambda: list(layers)
    return utils


class TestRefreshThematicMapLayers:
    def test_matching_thematic_layer_is_reloaded_and_repainted(self):
        thematic = _mockLayer("qgisred_query_pipes_diameter", PIPES_PATH)

        _utils([thematic]).refreshThematicMapLayers(PIPES_PATH)

        thematic.dataProvider.return_value.reloadData.assert_called_once()
        thematic.triggerRepaint.assert_called_once()
        thematic.countSymbolFeatures.assert_called_once()
        thematic.setRenderer.assert_not_called()
        thematic.setDataSource.assert_not_called()

    def test_input_layer_and_other_files_are_untouched(self):
        inputLayer = _mockLayer("qgisred_pipes", PIPES_PATH)
        otherThematic = _mockLayer("qgisred_query_junctions_elevation", JUNCTIONS_PATH)

        _utils([inputLayer, otherThematic]).refreshThematicMapLayers(PIPES_PATH)

        inputLayer.dataProvider.return_value.reloadData.assert_not_called()
        inputLayer.triggerRepaint.assert_not_called()
        otherThematic.dataProvider.return_value.reloadData.assert_not_called()
        otherThematic.triggerRepaint.assert_not_called()

    def test_a_failing_layer_does_not_stop_the_next_one(self):
        broken = _mockLayer("qgisred_query_pipes_diameter", PIPES_PATH)
        broken.dataProvider.return_value.reloadData.side_effect = RuntimeError("dead layer")
        healthy = _mockLayer("qgisred_query_pipes_material", PIPES_PATH)

        _utils([broken, healthy]).refreshThematicMapLayers(PIPES_PATH)

        healthy.dataProvider.return_value.reloadData.assert_called_once()
        healthy.triggerRepaint.assert_called_once()

    def test_broken_tree_entries_are_skipped_without_error(self):
        noProvider = _mockLayer("qgisred_query_pipes_length", PIPES_PATH)
        noProvider.dataProvider.return_value = None
        healthy = _mockLayer("qgisred_query_pipes_diameter", PIPES_PATH)

        _utils([None, noProvider, healthy]).refreshThematicMapLayers(PIPES_PATH)

        healthy.triggerRepaint.assert_called_once()


class _CategorizedRendererStub:
    pass


class TestCategorizedThematicMaps:
    def _categorizedLayer(self, field="Material", styleUri="/proj/pipe_materials.qml"):
        properties = {
            "qgisred_identifier": "qgisred_query_pipes_material",
            "query_field": field,
            "styleURI": styleUri,
        }
        layer = _mockLayer("qgisred_query_pipes_material", PIPES_PATH)
        layer.customProperty.side_effect = lambda name, *a: properties.get(name)
        layer.renderer.return_value = _CategorizedRendererStub()
        return layer

    def test_categories_are_rebuilt_so_new_values_get_drawn(self, monkeypatch):
        monkeypatch.setattr(layer_utils_module, "QgsCategorizedSymbolRenderer",
                            _CategorizedRendererStub)
        layer = self._categorizedLayer()
        utils = _utils([layer])
        styling = MagicMock()
        utils._styling = lambda: styling

        utils.refreshThematicMapLayers(PIPES_PATH)

        styling.applyCategorizedRenderer.assert_called_once_with(
            layer, "Material", "/proj/pipe_materials.qml")
        layer.triggerRepaint.assert_called_once()

    def test_a_failing_rebuild_still_repaints(self, monkeypatch):
        monkeypatch.setattr(layer_utils_module, "QgsCategorizedSymbolRenderer",
                            _CategorizedRendererStub)
        layer = self._categorizedLayer()
        utils = _utils([layer])
        styling = MagicMock()
        styling.applyCategorizedRenderer.side_effect = ValueError("field not found")
        utils._styling = lambda: styling

        utils.refreshThematicMapLayers(PIPES_PATH)

        layer.triggerRepaint.assert_called_once()

    def test_non_categorized_maps_keep_their_renderer(self, monkeypatch):
        monkeypatch.setattr(layer_utils_module, "QgsCategorizedSymbolRenderer",
                            _CategorizedRendererStub)
        layer = self._categorizedLayer()
        layer.renderer.return_value = MagicMock()
        utils = _utils([layer])
        styling = MagicMock()
        utils._styling = lambda: styling

        utils.refreshThematicMapLayers(PIPES_PATH)

        styling.applyCategorizedRenderer.assert_not_called()
        layer.triggerRepaint.assert_called_once()


class TestTryReloadExistingLayer:
    def test_delegates_after_reloading_the_main_layer(self):
        utils = _utils([])
        mainLayer = _mockLayer("qgisred_pipes", PIPES_PATH)
        utils._findLayerByPath = MagicMock(return_value=mainLayer)
        utils.refreshThematicMapLayers = MagicMock()

        result = utils._tryReloadExistingLayer(PIPES_PATH)

        assert result is mainLayer
        mainLayer.dataProvider.return_value.reloadData.assert_called_once()
        mainLayer.triggerRepaint.assert_called_once()
        utils.refreshThematicMapLayers.assert_called_once_with(PIPES_PATH)

    def test_delegates_even_when_no_main_layer_is_open(self):
        utils = _utils([])
        utils._findLayerByPath = MagicMock(return_value=None)
        utils.refreshThematicMapLayers = MagicMock()

        result = utils._tryReloadExistingLayer(PIPES_PATH)

        assert result is None
        utils.refreshThematicMapLayers.assert_called_once_with(PIPES_PATH)


class TestSyncLayersKeepsThematicStyle:
    def test_data_is_refreshed_but_renderer_is_never_cloned(self):
        dialog = object.__new__(QGISRedThematicMapsDialog)
        mainLayer = MagicMock()
        derivedLayer = MagicMock()

        dialog.syncLayers(mainLayer, derivedLayer)

        derivedLayer.dataProvider.return_value.forceReload.assert_called_once()
        derivedLayer.triggerRepaint.assert_called_once()
        derivedLayer.setRenderer.assert_not_called()
        mainLayer.renderer.assert_not_called()


class TestGroupEditAcceptRefreshesThematicMaps:
    def _dialog(self, layer):
        dialog = object.__new__(groupedit_module.QGISRedGroupEditDialog)
        dialog.ProjectDirectory = "/proj"
        dialog.NetworkName = "Net"
        dialog.iface = MagicMock()
        dialog.editedLayers = [layer]
        dialog.banner = MagicMock()
        dialog._hasPendingChanges = lambda: False
        dialog._applyBeforeAccept = lambda: True
        dialog._removePreviewHighlights = MagicMock()
        dialog._disconnectCountSignals = MagicMock()
        dialog._disconnectProjectSignals = MagicMock()
        dialog.accept = MagicMock()
        return dialog

    def _editedLayer(self, commits=True):
        layer = _mockLayer("qgisred_pipes", PIPES_PATH)
        layer.isEditable.return_value = True
        layer.commitChanges.return_value = commits
        layer.commitErrors.return_value = []
        return layer

    def test_refreshes_thematic_layers_after_a_successful_commit(self, monkeypatch):
        layerUtilsClass = MagicMock()
        monkeypatch.setattr(groupedit_module, "QGISRedLayerUtils", layerUtilsClass)
        layer = self._editedLayer()
        dialog = self._dialog(layer)

        dialog._onAccept()

        layerUtilsClass.assert_called_once_with("/proj", "Net", dialog.iface)
        layerUtilsClass.return_value.refreshThematicMapLayers.assert_called_once_with(
            _uniform(PIPES_PATH))
        dialog.accept.assert_called_once()

    def test_no_refresh_when_the_commit_fails(self, monkeypatch):
        layerUtilsClass = MagicMock()
        monkeypatch.setattr(groupedit_module, "QGISRedLayerUtils", layerUtilsClass)
        layer = self._editedLayer(commits=False)
        dialog = self._dialog(layer)

        dialog._onAccept()

        layerUtilsClass.assert_not_called()
        dialog.accept.assert_not_called()
