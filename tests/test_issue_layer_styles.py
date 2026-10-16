# -*- coding: utf-8 -*-
"""The layers the network checks write get a shipped legend by severity.

One style per issue layer type ({Element}Issues.qml.bak), found the way every other style is
(project, global, shipped) and listed in the Legend Editor as a fixed legend of three classes:
Errors, Warnings, Information. Symbol levels draw the worst severity on top where an element
carries several issues.
"""
import os
import xml.etree.ElementTree as ElementTree
from unittest.mock import MagicMock, patch

import pytest

from .conftest import REAL_QGIS
from .test_legend_groups_trees import FakeGroup, FakeLayer, FakeLayerNode

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from QGISRed.tools.utils.qgisred_styling_utils import (
    ISSUE_CLASS_FIELD, ISSUE_CLASS_VALUES, ISSUE_LAYER_IDENTIFIERS, QGISRedStylingUtils,
)
from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")

# Per identifier: the layer name openIssuesLayers passes, and the geometry the DLL writes
ISSUE_LAYERS = {
    "qgisred_junctions_issues": ("Junctions_Issues", "Point"),
    "qgisred_tanks_issues": ("Tanks_Issues", "Point"),
    "qgisred_reservoirs_issues": ("Reservoirs_Issues", "Point"),
    "qgisred_pipes_issues": ("Pipes_Issues", "LineString"),
    "qgisred_valves_issues": ("Valves_Issues", "LineString"),
    "qgisred_pumps_issues": ("Pumps_Issues", "LineString"),
    "qgisred_isolationvalves_issues": ("IsolationValves_Issues", "Point"),
    "qgisred_serviceconnections_issues": ("ServiceConnections_Issues", "LineString"),
    "qgisred_meters_issues": ("Meters_Issues", "Point"),
}
ISSUE_SCHEMA = (
    "field=Id:string(31)&field=ErrorType:string(32)&field=MajorGroup:integer"
    "&field=MinorGroup:string(32)&field=Message:string(255)"
)


def _shippedPath(identifier):
    return os.path.join(SHIPPED, ISSUE_LAYERS[identifier][0].replace("_", "") + ".qml.bak")


def _shippedXml(identifier):
    return ElementTree.parse(_shippedPath(identifier)).getroot()


def _symbolLayers(root):
    """(class value, first symbol layer element) per class of a shipped style, in legend order."""
    renderer = root.find("renderer-v2")
    symbolsByName = {symbol.get("name"): symbol for symbol in renderer.find("symbols")}
    return [
        (category.get("value"), symbolsByName[category.get("symbol")].find("layer"))
        for category in renderer.find("categories")
    ]


def _optionValue(layerElement, name):
    return next(option.get("value") for option in layerElement.find("Option") if option.get("name") == name)


class _FakeLayer:
    """What openLayer builds for the file: records the style it was given and its identifier."""

    def __init__(self):
        self.loadedPath = None
        self.customProperties = {}
        self.metadata = None

    def loadNamedStyle(self, path):
        self.loadedPath = path

    def setCustomProperty(self, name, value):
        self.customProperties[name] = value

    def customProperty(self, name):
        return self.customProperties.get(name)

    def setMetadata(self, metadata):
        self.metadata = metadata

    def setLabelsEnabled(self, enabled):
        pass

    def labelsEnabled(self):
        return False

    def renderer(self):
        return None

    def mapTipTemplate(self):
        return ""

    def setMapTipTemplate(self, template):
        pass

    def labeling(self):
        return None

    def setName(self, name):
        pass


def _issuesUtils(tmp_path, globalFolder):
    """Layer utils as openIssuesLayers builds them, with a real style lookup behind them."""
    projectRoot = str(tmp_path / "project")
    utils = QGISRedLayerUtils(projectRoot, "Net", MagicMock(), group="Issues")
    issuesFolder = utils.LayersDirectory
    os.makedirs(issuesFolder)
    styling = utils._styling()
    styling._getQGISRedFolder = lambda: globalFolder
    utils._styling = lambda: styling
    return utils, issuesFolder, projectRoot


def _writeStyle(folder, fileName):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, fileName)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("<qgis></qgis>")
    return path


class TestShippedIssueStyles:
    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_every_issue_layer_ships_a_style_the_runtime_name_finds(self, tmp_path, identifier):
        styling = QGISRedStylingUtils(str(tmp_path / "project"), "Net")
        styling._getQGISRedFolder = lambda: str(tmp_path / "global")
        layer = _FakeLayer()

        styling.setStyle(layer, ISSUE_LAYERS[identifier][0].lower())

        assert layer.loadedPath == _shippedPath(identifier)
        assert os.path.exists(layer.loadedPath)

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_the_legend_is_by_severity_for_the_geometry_of_the_layer(self, identifier):
        root = _shippedXml(identifier)
        renderer = root.find("renderer-v2")

        assert renderer.get("type") == "categorizedSymbol"
        assert renderer.get("attr") == ISSUE_CLASS_FIELD
        assert [category.get("value") for category in renderer.find("categories")] == list(ISSUE_CLASS_VALUES)
        isPoint = ISSUE_LAYERS[identifier][1] == "Point"
        assert root.find("layerGeometryType").text == ("0" if isPoint else "1")
        assert {symbol.get("type") for symbol in renderer.find("symbols")} == {"marker" if isPoint else "line"}

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_the_worst_severity_is_drawn_on_top(self, identifier):
        root = _shippedXml(identifier)

        assert root.find("renderer-v2").get("symbollevels") == "1"
        passes = [int(symbolLayer.get("pass")) for _value, symbolLayer in _symbolLayers(root)]
        assert passes == sorted(passes, reverse=True) and len(set(passes)) == 3

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_each_severity_has_its_own_colour_shared_by_every_element(self, identifier):
        isPoint = ISSUE_LAYERS[identifier][1] == "Point"
        colorOption = "outline_color" if isPoint else "line_color"
        root = _shippedXml(identifier)
        colors = [_optionValue(symbolLayer, colorOption) for _value, symbolLayer in _symbolLayers(root)]
        assert len(set(colors)) == 3
        reference = [
            _optionValue(symbolLayer, "outline_color")
            for _value, symbolLayer in _symbolLayers(_shippedXml("qgisred_junctions_issues"))
        ]
        assert colors == reference

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_sizes_are_in_millimetres(self, identifier):
        isPoint = ISSUE_LAYERS[identifier][1] == "Point"
        for _value, symbolLayer in _symbolLayers(_shippedXml(identifier)):
            if isPoint:
                assert _optionValue(symbolLayer, "size_unit") == "MM"
                assert _optionValue(symbolLayer, "outline_width_unit") == "MM"
                assert float(_optionValue(symbolLayer, "size")) > 0
            else:
                assert _optionValue(symbolLayer, "line_width_unit") == "MM"
                assert float(_optionValue(symbolLayer, "line_width")) > 0

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_the_map_tip_shows_the_message_of_the_issue(self, identifier):
        mapTip = _shippedXml(identifier).find("mapTip")
        assert mapTip.get("enabled") == "1"
        assert '"Message"' in mapTip.text and '"Id"' in mapTip.text


class TestOpeningAnIssueLayer:
    def _open(self, utils, issuesFolder, name):
        with open(os.path.join(issuesFolder, "Net_" + name + ".shp"), "wb"):
            pass
        layer = _FakeLayer()
        # The project is replaced in both legs: the real one refuses a fake layer
        with patch("QGISRed.tools.utils.qgisred_layer_utils.QgsVectorLayer", return_value=layer), \
                patch("QGISRed.tools.utils.qgisred_layer_utils.QgsProject"):
            utils.openLayer(None, name, issues=True)
        return layer

    def test_a_new_issue_layer_takes_the_shipped_style(self, tmp_path):
        utils, issuesFolder, _ = _issuesUtils(tmp_path, str(tmp_path / "global"))

        layer = self._open(utils, issuesFolder, "Junctions_Issues")

        assert layer.loadedPath == os.path.join(SHIPPED, "JunctionsIssues.qml.bak")
        assert layer.customProperties["qgisred_identifier"] == "qgisred_junctions_issues"

    def test_the_project_style_saved_by_the_editor_wins(self, tmp_path):
        utils, issuesFolder, projectRoot = _issuesUtils(tmp_path, str(tmp_path / "global"))
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
        dialog.networkName = "Net"
        dialog.currentLayer = MagicMock()
        dialog.currentLayer.customProperty.side_effect = (
            lambda key, *a: {"qgisred_identifier": "qgisred_pipes_issues"}.get(key))
        fileName = dialog.getProjectStyleFilename(dialog.getStyleNameForIdentifier("qgisred_pipes_issues"))
        expected = _writeStyle(os.path.join(projectRoot, "layerStyles"), fileName)

        layer = self._open(utils, issuesFolder, "Pipes_Issues")

        assert layer.loadedPath == expected

    def test_the_global_style_is_loaded_when_the_project_has_none(self, tmp_path):
        globalFolder = str(tmp_path / "global")
        utils, issuesFolder, _ = _issuesUtils(tmp_path, globalFolder)
        expected = _writeStyle(os.path.join(globalFolder, "layerStyles"), "MetersIssues.qml")

        layer = self._open(utils, issuesFolder, "Meters_Issues")

        assert layer.loadedPath == expected

    def test_the_section_looks_the_styles_up_in_the_project_root(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()
        section.issuesLayers = ["Pipes_Issues"]
        with patch("QGISRed.sections.layer_management_section.QGISRedLayerUtils") as utilsCls:
            section.openIssuesLayers()

        utilsCls.assert_called_once_with("C:/proj", "Net", section.iface, group="Issues")
        utilsCls.return_value.openIssuesLayers.assert_called_once_with(
            utilsCls.return_value.getOrCreateNestedGroup.return_value, ["Pipes_Issues"])


class TestLegendEditor:
    @pytest.fixture(autouse=True)
    def fakeTreeClasses(self, monkeypatch):
        monkeypatch.setattr(legendsModule, "QgsLayerTreeGroup", FakeGroup)
        monkeypatch.setattr(legendsModule, "QgsLayerTreeLayer", FakeLayerNode)
        monkeypatch.setattr(legendsModule, "QgsVectorLayer", FakeLayer)

    def _dialog(self):
        return QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)

    def _root(self, issuesLayer):
        connectivity = FakeGroup("Connectivity", identifier="qgisred_connectivity", children=[
            FakeLayerNode(FakeLayer("qgisred_connectivity_links", "categorizedSymbol", name="Links")),
        ])
        issues = FakeGroup("Issues", identifier="qgisred_issues", children=[FakeLayerNode(issuesLayer), connectivity])
        return FakeGroup("", children=[FakeGroup("Network", children=[issues])])

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_the_issue_layers_are_fixed_legends_of_the_three_severities(self, identifier):
        assert QGISRedLegendsDialog.FIXED_LEGEND_CLASSES[identifier] == ISSUE_CLASS_VALUES
        assert identifier in QGISRedLegendsDialog.EDITABLE_QUERY_IDENTIFIERS

    def test_the_issues_group_is_listed_with_its_own_layers_only(self):
        pipes = FakeLayer("qgisred_pipes_issues", "categorizedSymbol", name="Pipes I")
        results = []
        self._dialog().collectGroupsRecursive(self._root(pipes), [], results)

        entries = {label: group for label, _path, group in results}
        assert "Issues" in entries and "Connectivity" in entries
        assert self._dialog().getRenderableLayersInGroup(entries["Issues"]) == [pipes]

    def test_a_single_symbol_issue_layer_of_an_older_version_is_still_listed(self):
        legacy = FakeLayer("qgisred_junctions_issues", "singleSymbol", name="Junctions I")
        assert self._dialog().getRenderableLayersInGroup(self._root(legacy)._children[0]._children[0]) == [legacy]

    def test_a_single_symbol_issue_layer_is_a_legacy_legend(self):
        legacy = FakeLayer("qgisred_junctions_issues", "singleSymbol")
        assert self._dialog().hasLegacyFixedLegend(legacy) is True

    def test_the_shipped_legend_is_not_a_legacy_one(self):
        class _Category:
            def __init__(self, value):
                self._value = value

            def value(self):
                return self._value

        class _Renderer:
            def type(self):
                return "categorizedSymbol"

            def categories(self):
                return [_Category(value) for value in ISSUE_CLASS_VALUES]

        shipped = FakeLayer("qgisred_junctions_issues", renderer=_Renderer())
        assert self._dialog().hasLegacyFixedLegend(shipped) is False


def _issueLayer(geometry, severities):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY

    layer = QgsVectorLayer("%s?crs=EPSG:25830&%s" % (geometry, ISSUE_SCHEMA), "issues", "memory")
    provider = layer.dataProvider()
    for index, severity in enumerate(severities):
        feature = QgsFeature(layer.fields())
        if geometry == "Point":
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
        else:
            feature.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(index, 0), QgsPointXY(index + 1, 0)]))
        feature.setAttributes(["E%d" % index, severity, 1, "E18", "message %d" % index])
        provider.addFeature(feature)
    layer.updateExtents()
    return layer


@pytest.mark.skipif(not REAL_QGIS, reason="needs real QGIS renderers")
class TestShippedIssueStylesInQgis:
    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_the_style_loads_as_a_legend_by_severity(self, identifier):
        from qgis.core import QgsCategorizedSymbolRenderer

        _name, geometry = ISSUE_LAYERS[identifier]
        layer = _issueLayer(geometry, ISSUE_CLASS_VALUES)

        _message, loaded = layer.loadNamedStyle(_shippedPath(identifier))

        assert loaded
        renderer = layer.renderer()
        assert isinstance(renderer, QgsCategorizedSymbolRenderer)
        assert renderer.classAttribute() == ISSUE_CLASS_FIELD
        assert [category.value() for category in renderer.categories()] == list(ISSUE_CLASS_VALUES)
        assert renderer.usingSymbolLevels()
        passes = [category.symbol().symbolLayer(0).renderingPass() for category in renderer.categories()]
        assert passes == [2, 1, 0]
        assert '"Message"' in layer.mapTipTemplate()

    @pytest.mark.parametrize("identifier", ISSUE_LAYER_IDENTIFIERS)
    def test_each_class_is_coloured_where_the_editor_reads_it(self, identifier):
        from qgis.core import QgsLineSymbol

        _name, geometry = ISSUE_LAYERS[identifier]
        layer = _issueLayer(geometry, ISSUE_CLASS_VALUES)
        layer.loadNamedStyle(_shippedPath(identifier))
        dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)

        colors = []
        for category in layer.renderer().categories():
            symbol = category.symbol()
            color = dialog.fixedClassColor(symbol, category.value())
            colors.append(color.name())
            if not isinstance(symbol, QgsLineSymbol):
                # A ring around the element: the inside stays see-through
                assert symbol.symbolLayer(0).color().alpha() == 0
        assert len(set(colors)) == 3

    def test_open_layer_styles_a_generated_issue_shapefile(self, tmp_path):
        from qgis.core import QgsProject, QgsVectorFileWriter, QgsCategorizedSymbolRenderer

        projectRoot = str(tmp_path)
        issuesFolder = os.path.join(projectRoot, "Issues")
        os.makedirs(issuesFolder)
        shapefile = os.path.join(issuesFolder, "Net_Junctions_Issues.shp")
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        QgsVectorFileWriter.writeAsVectorFormatV3(
            _issueLayer("Point", ["Error", "Info"]), shapefile, QgsProject.instance().transformContext(), options)
        utils = QGISRedLayerUtils(projectRoot, "Net", MagicMock(), group="Issues")
        utils._styling()._getQGISRedFolder = lambda: str(tmp_path / "global")

        utils.openLayer(None, "Junctions_Issues", issues=True)

        opened = utils._findLayerByPath(utils._fs().getUniformedPath(shapefile))
        try:
            assert opened is not None
            assert opened.customProperty("qgisred_identifier") == "qgisred_junctions_issues"
            renderer = opened.renderer()
            assert isinstance(renderer, QgsCategorizedSymbolRenderer)
            assert renderer.classAttribute() == ISSUE_CLASS_FIELD
            assert [category.label() for category in renderer.categories()] == ["Errors", "Warnings", "Information"]
            assert renderer.usingSymbolLevels()
        finally:
            if opened is not None:
                QgsProject.instance().removeMapLayer(opened.id())
