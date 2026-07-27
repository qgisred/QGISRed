# -*- coding: utf-8 -*-
"""Result-layer field resolution across both DLL schemas (Id/Type vs NodeID/NodeType)."""
from QGISRed.tools.utils.qgisred_result_fields import (
    RESULT_ID_EXPR, RESULT_TYPE_EXPR,
    resultIdColumnRef, resultIdField, resultTypeColumnRef, resultTypeField,
)


class _StubField:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class _StubFields:
    """Mimics QgsFields: iterable of fields and a names() accessor."""

    def __init__(self, names):
        self._names = list(names)

    def __iter__(self):
        return iter(_StubField(n) for n in self._names)

    def names(self):
        return list(self._names)


class _StubFieldsWithoutNames(_StubFields):
    names = None


class _StubLayer:
    def __init__(self, names, fieldsClass=_StubFields):
        self._fields = fieldsClass(names)

    def fields(self):
        return self._fields


class _StubFeature(_StubLayer):
    pass


class TestResultIdField:
    def test_new_schema(self):
        assert resultIdField(_StubLayer(["NodeID", "NodeType", "Pressure"])) == "NodeID"
        assert resultIdField(_StubLayer(["LinkID", "LinkType", "Flow"])) == "LinkID"

    def test_legacy_schema(self):
        assert resultIdField(_StubLayer(["Id", "Type", "Pressure"])) == "Id"

    def test_new_name_wins_when_both_are_present(self):
        assert resultIdField(_StubLayer(["Id", "NodeID"])) == "NodeID"

    def test_defaults_to_id_when_absent(self):
        assert resultIdField(_StubLayer(["Pressure"])) == "Id"
        assert resultIdField(None) == "Id"


class TestResultTypeField:
    def test_new_schema(self):
        assert resultTypeField(_StubLayer(["NodeID", "NodeType"])) == "NodeType"
        assert resultTypeField(_StubLayer(["LinkID", "LinkType"])) == "LinkType"

    def test_legacy_schema(self):
        assert resultTypeField(_StubLayer(["Id", "Type"])) == "Type"

    def test_returns_none_when_absent_so_callers_can_skip_filtering(self):
        assert resultTypeField(_StubLayer(["Id", "Pressure"])) is None

    def test_honours_an_explicit_default(self):
        assert resultTypeField(_StubLayer(["Id"]), default="Type") == "Type"


class TestSourceKinds:
    def test_accepts_a_plain_list_of_names(self):
        assert resultIdField(["LinkID", "Flow"]) == "LinkID"
        assert resultTypeField({"Type", "Flow"}) == "Type"

    def test_accepts_a_feature(self):
        assert resultIdField(_StubFeature(["NodeID"])) == "NodeID"

    def test_accepts_fields_without_a_names_accessor(self):
        layer = _StubLayer(["LinkID", "LinkType"], fieldsClass=_StubFieldsWithoutNames)
        assert resultIdField(layer) == "LinkID"
        assert resultTypeField(layer) == "LinkType"


class TestColumnRefs:
    def test_quotes_the_resolved_column(self):
        assert resultIdColumnRef(_StubLayer(["NodeID"])) == '"NodeID"'
        assert resultTypeColumnRef(_StubLayer(["LinkType"])) == '"LinkType"'

    def test_type_column_ref_falls_back_to_the_legacy_name(self):
        assert resultTypeColumnRef(_StubLayer(["Id"])) == '"Type"'


class TestStaticStyleExpressions:
    def test_cover_both_schemas_null_safely(self):
        for expr, new, legacy in (
            (RESULT_ID_EXPR, "NodeID", "Id"),
            (RESULT_TYPE_EXPR, "NodeType", "Type"),
        ):
            # attribute() yields NULL for a missing field, unlike a direct "column" reference
            assert expr.startswith("coalesce(attribute($currentfeature,")
            assert "'{}'".format(new) in expr
            assert "'{}'".format(legacy) in expr
