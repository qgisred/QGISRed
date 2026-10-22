# -*- coding: utf-8 -*-
"""A project saved in one language and reopened in another: the map tips, the result map tips and
the "other values" legend class are recognised by what they are, not by the text of the language
they were saved in, and the project is resolved before anything is renamed."""
from unittest.mock import MagicMock, patch

import pytest

import QGISRed.tools.utils.qgisred_styling_utils as stylingModule
import QGISRed.ui.analysis.qgisred_results_data as resultsData
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

from .test_maptip_translation import FakeLayer
from .test_post_qgz_open import _QGS_PROJECT, _STYLING_CLS, _make_section

_SPANISH = {"Junction": "Unión", "Isolation Valve": "Válvula de seccionamiento", "Valve": "Válvula",
            "Other Values": "Otros valores"}
_FRENCH = {"Junction": "Nœud de demande", "Isolation Valve": "Vanne d’isolement", "Valve": "Vanne",
           "Other Values": "Autres valeurs"}


class FakeTranslator:
    def __init__(self, texts):
        self._texts = texts

    def translate(self, context, source):
        return self._texts.get(source, "")


@pytest.fixture
def shippedLanguages(monkeypatch):
    monkeypatch.setattr(stylingModule, "_shippedTranslators", [FakeTranslator(_SPANISH), FakeTranslator(_FRENCH)])


def _stylingIn(texts):
    utils = QGISRedStylingUtils("", "")
    utils.tr = lambda message: texts.get(message, message)
    return utils


class TestAllLanguageTexts:
    def test_gives_the_text_in_every_shipped_language_and_the_source(self, shippedLanguages):
        assert stylingModule.allLanguageTexts("ctx", "Other Values") == {
            "Other Values", "Otros valores", "Autres valeurs"}

    def test_a_language_without_the_text_adds_nothing(self, shippedLanguages):
        assert stylingModule.allLanguageTexts("ctx", "Pipe") == {"Pipe"}

    def test_other_values_texts_is_the_other_values_class_in_every_language(self, shippedLanguages):
        assert "Otros valores" in stylingModule.otherValuesTexts()


class TestMapTipSavedInAnotherLanguage:
    def test_the_leading_word_goes_from_spanish_to_french(self, shippedLanguages):
        layer = FakeLayer("Unión [% \"Id\" %]")
        _stylingIn(_FRENCH).translateMapTip(layer)
        assert layer.mapTipTemplate() == "Nœud de demande [% \"Id\" %]"

    def test_the_longer_word_wins_over_the_bare_valve(self, shippedLanguages):
        layer = FakeLayer("Válvula de seccionamiento [% \"Id\" %]")
        _stylingIn(_FRENCH).translateMapTip(layer)
        assert layer.mapTipTemplate() == "Vanne d’isolement [% \"Id\" %]"

    def test_the_active_language_leaves_the_tip_alone(self, shippedLanguages):
        layer = FakeLayer("Unión [% \"Id\" %]")
        _stylingIn(_SPANISH).translateMapTip(layer)
        assert layer.mapTipTemplate() == "Unión [% \"Id\" %]"

    def test_an_already_wrapped_type_code_is_wrapped_again_in_the_active_language(self):
        expression = "coalesce(attribute($currentfeature,'ValveType'), attribute($currentfeature,'Type'))"
        wrapped = QGISRedStylingUtils._wrapTypeCode("Valve [% " + expression + " %]", expression, {"PRV": "VRP"})
        rewrapped = QGISRedStylingUtils._wrapTypeCode(wrapped, expression, {"PRV": "PRV"})
        assert rewrapped == QGISRedStylingUtils._wrapTypeCode("Valve [% " + expression + " %]", expression,
                                                              {"PRV": "PRV"})


class TestResultMapTipSavedInAnotherLanguage:
    _SAVED = ("<b>Demanda</b><br>[% (CASE WHEN \"NodeType\" = 'JUNCTION' THEN 'Unión' "
              "WHEN \"NodeType\" = 'TANK' THEN 'Depósito' ELSE \"NodeType\" END) || ' ' || \"NodeID\" %]"
              "<br>Máx [% \"Demand\" %] lps")

    def _translate(self, layer, words):
        sources = {"Demand": "Demand", "Junction": "Junction", "Tank": "Tank", "Max": "Max"}
        with patch.object(resultsData, "_translateResultsWord", side_effect=lambda s: words.get(s, s)), \
                patch.object(resultsData, "_resultsWordSpellings",
                             side_effect=lambda s: {s, sources.get(s, s), "Máx"}):
            resultsData.retranslateResultMapTip(layer, "Demand")

    def test_the_variable_the_element_types_and_the_statistic_prefix_follow_the_language(self):
        layer = FakeLayer(self._SAVED)
        self._translate(layer, {"Demand": "Demande", "Junction": "Nœud", "Tank": "Réservoir", "Max": "Max"})
        assert layer.mapTipTemplate() == (
            "<b>Demande</b><br>[% (CASE WHEN \"NodeType\" = 'JUNCTION' THEN 'Nœud' "
            "WHEN \"NodeType\" = 'TANK' THEN 'Réservoir' ELSE \"NodeType\" END) || ' ' || \"NodeID\" %]"
            "<br>Max [% \"Demand\" %] lps")

    def test_the_expressions_are_left_as_they_are(self):
        layer = FakeLayer(self._SAVED)
        self._translate(layer, {"Demand": "Demande"})
        assert "\"NodeType\" END) || ' ' || \"NodeID\" %]" in layer.mapTipTemplate()

    def test_a_layer_without_a_known_variable_is_left_alone(self):
        layer = FakeLayer(self._SAVED)
        resultsData.retranslateResultMapTip(layer, "Nonexistent")
        assert layer.mapTipTemplate() == self._SAVED


class TestPostQgzOpenResolvesTheProject:
    def test_the_default_project_is_resolved_from_the_layers_first(self):
        section = _make_section(project_dir="Temporal Folder")
        section.defineCurrentProject = MagicMock()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        with patch(_STYLING_CLS), patch(_QGS_PROJECT):
            section._post_qgz_open({"inputs_to_restyle": [], "results_no_id": False, "results_with_id": []})

        section.defineCurrentProject.assert_called_once()

    def test_a_project_already_known_is_not_resolved_again(self):
        section = _make_section(project_dir="C:/proj")
        section.defineCurrentProject = MagicMock()
        section._writePluginVersionToProject = MagicMock()
        section._migrateLayersToSubfolders = MagicMock()
        section.removeOldResultLayers = MagicMock()

        with patch(_STYLING_CLS), patch(_QGS_PROJECT):
            section._post_qgz_open({"inputs_to_restyle": [], "results_no_id": False, "results_with_id": []})

        section.defineCurrentProject.assert_not_called()
