from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedProjectManagementMixin:
    @staticmethod
    def SetCulture(culture):
        culture = _encode(culture)

        mydll = _load_dll()
        mydll.SetCulture.argtypes = (c_char_p,)
        mydll.SetCulture.restype = c_char_p
        b = mydll.SetCulture(culture)
        return _to_string(b)

    def GetVersion():
        mydll = _load_dll()
        mydll.GetVersion.argtypes = ()
        mydll.GetVersion.restype = c_char_p
        b = mydll.GetVersion()
        return _to_string(b)

    @staticmethod
    def CreateProject(projectFolder, networkName, epsg, units, headloss, materialPath):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        epsg = _encode(epsg)
        units = _encode(units)
        headloss = _encode(headloss)
        materialPath = _encode(materialPath)

        mydll = _load_dll()
        mydll.CreateProject.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateProject.restype = c_char_p
        b = mydll.CreateProject(projectFolder, networkName, epsg, units, headloss, materialPath)
        return _to_string(b)

    @staticmethod
    def Commit(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.Commit.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Commit.restype = c_char_p
        b = mydll.Commit(projectFolder, networkName, tempFolder)
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
