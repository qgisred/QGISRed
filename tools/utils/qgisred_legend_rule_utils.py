# -*- coding: utf-8 -*-
"""Reading the filters of a rule-based renderer back as ranges or categories.

``applyNullStyle`` turns a graduated renderer into rules so NULL features stay visible,
and everything that needs the classes back -the legend editor and the results
histogram- has to undo that conversion by parsing the filter expressions.

The parsing lives here because those two readers must agree: a filter one of them
rejects is a class the other would silently lose.
"""
import re

# Range filters as applyNullStyle leaves them, by way of convertFromRenderer. Two
# things vary and neither can be assumed: the classified column arrives spelled
# however the conversion produced it — (Velocity), "Velocity", Velocity, abs(Flow) —
# and the outer classes carry a single bound, because the conversion drops the
# redundant one ('<0.1' is just "(Velocity) <= 0.1"). So each side is read on its own
# instead of matching one fixed shape.
_NUMBER = r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?'
_RANGE_ATTRIBUTE = re.compile(r'^\s*(.+?)\s*(?:>=?|<=?)\s*' + _NUMBER)
_RANGE_LOWER = re.compile(r'>=?\s*(' + _NUMBER + r')')
_RANGE_UPPER = re.compile(r'<=?\s*(' + _NUMBER + r')')

# Stands in for the bound the conversion left out. It is the sentinel the plugin's own
# styles already use for their open-ended first and last classes, so applying a table
# untouched writes back exactly the values the style file had.
OPEN_RANGE_BOUND = 1e10

_SIMPLE_RULE_FILTER_PATTERN = re.compile(r"^\s*\"([^\"]+)\"\s*=\s*'([^']*)'\s*$")
_COMPOSITE_RULE_FILTER_PATTERN = re.compile(
    r"^\s*\"([^\"]+)\"\s*=\s*'([^']*)'\s*AND\s*\"([^\"]+)\"\s*(=|<>)\s*'([^']*)'\s*$",
    re.IGNORECASE,
)


def unwrapClassAttribute(attr):
    """Strip the quotes or the wrapping parentheses a filter may carry around a column.

    abs(Flow) also ends in ")" without being wrapped, so the parentheses are only
    removed when they really enclose the whole string.
    """
    attr = attr.strip()
    if len(attr) > 1 and attr[0] == '"' and attr[-1] == '"':
        return attr[1:-1]
    if len(attr) > 1 and attr[0] == "(" and attr[-1] == ")":
        depth = 0
        for char in attr[1:-1]:
            depth += (char == "(") - (char == ")")
            if depth < 0:
                return attr
        return attr[1:-1]
    return attr


def parseRangeFilter(expression, openBound=OPEN_RANGE_BOUND):
    """(column, lower, upper) of a range rule, or None when the rule is not a range."""
    expression = expression or ""
    attribute = _RANGE_ATTRIBUTE.match(expression)
    if not attribute:
        return None
    lower = _RANGE_LOWER.search(expression)
    upper = _RANGE_UPPER.search(expression)
    if not lower and not upper:
        return None
    return (
        unwrapClassAttribute(attribute.group(1)),
        float(lower.group(1)) if lower else -openBound,
        float(upper.group(1)) if upper else openBound,
    )


def parseCategoricalRuleFilter(filterExpr):
    """Parse a categorical rule filter into (field, value), or None if not categorical.

    Supports "Field" = 'value' and the Hydraulic Sectors split pair
    "Class" = 'nH-nQ' AND "SubNet" =/<> 'ClosedLinks' (the '=' clause names the
    displayed value, the '<>' clause keeps the main class value).
    """
    if not filterExpr:
        return None
    match = _SIMPLE_RULE_FILTER_PATTERN.match(filterExpr)
    if match:
        return match.group(1), match.group(2)
    match = _COMPOSITE_RULE_FILTER_PATTERN.match(filterExpr)
    if match:
        field, value, _secondField, op, secondValue = match.groups()
        return field, secondValue if op == "=" else value
    return None
