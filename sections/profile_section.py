# -*- coding: utf-8 -*-
"""Longitudinal profiles section for QGISRed."""

import os
from contextlib import suppress

from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils
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
    flow_direction_along_path,
    envelope_points,
    node_distance,
)
from ..tools.utils.qgisred_profile_plot_utils import (
    format_profile_value,
    profile_variable_color_hex,
    label_with_unit,
    joined_labels,
    PROFILE_VARIABLE_UNIT_FIELDS,
    PROFILE_DISTANCE_UNIT_FIELD,
    MAIN_PATH_KEY,
)

_NODE_LAYER_IDENTIFIERS = ("qgisred_junctions", "qgisred_tanks", "qgisred_reservoirs")
_LINK_LAYER_IDENTIFIERS = ("qgisred_pipes", "qgisred_pumps", "qgisred_valves")

_PATH_HIGHLIGHT_RGB = (0, 184, 196)


class ProfileState:
    def __init__(self):
        self.reference_nodes = []
        self.path = None
        self.branches = []
        self.current_branch = None
        self.distances = []
        self.adjacency = None
        self.link_lengths = {}
        self.node_elev = {}
        self.node_types = {}
        self.link_types = {}
        self.link_endpoints = {}
        self.report_start = 0
        self.report_step = 3600
        self.stat_cache = None
        self.show_symbols = False
        self.envelope_mode = "off"
        self.highlights = []
        self.markers = []
        self.dock = None


_PROFILE_STATE_FIELDS = {
    "_profileReferenceNodes": "reference_nodes",
    "_profilePath": "path",
    "_profileBranches": "branches",
    "_profileCurrentBranch": "current_branch",
    "_profileDistances": "distances",
    "_profileAdjacency": "adjacency",
    "_profileLinkLengths": "link_lengths",
    "_profileNodeElev": "node_elev",
    "_profileNodeTypes": "node_types",
    "_profileLinkTypes": "link_types",
    "_profileLinkEndpoints": "link_endpoints",
    "_profileReportStart": "report_start",
    "_profileReportStep": "report_step",
    "_profileStatCache": "stat_cache",
    "_profileShowSymbols": "show_symbols",
    "_profileEnvelopeMode": "envelope_mode",
    "_profileHighlights": "highlights",
    "_profileMarkers": "markers",
}


def _profile_state_property(field):
    def getter(self):
        state = getattr(self, "_activeProfile", None)
        if state is None:
            return getattr(ProfileState(), field)
        return getattr(state, field)

    def setter(self, value):
        state = getattr(self, "_activeProfile", None)
        if state is not None:
            setattr(state, field, value)

    return property(getter, setter)


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

        if not getattr(self, "_profiles", None):
            self._createProfilePanel(out_path)
        else:
            dock = self._activeDock() or self._profiles[0].dock
            self._activateProfile(dock)
            dock.show()
            dock.raise_()
            dock.setEditMode(True)
            self._drawProfileHighlight()

    def newProfilePanel(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        out_path = self._outFilePath()
        if not os.path.exists(out_path):
            self.pushMessage(self.tr("Run a simulation first to build a longitudinal profile."), level=1)
            return
        self._createProfilePanel(out_path)

    def _createProfilePanel(self, out_path):
        from ..ui.analysis.qgisred_profile_dock import QGISRedProfileDock
        from qgis.PyQt.QtCore import Qt
        from qgis.PyQt.QtWidgets import QApplication

        if not isinstance(getattr(self, "_profiles", None), list):
            self._profiles = []
        state = ProfileState()
        dock = QGISRedProfileDock(self.iface)
        self._profileDockCounter = int(getattr(self, "_profileDockCounter", 0)) + 1
        counter = self._profileDockCounter
        base_title = dock.windowTitle() or self.tr("QGISRed: Longitudinal profile")
        dock.setWindowTitle("%s %d" % (base_title, counter))
        dock.setObjectName("QGISRedProfileDock%d" % counter)
        dock._state = state
        state.dock = dock
        self._profiles.append(state)

        self._wireProfileDock(dock)
        dock.destroyed.connect(self._onProfileDockDestroyed)
        with suppress(Exception):
            base = os.path.splitext(os.path.basename(out_path))[0]
            dock._defaultConfigPath = os.path.join(
                os.path.dirname(out_path), base + "_Profile_Config.cfg")
        with suppress(Exception):
            self._initResultsDock()
            if not getattr(self, "_profileTimeConnected", False):
                self.ResultDockwidget.timeTextChanged.connect(self._onProfileTimeChanged)
                with suppress(Exception):
                    self.ResultDockwidget.resultPropertyChanged.connect(self._onProfileTimeChanged)
                self._profileTimeConnected = True
        if not getattr(self, "_profileFocusConnected", False):
            with suppress(Exception):
                QApplication.instance().focusChanged.connect(self._onProfilePanelFocusChanged)
                self._profileFocusConnected = True

        self._setActiveProfileDock(dock)
        with suppress(Exception):
            dock.setQualityDisplayName(self._profileQualityLabel())
        self.iface.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)
        dock.clearPlot()
        dock.show()
        dock.raise_()
        dock.setEditMode(True)

    def _wireProfileDock(self, dock):
        dock.editModeToggled.connect(lambda on, d=dock: self._onProfileEditToggled(d, on))
        dock.clearRequested.connect(lambda d=dock: self._onProfileClearRequested(d))
        dock.variableChanged.connect(lambda key, d=dock: self._onProfileVariableChanged(d, key))
        dock.secondaryVariableChanged.connect(lambda key, d=dock: self._onProfileVariableChanged(d, key))
        dock.symbolsToggled.connect(lambda checked, d=dock: self._onProfileSymbolsToggled(d, checked))
        dock.envelopeModeChanged.connect(lambda mode, d=dock: self._onProfileEnvelopeModeChanged(d, mode))
        dock.exportConfigRequested.connect(lambda path, d=dock: self._onProfileExportConfig(d, path))
        dock.importConfigRequested.connect(lambda path, d=dock: self._onProfileImportConfig(d, path))
        dock.newPanelRequested.connect(self.newProfilePanel)
        dock.curveDeleteRequested.connect(lambda label, d=dock: self._onProfileCurveDelete(d, label))
        dock.plot.cursorNodeIdChanged.connect(lambda nid, d=dock: self._onProfileHoverNodeId(d, nid))
        dock.activated.connect(lambda d=dock: self._onProfileDockActivated(d))
        dock.visibilityChanged.connect(lambda vis, d=dock: self._onProfileDockVisibility(d, vis))

    def _setActiveProfileDock(self, dock):
        state = getattr(dock, "_state", None)
        if state is None or getattr(self, "_activeProfile", None) is state:
            return
        self._activeProfile = state
        self._restyleProfileDocks()

    def _activateProfile(self, dock):
        self._setActiveProfileDock(dock)

    def _activeDock(self):
        state = getattr(self, "_activeProfile", None)
        return state.dock if state is not None else None

    def _syncActiveProfileToVisible(self):
        active = getattr(self, "_activeProfile", None)
        if active is not None and active.dock is not None:
            with suppress(Exception):
                if active.dock.isVisible() and not active.dock.visibleRegion().isEmpty():
                    return
        for state in getattr(self, "_profiles", []) or []:
            dock = state.dock
            if dock is None:
                continue
            with suppress(Exception):
                if dock.isVisible() and not dock.visibleRegion().isEmpty():
                    self._setActiveProfileDock(dock)
                    return

    def _restyleProfileDocks(self):
        from ..tools.utils.qgisred_ui_utils import QGISRedUIUtils

        active_dock = self._activeDock()
        ceded = getattr(self, "_profileFocusCeded", False)
        docks = [s.dock for s in (getattr(self, "_profiles", []) or []) if s.dock is not None]
        multiple = len(docks) > 1
        for dock in docks:
            is_active = (not ceded) and (dock is active_dock or not multiple)
            with suppress(Exception):
                accent = "#00838F" if is_active else "#B0BEC5"
                QGISRedUIUtils.applyDockStyle(dock, accent, backgroundColor="white")

    def _onProfileDockActivated(self, dock):
        if dock is None:
            return
        ceded = getattr(self, "_profileFocusCeded", False)
        if self._activeDock() is dock and not ceded:
            return
        with suppress(Exception):
            self._cedeTimeSeriesFocus()
        self._setActiveProfileDock(dock)
        if ceded:
            self._profileFocusCeded = False
            self._restyleProfileDocks()
            self._redrawAllProfileHighlights()
        self._rearmProfileMapTool(dock)

    def _widgetBelongsToProfileDock(self, widget, dock):
        if widget is None or dock is None:
            return False
        try:
            return widget is dock or dock.isAncestorOf(widget)
        except Exception:
            return False

    def _onProfilePanelFocusChanged(self, old, now):
        if now is None:
            return
        for state in getattr(self, "_profiles", None) or []:
            dock = state.dock
            if dock is not None and self._widgetBelongsToProfileDock(now, dock):
                self._onProfileDockActivated(dock)
                return
        if self._focusInTimeSeries(now):
            self._cedeProfileFocus()

    def _focusInTimeSeries(self, widget):
        for dock in (getattr(self, "timeSeriesDocks", None) or []):
            if dock is not None and self._widgetBelongsToProfileDock(widget, dock):
                return True
        return False

    def _cedeProfileFocus(self):
        if getattr(self, "_profileFocusCeded", False) or not getattr(self, "_profiles", None):
            return
        self._profileFocusCeded = True
        self._deactivateProfileMapTool()
        self._clearProfileMapHover()
        for state in list(self._profiles):
            self._clearHighlightForState(state)
        self._restyleProfileDocks()

    def _redrawAllProfileHighlights(self):
        saved = getattr(self, "_activeProfile", None)
        for state in list(getattr(self, "_profiles", []) or []):
            self._activeProfile = state
            with suppress(Exception):
                self._drawProfileHighlight()
        self._activeProfile = saved

    def _rearmProfileMapTool(self, dock):
        with suppress(Exception):
            self._onProfileEditToggled(dock, dock.isEditMode())

    def _clearHighlightForState(self, state):
        if state is None:
            return
        for band in state.highlights or []:
            with suppress(Exception):
                band.reset()
                self.iface.mapCanvas().scene().removeItem(band)
        for marker in state.markers or []:
            with suppress(Exception):
                self.iface.mapCanvas().scene().removeItem(marker)
        state.highlights = []
        state.markers = []

    def _onProfileDockDestroyed(self, obj=None):
        states = list(getattr(self, "_profiles", []) or [])
        gone = next((s for s in states if s.dock is obj), None)
        self._clearHighlightForState(gone)
        remaining = [s for s in states if s.dock is not obj]
        self._profiles = remaining
        active = getattr(self, "_activeProfile", None)
        if active is None or active is gone or active not in remaining:
            self._activeProfile = remaining[-1] if remaining else None
        self._restyleProfileDocks()

    def _setProfileMapTool(self, kind, callback, context_callback=None):
        from ..tools.map_tools.qgisred_selectPoint import QGISRedSelectPointTool, SelectPointType

        self._deactivateProfileMapTool()
        point_type = SelectPointType.TwoPoints if kind == "two" else SelectPointType.Point
        self.myMapTools["Profile"] = QGISRedSelectPointTool(
            None, self, callback, point_type, cursor=":/images/iconProfile.svg",
            move_callback=self._profileHoverOnMap, context_callback=context_callback,
        )
        self.iface.mapCanvas().setMapTool(self.myMapTools["Profile"])

    def _deactivateProfileMapTool(self):
        tool = getattr(self, "myMapTools", {}).get("Profile")
        if tool is not None and self.iface.mapCanvas().mapTool() is tool:
            self.iface.mapCanvas().unsetMapTool(tool)

    def _profileHoverOnMap(self, point):
        dock = self._activeDock()
        if dock is None:
            return
        node_id = None
        with suppress(Exception):
            node_id = self._resolveProfileNode(point)
        self._showProfileMapHover(node_id)
        distance = self._profileNodeTreeDistance(node_id) if node_id else None
        with suppress(Exception):
            dock.plot.setCursorDistance(distance, node_id)

    def _onProfileHoverNodeId(self, dock, node_id):
        self._activateProfile(dock)
        self._showProfileMapHover(node_id if node_id else None, from_chart=True)

    def _showProfileMapHover(self, node_id, from_chart=False):
        if (node_id == getattr(self, "_profileHoverNodeId", None)
                and from_chart == getattr(self, "_profileHoverFromChart", False)):
            return
        self._clearProfileMapHover()
        if not node_id:
            return
        geoms = self._profileNodeGeometries({node_id})
        if not geoms:
            return
        with suppress(Exception):
            from qgis.gui import QgsVertexMarker
            from qgis.core import QgsPointXY
            from qgis.PyQt.QtGui import QColor

            marker = QgsVertexMarker(self.iface.mapCanvas())
            if from_chart:
                marker.setColor(QColor(25, 118, 210))
                marker.setPenWidth(2)
            else:
                marker.setColor(QColor(255, 127, 0))
                marker.setPenWidth(3)
            marker.setIconSize(20)
            marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            marker.setCenter(QgsPointXY(geoms[0].asPoint()))
            self._profileHoverMarker = marker
            self._profileHoverNodeId = node_id
            self._profileHoverFromChart = from_chart

    def _clearProfileMapHover(self):
        marker = getattr(self, "_profileHoverMarker", None)
        if marker is not None:
            with suppress(Exception):
                self.iface.mapCanvas().scene().removeItem(marker)
            self._profileHoverMarker = None
        self._profileHoverNodeId = None

    def _onProfileEditToggled(self, dock, on):
        self._activateProfile(dock)
        self._deactivateProfileMapTool()
        self._profileEditSeq = None
        self._profileExtendAtStart = False
        self._profileMoveSource = None
        self._profileCurrentBranch = None
        if on:
            if not (getattr(self, "_profileReferenceNodes", []) or []):
                self._profileEditSeq = "main"
            self._setProfileMapTool("one", self._profileEditLeftClick, self._profileEditRightClick)
        else:
            self._setProfileMapTool("one", self._profileTrackingClick, self._profileTrackingContext)

    def _profileTrackingClick(self, _point):
        self._syncActiveProfileToVisible()

    def _profileTrackingContext(self, _point):
        return

    def _onProfileClearRequested(self, dock):
        self._activateProfile(dock)
        self._profileReferenceNodes = []
        self._profilePath = None
        self._profileBranches = []
        self._profileCurrentBranch = None
        self._profileShowSymbols = False
        self._profileEnvelopeMode = "off"
        self._clearProfileHighlight()
        dock.clearPlot()
        dock.resetControls()
        self._onProfileEditToggled(dock, dock.isEditMode())

    def _onProfileVariableChanged(self, dock, _key):
        self._activateProfile(dock)
        self._redrawProfile()

    def _onProfileEnvelopeModeChanged(self, dock, mode):
        self._activateProfile(dock)
        self._profileEnvelopeMode = mode or "off"
        self._redrawProfile()

    def _profileStats(self):
        cache = getattr(self, "_profileStatCache", None)
        if cache is not None:
            return cache
        from ..ui.analysis.qgisred_results_binary import getOut_StatNodesProperties

        out_path = self._outFilePath()
        cache = (
            getOut_StatNodesProperties(out_path, "Maximum"),
            getOut_StatNodesProperties(out_path, "Minimum"),
        )
        self._profileStatCache = cache
        return cache

    def _profileEnvelopeActive(self, key):
        mode = getattr(self, "_profileEnvelopeMode", "off")
        return mode != "off" and key in ("Head", "Pressure", "Quality")

    def _applyProfileEnvelope(self, dock, key, nodes, distances):
        if not self._profileEnvelopeActive(key):
            dock.clearEnvelope()
            return
        stat_max, stat_min = self._profileStats()
        max_points, min_points = envelope_points(nodes, distances, stat_max, stat_min, key)
        labels = {
            "max": self.tr("Maxima"),
            "min": self.tr("Minima"),
            "band": self.tr("Envelope"),
        }
        dock.setEnvelope(max_points, min_points, self._profileEnvelopeMode, labels)

    def _profileStableSegments(self, include_branches):
        segments = []
        main = getattr(self, "_profilePath", None)
        if main and main["nodes"]:
            segments.append((main["nodes"], self._profileDistances))
        if include_branches:
            for branch in getattr(self, "_profileBranches", []) or []:
                branch_path = branch.get("path")
                if branch_path and branch_path["nodes"]:
                    segments.append((branch_path["nodes"], branch["distances"]))
        return segments

    def _profileStableAxisPoints(self, key, segments):
        if key not in ("Head", "Pressure", "Quality"):
            return None
        stat_max, stat_min = self._profileStats()
        points = []
        for seg_nodes, seg_distances in segments:
            max_points, min_points = envelope_points(seg_nodes, seg_distances, stat_max, stat_min, key)
            points.extend((d, v) for d, v in max_points if v is not None)
            points.extend((d, v) for d, v in min_points if v is not None)
        return points or None

    def _applyProfileStableRanges(self, dock, key, secondary_key):
        left_segments = self._profileStableSegments(include_branches=True)
        left = self._profileStableAxisPoints(key, left_segments) or []
        if key == "Head":
            elev = getattr(self, "_profileNodeElev", {})
            for seg_nodes, seg_distances in left_segments:
                for i, node in enumerate(seg_nodes):
                    value = elev.get(node)
                    if value is not None:
                        left.append((seg_distances[i], float(value)))
        right = None
        if secondary_key and secondary_key != key:
            right = self._profileStableAxisPoints(
                secondary_key, self._profileStableSegments(include_branches=False))
        dock.setStableRanges(left or None, right)

    def _onProfileSymbolsToggled(self, dock, checked):
        self._activateProfile(dock)
        self._profileShowSymbols = bool(checked)
        self._redrawProfile()

    def _profileLinkFlows(self):
        return {lid: props.get("Flow") for lid, props in self._profileLinkProperties().items()}

    def _applyProfileSymbols(self, dock, nodes, links):
        if not getattr(self, "_profileShowSymbols", False):
            dock.clearSymbols()
            return
        symbols = {MAIN_PATH_KEY: self._profilePathSymbols(nodes, links)}
        for i, branch in enumerate(getattr(self, "_profileBranches", []) or []):
            branch_path = branch.get("path")
            if branch_path and branch_path["nodes"]:
                symbols["branch_{}".format(i)] = self._profilePathSymbols(
                    branch_path["nodes"], branch_path["links"])
        dock.setSymbols(symbols)

    def _profilePathSymbols(self, nodes, links):
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
        return {"nodes": node_kinds, "links": link_info}

    def _onProfileTimeChanged(self, _text=None):
        saved = getattr(self, "_activeProfile", None)
        for state in list(getattr(self, "_profiles", []) or []):
            self._activeProfile = state
            self._redrawProfile()
        self._activeProfile = saved

    def _onProfileDockVisibility(self, dock, visible):
        state = getattr(dock, "_state", None)
        if state is None:
            return
        if not visible:
            if self._activeDock() is dock:
                self._deactivateProfileMapTool()
            self._clearHighlightForState(state)
            self._clearProfileMapHover()
        else:
            self._setActiveProfileDock(dock)
            with suppress(Exception):
                self._drawProfileHighlight()

    def _onProfileExportConfig(self, dock, path):
        from ..ui.analysis.profile_config_io import write_profile_config

        self._activateProfile(dock)
        if dock is None or not path:
            return
        plot = dock.plot
        profile = {
            "variable": dock.currentVariableKey(),
            "secondary_variable": dock.currentSecondaryVariableKey(),
            "reference_nodes": list(getattr(self, "_profileReferenceNodes", []) or []),
            "branches": [
                {"reference_nodes": list(b.get("reference_nodes", []) or []), "offset": b.get("offset", 0.0)}
                for b in (getattr(self, "_profileBranches", []) or [])
            ],
            "options": {
                "show_symbols": bool(getattr(self, "_profileShowSymbols", False)),
                "show_labels": bool(dock.btnLabels.isChecked()),
                "envelope_mode": getattr(self, "_profileEnvelopeMode", "off"),
            },
        }
        try:
            write_profile_config(
                path, profile, plot._axis_cfg_x, plot._axis_cfg_y,
                plot._general_cfg, plot._curve_overrides, comment=dock.comment(),
                axis_y_right=plot._axis_cfg_y_right)
        except Exception:
            self.pushMessage(self.tr("The profile configuration could not be exported."), level=2)
            return
        self.pushMessage(self.tr("Profile configuration exported."), level=3)

    def _onProfileImportConfig(self, dock, path):
        from ..ui.analysis.profile_config_io import read_profile_config
        from ..ui.analysis.profile_chart_settings import clone_axis, clone_general

        self._activateProfile(dock)
        if dock is None or not path:
            return
        try:
            config = read_profile_config(path)
        except Exception:
            self.pushMessage(self.tr("The profile configuration could not be imported."), level=2)
            return

        dock.setVariableKey(config.get("variable") or "Head")
        dock.setSecondaryVariableKey(config.get("secondary_variable") or "")
        self._profileReferenceNodes = list(config.get("reference_nodes", []) or [])
        self._profileBranches = []
        self._profileCurrentBranch = None
        self._profileStatCache = None

        try:
            self._recomputeProfileStructure()
        except ProfilePathError:
            self.pushMessage(self.tr("The saved profile does not match the current network."), level=2)
            return

        for branch_cfg in config.get("branches", []) or []:
            refs = list(branch_cfg.get("reference_nodes", []) or [])
            if len(refs) < 2:
                continue
            offset = self._profileNodeTreeDistance(refs[0])
            if offset is None:
                offset = branch_cfg.get("offset", 0.0)
            branch = {"reference_nodes": refs, "offset": offset, "path": None, "distances": None}
            with suppress(ProfilePathError):
                self._recomputeBranch(branch)
                self._profileBranches.append(branch)

        plot = dock.plot
        plot._axis_cfg_x = clone_axis(config["axis_x"])
        plot._axis_cfg_y = clone_axis(config["axis_y"])
        with suppress(Exception):
            plot._axis_cfg_y_right = clone_axis(config["axis_y_right"])
        plot._general_cfg = clone_general(config["general"])
        plot._curve_overrides = config.get("curve_overrides", {}) or {}

        options = config.get("options", {}) or {}
        self._profileShowSymbols = bool(options.get("show_symbols"))
        self._profileEnvelopeMode = options.get("envelope_mode", "off") or "off"
        dock.setComment(config.get("comment", ""))
        dock.setSymbolsChecked(self._profileShowSymbols)
        dock.setLabelsChecked(bool(options.get("show_labels")))
        dock.setEnvelopeModeState(self._profileEnvelopeMode)

        self._redrawProfile()
        self.pushMessage(self.tr("Profile configuration imported."), level=3)

    def _profileEditLeftClick(self, point):
        self._syncActiveProfileToVisible()
        node_id = self._resolveProfileNode(point)
        if node_id is None:
            self.pushMessage(self.tr("No network node found at this location."), level=1)
            return
        seq = getattr(self, "_profileEditSeq", None)
        if seq == "move":
            source = getattr(self, "_profileMoveSource", None)
            self._profileMoveSource = None
            self._profileEditSeq = None
            if source is not None and source != node_id:
                self._applyProfileMove(source, node_id)
            return
        if seq == "branch":
            self._profileAppendBranchNode(node_id)
            return
        if seq == "main":
            self._profileAppendMainNode(node_id)

    def _profileEditRightClick(self, point):
        self._syncActiveProfileToVisible()
        seq = getattr(self, "_profileEditSeq", None)
        if seq == "move":
            self._profileMoveSource = None
            self._profileEditSeq = None
            return
        if self._profileSequenceHasNodes(seq):
            self._profileFinishSequence()
            return
        node_id = self._resolveProfileNode(point) if point is not None else None
        self._profileShowContextMenu(node_id)

    def _profileSequenceHasNodes(self, seq):
        if seq == "main":
            return bool(getattr(self, "_profileReferenceNodes", []) or [])
        if seq == "branch":
            return getattr(self, "_profileCurrentBranch", None) is not None
        return False

    def _profileShowContextMenu(self, node_id):
        from qgis.PyQt.QtWidgets import QMenu
        from qgis.PyQt.QtGui import QCursor

        role = self._profileClassifyNode(node_id)
        if not role:
            return
        entries = self._profileMenuEntries(role, node_id)
        if not entries:
            return
        menu = QMenu()
        mapping = {}
        for label, handler in entries:
            action = menu.addAction(label)
            mapping[action] = handler
        chosen = menu.exec(QCursor.pos())
        if chosen is not None and chosen in mapping:
            mapping[chosen]()

    def _profileMenuEntries(self, role, node_id):
        extend = (self.tr("Extend path"), lambda: self._profileStartExtend(node_id))
        branch = (self.tr("Create branch"), lambda: self._profileStartBranch(node_id))
        declare = (self.tr("Declare pass node"), lambda: self._profileDeclarePoint(node_id))
        move = (self.tr("Move pass node"), lambda: self._profileStartMove(node_id))
        remove = (self.tr("Delete pass node"), lambda: self._profileRemovePoint(node_id))
        start = (self.tr("Start new path here"), lambda: self._profileStartMain(node_id))
        return {
            "start": [start],
            "intermediate_path": [declare],
            "origin": [extend, branch],
            "terminal": [extend, branch, move, remove],
            "through": [branch, move, remove],
            "bifurcation": [branch],
        }.get(role, [])

    def _profileClassifyNode(self, node_id):
        main = getattr(self, "_profilePath", None)
        tree_exists = bool(main and main["nodes"])
        if not tree_exists:
            return "start" if node_id else None
        if not node_id:
            return None
        path_target, _pb = self._profileTargetForNode(node_id, "path")
        if path_target is None:
            return None
        declared_target, _db = self._profileTargetForNode(node_id, "declared")
        if declared_target is None:
            return "intermediate_path"
        if node_id == main["nodes"][0]:
            return "origin"
        if self._isBranchOrigin(node_id):
            return "bifurcation"
        if self._profileIsTerminalWaypoint(node_id):
            return "terminal"
        return "through"

    def _profileIsTerminalWaypoint(self, node_id):
        main = getattr(self, "_profilePath", None)
        if main and main["nodes"]:
            if node_id == main["nodes"][-1] and node_id != main["nodes"][0]:
                return True
        for branch in getattr(self, "_profileBranches", []) or []:
            branch_path = branch.get("path")
            if branch_path and branch_path["nodes"] and node_id == branch_path["nodes"][-1]:
                return True
        return False

    def _profileStartMain(self, node_id):
        self._profileEditSeq = "main"
        self._profileExtendAtStart = False
        self.pushMessage(self.tr("Click nodes to trace the path; right-click to finish."), level=3)
        self._profileAppendMainNode(node_id)

    def _profileStartExtend(self, node_id):
        main = getattr(self, "_profilePath", None)
        if main and main["nodes"] and node_id in (main["nodes"][0], main["nodes"][-1]):
            self._profileEditSeq = "main"
            self._profileExtendAtStart = (node_id == main["nodes"][0])
            self.pushMessage(self.tr("Click nodes to trace the path; right-click to finish."), level=3)
            return
        for branch in getattr(self, "_profileBranches", []) or []:
            branch_path = branch.get("path")
            if branch_path and branch_path["nodes"] and node_id == branch_path["nodes"][-1]:
                self._profileCurrentBranch = branch
                self._profileEditSeq = "branch"
                self.pushMessage(self.tr("Click nodes to build the branch; right-click to finish."), level=3)
                return

    def _profileStartBranch(self, node_id):
        tree_distance = self._profileNodeTreeDistance(node_id)
        if tree_distance is None:
            return
        if not isinstance(getattr(self, "_profileBranches", None), list):
            self._profileBranches = []
        branch = {"reference_nodes": [node_id], "offset": tree_distance, "path": None, "distances": None}
        self._profileBranches.append(branch)
        self._profileCurrentBranch = branch
        self._profileEditSeq = "branch"
        with suppress(ProfilePathError):
            self._recomputeBranch(branch)
        self.pushMessage(self.tr("Click nodes to build the branch; right-click to finish."), level=3)
        self._redrawProfile()

    def _profileStartMove(self, node_id):
        self._profileEditSeq = "move"
        self._profileMoveSource = node_id
        self.pushMessage(self.tr("Click the destination node for the pass point."), level=3)

    def _profileDeclarePoint(self, node_id):
        self._applyProfileAdd(node_id)

    def _profileRemovePoint(self, node_id):
        self._applyProfileRemove(node_id)

    def _profileAppendMainNode(self, node_id):
        refs = getattr(self, "_profileReferenceNodes", []) or []
        at_start = getattr(self, "_profileExtendAtStart", False)
        if refs and (refs[0] if at_start else refs[-1]) == node_id:
            return
        if at_start:
            refs.insert(0, node_id)
        else:
            refs.append(node_id)
        self._profileReferenceNodes = refs
        try:
            self._recomputeProfileStructure()
        except ProfilePathError:
            if at_start:
                refs.pop(0)
            else:
                refs.pop()
            self._profileReferenceNodes = refs
            self.pushMessage(
                self.tr("Selected node is not connected to the previous one along the network."),
                level=1,
            )
            return
        self._redrawProfile()

    def _profileAppendBranchNode(self, node_id):
        current = getattr(self, "_profileCurrentBranch", None)
        if current is None:
            return
        current["reference_nodes"].append(node_id)
        try:
            self._recomputeBranch(current)
        except ProfilePathError:
            current["reference_nodes"].pop()
            self.pushMessage(self.tr("Selected node is not connected to the branch along the network."), level=1)
            return
        self._redrawProfile()

    def _profileFinishSequence(self):
        current = getattr(self, "_profileCurrentBranch", None)
        if current is not None and len(current.get("reference_nodes") or []) < 2:
            self._profileBranches = [
                b for b in (getattr(self, "_profileBranches", []) or []) if b is not current
            ]
        self._profileEditSeq = None
        self._profileExtendAtStart = False
        self._profileMoveSource = None
        self._profileCurrentBranch = None
        self._redrawProfile()

    def _profileNodeTreeDistance(self, node):
        main_path = getattr(self, "_profilePath", None)
        if main_path and main_path["nodes"]:
            distance = node_distance(main_path["nodes"], self._profileDistances, node)
            if distance is not None:
                return distance
        for branch in getattr(self, "_profileBranches", []) or []:
            branch_path = branch.get("path")
            if branch_path and branch_path["nodes"]:
                distance = node_distance(branch_path["nodes"], branch["distances"], node)
                if distance is not None:
                    return distance
        return None

    def _recomputeBranch(self, branch):
        self._rebuildProfilePaths()

    @staticmethod
    def _originOffset(origin, built):
        for nodes, distances in built:
            distance = node_distance(nodes, distances, origin)
            if distance is not None:
                return distance
        return None

    def _rebuildProfilePaths(self):
        adjacency = getattr(self, "_profileAdjacency", None)
        if adjacency is None:
            raise ProfilePathError("No network topology available")
        link_lengths = getattr(self, "_profileLinkLengths", {})
        main = build_profile_path(adjacency, getattr(self, "_profileReferenceNodes", []) or [])
        main_distances = cumulative_distances(main["links"], link_lengths)
        used_links = set(main["links"])
        used_nodes = set(main["nodes"])
        built = [(main["nodes"], main_distances)]
        results = []
        for branch in getattr(self, "_profileBranches", []) or []:
            refs = branch.get("reference_nodes") or []
            if not refs:
                raise ProfilePathError("Empty branch")
            origin = refs[0]
            offset = self._originOffset(origin, built)
            if offset is None:
                raise ProfilePathError("Branch origin is not on the profile")
            path = build_profile_path(
                adjacency, refs,
                excluded_links=used_links,
                excluded_nodes=used_nodes - {origin},
            )
            for node in path["nodes"]:
                if node != origin and node in used_nodes:
                    raise ProfilePathError("Branch reuses an already declared node")
            distances = [offset + d for d in cumulative_distances(path["links"], link_lengths)]
            results.append((branch, path, offset, distances))
            used_links |= set(path["links"])
            used_nodes |= set(path["nodes"])
            built.append((path["nodes"], distances))
        self._profilePath = main
        self._profileDistances = main_distances
        for branch, path, offset, distances in results:
            branch["path"] = path
            branch["offset"] = offset
            branch["distances"] = distances

    def _profileTargetForNode(self, node_id, mode):
        if mode == "declared":
            if node_id in (getattr(self, "_profileReferenceNodes", []) or []):
                return ("main", None)
            for branch in getattr(self, "_profileBranches", []) or []:
                if node_id in (branch.get("reference_nodes") or []):
                    return ("branch", branch)
        else:
            main_path = getattr(self, "_profilePath", None)
            if main_path and node_id in main_path["nodes"]:
                return ("main", None)
            for branch in getattr(self, "_profileBranches", []) or []:
                branch_path = branch.get("path")
                if branch_path and node_id in branch_path["nodes"]:
                    return ("branch", branch)
        return (None, None)

    def _applyProfileAdd(self, node_id):
        target, branch = self._profileTargetForNode(node_id, "path")
        if target == "main":
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
        elif target == "branch":
            with suppress(ProfilePathError):
                new_bp = add_pass_node(branch["path"], node_id)
                branch["path"] = new_bp
                branch["reference_nodes"] = reference_nodes_from_path(new_bp)
                local = cumulative_distances(new_bp["links"], getattr(self, "_profileLinkLengths", {}))
                branch["distances"] = [branch["offset"] + d for d in local]
                self._redrawProfile()
        else:
            self.pushMessage(self.tr("Pick an intermediate node of the current profile path."), level=1)

    def _isBranchOrigin(self, node_id):
        for b in getattr(self, "_profileBranches", []) or []:
            refs = b.get("reference_nodes") or []
            if refs and refs[0] == node_id:
                return True
        return False

    def _applyProfileRemove(self, node_id):
        if self._isBranchOrigin(node_id):
            self.pushMessage(
                self.tr("This point starts a branch and cannot be removed. Trim the branch from its far end first."),
                level=1,
            )
            return
        target, branch = self._profileTargetForNode(node_id, "declared")
        if target == "main":
            previous = list(getattr(self, "_profileReferenceNodes", []) or [])
            self._profileReferenceNodes = remove_pass_node(previous, node_id)
            try:
                self._recomputeProfileStructure()
            except ProfilePathError:
                self._profileReferenceNodes = previous
                with suppress(ProfilePathError):
                    self._recomputeProfileStructure()
                return
            self._redrawProfile()
        elif target == "branch":
            refs = list(branch.get("reference_nodes") or [])
            if len(refs) <= 2:
                self._profileBranches = [b for b in (getattr(self, "_profileBranches", []) or []) if b is not branch]
            else:
                branch["reference_nodes"] = [n for n in refs if n != node_id]
                try:
                    self._rebuildProfilePaths()
                except ProfilePathError:
                    branch["reference_nodes"] = refs
                    with suppress(ProfilePathError):
                        self._rebuildProfilePaths()
                    return
            self._redrawProfile()
        else:
            self.pushMessage(self.tr("Pick a declared profile point to remove."), level=1)

    def _applyProfileMove(self, node_id, new_node_id):
        if node_id == new_node_id:
            return
        main_refs = list(getattr(self, "_profileReferenceNodes", []) or [])
        branches = getattr(self, "_profileBranches", []) or []
        in_main = node_id in main_refs
        in_branch = any(node_id in (b.get("reference_nodes") or []) for b in branches)
        if not in_main and not in_branch:
            self.pushMessage(self.tr("Only declared profile points can be moved."), level=1)
            return

        prev_main = main_refs
        prev_branch_refs = [list(b.get("reference_nodes") or []) for b in branches]

        self._profileReferenceNodes = [new_node_id if n == node_id else n for n in main_refs]
        for b in branches:
            refs = b.get("reference_nodes") or []
            if node_id in refs:
                b["reference_nodes"] = [new_node_id if n == node_id else n for n in refs]

        try:
            self._rebuildProfilePaths()
        except ProfilePathError:
            self._profileReferenceNodes = prev_main
            for b, refs in zip(branches, prev_branch_refs):
                b["reference_nodes"] = refs
            with suppress(ProfilePathError):
                self._rebuildProfilePaths()
            self.pushMessage(
                self.tr("The point cannot be moved there without reusing already declared pipes or nodes."),
                level=1,
            )
            return
        self._redrawProfile()

    def _branchHasDerivations(self, branch):
        branch_nodes = set((branch.get("path") or {}).get("nodes") or [])
        if not branch_nodes:
            branch_nodes = set(branch.get("reference_nodes") or [])
        origin = (branch.get("reference_nodes") or [None])[0]
        branch_nodes.discard(origin)
        for other in getattr(self, "_profileBranches", []) or []:
            if other is branch:
                continue
            other_origin = (other.get("reference_nodes") or [None])[0]
            if other_origin in branch_nodes:
                return True
        return False

    def _onProfileCurveDelete(self, dock, label):
        self._activateProfile(dock)
        branches = getattr(self, "_profileBranches", []) or []
        for i in range(len(branches)):
            if label == (self.tr("Branch") + " " + str(i + 1)):
                if self._branchHasDerivations(branches[i]):
                    self.pushMessage(
                        self.tr("This branch has derivations. Remove them first from their far ends."),
                        level=1,
                    )
                    return
                self._profileBranches = [b for j, b in enumerate(branches) if j != i]
                self._redrawProfile()
                return
        sec_key = dock.currentSecondaryVariableKey()
        if sec_key and label == self._profileVariableDisplay(sec_key):
            dock.setSecondaryVariableKey("")
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
            idField = QGISRedFieldUtils().getIdFieldName(layer)
            for feature in layer.getFeatures(rect):
                return str(feature.attribute(idField))
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
        self._profileAdjacency = adjacency
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

        self._rebuildProfilePaths()

    def _profileTimeSource(self):
        source = getattr(self, "_profileSourceCache", None)
        if source is None:
            with suppress(Exception):
                source = self._getTimeSeriesSource()
            self._profileSourceCache = source
        return source

    def _profileCurrentTimeSeconds(self):
        dock = getattr(self, "ResultDockwidget", None)
        index = 0
        if dock is not None:
            with suppress(Exception):
                index = max(0, dock.cbTimes.currentIndex())
        source = self._profileTimeSource()
        if source:
            times = source.get("times") or []
            if 0 <= index < len(times):
                return times[index]
        report_start = getattr(self, "_profileReportStart", 0)
        report_step = getattr(self, "_profileReportStep", 3600)
        return report_start + index * report_step

    def _profileTimeText(self):
        dock = getattr(self, "ResultDockwidget", None)
        if dock is not None:
            with suppress(Exception):
                text = dock.cbTimes.currentText()
                if text and text.strip():
                    return text.strip()
        with suppress(Exception):
            from ..ui.analysis.qgisred_results_data import seconds_to_time_str_no_seconds
            return seconds_to_time_str_no_seconds(int(self._profileCurrentTimeSeconds()))
        return ""

    def _profileNodeValues(self, key):
        if key == "Elevation":
            return dict(getattr(self, "_profileNodeElev", {}))
        source = self._profileTimeSource()
        seconds = self._profileCurrentTimeSeconds()
        if source and source.get("kind") == "hyd":
            from ..ui.analysis.qgisred_results_hyd import getHyd_TimeNodesProperties

            data = getHyd_TimeNodesProperties(source["hyd_path"], source["out_path"], seconds)
        else:
            from ..ui.analysis.qgisred_results_binary import getOut_TimeNodesProperties

            data = getOut_TimeNodesProperties(self._outFilePath(), seconds)
        return {nid: props.get(key) for nid, props in data.items()}

    def _profileLinkProperties(self):
        source = self._profileTimeSource()
        seconds = self._profileCurrentTimeSeconds()
        if source and source.get("kind") == "hyd":
            from ..ui.analysis.qgisred_results_hyd import getHyd_TimeLinksProperties

            return getHyd_TimeLinksProperties(source["hyd_path"], source["out_path"], seconds)
        from ..ui.analysis.qgisred_results_binary import getOut_TimeLinksProperties

        return getOut_TimeLinksProperties(self._outFilePath(), seconds)

    def _profileLinkLosses(self):
        return {lid: (props.get("HeadLoss") or 0.0) for lid, props in self._profileLinkProperties().items()}

    def _redrawProfile(self):
        dock = self._activeDock()
        path = getattr(self, "_profilePath", None)
        self._profileSourceCache = None
        if dock is None:
            return
        with suppress(Exception):
            dock.setQualityDisplayName(self._profileQualityLabel())
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

        node_id_strs = [str(n) for n in nodes]
        series = []
        if key == "HeadLoss":
            losses = self._profileLinkLosses()
            values = cumulative_link_losses(links, losses)
            points = [(distances[i], values[i]) for i in range(len(nodes))]
            series.append({
                "label": self.tr("Accumulated head loss"),
                "display_label": self._profileVariableDisplayWithUnit("HeadLoss"),
                "points": points,
                "reference_indices": reference_indices,
                "node_ids": node_id_strs,
                "color": self._profileVariableColor("HeadLoss"),
                "fill": False,
                "symbols_mode": "full",
            })
            y_label = self._profileVariableDisplayWithUnit("HeadLoss")
        else:
            node_values = self._profileNodeValues(key)
            samples = sample_node_variable(nodes, distances, node_values, is_reference)
            points = [(s["distance"], s["value"]) for s in samples]
            series.append({
                "label": self._profileVariableDisplay(key),
                "display_label": self._profileVariableDisplayWithUnit(key),
                "points": points,
                "reference_indices": reference_indices,
                "node_ids": node_id_strs,
                "color": self._profileVariableColor(key),
                "fill": key == "Elevation",
                "symbols_mode": "full",
            })
            if key == "Head":
                elevation_samples = sample_node_variable(
                    nodes, distances, getattr(self, "_profileNodeElev", {}), is_reference
                )
                elevation_points = [(s["distance"], s["value"]) for s in elevation_samples]
                series.append({
                    "label": self.tr("Elevation"),
                    "display_label": self._profileVariableDisplayWithUnit("Elevation"),
                    "points": elevation_points,
                    "reference_indices": reference_indices,
                    "node_ids": node_id_strs,
                    "color": self._profileVariableColor("Elevation"),
                })
                y_label = label_with_unit(
                    joined_labels([
                        self._profileVariableDisplay("Elevation"),
                        self._profileVariableDisplay("Head"),
                    ]),
                    self._profileVariableUnit("Head"),
                )
            else:
                y_label = self._profileVariableDisplayWithUnit(key)

        secondary_key = dock.currentSecondaryVariableKey()
        y_right_label = ""
        if secondary_key and secondary_key != key and not (key == "Head" and secondary_key == "Elevation"):
            with suppress(Exception):
                sec_points = self._profileVariablePoints(secondary_key, nodes, links, distances, is_reference)
                series.append({
                    "label": self._profileVariableDisplay(secondary_key),
                    "display_label": self._profileVariableDisplayWithUnit(secondary_key),
                    "points": sec_points,
                    "reference_indices": reference_indices,
                    "node_ids": node_id_strs,
                    "color": self._profileVariableColor(secondary_key),
                    "y_axis": "right",
                    "fill": False,
                    "deletable": True,
                    "symbols_mode": "arrows",
                })
                y_right_label = self._profileVariableDisplayWithUnit(secondary_key)

        with suppress(Exception):
            self._pushProfileTable(dock, series, nodes, distances, key)
        for s in series:
            s["path_key"] = MAIN_PATH_KEY
            s["path_label"] = self.tr("Main path")
        with suppress(Exception):
            self._appendProfileBranchSeries(series, key)
        time_text = self._profileTimeText()
        if time_text:
            title = self.tr("Longitudinal profiles at {0}").format(time_text)
        else:
            title = self.tr("Longitudinal profiles")
        dock.setSeries(series, title, self._profileDistanceDisplay(), y_label, y_right_label)
        self._drawProfileHighlight()
        with suppress(Exception):
            self._applyProfileStableRanges(dock, key, secondary_key)
        with suppress(Exception):
            self._applyProfileEnvelope(dock, key, nodes, distances)
        with suppress(Exception):
            self._applyProfileSymbols(dock, nodes, links)

    def _profileVariablePoints(self, key, nodes, links, distances, is_reference):
        if key == "HeadLoss":
            losses = self._profileLinkLosses()
            values = cumulative_link_losses(links, losses)
            return [(distances[i], values[i]) for i in range(len(nodes))]
        node_values = self._profileNodeValues(key)
        samples = sample_node_variable(nodes, distances, node_values, is_reference)
        return [(s["distance"], s["value"]) for s in samples]

    def _profileVariableLabel(self, key):
        return {
            "Elevation": "Elevation",
            "Head": "Head",
            "Pressure": "Pressure",
            "Quality": "Quality",
            "HeadLoss": "Accumulated head loss",
        }.get(key, key)

    def _profileQualityLabel(self):
        dock = getattr(self, "ResultDockwidget", None)
        with suppress(Exception):
            name = getattr(dock, "lbl_quality", "") if dock is not None else ""
            if name:
                return name
        with suppress(Exception):
            from ..tools.utils.qgisred_project_utils import QGISRedProjectUtils
            name = QGISRedProjectUtils.getQualityDisplayName()
            if name:
                return name
        return self.tr("Quality")

    def _profileVariableDisplay(self, key):
        if key == "Quality":
            return self._profileQualityLabel()
        return self.tr(self._profileVariableLabel(key))

    def _profileVariableUnit(self, key):
        field = PROFILE_VARIABLE_UNIT_FIELDS.get(key)
        if not field:
            return ""
        with suppress(Exception):
            return QGISRedFieldUtils().getUnitAbbreviation(field[0], field[1]) or ""
        return ""

    def _profileDistanceUnit(self):
        with suppress(Exception):
            return QGISRedFieldUtils().getUnitAbbreviation(
                PROFILE_DISTANCE_UNIT_FIELD[0], PROFILE_DISTANCE_UNIT_FIELD[1]
            ) or ""
        return ""

    def _profileDistanceDisplay(self):
        return label_with_unit(self.tr("Distance"), self._profileDistanceUnit())

    def _profileVariableDisplayWithUnit(self, key):
        return label_with_unit(self._profileVariableDisplay(key), self._profileVariableUnit(key))

    def _pushProfileTable(self, dock, series, nodes, distances, key):
        headers = [self.tr("Id"), self._profileDistanceDisplay()] + [
            s.get("display_label") or s["label"] for s in series
        ]
        add_envelope = self._profileEnvelopeActive(key)
        stat_max, stat_min = ({}, {})
        if add_envelope:
            headers += [self.tr("Maximum"), self.tr("Max. time"), self.tr("Minimum"), self.tr("Min. time")]
            stat_max, stat_min = self._profileStats()
        rows = []
        for i, node in enumerate(nodes):
            row = [str(node), format_profile_value(distances[i])]
            for s in series:
                value = s["points"][i][1] if i < len(s["points"]) else None
                row.append(format_profile_value(value))
            if add_envelope:
                mx = stat_max.get(node, {}).get(key, {})
                mn = stat_min.get(node, {}).get(key, {})
                row += [
                    format_profile_value(mx.get("Value")),
                    self._formatStatTime(mx.get("Time")),
                    format_profile_value(mn.get("Value")),
                    self._formatStatTime(mn.get("Time")),
                ]
            rows.append(row)
        dock.setTableData(headers, rows)

    def _formatStatTime(self, seconds):
        if seconds is None or seconds < 0:
            return "-"
        from ..ui.analysis.qgisred_results_data import seconds_to_time_str_no_seconds

        with suppress(Exception):
            return seconds_to_time_str_no_seconds(int(seconds))
        return "-"

    def _profileVariableColor(self, key):
        from qgis.PyQt.QtGui import QColor

        hex_color = profile_variable_color_hex(key)
        return QColor(hex_color) if hex_color else None

    def _appendProfileBranchSeries(self, series, key):
        branches = getattr(self, "_profileBranches", []) or []
        if not branches:
            return
        node_values = None
        losses = None
        if key == "HeadLoss":
            losses = self._profileLinkLosses()
        else:
            node_values = self._profileNodeValues(key)
        for i, branch in enumerate(branches):
            branch_path = branch.get("path")
            if not branch_path or len(branch_path["nodes"]) < 2:
                continue
            branch_nodes = branch_path["nodes"]
            branch_distances = branch["distances"]
            branch_is_reference = branch_path["is_reference"]
            reference_indices = {j for j, r in enumerate(branch_is_reference) if r}
            if key == "HeadLoss":
                values = cumulative_link_losses(branch_path["links"], losses)
                points = [(branch_distances[j], values[j]) for j in range(len(branch_nodes))]
            else:
                samples = sample_node_variable(branch_nodes, branch_distances, node_values, branch_is_reference)
                points = [(s["distance"], s["value"]) for s in samples]
            branch_label = self.tr("Branch") + " " + str(i + 1)
            branch_key = "branch_{}".format(i)
            series.append({
                "label": branch_label,
                "readout_label": self._profileVariableDisplayWithUnit(key),
                "points": points,
                "reference_indices": reference_indices,
                "node_ids": [str(n) for n in branch_nodes],
                "color": self._profileVariableColor(key),
                "fill": key == "Elevation",
                "deletable": True,
                "path_key": branch_key,
                "path_label": branch_label,
                "symbols_mode": "full",
            })
            if key == "Head":
                elev_samples = sample_node_variable(
                    branch_nodes, branch_distances, getattr(self, "_profileNodeElev", {}), branch_is_reference
                )
                elev_points = [(s["distance"], s["value"]) for s in elev_samples]
                series.append({
                    "label": self.tr("Elevation"),
                    "display_label": self._profileVariableDisplayWithUnit("Elevation"),
                    "points": elev_points,
                    "reference_indices": reference_indices,
                    "node_ids": [str(n) for n in branch_nodes],
                    "color": self._profileVariableColor("Elevation"),
                    "path_key": branch_key,
                    "path_label": branch_label,
                })

    def _drawProfileHighlight(self):
        from qgis.gui import QgsRubberBand, QgsVertexMarker
        from qgis.core import Qgis, QgsGeometry, QgsPointXY
        from qgis.PyQt.QtGui import QColor

        self._clearProfileHighlight()
        if getattr(self, "_profileFocusCeded", False):
            return
        dock = self._activeDock()
        if dock is not None and not dock.isVisible():
            return
        path = getattr(self, "_profilePath", None)
        if not path or not path["nodes"]:
            return

        canvas = self.iface.mapCanvas()
        link_ids = {str(lid) for lid in path["links"]}
        reference_ids = {
            path["nodes"][i] for i in range(len(path["nodes"])) if path["is_reference"][i]
        }
        for branch in getattr(self, "_profileBranches", []) or []:
            branch_path = branch.get("path")
            if branch_path and branch_path["nodes"]:
                link_ids |= {str(lid) for lid in branch_path["links"]}
                reference_ids |= {
                    branch_path["nodes"][j]
                    for j in range(len(branch_path["nodes"]))
                    if branch_path["is_reference"][j]
                }

        if link_ids:
            band = None
            for identifier in _LINK_LAYER_IDENTIFIERS:
                layer = self._profileLayerByIdentifier(identifier)
                if layer is None:
                    continue
                idField = QGISRedFieldUtils().getIdFieldName(layer)
                for feature in layer.getFeatures():
                    if str(feature.attribute(idField)) not in link_ids:
                        continue
                    if band is None:
                        band = QgsRubberBand(canvas, Qgis.GeometryType.Line)
                        band.setColor(QColor(_PATH_HIGHLIGHT_RGB[0], _PATH_HIGHLIGHT_RGB[1],
                                             _PATH_HIGHLIGHT_RGB[2], 220))
                        band.setWidth(5)
                        self._profileHighlights.append(band)
                    band.addGeometry(feature.geometry(), layer)

        node_geoms = self._profileNodeGeometries(reference_ids)
        for geom in node_geoms:
            marker = QgsVertexMarker(canvas)
            marker.setColor(QColor(255, 127, 0))
            marker.setIconSize(18)
            marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
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
            idField = QGISRedFieldUtils().getIdFieldName(layer)
            for feature in layer.getFeatures():
                fid = str(feature.attribute(idField))
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
        self._clearProfileMapHover()


for _attr, _field in _PROFILE_STATE_FIELDS.items():
    setattr(ProfileSection, _attr, _profile_state_property(_field))
