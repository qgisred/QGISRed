from qgis.core import QgsVectorLayer, QgsProject, QgsLayerTreeLayer

try: #QGis 3.x
    from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayer, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
    from qgis.core import Qgis
except: #QGis 2.x
    from qgis.core import QgsSvgMarkerSymbolLayerV2 as QgsSvgMarkerSymbolLayer, QgsSymbolV2 as QgsSymbol, QgsSingleSymbolRendererV2 as QgsSingleSymbolRenderer, QgsLineSymbolV2 as QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayerV2 as QgsSimpleLineSymbolLayer, QgsMarkerSymbolV2 as QgsMarkerSymbol, QgsMarkerLineSymbolLayerV2 as QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayerV2 as QgsSimpleMarkerSymbolLayer
    from qgis.core import QgsMapLayerRegistry
    from qgis.core import QgsMapLayerRegistry, QGis as Qgis

import os
import gc

class QGISRedUtils:

    def __init__(self, directory="", networkName="", iface=None):
        self.iface = iface
        self.ProjectDirectory = directory
        self.NetworkName = networkName

    def isLayerOpened(self, layerName):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0]).replace("/","\\")== os.path.join(self.ProjectDirectory.replace("/","\\"), self.NetworkName + "_" + layerName + ".shp"):
                return True
        return False

    def openElementsLayers(self, group, crs, ownMainLayers, ownFiles):
        utils = QGISRedUtils(self.ProjectDirectory, self.NetworkName)
        for fileName in ownFiles:
            utils.openLayer(crs, group, fileName, ".dbf")
        for fileName in ownMainLayers:
            utils.openLayer(crs, group, fileName)

    def openLayer(self, crs, group, name, ext=".shp", results=False):
        layerName = self.NetworkName + "_" + name
        if os.path.exists(os.path.join(self.ProjectDirectory, layerName + ext)):
            vlayer = QgsVectorLayer(os.path.join(self.ProjectDirectory, layerName + ext), name, "ogr")
            if not ext == ".dbf":
                vlayer.setCrs(crs)
                if results:
                    self.setResultStyle(vlayer)
                else:
                    self.setStyle(vlayer, name.lower())
            try: #QGis 3.x
                QgsProject.instance().addMapLayer(vlayer, group is None)
            except: #QGis 2.x
                QgsMapLayerRegistry.instance().addMapLayer(vlayer, group is None)
            if group is not None:
                group.insertChildNode(0, QgsLayerTreeLayer(vlayer))
            del vlayer

    def removeLayers(self, layers, ext=".shp"):
        for layerName in layers:
            self.removeLayer(layerName, ext)

    def removeLayer(self, name, ext=".shp"):
        try: #QGis 3.x
            layers = [tree_layer.layer() for tree_layer in QgsProject.instance().layerTreeRoot().findLayers()]
        except: #QGis 2.x
            layers = self.iface.legendInterface().layers()
        for layer in layers:
            if str(layer.dataProvider().dataSourceUri().split("|")[0])== os.path.join(self.ProjectDirectory, self.NetworkName + "_" + name + ext):
                try: #QGis 3.x
                    QgsProject.instance().removeMapLayer(layer.id())
                except: #QGis 2.x
                    QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
        self.iface.mapCanvas().refresh()
        del layers

    def writeFile(self, file, string):
        try: #QGis 2.x !!!!!!
            file.write(string.encode('utf-8'))
        except:
            file.write(string)

    def setStyle(self, layer, name):
        if name=="":
            return
        stylePath = os.path.join(os.path.dirname(__file__), "layerStyles")
        
        qmlPath= os.path.join(stylePath, name + ".qml")
        if os.path.exists(qmlPath):
            ret = layer.loadNamedStyle(qmlPath)
        
        svgPath= os.path.join(stylePath, name + ".svg")
        if os.path.exists(svgPath):
            render = None
            if layer.geometryType()==0: #Point
                svg_style = dict()
                svg_style['name'] = svgPath
                svg_style['size'] = str(7)
                symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.changeSymbolLayer(0, symbol_layer)
                renderer = QgsSingleSymbolRenderer(symbol)
            else: #Line
                symbol = QgsLineSymbol().createSimple({})
                symbol.deleteSymbolLayer(0)
                # Line
                lineSymbol = QgsSimpleLineSymbolLayer()
                lineSymbol.setWidthUnit(2) #Pixels
                lineSymbol.setWidth(1.5)
                symbol.appendSymbolLayer(lineSymbol)
                # Symbol
                marker = QgsMarkerSymbol.createSimple({})
                marker.deleteSymbolLayer(0)
                svg_props = dict()
                svg_props['name'] = svgPath
                svg_props['size'] = str(6)
                markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
                marker.appendSymbolLayer(markerSymbol)
                # Final Symbol
                finalMarker = QgsMarkerLineSymbolLayer()
                finalMarker.setSubSymbol(marker)
                finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
                symbol.appendSymbolLayer(finalMarker)
                renderer = QgsSingleSymbolRenderer(symbol)
            
            try: #QGis 3.x
                layer.setRenderer(renderer)
            except: #QGis 2.x
                layer.setRendererV2(renderer)

    def setResultStyle(self, layer):
        stylePath = os.path.join(os.path.dirname(__file__), "layerStyles")
        
        v=""
        if str(Qgis.QGIS_VERSION).startswith('2'): #QGis 2.x
            v="2"
        
        if layer.geometryType()==0: #Point
            qmlBasePath= os.path.join(stylePath, "nodeResults" + v +"Base.qml")
        else:
            qmlBasePath= os.path.join(stylePath, "linkResultsBase.qml")
        if os.path.exists(qmlBasePath):
            f=open(qmlBasePath, "r")
            contents =f.read()
            f.close()
            qmlPath=""
            if layer.geometryType()==0: #Point
                svgPath= os.path.join(stylePath, "tanksResults.svg")
                contents = contents.replace("tanks.svg", svgPath)
                svgPath= os.path.join(stylePath, "reservoirsResults.svg")
                contents = contents.replace("reservoirs.svg", svgPath)
                qmlPath= os.path.join(stylePath, "nodeResults.qml")
            else:
                svgPath= os.path.join(stylePath, "pumps.svg")
                contents = contents.replace("pumps.svg", svgPath)
                svgPath= os.path.join(stylePath, "valves.svg")
                contents = contents.replace("valves.svg", svgPath)
                qmlPath= os.path.join(stylePath, "linkResults.qml")
            f=open(qmlPath, "w+")
            f.write(contents)
            f.close()
            ret = layer.loadNamedStyle(qmlPath)
        
        # try: # QGis 3
            # symbol = layer.renderer().symbol() 
        # except: # QGis 2
            # symbol = layer.rendererV2().symbols()[0] 
        # if layer.geometryType()==0: #Point
            # #Reservoir:
            # svgPath= os.path.join(stylePath, "reservoirs.svg")
            # svg_style = dict()
            # svg_style['name'] = svgPath
            # svg_style['size'] = str(7)
            # svg_style['size_dd_expression'] = "if(""Type"" ='RESERVOIR', 7,0)"
            # symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
            # #symbol = layer.rendererV2().symbols()[0] 
            # symbol.changeSymbolLayer(1, symbol_layer) #1=reservoir
            # #Tank:
            # svgPath= os.path.join(stylePath, "tanks.svg")
            # svg_style = dict()
            # svg_style['name'] = svgPath
            # svg_style['size'] = str(7)
            # svg_style['size_dd_expression'] = "if(""Type"" ='TANK', 7,0)"
            # symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
            # #symbol = layer.rendererV2().symbols()[0] 
            # symbol.changeSymbolLayer(0, symbol_layer) #0=Tank
        # else: #Line
            # #Pump
            # svgPath= os.path.join(stylePath, "pumps.svg")
            # marker = QgsMarkerSymbol.createSimple({})
            # marker.deleteSymbolLayer(0)
            # svg_props = dict()
            # svg_props['name'] = svgPath
            # svg_props['size'] = str(6)
            # svg_props['size_dd_expression'] = "if(""Type"" ='PUMP', 6,0)"
            # markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
            # marker.appendSymbolLayer(markerSymbol)
            # finalMarker = QgsMarkerLineSymbolLayer()
            # finalMarker.setSubSymbol(marker)
            # finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
            # symbol.appendSymbolLayer(finalMarker)
            # #Valve
            # svgPath= os.path.join(stylePath, "valves.svg")
            # marker = QgsMarkerSymbol.createSimple({})
            # marker.deleteSymbolLayer(0)
            # svg_props = dict()
            # svg_props['name'] = svgPath
            # svg_props['size'] = str(6)
            # svg_props['size_dd_expression'] = "if(""Type"" ='VALVE', 6,0)"
            # markerSymbol = QgsSvgMarkerSymbolLayer.create(svg_props)
            # marker.appendSymbolLayer(markerSymbol)
            # finalMarker = QgsMarkerLineSymbolLayer()
            # finalMarker.setSubSymbol(marker)
            # finalMarker.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
            # symbol.appendSymbolLayer(finalMarker)
        # layer.triggerRepaint()

