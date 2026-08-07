import pytest
import os
import shutil
import tempfile
from unittest.mock import patch
from QGISRed.tools.utils.qgisred_filesystem_utils import (
    APP_DATA_MATERIALS_FOLDER,
    INSTALL_DEFAULTS_FOLDER,
    QGISRedFileSystemUtils,
)


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
        # Use a real absolute folder so realpath() doesn't resolve it against the CWD.
        folder = tempfile.gettempdir()
        file = "net.inp"
        # generatePath joins folder + file and normalizes via getUniformedPath (realpath + os.sep).
        expected = os.path.realpath(os.path.join(folder, file)).replace("/", os.sep)
        assert utils.generatePath(folder, file) == expected

    # getQGISRedFolder / getGISRedDllFolder branch on sys.platform, so mock it to
    # exercise every OS branch regardless of the host running the tests. Expected
    # values are built with os.path.join (never hardcoded separators) so the
    # assertions hold on Windows, macOS and Linux alike.

    def test_getQGISRedFolder_windows(self, utils):
        appdata = os.path.join(tempfile.gettempdir(), "AppData")
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"APPDATA": appdata}):
            assert utils.getQGISRedFolder() == os.path.join(appdata, "QGISRed")

    def test_getQGISRedFolder_macos(self, utils):
        with patch("sys.platform", "darwin"):
            expected = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "QGISRed")
            assert utils.getQGISRedFolder() == expected

    def test_getQGISRedFolder_linux(self, utils):
        xdg = os.path.join(tempfile.gettempdir(), "config")
        with patch("sys.platform", "linux"), patch.dict(os.environ, {"XDG_CONFIG_HOME": xdg}):
            assert utils.getQGISRedFolder() == os.path.join(xdg, "QGISRed")

    # The installer folder is where the MSI/.deb/.pkg deploy dlls and defaults. It is the
    # per-user folder on Windows only; on Linux/macOS the packages install machine-wide.
    # These paths must match GISRed.Utils.PlatformPaths.InstallRoot on the C# side.

    def test_getQGISRedInstallFolder_windows_is_the_user_folder(self, utils):
        appdata = os.path.join(tempfile.gettempdir(), "AppData")
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"APPDATA": appdata}):
            assert utils.getQGISRedInstallFolder() == utils.getQGISRedFolder()

    def test_getQGISRedInstallFolder_macos_is_machine_wide(self, utils):
        with patch("sys.platform", "darwin"):
            assert utils.getQGISRedInstallFolder() == "/Library/Application Support/QGISRed"

    def test_getQGISRedInstallFolder_linux_is_machine_wide(self, utils):
        with patch("sys.platform", "linux"):
            assert utils.getQGISRedInstallFolder() == "/opt/QGISRed"

    def test_getDefaultsFolder(self, utils):
        assert utils.getDefaultsFolder() == os.path.join(utils.getQGISRedInstallFolder(), INSTALL_DEFAULTS_FOLDER)

    def test_getDefaultsFolder_linux_is_machine_wide(self, utils):
        with patch("sys.platform", "linux"):
            assert utils.getDefaultsFolder() == os.path.join("/opt/QGISRed", INSTALL_DEFAULTS_FOLDER)

    def test_getMaterialsFolder(self, utils):
        assert utils.getMaterialsFolder() == os.path.join(utils.getQGISRedFolder(), APP_DATA_MATERIALS_FOLDER)

    def test_getMaterialsFolder_linux_stays_per_user(self, utils):
        # Material tables are user data, so they never move to the machine-wide folder.
        xdg = os.path.join(tempfile.gettempdir(), "config")
        with patch("sys.platform", "linux"), patch.dict(os.environ, {"XDG_CONFIG_HOME": xdg}):
            assert utils.getMaterialsFolder() == os.path.join(xdg, "QGISRed", APP_DATA_MATERIALS_FOLDER)

    def test_getGISRedDllFolder_windows_x64(self, utils):
        # QGIS is 64-bit only, so Windows always resolves to x64 - there is no x86 build.
        appdata = os.path.join(tempfile.gettempdir(), "AppData")
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"APPDATA": appdata}):
            assert utils.getGISRedDllFolder() == os.path.join(appdata, "QGISRed", "dlls", "x64")

    def test_getGISRedDllFolder_macos(self, utils):
        with patch("sys.platform", "darwin"):
            expected = os.path.join("/Library/Application Support/QGISRed", "dlls", "osx")
            assert utils.getGISRedDllFolder() == expected

    def test_getGISRedDllFolder_linux_x64(self, utils):
        with patch("sys.platform", "linux"), patch("platform.machine", return_value="x86_64"):
            expected = os.path.join("/opt/QGISRed", "dlls", "x64")
            assert utils.getGISRedDllFolder() == expected

    def test_getGISRedDllFolder_linux_arm64(self, utils):
        with patch("sys.platform", "linux"), patch("platform.machine", return_value="aarch64"):
            expected = os.path.join("/opt/QGISRed", "dlls", "arm64")
            assert utils.getGISRedDllFolder() == expected

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
