from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedLifecycleMixin:
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
    def ChangeCrs(projectFolder, networkName, epsg):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        epsg = _encode(epsg)

        mydll = _load_dll()
        mydll.ChangeCrs.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ChangeCrs.restype = c_char_p
        b = mydll.ChangeCrs(projectFolder, networkName, epsg)
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
    def DefaultValues(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.DefaultValues.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DefaultValues.restype = c_char_p
        b = mydll.DefaultValues(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def ExportToInp(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(projectFolder, networkName)
        return _to_string(b)

    @staticmethod
    def ImportFromInp(projectFolder, networkName, tempFolder, inpFile, epsg):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        inpFile = _encode(inpFile)
        epsg = _encode(epsg)

        mydll = _load_dll()
        mydll.ImportFromInp.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ImportFromInp.restype = c_char_p
        b = mydll.ImportFromInp(projectFolder, networkName, tempFolder, inpFile, epsg)
        return _to_string(b)

    @staticmethod
    def Materials(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.Materials.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Materials.restype = c_char_p
        b = mydll.Materials(projectFolder, networkName, tempFolder)
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
    def Summary(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.AbstractReport.argtypes = (c_char_p, c_char_p)
        mydll.AbstractReport.restype = c_char_p
        b = mydll.AbstractReport(projectFolder, networkName)
        return _to_string(b)
