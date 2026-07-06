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
DIR_DEMANDS_BUILDER    = "DemandsBuilder"

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
    "DemandsBuilder": {
        "subdir":    os.path.join(DIR_AUXILIARY_LAYERS, DIR_DEMANDS_BUILDER),
        "tree_path": ["Auxiliary Layers", "DemandsBuilder"],
        "flags":     {},
    },
}


class QGISRedFileSystemUtils:
    DllTempoFolder = None

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
        return os.path.join(os.getenv("APPDATA"), "QGISRed")

    def getMaterialFiles(self):
        """Returns a list of (name, path) tuples for all .dbf files in global_defaults and materials folders."""
        result = []
        root = self.getQGISRedFolder()
        for subfolder in ("global_defaults", "materials"):
            folder = os.path.join(root, subfolder)
            if not os.path.isdir(folder):
                continue
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith(".dbf"):
                    result.append((os.path.splitext(fname)[0], os.path.join(folder, fname)))
        return result

    def getGISRedDllFolder(self):
        plat = "x86"
        if "64bit" in str(platform.architecture()):
            plat = "x64"
        dllFolder = os.path.join(self.getQGISRedFolder(), "dlls")
        return os.path.join(dllFolder, plat)

    def getUserFolder(self):
        userFolder = os.path.expanduser("~\\QGISRed")
        try:  # create directory if does not exist
            os.stat(userFolder)
        except Exception:
            os.mkdir(userFolder)
        userFolder = os.path.expanduser("~\\QGISRed\\Projects")
        try:  # create directory if does not exist
            os.stat(userFolder)
        except Exception:
            os.mkdir(userFolder)
        return userFolder

    def getCurrentDll(self):
        os.chdir(QGISRedFileSystemUtils.DllTempoFolder)
        return os.path.join(QGISRedFileSystemUtils.DllTempoFolder, "GISRed.QGISRed.dll")

    def copyDependencies(self):
        if not os.path.exists(self.getGISRedDllFolder()):
            return
        QGISRedFileSystemUtils.DllTempoFolder = tempfile._get_default_tempdir() + "\\QGISRed_" + next(tempfile._get_candidate_names())
        shutil.copytree(self.getGISRedDllFolder(), QGISRedFileSystemUtils.DllTempoFolder)

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
