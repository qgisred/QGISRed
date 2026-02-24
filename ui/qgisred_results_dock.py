# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsLayerTreeGroup
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsTextFormat
from qgis.core import QgsProperty, QgsRenderContext
from qgis.core import QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer

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

        self.lbNotAvailable.setVisible(False)
        self.displayingLinkField = ""
        self.displayingNodeField = ""

    """Methods"""

    def isCurrentProject(self):
        currentNetwork = ""
        currentDirectory = ""
        message = self.tr("The current project has been changed. Please, try again.")

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
                    self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                    self.close()
                    return False

        self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
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
            QGISRedUtils.setGroupIdentifier(group, scenario)
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
            QGISRedUtils.setGroupIdentifier(resultGroup, "Results")
        resultGroup.setItemVisibilityChecked(True)
        return resultGroup

    """UI Elements"""

    def setSelectedItemInLinkNodeComboboxes(self, nameLayer):
        if nameLayer == "Link_All":
            self.cbLinks.setCurrentIndex(1)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Node_All":
            self.cbNodes.setCurrentIndex(1)
        if nameLayer == "Link_Flow":
            self.cbLinks.setCurrentIndex(1)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_Velocity":
            self.cbLinks.setCurrentIndex(2)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_HeadLoss":
            self.cbLinks.setCurrentIndex(3)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_UnitHeadLoss":
            self.cbLinks.setCurrentIndex(4)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_Status":
            self.cbLinks.setCurrentIndex(5)
            self.cbFlowDirections.setVisible(True)
        if nameLayer == "Link_Quality":
            self.cbLinks.setCurrentIndex(6)
            self.cbFlowDirections.setVisible(True)
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

        for nameLayer in self.LabelsToOpRe:
            layerResult = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openLayerPath = self.getLayerPath(layer)
                if openLayerPath == layerResult:
                    if "Link" in nameLayer:
                        self.cbLinks.setCurrentIndex(1) # Default to first result
                        self.cbFlowDirections.setVisible(True)
                    else:
                        self.cbNodes.setCurrentIndex(1) # Default to first result
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
            self.iface.messageBar().pushMessage(self.tr("Validations"), self.tr("No variable results selected"), level=1)
            return False
        return True

    def setLayersNames(self, allLayers=False):
        self.LabelsToOpRe = []
        if self.cbLinks.currentIndex() != 0 or allLayers:
            self.LabelsToOpRe.append("Link_All")
        if self.cbNodes.currentIndex() != 0 or allLayers:
            self.LabelsToOpRe.append("Node_All")

    def setLinksLayersNames(self):
        self.LabelsToOpRe = ["Link_All"]

    def setNodesLayersNames(self):
        self.LabelsToOpRe = ["Node_All"]

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
                    # Use the field that IS currently displayed on the layer
                    var_key = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
                    
                    if not var_key:
                        continue
                        
                    storage_key = openedLayerPath + "|" + var_key
                    renderer = layer.renderer()
                    if renderer.type() == "graduatedSymbol":
                        dictSce[storage_key] = renderer.ranges()
                    else:
                        dictSce[storage_key] = renderer.rootRule().clone()
        self.Renders[self.Scenario] = dictSce

    def paintIntervalTimeResults(self, columnNumber, setRender=False):
        if not self.isCurrentProject():
            return

        self.Scenario = self.cbScenarios.currentText()
        resultPath = os.path.join(self.ProjectDirectory, "Results")
        layers = self.getLayers()
        
        time_text = self.cbTimes.currentText()
        self.lbTime.setText(time_text)
        
        for nameLayer in self.LabelsToOpRe: 
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in layers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    # Apply filter by Time
                    layer.setSubsetString("Time = '" + time_text + "'")
                    
                    field = ""
                    disp_name = ""
                    var_translated = ""
                    if "Link" in nameLayer:
                        idx = self.cbLinks.currentIndex()
                        if idx > 0:
                            columnNumber = [0, 3, 4, 5, 6, 7, 9][idx]
                            field = layer.fields().at(columnNumber).name()
                            var_translated = self.cbLinks.currentText()
                            disp_name = var_translated + " " + self.tr("in links")
                    else:
                        idx = self.cbNodes.currentIndex()
                        if idx > 0:
                            columnNumber = [0,5,4,3,6][idx]
                            field = layer.fields().at(columnNumber).name()
                            var_translated = self.cbNodes.currentText()
                            disp_name = var_translated + " " + self.tr("in nodes")
                    
                    if field:
                        self.setGraduadedPalette(layer, field, setRender, nameLayer)
                        if "Link" in nameLayer: self.displayingLinkField = field
                        else: self.displayingNodeField = field

                        if disp_name:
                            layer.setName(disp_name)
                        
                        tip = var_translated + ': [% "' + field + '" %]'
                        layer.setMapTipTemplate(tip)
                        self.setLayerLabels(layer, field)

    def setLayerLabels(self, layer, fieldName):
        firstCondition = layer.geometryType() == 0 and self.cbNodeLabels.isChecked()
        secondCondition = layer.geometryType() == 1 and self.cbLinkLabels.isChecked()
        if firstCondition or secondCondition:
            layer_settings = QgsPalLayerSettings()
            layer_settings.formatNumbers = True 
            layer_settings.decimals = 2
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

    def setArrowsVisibility(self, symbol, layer, prop, field):
        try:
            if layer.geometryType() == 1 and self.cbFlowDirections.isChecked():
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
        except:
            self.cbFlowDirections.setChecked(False)
            self.cbFlowDirections.setEnabled(False)
            self.lbNotAvailable.setVisible(True)

    def setGraduadedPalette(self, layer, field, setRender, nameLayer):
        renderer = layer.renderer()
        prop = QgsProperty()
        rawField = field  # column name
        if rawField == "UnitHeadLo":
            rawField = field + "ss"
        if field == "Flow":
            field = "abs(" + field + ")"
        
        is_status = (rawField == "Status")
        hasRender = False
        ranges = None
        
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        
        if setRender:  # Just opened a layer or changed variable
            dictRend = self.Renders.get(self.Scenario)
            layerPath = self.getLayerPath(layer)
            storage_key = layerPath + "|" + rawField
            
            if dictRend is None:
                dictRend = self.Renders.get("Base")
                if dictRend is not None:
                    base_storage_key = layerPath.replace("_" + self.Scenario + "_", "_Base_") + "|" + rawField
                    ranges = dictRend.get(base_storage_key)
                    if ranges is not None:
                        hasRender = True
            else:
                ranges = dictRend.get(storage_key)
                if ranges is not None:
                    hasRender = True
                else:
                    dictRendBase = self.Renders.get("Base")
                    if dictRendBase is not None:
                        base_storage_key = layerPath.replace("_" + self.Scenario + "_", "_Base_") + "|" + rawField
                        ranges = dictRendBase.get(base_storage_key)
                        if ranges is not None:
                            hasRender = True
        # Ensure correct renderer type
        if is_status:
            # Check if we need to load default QML
            if not hasRender and not isinstance(renderer, QgsRuleBasedRenderer):
                qmlName = nameLayer.split("_")[0] + "_" + rawField 
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()
            
            if hasRender and isinstance(ranges, QgsRuleBasedRenderer.Rule):
                renderer = QgsRuleBasedRenderer(ranges.clone())
            
            # Update specific rules filter to match our field name "Status"
            # from the style are applied to our actual "Status" column.
            if isinstance(renderer, QgsRuleBasedRenderer):
                try:
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
                except:
                    pass
        else:
            # Check if we need to load default QML
            # We load it if there's no saved render AND (it's not graduated OR it's the wrong variable)
            wrong_variable = isinstance(renderer, QgsGraduatedSymbolRenderer) and renderer.classAttribute() != field
            if not hasRender and (not isinstance(renderer, QgsGraduatedSymbolRenderer) or len(renderer.ranges()) == 0 or wrong_variable):
                qmlName = nameLayer.split("_")[0] + "_" + rawField 
                utils.setResultStyle(layer, qmlName)
                renderer = layer.renderer()
                
            if hasRender and isinstance(ranges, list):
                renderer = QgsGraduatedSymbolRenderer(field, ranges)
            
            if isinstance(renderer, QgsGraduatedSymbolRenderer):
                renderer.setClassAttribute(field)

        # Update arrow visibility
        try:
            # Arrows always use the Flow field (index 3 in layer)
            flow_field = layer.fields().at(3).name() 
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, prop, flow_field)
        except:
            pass

        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def setFilterExpression(self, root_rule, index, field, expression):
        rule = root_rule.children()[index]
        rule.setFilterExpression('"' + field + '"' + expression)

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
        if not self.validationsOpenResult():
            return
        self.cbFlowDirections.setVisible(self.cbLinks.currentIndex() != 0)
        self.lbNotAvailable.setVisible(False)

        self.setLinksLayersNames()
        self.saveCurrentRender()
        
        if self.cbLinks.currentIndex() == 0:
            self.removeResults(None)
        else:
            # If the layer is already open, just paint. If not, open and paint.
            resultPath = os.path.join(self.ProjectDirectory, "Results")
            # LabelsToOpRe is ["Link_All"] here
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_Link_All.shp")
            
            is_open = False
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    is_open = True
                    break
            
            if is_open:
                self.paintIntervalTimeResults(self.cbTimes.currentIndex(), True)
            else:
                self.openResult()

    def nodesChanged(self):
        if self.Computing:
            return
        if not self.validationsOpenResult():
            return
        
        self.setNodesLayersNames()
        self.saveCurrentRender()
        
        if self.cbNodes.currentIndex() == 0:
            self.removeResults(None)
        else:
            resultPath = os.path.join(self.ProjectDirectory, "Results")
            # LabelsToOpRe is ["Node_All"] here
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_Node_All.shp")
            
            is_open = False
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    is_open = True
                    break
            
            if is_open:
                self.paintIntervalTimeResults(self.cbTimes.currentIndex(), True)
            else:
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
                        idx = self.cbNodes.currentIndex()
                        if idx > 0:
                            field = layer.fields().at(2 + idx).name()
                            self.setLayerLabels(layer, field)
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
                        idx = self.cbLinks.currentIndex()
                        if idx > 0:
                            field = layer.fields().at(2 + idx).name()
                            self.setLayerLabels(layer, field)
                    else:
                        layer.setLabelsEnabled(False)
                        layer.triggerRepaint()

    def flowDirectionsClicked(self):
        linkIndex = self.cbLinks.currentIndex()
        if linkIndex != 0:
            if not self.validationsOpenResult(False):
                return
            
            self.setLinksLayersNames() # LabelsToOpRe = ["Link_All"]
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No scenario results are available"), level=1, duration=5)
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
            self.cbTimes.addItem(self.tr("Permanent"))
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No scenario results are available"), level=1, duration=5)
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
            # Hide all sibling groups except Results
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is not None:
                for child in netGroup.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        groupId = child.customProperty("qgisred_identifier")
                        if groupId != "qgisred_results" and child.name() != "Results":
                            child.setItemVisibilityChecked(False)
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
            self.TimeLabels.append(self.tr("Permanent"))
            self.cbTimes.addItem(self.tr("Permanent"))
        else:
            for item in mylist:
                self.TimeLabels.append(item)
                self.cbTimes.addItem(item)
        self.LabelResults["Base"] = self.TimeLabels
        self.IndexTime["Base"] = 0
        self.cbTimes.setCurrentIndex(0)
        self.timeSlider.setValue(0)
        self.timeSlider.setMaximum(len(self.TimeLabels) - 1)
        self.lbTime.setText(self.TimeLabels[0])

        # Comments
        self.Comments["Base"] = self.tr("Last results computed")
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
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("No scenario results are available"), level=1, duration=5)
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
            pass  # self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

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
            pass  # self.iface.messageBar().pushMessage(self.tr("Information"), self.tr("Process successfully completed"), level=3, duration=5)
        elif resMessage == "False":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Some issues occurred in the process"), level=1, duration=5)
        else:
            self.iface.messageBar().pushMessage(self.tr("Error"), resMessage, level=2, duration=5)

    def saveScenario(self):
        if not self.isCurrentProject():
            return False
        # Validations
        isBaseScenario = self.cbScenarios.currentText() == "Base"
        if not isBaseScenario:
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Only 'Base' scenario could be saved"), level=1, duration=5)
            return
        newScenario = self.tbScenarioName.text().strip()
        if newScenario == "":
            self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Scenario name is not valid"), level=1, duration=5)
            return
        for i in range(self.cbScenarios.count()):
            if self.cbScenarios.itemText(i).lower() == newScenario.lower():
                self.iface.messageBar().pushMessage(self.tr("Warning"), self.tr("Scenario name is already used"), level=1, duration=5)
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
            self.iface.messageBar().pushMessage(self.tr("Error"), self.tr("Scenario could not be saved"), level=2, duration=5)
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