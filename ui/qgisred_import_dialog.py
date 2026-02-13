# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QFileDialog, QDialog, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from qgis.core import QgsVectorLayer, QgsProject, QgsCoordinateReferenceSystem, QgsWkbTypes
from qgis.PyQt import uic
from qgis.gui import QgsProjectionSelectionDialog as QgsGenericProjectionSelector
from ..tools.qgisred_utils import QGISRedUtils
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
import os
import tempfile


FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_import_dialog.ui"))


class QGISRedImportDialog(QDialog, FORM_CLASS):
    # Common variables
    iface = None
    NewProject = True
    NetworkName = ""
    ProjectDirectory = ""
    InpFile = ""
    ZipFile = ""
    gplFile = ""
    ownMainLayers = ["Pipes", "Valves", "Pumps", "Junctions", "Tanks", "Reservoirs", "Demands", "Sources"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns"]

    def __init__(self, parent=None):
        """Constructor."""
        super(QGISRedImportDialog, self).__init__(parent)
        self.setupUi(self)
        gplFolder = os.path.join(os.getenv("APPDATA"), "QGISRed")
        try:  # create directory if does not exist
            os.stat(gplFolder)
        except Exception:
            os.mkdir(gplFolder)
        self.gplFile = os.path.join(gplFolder, "qgisredprojectlist.gpl")
        # INP
        self.btImportInp.clicked.connect(self.importInpProject)
        self.btSelectDirectory.clicked.connect(self.selectDirectory)
        self.btSelectCRS.clicked.connect(self.selectCRS)
        self.btSelectInp.clicked.connect(self.selectINP)
        # SHPs
        self.btSelectSHPDirectory.clicked.connect(self.selectSHPDirectory)
        self.cbPipeLayer.currentIndexChanged.connect(self.pipeLayerChanged)
        self.cbValveLayer.currentIndexChanged.connect(self.valveLayerChanged)
        self.cbPumpLayer.currentIndexChanged.connect(self.pumpLayerChanged)
        self.cbTankLayer.currentIndexChanged.connect(self.tankLayerChanged)
        self.cbReservoirLayer.currentIndexChanged.connect(self.reservoirLayerChanged)
        self.cbJunctionLayer.currentIndexChanged.connect(self.junctionLayerChanged)
        self.cbServiceConnectionLayer.currentIndexChanged.connect(self.serviceConnectionLayerChanged)
        self.cbIsolationValveLayer.currentIndexChanged.connect(self.isolationValveLayerChanged)
        self.cbMeterLayer.currentIndexChanged.connect(self.meterLayerChanged)
        self.cbMeterType.currentIndexChanged.connect(self.meterTypeChanged)
        self.btImportShps.clicked.connect(self.importShpProject)
        # QGISRed project
        self.btSelectZip.clicked.connect(self.selectZIP)
        self.btImportProject.clicked.connect(self.importProject)

    def config(self, ifac, direct, netw, parent):
        self.parent = parent
        self.iface = ifac

        utils = QGISRedUtils(direct, netw, ifac)
        self.crs = utils.getProjectCrs()
        self.tbCRS.setText(self.crs.description())
        self.lbUnits.setText("Degrees")
        self.ProcessDone = False
        self.InpFile = ""

        self.NetworkName = netw
        self.tbNetworkName.setText(netw)
        self.NewProject = False
        if direct == "Temporal folder":
            self.NewProject = True
            direct = QGISRedUtils().getUserFolder()
        self.ProjectDirectory = direct
        self.tbProjectDirectory.setText(direct)
        # self.tbProjectDirectory.setCursorPosition(0)
        self.tbTolerance.setText(str(0))
        self.tbScLength.setText(str(5))
        self.isPunctualConnection = False
        self.tbScLength.setEnabled(self.isPunctualConnection)

        if not self.NewProject:
            self.setWindowTitle("QGISRed: Add data")
            icon_path = ":/plugins/QGISRed/images/iconAddData.png"
            self.setWindowIcon(QIcon(icon_path))
            self.lbProject.setVisible(False)
            self.tbProjectDirectory.setVisible(False)
            self.btSelectDirectory.setVisible(False)
            self.lbName.setVisible(False)
            self.tbNetworkName.setVisible(False)
            self.lbCrs.setVisible(False)
            self.tbCRS.setVisible(False)
            self.btSelectCRS.setVisible(False)
            self.tabWidget.removeTab(0)
            self.tabWidget.removeTab(1)
            self.label_14.setVisible(False)
            self.label_15.setVisible(False)
            self.cbUnits.setVisible(False)
            self.cbHeadloss.setVisible(False)
            self.cbCreateSubfolder.setVisible(False)

    def selectDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory(self, "Select folder", self.ProjectDirectory)
        if not selected_directory == "":
            self.tbProjectDirectory.setText(selected_directory)
            # self.tbProjectDirectory.setCursorPosition(0)
            self.ProjectDirectory = selected_directory
            self.NetworkName = self.tbNetworkName.text()

            dirList = os.listdir(self.ProjectDirectory)
            self.NewProject = True
            for name in self.ownMainLayers:
                if self.NetworkName + "_" + name + ".shp" in dirList:
                    self.NewProject = False
                    break

    def selectCRS(self):
        projSelector = QgsGenericProjectionSelector()
        if projSelector.exec_():
            crsId = projSelector.crs().srsid()
            if not crsId == 0:
                self.crs = QgsCoordinateReferenceSystem()
                self.crs.createFromId(crsId, QgsCoordinateReferenceSystem.InternalCrsId)
                self.tbCRS.setText(self.crs.description())
                self.lbUnits.setText(str(self.convertMapUnits(self.crs.mapUnits())).replace("DistanceUnit.", ""))

    def convertMapUnits(self, units):
        if units == 0:
            return "Meters"
        if units == 1:
            return "Kilometers"
        if units == 2:
            return "Feets"
        if units == 3:
            return "NauticalMiles"
        if units == 4:
            return "Yards"
        if units == 5:
            return "Miles"
        if units == 6:
            return "Degrees"
        if units == 7:
            return "Centimeters"
        if units == 8:
            return "Milimeters"
        if units == 9:
            return "Unknown"

        return units
        

    def validationsCreateProject(self, validateName=True):
        if not self.NewProject:
            return True
        self.NetworkName = self.tbNetworkName.text()
        if validateName and len(self.NetworkName) == 0:
            self.iface.messageBar().pushMessage("Validations", "The project name is not valid", level=1)
            return False
        self.ProjectDirectory = self.tbProjectDirectory.text()
        if len(self.ProjectDirectory) == 0:
            self.iface.messageBar().pushMessage("Validations", "The project folder is not valid", level=1)
            return False
        else:
            if not os.path.exists(self.ProjectDirectory):
                self.iface.messageBar().pushMessage("Validations", "The project folder does not exist", level=1)
                return False
            elif validateName:
                if self.cbCreateSubfolder.isChecked():
                    self.ProjectDirectory = os.path.join(self.ProjectDirectory, self.NetworkName)
                if os.path.exists(self.ProjectDirectory):
                    dirList = os.listdir(self.ProjectDirectory)
                    layers = [
                        "Pipes",
                        "Junctions",
                        "Tanks",
                        "Reservoirs",
                        "Valves",
                        "Pumps",
                        "IsolationValves",
                        "Hydrants",
                        "WashoutValves",
                        "AirReleaseValves",
                        "ServiceConnections",
                        "Manometers",
                        "Flowmeters",
                        "Countermeters",
                        "LevelSensors",
                    ]
                    for layer in layers:
                        if self.NetworkName + "_" + layer + ".shp" in dirList:
                            message = "The selected folder has some files with the same project name."
                            self.iface.messageBar().pushMessage("Validations", message, level=1)
                            return False
        if self.cbCreateSubfolder.isChecked() and not os.path.exists(self.ProjectDirectory):
            try:  # create directory if does not exist
                os.stat(self.ProjectDirectory)
            except Exception:
                os.mkdir(self.ProjectDirectory)

        return True

    def createProject(self):
        epsg = self.crs.authid().replace("EPSG:", "")
        units = self.cbUnits.currentText()
        headloss = self.cbHeadloss.currentText()
        # Process
        QApplication.setOverrideCursor(Qt.WaitCursor)
        resMessage = GISRed.CreateProject(self.ProjectDirectory, self.NetworkName, epsg, units, headloss)
        QApplication.restoreOverrideCursor()

        # Message
        if not resMessage == "True":
            if resMessage == "False":
                self.iface.messageBar().pushMessage("Warning", "Some issues occurred in the process", level=1, duration=5)
            else:
                self.iface.messageBar().pushMessage("Error", resMessage, level=2, duration=5)
            self.close()
            return False

        # Write .gql file
        file = open(self.gplFile, "a+")
        QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + "\n")
        file.close()
        return True

    def getInputGroup(self):
        inputGroup = QgsProject.instance().layerTreeRoot().findGroup("Inputs")
        if inputGroup is None:
            netGroup = QgsProject.instance().layerTreeRoot().findGroup(self.NetworkName)
            if netGroup is None:
                root = QgsProject.instance().layerTreeRoot()
                netGroup = root.insertGroup(0, self.NetworkName)
            inputGroup = netGroup.addGroup("Inputs")
        return inputGroup

    def setZoomExtent(self, exception=None, result=None):
        self.iface.mapCanvas().zoomToFullExtent()
        self.iface.mapCanvas().refresh()

    """INP SECTION"""

    def selectINP(self):
        qfd = QFileDialog()
        path = ""
        filter = "inp(*.inp)"
        f = QFileDialog.getOpenFileName(qfd, "Select INP file", path, filter)
        f = f[0]
        if not f == "":
            self.InpFile = f
            self.tbInpFile.setText(f)
            # self.tbInpFile.setCursorPosition(0)

    def importInpProject(self):
        # Common validations
        isValid = self.validationsCreateProject()
        if isValid:
            # Validations INP
            self.InpFile = self.tbInpFile.text()
            if len(self.InpFile) == 0:
                self.iface.messageBar().pushMessage("Validations", "INP file is not valid", level=1)
                return
            else:
                if not os.path.exists(self.InpFile):
                    self.iface.messageBar().pushMessage("Validations", "INP file does not exist", level=1)
                    return

            self.close()
            # Process
            self.parent.zoomToFullExtent = True
            epsg = self.crs.authid().replace("EPSG:", "")
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.ImportFromInp(self.ProjectDirectory, self.NetworkName, self.parent.tempFolder, self.InpFile, epsg)
            QApplication.restoreOverrideCursor()
            self.parent.ProjectDirectory = self.ProjectDirectory
            self.parent.NetworkName = self.NetworkName

            # Write .gql file
            file = open(self.gplFile, "a+")
            QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + "\n")
            file.close()

            # Open files
            self.parent.processCsharpResult(resMessage, "")

    """SHPS SECTION"""

    def selectSHPDirectory(self):
        selected_directory = QFileDialog.getExistingDirectory(self, "Select folder", self.ProjectDirectory)
        if selected_directory == "":
            return

        self.tbShpDirectory.setText(selected_directory)
        # self.tbShpDirectory.setCursorPosition(0)

        dirList = os.listdir(selected_directory)
        self.cbPipeLayer.clear()
        self.cbPipeLayer.addItem("None")
        self.cbValveLayer.clear()
        self.cbValveLayer.addItem("None")
        self.cbPumpLayer.clear()
        self.cbPumpLayer.addItem("None")
        self.cbTankLayer.clear()
        self.cbTankLayer.addItem("None")
        self.cbReservoirLayer.clear()
        self.cbReservoirLayer.addItem("None")
        self.cbJunctionLayer.clear()
        self.cbJunctionLayer.addItem("None")
        self.cbServiceConnectionLayer.clear()
        self.cbServiceConnectionLayer.addItem("None")
        self.cbIsolationValveLayer.clear()
        self.cbIsolationValveLayer.addItem("None")
        self.cbMeterLayer.clear()
        self.cbMeterLayer.addItem("None")

        self.layerGeometryType = {}
        for file in dirList:
            if ".shp" in file:
                layerPath = os.path.join(self.tbShpDirectory.text(), file)
                vlayer = QgsVectorLayer(layerPath, "layer", "ogr")
                if not vlayer.isValid():
                    continue
                features = vlayer.getFeatures()
                # only check first feature
                for feature in features:
                    featureType = feature.geometry().type()
                    name = os.path.splitext(os.path.basename(file))[0]
                    if featureType == QgsWkbTypes.LineGeometry:
                        self.cbPipeLayer.addItem(name)
                    if featureType == QgsWkbTypes.LineGeometry or featureType == QgsWkbTypes.PointGeometry:
                        if featureType == QgsWkbTypes.LineGeometry:
                            self.layerGeometryType[name] = "Line"
                        else:
                            self.layerGeometryType[name] = "Point"
                        self.cbValveLayer.addItem(name)
                        self.cbPumpLayer.addItem(name)
                        self.cbServiceConnectionLayer.addItem(name)
                    if featureType == QgsWkbTypes.PointGeometry:
                        self.cbTankLayer.addItem(name)
                        self.cbReservoirLayer.addItem(name)
                        self.cbJunctionLayer.addItem(name)
                        self.cbIsolationValveLayer.addItem(name)
                        self.cbMeterLayer.addItem(name)
                    break
                vlayer = None

    def selectComboBoxItem(self, combobox, options):
        for i in range(combobox.count()):
            fieldName = combobox.itemText(i).lower()
            if fieldName in options:
                combobox.setCurrentIndex(i)
                return

    def pipeLayerChanged(self):
        newItem = self.cbPipeLayer.currentText()
        self.cbPipe_Id.clear()
        self.cbPipe_Length.clear()
        self.cbPipe_Diameter.clear()
        self.cbPipe_Roughness.clear()
        self.cbPipe_LossCoef.clear()
        self.cbPipe_Material.clear()
        self.cbPipe_InstDate.clear()
        self.cbPipe_Status.clear()
        self.cbPipe_Bulk.clear()
        self.cbPipe_Wall.clear()
        self.cbPipe_Tag.clear()
        self.cbPipe_Descr.clear()
        if newItem == "None":
            self.gbPipes.setEnabled(False)
            return

        self.gbPipes.setEnabled(True)

        pipeLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(pipeLayer, "Pipes layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbPipe_Id.addItems(field_names)
        self.cbPipe_Length.addItems(field_names)
        self.cbPipe_Diameter.addItems(field_names)
        self.cbPipe_Roughness.addItems(field_names)
        self.cbPipe_LossCoef.addItems(field_names)
        self.cbPipe_Material.addItems(field_names)
        self.cbPipe_InstDate.addItems(field_names)
        self.cbPipe_Status.addItems(field_names)
        self.cbPipe_Bulk.addItems(field_names)
        self.cbPipe_Wall.addItems(field_names)
        self.cbPipe_Tag.addItems(field_names)
        self.cbPipe_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbPipe_Id, ["id"])
        self.selectComboBoxItem(self.cbPipe_Length, ["length", "longitud"])
        self.selectComboBoxItem(self.cbPipe_Diameter, ["diameter", "diam", "diametro", "diámetro"])
        self.selectComboBoxItem(self.cbPipe_Roughness, ["roughness", "roughcoeff"])
        self.selectComboBoxItem(self.cbPipe_LossCoef, ["losscoeff"])
        self.selectComboBoxItem(self.cbPipe_Material, ["material"])
        self.selectComboBoxItem(self.cbPipe_InstDate, ["instaldate", "instdate", "date", "fecha", "fecha_de_i"])
        self.selectComboBoxItem(self.cbPipe_Status, ["status", "estado", "inistatus"])
        self.selectComboBoxItem(self.cbPipe_Bulk, ["bulkcoeff"])
        self.selectComboBoxItem(self.cbPipe_Wall, ["wallcoeff"])
        self.selectComboBoxItem(self.cbPipe_Tag, ["tag"])
        self.selectComboBoxItem(self.cbPipe_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def valveLayerChanged(self):
        newItem = self.cbValveLayer.currentText()
        self.cbValve_Id.clear()
        self.cbValve_Diameter.clear()
        self.cbValve_Type.clear()
        self.cbValve_InitStat.clear()
        self.cbValve_Orient.clear()
        self.cbValve_Tag.clear()
        self.cbValve_Descr.clear()
        if newItem == "None":
            self.gbValves.setEnabled(False)
            return

        self.gbValves.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "Valves layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbValve_Id.addItems(field_names)
        self.cbValve_Diameter.addItems(field_names)
        self.cbValve_Type.addItems(field_names)
        self.cbValve_InitStat.addItems(field_names)
        self.cbValve_Orient.addItems(field_names)
        self.cbValve_Tag.addItems(field_names)
        self.cbValve_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbValve_Id, ["id"])
        self.selectComboBoxItem(self.cbValve_Diameter, ["diameter", "diam", "diametro", "diámetro"])
        self.selectComboBoxItem(self.cbValve_Type, ["type", "tipo"])
        self.selectComboBoxItem(self.cbValve_InitStat, ["inistatus"])
        self.selectComboBoxItem(self.cbValve_Orient, ["orientatio"])
        self.selectComboBoxItem(self.cbValve_Tag, ["tag"])
        self.selectComboBoxItem(self.cbValve_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def pumpLayerChanged(self):
        newItem = self.cbPumpLayer.currentText()
        self.cbPump_Id.clear()
        self.cbPump_Power.clear()
        self.cbPump_PumpCurve.clear()
        self.cbPump_EfficCurve.clear()
        self.cbPump_InitStat.clear()
        self.cbPump_Orient.clear()
        self.cbPump_Tag.clear()
        self.cbPump_Descr.clear()
        if newItem == "None":
            self.gbPumps.setEnabled(False)
            return

        self.gbPumps.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "Pumps layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbPump_Id.addItems(field_names)
        self.cbPump_Power.addItems(field_names)
        self.cbPump_PumpCurve.addItems(field_names)
        self.cbPump_EfficCurve.addItems(field_names)
        self.cbPump_InitStat.addItems(field_names)
        self.cbPump_Orient.addItems(field_names)
        self.cbPump_Tag.addItems(field_names)
        self.cbPump_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbPump_Id, ["id"])
        self.selectComboBoxItem(self.cbPump_Power, ["power", "potencia"])
        self.selectComboBoxItem(self.cbPump_PumpCurve, ["idhfcurve"])
        self.selectComboBoxItem(self.cbPump_EfficCurve, ["idefficur"])
        self.selectComboBoxItem(self.cbPump_InitStat, ["inistatus"])
        self.selectComboBoxItem(self.cbPump_Orient, ["orientatio"])
        self.selectComboBoxItem(self.cbPump_Tag, ["tag"])
        self.selectComboBoxItem(self.cbPump_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def tankLayerChanged(self):
        newItem = self.cbTankLayer.currentText()
        self.cbTank_Id.clear()
        self.cbTank_Elevat.clear()
        self.cbTank_MinLevel.clear()
        self.cbTank_MaxLevel.clear()
        self.cbTank_Diameter.clear()
        self.cbTank_ReactCoeff.clear()
        self.cbTank_InitLevel.clear()
        self.cbTank_MinVolume.clear()
        self.cbTank_MixModel.clear()
        self.cbTank_MixFraction.clear()
        self.cbTank_Tag.clear()
        self.cbTank_Descr.clear()
        if newItem == "None":
            self.gbTanks.setEnabled(False)
            return

        self.gbTanks.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "Tanks layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbTank_Id.addItems(field_names)
        self.cbTank_Elevat.addItems(field_names)
        self.cbTank_MinLevel.addItems(field_names)
        self.cbTank_MaxLevel.addItems(field_names)
        self.cbTank_Diameter.addItems(field_names)
        self.cbTank_ReactCoeff.addItems(field_names)
        self.cbTank_InitLevel.addItems(field_names)
        self.cbTank_MinVolume.addItems(field_names)
        self.cbTank_MixModel.addItems(field_names)
        self.cbTank_MixFraction.addItems(field_names)
        self.cbTank_Tag.addItems(field_names)
        self.cbTank_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbTank_Id, ["id"])
        self.selectComboBoxItem(self.cbTank_Elevat, ["elevation"])
        self.selectComboBoxItem(self.cbTank_MinLevel, ["minlevel"])
        self.selectComboBoxItem(self.cbTank_MaxLevel, ["maxlevel"])
        self.selectComboBoxItem(self.cbTank_Diameter, ["diameter", "diam", "diametro", "diámetro"])
        self.selectComboBoxItem(self.cbTank_ReactCoeff, ["reactcoef"])
        self.selectComboBoxItem(self.cbTank_InitLevel, ["inilevel", "level", "nivel"])
        self.selectComboBoxItem(self.cbTank_MinVolume, ["minvolume"])
        self.selectComboBoxItem(self.cbTank_MixModel, ["mixingmod", "mixmodel"])
        self.selectComboBoxItem(self.cbTank_MixFraction, ["mixingfrac", "mixfraction"])
        self.selectComboBoxItem(self.cbTank_Tag, ["tag"])
        self.selectComboBoxItem(self.cbTank_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def reservoirLayerChanged(self):
        newItem = self.cbReservoirLayer.currentText()
        self.cbReservoir_Id.clear()
        self.cbReservoir_TotHead.clear()
        self.cbReservoir_HeadPatt.clear()
        self.cbReservoir_Tag.clear()
        self.cbReservoir_Descr.clear()
        if newItem == "None":
            self.gbReservoirs.setEnabled(False)
            return

        self.gbReservoirs.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "Reservoirs layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbReservoir_Id.addItems(field_names)
        self.cbReservoir_TotHead.addItems(field_names)
        self.cbReservoir_HeadPatt.addItems(field_names)
        self.cbReservoir_Tag.addItems(field_names)
        self.cbReservoir_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbReservoir_Id, ["id"])
        self.selectComboBoxItem(self.cbReservoir_TotHead, ["totalhead"])
        self.selectComboBoxItem(self.cbReservoir_HeadPatt, ["idheadpatt"])
        self.selectComboBoxItem(self.cbReservoir_Tag, ["tag"])
        self.selectComboBoxItem(self.cbReservoir_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def junctionLayerChanged(self):
        newItem = self.cbJunctionLayer.currentText()
        self.cbJunction_Id.clear()
        self.cbJunction_Elevation.clear()
        self.cbJunction_BaseDem.clear()
        self.cbJunction_Pattern.clear()
        self.cbJunction_Tag.clear()
        self.cbJunction_Descr.clear()
        if newItem == "None":
            self.gbJunctions.setEnabled(False)
            return

        self.gbJunctions.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "Juntions layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbJunction_Id.addItems(field_names)
        self.cbJunction_Elevation.addItems(field_names)
        self.cbJunction_BaseDem.addItems(field_names)
        self.cbJunction_Pattern.addItems(field_names)
        self.cbJunction_Tag.addItems(field_names)
        self.cbJunction_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbJunction_Id, ["id"])
        self.selectComboBoxItem(self.cbJunction_Elevation, ["elevation"])
        self.selectComboBoxItem(self.cbJunction_BaseDem, ["basedem"])
        self.selectComboBoxItem(self.cbJunction_Pattern, ["pattern", "idpattdem"])
        self.selectComboBoxItem(self.cbJunction_Tag, ["tag"])
        self.selectComboBoxItem(self.cbJunction_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def serviceConnectionLayerChanged(self):
        newItem = self.cbServiceConnectionLayer.currentText()
        self.cbServiceConnection_Id.clear()
        self.cbServiceConnection_Length.clear()
        self.cbServiceConnection_Diameter.clear()
        self.cbServiceConnection_Roughness.clear()
        self.cbServiceConnection_Material.clear()
        self.cbServiceConnection_Demand.clear()
        self.cbServiceConnection_Pattern.clear()
        self.cbServiceConnection_IsActive.clear()
        self.cbServiceConnection_InstDate.clear()
        self.cbServiceConnection_Tag.clear()
        self.cbServiceConnection_Descr.clear()

        if newItem == "None" or newItem == "":
            self.gbServiceConnection.setEnabled(False)
            return

        self.gbServiceConnection.setEnabled(True)
        self.isPunctualConnection = self.layerGeometryType[newItem] == "Point"
        self.tbScLength.setEnabled(self.isPunctualConnection)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "SC layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbServiceConnection_Id.addItems(field_names)
        self.cbServiceConnection_Length.addItems(field_names)
        self.cbServiceConnection_Diameter.addItems(field_names)
        self.cbServiceConnection_Roughness.addItems(field_names)
        self.cbServiceConnection_Material.addItems(field_names)
        self.cbServiceConnection_Demand.addItems(field_names)
        self.cbServiceConnection_Pattern.addItems(field_names)
        self.cbServiceConnection_IsActive.addItems(field_names)
        self.cbServiceConnection_InstDate.addItems(field_names)
        self.cbServiceConnection_Tag.addItems(field_names)
        self.cbServiceConnection_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbServiceConnection_Id, ["id"])
        self.selectComboBoxItem(self.cbServiceConnection_Length, ["length", "longitud"])
        self.selectComboBoxItem(self.cbServiceConnection_Diameter, ["diameter", "diam", "diametro", "diámetro"])
        self.selectComboBoxItem(self.cbServiceConnection_Roughness, ["roughness"])
        self.selectComboBoxItem(self.cbServiceConnection_Material, ["material"])
        self.selectComboBoxItem(self.cbServiceConnection_Demand, ["demand", "basedem", "basedemand"])
        self.selectComboBoxItem(self.cbServiceConnection_Pattern, ["pattern", "idpattdem"])
        self.selectComboBoxItem(self.cbServiceConnection_IsActive, ["isactive", "active"])
        self.selectComboBoxItem(self.cbServiceConnection_InstDate, ["instdate", "date", "fecha", "fecha_de_i"])
        self.selectComboBoxItem(self.cbServiceConnection_Tag, ["tag"])
        self.selectComboBoxItem(self.cbServiceConnection_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def isolationValveLayerChanged(self):
        newItem = self.cbIsolationValveLayer.currentText()
        self.cbIsolationValve_Id.clear()
        self.cbIsolationValve_Diameter.clear()
        self.cbIsolationValve_LossCoeff.clear()
        self.cbIsolationValve_Status.clear()
        self.cbIsolationValve_Available.clear()
        self.cbIsolationValve_InstDate.clear()
        self.cbIsolationValve_Tag.clear()
        self.cbIsolationValve_Descr.clear()

        if newItem == "None":
            self.gbIsolationValve.setEnabled(False)
            return

        self.gbIsolationValve.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "IV layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbIsolationValve_Id.addItems(field_names)
        self.cbIsolationValve_Diameter.addItems(field_names)
        self.cbIsolationValve_LossCoeff.addItems(field_names)
        self.cbIsolationValve_Status.addItems(field_names)
        self.cbIsolationValve_Available.addItems(field_names)
        self.cbIsolationValve_InstDate.addItems(field_names)
        self.cbIsolationValve_Tag.addItems(field_names)
        self.cbIsolationValve_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbIsolationValve_Id, ["id"])
        self.selectComboBoxItem(self.cbIsolationValve_Diameter, ["diameter", "diam", "diametro", "diámetro"])
        self.selectComboBoxItem(self.cbIsolationValve_LossCoeff, ["losscoeff"])
        self.selectComboBoxItem(self.cbIsolationValve_Status, ["status", "estado"])
        self.selectComboBoxItem(self.cbIsolationValve_Available, ["available", "works", "disponible", "funciona"])
        self.selectComboBoxItem(self.cbIsolationValve_InstDate, ["instdate", "date", "fecha", "fecha_de_i"])
        self.selectComboBoxItem(self.cbIsolationValve_Tag, ["tag"])
        self.selectComboBoxItem(self.cbIsolationValve_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def meterLayerChanged(self):
        newItem = self.cbMeterLayer.currentText()
        self.cbMeter_Id.clear()
        self.cbMeter_Type.clear()
        self.cbMeter_Active.clear()
        self.cbMeter_InstDate.clear()
        self.cbMeter_Orientation.clear()
        self.cbMeter_Tag.clear()
        self.cbMeter_Descr.clear()

        if newItem == "None":
            self.gbMeter.setEnabled(False)
            return

        self.gbMeter.setEnabled(True)

        valveLayer = os.path.join(self.tbShpDirectory.text(), newItem + ".shp")
        vlayer = QgsVectorLayer(valveLayer, "IV layer", "ogr")
        if not vlayer.isValid():
            return
        field_names = [field.name() for field in vlayer.fields()]
        field_names.insert(0, "None")
        self.cbMeter_Id.addItems(field_names)
        self.cbMeter_Type.addItems(field_names)
        self.cbMeter_Active.addItems(field_names)
        self.cbMeter_InstDate.addItems(field_names)
        self.cbMeter_Orientation.addItems(field_names)
        self.cbMeter_Tag.addItems(field_names)
        self.cbMeter_Descr.addItems(field_names)

        self.selectComboBoxItem(self.cbMeter_Id, ["id"])
        self.selectComboBoxItem(self.cbMeter_Type, ["type", "tipo", "meter", "medidor"])
        self.selectComboBoxItem(self.cbMeter_Active, ["active", "activo"])
        self.selectComboBoxItem(self.cbMeter_InstDate, ["instdate", "date", "fecha", "fecha_de_i"])
        self.selectComboBoxItem(self.cbMeter_Orientation, ["orientation"])
        self.selectComboBoxItem(self.cbMeter_Tag, ["tag"])
        self.selectComboBoxItem(self.cbMeter_Descr, ["descrip", "descr", "description", "descripcion", "descripción"])

    def meterTypeChanged(self):
        newItem = self.cbMeterType.currentIndex()

        self.cbMeter_Type.setEnabled(newItem == 0)
        if newItem != 0:
            self.cbMeter_Type.setCurrentIndex(0)
        self.cbMeter_Orientation.setEnabled(newItem == 0 or newItem == 2 or newItem == 3)
        if newItem != 0 and newItem != 2 and newItem != 3:
            self.cbMeter_Orientation.setCurrentIndex(0)

    def createShpsNames(self):
        shpFolder = self.tbShpDirectory.text()
        shpNames = ""

        name = self.cbPipeLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[PIPES]" + os.path.join(shpFolder, name) + ","
        name = self.cbValveLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[VALVES]" + os.path.join(shpFolder, name) + ","
        name = self.cbPumpLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[PUMPS]" + os.path.join(shpFolder, name) + ","
        name = self.cbTankLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[TANKS]" + os.path.join(shpFolder, name) + ","
        name = self.cbReservoirLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[RESERVOIRS]" + os.path.join(shpFolder, name) + ","
        name = self.cbJunctionLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[JUNCTIONS]" + os.path.join(shpFolder, name) + ","
        name = self.cbServiceConnectionLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[SERVICECONNECTIONS]" + os.path.join(shpFolder, name) + ","
        name = self.cbIsolationValveLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[ISOLATIONVALVES]" + os.path.join(shpFolder, name) + ","
        name = self.cbMeterLayer.currentText()
        if not name == "None":
            shpNames = shpNames + "[METERS]" + os.path.join(shpFolder, name) + ","
        return shpNames

    def createShpFields(self):
        fields = ""

        name = self.cbPipeLayer.currentText()
        if not name == "None":
            fields = "[PIPES]"
            name = self.cbPipe_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Length.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Diameter.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Roughness.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Material.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_InstDate.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_LossCoef.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Status.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Bulk.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Wall.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPipe_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbValveLayer.currentText()
        if not name == "None":
            fields = fields + "[VALVES]"
            name = self.cbValve_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbValve_Diameter.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbValve_Type.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # Setting
            fields = fields + ";"  # IdHeadLoss
            fields = fields + ";"  # LossCoef
            name = self.cbValve_InitStat.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbValve_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbValve_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            # fields = fields + ";" #Sector
            name = self.cbValve_Orient.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbPumpLayer.currentText()
        if not name == "None":
            fields = fields + "[PUMPS]"
            name = self.cbPump_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPump_PumpCurve.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"  # IdHFCurve
            name = self.cbPump_Power.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # Speed
            fields = fields + ";"  # IdSpeedPat
            name = self.cbPump_InitStat.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPump_EfficCurve.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # EnergPrice
            fields = fields + ";"  # IdPricePat
            name = self.cbPump_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbPump_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            # fields = fields + ";" #Sector
            name = self.cbPump_Orient.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbTankLayer.currentText()
        if not name == "None":
            fields = fields + "[TANKS]"
            name = self.cbTank_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_Elevat.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_InitLevel.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_MinLevel.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_MaxLevel.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_Diameter.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_MinVolume.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # IdVolCur
            name = self.cbTank_MixModel.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_MixFraction.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_ReactCoeff.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # InitialQuality
            name = self.cbTank_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbTank_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbReservoirLayer.currentText()
        if not name == "None":
            fields = fields + "[RESERVOIRS]"
            name = self.cbReservoir_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbReservoir_TotHead.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbReservoir_HeadPatt.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # IniQual
            name = self.cbReservoir_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbReservoir_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbJunctionLayer.currentText()
        if not name == "None":
            fields = fields + "[JUNCTIONS]"
            name = self.cbJunction_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbJunction_Elevation.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbJunction_BaseDem.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbJunction_Pattern.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"  # EmitCoef
            fields = fields + ";"  # IniQual
            name = self.cbJunction_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbJunction_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbServiceConnectionLayer.currentText()
        if not name == "None":
            fields = fields + "[SERVICECONNECTIONS]"
            name = self.cbServiceConnection_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Length.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Diameter.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Roughness.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Material.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_IsActive.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_InstDate.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Demand.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbServiceConnection_Pattern.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            fields = fields + ";"  # Reliability
            fields = fields + ","  # To separate layers

        name = self.cbIsolationValveLayer.currentText()
        if not name == "None":
            fields = fields + "[ISOLATIONVALVES]"
            name = self.cbIsolationValve_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_Diameter.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_LossCoeff.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_Status.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_Available.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_InstDate.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbIsolationValve_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        name = self.cbMeterLayer.currentText()
        if not name == "None":
            fields = fields + "[METERS]"
            name = self.cbMeter_Id.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            index = self.cbMeterType.currentIndex()
            if index == 0:
                name = self.cbMeter_Type.currentText()
                if not name == "None":
                    fields = fields + name
            else:
                name = self.cbMeterType.currentText()
                fields = fields + "QGISRed" + name.replace(" ", "")
            fields = fields + ";"
            name = self.cbMeter_Active.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbMeter_InstDate.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbMeter_Tag.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbMeter_Descr.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"
            name = self.cbMeter_Orientation.currentText()
            if not name == "None":
                fields = fields + name
            fields = fields + ";"

            fields = fields + ","  # To separate layers

        return fields

    def importShpProject(self):
        # Common validations
        isValid = self.validationsCreateProject()
        if isValid:
            # Validations SHP's
            if not os.path.exists(self.tbShpDirectory.text()):
                self.iface.messageBar().pushMessage("Validations", "The SHPs folder is not valid or does not exist", level=1)
                return
            # Tolerance
            tolerance = self.tbTolerance.text()
            try:
                t = float(tolerance)
                if t < 0:
                    self.iface.messageBar().pushMessage("Validations", "Not valid Tolerance", level=1)
                    return
            except Exception:
                self.iface.messageBar().pushMessage("Validations", "Not numeric Tolerance", level=1)
                return
            # ServiceConnection Length
            scLength = self.tbScLength.text()
            if self.isPunctualConnection:
                try:
                    t = float(scLength)
                    if t < 0:
                        self.iface.messageBar().pushMessage("Validations", "Not valid Service Connection Length", level=1)
                        return
                except Exception:
                    self.iface.messageBar().pushMessage("Validations", "Not numeric Service Connection Length", level=1)
                    return
            # Fields
            fields = self.createShpFields()
            if fields == "":
                self.iface.messageBar().pushMessage("Validations", "Any SHP selected for importing", level=1)
                return

            # Process
            if self.NewProject:
                if not self.createProject():
                    return

            self.close()
            self.parent.zoomToFullExtent = True

            epsg = self.crs.authid().replace("EPSG:", "")
            shapes = self.createShpsNames()
            # fields = self.createShpFields()

            # Process
            QApplication.setOverrideCursor(Qt.WaitCursor)
            resMessage = GISRed.ImportFromShps(
                self.ProjectDirectory, self.NetworkName, self.parent.tempFolder, shapes, fields, epsg, tolerance, scLength
            )
            QApplication.restoreOverrideCursor()
            self.parent.ProjectDirectory = self.ProjectDirectory
            self.parent.NetworkName = self.NetworkName

            self.parent.especificComplementaryLayers = []
            sc = self.cbServiceConnectionLayer.currentText()
            if not sc == "None":
                self.parent.especificComplementaryLayers.append("ServiceConnections")

            iv = self.cbIsolationValveLayer.currentText()
            if not iv == "None":
                self.parent.especificComplementaryLayers.append("IsolationValves")

            me = self.cbMeterLayer.currentText()
            if not me == "None":
                self.parent.especificComplementaryLayers.append("Meters")

            self.parent.processCsharpResult(resMessage, "")

    """QGISRED PROJECT SECTION"""

    def selectZIP(self):
        qfd = QFileDialog()
        path = ""
        filter = "zip(*.zip)"
        f = QFileDialog.getOpenFileName(qfd, "Select ZIP file", path, filter)
        f = f[0]
        if not f == "":
            self.ZipFile = f
            self.tbZipFile.setText(f)
            # self.tbZipFile.setCursorPosition(0)

    def importProject(self):
        pass
        # Common validations
        isValid = self.validationsCreateProject(False)
        if isValid:
            # Validations ZIP
            self.ZipFile = self.tbZipFile.text()
            if len(self.ZipFile) == 0:
                self.iface.messageBar().pushMessage("Validations", "ZIP file is not valid", level=1)
                return
            else:
                if not os.path.exists(self.ZipFile):
                    self.iface.messageBar().pushMessage("Validations", "ZIP file does not exist", level=1)
                    return

            self.close()
            # Process
            self.parent.zoomToFullExtent = True
            QApplication.setOverrideCursor(Qt.WaitCursor)
            # Unzip
            tempFolder = tempfile._get_default_tempdir() + "\\" + next(tempfile._get_candidate_names())
            QGISRedUtils().unzipFile(self.ZipFile, tempFolder)
            QApplication.restoreOverrideCursor()

            validProject = False
            for f in os.listdir(tempFolder):
                filepath = os.path.join(tempFolder, f)
                if "_Pipes.shp" in filepath:
                    validProject = True
                    self.NetworkName = f.replace("_Pipes.shp", "")
                    break

            if not validProject:
                self.iface.messageBar().pushMessage("Warninf", "ZIP file does not contain a valid QGISRed project", level=1)
                return

            QGISRedUtils().copyFolderFiles(tempFolder, self.ProjectDirectory)
            QGISRedUtils().removeFolder(tempFolder)
            self.parent.ProjectDirectory = self.ProjectDirectory
            self.parent.NetworkName = self.NetworkName

            # Write .gql file
            file = open(self.gplFile, "a+")
            QGISRedUtils().writeFile(file, self.NetworkName + ";" + self.ProjectDirectory + "\n")
            file.close()

            # Open files
            utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            utils.openProjectInQgis()
