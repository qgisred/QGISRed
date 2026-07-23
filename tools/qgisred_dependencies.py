from .dependencies._base import QGISRedBase
from .dependencies._project_management import QGISRedProjectManagementMixin
from .dependencies._network_editing import QGISRedNetworkEditingMixin
from .dependencies._analysis import QGISRedAnalysisMixin
from .dependencies._validation import QGISRedValidationMixin
from .dependencies._lifecycle import QGISRedLifecycleMixin
from .dependencies._digital_twin import QGISRedDigitalTwinMixin
from .dependencies._layer_management import QGISRedLayerManagementMixin
from .dependencies._tools import QGISRedToolsMixin


class QGISRedDependencies(
    QGISRedProjectManagementMixin,
    QGISRedNetworkEditingMixin,
    QGISRedAnalysisMixin,
    QGISRedValidationMixin,
    QGISRedLifecycleMixin,
    QGISRedDigitalTwinMixin,
    QGISRedLayerManagementMixin,
    QGISRedToolsMixin,
    QGISRedBase,
):
    pass
