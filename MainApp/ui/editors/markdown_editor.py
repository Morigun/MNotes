import markdown2

from PyQt6.QtWidgets import QSplitter, QPlainTextEdit, QTextBrowser, QVBoxLayout
from PyQt6.QtCore import Qt

from ui.editors.base_editor import BaseEditor


class MarkdownEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self._source = QPlainTextEdit()
        self._source.setPlaceholderText("Введите Markdown...")
        self._source.textChanged.connect(self._render_preview)

        self._preview = QTextBrowser()
        self._preview.setOpenExternalLinks(False)

        splitter.addWidget(self._source)
        splitter.addWidget(self._preview)
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)

    def _render_preview(self):
        md_text = self._source.toPlainText()
        html = markdown2.markdown(md_text, extras=["fenced-code-blocks", "tables"])
        self._preview.setHtml(html)

    def get_content(self) -> bytes:
        return self._source.toPlainText().encode("utf-8")

    def set_content(self, data: bytes):
        self._source.setPlainText(data.decode("utf-8", errors="replace"))

    def clear(self):
        self._source.clear()
        self._preview.clear()
