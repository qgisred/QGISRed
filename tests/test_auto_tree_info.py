# -*- coding: utf-8 -*-
"""Reading a tree's own Nodes shapefile to auto-refresh it without opening the dialog.

AutoTree needs the root id, the function-cost code and whether closed pipes were ignored --
exactly what WriteTree stamps on the tree's ROOT node row (tools/utils/... on the C# side).
This covers recovering that, and recognising when there isn't enough of it to try: a tree
built before these columns existed, or one whose files are simply gone.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from qgis.core import NULL

_QGSPROJECT = "QGISRed.sections.tools_section.QgsProject"
_QGSVECTORLAYER = "QGISRed.sections.tools_section.QgsVectorLayer"
_GISRED = "QGISRed.sections.tools_section.GISRed"
_QAPPLICATION = "QGISRed.sections.tools_section.QApplication"


class FakeFeature:
    def __init__(self, values):
        self._values = values

    def __getitem__(self, name):
        return self._values.get(name, NULL)


class FakeFields:
    def __init__(self, names):
        self._names = set(names)

    def indexFromName(self, name):
        return 0 if name in self._names else -1


class FakeNodesLayer:
    def __init__(self, features, fieldNames=("Id", "NodeType", "CostFn", "IgnClosed"), valid=True):
        self._features = features
        self._fields = FakeFields(fieldNames)
        self._valid = valid

    def isValid(self):
        return self._valid

    def fields(self):
        return self._fields

    def getFeatures(self):
        return list(self._features)


@pytest.fixture
def section(tmp_path):
    # Imported here, not at module level: importing sections.tools_section at collection
    # time (before the per-test Qt mock fixtures below have run) leaves
    # QGISRedSelectPointTool a broken MagicMock for every test collected after this file --
    # tools_section.py imports it, and every other test file imports section modules the
    # same lazy way for exactly this reason.
    from QGISRed.sections.tools_section import ToolsSection

    class Section(ToolsSection):
        def __init__(self, projectDirectory, networkName):
            self.ProjectDirectory = projectDirectory
            self.NetworkName = networkName
            self.tempFolder = "/temp"
            self.checkDependencies = lambda: True
            self.defineCurrentProject = lambda: None
            self.isValidProject = lambda: True
            self.isLayerOnEdition = lambda: False
            self.runTree = MagicMock()
            self._handleTreeResult = MagicMock()

    return Section(str(tmp_path), "Net")


def _clickedLayer(sourcePath):
    layer = MagicMock()
    layer.dataProvider.return_value.dataSourceUri.return_value = sourcePath
    return layer


def _nodesPath(section, treeName):
    fileName = section.NetworkName + "_" + treeName + "_Nodes.shp"
    return os.path.join(section.ProjectDirectory, "Queries", "Trees", fileName)


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


class TestTreeNameFromLayerPath:
    """The tree's identifier ("qgisred_tree_nodes"/"..._links") is the same for every tree,
    so the file name is the only thing that tells them apart."""

    def test_recovers_the_name_from_the_nodes_file(self, section):
        path = os.path.join(section.ProjectDirectory, "Net_J5_Union_Nodes.shp")
        assert section._treeNameFromLayerPath(path) == "J5_Union"

    def test_recovers_the_name_from_the_links_file(self, section):
        path = os.path.join(section.ProjectDirectory, "Net_J5_Union_Links.shp")
        assert section._treeNameFromLayerPath(path) == "J5_Union"

    def test_a_path_from_another_network_matches_nothing(self, section):
        path = os.path.join(section.ProjectDirectory, "OtherNet_J5_Union_Nodes.shp")
        assert section._treeNameFromLayerPath(path) is None

    def test_a_shapefile_that_is_not_a_tree_matches_nothing(self, section):
        path = os.path.join(section.ProjectDirectory, "Net_Pipes.shp")
        assert section._treeNameFromLayerPath(path) is None


class TestReadAutoTreeInfo:

    def test_reads_the_root_row(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        root = FakeFeature({
            "NodeType": "ROOT", "Id": "J5",
            "CostFn": "HydraulicResistance", "IgnClosed": "False",
        })
        other = FakeFeature({"NodeType": "Junction", "Id": "J6"})
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([other, root])):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            info = section._readAutoTreeInfo("layerId")

        assert info == (treeName, "J5", "HydraulicResistance", "False")

    def test_the_clicked_layer_can_be_the_nodes_layer_itself(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        root = FakeFeature({
            "NodeType": "ROOT", "Id": "J5",
            "CostFn": "Diameter", "IgnClosed": "True",
        })
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Nodes.shp"))

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([root])):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            info = section._readAutoTreeInfo("layerId")

        assert info == (treeName, "J5", "Diameter", "True")

    def test_the_clicked_layer_no_longer_exists(self, section):
        with patch(_QGSPROJECT) as qgsProject:
            qgsProject.instance.return_value.mapLayer.return_value = None
            assert section._readAutoTreeInfo("layerId") is None

    def test_a_path_that_is_not_a_tree_shapefile_yields_nothing(self, section):
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_Pipes.shp"))
        with patch(_QGSPROJECT) as qgsProject:
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None

    def test_a_missing_nodes_shapefile_yields_nothing(self, section):
        # Never written, e.g. Queries/Trees was cleaned up by hand.
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_Ghost_Links.shp"))
        with patch(_QGSPROJECT) as qgsProject:
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None

    def test_a_tree_from_before_the_new_columns_existed_yields_nothing(self, section):
        treeName = "Old_Tree"
        _touch(_nodesPath(section, treeName))
        root = FakeFeature({"NodeType": "ROOT", "Id": "J5"})
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))
        noCostFnFields = FakeNodesLayer([root], fieldNames=("Id", "NodeType"))

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=noCostFnFields):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None

    def test_a_root_row_missing_a_value_yields_nothing(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        root = FakeFeature({"NodeType": "ROOT", "Id": "J5", "CostFn": "Length"})  # IgnClosed absent -> NULL
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([root])):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None

    def test_no_root_row_at_all_yields_nothing(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        onlyOther = FakeFeature({"NodeType": "Junction", "Id": "J6"})
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([onlyOther])):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None

    def test_an_invalid_layer_yields_nothing(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))
        invalidLayer = FakeNodesLayer([], valid=False)

        with patch(_QGSPROJECT) as qgsProject, patch(_QGSVECTORLAYER, return_value=invalidLayer):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            assert section._readAutoTreeInfo("layerId") is None


class TestRunAutoTree:
    """The public entry point the stale-tree warning calls: read the tree's own recipe off
    its Nodes shapefile, or fall back to the interactive dialog when there isn't one."""

    def test_missing_info_falls_back_to_the_interactive_dialog(self, section):
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_Pipes.shp"))
        with patch(_QGSPROJECT) as qgsProject, patch(_GISRED) as gisRed, patch(_QAPPLICATION):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            section.runAutoTree("layerId")

        section.runTree.assert_called_once_with(False)
        gisRed.AutoTree.assert_not_called()
        section._handleTreeResult.assert_not_called()

    def test_available_info_calls_the_dll_and_hands_off_the_result(self, section):
        treeName = "J5_Union"
        _touch(_nodesPath(section, treeName))
        root = FakeFeature({
            "NodeType": "ROOT", "Id": "J5",
            "CostFn": "HydraulicResistance", "IgnClosed": "False",
        })
        clickedLayer = _clickedLayer(os.path.join(section.ProjectDirectory, "Net_" + treeName + "_Links.shp"))

        with patch(_QGSPROJECT) as qgsProject, \
                patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([root])), \
                patch(_GISRED) as gisRed, patch(_QAPPLICATION):
            qgsProject.instance.return_value.mapLayer.return_value = clickedLayer
            gisRed.AutoTree.return_value = "shps^" + treeName
            section.runAutoTree("layerId")

        gisRed.AutoTree.assert_called_once_with(
            section.ProjectDirectory, section.NetworkName, section.tempFolder,
            treeName, "J5", "HydraulicResistance", "False",
        )
        section.runTree.assert_not_called()
        section._handleTreeResult.assert_called_once_with("shps^" + treeName)
