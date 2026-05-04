# -*- coding: utf-8 -*-
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class NiceScale:
    axis_min: float
    axis_max: float
    step: float
    divisions: int

    def ticks(self) -> List[float]:
        if self.divisions <= 0 or self.step == 0:
            return [self.axis_min, self.axis_max]
        return [self.axis_min + i * self.step for i in range(self.divisions + 1)]


def estimate_max_ticks(axis_pixel_size: float, label_pixel_size: float, *, min_ticks: int = 2, max_ticks: int = 12) -> int:
    """
    Estima el máximo de ticks (marcas) que caben sin solape:
    - axis_pixel_size / label_pixel_size
    - acotado a [min_ticks, max_ticks]
    """
    if label_pixel_size <= 0:
        return max_ticks
    raw = int(axis_pixel_size // label_pixel_size)
    return max(min_ticks, min(max_ticks, raw))


def _nice_num(x: float, *, round_: bool, nice_fractions: Sequence[float]) -> float:
    """
    Devuelve un 'nice number' cercano a x, de la forma f * 10^exp, con f en nice_fractions.
    Si round_=True, aproxima al más cercano; si False, redondea hacia arriba (ceiling).
    """
    if x == 0:
        return 0.0
    if x < 0:
        x = abs(x)
    exp = math.floor(math.log10(x))
    f = x / (10 ** exp)

    if round_:
        best = min(nice_fractions, key=lambda nf: abs(nf - f))
    else:
        bigger = [nf for nf in nice_fractions if nf >= f]
        best = bigger[0] if bigger else nice_fractions[-1]
    return best * (10 ** exp)


def compute_nice_scale(
    data_min: float,
    data_max: float,
    max_ticks: int,
    *,
    nice_fractions: Sequence[float] = (1, 2, 4, 5, 10),
    include_zero: bool = False,
) -> NiceScale:
    """
    Autoescalado numérico usando 'nice numbers'.

    - Cubre completamente [data_min, data_max]
    - Elige un step 'bonito' cercano al step ideal (rango/(max_ticks-1))
    - Devuelve axis_min, axis_max ajustados, step y divisiones
    """
    if max_ticks < 2:
        max_ticks = 2

    if data_min == data_max:
        if data_min == 0:
            data_min, data_max = -1.0, 1.0
        else:
            pad = abs(data_min) * 0.1 or 1.0
            data_min -= pad
            data_max += pad

    if include_zero:
        data_min = min(0.0, data_min)
        data_max = max(0.0, data_max)

    raw_range = data_max - data_min
    if raw_range == 0:
        raw_range = 1.0

    nice_range = _nice_num(raw_range, round_=False, nice_fractions=nice_fractions)
    raw_step = nice_range / (max_ticks - 1)
    step = _nice_num(raw_step, round_=True, nice_fractions=nice_fractions)
    if step == 0:
        step = raw_step or 1.0

    axis_min = math.floor(data_min / step) * step
    axis_max = math.ceil(data_max / step) * step
    divisions = int(round((axis_max - axis_min) / step))
    if divisions < 1:
        divisions = 1
        axis_max = axis_min + step

    # Si por redondeos quedaron demasiados ticks, subimos el step al siguiente 'nice'
    _prev_divisions = divisions
    _iters = 0
    while divisions + 1 > max_ticks and step > 0:
        _iters += 1
        step = _nice_num(step * 1.01, round_=False, nice_fractions=nice_fractions)
        axis_min = math.floor(data_min / step) * step
        axis_max = math.ceil(data_max / step) * step
        divisions = int(round((axis_max - axis_min) / step))
        # Si no progresamos o llevamos demasiadas iteraciones, forzar 1 sola división
        if _iters > 50 or divisions >= _prev_divisions:
            divisions = max_ticks - 1
            axis_max = axis_min + step
            break
        _prev_divisions = divisions

    return NiceScale(axis_min=axis_min, axis_max=axis_max, step=step, divisions=divisions)


def _sorted_unique(xs: Iterable[float]) -> List[float]:
    out = sorted(set(float(x) for x in xs))
    return out


def compute_nice_time_scale_hours(
    data_min_hours: float,
    data_max_hours: float,
    max_ticks: int,
) -> NiceScale:
    """
    Autoescalado para eje temporal medido en horas (puede abarcar días).

    Usa pasos en horas enteras (1, 2, 3, 4, 6, 8, 12, 24, 48, ...) para que
    los ticks caigan siempre en horas exactas (9:00, 10:00, etc.).
    """
    if max_ticks < 2:
        max_ticks = 2

    if data_min_hours == data_max_hours:
        data_max_hours = data_min_hours + 1.0

    raw_range = data_max_hours - data_min_hours
    if raw_range <= 0:
        raw_range = 1.0

    raw_step = raw_range / (max_ticks - 1)

    # Pasos en horas enteras: subbora, hora, múltiplos de hora, días
    candidates = _sorted_unique([
        1, 2, 3, 4, 6, 8, 12,
        24, 48, 72, 120, 168, 240, 360, 480, 720,
    ])

    # Elegimos el candidato más cercano al ideal, pero penalizando exceso de ticks.
    def score(step: float) -> Tuple[float, float]:
        divisions = math.ceil(raw_range / step)
        overflow = max(0.0, (divisions + 1) - max_ticks)
        closeness = abs(math.log(step / raw_step)) if step > 0 and raw_step > 0 else float("inf")
        return (overflow, closeness)

    step = min(candidates, key=score)

    axis_min = math.floor(data_min_hours / step) * step
    axis_max = math.ceil(data_max_hours / step) * step
    divisions = int(round((axis_max - axis_min) / step))
    if divisions < 1:
        divisions = 1
        axis_max = axis_min + step

    # Si aún sobran ticks, subimos al siguiente candidato mayor
    if divisions + 1 > max_ticks:
        bigger = [c for c in candidates if c > step]
        if bigger:
            step = bigger[0]
            axis_min = math.floor(data_min_hours / step) * step
            axis_max = math.ceil(data_max_hours / step) * step
            divisions = int(round((axis_max - axis_min) / step))

    return NiceScale(axis_min=axis_min, axis_max=axis_max, step=step, divisions=divisions)


def format_time_tick_hours(hours: float, step_hours: float | None = None) -> str:
    """
    Etiqueta en 2 líneas:
    - Línea superior: hora (00–23) y minutos (00–59) cuando aplica
    - Línea inferior: días (ej: 15d)
    """
    # Si el step tiene minutos (p.ej. 2.4h = 2h24m), redondeamos a minuto.
    # Si no, redondeamos a segundo para mantener compatibilidad.
    if step_hours is not None and abs(step_hours - round(step_hours)) > 1e-9:
        total_seconds = int(round(hours * 3600 / 60.0) * 60)
    else:
        total_seconds = int(round(hours * 3600))
    d = total_seconds // 86400
    rem = total_seconds % 86400
    h = rem // 3600
    m = (rem % 3600) // 60
    return f"{h:02d}:{m:02d}\n{d}d"


def format_number_tick(value: float, step: float, *, decimal_places: int | None = None) -> str:
    """
    Formatea valores numéricos evitando decimales innecesarios.
    El número de decimales depende del step, salvo que decimal_places fuerce el formato.
    """
    if decimal_places is not None and decimal_places >= 0:
        v = round(float(value), int(decimal_places))
        if int(decimal_places) == 0:
            return str(int(round(v)))
        return f"{v:.{int(decimal_places)}f}"

    if step == 0 or not math.isfinite(step):
        return str(value)

    step_abs = abs(step)
    if step_abs >= 1:
        decimals = 0
    else:
        decimals = int(math.ceil(-math.log10(step_abs)))
        decimals = max(0, min(6, decimals))

    v = round(value, decimals)
    if decimals == 0:
        return str(int(round(v)))
    return f"{v:.{decimals}f}"

