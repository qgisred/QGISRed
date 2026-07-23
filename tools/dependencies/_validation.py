from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedValidationMixin:
    @staticmethod
    def CheckAlignedVertices(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckAlignedVertices.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckAlignedVertices.restype = c_char_p
        b = mydll.CheckAlignedVertices(projectFolder, networkName, tempFolder, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckConnectivity(projectFolder, networkName, linesToDelete, step, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        linesToDelete = _encode(linesToDelete)
        step = _encode(step)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.CheckConnectivity.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        b = mydll.CheckConnectivity(projectFolder, networkName, linesToDelete, step, tempFolder)
        return _to_string(b)

    @staticmethod
    def CheckDiameters(projectFolder, networkName, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckDiameters.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckDiameters.restype = c_char_p
        b = mydll.CheckDiameters(projectFolder, networkName, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckInstallationDates(projectFolder, networkName, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckInstallationDates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckInstallationDates.restype = c_char_p
        b = mydll.CheckInstallationDates(projectFolder, networkName, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckJoinPipes(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.CheckJoinPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckJoinPipes.restype = c_char_p
        b = mydll.CheckJoinPipes(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def CheckLengths(projectFolder, networkName, tolerance, tempFolder, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tolerance = _encode(tolerance)
        tempFolder = _encode(tempFolder)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckLengths.restype = c_char_p
        b = mydll.CheckLengths(projectFolder, networkName, tolerance, tempFolder, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckMaterials(projectFolder, networkName, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckMaterials.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckMaterials.restype = c_char_p
        b = mydll.CheckMaterials(projectFolder, networkName, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckOverlappingElements(projectFolder, networkName, tempFolder, nodeIds, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        nodeIds = _encode(nodeIds)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.CheckOverlappingElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckOverlappingElements.restype = c_char_p
        b = mydll.CheckOverlappingElements(projectFolder, networkName, tempFolder, nodeIds, linkIds)
        return _to_string(b)

    @staticmethod
    def CheckTConnections(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.CheckTConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckTConnections.restype = c_char_p
        b = mydll.CheckTConnections(projectFolder, networkName, tempFolder)
        return _to_string(b)
