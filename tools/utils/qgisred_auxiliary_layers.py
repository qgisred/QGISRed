# -*- coding: utf-8 -*-
"""The Demand Builder's auxiliary themes: file naming and on-disk housekeeping.

Unlike the network's own layers, of which there is exactly one each, the user can keep
several themes of every type — one per billing run, per sector division, and so on. What
ties a file to its type is the token its name carries:

    {NetworkName}_DemandBuilder_{Type}[_{theme name}].shp

The network prefix is what lets a theme survive closing and reopening a project that has
no .qgs (see `_buildGroupsString` and `QGISRedProjectIO._openGroupByName`, which strip and
rebuild it), and the type token is what gives the loaded layer its qgisred_identifier. The
themes the Demands Manager writes by itself carry no trailing name and parse just the same.
"""

import os


# Every file a theme is made of. Shapefiles are not one file, and a theme that leaves its
# .dbf behind comes back as a broken row in the layer manager.
THEME_EXTENSIONS = (
    ".shp", ".shx", ".dbf", ".prj", ".cpg", ".qix",
    ".sbn", ".sbx", ".qmd", ".qml", ".shp.xml",
)


class AuxiliaryLayerType:
    """A theme type, and the three names it answers to.

    They are deliberately not the same string:

    * `key` is what the DLL entry point expects as its themeType.
    * `fileToken` is what new files carry, and `identifierToken` what the loaded layer
      takes as its qgisred_identifier. They differ because the file names were shortened
      further than the identifiers were.
    * `legacyFileTokens` are the spellings still read but no longer written: the plural
      DemandsBuilder and the longer type names, which every theme created before this
      rename carries.
    """

    def __init__(self, key, fileToken, identifierToken, legacyFileTokens=()):
        self.key = key
        self.fileToken = fileToken
        self.identifierToken = identifierToken
        self.identifier = "qgisred_" + identifierToken.lower()
        self.fileTokens = (fileToken,) + tuple(legacyFileTokens)

    def __repr__(self):
        return "AuxiliaryLayerType(%s)" % self.key


# The theme types the layer manager offers. Their columns are declared in
# GISRed.ExtendedModel/Writers/ToShp.AuxiliaryLayers.cs, which is what creates the files.
AUXILIARY_LAYER_TYPES = (
    AuxiliaryLayerType(
        "Consumptions", "DemandBuilder_Consumptions", "DemandBuilder_ConsumptionPoints",
        ("DemandsBuilder_ConsumptionPoints", "DemandBuilder_ConsumptionPoints"),
    ),
    AuxiliaryLayerType(
        "Links", "DemandBuilder_Links", "DemandBuilder_DemandLinks",
        ("DemandsBuilder_DemandLinks", "DemandBuilder_DemandLinks"),
    ),
    AuxiliaryLayerType(
        "Sectors", "DemandBuilder_Sectors", "DemandBuilder_Sectors",
        ("DemandsBuilder_Sectors",),
    ),
)

# Mirrors ToShp.DefaultBaseDemandField: the first base demand column of a consumption
# points theme. Passing it explicitly keeps the created file readable if the C# default
# ever changes without the plugin noticing.
DEFAULT_BASE_DEMAND_FIELD = "BaseDem"

AUXILIARY_TYPES_BY_KEY = {layerType.key: layerType for layerType in AUXILIARY_LAYER_TYPES}


"""File naming"""


def composeBaseName(networkName, layerType, themeName=""):
    """`{Net}_DemandBuilder_{Type}[_{theme name}]`, without extension."""
    parts = [networkName, layerType.fileToken]
    if themeName:
        parts.append(themeName)
    return "_".join(part for part in parts if part)


def parseBaseName(baseName, networkName=""):
    """(layerType, themeName) for a recognised theme file name, else (None, "").

    The network prefix is optional so that a folder copied between projects still reads.
    """
    if not baseName:
        return None, ""

    remainder = baseName
    prefix = networkName + "_" if networkName else ""
    if prefix and remainder.startswith(prefix):
        remainder = remainder[len(prefix):]

    for layerType in AUXILIARY_LAYER_TYPES:
        for token in layerType.fileTokens:
            if remainder == token:
                return layerType, ""
            if remainder.startswith(token + "_"):
                return layerType, remainder[len(token) + 1:]
    return None, ""


def isValidThemeName(themeName):
    """A theme name becomes part of a file name, so it may not smuggle a path into one."""
    if not themeName or themeName != themeName.strip():
        return False
    return not any(char in themeName for char in '\\/:*?"<>|')


def listThemes(folder, networkName=""):
    """(layerType, themeName, path) for every recognised theme in `folder`, name-sorted."""
    if not folder or not os.path.isdir(folder):
        return []

    themes = []
    for fileName in os.listdir(folder):
        base, extension = os.path.splitext(fileName)
        if extension.lower() != ".shp":
            continue
        layerType, themeName = parseBaseName(base, networkName)
        if layerType is None:
            continue
        themes.append((layerType, themeName, os.path.join(folder, fileName)))

    return sorted(themes, key=lambda theme: (theme[0].key, theme[1].lower()))


def deleteTheme(path):
    """Remove a theme and every sidecar. Returns "" or the first error.

    The caller must have closed the layer first: on Windows a file QGIS still holds open
    cannot be removed, and even when it can the handle is left pointing at nothing.
    """
    base = os.path.splitext(path)[0]
    for extension in THEME_EXTENSIONS:
        candidate = base + extension
        if not os.path.exists(candidate):
            continue
        try:
            os.remove(candidate)
        except OSError as error:
            return str(error)
    return ""
