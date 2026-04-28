from database.models import Note
from database.repository import Repository
from services.export_service import ExportService

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QListWidget, QListWidgetItem, QLabel,
)
from PyQt6.QtCore import Qt


class ExportDialog(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._service = ExportService(repo)
        self.setWindowTitle("Экспорт / Импорт")
        self.setMinimumSize(500, 400)
        self.resize(600, 450)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Выберите заметки для экспорта:"))

        self._list = QListWidget()
        notes = self._repo.get_notes()
        for note in notes:
            item = QListWidgetItem(f"{note.title or 'Без названия'} ({note.type})")
            item.setData(Qt.ItemDataRole.UserRole, note.id)
            item.setCheckState(Qt.CheckState.Unchecked)
            self._list.addItem(item)
        layout.addWidget(self._list, stretch=1)

        btn_row = QHBoxLayout()

        export_sel_btn = QPushButton("📤 Экспорт выбранных")
        export_sel_btn.clicked.connect(self._export_selected)
        btn_row.addWidget(export_sel_btn)

        export_all_btn = QPushButton("📦 Экспорт всех (ZIP)")
        export_all_btn.clicked.connect(self._export_all)
        btn_row.addWidget(export_all_btn)

        import_btn = QPushButton("📥 Импорт из ZIP")
        import_btn.clicked.connect(self._import_zip)
        btn_row.addWidget(import_btn)

        btn_row.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def _export_selected(self):
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                note_id = item.data(Qt.ItemDataRole.UserRole)
                note = self._repo.get_note(note_id)
                if note:
                    path, _ = QFileDialog.getSaveFileName(
                        self, "Экспорт заметки", note.title or "note",
                        "Все файлы (*)",
                    )
                    if path:
                        self._service.export_note(note, path)

    def _export_all(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Экспорт всех заметок", "mnotes_export.zip",
            "ZIP архив (*.zip)",
        )
        if path:
            self._service.export_all(path)

    def _import_zip(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Импорт заметок", "", "ZIP архив (*.zip)",
        )
        if path:
            count = self._service.import_from_zip(path)
            self.accept()
