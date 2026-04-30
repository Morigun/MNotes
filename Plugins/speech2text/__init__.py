from plugins.plugin_base import PluginBase
from plugins.speech2text.settings import stt_vosk_dir, set_stt_vosk_dir, stt_model_path, set_stt_model_path, available_models
from pathlib import Path
import sys

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QComboBox, QPushButton, QLineEdit, QFileDialog, QMessageBox,
)


class Plugin(PluginBase):
    @property
    def name(self) -> str:
        return "speech2text"

    @property
    def description(self) -> str:
        return "Распознавание речи (Vosk). Перевод аудиозаметок в текст."

    def is_available(self) -> bool:
        return True

    def on_load(self):
        from plugins.plugin_manager import register_editor_action
        register_editor_action("audio", "📝 В текст", self._on_transcribe)

    def _on_transcribe(self, editor):
        try:
            from plugins.speech2text.vosk_shim import Model, KaldiRecognizer, SetLogLevel
        except Exception as e:
            QMessageBox.warning(editor, "Распознавание", f"Ошибка загрузки vosk:\n{e}")
            return
        if not editor._audio_data:
            return
        from PyQt6.QtWidgets import QApplication
        path = editor._temp_path()
        editor._ensure_player_source()
        editor._status_label.setText("Распознавание...")
        QApplication.processEvents()
        try:
            from plugins.speech2text.stt_service import transcribe
            text = transcribe(path)
        except Exception as e:
            QMessageBox.warning(editor, "Распознавание", f"Ошибка: {e}")
            editor._status_label.setText("")
            return
        if not text.strip():
            QMessageBox.information(editor, "Распознавание", "Речь не обнаружена.")
            editor._status_label.setText("")
            return
        from database.models import Note
        from database.repository import Repository
        repo = Repository()
        parent_id = None
        title = "Текст из аудио"
        if editor._note_id:
            src = repo.get_note(editor._note_id)
            if src:
                parent_id = src.parent_id if src.parent_id else None
                title = (src.title or "Аудио") + " (текст)"
        note = Note(type="text", title=title, parent_id=parent_id)
        note.content = text.strip().encode("utf-8")
        note.id = repo.create_note(note)
        editor._status_label.setText("Текстовая заметка создана")
        QMessageBox.information(
            editor, "Распознавание",
            f"Создана заметка «{title}».\n\n{text.strip()[:200]}",
        )

    def get_settings_widget(self, parent=None) -> QWidget:
        return _STTSettingsWidget(parent)


class _STTSettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Распознавание речи (Vosk)")
        gl = QVBoxLayout(group)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("Папка с моделями:"))
        self._dir_edit = QLineEdit(str(stt_vosk_dir()))
        dir_row.addWidget(self._dir_edit, stretch=1)
        browse_btn = QPushButton("Обзор...")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)
        gl.addLayout(dir_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Модель:"))
        self._model_combo = QComboBox()
        model_row.addWidget(self._model_combo, stretch=1)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._refresh_models)
        model_row.addWidget(refresh_btn)
        gl.addLayout(model_row)

        self._model_info = QLabel("")
        gl.addWidget(self._model_info)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._on_save)
        gl.addWidget(save_btn)

        layout.addWidget(group)
        layout.addStretch()
        self._refresh_models()

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Папка с моделями Vosk")
        if path:
            self._dir_edit.setText(path)
            self._refresh_models()

    def _refresh_models(self):
        set_stt_vosk_dir(self._dir_edit.text())
        self._model_combo.clear()
        models = available_models()
        if models:
            self._model_combo.addItems(models)
            current = stt_model_path()
            idx = self._model_combo.findText(current.name)
            if idx < 0:
                idx = 0
            self._model_combo.setCurrentIndex(idx)
        self._update_info()

    def _update_info(self):
        dir_text = self._dir_edit.text()
        model_name = self._model_combo.currentText()
        if not dir_text or not model_name:
            self._model_info.setText("Модель не найдена")
            return
        p = Path(dir_text) / model_name
        if p.exists():
            try:
                size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
                self._model_info.setText(f"Путь: {p}  ({size / 1024 / 1024:.1f} МБ)")
            except Exception:
                self._model_info.setText(f"Путь: {p}")
        else:
            self._model_info.setText("Модель не найдена")

    def _on_save(self):
        vosk_dir = self._dir_edit.text().strip()
        model_name = self._model_combo.currentText()
        if not vosk_dir:
            QMessageBox.warning(self, "Настройки", "Укажите папку с моделями.")
            return
        if not model_name:
            QMessageBox.warning(self, "Настройки", "Выберите модель.")
            return
        model_full = str(Path(vosk_dir) / model_name)
        if not Path(model_full).exists():
            QMessageBox.warning(self, "Настройки", f"Папка модели не найдена:\n{model_full}")
            return
        set_stt_vosk_dir(vosk_dir)
        set_stt_model_path(model_full)
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")
