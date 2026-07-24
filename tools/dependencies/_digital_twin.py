from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedDigitalTwinMixin:
    @staticmethod
    def DemandsBuilder(
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

        mydll.DemandsBuilder.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p,
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p
        )

        mydll.DemandsBuilder.restype = c_char_p

        b = mydll.DemandsBuilder(
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
    def CreateRemoveDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName, create):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        themeName = _encode(themeName)
        create = _encode(create)

        mydll = _load_dll()

        mydll.CreateRemoveDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)

        mydll.CreateRemoveDemandSectorTheme.restype = c_char_p

        b = mydll.CreateRemoveDemandSectorTheme(projectFolder, networkName,
            sectorizationName, themeName, create)

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
    def CreateCompleteDemandSectorTheme(projectFolder, networkName, sectorizationName, fromTheme, toTheme):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        fromTheme = _encode(fromTheme)
        toTheme = _encode(toTheme)

        mydll = _load_dll()

        mydll.CreateCompleteDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, 
                                                          c_char_p, c_char_p)

        mydll.CreateCompleteDemandSectorTheme.restype = c_char_p

        b = mydll.CreateCompleteDemandSectorTheme(projectFolder, networkName,
            sectorizationName, fromTheme, toTheme)

        return _to_string(b)
    
    @staticmethod
    def UpdateDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        sectorizationName = _encode(sectorizationName)
        themeName = _encode(themeName)

        mydll = _load_dll()

        mydll.UpdateDemandSectorTheme.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)

        mydll.UpdateDemandSectorTheme.restype = c_char_p

        b = mydll.UpdateDemandSectorTheme(projectFolder, networkName, sectorizationName, themeName)

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
    def ImportFromShps(projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance, scLength):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        shapes = _encode(shapes)
        fields = _encode(fields)
        epsg = _encode(epsg)
        tolerance = _encode(tolerance)
        scLength = _encode(scLength)

        mydll = _load_dll()
        mydll.ImportFromShps.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ImportFromShps.restype = c_char_p
        b = mydll.ImportFromShps(projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance, scLength)
        return _to_string(b)
