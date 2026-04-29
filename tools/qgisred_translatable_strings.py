# -*- coding: utf-8 -*-
# Translatable strings that pylupdate5 cannot extract automatically.
# Calling QCoreApplication.translate() directly with literal strings
# so pylupdate5 picks them up when generating/updating .ts files.
from qgis.PyQt.QtCore import QCoreApplication

# Common fields
QCoreApplication.translate('FieldPrettyNames', "Identifier")
QCoreApplication.translate('FieldPrettyNames', "Tag")
QCoreApplication.translate('FieldPrettyNames', "Description")
QCoreApplication.translate('FieldPrettyNames', "Age")
QCoreApplication.translate('FieldPrettyNames', "Installation Date")
QCoreApplication.translate('FieldPrettyNames', "Initial Status")
QCoreApplication.translate('FieldPrettyNames', "Type")
QCoreApplication.translate('FieldPrettyNames', "Status")
QCoreApplication.translate('FieldPrettyNames', "IsActive")

# Pipes
QCoreApplication.translate('FieldPrettyNames', "Length")
QCoreApplication.translate('FieldPrettyNames', "Diameter")
QCoreApplication.translate('FieldPrettyNames', "Roughness Coeff")
QCoreApplication.translate('FieldPrettyNames', "Loss Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Material")
QCoreApplication.translate('FieldPrettyNames', "Leak Area")
QCoreApplication.translate('FieldPrettyNames', "Leak Expansion Rate")
QCoreApplication.translate('FieldPrettyNames', "Bulk Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Wall Coefficient")

# Junctions
QCoreApplication.translate('FieldPrettyNames', "Elevation")
QCoreApplication.translate('FieldPrettyNames', "Base Demand")
QCoreApplication.translate('FieldPrettyNames', "Pattern Demand")
QCoreApplication.translate('FieldPrettyNames', "Emitter Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Initial Quality")

# Multiple Demands
QCoreApplication.translate('FieldPrettyNames', "Base Demand")

# Tanks
QCoreApplication.translate('FieldPrettyNames', "Initial Level")
QCoreApplication.translate('FieldPrettyNames', "MinimumLevel")
QCoreApplication.translate('FieldPrettyNames', "Maximum Level")
QCoreApplication.translate('FieldPrettyNames', "Volume")
QCoreApplication.translate('FieldPrettyNames', "Volume Curve")
QCoreApplication.translate('FieldPrettyNames', "Overflow Condition")
QCoreApplication.translate('FieldPrettyNames', "Mixing Model")
QCoreApplication.translate('FieldPrettyNames', "Mixing Fraction")

# Reservoirs
QCoreApplication.translate('FieldPrettyNames', "Total Head")
QCoreApplication.translate('FieldPrettyNames', "Head Pattern")

# Valves
QCoreApplication.translate('FieldPrettyNames', "Setting")
QCoreApplication.translate('FieldPrettyNames', "HeadLoss Curve")

# Pumps
QCoreApplication.translate('FieldPrettyNames', "Head Curve")
QCoreApplication.translate('FieldPrettyNames', "Power")
QCoreApplication.translate('FieldPrettyNames', "Speed")
QCoreApplication.translate('FieldPrettyNames', "Speed Pattern")
QCoreApplication.translate('FieldPrettyNames', "Efficiency Curve")
QCoreApplication.translate('FieldPrettyNames', "Energy Price")
QCoreApplication.translate('FieldPrettyNames', "Price Pattern")

# Curves
QCoreApplication.translate('FieldPrettyNames', "Value X axis")
QCoreApplication.translate('FieldPrettyNames', "Value Y axis")

# Sources
QCoreApplication.translate('FieldPrettyNames', "Source Quality")
QCoreApplication.translate('FieldPrettyNames', "Source Pattern")

# Service Connections
QCoreApplication.translate('FieldPrettyNames', "Reliability")

# Isolation Valves
QCoreApplication.translate('FieldPrettyNames', "Available")

# Options
QCoreApplication.translate('FieldPrettyNames', "Specific Gravity")
QCoreApplication.translate('FieldPrettyNames', "Viscosity")
QCoreApplication.translate('FieldPrettyNames', "Demand Multiplier")
QCoreApplication.translate('FieldPrettyNames', "Emitter Exponent")
QCoreApplication.translate('FieldPrettyNames', "Minimum Pressure")
QCoreApplication.translate('FieldPrettyNames', "Required Pressure")
QCoreApplication.translate('FieldPrettyNames', "Pressure Exponent")
QCoreApplication.translate('FieldPrettyNames', "Diffusivity")
QCoreApplication.translate('FieldPrettyNames', "Global Bulk")
QCoreApplication.translate('FieldPrettyNames', "Global Wall")
QCoreApplication.translate('FieldPrettyNames', "Limiting Potential")
QCoreApplication.translate('FieldPrettyNames', "Global Efficiency")
QCoreApplication.translate('FieldPrettyNames', "Global Price")
QCoreApplication.translate('FieldPrettyNames', "Demand Charge")

# Result nodes
QCoreApplication.translate('FieldPrettyNames', "Pressure")
QCoreApplication.translate('FieldPrettyNames', "Head")
QCoreApplication.translate('FieldPrettyNames', "Demand")
QCoreApplication.translate('FieldPrettyNames', "Full demand")
QCoreApplication.translate('FieldPrettyNames', "Demand Deficit")
QCoreApplication.translate('FieldPrettyNames', "Leakage Flow")
QCoreApplication.translate('FieldPrettyNames', "Emitter Flow")

# Result links
QCoreApplication.translate('FieldPrettyNames', "Flow")
QCoreApplication.translate('FieldPrettyNames', "Velocity")
QCoreApplication.translate('FieldPrettyNames', "HeadLoss")
QCoreApplication.translate('FieldPrettyNames', "Unit HeadLoss")
QCoreApplication.translate('FieldPrettyNames', "Friction factor")
QCoreApplication.translate('FieldPrettyNames', "Energy")
QCoreApplication.translate('FieldPrettyNames', "Reaction Rate")

# Result nodes and links
QCoreApplication.translate('FieldPrettyNames', "Element Type")
QCoreApplication.translate('FieldPrettyNames', "Simulation Time")

# Quality results (dynamic — also translated via getQualityDisplayName)
QCoreApplication.translate('FieldPrettyNames', "Chemical")
QCoreApplication.translate('FieldPrettyNames', "Trace")

# Layer names shown in QGIS legend (Inputs group)
QCoreApplication.translate('InputLayerNames', "Pipes")
QCoreApplication.translate('InputLayerNames', "Junctions")
QCoreApplication.translate('InputLayerNames', "Multiple Demands")
QCoreApplication.translate('InputLayerNames', "Reservoirs")
QCoreApplication.translate('InputLayerNames', "Tanks")
QCoreApplication.translate('InputLayerNames', "Pumps")
QCoreApplication.translate('InputLayerNames', "Valves")
QCoreApplication.translate('InputLayerNames', "Sources")
QCoreApplication.translate('InputLayerNames', "Service Connections")
QCoreApplication.translate('InputLayerNames', "Isolation Valves")
QCoreApplication.translate('InputLayerNames', "Meters")
QCoreApplication.translate('InputLayerNames', "Hydrants")
QCoreApplication.translate('InputLayerNames', "Washout Valves")
QCoreApplication.translate('InputLayerNames', "Air Release Valves")
# Layer names shown in QGIS legend (Queries group)
QCoreApplication.translate('InputLayerNames', "Links_Connect")
QCoreApplication.translate('InputLayerNames', "Links_HydSec")
QCoreApplication.translate('InputLayerNames', "Nodes_HydSec")
QCoreApplication.translate('InputLayerNames', "Isolated Demands_HydSec")
QCoreApplication.translate('InputLayerNames', "Links_DemSec")
QCoreApplication.translate('InputLayerNames', "Nodes_DemSec")
QCoreApplication.translate('InputLayerNames', "Links_IsolSeg")
QCoreApplication.translate('InputLayerNames', "Nodes_IsolSeg")
QCoreApplication.translate('InputLayerNames', "Isolated Demands_IsolSeg")
QCoreApplication.translate('InputLayerNames', "Links T")
QCoreApplication.translate('InputLayerNames', "Nodes T")
QCoreApplication.translate('InputLayerNames', "Demand Links DB")
QCoreApplication.translate('InputLayerNames', "Consumption Points DB")
QCoreApplication.translate('InputLayerNames', "%1 I")
# Layer names shown in QGIS legend (Thematic Maps group)
QCoreApplication.translate('InputLayerNames', "Pipe Diameters")
QCoreApplication.translate('InputLayerNames', "Pipe Lengths")
QCoreApplication.translate('InputLayerNames', "Pipe Materials")
