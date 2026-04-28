from PyQt6.QtWidgets import QWidget


class BaseEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def get_content(self) -> bytes:
        raise NotImplementedError

    def set_content(self, data: bytes):
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError
