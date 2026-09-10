# -*- coding: utf-8 -*-
"""The "Proportional to Value" size mode of the legend editor.

The map draws every feature through one scale_polynomial() expression; the Size
column has to show, per class, what that expression yields for the value the
class stands for (a range midpoint on graduated legends, the category itself on
categorized ones). Both legend types must write and drop that expression on Apply.
"""
import pytest

import QGISRed.ui.project.qgisred_legends_dialog as legendsModule
from QGISRed.ui.project.qgisred_legends_dialog import (
    PROPORTIONAL_SIZE_EXPONENT,
    QGISRedLegendsDialog,
)
from QGISRed.compat import SL_PROP_SIZE, SL_PROP_STROKE_WIDTH, WKB_LINE_GEOMETRY, WKB_POINT_GEOMETRY

FIELD = "Diameter"
NUMERIC = QGISRedLegendsDialog.FIELD_TYPE_NUMERIC
CATEGORICAL = QGISRedLegendsDialog.FIELD_TYPE_CATEGORICAL


def scalePolynomial(value, domainMin, domainMax, rangeMin, rangeMax, exponent):
    """QGIS's scale_polynomial(), as the map evaluates the expression the editor writes."""
    if value <= domainMin:
        return rangeMin
    if value >= domainMax:
        return rangeMax
    return ((rangeMax - rangeMin) / (domainMax - domainMin) ** exponent) * (value - domainMin) ** exponent + rangeMin


def expectedSize(value, values, minSize=1.0, maxSize=5.0, invert=False):
    first, second = (maxSize, minSize) if invert else (minSize, maxSize)
    return scalePolynomial(value, min(values), max(values), first, second, PROPORTIONAL_SIZE_EXPONENT)


class FakeLineEdit:
    def __init__(self, text):
        self._text = text
        self.signalsBlocked = False

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    def blockSignals(self, blocked):
        self.signalsBlocked = blocked


class FakeSpin:
    def __init__(self, value):
        self._value = value

    def value(self):
        return self._value


class FakeCheck:
    def __init__(self, checked):
        self._checked = checked

    def isChecked(self):
        return self._checked


class FakeCombo:
    def __init__(self, text):
        self._text = text

    def currentText(self):
        return self._text


class FakeTable:
    """Rows as (size text, value text, label); cells the builders read but the
    fakes do not carry (checkbox and colour containers) come back as None."""

    def __init__(self, rows):
        self.rows = [[None, None, FakeLineEdit(size), FakeLineEdit(value), FakeLineEdit(label)]
                     for size, value, label in rows]

    def rowCount(self):
        return len(self.rows)

    def cellWidget(self, row, column):
        return self.rows[row][column]

    def sizes(self):
        return [float(cells[2].text()) for cells in self.rows]


class FakeQgsProperty:
    ExpressionBasedProperty = object()

    def __init__(self, expr=None):
        self.expr = expr

    def __bool__(self):
        return self.expr is not None

    @classmethod
    def fromExpression(cls, expr):
        return cls(expr)

    def propertyType(self):
        return type(self).ExpressionBasedProperty

    def expressionString(self):
        return self.expr


class FakeSymbolLayer:
    def __init__(self, expressions=None):
        self._props = {key: FakeQgsProperty(expr) for key, expr in (expressions or {}).items()}

    def dataDefinedProperties(self):
        layer = self

        class _Collection:
            def property(self, key):
                return layer._props.get(key)

        return _Collection()

    def setDataDefinedProperty(self, key, prop):
        self._props[key] = prop

    def expression(self, key):
        prop = self._props.get(key)
        return prop.expr if prop else None


class FakeSymbol:
    def __init__(self, layers):
        self._layers = layers
        self.staticSize = None

    def clone(self):
        return self

    def symbolLayerCount(self):
        return len(self._layers)

    def symbolLayer(self, i):
        return self._layers[i]

    def setSize(self, size):
        self.staticSize = size

    def setWidth(self, width):
        self.staticSize = width


class FakeCategory:
    def __init__(self, value, symbol, label=""):
        self._value, self._symbol, self._label = value, symbol, label
        self.renderState = True

    def value(self):
        return self._value

    def symbol(self):
        return self._symbol

    def label(self):
        return self._label

    def setRenderState(self, state):
        self.renderState = state


class FakeRange:
    def __init__(self, lower, upper, symbol, label=""):
        self.lower, self.upper, self._symbol, self.label = lower, upper, symbol, label

    def symbol(self):
        return self._symbol

    def setRenderState(self, state):
        pass


class FakeCategorizedRenderer:
    def __init__(self, field, categories):
        self.field = field
        self._categories = categories

    def categories(self):
        return self._categories


class FakeGraduatedRenderer:
    def __init__(self, field, ranges):
        self.field = field
        self._ranges = ranges

    def ranges(self):
        return self._ranges


class FakeRule:
    def __init__(self, filterExpression, symbol, label=""):
        self._filter, self._symbol, self._label = filterExpression, symbol, label
        self.active = True

    def filterExpression(self):
        return self._filter

    def label(self):
        return self._label

    def symbol(self):
        return self._symbol

    def setSymbol(self, symbol):
        self._symbol = symbol

    def setLabel(self, label):
        self._label = label

    def setActive(self, active):
        self.active = active


class FakeRuleRenderer:
    def __init__(self, rules):
        self._rules = rules

    def clone(self):
        return self

    def rootRule(self):
        renderer = self

        class _Root:
            def children(self):
                return list(renderer._rules)

            def appendChild(self, rule):
                renderer._rules.append(rule)

            def removeChild(self, rule):
                renderer._rules.remove(rule)

        return _Root()


class FakeLayer:
    def __init__(self, renderer=None, geometryType=WKB_POINT_GEOMETRY):
        self._renderer = renderer
        self._geometryType = geometryType

    def renderer(self):
        return self._renderer

    def geometryType(self):
        return self._geometryType

    def customProperty(self, key):
        return None


def _dialog(monkeypatch, fieldType, rows, values, minSize=1.0, maxSize=5.0, invert=False,
            sizeMode="Proportional to Value", renderer=None, geometryType=WKB_POINT_GEOMETRY):
    monkeypatch.setattr(legendsModule, "QLineEdit", FakeLineEdit)
    monkeypatch.setattr(legendsModule, "QgsProperty", FakeQgsProperty)
    monkeypatch.setattr(legendsModule, "QgsCategorizedSymbolRenderer", FakeCategorizedRenderer)
    monkeypatch.setattr(legendsModule, "QgsGraduatedSymbolRenderer", FakeGraduatedRenderer)
    monkeypatch.setattr(legendsModule, "QgsRuleBasedRenderer", FakeRuleRenderer)
    monkeypatch.setattr(legendsModule, "QgsRendererCategory", FakeCategory)
    monkeypatch.setattr(legendsModule, "QgsRendererRange", FakeRange)
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    dialog.currentFieldType = fieldType
    dialog.currentFieldName = FIELD
    dialog.currentLayer = FakeLayer(renderer, geometryType)
    dialog.tableView = FakeTable(rows)
    dialog.spinSizeMin = FakeSpin(minSize)
    dialog.spinSizeMax = FakeSpin(maxSize)
    dialog.ckSizeInvert = FakeCheck(invert)
    dialog.cbSizes = FakeCombo(sizeMode)
    dialog.getNumericValues = lambda: sorted(values)
    dialog.discardProportionalSizes = False
    dialog._sourceRuleRenderer = None
    dialog.tr = lambda text: text
    return dialog


def rangeRows(bounds):
    return [("1.0", f"{lower:.2f} - {upper:.2f}", f"{lower} - {upper}") for lower, upper in bounds]


def categoryRows(categories):
    return [("1.0", value, value) for value in categories]


# ---------------------------------------------------------------------------
# Graduated legends: the class stands for its range midpoint
# ---------------------------------------------------------------------------

class TestGraduatedProportionalSizes:
    def _sizes(self, monkeypatch, bounds, values, **kwargs):
        dialog = _dialog(monkeypatch, NUMERIC, rangeRows(bounds), values, **kwargs)
        return dialog.calculateProportionalSizes(len(bounds))

    def test_equal_intervals_size_their_midpoints_like_the_map(self, monkeypatch):
        values = [0, 7, 12, 19, 23, 30]
        sizes = self._sizes(monkeypatch, [(0, 10), (10, 20), (20, 30)], values)
        assert sizes == pytest.approx([expectedSize(mid, values) for mid in (5, 15, 25)])
        assert 1.0 < sizes[0] < sizes[1] < sizes[2] < 5.0

    def test_uneven_quantile_like_ranges_follow_the_values_not_the_row_index(self, monkeypatch):
        values = [0, 1, 2, 3, 5, 40, 100]
        sizes = self._sizes(monkeypatch, [(0, 2), (2, 5), (5, 100)], values)
        assert sizes == pytest.approx([expectedSize(mid, values) for mid in (1, 3.5, 52.5)])
        # A Linear size mode would space the three rows evenly; here the first two
        # classes sit close together and far from the wide third one.
        assert sizes[1] - sizes[0] < (sizes[2] - sizes[1]) / 2

    def test_the_curve_is_the_flannery_like_one_not_a_straight_line(self, monkeypatch):
        values = [0, 100]
        [size] = self._sizes(monkeypatch, [(0, 100)], values)
        assert size == pytest.approx(1.0 + 4.0 * 0.5 ** PROPORTIONAL_SIZE_EXPONENT)
        assert size > 3.0  # the linear midpoint

    def test_classes_narrower_than_the_data_stay_strictly_between_the_bounds(self, monkeypatch):
        values = [0, 25, 50, 75, 100]
        sizes = self._sizes(monkeypatch, [(20, 40), (40, 60)], values)
        assert all(1.0 < size < 5.0 for size in sizes)
        assert sizes == pytest.approx([expectedSize(30, values), expectedSize(50, values)])

    def test_manual_ranges_beyond_the_data_clamp_to_the_size_bounds(self, monkeypatch):
        values = [10, 50, 100]
        sizes = self._sizes(monkeypatch, [(-500, 0), (0, 100), (100, 1000)], values)
        assert sizes[0] == pytest.approx(1.0)
        assert sizes[2] == pytest.approx(5.0)
        assert 1.0 < sizes[1] < 5.0

    def test_endpoints_hit_the_min_and_max_sizes_exactly(self, monkeypatch):
        values = [0, 100]
        sizes = self._sizes(monkeypatch, [(0, 0), (0, 100), (100, 100)], values, minSize=2.0, maxSize=8.0)
        assert sizes[0] == pytest.approx(2.0)
        assert sizes[2] == pytest.approx(8.0)

    def test_constant_data_gives_every_class_the_min_size(self, monkeypatch):
        sizes = self._sizes(monkeypatch, [(42, 42), (42, 42)], [42, 42, 42])
        assert sizes == [1.0, 1.0]

    def test_invert_flips_the_mapping_not_the_row_order(self, monkeypatch):
        values = [0, 1, 2, 3, 5, 40, 100]
        bounds = [(0, 2), (2, 5), (5, 100)]
        inverted = self._sizes(monkeypatch, bounds, values, invert=True)
        straight = self._sizes(monkeypatch, bounds, values)
        assert inverted == pytest.approx([expectedSize(mid, values, invert=True) for mid in (1, 3.5, 52.5)])
        assert inverted[0] > inverted[1] > inverted[2]
        # Reversing the straight list (the old behaviour) is not what the map draws
        assert inverted != pytest.approx(list(reversed(straight)))
        assert inverted == pytest.approx([6.0 - size for size in straight])

    def test_a_row_without_a_readable_range_takes_the_fallback_size(self, monkeypatch):
        rows = rangeRows([(0, 10)]) + [("1.0", "n/a", "broken")]
        dialog = _dialog(monkeypatch, NUMERIC, rows, [0, 10, 20], minSize=1.5)
        sizes = dialog.calculateProportionalSizes(2)
        assert sizes[1] == 1.5

    def test_apply_size_logic_writes_the_sizes_into_the_column(self, monkeypatch):
        values = [0, 100]
        dialog = _dialog(monkeypatch, NUMERIC, rangeRows([(0, 50), (50, 100)]), values)
        dialog.applySizeLogic()
        expected = [expectedSize(25, values), expectedSize(75, values)]
        assert dialog.tableView.sizes() == pytest.approx(expected, abs=0.05)


# ---------------------------------------------------------------------------
# Categorized legends: the class stands for its own value
# ---------------------------------------------------------------------------

class TestCategorizedProportionalSizes:
    def _sizes(self, monkeypatch, categories, values, **kwargs):
        dialog = _dialog(monkeypatch, CATEGORICAL, categoryRows(categories), values, **kwargs)
        return dialog.calculateProportionalSizes(len(categories))

    def test_numeric_categories_are_sized_by_their_value(self, monkeypatch):
        values = [100, 100, 200, 400, 400]
        sizes = self._sizes(monkeypatch, ["100", "200", "400"], values)
        assert sizes == pytest.approx([1.0, expectedSize(200, values), 5.0])

    def test_row_order_does_not_matter(self, monkeypatch):
        values = [100, 200, 400]
        reordered = self._sizes(monkeypatch, ["400", "100", "200"], values)
        sorted_ = self._sizes(monkeypatch, ["100", "200", "400"], values)
        assert reordered == pytest.approx([sorted_[2], sorted_[0], sorted_[1]])

    def test_a_class_outside_the_data_extent_clamps(self, monkeypatch):
        sizes = self._sizes(monkeypatch, ["50", "150", "9999"], [100, 150, 200])
        assert sizes[0] == pytest.approx(1.0)
        assert sizes[2] == pytest.approx(5.0)

    def test_special_classes_take_the_fallback_size(self, monkeypatch):
        sizes = self._sizes(monkeypatch, ["100", "NULL", "Other Values"], [100, 200], minSize=2.0)
        assert sizes[1:] == [2.0, 2.0]

    def test_text_categories_all_take_the_fallback_size(self, monkeypatch):
        # A text field has no numbers to be proportional to; the map draws the
        # same fallback through coalesce(), so legend and map still agree.
        sizes = self._sizes(monkeypatch, ["PVC", "Steel", "Iron"], [], minSize=1.5)
        assert sizes == [1.5, 1.5, 1.5]

    def test_invert_gives_the_smallest_value_the_largest_marker(self, monkeypatch):
        values = [100, 200, 400]
        sizes = self._sizes(monkeypatch, ["100", "200", "400"], values, invert=True)
        assert sizes == pytest.approx([5.0, expectedSize(200, values, invert=True), 1.0])

    def test_inverted_special_classes_take_the_max_size_like_the_expression_fallback(self, monkeypatch):
        sizes = self._sizes(monkeypatch, ["100", "NULL"], [100, 200], invert=True)
        assert sizes[1] == 5.0

    def test_a_missing_value_cell_takes_the_fallback_size(self, monkeypatch):
        dialog = _dialog(monkeypatch, CATEGORICAL, categoryRows(["100"]), [100, 200])
        dialog.tableView.rows[0][3] = None
        assert dialog.calculateProportionalSizes(1) == [1.0]


# ---------------------------------------------------------------------------
# Apply: the expression reaches every symbol of every legend type
# ---------------------------------------------------------------------------

EXPRESSION = (
    'coalesce(scale_polynomial("Diameter", minimum("Diameter"), maximum("Diameter"), 1.0, 5.0, 0.57), 1.0)'
)
INVERTED_EXPRESSION = (
    'coalesce(scale_polynomial("Diameter", minimum("Diameter"), maximum("Diameter"), 5.0, 1.0, 0.57), 5.0)'
)


class TestProportionalExpression:
    def test_marker_layers_get_a_size_expression(self, monkeypatch):
        layers = [FakeSymbolLayer(), FakeSymbolLayer()]
        _dialog(monkeypatch, NUMERIC, [], [0, 1]).applyProportionalSizeExpression(FakeSymbol(layers))
        assert [layer.expression(SL_PROP_SIZE) for layer in layers] == [EXPRESSION, EXPRESSION]
        assert layers[0].expression(SL_PROP_STROKE_WIDTH) is None

    def test_line_layers_get_a_stroke_width_expression(self, monkeypatch):
        layer = FakeSymbolLayer()
        dialog = _dialog(monkeypatch, NUMERIC, [], [0, 1], geometryType=WKB_LINE_GEOMETRY)
        dialog.applyProportionalSizeExpression(FakeSymbol([layer]))
        assert layer.expression(SL_PROP_STROKE_WIDTH) == EXPRESSION
        assert layer.expression(SL_PROP_SIZE) is None

    def test_invert_swaps_the_bounds_and_the_fallback(self, monkeypatch):
        layer = FakeSymbolLayer()
        _dialog(monkeypatch, NUMERIC, [], [0, 1], invert=True).applyProportionalSizeExpression(FakeSymbol([layer]))
        assert layer.expression(SL_PROP_SIZE) == INVERTED_EXPRESSION

    def test_the_column_and_the_expression_share_the_same_bounds(self, monkeypatch):
        dialog = _dialog(monkeypatch, NUMERIC, [], [0, 1], minSize=2.0, maxSize=8.0, invert=True)
        assert dialog.getProportionalSizeBounds() == (8.0, 2.0)


class TestCategorizedRendererApply:
    def _build(self, monkeypatch, categories, sizeMode="Proportional to Value", discard=False, **kwargs):
        symbols = {value: FakeSymbol([FakeSymbolLayer()]) for value in categories}
        existing = FakeCategorizedRenderer(FIELD, [FakeCategory(value, symbols[value], value) for value in categories])
        dialog = _dialog(monkeypatch, CATEGORICAL, categoryRows(categories), [100, 200, 400],
                         sizeMode=sizeMode, renderer=existing, **kwargs)
        dialog.discardProportionalSizes = discard
        dialog.applyColorToSymbol = lambda symbol, color: None
        dialog.applySizeToSymbol = lambda symbol, size: symbol.setSize(size)
        return dialog.buildCategoricalRenderer(), symbols

    def test_every_category_symbol_gets_the_expression(self, monkeypatch):
        renderer, symbols = self._build(monkeypatch, ["100", "200", "400"])
        assert renderer.field == FIELD and len(renderer.categories()) == 3
        for symbol in symbols.values():
            assert symbol.symbolLayer(0).expression(SL_PROP_SIZE) == EXPRESSION

    def test_the_static_size_still_backs_the_legend_swatch(self, monkeypatch):
        _, symbols = self._build(monkeypatch, ["100", "400"])
        assert symbols["100"].staticSize == 1.0

    def test_inverted_bounds_reach_the_categories(self, monkeypatch):
        _, symbols = self._build(monkeypatch, ["100", "400"], invert=True)
        assert symbols["400"].symbolLayer(0).expression(SL_PROP_SIZE) == INVERTED_EXPRESSION

    def test_other_size_modes_leave_the_symbols_alone(self, monkeypatch):
        _, symbols = self._build(monkeypatch, ["100", "400"], sizeMode="Linear")
        assert symbols["100"].symbolLayer(0).expression(SL_PROP_SIZE) is None

    def test_leaving_the_mode_drops_the_expression_on_apply(self, monkeypatch):
        symbols = {value: FakeSymbol([FakeSymbolLayer({SL_PROP_SIZE: EXPRESSION})]) for value in ("100", "400")}
        existing = FakeCategorizedRenderer(
            FIELD, [FakeCategory(value, symbol, value) for value, symbol in symbols.items()])
        dialog = _dialog(monkeypatch, CATEGORICAL, categoryRows(["100", "400"]), [100, 400],
                         sizeMode="Linear", renderer=existing)
        dialog.discardProportionalSizes = True
        dialog.applyColorToSymbol = lambda symbol, color: None
        dialog.applySizeToSymbol = lambda symbol, size: symbol.setSize(size)

        dialog.buildCategoricalRenderer()

        for symbol in symbols.values():
            assert symbol.symbolLayer(0).expression(SL_PROP_SIZE) is None


class TestRuleBasedCategorizedRendererApply:
    def _build(self, monkeypatch, sizeMode="Proportional to Value", discard=False, expression=None):
        layers = {value: FakeSymbolLayer({SL_PROP_SIZE: expression} if expression else None)
                  for value in ("100", "400")}
        rules = [FakeRule(f'"{FIELD}" = \'{value}\'', FakeSymbol([layer]), value) for value, layer in layers.items()]
        dialog = _dialog(monkeypatch, CATEGORICAL, categoryRows(["100", "400"]), [100, 400], sizeMode=sizeMode)
        dialog._sourceRuleRenderer = FakeRuleRenderer(rules)
        dialog.discardProportionalSizes = discard
        dialog.applyColorToSymbol = lambda symbol, color: None
        dialog.applySizeToSymbol = lambda symbol, size: symbol.setSize(size)
        renderer = dialog.buildCategoricalRenderer()
        return renderer, layers

    def test_rules_keep_their_filters_and_get_the_expression(self, monkeypatch):
        renderer, layers = self._build(monkeypatch)
        assert [rule.filterExpression() for rule in renderer.rootRule().children()] == [
            '"Diameter" = \'100\'', '"Diameter" = \'400\'']
        assert all(layer.expression(SL_PROP_SIZE) == EXPRESSION for layer in layers.values())

    def test_leaving_the_mode_drops_the_expression_from_the_rules(self, monkeypatch):
        _, layers = self._build(monkeypatch, sizeMode="Linear", discard=True, expression=EXPRESSION)
        assert all(layer.expression(SL_PROP_SIZE) is None for layer in layers.values())


class TestGraduatedRendererApply:
    def _build(self, monkeypatch, sizeMode="Proportional to Value", discard=False, expression=None):
        bounds = [(0, 50), (50, 100)]
        layers = [FakeSymbolLayer({SL_PROP_SIZE: expression} if expression else None) for _ in bounds]
        existing = FakeGraduatedRenderer(FIELD, [FakeRange(lower, upper, FakeSymbol([layer]))
                                                 for (lower, upper), layer in zip(bounds, layers)])
        dialog = _dialog(monkeypatch, NUMERIC, rangeRows(bounds), [0, 100], sizeMode=sizeMode, renderer=existing)
        dialog.discardProportionalSizes = discard
        dialog.applyColorToSymbol = lambda symbol, color: None
        dialog.applySizeToSymbol = lambda symbol, size: symbol.setSize(size)
        return dialog.buildNumericRenderer(), layers

    def test_every_range_symbol_gets_the_expression(self, monkeypatch):
        renderer, layers = self._build(monkeypatch)
        assert [(r.lower, r.upper) for r in renderer.ranges()] == [(0.0, 50.0), (50.0, 100.0)]
        assert all(layer.expression(SL_PROP_SIZE) == EXPRESSION for layer in layers)

    def test_leaving_the_mode_drops_the_expression_from_the_ranges(self, monkeypatch):
        _, layers = self._build(monkeypatch, sizeMode="Linear", discard=True, expression=EXPRESSION)
        assert all(layer.expression(SL_PROP_SIZE) is None for layer in layers)
