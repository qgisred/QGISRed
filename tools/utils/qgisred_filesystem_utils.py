# -*- coding: utf-8 -*-
from contextlib import suppress
import os
import tempfile
import shutil
import platform
from shutil import copyfile

from qgis.core import QgsVectorLayer  # noqa: F401 — used in getLayerPath exception path

# Project subdirectory names — single source of truth for all os.path.join calls
DIR_ISSUES            = "Issues"
DIR_QUERIES           = "Queries"
DIR_RESULTS           = "Results"
DIR_CONNECTIVITY      = "Connectivity"
DIR_HYDRAULIC_SECTORS = "HydraulicSectors"
DIR_DEMAND_SECTORS    = "DemandSectors"
DIR_ISOLATED_SEGMENTS = "IsolatedSegments"
DIR_AUXILIARY_LAYERS  = "Auxiliary Layers"
DIR_DEMAND_BUILDER     = "DemandBuilder"
DIR_BACKUPS           = "backups"

INSTALL_DEFAULTS_FOLDER   = "defaults"
APP_DATA_MATERIALS_FOLDER = "materials"
ELEMENT_LAYERS = [
    "Pipes",
    "Junctions",
    "Tanks",
    "Reservoirs",
    "Valves",
    "Pumps",
    "Demands",
    "Sources",
    "IsolationValves",
    "ServiceConnections",
    "Meters",
]

# Single source of truth: layer-type key → {subdir, tree_path, flags}
# subdir:    relative path from ProjectDirectory to the layer files
# tree_path: QGIS group path (without the NetworkName root)
# flags:     kwargs passed to QGISRedLayerUtils.openLayer()
LAYER_TYPE_CONFIG = {
    "HydraulicSectors": {
        "subdir":    os.path.join(DIR_ISSUES, DIR_HYDRAULIC_SECTORS),
        "tree_path": ["Issues", "Hydraulic Sectors"],
        "flags":     {"sectors": True},
    },
    "DemandSectors": {
        "subdir":    os.path.join(DIR_AUXILIARY_LAYERS, DIR_DEMAND_SECTORS),
        "tree_path": ["Auxiliary Layers", "DemandSectors"],
        "flags":     {"sectors": True},
    },
    "Connectivity": {
        "subdir":    os.path.join(DIR_ISSUES, DIR_CONNECTIVITY),
        "tree_path": ["Issues", "Connectivity"],
        "flags":     {},
    },
    "IsolatedSegments": {
        "subdir":    os.path.join(DIR_QUERIES, DIR_ISOLATED_SEGMENTS),
        "tree_path": ["Queries", "Isolated Segments"],
        "flags":     {},
    },
    "DemandBuilder": {
        "subdir":    os.path.join(DIR_AUXILIARY_LAYERS, DIR_DEMAND_BUILDER),
        "tree_path": ["Auxiliary Layers", "DemandBuilder"],
        "flags":     {"demandBuilder": True},
    },
}


class QGISRedFileSystemUtils:
    DllTempoFolder = None
    _pluginVersion = None

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def getUniformedPath(self, path):
        if path is None:
            return ""
        path = os.path.realpath(path)
        return path.replace("/", os.sep)

    def getLayerPath(self, layer):
        try:
            path = str(layer.dataProvider().dataSourceUri().split("|")[0])
            return self.getUniformedPath(path)
        except Exception:
            return ""

    def generatePath(self, folder, fileName):
        return self.getUniformedPath(os.path.join(folder, fileName))

    def getQGISRedFolder(self):
        """Per-user folder: everything the plugin writes on behalf of this user (project list,
        global styles, material tables, temp-folder registry...). Always under the user's home."""
        import sys
        if sys.platform == "win32":
            appdata = os.getenv("APPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
            return os.path.join(appdata, "QGISRed")
        elif sys.platform == "darwin":
            return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "QGISRed")
        else:
            xdg = os.getenv("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
            return os.path.join(xdg, "QGISRed")

    def getQGISRedInstallFolder(self):
        """Folder where the dependencies installer deploys its read-only assets (dlls, defaults).

        On Windows the MSI installs per-user, so it is the same folder as getQGISRedFolder(). On
        Linux and macOS the .deb and .pkg install as root, machine-wide. Must stay in sync with
        GISRed.Utils.PlatformPaths.InstallRoot on the C# side: both read the very same files.
        """
        import sys
        if sys.platform == "win32":
            return self.getQGISRedFolder()
        elif sys.platform == "darwin":
            return "/Library/Application Support/QGISRed"
        else:
            return "/opt/QGISRed"

    def getDefaultsFolder(self):
        """Installer-deployed folder with the defaults shared by every project (units/decimals
        CSV and the Materials_*.dbf tables). Read-only: not writable on Linux/macOS."""
        return os.path.join(self.getQGISRedInstallFolder(), INSTALL_DEFAULTS_FOLDER)

    def getMaterialsFolder(self):
        """Per-user folder with the user's own material tables (written by the C# side)."""
        return os.path.join(self.getQGISRedFolder(), APP_DATA_MATERIALS_FOLDER)

    def getMaterialFiles(self):
        """Returns a list of (name, path) tuples for all .dbf files in defaults and materials folders."""
        result = []
        for folder in (self.getDefaultsFolder(), self.getMaterialsFolder()):
            if not os.path.isdir(folder):
                continue
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(".dbf"):
                    result.append((os.path.splitext(fname)[0], os.path.join(folder, fname)))
        return result

    def getGISRedDllFolder(self):
        """Installer-deployed folder with the native libraries for this platform."""
        import sys
        if sys.platform == "darwin":
            subdir = "osx"
        elif sys.platform == "win32":
            subdir = "x64"  # QGIS has shipped 64-bit only for many versions; no x86 build exists
        else:
            machine = platform.machine()
            subdir = "arm64" if machine in ("aarch64", "arm64") else "x64"
        return os.path.join(self.getQGISRedInstallFolder(), "dlls", subdir)

    def getDownloadsFolder(self):
        """Returns the user's Downloads folder (cross-platform), falling back to the home folder."""
        with suppress(Exception):
            from qgis.PyQt.QtCore import QStandardPaths
            from ...compat import STD_LOCATION_DOWNLOAD
            if STD_LOCATION_DOWNLOAD is not None:
                path = QStandardPaths.writableLocation(STD_LOCATION_DOWNLOAD)
                if path and os.path.isdir(path):
                    return os.path.normpath(path)
        home = os.path.expanduser("~")
        fallback = os.path.join(home, "Downloads")
        return fallback if os.path.isdir(fallback) else home

    def getPluginVersion(self):
        """Reads the plugin version from metadata.txt at the plugin root. Returns '' if unavailable."""
        cached = QGISRedFileSystemUtils._pluginVersion
        if cached is not None:
            return cached
        version = ""
        # this file is <plugin>/tools/utils/qgisred_filesystem_utils.py
        pluginRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        metadata = os.path.join(pluginRoot, "metadata.txt")
        with suppress(Exception):
            with open(metadata, "r") as f:
                for line in f:
                    if line.startswith("version="):
                        version = line.replace("version=", "").strip()
                        break
        QGISRedFileSystemUtils._pluginVersion = version
        return version

    def getUserFolder(self):
        userRoot = os.path.join(os.path.expanduser("~"), "QGISRed")
        os.makedirs(userRoot, exist_ok=True)
        userFolder = os.path.join(userRoot, "Projects")
        os.makedirs(userFolder, exist_ok=True)
        return userFolder

    def getCurrentDll(self):
        import sys
        if sys.platform == "win32":
            dll_name = "GISRed.QGISRed.dll"
        elif sys.platform == "darwin":
            dll_name = "GISRed.QGISRed.dylib"
        else:
            dll_name = "GISRed.QGISRed.so"
        return os.path.join(QGISRedFileSystemUtils.DllTempoFolder, dll_name)

    def copyDependencies(self):
        src_folder = self.getGISRedDllFolder()
        if not os.path.exists(src_folder):
            return
        tmp = tempfile.mkdtemp(prefix="QGISRed_")
        QGISRedFileSystemUtils.DllTempoFolder = tmp
        for name in os.listdir(src_folder):
            src = os.path.join(src_folder, name)
            dst = os.path.join(tmp, name)
            if os.path.isdir(src):
                # Satellite assemblies (localization folders: es, fr...) must be copied recursively
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    def writeFile(self, file, string):
        file.write(string)

    def copyFolderFiles(self, originalFolder, destinationFolder):
        if not os.path.exists(destinationFolder):
            with suppress(Exception):
                os.mkdir(destinationFolder)

        folder = self.getUniformedPath(originalFolder)
        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath):
                with suppress(Exception):
                    copyfile(r"" + filepath, r"" + filepath.replace(folder, destinationFolder))
            elif os.path.isdir(filepath):
                self.copyFolderFiles(filepath, os.path.join(destinationFolder, f))

    def removeFolder(self, folder):
        try:
            if os.path.exists(folder) and os.path.isdir(folder):
                shutil.rmtree(folder)
        except Exception:
            return False
        return True
