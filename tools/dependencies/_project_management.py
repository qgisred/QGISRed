"""General and Project toolbars DLL calls (create/import project, settings, defaults, materials)."""

from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedProjectManagementMixin:
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
    def EditSettings(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.EditSettings.argtypes = (c_char_p, c_char_p)
        mydll.EditSettings.restype = c_char_p
        b = mydll.EditSettings(projectFolder, networkName)
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
    def ImportFromShps(
        projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance, scLength,
        scMaxDiameter="", scPipeIds=""
    ):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        shapes = _encode(shapes)
        fields = _encode(fields)
        epsg = _encode(epsg)
        tolerance = _encode(tolerance)
        scLength = _encode(scLength)
        scMaxDiameter = _encode(scMaxDiameter)
        scPipeIds = _encode(scPipeIds)

        mydll = _load_dll()
        mydll.ImportFromShps.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p
        )
        mydll.ImportFromShps.restype = c_char_p
        b = mydll.ImportFromShps(
            projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance, scLength,
            scMaxDiameter, scPipeIds
        )
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
    def Summary(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.AbstractReport.argtypes = (c_char_p, c_char_p)
        mydll.AbstractReport.restype = c_char_p
        b = mydll.AbstractReport(projectFolder, networkName)
        return _to_string(b)
