from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedNetworkEditingMixin:
    @staticmethod
    def AddConnection(projectFolder, networkName, tempFolder, pipePoints):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        pipePoints = _encode(pipePoints)

        mydll = _load_dll()
        mydll.AddConnection.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnection.restype = c_char_p
        b = mydll.AddConnection(projectFolder, networkName, tempFolder, pipePoints)
        return _to_string(b)

    @staticmethod
    def AddConnections(projectFolder, networkName, asNode, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        asNode = _encode(asNode)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.AddConnections.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        b = mydll.AddConnections(projectFolder, networkName, asNode, tempFolder)
        return _to_string(b)

    @staticmethod
    def AddHydrants(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        b = mydll.AddHydrants(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def AddIsolationValve(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.AddIsolationValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddIsolationValve.restype = c_char_p
        b = mydll.AddIsolationValve(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def AddMeter(projectFolder, networkName, tempFolder, point, metertype):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)
        metertype = _encode(metertype)

        mydll = _load_dll()
        mydll.AddMeter.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddMeter.restype = c_char_p
        b = mydll.AddMeter(projectFolder, networkName, tempFolder, point, metertype)
        return _to_string(b)

    @staticmethod
    def AddPipe(projectFolder, networkName, tempFolder, pipePoints):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        pipePoints = _encode(pipePoints)

        mydll = _load_dll()
        mydll.AddPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddPipe.restype = c_char_p
        b = mydll.AddPipe(projectFolder, networkName, tempFolder, pipePoints)
        return _to_string(b)

    @staticmethod
    def AddReservoir(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.AddReservoir.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddReservoir.restype = c_char_p
        b = mydll.AddReservoir(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def AddTank(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.AddTank.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddTank.restype = c_char_p
        b = mydll.AddTank(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def AddWashoutValves(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.AddWashoutValves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddWashoutValves.restype = c_char_p
        b = mydll.AddWashoutValves(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def ChangeStatus(projectFolder, networkName, tempFolder, point, ctrlPressed):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)
        ctrlPressed = _encode(ctrlPressed)

        mydll = _load_dll()
        mydll.ChangeStatus.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ChangeStatus.restype = c_char_p
        b = mydll.ChangeStatus(projectFolder, networkName, tempFolder, point, ctrlPressed)
        return _to_string(b)

    @staticmethod
    def CreateReverseCrossings(projectFolder, networkName, tempFolder, point1, tolerance):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point1 = _encode(point1)
        tolerance = _encode(tolerance)

        mydll = _load_dll()
        mydll.CreateReverseCrossings.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseCrossings.restype = c_char_p
        b = mydll.CreateReverseCrossings(projectFolder, networkName, tempFolder, point1, tolerance)
        return _to_string(b)

    @staticmethod
    def CreateReverseTConnection(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point1 = _encode(point1)
        point2 = _encode(point2)

        mydll = _load_dll()
        mydll.CreateReverseTConnection.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseTConnection.restype = c_char_p
        b = mydll.CreateReverseTConnection(projectFolder, networkName, tempFolder, point1, point2)
        return _to_string(b)

    @staticmethod
    def EditControls(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.EditControls.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditControls.restype = c_char_p
        b = mydll.EditControls(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def EditElements(mydll, projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll.EditElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditElements.restype = c_char_p
        b = mydll.EditElements(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def EditPatternsCurves(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.EditPatternsCurves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditPatternsCurves.restype = c_char_p
        b = mydll.EditPatternsCurves(projectFolder, networkName, tempFolder)
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
    def InsertPump(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        b = mydll.InsertPump(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def InsertValve(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        b = mydll.InsertValve(projectFolder, networkName, tempFolder, point)
        return _to_string(b)

    @staticmethod
    def MoveValvePump(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point1 = _encode(point1)
        point2 = _encode(point2)

        mydll = _load_dll()
        mydll.MoveValvePump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.MoveValvePump.restype = c_char_p
        b = mydll.MoveValvePump(projectFolder, networkName, tempFolder, point1, point2)
        return _to_string(b)

    @staticmethod
    def RemoveElements(projectFolder, networkName, tempFolder, point, ids):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)
        ids = _encode(ids)

        mydll = _load_dll()
        mydll.RemoveElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElements.restype = c_char_p
        b = mydll.RemoveElements(projectFolder, networkName, tempFolder, point, ids)
        return _to_string(b)

    @staticmethod
    def ReverseLink(projectFolder, networkName, tempFolder, point, linkIds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)
        linkIds = _encode(linkIds)

        mydll = _load_dll()
        mydll.ReverseLink.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ReverseLink.restype = c_char_p
        b = mydll.ReverseLink(projectFolder, networkName, tempFolder, point, linkIds)
        return _to_string(b)

    @staticmethod
    def SplitMergeJunction(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point1 = _encode(point1)
        point2 = _encode(point2)

        mydll = _load_dll()
        mydll.SplitMergeJunction.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitMergeJunction.restype = c_char_p
        b = mydll.SplitMergeJunction(projectFolder, networkName, tempFolder, point1, point2)
        return _to_string(b)

    @staticmethod
    def SplitPipe(projectFolder, networkName, tempFolder, point):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)
        point = _encode(point)

        mydll = _load_dll()
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        b = mydll.SplitPipe(projectFolder, networkName, tempFolder, point)
        return _to_string(b)
