"""Layer manager DLL calls (Project toolbar > Layer manager) plus internal layer/metadata helpers."""

from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedLayerManagementMixin:
    @staticmethod
    def CreateAuxiliaryLayer(projectFolder, networkName, themeType, filePath, baseDemandFieldName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        themeType = _encode(themeType)
        filePath = _encode(filePath)
        baseDemandFieldName = _encode(baseDemandFieldName)

        mydll = _load_dll()
        mydll.CreateAuxiliaryLayer.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateAuxiliaryLayer.restype = c_char_p
        b = mydll.CreateAuxiliaryLayer(projectFolder, networkName, themeType, filePath, baseDemandFieldName)
        return _to_string(b)

    @staticmethod
    def CreateLayer(projectFolder, networkName, layer, complLayer):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        layer = _encode(layer)
        complLayer = _encode(complLayer)

        mydll = _load_dll()
        mydll.CreateLayer.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateLayer.restype = c_char_p
        b = mydll.CreateLayer(projectFolder, networkName, layer, complLayer)
        return _to_string(b)

    @staticmethod
    def ReplaceTemporalFiles(projectFolder, tempFolder):
        projectFolder = _encode(projectFolder)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.ReplaceTemporalFiles.argtypes = (c_char_p, c_char_p)
        mydll.ReplaceTemporalFiles.restype = c_char_p
        b = mydll.ReplaceTemporalFiles(projectFolder, tempFolder)
        return _to_string(b)

    @staticmethod
    def UpdateMetadata(projectFolder, networkName, layersNames):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        layersNames = _encode(layersNames)

        mydll = _load_dll()
        mydll.UpdateMetadata.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.UpdateMetadata.restype = c_char_p
        b = mydll.UpdateMetadata(projectFolder, networkName, layersNames)
        return _to_string(b)
