# -*- coding: utf-8 -*-
"""Upstream / downstream routes of a node, following the results panel time."""

import os
from contextlib import suppress

from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ..tools.utils.qgisred_flow_paths import (
    DOWNSTREAM,
    UPSTREAM,
    flow_path_widths,
    oriented_links,
    source_nodes_from,
    trace_flow_paths,
    upstream_link_sources,
)

_NODE_LAYER_IDENTIFIERS = ("qgisred_junctions", "qgisred_tanks", "qgisred_reservoirs")
_LINK_LAYER_IDENTIFIERS = ("qgisred_pipes", "qgisred_pumps", "qgisred_valves")

# Downstream routes reaching the node directly first, then those that only
# reach it through one, two, three or more sources (tanks, reservoirs,
# negative demands).
_DOWNSTREAM_COLORS = ((20, 70, 200), (60, 140, 230), (120, 185, 240), (180, 215, 245))

# Upstream routes take a hue per source, from red to cadmium yellow, and lose
# saturation with each source standing between them and the node.
_UPSTREAM_HUE_RANGE = (0.0, 56.0)
_UPSTREAM_LEVEL_SATURATION = (0.95, 0.6, 0.4, 0.25)

# Statistics whose flows keep their sign, and so the direction of the water.
# Range and standard deviation are computed on |Q| and say nothing of it.
_SIGNED_STATISTICS = {"Maximum": "Flow", "Minimum": "Flow", "Average": "Flow_Sig"}

_MIN_WIDTH_MM = 0.5
_MAX_WIDTH_MM = 2.5


def _level_color(colors, level):
    from qgis.PyQt.QtGui import QColor

    rgb = colors[min(max(int(level), 0), len(colors) - 1)]
    return QColor(rgb[0], rgb[1], rgb[2])


def _source_hue_fraction(slot):
    """Where the source in `slot` sits between red (0) and cadmium yellow (1).

    The first two sources take both ends and the next ones keep halving the
    gaps, so every slot keeps its hue however many sources come later.
    """
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


class FlowPathsSection:
    # Identifies the routes in the highlight arbiter.
    FLOW_PATHS_HIGHLIGHT_KEY = "flowPaths"
    FLOW_PATHS_TOOL = "FlowPaths"

    # -- Entry point -------------------------------------------------------
    def runFlowPaths(self):
        button = getattr(self, "flowPathsButton", None)
        if button is not None and not button.isChecked():
            self._leaveFlowPaths()
            return
        if not self.checkDependencies():
            self._setFlowPathsButtonChecked(False)
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            self._setFlowPathsButtonChecked(False)
            return
        self._ensureResultsDockVisibleForTimeSeries()
        if not os.path.exists(self._outFilePath()):
            self.pushMessage(self.tr("Run a simulation first to identify the flow paths."), level=1)
            self._setFlowPathsButtonChecked(False)
            return
        self._connectFlowPathsToResults()
        self._registerFlowPathsHighlightOwner()

        from ..tools.map_tools.qgisred_flowPaths import QGISRedFlowPathsTool

        tool = self.myMapTools.get(self.FLOW_PATHS_TOOL)
        if tool is None:
            tool = QGISRedFlowPathsTool(button, self, self._flowPathsClick, cursor=":/images/iconFlowPaths.svg",
                                        doubleClickMethod=self._flowPathsDoubleClick)
            self.myMapTools[self.FLOW_PATHS_TOOL] = tool
        # Taking the canvas makes the arbiter hand the highlights back to the routes.
        self.iface.mapCanvas().setMapTool(tool)
        self._setFlowPathsButtonChecked(True)

    def _leaveFlowPaths(self):
        """The button was switched off: hide the routes but keep them to come back."""
        manager = getattr(self, "highlightManager", None)
        owner = manager.ownerByKey(self.FLOW_PATHS_HIGHLIGHT_KEY) if manager is not None else None
        tool = (getattr(self, "myMapTools", None) or {}).get(self.FLOW_PATHS_TOOL)
        if tool is not None and self.iface.mapCanvas().mapTool() is tool:
            self.iface.mapCanvas().unsetMapTool(tool)
        if owner is not None:
            manager.suspend(owner)
        else:
            self._clearFlowPathsDrawing()

    def _setFlowPathsButtonChecked(self, checked):
        button = getattr(self, "flowPathsButton", None)
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
            ownedTools=lambda: [(getattr(self, "myMapTools", None) or {}).get(self.FLOW_PATHS_TOOL)],
        ))

    def _flowPathsSuspended(self):
        manager = getattr(self, "highlightManager", None)
        if manager is None:
            return False
        owner = manager.ownerByKey(self.FLOW_PATHS_HIGHLIGHT_KEY)
        return owner is not None and manager.isSuspended(owner)

    def resetFlowPaths(self):
        """Forget the routes entirely (project closed, plugin unloaded)."""
        self._clearFlowPathsDrawing()
        self._disconnectFlowPathsFromResults()
        self._flowPathsNode = None
        self._flowPathsSourceSlots = {}
        self._flowPathsStructure = None
        self._flowPathsStatCache = None
        self._flowPathsGeometries = None

    # -- Map interaction ---------------------------------------------------
    def _flowPathsClick(self, point):
        """A click on a node traces its routes; a click elsewhere does nothing,
        so a stray click while moving around the map keeps them."""
        node_id = self._resolveFlowPathsNode(point)
        if node_id is None:
            return
        same_node = node_id == getattr(self, "_flowPathsNode", None)
        if not same_node:
            # Each node starts its own set of source colours.
            self._flowPathsSourceSlots = {}
        self._flowPathsNode = node_id
        # A new click re-reads the geometries: the network may have been edited.
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

    def _flowPathsDoubleClick(self, point):
        """A double click away from the nodes takes the routes off the map."""
        if self._resolveFlowPathsNode(point) is not None:
            return
        self._flowPathsNode = None
        self._flowPathsSourceSlots = {}
        self._clearFlowPathsDrawing()

    def _resolveFlowPathsNode(self, point):
        from qgis.core import QgsRectangle

        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance,
                            point.x() + tolerance, point.y() + tolerance)
        for identifier in _NODE_LAYER_IDENTIFIERS:
            layer = self._flowPathsLayer(identifier)
            if layer is None or not layer.isSpatial():
                continue
            layer_rect = rect
            with suppress(Exception):
                layer_rect = self.iface.mapCanvas().mapSettings().mapToLayerCoordinates(layer, rect)
            id_field = QGISRedFieldUtils().getIdFieldName(layer)
            for feature in layer.getFeatures(layer_rect):
                return str(feature.attribute(id_field))
        return None

    @staticmethod
    def _flowPathsLayer(identifier):
        from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        for layer in QGISRedLayerUtils().getLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                return layer
        return None

    def _onFlowPathsResultsChanged(self, *_args):
        if getattr(self, "_flowPathsNode", None) is None or self._flowPathsSuspended():
            return
        with suppress(Exception):
            self._redrawFlowPaths()

    # -- Data --------------------------------------------------------------
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
            meta = getOut_Metadata(f)
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
            "node_types": dict(zip(node_ids, meta["node_types"])),
        }
        self._flowPathsStructure = structure
        return structure

    def _flowPathsStatistic(self):
        """The statistic shown by the results panel: None outside statistics,
        "Maximum", "Minimum" or "Average", or False for one without a flow sign."""
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
        """Return (link flows, node demands, closed links) for the instant shown.

        With statistics on, the flows of the statistic shown are used, signed:
        Maximum and Minimum keep the sign of the flow at that time, and Average
        has its own signed column. The sign is all the routes need.
        """
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
                flows = {lid: (p.get(flow_field) or {}).get("Value") for lid, p in links.items()}
                demands = {nid: (p.get("Demand") or {}).get("Value") for nid, p in nodes.items()}
                cache = (key, flows, demands)
                self._flowPathsStatCache = cache
            return cache[1], cache[2], set()

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
        flows = {lid: p.get("Flow") for lid, p in links.items()}
        closed = {lid for lid, p in links.items() if str(p.get("Status") or "").startswith("Closed")}
        demands = {nid: p.get("Demand") for nid, p in nodes.items()}
        return flows, demands, closed

    @staticmethod
    def _flowPathsStatistics(statistic, out_path, hyd):
        """Link and node statistics from the same file the results panel uses."""
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
        """Return {UPSTREAM: trace, DOWNSTREAM: trace, "flows": flows} or None."""
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

    # -- Drawing -----------------------------------------------------------
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
        """Draw the routes of the selected node for the current instant.

        Returns the computed routes, or None when nothing could be drawn.
        """
        self._clearFlowPathsDrawing()
        node_id = getattr(self, "_flowPathsNode", None)
        if node_id is None or self._flowPathsStatistic() is False:
            # Without a flow sign there are no routes: wait for another statistic.
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

        # The rest of the network goes underneath in grey, one shared symbol per
        # link type so the canvas item can draw it in a single run.
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

        # Links of the same colour and width share one symbol as well.
        link_source = result[UPSTREAM].get("sources", {})
        # A source keeps its colour while the node stays selected, even if it
        # stops feeding for a while; newcomers take the next free one.
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
                    # Turn the line so the arrow points the way the water goes.
                    with suppress(Exception):
                        geometry = self._reversedLine(geometry)
                color = color_of(lid, level)
                key = (_link_kind(link_types.get(lid)), color.rgb(), round(widths[lid], 1))
                if key not in symbols:
                    symbols[key] = build_link_symbol(key[0], color, key[2])
                items.append((level, key, geometry, crs))
        # Routes that only arrive through a source sit underneath the direct ones.
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
        # Their labels stay as the results panel draws them, clear of the veil.
        item.setEntries(entries, kept_labels=on_route)
        return result

    @staticmethod
    def _reversedLine(geometry):
        from qgis.core import QgsGeometry

        # QgsCurve and QgsMultiCurve both know how to reverse themselves.
        return QgsGeometry(geometry.constGet().reversed())

    def _clearFlowPathsDrawing(self):
        item = getattr(self, "_flowPathsItem", None)
        if item is not None:
            item.dispose()
        self._flowPathsItem = None
