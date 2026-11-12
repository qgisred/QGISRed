# -*- coding: utf-8 -*-
"""Two networks in one folder where one name extends the other (Net1 and Net1_v2)."""
import os
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO, belongsToNetwork, networkNamesInFolder
from QGISRed.ui.general.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog


def _touch(*parts):
    path = os.path.join(*parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()
    return path


@pytest.fixture
def sharedFolder(tmp_path):
    root = str(tmp_path / "Shared")
    for net in ("Net1", "Net1_v2"):
        _touch(root, net + "_Metadata.txt")
        _touch(root, net + "_Pipes.shp")
        _touch(root, "Issues", net + "_Pipes_Issues.shp")
        _touch(root, "layerStyles", net + "_Pipes.qml")
    _touch(root, "layerStyles", "Pipes.qml")
    return root


def _uniformFs():
    fs = MagicMock()
    fs.getUniformedPath.side_effect = lambda p: p
    return fs


class TestBelongsToNetwork:
    @pytest.mark.parametrize("fileName,expected", [
        ("Net1_Pipes.shp", True),
        ("Net1_v2_Pipes.shp", False),
        ("Net1_v2.shp", True),
        ("Net10_Pipes.shp", False),
        ("Pipes.qml", False),
    ])
    def test_longest_network_name_owns_the_file(self, fileName, expected):
        assert belongsToNetwork(fileName, "Net1", {"Net1_v2"}) is expected

    def test_the_longer_network_keeps_its_files(self):
        assert belongsToNetwork("Net1_v2_Pipes.shp", "Net1_v2", {"Net1"}) is True

    def test_networks_are_found_by_their_marker_file(self, sharedFolder):
        assert networkNamesInFolder(sharedFolder) == {"Net1", "Net1_v2"}


class TestProcessProjectFiles:
    def test_renaming_leaves_the_sibling_alone(self, sharedFolder):
        io = QGISRedProjectIO(sharedFolder, "Net1")
        with patch.object(QGISRedProjectIO, "_fs", return_value=_uniformFs()):
            io.processProjectFiles(sharedFolder, "Net1", "Red", sharedFolder, deleteSource=True)
        assert os.path.exists(os.path.join(sharedFolder, "Red_Pipes.shp"))
        assert os.path.exists(os.path.join(sharedFolder, "Net1_v2_Pipes.shp"))
        assert os.path.exists(os.path.join(sharedFolder, "Issues", "Net1_v2_Pipes_Issues.shp"))
        assert not os.path.exists(os.path.join(sharedFolder, "Red_v2_Pipes.shp"))


class TestRemoveProject:
    def _dialog(self):
        dialog = QGISRedProjectManagerDialog.__new__(QGISRedProjectManagerDialog)
        dialog.utils = _uniformFs()
        return dialog

    def test_only_its_own_files_are_collected(self, sharedFolder):
        found = {os.path.relpath(p, sharedFolder) for p in self._dialog()._collectProjectFiles(sharedFolder, "Net1")}
        assert found == {
            "Net1_Metadata.txt",
            "Net1_Pipes.shp",
            os.path.join("Issues", "Net1_Pipes_Issues.shp"),
            os.path.join("layerStyles", "Net1_Pipes.qml"),
        }

    def test_the_shared_layerstyles_folder_is_kept(self, sharedFolder):
        found = self._dialog()._collectProjectFiles(sharedFolder, "Net1")
        assert os.path.join(sharedFolder, "layerStyles") not in found

    def test_a_lone_network_takes_its_layerstyles_folder(self, tmp_path):
        root = str(tmp_path / "Alone")
        _touch(root, "Net1_Metadata.txt")
        _touch(root, "layerStyles", "Pipes.qml")
        found = self._dialog()._collectProjectFiles(root, "Net1")
        assert os.path.join(root, "layerStyles") in found

