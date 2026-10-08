# -*- coding: utf-8 -*-
"""Builds the default result styles, defaults/layerStyles/Node*.qml.bak and Link*.qml.bak.

Developer tool, not part of the plugin runtime. The Results dock shows every node
variable on one layer and every link variable on another, so all the styles share one
node symbol (tank and reservoir icons plus a junction circle) and one link symbol (line,
pump and valve icons, flow arrows); only the classes differ. The symbols live as text
templates in result_style_templates/ and the classes in RESULT_STYLES below, following
the spec "El panel de Resultados de QGISRed y sus estilos" (F. Martinez Alzamora, 2026):

- five classes in the EPANET colours (orange and red instead of yellow), the first one
  "below the lower threshold" and the last one "above the upper threshold";
- fixed thresholds for most variables, two sets where they depend on the unit system
  (files NodePressureSI / NodePressureUS...), one file per water quality kind;
- Pretty Breaks over the data for Head, Demand, Flow, Reaction rate and any chemical that
  is not chlorine: those files carry a legend strategy the plugin replays on every load,
  and their classes are only placeholders; the breaks of Demand come from the absolute
  values of the junctions and those of Head ignore the reservoirs, and Demand keeps a
  white, larger class below zero like the pressures;
- Status as three groups of EPANET states: Open, Active, Closed.

Run it after changing RESULT_STYLES or a template:

    python scripts/build_result_styles.py
"""

import base64
import colorsys
import json
import os
import uuid
from xml.sax.saxutils import escape

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES_DIR = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "result_style_templates")

# The results palette, low to high, as the style database ships it (build_style_db.py).
PALETTE = ("#004eff", "#00ffff", "#00ff00", "#ffd800", "#ff3800")
PALETTE_NAME = "QGISRed EPANET Results"
NEGATIVE_COLOR = "#ffffff"

# Sizes in millimetres, a little above the input layers so results draw over them.
JUNCTION_SIZE = 2
NEGATIVE_PRESSURE_SIZE = 3
NEGATIVE_DEMAND_SIZE = 3.5
SPECIAL_SIZE = 8       # tanks and reservoirs
LINE_WIDTH = 0.7
ICON_SIZE = 7          # pumps and valves

# Sentinel of an open-ended class, the one the plugin's rule parsing expects.
OPEN_BOUND = 1e10

# Upper bound of the class below zero of a Pretty Breaks style (half of the last decimal).
NEGATIVE_UPPER = -0.005

# Values a wizard samples on the node layer: NULL (ignored) for the node types named first.
NODE_VALUES_EXCEPT = "if(coalesce(\"NodeType\", \"Type\") in ('%s'), NULL, %s)"

# Status groups: label, filter pattern, colour (the "QGISRed Link Status" palette colours).
STATUS_CLASSES = (
    ("Open", "Open%", "#00ff00"),
    ("Active", "Active%", "#ffd800"),
    ("Closed", "%Closed%", "#ff3800"),
)

# Sizes the templates state (the shipped NodePressure / LinkFlow symbols they were cut from).
TEMPLATE_JUNCTION_SIZE = "2"
TEMPLATE_SPECIAL_SIZE = "7"
TEMPLATE_LINE_WIDTH = "0.26"
TEMPLATE_ICON_SIZE = "6"
TEMPLATE_COLOR = "0,0,255,255,rgb:0,0,1,1"
TEMPLATE_FRAME_COLOR = "0,0,159,255,rgb:0,0,0.6249943,1"

ICON_FILES = {
    # Node icons are stored with LF line ends inside the style, link icons as they are.
    "SVG_TANK_WATER": ("tanksResults_water.svg", True),
    "SVG_TANK_FRAME": ("tanksResults_frame.svg", True),
    "SVG_RESERVOIR_WATER": ("reservoirsResults_water.svg", True),
    "SVG_RESERVOIR_FRAME": ("reservoirsResults_frame.svg", True),
    "SVG_PUMP": ("pumps.svg", False),
    "SVG_VALVE": ("valves.svg", False),
    "SVG_ARROW": ("arrow.svg", False),
}


def fixedStyle(name, element, identifier, breaks, minimum, maximum, shift, negativeClass=False):
    """A style with fixed thresholds.

    `breaks` are the thresholds between classes; the first class starts at `minimum` and
    the last one ends at `maximum`. Inner bounds sit `shift` below the threshold (half of
    the last displayed decimal) so a value exactly on a threshold reads in the upper
    class, as the labels "15 < 30" say. `negativeClass` adds a white, larger first class
    for values below zero (pressures).
    """
    return {"name": name, "element": element, "identifier": identifier, "kind": "fixed", "breaks": breaks,
            "minimum": minimum, "maximum": maximum, "shift": shift, "negativeClass": negativeClass}


def prettyStyle(name, element, identifier, field, sampleField=None, negativeClass=False):
    """A style whose five classes are Pretty Breaks over the data, recomputed on every load.

    `sampleField` is the expression the breaks are computed over when it differs from
    the classified `field` (absolute demands of the junctions only, heads without the
    reservoirs). `negativeClass` keeps a white, larger first class below zero.
    """
    return {"name": name, "element": element, "identifier": identifier, "kind": "pretty", "field": field,
            "sampleField": sampleField, "negativeClass": negativeClass}


def qualityStyles(element):
    identifier = "qgisred_%s_quality" % element.lower()
    return (
        fixedStyle(element + "Chlorine", element, identifier, (0.2, 0.4, 0.6, 0.8), 0, 2, 0.005),
        prettyStyle(element + "Chemical", element, identifier, "Quality"),
        fixedStyle(element + "Trace", element, identifier, (20, 40, 60, 80), 0, 100, 0.05),
        fixedStyle(element + "Age", element, identifier, (12, 24, 48, 72), 0, 1000, 0.05),
    )


# Shifts: half of the last decimal shown for the variable (defaults/qgisred_properties_units_decimals.csv;
# pressures and flows take theirs from the Global PressUnits / FlowUnits rows: 2 decimals).
RESULT_STYLES = (
    fixedStyle("NodePressureSI", "Node", "qgisred_node_pressure", (0, 15, 30, 40, 50), -1000, 200, 0.005, True),
    fixedStyle("NodePressureUS", "Node", "qgisred_node_pressure", (0, 20, 40, 60, 70), -1000, 300, 0.005, True),
    prettyStyle("NodeHead", "Node", "qgisred_node_head", "Head",
                sampleField=NODE_VALUES_EXCEPT % ("RESERVOIR", '"Head"')),
    prettyStyle("NodeDemand", "Node", "qgisred_node_demand", "Demand",
                sampleField=NODE_VALUES_EXCEPT % ("TANK','RESERVOIR", 'abs("Demand")'), negativeClass=True),
) + qualityStyles("Node") + (
    prettyStyle("LinkFlow", "Link", "qgisred_link_flow", "abs(Flow)"),
    fixedStyle("LinkVelocitySI", "Link", "qgisred_link_velocity", (0.25, 0.5, 0.75, 1), 0, 10, 0.005),
    fixedStyle("LinkVelocityUS", "Link", "qgisred_link_velocity", (0.75, 1.5, 2.25, 3), 0, 30, 0.005),
    fixedStyle("LinkHeadLossSI", "Link", "qgisred_link_headloss", (0.1, 0.5, 1, 2), 0, 50, 0.005),
    fixedStyle("LinkHeadLossUS", "Link", "qgisred_link_headloss", (0.3, 1.5, 3, 6), 0, 150, 0.005),
    fixedStyle("LinkUnitHdLoss", "Link", "qgisred_link_unitheadloss", (0.5, 1, 2, 5), 0, 50, 0.005),
    fixedStyle("LinkFricFactor", "Link", "qgisred_link_frictionfactor", (0.01, 0.015, 0.02, 0.03), 0, 1, 0.0005),
    prettyStyle("LinkReactRate", "Link", "qgisred_link_reactionrate", "ReactRate"),
) + qualityStyles("Link") + (
    {"name": "LinkStatus", "element": "Link", "identifier": "qgisred_link_status", "kind": "status"},
)


def readTemplate(name):
    with open(os.path.join(TEMPLATES_DIR, name), encoding="utf-8", newline="") as handle:
        return handle.read().replace("\r\n", "\n")


def iconBase64(fileName, normaliseLineEnds):
    with open(os.path.join(STYLES_DIR, "icons", fileName), "rb") as handle:
        data = handle.read()
    if normaliseLineEnds:
        data = data.replace(b"\r\n", b"\n")
    return base64.b64encode(data).decode("ascii")


def formatNumber(value):
    text = "%.15g" % float(value)
    return "0" if text == "-0" else text


def colorText(hexColor):
    """A colour as QGIS writes it: r,g,b,255,rgb:rf,gf,bf,1."""
    channels = tuple(int(hexColor[index:index + 2], 16) for index in (1, 3, 5))
    floats = ",".join(formatNumber(round(channel / 255.0, 7)) for channel in channels)
    return "%d,%d,%d,255,rgb:%s,1" % (channels + (floats,))


def frameColor(hexColor):
    """The darker shade of the tank/reservoir frame: the colour at 1/1.6 of its HSV value (QColor.darker(160))."""
    channels = [int(hexColor[index:index + 2], 16) / 255.0 for index in (1, 3, 5)]
    hue, saturation, value = colorsys.rgb_to_hsv(*channels)
    darker = colorsys.hsv_to_rgb(hue, saturation, value / 1.6)
    return "#%02x%02x%02x" % tuple(int(round(channel * 255)) for channel in darker)


def spanColor(index, count):
    """Palette colour of class `index` out of `count`, spread as the Span palettes are."""
    if count <= 1:
        return PALETTE[0]
    position = index * (len(PALETTE) - 1) / float(count - 1)
    if count <= len(PALETTE):
        return PALETTE[int(round(position))]
    lower = int(position)
    share = position - lower
    if lower + 1 >= len(PALETTE):
        return PALETTE[lower]
    first = [int(PALETTE[lower][i:i + 2], 16) for i in (1, 3, 5)]
    second = [int(PALETTE[lower + 1][i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(round(a + (b - a) * share)) for a, b in zip(first, second))


def stableUuid(*parts):
    return "{%s}" % uuid.uuid5(uuid.NAMESPACE_URL, "qgisred-result-style/" + "/".join(str(part) for part in parts))


def classSymbol(element, index, hexColor, junctionSize=JUNCTION_SIZE):
    block = readTemplate(element.lower() + "_class.xml")
    for key, (fileName, normalise) in ICON_FILES.items():
        block = block.replace("{" + key + "}", iconBase64(fileName, normalise))
    block = block.replace('name="0" force_rhr="0"', 'name="%d" force_rhr="0"' % index)
    block = block.replace('name="@0@', 'name="@%d@' % index)
    if element == "Node":
        block = block.replace(TEMPLATE_FRAME_COLOR, colorText(frameColor(hexColor)))
        block = block.replace(TEMPLATE_COLOR, colorText(hexColor))
        block = block.replace("'TANK', %s,0))" % TEMPLATE_SPECIAL_SIZE, "'TANK', %s,0))" % formatNumber(SPECIAL_SIZE))
        block = block.replace("'RESERVOIR', %s,0))" % TEMPLATE_SPECIAL_SIZE,
                              "'RESERVOIR', %s,0))" % formatNumber(SPECIAL_SIZE))
        block = block.replace('value="%s" type="QString" name="size"' % TEMPLATE_JUNCTION_SIZE,
                              'value="%s" type="QString" name="size"' % formatNumber(junctionSize))
        block = block.replace("'TANK', 0,%s))" % TEMPLATE_JUNCTION_SIZE, "'TANK', 0,%s))" % formatNumber(junctionSize))
    else:
        block = block.replace(TEMPLATE_COLOR, colorText(hexColor))
        block = block.replace('name="line_width" value="%s"' % TEMPLATE_LINE_WIDTH,
                              'name="line_width" value="%s"' % formatNumber(LINE_WIDTH))
        for icon in ("PUMP", "VALVE"):
            block = block.replace("='%s', %s, 0))" % (icon, TEMPLATE_ICON_SIZE),
                                  "='%s', %s, 0))" % (icon, formatNumber(ICON_SIZE)))
    return block


def fixedClasses(spec):
    """(lower, upper, label, colour, junction size) of every class of a fixed-threshold style."""
    breaks = list(spec["breaks"])
    bounds = [spec["minimum"]] + [value - spec["shift"] for value in breaks] + [spec["maximum"]]
    texts = [formatNumber(value) for value in breaks]
    labels = ["< " + texts[0]] + ["%s < %s" % pair for pair in zip(texts, texts[1:])] + ["> " + texts[-1]]
    colorCount = len(labels)
    colors = [spanColor(index, colorCount) for index in range(colorCount)]
    sizes = [JUNCTION_SIZE] * colorCount
    if spec["negativeClass"]:
        # The class below zero: white and larger.
        colors = [NEGATIVE_COLOR] + [spanColor(index, colorCount - 1) for index in range(colorCount - 1)]
        sizes[0] = NEGATIVE_PRESSURE_SIZE
    return [(bounds[i], bounds[i + 1], labels[i], colors[i], sizes[i]) for i in range(colorCount)]


def prettyClasses(spec):
    """Placeholder classes of a Pretty Breaks style: replaced from the data on every load.

    The class below zero is not a placeholder: the replay keeps it as the file states it.
    """
    count = len(PALETTE)
    classes = [(index, index + 1, "%d - %d" % (index, index + 1), PALETTE[index], JUNCTION_SIZE)
               for index in range(count)]
    if spec["negativeClass"]:
        classes.insert(0, (-OPEN_BOUND, NEGATIVE_UPPER, "< 0", NEGATIVE_COLOR, NEGATIVE_DEMAND_SIZE))
    return classes


def rangeLine(spec, index, lower, upper, label):
    return ('      <range lower="%s" label="%s" upper="%s" symbol="%d" render="true" uuid="%s"/>\n'
            % (formatNumber(lower), escape(label), formatNumber(upper), index, stableUuid(spec["name"], index)))


def presetRampXml():
    options = []
    for index, color in enumerate(PALETTE):
        options.append('        <Option value="%s" type="QString" name="preset_color_%d"/>\n'
                       % (colorText(color).split(",rgb:")[0], index))
        options.append('        <Option value="%d" type="QString" name="preset_color_name_%d"/>\n' % (index + 1, index))
    options.append('        <Option value="preset" type="QString" name="rampType"/>\n')
    return ('    <colorramp type="preset" name="[source]">\n      <Option type="Map">\n%s      </Option>\n'
            '    </colorramp>\n' % "".join(options))


RENDERER_TAIL = '''    <rotation/>
    <sizescale/>
    <data-defined-properties>
      <Option type="Map">
        <Option value="" type="QString" name="name"/>
        <Option name="properties"/>
        <Option value="collection" type="QString" name="type"/>
      </Option>
    </data-defined-properties>
  </renderer-v2>
'''


def classificationMethodXml(methodId):
    return ('    <classificationMethod id="%s">\n'
            '      <symmetricMode symmetrypoint="0" enabled="0" astride="0"/>\n'
            '      <labelFormat trimtrailingzeroes="1" format="%%1 - %%2" labelprecision="4"/>\n'
            '      <parameters>\n        <Option/>\n      </parameters>\n'
            '      <extraInformation/>\n    </classificationMethod>\n' % methodId)


def graduatedRenderer(spec, attribute, classes, methodId, withRamp):
    ranges = "".join(rangeLine(spec, index, lower, upper, label)
                     for index, (lower, upper, label, _color, _size) in enumerate(classes))
    symbols = "".join(classSymbol(spec["element"], index, color, size)
                      for index, (_lower, _upper, _label, color, size) in enumerate(classes))
    return ('  <renderer-v2 forceraster="0" referencescale="-1" attr="%s" type="graduatedSymbol" symbollevels="0"'
            ' graduatedMethod="GraduatedColor" enableorderby="0">\n    <ranges>\n%s    </ranges>\n'
            '    <symbols>\n%s    </symbols>\n%s%s%s'
            % (escape(attribute), ranges, symbols, presetRampXml() if withRamp else "",
               classificationMethodXml(methodId), RENDERER_TAIL))


def statusRenderer(spec):
    rules = "".join(
        '      <rule key="%s" symbol="%d" filter="%s" label="%s"/>\n'
        % (stableUuid(spec["name"], index), index,
           escape('"Status" LIKE \'%s\'' % pattern, {'"': "&quot;"}), label)
        for index, (label, pattern, _color) in enumerate(STATUS_CLASSES))
    symbols = "".join(classSymbol("Link", index, color)
                      for index, (_label, _pattern, color) in enumerate(STATUS_CLASSES))
    return ('  <renderer-v2 enableorderby="0" forceraster="0" symbollevels="0" referencescale="-1"'
            ' type="RuleRenderer">\n'
            '    <rules key="%s">\n%s    </rules>\n    <symbols>\n%s    </symbols>\n%s'
            % (stableUuid(spec["name"], "rules"), rules, symbols, RENDERER_TAIL))


def legendStrategy(spec):
    intervals = {"classificationMode": "Pretty", "classes": len(PALETTE)}
    if spec["sampleField"]:
        intervals["sampleField"] = spec["sampleField"]
    if spec["negativeClass"]:
        intervals["negativeClass"] = True
    return {
        "schema": "qgisred.legendStrategy.v2",
        "mode": "graduated",
        "field": spec["field"],
        "parts": ["intervals", "colors"],
        "intervals": intervals,
        "colors": {"source": "ramp", "rampName": PALETTE_NAME, "invertRamp": False},
    }


def tailXml(spec):
    tail = readTemplate(spec["element"].lower() + "_tail.xml")
    if spec["element"] == "Node":
        identifierLine = '      <Option value="%s" type="QString" name="qgisred_identifier"/>\n'
        strategyLine = '      <Option value="%s" type="QString" name="qgisred_legend_strategy"/>\n'
        templateLine = identifierLine % "qgisred_node_pressure"
    else:
        identifierLine = '      <Option name="qgisred_identifier" value="%s" type="QString"/>\n'
        strategyLine = '      <Option name="qgisred_legend_strategy" value="%s" type="QString"/>\n'
        templateLine = identifierLine % "qgisred_link_flow"
    replacement = identifierLine % spec["identifier"]
    if spec["kind"] == "pretty":
        strategy = json.dumps(legendStrategy(spec), separators=(",", ":"))
        replacement += strategyLine % escape(strategy, {'"': "&quot;"})
    assert tail.count(templateLine) == 1
    return tail.replace(templateLine, replacement)


def renderStyle(spec):
    """The full text of one result style."""
    head = readTemplate(spec["element"].lower() + "_head.xml")
    if spec["kind"] == "fixed":
        renderer = graduatedRenderer(spec, classAttribute(spec), fixedClasses(spec), "Custom", False)
    elif spec["kind"] == "pretty":
        renderer = graduatedRenderer(spec, spec["field"], prettyClasses(spec), "Pretty", True)
    else:
        renderer = statusRenderer(spec)
    return head + renderer + tailXml(spec)


def classAttribute(spec):
    """Column a fixed style classifies by default; the dock sets the one on display anyway."""
    name = spec["name"][len(spec["element"]):]
    for suffix in ("SI", "US"):
        if name.endswith(suffix):
            name = name[:-len(suffix)]
    return {"Chlorine": "Quality", "Trace": "Quality", "Age": "Quality"}.get(name, name)


def buildStyles():
    for spec in RESULT_STYLES:
        path = os.path.join(STYLES_DIR, spec["name"] + ".qml.bak")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(renderStyle(spec))
        print("written", os.path.relpath(path, PLUGIN_ROOT))


if __name__ == "__main__":
    buildStyles()
