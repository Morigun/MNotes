from PyQt6.QtWidgets import QTextEdit, QVBoxLayout

from ui.editors.base_editor import BaseEditor


class TextEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._edit = QTextEdit()
        self._edit.setAcceptRichText(False)
        self._edit.setPlaceholderText("Введите текст заметки...")
        layout.addWidget(self._edit)

    def get_content(self) -> bytes:
        return self._edit.toPlainText().encode("utf-8")

    def set_content(self, data: bytes):
        self._edit.setPlainText(data.decode("utf-8", errors="replace"))

    def clear(self):
        self._edit.clear()
