from database.repository import Repository

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCalendarWidget
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextCharFormat, QColor, QBrush


class CalendarWidget(QDialog):
    def __init__(self, repo: Repository, parent=None):
        super().__init__(parent)
        self._repo = repo
        self.selected_date: str | None = None
        self.setWindowTitle("Календарь")
        self.setMinimumSize(420, 380)

        layout = QVBoxLayout(self)
        self._calendar = QCalendarWidget()
        self._calendar.clicked.connect(self._on_date_clicked)
        layout.addWidget(self._calendar)

        self._mark_dates()

    def _mark_dates(self):
        note_dates = set(self._repo.get_dates_with_notes())
        reminder_dates = set(self._repo.get_dates_with_reminders())

        note_fmt = QTextCharFormat()
        note_fmt.setBackground(QBrush(QColor("#89b4fa")))

        reminder_fmt = QTextCharFormat()
        reminder_fmt.setBackground(QBrush(QColor("#f38ba8")))

        all_dates = note_dates | reminder_dates
        for d_str in all_dates:
            parts = d_str.split("-")
            if len(parts) != 3:
                continue
            qdate = QDate(int(parts[0]), int(parts[1]), int(parts[2]))
            if d_str in reminder_dates:
                self._calendar.setDateTextFormat(qdate, reminder_fmt)
            elif d_str in note_dates:
                self._calendar.setDateTextFormat(qdate, note_fmt)

    def _on_date_clicked(self, date: QDate):
        self.selected_date = date.toString("yyyy-MM-dd")
        self.accept()
