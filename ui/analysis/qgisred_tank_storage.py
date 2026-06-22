# -*- coding: utf-8 -*-
"""Stored volume in tanks from EPANET results and project tank/curve data.

Mirrors EPANET ``EN_TANKVOLUME`` / ``tankvolume()`` (hydraul.c):

- Only **storage tanks** are included; **reservoirs are excluded**.
- Water level at each report step: ``level = head - bottom_elevation`` (``h``).

**Without volume curve** (``tankvolume()``):

``V = Vmin + (h - Hmin) × A`` — ``MinVolume`` in the DBF is the input ``Vmin`` (volume
at minimum water level). When ``MinVolume`` is undeclared (``0``), EPANET's
``convertunits()`` initialises ``Vmin = A × Hmin`` (cylinder down to the bottom), so the
stored volume reduces to ``A × h`` rather than ``A × (h - Hmin)``.

**With volume curve** (input init + ``tankvolume()``):

- At init, EPANET sets ``Vmin = interp(curve, Hmin)``; DBF ``MinVolume`` is not an
  independent input in that case.
- Stored volume at level ``h`` is ``interp(curve, h)`` only (no extra ``Vmin`` term).
- During the simulation, volume never drops below ``Vmin``; when recomputing from
  reported heads we apply the same floor: ``max(interp(h), interp(Hmin))``.

**Numeric policy:** use EPANET values as read (``.out`` float32 heads/demands, binary
``tank_areas``, DBF fields) with no rounding in volume or spill-flow math. Chart/table
display decimals are handled separately in the time-series UI (see ``timeseries_globals``).

**Tank spill (EPANET 2.2+):** for tanks with ``Overflow = YES``, spillage rate is read
from the node ``Demand`` in the ``.out`` when the water level is at ``MaxLevel``.

EPANET volume curves in ``[CURVES]`` / ``Curves.dbf``: X = level, Y = volume.

DBF ``Tanks.Diameter`` storage (QGISRed convention, like link diameters in ``.out``):

- **SI:** millimetres in the DBF → converted to metres for area math.
- **US:** feet in the DBF (per ``qgisred_properties_units_decimals.csv``), not inches
  like Pipes/Valves. Prefer ``tank_areas`` from ``.out`` when available.
"""
import math
import os
import struct
from typing import Dict, List, Optional, Sequence, Tuple

from .qgisred_results_binary import _NT_TANK, getOut_Metadata
from .qgisred_results_hyd import _is_metric_model


def _read_dbf_records(path: str) -> List[dict]:
    """Read all records from a QGISRed DBF table."""
    if not path or not os.path.exists(path):
        return []
    rows = _read_dbf_records_binary(path)
    if rows:
        return rows
    try:
        from qgis.core import QgsVectorLayer

        layer = QgsVectorLayer(path, "dbf", "ogr")
        if not hasattr(layer, "isValid") or not layer.isValid():
            return []
        names = [field.name() for field in layer.fields()]
        ogr_rows = []
        for feature in layer.getFeatures():
            attrs = feature.attributes()
            ogr_rows.append({names[i]: attrs[i] for i in range(len(names))})
        return ogr_rows
    except Exception:
        return []


def _read_dbf_records_binary(path: str) -> List[dict]:
    with open(path, "rb") as handle:
        header = handle.read(32)
        if len(header) < 32 or header[0] not in (0x03, 0x30):
            return []

        num_records = struct.unpack_from("<I", header, 4)[0]
        header_size = struct.unpack_from("<H", header, 8)[0]
        record_size = struct.unpack_from("<H", header, 10)[0]

        handle.seek(32)
        fields = []
        while True:
            desc = handle.read(32)
            if not desc or desc[0] == 0x0D:
                break
            name = desc[:11].split(b"\x00", 1)[0].decode("ascii", errors="replace").strip()
            ftype = chr(desc[11])
            length = desc[16]
            decimals = desc[17]
            fields.append((name, ftype, length, decimals))

        rows = []
        handle.seek(header_size)
        for _ in range(num_records):
            raw = handle.read(record_size)
            if len(raw) < record_size:
                break
            if raw[0] == 0x2A:
                continue
            offset = 1
            record = {}
            for name, ftype, length, decimals in fields:
                chunk = raw[offset:offset + length]
                offset += length
                text = chunk.decode("ascii", errors="replace").strip()
                if ftype == "N":
                    record[name] = float(text) if text else None
                else:
                    record[name] = text
            rows.append(record)
        return rows


def _as_float(value, default=0.0) -> float:
    if value is None:
        return default
    try:
        text = str(value).strip()
        if not text or text.upper() == "NULL":
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


def _as_text(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text or text.upper() == "NULL":
        return ""
    return text


def _tank_can_overflow(value) -> bool:
    """True when EPANET tank overflow / spill is enabled (``[TANKS]`` Overflow = YES)."""
    text = _as_text(value).upper()
    if not text:
        return False
    return text in ("YES", "Y", "SI", "S", "1", "TRUE")


def _load_tank_properties(project_directory: str, network_name: str) -> Dict[str, dict]:
    path = os.path.join(project_directory, f"{network_name}_Tanks.dbf")
    tanks = {}
    for row in _read_dbf_records(path):
        tank_id = _as_text(row.get("Id"))
        if not tank_id:
            continue
        tanks[tank_id] = {
            "elevation": _as_float(row.get("Elevation")),
            "min_volume": _as_float(row.get("MinVolume")),
            "min_level": _as_float(row.get("MinLevel")),
            "max_level": _as_float(row.get("MaxLevel")),
            "diameter": _as_float(row.get("Diameter")),
            "volume_curve_id": _as_text(row.get("IdVolCurve")),
            "can_overflow": _tank_can_overflow(row.get("Overflow")),
        }
    return tanks


def _load_volume_curves(project_directory: str, network_name: str) -> Dict[str, List[Tuple[float, float]]]:
    path = os.path.join(project_directory, f"{network_name}_Curves.dbf")
    by_id: Dict[str, List[Tuple[float, float]]] = {}
    for row in _read_dbf_records(path):
        if _as_text(row.get("Type")).lower() != "volume":
            continue
        curve_id = _as_text(row.get("CurveID"))
        if not curve_id:
            continue
        level = _as_float(row.get("Xvalue", row.get("XValue")))
        volume = _as_float(row.get("Yvalue", row.get("YValue")))
        by_id.setdefault(curve_id, []).append((level, volume))

    for curve_id in by_id:
        by_id[curve_id].sort(key=lambda point: point[0])
    return by_id


def cylindrical_volume_from_level(
    level: float,
    *,
    min_volume: float,
    min_level: float,
    cross_section_area: float,
) -> float:
    """EPANET ``tankvolume()`` for a cylindrical tank: ``Vmin + (h - Hmin) * A``.

    When ``MinVolume`` is undeclared (``Vmin == 0``), EPANET's ``convertunits()`` sets
    ``Vmin = A * Hmin`` (full cylinder to the bottom), so stored volume becomes ``A * h``
    rather than ``A * (h - Hmin)``.
    """
    if min_volume <= 0.0:
        min_volume = cross_section_area * min_level
    volume = min_volume + cross_section_area * (level - min_level)
    return max(volume, min_volume)


def volume_from_level(
    level: float,
    *,
    min_volume: float,
    min_level: float = 0.0,
    cross_section_area: float,
    volume_curve_points: Optional[Sequence[Tuple[float, float]]] = None,
) -> Tuple[float, bool]:
    """Return (stored volume, uses_volume_curve) for water level ``h`` above bottom."""
    if volume_curve_points:
        volume = interpolate_volume_curve(level, volume_curve_points)
        v_min = interpolate_volume_curve(min_level, volume_curve_points)
        return max(volume, v_min), True
    return cylindrical_volume_from_level(
        level,
        min_volume=min_volume,
        min_level=min_level,
        cross_section_area=cross_section_area,
    ), False


def interpolate_volume_curve(level: float, points: Sequence[Tuple[float, float]]) -> float:
    """Linear interpolation on EPANET volume curve (level -> volume)."""
    if not points:
        return 0.0
    if level <= points[0][0]:
        return float(points[0][1])
    if level >= points[-1][0]:
        return float(points[-1][1])

    for index in range(len(points) - 1):
        level0, volume0 = points[index]
        level1, volume1 = points[index + 1]
        if level0 <= level <= level1:
            if level1 == level0:
                return float(volume0)
            ratio = (level - level0) / (level1 - level0)
            return float(volume0 + ratio * (volume1 - volume0))
    return float(points[-1][1])


def _tank_area_from_diameter(diameter_length: float) -> float:
    """Cross-section area from diameter already in EPANET length units (m or ft)."""
    if diameter_length <= 0.0:
        return 0.0
    radius = diameter_length * 0.5
    return math.pi * radius * radius


def _tank_diameter_dbf_to_model_length(diameter_dbf: float, flow_units) -> float:
    """Convert ``Tanks.Dbf`` ``Diameter`` to EPANET tank diameter (m or ft)."""
    d = float(diameter_dbf)
    if d <= 0.0:
        return 0.0
    if _is_metric_model(flow_units):
        return d / 1000.0
    return d


def spill_flow_from_tank_state(
    demand: float,
    level: float,
    *,
    can_overflow: bool,
    min_level: float,
    max_level: float,
) -> float:
    """EPANET spillage rate for one tank at a report step (flow, not volume).

    Only tanks with overflow enabled contribute. When ``max_level > min_level``,
    spill is counted only if ``level`` is at or above ``max_level``; otherwise
    positive ``demand`` is treated as spill (EPANET reports spillage in ``Demand``).
    """
    if not can_overflow:
        return 0.0
    if max_level > min_level + 1e-9 and level < max_level - 1e-6:
        return 0.0
    return max(0.0, float(demand))


def total_tank_spill_from_period(
    demands: Sequence[float],
    heads: Sequence[float],
    node_types: Sequence[int],
    node_ids: Sequence[str],
    tank_props_by_id: Dict[str, dict],
    *,
    head_factor: float = 1.0,
    demand_factor: float = 1.0,
) -> float:
    """Sum spill flow over all overflow-enabled tanks at one time step."""
    total = 0.0
    for node_index, node_type in enumerate(node_types):
        if node_type != _NT_TANK:
            continue
        tank_id = node_ids[node_index]
        props = tank_props_by_id.get(tank_id, {})
        if not props.get("can_overflow"):
            continue
        elevation = float(props.get("elevation", 0.0))
        head = float(heads[node_index]) * head_factor
        level = head - elevation
        demand = float(demands[node_index]) * demand_factor
        total += spill_flow_from_tank_state(
            demand,
            level,
            can_overflow=True,
            min_level=float(props.get("min_level", 0.0)),
            max_level=float(props.get("max_level", 0.0)),
        )
    return total


def _read_demands_by_period(handle, meta) -> List[List[float]]:
    n_nodes = meta["n_nodes"]
    num_periods = meta["num_periods"]
    period_size = meta["period_size"]
    results_offset = meta["results_offset"]
    demands = [[0.0] * num_periods for _ in range(n_nodes)]

    for period in range(num_periods):
        base = results_offset + period * period_size
        for node_index in range(n_nodes):
            handle.seek(base + node_index * 4)
            demands[node_index][period] = struct.unpack("f", handle.read(4))[0]
    return demands


def _read_heads_by_period(handle, meta) -> List[List[float]]:
    n_nodes = meta["n_nodes"]
    num_periods = meta["num_periods"]
    period_size = meta["period_size"]
    results_offset = meta["results_offset"]
    heads = [[0.0] * num_periods for _ in range(n_nodes)]

    for period in range(num_periods):
        base = results_offset + period * period_size + n_nodes * 4
        for node_index in range(n_nodes):
            handle.seek(base + node_index * 4)
            heads[node_index][period] = struct.unpack("f", handle.read(4))[0]
    return heads


def _out_tank_area_by_node(meta) -> Dict[int, float]:
    """Cross-section areas from .out; index 0 area marks a reservoir, not used for storage."""
    areas = {}
    tank_areas = meta.get("tank_areas") or []
    for tank_index, node_index in enumerate(meta.get("tank_node_indices") or []):
        if tank_index < len(tank_areas) and float(tank_areas[tank_index]) > 0.0:
            areas[node_index] = float(tank_areas[tank_index])
    return areas


def total_stored_volume_from_tank_rows(tank_rows: Sequence[dict]) -> List[float]:
    """Sum stored volume of all tanks at each report step (reservoirs already excluded)."""
    if not tank_rows:
        return []
    num_periods = len(tank_rows[0].get("volumes") or [])
    totals = [0.0] * num_periods
    for row in tank_rows:
        for period, volume in enumerate(row.get("volumes") or []):
            totals[period] += float(volume)
    return totals


def _tank_series_from_heads(
    meta,
    heads_by_period: List[List[float]],
    project_directory: str,
    network_name: str,
    *,
    head_factor: float = 1.0,
) -> List[dict]:
    tank_props = _load_tank_properties(project_directory, network_name)
    volume_curves = _load_volume_curves(project_directory, network_name)

    node_types = meta["node_types"]
    node_ids = meta["node_ids"]
    node_elevations = meta.get("node_elevations") or [0.0] * meta["n_nodes"]
    out_areas = _out_tank_area_by_node(meta)

    num_periods = meta.get("num_periods") or meta.get("hyd_num_periods") or 0
    report_start = meta.get("report_start", meta.get("hyd_report_start", 0))
    report_step = meta.get("report_step", meta.get("hyd_report_step", 0))
    if meta.get("hyd_num_periods"):
        times = list(meta.get("hyd_times") or [])
        if not times and num_periods:
            times = [report_start + period * report_step for period in range(num_periods)]
    else:
        times = [report_start + period * report_step for period in range(num_periods)]

    results = []
    for node_index, node_type in enumerate(node_types):
        if node_type != _NT_TANK:
            continue

        tank_id = node_ids[node_index]
        props = tank_props.get(tank_id, {})
        elevation = props.get("elevation")
        if elevation is None:
            elevation = float(node_elevations[node_index]) if node_index < len(node_elevations) else 0.0
        else:
            elevation = float(elevation)

        min_volume = float(props.get("min_volume", 0.0))
        min_level = float(props.get("min_level", 0.0))
        curve_id = props.get("volume_curve_id", "")
        curve_points = volume_curves.get(curve_id) if curve_id else None

        diameter_dbf = float(props.get("diameter", 0.0))
        cross_area = out_areas.get(node_index, 0.0)
        if cross_area <= 0.0 and diameter_dbf > 0.0:
            diameter_len = _tank_diameter_dbf_to_model_length(
                diameter_dbf, meta.get("flow_units"),
            )
            cross_area = _tank_area_from_diameter(diameter_len)

        levels = []
        volumes = []
        for period in range(num_periods):
            head = float(heads_by_period[node_index][period]) * head_factor
            level = head - elevation
            volume, _ = volume_from_level(
                level,
                min_volume=min_volume,
                min_level=min_level,
                cross_section_area=cross_area,
                volume_curve_points=curve_points,
            )
            levels.append(level)
            volumes.append(volume)

        results.append({
            "tank_id": tank_id,
            "uses_volume_curve": bool(curve_id and curve_points),
            "volume_curve_id": curve_id if curve_id and curve_points else "",
            "levels": levels,
            "volumes": volumes,
            "times": times,
        })

    results.sort(key=lambda item: item["tank_id"])
    return results


def getOut_TimesTankStoredVolumes(out_file_path: str, project_directory: str, network_name: str):
    """Stored volume time series for each tank in the network.

    Parameters
    ----------
    out_file_path:
        EPANET binary output (.out).
    project_directory:
        Folder with ``{network}_Tanks.dbf`` and ``{network}_Curves.dbf``.
    network_name:
        Network name prefix for project DBF files.

    Returns
    -------
    list[dict]
        One entry per tank node (reservoirs excluded), with keys:

        - ``tank_id`` (str)
        - ``uses_volume_curve`` (bool)
        - ``volume_curve_id`` (str, empty when cylindrical)
        - ``levels`` (list[float]): water level = head - bottom elevation
        - ``volumes`` (list[float]): stored volume per report period
        - ``times`` (list[int]): report time in seconds from simulation start
    """
    if not out_file_path or not os.path.exists(out_file_path):
        return []

    with open(out_file_path, "rb") as handle:
        meta = getOut_Metadata(handle, include_geometry=True)
        if not meta:
            return []
        heads_by_period = _read_heads_by_period(handle, meta)

    return _tank_series_from_heads(
        meta, heads_by_period, project_directory, network_name,
    )


def getOut_TimesTotalStoredVolume(out_file_path: str, project_directory: str, network_name: str):
    """Total stored volume in all tanks at each report step (reservoirs excluded)."""
    return total_stored_volume_from_tank_rows(
        getOut_TimesTankStoredVolumes(out_file_path, project_directory, network_name),
    )


def getHyd_TimesTankStoredVolumes(hyd_file_path: str, out_file_path: str, project_directory: str, network_name: str):
    """Stored volume time series per tank from hydraulic (.hyd) calculation steps."""
    from .qgisred_results_hyd import _head_factor_from_units, _read_hyd_period, getHyd_Metadata

    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []

    head_factor = _head_factor_from_units(meta.get("flow_units"))
    n_nodes = meta["n_nodes"]
    num_periods = meta["hyd_num_periods"]
    heads_by_period = [[0.0] * num_periods for _ in range(n_nodes)]
    for period in range(num_periods):
        _, _, heads, _, _, _ = _read_hyd_period(hyd_file_path, meta, period)
        for node_index in range(n_nodes):
            heads_by_period[node_index][period] = float(heads[node_index])

    return _tank_series_from_heads(
        meta, heads_by_period, project_directory, network_name, head_factor=head_factor,
    )


def getHyd_TimesTotalStoredVolume(hyd_file_path: str, out_file_path: str, project_directory: str, network_name: str):
    """Total stored volume in all tanks at each .hyd step (reservoirs excluded)."""
    return total_stored_volume_from_tank_rows(
        getHyd_TimesTankStoredVolumes(hyd_file_path, out_file_path, project_directory, network_name),
    )


def _find_tank_row(tank_rows: Sequence[dict], tank_id: str) -> Optional[dict]:
    """Return the per-tank row whose ``tank_id`` matches, or ``None``."""
    for row in tank_rows or []:
        if row.get("tank_id") == tank_id:
            return row
    return None


def getOut_TimesTankVolume(out_file_path: str, project_directory: str, network_name: str, tank_id: str):
    """Stored volume time series for a single tank (empty list if the tank is missing).

    Volume is in the model's volume units (m³ SI / ft³ US), matching the
    ``Tanks.MinVolume`` (Volume) declaration in the units file.
    """
    row = _find_tank_row(
        getOut_TimesTankStoredVolumes(out_file_path, project_directory, network_name),
        tank_id,
    )
    return list(row["volumes"]) if row else []


def getHyd_TimesTankVolume(hyd_file_path: str, out_file_path: str, project_directory: str, network_name: str, tank_id: str):
    """Stored volume time series for a single tank from .hyd steps (empty if missing)."""
    row = _find_tank_row(
        getHyd_TimesTankStoredVolumes(hyd_file_path, out_file_path, project_directory, network_name),
        tank_id,
    )
    return list(row["volumes"]) if row else []


def getOut_TimesTotalTankSpill(out_file_path: str, project_directory: str, network_name: str):
    """Total spill (overflow) flow from all overflow-enabled tanks at each report step."""
    if not out_file_path or not os.path.exists(out_file_path):
        return []

    tank_props = _load_tank_properties(project_directory, network_name)
    with open(out_file_path, "rb") as handle:
        meta = getOut_Metadata(handle, include_geometry=True)
        if not meta:
            return []
        demands_by_period = _read_demands_by_period(handle, meta)
        heads_by_period = _read_heads_by_period(handle, meta)

    node_types = meta["node_types"]
    node_ids = meta["node_ids"]
    n_nodes = meta["n_nodes"]
    num_periods = meta["num_periods"]
    totals = []
    for period in range(num_periods):
        demands = [demands_by_period[ni][period] for ni in range(n_nodes)]
        heads = [heads_by_period[ni][period] for ni in range(n_nodes)]
        totals.append(
            total_tank_spill_from_period(
                demands, heads, node_types, node_ids, tank_props,
            )
        )
    return totals


def getHyd_TimesTotalTankSpill(
    hyd_file_path: str,
    out_file_path: str,
    project_directory: str,
    network_name: str,
):
    """Total tank spill flow at each hydraulic (.hyd) step."""
    from .qgisred_results_hyd import _flow_factor_from_units, _head_factor_from_units, _read_hyd_period, getHyd_Metadata

    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []

    tank_props = _load_tank_properties(project_directory, network_name)
    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    head_factor = _head_factor_from_units(meta.get("flow_units"))
    node_types = meta["node_types"]
    node_ids = meta["node_ids"]
    n_nodes = meta["n_nodes"]
    num_periods = meta["hyd_num_periods"]
    totals = []
    for period in range(num_periods):
        _, demands, heads, _, _, _ = _read_hyd_period(hyd_file_path, meta, period)
        totals.append(
            total_tank_spill_from_period(
                demands,
                heads,
                node_types,
                node_ids,
                tank_props,
                head_factor=head_factor,
                demand_factor=flow_factor,
            )
        )
    return totals


def _tank_node_index(meta, tank_id: str) -> Optional[int]:
    """0-based node index of a storage tank by id, or ``None`` (reservoirs excluded)."""
    node_ids = meta.get("node_ids") or []
    node_types = meta.get("node_types") or []
    for index, node_id in enumerate(node_ids):
        if node_id == tank_id and index < len(node_types) and node_types[index] == _NT_TANK:
            return index
    return None


def _tank_spill_value(demand, head, props: dict, *, head_factor: float = 1.0, demand_factor: float = 1.0) -> float:
    """Spill (overflow) flow for one tank at one step from its reported demand/head.

    Tanks without overflow enabled always yield ``0`` (EPANET caps the level
    instead of spilling).
    """
    elevation = float(props.get("elevation", 0.0))
    level = float(head) * head_factor - elevation
    return spill_flow_from_tank_state(
        float(demand) * demand_factor,
        level,
        can_overflow=bool(props.get("can_overflow")),
        min_level=float(props.get("min_level", 0.0)),
        max_level=float(props.get("max_level", 0.0)),
    )


def getOut_TimesTankSpill(out_file_path: str, project_directory: str, network_name: str, tank_id: str):
    """Overflow (spill) flow time series for a single tank at each report step.

    Returns ``[]`` when the file or tank is missing. The flow is in the model's
    flow units; tanks without overflow enabled yield all-zero values.
    """
    if not out_file_path or not os.path.exists(out_file_path):
        return []

    props = _load_tank_properties(project_directory, network_name).get(tank_id, {})
    with open(out_file_path, "rb") as handle:
        meta = getOut_Metadata(handle, include_geometry=True)
        if not meta:
            return []
        node_index = _tank_node_index(meta, tank_id)
        if node_index is None:
            return []
        demands_by_period = _read_demands_by_period(handle, meta)
        heads_by_period = _read_heads_by_period(handle, meta)

    return [
        _tank_spill_value(
            demands_by_period[node_index][period],
            heads_by_period[node_index][period],
            props,
        )
        for period in range(meta["num_periods"])
    ]


def getHyd_TimesTankSpill(hyd_file_path: str, out_file_path: str, project_directory: str, network_name: str, tank_id: str):
    """Overflow (spill) flow time series for a single tank from .hyd steps."""
    from .qgisred_results_hyd import _flow_factor_from_units, _head_factor_from_units, _read_hyd_period, getHyd_Metadata

    meta = getHyd_Metadata(hyd_file_path, out_file_path)
    if not meta:
        return []
    node_index = _tank_node_index(meta, tank_id)
    if node_index is None:
        return []

    props = _load_tank_properties(project_directory, network_name).get(tank_id, {})
    flow_factor = _flow_factor_from_units(meta.get("flow_units"))
    head_factor = _head_factor_from_units(meta.get("flow_units"))
    series = []
    for period in range(meta["hyd_num_periods"]):
        _, demands, heads, _, _, _ = _read_hyd_period(hyd_file_path, meta, period)
        series.append(
            _tank_spill_value(
                demands[node_index], heads[node_index], props,
                head_factor=head_factor, demand_factor=flow_factor,
            )
        )
    return series
