# -*- coding: utf-8 -*-
"""Tests for the unified QGZ post-open flow across the three opening scenarios.

These tests verify that _post_qgz_open() is called with a correct snapshot
in all scenarios, and that its internal steps happen in the right order.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, call

# ---------------------------------------------------------------------------
# Patch target constants
# ---------------------------------------------------------------------------
# _post_qgz_open does `from ..tools.utils.qgisred_styling_utils import QGISRedStylingUtils`
# so the class is fetched from the styling_utils module namespace.
_STYLING_CLS = "QGISRed.tools.utils.qgisred_styling_utils.QGISRedStylingUtils"
# QgsProject is imported at the top of project_management_section, so it lives there.
_QGS_PROJECT = "QGISRed.sections.project_management_section.QgsProject"
_SECTION_MOD = "QGISRed.sections.project_management_section"


# ---------------------------------------------------------------------------
# Helpers — a minimal stand-in for ProjectManagementSection
# ---------------------------------------------------------------------------

def _make_section(project_dir="C:/proj", network_name="TestNet"):
    """Return an object that has just enough state to exercise the methods
    extracted from ProjectManagementSection, without importing QGIS at all."""
    # Import here so conftest mocks are already installed.
    from QGISRed.sections.project_management_section import ProjectManagementSection

    # Build a bare instance without calling __init__ (which requires the full
    # plugin to be initialised).
    section = object.__new__(ProjectManagementSection)
    section.ProjectDirectory = project_dir
    section.NetworkName = network_name
    section.TemporalFolder = "Temporal Folder"
    section.iface = MagicMock()
    section.layerOperationInProgress = False
    return section


def _empty_snapshot():
    return {"inputs_to_restyle": [], "results_no_id": False, "results_with_id": []}


# ---------------------------------------------------------------------------
# Tests for _post_qgz_open
# ---------------------------------------------------------------------------

class TestPostQgzOpen:
    """_post_qgz_open must write the plugin version, migrate layers,
    restyle inputs, and apply NullStyle / remove old result layers."""

    def _make_snapshot(self, inputs_to_restyle=None, results_no_id=False, results_with_id=None):
        return {
            "inputs_to_restyle": inputs_to_restyle or [],
            "results_no_id": results_no_id,
            "results_with_id": results_with_id or [],
        }

    def test_calls_write_plugin_version(self):
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        mock_qgs_project = MagicMock()
        with patch(_STYLING_CLS), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(self._make_snapshot())

        section._writePluginVersionToProject.assert_called_once()

    def test_calls_migrate_layers_to_subfolders(self):
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        mock_qgs_project = MagicMock()
        with patch(_STYLING_CLS), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(self._make_snapshot())

        section._migrateLayersToSubfolders.assert_called_once()

    def test_migrate_called_before_styling(self):
        """_migrateLayersToSubfolders must run before style operations."""
        call_order = []

        section = _make_section()
        section._writePluginVersionToProject = MagicMock(side_effect=lambda: call_order.append("version"))
        section._migrateLayersToSubfolders = MagicMock(side_effect=lambda: call_order.append("migrate"))
        section.removeOldResultLayers = MagicMock()

        mock_styling_cls = MagicMock()
        mock_styling = mock_styling_cls.return_value
        mock_styling.setStyle = MagicMock(side_effect=lambda *a: call_order.append("setStyle"))

        snapshot = self._make_snapshot(inputs_to_restyle=[("layer1", "pipes")])
        mock_layer = MagicMock()
        mock_qgs_project = MagicMock()
        mock_qgs_project.mapLayer.return_value = mock_layer

        with patch(_STYLING_CLS, mock_styling_cls), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(snapshot)

        assert "migrate" in call_order, "migrate was never called"
        assert "setStyle" in call_order, "setStyle was never called"
        assert call_order.index("migrate") < call_order.index("setStyle")

    def test_applies_null_style_to_results_with_id(self):
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        mock_styling_cls = MagicMock()
        mock_styling = mock_styling_cls.return_value

        snapshot = self._make_snapshot(results_with_id=["layer_r1", "layer_r2"])
        mock_layer = MagicMock()
        mock_qgs_project = MagicMock()
        mock_qgs_project.mapLayer.return_value = mock_layer

        with patch(_STYLING_CLS, mock_styling_cls), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(snapshot)

        assert mock_styling.applyNullStyle.call_count == 2
        section.removeOldResultLayers.assert_not_called()

    def test_calls_remove_old_result_layers_when_results_no_id(self):
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        snapshot = self._make_snapshot(results_no_id=True)
        mock_qgs_project = MagicMock()

        with patch(_STYLING_CLS), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(snapshot)

        section.removeOldResultLayers.assert_called_once()

    def test_restyles_input_layers_on_version_change(self):
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        mock_styling_cls = MagicMock()
        mock_styling = mock_styling_cls.return_value

        snapshot = self._make_snapshot(inputs_to_restyle=[("lid1", "pipes"), ("lid2", "junctions")])
        mock_layer = MagicMock()
        mock_qgs_project = MagicMock()
        mock_qgs_project.mapLayer.return_value = mock_layer

        with patch(_STYLING_CLS, mock_styling_cls), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(snapshot)

        assert mock_styling.setStyle.call_count == 2
        mock_styling.setStyle.assert_any_call(mock_layer, "pipes")
        mock_styling.setStyle.assert_any_call(mock_layer, "junctions")

    def test_empty_snapshot_runs_without_error(self):
        """An empty snapshot (no version change, no results) should run silently."""
        section = _make_section()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        mock_styling_cls = MagicMock()
        mock_qgs_project = MagicMock()

        with patch(_STYLING_CLS, mock_styling_cls), patch(_QGS_PROJECT) as mock_proj_cls:
            mock_proj_cls.instance.return_value = mock_qgs_project
            section._post_qgz_open(self._make_snapshot())

        section.removeOldResultLayers.assert_not_called()
        mock_styling_cls.return_value.applyNullStyle.assert_not_called()
        mock_styling_cls.return_value.setStyle.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for openProjectProcess (Scenario 2 — "Open Project" button)
# ---------------------------------------------------------------------------

class TestOpenProjectProcessScenario2:
    """When runOpenProject opens a QGZ (loaded_qgis=True), _post_qgz_open
    must be called; when it opens without QGZ it must NOT be called."""

    def _setup_section(self, loaded_qgis_return):
        section = _make_section()
        # Attributes used by runOpenProject
        section.gplFile = "fake.gpl"
        section.opendedLayers = False
        section.especificComplementaryLayers = []
        section.selectedFids = {}
        section.layerOperationInProgress = False

        # Methods called during the flow that we don't want to actually execute
        section.checkDependencies = MagicMock(return_value=True)
        section.defineCurrentProject = MagicMock()
        section.tr = MagicMock(side_effect=lambda s: s)
        section._post_qgz_open = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section._collectOpenSnapshot = MagicMock(return_value=_empty_snapshot())
        section.readOptions = MagicMock()
        section.suggestQgsProjectFilename = MagicMock()

        # Simulate dialog success
        mock_dlg = MagicMock()
        mock_dlg.ProcessDone = True
        mock_dlg.NetworkName = "TestNet"
        mock_dlg.ProjectDirectory = "C:/proj"
        mock_dlg.exec = MagicMock()

        # mock_io is what QGISRedProjectIO(...) returns (all instantiations)
        mock_io = MagicMock()
        mock_io.openProjectInQgis.return_value = loaded_qgis_return

        mock_identifiers = MagicMock()

        return section, mock_dlg, mock_io, mock_identifiers

    def test_post_qgz_open_called_when_qgz_loaded(self):
        """Scenario 2: loaded_qgis=True → _post_qgz_open must be called."""
        section, mock_dlg, mock_io, mock_identifiers = self._setup_section(loaded_qgis_return=True)

        with patch(_SECTION_MOD + ".QGISRedImportProjectDialog", return_value=mock_dlg), \
             patch(_SECTION_MOD + ".QGISRedProjectIO", return_value=mock_io), \
             patch(_SECTION_MOD + ".QGISRedIdentifierUtils", return_value=mock_identifiers), \
             patch(_SECTION_MOD + ".QgsProject"), \
             patch(_SECTION_MOD + ".QIcon"):
            section.runOpenProject()

        section._post_qgz_open.assert_called_once()

    def test_post_qgz_open_not_called_when_no_qgz(self):
        """Scenario 2: loaded_qgis=False → _post_qgz_open must NOT be called."""
        section, mock_dlg, mock_io, mock_identifiers = self._setup_section(loaded_qgis_return=False)

        with patch(_SECTION_MOD + ".QGISRedImportProjectDialog", return_value=mock_dlg), \
             patch(_SECTION_MOD + ".QGISRedProjectIO", return_value=mock_io), \
             patch(_SECTION_MOD + ".QGISRedIdentifierUtils", return_value=mock_identifiers), \
             patch(_SECTION_MOD + ".QgsProject"), \
             patch(_SECTION_MOD + ".QIcon"):
            section.runOpenProject()

        section._post_qgz_open.assert_not_called()

    def test_migrate_called_when_no_qgz(self):
        """Scenario 2: loaded_qgis=False → _migrateLayersToSubfolders must be called."""
        section, mock_dlg, mock_io, mock_identifiers = self._setup_section(loaded_qgis_return=False)

        with patch(_SECTION_MOD + ".QGISRedImportProjectDialog", return_value=mock_dlg), \
             patch(_SECTION_MOD + ".QGISRedProjectIO", return_value=mock_io), \
             patch(_SECTION_MOD + ".QGISRedIdentifierUtils", return_value=mock_identifiers), \
             patch(_SECTION_MOD + ".QgsProject"), \
             patch(_SECTION_MOD + ".QIcon"):
            section.runOpenProject()

        section._migrateLayersToSubfolders.assert_called_once()

    def test_snapshot_collected_before_enforce_all_identifiers(self):
        """The snapshot must be collected BEFORE enforceAllIdentifiers() is called."""
        call_order = []
        section, mock_dlg, mock_io, mock_identifiers = self._setup_section(loaded_qgis_return=True)
        section._collectOpenSnapshot = MagicMock(
            side_effect=lambda: call_order.append("snapshot") or _empty_snapshot()
        )
        mock_identifiers.enforceAllIdentifiers = MagicMock(
            side_effect=lambda: call_order.append("enforceAll")
        )

        with patch(_SECTION_MOD + ".QGISRedImportProjectDialog", return_value=mock_dlg), \
             patch(_SECTION_MOD + ".QGISRedProjectIO", return_value=mock_io), \
             patch(_SECTION_MOD + ".QGISRedIdentifierUtils", return_value=mock_identifiers), \
             patch(_SECTION_MOD + ".QgsProject"), \
             patch(_SECTION_MOD + ".QIcon"):
            section.runOpenProject()

        assert "snapshot" in call_order, "snapshot was never collected"
        assert "enforceAll" in call_order, "enforceAllIdentifiers was never called"
        assert call_order.index("snapshot") < call_order.index("enforceAll")


# ---------------------------------------------------------------------------
# Tests for runOpenedQgisProject (Scenario 3 — direct .qgz open)
# ---------------------------------------------------------------------------

class TestRunOpenedQgisProjectScenario3:
    """Scenario 3: the readProject signal triggers runOpenedQgisProject.
    _post_qgz_open must be scheduled via QTimer.singleShot (not called directly)."""

    def test_qtimer_singleshot_defers_post_qgz_open(self):
        """_post_qgz_open must be scheduled with QTimer.singleShot(0, ...) — not called inline."""
        section = _make_section()
        section.isUnloading = False
        section._loading_project = False  # Flag must be False for scenario 3 to proceed
        section.TemporalFolder = "Temporal Folder"
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "TestNet"
        section.gplFile = "fake.gpl"

        section._post_qgz_open = MagicMock()
        section._collectOpenSnapshot = MagicMock(return_value=_empty_snapshot())
        section.defineCurrentProject = MagicMock()
        section.readOptions = MagicMock()

        mock_identifiers = MagicMock()
        mock_identifiers.enforceGroupIdentifiers = MagicMock()
        mock_identifiers.assignLayerIdentifiers = MagicMock()
        mock_identifiers.getTranslatedNameForIdentifier = MagicMock(return_value=None)

        mock_io_cls = MagicMock()
        mock_io_cls.return_value = MagicMock()

        mock_layer_utils_cls = MagicMock()
        mock_layer_utils_cls.findGroupByIdentifier.return_value = None

        captured_callbacks = []

        def fake_singleshot(delay, cb):
            captured_callbacks.append((delay, cb))

        with patch(_SECTION_MOD + ".QGISRedIdentifierUtils", return_value=mock_identifiers), \
             patch(_SECTION_MOD + ".QGISRedProjectIO", mock_io_cls), \
             patch(_SECTION_MOD + ".QGISRedLayerUtils", mock_layer_utils_cls), \
             patch(_SECTION_MOD + ".QTimer") as mock_timer:
            mock_timer.singleShot.side_effect = fake_singleshot
            section.runOpenedQgisProject()

        # _post_qgz_open must NOT have been called immediately
        section._post_qgz_open.assert_not_called()

        # QTimer.singleShot must have been scheduled with delay=0
        assert any(delay == 0 for delay, _ in captured_callbacks), \
            "Expected QTimer.singleShot(0, ...) to be called"

        # Executing the deferred callback must invoke _post_qgz_open
        for delay, cb in captured_callbacks:
            if delay == 0:
                cb()
                break

        section._post_qgz_open.assert_called_once()

    def test_loading_project_flag_suppresses_handler(self):
        """When _loading_project=True (scenarios 1 & 2 are managing the open),
        runOpenedQgisProject must return immediately without calling anything."""
        section = _make_section()
        section.isUnloading = False
        section._loading_project = True  # Simulates scenario 1 or 2 in progress
        section.defineCurrentProject = MagicMock()
        section.readOptions = MagicMock()
        section._post_qgz_open = MagicMock()

        section.runOpenedQgisProject()

        section.defineCurrentProject.assert_not_called()
        section.readOptions.assert_not_called()
        section._post_qgz_open.assert_not_called()
