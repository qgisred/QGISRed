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
