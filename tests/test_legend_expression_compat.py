# -*- coding: utf-8 -*-
"""Guards for the two things a rebase silently reverted in the legends dialog.

Both were invisible to the suite: the QGIS 4 shims and the null-safe field
expressions have no behavioural test of their own, so a merge that restored the
QGIS 3 spellings passed green.
"""
import os
import re

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import (
    substituteCapturedGroup,
    styleVariablePattern,
    ISOLATION_VALVE_FILL_TEMPLATE,
)

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _coalescePattern(oldField, newField):
    """The null-safe form: a bare "Field" reference breaks when the field is absent."""
    return re.compile(
        r"coalesce\(\s*attribute\(\s*\$currentfeature\s*,\s*'%s'\s*\)\s*,"
        r"\s*attribute\(\s*\$currentfeature\s*,\s*'%s'\s*\)\s*\)" % (oldField, newField)
    )


class TestFieldRetrocompatInExpressions:
    """The DLLs renamed BaseDem→BaseDemand and IniStatus→Status.

    Layers exist in the wild with either spelling, so the legend expressions must
    read both. `attribute($currentfeature, 'X')` returns NULL for a missing field,
    while a direct "X" reference makes the whole expression fail to evaluate.

    The editor no longer writes these expressions from scratch: it substitutes the
    picked color into the with_variable() declaration the shipped style already carries
    (so a user color does not wipe the status branches). That moves the retro-compat into
    two places, and both are guarded here — the .qml.bak defaults, which are now the only
    source of the coalesce, and the template used when a symbol lost its expression entirely.
    """

    # The shipped styles whose expressions must keep reading both field spellings.
    SHIPPED_STYLES = [
        ("ServiceConnections.qml.bak", "BaseDem", "BaseDemand"),
        ("IsolationValves.qml.bak", "IniStatus", "Status"),
        ("demands.qml.bak", "BaseDem", "BaseValue"),
        ("Meters.qml.bak", "MeterType", "Type"),
    ]

    @pytest.mark.parametrize("styleFile, oldField, newField", SHIPPED_STYLES)
    def test_the_shipped_style_reads_both_field_names(self, styleFile, oldField, newField):
        path = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles", styleFile)
        source = open(path, encoding="utf-8").read()

        assert _coalescePattern(oldField, newField).search(source), (
            f"{styleFile} lost the null-safe {oldField}/{newField} pair; the editor only "
            "substitutes colors into this expression, so nothing would put it back"
        )

    @pytest.mark.parametrize("variable, expression, oldField, newField", [
        (
            "activeDemandServiceConnectionColor",
            "if(@id is NULL, NULL, with_variable('activeDemandServiceConnectionColor', '#b7dfa3', "
            "if(coalesce(attribute($currentfeature,'BaseDem'),attribute($currentfeature,'BaseDemand')) > 0, "
            "@activeDemandServiceConnectionColor, '#ffffff')))",
            "BaseDem", "BaseDemand",
        ),
        ("openIsolationValveColor", ISOLATION_VALVE_FILL_TEMPLATE, "IniStatus", "Status"),
    ])
    def test_substituting_a_color_keeps_the_coalesce(self, variable, expression, oldField, newField):
        # Group 1 of every variable pattern is the declared literal alone; anything else
        # being rewritten would take the retro-compat wrapper with it.
        updated, changed = substituteCapturedGroup(expression, styleVariablePattern(variable, True), "#123456")

        assert changed, "the picked color no longer reaches the shipped expression"
        assert _coalescePattern(oldField, newField).search(updated), updated

    def test_the_isolation_valve_template_reads_both_status_names(self):
        # Written when the symbol lost its expression, so it is a from-scratch
        # expression and carries the retro-compat itself.
        expression = ISOLATION_VALVE_FILL_TEMPLATE

        assert _coalescePattern("IniStatus", "Status").search(expression), expression
        withoutCoalesce = re.sub(r"coalesce\([^)]*\)[^)]*\)", "", expression)
        assert not re.search(r"(?<![\w'])Status(?![\w'])", withoutCoalesce), expression


# QGIS 4 removed or rescoped these enums; compat.py picks the right spelling at
# import time. Anything that reaches for the QGIS 3 name breaks the plugin on 4.x.
FORBIDDEN_QGIS3_ENUMS = [
    (r"QgsSymbolLayer\.Property(?:Size|Width|FillColor|StrokeColor|StrokeWidth)\b", "SL_PROP_* from compat"),
    (r"(?<![\w.])Qgis\.(?:Info|Warning|Critical|Success)\b", "QGIS_INFO / QGIS_WARNING / … from compat"),
    (r"QgsMapLayer\.(?:RasterLayer|VectorLayer)\b", "LAYER_TYPE_RASTER / LAYER_TYPE_VECTOR from compat"),
    (r"QgsWkbTypes\.(?:LineGeometry|PointGeometry)\b", "WKB_LINE_GEOMETRY / WKB_POINT_GEOMETRY from compat"),
    (r"QgsUnitTypes\.Render(?:Points|Millimeters)\b", "RENDER_UNIT_* from compat"),
    (r"QgsLayerTreeNode\.Node(?:Layer|Group)\b", "NODE_TYPE_LAYER / NODE_TYPE_GROUP from compat"),
    (r"QgsSnappingConfig\.(?:Vertex|Segment|VertexAndSegment)\b", "SNAP_TYPE_* from compat"),
    (r"(?<![\w.])QVariant\.(?:String|Double|Int|LongLong)\b", "QVariantString / QVariantDouble / … from compat"),
]


def _pluginSourceFiles():
    """Every plugin .py except the shim itself, the suite, and generated resources."""
    skipDirs = {".git", "__pycache__", "tests", "i18n", "help"}
    skipFiles = {"compat.py", "resources3x.py"}
    for folder, subfolders, files in os.walk(PLUGIN_ROOT):
        subfolders[:] = [d for d in subfolders if d not in skipDirs]
        for name in sorted(files):
            if name.endswith(".py") and name not in skipFiles:
                yield os.path.join(folder, name)


class TestQgis4EnumCompat:
    @pytest.mark.parametrize("pattern, replacement", FORBIDDEN_QGIS3_ENUMS)
    def test_no_plugin_file_uses_the_qgis3_only_spelling(self, pattern, replacement):
        compiled = re.compile(pattern)
        offenders = []
        for path in _pluginSourceFiles():
            with open(path, encoding="utf-8") as handle:
                for lineNumber, line in enumerate(handle, 1):
                    if compiled.search(line):
                        relative = os.path.relpath(path, PLUGIN_ROOT)
                        offenders.append(f"{relative}:{lineNumber}: {line.strip()}")

        assert not offenders, "use " + replacement + " instead:\n" + "\n".join(offenders)

    def test_the_legends_dialog_still_imports_the_shims(self):
        # It is the heaviest user of the symbol-layer properties, and the file a
        # rebase already reverted once.
        source = open(os.path.join(PLUGIN_ROOT, "ui", "project", "qgisred_legends_dialog.py"), encoding="utf-8").read()

        assert re.search(r"from \.\.\.compat import \(", source)
        for constant in ("SL_PROP_SIZE", "SL_PROP_FILL_COLOR", "SL_PROP_STROKE_COLOR", "QGIS_WARNING"):
            assert constant in source, constant
