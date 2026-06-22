# -*- coding: utf-8 -*-
from QGISRed.ui.analysis.qgisred_results_evolution import _ResultsEvolutionMixin


class _FakeCheckBox:
    def __init__(self, checked=False):
        self._checked = checked

    def isChecked(self):
        return self._checked

    def setChecked(self, value):
        self._checked = bool(value)

    def blockSignals(self, value):
        return None


class _FakeHost:
    def __init__(self):
        self.visible = None

    def setVisible(self, value):
        self.visible = bool(value)


class _FakeSignal:
    def __init__(self):
        self.count = 0

    def emit(self, *args):
        self.count += 1


class _EvoHarness(_ResultsEvolutionMixin):
    def __init__(self, node_evo=False, link_evo=False, node_dist=False, link_dist=False):
        self.cbNodeEvolution = _FakeCheckBox(node_evo)
        self.cbLinkEvolution = _FakeCheckBox(link_evo)
        self.cbNodeDistribution = _FakeCheckBox(node_dist)
        self.cbLinkDistribution = _FakeCheckBox(link_dist)
        self.evolutionChartContainer = _FakeHost()
        self.nodeEvolutionChartHost = _FakeHost()
        self.linkEvolutionChartHost = _FakeHost()
        self._evolution_popout = None
        self.evolutionPickCancelled = _FakeSignal()
        self.dist_sync_calls = 0

    def _syncDistributionPanelVisibility(self):
        self.dist_sync_calls += 1


class TestActiveEvolutionLayerType:
    def test_node(self):
        assert _EvoHarness(node_evo=True)._activeEvolutionLayerType() == "Node"

    def test_link(self):
        assert _EvoHarness(link_evo=True)._activeEvolutionLayerType() == "Link"

    def test_none(self):
        assert _EvoHarness()._activeEvolutionLayerType() is None


class TestExclusiveRadioBehavior:
    def test_activating_node_evolution_unchecks_the_other_three(self):
        harness = _EvoHarness(link_dist=True, node_dist=True, link_evo=True)
        harness._activateExclusiveResultsChart("NodeEvo")
        assert harness.cbLinkDistribution.isChecked() is False
        assert harness.cbNodeDistribution.isChecked() is False
        assert harness.cbLinkEvolution.isChecked() is False

    def test_activating_evolution_does_not_emit_cancel(self):
        harness = _EvoHarness(node_evo=True)
        harness._activateExclusiveResultsChart("LinkEvo")
        assert harness.evolutionPickCancelled.count == 0

    def test_activating_histogram_cancels_active_evolution(self):
        harness = _EvoHarness(node_evo=True)
        harness._activateExclusiveResultsChart("NodeDist")
        assert harness.cbNodeEvolution.isChecked() is False
        assert harness.evolutionPickCancelled.count == 1

    def test_activating_histogram_without_active_evolution_does_not_cancel(self):
        harness = _EvoHarness(link_dist=True)
        harness._activateExclusiveResultsChart("NodeDist")
        assert harness.evolutionPickCancelled.count == 0


class TestEvolutionPanelVisibility:
    def test_node_active_shows_container_and_node_host(self):
        harness = _EvoHarness(node_evo=True)
        harness._syncEvolutionPanelVisibility()
        assert harness.evolutionChartContainer.visible is True
        assert harness.nodeEvolutionChartHost.visible is True
        assert harness.linkEvolutionChartHost.visible is False

    def test_no_active_hides_container(self):
        harness = _EvoHarness()
        harness._syncEvolutionPanelVisibility()
        assert harness.evolutionChartContainer.visible is False


class TestEvolutionWidgetImportable:
    def test_construct_simplified_widget(self):
        from QGISRed.ui.analysis.results_evolution_widget import ResultsEvolutionPlotWidget

        widget = ResultsEvolutionPlotWidget()
        assert widget._simplified_cursor_only is True
        assert widget._legendGroups() == []
