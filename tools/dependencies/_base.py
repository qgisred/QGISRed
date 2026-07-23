from ..utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
import os
import sys
from ctypes import CDLL
if sys.platform == "win32":
    from ctypes import WinDLL


_dll_directories = {}


def _load_dll():
    dll_path = QGISRedFileSystemUtils().getCurrentDll() if QGISRedFileSystemUtils.DllTempoFolder else ""
    if not os.path.exists(dll_path):
        QGISRedFileSystemUtils().copyDependencies()  # Attempt to restore the DLL file
        if QGISRedFileSystemUtils.DllTempoFolder is None:
            raise FileNotFoundError("GISRed dependencies not found in " + QGISRedFileSystemUtils().getGISRedDllFolder())
        dll_path = QGISRedFileSystemUtils().getCurrentDll()
    dll_folder = os.path.dirname(dll_path)
    if sys.platform == "win32":
        os.chdir(dll_folder)  # Remove when QGISRedDeprecated is deleted
        if dll_folder not in _dll_directories:
            _dll_directories[dll_folder] = os.add_dll_directory(dll_folder)
        return WinDLL(dll_path)
    return CDLL(dll_path)


def _encode(string):
    return string.encode("utf-8")


def _to_string(binary):
    return "".join(map(chr, binary))


class QGISRedBase:
    @staticmethod
    def CreateInstance():
        return _load_dll()

    @staticmethod
    def encode(string):
        return _encode(string)

    @staticmethod
    def toString(binary):
        return _to_string(binary)
