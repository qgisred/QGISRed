# -*- coding: utf-8 -*-
"""The .qix rebuild state machine: only rebuild a sidecar that already existed, and never
touch the file while our own rebuild for that path is still in flight.

`schedule` is injected so these tests drive the state machine synchronously — no real
QgsTask, no real GDAL — and assert on exactly what maybeRebuild() decided to do.
"""
import os

from QGISRed.tools.utils.qgisred_spatial_index_rebuilder import SpatialIndexRebuilder


def _touch(path):
    with open(path, "wb"):
        pass


class _FakeScheduler:
    """Captures scheduled builds instead of running them; the test drives run/finish."""

    def __init__(self):
        self.calls = []  # (shpPath, runFn, finishedFn), in schedule order

    def __call__(self, shpPath, runFn, finishedFn):
        self.calls.append((shpPath, runFn, finishedFn))


def test_does_nothing_when_no_qix_existed(tmp_path):
    shp = str(tmp_path / "Links.shp")
    _touch(shp)
    scheduler = _FakeScheduler()
    builds = []
    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=builds.append)

    rebuilder.maybeRebuild(shp)

    assert scheduler.calls == []
    assert builds == []


def test_drops_sidecars_and_schedules_a_build_when_a_qix_existed(tmp_path):
    shp = str(tmp_path / "Links.shp")
    qix = str(tmp_path / "Links.qix")
    sbn = str(tmp_path / "Links.sbn")
    _touch(shp)
    _touch(qix)
    _touch(sbn)
    scheduler = _FakeScheduler()
    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=lambda _p: None)

    rebuilder.maybeRebuild(shp)

    assert not os.path.exists(qix)
    assert not os.path.exists(sbn)
    assert [c[0] for c in scheduler.calls] == [shp]


def test_a_reload_mid_build_does_not_touch_the_sidecar_and_is_replayed_on_finish(tmp_path):
    shp = str(tmp_path / "Links.shp")
    qix = str(tmp_path / "Links.qix")
    _touch(shp)
    _touch(qix)
    scheduler = _FakeScheduler()
    builds = []
    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=builds.append)

    rebuilder.maybeRebuild(shp)  # starts building #1; drops the original qix
    assert len(scheduler.calls) == 1

    # A second DLL run finishes while #1 is still in flight. The build wrote a fresh qix
    # by now (simulating what _buildWithGdal would have left on disk).
    _touch(qix)
    rebuilder.maybeRebuild(shp)
    assert len(scheduler.calls) == 1, "must not schedule a second build while one is running"
    assert os.path.exists(qix), "must not delete a qix while a build for this path is in flight"

    # Build #1 finishes: run it, then signal completion.
    _, runFn, finishedFn = scheduler.calls[0]
    runFn(shp)
    finishedFn(shp)

    # The queued reload is replayed: the qix from build #1 is dropped and a second build
    # is scheduled.
    assert builds == [shp]
    assert not os.path.exists(qix)
    assert [c[0] for c in scheduler.calls] == [shp, shp]


def test_finishing_with_nothing_queued_does_not_reschedule(tmp_path):
    shp = str(tmp_path / "Links.shp")
    qix = str(tmp_path / "Links.qix")
    _touch(shp)
    _touch(qix)
    scheduler = _FakeScheduler()
    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=lambda _p: None)

    rebuilder.maybeRebuild(shp)
    _, _runFn, finishedFn = scheduler.calls[0]
    finishedFn(shp)

    assert len(scheduler.calls) == 1
    assert shp not in rebuilder._building
    assert shp not in rebuilder._pending


def test_a_build_that_raises_does_not_propagate(tmp_path):
    shp = str(tmp_path / "Links.shp")
    qix = str(tmp_path / "Links.qix")
    _touch(shp)
    _touch(qix)
    scheduler = _FakeScheduler()

    def boom(_path):
        raise RuntimeError("locked file")

    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=boom)
    rebuilder.maybeRebuild(shp)
    _, runFn, _finishedFn = scheduler.calls[0]

    runFn(shp)  # must not raise


def test_dropping_a_locked_sidecar_does_not_raise(tmp_path, monkeypatch):
    shp = str(tmp_path / "Links.shp")
    qix = str(tmp_path / "Links.qix")
    _touch(shp)
    _touch(qix)
    scheduler = _FakeScheduler()
    rebuilder = SpatialIndexRebuilder(schedule=scheduler, build=lambda _p: None)

    def raise_permission_error(_path):
        raise OSError("file in use")

    monkeypatch.setattr(os, "remove", raise_permission_error)

    rebuilder.maybeRebuild(shp)  # must not raise

    assert [c[0] for c in scheduler.calls] == [shp]


def test_module_level_helper_shares_one_instance():
    from QGISRed.tools.utils import qgisred_spatial_index_rebuilder as module

    assert isinstance(module._sharedRebuilder, SpatialIndexRebuilder)
    assert module.maybeRebuildSpatialIndex.__module__ == module.__name__
