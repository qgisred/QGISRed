# -*- coding: utf-8 -*-
import os

from .test_timeseries_values_table_formatting import _patch_qt_for_import


def _dock(results_dock):
    _patch_qt_for_import()
    from QGISRed.ui.analysis.qgisred_timeseries_dock import QGISRedTimeSeriesDock

    d = QGISRedTimeSeriesDock.__new__(QGISRedTimeSeriesDock)
    d._resultsDock = results_dock
    return d


def test_exports_start_in_the_project_folder(tmp_path):
    results_dock = type("R", (), {"ProjectDirectory": str(tmp_path)})()
    assert _dock(results_dock)._exportStartDirectory() == str(tmp_path)


def test_exports_start_in_home_without_a_results_panel():
    assert _dock(None)._exportStartDirectory() == os.path.expanduser("~")


def test_exports_start_in_home_when_the_project_folder_is_gone(tmp_path):
    results_dock = type("R", (), {"ProjectDirectory": str(tmp_path / "missing")})()
    assert _dock(results_dock)._exportStartDirectory() == os.path.expanduser("~")
