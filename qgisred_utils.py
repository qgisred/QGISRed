try: #QGis 3.x
    from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayer, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer
except: #QGis 2.x
    from qgis.core import QgsSvgMarkerSymbolLayerV2 as QgsSvgMarkerSymbolLayer, QgsSymbolV2 as QgsSymbol, QgsSingleSymbolRendererV2 as QgsSingleSymbolRenderer, QgsLineSymbolV2 as QgsLineSymbol
    from qgis.core import QgsSimpleLineSymbolLayerV2 as QgsSimpleLineSymbolLayer, QgsMarkerSymbolV2 as QgsMarkerSymbol, QgsMarkerLineSymbolLayerV2 as QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayerV2 as QgsSimpleMarkerSymbolLayer

import os

class QGISRedUtils:

    def __init__(self):
        pass

    def writeFile(self, file, string):
        try: #QGis 2.x !!!!!!
            file.write(string.encode('utf-8'))
        except:
            file.write(string)

    def setStyle(self, layer, name, type):
        if name=="":
            return
        stylePath = os.path.join(os.path.dirname(__file__), "layerStyles")
        svgPath= os.path.join(stylePath, name + ".svg")
        if os.path.exists(svgPath):
            render = None
            if type=="point":
                svg_style = dict()
                svg_style['name'] = svgPath
                svg_style['size'] = str(7)
                symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
                symbol = QgsSymbol.defaultSymbol(layer.geometryType())
                symbol.changeSymbolLayer(0, symbol_layer)
                renderer = QgsSingleSymbolRenderer(symbol)
            else:
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
        else:
            ret = layer.loadNamedStyle(os.path.join(stylePath, name + ".qml"))