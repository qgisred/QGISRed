# -*- coding: utf-8 -*-
"""Network editing section for QGISRed (pipes, tanks, reservoirs, valves, pumps, editing operations)."""

from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtCore import Qt

from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.map_tools.qgisred_createPipe import QGISRedCreatePipeTool
from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType
from ..tools.map_tools.qgisred_moveNodes import QGISRedMoveNodesTool
from ..tools.map_tools.qgisred_multilayerSelection import QGISRedMultiLayerSelection
from ..tools.map_tools.qgisred_editLinksGeometry import QGISRedEditLinksGeometryTool


class NetworkEditingSection:
    """
    Network element creation and editing operations.

    Note: This section references toolbar button attributes created by MenuSection:
      self.addPipeButton, self.addTankButton, self.addReservoirButton,
      self.insertValveButton, self.insertPumpButton, self.selectElementsButton,
      self.moveElementsButton, self.moveVertexsButton, self.reverseLinkButton,
      self.splitPipeButton, self.mergeSplitJunctionButton, self.createReverseTconButton,
      self.createReverseCrossButton, self.moveValvePumpButton, self.changeStatusButton,
      self.removeElementsButton, self.editElementButton
    """

    def runPaintPipe(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.addPipeButton.setChecked(False)
            return

        tool = "createPipe"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.addPipeButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedCreatePipeTool(
                self.addPipeButton, self.iface, self.ProjectDirectory, self.NetworkName, self.runCreatePipe
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreatePipe(self, points):
        pipePoints = ""
        for p in points:
            p = self.transformPoint(p)
            pipePoints = pipePoints + str(p.x()) + ":" + str(p.y()) + ";"
        # Process:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.AddPipe(self.ProjectDirectory, self.NetworkName, self.tempFolder, pipePoints)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "Pipe added")

    def runSelectTankPoint(self):
        tool = "pointTank"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addTankButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addTankButton, self, self.runAddTank, SelectPointType.Point, cursor=":/images/iconAddTank.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddTank(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.AddTank(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectReservoirPoint(self):
        tool = "pointReservoir"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.addReservoirButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.addReservoirButton, self, self.runAddReservoir, SelectPointType.Point, cursor=":/images/iconAddReservoir.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runAddReservoir(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.AddReservoir(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectValvePoint(self):
        tool = "pointValve"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.insertValveButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.insertValveButton, self, self.runInsertValve, SelectPointType.Line, cursor=":/images/iconAddValve.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runInsertValve(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.InsertValve(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPumpPoint(self):
        tool = "pointPump"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.insertPumpButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.insertPumpButton, self, self.runInsertPump, SelectPointType.Line, cursor=":/images/iconAddPump.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runInsertPump(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.InsertPump(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectElements(self):
        tool = "selectElements"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            self.myMapTools[tool] = QGISRedMultiLayerSelection(self.iface, self.iface.mapCanvas(), self.selectElementsButton)
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMoveElements(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveElementsButton.setChecked(False)
            return

        oldTool = "moveVertexs"
        if oldTool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[oldTool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[oldTool])

        tool = "moveNodes"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.moveElementsButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedMoveNodesTool(
                self.moveElementsButton, self.iface, self.ProjectDirectory, self.NetworkName
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CursorShape.CrossCursor)

    def runEditLinkGeometry(self):
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.moveVertexsButton.setChecked(False)
            return

        oldTool = "moveNodes"
        if oldTool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[oldTool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[oldTool])

        tool = "moveVertexs"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
        else:
            if self.isLayerOnEdition():
                self.moveVertexsButton.setChecked(False)
                return
            self.myMapTools[tool] = QGISRedEditLinksGeometryTool(
                self.moveVertexsButton, self.iface, self.ProjectDirectory, self.NetworkName
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])
            self.setCursor(Qt.CursorShape.CrossCursor)

    def canReverseLink(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.reverseLinkButton.setChecked(False)
            return

        if not self.getSelectedFeaturesIds():
            self.reverseLinkButton.setChecked(False)
            return

        if self.linkIds == "" and not "ServiceConnections" in self.selectedIds:
            self.runSelectReverseLinkPoint()
            return
        self.reverseLinkButton.setChecked(False)

        if self.isLayerOnEdition():
            return

        self.runReverseLink(None)

    def runSelectReverseLinkPoint(self):
        tool = "pointReverseLink"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.reverseLinkButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.reverseLinkButton, self, self.runReverseLink, SelectPointType.Line, cursor=":/images/iconReverseElements.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runReverseLink(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        ids = ""
        pointText = ""
        if point is not None:
            point = self.transformPoint(point)
            pointText = str(point.x()) + ":" + str(point.y())
        else:
            for key in self.selectedIds:
                ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        self.especificComplementaryLayers = ["ServiceConnections"]
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ReverseLink(self.ProjectDirectory, self.NetworkName, self.tempFolder, pointText, ids)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectSplitPoint(self):
        tool = "pointSplit"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.splitPipeButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.splitPipeButton, self, self.runSplitPipe, SelectPointType.Line, cursor=":/images/iconSplitJoinPipes.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runSplitPipe(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.SplitPipe(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToMergeSplit(self):
        tool = "mergeSplitPoint"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.mergeSplitJunctionButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.mergeSplitJunctionButton, self, self.runMergeSplitPoints, SelectPointType.TwoPoints, cursor=":/images/iconMergeSplitJunctions.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMergeSplitPoints(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = self.transformPoint(point2)
            point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.SplitMergeJunction(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToTconnections(self):
        tool = "createReverseTconn"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.createReverseTconButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(
                self.createReverseTconButton, self, self.runCreateRemoveTconnections, SelectPointType.PointLine, cursor=":/images/iconCreateRemoveTConnections.svg"
            )
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateRemoveTconnections(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        if point2 is None:
            point2 = ""
        else:
            point2 = self.transformPoint(point2)
            point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CreateReverseTConnection(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectPointToCrossings(self):
        tool = "createReverseCross"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.createReverseCrossButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.createReverseCrossButton, self, self.runCreateRemoveCrossings, SelectPointType.Line, cursor=":/images/iconCreateRemoveCrossings.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runCreateRemoveCrossings(self, point1):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point1 = str(point1.x()) + ":" + str(point1.y())
        # Important, no snapping in crossings
        tolerance = str(self.getTolerance())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.CreateReverseCrossings(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, tolerance)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectValvePumpPoints(self):
        tool = "moveValvePump"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.moveValvePumpButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.moveValvePumpButton, self, self.runMoveValvePump, SelectPointType.TwoLines, cursor=":/images/iconMoveElements.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runMoveValvePump(self, point1, point2):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point1 = self.transformPoint(point1)
        point2 = self.transformPoint(point2)
        point1 = str(point1.x()) + ":" + str(point1.y())
        point2 = str(point2.x()) + ":" + str(point2.y())

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.MoveValvePump(self.ProjectDirectory, self.NetworkName, self.tempFolder, point1, point2)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runSelectElementStatusPoint(self):
        tool = "pointElementStatus"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.changeStatusButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.changeStatusButton, self, self.runChangeStatus, SelectPointType.Line, cursor=":/images/iconChangeStatus.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runChangeStatus(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        point = self.transformPoint(point)
        point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = ["IsolationValves", "Meters", "ServiceConnections"]
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.ChangeStatus(self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def canDeleteElements(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            self.removeElementsButton.setChecked(False)
            return

        if not self.getSelectedFeaturesIds():
            self.removeElementsButton.setChecked(False)
            return
        if len(self.selectedIds) == 0:
            self.runSelectDeleteElementPoint()
            return
        self.removeElementsButton.setChecked(False)

        if self.isLayerOnEdition():
            return

        self.runDeleteElement(None)

    def runSelectDeleteElementPoint(self):
        tool = "pointDeleteElement"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.removeElementsButton.setChecked(False)
        else:
            self.myMapTools[tool] = QGISRedSelectPointTool(self.removeElementsButton, self, self.runDeleteElement, SelectPointType.Line, cursor=":/images/iconDeleteElements.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runDeleteElement(self, point):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        pointText = ""
        if point is not None:
            point = self.transformPoint(point)
            pointText = str(point.x()) + ":" + str(point.y())

        ids = ""
        for key in self.selectedIds:
            ids = ids + key + ":" + str(self.selectedIds[key]) + ";"

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.RemoveElements(self.ProjectDirectory, self.NetworkName, self.tempFolder, pointText, ids)
        QApplication.restoreOverrideCursor()

        self.selectedFids = {}
        self.processCsharpResult(resMessage, "")

    def runSelectPointProperties(self):
        tool = "pointElement"
        if tool in self.myMapTools.keys() and self.iface.mapCanvas().mapTool() is self.myMapTools[tool]:
            self.iface.mapCanvas().unsetMapTool(self.myMapTools[tool])
            self.editElementButton.setChecked(False)
        else:
            self.gisredDll = None
            self.myMapTools[tool] = QGISRedSelectPointTool(self.editElementButton, self, self.runProperties, SelectPointType.Line, cursor=":/images/pencil.svg")
            self.iface.mapCanvas().setMapTool(self.myMapTools[tool])

    def runProperties(self, point):
        # Guard against calls during shutdown
        if self.isUnloading:
            return
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        if not point == "":
            point = self.transformPoint(point)
            point = str(point.x()) + ":" + str(point.y())

        # Process
        self.especificComplementaryLayers = self.getComplementaryLayersOpened()
        if self.gisredDll is None:
            self.gisredDll = GISRed.CreateInstance()
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.EditElements(self.gisredDll, self.ProjectDirectory, self.NetworkName, self.tempFolder, point)
        QApplication.restoreOverrideCursor()

        if resMessage == "Select":
            self.blockLayers(True)
        elif resMessage.startswith("["):
            self.blockLayers(True)
            comp = resMessage.split("]")
            layerName = comp[0].replace("[", "")
            elementId = comp[1]
            self.zoomToElementFromProperties(layerName, elementId)

            self.runProperties("")
        else:
            self.processCsharpResult(resMessage, "")
            self.gisredDll = None
            self.blockLayers(False)

    def runPatternsCurves(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.EditPatternsCurves(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")

    def runControls(self):
        if not self.checkDependencies():
            return
        # Validations
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if self.isLayerOnEdition():
            return

        # Process
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        resMessage = GISRed.EditControls(self.ProjectDirectory, self.NetworkName, self.tempFolder)
        QApplication.restoreOverrideCursor()

        self.processCsharpResult(resMessage, "")
