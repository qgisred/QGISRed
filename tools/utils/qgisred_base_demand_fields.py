# -*- coding: utf-8 -*-
"""The base demand columns of a consumption points theme.

One theme can hold several base demands side by side — one column per billing run, say —
so everything from the third column onwards is one of them: DemID and Category are the
fixed head of the schema (see GISRed.ExtendedModel/Writers/ToShp.AuxiliaryLayers.cs).

The planning half never touches QGIS, so the rules can be tested on their own;
applyFieldChanges is the only part that reaches a layer.
"""

import re


# DemID and Category. Everything after them is a base demand.
FIXED_FIELD_NAMES = ("DemID", "Category")
FIXED_FIELD_COUNT = len(FIXED_FIELD_NAMES)

# A DBF column name holds no more, and the file is the contract with the DLL.
MAX_FIELD_NAME_LENGTH = 10

# Why a name was rejected. The dialog turns these into translated sentences; keeping them
# symbolic is what lets the rules live outside the UI.
NAME_OK = ""
NAME_EMPTY = "empty"
NAME_TOO_LONG = "too_long"
NAME_INVALID = "invalid"
NAME_DUPLICATE = "duplicate"

_VALID_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def baseDemandFieldNames(fieldNames):
    """The base demand columns out of a theme's full field list, in file order."""
    return list(fieldNames[FIXED_FIELD_COUNT:])


def hasConsumptionPointsSchema(fieldNames):
    """Whether `fieldNames` starts with the head the DLL writes for a consumption points
    theme. That head is what says the rest of the columns are base demands."""
    head = [name.lower() for name in fieldNames[:FIXED_FIELD_COUNT]]
    return head == [name.lower() for name in FIXED_FIELD_NAMES]


def resolveBaseDemandField(fieldNames, preferred=""):
    """The base demand column to label a consumption points layer with, or "".

    The name cannot be assumed: the DLL writes the one it was asked for, and the field
    editor lets the user rename it or add more. So `preferred` — what the DLL just
    reported — wins when it is really there, and otherwise the layer's own schema
    answers: past DemID and Category everything is a base demand, whatever it is called.

    The BaseDem* fallback is for layers that do not carry that head, which is where the
    label used to come from before the columns became the user's to name.
    """
    from .qgisred_auxiliary_layers import DEFAULT_BASE_DEMAND_FIELD

    byLower = {name.lower(): name for name in fieldNames}

    if preferred and preferred.lower() in byLower:
        return byLower[preferred.lower()]

    if hasConsumptionPointsSchema(fieldNames):
        demands = baseDemandFieldNames(fieldNames)
        if demands:
            return demands[0]

    stem = DEFAULT_BASE_DEMAND_FIELD.lower()
    for name in fieldNames:
        if name.lower().startswith(stem):
            return name

    return ""


def validateFieldName(name, otherNames=()):
    """NAME_OK, or why `name` cannot be used. Comparison is case-insensitive: a DBF
    cannot tell BaseDem from basedem."""
    if not name or not name.strip():
        return NAME_EMPTY
    if name != name.strip():
        return NAME_INVALID
    if len(name) > MAX_FIELD_NAME_LENGTH:
        return NAME_TOO_LONG
    if not _VALID_NAME.match(name):
        return NAME_INVALID
    if name.lower() in {other.lower() for other in otherNames}:
        return NAME_DUPLICATE
    return NAME_OK


def validateRows(rows):
    """(errorCode, name) for the first problem in `rows`, or (NAME_OK, "").

    `rows` is the dialog's list of (originalName or None, newName), in display order. A
    theme with no base demand at all is not a theme, so an empty list is rejected too.
    """
    if not rows:
        return NAME_EMPTY, ""
    seen = []
    for _original, name in rows:
        error = validateFieldName(name, seen)
        if error:
            return error, name or ""
        seen.append(name)
    return NAME_OK, ""


def suggestFieldName(existingNames, stem=""):
    """A free name in the family of the one the DLL writes: BaseDem, BaseDem2, BaseDem3…

    Returns "" when no numbered name fits in MAX_FIELD_NAME_LENGTH, leaving the user to
    type one rather than offering a name that would be rejected.
    """
    from .qgisred_auxiliary_layers import DEFAULT_BASE_DEMAND_FIELD

    stem = stem or DEFAULT_BASE_DEMAND_FIELD
    taken = {name.lower() for name in existingNames if name}

    if stem.lower() not in taken and len(stem) <= MAX_FIELD_NAME_LENGTH:
        return stem

    index = 2
    while True:
        candidate = stem + str(index)
        if len(candidate) > MAX_FIELD_NAME_LENGTH:
            return ""
        if candidate.lower() not in taken:
            return candidate
        index += 1


def planFieldChanges(originalNames, rows):
    """(renames, additions, deletions) that turn `originalNames` into `rows`.

    Rows carry the name they started with, so a row whose text changed is a rename rather
    than a delete plus an add — which matters: renaming keeps the column's values, and
    the client asked for the values to go only when a field is actually removed.
    """
    kept = {original for original, _ in rows if original}
    deletions = [name for name in originalNames if name not in kept]
    renames = {original: name for original, name in rows if original and name != original}
    additions = [name for original, name in rows if not original]
    return renames, additions, deletions


def applyFieldChanges(layer, renames, additions, deletions):
    """Apply a plan to `layer`'s provider. Returns "" or the first error.

    Deletions run first so renames and additions cannot collide with a name on its way
    out. Indices are re-read between steps because every step shifts them, and the
    provider is reloaded in between: OGR does not publish the new field list to the next
    call otherwise, and the columns end up in the wrong order.
    """
    from qgis.core import QgsField
    from ...compat import FIELD_TYPE_DOUBLE

    provider = layer.dataProvider()

    def currentNames():
        return [field.name() for field in layer.fields()]

    if deletions:
        names = currentNames()
        indices = [names.index(name) for name in deletions if name in names]
        if indices and not provider.deleteAttributes(sorted(indices, reverse=True)):
            return "Could not delete the fields"
        layer.updateFields()
        provider.reloadData()

    if renames:
        names = currentNames()
        mapping = {names.index(old): new for old, new in renames.items() if old in names}
        if mapping and not provider.renameAttributes(mapping):
            return "Could not rename the fields"
        layer.updateFields()
        provider.reloadData()

    if additions:
        # Same width and precision the DLL writes, so a field added here is
        # indistinguishable from one that came with the theme.
        fields = [QgsField(name, FIELD_TYPE_DOUBLE, "Real", 17, 2) for name in additions]
        if not provider.addAttributes(fields):
            return "Could not add the fields"
        layer.updateFields()

    return ""
