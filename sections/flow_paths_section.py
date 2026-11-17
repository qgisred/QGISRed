# -*- coding: utf-8 -*-
import os
from contextlib import suppress

from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ..tools.utils.qgisred_flow_paths import (
    DOWNSTREAM,
    ROUTE_MAX_FLOW,
    ROUTE_MIN_ENERGY,
    ROUTE_MIN_LENGTH,
    ROUTE_MIN_TIME,
    UPSTREAM,
    faded,
    flow_path_widths,
    oriented_links,
    route_decomposition,
    route_flow_balance,
    route_link_costs,
    route_shades,
    route_summary,
    source_nodes_from,
    trace_flow_paths,
    trace_routes,
    upstream_link_sources,
)

_NODE_LAYER_IDENTIFIERS = ("qgisred_junctions", "qgisred_tanks", "qgisred_reservoirs")
_LINK_LAYER_IDENTIFIERS = ("qgisred_pipes", "qgisred_pumps", "qgisred_valves")

_DOWNSTREAM_COLORS = ((20, 70, 200), (60, 140, 230), (120, 185, 240), (180, 215, 245))

_UPSTREAM_HUE_RANGE = (0.0, 56.0)
_UPSTREAM_LEVEL_SATURATION = (0.95, 0.6, 0.4, 0.25)

_SIGNED_STATISTICS = {"Maximum": "Flow", "Minimum": "Flow", "Average": "Flow_Sig"}

_ROUTE_COLORS = {
    UPSTREAM: (((215, 25, 28), (125, 10, 15)), ((238, 140, 134), (176, 92, 90))),
    DOWNSTREAM: (((26, 115, 232), (16, 64, 150)), ((122, 172, 242), (78, 118, 186))),
}
_ROUTE_WIDTH_MM = 1.8
_ALTERNATIVE_WIDTH_MM = 1.3
_LABELED_ROUTES = 3

_ROUTE_OK = "ok"
_ROUTE_DISCONNECTED = "disconnected"
_ROUTE_STATISTIC = "statistic"

_MIN_WIDTH_MM = 0.5
_MAX_WIDTH_MM = 2.5


def _level_color(colors, level):
    from qgis.PyQt.QtGui import QColor

    rgb = colors[min(max(int(level), 0), len(colors) - 1)]
    return QColor(rgb[0], rgb[1], rgb[2])


def _source_hue_fraction(slot):
    if slot <= 0:
        return 0.0
    if slot == 1:
        return 1.0
    k, fraction, denominator = slot - 1, 0.0, 1.0
    while k:
        denominator *= 2.0
        k, bit = divmod(k, 2)
        fraction += bit / denominator
    return fraction


def _source_color(slot, level):
    from qgis.PyQt.QtGui import QColor

    first, last = _UPSTREAM_HUE_RANGE
    hue = first + (last - first) * _source_hue_fraction(slot)
    saturation = _UPSTREAM_LEVEL_SATURATION[min(max(int(level), 0), len(_UPSTREAM_LEVEL_SATURATION) - 1)]
    return QColor.fromHsvF(hue / 360.0, saturation, 0.9 if level <= 0 else 1.0)


def _link_kind(link_type):
    if link_type == 2:
        return "pump"
    if link_type is not None and link_type >= 3:
        return "valve"
    return "pipe"


_MODE_PATHS = "paths"
_MODE_ROUTES = "routes"


class FlowPathsSection:
    FLOW_PATHS_HIGHLIGHT_KEY = "flowPaths"
    FLOW_PATHS_TOOL = "FlowPaths"
    FLOW_ROUTES_TOOL = "FlowRoutes"

    def runFlowPaths(self):
        self._runFlowTool(_MODE_PATHS)

    def runFlowRoutes(self):
        if self._runFlowTool(_MODE_ROUTES) and getattr(self, "_flowRoutesOrigin", None) is None:
            self.pushMessage(self.tr("Click the start node and then the end node of the routes."))

    def _flowToolParts(self, mode):
        if mode == _MODE_ROUTES:
            return (getattr(self, "flowRoutesButton", None), self.FLOW_ROUTES_TOOL, ":/images/iconFlowRoutes.svg",
                    self._flowRoutesClick, None, self._flowRoutesRightClick, self._clearFlowRoutes)
        return (getattr(self, "flowPathsButton", None), self.FLOW_PATHS_TOOL, ":/images/iconFlowPaths.svg",
                self._flowPathsClick, self._flowPathsDoubleClick, None, None)

    def _runFlowTool(self, mode):
        button, key, cursor, click, double_click, right_click, escape = self._flowToolParts(mode)
        if button is not None and not button.isChecked():
            self._leaveFlowPaths(key)
            return False
        if not self.checkDependencies():
            self._setFlowPathsButtonChecked(button, False)
            return False
        self.defineCurrentProject()
        if not self.isValidProject():
            self._setFlowPathsButtonChecked(button, False)
            return False
        self._ensureResultsDockVisibleForTimeSeries()
        if not os.path.exists(self._outFilePath()):
            self.pushMessage(self.tr("Run a simulation first to identify the flow paths."), level=1)
            self._setFlowPathsButtonChecked(button, False)
            return False
        self._connectFlowPathsToResults()
        self._registerFlowPathsHighlightOwner()

        from ..tools.map_tools.qgisred_flowPaths import QGISRedFlowPathsTool

        tool = self.myMapTools.get(key)
        if tool is None:
            tool = QGISRedFlowPathsTool(button, self, click, cursor=cursor, doubleClickMethod=double_click,
                                        rightClickMethod=right_click, escapeMethod=escape)
            self.myMapTools[key] = tool
        changed = mode != getattr(self, "_flowPathsMode", None)
        self._flowPathsMode = mode
        self.iface.mapCanvas().setMapTool(tool)
        self._setFlowPathsButtonChecked(button, True)
        if changed:
            self._redrawFlowPaths()
        return True

    def _leaveFlowPaths(self, key):
        manager = getattr(self, "highlightManager", None)
        owner = manager.ownerByKey(self.FLOW_PATHS_HIGHLIGHT_KEY) if manager is not None else None
        tool = (getattr(self, "myMapTools", None) or {}).get(key)
        if tool is not None and self.iface.mapCanvas().mapTool() is tool:
            self.iface.mapCanvas().unsetMapTool(tool)
        if owner is not None:
            manager.suspend(owner)
        else:
            self._clearFlowPathsDrawing()

    @staticmethod
    def _setFlowPathsButtonChecked(button, checked):
        if button is None:
            return
        with suppress(Exception):
            if button.isChecked() != bool(checked):
                button.setChecked(bool(checked))

    def _connectFlowPathsToResults(self):
        if getattr(self, "_flowPathsResultsConnected", False):
            return
        dock = getattr(self, "ResultDockwidget", None)
        if dock is None:
            return
        with suppress(Exception):
            dock.timeTextChanged.connect(self._onFlowPathsResultsChanged)
        with suppress(Exception):
            dock.resultPropertyChanged.connect(self._onFlowPathsResultsChanged)
        with suppress(Exception):
            dock.statisticsModeChanged.connect(self._onFlowPathsResultsChanged)
        with suppress(Exception):
            dock.simulationFinished.connect(self._onFlowPathsResultsChanged)
        self._flowPathsResultsConnected = True

    def _disconnectFlowPathsFromResults(self):
        dock = getattr(self, "ResultDockwidget", None)
        if dock is not None:
            for signal in ("timeTextChanged", "resultPropertyChanged", "statisticsModeChanged", "simulationFinished"):
                with suppress(Exception):
                    getattr(dock, signal).disconnect(self._onFlowPathsResultsChanged)
        self._flowPathsResultsConnected = False

    def _registerFlowPathsHighlightOwner(self):
        manager = getattr(self, "highlightManager", None)
        if manager is None or manager.ownerByKey(self.FLOW_PATHS_HIGHLIGHT_KEY) is not None:
            return
        from ..tools.utils.qgisred_highlight_manager import QGISRedDelegatedHighlightOwner

        manager.register(QGISRedDelegatedHighlightOwner(
            self.FLOW_PATHS_HIGHLIGHT_KEY,
            lambda: [],
            self._clearFlowPathsDrawing,
            self._redrawFlowPaths,
            ownedTools=lambda: [(getattr(self, "myMapTools", None) or {}).get(key)
                                for key in (self.FLOW_PATHS_TOOL, self.FLOW_ROUTES_TOOL)],
        ))

    def _flowPathsSuspended(self):
        manager = getattr(self, "highlightManager", None)
        if manager is None:
            return False
        owner = manager.ownerByKey(self.FLOW_PATHS_HIGHLIGHT_KEY)
        return owner is not None and manager.isSuspended(owner)

    def resetFlowPaths(self):
        self._clearFlowPathsDrawing()
        self._disconnectFlowPathsFromResults()
        self._flowPathsNode = None
        self._flowRoutesOrigin = None
        self._flowRoutesTarget = None
        self._flowPathsRouteState = None
        self._flowPathsRouteChoice = None
        self._flowPathsShownRoutes = []
        self._flowPathsSourceSlots = {}
        self._flowPathsStructure = None
        self._flowPathsStatCache = None
        self._flowPathsGeometries = None

    def _flowPathsClick(self, point):
        node_id = self._resolveFlowPathsNode(point)
        if node_id is not None:
            self._selectFlowPathsNode(node_id)

    def _flowPathsDoubleClick(self, point):
        node_id = self._resolveFlowPathsNode(point)
        if node_id is not None:
            self._selectFlowPathsNode(node_id)
            return
        self._flowPathsNode = None
        self._flowPathsSourceSlots = {}
        self._clearFlowPathsDrawing()

    def _flowRoutesClick(self, point):
        origin = getattr(self, "_flowRoutesOrigin", None)
        target = getattr(self, "_flowRoutesTarget", None)
        if origin is not None and target is not None:
            if self._selectFlowRouteAt(point, labels_only=True):
                return
            node_id = self._resolveFlowPathsNode(point)
            if node_id is not None and node_id != target:
                self._flowPathsShownRoutes = []
                self._setFlowRoutesNodes(node_id, None)
                return
            self._selectFlowRouteAt(point)
            return
        node_id = self._resolveFlowPathsNode(point)
        if node_id is None or node_id == origin:
            return
        if origin is None:
            self._setFlowRoutesNodes(node_id, None)
        else:
            self._setFlowRoutesNodes(origin, node_id)

    def _setFlowRoutesNodes(self, origin, target):
        self._flowRoutesOrigin = origin
        self._flowRoutesTarget = target
        self._flowPathsRouteChoice = None
        self._flowPathsRouteState = None
        self._flowPathsGeometries = None
        self._redrawFlowPaths()

    def _clearFlowRoutes(self):
        self._flowPathsShownRoutes = []
        self._setFlowRoutesNodes(None, None)

    def _selectFlowPathsNode(self, node_id):
        same_node = node_id == getattr(self, "_flowPathsNode", None)
        if not same_node:
            self._flowPathsSourceSlots = {}
        self._flowPathsNode = node_id
        self._flowPathsGeometries = None
        if self._flowPathsStatistic() is False:
            self._clearFlowPathsDrawing()
            self.pushMessage(self.tr("Range and standard deviation carry no flow direction: choose another statistic to see the paths."), level=1)  # noqa: E501
            return
        result = self._redrawFlowPaths()
        if result is None or same_node:
            return
        has_up, has_down = bool(result[UPSTREAM]["links"]), bool(result[DOWNSTREAM]["links"])
        if not has_up and not has_down:
            self.pushMessage(self.tr("Node {0} has no upstream or downstream paths at this instant.").format(node_id))
        elif not has_up:
            self.pushMessage(self.tr("Node {0} has no upstream paths at this instant.").format(node_id))
        elif not has_down:
            self.pushMessage(self.tr("Node {0} has no downstream paths at this instant.").format(node_id))

    def _selectFlowRouteAt(self, point, labels_only=False):
        routes = getattr(self, "_flowPathsShownRoutes", None) or []
        if getattr(self, "_flowRoutesTarget", None) is None or len(routes) < 2:
            return False
        index = None
        item = getattr(self, "_flowPathsItem", None)
        if item is not None:
            with suppress(Exception):
                index = item.routeLabelAt(self.iface.mapCanvas().getCoordinateTransform().transform(point))
        on_label = index is not None
        if index is None and not labels_only:
            index = self._flowRouteNear(point, routes)
        if index is None or index >= len(routes):
            return False
        choice = tuple(routes[index]["own"])
        current = getattr(self, "_flowPathsRouteChoice", None) or tuple(routes[0]["own"])
        if choice != current:
            self._flowPathsRouteChoice = choice
            self._flowPathsRouteExpanded = None
            self._redrawFlowPaths()
        elif on_label and self._flowRoutesCriterion() == ROUTE_MAX_FLOW:
            key = self._flowRouteExpandKey(choice)
            self._flowPathsRouteExpanded = None if getattr(self, "_flowPathsRouteExpanded", None) == key else key
            self._redrawFlowPaths()
        return True

    def _flowRouteExpandKey(self, choice):
        return (getattr(self, "_flowRoutesOrigin", None), getattr(self, "_flowRoutesTarget", None), choice)

    def _flowRouteNear(self, point, routes):
        from qgis.core import QgsCoordinateTransform, QgsGeometry, QgsProject

        canvas = self.iface.mapCanvas()
        tolerance = canvas.getCoordinateTransform().mapUnitsPerPixel() * 6
        destination = canvas.mapSettings().destinationCrs()
        links = self._flowPathsGeometryIndex()["links"]
        best, best_distance = None, None
        for index, route in enumerate(routes):
            for lid in route["own"]:
                found = links.get(str(lid))
                if found is None:
                    continue
                geometry, crs = found
                geom = QgsGeometry(geometry)
                if crs is not None and crs.isValid() and destination.isValid() and crs != destination:
                    with suppress(Exception):
                        geom.transform(QgsCoordinateTransform(crs, destination, QgsProject.instance()))
                distance = geom.distance(QgsGeometry.fromPointXY(point))
                if distance <= tolerance and (best_distance is None or distance < best_distance):
                    best, best_distance = index, distance
        return best

    def _flowRoutesRightClick(self, _point):
        from qgis.PyQt.QtGui import QCursor
        from qgis.PyQt.QtWidgets import QMenu

        menu = QMenu()
        clear = None
        current = self._flowRoutesCriterion()
        labels = dict(self._flowRoutesCriteria())
        menu.addSection(self.tr("Optimal route"))
        for key, label in labels.items():
            action = menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(key == current)
            action.setData(key)
        if getattr(self, "_flowRoutesOrigin", None) is not None:
            menu.addSeparator()
            clear = menu.addAction(self.tr("Clear routes"))
        chosen = menu.exec(QCursor.pos())
        if chosen is None:
            return True
        if chosen is clear:
            self._clearFlowRoutes()
        elif chosen.data() in labels:
            self._flowPathsCriterion = chosen.data()
            self._applyFlowRoutesCriterion(labels[chosen.data()])
        return True

    def _flowRoutesCriteria(self):
        return (
            (ROUTE_MAX_FLOW, self.tr("Maximum flow")),
            (ROUTE_MIN_TIME, self.tr("Minimum travel time")),
            (ROUTE_MIN_ENERGY, self.tr("Minimum energy dissipated")),
            (ROUTE_MIN_LENGTH, self.tr("Minimum length")),
        )

    def _flowRoutesCriterion(self):
        return getattr(self, "_flowPathsCriterion", None) or ROUTE_MAX_FLOW

    def _applyFlowRoutesCriterion(self, label):
        origin = getattr(self, "_flowRoutesOrigin", None)
        target = getattr(self, "_flowRoutesTarget", None)
        self._flowPathsRouteChoice = None
        result = self._redrawFlowPaths() if target is not None else None
        if result and result.get("state") == _ROUTE_OK and len(result["routes"]) == 1:
            self.pushMessage(self.tr(
                "There is only one route between nodes {0} and {1}: every criterion gives the same one.").format(
                    origin, target))
        else:
            self.pushMessage(self.tr("Optimal route: {0}.").format(label))

    def _resolveFlowPathsNode(self, point):
        from qgis.core import QgsRectangle

        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance,
                            point.x() + tolerance, point.y() + tolerance)
        settings = self.iface.mapCanvas().mapSettings()
        nearest, nearest_distance = None, None
        for identifier in _NODE_LAYER_IDENTIFIERS:
            layer = self._flowPathsLayer(identifier)
            if layer is None or not layer.isSpatial():
                continue
            layer_rect = rect
            with suppress(Exception):
                layer_rect = settings.mapToLayerCoordinates(layer, rect)
            id_field = QGISRedFieldUtils().getIdFieldName(layer)
            for feature in layer.getFeatures(layer_rect):
                geometry = feature.geometry()
                if geometry is None or geometry.isEmpty():
                    continue
                location = geometry.asPoint()
                with suppress(Exception):
                    location = settings.layerToMapCoordinates(layer, location)
                distance = location.sqrDist(point)
                if nearest_distance is None or distance < nearest_distance:
                    nearest, nearest_distance = str(feature.attribute(id_field)), distance
        return nearest

    @staticmethod
    def _flowPathsLayer(identifier):
        from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        for layer in QGISRedLayerUtils().getLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                return layer
        return None

    def _onFlowPathsResultsChanged(self, *_args):
        if self._flowPathsSuspended():
            return
        with suppress(Exception):
            self._redrawFlowPaths()

    def _flowPathsOutStamp(self):
        out_path = self._outFilePath()
        with suppress(OSError):
            stat = os.stat(out_path)
            return (out_path, stat.st_mtime, stat.st_size)
        return (out_path, None, None)

    def _flowPathsNetwork(self):
        stamp = self._flowPathsOutStamp()
        cached = getattr(self, "_flowPathsStructure", None)
        if cached is not None and cached["stamp"] == stamp:
            return cached
        from ..ui.analysis.qgisred_results_binary import getOut_Metadata

        with open(stamp[0], "rb") as f:
            meta = getOut_Metadata(f, include_lengths=True)
        if not meta:
            return None
        node_ids = meta["node_ids"]
        link_ids = meta["link_ids"]
        endpoints = {}
        for i, lid in enumerate(link_ids):
            a, b = meta["link_from"][i], meta["link_to"][i]
            if 0 <= a < len(node_ids) and 0 <= b < len(node_ids):
                endpoints[lid] = (node_ids[a], node_ids[b])
        structure = {
            "stamp": stamp,
            "endpoints": endpoints,
            "link_types": dict(zip(link_ids, meta["link_types"])),
            "lengths": dict(zip(link_ids, meta.get("link_lengths") or [])),
            "flow_units": meta.get("flow_units"),
            "node_types": dict(zip(node_ids, meta["node_types"])),
        }
        self._flowPathsStructure = structure
        return structure

    def _flowPathsStatistic(self):
        dock = getattr(self, "ResultDockwidget", None)
        if dock is None or not getattr(dock, "_statsMode", False):
            return None
        text = None
        with suppress(Exception):
            text = dock.cbStatistics.currentText()
        names = {
            getattr(dock, "lbl_maximum", None): "Maximum",
            getattr(dock, "lbl_minimum", None): "Minimum",
            getattr(dock, "lbl_average", None): "Average",
        }
        return names.get(text, False)

    def _flowPathsCurrentSeconds(self, source):
        dock = getattr(self, "ResultDockwidget", None)
        index = 0
        if dock is not None:
            with suppress(Exception):
                index = max(0, dock.cbTimes.currentIndex())
        times = (source or {}).get("times") or []
        if 0 <= index < len(times):
            return times[index]
        return times[-1] if times else 0

    def _flowPathsValues(self):
        results = self._flowPathsResults()
        return results["flows"], results["demands"], results["closed"]

    def _flowPathsResults(self):
        out_path = self._outFilePath()
        source = None
        with suppress(Exception):
            source = self._getTimeSeriesSource()
        hyd = source if source and source.get("kind") == "hyd" else None
        statistic = self._flowPathsStatistic()
        if statistic:
            key = (self._flowPathsOutStamp(), statistic, hyd is not None)
            cache = getattr(self, "_flowPathsStatCache", None)
            if cache is None or cache[0] != key:
                links, nodes = self._flowPathsStatistics(statistic, out_path, hyd)
                flow_field = _SIGNED_STATISTICS[statistic]

                def stat(props, name):
                    return {k: (p.get(name) or {}).get("Value") for k, p in props.items()}

                cache = (key, {
                    "flows": stat(links, flow_field),
                    "demands": stat(nodes, "Demand"),
                    "closed": set(),
                    "velocities": stat(links, "Velocity"),
                    "headlosses": stat(links, "HeadLoss"),
                })
                self._flowPathsStatCache = cache
            return cache[1]

        seconds = self._flowPathsCurrentSeconds(source)
        if source and source.get("kind") == "hyd":
            from ..ui.analysis.qgisred_results_hyd import (
                getHyd_TimeLinksProperties,
                getHyd_TimeNodesProperties,
            )

            links = getHyd_TimeLinksProperties(source["hyd_path"], source["out_path"], seconds)
            nodes = getHyd_TimeNodesProperties(source["hyd_path"], source["out_path"], seconds)
        else:
            from ..ui.analysis.qgisred_results_binary import (
                getOut_TimeLinksProperties,
                getOut_TimeNodesProperties,
            )

            links = getOut_TimeLinksProperties(out_path, seconds)
            nodes = getOut_TimeNodesProperties(out_path, seconds)
        return {
            "flows": {lid: p.get("Flow") for lid, p in links.items()},
            "demands": {nid: p.get("Demand") for nid, p in nodes.items()},
            "closed": {lid for lid, p in links.items() if str(p.get("Status") or "").startswith("Closed")},
            "velocities": {lid: p.get("Velocity") for lid, p in links.items()},
            "headlosses": {lid: p.get("HeadLoss") for lid, p in links.items()},
        }

    @staticmethod
    def _flowPathsStatistics(statistic, out_path, hyd):
        links = nodes = None
        if hyd is not None:
            with suppress(Exception):
                from ..ui.analysis.qgisred_results_hyd import (
                    getHyd_StatLinksProperties,
                    getHyd_StatNodesProperties,
                )

                links = getHyd_StatLinksProperties(hyd["hyd_path"], out_path, statistic)
                nodes = getHyd_StatNodesProperties(hyd["hyd_path"], out_path, statistic)
        if not links:
            from ..ui.analysis.qgisred_results_binary import (
                getOut_StatLinksProperties,
                getOut_StatNodesProperties,
            )

            links = getOut_StatLinksProperties(out_path, statistic)
            nodes = getOut_StatNodesProperties(out_path, statistic)
        return links or {}, nodes or {}

    def computeFlowPaths(self, node_id):
        network = self._flowPathsNetwork()
        if network is None:
            return None
        flows, demands, closed = self._flowPathsValues()
        oriented = oriented_links(network["endpoints"], flows, closed_links=closed)
        sources = source_nodes_from(network["node_types"], demands)
        upstream = trace_flow_paths(node_id, oriented, sources, UPSTREAM)
        upstream["sources"], upstream["source_order"] = upstream_link_sources(
            node_id, upstream["links"], oriented, flows, sources)
        return {
            UPSTREAM: upstream,
            DOWNSTREAM: trace_flow_paths(node_id, oriented, sources, DOWNSTREAM),
            "flows": flows,
        }

    def computeFlowRoutes(self, origin, target, criterion):
        empty = {"direction": None, "routes": [], "summaries": [], "flows": {}}
        network = self._flowPathsNetwork()
        if network is None:
            return None
        if self._flowPathsStatistic() not in (None, "Average"):
            return dict(empty, state=_ROUTE_STATISTIC)
        values = self._flowPathsResults()
        flows = values["flows"]
        oriented = oriented_links(network["endpoints"], flows, closed_links=values["closed"])
        sources = source_nodes_from(network["node_types"], values["demands"])
        lengths = network.get("lengths")
        for direction in (DOWNSTREAM, UPSTREAM):
            trace = trace_flow_paths(origin, oriented, sources, direction)
            if target not in trace["nodes"]:
                continue
            links = trace_routes(origin, target, oriented, trace["links"], direction)
            if not links:
                continue
            upstream_end, downstream_end = (origin, target) if direction == DOWNSTREAM else (target, origin)
            costs = route_link_costs(criterion, links, flows, values["velocities"], values["headlosses"], lengths)
            routes = route_decomposition(upstream_end, downstream_end, oriented, links, costs, flows,
                                         by_flow=criterion == ROUTE_MAX_FLOW)
            if not routes:
                continue
            summaries = []
            for route in routes:
                summary = route_summary(route["links"], flows, values["velocities"], values["headlosses"], lengths)
                summary["balance"] = route_flow_balance(route["links"], oriented, flows, values["demands"])
                summaries.append(summary)
            return {"state": _ROUTE_OK, "direction": direction, "routes": routes,
                    "summaries": summaries, "flows": flows}
        return dict(empty, state=_ROUTE_DISCONNECTED, flows=flows)

    def _flowPathsGeometryIndex(self):
        cached = getattr(self, "_flowPathsGeometries", None)
        if cached is not None:
            return cached
        links, nodes = {}, {}
        for identifiers, target in ((_LINK_LAYER_IDENTIFIERS, links), (_NODE_LAYER_IDENTIFIERS, nodes)):
            for identifier in identifiers:
                layer = self._flowPathsLayer(identifier)
                if layer is None:
                    continue
                id_field = QGISRedFieldUtils().getIdFieldName(layer)
                crs = layer.crs()
                for feature in layer.getFeatures():
                    target[str(feature.attribute(id_field))] = (feature.geometry(), crs)
        cached = {"links": links, "nodes": nodes}
        self._flowPathsGeometries = cached
        return cached

    def _redrawFlowPaths(self):
        self._clearFlowPathsDrawing()
        if getattr(self, "_flowPathsMode", None) == _MODE_ROUTES:
            origin = getattr(self, "_flowRoutesOrigin", None)
            if origin is None:
                return None
            return self._redrawFlowRoutes(origin, getattr(self, "_flowRoutesTarget", None))
        node_id = getattr(self, "_flowPathsNode", None)
        if node_id is None or self._flowPathsStatistic() is False:
            return None
        try:
            result = self.computeFlowPaths(node_id)
        except Exception:
            result = None
        if result is None:
            return None

        from ..tools.utils.qgisred_flow_paths_canvas_item import (
            QGISRedFlowPathsCanvasItem,
            build_background_symbol,
            build_link_symbol,
            build_node_symbol,
        )

        geometries = self._flowPathsGeometryIndex()
        link_types = (self._flowPathsNetwork() or {}).get("link_types", {})
        flows = result["flows"]
        up_links = result[UPSTREAM]["links"]
        down_links = result[DOWNSTREAM]["links"]
        widths = flow_path_widths(flows, set(up_links) | set(down_links), _MIN_WIDTH_MM, _MAX_WIDTH_MM)

        entries = []
        background = {}
        on_route = {str(lid) for lid in set(up_links) | set(down_links)}
        for lid, (geometry, crs) in geometries["links"].items():
            if lid in on_route:
                continue
            kind = _link_kind(link_types.get(lid))
            if kind not in background:
                background[kind] = build_background_symbol(kind)
            entries.append((kind, geometry, crs))
        entries.sort(key=lambda entry: entry[0])
        entries = [(geometry, crs, background[kind]) for kind, geometry, crs in entries]

        link_source = result[UPSTREAM].get("sources", {})
        slots = getattr(self, "_flowPathsSourceSlots", None)
        if slots is None:
            slots = self._flowPathsSourceSlots = {}
        for source in result[UPSTREAM].get("source_order", []):
            slots.setdefault(source, len(slots))

        def up_color(lid, level):
            return _source_color(slots.get(link_source.get(lid), 0), level)

        def down_color(_lid, level):
            return _level_color(_DOWNSTREAM_COLORS, level)

        symbols = {}
        items = []
        for links, color_of in ((down_links, down_color), (up_links, up_color)):
            for lid, level in links.items():
                found = geometries["links"].get(str(lid))
                if found is None:
                    continue
                geometry, crs = found
                if (flows.get(lid) or 0) < 0:
                    with suppress(Exception):
                        geometry = self._reversedLine(geometry)
                color = color_of(lid, level)
                key = (_link_kind(link_types.get(lid)), color.rgb(), round(widths[lid], 1))
                if key not in symbols:
                    symbols[key] = build_link_symbol(key[0], color, key[2])
                items.append((level, key, geometry, crs))
        items.sort(key=lambda item: (-item[0], item[1][2], item[1][0]))
        entries.extend((geometry, crs, symbols[key]) for _level, key, geometry, crs in items)

        node_geometry = geometries["nodes"].get(str(node_id))
        if node_geometry is not None:
            entries.append((node_geometry[0], node_geometry[1], build_node_symbol()))

        canvas = self.iface.mapCanvas()
        item = getattr(self, "_flowPathsItem", None)
        if item is None:
            item = QGISRedFlowPathsCanvasItem(canvas)
            self._flowPathsItem = item
        item.setEntries(entries, kept_labels=on_route)
        return result

    def _redrawFlowRoutes(self, origin, target):
        self._flowPathsShownRoutes = []
        if target is None:
            result = {"state": None, "direction": None, "routes": [], "summaries": [], "flows": {}}
        else:
            try:
                result = self.computeFlowRoutes(origin, target, self._flowRoutesCriterion())
            except Exception:
                result = None
        if result is None:
            return None

        from ..tools.utils.qgisred_flow_paths_canvas_item import (
            QGISRedFlowPathsCanvasItem,
            build_background_symbol,
            build_node_symbol,
            build_route_symbol,
        )
        from qgis.PyQt.QtGui import QColor

        geometries = self._flowPathsGeometryIndex()
        link_types = (self._flowPathsNetwork() or {}).get("link_types", {})
        flows = result["flows"]
        routes = result["routes"]
        self._flowPathsShownRoutes = routes
        choice = getattr(self, "_flowPathsRouteChoice", None)
        state = result["state"]
        selected = next((i for i, route in enumerate(routes) if tuple(route["own"]) == choice), 0)
        on_route = {str(lid) for route in routes for lid in route["links"]}

        entries = []
        background = {}
        for lid, (geometry, crs) in geometries["links"].items():
            if lid in on_route:
                continue
            kind = _link_kind(link_types.get(lid))
            if kind not in background:
                background[kind] = build_background_symbol(kind)
            entries.append((kind, geometry, crs))
        entries.sort(key=lambda entry: entry[0])
        entries = [(geometry, crs, background[kind]) for kind, geometry, crs in entries]

        labels = []
        if result["direction"] is not None:
            (fill, border), (alt_fill, alt_border) = _ROUTE_COLORS[result["direction"]]
            ranked = [0] + sorted(range(1, len(routes)), key=lambda i: self._flowRouteRank(result["summaries"][i]))
            rank = {index: position for position, index in enumerate(ranked)}
            colors = {"selected": (QColor(*fill), QColor(*border))}
            for position, shade in enumerate(route_shades(len(routes))):
                colors[position] = (QColor(*faded(alt_fill, shade)), QColor(*faded(alt_border, shade * 0.5)))
            arrow_color = QColor(*alt_border).darker(190)
            symbols = {}
            strong = set(routes[selected]["links"])
            pale = [(lid, rank[i]) for i, route in enumerate(routes) for lid in route["own"] if lid not in strong]
            for lid, tone in pale + [(lid, "selected") for lid in routes[selected]["links"]]:
                is_selected = tone == "selected"
                found = geometries["links"].get(str(lid))
                if found is None:
                    continue
                geometry, crs = found
                if (flows.get(lid) or 0) < 0:
                    with suppress(Exception):
                        geometry = self._reversedLine(geometry)
                key = (_link_kind(link_types.get(lid)), tone)
                if key not in symbols:
                    color, casing = colors[tone]
                    symbols[key] = build_route_symbol(
                        key[0], color, casing, _ROUTE_WIDTH_MM if is_selected else _ALTERNATIVE_WIDTH_MM,
                        arrow_color=None if is_selected else arrow_color)
                entries.append((geometry, crs, symbols[key]))
            order = [i for i in ranked if i != selected] + [selected]
            for index in order:
                if rank[index] >= _LABELED_ROUTES and index != selected:
                    continue
                label = self._flowRouteLabel(index, routes, result["summaries"][index], geometries)
                if label is not None:
                    label["selected"] = index == selected
                    label["rank"] = rank[index]
                    label["dot"] = rank[index] >= _LABELED_ROUTES
                    label["color"] = colors["selected"][0]
                    label["tone"] = colors[rank[index]]
                    if index == selected:
                        label["details"] = self._flowRouteDetails(routes[index], result["summaries"][index])
                    labels.append(label)

        for node_id, shape in ((origin, "circle"), (target, "diamond")):
            node_geometry = geometries["nodes"].get(str(node_id))
            if node_geometry is not None:
                entries.append((node_geometry[0], node_geometry[1], build_node_symbol(shape)))

        canvas = self.iface.mapCanvas()
        item = getattr(self, "_flowPathsItem", None)
        if item is None:
            item = QGISRedFlowPathsCanvasItem(canvas)
            self._flowPathsItem = item
        kept = {str(lid) for lid in routes[selected]["links"]} if routes else set()
        item.setEntries(entries, kept_labels=kept)
        obstacles = [geometries["links"][lid] for lid in on_route if lid in geometries["links"]]
        item.setRouteLabels(labels, obstacles)

        previous = getattr(self, "_flowPathsRouteState", None)
        if state != previous:
            if state == _ROUTE_DISCONNECTED:
                self.pushMessage(self.tr(
                    "There is no one-way route between nodes {0} and {1} at this instant.").format(origin, target))
                if previous is None:
                    self._clearFlowRoutes()
                    return None
            elif state == _ROUTE_STATISTIC:
                self.pushMessage(self.tr(
                    "The routes between two nodes are only available for the average statistic."), level=1)
        self._flowPathsRouteState = state
        return result

    def _flowRouteRank(self, summary):
        criterion = self._flowRoutesCriterion()
        if criterion == ROUTE_MAX_FLOW:
            return -summary["flow"]
        return summary[{ROUTE_MIN_TIME: "time", ROUTE_MIN_ENERGY: "energy", ROUTE_MIN_LENGTH: "length"}[criterion]]

    def _flowRouteLabel(self, index, routes, summary, geometries):
        own = list(routes[index]["own"])
        found = None
        for lid in own[len(own) // 2:] + own[:len(own) // 2]:
            found = geometries["links"].get(str(lid))
            if found is not None:
                break
        if found is None:
            return None
        geometry, crs = found
        point = geometry.interpolate(geometry.length() / 2.0)
        if point is None or point.isEmpty():
            return None
        title, subtitle = self._flowRouteTexts(summary)
        if index == 0 and len(routes) > 1:
            title = "\u2605 " + title
        return {"geometry": point, "crs": crs, "title": title, "subtitle": subtitle, "index": index}

    def _flowRouteDetails(self, route, summary):
        balance = summary.get("balance")
        if not balance or self._flowRoutesCriterion() != ROUTE_MAX_FLOW:
            return []
        if getattr(self, "_flowPathsRouteExpanded", None) != self._flowRouteExpandKey(tuple(route["own"])):
            return []
        return [
            self.tr("Links: {0}").format(balance["links"]),
            self.tr("Initial flow: {0}").format(self._formatFlowRouteFlow(balance["first"])),
            self.tr("Final flow: {0}").format(self._formatFlowRouteFlow(balance["last"])),
            self.tr("Inflows: {0}").format(self._formatFlowRouteFlow(balance["gained"])),
            self.tr("Withdrawals: {0}").format(self._formatFlowRouteFlow(balance["lost"])),
        ]

    def _flowRouteTexts(self, summary):
        texts = {
            ROUTE_MIN_TIME: self._formatFlowRouteTime(summary["time"]),
            ROUTE_MIN_LENGTH: self._formatFlowRouteLength(summary["length"]),
            ROUTE_MAX_FLOW: self._formatFlowRouteFlow(summary["flow"]),
            ROUTE_MIN_ENERGY: self._formatFlowRouteEnergy(summary["energy"]),
        }
        criterion = self._flowRoutesCriterion()
        rest = [texts[key] for key in (ROUTE_MIN_TIME, ROUTE_MIN_LENGTH, ROUTE_MAX_FLOW) if key != criterion]
        return texts[criterion], " \u00b7 ".join(rest[:2])

    @staticmethod
    def _formatNumber(value, decimals):
        from qgis.PyQt.QtCore import QLocale

        return QLocale().toString(float(value), "f", decimals)

    def _flowRouteMetric(self):
        network = self._flowPathsNetwork() or {}
        units = network.get("flow_units")
        return units is None or int(units) >= 5

    def _formatFlowRouteTime(self, seconds):
        if seconds == float("inf"):
            return "\u221e"
        if seconds < 60:
            return "{0} s".format(int(round(seconds)))
        minutes = int(round(seconds / 60.0))
        if minutes < 60:
            return "{0} min".format(minutes)
        return "{0} h {1} min".format(minutes // 60, minutes % 60)

    def _formatFlowRouteLength(self, length):
        if self._flowRouteMetric():
            if length >= 1000:
                return "{0} km".format(self._formatNumber(length / 1000.0, 2))
            return "{0} m".format(self._formatNumber(length, 0))
        if length >= 5280:
            return "{0} mi".format(self._formatNumber(length / 5280.0, 2))
        return "{0} ft".format(self._formatNumber(length, 0))

    def _formatFlowRouteFlow(self, flow):
        from ..tools.utils.qgisred_project_utils import _FLOW_UNIT_SYMBOLS

        codes = ("CFS", "GPM", "MGD", "IMGD", "AFD", "LPS", "LPM", "MLD", "CMH", "CMD")
        unit = ""
        with suppress(Exception):
            unit = _FLOW_UNIT_SYMBOLS.get(codes[int((self._flowPathsNetwork() or {}).get("flow_units"))], "")
        return "{0} {1}".format(self._formatNumber(flow, 2), unit).strip()

    def _formatFlowRouteEnergy(self, energy):
        from ..ui.analysis.qgisred_results_hyd import _CFS_TO_FLOW, _CFS_TO_M3S

        units = (self._flowPathsNetwork() or {}).get("flow_units")
        with suppress(Exception):
            per_cfs = _CFS_TO_FLOW.get(int(units))
            if per_cfs:
                head_to_m = 1.0 if self._flowRouteMetric() else 0.3048
                kilowatts = 9.81 * energy / per_cfs * _CFS_TO_M3S * head_to_m
                return "{0} kW".format(self._formatNumber(kilowatts, 2))
        return self._formatNumber(energy, 2)

    @staticmethod
    def _reversedLine(geometry):
        from qgis.core import QgsGeometry

        return QgsGeometry(geometry.constGet().reversed())

    def _clearFlowPathsDrawing(self):
        item = getattr(self, "_flowPathsItem", None)
        if item is not None:
            item.dispose()
        self._flowPathsItem = None
