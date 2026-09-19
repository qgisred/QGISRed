# -*- coding: utf-8 -*-
"""Rebuilds a shapefile's stale .qix spatial index after we overwrite the .shp in place.

QGIS never creates a .qix on its own — it only uses one if present, building one requires
an explicit user action (Layer Properties > Source > "Create Spatial Index", or the
matching Processing algorithm). But once one exists, GDAL's shapefile driver does not
update it incrementally: a .qix built for a previous feature count/order/extent can make
the renderer silently skip features that are very much still in the file, until the index
is rebuilt or QGIS is restarted. Every reload path in this plugin overwrites the .shp in
place (see INTERNALS.md sections 1-3) without ever touching a sidecar index, so a project that ever
had one gets exactly this: results or input features that "disappear" after a DLL run and
come back once the project is reopened.

The fix has two rules:
  - Only rebuild a .qix that was already there. Never create one where none existed —
    that would add indexing overhead to layers nobody asked to have indexed.
  - Never touch the sidecar while our own rebuild for that path is in flight: on Windows a
    file GDAL still has open for writing cannot be deleted. A reload that lands mid-build
    is not lost, it is queued once and replayed the moment the in-flight build finishes.
"""
import os
from contextlib import suppress

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsApplication, QgsTask

_SIDECAR_EXTENSIONS = (".qix", ".sbn", ".sbx")


def _qixPath(shpPath):
    return os.path.splitext(shpPath)[0] + ".qix"


def _tr(msg):
    return QCoreApplication.translate("SpatialIndexRebuilder", msg)


class SpatialIndexRebuilder:
    """Per-path state machine driving the delete-then-rebuild cycle.

    `schedule` and `build` are injection points so tests can drive the state machine
    synchronously, without a real QgsTask or GDAL. Production code uses the module-level
    `maybeRebuildSpatialIndex()`, which shares one instance across every reload call site —
    the per-path tracking below only works if every caller for the same shapefile goes
    through it.
    """

    def __init__(self, schedule=None, build=None):
        self._schedule = schedule or self._scheduleWithQgsTask
        self._build = build or _buildWithGdal
        self._building = set()   # paths with a rebuild task currently in flight
        self._pending = set()    # paths that need another rebuild once that task finishes
        self._tasks = {}         # path -> QgsTask, kept alive until it finishes (else GC'd)

    def maybeRebuild(self, shpPath):
        """Call right after reloadData() on a shapefile written in place."""
        if shpPath in self._building:
            self._pending.add(shpPath)
            return
        if not os.path.exists(_qixPath(shpPath)):
            return
        self._dropSidecars(shpPath)
        self._building.add(shpPath)
        self._schedule(shpPath, self._runBuild, self._onFinished)

    @staticmethod
    def _dropSidecars(shpPath):
        base = os.path.splitext(shpPath)[0]
        for extension in _SIDECAR_EXTENSIONS:
            with suppress(OSError):
                os.remove(base + extension)

    def _runBuild(self, shpPath):
        with suppress(Exception):
            self._build(shpPath)

    def _onFinished(self, shpPath):
        self._tasks.pop(shpPath, None)
        self._building.discard(shpPath)
        if shpPath in self._pending:
            self._pending.discard(shpPath)
            self.maybeRebuild(shpPath)

    def _scheduleWithQgsTask(self, shpPath, runFn, finishedFn):
        def run(_task):
            runFn(shpPath)
            return True

        def finished(_ok, _result=None):
            finishedFn(shpPath)

        task = QgsTask.fromFunction(
            _tr("Rebuilding spatial index"), run, on_finished=finished,
            flags=QgsTask.Flag.Hidden | QgsTask.Flag.Silent)
        self._tasks[shpPath] = task
        QgsApplication.taskManager().addTask(task)


def _buildWithGdal(shpPath):
    """The actual index build. Raw GDAL, not PyQGIS: this runs on a worker thread, and a
    QgsVectorLayer (or anything else Qt) has no business being touched off the main thread."""
    from osgeo import ogr

    dataset = ogr.Open(shpPath, update=1)
    if dataset is None:
        return
    layer = dataset.GetLayer(0)
    if layer is not None:
        dataset.ExecuteSQL('CREATE SPATIAL INDEX ON "%s"' % layer.GetName())
    dataset = None


_sharedRebuilder = SpatialIndexRebuilder()


def maybeRebuildSpatialIndex(shpPath):
    """Call right after reloadData() on a shapefile that was just overwritten in place.
    No-op unless that path already had a .qix; see the module docstring for why."""
    _sharedRebuilder.maybeRebuild(shpPath)
