# -*- coding: utf-8 -*-
"""
Sections for QGISRed plugin.
Each section is a class intended to be used as a base class (multiple inheritance)
for the main QGISRed class. They are not intended to be instantiated directly.
"""
from .lifecycle_section import LifecycleSection
from .menu_section import MenuSection
from .project_management_section import ProjectManagementSection
from .layer_management_section import LayerManagementSection
from .utils_section import UtilsSection
from .network_editing_section import NetworkEditingSection
from .analysis_section import AnalysisSection
from .debug_validation_section import DebugValidationSection
from .tools_section import ToolsSection
from .digital_twin_section import DigitalTwinSection
from .queries_section import QueriesSection
from .segment_tree_section import SegmentTreeSection

__all__ = [
    "LifecycleSection",
    "MenuSection",
    "ProjectManagementSection",
    "LayerManagementSection",
    "UtilsSection",
    "NetworkEditingSection",
    "AnalysisSection",
    "DebugValidationSection",
    "ToolsSection",
    "DigitalTwinSection",
    "QueriesSection",
    "SegmentTreeSection",
]
