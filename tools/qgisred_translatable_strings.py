# -*- coding: utf-8 -*-
# Translatable strings that pylupdate5 cannot extract automatically.
# Calling QCoreApplication.translate() directly with literal strings
# so pylupdate5 picks them up when generating/updating .ts files.
from qgis.PyQt.QtCore import QCoreApplication

# Common fields
QCoreApplication.translate('FieldPrettyNames', "Identifier")
QCoreApplication.translate('FieldPrettyNames', "Tag")
QCoreApplication.translate('FieldPrettyNames', "Description")

# Pipes
QCoreApplication.translate('FieldPrettyNames', "Length")
QCoreApplication.translate('FieldPrettyNames', "Diameter")
QCoreApplication.translate('FieldPrettyNames', "Roughness")
QCoreApplication.translate('FieldPrettyNames', "Loss Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Material")
QCoreApplication.translate('FieldPrettyNames', "Installation Date")
QCoreApplication.translate('FieldPrettyNames', "Initial Status")
QCoreApplication.translate('FieldPrettyNames', "Bulk Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Wall Coefficient")

# Junctions
QCoreApplication.translate('FieldPrettyNames', "Elevation")
QCoreApplication.translate('FieldPrettyNames', "Base Demand")
QCoreApplication.translate('FieldPrettyNames', "Demand Pattern")
QCoreApplication.translate('FieldPrettyNames', "Emitter Coefficient")
QCoreApplication.translate('FieldPrettyNames', "Initial Quality")

# Tanks
QCoreApplication.translate('FieldPrettyNames', "Initial Level")
QCoreApplication.translate('FieldPrettyNames', "MinimumLevel")
QCoreApplication.translate('FieldPrettyNames', "Maximum Level")
QCoreApplication.translate('FieldPrettyNames', "Minimum Volume")
QCoreApplication.translate('FieldPrettyNames', "Volume Curve")
QCoreApplication.translate('FieldPrettyNames', "Overflow")
QCoreApplication.translate('FieldPrettyNames', "Mixing Model")
QCoreApplication.translate('FieldPrettyNames', "Mixing Fraction")
QCoreApplication.translate('FieldPrettyNames', "Bulk Coefficient")

# Reservoirs
QCoreApplication.translate('FieldPrettyNames', "Total Head")
QCoreApplication.translate('FieldPrettyNames', "Head Pattern")

# Valves
QCoreApplication.translate('FieldPrettyNames', "Type")
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

# Sources
QCoreApplication.translate('FieldPrettyNames', "Base Value")
QCoreApplication.translate('FieldPrettyNames', "Pattern")

# Meters
QCoreApplication.translate('FieldPrettyNames', "Is Active")

# Demands
QCoreApplication.translate('FieldPrettyNames', "Node Identifier")
QCoreApplication.translate('FieldPrettyNames', "Category")

# Service Connections
QCoreApplication.translate('FieldPrettyNames', "Reliability")

# Isolation Valves
QCoreApplication.translate('FieldPrettyNames', "Status")
QCoreApplication.translate('FieldPrettyNames', "Available")

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
QCoreApplication.translate('InputLayerNames', "Links Connectivity")
QCoreApplication.translate('InputLayerNames', "Links HS")
QCoreApplication.translate('InputLayerNames', "Nodes HS")
QCoreApplication.translate('InputLayerNames', "Isolated Demands HS")
QCoreApplication.translate('InputLayerNames', "Links DS")
QCoreApplication.translate('InputLayerNames', "Nodes DS")
QCoreApplication.translate('InputLayerNames', "Links IS")
QCoreApplication.translate('InputLayerNames', "Nodes IS")
QCoreApplication.translate('InputLayerNames', "Links T")
QCoreApplication.translate('InputLayerNames', "Nodes T")
QCoreApplication.translate('InputLayerNames', "%1 I")
