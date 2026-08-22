# -*- coding: utf-8 -*-
"""Builds defaults/qgisred_theme_colors.db from the shipped thematic map styles.

Developer tool, not part of the plugin runtime. Run it after changing the class
colors of any thematic .qml.bak style so the shipped database stays in sync:

    python scripts/build_theme_colors_db.py
"""

import os
import re
import sqlite3
import xml.etree.ElementTree as ElementTree

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STYLES_FOLDER = os.path.join(PLUGIN_ROOT, "defaults", "layerStyles")
DATABASE_PATH = os.path.join(PLUGIN_ROOT, "defaults", "qgisred_theme_colors.db")

# Thematic map styles referenced by the Thematic Maps dialog (units variants of
# the same theme share one entry because only the class breaks change, not the
# colors). Junction_Elevations computes its breaks from the data, so its colors
# are applied by class position. Junction_TotalBaseDemands is excluded: its
# colors live in data-defined expressions, not renderer classes. PipeMaterials
# has no renderer in its qml; its palette is MATERIAL_PALETTE below.
THEMATIC_STYLE_FILES = [
    "Junction_Elevations.qml.bak",
    "PipeAges.qml.bak",
    "PipeDiametersSI.qml.bak",
    "PipeInstallationYears.qml.bak",
    "PipeLengthsSI.qml.bak",
    "PipeRoughnessesCM.qml.bak",
    "PipeRoughnessesDWSI.qml.bak",
    "PipeRoughnessesHW.qml.bak",
]

# Fixed colors for the default Pipe Materials legend, so reloading the theme keeps
# the same color per material. Built from the 19 materials in the Materials_*.dbf
# tables: keys are the lowercase abbreviations and descriptions from the EN/ES
# tables plus the FR/PT description names, grouped by color family (ferrous greys
# and blues, cement/concrete earth tones, plastics purples and greens). Anything
# else still gets a random color. The abbreviation "AC" exists in both tables
# (Asbestos Cement vs Acero) and can only carry one color: the asbestos-cement
# brown; the Spanish steel is still matched through its description. Only the
# shipped default style uses this palette — project and global styles saved from
# the Legends dialog keep their own colors.
MATERIAL_PALETTE = (
    (("ci", "cast iron", "fg", "fundición gris", "fonte grise", "ferro fundido"), "#4d4d4d"),
    (("di", "ductile iron", "fd", "fundición dúctil", "fonte ductile", "ferro dúctil"), "#1f78b4"),
    (("st", "steel", "acero", "acier", "aço"), "#8c9aa5"),
    (("sst", "stainless steel", "ain", "acero inoxidable", "acier inoxydable", "aço inoxidável"), "#a6cee3"),
    (("gi", "galvanized iron", "agal", "acero galvanizado", "acier galvanisé", "aço galvanizado"), "#8b6914"),
    (("ac", "asbestos cement", "fc", "fibrocemento", "amiante-ciment", "fibrocimento"), "#b15928"),
    (("cwsmj", "concrete with sheet metal jacket", "hca", "hormigón con armadura"), "#c8a165"),
    (("cwosmj", "concrete without sheet metal jacket", "hs", "hormigón sin revestimiento"), "#bfb08e"),
    (("rfc", "reinforced concrete pipe", "har", "hormigón armado", "béton armé", "concreto armado", "betão armado"), "#a08052"),
    (("pc", "prestessed concrete", "prestressed concrete", "hp", "hormigón pretensado",
      "béton précontraint", "concreto protendido", "betão pré-esforçado"), "#8a7048"),
    (("l", "lead", "pb", "plomo", "plomb", "chumbo"), "#4a4a6a"),
    (("pvc", "polyvinyl chloride", "policloruro de vinilo", "polychlorure de vinyle", "policloreto de vinila"), "#6a3d9a"),
    (("pvc-o", "orientated pvc", "pvc orientado", "pvc orienté"), "#9a5fd1"),
    (("pvc-unp", "unplasticized pvc", "pvc-r", "pvc rígido", "pvc rigide"), "#b57bd6"),
    (("pe", "polyethylene", "polietileno", "polyéthylène"), "#33a02c"),
    (("hdpe", "hight density polyethylene", "high density polyethylene", "pe-ad", "pead",
      "polietileno alta densidad", "polyéthylène haute densité", "polietileno de alta densidade"), "#1a7a1a"),
    (("ldpe", "low density polyethylene", "pe-bd", "pebd",
      "polietileno baja densidad", "polyéthylène basse densité", "polietileno de baixa densidade"), "#7fce6e"),
    (("mdpe", "medium density polyethylene", "pe-md", "pemd",
      "polietileno media densidad", "polyéthylène moyenne densité", "polietileno de média densidade"), "#4fb84a"),
    (("cu", "cooper", "copper", "cobre", "cuivre"), "#b87333"),
    (("unknown", "desconocido", "inconnu", "desconhecido"), "#c0c0c0"),
)


def themeKeyFromFileName(fileName):
    baseName = fileName
    for suffix in (".bak", ".qml"):
        if baseName.endswith(suffix):
            baseName = baseName[: -len(suffix)]
    baseName = re.sub(r"_?(SI|US)$", "", baseName)
    return baseName.lower()


def colorToHex(colorValue):
    parts = colorValue.split(",")
    if len(parts) >= 3:
        return "#%02x%02x%02x" % (int(parts[0]), int(parts[1]), int(parts[2]))
    return colorValue


def extractClassColors(qmlPath):
    tree = ElementTree.parse(qmlPath)
    renderer = tree.getroot().find("renderer-v2")
    if renderer is None:
        return []

    if renderer.get("type") == "categorizedSymbol":
        classElements = renderer.findall("categories/category")
    elif renderer.get("type") == "graduatedSymbol":
        classElements = renderer.findall("ranges/range")
    elif renderer.get("type") == "RuleRenderer":
        classElements = renderer.findall("rules/rule")
    else:
        return []

    symbolColors = {}
    for symbol in renderer.findall("symbols/symbol"):
        for option in symbol.iter("Option"):
            if option.get("name") == "color" or option.get("name") == "line_color":
                symbolColors[symbol.get("name")] = colorToHex(option.get("value"))
                break

    classColors = []
    for index, classElement in enumerate(classElements):
        color = symbolColors.get(classElement.get("symbol"))
        if color is not None:
            classColors.append((index, classElement.get("label", ""), color))
    return classColors


def extractMaterialColors():
    materialColors = []
    for names, color in MATERIAL_PALETTE:
        for name in names:
            materialColors.append((len(materialColors), name, color))
    return materialColors


def buildDatabase():
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute(
        "CREATE TABLE themeColors ("
        "theme TEXT NOT NULL, "
        "classIndex INTEGER NOT NULL, "
        "label TEXT, "
        "color TEXT NOT NULL, "
        "PRIMARY KEY (theme, classIndex))"
    )
    for fileName in THEMATIC_STYLE_FILES:
        qmlPath = os.path.join(STYLES_FOLDER, fileName)
        theme = themeKeyFromFileName(fileName)
        for classIndex, label, color in extractClassColors(qmlPath):
            connection.execute(
                "INSERT INTO themeColors (theme, classIndex, label, color) VALUES (?, ?, ?, ?)",
                (theme, classIndex, label, color),
            )
        print("%s: %d classes" % (theme, connection.execute(
            "SELECT COUNT(*) FROM themeColors WHERE theme = ?", (theme,)).fetchone()[0]))
    for classIndex, label, color in extractMaterialColors():
        connection.execute(
            "INSERT INTO themeColors (theme, classIndex, label, color) VALUES (?, ?, ?, ?)",
            ("pipematerials", classIndex, label, color),
        )
    print("pipematerials: %d aliases" % connection.execute(
        "SELECT COUNT(*) FROM themeColors WHERE theme = 'pipematerials'").fetchone()[0])
    connection.commit()
    connection.close()
    print("Database written to %s" % DATABASE_PATH)


if __name__ == "__main__":
    buildDatabase()
