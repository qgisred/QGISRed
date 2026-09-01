"""The style database QGIS opens is never the file git tracks.

See INTERNALS.md §12: QGIS keeps whatever it opens locked for the whole session and Windows
will not let a locked file be replaced, so opening the tracked .bak would break `git pull`
while QGIS runs. A released plugin carries no .bak and reads the installer's copy instead.
"""
import os
from unittest.mock import patch

import pytest

from QGISRed.tools.utils.qgisred_styling_utils import STYLE_DATABASE_NAME, QGISRedStylingUtils


@pytest.fixture
def pluginDefaults(tmp_path):
    """A checkout's defaults folder, with the tracked .bak in it."""
    root = tmp_path / "plugin"
    (root / "defaults").mkdir(parents=True)
    (root / "defaults" / (STYLE_DATABASE_NAME + ".bak")).write_bytes(b"tracked-v1")
    with patch("QGISRed.tools.utils.qgisred_styling_utils._plugin_root", return_value=str(root)):
        yield root / "defaults"


@pytest.fixture
def installDefaults(tmp_path):
    folder = tmp_path / "install" / "defaults"
    folder.mkdir(parents=True)
    with patch(
        "QGISRed.tools.utils.qgisred_filesystem_utils.QGISRedFileSystemUtils.getDefaultsFolder",
        return_value=str(folder),
    ):
        yield folder


class TestStyleDatabasePaths:
    def test_the_tracked_database_is_a_bak_file_inside_defaults(self):
        path = QGISRedStylingUtils.developmentStyleDatabasePath()
        assert os.path.basename(path) == STYLE_DATABASE_NAME + ".bak"
        assert os.path.basename(os.path.dirname(path)) == "defaults"

    def test_the_tracked_database_is_part_of_the_checkout(self):
        assert os.path.exists(QGISRedStylingUtils.developmentStyleDatabasePath())

    def test_a_checkout_opens_the_db_beside_the_tracked_bak(self, pluginDefaults, installDefaults):
        assert QGISRedStylingUtils.styleDatabasePath() == str(pluginDefaults / STYLE_DATABASE_NAME)

    def test_a_release_falls_back_to_the_installer_copy(self, pluginDefaults, installDefaults):
        # The release ZIP leaves the .bak out, so only the installer's database is left.
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))

        assert QGISRedStylingUtils.styleDatabasePath() == str(installDefaults / STYLE_DATABASE_NAME)

    def test_the_opened_database_is_never_the_tracked_one(self, pluginDefaults, installDefaults):
        assert QGISRedStylingUtils.styleDatabasePath() != QGISRedStylingUtils.developmentStyleDatabasePath()


class TestEnsureStyleDatabase:
    def test_it_regenerates_the_working_copy(self, pluginDefaults, installDefaults):
        QGISRedStylingUtils.ensureStyleDatabase()

        workingPath = QGISRedStylingUtils.styleDatabasePath()
        assert open(workingPath, "rb").read() == b"tracked-v1"

    def test_the_tracked_file_always_wins(self, pluginDefaults, installDefaults):
        # The copy is derived, never edited by hand, so it is rewritten with no date check.
        QGISRedStylingUtils.ensureStyleDatabase()
        workingPath = QGISRedStylingUtils.styleDatabasePath()
        with open(workingPath, "wb") as handle:
            handle.write(b"stale")

        QGISRedStylingUtils.ensureStyleDatabase()

        assert open(workingPath, "rb").read() == b"tracked-v1"

    def test_a_release_regenerates_nothing(self, pluginDefaults, installDefaults):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))

        QGISRedStylingUtils.ensureStyleDatabase()

        assert os.listdir(str(installDefaults)) == []

    def test_a_locked_copy_leaves_no_staged_file_behind(self, pluginDefaults, installDefaults):
        # Another QGIS instance holding the copy open makes os.replace fail; that instance
        # must keep reading a valid database and no staged file may pile up.
        QGISRedStylingUtils.ensureStyleDatabase()
        workingPath = QGISRedStylingUtils.styleDatabasePath()
        (pluginDefaults / (STYLE_DATABASE_NAME + ".bak")).write_bytes(b"tracked-v2")

        with patch("os.replace", side_effect=OSError(13, "in use")):
            QGISRedStylingUtils.ensureStyleDatabase()

        assert open(workingPath, "rb").read() == b"tracked-v1"
        assert [name for name in os.listdir(str(pluginDefaults)) if name.endswith(".new")] == []

    def test_a_locked_copy_warns_instead_of_failing_silently(self, pluginDefaults, installDefaults):
        logTarget = "QGISRed.tools.utils.qgisred_styling_utils.QgsMessageLog"
        with patch("os.replace", side_effect=OSError(13, "in use")), patch(logTarget) as messageLog:
            QGISRedStylingUtils.ensureStyleDatabase()

        assert messageLog.logMessage.called

    def test_each_process_stages_to_its_own_file(self, pluginDefaults, installDefaults):
        # Two instances reloading at once must not write over each other's staged copy.
        staged = []
        with patch("os.replace", side_effect=lambda src, dst: staged.append(src)):
            with patch("os.getpid", return_value=111):
                QGISRedStylingUtils.ensureStyleDatabase()
            with patch("os.getpid", return_value=222):
                QGISRedStylingUtils.ensureStyleDatabase()

        assert staged[0] != staged[1]


class TestRegisterStyleDatabaseInProject:
    """A project stores the paths it was saved with, so stale ones must not pile up."""

    @pytest.fixture
    def styleSettings(self):
        from unittest.mock import MagicMock
        settings = MagicMock()
        settings.styleDatabasePaths.return_value = []
        project = MagicMock()
        project.styleSettings.return_value = settings
        with patch("QGISRed.tools.utils.qgisred_styling_utils.QgsProject") as qgsProject:
            qgsProject.instance.return_value = project
            yield settings

    def register(self, styleSettings, registered):
        styleSettings.styleDatabasePaths.return_value = list(registered)
        QGISRedStylingUtils.registerStyleDatabaseInProject()
        if not styleSettings.setStyleDatabasePaths.called:
            return list(registered)
        return styleSettings.setStyleDatabasePaths.call_args[0][0]

    def test_it_registers_this_machines_database(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()

        assert self.register(styleSettings, []) == [QGISRedStylingUtils.styleDatabasePath()]

    def test_a_path_from_another_machine_is_pruned(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        stale = "/home/someone/QGISRed/defaults/" + STYLE_DATABASE_NAME

        assert self.register(styleSettings, [stale]) == [QGISRedStylingUtils.styleDatabasePath()]

    def test_stale_paths_do_not_pile_up_over_sessions(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        older = ["/opt/QGISRed/defaults/" + STYLE_DATABASE_NAME,
                 "C:/other/defaults/" + STYLE_DATABASE_NAME]

        assert self.register(styleSettings, older) == [QGISRedStylingUtils.styleDatabasePath()]

    def test_databases_that_are_not_ours_are_left_alone(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        foreign = "/home/someone/my_own_symbols.db"

        assert self.register(styleSettings, [foreign]) == [foreign, QGISRedStylingUtils.styleDatabasePath()]

    def test_an_unchanged_list_is_not_rewritten(self, pluginDefaults, installDefaults, styleSettings):
        # Rewriting it would mark the project dirty every time one is opened.
        QGISRedStylingUtils.ensureStyleDatabase()
        styleSettings.styleDatabasePaths.return_value = [QGISRedStylingUtils.styleDatabasePath()]

        QGISRedStylingUtils.registerStyleDatabaseInProject()

        assert not styleSettings.setStyleDatabasePaths.called

    def test_a_missing_database_is_not_registered_but_stale_ones_still_go(
            self, pluginDefaults, installDefaults, styleSettings):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))
        stale = "/opt/QGISRed/defaults/" + STYLE_DATABASE_NAME

        assert self.register(styleSettings, [stale]) == []
