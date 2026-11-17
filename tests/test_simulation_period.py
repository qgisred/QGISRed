# -*- coding: utf-8 -*-
from datetime import datetime

import pytest

from QGISRed.ui.analysis.simulation_period import format_date, read_simulation_period
from QGISRed.ui.analysis.timeseries_time_utils import simulation_start_clock_seconds

_PERIOD_XML = (
    '<?xml version="1.0" encoding="utf-8"?><GISRed><DigitalTwin><SimulationPeriod>'
    "<Start>2026-01-01T06:00:00.0000000Z</Start><End>2026-01-03T06:00:00.0000000Z</End>"
    "<TimeZone>Romance Standard Time</TimeZone><StartLocal>2026-01-01T07:00:00</StartLocal>"
    "</SimulationPeriod></DigitalTwin></GISRed>"
)


def _write(tmp_path, content, name="Net"):
    (tmp_path / f"{name}_Metadata.txt").write_text(content, encoding="utf-8")
    return str(tmp_path)


def test_the_period_is_read_from_the_project_metadata(tmp_path):
    period = read_simulation_period(_write(tmp_path, _PERIOD_XML), "Net")

    assert period.start_local == datetime(2026, 1, 1, 7, 0, 0)
    assert period.duration_seconds == 2 * 86400
    assert period.start_clock_seconds == 7 * 3600


def test_the_date_follows_the_elapsed_time(tmp_path):
    period = read_simulation_period(_write(tmp_path, _PERIOD_XML), "Net")

    assert period.date_at(18 * 3600) == datetime(2026, 1, 2, 1, 0, 0)
    assert format_date(period.date_at(18 * 3600)) == "02/01/2026"


@pytest.mark.parametrize("content", [
    None,
    "<GISRed><Title>T</Title></GISRed>",
    "not xml",
    "<GISRed><SimulationPeriod><Start>x</Start><End>y</End><StartLocal>z</StartLocal></SimulationPeriod></GISRed>",
    "<GISRed><SimulationPeriod><Start>2026-01-02T00:00:00Z</Start><End>2026-01-01T00:00:00Z</End>"
    "<StartLocal>2026-01-02T00:00:00</StartLocal></SimulationPeriod></GISRed>",
])
def test_without_a_usable_period_there_is_none(tmp_path, content):
    folder = _write(tmp_path, content) if content is not None else str(tmp_path)

    assert read_simulation_period(folder, "Net") is None


def test_the_start_clock_of_the_period_wins_over_the_options(tmp_path):
    assert simulation_start_clock_seconds(_write(tmp_path, _PERIOD_XML), "Net") == 7 * 3600


def test_the_start_clock_without_a_period_is_unchanged(tmp_path):
    assert simulation_start_clock_seconds(str(tmp_path), "Net", fallback=3600) == 3600


def test_civil_time_shows_the_date_instead_of_the_day_count():
    from datetime import date

    from QGISRed.ui.analysis.timeseries_time_utils import format_civil_time

    start = date(2026, 1, 31)
    assert format_civil_time(1, 7 * 3600, start_date=start) == "31/01/2026 8:00"
    assert format_civil_time(18, 7 * 3600, start_date=start) == "01/02/2026 1:00"
    assert format_civil_time(18, 7 * 3600, start_date=start, am_pm=True) == "01/02/2026 1:00 am"


def test_civil_time_without_a_date_is_unchanged():
    from QGISRed.ui.analysis.timeseries_time_utils import format_civil_time

    assert format_civil_time(1, 7 * 3600) == "8:00"
    assert format_civil_time(18, 7 * 3600) == "1d 1:00"


def test_the_start_date_comes_from_the_period(tmp_path):
    from datetime import date

    from QGISRed.ui.analysis.simulation_period import simulation_start_date

    assert simulation_start_date(_write(tmp_path, _PERIOD_XML), "Net") == date(2026, 1, 1)
    assert simulation_start_date(str(tmp_path / "none"), "Net") is None
