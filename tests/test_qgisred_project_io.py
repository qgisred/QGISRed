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

    def test_getProjectGuid_fallback(self, io_utils, temp_project_dir):
        # Metadata doesn't exist
        assert io_utils.getProjectGuid() == "testNet"
