# -*- coding: utf-8 -*-
"""Values table with the first (time) column fixed during horizontal scroll."""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

_FROZEN_COLUMNS = 1


class TimeSeriesValuesTable(QWidget):
    """Two-pane table: column 0 stays fixed; remaining columns scroll horizontally."""

    customContextMenuRequested = pyqtSignal(object)
    cellClicked = pyqtSignal(int, int)

    frozen_column_count = _FROZEN_COLUMNS

    def __init__(self, parent=None):
        super(TimeSeriesValuesTable, self).__init__(parent)
        self._syncing = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._frozen = QTableWidget(self)
        self._frozen.setObjectName("timeSeriesValuesTableFrozen")
        self._frozen.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._frozen.verticalHeader().setVisible(False)
        self._frozen.setFrameShape(self._frozen.frameShape())

        self._body = QTableWidget(self)
        self._body.setObjectName("timeSeriesValuesTableBody")

        layout.addWidget(self._frozen)
        layout.addWidget(self._body, 1)

        for tbl in (self._frozen, self._body):
            tbl.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            tbl.customContextMenuRequested.connect(self._forward_context_menu)
            tbl.cellClicked.connect(self._on_cell_clicked)

        self._body.verticalScrollBar().valueChanged.connect(self._sync_vertical_scroll_from_body)
        self._frozen.verticalScrollBar().valueChanged.connect(self._sync_vertical_scroll_from_frozen)

        for tbl in (self._frozen, self._body):
            try:
                sm = tbl.selectionModel()
                if sm is not None:
                    sm.selectionChanged.connect(self._on_selection_changed)
            except Exception:
                pass

    def _forward_context_menu(self, pos):
        sender = self.sender()
        if sender is self._body:
            try:
                pos = self._body.viewport().mapTo(self, pos)
            except Exception:
                pass
        elif sender is self._frozen:
            try:
                pos = self._frozen.viewport().mapTo(self, pos)
            except Exception:
                pass
        self.customContextMenuRequested.emit(pos)

    def _on_cell_clicked(self, row: int, col: int) -> None:
        sender = self.sender()
        if sender is self._frozen:
            logical_col = int(col)
        elif sender is self._body:
            logical_col = int(col) + _FROZEN_COLUMNS
        else:
            return
        self.cellClicked.emit(int(row), logical_col)

    def _sync_vertical_scroll_from_body(self, value: int) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            self._frozen.verticalScrollBar().setValue(int(value))
        except Exception:
            pass
        finally:
            self._syncing = False

    def _sync_vertical_scroll_from_frozen(self, value: int) -> None:
        if self._syncing:
            return
        self._syncing = True
        try:
            self._body.verticalScrollBar().setValue(int(value))
        except Exception:
            pass
        finally:
            self._syncing = False

    def _on_selection_changed(self, *_args) -> None:
        if self._syncing:
            return
        sender = self.sender()
        if sender is None:
            return
        try:
            sm = sender.selectionModel()
            if sm is None:
                return
            rows = sorted({int(idx.row()) for idx in sm.selectedIndexes()})
        except Exception:
            return
        self._syncing = True
        try:
            for tbl in (self._frozen, self._body):
                if tbl is sender:
                    continue
                try:
                    tbl.blockSignals(True)
                    tbl.clearSelection()
                    for row in rows:
                        tbl.selectRow(int(row))
                except Exception:
                    pass
                finally:
                    try:
                        tbl.blockSignals(False)
                    except Exception:
                        pass
        finally:
            self._syncing = False

    def _pane_for_column(self, col: int):
        if int(col) < _FROZEN_COLUMNS:
            return self._frozen, int(col)
        return self._body, int(col) - _FROZEN_COLUMNS

    def rowCount(self) -> int:
        try:
            return int(self._body.rowCount())
        except Exception:
            return 0

    def columnCount(self) -> int:
        try:
            return int(self._frozen.columnCount()) + int(self._body.columnCount())
        except Exception:
            return 0

    def setRowCount(self, rows: int) -> None:
        n = int(rows)
        self._frozen.setRowCount(n)
        self._body.setRowCount(n)

    def setColumnCount(self, cols: int) -> None:
        n = max(0, int(cols))
        self._frozen.setColumnCount(min(_FROZEN_COLUMNS, n))
        self._body.setColumnCount(max(0, n - _FROZEN_COLUMNS))

    def setHorizontalHeaderLabels(self, labels) -> None:
        labels = list(labels or [])
        self._frozen.setHorizontalHeaderLabels(labels[:_FROZEN_COLUMNS])
        self._body.setHorizontalHeaderLabels(labels[_FROZEN_COLUMNS:])

    def horizontalHeader(self):
        return self._body.horizontalHeader()

    def verticalHeader(self):
        return self._body.verticalHeader()

    def horizontalHeaderItem(self, col: int):
        pane, local_col = self._pane_for_column(col)
        try:
            return pane.horizontalHeaderItem(local_col)
        except Exception:
            return None

    def item(self, row: int, col: int):
        pane, local_col = self._pane_for_column(col)
        try:
            return pane.item(int(row), local_col)
        except Exception:
            return None

    def setItem(self, row: int, col: int, item) -> None:
        pane, local_col = self._pane_for_column(col)
        try:
            pane.setItem(int(row), local_col, item)
        except Exception:
            pass

    def columnWidth(self, col: int) -> int:
        pane, local_col = self._pane_for_column(col)
        try:
            return int(pane.columnWidth(local_col))
        except Exception:
            return 0

    def resizeColumnsToContents(self) -> None:
        try:
            self._frozen.resizeColumnsToContents()
        except Exception:
            pass
        try:
            self._body.resizeColumnsToContents()
        except Exception:
            pass
        self._sync_row_heights()

    def _sync_row_heights(self) -> None:
        try:
            row_count = int(self.rowCount())
        except Exception:
            return
        for row in range(row_count):
            h = 0
            try:
                h = max(h, int(self._frozen.rowHeight(row)))
            except Exception:
                pass
            try:
                h = max(h, int(self._body.rowHeight(row)))
            except Exception:
                pass
            if h <= 0:
                continue
            try:
                self._frozen.setRowHeight(row, h)
            except Exception:
                pass
            try:
                self._body.setRowHeight(row, h)
            except Exception:
                pass

    def viewport(self):
        return self._body.viewport()

    def selectionModel(self):
        return self._body.selectionModel()

    def has_selection(self) -> bool:
        for tbl in (self._frozen, self._body):
            try:
                sm = tbl.selectionModel()
                if sm is not None and sm.hasSelection():
                    return True
            except Exception:
                pass
        return False

    def selected_logical_rows_and_columns(self):
        try:
            row_count = int(self.rowCount())
            col_count = int(self.columnCount())
        except Exception:
            return [], []
        if row_count <= 0 or col_count <= 0:
            return [], []

        indexes = []
        for tbl, col_offset in ((self._frozen, 0), (self._body, _FROZEN_COLUMNS)):
            try:
                sm = tbl.selectionModel()
                if sm is None:
                    continue
                for idx in sm.selectedIndexes():
                    indexes.append((int(idx.row()), int(idx.column()) + int(col_offset)))
            except Exception:
                continue
        if not indexes:
            return [], []

        rows = sorted({r for r, _c in indexes if 0 <= r < row_count})
        cols = sorted({c for _r, c in indexes if 0 <= c < col_count})
        return rows, cols

    def blockSignals(self, block: bool) -> bool:
        a = super(TimeSeriesValuesTable, self).blockSignals(block)
        try:
            self._frozen.blockSignals(block)
        except Exception:
            pass
        try:
            self._body.blockSignals(block)
        except Exception:
            pass
        return a

    def clearSelection(self) -> None:
        try:
            self._frozen.clearSelection()
        except Exception:
            pass
        try:
            self._body.clearSelection()
        except Exception:
            pass

    def selectRow(self, row: int) -> None:
        self._syncing = True
        try:
            self._frozen.selectRow(int(row))
            self._body.selectRow(int(row))
        except Exception:
            pass
        finally:
            self._syncing = False

    def setCurrentCell(self, row: int, col: int) -> None:
        pane, local_col = self._pane_for_column(col)
        try:
            pane.setCurrentCell(int(row), local_col)
        except Exception:
            pass

    def scrollToItem(self, item, hint=None) -> None:
        if item is None:
            return
        try:
            table = item.tableWidget()
        except Exception:
            table = None
        if table is self._frozen:
            target = self._frozen
        else:
            target = self._body
        try:
            if hint is None:
                target.scrollToItem(item)
            else:
                target.scrollToItem(item, hint)
        except Exception:
            pass

    def frameWidth(self) -> int:
        try:
            return int(self._body.frameWidth())
        except Exception:
            return 0

    def verticalScrollBar(self):
        return self._body.verticalScrollBar()

    def setObjectName(self, name: str) -> None:
        super(TimeSeriesValuesTable, self).setObjectName(name)

    def _apply_to_both(self, attr: str, value) -> None:
        for tbl in (self._frozen, self._body):
            try:
                getattr(tbl, attr)(value)
            except Exception:
                pass

    def setAlternatingRowColors(self, enable: bool) -> None:
        self._apply_to_both("setAlternatingRowColors", enable)

    def setSelectionBehavior(self, behavior) -> None:
        self._apply_to_both("setSelectionBehavior", behavior)

    def setSelectionMode(self, mode) -> None:
        self._apply_to_both("setSelectionMode", mode)

    def setEditTriggers(self, triggers) -> None:
        self._apply_to_both("setEditTriggers", triggers)

    def setSortingEnabled(self, enable: bool) -> None:
        self._apply_to_both("setSortingEnabled", enable)

    def setHorizontalScrollBarPolicy(self, policy) -> None:
        self._body.setHorizontalScrollBarPolicy(policy)

    def setContextMenuPolicy(self, policy) -> None:
        self._apply_to_both("setContextMenuPolicy", policy)

    def setStyleSheet(self, sheet: str) -> None:
        self._apply_to_both("setStyleSheet", sheet)

    def _header_widgets(self):
        return (self._frozen.horizontalHeader(), self._body.horizontalHeader())

    def init_header_style(self, section_style: str, bold: bool = True) -> None:
        for hdr in self._header_widgets():
            try:
                if bold:
                    f = hdr.font()
                    f.setBold(True)
                    hdr.setFont(f)
            except Exception:
                pass
            try:
                hdr.setStyleSheet(section_style)
            except Exception:
                pass
            try:
                hdr.setStretchLastSection(False)
                hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            except Exception:
                pass

    def apply_header_layout(self, align, min_height: int) -> None:
        for hdr in self._header_widgets():
            try:
                hdr.setDefaultAlignment(align)
                hdr.setMinimumHeight(int(min_height))
            except Exception:
                pass
