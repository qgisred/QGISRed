# -*- coding: utf-8 -*-
import os
import datetime
import json
import shutil
import tempfile
import re
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree  # nosec B314 — parses local project files only, no external input
import urllib.parse
import xml.sax.saxutils

from qgis.PyQt.QtCore import QCoreApplication, QFileInfo
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsVectorLayer,
    QgsLayerDefinition
)
from .qgisred_ui_utils import QGISRedUIUtils


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

    _GROUP_SUBDIR = {
        "Inputs":                   "",
        "Issues":                   "Issues",
        "Results":                  "Results",
        "Queries/Connectivity":     "",
        "Queries/HydraulicSectors": "Queries",
        "Queries/DemandSectors":    "Queries",
        "Queries/IsolatedSegments": "Queries",
    }

    _GROUP_TREE_PATH = {
        "Inputs":                   ["Inputs"],
        "Issues":                   ["Issues"],
        "Results":                  ["Results"],
        "Queries/Connectivity":     ["Queries", "Connectivity"],
        "Queries/HydraulicSectors": ["Queries", "Hydraulic Sectors"],
        "Queries/DemandSectors":    ["Queries", "Demand Sectors"],
        "Queries/IsolatedSegments": ["Queries", "Isolated Segments"],
    }

    _GROUP_OPEN_FLAGS = {
        "Inputs":                   {},
        "Issues":                   {"issues": True},
        "Results":                  {"results": True},
        "Queries/Connectivity":     {},
        "Queries/HydraulicSectors": {"sectors": True},
        "Queries/DemandSectors":    {"sectors": True},
        "Queries/IsolatedSegments": {},
    }

    def _openGroupByName(self, groupName, layerNames):
        from .qgisred_layer_utils import QGISRedLayerUtils
        from .qgisred_styling_utils import QGISRedStylingUtils

        # Special case: Tree subgroups — "Queries/Tree_*"
        if re.match(r'^Queries/Tree_', groupName):
            # Layer names are sanitized ASCII (e.g. "Nodes_Tree_J5_Union").
            # Recover the actual tree name (e.g. "J5-Unión") by scanning disk.
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
            queries_dir = os.path.join(self.ProjectDirectory, "Queries")
            tree_name = None
            pattern = os.path.join(queries_dir, self.NetworkName + "_Nodes_Tree_*.shp")
            for path in _glob.glob(pattern):
                basename = os.path.splitext(os.path.basename(path))[0]
                prefix = self.NetworkName + "_Nodes_Tree_"
                if basename.startswith(prefix):
                    candidate = basename[len(prefix):]
                    norm = _ud.normalize("NFKD", candidate).encode("ascii", "ignore").decode("ascii")
                    norm = norm.replace("-", "_")
                    if norm == sanitized_tree:
                        tree_name = candidate
                        break
            if tree_name is None:
                return
            utils = QGISRedLayerUtils(queries_dir, self.NetworkName, self.iface)
            group = utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Tree: " + tree_name])
            for name in reversed(layerNames):
                is_link = name.lower().startswith("links")
                utils.openTreeLayer(group, "Links" if is_link else "Nodes", tree_name, link=is_link)
            return

        # Try full path as key (e.g. "Queries/HydraulicSectors", or legacy "HydraulicSectors")
        tree_path = self._GROUP_TREE_PATH.get(groupName)
        subdir = self._GROUP_SUBDIR.get(groupName, "")
        flags = self._GROUP_OPEN_FLAGS.get(groupName, {})
        full_tree_path = tree_path

        if tree_path is None:
            # Dynamic paths — e.g. "Results/Base": use top-level key + sub-parts
            parts = groupName.split("/")
            top = parts[0]
            sub_parts = parts[1:]
            tree_path = self._GROUP_TREE_PATH.get(top)
            if tree_path is None:
                return  # unknown group — skip silently
            subdir = self._GROUP_SUBDIR.get(top, "")
            flags = self._GROUP_OPEN_FLAGS.get(top, {})
            full_tree_path = tree_path + sub_parts

        top = groupName.split("/")[0]
        layersDir = os.path.join(self.ProjectDirectory, subdir) if subdir else self.ProjectDirectory
        utils = QGISRedLayerUtils(layersDir, self.NetworkName, self.iface)
        group = utils.getOrCreateNestedGroup([self.NetworkName] + full_tree_path)

        if top == "Results":
            styling = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            for name in reversed(layerNames):
                # "Base_Node_Pressure" → file_name="Base_Node", layer_type="Node", variable="Pressure"
                m = re.match(r'^(.+_(Node|Link))_(.+)$', name, re.IGNORECASE)
                if m:
                    file_name, layer_type, variable = m.group(1), m.group(2), m.group(3)
                else:
                    file_name, layer_type, variable = name, None, None
                utils.openLayer(group, file_name, **flags)
                if not variable or not layer_type:
                    continue
                layer_path = utils._fs().generatePath(layersDir, self.NetworkName + "_" + file_name + ".shp")
                opened = utils._findLayerByPath(layer_path)
                if not opened:
                    continue
                scenario = file_name.rsplit("_", 1)[0]  # "Base_Node" → "Base"
                QgsProject.instance().writeEntry("QGISRed", f"results_{scenario}_{layer_type}", variable)
                styling.setResultStyle(opened, layer_type + "_" + variable)
                template = QCoreApplication.translate("QGISRedResultsDock", layer_type + " %1")
                translated_var = QCoreApplication.translate("QGISRedResultsDock", variable)
                opened.setName(template.replace("%1", translated_var))
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

    def _applyQGisReplacements(self, content, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None, collectExternal=False):
        """Standard path replacement in QGIS project XML. 
        If collectExternal is True, it will also copy external layers to newFolder/ExternalLayers."""
        oldFolderNorm = os.path.normcase(os.path.normpath(oldFolder))
        newFolderNorm = os.path.normpath(newFolder)
        externalLayersDir = os.path.join(newFolderNorm, "ExternalLayers")
        
        def replacePathInValue(val):
            # XML entities (like &amp;) need to be unescaped for comparison
            # We return an unescaped string so the caller can handle the final XML escaping consistently.
            logical_val = xml.sax.saxutils.unescape(val)
            
            # If it's a connection string (XYZ, WMS, etc.), don't treat it as a local path
            # Detection: url=, crs=, type= (common in datasource), service=, request=, OR starts with http
            if any(marker in logical_val.lower() for marker in ["url=", "crs=", "type=", "service=", "request="]) or logical_val.lower().startswith(("http://", "https://")):
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
            
            # Normalize to absolute for comparison
            if os.path.isabs(val):
                absPath = os.path.normcase(os.path.normpath(val))
                wasRelative = False
            elif oldQgisDir:
                absPath = os.path.normcase(os.path.normpath(os.path.join(oldQgisDir, val)))
                wasRelative = True
            else:
                return logical_val

            # Check if this path is inside the old project folder
            if absPath.startswith(oldFolderNorm):
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
                
                # Use relative path if the original was relative OR if we are exporting (collectExternal=True)
                if wasRelative or collectExternal:
                    rel = os.path.relpath(newAbsPath, newQgisDir if newQgisDir else oldQgisDir)
                    return protocol + rel.replace('\\', '/')
                else:
                    return protocol + newAbsPath.replace('\\', '/')
            
            # If it's external and we want to collect it:
            if collectExternal:
                # Check if it's a local file
                cleanPath = absPath
                if '|' in cleanPath:
                    cleanPath = cleanPath.split('|')[0]
                
                if os.path.isfile(cleanPath):
                    os.makedirs(externalLayersDir, exist_ok=True)
                    basePath = self.stripAllExtensions(cleanPath)
                    parent = os.path.dirname(cleanPath)
                    try:
                        for f in os.listdir(parent):
                            current_file_path = os.path.join(parent, f)
                            if os.path.normcase(self.stripAllExtensions(current_file_path)) == os.path.normcase(basePath):
                                shutil.copy2(current_file_path, os.path.join(externalLayersDir, f))
                    except Exception:
                        pass
                    
                    suffix = ""
                    if '|' in absPath:
                        suffix = absPath[absPath.find('|'):]
                        
                    newExternalPath = os.path.join(externalLayersDir, os.path.basename(cleanPath)) + suffix
                    
                    # When collecting external layers (export), the path MUST be relative to the project
                    # to ensure the ZIP is portable.
                    rel = os.path.relpath(newExternalPath, newQgisDir if newQgisDir else oldQgisDir)
                    return rel.replace('\\', '/')

            # If it's external and we don't want to collect it, we might still 
            # need to update the relative path if the original was relative.
            if not collectExternal and wasRelative:
                targetQgisDir = newQgisDir if newQgisDir else oldQgisDir
                try:
                    rel = os.path.relpath(absPath, targetQgisDir)
                    return protocol + rel.replace('\\', '/')
                except ValueError:
                    # Occurs if on different drives on Windows
                    pass

            return logical_val

        # Replace path values in XML attributes (source="..." url="..." filename="...")
        # We re-escape the result since attributes need proper XML escaping
        content = re.sub(r'(source|url|filename)(=)(")([^"]+)(")',
                         lambda m: m.group(1) + m.group(2) + m.group(3) + xml.sax.saxutils.escape(replacePathInValue(m.group(4))) + m.group(5),
                         content)
        content = re.sub(r"(source|url|filename)(=)(')([^']+)(')",
                         lambda m: m.group(1) + m.group(2) + m.group(3) + xml.sax.saxutils.escape(replacePathInValue(m.group(4))) + m.group(5),
                         content)

        # Replace path values in <datasource>...</datasource> element content
        content = re.sub(r'(<datasource>)([^<]+)(</datasource>)',
                         lambda m: m.group(1) + xml.sax.saxutils.escape(replacePathInValue(m.group(2))) + m.group(3),
                         content)

        if oldName != newName:
            # We must handle both the raw name and its XML-escaped version
            # (e.g., if project name is "Red & Blue")
            oldNameEsc = xml.sax.saxutils.escape(oldName)
            newNameEsc = xml.sax.saxutils.escape(newName)

            # Global string replacements
            # We search for escaped versions because they are stored that way in the XML attributes and content
            content = content.replace(oldName + '_', newName + '_' )
            if oldName != oldNameEsc:
                content = content.replace(oldNameEsc + '_', newNameEsc + '_' )
            
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
        try:
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)
            for qgs in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if qgs.text and (".qgs" in qgs.text or ".qgz" in qgs.text):
                    qgisPath = qgs.text
                    if not os.path.isabs(qgisPath):
                        qgisPath = os.path.normpath(os.path.join(folder, qgisPath))
                    return self.stripAllExtensions(self._fs().getUniformedPath(qgisPath))
        except Exception:
            pass
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
        try:
            for f in os.listdir(folder):
                filepath = os.path.join(folder, f)
                if os.path.isfile(filepath) and f.startswith(prefix + "_"):
                    return True
                if os.path.isdir(filepath) and self._hasProjectFiles(filepath, prefix):
                    return True
        except Exception:
            pass
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
                try:
                    destName = f.replace(oldName + "_", newName + "_", 1)
                    shutil.copy2(filepath, os.path.join(targetDir, destName))
                    if deleteSource:
                        os.remove(filepath)
                except Exception:
                    pass
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
                    try:
                        if not os.listdir(filepath):
                            os.rmdir(filepath)
                    except Exception:
                        pass
        if deleteSource:
            try:
                if self._fs().getUniformedPath(folder) != self._fs().getUniformedPath(targetDir) and not os.listdir(folder):
                    os.rmdir(folder)
            except Exception:
                pass

    def processQGisProjectFiles(self, qgisBase, newName, targetDir, deleteSource=False):
        """Copies/moves QGIS project files (.qgz/.qgs and backups) to targetDir.
        Returns the new relative path of the .qgz/.qgs file."""
        parentDir = os.path.dirname(qgisBase)
        oldBaseName = os.path.basename(qgisBase)
        newQgisPath = None
        try:
            for f in os.listdir(parentDir):
                filepath = os.path.join(parentDir, f)
                if os.path.isfile(filepath):
                    stripped = self.stripAllExtensions(filepath)
                    if os.path.normcase(stripped) == os.path.normcase(qgisBase):
                        extensions = f[len(oldBaseName):]
                        newFilepath = os.path.join(targetDir, newName + extensions)
                        try:
                            shutil.copy2(filepath, newFilepath)
                            if deleteSource:
                                os.remove(filepath)
                            if newQgisPath is None and (f.endswith(".qgs") or f.endswith(".qgz")):
                                newQgisPath = newFilepath
                        except Exception:
                            pass
            if deleteSource:
                try:
                    if self._fs().getUniformedPath(parentDir) != self._fs().getUniformedPath(targetDir) and not os.listdir(parentDir):
                        os.rmdir(parentDir)
                except Exception:
                    pass
        except Exception:
            pass
        return newQgisPath

    def updateQGisProjectContent(self, qgisPath, oldName, newName, oldFolder, newFolder, oldQgisDir=None, newQgisDir=None, collectExternal=False):
        """Updates internal project references."""
        try:
            if qgisPath.endswith('.qgz'):
                files = {}
                with ZipFile(qgisPath, 'r') as zin:
                    for name in zin.namelist():
                        files[name] = zin.read(name)
                for name in list(files.keys()):
                    if name.endswith('.qgs'):
                        xml = files[name].decode('utf-8')
                        xml = self._applyQGisReplacements(xml, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir, collectExternal)
                        files[name] = xml.encode('utf-8')
                with ZipFile(qgisPath, 'w', ZIP_DEFLATED) as zout:
                    for name, data in files.items():
                        zout.writestr(name, data)
            elif qgisPath.endswith('.qgs'):
                with open(qgisPath, 'r', encoding='utf-8') as f:
                    content = f.read()
                content = self._applyQGisReplacements(content, oldName, newName, oldFolder, newFolder, oldQgisDir, newQgisDir, collectExternal)
                with open(qgisPath, 'w', encoding='utf-8') as f:
                    f.write(content)
        except Exception:
            pass

    """Methods"""
    def updateMetadataQGisProject(self, projectPath, networkName, newQgisPath):
        """Updates the <QGisProject> node in the metadata file."""
        metadataFile = os.path.join(projectPath, networkName + "_Metadata.txt")
        if not os.path.exists(metadataFile):
            return
        try:
            with open(metadataFile, "r", encoding="latin-1") as mf:
                data = mf.read()
            xmlRoot = ElementTree.fromstring(data)
            updated = False
            for node in xmlRoot.findall("./ThirdParty/QGISRed/QGisProject"):
                if node.text and (".qgs" in node.text or ".qgz" in node.text):
                    node.text = os.path.relpath(newQgisPath, projectPath)
                    updated = True
            if updated:
                with open(metadataFile, "w", encoding="latin-1") as mf:
                    mf.write(ElementTree.tostring(xmlRoot, encoding="unicode"))
        except Exception:
            pass

    def openProjectInQgis(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            # Read data as text plain to include the encoding
            data = ""
            with open(metadataFile, "r", encoding="latin-1") as contentFile:
                data = contentFile.read()
            # Parse data as XML
            root = ElementTree.fromstring(data)
            # Get data from nodes
            for qgs in root.findall("./ThirdParty/QGISRed/QGisProject"):
                if ".qgs" in qgs.text or ".qgz" in qgs.text:
                    finfo = QFileInfo(qgs.text)
                    qgisPath = finfo.filePath()
                    if not os.path.isfile(qgisPath):  # Create absolute path
                        currentDirectory = os.getcwd()
                        os.chdir(self.ProjectDirectory)
                        qgisPath = os.path.abspath(qgisPath)
                        os.chdir(currentDirectory)

                    if os.path.exists(qgisPath):
                        QgsProject.instance().read(qgisPath)
                        return True
                    else:
                        request = QMessageBox.question(
                            self.iface.mainWindow(),
                            self.tr("QGISRed Project"),
                            self.tr("We cannot find the QGIS project file. Do you want to find this file manually? If not, we will open only the layers from the Inputs group."),
                            QMessageBox.StandardButtons(QMessageBox.Yes | QMessageBox.No),
                        )
                        if request == QMessageBox.Yes:
                            qfd = QFileDialog()
                            filter = "qgz(*.qgz)"
                            f = QFileDialog.getOpenFileName(qfd, "Select QGis file", "", filter)
                            qgisPath = f[0]
                            if not qgisPath == "":
                                QgsProject.instance().read(qgisPath)
                                return True
                        else:
                            layers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
                            self._openGroupByName("Inputs", layers)
                    return False
            for groups_node in root.findall("./ThirdParty/QGISRed/Groups"):
                self._openGroupsNode(groups_node, "")
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
    def saveFilesInZip(self, zipPath):
        fs = self._fs()
        filePaths = []
        for f in os.listdir(self.ProjectDirectory):
            filepath = os.path.join(self.ProjectDirectory, f)
            if os.path.isfile(filepath):
                filePaths.append(fs.getUniformedPath(filepath))

        with ZipFile(zipPath, "w", ZIP_DEFLATED) as zipFile:
            for file in filePaths:
                if self._fs().getUniformedPath(self.ProjectDirectory) + os.sep + self.NetworkName + "_" in file:
                    relPath = os.path.relpath(file, self.ProjectDirectory)
                    zipFile.write(file, relPath)

    def exportProjectToZip(self, zipPath):
        """Comprehensive export of the project to a ZIP file."""
        with tempfile.TemporaryDirectory() as tempDir:
            # 1. Copy project files (no rename, no delete)
            self.processProjectFiles(self.ProjectDirectory, self.NetworkName, self.NetworkName, tempDir, deleteSource=False)
            
            # 2. Handle QGIS project
            qgisBase = self.getQGisProjectBase(self.ProjectDirectory, self.NetworkName)
            if qgisBase:
                oldQgisDir = os.path.dirname(qgisBase)
                relQgisDir = os.path.relpath(oldQgisDir, self.ProjectDirectory)
                targetQgisDir = os.path.normpath(os.path.join(tempDir, relQgisDir))
                os.makedirs(targetQgisDir, exist_ok=True)
                
                newQgisPath = self.processQGisProjectFiles(qgisBase, self.NetworkName, targetQgisDir, deleteSource=False)
                if newQgisPath:
                    self.updateQGisProjectContent(
                        newQgisPath, self.NetworkName, self.NetworkName,
                        self.ProjectDirectory, tempDir,
                        oldQgisDir, targetQgisDir,
                        collectExternal=True
                    )
                    self.updateMetadataQGisProject(tempDir, self.NetworkName, newQgisPath)
            
            # 3. ZIP everything in tempDir
            zipDir = os.path.dirname(zipPath)
            if not os.path.exists(zipDir):
                os.makedirs(zipDir, exist_ok=True)
                
            with ZipFile(zipPath, "w", ZIP_DEFLATED) as zout:
                for root, dirs, files in os.walk(tempDir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, tempDir)
                        zout.write(full_path, rel_path)

    def unzipFile(self, zipfile, directory):
        with ZipFile(zipfile, "r") as zipRef:
            zipRef.extractall(directory)

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

    def saveBackup(self):
        dirpath = os.path.join(self.ProjectDirectory, "backups")
        if not os.path.exists(dirpath):
            try:
                os.mkdir(dirpath)
            except Exception:
                pass

        timeString = datetime.datetime.now().timestamp()
        zipPath = os.path.join(dirpath, self.NetworkName + "_" + str(timeString) + ".zip")

        self.saveFilesInZip(zipPath)
        return zipPath

    """QLR Operations"""
    def getProjectGuid(self):
        metadataFile = os.path.join(self.ProjectDirectory, self.NetworkName + "_Metadata.txt")
        if os.path.exists(metadataFile):
            try:
                with open(metadataFile, "r", encoding="latin-1") as f:
                    data = f.read()
                root = ElementTree.fromstring(data)
                guidNode = root.find("Guid")
                if guidNode is not None and guidNode.text:
                    return guidNode.text
            except Exception:
                pass
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

            try:
                success = QgsLayerDefinition.exportLayerDefinition(qlrPath, [layerNode])
                if success:
                    savedCount += 1
            except Exception:
                continue

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

            try:
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
            except Exception:
                continue

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
                try:
                    os.remove(os.path.join(qlrFolder, filename))
                    deletedAny = True
                except Exception:
                    pass

        try:
            if not os.listdir(qlrFolder):
                os.rmdir(qlrFolder)
        except Exception:
            pass

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
