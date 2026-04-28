from qgis.gui import QgsVertexMarker
from .qgisred_createLineTool import QGISRedCreateLineTool
from ...compat import SNAP_TYPE_BOTH


class QGISRedCreateConnectionTool(QGISRedCreateLineTool):
    MARKER_ICON = QgsVertexMarker.ICON_X
    MARKER_SIZE = 10
    SNAP_TYPE = SNAP_TYPE_BOTH
    SNAP_TO_SEGMENTS = True
    SHOW_GRID = True
