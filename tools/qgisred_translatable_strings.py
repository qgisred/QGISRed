# -*- coding: utf-8 -*-
# Translatable strings from qgisred_units.json 
from PyQt5.QtCore import QCoreApplication

def _tr(s):
    return QCoreApplication.translate('FieldPrettyNames', s)

# Common fields
_tr("Identifier")
_tr("Tag")
_tr("Description")

# Pipes
_tr("Length")
_tr("Diameter")
_tr("Roughness Coefficient")
_tr("Loss Coefficient")
_tr("Material")
_tr("Installation Date")
_tr("Initial Status")
_tr("Bulk Coefficient")
_tr("Wall Coefficient")

# Junctions
_tr("Elevation")
_tr("Base Demand")
_tr("Demand Pattern")
_tr("Emitter Coefficient")
_tr("Initial Quality")

# Tanks
_tr("Initial Level")
_tr("Minimum Level")
_tr("Maximum Level")
_tr("Minimum Volume")
_tr("Volume Curve")
_tr("Overflow")
_tr("Mixing Model")
_tr("Mixing Fraction")
_tr("Reaction Coefficient")

# Reservoirs
_tr("Total Head")
_tr("Head Pattern")

# Valves
_tr("Type")
_tr("Setting")
_tr("HeadLoss Curve")

# Pumps
_tr("Head Curve")
_tr("Power")
_tr("Speed")
_tr("Speed Pattern")
_tr("Efficiency Curve")
_tr("Energy Price")
_tr("Price Pattern")

# Sources
_tr("Base Value")
_tr("Pattern")

# Meters
_tr("Is Active")

# Demands
_tr("Node Identifier")
_tr("Category")

# Service Connections
_tr("Reliability")

# Isolation Valves
_tr("Status")
_tr("Available")
