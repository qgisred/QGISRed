# -*- coding: utf-8 -*-
"""Click routing of the four node editing tools (split/join, T, crossing, merge)."""
import sys
from unittest.mock import MagicMock

import pytest

from .conftest import _qt_stub

for _name in ("QgsMapTool", "QgsMapToolEmitPoint", "QgsMapToolIdentify",
              "QgsMapToolIdentifyFeature", "QgsMapToolPan", "QgsRubberBand", "QgsVertexMarker"):
    setattr(sys.modules['qgis.gui'], _name, _qt_stub(_name))

from QGISRed.sections.network_editing_section import NetworkEditingSection  # noqa: E402


class _Section(NetworkEditingSection):
    pass


@pytest.fixture
def section():
    s = _Section()
    s.iface = MagicMock()
    s.myMapTools = {}
    s.pushMessage = MagicMock()
    s.tr = lambda text: text
    s.runSplitJoinPipe = MagicMock(return_value=True)
    s.runCrossing = MagicMock(return_value=True)
    s.runMergeSplitPoints = MagicMock(return_value=True)
    s.runCreateRemoveTconnections = MagicMock(return_value=True)
    return s


def _onJunction(section, present):
    section.junctionAt = MagicMock(return_value=present)


POINT = MagicMock()


class TestJunctionAt:
    def _layer(self, identifier, features):
        layer = MagicMock()
        layer.customProperty.return_value = identifier
        layer.getFeatures.return_value = features
        return layer

    def _section(self, layers):
        s = _Section()
        s.iface = MagicMock()
        s.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel.return_value = 0.1
        s.getLayers = MagicMock(return_value=layers)
        return s

    def test_trueWhenJunctionLayerHasAFeatureThere(self):
        s = self._section([self._layer("qgisred_junctions", [MagicMock()])])
        assert s.junctionAt(MagicMock(**{"x.return_value": 1.0, "y.return_value": 2.0})) is True

    def test_falseWhenJunctionLayerIsEmptyThere(self):
        s = self._section([self._layer("qgisred_junctions", [])])
        assert s.junctionAt(MagicMock(**{"x.return_value": 1.0, "y.return_value": 2.0})) is False

    def test_otherLayersAreIgnored(self):
        s = self._section([self._layer("qgisred_pipes", [MagicMock()]),
                           self._layer("qgisred_tanks", [MagicMock()])])
        assert s.junctionAt(MagicMock(**{"x.return_value": 1.0, "y.return_value": 2.0})) is False


class TestSplitJoinPipes:
    def test_leftClickSplitsWhereThereIsNoJunction(self, section):
        _onJunction(section, False)
        assert section.runSplitPipe(POINT) is True
        section.runSplitJoinPipe.assert_called_once_with(POINT)
        section.pushMessage.assert_not_called()

    def test_leftClickDoesNothingOnAJunction(self, section):
        _onJunction(section, True)
        assert section.runSplitPipe(POINT) is False
        section.runSplitJoinPipe.assert_not_called()
        section.pushMessage.assert_called_once()

    def test_undoJoinsOnAJunction(self, section):
        _onJunction(section, True)
        assert section.runJoinPipes(POINT) is True
        section.runSplitJoinPipe.assert_called_once_with(POINT)

    def test_undoDoesNothingWithoutAJunction(self, section):
        _onJunction(section, False)
        assert section.runJoinPipes(POINT) is False
        section.runSplitJoinPipe.assert_not_called()
        section.pushMessage.assert_called_once()

    def test_rightClickOnEmptySpaceLeavesTheTool(self, section):
        tool = MagicMock()
        section.myMapTools["pointSplit"] = tool
        assert section.runJoinPipesFromContext(None) is False
        section.iface.mapCanvas().unsetMapTool.assert_called_once_with(tool)


class TestCrossings:
    def test_leftClickCreatesWhereThereIsNoJunction(self, section):
        _onJunction(section, False)
        assert section.runCreateRemoveCrossings(POINT) is True
        section.runCrossing.assert_called_once_with(POINT)

    def test_leftClickDoesNothingOnAJunction(self, section):
        _onJunction(section, True)
        assert section.runCreateRemoveCrossings(POINT) is False
        section.runCrossing.assert_not_called()
        section.pushMessage.assert_called_once()

    def test_undoRemovesOnAJunction(self, section):
        _onJunction(section, True)
        assert section.runRemoveCrossing(POINT) is True
        section.runCrossing.assert_called_once_with(POINT)

    def test_undoDoesNothingWithoutAJunction(self, section):
        _onJunction(section, False)
        assert section.runRemoveCrossing(POINT) is False
        section.runCrossing.assert_not_called()
        section.pushMessage.assert_called_once()

    def test_rightClickOnEmptySpaceLeavesTheTool(self, section):
        tool = MagicMock()
        section.myMapTools["createReverseCross"] = tool
        assert section.runRemoveCrossingFromContext(None) is False
        section.iface.mapCanvas().unsetMapTool.assert_called_once_with(tool)


class TestTwoStepTools:
    def test_undoTsendsASinglePoint(self, section):
        assert section.runReverseTconnection(POINT) is True
        section.runCreateRemoveTconnections.assert_called_once_with(POINT, None)

    def test_dissolveJunctionSendsASinglePoint(self, section):
        assert section.runMergeJunction(POINT) is True
        section.runMergeSplitPoints.assert_called_once_with(POINT, None)
