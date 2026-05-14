# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QHeaderView,
    QMessageBox,
    QTableWidgetItem,
)

formClass, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "qgisred_statistics_manual_breaks_dialog.ui"))


class QGISRedStatisticsManualBreaksDialog(QDialog, formClass):
    def __init__(self, dataMin, dataMax, initialBreaks=None, initialClassCount=5, parent=None):
        super(QGISRedStatisticsManualBreaksDialog, self).__init__(parent)
        self.setupUi(self)
        self.dataMin = float(dataMin) if dataMin is not None else 0.0
        self.dataMax = float(dataMax) if dataMax is not None else 1.0
        if self.dataMax <= self.dataMin:
            self.dataMax = self.dataMin + 1.0
        self.resultBreaks = []
        self.applyWhiteStyle()
        self.tableBreaks.setColumnCount(2)
        self.tableBreaks.setHorizontalHeaderLabels([self.tr("Lower"), self.tr("Upper")])
        header = self.tableBreaks.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tableBreaks.verticalHeader().setVisible(True)
        self.spinClasses.valueChanged.connect(self.onClassCountChanged)
        self.btReset.clicked.connect(self.resetToEqualInterval)
        self.tableBreaks.itemChanged.connect(self.onCellChanged)
        self.suspendItemChanged = False

        if initialBreaks and len(initialBreaks) >= 2:
            self.spinClasses.blockSignals(True)
            self.spinClasses.setValue(len(initialBreaks) - 1)
            self.spinClasses.blockSignals(False)
            self.populateTable(list(initialBreaks))
        else:
            self.spinClasses.blockSignals(True)
            self.spinClasses.setValue(int(initialClassCount) or 5)
            self.spinClasses.blockSignals(False)
            self.resetToEqualInterval()

    def applyWhiteStyle(self):
        whiteStyle = (
            "QSpinBox, QDoubleSpinBox { background-color: white; }"
            "QLineEdit { background-color: white; }"
            "QTableWidget { background-color: white; }"
        )
        self.setStyleSheet(whiteStyle)

    def onClassCountChanged(self):
        self.resetToEqualInterval()

    def resetToEqualInterval(self):
        numClasses = self.spinClasses.value()
        step = (self.dataMax - self.dataMin) / float(numClasses)
        edges = [self.dataMin + i * step for i in range(numClasses + 1)]
        edges[-1] = self.dataMax
        self.populateTable(edges)

    def populateTable(self, edges):
        self.suspendItemChanged = True
        numClasses = len(edges) - 1
        self.tableBreaks.setRowCount(numClasses)
        for i in range(numClasses):
            lowerItem = QTableWidgetItem(self.formatNumber(edges[i]))
            upperItem = QTableWidgetItem(self.formatNumber(edges[i + 1]))
            lowerItem.setData(Qt.ItemDataRole.UserRole, float(edges[i]))
            upperItem.setData(Qt.ItemDataRole.UserRole, float(edges[i + 1]))
            self.tableBreaks.setItem(i, 0, lowerItem)
            self.tableBreaks.setItem(i, 1, upperItem)
        self.suspendItemChanged = False

    def onCellChanged(self, item):
        if self.suspendItemChanged:
            return
        row = item.row()
        column = item.column()
        try:
            newValue = float(item.text())
        except (TypeError, ValueError):
            stored = item.data(Qt.ItemDataRole.UserRole)
            self.suspendItemChanged = True
            item.setText(self.formatNumber(stored if stored is not None else 0.0))
            self.suspendItemChanged = False
            return
        item.setData(Qt.ItemDataRole.UserRole, newValue)
        self.suspendItemChanged = True
        if column == 1 and row + 1 < self.tableBreaks.rowCount():
            nextItem = self.tableBreaks.item(row + 1, 0)
            if nextItem is not None:
                nextItem.setText(self.formatNumber(newValue))
                nextItem.setData(Qt.ItemDataRole.UserRole, newValue)
        elif column == 0 and row > 0:
            prevItem = self.tableBreaks.item(row - 1, 1)
            if prevItem is not None:
                prevItem.setText(self.formatNumber(newValue))
                prevItem.setData(Qt.ItemDataRole.UserRole, newValue)
        self.suspendItemChanged = False

    def collectEdges(self):
        edges = []
        for row in range(self.tableBreaks.rowCount()):
            lowerItem = self.tableBreaks.item(row, 0)
            if lowerItem is None:
                return None
            try:
                edges.append(float(lowerItem.text()))
            except (TypeError, ValueError):
                return None
        lastUpper = self.tableBreaks.item(self.tableBreaks.rowCount() - 1, 1)
        if lastUpper is None:
            return None
        try:
            edges.append(float(lastUpper.text()))
        except (TypeError, ValueError):
            return None
        return edges

    def accept(self):
        edges = self.collectEdges()
        if edges is None or len(edges) < 2:
            QMessageBox.warning(self, self.tr("Invalid breaks"), self.tr("Each row must contain numeric Lower and Upper values."))
            return
        for i in range(len(edges) - 1):
            if edges[i + 1] < edges[i]:
                QMessageBox.warning(
                    self,
                    self.tr("Invalid breaks"),
                    self.tr("Class edges must be in non-decreasing order."),
                )
                return
        self.resultBreaks = edges
        super().accept()

    def getBreaks(self):
        return list(self.resultBreaks)

    def getClassCount(self):
        return self.spinClasses.value()

    def formatNumber(self, value):
        try:
            numericValue = float(value)
        except (TypeError, ValueError):
            return str(value)
        if numericValue == int(numericValue) and abs(numericValue) < 1e9:
            return str(int(numericValue))
        return "{:g}".format(numericValue)
