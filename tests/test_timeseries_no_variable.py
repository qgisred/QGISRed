# -*- coding: utf-8 -*-
from types import SimpleNamespace


def _section(nodeText, linkText, withResultsDock=True):
    from QGISRed.sections.analysis_section import AnalysisSection

    section = AnalysisSection.__new__(AnalysisSection)
    section.ResultDockwidget = (
        SimpleNamespace(
            lbl_none="None",
            cbNodes=SimpleNamespace(currentText=lambda: nodeText),
            cbLinks=SimpleNamespace(currentText=lambda: linkText),
        )
        if withResultsDock
        else None
    )
    return section


def test_node_click_with_none_selected_has_no_variable():
    assert _section("None", "Flow")._timeSeriesNoVariableSelected("Node")


def test_link_click_follows_the_link_selector():
    section = _section("None", "Flow")
    assert not section._timeSeriesNoVariableSelected("Link")
    assert _section("Pressure", "None")._timeSeriesNoVariableSelected("Link")


def test_without_results_panel_a_variable_is_assumed():
    assert not _section("", "", withResultsDock=False)._timeSeriesNoVariableSelected("Node")
