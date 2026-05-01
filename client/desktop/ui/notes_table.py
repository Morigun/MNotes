from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen


_NOTE_TYPE_ICONS = {
    "text": "\U0001f4dd",
    "markdown": "\U0001f4cb",
    "list": "\u2611",
    "audio": "\U0001f3b5",
    "richtext": "\u270f",
    "image": "\U0001f5bc",
    "folder": "\U0001f4c1",
}


def _create_table_icon(size: int = 16) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    pen = QPen(QColor("#89b4fa"), 1.5)
    painter.setPen(pen)
    m = 2
    w = size - 2 * m
    h = size - 2 * m
    painter.drawRect(m, m, w, h)
    painter.drawLine(m + w // 3, m, m + w // 3, m + h)
    painter.drawLine(m + 2 * w // 3, m, m + 2 * w // 3, m + h)
    painter.drawLine(m, m + h // 3, m + w, m + h // 3)
    painter.drawLine(m, m + 2 * h // 3, m + w, m + 2 * h // 3)
    fill = QColor("#89b4fa")
    fill.setAlpha(40)
    painter.fillRect(m + 1, m + 1, w // 3 - 1, h // 3 - 1, fill)
    painter.fillRect(m + w // 3 + 1, m + h // 3 + 1, w // 3 - 1, h // 3 - 1, fill)
    painter.end()
    return pixmap


class NotesTable(QTableWidget):
    note_double_clicked = pyqtSignal(int)
    note_clicked = pyqtSignal(int, bool)
    context_menu_requested = pyqtSignal(int, object)
    remove_from_folder = pyqtSignal(int)
    rename_folder = pyqtSignal(int)
    delete_folder = pyqtSignal(int)

    COL_PIN = 0
    COL_TYPE = 1
    COL_TITLE = 2
    COL_CATEGORY = 3
    COL_PREVIEW = 4
    COL_DATE = 5
    COL_TAGS = 6
    COL_COUNT = 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("notesTable")
        self.setColumnCount(self.COL_COUNT)
        self.setHorizontalHeaderLabels(["\U0001f4cc", "\u0422\u0438\u043f", "\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435", "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f", "\u041f\u0440\u0435\u0432\u044c\u044e", "\u0414\u0430\u0442\u0430", "\u0422\u0435\u0433\u0438"])
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(self.COL_PIN, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.Fixed)
        self.horizontalHeader().setSectionResizeMode(self.COL_TITLE, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(self.COL_CATEGORY, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setSectionResizeMode(self.COL_PREVIEW, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setSectionResizeMode(self.COL_DATE, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setSectionResizeMode(self.COL_TAGS, QHeaderView.ResizeMode.Interactive)
        self.setColumnWidth(self.COL_PIN, 30)
        self.setColumnWidth(self.COL_TYPE, 40)
        self.setColumnWidth(self.COL_CATEGORY, 120)
        self.setColumnWidth(self.COL_PREVIEW, 200)
        self.setColumnWidth(self.COL_DATE, 130)
        self.setColumnWidth(self.COL_TAGS, 120)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(False)
        self._id_to_row: dict[int, int] = {}
        self._row_data: dict[int, dict] = {}
        self._selected_ids: set[int] = set()
        self._table_icon = _create_table_icon(16)
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.cellClicked.connect(self._on_cell_clicked)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def add_note(self, note_id: int, title: str, note_type: str,
                 preview: str = "", is_pinned: bool = False,
                 is_encrypted: bool = False, updated_at: str = "",
                 child_count: int = 0, category_name: str = "",
                 tags: str = "", in_folder: bool = False):
        row = self.rowCount()
        self.insertRow(row)
        self.setRowHeight(row, 32)

        pin_item = QTableWidgetItem("\U0001f4cc" if is_pinned else "")
        pin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        pin_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_PIN, pin_item)

        if note_type == "table":
            type_item = QTableWidgetItem()
            type_item.setData(Qt.ItemDataRole.DecorationRole, self._table_icon)
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            type_item = QTableWidgetItem(_NOTE_TYPE_ICONS.get(note_type, ""))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setItem(row, self.COL_TYPE, type_item)

        title_text = title or "\u0411\u0435\u0437 \u043d\u0430\u0437\u0432\u0430\u043d\u0438\u044f"
        if note_type == "folder" and child_count > 0:
            title_text += f" ({child_count})"
        if is_encrypted:
            title_text += " \U0001f512"
        title_item = QTableWidgetItem(title_text)
        title_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_TITLE, title_item)

        cat_item = QTableWidgetItem(category_name or "\u2014")
        cat_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_CATEGORY, cat_item)

        prev_item = QTableWidgetItem((preview or "")[:80].replace("\n", " "))
        prev_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_PREVIEW, prev_item)

        date_item = QTableWidgetItem(updated_at or "")
        date_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_DATE, date_item)

        tags_item = QTableWidgetItem(tags)
        tags_item.setData(Qt.ItemDataRole.UserRole, note_id)
        self.setItem(row, self.COL_TAGS, tags_item)

        self._id_to_row[note_id] = row
        self._row_data[note_id] = {
            "note_type": note_type,
            "in_folder": in_folder,
        }

    def clear_notes(self):
        self.setRowCount(0)
        self._id_to_row.clear()
        self._row_data.clear()
        self._selected_ids.clear()

    def set_selected(self, note_id: int, selected: bool):
        if note_id not in self._id_to_row:
            return
        if selected:
            self._selected_ids.add(note_id)
        else:
            self._selected_ids.discard(note_id)
        row = self._id_to_row[note_id]
        for col in range(self.COL_COUNT):
            item = self.item(row, col)
            if item:
                if selected:
                    item.setBackground(QColor(137, 180, 250, 40))
                else:
                    item.setBackground(QColor(0, 0, 0, 0))

    def clear_selection(self):
        for nid in list(self._selected_ids):
            self.set_selected(nid, False)
        self._selected_ids.clear()

    def select_all(self):
        for nid in self._id_to_row:
            self.set_selected(nid, True)

    @property
    def note_ids(self) -> set[int]:
        return set(self._id_to_row.keys())

    def _on_cell_double_clicked(self, row: int, _col: int):
        note_id = self._note_id_at_row(row)
        if note_id is not None:
            self.note_double_clicked.emit(note_id)

    def _on_cell_clicked(self, row: int, _col: int):
        note_id = self._note_id_at_row(row)
        if note_id is None:
            return
        ctrl = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
        self.note_clicked.emit(note_id, ctrl)

    def _on_context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row < 0:
            return
        note_id = self._note_id_at_row(row)
        if note_id is None:
            return
        global_pos = self.viewport().mapToGlobal(pos)
        self.context_menu_requested.emit(note_id, global_pos)

    def _note_id_at_row(self, row: int) -> int | None:
        item = self.item(row, self.COL_PIN)
        if item is None:
            return None
        nid = item.data(Qt.ItemDataRole.UserRole)
        return nid if isinstance(nid, int) else None

    def get_note_type(self, note_id: int) -> str:
        data = self._row_data.get(note_id)
        return data["note_type"] if data else ""

    def get_in_folder(self, note_id: int) -> bool:
        data = self._row_data.get(note_id)
        return data.get("in_folder", False) if data else False


from PyQt6.QtWidgets import QApplication
