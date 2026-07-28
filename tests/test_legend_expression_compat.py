# -*- coding: utf-8 -*-
"""Guards for the two things a rebase silently reverted in the legends dialog.

Both were invisible to the suite: the QGIS 4 shims and the null-safe field
expressions have no behavioural test of their own, so a merge that restored the
QGIS 3 spellings passed green.
"""
import os
import re

import pytest

from QGISRed.ui.project.qgisred_legends_dialog import QGISRedLegendsDialog

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Color:
    """Minimal QColor stand-in: the real one is a MagicMock under the test env."""

    def __init__(self, hexName="#1f78b4", rgb=(31, 120, 180)):
        self._hex = hexName
        self._rgb = rgb

    def name(self):
        return self._hex

    def red(self):
        return self._rgb[0]

    def green(self):
        return self._rgb[1]

    def blue(self):
        return self._rgb[2]


def _dialogCapturingExpressions():
    """Bare dialog that records what it would write, instead of touching symbols."""
    dialog = QGISRedLegendsDialog.__new__(QGISRedLegendsDialog)
    captured = {}
    dialog._setExpressionOnLayers = lambda symbol, key, expression: captured.setdefault(key, []).append(expression)
    dialog._lightenColor = lambda color, fraction: _Color("#8fc4e0")
    return dialog, captured


def _allExpressions(captured):
    return [expression for perKey in captured.values() for expression in perKey]


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
    """

    def test_service_connections_fill_reads_both_demand_field_names(self):
        dialog, captured = _dialogCapturingExpressions()

        dialog._applyServiceConnectionsLegend(symbol=None, color=_Color(), size=None)

        demandExpressions = [e for e in _allExpressions(captured) if "BaseDem" in e]
        assert demandExpressions, "the fill expression no longer classifies on the demand field"
        for expression in demandExpressions:
            assert _coalescePattern("BaseDem", "BaseDemand").search(expression), expression

    def test_isolation_valves_fill_reads_both_status_field_names(self):
        dialog, captured = _dialogCapturingExpressions()

        dialog._applyIsolationValvesLegend(symbol=None, color=_Color(), size=None)

        statusExpressions = [e for e in _allExpressions(captured) if "Status" in e]
        assert statusExpressions, "the fill expression no longer classifies on the status field"
        for expression in statusExpressions:
            assert _coalescePattern("IniStatus", "Status").search(expression), expression

    @pytest.mark.parametrize("method, marker", [
        ("_applyServiceConnectionsLegend", "BaseDemand"),
        ("_applyIsolationValvesLegend", "Status"),
    ])
    def test_the_renamed_field_is_never_referenced_directly(self, method, marker):
        dialog, captured = _dialogCapturingExpressions()

        getattr(dialog, method)(symbol=None, color=_Color(), size=None)

        for expression in _allExpressions(captured):
            withoutCoalesce = re.sub(r"coalesce\([^)]*\)[^)]*\)", "", expression)
            assert f'"{marker}"' not in withoutCoalesce, expression
            assert not re.search(r"(?<![\w'])%s(?![\w'])" % marker, withoutCoalesce), expression


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
