# -*- coding: utf-8 -*-
"""Checks that the plugin applies the spec "The QGISRed Results Panel and its styles" (F. Martinez
Alzamora, September 2026): palette, ranges, labels, sizes, file names and legend strategies.

Every check loads the shipped style through the plugin's own loader, the one the Results
dock uses, onto a memory layer carrying result fields, then reads what QGIS really built:
renderer, classes, evaluated symbol sizes. Nothing is parsed from the XML by hand.

Run it on its own with the QGIS Python (no QGIS window needed):

    "C:\\Program Files\\QGIS 3.40.0\\bin\\python-qgis.bat" scripts\\check_result_styles_spec.py

or paste it into the QGIS Python console:

    exec(open(r"<plugin folder>\\scripts\\check_result_styles_spec.py", encoding="utf-8").read())

It prints one line per check and ends with a summary; the exit code is 1 when a check fails.
Lines starting with NOTE are decisions taken where the document is open or inconsistent.
"""
import json
import os
import re
import sys
import tempfile

STANDALONE = __name__ == "__main__"
if STANDALONE:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from qgis.core import (  # noqa: E402
    QgsApplication, QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField,
    QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer, QgsExpressionContext, QgsExpressionContextScope,
    QgsExpressionContextUtils, QgsRenderContext, Qgis,
)
from qgis.PyQt.QtGui import QColor  # noqa: E402

if QgsApplication.instance() is None:
    APP = QgsApplication([], False)
    APP.initQgis()

def findPluginRoot():
    """The plugin folder: beside this script, or the loaded plugin's when the console runs a temp copy."""
    if "__file__" in globals():
        candidate = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.path.isdir(os.path.join(candidate, "defaults", "layerStyles")):
            return candidate
    from qgis.utils import plugins
    return os.path.dirname(os.path.abspath(sys.modules[plugins["QGISRed"].__module__].__file__))


PLUGIN_ROOT = findPluginRoot()
if os.path.dirname(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, os.path.dirname(PLUGIN_ROOT))

from QGISRed.compat import QVariantDouble, QVariantString, RENDER_UNIT_MILLIMETERS, SL_PROP_SIZE  # noqa: E402
from QGISRed.tools.utils.qgisred_styling_utils import QGISRedStylingUtils, PALETTE_KIND_SPAN  # noqa: E402
from QGISRed.ui.analysis.qgisred_results_data import resultStyleName  # noqa: E402

STYLES_FOLDER = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")

# ---------------------------------------------------------------- the document, as data
PALETTE = ["#004eff", "#00ffff", "#00ff00", "#ffd800", "#ff3800"]
PALETTE_NAME = "QGISRed EPANET Results"
NEGATIVE_COLOR = "#ffffff"

RESULT_SIZES = {"junction": 2.0, "negativePressure": 3.0, "negativeDemand": 3.5, "tankReservoir": 8.0, "line": 0.7,
                "pumpValve": 7.0}
DATA_SIZES = {"junction": 1.6, "tankReservoir": 7.0, "line": 0.5, "pumpValve": 6.0}

# name: (field the dock classifies, thresholds, minimum, maximum)
FIXED_STYLES = {
    "NodePressureSI": ("Pressure", (15, 30, 40, 50), -1000, 200),
    "NodePressureUS": ("Pressure", (20, 40, 60, 70), -1000, 300),
    "NodeChlorine": ("Quality", (0.2, 0.4, 0.6, 0.8), 0, 2),
    "NodeTrace": ("Quality", (20, 40, 60, 80), 0, 100),
    "NodeAge": ("Quality", (12, 24, 48, 72), 0, 1000),
    "LinkVelocitySI": ("Velocity", (0.25, 0.5, 0.75, 1), 0, 10),
    "LinkVelocityUS": ("Velocity", (0.75, 1.5, 2.25, 3), 0, 30),
    "LinkHeadLossSI": ("HeadLoss", (0.1, 0.5, 1, 2), 0, 50),
    "LinkHeadLossUS": ("HeadLoss", (0.3, 1.5, 3, 6), 0, 150),
    "LinkUnitHdLoss": ("UnitHdLoss", (0.5, 1, 2, 5), 0, 50),
    "LinkFricFactor": ("FricFactor", (0.01, 0.015, 0.02, 0.03), 0, 1),
    "LinkChlorine": ("Quality", (0.2, 0.4, 0.6, 0.8), 0, 2),
    "LinkTrace": ("Quality", (20, 40, 60, 80), 0, 100),
    "LinkAge": ("Quality", (12, 24, 48, 72), 0, 1000),
}
NEGATIVE_PRESSURE_STYLES = ("NodePressureSI", "NodePressureUS")

# name: field the dock classifies with Pretty Breaks, 5 intervals
PRETTY_STYLES = {
    "NodeHead": "Head", "NodeDemand": "Demand", "NodeChemical": "Quality",
    "LinkFlow": "abs(Flow)", "LinkReactRate": "ReactRate", "LinkChemical": "Quality",
}

NEGATIVE_DEMAND_STYLES = ("NodeDemand",)

# name: expression any wizard samples (absolute demands of the junctions, heads without the reservoirs)
SAMPLE_FIELDS = {
    "NodeHead": "if(coalesce(\"NodeType\", \"Type\") in ('RESERVOIR'), NULL, \"Head\")",
    "NodeDemand": "if(coalesce(\"NodeType\", \"Type\") in ('TANK','RESERVOIR'), NULL, abs(\"Demand\"))",
}

STATUS_CLASSES = [("Open", "#00ff00"), ("Active", "#ffd800"), ("Closed", "#ff3800")]

# (project units entry, quality model, chemical label) -> style name the dock must ask for
FILE_NAME_CASES = [
    (("LPS", "Chemical", "Chlorine"), "Node", "Pressure", "NodePressureSI"),
    (("GPM", "Chemical", "Chlorine"), "Node", "Pressure", "NodePressureUS"),
    (("CMH", "Chemical", "Chlorine"), "Node", "Pressure", "NodePressureSI"),
    (("MGD", "Chemical", "Chlorine"), "Node", "Pressure", "NodePressureUS"),
    (("LPS", "Chemical", "Chlorine"), "Node", "Head", "NodeHead"),
    (("LPS", "Chemical", "Chlorine"), "Node", "Demand", "NodeDemand"),
    (("LPS", "Chemical", "Chlorine"), "Node", "Quality", "NodeChlorine"),
    (("LPS", "Chemical", "Cloro"), "Node", "Quality", "NodeChlorine"),
    (("LPS", "Chemical", "Cl2"), "Node", "Quality", "NodeChlorine"),
    (("LPS", "Chemical", "Fluoride"), "Node", "Quality", "NodeChemical"),
    (("LPS", "Trace", ""), "Node", "Quality", "NodeTrace"),
    (("LPS", "Age", ""), "Node", "Quality", "NodeAge"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Flow", "LinkFlow"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Flow_Sig", "LinkFlow"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Flow_Unsig", "LinkFlow"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Velocity", "LinkVelocitySI"),
    (("GPM", "Chemical", "Chlorine"), "Link", "Velocity", "LinkVelocityUS"),
    (("LPS", "Chemical", "Chlorine"), "Link", "HeadLoss", "LinkHeadLossSI"),
    (("GPM", "Chemical", "Chlorine"), "Link", "HeadLoss", "LinkHeadLossUS"),
    (("LPS", "Chemical", "Chlorine"), "Link", "UnitHdLoss", "LinkUnitHdLoss"),
    (("LPS", "Chemical", "Chlorine"), "Link", "FricFactor", "LinkFricFactor"),
    (("LPS", "Chemical", "Chlorine"), "Link", "ReactRate", "LinkReactRate"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Quality", "LinkChlorine"),
    (("LPS", "Chemical", "Fluoride"), "Link", "Quality", "LinkChemical"),
    (("LPS", "Trace", ""), "Link", "Quality", "LinkTrace"),
    (("LPS", "Age", ""), "Link", "Quality", "LinkAge"),
    (("LPS", "Chemical", "Chlorine"), "Link", "Status", "LinkStatus"),
]

# ---------------------------------------------------------------- reporting
RESULTS = {"pass": 0, "fail": 0, "warn": 0}
LINES = []


def report(ok, text):
    RESULTS["pass" if ok else "fail"] += 1
    LINES.append(("PASS  " if ok else "FAIL  ") + text)


def note(text):
    LINES.append("NOTE  " + text)


def warn(text):
    RESULTS["warn"] += 1
    LINES.append("WARN  " + text)


def section(title):
    LINES.append("")
    LINES.append("=== " + title)


def same(a, b, tolerance=1e-6):
    return abs(float(a) - float(b)) <= tolerance


def hexColor(color):
    return QColor(color).name().lower()


# ---------------------------------------------------------------- layers with results
def addFeature(layer, geometry, values):
    feature = QgsFeature(layer.fields())
    feature.setGeometry(geometry)
    for name, value in values.items():
        feature[name] = value
    layer.dataProvider().addFeature(feature)


def resultLayer(element):
    if element == "Node":
        layer = QgsVectorLayer("Point?crs=EPSG:25830", "Nodes", "memory")
        names = ["Pressure", "Head", "Demand", "Quality"]
    else:
        layer = QgsVectorLayer("LineString?crs=EPSG:25830", "Links", "memory")
        names = ["Flow", "Flow_Sig", "Flow_Unsig", "Velocity", "HeadLoss", "UnitHdLoss", "FricFactor",
                 "ReactRate", "Quality"]
    fields = [QgsField("Id", QVariantString), QgsField("Type", QVariantString)]
    fields += [QgsField(name, QVariantDouble) for name in names]
    if element == "Link":
        fields.append(QgsField("Status", QVariantString))
    layer.dataProvider().addAttributes(fields)
    layer.updateFields()
    types = ["JUNCTION", "TANK", "RESERVOIR"] if element == "Node" else ["PIPE", "PUMP", "VALVE"]
    statuses = ["Open", "Active", "Closed", "Temporarily Closed", "Open"]
    for index in range(12):
        # Twelve spread values so Pretty Breaks has something to cut into five intervals.
        value = -5.0 + index * 18.3
        values = {"Id": "E%d" % index, "Type": types[index % 3]}
        for name in names:
            values[name] = value if name != "Flow_Sig" else -value
        if element == "Link":
            values["Status"] = statuses[index % 5]
        point = QgsPointXY(index * 10.0, index * 3.0)
        geometry = QgsGeometry.fromPointXY(point) if element == "Node" else QgsGeometry.fromPolylineXY(
            [point, QgsPointXY(index * 10.0 + 5.0, index * 3.0)])
        addFeature(layer, geometry, values)
    layer.updateExtents()
    return layer


def featureOfType(layer, typeName):
    return next(feature for feature in layer.getFeatures() if feature["Type"] == typeName)


# ---------------------------------------------------------------- reading what QGIS built
def evaluationContext(layer, feature):
    context = QgsExpressionContext(QgsExpressionContextUtils.globalProjectLayerScopes(layer))
    scope = QgsExpressionContextScope()
    scope.setVariable("id", feature.id())
    context.appendScope(scope)
    context.setFeature(feature)
    return context


def evaluatedSizes(symbol, context):
    """Sizes in symbol units every marker layer of `symbol` (and of its sub symbols) resolves to."""
    sizes = []
    for index in range(symbol.symbolLayerCount()):
        symbolLayer = symbol.symbolLayer(index)
        subSymbol = symbolLayer.subSymbol()
        if subSymbol is not None:
            sizes.extend(evaluatedSizes(subSymbol, context))
            continue
        if not hasattr(symbolLayer, "size"):
            continue
        sizeProperty = symbolLayer.dataDefinedProperties().property(SL_PROP_SIZE)
        if sizeProperty.isActive():
            value, ok = sizeProperty.valueAsDouble(context, symbolLayer.size())
            sizes.append(value if ok else symbolLayer.size())
        else:
            sizes.append(symbolLayer.size())
    return sizes


def drawnSize(symbol, layer, typeName):
    """Largest marker a feature of `typeName` draws with `symbol`, in millimetres."""
    context = evaluationContext(layer, featureOfType(layer, typeName))
    return max(evaluatedSizes(symbol, context) or [0.0])


def lineWidth(symbol):
    return symbol.symbolLayer(0).width()


def symbolUnits(symbol):
    units = set()
    for index in range(symbol.symbolLayerCount()):
        symbolLayer = symbol.symbolLayer(index)
        if hasattr(symbolLayer, "sizeUnit"):
            units.add(symbolLayer.sizeUnit())
        if hasattr(symbolLayer, "widthUnit"):
            units.add(symbolLayer.widthUnit())
        if symbolLayer.subSymbol() is not None:
            units |= symbolUnits(symbolLayer.subSymbol())
    return units


def classSymbols(renderer):
    """Clones: a symbol read from a temporary range dies with it and aborts the process."""
    if isinstance(renderer, QgsGraduatedSymbolRenderer):
        ranges = renderer.ranges()
        return [classRange.symbol().clone() for classRange in ranges]
    if isinstance(renderer, QgsRuleBasedRenderer):
        return [rule.symbol().clone() for rule in renderer.rootRule().children() if rule.symbol() is not None]
    return []


def loadShippedStyle(layer, name, field):
    """The plugin's own loader (the one setStyle ends in) over the shipped default file."""
    styling = QGISRedStylingUtils(tempfile.gettempdir(), "SpecCheck", None)
    path = os.path.join(STYLES_FOLDER, name + ".qml.bak")
    if not os.path.exists(path):
        report(False, "%s: shipped file %s is missing" % (name, os.path.basename(path)))
        return None
    resolved = styling.resolveStylePath(name + ".qml")
    if os.path.normcase(resolved) != os.path.normcase(path):
        note("%s: a saved user style would take over the shipped default: %s" % (name, resolved))
    styling._loadStyleFile(layer, path, field)
    return layer.renderer()


# ---------------------------------------------------------------- the checks
def checkPalette():
    section("Results palette in the style database")
    ramp = QGISRedStylingUtils.findColorRamp(PALETTE_NAME)
    report(ramp is not None, "palette '%s' exists in %s" % (PALETTE_NAME, QGISRedStylingUtils.styleDatabasePath()))
    if ramp is None:
        return
    colors = [hexColor(color) for color in ramp.colors()]
    report(colors == PALETTE, "palette colours low to high %s (orange and red, no yellow)" % colors)
    kind = QGISRedStylingUtils.findColorRampKind(PALETTE_NAME)
    report(kind == PALETTE_KIND_SPAN, "palette is expanded over the classes (kind '%s')" % kind)

    styling = QGISRedStylingUtils(tempfile.gettempdir(), "SpecCheck", None)

    def spread(count):
        return [hexColor(styling.rampClassColor(ramp, kind, "", index, count, False)) for index in range(count)]

    report(spread(1) == [PALETTE[0]], "one range takes the first colour: %s" % spread(1))
    report(spread(3) == [PALETTE[0], PALETTE[2], PALETTE[4]],
           "three ranges take first, middle and last colours: %s" % spread(3))
    report(spread(5) == PALETTE, "five ranges take the whole palette in order")
    nine = spread(9)
    presetKept = nine[0::2] == PALETTE
    blended = all(nine[index] not in PALETTE for index in range(1, 9, 2))
    report(presetKept and blended, "nine ranges keep the preset colours and interpolate between them: %s" % nine)


def checkFileNames():
    section("Style file the dock asks for (NodeVariable / LinkVariable, SI or US suffix)")
    project = QgsProject.instance()
    saved = {key: project.readEntry("QGISRed", key)[0]
             for key in ("project_units", "project_qualitymodel", "project_chemicallabel")}
    try:
        for (units, model, label), element, variable, expected in FILE_NAME_CASES:
            project.writeEntry("QGISRed", "project_units", units)
            project.writeEntry("QGISRed", "project_qualitymodel", model)
            project.writeEntry("QGISRed", "project_chemicallabel", label)
            name = resultStyleName(element, variable)
            exists = os.path.exists(os.path.join(STYLES_FOLDER, name + ".qml.bak"))
            report(name == expected and exists, "%s %-10s units=%s model=%s label=%-8s -> %s%s"
                   % (element, variable, units, model, label or "''", name, "" if exists else " (no file)"))
    finally:
        for key, value in saved.items():
            project.writeEntry("QGISRed", key, value)
    note("the document spells the suffix '_SI' / '_US'; the plugin ships 'SI' / 'US' without the underscore")


def checkSizes(name, layer, renderer, negativeSize=None):
    symbols = classSymbols(renderer)
    units = set()
    for symbol in symbols:
        units |= symbolUnits(symbol)
    report(units == {RENDER_UNIT_MILLIMETERS}, "%s: every size is in millimetres" % name)
    if name.startswith("Node"):
        junctionSizes = [drawnSize(symbol, layer, "JUNCTION") for symbol in symbols]
        expectedJunctions = [RESULT_SIZES["junction"]] * len(symbols)
        if negativeSize is not None:
            expectedJunctions[0] = negativeSize
        junctionsOk = all(same(a, b) for a, b in zip(junctionSizes, expectedJunctions))
        report(junctionsOk, "%s: junction circles draw %s mm" % (name, junctionSizes))
        for typeName in ("TANK", "RESERVOIR"):
            sizes = [drawnSize(symbol, layer, typeName) for symbol in symbols]
            report(all(same(size, RESULT_SIZES["tankReservoir"]) for size in sizes),
                   "%s: %s icons draw %s mm" % (name, typeName.lower(), sorted(set(sizes))))
    else:
        widths = [lineWidth(symbol) for symbol in symbols]
        report(all(same(width, RESULT_SIZES["line"]) for width in widths),
               "%s: lines draw %s mm wide" % (name, sorted(set(widths))))
        for typeName in ("PUMP", "VALVE"):
            sizes = [drawnSize(symbol, layer, typeName) for symbol in symbols]
            report(all(same(size, RESULT_SIZES["pumpValve"]) for size in sizes),
                   "%s: %s markers draw %s mm" % (name, typeName.lower(), sorted(set(sizes))))


def checkColors(name, renderer, expected):
    colors = [hexColor(symbol.color()) for symbol in classSymbols(renderer)]
    report(colors == expected, "%s: class colours %s" % (name, colors))


def checkFixedStyle(name, layer):
    field, thresholds, minimum, maximum = FIXED_STYLES[name]
    negative = name in NEGATIVE_PRESSURE_STYLES
    section(name)
    renderer = loadShippedStyle(layer, name, field)
    if renderer is None:
        return
    report(isinstance(renderer, QgsGraduatedSymbolRenderer), "%s: graduated legend" % name)
    if not isinstance(renderer, QgsGraduatedSymbolRenderer):
        return
    report(renderer.classAttribute() == field, "%s: classifies %s" % (name, renderer.classAttribute()))
    ranges = renderer.ranges()
    expectedCount = 5 + (1 if negative else 0)
    countText = " (5 plus the negative pressures)" if negative else ""
    report(len(ranges) == expectedCount, "%s: %d ranges%s" % (name, len(ranges), countText))
    if len(ranges) != expectedCount:
        return
    report(same(ranges[0].lowerValue(), minimum) and same(ranges[-1].upperValue(), maximum),
           "%s: first range starts at %g and last ends at %g" % (name, ranges[0].lowerValue(), ranges[-1].upperValue()))
    consecutive = all(same(ranges[i].upperValue(), ranges[i + 1].lowerValue()) for i in range(len(ranges) - 1))
    report(consecutive, "%s: ranges are consecutive" % name)
    innerBounds = [classRange.upperValue() for classRange in ranges[:-1]]
    wanted = ([0] if negative else []) + list(thresholds)
    # The bound sits just below the threshold, by half of the last decimal the variable displays.
    onThreshold = all(0 < threshold - bound <= 0.05 + 1e-9 for bound, threshold in zip(innerBounds, wanted))
    report(onThreshold, "%s: thresholds %s just above the bounds %s (a value on a threshold reads in the upper range)"
           % (name, wanted, ["%g" % bound for bound in innerBounds]))
    labels = [classRange.label() for classRange in ranges]
    texts = ["%g" % value for value in thresholds]
    expectedLabels = ["< " + texts[0]] + ["%s < %s" % pair for pair in zip(texts, texts[1:])] + ["> " + texts[-1]]
    if negative:
        expectedLabels = ["< 0", "0 < " + texts[0]] + expectedLabels[1:]
    report(labels == expectedLabels, "%s: labels %s" % (name, labels))
    checkColors(name, renderer, ([NEGATIVE_COLOR] if negative else []) + PALETTE)
    checkSizes(name, layer, renderer, negativeSize=RESULT_SIZES["negativePressure"] if negative else None)
    report(not layer.labelsEnabled(), "%s: no map labels switched on by the style" % name)


def checkPrettyStyle(name, layer):
    field = PRETTY_STYLES[name]
    section(name)
    renderer = loadShippedStyle(layer, name, field)
    if renderer is None:
        return
    report(isinstance(renderer, QgsGraduatedSymbolRenderer), "%s: graduated legend" % name)
    if not isinstance(renderer, QgsGraduatedSymbolRenderer):
        return
    report(renderer.classAttribute() == field, "%s: classifies %s" % (name, renderer.classAttribute()))
    method = renderer.classificationMethod().id()
    report(method == "Pretty", "%s: classification method '%s'" % (name, method))
    strategy = json.loads(layer.customProperty("qgisred_legend_strategy") or "{}")
    requested = strategy.get("intervals", {}).get("classes")
    report(requested == 5 and strategy.get("intervals", {}).get("classificationMode") == "Pretty",
           "%s: the style asks for Pretty Breaks in 5 intervals on every load" % name)
    negative = name in NEGATIVE_DEMAND_STYLES
    sampleField = strategy.get("intervals", {}).get("sampleField")
    if name in SAMPLE_FIELDS:
        report(sampleField == SAMPLE_FIELDS[name], "%s: the breaks are computed over %s" % (name, sampleField))
    allRanges = renderer.ranges()
    if negative:
        report(strategy.get("intervals", {}).get("negativeClass") is True and allRanges[0].label() == "< 0",
               "%s: the first range holds the negative demands (%s)" % (name, allRanges[0].label()))
    ranges = allRanges[1:] if negative else allRanges
    labels = [classRange.label() for classRange in ranges]
    if len(ranges) == 5:
        report(True, "%s: 5 intervals over the data on screen: %s" % (name, labels))
    else:
        warn("%s: QGIS Pretty Breaks cut the sample into %d intervals, not 5: %s (round numbers win over the count)"
             % (name, len(ranges), labels))
    if len(ranges) < 2:
        return
    consecutive = all(same(allRanges[i].upperValue(), allRanges[i + 1].lowerValue()) for i in range(len(allRanges) - 1))
    report(consecutive, "%s: ranges are consecutive" % name)
    openEnded = labels[0].startswith("< ") and labels[-1].startswith("> ")
    report(openEnded, "%s: first range is 'below', last is 'above' (%s ... %s)" % (name, labels[0], labels[-1]))
    actualColors = [hexColor(symbol.color()) for symbol in classSymbols(renderer)]
    expectedColors = ([NEGATIVE_COLOR] if negative else []) + PALETTE
    checkColors(name, renderer, expectedColors if len(ranges) == 5 else actualColors)
    checkSizes(name, layer, renderer, negativeSize=RESULT_SIZES["negativeDemand"] if negative else None)
    report(not layer.labelsEnabled(), "%s: no map labels switched on by the style" % name)


def checkStatus(layer):
    section("LinkStatus")
    renderer = loadShippedStyle(layer, "LinkStatus", "Status")
    if renderer is None:
        return
    report(isinstance(renderer, QgsRuleBasedRenderer), "LinkStatus: categorized by rules")
    if not isinstance(renderer, QgsRuleBasedRenderer):
        return
    rules = [rule for rule in renderer.rootRule().children() if rule.symbol() is not None]
    labels = [rule.label() for rule in rules]
    report(labels == [label for label, _ in STATUS_CLASSES], "LinkStatus: three categories %s" % labels)
    checkColors("LinkStatus", renderer, [color for _, color in STATUS_CLASSES])
    note("the document paints Closed 'green' like Open; the plugin paints it red, read as a typo in the document")
    context = QgsRenderContext()
    renderer.startRender(context, layer.fields())
    try:
        matched = {}
        for feature in layer.getFeatures():
            context.expressionContext().setFeature(feature)
            hits = [rule.label() for rule in rules if rule.isFilterOK(feature, context)]
            matched[feature["Status"]] = hits
    finally:
        renderer.stopRender(context)
    expected = {"Open": ["Open"], "Active": ["Active"], "Closed": ["Closed"], "Temporarily Closed": ["Closed"]}
    report(matched == expected, "LinkStatus: EPANET states fall in their group: %s" % matched)
    checkSizes("LinkStatus", layer, renderer)


def checkDataSizes():
    section("Input layer sizes the document compares against")

    def numberAfter(fileName, pattern):
        with open(os.path.join(STYLES_FOLDER, fileName), encoding="utf-8") as handle:
            match = re.search(pattern, handle.read(), re.S)
        return float(match.group(1)) if match else None

    found = {
        "junction": numberAfter("Junctions.qml.bak", r"with_variable\('junctionSize', ([0-9.]+)"),
        "tank": numberAfter("Tanks.qml.bak", r'class="SvgMarker".*?value="([0-9.]+)" name="size"'),
        "reservoir": numberAfter("Reservoirs.qml.bak", r'class="SvgMarker".*?value="([0-9.]+)" name="size"'),
        "line": numberAfter("Pipes.qml.bak", r'name="line_width" value="([0-9.]+)"'),
        "pump": numberAfter("Pumps.qml.bak", r'class="SvgMarker".*?name="size" value="([0-9.]+)"'),
        "valve": numberAfter("Valves.qml.bak", r'class="SvgMarker".*?name="size" value="([0-9.]+)"'),
    }
    expected = {"junction": DATA_SIZES["junction"], "tank": DATA_SIZES["tankReservoir"],
                "reservoir": DATA_SIZES["tankReservoir"], "line": DATA_SIZES["line"],
                "pump": DATA_SIZES["pumpValve"], "valve": DATA_SIZES["pumpValve"]}
    for key in expected:
        value = found[key]
        report(value is not None and same(value, expected[key]),
               "%s data size %s mm (document: %g mm, results draw slightly larger)" % (key, value, expected[key]))


def run():
    LINES.append("QGIS %s   plugin %s" % (Qgis.QGIS_VERSION, PLUGIN_ROOT))
    checkPalette()
    checkFileNames()
    nodeLayer = resultLayer("Node")
    linkLayer = resultLayer("Link")
    QgsProject.instance().addMapLayers([nodeLayer, linkLayer], False)
    for name in FIXED_STYLES:
        checkFixedStyle(name, nodeLayer if name.startswith("Node") else linkLayer)
    for name in PRETTY_STYLES:
        checkPrettyStyle(name, nodeLayer if name.startswith("Node") else linkLayer)
    checkStatus(linkLayer)
    checkDataSizes()
    QgsProject.instance().removeMapLayers([nodeLayer.id(), linkLayer.id()])
    section("Not checked")
    note("'Description of the Results Panel' and 'Map labels and notices' are still to be drafted in the document")
    note("the 13-state Status legend is a possible future proposal in the document, not a requirement")
    LINES.append("")
    LINES.append("%d checks passed, %d failed, %d warnings" % (RESULTS["pass"], RESULTS["fail"], RESULTS["warn"]))
    print("\n".join(LINES))
    return RESULTS["fail"] == 0


if STANDALONE:
    ok = run()
    sys.stdout.flush()
    os._exit(0 if ok else 1)
else:
    run()
