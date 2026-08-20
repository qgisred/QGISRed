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
# colors). junction_base_demand is excluded: its colors live in data-defined
# expressions, not renderer classes. PipeMaterials has no renderer in its qml;
# its palette is read from _DEFAULT_MATERIAL_COLORS in qgisred_styling_utils.py.
THEMATIC_STYLE_FILES = [
    "PipeAges.qml.bak",
    "PipeDiametersSI.qml.bak",
    "PipeInstallationYears.qml.bak",
    "PipeLengthsSI.qml.bak",
    "PipeRoughnessesCM.qml.bak",
    "PipeRoughnessesDWSI.qml.bak",
    "PipeRoughnessesHW.qml.bak",
]


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
    # The material palette lives as a literal tuple in qgisred_styling_utils.py;
    # evaluate just that literal so this script does not need the QGIS runtime.
    import ast

    utilsPath = os.path.join(PLUGIN_ROOT, "tools", "utils", "qgisred_styling_utils.py")
    with open(utilsPath, encoding="utf-8") as utilsFile:
        source = utilsFile.read()
    match = re.search(r"for _names, _color in \((.*?)\n\):", source, re.DOTALL)
    if match is None:
        raise RuntimeError("Material palette not found in qgisred_styling_utils.py")
    paletteTuples = ast.literal_eval("(%s)" % match.group(1))

    materialColors = []
    for names, color in paletteTuples:
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
