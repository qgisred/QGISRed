# -*- coding: utf-8 -*-
"""Builds the thematic map layers: derives a layer from an input shapefile, dresses it in
the right style for the project's units and headloss formula, and puts it in the tree.

This is the whole of what the Thematic Maps dialog used to do behind its Accept button. It
lives apart from that dialog because the legend's outdated-layer warning rebuilds a single
map with no dialog in sight, and reaching this code through a widget would mean building a
window nobody ever sees.
"""

# Standard library imports
from contextlib import suppress
import os

# Third-party imports
from qgis.PyQt.QtCore import QCoreApplication

# QGIS imports
from qgis.core import QgsLayerTreeGroup, QgsLayerTreeLayer, QgsProject
from qgis.core import QgsField, QgsVectorFileWriter, QgsVectorLayer
from qgis.core import QgsPalLayerSettings, QgsVectorLayerSimpleLabeling
from qgis.core import QgsDataDefinedSizeLegend, QgsMapLayerLegendUtils
from qgis.core import QgsClassificationPrettyBreaks, QgsGraduatedSymbolRenderer, QgsRendererRange
from qgis.core import QgsGradientColorRamp, QgsGradientStop

# Local imports
from ...compat import sip, NODE_TYPE_LAYER, NODE_TYPE_GROUP, PAL_PLACEMENT_OVER_POINT, FIELD_TYPE_INT
from .qgisred_field_utils import QGISRedFieldUtils
from .qgisred_filesystem_utils import QGISRedFileSystemUtils
from .qgisred_layer_utils import QGISRedLayerUtils
from .qgisred_styling_utils import QGISRedStylingUtils
from .qgisred_project_utils import QGISRedProjectUtils
from .qgisred_thematicmaps_queries import buildQueryCatalogue, queryIdentifier


class QGISRedThematicMapsBuilder:
    """Creates and recreates thematic map layers for one project."""

    def __init__(self, iface, projectDirectory, networkName):
        self.iface = iface
        self.ProjectDirectory = projectDirectory
        self.NetworkName = networkName

    @staticmethod
    def tr(message):
        return QCoreApplication.translate("QGISRedThematicMapsBuilder", message)

    def rebuildThematicMaps(self, identifiers):
        """Rebuild the named thematic maps from the project's current settings."""
        return self.applyQueries(buildQueryCatalogue(), set(identifiers))

    def applyQueries(self, queries, identifiers):
        """Build (or rebuild) exactly the queries whose identifier is in `identifiers`."""
        queries = [query for query in queries if queryIdentifier(query) in identifiers]
        if not queries:
            return False

        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        inputsGroup = utils.getOrCreateGroup("Inputs")
        if inputsGroup is None:
            return False

        thematicGroup = self.getOrCreateQueriesGroup(self.getRootGroup(), inputsGroup)
        # Creating the Queries hierarchy re-parents and hides sibling groups, so the
        # Inputs node captured above may already be dead by the time it is read.
        inputsGroup = utils.getOrCreateGroup("Inputs")
        if inputsGroup is None:
            return False

        pipesLayer = self.findLayerInGroup(inputsGroup, 'Pipes', 'qgisred_pipes')
        if pipesLayer is None:
            return False
        junctionsLayer = self.findLayerInGroup(inputsGroup, 'Junctions', 'qgisred_junctions')

        for query in reversed(queries):
            if query['layer_type'] == 'Junctions':
                if junctionsLayer is not None:
                    self.processQuery(query, junctionsLayer, thematicGroup)
            else:
                self.processQuery(query, pipesLayer, thematicGroup)
        return True

    def cleanupEmptyQueryGroups(self):
        queriesGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_queries")
        if queriesGroup is not None:
            thematicGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_thematicmaps")
            if thematicGroup is not None and not thematicGroup.children():
                thematicParent = thematicGroup.parent()
                if thematicParent is not None:
                    thematicParent.removeChildNode(thematicGroup)
            if not queriesGroup.children():
                parent = queriesGroup.parent()
                if parent is not None:
                    parent.removeChildNode(queriesGroup)

    def removeQueryLayersByIdentifiers(self, identifiersToRemove):
        if not identifiersToRemove:
            return

        # Prefer Queries → Thematic Maps, but fall back to Queries (for legacy layers)
        queriesGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_queries")
        thematicGroup = QGISRedLayerUtils.findGroupByIdentifier("qgisred_thematicmaps")
        targetGroup = thematicGroup or queriesGroup

        if targetGroup:
            self.recursiveRemoveByIdentifiers(targetGroup, identifiersToRemove)

            # tidy up if groups become empty
            if thematicGroup is not None and not thematicGroup.children():
                thematicParent = thematicGroup.parent()
                if thematicParent is not None:
                    thematicParent.removeChildNode(thematicGroup)
            if queriesGroup is not None and not queriesGroup.children():
                parent = queriesGroup.parent()
                if parent is not None:
                    parent.removeChildNode(queriesGroup)

    def recursiveRemoveByIdentifiers(self, group, identifiers):
        QGISRedLayerUtils.stopRenderingForRemoval(self.iface)
        for child in list(group.children()):
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer:
                    layerId = layer.customProperty("qgisred_identifier")
                    if layerId in identifiers:
                        QgsProject.instance().removeMapLayer(layer.id())
            elif isinstance(child, QgsLayerTreeGroup):
                self.recursiveRemoveByIdentifiers(child, identifiers)

    def getRootGroup(self):
        project = QgsProject.instance()
        root = project.layerTreeRoot()
        if isinstance(root, QgsLayerTreeGroup):
            return root
        else:
            return root.rootGroup()

    def getOrCreateQueriesGroup(self, rootGroup, inputsGroup):
        inputsParent = inputsGroup.parent()
        if inputsParent is None:
            inputsParent = rootGroup
        networkName = inputsParent.name() if inputsParent != rootGroup else ""
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        if networkName:
            return utils.getOrCreateNestedGroup([networkName, "Queries", "Thematic Maps"])
        else:
            return utils.getOrCreateNestedGroup(["Queries", "Thematic Maps"])

    def findLayerInGroup(self, group, layerName=None, custom_property=None):
        for child in group.children():
            if custom_property:
                # Search by custom property
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer and layer.customProperty('qgisred_identifier') == custom_property:
                        return layer
            else:
                # Search by layer name (original behavior)
                if child.nodeType() == NODE_TYPE_LAYER and child.name() == layerName and child.checkedLayers():
                    return child.checkedLayers()[0]
                elif isinstance(child, QgsLayerTreeLayer) and child.name() == layerName:
                    return child.layer()

            # Recursively search in subgroups
            if child.nodeType() == NODE_TYPE_GROUP:
                layer = self.findLayerInGroup(child, layerName, custom_property)
                if layer is not None:
                    return layer
        return None

    def processQuery(self, query, mainLayer, queriesGroup):
        layerName = QCoreApplication.translate('InputLayerNames', query['layer_name']) + query.get('name_suffix', '')
        field = query['field']
        qmlFile = query['qml_file']

        layerType = query.get('layer_type', 'unknown').lower()
        layerIdentifier = queryIdentifier(query)

        # Find existing layer by identifier instead of name
        existingLayer, layerPosition = self.findLayerByIdentifier(queriesGroup, layerIdentifier)
        parentGroup = queriesGroup
        # A map being rebuilt goes back where it was; a brand new one goes on top.
        if existingLayer is None:
            layerPosition = 0

        if existingLayer is not None:
            with suppress(Exception):
                parentGroup = existingLayer.parent()

                layerId = None
                if isinstance(existingLayer, QgsLayerTreeLayer) and existingLayer.layer():
                    layerId = existingLayer.layer().id()
                elif existingLayer.nodeType() == NODE_TYPE_LAYER and existingLayer.checkedLayers():
                    layerId = existingLayer.checkedLayers()[0].id()

                if layerId and QgsProject.instance().mapLayer(layerId):
                    QGISRedLayerUtils.stopRenderingForRemoval(self.iface)
                    QgsProject.instance().removeMapLayer(layerId)

                if parentGroup and not sip.isdeleted(parentGroup):
                    parentGroup.removeChildNode(existingLayer)

        derivedLayer = self.createDerivedLayer(mainLayer, layerName, field)

        derivedLayer.setCustomProperty("query_field", field)

        qmlPath = self.loadQmlStyle(derivedLayer, qmlFile)
        derivedLayer.setLabelsEnabled(False)

        if field == 'Material':
            # Material colors are resolved per data value inside applyCategorizedRenderer,
            # which reads them from the QGISRed style database.
            QGISRedStylingUtils().applyCategorizedRenderer(derivedLayer, field, qmlPath)

        derivedLayer.setCustomProperty("qgisred_identifier", layerIdentifier)
        self.markThemeDependencies(derivedLayer, query)

        QgsProject.instance().addMapLayer(derivedLayer, False)
        # 'field' here is the query's stable identifier value ('Type'), used above to build
        # layerIdentifier -- it must stay 'Type' regardless of schema. The real column on a
        # project exported by the current DLL is 'ValveType'; resolve it only for the actual
        # attribute-table lookup, which needs the name that is really on the layer.
        hideField = field
        if layerType == 'valves' and field == 'Type' and derivedLayer.fields().indexFromName('ValveType') >= 0:
            hideField = 'ValveType'
        # Same split for the installation-year map: 'InstallYear' is only the query's
        # identifier value, while the classified column is the virtual InstYear field
        # the style file adds on top of the raw InstalDate column.
        if layerType == 'pipes' and field == 'InstallYear' and derivedLayer.fields().indexFromName('InstYear') >= 0:
            hideField = 'InstYear'
        # Same split for roughness: 'Roughness' is the query's identifier value,
        # while the classified column on the layer is 'RoughCoeff'.
        if layerType == 'pipes' and field == 'Roughness' and derivedLayer.fields().indexFromName('RoughCoeff') >= 0:
            hideField = 'RoughCoeff'
        # The two date-based maps should expose the raw InstalDate column followed by
        # both virtual fields (InstYear and Age). A style copied to the project or
        # global folder may predate one of them, so add whichever is missing before
        # deciding which columns stay visible.
        if layerType == 'pipes' and field in ('InstallYear', 'Age'):
            if derivedLayer.fields().indexFromName('InstalDate') >= 0:
                expressions = {
                    'InstYear': 'to_int( left( "InstalDate" ,4))',
                    'Age': "round(year(age(now(),to_datetime(\"InstalDate\",'yyyyMMdd'))),0)",
                }
                for name, expression in expressions.items():
                    if derivedLayer.fields().indexFromName(name) < 0:
                        derivedLayer.addExpressionField(expression, QgsField(name, FIELD_TYPE_INT))
            hideField = [name for name in ('InstalDate', 'InstYear', 'Age')
                         if derivedLayer.fields().indexFromName(name) >= 0] or hideField
        # Same split for the base demand map: 'TotalBaseDemand' is the query's
        # identifier value, while the classified columns are the TotBaseDem/DemType
        # virtual fields the style file adds; the style also needs the demands layer
        # id and the project flow units, which only this code can know.
        if layerType == 'junctions' and field == 'TotalBaseDemand':
            self.adaptBaseDemandDerivedLayer(derivedLayer)
            hideField = [name for name in ('TotBaseDem', 'DemType')
                         if derivedLayer.fields().indexFromName(name) >= 0] or hideField
        # Elevations follow no standard ranges, so the style only ships the look of
        # the classes; their breaks and their units come from the data and the project.
        if layerType == 'junctions' and field == 'Elevation':
            self.adaptElevationDerivedLayer(derivedLayer)

        # hideFields() would otherwise resolve the identity column itself via
        # derivedLayer's own qgisred_identifier -- but that property is set above to this
        # query's own identifier (e.g. "qgisred_query_pipes_material"), not the element's
        # ("qgisred_pipes"), so its CSV-driven lookup can't match and falls back to the
        # legacy bare "Id". Resolve it from mainLayer, which still carries the element
        # identifier, so both old ("Id") and new ("PipeID") schemas work.
        idFieldName = QGISRedFieldUtils().getIdFieldName(mainLayer)
        if derivedLayer.fields().indexFromName(idFieldName) < 0:
            idFieldName = None
        QGISRedStylingUtils().hideFields(derivedLayer, hideField, idFieldName)

        if parentGroup is not None and not sip.isdeleted(parentGroup):
            # Use insertChildNode with a new QgsLayerTreeLayer instance for better QGIS 4 compatibility.
            # insertChildNode() returns None on QGIS 3, so keep our own reference to the node.
            layerTreeLayer = QgsLayerTreeLayer(derivedLayer)
            layerTreeLayer.setCustomProperty("showFeatureCount", True)
            isBaseDemandQuery = layerType == 'junctions' and field == 'TotalBaseDemand'
            if isBaseDemandQuery:
                self.hideProportionalLegendTitle(derivedLayer, layerTreeLayer)
            parentGroup.insertChildNode(layerPosition, layerTreeLayer)

        def syncDerivedLayer():
            if sip.isdeleted(derivedLayer):
                self.safeDisconnect(mainLayer.dataChanged, syncDerivedLayer)
                return
            self.syncLayers(mainLayer, derivedLayer)

        mainLayer.dataChanged.connect(syncDerivedLayer)

        def refreshAfterCommit():
            # Commits made through a QGIS edit session (attribute table, field
            # calculator) never pass through the plugin's reload pipeline, so the
            # central refresh must be driven from the layer's own commit signal.
            if sip.isdeleted(derivedLayer):
                self.safeDisconnect(mainLayer.afterCommitChanges, refreshAfterCommit)
                return
            utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            fs = QGISRedFileSystemUtils(self.ProjectDirectory, self.NetworkName, self.iface)
            utils.refreshThematicMapLayers(fs.getLayerPath(mainLayer))

        mainLayer.afterCommitChanges.connect(refreshAfterCommit)
        derivedLayer.dataChanged.connect(lambda: derivedLayer.triggerRepaint())
        derivedLayer.setReadOnly(True)

        return derivedLayer

    def markThemeDependencies(self, derivedLayer, query):
        # Stamp the units/formula the theme was built with so the stale layer
        # manager can flag it when either project setting changes afterwards.
        units = QGISRedProjectUtils.getUnits()
        if query['file_name'].endswith(f'_{units}'):
            derivedLayer.setCustomProperty("qgisred_theme_units", units)
        if query['field'] == 'Roughness':
            formula = QGISRedProjectUtils.getHeadlossFormula()
            derivedLayer.setCustomProperty("qgisred_theme_formula", formula)
            if formula not in ('H-W', 'C-M'):
                derivedLayer.setCustomProperty("qgisred_theme_units", units)
        if query['field'] == 'TotalBaseDemand':
            derivedLayer.setCustomProperty("qgisred_theme_flow_units", QGISRedProjectUtils.getFlowUnit())

    def findLayerByIdentifier(self, parentGroup, identifier):
        if not parentGroup:
            return None, None

        for i, child in enumerate(parentGroup.children()):
            if child.nodeType() == NODE_TYPE_LAYER:
                if self.nodeIdentifier(child) == identifier:
                    return child, i
            elif child.nodeType() == NODE_TYPE_GROUP:
                foundLayer, foundPosition = self.findLayerByIdentifier(child, identifier)
                if foundLayer is not None:
                    return foundLayer, foundPosition

        return None, None

    @staticmethod
    def nodeIdentifier(node):
        """The qgisred_identifier of the layer behind a tree node.

        It is stamped on the layer, never on the node — and a node keeps its own, separate
        custom property store, so asking the node answers None for every thematic map there
        is. That silence is what used to leave the old map in place beside its rebuild.
        """
        layer = None
        if isinstance(node, QgsLayerTreeLayer) and node.layer():
            layer = node.layer()
        elif node.nodeType() == NODE_TYPE_LAYER and node.checkedLayers():
            layer = node.checkedLayers()[0]
        return layer.customProperty("qgisred_identifier") if layer is not None else None

    def syncLayers(self, mainLayer, derivedLayer):
        # Only refresh the derived layer's data; its thematic symbology must survive
        # any change made to the input layer.
        derivedLayer.dataProvider().forceReload()
        derivedLayer.triggerRepaint()

    def safeDisconnect(self, signal, slot):
        with suppress(TypeError, RuntimeError):
            signal.disconnect(slot)

    def checkExistingLayer(self, queriesGroup, layerName, layerPath=None):
        existingLayer = None
        for child in queriesGroup.children():
            if isinstance(child, QgsLayerTreeLayer) and child.name() == layerName:
                existingLayer = child
                break

        if existingLayer is not None:
            if layerPath and os.path.exists(layerPath):
                QgsVectorFileWriter.deleteShapeFile(layerPath)

            QGISRedLayerUtils.stopRenderingForRemoval(self.iface)
            QgsProject.instance().removeMapLayer(existingLayer.id())
            return True

        return False

    def createDerivedLayer(self, sourceLayer, newLayerName, field):
        uri = sourceLayer.source()

        providerType = sourceLayer.providerType()

        derivedLayer = QgsVectorLayer(uri, newLayerName, providerType)

        if not derivedLayer.isValid():
            raise Exception(self.tr("Failed to create derived layer from %1").replace("%1", sourceLayer.name()))

        derivedLayer.setCrs(sourceLayer.crs())

        return derivedLayer

    def loadQmlStyle(self, layer, qmlFile):
        if qmlFile.endswith('.qml.bak'):
            qmlFile = qmlFile[:-4]

        styling = QGISRedStylingUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        qmlPath = styling.resolveStylePath(qmlFile)
        if os.path.exists(qmlPath):
            layer.loadNamedStyle(qmlPath)
            layer.setCustomProperty("styleURI", qmlPath)
            styling.applyStrategyFromLayer(layer)
            layer.triggerRepaint()
        return qmlPath

    def adaptBaseDemandDerivedLayer(self, layer):
        self.pointBaseDemandFieldsToDemandsLayer(layer)
        self.classifyBaseDemandBySize(layer)
        self.applyFlowUnitsToBaseDemandStyle(layer)

    def classifyBaseDemandBySize(self, layer):
        # Pretty Breaks depend on the data, so the classes shipped in the style
        # are placeholders rebuilt here; map circles keep their data-defined
        # size expression while each legend class gets the Flannery size of its
        # central value: r = rmin + k * (value - vmin)^0.5716.
        renderer = layer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return
        values = [feature['TotBaseDem'] for feature in layer.getFeatures()
                  if isinstance(feature['TotBaseDem'], (int, float))]
        if not values:
            return
        renderer.setClassificationMethod(QgsClassificationPrettyBreaks())
        renderer.updateClasses(layer, 5)
        minimumValue, maximumValue = min(values), max(values)
        minimumSize, maximumSize, exponent = 1.3, 5.0, 0.5716
        valueSpan = (maximumValue - minimumValue) ** exponent if maximumValue > minimumValue else 0
        sizeFactor = (maximumSize - minimumSize) / valueSpan if valueSpan else 0
        for index, classRange in enumerate(renderer.ranges()):
            centralValue = (classRange.lowerValue() + classRange.upperValue()) / 2
            valueOffset = max(centralValue - minimumValue, 0)
            symbol = classRange.symbol().clone()
            symbol.setSize(minimumSize + sizeFactor * (valueOffset ** exponent))
            renderer.updateRangeSymbol(index, symbol)
            renderer.updateRangeLabel(index, classRange.label() + ' ' + QGISRedProjectUtils.getFlowUnit().lower())

    def hideProportionalLegendTitle(self, layer, layerTreeLayer):
        # The proportional size legend always renders a title row, falling back
        # to the classified field name when the stored title is empty, so the
        # node is dropped from the legend order instead (what the Legend
        # properties tab does when an entry is removed).
        renderer = layer.renderer()
        sizeLegend = renderer.dataDefinedSizeLegend() if hasattr(renderer, 'dataDefinedSizeLegend') else None
        if sizeLegend is None:
            return
        classCount = len(sizeLegend.classes())
        QgsMapLayerLegendUtils.setLegendNodeOrder(layerTreeLayer, list(range(1, classCount + 1)))

    def pointBaseDemandFieldsToDemandsLayer(self, layer):
        # The style file references the multiple demands layer by its default
        # name; the real layer may be renamed or translated, so retarget the
        # virtual field expressions to its stable layer id.
        demandsLayer = self.findLayerInGroup(self.getRootGroup(), None, 'qgisred_demands')
        if demandsLayer is None:
            return
        for fieldName in ('TotBaseDem', 'DemType'):
            fieldIndex = layer.fields().indexFromName(fieldName)
            if fieldIndex < 0:
                continue
            expression = layer.expressionField(fieldIndex)
            if "'Demands'" in expression:
                layer.updateExpressionField(fieldIndex, expression.replace("'Demands'", "'%s'" % demandsLayer.id()))

    def applyFlowUnitsToBaseDemandStyle(self, layer):
        flowUnit = QGISRedProjectUtils.getFlowUnit().lower()
        layer.setMapTipTemplate(layer.mapTipTemplate().replace('LPS', flowUnit))

        labeling = layer.labeling()
        if labeling is not None:
            labelSettings = labeling.settings()
            labelSettings.fieldName = labelSettings.fieldName.replace('LPS', flowUnit)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))

        renderer = layer.renderer()
        sizeLegend = renderer.dataDefinedSizeLegend() if hasattr(renderer, 'dataDefinedSizeLegend') else None
        if sizeLegend is not None:
            updatedLegend = QgsDataDefinedSizeLegend(sizeLegend)
            updatedLegend.setClasses([
                QgsDataDefinedSizeLegend.SizeClass(sizeClass.size, sizeClass.label.replace('LPS', flowUnit))
                for sizeClass in sizeLegend.classes()
            ])
            renderer.setDataDefinedSizeLegend(updatedLegend)

    def adaptElevationDerivedLayer(self, layer):
        units = QGISRedFieldUtils().getUnitAbbreviation('Junctions', 'Elevation')
        self.classifyElevationByPrettyBreaks(layer, units)
        self.applyLengthUnitsToElevationStyle(layer, units)

    def classifyElevationByPrettyBreaks(self, layer, units):
        # Breaks come from the data (none at all when every junction shares one
        # elevation) and are shifted down so a value sitting on a break reads in
        # the upper class, as the labels say; the outer bounds cover later edits.
        # Each class takes the color of its position in the shipped legend.
        renderer = layer.renderer()
        if not isinstance(renderer, QgsGraduatedSymbolRenderer):
            return
        shippedRanges = renderer.ranges()
        if not shippedRanges:
            return
        colors = [classRange.symbol().color() for classRange in shippedRanges]
        stops = [QgsGradientStop(index / (len(colors) - 1), color)
                 for index, color in enumerate(colors[1:-1], 1)]
        renderer.setSourceSymbol(shippedRanges[0].symbol().clone())
        renderer.setSourceColorRamp(QgsGradientColorRamp(colors[0], colors[-1], False, stops))
        renderer.setClassificationMethod(QgsClassificationPrettyBreaks())
        renderer.updateClasses(layer, 5)
        classRanges = renderer.ranges()
        if not classRanges:
            elevation = layer.minimumValue(layer.fields().indexFromName('Elevation'))
            label = units
            if isinstance(elevation, (int, float)):
                label = '%s %s' % (self.formatBreakValue(elevation), units)
            renderer.addClass(QgsRendererRange(-100000, 100000, shippedRanges[0].symbol().clone(), label))
            return
        lastIndex = len(classRanges) - 1
        for index, classRange in enumerate(classRanges):
            renderer.updateRangeLowerValue(index, -100000 if index == 0 else classRange.lowerValue() - 0.001)
            renderer.updateRangeUpperValue(index, 100000 if index == lastIndex else classRange.upperValue() - 0.001)
            lowerText = self.formatBreakValue(classRange.lowerValue())
            upperText = self.formatBreakValue(classRange.upperValue())
            if index == 0:
                label = '< %s %s' % (upperText, units)
            elif index == lastIndex:
                label = '>= %s %s' % (lowerText, units)
            else:
                label = '%s < %s %s' % (lowerText, upperText, units)
            renderer.updateRangeLabel(index, label)

    def formatBreakValue(self, value):
        return ('%.3f' % value).rstrip('0').rstrip('.')

    def applyLengthUnitsToElevationStyle(self, layer, units):
        layer.setMapTipTemplate(layer.mapTipTemplate().replace('[units]', units))

        labeling = layer.labeling()
        if labeling is not None:
            labelSettings = labeling.settings()
            labelSettings.fieldName = labelSettings.fieldName.replace('[units]', units)
            layer.setLabeling(QgsVectorLayerSimpleLabeling(labelSettings))

    def assignLabels(self, layer, field, ):
        layer.setLabelsEnabled(True)
        labeling = layer.labeling()
        if labeling is not None:
            labelSettings = labeling.clone()
            labelSettings.fieldName = field
            layer.setLabeling(labelSettings)

    def setLabelsWithNullHandling(self, layer, fieldName, qmlFilePath):
        if not layer or not isinstance(layer, QgsVectorLayer):
            return

        # Create the label expression using coalesce to handle NULL values
        expression = f"""
                    CASE
                        WHEN "{fieldName}" IS NULL THEN '#NA'
                        ELSE "{fieldName}"
                    END
        """
        # Set up label settings
        labelSettings = QgsPalLayerSettings()
        labelSettings.fieldName = expression
        labelSettings.isExpression = True
        labelSettings.placement = PAL_PLACEMENT_OVER_POINT
        # Apply labeling to the layer
        labeling = QgsVectorLayerSimpleLabeling(labelSettings)
        layer.setLabeling(labeling)

        layer.triggerRepaint()

    @staticmethod
    def collectExistingIdentifiers(group):
        identifiers = set()

        def recursiveCollect(g):
            for child in g.children():
                if isinstance(child, QgsLayerTreeLayer):
                    layer = child.layer()
                    if layer:
                        identifier = layer.customProperty("qgisred_identifier")
                        if identifier and identifier.startswith("qgisred_query_"):
                            identifiers.add(identifier)
                elif isinstance(child, QgsLayerTreeGroup):
                    recursiveCollect(child)
        recursiveCollect(group)
        return identifiers
