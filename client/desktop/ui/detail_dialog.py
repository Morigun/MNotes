import json
from typing import Optional

from database.models import Note, Category, Tag
from database.repository import Repository
from services.crypto_service import encrypt, decrypt, hash_password, verify_password
from ui.editors.text_editor import TextEditor
from ui.editors.markdown_editor import MarkdownEditor
from ui.editors.list_editor import ListEditor
from ui.editors.audio_editor import AudioEditor
from ui.editors.richtext_editor import RichTextEditor
from ui.editors.image_editor import ImageEditor
from ui.editors.table_editor import TableEditor
from ui.editors.folder_editor import FolderEditor
from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
    QDialogButtonBox, QPushButton, QComboBox, QWidget,
    QInputDialog, QApplication, QDateTimeEdit, QCheckBox,
)
from PyQt6.QtCore import Qt, QTimer, QDateTime


_EDITOR_MAP = {
    "text": TextEditor,
    "markdown": MarkdownEditor,
    "list": ListEditor,
    "audio": AudioEditor,
    "richtext": RichTextEditor,
    "image": ImageEditor,
    "table": TableEditor,
    "folder": FolderEditor,
}


class DetailDialog(QDialog):
    def __init__(self, note: Note, repo: Repository, parent=None):
        super().__init__(parent)
        self._note = note
        self._repo = repo
        self._editor: Optional[BaseEditor] = None
        self._deleted = False
        self._decrypted_content: Optional[bytes] = None

        self.setWindowTitle(note.title or "Новая заметка")
        self.setMinimumSize(700, 500)
        self.resize(900, 650)

        self._setup_ui()
        self._load_note_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title_row = QHBoxLayout()
        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Заголовок заметки")
        title_row.addWidget(self._title_edit)
        layout.addLayout(title_row)

        meta_row = QHBoxLayout()

        self._category_combo = QComboBox()
        self._category_combo.addItem("Без категории", None)
        categories = self._repo.get_all_categories()
        for cat in categories:
            self._category_combo.addItem(cat.name, cat.id)
        meta_row.addWidget(QLabel("Категория:"))
        meta_row.addWidget(self._category_combo)

        self._tag_edit = QLineEdit()
        self._tag_edit.setPlaceholderText("Теги через запятую")
        meta_row.addWidget(QLabel("Теги:"))
        meta_row.addWidget(self._tag_edit)

        layout.addLayout(meta_row)

        reminder_row = QHBoxLayout()
        reminder_row.addWidget(QLabel("Напоминание:"))
        self._reminder_check = QCheckBox()
        self._reminder_check.toggled.connect(self._on_reminder_toggle)
        reminder_row.addWidget(self._reminder_check)

        self._reminder_datetime = QDateTimeEdit(QDateTime.currentDateTime())
        self._reminder_datetime.setCalendarPopup(True)
        self._reminder_datetime.setDisplayFormat("dd.MM.yyyy HH:mm")
        self._reminder_datetime.setEnabled(False)
        reminder_row.addWidget(self._reminder_datetime)

        self._repeat_combo = QComboBox()
        self._repeat_combo.addItem("Без повтора", "none")
        for val, label in [
            ("daily", "Ежедневно"), ("weekly", "Еженедельно"),
            ("monthly", "Ежемесячно"), ("yearly", "Ежегодно"),
        ]:
            self._repeat_combo.addItem(label, val)
        self._repeat_combo.setEnabled(False)
        reminder_row.addWidget(self._repeat_combo)
        layout.addLayout(reminder_row)

        self._editor_container = QVBoxLayout()
        layout.addLayout(self._editor_container, stretch=1)

        buttons_row = QHBoxLayout()

        self._pin_btn = QPushButton("📌 Закрепить")
        self._pin_btn.setCheckable(True)
        self._pin_btn.toggled.connect(self._on_pin_toggle)
        buttons_row.addWidget(self._pin_btn)

        self._encrypt_btn = QPushButton("🔒 Зашифровать")
        self._encrypt_btn.setCheckable(True)
        self._encrypt_btn.toggled.connect(self._on_encrypt_toggle)
        buttons_row.addWidget(self._encrypt_btn)

        delete_btn = QPushButton("🗑 В корзину")
        delete_btn.clicked.connect(self._on_soft_delete)
        buttons_row.addWidget(delete_btn)

        buttons_row.addStretch()

        save_btn = QPushButton("💾 Сохранить")
        save_btn.clicked.connect(self._on_save)
        save_btn.setShortcut("Ctrl+S")
        buttons_row.addWidget(save_btn)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        buttons_row.addWidget(close_btn)

        layout.addLayout(buttons_row)

    def _load_note_data(self):
        self._title_edit.setText(self._note.title)

        if self._note.category_id:
            idx = self._category_combo.findData(self._note.category_id)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)

        tags = self._note.tags if self._note.tags else []
        self._tag_edit.setText(", ".join(t.name for t in tags))

        self._pin_btn.setChecked(bool(self._note.is_pinned))
        self._encrypt_btn.setChecked(bool(self._note.is_encrypted))

        if self._note.reminder_at:
            self._reminder_check.setChecked(True)
            dt = QDateTime.fromString(self._note.reminder_at[:16], "yyyy-MM-ddTHH:mm")
            if not dt.isValid():
                dt = QDateTime.fromString(self._note.reminder_at[:16], "yyyy-MM-dd HH:mm")
            if dt.isValid():
                self._reminder_datetime.setDateTime(dt)
        if self._note.reminder_repeat:
            idx = self._repeat_combo.findData(self._note.reminder_repeat)
            if idx >= 0:
                self._repeat_combo.setCurrentIndex(idx)

        editor_cls = _EDITOR_MAP.get(self._note.type, TextEditor)
        self._editor = editor_cls()
        if self._note.id:
            self._editor.set_note_id(self._note.id)
        self._editor_container.addWidget(self._editor, stretch=1)

        if self._note.is_encrypted and self._note.content:
            password, ok = QInputDialog.getText(
                self, "Введите пароль", "Пароль для расшифровки:",
                QLineEdit.EchoMode.Password,
            )
            if not ok or not password:
                QTimer.singleShot(0, self.reject)
                return
            decrypted = decrypt(self._note.content, password)
            if decrypted is not None:
                self._decrypted_content = decrypted
                self._editor.set_content(decrypted)
            else:
                self._editor.clear()
        elif self._note.content:
            self._editor.set_content(self._note.content)

    def _on_reminder_toggle(self, checked: bool):
        self._reminder_datetime.setEnabled(checked)
        self._repeat_combo.setEnabled(checked)
        if checked:
            self._reminder_datetime.setDateTime(QDateTime.currentDateTime())

    def _on_pin_toggle(self, checked: bool):
        self._pin_btn.setText("📌 Закреплено" if checked else "📌 Закрепить")

    def _on_encrypt_toggle(self, checked: bool):
        if checked:
            self._encrypt_btn.setText("🔓 Зашифровано")
        else:
            self._encrypt_btn.setText("🔒 Зашифровать")

    def _on_soft_delete(self):
        if self._note.id:
            self._repo.soft_delete_note(self._note.id)
            self._deleted = True
            self.reject()

    def _on_save(self):
        self._note.title = self._title_edit.text()
        self._note.category_id = self._category_combo.currentData()

        if self._editor:
            raw = self._editor.get_content()
        else:
            raw = b""

        if self._encrypt_btn.isChecked() and raw:
            password, ok = QInputDialog.getText(
                self, "Установка пароля", "Пароль для шифрования:",
                QLineEdit.EchoMode.Password,
            )
            if ok and password:
                self._note.content = encrypt(raw, password)
                self._note.is_encrypted = 1
                self._note.password_hash = hash_password(password)
            else:
                self._note.content = raw
        else:
            self._note.content = raw
            self._note.is_encrypted = 0

        self._note.is_pinned = 1 if self._pin_btn.isChecked() else 0
        if self._reminder_check.isChecked():
            self._note.reminder_at = self._reminder_datetime.dateTime().toString("yyyy-MM-ddTHH:mm:ss")
        else:
            self._note.reminder_at = None
        self._note.reminder_repeat = self._repeat_combo.currentData() if self._reminder_check.isChecked() else None

        tag_names = [
            t.strip() for t in self._tag_edit.text().split(",") if t.strip()
        ]
        tag_ids = []
        for name in tag_names:
            existing = self._repo.get_all_tags()
            found = next((t for t in existing if t.name == name), None)
            if found:
                tag_ids.append(found.id)
            else:
                tag_ids.append(self._repo.create_tag(name))

        self._repo.update_note(self._note)
        if self._note.id and tag_ids:
            self._repo.set_note_tags(self._note.id, tag_ids)
        elif self._note.id:
            self._repo.set_note_tags(self._note.id, [])

        self.accept()
