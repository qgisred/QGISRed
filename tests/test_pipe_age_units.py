# -*- coding: utf-8 -*-
"""The Pipe Age thematic map reads its ages in years in the user's language.

English "yrs", Spanish "años", French "ans" and Portuguese "anos": in the legend classes,
in the map tip, and in the classes the Legend Editor creates (through the units CSV).
Reopening the project in another language swaps the unit already written.
"""
import csv
import os

import pytest

import QGISRed.tools.utils.qgisred_field_utils as fieldUtilsModule
import QGISRed.tools.utils.qgisred_styling_utils as stylingModule
from QGISRed.tools.utils.qgisred_field_utils import QGISRedFieldUtils
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils

_UNITS_CSV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "defaults",
                          "qgisred_properties_units_decimals.csv")
_YEARS = {"es": "años", "fr": "ans", "pt": "anos", "en": "yrs"}


def _speaking(monkeypatch, language):
    class Translator:
        @staticmethod
        def translate(context, text):
            return _YEARS[language] if (context, text) == ("UnitAbbreviations", "yrs") else text

    monkeypatch.setattr(fieldUtilsModule, "QCoreApplication", Translator)


class FakeRule:
    def __init__(self, label):
        self._label = label

    def label(self):
        return self._label

    def setLabel(self, label):
        self._label = label


class FakeRoot:
    def __init__(self, labels):
        self.rules = [FakeRule(label) for label in labels]

    def children(self):
        return self.rules


class FakeRuleRenderer:
    def __init__(self, labels):
        self.root = FakeRoot(labels)

    def rootRule(self):
        return self.root


class FakeCategory:
    def __init__(self, label):
        self._label = label

    def label(self):
        return self._label


class FakeCategorizedRenderer:
    def __init__(self, labels):
        self.items = [FakeCategory(label) for label in labels]

    def categories(self):
        return list(self.items)

    def updateCategoryLabel(self, index, label):
        self.items[index] = FakeCategory(label)


class FakeGraduatedRenderer:
    pass


class FakeAgeLayer:
    def __init__(self, renderer, mapTip):
        self._renderer = renderer
        self._mapTip = mapTip

    def renderer(self):
        return self._renderer

    def mapTipTemplate(self):
        return self._mapTip

    def setMapTipTemplate(self, mapTip):
        self._mapTip = mapTip


@pytest.fixture(autouse=True)
def fakeRenderers(monkeypatch):
    monkeypatch.setattr(stylingModule, "QgsRuleBasedRenderer", FakeRuleRenderer)
    monkeypatch.setattr(stylingModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)
    monkeypatch.setattr(stylingModule, "QgsGraduatedSymbolRenderer", FakeGraduatedRenderer)


SHIPPED_LABELS = ["< 10 yrs", "10 - 24 yrs", "25 - 49 yrs", "50 - 74 yrs", "75 - 100 yrs", ">= 100 yrs"]


class TestTheAgeUnit:
    @pytest.mark.parametrize("language", sorted(_YEARS))
    def test_years_are_written_in_each_language(self, monkeypatch, language):
        _speaking(monkeypatch, language)
        assert QGISRedFieldUtils.ageUnit() == _YEARS[language]

    def test_symbols_are_not_translated(self, monkeypatch):
        _speaking(monkeypatch, "es")
        assert QGISRedFieldUtils.translateUnitAbbreviation("m") == "m"

    def test_the_units_file_measures_every_age_in_yrs(self):
        with open(_UNITS_CSV, encoding="utf-8-sig") as handle:
            ageRows = [row for row in csv.reader(handle) if len(row) > 7 and row[1] == "Age" and row[3] == "Years"]
        assert ageRows and all(row[4] == "yrs" and row[7] == "yrs" for row in ageRows)


class TestThePipeAgeMap:
    def test_the_shipped_classes_read_in_spanish(self, monkeypatch):
        _speaking(monkeypatch, "es")
        layer = FakeAgeLayer(FakeRuleRenderer(SHIPPED_LABELS), '[%"Age"%] yr')
        QGISRedStylingUtils.labelAgesWithUnit(layer)
        assert [rule.label() for rule in layer.renderer().rootRule().children()] == [
            "< 10  años", "10 - 24  años", "25 - 49  años", "50 - 74  años", "75 - 100  años", ">= 100  años"]
        assert layer.mapTipTemplate() == '[%"Age"%] años'

    def test_reopening_in_another_language_swaps_the_unit(self, monkeypatch):
        _speaking(monkeypatch, "es")
        layer = FakeAgeLayer(FakeRuleRenderer(SHIPPED_LABELS), '[%"Age"%] yr')
        QGISRedStylingUtils.labelAgesWithUnit(layer)
        _speaking(monkeypatch, "fr")
        QGISRedStylingUtils.labelAgesWithUnit(layer)
        assert layer.renderer().rootRule().children()[1].label() == "10 - 24  ans"
        assert layer.mapTipTemplate() == '[%"Age"%] ans'

    def test_a_categorized_age_map_labels_each_age(self, monkeypatch):
        _speaking(monkeypatch, "pt")
        layer = FakeAgeLayer(FakeCategorizedRenderer(["12 yrs", "30", "NULL"]), "")
        QGISRedStylingUtils.labelAgesWithUnit(layer)
        assert [category.label() for category in layer.renderer().categories()] == ["12  anos", "30  anos", "NULL"]
