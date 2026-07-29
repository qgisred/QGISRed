# -*- coding: utf-8 -*-
"""Warning shown in the legend editor when Appearance is rewriting the result symbols.

The sizes in the editor's table ignore those settings, so editing them without resetting
Appearance first can leave the style inconsistent.
"""
import os
from unittest.mock import MagicMock

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.tools.utils.qgisred_filesystem_utils import DIR_RESULTS

DEFAULTS = 'pipeFactor="1.0" symbolFactor="1.0" arrowFactor="1.0" proportional="false" nodeBorder="false"'


def _dialog(tmp_path, networkName="Net"):
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.projectDirectory = str(tmp_path / "project")
    dialog.networkName = networkName
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.customProperty.return_value = "qgisred_node_pressure"
    return dialog


def _writeConfig(tmp_path, symbols=DEFAULTS, extra=""):
    folder = os.path.join(str(tmp_path / "project"), DIR_RESULTS)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "Net_Results_Config.cfg")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f'<?xml version="1.0"?><AppearanceConfig>{extra}<Symbols {symbols}/></AppearanceConfig>')
    return path


class TestHasAppearanceOverrides:
    def test_no_file_means_nothing_is_being_rewritten(self, tmp_path):
        assert _dialog(tmp_path).hasAppearanceOverrides() is False

    def test_a_file_with_everything_at_its_default_does_not_warn(self, tmp_path):
        # The file is also written when only decimals or labels change, and warning about
        # those would teach the user to ignore the banner.
        _writeConfig(tmp_path)

        assert _dialog(tmp_path).hasAppearanceOverrides() is False

    def test_decimals_and_labels_alone_do_not_warn(self, tmp_path):
        _writeConfig(tmp_path, extra='<Labels fontSize="14" showNodeId="true"/>'
                                     '<Decimals><Var name="Pressure" value="4"/></Decimals>')

        assert _dialog(tmp_path).hasAppearanceOverrides() is False

    @pytest.mark.parametrize("symbols", [
        'pipeFactor="2.0" symbolFactor="1.0" arrowFactor="1.0" proportional="false" nodeBorder="false"',
        'pipeFactor="1.0" symbolFactor="0.5" arrowFactor="1.0" proportional="false" nodeBorder="false"',
        'pipeFactor="1.0" symbolFactor="1.0" arrowFactor="3.0" proportional="false" nodeBorder="false"',
        'pipeFactor="1.0" symbolFactor="1.0" arrowFactor="1.0" proportional="true" nodeBorder="false"',
        'pipeFactor="1.0" symbolFactor="1.0" arrowFactor="1.0" proportional="false" nodeBorder="true"',
    ])
    def test_each_setting_that_rewrites_symbols_warns(self, tmp_path, symbols):
        _writeConfig(tmp_path, symbols)

        assert _dialog(tmp_path).hasAppearanceOverrides() is True

    @pytest.mark.parametrize("written", ["1", "1.000000", "1.0"])
    def test_a_factor_of_one_however_it_is_written_is_untouched(self, tmp_path, written):
        _writeConfig(tmp_path, f'pipeFactor="{written}" symbolFactor="1.0" arrowFactor="1.0"'
                               ' proportional="false" nodeBorder="false"')

        assert _dialog(tmp_path).hasAppearanceOverrides() is False

    def test_a_corrupt_file_does_not_break_the_dialog(self, tmp_path):
        folder = os.path.join(str(tmp_path / "project"), DIR_RESULTS)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "Net_Results_Config.cfg"), "w", encoding="utf-8") as handle:
            handle.write("not xml at all")

        assert _dialog(tmp_path).hasAppearanceOverrides() is False

    def test_without_a_project_there_is_nothing_to_read(self, tmp_path):
        dialog = _dialog(tmp_path, networkName="")

        assert dialog.appearanceConfigPath() is None
        assert dialog.hasAppearanceOverrides() is False


class TestUpdateAppearanceWarning:
    def _dialogWithBanner(self, tmp_path, identifier):
        dialog = _dialog(tmp_path)
        dialog.currentLayer.customProperty.return_value = identifier
        dialog.appearanceWarningWidget = MagicMock()
        return dialog

    def test_shown_on_a_result_layer_being_rewritten(self, tmp_path):
        _writeConfig(tmp_path, 'pipeFactor="2.0" symbolFactor="1.0" arrowFactor="1.0"'
                               ' proportional="false" nodeBorder="false"')
        dialog = self._dialogWithBanner(tmp_path, "qgisred_link_flow")

        dialog.updateAppearanceWarning()

        dialog.appearanceWarningWidget.setVisible.assert_called_once_with(True)

    def test_hidden_on_a_layer_appearance_does_not_touch(self, tmp_path):
        # Appearance only rewrites result layers, so a pipe layer must never warn.
        _writeConfig(tmp_path, 'pipeFactor="2.0" symbolFactor="1.0" arrowFactor="1.0"'
                               ' proportional="false" nodeBorder="false"')
        dialog = self._dialogWithBanner(tmp_path, "qgisred_pipes")

        dialog.updateAppearanceWarning()

        dialog.appearanceWarningWidget.setVisible.assert_called_once_with(False)

    def test_hidden_once_appearance_has_been_reset(self, tmp_path):
        # Resetting deletes the file, which is what puts the banner away.
        dialog = self._dialogWithBanner(tmp_path, "qgisred_node_pressure")

        dialog.updateAppearanceWarning()

        dialog.appearanceWarningWidget.setVisible.assert_called_once_with(False)
