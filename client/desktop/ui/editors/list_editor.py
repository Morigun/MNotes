import json

from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QCheckBox, QLineEdit,
    QPushButton, QWidget, QScrollArea, QStyle,
)
from PyQt6.QtCore import Qt

from ui.editors.base_editor import BaseEditor


class _ListItem(QWidget):
    def __init__(self, text: str = "", checked: bool = False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(checked)
        layout.addWidget(self.checkbox)

        self.line_edit = QLineEdit(text)
        self.line_edit.setPlaceholderText("Пункт списка...")
        layout.addWidget(self.line_edit)

        self.remove_btn = QPushButton()
        self.remove_btn.setFixedSize(28, 28)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)
        self.remove_btn.setIcon(icon)
        self.remove_btn.setToolTip("Удалить пункт")
        layout.addWidget(self.remove_btn)


class ListEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list[_ListItem] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._container)
        outer.addWidget(scroll)

        add_btn = QPushButton("+ Добавить пункт")
        add_btn.clicked.connect(lambda: self._add_item())
        outer.addWidget(add_btn)

    def _add_item(self, text: str = "", checked: bool = False):
        item = _ListItem(text, checked)
        item.remove_btn.clicked.connect(lambda: self._remove_item(item))
        self._items.append(item)
        self._layout.addWidget(item)

    def _remove_item(self, item: _ListItem):
        self._items.remove(item)
        self._layout.removeWidget(item)
        item.deleteLater()

    def get_content(self) -> bytes:
        data = [
            {"text": it.line_edit.text(), "checked": it.checkbox.isChecked()}
            for it in self._items
        ]
        return json.dumps(data, ensure_ascii=False).encode("utf-8")

    def set_content(self, data: bytes):
        self.clear()
        items = json.loads(data.decode("utf-8", errors="replace"))
        for entry in items:
            self._add_item(entry.get("text", ""), entry.get("checked", False))

    def clear(self):
        for item in list(self._items):
            self._remove_item(item)
