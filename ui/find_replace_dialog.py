from database.repository import Repository

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox,
)


class FindReplaceDialog(QDialog):
    def __init__(self, repo: Repository, note_ids: list[int], parent=None):
        super().__init__(parent)
        self._repo = repo
        self._note_ids = note_ids
        self.replaced_count = 0

        self.setWindowTitle("Найти и заменить")
        self.setMinimumWidth(400)
        self.resize(450, 180)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Найти:"))
        self._find_edit = QLineEdit()
        self._find_edit.setPlaceholderText("Текст для поиска...")
        layout.addWidget(self._find_edit)

        layout.addWidget(QLabel("Заменить на:"))
        self._replace_edit = QLineEdit()
        self._replace_edit.setPlaceholderText("Текст для замены...")
        layout.addWidget(self._replace_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        replace_btn = QPushButton("Заменить все")
        replace_btn.clicked.connect(self._on_replace)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        btn_row.addWidget(replace_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _on_replace(self):
        find_text = self._find_edit.text()
        replace_text = self._replace_edit.text()
        if not find_text:
            return

        self.replaced_count = 0
        for note_id in self._note_ids:
            note = self._repo.get_note(note_id)
            if note is None or note.type not in ("text", "markdown", "richtext"):
                continue
            if note.content is None:
                continue
            try:
                content_str = note.content.decode("utf-8")
            except Exception:
                continue

            count = content_str.count(find_text)
            if count == 0:
                continue

            new_content = content_str.replace(find_text, replace_text)
            note.content = new_content.encode("utf-8")
            self._repo.update_note(note)
            self.replaced_count += count

        msg = f"Заменено вхождений: {self.replaced_count}" if self.replaced_count else "Вхождения не найдены."
        QMessageBox.information(self, "Результат", msg)
