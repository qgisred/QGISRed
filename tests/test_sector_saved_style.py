# -*- coding: utf-8 -*-
"""A style saved by the user wins over the one the plugin computes for sector layers.

Demand sectors get their look generated — setSectorsStyle picks a random colour per class
and redraws them on every reload — so until now a style saved for them could never take
effect. Hydraulic sectors ship a style file and keep going through setStyle.
"""
import os
from unittest.mock import MagicMock

import pytest

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils


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


class TestSetSavedStyle:
    def test_a_project_style_is_applied(self, tmp_path):
        utils = _styling(tmp_path)
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"),
                               "Net_DemandSectorsLinks.qml")
        layer = _FakeLayer()

        assert utils.setSavedStyle(layer, "DemandSectors_Links") is True
        assert layer.loadedPath == expected

    def test_a_global_style_is_applied(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "DemandSectorsLinks.qml")
        layer = _FakeLayer()

        assert utils.setSavedStyle(layer, "DemandSectors_Links") is True
        assert layer.loadedPath == expected

    def test_the_project_one_wins(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils = _styling(tmp_path, globalFolder=globalFolder)
        expected = _writeStyle(os.path.join(str(tmp_path / "project"), "layerStyles"),
                               "Net_DemandSectorsLinks.qml")
        _writeStyle(os.path.join(globalFolder, "layerStyles"), "DemandSectorsLinks.qml")
        layer = _FakeLayer()

        utils.setSavedStyle(layer, "DemandSectors_Links")

        assert layer.loadedPath == expected

    def test_it_never_falls_through_to_the_shipped_defaults(self, tmp_path):
        # The whole point: the caller has to be told there is nothing saved, so it can
        # generate the style instead. setStyle would silently load a factory file.
        utils = _styling(tmp_path)
        layer = _FakeLayer()

        assert utils.setSavedStyle(layer, "DemandSectors_Links") is False
        assert layer.loadedPath is None

    def test_no_name_means_nothing_to_look_for(self, tmp_path):
        assert _styling(tmp_path).setSavedStyle(_FakeLayer(), "") is False


class TestApplySectorStyle:
    def _utils(self):
        return QGISRedLayerUtils.__new__(QGISRedLayerUtils)

    def test_demand_sectors_generate_their_style_when_none_is_saved(self):
        styling = MagicMock()
        styling.setSavedStyle.return_value = False
        layer = MagicMock()

        self._utils()._applySectorStyle(styling, layer, "DemandSectors_Links")

        styling.setSectorsStyle.assert_called_once_with(layer)

    def test_a_saved_style_stops_the_random_colours(self):
        styling = MagicMock()
        styling.setSavedStyle.return_value = True
        layer = MagicMock()

        self._utils()._applySectorStyle(styling, layer, "DemandSectors_Links")

        styling.setSectorsStyle.assert_not_called()

    @pytest.mark.parametrize("name", ["HydraulicSectors_Links", "HydraulicSectors_IsolatedDemands"])
    def test_hydraulic_sectors_keep_going_through_setstyle(self, name):
        # They ship a style file, so setStyle already covers project, global and factory.
        styling = MagicMock()
        layer = MagicMock()

        self._utils()._applySectorStyle(styling, layer, name)

        styling.setStyle.assert_called_once_with(layer, name)
        styling.setSavedStyle.assert_not_called()
        styling.setSectorsStyle.assert_not_called()
