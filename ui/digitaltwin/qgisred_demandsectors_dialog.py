# -*- coding: utf-8 -*-
from qgis.PyQt.QtCore import QLocale, Qt, QTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from . import demand_sectors_data as ds_data

_REFRESH_DELAY_MS = 300


class QGISRedDemandSectorsDialog(QDialog):
    ProcessDone = False

    def __init__(self, identify, parent=None):
        super().__init__(parent)
        self._identify = identify
        self._identification = None

        self.setWindowTitle(self.tr("Demand sectors"))
        self.setWindowIcon(QIcon(":/images/iconDemandSectors.svg"))
        self.setSizeGripEnabled(True)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(_REFRESH_DELAY_MS)
        self._timer.timeout.connect(self.refresh)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._buildIdentificationTab(), self.tr("Identification"))
        tabs.addTab(QWidget(), self.tr("Analysis"))
        tabs.setTabEnabled(1, False)
        layout.addWidget(tabs, 1)

        buttons = QDialogButtonBox()
        self.btCreate = QPushButton(self.tr("Create sectors"))
        self.btCancel = QPushButton(self.tr("Cancel"))
        buttons.addButton(self.btCreate, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(self.btCancel, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)
        self.btCreate.clicked.connect(self.accept)
        self.btCancel.clicked.connect(self.reject)

        self.resize(640, 480)
        self.refresh()

    def _buildIdentificationTab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        intro = QLabel(self.tr("The sectors are delimited by the active flow meters, counters and level sensors."))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self.sbZLimit = QDoubleSpinBox()
        self.sbZLimit.setDecimals(3)
        self.sbZLimit.setRange(0, 1000000)
        self.sbZLimit.setSingleStep(0.1)
        self.sbZLimit.setValue(0.1)
        self.sbZLimit.valueChanged.connect(lambda _value: self._timer.start())
        form.addRow(self.tr("Demand below which a sector is Z (l/s)"), self.sbZLimit)
        layout.addLayout(form)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            self.tr("Sector"), self.tr("Type"), self.tr("Nodes"), self.tr("Links"), self.tr("Meters"),
            self.tr("Demand (l/s)"),
        ])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.lbSummary = QLabel()
        self.lbSummary.setWordWrap(True)
        layout.addWidget(self.lbSummary)
        return tab

    def options(self):
        return ds_data.build_options(self.sbZLimit.value())

    def kindText(self, kind):
        if kind == ds_data.Z:
            return self.tr("Z (no demand)")
        if kind == ds_data.UNCONTROLLED:
            return self.tr("Uncontrolled")
        return self.tr("Valid")

    def refresh(self):
        self._timer.stop()
        answer = self._identify(self.options())
        self._identification = ds_data.parse_identification(answer)
        if self._identification is None:
            self.table.setRowCount(0)
            self.lbSummary.setText(ds_data.error_message(answer))
        else:
            self._fillTable(self._identification["sectors"])
            summary = self._identification["summary"]
            self.lbSummary.setText(self.tr(
                "{0} valid sectors, {1} Z sectors and {2} uncontrolled sectors (these are not created). "
                "Ignored meters: {3}."
            ).format(summary[ds_data.VALID], summary[ds_data.Z], summary[ds_data.UNCONTROLLED],
                     summary["ignoredMeters"]))
        self.btCreate.setEnabled(ds_data.can_create(self._identification))

    def _fillTable(self, sectors):
        locale = QLocale()
        self.table.setRowCount(len(sectors))
        for row, sector in enumerate(sectors):
            values = [sector["id"], self.kindText(sector["kind"]), str(sector["nodes"]), str(sector["links"]),
                      str(sector["meters"]), locale.toString(sector["demand"], "f", 3)]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column >= 2:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(row, column, item)

    def accept(self):
        if not ds_data.can_create(self._identification):
            return
        self.ProcessDone = True
        super().accept()
