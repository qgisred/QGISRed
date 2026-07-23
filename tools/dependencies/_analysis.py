from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedAnalysisMixin:
    @staticmethod
    def AnalysisOptions(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.AnalysisOptions.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AnalysisOptions.restype = c_char_p
        b = mydll.AnalysisOptions(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def Compute(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.Compute.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def HydarulicSectors(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(projectFolder, networkName, tempFolder)
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
    def LoadReadings(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.LoadReadings.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.LoadReadings.restype = c_char_p
        b = mydll.LoadReadings(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def LoadScada(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.LoadScada.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.LoadScada.restype = c_char_p
        b = mydll.LoadScada(projectFolder, networkName, tempFolder)
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
