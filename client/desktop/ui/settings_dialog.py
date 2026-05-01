from pathlib import Path

from plugins.plugin_manager import loaded_plugins, plugin_info, discover_plugins

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QTabWidget, QWidget, QPushButton,
)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)
        self.resize(550, 400)

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs, stretch=1)

        self._build_plugins_tab()
        self._build_plugin_settings()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _build_plugins_tab(self):
        page = QWidget()
        pl = QVBoxLayout(page)

        pl.addWidget(QLabel("Установленные плагины:"))

        for name in discover_plugins():
            info = plugin_info(name)
            row = QHBoxLayout()
            from plugins.plugin_manager import get_plugin
            plugin = get_plugin(name)
            loaded = plugin is not None and plugin.is_available()
            status = "✓" if loaded else "✗"
            title = info.get("description", name) if info else name
            ver = info.get("version", "") if info else ""
            row.addWidget(QLabel(f"{status} {title} ({ver})"))
            row.addStretch()
            pl.addLayout(row)

        pl.addStretch()
        self._tabs.addTab(page, "Плагины")

    def _build_plugin_settings(self):
        for plugin in loaded_plugins():
            widget = plugin.get_settings_widget(self)
            if widget:
                self._tabs.addTab(widget, plugin.name)
