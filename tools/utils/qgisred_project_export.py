# -*- coding: utf-8 -*-
"""Packaging of a QGISRed project into a portable ZIP file (and back).

The goal is that another user can import the ZIP and get the project back *including its map
visualization* (the .qgs/.qgz) and the third-party layers it references.

Terminology — "external data"
-----------------------------
Here, "external data" means layers in the QGIS project that do NOT belong to QGISRed: background
cartography, DTM rasters, orthophotos, etc. Do not confuse it with
``LayerManagementSection.getComplementaryLayersOpened()``, which is an unrelated concept (QGISRed's
own *optional* element layers such as Isolation Valves or Meters, that live inside the Inputs group).

The export root
---------------
Everything exported shares a common ancestor folder, the *export root*, which by the rules of this
feature can only be one of two things:

  * ``STRUCTURE_PROJECT`` — the export root is the project folder itself. The ZIP holds a single
    project folder with everything inside.
  * ``STRUCTURE_PARENT``  — the export root is the project folder's parent. The ZIP holds the
    .qgs/.qgz plus sibling folders, one of them being the project folder and the rest holding
    external data.

Structure B is used when the .qgz sits one level above the project folder, or when external data
lives in folders parallel to it. Since every included path keeps its path relative to the export
root, ``relpath(path, exportRoot)`` can never start with ``..``, and the datasources inside the
.qgz stay valid after extraction — so importing needs no path rewriting at all.
"""
from contextlib import suppress
import datetime
import json
import ntpath
import os
import posixpath
import re
import shutil
import tempfile
import urllib.parse
import xml.sax.saxutils  # nosec B406 — only escape()/unescape() string helpers used, not XML parsing
from xml.etree import ElementTree  # nosec B405 — parses local project files only, no external input
from zipfile import ZipFile, ZIP_DEFLATED

from .qgisred_filesystem_utils import (
    DIR_BACKUPS, DIR_RESULTS, DIR_ISSUES, DIR_QUERIES, DIR_AUXILIARY_LAYERS,
    QGISRedFileSystemUtils,
)
from .qgisred_project_io import (
    QGISRedProjectIO,
    RE_DATASOURCE_ATTR_DQ, RE_DATASOURCE_ATTR_SQ, RE_DATASOURCE_ELEMENT,
    URI_SUFFIX_SEPARATOR, isRemoteDatasource,
)

SCHEMA_VERSION = 1
MANIFEST_NAME = "qgisred_export.json"

# Zip layouts (see the module docstring)
STRUCTURE_PROJECT = "project"
STRUCTURE_PARENT = "parent"

# Where a referenced path lives, relative to the project folder
SCOPE_PROJECT = "project"   # under ProjectDirectory            → fits structure A
SCOPE_SIBLING = "sibling"   # under dirname(ProjectDirectory)   → forces structure B
SCOPE_OUTSIDE = "outside"   # anywhere else                     → cannot be exported
SCOPE_REMOTE = "remote"     # WMS/XYZ/database — nothing to copy, never blocking

# Machine-readable reasons. This module is UI-free: all user-facing wording lives in the dialogs.
REASON_QGZ_OUTSIDE = "qgz_out_of_scope"
REASON_NO_QGZ = "no_qgis_project"
REASON_EXTERNAL_OUTSIDE = "external_out_of_scope"
REASON_EXTERNAL_EXCLUDED = "external_excluded_by_user"
REASON_PROJECT_IS_ROOT = "project_dir_is_drive_root"
REASON_UNSAFE_MEMBER = "unsafe_zip_member"
REASON_NO_PIPES_IN_ZIP = "no_pipes_in_zip"
REASON_SCHEMA_TOO_NEW = "manifest_schema_too_new"

# Recognises the one file that makes an archive a QGISRed project, at any depth
RE_PIPES_MEMBER = re.compile(r"^(?:(?P<folder>.*)/)?(?P<net>[^/]+)_Pipes\.shp$", re.IGNORECASE)

KNOWN_CONTENT_GROUPS = (
    ("results", DIR_RESULTS),
    ("issues", DIR_ISSUES),
    ("queries", DIR_QUERIES),
    ("auxiliary", DIR_AUXILIARY_LAYERS),
)


def norm(path):
    """Canonical form used for every path comparison in this module."""
    if not path:
        return ""
    return os.path.normcase(os.path.normpath(os.path.realpath(path)))


def relativeToRoot(path, root):
    """Posix path of `path` relative to `root`, or None when it falls outside root.

    Both sides go through realpath first, because the project folder comes from the layer tree /
    the .gpl registry while the .qgz path comes from the metadata file, and the two may disagree on
    symlinks or short names even when they point at the same folder.
    """
    if not path or not root:
        return None
    relative = os.path.relpath(os.path.realpath(path), os.path.realpath(root))
    if relative == os.curdir:
        return ""
    if relative.startswith(os.pardir):
        return None
    return relative.replace(os.sep, "/")


def safeJoin(root, relativePath):
    """Joins relativePath onto root, refusing anything that would escape root.

    Guards against zip-slip: '..' traversal, absolute POSIX/Windows paths and drive letters.
    Returns the absolute joined path; raises ValueError otherwise.
    """
    if relativePath is None:
        raise ValueError(REASON_UNSAFE_MEMBER)
    candidate = str(relativePath).replace("\\", "/")
    if candidate in ("", "."):
        return os.path.realpath(root)
    if posixpath.isabs(candidate) or ntpath.isabs(candidate):
        raise ValueError(REASON_UNSAFE_MEMBER)
    firstComponent = candidate.split("/")[0]
    if ":" in firstComponent:
        raise ValueError(REASON_UNSAFE_MEMBER)

    rootReal = os.path.realpath(root)
    target = os.path.realpath(os.path.join(rootReal, *[p for p in candidate.split("/") if p not in ("", ".")]))
    if target != rootReal and not target.startswith(rootReal + os.sep):
        raise ValueError(REASON_UNSAFE_MEMBER)
    return target


class ExternalItem:
    """A file or folder referenced by the QGIS project that does not belong to QGISRed."""

    def __init__(self, source, kind, scope, relPath=None, layerNames=None, sizeBytes=0,
                 sidecars=None, rawValues=None):
        self.source = source          # absolute real path on disk (no |layername= suffix)
        self.kind = kind              # "file" | "folder" | "remote"
        self.scope = scope            # SCOPE_*
        self.relPath = relPath        # posix path relative to the export root, or None
        self.layerNames = layerNames or []
        self.sizeBytes = sizeBytes
        self.sidecars = sidecars or []  # absolute paths sharing the same stem (.shx, .dbf, .prj…)
        self.rawValues = rawValues or []  # original datasource strings, for reference
        self.selected = True          # set by applySelection from the user's per-layer choice
        self.placements = []

    @property
    def isExportable(self):
        return self.scope in (SCOPE_PROJECT, SCOPE_SIBLING)

    @property
    def displayName(self):
        if self.layerNames:
            return ", ".join(self.layerNames)
        return os.path.basename(self.source) or self.source


class ContentGroup:
    """An optional subfolder of the project that the user can choose to include or omit."""

    def __init__(self, key, dirName, exists=False, fileCount=0, sizeBytes=0):
        self.key = key
        self.dirName = dirName
        self.exists = exists
        self.fileCount = fileCount
        self.sizeBytes = sizeBytes


class ExportPlan:
    """Everything the dialog needs to render, and the stager needs to run, one export."""

    def __init__(self, projectDirectory, networkName):
        self.projectDirectory = projectDirectory
        self.networkName = networkName
        self.qgisPath = None          # absolute path to the .qgz/.qgs, or None
        self.qgisScope = None         # SCOPE_* of the .qgz, or None when absent
        self.exportRoot = None
        self.structure = STRUCTURE_PROJECT
        self.projectFolderRel = ""    # "" for structure A, basename(projectDirectory) for B
        self.externalItems = []
        self.contentGroups = []
        self.includeGroups = set()
        self.includeExternal = True
        self.baseFileCount = 0
        self.baseSizeBytes = 0
        self.blockingReasons = []

    @property
    def inScopeItems(self):
        return [item for item in self.externalItems if item.isExportable]

    @property
    def selectedExternalItems(self):
        return [item for item in self.externalItems if item.isExportable and item.selected]

    @property
    def outOfScopeItems(self):
        return [item for item in self.externalItems if item.scope == SCOPE_OUTSIDE]

    @property
    def omittedGroups(self):
        return [g for g in self.contentGroups if g.exists and g.key not in self.includeGroups]

    @property
    def isValid(self):
        return not self.blockingReasons

    def externalSizeBytes(self):
        return sum(item.sizeBytes for item in self.selectedExternalItems)

    def selectedSizeBytes(self):
        total = self.baseSizeBytes
        total += sum(g.sizeBytes for g in self.contentGroups if g.key in self.includeGroups)
        return total + self.externalSizeBytes()


class ZipInspection:
    """What an exported ZIP holds, worked out without extracting anything."""

    def __init__(self):
        self.structure = STRUCTURE_PROJECT
        # "" normally; "<folder>/" when the archive was re-wrapped around its own root folder
        # (e.g. someone extracted it and zipped the folder again). Every relative path below
        # already includes it, so extraction stays verbatim and the internal layout is preserved.
        self.rootPrefix = ""
        self.projectFolderRel = ""     # posix path of the project folder inside the ZIP
        self.networkName = ""
        self.qgisProjectRel = None     # posix path of the .qgz/.qgs, or None
        self.externalRel = []          # posix paths/prefixes of the complementary data
        self.manifest = None           # the parsed manifest, or None for a legacy/hand-made ZIP
        self.members = []              # every file entry in the archive
        self.projectSizeBytes = 0
        self.externalSizeBytes = 0
        self.isValid = False
        self.reason = None

    @property
    def hasQgisProject(self):
        return bool(self.qgisProjectRel)

    @property
    def hasExternalData(self):
        return bool(self.externalRel)

    @property
    def hasOwnRootFolder(self):
        """True when the ZIP already carries the folder the project must live in."""
        return bool(self.projectFolderRel)

    def isExternalMember(self, name):
        for prefix in self.externalRel:
            if name == prefix or name.startswith(prefix + "/"):
                return True
        return False


class QGISRedProjectPackage:
    """Builds and inspects portable ZIP packages of a QGISRed project."""

    def __init__(self, projectDirectory="", networkName="", iface=None):
        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName
        self.iface = iface

    def _io(self):
        return QGISRedProjectIO(self.ProjectDirectory, self.NetworkName, self.iface)

    """Classification"""

    def parentDirectory(self):
        return os.path.dirname(os.path.normpath(self.ProjectDirectory))

    def classifyPath(self, path):
        """Returns the SCOPE_* of a local path with respect to the project folder."""
        if not path:
            return SCOPE_OUTSIDE
        target = norm(path)
        projectDir = norm(self.ProjectDirectory)
        if target == projectDir or target.startswith(projectDir + os.sep):
            return SCOPE_PROJECT
        parentDir = norm(self.parentDirectory())
        # Guard against a project folder at a drive root, where parent == project
        if parentDir and parentDir != projectDir:
            if target == parentDir or target.startswith(parentDir + os.sep):
                return SCOPE_SIBLING
        return SCOPE_OUTSIDE

    def classifyQgisLocation(self):
        """Returns (scope, qgisPath). Both None when the project has no QGIS project file.

        The .qgz is only accepted inside the project folder or exactly one level above it; anywhere
        else the user must relocate it with the Move command first.
        """
        io = self._io()
        qgisBase = io.getQGisProjectBase(self.ProjectDirectory, self.NetworkName)
        qgisPath = io.findQGisProjectFile(qgisBase)
        if not qgisPath:
            return None, None
        qgisDir = os.path.dirname(qgisPath)
        scope = self.classifyPath(qgisDir)
        if scope == SCOPE_SIBLING and norm(qgisDir) != norm(self.parentDirectory()):
            # A sibling *subfolder* is not "one level above" — only the parent folder itself is.
            scope = SCOPE_OUTSIDE
        return scope, qgisPath

    def computeExportRoot(self, qgisScope, selectedItems):
        """Returns (exportRoot, structure, projectFolderRel) for the items actually being exported."""
        needsParent = qgisScope == SCOPE_SIBLING
        if not needsParent:
            needsParent = any(item.scope == SCOPE_SIBLING for item in selectedItems)

        if not needsParent:
            return os.path.normpath(self.ProjectDirectory), STRUCTURE_PROJECT, ""

        parentDir = self.parentDirectory()
        projectFolderRel = os.path.basename(os.path.normpath(self.ProjectDirectory))
        if not parentDir or not projectFolderRel:
            # Project folder is a drive root: structure B cannot be represented.
            return os.path.normpath(self.ProjectDirectory), STRUCTURE_PROJECT, ""
        return os.path.normpath(parentDir), STRUCTURE_PARENT, projectFolderRel

    """Content groups"""

    def _walkProjectFiles(self, folder):
        """Returns (fileCount, sizeBytes) for files under folder that belong to this network."""
        prefix = (self.NetworkName + "_").lower()
        count = 0
        size = 0
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d.lower() != DIR_BACKUPS.lower()]
            for name in files:
                if not name.lower().startswith(prefix):
                    continue
                count += 1
                with suppress(OSError):
                    size += os.path.getsize(os.path.join(root, name))
        return count, size

    def inspectContentGroups(self):
        """Detects the optional subfolders that hold data for this network.

        The four known groups are always listed (disabled when empty) so the dialog also says what
        the project does *not* have. Any other first-level subfolder holding `<Net>_*` files is
        discovered and offered too: the DLL has renamed its output folders before (a project can
        carry both "Auxiliary Layers" and a legacy "AuxiliaryLayers"), and a hardcoded list would
        silently ship those files with no way to leave them out and no weight in the size estimate.

        `backups/` is deliberately never listed: it is a legacy folder of the removed Backup
        command, and it is never counted nor exported.
        """
        groups = []
        seen = set()
        for key, dirName in KNOWN_CONTENT_GROUPS:
            folder = os.path.join(self.ProjectDirectory, dirName)
            if os.path.isdir(folder):
                fileCount, sizeBytes = self._walkProjectFiles(folder)
            else:
                fileCount, sizeBytes = 0, 0
            # A folder that exists but holds no file of this network counts as absent: there is
            # nothing to export, so its checkbox must come up disabled.
            groups.append(ContentGroup(key, dirName, fileCount > 0, fileCount, sizeBytes))
            seen.add(dirName.lower())

        for dirName in self._discoverExtraGroupFolders(seen):
            fileCount, sizeBytes = self._walkProjectFiles(os.path.join(self.ProjectDirectory, dirName))
            groups.append(ContentGroup(dirName, dirName, True, fileCount, sizeBytes))
        return groups

    def _discoverExtraGroupFolders(self, knownLowercase):
        """First-level subfolders holding project files that are not one of the known groups."""
        found = []
        with suppress(OSError):
            for name in sorted(os.listdir(self.ProjectDirectory)):
                if name.lower() in knownLowercase or name.lower() == DIR_BACKUPS.lower():
                    continue
                folder = os.path.join(self.ProjectDirectory, name)
                if not os.path.isdir(folder):
                    continue
                if self._walkProjectFiles(folder)[0]:
                    found.append(name)
        return found

    def inspectBaseFiles(self):
        """Returns (fileCount, sizeBytes) of the always-exported files at the project root."""
        prefix = (self.NetworkName + "_").lower()
        count = 0
        size = 0
        with suppress(OSError):
            for name in os.listdir(self.ProjectDirectory):
                path = os.path.join(self.ProjectDirectory, name)
                if os.path.isfile(path) and name.lower().startswith(prefix):
                    count += 1
                    with suppress(OSError):
                        size += os.path.getsize(path)
        return count, size

    """External data — enumerated from the .qgz on disk, not from the live layer tree"""

    def readQgisXmlMembers(self, qgisPath):
        """Returns [(memberName, xmlText)] for every .qgs document in the project file.

        memberName is None for a plain .qgs file (there is no containing archive).
        """
        members = []
        if not qgisPath or not os.path.isfile(qgisPath):
            return members
        if qgisPath.lower().endswith(".qgz"):
            with ZipFile(qgisPath, "r") as zin:
                for name in zin.namelist():
                    if name.endswith(".qgs"):
                        members.append((name, zin.read(name).decode("utf-8", "replace")))
        else:
            with open(qgisPath, "r", encoding="utf-8", errors="replace") as f:
                members.append((None, f.read()))
        return members

    def readLayerTree(self, xmlText):
        """Maps layer id -> (groupPath, name) from the project's <layer-tree-group> hierarchy.

        This is what lets the dialog show the complementary layers the way QGIS shows them, groups
        and all, without a live QGIS session. Group names come out translated when the project was
        saved in another locale, which does not matter: QGISRed's own layers are filtered out by
        file name, never by group name.
        """
        placement = {}

        def walk(node, path):
            for child in node:
                if child.tag == "layer-tree-group":
                    name = child.get("name") or ""
                    walk(child, path + (name,) if name else path)
                elif child.tag == "layer-tree-layer":
                    layerId = child.get("id")
                    if layerId:
                        placement[layerId] = (path, child.get("name") or "")

        with suppress(Exception):
            root = ElementTree.fromstring(xmlText)  # nosec B314 — local project file
            for tree in root.iter("layer-tree-group"):
                walk(tree, ())
                break  # the first one is the root group; walk() covers everything below it
        return placement

    def iterQgisDatasources(self, qgisPath):
        """Yields (rawValue, layerName, groupPath) for every datasource the project references.

        A primary pass over <maplayer> nodes gives datasource + display name + position in the
        layer tree; a secondary regex sweep catches values outside <maplayer> (print layouts, SVG
        markers, meshes), which have no tree position and yield (None, None).
        """
        for _memberName, xmlText in self.readQgisXmlMembers(qgisPath):
            seenRaw = set()
            placement = self.readLayerTree(xmlText)
            with suppress(Exception):
                root = ElementTree.fromstring(xmlText)  # nosec B314 — local project file
                for maplayer in root.iter("maplayer"):
                    datasource = maplayer.find("datasource")
                    if datasource is None or not datasource.text:
                        continue
                    idNode = maplayer.find("id")
                    groupPath, treeName = placement.get(idNode.text if idNode is not None else None,
                                                        ((), None))
                    layerNode = maplayer.find("layername")
                    layerName = treeName or (layerNode.text if layerNode is not None else None)
                    seenRaw.add(datasource.text)
                    yield datasource.text, layerName, groupPath

            for pattern, group in ((RE_DATASOURCE_ATTR_DQ, 4), (RE_DATASOURCE_ATTR_SQ, 4),
                                   (RE_DATASOURCE_ELEMENT, 2)):
                for match in pattern.finditer(xmlText):
                    raw = match.group(group)
                    if raw in seenRaw:
                        continue
                    seenRaw.add(raw)
                    yield raw, None, ()

    def resolveDatasource(self, rawValue, qgisDir):
        """Resolves a raw datasource string to (absolutePath, uriSuffix, isRemote).

        Mirrors the normalization done by QGISRedProjectIO._applyQGisReplacements so that whatever
        we enumerate here is exactly what the rewriter will act upon. absolutePath is None for
        remote sources and for relative paths that cannot be resolved.
        """
        logical = xml.sax.saxutils.unescape(rawValue or "")
        if not logical:
            return None, "", False
        if isRemoteDatasource(logical):
            return None, "", True

        value = urllib.parse.unquote(logical)
        if value.startswith("file:///"):
            value = value[8:]
        elif value.startswith("file://"):
            value = value[7:]

        suffix = ""
        if URI_SUFFIX_SEPARATOR in value:
            index = value.find(URI_SUFFIX_SEPARATOR)
            suffix = value[index:]
            value = value[:index]
        if not value:
            return None, suffix, False

        if os.path.isabs(value):
            return os.path.realpath(value), suffix, False
        if qgisDir:
            return os.path.realpath(os.path.join(qgisDir, value)), suffix, False
        return None, suffix, False

    def _isOwnProjectFile(self, path):
        """True when the path is one of QGISRed's own files.

        On-disk equivalent of the `qgisred_identifier` custom property: identifiers map 1:1 to
        `<NetworkName>_*` files inside the project folder. Works without a live layer tree, which
        is what lets the Project Manager export any project in its list, not just the open one.
        """
        if self.classifyPath(path) != SCOPE_PROJECT:
            return False
        return os.path.basename(path).lower().startswith((self.NetworkName + "_").lower())

    def _findSidecars(self, path):
        """Files sharing the stem of path (.shx, .dbf, .prj, .qml, .aux.xml…), excluding it."""
        io = self._io()
        sidecars = []
        parent = os.path.dirname(path)
        stem = norm(io.stripAllExtensions(path))
        with suppress(OSError):
            for name in os.listdir(parent):
                candidate = os.path.join(parent, name)
                if not os.path.isfile(candidate) or norm(candidate) == norm(path):
                    continue
                if norm(io.stripAllExtensions(candidate)) == stem:
                    sidecars.append(candidate)
        return sidecars

    def _folderSize(self, folder):
        size = 0
        for root, _dirs, files in os.walk(folder):
            for name in files:
                with suppress(OSError):
                    size += os.path.getsize(os.path.join(root, name))
        return size

    def collectExternalData(self, qgisPath):
        """Returns the deduplicated list of ExternalItem referenced by the QGIS project."""
        if not qgisPath:
            return []
        qgisDir = os.path.dirname(qgisPath)
        items = {}
        for rawValue, layerName, groupPath in self.iterQgisDatasources(qgisPath):
            absPath, _suffix, isRemote = self.resolveDatasource(rawValue, qgisDir)
            if isRemote:
                continue
            if not absPath or not os.path.exists(absPath):
                continue
            if self._isOwnProjectFile(absPath):
                continue
            # The .qgz itself is handled separately, never as external data
            if norm(absPath) == norm(qgisPath):
                continue

            key = norm(absPath)
            item = items.get(key)
            if item is None:
                isFolder = os.path.isdir(absPath)
                scope = self.classifyPath(absPath)
                sidecars = [] if isFolder else self._findSidecars(absPath)
                if isFolder:
                    sizeBytes = self._folderSize(absPath)
                else:
                    sizeBytes = 0
                    for candidate in [absPath] + sidecars:
                        with suppress(OSError):
                            sizeBytes += os.path.getsize(candidate)
                item = ExternalItem(
                    source=absPath,
                    kind="folder" if isFolder else "file",
                    scope=scope,
                    sizeBytes=sizeBytes,
                    sidecars=sidecars,
                )
                items[key] = item
            if layerName and layerName not in item.layerNames:
                item.layerNames.append(layerName)
            if rawValue not in item.rawValues:
                item.rawValues.append(rawValue)
            if layerName is None and item.placements:
                # A nameless hit is the regex sweep re-catching a layer the <maplayer> pass already
                # placed: the same datasource is escaped differently in the layer-tree attribute, so
                # seenRaw cannot match it. Keeping it would draw a second, group-less row.
                continue
            placement = (tuple(groupPath), layerName or os.path.basename(absPath))
            if placement not in item.placements:
                item.placements.append(placement)
        return list(items.values())

    """Planning"""

    def inspectForExport(self, includeExternal=True, includeGroups=None, externalSources=None):
        """Builds the ExportPlan for this project. Read-only: touches nothing on disk."""
        plan = ExportPlan(self.ProjectDirectory, self.NetworkName)
        plan.qgisScope, plan.qgisPath = self.classifyQgisLocation()
        if plan.qgisScope == SCOPE_OUTSIDE:
            plan.blockingReasons.append(REASON_QGZ_OUTSIDE)

        plan.externalItems = self.collectExternalData(plan.qgisPath)
        plan.contentGroups = self.inspectContentGroups()
        plan.baseFileCount, plan.baseSizeBytes = self.inspectBaseFiles()
        if includeGroups is None:
            includeGroups = {g.key for g in plan.contentGroups if g.exists}

        self.applySelection(plan, includeExternal, includeGroups, externalSources)
        return plan

    def applySelection(self, plan, includeExternal, includeGroups, externalSources=None):
        """Recomputes the export root and the relative paths for a new user selection.

        externalSources is the set of source paths the user ticked (any form accepted, they are
        normalized here); None means "every exportable item", so the plain includeExternal flag
        keeps working for callers that do not offer per-layer control.

        Cheap on purpose: the content groups all live inside the project folder, so only the
        external data can change the A/B structure.
        """
        plan.includeGroups = set(includeGroups)
        wanted = None if externalSources is None else {norm(p) for p in externalSources}
        for item in plan.externalItems:
            item.selected = bool(includeExternal) and item.isExportable and (
                wanted is None or norm(item.source) in wanted
            )
        plan.includeExternal = any(item.selected for item in plan.externalItems)

        plan.exportRoot, plan.structure, plan.projectFolderRel = self.computeExportRoot(
            plan.qgisScope, plan.selectedExternalItems
        )
        for item in plan.externalItems:
            if not item.isExportable:
                item.relPath = None
                continue
            item.relPath = relativeToRoot(item.source, plan.exportRoot)
            if item.relPath is None:
                item.scope = SCOPE_OUTSIDE
                item.selected = False
        return plan

    """Staging and zipping"""

    def _stageProjectFiles(self, plan, stageDir):
        """Copies the project's own files, honouring the content-group selection."""
        excludeDirs = [DIR_BACKUPS]
        excludeDirs += [g.dirName for g in plan.contentGroups if g.key not in plan.includeGroups]

        stageProjectDir = safeJoin(stageDir, plan.projectFolderRel)
        os.makedirs(stageProjectDir, exist_ok=True)
        self._io().processProjectFiles(
            plan.projectDirectory, plan.networkName, plan.networkName,
            stageProjectDir, deleteSource=False, excludeDirs=excludeDirs,
        )
        return stageProjectDir

    def _stageQgisProject(self, plan, stageDir):
        """Copies the .qgz/.qgs (and its siblings) preserving its location relative to the root."""
        if not plan.qgisPath:
            return None, None
        io = self._io()
        qgisDir = os.path.dirname(plan.qgisPath)
        qgisDirRel = relativeToRoot(qgisDir, plan.exportRoot)
        if qgisDirRel is None:
            raise ValueError(REASON_QGZ_OUTSIDE)
        stagedQgisDir = safeJoin(stageDir, qgisDirRel)
        os.makedirs(stagedQgisDir, exist_ok=True)

        qgisBase = io.stripAllExtensions(plan.qgisPath)
        stagedQgisPath = io.processQGisProjectFiles(
            qgisBase, os.path.basename(qgisBase), stagedQgisDir, deleteSource=False
        )
        return stagedQgisPath, stagedQgisDir

    def _stageExternalData(self, plan, stageDir, stageProjectDir):
        """Copies the in-scope external data. Returns (pathMap, stagedItems)."""
        pathMap = {}
        staged = []
        for item in plan.selectedExternalItems:
            target = safeJoin(stageDir, item.relPath)
            if os.path.exists(target):
                pathMap[norm(item.source)] = target
                staged.append(item)
                continue

            if item.kind == "folder":
                shutil.copytree(item.source, target, dirs_exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copy2(item.source, target)
                for sidecar in item.sidecars:
                    shutil.copy2(sidecar, os.path.join(os.path.dirname(target), os.path.basename(sidecar)))
            pathMap[norm(item.source)] = target
            staged.append(item)
        return pathMap, staged

    def buildManifest(self, plan, stagedItems):
        """The machine-readable description of the package, written at the zip root."""
        return {
            "schema": SCHEMA_VERSION,
            "generator": "QGISRed",
            "pluginVersion": self.pluginVersion(),
            "created": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "structure": plan.structure,
            "networkName": plan.networkName,
            "projectFolder": plan.projectFolderRel,
            "qgisProject": self._manifestQgisRel(plan),
            "includedGroups": [g.key for g in plan.contentGroups if g.key in plan.includeGroups],
            "omittedGroups": [g.key for g in plan.omittedGroups],
            "includesExternalData": bool(stagedItems),
            "externalData": [
                {"path": item.relPath, "type": item.kind, "layers": item.layerNames}
                for item in stagedItems
            ],
            "skippedExternalData": [
                {
                    "source": item.source,
                    "layers": item.layerNames,
                    "reason": REASON_EXTERNAL_OUTSIDE if item.scope == SCOPE_OUTSIDE else REASON_EXTERNAL_EXCLUDED,
                }
                for item in plan.externalItems if not item.selected
            ],
        }

    def _manifestQgisRel(self, plan):
        if not plan.qgisPath:
            return None
        return relativeToRoot(plan.qgisPath, plan.exportRoot)

    def stageExport(self, plan, stageDir):
        """Materializes the whole package inside stageDir. Returns the manifest dict."""
        stageProjectDir = self._stageProjectFiles(plan, stageDir)
        stagedQgisPath, stagedQgisDir = self._stageQgisProject(plan, stageDir)
        pathMap, stagedItems = self._stageExternalData(plan, stageDir, stageProjectDir)

        if stagedQgisPath:
            self._io().updateQGisProjectContent(
                stagedQgisPath, plan.networkName, plan.networkName,
                plan.projectDirectory, stageProjectDir,
                os.path.dirname(plan.qgisPath), stagedQgisDir,
                relativizeUnder=stageDir, pathMap=pathMap, raiseErrors=True,
            )
            # Writes "Net.qgz" for structure A and "../Net.qgz" for structure B; openProjectInQgis
            # already resolves both against the project folder.
            self._io().updateMetadataQGisProject(stageProjectDir, plan.networkName, stagedQgisPath)

        manifest = self.buildManifest(plan, stagedItems)
        with open(os.path.join(stageDir, MANIFEST_NAME), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        return manifest

    def writeZip(self, stageDir, zipPath):
        """Zips stageDir into zipPath atomically (via a .part file)."""
        zipDir = os.path.dirname(zipPath)
        if zipDir:
            os.makedirs(zipDir, exist_ok=True)
        partPath = zipPath + ".part"
        with ZipFile(partPath, "w", ZIP_DEFLATED) as zout:
            for root, _dirs, files in os.walk(stageDir):
                for name in files:
                    fullPath = os.path.join(root, name)
                    relPath = os.path.relpath(fullPath, stageDir).replace(os.sep, "/")
                    zout.write(fullPath, relPath)
        os.replace(partPath, zipPath)

    def exportToZip(self, zipPath, includeExternal=True, includeGroups=None, plan=None,
                    externalSources=None):
        """Exports the project to zipPath. Returns (ok, reason, manifest).

        No exception escapes and no `suppress` hides a partial result: a silently incomplete export
        is the worst possible failure mode here, so any error aborts and reports.
        """
        manifest = None
        partPath = zipPath + ".part" if zipPath else ""
        try:
            if plan is None:
                plan = self.inspectForExport(includeExternal=includeExternal, includeGroups=includeGroups,
                                             externalSources=externalSources)
            else:
                selectedGroups = plan.includeGroups if includeGroups is None else includeGroups
                self.applySelection(plan, includeExternal, selectedGroups, externalSources)
            if not plan.isValid:
                return False, plan.blockingReasons[0], None

            with tempfile.TemporaryDirectory() as stageDir:
                manifest = self.stageExport(plan, stageDir)
                self.writeZip(stageDir, zipPath)
            return True, None, manifest
        except Exception as exc:  # noqa: BLE001 — reported to the caller, never swallowed
            if partPath:
                with suppress(OSError):
                    os.remove(partPath)
            return False, str(exc) or exc.__class__.__name__, None

    """Import side"""

    @staticmethod
    def inspectZip(zipPath):
        """Works out the contents of an exported ZIP without extracting it.

        Deterministic when the archive carries a manifest; otherwise it falls back to locating
        `*_Pipes.shp` at any depth, which is what makes the ZIPs produced by older versions of the
        plugin (and hand-made ones) still importable.
        """
        inspection = ZipInspection()
        manifestName = None
        sizes = {}
        try:
            with ZipFile(zipPath, "r") as zin:
                infos = [info for info in zin.infolist() if not info.is_dir()]
                sizes = {info.filename: info.file_size for info in infos}
                inspection.members = [info.filename for info in infos]

                # Refuse the whole archive if any entry could write outside the destination
                with tempfile.TemporaryDirectory() as probeRoot:
                    for name in inspection.members:
                        try:
                            safeJoin(probeRoot, name)
                        except ValueError:
                            inspection.reason = REASON_UNSAFE_MEMBER
                            return inspection

                manifestName = QGISRedProjectPackage._locateManifest(inspection.members)
                if manifestName:
                    inspection.rootPrefix = manifestName[:-len(MANIFEST_NAME)]
                    manifest = json.loads(zin.read(manifestName).decode("utf-8"))
                    if not QGISRedProjectPackage._applyManifest(inspection, manifest):
                        return inspection
                elif not QGISRedProjectPackage._applyHeuristics(inspection):
                    return inspection
        except Exception as exc:  # noqa: BLE001 — reported through the inspection, never swallowed
            inspection.reason = str(exc) or exc.__class__.__name__
            return inspection

        for name, size in sizes.items():
            if name == manifestName:
                continue
            if inspection.isExternalMember(name):
                inspection.externalSizeBytes += size
            else:
                inspection.projectSizeBytes += size
        inspection.isValid = True
        return inspection

    @staticmethod
    def _locateManifest(members):
        """The manifest at the ZIP root, or under a single wrapper folder. None if absent."""
        if MANIFEST_NAME in members:
            return MANIFEST_NAME
        candidates = [
            name for name in members
            if name.endswith("/" + MANIFEST_NAME) and name.count("/") == 1
        ]
        return candidates[0] if len(candidates) == 1 else None

    @staticmethod
    def _applyManifest(inspection, manifest):
        """Fills the inspection from the manifest. False (with a reason) if it cannot be trusted."""
        if int(manifest.get("schema", 0)) > SCHEMA_VERSION:
            inspection.reason = REASON_SCHEMA_TOO_NEW
            return False

        prefix = inspection.rootPrefix
        inspection.manifest = manifest
        inspection.structure = manifest.get("structure") or STRUCTURE_PROJECT
        inspection.networkName = manifest.get("networkName") or ""
        inspection.projectFolderRel = (prefix + (manifest.get("projectFolder") or "")).strip("/")
        qgisProject = manifest.get("qgisProject")
        inspection.qgisProjectRel = (prefix + qgisProject) if qgisProject else None
        inspection.externalRel = [
            prefix + entry["path"] for entry in manifest.get("externalData") or [] if entry.get("path")
        ]
        if not inspection.networkName:
            inspection.reason = REASON_NO_PIPES_IN_ZIP
            return False
        return True

    @staticmethod
    def _applyHeuristics(inspection):
        """Derives the layout from the file names alone, for archives without a manifest."""
        pipes = None
        for name in inspection.members:
            match = RE_PIPES_MEMBER.match(name)
            if match:
                pipes = match
                break
        if not pipes:
            inspection.reason = REASON_NO_PIPES_IN_ZIP
            return False

        inspection.networkName = pipes.group("net")
        inspection.projectFolderRel = (pipes.group("folder") or "").strip("/")
        inspection.structure = STRUCTURE_PARENT if inspection.projectFolderRel else STRUCTURE_PROJECT

        projectPrefix = inspection.projectFolderRel + "/" if inspection.projectFolderRel else ""
        for name in inspection.members:
            lowered = name.lower()
            if not (lowered.endswith(".qgz") or lowered.endswith(".qgs")):
                continue
            folder = posixpath.dirname(name)
            if folder in ("", inspection.projectFolderRel):
                inspection.qgisProjectRel = name
                if lowered.endswith(".qgz"):
                    break  # .qgz wins over .qgs, as it does everywhere else in the plugin

        # Anything at the root that is not the project folder nor the map file is external data.
        # For a flat (structure A) archive everything already lives in the project folder, which is
        # what keeps the legacy `ExternalLayers/` subfolder travelling as part of the project.
        if projectPrefix:
            external = []
            for name in inspection.members:
                if name.startswith(projectPrefix) or name == inspection.qgisProjectRel:
                    continue
                top = name.split("/")[0]
                if top not in external:
                    external.append(top)
            inspection.externalRel = external
        return True

    @staticmethod
    def membersToExtract(inspection, includeExternal=True):
        """Entry names to pull out of the archive: everything but the manifest, minus the
        complementary data when the user chose to leave it behind."""
        members = []
        for name in inspection.members:
            if name == inspection.rootPrefix + MANIFEST_NAME:
                continue
            if not includeExternal and inspection.isExternalMember(name):
                continue
            members.append(name)
        return members

    @staticmethod
    def planExtraction(inspection, destinationRoot, includeExternal=True):
        """Returns (targets, conflicts): what would be written, and what already exists there."""
        targets = []
        conflicts = []
        for name in QGISRedProjectPackage.membersToExtract(inspection, includeExternal):
            target = safeJoin(destinationRoot, name)
            targets.append(target)
            if os.path.exists(target):
                conflicts.append(name)
        return targets, conflicts

    @staticmethod
    def extractZip(zipPath, destinationRoot, inspection, includeExternal=True):
        """Recreates the archive's tree under destinationRoot and returns the project folder.

        No path rewriting happens here: because everything kept its position relative to the export
        root, the datasources inside the .qgz are still correct once the tree is back on disk.
        """
        members = QGISRedProjectPackage.membersToExtract(inspection, includeExternal)
        QGISRedProjectIO().unzipFile(zipPath, destinationRoot, members=members)
        if inspection.projectFolderRel:
            return os.path.normpath(safeJoin(destinationRoot, inspection.projectFolderRel))
        return os.path.normpath(os.path.realpath(destinationRoot))

    """Helpers shared with the dialogs"""

    @staticmethod
    def sanitizeZipFileName(name):
        """Returns a file name safe on every platform, without the .zip extension."""
        candidate = (name or "").strip()
        if candidate.lower().endswith(".zip"):
            candidate = candidate[:-4]
        candidate = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "", candidate).strip().rstrip(".")
        reserved = {"con", "prn", "aux", "nul"}
        reserved.update("com%d" % i for i in range(1, 10))
        reserved.update("lpt%d" % i for i in range(1, 10))
        if candidate.lower() in reserved:
            return ""
        return candidate

    @staticmethod
    def buildZipPath(folder, name):
        """Joins folder and name, enforcing exactly one .zip extension."""
        cleaned = QGISRedProjectPackage.sanitizeZipFileName(name)
        if not cleaned or not folder:
            return ""
        return os.path.join(folder, cleaned + ".zip")

    @staticmethod
    def pluginVersion():
        return QGISRedFileSystemUtils().getPluginVersion()
