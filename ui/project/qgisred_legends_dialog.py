# -*- coding: utf-8 -*-

from contextlib import suppress
import os
import re
import json
import random
import math
import statistics
import xml.etree.ElementTree as ET  # nosec B405 — parses a local settings file written by this plugin

from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QHeaderView, QLineEdit, QAbstractItemView
from qgis.PyQt.QtWidgets import QCheckBox, QSpinBox, QApplication, QProgressDialog, QWidget, QHBoxLayout, QMenu
from qgis.PyQt.QtCore import Qt, QTimer, QEvent
from qgis.PyQt import uic
from ...compat import (
    QVariantInt, QVariantDouble, QVariantLongLong,
    QGIS_INFO, QGIS_WARNING,
    SL_PROP_SIZE, SL_PROP_WIDTH, SL_PROP_FILL_COLOR, SL_PROP_STROKE_COLOR, SL_PROP_STROKE_WIDTH,
    PAL_PROPERTY_COLOR,
)

from qgis.core import QgsProject, QgsVectorLayer, QgsMessageLog, QgsGraduatedSymbolRenderer
from qgis.core import QgsCategorizedSymbolRenderer, QgsRendererRange, QgsRendererCategory, QgsSymbol
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGradientColorRamp, QgsClassificationJenks
from qgis.core import QgsClassificationPrettyBreaks, QgsStyle, QgsPresetSchemeColorRamp, QgsProperty
from qgis.core import QgsRuleBasedRenderer, QgsFillSymbolLayer, QgsMapLayerStyle, QgsRandomColorRamp, NULL
from qgis.core import QgsLineSymbol, QgsMarkerSymbol, QgsFillSymbol
from qgis.utils import iface

from ...compat import WKB_LINE_GEOMETRY, WKB_POINT_GEOMETRY
from ...tools.utils.qgisred_styling_utils import _NULL_RULE_LABEL, QGISRedStylingUtils
from ...tools.utils.qgisred_legend_rule_utils import (
    OPEN_RANGE_BOUND as _OPEN_RANGE_BOUND,
    parseCategoricalRuleFilter,
    parseRangeFilter as _parseRangeFilter,
    unwrapClassAttribute as _unwrapClassAttribute,
)
from ...tools.utils.qgisred_ui_utils import QGISRedUIUtils, QGISRedBanner
from ...tools.utils.qgisred_identifier_utils import QGISRedIdentifierUtils
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils, resolve_layer_id
from ...tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ...tools.utils.qgisred_project_utils import QGISRedProjectUtils
from ...tools.utils.qgisred_filesystem_utils import QGISRedFileSystemUtils, DIR_RESULTS
from ..analysis.qgisred_results_data import resultStyleName
from ..analysis.qgisred_results_rendering import apply_junction_size, read_node_base_sizes
from .qgisred_custom_dialogs import QGISRedRangeEditDialog, QGISRedSymbolColorSelector
from .qgisred_custom_dialogs import QGISRedColorRampSelector, QGISRedRowSelectionFilter
from .qgisred_custom_dialogs import QGISRedPaletteEmulator, QGISRedSizePaletteEmulator
from .qgisred_custom_dialogs import QGISRedSaveStrategyDialog

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_legends_dialog.ui"))

# Flannery-like exponent used by the shipped proportional size themes (e.g. JunctionTotalBaseDemands)
PROPORTIONAL_SIZE_EXPONENT = 0.57


def formatExpressionNumber(value, precision=3):
    """Format a number for use inside a QGIS expression, trimming trailing zeros."""
    rounded = round(float(value), precision)
    if rounded == int(rounded):
        return str(int(rounded))
    return repr(rounded)


def substituteCapturedGroup(expr, pattern, newText):
    """Replace group 1 of every match of pattern inside expr with newText.

    Leaves the rest of the expression untouched, so wrapper constructs like
    coalesce(...) or with_variable(...) survive. Returns (newExpr, changed).
    """
    if not expr:
        return expr, False
    compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
    parts = []
    last = 0
    changed = False
    for match in compiled.finditer(expr):
        start, end = match.span(1)
        if start < 0:
            continue
        parts.append(expr[last:start])
        parts.append(newText)
        last = end
        changed = True
    if not changed:
        return expr, False
    parts.append(expr[last:])
    return "".join(parts), True


_NUMERIC_LITERAL_PATTERN = re.compile(r"(?<![\w.'])\d+(?:\.\d+)?(?![\w.'])")


def scaleNumericLiterals(expr, scale, precision=3):
    """Scale every bare numeric literal in a size expression, keeping its structure.

    Zeros stay zero, so branches that hide a symbol layer are preserved.
    """
    def replaceLiteral(match):
        return formatExpressionNumber(float(match.group(0)) * scale, precision)

    return _NUMERIC_LITERAL_PATTERN.sub(replaceLiteral, expr)


_METER_TYPE_PATTERN = re.compile(r"(?:@mt|\"?Type\"?)\s*=\s*'([^']+)'")
_METER_TYPE_SIZE_PATTERN = re.compile(r"((?:@mt|\"?Type\"?)\s*=\s*'[^']+'\s*,\s*)(\d+(?:\.\d+)?)")
_METER_NULL_SIZE_PATTERN = re.compile(r"((?:@mt|\"?Type\"?)\s+is\s+NULL\s*,\s*)(\d+(?:\.\d+)?)")


def extractMeterTypeFromExpression(expr):
    """Return the meter type gating a Meters size/width expression, or None."""
    match = _METER_TYPE_PATTERN.search(expr or "")
    return match.group(1) if match else None


def rewriteMeterSizeExpression(expr, newSize, onlyType=None):
    """Rewrite the visible-size literals of a Meters type-gate expression in place.

    Handles both the legacy flat form (if (Type = 'X', 5, 0)) and the shipped
    with_variable('mt', coalesce("MeterType", "Type"), ...) form without
    touching the wrapper. Zero literals (the "hide this layer" branches) are
    preserved; the non-zero NULL branch (Manometer default) follows the new
    size. Returns (newExpr, meterType); expr is returned unchanged when the
    layer's type does not match onlyType.
    """
    meterType = extractMeterTypeFromExpression(expr)
    if meterType is None:
        return expr, None
    if onlyType is not None and meterType != onlyType:
        return expr, meterType
    sizeText = formatExpressionNumber(newSize)

    def replaceTypeBranch(match):
        return match.group(1) + sizeText

    def replaceNullBranch(match):
        if float(match.group(2)) == 0:
            return match.group(0)
        return match.group(1) + sizeText

    newExpr = _METER_TYPE_SIZE_PATTERN.sub(replaceTypeBranch, expr)
    newExpr = _METER_NULL_SIZE_PATTERN.sub(replaceNullBranch, newExpr)
    return newExpr, meterType


# Substitution targets inside the shipped style expressions. Each pattern captures
# exactly the color/size literal to replace as group 1; everything around it stays.
SERVICE_CONNECTION_ACTIVE_STROKE_PATTERNS = (
    re.compile(r"IsActive\s+is\s+NULL\s*,\s*'(#[0-9a-fA-F]{3,6})'"),
    re.compile(r"IsActive\s*>\s*0\s*,\s*'(#[0-9a-fA-F]{3,6})'"),
)
SERVICE_CONNECTION_ACTIVE_FILL_PATTERN = re.compile(
    r"IsActive\s+is\s+NULL\s+or\s+IsActive\s*>\s*0\s*,\s*'(#[0-9a-fA-F]{3,6})'"
)
ISOLATION_VALVE_GREEN_PATTERN = re.compile(
    r"\"?LossCoeff\"?\s*=\s*0\s*,\s*(color_rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\))"
)
# The shipped Isolation Valves fill expression (defaults/layerStyles/IsolationValves.qml.bak):
# red when closed, {green} when open without loss, amber with loss, grey when
# not available. Used to restore the expression on symbols that lost it.
ISOLATION_VALVE_FILL_TEMPLATE = (
    'if( "Available"!=0,'
    "if( coalesce(attribute($currentfeature,'IniStatus'),attribute($currentfeature,'Status'))='CLOSED',"
    "color_rgb(255,19,19),"
    ' if("LossCoeff" = 0, {green},color_rgb(246,185,18))),'
    "color_rgb(125,139,143))"
)
# The positive-demand branch of the Multiple Demands fill expression (the
# '#fdbf6f' slot, like Junctions). The negative color and white base stay fixed.
DEMAND_POSITIVE_FILL_PATTERN = re.compile(
    r"(?:@bd|\"?Base(?:Value|Demand|Dem)\"?)\s*>\s*0\s*,\s*'(#[0-9a-fA-F]{3,6})'"
)
METER_ACTIVE_FILL_PATTERNS = (
    re.compile(r"IsActive\s+is\s+NULL\s*,\s*'(#[0-9a-fA-F]{3,6})'"),
    re.compile(r"IsActive\s*!=\s*0\s*,\s*'(#[0-9a-fA-F]{3,6})'"),
)


class QGISRedLegendsDialog(QDialog, formClass):
    FIELD_TYPE_NUMERIC = "numeric"
    FIELD_TYPE_CATEGORICAL = "categorical"
    FIELD_TYPE_UNKNOWN = "unknown"
    FIELD_TYPE_SINGLE = "single"

    WARN_CLASSES = 50
    MAX_CLASSES = 1000

    # Same size used by QGISRED_COMBO_STYLE, so every input matches the comboboxes
    CONTROL_FONT_SIZE = "8pt"

    ALLOWED_GROUP_IDENTIFIERS = [
        "qgisred_thematicmaps",
        "qgisred_results",
        "qgisred_inputs",
        "qgisred_connectivity",
        "qgisred_hydraulicsectors",
        "qgisred_demandsectors",
        "qgisred_isolatedsegments",
        "qgisred_demandbuilder"
    ]

    # Only these Demand Builder layers are editable in the Legend Editor
    DEMANDS_BUILDER_EDITABLE_IDENTIFIERS = {
        "qgisred_demandbuilder_consumptionpoints",
        "qgisred_demandbuilder_demandlinks",
    }

    QUERIES_GROUP_PREFIXES = (
        "qgisred_connectivity",
        "qgisred_hydraulicsectors",
        "qgisred_demandsectors",
        "qgisred_isolatedsegments",
    )

    # Query layers editable as a single symbol but restricted to size changes only.
    # Their colors are driven by data-defined expressions (Status/ElemType/...),
    # so a generic color edit would be invisible yet destructive.
    SIZE_ONLY_QUERY_IDENTIFIERS = {
        "qgisred_tree_nodes",
        "qgisred_isolatedsegments_links",
        "qgisred_isolatedsegments_nodes",
        "qgisred_isolatedsegments_isolateddemands",
        "qgisred_hydraulicsectors_isolateddemands",
    }

    # Exception among the size-only layers: Tree nodes also take a color, applied
    # to the outer circle's stroke only (the star and element icons keep theirs).
    TREE_NODES_IDENTIFIER = "qgisred_tree_nodes"

    # Query layers editable as a single symbol (color and size)
    SINGLE_EDITABLE_QUERY_IDENTIFIERS = {"qgisred_connectivity_links"}

    # Every singleSymbol query layer the dialog can edit. The layers-panel gate and
    # detectFieldType must accept exactly what the group enumeration lists.
    EDITABLE_QUERY_IDENTIFIERS = SIZE_ONLY_QUERY_IDENTIFIERS | SINGLE_EDITABLE_QUERY_IDENTIFIERS

    # Layer-identifier prefixes of every query family the dialog handles
    QUERY_LAYER_IDENTIFIER_PREFIXES = (
        "qgisred_connectivity",
        "qgisred_hydraulicsectors",
        "qgisred_demandsectors",
        "qgisred_isolatedsegments",
        "qgisred_tree",
        "qgisred_demandbuilder",
    )

    # Meter types gating the stacked SvgMarker layers in the Meters style
    METER_TYPES = (
        "Countermeter",
        "DifferentialManometer",
        "EnergySensor",
        "Flowmeter",
        "LevelSensor",
        "Manometer",
        "QualitySensor",
        "StatusSensor",
        "Tachometer",
        "ValveOpening",
    )

    INPUT_LAYER_IDENTIFIERS = frozenset({
        "qgisred_pipes", "qgisred_pumps", "qgisred_valves",
        "qgisred_junctions", "qgisred_reservoirs", "qgisred_tanks",
        "qgisred_sources", "qgisred_serviceconnections",
        "qgisred_isolationvalves", "qgisred_meters", "qgisred_demands"
    })

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self, parent=None):
        super(QGISRedLegendsDialog, self).__init__(parent)
        self.setupUi(self)
        self.initializeProperties()
        self.initializeUi()
        self.connectSignals()
        self.loadInitialState()

        from qgis.PyQt.QtWidgets import QComboBox
        for combo in self.findChildren(QComboBox):
            QGISRedUIUtils.applyComboStyle(combo)
        self.resizeToFitContents()

    def resizeToFitContents(self):
        # The scroll area adjusts to its contents, so the dialog's own size hint
        # already accounts for the full editor content plus header and buttons.
        hint = self.sizeHint()
        self.resize(max(self.width(), hint.width() + 4), max(self.height(), hint.height() + 4))

    def initializeProperties(self):
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.currentFieldName = None
        self.currentLayer = None
        self.pluginFolder = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.isEditing = True
        self.originalRenderer = None
        self._workingRenderer = None
        self._sourceRuleRenderer = None
        self._syncedSiblingIds = set()
        self.availableUniqueValues = []
        self.usedUniqueValues = []
        self.addClassClickTimer = None
        self.addClassBeforeSelection = False
        self.layerTreeViewConnection = None
        self.layerTreeRoot = None
        self.style = None
        self.lastValidLayerId = None
        self.initialRenderers = {}
        self.isClosing = False
        self.hasAppliedChanges = False

        self.parentPlugin = None
        self.qgisInterface = None
        self.projectDirectory = ""
        self.networkName = ""
        self.utils = None
        self.fieldUtils = None
        self.fsUtils = None
        self.paletteEmulator = QGISRedPaletteEmulator(self)
        self.sizePaletteEmulator = QGISRedSizePaletteEmulator(self)
        self.previousClassificationMode = None
        self.previousSizeMode = None

    # ============================================================
    # RESULTS LAYER DETECTION AND VALUE EXTRACTION
    # ============================================================

    def isResultsLayer(self):
        """Check if the current layer is a results layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            return False
        return identifier.startswith("qgisred_link_") or identifier.startswith("qgisred_node_")

    def isLinkResultLayer(self):
        """Check if current layer is a Link result layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_link_")

    def isNodeResultLayer(self):
        """Check if current layer is a Node result layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier and identifier.startswith("qgisred_node_")

    def isInputLayer(self):
        """Check if the current layer is an input (model element) layer."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            return False
        return identifier in self.INPUT_LAYER_IDENTIFIERS

    def isSizeOnlyQueryLayer(self):
        """Check if the current layer is a query layer editable for size only."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier in self.SIZE_ONLY_QUERY_IDENTIFIERS

    def isSingleEditableQueryLayer(self):
        """Check if the current layer is a query layer editable as a single symbol (color and size)."""
        if not self.currentLayer:
            return False
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return identifier in self.SINGLE_EDITABLE_QUERY_IDENTIFIERS

    def isQueryLayer(self, layer):
        """Check whether the layer belongs to one of the query families by identifier prefix."""
        identifier = layer.customProperty("qgisred_identifier") if layer else None
        return bool(identifier) and identifier.startswith(self.QUERY_LAYER_IDENTIFIER_PREFIXES)

    def getResultFieldMapping(self):
        """Map layer identifier to field name in the 'All' shapefile."""
        mapping = {
            "qgisred_link_flow": "Flow",
            "qgisred_link_velocity": "Velocity",
            "qgisred_link_headloss": "HeadLoss",
            "qgisred_link_unitheadloss": "UnitHeadLo",
            "qgisred_link_status": "Status",
            "qgisred_link_quality": "Quality",
            "qgisred_node_demand": "Demand",
            "qgisred_node_head": "Head",
            "qgisred_node_pressure": "Pressure",
            "qgisred_node_quality": "Quality",
        }
        if not self.currentLayer:
            return None
        identifier = self.currentLayer.customProperty("qgisred_identifier")
        return mapping.get(identifier)

    def getResultsAllShapefilePath(self):
        """Get path to the corresponding 'All' shapefile for results layers."""
        if not self.projectDirectory or not self.networkName:
            return None

        resultsDir = os.path.join(self.projectDirectory, DIR_RESULTS)

        if self.isLinkResultLayer():
            return os.path.join(resultsDir, f"{self.networkName}_Base_Link_All.shp")
        elif self.isNodeResultLayer():
            return os.path.join(resultsDir, f"{self.networkName}_Base_Node_All.shp")
        return None

    def loadResultsAllLayer(self):
        """Load the 'All' shapefile as a temporary QgsVectorLayer."""
        shapefilePath = self.getResultsAllShapefilePath()
        if not shapefilePath or not os.path.exists(shapefilePath):
            return None

        layer = QgsVectorLayer(shapefilePath, "temp_results_all", "ogr")
        return layer if layer.isValid() else None

    def getResultsNumericValues(self):
        """Get numeric values from the 'All' shapefile for results layers."""
        allLayer = self.loadResultsAllLayer()
        if not allLayer:
            return []

        fieldName = self.getResultFieldMapping()
        if not fieldName:
            del allLayer
            return []

        fieldIdx = allLayer.fields().indexOf(fieldName)
        if fieldIdx < 0:
            del allLayer
            return []

        values = []
        for feature in allLayer.getFeatures():
            with suppress(Exception):
                val = float(feature[fieldName])
                values.append(val)

        del allLayer
        return sorted(values)

    def getResultsUniqueValues(self):
        """Get unique values from the 'All' shapefile for categorical results."""
        allLayer = self.loadResultsAllLayer()
        if not allLayer:
            return []

        fieldName = self.getResultFieldMapping()
        if not fieldName:
            del allLayer
            return []

        fieldIdx = allLayer.fields().indexOf(fieldName)
        if fieldIdx < 0:
            del allLayer
            return []

        values = set()
        for feature in allLayer.getFeatures():
            value = feature[fieldName]
            values.add(str(value) if value is not None else "NULL")

        specialValues = ["NULL", "#NA"]
        regularValues = [v for v in values if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in values]

        del allLayer
        return sorted(regularValues) + foundSpecials

    def config(self, qgisInterface, projectDirectory, networkName, parentPlugin):
        self.parentPlugin = parentPlugin
        self.qgisInterface = qgisInterface
        self.projectDirectory = projectDirectory
        self.networkName = networkName
        self.utils = QGISRedIdentifierUtils(projectDirectory, networkName, qgisInterface)
        self.fieldUtils = QGISRedFieldUtils(projectDirectory, networkName, qgisInterface)
        self.fsUtils = QGISRedFileSystemUtils(projectDirectory, networkName, qgisInterface)

        if self.cbLegendLayer.currentLayer():
            self.onLayerChanged(self.cbLegendLayer.currentLayer())

    # ============================================================
    # UI INITIALIZATION
    # ============================================================

    def initializeUi(self):
        self.configureWindow()
        self.setupAppearanceWarning()
        self.setupTableView()
        self.populateClassificationModes()
        self.populateLegendTypes()
        self.populateGroups()
        self.setupClassCountField()
        self.setupClassifyAllButton()
        self.setupMeterTypeCombo()
        self.setupAdvancedUi()
        self.loadStyleDatabase()
        self.applyConsistentStyling()
        self.setupStyleMenus()
        self.setupTooltips()
        self.hideIntervalControls()
        self.installEventFilter(self)
        self.btClassPlus.installEventFilter(self)

    # Row 3 of dialogLayout: right below the caption and above the classes table, which is where
    # the warning has always been shown.
    APPEARANCE_WARNING_ROW = 3

    def setupAppearanceWarning(self):
        """Places the shared QGISRedBanner where the hand-built warning widget used to live."""
        self.appearanceWarningBanner = QGISRedBanner(self)
        self.dialogLayout.insertWidget(self.APPEARANCE_WARNING_ROW, self.appearanceWarningBanner)

    def configureWindow(self):
        self.setWindowIcon(QIcon(":/images/iconThematicMaps.svg"))
        self.setWindowTitle(self.tr("QGISRed: Legend Editor"))
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowCloseButtonHint)
        self.btClassPlus.setIcon(QIcon(":/images/iconClassAdd.svg"))
        self.btClassMinus.setIcon(QIcon(":/images/iconClassRemove.svg"))

    def setupTableView(self):
        self.tableView.setColumnCount(5)
        self.tableView.setHorizontalHeaderLabels(["", self.tr("Color"), self.tr("Size"), self.tr("Value"), self.tr("Legend")])
        self.rowSelectionFilter = QGISRedRowSelectionFilter(self.tableView)

        header = self.tableView.horizontalHeader()

        # Visibility checkbox
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tableView.setColumnWidth(0, 30)

        # Color
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tableView.setColumnWidth(1, 40)

        # Size
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.tableView.setColumnWidth(2, 60)

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Value
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Legend

        self.tableView.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tableView.setAlternatingRowColors(False)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setShowGrid(True)
        self.applyTableStylesheet()

    def applyTableStylesheet(self):
        stylesheet = """
            QTableWidget {background-color: white;gridline-color: #d0d0d0;
            selection-background-color: #3399ff;selection-color: white;border: 1px solid #d0d0d0;
            font-size: %(fontSize)s;}
            QTableWidget::item {border-bottom: 1px solid #d0d0d0;padding: 0px;}
            QTableWidget::item:selected {background-color: #3399ff;}
            QHeaderView::section {background-color: #f0f0f0;padding: 4px;border: 1px solid #d0d0d0;
            font-size: %(fontSize)s;}
        """ % {"fontSize": self.CONTROL_FONT_SIZE}
        self.tableView.setStyleSheet(stylesheet)

    def setupClassCountField(self):
        self.leClassCount.setMinimum(0)
        self.leClassCount.setMaximum(self.MAX_CLASSES)
        self.leClassCount.valueChanged.connect(self.onClassCountChanged)
        self.setClassCountEditable(False)

    def setupClassifyAllButton(self):
        self.btClassifyAll.setIcon(QIcon(":/images/iconClassifyAll.svg"))
        self.btClassifyAll.setToolTip(self.tr("Classify All Unique Values"))
        self.btClassifyAll.clicked.connect(self.classifyAllUniqueValues)

    def setupMeterTypeCombo(self):
        self.cbMeterType.addItem(self.tr("All types"), None)
        for meterType in self.METER_TYPES:
            self.cbMeterType.addItem(meterType, meterType)
        self.cbMeterType.currentIndexChanged.connect(self.onMeterTypeChanged)
        self.labelMeterType.setVisible(False)
        self.cbMeterType.setVisible(False)

    def getSelectedMeterType(self):
        """Return the meter type selected in the dropdown, or None for 'All types'."""
        if not hasattr(self, "cbMeterType"):
            return None
        return self.cbMeterType.currentData()

    def updateMeterTypeControls(self, identifier=None):
        if not hasattr(self, "cbMeterType"):
            return
        isMeters = identifier == "qgisred_meters"
        self.labelMeterType.setVisible(isMeters)
        self.cbMeterType.setVisible(isMeters)
        if not isMeters and self.cbMeterType.currentIndex() != 0:
            self.cbMeterType.blockSignals(True)
            self.cbMeterType.setCurrentIndex(0)
            self.cbMeterType.blockSignals(False)

    def onMeterTypeChanged(self):
        if self.currentLayer and self.currentLayer.customProperty("qgisred_identifier") == "qgisred_meters":
            self.populateLegendTable()

    def setupAdvancedUi(self):
        self.setupSizeControls()
        self.setupColorControls()
        self.setupColorRampButton()
        self.onSizeModeChanged()
        self.onColorModeChanged()

    def setupSizeControls(self):
        sizeModes = [
            "Manual",
            "Equal",
            "Linear",
            "Quadratic",
            "Exponential",
            "Proportional to Value",
        ]

        self.cbSizes.addItems(sizeModes)
        self.cbSizes.currentIndexChanged.connect(self.onSizeModeChanged)
        self.spinSizeEqual.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMin.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.spinSizeMax.valueChanged.connect(self.applySizeLogic)
        self.spinSizeMax.valueChanged.connect(self.updateSizeSpinBoxConstraints)
        self.ckSizeInvert.toggled.connect(self.applySizeLogic)
        self.updateSizeSpinBoxConstraints()

    def setupColorControls(self):
        colorModes = ["Manual", "Equal", "Random", "Ramp", "Palette"]
        self.cbColors.addItems(colorModes)
        self.cbColors.currentIndexChanged.connect(self.onColorModeChanged)
        self.btColorEqual.setColor(QColor("red"))
        self.btColorEqual.colorChanged.connect(self.applyColorLogic)
        self.ckColorInvert.toggled.connect(self.applyColorLogic)
        self.btRefreshColors.setIcon(QIcon(":/images/themes/default/mActionRefresh.svg"))
        self.btRefreshColors.clicked.connect(lambda: self.applyColorLogic(forceRefresh=True))

    def setupColorRampButton(self):
        self.btnColorRamp = QGISRedColorRampSelector(self)
        self.btnColorRamp.setVisible(False)
        self.palletesHorizontalLayout.addWidget(self.btnColorRamp)
        self.btnColorRamp.rampChanged.connect(self.onCustomColorChanged)

    def applyConsistentStyling(self):
        comboStyle = "QComboBox { background-color: white; }"
        spinStyle = (
            "QSpinBox, QDoubleSpinBox { background-color: white; font-size: %s; }" % self.CONTROL_FONT_SIZE
        )

        self.cbGroups.setStyleSheet(comboStyle)
        self.cbLegendLayer.setStyleSheet(comboStyle)
        self.cbMode.setStyleSheet(comboStyle)
        self.cbLegendsType.setStyleSheet(comboStyle)
        self.cbSizes.setStyleSheet(comboStyle)
        self.cbColors.setStyleSheet(comboStyle)

        self.spinIntervalRange.setStyleSheet(spinStyle)
        self.spinSizeEqual.setStyleSheet(spinStyle)
        self.spinSizeMin.setStyleSheet(spinStyle)
        self.spinSizeMax.setStyleSheet(spinStyle)
        self.leClassCount.setStyleSheet(spinStyle)

        self.applySubOptionStyling()

    def applySubOptionStyling(self):
        # Sub-option captions (Min, Max, Value, Interval Range, Invert) read as
        # secondary to the section labels: italic.
        subOptionWidgets = [
            self.labelIntervalRange,
            self.labelSizeValue,
            self.labelSpinMin,
            self.labelSpinMax,
            self.ckSizeInvert,
            self.ckColorInvert,
        ]
        for widget in subOptionWidgets:
            font = widget.font()
            font.setItalic(True)
            widget.setFont(font)

    def setupStyleMenus(self):
        loadMenu = QMenu(self)
        loadMenu.addAction(self.tr("Default Style"), self.loadDefaultStyle)
        loadMenu.addAction(self.tr("Global Style"), self.loadGlobalStyle)
        loadMenu.addAction(self.tr("Project Style"), self.loadProjectStyle)
        loadMenu.addSeparator()
        self.actionRevertOriginal = loadMenu.addAction(self.tr("Revert to Original Legend"), self.revertToOriginalStyle)
        self.actionRevertOriginal.setToolTip(self.tr("Show the legend the layer had when this dialog was opened; press Apply to update the layer"))
        self.btLoadMenu.setMenu(loadMenu)

        saveMenu = QMenu(self)
        saveMenu.setToolTipsVisible(True)
        applyNote = self.tr("Saves the legend as shown in the dialog; the layer itself only changes with Apply")
        actionSaveGlobal = saveMenu.addAction(self.tr("To Global…"), self.saveGlobalStyle)
        actionSaveGlobal.setToolTip(applyNote)
        actionSaveProject = saveMenu.addAction(self.tr("To Project…"), self.saveProjectStyle)
        actionSaveProject.setToolTip(applyNote)
        self.btSaveMenu.setMenu(saveMenu)

    def setupTooltips(self):
        self.btUp.setToolTip(self.tr("Move selected class up"))
        self.btDown.setToolTip(self.tr("Move selected class down"))
        self.btClassMinus.setToolTip(self.tr("Remove selected class(es)"))
        self.btClassifyAll.setToolTip(self.tr("Add all unique values as separate classes"))

        if hasattr(self, "btRefreshColors"):
            self.btRefreshColors.setToolTip(self.tr("Refresh color ramp"))

        self.btLoadMenu.setToolTip(self.tr("Load a saved style or revert to the original legend"))
        self.btSaveMenu.setToolTip(self.tr("Save the current legend as a style"))
        self.btAcceptLegend.setToolTip(self.tr("Apply changes to layer and close"))
        self.btApplyLegend.setToolTip(self.tr("Apply changes to layer"))
        self.btCancelLegend.setToolTip(self.tr("Close and restore the legend the layer had when this dialog was opened"))

    def hideIntervalControls(self):
        self.labelIntervalRange.setVisible(False)
        self.spinIntervalRange.setVisible(False)

    def loadStyleDatabase(self):
        self.style = QgsStyle()
        dbPath = os.path.join(self.pluginFolder, "defaults", "symbology-style_QGISRed.db")

        if os.path.exists(dbPath):
            try:
                success = self.style.load(dbPath)
                if not success:
                    QgsMessageLog.logMessage(
                        f"Failed to load style database: {dbPath}",
                        "QGISRed",
                        QGIS_WARNING,
                    )
            except Exception as e:
                QgsMessageLog.logMessage(
                    f"Error loading style database: {str(e)}",
                    "QGISRed",
                    QGIS_WARNING,
                )
        else:
            QgsMessageLog.logMessage(
                f"Style database not found: {dbPath}",
                "QGISRed",
                QGIS_INFO,
            )

    # ============================================================
    # SIGNAL CONNECTIONS
    # ============================================================

    def connectSignals(self):
        self.cbGroups.currentIndexChanged.connect(self.onGroupChanged)
        self.cbLegendLayer.layerChanged.connect(self.onLayerChanged)
        self.btAcceptLegend.clicked.connect(self.acceptAndClose)
        self.btApplyLegend.clicked.connect(self.applyLegend)
        self.btCancelLegend.clicked.connect(self.cancelAndClose)
        self.cbMode.currentIndexChanged.connect(self.onModeChanged)
        self.cbLegendsType.currentIndexChanged.connect(self.onLegendTypeChanged)
        self.spinIntervalRange.valueChanged.connect(self.onIntervalRangeChanged)
        self.btClassPlus.clicked.connect(self.onAddClassClicked)
        self.btClassMinus.clicked.connect(self.removeClass)
        self.btUp.clicked.connect(self.moveClassUp)
        self.btDown.clicked.connect(self.moveClassDown)
        self.tableView.cellDoubleClicked.connect(self.onCellDoubleClicked)
        self.tableView.itemSelectionChanged.connect(self.updateButtonStates)
        self.connectLayerTreeSignal()

    def connectLayerTreeSignal(self):
        if iface and iface.layerTreeView():
            self.layerTreeViewConnection = iface.layerTreeView().currentLayerChanged.connect(self.onQgisLayerSelectionChanged)

    def loadInitialState(self):
        self.labelFrameLegends.setText(self.tr("Legend"))
        # Projects saved by older builds carry doubled Tree layer identifiers
        # (qgisred_qgisred_...), which none of the identifier gates recognize.
        QGISRedIdentifierUtils.repairDoubledIdentifiers()
        # preselectGroupAndLayer -> onGroupChanged already runs the full layer
        # selection (populate, legend types, label) exactly once.
        self.preselectGroupAndLayer()
        self.frameLegends.setEnabled(bool(self.cbLegendLayer.currentLayer()))
        self.updateClassCount()

    # ============================================================
    # EVENT HANDLERS - LAYER AND GROUP
    # ============================================================

    def onQgisLayerSelectionChanged(self, layer):
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        layerNode = QgsProject.instance().layerTreeRoot().findLayer(layer)
        if not layerNode:
            return

        groupPath = self.findGroupPathForLayer(layerNode)
        if not groupPath:
            return

        rendererType = layer.renderer().type() if layer.renderer() else ""
        if rendererType not in ("graduatedSymbol", "categorizedSymbol", "RuleRenderer"):
            if rendererType != "singleSymbol":
                return
            identifier = layer.customProperty("qgisred_identifier") or ""
            isResultLayer = identifier.startswith("qgisred_link") or identifier.startswith("qgisred_node")
            isInputLayer = identifier in self.INPUT_LAYER_IDENTIFIERS
            isEditableQuery = identifier in self.EDITABLE_QUERY_IDENTIFIERS
            if not isResultLayer and not isInputLayer and not isEditableQuery:
                return

        currentGroupPath = self.cbGroups.currentData()
        if currentGroupPath != groupPath:
            self.setGroupByPath(groupPath)
            self.onGroupChanged()

        if self.cbLegendLayer.currentLayer() != layer:
            self.cbLegendLayer.setLayer(layer)

    def onGroupChanged(self):
        allowedLayers = self.getRenderableLayersInSelectedGroup()
        allLayers = list(QgsProject.instance().mapLayers().values())
        exceptedLayers = [layer for layer in allLayers if layer not in allowedLayers]

        targetLayer = self.determineTargetLayer(allowedLayers)

        self.cbLegendLayer.blockSignals(True)
        # Filter first: setExceptedLayerList resets the combo's model, and clearing
        # the index afterwards keeps the combo blank when the group has no target.
        self.cbLegendLayer.setExceptedLayerList(exceptedLayers)
        self.cbLegendLayer.setCurrentIndex(-1)
        if targetLayer:
            self.cbLegendLayer.setLayer(targetLayer)
        self.cbLegendLayer.blockSignals(False)
        self.onLayerChanged(targetLayer)

    def determineTargetLayer(self, allowedLayers):
        currentLayer = self.cbLegendLayer.currentLayer()
        targetLayer = None

        activeNode = self.getActiveLayerFromTree()
        if activeNode:
            activeLayer = activeNode.layer()
            if activeLayer in allowedLayers:
                targetLayer = activeLayer

        if targetLayer is None and self.lastValidLayerId:
            for layer in allowedLayers:
                if layer.id() == self.lastValidLayerId:
                    targetLayer = layer
                    break

        if targetLayer is None and currentLayer and currentLayer in allowedLayers:
            targetLayer = currentLayer

        if targetLayer is None and allowedLayers:
            targetLayer = allowedLayers[0]

        return targetLayer

    def onLayerChanged(self, layer):
        if layer and isinstance(layer, QgsVectorLayer):
            self.handleValidLayerSelection(layer)
        else:
            self.resetToEmptyState()

    def handleValidLayerSelection(self, layer):
        self.lastValidLayerId = layer.id()
        self.currentLayer = layer
        self._workingRenderer = None
        self.originalRenderer = layer.renderer().clone() if layer.renderer() else None
        # Pristine snapshot for "Revert to Original Legend": taken once per layer,
        # never touched by Apply/Save (unlike originalRenderer).
        if layer.id() not in self.initialRenderers:
            self.initialRenderers[layer.id()] = self.originalRenderer.clone() if self.originalRenderer else None
        self.currentFieldType, self.currentFieldName = self.detectFieldType(layer)
        self.frameLegends.setEnabled(True)

        self.updateMeterTypeControls(layer.customProperty("qgisred_identifier"))
        self.updateFrameLegendLabel(layer)
        self.populateLegendTypes(layer)
        self.syncLegendTypeComboBox(layer)
        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        self.populateLegendTable()
        self.updateButtonStates()
        self.updateInputLayerRestrictions()
        self.updateAppearanceWarning()

    def updateFrameLegendLabel(self, layer):
        layerName = layer.name()
        prefix = self.tr("Legend for")
        boldLayer = f"<b><span style='font-size:larger'>{layerName}</span></b>"
        units = self.getLayerUnits()

        if units:
            self.labelFrameLegends.setText(f"{prefix} {boldLayer} | {units} units")
        else:
            self.labelFrameLegends.setText(f"{prefix} {boldLayer}")

    def syncLegendTypeComboBox(self, layer, renderer=None):
        renderer = renderer if renderer is not None else layer.renderer()
        rendererType = renderer.type()
        if rendererType == "RuleRenderer":
            rendererType = "categorizedSymbol" if self.ruleBasedAsCategories(renderer) else "graduatedSymbol"
        index = self.cbLegendsType.findData(rendererType)

        if index != -1:
            self.cbLegendsType.blockSignals(True)
            self.cbLegendsType.setCurrentIndex(index)
            self.cbLegendsType.blockSignals(False)

    def populateLegendTable(self):
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.populateNumericLegend()
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.populateCategoricalLegend()
        elif self.currentFieldType == self.FIELD_TYPE_SINGLE:
            self.populateSingleSymbolLegend()
        else:
            self.clearTable()

    # ============================================================
    # EVENT HANDLERS - MODE AND TYPE CHANGES
    # ============================================================

    def onModeChanged(self):
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC or not self.currentLayer:
            return

        self.updateUiBasedOnFieldType()
        methodId = self.cbMode.currentData()

        if self.previousClassificationMode is None and methodId is not None:
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)

        # Capture anchor sizes when transitioning TO automatic interval mode while size mode is manual
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        wasManualIntervalMode = self.previousClassificationMode is None or self.previousClassificationMode == "Manual"
        isNowAutomaticIntervalMode = methodId is not None and methodId != "Manual"

        if wasManualIntervalMode and isNowAutomaticIntervalMode and sizeMode == "Manual":
            currentSizes = self.collectCurrentTableSizes()
            if len(currentSizes) >= 2:
                self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)

        self.previousClassificationMode = methodId

        if not methodId:
            return

        if methodId == "FixedInterval":
            self.calculateOptimalInterval()

        self.applyClassificationMethod(methodId)

    def onIntervalRangeChanged(self):
        if self.cbMode.currentData() == "FixedInterval":
            self.applyClassificationMethod("FixedInterval")

    def onLegendTypeChanged(self):
        if not self.currentLayer:
            return

        newType = self.cbLegendsType.currentData()
        currentType = self.getCurrentRendererType()

        if newType == currentType:
            return

        field = self.currentFieldName
        # Single-symbol query layers (e.g. Connectivity) have no field yet: pick one.
        if not field and newType == "categorizedSymbol" and self.isSingleEditableQueryLayer():
            field = self._detectQueryClassField()
        if not field and newType in ("categorizedSymbol", "graduatedSymbol"):
            return

        if newType == "categorizedSymbol":
            if not self.validateCategorizedConversion(field, currentType):
                return
            self.convertToCategorized(field)
            self.currentFieldType = self.FIELD_TYPE_CATEGORICAL
            self.currentFieldName = field

        elif newType == "graduatedSymbol":
            if not self.restoreOriginalGraduatedRenderer(field):
                self.convertToGraduated(field)
            self.currentFieldType, self.currentFieldName = self.detectFieldType(
                self.currentLayer
            )
        elif newType == "singleSymbol" and self.isSingleEditableQueryLayer():
            self.restoreOriginalSingleSymbolRenderer()
            self.currentFieldType, self.currentFieldName = self.FIELD_TYPE_SINGLE, None
        else:
            self.currentFieldType, self.currentFieldName = self.detectFieldType(
                self.currentLayer
            )

        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        self.populateLegendTable()

        if newType == "categorizedSymbol" and self.availableUniqueValues:
            self.classifyAllUniqueValues()

        self.updateButtonStates()
        self.updateInputLayerRestrictions()

    def _detectQueryClassField(self):
        """Pick a classification field for query layers styled as a single symbol.

        Prefers 'Class', then 'SubNet', then the first field that is not an id.
        """
        if not self.currentLayer:
            return None
        fields = self.currentLayer.fields()
        for preferred in ("Class", "SubNet"):
            if fields.indexOf(preferred) >= 0:
                return preferred
        for field in fields:
            if field.name().lower() not in ("id", "fid"):
                return field.name()
        return None

    def restoreOriginalSingleSymbolRenderer(self):
        """Preview the pristine single-symbol renderer again after a categorized detour."""
        snapshot = self.initialRenderers.get(self.currentLayer.id()) if self.currentLayer else None
        candidate = None
        if snapshot is not None and snapshot.type() == "singleSymbol":
            candidate = snapshot
        elif self.originalRenderer is not None and self.originalRenderer.type() == "singleSymbol":
            candidate = self.originalRenderer
        if candidate is not None:
            self._workingRenderer = candidate.clone()

    def validateCategorizedConversion(self, field, currentType):
        """Validates if conversion to categorized renderer is allowed based on unique value count."""
        fieldIdx = self.currentLayer.fields().indexOf(field)
        if fieldIdx < 0:
            return True

        uniqueValues = self.currentLayer.uniqueValues(fieldIdx)
        uniqueCount = len([v for v in uniqueValues if v is not None and str(v) != "NULL"])

        if uniqueCount > self.MAX_CLASSES:
            QMessageBox.critical(
                self,
                self.tr("Too Many Classes"),
                self.tr(
                    f"The field '{field}' has {uniqueCount} unique values.\n"
                    f"The maximum allowed is {self.MAX_CLASSES}.\n"
                    f"Please filter the data or choose a different field."
                ),
            )
            self.revertLegendTypeComboBox(currentType)
            return False

        if uniqueCount > self.WARN_CLASSES:
            reply = QMessageBox.question(
                self,
                self.tr("High Class Count Warning"),
                self.tr(
                    f"The field '{field}' has {uniqueCount} unique values.\n"
                    f"Creating a categorized legend with more than {self.WARN_CLASSES} classes "
                    f"may affect performance and readability.\n\n"
                    f"Do you want to proceed?"
                ),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                self.revertLegendTypeComboBox(currentType)
                return False

        return True

    def revertLegendTypeComboBox(self, previousType):
        self.cbLegendsType.blockSignals(True)
        idx = self.cbLegendsType.findData(previousType)
        if idx >= 0:
            self.cbLegendsType.setCurrentIndex(idx)
        self.cbLegendsType.blockSignals(False)

    def onClassCountChanged(self, newValue):
        if not self.currentLayer or not self.modeHasVariableClassCount():
            return

        currentCount = self.tableView.rowCount()
        if newValue == currentCount:
            return

        self.leClassCount.blockSignals(True)

        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.adjustNumericClassCount(newValue, currentCount)
        elif self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.adjustCategoricalClassCount(newValue, currentCount)

        self.leClassCount.blockSignals(False)

    def adjustNumericClassCount(self, newValue, currentCount):
        isRemoval = newValue < currentCount

        if newValue > currentCount:
            while self.tableView.rowCount() < newValue:
                self.addNumericClass()
        elif newValue < currentCount:
            while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                self.tableView.removeRow(self.tableView.rowCount() - 1)

        self.leClassCount.setValue(self.tableView.rowCount())

        modeId = self.cbMode.currentData()
        if modeId and modeId not in [None, "Manual"] and newValue > currentCount:
            self.applyClassificationMethod(modeId)
        else:
            self.handleColorLogicOnClassChange()
            self.handleSizeLogicOnClassChange(isRemoval=isRemoval)

    def adjustCategoricalClassCount(self, newValue, currentCount):
        isRemoval = newValue < currentCount

        if newValue > currentCount:
            while (
                self.tableView.rowCount() < newValue and self.availableUniqueValues
            ):
                self.addCategoricalClass()
        elif newValue < currentCount:
            while self.tableView.rowCount() > newValue and self.tableView.rowCount() > 0:
                self.removeCategoricalRow(self.tableView.rowCount() - 1)

        self.leClassCount.setValue(self.tableView.rowCount())
        self.updateClassCountLimits()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange(isRemoval=isRemoval)

    def onCellDoubleClicked(self, row, column):
        if column == 2 and self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            self.openRangeEditor(row)

    # ============================================================
    # EVENT HANDLERS - SIZE AND COLOR
    # ============================================================

    def onSizeModeChanged(self):
        mode = self.cbSizes.currentText()
        showEqual = mode == "Equal"
        showMinMax = mode in [
            "Linear",
            "Quadratic",
            "Exponential",
            "Proportional to Value",
        ]

        self.spinSizeEqual.setVisible(showEqual)
        self.labelSizeValue.setVisible(showEqual)
        self.spinSizeMin.setVisible(showMinMax)
        self.spinSizeMax.setVisible(showMinMax)
        self.labelSpinMin.setVisible(showMinMax)
        self.labelSpinMax.setVisible(showMinMax)
        self.ckSizeInvert.setVisible(mode != "Manual" and mode != "Equal")

        # Capture anchor sizes when transitioning TO manual while interval mode is automatic
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"
        wasAutomaticSizeMode = self.previousSizeMode is not None and self.previousSizeMode != "Manual"

        if mode == "Manual" and wasAutomaticSizeMode and isAutomaticIntervalMode:
            currentSizes = self.collectCurrentTableSizes()
            if len(currentSizes) >= 2:
                self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)

        self.previousSizeMode = mode

        self.applySizeLogic()

    def onColorModeChanged(self):
        mode = self.cbColors.currentText()
        self.btColorEqual.setVisible(mode == "Equal")

        isRampOrPalette = mode in ["Ramp", "Palette"]
        self.btnColorRamp.setVisible(isRampOrPalette)
        self.ckColorInvert.setVisible(isRampOrPalette)
        self.btRefreshColors.setVisible(mode == "Random")

        if isRampOrPalette:
            self.syncColorRampButton()

        self.applyColorLogic()

    def onCustomColorChanged(self, ramp):
        self.applyColorLogic()

    def onRowColorChanged(self, _color):
        """Handles when a user manually changes a row's color via the color picker.

        When in automatic interval mode with manual colors, updates the palette
        emulator with current colors so subsequent class additions/removals
        will interpolate from the updated palette.
        """
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and colorMode == "Manual":
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)

    def updateSizeSpinBoxConstraints(self):
        minVal = self.spinSizeMin.value()
        maxVal = self.spinSizeMax.value()

        self.spinSizeMin.blockSignals(True)
        self.spinSizeMax.blockSignals(True)

        self.spinSizeMin.setMaximum(maxVal)
        self.spinSizeMax.setMinimum(minVal)

        self.spinSizeMin.blockSignals(False)
        self.spinSizeMax.blockSignals(False)

    # ============================================================
    # SIZE LOGIC
    # ============================================================

    def applySizeLogic(self):
        if not hasattr(self, "cbSizes"):
            return

        mode = self.cbSizes.currentText()
        if mode == "Manual" or self.tableView.rowCount() == 0:
            return

        rows = self.tableView.rowCount()
        sizes = self.calculateSizesForMode(mode, rows)
        self.applySizesToTable(sizes)

    def calculateSizesForMode(self, mode, rows):
        if mode == "Equal":
            return [self.spinSizeEqual.value()] * rows

        if mode == "Proportional to Value":
            return self.calculateProportionalSizes(rows)

        return self.calculateInterpolatedSizes(mode, rows)

    def calculateProportionalSizes(self, rows):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()

        rangeAverageValues = []
        for row in range(rows):
            rangeValues = self.getRangeValues(row)
            if rangeValues:
                lowerBound, upperBound = rangeValues
                rangeAverageValues.append((lowerBound + upperBound) / 2.0)
            else:
                rangeAverageValues.append(0.0)

        globalValueMin, globalValueMax = self.getLayerMinMax()

        sizes = []
        for averageValue in rangeAverageValues:
            calculatedSize = self.computeProportionalSize(minSize, maxSize, globalValueMin, globalValueMax, averageValue)
            sizes.append(calculatedSize)

        if self.ckSizeInvert.isChecked():
            sizes.reverse()

        return sizes

    def computeProportionalSize(self, minSize, maxSize, globalValueMin, globalValueMax, averageValue):
        valueRange = globalValueMax - globalValueMin
        if valueRange == 0:
            return minSize

        calculatedSize = minSize + ((maxSize - minSize) / valueRange) * (averageValue - globalValueMin)
        return max(minSize, min(maxSize, calculatedSize))

    def calculateInterpolatedSizes(self, mode, rows):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()

        tValues = [i / max(1, rows - 1) for i in range(rows)]

        if self.ckSizeInvert.isChecked():
            tValues.reverse()

        sizes = []
        for t in tValues:
            if mode == "Linear":
                sizes.append(minSize + t * (maxSize - minSize))
            elif mode == "Quadratic":
                sizes.append(minSize + (t * t) * (maxSize - minSize))
            elif mode == "Exponential":
                if rows > 1:
                    factor = (math.exp(t) - 1) / (math.exp(1) - 1)
                    sizes.append(minSize + factor * (maxSize - minSize))
                else:
                    sizes.append(minSize)

        return sizes

    def applySizesToTable(self, sizes):
        for row in range(self.tableView.rowCount()):
            sizeWidget = self.tableView.cellWidget(row, 2)

            if sizeWidget:
                sizeWidget.blockSignals(True)
                sizeWidget.setText(f"{sizes[row]:.2f}")
                sizeWidget.blockSignals(False)

    # ============================================================
    # COLOR LOGIC
    # ============================================================

    def applyColorLogic(self, forceRefresh=False, previousColors=None):
        if not hasattr(self, "cbColors"):
            return

        mode = self.cbColors.currentText()
        rows = self.tableView.rowCount()

        if rows == 0:
            return

        if mode == "Manual":
            if previousColors and len(previousColors) >= 2:
                colors = self.calculateEmulatedPaletteColors(rows, previousColors)
                self.applyColorsToTable(colors)
            return

        colors = self.calculateColorsForMode(mode, rows, forceRefresh)
        self.applyColorsToTable(colors)

    def calculateColorsForMode(self, mode, rows, forceRefresh):
        if mode == "Equal":
            return [self.btColorEqual.color()] * rows

        if mode == "Random":
            return self.calculateRandomColors(rows, forceRefresh)

        if mode == "Ramp":
            return self.calculateRampColors(rows)

        if mode == "Palette":
            return self.calculatePaletteColors(rows)

        return self.generateShuffledRandomColors(rows)

    def calculateRandomColors(self, rows, forceRefresh):
        if forceRefresh:
            return self.generateShuffledRandomColors(rows)

        colors = []
        for row in range(rows):
            existingColor = self.getRowColor(row)
            if existingColor and existingColor.isValid():
                colors.append(existingColor)
            else:
                colors.append(self.generateRandomColor())
        return colors

    def generateShuffledRandomColors(self, count):
        """N visually distinct colors, QGIS "Shuffle Random Colors" style:
        evenly spaced hues from a random offset, pleasant sat/val, shuffled."""
        ramp = QgsRandomColorRamp()
        ramp.setTotalColorCount(count)
        return [ramp.color(0.0 if count <= 1 else i / (count - 1)) for i in range(count)]

    def calculateRampColors(self, rows):
        ramp = self.btnColorRamp.getActiveRampClone()
        if isinstance(ramp, QgsGradientColorRamp):
            colors = self.algorithmRamp(ramp, rows)
        else:
            colors = [self.generateRandomColor() for _ in range(rows)]

        if self.ckColorInvert.isChecked():
            colors.reverse()

        return colors

    def calculatePaletteColors(self, rows):
        palette = self.btnColorRamp.getActiveRampClone()
        if isinstance(palette, QgsPresetSchemeColorRamp):
            colors = self.algorithmPalette(palette, rows)
        else:
            colors = [self.generateRandomColor() for _ in range(rows)]

        if self.ckColorInvert.isChecked():
            colors.reverse()

        return colors

    def calculateEmulatedPaletteColors(self, rows, previousColors):
        """Generates interpolated colors using the palette emulator from existing colors."""
        if self.paletteEmulator.getPaletteCount() >= 2:
            pass
        elif previousColors and len(previousColors) >= 2:
            self.paletteEmulator.setPaletteFromQColors(previousColors)
        else:
            self.paletteEmulator.reset()
            return [self.generateRandomColor() for _ in range(rows)]

        self.paletteEmulator.generate(rows)

        return self.paletteEmulator.getQColorList()

    def applyColorsToTable(self, colors):
        for row in range(self.tableView.rowCount()):
            colorContainer = self.tableView.cellWidget(row, 1)
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
            if colorWidget:
                colorWidget.setSelectorColor(colors[row])

    def collectCurrentTableColors(self):
        """Collects all current colors from the table rows."""
        colors = []
        for row in range(self.tableView.rowCount()):
            color = self.getRowColor(row)
            if color and color.isValid():
                colors.append(color)
        return colors

    def collectCurrentTableSizes(self):
        """Collects all current sizes from the table rows."""
        sizes = []
        for row in range(self.tableView.rowCount()):
            sizeWidget = self.tableView.cellWidget(row, 2)
            if sizeWidget and isinstance(sizeWidget, QLineEdit):
                try:
                    size = float(sizeWidget.text())
                    sizes.append(size)
                except (ValueError, TypeError):
                    sizes.append(0.0)
        return sizes

    def handleColorLogicOnClassChange(self):
        """Handles color logic when adding or removing classes.

        When in automatic interval mode with manual colors, regenerates
        the palette emulation based on current colors and applies it.
        Otherwise, falls back to standard color logic.
        """
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and colorMode == "Manual":
            currentColors = self.collectCurrentTableColors()
            if len(currentColors) >= 2:
                self.paletteEmulator.setPaletteFromQColors(currentColors)
                rows = self.tableView.rowCount()
                if rows > 0:
                    colors = self.calculateEmulatedPaletteColors(rows, currentColors)
                    self.applyColorsToTable(colors)
            return

        self.applyColorLogic()

    def handleSizeLogicOnClassChange(self, isRemoval=False):
        """Handles size logic when adding or removing classes.

        When in automatic interval mode with manual sizes:
        - For removal: Updates the palette anchors with current sizes (don't regenerate)
        - For addition: Generates interpolated sizes from existing palette
        Otherwise, falls back to standard size logic.
        """
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        modeId = self.cbMode.currentData()
        isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

        if isAutomaticIntervalMode and sizeMode == "Manual":
            if isRemoval:
                currentSizes = self.collectCurrentTableSizes()
                if len(currentSizes) >= 2:
                    self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)
            else:
                if self.sizePaletteEmulator.isValidPalette():
                    rows = self.tableView.rowCount()
                    if rows > 0:
                        sizes = self.sizePaletteEmulator.generate(rows)
                        if sizes:
                            self.applySizesToTable(sizes)
            return

        self.applySizeLogic()

    def algorithmPalette(self, paletteRamp, numClasses):
        """Interpolates colors from a discrete palette for the specified number of classes."""
        if numClasses < 1:
            return []

        palColors = paletteRamp.colors()
        if not palColors:
            return [QColor("black")] * numClasses

        numColPaleta = len(palColors)

        increment = 0.0
        if numClasses > 1:
            increment = (numColPaleta - 1) / (numClasses - 1)

        indColor = []
        for i in range(numClasses):
            idx = int(math.floor(increment * i))
            idx = max(0, min(idx, numColPaleta - 1))
            indColor.append(idx)

        finalColors = [QColor()] * numClasses

        i = 0
        while i < numClasses:
            currentPalIdx = indColor[i]

            j = i
            while j < numClasses and indColor[j] == currentPalIdx:
                j += 1

            groupSize = j - i

            colorStart = palColors[currentPalIdx]
            if currentPalIdx + 1 < numColPaleta:
                colorEnd = palColors[currentPalIdx + 1]
            else:
                colorEnd = colorStart

            for k in range(groupSize):
                globalIdx = i + k
                factor = (k) / (groupSize + 1) if (groupSize + 1) > 0 else 0

                r = int(
                    colorStart.red()
                    + (colorEnd.red() - colorStart.red()) * factor
                )
                g = int(
                    colorStart.green()
                    + (colorEnd.green() - colorStart.green()) * factor
                )
                b = int(
                    colorStart.blue()
                    + (colorEnd.blue() - colorStart.blue()) * factor
                )

                finalColors[globalIdx] = QColor(r, g, b)

            i = j

        return finalColors

    def algorithmRamp(self, gradientRamp, numClasses):
        if numClasses < 1:
            return []

        colors = []
        for i in range(numClasses):
            position = 0.0
            if numClasses > 1:
                position = i / (numClasses - 1)
            colors.append(gradientRamp.color(position))

        return colors

    def syncColorRampButton(self):
        self.btnColorRamp.clearRamps()
        mode = self.cbColors.currentText()

        if mode == "Ramp":
            ramps = self.loadGradientRampsFromStyle()
        elif mode == "Palette":
            ramps = self.loadPaletteRampsFromStyle()
        else:
            return

        if ramps:
            self.btnColorRamp.addColorRamps(ramps)
            firstName = list(ramps.keys())[0]
            self.btnColorRamp.setActiveRampByName(firstName)

    def loadGradientRampsFromStyle(self):
        ramps = {}

        if self.style:
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsGradientColorRamp):
                    ramps[name] = ramp

        if not ramps:
            ramps["Default (Blue to Red)"] = QgsGradientColorRamp(QColor(0, 0, 255), QColor(255, 0, 0))
            ramps["Default (Green to Yellow)"] = QgsGradientColorRamp(QColor(0, 128, 0), QColor(255, 255, 0))

        return ramps

    def loadPaletteRampsFromStyle(self):
        ramps = {}

        if self.style:
            names = self.style.colorRampNames()
            for name in names:
                ramp = self.style.colorRamp(name)
                if isinstance(ramp, QgsPresetSchemeColorRamp):
                    ramps[name] = ramp

        if not ramps:
            primaryColors = [
                QColor(255, 0, 0),
                QColor(0, 255, 0),
                QColor(0, 0, 255),
                QColor(255, 255, 0),
                QColor(255, 0, 255),
                QColor(0, 255, 255),
            ]
            ramps["Primary Colors"] = QgsPresetSchemeColorRamp(primaryColors)

            warmColors = [
                QColor(255, 87, 51),
                QColor(255, 140, 0),
                QColor(255, 195, 0),
                QColor(220, 60, 60),
                QColor(255, 165, 79),
                QColor(238, 130, 98),
            ]
            ramps["Warm Colors"] = QgsPresetSchemeColorRamp(warmColors)

        return ramps

    # ============================================================
    # LAYER AND GROUP MANAGEMENT
    # ============================================================

    def populateGroups(self):
        self.cbGroups.blockSignals(True)
        self.cbGroups.clear()

        groups = []
        self.collectGroupsRecursive(QgsProject.instance().layerTreeRoot(), [], groups)

        for name, path, _ in groups:
            self.cbGroups.addItem(name, path)

        self.cbGroups.blockSignals(False)

        if self.cbGroups.count() == 0:
            self.handleEmptyGroupState()

    def handleEmptyGroupState(self):
        self.cbGroups.setCurrentIndex(-1)

        self.cbLegendLayer.blockSignals(True)
        self.cbLegendLayer.setExceptedLayerList(list(QgsProject.instance().mapLayers().values()))
        self.cbLegendLayer.setLayer(None)
        self.cbLegendLayer.blockSignals(False)

        self.frameLegends.setEnabled(False)
        self.labelFrameLegends.setText(self.tr("Legend"))
        self.onLayerChanged(None)

    def collectGroupsRecursive(self, parent, pathParts, results):
        for child in parent.children():
            if isinstance(child, QgsLayerTreeGroup):
                currentPath = pathParts + [child.name()]
                identifier = child.customProperty("qgisred_identifier") or ""

                # The Trees parent group is never listed itself: each tree's own
                # subgroup becomes an entry, labeled with the tree name.
                if identifier == "qgisred_trees":
                    for sub in child.children():
                        if isinstance(sub, QgsLayerTreeGroup) and self.groupHasRenderableLayers(sub):
                            subPath = currentPath + [sub.name()]
                            results.append((sub.name(), " / ".join(subPath), sub))
                    continue

                isAllowed = identifier in self.ALLOWED_GROUP_IDENTIFIERS or self.isQueriesGroup(identifier)
                if isAllowed and self.groupHasRenderableLayers(child):
                    results.append((currentPath[-1], " / ".join(currentPath), child))

                self.collectGroupsRecursive(child, currentPath, results)

    def isQueriesGroup(self, identifier):
        return any(identifier.startswith(prefix) for prefix in self.QUERIES_GROUP_PREFIXES)

    def isTreeChildGroup(self, group):
        """Check whether the group is one tree's own subgroup under the Trees parent group."""
        parent = group.parent() if group else None
        if not isinstance(parent, QgsLayerTreeGroup):
            return False
        return (parent.customProperty("qgisred_identifier") or "") == "qgisred_trees"

    def groupHasAnyLayers(self, group):
        return any(isinstance(child, QgsLayerTreeLayer) for child in group.children())

    def groupHasRenderableLayers(self, group):
        identifier = group.customProperty("qgisred_identifier") or ""
        isQueriesGroup = self.isQueriesGroup(identifier) or self.isTreeChildGroup(group)
        recurseIntoSubgroups = identifier == "qgisred_results" or isQueriesGroup
        layers = []
        self.collectRenderableLayersRecursive(group, layers, recurseIntoSubgroups, isQueriesGroup)
        return len(layers) > 0

    def getRenderableLayersInSelectedGroup(self):
        path = self.cbGroups.currentData()
        if not path:
            return []

        group = self.findGroupByPath(path)
        if not group:
            return []

        identifier = group.customProperty("qgisred_identifier") or ""
        isQueriesGroup = self.isQueriesGroup(identifier) or self.isTreeChildGroup(group)
        recurseIntoSubgroups = identifier == "qgisred_results" or isQueriesGroup

        layers = []
        self.collectRenderableLayersRecursive(group, layers, recurseIntoSubgroups, isQueriesGroup)

        return layers

    def collectRenderableLayersRecursive(self, group, layers, recurseIntoSubgroups, isQueriesGroup=False):
        """Collects renderable layers from a group, optionally recursing into subgroups."""
        groupIdentifier = group.customProperty("qgisred_identifier") or ""
        isInputGroup = groupIdentifier == "qgisred_inputs"

        isDemandBuilderGroup = groupIdentifier == "qgisred_demandbuilder"

        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer and isinstance(layer, QgsVectorLayer):
                    if isDemandBuilderGroup and (
                        layer.customProperty("qgisred_identifier")
                        not in self.DEMANDS_BUILDER_EDITABLE_IDENTIFIERS
                    ):
                        continue
                    rendererType = layer.renderer().type() if layer.renderer() else ""
                    isInputLayer = (
                        isInputGroup
                        or layer.customProperty("qgisred_identifier") in self.INPUT_LAYER_IDENTIFIERS
                    )
                    if rendererType in ("graduatedSymbol", "categorizedSymbol", "RuleRenderer") or (
                        rendererType == "singleSymbol" and (isInputLayer or recurseIntoSubgroups or isQueriesGroup)
                    ):
                        layers.append(layer)
            elif isinstance(child, QgsLayerTreeGroup) and recurseIntoSubgroups:
                self.collectRenderableLayersRecursive(child, layers, recurseIntoSubgroups, isQueriesGroup)

    def findGroupByPath(self, pathStr):
        current = QgsProject.instance().layerTreeRoot()
        for part in pathStr.split(" / "):
            found = next((child for child in current.children() if isinstance(child, QgsLayerTreeGroup) and child.name().strip() == part.strip()), None)
            if not found:
                return None
            current = found
        return current

    def preselectGroupAndLayer(self):
        if not self.cbGroups.count():
            return

        activeLayer = self.getActiveLayerFromTree()
        targetGroup = None
        targetLayer = None

        if activeLayer:
            targetGroup = self.findGroupPathForLayer(activeLayer)
            if targetGroup:
                targetLayer = activeLayer.layer()

        if not targetGroup:
            targetGroup = self.cbGroups.itemData(0)

        self.setGroupByPath(targetGroup)
        # Runs the whole selection once: determineTargetLayer already prefers the
        # panel's active layer and falls back to the group's first layer.
        self.onGroupChanged()

        if targetLayer and self.cbLegendLayer.currentLayer() != targetLayer:
            self.cbLegendLayer.setLayer(targetLayer)

    def getActiveLayerFromTree(self):
        if iface and iface.layerTreeView():
            selectedLayers = iface.layerTreeView().selectedLayers()
            if selectedLayers:
                return QgsProject.instance().layerTreeRoot().findLayer(selectedLayers[0])
        return None

    def findGroupPathForLayer(self, layerNode):
        parent = layerNode.parent()
        while parent and not isinstance(parent, QgsLayerTreeGroup):
            parent = parent.parent()

        if isinstance(parent, QgsLayerTreeGroup):
            path = self.buildGroupPath(parent)
            for i in range(self.cbGroups.count()):
                if self.cbGroups.itemData(i) == path:
                    return path

        return None

    def buildGroupPath(self, group):
        parts = []
        current = group
        while current and current.parent():
            parts.insert(0, current.name())
            current = current.parent()
        return " / ".join(parts)

    def setGroupByPath(self, path):
        # Signals are blocked: every caller invokes onGroupChanged() explicitly,
        # otherwise the currentIndexChanged connection would run it a second time.
        for i in range(self.cbGroups.count()):
            if self.cbGroups.itemData(i) == path:
                self.cbGroups.blockSignals(True)
                self.cbGroups.setCurrentIndex(i)
                self.cbGroups.blockSignals(False)
                break

    # ============================================================
    # TABLE POPULATION
    # ============================================================

    def populateClassificationModes(self):
        self.cbMode.blockSignals(True)
        self.cbMode.clear()
        self.cbMode.addItem("Manual", None)

        modes = [
            ("EqualInterval", "Equal Interval"),
            ("FixedInterval", "Fixed Interval"),
            ("Quantile", "Quantile (Equal Count)"),
            ("Jenks", "Natural Breaks (Jenks)"),
            ("StdDev", "Standard Deviation"),
            ("Pretty", "Pretty Breaks"),
        ]

        for modeId, modeName in modes:
            self.cbMode.addItem(self.tr(modeName), modeId)

        self.cbMode.blockSignals(False)

    def populateLegendTypes(self, layer=None):
        self.cbLegendsType.blockSignals(True)
        self.cbLegendsType.clear()

        if not layer:
            self.addDefaultLegendTypes()
        else:
            self.addLayerSpecificLegendTypes(layer)

        self.cbLegendsType.blockSignals(False)

    def addDefaultLegendTypes(self):
        self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")
        self.cbLegendsType.addItem(self.tr("Categorized"), "categorizedSymbol")
        self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")

    def addLayerSpecificLegendTypes(self, layer):
        layerIdentifier = layer.customProperty("qgisred_identifier")
        currentRendererType = layer.renderer().type() if layer.renderer() else "singleSymbol"

        supportsCategorized = False
        if self.utils:
            supportsCategorized = QGISRedLayerUtils.getLayerSupportsCategorized(layerIdentifier)

        if layerIdentifier in self.SINGLE_EDITABLE_QUERY_IDENTIFIERS:
            self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif supportsCategorized:
            self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif currentRendererType == "categorizedSymbol":
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif currentRendererType == "RuleRenderer" and self.ruleBasedAsCategories(layer.renderer()):
            self.cbLegendsType.addItem(
                self.tr("Categorized"), "categorizedSymbol"
            )
        elif currentRendererType in ("graduatedSymbol", "RuleRenderer"):
            self.cbLegendsType.addItem(self.tr("Graduated"), "graduatedSymbol")
        else:
            self.cbLegendsType.addItem(self.tr("Single Symbol"), "singleSymbol")

    OPEN_RANGE_BOUND = _OPEN_RANGE_BOUND

    def parseRangeFilter(self, expression):
        """(column, lower, upper) of a range rule, or None when the rule is not a range."""
        return _parseRangeFilter(expression, self.OPEN_RANGE_BOUND)

    unwrapClassAttribute = staticmethod(_unwrapClassAttribute)

    def ruleBasedAsGraduated(self, renderer):
        """Convert a QgsRuleBasedRenderer (created by applyNullStyle) back to QgsGraduatedSymbolRenderer."""
        if not isinstance(renderer, QgsRuleBasedRenderer):
            return None
        rules = [r for r in renderer.rootRule().children() if _NULL_RULE_LABEL not in r.label()]
        if not rules:
            return None

        classAttr = None
        ranges = []
        for rule in rules:
            parsed = self.parseRangeFilter(rule.filterExpression())
            if parsed is None:
                continue
            attribute, lower, upper = parsed
            if classAttr is None:
                classAttr = attribute
            ranges.append(QgsRendererRange(lower, upper, rule.symbol().clone(), rule.label()))
        if classAttr is None or not ranges:
            return None
        return QgsGraduatedSymbolRenderer(classAttr, ranges)

    def ruleBasedAsCategories(self, renderer):
        """Parse a QgsRuleBasedRenderer with categorical filters into (field, entries).

        Returns None unless every non-NULL rule is a "Field" = 'value' filter
        (or the Hydraulic Sectors ClosedLinks composite) on the same field.
        """
        if not isinstance(renderer, QgsRuleBasedRenderer):
            return None
        rules = [r for r in renderer.rootRule().children() if _NULL_RULE_LABEL not in (r.label() or "")]
        if not rules:
            return None
        field = None
        entries = []
        for rule in rules:
            parsed = parseCategoricalRuleFilter(rule.filterExpression())
            if not parsed:
                return None
            ruleField, value = parsed
            if field is None:
                field = ruleField
            elif ruleField != field:
                return None
            entries.append({
                "value": value,
                "label": rule.label(),
                "symbol": rule.symbol(),
                "renderState": rule.active(),
            })
        return field, entries

    def detectFieldType(self, layer, renderer=None):
        renderer = renderer if renderer is not None else layer.renderer()

        if isinstance(renderer, QgsGraduatedSymbolRenderer):
            return self.FIELD_TYPE_NUMERIC, renderer.classAttribute()

        if isinstance(renderer, QgsRuleBasedRenderer):
            graduated = self.ruleBasedAsGraduated(renderer)
            if graduated:
                return self.FIELD_TYPE_NUMERIC, graduated.classAttribute()
            categorical = self.ruleBasedAsCategories(renderer)
            if categorical:
                return self.FIELD_TYPE_CATEGORICAL, categorical[0]

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            fieldName = renderer.classAttribute()
            fieldIdx = layer.fields().indexOf(fieldName)

            # Query layers stay categorical even when the class field is numeric
            # (e.g. Connectivity component ids or integer sector ids).
            if fieldIdx >= 0 and not self.isQueryLayer(layer) and layer.fields().field(fieldIdx).type() in [
                QVariantInt,
                QVariantDouble,
                QVariantLongLong,
            ]:
                return self.FIELD_TYPE_NUMERIC, fieldName

            return self.FIELD_TYPE_CATEGORICAL, fieldName

        # singleSymbol renderer for input and single/size-only query layers gets its own field type
        if renderer and renderer.type() == "singleSymbol" and (
            self.isInputLayer() or self.isSizeOnlyQueryLayer() or self.isSingleEditableQueryLayer()
        ):
            return self.FIELD_TYPE_SINGLE, None

        return self.FIELD_TYPE_UNKNOWN, None

    def getCurrentRendererType(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return "categorizedSymbol"
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            return "graduatedSymbol"
        if self.currentFieldType == self.FIELD_TYPE_SINGLE:
            return "singleSymbol"
        return None

    def resetToEmptyState(self):
        self.frameLegends.setEnabled(False)
        self.labelFrameLegends.setVisible(False)
        self.updateMeterTypeControls(None)
        self.currentLayer = None
        self.currentFieldType = self.FIELD_TYPE_UNKNOWN
        self.clearTable()
        self.updateUiBasedOnFieldType()

    def clearTable(self):
        self.tableView.setRowCount(0)
        self.updateClassCount()

    def populateNumericLegend(self):
        if not self.currentLayer:
            return

        renderer = self._workingRenderer or self.currentLayer.renderer()
        self._workingRenderer = None
        if isinstance(renderer, QgsRuleBasedRenderer):
            renderer = self.ruleBasedAsGraduated(renderer)
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return

        self.clearTable()
        geometryHint = self.getGeometryHint()

        for i, rangeItem in enumerate(renderer.ranges()):
            self.tableView.insertRow(i)
            valueText = f"{rangeItem.lowerValue():.2f} - {rangeItem.upperValue():.2f}"

            self.setRowWidgets(
                i,
                rangeItem.symbol(),
                rangeItem.renderState(),
                valueText,
                rangeItem.label(),
                geometryHint,
            )

        self.updateClassCount()

    def populateCategoricalLegend(self):
        if not self.currentLayer:
            return

        renderer = self._workingRenderer or self.currentLayer.renderer()
        self._workingRenderer = None
        self.clearTable()

        self.usedUniqueValues = []
        self.availableUniqueValues = self.getUniqueValuesFromLayer()

        # Categorical rule-based renderers (e.g. Hydraulic Sectors links) keep their
        # rule structure: remember the source so Apply rebuilds rules, not categories.
        self._sourceRuleRenderer = None
        if isinstance(renderer, QgsRuleBasedRenderer):
            categorical = self.ruleBasedAsCategories(renderer)
            if categorical:
                self._sourceRuleRenderer = renderer.clone()
                geometryHint = self.getGeometryHint()
                for entry in categorical[1]:
                    if entry["symbol"] is None:
                        continue
                    if entry["value"] in self.availableUniqueValues:
                        self.usedUniqueValues.append(entry["value"])
                    row = self.tableView.rowCount()
                    self.tableView.insertRow(row)
                    self.setRowWidgets(
                        row,
                        entry["symbol"],
                        entry["renderState"],
                        entry["value"],
                        entry["label"],
                        geometryHint,
                        isReadOnlyValue=True,
                    )

        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            categories = renderer.categories()
            otherCategory = None
            geometryHint = self.getGeometryHint()

            for category in categories:
                if category.value() == "" or category.label() in [
                    self.tr("Other Values"),
                    "Other Values",
                ]:
                    otherCategory = category
                    continue

                valueStr = str(category.value()) if category.value() is not None else "NULL"

                if valueStr in self.availableUniqueValues:
                    self.usedUniqueValues.append(valueStr)

                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(
                    row,
                    category.symbol(),
                    category.renderState(),
                    valueStr,
                    category.label(),
                    geometryHint,
                    isReadOnlyValue=True,
                )

            if otherCategory:
                row = self.tableView.rowCount()
                self.tableView.insertRow(row)
                self.setRowWidgets(
                    row,
                    otherCategory.symbol(),
                    otherCategory.renderState(),
                    self.tr("Other Values"),
                    otherCategory.label(),
                    geometryHint,
                    isReadOnlyValue=True,
                )

        self.availableUniqueValues = [v for v in self.availableUniqueValues if v not in self.usedUniqueValues]
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def populateSingleSymbolLegend(self):
        """Populate the table with a single row representing the singleSymbol renderer."""
        if not self.currentLayer:
            return

        renderer = self._workingRenderer or self.currentLayer.renderer()
        self._workingRenderer = None
        self.clearTable()

        if not renderer or renderer.type() != "singleSymbol":
            return

        symbol = renderer.symbol()
        if not symbol:
            return

        geometryHint = self.getGeometryHint()
        row = self.tableView.rowCount()
        self.tableView.insertRow(row)
        self.setRowWidgets(row, symbol, True, "", "", geometryHint, isReadOnlyValue=True)
        self.updateClassCount()

    def setRowWidgets(
        self,
        row,
        symbol,
        visible,
        valueText,
        legendText,
        geometryHint,
        isReadOnlyValue=False,
    ):
        self.setCheckboxWidget(row, visible)
        geometryHint = self.effectiveGeometryHint(symbol, geometryHint)
        self.setColorWidget(row, symbol, geometryHint)
        self.setSizeWidget(row, symbol, geometryHint)
        self.setValueWidget(row, valueText, isReadOnlyValue)
        self.setLegendWidget(row, legendText)

    @staticmethod
    def effectiveGeometryHint(symbol, geometryHint):
        """Trust the symbol class over the layer geometry.

        An invalid or reloading layer reports Unknown geometry while its renderer
        still holds line or marker symbols; reading a marker size from a line
        symbol then raises AttributeError.
        """
        if isinstance(symbol, QgsLineSymbol):
            return "line"
        if isinstance(symbol, QgsMarkerSymbol):
            return "marker"
        if isinstance(symbol, QgsFillSymbol):
            return "fill"
        return geometryHint

    def setCheckboxWidget(self, row, visible):
        checkbox = QCheckBox(self.tableView)
        checkbox.setChecked(visible)
        checkbox.installEventFilter(self.rowSelectionFilter)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, 0, container)

    def setColorWidget(self, row, symbol, geometryHint):
        identifier = self.currentLayer.customProperty("qgisred_identifier") if self.currentLayer else ""
        # For input layers, the visible color is set via a data-defined expression — read it from there.
        color = None
        previewSymbol = symbol
        strokeColorOnly = False
        if self.isInputLayer():
            color = self._readInputLayerColor(symbol, identifier)
        if identifier == self.TREE_NODES_IDENTIFIER:
            # The edited color is the outer circle's stroke; preview the circle
            # alone so the swatch does not show the star on top of it.
            circles = self._circleMarkerLayers(symbol)
            if circles:
                color = circles[0].strokeColor()
                previewSymbol = self._circleOnlySymbol(symbol)
                strokeColorOnly = True
        if color is None:
            if symbol.symbolLayerCount() > 0:
                color = symbol.symbolLayer(0).color()
            else:
                color = symbol.color()

        colorSelector = QGISRedSymbolColorSelector(
            self.tableView,
            geometryHint,
            color,
            True,
            "Pick color",
            doubleClickOnly=True,
            actualSymbol=previewSymbol,
            # Multiple Demands: preview the picked color on the inner circle
            # (the expression-driven layer) and keep the outer circle as is.
            colorExpressionLayersOnly=(identifier == "qgisred_demands"),
            strokeColorOnly=strokeColorOnly,
        )
        colorSelector.setEnabled(self.isEditing)
        colorSelector.colorChanged.connect(self.onRowColorChanged)
        colorSelector.setAutoFillBackground(False)
        colorSelector.setFixedSize(30, 20)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        colorSelector.installEventFilter(self.rowSelectionFilter)
        layout.addStretch()
        layout.addWidget(colorSelector, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        container.setAutoFillBackground(False)
        container.installEventFilter(self.rowSelectionFilter)

        self.tableView.setCellWidget(row, 1, container)

    def setSizeWidget(self, row, symbol, geometryHint):
        size = self._getLineWidth(symbol) if geometryHint == "line" else self._getNodeSize(symbol)
        meterTypeSize = self._readSelectedMeterTypeSize(symbol)
        if meterTypeSize is not None:
            size = meterTypeSize
        sizeWidget = QLineEdit(str(size))
        sizeWidget.setEnabled(self.isEditing)
        sizeWidget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sizeWidget.setStyleSheet(self.getBaseLineEditStyle())
        sizeWidget.installEventFilter(self.rowSelectionFilter)
        sizeWidget.textChanged.connect(lambda text, r=row: self.onSizeChanged(r, text))

        self.tableView.setCellWidget(row, 2, sizeWidget)

    def setValueWidget(self, row, valueText, isReadOnlyValue):
        valueWidget = QLineEdit(valueText)
        valueWidget.setReadOnly(True)
        valueWidget.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if self.isInputLayer():
            valueWidget.setEnabled(False)
            valueWidget.setStyleSheet(self.getReadOnlyLineEditStyle())
        elif isReadOnlyValue:
            valueWidget.setStyleSheet(self.getReadOnlyLineEditStyle())
        else:
            valueWidget.setStyleSheet(self.getBaseLineEditStyle())
            valueWidget.mouseDoubleClickEvent = lambda event, r=row: self.openRangeEditor(r)

        valueWidget.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, 3, valueWidget)

    def setLegendWidget(self, row, legendText):
        legendWidget = QLineEdit(legendText)
        isEnabled = self.isEditing and not self.isInputLayer()
        legendWidget.setEnabled(isEnabled)
        legendWidget.setStyleSheet(
            self.getReadOnlyLineEditStyle() if not isEnabled else self.getBaseLineEditStyle()
        )
        legendWidget.installEventFilter(self.rowSelectionFilter)

        self.tableView.setCellWidget(row, 4, legendWidget)

    def getBaseLineEditStyle(self):
        return """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #2b2b2b;
                font-size: %s;
            }
            QLineEdit:focus {
                border: 1px solid #3399ff;
            }
        """ % self.CONTROL_FONT_SIZE

    def getReadOnlyLineEditStyle(self):
        return """
            QLineEdit {
                background-color: transparent;
                border: none;
                padding: 2px;
                color: #808080;
                font-size: %s;
            }
        """ % self.CONTROL_FONT_SIZE

    def getUniqueValuesFromLayer(self):
        if not self.currentLayer or not self.currentFieldName:
            return []

        # For results layers, get values from the All shapefile
        if self.isResultsLayer():
            resultsValues = self.getResultsUniqueValues()
            if resultsValues:
                return resultsValues

        # Original implementation for non-results layers
        fieldIdx = self.currentLayer.fields().indexOf(self.currentFieldName)
        if fieldIdx < 0:
            # The class attribute can be an expression (e.g. the Demand Builder
            # CASE over "Category"): evaluate it per feature instead.
            values = self.getUniqueValuesFromExpression()
        else:
            values = set()
            for feature in self.currentLayer.getFeatures():
                value = feature[self.currentFieldName]
                values.add(str(value) if value is not None else "NULL")

        specialValues = ["NULL", "#NA"]
        regularValues = [v for v in values if v not in specialValues]
        foundSpecials = [v for v in specialValues if v in values]

        return sorted(regularValues) + foundSpecials

    def getUniqueValuesFromExpression(self):
        """Evaluate currentFieldName as an expression over every feature and collect the results."""
        values = set()
        try:
            from qgis.core import QgsExpression, QgsExpressionContext, QgsExpressionContextUtils

            expression = QgsExpression(self.currentFieldName)
            if expression.hasParserError():
                return values
            context = QgsExpressionContext()
            context.appendScopes(QgsExpressionContextUtils.globalProjectLayerScopes(self.currentLayer))
            for feature in self.currentLayer.getFeatures():
                context.setFeature(feature)
                value = expression.evaluate(context)
                if value == NULL:
                    value = None
                values.add(str(value) if value is not None else "NULL")
        except Exception:
            return values
        return values

    # ============================================================
    # CLASS MANIPULATION - ADD
    # ============================================================

    def onAddClassClicked(self):
        if not self.currentLayer:
            return

        if self.addClassClickTimer and self.addClassClickTimer.isActive():
            self.addClassClickTimer.stop()
            self.addClassClickTimer = None

            if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
                self.ensureOtherValuesCategory()
            return

        self.addClassClickTimer = QTimer()
        self.addClassClickTimer.setSingleShot(True)
        self.addClassClickTimer.timeout.connect(self.onSingleClickAdd)
        self.addClassClickTimer.start(250)

    def onSingleClickAdd(self):
        self.addClassClickTimer = None
        self.addClassBeforeSelection = False
        self.executeAddClass()

    def executeAddClass(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.addCategoricalClass()
        else:
            self.addNumericClass()
            modeId = self.cbMode.currentData()
            if modeId and modeId != "Manual" and modeId != "FixedInterval":
                self.applyClassificationMethod(modeId)

        self.updateButtonStates()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange()

    def addNumericClass(self):
        if self.tableView.rowCount() >= self.MAX_CLASSES:
            self.showMaxClassesError()
            return

        selectedRows = self.getSelectedRows()
        if len(selectedRows) > 1:
            self.tableView.clearSelection()
            selectedRows = []

        insertionRow = self.calculateNumericInsertionRow(selectedRows)
        lower, upper = self.calculateInitialRangeForNewRow(insertionRow)

        modeId = self.cbMode.currentData()
        colorMode = self.cbColors.currentText() if hasattr(self, "cbColors") else "Manual"
        sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
        isManualMode = modeId is None or modeId == "Manual"

        if isManualMode and colorMode == "Manual":
            newColor = self.getSmartColorForNewRow(insertionRow)
        else:
            newColor = self.generateRandomColor()

        if isManualMode and sizeMode == "Manual":
            smartSize = self.getSmartSizeForNewRow(insertionRow)
        else:
            smartSize = None

        self.tableView.insertRow(insertionRow)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(newColor)

        if smartSize is not None:
            if self.currentLayer.geometryType() == WKB_LINE_GEOMETRY:
                symbol.setWidth(smartSize)
            else:
                symbol.setSize(smartSize)
        else:
            self.setDefaultSymbolSize(symbol)

        valueText = f"{lower:.2f} - {upper:.2f}"
        self.setRowWidgets(
            insertionRow,
            symbol,
            True,
            valueText,
            valueText,
            self.getGeometryHint(),
        )

        self.updateAdjacentRowsAfterInsertion(insertionRow, lower, upper)

        if isManualMode and sizeMode == "Manual":
            self.smoothEdgeSizeAfterInsertion(insertionRow)

        self.tableView.clearSelection()
        self.tableView.selectRow(insertionRow)
        self.updateClassCount()
        self.refreshAllLegendLabels()

    def calculateNumericInsertionRow(self, selectedRows):
        if selectedRows and len(selectedRows) == 1:
            row = selectedRows[0]
            if not self.addClassBeforeSelection:
                row += 1
            return row
        return self.tableView.rowCount()

    def addCategoricalClass(self):
        if self.tableView.rowCount() >= self.MAX_CLASSES:
            self.showMaxClassesError()
            return

        if not self.availableUniqueValues:
            QMessageBox.information(self, "Info", "All values used.")
            return

        value = self.availableUniqueValues.pop(0)
        self.usedUniqueValues.append(value)

        insertionRow = self.calculateCategoricalInsertionRow()

        self.tableView.insertRow(insertionRow)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(self.generateRandomColor())
        self.setDefaultSymbolSize(symbol)

        displayValue = str(value)
        unitAbbr = self.getCurrentLayerUnitAbbr()
        legendText = f"{value} {unitAbbr}" if unitAbbr else displayValue

        self.setRowWidgets(
            insertionRow,
            symbol,
            True,
            displayValue,
            legendText,
            self.getGeometryHint(),
            isReadOnlyValue=True,
        )

        self.tableView.clearSelection()
        self.tableView.selectRow(insertionRow)
        self.updateClassCount()
        self.updateButtonStates()
        self.updateClassCountLimits()

    def calculateCategoricalInsertionRow(self):
        selectedRows = self.getSelectedRows()
        insertionRow = self.tableView.rowCount()

        if self.hasOtherValuesCategory():
            insertionRow -= 1

        if selectedRows and len(selectedRows) == 1:
            selectedWidget = self.tableView.cellWidget(selectedRows[0], 3)
            if isinstance(selectedWidget, QLineEdit) and selectedWidget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                insertionRow = selectedRows[0]
            elif self.addClassBeforeSelection:
                insertionRow = selectedRows[0]
            else:
                insertionRow = selectedRows[0] + 1

        return insertionRow

    def setDefaultSymbolSize(self, symbol):
        # The symbol class decides, not the layer geometry: an invalid layer can
        # report a geometry that does not match the symbols its renderer holds.
        if isinstance(symbol, QgsLineSymbol):
            symbol.setWidth(0.4)
        elif isinstance(symbol, QgsMarkerSymbol):
            symbol.setSize(3)
        elif hasattr(symbol, "setSize"):
            symbol.setSize(1.5)

    def classifyAllUniqueValues(self):
        if len(self.availableUniqueValues) == 0:
            QMessageBox.information(
                self, self.tr("Info"), self.tr("All values are already classified.")
            )
            return
        self.classifyMissingUniqueValues()

    def classifyMissingUniqueValues(self):
        uniqueCountToAdd = len(self.availableUniqueValues)

        if uniqueCountToAdd == 0:
            return

        currentCount = self.tableView.rowCount()
        totalPotential = currentCount + uniqueCountToAdd

        if totalPotential > self.MAX_CLASSES:
            QMessageBox.critical(
                self,
                self.tr("Limit Exceeded"),
                self.tr(
                    f"Adding {uniqueCountToAdd} classes would result in {totalPotential} total classes,\n"
                    f"which exceeds the maximum limit of {self.MAX_CLASSES}."
                ),
            )
            return

        self.tableView.setUpdatesEnabled(False)
        self.tableView.blockSignals(True)

        progress = None
        useProgress = uniqueCountToAdd > self.WARN_CLASSES

        if useProgress:
            progress = QProgressDialog(
                self.tr("Adding classes..."),
                self.tr("Cancel"),
                0,
                uniqueCountToAdd,
                self,
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

        try:
            count = 0
            while self.availableUniqueValues:
                self.addCategoricalClass()
                count += 1

                if useProgress:
                    progress.setValue(count)
                    QApplication.processEvents()
                    if progress.wasCanceled():
                        break

            self.removeOtherValuesRows()

        finally:
            if progress:
                progress.close()

            self.tableView.blockSignals(False)
            self.tableView.setUpdatesEnabled(True)

            self.updateClassCount()
            self.updateButtonStates()
            self.handleColorLogicOnClassChange()
            self.handleSizeLogicOnClassChange()

    def removeOtherValuesRows(self):
        for row in reversed(range(self.tableView.rowCount())):
            widget = self.tableView.cellWidget(row, 3)
            if isinstance(widget, QLineEdit) and widget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                self.tableView.removeRow(row)

    def showMaxClassesError(self):
        QMessageBox.critical(
            self,
            self.tr("Limit Exceeded"),
            self.tr("Maximum of %1 classes reached.").replace("%1", str(self.MAX_CLASSES)),
        )

    # ============================================================
    # CLASS MANIPULATION - REMOVE AND MOVE
    # ============================================================

    def removeClass(self):
        rows = sorted(self.getSelectedRows(), reverse=True)
        if not rows:
            return

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.removeCategoricalRows(rows)
        else:
            self.removeNumericRows(rows)

        self.updateClassCount()
        self.refreshAllLegendLabels()
        self.updateButtonStates()
        self.handleColorLogicOnClassChange()
        self.handleSizeLogicOnClassChange(isRemoval=True)

        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.updateClassCountLimits()

    def removeCategoricalRows(self, rows):
        for row in rows:
            widget = self.tableView.cellWidget(row, 3)
            if isinstance(widget, QLineEdit):
                value = widget.text()
                if (
                    value != self.tr("Other Values")
                    and value in self.usedUniqueValues
                ):
                    self.usedUniqueValues.remove(value)
                    self.availableUniqueValues.append(value)
            self.tableView.removeRow(row)

        self.sortAvailableUniqueValues()

    def removeNumericRows(self, rows):
        lowestRow = rows[-1]
        for row in rows:
            self.tableView.removeRow(row)
        self.mergeAdjacentRowsAfterDeletion(lowestRow)

    def removeCategoricalRow(self, row):
        widget = self.tableView.cellWidget(row, 3)
        if isinstance(widget, QLineEdit):
            value = widget.text()
            if value != self.tr("Other Values") and value in self.usedUniqueValues:
                self.usedUniqueValues.remove(value)
                self.availableUniqueValues.append(value)

        self.tableView.removeRow(row)
        self.sortAvailableUniqueValues()
        self.updateButtonStates()

    def sortAvailableUniqueValues(self):
        specialValues = ["NULL", "#NA"]
        regularValues = [value for value in self.availableUniqueValues if value not in specialValues]
        foundSpecials = [value for value in specialValues if value in self.availableUniqueValues]
        self.availableUniqueValues = sorted(regularValues) + foundSpecials

    def moveClassUp(self):
        self.moveRow(-1)

    def moveClassDown(self):
        self.moveRow(1)

    def moveRow(self, offset):
        rows = self.getSelectedRows()
        if len(rows) != 1:
            return

        row = rows[0]
        if not (0 <= row + offset < self.tableView.rowCount()):
            return

        self.swapTableRows(row, row + offset)
        self.tableView.selectRow(row + offset)

    def swapTableRows(self, row1, row2):
        data1 = self.getRowData(row1)
        data2 = self.getRowData(row2)
        self.setRowData(row1, data2)
        self.setRowData(row2, data1)

    def getRowData(self, row):
        data = []

        for column in range(5):
            widget = self.tableView.cellWidget(row, column)

            if column == 0:
                data.append(self.extractCheckboxData(widget))
            elif column == 1:
                data.append(self.extractColorSelectorData(widget))
            elif isinstance(widget, QLineEdit):
                hasDoubleClick = (
                    column == 3
                    and hasattr(widget, "mouseDoubleClickEvent")
                    and widget.mouseDoubleClickEvent.__name__ == "<lambda>"
                )
                data.append(("le", widget.text(), widget.isReadOnly(), hasDoubleClick))
            else:
                data.append(None)

        return data

    def extractCheckboxData(self, widget):
        if widget:
            checkbox = widget.findChild(QCheckBox)
            if checkbox:
                return ("ck", checkbox.isChecked())
        return None

    def extractColorSelectorData(self, widget):
        if widget:
            colorSelector = widget.findChild(QGISRedSymbolColorSelector)
            if colorSelector:
                # Index 2 kept as a placeholder: the preview no longer tracks a size
                return (
                    "cs",
                    colorSelector.activeColor,
                    None,
                    colorSelector.geometryType,
                )
        return None

    def setRowData(self, row, data):
        for column, columnData in enumerate(data):
            if not columnData:
                continue

            dataType = columnData[0]

            if dataType == "ck":
                self.recreateCheckboxWidget(row, column, columnData[1])
            elif dataType == "cs":
                self.recreateColorSelectorWidget(row, column, columnData)
            elif dataType == "le":
                self.recreateLineEditWidget(row, column, columnData)

    def recreateCheckboxWidget(self, row, column, isChecked):
        checkbox = QCheckBox(self.tableView)
        checkbox.setChecked(isChecked)
        checkbox.installEventFilter(self.rowSelectionFilter)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, column, container)

    def recreateColorSelectorWidget(self, row, column, data):
        color = data[1]
        geometryHint = data[3]

        colorSelector = QGISRedSymbolColorSelector(
            self.tableView,
            geometryHint,
            color,
            True,
            "Pick color",
            doubleClickOnly=True,
        )
        colorSelector.setEnabled(self.isEditing)
        colorSelector.setAutoFillBackground(False)
        colorSelector.setFixedSize(30, 20)

        container = QWidget(self.tableView)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()
        layout.addWidget(colorSelector)
        layout.addStretch()
        container.setAutoFillBackground(False)

        self.tableView.setCellWidget(row, column, container)

    def recreateLineEditWidget(self, row, column, data):
        text = data[1]
        isReadOnly = data[2]
        hasDoubleClick = data[3] if len(data) > 3 else False

        lineEdit = QLineEdit(text)
        lineEdit.setEnabled(self.isEditing)

        if isReadOnly:
            lineEdit.setReadOnly(True)
            if column == 3:
                lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if hasDoubleClick:
                    lineEdit.setStyleSheet(self.getBaseLineEditStyle())
                    lineEdit.mouseDoubleClickEvent = (
                        lambda event, r=row: self.openRangeEditor(r)
                    )
                else:
                    lineEdit.setStyleSheet(self.getReadOnlyLineEditStyle())
            else:
                lineEdit.setStyleSheet(self.getBaseLineEditStyle())
        else:
            lineEdit.setStyleSheet(self.getBaseLineEditStyle())

        if column == 2:
            lineEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lineEdit.textChanged.connect(lambda t, r=row: self.onSizeChanged(r, t))

        lineEdit.installEventFilter(self.rowSelectionFilter)
        self.tableView.setCellWidget(row, column, lineEdit)

    # ============================================================
    # NUMERIC CLASSIFICATION LOGIC
    # ============================================================

    def calculateInitialRangeForNewRow(self, row):
        """Determines range for new row using half-splitting logic for contiguous ranges."""
        total = self.tableView.rowCount()

        if total == 0:
            return self.getLayerMinMax()

        if total == 1:
            return self.calculateSplitRangeForSingleRow(row)

        return self.calculateSplitRangeForMultipleRows(row, total)

    def calculateSplitRangeForSingleRow(self, row):
        existing = self.getRangeValues(0)
        if existing:
            lower, upper = existing
            mid = (lower + upper) / 2.0
            if row == 0:
                return (lower, mid)
            else:
                return (mid, upper)
        return self.getLayerMinMax()

    def calculateSplitRangeForMultipleRows(self, row, total):
        if row == 0:
            splitRow = 0
        elif row >= total:
            splitRow = total - 1
        else:
            if self.addClassBeforeSelection:
                splitRow = row
            else:
                splitRow = row - 1

        targetRange = self.getRangeValues(splitRow)
        if targetRange:
            lower, upper = targetRange
            mid = (lower + upper) / 2.0

            if row <= splitRow:
                return (lower, mid)
            else:
                return (mid, upper)

        return self.getLayerMinMax()

    def getLayerMinMax(self):
        values = self.getNumericValues()
        if values and len(values) > 0:
            return (min(values), max(values))
        return (0.0, 1.0)

    def getRangeValues(self, row):
        widget = self.tableView.cellWidget(row, 3)
        if not isinstance(widget, QLineEdit):
            return None
        try:
            parts = widget.text().split(" - ")
            return float(parts[0]), float(parts[1])
        except Exception:
            return None

    def updateAdjacentRowsAfterInsertion(self, row, newLower, newUpper):
        total = self.tableView.rowCount()

        if total == 2:
            self.handleTwoRowInsertion(row, newLower, newUpper)
            return

        if row > 0:
            prevRange = self.getRangeValues(row - 1)
            if prevRange:
                prevLower, prevUpper = prevRange
                if abs(prevUpper - newLower) < 0.0001 or prevUpper > newLower:
                    self.updateRangeValue(row - 1, None, newLower)

        if row < total - 1:
            nextRange = self.getRangeValues(row + 1)
            if nextRange:
                nextLower, nextUpper = nextRange
                if abs(nextLower - newUpper) < 0.0001 or nextLower < newUpper:
                    self.updateRangeValue(row + 1, newUpper, None)

    def handleTwoRowInsertion(self, row, newLower, newUpper):
        range0 = self.getRangeValues(0)
        range1 = self.getRangeValues(1)

        if range0 and range1:
            if row == 0:
                self.updateRangeValue(1, newUpper, None)
            else:
                self.updateRangeValue(0, None, newLower)

    def mergeAdjacentRowsAfterDeletion(self, rowPos):
        if rowPos > 0 and rowPos < self.tableView.rowCount():
            currentRange = self.getRangeValues(rowPos)
            if currentRange:
                self.updateRangeValue(rowPos - 1, None, currentRange[0])

    def updateRangeValue(self, row, newLower=None, newUpper=None):
        currentRange = self.getRangeValues(row)
        if not currentRange:
            return

        lower, upper = currentRange

        if newLower is not None:
            lower = newLower
        if newUpper is not None:
            upper = newUpper

        text = f"{lower:.2f} - {upper:.2f}"
        valueWidget = self.tableView.cellWidget(row, 3)

        if isinstance(valueWidget, QLineEdit):
            valueWidget.setText(text)

        self.updateLegendsValues(row, lower, upper)

    def updateLegendsValues(self, row, lower, upper):
        legendWidget = self.tableView.cellWidget(row, 4)
        if not isinstance(legendWidget, QLineEdit):
            return

        unitAbbr = self.getCurrentLayerUnitAbbr()
        totalRows = self.tableView.rowCount()
        decimalPlaces = self.calculateDecimalPlaces(totalRows)
        formatString = f"{{:.{decimalPlaces}f}}"

        if row == 0:
            newLegendText = self.formatFirstRowLegend(upper, formatString, unitAbbr)
        elif row == totalRows - 1:
            newLegendText = self.formatLastRowLegend(lower, formatString, unitAbbr)
        else:
            newLegendText = self.formatMiddleRowLegend(lower, upper, formatString, unitAbbr)

        legendWidget.setText(newLegendText)

    def calculateDecimalPlaces(self, totalRows):
        values = self.getNumericValues()
        if values and len(values) > 0:
            minValue, maxValue = min(values), max(values)
            try:
                precision = self.calculateLegendRoundingPrecision(minValue, maxValue, totalRows)
                return max(0, -precision)
            except ValueError:
                return 2
        return 2

    def formatFirstRowLegend(self, upper, formatString, unitAbbr):
        if unitAbbr:
            return f"< {formatString.format(upper)} {unitAbbr}"
        return f"< {formatString.format(upper)}"

    def formatLastRowLegend(self, lower, formatString, unitAbbr):
        if unitAbbr:
            return f"> {formatString.format(lower)} {unitAbbr}"
        return f"> {formatString.format(lower)}"

    def formatMiddleRowLegend(self, lower, upper, formatString, unitAbbr):
        if unitAbbr:
            return f"{formatString.format(lower)} < {formatString.format(upper)} {unitAbbr}"
        return f"{formatString.format(lower)} < {formatString.format(upper)}"

    def refreshAllLegendLabels(self):
        for row in range(self.tableView.rowCount()):
            values = self.getRangeValues(row)
            if values:
                self.updateLegendsValues(row, values[0], values[1])

    def calculateLegendRoundingPrecision(self, minValue, maxValue, intervals=10):
        """Calculates optimal rounding precision for legend values based on data range and interval count."""
        if intervals <= 0:
            raise ValueError("intervals must be > 0")
        if maxValue < minValue:
            raise ValueError("maxValue must be >= minValue")

        increment = (maxValue - minValue) / intervals
        meanAbs = (abs(minValue) + abs(maxValue)) / 2.0

        m1 = math.floor(math.log10(meanAbs) - 2 + 0.5) if meanAbs > 0 else 0
        m2 = math.floor(math.log10(increment)) if increment > 0 else 0

        return min(m1, m2)

    def calculateOptimalInterval(self):
        values = self.getNumericValues()
        if not values:
            return

        valueRange = max(values) - min(values)
        if valueRange == 0:
            self.spinIntervalRange.setValue(1.0)
            return

        target = valueRange / 5.0
        magnitude = math.floor(math.log10(target))
        mantissa = target / (10**magnitude)

        if mantissa <= 1.5:
            niceValue = 1
        elif mantissa <= 3:
            niceValue = 2
        elif mantissa <= 7:
            niceValue = 5
        else:
            niceValue = 10

        self.spinIntervalRange.blockSignals(True)
        self.spinIntervalRange.setValue(niceValue * (10**magnitude))
        self.spinIntervalRange.blockSignals(False)

    def applyClassificationMethod(self, methodId):
        """Applies the selected classification algorithm to generate class breaks."""
        values = self.getNumericValues()
        if not values:
            return

        numClasses = self.tableView.rowCount() or 5
        minValue, maxValue = min(values), max(values)

        previousColors = self.collectCurrentTableColors()

        breaks = self.calculateBreaksForMethod(methodId, values, numClasses, minValue, maxValue)

        if len(breaks) < 2:
            return

        numClasses = len(breaks) - 1
        self.adjustTableRowCount(numClasses)
        self.applyBreaksToTable(breaks, numClasses, minValue, maxValue)

        self.updateClassCount()
        self.applyColorLogic(previousColors=previousColors)
        self.handleSizeLogicOnClassChange()

    def calculateBreaksForMethod(self, methodId, values, numClasses, minValue, maxValue):
        if methodId == "EqualInterval":
            return self.calculateEqualIntervalBreaks(numClasses, minValue, maxValue)

        if methodId == "FixedInterval":
            return self.calculateFixedIntervalBreaks(minValue, maxValue)

        if methodId == "Quantile":
            return self.calculateQuantileBreaks(values, numClasses, minValue, maxValue)

        if methodId == "Jenks":
            return self.calculateJenksBreaks(numClasses, minValue)

        if methodId == "StdDev":
            return self.calculateStdDevBreaks(values, numClasses, minValue, maxValue)

        if methodId == "Pretty":
            return self.calculatePrettyBreaks(numClasses, minValue)

        return []

    def calculateEqualIntervalBreaks(self, numClasses, minValue, maxValue):
        step = (maxValue - minValue) / numClasses
        return [minValue + i * step for i in range(numClasses + 1)]

    def calculateFixedIntervalBreaks(self, minValue, maxValue):
        step = self.spinIntervalRange.value()
        breaks = [minValue]
        current = minValue
        while current < maxValue:
            current += step
            breaks.append(current)
        return breaks

    def calculateQuantileBreaks(self, values, numClasses, minValue, maxValue):
        breaks = [minValue]
        for i in range(1, numClasses):
            index = min(int(i / numClasses * len(values)), len(values) - 1)
            breaks.append(values[index])
        breaks.append(maxValue)
        return breaks

    def calculateJenksBreaks(self, numClasses, minValue):
        # For results layers, use values from All shapefile
        if self.isResultsLayer():
            allLayer = self.loadResultsAllLayer()
            fieldName = self.getResultFieldMapping()
            if allLayer and fieldName:
                classifier = QgsClassificationJenks()
                classifier.setLabelFormat("%1 - %2")
                classes = classifier.classes(allLayer, fieldName, numClasses)
                del allLayer
                return [minValue] + [cls.upperBound() for cls in classes]

        # Original implementation for non-results layers
        classifier = QgsClassificationJenks()
        classifier.setLabelFormat("%1 - %2")
        classes = classifier.classes(self.currentLayer, self.currentFieldName, numClasses)
        return [minValue] + [cls.upperBound() for cls in classes]

    def calculateStdDevBreaks(self, values, numClasses, minValue, maxValue):
        mean = statistics.mean(values)
        stdDev = statistics.stdev(values) if len(values) > 1 else 0

        breaks = [minValue, maxValue]
        for i in range(-numClasses // 2, numClasses // 2 + 1):
            breakValue = mean + i * stdDev
            if minValue < breakValue < maxValue:
                breaks.append(breakValue)

        return sorted(list(set(breaks)))

    def calculatePrettyBreaks(self, numClasses, minValue):
        # For results layers, use values from All shapefile
        if self.isResultsLayer():
            allLayer = self.loadResultsAllLayer()
            fieldName = self.getResultFieldMapping()
            if allLayer and fieldName:
                classifier = QgsClassificationPrettyBreaks()
                classes = classifier.classes(allLayer, fieldName, numClasses)
                del allLayer
                return [minValue] + [cls.upperBound() for cls in classes]

        # Original implementation for non-results layers
        classifier = QgsClassificationPrettyBreaks()
        classes = classifier.classes(self.currentLayer, self.currentFieldName, numClasses)
        return [minValue] + [cls.upperBound() for cls in classes]

    def adjustTableRowCount(self, targetCount):
        while self.tableView.rowCount() < targetCount:
            self.addNumericClass()
        while self.tableView.rowCount() > targetCount:
            self.tableView.removeRow(self.tableView.rowCount() - 1)

    def applyBreaksToTable(self, breaks, numClasses, minValue, maxValue):
        try:
            precision = self.calculateLegendRoundingPrecision(minValue, maxValue, numClasses)
            decimalPlaces = max(0, -precision)
        except ValueError:
            decimalPlaces = 2

        formatString = f"{{:.{decimalPlaces}f}}"
        unitAbbr = self.getCurrentLayerUnitAbbr()

        for i in range(numClasses):
            lower, upper = breaks[i], breaks[i + 1]
            valueText = f"{formatString.format(lower)} - {formatString.format(upper)}"

            valueWidget = self.tableView.cellWidget(i, 3)
            if isinstance(valueWidget, QLineEdit):
                valueWidget.setText(valueText)

            legendText = self.formatLegendForBreaks(i, numClasses, lower, upper, formatString, unitAbbr)
            legendWidget = self.tableView.cellWidget(i, 4)
            if isinstance(legendWidget, QLineEdit):
                legendWidget.setText(legendText)

    def formatLegendForBreaks(self, index, numClasses, lower, upper, formatString, unitAbbr):
        if index == 0:
            return self.formatFirstRowLegend(upper, formatString, unitAbbr)
        if index == numClasses - 1:
            return self.formatLastRowLegend(lower, formatString, unitAbbr)
        return self.formatMiddleRowLegend(lower, upper, formatString, unitAbbr)

    def getNumericValues(self):
        if not self.currentLayer or not self.currentFieldName:
            return []

        # For results layers, get values from the All shapefile
        if self.isResultsLayer():
            resultsValues = self.getResultsNumericValues()
            if resultsValues:
                return resultsValues

        # Original implementation for non-results layers
        values = []
        for feature in self.currentLayer.getFeatures():
            with suppress(Exception):
                values.append(float(feature[self.currentFieldName]))

        return sorted(values)

    # ============================================================
    # RANGE EDITING
    # ============================================================

    def openRangeEditor(self, row):
        modeId = self.cbMode.currentData()
        if modeId and modeId != "Manual":
            return

        currentRange = self.getRangeValues(row)
        if not currentRange:
            return

        unitAbbr = self.getCurrentLayerUnitAbbr()
        dialog = QGISRedRangeEditDialog(currentRange[0], currentRange[1], self, unitAbbreviation=unitAbbr)

        if dialog.exec():
            newLower, newUpper = dialog.getRangeValues()

            if not self.validateRangeEdit(row, newLower, newUpper):
                return

            self.updateRangeValue(row, newLower, newUpper)

            if row > 0:
                self.updateRangeValue(row - 1, None, newLower)
            if row < self.tableView.rowCount() - 1:
                self.updateRangeValue(row + 1, newUpper, None)

            if self.cbSizes.currentText() == "Proportional to Value":
                self.applySizeLogic()

    def validateRangeEdit(self, row, newLower, newUpper):
        if newLower >= newUpper:
            QMessageBox.warning(
                self, "Invalid Range", "Min value must be less than Max value."
            )
            return False

        if row > 0:
            prevRange = self.getRangeValues(row - 1)
            if prevRange and newLower < prevRange[0]:
                QMessageBox.warning(
                    self,
                    "Range Overflow",
                    f"New minimum ({newLower}) is smaller than the previous row's minimum ({prevRange[0]}).\nCannot apply changes.",
                )
                return False

        if row < self.tableView.rowCount() - 1:
            nextRange = self.getRangeValues(row + 1)
            if nextRange and newUpper > nextRange[1]:
                QMessageBox.warning(
                    self,
                    "Range Overflow",
                    f"New maximum ({newUpper}) is larger than the next row's maximum ({nextRange[1]}).\nCannot apply changes.",
                )
                return False

        return True

    def onSizeChanged(self, row, text):
        with suppress(Exception):
            float(text)

            # Update size palette when in automatic interval mode with manual sizes
            sizeMode = self.cbSizes.currentText() if hasattr(self, "cbSizes") else "Manual"
            modeId = self.cbMode.currentData()
            isAutomaticIntervalMode = modeId is not None and modeId != "Manual"

            if isAutomaticIntervalMode and sizeMode == "Manual":
                currentSizes = self.collectCurrentTableSizes()
                if len(currentSizes) >= 2:
                    self.sizePaletteEmulator.setPaletteFromSizes(currentSizes)

    # ============================================================
    # RENDERER CONVERSION
    # ============================================================

    def convertToCategorized(self, field):
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return

        rawValues = layer.uniqueValues(fieldIdx)
        nonNullValues = [v for v in rawValues if v is not None and str(v) != "NULL"]
        hasNull = any(v is None or str(v) == "NULL" for v in rawValues)
        uniqueValues = sorted(nonNullValues)
        categories = []

        unitAbbr = self.getUnitAbbrForLayer()

        for value in uniqueValues:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            color = self.generateRandomHsvColor()
            symbol.setColor(color)
            self.setSymbolSizeForGeometry(symbol)

            label = str(value)
            if unitAbbr:
                label = f"{value} {unitAbbr}"

            category = QgsRendererCategory(value, symbol, label)
            categories.append(category)

        if hasNull:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(self.generateRandomHsvColor())
            self.setSymbolSizeForGeometry(symbol)
            categories.append(QgsRendererCategory(None, symbol, "NULL"))

        renderer = QgsCategorizedSymbolRenderer(field, categories)
        self._workingRenderer = renderer

    def restoreOriginalGraduatedRenderer(self, field):
        """Reuse the renderer the layer had when the dialog opened instead of synthesizing
        a generic classification, so Categorized -> Graduated round-trips keep the legend."""
        original = self.originalRenderer
        if isinstance(original, QgsRuleBasedRenderer):
            original = self.ruleBasedAsGraduated(original)
        if isinstance(original, QgsGraduatedSymbolRenderer) and original.classAttribute() == field:
            self._workingRenderer = original.clone()
            return True
        return False

    def convertToGraduated(self, field):
        layer = self.currentLayer
        fieldIdx = layer.fields().indexOf(field)
        if fieldIdx < 0:
            return

        minVal = layer.minimumValue(fieldIdx)
        maxVal = layer.maximumValue(fieldIdx)

        if minVal is None or maxVal is None:
            return

        numClasses = 5
        interval = (maxVal - minVal) / numClasses
        ranges = []

        startColor = QColor(0, 255, 0)
        endColor = QColor(255, 0, 0)

        for i in range(numClasses):
            lower = minVal + (i * interval)
            upper = minVal + ((i + 1) * interval)

            color = self.interpolateColor(startColor, endColor, i, numClasses)

            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            self.setSymbolSizeForGeometry(symbol)

            label = f"{lower:.1f} - {upper:.1f}"
            rangeObj = QgsRendererRange(lower, upper, symbol, label)
            ranges.append(rangeObj)

        renderer = QgsGraduatedSymbolRenderer(field, ranges)
        self._workingRenderer = renderer

    def interpolateColor(self, startColor, endColor, index, total):
        t = index / max(1, total - 1)
        return QColor(
            int(startColor.red() + t * (endColor.red() - startColor.red())),
            int(startColor.green() + t * (endColor.green() - startColor.green())),
            int(startColor.blue() + t * (endColor.blue() - startColor.blue())),
        )

    def setSymbolSizeForGeometry(self, symbol):
        # The symbol class decides, not the layer geometry: an invalid layer can
        # report a geometry that does not match the symbols its renderer holds.
        if isinstance(symbol, QgsLineSymbol):
            symbol.setWidth(0.6)
        elif hasattr(symbol, "setSize"):
            symbol.setSize(2.5)

    def applyColorToSymbol(self, symbol, color):
        """Applies fill color to all layers of a symbol, preserving its structure."""
        for i in range(symbol.symbolLayerCount()):
            symbolLayer = symbol.symbolLayer(i)
            symbolLayer.setColor(color)
            # Sync stroke only on polygon fills; marker/line strokes belong to the style
            if isinstance(symbolLayer, QgsFillSymbolLayer):
                symbolLayer.setStrokeColor(color)
            # Handle sub-symbols (e.g., marker line's marker symbol)
            if hasattr(symbolLayer, 'subSymbol') and symbolLayer.subSymbol():
                self.applyColorToSymbol(symbolLayer.subSymbol(), color)

    def templateSymbol(self, existingSymbols):
        """Symbol for a class the layer did not have before: a copy of one it already has.

        A default symbol is a bare marker or line, and on result layers everything that
        makes the style work lives in the existing ones — the data-defined size expressions
        that tell tanks and reservoirs apart from junctions, the pump and valve icons, the
        flow arrows. Building a new class from scratch dropped all of it. Colour and size
        are overwritten from the table straight after, so only the structure is inherited.
        """
        for symbol in reversed(existingSymbols):
            if symbol is not None:
                return symbol.clone()
        return QgsSymbol.defaultSymbol(self.currentLayer.geometryType())

    def applySizeToSymbol(self, symbol, size):
        """Applies size to a symbol, preserving its structure."""
        hint = self.effectiveGeometryHint(symbol, self.getGeometryHint())
        if hint == "line":
            symbol.setWidth(size)
        elif hasattr(symbol, "setSize"):
            symbol.setSize(size)
            self.applyNodeSizeExpressions(symbol, size)

    def applyNodeSizeExpressions(self, symbol, size):
        """Write the size into the data-defined expressions that actually draw the markers.

        On result layers the marker size comes from a per-symbol-layer expression, and a
        data-defined property always beats setSize(). Writing only the latter is why the
        size used to change in the legend — drawn with no feature, so the expression cannot
        evaluate and QGIS falls back to the static size — and not on the map.

        Tanks and reservoirs keep their own size: apply_junction_size leaves their
        expressions alone, and Appearance scales them with a factor of their own.
        """
        for index in range(symbol.symbolLayerCount()):
            with suppress(Exception):
                symbolLayer = symbol.symbolLayer(index)
                properties = symbolLayer.dataDefinedProperties()
                sizeProperty = properties.property(SL_PROP_SIZE)
                if not sizeProperty.isActive():
                    continue
                expression = sizeProperty.expressionString()
                updated = apply_junction_size(expression, size)
                if updated != expression:
                    properties.setProperty(SL_PROP_SIZE, QgsProperty.fromExpression(updated))
                    symbolLayer.setDataDefinedProperties(properties)

    def _getNodeSize(self, symbol):
        """Return the junction size actually drawn; falls back to symbol.size().

        Mirror of applyNodeSizeExpressions: the drawn size lives in a data-defined
        expression that beats setSize(), so reading the static size showed the value last
        typed here while the map drew another one — the Appearance factor writes only the
        expression. Line symbols never had this problem, because _getLineWidth reads the
        very property the factor writes.
        """
        for index in range(symbol.symbolLayerCount()):
            with suppress(Exception):
                properties = symbol.symbolLayer(index).dataDefinedProperties()
                sizeProperty = properties.property(SL_PROP_SIZE)
                if not sizeProperty.isActive():
                    continue
                junction, _ = read_node_base_sizes(sizeProperty.expressionString())
                if junction is not None:
                    return junction
        if hasattr(symbol, "size"):
            return symbol.size()
        # Line and fill symbols have no size(); fall back to a width read.
        return self._getLineWidth(symbol)

    def _getLineWidth(self, symbol):
        """Return the width of the first SimpleLine layer; falls back to symbol.width()."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "SimpleLine":
                return sl.width()
        return symbol.width() if hasattr(symbol, 'width') else 0.0

    def _setLineWidth(self, symbol, newWidth):
        """Set width on every SimpleLine layer directly (does not scale other layers like setWidth would)."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "SimpleLine":
                sl.setWidth(newWidth)

    INPUT_COLOR_READERS = {
        "qgisred_junctions": (SL_PROP_FILL_COLOR, r"BaseDem\s*>\s*0\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_demands": (
            SL_PROP_FILL_COLOR,
            r"(?:@bd|\"?Base(?:Value|Demand|Dem)\"?)\s*>\s*0\s*,\s*'(#[0-9a-fA-F]{3,6})'",
        ),
        "qgisred_pipes": (SL_PROP_STROKE_COLOR, r"IniStatus is NULL\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_valves": (SL_PROP_STROKE_COLOR, r"IniStatus is NULL\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_pumps": (SL_PROP_STROKE_COLOR, r"IniStatus is NULL\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_meters": (SL_PROP_FILL_COLOR, r"IsActive is NULL\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_serviceconnections": (SL_PROP_STROKE_COLOR, r"IsActive is NULL\s*,\s*'(#[0-9a-fA-F]{6})'"),
        "qgisred_isolationvalves": (SL_PROP_FILL_COLOR, r'LossCoeff"\s*=\s*0\s*,\s*color_rgb\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)\)'),
    }

    def _readInputLayerColor(self, symbol, identifier):
        entry = self.INPUT_COLOR_READERS.get(identifier)
        if not entry:
            return None
        propertyKey, regex = entry
        match = self._findExpressionMatch(symbol, propertyKey, re.compile(regex))
        if not match:
            return None
        groups = match.groups()
        if len(groups) == 1:
            return QColor(groups[0])
        return QColor(int(groups[0]), int(groups[1]), int(groups[2]))

    def _findExpressionMatch(self, symbol, propertyKey, pattern):
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            prop = sl.dataDefinedProperties().property(propertyKey)
            if prop and prop.propertyType() == QgsProperty.ExpressionBasedProperty:
                m = pattern.search(prop.expressionString())
                if m:
                    return m
            if hasattr(sl, "subSymbol") and sl.subSymbol():
                m = self._findExpressionMatch(sl.subSymbol(), propertyKey, pattern)
                if m:
                    return m
        return None

    def getUnitAbbrForLayer(self):
        if self.utils:
            layerIdentifier = self.currentLayer.customProperty("qgisred_identifier")
            field = resolve_layer_id(layerIdentifier) if layerIdentifier else None
            if field:
                return self.fieldUtils.getUnitAbbreviation(*field)
        return ""

    def generateRandomHsvColor(self):
        return QColor.fromHsv(random.randint(0, 359), random.randint(150, 255), random.randint(150, 255))  # nosec B311 — cosmetic legend color, not security-sensitive

    # ============================================================
    # APPLY AND SAVE LEGEND
    # ============================================================

    def applyLegend(self):
        if not self.currentLayer:
            return

        # setRenderer already rebuilds the layer's legend in the Layers Panel;
        # an extra refreshLayerSymbology here would rebuild the nodes twice in
        # one event-loop turn and can crash the panel's deferred repaint.
        renderer = self.buildRendererFromDialog()
        if renderer is not None:
            self.currentLayer.setRenderer(renderer)
            self._syncHydraulicSectorSibling(renderer)
            self._syncDemandBuilderLabelColors(renderer)
            # Last, so the rule-based wrap is what the layer ends up carrying: the
            # sibling sync above reads the graduated/categorized renderer as applied.
            self.restoreResultNullClass()

        self.currentLayer.triggerRepaint()
        self.ensureLayerVisible(self.currentLayer)
        self.originalRenderer = self.currentLayer.renderer().clone() if self.currentLayer.renderer() else None
        self.hasAppliedChanges = True

    def restoreResultNullClass(self):
        """Put a result layer back into the rule-based form the results dock expects.

        This dialog commits a graduated renderer, but a result layer is meant to carry the
        NULL class applyNullStyle adds, and two things break at once without it: features
        with no value stop being drawn at all — a graduated renderer skips NULLs outright,
        which is the whole reason that function exists — and every Appearance factor turns
        into a silent no-op, because applySymbolScaleFactors returns early on anything that
        is not rule-based.

        Same pair of steps the results dock runs itself after building a renderer.
        """
        if not self.isResultsLayer():
            return
        with suppress(Exception):
            QGISRedStylingUtils(
                self.projectDirectory, self.networkName, self.qgisInterface
            ).applyNullStyle(self.currentLayer)

    def _syncDemandBuilderLabelColors(self, appliedRenderer):
        """Rebuild the label color expression so labels keep matching their category symbol."""
        identifier = self.currentLayer.customProperty("qgisred_identifier") if self.currentLayer else None
        if identifier not in self.DEMANDS_BUILDER_EDITABLE_IDENTIFIERS:
            return
        if not isinstance(appliedRenderer, QgsCategorizedSymbolRenderer):
            return
        labeling = self.currentLayer.labeling()
        if labeling is None:
            return
        colorExpression = "CASE "
        for category in appliedRenderer.categories():
            symbol = category.symbol()
            if symbol is None:
                continue
            colorName = symbol.color().name()
            value = str(category.value())
            if value == "Uncategorized":
                colorExpression += (
                    "WHEN \"Category\" IS NULL OR trim(\"Category\") = '' "
                    "OR lower(trim(\"Category\")) IN ('null', 'undefined') "
                    f"THEN '{colorName}' "
                )
            else:
                safeValue = value.replace("'", "''")
                colorExpression += f"WHEN trim(\"Category\") = '{safeValue}' THEN '{colorName}' "
        colorExpression += "ELSE 'gray' END"
        settings = labeling.settings()
        settings.dataDefinedProperties().setProperty(PAL_PROPERTY_COLOR, QgsProperty.fromExpression(colorExpression))
        labeling.setSettings(settings)

    HYDRAULIC_SECTOR_SIBLINGS = {
        "qgisred_hydraulicsectors_links": "qgisred_hydraulicsectors_nodes",
        "qgisred_hydraulicsectors_nodes": "qgisred_hydraulicsectors_links",
    }

    def _syncHydraulicSectorSibling(self, appliedRenderer):
        """Recolor matching classes in the sibling Hydraulic Sectors layer after Apply.

        Lines and nodes with the same class value always end up with the same
        color. The sibling's pristine renderer is snapshotted so Cancel can
        restore it too.
        """
        identifier = self.currentLayer.customProperty("qgisred_identifier") if self.currentLayer else None
        siblingIdentifier = self.HYDRAULIC_SECTOR_SIBLINGS.get(identifier or "")
        if not siblingIdentifier:
            return
        sibling = self._findSiblingLayerInGroup(siblingIdentifier)
        if sibling is None or sibling.renderer() is None:
            return
        colorByValue = self._rendererValueColors(appliedRenderer)
        if not colorByValue:
            return
        newRenderer = self._recolorRendererByValue(sibling.renderer(), colorByValue)
        if newRenderer is None:
            return
        if sibling.id() not in self.initialRenderers:
            self.initialRenderers[sibling.id()] = sibling.renderer().clone()
        self._syncedSiblingIds.add(sibling.id())
        sibling.setRenderer(newRenderer)
        sibling.triggerRepaint()

    def _findSiblingLayerInGroup(self, siblingIdentifier):
        """Find a layer with the given identifier inside the current layer's tree group."""
        node = QgsProject.instance().layerTreeRoot().findLayer(self.currentLayer.id())
        parent = node.parent() if node else None
        if parent is None:
            return None
        for child in parent.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer and layer.customProperty("qgisred_identifier") == siblingIdentifier:
                    return layer
        return None

    def _rendererValueColors(self, renderer):
        """Map class value -> color for categorized or categorical rule-based renderers."""
        colors = {}
        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            for category in renderer.categories():
                if category.symbol() is not None and category.value() not in (None, ""):
                    colors[str(category.value())] = QColor(category.symbol().color())
        elif isinstance(renderer, QgsRuleBasedRenderer):
            for rule in renderer.rootRule().children():
                if _NULL_RULE_LABEL in (rule.label() or ""):
                    continue
                parsed = parseCategoricalRuleFilter(rule.filterExpression())
                if parsed and rule.symbol() is not None:
                    colors[parsed[1]] = QColor(rule.symbol().color())
        return colors

    def _recolorRendererByValue(self, renderer, colorByValue):
        """Return a recolored clone of renderer, or None when nothing matches."""
        if isinstance(renderer, QgsCategorizedSymbolRenderer):
            newRenderer = renderer.clone()
            changed = False
            for index, category in enumerate(newRenderer.categories()):
                value = str(category.value()) if category.value() is not None else "NULL"
                color = colorByValue.get(value)
                if color is None or category.symbol() is None:
                    continue
                symbol = category.symbol().clone()
                self.applyColorToSymbol(symbol, QColor(color))
                newRenderer.updateCategorySymbol(index, symbol)
                changed = True
            return newRenderer if changed else None
        if isinstance(renderer, QgsRuleBasedRenderer):
            newRenderer = renderer.clone()
            changed = False
            for rule in newRenderer.rootRule().children():
                if _NULL_RULE_LABEL in (rule.label() or ""):
                    continue
                parsed = parseCategoricalRuleFilter(rule.filterExpression())
                if not parsed or rule.symbol() is None:
                    continue
                color = colorByValue.get(parsed[1])
                if color is None:
                    continue
                symbol = rule.symbol().clone()
                self.applyColorToSymbol(symbol, QColor(color))
                rule.setSymbol(symbol)
                changed = True
            return newRenderer if changed else None
        return None

    def buildRendererFromDialog(self):
        """Build a renderer from the current dialog state without touching the live layer."""
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            return self.buildNumericRenderer()
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return self.buildCategoricalRenderer()
        if self.currentFieldType == self.FIELD_TYPE_SINGLE:
            return self.buildSingleSymbolRenderer()
        return None

    def ensureLayerVisible(self, layer):
        """Make the layer (and any hidden ancestor group) visible so applied changes can be seen."""
        node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        while node is not None and node.parent() is not None:
            if not node.itemVisibilityChecked():
                node.setItemVisibilityChecked(True)
            node = node.parent()

    PIPE_DEFAULT_WIDTH = 1.5
    PIPE_DEFAULT_CV_SIZE = 5
    JUNCTION_DEFAULT_SIZE = 1.3
    DEMANDS_DEFAULT_SIZE = 1.6
    VALVE_PUMP_DEFAULT_MARKER_SIZE = 5
    SERVICE_CONNECTION_DEFAULT_LINE_WIDTH = 1.4
    SERVICE_CONNECTION_DEFAULT_DOT_SIZE = 1.5
    SERVICE_CONNECTION_LIGHTEN_FRACTION = 0.10

    def buildSingleSymbolRenderer(self):
        # Mutate a clone, never the live renderer's symbol: the canvas render
        # jobs and the Layers Panel legend nodes share state with the live
        # symbol, and editing it in place is a use-after-free crash risk.
        liveRenderer = self.currentLayer.renderer()
        if not liveRenderer or liveRenderer.type() != "singleSymbol":
            return None

        renderer = liveRenderer.clone()
        symbol = renderer.symbol()
        if not symbol:
            return None

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        colorContainer = self.tableView.cellWidget(0, 1)
        sizeWidget = self.tableView.cellWidget(0, 2)

        newColor = None
        colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None
        if colorWidget and colorWidget.isEnabled():
            newColor = colorWidget.activeColor

        newSize = None
        with suppress(Exception):
            newSize = float(sizeWidget.text())

        inputAppliers = {
            "qgisred_junctions": self._applyJunctionsLegend,
            "qgisred_pipes": self._applyPipesLegend,
            "qgisred_valves": self._applyValvesLegend,
            "qgisred_pumps": self._applyPumpsLegend,
            "qgisred_meters": self._applyMetersLegend,
            "qgisred_serviceconnections": self._applyServiceConnectionsLegend,
            "qgisred_isolationvalves": self._applyIsolationValvesLegend,
            "qgisred_sources": self._applySourcesLegend,
            "qgisred_demands": self._applyDemandsLegend,
        }
        for sizeOnlyIdentifier in self.SIZE_ONLY_QUERY_IDENTIFIERS:
            inputAppliers[sizeOnlyIdentifier] = self._applySizeOnlyQueryLegend
        inputAppliers[self.TREE_NODES_IDENTIFIER] = self._applyTreeNodesLegend

        applier = inputAppliers.get(identifier)
        if applier:
            applier(symbol, newColor, newSize)
            return renderer

        if newColor is not None:
            self.applyColorToSymbol(symbol, newColor)
        if newSize is not None:
            self.applySizeToSymbol(symbol, newSize)
        return renderer

    def _setExpressionOnLayers(self, symbol, propertyKey, expression):
        """Set the data-defined expression on every symbol layer (recursive) that already has one for propertyKey."""
        newProp = QgsProperty.fromExpression(expression)
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            existing = sl.dataDefinedProperties().property(propertyKey)
            if existing and existing.propertyType() == QgsProperty.ExpressionBasedProperty:
                sl.setDataDefinedProperty(propertyKey, newProp)
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._setExpressionOnLayers(sl.subSymbol(), propertyKey, expression)

    def _substituteExpressionOnLayers(self, symbol, propertyKey, pattern, newText):
        """Substitute group 1 of pattern inside each layer's existing expression for propertyKey.

        Unlike _setExpressionOnLayers this keeps the rest of the expression
        (coalesce/with_variable retro-compat wrappers) untouched.
        Returns True when at least one expression changed.
        """
        anyChanged = False
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            existing = sl.dataDefinedProperties().property(propertyKey)
            if existing and existing.propertyType() == QgsProperty.ExpressionBasedProperty:
                newExpr, changed = substituteCapturedGroup(existing.expressionString(), pattern, newText)
                if changed:
                    sl.setDataDefinedProperty(propertyKey, QgsProperty.fromExpression(newExpr))
                    anyChanged = True
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                if self._substituteExpressionOnLayers(sl.subSymbol(), propertyKey, pattern, newText):
                    anyChanged = True
        return anyChanged

    def _forceExpressionOnLayers(self, symbol, propertyKey, expression):
        """Set the data-defined expression on every symbol layer (recursive), creating it when missing.

        Repair path for symbols that lost their expression (older builds
        applied flat colors over it): _setExpressionOnLayers and
        _substituteExpressionOnLayers only touch existing expressions.
        """
        newProp = QgsProperty.fromExpression(expression)
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            sl.setDataDefinedProperty(propertyKey, newProp)
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._forceExpressionOnLayers(sl.subSymbol(), propertyKey, expression)

    def _lightenColor(self, color, fraction):
        red = int(color.red() + (255 - color.red()) * fraction)
        green = int(color.green() + (255 - color.green()) * fraction)
        blue = int(color.blue() + (255 - color.blue()) * fraction)
        return QColor(red, green, blue)

    def _scalePipeCvMarker(self, symbol, newWidth):
        if newWidth <= 0:
            return
        scaleFactor = newWidth / self.PIPE_DEFAULT_WIDTH
        newCvSize = round(self.PIPE_DEFAULT_CV_SIZE * scaleFactor, 3)
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "MarkerLine":
                markerSymbol = sl.subSymbol()
                if markerSymbol:
                    for j in range(markerSymbol.symbolLayerCount()):
                        ml = markerSymbol.symbolLayer(j)
                        expr = f"if(IniStatus is NULL, 0,if(IniStatus !='CV', 0,{newCvSize}))"
                        ml.setDataDefinedProperty(SL_PROP_SIZE, QgsProperty.fromExpression(expr))

    def _scaleMarkerLineMarkerSize(self, symbol, defaultMarkerSize, newWidth, defaultWidth):
        """Scale every marker layer inside a MarkerLine proportionally to the line width."""
        if newWidth <= 0 or defaultWidth <= 0:
            return
        newSize = round(defaultMarkerSize * (newWidth / defaultWidth), 3)
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "MarkerLine":
                markerSymbol = sl.subSymbol()
                if markerSymbol:
                    for j in range(markerSymbol.symbolLayerCount()):
                        ml = markerSymbol.symbolLayer(j)
                        if hasattr(ml, "setSize"):
                            ml.setSize(newSize)

    def _applyJunctionsLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            fillExpr = (
                f"if (BaseDem is NULL, '#ffffff', if( BaseDem >0, '{userHex}', "
                f"if (BaseDem <0 , '#78b3dc', '#ffffff')))"
            )
            self._setExpressionOnLayers(symbol, SL_PROP_FILL_COLOR, fillExpr)
        if size is not None:
            scale = size / self.JUNCTION_DEFAULT_SIZE
            self._rebuildJunctionSize(symbol, scale)

    def _rebuildJunctionSize(self, symbol, scale):
        smallNoEmit = round(1.3 * scale, 3)
        bigNoEmit = round(3.5 * scale, 3)
        smallEmit = round(2.2 * scale, 3)
        bigEmit = round(4 * scale, 3)
        emitterExpr = (
            f"if (EmittCoef> 0, if (BaseDem is NULL, {smallEmit}, "
            f"if( BaseDem >0, {smallEmit}, if (BaseDem <0 , {bigEmit}, {smallEmit}))),0)"
        )
        noEmitterExpr = (
            f"if (EmittCoef>0, 0, if (BaseDem is NULL, {smallNoEmit}, "
            f"if( BaseDem >0, {smallNoEmit}, if (BaseDem <0 , {bigNoEmit}, {smallNoEmit}))))"
        )
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            existing = sl.dataDefinedProperties().property(SL_PROP_SIZE)
            if existing and existing.propertyType() == QgsProperty.ExpressionBasedProperty:
                expr = existing.expressionString()
                if re.search(r'EmittCoef\s*>\s*0\s*,\s*0\s*,', expr):
                    newExpr = noEmitterExpr
                else:
                    newExpr = emitterExpr
                sl.setDataDefinedProperty(SL_PROP_SIZE, QgsProperty.fromExpression(newExpr))
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._rebuildJunctionSize(sl.subSymbol(), scale)

    def _applyPipesLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            strokeExpr = f"if(IniStatus is NULL, '{userHex}',if(IniStatus !='CLOSED', '{userHex}','#ff0f13'))"
            self._setExpressionOnLayers(symbol, SL_PROP_STROKE_COLOR, strokeExpr)
            # The CV SvgMarker carries the same color rule on its fill — keep it in sync
            self._setExpressionOnLayers(symbol, SL_PROP_FILL_COLOR, strokeExpr)
        if size is not None:
            self._setLineWidth(symbol, size)
            self._scalePipeCvMarker(symbol, size)

    def _applyValvesLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            colorExpr = (
                f"if(IniStatus is NULL, '{userHex}',"
                f"if(IniStatus is 'CLOSED', '#ff0f13', "
                f"if(IniStatus !='ACTIVE', '{userHex}','#ff9900')))"
            )
            self._setExpressionOnLayers(symbol, SL_PROP_STROKE_COLOR, colorExpr)
            self._setExpressionOnLayers(symbol, SL_PROP_FILL_COLOR, colorExpr)
        if size is not None:
            self._setLineWidth(symbol, size)
            self._scaleMarkerLineMarkerSize(
                symbol, self.VALVE_PUMP_DEFAULT_MARKER_SIZE, size, self.PIPE_DEFAULT_WIDTH
            )

    def _applyPumpsLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            colorExpr = f"if(IniStatus is NULL, '{userHex}',if(IniStatus !='CLOSED', '{userHex}','#ff0f13'))"
            self._setExpressionOnLayers(symbol, SL_PROP_STROKE_COLOR, colorExpr)
            self._setExpressionOnLayers(symbol, SL_PROP_FILL_COLOR, colorExpr)
        if size is not None:
            self._setLineWidth(symbol, size)
            self._scaleMarkerLineMarkerSize(
                symbol, self.VALVE_PUMP_DEFAULT_MARKER_SIZE, size, self.PIPE_DEFAULT_WIDTH
            )

    def _applyMetersLegend(self, symbol, color, size):
        selectedType = self.getSelectedMeterType()
        if color is not None:
            userHex = color.name().lower()
            self._applyMeterFill(symbol, userHex, selectedType)
        if size is not None:
            self._rebuildMeterSizes(symbol, size, selectedType)

    def _meterLayerType(self, sl):
        """Return the meter type gating this symbol layer's size/width expression, or None."""
        for propertyKey in (SL_PROP_SIZE, SL_PROP_WIDTH):
            prop = sl.dataDefinedProperties().property(propertyKey)
            if prop and prop.propertyType() == QgsProperty.ExpressionBasedProperty:
                meterType = extractMeterTypeFromExpression(prop.expressionString())
                if meterType:
                    return meterType
        return None

    def _applyMeterFill(self, symbol, userHex, onlyType=None):
        """Substitute the active-branch fill colors in place, optionally for one meter type only."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if onlyType is None or self._meterLayerType(sl) == onlyType:
                existing = sl.dataDefinedProperties().property(SL_PROP_FILL_COLOR)
                if existing and existing.propertyType() == QgsProperty.ExpressionBasedProperty:
                    expr = existing.expressionString()
                    changedAny = False
                    for pattern in METER_ACTIVE_FILL_PATTERNS:
                        expr, changed = substituteCapturedGroup(expr, pattern, userHex)
                        changedAny = changedAny or changed
                    if changedAny:
                        sl.setDataDefinedProperty(
                            SL_PROP_FILL_COLOR, QgsProperty.fromExpression(expr)
                        )
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._applyMeterFill(sl.subSymbol(), userHex, onlyType)

    def _rebuildMeterSizes(self, symbol, newSize, onlyType=None):
        # The Meters QML binds the size expression to "width" on SvgMarker layers,
        # so probe both keys and write back to whichever holds the rule.
        sizeKeys = (SL_PROP_SIZE, SL_PROP_WIDTH)
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            for propertyKey in sizeKeys:
                existing = sl.dataDefinedProperties().property(propertyKey)
                if not existing or existing.propertyType() != QgsProperty.ExpressionBasedProperty:
                    continue
                expr = existing.expressionString()
                newExpr, meterType = rewriteMeterSizeExpression(expr, newSize, onlyType)
                if meterType is not None and newExpr != expr:
                    sl.setDataDefinedProperty(propertyKey, QgsProperty.fromExpression(newExpr))
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._rebuildMeterSizes(sl.subSymbol(), newSize, onlyType)

    def _readSelectedMeterTypeSize(self, symbol):
        """Current visible size of the selected meter type, or None when not applicable."""
        if not self.currentLayer or self.currentLayer.customProperty("qgisred_identifier") != "qgisred_meters":
            return None
        meterType = self.getSelectedMeterType()
        if not meterType:
            return None
        pattern = re.compile(
            r"(?:@mt|\"?Type\"?)\s*=\s*'" + re.escape(meterType) + r"'\s*,\s*(\d+(?:\.\d+)?)"
        )
        for propertyKey in (SL_PROP_SIZE, SL_PROP_WIDTH):
            match = self._findExpressionMatch(symbol, propertyKey, pattern)
            if match:
                return float(match.group(1))
        return None

    def _applyServiceConnectionsLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            lighterColor = self._lightenColor(color, self.SERVICE_CONNECTION_LIGHTEN_FRACTION)
            lighterHex = lighterColor.name().lower()
            for pattern in SERVICE_CONNECTION_ACTIVE_STROKE_PATTERNS:
                self._substituteExpressionOnLayers(
                    symbol, SL_PROP_STROKE_COLOR, pattern, userHex
                )
            self._substituteExpressionOnLayers(
                symbol, SL_PROP_FILL_COLOR,
                SERVICE_CONNECTION_ACTIVE_FILL_PATTERN, lighterHex
            )
            self._recolorServiceConnectionBaseLayers(symbol, color, lighterColor)
        if size is not None:
            self._setLineWidth(symbol, size)
            self._scaleMarkerLineMarkerSize(
                symbol, self.SERVICE_CONNECTION_DEFAULT_DOT_SIZE,
                size, self.SERVICE_CONNECTION_DEFAULT_LINE_WIDTH
            )

    def _recolorServiceConnectionBaseLayers(self, symbol, userColor, lighterColor):
        """Recolor the base (non-expression) colors so the legend swatch matches the user pick."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "SimpleLine":
                sl.setColor(userColor)
            elif sl.layerType() == "MarkerLine" and sl.subSymbol():
                markerSymbol = sl.subSymbol()
                for j in range(markerSymbol.symbolLayerCount()):
                    ml = markerSymbol.symbolLayer(j)
                    ml.setColor(lighterColor)
                    if hasattr(ml, "setStrokeColor"):
                        ml.setStrokeColor(userColor)

    def _applyIsolationValvesLegend(self, symbol, color, size):
        if color is not None:
            rgb = f"color_rgb({color.red()},{color.green()},{color.blue()})"
            # Only the "LossCoeff" = 0 green branch changes; the closed/loss/unavailable
            # colors and any coalesce() retro-compat wrapper stay as they are.
            changed = self._substituteExpressionOnLayers(
                symbol, SL_PROP_FILL_COLOR, ISOLATION_VALVE_GREEN_PATTERN, rgb
            )
            if not changed:
                # The status expression is gone (older builds applied flat colors
                # over it, freezing every valve on one color): restore the shipped
                # expression with the picked color in the green slot so closed /
                # with-loss / unavailable valves get their status colors back.
                self._forceExpressionOnLayers(
                    symbol,
                    SL_PROP_FILL_COLOR,
                    ISOLATION_VALVE_FILL_TEMPLATE.format(green=rgb),
                )
            # Keep the base color in sync: the Layers Panel icon shows it, and
            # QGIS falls back to it if the expression ever fails to evaluate.
            symbol.setColor(color)
        if size is not None:
            self.applySizeToSymbol(symbol, size)

    def _applySourcesLegend(self, symbol, color, size):
        if size is not None:
            self.applySizeToSymbol(symbol, size)

    @staticmethod
    def _circleMarkerLayers(symbol):
        """The SimpleMarker circle layers of a stacked marker symbol (e.g. the
        Tree nodes outer circle, drawn under the star and the element icons)."""
        return [
            symbol.symbolLayer(i)
            for i in range(symbol.symbolLayerCount())
            if symbol.symbolLayer(i).layerType() == "SimpleMarker"
            and symbol.symbolLayer(i).properties().get("name") == "circle"
        ]

    def _circleOnlySymbol(self, symbol):
        """A clone of symbol keeping only its SimpleMarker circle layers."""
        preview = symbol.clone()
        for i in range(preview.symbolLayerCount() - 1, -1, -1):
            symbolLayer = preview.symbolLayer(i)
            if not (symbolLayer.layerType() == "SimpleMarker" and symbolLayer.properties().get("name") == "circle"):
                preview.deleteSymbolLayer(i)
        return preview

    def _applyTreeNodesLegend(self, symbol, color, size):
        """Tree nodes: the color goes to the outer circle's stroke only (the star
        and the element icons keep theirs); size rescales like the other
        size-only query layers."""
        if color is not None:
            for circle in self._circleMarkerLayers(symbol):
                circle.setStrokeColor(color)
        self._applySizeOnlyQueryLegend(symbol, None, size)

    def _applySizeOnlyQueryLegend(self, symbol, color, size):
        """Proportionally rescale a size-only query layer (tree nodes, isolated segments...).

        These styles gate sub-layer visibility with data-defined size/width
        expressions, so everything is scaled by one factor: zeros stay zero and
        the per-layer proportions survive. The factor is anchored on the value
        the size cell displays, so an untouched cell is a strict no-op. Color is
        ignored: the color column is locked for these layers.
        """
        if size is None or size <= 0:
            return
        isLine = self.currentLayer and self.currentLayer.geometryType() == WKB_LINE_GEOMETRY
        currentSize = None
        with suppress(Exception):
            currentSize = float(self._getLineWidth(symbol) if isLine else symbol.size())
        if not currentSize or currentSize <= 0 or abs(size - currentSize) < 1e-9:
            return
        factor = size / currentSize
        for propertyKey in (
            SL_PROP_SIZE,
            SL_PROP_WIDTH,
            SL_PROP_STROKE_WIDTH,
        ):
            self._scaleSizeExpressionsOnLayers(symbol, propertyKey, factor)
        if isLine:
            self._scaleBaseSizes(symbol, factor)
        else:
            with suppress(Exception):
                symbol.setSize(size)

    def _scaleBaseSizes(self, symbol, factor):
        """Scale every layer's base width/size by factor, preserving per-layer ratios."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            if sl.layerType() == "SimpleLine":
                sl.setWidth(sl.width() * factor)
            elif hasattr(sl, "size") and hasattr(sl, "setSize"):
                with suppress(Exception):
                    sl.setSize(sl.size() * factor)
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._scaleBaseSizes(sl.subSymbol(), factor)

    def _applyDemandsLegend(self, symbol, color, size):
        if color is not None:
            userHex = color.name().lower()
            # Only the inner marker carries the fill expression, and only its
            # positive-demand branch takes the new color (like Junctions); the
            # negative color, the white base branches, strokes and the outer
            # marker stay untouched.
            self._substituteExpressionOnLayers(
                symbol, SL_PROP_FILL_COLOR, DEMAND_POSITIVE_FILL_PATTERN, userHex
            )
        if size is not None and size > 0:
            # The size cell shows the overall symbol size, so an untouched cell must
            # be a strict no-op: scale expressions and base sizes only on a real change.
            currentSize = None
            with suppress(Exception):
                currentSize = float(symbol.size())
            if currentSize and currentSize > 0 and abs(size - currentSize) > 1e-9:
                self._scaleSizeExpressionsOnLayers(symbol, SL_PROP_SIZE, size / currentSize)
                with suppress(Exception):
                    symbol.setSize(size)

    def _scaleSizeExpressionsOnLayers(self, symbol, propertyKey, factor):
        """Scale every numeric literal of each layer's size expression by factor (recursive)."""
        for i in range(symbol.symbolLayerCount()):
            sl = symbol.symbolLayer(i)
            existing = sl.dataDefinedProperties().property(propertyKey)
            if existing and existing.propertyType() == QgsProperty.ExpressionBasedProperty:
                newExpr = scaleNumericLiterals(existing.expressionString(), factor)
                sl.setDataDefinedProperty(propertyKey, QgsProperty.fromExpression(newExpr))
            if hasattr(sl, 'subSymbol') and sl.subSymbol():
                self._scaleSizeExpressionsOnLayers(sl.subSymbol(), propertyKey, factor)

    def buildNumericRenderer(self):
        ranges = []
        isProportionalMode = self.cbSizes.currentText() == "Proportional to Value"

        # Get existing renderer to clone symbols from (preserving complex symbol structures)
        existingRenderer = self.currentLayer.renderer()
        if isinstance(existingRenderer, QgsRuleBasedRenderer):
            existingRenderer = self.ruleBasedAsGraduated(existingRenderer)
        existingRanges = existingRenderer.ranges() if isinstance(existingRenderer, QgsGraduatedSymbolRenderer) else []

        for row in range(self.tableView.rowCount()):
            values = self.getRangeValues(row)
            if not values:
                continue

            checkboxContainer = self.tableView.cellWidget(row, 0)
            colorContainer = self.tableView.cellWidget(row, 1)
            legendWidget = self.tableView.cellWidget(row, 4)
            sizeWidget = self.tableView.cellWidget(row, 2)

            checkbox = checkboxContainer.findChild(QCheckBox) if checkboxContainer else None
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            # Clone existing symbol to preserve complex structure
            if row < len(existingRanges) and existingRanges[row].symbol():
                symbol = existingRanges[row].symbol().clone()
            else:
                symbol = self.templateSymbol([r.symbol() for r in existingRanges])

            if colorWidget:
                self.applyColorToSymbol(symbol, colorWidget.activeColor)

            with suppress(Exception):
                size = float(sizeWidget.text())
                self.applySizeToSymbol(symbol, size)

            if isProportionalMode:
                self.applyProportionalSizeExpression(symbol)

            rangeObj = QgsRendererRange(
                values[0], values[1], symbol, legendWidget.text()
            )
            rangeObj.setRenderState(checkbox.isChecked() if checkbox else True)
            ranges.append(rangeObj)

        if ranges:
            return QgsGraduatedSymbolRenderer(self.currentFieldName, ranges)
        return None

    def applyProportionalSizeExpression(self, symbol):
        minSize = self.spinSizeMin.value()
        maxSize = self.spinSizeMax.value()
        fieldName = self.currentFieldName
        isLine = self.currentLayer.geometryType() == WKB_LINE_GEOMETRY

        if self.ckSizeInvert.isChecked():
            firstSize, secondSize = maxSize, minSize
        else:
            firstSize, secondSize = minSize, maxSize
        expression = (
            f'coalesce(scale_polynomial("{fieldName}", minimum("{fieldName}"), maximum("{fieldName}"), '
            f"{firstSize}, {secondSize}, {PROPORTIONAL_SIZE_EXPONENT}), {firstSize})"
        )

        sizeProperty = QgsProperty.fromExpression(expression)

        for i in range(symbol.symbolLayerCount()):
            symbolLayer = symbol.symbolLayer(i)
            if isLine:
                symbolLayer.setDataDefinedProperty(SL_PROP_STROKE_WIDTH, sizeProperty)
            else:
                symbolLayer.setDataDefinedProperty(SL_PROP_SIZE, sizeProperty)

    def buildCategoricalRenderer(self):
        if self._sourceRuleRenderer is not None:
            return self.buildRuleBasedCategoricalRenderer()

        categories = []

        # Get existing renderer to clone symbols from (preserving complex symbol structures)
        existingRenderer = self.currentLayer.renderer()
        existingCategories = existingRenderer.categories() if isinstance(existingRenderer, QgsCategorizedSymbolRenderer) else []

        # Build a map of value -> symbol for quick lookup
        existingSymbolMap = {}
        for cat in existingCategories:
            catValue = str(cat.value()) if cat.value() is not None else "NULL"
            existingSymbolMap[catValue] = cat.symbol()

        for row in range(self.tableView.rowCount()):
            checkboxContainer = self.tableView.cellWidget(row, 0)
            colorContainer = self.tableView.cellWidget(row, 1)
            legendWidget = self.tableView.cellWidget(row, 4)
            valueWidget = self.tableView.cellWidget(row, 3)
            sizeWidget = self.tableView.cellWidget(row, 2)

            checkbox = checkboxContainer.findChild(QCheckBox) if checkboxContainer else None
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            value = valueWidget.text() if isinstance(valueWidget, QLineEdit) else ""
            label = legendWidget.text()

            realValue = self.determineRealCategoricalValue(value, label)

            # Clone existing symbol to preserve complex structure
            lookupKey = value if value not in [self.tr("Other Values"), "Other Values"] else ""
            if lookupKey in existingSymbolMap and existingSymbolMap[lookupKey]:
                symbol = existingSymbolMap[lookupKey].clone()
            else:
                symbol = self.templateSymbol(list(existingSymbolMap.values()))

            if colorWidget:
                self.applyColorToSymbol(symbol, colorWidget.activeColor)

            with suppress(Exception):
                size = float(sizeWidget.text())
                self.applySizeToSymbol(symbol, size)

            category = QgsRendererCategory(realValue, symbol, label)
            category.setRenderState(checkbox.isChecked() if checkbox else True)
            categories.append(category)

        if categories:
            return QgsCategorizedSymbolRenderer(self.currentFieldName, categories)
        return None

    def buildRuleBasedCategoricalRenderer(self):
        """Rebuild the source rule-based renderer with the table's colors, sizes, labels and visibility.

        Rule filters are kept as they are (including composite ones like the
        Hydraulic Sectors ClosedLinks split and the hidden NULL rules), so the
        renderer is never flattened into a categorized one.
        """
        renderer = self._sourceRuleRenderer.clone()
        rootRule = renderer.rootRule()

        ruleByValue = {}
        for rule in rootRule.children():
            if _NULL_RULE_LABEL in (rule.label() or ""):
                continue
            parsed = parseCategoricalRuleFilter(rule.filterExpression())
            if parsed:
                ruleByValue[parsed[1]] = rule

        matchedValues = set()
        for row in range(self.tableView.rowCount()):
            checkboxContainer = self.tableView.cellWidget(row, 0)
            colorContainer = self.tableView.cellWidget(row, 1)
            sizeWidget = self.tableView.cellWidget(row, 2)
            valueWidget = self.tableView.cellWidget(row, 3)
            legendWidget = self.tableView.cellWidget(row, 4)

            checkbox = checkboxContainer.findChild(QCheckBox) if checkboxContainer else None
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector) if colorContainer else None

            value = valueWidget.text() if isinstance(valueWidget, QLineEdit) else ""
            label = legendWidget.text()
            checked = checkbox.isChecked() if checkbox else True
            matchedValues.add(value)

            rule = ruleByValue.get(value)
            if rule is not None:
                symbol = rule.symbol().clone() if rule.symbol() else QgsSymbol.defaultSymbol(
                    self.currentLayer.geometryType()
                )
            else:
                symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())

            if colorWidget:
                self.applyColorToSymbol(symbol, colorWidget.activeColor)
            with suppress(Exception):
                size = float(sizeWidget.text())
                self.applySizeToSymbol(symbol, size)

            if rule is not None:
                rule.setSymbol(symbol)
                rule.setLabel(label)
                rule.setActive(checked)
            else:
                if value == "" or label in [self.tr("Other Values"), "Other Values"]:
                    filterExpr = "ELSE"
                else:
                    filterExpr = f"\"{self.currentFieldName}\" = '{value}'"
                newRule = QgsRuleBasedRenderer.Rule(symbol, 0, 0, filterExpr, label)
                newRule.setActive(checked)
                rootRule.appendChild(newRule)

        for value, rule in ruleByValue.items():
            if value not in matchedValues:
                rootRule.removeChild(rule)

        return renderer

    def determineRealCategoricalValue(self, value, label):
        if value == "NULL":
            return None
        if value == "" and label in [self.tr("Other Values"), "Other Values"]:
            return ""
        return value

    # ============================================================
    # STYLE MANAGEMENT
    # ============================================================

    def saveProjectStyle(self):
        self.saveStyle(globalStyle=False)

    def saveGlobalStyle(self):
        self.saveStyle(globalStyle=True)

    def saveStyle(self, globalStyle):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            QMessageBox.warning(
                self,
                self.tr("Cannot Save"),
                self.tr("This layer is not managed by QGISRed and its style cannot be saved here."),
            )
            return

        name = self.getElementNameForIdentifier(identifier)
        if not name:
            QMessageBox.warning(
                self,
                self.tr("Cannot Save"),
                self.tr("Saving styles from this dialog is not supported for this layer type."),
            )
            return

        filename = self.getStyleBasename(name) + ".qml" if globalStyle else self.getProjectStyleFilename(name)
        folder = self.getStyleFolder(globalStyle)

        if not folder:
            return

        if not os.path.exists(folder):
            os.makedirs(folder)

        path = os.path.join(folder, filename)

        selectedParts = self.promptForStrategyParts(globalStyle)
        if selectedParts is None:
            return

        if os.path.exists(path):
            reply = QMessageBox.question(
                self,
                self.tr("Overwrite"),
                self.tr("Overwrite style?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.saveDialogLegendToFile(path, selectedParts)
        if globalStyle:
            message = self.tr("The current legend was saved as %1 in the global layerStyles folder.")
        else:
            message = self.tr("The current legend was saved as %1 in the layerStyles folder of your project.")
        QMessageBox.information(self, self.tr("Saved"), message.replace("%1", filename))

    def saveDialogLegendToFile(self, path, selectedParts):
        """Write the legend shown in the dialog to a QML via a detached copy of the layer.

        The live layer must stay untouched (only Apply changes it): temporarily
        applying and restoring its renderer swaps the Layers Panel legend twice
        per save and can crash its deferred repaint.
        """
        tempLayer = QgsVectorLayer(self.currentLayer.source(), self.currentLayer.name(), self.currentLayer.providerType())
        if not tempLayer.isValid():
            return

        # Carry over the full live style (labeling, custom properties, ...) so the
        # saved QML only differs in what the dialog edits.
        style = QgsMapLayerStyle()
        style.readFromLayer(self.currentLayer)
        style.writeToLayer(tempLayer)

        renderer = self.buildRendererFromDialog()
        if renderer is not None:
            tempLayer.setRenderer(renderer)

        strategy = self.buildStrategyFromCurrentUi(selectedParts, renderer) if selectedParts else None
        if strategy is not None:
            tempLayer.setCustomProperty("qgisred_legend_strategy", json.dumps(strategy))
        else:
            tempLayer.removeCustomProperty("qgisred_legend_strategy")
        tempLayer.saveNamedStyle(path)

    def promptForStrategyParts(self, globalStyle):
        applicableParts = self.getBuildableStrategyParts()
        if not applicableParts:
            return []

        isCategorical = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
        structuralApplicable = "allClasses" in applicableParts or "intervals" in applicableParts

        dialog = QGISRedSaveStrategyDialog(
            self.currentLayer.name(),
            globalStyle,
            isCategorical,
            structuralApplicable,
            "sizes" in applicableParts,
            "colors" in applicableParts,
            parent=self,
        )
        if dialog.exec_() != QDialog.DialogCode.Accepted:
            return None

        return dialog.selectedParts()

    def strategyParts(self, strategy):
        if not isinstance(strategy, dict):
            return []
        parts = strategy.get("parts")
        if not isinstance(parts, list):
            parts = self.inferLegacyParts(strategy)
        return parts

    def applyStrategyToDialog(self, strategy):
        if not isinstance(strategy, dict):
            return

        parts = self.strategyParts(strategy)

        mode = strategy.get("mode")
        desiredType = {"graduated": "graduatedSymbol", "categorized": "categorizedSymbol"}.get(mode)
        if desiredType and desiredType != self.getCurrentRendererType():
            index = self.cbLegendsType.findData(desiredType)
            if index >= 0:
                self.cbLegendsType.setCurrentIndex(index)

        if mode == "categorized" and self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            # With pinned classes (allClasses) the class list must not be re-derived from data.
            if "allClasses" not in parts and any(part in parts for part in ("intervals", "sizes", "colors")):
                self.classifyMissingUniqueValues()

        if "intervals" in parts:
            self.restoreIntervalsUi(self.readPartBlock(strategy, "intervals"))
        if "sizes" in parts:
            self.restoreSizesUi(self.readPartBlock(strategy, "sizes"))
        if "colors" in parts:
            self.restoreColorsUi(self.readPartBlock(strategy, "colors"))

    def readPartBlock(self, strategy, partName):
        block = strategy.get(partName)
        if isinstance(block, dict):
            return block
        # v1 fallback: intervals + colors lived under "graduated"/"categorized"
        legacy = strategy.get("graduated") or strategy.get("categorized") or {}
        return legacy

    def inferLegacyParts(self, strategy):
        mode = strategy.get("mode")
        if mode == "graduated":
            return ["intervals", "colors"]
        if mode == "categorized":
            return ["colors"]
        return []

    def restoreIntervalsUi(self, intervalsBlock):
        classificationMode = intervalsBlock.get("classificationMode")
        if classificationMode:
            index = self.cbMode.findData(classificationMode)
            if index >= 0:
                self.cbMode.setCurrentIndex(index)
        classes = intervalsBlock.get("classes")
        if isinstance(classes, int) and classes > 0:
            self.leClassCount.setValue(classes)

    def restoreSizesUi(self, sizesBlock):
        sizeMode = sizesBlock.get("mode")
        if sizeMode:
            index = self.cbSizes.findText(sizeMode)
            if index >= 0:
                self.cbSizes.setCurrentIndex(index)
        if "value" in sizesBlock:
            self.spinSizeEqual.setValue(float(sizesBlock.get("value") or 0.0))
        if "min" in sizesBlock:
            self.spinSizeMin.setValue(float(sizesBlock.get("min") or 0.0))
        if "max" in sizesBlock:
            self.spinSizeMax.setValue(float(sizesBlock.get("max") or 0.0))
        if "invert" in sizesBlock:
            self.ckSizeInvert.setChecked(bool(sizesBlock.get("invert")))
        self.onSizeModeChanged()

    def restoreColorsUi(self, colorsBlock):
        source = colorsBlock.get("source") or colorsBlock.get("colorSource")
        rampName = colorsBlock.get("rampName")
        invertRamp = colorsBlock.get("invertRamp", False)
        if source == "ramp":
            self.cbColors.setCurrentText("Ramp")
            if rampName:
                self.btnColorRamp.setActiveRampByName(rampName)
            self.ckColorInvert.setChecked(bool(invertRamp))
            self.applyColorLogic()
        elif source == "random":
            self.cbColors.setCurrentText("Random")
            self.applyColorLogic(forceRefresh=True)

    def readStrategyFromStyleFile(self, path):
        # Reads the saved strategy from a .qml without mutating the live layer.
        tempLayer = QgsVectorLayer(self.currentLayer.source(), self.currentLayer.name(), self.currentLayer.providerType())
        if not tempLayer.isValid():
            return None
        tempLayer.loadNamedStyle(path)
        rawStrategy = tempLayer.customProperty("qgisred_legend_strategy")
        if not rawStrategy:
            return None
        try:
            return json.loads(rawStrategy)
        except Exception:
            return None

    def isLiteralStyle(self, strategy):
        if not isinstance(strategy, dict):
            return True
        return self.strategyParts(strategy) == ["allClasses"]

    def loadLiteralStyleIntoDialog(self, path):
        # Load the style into a detached copy of the layer so the live layer
        # stays untouched; the dialog previews the legend and only Apply commits it.
        tempLayer = QgsVectorLayer(self.currentLayer.source(), self.currentLayer.name(), self.currentLayer.providerType())
        if not tempLayer.isValid():
            return
        tempLayer.loadNamedStyle(path)
        renderer = tempLayer.renderer().clone() if tempLayer.renderer() else None
        if renderer is None:
            return
        self.populateDialogFromRenderer(renderer)

    def populateDialogFromRenderer(self, renderer):
        """Show the given renderer in the dialog without touching the live layer."""
        self.currentFieldType, self.currentFieldName = self.detectFieldType(self.currentLayer, renderer)
        self.syncLegendTypeComboBox(self.currentLayer, renderer)
        self.resetAllModesToManual()
        self.updateUiBasedOnFieldType()
        self._workingRenderer = renderer
        self.populateLegendTable()
        self.updateButtonStates()
        self.updateInputLayerRestrictions()

    def loadDefaultStyle(self):
        self.loadStyle(isDefault=True)

    def loadGlobalStyle(self):
        self.loadStyle(isDefault=False)

    def loadProjectStyle(self):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            QMessageBox.warning(
                self,
                self.tr("Cannot Load"),
                self.tr("This layer is not managed by QGISRed and its style cannot be loaded here."),
            )
            return

        name = self.getElementNameForIdentifier(identifier)
        if not name:
            QMessageBox.warning(
                self,
                self.tr("Cannot Load"),
                self.tr("Loading styles from this dialog is not supported for this layer type."),
            )
            return

        filename = self.getProjectStyleFilename(name)
        projectDir = self.getProjectDirectoryFromUtils()

        if not projectDir:
            QMessageBox.warning(self, self.tr("No Project"), self.tr("Project directory not set."))
            return

        folder = os.path.join(projectDir, "layerStyles")
        # Same lookup setStyle uses, so this finds whatever it would load.
        path = QGISRedStylingUtils.findStyleFile(folder, [filename])

        if not path:
            QMessageBox.warning(self, self.tr("Not Found"),
                                self.tr("Style file not found: %1").replace("%1", os.path.join(folder, filename)))
            return

        strategy = self.readStrategyFromStyleFile(path)
        if self.isLiteralStyle(strategy):
            self.loadLiteralStyleIntoDialog(path)
            message = self.tr("Legend loaded into the dialog from %1. Press Apply to update the layer.").replace("%1", filename)
        else:
            if "allClasses" in self.strategyParts(strategy):
                # Pin the saved classes from the QML, then regenerate colors/sizes on top.
                self.loadLiteralStyleIntoDialog(path)
            self.applyStrategyToDialog(strategy)
            message = self.tr("Strategy loaded into the dialog from %1. Press Apply to update the layer.").replace("%1", filename)
        QMessageBox.information(self, self.tr("Loaded"), message)

    def loadStyle(self, isDefault):
        if not self.currentLayer:
            return

        identifier = self.currentLayer.customProperty("qgisred_identifier")
        if not identifier:
            QMessageBox.warning(
                self,
                self.tr("Cannot Load"),
                self.tr("This layer is not managed by QGISRed and its style cannot be loaded here."),
            )
            return

        name = self.getElementNameForIdentifier(identifier)
        if not name:
            QMessageBox.warning(
                self,
                self.tr("Cannot Load"),
                self.tr("Loading styles from this dialog is not supported for this layer type."),
            )
            return

        filename = self.getStyleBasename(name) + ".qml" + (".bak" if isDefault else "")
        subfolder = os.path.join("defaults", "layerStyles") if isDefault else "layerStyles"
        folder = os.path.join(self.pluginFolder if isDefault else self.getQGISRedDirectoryFromUtils(), subfolder)
        # Same lookup setStyle uses, so this finds whatever it would load.
        path = QGISRedStylingUtils.findStyleFile(folder, [filename])

        if not path:
            QMessageBox.warning(self, self.tr("Not Found"),
                                self.tr("Style file not found: %1").replace("%1", os.path.join(folder, filename)))
            return

        if isDefault:
            # Restoring the default must rebuild the shipped expressions, symbol layers
            # and labels, which the dialog cannot recreate, so the file goes straight
            # onto the live layer instead of only into the dialog table.
            self.applyStyleFileToLayer(path)
            message = self.tr("Default style applied to the layer from %1.").replace("%1", filename)
            QMessageBox.information(self, self.tr("Loaded"), message)
            return

        strategy = self.readStrategyFromStyleFile(path)
        if self.isLiteralStyle(strategy):
            self.loadLiteralStyleIntoDialog(path)
            message = self.tr("Legend loaded into the dialog from %1. Press Apply to update the layer.").replace("%1", filename)
        else:
            if "allClasses" in self.strategyParts(strategy):
                # Pin the saved classes from the QML, then regenerate colors/sizes on top.
                self.loadLiteralStyleIntoDialog(path)
            self.applyStrategyToDialog(strategy)
            message = self.tr("Strategy loaded into the dialog from %1. Press Apply to update the layer.").replace("%1", filename)
        QMessageBox.information(self, self.tr("Loaded"), message)

    def applyStyleFileToLayer(self, path):
        self.currentLayer.loadNamedStyle(path)
        self.restoreResultNullClass()
        self.currentLayer.triggerRepaint()
        self.ensureLayerVisible(self.currentLayer)
        self.originalRenderer = self.currentLayer.renderer().clone() if self.currentLayer.renderer() else None
        self.hasAppliedChanges = True
        renderer = self.currentLayer.renderer().clone() if self.currentLayer.renderer() else None
        if renderer is not None:
            self.populateDialogFromRenderer(renderer)

    # Appearance settings that rewrite a result layer's symbols, with the value that means
    # "untouched". Decimals and labels also live in that file but change nothing here, so
    # they must not raise the warning — see hasAppearanceOverrides.
    _APPEARANCE_SYMBOL_SETTINGS = (
        ("Symbols", "pipeFactor", "1.0"),
        ("Symbols", "symbolFactor", "1.0"),
        ("Symbols", "arrowFactor", "1.0"),
        ("Symbols", "proportional", "false"),
        ("Symbols", "nodeBorder", "false"),
    )

    def appearanceConfigPath(self):
        """The results dock's appearance file for this network, or None without a project."""
        if not self.projectDirectory or not self.networkName:
            return None
        return os.path.join(self.projectDirectory, DIR_RESULTS,
                            self.networkName + "_Results_Config.cfg")

    def hasAppearanceOverrides(self):
        """True when the Appearance tab is currently rewriting the result symbols.

        Read from the file rather than from the dock so the dialog stays independent of it.
        The mere presence of the file means nothing: it is also written when only decimals
        or labels change, and warning about those would train the user to ignore this.
        """
        path = self.appearanceConfigPath()
        if not path or not os.path.isfile(path):
            return False
        try:
            root = ET.parse(path).getroot()  # nosec B314 — local file written by this plugin
        except Exception:
            return False
        for section, attribute, default in self._APPEARANCE_SYMBOL_SETTINGS:
            element = root.find(section)
            if element is None:
                continue
            value = element.get(attribute, default).strip().lower()
            if value == default:
                continue
            if default in ("true", "false"):
                return True
            try:
                # 1, 1.0 and 1.000000 all mean the factor was left alone.
                if float(value) != float(default):
                    return True
            except ValueError:
                return True
        return False

    def updateAppearanceWarning(self):
        """Show the banner only on result layers whose symbols Appearance is rewriting."""
        isResult = bool(self.currentLayer) and self.isResultsLayer()
        if isResult and self.hasAppearanceOverrides():
            # duration=0: it reflects a state, so it must stay up until the state changes
            self.appearanceWarningBanner.pushMessage(
                self.tr("Warning"),
                self.tr(
                    "The Appearance tab of the Results panel is changing this layer's symbols. Sizes "
                    "shown here ignore those settings, so editing them may leave the style "
                    "inconsistent: reset Appearance first."
                ),
                level=1,
                duration=0,
            )
        else:
            self.appearanceWarningBanner.hide()

    def getStyleBasename(self, name):
        styleURI = self.currentLayer.customProperty("styleURI") if self.currentLayer else None
        if styleURI:
            basename = os.path.basename(styleURI)
            if basename.endswith(".bak"):
                basename = basename[:-4]
            if basename.endswith(".qml"):
                basename = basename[:-4]
            if basename:
                return basename
        return name.replace(" ", "")

    def getResultStyleName(self, identifier):
        """QML name the results dock loads for this layer, e.g. "NodePressure".

        None when the layer is not a result layer. Never derived from layer.name(), which
        is translated and would yield a different file name in every language.
        """
        if identifier.startswith("qgisred_node_"):
            element = "Node"
        elif identifier.startswith("qgisred_link_"):
            element = "Link"
        else:
            return None
        return resultStyleName(element, self.getResultStyleVariable(element)) or None

    def getResultStyleVariable(self, element):
        """Result variable the layer displays, in English, or None.

        The column the renderer classifies is read straight from the layer being edited,
        so it cannot go stale. Status is the exception: it classifies through rule filters
        and exposes no class attribute, and there the project entry answers — the dock
        rewrites it on every restyle, and so does the metadata reader when reopening.
        """
        field = (self.currentFieldName or "").strip()
        # Flow is classified through abs("Flow"); every other variable is a bare column.
        match = re.fullmatch(r'abs\(\s*"?(\w+)"?\s*\)', field)
        if match:
            field = match.group(1)
        if re.fullmatch(r'\w+', field):
            return field

        # The dock only ever works on the Base scenario (see its Scenario assignments).
        return QgsProject.instance().readEntry("QGISRed", "results_Base_" + element)[0] or None

    def getStyleNameForIdentifier(self, identifier):
        """Style name the plugin loads for this layer, or None when it has no file style.

        setStyle() is called with the identifier minus its "qgisred_" prefix for input
        layers, and with names that reduce to the same thing for sectors, trees and
        isolated segments ("HydraulicSectors_Links" → HydraulicSectorsLinks.qml). Deriving
        it the same way here is what makes a style saved from this dialog findable later.
        Underscores have to go, because setStyle strips them before looking the file up;
        case does not matter, findStyleFile compares in lowercase.

        Thematic maps are left out on purpose: their styles follow a different scheme
        (pipe_roughness.qml) resolved by the thematic maps dialog, not by setStyle.
        """
        thematicName = self.getThematicQueryStyleName(identifier)
        if thematicName:
            return thematicName
        prefix = "qgisred_"
        if not identifier.startswith(prefix) or identifier.startswith(prefix + "query_"):
            return None
        return identifier[len(prefix):].replace("_", "") or None

    def getThematicQueryStyleName(self, identifier):
        """Basename of the qml the thematic maps dialog resolves for this theme, or None."""
        if identifier == "qgisred_query_pipes_installdate":
            return "PipeInstallationYears"
        if identifier == "qgisred_query_pipes_age":
            return "PipeAges"
        if identifier == "qgisred_query_pipes_roughness":
            formula = QGISRedProjectUtils.getHeadlossFormula()
            if formula == "H-W":
                return "PipeRoughnessesHW"
            if formula == "C-M":
                return "PipeRoughnessesCM"
            return "PipeRoughnessesDW" + QGISRedProjectUtils.getUnits()
        return None

    def getElementNameForIdentifier(self, identifier):
        resultName = self.getResultStyleName(identifier or "")
        if resultName:
            return resultName
        styleName = self.getStyleNameForIdentifier(identifier or "")
        if styleName:
            return styleName
        if self.currentLayer:
            return self.currentLayer.name()
        return None

    def getProjectStyleFilename(self, name):
        base = self.getStyleBasename(name)
        if self.networkName:
            return f"{self.networkName}_{base}.qml"
        return base + ".qml"

    def getStyleFolder(self, globalStyle):
        if globalStyle:
            return os.path.join(self.getQGISRedDirectoryFromUtils(), "layerStyles")

        projectDir = self.getProjectDirectoryFromUtils()
        if not projectDir:
            QMessageBox.warning(self, self.tr("No Project"), self.tr("Project directory not set."))
            return None

        return os.path.join(projectDir, "layerStyles")

    def getProjectDirectoryFromUtils(self):
        return self.projectDirectory

    def getQGISRedDirectoryFromUtils(self):
        return self.fsUtils.getQGISRedFolder()

    # ============================================================
    # UI STATE MANAGEMENT
    # ============================================================

    def resetAllModesToManual(self):
        self.cbMode.blockSignals(True)
        self.cbMode.setCurrentIndex(0)
        self.cbMode.blockSignals(False)

        self.cbSizes.blockSignals(True)
        self.cbSizes.setCurrentIndex(0)
        self.cbSizes.blockSignals(False)

        self.cbColors.blockSignals(True)
        self.cbColors.setCurrentIndex(0)
        self.cbColors.blockSignals(False)

        self.onSizeModeChanged()
        self.onColorModeChanged()

    def updateUiBasedOnFieldType(self):
        isNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC
        isCategorical = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
        isSingle = self.currentFieldType == self.FIELD_TYPE_SINGLE
        isFixedInterval = isNumeric and self.cbMode.currentData() == "FixedInterval"
        isManualNumeric = isNumeric and (
            self.cbMode.currentData() is None
            or self.cbMode.currentData() == "Manual"
        )

        self.updateModeVisibility(isNumeric, isFixedInterval)
        self.updateClassButtonsVisibility(isCategorical, isNumeric, isFixedInterval)
        self.updateNavigationButtonsVisibility(isCategorical)
        self.updateClassCountEditability(isCategorical, isNumeric, isManualNumeric)
        self.updateAddClassTooltip(isCategorical, isNumeric)

        if isCategorical:
            self.updateAddClassButtonState()

        if isSingle:
            self.labelFrameLegends.setVisible(True)

        if self.currentFieldType not in (self.FIELD_TYPE_UNKNOWN, self.FIELD_TYPE_SINGLE):
            self.applySizeLogic()
            self.applyColorLogic()

    def getBuildableStrategyParts(self):
        if not self.currentFieldName:
            return []
        parts = []
        if (
            self.currentFieldType == self.FIELD_TYPE_CATEGORICAL
            and self.tableView.rowCount() > 0
            and self._sourceRuleRenderer is None  # rule-based classes cannot be snapshotted
        ):
            parts.append("allClasses")
        if self.canBuildIntervalsPart():
            parts.append("intervals")
        if self.canBuildSizesPart():
            parts.append("sizes")
        if self.canBuildColorsPart():
            parts.append("colors")
        return parts

    def canBuildIntervalsPart(self):
        if self.currentFieldType != self.FIELD_TYPE_NUMERIC:
            return False
        return self.cbMode.currentData() in ("EqualInterval", "Quantile", "Jenks", "StdDev", "Pretty")

    def canBuildSizesPart(self):
        if self.currentFieldType not in (self.FIELD_TYPE_NUMERIC, self.FIELD_TYPE_CATEGORICAL):
            return False
        return self.cbSizes.currentText() in ("Equal", "Linear", "Quadratic", "Exponential", "Proportional to Value")

    def canBuildColorsPart(self):
        if self.currentFieldType not in (self.FIELD_TYPE_NUMERIC, self.FIELD_TYPE_CATEGORICAL):
            return False
        return self.cbColors.currentText() in ("Random", "Ramp", "Palette")

    def buildStrategyFromCurrentUi(self, parts, renderer=None):
        if not parts or not self.currentFieldName:
            return None
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return self.buildCategoricalStrategy(parts, renderer)
        if self.currentFieldType == self.FIELD_TYPE_NUMERIC:
            return self.buildGraduatedStrategy(parts)
        return None

    def buildCategoricalStrategy(self, parts, renderer=None):
        # Categorical layers never persist intervals. The parts are independent:
        # allClasses pins the classes, colors/sizes regenerate on top of them.
        retainedParts = [part for part in parts if part != "intervals"]
        if not retainedParts:
            return None
        strategy = {
            "schema": "qgisred.legendStrategy.v2",
            "mode": "categorized",
            "field": self.currentFieldName,
            "parts": retainedParts,
        }
        if "allClasses" in retainedParts:
            allClassesPart = self.buildAllClassesPart(renderer)
            if allClassesPart is None:
                return None
            strategy["allClasses"] = allClassesPart
        if "sizes" in retainedParts:
            strategy["sizes"] = self.buildSizesPart()
        if "colors" in retainedParts:
            colorsPart = self.buildColorsPart()
            if colorsPart is None:
                return None
            strategy["colors"] = colorsPart
        return strategy

    def buildGraduatedStrategy(self, parts):
        strategy = {
            "schema": "qgisred.legendStrategy.v2",
            "mode": "graduated",
            "field": self.currentFieldName,
            "parts": list(parts),
        }
        if "intervals" in parts:
            intervalsPart = self.buildIntervalsPart()
            if intervalsPart is None:
                return None
            strategy["intervals"] = intervalsPart
        if "sizes" in parts:
            strategy["sizes"] = self.buildSizesPart()
        if "colors" in parts:
            colorsPart = self.buildColorsPart()
            if colorsPart is None:
                return None
            strategy["colors"] = colorsPart
        return strategy

    def buildIntervalsPart(self):
        classificationMode = self.cbMode.currentData()
        if classificationMode not in ("EqualInterval", "Quantile", "Jenks", "StdDev", "Pretty"):
            return None
        return {
            "classificationMode": classificationMode,
            "classes": int(self.leClassCount.value()),
        }

    def buildSizesPart(self):
        return {
            "mode": self.cbSizes.currentText(),
            "value": float(self.spinSizeEqual.value()),
            "min": float(self.spinSizeMin.value()),
            "max": float(self.spinSizeMax.value()),
            "invert": bool(self.ckSizeInvert.isChecked()),
        }

    def buildColorsPart(self):
        mode = self.cbColors.currentText()
        if mode == "Random":
            return {
                "source": "random",
                "rampName": None,
                "invertRamp": False,
                "deterministic": True,
            }
        if mode in ("Ramp", "Palette"):
            return {
                "source": "ramp",
                "rampName": self.btnColorRamp.activeRampName,
                "invertRamp": bool(self.ckColorInvert.isChecked()),
            }
        return None

    def buildAllClassesPart(self, renderer=None):
        # Snapshot the renderer built from the dialog, so the strategy matches
        # the QML saved next to it even when the user did not press Apply.
        if renderer is None:
            renderer = self.currentLayer.renderer()
        if not isinstance(renderer, QgsCategorizedSymbolRenderer):
            return None
        geometryType = self.currentLayer.geometryType()
        classes = []
        for category in renderer.categories():
            symbol = category.symbol()
            value = category.value()
            if geometryType == WKB_LINE_GEOMETRY:
                size = float(symbol.width())
            elif geometryType == WKB_POINT_GEOMETRY:
                size = float(symbol.size())
            else:
                size = None
            isNull = value is None or value == NULL or str(value) == "NULL"
            classes.append({
                "value": None if isNull else str(value),
                "label": category.label(),
                "color": symbol.color().name(),
                "size": size,
                "render": bool(category.renderState()),
            })
        if not classes:
            return None
        return {"classes": classes}

    def updateModeVisibility(self, isNumeric, isFixedInterval):
        self.cbMode.setVisible(isNumeric)
        self.labelMode.setVisible(isNumeric)
        self.labelIntervalRange.setVisible(isFixedInterval)
        self.spinIntervalRange.setVisible(isFixedInterval)

    def updateClassButtonsVisibility(self, isCategorical, isNumeric, isFixedInterval):
        self.btClassPlus.setVisible(isCategorical or isNumeric)
        self.btClassMinus.setVisible(isCategorical or isNumeric)
        self.btClassPlus.setEnabled(not isFixedInterval)
        self.btClassMinus.setEnabled(not isFixedInterval)
        self.labelClass.setVisible(isCategorical or isNumeric)
        self.leClassCount.setVisible(isCategorical or isNumeric)
        self.labelFrameLegends.setVisible(isNumeric or isCategorical)
        self.btClassifyAll.setVisible(isCategorical)

    def updateNavigationButtonsVisibility(self, isCategorical):
        self.btUp.setVisible(isCategorical)
        self.btDown.setVisible(isCategorical)

    def updateClassCountEditability(self, isCategorical, isNumeric, isManualNumeric):
        if isCategorical:
            self.setClassCountEditable(False)
            self.updateClassCountLimits()
        elif isNumeric:
            # Drop the tight limit a categorical layer may have left behind.
            self.leClassCount.blockSignals(True)
            self.leClassCount.setMaximum(self.MAX_CLASSES)
            self.leClassCount.blockSignals(False)
            self.setClassCountEditable(not isManualNumeric and self.modeHasVariableClassCount())
        else:
            self.setClassCountEditable(False)

    def updateAddClassTooltip(self, isCategorical, isNumeric):
        if isCategorical:
            self.btClassPlus.setToolTip(
                self.tr(
                    'Right-click: Add a new item above the current selection\n'
                    'Left-click: Add a new item below the current selection\n'
                    'Double-click: Add "Other values" option'
                )
            )
        elif isNumeric:
            self.btClassPlus.setToolTip(
                self.tr(
                    "Right-click: Add a new item above the current selection\n"
                    "Left-click: Add a new item below the current selection"
                )
            )

    def setClassCountEditable(self, editable):
        if editable:
            self.leClassCount.setReadOnly(False)
            self.leClassCount.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
            self.leClassCount.setStyleSheet(
                "QSpinBox { background-color: white; color: #2b2b2b; }"
            )
        else:
            self.leClassCount.setReadOnly(True)
            self.leClassCount.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            self.leClassCount.setStyleSheet(
                "QSpinBox { background-color: #F0F0F0; color: #808080; }"
            )

    def modeHasVariableClassCount(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            return True

        modeId = self.cbMode.currentData()
        fixedModes = ["FixedInterval", "StdDev"]
        return modeId not in fixedModes

    def updateClassCountLimits(self):
        if self.currentFieldType != self.FIELD_TYPE_CATEGORICAL:
            return

        currentCount = self.tableView.rowCount()
        maxPossible = currentCount + len(self.availableUniqueValues)

        if not self.hasOtherValuesCategory():
            maxPossible += 1

        self.leClassCount.blockSignals(True)
        self.leClassCount.setMinimum(0)
        self.leClassCount.setMaximum(maxPossible)
        self.leClassCount.blockSignals(False)

    def updateButtonStates(self):
        if not self.currentLayer:
            return

        selectedRows = self.getSelectedRows()
        selectionCount = len(selectedRows)
        isCategorical = self.currentFieldType == self.FIELD_TYPE_CATEGORICAL

        modeId = self.cbMode.currentData()
        isManualNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC and (
            modeId is None or modeId == "Manual"
        )
        isAutoNumeric = self.currentFieldType == self.FIELD_TYPE_NUMERIC and not isManualNumeric

        self.updateAddButtonState(isCategorical, isAutoNumeric, isManualNumeric, selectionCount, modeId)
        self.updateRemoveButtonState(modeId, selectionCount)
        self.updateMoveButtonsState(isCategorical, selectionCount, selectedRows)

    def updateAddButtonState(self, isCategorical, isAutoNumeric, isManualNumeric, selectionCount, modeId):
        if modeId == "FixedInterval":
            self.btClassPlus.setEnabled(False)
            return

        if isCategorical:
            if selectionCount > 1:
                self.btClassPlus.setEnabled(False)
            else:
                self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())
        elif isAutoNumeric:
            self.btClassPlus.setEnabled(True)
        else:
            self.btClassPlus.setEnabled(selectionCount <= 1)

    def updateRemoveButtonState(self, modeId, selectionCount):
        if modeId == "FixedInterval":
            self.btClassMinus.setEnabled(False)
        else:
            self.btClassMinus.setEnabled(selectionCount >= 1)

    def updateMoveButtonsState(self, isCategorical, selectionCount, selectedRows):
        if isCategorical:
            canMove = selectionCount == 1
            if canMove:
                rowIndex = selectedRows[0]
                self.btUp.setEnabled(rowIndex > 0)
                self.btDown.setEnabled(rowIndex < self.tableView.rowCount() - 1)
            else:
                self.btUp.setEnabled(False)
                self.btDown.setEnabled(False)
        else:
            self.btUp.setEnabled(False)
            self.btDown.setEnabled(False)

    def updateAddClassButtonState(self):
        if self.currentFieldType == self.FIELD_TYPE_CATEGORICAL:
            self.btClassPlus.setEnabled(len(self.availableUniqueValues) > 0 or not self.hasOtherValuesCategory())

    def updateClassCount(self):
        # The maximum may still belong to the previously selected layer; setValue
        # would clamp to it and the valueChanged handler would delete table rows.
        rowCount = self.tableView.rowCount()
        self.leClassCount.blockSignals(True)
        if self.leClassCount.maximum() < rowCount:
            self.leClassCount.setMaximum(rowCount)
        self.leClassCount.setValue(rowCount)
        self.leClassCount.blockSignals(False)

    # ============================================================
    # INPUT LAYER RESTRICTIONS
    # ============================================================

    def updateInputLayerRestrictions(self):
        """Disable right-panel batch controls for input layers; apply per-element column rules."""
        isInput = self.isInputLayer() or self.isSizeOnlyQueryLayer() or (
            self.isSingleEditableQueryLayer() and self.currentFieldType == self.FIELD_TYPE_SINGLE
        )

        # Classification panel
        self.cbMode.setEnabled(not isInput)
        self.spinIntervalRange.setEnabled(not isInput)
        self.leClassCount.setReadOnly(isInput)
        if isInput:
            self.leClassCount.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        else:
            self.leClassCount.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)

        # Class action buttons
        self.btClassPlus.setEnabled(not isInput)
        self.btClassMinus.setEnabled(not isInput)
        self.btUp.setEnabled(not isInput)
        self.btDown.setEnabled(not isInput)
        self.btClassifyAll.setEnabled(not isInput)

        # Color panel
        self.cbColors.setEnabled(not isInput)
        self.btColorEqual.setEnabled(not isInput)
        self.btnColorRamp.setEnabled(not isInput)
        self.btRefreshColors.setEnabled(not isInput)
        self.ckColorInvert.setEnabled(not isInput)

        # Size panel
        self.cbSizes.setEnabled(not isInput)
        self.spinSizeEqual.setEnabled(not isInput)
        self.spinSizeMin.setEnabled(not isInput)
        self.spinSizeMax.setEnabled(not isInput)
        self.ckSizeInvert.setEnabled(not isInput)

        # Per-element column restrictions (applied on top, after table is populated)
        if isInput:
            self.updateInputElementColumnRestrictions()

    def updateInputElementColumnRestrictions(self):
        """Apply per-element-type color/size column restrictions for input layers."""
        identifier = self.currentLayer.customProperty("qgisred_identifier") if self.currentLayer else ""

        COLOR_LOCKED = {"qgisred_reservoirs", "qgisred_tanks", "qgisred_sources"} | (
            self.SIZE_ONLY_QUERY_IDENTIFIERS - {self.TREE_NODES_IDENTIFIER}
        )

        if identifier in COLOR_LOCKED:
            self._disableColorColumnInTable()

    def _disableColorColumnInTable(self):
        """Disable color button (col 1) for every row in the table."""
        for row in range(self.tableView.rowCount()):
            container = self.tableView.cellWidget(row, 1)
            if container:
                colorWidget = container.findChild(QGISRedSymbolColorSelector)
                if colorWidget:
                    colorWidget.setEnabled(False)

    # ============================================================
    # UTILITY METHODS
    # ============================================================

    def getLayerUnits(self):
        if not self.utils:
            return ""

        try:
            return QGISRedProjectUtils.getUnits()
        except Exception:
            return ""

    def getGeometryHint(self):
        if not self.currentLayer:
            return "fill"

        geometryType = self.currentLayer.geometryType()
        if geometryType == WKB_POINT_GEOMETRY:
            return "marker"
        if geometryType == WKB_LINE_GEOMETRY:
            return "line"
        return "fill"

    def generateRandomColor(self):
        color = QColor()
        color.setHsl(random.randint(0, 359), random.randint(178, 255), random.randint(102, 178))  # nosec B311 — cosmetic legend color, not security-sensitive
        return color

    def getRowColor(self, row):
        if row < 0 or row >= self.tableView.rowCount():
            return None

        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector)
            if colorWidget:
                return colorWidget.activeColor
        return None

    def setRowColor(self, row, color):
        if row < 0 or row >= self.tableView.rowCount():
            return

        colorContainer = self.tableView.cellWidget(row, 1)
        if colorContainer:
            colorWidget = colorContainer.findChild(QGISRedSymbolColorSelector)
            if colorWidget:
                colorWidget.setSelectorColor(color)

    def getRowSize(self, row):
        """Gets the size value from a table row."""
        if row < 0 or row >= self.tableView.rowCount():
            return None

        sizeWidget = self.tableView.cellWidget(row, 2)
        if sizeWidget and isinstance(sizeWidget, QLineEdit):
            try:
                return float(sizeWidget.text())
            except (ValueError, TypeError):
                return None
        return None

    def setRowSize(self, row, size):
        """Sets the size value for a table row."""
        if row < 0 or row >= self.tableView.rowCount():
            return

        sizeWidget = self.tableView.cellWidget(row, 2)
        if sizeWidget and isinstance(sizeWidget, QLineEdit):
            sizeWidget.blockSignals(True)
            sizeWidget.setText(f"{size:.2f}")
            sizeWidget.blockSignals(False)

    def getDefaultSize(self):
        """Returns the default size based on geometry type."""
        if not self.currentLayer:
            return 0.4

        geometryType = self.currentLayer.geometryType()
        if geometryType == WKB_POINT_GEOMETRY:
            return 3.0
        elif geometryType == WKB_LINE_GEOMETRY:
            return 0.4
        else:
            return 1.5

    def calculateIntermediateColor(self, color1, color2):
        return QColor(
            (color1.red() + color2.red()) // 2,
            (color1.green() + color2.green()) // 2,
            (color1.blue() + color2.blue()) // 2,
        )

    def calculateComplementaryColor(self, color):
        h, s, l, a = color.getHsl()
        complementaryHue = (h + 180) % 360
        complementaryColor = QColor()
        complementaryColor.setHsl(complementaryHue, s, l, a)
        return complementaryColor

    def getSmartColorForNewRow(self, insertionRow):
        """Determines intelligent color for new row based on position and existing colors."""
        rowCount = self.tableView.rowCount()

        if rowCount == 0:
            return self.generateRandomColor()

        if rowCount == 1:
            firstColor = self.getRowColor(0)
            if firstColor:
                return self.calculateComplementaryColor(firstColor)
            return self.generateRandomColor()

        if insertionRow == 0:
            firstColor = self.getRowColor(0)
            return firstColor if firstColor else self.generateRandomColor()

        if insertionRow >= rowCount:
            lastColor = self.getRowColor(rowCount - 1)
            return lastColor if lastColor else self.generateRandomColor()

        prevColor = self.getRowColor(insertionRow - 1)
        nextColor = self.getRowColor(insertionRow)

        if prevColor and nextColor:
            return self.calculateIntermediateColor(prevColor, nextColor)
        if prevColor:
            return prevColor
        if nextColor:
            return nextColor

        return self.generateRandomColor()

    def getSmartSizeForNewRow(self, insertionRow):
        """Determines intelligent size for new row based on position and existing sizes."""
        rowCount = self.tableView.rowCount()

        if rowCount == 0:
            return self.getDefaultSize()

        if rowCount == 1:
            existingSize = self.getRowSize(0)
            return existingSize if existingSize is not None else self.getDefaultSize()

        if insertionRow == 0:
            firstSize = self.getRowSize(0)
            return firstSize if firstSize is not None else self.getDefaultSize()

        if insertionRow >= rowCount:
            lastSize = self.getRowSize(rowCount - 1)
            return lastSize if lastSize is not None else self.getDefaultSize()

        prevSize = self.getRowSize(insertionRow - 1)
        nextSize = self.getRowSize(insertionRow)

        if prevSize is not None and nextSize is not None:
            return (prevSize + nextSize) / 2.0
        if prevSize is not None:
            return prevSize
        if nextSize is not None:
            return nextSize

        return self.getDefaultSize()

    def smoothEdgeColorAfterInsertion(self, insertedRow):
        """Applies edge color smoothing after insertion when there are 3+ classes."""
        rowCount = self.tableView.rowCount()

        if rowCount < 3:
            return

        if insertedRow == 0:
            self.smoothFirstRowInsertion(rowCount)
        elif insertedRow == rowCount - 1:
            self.smoothLastRowInsertion(rowCount)

    def smoothFirstRowInsertion(self, rowCount):
        newFirstColor = self.getRowColor(0)
        lastColor = self.getRowColor(rowCount - 1)

        if newFirstColor and lastColor:
            interpolatedColor = self.calculateIntermediateColor(newFirstColor, lastColor)
            self.setRowColor(1, interpolatedColor)

    def smoothLastRowInsertion(self, rowCount):
        newLastColor = self.getRowColor(rowCount - 1)

        antepenultimateColor = None
        if rowCount >= 3:
            antepenultimateColor = self.getRowColor(rowCount - 3)

        if newLastColor and antepenultimateColor:
            interpolatedColor = self.calculateIntermediateColor(newLastColor, antepenultimateColor)
            self.setRowColor(rowCount - 2, interpolatedColor)

    def smoothEdgeSizeAfterInsertion(self, insertedRow):
        """Applies edge size smoothing after insertion when there are 3+ classes."""
        rowCount = self.tableView.rowCount()

        if rowCount < 3:
            return

        if insertedRow == 0:
            self.smoothFirstRowSizeInsertion(rowCount)
        elif insertedRow == rowCount - 1:
            self.smoothLastRowSizeInsertion(rowCount)

    def smoothFirstRowSizeInsertion(self, rowCount):
        """Interpolate old first (now second) between new first and last."""
        newFirstSize = self.getRowSize(0)
        lastSize = self.getRowSize(rowCount - 1)

        if newFirstSize is not None and lastSize is not None:
            interpolatedSize = (newFirstSize + lastSize) / 2.0
            self.setRowSize(1, interpolatedSize)

    def smoothLastRowSizeInsertion(self, rowCount):
        """Interpolate old last (now second-to-last) between first and new last."""
        firstSize = self.getRowSize(0)
        newLastSize = self.getRowSize(rowCount - 1)

        if firstSize is not None and newLastSize is not None:
            interpolatedSize = (firstSize + newLastSize) / 2.0
            self.setRowSize(rowCount - 2, interpolatedSize)

    def getSelectedRows(self):
        return [idx.row() for idx in self.tableView.selectionModel().selectedRows()]

    def hasOtherValuesCategory(self):
        for row in range(self.tableView.rowCount()):
            widget = self.tableView.cellWidget(row, 4)
            if isinstance(widget, QLineEdit) and widget.text() in [
                self.tr("Other Values"),
                "Other Values",
            ]:
                return True
        return False

    def ensureOtherValuesCategory(self):
        if self.hasOtherValuesCategory():
            return

        row = self.tableView.rowCount()
        self.tableView.insertRow(row)

        symbol = QgsSymbol.defaultSymbol(self.currentLayer.geometryType())
        symbol.setColor(self.generateRandomColor())

        self.setRowWidgets(
            row,
            symbol,
            True,
            self.tr("Other Values"),
            self.tr("Other Values"),
            self.getGeometryHint(),
            isReadOnlyValue=True,
        )

        self.updateClassCount()

    def getCurrentLayerUnitAbbr(self):
        if not self.currentLayer or not self.utils:
            return ""

        layerIdent = self.currentLayer.customProperty("qgisred_identifier")
        field = resolve_layer_id(layerIdent) if layerIdent else None
        if field:
            return self.fieldUtils.getUnitAbbreviation(*field)
        return ""

    # ============================================================
    # DIALOG LIFECYCLE
    # ============================================================

    def acceptAndClose(self):
        if self.isClosing:
            return
        self.applyLegend()
        self.isClosing = True
        self.close()

    def cancelAndClose(self):
        if self.isClosing:
            return
        if self.hasAppliedChanges:
            reply = QMessageBox.question(
                self,
                self.tr("Discard Applied Changes"),
                self.tr("The changes already applied to the layer will be lost.\nDo you want to proceed?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        self.isClosing = True
        # Cancel behaves like "Revert to Original Legend": restore the pristine
        # snapshot taken when the layer was first selected, even after Apply.
        if self.currentLayer:
            snapshot = self.initialRenderers.get(self.currentLayer.id())
            if snapshot is not None:
                self.currentLayer.setRenderer(snapshot.clone())
                self.currentLayer.triggerRepaint()
        # Sibling layers recolored by the Hydraulic Sectors sync revert as well.
        for siblingId in self._syncedSiblingIds:
            snapshot = self.initialRenderers.get(siblingId)
            layer = QgsProject.instance().mapLayer(siblingId)
            if snapshot is not None and layer is not None:
                layer.setRenderer(snapshot.clone())
                layer.triggerRepaint()
        self.close()

    def reject(self):
        # Esc and the window close button just close the dialog: the layer keeps
        # whatever was applied. Only the Cancel button reverts to the snapshot.
        # close() (guarded by isClosing) makes sure closeEvent cleanup runs
        # instead of just hiding the dialog.
        if not self.isClosing:
            self.isClosing = True
            self.close()
        super().reject()

    def revertToOriginalStyle(self):
        if not self.currentLayer:
            return
        snapshot = self.initialRenderers.get(self.currentLayer.id())
        if snapshot is None:
            return
        # Preview only: the layer itself changes when Apply is pressed.
        self.populateDialogFromRenderer(snapshot.clone())

    def eventFilter(self, obj, event):
        if obj == self.btClassPlus and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.RightButton and self.btClassPlus.isEnabled():
                self.addClassBeforeSelection = True
                self.executeAddClass()
                self.addClassBeforeSelection = False
                return True

        if obj == self and event.type() == QEvent.Type.MouseButtonPress:
            clickPos = event.pos()
            tableGeometry = self.tableView.geometry()
            if not tableGeometry.contains(clickPos):
                self.tableView.clearSelection()

        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        self.disconnectLayerTreeSignal()
        self.cleanupParentReference()
        super().closeEvent(event)

    def disconnectLayerTreeSignal(self):
        if self.layerTreeViewConnection and iface and iface.layerTreeView():
            with suppress(Exception):
                iface.layerTreeView().currentLayerChanged.disconnect(self.onQgisLayerSelectionChanged)

    def cleanupParentReference(self):
        if self.parentPlugin and hasattr(self.parentPlugin, "legendsDialog"):
            self.parentPlugin.legendsDialog = None
