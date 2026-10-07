# -*- coding: utf-8 -*-
"""Style file name the legend editor saves to / loads from, per layer identifier.

It must match the name the results dock asks setStyle for ("<Node|Link><Variable>"),
and must not depend on the interface language.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog
from QGISRed.ui.analysis.qgisred_results_data import resultStyleName
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(autouse=True)
def noProjectEntry():
    """No results_* entry by default, so tests exercise the fallbacks explicitly."""
    with patch("QGISRed.ui.project.qgisred_legends_dialog.QgsProject") as project:
        project.instance.return_value.readEntry.return_value = ("", False)
        yield project


def _projectOptions(project, flowUnit="LPS", qualityModel="Chemical", chemicalLabel=""):
    """The Analysis Options the style names depend on, as the project stores them."""
    entries = {"project_units": flowUnit, "project_qualitymodel": qualityModel, "project_chemicallabel": chemicalLabel}
    project.instance.return_value.readEntry.side_effect = (
        lambda section, key, default="": (entries[key], True) if key in entries else (default, False))


@pytest.fixture(autouse=True)
def siProjectWithoutChlorine():
    """SI units and an unnamed chemical unless a test says otherwise."""
    with patch("QGISRed.tools.utils.qgisred_project_utils.QgsProject") as project:
        _projectOptions(project)
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
        ("Node", "Pressure", "NodePressureSI"),
        ("Node", "Head", "NodeHead"),
        ("Link", "Status", "LinkStatus"),
        ("Link", "UnitHdLoss", "LinkUnitHdLoss"),
        ("Link", "Flow_Unsig", "LinkFlow"),
        ("Link", "Flow_Sig", "LinkFlow"),
    ])
    def test_builds_the_shipped_qml_names(self, layerType, variable, expected):
        assert resultStyleName(layerType, variable) == expected

    @pytest.mark.parametrize("flowUnit, expected", [("LPS", "SI"), ("CMH", "SI"), ("GPM", "US"), ("CFS", "US")])
    @pytest.mark.parametrize("layerType, variable", [("Node", "Pressure"), ("Link", "Velocity"), ("Link", "HeadLoss")])
    def test_variables_with_unit_dependent_thresholds_carry_the_unit_system(
            self, siProjectWithoutChlorine, flowUnit, expected, layerType, variable):
        _projectOptions(siProjectWithoutChlorine, flowUnit=flowUnit)

        assert resultStyleName(layerType, variable) == layerType + variable + expected

    @pytest.mark.parametrize("qualityModel, chemicalLabel, expected", [
        ("Chemical", "Chlorine", "Chlorine"),
        ("Chemical", "cloro residual", "Chlorine"),
        ("Chemical", "Chlore", "Chlorine"),
        ("Chemical", "CL2", "Chlorine"),
        ("Chemical", "cl", "Chlorine"),
        ("Chemical", "Fluoride", "Chemical"),
        ("Chemical", "", "Chemical"),
        ("Age", "Chlorine", "Age"),
        ("Trace", "", "Trace"),
        ("None", "", "Chemical"),
    ])
    def test_quality_takes_the_style_of_its_kind(self, siProjectWithoutChlorine, qualityModel, chemicalLabel, expected):
        _projectOptions(siProjectWithoutChlorine, qualityModel=qualityModel, chemicalLabel=chemicalLabel)

        assert resultStyleName("Node", "Quality") == "Node" + expected
        assert resultStyleName("Link", "Quality") == "Link" + expected

    def test_tolerates_the_composite_layer_name_the_dock_passes(self):
        assert resultStyleName("Node_Something", "Pressure") == "NodePressureSI"

    @pytest.mark.parametrize("layerType, variable", [("", "Pressure"), ("Node", ""), ("Node", None)])
    def test_returns_empty_without_a_name_to_build(self, layerType, variable):
        assert resultStyleName(layerType, variable) == ""


class TestResultStyleName:
    @pytest.mark.parametrize("identifier, field, expected", [
        ("qgisred_node_pressure", "Pressure", "NodePressureSI"),
        ("qgisred_node_head", "Head", "NodeHead"),
        ("qgisred_node_demand", "Demand", "NodeDemand"),
        ("qgisred_node_quality", "Quality", "NodeChemical"),
        ("qgisred_link_velocity", "Velocity", "LinkVelocitySI"),
        ("qgisred_link_headloss", "HeadLoss", "LinkHeadLossSI"),
        ("qgisred_link_unitheadloss", "UnitHdLoss", "LinkUnitHdLoss"),
        ("qgisred_link_frictionfactor", "FricFactor", "LinkFricFactor"),
        ("qgisred_link_reactionrate", "ReactRate", "LinkReactRate"),
    ])
    def test_matches_the_shipped_qml_names(self, identifier, field, expected):
        assert _dialog(field).getResultStyleName(identifier) == expected

    def test_flow_is_classified_through_an_abs_expression(self, identifier="qgisred_link_flow"):
        assert _dialog('abs("Flow")').getResultStyleName(identifier) == "LinkFlow"
        assert _dialog("abs(Flow)").getResultStyleName(identifier) == "LinkFlow"
        assert _dialog("abs(Flow_Sig)").getResultStyleName(identifier) == "LinkFlow"

    @pytest.mark.parametrize("field", ["Flow_Sig", "Flow_Unsig"])
    def test_signed_flow_variants_share_the_flow_style(self, field):
        assert _dialog(field).getResultStyleName("qgisred_link_flow") == "LinkFlow"

    @pytest.mark.parametrize("field, expected", [
        ("Quality", "LinkChemical"),
        ("FricFactor", "LinkFricFactor"),
        ("ReactRate", "LinkReactRate"),
    ])
    def test_the_column_names_the_style_whatever_the_identifier(self, field, expected):
        # Styles saved by older plugins stamped qgisred_link_quality on FricFactor and ReactRate too.
        assert _dialog(field).getResultStyleName("qgisred_link_quality") == expected

    def test_without_a_column_or_a_project_entry_there_is_no_name(self):
        # Guessing from the identifier is not an option: a layer styled by an older plugin may
        # carry qgisred_link_quality for FricFactor or ReactRate and would pick the wrong file.
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


class TestStyleNameForIdentifier:
    """The editor must ask for the same file setStyle would load.

    setStyle is called with the identifier minus its "qgisred_" prefix and strips
    underscores before the lookup, so deriving it the same way here is what makes a saved
    style findable again.
    """

    # Every family whose style comes from a file, with the shipped default it must reach.
    STYLED_IDENTIFIERS = [
        ("qgisred_pipes", "Pipes.qml.bak"),
        ("qgisred_junctions", "Junctions.qml.bak"),
        ("qgisred_tanks", "Tanks.qml.bak"),
        ("qgisred_reservoirs", "Reservoirs.qml.bak"),
        ("qgisred_valves", "Valves.qml.bak"),
        ("qgisred_pumps", "Pumps.qml.bak"),
        ("qgisred_sources", "Sources.qml.bak"),
        ("qgisred_meters", "Meters.qml.bak"),
        # These two were saved as MultipleDemands.qml and ServiceConnection.qml (singular).
        ("qgisred_demands", "Demands.qml.bak"),
        ("qgisred_serviceconnections", "ServiceConnections.qml.bak"),
        ("qgisred_isolationvalves", "IsolationValves.qml.bak"),
        # And this whole family was saved with short names full of underscores.
        ("qgisred_hydraulicsectors_links", "HydraulicSectorsLinks.qml.bak"),
        ("qgisred_hydraulicsectors_nodes", "HydraulicSectorsNodes.qml.bak"),
        ("qgisred_hydraulicsectors_isolateddemands", "HydraulicSectorsIsolatedDemands.qml.bak"),
        ("qgisred_isolatedsegments_links", "IsolatedSegmentsLinks.qml.bak"),
        ("qgisred_isolatedsegments_nodes", "IsolatedSegmentsNodes.qml.bak"),
        ("qgisred_isolatedsegments_isolateddemands", "IsolatedSegmentsIsolatedDemands.qml.bak"),
        ("qgisred_tree_links", "TreeLinks.qml.bak"),
        ("qgisred_tree_nodes", "TreeNodes.qml.bak"),
        ("qgisred_connectivity_links", "ConnectLinks.qml.bak"),
        # The Demand Builder themes: one shipped style per type, shared by every theme of it.
        ("qgisred_demandbuilder_consumptionpoints", "DemandBuilderConsumptionPoints.qml.bak"),
        ("qgisred_demandbuilder_demandlinks", "DemandBuilderDemandLinks.qml.bak"),
        ("qgisred_demandbuilder_sectors", "DemandBuilderSectors.qml.bak"),
    ]

    @pytest.mark.parametrize("identifier, defaultFile", STYLED_IDENTIFIERS)
    def test_resolves_to_the_shipped_default(self, identifier, defaultFile):
        name = _dialog().getElementNameForIdentifier(identifier)
        defaults = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")

        found = QGISRedStylingUtils.findStyleFile(defaults, [name + ".qml.bak"])

        assert found is not None, f"{identifier} → {name}.qml has no default style to match"
        assert os.path.basename(found) == defaultFile

    def test_thematic_maps_are_left_to_their_own_scheme(self):
        # Their styles are named pipe_material.qml and resolved by the thematic maps
        # dialog, which records the file it used in the styleURI custom property.
        assert _dialog().getStyleNameForIdentifier("qgisred_query_pipes_material") is None

    def test_classifiable_thematic_maps_map_to_their_theme_qml(self):
        assert _dialog().getStyleNameForIdentifier("qgisred_query_pipes_installyear") == "PipeInstallationYears"
        assert _dialog().getStyleNameForIdentifier("qgisred_query_pipes_age") == "PipeAges"

    def test_a_layer_outside_the_plugin_has_no_derived_name(self):
        assert _dialog().getStyleNameForIdentifier("something_else") is None
        assert _dialog().getStyleNameForIdentifier("") is None


class TestStyleBasename:
    def _dialog(self, identifier, styleURI):
        dialog = _dialog(None)
        properties = {"qgisred_identifier": identifier, "styleURI": styleURI}
        dialog.currentLayer.customProperty.side_effect = lambda key, *a: properties.get(key)
        return dialog

    def test_thematic_maps_take_the_file_recorded_in_style_uri(self):
        dialog = self._dialog("qgisred_query_pipes_material", "/styles/pipe_material.qml.bak")
        assert dialog.getStyleBasename("Mapa temático") == "pipe_material"

    def test_other_layers_ignore_a_stale_style_uri(self):
        # A styleURI copied along with an old QML sent Service Connections after demand.qml
        dialog = self._dialog("qgisred_serviceconnections", "/styles/demand.qml")
        assert dialog.getStyleBasename("serviceconnections") == "serviceconnections"


class TestProjectStyleFilename:
    def _dialog(self, identifier, source):
        dialog = _dialog(None)
        dialog.networkName = "Net"
        properties = {"qgisred_identifier": identifier}
        dialog.currentLayer.customProperty.side_effect = lambda key, *a: properties.get(key)
        dialog.currentLayer.source.return_value = source
        return dialog

    def test_a_tree_layer_carries_its_tree_name(self):
        dialog = self._dialog("qgisred_tree_links", "C:/proj/Queries/Trees/Net_J5_Union_Links.shp")
        assert dialog.getProjectStyleFilename("treelinks") == "Net_treelinks_J5_Union.qml"

    def test_two_trees_get_two_files(self):
        first = self._dialog("qgisred_tree_nodes", "C:/proj/Queries/Trees/Net_J5_Union_Nodes.shp")
        second = self._dialog("qgisred_tree_nodes", "C:/proj/Queries/Trees/Net_T12_Nodes.shp|layername=x")
        assert first.getProjectStyleFilename("treenodes") == "Net_treenodes_J5_Union.qml"
        assert second.getProjectStyleFilename("treenodes") == "Net_treenodes_T12.qml"

    def test_other_layers_keep_the_plain_name(self):
        dialog = self._dialog("qgisred_pipes", "C:/proj/Net_Pipes.shp")
        assert dialog.getProjectStyleFilename("pipes") == "Net_pipes.qml"

    def test_a_demand_builder_theme_carries_its_theme_name(self):
        dialog = self._dialog("qgisred_demandbuilder_consumptionpoints",
                              "C:/proj/Auxiliary Layers/DemandBuilder/Net_DemandBuilder_Consumptions_Padron.shp")
        assert dialog.getProjectStyleFilename("demandbuilderconsumptionpoints") == \
            "Net_demandbuilderconsumptionpoints_Padron.qml"

    def test_an_unnamed_theme_keeps_the_plain_name(self):
        dialog = self._dialog("qgisred_demandbuilder_sectors",
                              "C:/proj/Auxiliary Layers/DemandBuilder/Net_DemandBuilder_Sectors.shp")
        assert dialog.getProjectStyleFilename("demandbuildersectors") == "Net_demandbuildersectors.qml"

    def test_two_themes_of_one_type_get_two_files(self):
        folder = "C:/proj/Auxiliary Layers/DemandBuilder/"
        first = self._dialog("qgisred_demandbuilder_sectors", folder + "Net_DemandBuilder_Sectors_Barrios.shp")
        second = self._dialog(
            "qgisred_demandbuilder_sectors", folder + "Net_DemandBuilder_Sectors_Centro.shp|layername=x")
        assert first.getProjectStyleFilename("demandbuildersectors") == "Net_demandbuildersectors_Barrios.qml"
        assert second.getProjectStyleFilename("demandbuildersectors") == "Net_demandbuildersectors_Centro.qml"


class TestElementNameForIdentifier:
    def test_result_layer_ignores_the_translated_layer_name(self):
        dialog = _dialog("Pressure", layerName="Nudo Presión")

        assert dialog.getElementNameForIdentifier("qgisred_node_pressure") == "NodePressureSI"

    def test_input_layer_ignores_the_translated_layer_name_too(self):
        # It used to come from identifierToElementName, which gave names setStyle never
        # asks for ("Multiple Demands" against Demands.qml).
        dialog = _dialog(None, layerName="Tuberías")

        assert dialog.getElementNameForIdentifier("qgisred_pipes") == "pipes"

    def test_thematic_map_still_falls_back_to_its_name(self):
        # And getStyleBasename then overrides it with the file the thematic maps dialog
        # recorded in styleURI, which is the only place that scheme is known.
        dialog = _dialog(None, layerName="Mapa temático")

        assert dialog.getElementNameForIdentifier("qgisred_query_something") == "Mapa temático"
