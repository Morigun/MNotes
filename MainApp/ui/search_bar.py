from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QComboBox
from PyQt6.QtCore import pyqtSignal, QTimer


class SearchBar(QWidget):
    search_changed = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск заметок...")
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input, stretch=1)

        self.type_filter = QComboBox()
        self.type_filter.addItem("Все типы", "")
        for t, label in [
            ("text", "Текст"), ("markdown", "Markdown"), ("list", "Список"),
            ("audio", "Аудио"), ("richtext", "Формат."), ("image", "Изображение"),
            ("table", "Таблица"), ("folder", "Папка"),
        ]:
            self.type_filter.addItem(label, t)
        layout.addWidget(self.type_filter)

        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(300)
        self._timer.timeout.connect(self._emit_search)

        self.search_input.textChanged.connect(self._on_text_changed)
        self.type_filter.currentIndexChanged.connect(self._emit_search)

    def _on_text_changed(self):
        self._timer.start()

    def _emit_search(self):
        self.search_changed.emit(
            self.search_input.text().strip(),
            self.type_filter.currentData() or "",
        )
