# -*- coding: utf-8 -*-

# Third-party imports
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, 
                             QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, 
                             QToolButton)
from PyQt5.QtCore import pyqtSignal, Qt, QEvent

from qgis.gui import QgsSymbolButton, QgsColorDialog
from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsSymbol

class RangeEditDialog(QDialog):
    def __init__(self, lowerValue, upperValue, parent=None):
        """Constructor."""
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Range"))
        self.initUi(lowerValue, upperValue)

    def initUi(self, lower, upper):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(self.tr("Lower Value:")))
        self.lowerSpinBox = self.createSpinBox(lower)
        layout.addWidget(self.lowerSpinBox)

        layout.addWidget(QLabel(self.tr("Upper Value:")))
        self.upperSpinBox = self.createSpinBox(upper)
        layout.addWidget(self.upperSpinBox)

        self.setupButtons(layout)

    def createSpinBox(self, value):
        """Factory method for consistent spinboxes."""
        sb = QDoubleSpinBox()
        sb.setRange(-1e12, 1e12)
        sb.setDecimals(4)
        sb.setValue(value)
        return sb

    def setupButtons(self, layout):
        """Add dialog buttons."""
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def getValues(self):
        """Return current bounds."""
        return self.lowerSpinBox.value(), self.upperSpinBox.value()


class SymbolColorSelector(QgsSymbolButton):
    colorChanged = pyqtSignal(QColor)

    def __init__(self, parent=None, geometryHint="fill", initialColor=None, allowAlpha=True, dialogTitle="Pick color", doubleClickOnly=False):
        """Constructor."""
        super().__init__(parent)
        self._geometryHint = self.clampGeometry(geometryHint)
        self._allowAlpha = bool(allowAlpha)
        self._dialogTitle = dialogTitle
        self._doubleClickOnly = doubleClickOnly
        self._color = QColor(initialColor) if (initialColor and initialColor.isValid()) else QColor(19, 125, 220, 255)
        self.symbolSize = 0.0 # Track internal size state

        self.configUi()
        self.applySymbol()
        self.installEventFilter(self)

    def configUi(self):
        """Configure widget appearance."""
        self.setPopupMode(QToolButton.DelayedPopup)
        self.setStyleSheet("""
            QToolButton::menu-indicator { image: none; width: 0px; }
            QToolButton { padding-right: 4px; background-color: transparent; border: none; }
        """)
        self.setToolTip(self.tr("Click to pick a color."))
        try: self.setGraphicsEffect(None)
        except: pass

    def clampGeometry(self, geom):
        """Normalize geometry hint string."""
        g = (geom or "").strip().lower()
        if g in ("point", "marker", "pts"): return "marker"
        if g in ("line", "polyline", "ln"): return "line"
        return "fill"

    def applySymbol(self):
        """Generate and apply QgsSymbol based on current state."""
        sym = self.createSymbol(self._geometryHint, self._color)
        if self.symbolSize > 0:
            self.applySizeToSymbol(sym, self.symbolSize, self._geometryHint == "line")
        self.setSymbol(sym)

    def createSymbol(self, geomType, color):
        """Factory method for QgsSymbol types."""
        rgba = f"{color.red()},{color.green()},{color.blue()},{color.alpha()}"
        if geomType == "marker":
            return QgsMarkerSymbol.createSimple({
                "name": "circle", "color": rgba, "outline_color": "0,0,0,255", "outline_width": "0.2"
            })
        elif geomType == "line":
            return QgsLineSymbol.createSimple({"color": rgba, "width": "0.8"})
        return QgsFillSymbol.createSimple({
            "color": rgba, "outline_color": "60,60,60,255", "outline_width": "0.3"
        })

    def applySizeToSymbol(self, symbol, size, isWidth):
        """Apply size/width to a symbol instance."""
        if isWidth: symbol.setWidth(size)
        else: symbol.setSize(size)

    def updateSymbolSize(self, size, isWidth=False):
        """External API to update size and refresh preview."""
        if size <= 0: return
        self.symbolSize = size
        current = self.symbol()
        if current:
            newSym = current.clone()
            self.applySizeToSymbol(newSym, size, isWidth)
            self.setSymbol(newSym)

    def setColor(self, color):
        """Set color and emit signal."""
        if not isinstance(color, QColor) or not color.isValid() or color == self._color: return
        self._color = QColor(color)
        self.applySymbol()
        self.colorChanged.emit(self._color)

    def color(self):
        return QColor(self._color)

    def setGeometryHint(self, hint):
        self._geometryHint = self.clampGeometry(hint)
        self.applySymbol()

    def geometryHint(self):
        return self._geometryHint

    def setAllowAlpha(self, allowed):
        self._allowAlpha = bool(allowed)

    def eventFilter(self, obj, event):
        """Intercept click events to show simple color dialog."""
        if obj is self:
            if event.type() == QEvent.Wheel: return True
            
            if self._doubleClickOnly:
                # In double-click mode, ignore single clicks but accept double clicks
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    return True # Consume single click
                if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
                    self.openColorDialog()
                    return True
            else:
                # Default behavior: Open on single click
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.openColorDialog()
                    return True
        return super().eventFilter(obj, event)

    def openColorDialog(self):
        """Show QGIS color picker."""
        chosen = QgsColorDialog.getColor(self._color, self, self._dialogTitle, self._allowAlpha)
        if chosen.isValid(): self.setColor(chosen)


class SymbolColorSelectorWithCheckbox(QWidget):
    colorChanged = pyqtSignal(QColor)
    enabledChanged = pyqtSignal(bool)

    def __init__(self, parent=None, geometryHint="fill", initialColor=None, allowAlpha=True, dialogTitle="Pick color", checked=True, checkboxLabel=""):
        """Constructor."""
        super().__init__(parent)
        self.initUi(geometryHint, initialColor, allowAlpha, dialogTitle, checked, checkboxLabel)

    def initUi(self, geom, color, alpha, title, checked, label):
        """Initialize layout and widgets."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.checkbox = QCheckBox(label, self)
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self.enabledChanged.emit)

        # Enable double-click only mode for the color selector
        self.colorSelector = SymbolColorSelector(self, geom, color, alpha, title, doubleClickOnly=True)
        self.colorSelector.colorChanged.connect(self.colorChanged.emit)
        self.colorSelector.setFixedSize(30, 20)

        layout.addWidget(self.checkbox, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        layout.addWidget(self.colorSelector, 0, Qt.AlignVCenter | Qt.AlignHCenter)

    # --- Proxy Methods ---
    def isChecked(self): return self.checkbox.isChecked()
    def setChecked(self, val): self.checkbox.setChecked(val)
    def color(self): return self.colorSelector.color()
    def setColor(self, val): self.colorSelector.setColor(val)
    def setGeometryHint(self, val): self.colorSelector.setGeometryHint(val)
    def geometryHint(self): return self.colorSelector.geometryHint()
    def setAllowAlpha(self, val): self.colorSelector.setAllowAlpha(val)
    def updateSymbolSize(self, s, w=False): self.colorSelector.updateSymbolSize(s, w)
    def setCheckboxLabel(self, val): self.checkbox.setText(val)