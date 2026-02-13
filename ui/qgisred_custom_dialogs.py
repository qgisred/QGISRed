# Third-party imports
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QCheckBox
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from PyQt5.QtWidgets import QToolButton

from qgis.gui import QgsSymbolButton, QgsColorDialog
from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsSymbol


class RangeEditDialog(QDialog):
    """A simple dialog for editing a numeric range (lower and upper bounds)."""
    def __init__(self, lowerValue, upperValue, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Range"))
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self.tr("Lower Value:")))
        self.lowerSpinBox = QDoubleSpinBox()
        self.lowerSpinBox.setRange(-1e12, 1e12)
        self.lowerSpinBox.setDecimals(4)
        self.lowerSpinBox.setValue(lowerValue)
        layout.addWidget(self.lowerSpinBox)

        layout.addWidget(QLabel(self.tr("Upper Value:")))
        self.upperSpinBox = QDoubleSpinBox()
        self.upperSpinBox.setRange(-1e12, 1e12)
        self.upperSpinBox.setDecimals(4)
        self.upperSpinBox.setValue(upperValue)
        layout.addWidget(self.upperSpinBox)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def getValues(self):
        """Returns the current values of the spin boxes."""
        return self.lowerSpinBox.value(), self.upperSpinBox.value()


class SymbolEditDialog(QDialog):
    """Dialog for editing symbol color and size together."""
    def __init__(self, initialColor, initialSize, isWidth=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Symbol"))
        layout = QVBoxLayout(self)

        # Color selection
        colorLayout = QHBoxLayout()
        colorLayout.addWidget(QLabel(self.tr("Color:")))
        self.colorButton = QToolButton()
        self.colorButton.setFixedSize(60, 30)
        self.currentColor = QColor(initialColor)
        self.updateColorButton()
        self.colorButton.clicked.connect(self.pickColor)
        colorLayout.addWidget(self.colorButton)
        colorLayout.addStretch()
        layout.addLayout(colorLayout)

        # Size/Width field
        sizeLabel = self.tr("Width:") if isWidth else self.tr("Size:")
        layout.addWidget(QLabel(sizeLabel))
        self.sizeSpinBox = QDoubleSpinBox()
        self.sizeSpinBox.setRange(0.1, 100.0)
        self.sizeSpinBox.setDecimals(2)
        self.sizeSpinBox.setValue(initialSize)
        layout.addWidget(self.sizeSpinBox)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def updateColorButton(self):
        """Update the color button appearance."""
        self.colorButton.setStyleSheet(f"""
            QToolButton {{
                background-color: rgb({self.currentColor.red()}, {self.currentColor.green()}, {self.currentColor.blue()});
                border: 1px solid #999;
            }}
        """)

    def pickColor(self):
        """Open color picker dialog."""
        chosen = QgsColorDialog.getColor(self.currentColor, self, self.tr("Pick Color"), True)
        if chosen.isValid():
            self.currentColor = chosen
            self.updateColorButton()

    def getValues(self):
        """Returns (color, size) tuple."""
        return self.currentColor, self.sizeSpinBox.value()


class SymbolColorSelector(QgsSymbolButton):
    """
    Internal color selector component used by SymbolColorSelectorWithCheckbox.
    Opens the QGIS color dialog (QgsColorDialog) on click.
    After choosing a color, the preview updates to reflect the selected color.

    Signals:
        colorChanged(QColor)
    """
    colorChanged = pyqtSignal(QColor)

    def __init__(
        self,
        parent=None,
        geometryHint: str = "fill",
        initialColor: QColor = QColor(19, 125, 220, 255),
        allowAlpha: bool = True,
        dialogTitle: str = "Pick color"
    ):
        super().__init__(parent)
        self._geometryHint = self.clampGeometry(geometryHint)
        self._allowAlpha = bool(allowAlpha)
        self._dialogTitle = dialogTitle
        self._color = QColor(initialColor) if initialColor.isValid() else QColor(19, 125, 220, 255)

        self.applySymbol()

        # Remove ▼ QgsSymbolButton Menu and remove shadow property
        self.setPopupMode(QToolButton.DelayedPopup)
        self.setStyleSheet("""
            QToolButton::menu-indicator { image: none; width: 0px; }
            QToolButton { padding-right: 4px; background-color: white; border: none; }
        """)

        # Explicitly remove any drop shadow effect
        try:
            self.setGraphicsEffect(None)
        except:
            pass

        self.setToolTip(self.tr("Click to pick a color."))
        self.installEventFilter(self)

    def setGeometryHint(self, geometryHint: str):
        self._geometryHint = self.clampGeometry(geometryHint)
        self.applySymbol()

    def geometryHint(self) -> str:
        return self._geometryHint

    def setAllowAlpha(self, allowAlpha: bool):
        self._allowAlpha = bool(allowAlpha)

    def color(self) -> QColor:
        return QColor(self._color)

    def setColor(self, color: QColor):
        if not isinstance(color, QColor) or not color.isValid():
            return
        if color == self._color:
            return
        self._color = QColor(color)
        self.applySymbol()
        self.colorChanged.emit(QColor(self._color))

    def updateSymbolSize(self, size: float, isWidth: bool = False):
        """Update the symbol size/width and refresh the preview."""
        if size <= 0:
            return

        currentSymbol = self.symbol()
        if not currentSymbol:
            return

        # Clone the current symbol to modify it
        newSymbol = currentSymbol.clone()

        if isWidth:
            # For lines
            newSymbol.setWidth(size)
        else:
            # For markers and fills
            newSymbol.setSize(size)

        self.setSymbol(newSymbol)

    # --- Internals ---
    def rgbaString(self, c: QColor) -> str:
        return f"{c.red()},{c.green()},{c.blue()},{c.alpha()}"

    def clampGeometry(self, geom: str) -> str:
        g = (geom or "").strip().lower()
        if g in ("point", "marker", "pts"):
            return "marker"
        if g in ("line", "polyline", "ln"):
            return "line"
        return "fill"

    def symbolFromColor(self, geometryHint: str, color: QColor) -> QgsSymbol:
        rgba = self.rgbaString(color)
        if geometryHint == "marker":
            return QgsMarkerSymbol.createSimple({
                "name": "circle",
                "color": rgba,
                "outline_color": "0,0,0,255",
                "outline_width": "0.2"
            })
        elif geometryHint == "line":
            return QgsLineSymbol.createSimple({
                "color": rgba,
                "width": "0.8"
            })
        else:
            return QgsFillSymbol.createSimple({
                "color": rgba,
                "outline_color": "60,60,60,255",
                "outline_width": "0.3"
            })

    def applySymbol(self):
        sym = self.symbolFromColor(self._geometryHint, self._color)
        self.setSymbol(sym)

    def openColorDialog(self):
        chosen = QgsColorDialog.getColor(self._color, self, self._dialogTitle, self._allowAlpha)
        if chosen.isValid():
            self.setColor(chosen)

    # --- Event filter replaces default click to open color dialog ---
    def eventFilter(self, obj, event):
        if obj is self:
            # Block mouse wheel events to prevent accidental size changes
            if event.type() == QEvent.Wheel:
                return True  # Consume the event

            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.openColorDialog()
                return True
        return super().eventFilter(obj, event)


class SymbolColorSelectorWithCheckbox(QWidget):
    """
    A widget combining a checkbox and SymbolColorSelector.
    Mimics QGIS's native symbology interface with enable/disable checkbox.
    
    Signals:
        colorChanged(QColor)
        enabledChanged(bool)
    """
    colorChanged = pyqtSignal(QColor)
    enabledChanged = pyqtSignal(bool)
    
    def __init__(
        self,
        parent=None,
        geometryHint: str = "fill",
        initialColor: QColor = QColor(19, 125, 220, 255),
        allowAlpha: bool = True,
        dialogTitle: str = "Pick color",
        checked: bool = True,
        checkboxLabel: str = ""
    ):
        super().__init__(parent)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Minimal margins for compact size
        layout.setSpacing(2)  # Reduced spacing

        # Create checkbox
        self.checkbox = QCheckBox(checkboxLabel, self)
        self.checkbox.setChecked(checked)
        self.checkbox.toggled.connect(self._onCheckboxToggled)

        # Create the symbol color selector
        self.colorSelector = SymbolColorSelector(
            parent=self,
            geometryHint=geometryHint,
            initialColor=initialColor,
            allowAlpha=allowAlpha,
            dialogTitle=dialogTitle
        )
        self.colorSelector.colorChanged.connect(self.colorChanged.emit)

        # Set smaller fixed size for more compact appearance
        self.colorSelector.setFixedSize(30, 20)

        # Add to layout with vertical and horizontal centering
        layout.addWidget(self.checkbox, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        layout.addWidget(self.colorSelector, 0, Qt.AlignVCenter | Qt.AlignHCenter)
        # Don't add stretch in table cells - it causes the color selector to disappear
    
    def _onCheckboxToggled(self, checked: bool):
        self.enabledChanged.emit(checked)
    
    def isChecked(self) -> bool:
        """Returns whether the checkbox is checked."""
        return self.checkbox.isChecked()
    
    def setChecked(self, checked: bool):
        """Set the checkbox state."""
        self.checkbox.setChecked(checked)
    
    def color(self) -> QColor:
        """Returns the current color."""
        return self.colorSelector.color()
    
    def setColor(self, color: QColor):
        """Set the color."""
        self.colorSelector.setColor(color)
    
    def setGeometryHint(self, geometryHint: str):
        """Set the geometry hint (marker, line, or fill)."""
        self.colorSelector.setGeometryHint(geometryHint)
    
    def geometryHint(self) -> str:
        """Returns the current geometry hint."""
        return self.colorSelector.geometryHint()
    
    def setAllowAlpha(self, allowAlpha: bool):
        """Set whether alpha channel is allowed."""
        self.colorSelector.setAllowAlpha(allowAlpha)
    
    def updateSymbolSize(self, size: float, isWidth: bool = False):
        """Update the symbol size/width and refresh the preview."""
        self.colorSelector.updateSymbolSize(size, isWidth)
    
    def setCheckboxLabel(self, label: str):
        """Set the checkbox label text."""
        self.checkbox.setText(label)