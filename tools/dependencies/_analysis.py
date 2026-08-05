"""Analysis toolbar DLL calls (run model, analysis options, export to INP)."""

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
    def ExportToInp(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(projectFolder, networkName)
        return _to_string(b)
