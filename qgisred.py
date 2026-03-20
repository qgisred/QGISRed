# -*- coding: utf-8 -*-
"""QGISRed plugin main class — thin orchestrator using multiple inheritance from Section classes."""

from .sections.lifecycle_section import LifecycleSection
from .sections.menu_section import MenuSection
from .sections.project_management_section import ProjectManagementSection
from .sections.layer_management_section import LayerManagementSection
from .sections.utils_section import UtilsSection
from .sections.network_editing_section import NetworkEditingSection
from .sections.analysis_section import AnalysisSection
from .sections.debug_validation_section import DebugValidationSection
from .sections.tools_section import ToolsSection
from .sections.digital_twin_section import DigitalTwinSection
from .sections.queries_section import QueriesSection
from .sections.segment_tree_section import SegmentTreeSection


class QGISRed(
    LifecycleSection,
    MenuSection,
    ProjectManagementSection,
    LayerManagementSection,
    UtilsSection,
    NetworkEditingSection,
    AnalysisSection,
    DebugValidationSection,
    ToolsSection,
    DigitalTwinSection,
    QueriesSection,
    SegmentTreeSection,
):
    """QGISRed Plugin Implementation."""

    # Common class-level variables shared across all sections via self.*
    ResultDockwidget = None
    ProjectDirectory = ""
    NetworkName = ""
    ownMainLayers = ["Pipes", "Junctions", "Demands", "Valves", "Pumps", "Tanks", "Reservoirs", "Sources"]
    ownFiles = ["DefaultValues", "Options", "Rules", "Controls", "Curves", "Patterns", "Materials", "Signals"]
    especificComplementaryLayers = []
    complementaryLayers = ["IsolationValves", "Hydrants", "WashoutValves", "AirReleaseValves", "ServiceConnections", "Meters"]
    TemporalFolder = "Temporal folder"
    DependenciesVersion = "1.0.17.2"
    gisredDll = None
