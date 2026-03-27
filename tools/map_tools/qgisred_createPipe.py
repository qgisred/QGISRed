from qgis.gui import QgsVertexMarker
from .qgisred_createLineTool import QGISRedCreateLineTool


class QGISRedCreatePipeTool(QGISRedCreateLineTool):
    MARKER_ICON = QgsVertexMarker.ICON_BOX
    MARKER_SIZE = 15
    SNAP_TYPE = 1       # Vertex
    SNAP_TO_SEGMENTS = False
    SHOW_GRID = True
