from qgis.gui import QgsVertexMarker
from .qgisred_createLineTool import QGISRedCreateLineTool


class QGISRedCreateConnectionTool(QGISRedCreateLineTool):
    MARKER_ICON = QgsVertexMarker.ICON_X
    MARKER_SIZE = 10
    SNAP_TYPE = 3       # Segment
    SNAP_TO_SEGMENTS = True
    SHOW_GRID = True
