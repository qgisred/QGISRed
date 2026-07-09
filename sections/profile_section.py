# -*- coding: utf-8 -*-
"""Longitudinal profiles section for QGISRed."""

import os
from contextlib import suppress

from ..tools.utils.qgisred_network_graph import build_adjacency_from_meta
from ..tools.utils.qgisred_profile_path import (
    ProfilePathError,
    build_profile_path,
    cumulative_distances,
    sample_node_variable,
    cumulative_link_losses,
    reference_nodes_from_path,
    add_pass_node,
    remove_pass_node,
    move_pass_node,
    flow_direction_along_path,
)

_NODE_LAYER_IDENTIFIERS = ("qgisred_junctions", "qgisred_tanks", "qgisred_reservoirs")
_LINK_LAYER_IDENTIFIERS = ("qgisred_pipes", "qgisred_pumps", "qgisred_valves")


class ProfileSection:
    def runProfile(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        self._ensureResultsDockVisibleForTimeSeries()
        out_path = self._outFilePath()
        if not os.path.exists(out_path):
            self.pushMessage(self.tr("Run a simulation first to build a longitudinal profile."), level=1)
            return

        self._initProfileDock()
        self._profileReferenceNodes = []
        self._profilePath = None
        self._clearProfileHighlight()
        self.profileDock.clearPlot()
        self.profileDock.show()
        self.profileDock.raise_()
        self.profileDock.setActiveMode("pick")
        self.runProfilePickTool()

    def _initProfileDock(self):
        if getattr(self, "profileDock", None) is not None:
            return
        from ..ui.analysis.qgisred_profile_dock import QGISRedProfileDock
        from qgis.PyQt.QtCore import Qt

        self.profileDock = QGISRedProfileDock(self.iface)
        self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.profileDock)
        self.profileDock.profileModeChanged.connect(self._onProfileModeChanged)
        self.profileDock.clearRequested.connect(self._onProfileClearRequested)
        self.profileDock.variableChanged.connect(self._onProfileVariableChanged)
        self.profileDock.symbolsToggled.connect(self._onProfileSymbolsToggled)
        self.profileDock.visibilityChanged.connect(self._onProfileDockVisibility)
        with suppress(Exception):
            self._initResultsDock()
            self.ResultDockwidget.timeTextChanged.connect(self._onProfileTimeChanged)
        self._profileReferenceNodes = getattr(self, "_profileReferenceNodes", [])
        self._profileHighlights = []
        self._profileMarkers = []

    def _setProfileMapTool(self, kind, callback):
        from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType

        self._deactivateProfileMapTool()
        point_type = SelectPointType.TwoPoints if kind == "two" else SelectPointType.Point
        self.myMapTools["Profile"] = QGISRedSelectPointTool(
            None, self, callback, point_type, cursor=":/images/iconProfile.svg",
        )
        self.iface.mapCanvas().setMapTool(self.myMapTools["Profile"])

    def _deactivateProfileMapTool(self):
        tool = getattr(self, "myMapTools", {}).get("Profile")
        if tool is not None and self.iface.mapCanvas().mapTool() is tool:
            self.iface.mapCanvas().unsetMapTool(tool)

    def runProfilePickTool(self):
        self._setProfileMapTool("one", self.profilePickCallback)

    def _onProfileModeChanged(self, mode):
        self._deactivateProfileMapTool()
        if mode == "pick":
            self._setProfileMapTool("one", self.profilePickCallback)
        elif mode == "add":
            self._setProfileMapTool("one", self.profileAddCallback)
        elif mode == "remove":
            self._setProfileMapTool("one", self.profileRemoveCallback)
        elif mode == "move":
            self._setProfileMapTool("two", self.profileMoveCallback)

    def _onProfileClearRequested(self):
        self._profileReferenceNodes = []
        self._profilePath = None
        self._clearProfileHighlight()
        if getattr(self, "profileDock", None) is not None:
            self.profileDock.clearPlot()

    def _onProfileVariableChanged(self, _key):
        self._redrawProfile()

    def _onProfileSymbolsToggled(self, checked):
        self._profileShowSymbols = bool(checked)
        self._redrawProfile()

    def _profileLinkFlows(self):
        from ..ui.analysis.qgisred_results_binary import getOut_TimeLinksProperties

        data = getOut_TimeLinksProperties(self._outFilePath(), self._profileCurrentTimeSeconds())
        return {lid: props.get("Flow") for lid, props in data.items()}

    def _applyProfileSymbols(self, dock, nodes, links):
        if not getattr(self, "_profileShowSymbols", False):
            dock.clearSymbols()
            return
        node_kind_map = {0: "junction", 1: "reservoir", 2: "tank"}
        node_types = getattr(self, "_profileNodeTypes", {})
        link_types = getattr(self, "_profileLinkTypes", {})
        node_kinds = [node_kind_map.get(node_types.get(n), "junction") for n in nodes]
        try:
            flows = self._profileLinkFlows()
            directions = flow_direction_along_path(
                nodes, links, getattr(self, "_profileLinkEndpoints", {}), flows
            )
        except Exception:
            directions = [0] * len(links)
        link_info = []
        for i, lid in enumerate(links):
            link_type = link_types.get(lid, 1)
            if link_type == 2:
                kind = "pump"
            elif link_type >= 3:
                kind = "valve"
            else:
                kind = "pipe"
            link_info.append({"kind": kind, "direction": directions[i] if i < len(directions) else 0})
        dock.setSymbols(node_kinds, link_info)

    def _onProfileTimeChanged(self, _text):
        self._redrawProfile()

    def _onProfileDockVisibility(self, visible):
        if not visible:
            self._deactivateProfileMapTool()

    def profilePickCallback(self, point):
        node_id = self._resolveProfileNode(point)
        if node_id is None:
            self.pushMessage(self.tr("No network node found at this location."), level=1)
            return
        refs = getattr(self, "_profileReferenceNodes", [])
        if refs and refs[-1] == node_id:
            return
        refs.append(node_id)
        self._profileReferenceNodes = refs
        try:
            self._recomputeProfileStructure()
        except ProfilePathError:
            refs.pop()
            self._profileReferenceNodes = refs
            self.pushMessage(
                self.tr("Selected node is not connected to the previous one along the network."),
                level=1,
            )
            return
        self._redrawProfile()

    def profileAddCallback(self, point):
        node_id = self._resolveProfileNode(point)
        if node_id is None:
            self.pushMessage(self.tr("No network node found at this location."), level=1)
            return
        self._applyProfileAdd(node_id)

    def profileRemoveCallback(self, point):
        node_id = self._resolveProfileNode(point)
        if node_id is None:
            self.pushMessage(self.tr("No network node found at this location."), level=1)
            return
        self._applyProfileRemove(node_id)

    def profileMoveCallback(self, point, new_point):
        node_id = self._resolveProfileNode(point)
        new_node_id = self._resolveProfileNode(new_point)
        if node_id is None or new_node_id is None:
            self.pushMessage(self.tr("No network node found at this location."), level=1)
            return
        self._applyProfileMove(node_id, new_node_id)

    def _applyProfileAdd(self, node_id):
        path = getattr(self, "_profilePath", None)
        if not path or not path["nodes"]:
            return
        try:
            new_path = add_pass_node(path, node_id)
        except ProfilePathError:
            self.pushMessage(self.tr("Pick an intermediate node of the current profile path."), level=1)
            return
        self._profilePath = new_path
        self._profileReferenceNodes = reference_nodes_from_path(new_path)
        self._profileDistances = cumulative_distances(new_path["links"], getattr(self, "_profileLinkLengths", {}))
        self._redrawProfile()

    def _applyProfileRemove(self, node_id):
        refs = getattr(self, "_profileReferenceNodes", [])
        if node_id not in refs:
            self.pushMessage(self.tr("Pick a declared profile point to remove."), level=1)
            return
        self._profileReferenceNodes = remove_pass_node(refs, node_id)
        try:
            self._recomputeProfileStructure()
        except ProfilePathError:
            return
        self._redrawProfile()

    def _applyProfileMove(self, node_id, new_node_id):
        refs = getattr(self, "_profileReferenceNodes", [])
        if node_id not in refs:
            self.pushMessage(self.tr("Only declared profile points can be moved."), level=1)
            return
        previous = list(refs)
        self._profileReferenceNodes = move_pass_node(refs, node_id, new_node_id)
        try:
            self._recomputeProfileStructure()
        except ProfilePathError:
            self._profileReferenceNodes = previous
            with suppress(ProfilePathError):
                self._recomputeProfileStructure()
            self.pushMessage(self.tr("The moved node cannot be connected along the network."), level=1)
            return
        self._redrawProfile()

    def _resolveProfileNode(self, point):
        from qgis.core import QgsRectangle

        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * 10
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance,
                            point.x() + tolerance, point.y() + tolerance)
        for identifier in _NODE_LAYER_IDENTIFIERS:
            layer = self._profileLayerByIdentifier(identifier)
            if layer is None:
                continue
            for feature in layer.getFeatures(rect):
                return str(feature.attribute("ID"))
        return None

    def _profileLayerByIdentifier(self, identifier):
        from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils

        for layer in QGISRedLayerUtils().getLayers():
            if layer.customProperty("qgisred_identifier") == identifier:
                return layer
        return None

    def _profileMetadata(self):
        from ..ui.analysis.qgisred_results_binary import getOut_Metadata

        out_path = self._outFilePath()
        if not os.path.exists(out_path):
            return None
        with open(out_path, "rb") as f:
            return getOut_Metadata(f, include_lengths=True, include_geometry=True)

    def _recomputeProfileStructure(self):
        meta = self._profileMetadata()
        if not meta:
            raise ProfilePathError("No results metadata available")
        adjacency = build_adjacency_from_meta(meta)
        self._profileLinkLengths = {
            meta["link_ids"][i]: (meta["link_lengths"][i] if meta["link_lengths"] else 0.0)
            for i in range(len(meta["link_ids"]))
        }
        self._profileNodeElev = {
            meta["node_ids"][i]: (meta["node_elevations"][i] if meta["node_elevations"] else 0.0)
            for i in range(len(meta["node_ids"]))
        }
        node_ids = meta["node_ids"]
        self._profileNodeTypes = {
            node_ids[i]: meta["node_types"][i] for i in range(len(node_ids))
        }
        self._profileLinkTypes = {
            meta["link_ids"][i]: meta["link_types"][i] for i in range(len(meta["link_ids"]))
        }
        self._profileLinkEndpoints = {
            meta["link_ids"][i]: (node_ids[meta["link_from"][i]], node_ids[meta["link_to"][i]])
            for i in range(len(meta["link_ids"]))
            if 0 <= meta["link_from"][i] < len(node_ids) and 0 <= meta["link_to"][i] < len(node_ids)
        }
        self._profileReportStart = meta["report_start"]
        self._profileReportStep = meta["report_step"]

        path = build_profile_path(adjacency, self._profileReferenceNodes)
        self._profilePath = path
        self._profileDistances = cumulative_distances(path["links"], self._profileLinkLengths)

    def _profileCurrentTimeSeconds(self):
        dock = getattr(self, "ResultDockwidget", None)
        index = 0
        if dock is not None:
            with suppress(Exception):
                index = max(0, dock.cbTimes.currentIndex())
        report_start = getattr(self, "_profileReportStart", 0)
        report_step = getattr(self, "_profileReportStep", 3600)
        return report_start + index * report_step

    def _profileNodeValues(self, key):
        if key == "Elevation":
            return dict(getattr(self, "_profileNodeElev", {}))
        from ..ui.analysis.qgisred_results_binary import getOut_TimeNodesProperties

        data = getOut_TimeNodesProperties(self._outFilePath(), self._profileCurrentTimeSeconds())
        return {nid: props.get(key) for nid, props in data.items()}

    def _profileLinkLosses(self):
        from ..ui.analysis.qgisred_results_binary import getOut_TimeLinksProperties

        data = getOut_TimeLinksProperties(self._outFilePath(), self._profileCurrentTimeSeconds())
        return {lid: (props.get("HeadLoss") or 0.0) for lid, props in data.items()}

    def _redrawProfile(self):
        dock = getattr(self, "profileDock", None)
        path = getattr(self, "_profilePath", None)
        if dock is None:
            return
        if not path or not path["nodes"]:
            dock.clearPlot()
            self._drawProfileHighlight()
            return

        nodes = path["nodes"]
        links = path["links"]
        is_reference = path["is_reference"]
        distances = self._profileDistances
        reference_indices = {i for i, r in enumerate(is_reference) if r}
        key = dock.currentVariableKey()

        series = []
        if key == "HeadLoss":
            losses = self._profileLinkLosses()
            values = cumulative_link_losses(links, losses)
            points = [(distances[i], values[i]) for i in range(len(nodes))]
            series.append({
                "label": self.tr("Accumulated head loss"),
                "points": points,
                "reference_indices": reference_indices,
            })
            y_label = self.tr("Accumulated head loss")
        else:
            node_values = self._profileNodeValues(key)
            samples = sample_node_variable(nodes, distances, node_values, is_reference)
            points = [(s["distance"], s["value"]) for s in samples]
            series.append({
                "label": self.tr(self._profileVariableLabel(key)),
                "points": points,
                "reference_indices": reference_indices,
            })
            if key == "Head":
                from qgis.PyQt.QtGui import QColor

                elevation_samples = sample_node_variable(
                    nodes, distances, getattr(self, "_profileNodeElev", {}), is_reference
                )
                elevation_points = [(s["distance"], s["value"]) for s in elevation_samples]
                series.append({
                    "label": self.tr("Elevation"),
                    "points": elevation_points,
                    "reference_indices": reference_indices,
                    "color": QColor(140, 100, 60),
                })
            y_label = self.tr(self._profileVariableLabel(key))

        dock.setSeries(series, self.tr("Longitudinal profile"), self.tr("Distance"), y_label)
        self._drawProfileHighlight()
        with suppress(Exception):
            self._applyProfileSymbols(dock, nodes, links)

    def _profileVariableLabel(self, key):
        return {
            "Elevation": "Elevation",
            "Head": "Head",
            "Pressure": "Pressure",
            "Quality": "Quality",
            "HeadLoss": "Accumulated head loss",
        }.get(key, key)

    def _drawProfileHighlight(self):
        from qgis.gui import QgsRubberBand, QgsVertexMarker
        from qgis.core import Qgis, QgsGeometry, QgsPointXY
        from qgis.PyQt.QtGui import QColor

        self._clearProfileHighlight()
        path = getattr(self, "_profilePath", None)
        if not path or not path["nodes"]:
            return

        canvas = self.iface.mapCanvas()
        link_ids = set(path["links"])
        if link_ids:
            band = QgsRubberBand(canvas, Qgis.GeometryType.Line)
            band.setColor(QColor(214, 39, 40, 200))
            band.setWidth(3)
            for identifier in _LINK_LAYER_IDENTIFIERS:
                layer = self._profileLayerByIdentifier(identifier)
                if layer is None:
                    continue
                for feature in layer.getFeatures():
                    if str(feature.attribute("ID")) in link_ids:
                        band.addGeometry(feature.geometry(), layer)
            self._profileHighlights.append(band)

        reference_ids = {
            path["nodes"][i] for i in range(len(path["nodes"])) if path["is_reference"][i]
        }
        node_geoms = self._profileNodeGeometries(reference_ids)
        for geom in node_geoms:
            marker = QgsVertexMarker(canvas)
            marker.setColor(QColor(31, 119, 180))
            marker.setIconSize(12)
            marker.setIconType(QgsVertexMarker.ICON_BOX)
            marker.setPenWidth(3)
            marker.setCenter(QgsPointXY(geom.asPoint()))
            self._profileMarkers.append(marker)

    def _profileNodeGeometries(self, node_ids):
        geoms = []
        remaining = set(node_ids)
        for identifier in _NODE_LAYER_IDENTIFIERS:
            if not remaining:
                break
            layer = self._profileLayerByIdentifier(identifier)
            if layer is None:
                continue
            for feature in layer.getFeatures():
                fid = str(feature.attribute("ID"))
                if fid in remaining:
                    geoms.append(feature.geometry())
                    remaining.discard(fid)
        return geoms

    def _clearProfileHighlight(self):
        for band in getattr(self, "_profileHighlights", []) or []:
            with suppress(Exception):
                band.reset()
                self.iface.mapCanvas().scene().removeItem(band)
        for marker in getattr(self, "_profileMarkers", []) or []:
            with suppress(Exception):
                self.iface.mapCanvas().scene().removeItem(marker)
        self._profileHighlights = []
        self._profileMarkers = []
