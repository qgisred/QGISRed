"""Tools toolbar DLL calls (lengths, elevations, roughness, demand builder/sectors, scenarios, tree)."""

from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedToolsMixin:
    @staticmethod
    def CalculateLengths(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CalculateLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CalculateLengths.restype = c_char_p
        b = mydll.CalculateLengths(projectFolder, networkName, tempFolder, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        themeName = _encode(themeName)

        mydll = _load_dll()
        mydll.CheckDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckDemandSectorTheme.restype = c_char_p
        b = mydll.CheckDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName)
        return _to_string(b)

    @staticmethod
    def ConvertRoughness(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.ConvertRoughness.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ConvertRoughness.restype = c_char_p
        b = mydll.ConvertRoughness(projectFolder, networkName, tempFolder, linkIds)
        return _to_string(b)

    @staticmethod
    def CreateCompleteDemandSectorTheme(projectFolder, networkName, sectorizationName, fromTheme, toTheme):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        fromTheme = _encode(fromTheme)
        toTheme = _encode(toTheme)

        mydll = _load_dll()
        mydll.CreateCompleteDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateCompleteDemandSectorTheme.restype = c_char_p
        b = mydll.CreateCompleteDemandSectorTheme(projectFolder, networkName, sectorizationName, fromTheme, toTheme)
        return _to_string(b)

    @staticmethod
    def CreateDemandSectorization(projectFolder, networkName, sectorizationName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)

        mydll = _load_dll()
        mydll.CreateDemandSectorization.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CreateDemandSectorization.restype = c_char_p
        b = mydll.CreateDemandSectorization(projectFolder, networkName, sectorizationName)
        return _to_string(b)

    @staticmethod
    def CreateRemoveDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        themeName = _encode(themeName)

        mydll = _load_dll()
        mydll.CreateRemoveDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateRemoveDemandSectorTheme.restype = c_char_p
        b = mydll.CreateRemoveDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName)
        return _to_string(b)

    @staticmethod
    def DemandBuilder(
            projectFolder,
            networkName,
            tempFolder,
            ids,
            auxiliarLayers,
            qgisredPointLayers="",
            qgisredLineLayers="",
            qgisredSectorLayers="",
            selectedAuxiliaryLayerFids=""):

        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        ids = _encode(ids)
        auxiliarLayers = _encode(auxiliarLayers)
        qgisredPointLayers = _encode(qgisredPointLayers)
        qgisredLineLayers = _encode(qgisredLineLayers)
        qgisredSectorLayers = _encode(qgisredSectorLayers)
        selectedAuxiliaryLayerFids = _encode(selectedAuxiliaryLayerFids)

        mydll = _load_dll()
        mydll.DemandBuilder.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p,
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p
        )
        mydll.DemandBuilder.restype = c_char_p
        b = mydll.DemandBuilder(
            projectFolder,
            networkName,
            tempFolder,
            ids,
            auxiliarLayers,
            qgisredPointLayers,
            qgisredLineLayers,
            qgisredSectorLayers,
            selectedAuxiliaryLayerFids
        )
        return _to_string(b)

    @staticmethod
    def DemandSectorBuilder(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.DemandSectorBuilder.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DemandSectorBuilder.restype = c_char_p
        b = mydll.DemandSectorBuilder(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def DemandSectors(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.DemandSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DemandSectors.restype = c_char_p
        b = mydll.DemandSectors(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def ElevationInterpolation(projectFolder, networkName, tempFolder, elevationFiles):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        elevationFiles = _encode(elevationFiles)

        mydll = _load_dll()
        mydll.ElevationInterpolation.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ElevationInterpolation.restype = c_char_p
        b = mydll.ElevationInterpolation(projectFolder, networkName, tempFolder, elevationFiles)
        return _to_string(b)

    @staticmethod
    def GetDemandSectorThemes(projectFolder, networkName, sectorizationName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)

        mydll = _load_dll()
        mydll.GetDemandSectorThemes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.GetDemandSectorThemes.restype = c_char_p
        b = mydll.GetDemandSectorThemes(projectFolder, networkName, sectorizationName)
        return _to_string(b)

    @staticmethod
    def IsolatedSegments(mydll, projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll.IsolatedSegments.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.IsolatedSegments.restype = c_char_p
        b = mydll.IsolatedSegments(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def ScenarioManager(projectFolder, networkName, tempFolder, ids):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        ids = _encode(ids)

        mydll = _load_dll()
        mydll.ScenarioManager.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ScenarioManager.restype = c_char_p
        b = mydll.ScenarioManager(projectFolder, networkName, tempFolder, ids)
        return _to_string(b)

    @staticmethod
    def SetRoughness(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(projectFolder, networkName, tempFolder, linkIds)
        return _to_string(b)

    @staticmethod
    def Tree(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.Tree.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.Tree.restype = c_char_p
        b = mydll.Tree(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def UpdateDemandSectorThemesFromSource(projectFolder, networkName, sectorizationName, sourceTheme):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        sourceTheme = _encode(sourceTheme)

        mydll = _load_dll()
        mydll.UpdateDemandSectorThemesFromSource.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.UpdateDemandSectorThemesFromSource.restype = c_char_p
        b = mydll.UpdateDemandSectorThemesFromSource(projectFolder, networkName, sectorizationName, sourceTheme)
        return _to_string(b)
