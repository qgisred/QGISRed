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
        other = tempfile.mkdtemp()
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
        other = tempfile.mkdtemp()
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

    def test_out_of_scope_items_can_never_be_selected(self, workspace):
        other = tempfile.mkdtemp()
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


class TestExportDialogWiring:
    """The dialog itself cannot be instantiated (conftest stubs loadUiType, so every widget is a
    MagicMock and any assertion would be vacuous). These check the two invariants that would
    otherwise only blow up at runtime: the checkbox map and the .ui widget names."""

    def test_every_content_group_has_a_checkbox(self):
        from QGISRed.tools.utils.qgisred_project_export import CONTENT_GROUPS
        from QGISRed.ui.general.qgisred_exportproject_dialog import GROUP_CHECKBOXES
        assert sorted(GROUP_CHECKBOXES) == sorted(key for key, _dirName in CONTENT_GROUPS)

    def test_the_ui_declares_every_widget_the_dialog_uses(self):
        import re
        uiPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "ui", "general", "qgisred_exportproject_dialog.ui")
        with open(uiPath, encoding="utf-8") as f:
            declared = set(re.findall(r'name="(\w+)"', f.read()))
        needed = {
            "tbZipName", "tbTargetFolder", "btSelectFolder", "cbOpenFolder", "buttonBox",
            "lbBaseLayers", "cbResults", "cbIssues", "cbQueries", "cbAuxiliary",
            "gbExternal", "cbIncludeExternalData", "twExternalData",
            "lbStructure", "lbSizeEstimate", "verticalLayout",
        }
        assert not needed - declared


class TestFileSystemHelpers:
    def test_downloads_folder_falls_back_to_an_existing_folder(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
        assert os.path.isdir(QGISRedFileSystemUtils().getDownloadsFolder())

    def test_plugin_version_is_read_from_metadata(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
        QGISRedFileSystemUtils._pluginVersion = None
        version = QGISRedFileSystemUtils().getPluginVersion()
        assert version and version[0].isdigit()
