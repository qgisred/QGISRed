# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QDockWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from qgis.PyQt import uic
from qgis.core import QgsProject, QgsLayerTreeGroup, QgsField
from PyQt5.QtCore import Qt, QVariant
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsTextFormat
from qgis.core import QgsProperty, QgsRenderContext
from qgis.core import QgsGraduatedSymbolRenderer, QgsRuleBasedRenderer

from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.qgisred_results import getOut_TimeNodesProperties, getOut_TimeLinksProperties


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

    def getUniformedPath(self, path):
        return QGISRedUtils().getUniformedPath(path)

    def getLayerPath(self, layer):
        return QGISRedUtils().getLayerPath(layer)

    def generatePath(self, folder, fileName):
        return QGISRedUtils().generatePath(folder, fileName)

    def getResultsPath(self):
        return os.path.join(self.ProjectDirectory, "Results")

    """Layers and Groups"""

    def getLayers(self):
        return QGISRedUtils().getLayers()

    def openLayerResults(self, scenario):
        resultPath = self.getResultsPath()
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + scenario, self.iface)
        resultGroup = self.getResultGroup()
        group = resultGroup.findGroup(scenario)
        if group is None:
            group = resultGroup.addGroup(scenario)
            QGISRedUtils.setGroupIdentifier(group, scenario)
        
        openedLayersPaths = [self.getLayerPath(l) for l in self.getLayers()]
        
        for file in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + scenario + "_" + file + ".shp")
            # Ensure Shapefile exists
            if not os.path.exists(resultLayerPath):
                self.iface.messageBar().pushMessage(self.tr("Results"), self.tr("{} results not found").format(self.tr(file)), level=1)
                continue
           
            # Open layer if not already open
            if resultLayerPath not in openedLayersPaths:
                utils.openLayer(group, file, results=True)

    def removeResults(self, task):
        resultPath = self.getResultsPath()
        utils = QGISRedUtils(resultPath, self.NetworkName + "_" + self.Scenario, self.iface)
        utils.removeLayers(["Node", "Link"])
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
    def restoreElementsCb(self):
        self.Scenario = self.cbScenarios.currentText()
        resultPath = self.getResultsPath()
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

    def setVariables(self, all_vars=False):
        self.Variables = ""
        if self.cbLinks.currentIndex() == 1 or all_vars:
            self.Variables = self.Variables + "Flow_Link;"
        if self.cbLinks.currentIndex() == 2 or all_vars:
            self.Variables = self.Variables + "Velocity_Link;"
        if self.cbLinks.currentIndex() == 3 or all_vars:
            self.Variables = self.Variables + "HeadLoss_Link;"
        if self.cbLinks.currentIndex() == 4 or all_vars:
            self.Variables = self.Variables + "UnitHeadLoss_Link;"
        if self.cbLinks.currentIndex() == 5 or all_vars:
            self.Variables = self.Variables + "Status_Link;"
        if self.cbLinks.currentIndex() == 6 or all_vars:
            self.Variables = self.Variables + "Quality_Link;"
        if self.cbNodes.currentIndex() == 1 or all_vars:
            self.Variables = self.Variables + "Pressure_Node;"
        if self.cbNodes.currentIndex() == 2 or all_vars:
            self.Variables = self.Variables + "Head_Node;"
        if self.cbNodes.currentIndex() == 3 or all_vars:
            self.Variables = self.Variables + "Demand_Node;"
        if self.cbNodes.currentIndex() == 4 or all_vars:
            self.Variables = self.Variables + "Quality_Node;"

        if self.Variables == "" and not all_vars:
            self.iface.messageBar().pushMessage(self.tr("Validations"), self.tr("No variable results selected"), level=1)
            return False
        return True

    def setLayersNames(self, allLayers=False):
        self.LabelsToOpRe = []
        if self.cbLinks.currentIndex() != 0 or allLayers:
            self.LabelsToOpRe.append("Link_All")
        if self.cbNodes.currentIndex() != 0 or allLayers:
            self.LabelsToOpRe.append("Node_All")

    """Symbology"""

    def saveCurrentRender(self):
        openedLayers = self.getLayers()
        resultPath = self.getResultsPath()
        dictSce = self.Renders.get(self.Scenario)
        if dictSce is None:
            dictSce = {}

        resultLayersName = ["Node", "Link"]   
        for nameLayer in resultLayersName:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            for layer in openedLayers:
                openedLayerPath = self.getLayerPath(layer)
                if openedLayerPath == resultLayerPath:
                    # Use the field that IS currently displayed on the layer
                    var_key = self.displayingLinkField if "Link" in nameLayer else self.displayingNodeField
                    
                    if not var_key:
                        continue
                    
                    if var_key == "UnitHeadLo":
                        var_key = "UnitHeadLoss"
                        
                    storage_key = openedLayerPath + "|" + var_key
                    renderer = layer.renderer()
                    try:
                        if renderer.type() == "graduatedSymbol":
                            dictSce[storage_key] = renderer.ranges()
                        else:
                            dictSce[storage_key] = renderer.rootRule().clone()
                    except:
                        message = self.tr("Some issue occurred in the process of saving the style of the layer").format(self.tr(layerName))
                        self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                    
        self.Renders[self.Scenario] = dictSce

    def paintIntervalTimeResults(self, setRender=False):    
        time_text = self.cbTimes.currentText()
        self.lbTime.setText(time_text)
        
        resultPath = self.getResultsPath()
        for nameLayer in ["Node", "Link"]: 
            layer_to_paint = None
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            # Check if layer is already open
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    layer_to_paint = layer
                    break

            if layer_to_paint:                   
                field = ""
                disp_name = ""
                var_translated = ""
                if "Link" in nameLayer:
                    idx = self.cbLinks.currentIndex()
                    if idx > 0:
                        columnIndex = idx + 2
                        field = layer_to_paint.fields().at(columnIndex).name()
                        var_translated = self.cbLinks.currentText()
                        disp_name = self.tr("Link {}").format(var_translated)
                else:
                    idx = self.cbNodes.currentIndex()
                    if idx > 0:
                        columnIndex = idx + 2
                        field = layer_to_paint.fields().at(columnIndex).name()
                        var_translated = self.cbNodes.currentText()
                        disp_name = self.tr("Node {}").format(var_translated)
                
                if field:
                    self.setGraduadedPalette(layer_to_paint, field, setRender, nameLayer)
                    
                    # Store current displayed variable
                    if "Link" in nameLayer: self.displayingLinkField = field
                    else: self.displayingNodeField = field

                    # Set layer name in legend
                    layer_to_paint.setName(disp_name)
                    
                    # Configure map tip
                    tip = var_translated + ': [% "' + field + '" %]'
                    layer_to_paint.setMapTipTemplate(tip)
                    
                    # Configure layer labels
                    self.setLayerLabels(layer_to_paint, field)

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

            if fieldName == "Flow":
                layer_settings.fieldName = 'abs("Flow")'
                layer_settings.isExpression = True
            else:
                layer_settings.fieldName = fieldName
                layer_settings.isExpression = False

            layer_settings.placement = QgsPalLayerSettings.Line
            layer_settings.enabled = True
            labels = QgsVectorLayerSimpleLabeling(layer_settings)
            layer.setLabeling(labels)
            layer.setLabelsEnabled(True)
            layer.triggerRepaint()

    def setArrowsVisibility(self, symbol, layer, field):
        prop = QgsProperty()
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
                try:
                    renderer = QgsRuleBasedRenderer(ranges.clone())
                except:
                    message = self.tr("Some issue occurred in the process of applying the style to the layer").format(self.tr(layerName))
                    self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                    return
            
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
            # Arrows always use the Flow field (index 2 in layer)
            flow_field = layer.fields().at(2).name() 
            symbols = renderer.symbols(QgsRenderContext())
            for symbol in symbols:
                if symbol.type() == 1:  # line
                    self.setArrowsVisibility(symbol, layer, flow_field)
        except:
            pass

        layer.setRenderer(renderer)
        layer.triggerRepaint()

    def setFilterExpression(self, root_rule, index, field, expression):
        rule = root_rule.children()[index]
        rule.setFilterExpression('"' + field + '"' + expression)

    """Scenario"""

    def writeScenario(self, scenario, labels, comments):
        filePath = os.path.join(self.getResultsPath(), self.NetworkName + "_" + scenario + ".sce")
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
        resultPath = self.getResultsPath()
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

        self.lbNotAvailable.setVisible(False)

        self.saveCurrentRender()
        self.ensureResultsLayersAreOpen()
        self.paintIntervalTimeResults(True)

    def nodesChanged(self):
        if self.Computing:
            return
        if not self.validationsOpenResult():
            return
        
        self.saveCurrentRender()
        self.ensureResultsLayersAreOpen()
        self.paintIntervalTimeResults(True)

    def nodeLabelsClicked(self):
        self.updateLabels("Node")

    def linkLabelsClicked(self):
        self.updateLabels("Link")

    def flowDirectionsClicked(self):
        if not self.validationsOpenResult():
            return
        
        self.ensureResultsLayersAreOpen()

        resultLayerPath = self.generatePath(self.getResultsPath(), self.NetworkName + "_" + self.Scenario + "_Link.shp")
        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
                layer_to_paint = layer
                break
        if layer_to_paint:
            renderer = layer_to_paint.renderer()
            symbols = renderer.symbols(QgsRenderContext())
            flow_field = layer_to_paint.fields().at(2).name()  # Flow field
            for symbol in symbols:
                self.setArrowsVisibility(symbol, layer_to_paint, flow_field)
            
            layer_to_paint.setRenderer(renderer)
            layer_to_paint.triggerRepaint()

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
        
        if not self.validationsOpenResult():
            return

        self.ensureResultsLayersAreOpen()

        value = self.cbTimes.currentIndex()
        self.timeSlider.setValue(value)
        self.IndexTime[self.cbScenarios.currentText()] = value

        self.completeResultLayers()

        self.paintIntervalTimeResults(False)

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
    def updateLabels(self, layer_type):
        if not self.validationsOpenResult():
            return
        
        self.ensureResultsLayersAreOpen()

        resultPath = self.getResultsPath()
        resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layer_type + ".shp")
        
        checkbox = self.cbNodeLabels if layer_type == "Node" else self.cbLinkLabels
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks

        for layer in self.getLayers():
            if self.getLayerPath(layer) == resultLayerPath:
                if checkbox.isChecked():
                    idx = combobox.currentIndex()
                    if idx > 0:
                        field = layer.fields().at(idx + 2).name()
                        self.setLayerLabels(layer, field)
                else:
                    layer.setLabelsEnabled(False)
                    layer.triggerRepaint()

    def validationsOpenResult(self):
        if not self.isCurrentProject():
            return False

        self.Scenario = self.cbScenarios.currentText()
        resultsPath = self.getResultsPath()
        resultLayersName = ["Node", "Link"]
        for layerName in resultLayersName:
            filename = self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp"
            resultPath = os.path.join(resultsPath, filename)
            if not os.path.exists(resultPath):
                message = self.tr("No {} results are available").format(self.tr(layerName))
                self.iface.messageBar().pushMessage(self.tr("Warning"), message, level=1, duration=5)
                return False

        return True

    def ensureResultsLayersAreOpen(self):
        # Ensure result layers are opened
        if not self.isCurrentProject():
            return

        self.Scenario = self.cbScenarios.currentText()
        resultPath = self.getResultsPath()     
        for nameLayer in ["Node", "Link"]: 
            layer_to_paint = None
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp")
            
            # Check if layer is already open
            for layer in self.getLayers():
                if self.getLayerPath(layer) == resultLayerPath:
                    layer_to_paint = layer
                    break
            
            # If the layer is not open, open it!
            if layer_to_paint is None:
                self.openLayerResults(self.Scenario)

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
        if self.cbLinks.currentIndex() == 0:
            self.cbLinks.setCurrentIndex(1)
        if self.cbNodes.currentIndex() == 0:
            self.cbNodes.setCurrentIndex(1)

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
        if not self.validationsOpenResult():
            return

        if not self.setVariables(True):
            return

        # Task is necessary because after remove layers, DBF files are in use. With the task,
        # the remove process finishs and filer are not in use
        QGISRedUtils().runTask("update all results", self.removeResults, self.openAllResultsProcess)

    def openAllResultsProcess(self, exception=None, result=None):
        # Ensure result layers are opened
        self.ensureResultsLayersAreOpen()

        # Complete dbf table with results
        self.completeResultLayers()
        
        self.paintIntervalTimeResults(True)

        # Activate map tips
        self.iface.actionMapTips().setChecked(True)

    def completeResultLayers(self):
        """Populates the attribute tables of the result layers with data from the .out file."""
        if not self.isCurrentProject():
            return

        # 1. Parse time strings like "00d 01:23:45" to seconds
        time_text = self.cbTimes.currentText()
        if time_text == self.tr("Permanent"):
            time_seconds = 0
        else:
            try:
                # Format: "00d 00:00:00"
                parts = time_text.split(" ")
                days = int(parts[0].replace("d", ""))
                hms = parts[1].split(":")
                time_seconds = days * 86400 + int(hms[0]) * 3600 + int(hms[1]) * 60 + int(hms[2])
            except Exception:
                time_seconds = 0

        self.Scenario = self.cbScenarios.currentText()
        resultPath = self.getResultsPath()
        binary_path = os.path.join(resultPath, self.NetworkName + "_" + self.Scenario + ".out")
        if not os.path.exists(binary_path):
            return

        openedLayers = self.getLayers()
        for layerName in ["Node", "Link"]:
            resultLayerPath = self.generatePath(resultPath, self.NetworkName + "_" + self.Scenario + "_" + layerName + ".shp")
            target_layer = None
            for layer in openedLayers:
                if self.getLayerPath(layer) == resultLayerPath:
                    target_layer = layer
                    break

            if not target_layer:
                continue

            # Fetch results from binary file
            if layerName == "Node":
                results = getOut_TimeNodesProperties(binary_path, time_seconds)
            else:
                results = getOut_TimeLinksProperties(binary_path, time_seconds)
            
            if not results:
                continue

            # 2. Check and add missing fields
            first_id = next(iter(results))
            variables = list(v[:10] for v in results[first_id].keys())
            existing_fields = target_layer.fields().names()
            new_fields = []
            
            # Ensure "Time" field exists
            if "Time" not in existing_fields:
                new_fields.append(QgsField("Time", QVariant.String, "", 15))

            for var in variables:
                if var not in existing_fields:
                    new_fields.append(QgsField(var, QVariant.Double))

            if new_fields:
                target_layer.dataProvider().addAttributes(new_fields)
                target_layer.updateFields()

            # 3. Update features
            # Get field indices
            field_indices = {}
            for var in variables:
                field_indices[var] = target_layer.fields().indexOf(var)
            
            time_field_idx = target_layer.fields().indexOf("Time")
            
            # Find Id field index (assuming it's called "Id")
            id_field_idx = target_layer.fields().indexOf("Id")
            if id_field_idx == -1:
                # fallback to first field if "Id" not found
                id_field_idx = 0

            attribute_updates = {}
            for feature in target_layer.getFeatures():
                elem_id = str(feature.attributes()[id_field_idx])
                if elem_id in results:
                    elem_results = results[elem_id]
                    updates = {}
                    if time_field_idx != -1:
                        updates[time_field_idx] = time_text
                    
                    for var, val in elem_results.items():
                        updates[field_indices[var[:10]]] = val
                    attribute_updates[feature.id()] = updates

            # Apply updates via provider (more efficient for batch)
            if attribute_updates:
                target_layer.dataProvider().changeAttributeValues(attribute_updates)
                target_layer.triggerRepaint()

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
        resultPath = self.getResultsPath()
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
        resultPath = self.getResultsPath()
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