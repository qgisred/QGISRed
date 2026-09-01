# -*- coding: utf-8 -*-
"""The catalogue of thematic maps: what each one is called, which field it classifies and
which style file draws it.

Pure data, rebuilt on every call because half the entries depend on the project's unit
system and on the headloss formula, both of which the user can change at any time.
"""

from .qgisred_project_utils import QGISRedProjectUtils


def queryIdentifier(query):
    """The stable id a thematic map layer carries in its qgisred_identifier property."""
    return f"qgisred_query_{query['layer_type'].lower()}_{query['field'].lower()}"


def buildQueryCatalogue():
    """Every thematic map the plugin can build, described for the project's current
    units and headloss formula."""
    units = QGISRedProjectUtils.getUnits()
    queries = []

    # Tanks and Reservoirs queries (top)
    # Tanks queries
    queries.append({
        'layer_name': 'Tank Elevations',
        'layer_type': 'Tanks',
        'field': 'Elevation',
        'qml_file': f'tank_elevations_{units}.qml',
        'file_name': f'elevation_{units}',
        'tooltip_prefix': 'Elev'
    })

    queries.append({
        'layer_name': 'Tank Diameters',
        'layer_type': 'Tanks',
        'field': 'Diameter',
        'qml_file': f'tank_diameters_{units}.qml',
        'file_name': f'diameter_{units}',
        'tooltip_prefix': 'Diam'
    })

    queries.append({
        'layer_name': 'Tank Volumes',
        'layer_type': 'Tanks',
        'field': 'Volume',
        'qml_file': f'tank_volumes_{units}.qml',
        'file_name': f'volume_{units}',
        'tooltip_prefix': 'Vol'
    })

    queries.append({
        'layer_name': 'Tank Levels',
        'layer_type': 'Tanks',
        'field': 'Level',
        'qml_file': f'tank_levels_{units}.qml',
        'file_name': f'level_{units}',
        'tooltip_prefix': 'Level'
    })

    queries.append({
        'layer_name': 'Tank Initial Quality',
        'layer_type': 'Tanks',
        'field': 'InitQuality',
        'qml_file': 'tank_init_quality.qml',
        'file_name': 'init_quality',
        'tooltip_prefix': 'Quality'
    })

    queries.append({
        'layer_name': 'Tank Bulk Coefficient',
        'layer_type': 'Tanks',
        'field': 'BulkCoeff',
        'qml_file': 'tank_bulk_coeff.qml',
        'file_name': 'bulk_coeff',
        'tooltip_prefix': 'Bulk'
    })

    queries.append({
        'layer_name': 'Tank Mixing Models',
        'layer_type': 'Tanks',
        'field': 'MixModel',
        'qml_file': 'tank_mixing_model.qml',
        'file_name': 'mixing_model',
        'tooltip_prefix': 'Mix'
    })

    queries.append({
        'layer_name': 'Tank Tags',
        'layer_type': 'Tanks',
        'field': 'Tag',
        'qml_file': 'tank_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    # Reservoirs queries
    queries.append({
        'layer_name': 'Reservoir Total Head',
        'layer_type': 'Reservoirs',
        'field': 'TotalHead',
        'qml_file': f'reservoir_total_head_{units}.qml',
        'file_name': f'total_head_{units}',
        'tooltip_prefix': 'Head'
    })

    queries.append({
        'layer_name': 'Reservoir Head Patterns',
        'layer_type': 'Reservoirs',
        'field': 'HeadPattern',
        'qml_file': 'reservoir_head_pattern.qml',
        'file_name': 'head_pattern',
        'tooltip_prefix': 'Pattern'
    })

    queries.append({
        'layer_name': 'Reservoir Initial Quality',
        'layer_type': 'Reservoirs',
        'field': 'InitQuality',
        'qml_file': 'reservoir_init_quality.qml',
        'file_name': 'init_quality',
        'tooltip_prefix': 'Quality'
    })

    queries.append({
        'layer_name': 'Reservoir Tags',
        'layer_type': 'Reservoirs',
        'field': 'Tag',
        'qml_file': 'reservoir_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    # Junctions queries (second from top)
    # One style serves both unit systems (the breaks are computed from the
    # data); file_name still carries the units because labels, map tip and
    # legend are written in the project's length unit.
    queries.append({
        'layer_name': 'Junction Elevations',
        'layer_type': 'Junctions',
        'field': 'Elevation',
        'qml_file': 'JunctionElevations.qml',
        'file_name': f'elevation_{units}',
        'tooltip_prefix': 'Elev'
    })

    queries.append({
        'layer_name': 'Junction Total Base Demands',
        'layer_type': 'Junctions',
        'field': 'TotalBaseDemand',
        'qml_file': 'JunctionTotalBaseDemands.qml',
        'file_name': 'total_base_demand',
        'tooltip_prefix': 'Demand'
    })

    queries.append({
        'layer_name': 'Junction Pattern Demands',
        'layer_type': 'Junctions',
        'field': 'PatternDemand',
        'qml_file': 'junction_pattern_demand.qml',
        'file_name': 'pattern_demand',
        'tooltip_prefix': 'Pattern'
    })

    queries.append({
        'layer_name': 'Junction Emitter Coefficients',
        'layer_type': 'Junctions',
        'field': 'EmitterCoeff',
        'qml_file': 'junction_emitter_coeff.qml',
        'file_name': 'emitter_coeff',
        'tooltip_prefix': 'Emitter'
    })

    queries.append({
        'layer_name': 'Junction Initial Quality',
        'layer_type': 'Junctions',
        'field': 'InitQuality',
        'qml_file': 'junction_init_quality.qml',
        'file_name': 'init_quality',
        'tooltip_prefix': 'Quality'
    })

    queries.append({
        'layer_name': 'Junction Tags',
        'layer_type': 'Junctions',
        'field': 'Tag',
        'qml_file': 'junction_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    # Valves and Pumps queries (third from top)
    # Valves queries
    queries.append({
        'layer_name': 'Valve Types',
        'layer_type': 'Valves',
        'field': 'Type',
        'qml_file': 'valve_types.qml',
        'file_name': 'type',
        'tooltip_prefix': 'Type'
    })

    queries.append({
        'layer_name': 'Valve Diameters',
        'layer_type': 'Valves',
        'field': 'Diameter',
        'qml_file': f'valve_diameters_{units}.qml',
        'file_name': f'diameter_{units}',
        'tooltip_prefix': 'Diam'
    })

    queries.append({
        'layer_name': 'Valve Settings',
        'layer_type': 'Valves',
        'field': 'Setting',
        'qml_file': 'valve_settings.qml',
        'file_name': 'setting',
        'tooltip_prefix': 'Set'
    })

    queries.append({
        'layer_name': 'Valve Initial Status',
        'layer_type': 'Valves',
        'field': 'InitStatus',
        'qml_file': 'valve_init_status.qml',
        'file_name': 'init_status',
        'tooltip_prefix': 'Status'
    })

    queries.append({
        'layer_name': 'Valve Loss Coefficients',
        'layer_type': 'Valves',
        'field': 'LossCoeff',
        'qml_file': 'valve_loss_coeff.qml',
        'file_name': 'loss_coeff',
        'tooltip_prefix': 'Loss'
    })

    queries.append({
        'layer_name': 'Valve Tags',
        'layer_type': 'Valves',
        'field': 'Tag',
        'qml_file': 'valve_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    # Pumps queries
    queries.append({
        'layer_name': 'Pump Types',
        'layer_type': 'Pumps',
        'field': 'Type',
        'qml_file': 'pump_types.qml',
        'file_name': 'type',
        'tooltip_prefix': 'Type'
    })

    queries.append({
        'layer_name': 'Pump Curves',
        'layer_type': 'Pumps',
        'field': 'PumpCurve',
        'qml_file': 'pump_curves.qml',
        'file_name': 'pump_curve',
        'tooltip_prefix': 'Curve'
    })

    queries.append({
        'layer_name': 'Pump Power',
        'layer_type': 'Pumps',
        'field': 'Power',
        'qml_file': 'pump_power.qml',
        'file_name': 'power',
        'tooltip_prefix': 'Power'
    })

    queries.append({
        'layer_name': 'Pump Initial Status',
        'layer_type': 'Pumps',
        'field': 'InitStatus',
        'qml_file': 'pump_init_status.qml',
        'file_name': 'init_status',
        'tooltip_prefix': 'Status'
    })

    queries.append({
        'layer_name': 'Pump Speed',
        'layer_type': 'Pumps',
        'field': 'Speed',
        'qml_file': 'pump_speed.qml',
        'file_name': 'speed',
        'tooltip_prefix': 'Speed'
    })

    queries.append({
        'layer_name': 'Pump Efficiency Curves',
        'layer_type': 'Pumps',
        'field': 'EffCurve',
        'qml_file': 'pump_efficiency_curves.qml',
        'file_name': 'efficiency_curve',
        'tooltip_prefix': 'Eff'
    })

    queries.append({
        'layer_name': 'Pump Energy Price',
        'layer_type': 'Pumps',
        'field': 'EnergyPrice',
        'qml_file': 'pump_energy_price.qml',
        'file_name': 'energy_price',
        'tooltip_prefix': 'Price'
    })

    queries.append({
        'layer_name': 'Pump Tags',
        'layer_type': 'Pumps',
        'field': 'Tag',
        'qml_file': 'pump_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    # Service Connections queries
    queries.append({
        'layer_name': 'Service Connection',
        'layer_type': 'ServiceConnection',
        'field': 'Temporary',
        'qml_file': 'service_connection.qml',
        'file_name': 'temporary',
        'tooltip_prefix': 'Temp'
    })

    # Isolation Valves queries
    queries.append({
        'layer_name': 'Isolation Valves',
        'layer_type': 'IsolationValves',
        'field': 'Temporary',
        'qml_file': 'isolation_valves.qml',
        'file_name': 'temporary',
        'tooltip_prefix': 'Temp'
    })

    # Meters queries
    queries.append({
        'layer_name': 'Meters',
        'layer_type': 'Meters',
        'field': 'Temporary',
        'qml_file': 'meters.qml',
        'file_name': 'temporary',
        'tooltip_prefix': 'Temp'
    })

    # Pipes queries (bottom)
    queries.append({
        'layer_name': 'Pipe Diameters',
        'layer_type': 'Pipes',
        'field': 'Diameter',
        'qml_file': f'PipeDiameters{units}.qml',
        'file_name': f'diameter_{units}',
        'tooltip_prefix': 'Diam'
    })

    queries.append({
        'layer_name': 'Pipe Lengths',
        'layer_type': 'Pipes',
        'field': 'Length',
        'qml_file': f'PipeLengths{units}.qml',
        'file_name': f'length_{units}',
        'tooltip_prefix': 'Len'
    })

    queries.append({
        'layer_name': 'Pipe Materials',
        'layer_type': 'Pipes',
        'field': 'Material',
        'qml_file': 'PipeMaterials.qml',
        'file_name': 'material',
        'tooltip_prefix': 'Mat'
    })

    # Roughness meaning (and its classes) depends on the headloss formula:
    # H-W is unitless, C-M is s/m^(1/3), and only D-W uses length units.
    formula = QGISRedProjectUtils.getHeadlossFormula()
    if formula == 'H-W':
        roughnessQml = 'PipeRoughnessesHW.qml'
        formulaAbbreviation = 'HW'
    elif formula == 'C-M':
        roughnessQml = 'PipeRoughnessesCM.qml'
        formulaAbbreviation = 'CM'
    else:
        roughnessQml = f'PipeRoughnessesDW{units}.qml'
        formulaAbbreviation = 'DW'
    queries.append({
        'layer_name': 'Pipe Roughnesses',
        'layer_type': 'Pipes',
        'field': 'Roughness',
        'qml_file': roughnessQml,
        'file_name': 'roughness',
        'tooltip_prefix': 'Rough',
        'name_suffix': f'_{formulaAbbreviation}'
    })

    queries.append({
        'layer_name': 'Pipe Ages',
        'layer_type': 'Pipes',
        'field': 'Age',
        'qml_file': 'PipeAges.qml',
        'file_name': 'age',
        'tooltip_prefix': 'Age'
    })

    queries.append({
        'layer_name': 'Pipe Loss Coefficient',
        'layer_type': 'Pipes',
        'field': 'LossCoeff',
        'qml_file': 'pipe_loss_coeff.qml',
        'file_name': 'loss_coeff',
        'tooltip_prefix': 'Loss'
    })

    queries.append({
        'layer_name': 'Pipe Initial Status',
        'layer_type': 'Pipes',
        'field': 'InitStatus',
        'qml_file': 'pipe_init_status.qml',
        'file_name': 'init_status',
        'tooltip_prefix': 'Status'
    })

    queries.append({
        'layer_name': 'Pipe Installation Year',
        'layer_type': 'Pipes',
        'field': 'InstallYear',
        'qml_file': 'PipeInstallationYears.qml',
        'file_name': 'install_year',
        'tooltip_prefix': 'Inst'
    })

    queries.append({
        'layer_name': 'Pipe Bulk Coefficient',
        'layer_type': 'Pipes',
        'field': 'BulkCoeff',
        'qml_file': 'pipe_bulk_coeff.qml',
        'file_name': 'bulk_coeff',
        'tooltip_prefix': 'Bulk'
    })

    queries.append({
        'layer_name': 'Pipe Wall Coefficient',
        'layer_type': 'Pipes',
        'field': 'WallCoeff',
        'qml_file': 'pipe_wall_coeff.qml',
        'file_name': 'wall_coeff',
        'tooltip_prefix': 'Wall'
    })

    queries.append({
        'layer_name': 'Pipe Tags',
        'layer_type': 'Pipes',
        'field': 'Tag',
        'qml_file': 'pipe_tags.qml',
        'file_name': 'tags',
        'tooltip_prefix': 'Tag'
    })

    return queries
