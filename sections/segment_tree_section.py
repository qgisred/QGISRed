# -*- coding: utf-8 -*-
"""Isolated segments and tree analysis section for QGISRed."""

import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool


class SegmentTreeSection:
    """Isolated segment analysis and tree/isolation path analysis."""

    def runIsolatedSegments(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        resMessage = "Select"
        tool = "pointIsolatedSegment"
        if point == True or point == False:
            point = ""
            self.gisredDll = None
        if not point == "":
            point = self.transformPoint(point)
            point = str(point.x()) + ":" + str(point.y())

            # Process
            if self.gisredDll is None:
                self.gisredDll = GISRed.CreateInstance()
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.IsolatedSegments(self.gisredDll, self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
            QApplication.restoreOverrideCursor()

        if resMessage == "False" or resMessage == "Cancelled":
            return
        elif resMessage == "Select":
            self.blockLayers(True)
            self.myMapTools[tool] = QGISRedSelectPointTool(self.isolatedSegmentsButton, self, self.runIsolatedSegments, 2)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
        elif "shps" in resMessage:
            if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
                self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
                self.isolatedSegmentsButton.setChecked(False)
            self.gisredDll = None
            self.blockLayers(False)
            # self.treeName = resMessage.split("^")[1]
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeIsolatedSegmentsLayers, self.runLoadIsolatedSegmentLayers)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runLoadIsolatedSegmentLayers(self):
        # Process
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        try:  # create directory if does not exist
            os.stat(queriesFolder)
        except Exception:
            os.mkdir(queriesFolder)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReplaceTemporalFiles(queriesFolder, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.openIsolatedSegmentsLayers()
        self.removingLayers = False

        # Message
        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def openIsolatedSegmentsLayers(self):
        # Open layers
        isoaltedSegmentsGroup = self.getIsolatedSegmentsGroup()
        queriesFolder = os.path.join(self.ProjectDirectory, "Queries")
        utils = QGISRedUtils(queriesFolder, self.NetworkName, self.iface)
        utils.openIsolatedSegmentsLayer(isoaltedSegmentsGroup, "Links")
        utils.openIsolatedSegmentsLayer(isoaltedSegmentsGroup, "Nodes")

    def getIsolatedSegmentsGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Isolated Segments"])

    def removeIsolatedSegmentsLayers(self):
        path = os.path.join(self.ProjectDirectory, "Queries")
        utils = QGISRedUtils(path, self.NetworkName, self.iface)
        utils.removeLayers(["IsolatedSegments_Links", "IsolatedSegments_Nodes"])

    def runTree(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = ""
        if point is not False:
            point = self.transformPoint(point)
            point1 = str(point.x()) + ":" + str(point.y())

        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])

        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Tree(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1)
        QApplication.restoreOverrideCursor()

        # Action
        if resMessage == "False" or resMessage == "Cancelled":
            return
        elif resMessage == "Select":
            self.selectPointToTree()
        elif "shps" in resMessage:
            self.treeName = resMessage.split("^")[1]
            self.removingLayers = True
            QGISRedUtils().runTask(self.removeTreeLayers, self.runTreeProcess)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def runTreeProcess(self):
        # Process
        treeFolder = os.path.join(self.ProjectDirectory, "Trees")
        try:  # create directory if does not exist
            os.stat(treeFolder)
        except Exception:
            os.mkdir(treeFolder)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.ReplaceTemporalFiles(treeFolder, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.openTreeLayers()
        self.removingLayers = False

        # Message
        if resMessage == "True":
            pass
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def selectPointToTree(self):
        tool = "treeNode"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(None, self, self.runTree, 1)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def openTreeLayers(self):
        # Open layers
        treeGroup = self.getTreeGroup()
        treeFolder = os.path.join(self.ProjectDirectory, "Trees")
        utils = QGISRedUtils(treeFolder, self.NetworkName, self.iface)
        utils.openTreeLayer(treeGroup, "Links", self.treeName, link=True)
        utils.openTreeLayer(treeGroup, "Nodes", self.treeName)
        group = self.getInputGroup()
        if group is not None:
            group.setItemVisibilityChecked(False)

    def getTreeGroup(self):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        return utils.getOrCreateNestedGroup([self.NetworkName, "Queries", "Tree: " + self.treeName])

    def removeTreeLayers(self):
        treePath = os.path.join(self.ProjectDirectory, "Trees")
        utils = QGISRedUtils(treePath, self.NetworkName, self.iface)
        utils.removeLayers(["Links_Tree_" + self.treeName, "Nodes_Tree_" + self.treeName])
        self.removeEmptyQuerySubGroup("Tree")
