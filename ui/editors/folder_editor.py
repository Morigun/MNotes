from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import QLabel, QVBoxLayout


class FolderEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel("Перетащите заметки в эту папку")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def get_content(self) -> bytes:
        return b""

    def set_content(self, data: bytes):
        pass

    def clear(self):
        pass
