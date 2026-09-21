# -*- coding: utf-8 -*-
"""Re-running Isolated Segments from the legend's stale-layer warning, without asking the
user to click a point on the map again.

Unlike Tree, IsolatedSegments was never behind a WPF dialog on the C# side -- the "dialog"
is QGISRedSelectPointTool, entirely on the Python side, and the DLL export always just took
an "x:y" string. WriteIsolatedNodes stamps that exact point back onto its own Nodes
shapefile as a NodeType == "INCIDENCE" feature, already in the project's own CRS, so a
rerun only has to read it -- no DLL changes, no transformPoint.
"""
import os
from unittest.mock import MagicMock, patch

import pytest

_QGSVECTORLAYER = "QGISRed.sections.tools_section.QgsVectorLayer"
_GISRED = "QGISRed.sections.tools_section.GISRed"
_QAPPLICATION = "QGISRed.sections.tools_section.QApplication"


class FakePoint:
    def __init__(self, x, y):
        self._x = x
        self._y = y

    def x(self):
        return self._x

    def y(self):
        return self._y


class FakeGeometry:
    def __init__(self, x, y):
        self._point = FakePoint(x, y)

    def asPoint(self):
        return self._point


class FakeFeature:
    def __init__(self, nodeType, x=0.0, y=0.0):
        self._nodeType = nodeType
        self._geometry = FakeGeometry(x, y)

    def __getitem__(self, name):
        if name == "NodeType":
            return self._nodeType
        raise KeyError(name)

    def geometry(self):
        return self._geometry


class FakeFields:
    def __init__(self, names):
        self._names = set(names)

    def indexFromName(self, name):
        return 0 if name in self._names else -1


class FakeNodesLayer:
    def __init__(self, features, fieldNames=("Id", "NodeType", "Status"), valid=True):
        self._features = features
        self._fields = FakeFields(fieldNames)
        self._valid = valid

    def isValid(self):
        return self._valid

    def fields(self):
        return self._fields

    def getFeatures(self):
        return list(self._features)


@pytest.fixture
def section(tmp_path):
    # Imported here, not at module level -- see test_auto_tree_info.py's section fixture
    # for why: importing sections.tools_section at collection time corrupts
    # QGISRedSelectPointTool for every test file collected afterwards.
    from QGISRed.sections.tools_section import ToolsSection

    class Section(ToolsSection):
        def __init__(self, projectDirectory, networkName):
            self.ProjectDirectory = projectDirectory
            self.NetworkName = networkName
            self.tempFolder = "/temp"
            self.gisredDll = None
            self.checkDependencies = lambda: True
            self.defineCurrentProject = lambda: None
            self.isValidProject = lambda: True
            self.isLayerOnEdition = lambda: False
            self.runIsolatedSegments = MagicMock()
            self._handleIsolatedSegmentsResult = MagicMock()

    return Section(str(tmp_path), "Net")


def _nodesPath(section):
    return os.path.join(section.ProjectDirectory, "Queries", "IsolatedSegments", "Net_IsolatedSegments_Nodes.shp")


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").close()


class TestReadIncidencePoint:

    def test_reads_the_incidence_feature(self, section):
        _touch(_nodesPath(section))
        other = FakeFeature("PIPE", 1.0, 2.0)
        incidence = FakeFeature("INCIDENCE", 100.5, -25.25)

        with patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([other, incidence])):
            assert section._readIncidencePoint() == "100.5:-25.25"

    def test_a_missing_nodes_shapefile_yields_nothing(self, section):
        # Never computed yet, or the folder was cleaned up by hand.
        assert section._readIncidencePoint() is None

    def test_an_invalid_layer_yields_nothing(self, section):
        _touch(_nodesPath(section))
        with patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([], valid=False)):
            assert section._readIncidencePoint() is None

    def test_a_layer_missing_the_nodetype_field_yields_nothing(self, section):
        # A file written before this column existed, hypothetically -- same defensive
        # posture as AutoTree's missing-CostFn case.
        _touch(_nodesPath(section))
        layer = FakeNodesLayer([FakeFeature("INCIDENCE")], fieldNames=("Id", "Status"))
        with patch(_QGSVECTORLAYER, return_value=layer):
            assert section._readIncidencePoint() is None

    def test_no_incidence_feature_yields_nothing(self, section):
        _touch(_nodesPath(section))
        other = FakeFeature("PIPE", 1.0, 2.0)
        with patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([other])):
            assert section._readIncidencePoint() is None


class TestRunAutoIsolatedSegments:
    """The public entry point the stale warning calls: read the point off the tool's own
    Nodes shapefile, or fall back to the interactive click when there isn't one."""

    def test_missing_info_falls_back_to_the_interactive_tool(self, section):
        with patch(_GISRED) as gisRed:
            section.runAutoIsolatedSegments()

        section.runIsolatedSegments.assert_called_once_with(False)
        gisRed.IsolatedSegments.assert_not_called()
        section._handleIsolatedSegmentsResult.assert_not_called()

    def test_available_info_calls_the_dll_and_hands_off_the_result(self, section):
        _touch(_nodesPath(section))
        incidence = FakeFeature("INCIDENCE", 100.5, -25.25)

        with patch(_QGSVECTORLAYER, return_value=FakeNodesLayer([incidence])), \
                patch(_GISRED) as gisRed, patch(_QAPPLICATION):
            gisRed.CreateInstance.return_value = "dll-instance"
            gisRed.IsolatedSegments.return_value = "shps"
            section.runAutoIsolatedSegments()

        gisRed.IsolatedSegments.assert_called_once_with(
            "dll-instance", section.ProjectDirectory, section.NetworkName,
            section.tempFolder, "100.5:-25.25",
        )
        section.runIsolatedSegments.assert_not_called()
        section._handleIsolatedSegmentsResult.assert_called_once_with("shps", "pointIsolatedSegment")
