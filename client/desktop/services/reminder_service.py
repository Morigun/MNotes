from __future__ import annotations

from datetime import datetime, timedelta

from PyQt6.QtCore import QTimer, QObject, pyqtSignal
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon

from database.models import Note
from database.repository import Repository


_REPEAT_DELTAS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
    "yearly": timedelta(days=365),
}

_TYPE_ICONS = {
    "text": "📝",
    "markdown": "📋",
    "list": "☑",
    "audio": "🎵",
    "richtext": "✏",
    "image": "🖼",
    "table": "▦",
    "folder": "📁",
}


class ReminderService(QObject):
    reminder_triggered = pyqtSignal(int)

    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self._tray: QSystemTrayIcon | None = None
        self._window = None
        self._icon: QIcon | None = None
        self._last_notified_id: int | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(10_000)
        self._timer.timeout.connect(self._check)
        self._timer.start()
        self._check()

    def set_tray(self, tray: QSystemTrayIcon):
        self._tray = tray

    def set_window(self, window):
        self._window = window

    def set_icon(self, icon: QIcon):
        self._icon = icon

    @staticmethod
    def _make_body(note: Note) -> str:
        if note.type in ("text", "markdown", "richtext") and note.content:
            text = note.content.decode("utf-8", errors="replace")[:180]
            return text + "..." if len(note.content) > 180 else text
        return "Заметка"

    def _check(self):
        notes = self._repo.get_pending_reminders()
        for note in notes:
            self._notify(note)
            self._advance_reminder(note)

    def _notify(self, note: Note):
        title = note.title or "Без названия"
        body = self._make_body(note)
        type_icon = _TYPE_ICONS.get(note.type, "")
        self._last_notified_id = note.id

        icon = self._icon or (self._tray.icon() if self._tray else None)

        if self._window:
            from ui.notification_popup import NotificationPopup
            popup = NotificationPopup(title, body, icon, type_icon, parent=self._window)
            popup.clicked.connect(self._on_message_clicked)
            popup.show_at()

        self.reminder_triggered.emit(note.id)

    def _on_message_clicked(self):
        if self._last_notified_id and self._window:
            self._window._restore()
            self._window._open_note(self._last_notified_id)

    def _advance_reminder(self, note: Note):
        if not note.reminder_repeat or note.reminder_repeat == "none":
            self._repo._conn.execute(
                "UPDATE notes SET reminder_at=NULL WHERE id=?", (note.id,)
            )
            self._repo._conn.commit()
            return

        delta = _REPEAT_DELTAS.get(note.reminder_repeat)
        if delta and note.reminder_at:
            try:
                current = datetime.fromisoformat(note.reminder_at)
                new_time = current + delta
                self._repo._conn.execute(
                    "UPDATE notes SET reminder_at=? WHERE id=?",
                    (new_time.strftime("%Y-%m-%d %H:%M:%S"), note.id),
                )
                self._repo._conn.commit()
            except (ValueError, TypeError):
                pass
