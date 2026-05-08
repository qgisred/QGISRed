# -*- coding: utf-8 -*-

ELEMENT_PROPERTIES = {
    "qgisred_pipes": {
        "properties": ["Length", "Diameter", "Material", "Age", "RoughCoeff", "InstalDate"],
        "classifyBy": ["Diameter", "Material", "Length", "Age", "InstalDate"],
    },
    "qgisred_junctions": {
        "properties": ["Elevation", "BaseDem"],
        "classifyBy": ["Elevation", "BaseDem"],
    },
    "qgisred_tanks": {
        "properties": ["Elevation", "IniLevel", "Diameter", "MinVolume"],
        "classifyBy": ["Elevation", "Diameter"],
    },
    "qgisred_reservoirs": {
        "properties": ["TotalHead"],
        "classifyBy": ["TotalHead"],
    },
    "qgisred_valves": {
        "properties": ["Diameter", "Setting", "Type"],
        "classifyBy": ["Diameter", "Type"],
    },
    "qgisred_pumps": {
        "properties": ["Power"],
        "classifyBy": ["Power"],
    },
    "qgisred_serviceconnections": {
        "properties": ["BaseDemand"],
        "classifyBy": ["BaseDemand"],
    },
    "qgisred_isolationvalves": {
        "properties": ["Status"],
        "classifyBy": ["Status"],
    },
}

ELEMENT_TYPE_ORDER = [
    "qgisred_pipes",
    "qgisred_junctions",
    "qgisred_tanks",
    "qgisred_reservoirs",
    "qgisred_valves",
    "qgisred_pumps",
    "qgisred_serviceconnections",
    "qgisred_isolationvalves",
]

CUMULATIVE_PROPERTIES = {"Length", "MinVolume", "BaseDem", "BaseDemand", "Power"}

INTENSIVE_PROPERTIES = {"Diameter", "Elevation", "RoughCoeff", "Age", "TotalHead", "IniLevel", "Setting"}

CATEGORICAL_FIELDS = {"Material", "Type", "Status", "InstalDate"}

RANGED_PRESETS = {
    ("qgisred_pipes", "Diameter"): {
        "type": "breaks",
        "values": [0, 50, 80, 100, 125, 150, 200, 250, 300, 400, 500, 600, 800, 1000],
    },
}

DEFAULT_NUM_CLASSES = 5
NUM_CLASSES_CHOICES = [3, 4, 5, 6, 7, 8, 10, 12, 15, 20]


def getPropertyMode(fieldName):
    if fieldName in CUMULATIVE_PROPERTIES:
        return "cumulative"
    if fieldName in INTENSIVE_PROPERTIES:
        return "intensive"
    return "plain"


def isCategoricalField(fieldName):
    return fieldName in CATEGORICAL_FIELDS


def getRangedOptions(elementIdentifier, classifyField):
    options = []
    if (elementIdentifier, classifyField) in RANGED_PRESETS:
        options.append("Preset")
    if isCategoricalField(classifyField):
        options.append("Distinct")
    else:
        options.append("Auto")
    return options


def getRangedPreset(elementIdentifier, classifyField):
    return RANGED_PRESETS.get((elementIdentifier, classifyField))
