import winsound

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor


class NotificationPopup(QWidget):
    clicked = pyqtSignal()

    def __init__(self, title: str, body: str, app_icon: QIcon,
                 type_icon: str = "", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("notificationPopup")
        self.setFixedWidth(340)
        self.setMinimumHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setObjectName("notifCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 10, 14, 12)
        card_layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        if not app_icon.isNull():
            lbl_app_icon = QLabel()
            lbl_app_icon.setPixmap(app_icon.pixmap(16, 16))
            header_row.addWidget(lbl_app_icon)
        lbl_app_name = QLabel("MNotes")
        lbl_app_name.setObjectName("notifAppName")
        header_row.addWidget(lbl_app_name)
        header_row.addStretch()

        close_btn = QPushButton("X")
        close_btn.setObjectName("notifCloseBtn")
        close_btn.setFixedSize(24, 24)
        close_btn.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        close_btn.clicked.connect(self._close)
        header_row.addWidget(close_btn)
        card_layout.addLayout(header_row)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)

        if type_icon:
            lbl_type = QLabel()
            lbl_type.setObjectName("notifTypeIcon")
            lbl_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_type.setFixedSize(44, 44)
            pixmap = self._render_emoji(type_icon, 36)
            lbl_type.setPixmap(pixmap)
            content_row.addWidget(lbl_type)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        lbl_title = QLabel(title)
        lbl_title.setObjectName("notifTitle")
        lbl_title.setWordWrap(True)
        tf2 = lbl_title.font()
        tf2.setBold(True)
        tf2.setPointSize(10)
        lbl_title.setFont(tf2)
        text_col.addWidget(lbl_title)

        lbl_body = QLabel(body)
        lbl_body.setObjectName("notifBody")
        lbl_body.setWordWrap(True)
        text_col.addWidget(lbl_body)

        content_row.addLayout(text_col, stretch=1)
        card_layout.addLayout(content_row)

        outer.addWidget(card)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(6000)
        self._timer.timeout.connect(self._fade_out)

        self._opacity = 1.0
        self._fade_timer = QTimer(self)
        self._fade_timer.setInterval(30)
        self._fade_timer.timeout.connect(self._tick_fade)

        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

    def show_at(self):
        primary = QApplication.primaryScreen()
        if primary:
            screen = primary.availableGeometry()
        else:
            screen = QRect(0, 0, 1920, 1080)
        self.adjustSize()
        x = screen.right() - self.width() - 12
        y = screen.bottom() - self.height() - 12
        self.move(x, y)
        self.show()
        self._timer.start()

    def _close(self):
        self._timer.stop()
        self._fade_timer.stop()
        self.close()
        self.deleteLater()

    @staticmethod
    def _render_emoji(text: str, size: int) -> QPixmap:
        sz = int(size * 1.2)
        pixmap = QPixmap(sz, sz)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Segoe UI Emoji", int(size * 0.6))
        painter.setFont(font)
        rect = pixmap.rect().adjusted(0, -int(size * 0.1), 0, int(size * 0.15))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

    def _fade_out(self):
        self._fade_timer.start()

    def _tick_fade(self):
        self._opacity -= 0.05
        if self._opacity <= 0:
            self._fade_timer.stop()
            self.close()
            self.deleteLater()
        else:
            self.setWindowOpacity(self._opacity)

    def mousePressEvent(self, event):
        self._close()
        self.clicked.emit()
