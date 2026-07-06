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
        self.profileDock.setPickActive(True)
        self.runProfilePickTool()

    def _initProfileDock(self):
        if getattr(self, "profileDock", None) is not None:
            return
        from ..ui.analysis.qgisred_profile_dock import QGISRedProfileDock
        from qgis.PyQt.QtCore import Qt

        self.profileDock = QGISRedProfileDock(self.iface)
        self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.profileDock)
        self.profileDock.pickPathRequested.connect(self._onProfilePickRequested)
        self.profileDock.pickPathCancelled.connect(self._onProfilePickCancelled)
        self.profileDock.clearRequested.connect(self._onProfileClearRequested)
        self.profileDock.variableChanged.connect(self._onProfileVariableChanged)
        self.profileDock.visibilityChanged.connect(self._onProfileDockVisibility)
        with suppress(Exception):
            self._initResultsDock()
            self.ResultDockwidget.timeTextChanged.connect(self._onProfileTimeChanged)
        self._profileReferenceNodes = getattr(self, "_profileReferenceNodes", [])
        self._profileHighlights = []
        self._profileMarkers = []

    def runProfilePickTool(self):
        from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType

        self.myMapTools["Profile"] = QGISRedSelectPointTool(
            None, self, self.profilePickCallback, SelectPointType.Point,
            cursor=":/images/iconProfile.svg",
        )
        self.iface.mapCanvas().setMapTool(self.myMapTools["Profile"])

    def _deactivateProfileMapTool(self):
        tool = getattr(self, "myMapTools", {}).get("Profile")
        if tool is not None and self.iface.mapCanvas().mapTool() is tool:
            self.iface.mapCanvas().unsetMapTool(tool)

    def _onProfilePickRequested(self):
        self.runProfilePickTool()

    def _onProfilePickCancelled(self):
        self._deactivateProfileMapTool()

    def _onProfileClearRequested(self):
        self._profileReferenceNodes = []
        self._profilePath = None
        self._clearProfileHighlight()
        if getattr(self, "profileDock", None) is not None:
            self.profileDock.clearPlot()

    def _onProfileVariableChanged(self, _key):
        self._redrawProfile()

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
