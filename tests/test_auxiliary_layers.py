# -*- coding: utf-8 -*-
"""The Demand Builder's auxiliary themes: naming, listing, and the Accept diff.

Several themes of each type can coexist, so what ties a file to its type — and therefore
to its qgisred_identifier and its style — is the token its name carries. These tests pin
that convention down, because everything else in the feature is derived from it.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.tools.utils.qgisred_auxiliary_layers import (
    AUXILIARY_LAYER_TYPES,
    AUXILIARY_TYPES_BY_KEY,
    DEFAULT_BASE_DEMAND_FIELD,
    composeBaseName,
    deleteTheme,
    isValidThemeName,
    listThemes,
    parseBaseName,
)

_UTILS_CLS = "QGISRed.sections.layer_management_section.QGISRedLayerUtils"

CONSUMPTION = AUXILIARY_TYPES_BY_KEY["ConsumptionPoints"]
LINKS = AUXILIARY_TYPES_BY_KEY["DemandLinks"]
SECTORS = AUXILIARY_TYPES_BY_KEY["Sectors"]


class TestComposeBaseName:
    def test_a_named_theme_carries_network_type_and_name(self):
        assert composeBaseName("Net", CONSUMPTION, "Facturacion2024") == \
            "Net_DemandsBuilder_ConsumptionPoints_Facturacion2024"

    def test_the_demands_manager_theme_has_no_trailing_name(self):
        assert composeBaseName("Net", SECTORS) == "Net_DemandsBuilder_Sectors"

    def test_the_composed_name_parses_back(self):
        base = composeBaseName("Net", LINKS, "Enlaces")
        assert parseBaseName(base, "Net") == (LINKS, "Enlaces")


class TestParseBaseName:
    def test_a_named_theme_resolves_to_its_type(self):
        layerType, name = parseBaseName("Net_DemandsBuilder_ConsumptionPoints_Padron", "Net")
        assert layerType is CONSUMPTION
        assert name == "Padron"

    def test_the_unnamed_theme_resolves_with_an_empty_name(self):
        assert parseBaseName("Net_DemandsBuilder_Sectors", "Net") == (SECTORS, "")

    def test_a_theme_name_may_contain_underscores(self):
        _, name = parseBaseName("Net_DemandsBuilder_DemandLinks_Alta_Zona_2", "Net")
        assert name == "Alta_Zona_2"

    def test_the_network_prefix_is_optional(self):
        """A folder copied between projects must still read."""
        assert parseBaseName("DemandsBuilder_Sectors_Barrios") == (SECTORS, "Barrios")

    def test_a_network_named_after_a_token_does_not_confuse_it(self):
        layerType, name = parseBaseName("Sectors_DemandsBuilder_Sectors_A", "Sectors")
        assert layerType is SECTORS
        assert name == "A"

    def test_isolated_demands_connections_is_not_a_managed_theme(self):
        """It lives in the same folder but the layer manager does not offer it."""
        assert parseBaseName("Net_DemandsBuilder_IsolatedDemandsServiceConnections", "Net") == (None, "")

    def test_an_unrelated_file_is_rejected(self):
        assert parseBaseName("Net_Pipes", "Net") == (None, "")

    def test_an_empty_name_is_rejected(self):
        assert parseBaseName("", "Net") == (None, "")


class TestIsValidThemeName:
    @pytest.mark.parametrize("name", ["Facturacion2024", "Alta_Zona_2", "a"])
    def test_plain_names_are_accepted(self, name):
        assert isValidThemeName(name) is True

    @pytest.mark.parametrize("name", ["", "  ", " Padron", "Padron ", "a/b", "a\\b", "a:b", "a*b", "a?b"])
    def test_a_name_that_could_escape_the_folder_is_rejected(self, name):
        assert isValidThemeName(name) is False


def _uniform(path):
    """Same normalisation the dialog applies, so expectations line up on Windows."""
    from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
    return QGISRedFileSystemUtils().getUniformedPath(path)


def _touchTheme(folder, baseName):
    os.makedirs(folder, exist_ok=True)
    for extension in (".shp", ".shx", ".dbf"):
        open(os.path.join(folder, baseName + extension), "w").close()
    return os.path.join(folder, baseName + ".shp")


class TestListThemes:
    def test_only_recognised_shapefiles_are_listed(self, tmp_path):
        folder = str(tmp_path)
        _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        _touchTheme(folder, "Net_DemandsBuilder_IsolatedDemandsServiceConnections")
        _touchTheme(folder, "Net_Pipes")

        themes = listThemes(folder, "Net")

        assert [(t.key, name) for t, name, _ in themes] == [("Sectors", "Barrios")]

    def test_themes_are_sorted_by_type_then_name(self, tmp_path):
        folder = str(tmp_path)
        _touchTheme(folder, "Net_DemandsBuilder_Sectors_Zonas")
        _touchTheme(folder, "Net_DemandsBuilder_ConsumptionPoints_Padron")
        _touchTheme(folder, "Net_DemandsBuilder_ConsumptionPoints_Facturacion")

        themes = listThemes(folder, "Net")

        assert [name for _, name, _ in themes] == ["Facturacion", "Padron", "Zonas"]

    def test_a_missing_folder_is_not_an_error(self, tmp_path):
        assert listThemes(str(tmp_path / "nope"), "Net") == []


class TestDeleteTheme:
    def test_every_sidecar_goes_with_the_shapefile(self, tmp_path):
        """A theme that leaves its .dbf behind comes back as a broken row."""
        folder = str(tmp_path)
        path = _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        open(os.path.join(folder, "Net_DemandsBuilder_Sectors_Barrios.prj"), "w").close()

        assert deleteTheme(path) == ""
        assert os.listdir(folder) == []

    def test_deleting_what_is_already_gone_is_not_an_error(self, tmp_path):
        assert deleteTheme(str(tmp_path / "Net_DemandsBuilder_Sectors_X.shp")) == ""


class TestIdentifierNormalisation:
    """A user-named theme must still resolve to the identifier of its type."""

    def _normalize(self, name):
        from QGISRed.tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
        utils = object.__new__(QGISRedIdentifierUtils)
        return utils._normalizeDemandsBuilderLayerType(name)

    def test_a_named_theme_collapses_onto_its_type(self):
        assert self._normalize("Net_DemandsBuilder_ConsumptionPoints_Facturacion2024") == \
            "demandsbuilder_consumptionpoints"

    def test_the_unnamed_theme_still_collapses(self):
        assert self._normalize("Net_DemandsBuilder_Sectors") == "demandsbuilder_sectors"

    def test_the_token_passed_by_the_loader_collapses(self):
        assert self._normalize("DemandsBuilder_DemandLinks") == "demandsbuilder_demandlinks"

    def test_isolated_demands_connections_keeps_its_own_identifier(self):
        assert self._normalize("Net_DemandsBuilder_IsolatedDemandsServiceConnections") == \
            "demandsbuilder_isolateddemandsserviceconnections"

    def test_an_unrelated_name_is_left_alone(self):
        assert self._normalize("Net_Pipes") == "Net_Pipes"


class TestApplyAuxiliaryLayerSelection:
    def _makeSection(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()
        section.layerOperationInProgress = False
        section.openAuxiliaryThemes = MagicMock()
        section.closeAuxiliaryThemes = MagicMock()
        return section

    def test_only_unchecked_themes_are_closed(self):
        section = self._makeSection()
        managed = ["C:/proj/a.shp", "C:/proj/b.shp", "C:/proj/c.shp"]

        section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], managed)

        assert section.closeAuxiliaryThemes.call_args[0][0] == ["C:/proj/b.shp", "C:/proj/c.shp"]

    def test_checked_themes_are_opened(self):
        section = self._makeSection()

        section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], ["C:/proj/a.shp"])

        section.openAuxiliaryThemes.assert_called_once_with(["C:/proj/a.shp"])
        assert section.closeAuxiliaryThemes.call_args[0][0] == []

    def test_the_comparison_ignores_path_case(self):
        """Windows hands back the same file spelled either way."""
        section = self._makeSection()

        section.applyAuxiliaryLayerSelection(["C:/proj/A.shp"], ["c:/proj/a.shp"])

        assert section.closeAuxiliaryThemes.call_args[0][0] == []

    def test_the_flag_is_released_even_when_opening_fails(self):
        section = self._makeSection()
        section.openAuxiliaryThemes.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], ["C:/proj/a.shp"])

        assert section.layerOperationInProgress is False


class TestCloseAuxiliaryThemes:
    def test_the_layer_is_removed_from_the_project(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()

        layer = MagicMock()
        layer.id.return_value = "layer-1"
        with patch(_UTILS_CLS) as utilsCls, \
                patch("QGISRed.sections.layer_management_section.QgsProject") as project:
            utilsCls.return_value._findLayerByPath.return_value = layer
            section.closeAuxiliaryThemes(["C:/proj/a.shp"])

        project.instance.return_value.removeMapLayer.assert_called_once_with("layer-1")

    def test_nothing_happens_without_paths(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        with patch(_UTILS_CLS) as utilsCls:
            section.closeAuxiliaryThemes([])
        utilsCls.assert_not_called()

    def test_the_path_is_resolved_before_looking_the_layer_up(self):
        """_findLayerByPath compares against getUniformedPath, which resolves the path.

        Handing it an os.path.join path left the layer open and its shapefile locked, so
        deleting the theme afterwards failed with 'file in use'.
        """
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()

        with patch(_UTILS_CLS) as utilsCls, \
                patch("QGISRed.sections.layer_management_section.QgsProject"):
            utils = utilsCls.return_value
            utils._findLayerByPath.return_value = None
            section.closeAuxiliaryThemes(["C:/proj/Auxiliary Layers/a.shp"])

        assert utils._findLayerByPath.call_args[0][0] == _uniform("C:/proj/Auxiliary Layers/a.shp")


# ---------------------------------------------------------------------------
# The Auxiliary layers tab
# ---------------------------------------------------------------------------

_DIALOG_MOD = "QGISRed.ui.project.qgisred_layermanagement_dialog"


class _FakeItem:
    """Stands in for QTableWidgetItem, which is a bare mock in this harness."""

    def __init__(self, text=""):
        self._text = text
        self._checkState = None
        self._data = {}

    def setFlags(self, flags):
        self._flags = flags

    def setCheckState(self, state):
        self._checkState = state

    def checkState(self):
        return self._checkState

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)

    def text(self):
        return self._text


class _FakeTable:
    def __init__(self):
        self._rows = 0
        self._items = {}
        self._current = -1

    def setRowCount(self, rows):
        self._rows = rows
        self._items = {key: item for key, item in self._items.items() if key[0] < rows}

    def rowCount(self):
        return self._rows

    def setItem(self, row, column, item):
        self._items[(row, column)] = item

    def item(self, row, column):
        return self._items.get((row, column))

    def currentRow(self):
        return self._current


def _qt():
    """The Qt the dialog captured at import time.

    Another test module may have swapped sys.modules['qgis.PyQt.QtCore'] since, and the
    mocked enum members are only identical to themselves.
    """
    from QGISRed.ui.project import qgisred_layermanagement_dialog
    return qgisred_layermanagement_dialog.Qt


def _makeDialog(projectDirectory, networkName="Net"):
    from QGISRed.ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog

    dialog = QGISRedLayerManagementDialog.__new__(QGISRedLayerManagementDialog)
    dialog.NetworkName = networkName
    dialog.ProjectDirectory = str(projectDirectory)
    dialog.iface = MagicMock()
    dialog.utils = MagicMock()
    dialog.utils.getLayers.return_value = []
    dialog.parent = MagicMock()
    dialog.messageBar = MagicMock()
    dialog.crs = MagicMock()
    dialog.crs.toWkt.return_value = ""
    dialog.tbAuxiliary = _FakeTable()
    dialog.elements = []
    return dialog


def _auxFolder(projectDirectory):
    from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
    folder = os.path.join(str(projectDirectory), LAYER_TYPE_CONFIG["DemandsBuilder"]["subdir"])
    os.makedirs(folder, exist_ok=True)
    return folder


class TestFillAuxiliaryTable:
    def test_one_row_per_theme_on_disk(self, tmp_path):
        folder = _auxFolder(tmp_path)
        _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        _touchTheme(folder, "Net_DemandsBuilder_ConsumptionPoints_Padron")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.rowCount() == 2

    def test_a_loaded_theme_comes_back_checked(self, tmp_path):
        Qt = _qt()
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(return_value={os.path.normcase(path)})

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).checkState() == Qt.CheckState.Checked

    def test_an_unloaded_theme_comes_back_unchecked(self, tmp_path):
        Qt = _qt()
        _touchTheme(_auxFolder(tmp_path), "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(return_value=set())

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).checkState() == Qt.CheckState.Unchecked

    def test_the_name_and_the_type_sit_beside_the_checkbox(self, tmp_path):
        """The checkbox has a column of its own; name and type follow it."""
        _touchTheme(_auxFolder(tmp_path), "Net_DemandsBuilder_DemandLinks_p1")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).text() == ""
        assert dialog.tbAuxiliary.item(0, 1).text() == "p1"
        assert dialog.tbAuxiliary.item(0, 2).text() is not None

    def test_the_demands_manager_theme_is_labelled_as_the_default_one(self, tmp_path):
        _touchTheme(_auxFolder(tmp_path), "Net_DemandsBuilder_Sectors")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 1).text() != ""

    def test_the_row_carries_the_path_of_its_theme(self, tmp_path):
        Qt = _qt()
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).data(Qt.ItemDataRole.UserRole) == _uniform(path)

    def test_stale_rows_do_not_survive_a_refresh(self, tmp_path):
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
            deleteTheme(path)
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.rowCount() == 0
        assert dialog.auxiliaryRowPaths() == []


class TestAuxiliaryRowPaths:
    def _fill(self, tmp_path, checked):
        folder = _auxFolder(tmp_path)
        first = _touchTheme(folder, "Net_DemandsBuilder_ConsumptionPoints_A")
        second = _touchTheme(folder, "Net_DemandsBuilder_Sectors_B")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(
            return_value={os.path.normcase(p) for p in checked}
        )
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
        return dialog, first, second

    def test_every_row_is_reported_as_managed(self, tmp_path):
        dialog, first, second = self._fill(tmp_path, [])
        assert set(dialog.auxiliaryRowPaths()) == {_uniform(first), _uniform(second)}

    def test_nothing_loaded_means_nothing_selected(self, tmp_path):
        dialog, _, _ = self._fill(tmp_path, [])
        assert dialog.auxiliaryRowPaths(onlyChecked=True) == []

    def test_only_the_loaded_theme_is_selected(self, tmp_path):
        folder = _auxFolder(tmp_path)
        loaded = os.path.join(folder, "Net_DemandsBuilder_ConsumptionPoints_A.shp")
        dialog, first, _ = self._fill(tmp_path, [loaded])
        assert dialog.auxiliaryRowPaths(onlyChecked=True) == [_uniform(first)]


class TestCreateAuxiliaryTheme:
    """Writing the file is the DLL's job; the dialog composes the path and reacts."""

    def _run(self, dialog, layerType, name, resMessage="True"):
        def write(_project, _network, _themeType, path, _baseDemand):
            if resMessage == "True":
                _touchTheme(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0])
            return resMessage

        with patch(_DIALOG_MOD + "._NewAuxiliaryThemeDialog") as dialogCls, \
                patch(_DIALOG_MOD + ".GISRed") as gisred, \
                patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialogCls.return_value.exec.return_value = True
            dialogCls.return_value.selection.return_value = (layerType, name)
            gisred.CreateAuxiliaryLayer.side_effect = write
            dialog.createAuxiliaryTheme()
            return gisred

    def test_the_dll_is_asked_for_the_composed_path(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "Barrios")

        expected = os.path.join(_auxFolder(tmp_path), "Net_DemandsBuilder_Sectors_Barrios.shp")
        assert gisred.CreateAuxiliaryLayer.call_args[0] == (
            dialog.ProjectDirectory, "Net", "Sectors", expected, DEFAULT_BASE_DEMAND_FIELD)

    def test_the_created_theme_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios")

        expected = os.path.join(_auxFolder(tmp_path), "Net_DemandsBuilder_Sectors_Barrios.shp")
        dialog.parent.openAuxiliaryThemes.assert_called_once_with([expected])

    def test_the_new_row_shows_up_in_the_table(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, LINKS, "Enlaces")

        assert dialog.tbAuxiliary.rowCount() == 1

    def test_a_dll_error_is_reported_and_nothing_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios", resMessage="Unknown auxiliary theme type")

        dialog.parent.openAuxiliaryThemes.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 2

    def test_a_dll_warning_is_reported_and_nothing_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios", resMessage="False")

        dialog.parent.openAuxiliaryThemes.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_an_existing_name_is_refused_before_calling_the_dll(self, tmp_path):
        folder = _auxFolder(tmp_path)
        _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "Barrios")

        gisred.CreateAuxiliaryLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_a_name_that_could_escape_the_folder_is_refused(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "../evil")

        gisred.CreateAuxiliaryLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_cancelling_writes_nothing(self, tmp_path):
        folder = _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + "._NewAuxiliaryThemeDialog") as dialogCls, \
                patch(_DIALOG_MOD + ".GISRed") as gisred:
            dialogCls.return_value.exec.return_value = False
            dialog.createAuxiliaryTheme()

        assert os.listdir(folder) == []
        gisred.CreateAuxiliaryLayer.assert_not_called()


class TestDeleteAuxiliaryTheme:
    def _dialog(self, tmp_path):
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
        dialog.tbAuxiliary._current = 0
        return dialog, path

    def _confirm(self, dialog, accepted=True):
        with patch(_DIALOG_MOD + ".QMessageBox") as messageBox, \
                patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            answer = messageBox.StandardButton.Yes if accepted else messageBox.StandardButton.No
            messageBox.question.return_value = answer
            dialog.deleteAuxiliaryTheme()

    def test_the_files_are_removed(self, tmp_path):
        dialog, path = self._dialog(tmp_path)

        self._confirm(dialog)

        assert not os.path.exists(path)
        assert os.listdir(os.path.dirname(path)) == []

    def test_the_layer_is_unloaded_before_the_file_is_deleted(self, tmp_path):
        """Deleting a shapefile QGIS still holds leaves a handle pointing at nothing."""
        dialog, path = self._dialog(tmp_path)
        order = []
        dialog.parent.closeAuxiliaryThemes.side_effect = \
            lambda paths: order.append(("close", os.path.exists(path)))

        self._confirm(dialog)
        order.append(("deleted", not os.path.exists(path)))

        assert order == [("close", True), ("deleted", True)]

    def test_declining_the_confirmation_keeps_everything(self, tmp_path):
        dialog, path = self._dialog(tmp_path)

        self._confirm(dialog, accepted=False)

        assert os.path.exists(path)
        dialog.parent.closeAuxiliaryThemes.assert_not_called()

    def test_deleting_with_no_row_selected_only_warns(self, tmp_path):
        dialog, path = self._dialog(tmp_path)
        dialog.tbAuxiliary._current = -1

        self._confirm(dialog)

        assert os.path.exists(path)
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1


class TestAcceptSendsBothSelections:
    def test_auxiliary_themes_are_applied_before_the_input_layers(self, tmp_path):
        """applyInputLayerSelection ends in updateMetadata, which must see the final tree."""
        from QGISRed.ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog

        _touchTheme(_auxFolder(tmp_path), "Net_DemandsBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.crs = dialog.originalCrs = MagicMock()
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        order = []
        dialog.parent.applyAuxiliaryLayerSelection.side_effect = lambda *a: order.append("aux")
        dialog.parent.applyInputLayerSelection.side_effect = lambda *a: order.append("inputs")

        base = QGISRedLayerManagementDialog.__mro__[1]
        original = getattr(base, "accept", None)
        base.accept = MagicMock()
        try:
            dialog.accept()
        finally:
            if original is None:
                del base.accept
            else:
                base.accept = original

        assert order == ["aux", "inputs"]
        selected, managed = dialog.parent.applyAuxiliaryLayerSelection.call_args[0]
        assert managed == dialog.auxiliaryRowPaths()
        assert selected == []
