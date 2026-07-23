from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedToolsMixin:
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
