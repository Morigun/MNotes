from database.models import Note
from database.repository import Repository
from database.db_manager import DB_PATH
from ui.note_card import NoteCard
from ui.detail_dialog import DetailDialog
from ui.sidebar import Sidebar
from ui.search_bar import SearchBar
from ui.notes_grid import FlowLayout

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea,
    QToolBar, QStatusBar, QPushButton, QMenu, QLabel, QInputDialog, QMessageBox,
    QApplication, QFileDialog, QFrame,
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
        self._selected_ids: set[int] = set()
        self._current_filter: dict = {}
        self._current_parent: int = 0
        self._nav_stack: list[int] = []

        self._setup_ui()
        self._setup_menu_bar()
        self._init_theme_state()
        self._setup_actions()
        self._load_plugins()
        self._apply_titlebar()
        self._load_notes()

    def _is_dark_theme(self) -> bool:
        from main import current_theme
        return current_theme() == "dark"

    def _apply_titlebar(self):
        from main import apply_titlebar_theme
        apply_titlebar_theme(self, self._is_dark_theme())

    def _exec_dialog(self, dialog):
        from main import apply_titlebar_theme
        apply_titlebar_theme(dialog, self._is_dark_theme())
        return dialog.exec()

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
        self._breadcrumb_layout.setContentsMargins(0, 6, 12, 0)

        self._back_btn = QPushButton("← Назад")
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setVisible(False)
        self._breadcrumb_layout.addWidget(self._back_btn)
        self._breadcrumb_layout.addSpacing(4)

        self._breadcrumb_label = QLabel("Все заметки")
        self._breadcrumb_label.setObjectName("cardTitle")
        self._breadcrumb_layout.addWidget(self._breadcrumb_label)
        self._breadcrumb_layout.addStretch()
        right_layout.addLayout(self._breadcrumb_layout)
        right_layout.addSpacing(6)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)
        scroll.setObjectName("notesGrid")
        self._grid_container = QWidget()
        self._grid_container.setObjectName("gridContainer")
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
        self._selected_ids.clear()

    def _on_card_clicked(self, note_id: int, ctrl: bool):
        if ctrl:
            if note_id in self._selected_ids:
                self._selected_ids.discard(note_id)
            else:
                self._selected_ids.add(note_id)
        else:
            self._selected_ids.clear()
            self._selected_ids.add(note_id)
        self._update_card_selections()

    def _update_card_selections(self):
        for card in self._cards:
            card.set_selected(card.note_id in self._selected_ids)

    def _clear_selection(self):
        self._selected_ids.clear()
        self._update_card_selections()

    def _select_all(self):
        self._selected_ids = {c.note_id for c in self._cards}
        self._update_card_selections()

    def _card_by_id(self, note_id: int) -> NoteCard | None:
        return next((c for c in self._cards if c.note_id == note_id), None)

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
            card.clicked.connect(self._on_card_clicked)
            card.context_menu_requested.connect(self._on_card_context_menu)
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

    def _on_card_context_menu(self, note_id: int, pos):
        if note_id not in self._selected_ids:
            self._selected_ids.clear()
            self._selected_ids.add(note_id)
            self._update_card_selections()

        menu = QMenu(self)
        ids = list(self._selected_ids)
        folders_in_sel = sum(
            1 for c in self._cards if c.note_id in self._selected_ids and c.note_type == "folder"
        )
        in_folder_in_sel = sum(
            1 for c in self._cards if c.note_id in self._selected_ids and c._in_folder
        )

        if len(ids) == 1:
            menu.addAction("Открыть", lambda: self._open_selected())
        else:
            menu.addAction(f"Открыть все ({len(ids)})", lambda: self._open_selected())

        if len(ids) == 1 and folders_in_sel == 1:
            menu.addAction("Переименовать", lambda: self._rename_folder(ids[0]))

        menu.addAction(
            "Закрепить / Открепить" if len(ids) == 1 else f"Закрепить / Открепить ({len(ids)})",
            self._toggle_pin_selected,
        )

        del_label = "В корзину" if len(ids) == 1 else f"В корзину ({len(ids)})"
        menu.addAction(del_label, lambda: self._delete_items(ids))

        if in_folder_in_sel > 0:
            menu.addSeparator()
            if in_folder_in_sel == 1:
                nid = next(c.note_id for c in self._cards if c.note_id in self._selected_ids and c._in_folder)
                menu.addAction("Убрать из папки", lambda: self._remove_from_folder(nid))
            else:
                menu.addAction(f"Убрать из папки ({in_folder_in_sel})", lambda: self._remove_selected_from_folder())

        menu.exec(pos)

    def _remove_selected_from_folder(self):
        for card in self._cards:
            if card.note_id in self._selected_ids and card._in_folder:
                self._repo.remove_note_from_folder(card.note_id)
        self._load_notes()

    def _delete_folder(self, folder_id: int):
        self._delete_items([folder_id])

    def _delete_selected(self):
        if not self._selected_ids:
            return
        self._delete_items(list(self._selected_ids))

    def _delete_items(self, ids: list[int]):
        if not ids:
            return

        folders = []
        notes = []
        for nid in ids:
            n = self._repo.get_note(nid)
            if n and n.type == "folder":
                folders.append(n)
            elif n:
                notes.append(n)

        parts = []
        if notes:
            parts.append(f"{len(notes)} замет(ок)" if len(notes) > 1 else "заметку")
        if folders:
            parts.append(f"{len(folders)} пап(ок)" if len(folders) > 1 else "папку")
        msg = f"Удалить {' и '.join(parts)}?\n"
        if folders:
            msg += "Папки будут удалены навсегда, содержимое — перенесено в корзину.\n"
        if notes:
            msg += "Заметки будут перенесены в корзину."

        reply = QMessageBox.question(
            self, "Удаление", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for folder in folders:
            base_path = self._folder_path(folder.id)
            self._delete_folder_permanent(folder.id, base_path)
        for n in notes:
            self._repo.soft_delete_note(n.id)

        self._selected_ids.clear()
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
        self._exec_dialog(dialog)
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
        if self._exec_dialog(dialog):
            self._load_notes()

    def _show_calendar(self):
        from ui.calendar_widget import CalendarWidget
        dialog = CalendarWidget(self._repo, parent=self)
        if self._exec_dialog(dialog):
            if dialog.selected_date:
                self._current_filter = {"date": dialog.selected_date}
                self._load_notes()

    def _show_export(self):
        from ui.export_dialog import ExportDialog
        dialog = ExportDialog(self._repo, parent=self)
        self._exec_dialog(dialog)
        self._load_notes()

    def _setup_menu_bar(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("Файл")

        import_action = file_menu.addAction("Импорт...")
        import_action.triggered.connect(self._show_import)
        export_action = file_menu.addAction("Экспорт...")
        export_action.triggered.connect(self._show_export)
        file_menu.addSeparator()
        backup_action = file_menu.addAction("Создать резервную копию...")
        backup_action.triggered.connect(self._backup_db)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Выход")
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(QApplication.quit)

        edit_menu = menu_bar.addMenu("Правка")
        select_all_action = edit_menu.addAction("Выделить все")
        select_all_action.setShortcut(QKeySequence("Ctrl+A"))
        select_all_action.triggered.connect(self._select_all)
        deselect_action = edit_menu.addAction("Снять выделение")
        deselect_action.setShortcut(QKeySequence("Escape"))
        deselect_action.triggered.connect(self._clear_selection)
        edit_menu.addSeparator()
        find_replace_action = edit_menu.addAction("Найти и заменить...")
        find_replace_action.setShortcut(QKeySequence("Ctrl+H"))
        find_replace_action.triggered.connect(self._show_find_replace)

        notes_menu = menu_bar.addMenu("Заметки")

        add_menu = notes_menu.addMenu("Добавить")
        for note_type, label in _NOTE_TYPES:
            action = add_menu.addAction(label)
            action.setData(note_type)
            action.triggered.connect(self._on_new_note_action)

        notes_menu.addSeparator()

        self._open_selected_action = notes_menu.addAction("Открыть")
        self._open_selected_action.triggered.connect(self._open_selected)
        self._pin_selected_action = notes_menu.addAction("Закрепить / Открепить")
        self._pin_selected_action.triggered.connect(self._toggle_pin_selected)
        duplicate_action = notes_menu.addAction("Дублировать")
        duplicate_action.setShortcut(QKeySequence("Ctrl+D"))
        duplicate_action.triggered.connect(self._duplicate_selected)
        move_action = notes_menu.addAction("Переместить в папку...")
        move_action.triggered.connect(self._move_to_folder)
        self._delete_selected_action = notes_menu.addAction("В корзину")
        self._delete_selected_action.setShortcut(QKeySequence("Delete"))
        self._delete_selected_action.triggered.connect(self._delete_selected)

        notes_menu.addSeparator()

        all_notes_action = notes_menu.addAction("Все заметки")
        all_notes_action.triggered.connect(self._on_all_notes)
        trash_action = notes_menu.addAction("Корзина...")
        trash_action.triggered.connect(self._show_trash)

        view_menu = menu_bar.addMenu("Вид")
        settings_action = view_menu.addAction("Настройки...")
        settings_action.triggered.connect(self._show_settings)
        view_menu.addSeparator()
        calendar_action = view_menu.addAction("Календарь...")
        calendar_action.triggered.connect(self._show_calendar)
        refresh_action = view_menu.addAction("Обновить")
        refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        refresh_action.triggered.connect(self._load_notes)
        view_menu.addSeparator()
        self._theme_action = view_menu.addAction("Светлая тема")
        self._theme_action.setCheckable(True)
        self._theme_action.triggered.connect(self._toggle_theme)
        self._sidebar_toggle = view_menu.addAction("Боковая панель")
        self._sidebar_toggle.setCheckable(True)
        self._sidebar_toggle.setChecked(True)
        self._sidebar_toggle.triggered.connect(self._toggle_sidebar)

        help_menu = menu_bar.addMenu("Помощь")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self._show_about)

    def _load_plugins(self):
        from plugins.plugin_manager import load_all_plugins
        load_all_plugins()

    def _show_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(parent=self)
        self._exec_dialog(dialog)

    def _init_theme_state(self):
        from main import current_theme
        self._theme_action.setChecked(current_theme() == "light")

    def _open_selected(self):
        for note_id in list(self._selected_ids):
            self._open_note(note_id)

    def _toggle_pin_selected(self):
        for note_id in list(self._selected_ids):
            note = self._repo.get_note(note_id)
            if note:
                note.is_pinned = 0 if note.is_pinned else 1
                self._repo.update_note(note)
        self._load_notes()

    def _backup_db(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Резервная копия", "mnotes_backup.db",
            "SQLite (*.db);;Все файлы (*)",
        )
        if not path:
            return
        import shutil
        try:
            self._repo._conn.execute("PRAGMA wal_checkpoint(FULL)")
            shutil.copy2(str(DB_PATH), path)
            QMessageBox.information(self, "Резервная копия", f"База данных сохранена:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать копию:\n{e}")

    def _move_to_folder(self):
        if not self._selected_ids:
            return
        from ui.folder_picker_dialog import FolderPickerDialog
        exclude = set()
        for nid in self._selected_ids:
            n = self._repo.get_note(nid)
            if n and n.type == "folder":
                exclude.add(n.id)
        dialog = FolderPickerDialog(self._repo, exclude_ids=exclude, parent=self)
        if self._exec_dialog(dialog):
            for nid in list(self._selected_ids):
                if dialog.selected_folder_id == 0:
                    self._repo.remove_note_from_folder(nid)
                else:
                    self._repo.move_note_to_folder(nid, dialog.selected_folder_id)
            self._load_notes()

    def _duplicate_selected(self):
        if not self._selected_ids:
            return
        for nid in list(self._selected_ids):
            self._repo.duplicate_note(nid)
        self._load_notes()

    def _toggle_theme(self, checked: bool):
        theme = "light" if checked else "dark"
        from main import load_theme, set_theme
        set_theme(theme)
        load_theme(QApplication.instance(), theme)
        self._apply_titlebar()

    def _show_find_replace(self):
        text_ids = []
        for nid in self._selected_ids:
            n = self._repo.get_note(nid)
            if n and n.type in ("text", "markdown", "richtext"):
                text_ids.append(nid)
        if not text_ids:
            QMessageBox.information(
                self, "Найти и заменить",
                "Выделите текстовые заметки (текст, Markdown, форматирование).",
            )
            return
        from ui.find_replace_dialog import FindReplaceDialog
        dialog = FindReplaceDialog(self._repo, text_ids, parent=self)
        self._exec_dialog(dialog)
        if dialog.replaced_count > 0:
            self._load_notes()

    def _toggle_sidebar(self, checked: bool):
        self._sidebar.setVisible(checked)

    def _show_about(self):
        QMessageBox.about(
            self, "О программе",
            "<h3>MNotes</h3>"
            "<p>Десктопное приложение для управления заметками.</p>"
            "<p>Поддерживаемые типы: текст, Markdown, форматирование, "
            "списки, таблицы, аудио, изображения, папки.</p>"
            "<p>Шифрование: AES-256-GCM</p>"
        )

    def _show_import(self):
        from ui.export_dialog import ExportDialog
        dialog = ExportDialog(self._repo, parent=self)
        self._exec_dialog(dialog)
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
