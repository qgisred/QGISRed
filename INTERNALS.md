# Layer Lifecycle — Developer Reference

> **Audience**: QGISRed plugin developers.
> This document describes how the plugin manages QGIS vector layers (opening, refreshing,
> and moving files) without removing and re-adding layers to the QGIS project.

---

## Background: why layers must never be removed

On Windows, OGR opens shapefiles with `FILE_SHARE_READ | FILE_SHARE_WRITE` (not exclusive).
This means another process can overwrite the file contents while QGIS has it open — and QGIS
will see the new content after a `reloadData()` call.

However, **deleting a file and creating a new one at the same path creates a new inode**.
Any process that had the original file open gets a *zombie handle* — the directory entry is
gone but the old data persists until all handles close.

**Rule**: never call `QgsProject.instance().removeMapLayer()` on a QGISRed layer unless the
layer file is also being permanently deleted.  Instead, overwrite the file in-place and call
`reloadData()`.

---

## In-place overwrite vs. delete + recreate

| Operation | inode preserved? | QGIS handle valid? | Safe pattern |
|-----------|:-:|:-:|---|
| `shutil.copy2(src, dst)` (dst exists) | **Yes** | **Yes** | ✓ Use this |
| `open(dst, 'wb').write(...)` | **Yes** | **Yes** | ✓ |
| `os.replace(src, dst)` | No (new inode at dst) | No | ✗ |
| `os.rename(src, dst)` | No (new inode at dst) | No | ✗ |
| `os.remove(dst)` + new file at same path | No | No | ✗ |

`shutil.copy2` opens the destination with `CREATE_ALWAYS` on Windows, which **truncates and
rewrites the existing file without changing its inode**.  Existing OGR handles remain valid.

---

## Core reload helper

`tools/utils/qgisred_layer_utils.py` → `QGISRedLayerUtils._tryReloadExistingLayer(layerPath)`

```python
def _tryReloadExistingLayer(self, layerPath):
    for layer in self.getLayers():
        if fs.getLayerPath(layer) == layerPath:
            layer.dataProvider().reloadData()
            layer.updateExtents()
            layer.triggerRepaint()
            return True
    return False
```

Called by `openLayer()`, `openTreeLayer()`, `openIsolatedSegmentsLayer()`.
Returns `True` → file was reloaded in-place, no new `QgsVectorLayer` created.
Returns `False` → layer not open yet, caller opens it fresh.

---

## Layer types and their file movement patterns

### Network (input) layers — `sections/layer_management_section.py`

DLL writes to `tempFolder`. Python calls `GISRed.ReplaceTemporalFiles(projectDir, tempFolder)`,
which copies files from `tempFolder` → `projectDir` using in-place overwrite (same inode).
`openElementsLayers()` detects each layer as already open and calls `_reloadOpenLayer()`.

### Issues layers — `sections/layer_management_section.py` → `runOpenTemporaryFiles()`

DLL writes `*_Issues.*` files to `projectDir` root.
Python moves them to `projectDir/Issues/` using `shutil.copy2()` + `os.remove()` (NOT
`os.rename` or `os.replace`, which would create a new inode at the destination).
`openIssuesLayers()` → `openLayer()` → `_tryReloadExistingLayer()` reloads in-place.

```python
# Correct pattern
shutil.copy2(src, dst)   # overwrite in-place at destination, preserving inode
os.remove(src)           # remove the source temp file
```

### Sector layers (hydraulic / demand) — same pattern as Issues

DLL writes `*_HydraulicSectors.*` / `*_DemandSectors.*` to `projectDir` root.
Python moves them to `projectDir/Queries/` using `shutil.copy2()` + `os.remove()`.
`openSectorLayers()` → `openLayer()` → `_tryReloadExistingLayer()`.

### Tree and Isolated Segments layers — `sections/tools_section.py`

DLL writes directly to `tempFolder`, then
`GISRed.ReplaceTemporalFiles(queriesFolder, tempFolder)` copies in-place to
`projectDir/Queries/`.
`openTreeLayers()` / `openIsolatedSegmentsLayers()` → `_tryReloadExistingLayer()`.

### Result layers — `ui/analysis/qgisred_results_dock.py`

> **Pending DLL change**: `GISRed.Compute()` must be updated to accept a `tempFolder`
> parameter and write output there instead of directly to `projectDir/Results/`.

Current Python side is ready:
- `simulationProcess()` creates a temp dir, calls `GISRed.Compute(projectDir, networkName, tempFolder)`
- Copies result files from `tempFolder` → `projectDir/Results/` with `shutil.copy2()`
- `openLayerResults()` reloads existing layers via `_tryReloadExistingLayer()` or opens fresh

`openAllResults()` calls `openAllResultsProcess()` **directly** (no remove step).
`openLayerResults()` always calls `prepareResultFields()` on the layer regardless of whether
it was newly opened or reloaded, because the DLL only writes base fields — time-series fields
are added by Python.

---

## runTask is no longer used for layer management

`QGISRedLayerUtils.runTask(A, B)` runs `A()` synchronously then schedules `B()` via
`QTimer.singleShot(0, B)`.  It was originally needed to give the event loop time to process
layer removal and release OGR file handles before the next operation.

Since layers are never removed, the event loop delay is unnecessary.  All layer management
methods call their process functions **directly**:

| Method | Before | After |
|--------|--------|-------|
| `runTree()` | `runTask(removeTreeLayers, runTreeProcess)` | `runTreeProcess()` |
| `runIsolatedSegments()` | `runTask(removeIsolatedSegmentsLayers, runLoadIsolatedSegmentLayers)` | `runLoadIsolatedSegmentLayers()` |
| `runDemandSectors()` | `runTask(removeSectorLayers, runOpenTemporaryFiles)` | `runOpenTemporaryFiles()` |
| `runHydraulicSectors()` | `runTask(removeSectorLayers, runOpenTemporaryFiles)` | `runOpenTemporaryFiles()` |

---

## QLR mechanism — removed

`saveProjectAsQLR()` / `loadProjectFromQLR()` saved all open QGISRed layers to `.qlr` files
before a DLL operation, then restored them afterwards.  It was used to preserve layer styles
when layers were removed and re-opened.

This mechanism was **removed** because:
1. Layers are no longer removed, so their state (style, CRS, attribute table) is preserved
   automatically.
2. `loadProjectFromQLR()` called `removePluginLayers()` internally, which removed **all**
   QGISRed layers (including result layers) as a side effect of loading input layers.
3. The QLR snapshot was taken after the DLL had written new files, so any zombie-handle CRS
   corruption was baked into the `.qlr` and restored upon load.

---

## Adding a new DLL operation — checklist

1. DLL writes output to `tempFolder` (third parameter), not directly to `projectDir`.
2. Python copies files from `tempFolder` → final destination with `shutil.copy2()` + `os.remove()`.
3. Call the appropriate `open*Layers()` method — it uses `_tryReloadExistingLayer()` internally.
4. Do **not** call `removeLayers()` / `removeMapLayer()` before step 2.
5. Do **not** use `runTask(remove..., open...)` — call the open method directly.
