# -*- coding: utf-8 -*-
import pytest

from QGISRed.ui.analysis.qgisred_results_hyd import (
    getHyd_Metadata,
    getHyd_TimeLabels,
    getHyd_TimeNodesProperties,
    getHyd_TimeLinksProperties,
)
from .helpers.epanet_hyd_builder import build_epanet_hyd
from .helpers.epanet_out_builder import simple_network_out


@pytest.fixture
def simple_network_hyd(tmp_path, simple_network_out):
    """Hydraulic file with 2 instants matching simple_network_out topology (3 nodes, 2 links)."""
    hyd_path = tmp_path / "test_network.hyd"
    records = [
        {
            "time_s": 0,
            "step_s": 3600,
            "demands": [-10.0, 5.0, 5.0],
            "heads": [100.0, 80.0, 60.0],
            "flows": [10.0, 5.0],
            "statuses": [3.0, 3.0],
            "settings": [0.0, 0.0],
        },
        {
            "time_s": 3600,
            "step_s": 3600,
            "demands": [-12.0, 6.0, 6.0],
            "heads": [100.0, 75.0, 55.0],
            "flows": [12.0, 6.0],
            "statuses": [3.0, 3.0],
            "settings": [0.0, 0.0],
        },
    ]
    hyd_path.write_bytes(build_epanet_hyd(3, 2, records, duration=3600, n_tanks=1))
    return str(hyd_path), simple_network_out


class TestGetHydMetadata:
    def test_reads_times(self, simple_network_hyd):
        hyd_path, _ = simple_network_hyd
        meta = getHyd_Metadata(hyd_path)
        assert meta is not None
        assert meta["num_records"] == 2
        assert meta["times"] == [0, 3600]

    def test_missing_file(self, tmp_path):
        assert getHyd_Metadata(str(tmp_path / "missing.hyd")) is None


class TestGetHydTimeLabels:
    def test_labels(self, simple_network_hyd):
        hyd_path, _ = simple_network_hyd
        labels = getHyd_TimeLabels(hyd_path)
        assert labels == "0:00:00;1:00:00"


class TestGetHydTimeProperties:
    def test_nodes_at_t0(self, simple_network_hyd):
        hyd_path, out_path = simple_network_hyd
        results = getHyd_TimeNodesProperties(hyd_path, 0, out_path)
        assert results["J1"]["Demand"] == 5.0
        assert results["J1"]["Head"] == 80.0

    def test_nodes_at_t3600(self, simple_network_hyd):
        hyd_path, out_path = simple_network_hyd
        results = getHyd_TimeNodesProperties(hyd_path, 3600, out_path)
        assert results["J1"]["Demand"] == 6.0

    def test_links_flow(self, simple_network_hyd):
        hyd_path, out_path = simple_network_hyd
        results = getHyd_TimeLinksProperties(hyd_path, 0, out_path)
        assert results["P1"]["Flow"] == 10.0
        assert results["P1"]["Status"] == "Open"
