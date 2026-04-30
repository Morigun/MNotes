from PyQt6.QtWidgets import QWidget


class BaseEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._note_id: int | None = None

    def set_note_id(self, note_id: int):
        self._note_id = note_id

    def get_content(self) -> bytes:
        raise NotImplementedError

    def set_content(self, data: bytes):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError
