# -*- coding: utf-8 -*-
"""Reopening the Queries/Trees group from _Metadata.txt (no .qgs saved).

getTreeGroup() stopped naming the group "Tree: <name>" and started using the tree's own
name directly (sections/layer_management_section.py), which changed the ASCII tag
_buildGroupsString writes for it — from "Tree_<name>" to just "<name>" — and changed the
shapefile naming openTreeLayer() looks for — from "<Nodes|Links>_Tree_<name>.shp" to just
"<name>_<Nodes|Links>.shp". _openGroupByName's detection regex, its sanitized-name
extraction and its Links/Nodes check were never updated to match, so no Tree layer came
back when a project with no saved .qgs was reopened.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

from unittest.mock import MagicMock

import pytest


class TestTreeGroupDetection:
    """_TREE_GROUP_RE decides whether a metadata group tag names a tree leaf."""

    def _matches(self, groupName):
        from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO
        return bool(QGISRedProjectIO._TREE_GROUP_RE.match(groupName))

    def test_the_current_bare_tree_name_is_recognised(self):
        """getTreeGroup() now names the leaf group after the tree itself, with no
        "Tree_"/"Tree: " marker at all."""
        assert self._matches("Queries/Trees/J5_Union")

    def test_the_legacy_flat_group_is_still_recognised(self):
        assert self._matches("Queries/Tree_J5_Union")

    def test_the_intermediate_prefixed_group_is_still_recognised(self):
        """Projects saved between feeba06 and f44f435 nested the group under Trees but
        still carried a "Tree_" marker in its tag."""
        assert self._matches("Queries/Trees/Tree_J5_Union")

    def test_unrelated_queries_groups_are_left_alone(self):
        assert not self._matches("Queries/IsolatedSegments")

    def test_other_top_level_groups_are_left_alone(self):
        assert not self._matches("Issues/HydraulicSectors")


class TestReopenTreeLayersFromMetadata:
    """_openGroupByName must find the actual shapefiles and reopen them."""

    def _io(self, tmp_path):
        from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO
        io = QGISRedProjectIO(directory=str(tmp_path), networkName="Net", iface=MagicMock())
        return io

    def _patchUtils(self, monkeypatch):
        from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        fakeGroup = MagicMock()
        monkeypatch.setattr(QGISRedLayerUtils, "getOrCreateNestedGroup", MagicMock(return_value=fakeGroup))
        openCalls = []
        monkeypatch.setattr(
            QGISRedLayerUtils, "openTreeLayer",
            lambda self, group, name, treeName, link=False: openCalls.append((name, treeName, link)))
        return fakeGroup, openCalls

    def test_the_current_naming_scheme_is_reopened(self, tmp_path, monkeypatch):
        """Shapefiles named "<treeName>_Nodes.shp" / "<treeName>_Links.shp", the format
        openTreeLayer() writes today."""
        treesDir = tmp_path / "Queries" / "Trees"
        treesDir.mkdir(parents=True)
        (treesDir / "Net_J5_Union_Nodes.shp").write_text("")
        (treesDir / "Net_J5_Union_Links.shp").write_text("")

        io = self._io(tmp_path)
        fakeGroup, openCalls = self._patchUtils(monkeypatch)

        io._openGroupByName("Queries/Trees/J5_Union", ["J5_Union_Nodes", "J5_Union_Links"])

        assert openCalls == [
            ("Links", "J5_Union", True),
            ("Nodes", "J5_Union", False),
        ]

    def test_a_tree_name_with_accents_still_resolves(self, tmp_path, monkeypatch):
        """The metadata tag and layer names are ASCII-sanitized; the real file name on
        disk keeps the accent and must still be matched and passed through untouched."""
        treesDir = tmp_path / "Queries" / "Trees"
        treesDir.mkdir(parents=True)
        (treesDir / "Net_J5-Unión_Nodes.shp").write_text("")
        (treesDir / "Net_J5-Unión_Links.shp").write_text("")

        io = self._io(tmp_path)
        fakeGroup, openCalls = self._patchUtils(monkeypatch)

        io._openGroupByName("Queries/Trees/J5_Union", ["J5_Union_Nodes", "J5_Union_Links"])

        assert openCalls == [
            ("Links", "J5-Unión", True),
            ("Nodes", "J5-Unión", False),
        ]

    def test_the_legacy_naming_scheme_still_resolves(self, tmp_path, monkeypatch):
        """Shapefiles named "<Nodes|Links>_Tree_<treeName>.shp", the format used before
        b302045/f44f435 reordered it."""
        treesDir = tmp_path / "Queries" / "Trees"
        treesDir.mkdir(parents=True)
        (treesDir / "Net_Nodes_Tree_J5_Union.shp").write_text("")
        (treesDir / "Net_Links_Tree_J5_Union.shp").write_text("")

        io = self._io(tmp_path)
        fakeGroup, openCalls = self._patchUtils(monkeypatch)

        io._openGroupByName("Queries/Tree_J5_Union", ["Nodes_Tree_J5_Union", "Links_Tree_J5_Union"])

        assert openCalls == [
            ("Links", "J5_Union", True),
            ("Nodes", "J5_Union", False),
        ]

    def test_no_matching_shapefile_opens_nothing(self, tmp_path, monkeypatch):
        io = self._io(tmp_path)
        fakeGroup, openCalls = self._patchUtils(monkeypatch)

        io._openGroupByName("Queries/Trees/Missing", ["Missing_Nodes", "Missing_Links"])

        assert openCalls == []
