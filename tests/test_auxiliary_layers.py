# -*- coding: utf-8 -*-
"""The Demand Builder's auxiliary themes: naming, listing, and the Accept diff.

Several themes of each type can coexist, so what ties a file to its type — and therefore
to its qgisred_identifier and its style — is the token its name carries. These tests pin
that convention down, because everything else in the feature is derived from it.

All QGIS / PyQt dependencies are mocked via conftest.py.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from .conftest import REAL_QGIS

from QGISRed.tools.utils.qgisred_auxiliary_layers import (
    AUXILIARY_LAYER_TYPES,
    AUXILIARY_TYPES_BY_KEY,
    DEFAULT_BASE_DEMAND_FIELD,
    composeBaseName,
    deleteTheme,
    isValidThemeName,
    listThemes,
    parseBaseName,
)

if REAL_QGIS:
    # QgsSymbol.defaultSymbol() takes the geometry enum, not its int value.
    from qgis.core import QgsVectorLayer
    POLYGON_GEOMETRY = QgsVectorLayer('Polygon?crs=EPSG:25830', 'probe', 'memory').geometryType()
else:
    POLYGON_GEOMETRY = 2

_UTILS_CLS = "QGISRed.sections.layer_management_section.QGISRedLayerUtils"

CONSUMPTION = AUXILIARY_TYPES_BY_KEY["Consumptions"]
LINKS = AUXILIARY_TYPES_BY_KEY["Links"]
SECTORS = AUXILIARY_TYPES_BY_KEY["Sectors"]


class TestComposeBaseName:
    def test_a_named_theme_carries_network_type_and_name(self):
        assert composeBaseName("Net", CONSUMPTION, "Facturacion2024") == \
            "Net_DemandBuilder_Consumptions_Facturacion2024"

    def test_the_demands_manager_theme_has_no_trailing_name(self):
        assert composeBaseName("Net", SECTORS) == "Net_DemandBuilder_Sectors"

    def test_the_composed_name_parses_back(self):
        base = composeBaseName("Net", LINKS, "Enlaces")
        assert parseBaseName(base, "Net") == (LINKS, "Enlaces")


class TestParseBaseName:
    def test_a_named_theme_resolves_to_its_type(self):
        layerType, name = parseBaseName("Net_DemandBuilder_ConsumptionPoints_Padron", "Net")
        assert layerType is CONSUMPTION
        assert name == "Padron"

    def test_the_unnamed_theme_resolves_with_an_empty_name(self):
        assert parseBaseName("Net_DemandBuilder_Sectors", "Net") == (SECTORS, "")

    def test_a_theme_name_may_contain_underscores(self):
        _, name = parseBaseName("Net_DemandBuilder_DemandLinks_Alta_Zona_2", "Net")
        assert name == "Alta_Zona_2"

    def test_the_network_prefix_is_optional(self):
        """A folder copied between projects must still read."""
        assert parseBaseName("DemandBuilder_Sectors_Barrios") == (SECTORS, "Barrios")

    def test_a_network_named_after_a_token_does_not_confuse_it(self):
        layerType, name = parseBaseName("Sectors_DemandBuilder_Sectors_A", "Sectors")
        assert layerType is SECTORS
        assert name == "A"

    def test_isolated_demands_connections_is_not_a_managed_theme(self):
        """It lives in the same folder but the layer manager does not offer it."""
        assert parseBaseName("Net_DemandBuilder_IsolatedDemandsServiceConnections", "Net") == (None, "")

    def test_an_unrelated_file_is_rejected(self):
        assert parseBaseName("Net_Pipes", "Net") == (None, "")

    def test_an_empty_name_is_rejected(self):
        assert parseBaseName("", "Net") == (None, "")


class TestShortenedFileNames:
    """New files carry DemandBuilder_{Type}; the long spelling is still read.

    Themes created before the rename keep it, and so do the ones the Demands Manager
    writes by itself, which the plugin does not name.
    """

    def test_new_files_use_the_short_token(self):
        assert composeBaseName("Net", CONSUMPTION, "pr1") == "Net_DemandBuilder_Consumptions_pr1"
        assert composeBaseName("Net", LINKS, "en2") == "Net_DemandBuilder_Links_en2"
        assert composeBaseName("Net", SECTORS, "sec1") == "Net_DemandBuilder_Sectors_sec1"

    @pytest.mark.parametrize("baseName,expected", [
        ("Net_DemandBuilder_Consumptions_pr1", "Consumptions"),
        ("Net_DemandBuilder_Links_en2", "Links"),
        ("Net_DemandBuilder_Sectors_sec1", "Sectors"),
    ])
    def test_the_short_token_parses_back(self, baseName, expected):
        layerType, _name = parseBaseName(baseName, "Net")
        assert layerType.key == expected

    @pytest.mark.parametrize("baseName,expected", [
        ("Net_DemandsBuilder_ConsumptionPoints_pr1", "Consumptions"),
        ("Net_DemandsBuilder_DemandLinks_en2", "Links"),
        ("Net_DemandsBuilder_Sectors_sec1", "Sectors"),
    ])
    def test_files_written_before_the_rename_still_read(self, baseName, expected):
        layerType, _name = parseBaseName(baseName, "Net")
        assert layerType.key == expected

    def test_the_short_and_long_spellings_are_the_same_type(self):
        short, _ = parseBaseName("Net_DemandBuilder_Sectors_a", "Net")
        long, _ = parseBaseName("Net_DemandsBuilder_Sectors_a", "Net")
        assert short is long

    def test_both_spellings_are_listed_together(self, tmp_path):
        folder = str(tmp_path)
        _touchTheme(folder, "Net_DemandBuilder_Sectors_nuevo")
        _touchTheme(folder, "Net_DemandsBuilder_Sectors_viejo")

        themes = listThemes(folder, "Net")

        assert [name for _type, name, _path in themes] == ["nuevo", "viejo"]

    def test_the_identifier_did_not_follow_the_rename(self):
        """Legend names, saved styles and the legend editor are all keyed on it, and so
        are the identifiers already written into existing .qgs projects."""
        assert CONSUMPTION.identifier == "qgisred_demandbuilder_consumptionpoints"
        assert LINKS.identifier == "qgisred_demandbuilder_demandlinks"
        assert SECTORS.identifier == "qgisred_demandbuilder_sectors"

    def test_the_dll_contract_uses_the_same_words_as_the_files(self):
        assert {t.key for t in AUXILIARY_LAYER_TYPES} == {"Consumptions", "Links", "Sectors"}

    def test_no_short_token_hides_inside_a_long_one(self):
        """Otherwise a file would resolve to whichever type happened to be checked first."""
        tokens = [token for t in AUXILIARY_LAYER_TYPES for token in t.fileTokens]
        for token in tokens:
            others = [other for other in tokens if other != token]
            assert not any(token in other for other in others), token


class TestIsValidThemeName:
    @pytest.mark.parametrize("name", ["Facturacion2024", "Alta_Zona_2", "a"])
    def test_plain_names_are_accepted(self, name):
        assert isValidThemeName(name) is True

    @pytest.mark.parametrize("name", ["", "  ", " Padron", "Padron ", "a/b", "a\\b", "a:b", "a*b", "a?b"])
    def test_a_name_that_could_escape_the_folder_is_rejected(self, name):
        assert isValidThemeName(name) is False


def _uniform(path):
    """Same normalisation the dialog applies, so expectations line up on Windows."""
    from QGISRed.tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils
    return QGISRedFileSystemUtils().getUniformedPath(path)


def _touchTheme(folder, baseName):
    os.makedirs(folder, exist_ok=True)
    for extension in (".shp", ".shx", ".dbf"):
        open(os.path.join(folder, baseName + extension), "w").close()
    return os.path.join(folder, baseName + ".shp")


class TestListThemes:
    def test_only_recognised_shapefiles_are_listed(self, tmp_path):
        folder = str(tmp_path)
        _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        _touchTheme(folder, "Net_DemandBuilder_IsolatedDemandsServiceConnections")
        _touchTheme(folder, "Net_Pipes")

        themes = listThemes(folder, "Net")

        assert [(t.key, name) for t, name, _ in themes] == [("Sectors", "Barrios")]

    def test_themes_are_sorted_by_type_then_name(self, tmp_path):
        folder = str(tmp_path)
        _touchTheme(folder, "Net_DemandBuilder_Sectors_Zonas")
        _touchTheme(folder, "Net_DemandBuilder_ConsumptionPoints_Padron")
        _touchTheme(folder, "Net_DemandBuilder_ConsumptionPoints_Facturacion")

        themes = listThemes(folder, "Net")

        assert [name for _, name, _ in themes] == ["Facturacion", "Padron", "Zonas"]

    def test_a_missing_folder_is_not_an_error(self, tmp_path):
        assert listThemes(str(tmp_path / "nope"), "Net") == []


class TestDeleteTheme:
    def test_every_sidecar_goes_with_the_shapefile(self, tmp_path):
        """A theme that leaves its .dbf behind comes back as a broken row."""
        folder = str(tmp_path)
        path = _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        open(os.path.join(folder, "Net_DemandBuilder_Sectors_Barrios.prj"), "w").close()

        assert deleteTheme(path) == ""
        assert os.listdir(folder) == []

    def test_deleting_what_is_already_gone_is_not_an_error(self, tmp_path):
        assert deleteTheme(str(tmp_path / "Net_DemandBuilder_Sectors_X.shp")) == ""


class TestIdentifierNormalisation:
    """A user-named theme must still resolve to the identifier of its type."""

    def _normalize(self, name):
        from QGISRed.tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
        utils = object.__new__(QGISRedIdentifierUtils)
        return utils._normalizeDemandBuilderLayerType(name)

    def test_a_named_theme_collapses_onto_its_type(self):
        assert self._normalize("Net_DemandBuilder_Consumptions_Facturacion2024") == \
            "demandbuilder_consumptionpoints"

    def test_the_unnamed_theme_still_collapses(self):
        assert self._normalize("Net_DemandBuilder_Sectors") == "demandbuilder_sectors"

    def test_the_token_passed_by_the_loader_collapses(self):
        assert self._normalize("DemandBuilder_DemandLinks") == "demandbuilder_demandlinks"

    def test_isolated_demands_connections_keeps_its_own_identifier(self):
        assert self._normalize("Net_DemandBuilder_IsolatedDemandsServiceConnections") == \
            "demandbuilder_isolateddemandsserviceconnections"

    def test_an_unrelated_name_is_left_alone(self):
        assert self._normalize("Net_Pipes") == "Net_Pipes"


class TestGroupConfigLookup:
    """The metadata round trip drops spaces at both ends; the lookup must too.

    `_buildGroupsString` strips them to keep the XML tags ASCII, and `_openGroupsNode`
    strips them again on the way back, so a two-word group arrives as one word. While the
    keys were matched literally, nothing under Auxiliary Layers reopened.
    """

    def _config(self, groupName):
        from QGISRed.tools.utils.qgisred_project_io import QGISRedProjectIO
        return QGISRedProjectIO._groupConfig(groupName)

    def test_the_demand_builder_group_is_found_without_its_space(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
        assert self._config("AuxiliaryLayers/DemandBuilder") is LAYER_TYPE_CONFIG["DemandBuilder"]

    def test_the_demand_sectors_group_is_found_without_its_space(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
        assert self._config("AuxiliaryLayers/DemandSectors") is LAYER_TYPE_CONFIG["DemandSectors"]

    def test_the_spelled_out_key_still_resolves(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
        assert self._config("Auxiliary Layers/DemandBuilder") is LAYER_TYPE_CONFIG["DemandBuilder"]

    def test_groups_without_spaces_are_unaffected(self):
        assert self._config("Inputs") is not None
        assert self._config("Issues/HydraulicSectors") is not None

    def test_an_unknown_group_is_still_unknown(self):
        assert self._config("Whatever/Else") is None

    def test_an_empty_name_is_not_a_match(self):
        assert self._config("") is None

    def test_a_localised_parent_tag_still_resolves(self):
        """Projects written before the parent group carried its identifier have its
        translated name in the metadata: <CapasAuxiliares>, <CouchesAuxiliaires>…"""
        from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
        assert self._config("CapasAuxiliares/DemandBuilder") is LAYER_TYPE_CONFIG["DemandBuilder"]
        assert self._config("CouchesAuxiliaires/DemandSectors") is LAYER_TYPE_CONFIG["DemandSectors"]

    def test_a_dynamic_subgroup_is_not_swallowed_by_the_fallback(self):
        """Results/Base must keep reaching the top-level branch that handles sub-paths."""
        assert self._config("Results/Base") is None

    def test_the_fallback_needs_a_nested_key(self):
        assert self._config("Whatever/Inputs") is None


class TestGroupIdentifierAssignment:
    def test_the_declared_identifier_wins_over_the_derived_one(self):
        """qgisred_auxiliarylayers is not in _IDENTIFIER_TO_CANONICAL, so deriving it made
        the group fall back to its localised name when the metadata was written."""
        from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        group = MagicMock()
        group.customProperty.return_value = None
        QGISRedLayerUtils.setGroupIdentifier(group, "Auxiliary Layers")

        group.setCustomProperty.assert_called_once_with("qgisred_identifier", "qgisred_auxiliary")

    def test_a_group_without_a_declared_identifier_still_derives_one(self):
        from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        # setGroupIdentifier registers what it derives into the class dictionaries, so an
        # unknown name has to be rolled back or it leaks into every later test.
        declared = dict(QGISRedLayerUtils.groupIdentifiers)
        byIdentifier = dict(QGISRedLayerUtils.identifierToGroupName)
        try:
            group = MagicMock()
            group.customProperty.return_value = None
            QGISRedLayerUtils.setGroupIdentifier(group, "Some New Group")

            group.setCustomProperty.assert_called_once_with("qgisred_identifier", "qgisred_somenewgroup")
        finally:
            QGISRedLayerUtils.groupIdentifiers = declared
            QGISRedLayerUtils.identifierToGroupName = byIdentifier

    def test_every_declared_identifier_has_a_canonical_name(self):
        """Otherwise getCanonicalGroupName falls back to the localised name and the
        metadata gets a tag nothing can read back."""
        from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        missing = [
            identifier for identifier in QGISRedLayerUtils.groupIdentifiers.values()
            if identifier not in QGISRedLayerUtils._IDENTIFIER_TO_CANONICAL
        ]
        assert missing == []


class TestDemandBuilderStyleFlag:
    """The look is computed, not shipped as a QML, so openLayer must apply it.

    Demand sectors already work this way. Doing it here too is what removed the need for a
    "restyle after the project loaded" special case on the metadata-only path.
    """

    def test_the_group_config_carries_the_flag(self):
        from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
        assert LAYER_TYPE_CONFIG["DemandBuilder"]["flags"] == {"demandBuilder": True}

    def test_open_layer_accepts_it(self):
        import inspect
        from QGISRed.tools.utils.qgisred_layer_utils import QGISRedLayerUtils
        assert "demandBuilder" in inspect.signature(QGISRedLayerUtils.openLayer).parameters

    def test_the_styling_utils_own_the_look(self):
        from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
        assert hasattr(QGISRedStylingUtils, "setDemandBuilderStyle")

    def test_the_isolated_demands_connections_keep_their_qml(self):
        """They are told apart by file name, not by the display name they end up with."""
        from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

        styling = object.__new__(QGISRedStylingUtils)
        styling.setStyle = MagicMock()
        layer = MagicMock()
        layer.name.return_value = "DemBuild_Isolated Demands Connections"

        styling.setDemandBuilderStyle(layer, "DemandBuilder_IsolatedDemandsServiceConnections")

        styling.setStyle.assert_called_once_with(
            layer, "DemandBuilderIsolatedDemandsServiceConnections")

    def test_a_theme_does_not_take_that_qml(self):
        from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

        styling = object.__new__(QGISRedStylingUtils)
        styling.setStyle = MagicMock()
        styling.translateRendererLabels = MagicMock()
        layer = MagicMock()
        layer.name.return_value = "DemBuild_Sectors"
        layer.fields.return_value.indexFromName.return_value = -1
        layer.geometryType.return_value = POLYGON_GEOMETRY

        styling.setDemandBuilderStyle(layer, "DemandBuilder_Sectors_Barrios")

        styling.setStyle.assert_not_called()
        layer.setRenderer.assert_called_once()


class TestApplyAuxiliaryLayerSelection:
    def _makeSection(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()
        section.layerOperationInProgress = False
        section.openAuxiliaryThemes = MagicMock()
        section.closeAuxiliaryThemes = MagicMock()
        return section

    def test_only_unchecked_themes_are_closed(self):
        section = self._makeSection()
        managed = ["C:/proj/a.shp", "C:/proj/b.shp", "C:/proj/c.shp"]

        section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], managed)

        assert section.closeAuxiliaryThemes.call_args[0][0] == ["C:/proj/b.shp", "C:/proj/c.shp"]

    def test_checked_themes_are_opened(self):
        section = self._makeSection()

        section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], ["C:/proj/a.shp"])

        section.openAuxiliaryThemes.assert_called_once_with(["C:/proj/a.shp"])
        assert section.closeAuxiliaryThemes.call_args[0][0] == []

    def test_the_comparison_ignores_path_case(self):
        """Windows hands back the same file spelled either way.

        os.path.normcase only folds case on Windows, so on any other platform
        the fold has to be simulated — otherwise this passes for the wrong
        reason there and the check would be just as green with one of the two
        sides not normalised at all.
        """
        section = self._makeSection()

        with patch("os.path.normcase", str.lower):
            section.applyAuxiliaryLayerSelection(["C:/proj/A.shp"], ["c:/proj/a.shp"])

        assert section.closeAuxiliaryThemes.call_args[0][0] == []

    def test_the_flag_is_released_even_when_opening_fails(self):
        section = self._makeSection()
        section.openAuxiliaryThemes.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError):
            section.applyAuxiliaryLayerSelection(["C:/proj/a.shp"], ["C:/proj/a.shp"])

        assert section.layerOperationInProgress is False


class TestAuxiliaryThemeName:
    """A theme must read the same whether the layer manager or the metadata loaded it."""

    def _identifiers(self, families=None):
        from QGISRed.tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils

        utils = object.__new__(QGISRedIdentifierUtils)
        utils.NetworkName = "Net"
        known = families if families is not None else {
            "qgisred_demandbuilder_consumptionpoints": "DemBuild_Consumptions",
            "qgisred_demandbuilder_demandlinks": "DemBuild_Links",
            "qgisred_demandbuilder_sectors": "DemBuild_Sectors",
        }
        utils.getTranslatedNameForIdentifier = lambda identifier: known.get(identifier)
        return utils

    def test_a_named_theme_shows_its_family_and_its_name(self):
        utils = self._identifiers()
        assert utils.getAuxiliaryThemeName("Net_DemandBuilder_ConsumptionPoints_pr1") == \
            "DemBuild_Consumptions_pr1"

    def test_the_demands_manager_theme_shows_only_its_family(self):
        utils = self._identifiers()
        assert utils.getAuxiliaryThemeName("Net_DemandBuilder_Sectors") == "DemBuild_Sectors"

    def test_each_family_keeps_its_own_name(self):
        """They all used to collapse onto 'Multiple Demands': getLayerNameToLegend rewrites
        anything containing 'Demands', and DemandBuilder is in every one of these."""
        utils = self._identifiers()
        names = [
            utils.getAuxiliaryThemeName("Net_DemandBuilder_ConsumptionPoints_pr1"),
            utils.getAuxiliaryThemeName("Net_DemandBuilder_DemandLinks_en2"),
            utils.getAuxiliaryThemeName("Net_DemandBuilder_Sectors_sec1"),
        ]
        assert len(set(names)) == 3
        assert not any("Multiple Demands" in name for name in names)

    def test_two_themes_of_one_family_are_told_apart(self):
        utils = self._identifiers()
        first = utils.getAuxiliaryThemeName("Net_DemandBuilder_ConsumptionPoints_pr1")
        second = utils.getAuxiliaryThemeName("Net_DemandBuilder_ConsumptionPoints_consumPuntual")
        assert first != second

    def test_a_file_that_is_not_a_theme_gets_no_name(self):
        utils = self._identifiers()
        assert utils.getAuxiliaryThemeName("Net_Pipes") == ""

    def test_an_unknown_family_gets_no_name(self):
        """The caller falls back rather than showing half a name."""
        utils = self._identifiers(families={})
        assert utils.getAuxiliaryThemeName("Net_DemandBuilder_Sectors_sec1") == ""


class TestGroupVisibility:
    """The layer manager loads and unloads on request; it does not retick the legend.

    Every other tool opens layers as the result of running something and is expected to
    show what it produced, which is what getOrCreateNestedGroup does by default.
    """

    def _makeSection(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()
        return section

    def test_opening_a_theme_leaves_the_legend_alone(self):
        section = self._makeSection()
        with patch(_UTILS_CLS) as utilsCls:
            section.getDemandBuilderGroup(applyVisibility=False)
        _path, applyVisibility = utilsCls.return_value.getOrCreateNestedGroup.call_args[0]
        assert applyVisibility is False

    def test_the_demands_manager_still_brings_its_group_forward(self):
        section = self._makeSection()
        with patch(_UTILS_CLS) as utilsCls:
            section.getDemandBuilderGroup()
        _path, applyVisibility = utilsCls.return_value.getOrCreateNestedGroup.call_args[0]
        assert applyVisibility is True

    def test_the_auxiliary_loader_asks_for_no_visibility_changes(self):
        section = self._makeSection()
        section.getDemandBuilderGroup = MagicMock()
        with patch(_UTILS_CLS) as utilsCls:
            utilsCls.return_value._tryReloadExistingLayer.return_value = True
            section.openAuxiliaryThemes([__file__])
        section.getDemandBuilderGroup.assert_called_once_with(applyVisibility=False)


class TestCloseAuxiliaryThemes:
    def test_the_layer_is_removed_from_the_project(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()

        layer = MagicMock()
        layer.id.return_value = "layer-1"
        with patch(_UTILS_CLS) as utilsCls, \
                patch("QGISRed.sections.layer_management_section.QgsProject") as project:
            utilsCls.return_value._findLayerByPath.return_value = layer
            section.closeAuxiliaryThemes(["C:/proj/a.shp"])

        project.instance.return_value.removeMapLayer.assert_called_once_with("layer-1")

    def test_nothing_happens_without_paths(self):
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        with patch(_UTILS_CLS) as utilsCls:
            section.closeAuxiliaryThemes([])
        utilsCls.assert_not_called()

    def test_the_path_is_resolved_before_looking_the_layer_up(self):
        """_findLayerByPath compares against getUniformedPath, which resolves the path.

        Handing it an os.path.join path left the layer open and its shapefile locked, so
        deleting the theme afterwards failed with 'file in use'.
        """
        from QGISRed.sections.layer_management_section import LayerManagementSection

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = "C:/proj"
        section.NetworkName = "Net"
        section.iface = MagicMock()

        with patch(_UTILS_CLS) as utilsCls, \
                patch("QGISRed.sections.layer_management_section.QgsProject"):
            utils = utilsCls.return_value
            utils._findLayerByPath.return_value = None
            section.closeAuxiliaryThemes(["C:/proj/Auxiliary Layers/a.shp"])

        assert utils._findLayerByPath.call_args[0][0] == _uniform("C:/proj/Auxiliary Layers/a.shp")


# ---------------------------------------------------------------------------
# The Auxiliary layers tab
# ---------------------------------------------------------------------------

_DIALOG_MOD = "QGISRed.ui.project.qgisred_layermanagement_dialog"


class _FakeItem:
    """Stands in for QTableWidgetItem, which is a bare mock in this harness."""

    def __init__(self, text=""):
        self._text = text
        self._checkState = None
        self._data = {}

    def setFlags(self, flags):
        self._flags = flags

    def setCheckState(self, state):
        self._checkState = state

    def checkState(self):
        return self._checkState

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)

    def text(self):
        return self._text


class _FakeTable:
    def __init__(self):
        self._rows = 0
        self._items = {}
        self._current = -1

    def setRowCount(self, rows):
        self._rows = rows
        self._items = {key: item for key, item in self._items.items() if key[0] < rows}

    def rowCount(self):
        return self._rows

    def setItem(self, row, column, item):
        self._items[(row, column)] = item

    def item(self, row, column):
        return self._items.get((row, column))

    def currentRow(self):
        return self._current


def _qt():
    """The Qt the dialog captured at import time.

    Another test module may have swapped sys.modules['qgis.PyQt.QtCore'] since, and the
    mocked enum members are only identical to themselves.
    """
    from QGISRed.ui.project import qgisred_layermanagement_dialog
    return qgisred_layermanagement_dialog.Qt


def _makeDialog(projectDirectory, networkName="Net"):
    from QGISRed.ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog

    dialog = QGISRedLayerManagementDialog.__new__(QGISRedLayerManagementDialog)
    dialog.NetworkName = networkName
    dialog.ProjectDirectory = str(projectDirectory)
    dialog.iface = MagicMock()
    dialog.utils = MagicMock()
    dialog.utils.getLayers.return_value = []
    dialog.parent = MagicMock()
    dialog.messageBar = MagicMock()
    dialog.crs = MagicMock()
    dialog.crs.toWkt.return_value = ""
    dialog.tbAuxiliary = _FakeTable()
    dialog.elements = []
    return dialog


def _auxFolder(projectDirectory):
    from QGISRed.tools.utils.qgisred_filesystem_utils import LAYER_TYPE_CONFIG
    folder = os.path.join(str(projectDirectory), LAYER_TYPE_CONFIG["DemandBuilder"]["subdir"])
    os.makedirs(folder, exist_ok=True)
    return folder


class TestFillAuxiliaryTable:
    def test_one_row_per_theme_on_disk(self, tmp_path):
        folder = _auxFolder(tmp_path)
        _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        _touchTheme(folder, "Net_DemandBuilder_ConsumptionPoints_Padron")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.rowCount() == 2

    def test_a_loaded_theme_comes_back_checked(self, tmp_path):
        Qt = _qt()
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(return_value={os.path.normcase(path)})

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).checkState() == Qt.CheckState.Checked

    def test_an_unloaded_theme_comes_back_unchecked(self, tmp_path):
        Qt = _qt()
        _touchTheme(_auxFolder(tmp_path), "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(return_value=set())

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).checkState() == Qt.CheckState.Unchecked

    def test_the_name_and_the_type_sit_beside_the_checkbox(self, tmp_path):
        """The checkbox has a column of its own; name and type follow it."""
        _touchTheme(_auxFolder(tmp_path), "Net_DemandBuilder_DemandLinks_p1")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).text() == ""
        assert dialog.tbAuxiliary.item(0, 1).text() == "p1"
        assert dialog.tbAuxiliary.item(0, 2).text() is not None

    def test_the_demands_manager_theme_is_labelled_as_the_default_one(self, tmp_path):
        _touchTheme(_auxFolder(tmp_path), "Net_DemandBuilder_Sectors")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 1).text() != ""

    def test_the_row_carries_the_path_of_its_theme(self, tmp_path):
        Qt = _qt()
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.item(0, 0).data(Qt.ItemDataRole.UserRole) == _uniform(path)

    def test_stale_rows_do_not_survive_a_refresh(self, tmp_path):
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
            deleteTheme(path)
            dialog.fillAuxiliaryTable()

        assert dialog.tbAuxiliary.rowCount() == 0
        assert dialog.auxiliaryRowPaths() == []


class TestAuxiliaryRowPaths:
    def _fill(self, tmp_path, checked):
        folder = _auxFolder(tmp_path)
        first = _touchTheme(folder, "Net_DemandBuilder_ConsumptionPoints_A")
        second = _touchTheme(folder, "Net_DemandBuilder_Sectors_B")
        dialog = _makeDialog(tmp_path)
        dialog.openLayerPaths = MagicMock(
            return_value={os.path.normcase(p) for p in checked}
        )
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
        return dialog, first, second

    def test_every_row_is_reported_as_managed(self, tmp_path):
        dialog, first, second = self._fill(tmp_path, [])
        assert set(dialog.auxiliaryRowPaths()) == {_uniform(first), _uniform(second)}

    def test_nothing_loaded_means_nothing_selected(self, tmp_path):
        dialog, _, _ = self._fill(tmp_path, [])
        assert dialog.auxiliaryRowPaths(onlyChecked=True) == []

    def test_only_the_loaded_theme_is_selected(self, tmp_path):
        folder = _auxFolder(tmp_path)
        loaded = os.path.join(folder, "Net_DemandBuilder_ConsumptionPoints_A.shp")
        dialog, first, _ = self._fill(tmp_path, [loaded])
        assert dialog.auxiliaryRowPaths(onlyChecked=True) == [_uniform(first)]


class TestCreateAuxiliaryTheme:
    """Writing the file is the DLL's job; the dialog composes the path and reacts."""

    def _run(self, dialog, layerType, name, resMessage="True"):
        def write(_project, _network, _themeType, path, _baseDemand):
            if resMessage == "True":
                _touchTheme(os.path.dirname(path), os.path.splitext(os.path.basename(path))[0])
            return resMessage

        with patch(_DIALOG_MOD + "._NewAuxiliaryThemeDialog") as dialogCls, \
                patch(_DIALOG_MOD + ".GISRed") as gisred, \
                patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialogCls.return_value.exec.return_value = True
            dialogCls.return_value.selection.return_value = (layerType, name)
            gisred.CreateAuxiliaryLayer.side_effect = write
            dialog.createAuxiliaryTheme()
            return gisred

    def test_the_dll_is_asked_for_the_composed_path(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "Barrios")

        expected = os.path.join(_auxFolder(tmp_path), "Net_DemandBuilder_Sectors_Barrios.shp")
        assert gisred.CreateAuxiliaryLayer.call_args[0] == (
            dialog.ProjectDirectory, "Net", "Sectors", expected, DEFAULT_BASE_DEMAND_FIELD)

    def test_the_created_theme_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios")

        expected = os.path.join(_auxFolder(tmp_path), "Net_DemandBuilder_Sectors_Barrios.shp")
        dialog.parent.syncAuxiliaryThemes.assert_called_once_with([expected], load=True)

    def test_the_new_row_shows_up_in_the_table(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, LINKS, "Enlaces")

        assert dialog.tbAuxiliary.rowCount() == 1

    def test_a_dll_error_is_reported_and_nothing_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios", resMessage="Unknown auxiliary theme type")

        dialog.parent.syncAuxiliaryThemes.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 2

    def test_a_dll_warning_is_reported_and_nothing_is_loaded(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        self._run(dialog, SECTORS, "Barrios", resMessage="False")

        dialog.parent.syncAuxiliaryThemes.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_an_existing_name_is_refused_before_calling_the_dll(self, tmp_path):
        folder = _auxFolder(tmp_path)
        _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "Barrios")

        gisred.CreateAuxiliaryLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_a_name_that_could_escape_the_folder_is_refused(self, tmp_path):
        _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        gisred = self._run(dialog, SECTORS, "../evil")

        gisred.CreateAuxiliaryLayer.assert_not_called()
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1

    def test_cancelling_writes_nothing(self, tmp_path):
        folder = _auxFolder(tmp_path)
        dialog = _makeDialog(tmp_path)

        with patch(_DIALOG_MOD + "._NewAuxiliaryThemeDialog") as dialogCls, \
                patch(_DIALOG_MOD + ".GISRed") as gisred:
            dialogCls.return_value.exec.return_value = False
            dialog.createAuxiliaryTheme()

        assert os.listdir(folder) == []
        gisred.CreateAuxiliaryLayer.assert_not_called()


class TestDeleteAuxiliaryTheme:
    def _dialog(self, tmp_path):
        folder = _auxFolder(tmp_path)
        path = _touchTheme(folder, "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()
        dialog.tbAuxiliary._current = 0
        return dialog, path

    def _confirm(self, dialog, accepted=True, runDeferred=True):
        """Delete, then run what was scheduled — the file removal waits one event loop turn."""
        scheduled = []
        with patch(_DIALOG_MOD + ".QMessageBox") as messageBox, \
                patch(_DIALOG_MOD + ".QTimer") as timer, \
                patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            answer = messageBox.StandardButton.Yes if accepted else messageBox.StandardButton.No
            messageBox.question.return_value = answer
            timer.singleShot.side_effect = lambda _delay, callback: scheduled.append(callback)
            dialog.deleteAuxiliaryTheme()
            if runDeferred:
                for callback in scheduled:
                    callback()
        return scheduled

    def test_the_files_are_removed(self, tmp_path):
        dialog, path = self._dialog(tmp_path)

        self._confirm(dialog)

        assert not os.path.exists(path)
        assert os.listdir(os.path.dirname(path)) == []

    def test_the_layer_is_unloaded_before_the_file_is_deleted(self, tmp_path):
        """Deleting a shapefile QGIS still holds leaves a handle pointing at nothing."""
        dialog, path = self._dialog(tmp_path)
        order = []
        dialog.parent.syncAuxiliaryThemes.side_effect = \
            lambda paths, load: order.append(("close", os.path.exists(path)))

        self._confirm(dialog)
        order.append(("deleted", not os.path.exists(path)))

        assert order == [("close", True), ("deleted", True)]

    def test_the_removal_waits_a_turn_of_the_event_loop(self, tmp_path):
        """removeMapLayer only schedules the layer's destruction: deleting the file in the
        same call stack is what used to fail with 'in use' on a loaded theme."""
        dialog, path = self._dialog(tmp_path)

        scheduled = self._confirm(dialog, runDeferred=False)

        assert len(scheduled) == 1
        assert os.path.exists(path)
        scheduled[0]()
        assert not os.path.exists(path)

    def test_a_theme_that_is_loaded_is_deleted_all_the_same(self, tmp_path):
        dialog, path = self._dialog(tmp_path)
        dialog.openLayerPaths = MagicMock(return_value={os.path.normcase(_uniform(path))})

        self._confirm(dialog)

        dialog.parent.syncAuxiliaryThemes.assert_called_once_with([_uniform(path)], load=False)
        assert not os.path.exists(path)

    def test_declining_the_confirmation_keeps_everything(self, tmp_path):
        dialog, path = self._dialog(tmp_path)

        self._confirm(dialog, accepted=False)

        assert os.path.exists(path)
        dialog.parent.syncAuxiliaryThemes.assert_not_called()

    def test_deleting_with_no_row_selected_only_warns(self, tmp_path):
        dialog, path = self._dialog(tmp_path)
        dialog.tbAuxiliary._current = -1

        self._confirm(dialog)

        assert os.path.exists(path)
        assert dialog.messageBar.pushMessage.call_args[0][2] == 1


class TestAcceptSendsBothSelections:
    def test_auxiliary_themes_are_applied_before_the_input_layers(self, tmp_path):
        """applyInputLayerSelection ends in updateMetadata, which must see the final tree."""
        from QGISRed.ui.project.qgisred_layermanagement_dialog import QGISRedLayerManagementDialog

        _touchTheme(_auxFolder(tmp_path), "Net_DemandBuilder_Sectors_Barrios")
        dialog = _makeDialog(tmp_path)
        dialog.crs = dialog.originalCrs = MagicMock()
        with patch(_DIALOG_MOD + ".QTableWidgetItem", _FakeItem):
            dialog.fillAuxiliaryTable()

        order = []
        dialog.parent.applyAuxiliaryLayerSelection.side_effect = lambda *a: order.append("aux")
        dialog.parent.applyInputLayerSelection.side_effect = lambda *a: order.append("inputs")

        base = QGISRedLayerManagementDialog.__mro__[1]
        original = getattr(base, "accept", None)
        base.accept = MagicMock()
        try:
            dialog.accept()
        finally:
            if original is None:
                del base.accept
            else:
                base.accept = original

        assert order == ["aux", "inputs"]
        selected, managed = dialog.parent.applyAuxiliaryLayerSelection.call_args[0]
        assert managed == dialog.auxiliaryRowPaths()
        assert selected == []


class TestOpenDemandBuilderLayers:
    """After a Demand Builder run, only what the DLL reported is opened.

    The DLL names every layer it created or updated after the "^" of its result, so there
    is nothing to discover by listing the folder — and listing it would reopen the user's
    own themes, including the ones they had just unloaded from the layer manager.
    """

    def _makeSection(self, tmp_path, reported, monkeypatch):
        from QGISRed.sections import layer_management_section as mod
        from QGISRed.sections.layer_management_section import LayerManagementSection

        folder = tmp_path / "Auxiliary Layers" / "DemandBuilder"
        folder.mkdir(parents=True)
        for name in ("Net_DemandBuilder_Sectors.shp", "Net_DemandBuilder_Sectors_Mine.shp"):
            (folder / name).write_text("")

        section = object.__new__(LayerManagementSection)
        section.ProjectDirectory = str(tmp_path)
        section.NetworkName = "Net"
        section.iface = MagicMock()
        section._demandBuilderExtraPaths = [str(folder / name) for name in reported]
        section.getDemandBuilderGroup = MagicMock()
        section._applyDemandBuilderStyle = MagicMock()

        # Nothing is ever already open in these tests, so every path takes the
        # "open a fresh layer" branch.
        utils = MagicMock()
        utils._tryReloadExistingLayer.return_value = None
        monkeypatch.setattr(mod, "QGISRedLayerUtils", MagicMock(return_value=utils))

        identifiers = MagicMock()
        identifiers.getAuxiliaryThemeName.side_effect = lambda base, net: base
        monkeypatch.setattr(mod, "QGISRedIdentifierUtils", MagicMock(return_value=identifiers))

        opened = []

        def makeLayer(path, name, provider):
            layer = MagicMock()
            layer.isValid.return_value = True
            opened.append(os.path.basename(path))
            return layer

        monkeypatch.setattr(mod, "QgsVectorLayer", makeLayer)
        monkeypatch.setattr(mod, "QgsProject", MagicMock())
        monkeypatch.setattr(mod, "QgsLayerTreeLayer", MagicMock())

        return section, opened, folder

    def test_only_the_reported_layer_is_opened(self, tmp_path, monkeypatch):
        section, opened, _ = self._makeSection(
            tmp_path, ["Net_DemandBuilder_Sectors.shp"], monkeypatch)

        section.openDemandBuilderLayers()

        assert opened == ["Net_DemandBuilder_Sectors.shp"]

    def test_a_theme_the_user_had_unloaded_stays_unloaded(self, tmp_path, monkeypatch):
        """It sits in the same folder as what the DLL wrote, which is why sweeping the
        folder used to bring it back."""
        section, opened, _ = self._makeSection(
            tmp_path, ["Net_DemandBuilder_Sectors.shp"], monkeypatch)

        section.openDemandBuilderLayers()

        assert "Net_DemandBuilder_Sectors_Mine.shp" not in opened

    def test_every_reported_layer_is_opened(self, tmp_path, monkeypatch):
        section, opened, _ = self._makeSection(
            tmp_path,
            ["Net_DemandBuilder_Sectors.shp", "Net_DemandBuilder_Sectors_Mine.shp"],
            monkeypatch)

        section.openDemandBuilderLayers()

        assert sorted(opened) == [
            "Net_DemandBuilder_Sectors.shp", "Net_DemandBuilder_Sectors_Mine.shp"]

    def test_nothing_reported_opens_nothing(self, tmp_path, monkeypatch):
        section, opened, _ = self._makeSection(tmp_path, [], monkeypatch)

        section.openDemandBuilderLayers()

        assert opened == []

    def test_nothing_reported_leaves_the_group_alone(self, tmp_path, monkeypatch):
        """Creating it would show an empty Demand Builder group after a run that wrote
        nothing into it."""
        section, _opened, _ = self._makeSection(tmp_path, [], monkeypatch)

        section.openDemandBuilderLayers()

        section.getDemandBuilderGroup.assert_not_called()

    def test_a_reported_path_that_is_not_there_is_skipped(self, tmp_path, monkeypatch):
        section, opened, folder = self._makeSection(tmp_path, [], monkeypatch)
        section._demandBuilderExtraPaths = [str(folder / "Net_DemandBuilder_Gone.shp")]

        section.openDemandBuilderLayers()

        assert opened == []

    def test_the_reported_list_is_spent_once(self, tmp_path, monkeypatch):
        """Otherwise the next unrelated run would reopen this one's layers."""
        section, opened, _ = self._makeSection(
            tmp_path, ["Net_DemandBuilder_Sectors.shp"], monkeypatch)

        section.openDemandBuilderLayers()
        section.openDemandBuilderLayers()

        assert opened == ["Net_DemandBuilder_Sectors.shp"]
