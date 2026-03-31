# -*- coding: utf-8 -*-
import pytest
import sys
import os
import shutil
import tempfile
from zipfile import ZipFile
from unittest.mock import MagicMock, patch

# Add plugin root to sys.path
_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

# Mock QGIS and PyQt5
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['PyQt5'] = MagicMock()
sys.modules['PyQt5.QtCore'] = MagicMock()
sys.modules['PyQt5.QtWidgets'] = MagicMock()

from tools.utils.qgisred_project_io import QGISRedProjectIO

class TestProjectIO:
    @pytest.fixture
    def temp_project_dir(self):
        dirpath = tempfile.mkdtemp()
        yield dirpath
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)

    @pytest.fixture
    def io_utils(self, temp_project_dir):
        return QGISRedProjectIO(directory=temp_project_dir, networkName="testNet")

    def test_addProjectToGplFile_new_file(self, io_utils, temp_project_dir):
        gpl_file = os.path.join(temp_project_dir, "projects.gpl")
        io_utils.addProjectToGplFile(gpl_file, networkName="Net1", projectDirectory="C:/dir1")
        
        with open(gpl_file, "r") as f:
            lines = f.readlines()
        
        assert len(lines) == 1
        assert "Net1;" in lines[0]

    def test_addProjectToGplFile_append_and_reorder(self, io_utils, temp_project_dir):
        gpl_file = os.path.join(temp_project_dir, "projects.gpl")
        
        # Existing entries
        with open(gpl_file, "w") as f:
            f.write("OldNet;C:/old\n")
            f.write("OtherNet;C:/other\n")
            
        new_dir = "C:/new"
        expected_dir = os.path.normpath(new_dir)
        io_utils.addProjectToGplFile(gpl_file, networkName="NetNew", projectDirectory=new_dir)
        
        with open(gpl_file, "r") as f:
            lines = [line.strip() for line in f.readlines()]
        
        # New entry should be FIRST
        assert lines[0] == f"NetNew;{expected_dir}"
        assert lines[1] == "OldNet;C:/old"
        assert lines[2] == "OtherNet;C:/other"

    def test_saveFilesInZip(self, io_utils, temp_project_dir):
        # Create some files in project dir
        with open(os.path.join(temp_project_dir, "testNet_data.shp"), "w") as f:
            f.write("data")
        with open(os.path.join(temp_project_dir, "other.txt"), "w") as f:
            f.write("other")
            
        zip_path = os.path.join(temp_project_dir, "backup.zip")
        
        # We need to mock _fs() to return a mock that handles getUniformedPath
        mock_fs = MagicMock()
        mock_fs.getUniformedPath.side_effect = lambda x: x.replace("/", os.sep)
        
        with patch.object(QGISRedProjectIO, '_fs', return_value=mock_fs):
            io_utils.saveFilesInZip(zip_path)
        
        assert os.path.exists(zip_path)
        with ZipFile(zip_path, "r") as z:
            names = z.namelist()
            # Only files starting with NetworkName_ should be included
            # Check the logic in saveFilesInZip:
            # if fs.getUniformedPath(self.ProjectDirectory) + "\\" + self.NetworkName + "_" in file:
            assert any("testNet_data.shp" in n for n in names)
            assert not any("other.txt" in n for n in names)

    def test_unzipFile(self, io_utils, temp_project_dir):
        # Create a zip
        zip_path = os.path.join(temp_project_dir, "test.zip")
        extract_dir = os.path.join(temp_project_dir, "extracted")
        os.mkdir(extract_dir)
        
        with ZipFile(zip_path, "w") as z:
            z.writestr("file1.txt", "content1")
            
        io_utils.unzipFile(zip_path, extract_dir)
        
        assert os.path.exists(os.path.join(extract_dir, "file1.txt"))
        with open(os.path.join(extract_dir, "file1.txt"), "r") as f:
            assert f.read() == "content1"

    def test_getProjectGuid_from_metadata(self, io_utils, temp_project_dir):
        metadata_file = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        guid = "1234-abcd-5678"
        xml_content = f"""<Project><Guid>{guid}</Guid></Project>"""
        with open(metadata_file, "w") as f:
            f.write(xml_content)
            
        assert io_utils.getProjectGuid() == guid

    def test_getProjectGuid_fallback(self, io_utils):
        # Metadata doesn't exist
        assert io_utils.getProjectGuid() == "testNet"

    # ------------------------------------------------------------------ #
    # stripAllExtensions
    # ------------------------------------------------------------------ #

    def test_stripAllExtensions_no_extension(self, io_utils):
        assert io_utils.stripAllExtensions("foo") == "foo"

    def test_stripAllExtensions_single(self, io_utils):
        assert io_utils.stripAllExtensions("foo.shp") == "foo"

    def test_stripAllExtensions_multiple(self, io_utils):
        assert io_utils.stripAllExtensions("foo.qgz.bak") == "foo"

    def test_stripAllExtensions_with_directory(self, io_utils):
        result = io_utils.stripAllExtensions(os.path.join("dir", "foo.qgs.bak"))
        assert result == os.path.join("dir", "foo")

    # ------------------------------------------------------------------ #
    # getQGisProjectBase
    # ------------------------------------------------------------------ #

    def test_getQGisProjectBase_no_metadata(self, io_utils, temp_project_dir):
        assert io_utils.getQGisProjectBase(temp_project_dir, "testNet") is None

    def test_getQGisProjectBase_no_qgisproject_node(self, io_utils, temp_project_dir):
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        with open(metadata, "w") as f:
            f.write("<Project><ThirdParty><QGISRed /></ThirdParty></Project>")
        assert io_utils.getQGisProjectBase(temp_project_dir, "testNet") is None

    def test_getQGisProjectBase_relative_qgs(self, io_utils, temp_project_dir):
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        with open(metadata, "w") as f:
            f.write("<Project><ThirdParty><QGISRed>"
                    "<QGisProject>testNet.qgs</QGisProject>"
                    "</QGISRed></ThirdParty></Project>")
        mock_fs = MagicMock()
        mock_fs.getUniformedPath.side_effect = lambda x: x
        with patch.object(QGISRedProjectIO, '_fs', return_value=mock_fs):
            result = io_utils.getQGisProjectBase(temp_project_dir, "testNet")
        expected = os.path.normpath(os.path.join(temp_project_dir, "testNet"))
        assert result == expected

    def test_getQGisProjectBase_absolute_qgz(self, io_utils, temp_project_dir):
        abs_qgz = os.path.join(temp_project_dir, "testNet.qgz")
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        with open(metadata, "w") as f:
            f.write(f"<Project><ThirdParty><QGISRed>"
                    f"<QGisProject>{abs_qgz}</QGisProject>"
                    f"</QGISRed></ThirdParty></Project>")
        mock_fs = MagicMock()
        mock_fs.getUniformedPath.side_effect = lambda x: x
        with patch.object(QGISRedProjectIO, '_fs', return_value=mock_fs):
            result = io_utils.getQGisProjectBase(temp_project_dir, "testNet")
        assert result == os.path.normpath(os.path.join(temp_project_dir, "testNet"))

    def test_getQGisProjectBase_malformed_xml(self, io_utils, temp_project_dir):
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        with open(metadata, "w") as f:
            f.write("<<not valid xml>>")
        assert io_utils.getQGisProjectBase(temp_project_dir, "testNet") is None

    # ------------------------------------------------------------------ #
    # findQGisProjectFile
    # ------------------------------------------------------------------ #

    def test_findQGisProjectFile_none_base(self, io_utils):
        assert io_utils.findQGisProjectFile(None) is None

    def test_findQGisProjectFile_qgz_exists(self, io_utils, temp_project_dir):
        base = os.path.join(temp_project_dir, "proj")
        open(base + ".qgz", "w").close()
        assert io_utils.findQGisProjectFile(base) == base + ".qgz"

    def test_findQGisProjectFile_only_qgs(self, io_utils, temp_project_dir):
        base = os.path.join(temp_project_dir, "proj")
        open(base + ".qgs", "w").close()
        assert io_utils.findQGisProjectFile(base) == base + ".qgs"

    def test_findQGisProjectFile_neither_exists(self, io_utils, temp_project_dir):
        base = os.path.join(temp_project_dir, "proj")
        assert io_utils.findQGisProjectFile(base) is None

    def test_findQGisProjectFile_both_exist_returns_qgz(self, io_utils, temp_project_dir):
        base = os.path.join(temp_project_dir, "proj")
        open(base + ".qgz", "w").close()
        open(base + ".qgs", "w").close()
        assert io_utils.findQGisProjectFile(base) == base + ".qgz"

    # ------------------------------------------------------------------ #
    # processProjectFiles
    # ------------------------------------------------------------------ #

    def _make_mock_fs(self):
        mock_fs = MagicMock()
        mock_fs.getUniformedPath.side_effect = lambda x: x
        return mock_fs

    def test_processProjectFiles_copies_and_renames(self, io_utils, temp_project_dir):
        src = temp_project_dir
        dst = tempfile.mkdtemp()
        try:
            open(os.path.join(src, "oldNet_pipes.shp"), "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processProjectFiles(src, "oldNet", "newNet", dst)
            assert os.path.exists(os.path.join(dst, "newNet_pipes.shp"))
        finally:
            shutil.rmtree(dst)

    def test_processProjectFiles_ignores_non_prefixed(self, io_utils, temp_project_dir):
        src = temp_project_dir
        dst = tempfile.mkdtemp()
        try:
            open(os.path.join(src, "readme.txt"), "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processProjectFiles(src, "oldNet", "newNet", dst)
            assert not os.path.exists(os.path.join(dst, "readme.txt"))
        finally:
            shutil.rmtree(dst)

    def test_processProjectFiles_copies_layerstyles(self, io_utils, temp_project_dir):
        src = temp_project_dir
        dst = tempfile.mkdtemp()
        try:
            ls_dir = os.path.join(src, "layerstyles")
            os.makedirs(ls_dir)
            open(os.path.join(ls_dir, "style.qml"), "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processProjectFiles(src, "oldNet", "newNet", dst)
            assert os.path.exists(os.path.join(dst, "layerstyles", "style.qml"))
        finally:
            shutil.rmtree(dst)

    def test_processProjectFiles_delete_source(self, io_utils):
        src = tempfile.mkdtemp()
        dst = tempfile.mkdtemp()
        try:
            src_file = os.path.join(src, "oldNet_pipes.shp")
            open(src_file, "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processProjectFiles(src, "oldNet", "newNet", dst, deleteSource=True)
            assert not os.path.exists(src_file)
            assert os.path.exists(os.path.join(dst, "newNet_pipes.shp"))
        finally:
            if os.path.exists(dst):
                shutil.rmtree(dst)

    def test_processProjectFiles_creates_target_dir(self, io_utils):
        parent = tempfile.mkdtemp()
        src = os.path.join(parent, "src")
        os.makedirs(src)
        dst = os.path.join(parent, "dst_new")
        try:
            assert not os.path.exists(dst)
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processProjectFiles(src, "oldNet", "newNet", dst)
            assert os.path.exists(dst)
        finally:
            shutil.rmtree(parent, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # processQGisProjectFiles
    # ------------------------------------------------------------------ #

    def test_processQGisProjectFiles_copies_qgz(self, io_utils):
        src_dir = tempfile.mkdtemp()
        dst_dir = tempfile.mkdtemp()
        try:
            qgis_base = os.path.join(src_dir, "myProj")
            open(qgis_base + ".qgz", "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                result = io_utils.processQGisProjectFiles(qgis_base, "newProj", dst_dir)
            expected = os.path.join(dst_dir, "newProj.qgz")
            assert result == expected
            assert os.path.exists(expected)
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_processQGisProjectFiles_copies_backup(self, io_utils):
        src_dir = tempfile.mkdtemp()
        dst_dir = tempfile.mkdtemp()
        try:
            qgis_base = os.path.join(src_dir, "myProj")
            open(qgis_base + ".qgz", "w").close()
            open(qgis_base + ".qgz.bak", "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processQGisProjectFiles(qgis_base, "newProj", dst_dir)
            assert os.path.exists(os.path.join(dst_dir, "newProj.qgz.bak"))
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_processQGisProjectFiles_delete_source(self, io_utils):
        src_dir = tempfile.mkdtemp()
        dst_dir = tempfile.mkdtemp()
        try:
            qgis_base = os.path.join(src_dir, "myProj")
            src_file = qgis_base + ".qgz"
            open(src_file, "w").close()
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                io_utils.processQGisProjectFiles(qgis_base, "newProj", dst_dir, deleteSource=True)
            assert not os.path.exists(src_file)
        finally:
            if os.path.exists(src_dir):
                shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    def test_processQGisProjectFiles_no_project_file(self, io_utils):
        src_dir = tempfile.mkdtemp()
        dst_dir = tempfile.mkdtemp()
        try:
            qgis_base = os.path.join(src_dir, "myProj")
            with patch.object(QGISRedProjectIO, '_fs', return_value=self._make_mock_fs()):
                result = io_utils.processQGisProjectFiles(qgis_base, "newProj", dst_dir)
            assert result is None
        finally:
            shutil.rmtree(src_dir)
            shutil.rmtree(dst_dir)

    # ------------------------------------------------------------------ #
    # updateQGisProjectContent
    # ------------------------------------------------------------------ #

    def test_updateQGisProjectContent_qgs_name_replacement(self, io_utils, temp_project_dir):
        qgs_path = os.path.join(temp_project_dir, "proj.qgs")
        with open(qgs_path, "w", encoding="utf-8") as f:
            f.write('<datasource>Net1_pipes.shp</datasource>')
        io_utils.updateQGisProjectContent(
            qgs_path, "Net1", "Net2",
            temp_project_dir, temp_project_dir
        )
        with open(qgs_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Net2_pipes.shp" in content
        assert "Net1_pipes.shp" not in content

    def test_updateQGisProjectContent_qgz_name_replacement(self, io_utils, temp_project_dir):
        from zipfile import ZipFile, ZIP_DEFLATED
        qgz_path = os.path.join(temp_project_dir, "proj.qgz")
        with ZipFile(qgz_path, "w", ZIP_DEFLATED) as zout:
            zout.writestr("proj.qgs", '<datasource>Net1_pipes.shp</datasource>')
        io_utils.updateQGisProjectContent(
            qgz_path, "Net1", "Net2",
            temp_project_dir, temp_project_dir
        )
        with ZipFile(qgz_path, "r") as zin:
            content = zin.read("proj.qgs").decode("utf-8")
        assert "Net2_pipes.shp" in content
        assert "Net1_pipes.shp" not in content

    def test_updateQGisProjectContent_nonexistent_file(self, io_utils, temp_project_dir):
        # Should not raise
        io_utils.updateQGisProjectContent(
            os.path.join(temp_project_dir, "missing.qgs"),
            "Net1", "Net2", temp_project_dir, temp_project_dir
        )

    # ------------------------------------------------------------------ #
    # updateMetadataQGisProject
    # ------------------------------------------------------------------ #

    def test_updateMetadataQGisProject_no_metadata(self, io_utils, temp_project_dir):
        # Should not raise
        io_utils.updateMetadataQGisProject(temp_project_dir, "testNet", "/new/path/proj.qgz")

    def test_updateMetadataQGisProject_updates_node(self, io_utils, temp_project_dir):
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        old_qgis = os.path.join(temp_project_dir, "testNet.qgz")
        with open(metadata, "w", encoding="latin-1") as f:
            f.write(
                f"<Project><ThirdParty><QGISRed>"
                f"<QGisProject>{old_qgis}</QGisProject>"
                f"</QGISRed></ThirdParty></Project>"
            )
        new_qgis = os.path.join(temp_project_dir, "testNet_v2.qgz")
        io_utils.updateMetadataQGisProject(temp_project_dir, "testNet", new_qgis)
        with open(metadata, "r", encoding="latin-1") as f:
            updated = f.read()
        assert os.path.relpath(new_qgis, temp_project_dir) in updated

    def test_updateMetadataQGisProject_no_qgisproject_node(self, io_utils, temp_project_dir):
        metadata = os.path.join(temp_project_dir, "testNet_Metadata.txt")
        original = "<Project><ThirdParty><QGISRed /></ThirdParty></Project>"
        with open(metadata, "w", encoding="latin-1") as f:
            f.write(original)
        io_utils.updateMetadataQGisProject(temp_project_dir, "testNet", "/new/proj.qgz")
        with open(metadata, "r", encoding="latin-1") as f:
            content = f.read()
        assert content == original
