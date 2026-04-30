import json

from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import (
    QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog, QToolBar, QMenu,
)
from PyQt6.QtCore import Qt


class TableEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list[list[str]] = [[]]
        self._headers: list[str] = ["Столбец 1"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QToolBar()
        add_row_btn = QPushButton("+ Строка")
        add_row_btn.clicked.connect(self._add_row)
        toolbar.addWidget(add_row_btn)

        add_col_btn = QPushButton("+ Столбец")
        add_col_btn.clicked.connect(self._add_column)
        toolbar.addWidget(add_col_btn)

        del_row_btn = QPushButton("- Строка")
        del_row_btn.clicked.connect(self._del_row)
        toolbar.addWidget(del_row_btn)

        del_col_btn = QPushButton("- Столбец")
        del_col_btn.clicked.connect(self._del_column)
        toolbar.addWidget(del_col_btn)

        layout.addWidget(toolbar)

        self._table = QTableWidget()
        self._table.setObjectName("tableEditor")
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSectionsClickable(True)
        self._table.horizontalHeader().sectionClicked.connect(self._on_header_click)
        self._table.horizontalHeader().setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.horizontalHeader().customContextMenuRequested.connect(self._header_context_menu)
        layout.addWidget(self._table, stretch=1)

        self._rebuild_table()

    def _rebuild_table(self):
        self._table.blockSignals(True)
        self._table.setSortingEnabled(False)
        self._table.setRowCount(len(self._data))
        self._table.setColumnCount(len(self._headers))
        self._table.setHorizontalHeaderLabels(self._headers)

        for r, row in enumerate(self._data):
            for c, val in enumerate(row):
                item = QTableWidgetItem(val)
                self._table.setItem(r, c, item)

        self._table.setSortingEnabled(True)
        self._table.blockSignals(False)

    def _sync_from_table(self):
        self._table.setSortingEnabled(False)
        rows = self._table.rowCount()
        cols = self._table.columnCount()
        self._data = []
        for r in range(rows):
            row = []
            for c in range(cols):
                item = self._table.item(r, c)
                row.append(item.text() if item else "")
            self._data.append(row)
        self._table.setSortingEnabled(True)

    def _add_row(self):
        self._sync_from_table()
        self._data.append([""] * len(self._headers))
        self._rebuild_table()
        self._table.scrollToBottom()

    def _add_column(self):
        self._sync_from_table()
        idx = len(self._headers) + 1
        name, ok = QInputDialog.getText(self, "Новый столбец", "Название:", text=f"Столбец {idx}")
        if not ok:
            return
        self._headers.append(name or f"Столбец {idx}")
        for row in self._data:
            row.append("")
        self._rebuild_table()

    def _del_row(self):
        self._sync_from_table()
        row = self._table.currentRow()
        if row >= 0 and len(self._data) > 1:
            self._data.pop(row)
            self._rebuild_table()
        elif len(self._data) == 1:
            self._data = [[""] * len(self._headers)]
            self._rebuild_table()

    def _del_column(self):
        self._sync_from_table()
        col = self._table.currentColumn()
        if col >= 0 and len(self._headers) > 1:
            self._headers.pop(col)
            for row in self._data:
                if col < len(row):
                    row.pop(col)
            self._rebuild_table()

    def _context_menu(self, pos):
        col = self._table.columnAt(pos.x())
        menu = QMenu(self)

        if col >= 0:
            menu.addAction("Переименовать столбец", lambda: self._rename_column(col))
            menu.addAction("Удалить столбец", lambda: self._del_column_at(col))
            menu.addSeparator()

        row = self._table.rowAt(pos.y())
        menu.addAction("Вставить строку выше", lambda: self._insert_row(max(row, 0)))
        menu.addAction("Вставить строку ниже", lambda: self._insert_row(row + 1 if row >= 0 else len(self._data)))
        menu.addSeparator()
        menu.addAction("Вставить столбец слева", lambda: self._insert_col(max(col, 0)))
        menu.addAction("Вставить столбец справа", lambda: self._insert_col(col + 1 if col >= 0 else len(self._headers)))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_header_click(self, col: int):
        pass

    def _header_context_menu(self, pos):
        col = self._table.horizontalHeader().logicalIndexAt(pos)
        if col < 0:
            return
        menu = QMenu(self)
        menu.addAction("Переименовать столбец", lambda: self._rename_column(col))
        menu.addAction("Удалить столбец", lambda: self._del_column_at(col))
        menu.exec(self._table.horizontalHeader().mapToGlobal(pos))

    def _rename_column(self, col: int):
        self._sync_from_table()
        old_name = self._headers[col] if col < len(self._headers) else ""
        name, ok = QInputDialog.getText(self, "Переименовать", "Название:", text=old_name)
        if ok and name.strip():
            self._headers[col] = name.strip()
            self._rebuild_table()

    def _del_column_at(self, col: int):
        self._sync_from_table()
        if len(self._headers) <= 1:
            return
        self._headers.pop(col)
        for row in self._data:
            if col < len(row):
                row.pop(col)
        self._rebuild_table()

    def _insert_row(self, index: int):
        self._sync_from_table()
        index = max(0, min(index, len(self._data)))
        self._data.insert(index, [""] * len(self._headers))
        self._rebuild_table()

    def _insert_col(self, index: int):
        self._sync_from_table()
        index = max(0, min(index, len(self._headers)))
        idx = len(self._headers) + 1
        name, ok = QInputDialog.getText(self, "Новый столбец", "Название:", text=f"Столбец {idx}")
        if not ok:
            return
        self._headers.insert(index, name or f"Столбец {idx}")
        for row in self._data:
            row.insert(index, "")
        self._rebuild_table()

    def get_content(self) -> bytes:
        self._sync_from_table()
        payload = {"headers": self._headers, "rows": self._data}
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")

    def set_content(self, data: bytes):
        try:
            payload = json.loads(data.decode("utf-8", errors="replace"))
            self._headers = payload.get("headers", ["Столбец 1"])
            self._data = payload.get("rows", [[""]])
        except (json.JSONDecodeError, KeyError):
            self._headers = ["Столбец 1"]
            self._data = [[""]]
        self._rebuild_table()

    def clear(self):
        self._headers = ["Столбец 1"]
        self._data = [[""]]
        self._rebuild_table()
