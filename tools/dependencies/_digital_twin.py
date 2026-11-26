"""Digital Twin toolbar DLL calls (service connections, isolation valves, meters, readings/SCADA)."""

import locale
from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


def _decode_text(binary):
    try:
        return binary.decode("utf-8")
    except UnicodeDecodeError:
        return binary.decode(locale.getpreferredencoding(False), "replace")


class QGISRedDigitalTwinMixin:
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
    def ManageFieldData(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.ManageFieldData.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ManageFieldData.restype = c_char_p
        b = mydll.ManageFieldData(projectFolder, networkName, tempFolder)
        return _to_string(b)

    @staticmethod
    def GetFieldDataSignals(projectFolder, networkName):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)

        mydll = _load_dll()
        mydll.GetFieldDataSignals.argtypes = (c_char_p, c_char_p)
        mydll.GetFieldDataSignals.restype = c_char_p
        b = mydll.GetFieldDataSignals(projectFolder, networkName)
        return _decode_text(b)

    @staticmethod
    def GetFieldDataValues(projectFolder, networkName, signalIds, elapsedSeconds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        signalIds = _encode(signalIds)
        elapsedSeconds = _encode(elapsedSeconds)

        mydll = _load_dll()
        mydll.GetFieldDataValues.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.GetFieldDataValues.restype = c_char_p
        b = mydll.GetFieldDataValues(projectFolder, networkName, signalIds, elapsedSeconds)
        return _decode_text(b)

    @staticmethod
    def GetFieldDataSeries(projectFolder, networkName, requests, startSeconds, endSeconds, stepSeconds):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        requests = _encode(requests)
        startSeconds = _encode(startSeconds)
        endSeconds = _encode(endSeconds)
        stepSeconds = _encode(stepSeconds)

        mydll = _load_dll()
        mydll.GetFieldDataSeries.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.GetFieldDataSeries.restype = c_char_p
        b = mydll.GetFieldDataSeries(projectFolder, networkName, requests, startSeconds, endSeconds, stepSeconds)
        return _decode_text(b)

    @staticmethod
    def SetInitialStatusPipes(projectFolder, networkName, tempFolder):
        projectFolder = _encode(projectFolder)
        networkName = _encode(networkName)
        tempFolder = _encode(tempFolder)

        mydll = _load_dll()
        mydll.SetInitialStatusPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.SetInitialStatusPipes.restype = c_char_p
        b = mydll.SetInitialStatusPipes(projectFolder, networkName, tempFolder)
        return _to_string(b)
