from database.repository import Repository
from database.models import Note

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel,
)
from PyQt6.QtCore import Qt


class TrashView(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self.setWindowTitle("Корзина")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self._list = QListWidget()
        layout.addWidget(self._list, stretch=1)

        btn_row = QHBoxLayout()

        restore_btn = QPushButton("↩ Восстановить")
        restore_btn.clicked.connect(self._restore_selected)
        btn_row.addWidget(restore_btn)

        delete_btn = QPushButton("🗑 Удалить навсегда")
        delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(delete_btn)

        clear_btn = QPushButton("Очистить корзину")
        clear_btn.clicked.connect(self._clear_trash)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self._load()

    def _load(self):
        self._list.clear()
        notes = self._repo.get_notes(is_deleted=1, show_all_parents=True)
        for note in notes:
            label = f"{note.title or 'Без названия'} ({note.type})"
            row_data = self._repo._conn.execute(
                "SELECT deleted_parent_name FROM notes WHERE id=?", (note.id,)
            ).fetchone()
            parent_name = row_data["deleted_parent_name"] if row_data else None
            if parent_name:
                label += f"  ← из папки «{parent_name}»"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            self._list.addItem(item)

    def _get_selected_id(self) -> int | None:
        items = self._list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def _restore_selected(self):
        note_id = self._get_selected_id()
        if note_id is None:
            return

        row = self._repo._conn.execute(
            "SELECT deleted_parent_name FROM notes WHERE id=?", (note_id,)
        ).fetchone()
        path = row["deleted_parent_name"] if row else None

        if path:
            folder_id = self._ensure_folder_path(path)
            self._repo._conn.execute(
                "UPDATE notes SET is_deleted=0, parent_id=?, deleted_parent_name=NULL, updated_at=datetime('now') WHERE id=?",
                (folder_id, note_id),
            )
            self._repo._conn.commit()
        else:
            self._repo.restore_note(note_id)

        self._load()

    def _ensure_folder_path(self, path: str) -> int:
        parts = [p.strip() for p in path.split("/") if p.strip()]
        parent_id = None
        for name in parts:
            if parent_id is None:
                row = self._repo._conn.execute(
                    "SELECT id FROM notes WHERE title=? AND type='folder' AND is_deleted=0 AND parent_id IS NULL",
                    (name,),
                ).fetchone()
            else:
                row = self._repo._conn.execute(
                    "SELECT id FROM notes WHERE title=? AND type='folder' AND is_deleted=0 AND parent_id=?",
                    (name, parent_id),
                ).fetchone()
            if row:
                parent_id = row["id"]
            else:
                parent_id = self._create_folder(name, parent_id)
        return parent_id

    def _create_folder(self, name: str, parent_id: int | None) -> int:
        from database.models import Note as N
        folder = N(type="folder", title=name, parent_id=parent_id)
        return self._repo.create_note(folder)

    def _delete_selected(self):
        note_id = self._get_selected_id()
        if note_id:
            self._repo.delete_note_permanent(note_id)
            self._load()

    def _clear_trash(self):
        self._repo.delete_all_trashed()
        self._load()
