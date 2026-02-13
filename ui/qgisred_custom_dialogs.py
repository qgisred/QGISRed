# -*- coding: utf-8 -*-

from PyQt5.QtGui import QColor, QPixmap, QPainter, QIcon
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QVBoxLayout, QStyle
from PyQt5.QtWidgets import QToolButton, QComboBox, QApplication, QStylePainter, QStyleOptionComboBox
from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QSize, QObject, QPoint, QItemSelectionModel, QItemSelection

from qgis.gui import QgsSymbolButton, QgsColorDialog
from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsColorRamp
from typing import List, Tuple

class QGISRedRangeEditDialog(QDialog):
    def __init__(self, lowerValue, upperValue, parent=None, unitAbbreviation=""):
        super().__init__(parent)

        self.unitAbbreviation = unitAbbreviation
        self.lowerValueSpinBox = self.createRangeSpinBox(lowerValue)
        self.upperValueSpinBox = self.createRangeSpinBox(upperValue)

        self.initializeInterface()

    def initializeInterface(self):
        self.setWindowTitle(self.tr("Edit Range"))
        self.setupLayout()

    def setupLayout(self):
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(self.formatLabelText("Lower Value")))
        layout.addWidget(self.lowerValueSpinBox)

        layout.addWidget(QLabel(self.formatLabelText("Upper Value")))
        layout.addWidget(self.upperValueSpinBox)

        self.addStandardButtons(layout)

    def createRangeSpinBox(self, initialValue):
        spinBox = QDoubleSpinBox()
        spinBox.setRange(-1e12, 1e12)
        spinBox.setDecimals(4)
        spinBox.setValue(initialValue)
        return spinBox

    def formatLabelText(self, baseName):
        if self.unitAbbreviation:
            return self.tr(f"{baseName} ({self.unitAbbreviation}):")
        return self.tr(f"{baseName}:")

    def addStandardButtons(self, layout):
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def getRangeValues(self):
        return self.lowerValueSpinBox.value(), self.upperValueSpinBox.value()

class QGISRedSymbolColorSelector(QgsSymbolButton):
    colorChanged = pyqtSignal(QColor)

    markerType = "marker"
    lineType = "line"
    fillType = "fill"
    defaultRgba = QColor(19, 125, 220, 255)

    def __init__(self, parent=None, geometryHint="fill", initialColor=None,
                 allowAlpha=True, dialogTitle="Pick color", doubleClickOnly=False):
        super().__init__(parent)

        self.geometryType = self.normalizeGeometryHint(geometryHint)
        self.allowAlpha = bool(allowAlpha)
        self.dialogTitle = dialogTitle
        self.useDoubleClick = doubleClickOnly
        self.activeColor = self.parseInitialColor(initialColor)
        self.currentSymbolSize = 0.0

        self.configureWidgetStyle()
        self.refreshSymbolDisplay()
        self.installEventFilter(self)

    def parseInitialColor(self, color):
        if color and isinstance(color, QColor) and color.isValid():
            return QColor(color)
        return QColor(self.defaultRgba)

    def normalizeGeometryHint(self, hint):
        cleanHint = (hint or "").strip().lower()

        if cleanHint in ("point", "marker", "pts"):
            return self.markerType
        if cleanHint in ("line", "polyline", "ln"):
            return self.lineType

        return self.fillType

    def configureWidgetStyle(self):
        self.setPopupMode(QToolButton.DelayedPopup)
        self.setStyleSheet(
            "QToolButton::menu-indicator { image: none; width: 0px; } "
            "QToolButton { padding-right: 4px; background-color: transparent; border: none; }"
        )
        self.setToolTip(self.tr("Click to pick a color."))

    def refreshSymbolDisplay(self):
        symbol = self.createGeometrySpecificSymbol()

        if self.currentSymbolSize > 0:
            self.applySizeScaling(symbol)

        self.setSymbol(symbol)

    def createGeometrySpecificSymbol(self):
        rgbaString = self.getColorRgbaString()

        if self.geometryType == self.markerType:
            return self.createMarkerSymbol(rgbaString)

        if self.geometryType == self.lineType:
            return self.createLineSymbol(rgbaString)

        return self.createFillSymbol(rgbaString)

    def getColorRgbaString(self):
        return f"{self.activeColor.red()},{self.activeColor.green()},{self.activeColor.blue()},{self.activeColor.alpha()}"

    def createMarkerSymbol(self, rgba):
        return QgsMarkerSymbol.createSimple({
            "name": "circle", "color": rgba, "outline_color": "0,0,0,255", "outline_width": "0.2"
        })

    def createLineSymbol(self, rgba):
        return QgsLineSymbol.createSimple({"color": rgba, "width": "0.8"})

    def createFillSymbol(self, rgba):
        return QgsFillSymbol.createSimple({
            "color": rgba, "outline_color": "60,60,60,255", "outline_width": "0.3"
        })

    def applySizeScaling(self, symbol):
        if self.geometryType == self.lineType:
            symbol.setWidth(self.currentSymbolSize)
        elif self.geometryType == self.markerType:
            symbol.setSize(self.currentSymbolSize)

    def updateSymbolSize(self, newSize, isLine=False):
        if newSize > 0:
            self.currentSymbolSize = newSize
            self.refreshSymbolDisplay()

    def setSelectorColor(self, newColor):
        if self.isValidNewColor(newColor):
            self.activeColor = QColor(newColor)
            self.refreshSymbolDisplay()
            self.colorChanged.emit(self.activeColor)

    def isValidNewColor(self, color):
        return isinstance(color, QColor) and color.isValid() and color != self.activeColor

    def eventFilter(self, watched, event):
        if watched is not self:
            return super().eventFilter(watched, event)

        if event.type() == QEvent.Wheel:
            return True

        if self.useDoubleClick:
            return self.handleDoubleClickLogic(event)

        return self.handleSingleClickLogic(event)

    def handleDoubleClickLogic(self, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            return True

        if event.type() == QEvent.MouseButtonDblClick and event.button() == Qt.LeftButton:
            self.openColorPicker()
            return True

        return False

    def handleSingleClickLogic(self, event):
        if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.openColorPicker()
            return True

        return False

    def openColorPicker(self):
        newColor = QgsColorDialog.getColor(self.activeColor, self, self.dialogTitle, self.allowAlpha)
        if newColor.isValid():
            self.setSelectorColor(newColor)

class QGISRedColorRampSelector(QComboBox):
    rampChanged = pyqtSignal(QgsColorRamp)

    preferredWidth = 150
    preferredHeight = 24
    iconWidth = 50
    iconHeight = 16
    arrowPadding = 20

    def __init__(self, parent=None):
        super().__init__(parent)

        self.colorRampCache = {}
        self.activeRampName = None

        self.configureDimensions()
        self.currentIndexChanged.connect(self.onSelectionChanged)

    def configureDimensions(self):
        self.setFixedWidth(self.preferredWidth)
        self.setFixedHeight(self.preferredHeight)
        self.setIconSize(QSize(self.iconWidth, self.iconHeight))

    def paintEvent(self, event):
        painter = QStylePainter(self)
        option = self.prepareStyleOption()

        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)

        self.renderRampPreview(painter)

    def prepareStyleOption(self):
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = ""
        return option

    def renderRampPreview(self, painter):
        ramp = self.getActiveRampClone()
        if not ramp:
            return

        previewRect = self.rect().adjusted(4, 4, -self.arrowPadding - 4, -4)
        if previewRect.isValid():
            gradientPixmap = self.generateGradientPixmap(ramp, previewRect.width(), previewRect.height())
            painter.drawPixmap(previewRect.topLeft(), gradientPixmap)

    def onSelectionChanged(self, index):
        if index < 0:
            return

        name = self.itemData(index)
        if name in self.colorRampCache:
            self.activeRampName = name
            self.rampChanged.emit(self.getActiveRampClone())

    def clearRamps(self):
        self.clear()
        self.colorRampCache.clear()
        self.activeRampName = None

    def addColorRamps(self, ramps):
        for name, ramp in ramps.items():
            self.registerColorRamp(name, ramp)

    def registerColorRamp(self, name, ramp):
        if not isinstance(ramp, QgsColorRamp):
            return

        self.colorRampCache[name] = ramp.clone()
        iconPixmap = self.generateGradientPixmap(ramp, self.iconWidth, self.iconHeight)
        self.addItem(QIcon(iconPixmap), name, name)

        if self.activeRampName is None:
            self.setActiveRampByName(name)

    def setActiveRampByName(self, name):
        if name not in self.colorRampCache:
            return

        self.activeRampName = name
        index = self.findData(name)

        if index >= 0:
            self.updateSelectedIndex(index)

    def updateSelectedIndex(self, index):
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)
        self.rampChanged.emit(self.getActiveRampClone())

    def getActiveRampClone(self):
        if self.activeRampName in self.colorRampCache:
            return self.colorRampCache[self.activeRampName].clone()
        return None

    def generateGradientPixmap(self, ramp, width, height):
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        self.drawRampLines(painter, ramp, width, height)

        painter.end()
        return pixmap

    def drawRampLines(self, painter, ramp, width, height):
        """Iterates through pixels to map the color ramp to a linear gradient."""
        maxWidth = max(1, width - 1)
        for x in range(width):
            painter.setPen(ramp.color(x / maxWidth))
            painter.drawLine(x, 0, x, height)

class QGISRedRowSelectionFilter(QObject):
    def __init__(self, table):
        super().__init__(table)
        self.targetTable = table

    def eventFilter(self, widget, event):
        isFocusEvent = event.type() == QEvent.FocusIn
        isClickEvent = event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton

        if isFocusEvent or isClickEvent:
            self.synchronizeSelectionToWidget(widget)

        return False

    def synchronizeSelectionToWidget(self, widget):
        viewportPosition = widget.mapTo(self.targetTable.viewport(), QPoint(0, 0))
        index = self.targetTable.indexAt(viewportPosition)

        if index.isValid():
            self.executeRowSelection(index)

    def executeRowSelection(self, index):
        selectionCommand = self.determineSelectionCommand()
        rowRange = self.createFullRowSelection(index.row())

        self.targetTable.selectionModel().select(rowRange, selectionCommand)
        self.targetTable.setCurrentIndex(index)
        self.targetTable.viewport().update()

    def determineSelectionCommand(self):
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.ControlModifier:
            return QItemSelectionModel.Toggle
        if modifiers & Qt.ShiftModifier:
            return QItemSelectionModel.Select

        return QItemSelectionModel.ClearAndSelect

    def createFullRowSelection(self, rowIndex):
        model = self.targetTable.model()
        firstColumn = model.index(rowIndex, 0)
        lastColumn = model.index(rowIndex, self.targetTable.columnCount() - 1)
        return QItemSelection(firstColumn, lastColumn)

class QGISRedPaletteEmulator(QObject):
    """Generates interpolated colors for N classes from a customizable palette.

    The algorithm distributes palette colors across the requested number of classes,
    keeping the first palette color as the first class color and the last palette
    color as the last class color. Intermediate colors are interpolated between
    adjacent palette colors.
    """

    paletteChanged = pyqtSignal()
    colorsGenerated = pyqtSignal(list)

    basePalette = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 0),
    ]

    def __init__(self, parent=None, customPrefix: List[Tuple[int, int, int]] = None, useBase: bool = True):
        super().__init__(parent)

        self.colors = []
        self.generatedColors = []

        self.initializePalette(customPrefix, useBase)

    def initializePalette(self, customPrefix, useBase):
        self.colors = []

        if customPrefix:
            self.colors.extend(customPrefix)
        if useBase:
            self.colors.extend(self.basePalette)

    def prepend(self, newColors: List[Tuple[int, int, int]]):
        self.colors = list(newColors) + self.colors
        self.paletteChanged.emit()

    def append(self, newColors: List[Tuple[int, int, int]]):
        self.colors.extend(newColors)
        self.paletteChanged.emit()

    def insert(self, position: int, color: Tuple[int, int, int]):
        self.colors.insert(position, color)
        self.paletteChanged.emit()

    def remove(self, position: int):
        if len(self.colors) > 2:
            self.colors.pop(position)
            self.paletteChanged.emit()

    def reset(self):
        self.colors = list(self.basePalette)
        self.paletteChanged.emit()

    def setPalette(self, newPalette: List[Tuple[int, int, int]]):
        if len(newPalette) >= 2:
            self.colors = list(newPalette)
            self.paletteChanged.emit()

    def setPaletteFromQColors(self, qcolors: List[QColor]):
        if len(qcolors) >= 2:
            self.colors = [(c.red(), c.green(), c.blue()) for c in qcolors if c and c.isValid()]
            if len(self.colors) >= 2:
                self.paletteChanged.emit()

    def getPaletteCount(self):
        return len(self.colors)

    def generate(self, totalClasses: int) -> List[dict]:
        if not self.isValidPalette():
            return []

        if totalClasses < 1:
            return []

        if totalClasses == 1:
            return self.createSingleClassResult()

        self.generatedColors = self.computeInterpolatedColors(totalClasses)
        self.colorsGenerated.emit(self.generatedColors)

        return self.generatedColors

    def isValidPalette(self):
        return len(self.colors) >= 2

    def createSingleClassResult(self):
        firstColor = self.colors[0]
        return [{
            "classIndex": 1,
            "rgb": firstColor,
            "hex": self.rgbToHex(firstColor),
            "qcolor": self.rgbToQColor(firstColor)
        }]

    def computeInterpolatedColors(self, totalClasses):
        paletteSize = len(self.colors)
        results = []

        for classIdx in range(totalClasses):
            if totalClasses == 1:
                position = 0.0
            else:
                position = classIdx / (totalClasses - 1) * (paletteSize - 1)

            lowerIdx = int(position)
            upperIdx = min(lowerIdx + 1, paletteSize - 1)
            fraction = position - lowerIdx

            interpolatedRgb = self.linearInterpolate(
                self.colors[lowerIdx],
                self.colors[upperIdx],
                fraction
            )

            results.append(self.createColorResult(classIdx + 1, interpolatedRgb))

        return results

    def linearInterpolate(self, color1, color2, factor):
        red = int(color1[0] + (color2[0] - color1[0]) * factor)
        green = int(color1[1] + (color2[1] - color1[1]) * factor)
        blue = int(color1[2] + (color2[2] - color1[2]) * factor)

        return (
            self.clampColorValue(red),
            self.clampColorValue(green),
            self.clampColorValue(blue)
        )

    def clampColorValue(self, value):
        return max(0, min(255, value))

    def createColorResult(self, classIndex, rgb):
        return {
            "classIndex": classIndex,
            "rgb": rgb,
            "hex": self.rgbToHex(rgb),
            "qcolor": self.rgbToQColor(rgb)
        }

    def rgbToHex(self, rgb: Tuple[int, int, int]) -> str:
        return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"

    def rgbToQColor(self, rgb: Tuple[int, int, int]) -> QColor:
        return QColor(rgb[0], rgb[1], rgb[2])

    def hexToRgb(self, hexColor: str) -> Tuple[int, int, int]:
        cleanHex = hexColor.lstrip('#')
        return tuple(int(cleanHex[i:i+2], 16) for i in (0, 2, 4))

    def getColorAtIndex(self, index: int) -> dict:
        if not self.generatedColors:
            return None

        adjustedIndex = index - 1
        if 0 <= adjustedIndex < len(self.generatedColors):
            return self.generatedColors[adjustedIndex]

        return None

    def getQColorList(self) -> List[QColor]:
        return [color["qcolor"] for color in self.generatedColors]

    def getRgbList(self) -> List[Tuple[int, int, int]]:
        return [color["rgb"] for color in self.generatedColors]

    def getHexList(self) -> List[str]:
        return [color["hex"] for color in self.generatedColors]