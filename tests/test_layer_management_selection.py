# -*- coding: utf-8 -*-
"""Tests for the layer-management dialog and the Accept path behind it.

The dialog hands over the checked elements plus the full list of elements it manages;
the section turns that into a *difference*: only unchecked elements are closed, and only
elements the dialog owns may be closed at all. A CRS change is the exception, because
the DLL rewrites every shapefile underneath the open layers.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

import os
from unittest.mock import MagicMock, patch

from QGISRed.ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog, _Element

_UTILS_CLS = "QGISRed.sections.layer_management_section.QGISRedLayerUtils"
_CRS_SELECTOR = "QGISRed.ui.project.qgisred_layermanagement_dialog.QgsGenericProjectionSelector"
_GISRED = "QGISRed.ui.project.qgisred_layermanagement_dialog.GISRed"

# Mirrors qgisred.py.
OWN_MAIN = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
COMPLEMENTARY = ["IsolationValves", "ServiceConnections", "Meters"]
MANAGED = [
    "Pipes", "Junctions", "Tanks", "Reservoirs", "Valves", "Pumps",
    "Demands", "Sources", "IsolationValves", "ServiceConnections", "Meters",
]


# ---------------------------------------------------------------------------
# Section — applyInputLayerSelection
# ---------------------------------------------------------------------------

def _makeSection(project_dir="C:/proj", network_name="TestNet"):
    from QGISRed.sections.layer_management_section import LayerManagementSection

    section = object.__new__(LayerManagementSection)
    section.ProjectDirectory = project_dir
    section.NetworkName = network_name
    section.iface = MagicMock()
    section.ownMainLayers = list(OWN_MAIN)
    section.ownFiles = ["DefaultValues", "Options"]
    section.complementaryLayers = list(COMPLEMENTARY)
    section.layerOperationInProgress = False
    return section


def _apply(section, selected, epsg=None, managed=None):
    """Run applyInputLayerSelection with the deferred task hook stubbed out."""
    with patch(_UTILS_CLS) as utilsCls:
        utilsCls.return_value.runTask = MagicMock()
        section.applyInputLayerSelection(selected, managed or MANAGED, epsg)
    return section


class TestLayersToClose:
    def test_only_unchecked_elements_are_closed(self):
        section = _apply(_makeSection(), ["Pipes", "Junctions", "Valves"])
        assert "Pipes" not in section.layersToClose
        assert "Junctions" not in section.layersToClose
        assert "Valves" not in section.layersToClose
        assert "Tanks" in section.layersToClose
        assert "Meters" in section.layersToClose

    def test_checked_elements_are_never_closed(self):
        section = _apply(_makeSection(), list(MANAGED))
        assert section.layersToClose == []

    def test_nothing_outside_the_managed_list_is_closed(self):
        """Whatever else the user keeps inside Inputs must survive Accept untouched."""
        section = _apply(_makeSection(), [])
        assert set(section.layersToClose) == set(MANAGED)

    def test_selected_layers_are_the_ones_reopened(self):
        section = _apply(_makeSection(), ["Pipes", "Meters"])
        assert section.specificLayers == ["Pipes", "Meters"]

    def test_caller_list_is_not_mutated(self):
        selected = ["Pipes"]
        _apply(_makeSection(), selected)
        assert selected == ["Pipes"]

    def test_flags_the_operation_as_in_progress(self):
        section = _apply(_makeSection(), ["Pipes"])
        assert section.layerOperationInProgress is True


class TestCrsChange:
    def test_every_managed_element_is_closed_when_the_crs_changes(self):
        """ChangeCrs rewrites every shapefile, so no input layer may stay open."""
        section = _apply(_makeSection(), ["Pipes"], epsg="25830")
        assert set(section.layersToClose) == set(MANAGED)

    def test_epsg_is_stored_for_the_change_crs_step(self):
        section = _apply(_makeSection(), ["Pipes"], epsg="25830")
        assert section.specificEpsg == "25830"

    def test_no_crs_change_leaves_epsg_unset(self):
        section = _apply(_makeSection(), ["Pipes"])
        assert section.specificEpsg is None


class TestCloseUnselectedInputLayers:
    def test_closes_exactly_the_computed_list(self):
        section = _makeSection()
        section.layersToClose = ["Tanks", "Meters"]
        section.specificEpsg = None

        with patch(_UTILS_CLS) as utilsCls:
            utils = utilsCls.return_value
            section.closeUnselectedInputLayers()

        utils.removeLayers.assert_called_once_with(["Tanks", "Meters"])

    def test_dbf_tables_are_only_closed_on_a_crs_change(self):
        section = _makeSection()
        section.layersToClose = ["Tanks"]
        section.specificEpsg = "25830"

        with patch(_UTILS_CLS) as utilsCls:
            utils = utilsCls.return_value
            section.closeUnselectedInputLayers()

        assert utils.removeLayers.call_args_list[1][0] == (section.ownFiles, ".dbf")


class TestOpenElementLayer:
    def test_guards_the_legend_signal_while_the_layer_is_added(self):
        """runLegendChanged must not rewrite the metadata halfway through the open."""
        section = _makeSection()
        seen = []
        section.getInputGroup = MagicMock()
        section.updateMetadata = MagicMock(side_effect=lambda: seen.append(section.layerOperationInProgress))

        with patch(_UTILS_CLS):
            section.openElementLayer("Meters")

        assert seen == [True]
        assert section.layerOperationInProgress is False


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

def _makeDialog(projectDirectory, networkName="TestNet"):
    dialog = QGISRedLayerManagementDialog.__new__(QGISRedLayerManagementDialog)
    dialog.NetworkName = networkName
    dialog.ProjectDirectory = str(projectDirectory)
    dialog.iface = MagicMock()
    dialog.utils = MagicMock()
    dialog.utils.getLayers.return_value = []
    dialog.utils.isLayerOpened.return_value = False
    dialog.parent = MagicMock()
    dialog.messageBar = MagicMock()
    dialog.tbCRS = MagicMock()
    dialog.elements = []
    for name in MANAGED:
        checkBox, button = MagicMock(), MagicMock()
        checkBox.text.return_value = name
        dialog.elements.append(_Element(name, checkBox, button, name in COMPLEMENTARY))
    return dialog


def _element(dialog, name):
    return next(element for element in dialog.elements if element.name == name)


def _openLayer(identifier, name):
    layer = MagicMock()
    layer.customProperty.return_value = identifier
    layer.name.return_value = name
    return layer


def _touch(folder, networkName, *elements):
    for element in elements:
        open(os.path.join(str(folder), networkName + "_" + element + ".shp"), "w").close()


class TestSetProperties:
    def test_create_button_only_shows_when_the_shapefile_is_missing(self, tmp_path):
        _touch(tmp_path, "TestNet", "Pipes")
        dialog = _makeDialog(tmp_path)

        dialog.setProperties()

        _element(dialog, "Pipes").createButton.setVisible.assert_called_once_with(False)
        _element(dialog, "Meters").createButton.setVisible.assert_called_once_with(True)

    def test_a_missing_shapefile_leaves_the_checkbox_disabled(self, tmp_path):
        dialog = _makeDialog(tmp_path)

        dialog.setProperties()

        _element(dialog, "Meters").checkBox.setEnabled.assert_called_once_with(False)

    def test_open_layers_come_back_checked(self, tmp_path):
        _touch(tmp_path, "TestNet", "Meters")
        dialog = _makeDialog(tmp_path)
        dialog.utils.getLayers.return_value = [_openLayer("qgisred_meters", "My meters")]

        dialog.setProperties()

        _element(dialog, "Meters").checkBox.setChecked.assert_called_once_with(True)

    def test_the_row_shows_the_real_layer_name(self, tmp_path):
        _touch(tmp_path, "TestNet", "Meters")
        dialog = _makeDialog(tmp_path)
        dialog.utils.getLayers.return_value = [_openLayer("qgisred_meters", "My meters")]

        dialog.setProperties()

        _element(dialog, "Meters").checkBox.setText.assert_called_once_with("My meters")

    def test_a_closed_layer_keeps_the_translated_ui_text(self, tmp_path):
        _touch(tmp_path, "TestNet", "Meters")
        dialog = _makeDialog(tmp_path)

        dialog.setProperties()

        _element(dialog, "Meters").checkBox.setText.assert_called_once_with("Meters")

    def test_projects_without_identifiers_still_match_by_path(self, tmp_path):
        _touch(tmp_path, "TestNet", "Meters")
        dialog = _makeDialog(tmp_path)
        dialog.utils.isLayerOpened.side_effect = lambda name: name == "Meters"

        dialog.setProperties()

        _element(dialog, "Meters").checkBox.setChecked.assert_called_once_with(True)

    def test_open_pipes_cannot_be_unchecked(self, tmp_path):
        """Pipes carry the network: unloading them would leave the project headless."""
        _touch(tmp_path, "TestNet", "Pipes")
        dialog = _makeDialog(tmp_path)
        dialog.utils.getLayers.return_value = [_openLayer("qgisred_pipes", "Pipes")]

        dialog.setProperties()

        _element(dialog, "Pipes").checkBox.setEnabled.assert_called_once_with(False)

    def test_closed_pipes_can_be_checked(self, tmp_path):
        _touch(tmp_path, "TestNet", "Pipes")
        dialog = _makeDialog(tmp_path)

        dialog.setProperties()

        _element(dialog, "Pipes").checkBox.setEnabled.assert_called_once_with(True)


class TestSelectCRS:
    def _select(self, dialog, authid, valid=True, accepted=True):
        crs = MagicMock()
        crs.isValid.return_value = valid
        crs.authid.return_value = authid
        with patch(_CRS_SELECTOR) as selectorCls:
            selectorCls.return_value.exec.return_value = accepted
            selectorCls.return_value.crs.return_value = crs
            dialog.selectCRS()
        return crs

    def test_an_epsg_crs_is_accepted(self, tmp_path):
        dialog = _makeDialog(tmp_path)
        dialog.crs = MagicMock()

        crs = self._select(dialog, "EPSG:25830")

        assert dialog.crs is crs

    def test_a_custom_crs_is_refused_with_a_warning(self, tmp_path):
        """The DLL only reprojects from an EPSG code; USER:xxxxx means nothing to it."""
        dialog = _makeDialog(tmp_path)
        original = dialog.crs = MagicMock()

        self._select(dialog, "USER:100001")

        assert dialog.crs is original
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_cancelling_the_selector_changes_nothing(self, tmp_path):
        dialog = _makeDialog(tmp_path)
        original = dialog.crs = MagicMock()

        self._select(dialog, "EPSG:25830", accepted=False)

        assert dialog.crs is original
        dialog.messageBar.pushMessage.assert_not_called()

    def test_an_invalid_crs_is_ignored_silently(self, tmp_path):
        dialog = _makeDialog(tmp_path)
        original = dialog.crs = MagicMock()

        self._select(dialog, "EPSG:25830", valid=False)

        assert dialog.crs is original


class TestCreateElement:
    def _create(self, dialog, resMessage, name="Meters"):
        dialog.setProperties = MagicMock()
        with patch(_GISRED) as gisred:
            gisred.CreateLayer.return_value = resMessage
            dialog.createElement(_element(dialog, name))
        return gisred

    def test_a_complementary_element_travels_in_the_fourth_argument(self, tmp_path):
        dialog = _makeDialog(tmp_path)

        gisred = self._create(dialog, "True", "Meters")

        assert gisred.CreateLayer.call_args[0] == (dialog.ProjectDirectory, "TestNet", "", "Meters")

    def test_a_basic_element_travels_in_the_third_argument(self, tmp_path):
        dialog = _makeDialog(tmp_path)

        gisred = self._create(dialog, "True", "Pipes")

        assert gisred.CreateLayer.call_args[0] == (dialog.ProjectDirectory, "TestNet", "Pipes", "")

    def test_a_created_element_is_opened_and_the_rows_refreshed(self, tmp_path):
        dialog = _makeDialog(tmp_path)

        self._create(dialog, "True")

        dialog.parent.openElementLayer.assert_called_once_with("Meters")
        dialog.setProperties.assert_called_once()

    def test_an_error_is_reported_and_nothing_is_opened(self, tmp_path):
        """The banner lives in this dialog, so it must not close while showing a message."""
        dialog = _makeDialog(tmp_path)

        self._create(dialog, "Some DLL failure")

        dialog.parent.openElementLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][1] == "Some DLL failure"
        assert dialog.messageBar.pushMessage.call_args[0][2] == 2

    def test_a_warning_is_reported_and_nothing_is_opened(self, tmp_path):
        dialog = _makeDialog(tmp_path)

        self._create(dialog, "False")

        dialog.parent.openElementLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1


class TestAccept:
    def _accept(self, dialog, monkeypatch):
        # QDialog is a bare stub in the test harness and has no accept() to chain to.
        monkeypatch.setattr(QGISRedLayerManagementDialog.__mro__[1], "accept", MagicMock(), raising=False)
        dialog.accept()
        return dialog.parent.applyInputLayerSelection.call_args[0]

    def test_only_the_checked_elements_are_sent(self, tmp_path, monkeypatch):
        dialog = _makeDialog(tmp_path)
        dialog.crs = dialog.originalCrs = MagicMock()
        for element in dialog.elements:
            element.checkBox.isChecked.return_value = element.name in ("Pipes", "Meters")

        selected, managed, epsg = self._accept(dialog, monkeypatch)

        assert selected == ["Pipes", "Meters"]
        assert managed == MANAGED

    def test_an_unchanged_crs_sends_no_epsg(self, tmp_path, monkeypatch):
        dialog = _makeDialog(tmp_path)
        dialog.crs = dialog.originalCrs = MagicMock()
        for element in dialog.elements:
            element.checkBox.isChecked.return_value = False

        assert self._accept(dialog, monkeypatch)[2] is None

    def test_a_changed_crs_sends_the_bare_epsg_code(self, tmp_path, monkeypatch):
        dialog = _makeDialog(tmp_path)
        dialog.originalCrs = MagicMock()
        dialog.crs = MagicMock()
        dialog.crs.authid.return_value = "EPSG:25830"
        for element in dialog.elements:
            element.checkBox.isChecked.return_value = False

        assert self._accept(dialog, monkeypatch)[2] == "25830"
