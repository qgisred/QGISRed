# -*- coding: utf-8 -*-
"""Field-name resolution for the Node/Link result layers, for both DLL schemas.

Older DLL builds wrote the result base layers (``Results/<Net>_<Scenario>_{Node|Link}.shp``)
with the generic columns ``Id`` and ``Type``. Newer builds write ``NodeID``/``LinkID`` and
``NodeType``/``LinkType`` instead. A project simulated before the DLL change keeps the old
columns until it is simulated again, so both schemas must be read transparently.

Two resolution styles are provided:

* ``resultIdField`` / ``resultTypeField`` — resolve the real column name from a layer (or
  from a list of field names). Use this in Python and when building QGIS expressions from
  code, where the layer is at hand.
* ``RESULT_ID_EXPR`` / ``RESULT_TYPE_EXPR`` — layer-agnostic, null-safe expression
  fragments for static ``.qml`` styles, where no layer is available. The direct column
  reference ``"NodeID"`` cannot be used there because it breaks when the field is absent;
  ``attribute($currentfeature, ...)`` returns NULL instead.

This module deliberately has no QGIS imports so it stays cheap and unit-testable.
"""

# Ordered candidates; the new names come first so a re-simulated project uses them.
ID_FIELD_CANDIDATES = ("NodeID", "LinkID", "Id", "ID", "id")
TYPE_FIELD_CANDIDATES = ("NodeType", "LinkType", "Type")

# Null-safe fallbacks for static .qml styles (no layer context available there).
RESULT_ID_EXPR = "coalesce(attribute($currentfeature,'NodeID'),attribute($currentfeature,'LinkID'),attribute($currentfeature,'Id'))"
RESULT_TYPE_EXPR = "coalesce(attribute($currentfeature,'NodeType'),attribute($currentfeature,'LinkType'),attribute($currentfeature,'Type'))"


def _fieldNames(source):
    """Accept a QgsVectorLayer, a QgsFeature, a QgsFields or a plain list of names."""
    if source is None:
        return []
    if isinstance(source, (list, tuple, set, frozenset)):
        return list(source)
    fields = getattr(source, "fields", None)
    if callable(fields):
        source = fields()
    names = getattr(source, "names", None)
    if callable(names):
        return list(names())
    try:
        return [field.name() for field in source]
    except TypeError:
        return []


def _firstPresent(source, candidates, default):
    names = _fieldNames(source)
    for candidate in candidates:
        if candidate in names:
            return candidate
    return default


def resultIdField(source, default="Id"):
    """Return the element-id column of a result layer ('NodeID', 'LinkID' or 'Id')."""
    return _firstPresent(source, ID_FIELD_CANDIDATES, default)


def resultTypeField(source, default=None):
    """Return the element-type column of a result layer ('NodeType', 'LinkType' or 'Type').

    Returns ``default`` (None) when the layer carries no type column at all, so callers can
    skip type-dependent behaviour instead of building an expression on a missing field.
    """
    return _firstPresent(source, TYPE_FIELD_CANDIDATES, default)


def resultIdColumnRef(source):
    """Quoted column reference for the element-id field, for use in QGIS expressions."""
    return '"{}"'.format(resultIdField(source))


def resultTypeColumnRef(source):
    """Quoted column reference for the element-type field, for use in QGIS expressions."""
    return '"{}"'.format(resultTypeField(source, default="Type"))
