# -*- coding: utf-8 -*-
"""translateMapTip: the element-type word the shipped styles hardcode at the
start of a layer's map tip (e.g. "Junction [%...%]") must be localized, the
same way translateRendererLabels already localizes legend labels. Meters and
Valves instead pull their type off a feature attribute (MeterType/ValveType) --
that raw code must come back wrapped in a translated CASE expression."""
import os
import xml.etree.ElementTree as ElementTree

import pytest

import QGISRed.tools.utils.qgisred_styling_utils as stylingModule
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

from .conftest import REAL_QGIS

_TRANSLATIONS = {
    "Junction": "Unión",
    "Isolation Valve": "Válvula de seccionamiento",
    "Service Connection": "Acometida",
    "Multiple Demand": "Demanda Múltiple",
    "Valve": "Válvula",
}

_STYLES_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "defaults", "layerStyles")
_LEGACY_METER_TIP = (
    "[[% coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type')) %]]"
    " [% coalesce(attribute($currentfeature,'MeterID'), attribute($currentfeature,'Id')) %]"
)
_LEGACY_VALVE_TIP = (
    "[% coalesce(attribute($currentfeature,'ValveType'), attribute($currentfeature,'Type')) %]"
    " [% coalesce(attribute($currentfeature,'ValveID'), attribute($currentfeature,'Id')) %]"
)
_LEGACY_DEMAND_TIP = (
    "Mult_Demand [% coalesce(attribute($currentfeature,'BaseDem'), attribute($currentfeature,'BaseValue')) %] ..."
)


def _shippedStyle(name):
    return ElementTree.parse(os.path.join(_STYLES_FOLDER, name + ".qml.bak")).getroot()


def _shippedMapTip(name):
    return _shippedStyle(name).find("mapTip").text


def _shippedLabelExpression(name):
    return _shippedStyle(name).find("labeling/settings/text-style").get("fieldName")


class FakeLayer:
    def __init__(self, template):
        self._template = template

    def mapTipTemplate(self):
        return self._template

    def setMapTipTemplate(self, template):
        self._template = template


class FakeLabelSettings:
    def __init__(self, fieldName):
        self.fieldName = fieldName


class FakeLabeling:
    def __init__(self, settings):
        self._settings = settings

    def type(self):
        return "simple"

    def settings(self):
        # Like QGIS, hands out a copy: a change only counts once it is set back on the layer
        return FakeLabelSettings(self._settings.fieldName)


class FakeLabeledLayer:
    def __init__(self, fieldName):
        self._labeling = FakeLabeling(FakeLabelSettings(fieldName))

    def labeling(self):
        return self._labeling

    def setLabeling(self, labeling):
        self._labeling = labeling


@pytest.fixture
def untranslatedTypeNames(monkeypatch):
    for getter in ("getMeterTypeName", "getValveTypeAbbreviation", "getSourceTypeName"):
        monkeypatch.setattr(stylingModule, getter, lambda code: code)


def _utils():
    utils = QGISRedStylingUtils("", "")
    utils.tr = lambda message: _TRANSLATIONS.get(message, message)
    return utils


class TestTranslateMapTip:
    def test_translates_the_leading_element_word(self):
        layer = FakeLayer("Junction [% coalesce(attribute($currentfeature,'JunctionID'), attribute($currentfeature,'Id')) %]")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate().startswith("Unión [%")

    def test_only_the_leading_word_is_replaced_the_rest_survives_untouched(self):
        layer = FakeLayer("Junction [% \"Id\" %]")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == "Unión [% \"Id\" %]"

    def test_prefers_the_longer_match_isolation_valve_over_a_bare_valve(self):
        layer = FakeLayer("Isolation Valve [% \"Id\" %]")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == "Válvula de seccionamiento [% \"Id\" %]"

    def test_translates_service_connection_no_longer_the_sconnec_abbreviation(self):
        layer = FakeLayer("Service Connection [% \"Id\" %]")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == "Acometida [% \"Id\" %]"

    def test_a_custom_map_tip_with_no_known_leading_word_is_left_alone(self):
        layer = FakeLayer("[% \"Descrip\" %]")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == "[% \"Descrip\" %]"

    def test_an_empty_map_tip_is_a_no_op(self):
        layer = FakeLayer("")
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == ""

    def test_no_translation_available_leaves_the_template_unchanged(self):
        layer = FakeLayer("Tank [% \"Id\" %]")
        utils = QGISRedStylingUtils("", "")
        utils.tr = lambda message: message
        utils.translateMapTip(layer)
        assert layer.mapTipTemplate() == "Tank [% \"Id\" %]"

    def test_wraps_the_meter_type_attribute_in_a_translated_case(self, monkeypatch):
        monkeypatch.setattr(
            stylingModule, "getMeterTypeName",
            lambda code: {"Manometer": "Manómetro"}.get(code, code),
        )
        layer = FakeLayer(_shippedMapTip("Meters"))
        utils = QGISRedStylingUtils("", "")
        utils.tr = lambda message: message
        utils.translateMapTip(layer)
        result = layer.mapTipTemplate()
        assert result.startswith("[% with_variable(")
        assert "WHEN @qgisred_type = 'Manometer' THEN 'Manómetro'" in result
        # The id half of the template, outside the type expression, survives untouched.
        assert "coalesce(attribute($currentfeature,'MeterID'), attribute($currentfeature,'Id'))" in result

    def test_wraps_the_valve_type_attribute_using_the_shared_valve_type_abbreviations(self, monkeypatch):
        # The map tip shows the localized abbreviation (siglas), same choice as the
        # Element Explorer's Type column -- not the long descriptive name.
        monkeypatch.setattr(
            stylingModule, "getValveTypeAbbreviation",
            lambda code: {"PBV": "VRC"}.get(code, code),
        )
        layer = FakeLayer(_shippedMapTip("Valves"))
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate().startswith("Válvula [% with_variable(")
        assert "WHEN @qgisred_type = 'PBV' THEN 'VRC'" in layer.mapTipTemplate()

    def test_the_multiple_demand_word_is_translated(self):
        layer = FakeLayer(_shippedMapTip("Demands"))
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate().startswith("Demanda Múltiple [% coalesce(")

    def test_the_meter_type_is_shown_without_square_brackets(self):
        assert "[[%" not in _shippedMapTip("Meters") and "%]]" not in _shippedMapTip("Meters")

    @pytest.mark.parametrize("legacyTip, shippedStyle", [
        (_LEGACY_METER_TIP, "Meters"),
        (_LEGACY_VALVE_TIP, "Valves"),
        (_LEGACY_DEMAND_TIP, "Demands"),
    ])
    def test_a_style_saved_with_an_old_map_tip_shows_the_same_as_the_shipped_one(
        self, untranslatedTypeNames, legacyTip, shippedStyle
    ):
        legacyLayer = FakeLayer(legacyTip)
        shippedLayer = FakeLayer(_shippedMapTip(shippedStyle))
        _utils().translateMapTip(legacyLayer)
        _utils().translateMapTip(shippedLayer)
        assert legacyLayer.mapTipTemplate() == shippedLayer.mapTipTemplate()

    @pytest.mark.parametrize("shippedStyle", ["Meters", "Valves", "Sources", "Demands"])
    def test_a_map_tip_already_translated_is_left_as_it_is(
        self, untranslatedTypeNames, shippedStyle
    ):
        layer = FakeLayer(_shippedMapTip(shippedStyle))
        _utils().translateMapTip(layer)
        translatedOnce = layer.mapTipTemplate()
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate() == translatedOnce

    def test_an_unrecognized_type_code_falls_back_to_the_raw_value_at_hover_time(self, monkeypatch):
        monkeypatch.setattr(stylingModule, "getMeterTypeName", lambda code: code)
        template = "[% coalesce(attribute($currentfeature,'MeterType'),attribute($currentfeature,'Type')) %] [% \"Id\" %]"
        layer = FakeLayer(template)
        _utils().translateMapTip(layer)
        assert layer.mapTipTemplate().rstrip().endswith("ELSE @qgisred_type END) %] [% \"Id\" %]")

    def test_wraps_the_source_type_attribute_and_translates_the_leading_word(self, monkeypatch):
        monkeypatch.setattr(
            stylingModule, "getSourceTypeName",
            lambda code: {
                "CONCEN": "Concentración",
                "MASS": "Booster de masa fija",
            }.get(code, code),
        )
        template = (
            "Source [% coalesce(attribute($currentfeature,'SourceType'), attribute($currentfeature,'Type')) %]"
            " [% coalesce(attribute($currentfeature,'SourceQual'), attribute($currentfeature,'BaseValue')) %]"
        )
        layer = FakeLayer(template)
        utils = QGISRedStylingUtils("", "")
        utils.tr = lambda message: {"Source": "Fuente"}.get(message, message)
        utils.translateMapTip(layer)
        result = layer.mapTipTemplate()
        assert result.startswith("Fuente [%")
        assert "WHEN @qgisred_type = 'CONCEN' THEN 'Concentración'" in result
        assert "WHEN @qgisred_type = 'MASS' THEN 'Booster de masa fija'" in result
        # The quality-value half of the template, outside the type expression, survives untouched.
        assert "coalesce(attribute($currentfeature,'SourceQual'), attribute($currentfeature,'BaseValue'))" in result

    @pytest.mark.skipif(not REAL_QGIS, reason="needs a real QgsExpression parser to catch CASE syntax errors")
    def test_the_generated_case_expression_actually_parses_in_qgis(self):
        # Regression test: an earlier version wrote "CASE @var WHEN 'x' THEN ...", which
        # QGIS expressions do not support (only "CASE WHEN <condition> THEN ..." exists) --
        # QgsExpression silently failed to evaluate it and the map tip showed the raw,
        # unevaluated expression text instead of a translated label.
        from qgis.core import QgsExpression

        templates = [_shippedMapTip("Meters"), _shippedMapTip("Valves"), _shippedMapTip("Sources")]
        utils = QGISRedStylingUtils("", "")
        utils.tr = lambda message: message
        for template in templates:
            layer = FakeLayer(template)
            utils.translateMapTip(layer)
            # Pull out just the with_variable(...) expression between the [% %] markers.
            inner = layer.mapTipTemplate().split("[% ", 1)[1].split(" %]", 1)[0]
            expr = QgsExpression(inner)
            assert not expr.hasParserError(), (inner, expr.parserErrorString())


class TestTranslateValveTypeLabel:
    def test_the_label_shows_the_abbreviation_of_the_current_language(self, monkeypatch):
        monkeypatch.setattr(stylingModule, "getValveTypeAbbreviation", lambda code: {"PRV": "VRP"}.get(code, code))
        monkeypatch.setattr(stylingModule, "QgsVectorLayerSimpleLabeling", FakeLabeling)
        layer = FakeLabeledLayer(_shippedLabelExpression("Valves"))
        _utils().translateValveTypeLabel(layer)
        expression = layer.labeling().settings().fieldName
        assert expression.startswith("concat(with_variable('qgisred_type', coalesce(")
        assert "WHEN @qgisred_type = 'PRV' THEN 'VRP'" in expression

    def test_a_label_of_another_layer_is_left_alone(self, monkeypatch):
        monkeypatch.setattr(stylingModule, "QgsVectorLayerSimpleLabeling", FakeLabeling)
        layer = FakeLabeledLayer(_shippedLabelExpression("Pumps"))
        _utils().translateValveTypeLabel(layer)
        assert layer.labeling().settings().fieldName == _shippedLabelExpression("Pumps")

    @pytest.mark.skipif(not REAL_QGIS, reason="needs the real style loader and expression engine")
    def test_the_shipped_valve_label_evaluates_to_the_translated_abbreviation(self, monkeypatch):
        from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils, QgsFeature, QgsVectorLayer

        monkeypatch.setattr(stylingModule, "getValveTypeAbbreviation", lambda code: {"PRV": "VRP"}.get(code, code))
        layer = QgsVectorLayer("LineString?field=Id:string&field=Type:string", "Valves", "memory")
        layer.loadNamedStyle(os.path.join(_STYLES_FOLDER, "Valves.qml.bak"))
        _utils().translateValveTypeLabel(layer)
        feature = QgsFeature(layer.fields())
        feature.setAttributes(["V1", "PRV"])
        context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
        context.setFeature(feature)
        expression = QgsExpression(layer.labeling().settings().fieldName)
        assert expression.evaluate(context) == "VRP V1"
