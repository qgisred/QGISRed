from .qgisred_utils import QGISRedUtils
from ctypes import c_char_p, WinDLL


class QGISRedDependencies:
    @staticmethod
    def AddConnections(projectFolder, networkName, asNode, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        asNode = QGISRedDependencies.encode(asNode)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddConnections.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddConnections.restype = c_char_p
        b = mydll.AddConnections(projectFolder, networkName, asNode, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AddHydrants(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddHydrants.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddHydrants.restype = c_char_p
        b = mydll.AddHydrants(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AddPipe(projectFolder, networkName, tempFolder, pipePoints):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        pipePoints = QGISRedDependencies.encode(pipePoints)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddPipe.restype = c_char_p
        b = mydll.AddPipe(projectFolder, networkName, tempFolder, pipePoints)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AddReservoir(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddReservoir.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddReservoir.restype = c_char_p
        b = mydll.AddReservoir(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AddTank(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddTank.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.AddTank.restype = c_char_p
        b = mydll.AddTank(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AddWashoutValves(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AddWashoutValves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AddWashoutValves.restype = c_char_p
        b = mydll.AddWashoutValves(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def AnalysisOptions(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AnalysisOptions.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.AnalysisOptions.restype = c_char_p
        b = mydll.AnalysisOptions(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ChangeCrs(projectFolder, networkName, epsg):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        epsg = QGISRedDependencies.encode(epsg)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ChangeCrs.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.ChangeCrs.restype = c_char_p
        b = mydll.ChangeCrs(projectFolder, networkName, epsg)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckAlignedVertices(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckAlignedVertices.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckAlignedVertices.restype = c_char_p
        b = mydll.CheckAlignedVertices(projectFolder, networkName, tempFolder, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckConnectivity(projectFolder, networkName, linesToDelete, step, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        linesToDelete = QGISRedDependencies.encode(linesToDelete)
        step = QGISRedDependencies.encode(step)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckConnectivity.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckConnectivity.restype = c_char_p
        b = mydll.CheckConnectivity(projectFolder, networkName, linesToDelete, step, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckDiameters(projectFolder, networkName, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckDiameters.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckDiameters.restype = c_char_p
        b = mydll.CheckDiameters(projectFolder, networkName, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckInstallationDates(projectFolder, networkName, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckInstallationDates.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckInstallationDates.restype = c_char_p
        b = mydll.CheckInstallationDates(projectFolder, networkName, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckJoinPipes(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckJoinPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckJoinPipes.restype = c_char_p
        b = mydll.CheckJoinPipes(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckLengths(projectFolder, networkName, tolerance, tempFolder, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tolerance = QGISRedDependencies.encode(tolerance)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckLengths.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckLengths.restype = c_char_p
        b = mydll.CheckLengths(projectFolder, networkName, tolerance, tempFolder, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckMaterials(projectFolder, networkName, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckMaterials.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckMaterials.restype = c_char_p
        b = mydll.CheckMaterials(projectFolder, networkName, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckOverlappingElements(projectFolder, networkName, tempFolder, nodeIds, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        nodeIds = QGISRedDependencies.encode(nodeIds)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckOverlappingElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CheckOverlappingElements.restype = c_char_p
        b = mydll.CheckOverlappingElements(projectFolder, networkName, tempFolder, nodeIds, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CheckTConnections(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CheckTConnections.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CheckTConnections.restype = c_char_p
        b = mydll.CheckTConnections(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def Commit(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.Commit.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.Commit.restype = c_char_p
        b = mydll.Commit(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def Compute(projectFolder, networkName):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.Compute.argtypes = (c_char_p, c_char_p)
        mydll.Compute.restype = c_char_p
        b = mydll.Compute(projectFolder, networkName)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CreateLayer(projectFolder, networkName, layer, complLayer):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        layer = QGISRedDependencies.encode(layer)
        complLayer = QGISRedDependencies.encode(complLayer)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CreateLayer.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateLayer.restype = c_char_p
        b = mydll.CreateLayer(projectFolder, networkName, layer, complLayer)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CreateProject(projectFolder, networkName, epsg):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        epsg = QGISRedDependencies.encode(epsg)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CreateProject.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.CreateProject.restype = c_char_p
        b = mydll.CreateProject(projectFolder, networkName, epsg)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CreateResults(projectFolder, networkName, scenario, variables):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        scenario = QGISRedDependencies.encode(scenario)
        variables = QGISRedDependencies.encode(variables)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CreateResults.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateResults.restype = c_char_p
        b = mydll.CreateResults(projectFolder, networkName, scenario, variables)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CreateReverseCrossings(projectFolder, networkName, tempFolder, point1, tolerance):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point1 = QGISRedDependencies.encode(point1)
        tolerance = QGISRedDependencies.encode(tolerance)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CreateReverseCrossings.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseCrossings.restype = c_char_p
        b = mydll.CreateReverseCrossings(projectFolder, networkName, tempFolder, point1, tolerance)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def CreateReverseTConnection(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point1 = QGISRedDependencies.encode(point1)
        point2 = QGISRedDependencies.encode(point2)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.CreateReverseTConnection.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.CreateReverseTConnection.restype = c_char_p
        b = mydll.CreateReverseTConnection(projectFolder, networkName, tempFolder, point1, point2)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def DefaultValues(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.DefaultValues.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DefaultValues.restype = c_char_p
        b = mydll.DefaultValues(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def DemandSectors(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.DemandSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.DemandSectors.restype = c_char_p
        b = mydll.DemandSectors(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def EditControls(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.EditControls.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditControls.restype = c_char_p
        b = mydll.EditControls(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def EditElements(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.EditElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.EditElements.restype = c_char_p
        b = mydll.EditElements(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def EditPatternsCurves(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.EditPatternsCurves.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.EditPatternsCurves.restype = c_char_p
        b = mydll.EditPatternsCurves(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def EditSettings(projectFolder, networkName):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.EditSettings.argtypes = (c_char_p, c_char_p)
        mydll.EditSettings.restype = c_char_p
        b = mydll.EditSettings(projectFolder, networkName)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ElevationInterpolation(projectFolder, networkName, tempFolder, elevationFiles):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        elevationFiles = QGISRedDependencies.encode(elevationFiles)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ElevationInterpolation.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ElevationInterpolation.restype = c_char_p
        b = mydll.ElevationInterpolation(projectFolder, networkName, tempFolder, elevationFiles)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ExportToInp(projectFolder, networkName):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ExportToInp.argtypes = (c_char_p, c_char_p)
        mydll.ExportToInp.restype = c_char_p
        b = mydll.ExportToInp(projectFolder, networkName)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def HydarulicSectors(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.HydarulicSectors.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.HydarulicSectors.restype = c_char_p
        b = mydll.HydarulicSectors(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ImportFromInp(projectFolder, networkName, tempFolder, inpFile, epsg):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        inpFile = QGISRedDependencies.encode(inpFile)
        epsg = QGISRedDependencies.encode(epsg)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ImportFromInp.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ImportFromInp.restype = c_char_p
        b = mydll.ImportFromInp(projectFolder, networkName, tempFolder, inpFile, epsg)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ImportFromShps(projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        shapes = QGISRedDependencies.encode(shapes)
        fields = QGISRedDependencies.encode(fields)
        epsg = QGISRedDependencies.encode(epsg)
        tolerance = QGISRedDependencies.encode(tolerance)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ImportFromShps.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ImportFromShps.restype = c_char_p
        b = mydll.ImportFromShps(projectFolder, networkName, tempFolder, shapes, fields, epsg, tolerance)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def InsertPump(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.InsertPump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertPump.restype = c_char_p
        b = mydll.InsertPump(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def InsertValve(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.InsertValve.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.InsertValve.restype = c_char_p
        b = mydll.InsertValve(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def MoveValvePump(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point1 = QGISRedDependencies.encode(point1)
        point2 = QGISRedDependencies.encode(point2)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.MoveValvePump.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.MoveValvePump.restype = c_char_p
        b = mydll.MoveValvePump(projectFolder, networkName, tempFolder, point1, point2)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def RemoveElements(projectFolder, networkName, tempFolder, point, nodeIds, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)
        nodeIds = QGISRedDependencies.encode(nodeIds)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.RemoveElements.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.RemoveElements.restype = c_char_p
        b = mydll.RemoveElements(projectFolder, networkName, tempFolder, point, nodeIds, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ReplaceTemporalFiles(projectFolder, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ReplaceTemporalFiles.argtypes = (c_char_p, c_char_p)
        mydll.ReplaceTemporalFiles.restype = c_char_p
        b = mydll.ReplaceTemporalFiles(projectFolder, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def ReverseLink(projectFolder, networkName, tempFolder, point, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.ReverseLink.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.ReverseLink.restype = c_char_p
        b = mydll.ReverseLink(projectFolder, networkName, tempFolder, point, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def SetInitialStatusPipes(projectFolder, networkName, tempFolder):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.SetInitialStatusPipes.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.SetInitialStatusPipes.restype = c_char_p
        b = mydll.SetInitialStatusPipes(projectFolder, networkName, tempFolder)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def SetRoughness(projectFolder, networkName, tempFolder, linkIds):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        linkIds = QGISRedDependencies.encode(linkIds)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.SetRoughness.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SetRoughness.restype = c_char_p
        b = mydll.SetRoughness(projectFolder, networkName, tempFolder, linkIds)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def SplitMergeJunction(projectFolder, networkName, tempFolder, point1, point2):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point1 = QGISRedDependencies.encode(point1)
        point2 = QGISRedDependencies.encode(point2)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.SplitMergeJunction.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitMergeJunction.restype = c_char_p
        b = mydll.SplitMergeJunction(projectFolder, networkName, tempFolder, point1, point2)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def SplitPipe(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.SplitPipe.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.SplitPipe.restype = c_char_p
        b = mydll.SplitPipe(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def Summary(projectFolder, networkName):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.AbstractReport.argtypes = (c_char_p, c_char_p)
        mydll.AbstractReport.restype = c_char_p
        b = mydll.AbstractReport(projectFolder, networkName)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def Tree(projectFolder, networkName, tempFolder, point):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        tempFolder = QGISRedDependencies.encode(tempFolder)
        point = QGISRedDependencies.encode(point)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.Tree.argtypes = (c_char_p, c_char_p, c_char_p, c_char_p)
        mydll.Tree.restype = c_char_p
        b = mydll.Tree(projectFolder, networkName, tempFolder, point)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def UpdateMetadata(projectFolder, networkName, layersNames):
        projectFolder = QGISRedDependencies.encode(projectFolder)
        networkName = QGISRedDependencies.encode(networkName)
        layersNames = QGISRedDependencies.encode(layersNames)

        mydll = WinDLL(QGISRedUtils().getCurrentDll())
        mydll.UpdateMetadata.argtypes = (c_char_p, c_char_p, c_char_p)
        mydll.UpdateMetadata.restype = c_char_p
        b = mydll.UpdateMetadata(projectFolder, networkName, layersNames)
        return QGISRedDependencies.toString(b)

    @staticmethod
    def encode(string):
        return string.encode('utf-8')

    @staticmethod
    def toString(binary):
        return "".join(map(chr, binary))  # bytes to string
