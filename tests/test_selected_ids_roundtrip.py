"""Capturing and restoring the map selection across a DLL run.

The selection is remembered by the layers' stable ID field, never by feature ids:
reloadData() drops a layer's selection outright, so the fids captured before a reload
are unusable. `selectedIds` is the only state holding it — a second dictionary in
parallel is what used to go stale.
"""
import os

import pytest

from QGISRed.sections.utils_section import UtilsSection


class FakeFeature:
    def __init__(self, fid, elementId, idField="PipeID"):
        self._fid = fid
        self._values = {idField: elementId}

    def id(self):
        return self._fid

    def __getitem__(self, field):
        return self._values[field]


class FakeLayer:
    def __init__(self, features, selected=(), layerName="Pipes"):
        self._features = features
        self.layerName = layerName
        self._selected = list(selected)
        self.geometryTypeValue = 1

    def getFeatures(self):
        return list(self._features)

    def getSelectedFeatures(self):
        return [f for f in self._features if f.id() in self._selected]

    def selectByIds(self, fids):
        self._selected = list(fids)

    def geometryType(self):
        return self.geometryTypeValue


class Section(UtilsSection):
    """UtilsSection with its layer lookup stubbed: only the selection logic is under test."""

    def __init__(self, *layers):
        self.layers = list(layers)
        self.ProjectDirectory = os.path.join("C", "net")
        self.NetworkName = "Net"
        self.ownMainLayers = [layer.layerName for layer in self.layers]
        self.complementaryLayers = []
        self.selectedIds = {}
        self.linkIds = ""
        self.nodeIds = ""

    @property
    def layer(self):
        return self.layers[0]

    @layer.setter
    def layer(self, value):
        self.layers = [value]

    def getLayers(self):
        return self.layers

    def getLayerPath(self, layer):
        return os.path.join(self.ProjectDirectory, "Net_" + layer.layerName + ".shp")

    def generatePath(self, folder, fileName):
        return os.path.join(folder, fileName)

    def _getIdFieldName(self, layerName, layer):
        return layerName[:-1] + "ID"


@pytest.fixture
def features():
    return [FakeFeature(1, "P-1"), FakeFeature(2, "P-2"), FakeFeature(3, "P-3")]


class TestCapture:
    def test_it_remembers_the_element_ids_of_the_selection(self, features):
        section = Section(FakeLayer(features, selected=[1, 3]))

        assert section.getSelectedFeaturesIds() is not False
        assert section.selectedIds == {"Pipes": ["P-1", "P-3"]}

    def test_an_element_without_id_aborts_and_leaves_nothing_behind(self, features):
        # The abort has to drop what the layers already collected: a half-filled
        # dictionary would be restored on the next reload as if nothing had failed
        valves = [FakeFeature(1, "NULL", idField="ValveID")]
        section = Section(FakeLayer(features, selected=[1, 3]),
                          FakeLayer(valves, selected=[1], layerName="Valves"))

        assert section.getSelectedFeaturesIds() is False
        assert section.selectedIds == {}


class TestRestore:
    def test_it_reselects_by_element_id_after_the_fids_changed(self, features):
        section = Section(FakeLayer(features, selected=[1, 3]))
        section.getSelectedFeaturesIds()
        # The reload renumbers the features and drops the selection
        reloaded = FakeLayer([FakeFeature(10, "P-1"), FakeFeature(11, "P-2"), FakeFeature(12, "P-3")])
        section.layer = reloaded

        section.setSelectedFeaturesById()

        assert reloaded._selected == [10, 12]

    def test_elements_that_no_longer_exist_are_skipped(self, features):
        # What a Remove Elements run leaves behind: the survivors keep their selection
        section = Section(FakeLayer(features, selected=[1, 2, 3]))
        section.getSelectedFeaturesIds()
        section.layer = FakeLayer([FakeFeature(10, "P-2")])

        section.setSelectedFeaturesById()

        assert section.layer._selected == [10]

    def test_restoring_clears_what_it_restored(self, features):
        section = Section(FakeLayer(features, selected=[1]))
        section.getSelectedFeaturesIds()

        section.setSelectedFeaturesById()

        assert section.selectedIds == {}

    def test_nothing_captured_restores_nothing(self, features):
        layer = FakeLayer(features)
        section = Section(layer)

        section.setSelectedFeaturesById()

        assert layer._selected == []
