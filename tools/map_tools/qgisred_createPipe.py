from qgis.gui import QgsVertexMarker
from .qgisred_createLineTool import QGISRedCreateLineTool
from ...compat import SNAP_TYPE_VERTEX


class QGISRedCreatePipeTool(QGISRedCreateLineTool):
    MARKER_ICON = QgsVertexMarker.ICON_BOX
    MARKER_SIZE = 15
    SNAP_TYPE = SNAP_TYPE_VERTEX
    SNAP_TO_SEGMENTS = False
    SHOW_GRID = False
