# -*- coding: utf-8 -*-

# Third-party imports
from PyQt5.QtGui import QColor, QPixmap, QPainter, QIcon
from PyQt5.QtWidgets import (QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, 
                             QVBoxLayout, QWidget, QHBoxLayout, QCheckBox, 
                             QToolButton, QPushButton, QMenu, QAction)
from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QSize

from qgis.gui import QgsSymbolButton, QgsColorDialog
from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsSymbol, QgsColorRamp

class RangeEditDialog(QDialog):
    def __init__(self, lowerValue, upperValue, parent=None, unitAbbr=""):
        """Constructor.
        
        Args:
            lowerValue: Initial lower bound value
            upperValue: Initial upper bound value
            parent: Parent widget
            unitAbbr: Unit abbreviation to display (e.g., 'mm', 'm')
        """
        super().__init__(parent)
        self.unitAbbr = unitAbbr
        self.setWindowTitle(self.tr("Edit Range"))
        self.initUi(lowerValue, upperValue)

    def initUi(self, lower, upper):
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        
        # Build label with optional unit suffix
        lowerLabel = self.tr("Lower Value:")
        upperLabel = self.tr("Upper Value:")
        if self.unitAbbr:
            lowerLabel = self.tr(f"Lower Value ({self.unitAbbr}):")
            upperLabel = self.tr(f"Upper Value ({self.unitAbbr}):")
        
        layout.addWidget(QLabel(lowerLabel))
        self.lowerSpinBox = self.createSpinBox(lower)
        layout.addWidget(self.lowerSpinBox)

        layout.addWidget(QLabel(upperLabel))
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


class QGISRedColorRampSelector(QWidget):
    """
    Custom color ramp selector widget that displays only user-defined color ramps.
    Provides a button with gradient preview and dropdown menu for ramp selection.
    """
    
    colorRampChanged = pyqtSignal(QgsColorRamp)
    
    def __init__(self, parent=None):
        """Initialize the custom color ramp selector widget."""
        super(QGISRedColorRampSelector, self).__init__(parent)
        
        # Internal storage
        self._ramps = {}  # {name: QgsColorRamp}
        self._currentRampName = None
        
        # Setup UI
        self._initUi()
    
    def _initUi(self):
        """Initialize the user interface."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create button with dropdown arrow
        self._button = QPushButton(self)
        self._button.setMinimumHeight(24)
        self._button.clicked.connect(self._showRampMenu)
        
        layout.addWidget(self._button)
        
        # Initial display
        self._updateButtonDisplay()
    
    def addColorRamp(self, name, ramp):
        """
        Add a color ramp to the selector.
        
        Args:
            name: Name/identifier for the ramp
            ramp: QgsColorRamp instance
        """
        if not isinstance(ramp, QgsColorRamp):
            return
        
        # Clone the ramp to avoid external modifications
        self._ramps[name] = ramp.clone()
        
        # Set as current if this is the first ramp
        if self._currentRampName is None:
            self.setCurrentRamp(name)
    
    def addColorRamps(self, ramps):
        """
        Add multiple color ramps at once.
        
        Args:
            ramps: Dictionary of {name: QgsColorRamp}
        """
        for name, ramp in ramps.items():
            self.addColorRamp(name, ramp)
    
    def clearRamps(self):
        """Remove all color ramps."""
        self._ramps.clear()
        self._currentRampName = None
        self._updateButtonDisplay()
    
    def removeRamp(self, name):
        """
        Remove a specific color ramp.
        
        Args:
            name: Name of the ramp to remove
        """
        if name in self._ramps:
            del self._ramps[name]
            
            # If we removed the current ramp, select another
            if self._currentRampName == name:
                if self._ramps:
                    self.setCurrentRamp(list(self._ramps.keys())[0])
                else:
                    self._currentRampName = None
                    self._updateButtonDisplay()
    
    def setCurrentRamp(self, name):
        """
        Set the current ramp by name.
        
        Args:
            name: Name of the ramp to select
        """
        if name in self._ramps:
            self._currentRampName = name
            self._updateButtonDisplay()
            
            # Emit signal
            ramp = self.currentRamp()
            if ramp:
                self.colorRampChanged.emit(ramp)
    
    def currentRampName(self):
        """Get the name of the currently selected ramp."""
        return self._currentRampName
    
    def currentRamp(self):
        """Get the currently selected QgsColorRamp instance."""
        if self._currentRampName and self._currentRampName in self._ramps:
            return self._ramps[self._currentRampName].clone()
        return None
    
    def _showRampMenu(self):
        """Display dropdown menu with available color ramps."""
        if not self._ramps:
            return
        
        menu = QMenu(self)
        
        # Sort ramp names alphabetically
        for name in sorted(self._ramps.keys()):
            ramp = self._ramps[name]
            
            # Create gradient preview icon
            icon = self._createRampIcon(ramp, 50, 16)
            
            # Create menu action
            action = QAction(icon, name, self)
            action.triggered.connect(lambda checked, n=name: self.setCurrentRamp(n))
            
            # Mark current selection
            if name == self._currentRampName:
                action.setCheckable(True)
                action.setChecked(True)
            
            menu.addAction(action)
        
        # Show menu below button
        menu.exec_(self._button.mapToGlobal(self._button.rect().bottomLeft()))
    
    def _updateButtonDisplay(self):
        """Update button display with current ramp gradient."""
        if self._currentRampName and self._currentRampName in self._ramps:
            ramp = self._ramps[self._currentRampName]
            
            # Get button size
            width = max(100, self._button.width())
            height = max(20, self._button.height() - 4)
            
            # Create gradient preview
            pixmap = self._renderGradientPreview(ramp, width, height)
            
            # Set as button icon
            self._button.setIcon(QIcon(pixmap))
            self._button.setIconSize(QSize(width, height))
            self._button.setText("")  # Clear text to show only gradient
        else:
            # No ramp selected - show placeholder
            self._button.setIcon(QIcon())
            self._button.setText("No ramp")
    
    def _renderGradientPreview(self, ramp, width, height):
        """
        Render a color ramp as a horizontal gradient.
        
        Args:
            ramp: QgsColorRamp instance
            width: Pixmap width in pixels
            height: Pixmap height in pixels
            
        Returns:
            QPixmap with gradient preview
        """
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(255, 255, 255))
        
        painter = QPainter(pixmap)
        
        # Draw gradient by sampling the ramp
        for x in range(width):
            # Calculate position (0.0 to 1.0)
            t = x / max(1, width - 1)
            
            # Get color from ramp
            color = ramp.color(t)
            
            # Draw vertical line
            painter.setPen(color)
            painter.drawLine(x, 0, x, height)
        
        painter.end()
        
        return pixmap
    
    def _createRampIcon(self, ramp, width, height):
        """
        Create a QIcon with gradient preview for menu items.
        
        Args:
            ramp: QgsColorRamp instance
            width: Icon width in pixels
            height: Icon height in pixels
            
        Returns:
            QIcon with gradient preview
        """
        pixmap = self._renderGradientPreview(ramp, width, height)
        return QIcon(pixmap)