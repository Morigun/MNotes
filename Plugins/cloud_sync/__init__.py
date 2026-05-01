from plugins.plugin_base import PluginBase

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QMessageBox,
)
from PyQt6.QtCore import Qt


class Plugin(PluginBase):
    @property
    def name(self) -> str:
        return "cloud_sync"

    @property
    def description(self) -> str:
        return "Синхронизация с удалённой БД через PHP сервер"

    def is_available(self) -> bool:
        try:
            import requests
            return True
        except ImportError:
            return False

    def on_load(self):
        from plugins.plugin_manager import register_toolbar_action
        register_toolbar_action("\u2601 Синхронизация", self._on_sync_toolbar)

    def _on_sync_toolbar(self):
        try:
            from plugins.cloud_sync.settings import (
                cloud_server_url, cloud_login, cloud_password,
            )
            url = cloud_server_url()
            login = cloud_login()
            password = cloud_password()
            if not url or not login:
                QMessageBox.warning(
                    None, "Синхронизация",
                    "Настройте сервер и логин в настройках (Вид → Настройки).",
                )
                return
            self._run_sync(url, login, password)
        except Exception as e:
            QMessageBox.warning(None, "Синхронизация", f"Ошибка: {e}")

    def _run_sync(self, url, login, password):
        from plugins.cloud_sync.api_client import CloudApiClient
        from plugins.cloud_sync.sync_engine import SyncEngine
        from plugins.cloud_sync.sync_dialog import SyncDialog
        from plugins.cloud_sync.settings import cloud_last_sync
        from database.repository import Repository

        repo = Repository()
        client = CloudApiClient(url, login, password)
        engine = SyncEngine(repo, client)
        last_sync = cloud_last_sync()

        dialog = SyncDialog(engine, last_sync)
        dialog.start()
        dialog.exec()

    def get_settings_widget(self, parent=None) -> QWidget:
        return _CloudSyncSettingsWidget(parent, self)


class _CloudSyncSettingsWidget(QWidget):
    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self._plugin = plugin
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("Облачная синхронизация")
        gl = QVBoxLayout(group)

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Адрес сервера:"))
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://example.com/mnotes/api/")
        url_row.addWidget(self._url_edit, stretch=1)
        gl.addLayout(url_row)

        login_row = QHBoxLayout()
        login_row.addWidget(QLabel("Логин:"))
        self._login_edit = QLineEdit()
        login_row.addWidget(self._login_edit, stretch=1)
        gl.addLayout(login_row)

        pass_row = QHBoxLayout()
        pass_row.addWidget(QLabel("Пароль:"))
        self._pass_edit = QLineEdit()
        self._pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pass_row.addWidget(self._pass_edit, stretch=1)
        gl.addLayout(pass_row)

        from plugins.cloud_sync.settings import (
            cloud_server_url, cloud_login, cloud_password,
            cloud_last_sync,
        )
        self._url_edit.setText(cloud_server_url())
        self._login_edit.setText(cloud_login())
        self._pass_edit.setText(cloud_password())

        btn_row = QHBoxLayout()
        test_btn = QPushButton("Проверить соединение")
        test_btn.clicked.connect(self._test_connection)
        btn_row.addWidget(test_btn)
        sync_btn = QPushButton("Синхронизировать сейчас")
        sync_btn.clicked.connect(self._sync_now)
        btn_row.addWidget(sync_btn)
        gl.addLayout(btn_row)

        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self._save_settings)
        gl.addWidget(save_btn)

        last_sync = cloud_last_sync()
        self._status_label = QLabel(
            f"Последняя синхронизация: {last_sync}" if last_sync else "Синхронизация не выполнялась"
        )
        gl.addWidget(self._status_label)

        layout.addWidget(group)
        layout.addStretch()

    def _save_settings(self):
        try:
            from plugins.cloud_sync.settings import (
                set_cloud_server_url, set_cloud_login, set_cloud_password,
            )
            set_cloud_server_url(self._url_edit.text().strip())
            set_cloud_login(self._login_edit.text().strip())
            set_cloud_password(self._pass_edit.text())
            QMessageBox.information(self, "Настройки", "Настройки сохранены.")
        except Exception as e:
            QMessageBox.warning(self, "Настройки", f"Ошибка: {e}")

    def _test_connection(self):
        try:
            self._save_settings_silent()
            from plugins.cloud_sync.settings import (
                cloud_server_url, cloud_login, cloud_password,
            )
            from plugins.cloud_sync.api_client import CloudApiClient
            url = cloud_server_url()
            login = cloud_login()
            password = cloud_password()
            if not url:
                QMessageBox.warning(self, "Проверка", "Укажите адрес сервера.")
                return
            client = CloudApiClient(url, login, password)
            client.authenticate()
            QMessageBox.information(self, "Проверка", "Соединение успешно!")
        except Exception as e:
            QMessageBox.warning(self, "Проверка", f"Ошибка: {e}")

    def _sync_now(self):
        try:
            self._save_settings_silent()
            if self._plugin:
                self._plugin._on_sync_toolbar()
            from plugins.cloud_sync.settings import cloud_last_sync
            last = cloud_last_sync()
            self._status_label.setText(
                f"Последняя синхронизация: {last}" if last else "Синхронизация не выполнялась"
            )
        except Exception as e:
            QMessageBox.warning(self, "Синхронизация", f"Ошибка: {e}")

    def _save_settings_silent(self):
        from plugins.cloud_sync.settings import (
            set_cloud_server_url, set_cloud_login, set_cloud_password,
        )
        set_cloud_server_url(self._url_edit.text().strip())
        set_cloud_login(self._login_edit.text().strip())
        set_cloud_password(self._pass_edit.text())
