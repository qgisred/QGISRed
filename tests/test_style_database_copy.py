"""The style database QGIS opens is never the file git tracks.

See INTERNALS.md §12: QGIS keeps whatever it opens locked for the whole session and Windows
will not let a locked file be replaced, so opening the tracked .bak would break `git pull`
while QGIS runs. A released plugin carries no .bak and reads the installer's copy instead.

Beside that default library the user has an own one in the per-user folder: a copy seeded once
from the default and never regenerated. A setting says which of the two the wizards read.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_styling_utils import STYLE_DATABASE_NAME, QGISRedStylingUtils
from QGISRed.tools.utils.qgisred_styling_utils import STYLE_LIBRARY_DEFAULT, STYLE_LIBRARY_OWNER, STYLE_LIBRARY_SETTING


@pytest.fixture(autouse=True)
def userFolder(tmp_path):
    """The per-user QGISRed folder, where the owner library lives."""
    folder = tmp_path / "user" / "QGISRed"
    with patch(
        "QGISRed.tools.utils.qgisred_filesystem_utils.QGISRedFileSystemUtils.getQGISRedFolder",
        return_value=str(folder),
    ):
        yield folder


@pytest.fixture
def selectedLibrary():
    """Patches the settings so the test decides which library is selected."""
    settings = MagicMock()
    settings.value.return_value = STYLE_LIBRARY_OWNER
    with patch("QGISRed.tools.utils.qgisred_styling_utils.QgsSettings", return_value=settings):
        yield settings


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
        assert QGISRedStylingUtils.defaultStyleDatabasePath() == str(pluginDefaults / STYLE_DATABASE_NAME)

    def test_a_release_falls_back_to_the_installer_copy(self, pluginDefaults, installDefaults):
        # The release ZIP leaves the .bak out, so only the installer's database is left.
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))

        assert QGISRedStylingUtils.defaultStyleDatabasePath() == str(installDefaults / STYLE_DATABASE_NAME)

    def test_the_opened_database_is_never_the_tracked_one(self, pluginDefaults, installDefaults):
        assert QGISRedStylingUtils.defaultStyleDatabasePath() != QGISRedStylingUtils.developmentStyleDatabasePath()

    def test_the_owner_library_lives_in_the_per_user_folder(self, pluginDefaults, installDefaults, userFolder):
        assert QGISRedStylingUtils.ownerStyleDatabasePath() == str(userFolder / STYLE_DATABASE_NAME)


class TestSelectedStyleLibrary:
    def test_the_owner_library_is_selected_until_the_user_says_otherwise(self, selectedLibrary):
        selectedLibrary.value.side_effect = lambda key, default=None: default

        assert QGISRedStylingUtils.selectedStyleLibrary() == STYLE_LIBRARY_OWNER

    def test_an_unknown_value_falls_back_to_the_owner_library(self, selectedLibrary):
        selectedLibrary.value.return_value = "something else"

        assert QGISRedStylingUtils.selectedStyleLibrary() == STYLE_LIBRARY_OWNER

    def test_the_choice_is_stored_under_the_legends_key(self, selectedLibrary):
        QGISRedStylingUtils.setSelectedStyleLibrary(STYLE_LIBRARY_DEFAULT)

        selectedLibrary.setValue.assert_called_once_with(STYLE_LIBRARY_SETTING, STYLE_LIBRARY_DEFAULT)

    def test_the_wizards_read_the_selected_library(self, pluginDefaults, installDefaults, selectedLibrary):
        selectedLibrary.value.return_value = STYLE_LIBRARY_DEFAULT
        assert QGISRedStylingUtils.styleDatabasePath() == QGISRedStylingUtils.defaultStyleDatabasePath()

        selectedLibrary.value.return_value = STYLE_LIBRARY_OWNER
        assert QGISRedStylingUtils.styleDatabasePath() == QGISRedStylingUtils.ownerStyleDatabasePath()


class TestEnsureStyleDatabase:
    def test_it_regenerates_the_working_copy(self, pluginDefaults, installDefaults):
        QGISRedStylingUtils.ensureStyleDatabase()

        workingPath = QGISRedStylingUtils.defaultStyleDatabasePath()
        assert open(workingPath, "rb").read() == b"tracked-v1"

    def test_the_tracked_file_always_wins(self, pluginDefaults, installDefaults):
        # The copy is derived, never edited by hand, so it is rewritten with no date check.
        QGISRedStylingUtils.ensureStyleDatabase()
        workingPath = QGISRedStylingUtils.defaultStyleDatabasePath()
        with open(workingPath, "wb") as handle:
            handle.write(b"stale")

        QGISRedStylingUtils.ensureStyleDatabase()

        assert open(workingPath, "rb").read() == b"tracked-v1"

    def test_a_reload_with_no_style_changes_never_touches_the_open_working_copy(
            self, pluginDefaults, installDefaults):
        # QGIS holds the working copy open for the whole session, so an ordinary plugin
        # reload (which never edits the .bak) must not attempt os.replace on it at all —
        # otherwise every such reload would hit a locked file for no reason.
        QGISRedStylingUtils.ensureStyleDatabase()

        with patch("os.replace") as replace:
            QGISRedStylingUtils.ensureStyleDatabase()

        replace.assert_not_called()

    def test_a_release_regenerates_nothing(self, pluginDefaults, installDefaults):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))

        QGISRedStylingUtils.ensureStyleDatabase()

        assert os.listdir(str(installDefaults)) == []

    def test_a_locked_copy_leaves_no_staged_file_behind(self, pluginDefaults, installDefaults):
        # Another QGIS instance holding the copy open makes os.replace fail; that instance
        # must keep reading a valid database and no staged file may pile up.
        QGISRedStylingUtils.ensureStyleDatabase()
        workingPath = QGISRedStylingUtils.defaultStyleDatabasePath()
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


class TestEnsureOwnerStyleDatabase:
    def test_the_owner_library_is_seeded_from_the_tracked_database(self, pluginDefaults, installDefaults, userFolder):
        QGISRedStylingUtils.ensureStyleDatabase()

        assert (userFolder / STYLE_DATABASE_NAME).read_bytes() == b"tracked-v1"

    def test_a_release_seeds_it_from_the_installer_copy(self, pluginDefaults, installDefaults, userFolder):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))
        (installDefaults / STYLE_DATABASE_NAME).write_bytes(b"installed")

        QGISRedStylingUtils.ensureStyleDatabase()

        assert (userFolder / STYLE_DATABASE_NAME).read_bytes() == b"installed"

    def test_the_users_edits_survive_every_reload(self, pluginDefaults, installDefaults, userFolder):
        QGISRedStylingUtils.ensureStyleDatabase()
        (userFolder / STYLE_DATABASE_NAME).write_bytes(b"edited by the user")
        (pluginDefaults / (STYLE_DATABASE_NAME + ".bak")).write_bytes(b"tracked-v2")

        QGISRedStylingUtils.ensureStyleDatabase()
        QGISRedStylingUtils.ensureOwnerStyleDatabase()

        assert (userFolder / STYLE_DATABASE_NAME).read_bytes() == b"edited by the user"

    def test_nothing_to_seed_from_leaves_no_file(self, pluginDefaults, installDefaults, userFolder):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))

        QGISRedStylingUtils.ensureOwnerStyleDatabase()

        assert not (userFolder / STYLE_DATABASE_NAME).exists()


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

    def test_it_registers_this_users_own_library(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()

        assert self.register(styleSettings, []) == [QGISRedStylingUtils.ownerStyleDatabasePath()]

    def test_a_path_from_another_machine_is_pruned(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        stale = "/home/someone/QGISRed/defaults/" + STYLE_DATABASE_NAME

        assert self.register(styleSettings, [stale]) == [QGISRedStylingUtils.ownerStyleDatabasePath()]

    def test_stale_paths_do_not_pile_up_over_sessions(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        older = ["/opt/QGISRed/defaults/" + STYLE_DATABASE_NAME,
                 "C:/other/defaults/" + STYLE_DATABASE_NAME]

        assert self.register(styleSettings, older) == [QGISRedStylingUtils.ownerStyleDatabasePath()]

    def test_databases_that_are_not_ours_are_left_alone(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        foreign = "/home/someone/my_own_symbols.db"

        assert self.register(styleSettings, [foreign]) == [foreign, QGISRedStylingUtils.ownerStyleDatabasePath()]

    def test_an_unchanged_list_is_not_rewritten(self, pluginDefaults, installDefaults, styleSettings):
        # Rewriting it would mark the project dirty every time one is opened.
        QGISRedStylingUtils.ensureStyleDatabase()
        styleSettings.styleDatabasePaths.return_value = [QGISRedStylingUtils.ownerStyleDatabasePath()]

        QGISRedStylingUtils.registerStyleDatabaseInProject()

        assert not styleSettings.setStyleDatabasePaths.called

    def test_a_missing_database_is_not_registered_but_stale_ones_still_go(
            self, pluginDefaults, installDefaults, styleSettings):
        os.remove(str(pluginDefaults / (STYLE_DATABASE_NAME + ".bak")))
        stale = "/opt/QGISRed/defaults/" + STYLE_DATABASE_NAME

        assert self.register(styleSettings, [stale]) == []


class TestUnregisterStyleDatabaseFromProject:
    """Removing the path is what lets QGIS release its file handle on unload.

    A literal string compare against what styleDatabasePaths() hands back is not
    enough: QGIS is free to return the path in a different case or separator style
    than the one styleDatabasePath() computes fresh, and a compare that then fails
    to match leaves the database registered forever, so QGIS never releases the
    handle and every reload hits "another instance is using the style database".
    """

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

    def test_it_drops_this_machines_database(self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        styleSettings.styleDatabasePaths.return_value = [QGISRedStylingUtils.ownerStyleDatabasePath()]

        QGISRedStylingUtils.unregisterStyleDatabaseFromProject()

        assert styleSettings.setStyleDatabasePaths.call_args[0][0] == []

    @pytest.mark.skipif(os.altsep is None, reason="path separator styles only differ on Windows")
    def test_it_drops_the_database_even_when_qgis_returns_the_other_separator_style(
            self, pluginDefaults, installDefaults, styleSettings):
        QGISRedStylingUtils.ensureStyleDatabase()
        reshaped = QGISRedStylingUtils.ownerStyleDatabasePath().replace(os.sep, os.altsep)
        styleSettings.styleDatabasePaths.return_value = [reshaped]

        QGISRedStylingUtils.unregisterStyleDatabaseFromProject()

        assert styleSettings.setStyleDatabasePaths.call_args[0][0] == []

    def test_a_database_that_is_not_ours_is_left_alone(self, pluginDefaults, installDefaults, styleSettings):
        foreign = "/home/someone/my_own_symbols.db"
        styleSettings.styleDatabasePaths.return_value = [foreign]

        QGISRedStylingUtils.unregisterStyleDatabaseFromProject()

        assert not styleSettings.setStyleDatabasePaths.called
