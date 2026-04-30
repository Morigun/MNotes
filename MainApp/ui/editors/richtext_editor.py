from ui.editors.base_editor import BaseEditor

from PyQt6.QtWidgets import (
    QVBoxLayout, QTextEdit, QToolBar, QPushButton,
)
from PyQt6.QtGui import QTextCharFormat, QTextBlockFormat, QFont
from PyQt6.QtCore import Qt


class RichTextEditor(BaseEditor):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QToolBar()
        layout.addWidget(toolbar)

        bold_btn = QPushButton("B")
        bold_btn.setStyleSheet("font-weight: bold; font-size: 15px;")
        bold_btn.clicked.connect(self._toggle_bold)
        bold_btn.setToolTip("Жирный")
        toolbar.addWidget(bold_btn)

        italic_btn = QPushButton("I")
        italic_btn.setStyleSheet("font-style: italic; font-size: 15px;")
        italic_btn.clicked.connect(self._toggle_italic)
        italic_btn.setToolTip("Курсив")
        toolbar.addWidget(italic_btn)

        underline_btn = QPushButton("U")
        underline_btn.setStyleSheet("text-decoration: underline; font-size: 15px;")
        underline_btn.clicked.connect(self._toggle_underline)
        underline_btn.setToolTip("Подчёркнутый")
        toolbar.addWidget(underline_btn)

        toolbar.addSeparator()

        align_left = QPushButton("⫷")
        align_left.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignLeft))
        align_left.setToolTip("По левому краю")
        toolbar.addWidget(align_left)

        align_center = QPushButton("☰")
        align_center.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignCenter))
        align_center.setToolTip("По центру")
        toolbar.addWidget(align_center)

        align_right = QPushButton("⫸")
        align_right.clicked.connect(lambda: self._set_alignment(Qt.AlignmentFlag.AlignRight))
        align_right.setToolTip("По правому краю")
        toolbar.addWidget(align_right)

        toolbar.addSeparator()

        list_btn = QPushButton("• Список")
        list_btn.clicked.connect(self._insert_list)
        list_btn.setToolTip("Вставить список")
        toolbar.addWidget(list_btn)

        self._edit = QTextEdit()
        self._edit.setAcceptRichText(True)
        self._edit.setPlaceholderText("Введите форматированный текст...")
        layout.addWidget(self._edit, stretch=1)

    def _toggle_bold(self):
        cursor = self._edit.textCursor()
        current = cursor.charFormat().fontWeight()
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal if current >= QFont.Weight.Bold else QFont.Weight.Bold)
        self._apply_format(fmt)

    def _toggle_italic(self):
        cursor = self._edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontItalic(not cursor.charFormat().fontItalic())
        self._apply_format(fmt)

    def _toggle_underline(self):
        cursor = self._edit.textCursor()
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not cursor.charFormat().fontUnderline())
        self._apply_format(fmt)

    def _apply_format(self, fmt: QTextCharFormat):
        cursor = self._edit.textCursor()
        cursor.mergeCharFormat(fmt)
        self._edit.mergeCurrentCharFormat(fmt)
        self._edit.setFocus()

    def _set_alignment(self, alignment):
        cursor = self._edit.textCursor()
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        fmt = QTextBlockFormat()
        fmt.setAlignment(alignment)
        cursor.setBlockFormat(fmt)

    def _insert_list(self):
        self._edit.textCursor().insertHtml("<ul><li>Пункт</li></ul>")

    def get_content(self) -> bytes:
        return self._edit.toHtml().encode("utf-8")

    def set_content(self, data: bytes):
        html = data.decode("utf-8", errors="replace")
        if html.strip().startswith("<"):
            self._edit.setHtml(html)
        else:
            self._edit.setPlainText(html)

    def clear(self):
        self._edit.clear()
