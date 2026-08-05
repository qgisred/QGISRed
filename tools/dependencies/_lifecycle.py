"""Plugin lifecycle DLL calls (no toolbar: used by LifecycleSection on load/unload)."""

from ctypes import c_char_p
from ._base import _load_dll, _encode, _to_string


class QGISRedLifecycleMixin:
    @staticmethod
    def GetVersion():
        mydll = _load_dll()
        mydll.GetVersion.argtypes = ()
        mydll.GetVersion.restype = c_char_p
        b = mydll.GetVersion()
        return _to_string(b)

    @staticmethod
    def SetCulture(culture):
        culture = _encode(culture)

        mydll = _load_dll()
        mydll.SetCulture.argtypes = (c_char_p,)
        mydll.SetCulture.restype = c_char_p
        b = mydll.SetCulture(culture)
        return _to_string(b)
