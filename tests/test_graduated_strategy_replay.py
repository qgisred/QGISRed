# -*- coding: utf-8 -*-
"""Replaying an "Automatic" legend strategy classifies the data as the legend editor shows it.

A style can carry a strategy (Pretty Breaks over N classes); on every load the classes are
rebuilt from the layer's values. The editor labels such legends "< b1", "b1 < b2", "> bn"
with open first and last classes, and the replay has to produce the same thing, or a value
of a later time step beyond the breaks would fall into the grey "no value" rule.
"""
import pytest

from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils
from QGISRed.tests.conftest import REAL_QGIS


class TestRangeLabels:
    def test_first_and_last_classes_are_open(self):
        assert QGISRedStylingUtils.rangeLabels([5, 10, 20]) == ["< 5", "5 < 10", "10 < 20", "> 20"]

    def test_three_decimals_are_enough_when_they_tell_the_breaks_apart(self):
        assert QGISRedStylingUtils.rangeLabels([0.25, 0.5]) == ["< 0.25", "0.25 < 0.5", "> 0.5"]

    def test_more_decimals_when_breaks_sit_closer_than_a_thousandth(self):
        # Reaction rates and chemical concentrations break below 0.001.
        assert QGISRedStylingUtils.rangeLabels([0.0002, 0.0004]) == ["< 0.0002", "0.0002 < 0.0004", "> 0.0004"]

    def test_trailing_zeros_and_negative_zero_are_trimmed(self):
        assert QGISRedStylingUtils.formatBreak(10.0, 3) == "10"
        assert QGISRedStylingUtils.formatBreak(-0.0001, 3) == "0"

    def test_no_breaks_gives_no_labels(self):
        assert QGISRedStylingUtils.rangeLabels([]) == []


def _pointLayer(field, values):
    from qgis.core import QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY

    layer = QgsVectorLayer("Point?crs=EPSG:3857&field=%s:double" % field, "nodes", "memory")
    provider = layer.dataProvider()
    features = []
    for index, value in enumerate(values):
        feature = QgsFeature(layer.fields())
        feature.setAttribute(field, value)
        feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
        features.append(feature)
    provider.addFeatures(features)
    layer.updateExtents()
    return layer


def _prettyStrategy(field):
    return {
        "schema": "qgisred.legendStrategy.v2",
        "mode": "graduated",
        "field": field,
        "parts": ["intervals"],
        "intervals": {"classificationMode": "Pretty", "classes": 5},
    }


@pytest.mark.skipif(not REAL_QGIS, reason="classifies with the real QGIS classification methods")
class TestPrettyReplayOnRealQgis:
    def test_classes_come_from_the_data_with_open_ends_and_editor_labels(self):
        from qgis.core import QgsGraduatedSymbolRenderer

        layer = _pointLayer("Head", [12.5, 18.0, 23.0, 31.0, 44.0, 52.0, 67.0])

        QGISRedStylingUtils().applyLegendStrategy(layer, _prettyStrategy("Head"))

        renderer = layer.renderer()
        assert isinstance(renderer, QgsGraduatedSymbolRenderer)
        ranges = renderer.ranges()
        assert len(ranges) >= 2
        assert ranges[0].lowerValue() == -1e10
        assert ranges[-1].upperValue() == 1e10
        breaks = [classRange.upperValue() for classRange in ranges[:-1]]
        assert breaks == sorted(breaks)
        assert ranges[0].label() == "< " + QGISRedStylingUtils.formatBreak(breaks[0], 3)
        assert ranges[-1].label() == "> " + QGISRedStylingUtils.formatBreak(breaks[-1], 3)
        for classRange, lower, upper in zip(ranges[1:-1], breaks, breaks[1:]):
            assert classRange.label() == "%s < %s" % (
                QGISRedStylingUtils.formatBreak(lower, 3), QGISRedStylingUtils.formatBreak(upper, 3))

    def test_an_expression_is_classified_like_a_column(self):
        layer = _pointLayer("Flow", [-30.0, -12.0, 4.0, 15.0, 27.0, 41.0])

        QGISRedStylingUtils().applyLegendStrategy(layer, _prettyStrategy("Flow"), field="abs(Flow)")

        renderer = layer.renderer()
        assert renderer.classAttribute() == "abs(Flow)"
        assert renderer.ranges()[0].lowerValue() == -1e10

    def test_the_breaks_come_from_the_sample_expression_while_the_field_is_classified(self):
        from qgis.core import QgsFeature, QgsGeometry, QgsPointXY, QgsVectorLayer

        layer = QgsVectorLayer("Point?crs=EPSG:3857&field=Type:string&field=Demand:double", "nodes", "memory")
        features = []
        for index, (nodeType, demand) in enumerate(
                [("JUNCTION", -3.0), ("JUNCTION", 4.0), ("JUNCTION", 9.0), ("JUNCTION", 14.0), ("TANK", 950.0)]):
            feature = QgsFeature(layer.fields())
            feature.setAttributes([nodeType, demand])
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(index, 0)))
            features.append(feature)
        layer.dataProvider().addFeatures(features)
        strategy = _prettyStrategy("Demand")
        strategy["intervals"]["sampleField"] = "if(\"Type\" in ('TANK'), NULL, abs(\"Demand\"))"

        QGISRedStylingUtils().applyLegendStrategy(layer, strategy)

        renderer = layer.renderer()
        assert renderer.classAttribute() == "Demand"
        assert renderer.ranges()[-1].label() == "> " + QGISRedStylingUtils.formatBreak(
            renderer.ranges()[-2].upperValue(), 3)
        assert renderer.ranges()[-2].upperValue() <= 15

    def test_the_class_below_zero_of_the_loaded_style_is_kept_in_front(self):
        from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange, QgsMarkerSymbol

        layer = _pointLayer("Demand", [-3.0, 4.0, 9.0, 14.0, 21.0, 27.0])
        negative = QgsMarkerSymbol.createSimple({"size": "2.5", "color": "255,255,255,255"})
        regular = QgsMarkerSymbol.createSimple({"size": "2"})
        layer.setRenderer(QgsGraduatedSymbolRenderer("Demand", [
            QgsRendererRange(-1e10, -0.005, negative, "< 0"), QgsRendererRange(0, 1, regular, "0 - 1")]))
        strategy = _prettyStrategy("Demand")
        strategy["intervals"]["negativeClass"] = True

        QGISRedStylingUtils().applyLegendStrategy(layer, strategy)

        ranges = layer.renderer().ranges()
        assert (ranges[0].lowerValue(), ranges[0].upperValue(), ranges[0].label()) == (-1e10, -0.005, "< 0")
        assert ranges[0].symbol().size() == 2.5
        assert ranges[1].lowerValue() == -0.005 and ranges[1].label().startswith("< ")
        assert all(classRange.symbol().size() == 2 for classRange in ranges[1:])
        assert ranges[-1].upperValue() == 1e10

    def test_a_single_value_keeps_one_class_named_after_it(self):
        layer = _pointLayer("Demand", [0.0, 0.0, 0.0])

        QGISRedStylingUtils().applyLegendStrategy(layer, _prettyStrategy("Demand"))

        ranges = layer.renderer().ranges()
        assert len(ranges) == 1
        assert (ranges[0].lowerValue(), ranges[0].upperValue()) == (-1e10, 1e10)
        assert ranges[0].label() == "0"


@pytest.mark.skipif(not REAL_QGIS, reason="converts a real graduated renderer into rules")
class TestNullRuleTemplateOnRealQgis:
    def test_the_grey_rule_copies_the_last_class_not_the_first(self):
        from qgis.core import QgsGraduatedSymbolRenderer, QgsRendererRange, QgsMarkerSymbol, QgsRuleBasedRenderer
        from QGISRed.tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL

        layer = _pointLayer("Pressure", [-3.0, 20.0])
        negative = QgsMarkerSymbol.createSimple({"size": "2.5"})
        regular = QgsMarkerSymbol.createSimple({"size": "2"})
        renderer = QgsGraduatedSymbolRenderer("Pressure", [
            QgsRendererRange(-10, 0, negative, "< 0"), QgsRendererRange(0, 200, regular, "> 0")])
        layer.setRenderer(renderer)

        QGISRedStylingUtils().applyNullStyle(layer)

        rules = layer.renderer().rootRule().children()
        assert isinstance(layer.renderer(), QgsRuleBasedRenderer)
        nullRule = next(rule for rule in rules if rule.label() == _NULL_RULE_LABEL)
        assert nullRule.symbol().size() == 2
