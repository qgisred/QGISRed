# -*- coding: utf-8 -*-
"""Frozen first column for the time-series values table.

Standard Qt "frozen column" pattern: a QTableView overlaid on the left edge of
the real QTableWidget, sharing its model and selection model. The overlay is
purely visual — the dock keeps working against the QTableWidget for everything
(items, selection, clipboard), and rows/selection stay aligned automatically
because both views render the same model.
"""

from qgis.PyQt.QtCore import QEvent, Qt
from qgis.PyQt.QtWidgets import QAbstractItemView, QTableView

FROZEN_COLUMNS = 1


class FrozenColumnOverlay(QTableView):
    """Pins the first column of `table` while the rest scrolls horizontally."""

    def __init__(self, table):
        super(FrozenColumnOverlay, self).__init__(table)
        self._table = table

        self.setModel(table.model())
        self.setSelectionModel(table.selectionModel())
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.verticalHeader().hide()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(table.selectionBehavior())
        self.setSelectionMode(table.selectionMode())
        self.setAlternatingRowColors(table.alternatingRowColors())
        self.setStyleSheet("QTableView { border: none; gridline-color: #c8c8c8; }")

        self.clicked.connect(lambda idx: table.cellClicked.emit(idx.row(), idx.column()))
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._forward_context_menu)

        table.verticalScrollBar().valueChanged.connect(self.verticalScrollBar().setValue)
        self.verticalScrollBar().valueChanged.connect(table.verticalScrollBar().setValue)
        table.horizontalHeader().sectionResized.connect(self._on_column_resized)
        table.verticalHeader().sectionResized.connect(self._on_row_resized)
        table.installEventFilter(self)
        table.horizontalHeader().installEventFilter(self)

        self.refresh()

    def refresh(self) -> None:
        """Re-sync hidden columns, widths, header look and geometry.

        Call after the table contents/headers are rebuilt."""
        model = self._table.model()
        count = int(model.columnCount()) if model is not None else 0
        for col in range(count):
            self.setColumnHidden(col, col >= FROZEN_COLUMNS)
            if col < FROZEN_COLUMNS:
                self.setColumnWidth(col, self._table.columnWidth(col))
        src = self._table.horizontalHeader()
        dst = self.horizontalHeader()
        dst.setFont(src.font())
        dst.setStyleSheet(src.styleSheet())
        dst.setDefaultAlignment(src.defaultAlignment())
        self.verticalHeader().setDefaultSectionSize(self._table.verticalHeader().defaultSectionSize())
        self._update_geometry()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Type.Resize, QEvent.Type.Show):
            if obj is self._table or obj is self._table.horizontalHeader():
                self._update_geometry()
        return False

    def _on_column_resized(self, col, _old, new_size) -> None:
        if int(col) < FROZEN_COLUMNS:
            self.setColumnWidth(int(col), int(new_size))
            self._update_geometry()

    def _on_row_resized(self, row, _old, new_size) -> None:
        self.setRowHeight(int(row), int(new_size))

    def _forward_context_menu(self, pos) -> None:
        target = self._table.viewport().mapFromGlobal(self.viewport().mapToGlobal(pos))
        self._table.customContextMenuRequested.emit(target)

    def _update_geometry(self) -> None:
        t = self._table
        header_h = int(t.horizontalHeader().height())
        if header_h > 0:
            self.horizontalHeader().setFixedHeight(header_h)
        width = sum(t.columnWidth(c) for c in range(FROZEN_COLUMNS))
        frame = t.frameWidth()
        self.setGeometry(frame, frame, width, header_h + t.viewport().height())
