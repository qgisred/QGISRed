# -*- coding: utf-8 -*-
from contextlib import suppress
import os
import glob as _glob

from qgis.core import QgsProject
from qgis.gui import QgsLayerTreeViewIndicator
from qgis.PyQt.QtCore import QTimer, QCoreApplication
from qgis.PyQt.QtGui import QIcon


class StaleLayerManager:
    """Polls every 5 s and adds a QgsLayerTreeViewIndicator to Issues/Queries layers
    whose files are older than the newest input shapefile."""

    def __init__(self, iface, getProjectInfo):
        """
        iface          — QgisInterface
        getProjectInfo — callable returning (NetworkName, ProjectDirectory); empty
                         strings mean no project is open.
        """
        self._iface = iface
        self._getProjectInfo = getProjectInfo
        self._indicators = {}  # layer_id → QgsLayerTreeViewIndicator

        QgsProject.instance().layersRemoved.connect(self._onLayersRemoved)

        self._timer = QTimer()
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._check)
        self._timer.start()

    @staticmethod
    def tr(msg):
        return QCoreApplication.translate("StaleLayerManager", msg)

    # ------------------------------------------------------------------
    # Timer callback
    # ------------------------------------------------------------------

    def _check(self):
        net, projDir = self._getProjectInfo()
        if not net or not projDir:
            self._clearAll()
            return

        inputFiles = (
            _glob.glob(os.path.join(projDir, f"{net}_*.shp")) +
            _glob.glob(os.path.join(projDir, f"{net}_*.dbf"))
        )
        if not inputFiles:
            self._clearAll()
            return

        newestInput = max(os.path.getmtime(f) for f in inputFiles if os.path.exists(f))

        issuesDir = os.path.normcase(os.path.join(projDir, "Issues"))
        queriesDir = os.path.normcase(os.path.join(projDir, "Queries"))
        resultsDir = os.path.normcase(os.path.join(projDir, "Results"))

        for layer in list(QgsProject.instance().mapLayers().values()):
            layerFile = layer.dataProvider().dataSourceUri().split("|")[0].strip()
            normFile = os.path.normcase(layerFile)
            baseName = os.path.basename(layerFile)

            relevant = (
                (normFile.startswith(issuesDir) or normFile.startswith(queriesDir) or normFile.startswith(resultsDir))
                and baseName.lower().startswith(net.lower() + "_")
            )

            if not relevant:
                self._removeIndicator(layer.id())
                continue

            if not os.path.exists(layerFile):
                self._removeIndicator(layer.id())
                continue

            if newestInput > os.path.getmtime(layerFile):
                self._addIndicator(layer)
            else:
                self._removeIndicator(layer.id())

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------

    def _addIndicator(self, layer):
        layerId = layer.id()
        if layerId in self._indicators:
            return
        view = self._iface.layerTreeView()
        node = QgsProject.instance().layerTreeRoot().findLayer(layerId)
        if node is None:
            return
        indicator = QgsLayerTreeViewIndicator(view)
        indicator.setIcon(QIcon(":/images/iconWarning.svg"))
        indicator.setToolTip(self.tr("Layer may be outdated — inputs have changed since last generation"))
        view.addIndicator(node, indicator)
        self._indicators[layerId] = indicator

    def _removeIndicator(self, layerId):
        indicator = self._indicators.pop(layerId, None)
        if indicator is None:
            return
        view = self._iface.layerTreeView()
        node = QgsProject.instance().layerTreeRoot().findLayer(layerId)
        if node is not None:
            view.removeIndicator(node, indicator)

    def _clearAll(self):
        for layerId in list(self._indicators.keys()):
            self._removeIndicator(layerId)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _onLayersRemoved(self, layerIds):
        # Node is already gone; just clean the dict to avoid orphaned entries.
        for layerId in layerIds:
            self._indicators.pop(layerId, None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def forceCheck(self):
        """Run an immediate staleness check without waiting for the next timer tick."""
        self._check()

    def stop(self):
        self._timer.stop()
        self._clearAll()
        with suppress(Exception):
            QgsProject.instance().layersRemoved.disconnect(self._onLayersRemoved)
