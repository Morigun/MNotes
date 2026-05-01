import sys
import ctypes
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QFont, QAction, QIcon
from PyQt6.QtCore import Qt, QSettings, QTimer

from database.db_manager import DatabaseManager
from database.repository import Repository
from services.reminder_service import ReminderService
from ui.main_window import MainWindow

APP_VERSION = "1.1.1"
APP_DIR = Path(__file__).parent

MUTEX_NAME = "MNotes_SingleInstance_Mutex"
ACTIVATE_EVENT_NAME = "MNotes_Activate_Event"

THEMES = {
    "dark": APP_DIR / "resources" / "style.qss",
    "light": APP_DIR / "resources" / "style_light.qss",
}


def load_theme(app: QApplication, theme: str = "dark") -> None:
    qss_path = THEMES.get(theme, THEMES["dark"])
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))


def current_theme() -> str:
    settings = QSettings("MNotes", "MNotes")
    return settings.value("theme", "dark")


def set_theme(theme: str) -> None:
    settings = QSettings("MNotes", "MNotes")
    settings.setValue("theme", theme)


def apply_titlebar_theme(widget, dark: bool) -> None:
    try:
        hwnd = int(widget.winId())
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value), ctypes.sizeof(value),
        )
    except Exception:
        pass


def main():
    kernel32 = ctypes.windll.kernel32

    mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    already_running = kernel32.GetLastError() == 183

    if already_running:
        event = kernel32.OpenEventW(0x0002, False, ACTIVATE_EVENT_NAME)
        if event:
            kernel32.SetEvent(event)
            kernel32.CloseHandle(event)
        sys.exit(0)

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MNotes")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("MNotes")
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setQuitOnLastWindowClosed(False)

    activate_event = kernel32.CreateEventW(None, False, False, ACTIVATE_EVENT_NAME)

    app_icon = QIcon(str(APP_DIR / "app.ico"))
    app.setWindowIcon(app_icon)

    load_theme(app, current_theme())

    db = DatabaseManager()
    db.init_db()

    repo = Repository()

    window = MainWindow()
    window.setWindowIcon(app_icon)

    def check_activate():
        if kernel32.WaitForSingleObject(activate_event, 0) == 0:
            window._restore()

    activate_timer = QTimer()
    activate_timer.timeout.connect(check_activate)
    activate_timer.start(200)

    icon = app_icon

    tray_menu = QMenu()
    show_action = tray_menu.addAction("Показать MNotes")
    show_action.triggered.connect(window._restore)
    new_action = tray_menu.addAction("Новая заметка")
    new_action.triggered.connect(lambda: window._create_note("text"))
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction("Выход")
    quit_action.triggered.connect(app.quit)

    tray = QSystemTrayIcon()
    tray.setIcon(QIcon(icon))
    tray.setContextMenu(tray_menu)
    tray.setToolTip(f"MNotes v{APP_VERSION}")
    tray.activated.connect(lambda reason: window._restore() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)
    tray.show()

    reminder_svc = ReminderService(repo)
    reminder_svc.set_tray(tray)
    reminder_svc.set_window(window)
    reminder_svc.set_icon(app_icon)
    tray.messageClicked.connect(reminder_svc._on_message_clicked)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
