# -*- coding: utf-8 -*-
from contextlib import suppress
import os
import xml.etree.ElementTree as ET  # nosec B405 — parses a local appearance settings file written by this plugin, no external input

from qgis.PyQt.QtWidgets import QApplication, QColorDialog
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtGui import QColor, QPixmap, QIcon, QPainter

from ...compat import PAINTER_ANTIALIASING
from ...tools.utils.qgisred_field_utils import QGISRedFieldUtils
from .qgisred_results_data import NODE_RESULT_FIELDS, LINK_RESULT_FIELDS
from .qgisred_results_rendering import time_field_name


class _ResultsAppearanceMixin:
    """Mixin that handles the Appearance tab: labels, symbol factors, background color,
    per-variable decimal storage, and XML persistence of all appearance settings."""

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    def _refreshLabelsIfShowing(self, layer_type):
        layer = self._findResultLayer(layer_type)
        if not layer:
            return
        checkbox = self.cbNodeLabels if layer_type == "Node" else self.cbLinkLabels
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks
        field_map = self._node_field_map if layer_type == "Node" else self._link_field_map
        if checkbox.isChecked() and combobox.currentIndex() > 0:
            field = field_map.get(combobox.currentText(), "")
            if field:
                is_min_max_stat = self._statsMode and self.cbStatistics.currentText() in (
                    self.lbl_maximum, self.lbl_minimum)
                time_fld = time_field_name(field, layer_type) if is_min_max_stat else None
                self.setLayerLabels(layer, field, time_fld)
        else:
            layer.setLabelsEnabled(False)
            layer.triggerRepaint()

    def _onLabelStyleChanged(self):
        self._labelFontSize = self.spFontSize.value()
        self._labelColorByRange = self.rbColorByRange.isChecked()
        self._labelShowId = self.cbShowId.isChecked()
        self._saveAppearanceSettings()
        self._refreshLabelsIfShowing("Node")
        self._refreshLabelsIfShowing("Link")

    # ------------------------------------------------------------------
    # Decimals
    # ------------------------------------------------------------------

    def _onDecimalsChanged(self):
        node_field = self._node_field_map.get(self.cbNodes.currentText(), "")
        link_field = self._link_field_map.get(self.cbLinks.currentText(), "")
        if node_field:
            self._varDecimals[node_field] = self.spNodeDecimals.value()
        if link_field:
            self._varDecimals[link_field] = self.spLinkDecimals.value()
        self._saveAppearanceSettings()
        self._reloadResultsWithNewDecimals()
        self._refreshLabelsIfShowing("Node")
        self._refreshLabelsIfShowing("Link")

    def _onResetSingleDecimals(self, layer_type):
        """Clear the stored decimals override for the variable currently selected
        in cbNodes/cbLinks, falling back to the CSV default."""
        field_map = self._node_field_map if layer_type == "Node" else self._link_field_map
        combobox = self.cbNodes if layer_type == "Node" else self.cbLinks
        field = field_map.get(combobox.currentText(), "")
        self._varDecimals.pop(field, None)
        self._resetDecimalsForVariable(field, "Nodes" if layer_type == "Node" else "Links", layer_type)
        self._saveAppearanceSettings()
        self._reloadResultsWithNewDecimals()
        self._refreshLabelsIfShowing("Node")
        self._refreshLabelsIfShowing("Link")

    def _reloadResultsWithNewDecimals(self):
        """Delete and recreate Double result fields so shapefile precision matches the new decimal count."""
        if not self._findResultLayer("Node") and not self._findResultLayer("Link"):
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for layerName in ["Node", "Link"]:
                layer = self._findResultLayer(layerName)
                if not layer:
                    continue
                fields_def = NODE_RESULT_FIELDS if layerName == "Node" else LINK_RESULT_FIELDS
                double_indices = [
                    layer.fields().indexOf(name)
                    for name, type_str, *_ in fields_def
                    if type_str == "Double" and layer.fields().indexOf(name) >= 0
                ]
                if double_indices:
                    layer.dataProvider().deleteAttributes(double_indices)
                    layer.updateFields()
                    layer.dataProvider().reloadData()
                self.prepareResultFields(layer, layerName)
            if self._statsMode:
                self.completeStatsLayers()
            else:
                self.completeResultLayers()
        finally:
            QApplication.restoreOverrideCursor()

    def _resetDecimalsForVariable(self, field_name, csv_element_type, layer_type="Node"):
        """Update the decimals spinbox to the stored value (or CSV default) for field_name."""
        try:
            csv_dec = QGISRedFieldUtils().getDecimals(csv_element_type, field_name) if field_name else 2
        except Exception:
            csv_dec = 2
        dec = self._varDecimals.get(field_name, csv_dec)
        if layer_type == "Node":
            self.spNodeDecimals.blockSignals(True)
            self.spNodeDecimals.setValue(dec)
            self.spNodeDecimals.blockSignals(False)
            var_name = self.cbNodes.currentText() if self.cbNodes.currentIndex() > 0 else QCoreApplication.translate("QGISRedResultsDock", "Nodes")
            self.lbNodeDecimals.setText(QCoreApplication.translate("QGISRedResultsDock", "%1 decimals").replace("%1", var_name) + ":")
        else:
            self.spLinkDecimals.blockSignals(True)
            self.spLinkDecimals.setValue(dec)
            self.spLinkDecimals.blockSignals(False)
            var_name = self.cbLinks.currentText() if self.cbLinks.currentIndex() > 0 else QCoreApplication.translate("QGISRedResultsDock", "Links")
            self.lbLinkDecimals.setText(QCoreApplication.translate("QGISRedResultsDock", "%1 decimals").replace("%1", var_name) + ":")

    # ------------------------------------------------------------------
    # Enablement (grey out controls tied to a variable combobox on None)
    # ------------------------------------------------------------------

    def _updateAppearanceEnablement(self):
        """Sync the Appearance tab (enabled state + decimals label/value) to whichever
        variable is currently selected in cbNodes/cbLinks — including the "None" case,
        where the field maps resolve to "" and _resetDecimalsForVariable falls back to
        the generic "Nodes"/"Links" label."""
        node_field = self._node_field_map.get(self.cbNodes.currentText(), "")
        link_field = self._link_field_map.get(self.cbLinks.currentText(), "")
        nodes_active = self.cbNodes.currentIndex() > 0
        links_active = self.cbLinks.currentIndex() > 0
        # Status is categorical (OPEN/CLOSED/...) — decimals don't apply to it.
        link_decimals_active = links_active and link_field != "Status"
        for widget in (self.lbNodeDecimals, self.spNodeDecimals,
                       self.lbSymbolFactor, self.dspSymbolFactor,
                       self.cbNodeBorder):
            widget.setEnabled(nodes_active)
        for widget in (self.lbPipeFactor, self.dspPipeFactor,
                       self.lbArrowFactor, self.dspArrowFactor):
            widget.setEnabled(links_active)
        for widget in (self.lbLinkDecimals, self.spLinkDecimals):
            widget.setEnabled(link_decimals_active)
        self.cbProportional.setEnabled(nodes_active or links_active)

        self._resetDecimalsForVariable(node_field, "Nodes", "Node")
        self._resetDecimalsForVariable(link_field, "Links", "Link")

    # ------------------------------------------------------------------
    # Symbol factors
    # ------------------------------------------------------------------

    def _onSymbolFactorChanged(self):
        self._pipeFactor = self.dspPipeFactor.value()
        self._symbolFactor = self.dspSymbolFactor.value()
        self._arrowFactor = self.dspArrowFactor.value()
        self._proportional = self.cbProportional.isChecked()
        self._nodeBorder = self.cbNodeBorder.isChecked()
        self._saveAppearanceSettings()
        node_layer = self._findResultLayer("Node")
        link_layer = self._findResultLayer("Link")
        if node_layer:
            self.applySymbolScaleFactors(node_layer)
        if link_layer:
            self.applySymbolScaleFactors(link_layer)

    # ------------------------------------------------------------------
    # Background color
    # ------------------------------------------------------------------

    def _onBgColorClicked(self):
        initial = self._bgColor if self._bgColor else QColor("white")
        color = QColorDialog.getColor(initial, self, QCoreApplication.translate("QGISRedResultsDock", "Map background color"))
        if color.isValid():
            self._bgColor = color
            self.btBgColor.setStyleSheet(f"background-color: {color.name()};")
            self.btBgColor.setText(color.name())
            self.btClearBgColor.setEnabled(True)
            self._applyBgColor()
            self._saveAppearanceSettings()

    def _onClearBgColor(self):
        self._bgColor = None
        self.btBgColor.setStyleSheet("")
        self.btBgColor.setText(QCoreApplication.translate("QGISRedResultsDock", "No color"))
        self.btClearBgColor.setEnabled(False)
        self._applyBgColor()
        self._saveAppearanceSettings()

    def _applyBgColor(self):
        canvas = self.iface.mapCanvas()
        if self._bgColor:
            if self._savedBgColor is None:
                self._savedBgColor = canvas.canvasColor()
            canvas.setCanvasColor(self._bgColor)
        else:
            if self._savedBgColor is not None:
                canvas.setCanvasColor(self._savedBgColor)
                self._savedBgColor = None
        canvas.refresh()

    # ------------------------------------------------------------------
    # Icons (drawn from a glyph so translators never see them in button text)
    # ------------------------------------------------------------------

    def _makeGlyphIcon(self, glyph, size=16):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(PAINTER_ANTIALIASING)
        font = painter.font()
        font.setPointSize(int(size * 0.65))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, glyph)
        painter.end()
        return QIcon(pixmap)

    # ------------------------------------------------------------------
    # Reset all
    # ------------------------------------------------------------------

    def _onResetAppearance(self):
        self._labelFontSize = 8
        self._varDecimals = {}
        self._labelColorByRange = False
        self._labelShowId = False
        self._pipeFactor = 1.0
        self._symbolFactor = 1.0
        self._arrowFactor = 1.0
        self._proportional = False
        self._nodeBorder = False
        self._bgColor = None

        self.spFontSize.blockSignals(True)
        self.spFontSize.setValue(8)
        self.spFontSize.blockSignals(False)
        node_field = self._node_field_map.get(self.cbNodes.currentText(), "")
        self._resetDecimalsForVariable(node_field, "Nodes", "Node")
        link_field = self._link_field_map.get(self.cbLinks.currentText(), "")
        self._resetDecimalsForVariable(link_field, "Links", "Link")
        self.rbColorBlack.setChecked(True)
        self.cbShowId.setChecked(False)
        self.dspPipeFactor.blockSignals(True)
        self.dspPipeFactor.setValue(1.0)
        self.dspPipeFactor.blockSignals(False)
        self.dspSymbolFactor.blockSignals(True)
        self.dspSymbolFactor.setValue(1.0)
        self.dspSymbolFactor.blockSignals(False)
        self.dspArrowFactor.blockSignals(True)
        self.dspArrowFactor.setValue(1.0)
        self.dspArrowFactor.blockSignals(False)
        self.cbProportional.blockSignals(True)
        self.cbProportional.setChecked(False)
        self.cbProportional.blockSignals(False)
        self.cbNodeBorder.blockSignals(True)
        self.cbNodeBorder.setChecked(False)
        self.cbNodeBorder.blockSignals(False)
        self.btBgColor.setStyleSheet("")
        self.btBgColor.setText(QCoreApplication.translate("QGISRedResultsDock", "No color"))
        self.btClearBgColor.setEnabled(False)

        self._applyBgColor()
        self._saveAppearanceSettings()

        self._reloadResultsWithNewDecimals()
        self._refreshLabelsIfShowing("Node")
        self._refreshLabelsIfShowing("Link")
        node_layer = self._findResultLayer("Node")
        link_layer = self._findResultLayer("Link")
        if node_layer:
            self.applySymbolScaleFactors(node_layer)
        if link_layer:
            self.applySymbolScaleFactors(link_layer)

    # ------------------------------------------------------------------
    # Persistence (XML file in Results/)
    # ------------------------------------------------------------------

    def _appearanceFilePath(self):
        return os.path.join(self.getResultsPath(),
                            f"{self.NetworkName}_Results_Config.cfg")

    def _saveAppearanceSettings(self):
        root = ET.Element("AppearanceConfig")
        ET.SubElement(root, "Labels",
                      fontSize=str(self._labelFontSize),
                      colorByRange="true" if self._labelColorByRange else "false",
                      showId="true" if self._labelShowId else "false")
        dec_elem = ET.SubElement(root, "Decimals")
        for var_name, val in self._varDecimals.items():
            ET.SubElement(dec_elem, "Var", name=var_name, value=str(val))
        ET.SubElement(root, "Symbols",
                      pipeFactor=str(self._pipeFactor),
                      symbolFactor=str(self._symbolFactor),
                      arrowFactor=str(self._arrowFactor),
                      proportional="true" if self._proportional else "false",
                      nodeBorder="true" if self._nodeBorder else "false")
        ET.SubElement(root, "Background",
                      color=self._bgColor.name() if self._bgColor else "")
        with suppress(Exception):
            path = self._appearanceFilePath()
            ET.indent(root)
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def loadAppearanceSettings(self):
        path = self._appearanceFilePath()
        if os.path.isfile(path):
            with suppress(Exception):
                tree = ET.parse(path)  # nosec B314 — local file written by this plugin, not user input
                root = tree.getroot()

                labels = root.find("Labels")
                if labels is not None:
                    self._labelFontSize = int(labels.get("fontSize", 10))
                    self._labelColorByRange = labels.get("colorByRange", "false") == "true"
                    self._labelShowId = labels.get("showId", "false") == "true"

                dec_elem = root.find("Decimals")
                if dec_elem is not None:
                    for var_elem in dec_elem.findall("Var"):
                        name = var_elem.get("name", "")
                        val = var_elem.get("value", "")
                        if name and val:
                            with suppress(ValueError):
                                self._varDecimals[name] = int(val)

                symbols = root.find("Symbols")
                if symbols is not None:
                    self._pipeFactor = float(symbols.get("pipeFactor", 1.0))
                    self._symbolFactor = float(symbols.get("symbolFactor", 1.0))
                    self._arrowFactor = float(symbols.get("arrowFactor", 1.0))
                    self._proportional = symbols.get("proportional", "false") == "true"
                    self._nodeBorder = symbols.get("nodeBorder", "false") == "true"

                bg = root.find("Background")
                if bg is not None:
                    bg_hex = bg.get("color", "")
                    self._bgColor = QColor(bg_hex) if bg_hex else None

        # Always update widgets for current state (with or without saved file)
        self.spFontSize.blockSignals(True)
        self.spFontSize.setValue(self._labelFontSize)
        self.spFontSize.blockSignals(False)
        self.rbColorByRange.blockSignals(True)
        self.rbColorByRange.setChecked(self._labelColorByRange)
        self.rbColorBlack.setChecked(not self._labelColorByRange)
        self.rbColorByRange.blockSignals(False)
        self.cbShowId.setChecked(self._labelShowId)
        node_field = self._node_field_map.get(self.cbNodes.currentText(), "")
        self._resetDecimalsForVariable(node_field, "Nodes", "Node")
        link_field = self._link_field_map.get(self.cbLinks.currentText(), "")
        self._resetDecimalsForVariable(link_field, "Links", "Link")
        self.dspPipeFactor.blockSignals(True)
        self.dspPipeFactor.setValue(self._pipeFactor)
        self.dspPipeFactor.blockSignals(False)
        self.dspSymbolFactor.blockSignals(True)
        self.dspSymbolFactor.setValue(self._symbolFactor)
        self.dspSymbolFactor.blockSignals(False)
        self.dspArrowFactor.blockSignals(True)
        self.dspArrowFactor.setValue(self._arrowFactor)
        self.dspArrowFactor.blockSignals(False)
        self.cbProportional.blockSignals(True)
        self.cbProportional.setChecked(self._proportional)
        self.cbProportional.blockSignals(False)
        self.cbNodeBorder.blockSignals(True)
        self.cbNodeBorder.setChecked(self._nodeBorder)
        self.cbNodeBorder.blockSignals(False)
        if self._bgColor:
            self.btBgColor.setStyleSheet(f"background-color: {self._bgColor.name()};")
            self.btBgColor.setText(self._bgColor.name())
            self.btClearBgColor.setEnabled(True)
            self._applyBgColor()

        # Apply restored settings to open layers
        node_layer = self._findResultLayer("Node")
        link_layer = self._findResultLayer("Link")
        if node_layer:
            self.applySymbolScaleFactors(node_layer)
            self.updateLabels("Node")
        if link_layer:
            self.applySymbolScaleFactors(link_layer)
            self.updateLabels("Link")

        self._updateAppearanceEnablement()
