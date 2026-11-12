# -*- coding: utf-8 -*-
"""The optional content groups of the export dialog show their translated layer-tree names."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from QGISRed.ui.general import qgisred_exportproject_dialog as dialog_module
from QGISRed.ui.general.qgisred_exportproject_dialog import QGISRedExportProjectDialog

SPANISH = {"Results": "Resultados", "Issues": "Incidencias", "Trees": "Árboles"}


def _translate(context, text, *args):
    return SPANISH.get(text, text) if context == "QGISRedGroups" else text


def _group(key, dirName, exists):
    return SimpleNamespace(key=key, dirName=dirName, exists=exists, fileCount=3, sizeBytes=1024)


def _labels(groups):
    dialog = QGISRedExportProjectDialog.__new__(QGISRedExportProjectDialog)
    dialog.tr = lambda text: text
    dialog._formatSize = lambda size: "1 KB"
    dialog._groupCheckboxes = {}
    dialog.lbBaseLayers = MagicMock()
    dialog.gbContent = MagicMock()
    dialog.verticalLayoutContent = MagicMock()
    dialog._plan = SimpleNamespace(baseFileCount=1, baseSizeBytes=1, contentGroups=groups,
                                   includeGroups={g.key for g in groups})
    with patch.object(dialog_module, "QCheckBox", side_effect=lambda parent: MagicMock()), \
         patch("QGISRed.tools.utils.qgisred_layer_utils.QCoreApplication.translate", side_effect=_translate):
        dialog._fillContentGroups()
    return {key: box.setText.call_args[0][0] for key, box in dialog._groupCheckboxes.items()}


def test_groups_with_data_are_translated():
    labels = _labels([_group("results", "Results", True), _group("Trees", "Trees", True)])
    assert labels == {"results": "Resultados (3 files, 1 KB)", "Trees": "Árboles (3 files, 1 KB)"}


def test_empty_groups_are_translated():
    assert _labels([_group("issues", "Issues", False)]) == {"issues": "Incidencias — no data"}


def test_unknown_folders_keep_their_name():
    assert _labels([_group("Extra", "Extra", True)]) == {"Extra": "Extra (3 files, 1 KB)"}
