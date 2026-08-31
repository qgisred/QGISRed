# -*- coding: utf-8 -*-
"""Tests for the pipe restrictions applied when importing punctual service connections.

The import dialog lets the user narrow the pipes that can host a service connection, either by a
maximum diameter or by the current selection of the Pipes layer. Both travel to the DLL as two extra
string parameters of ImportFromShps.
"""
import os
import re
from unittest.mock import MagicMock

import pytest

from QGISRed.ui.general.qgisred_import_dialog import QGISRedImportDialog

UI_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui", "general", "qgisred_import_dialog.ui"
)


def makeDialog(isPunctual=True, newProject=False, selectedPipeIds=None, maxDiameterChecked=False,
               selectedPipesChecked=False, maxDiameterText="0"):
    dialog = QGISRedImportDialog.__new__(QGISRedImportDialog)
    dialog.tr = lambda text: text
    dialog.noneLabel = "Ninguna"          # el centinela va traducido; nada debe compararlo con "None"
    dialog.isPunctualConnection = isPunctual
    dialog.NewProject = newProject
    dialog.selectedPipeIds = list(selectedPipeIds or [])

    dialog.chkScMaxDiameter = MagicMock()
    dialog.chkScMaxDiameter.isChecked.return_value = maxDiameterChecked
    dialog.chkScSelectedPipes = MagicMock()
    dialog.chkScSelectedPipes.isChecked.return_value = selectedPipesChecked
    dialog.tbScMaxDiameter = MagicMock()
    dialog.tbScMaxDiameter.text.return_value = maxDiameterText
    dialog.lbScSelectedPipes = MagicMock()
    return dialog


class TestTheUiDeclaresTheControls:
    def test_the_ui_declares_every_widget_the_restrictions_use(self):
        with open(UI_PATH, encoding="utf-8") as f:
            declared = set(re.findall(r'name="(\w+)"', f.read()))
        needed = {"chkScMaxDiameter", "tbScMaxDiameter", "lbScDiameterUnits",
                  "chkScSelectedPipes", "lbScSelectedPipes"}
        assert not needed - declared

    def test_each_restriction_has_its_own_row_and_none_collide(self):
        """gbServiceConnection used to sit on row 2; the two restriction rows took 2 and 3, so
        everything below has to move down or Qt overlaps the widgets."""
        import xml.etree.ElementTree as ET

        rows = {}
        for layout in ET.parse(UI_PATH).getroot().iter("layout"):
            if layout.get("name") != "gridLayout_33":
                continue
            for item in layout.findall("item"):
                rows.setdefault(item.get("row"), []).append(list(item)[0].get("name"))

        assert rows, "gridLayout_33 not found"
        assert all(len(names) == 1 for names in rows.values()), rows
        # The selection restriction comes first, the diameter one below it
        assert rows["2"] == ["horizontalLayout_scSelectedPipes"]
        assert rows["3"] == ["horizontalLayout_scMaxDiameter"]
        assert rows["4"] == ["gbServiceConnection"]


class TestTheNoneSentinelIsConsistent:
    """cbPipeLayer was filled with self.tr("None") -- "Ninguna" in Spanish -- while
    createShpsNames/createShpFields compared the current text against the literal "None". The Pipes
    layer was therefore always sent to the DLL as '<folder>/Ninguna.shp' even when left unset. Now
    every combo and every comparison goes through the single self.noneLabel."""

    def _source(self):
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "ui", "general", "qgisred_import_dialog.py")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_the_sentinel_is_translated_exactly_once(self):
        source = self._source()
        assert source.count('self.tr("None")') == 1
        assert 'self.noneLabel = self.tr("None")' in source

    def test_no_bare_none_literal_survives(self):
        """A literal left behind would silently stop matching the translated combo text."""
        source = self._source()
        for line in source.splitlines():
            if 'self.noneLabel = self.tr("None")' in line:
                continue
            assert '"None"' not in line, line.strip()

    def test_every_layer_combo_uses_the_shared_sentinel(self):
        source = self._source()
        combos = ["cbPipeLayer", "cbValveLayer", "cbPumpLayer", "cbTankLayer", "cbReservoirLayer",
                  "cbJunctionLayer", "cbServiceConnectionLayer", "cbIsolationValveLayer", "cbMeterLayer"]
        for combo in combos:
            assert "%s.addItem(self.noneLabel)" % combo in source, combo

    def test_an_unset_pipes_combo_keeps_the_pipes_tag_out_of_the_shapes_string(self):
        dialog = QGISRedImportDialog.__new__(QGISRedImportDialog)
        dialog.noneLabel = "Ninguna"
        dialog.tbShpDirectory = MagicMock()
        dialog.tbShpDirectory.text.return_value = "C:/shps"
        for combo in ("cbPipeLayer", "cbValveLayer", "cbPumpLayer", "cbTankLayer", "cbReservoirLayer",
                      "cbJunctionLayer", "cbIsolationValveLayer", "cbMeterLayer"):
            setattr(dialog, combo, MagicMock())
            getattr(dialog, combo).currentText.return_value = "Ninguna"
        dialog.cbServiceConnectionLayer = MagicMock()
        dialog.cbServiceConnectionLayer.currentText.return_value = "serviceConnections"

        shapes = dialog.createShpsNames()

        assert "[PIPES]" not in shapes
        assert "Ninguna" not in shapes
        assert "[SERVICECONNECTIONS]" in shapes


class TestReadingTheSelectedPipes:
    def test_a_brand_new_project_has_nothing_selected(self):
        """The first import brings the pipes in the same operation, so there is no selection to
        read and the parent must not even be queried."""
        dialog = makeDialog(newProject=True)
        dialog.parent = MagicMock()

        assert dialog._getSelectedPipeIds() == []
        dialog.parent.getSelectedFeaturesIds.assert_not_called()

    def test_the_pipe_ids_come_from_the_parent(self):
        dialog = makeDialog()
        dialog.parent = MagicMock()
        dialog.parent.getSelectedFeaturesIds.return_value = True
        dialog.parent.selectedIds = {"Pipes": ["P1", "P2"], "Junctions": ["J1"]}

        assert dialog._getSelectedPipeIds() == ["P1", "P2"]

    def test_a_null_id_in_the_selection_is_treated_as_no_selection(self):
        dialog = makeDialog()
        dialog.parent = MagicMock()
        dialog.parent.getSelectedFeaturesIds.return_value = False
        dialog.parent.selectedIds = {"Pipes": ["P1"]}

        assert dialog._getSelectedPipeIds() == []

    def test_no_pipes_selected_yields_an_empty_list(self):
        dialog = makeDialog()
        dialog.parent = MagicMock()
        dialog.parent.getSelectedFeaturesIds.return_value = True
        dialog.parent.selectedIds = {"Junctions": ["J1"]}

        assert dialog._getSelectedPipeIds() == []


class TestEnablingTheControls:
    def test_a_line_layer_disables_both_restrictions(self):
        """They only make sense when the connections come as points and have to be projected."""
        dialog = makeDialog(isPunctual=False, selectedPipeIds=["P1"])
        dialog.updateServiceConnectionRestrictions()

        dialog.chkScMaxDiameter.setEnabled.assert_called_once_with(False)
        dialog.chkScSelectedPipes.setEnabled.assert_called_once_with(False)
        dialog.tbScMaxDiameter.setEnabled.assert_called_once_with(False)

    def test_without_a_selection_only_the_diameter_restriction_is_offered(self):
        dialog = makeDialog(selectedPipeIds=[])
        dialog.updateServiceConnectionRestrictions()

        dialog.chkScMaxDiameter.setEnabled.assert_called_once_with(True)
        dialog.chkScSelectedPipes.setEnabled.assert_called_once_with(False)

    def test_with_a_selection_both_restrictions_are_offered(self):
        dialog = makeDialog(selectedPipeIds=["P1", "P2"])
        dialog.updateServiceConnectionRestrictions()

        dialog.chkScMaxDiameter.setEnabled.assert_called_once_with(True)
        dialog.chkScSelectedPipes.setEnabled.assert_called_once_with(True)

    def test_the_diameter_box_follows_its_checkbox(self):
        dialog = makeDialog(maxDiameterChecked=True)
        dialog.updateServiceConnectionRestrictions()
        dialog.tbScMaxDiameter.setEnabled.assert_called_once_with(True)

    def test_a_disabled_checkbox_is_unchecked_so_no_hidden_restriction_survives(self):
        dialog = makeDialog(isPunctual=False, maxDiameterChecked=True, selectedPipesChecked=True)
        dialog.chkScMaxDiameter.isEnabled.return_value = False
        dialog.chkScSelectedPipes.isEnabled.return_value = False

        dialog.updateServiceConnectionRestrictions()

        dialog.chkScMaxDiameter.setChecked.assert_called_once_with(False)
        dialog.chkScSelectedPipes.setChecked.assert_called_once_with(False)

    def test_the_label_reports_how_many_pipes_are_selected(self):
        dialog = makeDialog(selectedPipeIds=["P1", "P2", "P3"])
        dialog.updateServiceConnectionRestrictions()
        assert "3" in dialog.lbScSelectedPipes.setText.call_args[0][0]

    def test_without_a_selection_the_label_stays_empty(self):
        dialog = makeDialog(selectedPipeIds=[])
        dialog.updateServiceConnectionRestrictions()
        assert dialog.lbScSelectedPipes.setText.call_args[0][0] == ""

    def test_a_line_layer_leaves_the_label_empty(self):
        dialog = makeDialog(isPunctual=False, selectedPipeIds=["P1"])
        dialog.updateServiceConnectionRestrictions()
        assert dialog.lbScSelectedPipes.setText.call_args[0][0] == ""


class TestTheUnitLabels:
    """Nothing converts these two values, so each label has to name the project's own unit: the
    diameter is compared against Pipe.Diameter and the length is written to the Length attribute."""

    def _dialog(self, newProject, flowUnit="LPS"):
        dialog = QGISRedImportDialog.__new__(QGISRedImportDialog)
        dialog.NewProject = newProject
        dialog.cbUnits = MagicMock()
        dialog.cbUnits.currentText.return_value = flowUnit
        return dialog

    def test_a_new_si_project_uses_millimetres_and_metres(self):
        dialog = self._dialog(True, "LPS")
        assert dialog._diameterUnitAbbreviation() == "mm"
        assert dialog._lengthUnitAbbreviation() == "m"

    def test_a_new_us_project_uses_inches_and_feet(self):
        dialog = self._dialog(True, "GPM")
        assert dialog._diameterUnitAbbreviation() == "in"
        assert dialog._lengthUnitAbbreviation() == "ft"

    def test_an_existing_project_asks_the_field_utils_for_the_service_connection_row(self, monkeypatch):
        import QGISRed.ui.general.qgisred_import_dialog as module

        utils = MagicMock(**{"getUnitAbbreviation.return_value": "ft"})
        monkeypatch.setattr(module, "QGISRedFieldUtils", lambda: utils)

        assert self._dialog(False)._lengthUnitAbbreviation() == "ft"
        utils.getUnitAbbreviation.assert_called_with("Service Connection", "Length")

    def test_an_unknown_unit_falls_back_to_the_si_abbreviation(self, monkeypatch):
        import QGISRed.ui.general.qgisred_import_dialog as module

        monkeypatch.setattr(module, "QGISRedFieldUtils",
                            lambda: MagicMock(**{"getUnitAbbreviation.return_value": ""}))
        dialog = self._dialog(False)

        assert dialog._diameterUnitAbbreviation() == "mm"
        assert dialog._lengthUnitAbbreviation() == "m"


@pytest.mark.mock_only
class TestWhatReachesTheDll:
    """importShpProject is driven end to end with stubs so the two new parameters can be read off
    the ImportFromShps call."""

    def _run(self, monkeypatch, **kwargs):
        import QGISRed.ui.general.qgisred_import_dialog as module

        calls = []
        monkeypatch.setattr(module.GISRed, "ImportFromShps", lambda *a, **k: calls.append(a) or "True")
        monkeypatch.setattr(module, "QApplication", MagicMock())
        monkeypatch.setattr(module.os.path, "exists", lambda path: True)

        messages = []
        dialog = makeDialog(**kwargs)
        dialog.pushMessage = lambda *a, **k: messages.append(a)
        dialog.validationsCreateProject = lambda: True
        dialog.createShpFields = lambda: "[PIPES]Id;"
        dialog.createShpsNames = lambda: "[PIPES]pipes,"
        dialog.close = lambda: None
        dialog.NewProject = False
        dialog.ProjectDirectory = "C:/net"
        dialog.NetworkName = "Net"
        dialog.tbShpDirectory = MagicMock()
        dialog.tbTolerance = MagicMock()
        dialog.tbTolerance.text.return_value = "0"
        dialog.tbScLength = MagicMock()
        dialog.tbScLength.text.return_value = "5"
        dialog.crs = MagicMock()
        dialog.crs.authid.return_value = "EPSG:25830"
        dialog.parent = MagicMock()
        for combo in ("cbServiceConnectionLayer", "cbIsolationValveLayer", "cbMeterLayer"):
            setattr(dialog, combo, MagicMock())
            getattr(dialog, combo).currentText.return_value = dialog.noneLabel

        dialog.importShpProject()
        return calls, messages

    def test_without_restrictions_the_dll_gets_the_neutral_values(self, monkeypatch):
        calls, messages = self._run(monkeypatch)

        assert not messages
        assert calls[0][-2:] == ("0", "")

    def test_the_max_diameter_is_forwarded(self, monkeypatch):
        calls, messages = self._run(monkeypatch, maxDiameterChecked=True, maxDiameterText="200")

        assert not messages
        assert calls[0][-2:] == ("200", "")

    def test_the_selected_pipe_ids_travel_semicolon_separated(self, monkeypatch):
        calls, messages = self._run(
            monkeypatch, selectedPipesChecked=True, selectedPipeIds=["P1", "P2", "P3"]
        )

        assert not messages
        assert calls[0][-2:] == ("0", "P1;P2;P3")

    def test_both_restrictions_can_travel_together(self, monkeypatch):
        calls, messages = self._run(
            monkeypatch, maxDiameterChecked=True, maxDiameterText="150",
            selectedPipesChecked=True, selectedPipeIds=["P7"]
        )

        assert calls[0][-2:] == ("150", "P7")

    def test_a_line_layer_ignores_both_restrictions_even_if_ticked(self, monkeypatch):
        calls, _ = self._run(
            monkeypatch, isPunctual=False, maxDiameterChecked=True, maxDiameterText="150",
            selectedPipesChecked=True, selectedPipeIds=["P7"]
        )

        assert calls[0][-2:] == ("0", "")

    @pytest.mark.parametrize("text", ["abc", "0", "-5"])
    def test_an_invalid_diameter_stops_the_import(self, monkeypatch, text):
        calls, messages = self._run(monkeypatch, maxDiameterChecked=True, maxDiameterText=text)

        assert not calls
        assert messages
