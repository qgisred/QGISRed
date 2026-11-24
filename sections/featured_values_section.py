# -*- coding: utf-8 -*-
import os
from contextlib import suppress

from qgis.PyQt.QtCore import QLocale, QTimer
from qgis.core import (
    QgsBookmark, QgsFeatureRequest, QgsGeometry, QgsMessageLog, QgsPointXY, QgsProject, QgsRectangle,
    QgsReferencedRectangle,
)
from qgis.gui import QgsMapToolEmitPoint

from ..compat import QGIS_WARNING
from ..tools.qgisred_dependencies import QGISRedDependencies as GISRed
from ..tools.utils.qgisred_field_utils import QGISRedFieldUtils
from ..tools.utils.qgisred_layer_utils import QGISRedLayerUtils
from ..tools.utils.qgisred_result_fields import resultIdField
from ..ui.analysis import featured_values_config as fv_config
from ..ui.analysis import featured_values_fielddata as fv_data
from ..ui.analysis import featured_values_layer as fv_layer

_SIGNAL_COLOR = "#555555"
_MISSING_TEXT = "—"
_PICK_TOLERANCE_PIXELS = 10


class _FeaturedValuesPickTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self._callback = callback

    def canvasReleaseEvent(self, event):
        self._callback(self.toMapCoordinates(event.pos()))


class FeaturedValuesSection:
    featuredValuesDialog = None
    _featuredValuesConfig = None
    _featuredValuesConfigPath = ""
    _featuredValuesPending = False
    _featuredValuesPickTool = None
    _featuredValuesStyleKey = None
    _featuredValuesPoints = None
    _featuredValuesSignals = None

    def runFeaturedValues(self):
        if not self.checkDependencies():
            return
        self.defineCurrentProject()
        if not self.isValidProject():
            return
        if not os.path.exists(self._outFilePath()):
            self.pushMessage(self.tr("Run the model before declaring featured values."), level=1)
            return
        dock = self.ResultDockwidget
        if dock is None or not getattr(dock, "outPath", "") or not dock.TimeLabels:
            self.runShowResultsDock()
        if self.ResultDockwidget is None:
            return

        from ..ui.analysis.qgisred_featuredvalues_dialog import QGISRedFeaturedValuesDialog
        if self.featuredValuesDialog is None:
            self.featuredValuesDialog = QGISRedFeaturedValuesDialog(self, self.iface.mainWindow())
        self._loadFeaturedValuesDialog()
        self.featuredValuesDialog.showNormal()
        self.featuredValuesDialog.raise_()
        self.featuredValuesDialog.activateWindow()
        self.refreshFeaturedValues()

    def closeFeaturedValues(self):
        self.featuredValuesStopPicking()
        dialog, self.featuredValuesDialog = self.featuredValuesDialog, None
        if dialog is not None:
            with suppress(Exception):
                dialog.close()
                dialog.deleteLater()
        self._featuredValuesConfig = None
        self._featuredValuesConfigPath = ""
        self._featuredValuesStyleKey = None
        self._featuredValuesPoints = None
        self._featuredValuesSignals = None

    def _connectFeaturedValuesToResultsDock(self):
        dock = self.ResultDockwidget
        dock.timeTextChanged.connect(self._scheduleFeaturedValuesRefresh)
        dock.simulationFinished.connect(self._scheduleFeaturedValuesRefresh)
        dock.statisticsModeChanged.connect(self._scheduleFeaturedValuesRefresh)
        dock.resultPropertyChanged.connect(self._scheduleFeaturedValuesRefresh)

    def _scheduleFeaturedValuesRefresh(self, *_args):
        if self._featuredValuesPending:
            return
        self._featuredValuesPending = True
        QTimer.singleShot(0, self._runScheduledFeaturedValuesRefresh)

    def _runScheduledFeaturedValuesRefresh(self):
        self._featuredValuesPending = False
        self.refreshFeaturedValues()

    def _featuredValuesCurrentConfig(self):
        path = fv_config.config_path(self.ProjectDirectory, self.NetworkName)
        if self._featuredValuesConfig is None or path != self._featuredValuesConfigPath:
            self._featuredValuesConfig = fv_config.load(path)
            self._featuredValuesConfigPath = path
            self._featuredValuesStyleKey = None
        return self._featuredValuesConfig

    def _featuredValuesTopology(self):
        topology = None
        with suppress(Exception):
            topology = self.ResultDockwidget._resultsTopology()
        if not topology:
            return [], []
        return list(topology[0]), list(topology[1])

    def _featuredValuesQuery(self, method, *arguments):
        try:
            answer = method(self.ProjectDirectory, self.NetworkName, *arguments)
        except Exception as exc:
            answer = str(exc)
        if not answer.startswith(fv_data.OK):
            QgsMessageLog.logMessage("Featured values: {}".format(answer), "QGISRed", QGIS_WARNING)
        return answer

    def featuredValuesSignals(self, reload=False):
        if reload or self._featuredValuesSignals is None:
            self._featuredValuesSignals = fv_data.parse_signals(self._featuredValuesQuery(GISRed.GetFieldDataSignals))
        return self._featuredValuesSignals

    def _featuredValuesMeasured(self, rows, elapsed_seconds):
        signal_ids = sorted({row["signal"] for row in rows if row["slot"] >= 0 and row["showMeasured"]})
        if not signal_ids:
            return {}
        return fv_data.parse_values(self._featuredValuesQuery(
            GISRed.GetFieldDataValues, fv_data.join_ids(signal_ids), repr(float(elapsed_seconds))))

    def _featuredValuesElementData(self, rows):
        dock = self.ResultDockwidget
        data = {}
        for element in (fv_config.NODE, fv_config.LINK):
            ids = sorted({row["id"] for row in rows if row["element"] == element})
            layer = dock._findResultLayer(element) if ids else None
            if layer is None:
                continue
            id_field = resultIdField(layer)
            quoted = ",".join("'" + element_id.replace("'", "''") + "'" for element_id in ids)
            request = QgsFeatureRequest().setFilterExpression('"{}" IN ({})'.format(id_field, quoted))
            names = layer.fields().names()
            for feature in layer.getFeatures(request):
                if not feature.hasGeometry():
                    continue
                geometry = feature.geometry()
                if element == fv_config.LINK:
                    geometry = geometry.interpolate(geometry.length() / 2.0)
                values = {}
                for name in names:
                    value = feature[name]
                    values[name] = value if isinstance(value, (int, float, str)) else None
                data[(element, str(feature[id_field]))] = (geometry.asPoint(), values)
        return data

    def featuredValuesFieldName(self, element, field):
        dock = self.ResultDockwidget
        field_map = getattr(dock, "_node_field_map" if element == fv_config.NODE else "_link_field_map", {})
        return next((label for label, name in field_map.items() if name == field), field)

    def featuredValuesMagnitudeName(self, key):
        element, _, field = key.partition("/")
        if element == "Signal":
            return field
        name = self.featuredValuesFieldName(element, field)
        if element == fv_config.LINK and field in fv_config.NODE_FIELDS:
            name = "{} ({})".format(name, self.tr("links"))
        return name

    def _featuredValuesColor(self, key):
        element, _, field = key.partition("/")
        if element == "Signal":
            return _SIGNAL_COLOR
        color = None
        with suppress(Exception):
            color = self.ResultDockwidget._magnitudeColor(field, element == fv_config.NODE)
        return color or _SIGNAL_COLOR

    def featuredValuesRows(self):
        config = self._featuredValuesCurrentConfig()
        node_ids, link_ids = self._featuredValuesTopology()
        return fv_config.build_rows(config, self.featuredValuesSignals(), node_ids, link_ids)

    def _formatFeaturedValue(self, value, decimals, unit, show_units):
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        text = QLocale().toString(float(value), "f", decimals)
        return "{} {}".format(text, unit) if show_units and unit else text

    def _featuredValuesRecords(self, rows, display):
        dock = self.ResultDockwidget
        signals = self.featuredValuesSignals()
        elements = self._featuredValuesElementData(rows)
        field_utils = QGISRedFieldUtils()
        stats_mode = bool(getattr(dock, "_statsMode", False))
        index = dock.cbTimes.currentIndex()
        elapsed_text = dock.TimeLabels[index] if 0 <= index < len(dock.TimeLabels) else ""
        elapsed = dock._elapsedTextToSeconds(elapsed_text) if elapsed_text else 0
        var_decimals = getattr(dock, "_varDecimals", {}) or {}
        measured = {} if stats_mode else self._featuredValuesMeasured(rows, elapsed)

        records = []
        points = {}
        for row in rows:
            element_data = elements.get((row["element"], row["id"]))
            signal = signals.get(row["signal"], {}) if row["signal"] else {}
            point = QgsPointXY(*signal["point"]) if signal.get("point") else None
            if point is None and element_data is not None:
                point = element_data[0]
            if point is None:
                continue
            points[fv_config.item_key(row["item"])] = point
            if row["slot"] < 0:
                continue

            decimals, unit = 2, ""
            if row["field"]:
                plural = "Nodes" if row["element"] == fv_config.NODE else "Links"
                decimals = var_decimals.get(row["field"])
                if decimals is None:
                    decimals = field_utils.getDecimals(plural, row["field"])
                unit = field_utils.getUnitAbbreviation(plural, row["field"])

            sim_value = element_data[1].get(row["field"]) if element_data and row["showSimulated"] else None
            sim_text = self._formatFeaturedValue(sim_value, decimals, unit, display["showUnits"])
            meas_value, meas_text = None, ""
            if row["showMeasured"] and not stats_mode:
                meas_value = measured.get(row["signal"])
                meas_text = self._formatFeaturedValue(meas_value, decimals, signal.get("units", ""),
                                                      display["showUnits"]) or _MISSING_TEXT
            if not sim_text and not meas_text:
                continue
            if display["showId"]:
                prefix = (row["id"] or row["signal"]) + ": "
                if sim_text:
                    sim_text = prefix + sim_text
                else:
                    meas_text = prefix + meas_text

            color = self._featuredValuesColor(row["magnitude"])
            records.append({
                "point": point,
                "Id": row["id"] or row["meter"],
                "Type": row["element"] or fv_config.METER,
                "Magnitude": self.featuredValuesMagnitudeName(row["magnitude"]),
                "Signal": row["signal"],
                "SimValue": sim_value if isinstance(sim_value, (int, float)) else None,
                "MeasValue": meas_value,
                "SimText": sim_text,
                "MeasText": meas_text,
                "Level": row["level"],
                "Row": row["slot"],
                "Color": color,
                "Contrast": fv_layer.contrast_color(color),
            })
        self._featuredValuesPoints = points
        return records

    def _removeFeaturedValuesLayer(self):
        layer = fv_layer.find_layer()
        if layer is None:
            return
        QGISRedLayerUtils.stopRenderingForRemoval(self.iface)
        QgsProject.instance().removeMapLayer(layer.id())
        self._featuredValuesStyleKey = None

    def _featuredValuesLayer(self, display):
        layer = fv_layer.find_layer()
        if layer is not None and layer.fields().names() != [name for name, _ in fv_layer._FIELDS]:
            self._removeFeaturedValuesLayer()
            layer = None
        if layer is not None:
            return layer
        dock = self.ResultDockwidget
        node_layer = dock._findResultLayer(fv_config.NODE)
        crs = node_layer.crs() if node_layer is not None else QgsProject.instance().crs()
        layer = fv_layer.create_layer(crs, self.tr("Featured values"))
        utils = QGISRedLayerUtils(self.ProjectDirectory, self.NetworkName, self.iface)
        group = utils.getOrCreateNestedGroup([self.NetworkName, "Results", dock.Scenario])
        QgsProject.instance().addMapLayer(layer, False)
        group.insertLayer(0, layer)
        self._featuredValuesStyleKey = None
        self._applyFeaturedValuesVisibility(layer, display)
        return layer

    def _applyFeaturedValuesVisibility(self, layer, display):
        node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if node is not None:
            node.setItemVisibilityChecked(bool(display["visible"]))

    def refreshFeaturedValues(self):
        try:
            self._refreshFeaturedValues()
        except Exception as exc:
            QgsMessageLog.logMessage("Featured values: {}".format(exc), "QGISRed", QGIS_WARNING)

    def _refreshFeaturedValues(self):
        dock = self.ResultDockwidget
        if dock is None or not self.ProjectDirectory or not self.NetworkName:
            return
        if not getattr(dock, "TimeLabels", None) or not dock.isCurrentProject():
            return
        config = self._featuredValuesCurrentConfig()
        display = config["display"]
        self.featuredValuesSignals(reload=True)
        rows = fv_config.assign_slots(self.featuredValuesRows(), display)
        records = self._featuredValuesRecords(rows, display) if rows else []
        if not records:
            self._removeFeaturedValuesLayer()
            return

        layer = self._featuredValuesLayer(display)
        fv_layer.set_records(layer, records)
        magnitudes = sorted({(record["Magnitude"], record["Color"]) for record in records})
        extent = None
        node_layer = dock._findResultLayer(fv_config.NODE)
        if node_layer is not None:
            extent = node_layer.extent()
        network_size = max(extent.width(), extent.height()) if extent is not None else 0.0
        style_key = (repr(sorted(display.items())), tuple(magnitudes), network_size)
        if style_key != self._featuredValuesStyleKey:
            fv_layer.apply_labeling(layer, display, network_size, self.tr("Simulated"), self.tr("Measured"))
            fv_layer.apply_renderer(layer, magnitudes)
            self._featuredValuesStyleKey = style_key
            with suppress(Exception):
                self.iface.layerTreeView().refreshLayerSymbology(layer.id())
        layer.triggerRepaint()

    def _loadFeaturedValuesDialog(self):
        node_ids, link_ids = self._featuredValuesTopology()
        self.featuredValuesDialog.setData(
            self._featuredValuesCurrentConfig(), node_ids, link_ids, self.featuredValuesSignals(reload=True))

    def featuredValuesConfigChanged(self):
        config = self._featuredValuesCurrentConfig()
        try:
            fv_config.save(self._featuredValuesConfigPath, config)
        except OSError as exc:
            self.pushMessage(self.tr("The featured values could not be saved: %1").replace("%1", str(exc)), level=1)
        self.refreshFeaturedValues()
        layer = fv_layer.find_layer()
        if layer is not None:
            self._applyFeaturedValuesVisibility(layer, config["display"])

    def featuredValuesStartPicking(self):
        canvas = self.iface.mapCanvas()
        if self._featuredValuesPickTool is None:
            self._featuredValuesPickTool = _FeaturedValuesPickTool(canvas, self._featuredValuesPicked)
            self._featuredValuesPickTool.deactivated.connect(self._onFeaturedValuesPickDeactivated)
        canvas.setMapTool(self._featuredValuesPickTool)

    def featuredValuesStopPicking(self):
        tool = self._featuredValuesPickTool
        if tool is not None:
            with suppress(Exception):
                if self.iface.mapCanvas().mapTool() is tool:
                    self.iface.mapCanvas().unsetMapTool(tool)

    def _onFeaturedValuesPickDeactivated(self):
        if self.featuredValuesDialog is not None:
            self.featuredValuesDialog.setPicking(False)

    def _featuredValuesPicked(self, point):
        dialog = self.featuredValuesDialog
        dock = self.ResultDockwidget
        if dialog is None or dock is None:
            return
        element = dialog.currentElement()
        layer = dock._findResultLayer(element)
        if layer is None:
            return
        tolerance = self.iface.mapCanvas().getCoordinateTransform().mapUnitsPerPixel() * _PICK_TOLERANCE_PIXELS
        rect = QgsRectangle(point.x() - tolerance, point.y() - tolerance, point.x() + tolerance, point.y() + tolerance)
        target = QgsGeometry.fromPointXY(point)
        nearest, nearest_distance = None, None
        for feature in layer.getFeatures(QgsFeatureRequest().setFilterRect(rect)):
            distance = feature.geometry().distance(target)
            if nearest is None or distance < nearest_distance:
                nearest, nearest_distance = feature, distance
        if nearest is None:
            self.pushMessage(self.tr("No network element found at this location."), level=1)
            return
        dialog.addSimulated(element, str(nearest[resultIdField(layer)]))

    def _featuredValuesExtent(self, items):
        points = [self._featuredValuesPoints.get(fv_config.item_key(item)) for item in items] \
            if self._featuredValuesPoints else []
        points = [point for point in points if point is not None]
        if not points:
            return None
        rect = QgsRectangle(points[0], points[0])
        for point in points[1:]:
            rect.combineExtentWith(point)
        network = None
        node_layer = self.ResultDockwidget._findResultLayer(fv_config.NODE) if self.ResultDockwidget else None
        if node_layer is not None:
            network = node_layer.extent()
        base = max(network.width(), network.height()) / 40.0 if network is not None else 0.0
        margin = max(rect.width(), rect.height()) * 0.5 + base
        if margin <= 0:
            margin = 1.0
        return rect.buffered(margin)

    def featuredValuesZoomTo(self, items):
        rect = self._featuredValuesExtent(items)
        if rect is None:
            self.pushMessage(self.tr("The selected featured values have no position on the map."), level=1)
            return
        canvas = self.iface.mapCanvas()
        canvas.setExtent(rect)
        canvas.refresh()

    def featuredValuesBookmark(self, items, name):
        rect = self._featuredValuesExtent(items)
        if rect is None:
            self.pushMessage(self.tr("The selected featured values have no position on the map."), level=1)
            return
        layer = fv_layer.find_layer()
        crs = layer.crs() if layer is not None else QgsProject.instance().crs()
        bookmark = QgsBookmark()
        bookmark.setName(name)
        bookmark.setGroup("QGISRed")
        bookmark.setExtent(QgsReferencedRectangle(rect, crs))
        QgsProject.instance().bookmarkManager().addBookmark(bookmark)
        self.pushMessage(self.tr("Bookmark '%1' created.").replace("%1", name), level=3)
