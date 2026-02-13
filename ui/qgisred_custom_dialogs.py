# Third-party imports
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QVBoxLayout
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

class SymbolColorSelector(QgsSymbolButton):
    """
    Looks like a QgsSymbolButton; on click, opens the QGIS color dialog (QgsColorDialog).
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

        # Remove ▼ QgsSymbolButton Menu
        self.setPopupMode(QToolButton.DelayedPopup)
        self.setStyleSheet("""
            QToolButton::menu-indicator { image: none; width: 0px; }
            QToolButton { padding-right: 4px; }  /* optional: tighten right padding */
        """)

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
            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseButtonRelease):
                if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                    self.openColorDialog()
                return True
        return super().eventFilter(obj, event)
