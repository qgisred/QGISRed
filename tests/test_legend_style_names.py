# -*- coding: utf-8 -*-
"""Style file name the legend editor saves to / loads from, per layer identifier.

It must match the name the results dock asks setStyle for ("<Node|Link><Variable>"),
and must not depend on the interface language.
"""
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.ui.analysis.qgisred_results_data import resultStyleName


@pytest.fixture(autouse=True)
def noProjectEntry():
    """No results_* entry by default, so tests exercise the fallbacks explicitly."""
    with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsProject") as project:
        project.instance.return_value.readEntry.return_value = ("", False)
        yield project


def _dialog(fieldName=None, layerName="Node Pressure"):
    """Bare dialog: these helpers only read currentFieldName / currentLayer."""
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentFieldName = fieldName
    dialog.currentLayer = MagicMock()
    dialog.currentLayer.name.return_value = layerName
    dialog.utils = None
    return dialog


class TestSharedStyleNameHelper:
    """resultStyleName is the single source of truth for dock, metadata reader and editor."""

    @pytest.mark.parametrize("layerType, variable, expected", [
        ("Node", "Pressure", "NodePressure"),
        ("Link", "Status", "LinkStatus"),
        ("Link", "UnitHdLoss", "LinkUnitHdLoss"),
        ("Link", "Flow_Unsig", "LinkFlow"),
        ("Link", "Flow_Sig", "LinkFlow"),
    ])
    def test_builds_the_shipped_qml_names(self, layerType, variable, expected):
        assert resultStyleName(layerType, variable) == expected

    def test_tolerates_the_composite_layer_name_the_dock_passes(self):
        assert resultStyleName("Node_Something", "Pressure") == "NodePressure"

    @pytest.mark.parametrize("layerType, variable", [("", "Pressure"), ("Node", ""), ("Node", None)])
    def test_returns_empty_without_a_name_to_build(self, layerType, variable):
        assert resultStyleName(layerType, variable) == ""


class TestResultStyleName:
    @pytest.mark.parametrize("identifier, field, expected", [
        ("qgisred_node_pressure", "Pressure", "NodePressure"),
        ("qgisred_node_head", "Head", "NodeHead"),
        ("qgisred_node_demand", "Demand", "NodeDemand"),
        ("qgisred_node_quality", "Quality", "NodeQuality"),
        ("qgisred_link_velocity", "Velocity", "LinkVelocity"),
        ("qgisred_link_headloss", "HeadLoss", "LinkHeadLoss"),
        ("qgisred_link_unitheadloss", "UnitHdLoss", "LinkUnitHdLoss"),
    ])
    def test_matches_the_shipped_qml_names(self, identifier, field, expected):
        assert _dialog(field).getResultStyleName(identifier) == expected

    def test_flow_is_classified_through_an_abs_expression(self, identifier="qgisred_link_flow"):
        assert _dialog('abs("Flow")').getResultStyleName(identifier) == "LinkFlow"
        assert _dialog("abs(Flow)").getResultStyleName(identifier) == "LinkFlow"

    @pytest.mark.parametrize("field", ["Flow_Sig", "Flow_Unsig"])
    def test_signed_flow_variants_share_the_flow_style(self, field):
        assert _dialog(field).getResultStyleName("qgisred_link_flow") == "LinkFlow"

    @pytest.mark.parametrize("field, expected", [
        ("Quality", "LinkQuality"),
        ("FricFactor", "LinkFricFactor"),
        ("ReactRate", "LinkReactRate"),
    ])
    def test_column_disambiguates_the_shared_quality_identifier(self, field, expected):
        # LinkQuality, LinkFricFactor and LinkReactRate all ship with the same identifier.
        assert _dialog(field).getResultStyleName("qgisred_link_quality") == expected

    def test_without_a_column_or_a_project_entry_there_is_no_name(self):
        # Guessing from the identifier is not an option: Quality, FricFactor and
        # ReactRate share qgisred_link_quality and it would pick the wrong style file.
        assert _dialog(None).getResultStyleName("qgisred_link_quality") is None
        assert _dialog(None).getResultStyleName("qgisred_node_pressure") is None

    def test_non_result_layer_returns_none(self):
        assert _dialog("Diameter").getResultStyleName("qgisred_pipes") is None
        assert _dialog("Diameter").getResultStyleName("") is None


class TestProjectEntryCoversStatus:
    """Status classifies through rule filters, so the layer exposes no class attribute.

    The dock records the displayed variable in the project on every restyle, which is
    what answers for it.
    """

    def test_status_comes_from_the_project_entry(self, noProjectEntry):
        noProjectEntry.instance.return_value.readEntry.return_value = ("Status", True)

        assert _dialog(None).getResultStyleName("qgisred_link_status") == "LinkStatus"

    def test_entry_is_read_for_the_matching_element(self, noProjectEntry):
        _dialog(None).getResultStyleName("qgisred_node_pressure")

        noProjectEntry.instance.return_value.readEntry.assert_called_with("QGISRed", "results_Base_Node")

    def test_signed_flow_from_the_entry_uses_the_flow_style(self, noProjectEntry):
        noProjectEntry.instance.return_value.readEntry.return_value = ("Flow_Unsig", True)

        assert _dialog(None).getResultStyleName("qgisred_link_flow") == "LinkFlow"

    def test_the_layer_column_is_preferred_over_the_entry(self, noProjectEntry):
        # The column is read from the layer being edited, so it cannot go stale.
        noProjectEntry.instance.return_value.readEntry.return_value = ("Quality", True)

        assert _dialog("FricFactor").getResultStyleName("qgisred_link_quality") == "LinkFricFactor"


class TestElementNameForIdentifier:
    def test_result_layer_ignores_the_translated_layer_name(self):
        dialog = _dialog("Pressure", layerName="Nudo Presión")

        assert dialog.getElementNameForIdentifier("qgisred_node_pressure") == "NodePressure"

    def test_input_layer_keeps_using_the_identifier_map(self):
        dialog = _dialog(None, layerName="Tuberías")
        dialog.utils = MagicMock()
        dialog.utils.identifierToElementName = {"qgisred_pipes": "Pipes"}
        dialog.utils.identifierToLegendName = {}

        assert dialog.getElementNameForIdentifier("qgisred_pipes") == "Pipes"

    def test_unmapped_layer_still_falls_back_to_its_name(self):
        dialog = _dialog(None, layerName="Mapa temático")
        dialog.utils = MagicMock()
        dialog.utils.identifierToElementName = {}
        dialog.utils.identifierToLegendName = {}

        assert dialog.getElementNameForIdentifier("qgisred_query_something") == "Mapa temático"
