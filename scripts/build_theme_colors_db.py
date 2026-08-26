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
# colors). JunctionElevations computes its breaks from the data, so its colors
# are applied by class position. JunctionTotalBaseDemands is excluded: its
# colors live in data-defined expressions, not renderer classes. PipeMaterials
# has no renderer in its qml; its palette is MATERIAL_PALETTE below.
THEMATIC_STYLE_FILES = [
    "JunctionElevations.qml.bak",
    "PipeAges.qml.bak",
    "PipeDiametersSI.qml.bak",
    "PipeInstallationYears.qml.bak",
    "PipeLengthsSI.qml.bak",
    "PipeRoughnessesCM.qml.bak",
    "PipeRoughnessesDWSI.qml.bak",
    "PipeRoughnessesHW.qml.bak",
]

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
