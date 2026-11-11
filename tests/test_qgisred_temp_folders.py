import os
import subprocess
import sys
import time

import pytest

from QGISRed.tools.utils.qgisred_temp_folders import (
    KIND_DLL,
    KIND_WORK,
    createSessionTempFolder,
    removeSessionTempFolder,
    removeStaleTempFolders,
)


@pytest.fixture(scope="module")
def deadPid():
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait()
    return process.pid


def _makeOld(path):
    old = time.time() - 3600
    os.utime(path, (old, old))


def _ownedFolder(root, name, pid):
    folder = root / name
    folder.mkdir()
    (folder / "file.shp").write_text("x")
    (root / (name + ".owner")).write_text(str(pid))
    return folder


def test_created_folder_has_its_owner_file_beside_it_not_inside(tmp_path):
    folder = createSessionTempFolder(KIND_WORK, tempRoot=str(tmp_path))

    assert os.path.basename(folder).startswith("QGISRed_work_")
    assert os.listdir(folder) == []
    with open(folder + ".owner") as ownerFile:
        assert ownerFile.read() == str(os.getpid())


def test_removing_a_session_folder_also_removes_its_owner_file(tmp_path):
    folder = createSessionTempFolder(KIND_DLL, tempRoot=str(tmp_path))

    removeSessionTempFolder(folder)

    assert os.listdir(tmp_path) == []


def test_folder_of_a_finished_session_is_removed(tmp_path, deadPid):
    _ownedFolder(tmp_path, "QGISRed_dll_abc", deadPid)

    removeStaleTempFolders(str(tmp_path))

    assert os.listdir(tmp_path) == []


def test_folder_of_a_running_session_is_kept(tmp_path):
    folder = _ownedFolder(tmp_path, "QGISRed_dll_abc", os.getpid())
    _makeOld(folder)

    removeStaleTempFolders(str(tmp_path))

    assert (folder / "file.shp").exists()


def test_old_unowned_folder_from_previous_versions_is_removed(tmp_path):
    folder = tmp_path / "QGISRed_abc"
    folder.mkdir()
    (folder / "GISRed.QGISRed.dll").write_text("x")
    _makeOld(folder)

    removeStaleTempFolders(str(tmp_path))

    assert not folder.exists()


def test_recent_unowned_folder_is_kept_while_its_owner_file_may_be_on_its_way(tmp_path):
    folder = tmp_path / "QGISRed_abc"
    folder.mkdir()

    removeStaleTempFolders(str(tmp_path))

    assert folder.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="only Windows locks a loaded library")
def test_unowned_folder_whose_library_is_locked_is_left_intact(tmp_path):
    folder = tmp_path / "QGISRed_abc"
    folder.mkdir()
    library = folder / "GISRed.QGISRed.dll"
    library.write_text("x")
    (folder / "epanet2.dll").write_text("x")
    _makeOld(folder)

    with open(library, "r"):
        removeStaleTempFolders(str(tmp_path))
        assert (folder / "epanet2.dll").exists()


def test_orphan_owner_file_of_a_finished_session_is_removed(tmp_path, deadPid):
    (tmp_path / "QGISRed_work_abc.owner").write_text(str(deadPid))

    removeStaleTempFolders(str(tmp_path))

    assert os.listdir(tmp_path) == []


def test_unrelated_entries_are_not_touched(tmp_path):
    (tmp_path / "Other_abc").mkdir()
    (tmp_path / "QGISRed_installer.zip").write_text("x")

    removeStaleTempFolders(str(tmp_path))

    assert sorted(os.listdir(tmp_path)) == ["Other_abc", "QGISRed_installer.zip"]
