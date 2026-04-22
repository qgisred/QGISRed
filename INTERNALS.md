# QGISRed — Developer Internals

> **Audience**: QGISRed plugin developers.
> Internal design decisions and implementation patterns that are not obvious from reading
> the code alone.

---

## 1. Layer lifecycle — why layers must never be removed

On Windows, OGR opens shapefiles with `FILE_SHARE_READ | FILE_SHARE_WRITE` (not exclusive).
This means another process can overwrite the file contents while QGIS has it open — and QGIS
will see the new content after a `reloadData()` call.

However, **deleting a file and creating a new one at the same path creates a new inode**.
Any process that had the original file open gets a *zombie handle* — the directory entry is
gone but the old data persists until all handles close.  QGIS layers pointing to the zombie
inode lose their CRS (`.prj` gone) and appear as `(null)` in the legend.

**Rule**: never call `QgsProject.instance().removeMapLayer()` on a QGISRed layer unless the
layer file is also being permanently deleted.  Instead, overwrite the file in-place and call
`reloadData()`.

---

## 2. In-place overwrite vs. delete + recreate

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

## 3. Core reload helpers

Both live in `tools/utils/qgisred_layer_utils.py` → `QGISRedLayerUtils`.

### `_findLayerByPath(layerPath)`

Returns the open `QgsVectorLayer` whose source file matches `layerPath`, or `None`.
Used internally whenever a reload or post-reload action needs a reference to the layer.

### `_tryReloadExistingLayer(layerPath)`

Calls `_findLayerByPath`, and if a match is found, runs:
```python
layer.dataProvider().reloadData()
layer.updateExtents()
layer.triggerRepaint()
return True   # False if not found
```

Called by `openLayer()`, `openTreeLayer()`, `openIsolatedSegmentsLayer()`.
Returns `True` → file was reloaded in-place, no new `QgsVectorLayer` created.
Returns `False` → layer not open yet, caller opens it fresh.

---

## 4. Post-reload style refresh

`reloadData()` refreshes the underlying OGR data but **does not update the renderer**.
For layers whose style is computed from the actual data values (e.g. categorized renderers),
the style must be re-applied after every reload so that new values are reflected in the
legend.

### Current case: sector layers

Sector layers (hydraulic / demand) use a **categorized renderer** built from the unique
values of the `Class` field (demand) or `SubNet` field (hydraulic).  Each DLL run can
produce a different set of sectors, so the renderer must be rebuilt on every reload.

`openLayer()` handles this transparently: when `_tryReloadExistingLayer()` returns `True`
and `sectors=True`, it immediately calls `setSectorsStyle(layer)` on the reloaded layer.

```python
# Inside openLayer(), after _tryReloadExistingLayer() returns True:
if sectors:
    existingLayer = self._findLayerByPath(layerPath)
    if existingLayer is not None:
        styling.setSectorsStyle(existingLayer)
return
```

### Generalising to other layer types

If a future layer type also needs post-reload style work, the right place is the same
pattern inside `openLayer()` — add an `elif` branch for the new flag (e.g. `issues`,
`results`, or a new one).  If the number of cases grows, consider replacing the individual
boolean flags with an enum or a `post_reload` callback parameter so callers can inject
arbitrary post-reload logic without modifying `openLayer()` itself.

---

## 5. Layer types and their file movement patterns

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

### Sector layers (hydraulic / demand)

DLL writes `*_HydraulicSectors.*` / `*_DemandSectors.*` to `projectDir` root.
Python moves them to `projectDir/Queries/` using `shutil.copy2()` + `os.remove()`.
`openSectorLayers()` → `openLayer(..., sectors=True)` → `_tryReloadExistingLayer()` +
`setSectorsStyle()` (see §4).

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

## 6. Group visibility — automatic activation via `getOrCreateNestedGroup`

### Goal

Whenever layers are loaded into a group (Inputs, Results, Queries/Tree, Issues…), the
QGIS legend should automatically:
- **Show** the group that just received layers (and all its ancestors).
- **Hide** its sibling groups at the same level.

For example, opening a Tree result should show `NetworkName → Queries → Tree: X` and
hide `Inputs`, `Results`, and `Issues` at the network level.

### Implementation

The visibility logic is baked into `getOrCreateNestedGroup()` in
`tools/utils/qgisred_layer_utils.py`.  After resolving or creating each group along the
path, it applies visibility to all groups at that level **from path index 1 onwards**
(index 0 is the network root or a top-level group that is never hidden):

```python
if i > 0:
    for sibling in currentParent.children():
        if isinstance(sibling, QgsLayerTreeGroup):
            sibling.setItemVisibilityChecked(sibling == foundGroup)
```

Because every `open*Layers()` method calls `getOrCreateNestedGroup()` before opening
layers, this fires automatically with no extra code at call sites.

### Why index 0 is excluded

`path[0]` is the network root group (e.g. `"Network987"`).  A project can have multiple
networks loaded simultaneously, so hiding sibling network groups would be wrong.  The
rule only applies from the first child level downwards (`i > 0`).

### Callers that do NOT use `getOrCreateNestedGroup`

`getOrCreateGroup(name)` is a thin wrapper that looks up a single group by name within
the current network root.  It does **not** apply visibility logic.  It is used only by
methods that need a group reference for purposes other than immediately loading layers
into it (e.g. `activeInputGroup()`, `getResultGroup()`).  Do not add visibility side
effects there.

---

## 7. Centralized DLL result handling — `processCsharpResult`

Every DLL call returns a string. `processCsharpResult` in
`sections/layer_management_section.py` is the single method that interprets that string
and triggers the appropriate layer-opening flow.

### Return values and their meaning

| Return value | Meaning |
|---|---|
| `"True"` | Operation succeeded; show optional success message. No layers to open. |
| `"False"` | Silent no-op (caller may show a specific message before calling). |
| `"Cancelled"` | User cancelled in the DLL dialog. No-op. |
| `"commit"` | Network changed; reload all input layers. |
| `"shps"` | New query/result shapefiles ready; open the appropriate layer group. |
| `"commit/shps"` | Both of the above. |
| anything else | Error message; displayed via `pushMessage(level=2)`. |

### Signature

```python
def processCsharpResult(self, b, message, layerType="issues", onOpenLayers=None):
```

- `message` — shown via `pushMessage(level=3)` only when `b == "True"` and message is non-empty.
- `layerType` — controls which flag is set when `b` is `"shps"` or `"commit/shps"`:
  - `"issues"` (default) → `hasToOpenIssuesLayers = True`
  - `"sectors"` → `hasToOpenSectorLayers = True`
  - `"connectivity"` → `hasToOpenConnectivityLayers = True`
- `onOpenLayers` — optional callback that replaces `runOpenTemporaryFiles()` as the
  layer-opening step. Used by operations whose files land in a non-standard folder
  (e.g. Tree and IsolatedSegments write to `Queries/`, not `projectDir`).

### Flow

```
processCsharpResult(b, ...)
  └─ sets hasToOpen* flags
  └─ if any flag set:
       layerOperationInProgress = True
       onOpenLayers()  OR  runOpenTemporaryFiles()
         ├─ GISRed.ReplaceTemporalFiles(projectDir, tempFolder)
         ├─ move *_Issues.* → Issues/          [if hasToOpenIssuesLayers]
         ├─ openElementLayers() + setExtent()  [if hasToOpenNewLayers]
         ├─ openIssuesLayers()                 [if hasToOpenIssuesLayers]
         ├─ openConnectivityLayer()            [if hasToOpenConnectivityLayers]
         └─ move *Sectors.* → Queries/ + openSectorLayers()  [if hasToOpenSectorLayers]
         └─ layerOperationInProgress = False
     else:
       layerOperationInProgress = False
```

### Operations that bypass `processCsharpResult` (by design)

`IsolatedSegments` and `Tree` have an interactive point-selection state (`"Select"`)
that must be handled before any result dispatch.  Their pattern is:

```python
if resMessage in ("False", "Cancelled"):
    return
if resMessage == "Select":
    # activate map tool
    return
# For "shps" and errors, clean up tool state then:
self.processCsharpResult(resMessage, "", onOpenLayers=self.runLoadIsolatedSegmentLayers)
```

`AnalysisOptions` pre-processes the `"True:units text"` response to extract the units
label before normalising to `"commit"` and calling `processCsharpResult`.

---

## 8. `layerOperationInProgress` flag

`runLegendChanged` is connected to QGIS's `layerTreeRoot().layerOrderChanged` and
`nameChanged` signals.  When any layer is added to the legend (even during an in-place
reload that adds a layer for the first time), these signals fire and `runLegendChanged`
would call `defineCurrentProject()` and `updateMetadata()` in the middle of the
layer-opening operation.

`layerOperationInProgress` guards against this:

```python
def runLegendChanged(self):
    if self.isUnloading:
        return
    if not self.layerOperationInProgress:
        self.defineCurrentProject()
        ...
        self.updateMetadata()
```

`processCsharpResult` sets it to `True` before opening layers and `runOpenTemporaryFiles`
(or the custom `onOpenLayers` callback) resets it to `False` when done.
When no layers need to be opened, `processCsharpResult` resets it to `False` immediately.

`openRemoveSpecificLayers` (Layer Management dialog) also sets it to `True` before its
own remove+reopen sequence.

---

## 9. `runTask` — where it is still used

`QGISRedLayerUtils.runTask(A, B)` runs `A()` synchronously then schedules `B()` via
`QTimer.singleShot(0, B)`.

The DLL result flow (§7) no longer uses it — all open calls are direct.  It survives
in two places:

| Call site | A | B | Why kept |
|-----------|---|---|---|
| `openRemoveSpecificLayers` | `removeLayers` | `openSpecificLayers` | Layer Management dialog explicitly removes layers before reopening with a different CRS or set |
| `openSpecificLayers` | `openSpecificLayersProcess` | `setExtent` | Defers extent zoom until after layers are rendered |

---

## 10. QLR mechanism — removed

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

## 11. Adding a new DLL operation — checklist

1. DLL writes output to `tempFolder` (third parameter), not directly to `projectDir`.
2. Python copies files from `tempFolder` → final destination with `shutil.copy2()` + `os.remove()`.
3. Call the appropriate `open*Layers()` method — it uses `_tryReloadExistingLayer()` internally.
4. Do **not** call `removeLayers()` / `removeMapLayer()` before step 2.
5. Do **not** use `runTask(remove..., open...)` — call the open method directly.
6. If the layer uses a data-driven style (categorized, graduated…), add a post-reload style
   refresh inside `openLayer()` following the pattern in §4.
