from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedLayerManagementMixin:
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
    def UpdateMetadata(projectFolder, networkName, layersNames):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        layersNames = _encode(layersNames)

        mydll = _load_dll()
        mydll.UpdateMetadata.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.UpdateMetadata.restype = c_char_p
        b = mydll.UpdateMetadata(projectFolder, networkName, layersNames)
        return _to_string(b)
