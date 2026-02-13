# -*- coding: utf-8 -*-

from PyQt5.QtGui import QColor, QPixmap, QPainter, QIcon
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QLabel, QVBoxLayout, QStyle
from PyQt5.QtWidgets import QToolButton, QComboBox, QApplication, QStylePainter, QStyleOptionComboBox
from PyQt5.QtCore import pyqtSignal, Qt, QEvent, QSize, QObject, QPoint, QItemSelectionModel, QItemSelection

from qgis.gui import QgsSymbolButton, QgsColorDialog
from qgis.core import QgsMarkerSymbol, QgsLineSymbol, QgsFillSymbol, QgsColorRamp

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
        else:
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