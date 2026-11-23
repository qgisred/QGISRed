# -*- coding: utf-8 -*-
import bisect
import math
import os
import struct
from collections import namedtuple
from datetime import datetime

TICKS_PER_SECOND = 10_000_000
FOLDER_NAME = "Field_Data"
FILE_EXTENSION = ".fds"
DEFAULT_FREQUENCY_SECONDS = 3600

_SIGNATURE = b"QFDS"
_CURRENT_VERSION = 3
_HEADER_SIZE = 128
_LEGACY_HEADER_SIZE = 64
_ORIGINAL_RECORD = struct.Struct("<qd")
_CHANGE_RECORD = struct.Struct("<qdqHB5x")
_OPERATION_RECORD = struct.Struct("<BBHiiiddqqq8x")
_LOCAL_FLAG = 1
_OPERATION_ENABLED_FLAG = 1
_OPERATION_APPLY_TO_NEW_FLAG = 2

CHANGE_VALUE = 1
CHANGE_REMOVED = 2
CHANGE_RESTORE = 3
OPERATION_LIMITS = 1
OPERATION_MOVING_AVERAGE = 2
OPERATION_FILL_GAPS = 3

Series = namedtuple("Series", "is_local anchor original changes operations")
Change = namedtuple("Change", "time value revision kind")
Operation = namedtuple(
    "Operation", "kind enabled apply_to_new window max_missing frequency minimum maximum range_from range_to"
)
Rules = namedtuple("Rules", "scale_factor offset scale_limit allow_negatives allow_zeros")
NO_RULES = Rules(1.0, 0.0, 0.0, True, True)


class FieldDataError(Exception):
    pass


def datetime_to_ticks(value):
    delta = value.replace(tzinfo=None) - datetime(1, 1, 1)
    return (delta.days * 86400 + delta.seconds) * TICKS_PER_SECOND + delta.microseconds * 10


def decode_file_name(name):
    decoded = []
    index = 0
    while index < len(name):
        character = name[index]
        if character != "%":
            decoded.append(character)
            index += 1
            continue
        try:
            decoded.append(chr(int(name[index + 1:index + 3], 16)))
        except ValueError:
            return None
        if index + 2 >= len(name):
            return None
        index += 3
    return "".join(decoded)


def list_series_files(folder):
    files = {}
    try:
        names = os.listdir(folder)
    except OSError:
        return files
    for name in names:
        if not name.lower().endswith(FILE_EXTENSION):
            continue
        signal_id = decode_file_name(name[:-len(FILE_EXTENSION)])
        if signal_id:
            files[signal_id.lower()] = os.path.join(folder, name)
    return files


def read_series(path):
    with open(path, "rb") as handle:
        raw = handle.read()
    if len(raw) < _LEGACY_HEADER_SIZE or raw[:4] != _SIGNATURE:
        raise FieldDataError("Not a field data file: " + path)
    version, flags, anchor, original_count, change_count = struct.unpack_from("<HHqii", raw, 4)
    if version > _CURRENT_VERSION:
        raise FieldDataError("Field data file written by a newer version: " + path)
    header_size = _HEADER_SIZE if version >= 2 else _LEGACY_HEADER_SIZE
    operation_count = struct.unpack_from("<i", raw, 124)[0] if version >= 2 and len(raw) >= _HEADER_SIZE else 0
    expected = (header_size + original_count * _ORIGINAL_RECORD.size + change_count * _CHANGE_RECORD.size
                + operation_count * _OPERATION_RECORD.size)
    if min(original_count, change_count, operation_count) < 0 or len(raw) != expected:
        raise FieldDataError("Damaged field data file: " + path)

    offset = header_size
    original = []
    for _ in range(original_count):
        original.append(_ORIGINAL_RECORD.unpack_from(raw, offset))
        offset += _ORIGINAL_RECORD.size
    changes = []
    for _ in range(change_count):
        time, value, _edited, revision, kind = _CHANGE_RECORD.unpack_from(raw, offset)
        changes.append(Change(time, value, revision, kind))
        offset += _CHANGE_RECORD.size
    operations = []
    for _ in range(operation_count):
        (kind, _algorithm, op_flags, window, max_missing, frequency, minimum, maximum,
         range_from, range_to, _applied) = _OPERATION_RECORD.unpack_from(raw, offset)
        operations.append(Operation(
            kind, bool(op_flags & _OPERATION_ENABLED_FLAG), bool(op_flags & _OPERATION_APPLY_TO_NEW_FLAG),
            window, max_missing, frequency,
            None if math.isnan(minimum) else minimum, None if math.isnan(maximum) else maximum,
            range_from, range_to,
        ))
        offset += _OPERATION_RECORD.size

    is_local = bool(flags & _LOCAL_FLAG)
    return Series(is_local, anchor if is_local else None, original, changes, operations)


def _excluded(value, rules):
    if rules.scale_limit > 0 and abs(value) > rules.scale_limit:
        return True
    if not rules.allow_negatives and value < 0:
        return True
    return not rules.allow_zeros and value == 0


def _filter(points, rules):
    if rules is NO_RULES:
        return points
    return [point for point in points if not _excluded(point[1], rules)]


def _missing_between(before, after, frequency):
    if frequency <= 0:
        return 0
    return max(0, int(round((after - before) / TICKS_PER_SECOND / frequency)) - 1)


def _operation_edits(points, operation):
    edits = {}
    if operation.kind == OPERATION_LIMITS:
        for time, value in points:
            below = operation.minimum is not None and value < operation.minimum
            above = operation.maximum is not None and value > operation.maximum
            if below or above:
                edits[time] = None
    elif operation.kind == OPERATION_MOVING_AVERAGE and operation.window >= 3:
        half = operation.window // 2
        for index, (time, value) in enumerate(points):
            window = points[max(0, index - half):min(len(points) - 1, index + half) + 1]
            average = sum(item[1] for item in window) / len(window)
            if average != value:
                edits[time] = average
    elif operation.kind == OPERATION_FILL_GAPS and operation.frequency > 0:
        step = operation.frequency * TICKS_PER_SECOND
        for (before_time, before_value), (after_time, after_value) in zip(points, points[1:]):
            missing = _missing_between(before_time, after_time, operation.frequency)
            if missing == 0 or missing > operation.max_missing:
                continue
            for k in range(1, missing + 1):
                edits[before_time + k * step] = before_value + (after_value - before_value) * k / (missing + 1)
    return edits


def _apply_operation(points, operation):
    if not operation.enabled:
        return points
    inside = [point for point in points
              if operation.apply_to_new or operation.range_from <= point[0] <= operation.range_to]
    edits = _operation_edits(inside, operation) if inside else {}
    if not edits:
        return points
    values = dict(points)
    for time, value in edits.items():
        if value is None:
            values.pop(time, None)
        else:
            values[time] = value
    return sorted(values.items())


def effective_points(series, rules=NO_RULES):
    original = sorted((time, value * rules.scale_factor + rules.offset) for time, value in series.original)
    points = _filter(original, rules)
    for operation in series.operations:
        points = _apply_operation(points, operation)

    latest = {}
    for change in series.changes:
        current = latest.get(change.time)
        if current is None or change.revision > current.revision:
            latest[change.time] = change
    if not latest:
        return _filter(points, rules)

    original_by_time = dict(original)
    values = dict(points)
    for change in latest.values():
        if change.kind == CHANGE_VALUE:
            values[change.time] = change.value
        elif change.kind == CHANGE_RESTORE and change.time in original_by_time:
            values[change.time] = original_by_time[change.time]
        else:
            values.pop(change.time, None)
    return _filter(sorted(values.items()), rules)


def value_at(points, ticks, frequency_seconds=DEFAULT_FREQUENCY_SECONDS):
    if not points:
        return None
    tolerance = (frequency_seconds if frequency_seconds and frequency_seconds > 0
                 else DEFAULT_FREQUENCY_SECONDS) * TICKS_PER_SECOND
    index = bisect.bisect_left(points, (ticks,))
    after = points[index] if index < len(points) else None
    before = points[index - 1] if index > 0 else None
    if after is not None and after[0] == ticks:
        return after[1]
    if before is not None and after is not None and ticks - before[0] <= tolerance and after[0] - ticks <= tolerance:
        fraction = (ticks - before[0]) / (after[0] - before[0])
        return before[1] + (after[1] - before[1]) * fraction
    nearest = min((point for point in (before, after) if point is not None), key=lambda point: abs(point[0] - ticks))
    if abs(nearest[0] - ticks) <= tolerance / 2:
        return nearest[1]
    return None


def series_origin_ticks(series, simulation_start_utc_ticks):
    if series.is_local:
        return series.anchor
    return simulation_start_utc_ticks
