# -*- coding: utf-8 -*-
"""Temporary folders of a QGIS session and the cleanup of those left behind."""
from contextlib import suppress
import os
import shutil
import sys
import tempfile
import time

TEMP_PREFIX = "QGISRed_"
KIND_DLL = "dll"
KIND_WORK = "work"
KIND_COMPUTE = "compute"

# The owner file sits next to the folder, never inside it: callers copy every file of
# the work and compute folders elsewhere (e.g. into Results/).
_OWNER_SUFFIX = ".owner"
# A folder without an owner file is either from an older plugin version or one whose
# owner file is still being written; a recent one is given the benefit of the doubt.
_UNOWNED_GRACE_SECONDS = 120
_LIBRARY_PREFIX = "GISRed.QGISRed."


def createSessionTempFolder(kind, tempRoot=None):
    folder = tempfile.mkdtemp(prefix="{}{}_".format(TEMP_PREFIX, kind), dir=tempRoot)
    with open(folder + _OWNER_SUFFIX, "w") as ownerFile:
        ownerFile.write(str(os.getpid()))
    return folder


def removeSessionTempFolder(folder):
    if not folder:
        return
    shutil.rmtree(folder, ignore_errors=True)
    with suppress(OSError):
        os.remove(folder + _OWNER_SUFFIX)


def removeStaleTempFolders(tempRoot=None):
    """Delete the QGISRed temp folders of sessions that are no longer running."""
    root = tempRoot or tempfile.gettempdir()
    try:
        names = os.listdir(root)
    except OSError:
        return
    for name in names:
        if not name.startswith(TEMP_PREFIX):
            continue
        path = os.path.join(root, name)
        if name.endswith(_OWNER_SUFFIX):
            if not os.path.isdir(path[:-len(_OWNER_SUFFIX)]) and not _isOwnerAlive(path):
                with suppress(OSError):
                    os.remove(path)
            continue
        if os.path.isdir(path) and not _isInUse(path):
            removeSessionTempFolder(path)


def _isInUse(folder):
    ownerPath = folder + _OWNER_SUFFIX
    if os.path.exists(ownerPath):
        return _isOwnerAlive(ownerPath)
    return _isRecent(folder) or _holdsLoadedLibrary(folder)


def _isOwnerAlive(ownerPath):
    try:
        with open(ownerPath, "r") as ownerFile:
            pid = int(ownerFile.read().strip())
    except (OSError, ValueError):
        return _isRecent(ownerPath)
    return _isProcessAlive(pid)


def _isRecent(path):
    try:
        return time.time() - os.path.getmtime(path) < _UNOWNED_GRACE_SECONDS
    except OSError:
        return False


def _holdsLoadedLibrary(folder):
    # Windows refuses to delete a loaded library, so a failed delete means some process
    # still runs from this folder; deleting the rest would break it.
    for name in os.listdir(folder):
        if not name.startswith(_LIBRARY_PREFIX):
            continue
        try:
            os.remove(os.path.join(folder, name))
        except OSError:
            return True
    return False


def _isProcessAlive(pid):
    if pid == os.getpid():
        return True
    if sys.platform == "win32":
        return _isWindowsProcessAlive(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def _isWindowsProcessAlive(pid):
    import ctypes
    from ctypes import wintypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    ERROR_ACCESS_DENIED = 5
    STILL_ACTIVE = 259

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)

    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ctypes.get_last_error() == ERROR_ACCESS_DENIED
    try:
        exitCode = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exitCode)):
            return True
        return exitCode.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)
