# -*- coding: utf-8 -*-
import pytest
import sys
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

# Add plugin root to sys.path
_PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

# Mock QGIS modules
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()

from tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils

class TestFileSystemUtils:
    @pytest.fixture
    def utils(self):
        return QGISRedFileSystemUtils()

    def test_getUniformedPath(self, utils):
        assert utils.getUniformedPath(None) == ""
        # Test path normalization
        path = "C:/tmp/foo/../bar"
        expected = os.path.realpath(path).replace("/", os.sep)
        assert utils.getUniformedPath(path) == expected

    def test_generatePath(self, utils):
        folder = "C:\\projects"
        file = "net.inp"
        # os.path.join handles separators
        expected = os.path.join(folder, file).replace("/", os.sep)
        assert utils.generatePath(folder, file) == expected

    def test_getQGISRedFolder(self, utils):
        with patch.dict(os.environ, {"APPDATA": "C:\\AppData"}):
            assert utils.getQGISRedFolder() == "C:\\AppData\\QGISRed"

    def test_getGISRedDllFolder_x64(self, utils):
        with patch.dict(os.environ, {"APPDATA": "C:\\AppData"}):
            with patch('platform.architecture', return_value=('64bit', 'WindowsPE')):
                assert utils.getGISRedDllFolder() == "C:\\AppData\\QGISRed\\dlls\\x64"

    def test_getGISRedDllFolder_x86(self, utils):
        with patch.dict(os.environ, {"APPDATA": "C:\\AppData"}):
            with patch('platform.architecture', return_value=('32bit', 'WindowsPE')):
                assert utils.getGISRedDllFolder() == "C:\\AppData\\QGISRed\\dlls\\x86"

    def test_removeFolder(self, utils):
        # Create a temp folder
        temp_dir = tempfile.mkdtemp()
        assert os.path.exists(temp_dir)
        assert utils.removeFolder(temp_dir) is True
        assert not os.path.exists(temp_dir)

    def test_copyFolderFiles(self, utils):
        # Setup source and dest dirs
        src = tempfile.mkdtemp()
        dst = tempfile.mkdtemp()
        try:
            # Create some files
            with open(os.path.join(src, "file1.txt"), "w") as f:
                f.write("hello")
            os.mkdir(os.path.join(src, "subdir"))
            with open(os.path.join(src, "subdir", "file2.txt"), "w") as f:
                f.write("world")
            
            utils.copyFolderFiles(src, dst)
            
            assert os.path.exists(os.path.join(dst, "file1.txt"))
            assert os.path.exists(os.path.join(dst, "subdir", "file2.txt"))
            with open(os.path.join(dst, "subdir", "file2.txt"), "r") as f:
                assert f.read() == "world"
        finally:
            shutil.rmtree(src)
            shutil.rmtree(dst)
