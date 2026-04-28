from database.models import Note
from database.repository import Repository
from ui.note_card import NoteCard
from ui.detail_dialog import DetailDialog
from ui.sidebar import Sidebar
from ui.search_bar import SearchBar
from ui.notes_grid import FlowLayout

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
    QToolBar, QStatusBar, QPushButton, QMenu, QLabel, QInputDialog, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QIcon, QCloseEvent


_NOTE_TYPES = [
    ("text", "Текст"),
    ("markdown", "Markdown"),
    ("list", "Список"),
    ("audio", "Аудио"),
    ("richtext", "Форматирование"),
    ("image", "Изображение"),
    ("table", "Таблица"),
    ("folder", "Папка"),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MNotes")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        self._repo = Repository()
        self._cards: list[NoteCard] = []
        self._current_filter: dict = {}
        self._current_parent: int = 0
        self._nav_stack: list[int] = []

        self._setup_ui()
        self._setup_actions()
        self._load_notes()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.category_selected.connect(self._on_category_selected)
        self._sidebar.tag_selected.connect(self._on_tag_selected)
        self._sidebar.all_notes_selected.connect(self._on_all_notes)
        main_layout.addWidget(self._sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setObjectName("mainToolbar")

        new_btn = QPushButton("＋ Новая")
        new_menu = QMenu(new_btn)
        for note_type, label in _NOTE_TYPES:
            action = new_menu.addAction(label)
            action.setData(note_type)
            action.triggered.connect(self._on_new_note_action)
        new_btn.setMenu(new_menu)
        toolbar.addWidget(new_btn)

        self._search_bar = SearchBar()
        self._search_bar.search_changed.connect(self._on_search)
        toolbar.addWidget(self._search_bar)

        trash_btn = QPushButton("🗑 Корзина")
        trash_btn.clicked.connect(self._show_trash)
        toolbar.addWidget(trash_btn)

        calendar_btn = QPushButton("📅 Календарь")
        calendar_btn.clicked.connect(self._show_calendar)
        toolbar.addWidget(calendar_btn)

        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self._show_export)
        toolbar.addWidget(export_btn)

        right_layout.addWidget(toolbar)

        self._breadcrumb_layout = QHBoxLayout()
        self._breadcrumb_layout.setContentsMargins(12, 6, 12, 0)

        self._back_btn = QPushButton("← Назад")
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setVisible(False)
        self._breadcrumb_layout.addWidget(self._back_btn)

        self._breadcrumb_label = QLabel("Все заметки")
        self._breadcrumb_label.setObjectName("cardTitle")
        self._breadcrumb_layout.addWidget(self._breadcrumb_label)
        self._breadcrumb_layout.addStretch()
        right_layout.addLayout(self._breadcrumb_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setObjectName("notesGrid")
        self._grid_container = QWidget()
        self._flow_layout = FlowLayout(self._grid_container, margin=12, hspacing=12, vspacing=12)
        scroll.setWidget(self._grid_container)
        right_layout.addWidget(scroll)

        main_layout.addWidget(right, stretch=1)

        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._update_status()

    def _clear_cards(self):
        for card in self._cards:
            self._flow_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def _load_notes(self):
        self._clear_cards()
        self._sidebar.refresh()

        filters = dict(self._current_filter)
        filters["parent_id"] = self._current_parent
        notes = self._repo.get_notes(**filters)

        for note in notes:
            preview = self._make_preview(note)
            child_count = 0
            if note.type == "folder":
                child_count = self._repo.get_folder_child_count(note.id)
            card = NoteCard(
                note_id=note.id,
                title=note.title,
                note_type=note.type,
                preview=preview,
                is_pinned=bool(note.is_pinned),
                is_encrypted=bool(note.is_encrypted),
                updated_at=note.updated_at,
                child_count=child_count,
                in_folder=self._current_parent != 0,
            )
            card.double_clicked.connect(self._open_note)
            card.remove_from_folder.connect(self._remove_from_folder)
            card.rename_folder.connect(self._rename_folder)
            card.delete_folder.connect(self._delete_folder)
            self._cards.append(card)
            self._flow_layout.addWidget(card)
        self._update_status()

    def _update_breadcrumb(self):
        if self._current_parent == 0:
            self._breadcrumb_label.setText("Все заметки")
            self._back_btn.setVisible(False)
        else:
            parts = []
            for pid in self._nav_stack:
                if pid == 0:
                    parts.append("Все заметки")
                else:
                    n = self._repo.get_note(pid)
                    parts.append(n.title if n else "Папка")
            current = self._repo.get_note(self._current_parent)
            parts.append(current.title if current else "Папка")
            self._breadcrumb_label.setText(" / ".join(parts))
            self._back_btn.setVisible(True)

    def _go_back(self):
        if self._nav_stack:
            self._current_parent = self._nav_stack.pop()
        else:
            self._current_parent = 0
        self._update_breadcrumb()
        self._load_notes()

    def _open_folder(self, folder_id: int):
        self._nav_stack.append(self._current_parent)
        self._current_parent = folder_id
        self._update_breadcrumb()
        self._load_notes()

    def _remove_from_folder(self, note_id: int):
        self._repo.remove_note_from_folder(note_id)
        self._load_notes()

    def _rename_folder(self, folder_id: int):
        note = self._repo.get_note(folder_id)
        if note is None:
            return
        name, ok = QInputDialog.getText(self, "Переименовать папку", "Название:", text=note.title)
        if ok:
            note.title = name.strip()
            self._repo.update_note(note)
            self._load_notes()

    def _delete_folder(self, folder_id: int):
        child_count = self._repo.get_folder_child_count(folder_id)
        if child_count > 0:
            reply = QMessageBox.question(
                self, "Удалить папку",
                f"В папке {child_count} замет(ок).\n"
                "Папка будет удалена навсегда, заметки — перенесены в корзину.\n\n"
                "Удалить?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        base_path = self._folder_path(folder_id)
        self._delete_folder_permanent(folder_id, base_path)
        self._load_notes()

    def _folder_path(self, folder_id: int) -> str:
        parts = []
        current_id = folder_id
        visited = set()
        while current_id:
            if current_id in visited:
                break
            visited.add(current_id)
            note = self._repo.get_note(current_id)
            if note is None:
                break
            parts.append(note.title or "Папка")
            current_id = note.parent_id
        parts.reverse()
        return "/".join(parts)

    def _delete_folder_permanent(self, folder_id: int, folder_path: str):
        children = self._repo.get_notes(parent_id=folder_id)
        for child in children:
            if child.type == "folder":
                child_path = f"{folder_path}/{child.title or 'Папка'}"
                self._delete_folder_permanent(child.id, child_path)
            else:
                self._repo._conn.execute(
                    "UPDATE notes SET is_deleted=1, deleted_parent_name=?, updated_at=datetime('now') WHERE id=?",
                    (folder_path, child.id),
                )
        self._repo._conn.execute(
            "UPDATE notes SET parent_id=NULL WHERE parent_id=?", (folder_id,)
        )
        self._repo._conn.commit()
        self._repo.delete_note_permanent(folder_id)

    @staticmethod
    def _make_preview(note: Note) -> str:
        if note.type == "folder":
            return "📁 Папка"
        if note.content is None:
            return ""
        if note.type in ("text", "markdown", "richtext"):
            try:
                return note.content.decode("utf-8", errors="replace")[:200]
            except Exception:
                return ""
        if note.type == "list":
            import json
            try:
                items = json.loads(note.content.decode("utf-8", errors="replace"))
                lines = [
                    ("☑ " if it.get("checked") else "☐ ") + it.get("text", "")
                    for it in items[:5]
                ]
                return "\n".join(lines)
            except Exception:
                return ""
        if note.type == "audio":
            return "🎵 Аудиозапись"
        if note.type == "image":
            return "🖼 Изображение"
        if note.type == "table":
            import json
            try:
                payload = json.loads(note.content.decode("utf-8", errors="replace"))
                rows = len(payload.get("rows", []))
                cols = len(payload.get("headers", []))
                return f"▦ {rows}×{cols}"
            except Exception:
                return "▦ Таблица"
        return ""

    def _update_status(self):
        count = self._repo.get_notes(is_deleted=0, show_all_parents=True).__len__()
        loc = "в папке" if self._current_parent != 0 else "всего"
        self._statusbar.showMessage(f"Заметок {loc}: {count}")

    def _on_new_note_action(self):
        action = self.sender()
        if action is None:
            return
        note_type = action.data()
        title = ""
        if note_type == "folder":
            title, ok = QInputDialog.getText(self, "Новая папка", "Название папки:")
            if not ok:
                return
        note = Note(type=note_type, title=title, parent_id=self._current_parent)
        note.id = self._repo.create_note(note)
        if note_type == "folder":
            self._load_notes()
        else:
            self._open_note(note.id)

    def _open_note(self, note_id: int):
        note = self._repo.get_note(note_id)
        if note is None:
            return
        if note.type == "folder":
            self._open_folder(note_id)
            return
        dialog = DetailDialog(note, self._repo, parent=self)
        if dialog.exec():
            self._load_notes()

    def _on_search(self, text: str, note_type: str):
        self._current_filter.pop("search", None)
        self._current_filter.pop("note_type", None)
        if text:
            self._current_filter["search"] = text
        if note_type:
            self._current_filter["note_type"] = note_type
        self._load_notes()

    def _on_category_selected(self, category_id: int):
        self._current_filter = {"category_id": category_id}
        self._load_notes()

    def _on_tag_selected(self, tag_id: int):
        self._current_filter = {"tag_id": tag_id}
        self._load_notes()

    def _on_all_notes(self):
        self._current_filter = {}
        self._current_parent = 0
        self._nav_stack.clear()
        self._update_breadcrumb()
        self._load_notes()

    def _show_trash(self):
        from ui.trash_view import TrashView
        dialog = TrashView(self._repo, parent=self)
        if dialog.exec():
            self._load_notes()

    def _show_calendar(self):
        from ui.calendar_widget import CalendarWidget
        dialog = CalendarWidget(self._repo, parent=self)
        if dialog.exec():
            if dialog.selected_date:
                self._current_filter = {"date": dialog.selected_date}
                self._load_notes()

    def _show_export(self):
        from ui.export_dialog import ExportDialog
        dialog = ExportDialog(self._repo, parent=self)
        dialog.exec()
        self._load_notes()

    def _setup_actions(self):
        new_text_action = QAction("Новая текстовая заметка", self)
        new_text_action.setShortcut(QKeySequence("Ctrl+N"))
        new_text_action.triggered.connect(lambda: self._create_note("text"))
        self.addAction(new_text_action)

        search_action = QAction("Поиск", self)
        search_action.setShortcut(QKeySequence("Ctrl+F"))
        search_action.triggered.connect(lambda: self._search_bar.search_input.setFocus())
        self.addAction(search_action)

    def _create_note(self, note_type: str):
        note = Note(type=note_type, title="", parent_id=self._current_parent)
        note.id = self._repo.create_note(note)
        self._open_note(note.id)

    def _restore(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def closeEvent(self, event: QCloseEvent):
        event.ignore()
        self.hide()
