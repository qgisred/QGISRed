# -*- coding: utf-8 -*-
from contextlib import suppress
import os
import json
import shutil
import tempfile
import re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree  # nosec B405 — parses local project files only, no external input
import urllib.parse
import xml.sax.saxutils  # nosec B406 — only escape()/unescape() string helpers used, not XML parsing

from qgis.PyQt.QtCore import QCoreApplication, QFileInfo
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsLayerTreeGroup, QgsVectorLayer,
    QgsLayerDefinition
)
from .qgisred_ui_utils import QGISRedUIUtils
from .qgisred_filesystem_utils import (
    DIR_ISSUES, DIR_QUERIES, DIR_RESULTS,
    LAYER_TYPE_CONFIG,
)

# What counts as a datasource in the QGIS project XML. Single source of truth, shared by the
# rewriter below and by the enumerator in qgisred_project_export, so the two can never disagree
# about which values are paths.
RE_DATASOURCE_ATTR_DQ = re.compile(r'(source|url|filename)(=)(")([^"]+)(")')
RE_DATASOURCE_ATTR_SQ = re.compile(r"(source|url|filename)(=)(')([^']+)(')")
RE_DATASOURCE_ELEMENT = re.compile(r'(<datasource>)([^<]+)(</datasource>)')

# Markers that identify a connection string (WMS, XYZ, postgres…) rather than a local path.
REMOTE_MARKERS = ("url=", "crs=", "type=", "service=", "request=")
REMOTE_PREFIXES = ("http://", "https://")

# Suffix QGIS appends to a file datasource, e.g. "roads.shp|layername=roads"
URI_SUFFIX_SEPARATOR = "|"


def isRemoteDatasource(value):
    """True when the datasource is a connection string rather than a local file path."""
    lowered = (value or "").lower()
    if lowered.startswith(REMOTE_PREFIXES):
        return True
    return any(marker in lowered for marker in REMOTE_MARKERS)


class QGISRedProjectIO:
    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    """Interal Helpers"""

    def tr(self, message):
        return QCoreApplication.translate("QGISRedProjectIO", message)

    def _fs(self):
        from .qgisred_filesystem_utils import QGISRedFileSystemUtils
        return QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _styling(self):
        from .qgisred_styling_utils import QGISRedStylingUtils
        return QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    def _layers(self):
        from .qgisred_layer_utils import QGISRedLayerUtils
        return QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)

    _GROUP_CONFIG = {
        "Inputs":                          {"subdir": "",         "tree_path": ["Inputs"],  "flags": {}},
        "Issues":                          {"subdir": DIR_ISSUES, "tree_path": ["Issues"],  "flags": {"issues": True}},
        "Results":                         {"subdir": DIR_RESULTS, "tree_path": ["Results"], "flags": {"results": True}},
        "Issues/Connectivity":             LAYER_TYPE_CONFIG["Connectivity"],
        "Issues/HydraulicSectors":         LAYER_TYPE_CONFIG["HydraulicSectors"],
        "Auxiliary Layers/DemandSectors":  LAYER_TYPE_CONFIG["DemandSectors"],
        "Queries/IsolatedSegments":        LAYER_TYPE_CONFIG["IsolatedSegments"],
        "Auxiliary Layers/DemandsBuilder": LAYER_TYPE_CONFIG["DemandsBuilder"],
    }

    def _openGroupByName(self, groupName, layerNames):
        from .qgisred_layer_utils import QGISRedLayerUtils
        from .qgisred_styling_utils import QGISRedStylingUtils

        # Special case: Tree subgroups — old style "Queries/Tree_*" or new style "Queries/Trees/Tree: ..."
        if re.match(r'^Queries/(?:Tree_|Trees/Tree:)', groupName):
            # Layer names are sanitized ASCII (e.g. "Nodes_Tree_J5_Union").
            # Recover the actual tree name (e.g. "J5-Unión") by scanning its subfolder.
            import glob as _glob
            import unicodedata as _ud
            sanitized_tree = None
            for name in layerNames:
                m = re.match(r'^(?:Nodes|Links)_Tree_(.+)$', name)
                if m:
                    sanitized_tree = m.group(1)
                    break
            if sanitized_tree is None:
                return
            queries_dir = os.path.join(self.ProjectDirectory, DIR_QUERIES)
            tree_name = None
            tree_dir = None
            # Each tree lives in Queries/Trees/ as files named with the full tree name.
            patterns = [
                os.path.join(queries_dir, "Trees", self.NetworkName + "_Nodes_Tree_*.shp"),
                os.path.join(queries_dir, "Trees", self.NetworkName + "_Links_Tree_*.shp"),
                os.path.join(queries_dir, "Trees", self.NetworkName + "_Tree_*_Nodes.shp"),
                os.path.join(queries_dir, "Trees", self.NetworkName + "_Tree_*_Links.shp"),
            ]
            for pattern in patterns:
                for path in _glob.glob(pattern):
                    basename = os.path.splitext(os.path.basename(path))[0]
                    candidate = None
                    prefix1 = self.NetworkName + "_Nodes_Tree_"
                    prefix2 = self.NetworkName + "_Links_Tree_"
                    prefix3 = self.NetworkName + "_Tree_"
                    if basename.startswith(prefix1):
                        candidate = basename[len(prefix1):]
                    elif basename.startswith(prefix2):
                        candidate = basename[len(prefix2):]
                    elif basename.startswith(prefix3) and basename.endswith("_Nodes"):
                        candidate = basename[len(prefix3):-len("_Nodes")]
                    elif basename.startswith(prefix3) and basename.endswith("_Links"):
                        candidate = basename[len(prefix3):-len("_Links")]
                    if candidate is None:
                        continue
                    norm = _ud.normalize("NFKD", candidate).encode("ascii", "ignore").decode("ascii")
                    norm = norm.replace("-", "_")
                    if norm == sanitized_tree:
                        tree_name = candidate
                        tree_dir = os.path.dirname(path)
                        break
                if tree_name is not None:
                    break
            if tree_name is None or tree_dir is None:
                return
            utils = QGISRedLayerUtils(tree_dir, self.NetworkName, self.iface)
            # Create a group named with the tree name
            group = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Trees", tree_name])
            for name in reversed(layerNames):
                is_link = name.lower().startswith("links")
                utils.openTreeLayer(group, "Links" if is_link else "Nodes", tree_name, link=is_link)
            return

        # Try full path as key (e.g. "Issues/HydraulicSectors", or legacy "HydraulicSectors")
        cfg = self._GROUP_CONFIG.get(groupName)
        if cfg is not None:
            tree_path = cfg["tree_path"]
            subdir = cfg["subdir"]
            flags = cfg["flags"]
            full_tree_path = tree_path
        else:
            # Dynamic paths — e.g. "Results/Base": use top-level key + sub-parts
            parts = groupName.split("/")
            top = parts[0]
            sub_parts = parts[1:]
            cfg = self._GROUP_CONFIG.get(top)
            if cfg is None:
                return  # unknown group — skip silently
            tree_path = cfg["tree_path"]
            subdir = cfg["subdir"]
            flags = cfg["flags"]
            full_tree_path = tree_path + sub_parts

        top = groupName.split("/")[0]
        layersDir = os.path.join(self.ProjectDirectory, subdir) if subdir else self.ProjectDirectory
        utils = QGISRedLayerUtils(layersDir, self.NetworkName, self.iface)
        group = utils.getOrCreateNestedGroup([self.NetworkName] + full_tree_path)

        if top == "Results":
            from ...ui.analysis.qgisred_results_data import (
                apply_result_column_visibility, infer_stat_en_from_layer,
                _RESULT_FIELD_DISPLAY_NAMES, resultStyleName,
            )
            from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils
            stat_en = QgsProject.instance().readEntry("QGISRed", "project_statistics", "NONE")[0]
            quality_simulated = QGISRedProjectUtils.getQualityModel().upper() != "NONE"

            styling = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)

            # Pass 1: open all layers first. orderResultLayers (called inside openLayer)
            # clones non-point layers on each call, so all cloning must finish before
            # we apply styles — otherwise later openLayer calls would re-clone and lose
            # the renderer/legend we just set.
            style_queue = []
            for name in reversed(layerNames):
                # "Base_Node_Pressure[_Stats]" → file_name="Base_Node", layer_type="Node",
                #                                variable="Pressure", is_stats=False/True
                m = re.match(r'^(.+_(Node|Link))_(.+?)(_Stats)?$', name, re.IGNORECASE)
                if m:
                    file_name  = m.group(1)
                    layer_type = m.group(2)
                    variable   = m.group(3)
                    is_stats   = m.group(4) is not None
                else:
                    file_name, layer_type, variable, is_stats = name, None, None, False
                utils.openLayer(group, file_name, **flags)
                style_queue.append((file_name, layer_type, variable, is_stats))

            # Pass 2: apply styles to the final layer instances (after all cloning is done).
            for file_name, layer_type, variable, is_stats in style_queue:
                if not variable or not layer_type:
                    continue
                layer_path = utils._fs().generatePath(layersDir, self.NetworkName + "_" + file_name + ".shp")
                opened = utils._findLayerByPath(layer_path)
                if not opened:
                    continue
                scenario = file_name.rsplit("_", 1)[0]  # "Base_Node" → "Base"
                QgsProject.instance().writeEntry("QGISRed", f"results_{scenario}_{layer_type}", variable)
                # Load QML template (color ramp + symbol complexity), fix the classAttribute
                # (QML templates may have a wrong default like 'Time'), then add a null/else
                # rule so out-of-range features are visible rather than invisible.
                styling.setStyle(opened, resultStyleName(layer_type, variable))
                renderer = opened.renderer()
                from qgis.core import QgsGraduatedSymbolRenderer
                if isinstance(renderer, QgsGraduatedSymbolRenderer):
                    class_attr = "abs(Flow)" if variable == "Flow" else variable
                    renderer.setClassAttribute(class_attr)
                    opened.setRenderer(renderer)
                styling.applyNullStyle(opened)
                template = QCoreApplication.translate("_ResultsRenderingMixin", layer_type + " %1")
                display_var = _RESULT_FIELD_DISPLAY_NAMES.get(variable, variable)
                translated_var = QCoreApplication.translate("QGISRedResultsDock", display_var)
                opened.setName(template.replace("%1", translated_var))
                if is_stats:
                    # project_statistics is only available when a .qgs file was saved.
                    # Without it, read the translated stat label from the Statistics field.
                    effective_stat = stat_en if stat_en.strip().upper() not in ("NONE", "") \
                        else infer_stat_en_from_layer(opened)
                else:
                    effective_stat = "NONE"
                apply_result_column_visibility(opened, layer_type, effective_stat, quality_simulated)
                opened.triggerRepaint()
        else:
            for name in reversed(layerNames):
                utils.openLayer(group, name, **flags)
            if top == "Inputs":
                for child in group.children():
                    child.setCustomProperty("showFeatureCount", True)

    def _openGroupsNode(self, node, parent_path):
        """Recursively open layers from a nested <Groups> XML subtree."""
        # Sub-levels use insertGroup(0, ...) so reversing preserves XML order.
        # Top-level groups (parent_path="") use _getInsertPosition and must NOT be reversed.
        children = reversed(list(node)) if parent_path else node
        for child in children:
            if child.tag == "Layer":
                continue
            tag = child.tag.replace(" ", "")
            current_path = (parent_path + "/" if parent_path else "") + tag
            layer_children = [c.text for c in child if c.tag == "Layer" and c.text]
            if layer_children:
                self._openGroupByName(current_path, layer_children)
            sub_groups = [c for c in child if c.tag != "Layer"]
            if sub_groups:
                self._openGroupsNode(child, current_path)

    def _renameGroupsToLocale(self):
        """After QgsProject.read(), rename all QGISRed groups to the active locale display names."""
        from .qgisred_layer_utils import QGISRedLayerUtils
        self._renameGroupsRecursive(QgsProject.instance().layerTreeRoot(), QGISRedLayerUtils)

    def _renameGroupsRecursive(self, parent, utils_cls):
        _canonical_names = set(utils_cls._IDENTIFIER_TO_CANONICAL.values())
        for child in parent.children():
            if not isinstance(child, QgsLayerTreeGroup):
                continue
            identifier = child.customProperty("qgisred_identifier")
            canonical = utils_cls._IDENTIFIER_TO_CANONICAL.get(identifier)
            if canonical is not None:
                # Group has a QGISRed identifier → rename to current locale
                translated = utils_cls._translateGroupName(canonical)
                if child.name() != translated:
                    child.setName(translated)
            elif child.name() in _canonical_names:
                # Old project without identifier but English canonical name → rename + assign identifier
                utils_cls.setGroupIdentifier(child, child.name())
                translated = utils_cls._translateGroupName(child.name())
                if child.name() != translated:
                    child.setName(translated)
            else:
                # Tree groups in canonical English form (old projects)
                if child.name().startswith("Tree: "):
                    new_name = utils_cls._translateGroupName(child.name())
                    if child.name() != new_name:
                        child.setName(new_name)
                else:
                    # Tree groups saved in another locale (e.g. Spanish → French)
                    tree_word = QCoreApplication.translate("QGISRedGroups", "Tree")
                    if child.name().startswith(tree_word + ": "):
                        tree_name = child.name()[len(tree_word) + 2:]
                        new_name = utils_cls._translateGroupName("Tree: " + tree_name)
                        if child.name() != new_name:
                            child.setName(new_name)
            self._renameGroupsRecursive(child, utils_cls)

    def _applyQGisReplacements(self, content, oldName, newName, oldFolder, newFolder,
                               oldQgisDir=None, newQgisDir=None,
                               relativizeUnder=None, pathMap=None):
        """Standard path replacement in QGIS project XML.

        pathMap maps a *resolved* absolute source path to the absolute path it now lives at (used by
        the exporter for staged external data). relativizeUnder is a folder under which resulting
        paths are emitted relative to newQgisDir (the staging root when exporting), which is what
        makes the exported project portable. With both left as None the behaviour is identical to
        the rename / move / clone flows.
        """
        oldFolderNorm = os.path.normcase(os.path.normpath(oldFolder))
        newFolderNorm = os.path.normpath(newFolder)
        relativizeUnderNorm = os.path.normcase(os.path.normpath(relativizeUnder)) if relativizeUnder else None

        def emitPath(absPath, protocol, wasRelative):
            """Renders a resolved absolute path back into a datasource value.

            Exporting (relativizeUnder set): everything that ended up inside the staging tree is
            emitted relative to the .qgz, which is what makes the ZIP portable; anything that was
            left behind is emitted absolute, so the receiver's "Handle unavailable layers" dialog
            shows a path they can recognise. Otherwise (rename / move / clone): relative iff the
            original value was relative.
            """
            targetQgisDir = newQgisDir if newQgisDir else oldQgisDir
            if relativizeUnderNorm:
                probe = os.path.normcase(os.path.normpath(absPath))
                shouldRelativize = probe == relativizeUnderNorm or probe.startswith(relativizeUnderNorm + os.sep)
            else:
                shouldRelativize = wasRelative
            if shouldRelativize and targetQgisDir:
                with suppress(ValueError):
                    rel = os.path.relpath(absPath, targetQgisDir)
                    return protocol + rel.replace('\\', '/')
            return protocol + absPath.replace('\\', '/')

        def replacePathInValue(val):
            # XML entities (like &amp;) need to be unescaped for comparison
            # We return an unescaped string so the caller can handle the final XML escaping consistently.
            logical_val = xml.sax.saxutils.unescape(val)

            # If it's a connection string (XYZ, WMS, etc.), don't treat it as a local path
            if isRemoteDatasource(logical_val):
                return logical_val

            # QGIS paths in XML can also be URL-encoded and might start with file://
            val = urllib.parse.unquote(logical_val)
            protocol = ""
            if val.startswith('file:///'):
                protocol = 'file:///'
                val = val[8:]
            elif val.startswith('file://'):
                protocol = 'file://'
                val = val[7:]

            # Normalize to absolute. Comparisons use the normcased form; the value we emit keeps the
            # original capitalisation, so a path handed back to the user stays readable (and valid
            # if the project is ever opened on a case-sensitive filesystem).
            if os.path.isabs(val):
                absPath = os.path.normpath(val)
                wasRelative = False
            elif oldQgisDir:
                absPath = os.path.normpath(os.path.join(oldQgisDir, val))
                wasRelative = True
            else:
                return logical_val
            # normpath already unified the separators, so normcase cannot change the length and the
            # index arithmetic on absPath below stays valid.
            absPathCmp = os.path.normcase(absPath)

            # Explicitly remapped by the caller (the exporter, for staged external data).
            # Keyed on the *resolved* path, so a folder name containing '&' or '|' cannot fool it.
            if pathMap:
                cleanPath = absPath
                uriSuffix = ""
                if URI_SUFFIX_SEPARATOR in cleanPath:
                    index = cleanPath.find(URI_SUFFIX_SEPARATOR)
                    uriSuffix = cleanPath[index:]
                    cleanPath = cleanPath[:index]
                mapped = pathMap.get(os.path.normcase(os.path.realpath(cleanPath)))
                if mapped:
                    return emitPath(mapped + uriSuffix, protocol, wasRelative)

            # Check if this path is inside the old project folder
            if absPathCmp.startswith(oldFolderNorm):
                suffix = absPath[len(oldFolderNorm):]
                newAbsPath = newFolderNorm + suffix
                head, tail = os.path.split(newAbsPath)
                oldNamePrefix = oldName + '_'
                newNamePrefix = newName + '_'

                # Case-insensitive replacement for the filename part (common on Windows)
                if oldName.lower() != newName.lower():
                    # Check if the tail starts with oldNamePrefix (case insensitive)
                    if tail.lower().startswith(oldNamePrefix.lower()):
                        tail = newNamePrefix + tail[len(oldNamePrefix):]
                elif oldName != newName:
                    # Same name different case? Just replace
                    tail = tail.replace(oldNamePrefix, newNamePrefix)

                newAbsPath = os.path.join(head, tail)
                return emitPath(newAbsPath, protocol, wasRelative)

            # Outside the project folder and not remapped: it was not part of this operation.
            if wasRelative or relativizeUnderNorm:
                return emitPath(absPath, protocol, wasRelative)

            return logical_val

        # Replace path values in XML attributes (source="..." url="..." filename="...")
        # We re-escape the result since attributes need proper XML escaping
        content = RE_DATASOURCE_ATTR_DQ.sub(
            lambda m: m.group(1) + m.group(2) + m.group(3) + xml.sax.saxutils.escape(replacePathInValue(m.group(4))) + m.group(5),
            content)
        content = RE_DATASOURCE_ATTR_SQ.sub(
            lambda m: m.group(1) + m.group(2) + m.group(3) + xml.sax.saxutils.escape(replacePathInValue(m.group(4))) + m.group(5),
            content)

        # Replace path values in <datasource>...</datasource> element content
        content = RE_DATASOURCE_ELEMENT.sub(
            lambda m: m.group(1) + xml.sax.saxutils.escape(replacePathInValue(m.group(2))) + m.group(3),
            content)

        if oldName != newName:
            # We must handle both the raw name and its XML-escaped version
            # (e.g., if project name is "Red & Blue")
            oldNameEsc = xml.sax.saxutils.escape(oldName)
            newNameEsc = xml.sax.saxutils.escape(newName)

            # Global string replacements
            # We search for escaped versions because they are stored that way in the XML attributes and content
            content = content.replace(oldName + '_', newName + '_')
            if oldName != oldNameEsc:
                content = content.replace(oldNameEsc + '_', newNameEsc + '_')

            content = content.replace('value="qgisred_' + oldName + '"', 'value="qgisred_' + newName + '"')
            content = content.replace('value="qgisred_' + oldNameEsc + '"', 'value="qgisred_' + newNameEsc + '"')

            content = content.replace('name="' + oldName + '"', 'name="' + newName + '"')
            content = content.replace('name="' + oldNameEsc + '"', 'name="' + newNameEsc + '"')

        return content

    """File Helpers"""

    def stripAllExtensions(self, path):
        """Strips all extensions from a path (e.g. 'foo.qgz.bak' -> 'foo')."""
        while True:
            base, ext = os.path.splitext(path)
            if not ext:
                break
            path = base
        return path

    def getQGisProjectBase(self, folder, networkName):
        """Returns the stem path (no extensions) of the QGIS project file, or None if not set."""
        metadataFile = os.path.join(folder, networkName + "_Metadata.txt")
        if not os.path.exists(metadataFile):
            return None
        with suppress(Exception):
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)  # nosec B314 — local file written by plugin DLL, not user input
            for qgs in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if qgs.text and (".qgs" in qgs.text or ".qgz" in qgs.text):
                    qgisPath = qgs.text
                    if not os.path.isabs(qgisPath):
                        qgisPath = os.path.normpath(os.path.join(folder, qgisPath))
                    return self.stripAllExtensions(self._fs().getUniformedPath(qgisPath))
        return None

    def findQGisProjectFile(self, qgisBase):
        """Returns the full path to the .qgs/.qgz file for a given base path."""
        if not qgisBase:
            return None
        if os.path.exists(qgisBase + ".qgz"):
            return qgisBase + ".qgz"
        if os.path.exists(qgisBase + ".qgs"):
            return qgisBase + ".qgs"
        return None

    def _hasProjectFiles(self, folder, prefix):
        """Returns True if folder (recursively) contains any file starting with prefix + '_'."""
        with suppress(Exception):
            for f in os.listdir(folder):
                filepath = os.path.join(folder, f)
                if os.path.isfile(filepath) and f.startswith(prefix + "_"):
                    return True
                if os.path.isdir(filepath) and self._hasProjectFiles(filepath, prefix):
                    return True
        return False

    def processProjectFiles(self, folder, oldName, newName, targetDir, deleteSource=False, excludeDirs=None):
        """Copies/moves project files (oldName_*) recursively to targetDir, renaming any file that starts with oldName_."""
        if excludeDirs is None:
            excludeDirs = []
        folder = self._fs().getUniformedPath(folder)
        if not os.path.exists(targetDir):
            os.makedirs(targetDir, exist_ok=True)

        for f in os.listdir(folder):
            filepath = os.path.join(folder, f)
            if os.path.isfile(filepath) and f.startswith(oldName + "_"):
                with suppress(Exception):
                    destName = f.replace(oldName + "_", newName + "_", 1)
                    shutil.copy2(filepath, os.path.join(targetDir, destName))
                    if deleteSource:
                        os.remove(filepath)
            elif os.path.isdir(filepath):
                if f.lower() in [d.lower() for d in excludeDirs]:
                    continue
                # Skip subdirectories that are the target or contain the target (would cause infinite recursion)
                normalizedFilepath = self._fs().getUniformedPath(filepath)
                normalizedTarget = self._fs().getUniformedPath(targetDir)
                if normalizedTarget == normalizedFilepath or normalizedTarget.startswith(normalizedFilepath + '/'):
                    continue
                # Skip subdirectories that contain no project files (avoid creating empty target dirs)
                if not self._hasProjectFiles(filepath, oldName):
                    continue
                subTarget = os.path.join(targetDir, f)
                if self._fs().getUniformedPath(folder) != self._fs().getUniformedPath(targetDir):
                    os.makedirs(subTarget, exist_ok=True)
                self.processProjectFiles(filepath, oldName, newName, subTarget, deleteSource, excludeDirs)
                if deleteSource:
                    with suppress(Exception):
                        if not os.listdir(filepath):
                            os.rmdir(filepath)
        if deleteSource:
            with suppress(Exception):
                if self._fs().getUniformedPath(folder) != self._fs().getUniformedPath(targetDir) and not os.listdir(folder):
                    os.rmdir(folder)

    def processQGisProjectFiles(self, qgisBase, newName, targetDir, deleteSource=False):
        """Copies/moves QGIS project files (.qgz/.qgs and backups) to targetDir.
        Returns the new relative path of the .qgz/.qgs file."""
        parentDir = os.path.dirname(qgisBase)
        oldBaseName = os.path.basename(qgisBase)
        newQgisPath = None
        with suppress(Exception):
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self.stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(oldBaseName):]
                        newFilepath = os.path.join(targetDir, newName + extensions)
                        with suppress(Exception):
                            shutil.copy2(filepath, newFilepath)
                            if deleteSource:
                                os.remove(filepath)
                            if newQgisPath is None and (f.endswith(".qgs") or f.endswith(".qgz")):
                                newQgisPath = newFilepath
            if deleteSource:
                with suppress(Exception):
                    if self._fs().getUniformedPath(parentDir) != self._fs().getUniformedPath(targetDir) and not os.listdir(parentDir):
                        os.rmdir(parentDir)
        return newQgisPath

    def updateQGisProjectContent(self, qgisPath, oldName, newName, oldFolder, newFolder,
                                 oldQgisDir=None, newQgisDir=None,
                                 relativizeUnder=None, pathMap=None, raiseErrors=False):
        """Updates internal project references. See _applyQGisReplacements for the parameters.

        Failures are swallowed by default to preserve the behaviour the rename / move / clone flows
        rely on; the exporter passes raiseErrors=True because a silently broken .qgz inside a ZIP is
        the worst possible outcome.
        """
        def run():
            if qgisPath.endswith('.qgz'):
                files = {}
                with ZipFile(qgisPath, 'r') as zin:
                    for name in zin.namelist():
                        files[name] = zin.read(name)
                for name in list(files.keys()):
                    if name.endswith('.qgs'):
                        xml = files[name].decode('utf-8')
                        xml = self._applyQGisReplacements(xml, oldName, newName, oldFolder, newFolder,
                                                          oldQgisDir, newQgisDir, relativizeUnder, pathMap)
                        files[name] = xml.encode('utf-8')
                with ZipFile(qgisPath, 'w', ZIP_DEFLATED) as zout:
                    for name, data in files.items():
                        zout.writestr(name, data)
            elif qgisPath.endswith('.qgs'):
                with open(qgisPath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = self._applyQGisReplacements(content, oldName, newName, oldFolder, newFolder,
                                                      oldQgisDir, newQgisDir, relativizeUnder, pathMap)
                with open(qgisPath, 'w', encoding='utf-8') as f:
                    f.write(content)

        if raiseErrors:
            run()
        else:
            with suppress(Exception):
                run()

    """Methods"""

    def updateMetadataQGisProject(self, projectPath, networkName, newQgisPath):
        """Updates the <QGisProject> node in the metadata file."""
        metadataFile = os.path.join(projectPath, networkName + "_Metadata.txt")
        if not os.path.exists(metadataFile):
            return
        with suppress(Exception):
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)  # nosec B314 — local file written by plugin DLL, not user input
            updated = False
            for node in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if node.text and (".qgs" in node.text or ".qgz" in node.text):
                    # Forward slashes: an exported project may be opened on another platform, and
                    # Windows accepts '/' too (getQGisProjectBase normpath's it on the way back in).
                    node.text = os.path.relpath(newQgisPath, projectPath).replace(os.sep, "/")
                    updated = True
            if updated:
                with open(metadataFile, "w", encoding="latin-1") as mf:
                    mf.write(ElementTree.tostring(xmlRoot, encoding="unicode"))

    def openProjectInQgis(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, "r", encoding="latin-1") as contentFile:
                data = contentFile.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)  # nosec B314 — local project file written by plugin DLL, not user input
            # Get data from nodes
            for qgs in root.findall("./ThirdParty/QGISRed/QGisProject"):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    qgisPath = finfo.filePath()
                    if not os.path.isfile(qgisPath):  # Create absolute path
                        qgisPath = os.path.normpath(os.path.join(self.ProjectDirectory, qgisPath))

                    if os.path.exists(qgisPath):
                        QgsProject.instance().read(qgisPath)
                        self._renameGroupsToLocale()
                        return True
                    else:
                        request = QMessageBox.question(
                            self.iface.mainWindow(),
                            self.tr("QGISRed Project"),
                            self.tr("We cannot find the QGIS project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group."),
                            QMessageBox.StandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No),
                        )
                        if request == QMessageBox.StandardButton.Yes:
                            qfd = QFileDialog()
                            filter = "qgz(*.qgz)"
                            f = QFileDialog.getOpenFileName(qfd, "Select QGis file", "", filter)
                            qgisPath = f[0]
                            if not qgisPath == "":
                                QgsProject.instance().read(qgisPath)
                                self._renameGroupsToLocale()
                                return True
                        else:
                            layers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
                            self._openGroupByName("Inputs", layers)
                    return False
            for groups_node in root.findall("./ThirdParty/QGISRed/Groups"):
                self._openGroupsNode(groups_node, "")
                if groups_node.find("Results") is not None:
                    self._layers().getOrCreateNestedGroup([self.NetworkName, "Results"])
            if self.iface:
                bridge = self.iface.layerTreeCanvasBridge()
                bridge.setCanvasLayers()
                self.iface.mapCanvas().refresh()
            return False

        else:  # old file
            gqpFilename = os.path.join(self.ProjectDirectory, self.NetworkName + ".gqp")
            if os.path.exists(gqpFilename):
                f = open(gqpFilename, "r")
                lines = f.readlines()
                qgsFile = lines[2]
                if ".qgs" in qgsFile or ".qgz" in qgsFile:
                    finfo = QFileInfo(qgsFile)
                    QgsProject.instance().read(finfo.filePath())
                    self._renameGroupsToLocale()
                    return True
                else:
                    styling = self._styling()
                    group = None
                    for i in range(2, len(lines)):
                        if "[" in lines[i]:
                            groupName = str(lines[i].strip("[").strip("\r\n").strip("]")).replace(self.NetworkName + " ", "")
                            root = QgsProject.instance().layerTreeRoot()
                            netGroup = root.insertGroup(0, self.NetworkName)
                            group = netGroup.insertGroup(0, groupName)
                        else:
                            layerPath = lines[i].strip("\r\n")
                            if not os.path.exists(layerPath):
                                continue
                            vlayer = None
                            layerName = os.path.splitext(os.path.basename(layerPath))[0].replace(self.NetworkName + "_", "")
                            if group is None:
                                vlayer = self.iface.addVectorLayer(layerPath, layerName, "ogr")
                            else:
                                vlayer = QgsVectorLayer(layerPath, layerName, "ogr")
                                QgsProject.instance().addMapLayer(vlayer, False)
                                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
                            if vlayer is not None:
                                if ".shp" in layerPath:
                                    names = (os.path.splitext(os.path.basename(layerPath))[0]).split("_")
                                    nameLayer = names[len(names) - 1]
                                    styling.setStyle(vlayer, nameLayer.lower())
                    return False
            else:
                QGISRedUIUtils.showGlobalMessage(self.iface, "File not found", level=1, duration=5)
                return False

    """Zip"""

    def exportProjectToZip(self, zipPath, includeExternal=True, includeGroups=None):
        """Comprehensive export of the project to a ZIP file. Returns (ok, reason, manifest).

        Thin delegator; the packaging logic lives in qgisred_project_export so it can be unit
        tested without QGIS. Imported lazily because that module imports this one.
        """
        from .qgisred_project_export import QGISRedProjectPackage
        package = QGISRedProjectPackage(self.ProjectDirectory, self.NetworkName, self.iface)
        return package.exportToZip(zipPath, includeExternal=includeExternal, includeGroups=includeGroups)

    def unzipFile(self, zipfile, directory, members=None):
        """Extracts a ZIP into directory, refusing any member that would escape it.

        extractall() is not used because a crafted archive can write outside the destination
        ('zip slip'): entries may hold '..', absolute paths or symlinks. members, when given, is the
        set of entry names to extract — the importer uses it to leave complementary data out.
        """
        from .qgisred_project_export import safeJoin  # lazy: that module imports this one

        destRoot = os.path.realpath(directory)
        os.makedirs(destRoot, exist_ok=True)
        with ZipFile(zipfile, "r") as zipRef:
            for info in zipRef.infolist():
                name = info.filename
                if members is not None and name not in members:
                    continue
                # Symlink entries would let the archive point anywhere on disk
                if (info.external_attr >> 16) & 0o170000 == 0o120000:
                    continue
                target = safeJoin(destRoot, name)
                if info.is_dir():
                    os.makedirs(target, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zipRef.open(info) as source, open(target, "wb") as dest:
                    shutil.copyfileobj(source, dest)

    def renameFilesInZip(self, zipPath, oldPrefix, newPrefix):
        """Renames files inside a ZIP archive that start with oldPrefix to start with newPrefix."""
        if not os.path.exists(zipPath):
            return

        temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
        os.close(temp_fd)

        try:
            with ZipFile(zipPath, 'r') as zin:
                with ZipFile(temp_path, 'w', ZIP_DEFLATED) as zout:
                    for item in zin.infolist():
                        filename = item.filename
                        # Zip entries may have leading slashes depending on how they were created.
                        # Also, ensure we compare using standard slashes.
                        clean_filename = filename.lstrip('/\\')
                        if clean_filename.startswith(oldPrefix):
                            idx = filename.find(oldPrefix)
                            new_filename = filename[:idx] + newPrefix + filename[idx + len(oldPrefix):]
                        else:
                            new_filename = filename
                        zout.writestr(new_filename, zin.read(item.filename))

            # Replace original with renamed version
            os.remove(zipPath)
            shutil.move(temp_path, zipPath)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    """QLR Operations"""

    def getProjectGuid(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            with suppress(Exception):
                with open(metadataFile, "r", encoding="latin-1") as f:
                    data = f.read()
                root = ElementTree.fromstring(data)  # nosec B314 — local project file written by plugin DLL, not user input
                guidNode = root.find("Guid")
                if guidNode is not None and guidNode.text:
                    return guidNode.text
        return self.NetworkName

    def getQLRFolder(self):
        qlrFolder = os.path.join(self._fs().getQGISRedFolder(), "qlr")
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)
        return qlrFolder

    def saveProjectAsQLR(self):
        qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())
        if not os.path.exists(qlrFolder):
            os.makedirs(qlrFolder)

        savedCount = 0
        layers = self._layers().getLayers()
        root = QgsProject.instance().layerTreeRoot()
        layerMeta = {}

        for layer in layers:
            identifier = layer.customProperty("qgisred_identifier")
            if not identifier:
                continue

            layerNode = root.findLayer(layer.id())
            if not layerNode:
                continue

            parent = layerNode.parent()
            groupPath = []
            current = parent
            while current and current != root:
                groupPath.insert(0, current.name())
                current = current.parent()

            position = 0
            if parent:
                for i, child in enumerate(parent.children()):
                    if child == layerNode:
                        position = i
                        break

            layerMeta[identifier] = {
                "group_path": groupPath,
                "position": position,
                "name": layer.name()
            }

            qlrFilename = f"{identifier}.qlr"
            qlrPath = os.path.join(qlrFolder, qlrFilename)

            with suppress(Exception):
                success = QgsLayerDefinition.exportLayerDefinition(qlrPath, [layerNode])
                if success:
                    savedCount += 1

        if savedCount > 0:
            metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
            with open(metadataPath, 'w') as f:
                json.dump(layerMeta, f, indent=2)

        return (savedCount > 0, qlrFolder)

    def loadProjectFromQLR(self, qlrFolder=None):
        if qlrFolder is None:
            qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())

        if not os.path.exists(qlrFolder):
            return False

        qlrFiles = [f for f in os.listdir(qlrFolder) if f.endswith('.qlr')]
        if not qlrFiles:
            return False

        layerMeta = {}
        metadataPath = os.path.join(qlrFolder, "layer_metadata.json")
        if os.path.exists(metadataPath):
            with open(metadataPath, 'r') as f:
                layerMeta = json.load(f)

        self._layers().removePluginLayers()

        loadedLayers = []
        root = QgsProject.instance().layerTreeRoot()

        for qlrFile in qlrFiles:
            qlrPath = os.path.join(qlrFolder, qlrFile)
            identifier = qlrFile.replace('.qlr', '')

            with suppress(Exception):
                success = QgsLayerDefinition().loadLayerDefinition(
                    qlrPath,
                    QgsProject.instance(),
                    root
                )
                if success:
                    for layer in self._layers().getLayers():
                        if layer.customProperty("qgisred_identifier") == identifier:
                            loadedLayers.append((layer, identifier))
                            break

        for layer, identifier in loadedLayers:
            metadata = layerMeta.get(identifier, {})
            groupPath = metadata.get("group_path", [])
            position = metadata.get("position", 0)

            targetGroup = root
            for groupName in groupPath:
                existingGroup = targetGroup.findGroup(groupName)
                if existingGroup:
                    targetGroup = existingGroup
                else:
                    targetGroup = targetGroup.insertGroup(0, groupName)

            layerNode = root.findLayer(layer.id())
            if layerNode and targetGroup != root:
                clonedNode = layerNode.clone()
                numChildren = len(targetGroup.children())
                insertPos = min(position, numChildren)
                targetGroup.insertChildNode(insertPos, clonedNode)

                if layerNode.parent():
                    layerNode.parent().removeChildNode(layerNode)

        return len(loadedLayers) > 0

    def deleteProjectQLR(self, qlrFolder=None):
        if qlrFolder is None:
            qlrFolder = os.path.join(self.getQLRFolder(), self.getProjectGuid())

        if not os.path.exists(qlrFolder):
            return False

        deletedAny = False

        for filename in os.listdir(qlrFolder):
            if filename.endswith('.qlr') or filename == 'layer_metadata.json':
                with suppress(Exception):
                    os.remove(os.path.join(qlrFolder, filename))
                    deletedAny = True

        with suppress(Exception):
            if not os.listdir(qlrFolder):
                os.rmdir(qlrFolder)

        return deletedAny

    def addProjectToGplFile(self, gplFile, networkName='', projectDirectory='', rawEntryLine=None):
        projectDirectory = self._fs().getUniformedPath(projectDirectory)
        newEntry = rawEntryLine or f"{networkName};{projectDirectory}"
        newEntry = newEntry.strip()

        existingEntries = []
        if os.path.exists(gplFile):
            with open(gplFile, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and line != newEntry:
                        existingEntries.append(line)

        with open(gplFile, "w") as f:
            f.write(newEntry + "\n")
            for entry in existingEntries:
                f.write(entry + "\n")
