# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from typing import NamedTuple, Optional


class SimulationPeriod(NamedTuple):
    start_local: datetime
    duration_seconds: int

    @property
    def start_clock_seconds(self) -> int:
        start = self.start_local
        return start.hour * 3600 + start.minute * 60 + start.second

    def date_at(self, elapsed_seconds) -> datetime:
        return self.start_local + timedelta(seconds=float(elapsed_seconds))


def _parse_iso(text: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat((text or "").strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.replace(tzinfo=None)


def read_simulation_period(project_directory: str, network_name: str) -> Optional[SimulationPeriod]:
    if not project_directory or not network_name:
        return None
    path = os.path.join(project_directory, f"{network_name}_Metadata.txt")
    if not os.path.exists(path):
        return None
    try:
        node = ET.parse(path).getroot().find(".//SimulationPeriod")
    except (ET.ParseError, OSError):
        return None
    if node is None:
        return None

    start_local = _parse_iso(node.findtext("StartLocal"))
    start_utc = _parse_iso(node.findtext("Start"))
    end_utc = _parse_iso(node.findtext("End"))
    if start_local is None or start_utc is None or end_utc is None or end_utc <= start_utc:
        return None
    return SimulationPeriod(start_local, int((end_utc - start_utc).total_seconds()))


def format_date(value) -> str:
    return value.strftime("%d/%m/%Y")


def simulation_start_date(project_directory: str, network_name: str) -> Optional[date]:
    period = read_simulation_period(project_directory, network_name)
    return period.start_local.date() if period is not None else None
