from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMenu
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QDrag, QBrush


def _create_table_icon(size: int = 16) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    pen = QPen(QColor("#89b4fa"), 1.5)
    painter.setPen(pen)
    m = 2
    w = size - 2 * m
    h = size - 2 * m
    painter.drawRect(m, m, w, h)
    painter.drawLine(m + w // 3, m, m + w // 3, m + h)
    painter.drawLine(m + 2 * w // 3, m, m + 2 * w // 3, m + h)
    painter.drawLine(m, m + h // 3, m + w, m + h // 3)
    painter.drawLine(m, m + 2 * h // 3, m + w, m + 2 * h // 3)
    fill = QColor("#89b4fa")
    fill.setAlpha(40)
    painter.fillRect(m + 1, m + 1, w // 3 - 1, h // 3 - 1, fill)
    painter.fillRect(m + w // 3 + 1, m + h // 3 + 1, w // 3 - 1, h // 3 - 1, fill)
    painter.end()
    return pixmap


class NoteCard(QWidget):
    double_clicked = pyqtSignal(int)
    clicked = pyqtSignal(int, bool)
    context_menu_requested = pyqtSignal(int, object)
    remove_from_folder = pyqtSignal(int)
    rename_folder = pyqtSignal(int)
    delete_folder = pyqtSignal(int)

    def __init__(self, note_id: int, title: str, note_type: str,
                 preview: str = "", is_pinned: bool = False,
                 is_encrypted: bool = False, updated_at: str = "",
                 child_count: int = 0, in_folder: bool = False,
                 parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.note_type = note_type
        self.title = title
        self._in_folder = in_folder
        self._selected = False
        self.setFixedSize(210, 210)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("noteCard")
        self.setAcceptDrops(note_type == "folder")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        header = QLabel(title or "Без названия")
        header.setObjectName("cardTitle")
        header.setWordWrap(True)
        layout.addWidget(header)

        date_label = QLabel(updated_at or "")
        date_label.setObjectName("cardDate")
        layout.addWidget(date_label)

        icon_row = QHBoxLayout()
        icon_row.setSpacing(4)

        if is_pinned:
            icon_row.addWidget(QLabel("📌"))
        if is_encrypted:
            icon_row.addWidget(QLabel("🔒"))

        type_icons = {
            "text": "📝", "markdown": "📋", "list": "☑",
            "audio": "🎵", "richtext": "✏", "image": "🖼",
            "folder": "📁",
        }
        if note_type == "table":
            lbl = QLabel()
            lbl.setPixmap(_create_table_icon(16))
            icon_row.addWidget(lbl)
        else:
            icon_text = type_icons.get(note_type, "")
            if icon_text:
                icon_row.addWidget(QLabel(icon_text))

        if note_type == "folder" and child_count > 0:
            icon_row.addWidget(QLabel(f"({child_count})"))

        icon_row.addStretch()
        layout.addLayout(icon_row)

        if preview:
            preview_label = QLabel(preview[:120])
            preview_label.setObjectName("cardPreview")
            preview_label.setWordWrap(True)
            layout.addWidget(preview_label)

        layout.addStretch()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self.note_id)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
            self.context_menu_requested.emit(self.note_id, pos)
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
            ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            self.clicked.emit(self.note_id, ctrl)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not hasattr(self, '_drag_start_pos'):
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        dist = (event.position().toPoint() if hasattr(event, 'position') else event.pos()) - self._drag_start_pos
        if dist.manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(str(self.note_id))
        if self.note_type == "folder":
            mime.setData("application/x-folder", b"1")
        drag.setMimeData(mime)
        drag.exec(Qt.DropAction.CopyAction)

    def dragEnterEvent(self, event):
        if self.note_type == "folder" and event.mimeData().hasText():
            dragged_id = int(event.mimeData().text())
            if dragged_id != self.note_id:
                event.acceptProposedAction()
                self.setStyleSheet(self.styleSheet() + "; border: 2px solid #89b4fa;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        note_id_str = event.mimeData().text()
        if not note_id_str.isdigit() or int(note_id_str) == self.note_id:
            return
        dragged_id = int(note_id_str)
        from database.repository import Repository
        repo = Repository()
        is_folder = event.mimeData().hasFormat("application/x-folder")
        if is_folder:
            dragged = repo.get_note(dragged_id)
            if dragged and self._is_descendant(self.note_id, dragged_id, repo):
                return
        repo.move_note_to_folder(dragged_id, self.note_id)
        event.acceptProposedAction()
        main_win = self.window()
        if hasattr(main_win, '_load_notes'):
            main_win._load_notes()

    @staticmethod
    def _is_descendant(target_id: int, folder_id: int, repo) -> bool:
        children = repo.get_notes(parent_id=folder_id)
        for child in children:
            if child.id == target_id:
                return True
            if child.type == "folder" and NoteCard._is_descendant(target_id, child.id, repo):
                return True
        return False

    def set_selected(self, selected: bool):
        if self._selected == selected:
            return
        self._selected = selected
        self.update()

    def is_selected(self) -> bool:
        return self._selected

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._selected:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor("#89b4fa"), 3))
            painter.setBrush(QBrush(QColor(137, 180, 250, 40)))
            painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 8, 8)
            painter.end()
