# -*- coding: utf-8 -*-
"""Builds the QGISRed content of defaults/symbology-style_QGISRed.db.

Developer tool, not part of the plugin runtime. The file is a QGIS style
database whose schema ships in git; this script refreshes only its QGISRed
content: the fixed pipe material colors (materialColors table) and the color
ramps and palettes offered by the Legends dialog, all tagged QGISRed. Run it
after changing MATERIAL_PALETTE, GRADIENT_RAMPS or PRESET_PALETTES:

    python scripts/build_style_db.py
"""

import os
import sqlite3

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(PLUGIN_ROOT, "defaults", "symbology-style_QGISRed.db")

# Fixed colors for the default Pipe Materials legend, so reloading the theme keeps
# the same color per material. Taken from the "Materiales" sheet of the
# Colores_Medidores_Materiales.xlsx spec: keys are the lowercase abbreviations and
# descriptions of every language (EN, ES, FR, PT). The spec guarantees that no
# abbreviation is reused for a different material across languages, so all of
# them map together. Anything else still gets a random color. Only the shipped
# default style uses this palette — project and global styles saved from the
# Legends dialog keep their own colors.
MATERIAL_PALETTE = (
    (("ci", "cast iron", "fg", "fundición gris", "fonte grise", "ff", "ferro fundido cinzento"), "#d0d0d0"),
    (("di", "ductile iron", "fd", "fundición dúctil", "fonte ductile", "ffd", "ferro fundido dúctil"), "#c6c5ba"),
    (("st", "steel", "ace", "acero", "aci", "acier", "aço"), "#a6a6a6"),
    (("sst", "stainless steel", "inox", "acero inoxidable", "acier inoxydable", "aço inoxidável"), "#9898b4"),
    (("ac", "asbestos cement", "fc", "fibrocemento", "amiante-ciment", "fibrocimento"), "#fff90f"),
    (("gi", "galvanized iron", "agal", "acero galvanizado", "ag", "acier galvanisé", "fgal", "ferro galvanizado"), "#b5c8e9"),
    (("cwsmj", "concrete with sheet metal jacket", "hccc", "hormigón con camisa de chapa",
      "bat", "béton à âme en tôle", "ccca", "concreto com cilindro de aço"), "#ffc000"),
    (("cwosmj", "concrete without sheet metal jacket", "hscc", "hormigón sin camisa de chapa",
      "bsat", "béton sans âme en tôle", "csca", "concreto sem cilindro de aço"), "#ffd54f"),
    (("rfc", "reinforced concrete pipe", "har", "hormigón armado", "ba", "béton armé", "ca", "concreto armado"), "#cece2c"),
    (("pc", "prestessed concrete", "hpr", "hormigón pretensado", "bp", "béton précontraint", "cp", "concreto protendido"), "#aba824"),
    (("l", "lead", "pb", "plomo", "plomb", "chumbo"), "#ff0000"),
    (("pvc", "polyvinyl chloride", "policloruro de vinilo", "polychlorure de vinyle", "policloreto de vinila"), "#94dcf8"),
    (("pe", "polyethylene", "polietileno", "polyéthylène"), "#a86ed4"),
    (("pvc-o", "orientated pvc", "pvc orientado", "pvc orienté"), "#52c6f4"),
    (("pvc-unp", "unplasticized pvc", "pvc-r", "pvc rígido", "pvc-u", "pvc non plastifié", "pvc não plastificado"), "#73a3f1"),
    (("cu", "cooper", "cobre", "cuivre"), "#83e28e"),
    (("hdpe", "hight density polyethylene", "pe-ad", "polietileno alta densidad",
      "pehd", "polyéthylène haute densité", "pead", "polietileno de alta densidade"), "#a83bb3"),
    (("ldpe", "low density polyethylene", "pe-bd", "polietileno baja densidad",
      "pebd", "polyéthylène basse densité", "polietileno de baixa densidade"), "#d697dd"),
    (("mdpe", "medium density polyethylene", "pe-md", "polietileno media densidad",
      "pemd", "polyéthylène moyenne densité", "polietileno de média densidade"), "#c76ed0"),
    (("frp", "fiberglass reinforced polyester", "prfv", "poliester reforzado con fibra de vidrio",
      "polyester renforcé de fibre de verre", "poliéster reforçado com fibra de vidro"), "#bfadbd"),
    (("#na", "not available", "no disponible", "non disponible", "não disponível"), "#e8e8e8"),
)

# Gradient ramps for the Legends dialog "Ramp" color mode, as (name, stops) with
# stops as (offset, hex). Ramp names are stable identifiers stored in saved
# legend strategies, so they are never renamed lightly.
GRADIENT_RAMPS = (
    ("QGISRed Elevation", ((0.0, "#446ee7"), (0.25, "#7bddee"), (0.5, "#84f71e"), (0.75, "#f7ba22"), (1.0, "#f21835"))),
    ("QGISRed Pressure", ((0.0, "#d7191c"), (0.25, "#fdae61"), (0.5, "#ffffbf"), (0.75, "#abd9e9"), (1.0, "#2c7bb6"))),
    ("QGISRed Velocity", ((0.0, "#ffffb2"), (0.25, "#fecc5c"), (0.5, "#fd8d3c"), (0.75, "#f03b20"), (1.0, "#bd0026"))),
    ("QGISRed Blue to Green", ((0.0, "#4574e7"), (1.0, "#bcdc3c"))),
    ("QGISRed Grayscale", ((0.0, "#f0f0f0"), (1.0, "#252525"))),
)

# Preset palettes for the Legends dialog "Palette" color mode. The first three
# mirror the shipped thematic legend colors.
PRESET_PALETTES = (
    ("QGISRed Pipe Diameters", ("#cdcae2", "#2abad4", "#8f5cd9", "#6ac12b", "#cbe314", "#ffcc4a", "#ff0000")),
    ("QGISRed Pipe Ages", ("#9dcbe7", "#579eca", "#abdda4", "#fdae61", "#ec6b6d", "#444444", "#d3d3d3")),
    ("QGISRed Pipe Roughness", ("#b72dcc", "#446ee7", "#2dcae5", "#7cd76c", "#f6cb5e", "#fc3a54")),
    ("QGISRed Pipe Materials", tuple(color for _, color in MATERIAL_PALETTE)),
    ("QGISRed Qualitative 10", ("#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00",
                                "#a65628", "#f781bf", "#999999", "#66c2a5", "#ffd92f")),
)


def hexToRgbaValue(hexColor):
    return "%d,%d,%d,255" % (int(hexColor[1:3], 16), int(hexColor[3:5], 16), int(hexColor[5:7], 16))


def gradientRampXml(name, stops):
    options = [
        '<Option type="QString" value="%s" name="color1"/>' % hexToRgbaValue(stops[0][1]),
        '<Option type="QString" value="%s" name="color2"/>' % hexToRgbaValue(stops[-1][1]),
        '<Option type="QString" value="0" name="discrete"/>',
        '<Option type="QString" value="gradient" name="rampType"/>',
    ]
    innerStops = stops[1:-1]
    if innerStops:
        stopsValue = ":".join("%s;%s" % (offset, hexToRgbaValue(color)) for offset, color in innerStops)
        options.append('<Option type="QString" value="%s" name="stops"/>' % stopsValue)
    return '<colorramp type="gradient" name="%s"><Option type="Map">%s</Option></colorramp>' % (name, "".join(options))


def presetRampXml(name, colors):
    options = []
    for index, color in enumerate(colors):
        options.append('<Option type="QString" value="%s" name="preset_color_%d"/>' % (hexToRgbaValue(color), index))
        options.append('<Option type="QString" value="%s" name="preset_color_name_%d"/>' % (color, index))
    options.append('<Option type="QString" value="preset" name="rampType"/>')
    return '<colorramp type="preset" name="%s"><Option type="Map">%s</Option></colorramp>' % (name, "".join(options))


def materialColorRows():
    rows = []
    for names, color in MATERIAL_PALETTE:
        for name in names:
            rows.append((name, color))
    return rows


def buildDatabase():
    if not os.path.exists(DATABASE_PATH):
        raise SystemExit("Style database not found: %s (its QGIS style schema ships in git)" % DATABASE_PATH)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("DROP TABLE IF EXISTS themeColors")
    connection.execute("DROP TABLE IF EXISTS materialColors")
    connection.execute("CREATE TABLE materialColors (label TEXT PRIMARY KEY, color TEXT NOT NULL)")
    connection.executemany("INSERT INTO materialColors (label, color) VALUES (?, ?)", materialColorRows())
    for table in ("symbol", "colorramp", "tag", "tagmap", "ctagmap"):
        connection.execute("DELETE FROM %s" % table)
    tagId = connection.execute("INSERT INTO tag (name) VALUES ('QGISRed')").lastrowid
    ramps = [(name, gradientRampXml(name, stops)) for name, stops in GRADIENT_RAMPS]
    ramps += [(name, presetRampXml(name, colors)) for name, colors in PRESET_PALETTES]
    for name, xml in ramps:
        rampId = connection.execute("INSERT INTO colorramp (name, xml, favorite) VALUES (?, ?, 0)", (name, xml)).lastrowid
        connection.execute("INSERT INTO ctagmap (tag_id, colorramp_id) VALUES (?, ?)", (tagId, rampId))
    connection.commit()
    print("materialColors: %d aliases" % connection.execute("SELECT COUNT(*) FROM materialColors").fetchone()[0])
    print("colorramp: %d ramps" % len(ramps))
    connection.close()
    print("Database written to %s" % DATABASE_PATH)


if __name__ == "__main__":
    buildDatabase()
