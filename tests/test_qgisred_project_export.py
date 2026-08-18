# -*- coding: utf-8 -*-
"""Tests for the portable project export engine (tools/utils/qgisred_project_export.py).

Everything runs against real temporary folders and a real .qgz (a ZipFile holding one .qgs), so the
path arithmetic that makes the ZIP portable is exercised for real rather than mocked.
"""
import json
import os
import shutil
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

from QGISRed.tools.utils.qgisred_project_export import (
    QGISRedProjectPackage, safeJoin, relativeToRoot, norm,
    STRUCTURE_PROJECT, STRUCTURE_PARENT,
    SCOPE_PROJECT, SCOPE_SIBLING, SCOPE_OUTSIDE,
    REASON_QGZ_OUTSIDE, REASON_EXTERNAL_OUTSIDE, REASON_EXTERNAL_EXCLUDED,
    REASON_NO_PIPES_IN_ZIP, REASON_SCHEMA_TOO_NEW, REASON_UNSAFE_MEMBER,
    MANIFEST_NAME, SCHEMA_VERSION,
)

NET = "Net"

METADATA_TEMPLATE = """<?xml version="1.0" encoding="ISO-8859-1"?>
<Metadata>
  <ThirdParty>
    <QGISRed>
      <QGisProject>{qgis}</QGisProject>
    </QGISRed>
  </ThirdParty>
</Metadata>
"""

QGS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<qgis version="3.34.0">
  <projectlayers>
{layers}
  </projectlayers>
</qgis>
"""

MAPLAYER_TEMPLATE = """    <maplayer>
      <datasource>{datasource}</datasource>
      <layername>{name}</layername>
    </maplayer>"""


def _touch(path, content="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _writeQgz(qgzPath, datasources):
    """Creates a real .qgz containing one .qgs that references `datasources`.

    datasources is a list of (rawValue, layerName).
    """
    layers = "\n".join(
        MAPLAYER_TEMPLATE.format(datasource=raw, name=name) for raw, name in datasources
    )
    qgs = QGS_TEMPLATE.format(layers=layers)
    os.makedirs(os.path.dirname(qgzPath), exist_ok=True)
    with ZipFile(qgzPath, "w", ZIP_DEFLATED) as zout:
        zout.writestr(os.path.basename(qgzPath).replace(".qgz", ".qgs"), qgs)
    return qgzPath


def _readQgzDatasources(qgzPath):
    """Returns the raw <datasource> values of the .qgs inside a .qgz."""
    import re
    values = []
    with ZipFile(qgzPath, "r") as zin:
        for name in zin.namelist():
            if name.endswith(".qgs"):
                text = zin.read(name).decode("utf-8")
                values.extend(re.findall(r"<datasource>([^<]*)</datasource>", text))
    return values


def _makeProject(parent, net=NET, qgzAt="project", datasources=(), groups=()):
    """Creates <parent>/<net>/ with the base layers, plus optionally the .qgz and content groups.

    qgzAt: "project" (inside the project folder) | "subfolder" | "parent" | "outside" | None
    groups: iterable of subfolder names to create with one <net>_* file inside
    Returns (projectDir, qgzPath or None).
    """
    projectDir = os.path.join(parent, net)
    _touch(os.path.join(projectDir, net + "_Pipes.shp"))
    _touch(os.path.join(projectDir, net + "_Pipes.dbf"))
    _touch(os.path.join(projectDir, net + "_Junctions.shp"))

    for group in groups:
        _touch(os.path.join(projectDir, group, net + "_" + group.replace(" ", "") + ".shp"))

    qgzPath = None
    if qgzAt == "project":
        qgzPath = os.path.join(projectDir, net + ".qgz")
    elif qgzAt == "subfolder":
        qgzPath = os.path.join(projectDir, "map", net + ".qgz")
    elif qgzAt == "parent":
        qgzPath = os.path.join(parent, net + ".qgz")
    elif qgzAt == "outside":
        qgzPath = os.path.join(parent, "elsewhere", net + ".qgz")

    if qgzPath:
        _writeQgz(qgzPath, datasources)
        relative = os.path.relpath(qgzPath, projectDir)
        _touch(os.path.join(projectDir, net + "_Metadata.txt"),
               METADATA_TEMPLATE.format(qgis=relative.replace(os.sep, "/")))
    else:
        _touch(os.path.join(projectDir, net + "_Metadata.txt"),
               METADATA_TEMPLATE.format(qgis=""))
    return projectDir, qgzPath


@pytest.fixture
def workspace():
    path = tempfile.mkdtemp()
    yield os.path.realpath(path)
    shutil.rmtree(path, ignore_errors=True)


class TestSafeJoin:
    def test_plain_and_nested_paths_are_joined(self, workspace):
        assert safeJoin(workspace, "") == os.path.realpath(workspace)
        assert safeJoin(workspace, ".") == os.path.realpath(workspace)
        assert safeJoin(workspace, "a/b.txt") == os.path.join(os.path.realpath(workspace), "a", "b.txt")

    @pytest.mark.parametrize("member", [
        "../evil.txt",
        "a/../../evil.txt",
        "C:/evil.txt",
        "/etc/evil",
        "\\\\server\\share\\evil",
        None,
    ])
    def test_escaping_members_are_refused(self, workspace, member):
        with pytest.raises(ValueError):
            safeJoin(workspace, member)


class TestRelativeToRoot:
    def test_inside_returns_posix_path(self, workspace):
        target = os.path.join(workspace, "a", "b.txt")
        assert relativeToRoot(target, workspace) == "a/b.txt"

    def test_root_itself_is_the_empty_string(self, workspace):
        assert relativeToRoot(workspace, workspace) == ""

    def test_outside_returns_none(self, workspace):
        assert relativeToRoot(os.path.dirname(workspace), workspace) is None


class TestClassifyQgisLocation:
    @pytest.mark.parametrize("qgzAt,expected", [
        ("project", SCOPE_PROJECT),
        ("subfolder", SCOPE_PROJECT),
        ("parent", SCOPE_SIBLING),
        ("outside", SCOPE_OUTSIDE),
    ])
    def test_scope_by_location(self, workspace, qgzAt, expected):
        projectDir, qgzPath = _makeProject(workspace, qgzAt=qgzAt)
        package = QGISRedProjectPackage(projectDir, NET)
        scope, resolved = package.classifyQgisLocation()
        assert scope == expected
        assert norm(resolved) == norm(qgzPath)

    def test_no_qgis_project_is_not_an_error(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt=None)
        scope, resolved = QGISRedProjectPackage(projectDir, NET).classifyQgisLocation()
        assert scope is None
        assert resolved is None

    def test_out_of_scope_qgz_blocks_the_export(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="outside")
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
        assert not plan.isValid
        assert REASON_QGZ_OUTSIDE in plan.blockingReasons


class TestComputeExportRoot:
    def test_structure_a_when_everything_is_inside(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
        assert plan.structure == STRUCTURE_PROJECT
        assert norm(plan.exportRoot) == norm(projectDir)
        assert plan.projectFolderRel == ""

    def test_structure_b_when_the_qgz_is_one_level_up(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="parent")
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
        assert plan.structure == STRUCTURE_PARENT
        assert norm(plan.exportRoot) == norm(workspace)
        assert plan.projectFolderRel == NET

    def test_structure_b_when_an_external_item_is_a_sibling(self, workspace):
        dtm = _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
        assert plan.structure == STRUCTURE_PARENT
        assert [norm(i.source) for i in plan.inScopeItems] == [norm(dtm)]

    def test_structure_collapses_to_a_when_external_data_is_excluded(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport(includeExternal=False)
        assert plan.structure == STRUCTURE_PROJECT


class TestCollectExternalData:
    def test_own_project_files_are_not_external(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("Net_Pipes.shp", "Pipes")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert items == []

    def test_remote_sources_are_ignored(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project", datasources=[
            ("type=xyz&amp;url=https://tile.example/%7Bz%7D/%7Bx%7D/%7By%7D.png", "Basemap"),
            ("crs=EPSG:25830&amp;service=WMS", "WMS"),
            ("https://example.org/data.json", "Remote"),
        ])
        assert QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems == []

    def test_file_url_and_percent_encoding_are_resolved(self, workspace):
        target = _touch(os.path.join(workspace, "my carto", "roads.shp"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("file:///" + target.replace(os.sep, "/").replace(" ", "%20"),
                                                   "Roads")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert [norm(i.source) for i in items] == [norm(target)]

    def test_layername_suffix_is_stripped(self, workspace):
        target = _touch(os.path.join(workspace, "carto", "roads.shp"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../carto/roads.shp|layername=roads", "Roads")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert [norm(i.source) for i in items] == [norm(target)]

    def test_two_layers_on_one_file_are_deduplicated(self, workspace):
        _touch(os.path.join(workspace, "carto", "roads.shp"))
        projectDir, _ = _makeProject(workspace, qgzAt="project", datasources=[
            ("../carto/roads.shp|layername=roads", "Roads A"),
            ("../carto/roads.shp|layername=roads", "Roads B"),
        ])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert len(items) == 1
        assert sorted(items[0].layerNames) == ["Roads A", "Roads B"]

    def test_sidecars_are_collected(self, workspace):
        _touch(os.path.join(workspace, "carto", "roads.shp"))
        _touch(os.path.join(workspace, "carto", "roads.dbf"))
        _touch(os.path.join(workspace, "carto", "roads.prj"))
        _touch(os.path.join(workspace, "carto", "other.shp"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../carto/roads.shp", "Roads")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert len(items) == 1
        assert sorted(os.path.basename(s) for s in items[0].sidecars) == ["roads.dbf", "roads.prj"]

    def test_a_folder_datasource_is_reported_as_a_folder(self, workspace):
        _touch(os.path.join(workspace, "tiles.gdb", "a00000001.gdbtable"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../tiles.gdb", "Tiles")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert [i.kind for i in items] == ["folder"]

    def test_out_of_scope_item_is_flagged(self, workspace):
        # Resolved like the workspace fixture: the exporter reports resolved paths, and on a
        # platform where the temp folder is reached through a link the raw one never matches.
        other = os.path.realpath(tempfile.mkdtemp())
        try:
            far = _touch(os.path.join(other, "ortho.tif"))
            projectDir, _ = _makeProject(workspace, qgzAt="project",
                                         datasources=[(far.replace(os.sep, "/"), "Ortho")])
            plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
            assert [i.scope for i in plan.externalItems] == [SCOPE_OUTSIDE]
            assert plan.outOfScopeItems and not plan.inScopeItems
            # An unreachable third-party layer must not block the export
            assert plan.isValid
        finally:
            shutil.rmtree(other, ignore_errors=True)


QGS_TREE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<qgis version="3.34.0">
  <layer-tree-group>
{tree}
  </layer-tree-group>
  <projectlayers>
{layers}
  </projectlayers>
</qgis>
"""

TREE_LAYER = '      <layer-tree-layer id="{id}" name="{name}" source="{source}"/>'
TREE_GROUP = """    <layer-tree-group name="{name}">
{layer}
    </layer-tree-group>"""

MAPLAYER_WITH_ID = """    <maplayer>
      <id>{id}</id>
      <datasource>{datasource}</datasource>
      <layername>{name}</layername>
    </maplayer>"""


def _writeQgzWithTree(qgzPath, entries):
    """entries: list of (groupPath tuple, layerName, datasource) — builds a real layer tree."""
    treeLines = []
    layerLines = []
    openGroups = []

    def closeTo(depth):
        while len(openGroups) > depth:
            openGroups.pop()
            treeLines.append("    " + "  " * len(openGroups) + "</layer-tree-group>")

    for index, (groupPath, name, source) in enumerate(entries):
        common = 0
        while common < min(len(groupPath), len(openGroups)) and groupPath[common] == openGroups[common]:
            common += 1
        closeTo(common)
        for groupName in groupPath[common:]:
            treeLines.append('    ' + "  " * len(openGroups) + '<layer-tree-group name="%s">' % groupName)
            openGroups.append(groupName)
        layerId = "L%d_id" % index
        treeLines.append(TREE_LAYER.format(id=layerId, name=name, source=source))
        layerLines.append(MAPLAYER_WITH_ID.format(id=layerId, datasource=source, name=name))
    closeTo(0)

    qgs = QGS_TREE_TEMPLATE.format(tree="\n".join(treeLines), layers="\n".join(layerLines))
    os.makedirs(os.path.dirname(qgzPath), exist_ok=True)
    with ZipFile(qgzPath, "w", ZIP_DEFLATED) as zout:
        zout.writestr(os.path.basename(qgzPath).replace(".qgz", ".qgs"), qgs)
    return qgzPath


class TestLayerTreePlacement:
    """The dialog mirrors the QGIS layers panel, and the hierarchy comes from the same .qgz we
    already parse — so it works for projects that are not open."""

    def _project(self, workspace, entries):
        projectDir = os.path.join(workspace, NET)
        _touch(os.path.join(projectDir, NET + "_Pipes.shp"))
        qgzPath = _writeQgzWithTree(os.path.join(projectDir, NET + ".qgz"), entries)
        _touch(os.path.join(projectDir, NET + "_Metadata.txt"),
               METADATA_TEMPLATE.format(qgis=NET + ".qgz"))
        return projectDir, qgzPath

    def test_group_path_is_recovered_from_the_tree(self, workspace):
        _touch(os.path.join(workspace, "Carto", "roads.shp"))
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = self._project(workspace, [
            (("Externas", "Cartografia"), "Roads", "../Carto/roads.shp"),
            (("Externas",), "MDT", "../DTM/mdt.tif"),
        ])
        items = {i.displayName: i for i in
                 QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems}

        assert items["Roads"].placements == [(("Externas", "Cartografia"), "Roads")]
        assert items["MDT"].placements == [(("Externas",), "MDT")]

    def test_nested_groups_keep_their_full_path(self, workspace):
        _touch(os.path.join(workspace, "Carto", "roads.shp"))
        projectDir, _ = self._project(workspace, [
            (("A", "B", "C"), "Roads", "../Carto/roads.shp"),
        ])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert items[0].placements == [(("A", "B", "C"), "Roads")]

    def test_one_file_in_two_groups_keeps_both_placements(self, workspace):
        """It is still a single ExternalItem — the file travels once — but the dialog shows it in
        both groups, as the layers panel does."""
        _touch(os.path.join(workspace, "Carto", "roads.shp"))
        projectDir, _ = self._project(workspace, [
            (("Grupo A",), "Roads A", "../Carto/roads.shp"),
            (("Grupo B",), "Roads B", "../Carto/roads.shp"),
        ])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems

        assert len(items) == 1
        assert items[0].placements == [(("Grupo A",), "Roads A"), (("Grupo B",), "Roads B")]

    def test_a_subset_datasource_is_not_shown_twice(self, workspace):
        """QGIS escapes the layer-tree `source` attribute one level deeper than the <datasource>
        element, so a datasource carrying quotes (a subset filter) reaches the regex sweep as a
        string seenRaw cannot match. It must not become a second, group-less row."""
        _touch(os.path.join(workspace, "Carto", "roads.shp"))
        projectDir = os.path.join(workspace, NET)
        _touch(os.path.join(projectDir, NET + "_Pipes.shp"))
        treeLayer = TREE_LAYER.format(
            id="L0_id", name="Roads",
            source="../Carto/roads.shp|subset=--&amp;quot;Id&amp;quot; ILIKE 'VS15'")
        qgs = QGS_TREE_TEMPLATE.format(
            tree=TREE_GROUP.format(name="Sectores", layer=treeLayer),
            layers=MAPLAYER_WITH_ID.format(
                id="L0_id", name="Roads",
                datasource="../Carto/roads.shp|subset=--&quot;Id&quot; ILIKE 'VS15'"),
        )
        with ZipFile(os.path.join(projectDir, NET + ".qgz"), "w", ZIP_DEFLATED) as zout:
            zout.writestr(NET + ".qgs", qgs)
        _touch(os.path.join(projectDir, NET + "_Metadata.txt"),
               METADATA_TEMPLATE.format(qgis=NET + ".qgz"))

        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems

        assert len(items) == 1
        assert items[0].placements == [(("Sectores",), "Roads")]

    def test_a_layer_outside_any_group_sits_at_the_root(self, workspace):
        _touch(os.path.join(workspace, "Carto", "roads.shp"))
        projectDir, _ = self._project(workspace, [((), "Roads", "../Carto/roads.shp")])
        items = QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems
        assert items[0].placements == [((), "Roads")]

    def test_the_projects_own_layers_never_reach_the_tree(self, workspace):
        projectDir, _ = self._project(workspace, [
            (("Datos",), "Pipes", "./" + NET + "_Pipes.shp"),
        ])
        assert QGISRedProjectPackage(projectDir, NET).inspectForExport().externalItems == []


class TestContentGroups:
    def test_only_groups_with_data_are_detected(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project", groups=["Results", "Issues"])
        os.makedirs(os.path.join(projectDir, "Queries"))                      # exists but empty
        _touch(os.path.join(projectDir, "Auxiliary Layers", "Other_Foo.shp"))  # another network
        groups = {g.key: g for g in QGISRedProjectPackage(projectDir, NET).inspectContentGroups()}

        assert groups["results"].exists and groups["results"].fileCount == 1
        assert groups["results"].sizeBytes > 0
        assert groups["issues"].exists
        assert not groups["queries"].exists
        assert not groups["auxiliary"].exists

    def test_nested_folders_count_towards_their_parent_group(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "Issues", "Connectivity", NET + "_Connectivity.shp"))
        groups = {g.key: g for g in QGISRedProjectPackage(projectDir, NET).inspectContentGroups()}
        assert groups["issues"].exists and groups["issues"].fileCount == 1

    def test_backups_is_never_a_content_group(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "backups", NET + "_123.zip"))
        groups = QGISRedProjectPackage(projectDir, NET).inspectContentGroups()
        assert "backups" not in [g.dirName for g in groups]
        assert all(not g.exists for g in groups)

    def test_an_unexpected_folder_is_discovered_and_offered(self, workspace):
        """Real case: the DLL renamed its output folder, so a project can carry both
        "Auxiliary Layers" and a legacy "AuxiliaryLayers". A hardcoded list of four names would
        ship the legacy one with no checkbox, no way to leave it out and no weight in the total."""
        projectDir, _ = _makeProject(workspace, qgzAt="project", groups=["Auxiliary Layers"])
        _touch(os.path.join(projectDir, "AuxiliaryLayers", "DemandSectors",
                            NET + "_DemSect_Frontiers.shp"))
        groups = {g.key: g for g in QGISRedProjectPackage(projectDir, NET).inspectContentGroups()}

        assert "AuxiliaryLayers" in groups
        assert groups["AuxiliaryLayers"].exists
        assert groups["AuxiliaryLayers"].fileCount == 1
        # and it did not get merged into the known, differently spelled group
        assert groups["auxiliary"].dirName == "Auxiliary Layers"
        assert groups["auxiliary"].fileCount == 1

    def test_the_known_groups_are_always_listed_even_when_empty(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        groups = QGISRedProjectPackage(projectDir, NET).inspectContentGroups()
        assert [g.key for g in groups] == ["results", "issues", "queries", "auxiliary"]
        assert all(not g.exists for g in groups)

    def test_a_stray_folder_without_project_files_is_not_offered(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "notes", "readme.txt"))
        _touch(os.path.join(projectDir, "OtherNet", "OtherNet_Pipes.shp"))
        keys = [g.key for g in QGISRedProjectPackage(projectDir, NET).inspectContentGroups()]
        assert "notes" not in keys        # no files of this network
        assert "OtherNet" not in keys     # files, but of another network

    def test_backups_is_never_discovered(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "backups", NET + "_123.zip"))
        keys = [g.key for g in QGISRedProjectPackage(projectDir, NET).inspectContentGroups()]
        assert "backups" not in keys

    def test_a_discovered_group_can_be_excluded(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "AuxiliaryLayers", NET + "_DemSect.shp"))
        zipPath = os.path.join(workspace, "out", "export.zip")
        package = QGISRedProjectPackage(projectDir, NET)

        ok, reason, manifest = package.exportToZip(zipPath, includeGroups=set())
        assert ok, reason
        with ZipFile(zipPath, "r") as z:
            names = z.namelist()
        assert not any(name.startswith("AuxiliaryLayers/") for name in names)
        assert "AuxiliaryLayers" in manifest["omittedGroups"]
        assert NET + "_Pipes.shp" in names   # base layers still travel

    def test_base_files_are_counted_apart(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project", groups=["Results"])
        plan = QGISRedProjectPackage(projectDir, NET).inspectForExport()
        # Net_Pipes.shp + Net_Pipes.dbf + Net_Junctions.shp + Net_Metadata.txt
        assert plan.baseFileCount == 4
        assert plan.baseSizeBytes > 0


class TestExportToZip:
    def _export(self, projectDir, workspace, **kwargs):
        zipPath = os.path.join(workspace, "out", "export.zip")
        package = QGISRedProjectPackage(projectDir, NET)
        ok, reason, manifest = package.exportToZip(zipPath, **kwargs)
        assert ok, reason
        with ZipFile(zipPath, "r") as z:
            names = z.namelist()
        return zipPath, names, manifest

    def test_structure_a_layout(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _zipPath, names, manifest = self._export(projectDir, workspace)

        assert NET + "_Pipes.shp" in names
        assert NET + ".qgz" in names
        assert MANIFEST_NAME in names
        assert not any(".." in name for name in names)
        assert not any(name.startswith("ExternalLayers/") for name in names)
        assert manifest["structure"] == STRUCTURE_PROJECT
        assert manifest["projectFolder"] == ""
        assert manifest["schema"] == SCHEMA_VERSION

    def test_structure_b_keeps_the_qgz_at_the_root(self, workspace):
        """Regression: with the .qgz one level up the old code wrote it outside the staging
        folder (relpath == '..') and it silently never made it into the ZIP."""
        projectDir, _ = _makeProject(workspace, qgzAt="parent")
        _zipPath, names, manifest = self._export(projectDir, workspace)

        assert NET + ".qgz" in names
        assert NET + "/" + NET + "_Pipes.shp" in names
        assert manifest["structure"] == STRUCTURE_PARENT
        assert manifest["projectFolder"] == NET
        assert manifest["qgisProject"] == NET + ".qgz"

    def test_a_qgz_in_a_project_subfolder_keeps_its_subfolder(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="subfolder")
        _zipPath, names, manifest = self._export(projectDir, workspace)
        assert "map/" + NET + ".qgz" in names
        assert manifest["qgisProject"] == "map/" + NET + ".qgz"

    def test_backups_are_never_exported(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        _touch(os.path.join(projectDir, "backups", NET + "_123.zip"))
        _zipPath, names, _manifest = self._export(projectDir, workspace)
        assert not any("backups" in name for name in names)

    def test_omitting_a_content_group_leaves_the_rest_intact(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project", groups=["Results", "Issues"])
        _zipPath, names, manifest = self._export(projectDir, workspace, includeGroups={"issues"})

        assert not any(name.startswith("Results/") for name in names)
        assert "Issues/" + NET + "_Issues.shp" in names
        assert NET + "_Pipes.shp" in names
        assert manifest["omittedGroups"] == ["results"]
        assert manifest["includedGroups"] == ["issues"]

    def test_including_every_group_exports_them_all(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project", groups=["Results", "Queries"])
        _zipPath, names, manifest = self._export(projectDir, workspace)
        assert "Results/" + NET + "_Results.shp" in names
        assert "Queries/" + NET + "_Queries.shp" in names
        assert manifest["omittedGroups"] == []

    def test_external_data_is_staged_and_the_qgz_points_at_it_relatively(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        zipPath, names, manifest = self._export(projectDir, workspace)

        assert "DTM/mdt.tif" in names
        assert manifest["includesExternalData"] is True
        assert manifest["externalData"] == [{"path": "DTM/mdt.tif", "type": "file", "layers": ["MDT"]}]

        extracted = os.path.join(workspace, "check")
        with ZipFile(zipPath, "r") as z:
            z.extractall(extracted)  # nosec B202 — archive built by this test
        assert _readQgzDatasources(os.path.join(extracted, NET, NET + ".qgz")) == ["../DTM/mdt.tif"]

    def test_excluded_external_data_keeps_an_absolute_path_in_the_qgz(self, workspace):
        dtm = _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        zipPath, names, manifest = self._export(projectDir, workspace, includeExternal=False)

        assert not any(name.startswith("DTM/") for name in names)
        assert manifest["includesExternalData"] is False

        extracted = os.path.join(workspace, "check")
        with ZipFile(zipPath, "r") as z:
            z.extractall(extracted)  # nosec B202 — archive built by this test
        values = _readQgzDatasources(os.path.join(extracted, NET + ".qgz"))
        assert values == [dtm.replace(os.sep, "/")]

    def test_out_of_scope_external_data_is_reported_and_skipped(self, workspace):
        # Resolved like the workspace fixture: the exporter reports resolved paths, and on a
        # platform where the temp folder is reached through a link the raw one never matches.
        other = os.path.realpath(tempfile.mkdtemp())
        try:
            far = _touch(os.path.join(other, "ortho.tif"))
            projectDir, _ = _makeProject(workspace, qgzAt="project",
                                         datasources=[(far.replace(os.sep, "/"), "Ortho")])
            _zipPath, names, manifest = self._export(projectDir, workspace)

            assert not any("ortho.tif" in name for name in names)
            assert manifest["skippedExternalData"] == [
                {"source": far, "layers": ["Ortho"], "reason": REASON_EXTERNAL_OUTSIDE}
            ]
        finally:
            shutil.rmtree(other, ignore_errors=True)

    def test_third_party_file_inside_the_project_folder_travels(self, workspace):
        """It is not named <Net>_*, so processProjectFiles skips it; the external pass must not."""
        _touch(os.path.join(workspace, NET, "extra", "background.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("extra/background.tif", "Background")])
        _zipPath, names, manifest = self._export(projectDir, workspace)
        assert "extra/background.tif" in names
        assert manifest["structure"] == STRUCTURE_PROJECT

    def test_metadata_points_at_the_qgz_after_extraction(self, workspace):
        """End-to-end: a structure-B package must resolve its own .qgz once extracted."""
        projectDir, _ = _makeProject(workspace, qgzAt="parent")
        zipPath, _names, _manifest = self._export(projectDir, workspace)

        extracted = os.path.join(workspace, "restored")
        with ZipFile(zipPath, "r") as z:
            z.extractall(extracted)  # nosec B202 — archive built by this test

        from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO
        restoredProject = os.path.join(extracted, NET)
        io = QGISRedProjectIO(restoredProject, NET)
        base = io.getQGisProjectBase(restoredProject, NET)
        assert norm(io.findQGisProjectFile(base)) == norm(os.path.join(extracted, NET + ".qgz"))

        # The stored path must use forward slashes, or the package would not open on another platform
        with open(os.path.join(restoredProject, NET + "_Metadata.txt"), encoding="latin-1") as f:
            assert "<QGisProject>../" + NET + ".qgz</QGisProject>" in f.read()

    def test_a_project_without_a_qgz_still_exports_its_data(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt=None)
        _zipPath, names, manifest = self._export(projectDir, workspace)
        assert NET + "_Pipes.shp" in names
        assert manifest["qgisProject"] is None
        assert not any(name.endswith(".qgz") for name in names)

    def test_a_blocked_plan_reports_instead_of_writing(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="outside")
        zipPath = os.path.join(workspace, "out", "export.zip")
        ok, reason, manifest = QGISRedProjectPackage(projectDir, NET).exportToZip(zipPath)
        assert not ok
        assert reason == REASON_QGZ_OUTSIDE
        assert manifest is None
        assert not os.path.exists(zipPath)

    def test_no_partial_file_is_left_behind_on_success(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        zipPath, _names, _manifest = self._export(projectDir, workspace)
        assert not os.path.exists(zipPath + ".part")

    def test_manifest_is_valid_json_with_the_expected_keys(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="project")
        zipPath, _names, manifest = self._export(projectDir, workspace)
        with ZipFile(zipPath, "r") as z:
            stored = json.loads(z.read(MANIFEST_NAME).decode("utf-8"))
        assert stored == manifest
        for key in ("schema", "generator", "structure", "networkName", "projectFolder",
                    "qgisProject", "includedGroups", "omittedGroups", "includesExternalData",
                    "externalData", "skippedExternalData"):
            assert key in stored


class TestFileNameHelpers:
    @pytest.mark.parametrize("raw,expected", [
        ("Net", "Net"),
        ("Net.zip", "Net"),
        ("  Net  ", "Net"),
        ('a<>:"/\\|?*b', "ab"),
        ("Net.", "Net"),
        ("NUL", ""),
        ("com1", ""),
        ("LPT9", ""),
        ("", ""),
        (None, ""),
    ])
    def test_sanitize(self, raw, expected):
        assert QGISRedProjectPackage.sanitizeZipFileName(raw) == expected

    def test_build_zip_path_appends_the_extension_once(self):
        assert QGISRedProjectPackage.buildZipPath("/tmp", "Net") == os.path.join("/tmp", "Net.zip")
        assert QGISRedProjectPackage.buildZipPath("/tmp", "Net.zip") == os.path.join("/tmp", "Net.zip")

    def test_build_zip_path_is_empty_when_unusable(self):
        assert QGISRedProjectPackage.buildZipPath("/tmp", "NUL") == ""
        assert QGISRedProjectPackage.buildZipPath("", "Net") == ""


class TestPerLayerExternalSelection:
    """Complementary data is not all-or-nothing: a 2 GB DTM can be left out while the small
    cartography still travels."""

    def _twoExternals(self, workspace):
        dtm = _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        roads = _touch(os.path.join(workspace, "Carto", "roads.shp"))
        projectDir, _ = _makeProject(workspace, qgzAt="project", datasources=[
            ("../DTM/mdt.tif", "MDT"),
            ("../Carto/roads.shp", "Roads"),
        ])
        return projectDir, dtm, roads

    def test_only_the_selected_layer_is_exported(self, workspace):
        projectDir, _dtm, roads = self._twoExternals(workspace)
        zipPath = os.path.join(workspace, "out", "export.zip")
        package = QGISRedProjectPackage(projectDir, NET)
        ok, reason, manifest = package.exportToZip(zipPath, externalSources={roads})
        assert ok, reason

        with ZipFile(zipPath, "r") as z:
            names = z.namelist()
        assert "Carto/roads.shp" in names
        assert not any(name.startswith("DTM/") for name in names)
        assert manifest["externalData"] == [
            {"path": "Carto/roads.shp", "type": "file", "layers": ["Roads"]}
        ]
        assert [s["reason"] for s in manifest["skippedExternalData"]] == [REASON_EXTERNAL_EXCLUDED]
        assert manifest["includesExternalData"] is True

    def test_deselecting_the_only_sibling_collapses_to_structure_a(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        package = QGISRedProjectPackage(projectDir, NET)
        plan = package.inspectForExport()
        assert plan.structure == STRUCTURE_PARENT

        package.applySelection(plan, True, plan.includeGroups, externalSources=set())
        assert plan.structure == STRUCTURE_PROJECT
        assert plan.selectedExternalItems == []
        assert plan.includeExternal is False

    def test_the_estimate_follows_the_selection(self, workspace):
        projectDir, dtm, roads = self._twoExternals(workspace)
        package = QGISRedProjectPackage(projectDir, NET)
        plan = package.inspectForExport()
        both = plan.selectedSizeBytes()

        package.applySelection(plan, True, plan.includeGroups, externalSources={roads})
        onlyRoads = plan.selectedSizeBytes()
        package.applySelection(plan, True, plan.includeGroups, externalSources=set())
        none = plan.selectedSizeBytes()

        assert none < onlyRoads < both
        assert none == plan.baseSizeBytes + sum(
            g.sizeBytes for g in plan.contentGroups if g.key in plan.includeGroups
        )
        assert os.path.exists(dtm)  # nothing was moved or removed by planning

    def test_the_gate_wins_over_the_per_layer_ticks(self, workspace):
        """The dialog's "include complementary data" checkbox disables the tree but keeps the ticks,
        so the engine must export nothing when it is off, whatever selection it is handed."""
        projectDir, _dtm, roads = self._twoExternals(workspace)
        package = QGISRedProjectPackage(projectDir, NET)
        plan = package.inspectForExport()

        package.applySelection(plan, False, plan.includeGroups, externalSources={roads})

        assert plan.selectedExternalItems == []
        assert plan.includeExternal is False
        assert plan.structure == STRUCTURE_PROJECT   # no sibling travels, so no need for B

    def test_out_of_scope_items_can_never_be_selected(self, workspace):
        # Resolved like the workspace fixture: the exporter reports resolved paths, and on a
        # platform where the temp folder is reached through a link the raw one never matches.
        other = os.path.realpath(tempfile.mkdtemp())
        try:
            far = _touch(os.path.join(other, "ortho.tif"))
            projectDir, _ = _makeProject(workspace, qgzAt="project",
                                         datasources=[(far.replace(os.sep, "/"), "Ortho")])
            package = QGISRedProjectPackage(projectDir, NET)
            plan = package.inspectForExport()
            # Even asking for it explicitly must not select it
            package.applySelection(plan, True, plan.includeGroups, externalSources={far})
            assert plan.selectedExternalItems == []
        finally:
            shutil.rmtree(other, ignore_errors=True)


def _writeZip(path, entries):
    """entries: {memberName: content}"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with ZipFile(path, "w", ZIP_DEFLATED) as zout:
        for name, content in entries.items():
            zout.writestr(name, content)
    return path


class TestInspectZip:
    def test_a_manifest_makes_the_layout_explicit(self, workspace):
        projectDir, _ = _makeProject(workspace, qgzAt="parent")
        zipPath = os.path.join(workspace, "out", "export.zip")
        ok, reason, manifest = QGISRedProjectPackage(projectDir, NET).exportToZip(zipPath)
        assert ok, reason

        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        assert inspection.isValid
        assert inspection.manifest is not None
        assert inspection.structure == STRUCTURE_PARENT
        assert inspection.projectFolderRel == NET
        assert inspection.networkName == NET
        assert inspection.qgisProjectRel == NET + ".qgz"
        assert inspection.rootPrefix == ""
        assert manifest["structure"] == inspection.structure

    def test_external_data_is_listed_with_its_size(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"), "x" * 500)
        projectDir, _ = _makeProject(workspace, qgzAt="project",
                                     datasources=[("../DTM/mdt.tif", "MDT")])
        zipPath = os.path.join(workspace, "out", "export.zip")
        assert QGISRedProjectPackage(projectDir, NET).exportToZip(zipPath)[0]

        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        assert inspection.hasExternalData
        assert inspection.externalRel == ["DTM/mdt.tif"]
        assert inspection.externalSizeBytes == 500
        assert inspection.projectSizeBytes > 0

    def test_a_legacy_flat_zip_is_read_as_structure_a(self, workspace):
        """What older versions produced: a flat archive, no manifest, ExternalLayers inside."""
        zipPath = _writeZip(os.path.join(workspace, "legacy.zip"), {
            NET + "_Pipes.shp": "x",
            NET + "_Metadata.txt": METADATA_TEMPLATE.format(qgis=NET + ".qgz"),
            NET + ".qgz": "x",
            "ExternalLayers/ortho.tif": "x",
        })
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        assert inspection.isValid
        assert inspection.manifest is None
        assert inspection.structure == STRUCTURE_PROJECT
        assert inspection.projectFolderRel == ""
        assert inspection.networkName == NET
        assert inspection.qgisProjectRel == NET + ".qgz"
        # ExternalLayers is part of the project folder in a flat archive, not separate data
        assert inspection.externalRel == []

    def test_a_rooted_zip_without_a_manifest_is_read_as_structure_b(self, workspace):
        zipPath = _writeZip(os.path.join(workspace, "rooted.zip"), {
            NET + "/" + NET + "_Pipes.shp": "x",
            NET + "/" + NET + "_Metadata.txt": METADATA_TEMPLATE.format(qgis="../" + NET + ".qgz"),
            NET + ".qgz": "x",
            "DTM/mdt.tif": "x",
        })
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        assert inspection.isValid
        assert inspection.structure == STRUCTURE_PARENT
        assert inspection.projectFolderRel == NET
        assert inspection.qgisProjectRel == NET + ".qgz"
        assert inspection.externalRel == ["DTM"]

    def test_a_re_wrapped_archive_keeps_its_internal_layout(self, workspace):
        """Someone extracted an export and zipped the folder again, so everything sits one level
        deeper. The relative layout is intact, so the paths just gain the wrapper prefix."""
        projectDir, _ = _makeProject(workspace, qgzAt="parent")
        plain = os.path.join(workspace, "out", "export.zip")
        assert QGISRedProjectPackage(projectDir, NET).exportToZip(plain)[0]
        with ZipFile(plain, "r") as zin:
            entries = {"wrapper/" + name: zin.read(name) for name in zin.namelist()}
        rewrapped = _writeZip(os.path.join(workspace, "out", "rewrapped.zip"), entries)

        inspection = QGISRedProjectPackage.inspectZip(rewrapped)
        assert inspection.isValid
        assert inspection.rootPrefix == "wrapper/"
        assert inspection.projectFolderRel == "wrapper/" + NET
        assert inspection.qgisProjectRel == "wrapper/" + NET + ".qgz"

    def test_an_archive_without_a_project_is_rejected(self, workspace):
        zipPath = _writeZip(os.path.join(workspace, "junk.zip"), {"readme.txt": "nothing here"})
        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        assert not inspection.isValid
        assert inspection.reason == REASON_NO_PIPES_IN_ZIP

    def test_a_future_schema_is_refused_rather_than_guessed(self, workspace):
        zipPath = _writeZip(os.path.join(workspace, "future.zip"), {
            NET + "_Pipes.shp": "x",
            MANIFEST_NAME: json.dumps({"schema": SCHEMA_VERSION + 1, "networkName": NET}),
        })
        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        assert not inspection.isValid
        assert inspection.reason == REASON_SCHEMA_TOO_NEW

    @pytest.mark.parametrize("member", ["../evil.txt", "a/../../evil.txt", "/etc/evil"])
    def test_an_escaping_member_rejects_the_whole_archive(self, workspace, member):
        zipPath = _writeZip(os.path.join(workspace, "evil.zip"), {
            NET + "_Pipes.shp": "x",
            member: "pwned",
        })
        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        assert not inspection.isValid
        assert inspection.reason == REASON_UNSAFE_MEMBER

    def test_a_missing_file_is_reported_not_raised(self, workspace):
        inspection = QGISRedProjectPackage.inspectZip(os.path.join(workspace, "nope.zip"))
        assert not inspection.isValid
        assert inspection.reason


class TestExtractZip:
    def _exported(self, workspace, qgzAt, datasources=(), groups=()):
        projectDir, _ = _makeProject(workspace, qgzAt=qgzAt, datasources=datasources, groups=groups)
        zipPath = os.path.join(workspace, "out", "export.zip")
        ok, reason, _manifest = QGISRedProjectPackage(projectDir, NET).exportToZip(zipPath)
        assert ok, reason
        return zipPath

    def test_structure_a_lands_directly_in_the_destination(self, workspace):
        zipPath = self._exported(workspace, "project")
        dest = os.path.join(workspace, "dest")
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        projectDir = QGISRedProjectPackage.extractZip(zipPath, dest, inspection)

        assert norm(projectDir) == norm(dest)
        assert os.path.isfile(os.path.join(dest, NET + "_Pipes.shp"))
        assert os.path.isfile(os.path.join(dest, NET + ".qgz"))
        assert not os.path.exists(os.path.join(dest, MANIFEST_NAME))

    def test_structure_b_rebuilds_the_sibling_folders(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        # The .qgz sits in the parent folder, so its datasources are relative to it
        zipPath = self._exported(workspace, "parent", datasources=[("DTM/mdt.tif", "MDT")])
        dest = os.path.join(workspace, "dest")
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        projectDir = QGISRedProjectPackage.extractZip(zipPath, dest, inspection)

        assert norm(projectDir) == norm(os.path.join(dest, NET))
        assert os.path.isfile(os.path.join(dest, NET, NET + "_Pipes.shp"))
        assert os.path.isfile(os.path.join(dest, NET + ".qgz"))
        assert os.path.isfile(os.path.join(dest, "DTM", "mdt.tif"))

    def test_external_data_can_be_left_out_without_touching_the_project(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        # The .qgz sits in the parent folder, so its datasources are relative to it
        zipPath = self._exported(workspace, "parent", datasources=[("DTM/mdt.tif", "MDT")])
        dest = os.path.join(workspace, "dest")
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        QGISRedProjectPackage.extractZip(zipPath, dest, inspection, includeExternal=False)

        assert not os.path.exists(os.path.join(dest, "DTM"))
        assert os.path.isfile(os.path.join(dest, NET, NET + "_Pipes.shp"))
        assert os.path.isfile(os.path.join(dest, NET + ".qgz"))

    def test_the_round_trip_leaves_the_project_openable(self, workspace):
        """The whole point: after extracting, the metadata must resolve its own .qgz."""
        from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO
        zipPath = self._exported(workspace, "parent", groups=["Results"])
        dest = os.path.join(workspace, "dest")
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        projectDir = QGISRedProjectPackage.extractZip(zipPath, dest, inspection)

        io = QGISRedProjectIO(projectDir, NET)
        base = io.getQGisProjectBase(projectDir, NET)
        assert norm(io.findQGisProjectFile(base)) == norm(os.path.join(dest, NET + ".qgz"))
        assert os.path.isfile(os.path.join(projectDir, "Results", NET + "_Results.shp"))

    def test_conflicts_are_reported_before_anything_is_written(self, workspace):
        zipPath = self._exported(workspace, "project")
        dest = os.path.join(workspace, "dest")
        existing = _touch(os.path.join(dest, NET + "_Pipes.shp"), "do not lose me")

        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        _targets, conflicts = QGISRedProjectPackage.planExtraction(inspection, dest)

        assert NET + "_Pipes.shp" in conflicts
        with open(existing, encoding="utf-8") as f:
            assert f.read() == "do not lose me"  # planning must not write

    def test_no_conflicts_in_a_clean_destination(self, workspace):
        zipPath = self._exported(workspace, "project")
        inspection = QGISRedProjectPackage.inspectZip(zipPath)
        _targets, conflicts = QGISRedProjectPackage.planExtraction(
            inspection, os.path.join(workspace, "clean"))
        assert conflicts == []

    def test_omitted_external_data_is_not_reported_as_a_conflict(self, workspace):
        _touch(os.path.join(workspace, "DTM", "mdt.tif"))
        # The .qgz sits in the parent folder, so its datasources are relative to it
        zipPath = self._exported(workspace, "parent", datasources=[("DTM/mdt.tif", "MDT")])
        dest = os.path.join(workspace, "dest")
        _touch(os.path.join(dest, "DTM", "mdt.tif"))
        inspection = QGISRedProjectPackage.inspectZip(zipPath)

        _targets, withExternal = QGISRedProjectPackage.planExtraction(inspection, dest, True)
        _targets, without = QGISRedProjectPackage.planExtraction(inspection, dest, False)

        assert "DTM/mdt.tif" in withExternal
        assert without == []


class TestExportDialogWiring:
    """The dialog itself cannot be instantiated (conftest stubs loadUiType, so every widget is a
    MagicMock and any assertion would be vacuous). These check the two invariants that would
    otherwise only blow up at runtime: the checkbox map and the .ui widget names."""

    def test_the_ui_declares_every_widget_the_dialog_uses(self):
        import re
        uiPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "ui", "general", "qgisred_exportproject_dialog.ui")
        with open(uiPath, encoding="utf-8") as f:
            declared = set(re.findall(r'name="(\w+)"', f.read()))
        needed = {
            "tbZipName", "tbTargetFolder", "btSelectFolder", "cbOpenFolder", "buttonBox",
            "lbBaseLayers", "gbContent", "verticalLayoutContent",
            "gbExternal", "cbIncludeExternalData", "twExternalData",
            "lbStructure", "lbSizeEstimate", "verticalLayout",
        }
        assert not needed - declared

    def test_the_group_checkboxes_are_not_declared_in_the_ui(self):
        """They are created per project from the discovered folders, so hardcoding them would
        silently drop any folder that is not one of the four known names."""
        import re
        uiPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "ui", "general", "qgisred_exportproject_dialog.ui")
        with open(uiPath, encoding="utf-8") as f:
            declared = set(re.findall(r'name="(\w+)"', f.read()))
        assert not declared & {"cbResults", "cbIssues", "cbQueries", "cbAuxiliary"}


class TestImportTabWiring:
    """The import dialog cannot be instantiated either (stubbed loadUiType), so pin the two things
    that would only fail at runtime: the .ui widget names and the reason-to-message mapping."""

    def test_the_ui_declares_every_widget_the_zip_tab_uses(self):
        import re
        uiPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "ui", "general", "qgisred_import_dialog.ui")
        with open(uiPath, encoding="utf-8") as f:
            declared = set(re.findall(r'name="(\w+)"', f.read()))
        needed = {"tbZipFile", "btSelectZip", "btImportProject", "lbZipInfo",
                  "cbImportExternalData", "cbCreateSubfolder"}
        assert not needed - declared

    def test_every_invalid_reason_has_its_own_message(self):
        from QGISRed.ui.general.qgisred_import_dialog import QGISRedImportDialog
        dialog = QGISRedImportDialog.__new__(QGISRedImportDialog)
        dialog.tr = lambda text: text
        messages = {
            reason: QGISRedImportDialog.zipReasonMessage(dialog, reason)
            for reason in (REASON_NO_PIPES_IN_ZIP, REASON_SCHEMA_TOO_NEW, REASON_UNSAFE_MEMBER)
        }
        assert len(set(messages.values())) == 3       # no reason falls through to another's text
        assert all(messages.values())
        # An unknown reason still says something useful rather than crashing
        assert "boom" in QGISRedImportDialog.zipReasonMessage(dialog, "boom")

    def test_the_old_fragile_import_path_is_gone(self):
        """The rewrite dropped the extract-to-temp-then-copy round trip and the two private
        tempfile APIs it relied on."""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "general", "qgisred_import_dialog.py")
        with open(path, encoding="utf-8") as f:
            source = f.read()
        for forbidden in ("_get_default_tempdir", "_get_candidate_names", "copyFolderFiles"):
            assert forbidden not in source


class TestBackupIsGone:
    """"Project backup" was removed and Export does not take its place in the menu: exporting lives
    only in the Project Manager. The menu is built in initGui() and needs a live iface, so its
    contents are checked statically."""

    def _sectionsFolder(self):
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sections")

    def test_the_backup_command_is_gone(self):
        from QGISRed.sections.project_management_section import ProjectManagementSection
        assert not hasattr(ProjectManagementSection, "runCreateBackup")
        assert hasattr(ProjectManagementSection, "runExportProjectFor")

    def test_the_project_menu_offers_neither_backup_nor_export(self):
        with open(os.path.join(self._sectionsFolder(), "menu_section.py"), encoding="utf-8") as f:
            source = f.read()
        assert "runCreateBackup" not in source
        assert "Project backup" not in source
        assert "runExportProject" not in source

    def test_the_project_manager_is_the_only_entry_point(self):
        from QGISRed.ui.general.qgisred_projectmanager_dialog import QGISRedProjectManagerDialog
        assert "runExportProjectFor" in QGISRedProjectManagerDialog.exportData.__code__.co_names


class TestFileSystemHelpers:
    def test_downloads_folder_falls_back_to_an_existing_folder(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
        assert os.path.isdir(QGISRedFileSystemUtils().getDownloadsFolder())

    def test_plugin_version_is_read_from_metadata(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
        QGISRedFileSystemUtils._pluginVersion = None
        version = QGISRedFileSystemUtils().getPluginVersion()
        assert version and version[0].isdigit()

    @pytest.mark.parametrize("size,expected", [
        (0, "0 B"),
        (512, "512 B"),
        (1024, "1.0 KB"),
        (1536, "1.5 KB"),
        (5 * 1024 * 1024, "5.0 MB"),
        (3 * 1024 ** 3, "3.0 GB"),
        (4096 * 1024 ** 3, "4096.0 GB"),  # never overflows past GB
    ])
    def test_format_size(self, size, expected):
        from QGISRed.tools.utils.qgisred_ui_utils import QGISRedUIUtils
        assert QGISRedUIUtils.formatSize(size) == expected
