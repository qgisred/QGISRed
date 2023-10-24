# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsTextFormat
from qgis.core import QgsProperty, QgsRenderContext, QgsRendererRange
from qgis.core import QgsGraduatedSymbolRenderer, QgsGradientColorRamp as QgsVectorGradientColorRamp, QgsRuleBasedRenderer

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed

import os
from shutil import copyfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_results_dock.ui"))


class QGISRedResultsDock(QDockWidget, FORM_CLASS):
    # Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    LabelResults = {}
    IndexTime = {}
    Comments = {}
    Renders = {}
    Variables = ""
    Computing = False
    TimeLabels = []
    LabelsToOpRe = []

    def __init__(self, iface):
        """Constructor."""
        super(QGISRedResultsDock, self).__init__(iface.mainWindow())
        self.iface = iface
        self.setupUi(self)

        self.btMoreTime.clicked.connect(self.nextTime)
        self.btEndTime.clicked.connect(self.endTime)
        self.btLessTime.clicked.connect(self.previousTime)
        self.btInitTime.clicked.connect(self.initTime)
        self.cbTimes.view().setVerticalScrollBarPolicy(0)
        self.cbTimes.currentIndexChanged.connect(self.timeChanged)
        self.timeSlider.valueChanged.connect(self.sliderChanged)

        self.cbLinks.currentIndexChanged.connect(self.linksChanged)
        self.cbNodes.currentIndexChanged.connect(self.nodesChanged)
        self.cbLinkLabels.clicked.connect(self.linkLabelsClicked)
        self.cbNodeLabels.clicked.connect(self.nodeLabelsClicked)
        self.cbFlowDirections.clicked.connect(self.flowDirectionsClicked)
        self.btSaveScenario.clicked.connect(self.saveScenario)
        self.cbScenarios.currentIndexChanged.connect(self.scenarioChanged)
        self.btDeleteScenario.clicked.connect(self.deleteScenario)

    """Methods"""

    def isCurrentProject(self):
        currentNetwork = ""
        currentDirectory = ""
        message = "The current project has been changed. Please, try again."

        layers = self.getLayers()
        layerName = "Pipes"
        for layer in layers:
            layerUri = self.getLayerPath(layer)
            if "_" + layerName in layerUri:
                currentDirectory = os.path.dirname(layerUri)
                fileNameWithoutExt = os.path.splitext(os.path.basename(layerUri))[0]
                currentNetwork = fileNameWithoutExt.replace("_" + layerName, "")
                if self.NetworkName == currentNetwork and self.ProjectDirectory == currentDirectory:
                    return True
                else:
                    self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)
                    self.close()
                    return False

        self.iface.messageBar().pushMessage("Warning", message, level=1, duration=5)
        self.close()
        return False

    def insert(self, source_str, insert_str, pos):
        return source_str[:pos] + insert_str + source_str[pos:]

    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    """Layers and Groups"""

    def getLayers(self):
        return QGISRedUtils().getLayers()

    def openLayerResults(self, scenario):
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + scenario, self.iface)
        resultGroup = self.getResultGroup()
        group = resultGroup.findGroup(scenario)
        if group is None:
            group = resultGroup.addGroup(scenario)
        for file in self.LabelsToOpRe:
            utils.openLayer(group, file, results=True)

    def removeResults(self, task):
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + self.Scenario, self.iface)
        utils.removeLayers(self.LabelsToOpRe)
        if task is not None:
            return {"task": task.definition()}

    def getInputGroup(self):
        # Same method in qgisred_newproject_dialog and qgisred_plugins
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def getResultGroup(self):
        resultGroup = QgsProject.instance().layerTreeRoot().findGroup("Results")
        if resultGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.addGroup(self.NetworkName)
            resultGroup = netGroup.insertGroup(0, "Results")
        resultGroup.setItemVisibilityChecked(True)
        return resultGroup

    """UI Elements"""

    def setSelectedItemInLinkNodeComboboxes(self, nameLayer):
        if nameLayer == "Link_Flow":
            self.cbLinks.setCurrentIndex(1)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_Velocity":
            self.cbLinks.setCurrentIndex(2)
        if nameLayer == "Link_HeadLoss":
            self.cbLinks.setCurrentIndex(3)
        if nameLayer == "Link_UnitHeadLoss":
            self.cbLinks.setCurrentIndex(4)
        if nameLayer == "Link_Status":
            self.cbLinks.setCurrentIndex(5)
        if nameLayer == "Link_Quality":
            self.cbLinks.setCurrentIndex(6)
        if nameLayer == "Node_Pressure":
            self.cbNodes.setCurrentIndex(1)
        if nameLayer == "Node_Head":
            self.cbNodes.setCurrentIndex(2)
        if nameLayer == "Node_Demand":
            self.cbNodes.setCurrentIndex(3)
        if nameLayer == "Node_Quality":
            self.cbNodes.setCurrentIndex(4)

    def restoreElementsCb(self):
        self.Scenario = self.cbScenarios.currentText()
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        self.setLayersNames(True)
        layers = self.getLayers()

        self.Computing = True
        self.cbLinks.setCurrentIndex(0)
        self.cbNodes.setCurrentIndex(0)
        self.cbFlowDirections.setVisible(False)

        for nameLayer in self.LabelsToOpRe:
            layerResult = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openLayerPath = self.getLayerPath(layer)
                if openLayerPath == layerResult:
                    self.setSelectedItemInLinkNodeComboboxes(nameLayer)
        self.Computing = False

    """Create Lists"""

    def setVariables(self):
        self.Variables = ""
        if self.cbLinks.currentIndex() == 1:
            self.Variables = self.Variables + "Flow_Link;"
        if self.cbLinks.currentIndex() == 2:
            self.Variables = self.Variables + "Velocity_Link;"
        if self.cbLinks.currentIndex() == 3:
            self.Variables = self.Variables + "HeadLoss_Link;"
        if self.cbLinks.currentIndex() == 4:
            self.Variables = self.Variables + "UnitHeadLoss_Link;"
        if self.cbLinks.currentIndex() == 5:
            self.Variables = self.Variables + "Status_Link;"
        if self.cbLinks.currentIndex() == 6:
            self.Variables = self.Variables + "Quality_Link;"
        if self.cbNodes.currentIndex() == 1:
            self.Variables = self.Variables + "Pressure_Node;"
        if self.cbNodes.currentIndex() == 2:
            self.Variables = self.Variables + "Head_Node;"
        if self.cbNodes.currentIndex() == 3:
            self.Variables = self.Variables + "Demand_Node;"
        if self.cbNodes.currentIndex() == 4:
            self.Variables = self.Variables + "Quality_Node;"

        if self.Variables == "":
            self.iface.messageBar().pushMessage("Validations", "No variable results selected", level=1)
            return False
        return True

    def setLayersNames(self, allLayers=False):
        self.LabelsToOpRe = []
        if self.cbLinks.currentIndex() == 1 or allLayers:
            self.LabelsToOpRe.append("Link_Flow")
        if self.cbLinks.currentIndex() == 2 or allLayers:
            self.LabelsToOpRe.append("Link_Velocity")
        if self.cbLinks.currentIndex() == 3 or allLayers:
            self.LabelsToOpRe.append("Link_HeadLoss")
        if self.cbLinks.currentIndex() == 4 or allLayers:
            self.LabelsToOpRe.append("Link_UnitHeadLoss")
        if self.cbLinks.currentIndex() == 5 or allLayers:
            self.LabelsToOpRe.append("Link_Status")
        if self.cbLinks.currentIndex() == 6 or allLayers:
            self.LabelsToOpRe.append("Link_Quality")
        if self.cbNodes.currentIndex() == 1 or allLayers:
            self.LabelsToOpRe.append("Node_Pressure")
        if self.cbNodes.currentIndex() == 2 or allLayers:
            self.LabelsToOpRe.append("Node_Head")
        if self.cbNodes.currentIndex() == 3 or allLayers:
            self.LabelsToOpRe.append("Node_Demand")
        if self.cbNodes.currentIndex() == 4 or allLayers:
            self.LabelsToOpRe.append("Node_Quality")

    def setLinksLayersNames(self):
        self.LabelsToOpRe = []
        self.LabelsToOpRe.append("Link_Flow")
        self.LabelsToOpRe.append("Link_Velocity")
        self.LabelsToOpRe.append("Link_HeadLoss")
        self.LabelsToOpRe.append("Link_UnitHeadLoss")
        self.LabelsToOpRe.append("Link_Status")
        self.LabelsToOpRe.append("Link_Quality")

    def setNodesLayersNames(self):
        self.LabelsToOpRe = []
        self.LabelsToOpRe.append("Node_Pressure")
        self.LabelsToOpRe.append("Node_Head")
        self.LabelsToOpRe.append("Node_Demand")
        self.LabelsToOpRe.append("Node_Quality")

    """Symbology"""

    def saveCurrentRender(self):
        openedLayers = self.getLayers()
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        dictSce = self.Renders.get(self.Scenario)
        if dictSce is None:
            dictSce = {}
        for nameLayer in self.LabelsToOpRe:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in openedLayers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    renderer = layer.renderer()
                    if renderer.type() == "graduatedSymbol":
                        # Guarda por ruta, se pierde al cerrar QGis
                        dictSce[openedLayerPath] = renderer.ranges()
                    else:
                        dictSce[openedLayerPath] = renderer.rootRule().clone()
        self.Renders[self.Scenario] = dictSce

    def paintIntervalTimeResults(self, columnNumber, setRender=False):
        if not self.isCurrentProject():
            return

        self.Scenario = self.cbScenarios.currentText()
        resultPath = os.path.join(self.ProjectDirectory, "Results")

        layers = self.getLayers()

        self.lbTime.setText(self.TimeLabels[columnNumber])
        for nameLayer in self.LabelsToOpRe:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    field_names = [field.name() for field in layer.fields()]
                    field = field_names[columnNumber + 2]
                    self.setGraduadedPalette(layer, field, setRender, nameLayer)
                    layer.setName(nameLayer.replace("_", " "))
                    name = nameLayer.replace("Link_", "").replace("Node_", "") + ': [% "T' + str(columnNumber) + '" %]'
                    layer.setMapTipTemplate(name)
                    self.setLayerLabels(layer, "T" + str(columnNumber))

    def setLayerLabels(self, layer, fieldName):
        firstCondition = layer.geometryType() == 0 and self.cbNodeLabels.isChecked()
        secondCondition = layer.geometryType() != 0 and self.cbLinkLabels.isChecked()
        if firstCondition or secondCondition:
            layer_settings = QgsPalLayerSettings()
            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 10))
            color = "black"
            # if secondCondition:
            #     color = "blue"
            text_format.setColor(QColor(color))
            layer_settings.setFormat(text_format)

            layer_settings.fieldName = fieldName
            layer_settings.placement = QgsPalLayerSettings.Line
            layer_settings.enabled = True
            labels = QgsVectorLayerSimpleLabeling(layer_settings)
            layer.setLabeling(labels)
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()

    def getColorClasses(self, symbol, nameLayer):
        # Five classes as deafult
        simb1 = symbol.clone()
        simb2 = symbol.clone()
        simb3 = symbol.clone()
        simb4 = symbol.clone()
        simb5 = symbol.clone()
        simb1.setColor(QColor(0, 0, 255))
        simb2.setColor(QColor(0, 255, 255))
        simb3.setColor(QColor(0, 255, 0))
        simb4.setColor(QColor(255, 255, 0))
        simb5.setColor(QColor(165, 0, 0))
        ranges = []
        if "Pressure" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 20, simb1, "<20"))
            ranges.append(QgsRendererRange(20, 30, simb2, "20-30"))
            ranges.append(QgsRendererRange(30, 40, simb3, "30-40"))
            ranges.append(QgsRendererRange(40, 50, simb4, "40-50"))
            ranges.append(QgsRendererRange(50, 1e10, simb5, ">50"))
        elif "Node_Head" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 20, simb1, "<20"))
            ranges.append(QgsRendererRange(20, 40, simb2, "20-40"))
            ranges.append(QgsRendererRange(40, 60, simb3, "40-60"))
            ranges.append(QgsRendererRange(60, 80, simb4, "60-80"))
            ranges.append(QgsRendererRange(80, 1e10, simb5, ">80"))
        elif "Demand" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 5, simb1, "<5"))
            ranges.append(QgsRendererRange(5, 10, simb2, "5-10"))
            ranges.append(QgsRendererRange(10, 20, simb3, "10-20"))
            ranges.append(QgsRendererRange(20, 40, simb4, "20-40"))
            ranges.append(QgsRendererRange(40, 1e10, simb5, ">40"))
        elif "Node_Quality" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 25, simb1, "<25%"))
            ranges.append(QgsRendererRange(25, 50, simb2, "25%-50%"))
            ranges.append(QgsRendererRange(50, 75, simb3, "50%-75%"))
            ranges.append(QgsRendererRange(75, 100, simb4, "75%-100%"))
            ranges.append(QgsRendererRange(100, 1e10, simb5, ">100%"))
        elif "Flow" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 10, simb1, "<10"))
            ranges.append(QgsRendererRange(10, 20, simb2, "10-20"))
            ranges.append(QgsRendererRange(20, 50, simb3, "20-50"))
            ranges.append(QgsRendererRange(50, 100, simb4, "50-100"))
            ranges.append(QgsRendererRange(100, 1e10, simb5, ">100"))
        elif "Velocity" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 0.1, simb1, "<0.1"))
            ranges.append(QgsRendererRange(0.1, 0.5, simb2, "0.1-0.5"))
            ranges.append(QgsRendererRange(0.5, 1, simb3, "0.5-1"))
            ranges.append(QgsRendererRange(1, 2, simb4, "1-2"))
            ranges.append(QgsRendererRange(2, 1e10, simb5, ">2"))
        elif "HeadLoss" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 0.1, simb1, "<0.1"))
            ranges.append(QgsRendererRange(0.1, 0.5, simb2, "0.1-0.5"))
            ranges.append(QgsRendererRange(0.5, 1, simb3, "0.5-1"))
            ranges.append(QgsRendererRange(1, 5, simb4, "1-5"))
            ranges.append(QgsRendererRange(5, 1e10, simb5, ">5"))
        elif "UnitHeadLoss" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 0.1, simb1, "<0.1"))
            ranges.append(QgsRendererRange(0.1, 0.5, simb2, "0.1-0.5"))
            ranges.append(QgsRendererRange(0.5, 1, simb3, "0.5-1"))
            ranges.append(QgsRendererRange(1, 5, simb4, "1-5"))
            ranges.append(QgsRendererRange(5, 1e10, simb5, ">5"))
        elif "Link_Quality" in nameLayer:
            ranges.append(QgsRendererRange(-1e10, 25, simb1, "<25%"))
            ranges.append(QgsRendererRange(25, 50, simb2, "25%-50%"))
            ranges.append(QgsRendererRange(50, 75, simb3, "50%-75%"))
            ranges.append(QgsRendererRange(75, 100, simb4, "75%-100%"))
            ranges.append(QgsRendererRange(100, 1e10, simb5, ">100%"))

        return ranges

    def setArrowsVisibility(self, symbol, layer, prop, field):
        if "Flow" in layer.name() and self.cbFlowDirections.isChecked():
            # Show arrows in pipes
            ss = symbol.symbolLayer(3)  # arrow positive flow
            prop.setExpressionString("if(Type='PIPE', if(" + field + ">0,3,0),0)")
            ss.subSymbol().setDataDefinedSize(prop)
            ss = symbol.symbolLayer(4)  # arrow negative flow
            prop.setExpressionString("if(Type='PIPE', if(" + field + "<0,3,0),0)")
            ss.subSymbol().setDataDefinedSize(prop)
        else:
            # Hide arrows
            prop.setExpressionString("0")
            symbol.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
            symbol.symbolLayer(4).subSymbol().setDataDefinedSize(prop)

    def setNodesVisibility(self, prop, symbol):
        prop.setExpressionString("if(Type ='TANK', 7,0)")
        symbol.symbolLayer(0).setDataDefinedProperty(0, prop)  # 0 = PropertySize
        symbol.symbolLayer(0).setDataDefinedProperty(9, prop)  # 0 = PropertyWidth
        prop.setExpressionString("if(Type ='RESERVOIR', 7,0)")
        symbol.symbolLayer(1).setDataDefinedProperty(0, prop)
        symbol.symbolLayer(1).setDataDefinedProperty(9, prop)
        prop.setExpressionString("if(Type ='RESERVOIR' or Type='TANK', 0,2)")
        symbol.symbolLayer(2).setDataDefinedProperty(0, prop)
        symbol.symbolLayer(2).setDataDefinedProperty(9, prop)

    def setGraduadedPalette(self, layer, field, setRender, nameLayer):
        renderer = layer.renderer()
        prop = QgsProperty()
        # Set arrows and node icon visibility (only when layer is opened)
        # Links icon visibility are assigned when style is applied in Utils
        if setRender:  # Just opened a layer
            # SimpleSymbol (first time)
            symbol = renderer.symbol()
            if symbol.type() == 1:  # line
                self.setArrowsVisibility(symbol, layer, prop, field)
            else:  # point
                self.setNodesVisibility(prop, symbol)
        else:
            if not "Link_Status" in nameLayer:
                # GraduatedSymbol (other times)
                symbols = renderer.symbols(QgsRenderContext())
                for symbol in symbols:
                    if symbol.type() == 1:  # line
                        self.setArrowsVisibility(symbol, layer, prop, field)

        if "Flow" in layer.name():
            field = "abs(" + field + ")"

        # Set graduated colors
        if setRender:  # Just opened a layer
            # Has previous render saved?
            hasRender = False
            dictRend = self.Renders.get(self.Scenario)
            if dictRend is None:
                dictRend = self.Renders.get("Base")  # default
                if dictRend is not None:
                    ranges = dictRend.get(self.getLayerPath(layer).replace("_" + self.Scenario + "_", "_Base_"))
                    if ranges is not None:
                        hasRender = True
            else:
                ranges = dictRend.get(self.getLayerPath(layer))
                if ranges is not None:
                    hasRender = True
                else:
                    dictRend = self.Renders.get("Base")  # default
                    if dictRend is not None:
                        ranges = dictRend.get(self.getLayerPath(layer).replace("_" + self.Scenario + "_", "_Base_"))
                        if ranges is not None:
                            hasRender = True

            # Apply render
            if hasRender:
                if "Link_Status" in nameLayer:
                    renderer = QgsRuleBasedRenderer(ranges)  # this ranges is a rootRule
                else:
                    renderer = QgsGraduatedSymbolRenderer(field, ranges)
            else:
                if "Link_Status" in nameLayer:
                    symbol = renderer.symbol().clone()
                    renderer = QgsRuleBasedRenderer(symbol)
                    root_rule = renderer.rootRule()

                    self.setRule(root_rule, "1-Temp Closed", field, "=1", "red", True)
                    self.setRule(root_rule, "2-Closed", field, "=2", "red")
                    self.setRule(root_rule, "5-Closed (H > Hmax)", field, "=5", "red")
                    self.setRule(root_rule, "8-Closed (Q < 0)", field, "=8", "red")
                    self.setRule(root_rule, "9-Closed (P < Pset)", field, "=9", "red")
                    self.setRule(root_rule, "11-Closed (P > Pset)", field, "=11", "red")

                    self.setRule(root_rule, "3-Open", field, "=3", "green")
                    self.setRule(root_rule, "6-Open (Q > Qmax)", field, "=6", "green")
                    self.setRule(root_rule, "7-Open (Q < Qset)", field, "=7", "green")
                    self.setRule(root_rule, "10-Open (P > Pset)", field, "=10", "green")
                    self.setRule(root_rule, "12-Open (P < Pset)", field, "=12", "green")

                    self.setRule(root_rule, "4-Active", field, "=4", "orange")
                    self.setRule(root_rule, "13-Active (Rev Pump)", field, "=13", "orange")
                else:
                    ranges = self.getColorClasses(symbol, nameLayer)
                    if len(ranges) > 0:
                        renderer = QgsGraduatedSymbolRenderer(field, ranges)
                    else:
                        mode = QgsGraduatedSymbolRenderer.EqualInterval  # Quantile
                        classes = 5
                        ramp = {
                            "color1": "0,0,255,255",
                            "color2": "255,0,0,255",
                            "stops": "0.25;0,255,255,255:0.50;0,255,0,255:0.75;255,255,0,255",
                        }
                        colorRamp = QgsVectorGradientColorRamp.create(ramp)
                        self.iface.setActiveLayer(layer)
                        renderer = QgsGraduatedSymbolRenderer.createRenderer(layer, field, classes, mode, symbol, colorRamp)
                        myFormat = renderer.labelFormat()
                        myFormat.setPrecision(2)
                        myFormat.setTrimTrailingZeroes(True)
                        renderer.setLabelFormat(myFormat, True)
        else:
            if "Link_Status" in nameLayer:  # Id users change the layer style it will fail
                root_rule = renderer.rootRule()
                self.setFilterExpression(root_rule, 0, field, "=1")
                self.setFilterExpression(root_rule, 1, field, "=2")
                self.setFilterExpression(root_rule, 2, field, "=5")
                self.setFilterExpression(root_rule, 3, field, "=8")
                self.setFilterExpression(root_rule, 4, field, "=9")
                self.setFilterExpression(root_rule, 5, field, "=11")
                self.setFilterExpression(root_rule, 6, field, "=3")
                self.setFilterExpression(root_rule, 7, field, "=6")
                self.setFilterExpression(root_rule, 8, field, "=7")
                self.setFilterExpression(root_rule, 9, field, "=10")
                self.setFilterExpression(root_rule, 10, field, "=12")
                self.setFilterExpression(root_rule, 11, field, "=4")
                self.setFilterExpression(root_rule, 12, field, "=13")
            else:
                renderer.setClassAttribute(field)

        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def setRule(self, root_rule, label, field, expression, color, first=False):
        rule = root_rule.children()[0].clone()
        rule.setLabel(label)
        rule.setFilterExpression(field + expression)
        rule.symbol().setColor(QColor(color))
        if first:
            root_rule.removeChildAt(0)
        root_rule.appendChild(rule)

    def setFilterExpression(self, root_rule, index, field, expression):
        rule = root_rule.children()[index]
        rule.setFilterExpression(field + expression)

    """Scenario"""

    def writeScenario(self, scenario, labels, comments):
        filePath = os.path.join(os.path.join(self.ProjectDirectory, "Results"), self.NetworkName + "_" + scenario + ".sce")
        f = open(filePath, "w+")
        QGISRedUtils().writeFile(f, "[TimeLabels]" + "\n")
        lab = ""
        for label in labels:
            lab = lab + label + ";"
        lab = lab.strip(";")
        QGISRedUtils().writeFile(f, lab + "\n")
        QGISRedUtils().writeFile(f, "[Comments]" + "\n")
        QGISRedUtils().writeFile(f, comments + "\n")
        f.close()

    def readSavedScenarios(self):
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        if not os.path.exists(resultPath):
            return
        files = os.listdir(resultPath)
        for file in files:  # only names
            if ".sce" in file and "_Base" not in file:
                f = open(os.path.join(resultPath, file), "r")
                nameSc = file.replace(self.NetworkName + "_", "").replace(".sce", "")
                isLabel = False
                isComments = False
                comments = ""
                for line in f:
                    if "[TimeLabels]" in line:
                        isLabel = True
                        continue
                    if "[Comments]" in line:
                        isComments = True
                        continue
                    if isLabel:
                        self.LabelResults[nameSc] = line.strip("\r\n").split(";")
                        isLabel = False
                    if isComments:
                        comments = comments + line.strip() + "\n"

                comments = comments.strip("\n").strip().strip("\n")
                self.IndexTime[nameSc] = 0
                self.Comments[nameSc] = comments
                self.cbScenarios.addItem(nameSc)
                f.close()

    """Clicked events"""

    def linksChanged(self):
        if self.Computing:
            return
        self.cbFlowDirections.setVisible(False)
        if not self.validationsOpenResult():
            return
        result = ""
        if self.cbLinks.currentIndex() == 1:
            result = "Flow"
            self.cbFlowDirections.setVisible(True)
        if self.cbLinks.currentIndex() == 2:
            result = "Velocity"
        if self.cbLinks.currentIndex() == 3:
            result = "HeadLoss"
        if self.cbLinks.currentIndex() == 4:
            result = "UnitHeadLoss"
        if self.cbLinks.currentIndex() == 5:
            result = "Status"
        if self.cbLinks.currentIndex() == 6:
            result = "Quality"

        self.setLinksLayersNames()
        self.saveCurrentRender()
        self.removeResults(None)
        self.LabelsToOpRe = []
        if not self.cbLinks.currentIndex() == 0:
            self.LabelsToOpRe.append("Link_" + result)
            self.Variables = result + "_Link"
            self.openResult()

    def nodesChanged(self):
        if self.Computing:
            return
        if not self.validationsOpenResult():
            return
        result = ""
        if self.cbNodes.currentIndex() == 1:
            result = "Pressure"
        if self.cbNodes.currentIndex() == 2:
            result = "Head"
        if self.cbNodes.currentIndex() == 3:
            result = "Demand"
        if self.cbNodes.currentIndex() == 4:
            result = "Quality"

        self.setNodesLayersNames()
        self.saveCurrentRender()
        self.removeResults(None)
        self.LabelsToOpRe = []
        if not self.cbNodes.currentIndex() == 0:
            self.LabelsToOpRe.append("Node_" + result)
            self.Variables = result + "_Node"
            self.saveCurrentRender()
            self.openResult()

    def nodeLabelsClicked(self):
        self.setNodesLayersNames()
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        layers = self.getLayers()
        for nameLayer in self.LabelsToOpRe:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    if self.cbNodeLabels.isChecked():
                        self.setLayerLabels(layer, "T" + str(self.cbTimes.currentIndex()))
                    else:
                        layer.setLabelsEnabled(False)
                        layer.triggerRepaint()

    def linkLabelsClicked(self):
        self.setLinksLayersNames()
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        layers = self.getLayers()
        for nameLayer in self.LabelsToOpRe:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    if self.cbLinkLabels.isChecked():
                        self.setLayerLabels(layer, "T" + str(self.cbTimes.currentIndex()))
                    else:
                        layer.setLabelsEnabled(False)
                        layer.triggerRepaint()

    def flowDirectionsClicked(self):
        if self.cbLinks.currentIndex() == 1:
            if not self.validationsOpenResult(True):
                return
            if self.cbLinks.currentIndex() == 1:
                self.LabelsToOpRe.append("Link_Flow")
                self.Variables = "Flow_Link"
                value = self.cbTimes.currentIndex()
                self.paintIntervalTimeResults(value, False)

    def nextTime(self):
        index = self.cbTimes.currentIndex()
        if self.cbTimes.count() - 1 == index:
            self.cbTimes.setCurrentIndex(0)
        else:
            self.cbTimes.setCurrentIndex(index + 1)

    def endTime(self):
        self.cbTimes.setCurrentIndex(self.cbTimes.count() - 1)

    def initTime(self):
        self.cbTimes.setCurrentIndex(0)

    def previousTime(self):
        index = self.cbTimes.currentIndex()
        if index == 0:
            self.cbTimes.setCurrentIndex(self.cbTimes.count() - 1)
        else:
            self.cbTimes.setCurrentIndex(index - 1)

    def sliderChanged(self):
        if not self.timeSlider.value() == self.cbTimes.currentIndex():
            self.cbTimes.setCurrentIndex(self.timeSlider.value())

    def timeChanged(self):
        if self.Computing:
            return
        self.Scenario = self.cbScenarios.currentText()
        resultPath = os.path.join(os.path.join(self.ProjectDirectory, "Results"), self.NetworkName + "_" + self.Scenario)
        if not os.path.exists(resultPath):
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=5)
            return

        value = self.cbTimes.currentIndex()
        self.timeSlider.setValue(value)
        self.IndexTime[self.cbScenarios.currentText()] = value
        self.setLayersNames()
        self.paintIntervalTimeResults(value, False)

    def scenarioChanged(self):
        if self.Computing:
            return

        currentScenario = self.cbScenarios.currentText()
        self.TimeLabels = self.LabelResults[currentScenario]
        self.Computing = True

        self.cbTimes.clear()
        if len(self.TimeLabels) == 1:
            self.lbLabel5.setVisible(False)
            self.btLessTime.setVisible(False)
            self.btMoreTime.setVisible(False)
            self.btInitTime.setVisible(False)
            self.btEndTime.setVisible(False)
            self.cbTimes.setVisible(False)
            self.timeSlider.setVisible(False)
            self.cbTimes.addItem("Permanent")
        else:
            self.lbLabel5.setVisible(True)
            self.btLessTime.setVisible(True)
            self.btMoreTime.setVisible(True)
            self.btInitTime.setVisible(True)
            self.btEndTime.setVisible(True)
            self.cbTimes.setVisible(True)
            self.timeSlider.setVisible(True)
            for label in self.TimeLabels:
                self.cbTimes.addItem(label)
            if self.IndexTime.get(currentScenario) is not None:
                self.cbTimes.setCurrentIndex(self.IndexTime[currentScenario])
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        self.lbTime.setText(self.TimeLabels[self.IndexTime[currentScenario]])
        self.lbComments.setText(self.Comments[currentScenario])
        self.Computing = False

        self.btDeleteScenario.setEnabled(not currentScenario == "Base")

        self.Scenario = currentScenario
        self.restoreElementsCb()
        self.Computing = True
        self.setLayersNames()
        if len(self.LabelsToOpRe) == 0:
            self.cbLinks.setCurrentIndex(1)
            self.cbFlowDirections.setVisible(True)
            self.cbNodes.setCurrentIndex(1)
            self.IndexTime[currentScenario] = self.cbTimes.currentIndex()
            self.openAllResults()
        self.Computing = False

    """Main methods"""

    def validationsOpenResult(self, restore=False):
        if not self.isCurrentProject():
            return False
        self.Scenario = self.cbScenarios.currentText()
        resultPath = os.path.join(os.path.join(self.ProjectDirectory, "Results"), self.NetworkName + "_" + self.Scenario)
        if not os.path.exists(resultPath):
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=5)
            return False

        if restore:
            self.restoreElementsCb()
        self.LabelsToOpRe = []
        return True

    def simulate(self, direct, netw):
        self.Computing = True
        # If there is a new project, reset options
        if not (self.NetworkName == netw and self.ProjectDirectory == direct):
            self.LabelResults = {}
            self.IndexTime = {}
            self.cbScenarios.clear()
            self.cbScenarios.addItem("Base")
            self.NetworkName = netw
            self.ProjectDirectory = direct
            self.readSavedScenarios()

        # Project info
        self.NetworkName = netw
        self.ProjectDirectory = direct

        # Create list with results layers opened
        self.Scenario = "Base"
        self.setLayersNames(True)
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        openedLayers = self.getLayers()
        self.resultsLayersPreviouslyOpened = []
        for nameLayer in self.LabelsToOpRe:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in openedLayers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    self.resultsLayersPreviouslyOpened.append(nameLayer)

        # Save render previous remove layers
        self.LabelsToOpRe = self.resultsLayersPreviouslyOpened
        self.saveCurrentRender()

        # Remove results layers previous to simulate
        QGISRedUtils().runTask("simulate", self.removeResults, self.simulationProcess, True)

    def simulationProcess(self, exception=None, result=None):
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.Compute(self.ProjectDirectory, self.NetworkName)
        QApplication.restoreOverrideCursor()

        # Message
        if resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", self.tr("Some issues occurred in the process"), level=1, duration=5)
        elif resMessage.startswith("[TimeLabels]"):
            self.openBaseResults(resMessage.replace("[TimeLabels]", ""))
            self.show()
            # Input group
            group = self.getInputGroup()
            if group is not None:
                group.setItemVisibilityChecked(False)
            return
        else:
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

        # If some error, close the dock
        self.close()

    def openBaseResults(self, labels):
        # Scenario
        self.cbScenarios.setCurrentIndex(0)
        self.btDeleteScenario.setEnabled(False)

        # Select comboboxes item
        if len(self.LabelsToOpRe) == 0:
            self.cbLinks.setCurrentIndex(1)
            self.cbFlowDirections.setVisible(True)
            self.cbNodes.setCurrentIndex(1)
        else:
            for nameLayer in self.LabelsToOpRe:
                self.setSelectedItemInLinkNodeComboboxes(nameLayer)

        # Time labels
        mylist = labels.split(";")
        self.TimeLabels = []
        self.cbTimes.clear()
        if len(mylist) == 1:
            self.TimeLabels.append("Permanent")
            self.cbTimes.addItem("Permanent")
        else:
            for item in mylist:
                self.TimeLabels.append(self.insert(self.insert(item, " ", 6), " ", 3))
                self.cbTimes.addItem(self.insert(self.insert(item, " ", 6), " ", 3))
        self.LabelResults["Base"] = self.TimeLabels
        self.IndexTime["Base"] = 0
        self.cbTimes.setCurrentIndex(0)
        self.timeSlider.setValue(0)
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        self.lbTime.setText(self.TimeLabels[0])

        # Comments
        self.Comments["Base"] = "Last results computed"
        self.lbComments.setText(self.Comments["Base"])

        # Write Scenario
        self.writeScenario("Base", self.TimeLabels, self.Comments["Base"])

        # Configure Visibilities
        if len(mylist) == 1:
            self.lbLabel5.setVisible(False)
            self.btLessTime.setVisible(False)
            self.btMoreTime.setVisible(False)
            self.btInitTime.setVisible(False)
            self.btEndTime.setVisible(False)
            self.cbTimes.setVisible(False)
            self.timeSlider.setVisible(False)
        else:
            self.lbLabel5.setVisible(True)
            self.btLessTime.setVisible(True)
            self.btMoreTime.setVisible(True)
            self.btInitTime.setVisible(True)
            self.btEndTime.setVisible(True)
            self.cbTimes.setVisible(True)
            self.timeSlider.setVisible(True)

        self.Computing = False

        # Open results
        self.openAllResults()

    def openAllResults(self):
        resultPath = os.path.join(os.path.join(self.ProjectDirectory, "Results"), self.NetworkName + "_" + self.Scenario)
        if not os.path.exists(resultPath):
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=5)
            return

        if not self.setVariables():
            return

        # Process
        self.setLayersNames(True)
        # Task is necessary because after remove layers, DBF files are in use. With the task,
        # the remove process finishs and filer are not in use
        QGISRedUtils().runTask("update all results", self.removeResults, self.openAllResultsProcess)

    def openAllResultsProcess(self, exception=None, result=None):
        self.setLayersNames()

        found = True
        for file in self.LabelsToOpRe:
            f = os.path.join(self.ProjectDirectory, "Results", self.NetworkName + "_" + self.Scenario + "_" + file + ".shp")
            if not os.path.exists(f):
                found = False
        if not found:
            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.CreateResults(self.ProjectDirectory, self.NetworkName, self.Scenario, self.Variables)
            QApplication.restoreOverrideCursor()
        else:
            resMessage = "True"

        # Open layers
        self.openLayerResults(self.Scenario)
        value = self.cbTimes.currentIndex()
        self.paintIntervalTimeResults(value, True)

        self.iface.actionMapTips().setChecked(True)

        # Message
        if resMessage == "True":
            pass  # self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

    def openResult(self):
        found = True
        for file in self.LabelsToOpRe:
            f = os.path.join(self.ProjectDirectory, "Results", self.NetworkName + "_" + self.Scenario + "_" + file + ".shp")
            if not os.path.exists(f):
                found = False
        if not found:
            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.CreateResults(self.ProjectDirectory, self.NetworkName, self.Scenario, self.Variables)
            QApplication.restoreOverrideCursor()
        else:
            resMessage = "True"

        # Open layers
        self.openLayerResults(self.Scenario)
        value = self.cbTimes.currentIndex()
        self.paintIntervalTimeResults(value, True)

        # Message
        if resMessage == "True":
            pass  # self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)

    def saveScenario(self):
        if not self.isCurrentProject():
            return False
        # Validations
        isBaseScenario = self.cbScenarios.currentText() == "Base"
        if not isBaseScenario:
            self.iface.messageBar().pushMessage("Warning", "Only 'Base' scenario could be saved", level=1, duration=5)
            return
        newScenario = self.tbScenarioName.text().strip()
        if newScenario == "":
            self.iface.messageBar().pushMessage("Warning", "Scenario name is not valid", level=1, duration=5)
            return
        for i in range(self.cbScenarios.count()):
            if self.cbScenarios.itemText(i).lower() == newScenario.lower():
                self.iface.messageBar().pushMessage("Warning", "Scenario name is already used", level=1, duration=5)
                return

        # Save options
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        try:
            copyfile(
                r"" + os.path.join(resultPath, self.NetworkName + "_Base"),
                r"" + os.path.join(resultPath, self.NetworkName + "_" + newScenario),
            )  # Binary
            files = os.listdir(resultPath)
            for file in files:  # only names
                if self.NetworkName + "_Base_Link" in file or self.NetworkName + "_Base_Node" in file:
                    newName = file.replace("_Base_", "_" + newScenario + "_")
                    copyfile(r"" + os.path.join(resultPath, file), r"" + os.path.join(resultPath, newName))

            self.LabelResults[newScenario] = self.TimeLabels
            self.IndexTime[newScenario] = self.cbTimes.currentIndex()
            self.Comments[newScenario] = self.tbComments.toPlainText().strip().strip("\n")
            self.writeScenario(newScenario, self.TimeLabels, self.Comments[newScenario])
        except Exception:
            self.iface.messageBar().pushMessage("Error", "Scenario could not be saved", level=2, duration=5)
            return
        self.Scenario = "Base"
        self.saveCurrentRender()

        self.cbScenarios.addItem(newScenario)
        # self.cbScenarios.setCurrentIndex(self.cbScenarios.count()-1)
        self.tbScenarioName.setText("")
        self.tbComments.setText("")

    def deleteScenario(self):
        self.Scenario = self.cbScenarios.currentText()

        # Process
        self.setLayersNames(True)
        # Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and
        # filer are not in use
        QGISRedUtils().runTask("delete scenario", self.removeResults, self.deleteScenarioProcess)

    def deleteScenarioProcess(self, exception=None, result=None):
        # Delete Group
        resultGroup = self.getResultGroup()
        dataGroup = resultGroup.findGroup(self.Scenario)
        if dataGroup is not None:
            resultGroup.removeChildNode(dataGroup)
        # Delete files
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        files = os.listdir(resultPath)
        for file in files:  # only names
            if self.NetworkName + "_" + self.Scenario in file:
                try:
                    os.remove(os.path.join(resultPath, file))
                except Exception:
                    pass

        # Delete from combobox
        self.cbScenarios.removeItem(self.cbScenarios.currentIndex())
        self.cbScenarios.setCurrentIndex(self.cbScenarios.count() - 1)
