# -*- coding: utf-8 -*-
from qgis.gui import QgsMessageBar
from qgis.core import QgsVectorLayer, QgsProject
from qgis.PyQt import QtGui, uic

try: #QGis 3.x
    from qgis.core import Qgis, QgsTask, QgsApplication
    from PyQt5.QtWidgets import QDockWidget, QApplication
    from PyQt5.QtCore import Qt
    from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, QgsLineSymbol, QgsProperty, QgsRenderContext
    from qgis.core import QgsSimpleLineSymbolLayer, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
    from qgis.core import QgsGraduatedSymbolRenderer, QgsGradientColorRamp as QgsVectorGradientColorRamp
    from ..qgisred_utils import QGISRedUtils
except: #QGis 2.x
    from qgis.core import QGis as Qgis
    from PyQt4.QtGui import QDockWidget, QApplication
    from PyQt4.QtCore import Qt
    from qgis.core import QgsSvgMarkerSymbolLayerV2 as QgsSvgMarkerSymbolLayer, QgsSymbolV2 as QgsSymbol
    from qgis.core import QgsSingleSymbolRendererV2 as QgsSingleSymbolRenderer, QgsLineSymbolV2 as QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayerV2 as QgsSimpleLineSymbolLayer, QgsMarkerSymbolV2 as QgsMarkerSymbol
    from qgis.core import QgsMarkerLineSymbolLayerV2 as QgsMarkerLineSymbolLayer 
    from qgis.core import QgsSimpleMarkerSymbolLayerV2 as QgsSimpleMarkerSymbolLayer, QgsDataDefined
    from qgis.core import QgsGraduatedSymbolRendererV2 as QgsGraduatedSymbolRenderer, QgsVectorGradientColorRampV2 as QgsVectorGradientColorRamp
    from ..qgisred_utils import QGISRedUtils

import os
from ctypes import*
import tempfile

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'qgisred_results_dock.ui'))


class QGISRedResultsDock(QDockWidget, FORM_CLASS):
    #Common variables
    iface = None
    NetworkName = ""
    ProjectDirectory = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs"]
    Results= {}
    Variables=""
    Computing=False
    Scenario=""
    TimeLabels=[]
    LabelsToOpRe=[]
    def __init__(self, iface):
        """Constructor."""
        super(QGISRedResultsDock, self).__init__(iface.mainWindow())
        self.iface = iface
        self.setupUi(self)
        self.btCompute.clicked.connect(self.compute)
        self.hsTimes.valueChanged.connect(self.timeChanged)
        self.cbFlow.clicked.connect(self.flowClicked)
        self.cbVelocity.clicked.connect(self.velocityClicked)
        self.cbHeadLoss.clicked.connect(self.headLossClicked)
        self.cbPressure.clicked.connect(self.pressureClicked)
        self.cbHead.clicked.connect(self.headClicked)
        self.cbDemand.clicked.connect(self.demandClicked)
        self.cbQualityLink.clicked.connect(self.qualityLinkClicked)
        self.cbQualityNode.clicked.connect(self.qualityNodeClicked)
        self.cbFlowDirections.clicked.connect(self.flowDirectionsClicked)

    def config(self, direct, netw):
        if not (self.NetworkName == netw and self.ProjectDirectory == direct):
            self.Results={}
            self.tbScenario.setText("Base")
            self.lbTime.setVisible(False)
            self.hsTimes.setVisible(False)
        self.NetworkName = netw
        self.ProjectDirectory = direct
        self.tbNetworkName.setText(netw)
        self.tbProjectDirectory.setText(direct)
        self.tbProjectDirectory.setCursorPosition(0)
        self.restoreElementsCb()
        self.setLayersNames()
        if len(self.LabelsToOpRe)==0:
            self.cbFlow.setChecked(True)
            self.cbPressure.setChecked(True)

    def isCurrentProject(self):
        currentNetwork =""
        currentDirectory = ""
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            layerUri= layer.dataProvider().dataSourceUri().split("|")[0]
            self.CRS = layer.crs()
            for layerName in self.ownMainLayers:
                if "_" + layerName in layerUri:
                    currentDirectory = os.path.dirname(layerUri)
                    vectName = os.path.splitext(os.path.basename(layerUri))[0].split("_")
                    name =""
                    for part in vectName:
                        if part in self.ownMainLayers:
                            break
                        name = name + part + "_"
                    name = name.strip("_")
                    currentNetwork = name
                    if self.NetworkName == currentNetwork and self.ProjectDirectory == currentDirectory:
                        return True
                    else:
                        self.iface.messageBar().pushMessage("Warning", "The current project has been changed. Please, try again.", level=1, duration=10)
                        self.close()
                        return False

        self.iface.messageBar().pushMessage("Warning", "The current project has been changed. Please, try again.", level=1, duration=10)
        self.close()
        return False

    def openLayerResults(self, scenario):
        resultPath= os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(resultPath, self.NetworkName +"_" + scenario, self.iface)
        group = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName +" " + scenario + " Results")
        if group is None:
            root = QgsProject.instance().layerTreeRoot()
            group = root.insertGroup(0,self.NetworkName +" " + scenario + " Results")
        for file in self.LabelsToOpRe:
            utils.openLayer(self.CRS, group, file, results=True)

    def removeResults(self, task, wait_time):
        resultPath= os.path.join(self.ProjectDirectory, "Results")
        utils = QGISRedUtils(resultPath, self.NetworkName +"_" + self.Scenario, self.iface)
        utils.removeLayers(self.LabelsToOpRe)
        raise Exception('')

    def setVariablesTimes(self):
        self.Variables=""
        if self.cbFlow.isChecked():
            self.Variables=self.Variables + "Flow_Link;"
        if self.cbVelocity.isChecked():
            self.Variables=self.Variables + "Velocity_Link;"
        if self.cbHeadLoss.isChecked():
            self.Variables=self.Variables + "HeadLoss_Link;"
        if self.cbQualityLink.isChecked():
            self.Variables=self.Variables + "Quality_Link;"
        if self.cbPressure.isChecked():
            self.Variables=self.Variables + "Pressure_Node;"
        if self.cbHead.isChecked():
            self.Variables=self.Variables + "Head_Node;"
        if self.cbDemand.isChecked():
            self.Variables=self.Variables + "Demand_Node;"
        if self.cbQualityNode.isChecked():
            self.Variables=self.Variables + "Quality_Node;"
        if self.Variables=="":
            self.iface.messageBar().pushMessage("Validations", "No variable results selected", level=1)
            return False
        return True

    def setLayersNames(self, all=False):
        self.LabelsToOpRe = []
        if self.cbFlow.isChecked() or all:
            self.LabelsToOpRe.append("Link_" + "Flow")
        if self.cbVelocity.isChecked() or all:
            self.LabelsToOpRe.append("Link_" + "Velocity")
        if self.cbHeadLoss.isChecked() or all:
            self.LabelsToOpRe.append("Link_" + "HeadLoss")
        if self.cbQualityLink.isChecked() or all:
            self.LabelsToOpRe.append("Link_" + "Quaility")
        if self.cbPressure.isChecked() or all:
            self.LabelsToOpRe.append("Node_" + "Pressure")
        if self.cbHead.isChecked() or all:
            self.LabelsToOpRe.append("Node_" + "Head")
        if self.cbDemand.isChecked() or all:
            self.LabelsToOpRe.append("Node_" + "Demand")
        if self.cbQualityNode.isChecked() or all:
            self.LabelsToOpRe.append("Node_" + "Quaility")

    def insert(self, source_str, insert_str, pos):
        return source_str[:pos]+insert_str+source_str[pos:]

    def restoreElementsCb(self):
        self.Secnario = self.tbScenario.text()
        
        resultPath= os.path.join(self.ProjectDirectory, "Results")
        self.setLayersNames(True)
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()

        self.cbFlow.setChecked(False)
        self.cbVelocity.setChecked(False)
        self.cbHeadLoss.setChecked(False)
        self.cbPressure.setChecked(False)
        self.cbHead.setChecked(False)
        self.cbDemand.setChecked(False)
        self.cbQualityLink.setChecked(False)
        self.cbQualityNode.setChecked(False)
        for nameLayer in self.LabelsToOpRe:
            for layer in layers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0])== os.path.join(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp"):
                    if nameLayer == "Link_Flow":
                        self.cbFlow.setChecked(True)
                    if nameLayer == "Link_Velocity":
                        self.cbVelocity.setChecked(True)
                    if nameLayer == "Link_HeadLoss":
                        self.cbHeadLoss.setChecked(True)
                    if nameLayer == "Link_Quaility":
                        self.cbQualityLink.setChecked(True)
                    if nameLayer == "Node_Pressure":
                        self.cbPressure.setChecked(True)
                    if nameLayer == "Node_Head":
                        self.cbHead.setChecked(True)
                    if nameLayer == "Node_Demand":
                        self.cbDemand.setChecked(True)
                    if nameLayer == "Node_Quaility":
                        self.cbQualityNode.setChecked(True)

    def paintIntervalTimeResults(self, columnNumber, setRender = False):
        if not self.isCurrentProject():
            return
        
        self.Scenario = self.tbScenario.text()
        resultPath= os.path.join(self.ProjectDirectory, "Results")
        
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        
        self.lbTime.setText(self.TimeLabels[columnNumber])
        for nameLayer in self.LabelsToOpRe:
            for layer in layers:
                if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(resultPath, self.NetworkName + "_" + self.Scenario + "_" + nameLayer + ".shp").replace("/","\\"):
                    field_names = [field.name() for field in layer.fields()]
                    field = field_names[columnNumber+2]
                    self.setGraduadedPalette(layer, field, setRender)
                    layer.setName(nameLayer + " " + self.TimeLabels[columnNumber])
                    if str(Qgis.QGIS_VERSION).startswith('3'): #QGis 3.x
                        layer.setMapTipTemplate("<br>[% \"T" + str(columnNumber) + "\" %]")
                    else:
                        layer.setDisplayField('T' + str(columnNumber))

    def setGraduadedPalette(self, layer, field, setRender):
        try: # QGis 3
            version = 3
            renderer = layer.renderer()
            symbol = renderer.symbol() #SimpleSymbol
        except: # QGis 2
            try: # QGis 3
                symbol = renderer.symbols(QgsRenderContext()) #sourceSymbol() #GraduatedSymbol
            except:
                version = 2
                renderer = layer.rendererV2()
                symbol = renderer.symbols()
        if version ==2:
            for sym in symbol:
                if sym.type()==1: #line
                    if "Flow" in layer.name() and self.cbFlowDirections.isChecked():
                        ss = sym.symbolLayer(3) #arrow positive flow
                        ss.subSymbol().setDataDefinedSize(QgsDataDefined("if(Type='PIPE', if(" + field + ">0,4,0),0)"))
                        ss = sym.symbolLayer(4) #arrow negative flow
                        ss.subSymbol().setDataDefinedSize(QgsDataDefined("if(Type='PIPE', if(" + field + "<0,4,0),0)"))
                    else:
                        sym.symbolLayer(3).subSymbol().setDataDefinedSize(QgsDataDefined('0'))
                        sym.symbolLayer(4).subSymbol().setDataDefinedSize(QgsDataDefined('0'))
                else: #point
                    sym.symbolLayer(0).setDataDefinedProperty("size", QgsDataDefined("if(Type ='TANK', 7,0)"))
                    sym.symbolLayer(1).setDataDefinedProperty("size", QgsDataDefined("if(Type ='RESERVOIR', 7,0)"))
                    sym.symbolLayer(2).setDataDefinedProperty("size", QgsDataDefined("if(Type ='RESERVOIR' or Type='TANK', 0,2)"))
            symbol = symbol[0]
        else: #QGis 3
            print(self.cbFlowDirections.isChecked())
            if setRender:
                prop = QgsProperty()
                if symbol.type()==1: #line
                    if "Flow" in layer.name() and self.cbFlowDirections.isChecked():
                        ss = symbol.symbolLayer(3) #arrow positive flow
                        prop.setExpressionString("if(Type='PIPE', if(" + field + ">0,4,0),0)")
                        ss.subSymbol().setDataDefinedSize(prop)
                        ss = symbol.symbolLayer(4) #arrow negative flow
                        prop.setExpressionString("if(Type='PIPE', if(" + field + "<0,4,0),0)")
                        ss.subSymbol().setDataDefinedSize(prop)
                    else:
                        prop.setExpressionString("0")
                        symbol.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
                        symbol.symbolLayer(4).subSymbol().setDataDefinedSize(prop)
                else: #point
                    prop.setExpressionString("if(Type ='TANK', 7,0)")
                    symbol.symbolLayer(0).setDataDefinedProperty(0, prop) #0 = PropertySize
                    symbol.symbolLayer(0).setDataDefinedProperty(9, prop) #0 = PropertyWidth
                    prop.setExpressionString("if(Type ='RESERVOIR', 7,0)")
                    symbol.symbolLayer(1).setDataDefinedProperty(0, prop)
                    symbol.symbolLayer(1).setDataDefinedProperty(9, prop)
                    prop.setExpressionString("if(Type ='RESERVOIR' or Type='TANK', 0,2)")
                    symbol.symbolLayer(2).setDataDefinedProperty(0, prop)
                    symbol.symbolLayer(2).setDataDefinedProperty(9, prop)
            else:
                for sym in symbol:
                    if sym.type()==1: #line
                        prop = QgsProperty()
                        if "Flow" in layer.name() and self.cbFlowDirections.isChecked():
                            ss = sym.symbolLayer(3) #arrow positive flow
                            prop.setExpressionString("if(Type='PIPE', if(" + field + ">0,4,0),0)")
                            ss.subSymbol().setDataDefinedSize(prop)
                            ss = sym.symbolLayer(4) #arrow negative flow
                            prop.setExpressionString("if(Type='PIPE', if(" + field + "<0,4,0),0)")
                            ss.subSymbol().setDataDefinedSize(prop)
                        else:
                            prop.setExpressionString("0")
                            sym.symbolLayer(3).subSymbol().setDataDefinedSize(prop)
                            sym.symbolLayer(4).subSymbol().setDataDefinedSize(prop)
                    else: #point
                        pass
        
        if "Flow" in layer.name():
            field = "abs(" + field + ")"
        if setRender:
            mode= QgsGraduatedSymbolRenderer.EqualInterval #Quantile
            classes = 5
            colorRamp = QgsVectorGradientColorRamp.create({'color1':'0,0,255,255', 'color2':'255,0,0,255','stops':'0.25;0,255,255,255:0.50;0,255,0,255:0.75;255,255,0,255'})
            self.iface.setActiveLayer(layer)
            renderer = QgsGraduatedSymbolRenderer.createRenderer( layer, field, classes, mode, symbol, colorRamp )
            myFormat = renderer.labelFormat()
            myFormat.setPrecision(2)
            myFormat.setTrimTrailingZeroes(True)
            renderer.setLabelFormat(myFormat, True)
        else:
            renderer.setClassAttribute(field)

        try: #QGis 3.x
            layer.setRenderer(renderer)
        except: #QGis 2.x
            layer.setRendererV2(renderer)
        layer.triggerRepaint()

    """Clicked events"""
    def flowClicked(self):
        checked = self.cbFlow.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbFlow.setChecked(checked)
        self.LabelsToOpRe.append("Link_Flow")
        self.Variables="Flow_Link"
        self.openResult(self.cbFlow.isChecked())

    def velocityClicked(self):
        checked = self.cbVelocity.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbVelocity.setChecked(checked)
        self.LabelsToOpRe.append("Link_Velocity")
        self.Variables="Velocity_Link"
        self.openResult(self.cbVelocity.isChecked())

    def headLossClicked(self):
        checked = self.cbHeadLoss.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbHeadLoss.setChecked(checked)
        self.LabelsToOpRe.append("Link_HeadLoss")
        self.Variables="HeadLoss_Link"
        self.openResult(self.cbHeadLoss.isChecked())

    def qualityLinkClicked(self):
        checked = self.cbQualityLink.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbQualityLink.setChecked(checked)
        self.LabelsToOpRe.append("Link_Quality")
        self.Variables="Quality_Link"
        self.openResult(self.cbQualityLink.isChecked())

    def pressureClicked(self):
        checked = self.cbPressure.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbPressure.setChecked(checked)
        self.LabelsToOpRe.append("Node_Pressure")
        self.Variables="Pressure_Node"
        self.openResult(self.cbPressure.isChecked())

    def headClicked(self):
        checked = self.cbHead.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbHead.setChecked(checked)
        self.LabelsToOpRe.append("Node_Head")
        self.Variables="Head_Node"
        self.openResult(self.cbHead.isChecked())

    def demandClicked(self):
        checked = self.cbDemand.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbDemand.setChecked(checked)
        self.LabelsToOpRe.append("Node_Demand")
        self.Variables="Demand_Node"
        self.openResult(self.cbDemand.isChecked())

    def qualityNodeClicked(self):
        checked = self.cbQualityNode.isChecked()
        if not self.validationsOpenResult():
            return
        self.cbQualityNode.setChecked(checked)
        self.LabelsToOpRe.append("Node_Quality")
        self.Variables="Quality_Node"
        self.openResult(self.cbQualityNode.isChecked())

    def flowDirectionsClicked(self):
        if self.cbFlow.isChecked():
            checked = self.cbFlow.isChecked()
            if not self.validationsOpenResult():
                return
            self.cbFlow.setChecked(checked)
            self.LabelsToOpRe.append("Link_Flow")
            self.Variables="Flow_Link"
            value = self.hsTimes.value()
            self.paintIntervalTimeResults(value, False)

    def timeChanged(self):
        if self.Computing:
            return
        self.Secnario = self.tbScenario.text()
        resultPath = self.Results.get(self.Secnario)
        if resultPath is None:
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=10)
            return
        
        value = self.hsTimes.value()
        self.setLayersNames()
        self.paintIntervalTimeResults(value)

    """Main methods"""
    def compute(self):
        #Validations
        if not self.isCurrentProject():
            return
        
        self.Scenario = self.tbScenario.text()
        if len(self.Scenario)==0:
            self.iface.messageBar().pushMessage("Validations", "The scenario name is not valid", level=1)
            return False
        
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        elements = "Junctions;Pipes;Tanks;Reservoirs;Valves;Pumps;"
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.Compute.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Scenario.encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        elif b.startswith("Message"):
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)
        else:
            #Binary result file and Time label list
            list = b.split(';')
            self.Results[self.Scenario]= list[0]
            del list[0]
            self.TimeLabels =[]
            if len(list)==1:
                self.TimeLabels.append("Permanent")
            else:
                for item in list:
                    self.TimeLabels.append(self.insert(self.insert(item, " ", 6), " ", 3))
            self.Computing=True
            
            if len(list)==1:
                self.hsTimes.setVisible(False)
            else:
                self.hsTimes.setVisible(True)
                self.hsTimes.setMaximum(len(list)-1)
            self.hsTimes.setValue(0)
            self.lbTime.setVisible(True)
            self.lbTime.setText(self.TimeLabels[0])
            self.Computing = False
            #Open results
            self.openAllResults()

    def validationsOpenResult(self):
        if not self.isCurrentProject():
            return False
        self.Secnario = self.tbScenario.text()
        resultPath = self.Results.get(self.Secnario)
        if resultPath is None:
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=10)
            return
        
        self.restoreElementsCb()
        self.LabelsToOpRe=[]
        return True

    def openAllResults(self):
        #Validations
        if not self.isCurrentProject():
            return

        self.Secnario = self.tbScenario.text()
        resultPath = self.Results.get(self.Secnario)
        if resultPath is None:
            self.iface.messageBar().pushMessage("Warning", "No scenario results are available", level=1, duration=10)
            return

        if not self.setVariablesTimes():
            return
        
        #Process
        self.setLayersNames(True)
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            try:
                self.removeResults(None,0)
            except:
                pass
            self.openAllResultsProcess()
        else:  #QGis 3.x
            #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
            task1 = QgsTask.fromFunction(u'Remove layers', self.removeResults, on_finished=self.openAllResultsProcess, wait_time=0)
            task1.run()
            QgsApplication.taskManager().addTask(task1)

    def openAllResultsProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        resultPath = self.Results.get(self.Secnario)
        self.setLayersNames()
        
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateResults.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateResults.restype = c_char_p
        b = mydll.CreateResults(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Secnario.encode('utf-8'), resultPath.encode('utf-8'), self.Variables.encode('utf-8'), "".encode('utf-8'), "".encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Open layers
        self.openLayerResults(self.Secnario)
        value = self.hsTimes.value()
        self.paintIntervalTimeResults(value, True)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass# self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)

    def openResult(self, open):
        if not open:
            try:
                self.removeResults(None,0)
            except:
                pass
        else:
            if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
                try:
                    self.removeResults(None,0)
                except:
                    pass
                self.openResultProcess()
            else:  #QGis 3.x
                #Task is necessary because after remove layers, DBF files are in use. With the task, the remove process finishs and filer are not in use
                task1 = QgsTask.fromFunction(u'Remove layers', self.removeResults, on_finished=self.openResultProcess, wait_time=0)
                task1.run()
                QgsApplication.taskManager().addTask(task1)

    def openResultProcess(self, exception=None, result=None):
        #Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "dlls"))
        resultPath = self.Results.get(self.Secnario)
        mydll = WinDLL("GISRed.QGisPlugins.dll")
        mydll.CreateResults.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateResults.restype = c_char_p
        b = mydll.CreateResults(self.ProjectDirectory.encode('utf-8'), self.NetworkName.encode('utf-8'), self.Secnario.encode('utf-8'), resultPath.encode('utf-8'), self.Variables.encode('utf-8'), "".encode('utf-8'), "".encode('utf-8'))
        try: #QGis 3.x
            b= "".join(map(chr, b)) #bytes to string
        except:  #QGis 2.x
            b=b
        
        #Open layers
        self.openLayerResults(self.Secnario)
        value = self.hsTimes.value()
        self.paintIntervalTimeResults(value, True)
        QApplication.restoreOverrideCursor()
        
        #Message
        if b=="True":
            pass# self.iface.messageBar().pushMessage("Information", "Process successfully completed", level=3, duration=10)
        elif b=="False":
            self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=10)
        else:
            self.iface.messageBar().pushMessage("Error", b, level=2, duration=10)